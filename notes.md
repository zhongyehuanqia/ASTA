# 算法组第一轮学习笔记

姓名：zhongyehuanqia

日期：2026-10-11

仓库链接：https://github.com/zhongyehuanqia/algo-week1

## 一、任务清单

- 完成了什么
  - [ ] VS Code 打开本仓库
  - [x] Git 配置姓名和邮箱
  - [x] 本地仓库初始化，并完成第一次提交
  - [ ] 推到 GitHub（远程已添加，本机还没有登录，尚未推上去）
  - [ ] 终端运行 `git status`、`git log` 并截图
- 没完成什么
  - YOLO 检测（Day 4–6）
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

截图保存为 `shots/git-status-log.png`，并在下面写一句你看到了什么。

- 截图：
- 说明：

### 3. 推到远程

远程仓库：https://github.com/zhongyehuanqia/algo-week1.git

```bash
git remote add origin https://github.com/zhongyehuanqia/algo-week1.git
git push -u origin main
```

## 三、报错库

| 日期 | 模块 | 报错/现象 | 原因 | 解决 | 参考 |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

## 四、代码/文件

| 文件路径 | 作用说明 |
| --- | --- |
| `notes.md` | 学习笔记，最后整份交到飞书 |
| `shots/` | 操作截图 |

## 五、小结与疑问

- 学到了什么
- 还没懂什么
