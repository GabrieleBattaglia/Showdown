"""
Strumenti comuni alle prove delle migrazioni del salvataggio: un documento del formato attuale
riportato com'era nel formato 6 o nel formato 5, da cui le prove dei formati più vecchi tolgono il resto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-09 con la tappa 11 e il formato 6; dal 2026-10-13, con la tappa 12, anche il formato 7.
"""

import copy

from costanti import MAPPA_ARCHETIPI_INDOLI

# I campi del giocatore che nascono con il formato 6, oltre ai due rinominati.
CAMPI_DEL_FORMATO_6 = ("programma", "intensita", "talento", "apprendista_rapido", "maturazione", "ambizione", "costanza", "contratto_stipendio",
                       "contratto_scadenza", "rinnovo_stipendio", "rinnovo_scadenza", "proposte_rinnovo", "ultima_trattativa")
# I campi del giocatore che nascono con il formato 7, della tappa 12.
CAMPI_DEL_FORMATO_7 = ("acciacco_fino", "acciacco_calo", "acciacco_giorni", "acciacco_sede")
ARCHETIPO_DELL_INDOLE = {indole: archetipo for archetipo, indole in MAPPA_ARCHETIPI_INDOLI.items()}


def al_formato_6(contenuto):
    """Un documento del formato 7 com'era nel formato 6: senza i campi della tappa 12."""
    vecchio = copy.deepcopy(contenuto)
    for g in vecchio["mondo"]["giocatori"]:
        for campo in CAMPI_DEL_FORMATO_7:
            del g[campo]
    vecchio["formato"] = 6
    return vecchio


def al_formato_5(contenuto):
    """
    Un documento del formato 7 com'era nel formato 5: i punti esperienza interi al posto dei punti
    allenamento, l'archetipo al posto dell'indole, senza i campi nuovi e senza le voci di diario
    delle spese d'allenamento; i conti delle polisportive senza la voce delle buonuscite.
    """
    vecchio = al_formato_6(contenuto)
    for p in vecchio["mondo"]["polisportive"].values():
        del p["conti_del_mese"]["buonuscite"]
        for bilancio in p["bilanci"]:
            del bilancio["buonuscite"]
    for g in vecchio["mondo"]["giocatori"]:
        g["puntiesperienza"] = int(g.pop("punti_allenamento"))
        g["archetipo_allenamento"] = ARCHETIPO_DELL_INDOLE[g.pop("indole")]
        for campo in CAMPI_DEL_FORMATO_6:
            del g[campo]
        g["diario"] = [voce for voce in g["diario"] if "spesa" not in voce]
    vecchio["formato"] = 5
    return vecchio
