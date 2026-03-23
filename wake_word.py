import pvporcupine
import pyaudio
import struct
import time

ACCESS_KEY = "JcZrK1kPoKkw6Y4QHrz2onwxnPq85QDbnExnRJiaxKG8K2R1Xkwy0A=="

def listen_for_wake_word():

    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keywords=["jarvis"]
    )

    pa = pyaudio.PyAudio()

    stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    print("Listening for wake word...")

    try:
        while True:
            pcm = stream.read(
                porcupine.frame_length,
                exception_on_overflow=False
            )
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                print("Wake word detected")
                time.sleep(1.0)   # small cooldown
                return True

    finally:
        stream.close()
        pa.terminate()
        porcupine.delete()