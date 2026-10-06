"""
L'archivio di MESS: caricamento e salvataggio del mondo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 2 del piano, dallo smontaggio di sd.py. Il formato è ancora
quello dei tre file pickle del vecchio programma, fino alla tappa 3, che lo sostituirà con file
JSON firmati, secondo la decisione D4. Intanto due cose cambiano. I file si cercano nella
cartella del programma e non in quella corrente, problema P10. E il lettore accetta soltanto le
classi del gioco e i pochi tipi che i salvataggi contengono: riporta a modelli.py le classi che
il vecchio sd.py registrava come appartenenti a __main__, problema P2, e rifiuta tutto il resto,
così un file costruito apposta non può eseguire nulla.
"""

import datetime
import pickle
import time

import percorsi
from costanti import DATA_NESSUN_MOVIMENTO, DB_GIOCATORI, DB_POLISPORTIVE, DB_STATO_GIOCO, NUM_GIOCATORI_INIZIALI
from modelli import Giocatore, Polisportiva
from utilita import adesso

CLASSI_DEL_GIOCO = {"Giocatore": Giocatore, "Polisportiva": Polisportiva}
MODULI_DEL_GIOCO = ("__main__", "sd", "modelli")
TIPI_AMMESSI = {
    ("datetime", "datetime"),
    ("datetime", "date"),
    ("datetime", "timedelta"),
    ("builtins", "set"),
    ("builtins", "frozenset"),
}
ERRORI_DI_LETTURA = (OSError, pickle.UnpicklingError, AttributeError, ValueError, TypeError, KeyError, IndexError)


class LettoreSalvataggi(pickle.Unpickler):
    """Ricostruisce soltanto le classi del gioco e i tipi elencati in TIPI_AMMESSI."""

    def find_class(self, module, name):
        if module in MODULI_DEL_GIOCO and name in CLASSI_DEL_GIOCO:
            return CLASSI_DEL_GIOCO[name]
        if (module, name) in TIPI_AMMESSI:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"Classe non ammessa nel salvataggio: {module}.{name}")


def _come_datetime(valore):
    """Le date dei salvataggi più vecchi diventano date con l'ora, a mezzanotte."""
    if isinstance(valore, datetime.date) and not isinstance(valore, datetime.datetime):
        return datetime.datetime.combine(valore, datetime.time.min)
    return valore


def _carica_stato(mondo):
    """La data simulata e quella dell'ultimo avanzamento; restituisce la data da usare per le nascite."""
    notifica = mondo.notifica
    dt_sim_per_creazione = adesso()
    stato_ok = False
    try:
        with open(percorsi.percorso(DB_STATO_GIOCO), "rb") as f:
            stato = LettoreSalvataggi(f).load()
        dt_sim = _come_datetime(stato.get('datetime_corrente_simulazione'))
        dt_run = _come_datetime(stato.get('datetime_ultimo_run_reale'))
        if isinstance(dt_sim, datetime.datetime) and isinstance(dt_run, datetime.datetime):
            if dt_sim < dt_run:
                notifica("*" * 75 + "\nATTENZIONE: INCOERENZA TEMPORALE CARICATA!\n" + f"  Data Sim ({dt_sim:%Y-%m-%d %H:%M}) < Ultimo Run ({dt_run:%Y-%m-%d %H:%M})\n" + "  Proseguo con date caricate.\n" + "*" * 75)
            mondo.datetime_corrente_simulazione, mondo.datetime_ultimo_run_reale = dt_sim, dt_run
            dt_sim_per_creazione = dt_sim
            stato_ok = True
            notifica(f"Stato caricato. Sim: {dt_sim:%Y-%m-%d %H:%M}, Ult Run: {dt_run:%Y-%m-%d %H:%M}.")
        else:
            notifica("WARN: Dati tempo stato non validi.")
    except FileNotFoundError:
        notifica(f"File stato '{DB_STATO_GIOCO}' non trovato.")
    except (*ERRORI_DI_LETTURA, EOFError) as e:
        notifica(f"ERR caricamento stato: {e}")
    if not stato_ok:
        mondo.datetime_corrente_simulazione = dt_sim_per_creazione
        mondo.datetime_ultimo_run_reale = dt_sim_per_creazione - datetime.timedelta(hours=8)
        notifica(f"Nuovo stato inizializzato. Data/Ora Sim: {mondo.datetime_corrente_simulazione:%Y-%m-%d %H:%M}")
    return dt_sim_per_creazione


def _mezzanotte(data):
    """La data dei campi più vecchi, giorno soltanto, portata a mezzanotte come faceva sd.py."""
    return datetime.datetime.combine(data, datetime.time.min)


def _ripara_giocatore(g, data_simulata):
    """Aggiunge ai giocatori dei salvataggi vecchi gli attributi nati dopo, e corregge i tipi delle date."""
    if hasattr(g, 'datacreazione') and isinstance(g.datacreazione, datetime.date):
        g.datetime_creazione_sim = _mezzanotte(g.datacreazione)
    if not isinstance(getattr(g, 'datetime_creazione_sim', None), datetime.datetime):
        g.datetime_creazione_sim = data_simulata
    if not isinstance(getattr(g, 'datacreazione_reale', None), datetime.datetime):
        g.datacreazione_reale = g.datetime_creazione_sim
    if hasattr(g, 'infortunio_fine_data') and isinstance(g.infortunio_fine_data, datetime.date):
        g.infortunio_fine_datetime = _mezzanotte(g.infortunio_fine_data)
    if hasattr(g, 'infortunio_fine_datetime') and not isinstance(g.infortunio_fine_datetime, datetime.datetime):
        g.infortunio_fine_datetime = None
    if not hasattr(g, 'archetipo_allenamento'):
        g.archetipo_allenamento = "Non Definito"
    if not hasattr(g, 'descrizione_fisica'):
        g.descrizione_fisica = ''
    if not hasattr(g, 'ori'):
        g.ori, g.argenti, g.bronzi, g.legni = 0, 0, 0, 0
    if not hasattr(g, 'forza_base'):
        g.forza_base = 0.0
    if not hasattr(g, 'forza_allenata'):
        g.forza_allenata = 0.0


def _carica_giocatori(mondo, dt_sim_per_creazione):
    notifica = mondo.notifica
    gioc_ok = False
    try:
        with open(percorsi.percorso(DB_GIOCATORI), "rb") as f:
            grezzi = LettoreSalvataggi(f).load()
        mondo.giocatori = {gid: g for gid, g in grezzi.items() if gid is not None and isinstance(gid, int)}
        num_filtrati = len(grezzi) - len(mondo.giocatori)
        if num_filtrati > 0:
            notifica(f"WARN: Filtrate {num_filtrati} voci ID non valido da '{DB_GIOCATORI}'.")
        notifica(f"Caricati {len(mondo.giocatori)} giocatori validi.")
        gioc_ok = True
        for g in mondo.giocatori.values():
            _ripara_giocatore(g, mondo.datetime_corrente_simulazione)
    except FileNotFoundError:
        notifica(f"File giocatori '{DB_GIOCATORI}' non trovato.")
    except (*ERRORI_DI_LETTURA, EOFError) as e:
        notifica(f"ERR caricamento giocatori: {e}")
    if not gioc_ok:
        notifica(f"\nPopolamento iniziale con {NUM_GIOCATORI_INIZIALI} giocatori...")
        mondo.nuovi_giocatori_sessione.clear()
        mondo.crea_giocatori_casuali(NUM_GIOCATORI_INIZIALI, dt_sim_per_creazione)
        notifica("Popolamento completato.")
        mondo.nuovi_giocatori_sessione.clear()


def _ripara_polisportiva(p, data_simulata, notifica):
    """Aggiunge alle polisportive dei salvataggi vecchi gli attributi nati dopo, e corregge i tipi delle date."""
    nome_p = getattr(p, 'nome', '?')
    if hasattr(p, 'datacreazione') and isinstance(p.datacreazione, datetime.date):
        p.datetime_creazione_sim = _mezzanotte(p.datacreazione)
    if not isinstance(getattr(p, 'datetime_creazione_sim', None), datetime.datetime):
        notifica(f"WARN: Fix dt_creaz_sim Poli '{nome_p}'.")
        p.datetime_creazione_sim = data_simulata
    if hasattr(p, 'data_ultimo_movimento') and isinstance(p.data_ultimo_movimento, datetime.date):
        p.datetime_ultimo_movimento = _mezzanotte(p.data_ultimo_movimento)
    if not isinstance(getattr(p, 'datetime_ultimo_movimento', None), datetime.datetime):
        p.datetime_ultimo_movimento = DATA_NESSUN_MOVIMENTO
    if not hasattr(p, 'movimenti_oggi'):
        p.movimenti_oggi = 0
    if not isinstance(getattr(p, 'datacreazione_reale', None), datetime.datetime):
        notifica(f"WARN: Fix dt_creaz_real Poli '{nome_p}'.")
        p.datacreazione_reale = p.datetime_creazione_sim
    if not isinstance(getattr(p, 'versione_creazione', None), str):
        notifica(f"WARN: Fix vers_creaz Poli '{nome_p}'.")
        p.versione_creazione = 'N/D'
    if not hasattr(p, 'ori'):
        p.ori, p.argenti, p.bronzi, p.legni = 0, 0, 0, 0
    if not hasattr(p, 'coppe_oro'):
        p.coppe_oro, p.coppe_argento, p.coppe_bronzo, p.coppe_legno = 0, 0, 0, 0


def _carica_polisportive(mondo):
    notifica = mondo.notifica
    try:
        with open(percorsi.percorso(DB_POLISPORTIVE), "rb") as f:
            lettore = LettoreSalvataggi(f)
            mondo.polisportive = lettore.load()
            nome_att = lettore.load()
        if not isinstance(mondo.polisportive, dict):
            raise ValueError("Formato file polisportive non valido")
        notifica(f"Caricate {len(mondo.polisportive)} polisportive.")
        for p in mondo.polisportive.values():
            _ripara_polisportiva(p, mondo.datetime_corrente_simulazione, notifica)
        if nome_att != "Nessuna" and nome_att in mondo.polisportive:
            mondo.miapolisportiva_attiva = mondo.polisportive[nome_att]
            notifica(f"Poli attiva: {nome_att}")
        else:
            mondo.miapolisportiva_attiva = None
            notifica("Nessuna poli attiva.")
    except FileNotFoundError:
        notifica(f"File polisportive '{DB_POLISPORTIVE}' non trovato.")
    except EOFError:
        notifica(f"File polisportive '{DB_POLISPORTIVE}' incompleto.")
    except ERRORI_DI_LETTURA as e:
        notifica(f"ERR caricamento polisportive: {e}")
        mondo.polisportive = {}


def carica(mondo):
    """Carica nel mondo lo stato, i giocatori e le polisportive; crea i giocatori iniziali se non ce ne sono."""
    mondo.notifica("\n--- Caricamento Dati ---")
    dt_sim_per_creazione = _carica_stato(mondo)
    _carica_giocatori(mondo, dt_sim_per_creazione)
    _carica_polisportive(mondo)
    mondo.notifica("--- Fine Caricamento ---")


def salva(mondo):
    """Salva giocatori, polisportive e stato del mondo. I morti della sessione non vengono salvati."""
    notifica = mondo.notifica
    notifica("\nSalvataggio databases...")
    inizio = time.time()
    successo = True
    try:
        giocatori_da_salvare = {gid: g for gid, g in mondo.giocatori.items() if gid not in mondo._ids_morti_processati_sessione}
        n_rimossi = len(mondo.giocatori) - len(giocatori_da_salvare)
        if n_rimossi:
            notifica(f"  (Rimuovendo {n_rimossi} giocatori morti/usciti)")
        with open(percorsi.percorso(DB_GIOCATORI), "wb") as f:
            pickle.dump(giocatori_da_salvare, f, pickle.HIGHEST_PROTOCOL)
        notifica(f" -> {len(giocatori_da_salvare)} giocatori salvati in '{DB_GIOCATORI}'.")
        with open(percorsi.percorso(DB_POLISPORTIVE), "wb") as f:
            pickle.dump(mondo.polisportive, f, pickle.HIGHEST_PROTOCOL)
            nome_attiva = mondo.miapolisportiva_attiva.nome if mondo.miapolisportiva_attiva else "Nessuna"
            pickle.dump(nome_attiva, f, pickle.HIGHEST_PROTOCOL)
        notifica(f" -> {len(mondo.polisportive)} polisportive salvate in '{DB_POLISPORTIVE}'.")
        stato = {'datetime_corrente_simulazione': mondo.datetime_corrente_simulazione, 'datetime_ultimo_run_reale': mondo.datetime_ultimo_run_reale}
        with open(percorsi.percorso(DB_STATO_GIOCO), "wb") as f:
            pickle.dump(stato, f, pickle.HIGHEST_PROTOCOL)
        notifica(f" -> Stato gioco salvato in '{DB_STATO_GIOCO}'.")
    except (OSError, pickle.PickleError) as e:
        notifica(f"\nERRORE FATALE salvataggio: {e}")
        successo = False
    tempo_impiegato = time.time() - inizio
    if successo:
        notifica(f"Salvataggio completato ({tempo_impiegato:.5f}s).")
    else:
        notifica(f"Salvataggio fallito ({tempo_impiegato:.5f}s).")
    return successo
