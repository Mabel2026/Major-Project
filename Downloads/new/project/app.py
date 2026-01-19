# app.py
import os
import time
import uuid
import tempfile
from flask import (
    Flask, request, render_template, send_from_directory, url_for, jsonify
)

from metadata_tools import (
    extract_metadata, remove_metadata, extract_tags,
    IMAGE_EXTS, MEDIA_EXTS
)
from video_analyzer import analyze_video

app = Flask(__name__)

BASE_UPLOAD = "uploads"
INPUT_FOLDER = os.path.join(BASE_UPLOAD, "input")
OUTPUT_FOLDER = os.path.join(BASE_UPLOAD, "output")

os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["INPUT_FOLDER"] = INPUT_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

ALLOWED_EXT = IMAGE_EXTS + MEDIA_EXTS


def allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXT


# ---------- METADATA PAGES ----------

@app.route("/")
def home():
    return render_template("upload.html")


@app.route("/uploads/input/<path:filename>")
def serve_input(filename):
    return send_from_directory(app.config["INPUT_FOLDER"], filename)


@app.route("/uploads/output/<path:filename>")
def serve_output(filename):
    return send_from_directory(app.config["OUTPUT_FOLDER"], filename)


@app.route("/download/<path:filename>")
def download_file(filename):
    return send_from_directory(
        app.config["OUTPUT_FOLDER"],
        filename,
        as_attachment=True
    )


@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return "No file part", 400
    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400
    if not allowed_file(file.filename):
        return "Unsupported file type", 400

    ext = os.path.splitext(file.filename)[1].lower()

    in_name = f"input_{uuid.uuid4().hex}{ext}"
    out_name = f"output_{uuid.uuid4().hex}{ext}"

    in_path = os.path.join(app.config["INPUT_FOLDER"], in_name)
    out_path = os.path.join(app.config["OUTPUT_FOLDER"], out_name)

    file.save(in_path)

    meta_before_full = extract_metadata(in_path)

    ok = remove_metadata(in_path, out_path)
    if not ok:
        return "Failed to remove metadata", 500

    meta_after_full = extract_metadata(out_path)

    hide_metadata = request.form.get("hide_metadata") == "1"

    metadata_before = meta_before_full
    if hide_metadata:
        metadata_after = extract_tags(meta_after_full)
    else:
        metadata_after = meta_after_full

    input_url = url_for("serve_input", filename=in_name)
    output_url = url_for("serve_output", filename=out_name)

    return render_template(
        "result.html",
        input_file=input_url,
        output_file=output_url,
        metadata_before=metadata_before,
        metadata_after=metadata_after,
        cleaned_filename=out_name,
        ts=int(time.time()),
    )


# ---------- VIDEO PRIVACY MODULE ----------

@app.route("/video")
def video_home():
    return render_template("video.html")


@app.route("/video/analyze", methods=["POST"])
def video_analyze_route():
    if "video" not in request.files:
        return jsonify({"error": "No video uploaded"}), 400

    video = request.files["video"]
    if video.filename == "":
        return jsonify({"error": "No file selected"}), 400

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    video.save(temp_file.name)
    temp_file.close()

    try:
        detections = analyze_video(temp_file.name)
    except Exception as e:
        print("Video analysis failed:", e)
        detections = []
    finally:
        try:
            os.remove(temp_file.name)
        except OSError:
            pass

    return jsonify({
        "status": "Analysis Complete",
        "video_name": video.filename,
        "detections": detections
    })


@app.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


if __name__ == "__main__":
    app.run(debug=True)
