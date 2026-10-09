"""
I contratti dei giocatori di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-09 con la tappa 11, al posto della regola d'abbandono del vecchio problema P8,
secondo la decisione D31, idea di Gabriele, e le sue risposte del 9 ottobre 2026. Un tesserato si
lega alla polisportiva con un contratto a tempo: chi lo prende e lo allena non lo perde dopo un mese
ma solo alla scadenza. La durata la propone il giocatore, secondo età e ambizione: i ragazzi la
vogliono breve, perché migliorano in fretta e vogliono ritrattare presto lo stipendio, gli anziani
lunga, per stare tranquilli; l'ambizioso la accorcia, il modesto la allunga. Lo stipendio si fissa
alla firma e resta quello fino alla scadenza. Negli ultimi tre mesi si propone il rinnovo, a
trattativa, con stipendio e durata nuovi, al massimo tre volte e una al giorno: il giocatore
accetta secondo la gloria della polisportiva, la fedeltà e l'offerta, e il contratto nuovo parte
alla scadenza di quello in corso. Chi non rinnova torna libero, e nessuno incassa niente. Lo
svincolo a contratto in corso costa una buonuscita, metà degli stipendi che restano.
Un mese di contratto è un mese del calendario simulato: circa trenta giorni simulati, cioè 0,28
anni d'età e dieci giorni veri. Scadenze e inizi cadono sempre il primo del mese.
Come economia.py, qui ci sono soltanto calcoli: le operazioni che firmano, rinnovano e lasciano
scadere i contratti sono regole del mondo, e stanno in mondo.py.
"""

import itertools
import math

import economia
from costanti import (
    ANNO_SIMULAZIONE_GIORNI,
    DURATA_PER_ETA,
    ESPONENTE_GLORIA_PER_AMBIZIONE,
    ESPONENTE_GLORIA_RINNOVO,
    GIORNI_PER_MESE,
    K_AMBIZIONE_DURATA,
    MESI_CONTRATTO_MAX,
    MESI_CONTRATTO_MIN,
    MESI_FINESTRA_RINNOVO,
    PROPOSTE_RINNOVO_MASSIME,
    QUOTA_BUONUSCITA,
    RINCARO_DURATA_RINNOVO,
    SCONTO_FEDELTA_RINNOVO,
    STIPENDIO_MINIMO,
)
from modelli import probabilita_accettazione

# La probabilità con cui una bandiera attiva accetta il rinnovo: gioca anche senza stipendio, D22.
PROBABILITA_BANDIERA = 97.0


# La durata.

def durata_base(anni):
    """La durata che un giocatore di ambizione media propone a quell'età, in mesi: in linea retta fra i punti di DURATA_PER_ETA."""
    punti = DURATA_PER_ETA
    if anni <= punti[0][0]:
        return punti[0][1]
    for (a1, m1), (a2, m2) in itertools.pairwise(punti):
        if anni <= a2:
            return m1 + (m2 - m1) * (anni - a1) / (a2 - a1)
    return punti[-1][1]


def fattore_ambizione(g):
    """Quanto l'ambizione allunga o accorcia la durata: da 1,4 per il più modesto a 0,6 per il più ambizioso."""
    return 1.0 + K_AMBIZIONE_DURATA * (50.0 - g.ambizione) / 50.0


def durata_proposta(g):
    """I mesi di contratto che il giocatore propone, da 4 a 24, secondo età e ambizione, arrotondati al mese, con il mezzo all'insù."""
    mesi = math.floor(durata_base(g.eta / ANNO_SIMULAZIONE_GIORNI) * fattore_ambizione(g) + 0.5)
    return max(MESI_CONTRATTO_MIN, min(MESI_CONTRATTO_MAX, mesi))


# Le date: inizi e scadenze cadono sempre il primo del mese, a mezzanotte.

def primo_del_mese(data):
    """Il primo del mese di quella data, a mezzanotte."""
    return data.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def aggiungi_mesi(data, mesi):
    """Il primo del mese che viene tanti mesi dopo quello della data."""
    indice = data.year * 12 + data.month - 1 + mesi
    return primo_del_mese(data).replace(year=indice // 12, month=indice % 12 + 1)


def inizio(data):
    """Quando parte un contratto firmato in quella data: oggi se è il primo del mese, altrimenti il primo del mese seguente."""
    return primo_del_mese(data) if data.day == 1 else aggiungi_mesi(data, 1)


def scadenza_dopo(data, mesi):
    """La scadenza di un contratto di tanti mesi firmato in quella data, o che parte da quella data: sempre un primo del mese."""
    return aggiungi_mesi(inizio(data), mesi)


def mesi_di_calendario(da, a):
    """I mesi fra due date, frazionari: i giorni diviso 30,44. Zero se la seconda viene prima."""
    return max(0.0, (a - da).total_seconds() / 86400.0 / GIORNI_PER_MESE)


def mesi_interi(da, a):
    """I mesi del calendario fra il mese di una data e quello dell'altra: dal 1 dicembre al 1 marzo sono 3."""
    return (a.year - da.year) * 12 + a.month - da.month


def ha_contratto(g):
    return g.contratto_scadenza is not None


def mesi_al_termine(g, oggi):
    """Quanti mesi mancano alla scadenza del contratto, frazionari; zero per chi non ha contratto."""
    if not ha_contratto(g):
        return 0.0
    return mesi_di_calendario(oggi, g.contratto_scadenza)


def inizio_finestra(g):
    """Il primo giorno in cui si può proporre il rinnovo: tre mesi prima della scadenza. None per chi non ha contratto."""
    if not ha_contratto(g):
        return None
    return aggiungi_mesi(g.contratto_scadenza, -MESI_FINESTRA_RINNOVO)


def in_finestra(g, oggi):
    """Vero negli ultimi tre mesi di contratto: chi scade il primo di marzo si rinnova dal primo di dicembre."""
    if not ha_contratto(g):
        return False
    return inizio_finestra(g).date() <= oggi.date() < g.contratto_scadenza.date()


def ha_rinnovo(g):
    """Vero se c'è già un rinnovo concordato, che partirà alla scadenza."""
    return g.rinnovo_scadenza is not None


def puo_trattare(g):
    """Vero se il giocatore accetta ancora proposte di rinnovo in questa finestra: al massimo tre."""
    return g.proposte_rinnovo < PROPOSTE_RINNOVO_MASSIME


def stipula(g, data, stipendio, mesi):
    """
    Scrive nel giocatore un contratto nuovo, firmato in quella data: lo stipendio, fisso fino
    alla scadenza, e la scadenza dopo i mesi. Toglie rinnovo, proposte e trattativa. Si chiama
    stipula e non firma, per non confonderla con la firma dei salvataggi.
    """
    g.annulla_contratto()
    g.contratto_stipendio = int(stipendio)
    g.contratto_scadenza = scadenza_dopo(data, mesi)


def concorda_rinnovo(g, stipendio, mesi):
    """Il rinnovo accettato: il contratto nuovo parte alla scadenza di quello in corso, con lo stipendio nuovo da lì."""
    g.rinnovo_stipendio = int(stipendio)
    g.rinnovo_scadenza = scadenza_dopo(g.contratto_scadenza, mesi)


def subentra_il_rinnovo(g):
    """Alla scadenza, il contratto rinnovato prende il posto del vecchio: stipendio e scadenza nuovi, proposte a zero."""
    stipendio, scadenza = g.rinnovo_stipendio, g.rinnovo_scadenza
    g.annulla_contratto()
    g.contratto_stipendio = stipendio
    g.contratto_scadenza = scadenza


# La richiesta di rinnovo: le tre cose di D31, la gloria della polisportiva, la fedeltà e l'offerta.

def fattore_gloria_rinnovo(g, poli):
    """
    Quanto la gloria del club sposta la richiesta: il fattore di reputazione dell'ingaggio, da 0,5 a
    2, elevato a 0,25 più metà dell'ambizione su cento. Il modesto guarda poco la gloria del club,
    l'ambizioso molto: con ambizione media il fattore va da 0,71 a 1,41.
    """
    return economia.fattore_reputazione(g, poli) ** (ESPONENTE_GLORIA_RINNOVO + ESPONENTE_GLORIA_PER_AMBIZIONE * g.ambizione / 100.0)


def fattore_fedelta_rinnovo(g):
    """La fedeltà al club fa chiedere meno: fino a un quarto in meno alla fedeltà piena."""
    return 1.0 - SCONTO_FEDELTA_RINNOVO * g.fedelta / 100.0


def fattore_durata_rinnovo(g, mesi):
    """Ogni mese di differenza dalla durata che il giocatore propone costa il 2 per cento in più."""
    return 1.0 + RINCARO_DURATA_RINNOVO * abs(mesi - durata_proposta(g))


def richiesta_rinnovo(g, poli, mesi=None):
    """Lo stipendio che il giocatore chiede per rinnovare per tanti mesi, la durata che propone se non è data, arrotondato alla decina."""
    mesi = durata_proposta(g) if mesi is None else mesi
    euro = economia.stipendio(g) * fattore_gloria_rinnovo(g, poli) * fattore_fedelta_rinnovo(g) * fattore_durata_rinnovo(g, mesi)
    return max(STIPENDIO_MINIMO, economia.arrotonda(euro))


def probabilita_rinnovo(g, poli, stipendio, mesi):
    """
    La probabilità, in percentuale, che il giocatore accetti il rinnovo: la curva dell'ingaggio, dal
    3 al 97 per cento fra il 30 per cento sotto e il 30 per cento sopra la richiesta. Una bandiera
    attiva accetta al 97, perché gioca anche senza stipendio.
    """
    if economia.bandiera_attiva(g):
        return PROBABILITA_BANDIERA
    return probabilita_accettazione(stipendio, richiesta_rinnovo(g, poli, mesi))


def buonuscita(g, oggi):
    """La buonuscita di uno svincolo a contratto in corso: metà degli stipendi che restano, arrotondata alla decina."""
    if not ha_contratto(g):
        return 0
    return economia.arrotonda(economia.stipendio_pagato(g) * mesi_al_termine(g, oggi) * QUOTA_BUONUSCITA)
