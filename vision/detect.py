"""用预训练 YOLOv8n 检测图片或视频中的物体。

先进入虚拟环境，再在本目录运行：

    source ~/venvs/yolo/bin/activate
    python detect.py --source bus.jpg
    python detect.py --source sample.mp4

画好框的结果保存在 runs/detect/ 下。
"""

import argparse
from pathlib import Path

from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="YOLOv8n 预训练检测")
    parser.add_argument("--source", required=True, help="图片或视频的路径")
    parser.add_argument(
        "--model",
        default=str(Path(__file__).resolve().parent / "yolov8n.pt"),
        help="预训练权重，默认使用本目录里的 yolov8n.pt",
    )
    args = parser.parse_args()

    # 加载预训练模型。第一次若本地没有权重，Ultralytics 会自动下载。
    model = YOLO(args.model)
    # save=True：把画了检测框的图片或视频写到 runs/detect/。
    model.predict(source=args.source, save=True)


if __name__ == "__main__":
    main()
