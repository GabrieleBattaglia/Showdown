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
d'ingresso, Ctrl+K, Ctrl+Maiusc+G, Ctrl+F e Ctrl+O, vive nel mondo, scelta di Gabriele, e col formato 10
dell'archivio si salva con lui: qui ogni campo si scrive e, alla lettura, si controlla. Con le verifiche dello stesso giorno lo stato di una porta fa il giro del salvataggio, nel JSON e
nei controlli della lettura, prima di entrare nel mondo e prima di essere scritto: il mondo non scrive mai uno
stato che poi rifiuterebbe. Nel prezzo sul valore di mercato i tesserati del computer, che hanno per costo
soltanto il valore di riferimento, vanno in fondo invece di costare sempre il 100%; e chi non ha il dato di un
limite, come un libero coi mesi di contratto, resta nell'elenco in modo dichiarato, e Filtri attivi lo dice,
come dice chi va in fondo anche negli ordini per stipendio e per mesi di contratto. È di Gabriele Battaglia
(IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Lo stesso giorno, con le scelte di Gabriele dopo la prova del prototipo, i preset dei filtri: i suoi, con un nome e
un numero che non cambia; le ricerche pronte diventano i dodici preset di serie, che non si cancellano, e Torna ai tuoi
filtri lascia il posto alla voce Filtri attuali, non salvati, in cima alla casella; ogni porta d'ingresso ricorda la
voce scelta e i filtri attuali, e Assumi apre sempre sugli allenatori liberi. Il nome, il salvataggio con la
sostituzione, la rinomina, l'eliminazione e lo spostamento dei preset stanno qui, e passano nel mondo, che li salva
nello stesso formato 10. I campi dei filtri si dividono in tre gruppi, uno per scheda della finestra. La scrittura
resta severa, e la lettura diventa indulgente: preset e porte si leggono separati, un preset non si toglie ma si
ripara, e quello che non si legge torna ai filtri di serie con un avviso, che l'archivio scrive nel registro degli
errori col dato originale, invece di far rifiutare il mondo. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude
Opus 5.5, UltraCode).
Lo stesso giorno, col passo della finestra: dopo un esito la scelta resta sulla stessa persona o, se non c'è più, sullo
stesso posto, col ripiego di indice_della_persona; e la sfida al club che oggi ha già rifiutato ha il motivo col suono
del lancio delle sfide, sfida_gia_rifiutata_oggi. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Lo stesso giorno, coi collegamenti della finestra, esce il mercato di prima, coi candidati, la scelta Mostra e i suoi
quattro ordini: lo ha sostituito la finestra. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Lo stesso giorno, con le verifiche della finestra: i massimi dei numeri dei filtri stanno qui, in MASSIMI_DEI_NUMERI, e
valgono per le caselle della finestra e per la lettura, che prima accettava qualunque numero; gli avvisi della lettura
citano i dati come il JSON del registro, sempre fra virgolette, e non più col repr di Python, a volte fra apici; gli
allenatori ordinati per classe, a parità di classe, vanno dal più giovane, come nel mercato degli allenatori di prima.
È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import copy
import json
import math
import unicodedata
from collections import namedtuple
from dataclasses import dataclass, field, fields

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
    INDOLI,
)
from economia import ingaggio_richiesto, stipendio, stipendio_pagato, valore_di_mercato
from utilita import accorda

# La finestra unica Mercato e ricerca, issue 8 e decisione D36.

# I tre stati di chi si può avere dal mercato: libero, in vendita da altri, tesserato del computer.
LIBERO = "libero"
IN_VENDITA = "in_vendita"
DEL_COMPUTER = "del_computer"

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
# I campi dei filtri in tre gruppi, uno per scheda della finestra, nell'ordine dei controlli: la scheda Filtri, coi
# controlli più usati e, accanto ai loro opposti, la classe peggiore e l'età minima; Altri filtri; i Filtri degli
# allenatori. Insieme sono tutti i campi, ciascuno una volta sola; le linguette delle ultime due schede dicono quanti
# dei loro sono impostati, e Azzera questi filtri li rimette a nessun filtro.
CAMPI_FILTRI = ("nome", "allenatori", "liberi", "in_vendita", "del_computer", "tuoi", "ritirati", "sesso", "classe_migliore", "classe_peggiore",
                "eta_massima", "eta_minima", "costo_massimo", "disponibili_oggi", "ordine", "ordine_allenatori")
CAMPI_ALTRI_FILTRI = ("regione", "provincia", "comune", "polisportiva", "tratti", "indole", "valore_minimo", "stipendio_massimo", "mesi_contratto_massimi",
                      "senza_acciacchi", "solo_ritirati_che_allenano", "solo_nuovi", "comprendi_usciti", "condizioni")
CAMPI_FILTRI_ALLENATORI = ("tipo_allenatore", "visus", "posto_attuale", "stipendio_capo_massimo", "senza_prelazione_altrui")
# I campi che contano soltanto per i giocatori, e quelli che contano soltanto per gli allenatori: agli
# altri non si applicano, e Filtri attivi dice che non contano.
CAMPI_SOLO_GIOCATORI = ("in_vendita", "ritirati", "costo_massimo", "disponibili_oggi", "tratti", "indole", "valore_minimo", "stipendio_massimo",
                        "senza_acciacchi", "solo_ritirati_che_allenano", "solo_nuovi", "comprendi_usciti", "condizioni")
CAMPI_SOLO_ALLENATORI = ("tipo_allenatore", "visus", "posto_attuale", "stipendio_capo_massimo", "senza_prelazione_altrui")
# Il massimo di ogni numero dei filtri: quello delle caselle della finestra, e quello che la lettura accetta.
MASSIMI_DEI_NUMERI = {"eta_massima": 120, "eta_minima": 120, "costo_massimo": 100_000_000, "valore_minimo": 100_000, "stipendio_massimo": 10_000_000,
                      "mesi_contratto_massimi": 240, "stipendio_capo_massimo": 10_000_000}


def _testo(valore):
    """Un testo di un campo così come conta: senza gli spazi in testa e in coda."""
    return valore.strip()


def impostato(filtri, campo):
    """Vero se il campo dei filtri non è al suo valore di nessun filtro; un testo di soli spazi non conta."""
    valore = getattr(filtri, campo)
    if isinstance(valore, str) and campo not in ("ordine", "ordine_allenatori"):
        return bool(_testo(valore))
    return valore != getattr(_PREDEFINITI, campo)


def quanti_impostati(filtri, campi):
    """Quanti filtri del gruppo di campi sono impostati, per la linguetta della sua scheda: ogni tratto e ogni condizione contano uno."""
    quanti = 0
    for campo in campi:
        if campo in ("tratti", "condizioni"):
            quanti += len(getattr(filtri, campo))
        elif impostato(filtri, campo):
            quanti += 1
    return quanti


def azzera(filtri, campi):
    """I filtri coi campi del gruppo a nessun filtro, come Azzera questi filtri: gli altri restano, e i filtri dati non cambiano."""
    nuovi = filtri.copia()
    for campo in campi:
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
    Chi non ha il dato dell'ordine scelto e va in fondo, come elenco dei gruppi spuntati, nell'ordine delle
    caselle. Negli ordini che seguono il costo i liberi senza polisportiva attiva, i tuoi tesserati che non sono
    in vendita da un'altra tua polisportiva, i ritirati e gli usciti di scena; nel prezzo sul valore di mercato
    anche i tesserati del computer, il cui prezzo vero è nascosto, decisione D23. Nell'ordine per stipendio i
    ritirati e gli usciti; nei mesi di contratto chi non ha un contratto, i liberi, i ritirati e gli usciti. Un
    elenco vuoto negli altri ordini e per gli allenatori, che hanno tutti lo stipendio chiesto da capo.
    """
    if filtri.allenatori:
        return []
    ritirati, usciti = ("ritirati", filtri.ritirati), ("usciti", filtri.comprendi_usciti)
    if filtri.ordine in ORDINI_DEL_COSTO:
        gruppi = (("liberi", filtri.liberi and attiva is None), ("del_computer", filtri.del_computer and filtri.ordine == "prezzo_sul_mercato"),
                  ("tuoi", filtri.tuoi), ritirati, usciti)
    elif filtri.ordine == "stipendio_basso":
        gruppi = (ritirati, usciti)
    elif filtri.ordine == "mesi_contratto":
        gruppi = (("liberi", filtri.liberi), ritirati, usciti)
    else:
        return []
    return [gruppo for gruppo, c in gruppi if c]


def restano(filtri, attiva=None):
    """
    I limiti impostati che non toccano chi non ha il loro dato: chi non ha un costo, uno stipendio o un
    contratto, con quel limite non c'entra e resta nell'elenco, invece di svuotarlo, come per i filtri che non
    contano. Coppie del campo e dei gruppi spuntati che restano, nell'ordine delle caselle: per il costo
    massimo, che conta soltanto con la polisportiva attiva, i tuoi tesserati che non sono in vendita da
    un'altra tua polisportiva, i ritirati e gli usciti di scena; per lo stipendio massimo i ritirati e gli
    usciti; per i mesi di contratto i liberi, i ritirati e gli usciti, e fra gli allenatori i liberi.
    """
    if filtri.allenatori:
        return [("mesi_contratto_massimi", ["liberi"])] if filtri.mesi_contratto_massimi and filtri.liberi else []
    ritirati, usciti = ("ritirati", filtri.ritirati), ("usciti", filtri.comprendi_usciti)
    limiti = (("costo_massimo", filtri.costo_massimo and attiva is not None, (("tuoi", filtri.tuoi), ritirati, usciti)),
              ("stipendio_massimo", filtri.stipendio_massimo, (ritirati, usciti)),
              ("mesi_contratto_massimi", filtri.mesi_contratto_massimi, (("liberi", filtri.liberi), ritirati, usciti)))
    trovati = []
    for campo, conta, gruppi in limiti:
        chi = [gruppo for gruppo, c in gruppi if c]
        if conta and chi:
            trovati.append((campo, chi))
    return trovati


# I preset di serie: le ricerche pronte della proposta, nella casella dei preset dopo quelli di Gabriele, e non si
# cancellano. Ognuno imposta le caselle, i filtri, l'ordine e il nome, e tutto il resto a nessun filtro. Torna ai tuoi
# filtri, la tredicesima ricerca pronta, lascia il posto alla voce Filtri attuali, non salvati, in cima alla casella.
PRESET_DI_SERIE = (
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
_FILTRI_DI_SERIE = {
    "mercato": {"liberi": True, "in_vendita": True, "ordine": "valore_alto"},
    "tutti_in_attivita": {**_IN_ATTIVITA, "ordine": "numero"},
    "piu_forti": {**_IN_ATTIVITA, "ordine": "valore_alto"},
    "giovani_migliori": {**_IN_ATTIVITA, "eta_massima": ETA_DEI_GIOVANI, "ordine": "valore_alto"},
    "liberi_convenienti": {"liberi": True, "ordine": "euro_per_punto"},
    "affari_in_vendita": {"in_vendita": True, "ordine": "prezzo_sul_mercato"},
    "avversari_amichevole": {**_IN_ATTIVITA, "disponibili_oggi": True, "ordine": "classe"},
    "piu_titolati": {**_IN_ATTIVITA, "ordine": "punti_nazionali"},
    "allenatori_liberi": {"allenatori": True, "liberi": True, "ordine_allenatori": "classe"},
    # I capi e gli assistenti migliori guardano soltanto chi ha quel posto: niente liberi, scelta di Gabriele.
    "capi_migliori": {**_STAFF_IMPIEGATO, "posto_attuale": staff.CAPO},
    "assistenti_migliori": {**_STAFF_IMPIEGATO, "posto_attuale": staff.ASSISTENTE},
    "nuovi_arrivati": {**_IN_ATTIVITA, "solo_nuovi": True, "ordine": "valore_alto"},
}
# I filtri che prende un preset di Gabriele che non si legge: quelli di Tutti in attività, senza filtri.
SERIE_DEI_FILTRI_ILLEGGIBILI = "tutti_in_attivita"
# Le porte d'ingresso della finestra, ciascuna col suo preset di serie: Ctrl+K, Ctrl+Maiusc+G, Ctrl+F e Ctrl+O, coi
# nomi per esteso degli avvisi del registro. Assumi dello staff non è una porta: apre sempre sugli allenatori liberi,
# filtri_di_serie("allenatori_liberi"), col posto già scelto, e non ricorda niente.
PORTE = ("mercato", "allenatori", "ricerca", "amichevole")
PRESET_DELLA_PORTA = {"mercato": "mercato", "allenatori": "allenatori_liberi", "ricerca": "tutti_in_attivita", "amichevole": "avversari_amichevole"}
NOMI_DELLE_PORTE = {"mercato": "Mercato, Ctrl+K", "allenatori": "Mercato degli allenatori, Ctrl+Maiusc+G", "ricerca": "Cerca giocatori, Ctrl+F",
                    "amichevole": "Amichevole, Ctrl+O"}
# Le due voci della casella che non sono preset: in cima i filtri fatti a mano, in fondo Salva filtri, che si apre
# soltanto con Invio. Le voci della casella, coi loro tipi: la scelta è None per le due voci, il numero per un preset
# di Gabriele, la chiave per un preset di serie.
NOME_DEI_FILTRI_ATTUALI = "Filtri attuali, non salvati"
NOME_DI_SALVA_FILTRI = "Salva filtri..."
VOCE_ATTUALI = "attuali"
VOCE_TUA = "tua"
VOCE_DI_SERIE = "di_serie"
VOCE_SALVA = "salva"
Voce = namedtuple("Voce", "tipo scelta nome")
# Il nome di un preset di Gabriele: da 1 a 50 caratteri, senza gli spazi in testa e in coda.
LUNGHEZZA_MASSIMA_DEL_NOME = 50
_NOMI_RISERVATI = frozenset(nome.casefold() for nome in (NOME_DEI_FILTRI_ATTUALI, NOME_DI_SALVA_FILTRI, *dict(PRESET_DI_SERIE).values()))


def nome_del_preset_di_serie(chiave):
    return dict(PRESET_DI_SERIE)[chiave]


def filtri_di_serie(chiave):
    """I filtri di un preset di serie, tutto il resto a nessun filtro; KeyError per una chiave che non c'è."""
    return Filtri(**copy.deepcopy(_FILTRI_DI_SERIE[chiave]))


@dataclass
class Preset:
    """Un preset di Gabriele: il numero, che non cambia mai ed è quello che le porte ricordano; il nome della casella; i filtri."""
    numero: int
    nome: str
    filtri: Filtri


@dataclass
class StatoDellaPorta:
    """
    Quello che una porta d'ingresso ricorda della finestra: la voce della casella scelta, None per Filtri attuali, non
    salvati, la chiave di un preset di serie o il numero di un preset di Gabriele; e i filtri attuali, quelli fatti a
    mano, che la voce in cima alla casella tiene anche mentre si scorrono i preset.
    """
    scelta: str | int | None
    attuali: Filtri

    def copia(self):
        return copy.deepcopy(self)


@dataclass
class FiltriDiRicerca:
    """
    I filtri della finestra Mercato e ricerca che il mondo ricorda e salva: i preset di Gabriele, nell'ordine della
    casella; il numero del prossimo preset, che non torna mai indietro, così il numero di un preset eliminato non passa
    a un altro, e una porta che lo ricordava non riapre il preset sbagliato; lo stato di ogni porta d'ingresso. Col
    magnate di D35, nel formato 11, ogni magnate avrà il suo.
    """
    preset: list = field(default_factory=list)
    prossimo_preset: int = 1
    porte: dict = field(default_factory=dict)

    def copia(self):
        return copy.deepcopy(self)


def stato_di_serie(porta):
    """Lo stato di una porta mai usata, e di un mondo che arriva dal formato 9: il suo preset di serie, coi suoi filtri come filtri attuali."""
    chiave = PRESET_DELLA_PORTA[porta]
    return StatoDellaPorta(chiave, filtri_di_serie(chiave))


def filtri_di_ricerca_di_serie():
    """I filtri di ricerca di un mondo nuovo: nessun preset, il primo col numero 1, e ogni porta sul suo preset di serie."""
    return FiltriDiRicerca([], 1, {porta: stato_di_serie(porta) for porta in PORTE})


def filtri_di_ricerca_del_mondo(mondo):
    """
    Una copia dei filtri di ricerca del mondo, che la finestra cambia senza toccarlo: preset e porte passano nel mondo
    con ricorda_i_preset e ricorda_la_porta. Il mondo li tiene a None finché non servono, e allora valgono quelli di serie.
    """
    filtri_di_ricerca = mondo.filtri_di_ricerca
    return filtri_di_ricerca.copia() if filtri_di_ricerca is not None else filtri_di_ricerca_di_serie()


def stato_della_porta(mondo, porta):
    """Una copia dello stato della porta che il mondo ricorda, o di quello di serie; KeyError per una porta che non esiste."""
    if porta not in PORTE:
        raise KeyError(porta)
    filtri_di_ricerca = mondo.filtri_di_ricerca
    return filtri_di_ricerca.porte[porta].copia() if filtri_di_ricerca is not None else stato_di_serie(porta)


def _numero_di_preset(valore):
    """Vero per il numero di un preset di Gabriele: un intero da 1 in su, e non vero o falso, che per Python sono 1 e 0."""
    return isinstance(valore, int) and not isinstance(valore, bool) and valore >= 1


def preset_col_numero(filtri_di_ricerca, numero):
    """Il preset di Gabriele con quel numero, o None."""
    if not _numero_di_preset(numero):
        return None
    return next((p for p in filtri_di_ricerca.preset if p.numero == numero), None)


def preset_col_nome(filtri_di_ricerca, nome):
    """Il preset di Gabriele con quel nome, senza badare alle maiuscole né agli spazi in testa e in coda, o None."""
    cercato = nome.strip().casefold()
    return next((p for p in filtri_di_ricerca.preset if p.nome.casefold() == cercato), None)


def filtri_della_voce(filtri_di_ricerca, scelta, attuali):
    """
    I filtri di una voce della casella, in una copia: i filtri attuali per la voce in cima, scelta None; quelli del
    preset di serie della chiave, o del preset di Gabriele del numero. È anche così che una porta riapre la finestra,
    con la scelta e i filtri attuali del suo stato. KeyError per un preset che non c'è.
    """
    if scelta is None:
        return attuali.copia()
    if _numero_di_preset(scelta):
        preset = preset_col_numero(filtri_di_ricerca, scelta)
        if preset is None:
            raise KeyError(scelta)
        return preset.filtri.copia()
    return filtri_di_serie(scelta)


def voci_della_casella(filtri_di_ricerca):
    """Le voci della casella dei preset, in ordine: Filtri attuali, non salvati; i preset di Gabriele; i preset di serie; Salva filtri."""
    return [Voce(VOCE_ATTUALI, None, NOME_DEI_FILTRI_ATTUALI), *(Voce(VOCE_TUA, p.numero, p.nome) for p in filtri_di_ricerca.preset),
            *(Voce(VOCE_DI_SERIE, chiave, nome) for chiave, nome in PRESET_DI_SERIE), Voce(VOCE_SALVA, None, NOME_DI_SALVA_FILTRI)]


def posto_della_scelta(voci, scelta):
    """Il posto nelle voci della casella della voce scelta: 0 per Filtri attuali, scelta None; None per un preset che fra le voci non c'è."""
    tipo = VOCE_ATTUALI if scelta is None else VOCE_TUA if _numero_di_preset(scelta) else VOCE_DI_SERIE
    return next((posto for posto, voce in enumerate(voci) if voce.tipo == tipo and voce.scelta == scelta), None)


def _con_caratteri_di_controllo(testo):
    """Vero se il testo ha un a capo, una tabulazione o un altro carattere di controllo, che nella casella non si leggerebbe."""
    return any(unicodedata.category(c) in ("Cc", "Zl", "Zp") for c in testo)


def problema_del_nome(filtri_di_ricerca, nome, numero=None):
    """
    Perché il nome non va per un preset di Gabriele, o None se va. Conta senza gli spazi in testa e in coda: da 1 a 50
    caratteri, senza a capo, tabulazioni o altri caratteri di controllo, e, senza badare alle maiuscole, diverso dalle
    voci di serie della casella, cioè i preset di serie, Filtri attuali, non salvati e Salva filtri. Il nome di un tuo
    preset, quando si salva, non è un problema, perché Salva filtri chiede se sostituirne i filtri; lo è quando si
    rinomina il preset del numero dato con il nome di un altro dei tuoi.
    """
    pulito = nome.strip()
    if not 1 <= len(pulito) <= LUNGHEZZA_MASSIMA_DEL_NOME:
        return f"Il nome del preset deve avere da 1 a {LUNGHEZZA_MASSIMA_DEL_NOME} caratteri."
    if _con_caratteri_di_controllo(pulito):
        return "Il nome del preset non può avere a capo, tabulazioni o altri caratteri di controllo."
    if pulito.casefold() in _NOMI_RISERVATI:
        return f"{pulito} è il nome di una voce di serie della casella dei preset: se ne sceglie un altro."
    if numero is not None:
        altro = preset_col_nome(filtri_di_ricerca, pulito)
        if altro is not None and altro.numero != numero:
            return f"Esiste già un preset che si chiama {altro.nome}."
    return None


def _filtri_dopo_il_giro(filtri):
    """I filtri dopo il giro del salvataggio, nel JSON e nei controlli della lettura: quello che si scrive deve rileggersi. ValueError se non va."""
    try:
        dati = json.loads(json.dumps(filtri_a_dizionario(filtri)))
    except (TypeError, ValueError, AttributeError) as e:
        raise ValueError(f"I filtri non si possono scrivere: {e}") from e
    problema = problema_dei_filtri(dati)
    if problema is not None:
        raise ValueError(f"I filtri non sono validi: {problema}")
    return filtri_da_dizionario(dati)


def _preset_dal_numero(filtri_di_ricerca, numero):
    preset = preset_col_numero(filtri_di_ricerca, numero)
    if preset is None:
        raise KeyError(numero)
    return preset


def salva_preset(filtri_di_ricerca, nome, filtri):
    """
    Salva i filtri come preset di Gabriele, nei filtri di ricerca della finestra. Se un tuo preset ha già quel nome,
    senza badare alle maiuscole, ne sostituisce i filtri, e quel preset tiene nome, posto e numero: Salva filtri lo ha
    già chiesto, con il No già scelto. Altrimenti un preset nuovo, in fondo ai tuoi, col prossimo numero. Restituisce il
    preset e vero se ha sostituito. ValueError, col perché, se il nome non va o se i filtri non si rileggerebbero.
    """
    problema = problema_del_nome(filtri_di_ricerca, nome)
    if problema is not None:
        raise ValueError(problema)
    salvati = _filtri_dopo_il_giro(filtri)
    esistente = preset_col_nome(filtri_di_ricerca, nome)
    if esistente is not None:
        esistente.filtri = salvati
        return esistente, True
    preset = Preset(filtri_di_ricerca.prossimo_preset, nome.strip(), salvati)
    filtri_di_ricerca.prossimo_preset += 1
    filtri_di_ricerca.preset.append(preset)
    return preset, False


def rinomina_preset(filtri_di_ricerca, numero, nome):
    """Il preset del numero prende il nome nuovo, e tiene posto, numero e filtri; KeyError se non c'è, ValueError, col perché, se il nome non va."""
    preset = _preset_dal_numero(filtri_di_ricerca, numero)
    problema = problema_del_nome(filtri_di_ricerca, nome, numero)
    if problema is not None:
        raise ValueError(problema)
    preset.nome = nome.strip()
    return preset


def elimina_preset(filtri_di_ricerca, numero):
    """
    Toglie il preset del numero, e lo restituisce; KeyError se non c'è. Le porte che lo riaprivano tornano al loro
    preset di serie e tengono i filtri attuali; il suo numero non passa più a nessun altro.
    """
    preset = _preset_dal_numero(filtri_di_ricerca, numero)
    filtri_di_ricerca.preset = [p for p in filtri_di_ricerca.preset if p is not preset]
    for porta, stato in list(filtri_di_ricerca.porte.items()):
        if _numero_di_preset(stato.scelta) and stato.scelta == numero:
            filtri_di_ricerca.porte[porta] = StatoDellaPorta(PRESET_DELLA_PORTA[porta], stato.attuali)
    return preset


def sposta_preset(filtri_di_ricerca, numero, verso):
    """Sposta il preset del numero di un posto, su con verso -1 e giù con 1; falso, e niente cambia, se è già al bordo. KeyError se non c'è."""
    if verso not in (-1, 1):
        raise ValueError(f"Un preset si sposta di un posto, su o giù, non di {verso!r}.")
    preset = _preset_dal_numero(filtri_di_ricerca, numero)
    posto = next(i for i, p in enumerate(filtri_di_ricerca.preset) if p is preset)
    nuovo = posto + verso
    if not 0 <= nuovo < len(filtri_di_ricerca.preset):
        return False
    elenco = filtri_di_ricerca.preset
    elenco[posto], elenco[nuovo] = elenco[nuovo], elenco[posto]
    return True


def ricorda_i_preset(mondo, filtri_di_ricerca):
    """
    Il mondo ricorda i preset di Gabriele e il prossimo numero dai filtri di ricerca della finestra, dopo ogni
    operazione sui preset, e li salva con sé; lo stato delle porte resta quello del mondo, salvo le porte che riaprivano
    un preset che non c'è più, che tornano al loro preset di serie. Tutto fa prima il giro del salvataggio: ValueError,
    col perché, se qualcosa non si rileggerebbe, e il mondo resta com'era.
    """
    nuovi = filtri_di_ricerca_del_mondo(mondo)
    nuovi.preset = filtri_di_ricerca.preset
    nuovi.prossimo_preset = filtri_di_ricerca.prossimo_preset
    numeri = {getattr(p, "numero", None) for p in nuovi.preset}
    for porta, stato in list(nuovi.porte.items()):
        if _numero_di_preset(stato.scelta) and stato.scelta not in numeri:
            nuovi.porte[porta] = StatoDellaPorta(PRESET_DELLA_PORTA[porta], stato.attuali)
    mondo.filtri_di_ricerca = _giro_del_salvataggio(nuovi)


def ricorda_la_porta(mondo, porta, stato):
    """
    Il mondo ricorda lo stato della porta, alla chiusura della finestra, e lo salva con sé; KeyError per una porta che
    non esiste. Lo stato fa prima il giro del salvataggio, e il mondo ricorda quello che ne torna: uno stato che la
    lettura dovrebbe riparare, come un sesso vuoto invece di None, un'età con la virgola o un preset che non c'è, dà
    ValueError, col perché, e il mondo resta com'era. Dalla verifica del 24 ottobre 2026: prima entrava, si salvava, e
    al caricamento dopo il mondo intero, file e copia, non si apriva più.
    """
    if porta not in PORTE:
        raise KeyError(porta)
    nuovi = filtri_di_ricerca_del_mondo(mondo)
    nuovi.porte[porta] = stato
    mondo.filtri_di_ricerca = _giro_del_salvataggio(nuovi)


# I filtri di ricerca nel salvataggio, dal formato 10 dell'archivio. Si scrivono severi: quello che si scrive deve
# rileggersi uguale, senza riparazioni. Si leggono indulgenti, scelta di Gabriele del 24 ottobre 2026: quello che non si
# legge torna ai filtri di serie, con un avviso nel registro degli errori, invece di far rifiutare il mondo.

def _intero(valore, massimo=None):
    return isinstance(valore, int) and not isinstance(valore, bool) and valore >= 0 and (massimo is None or valore <= massimo)


def _numero(valore):
    return isinstance(valore, (int, float)) and not isinstance(valore, bool) and math.isfinite(valore)


def _una_di(*scelte):
    return lambda valore: valore is None or (isinstance(valore, str) and valore in scelte)


def _tratti_validi(valore):
    return isinstance(valore, dict) and all(tratto in TRATTI and isinstance(voluto, bool) for tratto, voluto in valore.items())


def _condizioni_valide(valore):
    return isinstance(valore, list) and all(isinstance(c, list) and len(c) == 3 and c[0] in CRITERI_DELLE_CONDIZIONI and c[1] in ("maggiore", "minore")
                                            and _numero(c[2]) for c in valore)


def _booleano(valore):
    return isinstance(valore, bool)


def _scritto(valore):
    return isinstance(valore, str)


def _fino_a(campo, intero=True):
    """Il controllo di un numero dei filtri: da zero al suo massimo, intero, o per il valore minimo anche con la virgola."""
    massimo = MASSIMI_DEI_NUMERI[campo]
    if intero:
        return lambda valore: _intero(valore, massimo)
    return lambda valore: _numero(valore) and 0 <= valore <= massimo


_CONTROLLI_DEI_FILTRI = {
    "allenatori": _booleano, "liberi": _booleano, "in_vendita": _booleano, "del_computer": _booleano, "tuoi": _booleano, "ritirati": _booleano,
    "nome": _scritto, "sesso": _una_di("m", "f"), "classe_migliore": lambda v: _intero(v, modulo_classe.LIVELLI), "eta_massima": _fino_a("eta_massima"),
    "costo_massimo": _fino_a("costo_massimo"), "disponibili_oggi": _booleano, "ordine": lambda v: isinstance(v, str) and v in dict(ORDINI_GIOCATORI),
    "ordine_allenatori": lambda v: isinstance(v, str) and v in dict(ORDINI_ALLENATORI),
    "classe_peggiore": lambda v: _intero(v, modulo_classe.LIVELLI), "eta_minima": _fino_a("eta_minima"), "regione": _scritto, "provincia": _scritto,
    "comune": _scritto, "polisportiva": _scritto, "tratti": _tratti_validi, "indole": _una_di(*INDOLI), "valore_minimo": _fino_a("valore_minimo", intero=False),
    "stipendio_massimo": _fino_a("stipendio_massimo"), "mesi_contratto_massimi": _fino_a("mesi_contratto_massimi"), "senza_acciacchi": _booleano,
    "solo_ritirati_che_allenano": _booleano, "solo_nuovi": _booleano, "comprendi_usciti": _booleano, "condizioni": _condizioni_valide,
    "tipo_allenatore": _una_di(*staff.TIPI), "visus": _una_di(*staff.VISUS), "posto_attuale": _una_di(*staff.RUOLI),
    "stipendio_capo_massimo": _fino_a("stipendio_capo_massimo"), "senza_prelazione_altrui": _booleano,
}


def filtri_a_dizionario(filtri):
    """I filtri come dizionario del salvataggio JSON: i tratti un dizionario, le condizioni elenchi di tre."""
    dati = {campo.name: getattr(filtri, campo.name) for campo in fields(Filtri)}
    dati["tratti"] = dict(filtri.tratti)
    dati["condizioni"] = [list(condizione) for condizione in filtri.condizioni]
    return dati


def _unisci(parti):
    # testi importa questo modulo: si legge al momento, come in sfide.
    from testi import unisci
    return unisci([str(parte) for parte in parti])


def _citato(valore):
    """Un dato letto dal salvataggio, citato in un avviso come nel JSON del registro: i testi sempre fra virgolette."""
    try:
        return json.dumps(valore, ensure_ascii=False)
    except (TypeError, ValueError):
        return repr(valore)


def problema_dei_filtri(dati):
    """
    Perché i filtri letti dal salvataggio non vanno, o None se vanno: ci vogliono tutti i campi di questa versione, e
    soltanto loro, ciascuno col suo controllo. È tutto o niente, regola di Gabriele: dei filtri che non vanno non si
    tengono i campi buoni.
    """
    if not isinstance(dati, dict):
        return "non sono un elenco di campi"
    mancano = [campo for campo in _CONTROLLI_DEI_FILTRI if campo not in dati]
    in_piu = [campo for campo in dati if campo not in _CONTROLLI_DEI_FILTRI]
    if mancano or in_piu:
        parti = []
        if mancano:
            parti.append(f"{'manca' if len(mancano) == 1 else 'mancano'} {_unisci(mancano)}")
        if in_piu:
            parti.append(f"{'avanza' if len(in_piu) == 1 else 'avanzano'} {_unisci(in_piu)}")
        return f"i campi non sono quelli di questa versione: {_unisci(parti)}"
    for campo, controllo in _CONTROLLI_DEI_FILTRI.items():
        if not controllo(dati[campo]):
            return f"il campo {campo} ha un valore che non va, {_citato(dati[campo])}"
    return None


def filtri_da_dizionario(dati):
    """I filtri letti dal salvataggio, ogni campo controllato; ValueError, col perché di problema_dei_filtri, se non vanno."""
    problema = problema_dei_filtri(dati)
    if problema is not None:
        raise ValueError(f"I filtri non sono validi: {problema}")
    return Filtri(**{**dati, "tratti": dict(dati["tratti"]), "condizioni": tuple(tuple(condizione) for condizione in dati["condizioni"])})


def filtri_di_ricerca_a_dizionario(filtri_di_ricerca):
    """I filtri di ricerca come dizionario del salvataggio JSON: i preset in ordine, il prossimo numero e le porte."""
    return {
        "preset": [{"numero": p.numero, "nome": p.nome, "filtri": filtri_a_dizionario(p.filtri)} for p in filtri_di_ricerca.preset],
        "prossimo_preset": filtri_di_ricerca.prossimo_preset,
        "porte": {porta: {"scelta": stato.scelta, "attuali": filtri_a_dizionario(stato.attuali)} for porta, stato in filtri_di_ricerca.porte.items()},
    }


# Un avviso della lettura: che cosa non va, che cosa fa la lettura, e il dato originale, che il registro scrive in JSON
# perché, se serve, preset e filtri si possano ricostruire a mano.
Avviso = namedtuple("Avviso", "problema rimedio originale")


def testo_per_il_registro(avviso):
    """La riga del registro degli errori per un avviso della lettura, col dato originale in JSON."""
    try:
        originale = json.dumps(avviso.originale, ensure_ascii=False)
    except (TypeError, ValueError):
        originale = repr(avviso.originale)
    return f"Lettura del mondo, filtri di Mercato e ricerca. {avviso.problema} {avviso.rimedio} Il dato originale, in JSON: {originale}"


def _nome_riparato(grezzo, numero, usati):
    """
    Il nome di un preset letto dal salvataggio, riparato se serve, e i perché della riparazione: senza un nome diventa
    Preset e il suo numero; perde gli spazi in testa e in coda e i caratteri di controllo; si accorcia a 50 caratteri;
    se lo usa già, senza badare alle maiuscole, un preset di prima o una voce di serie, prende un numero fra parentesi,
    (2), (3), restando entro i 50 caratteri. usati sono i nomi già dati, in minuscolo per il confronto.
    """
    perche = []
    nome = grezzo.strip() if isinstance(grezzo, str) else ""
    if isinstance(grezzo, str) and nome and nome != grezzo:
        perche.append("ha degli spazi in testa o in coda")
    if _con_caratteri_di_controllo(nome):
        nome = " ".join("".join(" " if unicodedata.category(c) in ("Cc", "Zl", "Zp") else c for c in nome).split())
        perche.append("ha dei caratteri di controllo")
    if not nome:
        nome = f"Preset {numero}"
        if grezzo is not None:
            perche.append("non ha nessun carattere" if isinstance(grezzo, str) else "non è un testo")
    if len(nome) > LUNGHEZZA_MASSIMA_DEL_NOME:
        nome = nome[:LUNGHEZZA_MASSIMA_DEL_NOME].rstrip()
        perche.append(f"supera i {LUNGHEZZA_MASSIMA_DEL_NOME} caratteri")
    if nome.casefold() in usati:
        volta = 2
        while True:
            coda = f" ({volta})"
            candidato = nome[:LUNGHEZZA_MASSIMA_DEL_NOME - len(coda)].rstrip() + coda
            if candidato.casefold() not in usati:
                break
            volta += 1
        nome = candidato
        perche.append("lo usa già un'altra voce della casella")
    return nome, perche


def _preset_letti(voci, prossimo, avvisi):
    """
    I preset di Gabriele letti dal salvataggio, e il prossimo numero. Un preset non si toglie mai, salvo una voce che
    non è nemmeno un dizionario: senza un numero valido, o con quello di un preset di prima, ne riceve uno nuovo; il nome
    si ripara con _nome_riparato; dei filtri che non si leggono diventano quelli di Tutti in attività, senza filtri. Il
    prossimo numero è almeno il più alto più uno.
    """
    if not isinstance(voci, list):
        avvisi.append(Avviso("I tuoi preset dei filtri non si leggono.", "La casella dei preset riparte senza.", voci))
        voci = []
    letti = []
    for posto, voce in enumerate(voci, 1):
        if isinstance(voce, dict):
            letti.append((posto, voce))
        else:
            avvisi.append(Avviso(f"Il preset al posto {posto} della casella non si legge.", "Si toglie.", voce))
    usati = set()
    numeri = []
    for _posto, voce in letti:
        numero = voce.get("numero")
        buono = _numero_di_preset(numero) and numero not in usati
        numeri.append(numero if buono else None)
        if buono:
            usati.add(numero)
    prossimo_valido = _numero_di_preset(prossimo)
    nuovo = max(prossimo if prossimo_valido else 1, max(usati, default=0) + 1)
    nomi_usati = set(_NOMI_RISERVATI)
    preset = []
    for (posto, voce), numero in zip(letti, numeri, strict=True):
        if numero is None:
            numero, nuovo = nuovo, nuovo + 1
            vecchio = voce.get("numero")
            perche = f"ha lo stesso numero di un preset di prima, {vecchio}" if _numero_di_preset(vecchio) else f"non ha un numero valido, {_citato(vecchio)}"
            avvisi.append(Avviso(f"Il preset al posto {posto} della casella {perche}.", f"Riceve il numero {numero}.", voce))
        grezzo = voce.get("nome")
        nome, perche = _nome_riparato(grezzo, numero, nomi_usati)
        nomi_usati.add(nome.casefold())
        if grezzo is None:
            avvisi.append(Avviso(f"Al preset numero {numero} manca il nome.", f"Si chiama {nome}.", voce))
        elif perche:
            avvisi.append(Avviso(f"Il nome del preset numero {numero}, {_citato(grezzo)}, {_unisci(perche)}.", f"Diventa {nome}.", voce))
        problema = problema_dei_filtri(voce.get("filtri"))
        if problema is None:
            filtri = filtri_da_dizionario(voce["filtri"])
        else:
            filtri = filtri_di_serie(SERIE_DEI_FILTRI_ILLEGGIBILI)
            avvisi.append(Avviso(f"I filtri del preset {nome}, numero {numero}, non sono validi: {problema}.",
                                 f"Diventano quelli del preset di serie {nome_del_preset_di_serie(SERIE_DEI_FILTRI_ILLEGGIBILI)}.", voce))
        in_piu = [chiave for chiave in voce if chiave not in ("numero", "nome", "filtri")]
        if in_piu:
            avvisi.append(Avviso(f"Il preset {nome}, numero {numero}, ha dei dati che questa versione non conosce: {_unisci(in_piu)}.", "Si tolgono.", voce))
        preset.append(Preset(numero, nome, filtri))
    if not prossimo_valido:
        avvisi.append(Avviso(f"Il numero del prossimo preset non è valido, {_citato(prossimo)}.", f"Diventa {nuovo}.", prossimo))
    elif prossimo <= max(usati, default=0):
        avvisi.append(Avviso(f"Il numero del prossimo preset, {prossimo}, è già di un preset.", f"Diventa {nuovo}.", prossimo))
    return preset, nuovo


_MANCA = object()


def _porta_letta(porta, voce, numeri, avvisi):
    """
    Lo stato di una porta letto dal salvataggio: se non si legge, o se riapriva un preset che non c'è più, la porta
    torna al suo preset di serie; dei filtri attuali che non si leggono diventano quelli del preset di serie della porta.
    """
    nome = NOMI_DELLE_PORTE[porta]
    chiave = PRESET_DELLA_PORTA[porta]
    rimedio = f"Torna al suo preset di serie, {nome_del_preset_di_serie(chiave)}."
    if voce is _MANCA:
        avvisi.append(Avviso(f"Manca lo stato della porta {nome}.", rimedio, None))
        return stato_di_serie(porta)
    if not isinstance(voce, dict):
        avvisi.append(Avviso(f"Lo stato della porta {nome}, non si legge.", rimedio, voce))
        return stato_di_serie(porta)
    in_piu = [campo for campo in voce if campo not in ("scelta", "attuali")]
    if in_piu:
        avvisi.append(Avviso(f"Lo stato della porta {nome}, ha dei dati che questa versione non conosce: {_unisci(in_piu)}.", "Si tolgono.", voce))
    scelta = voce.get("scelta", _MANCA)
    if scelta is _MANCA:
        avvisi.append(Avviso(f"La porta {nome}, non dice quale voce della casella riaprire.", rimedio, voce))
        scelta = chiave
    elif _numero_di_preset(scelta) and scelta not in numeri:
        avvisi.append(Avviso(f"La porta {nome}, riapriva il preset numero {scelta}, che non c'è più.", rimedio, voce))
        scelta = chiave
    elif not (scelta is None or _numero_di_preset(scelta) or (isinstance(scelta, str) and scelta in _FILTRI_DI_SERIE)):
        avvisi.append(Avviso(f"La porta {nome}, riapriva una voce della casella che non c'è, {_citato(scelta)}.", rimedio, voce))
        scelta = chiave
    problema = problema_dei_filtri(voce.get("attuali"))
    if problema is None:
        return StatoDellaPorta(scelta, filtri_da_dizionario(voce["attuali"]))
    if scelta is None:
        scelta = chiave
    avvisi.append(Avviso(f"I filtri attuali della porta {nome}, non sono validi: {problema}.",
                         f"Diventano quelli del suo preset di serie, {nome_del_preset_di_serie(chiave)}.", voce))
    return StatoDellaPorta(scelta, filtri_di_serie(chiave))


def _porte_lette(dati, numeri, avvisi):
    """Lo stato delle porte letto dal salvataggio, ognuna per sé: una porta che non si legge non tocca le altre, né i preset."""
    if not isinstance(dati, dict):
        avvisi.append(Avviso("Lo stato delle porte d'ingresso non si legge.", "Ogni porta torna al suo preset di serie.", dati))
        return {porta: stato_di_serie(porta) for porta in PORTE}
    in_piu = [porta for porta in dati if porta not in PORTE]
    if in_piu:
        avvisi.append(Avviso(f"Ci sono porte d'ingresso che questa versione non conosce: {_unisci(in_piu)}.", "Si tolgono.",
                             {porta: dati[porta] for porta in in_piu}))
    return {porta: _porta_letta(porta, dati.get(porta, _MANCA), numeri, avvisi) for porta in PORTE}


def filtri_di_ricerca_da_dizionario(dati):
    """
    I filtri di ricerca letti dal salvataggio, e gli avvisi di quello che non si leggeva, nell'ordine in cui si sono
    trovati. Non solleva mai eccezioni, scelta di Gabriele: quello che non si legge torna ai filtri di serie, e il mondo
    si apre lo stesso. Preset e porte si leggono separati, così delle porte rovinate non tolgono i preset; un preset
    non si toglie mai, salvo una voce che non è nemmeno un dizionario, e si ripara.
    """
    avvisi = []
    if not isinstance(dati, dict):
        avvisi.append(Avviso("I filtri e i preset della finestra Mercato e ricerca non si leggono.", "Tornano quelli di serie, senza i tuoi preset.", dati))
        return filtri_di_ricerca_di_serie(), avvisi
    in_piu = [chiave for chiave in dati if chiave not in ("preset", "prossimo_preset", "porte")]
    if in_piu:
        avvisi.append(Avviso(f"I filtri della finestra Mercato e ricerca hanno dei dati che questa versione non conosce: {_unisci(in_piu)}.", "Si tolgono.",
                             {chiave: dati[chiave] for chiave in in_piu}))
    preset, prossimo = _preset_letti(dati.get("preset"), dati.get("prossimo_preset"), avvisi)
    porte = _porte_lette(dati.get("porte"), {p.numero for p in preset}, avvisi)
    return FiltriDiRicerca(preset, prossimo, porte), avvisi


def _giro_del_salvataggio(filtri_di_ricerca):
    """
    I filtri di ricerca dopo il giro del salvataggio, nel JSON e nella lettura: quello che si scrive deve rileggersi
    senza nessuna riparazione. ValueError, col primo problema, se non va.
    """
    try:
        testo = json.dumps(filtri_di_ricerca_a_dizionario(filtri_di_ricerca))
    except (TypeError, ValueError, AttributeError) as e:
        raise ValueError(f"I filtri della finestra Mercato e ricerca non si possono scrivere: {e}") from e
    letti, avvisi = filtri_di_ricerca_da_dizionario(json.loads(testo))
    if avvisi:
        # Senza il punto finale, come gli altri errori del salvataggio, che archivio.salva continua.
        raise ValueError(avvisi[0].problema.removesuffix("."))
    return letti


def filtri_di_ricerca_da_salvare(mondo):
    """
    I filtri di ricerca del mondo per il salvataggio, quelli di serie se il mondo non li ha. Fanno il giro del
    salvataggio anche qui, per chi li mettesse nel mondo senza ricorda_i_preset e ricorda_la_porta: con qualcosa che non
    si rileggerebbe, ValueError, e archivio.salva lascia il salvataggio di prima com'era, invece di scriverne uno da riparare.
    """
    filtri_di_ricerca = mondo.filtri_di_ricerca if mondo.filtri_di_ricerca is not None else filtri_di_ricerca_di_serie()
    return filtri_di_ricerca_a_dizionario(_giro_del_salvataggio(filtri_di_ricerca))


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
    # Chi non ha un contratto, come un libero o un ritirato, con quel limite non c'entra e resta, come più sotto
    # per lo stipendio e il costo: Filtri attivi lo dice, con restano.
    if filtri.mesi_contratto_massimi:
        prove.append(lambda r: not contratti.ha_contratto(r.persona) or contratti.mesi_al_termine(r.persona, oggi) <= filtri.mesi_contratto_massimi)
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

    def quota(r):
        # In fondo chi non ha un prezzo da confrontare: chi non ha un costo, e i tesserati del computer.
        valore = prezzo_sul_mercato(r, memoria)
        return (valore is None, valore or 0.0, r.persona.id)

    chiavi = {
        "valore_alto": lambda r: (-r.persona.indice_collettivo_valore, r.persona.id),
        "valore_basso": lambda r: (r.persona.indice_collettivo_valore, r.persona.id),
        "classe": lambda r: (-memoria.punteggio(r.persona), r.persona.id),
        "eta_giovane": lambda r: (r.persona.eta, r.persona.id),
        "eta_anziano": lambda r: (-r.persona.eta, r.persona.id),
        "costo_basso": lambda r: (r.costo is None, r.costo or 0, r.persona.id),
        "costo_alto": lambda r: (r.costo is None, -(r.costo or 0), r.persona.id),
        "euro_per_punto": lambda r: (r.costo is None, euro_per_punto(r) or 0.0, r.persona.id),
        "prezzo_sul_mercato": quota,
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
    """
    Il costo della riga diviso il valore di mercato del giocatore, 0,8 è l'80%; None se non ha un costo, e per
    un tesserato del computer, che ha per costo il valore di mercato come riferimento: il suo prezzo vero è
    nascosto, decisione D23, e arriva fino al 50% in più, quindi il 100% di ogni riga sarebbe un dato falso.
    """
    if r.costo is None or r.stato == DEL_COMPUTER:
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
    # Come per i giocatori, chi non ha un contratto, l'allenatore libero, resta.
    if filtri.mesi_contratto_massimi:
        prove.append(lambda r: not contratti.ha_contratto(r.persona) or contratti.mesi_al_termine(r.persona, oggi) <= filtri.mesi_contratto_massimi)
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
        # A parità di classe, dal più giovane, come nel mercato degli allenatori di prima.
        "classe": lambda r: (r.persona.livello, r.persona.eta(oggi), r.persona.numero),
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


def indice_della_persona(righe, numero, allenatori=False, ripiego=0):
    """
    Dopo un ricalcolo, il posto della stessa persona, cercata per numero; None se l'elenco è vuoto. Se non c'è più,
    il posto di ripiego, entro le righe: la prima dopo un filtro, lo stesso posto di prima dopo un esito, come
    l'ingaggio che toglie un libero dall'elenco e lascia la scelta sul seguente.
    """
    if not righe:
        return None
    trovato = next((i for i, r in enumerate(righe) if r.allenatore == allenatori and r.numero == numero), None)
    return trovato if trovato is not None else min(max(ripiego, 0), len(righe) - 1)


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
    di sfide.problema_bersaglio; il motivo dice se le sfide sono finite, se il club ha già rifiutato oggi, col
    suono del lancio di sfide, o se il club non si può sfidare.
    """
    if poli is None:
        return _senza_attiva("le sfide le lancia la polisportiva attiva")
    club = riga.polisportiva if riga.stato in (DEL_COMPUTER, IN_VENDITA) else None
    problema = sfide.problema_bersaglio(mondo, poli, club.nome if club is not None else None)
    if problema is None:
        return Possibile(SFIDA, None, None)
    if sfide.tua(poli) and sfide.disponibili(mondo, poli) <= 0:
        return Possibile(SFIDA, problema, "nessuna_sfida_da_lanciare")
    if club is not None and club.is_cpu_controlled and mondo.sfide.rifiutata_oggi(poli.nome, club.nome, mondo.datetime_corrente_simulazione.date()):
        return Possibile(SFIDA, problema, "sfida_gia_rifiutata_oggi")
    return Possibile(SFIDA, problema, CLUB_NON_SFIDABILE)
