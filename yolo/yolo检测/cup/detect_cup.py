"""用水杯权重检测。默认模型是本目录的 best.pt。

先进入虚拟环境，再在本目录运行：

    source ~/venvs/yolo/bin/activate
    python detect_cup.py --source dataset/images/test/test_00.jpg
    python detect_cup.py --source 0

摄像头按 q 退出。带框的画面存到上一级目录的 截图/cup-camera.jpg。
图片结果另外存到 截图/cup-detect.jpg。
"""

import argparse
from pathlib import Path

import cv2
from ultralytics import YOLO

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = HERE / "best.pt"
SHOTS = HERE.parent / "截图"


def open_camera(index):
    cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
    # 这台虚拟机里强制 MJPG 会出横条，和拍照脚本一样用默认格式。
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    if not cap.isOpened():
        raise SystemExit(f"打不开摄像头 {index}。先执行 ls /dev/video* 确认设备存在。")
    return cap


def run_camera(model, index):
    cap = open_camera(index)
    shot = SHOTS / "cup-camera.jpg"
    SHOTS.mkdir(parents=True, exist_ok=True)
    saved = False
    seen = 0
    print("摄像头已打开。窗口里按 q 退出。")
    while True:
        ok, frame = cap.read()
        if not ok:
            print("读不到画面，请检查 USB 是否仍连接在虚拟机上。")
            break
        seen += 1
        if seen < 20 or float(frame.mean()) < 8:
            continue
        result = model.predict(frame, verbose=False)[0]
        annotated = result.plot()
        found = result.boxes is not None and len(result.boxes) > 0
        if found and not saved:
            cv2.imwrite(str(shot), annotated)
            saved = True
            labels = ", ".join(
                f"{result.names[int(box.cls[0])]} {float(box.conf[0]):.2f}"
                for box in result.boxes
            )
            print(f"检出 {labels}")
            print(f"截图已保存：{shot}")
        cv2.imshow("cup", annotated)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="用训练好的权重检测水杯")
    parser.add_argument("--source", required=True, help="图片或视频路径，或摄像头编号 0")
    parser.add_argument("--model", default=str(DEFAULT_MODEL), help="best.pt 路径")
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.exists():
        raise SystemExit(f"找不到权重：{model_path}。先完成 train_cup.py。")
    model = YOLO(str(model_path))
    if args.source.isdigit():
        run_camera(model, int(args.source))
        return

    result = model.predict(source=args.source, save=True, project=str(HERE / "runs"), name="predict", exist_ok=True)[0]
    SHOTS.mkdir(parents=True, exist_ok=True)
    shot = SHOTS / "cup-detect.jpg"
    cv2.imwrite(str(shot), result.plot())
    names = result.names
    if result.boxes is None or len(result.boxes) == 0:
        print(f"没有检出水杯。画面已保存：{shot}")
        return
    for box in result.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        print(f"{names[cls_id]} {conf:.2f}")
    print(f"结果已保存：{shot}")


if __name__ == "__main__":
    main()
