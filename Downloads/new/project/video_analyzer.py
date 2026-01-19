# video_analyzer.py - COMPLETE PRIVACY EXPOSURE DETECTOR
import cv2
import pytesseract
import re
import base64
import numpy as np
import mediapipe as mp
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# COCO Classes for YOLO (privacy-relevant filtered)
COCO_CLASSES = [
    'person', 'laptop', 'cell phone', 'tv', 'book', 'keyboard', 'mouse', 
    'remote', 'oven', 'microwave', 'sink', 'refrigerator', 'book', 'clock'
]

SENSITIVE_PATTERNS = [
    r"\b\d{10}\b",                    # 10-digit phone
    r"\b\d{12}\b",                    # 12-digit ID
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",  # email
    r"\b\d{3}-\d{3}-\d{4}\b",         # 123-456-7890
    r"\b\d{4}\s\d{4}\s\d{4}\s\d{4}\b", # 4 4 4 4 groups
    r"\b\d{16}\b",                    # Credit card
]

# Global detectors
FACE_DETECTOR = None
NET_YOLO = None
MP_FACE = None

def frame_to_base64(frame):
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
    return "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')

def init_detectors():
    global FACE_DETECTOR, NET_YOLO, MP_FACE
    
    # 1. YuNet Face Detector (primary - most accurate)
    try:
        if FACE_DETECTOR is None and os.path.exists("face_detection_yunet_2023mar.onnx"):
            FACE_DETECTOR = cv2.FaceDetectorYN.create(
                "face_detection_yunet_2023mar.onnx", "", (320, 320), 0.9, 0.3, 5000
            )
            print("✓ YuNet loaded")
    except:
        print("⚠ YuNet unavailable, using MediaPipe")
    
    # 2. MediaPipe Fallback
    if MP_FACE is None:
        MP_FACE = mp.solutions.face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )
    
    # 3. YOLOv8 Object Detection
    try:
        if NET_YOLO is None and os.path.exists("yolov8n.onnx"):
            NET_YOLO = cv2.dnn.readNetFromONNX("yolov8n.onnx")
            NET_YOLO.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            NET_YOLO.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            print("✓ YOLOv8 loaded")
    except:
        print("⚠ YOLOv8 unavailable, skipping object detection")

def preprocess_ocr(gray):
    gray = cv2.medianBlur(gray, 3)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    kernel = np.ones((2, 2), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    return thresh

def detect_faces_yunet(gray):
    if FACE_DETECTOR:
        _, faces = FACE_DETECTOR.detect(gray)
        return len(faces) if faces is not None else 0
    return 0

def detect_faces_mediapipe(frame_rgb):
    if MP_FACE:
        results = MP_FACE.process(frame_rgb)
        return len(results.detections) if results.detections else 0
    return 0

def detect_objects_yolo(frame, conf_threshold=0.5):
    if not NET_YOLO:
        return []
    
    blob = cv2.dnn.blobFromImage(frame, 1/255.0, (640, 640), swapRB=True, crop=False)
    NET_YOLO.setInput(blob)
    outputs = NET_YOLO.forward()
    
    h, w = frame.shape[:2]
    privacy_objects = []
    
    for output in outputs[0]:
        scores = output[4:]
        class_id = np.argmax(scores)
        confidence = scores[class_id]
        
        if confidence > conf_threshold and class_id < len(COCO_CLASSES):
            obj_name = COCO_CLASSES[class_id]
            if obj_name in ['person', 'laptop', 'cell phone', 'tv', 'book', 'keyboard']:
                privacy_objects.append(obj_name)
    
    return list(set(privacy_objects))  # Remove duplicates

def analyze_video(video_path: str, frame_stride: int = 5, max_detections: int = 50):
    """Complete privacy exposure analysis"""
    init_detectors()
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": "Cannot open video"}
    
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    detections = []
    frame_index = 0
    
    print(f"🔍 Analyzing {video_path} (FPS: {fps}, stride: {frame_stride})")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_index += 1
        if frame_index % frame_stride != 0:
            continue
        
        timestamp = round(frame_index / fps, 2)
        frame_small = cv2.resize(frame, (640, 360))
        gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
        frame_rgb = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
        
        # 1. FACE DETECTION (YuNet + MediaPipe fallback)
        face_count = detect_faces_yunet(gray)
        if not face_count:
            face_count = detect_faces_mediapipe(frame_rgb)
        
        if face_count > 0:
            detections.append({
                "type": "faces",
                "timestamp": timestamp,
                "image": frame_to_base64(frame_small),
                "count": face_count,
                "frame_index": frame_index
            })
        
        # 2. OBJECT DETECTION
        objects = detect_objects_yolo(frame_small)
        if objects:
            detections.append({
                "type": "objects",
                "timestamp": timestamp,
                "image": frame_to_base64(frame_small),
                "content": ", ".join(objects),
                "frame_index": frame_index
            })
        
        # 3. OCR + SENSITIVE DATA
        ocr_gray = preprocess_ocr(gray)
        text = pytesseract.image_to_string(ocr_gray, config='--psm 6 --oem 3').strip()
        
        if len(text) > 3:
            snippet = text[:100] + "..." if len(text) > 100 else text
            detections.append({
                "type": "text",
                "timestamp": timestamp,
                "image": frame_to_base64(frame_small),
                "content": snippet,
                "frame_index": frame_index
            })
            
            # Check sensitive patterns
            for pattern in SENSITIVE_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    detections.append({
                        "type": "sensitive_text",
                        "timestamp": timestamp,
                        "image": frame_to_base64(frame_small),
                        "content": snippet,
                        "matched": pattern,
                        "frame_index": frame_index
                    })
                    break
        
        if len(detections) >= max_detections:
            print(f"⏹️  Max detections reached: {max_detections}")
            break
    
    cap.release()
    print(f"✅ Analysis complete: {len(detections)} detections")
    return sorted(detections, key=lambda x: x['timestamp'])
