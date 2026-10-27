#!/usr/bin/env python3
# Simulation only: /cmd_vel (Twist) -> Ackermann steering + rear wheel speeds
import math
import rospy
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64

L = 1.4      # wheelbase (m)
T = 1.1      # track width (m)
R = 0.3      # wheel radius (m)
MAX_STEER = 0.6108
TIMEOUT = 0.5  # stop if no /cmd_vel for this many seconds

rospy.init_node('sim_ackermann_bridge')
ns = '/vehicle/'
pub_fl = rospy.Publisher(ns + 'front_left_steering_controller/command', Float64, queue_size=1)
pub_fr = rospy.Publisher(ns + 'front_right_steering_controller/command', Float64, queue_size=1)
pub_rl = rospy.Publisher(ns + 'rear_left_wheel_controller/command', Float64, queue_size=1)
pub_rr = rospy.Publisher(ns + 'rear_right_wheel_controller/command', Float64, queue_size=1)
last = rospy.Time(0)

def send(fl, fr, wl, wr):
    pub_fl.publish(fl); pub_fr.publish(fr)
    pub_rl.publish(wl); pub_rr.publish(wr)

def cb(msg):
    global last
    last = rospy.Time.now()
    v, w = msg.linear.x, msg.angular.z
    if abs(v) < 1e-3:
        send(0.0, 0.0, 0.0, 0.0)
        return
    delta = math.atan(L * w / v)
    delta = max(-MAX_STEER, min(MAX_STEER, delta))
    if abs(delta) < 1e-4:
        send(0.0, 0.0, v / R, v / R)
        return
    turn_r = L / math.tan(delta)          # signed turning radius
    fl = math.atan(L / (turn_r - T / 2))
    fr = math.atan(L / (turn_r + T / 2))
    wl = v * (turn_r - T / 2) / turn_r / R
    wr = v * (turn_r + T / 2) / turn_r / R
    send(fl, fr, wl, wr)

rospy.Subscriber('/cmd_vel', Twist, cb)
rate = rospy.Rate(10)
while not rospy.is_shutdown():
    if last != rospy.Time(0) and (rospy.Time.now() - last).to_sec() > TIMEOUT:
        send(0.0, 0.0, 0.0, 0.0)
    rate.sleep()
