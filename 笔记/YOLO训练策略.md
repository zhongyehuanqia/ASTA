# YOLO 训练策略

模型是 YOLOv8n，从 `yolov8n.pt` 接着训。数据是 USB 摄像头拍的 30 张，24 张训练、6 张验证，类别只有 person，框由这个预训练模型自动标出。训练 15 个 epoch，输入 320，学习率 0.01，骨干没有冻住。

第 1 轮验证集 mAP50 是 0.945，mAP50-95 是 0.884，定位损失 0.42。第 15 轮变成 0.679、0.271 和 2.28。训练损失在降，验证定位损失在升。模型在背这 24 张图，换一张就更差。第 1 轮的高分基本还是原来的预训练权重。

person 在 COCO 里已经有。摄像头上 person 0.87 用的就是现成权重。下一轮要训的是预训练里没有的类，例如降落靶、闸门、本组标志。

## 用到的论文

| 论文 | 从里面取的结论 |
| --- | --- |
| Zhang 等，*Bag of Freebies for Training Object Detection Neural Networks*，2019。https://arxiv.org/abs/1902.04103 | 训练技巧不改网络、不增加推理开销。他们在 YOLOv3 和 Faster R-CNN 上叠了 mixup、学习率日程、label smoothing。YOLOv3 在 608 输入上比基线高 4.0 个 mAP，更低分辨率上高 5.4 个。增强是为了减轻过拟合。 |
| Bochkovskiy、Wang、Liao，*YOLOv4*，2020。https://arxiv.org/abs/2004.10934 | 把只在训练时起作用的方法叫做 Bag of Freebies。光度变化、缩放、翻转用来适应不同环境；Mosaic 把 4 张图拼在一起，让目标出现在更多位置和尺度。框回归用 CIoU。COCO 上 43.5% AP、65.7% AP50。 |
| Zheng 等，*Distance-IoU Loss*，AAAI 2020。https://arxiv.org/abs/1911.08287 | 框要同时看重叠面积、中心点距离、长宽比。CIoU 把这三样放进损失，比只看 IoU 收敛更快。YOLOv8 的框损失已经包含这一项。 |
| Kisantal 等，*Augmentation for small object detection*，2019。https://arxiv.org/abs/1902.07296 | 小目标差，是因为含小目标的图少，而且每张图里小目标出现的位置也少。他们过采样这些图，再把小目标复制粘贴到不重叠的位置。COCO 上小目标检测相对提高 7.1%，实例分割相对提高 9.7%。 |
| Ghiasi 等，*Simple Copy-Paste is a Strong Data Augmentation Method for Instance Segmentation*，CVPR 2021。https://arxiv.org/abs/2012.07177 | 随机把目标贴到另一张图上就有效，不必先建模周围场景。只用 10% 的 COCO 训练数据时，box AP 提高约 10 个点。完整 COCO 上达到 57.3 box AP。贴上去的框必须是准的。 |
| Kumar 等，*Fine-Tuning can Distort Pretrained Features and Underperform Out-of-Distribution*，ICLR 2022。https://arxiv.org/abs/2202.10054 | 这篇做的是分类，不是检测。结论是：预训练特征已经好、数据和原来差得远时，一上来改全部参数会把底层特征改坏。他们在 10 个分布偏移数据集上看到，全量微调比只训最后一层，分布内高约 2%，分布外低约 7%。先只训最后一层，再小学习率微调全部参数，分布外比直接全量微调高约 10%。 |
| Wang、Bochkovskiy、Liao，*YOLOv7*，CVPR 2023。https://arxiv.org/abs/2207.02696 | 继续强调 Bag of Freebies：重参数化、动态分配正样本，都只增加训练成本，不增加推理成本。他们在完整 COCO 上从零训练，V100 上 30 FPS 以上的检测器里达到 56.8% AP。 |

YOLOv8 没有一篇和 YOLOv4、YOLOv7 同等级的正式论文。现在用的 Mosaic、CIoU、预训练微调，来自上面这些工作。

## 合成后的训练策略

1. **先换类别，再谈训练。** person 继续用 `yolov8n.pt`。自己的模型用来认预训练没有的目标。

2. **图要换场景，不要连拍。** YOLOv4 写增强是为了亮度、尺度、遮挡这些环境变化。同一个房间连拍 30 张，增强也制造不出新场景。每个类先拍 100 张以上，远、近、斜、遮挡、不同光线都要有，再加没有目标的空图。验证集换一个时间或地点拍，不要从训练视频里抽帧。

3. **框自己画。** 现在的框是预训练模型自动标的，有的框宽度占整张图的 0.88。CIoU 会去贴近这个框。框是错的，损失学到的位置也是错的。自动框只当草稿，漏框、过大、框错的都改掉。

4. **先冻住骨干，再用小学习率放开。** 这对应 Kumar 的两步微调。检测里的做法是 `freeze=10`，先让检测头适应当前数据，预训练的底层特征先不动。验证定位损失不再下降，再解冻，学习率用 `0.001`，不要用这次的 `0.01`。YOLOv7 从零训练成立，是因为他们有完整 COCO。几十张图从零训没有这个条件。

5. **增强分两段开。** 第一版关掉 Mosaic，确认验证损失下降。数据过了 100 张、框也标紧之后，再把 Mosaic 打开。最后约 10 个 epoch 关掉 Mosaic，让模型看回正常的整张图。亮度、对比度、左右翻转可以一直留着，这是 Zhang 和 YOLOv4 里对过拟合有用、又不太破坏画面的部分。

6. **损失先不改。** CIoU 已经在 YOLOv8 里。这次变差是数据和学习率，不是损失公式少了一项。

7. **小目标单独处理。** 降落靶在画面里往往很小。按 Kisantal 的做法，含小靶的图多抽一些；输入用 640，不用 320。320 会把本来就小的目标再缩掉。复制粘贴放到框已经标紧之后：从标好的图里把靶贴到别的背景上，不要和已有目标叠在一起。Ghiasi 的结果是在至少约十分之一 COCO 的规模上得到的，30 张图上先不要靠粘贴凑数。

8. **用验证损失停，不用固定跑满。** 这次训练损失下降、验证定位损失上升，就该停在第 1 轮附近。下一轮设 50 个 epoch，`patience=10`。同时看 mAP50-95，不要只看 mAP50。mAP50 宽松，框偏了仍可能算对。

9. **用没见过的图和旧权重要对比。** 拿一张训练集、验证集都没有的照片，跑 `yolov8n.pt` 和自己的 `best.pt`。自己的权重更差，就丢掉这一轮。验证集分数只说明在那几张图上的表现。

## 下一轮可以照这个跑

数据准备好之后，在 `yolo检测` 目录：

```bash
source ~/venvs/yolo/bin/activate
yolo detect train \
  model=yolov8n.pt \
  data=dataset/data.yaml \
  epochs=50 patience=10 \
  imgsz=640 batch=8 device=cpu \
  lr0=0.001 freeze=10 \
  mosaic=0 \
  project=runs name=custom-train exist_ok=True
```

`data.yaml` 里的类别改成实际要认的名字。`freeze=10` 这一轮验证损失稳住以后，再用同一份 `best.pt` 做第二次训练：`freeze=0`，`lr0=0.0001`，`mosaic=1.0`，`close_mosaic=10`。第二次仍然从自己的 `best.pt` 开始，不要回到随机初始化。
