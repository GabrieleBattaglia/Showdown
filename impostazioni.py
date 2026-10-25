"""
Le impostazioni di MESS: dimensione dei caratteri, colori del testo e dello sfondo, volume degli effetti e della partita, velocità di gioco.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 5 del piano, secondo la decisione D12, sul modello di Terminal
Beast e di Tornello: i colori sono percentuali di rosso, verde e blu, da 0 a 100, e il valore
predefinito è il verde su nero a 12 punti degli altri due programmi. Si salvano nel file
mess_impostazioni.json, fuori da git come in Tornello. Dal 2026-10-23, per scelta di Gabriele, il file
sta nella cartella del mondo, percorsi.py, e viaggia col mondo fra le macchine. Un file mancante o rovinato non ferma niente: valgono i predefiniti.
Dal 2026-10-07, con la decisione D24, c'è anche il volume degli effetti sonori, da 0 a 100: a 50,
il predefinito, i suoni sono come li ha pensati chi li ha fatti, e a zero tacciono.
Dal 2026-10-08, con la decisione D29, c'è la velocità di gioco della partita dal vivo, da 1 a 8, e i
modi di seguire l'amichevole diventano Assisti e Vai alla fine, con i valori di prima migrati.
Con la decisione D30, lo stesso giorno, la velocità di gioco parte da 4, e chi l'ha già salvata la
ritrova com'era; e la partita ha un volume suo, da 0 a 100, accanto a quello degli effetti.
Dal 2026-10-21, con la 1.79.0, gli annunci della cronaca, chiesti da Gabriele prima del collaudo della
1.78.13: la cronaca della partita dal vivo e della differita si legge in automatico, alla sintesi, al
braille o a tutti e due, con la sintesi scelta fra l'automatica, NVDA, JAWS e la voce di Windows, le
celle del display braille e il tempo minimo di lettura di ogni blocco. Le chiavi delle uscite e delle
destinazioni sono quelle di GBsintesi, di GBUtils.
Dal 2026-10-25, con la decisione D38, la barra di stato su misura: le righe scelte e i loro dati, da una a sedici righe,
ciascuna una lista di chiavi del catalogo di barra.py, con la barra di serie di dieci righe come partenza. Le chiavi che
questo MESS non conosce restano nel file, perché il file viaggia col mondo fra le macchine e un MESS rimasto indietro non
deve perdere i dati di uno più nuovo: le ignora soltanto a schermo. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude
Opus 5.5, UltraCode).
"""

import contextlib
import json
import os

from GBsintesi import AUTOMATICA, DESTINAZIONI, USCITE

import percorsi

FILE_IMPOSTAZIONI = "mess_impostazioni.json"
DIMENSIONE_MINIMA = 8
DIMENSIONE_MASSIMA = 72
VOLUME_MINIMO = 0
VOLUME_MASSIMO = 100
# Le opzioni dell'amichevole si ricordano, scelta di Gabriele dell'8 ottobre 2026: i valori sono
# quelli del dialogo OpzioniAmichevole e del livello della cronaca del motore, scritti qui per non far
# dipendere le impostazioni dalla finestra.
SET_DELL_AMICHEVOLE = (3, 5)
# Con la decisione D29 i modi di seguire l'amichevole sono due, Assisti e Vai alla fine. I valori
# ricordati dalla tappa 9 si migrano: il punto alla volta diventa Assisti, che è la partita dal vivo,
# tutta subito e solo il risultato diventano Vai alla fine, che mostra il risultato e la cronaca.
MODI_DELL_AMICHEVOLE = ("assisti", "fine")
MODI_DI_PRIMA = {"punto": "assisti", "tutta": "fine", "risultato": "fine"}
LIVELLI_DELL_AMICHEVOLE = ("sintetica", "normale", "tecnica")
# La velocità di gioco della decisione D12, nella forma di D29: divide le pause e la procedura
# dell'arbitro della partita dal vivo, da 1, il tempo reale, a 8. Con D30 parte da 4: pause e
# procedura a un quarto del tempo reale. Vale solo per chi non l'ha mai salvata.
VELOCITA_MINIMA = 1
VELOCITA_MASSIMA = 8
VELOCITA_PREDEFINITA = 4
# Il volume della partita dal vivo, decisione D30, da 0 a 100 come quello degli effetti ma a parte:
# a 100, il volume di progetto di partita_sonora, la partita suona come nell'ascolto libero che
# Gabriele ha approvato; si parte da 50, la metà, scelta di Gabriele dell'8 ottobre 2026, così il
# cursore ha strada nei due sensi.
VOLUME_PARTITA_PREDEFINITO = 50
# Gli annunci della cronaca, 1.79.0, coi predefiniti di Gabriele: lettura automatica accesa, alla sintesi
# automatica e al braille, display di 40 celle. Le celle vanno da 0, che vuol dire non importa e manda
# ogni riga intera, a 160; il tempo minimo di lettura di ogni blocco del display, in millesimi, da 100 a
# 60.000 e 2.000 di partenza, come in MeTeOra, da cui viene la barra a blocchi.
CELLE_MASSIME = 160
LETTURA_MINIMA, LETTURA_MASSIMA = 100, 60_000
# La barra di stato su misura, D38: da una a sedici righe, scelta di Gabriele del 24 ottobre 2026, perché la vista scorre
# e la barra può prendere metà della finestra. La barra di serie ne ha dieci: le otto del catalogo del 24 ottobre, dalla
# più utile alla meno utile e con le cose da fare oggi nella seconda, più due composte coi venti dati rimasti, e in fondo
# le notizie con l'ultimo evento, perché Ctrl+Fine ci porta subito.
RIGHE_MASSIME = 16
BARRA_DI_SERIE = (
    ("stato_salvataggio", "data_simulata", "giorno_della_settimana", "ora_simulata", "prossimo_avanzamento_fra", "prossimo_avanzamento_alle",
     "ultimo_avanzamento_alle", "giorni_al_primo_del_mese"),
    ("amichevoli_di_tutte", "punti_di_tutte", "sfide_ricevute", "sfide_da_lanciare", "mosse_rimaste", "rinnovi_da_proporre", "contratti_in_uscita",
     "riservati_a_te", "differite_da_ascoltare"),
    ("nome_polisportiva", "gloria", "posto_per_gloria", "tesserati", "disponibili", "amichevoli_giocabili", "impegnati_oggi", "punti_allenamento",
     "infortunati", "acciaccati", "tuoi_in_vendita", "contratti_in_scadenza", "migliore", "capo_allenatore", "posti_staff", "rinnovi_staff", "prelazioni"),
    ("cassa", "margine_al_primo", "saldo_mensile", "autonomia", "arretrati", "pazienza_minima", "sponsor", "stipendi_tesserati", "stipendi_staff",
     "bilancio_ultimo_mese"),
    ("tornei_in_corso", "tuoi_in_gara", "iscrizioni_dei_tuoi", "prossimo_torneo_dei_tuoi", "sfide_di_domani", "convocati_campionato",
     "classifica_anno_uomini", "classifica_anno_donne", "classifica_uomini", "classifica_donne", "coppa_delle_polisportive"),
    ("polisportive_tue", "capitale", "atleti_in_tutto", "gloria_piu_alta", "medaglie_di_tutte", "coppe_di_tutte"),
    ("liberi_nel_mondo", "sotto_contratto_nel_mondo", "fermi_nel_mondo", "popolazione", "polisportive_nel_mondo", "vecchie_glorie", "nuovi_della_sessione",
     "ritirati_della_sessione", "durata_sessione", "comandi_della_sessione"),
    ("medaglie", "coppe", "palmares_cinque_anni", "sfide_vinte_perse", "valore_collettivo", "valore_di_mercato", "eta_media", "uomini_donne",
     "prossima_guarigione", "intensita_intensa", "iscrizione_manuale", "qualita_staff"),
    ("quote_del_mese", "premi_del_mese", "movimenti_del_mese", "in_vendita_nel_mondo", "allenatori_liberi", "edizioni_aperte",
     "prossimo_torneo_del_calendario", "prossima_apertura"),
    ("notizie_ultimo_avanzamento", "ultimo_evento"),
)
PREDEFINITE = {"dimensione": 12, "colore_testo": [0, 100, 0], "colore_sfondo": [0, 0, 0], "volume_effetti": 50,
               "amichevole_set": 3, "amichevole_modo": "assisti", "amichevole_livello": "normale", "velocita_gioco": VELOCITA_PREDEFINITA,
               "volume_partita": VOLUME_PARTITA_PREDEFINITO,
               "annunci_cronaca": True, "annunci_dove": "entrambi", "annunci_sintesi": AUTOMATICA, "annunci_celle": 40,
               "annunci_lettura_minima": 2000, "barra_di_stato": [list(riga) for riga in BARRA_DI_SERIE]}


def _colore_valido(valore):
    return isinstance(valore, list) and len(valore) == 3 and all(isinstance(c, int) and not isinstance(c, bool) and 0 <= c <= 100 for c in valore)


def barra_valida(valore):
    """
    La barra di stato ricevuta, pulita: una lista di righe, ogni riga una lista di chiavi. Si tengono soltanto le chiavi
    scritte come testo, una volta sola, dove compaiono la prima volta, anche quelle che questo MESS non conosce; le righe
    vuote se ne vanno, e oltre la sedicesima non si va. Se non resta niente, la barra di serie.
    """
    viste = set()
    righe = []
    for riga in valore if isinstance(valore, list) else ():
        if not isinstance(riga, list):
            continue
        tenute = []
        for chiave in riga:
            if isinstance(chiave, str) and chiave and chiave not in viste:
                viste.add(chiave)
                tenute.append(chiave)
        if tenute:
            righe.append(tenute)
    return righe[:RIGHE_MASSIME] or [list(riga) for riga in BARRA_DI_SERIE]


def valide(dati):
    """Le impostazioni ricevute, con i predefiniti al posto dei valori che mancano o non vanno."""
    risultato = {chiave: list(v) if isinstance(v, list) else v for chiave, v in PREDEFINITE.items()}
    risultato["barra_di_stato"] = barra_valida(None)
    if not isinstance(dati, dict):
        return risultato
    risultato["barra_di_stato"] = barra_valida(dati.get("barra_di_stato"))
    dimensione = dati.get("dimensione")
    if isinstance(dimensione, int) and not isinstance(dimensione, bool) and DIMENSIONE_MINIMA <= dimensione <= DIMENSIONE_MASSIMA:
        risultato["dimensione"] = dimensione
    for chiave in ("colore_testo", "colore_sfondo"):
        if _colore_valido(dati.get(chiave)):
            risultato[chiave] = list(dati[chiave])
    for chiave, minimo, massimo in (("volume_effetti", VOLUME_MINIMO, VOLUME_MASSIMO), ("volume_partita", VOLUME_MINIMO, VOLUME_MASSIMO),
                                    ("velocita_gioco", VELOCITA_MINIMA, VELOCITA_MASSIMA), ("annunci_celle", 0, CELLE_MASSIME),
                                    ("annunci_lettura_minima", LETTURA_MINIMA, LETTURA_MASSIMA)):
        valore = dati.get(chiave)
        if isinstance(valore, int) and not isinstance(valore, bool) and minimo <= valore <= massimo:
            risultato[chiave] = valore
    modo = dati.get("amichevole_modo")
    if isinstance(modo, str):
        dati = {**dati, "amichevole_modo": MODI_DI_PRIMA.get(modo, modo)}
    for chiave, ammessi in (("amichevole_set", SET_DELL_AMICHEVOLE), ("amichevole_modo", MODI_DELL_AMICHEVOLE), ("amichevole_livello", LIVELLI_DELL_AMICHEVOLE),
                            ("annunci_dove", DESTINAZIONI), ("annunci_sintesi", (AUTOMATICA, *USCITE))):
        valore = dati.get(chiave)
        if not isinstance(valore, bool) and valore in ammessi:
            risultato[chiave] = valore
    if isinstance(dati.get("annunci_cronaca"), bool):
        risultato["annunci_cronaca"] = dati["annunci_cronaca"]
    return risultato


def carica():
    """Le impostazioni salvate, o i predefiniti se il file manca o non si legge."""
    try:
        with open(percorsi.percorso(FILE_IMPOSTAZIONI), encoding="utf-8") as f:
            return valide(json.load(f))
    except (OSError, ValueError):
        return valide(None)


def salva(impostazioni):
    """
    Salva le impostazioni; restituisce vero se è riuscito. Scrive prima un file temporaneo, come il mondo.
    Dal 23 ottobre 2026 anche la cartella del mondo che non si sa dove sia, percorsi.CartellaIllegibile, è
    un salvataggio non riuscito, e non un errore imprevisto.
    """
    try:
        percorso = percorsi.percorso(FILE_IMPOSTAZIONI)
    except OSError:
        return False
    temporaneo = percorso + ".tmp"
    try:
        with open(temporaneo, "w", encoding="utf-8", newline="\n") as f:
            json.dump(valide(impostazioni), f, ensure_ascii=False, indent=1)
        os.replace(temporaneo, percorso)
    except OSError:
        with contextlib.suppress(OSError):
            os.remove(temporaneo)
        return False
    return True


def da_percentuale(percentuale):
    """Una componente di colore da percentuale, da 0 a 100, a byte, da 0 a 255, con lo stesso conto di Tornello."""
    return max(0, min(255, int(percentuale / 100 * 255)))
