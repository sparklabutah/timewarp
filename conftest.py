"""Make the in-repo ``src/browsergym`` namespace package importable during tests.

Without this, running pytest from a checkout requires the package to be pip
installed (or PYTHONPATH set by hand) before any test can even be collected.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
