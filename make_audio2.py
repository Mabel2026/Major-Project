# make_test_audio_gtts.py
from gtts import gTTS

text = (
    "Hello, my name is Michael Jones. "
    "My email is michael.jones at gmail dot com and my phone number is nine eight seven six five four three two one zero. "
    "My home address is 42 Maple Street, Springfield. "
    "Please contact me at michael.jones at example dot com. "
)

tts = gTTS(text)
tts.save("sample_audio_gtts.mp3")
print("Saved sample_audio_gtts.mp3")
