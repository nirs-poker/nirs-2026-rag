"""Development-only Passenger reload on Python source changes (no Docker socket)."""

import hashlib
import time
from pathlib import Path

ROOT = Path('/app')
MARKER = ROOT / 'tmp' / 'restart.txt'


def snapshot():
    paths = sorted((ROOT / 'code' / 'server').rglob('*.py'))
    paths.append(ROOT / 'passenger_wsgi.py')
    return tuple((str(path), hashlib.sha256(path.read_bytes()).digest()) for path in paths)


def main():
    previous = None
    while True:
        try:
            current = snapshot()
            if current != previous:
                # Passenger compares timestamp seconds; avoid losing two quick edits.
                if MARKER.exists() and int(time.time()) <= int(MARKER.stat().st_mtime):
                    time.sleep(1.05)
                MARKER.touch()
                previous = current
                print('Python source changed: Passenger will reload on the next request.', flush=True)
        except OSError as error:
            # Editors can replace files while the snapshot is being read.
            print(f'Reload scan will retry ({type(error).__name__}).', flush=True)
        time.sleep(1)


if __name__ == '__main__':
    main()
