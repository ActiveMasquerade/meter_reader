
import os
import cv2

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class FakeSensor(Node):
    def __init__(self):
        super().__init__('fake_sensor')

        self.declare_parameter('image_folder', '')
        self.declare_parameter('publish_rate', 1.0)
        self.declare_parameter('loop', True)

        folder = self.get_parameter('image_folder').get_parameter_value().string_value
        self.loop = self.get_parameter('loop').get_parameter_value().bool_value
        rate = self.get_parameter('publish_rate').get_parameter_value().double_value

        if not folder or not os.path.isdir(folder):
            raise RuntimeError('Invalid image folder')

        self.image_paths = sorted([
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])

        self.index = 0
        self.bridge = CvBridge()
        self.publisher = self.create_publisher(Image, '/image_data', 10)

        self.timer = self.create_timer(1.0 / rate, self.publish_image)

        self.get_logger().info(f'Loaded {len(self.image_paths)} images')

    def publish_image(self):
        if self.index >= len(self.image_paths):
            if self.loop:
                self.index = 0
            else:
                return

        path = self.image_paths[self.index]
        image = cv2.imread(path)

        if image is None:
            self.get_logger().warn(f'Failed to read {path}')
            self.index += 1
            return

        msg = self.bridge.cv2_to_imgmsg(image, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_frame'

        self.publisher.publish(msg)
        self.index += 1


def main():
    rclpy.init()
    node = FakeSensor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
