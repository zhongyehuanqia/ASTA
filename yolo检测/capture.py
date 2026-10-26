"""自己控制拍照，窗口里实时显示 YOLO 检测框。

先进入虚拟环境，再在本目录运行：

    source ~/venvs/yolo/bin/activate
    python capture.py

空格：保存当前原始画面（不把框画进文件，方便以后训练）
q：退出

照片保存在 dataset/images/manual/，不会覆盖以前自动拍的 30 张。
"""

from pathlib import Path

import cv2
from ultralytics import YOLO


def next_index(folder):
    numbers = []
    for path in folder.glob("manual_*.jpg"):
        stem = path.stem.replace("manual_", "")
        if stem.isdigit():
            numbers.append(int(stem))
    return max(numbers, default=-1) + 1


def main():
    out = Path(__file__).resolve().parent / "dataset" / "images" / "manual"
    out.mkdir(parents=True, exist_ok=True)
    index = next_index(out)

    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    if not cap.isOpened():
        raise SystemExit("打不开摄像头。先确认虚拟机里连的是 RGB Camera，并且存在 /dev/video0。")

    model = YOLO(str(Path(__file__).resolve().parent / "yolov8n.pt"))
    print("模型已加载。窗口里能看到检测框。空格保存一张，q 退出。")
    print(f"保存目录：{out}")
    while True:
        ok, frame = cap.read()
        if not ok:
            print("读不到画面。")
            break
        # plot() 把类别和置信度画在画面上，只用于显示。
        view = model.predict(frame, verbose=False)[0].plot()
        cv2.putText(
            view,
            f"saved {index}   SPACE save    Q quit",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )
        cv2.imshow("capture", view)
        key = cv2.waitKey(1) & 0xFF
        if key == ord(" "):
            path = out / f"manual_{index:02d}.jpg"
            cv2.imwrite(str(path), frame)
            print(f"已保存 {path.name}")
            index += 1
        elif key in (ord("q"), ord("Q")):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"本次目录里一共 {index} 张。")


if __name__ == "__main__":
    main()
