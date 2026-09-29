# Manageriale e Simulatore Showdown by Gabriele Battaglia & Gemini 2.5
# Data concepimento: 13/04/2015 16:13 by Gabriele Battaglia
# Inizio porting a Python 3.8.1: 31/01/2020. Ora in python 3.13.2 aprile 2025
import time
import datetime
import random
import pickle
import os
import sys
import math
import traceback
from typing import List, Dict, Tuple, Any, Optional, Set
from GBUtils import menu, key, dgt, percorso_risorsa

# --- Costanti Globali ---
VERSIONE = "25.4.24" # fai partite per testare le nuove funzioni introdotte di scaling potenza giocatori.
DB_GIOCATORI = "sd-players.db"
DB_POLISPORTIVE = "sd-polisport.db"
DB_STATO_GIOCO = "sd-gamestate.db"
FILE_NOMI_M = "nomi_maschili.txt"
FILE_NOMI_F = "nomi_femminili.txt"
FILE_COGNOMI = "cognomi.txt"
ANNO_SIMULAZIONE_GIORNI = 108
PROBABILITA_IPOVEDENTE_CREAZIONE = 65.0
# --- Costanti Descrizione Fisica ---
INIZIO_FRASE_DESC = "Ha un viso "
CONN_VISO_OCCHI_DESC = ". Gli occhi sono "
CONN_OCCHI_NASO_DESC = ", mentre il naso è "
CONN_NASO_BOCCA_DESC = ". La bocca ha "
CONN_BOCCA_CAPELLI_DESC = ", i suoi capelli "
SEPARATORE_FINALE_DESC = "."
# --- Costanti Poli CPU ---
GIOCATORI_ATTIVI_PER_POLI_CPU_TARGET = 16.5
PROB_CREAZIONE_POLI_CPU_PER_TICK = 75.0
ETA_MINIMA_CHIUSURA_CPU_ANNI = 1.5
SOGLIA_GLORIA_BASSA_CHIUSURA = 60
SOGLIA_MINIMA_TESSERATI_CHIUSURA = 6
PROB_CHIUSURA_BASE_GIORNALIERA = 0.3
FATTORE_PROB_GLORIA = 0.5
FATTORE_PROB_TESSERATI = 0.5
MAX_PROB_CHIUSURA_GIORNALIERA = 2.0
# --- Mappa Contrasto Skill Partita ---
MAPPA_CONTRASTO_SKILL = {
    'battutasx_base': 'chiusurasx_base', 'battutadx_base': 'chiusuradx_base',
    'singolaspondasx_base': 'chiusuradx_base', 'singolaspondadx_base': 'chiusurasx_base',
    'diagonalesx_base': 'chiusuradx_base',  # Assumendo difesa incrociata
    'diagonaledx_base': 'chiusurasx_base',  # Assumendo difesa incrociata
    'lungolineasx_base': 'chiusurasx_base',
    'lungolineadx_base': 'chiusuradx_base',
    'doppiaspondasx_base': 'chiusuradx_base',
    'doppiaspondadx_base': 'chiusurasx_base',
    'triplaspondasx_base': 'chiusuradx_base',
    'triplaspondadx_base': 'chiusurasx_base',
    'bomba_base': 'tenutapaletta_base',
    'attacco_base': 'difesa_base',
}

# --- Costanti Simulazione Partita ---
PUNTI_PER_GOAL = 2
PUNTI_PER_FALLO_AVVERSARIO = 1
PUNTI_VITTORIA_SET_BASE = 11
PUNTI_VANTAGGIO_NECESSARI = 2
PUNTI_LIMITE_SET = 17
SERVIZI_CONSECUTIVI_PER_GIOCATORE = 2
MARGINE_GOAL = 5.0
MARGINE_DIFESA = 3.0
PROB_FALLO_SU_FALLIMENTO_NORMALE = 20.0
PROB_PALLAMORTA_SU_FALLIMENTO_NORMALE = 5.0
FATTORE_BONUS_DIFESA_SU_RITORNO_FACILE = 1.4 # Bonus moltiplicativo difesa
VALORE_AZIONE_BONUS_BATTUTA = 25
ETA_MIN_CALO_RES = 20.0
ETA_MAX_CALO_RES = 55.0
TARGET_MIN_PERC_RES_SET5 = 0.45 # Target resistenza % set 5 per giovani
TARGET_MAX_PERC_RES_SET5 = 0.06 # Target resistenza % set 5 per vecchi
MODALITA_OUTPUT_RISULTATO = 'risultato'
MODALITA_OUTPUT_CONSOLE = 'console'
MODALITA_OUTPUT_FILE = 'file'
NOME_FILE_LOG_PARTITE = "log_partite_showdown.txt"
NOME_FILE_LOG_USCITE = "vecchie_glorie.log"
# --- Costanti Scaling Azione Partita ---
SCALING_K_DIFESA_ICV = 0.55  # Moltiplicatore ICV per stimare capacità difensiva generica
SCALING_SOGLIA_BASE = 50.0   # Punto medio della soglia di successo (tra 5 e 95)
SCALING_MODIFICATORE_MAX = 40.0 # Massimo scostamento (+/-) dalla soglia base
SCALING_RANGE_DELTA_EFF = 100.0 # Stima del range realistico di delta_azione (es. da -50 a +50)
# --- Costanti Infortunio ---
PROB_INFORTUNIO_BASE_PER_PARTITA = 0.015
ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI = 30.0
ETA_MAX_PROB_INFORTUNIO_ANNI = 75.0
PROB_INFORTUNIO_AUMENTO_MAX_PERC = 10.0
INFORTUNIO_DURATA_MIN_GIORNI = 3
INFORTUNIO_DURATA_MAX_GIORNI_ETA = 35
INFORTUNIO_MALUS_MAX_RESISTENZA = 10

# --- Costanti Guadagno Punti Esperienza (XP) per Partita ---
XP_VITTORIA_2_0 = 4; XP_VITTORIA_2_1 = 3; XP_SCONFITTA_1_2 = 2; XP_SCONFITTA_0_2 = 1
XP_VITTORIA_3_0 = 7; XP_VITTORIA_3_1 = 6; XP_VITTORIA_3_2 = 5
XP_SCONFITTA_2_3 = 4; XP_SCONFITTA_1_3 = 3; XP_SCONFITTA_0_3 = 2
XP_BONUS_TORNEO = 3; XP_BONUS_UNDERDOG = 1
ICV_DIFF_PERC_UNDERDOG = 25.0

# --- Costanti Costo Allenamento XP ---
XP_COSTO_SKILL_BREAKPOINTS = {0: 25, 9: 100, 15: 200, 19: 500} # Breakpoint per skill 0-20
XP_COSTO_FISICO_MOLTIPL = 2.0 # Si applica a Precisione, Resistenza E FORZA # <-- AGGIUNTO FORZA
XP_SCONTO_IPOVEDENTI_PERC = 7.0
MAX_ALLENATO_FISICO = 5.0 # Per Precisione, Resistenza E FORZA # <-- AGGIUNTO FORZA
MAX_ALLENATO_SKILL = 20.0 # Per le altre skill

# --- Parametri Calcolo Gloria Richiesta Giocatore ---
K_ICV_GLORIA_RICHIESTA = 0.9
ETA_PICCO_RICHIESTA_GLORIA_ANNI = 17.0
ETA_MINIMO_RICHIESTA_GLORIA_ANNI = 55.0
MAX_FATTORE_ETA_GLORIA = 2.7
MIN_FATTORE_ETA_GLORIA = 0.1
GLORIA_RICHIESTA_FISSA = 12
GLORIA_RICHIESTA_MINIMA_ASSOLUTA = 8
MAX_GLORIA_RICHIESTA = 1500
FATTORE_GLORIA_RICHIESTA_AMBIDESTRO = 1.35
FATTORE_GLORIA_RICHIESTA_GIOCO_RAPIDO = 1.10
FATTORE_GLORIA_RICHIESTA_CAMBIO_VEL = 1.10

# --- Parametri Calcolo Probabilità Accettazione Tesseramento ---
ACCETTAZIONE_REL_DIFF_THRESHOLD = 0.30
ACCETTAZIONE_PROB_MIN = 3.0
ACCETTAZIONE_PROB_MAX = 97.0
ACCETTAZIONE_PROB_MID = 50.0

# --- Età in ANNI (del simulatore) ---
ETA_MIN_CREAZIONE_ANNI = 9.0; ETA_MAX_CREAZIONE_ANNI = 45.0
AGING_START_AGE_ANNI = 50.0; ETA_MIN_RITIRO_ANNI = 58.0; ETA_MAX_RITIRO_ANNI = 75.0
ETA_MIN_MORTE_ANNI = 70.0; ETA_MAX_MORTE_ANNI = 103.0; AGING_PEAK_AGE_ANNI = 90.0
PROB_USCITA_PREMATURA_GIORNALIERA = 0.0075

# --- Funzione Helper Conversione Età ---
def _calcola_giorni_da_anni(anni):
    return int(anni * ANNO_SIMULAZIONE_GIORNI) if ANNO_SIMULAZIONE_GIORNI > 0 else int(anni*365.25)

# --- Converti età chiave in GIORNI di simulazione ---
ETA_MIN_CREAZIONE_GIORNI = _calcola_giorni_da_anni(ETA_MIN_CREAZIONE_ANNI)
ETA_MAX_CREAZIONE_GIORNI = _calcola_giorni_da_anni(ETA_MAX_CREAZIONE_ANNI)
AGING_START_AGE_GIORNI = _calcola_giorni_da_anni(AGING_START_AGE_ANNI)
ETA_MIN_RITIRO_GIORNI = _calcola_giorni_da_anni(ETA_MIN_RITIRO_ANNI)
ETA_MAX_RITIRO_GIORNI = _calcola_giorni_da_anni(ETA_MAX_RITIRO_ANNI)
ETA_MIN_MORTE_GIORNI = _calcola_giorni_da_anni(ETA_MIN_MORTE_ANNI)
ETA_MAX_MORTE_GIORNI = _calcola_giorni_da_anni(ETA_MAX_MORTE_ANNI)
AGING_PEAK_AGE_GIORNI = _calcola_giorni_da_anni(AGING_PEAK_AGE_ANNI)

# --- Costanti Aging & Skill ---
MAX_AGING_REDUCTION_FACTOR_PER_ANNO_SIM = 0.018
MAX_SKILL_VALUE = 20.0
MAX_PRECISIONE_RESISTENZA = 5.0 # Limite base per Precisione, Resistenza E FORZA # <-- AGGIUNTO FORZA
MAX_TOTALE_PRECISIONE_RESISTENZA = 10.0 # Limite totale (base+allenato) per Precisione, Resistenza E FORZA # <-- AGGIUNTO FORZA
MAX_TOTALE_SKILL_GIOCO = 40.0 # Limite totale per le altre skill

# --- Limiti & Costanti Varie ---
MAX_XP_PER_ALLENAMENTO = 15000
MAX_TESSERATI_POLISPORTIVA = 15
PAGINAZIONE_LISTE = 25
LIMITE_MOVIMENTI_PER_TICK = 5
NUM_GIOCATORI_INIZIALI = 50
CREA_NUOVI_PER_TICK_RANGE = (1, 7)
MAX_NUOVI_GIOCATORI_PER_AVVIO = 50

# --- Liste Attributi (aggiornate per FORZA) ---
ATTRIBUTI_BASE = {
    'id', 'nome', 'cognome', 'appartenenza', 'sesso', 'eta', 'etaritiro', 'etamorte',
    'versione', 'datetime_creazione_sim', 'datacreazione_reale', 'descrizione_fisica',
    'mancino', 'ambidestro', 'infortunato', 'infortunio_fine_datetime', 'ipovedente',
    'altezza', 'peso', 'giocorapido', 'cambiovelocita', 'ritirato', 'puntiesperienza',
    'partitevinte', 'partiteperse', 'setsvinti', 'setspersi', 'goalsfatti', 'goalssubiti',
    'precisione_base', 'resistenza_base', 'forza_base', # <-- AGGIUNTO FORZA_BASE
    'difesa_base', 'tenutapaletta_base',
    'chiusurasx_base', 'chiusuradx_base', 'bloccosx_base', 'bloccodx_base',
    'controllopalla_base', 'attacco_base', 'battutasx_base', 'battutadx_base', 'bomba_base',
    'lungolineasx_base', 'lungolineadx_base', 'diagonalesx_base', 'diagonaledx_base',
    'singolaspondasx_base', 'singolaspondadx_base', 'doppiaspondasx_base', 'doppiaspondadx_base',
    'triplaspondasx_base', 'triplaspondadx_base', 'icv_base', 'icv_allenato',
    'indice_collettivo_valore', 'archetipo_allenamento', 'ori', 'argenti', 'bronzi', 'legni'
}
ATTRIBUTI_ALLENABILI_MAP = {
    "prc": "precisione_allenata", "rst": "resistenza_allenata", "for": "forza_allenata", # <-- AGGIUNTO FORZA
    "dfa": "difesa_allenata",
    "tpa": "tenutapaletta_allenata", "csa": "chiusurasx_allenata", "cda": "chiusuradx_allenata",
    "bsa": "bloccosx_allenata", "bda": "bloccodx_allenata", "cpa": "controllopalla_allenata",
    "ata": "attacco_allenata", "btsa": "battutasx_allenata", "btda": "battutadx_allenata",
    "ba": "bomba_allenata", "llsa": "lungolineasx_allenata", "llda": "lungolineadx_allenata",
    "dsa": "diagonalesx_allenata", "dda": "diagonaledx_allenata", "sss": "singolaspondasx_allenata",
    "ssd": "singolaspondadx_allenata", "dpsa": "doppiaspondasx_allenata", "dpda": "doppiaspondadx_allenata",
    "tpsa": "triplaspondasx_allenata", "tpda": "triplaspondadx_allenata",
}
ATTRIBUTI_ALLENABILI: Set[str] = set(ATTRIBUTI_ALLENABILI_MAP.values())
ATTRIBUTI_BASE_CON_ALLENABILI: Set[str] = { attr.replace('_allenata', '_base') for attr in ATTRIBUTI_ALLENABILI }
ATTRIBUTI_INVECCHIABILI: Set[str] = ATTRIBUTI_BASE_CON_ALLENABILI.union(ATTRIBUTI_ALLENABILI)

# --- Liste Raggruppamento Caratteristiche (FORZA è fisica) ---
CARATTERISTICHE_FISICHE_BASE = ["precisione_base", "resistenza_base", "forza_base"] # <-- AGGIUNTO FORZA_BASE
CARATTERISTICHE_DIFESA_BASE = ["chiusurasx_base", "bloccosx_base", "bloccodx_base", "chiusuradx_base"]
CARATTERISTICHE_ATTACCO_BASE = [
    "battutasx_base", "lungolineasx_base", "diagonalesx_base", "singolaspondasx_base",
    "doppiaspondasx_base", "triplaspondasx_base", "bomba_base", "triplaspondadx_base",
    "doppiaspondadx_base", "singolaspondadx_base", "diagonaledx_base", "lungolineadx_base", "battutadx_base"
]
CARATTERISTICHE_CONTROLLO_BASE = ["difesa_base", "controllopalla_base", "tenutapaletta_base", "attacco_base"]

# --- Costanti Auto-Allenamento CPU ---
ETA_GIOVANE_MAX_GIORNI = _calcola_giorni_da_anni(20)
ETA_ANZIANO_MIN_GIORNI = AGING_START_AGE_GIORNI
PROB_SEGUE_ARCHETIPO = 80.0
PROB_ARCHETIPO_CASUALE_CREAZIONE = 10.0
ARCHETIPI_ALLENAMENTO = {
    "AttaccantePuro": { "desc": "Massimizza danno offensivo.", "priorita": ["attacco_allenata", "bomba_allenata", "diagonaledx_allenata", "diagonalesx_allenata", "lungolineadx_allenata", "lungolineasx_allenata", "precisione_allenata"], "strategia_scelta": "piu_bassa_prioritaria", "strategia_spesa": {"tipo": "percentuale", "valore": 25, "max_xp": 750}, "influenza_eta": {"anziano": "piu_economica_prioritaria"}},
    "DifensoreRoccioso": { "desc": "Focus su difesa e blocchi.", "priorita": ["difesa_allenata", "chiusuradx_allenata", "chiusurasx_allenata", "bloccodx_allenata", "bloccosx_allenata", "tenutapaletta_allenata", "resistenza_allenata"], "strategia_scelta": "piu_bassa_prioritaria", "strategia_spesa": {"tipo": "percentuale", "valore": 25, "max_xp": 750}, "influenza_eta": {"anziano": "piu_economica_prioritaria_o_resistenza"}},
    "MuroFisico": { "desc": "Priorità a precisione e Resistenza.", "priorita": ["precisione_allenata", "resistenza_allenata", "forza_allenata"], "strategia_scelta": "piu_bassa_tra_due", "strategia_spesa": {"tipo": "percentuale", "valore": 40, "max_xp": 1500}, "influenza_eta": {"anziano": "piu_bassa_tra_due_assoluta"}}, # <-- AGGIUNTO FORZA (priorità)
    "SpecialistaBlocchiDifesa": { "desc": "Eccelle nei blocchi e difesa generale.", "priorita": ["bloccodx_allenata", "bloccosx_allenata", "difesa_allenata", "chiusuradx_allenata", "chiusurasx_allenata", "tenutapaletta_allenata", "resistenza_allenata"], "strategia_scelta": "piu_bassa_prioritaria", "strategia_spesa": {"tipo": "quota_fissa", "valore": 400}, "influenza_eta": {"anziano": "piu_economica_prioritaria"}},
    "SpecialistaBlocchiAttacco": { "desc": "Blocca e riparte con attacchi controllati.", "priorita": ["bloccodx_allenata", "bloccosx_allenata", "attacco_allenata", "controllopalla_allenata", "diagonaledx_allenata", "diagonalesx_allenata", "precisione_allenata"], "strategia_scelta": "piu_bassa_prioritaria", "strategia_spesa": {"tipo": "quota_fissa", "valore": 400}, "influenza_eta": {"anziano": "piu_economica_prioritaria"}},
    "SpecialistaBlocchiControllo": { "desc": "Maestro blocchi e controllo palla.", "priorita": ["bloccodx_allenata", "bloccosx_allenata", "controllopalla_allenata", "tenutapaletta_allenata", "difesa_allenata", "resistenza_allenata"], "strategia_scelta": "a_rotazione", "strategia_spesa": {"tipo": "percentuale", "valore": 20, "max_xp": 500}, "influenza_eta": {}},
    "SpecialistaBattutaBlocco": { "desc": "Servizio efficace e buon muro.", "priorita": ["battutadx_allenata", "battutasx_allenata", "bloccodx_allenata", "bloccosx_allenata", "precisione_allenata", "difesa_allenata"], "strategia_scelta": "piu_bassa_prioritaria", "strategia_spesa": {"tipo": "obiettivo_punti", "valore": 0.1, "max_xp": 600}, "influenza_eta": {"anziano": "piu_economica_prioritaria"}},
    "CecchinoPreciso": { "desc": "Focus su colpi specifici e controllo.", "priorita": ["lungolineadx_allenata", "lungolineasx_allenata", "singolaspondadx_allenata", "singolaspondasx_allenata", "doppiaspondadx_allenata", "doppiaspondasx_allenata", "controllopalla_allenata", "tenutapaletta_allenata"], "strategia_scelta": "a_rotazione", "strategia_spesa": {"tipo": "quota_fissa", "valore": 350}, "influenza_eta": {}},
    "TuttofareBilanciato": { "desc": "Sviluppo equilibrato.",
                             "priorita_non_fisiche": [s for s in ATTRIBUTI_ALLENABILI if s not in ["precisione_allenata", "resistenza_allenata", "forza_allenata"]], # <-- AGGIUNTO FORZA
                             "priorita_fisiche": ["precisione_allenata", "resistenza_allenata", "forza_allenata"], # <-- AGGIUNTO FORZA
                             "strategia_scelta": "piu_bassa_assoluta_non_fisica", "strategia_spesa": {"tipo": "percentuale", "valore": 15, "max_xp": 300}, "influenza_eta": {"anziano": "piu_bassa_assoluta_o_fisica_bassa"}}
}

# --- Verifica coerenza skill ---
# Escludi TUTTE le fisiche (ora include forza)
_skill_gioco_definite = set(CARATTERISTICHE_DIFESA_BASE + CARATTERISTICHE_ATTACCO_BASE + CARATTERISTICHE_CONTROLLO_BASE)
_skill_gioco_totali = {attr for attr in ATTRIBUTI_BASE_CON_ALLENABILI if attr not in CARATTERISTICHE_FISICHE_BASE}
if _skill_gioco_definite != _skill_gioco_totali:
    print("ATTENZIONE: Discrepanza liste raggruppamento caratteristiche!")
    print(f"  Mancanti in Definite: {_skill_gioco_totali - _skill_gioco_definite}")
    print(f"  Extra in Definite: {_skill_gioco_definite - _skill_gioco_totali}")

# --- Menu ---
MAINMENU = {
    'AGT': 'Allena Giocatori Tesserati;', 'CEG': 'CErca Giocatori;', 'CLA': 'CLAssifica Globale Giocatori (per ICV);',
    'CTT': 'Copia Tesserati attuali nei Trovati;', 'MPO': 'Menu delle POlisportive;', 'OPA': 'Organizza Partita Amichevole;',
    'SGG': 'Statistica Globale Giocatori;', 'TOP': 'TOP10 giocatori e Polisportive;', 'VLN': 'Vedi Lista Nuovi;',
    'VLM': 'Vedi Lista Morti;', 'VLT': 'Vedi Lista Trovati (risultati ricerca);', 'VLR': 'Vedi Lista Ritirati;',
    'VRG': 'Vedi Riepilogo Giocatori (per ID range);', 'VSG': 'Vedi Scheda Giocatore;', 'DTS': 'Visualizza Data/Ora Simulazione;',
    '?': 'visualizza questo MENu;', '': 'INVIO a vuoto per USCIRE e salvare.'
}
POLIMENU = {
    "APR": "APRi una nuova polisportiva;", "CHI": "CHIudi la polisportiva attiva;", "CPA": "Cambia Polisportiva Attiva;",
    "ESG": "ESpelli Giocatore dalla polisportiva attiva;", "MPP": "Modifica Password Polisportiva attiva;",
    "TEG": "TEssera Giocatore nella polisportiva attiva;", "VGT": "Vedi Giocatori Tesserati della polisportiva attiva;",
    "VGP": "Vedi Giocatori Papabili (liberi ordinati per ICV);", "VLE": "Vedi Lista Polisportive Esistenti;",
    "VSP": "Vedi Scheda Polisportiva attiva;", "?": "Vedi Questo Menu;", "": "INVIO per tornare al menu principale;"
}
MENU_ALLENAMENTO = {
    "PRC": "Precisione;", "RST": "Resistenza;", "FOR": "Forza;", # <-- AGGIUNTO FORZA
    "DFA": "Difesa;", "TPA": "Tenuta paletta;", "CSA": "Chiusura SX;",
    "CDA": "Chiusura DX;", "BSA": "Blocco SX;", "BDA": "Blocco DX;", "CPA": "Controllo palla;", "ATA": "Attacco;",
    "BTSA": "Battuta SX;", "BTDA": "Battuta DX;", "BA": "Bomba;", "LLSA": "Lungolinea SX;", "LLDA": "Lungolinea DX;",
    "DSA": "Diagonale SX;", "DDA": "Diagonale DX;", "SSS": "S.Sponda SX;", "SSD": "S.Sponda DX;", "DPSA": "D.Sponda SX;",
    "DPDA": "D.Sponda DX;", "TPSA": "T.Sponda SX;", "TPDA": "T.Sponda DX;", "": "Termina allenamento atleta;"
}
MENU_RICERCA = {
    "ICV": "ICV;", "ETA": "Eta (anni sim);", "NOME": "Nome;", "COGNOME": "Cognome;", "IPO": "Ipovedente (s/n);",
    "PRC": "Precisione (Tot);", "RST": "Resistenza (Tot);", "FOR": "Forza (Tot);", # <-- AGGIUNTO FORZA
    "DFA": "Difesa (Tot);", "TPA": "Tenuta paletta (Tot);",
    "CSA": "Chiusura SX (Tot);", "CDA": "Chiusura DX (Tot);", "BSA": "Blocco SX (Tot);", "BDA": "Blocco DX (Tot);",
    "CPA": "Controllo palla (Tot);", "ATA": "Attacco (Tot);", "BTSA": "Battuta SX (Tot);", "BTDA": "Battuta DX (Tot);",
    "BA": "Bomba (Tot);", "LLSA": "Lungolinea SX (Tot);", "LLDA": "Lungolinea DX (Tot);", "DSA": "Diagonale SX (Tot);",
    "DDA": "Diagonale DX (Tot);", "SSS": "S.Sponda SX (Tot);", "SSD": "S.Sponda DX (Tot);",
    "DPSA": "D.Sponda SX (Tot);", "DPDA": "D.Sponda DX (Tot);", "TPSA": "T.Sponda SX (Tot);", "TPDA": "T.Sponda DX (Tot);"
}
MAPPA_RICERCA_ATTRIBUTI = {
    "ICV": "indice_collettivo_valore", "ETA": "eta_anni", "NOME": "nome", "COGNOME": "cognome", "IPO": "ipovedente",
    "PRC": "precisione_totale", "RST": "resistenza_totale", "FOR": "forza_totale", # <-- AGGIUNTO FORZA
    "DFA": "difesa_totale", "TPA": "tenutapaletta_totale",
    "CSA": "chiusurasx_totale", "CDA": "chiusuradx_totale", "BSA": "bloccosx_totale", "BDA": "bloccodx_totale",
    "CPA": "controllopalla_totale", "ATA": "attacco_totale", "BTSA": "battutasx_totale", "BTDA": "battutadx_totale",
    "BA": "bomba_totale", "LLSA": "lungolineasx_totale", "LLDA": "lungolineadx_totale", "DSA": "diagonalesx_totale",
    "DDA": "diagonaledx_totale", "SSS": "singolaspondasx_totale", "SSD": "singolaspondadx_totale",
    "DPSA": "doppiaspondasx_totale", "DPDA": "doppiaspondadx_totale", "TPSA": "triplaspondasx_totale", "TPDA": "triplaspondadx_totale"
}
NOME_ATTR_TO_DISPLAY_MAP = {
    "precisione_base": "Precisione", "precisione_allenata": "Precisione",
    "resistenza_base": "Resistenza", "resistenza_allenata": "Resistenza",
    "forza_base": "Forza", "forza_allenata": "Forza", # <-- AGGIUNTO FORZA
    "attacco_base": "Attacco", "attacco_allenata": "Attacco",
    "battutadx_base": "Battuta Destra", "battutadx_allenata": "Battuta Destra", "battutasx_base": "Battuta Sinistra",
    "battutasx_allenata": "Battuta Sinistra", "bloccodx_base": "Blocco Destro", "bloccodx_allenata": "Blocco Destro",
    "bloccosx_base": "Blocco Sinistro", "bloccosx_allenata": "Blocco Sinistro", "bomba_base": "Bomba Centrale",
    "bomba_allenata": "Bomba Centrale", "chiusuradx_base": "Chiusura Destra", "chiusuradx_allenata": "Chiusura Destra",
    "chiusurasx_base": "Chiusura Sinistra", "chiusurasx_allenata": "Chiusura Sinistra", "controllopalla_base": "Controllo Palla",
    "controllopalla_allenata": "Controllo Palla", "diagonaledx_base": "Diagonale Destra", "diagonaledx_allenata": "Diagonale Destra",
    "diagonalesx_base": "Diagonale Sinistra", "diagonalesx_allenata": "Diagonale Sinistra", "difesa_base": "Difesa",
    "difesa_allenata": "Difesa", "doppiaspondadx_base": "Doppia Sponda Destra", "doppiaspondadx_allenata": "Doppia Sponda Destra",
    "doppiaspondasx_base": "Doppia Sponda Sinistra", "doppiaspondasx_allenata": "Doppia Sponda Sinistra",
    "lungolineadx_base": "Lungolinea Destro", "lungolineadx_allenata": "Lungolinea Destro", "lungolineasx_base": "Lungolinea Sinistro",
    "lungolineasx_allenata": "Lungolinea Sinistro", "singolaspondadx_base": "Singola Sponda Destra",
    "singolaspondadx_allenata": "Singola Sponda Destra", "singolaspondasx_base": "Singola Sponda Sinistra",
    "singolaspondasx_allenata": "Singola Sponda Sinistra", "tenutapaletta_base": "Tenuta Paletta",
    "tenutapaletta_allenata": "Tenuta Paletta", "triplaspondadx_base": "Tripla Sponda Destra",
    "triplaspondadx_allenata": "Tripla Sponda Destra", "triplaspondasx_base": "Tripla Sponda Sinistra",
    "triplaspondasx_allenata": "Tripla Sponda Sinistra",
}
MAPPA_FLAG_SOMMARIO = {'mancino': 'M', 'ambidestro': 'A', 'infortunato': 'I', 'ipovedente': 'P', 'giocorapido': 'R', 'cambiovelocita': 'V'}

# --- Utility Functions ---
def carica_nomi(filename: str) -> List[str]:
    """Legge una collezione dalla cartella dati: una voce per riga, commenti col cancelletto."""
    percorso = percorso_risorsa(os.path.join("dati", filename))
    try:
        with open(percorso, encoding="utf-8") as f:
            return [r.strip() for r in f if r.strip() and not r.lstrip().startswith("#")]
    except FileNotFoundError: print(f"ATT: File {percorso} non trovato."); return []
    except Exception as e: print(f"Errore caricamento {percorso}: {e}"); return []

def genera_modelli(lista_nomi: List[str]) -> List[str]:
    modelli = set()
    for nome in lista_nomi:
        modello = "".join(["v" if c in 'aeiouy' else "c" if c in 'bcdfghjklmnpqrstvwxz' else "s" if c == ' ' else '' for c in nome.lower()])
        if modello: modelli.add(modello)
    return list(modelli)

def genera_nome_casuale(modelli: List[str], tipo: str) -> str:
    if not modelli: return "Casuale"
    modello = random.choice(modelli)
    nome = "".join([random.choice('bcdfghjklmnpqrstvwxz') if ct == 'c' else " " if ct == 's' else random.choice('aeiouy') for ct in modello])
    return nome.title()

def _converti_giorni_sim_a_aa_mm_gg(giorni_totali: int,
                                     anno_sim_giorni: int = ANNO_SIMULAZIONE_GIORNI,
                                     mesi_anno: int = 12,
                                     giorni_mese: int = 9,
                                     per_eta: bool = False) -> Tuple[int, int, int]:
    if giorni_totali < 0: return (0, 0, 0) if per_eta else (0, 1, 1)
    if anno_sim_giorni <= 0: return (0, 0, 0) if per_eta else (0, 1, 1)
    anni_compiuti = giorni_totali // anno_sim_giorni
    giorni_dopo_compleanno = giorni_totali % anno_sim_giorni
    if giorni_mese <= 0: mesi_dopo_compleanno, giorni_dopo_mese = 0, giorni_dopo_compleanno
    else: mesi_dopo_compleanno, giorni_dopo_mese = divmod(giorni_dopo_compleanno, giorni_mese)
    if per_eta: return anni_compiuti, mesi_dopo_compleanno, giorni_dopo_mese
    else: return anni_compiuti, mesi_dopo_compleanno + 1, giorni_dopo_mese + 1

def _formatta_eta_sim(giorni_totali: int, formato_breve: bool = False) -> str:
    try:
        anni, mesi, giorni = _converti_giorni_sim_a_aa_mm_gg(giorni_totali, per_eta=True)
        if formato_breve: return f"{anni}/{mesi}/{giorni}"
        else:
            a_str = f"{anni} ann{'o' if anni == 1 else 'i'}"
            if mesi > 0 or giorni > 0:
                m_str = f"{mesi} mes{'e' if mesi == 1 else 'i'}"
                g_str = f"{giorni} giorn{'o' if giorni == 1 else 'i'}"
                return f"{a_str}, {m_str} e {g_str}"
            else: return f"{a_str} (compiuti)"
    except Exception: return "Età N/D"

def caso(percentuale: float) -> bool:
    if not 0 <= percentuale <= 100: percentuale = max(0, min(100, percentuale))
    return random.uniform(0, 100) < percentuale

def converti_in_tempo(secondi: float) -> Tuple[int, int, int]:
    try: s_int=int(secondi); s=s_int%60; m_tot=s_int//60; m=m_tot%60; h=m_tot//60; return h,m,s
    except Exception: return 0,0,0

# --- Caricamento Nomi e Descrizioni ---
NOMI_MASCHILI = carica_nomi(FILE_NOMI_M); NOMI_FEMMINILI = carica_nomi(FILE_NOMI_F); COGNOMI = carica_nomi(FILE_COGNOMI)
MODELLI_NOMI_M = genera_modelli(NOMI_MASCHILI); MODELLI_NOMI_F = genera_modelli(NOMI_FEMMINILI); MODELLI_COGNOMI = genera_modelli(COGNOMI)
print("Caricamento frasi descrizione fisica...")
_D = "descrizioni"
FRASI_BOCCA_T = carica_nomi(os.path.join(_D, "bocche.txt")); FRASI_COLORI_CAPELLI_T = carica_nomi(os.path.join(_D, "colori_capelli.txt"))
FRASI_NASI_T = carica_nomi(os.path.join(_D, "nasi.txt")); FRASI_OCCHI_T = carica_nomi(os.path.join(_D, "occhi.txt"))
FRASI_TAGLIO_CAPELLI_F = carica_nomi(os.path.join(_D, "tagli_capelli_f.txt")); FRASI_TAGLIO_CAPELLI_M = carica_nomi(os.path.join(_D, "tagli_capelli_m.txt"))
FRASI_VISI_F = carica_nomi(os.path.join(_D, "visi_f.txt")); FRASI_VISI_M = carica_nomi(os.path.join(_D, "visi_m.txt"))
_descrizioni_caricate = {'bocca_t': FRASI_BOCCA_T, 'colori_capelli_t': FRASI_COLORI_CAPELLI_T, 'nasi_t': FRASI_NASI_T, 'occhi_t': FRASI_OCCHI_T,
                         'taglio_capelli_f': FRASI_TAGLIO_CAPELLI_F, 'taglio_capelli_m': FRASI_TAGLIO_CAPELLI_M, 'visi_f': FRASI_VISI_F, 'visi_m': FRASI_VISI_M}
for k, v in _descrizioni_caricate.items():
    if not v: sys.exit(f"ERRORE CRITICO: Lista descrizione '{k}' nella cartella dati è vuota o non caricata!")

# --- Funzione Genera Identita ---
def genera_identita(sesso: str) -> Tuple[str, str]:
    lista_n = NOMI_MASCHILI if sesso=='m' else NOMI_FEMMINILI; modelli_n = MODELLI_NOMI_M if sesso=='m' else MODELLI_NOMI_F
    nome = genera_nome_casuale(modelli_n, sesso) if caso(6.0) else random.choice(lista_n) if lista_n else "NomeCasuale"
    cogn = genera_nome_casuale(MODELLI_COGNOMI, 'c') if caso(8.0) else random.choice(COGNOMI) if COGNOMI else "CognomeCasuale"
    return nome.title(), cogn.title()

# --- Classi Principali ---
class Giocatore:
    def __init__(self, id_giocatore: int, datetime_creazione_sim: datetime.datetime, **kwargs: Any):
        self.id: int = id_giocatore; self.nome: str = "*"; self.cognome: str = "*"
        self.appartenenza: str = "*"; self.sesso: str = random.choice(('m', 'f'))
        eta_anni_casuale = random.uniform(ETA_MIN_CREAZIONE_ANNI, ETA_MAX_CREAZIONE_ANNI)
        self.eta: int = _calcola_giorni_da_anni(eta_anni_casuale)
        self.etaritiro: int = int(random.uniform(ETA_MIN_RITIRO_GIORNI, ETA_MAX_RITIRO_GIORNI))
        self.etamorte: int = int(random.uniform(ETA_MIN_MORTE_GIORNI, ETA_MAX_MORTE_GIORNI))
        self.versione: str = VERSIONE; self.descrizione_fisica: str = ""
        self.datetime_creazione_sim: datetime.datetime = datetime_creazione_sim
        self.datacreazione_reale: datetime.datetime = datetime.datetime.now()
        self.puntiesperienza: int = 0; self.mancino: bool = caso(8.5)
        self.ambidestro: bool = caso(4.25) if not self.mancino else False
        self.infortunato: bool = False; self.infortunio_fine_datetime: Optional[datetime.datetime] = None
        self.ipovedente: bool = False; self.altezza: int = random.randrange(160, 186); self.peso: int = 70
        self.giocorapido: bool = caso(12.0); self.cambiovelocita: bool = caso(15.0); self.ritirato: bool = False
        self.partitevinte: int = 0; self.partiteperse: int = 0; self.setsvinti: int = 0; self.setspersi: int = 0
        self.goalsfatti: int = 0; self.goalssubiti: int = 0
        self.icv_base: float = 0.0; self.icv_allenato: float = 0.0; self.indice_collettivo_valore: float = 0.0
        self.archetipo_allenamento: str = "Non Definito"; self.ori=0; self.argenti=0; self.bronzi=0; self.legni=0
        # <-- AGGIUNTO FORZA - Inizializzazione attributi base/allenata
        self.forza_base: float = 0.0
        self.forza_allenata: float = 0.0

        # Inizializzazione attributi base/allenati (loop)
        for nome_base in ATTRIBUTI_BASE_CON_ALLENABILI:
            nome_allenato = nome_base.replace('_base', '_allenata')
            # Determina se è fisica (Precisione, Resistenza o Forza)
            is_fisica = nome_base in CARATTERISTICHE_FISICHE_BASE # <-- AGGIUNTO FORZA (in lista)
            max_val = MAX_PRECISIONE_RESISTENZA if is_fisica else MAX_SKILL_VALUE
            setattr(self, nome_base, random.uniform(0, max_val * 0.6))
            setattr(self, nome_allenato, 0.0)

        # Gestione kwargs
        eta_giorni = kwargs.pop('eta', None)
        if 'ipovedente' in kwargs: self.ipovedente = bool(kwargs.pop('ipovedente')) if isinstance(kwargs['ipovedente'], bool) else str(kwargs.pop('ipovedente')).lower() in ['s','true','1','yes','vero']

        for key, value in kwargs.items():
            if key == 'nascita': continue
            elif key in ATTRIBUTI_ALLENABILI:
                try:
                    val_f = float(value)
                    # Determina se è fisica (Precisione, Resistenza o Forza)
                    is_f = key in ["precisione_allenata", "resistenza_allenata", "forza_allenata"] # <-- AGGIUNTO FORZA
                    lim_a = MAX_ALLENATO_FISICO if is_f else MAX_ALLENATO_SKILL
                    setattr(self, key, max(0.0, min(val_f, lim_a)))
                except:
                    setattr(self, key, 0.0)
                continue
            elif key == 'datetime_creazione_sim': self.datetime_creazione_sim = value if isinstance(value, datetime.datetime) else self.datetime_creazione_sim; continue
            elif key == 'datacreazione_reale': self.datacreazione_reale = value if isinstance(value, datetime.datetime) else self.datacreazione_reale; continue
            elif key == 'infortunio_fine_datetime': self.infortunio_fine_datetime = value if isinstance(value, datetime.datetime) else None; continue
            elif key == 'archetipo_allenamento': self.archetipo_allenamento = str(value) if isinstance(value, str) else "Non Definito"; continue
            elif key == 'descrizione_fisica': self.descrizione_fisica = str(value)[:500] if isinstance(value, str) else ""; continue
            elif hasattr(self, key):
                 try:
                     curr_t = type(getattr(self, key)); new_v = value
                     if key=='puntiesperienza' and not isinstance(value,int): new_v=int(value)
                     elif key in['etaritiro','etamorte'] and not isinstance(value,int):
                         try:
                            new_v=_calcola_giorni_da_anni(float(value)/10.)
                         except: continue
                     setattr(self, key, curr_t(new_v))
                 except:
                     try: setattr(self, key, value)
                     except: pass

        if eta_giorni is not None:
            try: self.eta = int(eta_giorni)
            except: pass

        # Controllo limite totale (dopo kwargs)
        for nome_base in ATTRIBUTI_BASE_CON_ALLENABILI:
            nome_allenato = nome_base.replace('_base', '_allenata')
            # Determina se è fisica (Precisione, Resistenza o Forza)
            is_fisica = nome_base in CARATTERISTICHE_FISICHE_BASE # <-- AGGIUNTO FORZA (in lista)
            max_totale_skill = MAX_TOTALE_PRECISIONE_RESISTENZA if is_fisica else MAX_TOTALE_SKILL_GIOCO
            v_b = getattr(self, nome_base, 0.0); v_a = getattr(self, nome_allenato, 0.0)
            if v_b+v_a > max_totale_skill:
                v_a_corr = max(0., max_totale_skill-v_b); setattr(self, nome_allenato, v_a_corr); v_a=v_a_corr
            if v_b+v_a > max_totale_skill: setattr(self, nome_base, max(0., max_totale_skill-v_a))

        # Aggiustamenti finali nome/fisico
        if self.nome=="*" and self.cognome=="*": self.nome,self.cognome=genera_identita(self.sesso)
        if 'altezza' not in kwargs: self.altezza=max(145,min(200,self.altezza+(random.randrange(0,16) if self.sesso=='m' else -random.randrange(0,16))))
        if 'peso' not in kwargs: self.peso=max(35,min(110,self.altezza-100+random.randrange(-15,16)+(random.randrange(0,11) if self.sesso=='m' else -random.randrange(0,8))))

        # Fallback per attributi essenziali (incluso forza)
        for attr, default in [('forza_base', 0.0), ('forza_allenata', 0.0), # <-- AGGIUNTO FORZA
                              ('ipovedente',False),('infortunato',False),('infortunio_fine_datetime',None),
                              ('archetipo_allenamento',"Non Definito"),('datacreazione_reale',self.datetime_creazione_sim),
                              ('descrizione_fisica',''),('ori',0),('argenti',0),('bronzi',0),('legni',0)]:
             if not hasattr(self, attr) or (getattr(self, attr, None) is None and default is not None): setattr(self, attr, default)

        # Assegna archetipo e calcola ICV
        if self.archetipo_allenamento=="Non Definito": self._assegna_archetipo_iniziale()
        self.aggiorna_icv()
        if not self.descrizione_fisica: self._genera_descrizione_fisica()

    def _get_valore_totale(self, nome_base: str) -> float:
        if not nome_base.endswith('_base'): return 0.0
        return getattr(self, nome_base, 0.0) + getattr(self, nome_base.replace('_base', '_allenata'), 0.0)

    @property
    def gloria_richiesta(self) -> int:
        g_base = self.indice_collettivo_valore * K_ICV_GLORIA_RICHIESTA
        if ANNO_SIMULAZIONE_GIORNI <= 0: return GLORIA_RICHIESTA_MINIMA_ASSOLUTA
        eta_p_gg = _calcola_giorni_da_anni(ETA_PICCO_RICHIESTA_GLORIA_ANNI); eta_m_gg = _calcola_giorni_da_anni(ETA_MINIMO_RICHIESTA_GLORIA_ANNI)
        range_eta = max(1, eta_m_gg - eta_p_gg); fatt_eta = MAX_FATTORE_ETA_GLORIA
        if self.eta >= eta_m_gg: fatt_eta = MIN_FATTORE_ETA_GLORIA
        elif self.eta > eta_p_gg: prog = (self.eta - eta_p_gg) / range_eta; fatt_eta = MAX_FATTORE_ETA_GLORIA - prog * (MAX_FATTORE_ETA_GLORIA - MIN_FATTORE_ETA_GLORIA)
        g_calc = (g_base * fatt_eta) + GLORIA_RICHIESTA_FISSA
        if getattr(self,'ambidestro',False): g_calc *= FATTORE_GLORIA_RICHIESTA_AMBIDESTRO
        if getattr(self,'giocorapido',False): g_calc *= FATTORE_GLORIA_RICHIESTA_GIOCO_RAPIDO
        if getattr(self,'cambiovelocita',False): g_calc *= FATTORE_GLORIA_RICHIESTA_CAMBIO_VEL
        g_fin = max(GLORIA_RICHIESTA_MINIMA_ASSOLUTA, int(g_calc))
        return min(g_fin, MAX_GLORIA_RICHIESTA)

    @property
    def eta_anni(self) -> float:
        return self.eta / ANNO_SIMULAZIONE_GIORNI if ANNO_SIMULAZIONE_GIORNI > 0 else 0.0

    def __str__(self) -> str:
        eta_vis = _formatta_eta_sim(self.eta, False); sex = "(Uomo)" if self.sesso=='m' else "(Donna)"; eta_sex = f"Età: {eta_vis} {sex}"
        stato = ["libero" if self.appartenenza=="*" else f"iscritto a {self.appartenenza}"]
        if self.ritirato: stato.append("ritirato")
        if self.infortunato: fine=f" (fino a {self.infortunio_fine_datetime:%Y-%m-%d %H:%M})" if self.infortunio_fine_datetime else " (N/D)"; stato.append("infortunato"+fine)
        flags_estesi = [nome_attr.replace('_', ' ').capitalize() for nome_attr, sigla in MAPPA_FLAG_SOMMARIO.items() if getattr(self, nome_attr, False)]
        if flags_estesi: stato.append(f"Flags: {', '.join(flags_estesi)}")
        stato_str = ", ".join(stato); compl = "Compleanno N/D"
        if ANNO_SIMULAZIONE_GIORNI > 0:
            gg_eta = self.eta; anni_c = gg_eta // ANNO_SIMULAZIONE_GIORNI; gg_dopo = gg_eta % ANNO_SIMULAZIONE_GIORNI
            gg_manc = (ANNO_SIMULAZIONE_GIORNI - gg_dopo) % ANNO_SIMULAZIONE_GIORNI; anni_prox = anni_c + 1
            if gg_dopo == 0 and gg_eta > 0: compl = f"Prossimo Compleanno (sim): tra {ANNO_SIMULAZIONE_GIORNI} giorni (compirà {anni_prox} anni sim)"
            elif gg_manc == 0 and gg_eta == 0: compl = f"Prossimo Compleanno (sim): tra {ANNO_SIMULAZIONE_GIORNI} giorni (compirà 1 anno sim)"
            else: compl = f"Prossimo Compleanno (sim): tra {gg_manc} giorni (compirà {anni_prox} anni sim)"
        out = [f"\n--- Scheda Giocatore ID: {self.id} ---", f"{self.nome} {self.cognome}", eta_sex, f"Stato: {stato_str}",
               f"Descrizione: {getattr(self, 'descrizione_fisica', '(N/D)')}",
               f"Scoperto (sim): {self.datetime_creazione_sim:%Y-%m-%d %H:%M}", f"Scoperto (reale): {self.datacreazione_reale:%Y-%m-%d %H:%M}",
               f"Versione Creazione: {self.versione}", f"{compl}", f"Altezza: {self.altezza} cm, Peso: {self.peso} kg",
               f"XP: {self.puntiesperienza}", f"ICV Tot: {self.indice_collettivo_valore:.2f} (B: {self.icv_base:.2f}, A: {self.icv_allenato:.2f})",
               f"Gloria Rich: {self.gloria_richiesta}"]
        def _stampa_c(nome_b, max_b): # max_b non è più usato qui, ma lasciato per compatibilità firma
             tot=self._get_valore_totale(nome_b); nome_d=NOME_ATTR_TO_DISPLAY_MAP.get(nome_b, nome_b.replace('_base','').replace('_',' ').title())
             # Determina se è fisica (PRC, RST, FOR) per limite totale
             is_f = nome_b in CARATTERISTICHE_FISICHE_BASE # <-- AGGIUNTO FORZA (in lista)
             max_t=MAX_TOTALE_PRECISIONE_RESISTENZA if is_f else MAX_TOTALE_SKILL_GIOCO
             perc=f"({(tot*100./max_t if max_t>0 else 0.):.0f}%)"; v_b=getattr(self,nome_b,0.); v_a=getattr(self,nome_b.replace('_base','_allenata'),0.)
             out.append(f"  - {nome_d:<25}: {v_b:5.2f} + {v_a:5.2f} = {tot:5.2f} {perc}")
        # La forza verrà stampata automaticamente qui perché in CARATTERISTICHE_FISICHE_BASE
        out.append("\nCaratteristiche Fisiche:"); [_stampa_c(nb, 0) for nb in CARATTERISTICHE_FISICHE_BASE]
        out.append("\nCaratteristiche Difensive:"); [_stampa_c(nb, 0) for nb in CARATTERISTICHE_DIFESA_BASE]
        out.append("\nCaratteristiche Offensive:"); [_stampa_c(nb, 0) for nb in CARATTERISTICHE_ATTACCO_BASE]
        out.append("\nPolivalenti:"); [_stampa_c(nb, 0) for nb in CARATTERISTICHE_CONTROLLO_BASE]
        out.append("\n--- Carriera e Palmarès ---"); pt = self.partitevinte + self.partiteperse; pv = f"({self.partitevinte*100./pt:.1f}%)" if pt else "(0%)"
        out.append(f"  Partite Giocate: {pt} (Vinte: {self.partitevinte} {pv})"); st = self.setsvinti + self.setspersi; sv = f"({self.setsvinti*100./st:.1f}%)" if st else "(0%)"
        out.append(f"  Sets Giocati: {st} (Vinti: {self.setsvinti} {sv})"); gf, gs = self.goalsfatti, self.goalssubiti; rapp_str = ""
        if gs > 0: rapp_str = f" (Rapp GF/GS: {(gf*100./gs):.1f}%)"
        elif gf > 0: rapp_str = " (Rapp GF/GS: Inf)"
        out.append(f"  Goals: Fatti={gf}, Subiti={gs}{rapp_str}"); oro = getattr(self,'ori',0); arg = getattr(self,'argenti',0); bro = getattr(self,'bronzi',0); leg = getattr(self,'legni',0)
        if oro>0 or arg>0 or bro>0 or leg>0: out.append(f"  Medaglie: Oro={oro}, Argento={arg}, Bronzo={bro}, Legno={leg}")
        else: out.append("  Medaglie: Nessuna")
        out.append("-" * 75); return "\n".join(out)

    def sommario(self) -> str:
        eta_vis = _formatta_eta_sim(self.eta, formato_breve=True); sesso = "(U)" if self.sesso == 'm' else "(D)"
        stato = "Ritirato" if self.ritirato else "Libero" if self.appartenenza == "*" else f"({self.appartenenza[:10]})"
        flags = "".join([f for a, f in MAPPA_FLAG_SOMMARIO.items() if getattr(self, a, False)]); flags_str = f" [{flags}]" if flags else ""
        xp = int(self.puntiesperienza or 0)
        return (f"ID:{self.id:<4d} {self.nome[:15]:<15} {self.cognome[:15]:<15} "
                f"{eta_vis:<8} {sesso} ICV:{self.indice_collettivo_valore:6.1f} XP:{xp:<5} {stato}{flags_str}")

    def aggiorna_icv(self):
        # La logica esistente funziona perché forza_base/forza_allenata sono nelle liste corrette
        self.icv_base = sum(getattr(self, attr, 0.0) for attr in ATTRIBUTI_BASE_CON_ALLENABILI)
        self.icv_allenato = sum(getattr(self, attr, 0.0) for attr in ATTRIBUTI_ALLENABILI)
        bonus = sum([33 for flag in ['ambidestro', 'giocorapido', 'cambiovelocita'] if getattr(self, flag, False)])
        self.indice_collettivo_valore = self.icv_base + self.icv_allenato + bonus

    def _genera_descrizione_fisica(self):
        try:
            frasi = {}; frasi['viso'] = random.choice(FRASI_VISI_M if self.sesso=='m' else FRASI_VISI_F)
            frasi['occhi'] = random.choice(FRASI_OCCHI_T).lower(); frasi['naso'] = random.choice(FRASI_NASI_T).lower(); frasi['bocca'] = random.choice(FRASI_BOCCA_T).lower()
            taglio = random.choice(FRASI_TAGLIO_CAPELLI_M if self.sesso=='m' else FRASI_TAGLIO_CAPELLI_F); colore = random.choice(FRASI_COLORI_CAPELLI_T).lower()
            desc_c = taglio.replace("[colore]", colore) if "[colore]" in taglio else f"{taglio} {colore}"; frasi['capelli'] = desc_c.lower()
            desc = INIZIO_FRASE_DESC + frasi.get('viso','') + CONN_VISO_OCCHI_DESC + frasi.get('occhi','') + CONN_OCCHI_NASO_DESC + frasi.get('naso','') + \
                   CONN_NASO_BOCCA_DESC + frasi.get('bocca','') + CONN_BOCCA_CAPELLI_DESC + frasi.get('capelli','') + SEPARATORE_FINALE_DESC
            if desc and not INIZIO_FRASE_DESC: desc = desc[0].upper() + desc[1:]
            self.descrizione_fisica = desc.strip()
        except Exception as e: print(f"WARN GID {self.id}: Err gen desc: {e}"); self.descrizione_fisica = "(N/D)"

    def _assegna_archetipo_iniziale(self):
        sugg = self._determina_archetipo_da_base()
        if sugg and sugg in ARCHETIPI_ALLENAMENTO and not caso(PROB_ARCHETIPO_CASUALE_CREAZIONE): self.archetipo_allenamento = sugg
        else: validi = list(ARCHETIPI_ALLENAMENTO.keys()); self.archetipo_allenamento = random.choice(validi) if validi else "TuttofareBilanciato"

    def _determina_archetipo_da_base(self) -> Optional[str]:
        try:
            # CARATTERISTICHE_FISICHE_BASE ora include forza_base
            stats={'fis':CARATTERISTICHE_FISICHE_BASE,'att':CARATTERISTICHE_ATTACCO_BASE,'dif':CARATTERISTICHE_DIFESA_BASE,'ctrl':CARATTERISTICHE_CONTROLLO_BASE,'bloc':['bloccosx_base','bloccodx_base'],'batt':['battutasx_base','battutadx_base']}
            medie={k: sum(getattr(self,s,0.) for s in v)/len(v) if v else 0. for k,v in stats.items()}
            # La logica dei pesi non usava esplicitamente la forza, quindi rimane invariata
            pesi={"MuroFisico":medie['fis']*2.5,"AttaccantePuro":medie['att'],"DifensoreRoccioso":medie['dif'],"SpecialistaBlocchiDifesa":medie['bloc']*1.5+medie['dif']*.5,"SpecialistaBlocchiAttacco":medie['bloc']*1.5+medie['att']*.5,"SpecialistaBlocchiControllo":medie['bloc']*1.5+medie['ctrl']*.5,"SpecialistaBattutaBlocco":medie['batt']*1.5+medie['bloc']*.5,"CecchinoPreciso":medie['ctrl']}
            soglia=5.; validi={k:v for k,v in pesi.items() if v>=soglia}
            if not validi: return None
            sugg=max(validi, key=validi.get)
            if medie['dif']>8. and medie['bloc']>8.: sugg="SpecialistaBlocchiDifesa"
            return sugg if sugg in ARCHETIPI_ALLENAMENTO else None
        except Exception as e: print(f"ERR det_arch GID {self.id}: {e}"); return None

    def _applica_declino_aggregato(self, giorni_passati: int):
        # La logica esistente funziona perché forza_base/forza_allenata sono in ATTRIBUTI_INVECCHIABILI
        if giorni_passati <= 0 or self.eta < AGING_START_AGE_GIORNI or ANNO_SIMULAZIONE_GIORNI <= 0: return
        prog_eta = max(0, self.eta - AGING_START_AGE_GIORNI); range_decl = max(1, AGING_PEAK_AGE_GIORNI - AGING_START_AGE_GIORNI)
        aging_f = min(1.0, prog_eta / range_decl); reduc_ann = aging_f * MAX_AGING_REDUCTION_FACTOR_PER_ANNO_SIM
        manten_ann = max(0.0, 1.0 - reduc_ann)
        try: manten_giorn = pow(manten_ann, 1.0 / ANNO_SIMULAZIONE_GIORNI)
        except ValueError: manten_giorn = 0.0
        manten_tot = pow(manten_giorn, giorni_passati)
        for attr in ATTRIBUTI_INVECCHIABILI: val = getattr(self, attr, 0.0); setattr(self, attr, max(0.0, val * manten_tot))

class Polisportiva:
    # Nessuna modifica necessaria in Polisportiva per la forza del giocatore
    def __init__(self, nome: str, password: Optional[str], datetime_creazione_sim: datetime.datetime, is_cpu_controlled: bool = False):
        self.nome: str = nome.title(); self.password: Optional[str] = password if not is_cpu_controlled else None
        self.datetime_creazione_sim: datetime.datetime = datetime_creazione_sim; self.is_cpu_controlled: bool = is_cpu_controlled
        self.tesserati: List[int] = []; self.indicecollettivotesserati: float = 0.0
        self.ori=0; self.argenti=0; self.bronzi=0; self.legni=0; self.coppe_oro=0; self.coppe_argento=0; self.coppe_bronzo=0; self.coppe_legno=0
        self.maxtesserati: int = MAX_TESSERATI_POLISPORTIVA; self.gloria: int = 100
        self.datetime_ultimo_movimento: datetime.datetime = datetime.datetime(1900, 1, 1); self.movimenti_oggi: int = 0
        self.datacreazione_reale = datetime.datetime.now()
        self.versione_creazione = VERSIONE

    def __str__(self) -> str:
        dt_creaz_sim_str = f"{self.datetime_creazione_sim:%Y-%m-%d %H:%M}" if isinstance(self.datetime_creazione_sim, datetime.datetime) else "N/D"
        dt_creaz_real_str = getattr(self, 'datacreazione_reale', '?').strftime('%Y-%m-%d %H:%M') if isinstance(getattr(self, 'datacreazione_reale', None), datetime.datetime) else "N/D"
        versione_creaz = getattr(self, 'versione_creazione', 'N/D')
        num_tesserati = len(self.tesserati); ic_medio_str = f"{(self.indicecollettivotesserati / num_tesserati):.2f}" if num_tesserati > 0 else "0.00"
        cpu = " [CPU]" if self.is_cpu_controlled else ""; mov_rimasti = LIMITE_MOVIMENTI_PER_TICK - self.movimenti_oggi
        eta_poli_str = "(Vedi Sommario/Statistiche per Età)"
        out = [f"\n--- Scheda Polisportiva: {self.nome}{cpu} ---", f"Fondata: (Reale: {dt_creaz_real_str}, Sim: {dt_creaz_sim_str}, Versione: {versione_creaz})",
               f"Tesserati: {num_tesserati}/{self.maxtesserati}, ICT: {self.indicecollettivotesserati:.2f}, IC Medio: {ic_medio_str}",
               f"Gloria: {self.gloria}, Movimenti Oggi Rimanenti: {mov_rimasti}/{LIMITE_MOVIMENTI_PER_TICK}",
               "\n--- Palmarès e Attività ---", f"Età Polisportiva (Sim): {eta_poli_str}", "Coppe (Squadra):",
               f"  Oro={self.coppe_oro}, Argento={self.coppe_argento}, Bronzo={self.coppe_bronzo}, Legno={self.coppe_legno}",
               "Medaglie (Individuali Tesserati):", f"  Oro={self.ori}, Argento={self.argenti}, Bronzo={self.bronzi}, Legno={self.legni}"]
        return "\n".join(out)

    def sommario(self, data_corrente_sim: Optional[datetime.datetime] = None) -> str:
        eta_str = "Età N/D"
        if data_corrente_sim and isinstance(self.datetime_creazione_sim, datetime.datetime):
            try: eta_str = _formatta_eta_sim(int((data_corrente_sim - self.datetime_creazione_sim).total_seconds()/(24*3600)), True)+" sim"
            except: eta_str = "Errore Età"
        cpu = " [CPU]" if self.is_cpu_controlled else ""
        return (f"{self.nome:<30} {len(self.tesserati):2d}/{self.maxtesserati} atl. ICT:{self.indicecollettivotesserati:7.1f} ({eta_str}) {cpu}")

    def aggiorna_ict(self, giocatori: Dict[int, Giocatore], ids_morti: Set[int]):
        self.indicecollettivotesserati = sum(g.indice_collettivo_valore for gid, g in giocatori.items() if gid in self.tesserati and gid not in ids_morti)

    def aggiungi_tesserato(self, gid: int, icv: float):
        if gid not in self.tesserati: self.tesserati.append(gid); self.indicecollettivotesserati += icv

    def rimuovi_tesserato(self, gid: int, icv: float):
        if gid in self.tesserati:
            try: self.tesserati.remove(gid); self.indicecollettivotesserati = max(0., self.indicecollettivotesserati - icv)
            except ValueError: pass

    def _chiudi_polisportiva_cpu(self, nome_p: str, dt_chiusura: datetime.datetime, sim: 'Simulatore'):
        poli = sim.polisportive.get(nome_p)
        if not poli or not poli.is_cpu_controlled: return False
        eta_str = "Età N/D"
        try: eta_str = _formatta_eta_sim(int((dt_chiusura - poli.datetime_creazione_sim).total_seconds()/(24*3600)))
        except: pass
        print(f"** Evento ({dt_chiusura:%Y-%m-%d %H:%M}): Chiusura Poli CPU '{nome_p}' (Età: {eta_str}, G:{poli.gloria}, T:{len(poli.tesserati)}) **")
        n_lib = 0
        for gid in list(poli.tesserati):
            if gid in sim.giocatori: sim.giocatori[gid].appartenenza = "*"; n_lib+=1
            try: poli.tesserati.remove(gid)
            except: pass
        del sim.polisportive[nome_p]; print(f" --> Chiusa. {n_lib} liberati."); return True

    def _controlla_chiusura_poli_cpu(self, dt_corr: datetime.datetime, sim: 'Simulatore'):
        if not isinstance(self.datetime_creazione_sim, datetime.datetime) or ANNO_SIMULAZIONE_GIORNI <= 0: return False
        try: anni_sim = (dt_corr - self.datetime_creazione_sim).total_seconds() / (24*3600) / ANNO_SIMULAZIONE_GIORNI
        except: return False
        if anni_sim < ETA_MINIMA_CHIUSURA_CPU_ANNI: return False
        g_bassa = self.gloria < SOGLIA_GLORIA_BASSA_CHIUSURA; p_tess = len(self.tesserati) < SOGLIA_MINIMA_TESSERATI_CHIUSURA
        if not (g_bassa or p_tess): return False
        prob = PROB_CHIUSURA_BASE_GIORNALIERA
        if g_bassa: norm = SOGLIA_GLORIA_BASSA_CHIUSURA or 1; prob += max(0.,norm-self.gloria)/norm * FATTORE_PROB_GLORIA
        if p_tess: norm = SOGLIA_MINIMA_TESSERATI_CHIUSURA or 1; prob += max(0.,norm-len(self.tesserati))/norm * FATTORE_PROB_TESSERATI
        if caso(min(prob, MAX_PROB_CHIUSURA_GIORNALIERA)): return self._chiudi_polisportiva_cpu(self.nome, dt_corr, sim)
        return False

    def aggiorna_gloria(self, giocatori: Dict[int, Giocatore], ids_morti: Set[int]):
        BASE=60.; C_O=100; C_A=50; C_B=20; C_L=5; M_O=30; M_A=15; M_B=5; M_L=1; K_C=12.; K_M=8.; K_ICV=0.4; ETA_REF=35.; K_ETA=1.5; K_NUM=15.
        p_c = self.coppe_oro*C_O + self.coppe_argento*C_A + self.coppe_bronzo*C_B + self.coppe_legno*C_L; v_c = math.sqrt(max(0.,p_c))*K_C
        p_m = self.ori*M_O + self.argenti*M_A + self.bronzi*M_B + self.legni*M_L; v_m = math.sqrt(max(0.,p_m))*K_M
        v_icv=0.; v_eta=0.; v_num=0.; n_val=0; eta_gg=0; icv_tot=0.
        for gid in self.tesserati:
            if gid in giocatori and gid not in ids_morti and not giocatori[gid].ritirato: n_val+=1; eta_gg+=giocatori[gid].eta; icv_tot+=giocatori[gid].indice_collettivo_valore
        if n_val > 0 and ANNO_SIMULAZIONE_GIORNI > 0:
            icv_m = icv_tot/n_val; eta_m_a = (eta_gg/n_val/ANNO_SIMULAZIONE_GIORNI)
            v_icv = icv_m*K_ICV; v_eta = max(0., ETA_REF-eta_m_a)*K_ETA
        if self.maxtesserati > 0: v_num = (len(self.tesserati)/self.maxtesserati)*K_NUM
        self.gloria = max(1, int(BASE + v_c + v_m + v_icv + v_eta + v_num))

class Simulatore:
    def __init__(self):
        self.start_time = time.time(); self.comandi_eseguiti = 0
        self.giocatori: Dict[int, Giocatore] = {}; self.polisportive: Dict[str, Polisportiva] = {}
        self.miapolisportiva_attiva: Optional[Polisportiva] = None
        self.datetime_ultimo_run_reale: datetime.datetime = datetime.datetime.now() - datetime.timedelta(days=1)
        self.datetime_corrente_simulazione: datetime.datetime = datetime.datetime.now()
        self.nuovi_giocatori_sessione: List[int] = []; self.giocatori_ritirati_sessione: List[Tuple[int, str]] = []
        self.giocatori_morti_sessione: List[Tuple[int, str]] = []; self._ids_morti_processati_sessione: Set[int] = set()
        self.risultati_ultima_ricerca: List[int] = []
        self._carica_dati(); self._processa_tempo_trascorso()

# All'interno della classe Simulatore

    def visualizza_scheda_giocatore(self):
        """Mostra la scheda dettagliata di un giocatore specifico."""
        try:
            gid = int(dgt("ID giocatore? ", "i", imin=1)) # Chiede ID
            if gid in self.giocatori: # Controlla se ID esiste
                g = self.giocatori[gid]
                if gid in self._ids_morti_processati_sessione:
                    print(f"\nATT: Giocatore {gid} ({g.nome}) deceduto (verrà rimosso al salvataggio).")
                print(g)
            else:
                print(f"\n\tID {gid} non trovato.")
        except (ValueError, TypeError):
            print("\n\tID non valido.")
        except EOFError:
            print("\nAnnullato.")

    def _carica_dati(self):
        print("\n--- Caricamento Dati ---"); stato_ok, gioc_ok, poli_ok = False, False, False
        dt_sim_per_creazione = datetime.datetime.now()
        try: # Stato
            with open(DB_STATO_GIOCO, "rb") as f: stato = pickle.load(f)
            dt_sim, dt_run = stato.get('datetime_corrente_simulazione'), stato.get('datetime_ultimo_run_reale')
            if isinstance(dt_sim,datetime.date) and not isinstance(dt_sim,datetime.datetime): dt_sim = datetime.datetime.combine(dt_sim,datetime.time.min)
            if isinstance(dt_run,datetime.date) and not isinstance(dt_run,datetime.datetime): dt_run = datetime.datetime.combine(dt_run,datetime.time.min)
            if isinstance(dt_sim,datetime.datetime) and isinstance(dt_run,datetime.datetime):
                if dt_sim < dt_run: print("*"*75 + "\nATTENZIONE: INCOERENZA TEMPORALE CARICATA!\n"+ f"  Data Sim ({dt_sim:%Y-%m-%d %H:%M}) < Ultimo Run ({dt_run:%Y-%m-%d %H:%M})\n"+"  Proseguo con date caricate.\n" + "*"*75)
                self.datetime_corrente_simulazione, self.datetime_ultimo_run_reale = dt_sim, dt_run
                dt_sim_per_creazione = self.datetime_corrente_simulazione; stato_ok = True
                print(f"Stato caricato. Sim: {self.datetime_corrente_simulazione:%Y-%m-%d %H:%M}, Ult Run: {self.datetime_ultimo_run_reale:%Y-%m-%d %H:%M}.")
            else: print("WARN: Dati tempo stato non validi.")
        except FileNotFoundError: print(f"File stato '{DB_STATO_GIOCO}' non trovato.")
        except Exception as e: print(f"ERR caricamento stato: {e}"); traceback.print_exc()
        if not stato_ok:
             self.datetime_corrente_simulazione = dt_sim_per_creazione
             self.datetime_ultimo_run_reale = dt_sim_per_creazione - datetime.timedelta(hours=8)
             print(f"Nuovo stato inizializzato. Data/Ora Sim: {self.datetime_corrente_simulazione:%Y-%m-%d %H:%M}")
        try: # Giocatori
            with open(DB_GIOCATORI, "rb") as f: giocatori_caricati_raw = pickle.load(f)
            self.giocatori = {gid: g for gid, g in giocatori_caricati_raw.items() if gid is not None and isinstance(gid, int)}
            num_filtrati = len(giocatori_caricati_raw) - len(self.giocatori)
            if num_filtrati > 0: print(f"WARN: Filtrate {num_filtrati} voci ID non valido da '{DB_GIOCATORI}'.")
            print(f"Caricati {len(self.giocatori)} giocatori validi."); gioc_ok = True
            if self.giocatori:
                for g in self.giocatori.values():
                    # Fix tipi e aggiungi attributi mancanti (incluso forza)
                    if hasattr(g,'datacreazione') and isinstance(g.datacreazione,datetime.date): g.datetime_creazione_sim = datetime.datetime.combine(g.datacreazione,datetime.time.min)
                    if not hasattr(g,'datetime_creazione_sim') or not isinstance(g.datetime_creazione_sim,datetime.datetime): g.datetime_creazione_sim=self.datetime_corrente_simulazione
                    if not hasattr(g,'datacreazione_reale') or not isinstance(g.datacreazione_reale,datetime.datetime): g.datacreazione_reale=g.datetime_creazione_sim
                    if hasattr(g,'infortunio_fine_data') and isinstance(g.infortunio_fine_data,datetime.date): g.infortunio_fine_datetime = datetime.datetime.combine(g.infortunio_fine_data,datetime.time.min)
                    if hasattr(g,'infortunio_fine_datetime') and not isinstance(g.infortunio_fine_datetime,datetime.datetime): g.infortunio_fine_datetime=None
                    if not hasattr(g,'archetipo_allenamento'): g.archetipo_allenamento="Non Definito"
                    if not hasattr(g,'descrizione_fisica'): setattr(g, 'descrizione_fisica', '')
                    if not hasattr(g,'ori'): setattr(g, 'ori', 0); setattr(g, 'argenti', 0); setattr(g, 'bronzi', 0); setattr(g, 'legni', 0)
                    # <-- AGGIUNTO FORZA - Fallback caricamento
                    if not hasattr(g, 'forza_base'): setattr(g, 'forza_base', 0.0)
                    if not hasattr(g, 'forza_allenata'): setattr(g, 'forza_allenata', 0.0)

        except FileNotFoundError: print(f"File giocatori '{DB_GIOCATORI}' non trovato.")
        except Exception as e: print(f"ERR caricamento giocatori: {e}"); traceback.print_exc()
        if not gioc_ok:
             print(f"\nPopolamento iniziale con {NUM_GIOCATORI_INIZIALI} giocatori...")
             self.nuovi_giocatori_sessione.clear()
             self._crea_giocatori_casuali(NUM_GIOCATORI_INIZIALI, dt_sim_per_creazione)
             print("Popolamento completato.")
             self.nuovi_giocatori_sessione.clear()
        try: # Polisportive
            with open(DB_POLISPORTIVE, "rb") as f: self.polisportive = pickle.load(f); nome_att = pickle.load(f)
            if not isinstance(self.polisportive, dict): raise ValueError("Formato file polisportive non valido")
            print(f"Caricate {len(self.polisportive)} polisportive."); poli_ok = True
            for p in self.polisportive.values():
                nome_p = getattr(p, 'nome', '?')
                if hasattr(p,'datacreazione') and isinstance(p.datacreazione,datetime.date): p.datetime_creazione_sim=datetime.datetime.combine(p.datacreazione,datetime.time.min)
                if not hasattr(p,'datetime_creazione_sim') or not isinstance(p.datetime_creazione_sim,datetime.datetime): print(f"WARN: Fix dt_creaz_sim Poli '{nome_p}'."); p.datetime_creazione_sim=self.datetime_corrente_simulazione
                if hasattr(p,'data_ultimo_movimento'):
                     if isinstance(p.data_ultimo_movimento,datetime.date): p.datetime_ultimo_movimento=datetime.datetime.combine(p.data_ultimo_movimento,datetime.time.min)
                     elif isinstance(p.data_ultimo_movimento,datetime.datetime): p.datetime_ultimo_movimento=p.data_ultimo_movimento
                if not hasattr(p,'datetime_ultimo_movimento') or not isinstance(p.datetime_ultimo_movimento,datetime.datetime): p.datetime_ultimo_movimento=datetime.datetime(1900,1,1)
                if not hasattr(p,'movimenti_oggi'): p.movimenti_oggi=0
                if not hasattr(p,'datacreazione_reale') or not isinstance(getattr(p,'datacreazione_reale',None),datetime.datetime): print(f"WARN: Fix dt_creaz_real Poli '{nome_p}'."); setattr(p,'datacreazione_reale',p.datetime_creazione_sim)
                if not hasattr(p,'versione_creazione') or not isinstance(getattr(p,'versione_creazione',None),str): print(f"WARN: Fix vers_creaz Poli '{nome_p}'."); setattr(p,'versione_creazione','N/D')
                if not hasattr(p,'ori'): setattr(p,'ori',0); setattr(p,'argenti',0); setattr(p,'bronzi',0); setattr(p,'legni',0)
                if not hasattr(p,'coppe_oro'): setattr(p,'coppe_oro',0); setattr(p,'coppe_argento',0); setattr(p,'coppe_bronzo',0); setattr(p,'coppe_legno',0)

            if nome_att != "Nessuna" and nome_att in self.polisportive: self.miapolisportiva_attiva=self.polisportive[nome_att]; print(f"Poli attiva: {nome_att}")
            else: self.miapolisportiva_attiva=None; print("Nessuna poli attiva.")
        except FileNotFoundError: print(f"File polisportive '{DB_POLISPORTIVE}' non trovato.")
        except EOFError: print(f"File polisportive '{DB_POLISPORTIVE}' incompleto."); self.polisportive=getattr(self,'polisportive',{})
        except Exception as e: print(f"ERR caricamento polisportive: {e}"); traceback.print_exc(); self.polisportive={}
        print("--- Fine Caricamento ---")

    def salva_dati(self):
        """Salva lo stato completo del gioco (giocatori, polisportive, stato)."""
        print("\nSalvataggio databases...")
        start_save_time = time.time()
        successo = True

        try:
            # 1. Salva Giocatori
            giocatori_da_salvare = {gid: g for gid, g in self.giocatori.items() if gid not in self._ids_morti_processati_sessione}
            n_rimossi = len(self.giocatori) - len(giocatori_da_salvare)
            if n_rimossi: print(f"  (Rimuovendo {n_rimossi} giocatori morti/usciti)")
            with open(DB_GIOCATORI, "wb") as f: pickle.dump(giocatori_da_salvare, f, pickle.HIGHEST_PROTOCOL)
            print(f" -> {len(giocatori_da_salvare)} giocatori salvati in '{DB_GIOCATORI}'.")
            # 2. Salva Polisportive
            with open(DB_POLISPORTIVE, "wb") as f:
                pickle.dump(self.polisportive, f, pickle.HIGHEST_PROTOCOL)
                nome_attiva = self.miapolisportiva_attiva.nome if self.miapolisportiva_attiva else "Nessuna"
                pickle.dump(nome_attiva, f, pickle.HIGHEST_PROTOCOL)
            print(f" -> {len(self.polisportive)} polisportive salvate in '{DB_POLISPORTIVE}'.")
            # 3. Salva Stato Gioco
            stato = {'datetime_corrente_simulazione': self.datetime_corrente_simulazione,'datetime_ultimo_run_reale': self.datetime_ultimo_run_reale}
            with open(DB_STATO_GIOCO, "wb") as f: pickle.dump(stato, f, pickle.HIGHEST_PROTOCOL)
            print(f" -> Stato gioco salvato in '{DB_STATO_GIOCO}'.")
        except Exception: print("\nERRORE FATALE salvataggio:"); traceback.print_exc(); successo = False
        finally:
            end_save_time = time.time(); tempo_impiegato = end_save_time - start_save_time
            if successo: print(f"Salvataggio completato ({tempo_impiegato:.5f}s).")
            else: print(f"Salvataggio fallito ({tempo_impiegato:.5f}s).")

    def _logga_uscita_giocatore(self, giocatore: Giocatore, motivo: str, dt_evento_sim: datetime.datetime):
        """Scrive l'uscita di un giocatore nel file di log storico 'vecchie_glorie.log'."""
        try:
            eta_mom = _formatta_eta_sim(giocatore.eta, False); dt_crea_s = giocatore.datetime_creazione_sim.strftime('%Y-%m-%d %H:%M')
            dt_crea_r = giocatore.datacreazione_reale.strftime('%Y-%m-%d %H:%M'); dt_evt_s = dt_evento_sim.strftime('%Y-%m-%d %H:%M')
            dt_evt_r = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            flags = ", ".join([f for a, f in MAPPA_FLAG_SOMMARIO.items() if getattr(giocatore, a, False)]) or "Nessuno"
            log = [f"--- {motivo.upper()} - GID: {giocatore.id} ---", f"Nome: {giocatore.nome} {giocatore.cognome}", f"Età (Sim): {eta_mom}",
                   f"Sesso: {'Uomo' if giocatore.sesso == 'm' else 'Donna'}", f"Club Finale: {'Libero' if giocatore.appartenenza == '*' else giocatore.appartenenza}",
                   f"Fisico: {giocatore.altezza} cm / {giocatore.peso} kg", f"Flags: {flags}", f"Scoperto (Sim): {dt_crea_s}", f"Scoperto (Reale): {dt_crea_r}",
                   f"Versione Creazione: {getattr(giocatore, 'versione', 'N/D')}", f"Evento (Sim): {dt_evt_s}", f"Evento (Reale): {dt_evt_r}",
                   f"Stats Partite: G={giocatore.partitevinte+giocatore.partiteperse}, V={giocatore.partitevinte}",
                   f"Stats Sets: G={giocatore.setsvinti+giocatore.setspersi}, V={giocatore.setsvinti}",
                   f"Stats Goals: F={giocatore.goalsfatti}, S={giocatore.goalssubiti}", f"XP Finali: {int(giocatore.puntiesperienza or 0)}",
                   f"ICV Finale: {giocatore.indice_collettivo_valore:.2f}", "-" * 50 + "\n"]
            with open(NOME_FILE_LOG_USCITE, "a", encoding="utf-8") as f: f.write("\n".join(log))
        except Exception as e: print(f"ERR scrittura log uscita GID {giocatore.id}: {e}")

    def _calcola_prob_infortunio(self, giocatore: Giocatore) -> float:
        """Calcola probabilità % infortunio post-partita."""
        prob_base = PROB_INFORTUNIO_BASE_PER_PARTITA; prob_aum_eta = 0.0; eta_a = giocatore.eta_anni
        if eta_a > ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI:
            eta_calc = min(eta_a, ETA_MAX_PROB_INFORTUNIO_ANNI); range_eta = max(1.0, ETA_MAX_PROB_INFORTUNIO_ANNI - ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI)
            prog = (eta_calc - ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI) / range_eta; prob_aum_eta = prog * PROB_INFORTUNIO_AUMENTO_MAX_PERC
        prob_calc = prob_base + prob_aum_eta; prob_fin = prob_calc
        if getattr(giocatore, 'ambidestro', False): prob_fin = prob_calc * 0.20
        return max(0.0, min(prob_fin, 95.0))

    def _calcola_durata_infortunio(self, giocatore: Giocatore) -> int:
        """Calcola durata casuale infortunio (giorni sim)."""
        if ANNO_SIMULAZIONE_GIORNI <= 0: return random.randint(3, 20)
        dur_base_cas = INFORTUNIO_DURATA_MIN_GIORNI; eta_min_s,eta_max_s=0,max(1,AGING_PEAK_AGE_GIORNI); range_eta=eta_max_s-eta_min_s
        eta_norm = max(0., min(1., (giocatore.eta-eta_min_s)/range_eta)) if range_eta>0 else 0.
        min_d, max_d = INFORTUNIO_DURATA_MIN_GIORNI, INFORTUNIO_DURATA_MAX_GIORNI_ETA; prob_l = eta_norm**1.5
        if random.random() < prob_l:
            medio=(min_d+max_d)/2.; lim_i=min(math.ceil(medio),max_d); dur_base_cas=random.randint(lim_i,max_d) if lim_i<=max_d else max_d
        else:
            medio=(min_d+max_d)/2.; lim_s=max(math.floor(medio),min_d); dur_base_cas=random.randint(min_d,lim_s) if min_d<=lim_s else min_d
        dur_mod=float(dur_base_cas); malus_r=0.
        try:
            # <-- AGGIUNTO FORZA - Resistenza rimane la skill rilevante per il malus durata
            res_t=giocatore._get_valore_totale('resistenza_base'); res_n=max(0.,min(res_t,MAX_TOTALE_PRECISIONE_RESISTENZA))
            if MAX_TOTALE_PRECISIONE_RESISTENZA>0: res_manc=1.-(res_n/MAX_TOTALE_PRECISIONE_RESISTENZA); malus_r=res_manc*INFORTUNIO_MALUS_MAX_RESISTENZA
            dur_mod+=malus_r
        except Exception as e: print(f"WARN: Err calc malus res GID {giocatore.id}: {e}")
        if getattr(giocatore,'ambidestro',False): dur_mod*=0.20
        return max(INFORTUNIO_DURATA_MIN_GIORNI, int(round(dur_mod)))

    # --- METODI PARTITA ---
    def gioca_partita(self, id_g1: int, id_g2: int, num_set_target: int,
                      modalita_output: str = MODALITA_OUTPUT_RISULTATO,
                      info_torneo: Optional[dict] = None) -> dict:
        """Simula una partita completa tra due giocatori."""
        print(f"\n--- Inizio Partita: ID {id_g1} vs ID {id_g2} (Al meglio dei {num_set_target} set) ---")
        risultato_partita = {
            'id_originale_g1': id_g1, 'id_originale_g2': id_g2, 'num_set_target': num_set_target,
            'vincitore_id': None, 'perdente_id': None, 'punteggio_set': [],
            'stats_g1': {'goal': 0, 'falli_fatti': 0, 'falli_subiti': 0},
            'stats_g2': {'goal': 0, 'falli_fatti': 0, 'falli_subiti': 0},
            'log_partita_completa': [], 'log_path': None, 'error': None
        }
        log_partita = risultato_partita['log_partita_completa']

        if id_g1 not in self.giocatori or id_g2 not in self.giocatori:
            risultato_partita['error'] = "ID giocatore non valido."; print(f"ERRORE: {risultato_partita['error']}"); return risultato_partita
        if id_g1 == id_g2:
            risultato_partita['error'] = "I giocatori devono essere diversi."; print(f"ERRORE: {risultato_partita['error']}"); return risultato_partita
        g1 = self.giocatori[id_g1]; g2 = self.giocatori[id_g2]
        if g1.ritirato or g2.ritirato:
             risultato_partita['error'] = "Uno o entrambi ritirati."; print(f"ERRORE: {risultato_partita['error']}"); return risultato_partita
        if g1.infortunato or g2.infortunato:
             risultato_partita['error'] = "Uno o entrambi infortunati."; print(f"ERRORE: {risultato_partita['error']}"); return risultato_partita

        set_vinti_g1, set_vinti_g2 = 0, 0
        set_da_vincere = math.ceil(num_set_target / 2.0)
        servizio_attuale_id = random.choice([id_g1, id_g2])
        file_log = None
        if modalita_output == MODALITA_OUTPUT_FILE:
            try:
                filepath = os.path.join(os.getcwd(), NOME_FILE_LOG_PARTITE)
                file_log = open(filepath, "a", encoding="utf-8")
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                header = f"\n=== PARTITA INIZIATA: {timestamp} ===\n"
                header += f"  {g1.nome} {g1.cognome} (ID:{id_g1}) vs {g2.nome} {g2.cognome} (ID:{id_g2})\n"
                header += f"  Al meglio dei {num_set_target} set\n" + "="*30 + "\n"
                file_log.write(header); risultato_partita['log_path'] = filepath
            except Exception as e: print(f"ERRORE apertura file log '{NOME_FILE_LOG_PARTITE}': {e}"); modalita_output = MODALITA_OUTPUT_RISULTATO

        numero_set_attuale = 1
        try:
            while set_vinti_g1 < set_da_vincere and set_vinti_g2 < set_da_vincere:
                if modalita_output != MODALITA_OUTPUT_RISULTATO:
                     log_partita.append(f"\n-- Set {numero_set_attuale} -- (Servizio: ID {servizio_attuale_id})")
                if modalita_output == MODALITA_OUTPUT_CONSOLE:
                    print(f"\n-- Inizio Set {numero_set_attuale} -- (Servizio: ID {servizio_attuale_id})")

                punteggio_set, vincitore_set_id = self._gioca_set(g1, g2, servizio_attuale_id, risultato_partita['stats_g1'],
                                                                  risultato_partita['stats_g2'], log_partita, modalita_output, numero_set_attuale)

                risultato_partita['punteggio_set'].append(punteggio_set)
                if vincitore_set_id == id_g1: set_vinti_g1 += 1
                elif vincitore_set_id == id_g2: set_vinti_g2 += 1

                if modalita_output != MODALITA_OUTPUT_RISULTATO:
                     log_partita.append(f"-- Fine Set {numero_set_attuale}: {punteggio_set[0]}-{punteggio_set[1]} (Vincitore: ID {vincitore_set_id}) --")
                     log_partita.append(f"Parziale Partita: {set_vinti_g1} - {set_vinti_g2}\n")
                if modalita_output == MODALITA_OUTPUT_CONSOLE:
                     print(f"-- Fine Set {numero_set_attuale}: {punteggio_set[0]}-{punteggio_set[1]} (Vincitore Set: ID {vincitore_set_id}) --")
                     print(f"Partita: {set_vinti_g1} - {set_vinti_g2}")

                servizio_attuale_id = id_g2 if servizio_attuale_id == id_g1 else id_g1
                numero_set_attuale += 1
        except (EOFError, KeyboardInterrupt):
             risultato_partita['error'] = "Partita interrotta dall'utente."; print(f"\n{risultato_partita['error']}")

        if risultato_partita['error'] is None:
            if set_vinti_g1 > set_vinti_g2: risultato_partita['vincitore_id'] = id_g1; risultato_partita['perdente_id'] = id_g2
            else: risultato_partita['vincitore_id'] = id_g2; risultato_partita['perdente_id'] = id_g1
            vincitore = self.giocatori.get(risultato_partita['vincitore_id']); perdente = self.giocatori.get(risultato_partita['perdente_id'])
            if vincitore and perdente:
                print("\n=== PARTITA TERMINATA ==="); print(f"Vincitore: {vincitore.nome} {vincitore.cognome} (ID:{vincitore.id})")
                print(f"Punteggio Finale: {set_vinti_g1} - {set_vinti_g2}"); print(f"Set: {risultato_partita['punteggio_set']}")
                self._aggiorna_statistiche_post_partita(risultato_partita, info_torneo) # Include controllo infortuni
            else: risultato_partita['error'] = "Errore recupero vincitore/perdente finale."; print(f"ERRORE: {risultato_partita['error']}")

        if file_log:
            try:
                footer = f"\n=== PARTITA { 'TERMINATA' if risultato_partita['error'] is None else 'INTERROTTA' } ===\n"
                if risultato_partita.get('vincitore_id'):
                     v_id = risultato_partita['vincitore_id']; v_nome = self.giocatori[v_id].nome + " " + self.giocatori[v_id].cognome
                     footer += f"Vincitore: ID {v_id} ({v_nome})\n"; footer += f"Punteggio: {set_vinti_g1} - {set_vinti_g2}\n"
                footer += f"Set: {risultato_partita.get('punteggio_set', [])}\n"
                id_orig_g1 = risultato_partita['id_originale_g1']; id_orig_g2 = risultato_partita['id_originale_g2']
                stats1 = risultato_partita['stats_g1']; stats2 = risultato_partita['stats_g2']
                footer += f"Stats G1 (ID:{id_orig_g1}): Goal={stats1.get('goal',0)}, Falli Fatti={stats1.get('falli_fatti',0)}, Falli Subiti={stats1.get('falli_subiti',0)}\n"
                footer += f"Stats G2 (ID:{id_orig_g2}): Goal={stats2.get('goal',0)}, Falli Fatti={stats2.get('falli_fatti',0)}, Falli Subiti={stats2.get('falli_subiti',0)}\n"
                if risultato_partita['error']: footer += f"Esito: {risultato_partita['error']}\n"
                footer += "="*30 + "\n"; log_completo = "\n".join(log_partita) + footer; file_log.write(log_completo); file_log.close()
                if risultato_partita['error'] is None: print(f"Cronaca completa salvata in: {risultato_partita['log_path']}")
            except Exception as e: print(f"ERRORE scrittura file log finale: {e}")
            finally:
                 if file_log and not file_log.closed: file_log.close()

        return risultato_partita

    def _gioca_set(self, g1: Giocatore, g2: Giocatore, id_servizio_inizio: int,
                   stats_g1: dict, stats_g2: dict,
                   log_partita: list, modalita_output: str,
                   numero_set_attuale: int) -> tuple[tuple[int, int], int]:
        """Simula un singolo set."""
        punti_g1, punti_g2 = 0, 0
        servizio_corrente_id = id_servizio_inizio
        servizi_giocati_da_attuale = 0
        res_perc_g1 = self._calcola_resistenza_set(g1, numero_set_attuale)
        res_perc_g2 = self._calcola_resistenza_set(g2, numero_set_attuale)
        if modalita_output != MODALITA_OUTPUT_RISULTATO:
            log_partita.append(f"    Res Inizio Set: G1({g1.id}): {res_perc_g1*100:.1f}%, G2({g2.id}): {res_perc_g2*100:.1f}%")

        while True:
            vincitore_set_id = None
            if punti_g1 >= PUNTI_LIMITE_SET: vincitore_set_id = g1.id
            elif punti_g2 >= PUNTI_LIMITE_SET: vincitore_set_id = g2.id
            elif punti_g1 >= PUNTI_VITTORIA_SET_BASE and punti_g1 >= punti_g2 + PUNTI_VANTAGGIO_NECESSARI: vincitore_set_id = g1.id
            elif punti_g2 >= PUNTI_VITTORIA_SET_BASE and punti_g2 >= punti_g1 + PUNTI_VANTAGGIO_NECESSARI: vincitore_set_id = g2.id
            if vincitore_set_id is not None: break

            servitore = g1 if servizio_corrente_id == g1.id else g2
            risponditore = g2 if servizio_corrente_id == g1.id else g1

            if modalita_output != MODALITA_OUTPUT_RISULTATO:
                 log_riga = f"  Pti: {punti_g1}-{punti_g2}. Serv: ID {servitore.id} ({servitore.nome[0]}.)"
                 if modalita_output == MODALITA_OUTPUT_CONSOLE: print(log_riga)
                 log_partita.append(log_riga)

            vincitore_punto_id, tipo_punto, dettaglio_azione = self._gioca_punto(
                g1, g2, servitore, risponditore, stats_g1, stats_g2, log_partita, modalita_output,
                res_perc_g1, res_perc_g2 # Passa resistenze corrette
            )

            if tipo_punto == 'PallaMorta':
                 if modalita_output != MODALITA_OUTPUT_RISULTATO: log_partita.append("      -> Punto da Ripetere (Palla Morta)")
                 continue

            punti_da_assegnare = PUNTI_PER_GOAL if tipo_punto == 'Goal' else PUNTI_PER_FALLO_AVVERSARIO if tipo_punto == 'Fallo' else 0
            if vincitore_punto_id == g1.id: punti_g1 += punti_da_assegnare
            elif vincitore_punto_id == g2.id: punti_g2 += punti_da_assegnare

            servizi_giocati_da_attuale += 1
            if servizi_giocati_da_attuale >= SERVIZI_CONSECUTIVI_PER_GIOCATORE:
                servizio_corrente_id = g2.id if servizio_corrente_id == g1.id else g1.id
                servizi_giocati_da_attuale = 0

            if modalita_output == MODALITA_OUTPUT_CONSOLE:
                try: key("... (Invio per prossimo punto)")
                except EOFError: print("Partita interrotta."); raise

        return (punti_g1, punti_g2), vincitore_set_id

    def _gioca_punto(self, g1: Giocatore, g2: Giocatore,
                     servitore: Giocatore, risponditore: Giocatore,
                     stats_g1: dict, stats_g2: dict,
                     log_partita: list, modalita_output: str,
                     res_perc_servitore: float, res_perc_risponditore: float # Riceve resistenze
                     ) -> tuple[int, str, Optional[str]]:
        """Simula un singolo punto/scambio."""
        debug_log_punto = []
        log_attivo = modalita_output != MODALITA_OUTPUT_RISULTATO
        id_servitore = servitore.id; id_risponditore = risponditore.id
        id_g1_orig = g1.id # ID originale del giocatore 1 della partita

        if log_attivo:
             log_partita.append(f"    Serve ID {id_servitore} ({servitore.nome[0]}. Res:{res_perc_servitore*100:.0f}%)"
                                f" vs ID {id_risponditore} ({risponditore.nome[0]}. Res:{res_perc_risponditore*100:.0f}%)")

        # --- FASE 1: Battuta ---
        skill_battuta_base = random.choice(['battutasx_base', 'battutadx_base'])
        azione_descr_batt = f"Battuta ({skill_battuta_base.replace('_base','')})"
        if log_attivo: debug_log_punto.append(f"    {azione_descr_batt} ID {id_servitore}")

        # Usa res_perc_servitore
        valore_battuta = self._calcola_valore_azione(servitore, "Battuta", skill_battuta_base, res_perc_servitore, debug_log=debug_log_punto)
        risultato_battuta, _ = self._risolvi_azione_vs_dado(servitore, risponditore, valore_battuta, azione_descr_batt, debug_log_punto)

        if risultato_battuta in ["FalloCritico", "Fallo"]:
            dettaglio = f"Fallo Battuta ({risultato_battuta})"
            if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> {dettaglio}! Punto a ID {id_risponditore}.")
            self._aggiorna_statistiche_punto(stats_g1 if id_risponditore == id_g1_orig else stats_g2,
                                             stats_g1 if id_servitore == id_g1_orig else stats_g2, 'Fallo')
            return id_risponditore, 'Fallo', dettaglio
        elif risultato_battuta == "Perfetto":
             dettaglio = f"Ace Battuta ({skill_battuta_base.replace('_base','')})"
             if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> {dettaglio}! Goal ID {id_servitore}!")
             self._aggiorna_statistiche_punto(stats_g1 if id_servitore == id_g1_orig else stats_g2,
                                              stats_g1 if id_risponditore == id_g1_orig else stats_g2, 'Goal')
             return id_servitore, 'Goal', dettaglio

        # --- FASE 2: Scambio ---
        attaccante_corrente = risponditore; difensore_corrente = servitore
        fattore_diff_difesa_ritorno = 1.0; ultimo_attacco_base = skill_battuta_base
        max_scambi_per_punto = 50; num_scambi = 0

        while num_scambi < max_scambi_per_punto:
            num_scambi += 1
            id_att = attaccante_corrente.id; id_dif = difensore_corrente.id
            # Determina resistenze correnti per att/dif
            res_perc_att = res_perc_risponditore if id_att == id_risponditore else res_perc_servitore
            res_perc_dif = res_perc_servitore if id_att == id_risponditore else res_perc_risponditore
            stats_att = stats_g1 if id_att == id_g1_orig else stats_g2
            stats_dif = stats_g2 if id_att == id_g1_orig else stats_g1

            # --- A. Azione Attaccante ---
            skill_attacco_base = random.choice(CARATTERISTICHE_ATTACCO_BASE)
            nome_colpo = skill_attacco_base.replace('_base','')
            azione_descr_att = f"Attacco ({nome_colpo}) ID {id_att}"
            if log_attivo: debug_log_punto.append(f"    {azione_descr_att}")

            val_attacco = self._calcola_valore_azione(attaccante_corrente, f"Attacco:{nome_colpo}", skill_attacco_base, res_perc_att, debug_log_punto)
            ris_att, _ = self._risolvi_azione_vs_dado(attaccante_corrente, difensore_corrente, val_attacco, azione_descr_att, debug_log_punto)

            if ris_att in ["FalloCritico", "Fallo"]:
                dettaglio = f"Fallo {nome_colpo} ({ris_att})"
                if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> {dettaglio} ID {id_att}! Punto a ID {id_dif}.")
                self._aggiorna_statistiche_punto(stats_dif, stats_att, 'Fallo')
                return id_dif, 'Fallo', dettaglio
            elif ris_att == "Perfetto":
                 dettaglio = f"Attacco Perfetto ({nome_colpo})"
                 if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> {dettaglio} ID {id_att}! Goal!")
                 self._aggiorna_statistiche_punto(stats_att, stats_dif, 'Goal')
                 return id_att, 'Goal', dettaglio
            elif ris_att != "Successo": # Fallimento Normale Attacco
                rand_fallimento = random.uniform(0, 100)
                if rand_fallimento < PROB_FALLO_SU_FALLIMENTO_NORMALE:
                    dettaglio = f"Fallo {nome_colpo} (Normale)"
                    if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> {dettaglio} ID {id_att}! Punto a ID {id_dif}.")
                    self._aggiorna_statistiche_punto(stats_dif, stats_att, 'Fallo')
                    return id_dif, 'Fallo', dettaglio
                elif rand_fallimento < PROB_FALLO_SU_FALLIMENTO_NORMALE + PROB_PALLAMORTA_SU_FALLIMENTO_NORMALE:
                    if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> Attacco Fallito ({nome_colpo}) ID {id_att}. Palla Morta.")
                    return 0, 'PallaMorta', None
                else: # Palla torna indietro FACILE
                    if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> Attacco Fallito ({nome_colpo}) ID {id_att}. Palla facile per ID {id_dif}!")
                    attaccante_corrente, difensore_corrente = difensore_corrente, attaccante_corrente
                    fattore_diff_difesa_ritorno = FATTORE_BONUS_DIFESA_SU_RITORNO_FACILE
                    ultimo_attacco_base = None # Non c'è un attacco specifico da contrastare
                    continue
            # Se arriviamo qui, ris_att == "Successo"
            ultimo_attacco_base = skill_attacco_base # Memorizza l'ultimo attacco valido

            # --- B. Azione Difensore ---
            chiusura_riuscita = False; blocco_riuscito = False

            # --- B.1 CHIUSURA / DIFESA PRIMARIA ---
            skill_difesa_base = MAPPA_CONTRASTO_SKILL.get(ultimo_attacco_base, 'difesa_base') if ultimo_attacco_base else 'difesa_base'
            nome_difesa = skill_difesa_base.replace('_base','')
            azione_descr_chius = f"Difesa ({nome_difesa}) ID {id_dif}"
            if log_attivo: debug_log_punto.append(f"    {azione_descr_chius}")

            val_difesa_base_calc = self._calcola_valore_azione(difensore_corrente, f"Difesa:{nome_difesa}", skill_difesa_base, res_perc_dif,
                                                               skill_attacco_avversario_base_nome=ultimo_attacco_base, debug_log=debug_log_punto)
            val_chiusura = val_difesa_base_calc * fattore_diff_difesa_ritorno
            if log_attivo and fattore_diff_difesa_ritorno != 1.0:
                 tipo_effetto = "Bonus" if fattore_diff_difesa_ritorno > 1.0 else "Malus"; debug_log_punto.append(f"      > {tipo_effetto} Difesa Ritorno: x{fattore_diff_difesa_ritorno:.2f} -> Val {nome_difesa} Eff: {val_chiusura:.2f}")

            ris_chius, _ = self._risolvi_azione_vs_dado(difensore_corrente, attaccante_corrente, val_chiusura, azione_descr_chius, debug_log_punto)

            if ris_chius in ["FalloCritico", "Fallo"]:
                dettaglio = f"Fallo {nome_difesa} ({ris_chius})"
                if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> {dettaglio} ID {id_dif}! Punto a ID {id_att}.")
                self._aggiorna_statistiche_punto(stats_att, stats_dif, 'Fallo')
                return id_att, 'Fallo', dettaglio
            elif ris_chius == "Perfetto":
                 if log_attivo: debug_log_punto.append(f"      -> Difesa ({nome_difesa}) Perfetta ID {id_dif}!")
                 chiusura_riuscita = True
            elif ris_chius == "Successo":
                 if val_chiusura >= val_attacco + MARGINE_DIFESA: # Difesa vince
                     if log_attivo: debug_log_punto.append(f"      -> Difesa ({nome_difesa}) riuscita!")
                     chiusura_riuscita = True
                 elif val_attacco >= val_chiusura + MARGINE_GOAL: # Attacco vince
                     dettaglio = f"Goal ({nome_colpo})"
                     if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> Attacco supera Difesa! {dettaglio} ID {id_att}!")
                     self._aggiorna_statistiche_punto(stats_att, stats_dif, 'Goal')
                     return id_att, 'Goal', dettaglio
                 else: # Valori Vicini -> Palla Morta
                     if log_attivo: log_partita.extend(debug_log_punto); log_partita.append("      -> Valori Attacco/Difesa vicini! Palla Morta.")
                     return 0, 'PallaMorta', None
            else: # Fallimento Normale Difesa
                rand_fallimento_dif = random.uniform(0, 100)
                if rand_fallimento_dif < PROB_FALLO_SU_FALLIMENTO_NORMALE:
                    dettaglio = f"Fallo {nome_difesa} (Normale)"
                    if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> {dettaglio} ID {id_dif}! Punto a ID {id_att}.")
                    self._aggiorna_statistiche_punto(stats_att, stats_dif, 'Fallo')
                    return id_att, 'Fallo', dettaglio
                elif rand_fallimento_dif < PROB_FALLO_SU_FALLIMENTO_NORMALE + PROB_PALLAMORTA_SU_FALLIMENTO_NORMALE:
                    if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> Difesa Fallita ({nome_difesa}) ID {id_dif}. Palla Morta.")
                    return 0, 'PallaMorta', None
                else: # Palla torna indietro FACILE
                    if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> Difesa Fallita ({nome_difesa}) ID {id_dif}. Palla facile per ID {id_att}!")
                    attaccante_corrente, difensore_corrente = difensore_corrente, attaccante_corrente # Inverti ruoli
                    fattore_diff_difesa_ritorno = FATTORE_BONUS_DIFESA_SU_RITORNO_FACILE # Bonus per prossimo difensore
                    ultimo_attacco_base = None # Non c'è un attacco specifico da contrastare
                    continue

            # --- B.2 BLOCCO (se Chiusura specifica è riuscita) ---
            skill_blocco_base = None
            if chiusura_riuscita:
                if skill_difesa_base == 'chiusurasx_base': skill_blocco_base = 'bloccosx_base'
                elif skill_difesa_base == 'chiusuradx_base': skill_blocco_base = 'bloccodx_base'
                else: blocco_riuscito = True # Salta blocco per tenuta/difesa generica

            if skill_blocco_base:
                nome_blocco = skill_blocco_base.replace('_base','')
                azione_descr_blocco = f"Blocco ({nome_blocco}) ID {id_dif}"
                if log_attivo: debug_log_punto.append(f"    {azione_descr_blocco}")

                val_blocco_base = self._calcola_valore_azione(difensore_corrente, f"Blocco:{nome_blocco}", skill_blocco_base, res_perc_dif, debug_log=debug_log_punto)
                val_blocco = val_blocco_base * fattore_diff_difesa_ritorno
                if log_attivo and fattore_diff_difesa_ritorno != 1.0: debug_log_punto.append(f"      > Fattore Difesa Ritorno: x{fattore_diff_difesa_ritorno:.2f} -> Val Blocco Eff: {val_blocco:.2f}")

                ris_blocco, _ = self._risolvi_azione_vs_dado(difensore_corrente, attaccante_corrente, val_blocco, azione_descr_blocco, debug_log_punto)

                if ris_blocco in ["FalloCritico", "Fallo"]:
                    dettaglio = f"Fallo Blocco ({nome_blocco}, {ris_blocco})"
                    if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> {dettaglio} ID {id_dif}! Punto a ID {id_att}.")
                    self._aggiorna_statistiche_punto(stats_att, stats_dif, 'Fallo')
                    return id_att, 'Fallo', dettaglio
                elif ris_blocco == "Perfetto" or ris_blocco == "Successo":
                     if log_attivo: debug_log_punto.append(f"      -> Blocco Riuscito ID {id_dif}!")
                     blocco_riuscito = True
                else: # Fallimento Normale Blocco
                    rand_fallimento_blocco = random.uniform(0, 100)
                    if rand_fallimento_blocco < PROB_FALLO_SU_FALLIMENTO_NORMALE:
                        dettaglio = f"Fallo Blocco ({nome_blocco}, Normale)"
                        if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> {dettaglio} ID {id_dif}! Punto a ID {id_att}.")
                        self._aggiorna_statistiche_punto(stats_att, stats_dif, 'Fallo')
                        return id_att, 'Fallo', dettaglio
                    elif rand_fallimento_blocco < PROB_FALLO_SU_FALLIMENTO_NORMALE + PROB_PALLAMORTA_SU_FALLIMENTO_NORMALE:
                        if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> Blocco Fallito ({nome_blocco}) ID {id_dif}. Palla Morta.")
                        return 0, 'PallaMorta', None
                    else: # Palla torna indietro FACILE
                        if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> Blocco Fallito ({nome_blocco}) ID {id_dif}. Palla facile per ID {id_att}!")
                        attaccante_corrente, difensore_corrente = difensore_corrente, attaccante_corrente
                        fattore_diff_difesa_ritorno = FATTORE_BONUS_DIFESA_SU_RITORNO_FACILE
                        ultimo_attacco_base = None
                        continue
            elif chiusura_riuscita:
                 blocco_riuscito = True # Se non serviva blocco, è considerato riuscito

            # --- B.3 CONTROLLO PALLA (se Blocco/Difesa OK) ---
            if blocco_riuscito:
                skill_controllo_base = 'controllopalla_base' # Usa base per calcolo valore
                azione_descr_ctrl = f"Controllo Palla ID {id_dif}"
                if log_attivo: debug_log_punto.append(f"    {azione_descr_ctrl}")

                val_controllo = self._calcola_valore_azione(difensore_corrente, "Controllo", skill_controllo_base, res_perc_dif, debug_log=debug_log_punto)
                ris_ctrl, _ = self._risolvi_azione_vs_dado(difensore_corrente, attaccante_corrente, val_controllo, azione_descr_ctrl, debug_log_punto)

                if ris_ctrl in ["FalloCritico", "Fallo"]:
                    dettaglio = f"Fallo Controllo Palla ({ris_ctrl})"
                    if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> {dettaglio} ID {id_dif}! Punto a ID {id_att}.")
                    self._aggiorna_statistiche_punto(stats_att, stats_dif, 'Fallo')
                    return id_att, 'Fallo', dettaglio
                elif ris_ctrl == "Perfetto" or ris_ctrl == "Successo":
                     if log_attivo: debug_log_punto.append(f"      -> Controllo Palla Riuscito ID {id_dif}! Ora attacca.")
                     attaccante_corrente, difensore_corrente = difensore_corrente, attaccante_corrente # Inverti ruoli
                     fattore_diff_difesa_ritorno = 1.0 # Resetta fattore bonus/malus
                     ultimo_attacco_base = None # Resetta ultimo attacco
                     continue # Continua scambio
                else: # Fallimento Normale Controllo
                    rand_fallimento_ctrl = random.uniform(0, 100)
                    if rand_fallimento_ctrl < PROB_FALLO_SU_FALLIMENTO_NORMALE:
                        dettaglio = "Fallo Controllo Palla (Normale)"
                        if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> {dettaglio} ID {id_dif}! Punto a ID {id_att}.")
                        self._aggiorna_statistiche_punto(stats_att, stats_dif, 'Fallo')
                        return id_att, 'Fallo', dettaglio
                    elif rand_fallimento_ctrl < PROB_FALLO_SU_FALLIMENTO_NORMALE + PROB_PALLAMORTA_SU_FALLIMENTO_NORMALE:
                        if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> Controllo Palla Fallito ID {id_dif}. Palla Morta.")
                        return 0, 'PallaMorta', None
                    else: # Palla torna indietro FACILE
                        if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> Controllo Palla Fallito ID {id_dif}. Palla facile per ID {id_att}!")
                        attaccante_corrente, difensore_corrente = difensore_corrente, attaccante_corrente
                        fattore_diff_difesa_ritorno = FATTORE_BONUS_DIFESA_SU_RITORNO_FACILE
                        ultimo_attacco_base = None
                        continue

            # Fallback sicurezza loop (improbabile)
            print(f"ERRORE LOGICO: Stato imprevisto in _gioca_punto fine B GID {id_dif}. Punto a GID {id_att}.")
            if log_attivo: log_partita.extend(debug_log_punto); log_partita.append(f"      -> Errore logico B! Punto a ID {id_att}.")
            self._aggiorna_statistiche_punto(stats_att, stats_dif, 'Fallo')
            return id_att, 'Fallo', 'Errore Flusso Difesa Post-Chiusura'

        # Se il loop while supera max_scambi_per_punto
        print(f"WARN: Punto terminato per limite scambi ({max_scambi_per_punto}). Assegno punto casuale.")
        if log_attivo: log_partita.extend(debug_log_punto); log_partita.append("      -> Limite scambi! Punto casuale.")
        vincitore_casuale = random.choice([id_att, id_dif])
        perdente_casuale = id_dif if vincitore_casuale == id_att else id_att
        stats_vinc_cas = stats_att if vincitore_casuale==id_att else stats_dif
        stats_perd_cas = stats_dif if vincitore_casuale==id_att else stats_att
        self._aggiorna_statistiche_punto(stats_vinc_cas, stats_perd_cas, 'Fallo')
        return vincitore_casuale, 'Fallo', 'Limite Scambi'

    def _calcola_valore_azione(self, giocatore: Giocatore, azione: str,
                               skill_specifica_base_nome: str, # Nome skill _base
                               resistenza_perc_attuale: float,
                               skill_attacco_avversario_base_nome: Optional[str] = None,
                               debug_log: Optional[list] = None) -> float:
        """Calcola il 'Valore Azione' completo, includendo bonus e malus."""
        try:
            if not skill_specifica_base_nome.endswith('_base'):
                 raise ValueError(f"Skill '{skill_specifica_base_nome}' deve essere _base GID {giocatore.id}")
            if not hasattr(giocatore, skill_specifica_base_nome):
                 raise ValueError(f"Skill '{skill_specifica_base_nome}' non trovata GID {giocatore.id}")

            skill_tot = giocatore._get_valore_totale(skill_specifica_base_nome)
            prec_tot = giocatore._get_valore_totale('precisione_base')
            forza_tot = giocatore._get_valore_totale('forza_base') # <-- RECUPERA FORZA
            res_tot = giocatore._get_valore_totale('resistenza_base')

            # Somma Componenti Base (SkillSpec + Prec*2 + Forza + Res + 5)
            valore_base_somma = 5+skill_tot + (prec_tot * 2.0) + forza_tot + res_tot

            bonus_azione_specifica = 0.0; azione_key = azione.split(':')[0]
            # Bonus Difesa vs Sponde
            if azione_key in ["Difesa", "Chiusura"] and skill_attacco_avversario_base_nome \
               and skill_attacco_avversario_base_nome in ['singolaspondasx_base', 'singolaspondadx_base', 'doppiaspondasx_base', 'doppiaspondadx_base', 'triplaspondasx_base', 'triplaspondadx_base']:
                bonus_azione_specifica += giocatore._get_valore_totale('difesa_base') * 0.25
            # Bonus Battuta
            elif azione_key == "Battuta": bonus_azione_specifica += VALORE_AZIONE_BONUS_BATTUTA
            # Bonus Forza alla Bomba
            elif skill_specifica_base_nome == 'bomba_base': bonus_azione_specifica += forza_tot * 0.10 # <-- BONUS FORZA BOMBA
            # Bonus Precisione al Controllo Palla
            elif azione_key == "Controllo": bonus_azione_specifica += prec_tot * 0.15

            bonus_flags = 0.0; is_azione_dinamica = azione_key in ["Attacco", "Difesa", "Blocco", "Battuta"]
            if is_azione_dinamica:
                if getattr(giocatore, 'giocorapido', False): bonus_flags += 5.0
                if getattr(giocatore, 'cambiovelocita', False): bonus_flags += 5.0

            valore_con_bonus = valore_base_somma + bonus_azione_specifica + bonus_flags
            perc_res_effettiva = max(0.05, resistenza_perc_attuale)
            valore_finale = valore_con_bonus * perc_res_effettiva

            if debug_log is not None:
                 log = f"      > Calc Val Azione ({azione} GID:{giocatore.id}):\n"
                 log += f"        - Base(5)+Skill({skill_specifica_base_nome.replace('_base','')}:{skill_tot:.1f})+Prec*2({prec_tot*2:.1f})+Forz({forza_tot:.1f})+Res({res_tot:.1f}) = {valore_base_somma:.1f}\n" # <-- CORRETTO LOG BASE e FORZA
                 if bonus_azione_specifica > 0: log += f"        - Bonus Azione Spec: +{bonus_azione_specifica:.1f}\n"
                 if bonus_flags > 0: log += f"        - Bonus Flags: +{bonus_flags:.1f}\n"
                 log += f"        - Subtotale: {valore_con_bonus:.1f}\n"
                 log += f"        - Malus Stanchezza (x{perc_res_effettiva:.2f}) -> Val Finale: {valore_finale:.2f}"
                 debug_log.append(log)
            return max(0.0, valore_finale)
        except AttributeError as e: print(f"ERRORE ATTRIBUTO in _calcola_valore_azione GID {giocatore.id}: {e}"); traceback.print_exc(); return 5.0
        except Exception as e: print(f"ERRORE inatteso in _calcola_valore_azione GID {giocatore.id}: {e}"); traceback.print_exc(); return 5.0

    def _calcola_resistenza_set(self, giocatore: Giocatore, num_set_attuale: int) -> float:
        """Calcola la percentuale di resistenza RIMANENTE per il set corrente."""
        if num_set_attuale <= 1: return 1.0
        eta_min_eff = ETA_MIN_CALO_RES; eta_max_eff = ETA_MAX_CALO_RES; range_eta_calo = eta_max_eff - eta_min_eff
        if range_eta_calo <= 0: range_eta_calo = 1
        eta_anni = giocatore.eta_anni
        perc_calo_target_set5 = TARGET_MIN_PERC_RES_SET5
        if eta_anni >= eta_max_eff: perc_calo_target_set5 = TARGET_MAX_PERC_RES_SET5
        elif eta_anni > eta_min_eff:
            progressione_eta = (eta_anni - eta_min_eff) / range_eta_calo
            perc_calo_target_set5 = TARGET_MIN_PERC_RES_SET5 + progressione_eta * (TARGET_MAX_PERC_RES_SET5 - TARGET_MIN_PERC_RES_SET5)
        if perc_calo_target_set5 <= 0: fattore_calo_per_set = 0.0
        else:
             try: fattore_calo_per_set = pow(perc_calo_target_set5, 0.25)
             except ValueError: fattore_calo_per_set = 0.01
        perc_resistenza_attuale = pow(fattore_calo_per_set, max(0, num_set_attuale - 1))
        return max(0.01, perc_resistenza_attuale)

    def _risolvi_azione_vs_dado(self, giocatore_att: Giocatore, giocatore_dif: Giocatore,
                                    valore_azione: float, azione_descr: str,
                                    debug_log: Optional[list] = None) -> Tuple[str, float]:
        """Tira dado e confronta col Valore Azione (o soglia scalata) per esito base."""
        dado = random.uniform(0, 100)
        risultato = "Fallo" # Default iniziale
        soglia_successo_scalata = valore_azione # Valore di fallback se non viene calcolata

        if dado < 5.0:
            risultato = "FalloCritico"
        elif dado >= 95.0:
            risultato = "Perfetto"
        else:
            # --- Inizio Logica Scaling ---
            # Calcola capacità difensiva generica del difensore (basata su ICV)
            capacita_difensiva = giocatore_dif.indice_collettivo_valore * SCALING_K_DIFESA_ICV
            delta_azione = valore_azione - capacita_difensiva

            # Normalizza delta tra -1 e 1 (approssimativamente, clampato)
            # Usa SCALING_RANGE_DELTA_EFF per definire la sensibilità
            # Se RANGE_DELTA_EFF è 0, evita divisione per zero
            range_div = (SCALING_RANGE_DELTA_EFF / 2.0)
            if range_div == 0:
                delta_norm = 0.0 # O gestisci come preferisci questo caso limite
            else:
                delta_norm = max(-1.0, min(1.0, delta_azione / range_div ))

            modificatore_soglia = delta_norm * SCALING_MODIFICATORE_MAX

            soglia_successo_scalata = SCALING_SOGLIA_BASE + modificatore_soglia
            # Assicura che la soglia rimanga tra i limiti dei critici/perfetti (5 e 95)
            soglia_successo_scalata = max(5.0, min(95.0, soglia_successo_scalata))

            if debug_log is not None:
                # Aggiungi log specifico per lo scaling
                log_scaling = f"      > Scaling Soglia: V.Az:{valore_azione:.1f}, Cap.Dif:{capacita_difensiva:.1f}, Delta:{delta_azione:.1f}, Soglia Scalata:{soglia_successo_scalata:.1f}"
                debug_log.append(log_scaling)

            # Confronto con il dado usando la soglia scalata
            if 5.0 <= dado < soglia_successo_scalata:
                risultato = "Successo"
            # Altrimenti rimane "Fallo" (se dado è tra soglia_scalata e 95.0)
            # --- Fine Logica Scaling ---

        # Log finale aggiornato
        if debug_log is not None:
             soglia_mostrata = soglia_successo_scalata if risultato not in ["FalloCritico", "Perfetto"] else valore_azione # Mostra valore originale per critici/perfetti
             debug_log.append(f"      > Risolvi Dado Scalato ({azione_descr} GID:{giocatore_att.id}): Dado={dado:.2f} vs Soglia={soglia_mostrata:.1f} -> {risultato}")

        return risultato, dado # Ritorna il dado originale
    
    def _aggiorna_statistiche_punto(self, stats_vincitore: dict, stats_perdente: dict, tipo_punto: str):
        """Aggiorna i contatori goal/falli in base all'esito del punto."""
        if tipo_punto == 'Goal': stats_vincitore['goal'] += 1
        elif tipo_punto == 'Fallo': stats_vincitore['falli_subiti'] += 1; stats_perdente['falli_fatti'] += 1

    def _aggiorna_statistiche_post_partita(self, risultato: dict, info_torneo: Optional[dict] = None):
        """Aggiorna statistiche permanenti, XP e gestisce infortuni post-partita."""
        try:
            id_vincitore = risultato.get('vincitore_id'); id_perdente = risultato.get('perdente_id')
            id_g1_orig = risultato.get('id_originale_g1'); id_g2_orig = risultato.get('id_originale_g2')
            num_set_target = risultato.get('num_set_target', 3); punteggio_set = risultato.get('punteggio_set', [])
            stats_g1 = risultato.get('stats_g1', {'goal':0, 'falli_fatti':0, 'falli_subiti':0})
            stats_g2 = risultato.get('stats_g2', {'goal':0, 'falli_fatti':0, 'falli_subiti':0})

            if None in [id_vincitore, id_perdente, id_g1_orig, id_g2_orig]: print("WARN: Dati risultato partita incompleti."); return
            g_vinc = self.giocatori.get(id_vincitore); g_perd = self.giocatori.get(id_perdente)
            if not g_vinc or not g_perd: print("WARN: Giocatore vincitore/perdente non trovato."); return

            stats_vinc = stats_g1 if id_vincitore == id_g1_orig else stats_g2
            stats_perd = stats_g2 if id_vincitore == id_g1_orig else stats_g1

            # Aggiorna Stats Permanenti
            g_vinc.partitevinte += 1; g_perd.partiteperse += 1
            set_vinti_vinc, set_vinti_perd = 0, 0
            for p1, p2 in punteggio_set:
                 if id_g1_orig == id_vincitore:
                     if p1 > p2: set_vinti_vinc += 1
                     else: set_vinti_perd += 1
                 else:
                      if p2 > p1: set_vinti_vinc += 1
                      else: set_vinti_perd += 1
            g_vinc.setsvinti += set_vinti_vinc; g_vinc.setspersi += set_vinti_perd
            g_perd.setsvinti += set_vinti_perd; g_perd.setspersi += set_vinti_vinc
            g_vinc.goalsfatti += stats_vinc.get('goal', 0); g_vinc.goalssubiti += stats_perd.get('goal', 0)
            g_perd.goalsfatti += stats_perd.get('goal', 0); g_perd.goalssubiti += stats_vinc.get('goal', 0)

            # Calcolo XP
            xp_vinc, xp_perd = 0, 0
            if set_vinti_vinc > set_vinti_perd:
                 if num_set_target <= 3:
                     if set_vinti_perd == 0: xp_vinc, xp_perd = XP_VITTORIA_2_0, XP_SCONFITTA_0_2
                     elif set_vinti_perd == 1: xp_vinc, xp_perd = XP_VITTORIA_2_1, XP_SCONFITTA_1_2
                 else:
                     if set_vinti_perd == 0: xp_vinc, xp_perd = XP_VITTORIA_3_0, XP_SCONFITTA_0_3
                     elif set_vinti_perd == 1: xp_vinc, xp_perd = XP_VITTORIA_3_1, XP_SCONFITTA_1_3
                     elif set_vinti_perd == 2: xp_vinc, xp_perd = XP_VITTORIA_3_2, XP_SCONFITTA_2_3
            if info_torneo: xp_vinc += XP_BONUS_TORNEO; xp_perd += XP_BONUS_TORNEO
            icv_vinc = g_vinc.indice_collettivo_valore; icv_perd = g_perd.indice_collettivo_valore
            max_icv = max(icv_vinc, icv_perd, 1.0); diff_perc = abs(icv_vinc - icv_perd) / max_icv * 100.0
            if diff_perc >= ICV_DIFF_PERC_UNDERDOG:
                if icv_vinc < icv_perd: xp_vinc += XP_BONUS_UNDERDOG
                else: xp_perd += XP_BONUS_UNDERDOG
            g_vinc.puntiesperienza = max(0, int(g_vinc.puntiesperienza or 0) + xp_vinc)
            g_perd.puntiesperienza = max(0, int(g_perd.puntiesperienza or 0) + xp_perd)
            print(f" -> XP Assegnati: ID {id_vincitore}: +{xp_vinc}, ID {id_perdente}: +{xp_perd}")

            # Controllo Infortuni
            print(" -> Controllo Infortuni...")
            for giocatore_corrente in [g_vinc, g_perd]:
                if not getattr(giocatore_corrente, 'infortunato', False):
                    prob_infortunio = self._calcola_prob_infortunio(giocatore_corrente)
                    if caso(prob_infortunio):
                        giocatore_corrente.infortunato = True
                        giorni_durata = self._calcola_durata_infortunio(giocatore_corrente)
                        data_fine = self.datetime_corrente_simulazione + datetime.timedelta(days=giorni_durata)
                        giocatore_corrente.infortunio_fine_datetime = data_fine
                        print(f"    -> INFORTUNIO! ID {giocatore_corrente.id} ({giocatore_corrente.nome}) fuori per {giorni_durata} giorni sim (fino a {data_fine:%Y-%m-%d %H:%M}). (Prob: {prob_infortunio:.3f}%)")
        except Exception as e: print(f"ERRORE aggiornamento stats post-partita: {e}"); traceback.print_exc()
    # --- FINE METODI PARTITA ---

    def visualizza_classifica_giocatori(self):
        """Mostra classifica globale giocatori attivi per ICV."""
        print("\n--- Classifica Globale Giocatori (per ICV) ---")
        attivi = [g for gid, g in self.giocatori.items() if gid not in self._ids_morti_processati_sessione and not g.ritirato]
        if not attivi: print("\n\tNessun giocatore attivo."); return
        ordinati = sorted(attivi, key=lambda g: g.indice_collettivo_valore, reverse=True); n_tot = len(ordinati); print(f"Trovati {n_tot} giocatori attivi.")
        try: pos_target = dgt(f"Visualizza intorno alla posizione (1-{n_tot})? ", "i", imin=1, imax=n_tot)
        except: print("\nInput non valido."); return
        idx_target = pos_target - 1; el_lato = 12; idx_start = max(0, idx_target - el_lato); idx_end = min(n_tot, idx_target + el_lato + 1)
        da_vis = ordinati[idx_start:idx_end]; n_vis = len(da_vis)
        if not da_vis: print("\n\tNessun giocatore nel range."); return
        print(f"\n--- Classifica Globale (Posizioni {idx_start + 1} - {idx_end}) ---")
        hdr = f"{'Pos':<5} {'ID':<5} {'Età(A/M/G)':<10} {'Archetipo':<25} {'ICV':<8} {'Club':<15} {'Nome Cognome'}"; print(hdr); print("-" * (len(hdr) + 5))
        for i, g in enumerate(da_vis):
            pos = idx_start + i + 1; eta = _formatta_eta_sim(g.eta, True); arch = getattr(g, 'archetipo_allenamento', 'N/D')[:25]
            icv = f"{g.indice_collettivo_valore:.1f}"; club = "Libero" if g.appartenenza == "*" else g.appartenenza[:15]; nome = f"{g.nome} {g.cognome}"
            prefix = "->" if pos == pos_target else "  "; print(f"{prefix}{pos:<3} {g.id:<5} {eta:<10} {arch:<25} {icv:<8} {club:<15} {nome}")
        print("-" * (len(hdr) + 5)); print(f"Visualizzate {n_vis} posizioni.")

    def _esegui_auto_allenamento_giocatore(self, giocatore: Giocatore):
        """Gestisce l'auto-allenamento CPU/Liberi."""
        xp_disp = int(giocatore.puntiesperienza or 0)
        if xp_disp <= 0 or giocatore.ritirato or giocatore.infortunato: return
        arch_nome = getattr(giocatore, 'archetipo_allenamento', "Non Definito")
        if arch_nome == "Non Definito" or arch_nome not in ARCHETIPI_ALLENAMENTO:
            validi = list(ARCHETIPI_ALLENAMENTO.keys()); arch_nome = random.choice(validi) if validi else "TuttofareBilanciato"; giocatore.archetipo_allenamento = arch_nome
        skill_scelta: Optional[str] = None; xp_spend: int = 0
        if caso(PROB_SEGUE_ARCHETIPO):
            try:
                cfg = ARCHETIPI_ALLENAMENTO[arch_nome]; priorita = list(cfg.get("priorita", []))
                if arch_nome=="TuttofareBilanciato": priorita=list(cfg.get("priorita_non_fisiche",[]))+list(cfg.get("priorita_fisiche",[]))
                str_scelta_base = cfg.get("strategia_scelta", "piu_bassa_prioritaria"); str_spesa = cfg.get("strategia_spesa", {"tipo":"perc","valore":10,"max_xp":200}); infl_eta = cfg.get("influenza_eta",{})
                fascia = "prime"
                if giocatore.eta <= ETA_GIOVANE_MAX_GIORNI: fascia = "giovane"
                elif giocatore.eta >= ETA_ANZIANO_MIN_GIORNI: fascia = "anziano"
                str_scelta = infl_eta.get(fascia, str_scelta_base); skill_ok = []
                for s in priorita:
                    if hasattr(giocatore, s):
                        v_a=getattr(giocatore,s,0.); a_b=s.replace('_allenata','_base'); v_b=getattr(giocatore,a_b,0.)
                        # <-- AGGIUNTO FORZA - Determina is_fis
                        is_fis = s in ["precisione_allenata", "resistenza_allenata", "forza_allenata"]
                        lim_a=MAX_ALLENATO_FISICO if is_fis else MAX_ALLENATO_SKILL; lim_t=MAX_TOTALE_PRECISIONE_RESISTENZA if is_fis else MAX_TOTALE_SKILL_GIOCO
                        if v_a<lim_a and(v_b+v_a)<lim_t: skill_ok.append(s)
                if not skill_ok: return
                # Implementazione strategie scelta (usa is_fis per costo)
                if str_scelta == "piu_bassa_prioritaria": skill_scelta = min(skill_ok, key=lambda s: getattr(giocatore, s, float('inf')))
                elif str_scelta == "piu_economica_prioritaria":
                    costi={s:self.calcola_costo_xp_per_punto(getattr(giocatore,s,0.), s in["precisione_allenata","resistenza_allenata", "forza_allenata"], giocatore.ipovedente) for s in skill_ok} # <-- AGGIUNTO FORZA
                    if costi: skill_scelta=min(costi,key=costi.get)
                elif str_scelta == "a_rotazione": skill_scelta = random.choice(skill_ok)
                elif str_scelta == "piu_bassa_tra_due":
                     due=[s for s in skill_ok if s in["precisione_allenata","resistenza_allenata", "forza_allenata"]]; skill_scelta = min(due,key=lambda s:getattr(giocatore,s,float('inf'))) if due else random.choice(skill_ok) if skill_ok else None # <-- AGGIUNTO FORZA
                elif str_scelta == "piu_bassa_assoluta_non_fisica":
                     non_f=[s for s in skill_ok if s not in["precisione_allenata","resistenza_allenata", "forza_allenata"]]; skill_scelta=min(non_f,key=lambda s:getattr(giocatore,s,float('inf'))) if non_f else random.choice(skill_ok) if skill_ok else None # <-- AGGIUNTO FORZA
                elif str_scelta == "piu_economica_prioritaria_o_resistenza":
                    s_res=3.; need_res="resistenza_allenata" in skill_ok and giocatore._get_valore_totale("resistenza_base")<s_res
                    if need_res: skill_scelta="resistenza_allenata"
                    else: costi={s:self.calcola_costo_xp_per_punto(getattr(giocatore,s,0.), s in["precisione_allenata","resistenza_allenata", "forza_allenata"], giocatore.ipovedente) for s in skill_ok}; skill_scelta=min(costi,key=costi.get) if costi else None # <-- AGGIUNTO FORZA
                elif str_scelta == "piu_bassa_tra_due_assoluta":
                    due=[s for s in skill_ok if s in["precisione_allenata","resistenza_allenata", "forza_allenata"]]; skill_scelta=min(due,key=lambda s:getattr(giocatore,s,float('inf'))) if due else skill_ok[0] if skill_ok else None # <-- AGGIUNTO FORZA
                elif str_scelta == "piu_bassa_assoluta_o_fisica_bassa":
                    s_fis=3.; fis_low=None; p_ok="precisione_allenata" in skill_ok; r_ok="resistenza_allenata" in skill_ok; f_ok="forza_allenata" in skill_ok # <-- AGGIUNTO FORZA check
                    p_tot=giocatore._get_valore_totale("precisione_base"); r_tot=giocatore._get_valore_totale("resistenza_base"); fo_tot=giocatore._get_valore_totale("forza_base") # <-- AGGIUNTO FORZA get
                    p_low=p_ok and p_tot<s_fis; r_low=r_ok and r_tot<s_fis; f_low=f_ok and fo_tot<s_fis # <-- AGGIUNTO FORZA check low
                    low_fis_skills = []
                    if p_low: low_fis_skills.append("precisione_allenata")
                    if r_low: low_fis_skills.append("resistenza_allenata")
                    if f_low: low_fis_skills.append("forza_allenata") # <-- AGGIUNTO FORZA
                    if low_fis_skills: fis_low = min(low_fis_skills, key=lambda s: getattr(giocatore, s, 0)) # Scegli la più bassa tra quelle basse
                    if fis_low: skill_scelta=fis_low
                    else: non_f=[s for s in skill_ok if s not in["precisione_allenata","resistenza_allenata", "forza_allenata"]]; skill_scelta=min(non_f,key=lambda s:getattr(giocatore,s,float('inf'))) if non_f else random.choice(skill_ok) if skill_ok else None # <-- AGGIUNTO FORZA
                if not skill_scelta and skill_ok: skill_scelta=random.choice(skill_ok)
                # Implementazione strategie spesa (usa is_fis per costo)
                if skill_scelta:
                    t_spesa=str_spesa.get("tipo","perc"); v_spesa=str_spesa.get("valore",10); max_xp=str_spesa.get("max_xp",MAX_XP_PER_ALLENAMENTO)
                    if t_spesa=="perc": xp_calc=int(xp_disp*(v_spesa/100.)); xp_spend=min(xp_calc,xp_disp,max_xp)
                    elif t_spesa=="quota": xp_spend=min(int(v_spesa),xp_disp,max_xp)
                    elif t_spesa=="obiettivo":
                        is_f=skill_scelta in["precisione_allenata","resistenza_allenata", "forza_allenata"]; v_att=getattr(giocatore,skill_scelta,0.); costo_p=self.calcola_costo_xp_per_punto(v_att,is_f,giocatore.ipovedente) # <-- AGGIUNTO FORZA
                        xp_calc=math.ceil(costo_p*v_spesa) if costo_p>0 else 0; xp_spend=min(xp_calc,xp_disp,max_xp)
                    else: xp_spend=min(int(xp_disp*0.1),max_xp)
                    xp_spend=max(0,xp_spend)
            except Exception as e: print(f"WARN: Err arch GID {giocatore.id}: {e}"); skill_scelta=None; xp_spend=0
        else: # Logica Reattiva
            nome_strategia_usata = "Reattivo"
            try:
                # <-- AGGIUNTO FORZA - Separa fisiche e non
                skill_nf_all=[s for s in ATTRIBUTI_ALLENABILI if s not in["precisione_allenata","resistenza_allenata", "forza_allenata"] and hasattr(giocatore,s)]
                skill_f_all=[s for s in ATTRIBUTI_ALLENABILI if s in["precisione_allenata","resistenza_allenata", "forza_allenata"] and hasattr(giocatore,s)]
                skill_nf,skill_f=[],[]
                # Filtra allenabili (non fisiche)
                for s in skill_nf_all:
                    v_a=getattr(giocatore,s,0.); a_b=s.replace('_allenata','_base'); v_b=getattr(giocatore,a_b,0.); lim_a=MAX_ALLENATO_SKILL; lim_t=MAX_TOTALE_SKILL_GIOCO
                    if v_a<lim_a and(v_b+v_a)<lim_t: skill_nf.append(s)
                # Filtra allenabili (fisiche)
                for s in skill_f_all:
                    v_a=getattr(giocatore,s,0.); a_b=s.replace('_allenata','_base'); v_b=getattr(giocatore,a_b,0.); lim_a=MAX_ALLENATO_FISICO; lim_t=MAX_TOTALE_PRECISIONE_RESISTENZA
                    if v_a<lim_a and(v_b+v_a)<lim_t: skill_f.append(s)
                fascia="prime"
                if giocatore.eta<=ETA_GIOVANE_MAX_GIORNI: fascia="giovane"
                elif giocatore.eta>=ETA_ANZIANO_MIN_GIORNI: fascia="anziano"
                # Priorità 1: Fisico per Anziani
                if fascia=="anziano":
                    s_fis=3.; allenare=None; p_tot=giocatore._get_valore_totale("precisione_base"); r_tot=giocatore._get_valore_totale("resistenza_base"); fo_tot=giocatore._get_valore_totale("forza_base") # <-- AGGIUNTO FORZA get
                    p_ok="precisione_allenata" in skill_f; r_ok="resistenza_allenata" in skill_f; f_ok="forza_allenata" in skill_f # <-- AGGIUNTO FORZA check
                    p_low=p_ok and p_tot<s_fis; r_low=r_ok and r_tot<s_fis; f_low=f_ok and fo_tot<s_fis # <-- AGGIUNTO FORZA check low
                    low_fis_skills = []
                    if p_low: low_fis_skills.append("precisione_allenata")
                    if r_low: low_fis_skills.append("resistenza_allenata")
                    if f_low: low_fis_skills.append("forza_allenata") # <-- AGGIUNTO FORZA
                    if low_fis_skills: allenare = min(low_fis_skills, key=lambda s: getattr(giocatore, s, 0))
                    if allenare: skill_scelta=allenare; xp_spend=min(xp_disp,350)
                # Priorità 2: Rafforza Debolezza (non fisica)
                if not skill_scelta and skill_nf:
                     s_deb=5.; vals={s:getattr(giocatore,s,0.) for s in skill_nf}
                     if vals:
                        p_b=min(vals,key=vals.get)
                        if vals[p_b]<s_deb: skill_scelta=p_b; xp_spend=min(xp_disp,250)
                # Priorità 3: Specializza (non fisica)
                if not skill_scelta and skill_nf:
                     vals={s:getattr(giocatore,s,0.) for s in skill_nf}
                     if vals: p_a=max(vals,key=vals.get); skill_scelta=p_a; xp_spend=min(xp_disp,450)
                # Fallback reattivo: più economica
                if not skill_scelta and(skill_nf or skill_f):
                    costi_f={s:self.calcola_costo_xp_per_punto(getattr(giocatore,s,0.),s in["precisione_allenata","resistenza_allenata", "forza_allenata"],giocatore.ipovedente) for s in skill_nf+skill_f} # <-- AGGIUNTO FORZA
                    if costi_f: skill_scelta=min(costi_f,key=costi_f.get); xp_spend=min(int(xp_disp*.15),300)
            except Exception as e: print(f"WARN: Err reatt GID {giocatore.id}: {e}"); skill_scelta=None; xp_spend=0
        # Esecuzione Allenamento
        if skill_scelta and xp_spend>0:
            try:
                v_a_att=getattr(giocatore,skill_scelta)
                # <-- AGGIUNTO FORZA - Determina is_fisica
                is_fisica = skill_scelta in ["precisione_allenata", "resistenza_allenata", "forza_allenata"]
                a_b=skill_scelta.replace('_allenata','_base'); v_b=getattr(giocatore,a_b,0.)
                lim_a=MAX_ALLENATO_FISICO if is_fisica else MAX_ALLENATO_SKILL; lim_t=MAX_TOTALE_PRECISIONE_RESISTENZA if is_fisica else MAX_TOTALE_SKILL_GIOCO; v_t_att=v_b+v_a_att
                if v_a_att>=lim_a or v_t_att>=lim_t: return
                xp_eff=min(xp_spend,xp_disp); costo_pt=self.calcola_costo_xp_per_punto(v_a_att,is_fisica,giocatore.ipovedente) # Passa is_fisica
                if costo_pt<=0: return
                guad_p=xp_eff/costo_pt; n_v_a_p=v_a_att+guad_p; guad_eff=guad_p; n_v_a_f=n_v_a_p; lim=False
                if n_v_a_p>lim_a: n_v_a_f=lim_a; lim=True
                if(v_b+n_v_a_f)>lim_t: n_v_a_f=max(0.,lim_t-v_b); lim=True
                if lim: guad_eff=max(0.,n_v_a_f-v_a_att); xp_nec=math.ceil(guad_eff*costo_pt); xp_eff=min(xp_eff,xp_nec,xp_disp)
                else: xp_nec_p=guad_eff*costo_pt; xp_eff=min(math.ceil(xp_nec_p),xp_disp)
                if xp_eff>0 and guad_eff>1e-4: setattr(giocatore,skill_scelta,n_v_a_f); giocatore.puntiesperienza=max(0,xp_disp-xp_eff); giocatore.aggiorna_icv()
            except Exception as e: print(f"WARN: Err exec allen GID {giocatore.id}: {e}"); traceback.print_exc()

    def visualizza_giocatori_papabili(self):
        if not self.miapolisportiva_attiva: print("\n\tAttiva richiesta."); return
        poli = self.miapolisportiva_attiva
        try: target = float(dgt("P.Acc. target [%]? (0-100, INVIO=100): ","f",fmin=0.,fmax=100.,default=100.))
        except: print("\nInput non valido."); return
        while True:
            print(f"\n--- Papabili per {poli.nome} (G:{poli.gloria}) ---")
            mov_rim = LIMITE_MOVIMENTI_PER_TICK - poli.movimenti_oggi
            print(f"Mov.tick rimasti: {mov_rim}/{LIMITE_MOVIMENTI_PER_TICK}")
            if mov_rim <= 0: print("Limite movimenti."); break
            liberi = [g for gid,g in self.giocatori.items() if g.appartenenza=="*" and not g.ritirato and gid not in self._ids_morti_processati_sessione]
            if not liberi: print("\n\tNessun libero."); break
            candidati=[(abs(self._calcola_probabilita_accettazione(poli.gloria,g.gloria_richiesta)-target), self._calcola_probabilita_accettazione(poli.gloria,g.gloria_richiesta), g) for g in liberi]
            candidati.sort(key=lambda x: (-x[1], -x[2].indice_collettivo_valore)); top20=candidati[:20]
            if not top20: print("\n\tNessun papabile."); break
            diz_papabili: Dict[str,str]={}
            hdr=f"{'P.Acc(%)':<8} {'Età(A/M/G)':<10} {'Nome Cognome':<25} {'Flg':<5} {'ICV'}"; print("\n"+hdr+"\n"+"-"*(len(hdr)+2))
            for _,prob,g in top20:
                flg="".join([f for a,f in MAPPA_FLAG_SOMMARIO.items() if getattr(g,a,False)]); flg_s=f"[{flg}]" if flg else ""
                eta=_formatta_eta_sim(g.eta,True); nome=f"{g.nome} {g.cognome}"[:25]; icv=f"ICV:{g.indice_collettivo_valore:6.1f}"
                riga=f"{prob:5.1f}% {'':<1} {eta:<10} {nome:<25} {flg_s:<5} {icv}"; diz_papabili[str(g.id)]=riga
            scelta=menu(d=diz_papabili,p="Tesserare? (ID o ESC): ",show=True,show_on_filter=True,pager=PAGINAZIONE_LISTE,keyslist=False,ntf="ID non in lista.")
            if scelta is None: print("Uscita."); break
            try: gid=int(scelta); self._tessera_giocatore(gid) if scelta in diz_papabili else print(f"\n\tID {gid} non visualizzato.")
            except: print(f"\n\tID '{scelta}' non valido.")
        print("\nRitorno Menu Poli...")

    def calcola_costo_xp_per_punto(self, val_allenato: float, is_fis: bool, is_ipo: bool) -> float:
        # is_fis è determinato da chi chiama (include forza)
        liv_calc = min(val_allenato, MAX_ALLENATO_FISICO if is_fis else MAX_ALLENATO_SKILL)
        bp_inf = 0; bps = sorted(XP_COSTO_SKILL_BREAKPOINTS.keys())
        for bp in bps:
            if liv_calc >= bp: bp_inf = bp
            else: break
        costo_base = XP_COSTO_SKILL_BREAKPOINTS[bp_inf]
        idx_inf = bps.index(bp_inf); bp_sup = bps[idx_inf+1] if idx_inf+1 < len(bps) else bp_inf; costo_sup = XP_COSTO_SKILL_BREAKPOINTS[bp_sup]
        costo = costo_base
        if bp_sup > bp_inf: costo = costo_base + ((liv_calc-bp_inf)/(bp_sup-bp_inf))*(costo_sup-costo_base)
        if is_fis: costo *= XP_COSTO_FISICO_MOLTIPL # Applica a PRC, RST, FOR
        if is_ipo and not is_fis: costo *= (1. - XP_SCONTO_IPOVEDENTI_PERC / 100.)
        return max(1., costo)

    def allenamento_giocatori_tesserati(self):
        if not self.miapolisportiva_attiva: print("\n\tAttiva richiesta."); return
        poli = self.miapolisportiva_attiva; print(f"\n--- Allenamenti {poli.nome} ---")
        allenabili=[gid for gid in list(poli.tesserati) if gid in self.giocatori and gid not in self._ids_morti_processati_sessione and not self.giocatori[gid].ritirato and not self.giocatori[gid].infortunato and int(self.giocatori[gid].puntiesperienza or 0)>0]
        if not allenabili: print("\nNessun atleta idoneo."); return
        print(f"{len(allenabili)} atleti con XP."); n_allenati=0; lasciati=[]
        for gid in allenabili:
            if gid not in self.giocatori or self.giocatori[gid].appartenenza!=poli.nome: continue
            g=self.giocatori[gid]; xp_pre=g.puntiesperienza; icv_pre=g.indice_collettivo_valore
            self._allena_singolo_giocatore(g)
            if g.puntiesperienza < xp_pre:
                n_allenati+=1; g.aggiorna_icv(); icv_post=g.indice_collettivo_valore
                print(f"-> XP Spesi:{xp_pre-g.puntiesperienza}. ICV:{icv_pre:.1f}->{icv_post:.1f}")
                g_rich=g.gloria_richiesta; p_gloria=poli.gloria; prob_esc=max(0.,100.-self._calcola_probabilita_accettazione(p_gloria,g_rich))
                print(f"-> Valutaz: G.Rich={g_rich}, G.Poli={p_gloria} => P.Uscita={prob_esc:.1f}%")
                if caso(prob_esc):
                    print(f"!!! INSODDISFATTO: {g.nome} lascia!"); lasciati.append((gid,g.nome,g.cognome))
                    poli_lasc=g.appartenenza; g.appartenenza="*"
                    if poli_lasc in self.polisportive: self.polisportive[poli_lasc].rimuovi_tesserato(gid,icv_post)
        poli.aggiorna_ict(self.giocatori, self._ids_morti_processati_sessione); poli.aggiorna_gloria(self.giocatori, self._ids_morti_processati_sessione)
        print(f"\n--- Allenamento {poli.nome} terminato ({n_allenati} allenati) ---")
        if lasciati: print("Atleti che hanno lasciato:"); [print(f"- ID:{id_l} {n} {c}") for id_l,n,c in lasciati]
        print(f"Stato finale {poli.nome}: ICT={poli.indicecollettivotesserati:.1f}, G={poli.gloria}")

    def _calcola_probabilita_accettazione(self, g_off: int, g_rich: int) -> float:
        if g_rich <= 0: return ACCETTAZIONE_PROB_MAX; th=ACCETTAZIONE_REL_DIFF_THRESHOLD
        th = ACCETTAZIONE_REL_DIFF_THRESHOLD
        d_min=-th*g_rich; d_max=th*g_rich; d_range=d_max-d_min; diff=float(g_off-g_rich)
        if diff <= d_min: return ACCETTAZIONE_PROB_MIN
        if diff >= d_max: return ACCETTAZIONE_PROB_MAX
        if d_range <= 0: return ACCETTAZIONE_PROB_MID
        pos=(diff-d_min)/d_range; prob=ACCETTAZIONE_PROB_MIN+pos*(ACCETTAZIONE_PROB_MAX-ACCETTAZIONE_PROB_MIN)
        return max(ACCETTAZIONE_PROB_MIN, min(prob, ACCETTAZIONE_PROB_MAX))

    def _aggiorna_stato_post_cpu(self):
        print("Aggiornamento stato polisportive...")
        if self.polisportive:
            n_agg=0
            for nome_p in list(self.polisportive.keys()):
                 if nome_p in self.polisportive:
                     p=self.polisportive[nome_p]; p.aggiorna_ict(self.giocatori,self._ids_morti_processati_sessione); p.aggiorna_gloria(self.giocatori,self._ids_morti_processati_sessione); n_agg+=1
            print(f"-> Stato ricalcolato per {n_agg} polisportive.")

    def _allena_singolo_giocatore(self, g: Giocatore):
        while int(g.puntiesperienza or 0) > 0:
            print(f"\nAllenando: {g.nome} {g.cognome} (ID:{g.id}, XP:{int(g.puntiesperienza or 0)})")
            if g.infortunato: print(f"{g.nome} infortunato."); return
            if g.ipovedente: print("(Ipovedente - Sconto XP)")
            try:
                scelta=menu(d=MENU_ALLENAMENTO,p="Caratteristica (ESC/Invio=Fine)? ",keyslist=True,pager=PAGINAZIONE_LISTE,show=True,show_on_filter=True)
                if scelta is None or scelta=='': break
                attr_a=ATTRIBUTI_ALLENABILI_MAP.get(scelta.lower())
                if not attr_a or not hasattr(g,attr_a): print("\n\tCodice non valido."); continue
                # <-- AGGIUNTO FORZA - Determina is_f
                is_f = attr_a in ["precisione_allenata", "resistenza_allenata", "forza_allenata"]
                nome_d=MENU_ALLENAMENTO.get(scelta,"?").replace(';','')
                val_a=getattr(g,attr_a,0.); attr_b=attr_a.replace('_allenata','_base'); val_b=getattr(g,attr_b,0.)
                lim_t=MAX_TOTALE_PRECISIONE_RESISTENZA if is_f else MAX_TOTALE_SKILL_GIOCO; lim_a=MAX_ALLENATO_FISICO if is_f else MAX_ALLENATO_SKILL; val_t=val_b+val_a
                print(f"\nScelto: {nome_d}"); print(f" Allenato:{val_a:.3f}(max {lim_a:.1f})"); print(f" Totale:{val_t:.3f}(max {lim_t:.1f})")
                if val_a>=lim_a or val_t>=lim_t: print("** Già al massimo! **"); input(" INVIO..."); continue
                costo_pt=self.calcola_costo_xp_per_punto(val_a,is_f,g.ipovedente); print(f" Costo:{costo_pt:.1f} XP/+1.0pt") # Passa is_f
                xp_max=int(g.puntiesperienza or 0); xp_spend=int(dgt(f"XP da spendere (max {xp_max}, 0=Annulla)? ","i",imin=0,imax=xp_max))
                if xp_spend==0: print("-> Annullato."); continue
                if costo_pt<=0: print("ERR: Costo nullo."); continue
                guad_p=xp_spend/costo_pt; n_a_p=val_a+guad_p; xp_eff=xp_spend; n_a_f=n_a_p; lim=False
                if n_a_p>lim_a: n_a_f=lim_a; lim=True
                if val_b+n_a_f>lim_t: n_a_f=max(0.,lim_t-val_b); lim=True
                guad_eff=max(0.,n_a_f-val_a)
                if lim: xp_nec=math.ceil(guad_eff*costo_pt); xp_eff=min(xp_spend,xp_nec,xp_max); print("INFO: Guadagno limitato.")
                xp_eff=min(xp_eff,xp_max); xp_rimb=xp_spend-xp_eff
                if xp_eff>0 and guad_eff>1e-4:
                    print(f"\nProposta: Spendi {xp_eff} XP per +{guad_eff:.3f} pt."); print(f"({xp_spend}-{xp_rimb}={xp_eff})") if xp_rimb>0 else None
                    print(f" {nome_d}(Allenata)-> {n_a_f:.3f}"); print(f" Totale-> {val_b+n_a_f:.3f}")
                    if key(" Confermi(S/n)? ").lower()!='n': setattr(g,attr_a,n_a_f); g.puntiesperienza=max(0,xp_max-xp_eff); print("-> Applicato!")
                    else: print("-> Annullato.")
                else: print("\nNessun allenamento."); print(f"({xp_spend} XP rimborsati).") if xp_rimb>0 and xp_spend>0 else None
            except EOFError: print("\nInterrotto."); break
            except Exception as e: print(f"\nERRORE: {e}"); traceback.print_exc(); break
        print(f"\nFine allenamento per {g.nome}.")

    def organizza_partita_amichevole(self):
        """Chiede i dettagli e avvia una partita amichevole tra due giocatori."""
        print("\n--- Organizza Partita Amichevole ---")
        try:
            id1 = dgt("ID Giocatore 1? ", "i", imin=1)
            if id1 not in self.giocatori: print(f"\tERRORE: Giocatore ID {id1} non trovato."); return
            g1 = self.giocatori[id1]
            if g1.ritirato: print(f"\tATTENZIONE: {g1.nome} è ritirato!"); return
            if g1.infortunato: print(f"\tATTENZIONE: {g1.nome} è infortunato!"); return
            id2 = dgt("ID Giocatore 2? ", "i", imin=1)
            if id2 == id1: print("\tERRORE: I giocatori devono essere diversi."); return
            if id2 not in self.giocatori: print(f"\tERRORE: Giocatore ID {id2} non trovato."); return
            g2 = self.giocatori[id2]
            if g2.ritirato: print(f"\tATTENZIONE: {g2.nome} è ritirato!"); return
            if g2.infortunato: print(f"\tATTENZIONE: {g2.nome} è infortunato!"); return
            print(f"\nPartita: {g1.nome} {g1.cognome} (ID:{id1}) vs {g2.nome} {g2.cognome} (ID:{id2})")
            set_input = dgt("Al meglio di quanti Set (3 o 5)? ", "i", imin=3, imax=5)
            num_set = 5 if set_input == 5 else 3
            print(f"Partita al meglio dei {num_set} set.")
            print("\nModalità Visualizzazione Risultati:")
            opzioni_output = {'R': "Solo Risultato finale", 'C': "Cronaca in Console (punto per punto)", 'F': "Salva Cronaca su File"}
            scelta_output = menu(d=opzioni_output, p="Scegli modalità (R/C/F)? ", keyslist=True, show=True)
            modalita = MODALITA_OUTPUT_RISULTATO
            if scelta_output == 'C': modalita = MODALITA_OUTPUT_CONSOLE
            elif scelta_output == 'F': modalita = MODALITA_OUTPUT_FILE
            print("Avvio simulazione partita...")
            risultato = self.gioca_partita(id1, id2, num_set, modalita)
            if risultato:
                if risultato.get('error'): print(f"\nErrore durante la partita: {risultato['error']}")
                else:
                    print("\n--- Riepilogo Partita Amichevole ---")
                    v_id = risultato.get('vincitore_id'); p_id = risultato.get('perdente_id')
                    if v_id and p_id and v_id in self.giocatori and p_id in self.giocatori:
                        print(f"Vincitore: ID {v_id} ({self.giocatori[v_id].nome} {self.giocatori[v_id].cognome})")
                        print(f"Perdente:  ID {p_id} ({self.giocatori[p_id].nome} {self.giocatori[p_id].cognome})")
                        print(f"Punteggio Set: {risultato.get('punteggio_set')}")
                    else: print("Errore nel determinare vincitore/perdente.")
                    if risultato.get('log_path'): print(f"Cronaca completa disponibile in: {risultato['log_path']}")
            else: print("\nErrore imprevisto: la funzione gioca_partita non ha restituito un risultato.")
        except (ValueError, TypeError) as e_input: print(f"\nERRORE Input/Tipo non valido: {e_input}"); print("Operazione partita annullata.")
        except EOFError: print("\nOperazione annullata (EOF).")
        except Exception as e: print(f"\nERRORE IMPREVISTO OPA: {e}"); traceback.print_exc()
        input("\nPremi INVIO per tornare al menu...")

    def _crea_nuova_poli_cpu_interna(self, dt_creaz: datetime.datetime) -> Optional[str]:
        suff=1; base="PoliTeam"
        while True:
            prefix=f"{base}{suff:02d} "
            if not any(n.startswith(prefix) for n in self.polisportive): break
            suff+=1
            if suff>9999: print("ATT: Suffix CPU>9999."); return None
        try:
            p1=genera_nome_casuale(["cvcv"],'x').lower()
            p2=genera_nome_casuale(["cvcv"],'x').lower()
            nome=f"{base}{suff:02d} {p1}-{p2}"
            if nome in self.polisportive: print(f"ATT: Collisione nome CPU '{nome}'."); return None
            nuova=Polisportiva(nome=nome,password=None,datetime_creazione_sim=dt_creaz,is_cpu_controlled=True)
            self.polisportive[nome]=nuova; return nome
        except Exception as e: print(f"ERR creaz poli CPU '{nome}': {e}"); return None

    def visualizza_riepilogo_giocatori(self):
        try:
            id1=int(dgt("ID iniziale? ","i",imin=1))
            id2=int(dgt("ID finale? ","i",imin=id1))
            ids=[gid for gid in range(id1,id2+1) if gid in self.giocatori]
            if not ids: print(f"\nNessun giocatore ID {id1}-{id2}."); return
            self.visualizza_lista(ids,f"Riepilogo Giocatori (ID {id1}-{id2})","giocatore")
        except (ValueError,TypeError): print("\n\tID non valido.")
        except EOFError: print("\nAnnullato.")

    def menu_polisportive(self):
        while True:
            print("\n"+"-"*30+" Menu Polisportive "+"-"*30)
            print(f"Attiva: <{self.miapolisportiva_attiva.sommario(self.datetime_corrente_simulazione)}>" if self.miapolisportiva_attiva else "<Nessuna Attiva>")
            try:
                scelta=menu(d=POLIMENU,keyslist=True,pager=PAGINAZIONE_LISTE,show=False,show_on_filter=True)
                if scelta is None: break
                if scelta and scelta != '?': self.comandi_eseguiti += 1
                cmd_map={'VLE':lambda: self.visualizza_lista(sorted(self.polisportive.keys()),"Lista Polisportive","polisportiva") if self.polisportive else print("\n\tNessuna."),
                         'APR':self._apri_nuova_polisportiva, 'CPA':self._cambia_polisportiva_attiva,
                         'VSP':lambda: (print(self.miapolisportiva_attiva), self._stampa_dettagli_tesserati_polisportiva()) if self.miapolisportiva_attiva else print("Attiva Richiesta."),
                         'VGT':lambda: self.visualizza_lista(sorted([gid for gid in self.miapolisportiva_attiva.tesserati if gid in self.giocatori]), f"Tesserati {self.miapolisportiva_attiva.nome}", "giocatore") if self.miapolisportiva_attiva and self.miapolisportiva_attiva.tesserati else print("Nessun tesserato." if self.miapolisportiva_attiva else "Attiva Richiesta."),
                         'VGP':self.visualizza_giocatori_papabili if self.miapolisportiva_attiva else lambda:print("Attiva Richiesta."),
                         'TEG':self._tessera_giocatore if self.miapolisportiva_attiva else lambda:print("Attiva Richiesta."),
                         'ESG':self._espelli_giocatore if self.miapolisportiva_attiva else lambda:print("Attiva Richiesta."),
                         'CHI':self._chiudi_polisportiva_attiva if self.miapolisportiva_attiva else lambda:print("Attiva Richiesta."),
                         'MPP':self._modifica_password_polisportiva if self.miapolisportiva_attiva else lambda:print("Attiva Richiesta."),}
                if scelta=='?': continue
                elif scelta in cmd_map: cmd_map[scelta]()
                else: print(f"\n\tComando '{scelta}' non valido.")
                if scelta=='CHI' and not self.miapolisportiva_attiva: break
            except EOFError: print("\nUscita (EOF)..."); break
            except Exception as e: print(f"\nERRORE menu poli: {e}"); traceback.print_exc(); input(" INVIO...")
        print("\nRitorno menu principale...")

    def _crea_polisportiva_cpu(self):
        print("\n--- Creazione Poli CPU ---")
        nome=self._crea_nuova_poli_cpu_interna(self.datetime_corrente_simulazione)
        print(f"\nPoli CPU '{nome}' creata.") if nome else print("\nCreazione fallita.")

    def _stampa_dettagli_tesserati_polisportiva(self):
        """Stampa dettagli aggiuntivi sui tesserati della polisportiva attiva."""
        if not self.miapolisportiva_attiva or not self.miapolisportiva_attiva.tesserati: return
        poli = self.miapolisportiva_attiva; somma_eta_giorni = 0; maschi = 0; femmine = 0; ipovedenti = 0
        tesserati_per_stats = [gid for gid in poli.tesserati if gid in self.giocatori and gid not in self._ids_morti_processati_sessione]
        num_tesserati_attuali = len(tesserati_per_stats)
        if num_tesserati_attuali == 0: print("Nessun tesserato valido trovato per statistiche dettagliate."); return
        for gid in tesserati_per_stats:
            g = self.giocatori[gid]; somma_eta_giorni += g.eta
            if g.sesso == 'm': maschi += 1
            else: femmine += 1
            if g.ipovedente: ipovedenti += 1
        eta_media_giorni = somma_eta_giorni / num_tesserati_attuali if num_tesserati_attuali > 0 else 0
        eta_media_str = _formatta_eta_sim(int(eta_media_giorni), formato_breve=True)
        print("\nDettagli Tesserati:"); print(f"  Composizione: {maschi} Uomini, {femmine} Donne ({num_tesserati_attuali} totali)")
        print(f"  Età Media (Sim): {eta_media_str}, Ipovedenti: {ipovedenti}"); print("-" * 30)

    def _apri_nuova_polisportiva(self):
        print("\n--- Apertura Nuova Polisportiva ---")
        try:
            nome=dgt("Nome (5-50)? ","s",smin=5,smax=50).title()
            if nome in self.polisportive or nome=="Nessuna": print(f"\n\tNome '{nome}' esistente/non valido."); return
            pwd1=self._chiedi_password("Password: ")
            if not pwd1: print("\n\tPassword vuota."); return
            if pwd1!=self._chiedi_password("Conferma: "): print("\n\tPassword non coincidono."); return
            nuova=Polisportiva(nome=nome,password=pwd1,datetime_creazione_sim=self.datetime_corrente_simulazione,is_cpu_controlled=False)
            self.polisportive[nome]=nuova; print(f"\nPoli '{nome}' creata ({self.datetime_corrente_simulazione:%Y-%m-%d %H:%M}).")
            if key("Attivarla ora (S/n)? ").lower()!='n': self.miapolisportiva_attiva=nuova; print("Attivata.")
        except EOFError: print("\nAnnullato.")
        except Exception as e: print(f"Errore: {e}")

    def _cambia_polisportiva_attiva(self):
        print("\n--- Cambia Polisportiva Attiva ---")
        poli_u={n:p for n,p in self.polisportive.items() if not p.is_cpu_controlled}
        if not poli_u: print("\n\tNessuna poli utente."); return
        print("Polisportive Utente:"); [print(f"- {p.sommario(self.datetime_corrente_simulazione)}") for p in poli_u.values()]
        try:
            nome=dgt("Nome poli da attivare: ","s",smin=1,smax=50).title()
            if nome in poli_u:
                p_sel=poli_u[nome]; pwd=self._chiedi_password(f"Password '{nome}': ")
                if pwd==p_sel.password: self.miapolisportiva_attiva=p_sel; print(f"\n'{nome}' attivata.")
                else: print("\n\tPassword errata.")
            else: print(f"\n\tPoli utente '{nome}' non trovata.")
        except EOFError: print("\nAnnullato.")

    def _tessera_giocatore(self, giocatore_id: Optional[int] = None):
        if not self.miapolisportiva_attiva: print("\n\tAttiva richiesta."); return
        poli = self.miapolisportiva_attiva
        if poli.movimenti_oggi >= LIMITE_MOVIMENTI_PER_TICK: print(f"\n\tLimite {LIMITE_MOVIMENTI_PER_TICK} movimenti tick."); return
        if len(poli.tesserati) >= poli.maxtesserati: print(f"\n\tLimite {poli.maxtesserati} tesserati."); return
        try:
            gid = giocatore_id
            if gid is None:
                print(f"\n--- Tesseramento {poli.nome} ---"); print(f"G:{poli.gloria}. MovTick:{poli.movimenti_oggi}/{LIMITE_MOVIMENTI_PER_TICK}")
                gid = int(dgt("ID giocatore? ", "i", imin=1))
            else: print(f"\n--- Tentativo Tess. ID:{gid} ({poli.nome}) ---"); print(f"MovTick:{poli.movimenti_oggi}/{LIMITE_MOVIMENTI_PER_TICK}")
            if gid not in self.giocatori: print(f"\n\tID {gid} non trovato."); return
            g=self.giocatori[gid]
            if gid in self._ids_morti_processati_sessione: print(f"\n\t{g.nome} deceduto."); return
            if g.ritirato and key(f"ATT: {g.nome} ritirato. Tesserare(s/N)? ").lower()!='s': print("Annullato."); return
            if g.appartenenza!="*": print(f"\n\tGià tesserato per '{g.appartenenza}'."); return
            g_rich=g.gloria_richiesta; g_off=poli.gloria; print(f"\tRich:{g_rich}. Off:{g_off}.")
            poli.movimenti_oggi+=1; poli.datetime_ultimo_movimento=datetime.datetime.now(); print(f"Tentativo... (Mov.{poli.movimenti_oggi}/{LIMITE_MOVIMENTI_PER_TICK})")
            prob=self._calcola_probabilita_accettazione(g_off,g_rich); print(f"\tProb.acc:{prob:.1f}%")
            if caso(prob): print(f"\t{g.nome} ACCETTA!"); g.appartenenza=poli.nome; poli.aggiungi_tesserato(gid,g.indice_collettivo_valore); print(f"\n{g.nome} tesserato!")
            else: print(f"\t{g.nome} RIFIUTA!")
            print(f"Mov.tick rimasti: {LIMITE_MOVIMENTI_PER_TICK-poli.movimenti_oggi}")
            if giocatore_id is not None: input("...INVIO...")
        except (ValueError,TypeError): print("\n\tID non valido.")
        except EOFError: print("\nAnnullato.")
        except Exception as e: print(f"\nErrore: {e}")

    def _espelli_giocatore(self):
        if not self.miapolisportiva_attiva: print("\n\tAttiva richiesta."); return
        poli = self.miapolisportiva_attiva; print(f"\n--- Espulsione da {poli.nome} ---"); print(f"Mov.Tick:{poli.movimenti_oggi}/{LIMITE_MOVIMENTI_PER_TICK}")
        if not poli.tesserati: print("\n\tNessun tesserato."); return
        ids_val=[gid for gid in poli.tesserati if gid in self.giocatori]
        if not ids_val: print("\n\tNessun tesserato valido."); return
        self.visualizza_lista(sorted(ids_val),f"Tesserati {poli.nome}","giocatore")
        try:
            gid=int(dgt("ID da espellere? ","i",imin=1))
            if gid not in poli.tesserati: print(f"\n\tID {gid} non tesserato qui."); return
            g_nome=f"ID {gid}"; g_icv=0.; g_esiste=gid in self.giocatori
            if g_esiste: g=self.giocatori[gid]; g_nome=f"{g.nome} {g.cognome}"; g_icv=g.indice_collettivo_valore
            else: print(f"ATT: ID {gid} non nel DB.")
            if key(f"Confermi espulsione {g_nome}(ID:{gid})? (s/N) ").lower()=='s':
                if poli.movimenti_oggi>=LIMITE_MOVIMENTI_PER_TICK: print(f"\n\tLimite {LIMITE_MOVIMENTI_PER_TICK} movimenti tick."); return
                poli.rimuovi_tesserato(gid,g_icv)
                if g_esiste: self.giocatori[gid].appartenenza="*"
                poli.movimenti_oggi+=1; poli.datetime_ultimo_movimento=datetime.datetime.now()
                print(f"\n{g_nome}(ID:{gid}) espulso."); print(f"Mov.tick rimasti:{LIMITE_MOVIMENTI_PER_TICK-poli.movimenti_oggi}")
            else: print("\nAnnullato.")
        except (ValueError,TypeError): print("\n\tID non valido.")
        except EOFError: print("\nAnnullato.")
        except Exception as e: print(f"\nErrore: {e}")

    def _chiudi_polisportiva_attiva(self):
        if not self.miapolisportiva_attiva: print("\n\tNessuna poli attiva."); return
        poli = self.miapolisportiva_attiva; print(f"\n--- Chiusura Definitiva {poli.nome} ---"); print("ATT: Irreversibile.")
        try:
            if self._chiedi_password(f"Password '{poli.nome}': ")==poli.password:
                if dgt("Scrivi 'CHIUDI': ","s",smax=6)=="CHIUDI":
                    n_lib=0
                    for gid in list(poli.tesserati):
                        icv=0.
                        if gid in self.giocatori: g=self.giocatori[gid]; g.appartenenza="*"; icv=g.indice_collettivo_valore
                        poli.rimuovi_tesserato(gid,icv); n_lib+=1
                    nome=poli.nome; del self.polisportive[nome]; print(f"\nPoli '{nome}' chiusa. {n_lib} liberati.")
                    self.miapolisportiva_attiva=None; print("Nessuna poli attiva.")
                else: print("\nConferma non valida.")
            else: print("\n\tPassword errata.")
        except EOFError: print("\nAnnullato.")

    def _modifica_password_polisportiva(self):
        if not self.miapolisportiva_attiva: print("\n\tNessuna poli attiva."); return
        poli = self.miapolisportiva_attiva; print(f"\n--- Modifica Password {poli.nome} ---")
        try:
            if self._chiedi_password("Password attuale: ")!=poli.password: print("\n\tPassword attuale errata."); return
            pwd1=self._chiedi_password("Nuova password: ")
            if not pwd1: print("\n\tPassword vuota."); return
            if pwd1==self._chiedi_password("Conferma nuova: "): poli.password=pwd1; print("\nPassword modificata.")
            else: print("\n\tNon coincidono.")
        except EOFError: print("\nAnnullato.")

    def _mostra_prossimo_sblocco_attivita(self):
        try:
            if hasattr(self,'datetime_ultimo_run_reale') and isinstance(self.datetime_ultimo_run_reale,datetime.datetime):
                ora_sblocco = self.datetime_ultimo_run_reale+datetime.timedelta(hours=8); now=datetime.datetime.now()
                if now < ora_sblocco:
                    try: h,m,s=converti_in_tempo((ora_sblocco-now).total_seconds()); print(f"INFO: Prox aggiornamento sim alle {ora_sblocco:%H:%M:%S del %d/%m/%Y} (tra {h}h {m}m).")
                    except: print(f"INFO: Prox aggiornamento sim alle {ora_sblocco:%H:%M:%S del %d/%m/%Y}.")
        except Exception as e: print(f"DEBUG: Errore _mostra_sblocco: {e}")

    def _processa_tempo_trascorso(self):
        """Avanza simulazione aggregata per tick 8h reali (1 giorno sim/tick)."""
        now = datetime.datetime.now()
        if not isinstance(self.datetime_ultimo_run_reale, datetime.datetime):
            print("WARN: dt_ultimo_run non valido. Reset.")
            self.datetime_ultimo_run_reale = now - datetime.timedelta(hours=8)

        delta_r = now - self.datetime_ultimo_run_reale
        ticks = int(delta_r.total_seconds() // (8 * 3600)) if delta_r.total_seconds() > 0 else 0

        if ticks <= 0:
            self._mostra_prossimo_sblocco_attivita()
            return

        print(f"\n--- Processando {ticks} tick da 8h ({delta_r}) ---")
        for p in self.polisportive.values():
            p.movimenti_oggi = 0

        # Calcoli tempo
        gg_tick = ANNO_SIMULAZIONE_GIORNI / (365.25 * 3.) if ANNO_SIMULAZIONE_GIORNI > 0 else 0.0
        giorni_per_tick = 1.0
        gg_sim_i = int(ticks * giorni_per_tick)
        gg_sim_f = float(gg_sim_i)
        dt_sim_s = self.datetime_corrente_simulazione
        dt_sim_e = dt_sim_s + datetime.timedelta(days=gg_sim_f)
        print(f"Avanzamento sim: +{gg_sim_i} giorni -> {dt_sim_e:%Y-%m-%d %H:%M}")

        # Applica effetti aggregati
        ids_proc = list(self.giocatori.keys())
        ids_morti_c, ids_rit_c = set(), set()
        self.giocatori_morti_sessione.clear(); self.giocatori_ritirati_sessione.clear(); self._ids_morti_processati_sessione.clear()
        n_gua, n_dec, n_rit, n_usciti_prem = 0, 0, 0, 0

        for gid in ids_proc:
            if gid not in self.giocatori: continue
            g = self.giocatori[gid]; eta_pre = g.eta
            # Guarigione
            if g.infortunato and g.infortunio_fine_datetime and dt_sim_e >= g.infortunio_fine_datetime:
                g.infortunato = False; g.infortunio_fine_datetime = None; n_gua += 1
            # Età
            g.eta += gg_sim_i
            # Declino (include forza perché in ATTRIBUTI_INVECCHIABILI)
            if gg_sim_i > 0: g._applica_declino_aggregato(gg_sim_i)

            # Controllo Uscita Prematura
            if gg_sim_i > 0 and PROB_USCITA_PREMATURA_GIORNALIERA > 0:
                prob_non_uscire_1 = 1.0 - (PROB_USCITA_PREMATURA_GIORNALIERA / 100.0)
                try: prob_non_uscire_N = pow(prob_non_uscire_1, gg_sim_i)
                except OverflowError: prob_non_uscire_N = 0.0
                prob_uscire_N = (1.0 - prob_non_uscire_N) * 100.0
                if caso(prob_uscire_N):
                    if gid not in ids_morti_c:
                         motivo_uscita = "Uscita Prematura"
                         msg = f"{motivo_uscita.upper()}: {g.nome} {g.cognome}(ID:{gid}) lascia il mondo a {_formatta_eta_sim(g.eta)} sim."
                         self.giocatori_morti_sessione.append((gid, msg))
                         self._ids_morti_processati_sessione.add(gid); ids_morti_c.add(gid); n_usciti_prem += 1
                         g.ritirato = True
                         if g.appartenenza != "*" and g.appartenenza in self.polisportive: self.polisportive[g.appartenenza].rimuovi_tesserato(gid, g.indice_collettivo_valore)
                         g.appartenenza = "*"; self._logga_uscita_giocatore(g, motivo_uscita, dt_sim_e)
                         continue

            # Controllo Morte Naturale
            if g.eta >= g.etamorte:
                if gid not in ids_morti_c:
                     motivo_uscita = "Decesso Naturale"
                     msg = f"DECESSO (Età): {g.nome} {g.cognome}(ID:{gid}) tra {_formatta_eta_sim(eta_pre)} e {_formatta_eta_sim(g.eta)} sim."
                     self.giocatori_morti_sessione.append((gid, msg))
                     self._ids_morti_processati_sessione.add(gid); ids_morti_c.add(gid); n_dec += 1; g.ritirato = True; g.appartenenza = "*"
                     self._logga_uscita_giocatore(g, motivo_uscita, dt_sim_e)
                     continue

            # Ritiro per età
            if not g.ritirato and g.eta >= g.etaritiro:
                 if gid not in ids_rit_c:
                      msg = f"RITIRO: {g.nome} {g.cognome}(ID:{gid}) a {_formatta_eta_sim(g.eta)} sim."
                      self.giocatori_ritirati_sessione.append((gid, msg)); ids_rit_c.add(gid); n_rit += 1; g.ritirato = True

        # Riepilogo effetti
        if n_gua: print(f"-> {n_gua} guariti.")
        if n_usciti_prem > 0: print(f"-> {n_usciti_prem} giocatori usciti prematuramente.")
        if n_dec > 0: print(f"-> {n_dec} deceduti per età.")
        if n_rit > 0: print(f"-> {n_rit} ritirati per età.")
        self._ids_morti_processati_sessione.update(ids_morti_c)

        # Azioni Aggregate
        print("Esecuzione azioni aggregate...")
        n_autoall = 0
        ids_vivi = [gid for gid in ids_proc if gid not in self._ids_morti_processati_sessione and gid in self.giocatori]

        # Auto-Allenamento (include forza perché in liste/logica)
        for gid in ids_vivi:
             if gid not in self.giocatori: continue
             g = self.giocatori[gid]
             if not g.ritirato and not g.infortunato and int(g.puntiesperienza or 0) > 0:
                  if g.appartenenza == "*" or \
                     (g.appartenenza in self.polisportive and self.polisportive[g.appartenenza].is_cpu_controlled):
                       xp_pre = g.puntiesperienza
                       self._esegui_auto_allenamento_giocatore(g)
                       if g.puntiesperienza < xp_pre: n_autoall += 1
        if n_autoall > 0: print(f"-> {n_autoall} giocatori si sono auto-allenati.")

        # Logica CPU Polisportive
        n_tess_cpu, n_esp_cpu = self._esegui_logica_cpu_polisportive()

        # Chiusura/Creazione Poli CPU
        n_chiuse, n_cr_sess, n_cr_ciclo = 0, 0, 0
        n_gioc_att = len(ids_vivi)
        lim_poli = (n_gioc_att / GIOCATORI_ATTIVI_PER_POLI_CPU_TARGET) if n_gioc_att > 0 and GIOCATORI_ATTIVI_PER_POLI_CPU_TARGET > 0 else 0.
        prob_crea = PROB_CREAZIONE_POLI_CPU_PER_TICK
        for nome_p in list(self.polisportive.keys()):
            if nome_p in self.polisportive and self.polisportive[nome_p].is_cpu_controlled:
                 if self.polisportive[nome_p]._controlla_chiusura_poli_cpu(dt_sim_e, self): n_chiuse += 1
        for k in range(ticks):
            if len(self.polisportive) < lim_poli and caso(prob_crea):
                dt_tick = dt_sim_s + datetime.timedelta(days=(k + 1) * gg_tick)
                nome_n = self._crea_nuova_poli_cpu_interna(dt_tick)
                if nome_n: n_cr_sess += 1; n_cr_ciclo += 1

        # Aggiorna Date Simulatore
        self.datetime_corrente_simulazione = dt_sim_e
        self.datetime_ultimo_run_reale = now

        # Aggiornamento stato finale (ICV) (include forza perché in icv_base/icv_allenato)
        for gid in ids_vivi:
             try:
                 if gid in self.giocatori: self.giocatori[gid].aggiorna_icv()
             except KeyError: pass
             except Exception as e_icv: print(f"ERR aggiornamento ICV finale GID {gid}: {e_icv}")

        # Creazione Nuovi Giocatori
        self.nuovi_giocatori_sessione.clear(); n_nuovi_creati_ciclo = 0
        try:
            inf,sup=CREA_NUOVI_PER_TICK_RANGE; min_n=inf*ticks; max_n=sup*ticks
            n_des=random.randrange(min_n,max_n+1) if max_n>=min_n else min_n
            n_crea=min(n_des,MAX_NUOVI_GIOCATORI_PER_AVVIO)
            if n_crea < n_des: print(f"INFO: Nuovi limitati a {MAX_NUOVI_GIOCATORI_PER_AVVIO} (desiderati: {n_des}).")
            if n_crea > 0:
                 num_da_creare_effettivo = n_crea
                 self._crea_giocatori_casuali(num_da_creare_effettivo, self.datetime_corrente_simulazione)
                 n_nuovi_creati_ciclo = len(self.nuovi_giocatori_sessione)
        except Exception as e_crea: print(f"ERRORE calcolo/creazione nuovi: {e_crea}"); traceback.print_exc()

        # Aggiorna ICT e Gloria Polisportive
        self._aggiorna_stato_post_cpu()

        # Report Riepilogativo Tick
        print("\n--- Riepilogo Avanzamento Tick ---")
        if n_rit > 0: print(f"* Ritirati (età): {n_rit}")
        if n_usciti_prem > 0: print(f"* Usciti Prematuramente: {n_usciti_prem}")
        if n_dec > 0: print(f"* Deceduti (età): {n_dec}")
        if n_nuovi_creati_ciclo > 0: print(f"* Nuovi giocatori: {n_nuovi_creati_ciclo}")
        if n_chiuse > 0: print(f"* Poli CPU chiuse: {n_chiuse}")
        if n_cr_ciclo > 0: print(f"* Poli CPU create: {n_cr_ciclo}")
        if n_tess_cpu > 0: print(f"* CPU Tesserati: {n_tess_cpu}")
        if n_esp_cpu > 0: print(f"* CPU Espulsi: {n_esp_cpu}")
        print("-" * 30)

    def concludi_sessione(self):
        print("\nInizio operazioni finali...")
        self.salva_dati()
        h,m,s=converti_in_tempo(time.time()-self.start_time); print(f"\nSessione: {h}h {m}m {s}s."); print(f"{self.comandi_eseguiti} comandi."); print("Arrivederci!")

    def _trova_prossimo_id_libero(self) -> int:
        """Trova il primo ID intero libero partendo da 1."""
        next_id = 1
        while next_id in self.giocatori:
            next_id += 1
        return next_id

    def _crea_giocatori_casuali(self, quanti: int, dt_creaz: datetime.datetime):
        """Crea un numero specificato di giocatori casuali."""
        if quanti <= 0: return
        print(f" -> Generazione {quanti} nuovi giocatori...")
        n_cr = 0
        for _ in range(quanti):
            new_id = self._trova_prossimo_id_libero()
            is_ipo = caso(PROBABILITA_IPOVEDENTE_CREAZIONE)
            try:
                # Giocatore.__init__ ora gestisce forza_base/forza_allenata
                nuovo = Giocatore(id_giocatore=new_id, datetime_creazione_sim=dt_creaz, ipovedente=is_ipo)
                self.giocatori[new_id] = nuovo
                self.nuovi_giocatori_sessione.append(new_id)
                n_cr += 1
            except Exception as e: print(f"ERR creaz GID {new_id}: {e}"); traceback.print_exc()
        print(f" -> Creati {n_cr} nuovi giocatori.")

    def _chiedi_password(self, prompt: str="Password? ") -> str:
        try: return dgt(prompt,smin=1,smax=30,pwd=True)
        except TypeError: return dgt(prompt,smin=1,smax=30)
        except Exception as e: print(f"Err chiedi_pwd: {e}"); return ""

    def visualizza_lista(self, lista: List[Any], titolo: str, tipo: str="giocatore"):
        if not lista: print(f"\n\t--- Lista '{titolo}' vuota. ---"); return
        print(f"\n--- {titolo} ({len(lista)} elementi) ---"); n_st=0; ids_mostr=set()
        items=reversed(lista) if tipo=="messaggio" or titolo.startswith("Lista Nuovi") else lista
        for item in items:
            id_n=None; somm="El. non valido."; mostra=True
            try:
                if tipo=="giocatore" and isinstance(item,int): id_n=item; somm=self.giocatori[id_n].sommario() if id_n in self.giocatori else f"ID:{id_n:<4d} {'DECEDUTO' if id_n in self._ids_morti_processati_sessione else 'NON TROVATO'}"
                elif tipo=="polisportiva" and isinstance(item,str): id_n=item; somm=self.polisportive[id_n].sommario(self.datetime_corrente_simulazione) if id_n in self.polisportive else f"{id_n:<30} NON TROVATA"
                elif tipo=="messaggio" and isinstance(item,tuple) and len(item)==2:
                    id_n=item[0]
                    if id_n in ids_mostr: mostra=False
                    else: ids_mostr.add(id_n); somm=item[1]
                else: mostra=False; somm=f"Non visualizzabile: {item}"
            except Exception as e: somm=f"Errore vis {item}: {e}"
            if mostra:
                print(somm); n_st+=1
                if n_st % PAGINAZIONE_LISTE == 0 and n_st < len(lista):
                    try:
                        k=key(f"...INVIO ({n_st}/{len(lista)}), E=Esci: ")
                        if k is not None and k.lower()=='e': break
                    except EOFError: break
        print("-"*(len(titolo)+8))

    def cerca_giocatori(self):
        print("\n--- Ricerca Giocatori ---"); ops={"I":"Intero DB","A":"Attivi","L":"Liberi","T":"Tesserati","N":"Nuovi","R":"Ritirati","M":"Morti","V":"VLT"}
        sel_l=menu(d=ops,p="Cerca in (ESC=Annulla): ",keyslist=False,show=True,pager=10)
        if sel_l is None: print("Annullato."); return
        if sel_l and sel_l != '?': self.comandi_eseguiti += 1
        ids=[]; desc=ops.get(sel_l,"?"); morti=self._ids_morti_processati_sessione
        if sel_l=='I': ids=list(self.giocatori.keys())
        elif sel_l=='A': ids=[gid for gid,g in self.giocatori.items() if gid not in morti and not g.ritirato]
        elif sel_l=='L': ids=[gid for gid,g in self.giocatori.items() if gid not in morti and not g.ritirato and g.appartenenza=="*"]
        elif sel_l=='T': ids=[gid for gid,g in self.giocatori.items() if gid not in morti and not g.ritirato and g.appartenenza!="*"]
        elif sel_l=='N': ids=list(self.nuovi_giocatori_sessione)
        elif sel_l=='R': ids=[gid for gid,g in self.giocatori.items() if gid not in morti and g.ritirato]
        elif sel_l=='M': ids=list(morti)
        elif sel_l=='V': ids=list(self.risultati_ultima_ricerca)
        else: print("Sel. lista non valida."); return
        if not ids: print(f"\n\tLista '{desc}' vuota."); return
        print(f"\nRicerca in: {desc} ({len(ids)} gioc.).")
        try:
            sel_a=menu(d=MENU_RICERCA,p="Caratteristica (ESC=Annulla)? ",keyslist=True,pager=PAGINAZIONE_LISTE,show=True,show_on_filter=True)
            if sel_a is None: print("Annullato."); return
            if sel_a and sel_a != '?': self.comandi_eseguiti += 1
            attr_l=MAPPA_RICERCA_ATTRIBUTI.get(sel_a)
            if not attr_l: print("\n\tErrore mappa."); return
            nome_d=MENU_RICERCA.get(sel_a,"?").replace(';',''); res=[]
            if attr_l=="ipovedente": val=key(f"Cercare chi È '{nome_d}'(s/N)? ").lower()=='s'; print(f"Ricerca '{nome_d}'={val}"); res=[gid for gid in ids if gid in self.giocatori and getattr(self.giocatori[gid],attr_l,False)==val]
            elif attr_l in ["nome","cognome"]: txt=dgt(f"'{nome_d}' contiene: ").lower(); print(f"Ricerca '{nome_d}'~'{txt}'..."); res=[gid for gid in ids if gid in self.giocatori and txt in getattr(self.giocatori[gid],attr_l,"").lower()] if txt else []
            else: # Numerico
                op=dgt(f"'{nome_d}' (>/<) di? ","s",smax=1)
                if op not in['>','<']: print("\tUsa > o <."); return
                tipo="f"; min_v=-float('inf'); max_v=float('inf')
                if attr_l=="eta_anni": min_v,max_v=0.,ETA_MAX_MORTE_ANNI+10
                # <-- AGGIUNTO FORZA - Gestisci limiti PRC, RST, FOR
                elif attr_l in ["precisione_totale", "resistenza_totale", "forza_totale"]:
                     min_v,max_v=0., MAX_TOTALE_PRECISIONE_RESISTENZA
                elif "_totale" in attr_l: min_v,max_v=0., MAX_TOTALE_SKILL_GIOCO
                elif attr_l=="indice_collettivo_valore": min_v,max_v=0.,1000
                soglia=dgt(f"Valore({min_v:.1f}-{max_v:.1f})? ",tipo,fmin=min_v,fmax=max_v); print(f"Ricerca '{nome_d}'{op}{soglia}...")
                for gid in ids:
                    if gid not in self.giocatori: continue
                    g=self.giocatori[gid]; val_g=0.
                    try:
                        if attr_l=="eta_anni": val_g=g.eta_anni
                        # <-- AGGIUNTO FORZA - Usa _get_valore_totale per PRC, RST, FOR
                        elif attr_l in ["precisione_totale", "resistenza_totale", "forza_totale"]:
                            val_g=g._get_valore_totale(attr_l.replace('_totale','_base'))
                        elif "_totale" in attr_l: val_g=g._get_valore_totale(attr_l.replace('_totale','_base'))
                        else: val_g=getattr(g,attr_l,0.)
                        val_g=float(val_g)
                        if (op=='>' and val_g>soglia) or (op=='<' and val_g<=soglia): res.append(gid)
                    except: continue
            self.risultati_ultima_ricerca=res; n_res=len(res); print(f"\nRisultati: {n_res}."+(" Vedi VLT." if n_res>0 else ""))
        except EOFError: print("\nAnnullato.")
        except Exception as e: print(f"\nERRORE ricerca: {e}"); traceback.print_exc()

    def _esegui_logica_cpu_polisportive(self) -> Tuple[int, int]:
        liberi=self._trova_giocatori_liberi_ordinati()
        n_tess_cpu_tot = 0; n_esp_cpu_tot = 0
        for nome_p in list(self.polisportive.keys()):
            if nome_p not in self.polisportive or not self.polisportive[nome_p].is_cpu_controlled: continue
            poli=self.polisportive[nome_p]
            # Tess.
            while poli.movimenti_oggi<LIMITE_MOVIMENTI_PER_TICK and len(poli.tesserati)<poli.maxtesserati:
                cand_ok=None; gid_t=-1; tent=False; ids_lib_rim=list(liberi.keys())
                if not ids_lib_rim: break
                for gid_c in ids_lib_rim:
                    if gid_c not in liberi: continue
                    cand=liberi[gid_c]; g_r=cand.gloria_richiesta; g_p=int(g_r*.9) if cand.ipovedente else g_r
                    if cand.appartenenza=="*" and g_p<=poli.gloria:
                        poli.movimenti_oggi+=1; poli.datetime_ultimo_movimento=datetime.datetime.now(); tent=True
                        if caso(self._calcola_probabilita_accettazione(poli.gloria,g_r)): cand_ok=cand; gid_t=gid_c
                        break
                if tent:
                    if cand_ok: cand_ok.appartenenza=poli.nome; poli.aggiungi_tesserato(gid_t,cand_ok.indice_collettivo_valore); del liberi[gid_t]; n_tess_cpu_tot += 1
                else: break
            # Esp.
            while poli.movimenti_oggi<LIMITE_MOVIMENTI_PER_TICK and len(poli.tesserati)>=poli.maxtesserati:
                pegg_gid=-1; min_icv=float('inf'); tess_v=[tid for tid in poli.tesserati if tid in self.giocatori and tid not in self._ids_morti_processati_sessione]
                if not tess_v: break
                for tid in tess_v:
                    icv=self.giocatori[tid].indice_collettivo_valore
                    if icv<min_icv: min_icv=icv; pegg_gid=tid
                if pegg_gid!=-1:
                    g_p=self.giocatori[pegg_gid]
                    poli.movimenti_oggi+=1; poli.datetime_ultimo_movimento=datetime.datetime.now()
                    poli.rimuovi_tesserato(pegg_gid,min_icv); g_p.appartenenza="*" ; n_esp_cpu_tot += 1
                else: break
        return n_tess_cpu_tot, n_esp_cpu_tot

    def _trova_giocatori_liberi_ordinati(self) -> Dict[int, Giocatore]:
        liberi={gid: g for gid,g in self.giocatori.items() if g.appartenenza=="*" and not g.ritirato and gid not in self._ids_morti_processati_sessione}
        return dict(sorted(liberi.items(), key=lambda item: item[1].indice_collettivo_valore, reverse=True))

    def statistica_globale(self):
        """Mostra statistiche aggregate e i migliori giocatori/polisportive."""
        print("\n--- Statistica Globale ---")
        morti = self._ids_morti_processati_sessione
        attivi = {gid: g for gid, g in self.giocatori.items() if gid not in morti and not g.ritirato}
        n_att = len(attivi)
        print("\n[ Statistiche Giocatori Attivi ]")
        if n_att == 0: print("Nessun giocatore attivo trovato.")
        else:
            m, f, et_g, et_m, et_f, icv_t, n_t, n_i = 0, 0, 0, 0, 0, 0., 0, 0
            nomi, cogn = set(), set()
            for g in attivi.values():
                et_g += g.eta; icv_t += g.indice_collettivo_valore; nomi.add(g.nome); cogn.add(g.cognome)
                if g.sesso == 'm': m += 1; et_m += g.eta
                else: f += 1; et_f += g.eta
                if g.appartenenza != "*": n_t += 1
                if g.ipovedente: n_i += 1
            pm = m*100./n_att if n_att>0 else 0.; pf = f*100./n_att if n_att>0 else 0.
            pt = n_t*100./n_att if n_att>0 else 0.; pl = 100. - pt; pipo = n_i*100./n_att if n_att>0 else 0.
            e_m_a = (et_g/n_att/ANNO_SIMULAZIONE_GIORNI) if n_att>0 and ANNO_SIMULAZIONE_GIORNI>0 else 0.
            e_m_m = (et_m/m/ANNO_SIMULAZIONE_GIORNI) if m>0 and ANNO_SIMULAZIONE_GIORNI>0 else 0.
            e_m_f = (et_f/f/ANNO_SIMULAZIONE_GIORNI) if f>0 and ANNO_SIMULAZIONE_GIORNI>0 else 0.
            icv_m = icv_t/n_att if n_att>0 else 0.
            print(f" Popolazione: {n_att}"); print(f" Sesso: {m} Uomini ({pm:.1f}%), {f} Donne ({pf:.1f}%)")
            print(f" Età media (anni sim): {e_m_a:.1f} (U:{e_m_m:.1f}, D:{e_m_f:.1f})")
            print(f" Stato: {n_t} Tesserati ({pt:.1f}%), {n_att - n_t} Liberi ({pl:.1f}%)")
            print(f" ICV medio: {icv_m:.2f}"); print(f" Ipovedenti: {n_i} ({pipo:.1f}%)"); print(f" Nomi Unici: {len(nomi)}, Cognomi Unici: {len(cogn)}")

        print("\n[ TOP Players per Caratteristica (Attivi) ]")
        if n_att > 0:
            # ATTRIBUTI_BASE_CON_ALLENABILI ora include forza_base
            top = {sk_base: (-1.0, None) for sk_base in sorted(list(ATTRIBUTI_BASE_CON_ALLENABILI))}
            for gid, player in attivi.items():
                for sk_base in top:
                    total_value = player._get_valore_totale(sk_base); current_max, _ = top[sk_base]
                    if total_value > current_max: top[sk_base] = (total_value, gid)
            print(f"{'Caratteristica':<25} {'Valore':<7} {'%':<5} {'ID':<5} {'Nome Giocatore':<30} {'Età(A/M/G)':<10} {'Club'}"); print("-" * 97)
            for sk_base, (max_val, p_id) in top.items():
                if p_id is not None and p_id in self.giocatori:
                    p = self.giocatori[p_id]; d_name = NOME_ATTR_TO_DISPLAY_MAP.get(sk_base, sk_base.replace('_base','').title()); nome_c = f"{p.nome} {p.cognome}"[:30]
                    eta_s = _formatta_eta_sim(p.eta, True); club = "Libero" if p.appartenenza=="*" else p.appartenenza[:15]
                    # <-- AGGIUNTO FORZA - Determina is_fisica per limite corretto
                    is_f = sk_base in CARATTERISTICHE_FISICHE_BASE
                    max_t = MAX_TOTALE_PRECISIONE_RESISTENZA if is_f else MAX_TOTALE_SKILL_GIOCO
                    perc = f"({(max_val*100./max_t if max_t>0 else 0.):.0f}%)"; print(f"{d_name:<25} {max_val:6.2f} {perc:<5} {p_id:<5} {nome_c:<30} {eta_s:<10} {club}")
                else: d_name = NOME_ATTR_TO_DISPLAY_MAP.get(sk_base, sk_base.replace('_base','').title()); print(f"{d_name:<25} {'N/D':<7} {'-':<5} {'-':<5} {'Nessuno':<30} {'-':<10} {'-'}")
        else: print("Nessun giocatore attivo per TOP Players.")

        print("\n[ TOP Polisportiva per ICT ]")
        if not self.polisportive: print("Nessuna polisportiva esistente.")
        else:
            top_p = max(self.polisportive.values(), key=lambda p: p.indicecollettivotesserati, default=None)
            if top_p: print(f"  Migliore Polisportiva: {top_p.nome}\n  Indice Collettivo Tesserati (ICT): {top_p.indicecollettivotesserati:.2f}")
            else: print("  Impossibile determinare TOP Polisportiva.")
        print("-" * 75)

    def visualizza_top_10(self):
        print("\n"+"="*30+" TOP 10 "+"="*30)
        print("\n--- TOP 10 Giocatori (Attivi, ICV) ---")
        attivi=[g for gid,g in self.giocatori.items() if gid not in self._ids_morti_processati_sessione and not g.ritirato]
        if not attivi: print("\n\tNessun attivo.")
        else:
            top10_g=sorted(attivi,key=lambda g:g.indice_collettivo_valore,reverse=True)[:10]
            print(f"{'Pos':<4} {'ID':<5} {'Nome Cognome':<30} {'ICV':<8} {'Età(A/M/G)':<10} {'Club'}"); print("-"*80)
            for i,g in enumerate(top10_g,1): n=f"{g.nome} {g.cognome}"[:30]; icv=f"{g.indice_collettivo_valore:.1f}"; eta=_formatta_eta_sim(g.eta,True); club="Libero" if g.appartenenza=="*" else g.appartenenza[:15]; print(f"{i:<4} {g.id:<5} {n:<30} {icv:<8} {eta:<10} {club}")
        print("\n--- TOP 10 Polisportive (ICT) ---")
        if not self.polisportive: print("\n\tNessuna.")
        else:
            top10_p=sorted(self.polisportive.values(),key=lambda p:p.indicecollettivotesserati,reverse=True)[:10]
            print(f"{'Pos':<4} {'Nome Polisportiva':<30} {'ICT':<10} {'Tess':<10} {'Età(A/M/G)'}"); print("-"*85)
            for i,p in enumerate(top10_p,1): ic=f"{p.indicecollettivotesserati:.1f}"; ts=f"{len(p.tesserati)}/{p.maxtesserati}"; cpu=" [CPU]" if p.is_cpu_controlled else ""; nm=(p.nome+cpu)[:30]; eta=p.sommario(self.datetime_corrente_simulazione).split('(')[1].split(')')[0]; print(f"{i:<4} {nm:<30} {ic:<10} {ts:<10} {eta}")
        print("\n"+"="*85)

    def run(self):
        """Loop principale del gioco."""
        now = datetime.datetime.now(); print("\n" + "="*75); print(f" MESS - Versione: {VERSIONE}")
        sim_dt_str = self.datetime_corrente_simulazione.strftime('%Y-%m-%d %H:%M') if isinstance(self.datetime_corrente_simulazione, datetime.datetime) else "N/D"
        print(f" Data Reale: {now:%Y-%m-%d %H:%M}, Data Sim: {sim_dt_str}"); print("="*75)
        try:
            if hasattr(self,'datetime_ultimo_run_reale') and isinstance(self.datetime_ultimo_run_reale,datetime.datetime):
                if (now - self.datetime_ultimo_run_reale).total_seconds() < (8 * 3600 - 60): self._mostra_prossimo_sblocco_attivita(); print("-" * 75)
        except Exception as e: print(f"DEBUG: Err controllo sblocco: {e}"); print("-"*75)
        cmd_map = {"VSG":self.visualizza_scheda_giocatore,"VRG":self.visualizza_riepilogo_giocatori,"CLA":self.visualizza_classifica_giocatori,
                   "VLN":lambda:self.visualizza_lista(self.nuovi_giocatori_sessione,"Lista Nuovi Sessione","giocatore"),
                   "VLM":lambda:self.visualizza_lista(self.giocatori_morti_sessione,"Lista Morti Sessione","messaggio"),
                   "VLR":lambda:self.visualizza_lista(self.giocatori_ritirati_sessione,"Lista Ritirati Sessione","messaggio"),
                   "VLT":lambda:self.visualizza_lista(self.risultati_ultima_ricerca,"Risultati Ultima Ricerca","giocatore"),
                   "MPO":self.menu_polisportive,"CEG":self.cerca_giocatori,"CTT":self._copia_tesserati_attivi_in_vlt,
                   "AGT":self.allenamento_giocatori_tesserati,"OPA":self.organizza_partita_amichevole,"SGG":self.statistica_globale,
                   "TOP":self.visualizza_top_10,"DTS":lambda: print(f"\nData/Ora Sim: {self.datetime_corrente_simulazione:%Y-%m-%d %H:%M:%S}")}
        running = True
        while running:
            try:
                poli_a = self.miapolisportiva_attiva.nome if self.miapolisportiva_attiva else "Nessuna"
                n_liberi = 0; n_tesserati = 0; n_non_giocanti = 0; n_tot = len(self.giocatori)
                morti_sessione = self._ids_morti_processati_sessione
                for gid, g in self.giocatori.items():
                    if gid not in morti_sessione:
                        if g.ritirato or g.infortunato: n_non_giocanti += 1
                        elif g.appartenenza == "*": n_liberi += 1
                        else: n_tesserati += 1
                prompt=f"(MEN)<{poli_a}> Gioc(L:{n_liberi}/T:{n_tesserati}/N:{n_non_giocanti}/Tot:{n_tot})> "
                scelta=menu(d=MAINMENU,p=prompt,keyslist=False,show_on_filter=True,pager=PAGINAZIONE_LISTE,show=False,ntf="Comando non valido")
                self.comandi_eseguiti += 1
                if scelta is None or scelta=='': running=False
                elif scelta=='?': print("\n--- Menu Principale ---"); [print(f" {k:<4}: {v}") for k,v in MAINMENU.items() if k]; print("-"*75); input("...INVIO...")
                elif scelta in cmd_map: cmd_map[scelta]()
                else: pass
            except EOFError: running=False; print("\nUscita (EOF)...")
            except KeyboardInterrupt: running=False; print("\nInterruzione...")
            except Exception as e:
                print(f"\nERRORE LOOP: {e}"); traceback.print_exc()
                try:
                    if key("Errore grave. Continuare(S/n)? ").lower()!='s': running=False
                except: running=False
        print("Uscita dal loop principale, chiamata a concludi_sessione...")
        self.concludi_sessione()

    def _copia_tesserati_attivi_in_vlt(self):
        if self.miapolisportiva_attiva:
            ids=[gid for gid in self.miapolisportiva_attiva.tesserati if gid in self.giocatori and gid not in self._ids_morti_processati_sessione and not self.giocatori[gid].ritirato]
            self.risultati_ultima_ricerca=ids; print(f"\nTrovati {len(ids)} tesserati ATTIVI. Copiati in VLT.")
        else: print("\n\tNessuna poli attiva.")

# --- Avvio ---
if __name__ == "__main__":
    try:
        sim = Simulatore()
        sim.run()
    except Exception as main_exception:
         print("\n--- ERRORE FATALE ESECUZIONE ---")
         print(f"Tipo: {type(main_exception).__name__}"); print(f"Msg: {main_exception}")
         traceback.print_exc(); print("\nProgramma terminato."); sys.exit(1)
