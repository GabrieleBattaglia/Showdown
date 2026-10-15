"""
La carriera perfetta di MESS e i mondi sintetici, per fissare le fonti dei punti allenamento e dell'esperienza.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-09 con la tappa 11, decisione D31 e punto 12.3 del progetto della tappa, che vi ha
fissato una volta per sempre la somma della carriera perfetta, le ancore e i pesi della classe. Usa
le funzioni vere di allenamento.py, del motore, dei tornei e dell'esito rapido, non scrive niente nel
progetto e alla fine stampa il blocco da copiare in costanti.py.
Dalla tappa 12, il 2026-10-14, decisione D32 e punto 10.4 del progetto, è riscritto: la carriera di
riferimento gioca davvero il calendario. Il nato di riferimento è quello di sempre, il novantesimo
percentile vedente senza tratti di cinque semi; la somma congelata e le ancore non si ricalcolano più,
si leggono da costanti.py. Giorno per giorno dai 9 ai 50 anni, 4.428 giorni: la seduta normale,
l'esperienza del giorno e la costanza; a ogni prossimo torneo, col contatore fisso nove volte su
dieci, si iscrive all'edizione che sceglierebbe l'iscrizione automatica nel calendario predefinito, e
la decima salta il turno; il torneo si gioca davvero con tornei.py, con gli altri iscritti presi dal
mondo sintetico a regime del suo sesso, o da tutto il mondo per gli aperti, fino al tetto, i loro
incontri con l'esito rapido e i suoi col motore vero in modalità essenziale, con la fatica della
giornata; ogni anno solare il mondiale, se il suo punteggio di classe sta fra i primi 32 del suo sesso
nel mondo sintetico a regime, grande quanto il mondo vero, contro gli altri 31; le sfide della sua
polisportiva, SFIDE_GIOCATE_AL_MESE, col 90 per cento di presenza, in gare a squadre col motore, con
due compagni e tre avversari del mondo sintetico; l'amichevole nel 90 per cento dei giorni liberi da
impegni, contro un avversario del mondo sintetico all'anno 10, come prima; la spesa completa ogni
giorno; il calo dei livelli alti ogni mese. Senza infortuni né acciacchi, come prima.
Il metodo, punto 10.4: con i fattori del giro si gioca la carriera e si contano per fonte i punti
grezzi, cioè senza fattore ma con l'importanza; il totale T dei punti della carriera si cerca perché
la più lenta delle cinque carriere vedenti arrivi ad A1 a 49 anni e tre quarti, nel mezzo del
bersaglio fra 49 e mezzo e 50; la seduta è fissa, quindi la parte delle partite è T meno la seduta, e
si divide fra tornei, amichevoli e sfide nelle proporzioni 40, 34 e 4 di D32; ogni fattore è la sua
parte divisa per i suoi punti grezzi. L'esperienza si risolve allo stesso modo, fonte per fonte, sulla
somma senza il tetto di 20: l'età fa da sé, circa 2, le amichevoli 2,5, le sfide 3, il club 4,5 e i
tornei 8, divisi 50 per cento agli incontri, 20 alle fasi superate e 30 ai piazzamenti; è l'ordine
delle parole di D32, dalla fonte più piccola alla più grande, che vale dalla decisione 8 di Gabriele
del 14 ottobre 2026, mentre prima le sfide facevano 1,5, il club 5 e i tornei 9. Il totale si cerca col
metodo delle secanti sul logaritmo di T; i mondi sintetici, che giocano le gare del mondo coi fattori
del giro, si rifanno a ogni giro, finché i fattori non si spostano più dell'uno per cento.
Lo strumento stampa: i fattori e le esperienze da copiare in costanti.py, le quote ottenute, la quota
della seduta, i punti al mese, l'età di A1 dei cinque semi e dei tre ipovedenti, l'esperienza a 50
anni senza tetto, la classe a 20, 30, 40 e 50 anni, quanto pesa il mondiale, i casi tipici di oggi e
le lettere dei mondi sintetici.
La revisione del 14 ottobre 2026 ha cambiato due cose. Primo, una carriera sola per nato era una
fortuna dell'estrazione: con altri semi del caso la stessa carriera arrivava ad A1 dopo i 50 anni. Ora
i nati sono dieci, ciascuno giocato con cinque estrazioni del caso, e il bersaglio è la media del nato
più lento, fra 49,5 e 50 anni, con al più una carriera su dieci dopo i 50; l'esperienza si risolve
sulla media dello stesso nato. Alla fine i mondi sintetici si rifanno coi fattori trovati e tutte le
carriere si rigiocano, così la carta si riproduce da costanti.py. Secondo, la carriera va al mondiale
come nel mondo: all'apertura, se i punti della classifica dell'ultimo anno, presi coi piazzamenti come
fa premiazioni.chiudi, passano la soglia del trentaduesimo convocato del mondo a regime,
PUNTI_PER_IL_MONDIALE; prima bastava il punteggio di classe del trentaduesimo del mondo sintetico, e la
carriera giocava sei mondiali sempre, dal primo a 32 anni e mezzo. Gli avversari del mondiale restano
i primi 31 per classe del mondo sintetico a regime, che per forza somigliano ai convocati del mondo.
La decisione 7 di Gabriele del 14 ottobre 2026: i pesi della classe sono diventati una copia di quelli
del valore, con le battute da 0,71 a 0,47, e la somma congelata e le ancore, misurate coi pesi di prima,
si ricalcolano una volta, con --ricalcola-classe, prima della ricerca dei fattori; poi tornano congelate,
e lo strumento rifiuta un secondo ricalcolo. Il ricalcolo converte, non ridefinisce: la somma non torna a
essere quella di una carriera, perché allora i fattori, che si cercano proprio perché le carriere
arrivino alla somma congelata, non avrebbero più un bersaglio. Con i fattori in vigore si giocano tutte
le carriere vedenti, e la somma nuova è quella della tappa 11 per il rapporto medio, a 50 anni, fra la
somma coi pesi nuovi e quella coi pesi di prima, arrotondato per difetto al decimo: le carriere restano
dove erano, e cambia soltanto quanto pesa ogni caratteristica. Le ancore dei nati del primo e del
novantanovesimo percentile si rifanno per definizione, coi pesi nuovi e la somma nuova; quella del bravo
dell'utente a 35 anni si converte come la somma, sulla parte del valore del suo caso tipico, perché il
caso tipico cambia coi fattori che la ricerca sta per cercare. Poi la ricerca gira con la classe nuova, e
il blocco da copiare in costanti.py ha anche la somma e le ancore, con i punteggi esatti per le prove.
La decisione 6 di Gabriele del 14 ottobre 2026 ha cambiato il bersaglio: non più la media del nato più
lento, che oscillava di mezzo anno da una misura all'altra secondo quanti mondiali giocava, ma la media
di tutte le carriere vedenti, che arriva ad A1 a 50 anni con 20 di esperienza. Il totale si cerca su
quella media, e i fattori e le esperienze si risolvono sui suoi punti grezzi e sui suoi conteggi; il
nato più lento e le carriere che arrivano dopo i 50 anni si dicono, senza essere bersagli. Con le misure
di un giro la retta del totale si stima ai minimi quadrati su tutti i passi, e non più con le secanti
sugli ultimi due, che rincorrevano il rumore.
Uso, dalla cartella del progetto o da qualunque altra:
    python strumenti/carriera_perfetta.py --processi 8 --rapporto carriera.txt
    python strumenti/carriera_perfetta.py --ricalcola-classe --processi 8 --rapporto carriera.txt
    python strumenti/carriera_perfetta.py --veloce
"""

import argparse
import concurrent.futures
import copy
import datetime
import math
import os
import random
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
for cartella in (RADICE, RADICE / "strumenti"):
    if str(cartella) not in sys.path:
        sys.path.insert(0, str(cartella))

from mondi_sintetici import FATTORE_GRUPPO, GIORNI_ANNO, allena_a_passi, mondo_sintetico, nati  # noqa: E402

import allenamento  # noqa: E402
import calendario  # noqa: E402
import classe  # noqa: E402
import costanti  # noqa: E402
import economia  # noqa: E402
import esito_rapido  # noqa: E402
import esperienza  # noqa: E402
import formule  # noqa: E402
import iscrizioni  # noqa: E402
import modelli_torneo  # noqa: E402
import palmares  # noqa: E402
import partita  # noqa: E402
import percorsi  # noqa: E402
import tornei  # noqa: E402
import valore  # noqa: E402
from modelli import Giocatore  # noqa: E402
from motore import ESSENZIALE, SQUADRE, Incontro, Squadra, formato_singolare, simula_incontro  # noqa: E402
from motore.squadre import composizione_valida  # noqa: E402
from partita import MotorePartita  # noqa: E402

ETA_INGRESSO, ETA_USCITA = 9.0, 50.0
GIORNI_CARRIERA = int((ETA_USCITA - ETA_INGRESSO) * GIORNI_ANNO)
MESI_CARRIERA = GIORNI_CARRIERA / 30.0
QUOTA_AMICHEVOLI = 0.9
QUOTA_TORNEI = 0.9
PRESENZA_SFIDE = 0.9
TAPPE = (20, 30, 40, 50)
# Il primo giorno del calendario della carriera: un lunedì qualunque, come quello della simulazione lunga.
DATA_INIZIO = datetime.date(2026, 1, 1)
# Le quote dei punti delle partite di D32, sulla parte delle partite, e quelle dell'esperienza, punto 10.3.
QUOTE_PARTITE = {esperienza.TORNEO: 40.0, esperienza.AMICHEVOLE: 34.0, esperienza.SFIDA: 4.0}
QUOTA_SEDUTA_ATTESA = 22.0
# L'ordine delle fonti d'esperienza, decisione 8 di Gabriele del 14 ottobre 2026: età, amichevoli, sfide,
# club e tornei, dalla più piccola alla più grande; l'età fa circa 2 da sé.
ESPERIENZA_AMICHEVOLI, ESPERIENZA_SFIDE, ESPERIENZA_CLUB, ESPERIENZA_TORNEI = 2.5, 3.0, 4.5, 8.0
PARTI_DEI_TORNEI = {"incontri_torneo": 0.5, "fasi": 0.2, "piazzamenti": 0.3}
# Il bersaglio, dalla decisione 6 di Gabriele del 14 ottobre 2026: la media di tutte le carriere vedenti
# ad A1 a 50 anni, dentro la banda da 49,75 a 50,25, con l'esperienza media a 50 anni senza tetto fra 19,9
# e 20,1. Fino ad allora era il nato più lento, fra 49 e mezzo e 50 anni, cercato nel mezzo, a 49,75.
ETA_A1_BERSAGLIO = 50.0
BANDA_ETA_A1 = (49.75, 50.25)
BANDA_ESPERIENZA = (19.9, 20.1)
# La convocazione al mondiale coi punti è una soglia: chi la passa per poco o la manca cambia di molto i
# suoi punti, e la media oscilla un poco da un passo all'altro anche coi semi fermi; i fattori di qualche
# per cento. Con la media di tutte le carriere l'oscillazione è più piccola di quella del nato più lento,
# per cui la revisione del 14 ottobre 2026 aveva allargato le tolleranze di prima, 0,08 anni e l'uno per
# cento, a 0,2 e al 3.
TOLLERANZA_ETA = 0.15
TOLLERANZA_FATTORI = 0.03
# I nati di riferimento della carriera perfetta, vedenti, e gli ipovedenti, misurati per dire quando
# arrivano ad A1; ciascuno con ESTRAZIONI del caso, dalla revisione del 14 ottobre 2026.
SEMI_RIFERIMENTO = (11, 12, 13, 21, 99, 31, 47, 58, 73, 85)
SEMI_IPOVEDENTI = (11, 12, 13)
ESTRAZIONI = 5
# Il mondo sintetico a regime grande quanto il mondo vero, per il mondiale: i primi 32 di circa 10.300 per sesso.
ATTIVI_A_REGIME = 20_600
QUALIFICATI_MONDIALE = 32
# I punti attesi per amichevole dei casi dell'utente, grezzi: il mediano 3,1 e il bravo 3,5.
PUNTI_AMICHEVOLE_MEDIANO = 3.1
PUNTI_AMICHEVOLE_BRAVO = 3.5
# L'ancora del bravo dell'utente: il livello, D0, e l'età a cui ci arriva.
ANCORA_DEL_BRAVO = (30, 35)
_FISICHE = ("precisione", "resistenza", "forza")
# La classe congelata dalla revisione della tappa 11, prima della decisione 7 di Gabriele del 14 ottobre
# 2026: i pesi, la somma della carriera perfetta e le ancore. --ricalcola-classe parte da qui per
# convertire una volta la somma e l'ancora del bravo ai pesi nuovi della classe, quelli del valore.
PESI_CLASSE_PRIMA = {
    "lungolineasx": 0.46, "lungolineadx": 0.46, "diagonalesx": 0.50, "diagonaledx": 0.50, "singolaspondasx": 0.46, "singolaspondadx": 0.46,
    "doppiaspondasx": 0.48, "doppiaspondadx": 0.48, "triplaspondasx": 0.41, "triplaspondadx": 0.41, "bomba": 0.50, "battutasx": 0.71,
    "battutadx": 0.71, "chiusura_dritto": 2.20, "chiusura_rovescio": 2.73, "blocco_dritto": 1.29, "blocco_rovescio": 1.55, "difesa": 3.33,
    "tenutapaletta": 1.25, "controllopalla": 0.75, "attacco": 1.36, "precisione": 10.25, "forza": 5.59, "resistenza": 3.63,
}
PESI_TRATTI_CLASSE_PRIMA = {"mancino": 2.7, "ambidestro": 3.9, "giocorapido": 0.9, "cambiovelocita": 4.5}
SOMMA_CARRIERA_PERFETTA_PRIMA = 363.5
ANCORE_CLASSE_PRIMA = ((100, 0.0), (89, 0.204), (50, 0.404), (30, 0.609), (1, 1.0))


def numero(valore_numerico, decimali=1):
    return f"{valore_numerico:.{decimali}f}".replace(".", ",")


def senza_tratti(g):
    """Vero per chi non ha tratti speciali né tratti rari dell'allenamento."""
    return not (g.mancino or g.ambidestro or g.giocorapido or g.cambiovelocita or g.talento or g.apprendista_rapido or g.maturazione)


def al_percentile(gruppo, quota):
    ordinati = sorted(gruppo, key=valore.somma_pesata)
    return ordinati[min(len(ordinati) - 1, int(len(ordinati) * quota))]


def percentile(valori, quota):
    ordinati = sorted(valori)
    return ordinati[min(len(ordinati) - 1, int(len(ordinati) * quota))] if ordinati else 0.0


def pronto(g, anni):
    """Una copia del giocatore all'età indicata, senza allenamento, esperienza, costanza né punti."""
    copia = copy.deepcopy(g)
    copia.eta = int(anni * GIORNI_ANNO)
    copia.esperienza = copia.costanza = copia.punti_allenamento = 0.0
    copia.diario = []
    copia.aggiorna_icv()
    return copia


def punteggio(somma, esp, somma_perfetta):
    return costanti.PESO_VALORE_CLASSE * somma / somma_perfetta + costanti.PESO_ESPERIENZA_CLASSE * min(1.0, esp / costanti.ESPERIENZA_MASSIMA)


# Le fonti: i fattori dei punti e le costanti dell'esperienza, nei moduli del processo.

def fonti_in_vigore():
    """I fattori dei punti delle tre fonti e le costanti dell'esperienza di costanti.py."""
    fattori = {esperienza.TORNEO: costanti.PA_FATTORE_TORNEO, esperienza.AMICHEVOLE: costanti.PA_FATTORE_AMICHEVOLE, esperienza.SFIDA: costanti.PA_FATTORE_SFIDA}
    esperienze = {"amichevoli": costanti.ESPERIENZA_PER_AMICHEVOLE, "sfide": costanti.ESPERIENZA_PER_SFIDA, "club": costanti.ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA,
                  "incontri_torneo": costanti.ESPERIENZA_PER_PARTITA_TORNEO, "fasi": costanti.ESPERIENZA_PER_FASE_SUPERATA, "piazzamenti": costanti.ESPERIENZA_PIAZZAMENTO_BASE}
    return fattori, esperienze


def imposta_fonti(fattori, esperienze):
    """
    Mette i fattori e le costanti dell'esperienza del giro nei moduli di questo processo, soltanto per la
    misura: costanti.py per i mondi sintetici, esperienza.py e partita.py per le funzioni vere.
    """
    costanti.PA_FATTORE_TORNEO, costanti.PA_FATTORE_AMICHEVOLE, costanti.PA_FATTORE_SFIDA = (fattori[esperienza.TORNEO], fattori[esperienza.AMICHEVOLE],
                                                                                           fattori[esperienza.SFIDA])
    partita.PA_FATTORE.update(fattori)
    nomi = {"amichevoli": "ESPERIENZA_PER_AMICHEVOLE", "sfide": "ESPERIENZA_PER_SFIDA", "club": "ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA",
            "incontri_torneo": "ESPERIENZA_PER_PARTITA_TORNEO", "fasi": "ESPERIENZA_PER_FASE_SUPERATA", "piazzamenti": "ESPERIENZA_PIAZZAMENTO_BASE"}
    for chiave, nome in nomi.items():
        setattr(costanti, nome, esperienze[chiave])
        setattr(esperienza, nome, esperienze[chiave])
    esperienza.PER_PARTITA.update({esperienza.AMICHEVOLE: esperienze["amichevoli"], esperienza.TORNEO: esperienze["incontri_torneo"],
                                   esperienza.SFIDA: esperienze["sfide"]})


# La classe: la somma e le ancore nei moduli del processo, e la somma coi pesi di prima della decisione 7.

def classe_in_vigore():
    """La somma della carriera perfetta e le ancore della classe di adesso, in questo processo."""
    return costanti.SOMMA_CARRIERA_PERFETTA, tuple(tuple(ancora) for ancora in costanti.ANCORE_CLASSE)


def imposta_classe(somma, ancore):
    """
    Mette la somma e le ancore della classe nei moduli di questo processo, soltanto per la misura:
    costanti.py, e classe.py con le sue soglie, come faceva la carriera perfetta della tappa 11.
    """
    ancore = tuple(tuple(ancora) for ancora in ancore)
    costanti.SOMMA_CARRIERA_PERFETTA = classe.SOMMA_CARRIERA_PERFETTA = somma
    costanti.ANCORE_CLASSE = ancore
    classe.SOGLIE_CLASSE = classe._soglie(ancore)
    classe._SOGLIE_CRESCENTI = tuple(-s for s in classe.SOGLIE_CLASSE)


def somma_classe_prima(g):
    """Il valore pesato della classe coi pesi congelati della tappa 11, quelli di prima della decisione 7."""
    return valore.somma_pesata(g, pesi=PESI_CLASSE_PRIMA) + valore.bonus_tratti(g, PESI_TRATTI_CLASSE_PRIMA)


# Il calendario predefinito della carriera.

def calendario_predefinito(giorni=GIORNI_CARRIERA):
    """
    Le edizioni del calendario predefinito nei giorni della carriera, dai modelli e dalle formule di
    dati/tornei: per ogni modello individuale e attivo il dizionario del modello, la formula e le date
    d'inizio. La cartella del programma la sposta chi chiama, perché i modelli si copiano accanto al gioco.
    """
    gestore = modelli_torneo.GestoreModelli()
    if not os.path.isdir(gestore.cartella()):
        gestore.crea_predefiniti()
    modelli, _scartati = gestore.modelli()
    formule_valide, _scartate = formule.leggi()
    fine = DATA_INIZIO + datetime.timedelta(days=giorni + 60)
    uscita = []
    for modello in modelli:
        if not modello.attivo or modello.tipo != modelli_torneo.INDIVIDUALE or modelli_torneo.problema(modello, formule_valide) is not None:
            continue
        formula = modelli_torneo.formula_del_modello(modello, formule_valide)
        date = []
        giorno = DATA_INIZIO
        while True:
            inizio = modelli_torneo.prossima_data(modello, giorno)
            if inizio > fine:
                break
            date.append(inizio.isoformat())
            giorno = inizio + datetime.timedelta(days=1)
        uscita.append((modello.a_dizionario(), formula, date))
    return uscita


def edizioni_del_calendario(predefinito):
    """Le edizioni del calendario come oggetti del calendario del mondo, in ordine d'apertura, con gli identificativi."""
    edizioni = []
    prossimo = 1
    for modello, formula, date in predefinito:
        oggetto = modelli_torneo.ModelloTorneo.da_dizionario(modello)
        durata = modelli_torneo.durata_prevista(oggetto, formula)
        for numero_edizione, testo in enumerate(date, start=1):
            inizio = datetime.date.fromisoformat(testo)
            apertura = inizio - datetime.timedelta(days=modello["giorni_iscrizione"])
            edizioni.append(calendario.Edizione(prossimo, modello, formula, inizio, apertura, numero_edizione, durata))
            prossimo += 1
    edizioni.sort(key=lambda ed: (ed.data_apertura, ed.id))
    return edizioni


# Il contesto di un processo: gli avversari dei mondi sintetici e il calendario.

_CONTESTO = {}


def prepara_contesto(dati):
    """
    Il contesto di un processo, dai dizionari: la classe in vigore, gli avversari delle amichevoli, quelli
    dei tornei per sesso, i primi per il mondiale e le soglie, le edizioni.
    """
    _CONTESTO.clear()
    if "classe" in dati:
        imposta_classe(*dati["classe"])
    _CONTESTO["amichevoli"] = [Giocatore.da_dizionario(d) for d in dati["amichevoli"]]
    regime = [Giocatore.da_dizionario(d) for d in dati["regime"]]
    for g in regime:
        g.aggiorna_icv()
    _CONTESTO["per_sesso"] = {sesso: [g for g in regime if g.sesso == sesso] for sesso in ("m", "f")}
    _CONTESTO["tutti"] = regime
    _CONTESTO["punteggi"] = {g.id: classe.punteggio(g) for g in regime}
    _CONTESTO["primi"] = {sesso: [next(g for g in regime if g.id == gid) for gid in ids] for sesso, ids in dati["primi"].items()}
    _CONTESTO["soglie"] = dict(dati["soglie"])
    _CONTESTO["edizioni"] = edizioni_del_calendario(dati["calendario"])


def contesto_in_dizionari(mondo_10, regime, predefinito):
    """
    Il contesto da mandare ai processi, in dizionari: la classe in vigore, che dopo --ricalcola-classe è
    quella nuova, i primi 31 di ogni sesso per punteggio di classe, e la soglia del trentaduesimo.
    """
    primi, soglie = {}, {}
    for sesso in ("m", "f"):
        ordinati = sorted((g for g in regime if g.sesso == sesso), key=lambda g: (-classe.punteggio(g), g.id))
        primi[sesso] = [g.id for g in ordinati[:QUALIFICATI_MONDIALE - 1]]
        soglie[sesso] = classe.punteggio(ordinati[QUALIFICATI_MONDIALE - 1]) if len(ordinati) >= QUALIFICATI_MONDIALE else 0.0
    return {"classe": classe_in_vigore(), "amichevoli": [g.a_dizionario() for g in mondo_10], "regime": [g.a_dizionario() for g in regime], "primi": primi,
            "soglie": soglie, "calendario": predefinito}


# La carriera.

class Carriera:
    """
    Una carriera perfetta giorno per giorno, col calendario e i mondi sintetici del contesto, i fattori
    dei punti e le costanti dell'esperienza dati. Conta i punti grezzi per fonte, con l'importanza, e i
    conteggi grezzi dell'esperienza; l'esperienza si accumula anche senza il tetto di 20.
    """

    def __init__(self, g0, seme, fattori, esperienze, giorni=GIORNI_CARRIERA, tappe=TAPPE, coda_da=45.0):
        self.rng = random.Random(f"carriera-{seme}")
        self.g = pronto(g0, ETA_INGRESSO)
        self.fattori = dict(fattori)
        self.esperienze = dict(esperienze)
        self.giorni = giorni
        self.tappe_chieste = tappe
        self.coda_da = coda_da
        self.grezzi = dict.fromkeys(QUOTE_PARTITE, 0.0)
        self.grezzi_mondiale = 0.0
        self.conteggi = {"amichevoli": 0.0, "sfide": 0.0, "giorni": 0.0, "incontri_torneo": 0.0, "fasi": 0.0, "piazzamenti": 0.0}
        self.esperienza_libera = 0.0
        self.seduta = 0.0
        self.registro = {}
        self.coda = []
        self.storia = {"tornei": 0, "incontri_torneo": 0, "vinti_torneo": 0, "medaglie": dict.fromkeys(("oro", "argento", "bronzo", "legno"), 0), "mondiali": 0,
                       "titoli_mondiali": 0, "primo_mondiale": None, "sfide": 0, "sfide_vinte": 0, "amichevoli": 0, "salti": 0}
        self.prossimo = None
        self.iscrizione = None
        self.mondiale = None
        # I punti della classifica dei piazzamenti, coppie di giorno e punti, per la convocazione al mondiale.
        self.punti_recenti = []
        self.torneo = None
        self.id_torneo = 0
        self.contatore_tornei = 0.0
        self.contatore_sfide = 0.0
        self.contatore_amichevoli = 0.0
        self.ritmo_sfide = costanti.SFIDE_GIOCATE_AL_MESE * PRESENZA_SFIDE / costanti.GIORNI_PER_MESE

    # L'esperienza, con e senza il tetto.

    def _esperienza(self, quanto):
        self.esperienza_libera += quanto
        self.g.esperienza = min(costanti.ESPERIENZA_MASSIMA, self.esperienza_libera)

    def _punti(self, fonte, grezzi):
        self.grezzi[fonte] += grezzi
        self.g.punti_allenamento += grezzi * self.fattori[fonte]
        self.g.costanza += (1.0 - costanti.DECADIMENTO_COSTANZA) * costanti.COSTANZA_PER_PARTITA

    def _punti_di_un_singolare(self, risultato, avversario, importanza):
        """I punti grezzi della formula per la carriera, col premio al più debole, per l'importanza."""
        mio = "A" if risultato.parti[0] == self.g.id else "B"
        giocati = risultato.set[:risultato.set_giocati]
        miei = sum(1 for a, b in giocati if (a > b) == (mio == "A"))
        suoi = len(giocati) - miei
        if risultato.vincitore == mio:
            punti, _altri = MotorePartita.punti_della_partita(miei, suoi)
        else:
            _altri, punti = MotorePartita.punti_della_partita(suoi, miei)
        if MotorePartita.piu_debole(self.g, avversario) is self.g:
            punti += costanti.PA_BONUS_PIU_DEBOLE
        return punti * importanza, risultato.vincitore == mio

    # Il giorno.

    def gioca(self):
        g = self.g
        oggi = DATA_INIZIO
        edizioni = _CONTESTO["edizioni"]
        prossima_apertura = 0
        aperte = []
        mondiali = [ed for ed in edizioni if ed.qualificazione == modelli_torneo.PUNTI_ANNO and ed.sesso == g.sesso]
        for giorno in range(self.giorni):
            oggi = DATA_INIZIO + datetime.timedelta(days=giorno)
            while prossima_apertura < len(edizioni) and edizioni[prossima_apertura].data_apertura <= oggi:
                aperte.append(edizioni[prossima_apertura])
                prossima_apertura += 1
            aperte = [ed for ed in aperte if ed.data_inizio > oggi]
            g.punti_allenamento += costanti.PA_SEDUTA
            self.seduta += costanti.PA_SEDUTA
            g.costanza = g.costanza * costanti.DECADIMENTO_COSTANZA + (1 - costanti.DECADIMENTO_COSTANZA)
            self._esperienza(esperienza._PER_GIORNO_DI_VITA + self.esperienze["club"] * FATTORE_GRUPPO)
            self.conteggi["giorni"] += FATTORE_GRUPPO
            self._mondiale_che_apre(mondiali, oggi)
            self._iscrizione_automatica(aperte, oggi)
            impegnato = self._sorteggi_e_giornata(oggi)
            if not impegnato:
                impegnato = self._sfida()
            if not impegnato:
                self._amichevole()
            allenamento.allena_secondo_programma(g, programma="completa")
            if giorno % 30 == 29:
                allenamento.mantenimento_del_mese(g, 30)
            g.eta += 1
            anni = round(g.eta / GIORNI_ANNO, 6)
            if self.coda_da is not None and anni >= self.coda_da:
                self.coda.append((anni, classe.somma_classe(g), self.esperienza_libera))
            if anni in self.tappe_chieste:
                g.aggiorna_icv()
                self.registro[int(anni)] = {"somma": classe.somma_classe(g), "valore": g.indice_collettivo_valore, "esperienza": self.esperienza_libera,
                                            "classe": classe.classe(g).codice}
        g.aggiorna_icv()
        return self

    def punti_dell_anno(self, oggi):
        """I punti della classifica dell'ultimo anno fino a oggi, come palmares.punti_dell_anno."""
        limite = oggi.toordinal() - costanti.GIORNI_PUNTI_RECENTI
        return sum(punti for giorno, punti in self.punti_recenti if giorno > limite)

    def _mondiale_che_apre(self, mondiali, oggi):
        """
        All'apertura del mondiale del suo sesso, la convocazione come nel mondo: se i punti dell'ultimo
        anno passano quelli del trentaduesimo convocato del mondo a regime; un'iscrizione che si
        sovrappone lascia il posto.
        """
        for ed in mondiali:
            if ed.data_apertura == oggi and self.punti_dell_anno(oggi) >= costanti.PUNTI_PER_IL_MONDIALE[self.g.sesso]:
                self.mondiale = ed
                if self.iscrizione is not None and self.iscrizione.data_inizio <= ed.data_fine and ed.data_inizio <= self.iscrizione.data_fine:
                    self.iscrizione = None

    def _impegni(self):
        impegni = []
        if self.mondiale is not None:
            impegni.append((self.mondiale.data_inizio, self.mondiale.data_fine))
        if self.torneo is not None:
            inizio = datetime.date.fromisoformat(self.torneo.data_inizio)
            impegni.append((inizio, inizio + datetime.timedelta(days=self._durata_del_torneo - 1)))
        return impegni

    def _iscrizione_automatica(self, aperte, oggi):
        """L'iscrizione automatica del punto 5.3: in attesa con la data del ritmo vuota o entro una settimana; nove volte su dieci si iscrive, la decima salta il turno."""
        if self.iscrizione is not None:
            return
        limite = oggi + datetime.timedelta(days=costanti.GIORNI_ANTICIPO_ISCRIZIONE)
        if self.prossimo is not None and self.prossimo > limite:
            return
        domani = oggi + datetime.timedelta(days=1)
        s = max(domani, self.prossimo) if self.prossimo is not None else domani
        individuali = [ed for ed in aperte if ed.individuale and ed.qualificazione == modelli_torneo.NESSUNA]
        ed = iscrizioni.scegli(individuali, self.g, s, self._impegni())
        if ed is None:
            return
        self.contatore_tornei += QUOTA_TORNEI
        if self.contatore_tornei >= 1.0 - 1e-9:
            self.contatore_tornei -= 1.0
            self.iscrizione = ed
        else:
            # Salta il turno: aspetta i suoi due mesi come se l'avesse giocato.
            self.storia["salti"] += 1
            self._aggiorna_ritmo(ed)

    def _aggiorna_ritmo(self, ed):
        scarto = self.rng.randint(-costanti.SCARTO_FRA_TORNEI, costanti.SCARTO_FRA_TORNEI)
        nuova = ed.data_inizio + datetime.timedelta(days=costanti.GIORNI_FRA_TORNEI + scarto)
        if self.prossimo is None or self.prossimo < nuova:
            self.prossimo = nuova

    def _sorteggi_e_giornata(self, oggi):
        """Il sorteggio dell'edizione che comincia oggi, e la giornata del torneo in corso; vero se la carriera ha giocato oggi."""
        if self.mondiale is not None and self.mondiale.data_inizio < oggi:
            self.mondiale = None
        if self.torneo is None:
            if self.mondiale is not None and self.mondiale.data_inizio == oggi:
                self._sorteggia(self.mondiale, _CONTESTO["primi"][self.g.sesso])
                self.mondiale = None
                self.storia["mondiali"] += 1
                if self.storia["primo_mondiale"] is None:
                    self.storia["primo_mondiale"] = self.g.eta_anni
            elif self.iscrizione is not None and self.iscrizione.data_inizio == oggi:
                ed = self.iscrizione
                self.iscrizione = None
                self._aggiorna_ritmo(ed)
                pool = _CONTESTO["tutti"] if ed.sesso == "aperto" else _CONTESTO["per_sesso"][self.g.sesso]
                self._sorteggia(ed, self.rng.sample(pool, min(len(pool), ed.tetto - 1)))
            elif self.iscrizione is not None and self.iscrizione.data_inizio < oggi:
                self.iscrizione = None
        if self.torneo is None:
            return False
        giocato = [False]
        torneo = self.torneo
        importanza = torneo.modello["importanza"]
        per_id = self._per_id

        def gioca(incontro, azioni):
            a, b = per_id[incontro.a], per_id[incontro.b]
            formato = formato_singolare(incontro.set_al_meglio)
            iniziali = {gid: round(costanti.FATICA_RESIDUA_GIORNATA * n) for gid, n in azioni.items() if n} or None
            if self.g.id in (a.id, b.id):
                r = Incontro(a, b, formato, seme=incontro.seme, dettaglio=ESSENZIALE, azioni_iniziali=iniziali).gioca()
                avversario = b if a is self.g else a
                grezzi, vinto = self._punti_di_un_singolare(r, avversario, importanza)
                self._punti(esperienza.TORNEO, grezzi)
                if torneo.modello["qualificazione"] == modelli_torneo.PUNTI_ANNO:
                    self.grezzi_mondiale += grezzi
                self._esperienza(self.esperienze["incontri_torneo"] * importanza)
                self.conteggi["incontri_torneo"] += importanza
                self.storia["incontri_torneo"] += 1
                self.storia["vinti_torneo"] += vinto
                giocato[0] = True
            else:
                r = esito_rapido.gioca(a, b, formato, incontro.seme, azioni_iniziali=iniziali, memoria=self._memoria)
            return {"esito": r.esito, "vince": r.vincitore, "set": [list(s) for s in r.set], "set_giocati": r.set_giocati,
                    "azioni": {gid: r.statistiche[gid].azioni for gid in r.parti}}

        _giocati, finito = torneo.giornata(gioca, oggi)
        if finito:
            self._chiudi(torneo, importanza)
            self.torneo = None
        return giocato[0]

    def _sorteggia(self, ed, avversari):
        """La sede della carriera: lei e gli avversari, con la forza dal punteggio di classe, il seme e l'edizione."""
        partecipanti = [self.g, *avversari][:ed.tetto]
        punteggi = _CONTESTO["punteggi"]
        info = {p.id: {"nome": f"{p.nome} {p.cognome}", "sesso": p.sesso, "club": None, "forza": classe.punteggio(p) if p is self.g else punteggi[p.id], "pagato": 0}
                for p in partecipanti}
        self.id_torneo += 1
        self.torneo = tornei.Torneo(self.id_torneo, ed.id, 1, ed.modello, ed.formula, ed.data_inizio, self.rng.getrandbits(63), info)
        self._per_id = {p.id: p for p in partecipanti}
        self._memoria = {}
        self._durata_del_torneo = ed.durata
        self.storia["tornei"] += 1

    def _chiudi(self, torneo, importanza):
        """La chiusura: l'esperienza delle fasi superate e del piazzamento, per l'importanza; le medaglie e i titoli per il racconto."""
        if torneo.stato != tornei.CONCLUSO:
            return
        posto = torneo.classifica_finale.index(self.g.id) + 1
        self.punti_recenti.append((datetime.date.fromisoformat(torneo.data_inizio).toordinal(), palmares.punti_classifica(posto, importanza)))
        fasi = torneo.fasi_superate().get(self.g.id, 0)
        self._esperienza(self.esperienze["fasi"] * fasi * importanza)
        self.conteggi["fasi"] += fasi * importanza
        scala = esperienza.premio_piazzamento(posto) / costanti.ESPERIENZA_PIAZZAMENTO_BASE
        self._esperienza(self.esperienze["piazzamenti"] * scala * importanza)
        self.conteggi["piazzamenti"] += scala * importanza
        medaglie = ("oro", "argento", "bronzo", "legno")
        if posto <= len(medaglie):
            self.storia["medaglie"][medaglie[posto - 1]] += 1
            if posto == 1 and torneo.modello["qualificazione"] == modelli_torneo.PUNTI_ANNO:
                self.storia["titoli_mondiali"] += 1

    def _sfida(self):
        """Una sfida della sua polisportiva, al ritmo misurato, con la sua presenza: la gara a squadre col motore. Vero se l'ha giocata."""
        self.contatore_sfide += self.ritmo_sfide
        if self.contatore_sfide < 1.0:
            return False
        self.contatore_sfide -= 1.0
        g = self.g
        stesso = _CONTESTO["per_sesso"][g.sesso]
        altro = _CONTESTO["per_sesso"]["f" if g.sesso == "m" else "m"]
        compagni = [self.rng.choice(stesso), self.rng.choice(altro)]
        if self.rng.random() < 0.5:
            avversari = [*self.rng.sample(stesso, 2), self.rng.choice(altro)]
        else:
            avversari = [*self.rng.sample(altro, 2), self.rng.choice(stesso)]
        nostri = [g, *compagni]
        if len({p.id for p in nostri + avversari}) < 6 or not composizione_valida(nostri) or not composizione_valida(avversari):
            return False
        r = Incontro(Squadra("noi", tuple(nostri)), Squadra("loro", tuple(avversari)), SQUADRE, seme=self.rng.getrandbits(63), dettaglio=ESSENZIALE).gioca()
        vinto = r.vincitore == "A"
        pa_vinc, pa_perd = MotorePartita.punti_della_partita(1, 0)
        self._punti(esperienza.SFIDA, pa_vinc if vinto else pa_perd)
        self._esperienza(self.esperienze["sfide"])
        self.conteggi["sfide"] += 1.0
        self.storia["sfide"] += 1
        self.storia["sfide_vinte"] += vinto
        return True

    def _amichevole(self):
        """L'amichevole nel 90 per cento dei giorni liberi, col contatore fisso, contro un avversario del mondo all'anno 10."""
        self.contatore_amichevoli += QUOTA_AMICHEVOLI
        if self.contatore_amichevoli < 1.0 - 1e-9:
            return
        self.contatore_amichevoli -= 1.0
        avversario = self.rng.choice(_CONTESTO["amichevoli"])
        r = simula_incontro(self.g, avversario, formato_singolare(3), seme=self.rng.getrandbits(63), dettaglio=ESSENZIALE)
        grezzi, _vinto = self._punti_di_un_singolare(r, avversario, 1.0)
        self._punti(esperienza.AMICHEVOLE, grezzi)
        self._esperienza(self.esperienze["amichevoli"])
        self.conteggi["amichevoli"] += 1.0
        self.storia["amichevoli"] += 1

    # Il riassunto.

    def eta_di_a1(self, somma_perfetta=None):
        """L'età in cui la carriera arriva ad A1; se a 50 anni non ci arriva, la stima in linea retta sull'ultimo anno."""
        somma_perfetta = somma_perfetta or costanti.SOMMA_CARRIERA_PERFETTA
        for anni, somma, esp in self.coda:
            if punteggio(somma, esp, somma_perfetta) >= 1.0:
                return anni
        anni, somma, esp = self.coda[-1]
        prima = next((c for c in self.coda if c[0] >= anni - 1.0), self.coda[0])
        p_ora, p_prima = punteggio(somma, esp, somma_perfetta), punteggio(prima[1], prima[2], somma_perfetta)
        pendenza = (p_ora - p_prima) / max(1e-6, anni - prima[0])
        return anni + (1.0 - p_ora) / max(1e-6, pendenza)

    def riassunto(self):
        return {"grezzi": dict(self.grezzi), "grezzi_mondiale": self.grezzi_mondiale, "conteggi": dict(self.conteggi), "esperienza_libera": self.esperienza_libera,
                "seduta": self.seduta, "eta_a1": self.eta_di_a1() if self.coda else None, "tappe": self.registro, "storia": self.storia,
                "somma_50": classe.somma_classe(self.g), "somma_50_prima": somma_classe_prima(self.g), "id": self.g.id, "fattori": dict(self.fattori),
                "punti_totali": self.seduta + sum(self.grezzi[f] * self.fattori[f] for f in self.grezzi)}


def _nato_di_riferimento(seme, ipovedente=False):
    return al_percentile([g for g in nati(4000, seme) if senza_tratti(g) and g.ipovedente == ipovedente], 0.9)


def gioca_una_carriera(seme, ipovedente, fattori, esperienze, giorni=GIORNI_CARRIERA, estrazione=0):
    """
    Una carriera in un processo, col contesto già pronto: il riassunto, col seme del nato e l'estrazione.
    L'estrazione zero gioca col caso di prima, seme; le altre col caso seme-estrazione.
    """
    imposta_fonti(fattori, esperienze)
    coda_da = 30.0 if giorni >= GIORNI_CARRIERA else ETA_INGRESSO
    caso = seme if estrazione == 0 else f"{seme}-{estrazione}"
    riassunto = Carriera(_nato_di_riferimento(seme, ipovedente), caso, fattori, esperienze, giorni=giorni, coda_da=coda_da).gioca().riassunto()
    riassunto["seme"], riassunto["estrazione"] = seme, estrazione
    return riassunto


def _media(gruppo, seme=None):
    """
    Le medie di un gruppo di carriere: età di A1, con la più giovane e la più vecchia, punti totali,
    seduta, punti grezzi e conteggi dell'esperienza, esperienza senza tetto, mondiali; e la carriera che
    lo rappresenta, quella con l'età di A1 più vicina alla media.
    """
    eta = statistics.fmean(c["eta_a1"] for c in gruppo)
    return {
        "seme": seme, "id": gruppo[0]["id"] if seme is not None else None, "carriere": gruppo, "eta_a1": eta, "eta_a1_min": min(c["eta_a1"] for c in gruppo),
        "eta_a1_max": max(c["eta_a1"] for c in gruppo), "punti_totali": statistics.fmean(c["punti_totali"] for c in gruppo),
        "seduta": statistics.fmean(c["seduta"] for c in gruppo), "esperienza_libera": statistics.fmean(c["esperienza_libera"] for c in gruppo),
        "grezzi": {f: statistics.fmean(c["grezzi"][f] for c in gruppo) for f in gruppo[0]["grezzi"]},
        "grezzi_mondiale": statistics.fmean(c["grezzi_mondiale"] for c in gruppo),
        "conteggi": {k: statistics.fmean(c["conteggi"][k] for c in gruppo) for k in gruppo[0]["conteggi"]},
        "mondiali": statistics.fmean(c["storia"]["mondiali"] for c in gruppo),
        "rappresentante": min(gruppo, key=lambda c: abs(c["eta_a1"] - eta)),
    }


def medie_per_nato(carriere):
    """Le carriere raccolte per nato, con le medie delle sue estrazioni, come _media, e il seme e il numero del nato."""
    per_nato = {}
    for c in carriere:
        per_nato.setdefault(c["seme"], []).append(c)
    return sorted((_media(gruppo, seme) for seme, gruppo in per_nato.items()), key=lambda m: m["seme"])


def media_di_tutte(carriere):
    """
    Le medie di tutte le carriere date, come _media, senza seme né numero del nato: il bersaglio della
    decisione 6 di Gabriele del 14 ottobre 2026, la media di tutte le carriere vedenti ad A1 a 50 anni.
    """
    return _media(list(carriere))


def prossimo_totale(punti, bersaglio=ETA_A1_BERSAGLIO, passo_massimo=0.15):
    """
    Il logaritmo del totale da provare al passo seguente, dalle coppie già misurate di logaritmo del
    totale ed età media di A1. Con una coppia sola, la pendenza di prima stima: un logaritmo in più toglie
    25 anni. Con due o più, la retta ai minimi quadrati su tutte, che con due è la secante; se la sua
    pendenza non scende, o scende meno di un anno per logaritmo, torna la prima stima. Il passo resta
    entro passo_massimo dall'ultimo logaritmo provato.
    """
    ultimo = punti[-1][0]
    if len(punti) == 1:
        nuovo = ultimo + (punti[0][1] - bersaglio) / 25.0
    else:
        mx = statistics.fmean(x for x, _y in punti)
        my = statistics.fmean(y for _x, y in punti)
        varianza = sum((x - mx) ** 2 for x, _y in punti)
        pendenza = sum((x - mx) * (y - my) for x, y in punti) / varianza if varianza > 1e-12 else -25.0
        if pendenza >= -1.0:
            pendenza = -25.0
        nuovo = mx + (bersaglio - my) / pendenza
    return max(ultimo - passo_massimo, min(ultimo + passo_massimo, nuovo))


def gioca_le_carriere(esecutore, semi, ipovedente, fattori, esperienze, giorni, estrazioni):
    """Tutte le carriere dei nati dati, ciascuno con le sue estrazioni, sui processi dell'esecutore."""
    futuri = [esecutore.submit(gioca_una_carriera, seme, ipovedente, fattori, esperienze, giorni, k) for seme in semi for k in range(estrazioni)]
    return [f.result() for f in futuri]


# Il metodo del punto 10.4.

def fattori_per_totale(totale, seduta, grezzi):
    """I fattori delle tre fonti che danno il totale con la seduta fissa, nelle proporzioni di D32, dai punti grezzi."""
    partite = totale - seduta
    somma_quote = sum(QUOTE_PARTITE.values())
    return {fonte: partite * quota / somma_quote / max(1e-9, grezzi[fonte]) for fonte, quota in QUOTE_PARTITE.items()}


def esperienze_dai_conteggi(conteggi):
    """Le costanti dell'esperienza che danno a 50 anni le quote del punto 10.3, fonte per fonte, dai conteggi grezzi."""
    return {"amichevoli": ESPERIENZA_AMICHEVOLI / max(1e-9, conteggi["amichevoli"]), "sfide": ESPERIENZA_SFIDE / max(1e-9, conteggi["sfide"]),
            "club": ESPERIENZA_CLUB / max(1e-9, conteggi["giorni"]),
            **{voce: ESPERIENZA_TORNEI * quota / max(1e-9, conteggi[voce]) for voce, quota in PARTI_DEI_TORNEI.items()}}


def costruisci_contesto(fattori, esperienze, quanti, attivi, predefinito, stampa):
    """I mondi sintetici del giro, coi fattori e le esperienze del giro: all'anno 10 per le amichevoli, a regime per i tornei, le sfide e il mondiale."""
    imposta_fonti(fattori, esperienze)
    inizio = time.perf_counter()
    mondo_10 = mondo_sintetico(quanti, 10, 2026)
    regime = mondo_sintetico(attivi, None, 2027, primo_id=600_000, candidati=int(attivi * 3.5))
    for g in regime:
        g.aggiorna_icv()
    stampa(f"Mondi sintetici del giro: {len(mondo_10)} giocatori all'anno 10 e {len(regime)} a regime, pronti in {numero(time.perf_counter() - inizio)} secondi.")
    return contesto_in_dizionari(mondo_10, regime, predefinito), mondo_10, regime


# Il ricalcolo della classe, decisione 7 di Gabriele del 14 ottobre 2026.

def classe_da_ricalcolare():
    """Vero finché costanti.py ha la somma e le ancore della tappa 11: il ricalcolo della decisione 7 si fa una volta sola."""
    somma, ancore = classe_in_vigore()
    return somma == SOMMA_CARRIERA_PERFETTA_PRIMA and ancore == ANCORE_CLASSE_PRIMA


def casi_dei_nati():
    """I 4.000 nati del seme 11 dei casi tipici, e fra quelli senza tratti il mediano e il bravo, al settantacinquesimo percentile."""
    nati_11 = nati(4000, 11)
    puliti = [g for g in nati_11 if senza_tratti(g)]
    return nati_11, al_percentile(puliti, 0.5), al_percentile(puliti, 0.75)


def bravo_dell_utente(bravo, fattori, anni):
    """Il caso tipico del bravo dell'utente all'età data: dai 15 anni, con un'amichevole ogni due giorni e le gare del mondo."""
    amichevole_bravo = 0.5 * PUNTI_AMICHEVOLE_BRAVO * fattori[esperienza.AMICHEVOLE]
    return allena_a_passi(pronto(bravo, 15), 15, anni, 1.0 + amichevole_bravo, "completa", amichevoli_al_giorno=0.5, gare=1.0)


def somma_convertita(carriere):
    """
    La somma della carriera perfetta coi pesi nuovi: quella congelata della tappa 11 per il rapporto medio,
    sulle carriere date, fra la somma a 50 anni coi pesi nuovi e quella coi pesi di prima, arrotondata per
    difetto al decimo come nella tappa 11. Restituisce la somma e i rapporti di tutte le carriere.
    """
    rapporti = [c["somma_50"] / c["somma_50_prima"] for c in carriere if c["somma_50_prima"] > 0]
    return math.floor(SOMMA_CARRIERA_PERFETTA_PRIMA * statistics.fmean(rapporti) * 10) / 10, rapporti


def ancore_ricalcolate(somma, nati_del_seme, bravo_a_35):
    """
    Le ancore della classe coi pesi nuovi e con la somma nuova, arrotondate per difetto al millesimo come
    nella tappa 11, perché chi fa da ancora stia nel suo livello. I nati del primo e del novantanovesimo
    percentile per somma della classe, senza esperienza, si rifanno per definizione. Il bravo dell'utente a
    35 anni si converte: l'ancora di prima più la differenza della sua parte del valore, il 70 per cento
    del valore pesato sulla somma, fra i pesi nuovi con la somma nuova e i pesi di prima con la somma di
    prima; la parte dell'esperienza non cambia. Restituisce le ancore e i punteggi esatti, per le prove.
    """
    somme = sorted(classe.somma_classe(g) for g in nati_del_seme)
    primo = punteggio(somme[len(somme) // 100], 0.0, somma)
    novantanovesimo = punteggio(somme[len(somme) * 99 // 100], 0.0, somma)
    livello_bravo = ANCORA_DEL_BRAVO[0]
    bravo = dict(ANCORE_CLASSE_PRIMA)[livello_bravo] + costanti.PESO_VALORE_CLASSE * (
        classe.somma_classe(bravo_a_35) / somma - somma_classe_prima(bravo_a_35) / SOMMA_CARRIERA_PERFETTA_PRIMA)
    esatti = {89: primo, 50: novantanovesimo, livello_bravo: bravo}
    ancore = ((100, 0.0), *((n, math.floor(p * 1000) / 1000) for n, p in sorted(esatti.items(), reverse=True)), (1, 1.0))
    return ancore, esatti


def passi_dei_livelli(ancore):
    """Quanto vale un livello nei tre tratti fra le ancore di mezzo: fra I9 e F0, fra F0 e D0, fra D0 e A1."""
    (_n0, _s0), (n1, s1), (n2, s2), (n3, s3), (n4, s4) = ancore
    return (s2 - s1) / (n1 - n2), (s3 - s2) / (n2 - n3), (s4 - s3) / (n3 - n4)


def ricalcola_classe(argomenti, stampa):
    """
    Il ricalcolo una tantum della decisione 7: con i fattori e le esperienze in vigore gioca tutte le
    carriere vedenti, converte la somma e l'ancora del bravo ai pesi nuovi della classe, rifà le ancore dei
    nati e mette la classe nuova in questo processo, così la ricerca che segue gira con lei. Restituisce la
    somma, le ancore e i punteggi esatti. Se costanti.py ha già una classe ricalcolata, si ferma.
    """
    if not classe_da_ricalcolare():
        raise SystemExit("La classe è già stata ricalcolata una volta, decisione 7 di Gabriele del 14 ottobre 2026: la somma e le ancore di costanti.py "
                         "restano congelate.")
    fattori, esperienze = fonti_in_vigore()
    predefinito = calendario_predefinito(argomenti.giorni)
    contesto, _mondo_10, _regime = costruisci_contesto(fattori, esperienze, argomenti.giocatori, argomenti.attivi, predefinito, stampa)
    with concurrent.futures.ProcessPoolExecutor(max_workers=argomenti.processi, initializer=prepara_contesto, initargs=(contesto,)) as esecutore:
        carriere = gioca_le_carriere(esecutore, argomenti.semi, False, fattori, esperienze, argomenti.giorni, argomenti.estrazioni)
    eta_prima = statistics.fmean(c["eta_a1"] for c in carriere)
    somma, rapporti = somma_convertita(carriere)
    nati_11, _mediano, bravo = casi_dei_nati()
    bravo_a_35 = bravo_dell_utente(bravo, fattori, ANCORA_DEL_BRAVO[1])
    ancore, esatti = ancore_ricalcolate(somma, nati_11, bravo_a_35)
    imposta_classe(somma, ancore)
    passi = passi_dei_livelli(ancore)
    stampa(f"Il ricalcolo della classe, decisione 7: {len(carriere)} carriere vedenti coi fattori in vigore; il rapporto fra la somma a 50 anni coi pesi "
           f"nuovi e quella coi pesi della tappa 11 va da {numero(min(rapporti), 4)} a {numero(max(rapporti), 4)}, in media {numero(statistics.fmean(rapporti), 4)}; "
           f"la somma congelata passa da {numero(SOMMA_CARRIERA_PERFETTA_PRIMA)} a {numero(somma)}. Coi pesi nuovi e la somma di prima le carriere arrivavano "
           f"ad A1 in media a {numero(eta_prima, 2)} anni.")
    stampa(f"Le ancore nuove, punteggi esatti: nato del primo percentile {numero(esatti[89], 6)}, del novantanovesimo {numero(esatti[50], 6)}, il bravo "
           f"dell'utente a {ANCORA_DEL_BRAVO[1]} anni, convertito, {numero(esatti[ANCORA_DEL_BRAVO[0]], 6)}; per confronto, il suo punteggio per definizione "
           f"col caso tipico di adesso sarebbe {numero(classe.punteggio(bravo_a_35), 6)}. Arrotondate per difetto al millesimo: {ancore!r}. Un livello vale "
           f"{numero(passi[0], 4)} di punteggio fra I9 e F0, {numero(passi[1], 4)} fra F0 e D0, {numero(passi[2], 4)} fra D0 e A1"
           + ("; i livelli si allargano dal basso verso l'alto, come vuole D31." if passi[0] < passi[1] < passi[2] else
              "; ATTENZIONE, i livelli NON si allargano dal basso verso l'alto, come vorrebbe D31."))
    return somma, ancore, esatti


def esegui(argomenti, stampa):
    """
    La ricerca dei fattori e delle esperienze, giro per giro, sulla media di tutte le carriere vedenti,
    decisione 6 di Gabriele del 14 ottobre 2026; alla fine i mondi sintetici rifatti coi fattori trovati e
    tutte le carriere rigiocate. Restituisce i fattori, le esperienze, le medie per nato delle carriere
    vedenti e delle ipovedenti, i mondi della verifica e la storia.
    """
    fattori, esperienze = fonti_in_vigore()
    predefinito = calendario_predefinito(argomenti.giorni)
    storia = []
    totale = None
    contesto = mondo_10 = regime = None
    for giro in range(1, argomenti.giri + 1):
        contesto, mondo_10, regime = costruisci_contesto(fattori, esperienze, argomenti.giocatori, argomenti.attivi, predefinito, stampa)
        stampa(f"Giro {giro}: i mondiali si giocano coi punti dell'ultimo anno, soglia {numero(costanti.PUNTI_PER_IL_MONDIALE['m'], 0)} per gli uomini e "
               f"{numero(costanti.PUNTI_PER_IL_MONDIALE['f'], 0)} per le donne; il punteggio di classe del trentaduesimo del mondo sintetico, la regola di prima, "
               f"sarebbe {numero(contesto['soglie']['m'], 4)} e {numero(contesto['soglie']['f'], 4)}.")
        fattori_di_inizio_giro = dict(fattori)
        with concurrent.futures.ProcessPoolExecutor(max_workers=argomenti.processi, initializer=prepara_contesto, initargs=(contesto,)) as esecutore:
            punti_del_giro = []
            for passo in range(1, argomenti.passi + 1):
                carriere = gioca_le_carriere(esecutore, argomenti.semi, False, fattori, esperienze, argomenti.giorni, argomenti.estrazioni)
                medie = medie_per_nato(carriere)
                tutte = media_di_tutte(carriere)
                eta = tutte["eta_a1"]
                totale_giocato = tutte["punti_totali"]
                punti_del_giro.append((math.log(totale_giocato), eta))
                dopo_i_50 = sum(1 for c in carriere if c["eta_a1"] > ETA_USCITA) / len(carriere)
                stampa(f"Giro {giro}, passo {passo}: fattori torneo {numero(fattori[esperienza.TORNEO], 3)}, amichevole {numero(fattori[esperienza.AMICHEVOLE], 3)}, "
                       f"sfida {numero(fattori[esperienza.SFIDA], 3)}; su tutte le {len(carriere)} carriere vedenti totale medio {numero(totale_giocato, 0)} punti, "
                       f"età media di A1 {numero(eta, 2)}, esperienza media a 50 anni senza tetto {numero(tutte['esperienza_libera'], 2)}; età media di A1 per nato "
                       + ", ".join(numero(m["eta_a1"], 2) for m in medie) + f"; carriere dopo i 50 anni {numero(100 * dopo_i_50, 0)} per cento.")
                nuove_esperienze = esperienze_dai_conteggi(tutte["conteggi"])
                totale = math.exp(prossimo_totale(punti_del_giro))
                nuovi_fattori = fattori_per_totale(totale, tutte["seduta"], tutte["grezzi"])
                spostamento = max(abs(nuovi_fattori[f] / fattori[f] - 1.0) for f in fattori)
                spostamento_esp = max(abs(nuove_esperienze[k] / esperienze[k] - 1.0) for k in esperienze)
                storia.append({"giro": giro, "passo": passo, "eta": eta, "totale": totale_giocato, "fattori": dict(fattori)})
                if abs(eta - ETA_A1_BERSAGLIO) <= TOLLERANZA_ETA and spostamento <= TOLLERANZA_FATTORI and spostamento_esp <= 3 * TOLLERANZA_FATTORI:
                    break
                fattori, esperienze = nuovi_fattori, nuove_esperienze
        spostamento_giro = max(abs(fattori[f] / fattori_di_inizio_giro[f] - 1.0) for f in fattori)
        stampa(f"Fine del giro {giro}: i fattori si sono spostati al più del {numero(100 * spostamento_giro, 1)} per cento dall'inizio del giro.")
        if giro > 1 and spostamento_giro <= TOLLERANZA_FATTORI:
            break
    # La verifica: i mondi sintetici rifatti coi fattori trovati, come li farebbe chi rilancia lo
    # strumento con costanti.py aggiornato, e tutte le carriere rigiocate su quei mondi.
    contesto, mondo_10, regime = costruisci_contesto(fattori, esperienze, argomenti.giocatori, argomenti.attivi, predefinito, stampa)
    with concurrent.futures.ProcessPoolExecutor(max_workers=argomenti.processi, initializer=prepara_contesto, initargs=(contesto,)) as esecutore:
        vedenti = medie_per_nato(gioca_le_carriere(esecutore, argomenti.semi, False, fattori, esperienze, argomenti.giorni, argomenti.estrazioni))
        ipovedenti = medie_per_nato(gioca_le_carriere(esecutore, SEMI_IPOVEDENTI, True, fattori, esperienze, argomenti.giorni, min(3, argomenti.estrazioni)))
    return fattori, esperienze, vedenti, ipovedenti, mondo_10, regime, storia


# Il racconto.

def lettere(giocatori):
    conta = {}
    for g in giocatori:
        lettera = classe.classe(g).codice[0]
        conta[lettera] = conta.get(lettera, 0) + 1
    return ", ".join(f"{lettera} {numero(100 * quanti / len(giocatori))}" for lettera, quanti in sorted(conta.items()))


def blocco_costanti(fattori, esperienze, ricalcolo=None):
    """
    Le righe da copiare in costanti.py; dopo --ricalcola-classe anche la somma e le ancore della classe, e
    i punteggi esatti di chi fa da ancora per ANCORE_ESATTE di tests/test_classe.py.
    """
    righe = ["Il blocco da copiare in costanti.py:",
             f"PA_FATTORE_AMICHEVOLE = {fattori[esperienza.AMICHEVOLE]:.3f}", f"PA_FATTORE_TORNEO = {fattori[esperienza.TORNEO]:.3f}",
             f"PA_FATTORE_SFIDA = {fattori[esperienza.SFIDA]:.3f}", f"ESPERIENZA_PER_AMICHEVOLE = {esperienze['amichevoli']:.6f}",
             f"ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA = {esperienze['club']:.6f}", f"ESPERIENZA_PER_SFIDA = {esperienze['sfide']:.5f}",
             f"ESPERIENZA_PER_PARTITA_TORNEO = {esperienze['incontri_torneo']:.5f}", f"ESPERIENZA_PER_FASE_SUPERATA = {esperienze['fasi']:.5f}",
             f"ESPERIENZA_PIAZZAMENTO_BASE = {esperienze['piazzamenti']:.5f}"]
    if ricalcolo is not None:
        somma, ancore, esatti = ricalcolo
        righe += [f"SOMMA_CARRIERA_PERFETTA = {somma}", f"ANCORE_CLASSE = {ancore!r}",
                  "E in tests/test_classe.py: ANCORE_ESATTE = (" + ", ".join(f"({n}, {p:.6f})" for n, p in sorted(esatti.items(), reverse=True)) + ")"]
    return righe


def racconta(fattori, esperienze, vedenti, ipovedenti, mondo_10, regime, storia, argomenti, scrivi, ricalcolo=None):
    """
    Le righe del racconto, sulla verifica coi mondi rifatti: le quote, le età per nato con le loro
    estrazioni, l'esperienza, la classe, il mondiale, i casi tipici e le lettere. I numeri dei bersagli
    sono le medie di tutte le carriere vedenti, decisione 6 di Gabriele del 14 ottobre 2026; la storia e
    le tappe sono della carriera più vicina alla loro età media di A1. Il nato più lento si dice a parte.
    Dopo --ricalcola-classe il blocco finale ha anche la somma e le ancore nuove.
    """
    imposta_fonti(fattori, esperienze)
    tutte = [c for m in vedenti for c in m["carriere"]]
    media = media_di_tutte(tutte)
    piu_lento = max(vedenti, key=lambda m: m["eta_a1"])
    lenta = media["rappresentante"]
    totale = media["punti_totali"]
    per_fonte = {f: media["grezzi"][f] * fattori[f] for f in fattori}
    dopo_i_50 = sum(1 for c in tutte if c["eta_a1"] > ETA_USCITA)
    ricerca = f"La ricerca ha fatto {len(storia)} passi in {max(s['giro'] for s in storia)} giri" if storia else "Soltanto la verifica, coi fattori e le esperienze di costanti.py"
    scrivi(f"{ricerca}; la verifica, coi mondi sintetici rifatti coi fattori trovati, ha giocato "
           f"{len(tutte)} carriere vedenti, {len(vedenti)} nati con {argomenti.estrazioni} estrazioni del caso ciascuno, e "
           f"{sum(len(m['carriere']) for m in ipovedenti)} carriere ipovedenti.")
    scrivi(f"La media di tutte le {len(tutte)} carriere vedenti: {numero(totale, 0)} punti allenamento in {GIORNI_CARRIERA} giorni, "
           f"{numero(totale / MESI_CARRIERA, 1)} al mese di 30 giorni; la seduta ne fa il {numero(100 * media['seduta'] / totale)} per cento, i tornei il "
           f"{numero(100 * per_fonte[esperienza.TORNEO] / totale)}, le amichevoli il {numero(100 * per_fonte[esperienza.AMICHEVOLE] / totale)}, le sfide il "
           f"{numero(100 * per_fonte[esperienza.SFIDA] / totale)}; sulla parte delle partite, le proporzioni 40, 34 e 4 di D32 diventano "
           f"{numero(78 * per_fonte[esperienza.TORNEO] / (totale - media['seduta']), 2)}, {numero(78 * per_fonte[esperienza.AMICHEVOLE] / (totale - media['seduta']), 2)} e "
           f"{numero(78 * per_fonte[esperienza.SFIDA] / (totale - media['seduta']), 2)}.")
    s = lenta["storia"]
    scrivi(f"Che cosa ha giocato la carriera più vicina all'età media di A1, nato numero {lenta['id']} del seme {lenta['seme']}, estrazione {lenta['estrazione']}, ad A1 a "
           f"{numero(lenta['eta_a1'], 2)} anni: {s['tornei']} tornei, di cui {s['mondiali']} mondiali, con "
           f"{s['incontri_torneo']} incontri e {s['vinti_torneo']} vinti; {s['salti']} turni saltati col contatore; medaglie: {s['medaglie']['oro']} ori, "
           f"{s['medaglie']['argento']} argenti, {s['medaglie']['bronzo']} bronzi, {s['medaglie']['legno']} legni, {s['titoli_mondiali']} titoli mondiali; {s['sfide']} sfide, "
           f"{s['sfide_vinte']} vinte; {s['amichevoli']} amichevoli. Un incontro di torneo vale in media "
           f"{numero(lenta['grezzi'][esperienza.TORNEO] * fattori[esperienza.TORNEO] / max(1, s['incontri_torneo']), 1)} punti, un'amichevole "
           f"{numero(lenta['grezzi'][esperienza.AMICHEVOLE] * fattori[esperienza.AMICHEVOLE] / max(1, s['amichevoli']), 2)}, una sfida "
           f"{numero(lenta['grezzi'][esperienza.SFIDA] * fattori[esperienza.SFIDA] / max(1, s['sfide']), 2)}.")
    primi = [c["storia"]["primo_mondiale"] for c in tutte if c["storia"]["primo_mondiale"]]
    scrivi(f"Il mondiale, con l'importanza 4 e la convocazione per i punti dell'ultimo anno come nel mondo: le carriere vedenti ne giocano da "
           f"{min(c['storia']['mondiali'] for c in tutte)} a {max(c['storia']['mondiali'] for c in tutte)}, in media {numero(statistics.fmean(c['storia']['mondiali'] for c in tutte), 1)}, "
           f"il primo fra {numero(min(primi), 1) if primi else 'nessuna'} e {numero(max(primi), 1) if primi else 'nessuna'} anni; nella media di tutte i mondiali fanno il "
           f"{numero(100 * media['grezzi_mondiale'] / max(1e-9, media['grezzi'][esperienza.TORNEO]))} per cento dei punti grezzi dei tornei: i punti si spostano "
           "verso la fine della carriera, come vuole Gabriele, risposta 10.")
    scrivi(f"Le {len(vedenti)} carriere vedenti, nato per nato, l'età media di A1 con la più giovane e la più vecchia delle estrazioni: " + "; ".join(
        f"nato numero {m['id']} del seme {m['seme']}, A1 in media a {numero(m['eta_a1'], 2)} anni, da {numero(m['eta_a1_min'], 2)} a {numero(m['eta_a1_max'], 2)}, "
        f"esperienza a 50 senza tetto {numero(m['esperienza_libera'], 2)}, mondiali {numero(m['mondiali'], 1)}" for m in vedenti) + ".")
    scrivi(f"Le carriere vedenti ad A1 dopo i 50 anni: {dopo_i_50} su {len(tutte)}, il {numero(100 * dopo_i_50 / len(tutte), 0)} per cento. Su tutte le carriere vedenti "
           f"l'età di A1 è in media {numero(media['eta_a1'], 2)} anni, mediana {numero(statistics.median(c['eta_a1'] for c in tutte), 2)}, dalla più giovane a "
           f"{numero(media['eta_a1_min'], 2)} alla più vecchia a {numero(media['eta_a1_max'], 2)}, e l'esperienza a 50 anni senza tetto in media "
           f"{numero(media['esperienza_libera'], 2)}. Il nato più lento, numero {piu_lento['id']} del seme {piu_lento['seme']}, arriva ad A1 in media a "
           f"{numero(piu_lento['eta_a1'], 2)} anni, con {numero(piu_lento['esperienza_libera'], 2)} di esperienza.")
    scrivi("Le carriere di nati ipovedenti, con lo sconto del 7 per cento sulle caratteristiche di gioco: " + "; ".join(
        f"nato numero {m['id']}, A1 in media a {numero(m['eta_a1'], 2)} anni, da {numero(m['eta_a1_min'], 2)} a {numero(m['eta_a1_max'], 2)}" for m in ipovedenti) + ".")
    conteggi = media["conteggi"]
    eta_parte = costanti.ESPERIENZA_PER_ANNO_DI_VITA * (ETA_USCITA - ETA_INGRESSO)
    parti = {"età": eta_parte, "amichevoli": esperienze["amichevoli"] * conteggi["amichevoli"], "sfide": esperienze["sfide"] * conteggi["sfide"],
             "club": esperienze["club"] * conteggi["giorni"], "incontri di torneo": esperienze["incontri_torneo"] * conteggi["incontri_torneo"],
             "fasi superate": esperienze["fasi"] * conteggi["fasi"], "piazzamenti": esperienze["piazzamenti"] * conteggi["piazzamenti"]}
    scrivi("L'esperienza media di tutte le carriere vedenti a 50 anni, fonte per fonte: " + ", ".join(f"{nome} {numero(v, 2)}" for nome, v in parti.items())
           + f"; i tornei insieme {numero(parti['incontri di torneo'] + parti['fasi superate'] + parti['piazzamenti'], 2)}; in tutto senza tetto "
           f"{numero(media['esperienza_libera'], 2)}.")
    for anni, t in sorted(lenta["tappe"].items()):
        scrivi(f"La carriera più vicina all'età media di A1, a {anni} anni: classe {t['classe']}, somma {numero(t['somma'], 1)}, valore {numero(t['valore'])}, "
               f"esperienza {numero(t['esperienza'], 2)}.")
    eta_dentro = BANDA_ETA_A1[0] <= media["eta_a1"] <= BANDA_ETA_A1[1]
    esperienza_dentro = BANDA_ESPERIENZA[0] <= media["esperienza_libera"] <= BANDA_ESPERIENZA[1]
    scrivi("I bersagli della decisione 6 di Gabriele del 14 ottobre 2026, sulla media di tutte le carriere vedenti: ad A1 in media fra "
           f"{numero(BANDA_ETA_A1[0], 2)} e {numero(BANDA_ETA_A1[1], 2)} anni, {'dentro' if eta_dentro else 'FUORI'}; l'esperienza media a 50 anni senza tetto fra "
           f"{numero(BANDA_ESPERIENZA[0])} e {numero(BANDA_ESPERIENZA[1])}, {'dentro' if esperienza_dentro else 'FUORI'}. Il nato più lento e le carriere dopo i 50 "
           "anni si dicono senza essere bersagli.")
    # I casi tipici, con le gare del mondo, e le lettere dei mondi sintetici.
    _nati_11, mediano, bravo = casi_dei_nati()
    amichevole_mediano = 0.5 * PUNTI_AMICHEVOLE_MEDIANO * fattori[esperienza.AMICHEVOLE]
    casi = []
    for anni in (35, 50):
        casi.append((f"mediano del computer, in polisportiva dai 20 anni, a {anni}", allena_a_passi(pronto(mediano, 20), 20, anni, 1.0, mediano.indole, gare=1.0)))
    casi.append(("libero mediano a 50 anni", allena_a_passi(pronto(mediano, 25), 25, 50, 0.5, mediano.indole, in_polisportiva=False, gare=1.0)))
    for anni in (25, 30, 35, 40):
        casi.append((f"mediano dell'utente dai 20 anni, con un'amichevole ogni due giorni e i tornei, a {anni}",
                     allena_a_passi(pronto(mediano, 20), 20, anni, 1.0 + amichevole_mediano, "completa", amichevoli_al_giorno=0.5, gare=1.0)))
    for anni in (30, 40, 50):
        casi.append((f"bravo dell'utente dai 15 anni, con un'amichevole ogni due giorni e i tornei, a {anni}", bravo_dell_utente(bravo, fattori, anni)))
    for nome, g in casi:
        scrivi(f"Caso, {nome}: classe {classe.classe(g).codice}, valore {numero(g.indice_collettivo_valore)}, esperienza {numero(g.esperienza, 2)}, stipendio {economia.stipendio(g)} euro.")
    mondi = {"all'anno 10": mondo_10, "a regime": regime}
    if not argomenti.veloce:
        for anni in (20, 40):
            mondi[f"all'anno {anni}"] = mondo_sintetico(argomenti.giocatori, anni, 2026)
    for nome, giocatori in mondi.items():
        scrivi(f"Mondo sintetico {nome}: lettere {lettere(giocatori)}; valore mediano {numero(statistics.median(g.indice_collettivo_valore for g in giocatori))}.")
    for riga in blocco_costanti(fattori, esperienze, ricalcolo):
        scrivi(riga)


def main():
    parser = argparse.ArgumentParser(description="La carriera perfetta di MESS col calendario vero: i fattori dei punti e le costanti dell'esperienza.")
    parser.add_argument("--processi", type=int, default=min(8, os.cpu_count() or 1), help="quanti processi giocano le carriere, fino a 8 se il computer li ha")
    parser.add_argument("--giri", type=int, default=3, help="i giri al più, ciascuno coi mondi sintetici rifatti, 3 se non indicati; zero per la sola verifica")
    parser.add_argument("--passi", type=int, default=10, help="i passi al più delle secanti in un giro, 10 se non indicati")
    parser.add_argument("--giocatori", type=int, default=3000, help="i giocatori del mondo sintetico all'anno 10, 3000 se non indicato")
    parser.add_argument("--attivi", type=int, default=ATTIVI_A_REGIME, help="i giocatori del mondo sintetico a regime, 20.600 se non indicato")
    parser.add_argument("--giorni", type=int, default=GIORNI_CARRIERA, help="i giorni della carriera, 4.428 se non indicato; più corta soltanto per provare lo strumento")
    parser.add_argument("--estrazioni", type=int, default=ESTRAZIONI, help="le estrazioni del caso di ogni nato, 5 se non indicato")
    parser.add_argument("--nati", type=int, default=len(SEMI_RIFERIMENTO), help="quanti nati di riferimento, i primi di SEMI_RIFERIMENTO, 10 se non indicato")
    parser.add_argument("--veloce", action="store_true", help="per provare lo strumento: mondi piccoli, un giro e due passi")
    parser.add_argument("--ricalcola-classe", action="store_true",
                        help="una volta sola, decisione 7: converte ai pesi nuovi della classe la somma e le ancore, prima della ricerca")
    parser.add_argument("--rapporto", type=Path, default=None, help="salva il racconto anche in questo file")
    argomenti = parser.parse_args()
    if argomenti.veloce:
        argomenti.giocatori, argomenti.attivi, argomenti.giri, argomenti.passi = 600, 3000, 1, 2
    argomenti.semi = SEMI_RIFERIMENTO[:max(1, argomenti.nati)]
    inizio = time.perf_counter()
    righe = []

    def scrivi(riga):
        righe.append(riga)
        print(riga, flush=True)

    cartella = tempfile.mkdtemp(prefix="mess_carriera_")
    cartella_vera = percorsi.cartella
    percorsi.cartella = lambda: cartella
    try:
        scrivi(f"Carriera perfetta col calendario vero, tappa 12: somma congelata {numero(costanti.SOMMA_CARRIERA_PERFETTA)}, sfide della polisportiva "
               f"{numero(costanti.SFIDE_GIOCATE_AL_MESE, 2)} al mese, carriere di {argomenti.giorni} giorni.")
        ricalcolo = ricalcola_classe(argomenti, scrivi) if argomenti.ricalcola_classe else None
        fattori, esperienze, carriere, ipovedenti, mondo_10, regime, storia = esegui(argomenti, scrivi)
        racconta(fattori, esperienze, carriere, ipovedenti, mondo_10, regime, storia, argomenti, scrivi, ricalcolo)
    finally:
        percorsi.cartella = cartella_vera
        shutil.rmtree(cartella, ignore_errors=True)
    scrivi(f"Misura completata in {numero(time.perf_counter() - inizio)} secondi.")
    if argomenti.rapporto:
        argomenti.rapporto.write_text("\n".join(righe) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
