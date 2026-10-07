"""
Il valore complessivo di un giocatore di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9, per il problema P14: il vecchio indice sommava alla pari
caratteristiche fisiche e tecniche e aggiungeva 33 punti per ogni tratto speciale. Ora ogni
caratteristica ha un peso, e chiusure e blocchi entrano per ruolo, di dritto e di rovescio: per il
destrimano il rovescio è il lato sinistro, per il mancino il destro, per l'ambidestro si prende la
media dei due lati. Così un mancino specchiato vale quanto il destrimano da cui viene.
L'indice è A più B per la somma pesata, più i pesi dei tratti presenti. Con i pesi della tappa 8,
tutti a 1, 33 punti per ambidestro, gioco rapido e cambio di velocità, zero per il mancino, A 0 e
B 1, l'indice è quello di prima; i pesi di costanti.py li ha misurati sul motore nuovo la taratura
del valore, strumenti/taratura_valore.py, e la scala li riporta alla mediana di 140 su cui conta
l'economia, decisione D22. Esperienza, età, temperamento e ipovedente restano fuori dal valore.
"""

from costanti import CARATTERISTICHE_VALORE, COLPI_DELLO_SCAMBIO, COLPI_DI_BATTUTA, PESI_TRATTI, PESI_VALORE, SCALA_VALORE_A, SCALA_VALORE_B

PARTI = ("base", "allenata", "totale")
TRATTI = ("mancino", "ambidestro", "giocorapido", "cambiovelocita")
_SEMPLICI = (*COLPI_DELLO_SCAMBIO, *COLPI_DI_BATTUTA, "difesa", "tenutapaletta", "controllopalla", "attacco", "precisione", "forza", "resistenza")


def _parte(g, nome, parte):
    if parte == "base":
        return getattr(g, nome + "_base", 0.0)
    if parte == "allenata":
        return getattr(g, nome + "_allenata", 0.0)
    return getattr(g, nome + "_base", 0.0) + getattr(g, nome + "_allenata", 0.0)


def caratteristiche(g, parte="totale"):
    """Le caratteristiche che entrano nel valore, per la parte innata, allenata o totale, nell'ordine di CARATTERISTICHE_VALORE."""
    if parte not in PARTI:
        raise ValueError(f"Parte sconosciuta: {parte}.")
    valori = {nome: _parte(g, nome, parte) for nome in _SEMPLICI}
    chiusure = (_parte(g, "chiusurasx", parte), _parte(g, "chiusuradx", parte))
    blocchi = (_parte(g, "bloccosx", parte), _parte(g, "bloccodx", parte))
    if getattr(g, "ambidestro", False):
        chiusura_dritto = chiusura_rovescio = (chiusure[0] + chiusure[1]) / 2.0
        blocco_dritto = blocco_rovescio = (blocchi[0] + blocchi[1]) / 2.0
    elif getattr(g, "mancino", False):
        chiusura_rovescio, chiusura_dritto = chiusure[1], chiusure[0]
        blocco_rovescio, blocco_dritto = blocchi[1], blocchi[0]
    else:
        chiusura_rovescio, chiusura_dritto = chiusure
        blocco_rovescio, blocco_dritto = blocchi
    valori.update(chiusura_dritto=chiusura_dritto, chiusura_rovescio=chiusura_rovescio, blocco_dritto=blocco_dritto, blocco_rovescio=blocco_rovescio)
    return {nome: valori[nome] for nome in CARATTERISTICHE_VALORE}


def tratti(g):
    """I tratti speciali che entrano nel valore, vero o falso."""
    return {nome: bool(getattr(g, nome, False)) for nome in TRATTI}


def somma_pesata(g, parte="totale", pesi=None):
    pesi = PESI_VALORE if pesi is None else pesi
    return sum(pesi[nome] * valore for nome, valore in caratteristiche(g, parte).items())


def bonus_tratti(g, pesi_tratti=None):
    pesi_tratti = PESI_TRATTI if pesi_tratti is None else pesi_tratti
    return sum(pesi_tratti[nome] for nome, presente in tratti(g).items() if presente)


def parti(g, pesi=None, pesi_tratti=None, a=None, b=None):
    """
    Le due parti del valore: icv_base, cioè A più B per la somma sulle parti innate più i tratti,
    e icv_allenato, cioè B per la somma sulle parti allenate.
    """
    a = SCALA_VALORE_A if a is None else a
    b = SCALA_VALORE_B if b is None else b
    icv_base = a + b * (somma_pesata(g, "base", pesi) + bonus_tratti(g, pesi_tratti))
    icv_allenato = b * somma_pesata(g, "allenata", pesi)
    return icv_base, icv_allenato


def indice(g, pesi=None, pesi_tratti=None, a=None, b=None):
    """Il valore complessivo: A più B per la somma pesata dei totali e dei tratti presenti."""
    a = SCALA_VALORE_A if a is None else a
    b = SCALA_VALORE_B if b is None else b
    return a + b * (somma_pesata(g, "totale", pesi) + bonus_tratti(g, pesi_tratti))
