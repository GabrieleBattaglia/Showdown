"""
I luoghi di provenienza di MESS: i comuni italiani, con la provincia, la regione e la popolazione.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-22 con la tappa 13, richiesta di Gabriele: il mondo di MESS è l'Italia, e chiunque nasca,
giocatore o allenatore, riceve un comune di provenienza, che si legge nella sua scheda. La collezione
sta in dati/luoghi_italiani.json, preparata da Gabriele: regione, provincia, comune e abitanti, tutti
comuni, così la popolazione è un peso giusto per l'estrazione, e più un comune è popoloso più è
probabile che un atleta venga di lì. Nel gioco non pesa su niente; servirà ai tornei provinciali,
regionali e al campionato nazionale, più avanti. Il comune si estrae da un caso nato dal numero di chi
nasce, come il temperamento, e il caso del mondo non si tocca. La collezione si legge alla prima
richiesta, come i nomi; se non si legge, nessuno riceve un luogo e l'avviso lo dice.
"""

import bisect
import json
import os
import random

import percorsi
from costanti import FILE_LUOGHI

# Le province che chiedono l'articolo dopo "provincia": le altre vogliono "di".
PROVINCE_CON_ARTICOLO = {
    "L'Aquila": "dell'Aquila", "La Spezia": "della Spezia", "Ogliastra": "dell'Ogliastra", "Medio Campidano": "del Medio Campidano",
    "Sulcis Iglesiente": "del Sulcis Iglesiente", "Gallura Nord-Est Sardegna": "della Gallura Nord-Est Sardegna",
    "Verbano-Cusio-Ossola": "del Verbano-Cusio-Ossola",
}

_tabella = {}
# Le collezioni che non si sono potute leggere, con il motivo, come per i nomi.
avvisi = []


def _carica():
    """La tabella dei comuni, letta una volta: l'elenco nell'ordine del file, le somme cumulate degli abitanti e il comune con provincia e regione."""
    if _tabella:
        return _tabella
    percorso = percorsi.risorsa(os.path.join("dati", FILE_LUOGHI))
    try:
        with open(percorso, encoding="utf-8") as f:
            dati = json.load(f)
    except (OSError, ValueError) as e:
        avvisi.append(f"File {percorso} non leggibile: {e}")
        dati = {}
    comuni, cumulati, dove = [], [], {}
    totale = 0
    for regione, province in dati.items():
        for provincia, luoghi in province.items():
            for comune, abitanti in luoghi.items():
                if isinstance(abitanti, int) and abitanti > 0:
                    totale += abitanti
                    comuni.append(comune)
                    cumulati.append(totale)
                    dove[comune] = (provincia, regione)
    _tabella.update(comuni=comuni, cumulati=cumulati, totale=totale, dove=dove)
    return _tabella


def estrai(seme):
    """Il comune estratto coi pesi della popolazione, da un caso nato dal seme; vuoto se la collezione non c'è."""
    tabella = _carica()
    if not tabella["totale"]:
        return ""
    punto = random.Random(seme).random() * tabella["totale"]
    return tabella["comuni"][bisect.bisect_right(tabella["cumulati"], punto)]


def luogo_del_giocatore(id_giocatore):
    """Il comune di provenienza di un giocatore, dal suo numero."""
    return estrai(f"MESS-luogo-giocatore-{id_giocatore}")


def luogo_dell_allenatore(numero):
    """Il comune di provenienza di un allenatore nato, dal suo numero; l'ex giocatore tiene il suo."""
    return estrai(f"MESS-luogo-allenatore-{numero}")


def provincia_e_regione(comune):
    """La provincia e la regione del comune, o None se non è nella collezione."""
    return _carica()["dove"].get(comune)


def descrivi(comune):
    """La provenienza a parole: Avezzano, provincia dell'Aquila, Abruzzo; il comune da solo se non è nella collezione."""
    dove = provincia_e_regione(comune)
    if dove is None:
        return comune
    provincia, regione = dove
    return f"{comune}, provincia {PROVINCE_CON_ARTICOLO.get(provincia, 'di ' + provincia)}, {regione}"
