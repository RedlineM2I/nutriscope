"""
Musique d'ambiance jouée en tâche de fond pendant les traitements longs.

S'appuie sur l'API MCI de Windows (winmm.dll) via ctypes : pas de dépendance
supplémentaire, et les formats courants (.mp3, .wav) sont gérés.
"""

import ctypes
import sys
import threading
from contextlib import contextmanager
from pathlib import Path

from src.config import BASE_DIR

MUSIC_FILE = BASE_DIR.parent / "assets" / "music.mp3"


def _mci(command):
    """
    Envoie une commande MCI et renvoie sa réponse, ou None en cas d'erreur.
    """
    buffer = ctypes.create_unicode_buffer(256)
    code = ctypes.windll.winmm.mciSendStringW(command, buffer, 255, None)
    return buffer.value if code == 0 else None


class Player:
    """
    Lecteur audio en arrière-plan, rejoué en boucle jusqu'à l'appel de stop().
    """

    def __init__(self, path, alias="nutriscope_bgm", volume=400):
        self.path = Path(path)
        self.alias = alias
        self.volume = volume          # 0 à 1000
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        if _mci(f'open "{self.path}" alias {self.alias}') is None:
            return False
        _mci(f"setaudio {self.alias} volume to {self.volume}")
        _mci(f"play {self.alias}")
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return True

    def _loop(self):
        """
        Relance la lecture depuis le début dès que le morceau est terminé.
        """
        while not self._stop.wait(0.5):
            if _mci(f"status {self.alias} mode") != "playing":
                _mci(f"seek {self.alias} to start")
                _mci(f"play {self.alias}")

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join()
        _mci(f"stop {self.alias}")
        _mci(f"close {self.alias}")


@contextmanager
def background_music(path=MUSIC_FILE, volume=400, play=True):
    """
    Joue un fichier audio en boucle pendant l'exécution du bloc.

    Ne bloque jamais le programme appelant : si la plateforme n'est pas Windows,
    si le fichier est absent ou si MCI refuse de l'ouvrir, on continue en silence.

    :param path: chemin du fichier audio (.mp3, .wav…)
    :param volume: volume de 0 à 1000
    :param play: à False, le bloc s'exécute sans aucune musique
    """
    player = None

    if play and sys.platform == "win32" and Path(path).is_file():
        candidate = Player(path, volume=volume)
        if candidate.start():
            player = candidate

    try:
        yield player
    finally:
        if player is not None:
            player.stop()
