"""
Le impostazioni d'aspetto di MESS: dimensione dei caratteri e colori del testo e dello sfondo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 5 del piano, secondo la decisione D12, sul modello di Terminal
Beast e di Tornello: i colori sono percentuali di rosso, verde e blu, da 0 a 100, e il valore
predefinito è il verde su nero a 12 punti degli altri due programmi. Si salvano nel file
mess_impostazioni.json accanto al programma, fuori da git come in Tornello, perché descrivono la
macchina e non il mondo. Un file mancante o rovinato non ferma niente: valgono i predefiniti.
"""

import contextlib
import json
import os

import percorsi

FILE_IMPOSTAZIONI = "mess_impostazioni.json"
DIMENSIONE_MINIMA = 8
DIMENSIONE_MASSIMA = 72
PREDEFINITE = {"dimensione": 12, "colore_testo": [0, 100, 0], "colore_sfondo": [0, 0, 0]}


def _colore_valido(valore):
    return isinstance(valore, list) and len(valore) == 3 and all(isinstance(c, int) and not isinstance(c, bool) and 0 <= c <= 100 for c in valore)


def valide(dati):
    """Le impostazioni ricevute, con i predefiniti al posto dei valori che mancano o non vanno."""
    risultato = {chiave: list(v) if isinstance(v, list) else v for chiave, v in PREDEFINITE.items()}
    if not isinstance(dati, dict):
        return risultato
    dimensione = dati.get("dimensione")
    if isinstance(dimensione, int) and not isinstance(dimensione, bool) and DIMENSIONE_MINIMA <= dimensione <= DIMENSIONE_MASSIMA:
        risultato["dimensione"] = dimensione
    for chiave in ("colore_testo", "colore_sfondo"):
        if _colore_valido(dati.get(chiave)):
            risultato[chiave] = list(dati[chiave])
    return risultato


def carica():
    """Le impostazioni salvate, o i predefiniti se il file manca o non si legge."""
    try:
        with open(percorsi.percorso(FILE_IMPOSTAZIONI), encoding="utf-8") as f:
            return valide(json.load(f))
    except (OSError, ValueError):
        return valide(None)


def salva(impostazioni):
    """Salva le impostazioni; restituisce vero se è riuscito. Scrive prima un file temporaneo, come il mondo."""
    percorso = percorsi.percorso(FILE_IMPOSTAZIONI)
    temporaneo = percorso + ".tmp"
    try:
        with open(temporaneo, "w", encoding="utf-8", newline="\n") as f:
            json.dump(valide(impostazioni), f, ensure_ascii=False, indent=1)
        os.replace(temporaneo, percorso)
    except OSError:
        with contextlib.suppress(OSError):
            os.remove(temporaneo)
        return False
    return True


def da_percentuale(percentuale):
    """Una componente di colore da percentuale, da 0 a 100, a byte, da 0 a 255, con lo stesso conto di Tornello."""
    return max(0, min(255, int(percentuale / 100 * 255)))
