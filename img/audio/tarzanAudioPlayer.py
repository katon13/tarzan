import os
import simpleaudio as sa
from .tarzanAudioCatalog import VOICE_MESSAGES

BASE_PATH = os.path.join(os.path.dirname(__file__), "voice")

def play(message):

    if message not in VOICE_MESSAGES:
        return

    file = os.path.join(BASE_PATH, VOICE_MESSAGES[message])

    wave = sa.WaveObject.from_wave_file(file)
    wave.play()