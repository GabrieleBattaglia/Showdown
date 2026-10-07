"""
Test degli effetti sonori della decisione D24, senza mai suonare: il conftest sostituisce il motore
con un registratore. La mappa: ogni preset esiste nella collezione, nessuno si ripete, né per nome
né per contenuto, nessuna onda quadra salvo donazione, la firma di MESS su quelli della collezione;
ogni evento è usato nel codice e ogni suono del codice è un evento. Poi il volume, l'altezza della
probabilità d'ingaggio, il motore vero con la scheda audio finta, e la scelta del suono di un
avanzamento del mondo, con il testo della barra di stato che lo accompagna.
"""

import ast
import json
import re
import time
from pathlib import Path

import numpy as np
import pytest
import wx
from GBUtils import Acusticator

import ascolta_suoni
import impostazioni
import suoni
from mondo import Mondo
from utilita import adesso

RADICE = Path(__file__).resolve().parent.parent
# Il motore vero, preso all'importazione: durante le prove il conftest lo sostituisce.
_RIPRODUCI_VERO = suoni._riproduci
# Le funzioni della finestra e dei dialoghi che ricevono un evento sonoro: la posizione
# dell'argomento e il suo nome.
CHIAMATE_CON_SUONO = {
    "suona": (0, "evento"), "in_coda": (0, "evento"), "mostra": (2, "suono"), "avvisa": (2, "suono"),
    "_avviso": (1, "suono"), "_domanda": (2, "suono"), "_concludi": (2, "suono"),
    "_scegli_giocatore": (2, "suono"), "_cifra": (4, "suono"), "_salva_impostazioni": (0, "suono_riuscito"),
    "aggiorna": (None, "suono"),
}


def _sorgenti():
    """I sorgenti del programma che fanno suonare: la radice, senza l'ascolto guidato, e la cartella gui."""
    return [p for p in sorted(RADICE.glob("*.py")) if p.name != "ascolta_suoni.py"] + sorted((RADICE / "gui").glob("*.py"))


def _codice(percorso):
    """Il testo di un sorgente; per suoni.py soltanto quello che segue la mappa, che nomina tutti gli eventi."""
    testo = percorso.read_text(encoding="utf-8")
    if percorso.name == "suoni.py":
        testo = testo.split("\nEVENTI = ", 1)[1]
    return testo


def _costanti(nodo):
    return [n.value for n in ast.walk(nodo) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def _suoni_nel_codice():
    """Le stringhe che il codice passa come evento sonoro: argomenti delle chiamate che suonano, variabili suono e primo, risposte delle funzioni che scelgono un suono."""
    trovati = []
    for percorso in _sorgenti():
        albero = ast.parse(percorso.read_text(encoding="utf-8"))
        for nodo in ast.walk(albero):
            if isinstance(nodo, ast.Call):
                nome = nodo.func.attr if isinstance(nodo.func, ast.Attribute) else getattr(nodo.func, "id", None)
                if nome not in CHIAMATE_CON_SUONO:
                    continue
                posizione, parola = CHIAMATE_CON_SUONO[nome]
                if posizione is not None and len(nodo.args) > posizione:
                    trovati.extend((percorso.name, s) for s in _costanti(nodo.args[posizione]))
                for chiave in nodo.keywords:
                    if chiave.arg == parola:
                        trovati.extend((percorso.name, s) for s in _costanti(chiave.value))
            elif isinstance(nodo, ast.Assign) and any(isinstance(b, ast.Name) and b.id in ("suono", "primo") for b in nodo.targets):
                trovati.extend((percorso.name, s) for s in _costanti(nodo.value))
            elif isinstance(nodo, ast.FunctionDef) and nodo.name in ("_suono_del_problema", "passaggio"):
                for ritorno in ast.walk(nodo):
                    if isinstance(ritorno, ast.Return) and ritorno.value is not None:
                        trovati.extend((percorso.name, s) for s in _costanti(ritorno.value))
    return trovati


# La mappa.

def test_ogni_preset_esiste_nella_collezione():
    mancanti = [preset for preset in suoni.EVENTI.values() if not Acusticator.preset(preset)[0]]
    assert not mancanti, f"preset che non esistono nella collezione: {mancanti}"


def test_nessun_evento_e_nessun_preset_si_ripetono():
    assert sum(len(gruppo) for _titolo, gruppo in suoni.GRUPPI) == len(suoni.EVENTI)
    preset = list(suoni.EVENTI.values())
    assert len(preset) == len(set(preset)), "due eventi con lo stesso preset"
    titoli = [titolo for titolo, _gruppo in suoni.GRUPPI]
    assert len(titoli) == len(set(titoli))


def test_nessun_preset_suona_uguale_a_un_altro():
    impronte = {}
    for evento, preset in suoni.EVENTI.items():
        score, kind, adsr = Acusticator.preset(preset)
        impronta = json.dumps([score, kind, adsr])
        assert impronta not in impronte, f"{evento} suona come {impronte[impronta]}"
        impronte[impronta] = evento


def test_nessuna_onda_quadra_salvo_donazione():
    quadre = [preset for preset in suoni.EVENTI.values() if Acusticator.preset(preset)[1] == 2]
    assert quadre == ["donazione"]
    assert suoni.EVENTI["caffe"] == "donazione"


def test_la_firma_di_mess():
    # Chi crea un suono lo firma nel nome, chi lo usa e basta nella descrizione: così Gabriele lo
    # ritrova in Acu_Maker cercando mess.
    firma = re.compile(r"Usato da: [^.]*\bmess\b")
    senza = [p for p in suoni.EVENTI.values() if not p.startswith("mess_") and not firma.search(Acusticator.descrizione(p))]
    assert not senza, f"preset senza la firma di MESS: {senza}"
    for preset in suoni.EVENTI.values():
        if preset.startswith("mess_"):
            assert Acusticator.descrizione(preset).startswith("MESS, "), preset


def test_ogni_evento_e_usato_nel_codice():
    codice = "".join(_codice(p) for p in _sorgenti())
    inutili = [evento for evento in suoni.EVENTI if f'"{evento}"' not in codice]
    assert not inutili, f"eventi che il codice non fa mai suonare: {inutili}"


def test_ogni_suono_del_codice_e_un_evento():
    trovati = _suoni_nel_codice()
    assert len(trovati) > 100
    sconosciuti = sorted({(file, s) for file, s in trovati if s not in suoni.EVENTI})
    assert not sconosciuti, f"suoni che non sono eventi della mappa: {sconosciuti}"


def test_l_ascolto_guidato_suona_ogni_evento_del_gruppo(suonati, monkeypatch, capsys):
    monkeypatch.setattr(ascolta_suoni.time, "sleep", lambda _secondi: None)
    eventi = next(g for _titolo, g in suoni.GRUPPI if "probabilita_ingaggio" in g)
    ascolta_suoni.ascolta(eventi)
    attesi = [e for evento in eventi for e in ([evento] * len(ascolta_suoni.PERCENTUALI_DI_PROVA) if evento == "probabilita_ingaggio" else [evento])]
    assert suonati == attesi
    assert all(d["sync"] is True and d["fattore"] == 1.0 for d in suonati.dettagli)
    scritto = capsys.readouterr().out
    assert f"1 di {len(eventi)}: " in scritto
    assert "\n\n" not in scritto


def test_l_ascolto_aspetta_il_via_e_filtra_i_gruppi(suonati, monkeypatch, capsys):
    monkeypatch.setattr(ascolta_suoni, "enter_escape", lambda *_a, **_k: False)
    monkeypatch.setattr("sys.argv", ["ascolta_suoni.py", "economia"])
    assert ascolta_suoni.main() == 0
    scritto = capsys.readouterr().out
    gruppi = [titolo for titolo, _g in suoni.GRUPPI if "economia" in titolo.casefold()]
    assert scritto.startswith(f"Ascolto degli effetti sonori di MESS: {len(gruppi)} gruppi, ")
    assert suonati == []
    monkeypatch.setattr("sys.argv", ["ascolta_suoni.py", "nessun gruppo si chiama così"])
    assert ascolta_suoni.main() == 1
    assert suonati == []


def test_l_ascolto_scrive_una_riga_per_voce(tmp_path):
    esiti = ascolta_suoni.Annotazioni(str(tmp_path / "ascolto.txt"))
    esiti.registra("Economia, il mercato", "la saracinesca è troppo lunga")
    esiti.registra("Mondo, i giocatori", "")
    righe = (tmp_path / "ascolto.txt").read_text(encoding="utf-8").splitlines()
    assert len(righe) == 2
    assert righe[0].startswith("Economia, il mercato, ") and righe[0].endswith(": la saracinesca è troppo lunga")
    assert righe[1].endswith(": nessun commento")


# Il volume.

def test_a_volume_zero_non_parte_niente(suonati):
    suoni.imposta_volume(0)
    assert not suoni.suona("avvio")
    assert not suoni.in_coda("uscita")
    assert suonati == []
    suoni.imposta_volume(50)
    assert not suoni.suona("avvio", volume=0)
    assert suoni.suona("avvio")
    assert suonati == ["avvio"]


def test_il_volume_moltiplica_il_suono(suonati):
    assert suoni.volume_effetti() == 50
    suoni.suona("avvio")
    suoni.suona("avvio", volume=100)
    suoni.imposta_volume(25)
    suoni.suona("avvio")
    assert [d["fattore"] for d in suonati.dettagli] == [1.0, 2.0, 0.5]
    suoni.imposta_volume(300)
    assert suoni.volume_effetti() == 100


def test_il_volume_si_legge_dalle_impostazioni(cartella_di_prova):
    assert impostazioni.salva({**impostazioni.PREDEFINITE, "volume_effetti": 70})
    assert suoni.volume_effetti() == 70


@pytest.mark.parametrize(("valore", "letto"), [(0, 0), (100, 100), (37, 37), (101, 50), (-1, 50), (True, 50), ("30", 50), (12.5, 50), (None, 50)])
def test_il_volume_si_valida(valore, letto):
    assert impostazioni.valide({"volume_effetti": valore})["volume_effetti"] == letto


def test_un_evento_sconosciuto_non_ferma_niente(suonati, capsys):
    assert not suoni.suona("nessuno_lo_conosce")
    assert suonati == []
    assert "nessuno_lo_conosce" in capsys.readouterr().err


def test_un_motore_che_si_rompe_non_ferma_niente(monkeypatch, capsys):
    def guasto(*_args):
        raise OSError("scheda audio sparita")

    monkeypatch.setattr(suoni, "_riproduci", guasto)
    assert not suoni.suona("avvio")
    assert "scheda audio sparita" in capsys.readouterr().err


def test_il_suono_in_coda_aspetta_la_fine_dell_altro(app_wx, suonati):
    assert suoni.in_coda("avvio")
    assert suonati == ["avvio"]
    # Un suono in corso per altri tre decimi: il secondo parte dopo, senza bloccare.
    suoni._FINE_DELL_ULTIMO[0] = time.monotonic() + 0.3
    assert suoni.in_coda("mondo_avanzato")
    assert suonati == ["avvio"]
    ciclo = wx.GUIEventLoop()
    wx.CallLater(1000, ciclo.Exit)
    ciclo.Run()
    assert suonati == ["avvio", "mondo_avanzato"]


# L'altezza della probabilità d'ingaggio.

def test_la_probabilita_sposta_l_altezza():
    assert suoni.probabilita_in_semitoni(50) == 0
    assert suoni.probabilita_in_semitoni(100) == pytest.approx(12)
    assert suoni.probabilita_in_semitoni(0) == pytest.approx(-12)
    assert suoni.probabilita_in_semitoni(140) == pytest.approx(12)
    assert suoni.probabilita_in_semitoni(75) > suoni.probabilita_in_semitoni(60)


def test_trasposto():
    score = ["a5", 0.1, 0, 0.5, "p", 0.05, 0, 0, "c4.e4", 0.2, 0, 0.5, 440, 0.1, 0, 0.5]
    alto = suoni.trasposto(score, 12)
    assert alto[0] == pytest.approx(1760)
    assert alto[4] == "p"
    assert alto[8] == "523.659"
    assert alto[12] == pytest.approx(880)
    assert alto[1::4] == score[1::4] and alto[3::4] == score[3::4]
    assert suoni.trasposto(score, 0)[0] == pytest.approx(880)


# Il motore vero, con la scheda audio sostituita: nessun suono esce.

def test_il_motore_moltiplica_i_campioni_e_ricorda_la_durata(monkeypatch):
    mandati = []
    monkeypatch.setattr(Acusticator, "riproduci", lambda buffer, fs=None, sync=False: mandati.append((np.asarray(buffer), sync)) or True)
    preset = suoni.EVENTI["fuoco_vista"]
    score, _kind, _adsr = Acusticator.preset(preset)
    assert _RIPRODUCI_VERO("fuoco_vista", preset, False, 1.0)
    assert suoni.attesa() == pytest.approx(sum(score[1::4]), abs=0.05)
    assert _RIPRODUCI_VERO("fuoco_vista", preset, 2.0, 2.0)
    pieno, doppio = mandati[0][0], mandati[1][0]
    assert mandati[1][1] == 2.0
    assert np.max(np.abs(doppio)) == pytest.approx(2 * np.max(np.abs(pieno)), rel=1e-3)
    assert _RIPRODUCI_VERO("probabilita_ingaggio", suoni.EVENTI["probabilita_ingaggio"], False, 1.0, 12.0)
    assert not _RIPRODUCI_VERO("prova", "mess_preset_che_non_esiste", False, 1.0)
    assert len(mandati) == 3


# L'avanzamento del mondo: un suono solo, con il suo testo per la barra.

def _rapporto(**voci):
    return Mondo.rapporto_vuoto(adesso()) | {"ticks": 1, "giorni": 1} | voci


def test_l_avanzamento_senza_giorni_non_suona():
    assert suoni.evento_avanzamento(Mondo.rapporto_vuoto(adesso())) == (None, None)
    assert suoni.evento_avanzamento(None) == (None, None)


def test_l_ordine_delle_notizie_dell_avanzamento():
    tutto = _rapporto(ticks=3, giorni=3, tuoi_partiti=2, tuoi_non_pagati=3, tuoi_venduti=1, tuoi_usciti=1, tuoi_ritirati=1, tue_bandiere=1,
                      mesi=1, morti=4, poli_chiuse=1, usciti=2, ritirati=5, poli_create=1)
    assert suoni.evento_avanzamento(tutto, salvato=False, ha_polisportive=True) == ("salvataggio_non_riuscito", "mondo avanzato di 3 giorni, non salvato")
    attesi = [
        ("tuoi_partiti", "tuoi_tesserati_partiti", "2 tesserati andati via, non pagati"),
        ("tuoi_non_pagati", "stipendi_non_pagati", "stipendi non pagati, vedi il bilancio"),
        ("tuoi_venduti", "tuo_tesserato_venduto", "1 tuo giocatore venduto"),
        ("tuoi_usciti", "tuo_tesserato_uscito_di_scena", "1 tuo tesserato uscito di scena"),
        ("tuoi_ritirati", "tuo_tesserato_ritirato", "1 tuo tesserato ritirato"),
        ("tue_bandiere", "tuo_tesserato_bandiera", "1 tuo tesserato diventa bandiera"),
        ("mesi", "primo_del_mese", "primo del mese, stipendi pagati"),
    ]
    for chiave, evento, testo in attesi:
        assert suoni.evento_avanzamento(tutto, True, True) == (evento, testo)
        tutto[chiave] = 0
    # Dopo più giorni le notizie del mondo non suonano: le racconta il riepilogo.
    assert suoni.evento_avanzamento(tutto, True, True) == ("mondo_avanzato_piu_giorni", "mondo avanzato di 3 giorni")
    tutto |= {"ticks": 1, "giorni": 1}
    for chiave, evento, testo in [("morti", "notizia_morte", "mondo avanzato, 4 morti"), ("poli_chiuse", "polisportiva_cpu_chiusa", "mondo avanzato, 1 polisportiva chiusa"),
                                  ("usciti", "notizia_uscita_prematura", "mondo avanzato, 2 usciti di scena"), ("ritirati", "notizia_ritiro", "mondo avanzato, 5 ritirati"),
                                  ("poli_create", "polisportiva_cpu_nata", "mondo avanzato, 1 nuova polisportiva")]:
        assert suoni.evento_avanzamento(tutto, True, True) == (evento, testo)
        tutto[chiave] = 0
    assert suoni.evento_avanzamento(tutto, True, True) == ("mondo_avanzato", "mondo avanzato di un giorno")


def test_il_primo_del_mese_suona_solo_a_chi_ha_una_polisportiva():
    assert suoni.evento_avanzamento(_rapporto(mesi=1), True, False) == ("mondo_avanzato", "mondo avanzato di un giorno")
    assert suoni.evento_avanzamento(_rapporto(mesi=1), True, True)[0] == "primo_del_mese"


def test_ogni_suono_dell_avanzamento_e_un_evento_e_il_testo_sta_nella_barra():
    chiavi = ("tuoi_partiti", "tuoi_non_pagati", "tuoi_venduti", "tuoi_usciti", "tuoi_ritirati", "tue_bandiere", "mesi", "morti", "poli_chiuse", "usciti", "ritirati", "poli_create")
    for chiave in chiavi:
        for giorni in (1, 12345):
            for salvato in (True, False):
                evento, testo = suoni.evento_avanzamento(_rapporto(ticks=giorni, giorni=giorni, **{chiave: 999}), salvato, True)
                assert evento in suoni.EVENTI
                assert len(testo) <= 40, testo
