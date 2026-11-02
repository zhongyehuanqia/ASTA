"""只重训降落靶。数据和权重都在 pad/ 里，不会动 cup/。

三轮除了下面写明的差异，其余设置相同：20 个 epoch，输入 416，batch 4，CPU，关掉 Mosaic。
已经训好的结果在 runs/n-lr001、runs/n-lr0001、runs/s-lr001。
检测用的是 n、学习率 0.01 那一轮：runs/n-lr001/weights/best.pt。
"""

from pathlib import Path

from ultralytics import YOLO

HERE = Path(__file__).resolve().parent
DATA = HERE / "dataset" / "data.yaml"
N_WEIGHT = HERE.parent / "yolov8n.pt"
S_WEIGHT = HERE.parent / "yolov8s.pt"
RUNS = HERE / "runs"

COMMON = dict(
    data=str(DATA),
    epochs=20,
    imgsz=416,
    batch=4,
    device="cpu",
    workers=2,
    mosaic=0.0,
    patience=20,
    optimizer="SGD",
    cache=True,
    exist_ok=True,
    project=str(RUNS),
    plots=True,
    verbose=True,
)


def run(name, model, **extra):
    print(f"\n===== {name} =====", flush=True)
    YOLO(model).train(name=name, **COMMON, **extra)


def main():
    run("n-lr001", str(N_WEIGHT), lr0=0.01)
    run("n-lr0001", str(N_WEIGHT), lr0=0.001, freeze=10)
    run("s-lr001", str(S_WEIGHT), lr0=0.01)
    print("\n降落靶三轮训练结束", flush=True)
    print(f"检测权重：{RUNS / 'n-lr001' / 'weights' / 'best.pt'}", flush=True)


if __name__ == "__main__":
    main()
