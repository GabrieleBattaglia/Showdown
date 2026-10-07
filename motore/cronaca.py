"""
La cronaca di una partita di showdown, in italiano, dagli eventi del motore di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9, decisione D25. Tre livelli: la sintetica, una riga per punto più
i set e l'incontro; la normale, ogni azione con il fischio e la chiamata dell'arbitro dentro la
frase dell'esito, per la finestra e il file; la tecnica, la normale più la procedura dell'arbitro, i
secondi e le probabilità delle fasce, che è il registro dei dubbi di taratura al posto del vecchio
registro dei dadi. Le chiamate sono i termini italiani della FISPIC.
Le frasi seguono le regole di accessibilità del parco: intere, a tutta larghezza, senza separatori
grafici e senza righe vuote; il genere si accorda con utilita.accorda. La cronaca non usa il caso:
quando una frase ha più varianti, sceglie con il progressivo dell'evento.
Una partita va in un file suo, nella cartella cronache accanto al programma, e gli eventi si possono
salvare in JSON per i banchi d'ascolto della tappa 10. Il vecchio registro unico
log_partite_showdown.txt non c'è più.
"""

import json
import os
import re
from typing import NamedTuple

import percorsi
from costanti import CARTELLA_CRONACHE, NOME_ATTR_TO_DISPLAY_MAP
from motore import eventi as E
from motore.eventi import CAUSE, CHIAMATE
from motore.tavolo import lato_di
from utilita import MESI, accorda

SINTETICA = "sintetica"
NORMALE = "normale"
TECNICA = "tecnica"
LIVELLI = (SINTETICA, NORMALE, TECNICA)


class Nome(NamedTuple):
    """Come chiamare un giocatore, o una squadra, nella cronaca, e il sesso per accordare le parole."""
    testo: str
    sesso: str


def nomi_dei_giocatori(giocatori, squadre=None):
    """
    I nomi della cronaca: il cognome, o nome e cognome quando due giocatori hanno lo stesso
    cognome. Le parti A e B prendono il nome del giocatore, nel singolare, o della squadra.
    """
    giocatori = list(giocatori)
    cognomi = [g.cognome for g in giocatori]
    nomi = {}
    for g in giocatori:
        testo = g.cognome if cognomi.count(g.cognome) == 1 else f"{g.nome} {g.cognome}"
        nomi[g.id] = Nome(testo, g.sesso)
    if squadre is not None:
        nomi["A"] = Nome(squadre[0].nome, "f")
        nomi["B"] = Nome(squadre[1].nome, "f")
    elif len(giocatori) == 2:
        nomi["A"] = nomi[giocatori[0].id]
        nomi["B"] = nomi[giocatori[1].id]
    return nomi


# Numeri e parole.

def _numero(valore, decimali=1):
    return f"{valore:.{decimali}f}".replace(".", ",")


def nome_colpo(colpo):
    """Il colpo a parole, al minuscolo: doppia sponda destra, battuta sinistra, bomba centrale."""
    if colpo is None:
        return "colpo"
    return NOME_ATTR_TO_DISPLAY_MAP.get(f"{colpo}_base", colpo).lower()


_ARTICOLI = {"bomba centrale": "una bomba centrale"}


def con_articolo(colpo):
    """Il colpo con l'articolo indeterminativo: un lungolinea destro, una doppia sponda destra."""
    parole = nome_colpo(colpo)
    if parole in _ARTICOLI:
        return _ARTICOLI[parole]
    maschili = ("lungolinea",)
    return ("un " if parole.split()[0] in maschili else "una ") + parole


def _n(nomi, chiave):
    nome = nomi.get(chiave)
    return nome.testo if nome else str(chiave)


def _accorda(nomi, chiave, parola):
    nome = nomi.get(chiave)
    return accorda(nome.sesso if nome else "m", parola)


def _altra(parte):
    return "B" if parte == "A" else "A"


_LATI = {"sinistra": "a sinistra", "centro": "al centro", "destra": "a destra"}
_DAL_LATO = {"sx": "dalla sinistra", "centro": "dal centro", "dx": "dalla destra"}
_ALLA = {"sinistra": "alla sinistra", "centro": "al centro", "destra": "alla destra"}
_FISCHI = {E.SINGOLO: "Fischio", E.DOPPIO: "Doppio fischio", E.LUNGO: "Fischio lungo"}
_SERVIZI = {1: "Primo", 2: "Secondo", 3: "Terzo"}


def _punteggio_di(punteggio, parte):
    """Il punteggio visto da una parte: prima i suoi punti."""
    a, b = punteggio
    return (a, b) if parte == "A" else (b, a)


def _chi_subisce(evento):
    dati = evento.dati or {}
    for chiave in ("battitore", "ricevitore"):
        if dati.get(chiave) is not None and dati.get(chiave) != evento.chi:
            return dati.get(chiave)
    return None


def _sponde(volo):
    return sum(1 for tappa in volo if tappa.tipo in ("sponda", "curva"))


# Le frasi, evento per evento.

def frase(evento, nomi, livello=NORMALE):
    """La frase di un evento al livello indicato, oppure None se a quel livello l'evento resta muto."""
    if livello not in LIVELLI:
        raise ValueError(f"Livello di cronaca sconosciuto: {livello}.")
    funzione = _FRASI.get(evento.tipo)
    if funzione is None:
        return None
    testo = funzione(evento, nomi, livello)
    if testo is None:
        return None
    if livello == TECNICA:
        testo += _dettagli_tecnici(evento)
    return testo


def _dettagli_tecnici(evento):
    parti = [f"secondo {_numero(evento.t)}"]
    if evento.durata:
        parti.append(f"durata {_numero(evento.durata)}")
    if evento.pos is not None and evento.chi is not None:
        parti.append(f"posizione {_numero(evento.pos[0], 0)}, {_numero(evento.pos[1], 0)}")
    dati = evento.dati or {}
    if dati.get("prob"):
        parti.append("fasce " + ", ".join(_numero(100 * p) for p in dati["prob"]))
    for chiave in ("qualita", "pressione", "valore"):
        if dati.get(chiave) is not None:
            parti.append(f"{chiave} {_numero(dati[chiave], 2)}")
    return " (" + "; ".join(parti) + ")"


def _inizio_incontro(evento, nomi, livello):
    dati = evento.dati or {}
    formato = dati.get("formato", "")
    if formato == "gara a squadre":
        return f"Inizio della gara a squadre: {_n(nomi, 'A')} contro {_n(nomi, 'B')}, un set a 31 punti."
    set_al_meglio = "5" if "5" in formato else "3"
    return f"Inizio dell'incontro: {_n(nomi, 'A')} contro {_n(nomi, 'B')}, al meglio dei {set_al_meglio} set."


def _sorteggio(evento, nomi, livello):
    d = evento.dati
    chiama, vince = d["chiama"], d["vince"]
    altro = _altra(vince)
    testo = f"Sorteggio: {_n(nomi, chiama)} chiama {d['faccia_chiamata']}, esce {d['faccia_uscita']}. Vince {_n(nomi, vince)}"
    if d["scelta"] in ("tiene", "cede"):
        # Nella gara a squadre la scelta arriva dopo la lettura delle formazioni.
        return testo + "."
    if d["scelta"] == "battuta":
        return testo + f", che sceglie la battuta; {_n(nomi, altro)} sceglie il lato del tavolo."
    return testo + f", che sceglie il lato del tavolo: batte {_n(nomi, altro)}."


def _elenco(parole):
    """Le parole in fila, con la e prima dell'ultima: Rossi, Verdi e Neri."""
    parole = list(parole)
    if len(parole) <= 1:
        return "".join(parole)
    return ", ".join(parole[:-1]) + " e " + parole[-1]


def _formazioni(evento, nomi, livello):
    """La lettura delle formazioni nella gara a squadre, e la scelta di chi ha vinto il sorteggio."""
    d = evento.dati
    squadre = []
    for parte in ("A", "B"):
        testo = f"{_n(nomi, parte)} con {_elenco(_n(nomi, gid) for gid in d['formazioni'][parte])}"
        riserve = d.get("riserve", {}).get(parte) or []
        if riserve:
            testo += f", in riserva {_elenco(_n(nomi, gid) for gid in riserve)}"
        squadre.append(testo)
    vince = d["vince"]
    if d["scelta"] == "tiene":
        scelta = f"{_n(nomi, vince)} tiene il primo servizio."
    else:
        scelta = f"{_n(nomi, vince)} cede il primo servizio: batte {_n(nomi, _altra(vince))}."
    return f"L'arbitro legge le formazioni: {squadre[0]}; {squadre[1]}. {scelta}"


def _riscaldamento_inizio(evento, nomi, livello):
    if livello == SINTETICA:
        return None
    secondi = int((evento.dati or {}).get("durata", 60))
    return "Riscaldamento, un minuto." if secondi == 60 else f"Riscaldamento, {secondi} secondi."


def _riscaldamento_colpo(evento, nomi, livello):
    if livello != TECNICA:
        return None
    return f"Riscaldamento: {_n(nomi, evento.chi)} prova {con_articolo(evento.colpo)}."


def _avviso_tempo(evento, nomi, livello):
    if livello != TECNICA:
        return None
    if evento.chiamata:
        return f"L'arbitro avvisa: {CHIAMATE.get(evento.chiamata, evento.chiamata)}."
    restano = (evento.dati or {}).get("restano", 15)
    return f"L'arbitro avvisa: {restano} secondi."


def _riscaldamento_fine(evento, nomi, livello):
    return None if livello == SINTETICA else "Fine del riscaldamento."


def _inizio_set(evento, nomi, livello):
    if livello == SINTETICA:
        return f"Set {evento.set_n}."
    apre = (evento.dati or {}).get("apre")
    return f"Set {evento.set_n}: apre {_n(nomi, apre)}."


def _recupero(evento, nomi, livello):
    if livello != TECNICA:
        return None
    da = {"tasca": "dalla tasca", "terra": "da terra"}.get((evento.dati or {}).get("da"), "dal tavolo")
    return f"L'arbitro recupera la pallina {da}."


def _consegna(evento, nomi, livello):
    if livello != TECNICA:
        return None
    return f"L'arbitro porta la pallina a {_n(nomi, (evento.dati or {}).get('a'))}."


def _annuncio(evento, nomi, livello):
    if livello == SINTETICA:
        return None
    d = evento.dati
    io, lui = d["punteggio_visto"]
    return f"{_SERVIZI.get(d['numero_servizio'], 'Nuovo')} servizio di {_n(nomi, d['battitore'])}, {io} a {lui}."


def _domanda_pronto(evento, nomi, livello):
    return "L'arbitro chiede se i giocatori sono pronti." if livello == TECNICA else None


def _fischio(evento, nomi, livello):
    return f"{_FISCHI[evento.fischio]}." if livello == TECNICA else None


def _chiamata(evento, nomi, livello):
    return f"Chiamata dell'arbitro: {CHIAMATE.get(evento.chiamata, evento.chiamata)}." if livello == TECNICA else None


def _cambio_battitore(evento, nomi, livello):
    return f"Cambio di battuta: ora batte {_n(nomi, evento.chi)}." if livello == TECNICA else None


def _fine_set(evento, nomi, livello):
    d = evento.dati
    a, b = d["punteggio"]
    vince = "A" if a > b else "B"
    io, lui = _punteggio_di((a, b), vince)
    sa, sb = d["set_vinti"]
    testo = f"Fischio lungo. Set a {_n(nomi, vince)}, {io} a {lui}"
    if d.get("ultimo"):
        testo += "."
    elif sa == sb:
        testo += f"; set pari, {_PAROLE[sa]} a {_PAROLE[sb]}."
    else:
        guida = "A" if sa > sb else "B"
        mio, suo = _punteggio_di((sa, sb), guida)
        testo += f"; {_n(nomi, guida)} conduce {'un' if mio == 1 else _PAROLE[mio]} set a {_PAROLE[suo]}."
    if livello == SINTETICA:
        return testo.replace("Fischio lungo. ", "")
    return testo


_PAROLE = ("zero", "uno", "due", "tre", "quattro", "cinque")


def _fine_incontro(evento, nomi, livello):
    d = evento.dati
    sa, sb = d["set_vinti"]
    vince = "A" if sa > sb else "B"
    mio, suo = _punteggio_di((sa, sb), vince)
    parziali = ", ".join(f"{x} a {y}" for x, y in (_punteggio_di(tuple(s), vince) for s in d["set"]))
    return f"Fine dell'incontro: vince {_n(nomi, vince)}, {mio} set a {suo}: {parziali}."


def _battuta(evento, nomi, livello):
    if livello == SINTETICA:
        return None
    return f"{nome_colpo(evento.colpo).capitalize()} di {_n(nomi, evento.chi)}."


def _volo(evento, nomi, livello):
    if livello == SINTETICA:
        return None
    dati = evento.dati or {}
    ultima = evento.volo[-1].tipo
    verso = dati.get("verso")
    if verso is None or ultima not in ("paletta", "porta", "corpo"):
        return None
    if dati.get("ribattuta"):
        return f"Palla facile per {_n(nomi, verso)}."
    sponde = _sponde(evento.volo)
    corsa = ("La pallina corre dritta", "La pallina rimbalza sulla sponda", "La pallina tocca due sponde", "La pallina tocca tre sponde")[min(sponde, 3)]
    if ultima == "porta":
        return f"{corsa} e punta alla porta di {_n(nomi, verso)}."
    parte_verso = _altra(evento.parte) if evento.parte else "A"
    lato = lato_di(evento.pos[0], parte_verso)
    return f"{corsa} e arriva {_ALLA[lato]} di {_n(nomi, verso)}."


def _parata(evento, nomi, livello):
    if livello == SINTETICA:
        return None
    chi = _n(nomi, evento.chi)
    esito = evento.esito
    di_cosa = "" if evento.dritto is None else (" di dritto" if evento.dritto else " di rovescio")
    if esito == "fermata":
        if evento.lato == "centro":
            testo = f"{chi} para al centro{di_cosa} e ferma la pallina"
        else:
            testo = f"{chi} chiude {_LATI[evento.lato]}{di_cosa} e ferma la pallina"
        return testo + (", ma non è una fermata pulita." if evento.causa == "sporca" else ".")
    if esito == "ribattuta":
        return f"{chi} para{di_cosa}, ma la pallina torna indietro piano."
    if esito == "goal":
        return f"{chi} non ci arriva."
    return None


def _cambio_mano(evento, nomi, livello):
    if livello == SINTETICA:
        return None
    mano = "sinistra" if evento.mano == "sinistra" else "destra"
    return f"{_n(nomi, evento.chi)} passa la paletta nella mano {mano}."


def _controllo(evento, nomi, livello):
    if livello == SINTETICA:
        return None
    chi = _n(nomi, evento.chi)
    if evento.esito == "sfuggita":
        return f"La pallina sfugge a {chi}."
    if evento.esito == "recupero":
        return f"{chi} la riprende."
    if evento.esito == "riuscito" and livello == TECNICA:
        return f"{chi} controlla la pallina."
    return None


def _colpo(evento, nomi, livello):
    if livello == SINTETICA:
        return None
    varianti = ("attacca con", "tira", "risponde con")
    verbo = varianti[evento.n % len(varianti)] if evento.colpo_n > 1 else "attacca con"
    return f"{_n(nomi, evento.chi)} {verbo} {con_articolo(evento.colpo)}."


def _testo_causa(codice, nomi, chi):
    return CAUSE[codice].frase.format(chi=_n(nomi, chi))


def _goal(evento, nomi, livello):
    segna = _n(nomi, evento.chi)
    subisce = _chi_subisce(evento)
    zona = (evento.dati or {}).get("zona")
    if evento.causa == "autogoal":
        testo = f"autogoal: {_testo_causa('autogoal', nomi, subisce)}; il goal è di {segna}"
    elif evento.causa == "goal_dopo_difesa_irregolare":
        testo = f"difesa irregolare di {_n(nomi, subisce)}, ma la pallina entra lo stesso: goal di {segna}"
    else:
        testo = f"goal di {segna}"
        if evento.causa == "goal_battuta":
            testo += ", direttamente dalla battuta"
        if zona and subisce is not None:
            testo += f", {_DAL_LATO[zona]} di {_n(nomi, subisce)}" if zona != "centro" else ", al centro"
    if livello == SINTETICA:
        return None
    return f"Doppio fischio: {testo}."


def _fallo(evento, nomi, livello):
    if livello == SINTETICA:
        return None
    chiamata = CHIAMATE[CAUSE[evento.causa].chiamata]
    testo = _testo_causa(evento.causa, nomi, evento.chi)
    clamoroso = " Errore clamoroso." if evento.critico else ""
    return f"Fischio: {chiamata}, {testo}.{clamoroso}"


def _palla_morta(evento, nomi, livello):
    if livello == SINTETICA:
        return None
    return f"Fischio: palla morta, {_testo_causa(evento.causa, nomi, evento.chi)}."


def _rottura(evento, nomi, livello):
    if livello == SINTETICA:
        return None
    testo = _testo_causa(evento.causa, nomi, evento.chi)
    return f"Fischio: {testo}, e il gioco si ferma."


def _sostituzione_attrezzo(evento, nomi, livello):
    if livello == SINTETICA:
        return None
    attrezzo = (evento.dati or {}).get("attrezzo", "paletta")
    return "L'arbitro fa cambiare la paletta." if attrezzo == "paletta" else "L'arbitro cambia la pallina."


def _ripetizione(evento, nomi, livello):
    return None if livello == SINTETICA else "Si ripete il servizio."


def _punto(evento, nomi, livello):
    if livello == SINTETICA:
        return None
    a, b = evento.punteggio
    if evento.punti >= 2:
        return f"{_n(nomi, 'A')} {a}, {_n(nomi, 'B')} {b}."
    io, lui = _punteggio_di((a, b), evento.a_chi)
    return f"Punto a {_n(nomi, evento.a_chi)}, {io} a {lui}."


def _timeout_inizio(evento, nomi, livello):
    return f"Time-out per {_n(nomi, evento.chi)}."


def _timeout_fine(evento, nomi, livello):
    return "Fine del time-out." if livello == TECNICA else None


def _cambio_campo_inizio(evento, nomi, livello):
    # Nella sintetica il cambio campo fra i set lo dice già la fine del set; quello a metà
    # dell'ultimo set, invece, compare accanto alla riga del punto.
    if (evento.dati or {}).get("fra_set"):
        return None if livello == SINTETICA else "Cambio campo: un minuto di pausa."
    a, b = evento.punteggio
    return f"Cambio campo, sul {a} a {b}."


def _cambio_campo_fine(evento, nomi, livello):
    return "Si riprende." if livello == TECNICA else None


def _ammonizione(evento, nomi, livello):
    chi = _n(nomi, evento.chi)
    return f"Ammonizione a {chi}, che {CAUSE[evento.causa].frase}."


def _penalita(evento, nomi, livello):
    chi = _n(nomi, evento.chi)
    causa = CAUSE[evento.causa]
    seconda = (evento.dati or {}).get("seconda_infrazione")
    motivo = f", seconda infrazione: {causa.frase}" if seconda else f": {causa.frase}"
    io, lui = _punteggio_di(evento.punteggio, evento.a_chi)
    return f"Penalità a {chi}{motivo}. Due punti a {_n(nomi, evento.a_chi)}, {io} a {lui}."


def _cambio_al_tavolo(evento, nomi, livello):
    if livello == SINTETICA:
        return None
    d = evento.dati
    return f"Cambio al tavolo: esce {_n(nomi, d['esce'])}, entra {_n(nomi, d['entra'])}; batte {_n(nomi, d['batte'])}."


def _sostituzione(evento, nomi, livello):
    d = evento.dati
    return f"Sostituzione: esce {_n(nomi, d['esce'])}, entra {_n(nomi, d['entra'])}."


_FRASI = {
    E.INIZIO_INCONTRO: _inizio_incontro, E.SORTEGGIO: _sorteggio, E.FORMAZIONI: _formazioni, E.RISCALDAMENTO_INIZIO: _riscaldamento_inizio, E.RISCALDAMENTO_COLPO: _riscaldamento_colpo,
    E.AVVISO_TEMPO: _avviso_tempo, E.RISCALDAMENTO_FINE: _riscaldamento_fine, E.INIZIO_SET: _inizio_set, E.RECUPERO: _recupero, E.CONSEGNA: _consegna,
    E.ANNUNCIO: _annuncio, E.DOMANDA_PRONTO: _domanda_pronto, E.FISCHIO: _fischio, E.CHIAMATA: _chiamata, E.CAMBIO_BATTITORE: _cambio_battitore,
    E.FINE_SET: _fine_set, E.FINE_INCONTRO: _fine_incontro, E.BATTUTA: _battuta, E.VOLO: _volo, E.PARATA: _parata, E.CAMBIO_MANO: _cambio_mano,
    E.CONTROLLO: _controllo, E.COLPO: _colpo, E.GOAL: _goal, E.FALLO: _fallo, E.PALLA_MORTA: _palla_morta, E.ROTTURA: _rottura,
    E.SOSTITUZIONE_ATTREZZO: _sostituzione_attrezzo, E.RIPETIZIONE: _ripetizione, E.PUNTO: _punto, E.TIMEOUT_INIZIO: _timeout_inizio,
    E.TIMEOUT_FINE: _timeout_fine, E.CAMBIO_CAMPO_INIZIO: _cambio_campo_inizio, E.CAMBIO_CAMPO_FINE: _cambio_campo_fine, E.AMMONIZIONE: _ammonizione,
    E.PENALITA: _penalita, E.CAMBIO_AL_TAVOLO: _cambio_al_tavolo, E.SOSTITUZIONE: _sostituzione,
}


# I momenti e la cronaca intera.

def riga_sintetica(esito, nomi):
    """Un punto in una riga: chi batte, quanti colpi, come finisce e il punteggio."""
    battitore = _n(nomi, esito.battitore)
    if esito.attacchi == 0:
        inizio = f"Battuta di {battitore}"
    elif esito.attacchi == 1:
        inizio = f"Battuta di {battitore}, un colpo di scambio"
    else:
        inizio = f"Battuta di {battitore}, scambio di {esito.attacchi} colpi"
    a, b = esito.punteggio
    punteggio = f"{_n(nomi, 'A')} {a}, {_n(nomi, 'B')} {b}."
    if esito.esito == "goal":
        segna = esito.battitore if esito.parte_battitore == esito.a_chi else esito.ricevitore
        if esito.causa == "autogoal":
            fine = f"autogoal, il punto va a {_n(nomi, segna)}"
        elif esito.causa == "goal_battuta":
            fine = "goal di battuta"
        elif esito.colpo_decisivo and esito.causa != "goal_ribattuta":
            fine = f"goal di {_n(nomi, segna)} con {con_articolo(esito.colpo_decisivo)}"
        else:
            fine = f"goal di {_n(nomi, segna)}"
        return f"{inizio}: {fine}. {punteggio}"
    if esito.esito == "fallo":
        chiamata = CHIAMATE[CAUSE[esito.causa].chiamata]
        return f"{inizio}: {chiamata} di {_n(nomi, esito.chi_commette)}. {punteggio}"
    if esito.esito == "palla_morta":
        return f"{inizio}: palla morta, si ripete il servizio."
    return f"{inizio}: il gioco si ferma per una rottura, si ripete il servizio."


def righe_del_momento(momento, nomi, livello=NORMALE):
    """Le righe di un momento dell'incontro al livello indicato, una frase per riga."""
    righe = []
    if livello == SINTETICA and momento.genere == "punto" and momento.esito is not None:
        righe.append(riga_sintetica(momento.esito, nomi))
        for evento in momento.eventi:
            if evento.tipo in (E.TIMEOUT_INIZIO, E.CAMBIO_CAMPO_INIZIO, E.SOSTITUZIONE, E.AMMONIZIONE, E.PENALITA):
                testo = frase(evento, nomi, SINTETICA)
                if testo:
                    righe.append(testo)
        return righe
    for evento in momento.eventi:
        testo = frase(evento, nomi, livello)
        if testo:
            righe.append(testo)
    return righe


def componi(momenti, nomi, livello=NORMALE):
    """Tutte le righe della cronaca, momento dopo momento."""
    righe = []
    for momento in momenti:
        righe.extend(righe_del_momento(momento, nomi, livello))
    return righe


def data_a_parole(dt):
    return f"{dt.day} {MESI[dt.month - 1]} {dt.year}"


def intestazione(risultato, nomi, istante_reale, data_simulata):
    """Le prime righe del file della cronaca: chi gioca, il formato, quando, e il seme per rigiocarla."""
    righe = [f"Cronaca dell'incontro fra {_n(nomi, 'A')} e {_n(nomi, 'B')}, {risultato.formato.nome}."]
    # L'articolo si elide davanti all'8 e all'11: l'8 ottobre, l'11 marzo.
    articolo = "l'" if istante_reale.day in (8, 11) else "il "
    quando = f"Giocato {articolo}{data_a_parole(istante_reale)} alle {istante_reale:%H:%M}"
    if data_simulata is not None:
        quando += f", data simulata {data_a_parole(data_simulata)}"
    righe.append(quando + ".")
    righe.append(f"Il seme della partita è {risultato.seme}: con lo stesso seme la partita si rigioca identica.")
    if risultato.durata_simulata is not None:
        minuti, secondi = divmod(round(risultato.durata_simulata), 60)
        righe.append(f"Durata simulata: {minuti} minuti e {secondi} secondi.")
    return righe


def riepilogo(risultato, nomi):
    """Il riepilogo di fine cronaca, giocatore per giocatore: goal, goal di battuta, falli per causa, sanzioni e scambio più lungo."""
    righe = []
    for gid, stats in risultato.statistiche.items():
        if not stats.azioni and not stats.ammonizioni and not stats.penalita:
            continue
        falli = sum(stats.falli.values())
        testo = f"{_n(nomi, gid)}: {stats.goal} goal"
        if stats.goal_battuta:
            testo += f", di cui {stats.goal_battuta} di battuta"
        if falli:
            chiamate = {}
            for codice, quanti in stats.falli.items():
                chiave = CHIAMATE[CAUSE[codice].chiamata] if CAUSE[codice].famiglia != "goal" else "difesa irregolare con goal"
                chiamate[chiave] = chiamate.get(chiave, 0) + quanti
            dettaglio = ", ".join(f"{quanti} {chiave}" for chiave, quanti in sorted(chiamate.items(), key=lambda v: (-v[1], v[0])))
            testo += f"; {falli} {'fallo' if falli == 1 else 'falli'}: {dettaglio}"
        else:
            testo += "; nessun fallo"
        if stats.ammonizioni:
            testo += f"; {stats.ammonizioni} {'ammonizione' if stats.ammonizioni == 1 else 'ammonizioni'}"
        if stats.penalita:
            testo += f"; {stats.penalita} penalità"
        testo += f"; scambio più lungo di {stats.scambio_piu_lungo} colpi."
        righe.append(testo)
    return righe


def riga_di_stato(stato, nomi):
    """La riga della barra braille per la live: il dato essenziale nei primi 40 caratteri, come Set 2, 7 a 5, batte Rossi."""
    a, b = stato.punteggio
    testo = f"Set {stato.set_n}, {a} a {b}"
    if stato.finito:
        return testo + ", finito"
    if stato.battitore is not None:
        testo += f", batte {_n(nomi, stato.battitore)}"
    sa, sb = stato.set_vinti
    return testo + f". Set {sa} a {sb}, servizio {stato.numero_servizio}."


_VIETATI = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def cartella_cronache():
    return os.path.join(percorsi.cartella(), CARTELLA_CRONACHE)


def nome_file(nomi, istante, cartella=None):
    """Il nome del file della cronaca, come 2026-10-07 15.30.12 Rossi contro Bianchi.txt, con un suffisso se esiste già."""
    titolo = _VIETATI.sub("", f"{_n(nomi, 'A')} contro {_n(nomi, 'B')}").strip(" .")
    base = f"{istante:%Y-%m-%d %H.%M.%S} {titolo}"
    cartella = cartella or cartella_cronache()
    nome = f"{base}.txt"
    numero = 2
    while os.path.exists(os.path.join(cartella, nome)):
        nome = f"{base} ({numero}).txt"
        numero += 1
    return nome


def salva(righe, nome, cartella=None):
    """Scrive la cronaca in UTF-8 nella cartella delle cronache, che crea se manca; restituisce il percorso."""
    cartella = cartella or cartella_cronache()
    os.makedirs(cartella, exist_ok=True)
    percorso = os.path.join(cartella, nome)
    with open(percorso, "w", encoding="utf-8") as f:
        f.write("\n".join(righe) + "\n")
    return percorso


def salva_eventi(eventi, percorso):
    """Gli eventi in un file JSON, per i banchi d'ascolto della tappa 10."""
    with open(percorso, "w", encoding="utf-8") as f:
        json.dump(E.eventi_in_json(eventi), f, ensure_ascii=False, indent=1)
    return percorso
