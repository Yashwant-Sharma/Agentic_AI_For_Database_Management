# test_voice.py
import pyttsx3

engine = pyttsx3.init()
engine.say("Hello, how can i help you")
engine.runAndWait()