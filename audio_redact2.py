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
audio_filename = "Intro_AUD.wav"  # REPLACE WITH YOUR FILENAME

result = model.transcribe(audio_filename, word_timestamps=True)
text = result["text"]
print("Original Transcription:", text)

# ------------------------------
# Step 3: Prepare Word List
# ------------------------------
word_list = []
for seg in result['segments']:
    if 'words' in seg:
        for w in seg['words']:
            clean_word = w['word'].strip()
            word_list.append({'word': clean_word, 'start': w['start'], 'end': w['end']})

print(f"Total words processed: {len(word_list)}")

# ------------------------------
# Step 4: Find EXACT Individual Words to Redact
# ------------------------------
words_to_redact = [
    "Tamara",
    "Beggley", 
    "Tammy",
    "Louisville",
    "Kentucky"
]

sensitive_segments = []

print("=== SEARCHING FOR SENSITIVE WORDS ===")
for i, word_info in enumerate(word_list):
    current_word = word_info['word'].lower().strip(' ,.!?;:"')
    
    for target_word in words_to_redact:
        if target_word.lower() == current_word:
            print(f"✓ Found '{word_info['word']}' at position {i}, time: {word_info['start']:.2f}-{word_info['end']:.2f}s")
            sensitive_segments.append((word_info['start'], word_info['end']))

print(f"Found {len(sensitive_segments)} sensitive words to redact")

# ------------------------------
# Step 5: Add small buffers around each word for clean redaction
# ------------------------------
buffered_segments = []
for start, end in sensitive_segments:
    buffered_start = max(0, start - 0.1)
    buffered_end = end + 0.1
    buffered_segments.append((buffered_start, buffered_end))

sensitive_segments = buffered_segments
print("Buffered sensitive segments:", sensitive_segments)

# ------------------------------
# Step 6: Load Audio and Apply PRECISE Redaction
# ------------------------------
if sensitive_segments:
    audio = AudioSegment.from_file(audio_filename)
    
    print("\n=== REDACTION OPTIONS ===")
    print("This will ONLY redact the specific names and locations:")
    print("- 'Tamara', 'Beggley', 'Tammy', 'Louisville', 'Kentucky'")
    print("- All other content will remain intact")
    
    choice = input("Enter 1 to mute, 2 to trim sensitive words: ")
    
    if choice == "1":
        redacted_audio = audio
        for start, end in sensitive_segments:
            start_ms = max(0, int(start * 1000))
            end_ms = min(len(audio), int(end * 1000))
            silence = AudioSegment.silent(duration=(end_ms - start_ms))
            redacted_audio = redacted_audio[:start_ms] + silence + redacted_audio[end_ms:]
        
        output_filename = "redacted_audio_precise_muted.wav"
        redacted_audio.export(output_filename, format="wav")
        print(f"✓ PRECISE redaction complete! Saved as '{output_filename}'")
        print("✓ Only the names and location were muted - all other content preserved!")
        
    elif choice == "2":
        output_audio = AudioSegment.empty()
        prev_end = 0
        
        for start, end in sensitive_segments:
            start_ms = max(0, int(start * 1000))
            end_ms = min(len(audio), int(end * 1000))
            output_audio += audio[prev_end:start_ms]
            prev_end = end_ms
        
        output_audio += audio[prev_end:]
        output_filename = "redacted_audio_precise_trimmed.wav"
        output_audio.export(output_filename, format="wav")
        print(f"✓ PRECISE redaction complete! Saved as '{output_filename}'")
        print("✓ Only the names and location were removed - all other content preserved!")
    
    else:
        print("Invalid choice. No audio redaction performed.")
    
    # ------------------------------
    # Step 7: Create Redacted Transcript
    # ------------------------------
    redacted_text = text
    for word in words_to_redact:
        redacted_text = re.sub(r'\b' + re.escape(word) + r'\b', '[REDACTED]', redacted_text, flags=re.IGNORECASE)
    
    print("\n=== FINAL RESULT ===")
    print("Original Transcript:", text)
    print("Redacted Transcript:", redacted_text)
    print(f"Redacted {len(sensitive_segments)} individual words/phrases")
    print("All other content remains intact!")

else:
    print("No sensitive words detected. Debug info:")
    print("First 30 words:", [w['word'] for w in word_list[:30]])