from gtts import gTTS

# Sample text with natural sensitive info
text = """
Hello everyone, my name is John Doh. 
I am really passionate about technology and programming.
If you ever want to reach me, you can email me at john.doh@example.com. 
Also, you can call me at 9876543210. 
Other than that, I enjoy reading books and going for long walks. 
Thank you for listening.
"""

# Generate speech
tts = gTTS(text=text, lang="en", slow=False)

# Save as MP3
tts = gTTS(text)
tts.save("sample_audio3.mp3")

print("Sample audio generated and saved as sample_audio.mp3")
