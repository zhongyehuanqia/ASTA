"""把 raw/ 里 labelImg 标好的水杯图划进 dataset，供 train_cup.py 使用。

txt 必须和 jpg 同名，并且都在 raw/ 里。一行格式是：
`0 中心x 中心y 宽 高`，类别 0 是 cup。

会先清空本目录 dataset 里已有的训练图和标注，再复制进去。raw 里的原图不删。
大约五分之四进训练集，其余进验证集。满 12 张时另留最后一张做测试。
这里只动水杯目录，不会改降落靶的 pad/dataset。
"""

import random
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
OUT = HERE / "dataset"
SEED = 7


def labeled_pairs():
    pairs = []
    missing = []
    for image in sorted(RAW.glob("img_*.jpg")):
        label = RAW / f"{image.stem}.txt"
        if label.exists():
            pairs.append((image, label))
        else:
            missing.append(image.name)
    return pairs, missing


def reset(folder):
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)


def main():
    pairs, missing = labeled_pairs()
    if not pairs:
        raise SystemExit(
            "raw/ 里没有和 jpg 同名的 txt。先运行 capture.py，再用 labelImg 把水杯标成类别 cup。"
        )
    if missing:
        print("这些图还没有标注，本次不放进训练集：")
        for name in missing:
            print(f"  {name}")

    rng = random.Random(SEED)
    rng.shuffle(pairs)
    test = []
    if len(pairs) >= 12:
        test = pairs[:1]
        pairs = pairs[1:]
    val_count = max(1, round(len(pairs) * 0.2))
    val = pairs[:val_count]
    train = pairs[val_count:]
    if not train:
        raise SystemExit("标注少于 2 张，没法同时做训练集和验证集。")

    for split in ("train", "val", "test"):
        reset(OUT / "images" / split)
        reset(OUT / "labels" / split)

    def copy_split(items, split):
        for index, (image, label) in enumerate(items):
            stem = f"{split}_{index:02d}"
            shutil.copy(image, OUT / "images" / split / f"{stem}.jpg")
            shutil.copy(label, OUT / "labels" / split / f"{stem}.txt")

    copy_split(train, "train")
    copy_split(val, "val")
    copy_split(test, "test")
    (OUT / "classes.txt").write_text("cup\n", encoding="utf-8")
    (OUT / "data.yaml").write_text(
        "\n".join(
            [
                f"path: {OUT}",
                "train: images/train",
                "val: images/val",
                "names:",
                "  0: cup",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"train {len(train)}  val {len(val)}  test {len(test)}")
    print("接下来运行 python train_cup.py")


if __name__ == "__main__":
    main()
