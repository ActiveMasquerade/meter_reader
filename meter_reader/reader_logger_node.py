import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MeterReaderClient(Node):
    def __init__(self):
        super().__init__('meter_reader_client')

       

        self.sub = self.create_subscription(
            String,
            '/meter_reading',
            self.image_callback,
            10
        )


        
    def image_callback(self, msg):
        self.get_logger().info(str(msg.data)+" is the reading")

   

def main():
    rclpy.init()
    node = MeterReaderClient()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
