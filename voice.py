import pyttsx3
from voice_config import *

engine = pyttsx3.init()

engine.setProperty('rate', VOICE_RATE)
engine.setProperty('volume', VOICE_VOLUME)

voices = engine.getProperty('voices')
if voices and len(voices) > VOICE_INDEX:
    engine.setProperty('voice', voices[VOICE_INDEX].id)


def speak(text: str):
    if not VOICE_ENABLED:
        return

    try:
        if not text:
            return

        short_text = str(text)[:MAX_SPEAK_LENGTH]

        engine.say(short_text)
        engine.runAndWait()

    except Exception as e:
        print("🔇 Voice Error:", e)