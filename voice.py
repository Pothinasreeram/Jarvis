import pyttsx3
import speech_recognition as sr
import threading

is_speaking = False
speech_lock = threading.Lock()


def speak(text):
    global is_speaking

    print("Speaking:", text)

    with speech_lock:
        is_speaking = True

        engine = pyttsx3.init(driverName='sapi5')
        engine.setProperty('rate', 175)

        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[0].id)

        engine.say(text)
        engine.runAndWait()
        engine.stop()

        is_speaking = False


def speaking_status():
    return is_speaking


recognizer = sr.Recognizer()
microphone = sr.Microphone()


def listen():
    with microphone as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)

    try:
        command = recognizer.recognize_google(audio)
        print("You said:", command)
        return command.lower()
    except:
        return ""