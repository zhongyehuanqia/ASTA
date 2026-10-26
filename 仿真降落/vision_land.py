"""视觉仿真：下视相机识别蓝色地面目标，飞到上方后降落。

水平位置只来自图像里的色块中心。高度来自仿真器状态，相当于气压计。
目标丢失时原地悬停并略微爬升，不继续往下扎。
"""

import os
import sys

import cv2
import numpy as np
import pybullet as p

from gym_pybullet_drones.envs.HoverAviary import HoverAviary
from gym_pybullet_drones.utils.enums import ActionType, ObservationType

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "shots")

# 蓝色地面圆盘。红色在 HSV 里会跨 0 度，任务文档建议用蓝或绿。
TARGET_XY = np.array([0.45, -0.25])
TARGET_RADIUS = 0.16
BLUE_LOWER = np.array([95, 80, 60], dtype=np.uint8)
BLUE_UPPER = np.array([135, 255, 255], dtype=np.uint8)

# 图像坐标：相机朝下，up 取世界 +X。
# 图像 y 向下对应世界 -X，图像 x 向右对应世界 -Y。
CENTER_PIX = 0.12
DESCEND_STEP = 0.06
HOLD_Z = 0.55
LAND_Z = 0.12
GAIN = 0.40


class LandAviary(HoverAviary):
    """把悬停环境的回合时间拉长，够飞过去再降落。"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.EPISODE_LEN_SEC = 40


def add_target(client):
    """在地面放一块蓝色薄圆柱，当作降落靶。"""
    col = p.createCollisionShape(
        p.GEOM_CYLINDER, radius=TARGET_RADIUS, height=0.02, physicsClientId=client
    )
    vis = p.createVisualShape(
        p.GEOM_CYLINDER,
        radius=TARGET_RADIUS,
        length=0.02,
        rgbaColor=[0.05, 0.15, 0.95, 1.0],
        physicsClientId=client,
    )
    return p.createMultiBody(
        baseMass=0,
        baseCollisionShapeIndex=col,
        baseVisualShapeIndex=vis,
        basePosition=[TARGET_XY[0], TARGET_XY[1], 0.01],
        physicsClientId=client,
    )


def look_down(env):
    """从无人机正下方拍一张图，返回 BGR。"""
    state = env._getDroneStateVector(0)
    pos = state[0:3]
    eye = pos + np.array([0.0, 0.0, 0.0])
    target = pos + np.array([0.0, 0.0, -1.0])
    view = p.computeViewMatrix(
        cameraEyePosition=eye,
        cameraTargetPosition=target,
        cameraUpVector=[1, 0, 0],
        physicsClientId=env.CLIENT,
    )
    proj = p.computeProjectionMatrixFOV(
        fov=70.0,
        aspect=1.0,
        nearVal=0.02,
        farVal=8.0,
        physicsClientId=env.CLIENT,
    )
    width, height = 160, 160
    _, _, rgba, _, _ = p.getCameraImage(
        width=width,
        height=height,
        viewMatrix=view,
        projectionMatrix=proj,
        renderer=p.ER_TINY_RENDERER,
        physicsClientId=env.CLIENT,
    )
    rgba = np.reshape(rgba, (height, width, 4))
    bgr = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2BGR)
    return bgr, pos


def find_blue(bgr):
    """返回色块中心。找不到时中心为 None。"""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, mask
    contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(contour) < 12:
        return None, mask
    moments = cv2.moments(contour)
    if moments["m00"] <= 0:
        return None, mask
    cx = int(moments["m10"] / moments["m00"])
    cy = int(moments["m01"] / moments["m00"])
    return (cx, cy), mask


def waypoint(pos, center, shape, lost_steps):
    """像素偏差映射成下一航点。丢失目标时保持水平位置并爬高搜索。"""
    x, y, z = pos
    if center is None:
        search_z = min(0.9, z + 0.04) if lost_steps > 8 else z
        return np.array([x, y, search_z], dtype=np.float32), False
    h, w = shape[:2]
    ex = (center[0] - w / 2) / (w / 2)
    ey = (center[1] - h / 2) / (h / 2)
    centered = abs(ex) < CENTER_PIX and abs(ey) < CENTER_PIX
    nxt = np.array(
        [x - ey * GAIN, y - ex * GAIN, z],
        dtype=np.float32,
    )
    if centered:
        nxt[2] = max(0.04, z - DESCEND_STEP)
    else:
        nxt[2] = max(z, HOLD_Z)
    return np.clip(nxt, -1.0, 1.0), centered


def draw_overlay(bgr, center, text):
    frame = bgr.copy()
    h, w = frame.shape[:2]
    cv2.drawMarker(frame, (w // 2, h // 2), (255, 255, 255), cv2.MARKER_CROSS, 16, 1)
    if center is not None:
        cv2.circle(frame, center, 6, (0, 255, 0), 2)
    cv2.putText(frame, text, (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    return frame


def main():
    os.makedirs(SHOTS, exist_ok=True)
    env = LandAviary(
        gui=False,
        obs=ObservationType.KIN,
        act=ActionType.PID,
        initial_xyzs=np.array([[0.0, 0.0, 0.6]]),
    )
    try:
        env.reset()
        target_id = add_target(env.CLIENT)
        frames = []
        saved = {"see": False, "center": False, "land": False, "lost": False}
        lost_steps = 0
        landed = False
        last_center = None
        hidden = False
        max_steps = 700

        for step in range(max_steps):
            # 中途把靶标涂灰，模拟丢失目标；之后涂回蓝色，确认能重新对准。
            if 40 <= step < 70:
                if not hidden:
                    p.changeVisualShape(
                        target_id, -1, rgbaColor=[0.45, 0.45, 0.45, 1], physicsClientId=env.CLIENT
                    )
                    hidden = True
            elif hidden:
                p.changeVisualShape(
                    target_id, -1, rgbaColor=[0.05, 0.15, 0.95, 1], physicsClientId=env.CLIENT
                )
                hidden = False

            bgr, pos = look_down(env)
            center, _mask = find_blue(bgr)
            if center is None:
                lost_steps += 1
            else:
                lost_steps = 0
                last_center = center
            nxt, centered = waypoint(pos, center, bgr.shape, lost_steps)
            dist_xy = float(np.linalg.norm(pos[:2] - TARGET_XY))
            text = "z=%.2f dxy=%.2f %s" % (
                pos[2],
                dist_xy,
                "lost" if center is None else "see",
            )
            frame = draw_overlay(bgr, center, text)
            if step % 3 == 0:
                frames.append(frame)

            if center is not None and not saved["see"]:
                cv2.imwrite(os.path.join(SHOTS, "01_detect.jpg"), frame)
                saved["see"] = True
            if center is None and lost_steps >= 5 and not saved["lost"]:
                cv2.imwrite(os.path.join(SHOTS, "04_lost.jpg"), frame)
                saved["lost"] = True
            if centered and not saved["center"]:
                cv2.imwrite(os.path.join(SHOTS, "02_above.jpg"), frame)
                saved["center"] = True

            action = np.expand_dims(nxt.astype(np.float32), axis=0)
            _obs, _reward, terminated, truncated, _info = env.step(action)

            if centered and pos[2] < LAND_Z and dist_xy < 0.22:
                landed = True
                cv2.imwrite(os.path.join(SHOTS, "03_land.jpg"), frame)
                saved["land"] = True
                print("landed step=%d pos=%s dist_xy=%.3f" % (step, np.round(pos, 3), dist_xy))
                break
            if terminated or truncated:
                print("stop step=%d terminated=%s truncated=%s pos=%s" % (
                    step, terminated, truncated, np.round(pos, 3)
                ))
                break
            if step % 30 == 0:
                print(
                    "step=%d pos=%s center=%s lost=%d"
                    % (step, np.round(pos, 3), center, lost_steps)
                )

        if frames:
            video_path = os.path.join(SHOTS, "landing.avi")
            h, w = frames[0].shape[:2]
            writer = cv2.VideoWriter(
                video_path, cv2.VideoWriter_fourcc(*"MJPG"), 10, (w, h)
            )
            for frame in frames:
                writer.write(frame)
            writer.release()

        if not landed:
            bgr, pos = look_down(env)
            dist_xy = float(np.linalg.norm(pos[:2] - TARGET_XY))
            print("not landed pos=%s dist_xy=%.3f last_center=%s" % (
                np.round(pos, 3), dist_xy, last_center
            ))
            cv2.imwrite(os.path.join(SHOTS, "03_final.jpg"), draw_overlay(bgr, last_center, "final"))
            return 1
        return 0
    finally:
        env.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("vision_land failed:", exc)
        raise
