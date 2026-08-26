"""
test_camera_stream.py - Test script for live camera barcode/QR scanning
"""

import cv2
import time
import vision_scanner
import excel_logger

def test_stream():
    scanner = vision_scanner.VisionScanner(debounce_seconds=2.0)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return
    
    print("Webcam opened successfully. Capturing 5 frames...")
    for i in range(5):
        ret, frame = cap.read()
        if ret:
            annotated, all_det, new_items = scanner.process_frame(frame, auto_debounce=True)
            print(f"Frame {i+1}: Detected {len(all_det)} codes, {len(new_items)} new items to log.")
        time.sleep(0.1)
        
    cap.release()
    print("Webcam stream test completed.")

if __name__ == "__main__":
    test_stream()
