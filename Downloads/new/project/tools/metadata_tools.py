# metadata_tools.py
import json
import shutil
import subprocess
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS

# ---------------- CONSTANTS ----------------

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp")
MEDIA_EXTS = (".mp4", ".mov", ".avi", ".mkv",
              ".mp3", ".wav", ".m4a", ".flac", ".ogg")


# ---------------- IMAGE METADATA ----------------

def extract_image_metadata(file_path: str) -> dict:
    """
    Extract EXIF + basic info from image files.
    """
    ext = file_path.lower()
    if not ext.endswith(IMAGE_EXTS):
        return {}

    try:
        img = Image.open(file_path)

        exif = {}
        # EXIF (JPEG/TIFF)
        try:
            raw_exif = img._getexif()
            if raw_exif:
                for tag_id, value in raw_exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif[str(tag)] = str(value)
        except Exception:
            pass

        # basic info
        exif["format"] = str(img.format)
        exif["mode"] = str(img.mode)
        exif["size"] = f"{img.size[0]}x{img.size[1]}"
        return exif
    except Exception as e:
        print("Image metadata extraction error:", e)
        return {}


def remove_image_metadata(input_path: str, output_path: str) -> bool:
    """
    Remove all image metadata by rebuilding from pixels.
    """
    try:
        img = Image.open(input_path)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        data = list(img.getdata())
        clean = Image.new(img.mode, img.size)
        clean.putdata(data)

        ext = Path(output_path).suffix.lower()
        if ext in (".png", ".webp"):
            fmt = ext[1:].upper()
        else:
            fmt = "JPEG"

        clean.save(output_path, format=fmt)
        return True
    except Exception as e:
        print("Image metadata removal error:", e)
        return False


# ---------------- MEDIA (AUDIO / VIDEO) ----------------

def extract_media_metadata(file_path: str) -> dict:
    """
    Extract metadata from audio/video using ffprobe (JSON).
    """
    try:
        if not shutil.which("ffprobe"):
            print("ERROR: ffprobe not found")
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
    Remove user metadata from audio/video using FFmpeg.
    Re-encode with simple presets; structural info stays but we hide it.
    """
    try:
        if not shutil.which("ffmpeg"):
            print("ERROR: ffmpeg not found")
            return False

        ext = Path(input_path).suffix.lower()

        # simple presets
        if ext in (".mp3", ".wav", ".m4a", ".flac", ".ogg"):
            codec_args = ["-c:a", "aac", "-b:a", "128k"]
        else:
            codec_args = [
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
            ]

        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-map", "0",
            "-map_metadata", "-1",
            "-map_chapters", "-1",
            *codec_args,
            "-y",
            output_path,
        ]

        print("DEBUG:", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("FFmpeg failed:", result.stderr)
            return False

        return True
    except Exception as e:
        print("Media metadata removal error:", e)
        return False


# ---------------- UNIVERSAL WRAPPERS ----------------

def extract_metadata(file_path: str) -> dict:
    ext = Path(file_path).suffix.lower()
    if ext in IMAGE_EXTS:
        return extract_image_metadata(file_path)
    if ext in MEDIA_EXTS:
        return extract_media_metadata(file_path)
    return {"error": f"Unsupported file type: {ext}"}


def remove_metadata(input_path: str, output_path: str) -> bool:
    ext = Path(input_path).suffix.lower()
    if ext in IMAGE_EXTS:
        return remove_image_metadata(input_path, output_path)
    if ext in MEDIA_EXTS:
        return remove_media_metadata(input_path, output_path)
    print("Unsupported file type:", ext)
    return False


# ---------------- SUMMARY FOR DISPLAY (HIDE TECHNICAL AFTER) ----------------

def extract_tags(meta: dict) -> dict:
    """
    For cleaned file: only show human‑style tags; hide technical fields.
    If nothing remains, return {"info": "No metadata found"}.
    """
    if not isinstance(meta, dict):
        return {}

    result = {}

    # ----- IMAGE CASE -----
    if "streams" not in meta:
        ignore = {"format", "mode", "size", "width", "height"}
        user_meta = {k: v for k, v in meta.items() if k not in ignore}
        if not user_meta:
            return {"info": "No metadata found"}
        return user_meta

    # ----- MEDIA CASE -----
    def filter_tag_dict(tag_dict: dict) -> dict:
        keep_keys = {
            "title", "artist", "album", "album_artist", "composer",
            "comment", "description", "genre", "lyrics", "encoder",
            "encoded_by", "creation_time", "location", "language",
            "publisher", "track", "disc", "show", "episode_id"
        }
        return {k: v for k, v in tag_dict.items() if k.lower() in keep_keys}

    fmt = meta.get("format", {})
    if isinstance(fmt, dict) and "tags" in fmt:
        ft = filter_tag_dict(fmt["tags"])
        if ft:
            result["format_tags"] = ft

    streams = meta.get("streams", [])
    stream_tags = []
    for s in streams:
        if not isinstance(s, dict) or "tags" not in s:
            continue
        st = filter_tag_dict(s["tags"])
        if st:
            stream_tags.append({
                "index": s.get("index"),
                "codec_type": s.get("codec_type"),
                "tags": st,
            })
    if stream_tags:
        result["stream_tags"] = stream_tags

    if not result:
        result["info"] = "No metadata found"
    return result
