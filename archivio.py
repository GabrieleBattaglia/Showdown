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
nei tesserati né ritirati né assenti. Il formato 4, della tappa 8, aggiunge l'economia: cassa,
vendite e bilanci delle polisportive, esperienza, fedeltà, pazienza, arretrati e bandiera dei
giocatori. Il formato 5, della tappa 9, del 2026-10-07, aggiunge a ogni giocatore il temperamento,
ricavato dal suo numero come alla nascita, e la sede dell'infortunio: non precisata per chi era già
infortunato, che resta fermo come prima; dal 2026-10-08, prima che il formato fosse pubblicato,
anche la data simulata dell'ultima amichevole, vuota per tutti, perché nessuno ne aveva ancora
giocate con la regola di una al giorno; un salvataggio del 5 scritto prima di quel giorno, senza
il campo, si legge lo stesso e lo riceve vuoto. Il valore complessivo non si salva, e si ricalcola alla
lettura con i pesi del momento. Un salvataggio di un formato vecchio si aggiorna da solo alla
lettura, e si riscrive nel formato nuovo al primo salvataggio; le versioni di prima rifiutano un
salvataggio di un formato più recente, con il loro messaggio.
Dal 2026-10-07, per gli effetti sonori della decisione D24, salva_con_avvisi restituisce a parte
gli avvisi di un salvataggio riuscito, perché la finestra li faccia sentire con un suono loro.
Il formato 6, della tappa 11, del 2026-10-09, decisione D31: i punti allenamento con la virgola, al
posto dei vecchi punti esperienza; l'indole al posto dell'archetipo, con il programma e l'intensità;
i tratti rari dell'allenamento e l'ambizione, ricavati dal numero del giocatore come alla nascita; la
costanza recente, zero per tutti; i contratti. La migrazione è l'unico posto in cui i contratti si
danno d'ufficio: i tesserati ricevono un contratto con lo stipendio che hanno, calcolato con i pesi e
la scala della versione 1.50.0, conservati qui come costanti storiche, così la nuova taratura del
valore non cambia lo stipendio a nessuno fino al rinnovo. Le caratteristiche non si toccano: senza
i tetti propri dell'allenata ogni valore di oggi resta valido così com'è. Alla lettura si controlla
la coerenza fra contratti e appartenenza, e un salvataggio incoerente si rifiuta, con il ripiego
sulla copia di sempre: il salvataggio non si ripara mai in silenzio.
Il formato 7, della tappa 12, del 2026-10-13, decisione D32, il mondo che gioca. Nasce col primo campo
salvato della tappa, l'acciacco del giocatore, e ogni passo seguente della tappa allarga la stessa
migrazione, finché la tappa non esce: un formato solo. La migrazione aggiunge soltanto, e rinomina
un campo: non tocca caratteristiche, valori, contratti, stipendi, casse, fedeltà né esperienza.
Dal 2026-10-16, decisione 4 di Gabriele, accelerare senza cambiare niente: il caricamento lavora con la
raccolta della memoria spenta, e il mondo caricato resta lo stesso.
Il formato 8, della tappa 13, del 2026-10-21, decisione D33, l'allenatore: gli allenatori del mondo, con
il contatore dei loro numeri; lo staff di ogni polisportiva; la classe migliore della carriera di ogni
giocatore. La migrazione dal 7 lascia gli staff vuoti, D33 risposta 16, e segna gli allenatori da far
nascere: li fa nascere il caricamento, quando ci sono i giocatori, un allenatore per ogni ritirato vivo
che può allenare e gli allenatori nati di un mondo della sua età. La classe migliore parte da quella di
oggi, l'unica che si conosce.
Il formato 9, della tappa 14, del 2026-10-23, richiesta di Gabriele: ogni polisportiva ha il comune della
sede. La migrazione dall'8 lo dà a tutte, anche a quelle dell'utente, estratto coi pesi della popolazione
da un caso nato dal nome, come per le polisportive del computer che nascono, e il caso del mondo non si tocca.
Dal 2026-10-23, richiesta di Gabriele, il salvataggio, la copia e i salvataggi illeggibili stanno nella cartella
del mondo, che percorsi.py rilegge a ogni chiamata e che si sceglie dal menu Impostazioni, non più accanto al programma.
Con la verifica finale dello stesso giorno carica può non rifare le copie dei salvataggi illeggibili, per le Riprova dell'avvio.
Il formato 10, del 2026-10-24, con la issue 8 e la decisione D36, scelta di Gabriele: il mondo conserva i filtri della
finestra unica Mercato e ricerca, uno stato per ogni porta d'ingresso, Ctrl+K, Ctrl+Maiusc+G, Ctrl+F e Ctrl+O, coi
filtri di adesso, la ricerca pronta da cui vengono e quelli fatti a mano prima. La migrazione dal 9 dà a ogni porta il
suo stato predefinito, quello della sua ricerca pronta, e non tocca altro; alla lettura ogni campo si controlla, e uno
stato che non va fa rifiutare il salvataggio, col ripiego sulla copia di sempre. Col magnate di D35 andrà per magnate.
Con le verifiche dello stesso giorno lo stato che la migrazione dal 9 dà alle porte è una costante storica del formato
10, come lo stipendio della 1.50.0, e non viene più dal mercato di oggi: quando i filtri cambieranno forma, col magnate,
un mondo del formato 9 diventerà sempre un documento del formato 10 vero, che la migrazione seguente sa leggere.
È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Lo stesso giorno, con le scelte di Gabriele dopo la prova del prototipo, il formato 10 cambia forma senza cambiare
numero, perché nessun mondo vero lo ha ancora: conserva i preset dei filtri di Gabriele, col numero del prossimo, e per
ogni porta la voce della casella scelta coi filtri attuali, non salvati. Dopo la migrazione dal 9 non c'è nessun
preset, il prossimo ha il numero 1 e ogni porta sta sul suo preset di serie. La lettura di quel blocco non rifiuta più il mondo, scelta
di Gabriele: quello che non si legge torna ai filtri di serie, un preset si ripara invece di sparire, e a mondo pronto
ogni riparazione va nel registro degli errori, col dato originale in JSON. Col magnate di D35, nel formato 11, il
blocco andrà dentro ogni magnate, e alla conversione al primo. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus
5.5, UltraCode).
La sera dello stesso giorno, col motore del costruttore di regole chiesto da Gabriele, il formato 10 avrà ancora un'altra
forma, sempre senza cambiare numero: il 24 ottobre sera i mondi di Gabriele, quello in gioco e le sue copie, sono tutti
del formato 9. I preset e i filtri attuali di ogni porta saranno regole con un ordine, e ogni porta avrà la sua regola in
preparazione. Qui c'è già la costante storica dello stato delle porte in quella forma, filtri_di_ricerca_del_formato_10_a_regole,
che le prove confrontano coi preset di serie del motore nuovo; la lettura che ripara e riconosce i filtri a schede sta
in mercato.py. La migrazione dal 9 e la lettura passano alla forma nuova col cambio della finestra, che oggi salva
ancora i filtri a schede. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import contextlib
import datetime
import gc
import gzip
import hashlib
import hmac
import json
import os
import shutil
import struct
import types
import zlib

import classe as modulo_classe
import contratti
import economia
import luoghi
import mercato
import percorsi
import registro
import staff
import tratti
import valore
from calendario import Calendario
from costanti import (
    CAPITALE_INIZIALE,
    ESPERIENZA_MASSIMA,
    FEDELTA_MASSIMA,
    FEDELTA_PER_MESE,
    FILE_MONDO,
    FILE_MONDO_COPIA,
    FILE_MONDO_COPIA_VECCHIO,
    FILE_MONDO_VECCHIO,
    INDOLE_PREDEFINITA,
    INTENSITA_PREDEFINITA,
    MAPPA_ARCHETIPI_INDOLI,
    MESI_MINIMI_MIGRAZIONE,
    NUM_GIOCATORI_INIZIALI,
    SEDE_NON_PRECISATA,
    VERSIONE,
)
from modelli import (
    CAMPI_ACCIACCO_VUOTO,
    CAMPI_SFIDE_VUOTO,
    DATA,
    VOCI_CONTI,
    Giocatore,
    Polisportiva,
    a_json,
    da_json,
    normalizza_nome,
    palmares_vuoto,
    ritmo_iniziale,
    temperamento_innato,
)
from mondo import CONSERVAZIONE_PREDEFINITA
from sfide import RegistroSfide
from utilita import adesso, adesso_utc, senza_raccolta

APPLICAZIONE = "MESS"
FORMATO = 10
CHIAVE_FIRMA = b"MESS_2026_firma_dei_salvataggi_di_Gabriele_e_ClaudIA"
CARTELLA_QUARANTENA = "salvataggi_illeggibili"
# Il segnaposto dei giocatori mentre si scrive il resto del documento, _testo_firmato: due caratteri
# d'uso privato che nessun nome e nessun diario contiene.
_SEGNAPOSTO_GIOCATORI = "giocatori di MESS"
# Da dove viene il mondo appena caricato.
NATO = "nato"
CARICATO = "caricato"
DALLA_COPIA = "dalla_copia"


# Le costanti storiche delle migrazioni, che non cambiano più. L'esperienza che i formati fino al 3
# davano per ogni mese passato nel club, e i pesi e la scala del valore della versione 1.50.0, con
# cui la migrazione dal formato 5 calcola lo stipendio dei contratti dei tesserati di allora.
ESPERIENZA_PER_MESE_FORMATO_3 = 0.1
PESI_VALORE_FORMATO_5 = {
    "lungolineasx": 0.44, "lungolineadx": 0.44, "diagonalesx": 0.49, "diagonaledx": 0.49, "singolaspondasx": 0.48, "singolaspondadx": 0.48,
    "doppiaspondasx": 0.45, "doppiaspondadx": 0.45, "triplaspondasx": 0.33, "triplaspondadx": 0.33, "bomba": 0.36, "battutasx": 0.78,
    "battutadx": 0.78, "chiusura_dritto": 2.22, "chiusura_rovescio": 2.81, "blocco_dritto": 1.35, "blocco_rovescio": 1.61, "difesa": 3.38,
    "tenutapaletta": 1.26, "controllopalla": 0.81, "attacco": 1.29, "precisione": 10.04, "forza": 5.18, "resistenza": 4.71,
}
PESI_TRATTI_FORMATO_5 = {"mancino": 2.9, "ambidestro": 3.4, "giocorapido": 1.2, "cambiovelocita": 4.5}
SCALA_A_FORMATO_5 = -82.61
SCALA_B_FORMATO_5 = 1.3878
# Le voci dei conti che nascono col formato 7: le iscrizioni ai tornei, i premi e i rimborsi.
VOCI_NUOVE_DEL_FORMATO_7 = ("iscrizioni", "premi", "rimborsi")


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


def _canonico(dato):
    return json.dumps(dato, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _testo_firmato(contenuto):
    """
    Il testo del file, in pezzi di byte da scrivere uno dopo l'altro: il documento con la sua firma.
    Dalla tappa 12, decisione 4 di Gabriele del 14 ottobre 2026, i giocatori, quasi tutto il mondo, si
    scrivono una volta sola, nella forma canonica della firma, coi campi in ordine alfabetico, e lo
    stesso testo serve alla firma e al file: prima il mondo si scriveva due volte, una per la firma e una
    per il file, e a regime erano secondi a ogni salvataggio. Al posto dei giocatori il resto del
    documento ha un segnaposto, che si scrive due volte, nelle due forme, ed è piccolo; la firma si
    calcola sui pezzi della forma canonica, senza rifare un testo unico. Il file resta un JSON del
    formato 7: chi lo legge, anche una versione di prima, rifà la forma canonica e trova la stessa
    firma, e i campi di un giocatore si leggono per nome, in qualunque ordine. Se il segnaposto
    comparisse anche altrove, il testo si fa nel modo di prima.
    """
    segno = json.dumps(_SEGNAPOSTO_GIOCATORI, ensure_ascii=False)
    guscio = {**contenuto, "mondo": {**contenuto["mondo"], "giocatori": _SEGNAPOSTO_GIOCATORI}}
    canonico = _canonico(guscio).split(segno)
    if len(canonico) == 2:
        giocatori = _canonico(contenuto["mondo"]["giocatori"]).encode("utf-8")
        calcolo = hmac.new(CHIAVE_FIRMA, canonico[0].encode("utf-8"), hashlib.sha256)
        calcolo.update(giocatori)
        calcolo.update(canonico[1].encode("utf-8"))
        scritto = json.dumps({**guscio, "firma": calcolo.hexdigest()}, ensure_ascii=False, separators=(",", ":")).split(segno)
        if len(scritto) == 2:
            return [scritto[0].encode("utf-8"), giocatori, scritto[1].encode("utf-8")]
    return [json.dumps({**contenuto, "firma": firma(contenuto)}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")]


def congela_la_memoria():
    """
    Mette da parte la memoria del mondo per la raccolta dei cicli di Python, dopo il caricamento e dopo
    ogni salvataggio: decisione 4 di Gabriele del 14 ottobre 2026, accelerare senza cambiare gli esiti,
    dalla verifica del 15 ottobre. Il mondo sono milioni di oggetti che vivono a lungo, e ogni tanto la
    raccolta completa li ripassava tutti: nel mondo a regime circa un secondo, in un giorno qualunque,
    che diventava il giorno peggiore dell'anno. Prima si raccolgono i cicli già da buttare, poi quello che
    resta si mette da parte, e la raccolta ripassa soltanto gli oggetti nati dopo. Un ciclo di oggetti
    messi da parte che diventa da buttare resta in memoria fino alla chiusura: il giorno ne fa pochissimi.
    """
    gc.collect()
    gc.freeze()


def _comprimi(pezzi):
    """
    I pezzi compressi in gzip col livello 6, uno dopo l'altro, senza rifare il testo intero: il file è
    un gzip come quello di gzip.compress, che gzip.decompress legge per intero, e l'intestazione si
    completa come la completa gzip.compress, con l'ora a zero e il sistema 255, così gli stessi dati
    danno sempre gli stessi byte. I byte compressi non sono quelli che gzip.compress darebbe sul testo
    intero, perché il compressore li fa anche secondo i pezzi che riceve: il testo che ne esce è lo stesso.
    """
    compressore = zlib.compressobj(6, zlib.DEFLATED, 31)
    compressi = [compressore.compress(pezzo) for pezzo in pezzi]
    compressi.append(compressore.flush())
    dati = b"".join(compressi)
    return struct.pack("<4sLBB", dati, 0, dati[8], 255) + dati[10:]


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
            "calendario": mondo.calendario.a_dizionario(),
            "sfide": mondo.sfide.a_dizionario(),
            # Dalla tappa 13, formato 8: gli allenatori, in ordine di numero, e il contatore.
            "allenatori": [a.a_dizionario() for _numero, a in sorted(mondo.allenatori.items())],
            "prossimo_allenatore": mondo.prossimo_allenatore,
            # Dalla issue 8, formato 10: i preset dei filtri della finestra Mercato e ricerca e lo stato di ogni porta d'ingresso.
            "filtri_di_ricerca": mercato.filtri_di_ricerca_da_salvare(mondo),
        },
    }


def scrivi(mondo, percorso, percorso_copia):
    """
    Scrive il mondo nel file indicato con la scrittura sicura, e il salvataggio precedente nella
    copia. Restituisce il documento scritto e gli avvisi, cioè le cose andate storte senza danno.
    """
    with senza_raccolta():
        contenuto = componi(mondo)
        # Con l'ora di compressione a zero, gli stessi dati danno sempre gli stessi byte.
        dati = _comprimi(_testo_firmato(contenuto))
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
    if formato == 5:
        _completa_formato_5(documento)
    while documento["formato"] < FORMATO:
        try:
            MIGRAZIONI[documento["formato"]](documento)
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            raise ErroreSalvataggio(f"il salvataggio del formato {documento['formato']} non si è potuto aggiornare: {e}") from e
    return documento


def _completa_formato_5(documento):
    """
    Il formato 5 si è allungato il 2026-10-08, prima di essere pubblicato, con la data dell'ultima
    amichevole: i salvataggi del 5 scritti prima, compresa la loro copia di sicurezza, non ce l'hanno,
    e la ricevono vuota come nella migrazione dal 4. Un documento rovinato resta com'è: lo rifiuta
    poi il controllo dei campi, con il suo messaggio.
    """
    mondo = documento.get("mondo")
    giocatori = mondo.get("giocatori") if isinstance(mondo, dict) else None
    if isinstance(giocatori, list):
        for g in giocatori:
            if isinstance(g, dict):
                g.setdefault("ultima_amichevole", None)


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


def _mesi_nel_club(g, oggi):
    """I mesi passati da quando il giocatore è entrato nel suo club, letti nel diario; zero se è libero o non si sa."""
    club = g["appartenenza"]
    if club == "*":
        return 0.
    for voce in g["diario"]:
        testo = voce.get("testo", "")
        if testo.startswith("Tesserat") and (testo.endswith(f" con {club}.") or f" con {club}," in testo):
            return max(0, (oggi - datetime.datetime.fromisoformat(voce["data"])).days) / 30
    return 0.


def _dal_formato_3(documento):
    """
    Dal formato 3 al 4, con la tappa 8: l'economia. Ogni polisportiva riceve il capitale iniziale,
    nessun tesserato in vendita, nessun bilancio e i conti del mese a zero. Ogni giocatore riceve
    pazienza piena e nessun arretrato; fedeltà ed esperienza vengono dai mesi passati nel club di
    adesso, contati dal diario. La bandiera si decide con un conto fisso sul numero del giocatore,
    uno su cento, così la migrazione non tocca il caso.
    """
    dati = documento["mondo"]
    oggi = datetime.datetime.fromisoformat(dati["data_simulata"])
    for p in dati["polisportive"].values():
        p.setdefault("cassa", CAPITALE_INIZIALE)
        p.setdefault("in_vendita", {})
        p.setdefault("bilanci", [])
        p.setdefault("conti_del_mese", dict.fromkeys(VOCI_CONTI, 0))
    for g in dati["giocatori"]:
        mesi = _mesi_nel_club(g, oggi)
        g.setdefault("esperienza", round(min(ESPERIENZA_MASSIMA, mesi * ESPERIENZA_PER_MESE_FORMATO_3), 2))
        g.setdefault("fedelta", round(min(FEDELTA_MASSIMA, mesi * FEDELTA_PER_MESE), 2))
        g.setdefault("pazienza", 100.)
        g.setdefault("arretrati", 0)
        g.setdefault("bandiera", g["id"] % 100 == 0)
    documento["formato"] = 4


def _dal_formato_4(documento):
    """
    Dal formato 4 al 5, con la tappa 9: ogni giocatore riceve il temperamento che avrebbe avuto
    alla nascita, ricavato dal suo numero senza toccare il caso, e la sede dell'infortunio, non
    precisata per chi è infortunato, così resta fermo come prima, e nessuna per gli altri. La data
    dell'ultima amichevole resta vuota: tutti possono giocarne una già oggi.
    """
    for g in documento["mondo"]["giocatori"]:
        g.setdefault("temperamento", temperamento_innato(g["id"]))
        g.setdefault("infortunio_sede", SEDE_NON_PRECISATA if g["infortunato"] else None)
        g.setdefault("ultima_amichevole", None)
    documento["formato"] = 5


def stipendio_della_1_50(dati_giocatore):
    """
    Lo stipendio che un giocatore del formato 5 chiedeva con la versione 1.50.0: su una vista leggera
    del suo dizionario, con i pesi e la scala di allora, conservati qui come costanti storiche.
    """
    vista = types.SimpleNamespace(**dati_giocatore)
    vista.indice_collettivo_valore = valore.indice(vista, PESI_VALORE_FORMATO_5, PESI_TRATTI_FORMATO_5, SCALA_A_FORMATO_5, SCALA_B_FORMATO_5)
    return economia.stipendio(vista)


def _dal_formato_5(documento):
    """
    Dal formato 5 al 6, con la tappa 11, decisione D31. I punti esperienza diventano punti
    allenamento, con la virgola; l'archetipo diventa l'indole, con la mappa dei nove nomi di prima,
    e il programma parte uguale all'indole, a intensità normale. Talento, apprendista rapido,
    maturazione e ambizione vengono dal numero del giocatore, come alla nascita; la costanza parte
    da zero. Le caratteristiche non si toccano. I tesserati ricevono un contratto con lo stipendio
    che hanno, calcolato come nella versione 1.50.0, e una scadenza di almeno un anno di calendario,
    o della durata che propongono se è più lunga, perché non scadano tutti nei primi mesi; i liberi
    non hanno contratto, e nessuno ha rinnovi o proposte in corso. I conti delle polisportive
    ricevono la voce nuova delle buonuscite, a zero, anche nei bilanci dei mesi passati.
    """
    dati = documento["mondo"]
    oggi = datetime.datetime.fromisoformat(dati["data_simulata"])
    for p in dati["polisportive"].values():
        p["conti_del_mese"].setdefault("buonuscite", 0)
        for bilancio in p["bilanci"]:
            bilancio.setdefault("buonuscite", 0)
    for g in dati["giocatori"]:
        punti = g.pop("puntiesperienza", 0)
        g.setdefault("punti_allenamento", float(punti))
        archetipo = g.pop("archetipo_allenamento", None)
        g.setdefault("indole", MAPPA_ARCHETIPI_INDOLI.get(archetipo, INDOLE_PREDEFINITA))
        g.setdefault("programma", g["indole"])
        g.setdefault("intensita", INTENSITA_PREDEFINITA)
        for campo, innato in tratti.tratti_innati(g["id"]).items():
            g.setdefault(campo, innato)
        g.setdefault("ambizione", tratti.ambizione_innata(g["id"]))
        g.setdefault("costanza", 0.0)
        if "contratto_stipendio" in g:
            continue
        g.update(contratto_stipendio=0, contratto_scadenza=None, rinnovo_stipendio=0, rinnovo_scadenza=None, proposte_rinnovo=0, ultima_trattativa=None)
        if g["appartenenza"] != "*":
            vista = types.SimpleNamespace(**g)
            g["contratto_stipendio"] = stipendio_della_1_50(g)
            mesi = max(MESI_MINIMI_MIGRAZIONE, contratti.durata_proposta(vista))
            g["contratto_scadenza"] = contratti.scadenza_dopo(oggi, mesi).isoformat()
    documento["formato"] = 6


def _dal_formato_6(documento):
    """
    Dal formato 6 al 7, con la tappa 12, decisione D32. Ogni giocatore riceve l'acciacco vuoto: nessuno
    ne ha, perché prima gli acciacchi non c'erano. La data dell'ultima amichevole diventa l'ultimo
    impegno, col suo valore: la regola di un impegno al giorno è una sola, e una sola deve essere la fonte.
    Poi il palmarès vuoto, la data del ritmo sparsa e l'iscrizione automatica accesa, il calendario e
    le sfide vuoti, le voci nuove dei conti a zero, e a ogni polisportiva due sfide da lanciare.
    """
    dati = documento["mondo"]
    oggi = datetime.datetime.fromisoformat(dati["data_simulata"])
    for g in dati["giocatori"]:
        for campo, vuoto in (*CAMPI_ACCIACCO_VUOTO.items(), *palmares_vuoto().items()):
            g.setdefault(campo, vuoto)
        if "ultimo_impegno" not in g:
            g["ultimo_impegno"] = g.pop("ultima_amichevole", None)
        # Il ritmo dei tornei parte sparso sui due mesi che vengono, e l'iscrizione automatica è accesa, risposta 17.
        g.setdefault("prossimo_torneo", ritmo_iniziale(g["id"], oggi).isoformat())
        g.setdefault("iscrizione_automatica", True)
    dati.setdefault("calendario", Calendario().a_dizionario())
    dati.setdefault("sfide", RegistroSfide().a_dizionario())
    # Le voci nuove dei conti, a zero, nel mese in corso e in ogni bilancio; il palmarès recente vuoto;
    # due sfide da lanciare, come il primo del mese, e nessuna giocata.
    for p in dati["polisportive"].values():
        for voce in VOCI_NUOVE_DEL_FORMATO_7:
            p["conti_del_mese"].setdefault(voce, 0)
            for bilancio in p["bilanci"]:
                bilancio.setdefault(voce, 0)
        p.setdefault("palmares_recente", {})
        for campo, vuoto in CAMPI_SFIDE_VUOTO.items():
            p.setdefault(campo, vuoto)
    documento["formato"] = 7


# La classe migliore che la migrazione non sa calcolare: la calcola il caricamento, coi giocatori costruiti.
CLASSE_MIGLIORE_DA_CALCOLARE = -1.0


def _dal_formato_7(documento):
    """
    Dal formato 7 all'8, con la tappa 13, decisione D33. Ogni giocatore riceve la classe migliore da
    calcolare, perché serve il giocatore costruito; ogni polisportiva lo staff vuoto, risposta 16; il
    mondo nessun allenatore, segnato come da far nascere, e il contatore che parte da 1.
    """
    dati = documento["mondo"]
    for g in dati["giocatori"]:
        g.setdefault("classe_migliore", CLASSE_MIGLIORE_DA_CALCOLARE)
        # Il comune di provenienza, richiesta di Gabriele del 22 ottobre 2026: dal numero del giocatore, come alla nascita.
        g.setdefault("luogo", luoghi.luogo_del_giocatore(g["id"]))
    for p in dati["polisportive"].values():
        p.setdefault("staff", [0, 0, 0])
        # La voce nuova dei conti, a zero, nel mese in corso e in ogni bilancio: gli stipendi dello staff.
        p["conti_del_mese"].setdefault("staff", 0)
        for bilancio in p["bilanci"]:
            bilancio.setdefault("staff", 0)
    dati.setdefault("allenatori", None)
    dati.setdefault("prossimo_allenatore", 1)
    documento["formato"] = 8


def _dal_formato_8(documento):
    """
    Dal formato 8 al 9, con la tappa 14, richiesta di Gabriele del 23 ottobre 2026: ogni polisportiva,
    del computer o dell'utente, riceve il comune della sede, estratto dal suo nome come alla nascita.
    """
    for p in documento["mondo"]["polisportive"].values():
        p.setdefault("luogo", luoghi.luogo_della_polisportiva(p["nome"]))
    documento["formato"] = 9


# I filtri del formato 10 a nessun filtro, e il preset di serie di ogni porta coi suoi filtri, costanti storiche del
# 24 ottobre 2026: la migrazione dal 9 non legge il mercato di oggi, che col magnate di D35 cambierà forma.
FILTRI_VUOTI_DEL_FORMATO_10 = {
    "allenatori": False, "liberi": False, "in_vendita": False, "del_computer": False, "tuoi": False, "ritirati": False, "nome": "", "sesso": None,
    "classe_migliore": 0, "eta_massima": 0, "costo_massimo": 0, "disponibili_oggi": False, "ordine": "valore_alto", "ordine_allenatori": "classe",
    "classe_peggiore": 0, "eta_minima": 0, "regione": "", "provincia": "", "comune": "", "polisportiva": "", "tratti": {}, "indole": None,
    "valore_minimo": 0, "stipendio_massimo": 0, "mesi_contratto_massimi": 0, "senza_acciacchi": False, "solo_ritirati_che_allenano": False,
    "solo_nuovi": False, "comprendi_usciti": False, "condizioni": [], "tipo_allenatore": None, "visus": None, "posto_attuale": None,
    "stipendio_capo_massimo": 0, "senza_prelazione_altrui": False,
}
_IN_ATTIVITA_DEL_FORMATO_10 = {"liberi": True, "in_vendita": True, "del_computer": True, "tuoi": True}
PORTE_DEL_FORMATO_10 = {
    "mercato": ("mercato", {"liberi": True, "in_vendita": True, "ordine": "valore_alto"}),
    "allenatori": ("allenatori_liberi", {"allenatori": True, "liberi": True, "ordine_allenatori": "classe"}),
    "ricerca": ("tutti_in_attivita", {**_IN_ATTIVITA_DEL_FORMATO_10, "ordine": "numero"}),
    "amichevole": ("avversari_amichevole", {**_IN_ATTIVITA_DEL_FORMATO_10, "disponibili_oggi": True, "ordine": "classe"}),
}


def filtri_di_ricerca_del_formato_10():
    """
    I filtri della finestra Mercato e ricerca di un mondo che arriva dal formato 9, nella forma del salvataggio, da quelle
    costanti: nessun preset, il prossimo col numero 1, e ogni porta sul suo preset di serie, coi filtri di quel preset
    come filtri attuali. Ogni volta un documento nuovo.
    """
    porte = {porta: {"scelta": scelta, "attuali": {**FILTRI_VUOTI_DEL_FORMATO_10, "tratti": {}, "condizioni": [], **filtri}}
             for porta, (scelta, filtri) in PORTE_DEL_FORMATO_10.items()}
    return {"preset": [], "prossimo_preset": 1, "porte": porte}


# Lo stesso stato delle porte nella forma del costruttore di regole, costante storica della sera del 24 ottobre 2026:
# per ogni porta il preset di serie, le sue regole, il suo ordine e il bersaglio della regola in preparazione, che è su
# Nome o numero, contiene, e vuota. Col cambio della finestra la migrazione dal 9 darà questa, al posto di quella a schede.
PORTE_DEL_FORMATO_10_A_REGOLE = {
    "mercato": ("mercato", [("giocatori", "stato", "uguale", "sul_mercato")], "valore_alto", "giocatori"),
    "allenatori": ("allenatori_liberi", [("allenatori", "stato", "uguale", "libero")], "classe", "allenatori"),
    "ricerca": ("tutti_in_attivita", [("giocatori", "stato", "uguale", "in_attivita")], "numero", "giocatori"),
    "amichevole": ("avversari_amichevole", [("giocatori", "disponibile", "uguale", True)], "classe", "giocatori"),
}


def filtri_di_ricerca_del_formato_10_a_regole():
    """
    I filtri della finestra Mercato e ricerca di un mondo che arriva dal formato 9, nella forma del costruttore di regole:
    nessun preset, il prossimo col numero 1, e ogni porta sul suo preset di serie, con le sue regole come filtri attuali e
    la regola in preparazione di serie. Ogni volta un documento nuovo.
    """
    porte = {}
    for porta, (scelta, regole, ordine, bersaglio) in PORTE_DEL_FORMATO_10_A_REGOLE.items():
        attuali = {"regole": [{"collegamento": "e", "bersaglio": chi, "caratteristica": caratteristica, "operatore": operatore, "valore": valore}
                              for chi, caratteristica, operatore, valore in regole], "ordine": ordine}
        preparazione = {"collegamento": "e", "bersaglio": bersaglio, "caratteristica": "nome", "operatore": "contiene", "valore": ""}
        porte[porta] = {"scelta": scelta, "attuali": attuali, "preparazione": preparazione}
    return {"preset": [], "prossimo_preset": 1, "porte": porte}


def _dal_formato_9(documento):
    """
    Dal formato 9 al 10, con la issue 8 e la decisione D36: nessun preset dei filtri, e ogni porta d'ingresso della
    finestra Mercato e ricerca sul suo preset di serie, come se la finestra non si fosse mai aperta.
    """
    documento["mondo"].setdefault("filtri_di_ricerca", filtri_di_ricerca_del_formato_10())
    documento["formato"] = 10


MIGRAZIONI = {1: _dal_formato_1, 2: _dal_formato_2, 3: _dal_formato_3, 4: _dal_formato_4, 5: _dal_formato_5, 6: _dal_formato_6,
              7: _dal_formato_7, 8: _dal_formato_8, 9: _dal_formato_9}


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
        for g in giocatori.values():
            controlla_contratto(g, polisportive)
        calendario_del_mondo = Calendario.da_dizionario(dati["calendario"])
        sfide_del_mondo = RegistroSfide.da_dizionario(dati["sfide"])
        # Dalla tappa 13 gli allenatori e lo staff; la classe migliore che la migrazione ha lasciato da calcolare.
        allenatori, da_far_nascere = _allenatori_da_json(dati["allenatori"], giocatori)
        prossimo_allenatore = da_json(dati["prossimo_allenatore"], int, "Mondo", "prossimo_allenatore")
        controlla_staff(polisportive, allenatori)
        for g in giocatori.values():
            if g.classe_migliore == CLASSE_MIGLIORE_DA_CALCOLARE:
                g.classe_migliore = modulo_classe.punteggio(g)
        # Dalla issue 8, formato 10: i preset e le porte della finestra Mercato e ricerca. È la sola lettura indulgente,
        # scelta di Gabriele del 24 ottobre 2026: quello che non si legge torna ai filtri di serie, con un avviso.
        filtri_di_ricerca, avvisi_dei_filtri = mercato.filtri_di_ricerca_da_dizionario(dati.get("filtri_di_ricerca"))
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
    mondo.calendario = calendario_del_mondo
    mondo.sfide = sfide_del_mondo
    mondo.allenatori = allenatori
    mondo.prossimo_allenatore = max(prossimo_allenatore, max(allenatori, default=0) + 1)
    mondo.filtri_di_ricerca = filtri_di_ricerca
    if da_far_nascere:
        mondo.fai_nascere_lo_staff()
    mondo.aggiorna_fattori_staff()
    # A mondo pronto, e soltanto per il salvataggio che si usa davvero, ogni riparazione dei filtri va nel registro.
    for avviso in avvisi_dei_filtri:
        registro.scrivi(mercato.testo_per_il_registro(avviso))


def _allenatori_da_json(valore, giocatori):
    """
    Gli allenatori del salvataggio, per numero, e vero se sono da far nascere, cioè se il salvataggio
    viene dal formato 7. Un ex giocatore deve avere il suo giocatore, vivo e ritirato.
    """
    if valore is None:
        return {}, True
    if not isinstance(valore, list):
        raise ValueError("Mondo: il campo allenatori non è valido")
    allenatori = {}
    for voce in valore:
        a = staff.Allenatore.da_dizionario(voce)
        if a.numero in allenatori:
            raise ValueError(f"Allenatore {a.numero}: numero ripetuto")
        if a.tipo == staff.EX and (a.giocatore_id not in giocatori or not giocatori[a.giocatore_id].ritirato):
            raise ValueError(f"Allenatore {a.numero}: il suo giocatore {a.giocatore_id} non è un ritirato del mondo")
        allenatori[a.numero] = a
    return allenatori, False


def controlla_staff(polisportive, allenatori):
    """
    La coerenza fra lo staff delle polisportive e l'impiego degli allenatori, ValueError se non va: ogni
    posto occupato ha un allenatore che dice quella polisportiva e il ruolo del posto, il capo nel primo e
    gli assistenti negli altri due, e ogni allenatore impiegato sta nello staff della sua polisportiva.
    """
    impiegati = set()
    for p in polisportive.values():
        for posto, numero in enumerate(p.staff):
            if not numero:
                continue
            a = allenatori.get(numero)
            ruolo = staff.CAPO if posto == 0 else staff.ASSISTENTE
            if a is None or a.polisportiva != p.nome or a.ruolo != ruolo:
                raise ValueError(f"Polisportiva {p.nome}: il posto {posto + 1} dello staff non corrisponde all'allenatore {numero}")
            impiegati.add(numero)
    for a in allenatori.values():
        if a.polisportiva is not None and a.numero not in impiegati:
            raise ValueError(f"Allenatore {a.numero}: dice di allenare {a.polisportiva}, che non lo ha nello staff")


def controlla_contratto(g, polisportive):
    """
    La coerenza fra contratto e appartenenza di un giocatore letto dal salvataggio, ValueError se non
    va: un tesserato ha uno stipendio e una scadenza al primo del mese; un libero non ha né contratto
    né rinnovo; un rinnovo ha stipendio e scadenza insieme; un'intensità diversa da normale l'ha
    soltanto un tesserato dell'utente.
    """
    chi = f"Giocatore {g.id}"
    if g.appartenenza != "*":
        if g.contratto_stipendio <= 0 or g.contratto_scadenza is None or g.contratto_scadenza.day != 1:
            raise ValueError(f"{chi}: è tesserato con {g.appartenenza} senza un contratto valido")
    elif g.contratto_stipendio or g.contratto_scadenza is not None or g.rinnovo_stipendio or g.rinnovo_scadenza is not None:
        raise ValueError(f"{chi}: è libero ma ha un contratto o un rinnovo")
    if (g.rinnovo_stipendio > 0) != (g.rinnovo_scadenza is not None) or (g.rinnovo_scadenza is not None and g.rinnovo_scadenza.day != 1):
        raise ValueError(f"{chi}: il rinnovo concordato non è valido")
    if g.intensita != INTENSITA_PREDEFINITA:
        club = polisportive.get(g.appartenenza)
        if club is None or club.is_cpu_controlled:
            raise ValueError(f"{chi}: soltanto un tesserato dell'utente si allena a intensità {g.intensita}")


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


def carica(mondo, metti_da_parte=True):
    """
    Carica il mondo dal salvataggio, oppure dalla copia di sicurezza se il salvataggio non si
    può usare; se non c'è nessuno dei due, fa nascere un mondo nuovo. Restituisce da dove viene il
    mondo: NATO, CARICATO o DALLA_COPIA. Se i file ci sono ma nessuno dei due si legge, blocca i
    salvataggi del mondo e solleva SalvataggioIllegibile, dopo averne messo le copie in una cartella
    datata di salvataggi_illeggibili. Dalla verifica finale della cartella del mondo, 23 ottobre 2026,
    con metti_da_parte falso quelle copie non si fanno, e l'errore ha la cartella None: l'avvio lo
    chiede a ogni Riprova dopo la prima, che le copie le ha già fatte. Il salvataggio scartato quando il
    mondo viene dalla copia si mette da parte sempre, perché la copia sta per prendere il suo posto.
    Dalla verifica del 15 ottobre 2026, a mondo pronto la memoria si congela, congela_la_memoria.
    Dal 16 ottobre 2026, decisione 4 di Gabriele, mentre si legge e si costruisce il mondo la raccolta dei
    cicli resta spenta, senza_raccolta: il mondo sono milioni di oggetti che nascono tutti insieme e
    vivono a lungo, e la raccolta li ripassava più volte, anche per intero, mentre crescevano. Alla fine
    congela_la_memoria fa una raccolta sola, come prima, e mette da parte il mondo, ancora con la raccolta
    spenta: riaccesa prima, ripasserebbe tutto il mondo appena caricato come oggetti giovani, un terzo di
    secondo nel mondo di sessant'anni, subito prima della raccolta completa. Se il caricamento non
    riesce, la raccolta si riaccende lo stesso. Il mondo caricato non cambia.
    """
    with senza_raccolta():
        origine = _carica(mondo, metti_da_parte)
        congela_la_memoria()
    return origine


def _carica(mondo, metti_da_parte=True):
    """Il caricamento di carica, senza la memoria congelata."""
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
    raise SalvataggioIllegibile(motivo, _metti_da_parte(principale, copia) if metti_da_parte else None)


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
    return salva_con_avvisi(mondo)[0]


def salva_con_avvisi(mondo):
    """
    Salva il mondo come salva, e restituisce l'esito insieme agli avvisi, cioè le cose andate
    storte senza danno: la copia di sicurezza non aggiornata, o il vecchio file non compresso che
    non si è potuto togliere. Gli avvisi arrivano anche per notifica, come gli altri messaggi.
    """
    if mondo.salvataggio_bloccato:
        mondo.notifica("Salvataggio rifiutato: il salvataggio esistente non si è potuto leggere, e il gioco non lo copre.")
        return False, []
    mondo.sfoltisci_diari()
    try:
        contenuto, avvisi = scrivi(mondo, percorsi.percorso(FILE_MONDO), percorsi.percorso(FILE_MONDO_COPIA))
    except (OSError, TypeError, ValueError) as e:
        mondo.notifica(f"Salvataggio non riuscito: {e}. Il salvataggio precedente è rimasto com'era.")
        return False, []
    # Dalla verifica del 15 ottobre 2026 la memoria si congela dopo ogni salvataggio riuscito.
    congela_la_memoria()
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
    return True, avvisi + _togli_il_vecchio(mondo)


def _togli_il_vecchio(mondo):
    """
    Dopo un salvataggio compresso riuscito, il salvataggio non compresso della tappa 6 e la sua copia
    non servono più. Restituisce gli avvisi dei file che non si sono potuti togliere.
    """
    tolti = []
    avvisi = []
    for nome in (FILE_MONDO_VECCHIO, FILE_MONDO_COPIA_VECCHIO):
        vecchio = percorsi.percorso(nome)
        if os.path.exists(vecchio):
            try:
                os.remove(vecchio)
            except OSError as e:
                avvisi.append(f"Il vecchio file {nome} non si è potuto togliere: {e}.")
                mondo.notifica(avvisi[-1])
            else:
                tolti.append(nome)
    if tolti:
        mondo.notifica(f"Il mondo ora si salva compresso, in {FILE_MONDO}: {' e '.join(tolti)}, del formato di prima, non servono più e sono stati tolti.")
    return avvisi
