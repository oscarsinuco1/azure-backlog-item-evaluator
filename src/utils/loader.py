import sys
import threading
import itertools
import time

# === Loader auxiliar ===
class Loader:
    def __init__(self, desc="Procesando...", end="", timeout=0.1):
        self.desc = desc
        self.end = end
        self.timeout = timeout
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._animate)
        self._thread.start()

    def _animate(self):
        for c in itertools.cycle(["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]):
            if not self._running:
                break
            sys.stdout.write(f"\r{self.desc} {c}")
            sys.stdout.flush()
            time.sleep(self.timeout)

    def stop(self):
        self._running = False
        self._thread.join()
        sys.stdout.write("\r" + " " * (len(self.desc) + 10) + "\r")
        sys.stdout.write(f"{self.end}\n")
        sys.stdout.flush()