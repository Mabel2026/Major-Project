# app.py
import os
import uuid
import time
from flask import Flask, request, render_template, send_from_directory, url_for

from metadata_tools import (
    extract_metadata,
    remove_metadata,
    extract_tags,
    IMAGE_EXTS,
    MEDIA_EXTS,
)

app = Flask(__name__)

# --------- FOLDERS ---------
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


# --------- ROUTES ---------

@app.route("/")
def home():
    # main metadata upload UI
    return render_template("upload.html")


# NEW: video analysis page (HTML you already have separately)
@app.route("/video")
def video_home():
    return render_template("video.html")


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

    input_filename = f"input_{uuid.uuid4().hex}{ext}"
    output_filename = f"output_{uuid.uuid4().hex}{ext}"

    input_path = os.path.join(app.config["INPUT_FOLDER"], input_filename)
    output_path = os.path.join(app.config["OUTPUT_FOLDER"], output_filename)

    file.save(input_path)

    meta_before_full = extract_metadata(input_path)

    success = remove_metadata(input_path, output_path)
    if not success:
        return "Failed to remove metadata", 500

    meta_after_full = extract_metadata(output_path)

    metadata_before = extract_tags(meta_before_full)
    metadata_after = extract_tags(meta_after_full)

    input_url = url_for("serve_input", filename=input_filename)
    output_url = url_for("serve_output", filename=output_filename)

    return render_template(
        "result.html",
        input_file=input_url,
        output_file=output_url,
        metadata_before=metadata_before,
        metadata_after=metadata_after,
        cleaned_filename=output_filename,
        ts=int(time.time()),
    )


@app.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


if __name__ == "__main__":
    app.run(debug=True)
