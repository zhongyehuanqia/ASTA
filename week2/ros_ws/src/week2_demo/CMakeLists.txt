cmake_minimum_required(VERSION 3.0.2)
project(week2_demo)

find_package(catkin REQUIRED COMPONENTS
  message_generation
  rospy
  std_msgs
)

add_message_files(FILES Detect.msg)
generate_messages(DEPENDENCIES std_msgs)

catkin_package(CATKIN_DEPENDS message_runtime rospy std_msgs)

catkin_install_python(PROGRAMS
  scripts/detector.py
  scripts/printer.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
