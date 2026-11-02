"""用已有摄像头照片当背景，把双环降落靶贴到不同位置，并写成 YOLO 标注。

标签和 labelImg 导出的格式相同：每一行是
`类别编号 中心x 中心y 宽 高`，四个数都除以整张图的宽或高。

背景按文件名拆开：img_00 到 img_23、manual_00 到 manual_05 只进训练集，
img_24 到 img_29 只进验证集。manual_06 留作训练没见过的测试图。
"""

import random
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BG_ALL = ROOT / "dataset" / "images" / "all"
BG_MANUAL = ROOT / "dataset" / "images" / "manual"
PAD_PATH = ROOT / "降落靶-双环.png"
OUT = HERE / "dataset"
PREVIEW = ROOT / "截图" / "pad-dataset.jpg"
SEED = 7


def load_pad():
    bgr = cv2.imread(str(PAD_PATH), cv2.IMREAD_COLOR)
    if bgr is None:
        raise SystemExit(f"读不到降落靶：{PAD_PATH}")
    white = np.all(bgr > 240, axis=2)
    alpha = np.where(white, 0, 255).astype(np.uint8)
    return bgr, alpha


def rotated_sprite(bgr, alpha, side, angle, gain):
    """缩放到指定边长，再旋转。返回裁紧后的图和透明通道。"""
    sprite = cv2.resize(bgr, (side, side), interpolation=cv2.INTER_AREA)
    mask = cv2.resize(alpha, (side, side), interpolation=cv2.INTER_AREA)
    sprite = np.clip(sprite.astype(np.float32) * gain, 0, 255).astype(np.uint8)

    center = (side / 2.0, side / 2.0)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])
    bound = (int(side * sin + side * cos), int(side * sin + side * cos))
    matrix[0, 2] += bound[0] / 2.0 - center[0]
    matrix[1, 2] += bound[1] / 2.0 - center[1]
    warped = cv2.warpAffine(sprite, matrix, bound, flags=cv2.INTER_LINEAR, borderValue=(255, 255, 255))
    warped_a = cv2.warpAffine(mask, matrix, bound, flags=cv2.INTER_LINEAR, borderValue=0)
    ys, xs = np.where(warped_a > 20)
    if len(xs) == 0:
        raise RuntimeError("旋转后没有不透明像素")
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return warped[y0:y1, x0:x1], warped_a[y0:y1, x0:x1]


def paste(bg, sprite, alpha, rng):
    h, w = bg.shape[:2]
    sh, sw = sprite.shape[:2]
    if sw >= w or sh >= h:
        raise RuntimeError("靶比背景大")
    x = rng.randint(0, w - sw)
    y = rng.randint(0, h - sh)
    roi = bg[y : y + sh, x : x + sw]
    a = (alpha.astype(np.float32) / 255.0)[..., None]
    blended = sprite.astype(np.float32) * a + roi.astype(np.float32) * (1.0 - a)
    out = bg.copy()
    out[y : y + sh, x : x + sw] = blended.astype(np.uint8)
    cx = (x + sw / 2.0) / w
    cy = (y + sh / 2.0) / h
    bw = sw / w
    bh = sh / h
    return out, (cx, cy, bw, bh)


def backgrounds(names, folder):
    paths = []
    for name in names:
        path = folder / name
        if not path.exists():
            raise SystemExit(f"缺少背景图：{path}")
        paths.append(path)
    return paths


def draw_box(image, box, text):
    h, w = image.shape[:2]
    cx, cy, bw, bh = box
    x0 = int((cx - bw / 2) * w)
    y0 = int((cy - bh / 2) * h)
    x1 = int((cx + bw / 2) * w)
    y1 = int((cy + bh / 2) * h)
    view = image.copy()
    cv2.rectangle(view, (x0, y0), (x1, y1), (0, 220, 0), 2)
    cv2.putText(view, text, (x0, max(16, y0 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 0), 1)
    return view


def main():
    rng = random.Random(SEED)
    pad_bgr, pad_a = load_pad()
    train_bgs = backgrounds([f"img_{i:02d}.jpg" for i in range(24)], BG_ALL)
    train_bgs += backgrounds([f"manual_{i:02d}.jpg" for i in range(6)], BG_MANUAL)
    val_bgs = backgrounds([f"img_{i:02d}.jpg" for i in range(24, 30)], BG_ALL)
    test_bg = BG_MANUAL / "manual_06.jpg"

    # 同一张背景可以贴两次，但验证集背景不会出现在训练集里。
    plan = [("train", path) for path in train_bgs]
    plan += [("train", train_bgs[i]) for i in range(10)]
    plan += [("val", path) for path in val_bgs]
    plan += [("val", val_bgs[i]) for i in range(4)]
    plan.append(("test", test_bg))

    for split in ("train", "val", "test"):
        (OUT / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUT / "labels" / split).mkdir(parents=True, exist_ok=True)

    counts = {"train": 0, "val": 0, "test": 0}
    previews = []
    for split, bg_path in plan:
        bg = cv2.imread(str(bg_path), cv2.IMREAD_COLOR)
        side = rng.randint(70, 280)
        angle = rng.uniform(-35, 35)
        gain = rng.uniform(0.75, 1.15)
        sprite, alpha = rotated_sprite(pad_bgr, pad_a, side, angle, gain)
        image, box = paste(bg, sprite, alpha, rng)
        index = counts[split]
        counts[split] += 1
        stem = f"{split}_{index:02d}"
        cv2.imwrite(str(OUT / "images" / split / f"{stem}.jpg"), image)
        cx, cy, bw, bh = box
        label = OUT / "labels" / split / f"{stem}.txt"
        label.write_text(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n", encoding="utf-8")
        if split != "test" and len(previews) < 8:
            previews.append(draw_box(image, box, stem))

    (OUT / "classes.txt").write_text("pad\n", encoding="utf-8")
    yaml = OUT / "data.yaml"
    yaml.write_text(
        "\n".join(
            [
                f"path: {OUT}",
                "train: images/train",
                "val: images/val",
                "names:",
                "  0: pad",
                "",
            ]
        ),
        encoding="utf-8",
    )

    cell_w, cell_h = 320, 240
    tiles = [cv2.resize(item, (cell_w, cell_h)) for item in previews]
    while len(tiles) < 8:
        tiles.append(np.zeros((cell_h, cell_w, 3), dtype=np.uint8))
    top = np.hstack(tiles[:4])
    bottom = np.hstack(tiles[4:8])
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(PREVIEW), np.vstack([top, bottom]))
    print(f"train {counts['train']}  val {counts['val']}  test {counts['test']}")
    print(f"配置：{yaml}")
    print(f"预览：{PREVIEW}")


if __name__ == "__main__":
    main()
