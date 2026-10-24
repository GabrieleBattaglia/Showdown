"""
Test del banco dei tempi della finestra Mercato e ricerca, strumenti/banco_mercato.py, issue 8: su un
mondo a regime piccolo misura tutte le porte, le ricerche pronte, i filtri a mano e gli ordini senza
errori, e lascia il caso del mondo com'era.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 24 ottobre 2026 col passo 2 della proposta della issue 8.
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))

import banco_mercato as bm

import mercato


def test_il_banco_misura_tutto_su_un_mondo_piccolo():
    random.seed(5)
    prima = random.random()
    random.seed(5)
    mondo = bm.costruisci_mondo(300, 31, lambda riga: None)
    assert random.random() == prima
    assert mondo.miapolisportiva_attiva.nome == "Pat-Bologna" and len(mondo.miapolisportiva_attiva.tesserati) == 12
    assert any(not a.libero for a in mondo.allenatori.values()) and any(a.libero for a in mondo.allenatori.values())
    righe = []
    esito = bm.banco(mondo, 1, righe.append)
    misure = esito["misure"]
    assert {f"apertura di {porta}" for porta in mercato.PORTE} <= set(misure)
    assert all(f"{nome}, a caldo" in misure for _chiave, nome in mercato.PRONTE[1:])
    assert all(f"ordine {nome}" in misure for _chiave, nome in mercato.ORDINI_GIOCATORI)
    assert misure["apertura di mercato"][2] > 0 and misure["apertura di allenatori"][2] > 0
    assert esito["piu_lento"][1][0] < bm.OBIETTIVO
    assert any(riga.startswith("Il ricalcolo a caldo più lento: ") for riga in righe)
