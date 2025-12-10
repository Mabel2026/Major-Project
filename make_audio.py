from gtts import gTTS

# Text with fake sensitive info
text = "Hello, my name is John Doe. My email is john.doe@gmail.com and my phone number is nine eight seven six five four three two one zero."

# Convert to speech
tts = gTTS(text)
tts.save("sample_audio.mp3")

print("Audio saved as sample_audio.mp3")
