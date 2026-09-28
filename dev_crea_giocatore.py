import pickle
import datetime # Import necessario
import os
import sys
import traceback # Per debug errori imprevisti

# --- Import necessari da sd.py ---
# Assicurati che sd.py sia nella stessa cartella o nel PYTHONPATH
try:
    # Importa la classe Giocatore e le costanti DB
    from sd import Giocatore, DB_GIOCATORI, DB_STATO_GIOCO

    # Importa le costanti necessarie per la creazione e validazione
    from sd import (
        ANNO_SIMULAZIONE_GIORNI, ETA_MIN_CREAZIONE_ANNI, ETA_MAX_MORTE_ANNI,
        MAX_PRECISIONE_RESISTENZA, MAX_SKILL_VALUE, MAX_TOTALE_PRECISIONE_RESISTENZA,
        MAX_TOTALE_SKILL_GIOCO, ATTRIBUTI_BASE_CON_ALLENABILI,
        NOME_ATTR_TO_DISPLAY_MAP
    )

    # Importa la funzione di input GBUtils (se usata)
    try:
        from GBUtils import dgt
    except ImportError:
        print("ATTENZIONE: GBUtils non trovato, uso input() base.")
        def dgt(prompt, *args, **kwargs): # Fallback semplice
            return input(prompt)

except ImportError as e:
    print("ERRORE: Impossibile importare componenti necessari da 'sd.py'.")
    print("Verifica che 'sd.py' sia presente nella stessa cartella e non contenga errori.")
    print(f"Dettaglio errore: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERRORE inaspettato durante l'import da sd.py: {e}")
    sys.exit(1)

# --- Funzioni Helper ---

def carica_file_pickle(filename, default_value):
    """Carica dati da un file pickle, gestendo FileNotFoundError."""
    if os.path.exists(filename):
        try:
            with open(filename, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"ATTENZIONE: Errore durante il caricamento di '{filename}': {e}")
            print(f"Verrà utilizzato il valore di default: {default_value}")
            return default_value
    else:
        # print(f"ATTENZIONE: File '{filename}' non trovato.") # Meno verboso
        return default_value

def salva_file_pickle(filename, data):
    """Salva dati su un file pickle."""
    try:
        # Usa file temporaneo per maggiore sicurezza
        temp_filename = filename + ".tmp"
        with open(temp_filename, "wb") as f:
            pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
        os.replace(temp_filename, filename) # Rinomina atomico
        print(f" -> Dati salvati correttamente in '{filename}'.")
        return True
    except Exception as e:
        print(f"\nERRORE FATALE durante il salvataggio di '{filename}': {e}")
        # Pulisci file temp se esiste
        if os.path.exists(temp_filename):
            try: os.remove(temp_filename)
            except: pass
        return False

def trova_prossimo_id_libero(ultimo_id: int, giocatori_dict: dict) -> tuple[int, int]:
    """Trova il prossimo ID intero non utilizzato."""
    next_id = ultimo_id + 1
    while next_id in giocatori_dict:
        next_id += 1
    # Restituisce l'ID suggerito e l'ultimo ID che verrebbe usato se si scegliesse questo
    return next_id, next_id

# --- Logica Principale Script ---

# All'interno della funzione main() di crea_giocatore.py

def main():
    print("--- Creazione Manuale Giocatore (Script Esterno v4 - ID Sequenziale) ---")

    # 1. Carica Dati Esistenti
    print(f"\nCaricamento dati da '{DB_GIOCATORI}' e '{DB_STATO_GIOCO}'...")
    giocatori = carica_file_pickle(DB_GIOCATORI, {})
    stato_gioco_originale = carica_file_pickle(DB_STATO_GIOCO, {}) # Carica stato per date

    # --- RIMOSSO: Caricamento/Validazione ultimo_id_usato ---

    # Leggi e valida date/ore dallo stato caricato (come prima)
    now_dt = datetime.datetime.now()
    dt_sim_caricata = stato_gioco_originale.get('datetime_corrente_simulazione')
    dt_run_caricato = stato_gioco_originale.get('datetime_ultimo_run_reale') # Leggi ma non modificare

    if isinstance(dt_sim_caricata, datetime.date) and not isinstance(dt_sim_caricata, datetime.datetime):
        dt_sim_caricata = datetime.datetime.combine(dt_sim_caricata, datetime.time.min)
    elif not isinstance(dt_sim_caricata, datetime.datetime):
        dt_sim_caricata = now_dt

    if isinstance(dt_run_caricato, datetime.date) and not isinstance(dt_run_caricato, datetime.datetime):
        dt_run_caricato = datetime.datetime.combine(dt_run_caricato, datetime.time.min)
    elif not isinstance(dt_run_caricato, datetime.datetime):
        dt_run_caricato = dt_sim_caricata - datetime.timedelta(hours=8)

    dt_sim_per_creazione = dt_sim_caricata

    print(f"Data simulazione riferimento creazione: {dt_sim_per_creazione:%Y-%m-%d %H:%M}")
    # Non mostriamo più ultimo_id_usato qui

    # 2. Raccogli Dati Nuovo Giocatore
    try:
        # --- CORREZIONE: Trova ID sequenziale libero ---
        final_id = 1
        while final_id in giocatori:
            final_id += 1
        print(f"ID suggerito (primo libero): {final_id}")
        override_id = dgt(f"Confermi ID {final_id} o inserisci un ID diverso (0=accetta)? ", "i", imin=0)
        if override_id > 0:
            final_id = override_id # Permetti override manuale
        # --- FINE CORREZIONE ---

        # --- RIMOSSO: Calcolo ultimo_id_aggiornato ---

        if final_id in giocatori:
            print(f"ATTENZIONE: ID {final_id} già occupato:")
            try: print(giocatori[final_id].sommario())
            except: print(f"(Info giocatore ID {final_id} non disponibili)")
            if dgt("Sovrascrivere? (s/N) ", smax=1).lower() != 's': print("Annullato."); sys.exit(0)

        print(f"\nCreazione giocatore ID: {final_id}")
        dati_giocatore = {}

        # ... (Input dati giocatore come prima: nome, cognome, sesso, eta, fisico, skill, altri) ...
        dati_giocatore['nome'] = dgt("Nome? ", smin=1, smax=24).title()
        dati_giocatore['cognome'] = dgt("Cognome? ", smin=1, smax=24).title()
        dati_giocatore['sesso'] = dgt("Sesso (m/f)? ", smax=1, default='m').lower()
        eta_anni = dgt(f"Età (anni sim, {ETA_MIN_CREAZIONE_ANNI:.1f}-{ETA_MAX_MORTE_ANNI:.1f})? ", "f", fmin=ETA_MIN_CREAZIONE_ANNI, fmax=ETA_MAX_MORTE_ANNI)
        if ANNO_SIMULAZIONE_GIORNI <= 0: dati_giocatore['eta'] = int(eta_anni*365)
        else: dati_giocatore['eta'] = int(eta_anni * ANNO_SIMULAZIONE_GIORNI)
        dati_giocatore['altezza'] = dgt("Altezza (cm, 140-210)? ", "i", imin=140, imax=210)
        dati_giocatore['peso'] = dgt("Peso (kg, 35-150)? ", "i", imin=35, imax=150)
        print("\nCaratteristiche:")
        skill_ordinate = sorted(list(ATTRIBUTI_BASE_CON_ALLENABILI), key=lambda x: NOME_ATTR_TO_DISPLAY_MAP.get(x, x))
        for nome_base in skill_ordinate:
            nome_allenato = nome_base.replace('_base', '_allenata')
            nome_display = NOME_ATTR_TO_DISPLAY_MAP.get(nome_base, nome_base.replace('_base','').title())
            is_fisica = 'forza' in nome_base or 'resistenza' in nome_base
            max_val_base = MAX_PRECISIONE_RESISTENZA if is_fisica else MAX_SKILL_VALUE
            max_totale_skill = MAX_TOTALE_PRECISIONE_RESISTENZA if is_fisica else MAX_TOTALE_SKILL_GIOCO
            max_val_allenato_input = max_totale_skill
            val_base = dgt(f"  {nome_display} - Base (0.0-{max_val_base:.1f})? ", "f", fmin=0.0, fmax=max_val_base)
            val_allenato = dgt(f"    -> Allenata (0.0-{max_val_allenato_input:.1f})? ", "f", fmin=0.0, fmax=max_val_allenato_input)
            if val_base + val_allenato > max_totale_skill:
                 val_allenato = max(0.0, max_totale_skill - val_base)
                 print(f"    -> Allenato limitato a: {val_allenato:.1f}")
            dati_giocatore[nome_base] = val_base
            dati_giocatore[nome_allenato] = val_allenato
        print("\nAltri attributi:")
        dati_giocatore['puntiesperienza'] = dgt("Punti Esperienza? ", "i", imin=0)
        dati_giocatore['mancino'] = dgt("Mancino (s/N)? ", smax=1).lower() == 's'
        dati_giocatore['ambidestro'] = False
        if not dati_giocatore['mancino']: dati_giocatore['ambidestro'] = dgt("Ambidestro (s/N)? ", smax=1).lower() == 's'
        dati_giocatore['infortunato'] = dgt("Infortunato (s/N)? ", smax=1).lower() == 's'
        dati_giocatore['ipovedente'] = dgt("Ipovedente (s/N)? ", smax=1).lower() == 's'
        dati_giocatore['ritirato'] = dgt("Già Ritirato (s/N)? ", smax=1).lower() == 's'
        dati_giocatore['giocorapido'] = dgt("Gioco Rapido (s/N)? ", smax=1).lower() == 's'
        dati_giocatore['cambiovelocita'] = dgt("Cambio Velocità (s/N)? ", smax=1).lower() == 's'


        # 3. Crea Istanza Giocatore
        nuovo_giocatore = Giocatore(
            id_giocatore=final_id,
            datetime_creazione_sim=dt_sim_per_creazione,
            **dati_giocatore
        )

        # 4. Aggiorna Dati e Salva
        giocatori[final_id] = nuovo_giocatore
        print("\nGiocatore creato/aggiornato:")
        try: print(nuovo_giocatore.sommario())
        except Exception as e: print(f"(Errore sommario: {e})")

        # Prepara stato gioco aggiornato
        # --- CORREZIONE: NON salvare ultimo_id_usato, NON modificare dt_run ---
        stato_gioco_aggiornato = {
            # Rimuovi 'ultimo_id_usato'
            'datetime_corrente_simulazione': dt_sim_per_creazione,
            'datetime_ultimo_run_reale': dt_run_caricato # Mantieni quello letto
        }
        # Aggiungi ultimo_id_usato solo se era presente nello stato originale
        if 'ultimo_id_usato' in stato_gioco_originale:
             stato_gioco_aggiornato['ultimo_id_usato'] = stato_gioco_originale['ultimo_id_usato']
             # Potremmo anche aggiornarlo se l'ID scelto manualmente è maggiore
             # stato_gioco_aggiornato['ultimo_id_usato'] = max(stato_gioco_originale['ultimo_id_usato'], final_id)
             # Ma è più sicuro lasciarlo invariato per non interferire col simulatore principale

        print(f"INFO: Salvataggio stato con dt_sim={stato_gioco_aggiornato['datetime_corrente_simulazione']:%Y-%m-%d %H:%M} e dt_run={stato_gioco_aggiornato['datetime_ultimo_run_reale']:%Y-%m-%d %H:%M}")
        # --- FINE CORREZIONE ---

        print("\nSalvataggio dati aggiornati...")
        if salva_file_pickle(DB_GIOCATORI, giocatori):
            salva_file_pickle(DB_STATO_GIOCO, stato_gioco_aggiornato)

        print("\nOperazione completata.")

    # ... (gestione eccezioni come prima) ...
    except (ValueError, EOFError) as e: print(f"\nInput non valido o interrotto: {e}\nNessuna modifica salvata."); sys.exit(1)
    except Exception as e: print(f"\nERRORE IMPREVISTO: {e}"); traceback.print_exc(); print("Nessuna modifica salvata."); sys.exit(1)

if __name__ == "__main__":
    main()