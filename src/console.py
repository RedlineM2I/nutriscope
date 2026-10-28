"""Affichage console : titres, spinner d'activité et chronométrage."""

import contextlib
import functools
import itertools
import sys
import threading
import time

BLUE, YELLOW, BOLD, RESET = "\033[34m", "\033[33m", "\033[1m", "\033[0m"
WIDTH = 60

def title1(text):
    print(f"\n{BLUE}{'=' * WIDTH}{RESET}")
    print(f"{BOLD}{text.upper().center(WIDTH)}{RESET}")
    print(f"{BLUE}{'=' * WIDTH}{RESET}\n")

def title2(text):
    print(f"\n{YELLOW}{BOLD} >> {text.upper()}{RESET}\n")


HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR_LINE = "\r\033[K"
SAVE_CURSOR = "\0337"
RESTORE_CURSOR = "\0338"
FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

_lock = threading.Lock()      # sérialise tous les accès à stdout
_stack = []                   # labels actifs, du plus externe au plus interne
_spinner_active = False
_paused = False               # vrai : le spinner n'écrit plus (voir pause_spinner)


class _SpinnerSafeStdout:
    """
    Remplace sys.stdout tant que le spinner tourne : chaque ligne complète
    efface d'abord la ligne du spinner, pour que print() s'affiche proprement.
    """

    def __init__(self, stream):
        self.stream = stream
        self._buffer = ""

    def write(self, text):
        with _lock:
            self._buffer += text
            if "\n" in self._buffer:
                lines, self._buffer = self._buffer.rsplit("\n", 1)
                self.stream.write(CLEAR_LINE + lines + "\n")
                self.stream.flush()
        return len(text)

    def flush(self):
        pass    # une ligne incomplète attend son "\n", sinon le spinner l'écraserait

    def close_buffer(self):
        """Écrit la ligne incomplète restante (appelé une fois le spinner arrêté).
        Le retour à la ligne évite qu'elle soit effacée par la ligne du timer."""
        with _lock:
            if self._buffer:
                self.stream.write(self._buffer + "\n")
                self._buffer = ""
            self.stream.flush()

    def __getattr__(self, name):
        return getattr(self.stream, name)


def _terminal():
    """Le vrai stdout, même quand il est remplacé par _SpinnerSafeStdout."""
    out = sys.stdout
    return out.stream if isinstance(out, _SpinnerSafeStdout) else out


def _emit(text):
    """Écrit une ligne sans se faire écraser par le spinner en cours."""
    with _lock:
        _terminal().write(CLEAR_LINE + text + "\n")
        _terminal().flush()


log = _emit   # équivalent de print(), conservé pour le code existant


@contextlib.contextmanager
def pause_spinner():
    """
    Place le spinner sur la ligne en dessous d'un affichage qui gère lui-même sa ligne
    (barre tqdm) : sinon les deux se réécrivent la même ligne en alternance (flickering).
    Sans effet si aucun spinner ne tourne.
    """
    global _paused
    with _lock:
        _paused = _spinner_active
        if _paused:
            # Réserve la ligne du dessous pour le spinner, puis remonte : la barre s'affiche ici
            _terminal().write(f"{CLEAR_LINE}\n\033[1A")
            _terminal().flush()
    try:
        yield
    finally:
        with _lock:
            # La barre fermée (tqdm) laisse le curseur sur la ligne du spinner : il y reprend
            _paused = False


def _spin(stop, out):
    frames = itertools.cycle(FRAMES)
    t0 = time.perf_counter()
    with _lock:
        out.write(HIDE_CURSOR)
        out.flush()
    try:
        while not stop.is_set():
            with _lock:
                label = _stack[-1] if _stack else ""
                elapsed = time.perf_counter() - t0
                text = f"{next(frames)} {label}… {elapsed:4.0f}s\033[K"
                if _paused:
                    # Dessine sur la ligne sous le curseur, sans le déplacer
                    out.write(f"{SAVE_CURSOR}\033[1B\r{text}{RESTORE_CURSOR}")
                else:
                    out.write(f"\r{text}")
                out.flush()
            stop.wait(0.1)    # réveil immédiat quand stop est levé
    finally:
        with _lock:
            out.write(CLEAR_LINE + SHOW_CURSOR)
            out.flush()


def timer(func=None, *, label=None, store=None, spinner=True):
    """
    Mesure le temps d'exécution, avec indicateur d'activité animé.

    Utilisable de 5 façons :
        @timer
        @timer(label="chargement")
        @timer(store=timings)                 # timings[nom] = durée
        @timer(label="load", store=timings)
        @timer(spinner=False)                 # sans animation

    Fonctionne sur n'importe quelle fonction OU méthode. Le temps est loggué
    même si la fonction lève. Les timers imbriqués partagent un seul spinner,
    qui affiche toujours l'étape la plus interne. Le spinner est désactivé
    automatiquement hors terminal (fichier, pipe, notebook).
    """

    def decorator(fn):
        name = label or fn.__qualname__       # __qualname__ => "Classe.methode"

        @functools.wraps(fn)                  # garde nom, docstring, signature
        def wrapper(*args, **kwargs):
            global _spinner_active

            with _lock:
                _stack.append(name)
                owns = (
                    spinner
                    and sys.stdout.isatty()
                    and not _spinner_active
                )
                if owns:
                    _spinner_active = True

            stop = thread = safe_stdout = None
            if owns:
                safe_stdout = _SpinnerSafeStdout(sys.stdout)
                sys.stdout = safe_stdout
                stop = threading.Event()
                thread = threading.Thread(target=_spin, args=(stop, safe_stdout.stream), daemon=True)
                thread.start()

            start = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                with _lock:
                    _stack.pop()
                if owns:
                    stop.set()
                    thread.join()
                    safe_stdout.close_buffer()
                    sys.stdout = safe_stdout.stream
                    with _lock:
                        _spinner_active = False
                        sys.stdout.write(SHOW_CURSOR)   # filet de sécurité
                        sys.stdout.flush()
                _emit(f"\n[{name}] {duration:.3f} s")   # ligne vide avant pour aérer
                if store is not None:
                    store[name] = duration


        return wrapper

    # @timer      -> func est la fonction  -> on décore tout de suite
    # @timer(...) -> func est None         -> on renvoie le décorateur
    return decorator(func) if callable(func) else decorator
