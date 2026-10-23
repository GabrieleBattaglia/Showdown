"""
Le sfide fra polisportive di MESS e la rosa della Coppa delle polisportive.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-14 con la tappa 12, decisione D32, risposte 14, 15 e 16 di Gabriele e punto 8 del
progetto. Una sfida è una gara a squadre IBSA, un set a 31 con 2 di scarto, squadre miste con due
giocatori di un sesso e uno dell'altro al tavolo, senza sostituzioni, D26.
Ogni polisportiva riceve il primo del mese due sfide da lanciare, fino a quattro; una sfida giocata ne
consuma una, una rifiutata o decaduta no. La convocazione prende fra i tesserati che possono giocare e
che quel giorno non hanno un impegno i migliori per punteggio di classe: i titolari sono i primi tre, e
se sono dello stesso sesso il terzo cede il posto al migliore dell'altro; le riserve sono i seguenti,
fino a sei in tutto. Un impegno è un torneo in corso o che comincia quel giorno, la rosa della coppa,
un'altra sfida accettata per quel giorno, o un incontro già giocato quel giorno. Per le tue
polisportive la convocazione è soltanto la proposta: la formazione la decidi tu, risposta 16.
Il computer ha un carattere, prudente, equilibrato o ardito, che nasce dal nome della polisportiva
senza toccare il caso del mondo e senza salvarsi: è la forbice del rapporto fra la forza della squadra
avversaria e la propria dentro cui accetta o lancia. Accetta se il rapporto sta nella forbice, se la
sua ultima sfida è più vecchia di cinque giorni e se convoca una squadra valida; altrimenti dice perché.
Ogni giorno, dopo i tornei, ogni polisportiva del computer con una sfida da lanciare la lancia col 7
per cento, a un bersaglio a caso con una squadra valida e la forza nella sua forbice, fino a tre
tentativi: fra polisportive del computer si gioca subito, con l'esito rapido; a una tua arriva una
proposta, a cui rispondi entro il giorno in cui arriva: all'avanzamento seguente decade, e i testi
dicono quel giorno, ultimo_giorno_per_rispondere, dalla revisione del 14 ottobre 2026, che ha trovato
scritto il giorno dopo, quando la sfida era già decaduta. Le tue sfide le lanci dal menu Partite, e
il computer risponde subito; accettate, si giocano all'avanzamento seguente, col motore vero, e le
fotografie dei giocatori permettono di riascoltarle. Il giorno della sfida la formazione si
riconvoca: chi non c'è più lascia il posto alle riserve, e chi non ha più una squadra valida perde a
tavolino, 31 a 0.
La posta: una coppa d'oro a chi vince e una d'argento a chi perde, nei contatori per sempre e nel
palmarès recente della gloria, con l'importanza piccola delle sfide; dalla decisione 3 di Gabriele
del 14 ottobre 2026 la coppa d'argento vale nella gloria soltanto una piccola parte di quella d'oro,
QUOTA_GLORIA_ARGENTO_SFIDA, così perdere tante sfide non conviene; nessun euro; un punto di
fedeltà a ogni convocato di chi vince. Le sfide delle tue polisportive restano nello storico, le
ultime dieci con la differita; quelle fra polisportive del computer restano nei contatori, nelle voci
aggregate dei diari e nel riepilogo del giorno.
La rosa della Coppa delle polisportive, punto 8.8: all'apertura delle iscrizioni si qualificano le
polisportive con più gloria che convocano una squadra valida per i giorni della coppa, fino al tetto,
e ognuna iscrive la sua rosa, fino a sei, che in quei giorni resta impegnata; per ogni incontro i
titolari sono i tre migliori sani della rosa, nell'ordine della formazione per le tue.
"""

import datetime
import random

import classe
import esito_rapido
import esperienza
import infortuni
import iscrizioni
import palmares
from costanti import (
    CONVOCATI_SFIDA,
    DIFFERITE_SFIDE_TUE,
    FEDELTA_PER_SFIDA_VINTA,
    FORBICI_SFIDA,
    GIOCATORI_AL_TAVOLO,
    GIORNI_RISPOSTA_SFIDA,
    IMPORTANZA_COPPA_SFIDA,
    PROB_LANCIO_SFIDA_CPU,
    QUOTA_GLORIA_ARGENTO_SFIDA,
    RIPOSO_SFIDA_GIORNI,
    TENTATIVI_SFIDA_CPU,
)
from grammatica import torneo_con_preposizione
from modelli import CAMPI_AGGREGATA_POLISPORTIVA, annota_aggregata
from motore import ESSENZIALE, SQUADRE, TAVOLINO, Incontro, Squadra, a_tavolino
from motore.squadre import composizione_valida
from partita import MotorePartita, differita_squadre
from premiazioni import COPPE_A_PAROLE
from utilita import caso, data_breve

PROPOSTA = "proposta"
ACCETTATA = "accettata"
RIFIUTATA = "rifiutata"
DECADUTA = "decaduta"
GIOCATA = "giocata"
STATI = (PROPOSTA, ACCETTATA, RIFIUTATA, DECADUTA, GIOCATA)
CARATTERI = ("prudente", "equilibrata", "ardita")
LATI = ("sfidante", "sfidata")
GARA = "la sfida"


def _giorno(data):
    return data.date() if isinstance(data, datetime.datetime) else data


def _alle_nove(giorno):
    """Il giorno come data con l'ora, per la regola di un impegno al giorno."""
    return giorno if isinstance(giorno, datetime.datetime) else datetime.datetime.combine(giorno, datetime.time(9, 0))


def _unisci(parti):
    # testi importa l'archivio, che importa il calendario, che importa questo modulo: si legge al momento.
    from testi import unisci
    return unisci(parti)


def nome_completo(g):
    return f"{g.nome} {g.cognome}"


def tua(poli):
    """Vero se la polisportiva è dell'utente."""
    return poli is not None and not poli.is_cpu_controlled


# Il carattere e la forza.

_CARATTERI_DEI_NOMI = {}


def carattere(nome):
    """
    Il carattere di una polisportiva del computer, dal suo nome, senza toccare il caso del mondo:
    prudente, equilibrata o ardita. Dalla tappa 12, decisione 4 di Gabriele del 14 ottobre 2026, si
    ricorda per nome: il generatore nato dal nome dà sempre lo stesso carattere, e farlo nascere a ogni
    lancio e a ogni risposta del computer costava migliaia di generatori al giorno.
    """
    risultato = _CARATTERI_DEI_NOMI.get(nome)
    if risultato is None:
        risultato = _CARATTERI_DEI_NOMI[nome] = random.Random(f"MESS-carattere-{nome}").choice(CARATTERI)
    return risultato


def forbice(nome):
    """La forbice del rapporto fra la forza avversaria e la propria dentro cui la polisportiva accetta o lancia una sfida."""
    return FORBICI_SFIDA[carattere(nome)]


def forza_squadra(giocatori, memoria=None):
    """La forza di una squadra: la media della forza dell'esito rapido dei tre titolari."""
    titolari = giocatori[:GIOCATORI_AL_TAVOLO]
    return sum(esito_rapido.forza(g, memoria=memoria) for g in titolari) / len(titolari)


# La convocazione.

def impegnati_il(mondo, giorno, esclusa=None):
    """Chi ha un impegno nel giorno: un torneo in corso o che comincia, la rosa della coppa, un'altra sfida accettata per quel giorno."""
    giorno = _giorno(giorno)
    return mondo.calendario.impegnati_il(giorno) | mondo.sfide.convocati_il(giorno, esclusa)


def disponibile(mondo, g, poli, giorno, impegnati):
    """Vero se il giocatore può giocare una sfida per la polisportiva nel giorno: è suo tesserato, può giocare, non ha impegni né ha già giocato."""
    return (g is not None and g.id not in mondo._ids_morti_processati_sessione and not g.ritirato and g.puo_giocare and g.appartenenza == poli.nome
            and g.id not in impegnati and not g.ha_un_impegno(_alle_nove(giorno)))


def convocabili(mondo, poli, giorno, impegnati=None):
    """I tesserati che possono giocare una sfida nel giorno, in ordine di punteggio di classe, dal migliore."""
    if impegnati is None:
        impegnati = impegnati_il(mondo, giorno)
    giocatori = (mondo.giocatori.get(gid) for gid in poli.tesserati)
    return sorted((g for g in giocatori if disponibile(mondo, g, poli, giorno, impegnati)), key=lambda g: (-classe.punteggio(g), g.id))


def forma(giocatori, quanti=CONVOCATI_SFIDA):
    """
    La squadra dai giocatori nell'ordine dato: i titolari sono i primi tre, e se sono dello stesso
    sesso il terzo cede il posto al migliore dell'altro e diventa la prima riserva; le riserve sono i
    seguenti, fino a quanti in tutto. None se non si arriva a una squadra valida.
    """
    giocatori = list(giocatori)
    if len(giocatori) < GIOCATORI_AL_TAVOLO:
        return None
    titolari = giocatori[:GIOCATORI_AL_TAVOLO]
    resto = giocatori[GIOCATORI_AL_TAVOLO:]
    if not composizione_valida(titolari):
        altro = next((g for g in resto if g.sesso != titolari[0].sesso), None)
        if altro is None:
            return None
        terzo = titolari[2]
        titolari[2] = altro
        resto = [terzo, *(g for g in resto if g is not altro)]
    return titolari + resto[:quanti - GIOCATORI_AL_TAVOLO]


def convoca(mondo, poli, giorno, quanti=CONVOCATI_SFIDA, impegnati=None):
    """La convocazione automatica per il giorno: i giocatori, titolari e riserve, oppure None se non c'è una squadra valida."""
    return forma(convocabili(mondo, poli, giorno, impegnati), quanti)


def schiera(mondo, poli, ids, giorno, impegnati):
    """
    La riconvocazione del giorno della sfida, come nei galà: dalla formazione, nel suo ordine, restano
    i disponibili, e chi non c'è più lascia il posto alle riserve. None se non c'è più una squadra valida.
    """
    presenti = [g for gid in ids if disponibile(mondo, g := mondo.giocatori.get(gid), poli, giorno, impegnati)]
    return forma(presenti)


def problema_formazione(mondo, poli, ids, giorno, esclusa=None):
    """
    Perché la formazione non va, in una frase, oppure None: da tre a sei giocatori, nessun doppione,
    tutti tesserati della polisportiva, in grado di giocare e senza impegni quel giorno, e al tavolo
    due giocatori di un sesso e uno dell'altro. Serve al dialogo della formazione, risposta 16.
    """
    ids = list(ids)
    if len(ids) < GIOCATORI_AL_TAVOLO:
        return "Servono tre titolari."
    if len(ids) > CONVOCATI_SFIDA:
        return f"Si convocano al massimo {CONVOCATI_SFIDA} giocatori, titolari e riserve."
    if len(set(ids)) != len(ids):
        return "Lo stesso giocatore compare due volte nella formazione."
    impegnati = impegnati_il(mondo, giorno, esclusa)
    for gid in ids:
        g = mondo.giocatori.get(gid)
        if g is None or g.appartenenza != poli.nome or gid in mondo._ids_morti_processati_sessione:
            return f"Il giocatore {gid} non è un tesserato di {poli.nome}."
        if g.ritirato or not g.puo_giocare:
            return f"{nome_completo(g)} non può giocare: è {'infortunato' if g.sesso == 'm' else 'infortunata'}."
        if gid in impegnati or g.ha_un_impegno(_alle_nove(giorno)):
            return f"{nome_completo(g)} quel giorno ha già un impegno."
    if not composizione_valida([mondo.giocatori[gid] for gid in ids[:GIOCATORI_AL_TAVOLO]]):
        return "Al tavolo servono due giocatori di un sesso e uno dell'altro."
    return None


def in_riposo(mondo, poli, giorno):
    """Vero se la polisportiva ha giocato una sfida, o ne ha una accettata, a meno di cinque giorni dal giorno dato."""
    giorno = _giorno(giorno)
    date = [_giorno(poli.ultima_sfida)] if poli.ultima_sfida is not None else []
    date += [s.data_gioco for s in mondo.sfide.attive if s.stato == ACCETTATA and poli.nome in (s.sfidante["nome"], s.sfidata["nome"])]
    return any(abs((giorno - d).days) < RIPOSO_SFIDA_GIORNI for d in date)


def valuta(mondo, poli, forza_avversaria, giorno, memoria=None, impegnati=None):
    """
    La risposta del computer a una sfida per il giorno dato, D32: i convocati e None se accetta,
    oppure None e il motivo, per il riposo, per la squadra o per la forbice del suo carattere.
    """
    if in_riposo(mondo, poli, giorno):
        return None, f"{poli.nome} ha appena giocato una sfida, e riposa."
    convocati = convoca(mondo, poli, giorno, impegnati=impegnati)
    if convocati is None:
        return None, f"{poli.nome} quel giorno non ha una squadra valida."
    propria = forza_squadra(convocati, memoria)
    basso, alto = forbice(poli.nome)
    rapporto = forza_avversaria / propria if propria > 0 else float("inf")
    if rapporto < basso:
        return None, f"{poli.nome} vi trova troppo deboli per una sfida."
    if rapporto > alto:
        return None, f"{poli.nome} vi trova troppo forti per una sfida."
    return convocati, None


# La sfida e il registro.

def _data(testo):
    return None if testo is None else datetime.date.fromisoformat(testo)


def _club_valido(club):
    return isinstance(club, dict) and set(club) == {"nome", "fondazione"} and all(isinstance(v, str) for v in club.values())


class Sfida:
    """
    Una sfida: l'identificativo, la sfidante e la sfidata col loro giorno di fondazione, i giorni del
    lancio, della scadenza della risposta e del gioco, lo stato, i convocati per club nell'ordine della
    formazione, il seme, e dopo il gioco il risultato e, per le tue, la differita.
    """

    __slots__ = ("convocati", "data_gioco", "differita", "id", "lancio", "risultato", "scadenza", "seme", "sfidante", "sfidata", "stato")

    def __init__(self, id_sfida, sfidante, sfidata, lancio, scadenza, stato=PROPOSTA, data_gioco=None, convocati=None, seme=None, risultato=None,
                 differita=None):
        self.id = id_sfida
        self.sfidante = dict(sfidante)
        self.sfidata = dict(sfidata)
        self.lancio = lancio
        self.scadenza = scadenza
        self.stato = stato
        self.data_gioco = data_gioco
        self.convocati = {lato: list((convocati or {}).get(lato, [])) for lato in LATI}
        self.seme = seme if seme is not None else random.Random(f"MESS-sfida-{id_sfida}-{lancio.isoformat()}").getrandbits(63)
        self.risultato = risultato
        self.differita = differita

    def club(self, lato):
        return self.sfidante if lato == "sfidante" else self.sfidata

    def di(self, nome):
        """Il lato della polisportiva nella sfida, sfidante o sfidata, oppure None."""
        return next((lato for lato in LATI if self.club(lato)["nome"] == nome), None)

    def a_dizionario(self):
        return {"id": self.id, "sfidante": dict(self.sfidante), "sfidata": dict(self.sfidata), "lancio": self.lancio.isoformat(),
                "scadenza": self.scadenza.isoformat(), "stato": self.stato, "data_gioco": self.data_gioco.isoformat() if self.data_gioco else None,
                "convocati": {lato: list(ids) for lato, ids in self.convocati.items()}, "seme": self.seme, "risultato": self.risultato,
                "differita": self.differita}

    @classmethod
    def da_dizionario(cls, dati):
        """La sfida dal salvataggio; ValueError col motivo se non va."""
        if not isinstance(dati, dict) or set(dati) != set(cls.__slots__):
            raise ValueError("Una sfida salvata ha i campi sbagliati.")
        if not isinstance(dati["id"], int) or isinstance(dati["id"], bool) or dati["id"] < 1 or not isinstance(dati["seme"], int):
            raise ValueError("Una sfida salvata ha un identificativo o un seme non validi.")
        if not _club_valido(dati["sfidante"]) or not _club_valido(dati["sfidata"]) or dati["stato"] not in STATI:
            raise ValueError(f"La sfida {dati['id']} ha i club o lo stato non validi.")
        convocati = dati["convocati"]
        if not isinstance(convocati, dict) or set(convocati) != set(LATI) or not all(
                isinstance(ids, list) and all(isinstance(x, int) and not isinstance(x, bool) for x in ids) for ids in convocati.values()):
            raise ValueError(f"La sfida {dati['id']} ha i convocati non validi.")
        if dati["risultato"] is not None and not (isinstance(dati["risultato"], dict) and {"esito", "vince", "punti"} <= set(dati["risultato"])):
            raise ValueError(f"La sfida {dati['id']} ha il risultato non valido.")
        if dati["differita"] is not None and not isinstance(dati["differita"], dict):
            raise ValueError(f"La sfida {dati['id']} ha la differita non valida.")
        try:
            lancio, scadenza, data_gioco = _data(dati["lancio"]), _data(dati["scadenza"]), _data(dati["data_gioco"])
        except (TypeError, ValueError):
            raise ValueError(f"La sfida {dati['id']} ha le date non valide.") from None
        if lancio is None or scadenza is None:
            raise ValueError(f"La sfida {dati['id']} ha le date non valide.")
        return cls(dati["id"], dati["sfidante"], dati["sfidata"], lancio, scadenza, dati["stato"], data_gioco, convocati, dati["seme"],
                   dati["risultato"], dati["differita"])


class RegistroSfide:
    """
    Le sfide del mondo, salvate: quelle attive, proposte o accettate; lo storico delle sfide con una tua
    polisportiva, le ultime DIFFERITE_SFIDE_TUE con la differita; il contatore; e chi ha giocato una
    sfida nell'ultimo giorno, per dire che impegno ha avuto.
    """

    def __init__(self):
        self.attive = []
        self.storico = []
        self.prossimo_id = 1
        self.giocate_oggi = {"data": None, "ids": []}

    def nuovo_id(self):
        nuovo = self.prossimo_id
        self.prossimo_id += 1
        return nuovo

    def sfida(self, id_sfida):
        return next((s for s in (*self.attive, *self.storico) if s.id == id_sfida), None)

    def convocati_il(self, giorno, esclusa=None):
        """I convocati delle sfide accettate per il giorno, tranne quella esclusa."""
        return {gid for s in self.attive if s is not esclusa and s.stato == ACCETTATA and s.data_gioco == giorno for ids in s.convocati.values() for gid in ids}

    def impegni(self):
        """Gli impegni delle sfide accettate, per giocatore, come intervalli di un giorno: li vede l'iscrizione ai tornei."""
        impegni = {}
        for s in self.attive:
            if s.stato == ACCETTATA:
                for ids in s.convocati.values():
                    for gid in ids:
                        impegni.setdefault(gid, []).append((s.data_gioco, s.data_gioco))
        return impegni

    def lanciate_in_sospeso(self, nome):
        """Le sfide lanciate dalla polisportiva e non ancora giocate: contano fra quelle già usate."""
        return sum(1 for s in self.attive if s.sfidante["nome"] == nome and s.stato in (PROPOSTA, ACCETTATA))

    def proposte_per(self, nome):
        """Le sfide che aspettano la risposta della polisportiva."""
        return [s for s in self.attive if s.stato == PROPOSTA and s.sfidata["nome"] == nome]

    def rifiutata_oggi(self, nome, bersaglio, oggi):
        """Vero se oggi il bersaglio ha già rifiutato una sfida della polisportiva: si riprova domani."""
        return any(s.stato == RIFIUTATA and s.sfidante["nome"] == nome and s.sfidata["nome"] == bersaglio and s.lancio == oggi for s in self.storico)

    def archivia(self, s):
        """Una sfida con una tua polisportiva entra nello storico; soltanto le ultime DIFFERITE_SFIDE_TUE tengono la differita."""
        self.storico.append(s)
        con_differita = [x for x in self.storico if x.differita]
        for vecchia in con_differita[:-DIFFERITE_SFIDE_TUE]:
            vecchia.differita = None

    def a_dizionario(self):
        return {"attive": [s.a_dizionario() for s in self.attive], "storico": [s.a_dizionario() for s in self.storico], "prossimo_id": self.prossimo_id,
                "giocate_oggi": {"data": self.giocate_oggi["data"], "ids": list(self.giocate_oggi["ids"])}}

    @classmethod
    def da_dizionario(cls, dati):
        """Il registro dal salvataggio, ValueError col motivo se non va: identificativi unici e sotto il contatore, attive soltanto proposte o accettate."""
        if not isinstance(dati, dict) or set(dati) != {"attive", "storico", "prossimo_id", "giocate_oggi"}:
            raise ValueError("Le sfide salvate hanno i campi sbagliati.")
        registro = cls()
        if not isinstance(dati["prossimo_id"], int) or isinstance(dati["prossimo_id"], bool) or dati["prossimo_id"] < 1:
            raise ValueError("Le sfide: il contatore non è valido.")
        registro.prossimo_id = dati["prossimo_id"]
        if not isinstance(dati["attive"], list) or not isinstance(dati["storico"], list):
            raise ValueError("Le sfide: le attive e lo storico non sono elenchi.")
        registro.attive = [Sfida.da_dizionario(s) for s in dati["attive"]]
        registro.storico = [Sfida.da_dizionario(s) for s in dati["storico"]]
        if any(s.stato not in (PROPOSTA, ACCETTATA) for s in registro.attive) or any(s.stato in (PROPOSTA, ACCETTATA) for s in registro.storico):
            raise ValueError("Le sfide: lo stato di una sfida non è quello del suo elenco.")
        if any(s.stato == ACCETTATA and s.data_gioco is None for s in registro.attive):
            raise ValueError("Le sfide: una sfida accettata non ha il giorno del gioco.")
        ids = [s.id for s in (*registro.attive, *registro.storico)]
        if len(ids) != len(set(ids)) or any(i >= registro.prossimo_id for i in ids):
            raise ValueError("Le sfide: una sfida ha un identificativo ripetuto.")
        oggi = dati["giocate_oggi"]
        if not isinstance(oggi, dict) or set(oggi) != {"data", "ids"} or not (oggi["data"] is None or isinstance(oggi["data"], str)) \
                or not isinstance(oggi["ids"], list):
            raise ValueError("Le sfide: chi ha giocato oggi non è valido.")
        registro.giocate_oggi = {"data": oggi["data"], "ids": list(oggi["ids"])}
        return registro


def descrivi(mondo, g, oggi):
    """Che cosa ha giocato oggi il giocatore fra le sfide, per la regola di un impegno al giorno: una sfida, oppure None."""
    registro = mondo.sfide
    if registro.giocate_oggi["data"] == _giorno(oggi).isoformat() and g.id in registro.giocate_oggi["ids"]:
        return "una sfida"
    return None


def disponibili(mondo, poli):
    """Quante sfide la polisportiva può ancora lanciare: quelle che ha, meno quelle lanciate e non ancora giocate."""
    return poli.sfide_da_lanciare - mondo.sfide.lanciate_in_sospeso(poli.nome)


# Il giorno delle sfide.

def giorno(mondo, data, rapporto):
    """
    Il giorno delle sfide, dopo i tornei, nell'ordine: le proposte senza risposta e le sfide con una
    polisportiva chiusa decadono, si giocano le sfide accettate per oggi, e il computer lancia le sue.
    Restituisce le polisportive che hanno vinto una coppa, perché ricalcolino subito la gloria.
    """
    registro = mondo.sfide
    oggi = _giorno(data)
    if registro.giocate_oggi["data"] != oggi.isoformat():
        registro.giocate_oggi = {"data": oggi.isoformat(), "ids": []}
    memoria = {}
    toccate = set()
    for s in list(registro.attive):
        chiusa = iscrizioni.polisportiva_del_club(mondo, s.sfidante) is None or iscrizioni.polisportiva_del_club(mondo, s.sfidata) is None
        if chiusa or (s.stato == PROPOSTA and oggi >= s.scadenza):
            _decade(mondo, s, rapporto, "una delle due polisportive ha chiuso" if chiusa else "nessuna risposta")
    for s in [s for s in registro.attive if s.stato == ACCETTATA and s.data_gioco <= oggi]:
        toccate |= _gioca(mondo, s, data, rapporto, memoria)
    toccate |= _lanci_del_computer(mondo, data, rapporto, memoria)
    rapporto["sfide_in_attesa"] = sum(1 for s in registro.attive if s.stato == PROPOSTA and tua(mondo.polisportive.get(s.sfidata["nome"])))
    return toccate


def _decade(mondo, s, rapporto, motivo):
    """La sfida decade: non consuma niente; le tue lo sanno dal diario, e le proposte senza risposta si contano."""
    registro = mondo.sfide
    proposta = s.stato == PROPOSTA
    s.stato = DECADUTA
    registro.attive.remove(s)
    tue = [p for lato in LATI if tua(p := iscrizioni.polisportiva_del_club(mondo, s.club(lato)))]
    if not tue:
        return
    registro.archivia(s)
    for poli in tue:
        altra = s.sfidata["nome"] if poli.nome == s.sfidante["nome"] else s.sfidante["nome"]
        mondo.annota(poli, f"La sfida con {altra} è decaduta: {motivo}.")
        if proposta and poli.nome == s.sfidata["nome"]:
            rapporto["sfide_decadute"] += 1


def _squadra_presente(mondo, poli, ids, nome):
    """La squadra di chi non ha una formazione valida, per il tavolino: i convocati che ci sono ancora, anche meno di tre."""
    presenti = tuple(g for gid in ids if (g := mondo.giocatori.get(gid)) is not None and poli is not None and g.appartenenza == poli.nome)
    return Squadra(nome, presenti)


def _gioca(mondo, s, data, rapporto, memoria):
    """
    La sfida accettata, il giorno del gioco: la riconvocazione, il tavolino per chi non ha più una
    squadra valida, il motore vero se c'è una tua polisportiva, l'esito rapido fra quelle del computer;
    la registrazione nella carriera e la posta. Restituisce le polisportive che hanno vinto una coppa.
    """
    registro = mondo.sfide
    oggi = _giorno(data)
    club = {lato: iscrizioni.polisportiva_del_club(mondo, s.club(lato)) for lato in LATI}
    impegnati = impegnati_il(mondo, oggi, esclusa=s)
    squadre = {lato: schiera(mondo, club[lato], s.convocati[lato], oggi, impegnati) for lato in LATI}
    if squadre["sfidante"] is None and squadre["sfidata"] is None:
        _decade(mondo, s, rapporto, "nessuna delle due aveva più una squadra valida")
        return set()
    s.stato = GIOCATA
    s.data_gioco = oggi
    motore = MotorePartita(mondo)
    rapporto["sfide_giocate"] += 1
    tue = any(tua(p) for p in club.values())
    nomi = {lato: club[lato].nome for lato in LATI}
    if squadre["sfidante"] is None or squadre["sfidata"] is None:
        assente = "A" if squadre["sfidante"] is None else "B"
        parti = [Squadra(nomi[lato], tuple(squadre[lato])) if squadre[lato] is not None else _squadra_presente(mondo, club[lato], s.convocati[lato], nomi[lato])
                 for lato in LATI]
        risultato = a_tavolino(parti[0], parti[1], SQUADRE, assente, s.seme)
        motore.registra_squadre(risultato, esperienza.SFIDA, 1.0, diario=True, solo_tuoi=True, gara=GARA)
        motore_usato = None
    else:
        sq_a, sq_b = (Squadra(nomi[lato], tuple(squadre[lato])) for lato in LATI)
        giocatori = (*sq_a.giocatori, *sq_b.giocatori)
        basi = {g.id: infortuni.probabilita_base(g) for g in giocatori}
        cali = {g.id: calo for g in giocatori if (calo := infortuni.calo_acciacco(g, mondo.datetime_corrente_simulazione))} or None
        if tue:
            s.differita = differita_squadre(sq_a, sq_b, basi, cali)
            risultato = Incontro(sq_a, sq_b, SQUADRE, seme=s.seme, dettaglio=ESSENZIALE, basi_infortunio=basi, cali=cali).gioca()
        else:
            risultato = esito_rapido.gioca_squadre(sq_a, sq_b, s.seme, basi_infortunio=basi, cali=cali, memoria=memoria)
        motore.registra_squadre(risultato, esperienza.SFIDA, 1.0, diario=True, solo_tuoi=True, gara=GARA, aggrega="sfide")
        rapporto["infortuni_in_gara"] += len(risultato.infortuni)
        rapporto["acciacchi_in_gara"] += len(risultato.acciacchi)
        motore_usato = "vero" if tue else "rapido"
    s.convocati = {lato: list(ids) for lato, ids in zip(LATI, risultato.parti, strict=True)}
    registro.giocate_oggi["ids"].extend(gid for ids in risultato.parti for gid in ids)
    vince = "sfidante" if risultato.vincitore == "A" else "sfidata"
    s.risultato = {"esito": risultato.esito, "vince": vince, "punti": list(risultato.set[0]),
                   "titolari": [list(ids[:GIOCATORI_AL_TAVOLO]) for ids in risultato.parti], "motore": motore_usato}
    toccate = _posta(mondo, s, club, risultato, data, rapporto)
    registro.attive.remove(s)
    if tue:
        registro.archivia(s)
    return toccate


def _posta(mondo, s, club, risultato, data, rapporto):
    """
    La posta della sfida, D32: la coppa d'oro a chi vince e quella d'argento a chi perde giocando, nei
    contatori e nel palmarès recente, dove l'argento vale una piccola parte dell'oro, decisione 3 di
    Gabriele del 14 ottobre 2026; le sfide vinte e perse, l'ultima sfida di tutte e due, la sfida
    consumata dalla sfidante, un punto di fedeltà a ogni convocato di chi vince; i diari e il riepilogo.
    """
    vince = s.risultato["vince"]
    perde = "sfidata" if vince == "sfidante" else "sfidante"
    tavolino = risultato.esito == TAVOLINO
    vincitrice, perdente = club[vince], club[perde]
    punti_v, punti_p = (s.risultato["punti"][0], s.risultato["punti"][1]) if vince == "sfidante" else (s.risultato["punti"][1], s.risultato["punti"][0])
    vincitrice.coppe_oro += 1
    palmares.aggiungi(vincitrice, data, punti_coppe=palmares.punti_coppa("oro", IMPORTANZA_COPPA_SFIDA))
    toccate = {vincitrice.nome}
    if not tavolino:
        # La coppa d'argento resta nei contatori, ma nella gloria vale soltanto una piccola parte di
        # quella d'oro, decisione 3 di Gabriele del 14 ottobre 2026.
        perdente.coppe_argento += 1
        palmares.aggiungi(perdente, data, punti_coppe=palmares.punti_coppa("oro", IMPORTANZA_COPPA_SFIDA) * QUOTA_GLORIA_ARGENTO_SFIDA)
        toccate.add(perdente.nome)
    vincitrice.sfide_vinte += 1
    perdente.sfide_perse += 1
    for poli in (vincitrice, perdente):
        poli.ultima_sfida = mondo.datetime_corrente_simulazione
    sfidante = club["sfidante"]
    sfidante.sfide_da_lanciare = max(0, sfidante.sfide_da_lanciare - 1)
    for gid in s.convocati[vince]:
        g = mondo.giocatori.get(gid)
        if g is not None and g.appartenenza == vincitrice.nome:
            mondo._aggiungi_fedelta(g, vincitrice, FEDELTA_PER_SFIDA_VINTA, data, rapporto)
    for poli, vinto, lato in ((vincitrice, True, vince), (perdente, False, perde)):
        altra = perdente.nome if vinto else vincitrice.nome
        coppa = "oro" if vinto else ("argento" if not tavolino else None)
        if poli.is_cpu_controlled:
            incrementi = {"sfide": 1, "sfide_vinte": int(vinto)}
            if coppa:
                incrementi[f"coppe_{coppa}"] = 1
            annota_aggregata(poli.diario, data, CAMPI_AGGREGATA_POLISPORTIVA, **incrementi)
            continue
        cognomi = _unisci([mondo.giocatori[gid].cognome for gid in s.risultato["titolari"][LATI.index(lato)] if gid in mondo.giocatori])
        if tavolino:
            testo = f"Vince a tavolino la sfida con {altra}, che non ha schierato una squadra valida: coppa d'oro." if vinto else \
                f"Perde a tavolino la sfida con {altra}: non aveva una squadra valida."
        else:
            mio, suo = (punti_v, punti_p) if vinto else (punti_p, punti_v)
            testo = f"{'Vince' if vinto else 'Perde'} la sfida con {altra}, {mio} a {suo}, con {cognomi}: coppa {COPPE_A_PAROLE[coppa]}."
        mondo.annota(poli, testo, data)
        if vinto:
            rapporto["tue_sfide_vinte"] += 1
            rapporto["notizie"].append(f"{poli.nome} vince la sfida con {altra}" + (" a tavolino." if tavolino else f", {punti_v} a {punti_p}."))
        elif tavolino:
            rapporto["tue_sfide_a_tavolino"] += 1
            rapporto["notizie"].append(f"{poli.nome} perde a tavolino la sfida con {altra}.")
        else:
            rapporto["tue_sfide_perse"] += 1
            rapporto["notizie"].append(f"{poli.nome} perde la sfida con {altra}, {punti_p} a {punti_v}.")
    return toccate


def _lanci_del_computer(mondo, data, rapporto, memoria):
    """
    Le sfide che il computer lancia oggi: ogni sua polisportiva con una sfida da lanciare, col 7 per
    cento, prova fino a tre bersagli a caso; a una polisportiva del computer che accetta si gioca
    subito, a una tua arriva la proposta. Restituisce le polisportive che hanno vinto una coppa.
    """
    oggi = _giorno(data)
    domani = oggi + datetime.timedelta(days=1)
    impegnati = impegnati_il(mondo, oggi)
    convocazioni = {}

    def squadra_di(poli):
        if poli.nome not in convocazioni:
            convocazioni[poli.nome] = convoca(mondo, poli, oggi, impegnati=impegnati)
        return convocazioni[poli.nome]

    toccate = set()
    nomi = list(mondo.polisportive)
    for nome in nomi:
        poli = mondo.polisportive.get(nome)
        if poli is None or not poli.is_cpu_controlled or disponibili(mondo, poli) <= 0 or not caso(PROB_LANCIO_SFIDA_CPU):
            continue
        if in_riposo(mondo, poli, oggi) or squadra_di(poli) is None:
            continue
        propria = squadra_di(poli)
        forza_propria = forza_squadra(propria, memoria)
        basso, alto = forbice(poli.nome)
        altri = [n for n in nomi if n != nome and n in mondo.polisportive]
        for nome_bersaglio in random.sample(altri, min(TENTATIVI_SFIDA_CPU, len(altri))):
            bersaglio = mondo.polisportive[nome_bersaglio]
            if bersaglio.is_cpu_controlled:
                if in_riposo(mondo, bersaglio, oggi):
                    continue
                sua = squadra_di(bersaglio)
            else:
                sua = convoca(mondo, bersaglio, domani)
            if sua is None or not basso <= forza_squadra(sua, memoria) / forza_propria <= alto:
                continue
            if not bersaglio.is_cpu_controlled:
                cpu_domani = convoca(mondo, poli, domani)
                if cpu_domani is not None:
                    _proponi(mondo, poli, bersaglio, cpu_domani, oggi, rapporto)
                    break
                continue
            convocati, _motivo = valuta(mondo, bersaglio, forza_propria, oggi, memoria, impegnati)
            if convocati is None:
                continue
            s = Sfida(mondo.sfide.nuovo_id(), iscrizioni.club_della(poli), iscrizioni.club_della(bersaglio), oggi, oggi, ACCETTATA, oggi,
                      {"sfidante": [g.id for g in propria], "sfidata": [g.id for g in convocati]})
            mondo.sfide.attive.append(s)
            toccate |= _gioca(mondo, s, data, rapporto, memoria)
            break
    return toccate


def ultimo_giorno_per_rispondere(s):
    """
    L'ultimo giorno in cui una proposta aspetta la risposta: quello prima della scadenza, perché
    all'avanzamento che porta il mondo alla scadenza la proposta decade per prima cosa.
    """
    return s.scadenza - datetime.timedelta(days=1)


def _proponi(mondo, cpu, poli, convocati, oggi, rapporto):
    """Una polisportiva del computer sfida una tua: la proposta aspetta la risposta fino all'avanzamento seguente."""
    scadenza = oggi + datetime.timedelta(days=GIORNI_RISPOSTA_SFIDA)
    s = Sfida(mondo.sfide.nuovo_id(), iscrizioni.club_della(cpu), iscrizioni.club_della(poli), oggi, scadenza, PROPOSTA,
              convocati={"sfidante": [g.id for g in convocati], "sfidata": []})
    mondo.sfide.attive.append(s)
    rapporto["sfide_ricevute"] += 1
    ultimo = data_breve(ultimo_giorno_per_rispondere(s))
    # Con la data: in un recupero di più giorni la sfida può essere già decaduta quando si legge il riepilogo.
    rapporto["notizie"].append(f"{cpu.nome} sfida {poli.nome}, il {data_breve(oggi)}: si risponde entro il {ultimo}, prima dell'avanzamento seguente.")
    mondo.annota(poli, f"{cpu.nome} lancia una sfida: si risponde entro il {ultimo}, prima dell'avanzamento seguente, e si gioca all'avanzamento che segue la risposta.")


# Le sfide dell'utente, per i dialoghi del passo 3 e per l'interfaccia testuale.

def _oggi(mondo):
    return _giorno(mondo.datetime_corrente_simulazione)


def giorno_del_gioco(mondo):
    """Il giorno in cui si gioca una sfida lanciata o accettata oggi: quello dell'avanzamento seguente."""
    return _oggi(mondo) + datetime.timedelta(days=1)


def proposta(mondo, poli):
    """La formazione proposta per una tua sfida, per il giorno del gioco: gli identificativi, titolari e riserve, oppure una lista vuota."""
    convocati = convoca(mondo, poli, giorno_del_gioco(mondo))
    return [g.id for g in convocati] if convocati else []


def bersagli(mondo, poli, memoria=None):
    """
    Le polisportive del computer che la tua può sfidare, per il dialogo del lancio: il nome, la forza
    della squadra del giorno del gioco, None se non ne ha una, la gloria e l'ultima sfida, per nome.
    """
    giorno_gioco = giorno_del_gioco(mondo)
    memoria = {} if memoria is None else memoria
    righe = []
    for p in sorted((p for p in mondo.polisportive.values() if p.is_cpu_controlled), key=lambda p: p.nome):
        convocati = convoca(mondo, p, giorno_gioco)
        righe.append({"nome": p.nome, "forza": forza_squadra(convocati, memoria) if convocati else None, "gloria": p.gloria, "ultima_sfida": p.ultima_sfida})
    return righe


def problema_lancio(mondo, poli, nome_bersaglio, ids):
    """Perché la tua polisportiva non può lanciare la sfida con questa formazione, in una frase, oppure None."""
    if not tua(poli):
        return "Le sfide si lanciano da una tua polisportiva."
    if disponibili(mondo, poli) <= 0:
        return f"{poli.nome} non ha sfide da lanciare: il primo del mese ne arrivano due, fino a quattro."
    bersaglio = mondo.polisportive.get(nome_bersaglio)
    if bersaglio is None or not bersaglio.is_cpu_controlled:
        return "Si sfidano soltanto le polisportive del computer."
    if mondo.sfide.rifiutata_oggi(poli.nome, bersaglio.nome, _oggi(mondo)):
        return f"{bersaglio.nome} ha già rifiutato oggi: si può riprovare domani."
    return problema_formazione(mondo, poli, ids, giorno_del_gioco(mondo))


def lancia(mondo, poli, nome_bersaglio, ids):
    """
    La tua polisportiva lancia una sfida con la formazione data, e il computer risponde subito: se
    accetta si gioca all'avanzamento seguente, se rifiuta dice perché, e a quel bersaglio si riprova
    domani. Restituisce la sfida e il messaggio da mostrare; ValueError col motivo se non si può.
    """
    problema = problema_lancio(mondo, poli, nome_bersaglio, ids)
    if problema:
        raise ValueError(problema)
    oggi = _oggi(mondo)
    giorno_gioco = giorno_del_gioco(mondo)
    bersaglio = mondo.polisportive[nome_bersaglio]
    formazione = [mondo.giocatori[gid] for gid in ids]
    convocati, motivo = valuta(mondo, bersaglio, forza_squadra(formazione), giorno_gioco)
    s = Sfida(mondo.sfide.nuovo_id(), iscrizioni.club_della(poli), iscrizioni.club_della(bersaglio), oggi, oggi, convocati={"sfidante": list(ids)})
    if convocati is None:
        s.stato = RIFIUTATA
        mondo.sfide.archivia(s)
        mondo.annota(poli, f"Lancia una sfida a {bersaglio.nome}, che rifiuta: {motivo}")
        return s, f"{bersaglio.nome} rifiuta: {motivo}"
    s.stato = ACCETTATA
    s.data_gioco = giorno_gioco
    s.convocati["sfidata"] = [g.id for g in convocati]
    mondo.sfide.attive.append(s)
    cognomi = _unisci([g.cognome for g in formazione[:GIOCATORI_AL_TAVOLO]])
    mondo.annota(poli, f"Lancia una sfida a {bersaglio.nome}, che accetta: si gioca il {data_breve(giorno_gioco)}, con {cognomi}.")
    return s, f"{bersaglio.nome} accetta: si gioca domani, con {cognomi}."


def in_arrivo(mondo, poli):
    """Le sfide che aspettano la risposta della tua polisportiva, con la forza della squadra di chi sfida."""
    return mondo.sfide.proposte_per(poli.nome)


def problema_risposta(mondo, id_sfida, poli, ids=None):
    """
    Perché la tua polisportiva non può accettare la sfida con questa formazione, in una frase, oppure
    None; senza formazione, soltanto se la sfida aspetta ancora la sua risposta.
    """
    s = mondo.sfide.sfida(id_sfida)
    if s is None or s.stato != PROPOSTA:
        return "Questa sfida non aspetta più una risposta."
    if not tua(poli) or s.sfidata["nome"] != poli.nome:
        return "Questa sfida non è per la tua polisportiva."
    sfidante = iscrizioni.polisportiva_del_club(mondo, s.sfidante)
    if sfidante is None:
        return f"{s.sfidante['nome']} ha chiuso."
    if ids is None:
        return None
    giorno_gioco = giorno_del_gioco(mondo)
    problema = problema_formazione(mondo, poli, ids, giorno_gioco, esclusa=s)
    if problema:
        return problema
    if schiera(mondo, sfidante, s.convocati["sfidante"], giorno_gioco, impegnati_il(mondo, giorno_gioco, esclusa=s)) is None \
            and convoca(mondo, sfidante, giorno_gioco) is None:
        return f"{sfidante.nome} non ha più una squadra valida per il {data_breve(giorno_gioco)}."
    return None


def accetta(mondo, id_sfida, poli, ids):
    """La tua polisportiva accetta la sfida con la formazione data: si gioca all'avanzamento seguente. Restituisce il messaggio; ValueError col motivo."""
    problema = problema_risposta(mondo, id_sfida, poli, ids)
    if problema:
        raise ValueError(problema)
    s = mondo.sfide.sfida(id_sfida)
    giorno_gioco = giorno_del_gioco(mondo)
    sfidante = iscrizioni.polisportiva_del_club(mondo, s.sfidante)
    impegnati = impegnati_il(mondo, giorno_gioco, esclusa=s)
    sua = schiera(mondo, sfidante, s.convocati["sfidante"], giorno_gioco, impegnati) or convoca(mondo, sfidante, giorno_gioco)
    s.stato = ACCETTATA
    s.data_gioco = giorno_gioco
    s.convocati = {"sfidante": [g.id for g in sua], "sfidata": list(ids)}
    cognomi = _unisci([mondo.giocatori[gid].cognome for gid in ids[:GIOCATORI_AL_TAVOLO]])
    mondo.annota(poli, f"Accetta la sfida di {sfidante.nome}: si gioca il {data_breve(giorno_gioco)}, con {cognomi}.")
    return f"Sfida accettata: si gioca domani contro {sfidante.nome}, con {cognomi}."


def rifiuta(mondo, id_sfida, poli):
    """La tua polisportiva rifiuta la sfida: non costa niente a nessuno. Restituisce il messaggio; ValueError col motivo."""
    problema = problema_risposta(mondo, id_sfida, poli)
    if problema:
        raise ValueError(problema)
    s = mondo.sfide.sfida(id_sfida)
    s.stato = RIFIUTATA
    mondo.sfide.attive.remove(s)
    mondo.sfide.archivia(s)
    mondo.annota(poli, f"Rifiuta la sfida di {s.sfidante['nome']}.")
    return f"Sfida di {s.sfidante['nome']} rifiutata."


# La rosa della Coppa delle polisportive, punto 8.8.

def _libero_nei_giorni(impegni, gid, inizio, fine):
    return not any(inizio <= fine_impegno and inizio_impegno <= fine for inizio_impegno, fine_impegno in impegni.get(gid, ()))


def rosa_per_la_coppa(mondo, poli, inizio, fine, impegni):
    """
    La rosa che la polisportiva iscrive alla coppa: i migliori tesserati che possono giocare e non hanno
    altri impegni in quei giorni, per punteggio di classe, con il due più uno, fino a sei. None se non
    convoca una squadra valida.
    """
    morti = mondo._ids_morti_processati_sessione
    candidati = [g for gid in poli.tesserati if (g := mondo.giocatori.get(gid)) is not None and gid not in morti and not g.ritirato and g.puo_giocare
                 and _libero_nei_giorni(impegni, gid, inizio, fine)]
    candidati.sort(key=lambda g: (-classe.punteggio(g), g.id))
    return forma(candidati)


def qualifica_coppa(mondo, calendario, ed, rapporto, quante=None):
    """
    Le polisportive che si qualificano alla coppa, all'apertura delle iscrizioni, risposta 14: per
    gloria, quelle che convocano una squadra valida per i giorni della coppa, fino al tetto, o fino a
    quante se si danno, al sorteggio, per chi prende il posto di una qualificata che ha chiuso. Ognuna
    iscrive la sua rosa; le tue lo sanno dal diario e dal riepilogo.
    """
    impegni = calendario.impegni(mondo)
    gia = set(ed.ids()) | set(ed.esclusi)
    aggiunte = 0
    for poli in sorted(mondo.polisportive.values(), key=lambda p: (-p.gloria, p.nome)):
        if len(ed.iscritti) >= ed.tetto or (quante is not None and aggiunte >= quante):
            break
        if poli.nome in gia:
            continue
        rosa = rosa_per_la_coppa(mondo, poli, ed.data_inizio, ed.data_fine, impegni)
        if rosa is None:
            continue
        ed.aggiungi(poli.nome, iscrizioni.club_della(poli), 0, iscrizioni.QUALIFICATO, rosa=[g.id for g in rosa])
        aggiunte += 1
        for g in rosa:
            impegni.setdefault(g.id, []).append((ed.data_inizio, ed.data_fine))
        if tua(poli):
            rapporto["tue_qualificazioni_coppa"] += 1
            rapporto["notizie"].append(f"{poli.nome} è qualificata {torneo_con_preposizione(ed.nome)}.")
            cognomi = _unisci([g.cognome for g in rosa])
            mondo.annota(poli, f"Qualificata {torneo_con_preposizione(ed.nome)}, dal {data_breve(ed.data_inizio)}, con {cognomi}.")


def rimpiazza_le_chiuse(mondo, calendario, ed, rapporto):
    """Al sorteggio della coppa una qualificata che ha chiuso lascia il posto alla prima esclusa, punto 8.8."""
    chiuse = [iscritto for iscritto in ed.iscritti if iscrizioni.polisportiva_del_club(mondo, iscritto["club"]) is None]
    for iscritto in chiuse:
        ed.togli(iscritto["id"])
        ed.esclusi.append(iscritto["id"])
    if chiuse:
        qualifica_coppa(mondo, calendario, ed, rapporto, quante=len(chiuse))


def problema_rosa(mondo, id_edizione, poli, ids):
    """
    Perché la tua polisportiva non può iscrivere questa rosa alla coppa, in una frase, oppure None: fino
    al sorteggio, da tre a sei tesserati senza doppioni, il due più uno fra i primi tre, e nessuno con
    un altro impegno nei giorni della coppa. L'infortunato si può mettere, a suo rischio.
    """
    calendario = mondo.calendario
    ed = calendario.edizione(id_edizione)
    if ed is None or ed.data_inizio <= _oggi(mondo):
        return "Il sorteggio è già fatto: la rosa non si cambia più."
    if not tua(poli) or ed.iscritto(poli.nome) is None:
        return f"{poli.nome if poli else 'La polisportiva'} non è qualificata {torneo_con_preposizione(ed.nome)}."
    ids = list(ids)
    if not GIOCATORI_AL_TAVOLO <= len(ids) <= CONVOCATI_SFIDA:
        return f"La rosa ha da {GIOCATORI_AL_TAVOLO} a {CONVOCATI_SFIDA} giocatori."
    if len(set(ids)) != len(ids):
        return "Lo stesso giocatore compare due volte nella rosa."
    impegni = calendario.impegni(mondo, esclusa=ed)
    for gid in ids:
        g = mondo.giocatori.get(gid)
        if g is None or gid not in poli.tesserati:
            return f"Il giocatore {gid} non è un tesserato di {poli.nome}."
        if g.ritirato:
            return f"{nome_completo(g)} si è {'ritirato' if g.sesso == 'm' else 'ritirata'} dall'attività."
        if not _libero_nei_giorni(impegni, gid, ed.data_inizio, ed.data_fine):
            return f"{nome_completo(g)} nei giorni della coppa ha già un altro impegno."
    if not composizione_valida([mondo.giocatori[gid] for gid in ids[:GIOCATORI_AL_TAVOLO]]):
        return "Fra i primi tre servono due giocatori di un sesso e uno dell'altro."
    return None


def cambia_rosa(mondo, id_edizione, poli, ids):
    """La tua polisportiva cambia la rosa della coppa, nell'ordine della formazione; ValueError col motivo."""
    problema = problema_rosa(mondo, id_edizione, poli, ids)
    if problema:
        raise ValueError(problema)
    ed = mondo.calendario.edizione(id_edizione)
    ed.iscritto(poli.nome)["rosa"] = list(ids)
    mondo.annota(poli, f"Cambia la rosa {torneo_con_preposizione(ed.nome, 'per')}: {_unisci([mondo.giocatori[gid].cognome for gid in ids])}.")


def schiera_coppa(mondo, poli, rosa, tua_polisportiva=None):
    """
    La squadra di un incontro della coppa: i tre migliori sani della rosa iscritta, nell'ordine della
    formazione per le tue e per punteggio di classe per il computer, con il due più uno; gli altri della
    rosa ancora tesserati sono le riserve. None se non c'è più una squadra valida.
    """
    if tua_polisportiva is None:
        tua_polisportiva = tua(poli)
    morti = mondo._ids_morti_processati_sessione
    presenti = [g for gid in rosa if (g := mondo.giocatori.get(gid)) is not None and gid not in morti and not g.ritirato and g.puo_giocare
                and g.appartenenza == poli.nome]
    if not tua_polisportiva:
        presenti.sort(key=lambda g: (-classe.punteggio(g), g.id))
    return forma(presenti)
