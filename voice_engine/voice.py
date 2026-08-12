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

        try:
            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=8
            )

        except sr.WaitTimeoutError:
            print("Listening timed out.")
            return ""

    try:
        command = recognizer.recognize_google(audio)
        print("You said:", command)
        return command.lower()

    except sr.UnknownValueError:
        print("Could not understand.")
        return ""

    except sr.RequestError as e:
        print("Speech Recognition Error:", e)
        return ""

    except Exception as e:
        print("Unexpected Error:", e)
        return ""