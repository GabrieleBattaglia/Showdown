"""
Test del banco dei tempi della finestra Mercato e ricerca, strumenti/banco_mercato.py, issue 8: su un
mondo a regime piccolo misura tutte le porte, le ricerche pronte, i filtri a mano e gli ordini senza
errori, e lascia il caso del mondo com'era.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 24 ottobre 2026 col passo 2 della proposta della issue 8. Lo stesso giorno le ricerche pronte diventano
i dodici preset di serie. La sera, col motore del costruttore di regole, il banco misura anche le regole, su un mondo
che ha anche gli usciti di scena, e le aperture di Ctrl+K, Ctrl+Maiusc+G e Ctrl+F stanno sotto i 300 ms. Col cambio
della finestra il motore a schede esce, e il banco misura soltanto le regole.
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))

import banco_mercato as bm

import mercato


def test_il_banco_misura_le_regole_coi_ritirati_e_gli_usciti_e_lascia_il_caso_com_era():
    random.seed(5)
    prima = random.random()
    random.seed(5)
    mondo = bm.costruisci_mondo(300, 31, lambda riga: None)
    assert random.random() == prima
    assert mondo.miapolisportiva_attiva.nome == "Pat-Bologna" and len(mondo.miapolisportiva_attiva.tesserati) == 12
    assert any(not a.libero for a in mondo.allenatori.values()) and any(a.libero for a in mondo.allenatori.values())
    ritirati = sum(1 for g in mondo.giocatori.values() if g.ritirato)
    assert mondo._ids_morti_processati_sessione and mondo._ids_morti_processati_sessione < {g.id for g in mondo.giocatori.values() if g.ritirato}
    righe = []
    esito = bm.banco(mondo, 1, righe.append)
    misure = esito["misure"]
    assert set(esito["aperture"]) == set(mercato.PORTE) and esito["aperture"]["mercato"][2] > 0 and esito["aperture"]["allenatori"][2] > 0
    assert all(f"{nome}, a caldo" in misure for _chiave, nome in mercato.PRESET_DI_SERIE)
    assert all(f"{nome}, a caldo" in misure for nome, _regole in bm.REGOLE_A_MANO)
    assert all(f"ordine {nome}" in misure for _chiave, nome in mercato.ORDINI)
    assert misure["ritirati o usciti di scena, a caldo"][2] == ritirati
    assert misure["ordine numero, dal più basso"][2] == len(mondo.giocatori) - ritirati + len(mondo.allenatori)
    assert misure["Mercato e nome rossi"][2] <= misure["Mercato e nome r"][2] <= esito["aperture"]["mercato"][2]
    assert all(esito["aperture"][porta][0] < bm.OBIETTIVO for porta in bm.PORTE_DA_300_MS) and esito["piu_lento"][1][0] < bm.OBIETTIVO
    assert any(riga.startswith("Il ricalcolo a caldo più lento: ") for riga in righe)
    assert any(riga.startswith("L'apertura di amichevole: ") and "del motore di prima" in riga for riga in righe)
