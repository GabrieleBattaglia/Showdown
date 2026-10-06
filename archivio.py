"""
L'archivio di MESS: il salvataggio del mondo in un file JSON firmato.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 2 del piano, dallo smontaggio di sd.py, e lo stesso giorno la
tappa 3, secondo la decisione D4, sostituisce i tre file pickle del vecchio programma con un solo
file JSON leggibile, mess_mondo.json, accanto al programma. Il modello è il salvataggio di
Terminal Beast, e quattro sono le sue garanzie.
La firma. Una firma HMAC-SHA256, calcolata sul contenuto in forma canonica, fa accorgere il gioco
di una modifica fatta a mano con un editor; spazi e a capo non contano, quindi il file si può
riformattare. La chiave sta nel codice, che è pubblico: la firma ferma chi curiosa o vuole barare
con un editor, non chi è deciso a ricalcolarla.
La scrittura sicura. Il mondo si scrive in un file temporaneo forzato su disco; il salvataggio
precedente diventa la copia di sicurezza mess_mondo.json.bak; poi il file temporaneo prende il
posto del salvataggio in un colpo solo. Un'interruzione lascia sempre un file intero.
Il ripiego. Se il salvataggio non si legge, o la firma non torna, il mondo viene dalla copia, che
prende il suo posto, e il file scartato si mette da parte nella cartella salvataggi_illeggibili.
Se non si legge nemmeno la copia, vanno da parte tutti e due e il mondo blocca i salvataggi:
un mondo nuovo, salvato all'uscita, li coprirebbe.
Il numero di formato, che dirà alle versioni future come aggiornare i salvataggi vecchi.
"""

import contextlib
import datetime
import hashlib
import hmac
import json
import os
import shutil

import percorsi
from costanti import FILE_MONDO, FILE_MONDO_COPIA, NUM_GIOCATORI_INIZIALI, VERSIONE
from modelli import DATA, Giocatore, Polisportiva, a_json, da_json
from utilita import adesso

APPLICAZIONE = "MESS"
FORMATO = 1
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
            "polisportive": {chiave: p.a_dizionario() for chiave, p in mondo.polisportive.items()},
            "giocatori": [g.a_dizionario() for gid, g in sorted(mondo.giocatori.items()) if gid not in morti],
        },
    }


def scrivi(mondo, percorso, percorso_copia):
    """
    Scrive il mondo nel file indicato con la scrittura sicura, e il salvataggio precedente nella
    copia. Restituisce il documento scritto e gli avvisi, cioè le cose andate storte senza danno.
    """
    contenuto = componi(mondo)
    testo = json.dumps({**contenuto, "firma": firma(contenuto)}, ensure_ascii=False, indent=1) + "\n"
    temporaneo = percorso + ".tmp"
    avvisi = []
    try:
        with open(temporaneo, "w", encoding="utf-8", newline="\n") as f:
            f.write(testo)
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
    """Legge e verifica un file del mondo e restituisce il documento senza la firma; ErroreSalvataggio se non va."""
    try:
        with open(percorso, encoding="utf-8") as f:
            documento = json.load(f)
    except OSError as e:
        raise ErroreSalvataggio(f"il file non si apre: {e}") from e
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
    # Qui si applicheranno, in ordine, le migrazioni dai formati più vecchi, quando ce ne saranno.
    return documento


def costruisci(documento, mondo):
    """
    Porta nel mondo il contenuto di un documento letto e verificato. Se un dato non va solleva
    ErroreSalvataggio, e il mondo resta com'era: lo si tocca soltanto quando tutto è stato letto.
    """
    try:
        dati = documento["mondo"]
        data_simulata = da_json(dati["data_simulata"], DATA, "Mondo", "data_simulata")
        ultimo_avanzamento = da_json(dati["ultimo_avanzamento"], DATA, "Mondo", "ultimo_avanzamento")
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
    ora = adesso()
    mondo.datetime_corrente_simulazione = ora
    mondo.datetime_ultimo_run_reale = ora - datetime.timedelta(hours=8)
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
    esiste_principale = os.path.exists(principale)
    esiste_copia = os.path.exists(copia)
    if not esiste_principale and not esiste_copia:
        _fai_nascere(mondo)
        return NATO
    motivo = f"il file {FILE_MONDO} non c'è"
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
    return True
