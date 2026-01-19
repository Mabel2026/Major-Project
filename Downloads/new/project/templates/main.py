main.py

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uuid
import os
import shutil
import whisper
import spacy

# ---------------- INIT ----------------

app = FastAPI(title="REDACTLY Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("⏳ Loading Whisper model...")
whisper_model = whisper.load_model("base")

print("⏳ Loading spaCy model...")
nlp = spacy.load("en_core_web_sm")

print("✅ Models loaded successfully")

# ---------------- HEALTH ----------------

@app.get("/")
def health():
    return {"status": "REDACTLY backend running"}

# ---------------- ANALYZE AUDIO ----------------

@app.post("/analyze/audio")
async def analyze_audio(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    # Keep original file extension
    original_filename = file.filename or "audio"
    file_extension = os.path.splitext(original_filename)[1]
    audio_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_extension}")

    # Save uploaded audio
    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ---------- TRANSCRIPTION ----------
    try:
        result = whisper_model.transcribe(audio_path)
        transcript_text = result.get("text", "").strip()
    except Exception as e:
        print("❌ Transcription error:", e)
        transcript_text = ""

    print("📝 TRANSCRIPT:", transcript_text)

    # ---------- ENTITY EXTRACTION ----------
    entities = []
    if transcript_text:
        doc = nlp(transcript_text)
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "type": ent.label_
            })

    return {
        "file_id": file_id,
        "transcript": transcript_text,
        "entities": entities
    }

# ---------------- REDACT AUDIO ----------------

@app.post("/redact/audio")
async def redact_audio(
    file_id: str = Form(...),
    mode: str = Form("beep"),
    targets: str = Form("")
):
    # Find the file with the given file_id (check all extensions)
    input_audio = None
    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(file_id):
            input_audio = os.path.join(UPLOAD_DIR, filename)
            break
    
    if not input_audio or not os.path.exists(input_audio):
        return {"error": "Audio file not found"}

    # Get the file extension
    _, file_extension = os.path.splitext(input_audio)
    output_audio = os.path.join(OUTPUT_DIR, f"{file_id}_redacted{file_extension}")

    # For now, return same audio (redaction logic already worked earlier)
    shutil.copy(input_audio, output_audio)

    return {
        "download_url": f"/download/{file_id}_redacted{file_extension}"
    }

# ---------------- DOWNLOAD ----------------

@app.get("/download/{filename}")
def download_file(filename: str):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        return {"error": "File not found"}
    return FileResponse(path, media_type="audio/wav", filename=filename)