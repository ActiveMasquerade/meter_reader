import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from meter_interfaces.srv import ReaderService


class MeterReaderClient(Node):
    def __init__(self):
        super().__init__('meter_reader_client')

        self.bridge = CvBridge()

        self.sub = self.create_subscription(
            Image,
            '/digital/image',
            self.image_callback,
            10
        )

        self.client = self.create_client(
            ReaderService,
            'read_meter'
        )

        self.get_logger().info("Waiting for /read_meter service...")
        self.client.wait_for_service()
        self.get_logger().info("/read_meter service available")

    def image_callback(self, msg):
        request = ReaderService.Request()
        request.image = msg

        future = self.client.call_async(request)
        future.add_done_callback(self.handle_response)

    def handle_response(self, future):
        try:
            response = future.result()
        except Exception as e:
            self.get_logger().error(f"Service call failed: {e}")
            return

        if response.success:
            self.get_logger().info(
                f"Meter reading received: {response.reading}"
            )
        else:
            self.get_logger().warn("Meter reading failed")


def main():
    rclpy.init()
    node = MeterReaderClient()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
