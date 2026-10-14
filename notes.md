# 算法组第一轮学习笔记

姓名：zhongyehuanqia

日期：2026-10-11

仓库链接：https://github.com/zhongyehuanqia/algo-week1

## 一、任务清单

- 完成了什么
  - [x] VS Code 打开本仓库
  - [x] Git 配置姓名和邮箱
  - [x] 本地仓库初始化，并完成第一次提交
  - [x] 推到 GitHub：https://github.com/zhongyehuanqia/algo-week1
  - [x] 终端运行 `git status`、`git log` 并截图
- 没完成什么
  - USB 摄像头实时检测（现在没有摄像头，图片和视频已经跑通）
  - PX4 250 框架阅读（Day 8–9）

## 二、操作记录

- 命令 + 截图
- 关键步骤说明

### 1. 配置 Git（每人自己的姓名和邮箱，只做一次）

```bash
git config --global user.name "你的姓名"
git config --global user.email "你的邮箱"
git config --global --list
```

把 `git config --global --list` 的终端截图放到 `shots/`，例如 `shots/git-config.png`。

### 2. 查看仓库状态

在仓库目录里执行：

```bash
cd ~/桌面/algo-week1
git status
git log --oneline
```

截图：

![git status 和 git log](shots/git-status-log.png)

说明：在 `main` 分支完成第一次提交 `ce9689d`（添加学习笔记模板和报错库）。`git status` 显示工作区干净，没有未提交的改动。

### 2.1 用 VS Code 打开仓库

```bash
code ~/桌面/algo-week1
```

截图：

![VS Code 打开 algo-week1](shots/vscode-algo-week1.png)

说明：左侧资源管理器里能看到 `notes.md`、`.gitignore` 和 `shots`。窗口标题是 `algo-week1`。

### 3. 推到远程

远程仓库：https://github.com/zhongyehuanqia/algo-week1.git

```bash
git remote add origin https://github.com/zhongyehuanqia/algo-week1.git
git push -u origin main
```

### 4. 用图片跑 YOLO 预训练检测

进入虚拟环境后，在 `vision` 目录执行：

```bash
source ~/venvs/yolo/bin/activate
cd ~/桌面/algo-week1/vision
yolo predict model=yolov8n.pt source='https://ultralytics.com/images/bus.jpg'
```

第一次运行会下载权重 `yolov8n.pt`。检测结果在 `vision/runs/detect/predict/bus.jpg`，截图已复制到 `shots/yolo-bus.jpg`。

![图片检测结果](shots/yolo-bus.jpg)

说明：预训练模型框出了公交车和行人。当时没有 USB 摄像头，所以先用图片跑通。

### 5. 用视频跑同一份代码

检测脚本是 `vision/detect.py`。视频文件是 `vision/sample.mp4`。

```bash
source ~/venvs/yolo/bin/activate
cd ~/桌面/algo-week1/vision
python detect.py --source sample.mp4
```

结果视频写在 `vision/runs/detect/predict-2/sample.avi`。终端里每一帧会打印检测到的类别，例如 `1 person`。下面是其中一帧，框出了沙滩上的人：

![视频检测结果](shots/yolo-video.jpg)

### 6. 后续：USB 摄像头实时检测

摄像头插上之后再做。先确认系统能看到设备，再沿用 `vision/detect.py`，把输入从视频文件改成摄像头编号 `0`。

```bash
ls /dev/video*
source ~/venvs/yolo/bin/activate
cd ~/桌面/algo-week1/vision
python detect.py --source 0
```

屏幕上应出现实时画面和检测框。按 `q` 或在终端按 Ctrl+C 结束。截一张带检测框的画面，保存为 `shots/yolo-camera.jpg`，并在这里补上截图和说明。

- [ ] 摄像头已插入，`/dev/video*` 存在
- [ ] `python detect.py --source 0` 能实时出框
- [ ] 截图保存到 `shots/yolo-camera.jpg`

## 三、报错库

| 日期 | 模块 | 报错/现象 | 原因 | 解决 | 参考 |
| --- | --- | --- | --- | --- | --- |
| 2026-10-11 | Git | `Permission to zhongyehuanqia/algo-week1.git denied to zhongyehuanqia`，HTTPS 返回 403 | 用来推送的 Token 没有这个仓库的写入权限 | 重新生成 Classic Token，勾选 `repo`，在 `git push` 的 Password 提示里粘贴 Token | https://github.com/zhongyehuanqia/algo-week1 |

## 四、代码/文件

| 文件路径 | 作用说明 |
| --- | --- |
| `notes.md` | 学习笔记，最后整份交到飞书 |
| `shots/` | 操作截图和检测结果图 |
| `vision/detect.py` | 用 YOLOv8n 检测图片或视频，结果保存到 `runs/detect/` |
| `vision/yolov8n.pt` | 预训练权重，不提交到 Git，本机运行时使用 |
| `vision/sample.mp4` | 用来代替摄像头的示例视频，不提交到 Git |

## 五、小结与疑问

- 学到了什么
  - 用 `git config` 配置姓名和邮箱，用 `git add` / `git commit` 做提交，用 `git push` 推到 GitHub。
  - `git status` 看有没有未提交的改动，`git log` 看提交记录。
  - 用 `code ~/桌面/algo-week1` 可以在 VS Code 里打开整个仓库。
  - 推送时 Password 要填 Token，不是 GitHub 登录密码。
  - 用虚拟环境安装 Ultralytics，并用 `yolov8n.pt` 对图片和视频做了预训练检测。
- 还没懂什么
  - Token 过期之后要不要重新生成，本地会不会还记着旧 Token。
  - USB 摄像头还没接上，实时检测留在第六节。PX4 250 框架还没开始读。
