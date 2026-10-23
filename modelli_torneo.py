"""
I modelli di torneo di MESS: com'è fatto un torneo, quando si gioca, quanto costa, e i loro file.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-13 con la tappa 12, decisioni D9, D13 e D32 e punto 3.3 del progetto: copiato da
TournamentModel di models.py e da tournament_manager.py di Terminal Beast, e corretto.
Un modello dice tutto ciò che serve a far nascere le sue edizioni: il tipo, individuale o a squadre;
il sesso, maschile, femminile o aperto, cioè misto, scelta di Gabriele in D32; la formula; la
ricorrenza, cioè ogni quanto si gioca e in che giorno, con quanti giorni d'iscrizione prima; il
minimo d'iscritti; i set, con le fasi finali che possono giocarne di più, così un ricorrente ha la
finale al meglio dei 5, D26, e il mondiale i 5 set dai quarti, D32; quanti turni si giocano in un
giorno, fino a tre o quattro come vuole D32, risposta 4 di Gabriele; l'importanza, che pesa punti
allenamento, esperienza, punti della classifica e palmarès; la quota d'iscrizione, il contributo
della federazione e il montepremi minimo; i posti premiati e la pendenza dei premi; la
qualificazione; e i filtri di classe e d'età di Terminal Beast, che il calendario predefinito non
usa, perché D32 vuole i tornei aperti a tutte le classi.
L'identificativo nasce col modello e non cambia mai, nemmeno quando si rinomina: il calendario del
mondo si lega a lui e non al nome. Spariscono i campi di Terminal Beast senza senso qui: famiglie,
archetipi, punti del pareggio, soglia di fatica, trattenuta dell'organizzatore, inviti automatici,
riempimento, seme del modello, invitati speciali. E si correggono i suoi difetti: da_dizionario
controlla ogni campo e rifiuta quelli sconosciuti, invece di accettare tutto; a_dizionario dà un
dizionario nuovo, invece di quello dell'oggetto; due nomi uguali a parte le maiuscole non si
sovrascrivono più; i file illeggibili non finiscono soltanto nel registro, ma in problemi(), che il
mondo e la finestra leggono.
I modelli stanno nella cartella tornei, dentro la cartella del mondo dal 2026-10-23, un file JSON per modello, e non nel
salvataggio, D9: ogni edizione aperta ne conserva una copia congelata, così l'editor cambia soltanto
le edizioni future. Al primo uso, se la cartella manca o è vuota, si copiano i predefiniti che
viaggiano col programma, in dati/tornei/modelli.
Dal collaudo di gioco di Gabriele, il 24 ottobre 2026: il ripristino del calendario predefinito che si
ferma a metà porta nel suo errore la cartella prima_del_ripristino_ dove sono già finiti dei file, perché
il messaggio la nomini; se non c'è finito niente, la cartella vuota se ne va. Con le verifiche dello
stesso collaudo il modello rinominato con le sole maiuscole non cancella più il suo file, e quello
rinominato quando il file di prima non si toglie lascia le cose come stavano. È di Gabriele Battaglia
(IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import contextlib
import copy
import dataclasses
import datetime
import json
import os
import shutil

import classe
import formule
import percorsi
from costanti import MINIMO_ISCRITTI, MONTEPREMI_MINIMO_MASSIMO
from utilita import adesso

CARTELLA = "tornei"
# I modelli predefiniti, che viaggiano col programma.
RISORSA = os.path.join("dati", "tornei", "modelli")
ESTENSIONE = ".json"
PREFISSO_ID = "modello_"
PREFISSO_RIPRISTINO = "prima_del_ripristino_"
# Il file della cartella tornei che ricorda il numero più alto mai dato a un modello: non è un modello,
# non ha l'estensione dei modelli, e il ripristino del calendario predefinito non lo sposta.
CONTATORE = "ultimo_identificativo.txt"
INDIVIDUALE = "individuale"
SQUADRE = "squadre"
TIPI = (INDIVIDUALE, SQUADRE)
SESSI = ("m", "f", "aperto")
SETTIMANALE = "settimanale"
MENSILE = "mensile"
ANNUALE = "annuale"
RICORRENZE = (SETTIMANALE, MENSILE, ANNUALE)
NESSUNA = "nessuna"
PUNTI_ANNO = "punti_anno"
GLORIA = "gloria"
QUALIFICAZIONI = (NESSUNA, PUNTI_ANNO, GLORIA)
NOME_MINIMO = 3
NOME_MASSIMO = 60
NOTE_MASSIME = 1000
GIORNI_ISCRIZIONE = (1, 60)
SET_AMMESSI = (3, 5)
FINALI_DA = (0, 2, 4, 8)
INCONTRI_AL_GIORNO = (1, 4)
IMPORTANZA = (0.5, 5.0)
PASSO_IMPORTANZA = 0.25
QUOTA_MASSIMA = 1000
CONTRIBUTO_MASSIMO = 5.0
PENDENZA_MASSIMA = 10.0
ETA = (9, 120)
# I nomi che Windows riserva ai dispositivi, anche seguiti da un'estensione.
NOMI_RISERVATI = frozenset({"CON", "PRN", "AUX", "NUL", *(f"COM{n}" for n in range(1, 10)), *(f"LPT{n}" for n in range(1, 10))})
CARATTERI_VIETATI = '<>:"/\\|?*'
CODICI_CLASSE = frozenset(classe.codice(n) for n in range(1, classe.LIVELLI + 1))


@dataclasses.dataclass
class ModelloTorneo:
    """Un modello di torneo: i campi del punto 3.3 del progetto della tappa 12, con i loro valori di partenza."""
    id: str
    nome: str
    note: str = ""
    attivo: bool = True
    tipo: str = INDIVIDUALE
    sesso: str | None = "aperto"
    formula: str = "gironi_32"
    ricorrenza: dict = dataclasses.field(default_factory=lambda: {"tipo": SETTIMANALE, "giorno": 5})
    giorni_iscrizione: int = 14
    minimo_iscritti: int = MINIMO_ISCRITTI
    set_al_meglio: int = 3
    set_finali: int = 5
    finali_da: int = 2
    incontri_al_giorno: int = 4
    importanza: float = 1.0
    quota_iscrizione: int = 10
    contributo_federazione: float = 1.0
    montepremi_minimo: int = 0
    posti_premiati: int = 8
    pendenza_premi: float = 1.5
    qualificazione: str = NESSUNA
    classe_minima: str | None = None
    classe_massima: str | None = None
    eta_minima: int | None = None
    eta_massima: int | None = None

    def a_dizionario(self):
        """Il modello come dizionario nuovo, per il file e per le copie congelate: niente è condiviso col modello."""
        return copy.deepcopy(dataclasses.asdict(self))

    @classmethod
    def da_dizionario(cls, dati):
        """Il modello dal suo dizionario; ValueError col motivo se un campo manca, è di troppo o non va."""
        problema = problema_dei_campi(dati)
        if problema:
            raise ValueError(problema)
        valori = copy.deepcopy(dati)
        valori["importanza"] = float(valori["importanza"])
        valori["contributo_federazione"] = float(valori["contributo_federazione"])
        valori["pendenza_premi"] = float(valori["pendenza_premi"])
        return cls(**valori)


CAMPI = tuple(campo.name for campo in dataclasses.fields(ModelloTorneo))


def _intero(valore):
    return isinstance(valore, int) and not isinstance(valore, bool)


def _numero(valore):
    return isinstance(valore, (int, float)) and not isinstance(valore, bool)


def _intero_fra(dati, campo, basso, alto, frase):
    valore = dati[campo]
    if not _intero(valore) or not basso <= valore <= alto:
        return f"{frase}: da {basso} a {alto}, non {valore!r}."
    return None


def problema_della_ricorrenza(ricorrenza):
    """None se la ricorrenza va bene; altrimenti il motivo."""
    if not isinstance(ricorrenza, dict) or ricorrenza.get("tipo") not in RICORRENZE:
        return "La ricorrenza dev'essere settimanale, mensile o annuale."
    tipo = ricorrenza["tipo"]
    attesi = {SETTIMANALE: {"tipo", "giorno"}, MENSILE: {"tipo", "giorno"}, ANNUALE: {"tipo", "mese", "giorno"}}[tipo]
    if set(ricorrenza) != attesi:
        return f"La ricorrenza {tipo} ha i campi {', '.join(sorted(attesi))}."
    giorno = ricorrenza["giorno"]
    if tipo == SETTIMANALE:
        if not _intero(giorno) or not 0 <= giorno <= 6:
            return "Il giorno della settimana va da 0, lunedì, a 6, domenica."
        return None
    if not _intero(giorno) or not 1 <= giorno <= 28:
        return "Il giorno del mese va da 1 a 28, perché ci sia in ogni mese."
    if tipo == ANNUALE and (not _intero(ricorrenza["mese"]) or not 1 <= ricorrenza["mese"] <= 12):
        return "Il mese va da 1 a 12."
    return None


def problema_dei_campi(dati):
    """
    None se il dizionario descrive un modello, campo per campo, senza guardare la formula; altrimenti
    il motivo, in una frase. I controlli che chiedono la formula li fa problema.
    """
    if not isinstance(dati, dict):
        return "Il modello non è descritto come si deve."
    sconosciuti = sorted(set(dati) - set(CAMPI))
    if sconosciuti:
        return f"Il modello ha campi sconosciuti: {', '.join(sconosciuti)}."
    mancanti = [campo for campo in CAMPI if campo not in dati]
    if mancanti:
        return f"Al modello mancano dei campi: {', '.join(mancanti)}."
    if not isinstance(dati["id"], str) or not dati["id"].startswith(PREFISSO_ID) or not dati["id"][len(PREFISSO_ID):].isdigit():
        return f"L'identificativo del modello dev'essere {PREFISSO_ID} seguito da un numero."
    if not isinstance(dati["nome"], str) or not NOME_MINIMO <= len(dati["nome"].strip()) <= NOME_MASSIMO or dati["nome"] != dati["nome"].strip():
        return f"Il nome del modello deve avere da {NOME_MINIMO} a {NOME_MASSIMO} caratteri, senza spazi all'inizio e alla fine."
    if not isinstance(dati["note"], str) or len(dati["note"]) > NOTE_MASSIME:
        return f"Le note sono un testo di al massimo {NOTE_MASSIME} caratteri."
    if not isinstance(dati["attivo"], bool):
        return "Attivo dev'essere sì o no."
    if dati["tipo"] not in TIPI:
        return "Il tipo dev'essere individuale o squadre."
    if dati["tipo"] == INDIVIDUALE and dati["sesso"] not in SESSI:
        return "Il sesso di un torneo individuale è maschile, femminile o aperto."
    if dati["tipo"] == SQUADRE and dati["sesso"] is not None:
        return "Un torneo a squadre non ha sesso: le squadre sono miste."
    if not isinstance(dati["formula"], str) or not dati["formula"]:
        return "La formula si indica col suo identificativo."
    problema = problema_della_ricorrenza(dati["ricorrenza"])
    if problema:
        return problema
    for campo, basso, alto, frase in (("giorni_iscrizione", *GIORNI_ISCRIZIONE, "I giorni d'iscrizione vanno"),
                                      ("minimo_iscritti", MINIMO_ISCRITTI, formule.PARTECIPANTI_MASSIMI, "Il minimo d'iscritti va"),
                                      ("incontri_al_giorno", *INCONTRI_AL_GIORNO, "I turni al giorno vanno"),
                                      ("quota_iscrizione", 0, QUOTA_MASSIMA, "La quota d'iscrizione, in euro, va"),
                                      ("montepremi_minimo", 0, MONTEPREMI_MINIMO_MASSIMO, "Il montepremi minimo, in euro, va"),
                                      ("posti_premiati", 1, formule.PARTECIPANTI_MASSIMI, "I posti premiati vanno")):
        problema = _intero_fra(dati, campo, basso, alto, frase)
        if problema:
            return problema
    if dati["set_al_meglio"] not in SET_AMMESSI or dati["set_finali"] not in SET_AMMESSI or not _intero(dati["set_al_meglio"]) or not _intero(dati["set_finali"]):
        return "Gli incontri si giocano al meglio dei 3 o dei 5 set, anche nelle fasi finali."
    if dati["finali_da"] not in FINALI_DA or not _intero(dati["finali_da"]):
        return "Le fasi finali con i loro set partono dalla finale, 2, dalle semifinali, 4, dai quarti, 8, oppure non ci sono, 0."
    importanza = dati["importanza"]
    if not _numero(importanza) or not IMPORTANZA[0] <= importanza <= IMPORTANZA[1] or (importanza / PASSO_IMPORTANZA) != round(importanza / PASSO_IMPORTANZA):
        return "L'importanza va da 0,5 a 5, a passi di 0,25."
    if not _numero(dati["contributo_federazione"]) or not 0 <= dati["contributo_federazione"] <= CONTRIBUTO_MASSIMO:
        return f"Il contributo della federazione va da 0 a {CONTRIBUTO_MASSIMO:g}: 1 raddoppia il montepremi."
    if not _numero(dati["pendenza_premi"]) or not 1 <= dati["pendenza_premi"] <= PENDENZA_MASSIMA:
        return f"La pendenza dei premi va da 1, premi uguali, a {PENDENZA_MASSIMA:g}."
    if dati["qualificazione"] not in QUALIFICAZIONI:
        return "La qualificazione è nessuna, per punti dell'ultimo anno o per gloria."
    if dati["tipo"] == SQUADRE and dati["qualificazione"] != GLORIA:
        return "Ai tornei a squadre si qualificano le polisportive per gloria."
    if dati["tipo"] == INDIVIDUALE and dati["qualificazione"] == GLORIA:
        return "La qualificazione per gloria vale soltanto per i tornei a squadre."
    for campo in ("classe_minima", "classe_massima"):
        if dati[campo] is not None and dati[campo] not in CODICI_CLASSE:
            return f"La classe si scrive col suo codice, da A1 a K0, oppure si lascia vuota: {dati[campo]!r} non va."
    for campo in ("eta_minima", "eta_massima"):
        if dati[campo] is not None and (not _intero(dati[campo]) or not ETA[0] <= dati[campo] <= ETA[1]):
            return f"L'età va da {ETA[0]} a {ETA[1]} anni, oppure si lascia vuota."
    if dati["classe_minima"] and dati["classe_massima"] and _livello(dati["classe_massima"]) > _livello(dati["classe_minima"]):
        return "La classe massima dev'essere più alta della minima, o la stessa."
    if dati["eta_minima"] is not None and dati["eta_massima"] is not None and dati["eta_minima"] > dati["eta_massima"]:
        return "L'età minima non può superare la massima."
    if dati["tipo"] == SQUADRE and any(dati[campo] is not None for campo in ("classe_minima", "classe_massima", "eta_minima", "eta_massima")):
        return "I filtri di classe e d'età valgono soltanto per i tornei individuali."
    # La revisione del 14 ottobre 2026: un modello a squadre con un montepremi prometteva premi che la
    # chiusura della coppa non paga, perché la coppa si gioca per le coppe, risposta 14 di Gabriele.
    if dati["tipo"] == SQUADRE and (dati["quota_iscrizione"] or dati["contributo_federazione"] or dati["montepremi_minimo"]):
        return "Un torneo a squadre non ha premi in euro: quota d'iscrizione, contributo della federazione e montepremi minimo restano a zero."
    return None


def _livello(codice):
    """Il livello di un codice di classe, da 1 per A1 a 100 per K0."""
    return 10 * classe.LETTERE.index(codice[0]) + int(codice[1])


# La ricorrenza e le date.

def _data(giorno):
    return giorno.date() if isinstance(giorno, datetime.datetime) else giorno


def prossima_data(modello, dopo):
    """La prima data della ricorrenza del modello da dopo in avanti, dopo compreso; dopo è una data o una data con l'ora."""
    giorno = _data(dopo)
    ricorrenza = modello.ricorrenza
    if ricorrenza["tipo"] == SETTIMANALE:
        return giorno + datetime.timedelta(days=(ricorrenza["giorno"] - giorno.weekday()) % 7)
    if ricorrenza["tipo"] == MENSILE:
        if giorno.day <= ricorrenza["giorno"]:
            return giorno.replace(day=ricorrenza["giorno"])
        anno, mese = (giorno.year + 1, 1) if giorno.month == 12 else (giorno.year, giorno.month + 1)
        return datetime.date(anno, mese, ricorrenza["giorno"])
    candidata = datetime.date(giorno.year, ricorrenza["mese"], ricorrenza["giorno"])
    return candidata if candidata >= giorno else datetime.date(giorno.year + 1, ricorrenza["mese"], ricorrenza["giorno"])


def nome_del_giorno(numero):
    """Il nome del giorno della settimana, da 0, lunedì, a 6, domenica."""
    return ("lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica")[numero]


def nome_del_mese(numero):
    return ("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre")[numero - 1]


# La formula del modello.

def _formule_valide(formule_date):
    return formule.leggi()[0] if formule_date is None else formule_date


def formula_del_modello(modello, formule_date=None):
    """La formula valida del modello, oppure None."""
    return next((f for f in _formule_valide(formule_date) if f["id"] == modello.formula), None)


def tetto(modello, formule_date=None):
    """Quanti iscritti al massimo in una sede: i partecipanti della prima fase della formula; None se la formula non c'è."""
    formula_data = formula_del_modello(modello, formule_date)
    return None if formula_data is None else formule.tetto(formula_data)


def idoneo(modello, g):
    """
    Vero se il giocatore può iscriversi a un'edizione del modello individuale: il sesso, con gli aperti
    per tutti, e i filtri di classe e d'età, se ci sono. Chi gioca e chi può pagare lo dicono le
    regole delle iscrizioni, non il modello.
    """
    if modello.tipo != INDIVIDUALE:
        return False
    if modello.sesso != "aperto" and g.sesso != modello.sesso:
        return False
    if modello.classe_minima or modello.classe_massima:
        livello = classe.livello(classe.punteggio(g))
        if modello.classe_minima and livello > _livello(modello.classe_minima):
            return False
        if modello.classe_massima and livello < _livello(modello.classe_massima):
            return False
    anni = g.eta_anni
    if modello.eta_minima is not None and anni < modello.eta_minima:
        return False
    return modello.eta_massima is None or anni < modello.eta_massima + 1


def giorni_di_gioco(fasi_giocate, incontri_al_giorno):
    """I giorni di gioco di una struttura: ogni fase comincia in un giorno nuovo, e in un giorno si giocano al massimo tanti turni."""
    return sum(-(-fase["turni"] // incontri_al_giorno) for fase in fasi_giocate)


def durata_prevista(modello, formula_data):
    """
    I giorni di gioco al massimo di un'edizione del modello: i più lunghi fra tutte le strutture
    possibili, da minimo_iscritti al tetto della formula, contando che ogni fase comincia in un giorno
    nuovo. Con gironi_32 e 4 turni al giorno fa tre giorni, perché con 13 iscritti nasce un girone
    da 5, che ha 5 turni.
    """
    massimo = formule.tetto(formula_data)
    piu_lunga = 0
    for n in range(min(modello.minimo_iscritti, massimo), massimo + 1):
        piu_lunga = max(piu_lunga, giorni_di_gioco(formule.struttura(formula_data, n), modello.incontri_al_giorno))
    return piu_lunga


def problema(modello, formule_date=None):
    """None se il modello può aprire edizioni; altrimenti il motivo: i campi, la formula che non c'è, il minimo e i posti oltre il tetto."""
    errore = problema_dei_campi(dataclasses.asdict(modello))
    if errore:
        return errore
    formula_data = formula_del_modello(modello, formule_date)
    if formula_data is None:
        return f"La formula {modello.formula} non c'è, o non è valida."
    massimo = formule.tetto(formula_data)
    if modello.minimo_iscritti > massimo:
        return f"Il minimo d'iscritti, {modello.minimo_iscritti}, supera il tetto della formula, {massimo}."
    if modello.posti_premiati > massimo:
        return f"I posti premiati, {modello.posti_premiati}, superano il tetto della formula, {massimo}."
    return None


# Il gestore dei file dei modelli, copiato da TournamentManager di Terminal Beast.

# Le letture, per cartella: così due gestori della stessa cartella vedono le stesse scritture.
_CACHE = {}


def azzera_cache():
    """
    I modelli di tutte le cartelle si rileggono dai file alla prossima richiesta: dal 23 ottobre 2026,
    dopo che i dati sono passati in un'altra cartella del mondo, perché una cartella lasciata e poi
    ripresa nella stessa sessione non mostri i modelli di prima.
    """
    _CACHE.clear()


def nome_file(nome):
    """
    Il nome del file di un modello: il nome senza i caratteri che Windows vieta e senza punti e
    spazi alla fine, con maiuscole e spazi com'erano, e l'estensione; torneo se non resta niente.
    In Terminal Beast diventava minuscolo, e due modelli diversi per le sole maiuscole si sovrascrivevano.
    """
    base = "".join("_" if c in CARATTERI_VIETATI or ord(c) < 32 else c for c in str(nome)).strip().rstrip(". ")
    return (base or "torneo") + ESTENSIONE


class GestoreModelli:
    """I modelli di torneo nella cartella tornei della cartella del mondo, o in quella indicata."""

    def __init__(self, cartella=None):
        self._cartella = cartella

    def cartella(self):
        return self._cartella or percorsi.percorso(CARTELLA)

    def azzera_cache(self):
        _CACHE.pop(os.path.abspath(self.cartella()), None)

    def _file_dei_modelli(self):
        cartella = self.cartella()
        if not os.path.isdir(cartella):
            return []
        return sorted(nome for nome in os.listdir(cartella) if nome.lower().endswith(ESTENSIONE) and os.path.isfile(os.path.join(cartella, nome)))

    def _leggi(self):
        """I modelli validi con il loro file, gli scartati con il motivo, e tutti gli identificativi visti."""
        validi, scartati, visti = [], [], set()
        for nome in self._file_dei_modelli():
            percorso = os.path.join(self.cartella(), nome)
            try:
                with open(percorso, encoding="utf-8") as f:
                    dati = json.load(f)
                if isinstance(dati, dict) and isinstance(dati.get("id"), str):
                    visti.add(dati["id"])
                modello = ModelloTorneo.da_dizionario(dati)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as e:
                scartati.append((nome, str(e)))
                continue
            if any(m.id == modello.id for m, _file in validi):
                scartati.append((nome, f"l'identificativo {modello.id} è già di un altro modello"))
                continue
            if any(m.nome.casefold() == modello.nome.casefold() for m, _file in validi):
                scartati.append((nome, f"il nome {modello.nome} è già di un altro modello"))
                continue
            validi.append((modello, nome))
        validi.sort(key=lambda coppia: coppia[0].nome.casefold())
        return validi, scartati, visti

    def _letti(self):
        chiave = os.path.abspath(self.cartella())
        if chiave not in _CACHE:
            _CACHE[chiave] = self._leggi()
        return _CACHE[chiave]

    def modelli(self):
        """I modelli validi, in ordine di nome, in copie, e gli scartati, come coppie di file e motivo."""
        validi, scartati, _visti = self._letti()
        return [copy.deepcopy(m) for m, _file in validi], list(scartati)

    def modello(self, id_modello):
        """Il modello valido con quell'identificativo, in una copia; None se non c'è."""
        return next((m for m in self.modelli()[0] if m.id == id_modello), None)

    def _file_del_modello(self, id_modello):
        return next((file for m, file in self._letti()[0] if m.id == id_modello), None)

    def nuovo_id(self):
        """
        L'identificativo di un modello nuovo, che non torna mai: modello_ e l'istante della creazione,
        AAAAMMGGhhmmss, oppure il numero dopo il più alto che i file usano, compresi quelli scartati ma
        leggibili, se è più grande. Un modello eliminato non presta mai il suo numero, e con lui la sua
        storia nel calendario del mondo, l'ultima apertura, la numerazione delle edizioni e le
        differite, a un modello che nasce dopo: nemmeno dopo il ripristino del calendario predefinito,
        né se si elimina l'ultimo nato, come succedeva prima della revisione del 14 ottobre 2026 col
        numero dopo il più alto. I modelli predefiniti tengono i loro numeri piccoli, da 1 a 10.
        """
        _validi, _scartati, visti = self._letti()
        numeri = [_numero_dell_id(i) for i in visti]
        numero = max(int(adesso().strftime("%Y%m%d%H%M%S")), max(numeri, default=0) + 1, self._ultimo_dato() + 1)
        while f"{PREFISSO_ID}{numero}" in visti:
            numero += 1
        return f"{PREFISSO_ID}{numero}"

    def _ultimo_dato(self):
        """Il numero più alto mai salvato in questa cartella, che il file CONTATORE ricorda anche dopo un'eliminazione o un ripristino; zero se non c'è."""
        try:
            with open(os.path.join(self.cartella(), CONTATORE), encoding="utf-8") as f:
                return int(f.read().strip())
        except (OSError, ValueError):
            return 0

    def _ricorda_id(self, id_modello):
        numero = _numero_dell_id(id_modello)
        if numero > self._ultimo_dato():
            _scrivi_sicuro(os.path.join(self.cartella(), CONTATORE), f"{numero}\n")

    def problema_nome(self, nome, escluso=None):
        """
        Perché il nome non va per un modello, oppure None. escluso è l'identificativo del modello che
        si sta rinominando, che può tenere il suo nome. Rifiuta i nomi uguali a parte le maiuscole, i
        nomi che darebbero lo stesso file, e i nomi che Windows riserva ai dispositivi, CON, PRN,
        AUX, NUL, da COM1 a COM9 e da LPT1 a LPT9, anche seguiti da un'estensione.
        """
        if not isinstance(nome, str) or not NOME_MINIMO <= len(nome.strip()) <= NOME_MASSIMO:
            return f"Il nome deve avere da {NOME_MINIMO} a {NOME_MASSIMO} caratteri."
        if nome != nome.strip():
            return "Il nome non comincia e non finisce con uno spazio."
        if nome.rstrip(".") != nome:
            return "Il nome non finisce con un punto: Windows lo toglierebbe dal nome del file."
        base = nome_file(nome)[:-len(ESTENSIONE)]
        if base.split(".")[0].strip().upper() in NOMI_RISERVATI:
            return f"{nome} è un nome che Windows riserva ai dispositivi: se ne sceglie un altro."
        for m, file in self._letti()[0]:
            if m.id == escluso:
                continue
            if m.nome.casefold() == nome.casefold():
                return f"Esiste già un modello che si chiama {m.nome}."
            if file.casefold() == nome_file(nome).casefold():
                return f"Il nome darebbe lo stesso file del modello {m.nome}."
        return None

    def salva(self, modello, formule_date=None):
        """
        Scrive il modello nel suo file, con la scrittura sicura; se è stato rinominato, il file di
        prima se ne va. ValueError col motivo, senza scrivere niente, se il modello o il nome non vanno.
        Dalle verifiche del collaudo di gioco: quando cambiano soltanto le maiuscole, su Windows il file
        scritto è quello di prima, e toglierlo cancellava il modello; ora prende soltanto le maiuscole
        nuove. E se il file di prima non si toglie, se ne va il nuovo e l'OSError sale: niente cambia, e
        non restano due file dello stesso modello.
        """
        errore = problema(modello, formule_date) or self.problema_nome(modello.nome, escluso=modello.id)
        if errore:
            raise ValueError(errore)
        cartella = self.cartella()
        os.makedirs(cartella, exist_ok=True)
        vecchio = self._file_del_modello(modello.id)
        nuovo = nome_file(modello.nome)
        percorso_nuovo = os.path.join(cartella, nuovo)
        _scrivi_sicuro(percorso_nuovo, json.dumps(modello.a_dizionario(), ensure_ascii=False, indent=1) + "\n")
        if vecchio and vecchio != nuovo:
            percorso_vecchio = os.path.join(cartella, vecchio)
            if _stesso_file(percorso_vecchio, percorso_nuovo):
                with contextlib.suppress(OSError):
                    os.rename(percorso_vecchio, percorso_nuovo)
            else:
                try:
                    os.remove(percorso_vecchio)
                except FileNotFoundError:
                    pass
                except OSError:
                    with contextlib.suppress(OSError):
                        os.remove(percorso_nuovo)
                    self.azzera_cache()
                    raise
        self._ricorda_id(modello.id)
        self.azzera_cache()

    def elimina(self, id_modello):
        """Toglie il file del modello; ValueError se il modello non c'è."""
        file = self._file_del_modello(id_modello)
        if file is None:
            raise ValueError(f"Il modello {id_modello} non c'è.")
        os.remove(os.path.join(self.cartella(), file))
        self.azzera_cache()

    def duplica(self, id_modello, formule_date=None):
        """Una copia del modello, con un identificativo nuovo e il nome Copia di, salvata; la restituisce."""
        originale = self.modello(id_modello)
        if originale is None:
            raise ValueError(f"Il modello {id_modello} non c'è.")
        copia = copy.deepcopy(originale)
        copia.id = self.nuovo_id()
        base = f"Copia di {originale.nome}"[:NOME_MASSIMO].rstrip(". ")
        copia.nome = base
        numero = 2
        while self.problema_nome(copia.nome):
            suffisso = f" {numero}"
            copia.nome = base[:NOME_MASSIMO - len(suffisso)].rstrip(". ") + suffisso
            numero += 1
        self.salva(copia, formule_date)
        return copia

    def crea_predefiniti(self):
        """Copia i modelli predefiniti se la cartella manca o non ha modelli; vero se li ha copiati."""
        if self._file_dei_modelli():
            return False
        _copia_predefiniti(self.cartella())
        self.azzera_cache()
        return True

    def ripristina_predefiniti(self):
        """
        Rimette il calendario predefinito: i modelli e il file delle formule di adesso vanno nella
        cartella tornei/prima_del_ripristino_AAAA-MM-GG_HH-MM, così non si perde niente, e al loro
        posto tornano i predefiniti. Restituisce la cartella dove sono andati quelli di prima.
        Il ripristino può fermarsi a metà, con l'OSError del file che non si sposta o non si copia, dopo
        aver già messo da parte una parte dei file: dal collaudo di gioco l'errore porta allora in
        da_parte la cartella dove sono, perché il messaggio la nomini; se non c'è finito niente, la
        cartella vuota se ne va, e l'errore non la porta.
        """
        cartella = self.cartella()
        os.makedirs(cartella, exist_ok=True)
        base = os.path.join(cartella, f"{PREFISSO_RIPRISTINO}{adesso():%Y-%m-%d_%H-%M}")
        da_parte, numero = base, 2
        while os.path.exists(da_parte):
            da_parte = f"{base}_{numero}"
            numero += 1
        os.makedirs(da_parte)
        try:
            for nome in self._file_dei_modelli():
                shutil.move(os.path.join(cartella, nome), os.path.join(da_parte, nome))
            file_formule = percorsi.percorso(formule.NOME_FILE)
            if os.path.exists(file_formule):
                shutil.move(file_formule, os.path.join(da_parte, formule.NOME_FILE))
            _copia_predefiniti(cartella)
        except OSError as errore:
            # rmdir toglie soltanto una cartella vuota: quella con dei file resta, e l'errore la nomina.
            with contextlib.suppress(OSError):
                os.rmdir(da_parte)
            if os.path.isdir(da_parte):
                errore.da_parte = da_parte
            formule.azzera_cache()
            self.azzera_cache()
            raise
        formule.azzera_cache()
        formule.percorso_formule()
        self.azzera_cache()
        return da_parte

    def problemi(self):
        """
        Tutto ciò che impedisce a una parte del calendario di funzionare, in frasi: i file dei modelli
        illeggibili o scartati, con il motivo; i modelli con una formula che non c'è o un tetto che non
        regge; le formule scartate. Il mondo e la finestra li leggono, e niente si ferma in silenzio.
        """
        validi, scartati, _visti = self._letti()
        frasi = [f"Il modello nel file {file} è scartato: {motivo}" for file, motivo in scartati]
        formule_valide, formule_scartate = formule.leggi()
        for m, file in validi:
            errore = problema(m, formule_valide)
            if errore:
                frasi.append(f"Il modello {m.nome}, nel file {file}, non può aprire edizioni: {errore}")
        frasi.extend(f"La formula {chi} è scartata: {motivo}" for chi, motivo in formule_scartate)
        return frasi


def _numero_dell_id(id_modello):
    """Il numero di un identificativo di modello, modello_ seguito da cifre; zero se non lo è."""
    if isinstance(id_modello, str) and id_modello.startswith(PREFISSO_ID) and id_modello[len(PREFISSO_ID):].isdigit():
        return int(id_modello[len(PREFISSO_ID):])
    return 0


def _stesso_file(primo, secondo):
    """Vero se i due percorsi sono lo stesso file, come su Windows due nomi che differiscono per le sole maiuscole."""
    try:
        return os.path.samefile(primo, secondo)
    except OSError:
        return False


def _scrivi_sicuro(percorso, testo):
    temporaneo = percorso + ".tmp"
    try:
        with open(temporaneo, "w", encoding="utf-8") as f:
            f.write(testo)
        os.replace(temporaneo, percorso)
    finally:
        if os.path.exists(temporaneo):
            with contextlib.suppress(OSError):
                os.remove(temporaneo)


def _copia_predefiniti(cartella):
    """I modelli predefiniti dalla risorsa che viaggia col programma alla cartella indicata."""
    origine = percorsi.risorsa(RISORSA)
    os.makedirs(cartella, exist_ok=True)
    if not os.path.isdir(origine):
        return
    for nome in sorted(os.listdir(origine)):
        if nome.lower().endswith(ESTENSIONE):
            shutil.copy2(os.path.join(origine, nome), os.path.join(cartella, nome))
