import rclpy
from rclpy.node import Node

import cv2
import imutils
import numpy as np

from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge


def has_digital_meter_balanced_from_cv(image_gray):

    blurred = cv2.GaussianBlur(image_gray, (5, 5), 0)

    v = np.median(blurred)
    lower = int(max(0, 0.66 * v))
    upper = int(min(255, 1.33 * v))

    edged = cv2.Canny(blurred, lower, upper)

    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(edged, kernel, iterations=1)

    cnts = cv2.findContours(
        dilated.copy(),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    cnts = imutils.grab_contours(cnts)

    h_img, w_img = image_gray.shape[:2]
    digit_candidates = []

    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)

        aspect_ratio = w / float(h + 1e-6)
        valid_height = (h > h_img * 0.04) and (h < h_img * 0.9)

        if valid_height and (0.12 < aspect_ratio < 1.5):
            digit_candidates.append((x, y, w, h))

    if len(digit_candidates) < 2:
        return False

    digit_candidates.sort(key=lambda b: b[0])

    pairs_found = 0

    for i in range(len(digit_candidates) - 1):
        x1, y1, w1, h1 = digit_candidates[i]
        x2, y2, w2, h2 = digit_candidates[i + 1]

        h_diff = abs(h1 - h2)
        similar_h = h_diff < (max(h1, h2) * 0.35)

        y_start = max(y1, y2)
        y_end = min(y1 + h1, y2 + h2)
        overlap_h = max(0, y_end - y_start)

        min_h = min(h1, h2)
        is_aligned = overlap_h > (min_h * 0.4)

        dist_x = x2 - (x1 + w1)
        is_close = dist_x < (max(w1, w2) * 3.5)

        if similar_h and is_aligned and is_close:
            pairs_found += 1

    return pairs_found > 0

class MeterDifferentiator(Node):
    def __init__(self):
        super().__init__('meter_differentiator')

        self.bridge = CvBridge()

        self.sub = self.create_subscription(
            Image,
            '/image_data',
            self.callback,
            10
        )

        self.digital_pub = self.create_publisher(
            Image, '/digital/image', 10
        )
        self.analog_pub = self.create_publisher(
            Image, '/analog/image', 10
        )

        self.type_pub = self.create_publisher(
            String, '/meter/type', 10
        )

        self.get_logger().info("Meter differentiator started")

    def callback(self, msg):
        try:
            gray = self.bridge.imgmsg_to_cv2(
                msg, desired_encoding='mono8'
            )
        except Exception as e:
            self.get_logger().warn(str(e))
            return

        is_digital = has_digital_meter_balanced_from_cv(gray)

        type_msg = String()
        type_msg.data = 'digital' if is_digital else 'analog'
        self.type_pub.publish(type_msg)

        if is_digital:
            self.digital_pub.publish(msg)
        else:
            self.analog_pub.publish(msg)


def main():
    rclpy.init()
    node = MeterDifferentiator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
