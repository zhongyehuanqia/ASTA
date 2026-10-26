# PX4 250 框架初读

阅读日期：2026-10-14

源码位置：`/home/qia/PX4-Autopilot`（官方仓库浅克隆，提交 `49b856b5`，2026-10-13）。这份源码不放进 `ros-px4-vision`，只在本笔记里记录路径。

这里的「250」对应多旋翼机架配置，不是另一个软件仓库。本机这份固件里有两份：

| 文件 | 机架 |
| --- | --- |
| `ROMFS/px4fmu_common/init.d/airframes/4050_generic_250` | Generic 250 Racer，X 型四旋翼 |
| `ROMFS/px4fmu_common/init.d/airframes/4052_holybro_qav250` | Holybro QAV250 |

它们只改默认参数（姿态增益、最大角速度、电机位置等），状态机和通信代码是所有机型共用的。

桌面上的 `MARTS-Planner-ROS-main/px4ctrl` 是电脑侧的 ROS 控制器。它通过 MAVROS 切 Offboard、解锁，真正的飞行状态仍在飞控固件里。

## 框架图

```text
遥控器 / 地面站 QGroundControl
            |
            |  MAVLink
            v
src/modules/mavlink/mavlink_main.cpp
mavlink_receiver.cpp 收到指令
mavlink_messages.cpp 向外发送状态
            |
            |  转成 uORB 消息（msg/*.msg）
            v
+---------------- 飞控内部 ----------------+
| commander          解锁、模式、整机状态     |
| navigator          任务、返航等自动飞行     |
| mc_pos_control     位置 -> 姿态期望         |
| mc_att_control     姿态 -> 角速度期望       |
| mc_rate_control    角速度 -> 力矩           |
| control_allocator  力矩 -> 四个电机         |
| src/drivers        IMU、GPS、遥控器等       |
+------------------------------------------+
            ^
            |  同一套 MAVLink
电脑上的 px4ctrl（经 MAVROS 切 Offboard）
```

模块之间不互相调用函数传数据，而是发布和订阅 uORB 话题。话题定义在 `msg/`，实现在 `platforms/common/uORB`。

## 目录

| 路径 | 作用 |
| --- | --- |
| `src/modules` | 飞行功能模块，状态机和通信都在这里 |
| `src/drivers` | 传感器、执行器驱动 |
| `msg/` | uORB 消息定义，例如 `VehicleStatus.msg` |
| `ROMFS/px4fmu_common/init.d` | 开机脚本和机架参数，250 机架在 `airframes/` |
| `boards/` | 具体飞控板的硬件配置 |
| `platforms/common/uORB` | 模块之间的通信机制 |

## 状态机在哪

总入口是 `src/modules/commander/`。

| 文件 | 作用 |
| --- | --- |
| `Commander.hpp`、`Commander.cpp` | 总控。用 `vehicle_status.arming_state` 表示是否解锁，并发布 `vehicle_status` |
| `ModeManagement.cpp` | 管理当前飞行模式 |
| `UserModeIntention.cpp` | 记录用户想切换到的模式 |
| `HealthAndArmingChecks/` | 解锁前检查传感器、电量等是否允许解锁 |
| `failsafe/` | 失控保护，例如丢失遥控后的处理 |
| `src/modules/navigator/` | 自动任务怎么飞。模式能不能进，先由 commander 决定 |

看状态时先搜这两个字段：`arming_state`（解锁状态）、`nav_state`（当前飞行模式）。

## 通信在哪

对外是 MAVLink，对内是 uORB。

| 文件 | 作用 |
| --- | --- |
| `src/modules/mavlink/mavlink_main.cpp` | MAVLink 模块入口，和地面站、机载电脑通信 |
| `src/modules/mavlink/mavlink_receiver.cpp` | 接收地面站或电脑发来的命令 |
| `src/modules/mavlink/mavlink_messages.cpp` | 把飞控状态打包发出去 |
| `platforms/common/uORB` | 飞控内部的发布/订阅 |
| `msg/VehicleStatus.msg` | 整机状态这条消息的字段定义 |

`px4ctrl` 里的 `toggle_offboard_mode()` 走的是 MAVROS，最后会变成飞控收到的模式切换命令，再进入 commander。

## 问题清单

1. `arming_state` 和 `nav_state` 各有哪些取值，解锁成功后 `nav_state` 会不会立刻变成 Offboard？
2. 用户拨遥控器切换模式时，先改的是 `UserModeIntention` 还是 `ModeManagement`？
3. 地面站发来的解锁命令，从 `mavlink_receiver.cpp` 到 `vehicle_command` 中间经过哪几个函数？
4. `4050_generic_250` 和 `4052_holybro_qav250` 除了参数，硬件接线有没有差别？
5. 位置控制、姿态控制、角速度控制三个模块，谁的输出是谁的输入？
6. `msg/VehicleStatus.msg` 和代码里的 `vehicle_status_s` 是怎么对应上的？
7. 这次只克隆了主仓库，没有拉子模块。读框架够不够，什么时候才需要把 `boards` 依赖的系统也拉下来？
8. `px4ctrl` 切 Offboard 失败时，应该先看 MAVROS 的连接，还是先看 commander 的解锁检查？
