"""REG.RU Passenger entry point; Python/CGI must be enabled for the site."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INTERP = Path.home() / "poker-trainer-venv" / "bin" / "python"
if INTERP.is_file() and Path(sys.executable).resolve() != INTERP.resolve():
    os.execl(str(INTERP), str(INTERP), *sys.argv)
if sys.version_info < (3, 11):
    raise RuntimeError("Poker Trainer requires Python 3.11 or newer.")

os.environ.setdefault("POKER_APP_ROOT", str(ROOT))
sys.path.insert(0, str(ROOT / "code" / "server"))

from wsgi import application  # noqa: E402
