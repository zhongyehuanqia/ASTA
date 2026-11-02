"""只训练水杯。不会读取或覆盖 pad/ 里的降落靶数据和权重。

每一轮训练里，Ultralytics 只在验证集 mAP50-95 变高时才覆盖该轮的 best.pt。
连续 10 个 epoch 没有变高就停止。

顺序：
1. n-stable：从 yolov8n.pt 开始，学习率 0.001，冻住前 10 层。
2. n-finetune：从 n-stable 的 best.pt 继续，学习率 0.0001，放开全部层。
3. s-stable：同样的小学习率和冻结，只把模型换成 yolov8s，用来对比速度。

三份 best.pt 里 mAP50-95 最高的一个复制到本目录 best.pt。detect_cup.py 默认用它。
"""

import csv
import shutil
from pathlib import Path

from ultralytics import YOLO

HERE = Path(__file__).resolve().parent
DATA = HERE / "dataset" / "data.yaml"
N_WEIGHT = HERE.parent / "yolov8n.pt"
S_WEIGHT = HERE.parent / "yolov8s.pt"
RUNS = HERE / "runs"
KEPT = HERE / "best.pt"

COMMON = dict(
    data=str(DATA),
    epochs=40,
    patience=10,
    imgsz=416,
    batch=4,
    device="cpu",
    workers=2,
    mosaic=0.0,
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
    score = best_map(name)
    print(f"{name} 的 best.pt 对应 mAP50-95 = {score:.3f}", flush=True)
    return score


def best_map(name):
    path = RUNS / name / "results.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))

    def score(row):
        for key, value in row.items():
            if key.strip() == "metrics/mAP50-95(B)":
                return float(value)
        raise KeyError(f"{path} 里没有 mAP50-95")

    return max(score(row) for row in rows)


def keep_best(scores):
    winner = max(scores, key=scores.get)
    source = RUNS / winner / "weights" / "best.pt"
    shutil.copy(source, KEPT)
    print(f"\n保留 {winner}，mAP50-95 = {scores[winner]:.3f}", flush=True)
    print(f"检测用的权重：{KEPT}", flush=True)


def main():
    if not DATA.exists():
        raise SystemExit("还没有 dataset/data.yaml。先拍照、标注，再运行 python split_real.py。")
    scores = {}
    scores["n-stable"] = run("n-stable", str(N_WEIGHT), lr0=0.001, freeze=10)
    stable_best = RUNS / "n-stable" / "weights" / "best.pt"
    scores["n-finetune"] = run("n-finetune", str(stable_best), lr0=0.0001, freeze=0)
    scores["s-stable"] = run("s-stable", str(S_WEIGHT), lr0=0.001, freeze=10)
    keep_best(scores)


if __name__ == "__main__":
    main()
