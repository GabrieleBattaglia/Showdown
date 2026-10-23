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
Dalla tappa 14, il 2026-10-23, richiesta di Gabriele: anche le polisportive appartengono a un territorio,
il comune della sede, con gli stessi pesi. Quelle del computer lo ricevono alla nascita da un caso nato
dal loro nome; quelle dell'utente lo scelgono alla fondazione, cercandolo per nome in un elenco che
dice, accanto a ogni comune, la sua popolazione in percentuale su quella del più popoloso. La ricerca
e la percentuale stanno qui, senza wx, così si collaudano da sole. Le parti della tappa 14 sono di
Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
"""

import bisect
import json
import os
import random
import unicodedata

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


def _chiave(testo):
    """Il testo come lo confronta la ricerca: senza maiuscole né accenti, con apostrofi e trattini come spazi, Forlì come forli, Sant'Angelo come sant angelo."""
    scomposto = unicodedata.normalize("NFD", testo.casefold())
    semplice = "".join(c for c in scomposto if not unicodedata.combining(c))
    # L'apostrofo tipografico, chr(0x2019), è quello che mettono i programmi di scrittura.
    for separatore in ("'", chr(0x2019), "-"):
        semplice = semplice.replace(separatore, " ")
    return " ".join(semplice.split())


def _carica():
    """
    La tabella dei comuni, letta una volta: l'elenco nell'ordine del file, le somme cumulate degli
    abitanti e il comune con provincia e regione; per la ricerca della tappa 14 gli abitanti di ogni
    comune, il più popoloso, i comuni dal più popoloso e la chiave di ricerca di ciascuno.
    """
    if _tabella:
        return _tabella
    percorso = percorsi.risorsa(os.path.join("dati", FILE_LUOGHI))
    try:
        with open(percorso, encoding="utf-8") as f:
            dati = json.load(f)
    except (OSError, ValueError) as e:
        avvisi.append(f"File {percorso} non leggibile: {e}")
        dati = {}
    comuni, cumulati, dove, popolazione = [], [], {}, {}
    totale = 0
    for regione, province in dati.items():
        for provincia, luoghi in province.items():
            for comune, abitanti in luoghi.items():
                if isinstance(abitanti, int) and abitanti > 0:
                    totale += abitanti
                    comuni.append(comune)
                    cumulati.append(totale)
                    dove[comune] = (provincia, regione)
                    popolazione[comune] = abitanti
    per_popolazione = sorted(comuni, key=lambda comune: (-popolazione[comune], _chiave(comune)))
    _tabella.update(comuni=comuni, cumulati=cumulati, totale=totale, dove=dove, abitanti=popolazione, massimo=max(popolazione.values(), default=0),
                    per_popolazione=per_popolazione, chiavi={comune: _chiave(comune) for comune in comuni})
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


def luogo_della_polisportiva(nome):
    """Il comune della sede di una polisportiva, dal suo nome: quelle del computer lo ricevono così alla nascita, e i mondi vecchi nell'aggiornamento."""
    return estrai(f"MESS-luogo-polisportiva-{nome}")


def comune_a_caso():
    """Un comune estratto coi pesi della popolazione da un caso nuovo, senza toccare quello del mondo: la proposta della fondazione."""
    return estrai(None)


def provincia_e_regione(comune):
    """La provincia e la regione del comune, o None se non è nella collezione."""
    return _carica()["dove"].get(comune)


def dove_a_parole(comune):
    """La provincia e la regione a parole: provincia dell'Aquila, Abruzzo; vuoto se il comune non è nella collezione."""
    posto = provincia_e_regione(comune)
    if posto is None:
        return ""
    provincia, regione = posto
    return f"provincia {PROVINCE_CON_ARTICOLO.get(provincia, 'di ' + provincia)}, {regione}"


def descrivi(comune):
    """La provenienza a parole: Avezzano, provincia dell'Aquila, Abruzzo; il comune da solo se non è nella collezione."""
    posto = dove_a_parole(comune)
    return f"{comune}, {posto}" if posto else comune


def percentuale(comune):
    """La popolazione del comune in percentuale su quella del più popoloso della collezione, Roma 100; None se il comune non c'è."""
    tabella = _carica()
    abitanti = tabella["abitanti"].get(comune)
    if abitanti is None:
        return None
    return abitanti * 100 / tabella["massimo"]


def decimali_della_percentuale(valore):
    """
    Quanti decimali servono perché la percentuale non si legga 0%: nessuno da 1 in su, 14%; poi
    tanti quanti ne chiede la prima cifra che non è zero, 0,4% e 0,04%. Si arrotonda come quando si scrive il
    numero, così 0,96 diventa 1% e non 1,0%.
    """
    decimali = 0
    while decimali < 6 and round(valore, decimali) == 0:
        decimali += 1
    return decimali


def candidati(testo):
    """
    I comuni che la ricerca della fondazione mostra per il testo scritto, senza badare a maiuscole,
    accenti e apostrofi: prima quello che si chiama proprio così, poi quelli che cominciano col
    testo, poi quelli con una parola che comincia col testo, infine quelli che lo contengono; in
    ogni gruppo dal più popoloso. Senza testo, tutti, dal più popoloso.
    """
    tabella = _carica()
    cercato = _chiave(testo)
    if not cercato:
        return list(tabella["per_popolazione"])
    gruppi = ([], [], [], [])
    for comune in tabella["per_popolazione"]:
        chiave = tabella["chiavi"][comune]
        if chiave == cercato:
            gruppi[0].append(comune)
        elif chiave.startswith(cercato):
            gruppi[1].append(comune)
        elif f" {cercato}" in chiave:
            gruppi[2].append(comune)
        elif cercato in chiave:
            gruppi[3].append(comune)
    return [comune for gruppo in gruppi for comune in gruppo]
