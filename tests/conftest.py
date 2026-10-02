"""Mette la radice del progetto nel percorso di importazione, così i test trovano i moduli di MESS."""

import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))
