"""
Le prove del registro degli errori e dei crash, tappa 14, decisione D34, nella cartella temporanea di
ogni prova: senza avvia non fa niente; problema scrive il resoconto con la pila; crash_vero riconosce i
resoconti fatali e ignora le eccezioni di Windows gestite; chiudi toglie il file del crash; il crash
della volta prima si mette da parte, e se non si può resta nel file del crash, che l'uscita non toglie;
lo stderr che il programma compilato non ha diventa il registro. Alla fine di ogni prova il registro si
chiude, e faulthandler torna com'era per pytest.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import faulthandler
import sys

import pytest

import registro

FATALE = "Fatal Python error: Segmentation fault\n\nThread 0x00001234 (most recent call first):\n  File \"mondo.py\", line 1 in avanza\n"
GESTITA = "Windows fatal exception: code 0x8001010d\n\nCurrent thread 0x00001234 (most recent call first):\n  File \"suoni.py\", line 9 in suona\n"


@pytest.fixture(autouse=True)
def registro_chiuso():
    acceso = faulthandler.is_enabled()
    yield
    registro.chiudi()
    if acceso and not faulthandler.is_enabled():
        faulthandler.enable(file=sys.__stderr__)


def _leggi(percorso):
    return percorso.read_text(encoding="utf-8")


def test_senza_avvia_non_fa_niente(tmp_path):
    registro.scrivi("una riga")
    registro.problema(ValueError, ValueError("prova"), None)
    registro.chiudi()
    assert list(tmp_path.iterdir()) == []


def test_problema_scrive_la_pila(tmp_path):
    assert registro.avvia(str(tmp_path)) is None
    registro.scrivi("MESS 2.0.0 si avvia.")
    try:
        raise ValueError("prova")
    except ValueError:
        registro.problema(*sys.exc_info())
    registro.chiudi()
    testo = _leggi(tmp_path / registro.FILE_DEGLI_ERRORI)
    assert "MESS 2.0.0 si avvia." in testo and "Traceback (most recent call last):" in testo
    assert "in test_problema_scrive_la_pila" in testo and testo.rstrip().endswith("ValueError: prova")


@pytest.mark.parametrize(("testo", "vero"), [
    (FATALE, True),
    ("Windows fatal exception: access violation\n", True),
    ("Windows fatal exception: stack overflow\n", True),
    ("Windows fatal exception: code 0xc0000374\n", True),
    (GESTITA, False),
    ("Windows fatal exception: code 0xe24c4a02\n", False),
    ("Windows fatal exception: code 0x406d1388\n", False),
    ("", False),
    (GESTITA + FATALE, True),
])
def test_crash_vero(testo, vero):
    assert registro.crash_vero(testo) is vero


def test_chiudi_toglie_il_file_del_crash(tmp_path):
    registro.avvia(str(tmp_path))
    assert (tmp_path / registro.FILE_DEL_CRASH).exists()
    registro.chiudi()
    assert not (tmp_path / registro.FILE_DEL_CRASH).exists()
    # Senza errori, il registro degli errori non nasce nemmeno.
    assert not (tmp_path / registro.FILE_DEGLI_ERRORI).exists()


def test_il_crash_precedente_si_mette_da_parte(tmp_path):
    (tmp_path / registro.FILE_DEL_CRASH).write_text(FATALE, encoding="utf-8")
    precedente = registro.avvia(str(tmp_path))
    assert precedente == str(tmp_path / registro.FILE_DEL_CRASH_PRECEDENTE)
    assert _leggi(tmp_path / registro.FILE_DEL_CRASH_PRECEDENTE) == FATALE
    assert _leggi(tmp_path / registro.FILE_DEL_CRASH) == ""
    registro.chiudi()
    assert not (tmp_path / registro.FILE_DEL_CRASH).exists() and (tmp_path / registro.FILE_DEL_CRASH_PRECEDENTE).exists()


def test_le_eccezioni_gestite_non_sono_un_crash(tmp_path):
    (tmp_path / registro.FILE_DEL_CRASH).write_text(GESTITA, encoding="utf-8")
    assert registro.avvia(str(tmp_path)) is None
    assert _leggi(tmp_path / registro.FILE_DEL_CRASH) == ""
    assert not (tmp_path / registro.FILE_DEL_CRASH_PRECEDENTE).exists()


def test_il_resoconto_che_non_si_sposta_non_si_perde(tmp_path, monkeypatch):
    crash = tmp_path / registro.FILE_DEL_CRASH
    crash.write_text(FATALE, encoding="utf-8")
    monkeypatch.setattr(registro, "_metti_da_parte", lambda *_argomenti: None)
    assert registro.avvia(str(tmp_path)) == str(crash)
    assert _leggi(crash) == FATALE
    registro.chiudi()
    # L'uscita pulita lo riporta al solo resoconto e lo lascia, per il prossimo avvio.
    assert _leggi(crash) == FATALE
    assert f"resta in {registro.FILE_DEL_CRASH}" in _leggi(tmp_path / registro.FILE_DEGLI_ERRORI)


def test_lo_stderr_del_programma_compilato(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "stderr", None)
    registro.avvia(str(tmp_path))
    assert sys.stderr is not None
    print("Un avviso di una libreria", file=sys.stderr)
    print("su due righe", file=sys.stderr)
    registro.chiudi()
    assert sys.stderr is None
    testo = _leggi(tmp_path / registro.FILE_DEGLI_ERRORI)
    assert "Un avviso di una libreria" in testo and "su due righe" in testo
