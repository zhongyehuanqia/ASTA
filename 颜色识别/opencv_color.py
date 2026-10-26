"""OpenCV 入门：在一张图里按颜色找出蓝色方块和红色圆。"""

from pathlib import Path

import cv2
import numpy as np


def draw_centers(image, mask, label, color):
    """找轮廓，画出外接框和中心点，返回中心坐标。"""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    centers = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 200:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        cx, cy = x + w // 2, y + h // 2
        cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
        cv2.circle(image, (cx, cy), 4, color, -1)
        cv2.putText(image, f"{label} ({cx},{cy})", (x, max(20, y - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        centers.append((cx, cy))
    return centers


def main():
    image = np.full((360, 640, 3), 30, np.uint8)
    cv2.rectangle(image, (80, 80), (220, 220), (255, 80, 40), -1)  # BGR 蓝色方块
    cv2.circle(image, (460, 180), 70, (40, 40, 220), -1)  # BGR 红色圆

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # OpenCV 的 H 范围是 0–179。蓝色一段就够，红色在色相两端，要并起来。
    blue = cv2.inRange(hsv, (90, 80, 80), (130, 255, 255))
    red = cv2.bitwise_or(
        cv2.inRange(hsv, (0, 80, 80), (10, 255, 255)),
        cv2.inRange(hsv, (160, 80, 80), (179, 255, 255)),
    )

    blue_centers = draw_centers(image, blue, "blue", (255, 180, 0))
    red_centers = draw_centers(image, red, "red", (0, 220, 255))
    print("blue", blue_centers)
    print("red", red_centers)

    out = Path(__file__).resolve().parent / "opencv_color_result.jpg"
    cv2.imwrite(str(out), image)
    print("saved", out)


if __name__ == "__main__":
    main()
