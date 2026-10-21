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
del valore, strumenti/taratura_valore.py, sugli incontri al meglio dei 3, e la scala li riporta
attorno alla mediana di 140 su cui conta l'economia, decisione D22: dalla decisione D26 la scala
la cerca la simulazione lunga, sulla cassa delle polisportive del computer. Esperienza, età,
temperamento e ipovedente restano fuori dal valore.
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


def nome_semplice(nome):
    """Il nome di una caratteristica senza il suffisso della parte: chiusurasx per chiusurasx_base e chiusurasx_allenata."""
    for suffisso in ("_allenata", "_base"):
        if nome.endswith(suffisso):
            return nome[:-len(suffisso)]
    return nome


def peso_per_punto(g, nome, pesi=None):
    """
    Quanta somma pesata vale un punto in più della caratteristica, per quel giocatore: il peso del
    ruolo che la caratteristica ha per lui. La chiusura sinistra è di rovescio per il destrimano e
    di dritto per il mancino; per l'ambidestro, che ha la media dei due lati in tutti e due i ruoli,
    vale la media dei due pesi. Lo stesso per i blocchi. Dalla tappa 11 è la base del costo
    dell'allenamento, che è in somma pesata e quindi non dipende dalla scala A e B.
    """
    pesi = PESI_VALORE if pesi is None else pesi
    nome = nome_semplice(nome)
    ruolo = nome[:-2]
    if ruolo not in ("chiusura", "blocco"):
        return pesi[nome]
    dritto, rovescio = pesi[ruolo + "_dritto"], pesi[ruolo + "_rovescio"]
    if getattr(g, "ambidestro", False):
        return (dritto + rovescio) / 2.0
    sinistro = nome.endswith("sx")
    if getattr(g, "mancino", False):
        return dritto if sinistro else rovescio
    return rovescio if sinistro else dritto


def tratti(g):
    """I tratti speciali che entrano nel valore, vero o falso."""
    return {nome: bool(getattr(g, nome, False)) for nome in TRATTI}


# I nomi delle parti delle caratteristiche semplici, per la somma in una passata.
_NOMI_SEMPLICI = tuple((nome, nome + "_base", nome + "_allenata") for nome in _SEMPLICI)
# I nomi di chiusure e blocchi, per ruolo: i due pesi e i due lati della parte innata e di quella allenata.
_NOMI_DEI_RUOLI = tuple((ruolo + "_dritto", ruolo + "_rovescio", ruolo + "sx_base", ruolo + "dx_base", ruolo + "sx_allenata", ruolo + "dx_allenata")
                        for ruolo in ("chiusura", "blocco"))


def _somme(g, pesi):
    """
    Le somme pesate della parte innata e di quella allenata, in una passata sola: è il conto di
    caratteristiche, con chiusure e blocchi per ruolo, fatto senza dizionari intermedi, perché dalla
    tappa 11 il valore si ricalcola a ogni spesa d'allenamento, centinaia di volte al giorno.
    Dalla tappa 12, punto 1.3 del progetto, le caratteristiche si leggono direttamente dal
    dizionario degli attributi del giocatore, ed è la via di tutti i giocatori veri; a un oggetto a
    cui ne manca una, come la vista leggera che archivio.stipendio_della_1_50 costruisce dal formato
    5, resta la via di prima, con getattr e lo zero per le parti che mancano. Gli stessi numeri fino
    all'ultimo bit, nello stesso ordine di somma.
    """
    try:
        return _somme_dal_dizionario(g.__dict__, pesi)
    except (AttributeError, KeyError):
        return _somme_con_getattr(g, pesi)


def _somme_dal_dizionario(attributi, pesi):
    """Le somme di _somme lette dal dizionario degli attributi; KeyError se manca una parte."""
    innata = allenata = 0.0
    for nome, nome_base, nome_allenata in _NOMI_SEMPLICI:
        peso = pesi[nome]
        innata += peso * attributi[nome_base]
        allenata += peso * attributi[nome_allenata]
    ambidestro, mancino = attributi["ambidestro"], attributi["mancino"]
    for chiave_dritto, chiave_rovescio, sx_base, dx_base, sx_allenata, dx_allenata in _NOMI_DEI_RUOLI:
        dritto, rovescio = pesi[chiave_dritto], pesi[chiave_rovescio]
        sx, dx = attributi[sx_base], attributi[dx_base]
        if ambidestro:
            innata += (dritto + rovescio) * (sx + dx) / 2.0
        elif mancino:
            innata += rovescio * dx + dritto * sx
        else:
            innata += rovescio * sx + dritto * dx
        sx, dx = attributi[sx_allenata], attributi[dx_allenata]
        if ambidestro:
            allenata += (dritto + rovescio) * (sx + dx) / 2.0
        elif mancino:
            allenata += rovescio * dx + dritto * sx
        else:
            allenata += rovescio * sx + dritto * dx
    return innata, allenata


def _somme_con_getattr(g, pesi):
    """Le somme di _somme per un oggetto qualunque, con lo zero per le parti che gli mancano: il conto della tappa 11."""
    innata = allenata = 0.0
    for nome, nome_base, nome_allenata in _NOMI_SEMPLICI:
        peso = pesi[nome]
        innata += peso * getattr(g, nome_base, 0.0)
        allenata += peso * getattr(g, nome_allenata, 0.0)
    ambidestro, mancino = getattr(g, "ambidestro", False), getattr(g, "mancino", False)
    for ruolo in ("chiusura", "blocco"):
        dritto, rovescio = pesi[ruolo + "_dritto"], pesi[ruolo + "_rovescio"]
        for parte in ("_base", "_allenata"):
            sx, dx = getattr(g, ruolo + "sx" + parte, 0.0), getattr(g, ruolo + "dx" + parte, 0.0)
            if ambidestro:
                somma = (dritto + rovescio) * (sx + dx) / 2.0
            elif mancino:
                somma = rovescio * dx + dritto * sx
            else:
                somma = rovescio * sx + dritto * dx
            if parte == "_base":
                innata += somma
            else:
                allenata += somma
    return innata, allenata


def somma_pesata(g, parte="totale", pesi=None):
    """La somma pesata della parte innata, allenata o totale."""
    if parte not in PARTI:
        raise ValueError(f"Parte sconosciuta: {parte}.")
    innata, allenata = _somme(g, PESI_VALORE if pesi is None else pesi)
    if parte == "base":
        return innata
    if parte == "allenata":
        return allenata
    return innata + allenata


def bonus_tratti(g, pesi_tratti=None):
    pesi_tratti = PESI_TRATTI if pesi_tratti is None else pesi_tratti
    return sum(pesi_tratti[nome] for nome in TRATTI if getattr(g, nome, False))


def parti(g, pesi=None, pesi_tratti=None, a=None, b=None):
    """
    Le due parti del valore: icv_base, cioè A più B per la somma sulle parti innate più i tratti,
    e icv_allenato, cioè B per la somma sulle parti allenate.
    """
    a = SCALA_VALORE_A if a is None else a
    b = SCALA_VALORE_B if b is None else b
    innata, allenata = _somme(g, PESI_VALORE if pesi is None else pesi)
    return a + b * (innata + bonus_tratti(g, pesi_tratti)), b * allenata


def indice(g, pesi=None, pesi_tratti=None, a=None, b=None):
    """Il valore complessivo: A più B per la somma pesata dei totali e dei tratti presenti."""
    a = SCALA_VALORE_A if a is None else a
    b = SCALA_VALORE_B if b is None else b
    return a + b * (somma_pesata(g, "totale", pesi) + bonus_tratti(g, pesi_tratti))
