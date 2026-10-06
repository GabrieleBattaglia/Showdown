"""
Piccoli strumenti di MESS: il tiro del caso e il calendario del simulatore.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 2 del piano, dallo smontaggio di sd.py. Nel simulatore un
anno dura 108 giorni, divisi in 12 mesi da 9 giorni.
"""

import datetime
import random

from costanti import ANNO_SIMULAZIONE_GIORNI


def adesso():
    """
    L'ora dell'orologio di chi gioca, senza fuso. Va bene per le date da mostrare; per misurare
    il tempo trascorso no, perché al cambio dell'ora legale guadagna o perde un'ora: lo corregge
    la tappa 6 del piano, insieme agli altri difetti del tempo del problema P3.
    """
    return datetime.datetime.now()  # noqa: DTZ005 - vedi la docstring


def caso(percentuale):
    """Vero con la probabilità indicata, in percentuale; i valori fuori da 0 e 100 si portano ai bordi."""
    if not 0 <= percentuale <= 100:
        percentuale = max(0, min(100, percentuale))
    return random.uniform(0, 100) < percentuale


def converti_in_tempo(secondi):
    """Ore, minuti e secondi di una durata in secondi."""
    try:
        s_int = int(secondi)
    except (TypeError, ValueError, OverflowError):
        return 0, 0, 0
    m_tot, s = divmod(s_int, 60)
    h, m = divmod(m_tot, 60)
    return h, m, s


def converti_giorni_sim(giorni_totali, anno_sim_giorni=ANNO_SIMULAZIONE_GIORNI, giorni_mese=9, per_eta=False):
    """
    Anni, mesi e giorni di una durata in giorni del simulatore. Con per_eta si contano i mesi
    e i giorni compiuti, partendo da zero; altrimenti è una data, e mesi e giorni partono da uno.
    """
    if giorni_totali < 0 or anno_sim_giorni <= 0:
        return (0, 0, 0) if per_eta else (0, 1, 1)
    anni_compiuti, giorni_dopo_compleanno = divmod(giorni_totali, anno_sim_giorni)
    if giorni_mese <= 0:
        mesi_dopo_compleanno, giorni_dopo_mese = 0, giorni_dopo_compleanno
    else:
        mesi_dopo_compleanno, giorni_dopo_mese = divmod(giorni_dopo_compleanno, giorni_mese)
    if per_eta:
        return anni_compiuti, mesi_dopo_compleanno, giorni_dopo_mese
    return anni_compiuti, mesi_dopo_compleanno + 1, giorni_dopo_mese + 1


def formatta_eta_sim(giorni_totali, formato_breve=False):
    """L'età in giorni del simulatore, per esteso oppure in forma breve anni/mesi/giorni."""
    try:
        anni, mesi, giorni = converti_giorni_sim(giorni_totali, per_eta=True)
    except TypeError:
        return "Età N/D"
    if formato_breve:
        return f"{anni}/{mesi}/{giorni}"
    a_str = f"{anni} ann{'o' if anni == 1 else 'i'}"
    if mesi > 0 or giorni > 0:
        m_str = f"{mesi} mes{'e' if mesi == 1 else 'i'}"
        g_str = f"{giorni} giorn{'o' if giorni == 1 else 'i'}"
        return f"{a_str}, {m_str} e {g_str}"
    return f"{a_str} (compiuti)"
