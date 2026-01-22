import cv2
import re
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge

# Use the official SDK for cleaner, more robust implementation
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Ensure this import matches your actual service definition
from meter_interfaces.srv import ReaderService

class GeminiReaderService(Node):
    def __init__(self):
        super().__init__('gemini_reader_service')

        self.bridge = CvBridge()

        # 1. Parameter Declarations
        self.declare_parameter('api_key', '')
        self.api_key = self.get_parameter('api_key').get_parameter_value().string_value

        if not self.api_key:
            self.get_logger().fatal("Gemini API key not provided. Shutting down.")
            raise RuntimeError("Gemini API key not provided")

        # 2. Configure Gemini Client
        genai.configure(api_key=self.api_key)
        
        # We use 'gemini-1.5-flash' for speed and low latency
        self.model = genai.GenerativeModel('gemini-2.5-flash')

        # 3. Service Setup
        self.service = self.create_service(
            ReaderService,
            'read_meter',
            self.handle_request
        )

        self.get_logger().info("Gemini Reader Service (v1.5 Flash) is ready.")

    def handle_request(self, request, response):
        try:
            # Convert ROS Image to OpenCV image
            cv_image = self.bridge.imgmsg_to_cv2(
                request.image,
                desired_encoding='bgr8'
            )

            # Query the model
            raw_text = self.query_gemini(cv_image)
            
            # Post-process: Extract only digits/decimals (Robustness fix)
            # This handles cases where the model says "The value is 45.2"
            clean_reading = self.extract_number(raw_text)

            response.reading = clean_reading
            response.success = True
            self.get_logger().info(f"Success: Read '{clean_reading}'")

        except Exception as e:
            self.get_logger().error(f"Failed to read meter: {str(e)}")
            response.reading = ''
            response.success = False
        self.get_logger().info(response)
        return response

    def query_gemini(self, image):
        """
        Sends the image to Gemini using the official SDK.
        """
        # PIL is the native image format for the SDK
        from PIL import Image as PILImage
        
        # Convert BGR (OpenCV) to RGB (PIL)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = PILImage.fromarray(rgb_image)

        # Prompt engineering: Be explicit about formatting
        prompt = (
            "Analyze this digital display. "
            "Identify the main numeric value shown on the screen. "
            "Return ONLY the digits and decimal points. Do not include units or text."
        )

        # Disable safety settings to prevent false positives on utility text
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # Generate content
        response = self.model.generate_content(
            [prompt, pil_image],
            safety_settings=safety_settings
        )

        return response.text

    def extract_number(self, text):
        """
        Safety net: uses Regex to pull the first valid number found in the response
        just in case the model chats a bit.
        """
        match = re.search(r"[-+]?\d*\.\d+|\d+", text)
        if match:
            return match.group()
        return text.strip() # Fallback to raw text if regex fails

def main():
    rclpy.init()
    try:
        node = GeminiReaderService()
        rclpy.spin(node)
    except Exception as e:
        pass
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()