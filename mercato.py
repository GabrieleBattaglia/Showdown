"""
Il mercato di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 7 del piano, secondo la decisione D20: come nel mercato di
Hattrick si cercano i giocatori con tanti filtri sulle caratteristiche, gli stessi della ricerca,
e a chi interessa si fa un'offerta. Dalla tappa 8, con l'economia delle decisioni D22 e D23, al
mercato ci sono tre tipi di giocatori: i liberi, a cui si offre un premio d'ingaggio; quelli in
vendita, che si comprano al prezzo chiesto; e i tesserati del computer, per cui si fa
un'offerta d'acquisto alla loro polisportiva. Qui sta la scelta dei candidati, con quanto costa
ciascuno; le offerte sono operazioni del mondo.
Dal 24 ottobre 2026, con la issue 8 e la decisione D36, qui sta anche il motore della finestra unica
Mercato e ricerca, che riunisce il mercato dei giocatori, quello degli allenatori, la ricerca e la scelta
dell'avversario dell'amichevole, come la descrive la proposta della notte. Chi cercare lo dicono cinque
caselle, che si sommano: liberi, in vendita da altri, tesserati del computer, tuoi tesserati e ritirati;
per gli allenatori i liberi, chi allena per il computer e il tuo staff. Poi i filtri dei controlli e di
Altri filtri: quelli che per chi si cerca non contano si ignorano invece di svuotare l'elenco, e quelli
che si escludono a vicenda si segnalano. Gli ordini hanno la direzione nel nome, comprese le 24
caratteristiche, i punti della classifica nazionale e l'euro per punto di valore, e a parità decide il
numero; le ricerche pronte sono tredici. Che cosa è tuo lo dice una funzione sola, di_chi, con il posto
per i magnati di D35. Le funzioni pure offerta_possibile, amichevole_possibile e sfida_possibile dicono
per ogni riga che cosa si può fare, o perché no: i divieti restano in mondo.problema_* e in
sfide.problema_bersaglio. La Memoria tiene classe e valore di mercato per la durata della finestra, e chi
è in vendita si legge dalle liste in_vendita delle polisportive. Lo stato dei filtri di ogni porta
d'ingresso, Ctrl+K, Ctrl+Maiusc+G, Ctrl+F e Ctrl+O, vive nel mondo, scelta di Gabriele. Il mercato di
prima, coi candidati e la scelta Mostra, resta per il dialogo di oggi finché la finestra non lo
sostituisce. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import copy
from collections import namedtuple
from dataclasses import dataclass, field

import classe as modulo_classe
import contratti
import infortuni
import luoghi
import palmares
import ricerca
import sfide
import staff
from costanti import (
    ANNO_SIMULAZIONE_GIORNI,
    CARATTERISTICHE_ATTACCO_BASE,
    CARATTERISTICHE_CONTROLLO_BASE,
    CARATTERISTICHE_DIFESA_BASE,
    CARATTERISTICHE_FISICHE_BASE,
)
from economia import ingaggio_richiesto, stipendio, stipendio_pagato, valore_di_mercato
from utilita import accorda

LIBERO = "libero"
IN_VENDITA = "in_vendita"
DEL_COMPUTER = "del_computer"
# Chi mostrare: chiave, nome da mostrare e tipi di giocatori.
SCELTE = (
    ("liberi_e_vendita", "i liberi e chi è in vendita", (LIBERO, IN_VENDITA)),
    ("liberi", "solo i liberi", (LIBERO,)),
    ("vendita", "solo chi è in vendita", (IN_VENDITA,)),
    ("computer", "i tesserati del computer", (DEL_COMPUTER,)),
    ("tutti", "tutti", (LIBERO, IN_VENDITA, DEL_COMPUTER)),
)
# Gli ordini dell'elenco dei candidati: chiave e nome da mostrare.
ORDINI = (
    ("valore", "valore, dal più alto"),
    ("costo", "costo, dal più basso"),
    ("stipendio", "stipendio, dal più basso"),
    ("eta", "età, dal più giovane"),
)
_CHIAVI = {
    "valore": lambda c: (-c.giocatore.indice_collettivo_valore, c.giocatore.id),
    "costo": lambda c: (c.costo, c.giocatore.id),
    "stipendio": lambda c: (c.stipendio, c.giocatore.id),
    "eta": lambda c: (c.giocatore.eta, c.giocatore.id),
}


@dataclass
class Candidato:
    """
    Un giocatore al mercato. Il costo è l'ingaggio che chiede, per un libero; il prezzo, per chi
    è in vendita; il valore di mercato del giorno, che fa da riferimento, per un tesserato del
    computer. Lo stipendio è quello che chiede oggi: chi arriva, anche comprato, firma un contratto nuovo.
    """
    giocatore: object
    tipo: str
    costo: int
    stipendio: int
    polisportiva: object = None


def candidati(mondo, poli, filtri=(), mostra="liberi_e_vendita", costo_massimo=0, ordine="valore"):
    """
    I giocatori al mercato per la polisportiva, che soddisfano tutti i filtri, terne di criterio,
    condizione e valore della ricerca, del tipo scelto e con un costo entro il massimo, se c'è,
    nell'ordine scelto. I tesserati della polisportiva stessa non ci sono mai.
    """
    tipi = {chiave: tipi for chiave, _nome, tipi in SCELTE}[mostra]
    righe = []
    if LIBERO in tipi:
        for gid in ricerca.cerca_con_filtri(mondo, "liberi", filtri):
            g = mondo.giocatori[gid]
            righe.append(Candidato(g, LIBERO, ingaggio_richiesto(g, poli), stipendio(g)))
    if IN_VENDITA in tipi or DEL_COMPUTER in tipi:
        for gid in ricerca.cerca_con_filtri(mondo, "tesserati", filtri):
            g = mondo.giocatori[gid]
            club = mondo.polisportive.get(g.appartenenza)
            if club is None or club is poli:
                continue
            if gid in club.in_vendita:
                if IN_VENDITA in tipi:
                    righe.append(Candidato(g, IN_VENDITA, club.in_vendita[gid], stipendio(g), club))
            elif club.is_cpu_controlled and DEL_COMPUTER in tipi:
                righe.append(Candidato(g, DEL_COMPUTER, valore_di_mercato(g, mondo.datetime_corrente_simulazione), stipendio(g), club))
    if costo_massimo:
        righe = [c for c in righe if c.costo <= costo_massimo]
    righe.sort(key=_CHIAVI[ordine])
    return righe


# La finestra unica Mercato e ricerca, issue 8 e decisione D36.

# Di chi è una polisportiva, per chi guarda dalla polisportiva attiva. Col magnate di D35 si aggiungerà
# DI_UN_ALTRO_MAGNATE, per le polisportive di un altro magnate: oggi tutte quelle dell'utente sono tue.
TUA_ATTIVA = "tua_attiva"
TUA_ALTRA = "tua_altra"
TUE = (TUA_ATTIVA, TUA_ALTRA)


def di_chi(mondo, poli):
    """
    Di chi è la polisportiva, la sola regola del motore: TUA_ATTIVA, TUA_ALTRA, una tua che non è l'attiva,
    DEL_COMPUTER, oppure None se non c'è. Fino alla finestra unica la regola era sparsa fra la finestra e il
    mercato; col magnate di D35 qui si distingueranno le polisportive degli altri magnati.
    """
    if poli is None:
        return None
    if poli.is_cpu_controlled:
        return DEL_COMPUTER
    if poli is mondo.miapolisportiva_attiva:
        return TUA_ATTIVA
    return TUA_ALTRA


# Gli stati di una riga dell'elenco, oltre a LIBERO, IN_VENDITA da altri e DEL_COMPUTER.
TUO = "tuo"
RITIRATO = "ritirato"
USCITO = "uscito"
# Le caselle del gruppo Chi cercare, che sono anche i campi dei filtri, con il nome della finestra.
CASELLE = (("liberi", "Liberi"), ("in_vendita", "In vendita da altri"), ("del_computer", "Tesserati del computer"),
           ("tuoi", "Tuoi tesserati"), ("ritirati", "Ritirati"))
# Le caselle che per gli allenatori non hanno un equivalente: chi è in vendita e i ritirati.
CASELLE_SOLO_GIOCATORI = ("in_vendita", "ritirati")
# I tratti di Altri filtri, ciascuno a tre voci: indifferente, sì e no. I nomi sono quelli della ricerca.
TRATTI = ("mancino", "ambidestro", "ipovedente", "giocorapido", "cambiovelocita", "talento", "apprendista_rapido", "precoce", "tardiva")
# Le 24 caratteristiche, per gli ordini e per le condizioni.
CARATTERISTICHE = CARATTERISTICHE_FISICHE_BASE + CARATTERISTICHE_DIFESA_BASE + CARATTERISTICHE_ATTACCO_BASE + CARATTERISTICHE_CONTROLLO_BASE
# I criteri delle condizioni di Altri filtri: i numerici della ricerca che non hanno già un campo, dalla
# proposta; sesso, classe, età, tratti, indole, nome e cognome restano fuori, e le condizioni restano
# maggiore di e minore di, strette come dice il loro nome.
CRITERI_DELLE_CONDIZIONI = ("valore", "esperienza", "ambizione", "punti_allenamento", "gloria_richiesta", "mesi_contratto", *CARATTERISTICHE)
# L'età massima dei giovani migliori, una ricerca pronta: la soglia si tara al collaudo.
ETA_DEI_GIOVANI = 20
# Gli ordini dei giocatori e quelli degli allenatori: la chiave e il nome, con la direzione.
ORDINI_GIOCATORI = (
    ("valore_alto", "valore, dal più alto"),
    ("valore_basso", "valore, dal più basso"),
    ("classe", "classe, dalla migliore"),
    ("eta_giovane", "età, dal più giovane"),
    ("eta_anziano", "età, dal più anziano"),
    ("costo_basso", "costo, dal più basso"),
    ("costo_alto", "costo, dal più alto"),
    ("euro_per_punto", "euro per punto di valore, dal più basso"),
    ("prezzo_sul_mercato", "prezzo sul valore di mercato, dal più basso"),
    ("stipendio_basso", "stipendio, dal più basso"),
    ("punti_nazionali", "punti della classifica nazionale, dal più alto"),
    ("punti_anno", "punti dell'ultimo anno, dal più alto"),
    ("esperienza", "esperienza, dalla più alta"),
    ("ambizione", "ambizione, dalla più alta"),
    ("punti_allenamento", "punti allenamento, dal più alto"),
    ("mesi_contratto", "mesi di contratto rimasti, dai meno"),
    ("numero", "numero, dal più basso"),
    *((caratteristica, f"{ricerca.nome_criterio(caratteristica)}, dalla più alta") for caratteristica in CARATTERISTICHE),
)
ORDINI_ALLENATORI = (
    ("classe", "classe, dalla migliore"),
    ("eta_giovane", "età, dal più giovane"),
    ("eta_anziano", "età, dal più anziano"),
    ("stipendio_basso", "stipendio chiesto da capo, dal più basso"),
    ("numero", "numero, dal più basso"),
)
# Gli ordini che seguono il costo: chi non ne ha uno, come un libero senza polisportiva attiva, va in fondo.
ORDINI_DEL_COSTO = ("costo_basso", "costo_alto", "euro_per_punto", "prezzo_sul_mercato")


def nome_dell_ordine(chiave, allenatori=False):
    return dict(ORDINI_ALLENATORI if allenatori else ORDINI_GIOCATORI)[chiave]


@dataclass
class Filtri:
    """
    I filtri della finestra Mercato e ricerca. I primi sono quelli dei controlli: la casella Allenatori, le
    cinque di Chi cercare, il nome, cognome o numero, il sesso, m o f, la classe migliore o uguale a un
    livello, da 1 per A1 a 100 per K0, l'età massima in anni interi, il costo massimo in euro, Disponibili
    oggi e i due ordini, uno per i giocatori e uno per gli allenatori. Gli altri sono quelli di Altri filtri.
    Per i numeri lo zero vuol dire nessun limite, per i testi il vuoto, per le scelte None. I tratti sono un
    dizionario dal tratto a vero o falso, e quelli che non ci sono restano indifferenti; le condizioni sono
    terne di criterio, condizione e valore, come nella ricerca.
    """
    allenatori: bool = False
    liberi: bool = False
    in_vendita: bool = False
    del_computer: bool = False
    tuoi: bool = False
    ritirati: bool = False
    nome: str = ""
    sesso: str | None = None
    classe_migliore: int = 0
    eta_massima: int = 0
    costo_massimo: int = 0
    disponibili_oggi: bool = False
    ordine: str = "valore_alto"
    ordine_allenatori: str = "classe"
    # Altri filtri.
    classe_peggiore: int = 0
    eta_minima: int = 0
    regione: str = ""
    provincia: str = ""
    comune: str = ""
    polisportiva: str = ""
    tratti: dict = field(default_factory=dict)
    indole: str | None = None
    valore_minimo: float = 0
    stipendio_massimo: int = 0
    mesi_contratto_massimi: int = 0
    senza_acciacchi: bool = False
    solo_ritirati_che_allenano: bool = False
    solo_nuovi: bool = False
    comprendi_usciti: bool = False
    condizioni: tuple = ()
    tipo_allenatore: str | None = None
    visus: str | None = None
    posto_attuale: str | None = None
    stipendio_capo_massimo: int = 0
    senza_prelazione_altrui: bool = False

    def copia(self):
        """Una copia che si può cambiare senza toccare questi filtri, tratti compresi."""
        return copy.deepcopy(self)

    @property
    def ordine_scelto(self):
        """L'ordine che vale per chi si cerca: quello degli allenatori se la casella è spuntata."""
        return self.ordine_allenatori if self.allenatori else self.ordine


_PREDEFINITI = Filtri()
# I campi di Altri filtri, nell'ordine in cui Filtri attivi li scrive.
CAMPI_ALTRI = ("classe_peggiore", "eta_minima", "regione", "provincia", "comune", "polisportiva", "tratti", "indole", "valore_minimo", "stipendio_massimo",
               "mesi_contratto_massimi", "senza_acciacchi", "solo_ritirati_che_allenano", "solo_nuovi", "comprendi_usciti", "condizioni",
               "tipo_allenatore", "visus", "posto_attuale", "stipendio_capo_massimo", "senza_prelazione_altrui")
# I campi che contano soltanto per i giocatori, e quelli che contano soltanto per gli allenatori: agli
# altri non si applicano, e Filtri attivi dice che non contano.
CAMPI_SOLO_GIOCATORI = ("in_vendita", "ritirati", "costo_massimo", "disponibili_oggi", "tratti", "indole", "valore_minimo", "stipendio_massimo",
                        "senza_acciacchi", "solo_ritirati_che_allenano", "solo_nuovi", "comprendi_usciti", "condizioni")
CAMPI_SOLO_ALLENATORI = ("tipo_allenatore", "visus", "posto_attuale", "stipendio_capo_massimo", "senza_prelazione_altrui")


def _testo(valore):
    """Un testo di un campo così come conta: senza gli spazi in testa e in coda."""
    return valore.strip()


def impostato(filtri, campo):
    """Vero se il campo dei filtri non è al suo valore di nessun filtro; un testo di soli spazi non conta."""
    valore = getattr(filtri, campo)
    if isinstance(valore, str) and campo not in ("ordine", "ordine_allenatori"):
        return bool(_testo(valore))
    return valore != getattr(_PREDEFINITI, campo)


def quanti_altri_filtri(filtri):
    """Quanti filtri di Altri filtri sono impostati, per l'etichetta del pulsante: ogni tratto e ogni condizione contano uno."""
    quanti = 0
    for campo in CAMPI_ALTRI:
        if campo in ("tratti", "condizioni"):
            quanti += len(getattr(filtri, campo))
        elif impostato(filtri, campo):
            quanti += 1
    return quanti


def azzera_altri(filtri):
    """I filtri con quelli di Altri filtri tutti a nessun filtro, come Azzera questi filtri; gli altri restano."""
    nuovi = filtri.copia()
    for campo in CAMPI_ALTRI:
        setattr(nuovi, campo, copy.deepcopy(getattr(_PREDEFINITI, campo)))
    return nuovi


def caselle_che_contano(filtri):
    """Le chiavi delle caselle di Chi cercare spuntate che contano per chi si cerca, nell'ordine della finestra."""
    return [chiave for chiave, _nome in CASELLE if getattr(filtri, chiave) and not (filtri.allenatori and chiave in CASELLE_SOLO_GIOCATORI)]


def non_contano(filtri, attiva=None):
    """
    I campi impostati che per chi si cerca non contano e si ignorano, nell'ordine dei campi, ciascuno col
    perché: "allenatori" per quelli dei soli giocatori, "giocatori" per quelli dei soli allenatori,
    "senza_attiva" per il costo massimo senza polisportiva attiva, perché l'ingaggio dipende dalla gloria
    di chi offre. attiva è la polisportiva attiva, o None.
    """
    if filtri.allenatori:
        return [(campo, "allenatori") for campo in CAMPI_SOLO_GIOCATORI if impostato(filtri, campo)]
    campi = [(campo, "giocatori") for campo in CAMPI_SOLO_ALLENATORI if impostato(filtri, campo)]
    if filtri.costo_massimo and attiva is None:
        campi.insert(0, ("costo_massimo", "senza_attiva"))
    return campi


def contraddizioni(filtri):
    """
    I filtri che contano e si escludono a vicenda, come coppie di codice e dati, nell'ordine in cui Filtri
    attivi li scrive. Non si correggono: l'elenco li applica tutti, e Filtri attivi dice perché si svuota.
    "disponibili" coi gruppi che Disponibili oggi esclude, i ritirati e gli usciti di scena; "allenano" coi
    gruppi che Solo i ritirati che allenano esclude, e "allenano_senza_ritirati" quando la casella Ritirati
    non è spuntata; "classi" ed "eta" coi due limiti rovesciati; "tratti" con due tratti che nessuno ha
    insieme; "polisportiva" coi gruppi che non hanno una polisportiva; "posto" per il posto attuale con gli
    allenatori liberi; "luogo" con una provincia che non sta nella regione scelta, e la sua regione vera.
    """
    gruppi = caselle_che_contano(filtri)
    usciti = filtri.comprendi_usciti and not filtri.allenatori
    trovate = []
    if not filtri.allenatori:
        if filtri.disponibili_oggi:
            esclusi = [gruppo for gruppo, c in (("ritirati", filtri.ritirati), ("usciti", usciti)) if c]
            if esclusi:
                trovate.append(("disponibili", esclusi))
        if filtri.solo_ritirati_che_allenano:
            esclusi = [g for g in gruppi if g != "ritirati"] + (["usciti"] if usciti else [])
            if esclusi:
                trovate.append(("allenano", esclusi))
            if not filtri.ritirati:
                trovate.append(("allenano_senza_ritirati", None))
    if filtri.classe_migliore and filtri.classe_peggiore and filtri.classe_peggiore > filtri.classe_migliore:
        trovate.append(("classi", (filtri.classe_migliore, filtri.classe_peggiore)))
    if filtri.eta_minima and filtri.eta_massima and filtri.eta_minima > filtri.eta_massima:
        trovate.append(("eta", (filtri.eta_minima, filtri.eta_massima)))
    if not filtri.allenatori:
        for primo, secondo in (("mancino", "ambidestro"), ("precoce", "tardiva")):
            if filtri.tratti.get(primo) and filtri.tratti.get(secondo):
                trovate.append(("tratti", (primo, secondo)))
    if _testo(filtri.polisportiva):
        senza_club = ("liberi", "ritirati") if not filtri.allenatori else ("liberi",)
        esclusi = [g for g in gruppi if g in senza_club] + (["usciti"] if usciti else [])
        if esclusi:
            trovate.append(("polisportiva", esclusi))
    if filtri.allenatori and filtri.posto_attuale and filtri.liberi:
        trovate.append(("posto", None))
    if filtri.regione and filtri.provincia:
        sua = luoghi.regione_della_provincia(filtri.provincia)
        if sua is not None and sua != filtri.regione:
            trovate.append(("luogo", (filtri.provincia, sua)))
    return trovate


def in_fondo(filtri, attiva=None):
    """
    Chi, in un ordine che segue il costo, non ha un costo e va in fondo: i liberi senza polisportiva attiva,
    i tuoi tesserati che non sono in vendita da un'altra tua polisportiva, i ritirati e gli usciti di scena.
    Un elenco vuoto negli altri ordini e per gli allenatori.
    """
    if filtri.allenatori or filtri.ordine not in ORDINI_DEL_COSTO:
        return []
    return [gruppo for gruppo, c in (("liberi", filtri.liberi and attiva is None), ("tuoi", filtri.tuoi), ("ritirati", filtri.ritirati),
                                       ("usciti", filtri.comprendi_usciti)) if c]


# Le ricerche pronte: ognuna imposta le caselle, i filtri, l'ordine e il nome, e azzera tutto il resto.
TORNA_AI_TUOI = "torna_ai_tuoi"
PRONTE = (
    (TORNA_AI_TUOI, "Torna ai tuoi filtri"),
    ("mercato", "Mercato: liberi e in vendita da altri, dal valore più alto"),
    ("tutti_in_attivita", "Tutti in attività, senza filtri, per numero"),
    ("piu_forti", "I più forti in attività, dal valore più alto"),
    ("giovani_migliori", f"I giovani migliori, fino a {ETA_DEI_GIOVANI} anni, dal valore più alto"),
    ("liberi_convenienti", "I liberi più convenienti, dagli euro d'ingaggio per punto di valore"),
    ("affari_in_vendita", "Gli affari in vendita da altri, dal prezzo sul valore di mercato"),
    ("avversari_amichevole", "Avversari per un'amichevole oggi, dalla classe migliore"),
    ("piu_titolati", "I più titolati in attività, dai punti della classifica nazionale"),
    ("allenatori_liberi", "Gli allenatori liberi migliori"),
    ("capi_migliori", "I capi allenatori migliori"),
    ("assistenti_migliori", "Gli assistenti migliori"),
    ("nuovi_arrivati", "I nuovi arrivati della sessione, dal valore più alto"),
)
_IN_ATTIVITA = {"liberi": True, "in_vendita": True, "del_computer": True, "tuoi": True}
_STAFF_IMPIEGATO = {"allenatori": True, "del_computer": True, "tuoi": True, "ordine_allenatori": "classe"}
_FILTRI_DELLE_PRONTE = {
    "mercato": {"liberi": True, "in_vendita": True, "ordine": "valore_alto"},
    "tutti_in_attivita": {**_IN_ATTIVITA, "ordine": "numero"},
    "piu_forti": {**_IN_ATTIVITA, "ordine": "valore_alto"},
    "giovani_migliori": {**_IN_ATTIVITA, "eta_massima": ETA_DEI_GIOVANI, "ordine": "valore_alto"},
    "liberi_convenienti": {"liberi": True, "ordine": "euro_per_punto"},
    "affari_in_vendita": {"in_vendita": True, "ordine": "prezzo_sul_mercato"},
    "avversari_amichevole": {**_IN_ATTIVITA, "disponibili_oggi": True, "ordine": "classe"},
    "piu_titolati": {**_IN_ATTIVITA, "ordine": "punti_nazionali"},
    "allenatori_liberi": {"allenatori": True, "liberi": True, "ordine_allenatori": "classe"},
    "capi_migliori": {**_STAFF_IMPIEGATO, "posto_attuale": staff.CAPO},
    "assistenti_migliori": {**_STAFF_IMPIEGATO, "posto_attuale": staff.ASSISTENTE},
    "nuovi_arrivati": {**_IN_ATTIVITA, "solo_nuovi": True, "ordine": "valore_alto"},
}
# Le porte d'ingresso della finestra, ciascuna con la sua ricerca pronta: Ctrl+K, Ctrl+Maiusc+G, che vale
# anche per Assumi dello staff, Ctrl+F e Ctrl+O.
PORTE = ("mercato", "allenatori", "ricerca", "amichevole")
PRONTA_DELLA_PORTA = {"mercato": "mercato", "allenatori": "allenatori_liberi", "ricerca": "tutti_in_attivita", "amichevole": "avversari_amichevole"}


def nome_della_pronta(chiave):
    return dict(PRONTE)[chiave]


def filtri_della_pronta(chiave):
    """I filtri di una ricerca pronta, tutto il resto a nessun filtro; KeyError per Torna ai tuoi filtri, che non ne ha di suoi."""
    return Filtri(**copy.deepcopy(_FILTRI_DELLE_PRONTE[chiave]))


@dataclass
class StatoDellaPorta:
    """
    Lo stato dei filtri di una porta d'ingresso, che il mondo ricorda: i filtri di adesso; la ricerca pronta
    da cui vengono, None se li hai fatti a mano; e gli ultimi filtri fatti a mano prima delle ricerche
    pronte, None se non ce ne sono, che Torna ai tuoi filtri rimette.
    """
    filtri: Filtri
    pronta: str | None = None
    a_mano: Filtri | None = None

    def copia(self):
        return copy.deepcopy(self)


def stato_predefinito(porta):
    """Lo stato di una porta mai usata, e quello di un mondo convertito: i filtri della sua ricerca pronta."""
    pronta = PRONTA_DELLA_PORTA[porta]
    return StatoDellaPorta(filtri_della_pronta(pronta), pronta)


def stato_della_porta(mondo, porta):
    """Una copia dello stato della porta che il mondo ricorda, o di quello predefinito: la finestra la cambia senza toccare il mondo."""
    stato = mondo.filtri_di_ricerca.get(porta)
    return stato.copia() if stato is not None else stato_predefinito(porta)


def ricorda_la_porta(mondo, porta, stato):
    """Il mondo ricorda lo stato della porta, che si salva con lui; KeyError per una porta che non esiste."""
    if porta not in PORTE:
        raise KeyError(porta)
    mondo.filtri_di_ricerca[porta] = stato.copia()


def fatti_a_mano(filtri):
    """Lo stato di filtri cambiati a mano: non vengono da una ricerca pronta, e Torna ai tuoi filtri sparisce."""
    return StatoDellaPorta(filtri.copia())


def con_la_pronta(stato, chiave):
    """
    Lo stato dopo una ricerca pronta. Torna ai tuoi filtri rimette gli ultimi fatti a mano; le altre ne
    impostano i filtri e ricordano quelli fatti a mano che c'erano, o quelli ricordati prima, se i filtri di
    adesso venivano già da una ricerca pronta. ValueError se Torna ai tuoi filtri non ha niente da rimettere.
    """
    if chiave == TORNA_AI_TUOI:
        if stato.a_mano is None:
            raise ValueError("Non ci sono filtri fatti a mano da rimettere.")
        return StatoDellaPorta(stato.a_mano.copia())
    a_mano = stato.filtri if stato.pronta is None else stato.a_mano
    return StatoDellaPorta(filtri_della_pronta(chiave), chiave, a_mano.copia() if a_mano is not None else None)


def pronte_disponibili(stato):
    """Le ricerche pronte del menu, coppie di chiave e nome: Torna ai tuoi filtri soltanto dopo una ricerca pronta, se prima c'erano filtri fatti a mano."""
    return [(chiave, nome) for chiave, nome in PRONTE if chiave != TORNA_AI_TUOI or stato.a_mano is not None]


class Memoria:
    """
    Quello che costa calcolare e, mentre la finestra è aperta, non cambia, perché il mondo non avanza: il
    punteggio di classe di ogni giocatore, da cui vengono livello e codice, il valore di mercato del giorno,
    lo stipendio che chiede e l'ingaggio che chiede a una polisportiva. Si calcola alla prima richiesta e si
    tiene per la durata della finestra; dopo un'offerta riuscita dimentica chi ha firmato, perché il
    contratto nuovo cambia il suo valore di mercato.
    """

    def __init__(self, mondo):
        self.oggi = mondo.datetime_corrente_simulazione
        self._punteggi = {}
        self._mercato = {}
        self._stipendi = {}
        self._ingaggi = {}

    def punteggio(self, g):
        valore = self._punteggi.get(g.id)
        if valore is None:
            valore = self._punteggi[g.id] = modulo_classe.punteggio(g)
        return valore

    def livello(self, g):
        """Il livello della classe del giocatore, da 1 per A1 a 100 per K0: quello di classe.classe."""
        return modulo_classe.livello(self.punteggio(g))

    def codice(self, g):
        """Il codice della classe del giocatore, come I1."""
        return modulo_classe.codice(self.livello(g))

    def valore_di_mercato(self, g):
        valore = self._mercato.get(g.id)
        if valore is None:
            valore = self._mercato[g.id] = valore_di_mercato(g, self.oggi)
        return valore

    def stipendio(self, g):
        valore = self._stipendi.get(g.id)
        if valore is None:
            valore = self._stipendi[g.id] = stipendio(g)
        return valore

    def ingaggio(self, g, poli):
        """L'ingaggio che il giocatore chiede alla polisportiva, che dipende dalla sua gloria: anche lei non cambia a finestra aperta."""
        chiave = (g.id, poli.nome, poli.gloria)
        valore = self._ingaggi.get(chiave)
        if valore is None:
            valore = self._ingaggi[chiave] = ingaggio_richiesto(g, poli)
        return valore

    def dimentica(self, *giocatori):
        """Dimentica quello che si sa dei giocatori dati, dopo un'offerta riuscita: alla prossima richiesta si ricalcola."""
        numeri = {g.id for g in giocatori}
        for memoria in (self._punteggi, self._mercato, self._stipendi):
            for gid in numeri:
                memoria.pop(gid, None)
        for chiave in [chiave for chiave in self._ingaggi if chiave[0] in numeri]:
            del self._ingaggi[chiave]


@dataclass(slots=True)
class Riga:
    """
    Una persona trovata dalla finestra. Lo stato è LIBERO, IN_VENDITA da una polisportiva che non è tua,
    DEL_COMPUTER, TUO, RITIRATO o USCITO di scena; per gli allenatori LIBERO, DEL_COMPUTER o TUO. La
    polisportiva è il suo club, che è anche chi la vende, e di_chi dice di chi è. Il costo è quanto costa
    averla, None se non si può avere o non si sa: l'ingaggio chiesto alla polisportiva attiva da un libero, il
    prezzo da chi è in vendita, anche da un'altra tua polisportiva, il valore di mercato di un tesserato del
    computer, che fa da riferimento. Lo stipendio è quello che chiede oggi, per chi firmerebbe un contratto
    nuovo, quello del contratto per i tuoi, None per i ritirati; per gli allenatori quello chiesto da capo.
    """
    persona: object
    stato: str
    polisportiva: object = None
    di_chi: str | None = None
    prezzo: int | None = None
    costo: int | None = None
    stipendio: int | None = None
    allenatore: bool = False

    @property
    def numero(self):
        """Il numero della persona: l'ID del giocatore, il numero dell'allenatore."""
        return self.persona.numero if self.allenatore else self.persona.id


def _prova_del_nome(testo, numero):
    """Come in SceltaGiocatore: le cifre cercano il numero dall'inizio, il resto una parte di nome e cognome, senza badare alle maiuscole."""
    cercato = _testo(testo).casefold()
    if cercato.isdigit():
        return lambda r: str(numero(r.persona)).startswith(cercato)
    return lambda r: cercato in f"{r.persona.nome} {r.persona.cognome}".casefold()


def _prova_del_luogo(filtri):
    """La prova di regione, provincia e comune, sul comune di provenienza della persona."""
    comuni = luoghi.comuni_che_contengono(filtri.comune) if _testo(filtri.comune) else None
    provincia, regione = filtri.provincia, filtri.regione

    def nel_luogo(r):
        luogo = r.persona.luogo
        if comuni is not None and luogo not in comuni:
            return False
        if provincia or regione:
            dove = luoghi.provincia_e_regione(luogo)
            if dove is None or (provincia and dove[0] != provincia) or (regione and dove[1] != regione):
                return False
        return True

    return nel_luogo


def _prove_comuni(filtri, eta_in_giorni, numero):
    """Le prove dei filtri che contano per tutti: nome, sesso, età, luogo, polisportiva e mesi di contratto."""
    prove = []
    if _testo(filtri.nome):
        prove.append(_prova_del_nome(filtri.nome, numero))
    if filtri.sesso:
        prove.append(lambda r: r.persona.sesso == filtri.sesso)
    # L'età conta gli anni interi, compreso quello scritto: fino a 20 anni vuol dire meno di 21.
    if filtri.eta_massima:
        limite = (filtri.eta_massima + 1) * ANNO_SIMULAZIONE_GIORNI
        prove.append(lambda r: eta_in_giorni(r.persona) < limite)
    if filtri.eta_minima:
        minimo = filtri.eta_minima * ANNO_SIMULAZIONE_GIORNI
        prove.append(lambda r: eta_in_giorni(r.persona) >= minimo)
    if filtri.regione or filtri.provincia or _testo(filtri.comune):
        prove.append(_prova_del_luogo(filtri))
    if _testo(filtri.polisportiva):
        club = _testo(filtri.polisportiva).casefold()
        prove.append(lambda r: r.polisportiva is not None and club in r.polisportiva.nome.casefold())
    return prove


def _prove_dei_giocatori(mondo, filtri, memoria, attiva):
    """Le prove dei filtri dei giocatori, le più leggere per prime: la classe, che la prima volta si calcola, per ultima."""
    oggi = mondo.datetime_corrente_simulazione
    prove = _prove_comuni(filtri, lambda g: g.eta, lambda g: g.id)
    if filtri.mesi_contratto_massimi:
        prove.append(lambda r: contratti.mesi_al_termine(r.persona, oggi) <= filtri.mesi_contratto_massimi)
    if filtri.disponibili_oggi:
        prove.append(lambda r: r.stato not in (RITIRATO, USCITO) and r.persona.puo_giocare_amichevole(oggi))
    for tratto, voluto in filtri.tratti.items():
        prove.append(lambda r, tratto=tratto, voluto=voluto: bool(ricerca.leggi_criterio(tratto, r.persona)) == voluto)
    if filtri.indole:
        prove.append(lambda r: r.persona.indole == filtri.indole)
    if filtri.valore_minimo:
        prove.append(lambda r: r.persona.indice_collettivo_valore >= filtri.valore_minimo)
    # Chi non ha uno stipendio o un costo, come un ritirato, non c'entra con quei limiti, e resta.
    if filtri.stipendio_massimo:
        prove.append(lambda r: r.stipendio is None or r.stipendio <= filtri.stipendio_massimo)
    if filtri.costo_massimo and attiva is not None:
        prove.append(lambda r: r.costo is None or r.costo <= filtri.costo_massimo)
    if filtri.senza_acciacchi:
        prove.append(lambda r: not r.persona.infortunato and infortuni.calo_acciacco(r.persona, oggi) <= 0)
    if filtri.solo_nuovi:
        nuovi = set(mondo.nuovi_giocatori_sessione)
        prove.append(lambda r: r.persona.id in nuovi)
    if filtri.solo_ritirati_che_allenano:
        allenano = {a.giocatore_id for a in mondo.allenatori.values() if a.tipo == staff.EX}
        prove.append(lambda r: r.stato == RITIRATO and r.persona.id in allenano)
    for criterio, condizione, valore in filtri.condizioni:
        condizione_del_giocatore = ricerca.prova(criterio, condizione, valore, oggi)
        prove.append(lambda r, prova=condizione_del_giocatore: prova(r.persona))
    if filtri.classe_migliore:
        prove.append(lambda r: memoria.livello(r.persona) <= filtri.classe_migliore)
    if filtri.classe_peggiore:
        prove.append(lambda r: memoria.livello(r.persona) >= filtri.classe_peggiore)
    return prove


def _candidati_giocatori(mondo, filtri, memoria, attiva):
    """
    Le righe dei giocatori delle caselle spuntate, prima dei filtri. Chi è in vendita viene dalle liste
    in_vendita delle polisportive, senza scorrere i tesserati; i tesserati del computer e i tuoi dalle rose;
    liberi, ritirati e usciti di scena da un giro sul mondo. Un giocatore compare una volta sola.
    """
    giocatori = mondo.giocatori
    morti = mondo._ids_morti_processati_sessione
    righe = []
    visti = set()
    if filtri.in_vendita:
        for club in mondo.polisportive.values():
            chi = di_chi(mondo, club)
            if chi in TUE:
                continue
            for gid, prezzo in club.in_vendita.items():
                g = giocatori.get(gid)
                if g is None or gid in morti or g.ritirato or g.appartenenza != club.nome:
                    continue
                righe.append(Riga(g, IN_VENDITA, club, chi, prezzo, prezzo, memoria.stipendio(g)))
                visti.add(gid)
    if filtri.del_computer or filtri.tuoi:
        for club in mondo.polisportive.values():
            chi = di_chi(mondo, club)
            if not ((chi in TUE and filtri.tuoi) or (chi == DEL_COMPUTER and filtri.del_computer)):
                continue
            for gid in club.tesserati:
                g = giocatori.get(gid)
                if g is None or gid in visti or gid in morti or g.ritirato:
                    continue
                prezzo = club.in_vendita.get(gid)
                if chi in TUE:
                    # Da un'altra tua polisportiva oggi si compra al prezzo di vendita; dalla attiva no, è già sua.
                    costo = prezzo if chi == TUA_ALTRA else None
                    righe.append(Riga(g, TUO, club, chi, prezzo, costo, stipendio_pagato(g)))
                elif prezzo is not None:
                    righe.append(Riga(g, IN_VENDITA, club, chi, prezzo, prezzo, memoria.stipendio(g)))
                else:
                    righe.append(Riga(g, DEL_COMPUTER, club, chi, None, memoria.valore_di_mercato(g), memoria.stipendio(g)))
    if filtri.liberi or filtri.ritirati or filtri.comprendi_usciti:
        for gid, g in giocatori.items():
            if gid in morti:
                if filtri.comprendi_usciti:
                    righe.append(Riga(g, USCITO))
            elif g.ritirato:
                if filtri.ritirati:
                    righe.append(Riga(g, RITIRATO))
            elif g.appartenenza == "*" and filtri.liberi:
                righe.append(Riga(g, LIBERO, costo=memoria.ingaggio(g, attiva) if attiva is not None else None, stipendio=memoria.stipendio(g)))
    return righe


def _chiave_dei_giocatori(ordine, memoria, oggi):
    """La chiave dell'ordine dei giocatori: a parità decide il numero; chi non ha il dato dell'ordine va in fondo."""
    if ordine in CARATTERISTICHE:
        return lambda r: (-ricerca.leggi_criterio(ordine, r.persona), r.persona.id)
    giorno = oggi.date()
    chiavi = {
        "valore_alto": lambda r: (-r.persona.indice_collettivo_valore, r.persona.id),
        "valore_basso": lambda r: (r.persona.indice_collettivo_valore, r.persona.id),
        "classe": lambda r: (-memoria.punteggio(r.persona), r.persona.id),
        "eta_giovane": lambda r: (r.persona.eta, r.persona.id),
        "eta_anziano": lambda r: (-r.persona.eta, r.persona.id),
        "costo_basso": lambda r: (r.costo is None, r.costo or 0, r.persona.id),
        "costo_alto": lambda r: (r.costo is None, -(r.costo or 0), r.persona.id),
        "euro_per_punto": lambda r: (r.costo is None, euro_per_punto(r) or 0.0, r.persona.id),
        "prezzo_sul_mercato": lambda r: (r.costo is None, prezzo_sul_mercato(r, memoria) or 0.0, r.persona.id),
        "stipendio_basso": lambda r: (r.stipendio is None, r.stipendio or 0, r.persona.id),
        # Per i punti decidono ori, argenti e bronzi, come nella classifica nazionale, e soltanto dopo il numero.
        "punti_nazionali": lambda r: (-r.persona.punti_mondiali, -r.persona.ori, -r.persona.argenti, -r.persona.bronzi, r.persona.id),
        "punti_anno": lambda r: (-palmares.punti_dell_anno(r.persona, giorno), r.persona.id),
        "esperienza": lambda r: (-r.persona.esperienza, r.persona.id),
        "ambizione": lambda r: (-r.persona.ambizione, r.persona.id),
        "punti_allenamento": lambda r: (-r.persona.punti_allenamento, r.persona.id),
        "mesi_contratto": lambda r: (not contratti.ha_contratto(r.persona), contratti.mesi_al_termine(r.persona, oggi), r.persona.id),
        "numero": lambda r: r.persona.id,
    }
    return chiavi[ordine]


def euro_per_punto(r):
    """Quanti euro costa la riga per punto di valore, None se non ha un costo."""
    if r.costo is None:
        return None
    return r.costo / max(r.persona.indice_collettivo_valore, 0.1)


def prezzo_sul_mercato(r, memoria):
    """Il costo della riga diviso il valore di mercato del giocatore, None se non ha un costo: 0,8 è l'80%."""
    if r.costo is None:
        return None
    return r.costo / max(1, memoria.valore_di_mercato(r.persona))


def _giocatori(mondo, filtri, memoria):
    attiva = mondo.miapolisportiva_attiva
    prove = _prove_dei_giocatori(mondo, filtri, memoria, attiva)
    righe = [r for r in _candidati_giocatori(mondo, filtri, memoria, attiva) if all(prova(r) for prova in prove)]
    righe.sort(key=_chiave_dei_giocatori(filtri.ordine, memoria, mondo.datetime_corrente_simulazione))
    return righe


def _allenatori(mondo, filtri):
    """Gli allenatori delle caselle spuntate che passano i filtri, nell'ordine scelto: a parità decide il numero."""
    oggi = mondo.datetime_corrente_simulazione
    attiva = mondo.miapolisportiva_attiva
    prove = _prove_comuni(filtri, lambda a: a.eta(oggi), lambda a: a.numero)
    if filtri.mesi_contratto_massimi:
        prove.append(lambda r: contratti.mesi_al_termine(r.persona, oggi) <= filtri.mesi_contratto_massimi)
    if filtri.classe_migliore:
        prove.append(lambda r: r.persona.livello <= filtri.classe_migliore)
    if filtri.classe_peggiore:
        prove.append(lambda r: r.persona.livello >= filtri.classe_peggiore)
    if filtri.tipo_allenatore:
        prove.append(lambda r: r.persona.tipo == filtri.tipo_allenatore)
    if filtri.visus:
        prove.append(lambda r: r.persona.visus == filtri.visus)
    if filtri.posto_attuale:
        prove.append(lambda r: r.persona.ruolo == filtri.posto_attuale)
    if filtri.stipendio_capo_massimo:
        prove.append(lambda r: r.stipendio <= filtri.stipendio_capo_massimo)
    if filtri.senza_prelazione_altrui:
        tua = attiva.nome if attiva is not None else None
        prove.append(lambda r: r.persona.prelazione is None or r.persona.prelazione == tua)
    righe = []
    for a in mondo.allenatori.values():
        if a.libero:
            if not filtri.liberi:
                continue
            riga = Riga(a, LIBERO, stipendio=staff.stipendio_richiesto(a, staff.CAPO), allenatore=True)
        else:
            club = mondo.polisportive.get(a.polisportiva)
            chi = di_chi(mondo, club)
            if chi in TUE and filtri.tuoi:
                stato = TUO
            elif chi == DEL_COMPUTER and filtri.del_computer:
                stato = DEL_COMPUTER
            else:
                continue
            riga = Riga(a, stato, club, chi, stipendio=staff.stipendio_richiesto(a, staff.CAPO), allenatore=True)
        if all(prova(riga) for prova in prove):
            righe.append(riga)
    chiavi = {
        "classe": lambda r: (r.persona.livello, r.persona.numero),
        "eta_giovane": lambda r: (r.persona.eta(oggi), r.persona.numero),
        "eta_anziano": lambda r: (-r.persona.eta(oggi), r.persona.numero),
        "stipendio_basso": lambda r: (r.stipendio, r.persona.numero),
        "numero": lambda r: r.persona.numero,
    }
    righe.sort(key=chiavi[filtri.ordine_allenatori])
    return righe


def cerca(mondo, filtri, memoria=None):
    """
    Le righe dei trovati coi filtri dati, nell'ordine scelto: gli allenatori se la casella Allenatori è
    spuntata, altrimenti i giocatori. I filtri che per chi si cerca non contano si ignorano; quelli che si
    escludono a vicenda si applicano tutti, e l'elenco può restare vuoto. La memoria è quella della
    finestra, e senza se ne usa una nuova.
    """
    if filtri.allenatori:
        return _allenatori(mondo, filtri)
    return _giocatori(mondo, filtri, memoria if memoria is not None else Memoria(mondo))


def indice_della_persona(righe, numero, allenatori=False):
    """Dopo un ricalcolo, il posto della stessa persona, cercata per numero: 0 se non c'è più, None se l'elenco è vuoto."""
    if not righe:
        return None
    return next((i for i, r in enumerate(righe) if r.allenatore == allenatori and r.numero == numero), 0)


# Le azioni sulle righe: che cosa si può fare, o perché no. Sono funzioni pure, che non cambiano niente:
# i divieti sono quelli del mondo e delle sfide. Il motivo è la chiave del suono che dice il perché: quelle
# di oggi, e tre nuove della proposta, che aspettano i loro suoni.
Possibile = namedtuple("Possibile", "azione problema motivo")
INGAGGIO = "ingaggio"
ACQUISTO = "acquisto"
OFFERTA_D_ACQUISTO = "offerta_d_acquisto"
INGAGGIO_ALLENATORE = "ingaggio_allenatore"
AMICHEVOLE = "amichevole"
SFIDA = "sfida"
OFFERTA_NON_POSSIBILE = "offerta_non_possibile"
NON_GIOCA_OGGI = "non_gioca_oggi"
CLUB_NON_SFIDABILE = "club_non_sfidabile"
NESSUNA_POLISPORTIVA_ATTIVA = "nessuna_polisportiva_attiva"


def _nome(persona):
    return f"{persona.nome} {persona.cognome}"


def _senza_attiva(cosa):
    return Possibile(None, f"Non hai una polisportiva attiva: {cosa}. Fondane una con Ctrl+N, o sceglila con Ctrl+Maiusc+C.", NESSUNA_POLISPORTIVA_ATTIVA)


def _motivo_dell_offerta(mondo, poli, costo=None):
    """Il motivo di un'offerta che il mondo non permette, nell'ordine in cui controlla: le mosse, la rosa piena, la cassa."""
    if mondo.mosse_rimaste(poli) <= 0:
        return "mosse_finite"
    if len(poli.tesserati) >= poli.maxtesserati:
        return "rosa_piena"
    if costo is not None and costo > poli.cassa:
        return "cassa_insufficiente"
    return OFFERTA_NON_POSSIBILE


def _offerta_all_allenatore(mondo, poli, riga, posto):
    a = riga.persona
    if not a.libero:
        return Possibile(None, f"{_nome(a)} allena già {a.polisportiva}: non si possono fare offerte.", OFFERTA_NON_POSSIBILE)
    if posto is None:
        posto = next((i for i, numero in enumerate(poli.staff) if not numero), None)
        if posto is None:
            return Possibile(INGAGGIO_ALLENATORE, f"Lo staff di {poli.nome} è al completo: per un'offerta serve un posto vuoto.", "staff_posto_occupato")
    if poli.cassa <= 0:
        return Possibile(INGAGGIO_ALLENATORE, f"La cassa di {poli.nome} è vuota.", "cassa_insufficiente")
    problema = mondo.problema_offerta_allenatore(poli, a, posto)
    if problema is None:
        return Possibile(INGAGGIO_ALLENATORE, None, None)
    if mondo.mosse_rimaste(poli) <= 0:
        motivo = "mosse_finite"
    elif 0 <= posto < len(poli.staff) and poli.staff[posto]:
        motivo = "staff_posto_occupato"
    elif a.prelazione is not None and a.prelazione != poli.nome:
        motivo = "allenatore_in_prelazione"
    else:
        motivo = OFFERTA_NON_POSSIBILE
    return Possibile(INGAGGIO_ALLENATORE, problema, motivo)


def offerta_possibile(mondo, poli, riga, posto=None):
    """
    Quale offerta la polisportiva può fare alla persona della riga, o perché no, come Possibile: l'azione,
    il problema, None se l'offerta si può fare, e il motivo. A un libero l'ingaggio; a chi è in vendita,
    anche da un'altra tua polisportiva, l'acquisto al prezzo; a un tesserato del computer l'offerta
    d'acquisto; a un allenatore libero l'ingaggio per il posto dato, o per il primo vuoto. A ritirati,
    usciti di scena, tuoi tesserati non in vendita e allenatori già impiegati non si fanno offerte, e
    l'azione è None. Come nel mercato di oggi, prima del mondo si controlla la cassa vuota.
    """
    if poli is None:
        return _senza_attiva("le offerte le fa la polisportiva attiva")
    if riga.allenatore:
        return _offerta_all_allenatore(mondo, poli, riga, posto)
    g = riga.persona
    if riga.stato == USCITO:
        return Possibile(None, f"{_nome(g)} è {accorda(g.sesso, 'uscito')} di scena: non si possono fare offerte.", OFFERTA_NON_POSSIBILE)
    if riga.stato == RITIRATO:
        return Possibile(None, f"{_nome(g)} si è {accorda(g.sesso, 'ritirato')} dall'attività: non si possono fare offerte.", OFFERTA_NON_POSSIBILE)
    if riga.stato == TUO and (riga.prezzo is None or riga.polisportiva is poli):
        return Possibile(None, f"{_nome(g)} è già {accorda(g.sesso, 'tuo')}: è {accorda(g.sesso, 'tesserato')} con {riga.polisportiva.nome}.",
                         OFFERTA_NON_POSSIBILE)
    if riga.stato == LIBERO:
        azione, problema, costo = INGAGGIO, mondo.problema_offerta(poli, g), None
    elif riga.stato in (IN_VENDITA, TUO):
        azione, problema, costo = ACQUISTO, mondo.problema_acquisto(poli, g), riga.prezzo
    else:
        azione, problema, costo = OFFERTA_D_ACQUISTO, mondo.problema_offerta_d_acquisto(poli, g), None
    if poli.cassa <= 0:
        return Possibile(azione, f"La cassa di {poli.nome} è vuota.", "cassa_insufficiente")
    if problema is None:
        return Possibile(azione, None, None)
    return Possibile(azione, problema, _motivo_dell_offerta(mondo, poli, costo))


def amichevole_possibile(mondo, poli, riga):
    """
    Se oggi si può giocare un'amichevole contro la persona della riga, o perché no, come Possibile: ci vuole
    la polisportiva attiva, e un giocatore che oggi può giocare. Il tuo giocatore lo si sceglie dopo, fra
    tuoi_per_l_amichevole; se non ce n'è nessuno, il testo è testi.nessuno_per_l_amichevole, che vuole l'ora vera.
    """
    if poli is None:
        return _senza_attiva("l'amichevole la gioca un tesserato della polisportiva attiva")
    p = riga.persona
    if riga.allenatore:
        chi = "un'allenatrice" if p.sesso == "f" else "un allenatore"
        return Possibile(None, f"{_nome(p)} è {chi}: le amichevoli le giocano i giocatori.", NON_GIOCA_OGGI)
    oggi = mondo.datetime_corrente_simulazione
    if riga.stato == USCITO:
        return Possibile(None, f"{_nome(p)} è {accorda(p.sesso, 'uscito')} di scena: non gioca più.", NON_GIOCA_OGGI)
    if p.ritirato:
        return Possibile(None, f"{_nome(p)} si è {accorda(p.sesso, 'ritirato')} dall'attività: non gioca più.", NON_GIOCA_OGGI)
    if not p.puo_giocare:
        return Possibile(None, f"Oggi {_nome(p)} non può giocare: è {accorda(p.sesso, 'infortunato')}.", NON_GIOCA_OGGI)
    if p.ha_un_impegno(oggi):
        return Possibile(None, f"Oggi {_nome(p)} ha già giocato {mondo.descrivi_impegno(p)}: ognuno gioca al massimo un incontro per giorno simulato.",
                         NON_GIOCA_OGGI)
    return Possibile(AMICHEVOLE, None, None)


def tuoi_per_l_amichevole(mondo, poli, avversario):
    """I tesserati della polisportiva che oggi possono giocare un'amichevole contro l'avversario, lui escluso, in ordine di numero."""
    oggi = mondo.datetime_corrente_simulazione
    morti = mondo._ids_morti_processati_sessione
    tuoi = (mondo.giocatori.get(gid) for gid in poli.tesserati if gid not in morti)
    return sorted((g for g in tuoi if g is not None and g is not avversario and g.puo_giocare_amichevole(oggi)), key=lambda g: g.id)


def sfida_possibile(mondo, poli, riga):
    """
    Se oggi la polisportiva può sfidare il club della persona della riga, o perché no, come Possibile: il club
    è quello di un tesserato del computer, o di un allenatore che allena per il computer. I divieti sono quelli
    di sfide.problema_bersaglio; il motivo dice se le sfide sono finite o se il club non si può sfidare.
    """
    if poli is None:
        return _senza_attiva("le sfide le lancia la polisportiva attiva")
    club = riga.polisportiva if riga.stato in (DEL_COMPUTER, IN_VENDITA) else None
    problema = sfide.problema_bersaglio(mondo, poli, club.nome if club is not None else None)
    if problema is None:
        return Possibile(SFIDA, None, None)
    finite = sfide.tua(poli) and sfide.disponibili(mondo, poli) <= 0
    return Possibile(SFIDA, problema, "nessuna_sfida_da_lanciare" if finite else CLUB_NON_SFIDABILE)
