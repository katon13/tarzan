import os
from pathlib import Path
try:
    import simpleaudio as sa
except ImportError:
    sa = None

try:
    import winsound
except ImportError:
    winsound = None

from .tarzanAudioCatalog import VOICE_MESSAGES

BASE_PATH = Path(__file__).parent / "voice"

def play(message):
    if not sa and not winsound:
        return
    if message not in VOICE_MESSAGES:
        return

    rel_path = VOICE_MESSAGES[message]
    file_path = (BASE_PATH / rel_path).resolve()

    if not file_path.exists():
        return

    try:
        if sa:
            wave = sa.WaveObject.from_wave_file(str(file_path))
            wave.play()
        elif winsound:
            # SND_FILENAME | SND_ASYNC - odtwarzaj asynchronicznie z pliku
            winsound.PlaySound(str(file_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        print(f"AUDIO ERROR playing {message}: {e}")