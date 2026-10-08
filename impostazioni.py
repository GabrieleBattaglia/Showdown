"""
Le impostazioni di MESS: dimensione dei caratteri, colori del testo e dello sfondo, volume degli effetti e della partita, velocità di gioco.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 5 del piano, secondo la decisione D12, sul modello di Terminal
Beast e di Tornello: i colori sono percentuali di rosso, verde e blu, da 0 a 100, e il valore
predefinito è il verde su nero a 12 punti degli altri due programmi. Si salvano nel file
mess_impostazioni.json accanto al programma, fuori da git come in Tornello, perché descrivono la
macchina e non il mondo. Un file mancante o rovinato non ferma niente: valgono i predefiniti.
Dal 2026-10-07, con la decisione D24, c'è anche il volume degli effetti sonori, da 0 a 100: a 50,
il predefinito, i suoni sono come li ha pensati chi li ha fatti, e a zero tacciono.
Dal 2026-10-08, con la decisione D29, c'è la velocità di gioco della partita dal vivo, da 1 a 8, e i
modi di seguire l'amichevole diventano Assisti e Vai alla fine, con i valori di prima migrati.
Con la decisione D30, lo stesso giorno, la velocità di gioco parte da 4, e chi l'ha già salvata la
ritrova com'era; e la partita ha un volume suo, da 0 a 100, accanto a quello degli effetti.
"""

import contextlib
import json
import os

import percorsi

FILE_IMPOSTAZIONI = "mess_impostazioni.json"
DIMENSIONE_MINIMA = 8
DIMENSIONE_MASSIMA = 72
VOLUME_MINIMO = 0
VOLUME_MASSIMO = 100
# Le opzioni dell'amichevole si ricordano, scelta di Gabriele dell'8 ottobre 2026: i valori sono
# quelli del dialogo OpzioniAmichevole e del livello della cronaca del motore, scritti qui per non far
# dipendere le impostazioni dalla finestra.
SET_DELL_AMICHEVOLE = (3, 5)
# Con la decisione D29 i modi di seguire l'amichevole sono due, Assisti e Vai alla fine. I valori
# ricordati dalla tappa 9 si migrano: il punto alla volta diventa Assisti, che è la partita dal vivo,
# tutta subito e solo il risultato diventano Vai alla fine, che mostra il risultato e la cronaca.
MODI_DELL_AMICHEVOLE = ("assisti", "fine")
MODI_DI_PRIMA = {"punto": "assisti", "tutta": "fine", "risultato": "fine"}
LIVELLI_DELL_AMICHEVOLE = ("sintetica", "normale", "tecnica")
# La velocità di gioco della decisione D12, nella forma di D29: divide le pause e la procedura
# dell'arbitro della partita dal vivo, da 1, il tempo reale, a 8. Con D30 parte da 4: pause e
# procedura a un quarto del tempo reale. Vale solo per chi non l'ha mai salvata.
VELOCITA_MINIMA = 1
VELOCITA_MASSIMA = 8
VELOCITA_PREDEFINITA = 4
# Il volume della partita dal vivo, decisione D30, da 0 a 100 come quello degli effetti ma a parte:
# a 95 la partita suona come nell'ascolto libero che Gabriele ha approvato, e a 100 il suo picco più
# alto arriva al tetto senza superarlo. È il VOLUME_DI_PROGETTO di partita_sonora, scritto qui per
# non far dipendere le impostazioni da numpy; una prova controlla che i due valori siano uguali.
VOLUME_PARTITA_PREDEFINITO = 95
PREDEFINITE = {"dimensione": 12, "colore_testo": [0, 100, 0], "colore_sfondo": [0, 0, 0], "volume_effetti": 50,
               "amichevole_set": 3, "amichevole_modo": "assisti", "amichevole_livello": "normale", "velocita_gioco": VELOCITA_PREDEFINITA,
               "volume_partita": VOLUME_PARTITA_PREDEFINITO}


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
    for chiave, minimo, massimo in (("volume_effetti", VOLUME_MINIMO, VOLUME_MASSIMO), ("volume_partita", VOLUME_MINIMO, VOLUME_MASSIMO),
                                    ("velocita_gioco", VELOCITA_MINIMA, VELOCITA_MASSIMA)):
        valore = dati.get(chiave)
        if isinstance(valore, int) and not isinstance(valore, bool) and minimo <= valore <= massimo:
            risultato[chiave] = valore
    modo = dati.get("amichevole_modo")
    if isinstance(modo, str):
        dati = {**dati, "amichevole_modo": MODI_DI_PRIMA.get(modo, modo)}
    for chiave, ammessi in (("amichevole_set", SET_DELL_AMICHEVOLE), ("amichevole_modo", MODI_DELL_AMICHEVOLE), ("amichevole_livello", LIVELLI_DELL_AMICHEVOLE)):
        valore = dati.get(chiave)
        if not isinstance(valore, bool) and valore in ammessi:
            risultato[chiave] = valore
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
