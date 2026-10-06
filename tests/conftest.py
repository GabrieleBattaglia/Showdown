"""
Mette la radice del progetto nel percorso di importazione, così i test trovano i moduli di MESS,
e dirotta in una cartella temporanea tutto ciò che il programma scrive: nessun test tocca i
salvataggi o i registri veri.
"""

import sys
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parent.parent
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))


@pytest.fixture(autouse=True)
def cartella_di_prova(tmp_path, monkeypatch):
    """La cartella in cui il programma scrive, durante i test, è una cartella temporanea."""
    import percorsi
    monkeypatch.setattr(percorsi, "cartella", lambda: str(tmp_path))
    return tmp_path
