"""
L'archivio di MESS: il salvataggio del mondo in un file JSON firmato.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 2 del piano, dallo smontaggio di sd.py, e lo stesso giorno la
tappa 3, secondo la decisione D4, sostituisce i tre file pickle del vecchio programma con un solo
file JSON accanto al programma. Dalla tappa 7, per il problema P18 e per scelta di Gabriele, il
file è compresso, mess_mondo.json.gz: un mondo di ottomila giocatori pesa 4,5 MB invece di 36, e
resta adatto a git. Il vecchio mess_mondo.json si legge ancora, e il primo salvataggio riuscito
lo sostituisce. Il modello è il salvataggio di Terminal Beast, e quattro sono le sue garanzie.
La firma. Una firma HMAC-SHA256, calcolata sul contenuto in forma canonica, fa accorgere il gioco
di una modifica fatta a mano con un editor; spazi e a capo non contano, quindi il file si può
riformattare, anche dopo averlo decompresso. La chiave sta nel codice, che è pubblico: la firma ferma chi curiosa o vuole barare
con un editor, non chi è deciso a ricalcolarla.
La scrittura sicura. Il mondo si scrive in un file temporaneo forzato su disco; il salvataggio
precedente diventa la copia di sicurezza mess_mondo.json.gz.bak; poi il file temporaneo prende il
posto del salvataggio in un colpo solo. Un'interruzione lascia sempre un file intero.
Il ripiego. Se il salvataggio non si legge, o la firma non torna, il mondo viene dalla copia, che
prende il suo posto, e il file scartato si mette da parte nella cartella salvataggi_illeggibili.
Se non si legge nemmeno la copia, vanno da parte tutti e due e il mondo blocca i salvataggi:
un mondo nuovo, salvato all'uscita, li coprirebbe.
Il numero di formato, che dice come aggiornare i salvataggi vecchi. Il formato 2, della tappa 6,
conserva in UTC l'istante dell'ultimo avanzamento, e aggiunge i diari di giocatori e polisportive,
i giorni per cui conservarli e il registro delle vecchie glorie. Il formato 3, della tappa 7,
registra ogni polisportiva sotto il suo nome, quello che i tesserati portano scritto, e non ha più
nei tesserati né ritirati né assenti. Un salvataggio di un formato vecchio si aggiorna da solo
alla lettura, e si riscrive nel formato nuovo al primo salvataggio.
"""

import contextlib
import datetime
import gzip
import hashlib
import hmac
import json
import os
import shutil
import zlib

import percorsi
from costanti import FILE_MONDO, FILE_MONDO_COPIA, FILE_MONDO_COPIA_VECCHIO, FILE_MONDO_VECCHIO, NUM_GIOCATORI_INIZIALI, VERSIONE
from modelli import DATA, Giocatore, Polisportiva, a_json, da_json, normalizza_nome
from mondo import CONSERVAZIONE_PREDEFINITA
from utilita import adesso, adesso_utc

APPLICAZIONE = "MESS"
FORMATO = 3
CHIAVE_FIRMA = b"MESS_2026_firma_dei_salvataggi_di_Gabriele_e_ClaudIA"
CARTELLA_QUARANTENA = "salvataggi_illeggibili"
# Da dove viene il mondo appena caricato.
NATO = "nato"
CARICATO = "caricato"
DALLA_COPIA = "dalla_copia"


class ErroreSalvataggio(Exception):
    """Un file del mondo che non si può usare: illeggibile, modificato fuori dal gioco, o di un formato sconosciuto."""


class SalvataggioIllegibile(Exception):
    """
    Il salvataggio esiste ma non si legge, e nemmeno la sua copia di sicurezza. Diverso dal file
    assente, quando nasce un mondo nuovo: qui no, perché lo coprirebbe. L'attributo cartella dice
    dove sono state messe da parte le copie dei file, oppure è None se la copia non è riuscita.
    """

    def __init__(self, motivo, cartella=None):
        super().__init__(motivo)
        self.cartella = cartella


def firma(documento):
    """La firma di un documento, cioè di un salvataggio senza la sua firma, calcolata sulla forma canonica."""
    canonico = json.dumps(documento, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hmac.new(CHIAVE_FIRMA, canonico, hashlib.sha256).hexdigest()


def componi(mondo):
    """Il mondo come documento da salvare, senza firma. I giocatori usciti di scena nella sessione non ci sono più."""
    morti = mondo._ids_morti_processati_sessione
    attiva = next((chiave for chiave, p in mondo.polisportive.items() if p is mondo.miapolisportiva_attiva), None)
    return {
        "applicazione": APPLICAZIONE,
        "formato": FORMATO,
        "versione": VERSIONE,
        "salvato": a_json(adesso(), DATA),
        "mondo": {
            "data_simulata": a_json(mondo.datetime_corrente_simulazione, DATA),
            "ultimo_avanzamento": a_json(mondo.datetime_ultimo_run_reale, DATA),
            "prossimo_id": mondo.prossimo_id,
            "polisportiva_attiva": attiva,
            "conservazione_diari": dict(mondo.conservazione_diari),
            "polisportive": {chiave: p.a_dizionario() for chiave, p in mondo.polisportive.items()},
            "giocatori": [g.a_dizionario() for gid, g in sorted(mondo.giocatori.items()) if gid not in morti],
            "vecchie_glorie": list(mondo.vecchie_glorie),
        },
    }


def scrivi(mondo, percorso, percorso_copia):
    """
    Scrive il mondo nel file indicato con la scrittura sicura, e il salvataggio precedente nella
    copia. Restituisce il documento scritto e gli avvisi, cioè le cose andate storte senza danno.
    """
    contenuto = componi(mondo)
    testo = json.dumps({**contenuto, "firma": firma(contenuto)}, ensure_ascii=False, separators=(",", ":"))
    # Con l'ora di compressione a zero, gli stessi dati danno sempre gli stessi byte.
    dati = gzip.compress(testo.encode("utf-8"), compresslevel=6, mtime=0)
    temporaneo = percorso + ".tmp"
    avvisi = []
    try:
        with open(temporaneo, "wb") as f:
            f.write(dati)
            f.flush()
            os.fsync(f.fileno())
        if os.path.exists(percorso):
            try:
                shutil.copy2(percorso, percorso_copia)
            except OSError as e:
                avvisi.append(f"La copia di sicurezza non si è potuta aggiornare: {e}.")
        os.replace(temporaneo, percorso)
    finally:
        if os.path.exists(temporaneo):
            with contextlib.suppress(OSError):
                os.remove(temporaneo)
    return contenuto, avvisi


def leggi(percorso):
    """
    Legge e verifica un file del mondo e restituisce il documento senza la firma; ErroreSalvataggio
    se non va. Il file può essere compresso, come lo scrive il gioco dalla tappa 7, oppure testo.
    """
    try:
        with open(percorso, "rb") as f:
            dati = f.read()
    except OSError as e:
        raise ErroreSalvataggio(f"il file non si apre: {e}") from e
    if dati[:2] == b"\x1f\x8b":
        try:
            dati = gzip.decompress(dati)
        except (OSError, EOFError, zlib.error) as e:
            raise ErroreSalvataggio(f"il file compresso è rovinato: {e}") from e
    try:
        documento = json.loads(dati.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ErroreSalvataggio(f"il file non è un JSON valido: {e}") from e
    if not isinstance(documento, dict) or "firma" not in documento:
        raise ErroreSalvataggio("il file non è un salvataggio di MESS")
    firma_scritta = documento.pop("firma")
    if not isinstance(firma_scritta, str) or not firma_scritta.isascii() or not hmac.compare_digest(firma_scritta, firma(documento)):
        raise ErroreSalvataggio("la firma non corrisponde al contenuto: il file è stato modificato fuori dal gioco, oppure si è rovinato")
    if documento.get("applicazione") != APPLICAZIONE:
        raise ErroreSalvataggio("il file non è un salvataggio di MESS")
    formato = documento.get("formato")
    if not isinstance(formato, int) or isinstance(formato, bool) or formato < 1:
        raise ErroreSalvataggio(f"il numero di formato non è valido: {formato!r}")
    if formato > FORMATO:
        raise ErroreSalvataggio(f"il file viene da una versione più recente del gioco, con il formato {formato}, mentre questa legge fino al {FORMATO}")
    while documento["formato"] < FORMATO:
        try:
            MIGRAZIONI[documento["formato"]](documento)
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            raise ErroreSalvataggio(f"il salvataggio del formato {documento['formato']} non si è potuto aggiornare: {e}") from e
    return documento


def _dal_formato_1(documento):
    """
    Dal formato 1 al 2: l'istante dell'ultimo avanzamento, scritto con l'ora locale senza fuso,
    passa in UTC; giocatori e polisportive ricevono un diario vuoto; arrivano i giorni di
    conservazione dei diari, predefiniti, e il registro delle vecchie glorie, vuoto.
    """
    mondo = documento["mondo"]
    ultimo = datetime.datetime.fromisoformat(mondo["ultimo_avanzamento"])
    if ultimo.tzinfo is None:
        ultimo = ultimo.astimezone()
    mondo["ultimo_avanzamento"] = ultimo.astimezone(datetime.UTC).isoformat()
    for g in mondo["giocatori"]:
        g.setdefault("diario", [])
    for p in mondo["polisportive"].values():
        p.setdefault("diario", [])
    mondo.setdefault("conservazione_diari", dict(CONSERVAZIONE_PREDEFINITA))
    mondo.setdefault("vecchie_glorie", [])
    documento["formato"] = 2


def _dal_formato_2(documento):
    """
    Dal formato 2 al 3: ogni polisportiva passa sotto il suo nome, senza spazi in più, che è
    quello scritto nei suoi tesserati (problema P16); chi è ritirato, o porta il nome di una
    polisportiva che non c'è, torna libero, e dagli elenchi dei tesserati spariscono assenti,
    ritirati e doppioni (problema P4).
    """
    dati = documento["mondo"]
    nuove = {}
    rinomina = {}
    for chiave, p in dati["polisportive"].items():
        nome = normalizza_nome(p["nome"])
        if nome in nuove:
            raise ValueError(f"due polisportive si chiamano {nome}")
        p["nome"] = nome
        nuove[nome] = p
        rinomina[chiave] = nome
    dati["polisportive"] = nuove
    if dati["polisportiva_attiva"] is not None:
        dati["polisportiva_attiva"] = rinomina[dati["polisportiva_attiva"]]
    giocatori = {g["id"]: g for g in dati["giocatori"]}
    for g in giocatori.values():
        if g["appartenenza"] != "*" and (g["ritirato"] or normalizza_nome(g["appartenenza"]) not in nuove):
            g["appartenenza"] = "*"
        elif g["appartenenza"] != "*":
            g["appartenenza"] = normalizza_nome(g["appartenenza"])
    for nome, p in nuove.items():
        p["tesserati"] = list(dict.fromkeys(gid for gid in p["tesserati"] if gid in giocatori and giocatori[gid]["appartenenza"] == nome))
    for g in giocatori.values():
        if g["appartenenza"] != "*" and g["id"] not in nuove[g["appartenenza"]]["tesserati"]:
            g["appartenenza"] = "*"
    documento["formato"] = 3


MIGRAZIONI = {1: _dal_formato_1, 2: _dal_formato_2}


def _conservazione_da_json(valore):
    if not isinstance(valore, dict) or set(valore) != set(CONSERVAZIONE_PREDEFINITA):
        raise ValueError(f"Mondo: il campo conservazione_diari non è valido: {valore!r}")
    for giorni in valore.values():
        if not isinstance(giorni, int) or isinstance(giorni, bool) or giorni < 0:
            raise ValueError(f"Mondo: il campo conservazione_diari non è valido: {valore!r}")
    return dict(valore)


def _vecchie_glorie_da_json(valore):
    if not isinstance(valore, list) or not all(isinstance(voce, dict) and isinstance(voce.get("nome"), str) and isinstance(voce.get("data"), str) for voce in valore):
        raise ValueError("Mondo: il registro delle vecchie glorie non è valido")
    return list(valore)


def costruisci(documento, mondo):
    """
    Porta nel mondo il contenuto di un documento letto e verificato. Se un dato non va solleva
    ErroreSalvataggio, e il mondo resta com'era: lo si tocca soltanto quando tutto è stato letto.
    """
    try:
        dati = documento["mondo"]
        data_simulata = da_json(dati["data_simulata"], DATA, "Mondo", "data_simulata")
        ultimo_avanzamento = da_json(dati["ultimo_avanzamento"], DATA, "Mondo", "ultimo_avanzamento")
        if ultimo_avanzamento.tzinfo is None:
            raise ValueError("Mondo: l'istante dell'ultimo avanzamento non ha il fuso")
        conservazione = _conservazione_da_json(dati["conservazione_diari"])
        vecchie_glorie = _vecchie_glorie_da_json(dati["vecchie_glorie"])
        prossimo_id = da_json(dati["prossimo_id"], int, "Mondo", "prossimo_id")
        giocatori = {}
        for voce in dati["giocatori"]:
            g = Giocatore.da_dizionario(voce)
            if g.id in giocatori:
                raise ValueError(f"Giocatore {g.id}: identificativo ripetuto")
            giocatori[g.id] = g
        if not isinstance(dati["polisportive"], dict):
            raise ValueError("Mondo: il campo polisportive non è valido")
        polisportive = {}
        for chiave, voce in dati["polisportive"].items():
            p = Polisportiva.da_dizionario(voce)
            if chiave != p.nome:
                raise ValueError(f"Polisportiva {p.nome}: è registrata sotto un altro nome, {chiave!r}")
            p.aggiorna_ict(giocatori, set())
            polisportive[chiave] = p
        attiva = dati["polisportiva_attiva"]
        if attiva is not None and attiva not in polisportive:
            raise ValueError(f"Mondo: la polisportiva attiva {attiva!r} non esiste")
    except KeyError as e:
        raise ErroreSalvataggio(f"manca il dato {e}") from e
    except (TypeError, ValueError, AttributeError) as e:
        raise ErroreSalvataggio(f"un dato non è valido: {e}") from e
    mondo.datetime_corrente_simulazione = data_simulata
    mondo.datetime_ultimo_run_reale = ultimo_avanzamento
    mondo.giocatori = giocatori
    mondo.polisportive = polisportive
    mondo.miapolisportiva_attiva = polisportive[attiva] if attiva is not None else None
    mondo.prossimo_id = max(prossimo_id, max(giocatori, default=0) + 1)
    mondo.conservazione_diari = conservazione
    mondo.vecchie_glorie = vecchie_glorie


def _metti_da_parte(*file_da_salvare):
    """Copia i file indicati in una cartella datata dentro salvataggi_illeggibili; ne restituisce il percorso, o None."""
    cartella = percorsi.percorso(os.path.join(CARTELLA_QUARANTENA, adesso().strftime("%Y-%m-%d_%H-%M-%S")))
    try:
        os.makedirs(cartella, exist_ok=True)
        for origine in file_da_salvare:
            if os.path.exists(origine):
                shutil.copy2(origine, cartella)
    except OSError:
        return None
    return cartella


def _quanti(giocatori, polisportive):
    """Giocatori e polisportive contati, con il singolare quando serve."""
    return f"{giocatori} {'giocatore' if giocatori == 1 else 'giocatori'} e {polisportive} {'polisportiva' if polisportive == 1 else 'polisportive'}"


def _riassunto(mondo):
    testo = f"{_quanti(len(mondo.giocatori), len(mondo.polisportive))}, data simulata {mondo.datetime_corrente_simulazione:%d/%m/%Y %H:%M}."
    if mondo.miapolisportiva_attiva is not None:
        testo += f" Polisportiva attiva: {mondo.miapolisportiva_attiva.nome}."
    return testo


def _fai_nascere(mondo):
    """Un mondo nuovo: la data simulata parte da oggi, e i primi giocatori nascono subito."""
    mondo.datetime_corrente_simulazione = ora = adesso()
    mondo.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=8)
    mondo.notifica(f"Nessun salvataggio trovato: nasce un mondo nuovo, con {NUM_GIOCATORI_INIZIALI} giocatori.")
    # I messaggi della generazione ripeterebbero la frase qui sopra.
    notifica, mondo.notifica = mondo.notifica, lambda *_args: None
    try:
        mondo.crea_giocatori_casuali(NUM_GIOCATORI_INIZIALI, ora)
    finally:
        mondo.notifica = notifica
    mondo.nuovi_giocatori_sessione.clear()


def carica(mondo):
    """
    Carica il mondo dal salvataggio, oppure dalla copia di sicurezza se il salvataggio non si
    può usare; se non c'è nessuno dei due, fa nascere un mondo nuovo. Restituisce da dove viene il
    mondo: NATO, CARICATO o DALLA_COPIA. Se i file ci sono ma nessuno dei due si legge, blocca i
    salvataggi del mondo e solleva SalvataggioIllegibile.
    """
    principale = percorsi.percorso(FILE_MONDO)
    copia = percorsi.percorso(FILE_MONDO_COPIA)
    if not os.path.exists(principale) and not os.path.exists(copia):
        # Prima della tappa 7 il salvataggio non era compresso, e aveva un altro nome.
        principale = percorsi.percorso(FILE_MONDO_VECCHIO)
        copia = percorsi.percorso(FILE_MONDO_COPIA_VECCHIO)
    esiste_principale = os.path.exists(principale)
    esiste_copia = os.path.exists(copia)
    if not esiste_principale and not esiste_copia:
        _fai_nascere(mondo)
        return NATO
    motivo = f"il file {os.path.basename(principale)} non c'è"
    if esiste_principale:
        try:
            costruisci(leggi(principale), mondo)
        except ErroreSalvataggio as e:
            motivo = str(e)
        else:
            mondo.notifica(f"Mondo caricato: {_riassunto(mondo)}")
            return CARICATO
    if esiste_copia:
        try:
            costruisci(leggi(copia), mondo)
        except ErroreSalvataggio as e:
            motivo = f"{motivo}; e la copia di sicurezza nemmeno, perché {e}"
        else:
            _annuncia_ripiego(mondo, motivo, principale, copia, esiste_principale)
            return DALLA_COPIA
    mondo.salvataggio_bloccato = True
    raise SalvataggioIllegibile(motivo, _metti_da_parte(principale, copia))


def _annuncia_ripiego(mondo, motivo, principale, copia, esiste_principale):
    """Il mondo viene dalla copia: la copia prende il posto del salvataggio, che va messo da parte."""
    cartella = _metti_da_parte(principale) if esiste_principale else None
    messaggio = f"Il salvataggio non si può usare: {motivo}. Il mondo viene dalla copia di sicurezza"
    try:
        shutil.copy2(copia, principale)
        messaggio += ", che ha preso il suo posto."
    except OSError as e:
        messaggio += f", che però non ha potuto prendere il suo posto: {e}."
    if cartella:
        messaggio += f" Il file scartato è stato messo da parte nella cartella {cartella}."
    mondo.notifica(messaggio)
    mondo.notifica(f"Mondo caricato dalla copia: {_riassunto(mondo)}")


def salva(mondo):
    """Salva il mondo; restituisce vero se è riuscito. Non salva mai sopra un salvataggio che non si è potuto leggere."""
    if mondo.salvataggio_bloccato:
        mondo.notifica("Salvataggio rifiutato: il salvataggio esistente non si è potuto leggere, e il gioco non lo copre.")
        return False
    mondo.sfoltisci_diari()
    try:
        contenuto, avvisi = scrivi(mondo, percorsi.percorso(FILE_MONDO), percorsi.percorso(FILE_MONDO_COPIA))
    except (OSError, TypeError, ValueError) as e:
        mondo.notifica(f"Salvataggio non riuscito: {e}. Il salvataggio precedente è rimasto com'era.")
        return False
    salvato = contenuto["mondo"]
    testo = f"Mondo salvato: {_quanti(len(salvato['giocatori']), len(salvato['polisportive']))}."
    usciti = len(mondo.giocatori) - len(salvato["giocatori"])
    if usciti == 1:
        testo += " Il giocatore uscito di scena in questa sessione non ne fa più parte."
    elif usciti > 1:
        testo += f" I {usciti} giocatori usciti di scena in questa sessione non ne fanno più parte."
    mondo.notifica(testo)
    for avviso in avvisi:
        mondo.notifica(avviso)
    _togli_il_vecchio(mondo)
    return True


def _togli_il_vecchio(mondo):
    """Dopo un salvataggio compresso riuscito, il salvataggio non compresso della tappa 6 e la sua copia non servono più."""
    tolti = []
    for nome in (FILE_MONDO_VECCHIO, FILE_MONDO_COPIA_VECCHIO):
        vecchio = percorsi.percorso(nome)
        if os.path.exists(vecchio):
            try:
                os.remove(vecchio)
            except OSError as e:
                mondo.notifica(f"Il vecchio file {nome} non si è potuto togliere: {e}.")
            else:
                tolti.append(nome)
    if tolti:
        mondo.notifica(f"Il mondo ora si salva compresso, in {FILE_MONDO}: {' e '.join(tolti)}, del formato di prima, non servono più e sono stati tolti.")
