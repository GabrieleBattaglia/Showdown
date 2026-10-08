"""
I modelli di MESS: il giocatore e la polisportiva.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 2 del piano, dallo smontaggio di sd.py. I nomi degli attributi
sono quelli del vecchio file. La chiusura delle polisportive del computer, che stava qui ma
agiva sull'intero mondo, si è spostata in mondo.py.
Dalla tappa 6 giocatori e polisportive hanno un diario, sul modello di quelli di Terminal Beast:
le voci più recenti in cima, ciascuna con la sua data simulata, e gli allenamenti consecutivi
sulla stessa caratteristica fusi in una voce sola.
Dalla tappa 7 il nome di una polisportiva resta come lo scrive chi la fonda, senza maiuscole
imposte, e gli ipovedenti chiedono il 10 per cento di gloria in meno, secondo la decisione D19.
Dalla tappa 8 c'è l'economia della decisione D22: il giocatore ha esperienza di carriera,
fedeltà e pazienza verso il suo club, stipendi arretrati e forse il tratto della bandiera; la
polisportiva ha una cassa, i tesserati in vendita, i bilanci mensili e i conti del mese.
Dalla tappa 9, il 2026-10-07, il giocatore ha un temperamento, da calmissimo a impetuoso, che nasce dal
suo numero e si calma con gli anni senza toccare il caso del mondo; un infortunio ha la sua sede, e
puo_giocare dice se il giocatore può scendere in campo, cosa che l'ambidestro fa anche con un braccio
fermo. Il valore complessivo lo calcola valore.py, con le caratteristiche per ruolo e i loro pesi.
Il salvataggio è al formato 5, che aggiunge temperamento e sede dell'infortunio. Le parti della tappa
9 sono di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Dal 2026-10-08, regola di Gabriele per le amichevoli della finestra, ogni giocatore ne gioca al
massimo una per giorno simulato, perché ogni amichevole dà punti allenamento: il giocatore ricorda
la data simulata dell'ultima, nel campo ultima_amichevole, salvato anche lui nel formato 5.
Dalla tappa 3 ogni modello sa scriversi come dizionario per il salvataggio JSON, con a_dizionario,
e ricostruirsi da lì, con da_dizionario, controllando ogni campo. Gli elenchi CAMPI_GIOCATORE e
CAMPI_POLISPORTIVA dicono quali attributi si salvano e di che tipo sono: i valori che si possono
ricalcolare, come l'indice di valore o la descrizione fisica, non si salvano e si ricalcolano.
"""

import contextlib
import datetime
import math
import random

import descrizioni
import valore
from costanti import (
    ACCETTAZIONE_PROB_MAX,
    ACCETTAZIONE_PROB_MID,
    ACCETTAZIONE_PROB_MIN,
    ACCETTAZIONE_REL_DIFF_THRESHOLD,
    AGING_PEAK_AGE_GIORNI,
    AGING_START_AGE_GIORNI,
    ALLENATE_FISICHE,
    ANNO_SIMULAZIONE_GIORNI,
    ARCHETIPI_ALLENAMENTO,
    ATTRIBUTI_ALLENABILI,
    ATTRIBUTI_BASE_CON_ALLENABILI,
    ATTRIBUTI_INVECCHIABILI,
    CALMA_PER_ANNO,
    CAPITALE_INIZIALE,
    CARATTERISTICHE_ATTACCO_BASE,
    CARATTERISTICHE_CONTROLLO_BASE,
    CARATTERISTICHE_DIFESA_BASE,
    CARATTERISTICHE_FISICHE_BASE,
    DATA_NESSUN_MOVIMENTO,
    ETA_INIZIO_CALMA,
    ETA_MAX_CREAZIONE_ANNI,
    ETA_MAX_MORTE_GIORNI,
    ETA_MAX_RITIRO_GIORNI,
    ETA_MIN_CREAZIONE_ANNI,
    ETA_MIN_MORTE_GIORNI,
    ETA_MIN_RITIRO_GIORNI,
    ETA_MINIMO_RICHIESTA_GLORIA_ANNI,
    ETA_PICCO_RICHIESTA_GLORIA_ANNI,
    FATTORE_GLORIA_RICHIESTA_AMBIDESTRO,
    FATTORE_GLORIA_RICHIESTA_CAMBIO_VEL,
    FATTORE_GLORIA_RICHIESTA_GIOCO_RAPIDO,
    FATTORE_GLORIA_RICHIESTA_IPOVEDENTE,
    GLORIA_RICHIESTA_FISSA,
    GLORIA_RICHIESTA_MINIMA_ASSOLUTA,
    K_ICV_GLORIA_RICHIESTA,
    LIMITE_MOVIMENTI_PER_TICK,
    MAPPA_FLAG_SOMMARIO,
    MAX_AGING_REDUCTION_FACTOR_PER_ANNO_SIM,
    MAX_ALLENATO_FISICO,
    MAX_ALLENATO_SKILL,
    MAX_FATTORE_ETA_GLORIA,
    MAX_GLORIA_RICHIESTA,
    MAX_PRECISIONE_RESISTENZA,
    MAX_SKILL_VALUE,
    MAX_TESSERATI_POLISPORTIVA,
    MAX_TOTALE_PRECISIONE_RESISTENZA,
    MAX_TOTALE_SKILL_GIOCO,
    MIN_FATTORE_ETA_GLORIA,
    NOME_ATTR_TO_DISPLAY_MAP,
    PROB_ARCHETIPO_CASUALE_CREAZIONE,
    PROBABILITA_BANDIERA_CREAZIONE,
    SEDE_NON_PRECISATA,
    SEDI_INFORTUNIO,
    TEMPERAMENTO_DEVIAZIONE,
    TEMPERAMENTO_MEDIA,
    VERSIONE,
    giorni_da_anni,
)
from nomi import genera_identita
from utilita import adesso, caso, crea_impronta, formatta_eta_sim, verifica_impronta


def probabilita_accettazione(g_off, g_rich):
    """
    La probabilità, in percentuale, che un giocatore che chiede g_rich di gloria accetti una
    polisportiva che ne offre g_off: cresce in linea retta fra il minimo e il massimo quando
    l'offerta passa dal 30 per cento in meno al 30 per cento in più della richiesta.
    """
    if g_rich <= 0:
        return ACCETTAZIONE_PROB_MAX
    th = ACCETTAZIONE_REL_DIFF_THRESHOLD
    d_min = -th * g_rich
    d_max = th * g_rich
    d_range = d_max - d_min
    diff = float(g_off - g_rich)
    if diff <= d_min:
        return ACCETTAZIONE_PROB_MIN
    if diff >= d_max:
        return ACCETTAZIONE_PROB_MAX
    if d_range <= 0:
        return ACCETTAZIONE_PROB_MID
    pos = (diff - d_min) / d_range
    prob = ACCETTAZIONE_PROB_MIN + pos * (ACCETTAZIONE_PROB_MAX - ACCETTAZIONE_PROB_MIN)
    return max(ACCETTAZIONE_PROB_MIN, min(prob, ACCETTAZIONE_PROB_MAX))


def temperamento_innato(id_giocatore):
    """
    Il temperamento con cui nasce un giocatore, da 0, calmissimo, a 100, impetuoso, con un
    decimale: una gaussiana attorno a 50 tirata da un generatore tutto suo, nato dal numero del
    giocatore. Il caso del mondo non si tocca, quindi la nascita resta quella di prima, e lo
    stesso numero dà sempre lo stesso temperamento: serve alla nascita e alla migrazione.
    """
    tiro = random.Random(f"MESS-temperamento-{id_giocatore}").gauss(TEMPERAMENTO_MEDIA, TEMPERAMENTO_DEVIAZIONE)
    return round(max(0.0, min(100.0, tiro)), 1)


SEDI_AMMESSE = frozenset((SEDE_NON_PRECISATA, *(sede[0] for sede in SEDI_INFORTUNIO)))
_SEDI_DI_BRACCIO = frozenset(sede[0] for sede in SEDI_INFORTUNIO if sede[2] is not None)


def e_fisica(nome_allenato):
    """Vero per le tre caratteristiche fisiche allenate: precisione, resistenza e forza."""
    return nome_allenato in ALLENATE_FISICHE


# I tipi dei campi salvati, oltre a bool, int, float e str.
DATA = "data"
DATA_O_NULLA = "data_o_nulla"
TESTO_O_NULLA = "testo_o_nulla"
LISTA_INTERI = "lista_interi"
DIARIO = "diario"
# Dalla tappa 8: i giocatori in vendita con il loro prezzo, i bilanci mensili e i conti del mese in corso.
VENDITE = "vendite"
BILANCI = "bilanci"
CONTI = "conti"
# Le voci dei conti di un mese: entrate e uscite della polisportiva, in euro.
VOCI_CONTI = ("sponsor", "vendite", "stipendi", "arretrati", "ingaggi", "acquisti")
_CONTROLLI = {
    bool: lambda v: isinstance(v, bool),
    int: lambda v: isinstance(v, int) and not isinstance(v, bool),
    float: lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    str: lambda v: isinstance(v, str),
    TESTO_O_NULLA: lambda v: v is None or isinstance(v, str),
    LISTA_INTERI: lambda v: isinstance(v, list) and all(isinstance(x, int) and not isinstance(x, bool) for x in v),
}
CAMPI_GIOCATORE = (
    ("id", int), ("nome", str), ("cognome", str), ("appartenenza", str), ("sesso", str),
    ("eta", int), ("etaritiro", int), ("etamorte", int), ("versione", str),
    ("datetime_creazione_sim", DATA), ("datacreazione_reale", DATA),
    ("puntiesperienza", int), ("mancino", bool), ("ambidestro", bool), ("ipovedente", bool),
    ("giocorapido", bool), ("cambiovelocita", bool), ("infortunato", bool), ("infortunio_fine_datetime", DATA_O_NULLA),
    ("ritirato", bool), ("partitevinte", int), ("partiteperse", int), ("setsvinti", int), ("setspersi", int),
    ("goalsfatti", int), ("goalssubiti", int), ("archetipo_allenamento", str),
    ("ori", int), ("argenti", int), ("bronzi", int), ("legni", int), ("diario", DIARIO),
    ("esperienza", float), ("fedelta", float), ("pazienza", float), ("arretrati", int), ("bandiera", bool),
    ("temperamento", float), ("infortunio_sede", TESTO_O_NULLA), ("ultima_amichevole", DATA_O_NULLA),
    *((nome, float) for nome in ATTRIBUTI_INVECCHIABILI),
)
# Per i giocatori senza tratti, che non possono ricalcolare il loro aspetto.
CAMPI_ASPETTO = (("altezza", int), ("peso", int), ("descrizione_fisica", str))
CAMPI_POLISPORTIVA = (
    ("nome", str), ("impronta_password", TESTO_O_NULLA), ("is_cpu_controlled", bool),
    ("datetime_creazione_sim", DATA), ("datacreazione_reale", DATA), ("versione_creazione", str),
    ("tesserati", LISTA_INTERI), ("maxtesserati", int), ("gloria", int),
    ("movimenti_oggi", int), ("datetime_ultimo_movimento", DATA),
    ("ori", int), ("argenti", int), ("bronzi", int), ("legni", int),
    ("coppe_oro", int), ("coppe_argento", int), ("coppe_bronzo", int), ("coppe_legno", int), ("diario", DIARIO),
    ("cassa", int), ("in_vendita", VENDITE), ("bilanci", BILANCI), ("conti_del_mese", CONTI),
)


def conti_vuoti():
    """I conti di un mese appena cominciato: ogni voce a zero."""
    return dict.fromkeys(VOCI_CONTI, 0)


def _intero(valore):
    return isinstance(valore, int) and not isinstance(valore, bool)


def annota_diario(diario, data, testo):
    """Mette in cima al diario una voce con la data simulata e il testo."""
    diario.insert(0, {"data": data, "testo": testo})


def annota_allenamento(diario, data, nome_base, da, a):
    """
    Annota un allenamento, con il valore della caratteristica prima e dopo. Se la voce in cima
    è un allenamento della stessa caratteristica, la fonde con quella, come Terminal Beast: resta
    il valore di partenza della prima e quello d'arrivo dell'ultima, con la data dell'ultima.
    """
    if diario and diario[0].get("allenamento") == nome_base:
        diario[0]["a"] = a
        diario[0]["data"] = data
    else:
        diario.insert(0, {"data": data, "allenamento": nome_base, "da": da, "a": a})


def _voce_da_json(voce, chi):
    """Una voce di diario letta dal salvataggio e controllata; ValueError se non va."""
    errore = ValueError(f"{chi}: una voce del diario non è valida: {voce!r}")
    if not isinstance(voce, dict) or not isinstance(voce.get("data"), str):
        raise errore
    try:
        data = datetime.datetime.fromisoformat(voce["data"])
    except ValueError:
        raise errore from None
    if set(voce) == {"data", "testo"} and isinstance(voce["testo"], str):
        return {"data": data, "testo": voce["testo"]}
    numeri = all(isinstance(voce.get(chiave), (int, float)) and not isinstance(voce.get(chiave), bool) for chiave in ("da", "a"))
    if set(voce) == {"data", "allenamento", "da", "a"} and voce["allenamento"] in ATTRIBUTI_BASE_CON_ALLENABILI and numeri:
        return {"data": data, "allenamento": voce["allenamento"], "da": float(voce["da"]), "a": float(voce["a"])}
    raise errore


def a_json(valore, tipo):
    """Un valore di un modello nella forma che il salvataggio JSON sa scrivere."""
    if tipo == VENDITE:
        return {str(gid): int(prezzo) for gid, prezzo in sorted(valore.items())}
    if tipo == BILANCI:
        return [{**voce, "data": voce["data"].isoformat()} for voce in valore]
    if tipo == CONTI:
        return {voce: int(valore[voce]) for voce in VOCI_CONTI}
    if tipo == DIARIO:
        return [{**voce, "data": voce["data"].isoformat()} for voce in valore]
    if tipo in (DATA, DATA_O_NULLA):
        return None if valore is None else valore.isoformat()
    if tipo == TESTO_O_NULLA:
        return None if valore is None else str(valore)
    if tipo == LISTA_INTERI:
        return [int(v) for v in valore]
    return tipo(valore)


def da_json(valore, tipo, chi, campo):
    """Un valore letto dal salvataggio, controllato e riportato al tipo del modello; ValueError se non va."""
    errore = ValueError(f"{chi}: il campo {campo} non è valido: {valore!r}")
    if tipo == VENDITE:
        if not isinstance(valore, dict) or not all(chiave.isdigit() and _intero(prezzo) and prezzo >= 0 for chiave, prezzo in valore.items()):
            raise errore
        return {int(chiave): prezzo for chiave, prezzo in valore.items()}
    if tipo == CONTI:
        if not isinstance(valore, dict) or set(valore) != set(VOCI_CONTI) or not all(_intero(v) for v in valore.values()):
            raise errore
        return dict(valore)
    if tipo == BILANCI:
        if not isinstance(valore, list):
            raise errore
        bilanci = []
        for voce in valore:
            if not isinstance(voce, dict) or set(voce) != {"data", "cassa", *VOCI_CONTI} or not all(_intero(voce[v]) for v in ("cassa", *VOCI_CONTI)):
                raise errore
            try:
                bilanci.append({**voce, "data": datetime.datetime.fromisoformat(voce["data"])})
            except (TypeError, ValueError):
                raise errore from None
        return bilanci
    if tipo == DIARIO:
        if not isinstance(valore, list):
            raise errore
        return [_voce_da_json(voce, chi) for voce in valore]
    if tipo in (DATA, DATA_O_NULLA):
        if valore is None and tipo == DATA_O_NULLA:
            return None
        if not isinstance(valore, str):
            raise errore
        try:
            return datetime.datetime.fromisoformat(valore)
        except ValueError:
            raise errore from None
    if not _CONTROLLI[tipo](valore):
        raise errore
    if tipo is float:
        return float(valore)
    if tipo == LISTA_INTERI:
        return list(valore)
    return valore


def _campi_da_dizionario(oggetto, dati, campi, chi):
    """Imposta sull'oggetto i campi elencati, letti e controllati dal dizionario del salvataggio."""
    if not isinstance(dati, dict):
        raise ValueError(f"{chi}: non è un dizionario")
    for campo, tipo in campi:
        if campo not in dati:
            raise ValueError(f"{chi}: manca il campo {campo}")
        setattr(oggetto, campo, da_json(dati[campo], tipo, chi, campo))


class Giocatore:
    def __init__(self, id_giocatore, datetime_creazione_sim, **kwargs):
        self.id = id_giocatore
        # Il temperamento nasce dal numero del giocatore, senza toccare il caso del mondo.
        self.temperamento = temperamento_innato(id_giocatore)
        self.infortunio_sede = None
        # La data simulata dell'ultima amichevole: chi nasce non ne ha ancora giocate.
        self.ultima_amichevole = None
        self.nome = "*"
        self.cognome = "*"
        self.appartenenza = "*"
        self.sesso = random.choice(('m', 'f'))
        eta_anni_casuale = random.uniform(ETA_MIN_CREAZIONE_ANNI, ETA_MAX_CREAZIONE_ANNI)
        self.eta = giorni_da_anni(eta_anni_casuale)
        self.etaritiro = int(random.uniform(ETA_MIN_RITIRO_GIORNI, ETA_MAX_RITIRO_GIORNI))
        self.etamorte = int(random.uniform(ETA_MIN_MORTE_GIORNI, ETA_MAX_MORTE_GIORNI))
        self.versione = VERSIONE
        self.descrizione_fisica = ""
        self.datetime_creazione_sim = datetime_creazione_sim
        self.datacreazione_reale = adesso()
        self.puntiesperienza = 0
        self.mancino = caso(8.5)
        self.ambidestro = caso(4.25) if not self.mancino else False
        self.infortunato = False
        self.infortunio_fine_datetime = None
        self.ipovedente = False
        # Altezza e peso li calcola poi aggiorna_aspetto dall'età; il tiro resta perché la
        # sequenza del caso alla nascita non cambi.
        self.altezza = random.randrange(160, 186)
        self.peso = 70
        self.giocorapido = caso(12.0)
        self.cambiovelocita = caso(15.0)
        self.ritirato = False
        self.partitevinte = 0
        self.partiteperse = 0
        self.setsvinti = 0
        self.setspersi = 0
        self.goalsfatti = 0
        self.goalssubiti = 0
        self.icv_base = 0.0
        self.icv_allenato = 0.0
        self.indice_collettivo_valore = 0.0
        self.archetipo_allenamento = "Non Definito"
        self.ori = 0
        self.argenti = 0
        self.bronzi = 0
        self.legni = 0
        self.forza_base = 0.0
        self.forza_allenata = 0.0
        self.diario = []
        for nome_base in ATTRIBUTI_BASE_CON_ALLENABILI:
            nome_allenato = nome_base.replace('_base', '_allenata')
            max_val = MAX_PRECISIONE_RESISTENZA if nome_base in CARATTERISTICHE_FISICHE_BASE else MAX_SKILL_VALUE
            setattr(self, nome_base, random.uniform(0, max_val * 0.6))
            setattr(self, nome_allenato, 0.0)
        self._applica_parametri(kwargs)
        self._rispetta_tetti()
        if self.nome == "*" and self.cognome == "*":
            self.nome, self.cognome = genera_identita(self.sesso)
        for attr, default in [('forza_base', 0.0), ('forza_allenata', 0.0),
                              ('ipovedente', False), ('infortunato', False), ('infortunio_fine_datetime', None),
                              ('archetipo_allenamento', "Non Definito"), ('datacreazione_reale', self.datetime_creazione_sim),
                              ('descrizione_fisica', ''), ('ori', 0), ('argenti', 0), ('bronzi', 0), ('legni', 0)]:
            if not hasattr(self, attr) or (getattr(self, attr, None) is None and default is not None):
                setattr(self, attr, default)
        if self.archetipo_allenamento == "Non Definito":
            self._assegna_archetipo_iniziale()
        self.aggiorna_icv()
        if not self.descrizione_fisica:
            self._genera_descrizione_fisica()
        # L'economia della tappa 8: esperienza di carriera, fedeltà e pazienza verso il club,
        # stipendi arretrati, e il tratto raro della bandiera, tirato per ultimo perché la
        # sequenza del caso alla nascita non cambi nel resto.
        self.esperienza = 0.0
        self.fedelta = 0.0
        self.pazienza = 100.0
        self.arretrati = 0
        self.bandiera = caso(PROBABILITA_BANDIERA_CREAZIONE)
        self.annota(self.datetime_creazione_sim, f"Entra nel mondo dello showdown, a {int(self.eta_anni)} anni.")

    def annota(self, data, testo):
        """Una voce nuova nel diario del giocatore, con la data simulata."""
        annota_diario(self.diario, data, testo)

    def annota_allenamento(self, data, nome_base, da, a):
        """Un allenamento nel diario, fuso con il precedente se riguarda la stessa caratteristica."""
        annota_allenamento(self.diario, data, nome_base, da, a)

    def _applica_parametri(self, kwargs):
        """Applica i valori passati alla creazione, controllandone tipo e limiti."""
        eta_giorni = kwargs.pop('eta', None)
        if 'ipovedente' in kwargs:
            valore = kwargs.pop('ipovedente')
            self.ipovedente = valore if isinstance(valore, bool) else str(valore).lower() in ['s', 'true', '1', 'yes', 'vero']
        for chiave, valore in kwargs.items():
            if chiave == 'nascita':
                continue
            if chiave in ATTRIBUTI_ALLENABILI:
                try:
                    val_f = float(valore)
                except (TypeError, ValueError):
                    setattr(self, chiave, 0.0)
                    continue
                lim_a = MAX_ALLENATO_FISICO if e_fisica(chiave) else MAX_ALLENATO_SKILL
                setattr(self, chiave, max(0.0, min(val_f, lim_a)))
            elif chiave == 'datetime_creazione_sim':
                if isinstance(valore, datetime.datetime):
                    self.datetime_creazione_sim = valore
            elif chiave == 'datacreazione_reale':
                if isinstance(valore, datetime.datetime):
                    self.datacreazione_reale = valore
            elif chiave == 'infortunio_fine_datetime':
                self.infortunio_fine_datetime = valore if isinstance(valore, datetime.datetime) else None
            elif chiave == 'archetipo_allenamento':
                self.archetipo_allenamento = valore if isinstance(valore, str) else "Non Definito"
            elif chiave == 'descrizione_fisica':
                self.descrizione_fisica = valore[:500] if isinstance(valore, str) else ""
            elif hasattr(self, chiave):
                self._imposta_attributo(chiave, valore)
        if eta_giorni is not None:
            with contextlib.suppress(TypeError, ValueError):
                self.eta = int(eta_giorni)

    def _imposta_attributo(self, chiave, valore):
        """Imposta un attributo esistente convertendo il valore al tipo che ha già, se si può."""
        nuovo = valore
        if chiave == 'puntiesperienza' and not isinstance(valore, int):
            try:
                nuovo = int(valore)
            except (TypeError, ValueError):
                setattr(self, chiave, valore)
                return
        elif chiave in ['etaritiro', 'etamorte'] and not isinstance(valore, int):
            try:
                nuovo = giorni_da_anni(float(valore) / 10.)
            except (TypeError, ValueError):
                return
        try:
            setattr(self, chiave, type(getattr(self, chiave))(nuovo))
        except (TypeError, ValueError):
            setattr(self, chiave, valore)

    def _rispetta_tetti(self):
        """Riporta ogni caratteristica entro il tetto del totale fra parte innata e allenata."""
        for nome_base in ATTRIBUTI_BASE_CON_ALLENABILI:
            nome_allenato = nome_base.replace('_base', '_allenata')
            max_totale_skill = MAX_TOTALE_PRECISIONE_RESISTENZA if nome_base in CARATTERISTICHE_FISICHE_BASE else MAX_TOTALE_SKILL_GIOCO
            v_b = getattr(self, nome_base, 0.0)
            v_a = getattr(self, nome_allenato, 0.0)
            if v_b + v_a > max_totale_skill:
                v_a = max(0., max_totale_skill - v_b)
                setattr(self, nome_allenato, v_a)
            if v_b + v_a > max_totale_skill:
                setattr(self, nome_base, max(0., max_totale_skill - v_a))

    def a_dizionario(self):
        """Il giocatore come dizionario per il salvataggio JSON."""
        dati = {campo: a_json(getattr(self, campo), tipo) for campo, tipo in CAMPI_GIOCATORE}
        tratti = getattr(self, "tratti", None)
        if tratti:
            dati["tratti"] = tratti
        else:
            dati.update({campo: a_json(getattr(self, campo), tipo) for campo, tipo in CAMPI_ASPETTO})
        return dati

    @classmethod
    def da_dizionario(cls, dati):
        """Ricostruisce un giocatore dal suo dizionario, senza tirare il caso; ValueError se un campo non va."""
        g = cls.__new__(cls)
        chi = f"Giocatore {dati.get('id', '?') if isinstance(dati, dict) else '?'}"
        _campi_da_dizionario(g, dati, CAMPI_GIOCATORE, chi)
        if g.sesso not in ('m', 'f'):
            raise ValueError(f"{chi}: il campo sesso non è valido: {g.sesso!r}")
        if not 0.0 <= g.temperamento <= 100.0:
            raise ValueError(f"{chi}: il campo temperamento non è valido: {g.temperamento!r}")
        if g.infortunio_sede is not None and g.infortunio_sede not in SEDI_AMMESSE:
            raise ValueError(f"{chi}: il campo infortunio_sede non è valido: {g.infortunio_sede!r}")
        tratti = dati.get("tratti")
        if tratti is not None:
            if not isinstance(tratti, dict):
                raise ValueError(f"{chi}: il campo tratti non è valido")
            g.tratti = tratti
            g.altezza, g.peso, g.descrizione_fisica = 0, 0, ""
        else:
            _campi_da_dizionario(g, dati, CAMPI_ASPETTO, chi)
        g._rispetta_tetti()
        g.aggiorna_icv()
        g.aggiorna_aspetto()
        return g

    def _get_valore_totale(self, nome_base):
        """Il valore di una caratteristica, parte innata più parte allenata."""
        if not nome_base.endswith('_base'):
            return 0.0
        return getattr(self, nome_base, 0.0) + getattr(self, nome_base.replace('_base', '_allenata'), 0.0)

    @property
    def gloria_richiesta(self):
        """La gloria che il giocatore chiede a una polisportiva: cresce col valore, cala dopo i 17 anni; gli ipovedenti chiedono un decimo in meno."""
        g_base = self.indice_collettivo_valore * K_ICV_GLORIA_RICHIESTA
        if ANNO_SIMULAZIONE_GIORNI <= 0:
            return GLORIA_RICHIESTA_MINIMA_ASSOLUTA
        eta_p_gg = giorni_da_anni(ETA_PICCO_RICHIESTA_GLORIA_ANNI)
        eta_m_gg = giorni_da_anni(ETA_MINIMO_RICHIESTA_GLORIA_ANNI)
        range_eta = max(1, eta_m_gg - eta_p_gg)
        fatt_eta = MAX_FATTORE_ETA_GLORIA
        if self.eta >= eta_m_gg:
            fatt_eta = MIN_FATTORE_ETA_GLORIA
        elif self.eta > eta_p_gg:
            prog = (self.eta - eta_p_gg) / range_eta
            fatt_eta = MAX_FATTORE_ETA_GLORIA - prog * (MAX_FATTORE_ETA_GLORIA - MIN_FATTORE_ETA_GLORIA)
        g_calc = (g_base * fatt_eta) + GLORIA_RICHIESTA_FISSA
        if getattr(self, 'ambidestro', False):
            g_calc *= FATTORE_GLORIA_RICHIESTA_AMBIDESTRO
        if getattr(self, 'giocorapido', False):
            g_calc *= FATTORE_GLORIA_RICHIESTA_GIOCO_RAPIDO
        if getattr(self, 'cambiovelocita', False):
            g_calc *= FATTORE_GLORIA_RICHIESTA_CAMBIO_VEL
        if getattr(self, 'ipovedente', False):
            g_calc *= FATTORE_GLORIA_RICHIESTA_IPOVEDENTE
        g_fin = max(GLORIA_RICHIESTA_MINIMA_ASSOLUTA, int(g_calc))
        return min(g_fin, MAX_GLORIA_RICHIESTA)

    @property
    def eta_anni(self):
        return self.eta / ANNO_SIMULAZIONE_GIORNI if ANNO_SIMULAZIONE_GIORNI > 0 else 0.0

    @property
    def temperamento_attuale(self):
        """Il temperamento di oggi: si calma senza caso di un quarto di punto all'anno dopo i 25, dieci punti a 65 anni."""
        return max(0.0, self.temperamento - CALMA_PER_ANNO * max(0.0, self.eta_anni - ETA_INIZIO_CALMA))

    @property
    def puo_giocare(self):
        """Vero se il giocatore può scendere in campo: non ritirato e non infortunato, oppure ambidestro con un braccio fermo."""
        if self.ritirato:
            return False
        if not self.infortunato:
            return True
        return bool(self.ambidestro) and self.infortunio_sede in _SEDI_DI_BRACCIO

    def ha_giocato_amichevole(self, oggi):
        """Vero se il giocatore ha già giocato un'amichevole nel giorno simulato di oggi, che è una data con l'ora."""
        return self.ultima_amichevole is not None and self.ultima_amichevole.date() == oggi.date()

    def puo_giocare_amichevole(self, oggi):
        """
        Vero se il giocatore può giocare un'amichevole oggi: deve poter scendere in campo, e non
        averne già giocata una nel giorno simulato, perché ognuno ne gioca al massimo una al giorno.
        """
        return self.puo_giocare and not self.ha_giocato_amichevole(oggi)

    def _riga_caratteristica(self, nome_b):
        tot = self._get_valore_totale(nome_b)
        nome_d = NOME_ATTR_TO_DISPLAY_MAP.get(nome_b, nome_b.replace('_base', '').replace('_', ' ').title())
        max_t = MAX_TOTALE_PRECISIONE_RESISTENZA if nome_b in CARATTERISTICHE_FISICHE_BASE else MAX_TOTALE_SKILL_GIOCO
        perc = f"({(tot * 100. / max_t if max_t > 0 else 0.):.0f}%)"
        v_b = getattr(self, nome_b, 0.)
        v_a = getattr(self, nome_b.replace('_base', '_allenata'), 0.)
        return f"  - {nome_d:<25}: {v_b:5.2f} + {v_a:5.2f} = {tot:5.2f} {perc}"

    def __str__(self):
        eta_vis = formatta_eta_sim(self.eta, False)
        sex = "(Uomo)" if self.sesso == 'm' else "(Donna)"
        eta_sex = f"Età: {eta_vis} {sex}"
        self.aggiorna_aspetto()
        stato = ["libero" if self.appartenenza == "*" else f"iscritto a {self.appartenenza}"]
        if self.ritirato:
            stato.append("ritirato")
        if self.infortunato:
            fine = f" (fino a {self.infortunio_fine_datetime:%Y-%m-%d %H:%M})" if self.infortunio_fine_datetime else " (N/D)"
            stato.append("infortunato" + fine)
        flags_estesi = [nome_attr.replace('_', ' ').capitalize() for nome_attr in MAPPA_FLAG_SOMMARIO if getattr(self, nome_attr, False)]
        if flags_estesi:
            stato.append(f"Flags: {', '.join(flags_estesi)}")
        stato_str = ", ".join(stato)
        compl = "Compleanno N/D"
        if ANNO_SIMULAZIONE_GIORNI > 0:
            gg_eta = self.eta
            anni_c, gg_dopo = divmod(gg_eta, ANNO_SIMULAZIONE_GIORNI)
            gg_manc = (ANNO_SIMULAZIONE_GIORNI - gg_dopo) % ANNO_SIMULAZIONE_GIORNI
            anni_prox = anni_c + 1
            if gg_dopo == 0 and gg_eta > 0:
                compl = f"Prossimo Compleanno (sim): tra {ANNO_SIMULAZIONE_GIORNI} giorni (compirà {anni_prox} anni sim)"
            elif gg_manc == 0 and gg_eta == 0:
                compl = f"Prossimo Compleanno (sim): tra {ANNO_SIMULAZIONE_GIORNI} giorni (compirà 1 anno sim)"
            else:
                compl = f"Prossimo Compleanno (sim): tra {gg_manc} giorni (compirà {anni_prox} anni sim)"
        out = [f"\n--- Scheda Giocatore ID: {self.id} ---", f"{self.nome} {self.cognome}", eta_sex, f"Stato: {stato_str}",
               f"Descrizione: {getattr(self, 'descrizione_fisica', '(N/D)')}",
               f"Scoperto (sim): {self.datetime_creazione_sim:%Y-%m-%d %H:%M}", f"Scoperto (reale): {self.datacreazione_reale:%Y-%m-%d %H:%M}",
               f"Versione Creazione: {self.versione}", f"{compl}", f"Altezza: {self.altezza} cm, Peso: {self.peso} kg",
               f"XP: {self.puntiesperienza}", f"ICV Tot: {self.indice_collettivo_valore:.2f} (B: {self.icv_base:.2f}, A: {self.icv_allenato:.2f})",
               f"Gloria Rich: {self.gloria_richiesta}"]
        for titolo, gruppo in (("\nCaratteristiche Fisiche:", CARATTERISTICHE_FISICHE_BASE), ("\nCaratteristiche Difensive:", CARATTERISTICHE_DIFESA_BASE),
                               ("\nCaratteristiche Offensive:", CARATTERISTICHE_ATTACCO_BASE), ("\nPolivalenti:", CARATTERISTICHE_CONTROLLO_BASE)):
            out.append(titolo)
            out.extend(self._riga_caratteristica(nb) for nb in gruppo)
        out.append("\n--- Carriera e Palmarès ---")
        pt = self.partitevinte + self.partiteperse
        pv = f"({self.partitevinte * 100. / pt:.1f}%)" if pt else "(0%)"
        out.append(f"  Partite Giocate: {pt} (Vinte: {self.partitevinte} {pv})")
        st = self.setsvinti + self.setspersi
        sv = f"({self.setsvinti * 100. / st:.1f}%)" if st else "(0%)"
        out.append(f"  Sets Giocati: {st} (Vinti: {self.setsvinti} {sv})")
        gf, gs = self.goalsfatti, self.goalssubiti
        rapp_str = ""
        if gs > 0:
            rapp_str = f" (Rapp GF/GS: {(gf * 100. / gs):.1f}%)"
        elif gf > 0:
            rapp_str = " (Rapp GF/GS: Inf)"
        out.append(f"  Goals: Fatti={gf}, Subiti={gs}{rapp_str}")
        oro = getattr(self, 'ori', 0)
        arg = getattr(self, 'argenti', 0)
        bro = getattr(self, 'bronzi', 0)
        leg = getattr(self, 'legni', 0)
        if oro > 0 or arg > 0 or bro > 0 or leg > 0:
            out.append(f"  Medaglie: Oro={oro}, Argento={arg}, Bronzo={bro}, Legno={leg}")
        else:
            out.append("  Medaglie: Nessuna")
        out.append("-" * 75)
        return "\n".join(out)

    def sommario(self):
        """Il giocatore in una riga."""
        eta_vis = formatta_eta_sim(self.eta, formato_breve=True)
        sesso = "(U)" if self.sesso == 'm' else "(D)"
        stato = "Ritirato" if self.ritirato else "Libero" if self.appartenenza == "*" else f"({self.appartenenza[:10]})"
        flags = "".join([f for a, f in MAPPA_FLAG_SOMMARIO.items() if getattr(self, a, False)])
        flags_str = f" [{flags}]" if flags else ""
        xp = int(self.puntiesperienza or 0)
        return (f"ID:{self.id:<4d} {self.nome[:15]:<15} {self.cognome[:15]:<15} "
                f"{eta_vis:<8} {sesso} ICV:{self.indice_collettivo_valore:6.1f} XP:{xp:<5} {stato}{flags_str}")

    def aggiorna_icv(self):
        """
        Ricalcola l'indice collettivo di valore con valore.py: la parte innata con i tratti, la parte
        allenata, e la loro somma. Con i pesi iniziali è l'indice di prima: tutte le caratteristiche
        più 33 punti per ogni tratto speciale.
        """
        self.icv_base, self.icv_allenato = valore.parti(self)
        self.indice_collettivo_valore = self.icv_base + self.icv_allenato

    def _genera_descrizione_fisica(self):
        """
        Dalla versione 1.1.0 i tratti del giocatore vengono dal motore grammaticale di
        descrizioni.py: altezza, peso e descrizione si ricalcolano con l'età del momento.
        """
        self.tratti = descrizioni.genera_tratti(self.sesso)
        self.aggiorna_aspetto()

    def aggiorna_aspetto(self):
        """Altezza, peso e descrizione all'età attuale. I giocatori nati prima della 1.1.0 non hanno tratti e tengono i loro."""
        tratti = getattr(self, "tratti", None)
        if not tratti:
            return
        self.altezza, self.peso = descrizioni.fisico(tratti, self.sesso, self.eta_anni)
        self.descrizione_fisica = descrizioni.descrivi(tratti, self.sesso, self.eta_anni)

    def _assegna_archetipo_iniziale(self):
        sugg = self._determina_archetipo_da_base()
        if sugg and sugg in ARCHETIPI_ALLENAMENTO and not caso(PROB_ARCHETIPO_CASUALE_CREAZIONE):
            self.archetipo_allenamento = sugg
        else:
            validi = list(ARCHETIPI_ALLENAMENTO.keys())
            self.archetipo_allenamento = random.choice(validi) if validi else "TuttofareBilanciato"

    def _determina_archetipo_da_base(self):
        """L'archetipo di allenamento che meglio si adatta alle caratteristiche innate, o None."""
        stats = {'fis': CARATTERISTICHE_FISICHE_BASE, 'att': CARATTERISTICHE_ATTACCO_BASE, 'dif': CARATTERISTICHE_DIFESA_BASE, 'ctrl': CARATTERISTICHE_CONTROLLO_BASE,
                 'bloc': ['bloccosx_base', 'bloccodx_base'], 'batt': ['battutasx_base', 'battutadx_base']}
        medie = {k: sum(getattr(self, s, 0.) for s in v) / len(v) if v else 0. for k, v in stats.items()}
        pesi = {"MuroFisico": medie['fis'] * 2.5, "AttaccantePuro": medie['att'], "DifensoreRoccioso": medie['dif'],
                "SpecialistaBlocchiDifesa": medie['bloc'] * 1.5 + medie['dif'] * .5, "SpecialistaBlocchiAttacco": medie['bloc'] * 1.5 + medie['att'] * .5,
                "SpecialistaBlocchiControllo": medie['bloc'] * 1.5 + medie['ctrl'] * .5, "SpecialistaBattutaBlocco": medie['batt'] * 1.5 + medie['bloc'] * .5,
                "CecchinoPreciso": medie['ctrl']}
        soglia = 5.
        validi = {k: v for k, v in pesi.items() if v >= soglia}
        if not validi:
            return None
        sugg = max(validi, key=validi.get)
        if medie['dif'] > 8. and medie['bloc'] > 8.:
            sugg = "SpecialistaBlocchiDifesa"
        return sugg if sugg in ARCHETIPI_ALLENAMENTO else None

    def _applica_declino_aggregato(self, giorni_passati):
        """Il declino dovuto all'età per i giorni trascorsi, dai 50 anni in poi."""
        if giorni_passati <= 0 or self.eta < AGING_START_AGE_GIORNI or ANNO_SIMULAZIONE_GIORNI <= 0:
            return
        prog_eta = max(0, self.eta - AGING_START_AGE_GIORNI)
        range_decl = max(1, AGING_PEAK_AGE_GIORNI - AGING_START_AGE_GIORNI)
        aging_f = min(1.0, prog_eta / range_decl)
        reduc_ann = aging_f * MAX_AGING_REDUCTION_FACTOR_PER_ANNO_SIM
        manten_ann = max(0.0, 1.0 - reduc_ann)
        manten_giorn = pow(manten_ann, 1.0 / ANNO_SIMULAZIONE_GIORNI)
        manten_tot = pow(manten_giorn, giorni_passati)
        for attr in ATTRIBUTI_INVECCHIABILI:
            setattr(self, attr, max(0.0, getattr(self, attr, 0.0) * manten_tot))


def normalizza_nome(nome):
    """Il nome di una polisportiva senza spazi in più; le maiuscole restano come le ha scritte chi la fonda."""
    return " ".join(nome.split())


class Polisportiva:
    def __init__(self, nome, password, datetime_creazione_sim, is_cpu_controlled=False):
        self.nome = normalizza_nome(nome)
        # Dalla tappa 3 la password non si conserva: si conserva la sua impronta.
        self.impronta_password = crea_impronta(password) if password and not is_cpu_controlled else None
        self.datetime_creazione_sim = datetime_creazione_sim
        self.is_cpu_controlled = is_cpu_controlled
        self.tesserati = []
        self.indicecollettivotesserati = 0.0
        self.ori = 0
        self.argenti = 0
        self.bronzi = 0
        self.legni = 0
        self.coppe_oro = 0
        self.coppe_argento = 0
        self.coppe_bronzo = 0
        self.coppe_legno = 0
        self.maxtesserati = MAX_TESSERATI_POLISPORTIVA
        self.gloria = 100
        self.datetime_ultimo_movimento = DATA_NESSUN_MOVIMENTO
        self.movimenti_oggi = 0
        self.datacreazione_reale = adesso()
        self.versione_creazione = VERSIONE
        self.diario = []
        # L'economia della tappa 8: la cassa, i tesserati in vendita con il loro prezzo, i
        # bilanci dei mesi passati, dal più recente, e i conti del mese in corso.
        self.cassa = CAPITALE_INIZIALE
        self.in_vendita = {}
        self.bilanci = []
        self.conti_del_mese = conti_vuoti()
        self.annota(datetime_creazione_sim, "Fondata.")

    def annota(self, data, testo):
        """Una voce nuova nel diario della polisportiva, con la data simulata."""
        annota_diario(self.diario, data, testo)

    @property
    def protetta(self):
        """Vero se la polisportiva è protetta da una password."""
        return self.impronta_password is not None

    def imposta_password(self, password):
        """Protegge la polisportiva con una password; con una password vuota toglie la protezione."""
        self.impronta_password = crea_impronta(password) if password else None

    def verifica_password(self, password):
        """Vero se la password è quella giusta, oppure se la polisportiva non è protetta."""
        if self.impronta_password is None:
            return True
        return verifica_impronta(password, self.impronta_password)

    def a_dizionario(self):
        """La polisportiva come dizionario per il salvataggio JSON."""
        return {campo: a_json(getattr(self, campo), tipo) for campo, tipo in CAMPI_POLISPORTIVA}

    @classmethod
    def da_dizionario(cls, dati):
        """
        Ricostruisce una polisportiva dal suo dizionario; ValueError se un campo non va. L'indice
        dei tesserati riparte da zero: lo ricalcola chi carica il mondo, quando ha i giocatori.
        """
        p = cls.__new__(cls)
        chi = f"Polisportiva {dati.get('nome', '?') if isinstance(dati, dict) else '?'}"
        _campi_da_dizionario(p, dati, CAMPI_POLISPORTIVA, chi)
        p.indicecollettivotesserati = 0.0
        return p

    def __str__(self):
        dt_creaz_sim_str = f"{self.datetime_creazione_sim:%Y-%m-%d %H:%M}" if isinstance(self.datetime_creazione_sim, datetime.datetime) else "N/D"
        reale = getattr(self, 'datacreazione_reale', None)
        dt_creaz_real_str = reale.strftime('%Y-%m-%d %H:%M') if isinstance(reale, datetime.datetime) else "N/D"
        versione_creaz = getattr(self, 'versione_creazione', 'N/D')
        num_tesserati = len(self.tesserati)
        ic_medio_str = f"{(self.indicecollettivotesserati / num_tesserati):.2f}" if num_tesserati > 0 else "0.00"
        cpu = " [CPU]" if self.is_cpu_controlled else ""
        mov_rimasti = LIMITE_MOVIMENTI_PER_TICK - self.movimenti_oggi
        eta_poli_str = "(Vedi Sommario/Statistiche per Età)"
        out = [f"\n--- Scheda Polisportiva: {self.nome}{cpu} ---", f"Fondata: (Reale: {dt_creaz_real_str}, Sim: {dt_creaz_sim_str}, Versione: {versione_creaz})",
               f"Tesserati: {num_tesserati}/{self.maxtesserati}, ICT: {self.indicecollettivotesserati:.2f}, IC Medio: {ic_medio_str}",
               f"Gloria: {self.gloria}, Movimenti Oggi Rimanenti: {mov_rimasti}/{LIMITE_MOVIMENTI_PER_TICK}",
               "\n--- Palmarès e Attività ---", f"Età Polisportiva (Sim): {eta_poli_str}", "Coppe (Squadra):",
               f"  Oro={self.coppe_oro}, Argento={self.coppe_argento}, Bronzo={self.coppe_bronzo}, Legno={self.coppe_legno}",
               "Medaglie (Individuali Tesserati):", f"  Oro={self.ori}, Argento={self.argenti}, Bronzo={self.bronzi}, Legno={self.legni}"]
        return "\n".join(out)

    def eta_sim(self, data_corrente_sim):
        """L'età della polisportiva in forma breve, oppure Età N/D se non si può calcolare."""
        if data_corrente_sim and isinstance(self.datetime_creazione_sim, datetime.datetime):
            return formatta_eta_sim(int((data_corrente_sim - self.datetime_creazione_sim).total_seconds() / (24 * 3600)), True) + " sim"
        return "Età N/D"

    def sommario(self, data_corrente_sim=None):
        """La polisportiva in una riga."""
        cpu = " [CPU]" if self.is_cpu_controlled else ""
        return (f"{self.nome:<30} {len(self.tesserati):2d}/{self.maxtesserati} atl. ICT:{self.indicecollettivotesserati:7.1f} ({self.eta_sim(data_corrente_sim)}) {cpu}")

    def aggiorna_ict(self, giocatori, ids_morti):
        """
        Ricalcola l'indice collettivo dei tesserati, morti esclusi. Scorre i tesserati in ordine di
        numero, che è l'ordine dei giocatori nel mondo: la somma resta identica, fino all'ultimo
        decimale, a quando si scorreva il mondo intero per ogni polisportiva.
        """
        self.indicecollettivotesserati = sum(giocatori[gid].indice_collettivo_valore for gid in sorted(set(self.tesserati)) if gid in giocatori and gid not in ids_morti)

    def aggiungi_tesserato(self, gid, icv):
        if gid not in self.tesserati:
            self.tesserati.append(gid)
            self.indicecollettivotesserati += icv

    def rimuovi_tesserato(self, gid, icv):
        if gid in self.tesserati:
            self.tesserati.remove(gid)
            self.indicecollettivotesserati = max(0., self.indicecollettivotesserati - icv)

    def aggiorna_gloria(self, giocatori, ids_morti):
        """Ricalcola la gloria da coppe, medaglie, valore, età e numero dei tesserati attivi."""
        base = 60.
        c_o, c_a, c_b, c_l = 100, 50, 20, 5
        m_o, m_a, m_b, m_l = 30, 15, 5, 1
        k_c, k_m, k_icv, eta_ref, k_eta, k_num = 12., 8., 0.4, 35., 1.5, 15.
        p_c = self.coppe_oro * c_o + self.coppe_argento * c_a + self.coppe_bronzo * c_b + self.coppe_legno * c_l
        v_c = math.sqrt(max(0., p_c)) * k_c
        p_m = self.ori * m_o + self.argenti * m_a + self.bronzi * m_b + self.legni * m_l
        v_m = math.sqrt(max(0., p_m)) * k_m
        v_icv = 0.
        v_eta = 0.
        v_num = 0.
        n_val = 0
        eta_gg = 0
        icv_tot = 0.
        for gid in self.tesserati:
            if gid in giocatori and gid not in ids_morti and not giocatori[gid].ritirato:
                n_val += 1
                eta_gg += giocatori[gid].eta
                icv_tot += giocatori[gid].indice_collettivo_valore
        if n_val > 0 and ANNO_SIMULAZIONE_GIORNI > 0:
            icv_m = icv_tot / n_val
            eta_m_a = eta_gg / n_val / ANNO_SIMULAZIONE_GIORNI
            v_icv = icv_m * k_icv
            v_eta = max(0., eta_ref - eta_m_a) * k_eta
        if self.maxtesserati > 0:
            v_num = (len(self.tesserati) / self.maxtesserati) * k_num
        self.gloria = max(1, int(base + v_c + v_m + v_icv + v_eta + v_num))
