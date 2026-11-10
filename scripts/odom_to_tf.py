import rospy
import tf
from nav_msgs.msg import Odometry

br = tf.TransformBroadcaster()

def callback(msg):
    pos = msg.pose.pose.position
    rot = msg.pose.pose.orientation
    br.sendTransform(
        (pos.x, pos.y, pos.z),
        (rot.x, rot.y, rot.z, rot.w),
        msg.header.stamp,
        "body_link",
        "world"
    )

rospy.init_node('odom_to_tf')
rospy.Subscriber('/odom', Odometry, callback)
rospy.spin()
