from gtts import gTTS

text = """
You know, it's funny - I was just thinking about how much I enjoy my morning routine. I usually start with a cup of black coffee while checking emails at michael.rodriguez@innovate.com. The caffeine really helps me focus on complex coding problems.

Speaking of which, I recently moved to a new apartment at 2847 Oakwood Drive in Portland. The neighborhood is fantastic - lots of great coffee shops and parks nearby. My phone number here is 503-555-0189 if you need to reach me quickly.

What I really love about programming is the creative problem-solving aspect. It's like solving puzzles all day long. Last weekend, I went hiking in the Columbia River Gorge - absolutely breathtaking views this time of year.On a personal note, I've been trying to learn guitar during my free time. It's challenging but really rewarding. My friend Emma Chen - you might know her from the marketing team at emma.chen@digitalplus.org - she's been giving me some tips.
If you need any technical documentation, our lead architect Robert Williams has everything you need. You can find him at r.williams@innovate.com or call his direct line at 503-555-0476. He's incredibly knowledgeable about our systems.
Speaking of weekends, I'm planning a trip to visit my family in Phoenix next month. My sister's birthday is on January 22nd, and I haven't seen them since Christmas last year. Family time is so important, don't you think?

Anyway, I should probably get back to work. Feel free to email me anytime at m.rodriguez.personal@gmail.com if you have more questions. Or you can try my cell at 971-555-0330 - though I'm better at responding to emails.

Thanks so much for the conversation! Looking forward to connecting again soon.
"""

tts = gTTS(text)
tts.save("AUD4.wav")
print("✅ Audio generated: test_audio.wav")