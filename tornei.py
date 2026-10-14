"""
Il motore dei tornei di MESS: una sede di torneo dal sorteggio alla classifica finale, senza mondo e senza wx.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-13 con la tappa 12, decisioni D9, D13 e D32 e punto 4 del progetto: è lo scheletro
di TournamentEngine di tournament_engine.py di Terminal Beast, riscritto perché un torneo duri giorni
simulati e si salvi. Lavora soltanto con identificativi, un intero per il giocatore e il nome per la
polisportiva nella coppa, e con le informazioni che riceve; non gioca le partite, che riceve da una
funzione, e non scrive nel mondo.
Le regole, punto per punto del progetto: le sedi parallele equilibrate a serpentina, risposta 1 di
Gabriele; la struttura adattata agli iscritti veri, in formule.py; le teste di serie dalla forza al
sorteggio, cioè dal punteggio di classe di oggi; i gironi a serpentina con i compagni di club separati
quando si può; le giornate col metodo del cerchio; la classifica del girone senza pareggi, con gli
spareggi dell'articolo 8 del Regolamento Eventi Federali della FISPIC del 23 giugno 2026, perché il
regolamento tecnico 2025-2028, la traduzione FISPIC delle regole IBSA, non ne parla; il
tabellone classico, dove le teste di serie si incontrano il più tardi possibile e i riposi toccano
alle prime teste, senza contare come vittorie; i compagni di girone separati al primo turno quando si
può; la finalina fra i due sconfitti delle semifinali, nello stesso turno della finale; la classifica
finale con lo sconfitto della finale sempre secondo; i premi di calculate_prizes_static, senza la
trattenuta dell'organizzatore, che qui è la federazione; il gioco a giornate, fino a tanti turni al
giorno quanti ne dice il modello, con ogni fase in un giorno nuovo.
Sono corretti i difetti di Terminal Beast dell'appendice A del progetto: la finalina che faceva
rientrare i semifinalisti sconfitti, lo sconfitto della finale che poteva risultare primo, il riposo
che valeva una vittoria, il primo contro l'ultimo a ogni fase, i gironi senza teste di serie e senza
giornate, la classifica di girone senza scontro diretto, le teste di serie del tabellone soltanto alla
prima fase, il torneo che non si salvava, la percentuale al primo sbagliata sopra i dieci posti, la
trattenuta col tetto di 1.500, le ricerche degli iscritti che confrontavano dizionari interi.
"""

import copy
import dataclasses
import datetime
import math
import random

import formule
import modelli_torneo

IN_CORSO = "in_corso"
CONCLUSO = "concluso"
ANNULLATO = "annullato"
STATI = (IN_CORSO, CONCLUSO, ANNULLATO)
REGOLARE = "regolare"
RITIRO = "ritiro"
TAVOLINO = "tavolino"
TAVOLINO_DOPPIO = "tavolino_doppio"
RIPOSO = "riposo"
ESITI = (REGOLARE, RITIRO, TAVOLINO, TAVOLINO_DOPPIO, RIPOSO)
# Gli esiti che arrivano dalla funzione che gioca: il riposo il torneo lo chiude da solo.
ESITI_GIOCATI = (REGOLARE, RITIRO, TAVOLINO, TAVOLINO_DOPPIO)
MOTORI = ("vero", "rapido")
TABELLONE = "T"
# La gara a squadre si gioca in un set solo.
SET_SQUADRE = 1
# Sopra i dieci posti premiati la pendenza si smorza verso questa, come in calculate_prizes_static.
PENDENZA_SMORZATA = 1.1
POSTI_SENZA_SMORZATURA = 10


def lettera_girone(indice):
    """La lettera del girone numero indice, contando da zero: A, B e così via fino a Z, poi AA, AB, come _get_group_letter di Terminal Beast."""
    lettere = ""
    while indice >= 0:
        lettere = chr(ord("A") + indice % 26) + lettere
        indice = indice // 26 - 1
    return lettere


# Le sedi, punto 4.3.

def dividi_in_sedi(ids_per_forza, tetto, minimo):
    """
    Gli iscritti di un'edizione divisi in sedi parallele: sotto il minimo nessuna sede, e l'edizione
    si annulla; altrimenti tante sedi quante ne servono perché nessuna superi il tetto, e gli iscritti,
    dal più forte, a serpentina, prima la sede 1, poi la 2 e così via e poi indietro: ogni sede ha la
    stessa forza e il suo favorito. ids_per_forza è già in ordine di forza.
    """
    n = len(ids_per_forza)
    if n < minimo or n == 0:
        return []
    quante = -(-n // tetto)
    sedi = [[] for _ in range(quante)]
    for posto, gid in enumerate(ids_per_forza):
        riga, colonna = divmod(posto, quante)
        sedi[colonna if riga % 2 == 0 else quante - 1 - colonna].append(gid)
    return sedi


# I gironi, punti 4.6 e 4.7.

def gironi_a_serpentina(ids, quanti, club_di):
    """
    I gironi a serpentina: gli iscritti, in ordine di testa di serie, stanno in urne da tanti quanti
    sono i gironi; l'urna pari va dal primo girone all'ultimo, la dispari al contrario. Dopo la prima
    urna, chi trova nel suo girone un compagno di club prova uno scambio con un altro della stessa
    urna che tolga il conflitto senza crearne un altro; se non c'è, resta dov'è: i compagni si
    separano quando si può. club_di dà la chiave del club di un iscritto, None per i liberi.
    Restituisce l'elenco dei gironi, ciascuno con gli iscritti in ordine di testa di serie.
    """
    gironi = [[] for _ in range(quanti)]
    for riga, inizio in enumerate(range(0, len(ids), quanti)):
        urna = ids[inizio:inizio + quanti]
        ordine = list(range(quanti)) if riga % 2 == 0 else list(range(quanti - 1, -1, -1))
        posti = dict(zip(urna, ordine, strict=False))
        if riga > 0:
            _separa_i_compagni(urna, posti, gironi, club_di)
        for gid in urna:
            gironi[posti[gid]].append(gid)
    return gironi


def _compagno_nel_girone(gid, girone, club_di, escluso=None):
    club = club_di(gid)
    return club is not None and any(altro != escluso and club_di(altro) == club for altro in girone)


def _separa_i_compagni(urna, posti, gironi, club_di):
    """Gli scambi dentro un'urna che tolgono un compagno di club dal girone, senza crearne un altro."""
    for gid in urna:
        if not _compagno_nel_girone(gid, gironi[posti[gid]], club_di):
            continue
        for altro in urna:
            if altro == gid:
                continue
            mio, suo = posti[gid], posti[altro]
            if _compagno_nel_girone(gid, gironi[suo], club_di) or _compagno_nel_girone(altro, gironi[mio], club_di):
                continue
            posti[gid], posti[altro] = suo, mio
            break


def calendario_del_girone(ids):
    """
    Le giornate di un girone col metodo del cerchio: con un numero dispari si aggiunge il riposo; il
    primo resta fermo, gli altri ruotano di un posto a ogni turno, e il turno accoppia il posto i col
    posto n meno 1 meno i. Con gli iscritti in ordine di testa di serie le prime due teste si incontrano
    all'ultimo turno. Restituisce un turno per elenco, con le coppie; chi riposa ha None come avversario.
    """
    posti = list(ids) + ([None] if len(ids) % 2 else [])
    n = len(posti)
    turni = []
    for _ in range(n - 1):
        coppie = []
        for i in range(n // 2):
            a, b = posti[i], posti[n - 1 - i]
            if a is None:
                a, b = b, a
            coppie.append((a, b))
        turni.append(coppie)
        posti = [posti[0], posti[-1], *posti[1:-1]]
    return turni


# Il tabellone, punto 4.9.

def ordine_tabellone(grandezza):
    """Le teste di serie nei posti del tabellone classico: 1 e 2 in metà opposte, le prime quattro in quarti diversi; per 8, 1, 8, 4, 5, 2, 7, 3, 6."""
    ordine = [1]
    while len(ordine) < grandezza:
        doppio = 2 * len(ordine) + 1
        ordine = [x for testa in ordine for x in (testa, doppio - testa)]
    return ordine


# I premi, punto 4.12.

def montepremi(modello, paganti):
    """Il montepremi di una sede: il più alto fra il minimo garantito e le quote dei paganti con il contributo della federazione, che con 1 lo raddoppia."""
    dalle_quote = int(modello["quota_iscrizione"] * paganti * (1.0 + modello["contributo_federazione"]))
    return max(modello["montepremi_minimo"], dalle_quote)


def pendenza_smorzata(pendenza, posti):
    """La pendenza vera dei premi: sopra i dieci posti si smorza verso 1,1, come in calculate_prizes_static di Terminal Beast."""
    if posti > POSTI_SENZA_SMORZATURA and pendenza > PENDENZA_SMORZATA:
        return PENDENZA_SMORZATA + (pendenza - PENDENZA_SMORZATA) * (POSTI_SENZA_SMORZATURA / posti)
    return pendenza


def _pesi_dei_premi(pendenza, posti):
    vera = pendenza_smorzata(pendenza, posti)
    return [math.pow(vera, posti - i - 1) for i in range(posti)]


def calcola_premi(montepremi_della_sede, posti, pendenza, iscritti=None):
    """
    I premi, dal primo in giù: tanti posti quanti premiati, non più degli iscritti, con i pesi della
    pendenza, smorzata sopra i dieci posti; ogni premio è intero, per troncamento, e la somma non
    supera mai il montepremi. Restituisce soltanto i premi maggiori di zero.
    """
    posti = min(posti, iscritti) if iscritti is not None else posti
    if montepremi_della_sede <= 0 or posti <= 0:
        return []
    pesi = _pesi_dei_premi(pendenza, posti)
    totale = sum(pesi)
    premi = [int(peso / totale * montepremi_della_sede) for peso in pesi]
    return [premio for premio in premi if premio > 0]


def prima_percentuale(pendenza, posti):
    """La percentuale del montepremi che va al primo, con la pendenza vera: in Terminal Beast sopra i dieci posti non era quella giusta."""
    if posti <= 1:
        return 100.0
    pesi = _pesi_dei_premi(pendenza, posti)
    return 100.0 * pesi[0] / sum(pesi)


def pendenza_per_prima(percentuale, posti):
    """La pendenza che dà al primo la percentuale indicata, cercata per bisezione fra 1 e il massimo, arrotondata al millesimo."""
    if posti <= 1 or percentuale <= 100.0 / posti:
        return 1.0
    basso, alto = 1.0, modelli_torneo.PENDENZA_MASSIMA
    for _ in range(60):
        mezzo = (basso + alto) / 2.0
        if prima_percentuale(mezzo, posti) < percentuale:
            basso = mezzo
        else:
            alto = mezzo
    return round((basso + alto) / 2.0, 3)


# Le strutture salvabili, punto 4.2.

def _intero(valore):
    return isinstance(valore, int) and not isinstance(valore, bool)


def _id_valido(valore):
    return _intero(valore) or (isinstance(valore, str) and bool(valore))


def _controlla(condizione, motivo):
    if not condizione:
        raise ValueError(motivo)


@dataclasses.dataclass
class IncontroDelTorneo:
    """
    Un incontro di una sede: a e b sono gli iscritti, b None per il riposo; esito None finché non
    si gioca; vince A, B o None per il tavolino doppio; set sono le coppie di punteggi, con quelli
    aggiunti dal ritiro, e set_giocati quelli giocati davvero; differita i dati per riascoltarlo,
    per gli incontri dei tesserati dell'utente; svelato vero quando l'utente l'ha ascoltato, letto o ne
    ha chiesto il risultato, risposta 18 di Gabriele.
    """
    id: int
    fase: int
    gruppo: str
    turno: int
    posto: int
    a: object
    b: object
    set_al_meglio: int
    finalina: bool = False
    esito: str | None = None
    vince: str | None = None
    set: list = dataclasses.field(default_factory=list)
    set_giocati: int = 0
    seme: int = 0
    data: str | None = None
    motore: str | None = None
    differita: dict | None = None
    svelato: bool = False

    def a_dizionario(self):
        dati = dataclasses.asdict(self)
        dati["set"] = [list(s) for s in self.set]
        return dati

    @classmethod
    def da_dizionario(cls, dati):
        _controlla(isinstance(dati, dict) and set(dati) == {f.name for f in dataclasses.fields(cls)}, f"Un incontro del torneo ha i campi sbagliati: {dati!r}")
        for campo in ("id", "fase", "turno", "posto", "set_al_meglio", "set_giocati", "seme"):
            _controlla(_intero(dati[campo]) and dati[campo] >= 0, f"Incontro del torneo: il campo {campo} non è valido.")
        _controlla(isinstance(dati["gruppo"], str) and dati["gruppo"], "Incontro del torneo: il gruppo non è valido.")
        _controlla(_id_valido(dati["a"]) and (dati["b"] is None or _id_valido(dati["b"])), "Incontro del torneo: i due iscritti non sono validi.")
        _controlla(dati["esito"] is None or dati["esito"] in ESITI, f"Incontro del torneo: l'esito {dati['esito']!r} non è valido.")
        _controlla(dati["vince"] in (None, "A", "B"), "Incontro del torneo: il vincitore non è valido.")
        _controlla(isinstance(dati["set"], list) and all(isinstance(s, list) and len(s) == 2 and all(_intero(x) and x >= 0 for x in s) for s in dati["set"]),
                   "Incontro del torneo: i set non sono validi.")
        _controlla(isinstance(dati["finalina"], bool) and isinstance(dati["svelato"], bool), "Incontro del torneo: finalina e svelato sono sì o no.")
        _controlla(dati["data"] is None or isinstance(dati["data"], str), "Incontro del torneo: la data non è valida.")
        _controlla(dati["motore"] is None or dati["motore"] in MOTORI, "Incontro del torneo: il motore non è valido.")
        _controlla(dati["differita"] is None or isinstance(dati["differita"], dict), "Incontro del torneo: la differita non è valida.")
        return cls(**{**dati, "set": [list(s) for s in dati["set"]]})

    @property
    def giocato(self):
        return self.esito is not None

    def set_e_punti(self):
        """I set vinti e persi e i punti fatti e subiti, di A e di B: (set di A, set di B, punti di A, punti di B)."""
        set_a = sum(1 for x, y in self.set if x > y)
        set_b = sum(1 for x, y in self.set if y > x)
        return set_a, set_b, sum(x for x, _y in self.set), sum(y for _x, y in self.set)


@dataclasses.dataclass
class Fase:
    """
    Una fase che si gioca: a gironi, con la lettera e gli iscritti di ogni girone in ordine, oppure a
    tabellone, con i posti del primo turno sotto la lettera T, None per i riposi. turno_corrente è il
    prossimo turno da giocare; promossi chi passa, in ordine, quando la fase è finita.
    """
    indice: int
    tipo: str
    gironi: dict
    turni: int
    turno_corrente: int = 1
    incontri: list = dataclasses.field(default_factory=list)
    promossi: list = dataclasses.field(default_factory=list)
    per_girone: int = 0
    finalina: bool = False
    ultima: bool = False
    grandezza: int = 0

    @property
    def finita(self):
        return self.turno_corrente > self.turni

    def a_dizionario(self):
        return {"indice": self.indice, "tipo": self.tipo, "gironi": [[lettera, list(ids)] for lettera, ids in self.gironi.items()], "turni": self.turni,
                "turno_corrente": self.turno_corrente, "incontri": [i.a_dizionario() for i in self.incontri], "promossi": list(self.promossi),
                "per_girone": self.per_girone, "finalina": self.finalina, "ultima": self.ultima, "grandezza": self.grandezza}

    @classmethod
    def da_dizionario(cls, dati):
        campi = {f.name for f in dataclasses.fields(cls)}
        _controlla(isinstance(dati, dict) and set(dati) == campi, f"Una fase del torneo ha i campi sbagliati: {sorted(dati) if isinstance(dati, dict) else dati!r}")
        _controlla(dati["tipo"] in (formule.GIRONI, formule.TABELLONE), "Fase del torneo: il tipo non è valido.")
        for campo in ("indice", "turni", "turno_corrente", "per_girone", "grandezza"):
            _controlla(_intero(dati[campo]) and dati[campo] >= 0, f"Fase del torneo: il campo {campo} non è valido.")
        _controlla(isinstance(dati["gironi"], list) and all(isinstance(g, list) and len(g) == 2 and isinstance(g[0], str) and isinstance(g[1], list) for g in dati["gironi"]),
                   "Fase del torneo: i gironi non sono validi.")
        _controlla(isinstance(dati["promossi"], list) and all(_id_valido(p) for p in dati["promossi"]), "Fase del torneo: i promossi non sono validi.")
        _controlla(isinstance(dati["finalina"], bool) and isinstance(dati["ultima"], bool), "Fase del torneo: finalina e ultima sono sì o no.")
        _controlla(isinstance(dati["incontri"], list), "Fase del torneo: gli incontri non sono un elenco.")
        return cls(indice=dati["indice"], tipo=dati["tipo"], gironi={lettera: list(ids) for lettera, ids in dati["gironi"]}, turni=dati["turni"],
                   turno_corrente=dati["turno_corrente"], incontri=[IncontroDelTorneo.da_dizionario(i) for i in dati["incontri"]], promossi=list(dati["promossi"]),
                   per_girone=dati["per_girone"], finalina=dati["finalina"], ultima=dati["ultima"], grandezza=dati["grandezza"])

    def del_turno(self, turno):
        return [i for i in self.incontri if i.turno == turno]


def _chiave_club(info):
    club = info.get("club")
    return None if club is None else (club["nome"], club["fondazione"])


class Torneo:
    """
    Una sede di torneo. Si crea al sorteggio con gli iscritti e le loro informazioni, per id: nome,
    sesso, club al momento dell'iscrizione col giorno di fondazione oppure None per i liberi, forza al
    sorteggio, quota pagata e, nella coppa, la rosa iscritta. Gli iscritti si ordinano per forza, dal
    più forte, e a parità per id: sono le teste di serie, dalla classe di oggi, D32.
    """

    def __init__(self, id_torneo, edizione, sede, modello, formula, data_inizio, seme, info):
        self.id = id_torneo
        self.edizione = edizione
        self.sede = sede
        self.modello = copy.deepcopy(dict(modello))
        self.formula = copy.deepcopy(dict(formula))
        self.data_inizio = _data_in_testo(data_inizio)
        self.seme = seme
        self.info = {gid: copy.deepcopy(dict(dati)) for gid, dati in info.items()}
        self.iscritti = sorted(self.info, key=lambda gid: (-self.info[gid]["forza"], gid))
        self.fasi = []
        self.fase_corrente = 0
        self.giorni_giocati = 0
        self.stato = IN_CORSO
        self.classifica_finale = []
        self.premi = {}
        self.prossimo_incontro = 1
        self._struttura = formule.struttura(self.formula, len(self.iscritti))
        self._posto_di_testa = {gid: posto for posto, gid in enumerate(self.iscritti)}
        self._prepara_fase(0, list(self.iscritti))

    # Le informazioni.

    @property
    def squadre(self):
        return self.modello["tipo"] == modelli_torneo.SQUADRE

    def forza(self, gid):
        return self.info[gid]["forza"]

    def _club_di(self, gid):
        return _chiave_club(self.info[gid])

    def _per_forza(self, ids):
        return sorted(ids, key=lambda gid: (-self.forza(gid), self._posto_di_testa[gid]))

    def incontri(self):
        """Tutti gli incontri della sede, fase per fase."""
        return [i for fase in self.fasi for i in fase.incontri]

    def incontri_di(self, gid):
        return [i for i in self.incontri() if gid in (i.a, i.b)]

    # La preparazione delle fasi.

    def _nuovo_incontro(self, fase, gruppo, turno, posto, a, b, set_al_meglio, finalina=False):
        incontro = IncontroDelTorneo(id=self.prossimo_incontro, fase=fase.indice, gruppo=gruppo, turno=turno, posto=posto, a=a, b=b, set_al_meglio=set_al_meglio,
                                     finalina=finalina)
        self.prossimo_incontro += 1
        incontro.seme = random.Random(f"{self.seme}-{incontro.id}").getrandbits(63)
        if b is None:
            incontro.esito, incontro.vince = RIPOSO, "A"
        fase.incontri.append(incontro)
        return incontro

    def _set_del_turno(self, giocatori_nel_turno):
        """Al meglio di quanti set si gioca un turno: la gara a squadre ha un set; il tabellone con al massimo finali_da giocatori usa set_finali."""
        if self.squadre:
            return SET_SQUADRE
        finali_da = self.modello["finali_da"]
        if giocatori_nel_turno is not None and finali_da and giocatori_nel_turno <= finali_da:
            return self.modello["set_finali"]
        return self.modello["set_al_meglio"]

    def _prepara_fase(self, indice, partecipanti):
        struttura = self._struttura[indice]
        if struttura["tipo"] == formule.GIRONI:
            gironi = gironi_a_serpentina(partecipanti, len(struttura["grandezze"]), self._club_di)
            fase = Fase(indice=indice, tipo=formule.GIRONI, gironi={lettera_girone(n): ids for n, ids in enumerate(gironi)},
                        turni=max(formule.turni_del_girone(len(ids)) for ids in gironi), per_girone=struttura["promossi"], ultima=struttura["ultima"])
            for lettera, ids in fase.gironi.items():
                for turno, coppie in enumerate(calendario_del_girone(ids), start=1):
                    for posto, (a, b) in enumerate(coppie):
                        self._nuovo_incontro(fase, lettera, turno, posto, a, b, self._set_del_turno(None))
        else:
            grandezza = struttura["grandezza"]
            posti = [partecipanti[testa - 1] if testa <= len(partecipanti) else None for testa in ordine_tabellone(grandezza)]
            if self.fasi and self.fasi[-1].tipo == formule.GIRONI:
                self._separa_compagni_di_girone(posti, self.fasi[-1])
            fase = Fase(indice=indice, tipo=formule.TABELLONE, gironi={TABELLONE: posti}, turni=struttura["turni"], finalina=struttura["finalina"],
                        ultima=struttura["ultima"], grandezza=grandezza)
            for posto in range(grandezza // 2):
                a, b = posti[2 * posto], posti[2 * posto + 1]
                if a is None:
                    a, b = b, a
                self._nuovo_incontro(fase, TABELLONE, 1, posto, a, b, self._set_del_turno(grandezza))
        self.fasi.append(fase)
        self.fase_corrente = len(self.fasi) - 1

    def _separa_compagni_di_girone(self, posti, gironi_di_prima):
        """
        Al primo turno del tabellone due compagni dello stesso girone non si affrontano, quando si può:
        il più debole dei due si scambia con chi sta allo stesso posto del confronto più vicino, se lo
        scambio non crea un altro conflitto. I riposi restano dove sono, e restano alle prime teste: un
        confronto con un riposo non entra negli scambi, perché il debole prenderebbe il riposo della
        testa e la testa dovrebbe giocare, contro il punto 4.9 del progetto; lo ha visto la revisione
        del 14 ottobre 2026.
        """
        girone_di = {gid: lettera for lettera, ids in gironi_di_prima.gironi.items() for gid in ids}

        def conflitto(k):
            a, b = posti[2 * k], posti[2 * k + 1]
            return a is not None and b is not None and girone_di.get(a) == girone_di.get(b)

        confronti = len(posti) // 2
        for k in range(confronti):
            if not conflitto(k):
                continue
            a, b = posti[2 * k], posti[2 * k + 1]
            debole = 2 * k + (1 if self._per_forza([a, b])[0] == a else 0)
            lato = debole - 2 * k
            for distanza in range(1, confronti):
                fatto = False
                for j in (k + distanza, k - distanza):
                    if not 0 <= j < confronti:
                        continue
                    altro = 2 * j + lato
                    if posti[altro] is None or posti[2 * j + 1 - lato] is None:
                        continue
                    posti[debole], posti[altro] = posti[altro], posti[debole]
                    if conflitto(k) or conflitto(j):
                        posti[debole], posti[altro] = posti[altro], posti[debole]
                        continue
                    fatto = True
                    break
                if fatto:
                    break

    # Il gioco, punto 4.13.

    def giornata(self, gioca, data):
        """
        Gioca la giornata di oggi: il turno corrente della fase corrente, poi il seguente, fino a
        incontri_al_giorno turni; una fase che finisce non lascia cominciare la seguente nello stesso
        giorno. Per ogni incontro chiama gioca(incontro, azioni_del_giorno), dove azioni_del_giorno
        dice per ciascuno dei due quante azioni ha già giocato oggi nel torneo, e riceve un dizionario
        con esito, vince, set, set_giocati e, se ci sono, motore, differita e azioni, le azioni giocate
        per id. I riposi si chiudono da soli. Restituisce gli incontri giocati e se il torneo è finito.
        """
        if self.stato != IN_CORSO:
            return [], True
        fase = self.fasi[self.fase_corrente]
        giocati = []
        azioni = {}
        turni_oggi = 0
        while turni_oggi < self.modello["incontri_al_giorno"] and not fase.finita:
            for incontro in fase.del_turno(fase.turno_corrente):
                if incontro.giocato:
                    continue
                risultato = gioca(incontro, {gid: azioni.get(gid, 0) for gid in (incontro.a, incontro.b)})
                self._registra(incontro, risultato, data)
                for gid, quante in (risultato.get("azioni") or {}).items():
                    azioni[gid] = azioni.get(gid, 0) + quante
                giocati.append(incontro)
            fase.turno_corrente += 1
            turni_oggi += 1
            if fase.tipo == formule.TABELLONE and not fase.finita:
                self._prossimo_turno_del_tabellone(fase)
        if turni_oggi:
            self.giorni_giocati += 1
        if fase.finita:
            self._chiudi_fase(fase)
        return giocati, self.stato != IN_CORSO

    def _registra(self, incontro, risultato, data):
        problema = problema_del_risultato(incontro, risultato)
        if problema:
            raise ValueError(problema)
        incontro.esito = risultato["esito"]
        incontro.vince = risultato["vince"]
        incontro.set = [list(s) for s in risultato["set"]]
        incontro.set_giocati = risultato["set_giocati"]
        incontro.motore = risultato.get("motore")
        incontro.differita = risultato.get("differita")
        incontro.data = _data_in_testo(data)

    def vincitore(self, incontro):
        """Chi passa: il vincitore, chi riposa, e nel tavolino doppio la testa di serie più alta dei due."""
        if incontro.esito == RIPOSO or incontro.vince == "A":
            return incontro.a
        if incontro.vince == "B":
            return incontro.b
        return min((incontro.a, incontro.b), key=lambda gid: self._posto_di_testa[gid])

    def sconfitto(self, incontro):
        """Chi non passa, oppure None per il riposo."""
        if incontro.esito == RIPOSO:
            return None
        vincitore = self.vincitore(incontro)
        return incontro.b if vincitore == incontro.a else incontro.a

    def _prossimo_turno_del_tabellone(self, fase):
        """I vincitori di due incontri vicini si affrontano; dopo le semifinali, con la finalina, anche i due sconfitti, nello stesso turno della finale."""
        turno = fase.turno_corrente
        precedenti = sorted(fase.del_turno(turno - 1), key=lambda i: i.posto)
        precedenti = [i for i in precedenti if not i.finalina]
        vincitori = [self.vincitore(i) for i in precedenti]
        giocatori_nel_turno = fase.grandezza >> (turno - 1)
        set_al_meglio = self._set_del_turno(giocatori_nel_turno)
        for posto in range(len(vincitori) // 2):
            self._nuovo_incontro(fase, TABELLONE, turno, posto, vincitori[2 * posto], vincitori[2 * posto + 1], set_al_meglio)
        if fase.finalina and turno == fase.turni and len(precedenti) == 2:
            sconfitti = [self.sconfitto(i) for i in precedenti]
            if None not in sconfitti:
                a, b = self._per_forza(sconfitti)
                self._nuovo_incontro(fase, TABELLONE, turno, 1, a, b, set_al_meglio, finalina=True)

    def _chiudi_fase(self, fase):
        if fase.tipo == formule.GIRONI:
            classifiche = {lettera: classifica_girone(self, fase, lettera) for lettera in fase.gironi}
            if not fase.ultima:
                for posto in range(fase.per_girone):
                    fase.promossi.extend(self._per_forza([ordine[posto] for ordine in classifiche.values() if posto < len(ordine)]))
        else:
            ultimo = sorted((i for i in fase.del_turno(fase.turni) if not i.finalina), key=lambda i: i.posto)
            fase.promossi = sorted((self.vincitore(i) for i in ultimo), key=lambda gid: self._posto_di_testa[gid])
        if fase.ultima:
            self._concludi()
        else:
            self._prepara_fase(fase.indice + 1, list(fase.promossi))

    def _concludi(self):
        self.classifica_finale = classifica_finale(self)
        paganti = sum(1 for dati in self.info.values() if dati.get("pagato", 0) > 0)
        premi = calcola_premi(montepremi(self.modello, paganti), self.modello["posti_premiati"], self.modello["pendenza_premi"], len(self.iscritti))
        self.premi = dict(zip(self.classifica_finale, premi, strict=False))
        self.stato = CONCLUSO

    @property
    def medaglie(self):
        """I primi quattro della classifica finale: oro, argento, bronzo e legno."""
        return dict(zip(("oro", "argento", "bronzo", "legno"), self.classifica_finale, strict=False))

    def fasi_superate(self):
        """
        Quante fasi ha superato ciascuno: un girone passato, un turno di tabellone vinto, anche col
        riposo, che non vale come vittoria ma come turno superato. Le finaline non contano.
        """
        superate = dict.fromkeys(self.iscritti, 0)
        for fase in self.fasi:
            if fase.tipo == formule.GIRONI:
                for gid in fase.promossi:
                    superate[gid] += 1
            else:
                for incontro in fase.incontri:
                    if incontro.giocato and not incontro.finalina:
                        superate[self.vincitore(incontro)] += 1
        return superate

    # Il salvataggio.

    def a_dizionario(self):
        return {
            "id": self.id, "edizione": self.edizione, "sede": self.sede, "modello": copy.deepcopy(self.modello), "formula": copy.deepcopy(self.formula),
            "data_inizio": self.data_inizio, "seme": self.seme, "iscritti": list(self.iscritti), "info": [[gid, copy.deepcopy(dati)] for gid, dati in self.info.items()],
            "fasi": [fase.a_dizionario() for fase in self.fasi], "fase_corrente": self.fase_corrente, "giorni_giocati": self.giorni_giocati, "stato": self.stato,
            "classifica_finale": list(self.classifica_finale), "premi": [[gid, euro] for gid, euro in self.premi.items()], "prossimo_incontro": self.prossimo_incontro,
        }

    @classmethod
    def da_dizionario(cls, dati):
        """La sede di torneo dal suo dizionario; ValueError col motivo se qualcosa non va."""
        campi = {"id", "edizione", "sede", "modello", "formula", "data_inizio", "seme", "iscritti", "info", "fasi", "fase_corrente", "giorni_giocati", "stato",
                 "classifica_finale", "premi", "prossimo_incontro"}
        _controlla(isinstance(dati, dict) and set(dati) == campi, "Un torneo salvato ha i campi sbagliati.")
        for campo in ("id", "edizione", "sede", "seme", "fase_corrente", "giorni_giocati", "prossimo_incontro"):
            _controlla(_intero(dati[campo]) and dati[campo] >= 0, f"Torneo: il campo {campo} non è valido.")
        problema = modelli_torneo.problema_dei_campi(dati["modello"])
        _controlla(problema is None, f"Torneo {dati['id']}: il modello congelato non va: {problema}")
        problema = formule.valida_formula(dati["formula"])
        _controlla(problema is None, f"Torneo {dati['id']}: la formula congelata non va: {problema}")
        _controlla(dati["stato"] in STATI, f"Torneo {dati['id']}: lo stato non è valido.")
        _controlla(isinstance(dati["info"], list) and all(isinstance(r, list) and len(r) == 2 and _id_valido(r[0]) and isinstance(r[1], dict) for r in dati["info"]),
                   f"Torneo {dati['id']}: le informazioni degli iscritti non sono valide.")
        info = {gid: copy.deepcopy(valori) for gid, valori in dati["info"]}
        for gid, valori in info.items():
            _controlla({"nome", "forza", "club"} <= set(valori) and isinstance(valori["forza"], (int, float)), f"Torneo {dati['id']}: le informazioni di {gid} non sono complete.")
        _controlla(isinstance(dati["data_inizio"], str), f"Torneo {dati['id']}: la data d'inizio non è valida.")
        torneo = cls.__new__(cls)
        torneo.id, torneo.edizione, torneo.sede, torneo.seme = dati["id"], dati["edizione"], dati["sede"], dati["seme"]
        torneo.modello, torneo.formula = copy.deepcopy(dati["modello"]), copy.deepcopy(dati["formula"])
        torneo.data_inizio = dati["data_inizio"]
        torneo.info = info
        torneo.iscritti = list(dati["iscritti"])
        _controlla(sorted(torneo.iscritti, key=str) == sorted(info, key=str), f"Torneo {dati['id']}: gli iscritti non corrispondono alle informazioni.")
        torneo.fasi = [Fase.da_dizionario(f) for f in dati["fasi"]]
        torneo.fase_corrente, torneo.giorni_giocati, torneo.stato = dati["fase_corrente"], dati["giorni_giocati"], dati["stato"]
        torneo.classifica_finale = list(dati["classifica_finale"])
        _controlla(isinstance(dati["premi"], list) and all(isinstance(r, list) and len(r) == 2 and _intero(r[1]) for r in dati["premi"]), f"Torneo {dati['id']}: i premi non sono validi.")
        torneo.premi = dict(dati["premi"])
        torneo.prossimo_incontro = dati["prossimo_incontro"]
        torneo._posto_di_testa = {gid: posto for posto, gid in enumerate(torneo.iscritti)}
        torneo._struttura = formule.struttura(torneo.formula, len(torneo.iscritti))
        _controlla(torneo.fasi and torneo.fase_corrente < len(torneo.fasi), f"Torneo {dati['id']}: le fasi non sono valide.")
        ids = [i.id for i in torneo.incontri()]
        _controlla(len(ids) == len(set(ids)) and all(i < torneo.prossimo_incontro for i in ids), f"Torneo {dati['id']}: gli incontri hanno identificativi doppi.")
        presenti = set(info)
        _controlla(all(i.a in presenti and (i.b is None or i.b in presenti) for i in torneo.incontri()), f"Torneo {dati['id']}: un incontro ha un iscritto che non c'è.")
        return torneo


def _data_in_testo(data):
    if isinstance(data, datetime.datetime):
        return data.date().isoformat()
    if isinstance(data, datetime.date):
        return data.isoformat()
    return str(data)


def problema_del_risultato(incontro, risultato):
    """None se il risultato che arriva dalla funzione che gioca è coerente con l'incontro; altrimenti il motivo."""
    if not isinstance(risultato, dict) or risultato.get("esito") not in ESITI_GIOCATI:
        return f"Il risultato dell'incontro {incontro.id} non ha un esito valido: {risultato!r}"
    esito, vince, sets, giocati = risultato["esito"], risultato.get("vince"), risultato.get("set"), risultato.get("set_giocati")
    if not isinstance(sets, list) or not all(isinstance(s, (list, tuple)) and len(s) == 2 and all(_intero(x) and x >= 0 for x in s) for s in sets):
        return f"Il risultato dell'incontro {incontro.id} non ha set validi."
    if not _intero(giocati) or not 0 <= giocati <= len(sets):
        return f"Il risultato dell'incontro {incontro.id} non ha un numero valido di set giocati."
    if esito == TAVOLINO_DOPPIO:
        return None if vince is None and not sets and giocati == 0 else f"Il tavolino doppio dell'incontro {incontro.id} non ha vincitori né set."
    if vince not in ("A", "B"):
        return f"Il risultato dell'incontro {incontro.id} non dice chi vince."
    necessari = incontro.set_al_meglio // 2 + 1
    vinti = sum(1 for x, y in sets if (x > y) == (vince == "A") and x != y)
    persi = len(sets) - vinti
    if vinti != necessari or persi >= necessari:
        return f"Nel risultato dell'incontro {incontro.id} il vincitore non ha i set che servono: {sets}."
    if esito == TAVOLINO and giocati != 0:
        return f"Il tavolino dell'incontro {incontro.id} non ha set giocati."
    if esito == REGOLARE and giocati != len(sets):
        return f"L'incontro regolare {incontro.id} ha giocato tutti i suoi set."
    return None


# Le classifiche, punti 4.8 e 4.11.

def _statistiche(incontri, ids):
    """Per ogni id: vittorie, set vinti e persi, punti fatti e subiti negli incontri dati, contando soltanto quelli fra due degli ids."""
    dentro = set(ids)
    conti = {gid: [0, 0, 0, 0, 0] for gid in ids}
    for incontro in incontri:
        if incontro.esito in (None, RIPOSO) or incontro.a not in dentro or incontro.b not in dentro:
            continue
        set_a, set_b, punti_a, punti_b = incontro.set_e_punti()
        for gid, vinto, s_f, s_s, p_f, p_s in ((incontro.a, incontro.vince == "A", set_a, set_b, punti_a, punti_b),
                                               (incontro.b, incontro.vince == "B", set_b, set_a, punti_b, punti_a)):
            riga = conti[gid]
            riga[0] += vinto
            riga[1] += s_f
            riga[2] += s_s
            riga[3] += p_f
            riga[4] += p_s
    return conti


def _spareggio(torneo, gruppo, incontri):
    """
    L'ordine di un gruppo a pari vittorie nel girone, secondo l'articolo 8 del Regolamento Eventi
    Federali della FISPIC, deliberazione del Consiglio federale del 23 giugno 2026. Fra due, il punto 1:
    prima le vittorie negli scontri diretti, poi la differenza set e la differenza punti negli scontri
    diretti. Fra tre o più, il punto 2: le vittorie negli scontri diretti fra tutti quelli a pari punti,
    poi la differenza set e la differenza punti negli stessi scontri, un criterio dopo l'altro, e ogni
    criterio divide soltanto chi il criterio di prima ha lasciato pari. Il testo aggiunge: «nel momento
    in cui rimangono due atleti in situazione di parità, deve essere adottato il punto 1, partendo dalla
    lettera a)»; quindi un blocco che resta di due, dopo qualunque criterio, si decide subito con lo
    scontro diretto fra loro due, e non col criterio seguente calcolato su tutti. Un blocco di tre o più
    che resta pari dopo la differenza punti riparte dal punto 2 fra loro soli, se sono meno di prima,
    lettura dell'architetto che il testo non esclude. Al posto del sorteggio la forza al sorteggio,
    scelta dell'architetto, perché il risultato sia ripetibile. La revisione del 14 ottobre 2026 ha
    corretto la prima versione, che ordinava tutto il gruppo con i tre criteri insieme e tornava allo
    scontro diretto soltanto quando erano pari in tutti e tre.
    """
    if len(gruppo) <= 1:
        return list(gruppo)
    conti = _statistiche(incontri, gruppo)
    criteri = (lambda gid: conti[gid][0], lambda gid: conti[gid][1] - conti[gid][2], lambda gid: conti[gid][3] - conti[gid][4])
    if len(gruppo) == 2:
        # Il punto 1: fra due gli scontri diretti sono gli incontri fra loro, e i tre criteri si leggono in fila.
        def chiave(gid):
            return tuple(criterio(gid) for criterio in criteri)
        primo, secondo = sorted(gruppo, key=chiave, reverse=True)
        return [primo, secondo] if chiave(primo) != chiave(secondo) else torneo._per_forza(gruppo)

    def dividi(blocco, livello):
        if len(blocco) == 1:
            return list(blocco)
        if len(blocco) == 2:
            return _spareggio(torneo, blocco, incontri)
        if livello == len(criteri):
            return _spareggio(torneo, blocco, incontri) if len(blocco) < len(gruppo) else torneo._per_forza(blocco)
        criterio = criteri[livello]
        ordine = []
        for valore in sorted({criterio(gid) for gid in blocco}, reverse=True):
            ordine.extend(dividi([gid for gid in blocco if criterio(gid) == valore], livello + 1))
        return ordine

    return dividi(list(gruppo), 0)


def classifica_girone(torneo, fase, lettera):
    """La classifica di un girone, senza pareggi, D6: prima le vittorie, poi gli spareggi dell'articolo 8 della FISPIC. Il tavolino doppio è una sconfitta per tutti e due."""
    ids = fase.gironi[lettera]
    incontri = [i for i in fase.incontri if i.gruppo == lettera]
    vittorie = {gid: riga[0] for gid, riga in _statistiche(incontri, ids).items()}
    ordine = []
    for quante in sorted(set(vittorie.values()), reverse=True):
        ordine.extend(_spareggio(torneo, [gid for gid in ids if vittorie[gid] == quante], incontri))
    return ordine


def statistiche_del_girone(fase, lettera):
    """Per ogni iscritto del girone: vittorie, set vinti e persi, punti fatti e subiti, per la classifica da leggere."""
    return _statistiche([i for i in fase.incontri if i.gruppo == lettera], fase.gironi[lettera])


def _quoziente(fatti, subiti):
    """Un quoziente: con zero al denominatore vale infinito, e zero se anche il numeratore è zero."""
    if subiti == 0:
        return math.inf if fatti > 0 else 0.0
    return fatti / subiti


def classifica_finale(torneo):
    """
    La classifica finale della sede, punto 4.11: il vincitore e lo sconfitto della finale, sempre
    primo e secondo; poi il vincitore e lo sconfitto della finalina, o senza finalina i semifinalisti
    sconfitti ordinati per gli spareggi; poi chi è uscito ai quarti, agli ottavi e così via; poi chi è
    uscito nei gironi, per posto nel girone. Gli spareggi, a parità di turno o di posto: le vittorie in
    tutto il torneo, il quoziente dei set, quello dei punti e la forza. Con un girone unico finale la
    classifica è la sua.
    """
    conti = _statistiche(torneo.incontri(), torneo.iscritti)

    def ordina(ids):
        def chiave(gid):
            vittorie, set_vinti, set_persi, punti_fatti, punti_subiti = conti[gid]
            return (-vittorie, -_quoziente(set_vinti, set_persi), -_quoziente(punti_fatti, punti_subiti), -torneo.forza(gid), torneo._posto_di_testa[gid])
        return sorted(ids, key=chiave)

    classifica = []
    for fase in reversed(torneo.fasi):
        if fase.tipo == formule.GIRONI:
            ordini = [classifica_girone(torneo, fase, lettera) for lettera in fase.gironi]
            if fase.ultima:
                classifica.extend(ordini[0] if len(ordini) == 1 else ordina([gid for ordine in ordini for gid in ordine]))
                continue
            for posto in range(fase.per_girone, max(len(o) for o in ordini)):
                classifica.extend(ordina([ordine[posto] for ordine in ordini if posto < len(ordine)]))
            continue
        def sconfitti(turno, fase=fase):
            return ordina([s for s in (torneo.sconfitto(i) for i in fase.del_turno(turno) if not i.finalina) if s is not None])

        if not fase.ultima:
            for turno in range(fase.turni, 0, -1):
                classifica.extend(sconfitti(turno))
            continue
        finale = next(i for i in fase.del_turno(fase.turni) if not i.finalina)
        classifica.extend([torneo.vincitore(finale), torneo.sconfitto(finale)])
        finalina = next((i for i in fase.del_turno(fase.turni) if i.finalina), None)
        if finalina is not None:
            classifica.extend([torneo.vincitore(finalina), torneo.sconfitto(finalina)])
        elif fase.turni >= 2:
            classifica.extend(sconfitti(fase.turni - 1))
        for turno in range(fase.turni - 2, 0, -1):
            classifica.extend(sconfitti(turno))
    visti = set()
    finale = []
    for gid in classifica:
        if gid not in visti:
            visti.add(gid)
            finale.append(gid)
    return finale
