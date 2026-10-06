"""
Piccoli strumenti di MESS: il tiro del caso, il calendario del simulatore, l'orologio e
l'impronta delle password.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 2 del piano, dallo smontaggio di sd.py. Nel simulatore un
anno dura 108 giorni, divisi in 12 mesi da 9 giorni.
"""

import datetime
import hashlib
import hmac
import random
import secrets

from costanti import ANNO_SIMULAZIONE_GIORNI

MESI = ("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre")


def adesso():
    """
    L'ora dell'orologio di chi gioca, senza fuso: serve soltanto a datare e mostrare le cose a
    chi legge. Per misurare il tempo trascorso si usa adesso_utc, che il cambio dell'ora legale
    non sposta: fino alla tappa 6 il tempo si misurava con questa, e in quei giorni il mondo
    guadagnava o perdeva un'ora, problema P3 del piano.
    """
    return datetime.datetime.now()  # noqa: DTZ005 - solo per mostrare, vedi la docstring


def adesso_utc():
    """L'istante attuale in UTC, con il fuso: la misura del tempo che passa, dalla tappa 6."""
    return datetime.datetime.now(datetime.UTC)


def in_ora_locale(istante):
    """Un istante con il fuso portato all'ora locale, senza fuso, per mostrarlo; uno senza fuso torna com'è."""
    if istante.tzinfo is None:
        return istante
    return istante.astimezone().replace(tzinfo=None)


def data_breve(dt):
    """Una data a parole, senza l'ora: 7 ottobre 2026."""
    return f"{dt.day} {MESI[dt.month - 1]} {dt.year}"


def accorda(sesso, maschile):
    """Una parola che finisce in o, al maschile o al femminile secondo il sesso, m o f: libero, libera."""
    return maschile if sesso == "m" else maschile[:-1] + "a"


# L'impronta delle password, dal 2026-10-06 con la tappa 3: PBKDF2 con SHA-256 e un sale casuale
# per ogni password. La password non si conserva mai, né in memoria né nel salvataggio.
METODO_IMPRONTA = "pbkdf2_sha256"
ITERAZIONI_IMPRONTA = 100_000


def crea_impronta(password):
    """L'impronta da conservare al posto di una password: metodo, iterazioni, sale e impronta, separati dal dollaro."""
    sale = secrets.token_hex(16)
    calcolata = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), bytes.fromhex(sale), ITERAZIONI_IMPRONTA).hex()
    return f"{METODO_IMPRONTA}${ITERAZIONI_IMPRONTA}${sale}${calcolata}"


def verifica_impronta(password, impronta):
    """Vero se la password corrisponde all'impronta; falso anche se l'impronta non è leggibile."""
    try:
        metodo, iterazioni, sale, attesa = str(impronta).split("$")
        calcolata = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), bytes.fromhex(sale), int(iterazioni)).hex()
    except ValueError:
        return False
    return metodo == METODO_IMPRONTA and hmac.compare_digest(calcolata, attesa)


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
