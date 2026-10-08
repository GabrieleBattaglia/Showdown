"""
Test dell'elenco dei suoni per Acu_Maker, strumenti/elenco_suoni.py, richiesta di Gabriele della
decisione D29: il file suoni_di_mess.txt nella cartella del progetto è aggiornato rispetto alle
mappe della finestra e della partita, una riga per voce con l'azione detta a parole e il nome del
preset, senza separatori grafici né righe vuote. Se la prova fallisce dopo un cambio di mappa, si
rilancia python strumenti/elenco_suoni.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))

import elenco_suoni

import partita_sonora
import suoni

RADICE = Path(__file__).resolve().parent.parent


def test_il_file_dell_elenco_e_aggiornato():
    percorso = RADICE / elenco_suoni.NOME_DEL_FILE
    assert percorso == elenco_suoni.percorso() and percorso.exists(), "manca suoni_di_mess.txt: si scrive con python strumenti/elenco_suoni.py"
    assert percorso.read_text(encoding="utf-8") == elenco_suoni.testo(), "suoni_di_mess.txt non è aggiornato: si rilancia python strumenti/elenco_suoni.py"


def test_una_riga_per_voce_con_l_azione_e_il_preset():
    righe = elenco_suoni.righe()
    voci = len(suoni.EVENTI) + len(partita_sonora.SUONI)
    # Due righe d'intestazione, una per ogni gruppo della finestra e una per la partita, e una per voce.
    assert len(righe) == 2 + len(suoni.GRUPPI) + 1 + voci
    assert all(riga.strip() == riga and riga for riga in righe)
    assert not any(s in riga for riga in righe for s in ("--", "==", "__", "**"))
    for evento, preset in suoni.EVENTI.items():
        azione = suoni.AZIONI[evento]
        assert f"{azione[0].upper()}{azione[1:]}: {preset}." in righe, evento
    for ruolo, preset in partita_sonora.SUONI.items():
        azione = partita_sonora.AZIONI[ruolo]
        assert f"{azione[0].upper()}{azione[1:]}: {preset}." in righe, ruolo
    # I titoli dei gruppi, con quanti suoni hanno, nell'ordine delle mappe.
    titoli = [riga for riga in righe[2:] if not any(riga.endswith(f": {p}.") for p in [*suoni.EVENTI.values(), *partita_sonora.SUONI.values()])]
    assert len(titoli) == len(suoni.GRUPPI) + 1
    assert titoli[-1] == f"{elenco_suoni.TITOLO_DELLA_PARTITA}, {len(partita_sonora.SUONI)} suoni."
    assert all(t.startswith("Finestra, ") for t in titoli[:-1])
