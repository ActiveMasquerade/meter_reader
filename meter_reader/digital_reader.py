import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import cv2
import imutils
from imutils.perspective import four_point_transform
from imutils import contours

from sensor_msgs.msg import Image
from cv_bridge import CvBridge


DIGITS_LOOKUP = {
    (1,1,1,0,1,1,1):0,
    (0,0,1,0,0,1,0):1,
    (1,0,1,1,1,1,0):2,
    (1,0,1,1,0,1,1):3,
    (0,1,1,1,0,1,0):4,
    (1,1,0,1,0,1,1):5,
    (1,1,0,1,1,1,1):6,
    (1,0,1,0,0,1,0):7,
    (1,1,1,1,1,1,1):8,
    (1,1,1,1,0,1,1):9
}


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
        self.pub = self.create_publisher(String,"meter_reading",10)

        self.get_logger().info("Digital reader node started")

    def callback(self, msg):
        image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        image = imutils.resize(image, height=500)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5,5), 0)
        edged = cv2.Canny(blurred, 50,200,255)

        cnts = cv2.findContours(
            edged.copy(),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
        displayCnt = None

        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                displayCnt = approx
                break

        warped = four_point_transform(gray, displayCnt.reshape(4, 2))
        output = four_point_transform(image, displayCnt.reshape(4, 2))

        thresh = cv2.threshold(
            warped, 0, 255,
            cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
        )[1]

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1,5))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        cnts = cv2.findContours(
            thresh.copy(),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        cnts = imutils.grab_contours(cnts)

        digitCnts = []

        for c in cnts:
            (x, y, w, h) = cv2.boundingRect(c)
            if w >= 15 and (h >= 30 and h <= 40):
                digitCnts.append(c)

        digitsCnts = contours.sort_contours(
            digitCnts,
            method="left-to-right"
        )[0]

        digits = []

        for c in digitsCnts:
            (x, y, w, h) = cv2.boundingRect(c)
            roi = thresh[y:y + h, x:x + w]

            (roiH, roiW) = roi.shape
            (dW, dH) = (int(roiW * 0.25), int(roiH * 0.15))
            dHC = int(roiH * 0.05)

            segments = [
                ((0,0), (w,dH)),
                ((0,0), (dW, h // 2)),
                ((w - dW, 0), (w,h // 2)),
                ((0, (h // 2) - dHC),(w,(h // 2) + dHC)),
                ((0, h // 2), (dW,h)),
                ((w - dW, h // 2), (w,h)),
                ((0, h - dH), (w, h))
            ]

            on = [0] * len(segments)

            for (i, ((xA, yA), (xB, yB))) in enumerate(segments):
                segROI = roi[yA:yB, xA:xB]
                total = cv2.countNonZero(segROI)
                area = (xB - xA) * (yB - yA)
                if total / float(area) > 0.5:
                    on[i] = 1

            digit = DIGITS_LOOKUP[tuple(on)]
            digits.append(digit)

        value = "{}{}{}".format(*digits)
        
        msg = String()
        msg.data = str(value)
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = DigitalReader()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
