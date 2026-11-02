"""用预训练 YOLOv8n 检测图片、视频或 USB 摄像头中的物体。

先进入虚拟环境，再在本目录运行：

    source ~/venvs/yolo/bin/activate
    python detect.py --source bus.jpg
    python detect.py --source sample.mp4
    python detect.py --source 0

摄像头画面按 q 退出。第一张带检测框的画面会存到 截图/yolo-camera.jpg。
图片和视频的结果保存在 runs/detect/ 下。
"""

import argparse
from pathlib import Path

import cv2
from ultralytics import YOLO


def run_camera(model, index):
    """打开 USB 摄像头，实时画框，并保存一张截图。"""
    cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
    # 这台摄像头在虚拟机里用默认格式会读超时，指定 MJPG 和 640x480 才能出图。
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    if not cap.isOpened():
        raise SystemExit(f"打不开摄像头 {index}。先执行 ls /dev/video* 确认设备存在。")

    shot = Path(__file__).resolve().parent / "截图" / "yolo-camera.jpg"
    saved = False
    seen = 0
    print("摄像头已打开。前几帧可能是黑的，稍等画面稳定。窗口里按 q 退出。")
    while True:
        ok, frame = cap.read()
        if not ok:
            print("读不到画面，请检查 USB 是否仍连接在虚拟机上。")
            break
        seen += 1
        # 刚打开时 JPEG 还没稳定，平均亮度过低的帧直接丢掉。
        if seen < 20 or float(frame.mean()) < 8:
            continue
        annotated = model.predict(frame, verbose=False)[0].plot()
        if not saved:
            cv2.imwrite(str(shot), annotated)
            saved = True
            print(f"截图已保存：{shot}")
        cv2.imshow("YOLO camera", annotated)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="YOLOv8n 预训练检测")
    parser.add_argument("--source", required=True, help="图片、视频路径，或摄像头编号 0")
    parser.add_argument(
        "--model",
        default=str(Path(__file__).resolve().parent / "yolov8n.pt"),
        help="预训练权重，默认使用本目录里的 yolov8n.pt",
    )
    args = parser.parse_args()

    model = YOLO(args.model)
    if args.source.isdigit():
        run_camera(model, int(args.source))
        return
    # save=True：把画了检测框的图片或视频写到 runs/detect/。
    model.predict(source=args.source, save=True)


if __name__ == "__main__":
    main()
