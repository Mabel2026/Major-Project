# download_models.py
import urllib.request
import os
import requests

print("🚀 Downloading Privacy Detection Models...")

# 1. YuNet Face Detection (OpenCV official)
yunet_url = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
yunet_path = "face_detection_yunet_2023mar.onnx"
if not os.path.exists(yunet_path):
    print("📥 Downloading YuNet...")
    urllib.request.urlretrieve(yunet_url, yunet_path)
    print("✓ YuNet ready")

# 2. YOLOv8n Object Detection (ONNX for OpenCV)
yolo_url = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.onnx"
yolo_path = "yolov8n.onnx"
if not os.path.exists(yolo_path):
    print("📥 Downloading YOLOv8n...")
    urllib.request.urlretrieve(yolo_url, yolo_path)
    print("✓ YOLOv8n ready")

print("✅ All models downloaded!")
