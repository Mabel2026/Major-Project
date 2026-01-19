# metadata_tools.py
import os
import json
import shutil
import subprocess
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS

# ---------------- IMAGE METADATA ----------------

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp")
MEDIA_EXTS = (".mp4", ".mov", ".avi", ".mkv", ".mp3", ".wav", ".m4a", ".flac", ".ogg")


def extract_image_metadata(file_path: str) -> dict:
    """
    Extract EXIF + basic info from image files.
    Supported: jpg, jpeg, png, webp, tiff, bmp.
    """
    ext = file_path.lower()
    if not ext.endswith(IMAGE_EXTS):
        return {}

    try:
        img = Image.open(file_path)

        exif = {}
        # EXIF block (mostly for JPEG/TIFF)
        try:
            raw_exif = img._getexif()
            if raw_exif:
                for tag_id, value in raw_exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif[str(tag)] = str(value)
        except Exception:
            pass

        # Basic info (always shown)
        exif["format"] = str(img.format)
        exif["mode"] = str(img.mode)
        exif["size"] = f"{img.size[0]}x{img.size[1]}"

        return exif
    except Exception as e:
        print("Image metadata extraction error:", e)
        return {}


def remove_image_metadata(input_path: str, output_path: str) -> bool:
    """
    Remove all metadata from images safely.
    Rebuilds the image pixel‑by‑pixel.
    """
    try:
        img = Image.open(input_path)
        print("DEBUG: Image mode:", img.mode, "format:", img.format)

        if img.mode != "RGB":
            img = img.convert("RGB")

        clean_img = Image.new("RGB", img.size)
        clean_img.putdata(list(img.getdata()))

        ext = output_path.lower()
        if ext.endswith(".png"):
            fmt = "PNG"
        elif ext.endswith(".webp"):
            fmt = "WEBP"
        else:
            fmt = "JPEG"

        clean_img.save(output_path, format=fmt)
        print("DEBUG: Saved cleaned image to:", output_path)
        return True
    except Exception as e:
        print("Image metadata removal error:", e)
        return False

# ---------------- AUDIO / VIDEO METADATA ----------------

def extract_media_metadata(file_path: str) -> dict:
    """
    Extract metadata from audio/video using ffprobe (part of FFmpeg).
    Returns a JSON‑like dict (format + streams).
    """
    try:
        if not shutil.which("ffprobe"):
            print("ERROR: ffprobe not found in PATH")
            return {}

        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("ffprobe failed:", result.stderr)
            return {}

        return json.loads(result.stdout or "{}")
    except Exception as e:
        print("Media metadata extraction error:", e)
        return {}


def remove_media_metadata(input_path: str, output_path: str) -> bool:
    """
    Remove all metadata from audio/video using ffmpeg.
    Keeps audio/video streams, strips tags/chapters.
    """
    try:
        if not shutil.which("ffmpeg"):
            print("ERROR: ffmpeg not found in PATH")
            return False

        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-map", "0",
            "-c", "copy",
            "-map_metadata", "-1",
            "-map_chapters", "-1",
            output_path,
            "-y",
        ]

        print("DEBUG: Running FFmpeg command:", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("FFmpeg failed:", result.stderr)
            return False

        print("DEBUG: Metadata removed from media file")
        return True
    except Exception as e:
        print("Media metadata removal error:", e)
        return False

# ---------------- UNIVERSAL WRAPPERS ----------------

def extract_metadata(file_path: str) -> dict:
    """
    Detect file type (image vs audio/video) and extract metadata.
    """
    ext = Path(file_path).suffix.lower()

    if ext in IMAGE_EXTS:
        return extract_image_metadata(file_path)
    elif ext in MEDIA_EXTS:
        return extract_media_metadata(file_path)
    else:
        return {"error": f"Unsupported file type for extraction: {ext}"}


def remove_metadata(input_path: str, output_path: str) -> bool:
    """
    Detect file type (image vs audio/video) and remove metadata.
    """
    ext = Path(input_path).suffix.lower()

    if ext in IMAGE_EXTS:
        return remove_image_metadata(input_path, output_path)
    elif ext in MEDIA_EXTS:
        return remove_media_metadata(input_path, output_path)
    else:
        print("Unsupported file type for removal:", ext)
        return False

# ------------- TAG FILTER FOR DISPLAY --------------

def extract_tags(meta: dict) -> dict:
    """
    For media (ffprobe dict): show user tags + useful technical info.
    For images (Pillow dict): return as-is (EXIF + format/mode/size).
    """
    if not isinstance(meta, dict):
        return {}

    # Image case: your Pillow dict has no "streams" list
    if "streams" not in meta:
        return meta

    result = {}

    # FORMAT-LEVEL
    fmt = meta.get("format", {})
    if isinstance(fmt, dict):
        if fmt.get("tags"):
            result["format_tags"] = fmt["tags"]

        basic_fmt = {}
        for key in ("filename", "format_name", "duration", "bit_rate", "size"):
            if key in fmt:
                basic_fmt[key] = fmt[key]
        if basic_fmt:
            result["format_info"] = basic_fmt

    # STREAM-LEVEL
    streams = meta.get("streams", [])
    stream_list = []
    for s in streams:
        if not isinstance(s, dict):
            continue

        info = {
            "index": s.get("index"),
            "codec_type": s.get("codec_type"),
            "codec_name": s.get("codec_name"),
            "width": s.get("width"),
            "height": s.get("height"),
            "sample_rate": s.get("sample_rate"),
            "channels": s.get("channels"),
        }

        if "tags" in s and s["tags"]:
            info["tags"] = s["tags"]

        info = {k: v for k, v in info.items() if v is not None}
        if info:
            stream_list.append(info)

    if stream_list:
        result["streams"] = stream_list

    if not result:
        result["info"] = "No user or technical metadata found"

    return result
