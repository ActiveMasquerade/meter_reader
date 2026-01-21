import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge


class DigitalReader(Node):
    def __init__(self):
        super().__init__('digital_reader')

        self.bridge = CvBridge()

        self.sub = self.create_subscription(
            Image,
            '/digital/image',
            self.callback,
            10
        )

        self.pub = self.create_publisher(
            String,
            '/meter/reading',
            10
        )

        self.get_logger().info("Digital reader started")

    def callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(
                msg, desired_encoding='bgr8'
            )
        except Exception as e:
            self.get_logger().warn(str(e))
            return

       
        reading = "UNREAD"  

        out = String()
        out.data = reading
        self.pub.publish(out)

        self.get_logger().info(f"Published meter reading: {reading}")


def main():
    rclpy.init()
    node = DigitalReader()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
