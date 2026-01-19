# test_analyzer.py
from video_analyzer import analyze_video
import json

# Test with your video
video_path = "your_video.mp4"  # Replace with your video path
results = analyze_video(video_path, frame_stride=10, max_detections=20)

print(f"\n📊 PRIVACY REPORT ({len(results)} findings):")
for detection in results:
    print(f"[{detection['timestamp']}s] {detection['type']}: {detection.get('content', detection.get('count', ''))}")

# Save report
with open("privacy_report.json", "w") as f:
    json.dump(results, f, indent=2)
print("\n💾 Report saved: privacy_report.json")
