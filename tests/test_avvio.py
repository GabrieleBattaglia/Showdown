"""
Test del programma intero, dall'avvio al salvataggio, con le risposte dell'utente preparate in
un copione e i file in una cartella temporanea: la nascita del mondo, una polisportiva, una
partita, il salvataggio; poi il ritorno, che ricarica il mondo; infine un salvataggio rovinato,
davanti al quale il programma si ferma senza toccare nulla.
"""

import builtins
import random

import pytest

import archivio
import cli
import Showdown
from costanti import FILE_MONDO, FILE_MONDO_COPIA


class Copione:
    """Risponde alle domande del programma con le risposte preparate, controllando che arrivino nell'ordine atteso."""

    def __init__(self, risposte):
        self.risposte = list(risposte)

    def __call__(self, tipo, domanda, dettagli):
        if tipo == "input" or (tipo == "key" and domanda.startswith("...")):
            return ""
        assert self.risposte, f"Copione finito, ma il programma chiede ancora: {domanda!r}"
        atteso, valore = self.risposte.pop(0)
        assert atteso == tipo, f"Attesa una domanda di tipo {atteso}, arrivata una di tipo {tipo}: {domanda!r}"
        return valore() if callable(valore) else valore


@pytest.fixture
def recita(monkeypatch):
    def installa(risposte):
        copione = Copione(risposte)
        monkeypatch.setattr(cli, "menu", lambda d=None, p="> ", **kw: copione("menu", p, {"d": d, **kw}))
        monkeypatch.setattr(cli, "dgt", lambda prompt="", kind="s", **kw: copione("dgt", prompt, kw))
        monkeypatch.setattr(cli, "key", lambda prompt="", **kw: copione("key", prompt, kw))
        monkeypatch.setattr(builtins, "input", lambda prompt="": copione("input", prompt, {}))
        return copione
    return installa


def test_nascita_partita_salvataggio_e_ritorno(cartella_di_prova, recita, capsys):
    random.seed(31)
    mondi = []

    def disponibile(posizione):
        return lambda: sorted(gid for gid, g in mondi[0].giocatori.items() if not g.ritirato and not g.infortunato)[posizione]

    copione = recita([
        ("menu", "MPO"), ("menu", "APR"), ("dgt", "club di prova"), ("dgt", "abc"), ("dgt", "abc"), ("key", "s"), ("menu", None),
        ("menu", "OPA"), ("dgt", disponibile(0)), ("dgt", disponibile(1)), ("dgt", 3), ("menu", "R"),
        ("menu", ""),
    ])
    assert Showdown.avvia(mondi.append)
    assert copione.risposte == []
    schermo = capsys.readouterr().out
    assert "Nessun salvataggio trovato: nasce un mondo nuovo, con 50 giocatori." in schermo
    assert "=== PARTITA TERMINATA ===" in schermo
    assert "Mondo salvato:" in schermo
    documento = archivio.leggi(cartella_di_prova / FILE_MONDO)
    club = documento["mondo"]["polisportive"]["club di prova"]
    assert club["impronta_password"] and "abc" not in club["impronta_password"]
    assert documento["mondo"]["polisportiva_attiva"] == "club di prova"
    giocati = [g for g in documento["mondo"]["giocatori"] if g["partitevinte"] + g["partiteperse"] == 1]
    assert len(giocati) == 2

    recita([("menu", "")])
    assert Showdown.avvia()
    schermo = capsys.readouterr().out
    assert "Mondo caricato:" in schermo and "Polisportiva attiva: club di prova." in schermo
    assert (cartella_di_prova / FILE_MONDO_COPIA).exists()


def test_salvataggio_rovinato_il_programma_si_ferma(cartella_di_prova, recita, capsys):
    (cartella_di_prova / FILE_MONDO).write_text("non è un salvataggio", encoding="utf-8")
    recita([])
    assert not Showdown.avvia()
    schermo = capsys.readouterr().out
    assert "il gioco si ferma qui senza salvare nulla" in schermo
    assert (cartella_di_prova / FILE_MONDO).read_text(encoding="utf-8") == "non è un salvataggio"
    assert not (cartella_di_prova / FILE_MONDO_COPIA).exists()
