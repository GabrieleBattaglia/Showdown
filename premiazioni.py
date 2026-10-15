"""
Le premiazioni dei tornei di MESS: la chiusura di una sede, con medaglie, premi, esperienza, fedeltà, punti, albo e diari.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-14 con la tappa 12, decisione D32, risposte 9, 12 e 13 di Gabriele e punti 5.6, 5.9,
5.10 e 5.11 del progetto. Quando una sede finisce, chiudi porta nel mondo quello che ha deciso:
le medaglie ai primi quattro, oro, argento, bronzo e legno, del giocatore per sempre e del club con
cui si era iscritto, se esiste ancora, cioè con lo stesso nome e lo stesso giorno di fondazione, sia
per sempre sia nel palmarès recente della gloria; per i liberi e per i club chiusi la medaglia è
soltanto del giocatore. I premi vanno al club dell'iscrizione, nella voce premi dei conti; quelli dei
liberi e dei club chiusi restano alla federazione, risposta 12. L'esperienza delle fasi superate e
quella del piazzamento a scalare per i primi dodici, per l'importanza, a tutti i partecipanti,
risposta 9; nessun punto allenamento per il piazzamento. La fedeltà per le medaglie vinte col club,
a chi ne è ancora tesserato. I punti della classifica mondiale, i tornei giocati e i titoli dei podi
più importanti. I diari: i tuoi tesserati e le tue polisportive hanno una voce col riassunto del
torneo, tutti gli altri la voce aggregata dell'anno, e i podi più importanti anche una voce a sé.
L'albo d'oro conserva tutto, per sempre, risposta 13: una voce corta per sede, con i nomi una volta
sola nelle sue tabelle.
Dalla decisione 9 di Gabriele del 14 ottobre 2026 la Coppa delle polisportive fa come i tornei: dà alla
rosa iscritta la fedeltà della coppa vinta, come una medaglia, e l'esperienza delle fasi superate e del
piazzamento.
"""

import datetime

import esperienza
import iscrizioni
import modelli_torneo
import palmares
from costanti import FEDELTA_PER_MEDAGLIA, IMPORTANZA_TITOLO
from economia import scritta_in_euro
from modelli import CAMPI_AGGREGATA_GIOCATORE, CAMPI_AGGREGATA_POLISPORTIVA, annota_aggregata
from utilita import accorda

MEDAGLIE = palmares.MEDAGLIE
CAMPI_DELLE_MEDAGLIE = {"oro": "ori", "argento": "argenti", "bronzo": "bronzi", "legno": "legni"}
CAMPI_DELLE_COPPE = {"oro": "coppe_oro", "argento": "coppe_argento", "bronzo": "coppe_bronzo", "legno": "coppe_legno"}
COPPE_A_PAROLE = {"oro": "d'oro", "argento": "d'argento", "bronzo": "di bronzo", "legno": "di legno"}
ORDINALI = ("primo", "secondo", "terzo", "quarto", "quinto", "sesto", "settimo", "ottavo", "nono", "decimo", "undicesimo", "dodicesimo")


def posto_a_parole(posto, sesso="m"):
    """Il posto in classifica a parole: primo, quinta; oltre il dodicesimo, il numero."""
    if posto <= len(ORDINALI):
        return accorda(sesso, ORDINALI[posto - 1])
    return f"{posto}°"


def _giorno(data):
    return data.date() if isinstance(data, datetime.datetime) else data


def incontri_di(torneo, gid):
    """Gli incontri giocati davvero dal giocatore nella sede, e quanti ne ha vinti: i riposi e i tavolini non contano."""
    giocati = vinti = 0
    for incontro in torneo.incontri():
        if gid not in (incontro.a, incontro.b) or incontro.esito not in ("regolare", "ritiro"):
            continue
        giocati += 1
        vinti += torneo.vincitore(incontro) == gid
    return giocati, vinti


def chiudi(mondo, calendario, torneo, data, rapporto):
    """
    La chiusura di una sede di torneo individuale: tutto quello che la sede ha deciso entra nel mondo.
    Restituisce le polisportive che hanno vinto qualcosa, perché ricalcolino subito la gloria. La
    coppa a squadre la chiude chiudi_squadre.
    """
    if torneo.squadre:
        return chiudi_squadre(mondo, calendario, torneo, data, rapporto)
    modello = torneo.modello
    importanza = modello["importanza"]
    nome = modello["nome"]
    mondiale = modello["qualificazione"] == modelli_torneo.PUNTI_ANNO
    classifica = torneo.classifica_finale
    fasi = torneo.fasi_superate()
    oggi = _giorno(data)
    toccate = set()
    rapporto["tornei_conclusi"] += 1
    rapporto["mondiali_conclusi"] += mondiale
    rapporto["premi_tornei"] += sum(torneo.premi.values())
    per_club = {}
    tuoi = []
    for posto, gid in enumerate(classifica, start=1):
        g = mondo.giocatori.get(gid)
        info = torneo.info[gid]
        poli = iscrizioni.polisportiva_del_club(mondo, info.get("club"))
        medaglia = MEDAGLIE[posto - 1] if posto <= len(MEDAGLIE) else None
        premio = torneo.premi.get(gid, 0)
        if poli is not None:
            conto = per_club.setdefault(poli.nome, {"poli": poli, "iscritti": 0, "medaglie": dict.fromkeys(MEDAGLIE, 0), "premi": 0, "righe": []})
            conto["iscritti"] += 1
        if medaglia and poli is not None:
            setattr(poli, CAMPI_DELLE_MEDAGLIE[medaglia], getattr(poli, CAMPI_DELLE_MEDAGLIE[medaglia]) + 1)
            palmares.aggiungi(poli, data, punti_medaglie=palmares.punti_medaglia(medaglia, importanza))
            per_club[poli.nome]["medaglie"][medaglia] += 1
            toccate.add(poli.nome)
        if premio and poli is not None:
            poli.cassa += premio
            poli.conti_del_mese["premi"] += premio
            per_club[poli.nome]["premi"] += premio
        if g is None:
            continue
        g.tornei_giocati += 1
        if medaglia:
            setattr(g, CAMPI_DELLE_MEDAGLIE[medaglia], getattr(g, CAMPI_DELLE_MEDAGLIE[medaglia]) + 1)
            if poli is not None and g.appartenenza == poli.nome:
                mondo._aggiungi_fedelta(g, poli, FEDELTA_PER_MEDAGLIA[medaglia], data, rapporto)
            if importanza >= IMPORTANZA_TITOLO:
                g.titoli.append({"data": oggi.isoformat(), "torneo": nome, "posto": posto, "mondiale": mondiale})
        if not g.ritirato:
            esperienza.da_fasi(g, fasi.get(gid, 0), importanza)
            esperienza.da_piazzamento(g, posto, importanza)
        palmares.aggiungi_punti(g, oggi, palmares.punti_classifica(posto, importanza))
        palmares.sfoltisci_punti(g, oggi)
        giocati, vinti = incontri_di(torneo, gid)
        if iscrizioni.tuo(mondo, g):
            tuoi.append(g)
            _voce_del_tuo(mondo, g, torneo, posto, len(classifica), giocati, vinti, medaglia, premio, poli, rapporto, mondiale)
            if poli is not None:
                per_club[poli.nome]["righe"].append(f"{g.nome} {g.cognome} {posto_a_parole(posto, g.sesso)}")
        else:
            incrementi = {"tornei": 1, "incontri": giocati, "vinti": vinti}
            if medaglia:
                incrementi[CAMPI_DELLE_MEDAGLIE[medaglia]] = 1
            annota_aggregata(g.diario, data, CAMPI_AGGREGATA_GIOCATORE, **incrementi)
            if medaglia and importanza >= IMPORTANZA_TITOLO:
                mondo.annota(g, f"{_medaglia_a_parole(medaglia).capitalize()} a {nome}, sede {torneo.sede}.", data)
    for conto in per_club.values():
        _voce_del_club(mondo, conto, torneo, data, importanza)
    if tuoi:
        rapporto["tuoi_tornei_conclusi"] += 1
        calendario.conserva_differite(torneo, {g.id for g in tuoi})
    calendario.albo.registra(mondo, torneo, calendario.numero_di(torneo))
    return toccate


def chiudi_squadre(mondo, calendario, torneo, data, rapporto):
    """
    La chiusura della Coppa delle polisportive, punto 8.8: le coppe ai primi quattro, oro, argento,
    bronzo e legno, con l'importanza del modello, nei contatori per sempre e nel palmarès recente della
    gloria, a chi esiste ancora; nessun premio in euro. Dalla decisione 9 di Gabriele del 14 ottobre
    2026 la coppa dà anche alla rosa iscritta quello che un torneo individuale dà ai suoi giocatori: vedi
    _alla_rosa. Le tue polisportive hanno la voce col riassunto, e i giocatori della loro rosa ancora
    tesserati una voce loro; quelle del computer la voce aggregata dell'anno, e i podi una voce a sé.
    Restituisce le polisportive che hanno vinto una coppa.
    """
    modello = torneo.modello
    importanza = modello["importanza"]
    nome = modello["nome"]
    classifica = torneo.classifica_finale
    fasi = torneo.fasi_superate()
    toccate = set()
    tue = set()
    rapporto["tornei_conclusi"] += 1
    for posto, cid in enumerate(classifica, start=1):
        info = torneo.info[cid]
        poli = iscrizioni.polisportiva_del_club(mondo, info.get("club"))
        coppa = MEDAGLIE[posto - 1] if posto <= len(MEDAGLIE) else None
        _alla_rosa(mondo, info.get("rosa", ()), poli, posto, coppa, fasi.get(cid, 0), importanza, data, rapporto)
        if poli is None:
            continue
        if coppa:
            campo = CAMPI_DELLE_COPPE[coppa]
            setattr(poli, campo, getattr(poli, campo) + 1)
            palmares.aggiungi(poli, data, punti_coppe=palmares.punti_coppa(coppa, importanza))
            toccate.add(poli.nome)
        giocati, vinti = incontri_di(torneo, cid)
        if poli.is_cpu_controlled:
            incrementi = {"tornei": 1}
            if coppa:
                incrementi[CAMPI_DELLE_COPPE[coppa]] = 1
            annota_aggregata(poli.diario, data, CAMPI_AGGREGATA_POLISPORTIVA, **incrementi)
            if coppa and importanza >= IMPORTANZA_TITOLO:
                mondo.annota(poli, f"Coppa {COPPE_A_PAROLE[coppa]} a {nome}.", data)
            continue
        tue.add(cid)
        testo = f"Chiude {nome}, sede {torneo.sede}, {posto_a_parole(posto, 'f')} su {len(classifica)}: {vinti} incontri vinti su {giocati}"
        if coppa:
            testo += f", coppa {COPPE_A_PAROLE[coppa]}"
            rapporto[f"tue_coppe_{coppa}"] += 1
            rapporto["notizie"].append(f"{poli.nome} vince la coppa {COPPE_A_PAROLE[coppa]} a {nome}.")
        mondo.annota(poli, testo + ".", data)
        for gid in info.get("rosa", ()):
            g = mondo.giocatori.get(gid)
            if g is not None and g.appartenenza == poli.nome:
                mondo.annota(g, f"Chiude {nome} con {poli.nome}, {posto_a_parole(posto, 'f')} su {len(classifica)}"
                             + (f": coppa {COPPE_A_PAROLE[coppa]}." if coppa else "."), data)
    if tue:
        rapporto["tuoi_tornei_conclusi"] += 1
        calendario.conserva_differite(torneo, tue)
    calendario.albo.registra(mondo, torneo, calendario.numero_di(torneo))
    return toccate


def _alla_rosa(mondo, rosa, poli, posto, coppa, fasi, importanza, data, rapporto):
    """
    Quello che la Coppa delle polisportive dà alla rosa iscritta, decisione 9 di Gabriele del 14 ottobre
    2026, come un torneo individuale ai suoi giocatori. A chi è ancora tesserato col club la fedeltà della
    coppa vinta, come per una medaglia: 4 per l'oro, 3 per l'argento, 2 per il bronzo, 1 per il legno. A
    tutti, anche a chi ha cambiato club o a chi ha giocato soltanto da riserva, l'esperienza delle fasi
    superate dal club e del suo piazzamento, per l'importanza della coppa; ai ritirati no, come nei tornei.
    Prima la rosa prendeva soltanto i punti e l'esperienza degli incontri.
    """
    for gid in rosa:
        g = mondo.giocatori.get(gid)
        if g is None:
            continue
        if coppa and poli is not None and g.appartenenza == poli.nome:
            mondo._aggiungi_fedelta(g, poli, FEDELTA_PER_MEDAGLIA[coppa], data, rapporto)
        if not g.ritirato:
            esperienza.da_fasi(g, fasi, importanza)
            esperienza.da_piazzamento(g, posto, importanza)


def _medaglia_a_parole(medaglia):
    return {"oro": "medaglia d'oro", "argento": "medaglia d'argento", "bronzo": "medaglia di bronzo", "legno": "medaglia di legno"}[medaglia]


def _voce_del_tuo(mondo, g, torneo, posto, iscritti, giocati, vinti, medaglia, premio, poli, rapporto, mondiale):
    """La voce del diario del tuo tesserato col riassunto del torneo, le notizie e i contatori del riepilogo."""
    nome = torneo.modello["nome"]
    testo = f"Chiude {nome}, sede {torneo.sede}, {posto_a_parole(posto, g.sesso)} su {iscritti}: {vinti} incontri vinti su {giocati}"
    if medaglia:
        testo += f", {_medaglia_a_parole(medaglia)}"
        rapporto[f"tue_medaglie_{medaglia}"] += 1
        notizia = f"{g.nome} {g.cognome} vince la {_medaglia_a_parole(medaglia)} a {nome}"
        if mondiale and medaglia == "oro":
            rapporto["tuoi_titoli_mondiali"] += 1
            notizia = f"{g.nome} {g.cognome} è {'campione' if g.sesso == 'm' else 'campionessa'} del mondo"
        rapporto["notizie"].append(notizia + ".")
    if premio and poli is not None:
        testo += f"; premio di {scritta_in_euro(premio)} a {poli.nome}"
        rapporto["tuoi_premi"] += premio
    mondo.annota(g, testo + ".")


def _voce_del_club(mondo, conto, torneo, data, importanza):
    """La voce del club: per le tue polisportive il riassunto del torneo, per quelle del computer la voce aggregata dell'anno e i podi importanti a sé."""
    poli = conto["poli"]
    nome = torneo.modello["nome"]
    medaglie = conto["medaglie"]
    if not poli.is_cpu_controlled:
        testo = f"Chiude {nome}, sede {torneo.sede}"
        if conto["righe"]:
            testo += ": " + ", ".join(conto["righe"])
        if conto["premi"]:
            testo += f"; premi per {scritta_in_euro(conto['premi'])}"
        mondo.annota(poli, testo + ".", data)
        return
    incrementi = {"iscrizioni": conto["iscritti"], "tornei": 1, "premi": conto["premi"]}
    for medaglia, quante in medaglie.items():
        if quante:
            incrementi[CAMPI_DELLE_MEDAGLIE[medaglia]] = quante
    annota_aggregata(poli.diario, data, CAMPI_AGGREGATA_POLISPORTIVA, **incrementi)
    if importanza >= IMPORTANZA_TITOLO and any(medaglie.values()):
        vinte = ", ".join(f"{quante} {CAMPI_DELLE_MEDAGLIE[m] if quante > 1 else m}" for m, quante in medaglie.items() if quante)
        mondo.annota(poli, f"Medaglie a {nome}: {vinte}.", data)


class Albo:
    """
    L'albo d'oro, che conserva tutto per sempre, risposta 13 di Gabriele, punto 5.10 del progetto. Una
    voce corta per ogni sede conclusa, una lista: modello, tipo, sesso, importanza, data, numero
    dell'edizione, sede, iscritti, il podio e i premi; per i singolari ogni posto del podio è il
    giocatore col suo club, per la coppa il club. I nomi stanno una volta sola in tre tabelle, scritte
    alla chiusura e mai sfoltite: i modelli col nome che avevano, i giocatori con nome e cognome, i club
    col nome e il giorno di fondazione. Così un podio si legge anche dopo l'uscita del giocatore e la
    chiusura del club. Un'edizione del mondiale che non si disputa ha la sua voce, con la sede zero.
    Il modello di una voce, dalla revisione del 14 ottobre 2026, è il posto nella tabella delle coppie
    di identificativo e nome, come i club: prima era l'identificativo, con un nome solo per modello
    riscritto a ogni chiusura, e una rinomina cambiava il nome a tutte le edizioni passate.
    """

    def __init__(self):
        self.voci = []
        self.modelli = []
        self._indice_modello = {}
        self.giocatori = {}
        self.club = []
        self._indice_club = {}

    def indice_del_modello(self, id_modello, nome):
        """Il posto della coppia di identificativo e nome nella tabella dei modelli, che si allunga a ogni nome nuovo."""
        chiave = (id_modello, nome)
        if chiave not in self._indice_modello:
            self._indice_modello[chiave] = len(self.modelli)
            self.modelli.append([id_modello, nome])
        return self._indice_modello[chiave]

    def nome_del_modello(self, indice):
        """Il nome che il modello della voce aveva quando la voce è nata."""
        return self.modelli[indice][1]

    def id_del_modello(self, indice):
        return self.modelli[indice][0]

    def indice_del_club(self, club):
        if club is None:
            return None
        chiave = (club["nome"], club["fondazione"])
        if chiave not in self._indice_club:
            self._indice_club[chiave] = len(self.club)
            self.club.append([club["nome"], club["fondazione"]])
        return self._indice_club[chiave]

    def registra(self, mondo, torneo, numero):
        """La voce della sede conclusa, con i nomi nelle tabelle."""
        modello = torneo.modello
        indice = self.indice_del_modello(modello["id"], modello["nome"])
        podio = []
        for gid in torneo.classifica_finale[:4]:
            info = torneo.info[gid]
            if modello["tipo"] == modelli_torneo.SQUADRE:
                podio.append(self.indice_del_club(info.get("club")))
                continue
            nome, _spazio, cognome = info["nome"].partition(" ")
            g = mondo.giocatori.get(gid)
            if g is not None:
                nome, cognome = g.nome, g.cognome
            self.giocatori[str(gid)] = [nome, cognome]
            podio.append([gid, self.indice_del_club(info.get("club"))])
        premi = [torneo.premi.get(gid, 0) for gid in torneo.classifica_finale[:4]]
        self.voci.append([indice, modello["tipo"], modello["sesso"], modello["importanza"], torneo.data_inizio, numero, torneo.sede,
                          len(torneo.iscritti), podio, premi])

    def non_disputato(self, ed, numero):
        """La voce di un'edizione che non si disputa, per pochi iscritti: sede zero, nessun podio."""
        indice = self.indice_del_modello(ed.modello_id, ed.nome)
        self.voci.append([indice, ed.modello["tipo"], ed.modello["sesso"], ed.modello["importanza"], ed.data_inizio.isoformat(), numero, 0,
                          len(ed.iscritti), [], []])

    def a_dizionario(self):
        return {"voci": [list(v) for v in self.voci], "modelli": [list(m) for m in self.modelli], "giocatori": {k: list(v) for k, v in self.giocatori.items()},
                "club": [list(c) for c in self.club]}

    @classmethod
    def da_dizionario(cls, dati):
        """L'albo dal salvataggio, ValueError se non va: ogni nome delle voci deve stare nelle tabelle."""
        if not isinstance(dati, dict) or set(dati) != {"voci", "modelli", "giocatori", "club"}:
            raise ValueError("L'albo d'oro non è valido.")
        albo = cls()
        if not isinstance(dati["club"], list) or not all(isinstance(c, list) and len(c) == 2 and all(isinstance(x, str) for x in c) for c in dati["club"]):
            raise ValueError("L'albo d'oro: la tabella dei club non è valida.")
        albo.club = [list(c) for c in dati["club"]]
        albo._indice_club = {(c[0], c[1]): n for n, c in enumerate(albo.club)}
        if (not isinstance(dati["modelli"], list) or not all(isinstance(m, list) and len(m) == 2 and all(isinstance(x, str) for x in m) for m in dati["modelli"])
                or not isinstance(dati["giocatori"], dict)):
            raise ValueError("L'albo d'oro: le tabelle dei nomi non sono valide.")
        albo.modelli = [list(m) for m in dati["modelli"]]
        albo._indice_modello = {(m[0], m[1]): n for n, m in enumerate(albo.modelli)}
        albo.giocatori = {k: list(v) for k, v in dati["giocatori"].items()}
        if not isinstance(dati["voci"], list):
            raise ValueError("L'albo d'oro: le voci non sono un elenco.")
        for voce in dati["voci"]:
            if (not isinstance(voce, list) or len(voce) != 10 or not isinstance(voce[0], int) or isinstance(voce[0], bool)
                    or not 0 <= voce[0] < len(albo.modelli) or not isinstance(voce[8], list)):
                raise ValueError(f"L'albo d'oro: una voce non è valida: {voce!r}")
            for posto in voce[8]:
                club = posto if voce[1] == modelli_torneo.SQUADRE else posto[1]
                if voce[1] != modelli_torneo.SQUADRE and str(posto[0]) not in albo.giocatori:
                    raise ValueError(f"L'albo d'oro: il giocatore {posto[0]} non è nella sua tabella.")
                if club is not None and not 0 <= club < len(albo.club):
                    raise ValueError("L'albo d'oro: un club non è nella sua tabella.")
        albo.voci = [list(v) for v in dati["voci"]]
        return albo
