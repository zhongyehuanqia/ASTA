#!/usr/bin/env python3
"""发布节点：每隔一秒往 /detect 发一条检测结果。"""

import rospy
from detect_demo.msg import Detect


def main():
    rospy.init_node("detector")
    pub = rospy.Publisher("/detect", Detect, queue_size=10)
    rate = rospy.Rate(1)
    cx = 0
    while not rospy.is_shutdown():
        msg = Detect()
        msg.label = "blue"
        msg.cx = cx
        msg.cy = 180
        pub.publish(msg)
        rospy.loginfo("publish %s (%d, %d)", msg.label, msg.cx, msg.cy)
        cx = (cx + 20) % 640
        rate.sleep()


if __name__ == "__main__":
    main()
