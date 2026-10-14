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
somma senza il tetto di 20: l'età fa da sé, le amichevoli 2,5, le sfide 1,5, il club 5 e i tornei 9,
divisi 50 per cento agli incontri, 20 alle fasi superate e 30 ai piazzamenti. Il totale si cerca col
metodo delle secanti sul logaritmo di T; i mondi sintetici, che giocano le gare del mondo coi fattori
del giro, si rifanno a ogni giro, finché i fattori non si spostano più dell'uno per cento.
Lo strumento stampa: i fattori e le esperienze da copiare in costanti.py, le quote ottenute, la quota
della seduta, i punti al mese, l'età di A1 dei cinque semi e dei tre ipovedenti, l'esperienza a 50
anni senza tetto, la classe a 20, 30, 40 e 50 anni, quanto pesa il mondiale, i casi tipici di oggi e
le lettere dei mondi sintetici.
Uso, dalla cartella del progetto o da qualunque altra:
    python strumenti/carriera_perfetta.py --processi 8 --rapporto carriera.txt
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
ESPERIENZA_AMICHEVOLI, ESPERIENZA_SFIDE, ESPERIENZA_CLUB, ESPERIENZA_TORNEI = 2.5, 1.5, 5.0, 9.0
PARTI_DEI_TORNEI = {"incontri_torneo": 0.5, "fasi": 0.2, "piazzamenti": 0.3}
# Il bersaglio: la più lenta delle carriere vedenti ad A1 fra 49 e mezzo e 50 anni, cercata nel mezzo.
ETA_A1_BERSAGLIO = 49.75
TOLLERANZA_ETA = 0.08
TOLLERANZA_FATTORI = 0.01
# I nati di riferimento della carriera perfetta, vedenti, e gli ipovedenti, misurati per dire quando arrivano ad A1.
SEMI_RIFERIMENTO = (11, 12, 13, 21, 99)
SEMI_IPOVEDENTI = (11, 12, 13)
# Il mondo sintetico a regime grande quanto il mondo vero, per il mondiale: i primi 32 di circa 10.300 per sesso.
ATTIVI_A_REGIME = 20_600
QUALIFICATI_MONDIALE = 32
# I punti attesi per amichevole dei casi dell'utente, grezzi: il mediano 3,1 e il bravo 3,5.
PUNTI_AMICHEVOLE_MEDIANO = 3.1
PUNTI_AMICHEVOLE_BRAVO = 3.5
ANCORA_DEL_BRAVO = (30, 35)
_FISICHE = ("precisione", "resistenza", "forza")


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
    """Il contesto di un processo, dai dizionari: gli avversari delle amichevoli, quelli dei tornei per sesso, i primi per il mondiale e le soglie, le edizioni."""
    _CONTESTO.clear()
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
    """Il contesto da mandare ai processi, in dizionari: i primi 31 di ogni sesso per punteggio di classe, e la soglia del trentaduesimo."""
    primi, soglie = {}, {}
    for sesso in ("m", "f"):
        ordinati = sorted((g for g in regime if g.sesso == sesso), key=lambda g: (-classe.punteggio(g), g.id))
        primi[sesso] = [g.id for g in ordinati[:QUALIFICATI_MONDIALE - 1]]
        soglie[sesso] = classe.punteggio(ordinati[QUALIFICATI_MONDIALE - 1]) if len(ordinati) >= QUALIFICATI_MONDIALE else 0.0
    return {"amichevoli": [g.a_dizionario() for g in mondo_10], "regime": [g.a_dizionario() for g in regime], "primi": primi, "soglie": soglie,
            "calendario": predefinito}


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

    def _mondiale_che_apre(self, mondiali, oggi):
        """All'apertura del mondiale del suo sesso, la convocazione se il punteggio di classe sta fra i primi 32; un'iscrizione che si sovrappone lascia il posto."""
        for ed in mondiali:
            if ed.data_apertura == oggi and classe.punteggio(self.g) >= _CONTESTO["soglie"][self.g.sesso]:
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
                "somma_50": classe.somma_classe(self.g), "id": self.g.id, "fattori": dict(self.fattori),
                "punti_totali": self.seduta + sum(self.grezzi[f] * self.fattori[f] for f in self.grezzi)}


def _nato_di_riferimento(seme, ipovedente=False):
    return al_percentile([g for g in nati(4000, seme) if senza_tratti(g) and g.ipovedente == ipovedente], 0.9)


def gioca_una_carriera(seme, ipovedente, fattori, esperienze, giorni=GIORNI_CARRIERA):
    """Una carriera in un processo, col contesto già pronto: il riassunto."""
    imposta_fonti(fattori, esperienze)
    coda_da = 30.0 if giorni >= GIORNI_CARRIERA else ETA_INGRESSO
    return Carriera(_nato_di_riferimento(seme, ipovedente), seme, fattori, esperienze, giorni=giorni, coda_da=coda_da).gioca().riassunto()


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


def esegui(argomenti, stampa):
    """La ricerca dei fattori e delle esperienze, giro per giro: restituisce i fattori, le esperienze, i riassunti delle carriere e i mondi dell'ultimo giro."""
    fattori, esperienze = fonti_in_vigore()
    predefinito = calendario_predefinito(argomenti.giorni)
    storia = []
    totale = None
    ultimi = None
    contesto = mondo_10 = regime = None
    for giro in range(1, argomenti.giri + 1):
        contesto, mondo_10, regime = costruisci_contesto(fattori, esperienze, argomenti.giocatori, argomenti.attivi, predefinito, stampa)
        stampa(f"Giro {giro}: soglia del mondiale, il punteggio di classe del trentaduesimo, {numero(contesto['soglie']['m'], 4)} per gli uomini e "
               f"{numero(contesto['soglie']['f'], 4)} per le donne.")
        fattori_di_inizio_giro = dict(fattori)
        with concurrent.futures.ProcessPoolExecutor(max_workers=argomenti.processi, initializer=prepara_contesto, initargs=(contesto,)) as esecutore:
            punti_secante = []
            for passo in range(1, argomenti.passi + 1):
                futuri = [esecutore.submit(gioca_una_carriera, seme, False, fattori, esperienze, argomenti.giorni) for seme in SEMI_RIFERIMENTO]
                carriere = [f.result() for f in futuri]
                lenta = max(carriere, key=lambda c: c["eta_a1"])
                eta = lenta["eta_a1"]
                totale_giocato = lenta["punti_totali"]
                punti_secante.append((math.log(totale_giocato), eta))
                stampa(f"Giro {giro}, passo {passo}: fattori torneo {numero(fattori[esperienza.TORNEO], 3)}, amichevole {numero(fattori[esperienza.AMICHEVOLE], 3)}, "
                       f"sfida {numero(fattori[esperienza.SFIDA], 3)}; totale della più lenta {numero(totale_giocato, 0)} punti; età di A1 "
                       + ", ".join(numero(c["eta_a1"], 2) for c in carriere) + "; esperienza a 50 anni senza tetto "
                       + ", ".join(numero(c["esperienza_libera"], 2) for c in carriere) + ".")
                ultimi = carriere
                nuove_esperienze = esperienze_dai_conteggi(lenta["conteggi"])
                if len(punti_secante) == 1:
                    log_totale = punti_secante[-1][0] + 0.04 * (eta - ETA_A1_BERSAGLIO)
                else:
                    (x0, y0), (x1, y1) = punti_secante[-2], punti_secante[-1]
                    pendenza = (y1 - y0) / (x1 - x0) if abs(x1 - x0) > 1e-9 else -25.0
                    if pendenza >= -1.0:
                        pendenza = -25.0
                    log_totale = x1 + (ETA_A1_BERSAGLIO - y1) / pendenza
                log_totale = max(punti_secante[-1][0] - 0.15, min(punti_secante[-1][0] + 0.15, log_totale))
                totale = math.exp(log_totale)
                nuovi_fattori = fattori_per_totale(totale, lenta["seduta"], lenta["grezzi"])
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
    with concurrent.futures.ProcessPoolExecutor(max_workers=argomenti.processi, initializer=prepara_contesto, initargs=(contesto,)) as esecutore:
        futuri = [esecutore.submit(gioca_una_carriera, seme, True, fattori, esperienze, argomenti.giorni) for seme in SEMI_IPOVEDENTI]
        ipovedenti = [f.result() for f in futuri]
    return fattori, esperienze, ultimi, ipovedenti, mondo_10, regime, storia


# Il racconto.

def lettere(giocatori):
    conta = {}
    for g in giocatori:
        lettera = classe.classe(g).codice[0]
        conta[lettera] = conta.get(lettera, 0) + 1
    return ", ".join(f"{lettera} {numero(100 * quanti / len(giocatori))}" for lettera, quanti in sorted(conta.items()))


def blocco_costanti(fattori, esperienze):
    return ["Il blocco da copiare in costanti.py:",
            f"PA_FATTORE_AMICHEVOLE = {fattori[esperienza.AMICHEVOLE]:.3f}", f"PA_FATTORE_TORNEO = {fattori[esperienza.TORNEO]:.3f}",
            f"PA_FATTORE_SFIDA = {fattori[esperienza.SFIDA]:.3f}", f"ESPERIENZA_PER_AMICHEVOLE = {esperienze['amichevoli']:.6f}",
            f"ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA = {esperienze['club']:.6f}", f"ESPERIENZA_PER_SFIDA = {esperienze['sfide']:.5f}",
            f"ESPERIENZA_PER_PARTITA_TORNEO = {esperienze['incontri_torneo']:.5f}", f"ESPERIENZA_PER_FASE_SUPERATA = {esperienze['fasi']:.5f}",
            f"ESPERIENZA_PIAZZAMENTO_BASE = {esperienze['piazzamenti']:.5f}"]


def racconta(fattori, esperienze, carriere, ipovedenti, mondo_10, regime, storia, argomenti, scrivi):
    """Le righe del racconto: le quote, le età, l'esperienza, la classe, il mondiale, i casi tipici e le lettere."""
    imposta_fonti(fattori, esperienze)
    lenta = max(carriere, key=lambda c: c["eta_a1"])
    totale = lenta["punti_totali"]
    per_fonte = {f: lenta["grezzi"][f] * fattori[f] for f in fattori}
    scrivi(f"La ricerca ha fatto {len(storia)} passi in {max(s['giro'] for s in storia)} giri.")
    scrivi(f"La carriera più lenta, il nato numero {lenta['id']}: {numero(totale, 0)} punti allenamento in {GIORNI_CARRIERA} giorni, {numero(totale / MESI_CARRIERA, 1)} al mese di "
           f"30 giorni; la seduta ne fa il {numero(100 * lenta['seduta'] / totale)} per cento, i tornei il {numero(100 * per_fonte[esperienza.TORNEO] / totale)}, le amichevoli il "
           f"{numero(100 * per_fonte[esperienza.AMICHEVOLE] / totale)}, le sfide il {numero(100 * per_fonte[esperienza.SFIDA] / totale)}; sulla parte delle partite, le proporzioni "
           f"40, 34 e 4 di D32 diventano {numero(78 * per_fonte[esperienza.TORNEO] / (totale - lenta['seduta']), 2)}, "
           f"{numero(78 * per_fonte[esperienza.AMICHEVOLE] / (totale - lenta['seduta']), 2)} e {numero(78 * per_fonte[esperienza.SFIDA] / (totale - lenta['seduta']), 2)}.")
    s = lenta["storia"]
    scrivi(f"Che cosa ha giocato: {s['tornei']} tornei, di cui {s['mondiali']} mondiali, con {s['incontri_torneo']} incontri e {s['vinti_torneo']} vinti; "
           f"{s['salti']} turni saltati col contatore; medaglie: {s['medaglie']['oro']} ori, {s['medaglie']['argento']} argenti, {s['medaglie']['bronzo']} bronzi, "
           f"{s['medaglie']['legno']} legni, {s['titoli_mondiali']} titoli mondiali; {s['sfide']} sfide, {s['sfide_vinte']} vinte; {s['amichevoli']} amichevoli. "
           f"Un incontro di torneo vale in media {numero(lenta['grezzi'][esperienza.TORNEO] * fattori[esperienza.TORNEO] / max(1, s['incontri_torneo']), 1)} punti, "
           f"un'amichevole {numero(lenta['grezzi'][esperienza.AMICHEVOLE] * fattori[esperienza.AMICHEVOLE] / max(1, s['amichevoli']), 2)}, una sfida "
           f"{numero(lenta['grezzi'][esperienza.SFIDA] * fattori[esperienza.SFIDA] / max(1, s['sfide']), 2)}.")
    primo = s["primo_mondiale"]
    scrivi(f"Il mondiale, con l'importanza 4: la carriera più lenta lo gioca per la prima volta a {numero(primo, 1) + ' anni' if primo else 'nessuna età'}, e i suoi incontri "
           f"fanno il {numero(100 * lenta['grezzi_mondiale'] / max(1e-9, lenta['grezzi'][esperienza.TORNEO]))} per cento dei punti grezzi dei tornei: i punti si spostano "
           "verso la fine della carriera, come vuole Gabriele, risposta 10.")
    scrivi("Le cinque carriere vedenti: " + "; ".join(
        f"nato numero {c['id']}, A1 a {numero(c['eta_a1'], 2)} anni, somma a 50 {numero(c['somma_50'], 1)}, esperienza a 50 senza tetto {numero(c['esperienza_libera'], 2)}, "
        f"{c['storia']['tornei']} tornei, {c['storia']['mondiali']} mondiali" for c in carriere) + ".")
    scrivi("Le tre carriere di nati ipovedenti, con lo sconto del 7 per cento sulle caratteristiche di gioco: " + "; ".join(
        f"nato numero {c['id']}, A1 a {numero(c['eta_a1'], 2)} anni, somma a 50 {numero(c['somma_50'], 1)}" for c in ipovedenti) + ".")
    conteggi = lenta["conteggi"]
    eta_parte = costanti.ESPERIENZA_PER_ANNO_DI_VITA * (ETA_USCITA - ETA_INGRESSO)
    parti = {"età": eta_parte, "amichevoli": esperienze["amichevoli"] * conteggi["amichevoli"], "sfide": esperienze["sfide"] * conteggi["sfide"],
             "club": esperienze["club"] * conteggi["giorni"], "incontri di torneo": esperienze["incontri_torneo"] * conteggi["incontri_torneo"],
             "fasi superate": esperienze["fasi"] * conteggi["fasi"], "piazzamenti": esperienze["piazzamenti"] * conteggi["piazzamenti"]}
    scrivi("L'esperienza della carriera più lenta a 50 anni, fonte per fonte: " + ", ".join(f"{nome} {numero(v, 2)}" for nome, v in parti.items())
           + f"; i tornei insieme {numero(parti['incontri di torneo'] + parti['fasi superate'] + parti['piazzamenti'], 2)}; in tutto senza tetto "
           f"{numero(lenta['esperienza_libera'], 2)}.")
    for anni, t in sorted(lenta["tappe"].items()):
        scrivi(f"Carriera più lenta a {anni} anni: classe {t['classe']}, somma {numero(t['somma'], 1)}, valore {numero(t['valore'])}, esperienza {numero(t['esperienza'], 2)}.")
    scrivi("I bersagli del punto 13.3: la più lenta delle cinque carriere vedenti ad A1 fra 49,5 e 50 anni, e nessuna dopo i 50: "
           + ("dentro" if all(c["eta_a1"] <= 50.0 for c in carriere) and 49.5 <= lenta["eta_a1"] <= 50.0 else "FUORI")
           + f"; l'esperienza a 50 anni senza tetto fra 19,9 e 20,1: {'dentro' if 19.9 <= lenta['esperienza_libera'] <= 20.1 else 'FUORI'}.")
    # I casi tipici, con le gare del mondo, e le lettere dei mondi sintetici.
    nati_11 = nati(4000, 11)
    puliti = [g for g in nati_11 if senza_tratti(g)]
    mediano = al_percentile(puliti, 0.5)
    bravo = al_percentile(puliti, 0.75)
    amichevole_mediano = 0.5 * PUNTI_AMICHEVOLE_MEDIANO * fattori[esperienza.AMICHEVOLE]
    amichevole_bravo = 0.5 * PUNTI_AMICHEVOLE_BRAVO * fattori[esperienza.AMICHEVOLE]
    casi = []
    for anni in (35, 50):
        casi.append((f"mediano del computer, in polisportiva dai 20 anni, a {anni}", allena_a_passi(pronto(mediano, 20), 20, anni, 1.0, mediano.indole, gare=1.0)))
    casi.append(("libero mediano a 50 anni", allena_a_passi(pronto(mediano, 25), 25, 50, 0.5, mediano.indole, in_polisportiva=False, gare=1.0)))
    for anni in (25, 30, 35, 40):
        casi.append((f"mediano dell'utente dai 20 anni, con un'amichevole ogni due giorni e i tornei, a {anni}",
                     allena_a_passi(pronto(mediano, 20), 20, anni, 1.0 + amichevole_mediano, "completa", amichevoli_al_giorno=0.5, gare=1.0)))
    for anni in (30, 40, 50):
        casi.append((f"bravo dell'utente dai 15 anni, con un'amichevole ogni due giorni e i tornei, a {anni}",
                     allena_a_passi(pronto(bravo, 15), 15, anni, 1.0 + amichevole_bravo, "completa", amichevoli_al_giorno=0.5, gare=1.0)))
    for nome, g in casi:
        scrivi(f"Caso, {nome}: classe {classe.classe(g).codice}, valore {numero(g.indice_collettivo_valore)}, esperienza {numero(g.esperienza, 2)}, stipendio {economia.stipendio(g)} euro.")
    mondi = {"all'anno 10": mondo_10, "a regime": regime}
    if not argomenti.veloce:
        for anni in (20, 40):
            mondi[f"all'anno {anni}"] = mondo_sintetico(argomenti.giocatori, anni, 2026)
    for nome, giocatori in mondi.items():
        scrivi(f"Mondo sintetico {nome}: lettere {lettere(giocatori)}; valore mediano {numero(statistics.median(g.indice_collettivo_valore for g in giocatori))}.")
    for riga in blocco_costanti(fattori, esperienze):
        scrivi(riga)


def main():
    parser = argparse.ArgumentParser(description="La carriera perfetta di MESS col calendario vero: i fattori dei punti e le costanti dell'esperienza.")
    parser.add_argument("--processi", type=int, default=min(8, os.cpu_count() or 1), help="quanti processi giocano le carriere, fino a 8 se il computer li ha")
    parser.add_argument("--giri", type=int, default=3, help="i giri al più, ciascuno coi mondi sintetici rifatti, 3 se non indicati")
    parser.add_argument("--passi", type=int, default=10, help="i passi al più delle secanti in un giro, 10 se non indicati")
    parser.add_argument("--giocatori", type=int, default=3000, help="i giocatori del mondo sintetico all'anno 10, 3000 se non indicato")
    parser.add_argument("--attivi", type=int, default=ATTIVI_A_REGIME, help="i giocatori del mondo sintetico a regime, 20.600 se non indicato")
    parser.add_argument("--giorni", type=int, default=GIORNI_CARRIERA, help="i giorni della carriera, 4.428 se non indicato; più corta soltanto per provare lo strumento")
    parser.add_argument("--veloce", action="store_true", help="per provare lo strumento: mondi piccoli, un giro e due passi")
    parser.add_argument("--rapporto", type=Path, default=None, help="salva il racconto anche in questo file")
    argomenti = parser.parse_args()
    if argomenti.veloce:
        argomenti.giocatori, argomenti.attivi, argomenti.giri, argomenti.passi = 600, 3000, 1, 2
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
        fattori, esperienze, carriere, ipovedenti, mondo_10, regime, storia = esegui(argomenti, scrivi)
        racconta(fattori, esperienze, carriere, ipovedenti, mondo_10, regime, storia, argomenti, scrivi)
    finally:
        percorsi.cartella = cartella_vera
        shutil.rmtree(cartella, ignore_errors=True)
    scrivi(f"Misura completata in {numero(time.perf_counter() - inizio)} secondi.")
    if argomenti.rapporto:
        argomenti.rapporto.write_text("\n".join(righe) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
