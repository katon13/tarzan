import os
from pathlib import Path
try:
    import simpleaudio as sa
except ImportError:
    sa = None

from .tarzanAudioCatalog import VOICE_MESSAGES

BASE_PATH = Path(__file__).parent / "voice"

def play(message):
    if not sa:
        return
    if message not in VOICE_MESSAGES:
        return

    rel_path = VOICE_MESSAGES[message]
    file_path = (BASE_PATH / rel_path).resolve()

    if not file_path.exists():
        return

    try:
        wave = sa.WaveObject.from_wave_file(str(file_path))
        wave.play()
    except Exception as e:
        print(f"AUDIO ERROR playing {message}: {e}")