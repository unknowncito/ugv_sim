#!/usr/bin/env python3
# WebSocket client -> /cmd_vel (same pattern as tag_goal_sender.py)
# Expects JSON: {"type": "cmd_vel", "data": {"linear": 0.3, "angular": 0.1}}
import json
import math
import threading
import time

import rospy
import websocket
from geometry_msgs.msg import Twist

rospy.init_node("ws_cmd_vel")
URL = rospy.get_param("~url", "ws://localhost:8765")
MAX_V = rospy.get_param("~max_linear", 0.5)     # m/s, safety limit
MAX_W = rospy.get_param("~max_angular", 0.5)    # rad/s, safety limit
TIMEOUT = rospy.get_param("~timeout", 0.5)      # s without messages -> stop

pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1)
lock = threading.Lock()
latest = {"v": 0.0, "w": 0.0, "t": 0.0}         # t = time of last good message


def clamp(x, lim):
    return max(-lim, min(lim, x))


def on_message(ws, message):
    try:
        msg = json.loads(message)
        if msg.get("type") != "cmd_vel":
            return                               # ignore other message types
        data = msg["data"]
        v = float(data["linear"])
        w = float(data["angular"])
        if not (math.isfinite(v) and math.isfinite(w)):
            raise ValueError("not a finite number")
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        rospy.logerr("Bad message: %s", e)
        return
    with lock:
        latest.update(v=clamp(v, MAX_V), w=clamp(w, MAX_W), t=time.monotonic())


def on_open(ws):
    rospy.loginfo("WebSocket connected to %s", URL)


def on_error(ws, error):
    rospy.logerr("WebSocket error: %s", error)


def on_close(ws, code, msg):
    rospy.logwarn("WebSocket closed (%s): %s", code, msg)
    with lock:
        latest.update(v=0.0, w=0.0, t=0.0)       # connection lost -> stop


def ws_thread():
    while not rospy.is_shutdown():
        try:
            ws = websocket.WebSocketApp(URL, on_open=on_open, on_message=on_message,
                                        on_error=on_error, on_close=on_close)
            ws.run_forever(ping_interval=20, ping_timeout=10)
        except Exception as e:
            rospy.logerr("WebSocket exception: %s", e)
        if not rospy.is_shutdown():
            rospy.loginfo("Reconnecting in 3 s...")
            time.sleep(3)


threading.Thread(target=ws_thread, daemon=True).start()

rate = rospy.Rate(10)
was_active = False
while not rospy.is_shutdown():
    with lock:
        v, w, t = latest["v"], latest["w"], latest["t"]
    active = t > 0.0 and (time.monotonic() - t) < TIMEOUT
    if active:
        cmd = Twist()
        cmd.linear.x = v
        cmd.angular.z = w
        pub.publish(cmd)
    elif was_active:
        pub.publish(Twist())                     # one stop command
        rospy.logwarn("No fresh command: stopping")
    was_active = active
    rate.sleep()
