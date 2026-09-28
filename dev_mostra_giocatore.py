# mostra_dati_giocatore.py
import pickle
import os
import sys
import pprint # Per stampare dizionari in modo leggibile

# --- Import Costanti DB ---
# Assicurati che sd.py sia accessibile
try:
    from sd import DB_GIOCATORI
    # Importiamo Giocatore solo per fare un check sul tipo (opzionale)
    # e per potenziali metodi futuri, ma non è strettamente necessario
    # per leggere __dict__
    from sd import Giocatore
except ImportError as e:
    print("ERRORE: Impossibile importare DB_GIOCATORI da 'sd.py'.")
    print("Verifica che 'sd.py' sia presente.")
    print(f"Dettaglio: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERRORE import da sd.py: {e}")
    sys.exit(1)

# --- Funzione Caricamento ---
def carica_giocatori(filename):
    """Carica il dizionario giocatori da file pickle."""
    if not os.path.exists(filename):
        print(f"ERRORE: File '{filename}' non trovato.")
        return None
    try:
        with open(filename, "rb") as f:
            data = pickle.load(f)
            # Filtra eventuali chiavi non valide per sicurezza
            giocatori_validi = {k: v for k, v in data.items() if isinstance(k, int)}
            if len(data) != len(giocatori_validi):
                print(f"ATTENZIONE: Filtrate {len(data) - len(giocatori_validi)} chiavi non intere dal DB.")
            return giocatori_validi
    except Exception as e:
        print(f"ERRORE durante il caricamento di '{filename}': {e}")
        return None

# --- Logica Principale ---
def main():
    print("--- Visualizzatore Dati Raw Giocatore ---")

    # Carica giocatori
    giocatori = carica_giocatori(DB_GIOCATORI)
    if giocatori is None:
        sys.exit(1) # Errore già stampato da carica_giocatori

    if not giocatori:
        print("Il database dei giocatori è vuoto.")
        sys.exit(0)

    print(f"Caricati {len(giocatori)} giocatori.")

    while True:
        try:
            # Chiedi ID
            id_input = input("Inserisci l'ID del giocatore da visualizzare (o lascia vuoto per uscire): ")
            if not id_input:
                break # Esce dal loop

            player_id = int(id_input)

            # Cerca giocatore
            if player_id in giocatori:
                player_obj = giocatori[player_id]
                print(f"\n--- Dati Raw Giocatore ID: {player_id} ---")
                print(f"(Nome: {getattr(player_obj, 'nome', '?')} {getattr(player_obj, 'cognome', '?')})")
                print("-" * 40)

                # Stampa tutti gli attributi usando __dict__ e pprint
                # __dict__ contiene tutti gli attributi dell'istanza
                if hasattr(player_obj, '__dict__'):
                    # Usa sort_dicts=False se la tua versione di Python lo supporta per mantenere ordine
                    try:
                        pprint.pprint(player_obj.__dict__, indent=2, sort_dicts=False)
                    except TypeError: # Versioni più vecchie non hanno sort_dicts
                        pprint.pprint(player_obj.__dict__, indent=2)
                else:
                     print("Impossibile accedere agli attributi tramite __dict__.")

                print("-" * 40)

            else:
                print(f"ERRORE: Giocatore con ID {player_id} non trovato nel database.")

        except ValueError:
            print("ERRORE: Inserisci un ID numerico valido.")
        except EOFError:
            break # Esce in caso di Ctrl+D/Ctrl+Z
        except Exception as e:
            print(f"ERRORE inaspettato: {e}")
            traceback.print_exc()

    print("\nUscita dal visualizzatore.")


if __name__ == "__main__":
    main()