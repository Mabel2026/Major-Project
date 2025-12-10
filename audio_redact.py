import whisper
import re
from pydub import AudioSegment

# ------------------------------
# Step 1: Load Whisper Model
# ------------------------------
model = whisper.load_model("base")

# ------------------------------
# Step 2: Transcribe Audio with Word Timestamps
# ------------------------------
result = model.transcribe("sample_audio3.mp3", word_timestamps=True)
text = result["text"]
print("Original Transcription:", text)

# Normalize transcript
normalized_text = text.replace(" at ", "@")
normalized_text = re.sub(r'(\d)\.(\d)', r'\1\2', normalized_text)  # fix decimals

# ------------------------------
# Step 3: Detect Emails & Phone Numbers
# ------------------------------
emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", normalized_text)
phones = re.findall(r'\b\d{7,15}\b', normalized_text)
name = "John Doh"  # adjust as needed

print("Emails found:", emails)
print("Phone numbers found:", phones)

# ------------------------------
# Step 4: Flatten word-level segments
# ------------------------------
word_list = []
for seg in result['segments']:
    if 'words' in seg:
        for w in seg['words']:
            w_text = w['word'].replace(" at ", "@")
            w_text = re.sub(r'(\d)\.(\d)', r'\1\2', w_text)
            word_list.append({'word': w_text, 'start': w['start'], 'end': w['end']})

# ------------------------------
# Step 5: Sentence splitting (no NLTK)
# ------------------------------
sentences = re.split(r'(?<=[.!?])\s+', normalized_text)

def map_sentence_to_segments(sentence, word_list):
    """ Map full sentence to start/end timestamps """
    words_in_sentence = []
    for w in word_list:
        if w['word'].lower() in sentence.lower():
            words_in_sentence.append(w)
    if words_in_sentence:
        return (words_in_sentence[0]['start'], words_in_sentence[-1]['end'])
    return None

# Find sentences containing sensitive info
sensitive_segments = []
for sentence in sentences:
    if any(s in sentence for s in [name] + emails + phones):
        seg = map_sentence_to_segments(sentence, word_list)
        if seg:
            sensitive_segments.append(seg)

print("Sensitive sentence segments:", sensitive_segments)

# ------------------------------
# Step 6: Merge overlapping segments
# ------------------------------
sensitive_segments = sorted(sensitive_segments, key=lambda x: x[0])
merged_segments = []
for seg in sensitive_segments:
    if not merged_segments:
        merged_segments.append(seg)
    else:
        prev_start, prev_end = merged_segments[-1]
        curr_start, curr_end = seg
        if curr_start <= prev_end:  # overlap
            merged_segments[-1] = (prev_start, max(prev_end, curr_end))
        else:
            merged_segments.append(seg)
sensitive_segments = merged_segments

# ------------------------------
# Step 7: Load Audio
# ------------------------------
audio = AudioSegment.from_file("sample_audio3.mp3")

# ------------------------------
# Step 8: User choice - mute or trim
# ------------------------------
choice = input("Enter 1 to mute, 2 to trim sensitive sentences: ")

if choice == "1":
    # Mute sensitive sentence segments
    for start, end in sensitive_segments:
        start_ms = max(0, int(start * 1000))
        end_ms = min(len(audio), int(end * 1000))
        silence = AudioSegment.silent(duration=(end_ms - start_ms))
        audio = audio[:start_ms] + silence + audio[end_ms:]
    audio.export("redacted_audio_sent_muted.mp3", format="mp3")
    print("Redacted audio saved as 'redacted_audio_sent_muted.mp3'")

elif choice == "2":
    # Trim full sensitive sentences
    output_audio = AudioSegment.empty()
    prev_end = 0
    for start, end in sensitive_segments:
        start_ms = max(0, int(start * 1000))
        end_ms = min(len(audio), int(end * 1000))
        output_audio += audio[prev_end:start_ms]
        prev_end = end_ms
    output_audio += audio[prev_end:]
    output_audio.export("redacted_audio_sent_trimmed.mp3", format="mp3")
    print("Redacted audio saved as 'redacted_audio_sent_trimmed.mp3'")

else:
    print("Invalid choice. No audio redaction performed.")

# ------------------------------
# Step 9: Redact transcript
# ------------------------------
redacted_text = normalized_text
for sentence in sentences:
    if any(s in sentence for s in [name] + emails + phones):
        redacted_text = redacted_text.replace(sentence, "[REDACTED_SENTENCE]")

print("Redacted Transcript:", redacted_text)
