#!/usr/bin/env python3
"""订阅节点：收到 /detect 后打印类别和像素坐标。"""

import rospy
from detect_demo.msg import Detect


def callback(msg):
    rospy.loginfo("receive %s (%d, %d)", msg.label, msg.cx, msg.cy)


def main():
    rospy.init_node("printer")
    rospy.Subscriber("/detect", Detect, callback, queue_size=10)
    rospy.spin()


if __name__ == "__main__":
    main()
