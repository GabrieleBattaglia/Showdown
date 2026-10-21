"""
Strumenti comuni alle prove del calendario dei tornei della tappa 12: un mondo di prova con giocatori
costruiti a mano, i modelli predefiniti nella cartella temporanea delle prove, l'apertura delle
edizioni dei soli modelli indicati e i giorni del calendario.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
"""

import datetime
import random

from aiuti_motore import giocatore

import formule
import modelli_torneo
from modelli import Polisportiva
from mondo import Mondo

# Un lunedì: il martedì dopo comincia l'Open maschile del martedì.
OGGI = datetime.datetime(2026, 10, 5, 9, 0)


def mondo_di_prova(uomini=40, donne=40, data=OGGI, seme=3):
    """Un mondo con giocatori liberi costruiti a mano, di forza diversa, senza data del ritmo e senza carico."""
    mondo = Mondo()
    mondo.datetime_corrente_simulazione = data
    rng = random.Random(seme)
    gid = 1
    for sesso, quanti in (("m", uomini), ("f", donne)):
        for _ in range(quanti):
            g = giocatore(gid, valore=rng.uniform(4.0, 10.0), fisico=rng.uniform(1.0, 3.0), anni=rng.uniform(18.0, 40.0), sesso=sesso)
            g.prossimo_torneo = None
            g.costanza = 0.0
            g.diario = []
            mondo.giocatori[gid] = g
            gid += 1
    mondo.prossimo_id = gid
    return mondo


def polisportiva(mondo, nome, cpu=True, cassa=5000, ids=(), fondazione_giorni=400):
    """Una polisportiva del mondo di prova, del computer o dell'utente, con i tesserati indicati."""
    poli = Polisportiva(nome, None, mondo.datetime_corrente_simulazione - datetime.timedelta(days=fondazione_giorni), is_cpu_controlled=cpu)
    poli.cassa = cassa
    mondo.polisportive[poli.nome] = poli
    for gid in ids:
        mondo._entra(poli, mondo.giocatori[gid])
    return poli


def modelli():
    """I modelli predefiniti, letti dalla cartella temporanea delle prove dove si copiano."""
    gestore = modelli_torneo.GestoreModelli()
    gestore.crea_predefiniti()
    return gestore.modelli()[0]


def modello(nome):
    return next(m for m in modelli() if m.nome == nome)


def apri(mondo, data, *nomi, rapporto=None):
    """Apre le edizioni dei soli modelli indicati, come fa il calendario il giorno dato."""
    scelti = [m for m in modelli() if m.nome in nomi]
    rapporto = rapporto if rapporto is not None else Mondo.rapporto_vuoto(data)
    mondo.calendario.apri_edizioni(mondo, data, scelti, formule.leggi()[0], rapporto)
    return [ed for ed in mondo.calendario.edizioni if ed.nome in nomi]


def iscrivi_tutti(edizione, mondo, ids, origine="libero"):
    """Iscrive d'ufficio i giocatori indicati, senza pagare, come liberi."""
    for gid in ids:
        edizione.aggiungi(gid, None, 0, origine)


def giorno(mondo, data, rapporto=None):
    """Un giorno del calendario soltanto, col rapporto vuoto se non si dà."""
    mondo.datetime_corrente_simulazione = data
    rapporto = rapporto if rapporto is not None else Mondo.rapporto_vuoto(data)
    mondo.calendario.giorno(mondo, data, rapporto)
    return rapporto


def solo(nomi):
    """Lascia attivi soltanto i modelli indicati, nella cartella delle prove."""
    gestore = modelli_torneo.GestoreModelli()
    gestore.crea_predefiniti()
    for m in gestore.modelli()[0]:
        if m.nome not in nomi:
            m.attivo = False
            gestore.salva(m)
