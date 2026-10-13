"""
Le iscrizioni ai tornei di MESS: le regole, le iscrizioni automatiche e quelle a mano, i pagamenti e i rimborsi.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-14 con la tappa 12, decisione D32, risposte 2, 3, 10, 17 e 19 di Gabriele e punti
5.3, 5.4, 5.7 e 5.8 del progetto. Lavora sul calendario del mondo, che gli passa chi chiama.
Il ritmo è di Gabriele: un torneo ogni due mesi simulati per atleta, per il computer, per i liberi e
per l'iscrizione automatica dei tuoi tesserati; a mano no, e iscrivi i tuoi quanto vuoi. Ogni atleta
ha la data da cui l'iscrizione automatica può fargli cominciare il torneo seguente, prossimo_torneo,
che si aggiorna al sorteggio di ogni edizione che gioca, anche di quelle a cui l'hai iscritto a mano:
61 giorni dopo l'inizio, più o meno uno scarto di 3 giorni. Il sorteggio e non l'iscrizione, scelta
dell'architetto: un'iscrizione tolta o un'edizione annullata non hanno date da rimettere.
È in attesa chi ha la data vuota o entro una settimana, chi può giocare e chi non è già iscritto.
Per lui si cercano le edizioni aperte a cui è idoneo, che cominciano dalla sua data in poi e non si
sovrappongono ai suoi impegni; fra quelle che cominciano nella settimana che segue la sua data sceglie
la più importante, poi la più vicina, poi quella del suo sesso prima dell'aperta, poi il nome; se
nessuna comincia in quella settimana, la più vicina.
Il computer iscrive ogni tesserato sano in attesa, se la cassa meno la quota resta sopra il monte
stipendi del mese, e salta chi ha giocato troppo di recente: l'eccesso di carico, la costanza recente
meno quella della sua seduta, deve stare sotto una soglia che scende con l'età, risposta 3. Il mondo
iscrive i liberi con la stessa regola, gratis. E iscrive i tuoi tesserati con l'iscrizione automatica
accesa, saltando gli infortunati; se la cassa non basta non iscrive, e lo conta una volta per atleta
e per edizione; la regola del carico non vale per i tuoi.
A mano dici tu: un no soltanto se il giocatore non è un tuo tesserato della polisportiva attiva, se
non è idoneo, se l'edizione è chiusa, se si sovrappone a un altro suo impegno, o se la cassa non ha
la quota. Iscrivere paga, togliere rimborsa; nessuno dei due tocca la data del ritmo.
Il campionato mondiale convoca all'apertura delle iscrizioni i migliori del suo sesso per i punti
dell'ultimo anno, gratis, risposta 10; un'iscrizione che si sovrappone ai suoi giorni si annulla col
rimborso, perché il mondiale ha la precedenza.
"""

import datetime
import random

import classe
import modelli_torneo
import palmares
from costanti import (
    COSTANZA_LIBERI,
    ETA_SOGLIA_CARICO_ANZIANI,
    ETA_SOGLIA_CARICO_GIOVANI,
    GIORNI_ANTICIPO_ISCRIZIONE,
    GIORNI_FRA_TORNEI,
    INTENSITA,
    SCARTO_FRA_TORNEI,
    SOGLIA_ECCESSO_CARICO_ANZIANI,
    SOGLIA_ECCESSO_CARICO_GIOVANI,
)
from economia import scritta_in_euro
from utilita import accorda, data_breve

COMPUTER = "computer"
MANO = "mano"
AUTOMATICA = "automatica"
LIBERO = "libero"
QUALIFICATO = "qualificato"
ORIGINI = (COMPUTER, MANO, AUTOMATICA, LIBERO, QUALIFICATO)


def _giorno(data):
    return data.date() if isinstance(data, datetime.datetime) else data


def nome_completo(g):
    return f"{g.nome} {g.cognome}"


# Il club e la sua chiave.

def club_della(poli):
    """Una polisportiva come la conservano un'iscrizione e una sfida: il nome e il giorno di fondazione."""
    return {"nome": poli.nome, "fondazione": poli.datetime_creazione_sim.date().isoformat()}


def club_di(mondo, g):
    """Il club del giocatore, come lo conserva un'iscrizione: il nome e il giorno di fondazione; None per i liberi."""
    poli = mondo.polisportive.get(g.appartenenza)
    if poli is None:
        return None
    return club_della(poli)


def polisportiva_del_club(mondo, club):
    """La polisportiva di un club conservato, se esiste ancora: lo stesso nome e lo stesso giorno di fondazione; altrimenti None."""
    if club is None:
        return None
    poli = mondo.polisportive.get(club["nome"])
    if poli is None or poli.datetime_creazione_sim.date().isoformat() != club["fondazione"]:
        return None
    return poli


def tuo(mondo, g):
    """Vero se il giocatore è un tesserato di una polisportiva dell'utente."""
    poli = mondo.polisportive.get(g.appartenenza)
    return poli is not None and not poli.is_cpu_controlled


# Il ritmo e il carico.

def aggiorna_ritmo(g, data_inizio, id_edizione):
    """
    La data del ritmo dopo il sorteggio di un'edizione che il giocatore gioca: la più tarda fra quella
    di adesso e l'inizio più GIORNI_FRA_TORNEI, più o meno uno scarto tirato dal numero del giocatore e
    dell'edizione, senza toccare il caso del mondo.
    """
    scarto = random.Random(f"MESS-ritmo-{g.id}-{id_edizione}").randint(-SCARTO_FRA_TORNEI, SCARTO_FRA_TORNEI)
    inizio = data_inizio if isinstance(data_inizio, datetime.datetime) else datetime.datetime.combine(data_inizio, datetime.time(9, 0))
    nuova = inizio + datetime.timedelta(days=GIORNI_FRA_TORNEI + scarto)
    if g.prossimo_torneo is None or g.prossimo_torneo < nuova:
        g.prossimo_torneo = nuova


def soglia_carico(anni):
    """La soglia dell'eccesso di carico: 0,15 fino ai 45 anni, poi in linea retta fino a 0,05 a 65, e 0,05 oltre."""
    if anni <= ETA_SOGLIA_CARICO_GIOVANI:
        return SOGLIA_ECCESSO_CARICO_GIOVANI
    if anni >= ETA_SOGLIA_CARICO_ANZIANI:
        return SOGLIA_ECCESSO_CARICO_ANZIANI
    quota = (anni - ETA_SOGLIA_CARICO_GIOVANI) / (ETA_SOGLIA_CARICO_ANZIANI - ETA_SOGLIA_CARICO_GIOVANI)
    return SOGLIA_ECCESSO_CARICO_GIOVANI + quota * (SOGLIA_ECCESSO_CARICO_ANZIANI - SOGLIA_ECCESSO_CARICO_GIOVANI)


def eccesso_carico(g, libero):
    """La costanza recente meno quella della seduta del giocatore: dei liberi, o della sua intensità."""
    seduta = COSTANZA_LIBERI if libero else INTENSITA[g.intensita]["costanza"]
    return g.costanza - seduta


def troppo_carico(g, libero):
    """Vero se il giocatore ha giocato troppo di recente per il computer: l'eccesso di carico sopra la soglia della sua età."""
    return eccesso_carico(g, libero) > soglia_carico(g.eta_anni)


# Le scelte.

def _sovrapposta(inizio, fine, impegni):
    return any(inizio <= fine_impegno and inizio_impegno <= fine for inizio_impegno, fine_impegno in impegni)


def candidate(edizioni, g, s, impegni):
    """Le edizioni aperte a cui il giocatore è idoneo, che cominciano da s in poi e non si sovrappongono ai suoi impegni."""
    scelte = []
    for ed in edizioni:
        if ed.data_inizio < s or not ed.individuale or ed.qualificazione != modelli_torneo.NESSUNA:
            continue
        if ed.sesso != "aperto" and ed.sesso != g.sesso:
            continue
        if ed.filtri and not modelli_torneo.idoneo(ed.oggetto_modello, g):
            continue
        if _sovrapposta(ed.data_inizio, ed.data_fine, impegni):
            continue
        scelte.append(ed)
    return scelte


def scegli(edizioni, g, s, impegni):
    """
    L'edizione che l'iscrizione automatica sceglie per il giocatore, dalla data s: fra quelle che
    cominciano entro una settimana da s la più importante, poi la più vicina, poi quella del suo sesso
    prima dell'aperta, poi il nome; se nessuna comincia in quella settimana, la più vicina. None se non ce n'è.
    """
    scelte = candidate(edizioni, g, s, impegni)
    if not scelte:
        return None
    finestra = s + datetime.timedelta(days=GIORNI_ANTICIPO_ISCRIZIONE)
    vicine = [ed for ed in scelte if ed.data_inizio <= finestra]
    if vicine:
        return min(vicine, key=lambda ed: (-ed.importanza, ed.data_inizio, 0 if ed.sesso == g.sesso else 1, ed.nome))
    return min(scelte, key=lambda ed: (ed.data_inizio, -ed.importanza, 0 if ed.sesso == g.sesso else 1, ed.nome))


# I pagamenti.

def paga(poli, euro):
    """La quota esce dalla cassa, nella voce delle iscrizioni del mese."""
    poli.cassa -= euro
    poli.conti_del_mese["iscrizioni"] += euro


def rimborsa(mondo, iscritto, data=None):
    """Il rimborso di una quota al club che l'ha pagata, se esiste ancora, nella voce dei rimborsi del mese in cui arriva; restituisce gli euro."""
    euro = iscritto.get("pagato", 0)
    poli = polisportiva_del_club(mondo, iscritto.get("club"))
    if euro <= 0 or poli is None:
        return 0
    poli.cassa += euro
    poli.conti_del_mese["rimborsi"] += euro
    return euro


# Le iscrizioni automatiche.

def automatiche(mondo, calendario, data, rapporto):
    """
    Le iscrizioni automatiche del giorno: il computer, i liberi e i tuoi tesserati con l'iscrizione
    automatica accesa, chi è in attesa, ciascuno all'edizione che la regola sceglie per lui.
    """
    oggi = _giorno(data)
    domani = oggi + datetime.timedelta(days=1)
    limite = oggi + datetime.timedelta(days=GIORNI_ANTICIPO_ISCRIZIONE)
    aperte = [ed for ed in calendario.edizioni if ed.data_inizio >= domani and ed.individuale and ed.qualificazione == modelli_torneo.NESSUNA]
    if not aperte:
        return
    iscritti = calendario.iscritti_alle_edizioni()
    impegni = calendario.impegni(mondo)
    morti = mondo._ids_morti_processati_sessione
    monti = {}
    for gid, g in mondo.giocatori.items():
        if g.ritirato or gid in morti or g.infortunato or gid in iscritti:
            continue
        prossimo = g.prossimo_torneo
        if prossimo is not None and prossimo.date() > limite:
            continue
        poli = mondo.polisportive.get(g.appartenenza)
        if poli is None:
            if troppo_carico(g, True):
                continue
        elif poli.is_cpu_controlled:
            if troppo_carico(g, False):
                continue
        elif not g.iscrizione_automatica:
            continue
        s = max(domani, prossimo.date()) if prossimo is not None else domani
        ed = scegli(aperte, g, s, impegni.get(gid, ()))
        if ed is None:
            continue
        quota = ed.quota if poli is not None else 0
        if poli is None:
            ed.aggiungi(gid, None, 0, LIBERO)
            continue
        if poli.is_cpu_controlled:
            if poli.nome not in monti:
                monti[poli.nome] = mondo.monte_stipendi(poli)
            if poli.cassa - quota < monti[poli.nome]:
                continue
            paga(poli, quota)
            ed.aggiungi(gid, club_di(mondo, g), quota, COMPUTER)
            continue
        if poli.cassa < quota:
            if calendario.conta_saltata(gid, ed.id):
                rapporto["tue_iscrizioni_saltate"] += 1
            continue
        paga(poli, quota)
        ed.aggiungi(gid, club_di(mondo, g), quota, AUTOMATICA)
        rapporto["tue_iscrizioni"] += 1
        testo = f"Iscritto in automatico a {ed.nome}, che comincia il {data_breve(ed.data_inizio)}" + (f": {scritta_in_euro(quota)}." if quota else ".")
        mondo.annota(g, testo.replace("Iscritto", accorda(g.sesso, "Iscritto"), 1))
        mondo.annota(poli, f"{nome_completo(g)} {accorda(g.sesso, 'iscritto')} in automatico a {ed.nome}, dal {data_breve(ed.data_inizio)}"
                     + (f": {scritta_in_euro(quota)}." if quota else "."))


# Le iscrizioni a mano.

def _edizione(calendario, id_edizione):
    return next((ed for ed in calendario.edizioni if ed.id == id_edizione), None)


def problema_iscrizione(mondo, id_edizione, g, poli):
    """
    Perché l'utente non può iscrivere il giocatore all'edizione con la polisportiva, in una frase,
    oppure None se può: soltanto un tuo tesserato della polisportiva attiva, idoneo, a un'edizione
    aperta, senza un altro impegno negli stessi giorni, con la quota nella cassa. La regola dei due mesi
    a mano non c'è, risposta 2; l'infortunato si può iscrivere, a suo rischio.
    """
    calendario = mondo.calendario
    ed = _edizione(calendario, id_edizione)
    oggi = _giorno(mondo.datetime_corrente_simulazione)
    if ed is None or ed.data_inizio <= oggi:
        return "Le iscrizioni di questa edizione sono chiuse."
    if poli is None or poli.is_cpu_controlled or g.id not in poli.tesserati:
        return f"{nome_completo(g)} non è {accorda(g.sesso, 'tesserato')} con la tua polisportiva attiva."
    if g.ritirato:
        return f"{nome_completo(g)} si è {accorda(g.sesso, 'ritirato')} dall'attività."
    if not ed.individuale or ed.qualificazione != modelli_torneo.NESSUNA:
        return f"A {ed.nome} si entra per qualificazione, non con l'iscrizione."
    if (ed.sesso != "aperto" and ed.sesso != g.sesso) or (ed.filtri and not modelli_torneo.idoneo(ed.oggetto_modello, g)):
        return f"{nome_completo(g)} non può giocare {ed.nome}: è un torneo per altri giocatori."
    if g.id in ed.ids():
        return f"{nome_completo(g)} è già {accorda(g.sesso, 'iscritto')} a {ed.nome}."
    for inizio, fine, descrizione in calendario.impegni_descritti(mondo, g.id):
        if inizio <= ed.data_fine and ed.data_inizio <= fine:
            return f"{nome_completo(g)} negli stessi giorni ha già {descrizione}: due tornei negli stessi giorni non si giocano."
    if poli.cassa < ed.quota:
        return f"La cassa di {poli.nome} ha {scritta_in_euro(poli.cassa)}: l'iscrizione costa {scritta_in_euro(ed.quota)}."
    return None


def iscrivi(mondo, id_edizione, g, poli):
    """L'utente iscrive a mano il suo tesserato: paga la quota, voce iscrizioni; ValueError col motivo se non si può. La data del ritmo non si tocca."""
    problema = problema_iscrizione(mondo, id_edizione, g, poli)
    if problema:
        raise ValueError(problema)
    ed = _edizione(mondo.calendario, id_edizione)
    paga(poli, ed.quota)
    ed.aggiungi(g.id, club_di(mondo, g), ed.quota, MANO)
    mondo.annota(g, f"{accorda(g.sesso, 'Iscritto')} a {ed.nome}, che comincia il {data_breve(ed.data_inizio)}.")
    mondo.annota(poli, f"Iscrive {nome_completo(g)} a {ed.nome}" + (f", per {scritta_in_euro(ed.quota)}." if ed.quota else "."))
    return ed


def problema_ritiro(mondo, id_edizione, g, poli):
    """Perché l'utente non può togliere il giocatore dall'edizione, oppure None: fino al sorteggio, soltanto i suoi tesserati iscritti."""
    ed = _edizione(mondo.calendario, id_edizione)
    if ed is None or ed.data_inizio <= _giorno(mondo.datetime_corrente_simulazione):
        return "Il sorteggio è già fatto: l'iscrizione non si toglie più."
    iscritto = ed.iscritto(g.id)
    if iscritto is None:
        return f"{nome_completo(g)} non è {accorda(g.sesso, 'iscritto')} a {ed.nome}."
    if poli is None or poli.is_cpu_controlled or (g.id not in poli.tesserati and polisportiva_del_club(mondo, iscritto["club"]) is not poli):
        return f"{nome_completo(g)} non è un tuo tesserato."
    return None


def togli(mondo, id_edizione, g, poli):
    """
    L'utente toglie il suo tesserato dall'edizione, fino al sorteggio: la quota torna, voce rimborsi.
    Dal mondiale, il posto passa al primo dei non convocati. Restituisce il rimborso; ValueError col motivo.
    """
    problema = problema_ritiro(mondo, id_edizione, g, poli)
    if problema:
        raise ValueError(problema)
    ed = _edizione(mondo.calendario, id_edizione)
    iscritto = ed.togli(g.id)
    euro = rimborsa(mondo, iscritto)
    mondo.annota(g, f"Non gioca più {ed.nome}: l'iscrizione è tolta.")
    mondo.annota(poli, f"Toglie {nome_completo(g)} da {ed.nome}" + (f": rimborso di {scritta_in_euro(euro)}." if euro else "."))
    if ed.qualificazione == modelli_torneo.PUNTI_ANNO:
        # Chi hai tolto non torna convocato: resta fra gli esclusi, come gli infortunati sostituiti.
        ed.esclusi.append(g.id)
        sostituto = prossimo_convocato(mondo, ed)
        if sostituto is not None:
            ed.aggiungi(sostituto.id, club_di(mondo, sostituto), 0, QUALIFICATO)
    return euro


# Il mondiale, punto 5.8.

def classifica_dell_anno(mondo, sesso, oggi):
    """
    I giocatori in attività del sesso, liberi compresi, per i punti dell'ultimo anno: a parità passa chi
    ha il punteggio di classe più alto, poi l'identificativo più basso, risposta 10 di Gabriele.
    """
    morti = mondo._ids_morti_processati_sessione
    attivi = [g for gid, g in mondo.giocatori.items() if gid not in morti and not g.ritirato and g.sesso == sesso]
    return sorted(attivi, key=lambda g: (-palmares.punti_dell_anno(g, oggi), -classe.punteggio(g), g.id))


def prossimo_convocato(mondo, ed, escludi=()):
    """Il primo della classifica dell'anno che non è già convocato, può giocare e non è escluso; None se non c'è."""
    gia = set(ed.ids()) | set(escludi) | set(ed.esclusi)
    for g in classifica_dell_anno(mondo, ed.sesso, _giorno(mondo.datetime_corrente_simulazione)):
        if g.id not in gia and g.puo_giocare:
            return g
    return None


def convoca_mondiale(mondo, calendario, ed, rapporto):
    """
    All'apertura delle iscrizioni del mondiale si convocano i migliori del suo sesso per i punti
    dell'ultimo anno, fino al tetto, gratis e senza toccare la data del ritmo; le iscrizioni che si
    sovrappongono ai suoi giorni si annullano col rimborso. I tuoi convocati lo sanno dal diario.
    """
    oggi = _giorno(mondo.datetime_corrente_simulazione)
    for g in classifica_dell_anno(mondo, ed.sesso, oggi)[:ed.tetto]:
        for altra in calendario.edizioni:
            if altra is ed or g.id not in altra.ids() or not (altra.data_inizio <= ed.data_fine and ed.data_inizio <= altra.data_fine):
                continue
            rimborsa(mondo, altra.togli(g.id))
            if tuo(mondo, g):
                mondo.annota(g, f"Lascia {altra.nome}: è {accorda(g.sesso, 'convocato')} a {ed.nome}, che ha la precedenza.")
        ed.aggiungi(g.id, club_di(mondo, g), 0, QUALIFICATO)
        if tuo(mondo, g):
            rapporto["tuoi_qualificati"] += 1
            mondo.annota(g, f"{accorda(g.sesso, 'Convocato')} a {ed.nome}, dal {data_breve(ed.data_inizio)}.")
            rapporto["notizie"].append(f"{nome_completo(g)} è {accorda(g.sesso, 'convocato')} a {ed.nome}.")


def sostituisci_gli_infortunati(mondo, ed):
    """Al sorteggio del mondiale chi è infortunato lascia il posto al primo dei non convocati che può giocare."""
    for iscritto in list(ed.iscritti):
        g = mondo.giocatori.get(iscritto["id"])
        if g is not None and g.puo_giocare and not g.ritirato:
            continue
        ed.togli(iscritto["id"])
        ed.esclusi.append(iscritto["id"])
        sostituto = prossimo_convocato(mondo, ed)
        if sostituto is not None:
            ed.aggiungi(sostituto.id, club_di(mondo, sostituto), 0, QUALIFICATO)
