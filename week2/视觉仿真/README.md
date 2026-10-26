# 视觉仿真降落

在 gym-pybullet-drones 里用朝下相机找蓝色地面靶，飞到正上方再降落。水平位置只看图像里的色块中心，高度用仿真状态，相当于气压计。

## 环境

系统 Python 是 3.8。仿真用单独的 Python 3.10：

```text
/home/qia/miniconda3/envs/drones
```

仿真库在上一级目录的 `gym-pybullet-drones`，来自 https://github.com/utiasDSL/gym-pybullet-drones 。这个上游仓库没有放进 git。当前上游声明要 Python 3.12，所以没有用 `pip install -e .`，运行时把该目录放到 `PYTHONPATH`。需要的包已经装在 `drones` 环境里：pybullet、gymnasium、numpy、scipy、opencv-python。

## 怎么跑

```bash
cd ~/桌面/第二周任务/视觉仿真
PYTHONPATH=~/桌面/第二周任务/gym-pybullet-drones \
  ~/miniconda3/envs/drones/bin/python vision_land.py
```

无界面。截图和视频写到 `shots/`：

- `01_detect.jpg`：起飞后看到蓝色靶
- `02_above.jpg`：靶心靠近画面中心
- `04_lost.jpg`：靶被涂灰，程序标成丢失并保持高度
- `03_land.jpg`：重新看到蓝色后降落，高度约 0.12 m
- `landing.avi`：整段过程

最近一次结果：第 179 步降落，水平偏差 0.044 m。

## 颜色和阈值

靶是蓝色圆柱，半径 0.16 m，位置 `(0.45, -0.25)`。不用红色，因为红色在 HSV 里要分两段。

OpenCV 用 BGR。HSV 阈值：

```text
H 95–135
S 80–255
V 60–255
```

轮廓面积小于 12 像素算没看到。

## 控制

画面中心是正下方。相机朝下，图像向上对应世界 +X，图像向右对应世界 -Y。像素偏差乘 0.40 得到下一航点，再交给环境自带的 PID。

偏差小于 0.12 才下降，否则高度保持在 0.55 m 左右。目标丢失超过 8 步就原地保持并略微爬升，不继续下降。程序在第 40 到 70 步把靶涂成灰色，用来走这段逻辑，之后涂回蓝色再降落。

## 遇到的问题

库自带相机朝前。降落需要朝下看，所以在 `vision_land.py` 里单独算了一张朝下的图。

悬停环境默认 8 秒就结束，不够降落，回合时间改成了 40 秒。

动作被限制在 -1 到 1 米，起飞高度设成 0.6 m，靶也放在这个范围内。
