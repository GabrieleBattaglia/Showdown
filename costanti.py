"""
Costanti di MESS: regole, tarature e tabelle delle caratteristiche dei giocatori.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 2 del piano, dallo smontaggio di sd.py: sono le costanti che
stavano in testa al vecchio file, con i valori invariati. Le tabelle dei menu del programma
testuale stanno invece in cli.py, perché sono interfaccia e non regole.
Con la tappa 9, il 2026-10-07, il motore di partita è nuovo, e qui restano soltanto le regole
IBSA della decisione D25, le misure del tavolo e i numeri del mondo, cioè temperamento,
infortuni e valore complessivo; i numeri regolabili del motore stanno in motore/taratura.py.
Se ne sono andate le costanti del vecchio motore: il limite dei 17 punti, i margini, le soglie
scalate, la resistenza a gradini, la mappa delle difese e il registro unico delle partite.
Le parti nuove sono di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import datetime

from version import __version__

VERSIONE = __version__
# Il salvataggio del mondo, accanto al programma, e la sua copia di sicurezza.
# Dalla tappa 7 il mondo si salva compresso: lo stesso JSON firmato, otto volte più piccolo.
FILE_MONDO = "mess_mondo.json.gz"
FILE_MONDO_COPIA = FILE_MONDO + ".bak"
# I nomi del salvataggio non compresso, fino alla tappa 6: si leggono ancora, e il primo salvataggio li sostituisce.
FILE_MONDO_VECCHIO = "mess_mondo.json"
FILE_MONDO_COPIA_VECCHIO = FILE_MONDO_VECCHIO + ".bak"
FILE_NOMI_M = "nomi_maschili.txt"
FILE_NOMI_F = "nomi_femminili.txt"
FILE_COGNOMI = "cognomi.txt"
ANNO_SIMULAZIONE_GIORNI = 108
PROBABILITA_IPOVEDENTE_CREAZIONE = 65.0
# Polisportive del computer.
GIOCATORI_ATTIVI_PER_POLI_CPU_TARGET = 16.5
PROB_CREAZIONE_POLI_CPU_PER_TICK = 75.0
ETA_MINIMA_CHIUSURA_CPU_ANNI = 1.5
SOGLIA_GLORIA_BASSA_CHIUSURA = 60
SOGLIA_MINIMA_TESSERATI_CHIUSURA = 6
PROB_CHIUSURA_BASE_GIORNALIERA = 0.3
FATTORE_PROB_GLORIA = 0.5
FATTORE_PROB_TESSERATI = 0.5
MAX_PROB_CHIUSURA_GIORNALIERA = 2.0
# Le regole della partita, tappa 9, decisione D25, dal regolamento IBSA 2025-2028: il goal vale 2
# punti, ogni errore di gioco 1 all'avversario, la penalità 2. Il set lo vince chi arriva ad almeno
# 11 punti con 2 di scarto, senza tetto; ogni giocatore batte due volte di seguito.
PUNTI_PER_GOAL = 2
PUNTI_PER_FALLO_AVVERSARIO = 1
PUNTI_PER_PENALITA = 2
PUNTI_VITTORIA_SET_BASE = 11
PUNTI_VANTAGGIO_NECESSARI = 2
SERVIZI_CONSECUTIVI_PER_GIOCATORE = 2
# Gli incontri sono al meglio di 3 o di 5 set, e nell'ultimo set possibile si cambia campo a 6 punti.
SET_AMMESSI = (3, 5)
PUNTI_CAMBIO_CAMPO_ULTIMO_SET = 6
# La gara a squadre: un set a 31, tre servizi a testa, cambio campo a 16, squadre miste da 3 a 6.
PUNTI_SET_SQUADRE = 31
SERVIZI_SQUADRE = 3
PUNTI_CAMBIO_CAMPO_SQUADRE = 16
GIOCATORI_SQUADRA_MIN = 3
GIOCATORI_SQUADRA_MAX = 6
GIOCATORI_AL_TAVOLO = 3
# Time-out, sostituzioni, riscaldamento e pause, in secondi dove sono durate.
TIMEOUT_PER_SET = 1
TIMEOUT_SQUADRE = 1
SOSTITUZIONI_SQUADRE = 1
RISCALDAMENTO_SINGOLARE = 60
RISCALDAMENTO_SQUADRE = 90
AVVISI_RISCALDAMENTO_SINGOLARE = (45,)
# Nella gara a squadre l'arbitro chiama 30 secondi ogni 30 secondi, regola IBSA 22.3.
AVVISI_RISCALDAMENTO_SQUADRE = (30, 60)
DURATA_PAUSA = 60
AVVISO_PAUSA = 45
# Il tavolo IBSA, in centimetri: 366 per 122, lo schermo a metà, le porte alle testate.
LARGHEZZA_TAVOLO = 122
LUNGHEZZA_TAVOLO = 366
META_TAVOLO = 183
RAGGIO_CURVE = 23
ALTEZZA_SPONDE = 14
LUCE_SCHERMO = 10
ALTEZZA_SCHERMO = 42
RAGGIO_TASCA = 15
# L'area di porta è un semicerchio di 40 cm di diametro attorno alla tasca.
RAGGIO_AREA_PORTA = 20
SPORGENZA_TAVOLA_CONTATTO = 5
RAGGIO_PALLINA = 3
MEZZA_ZONA_CENTRALE = 20
DISTANZA_ARBITRO = 50
ASCOLTO_DIETRO_TESTATA = 40
VOLUME_RIFERIMENTO_CM = 150
# I colpi dello scambio e le battute, coi nomi delle caratteristiche senza _base.
COLPI_DELLO_SCAMBIO = ("lungolineasx", "lungolineadx", "diagonalesx", "diagonaledx", "singolaspondasx", "singolaspondadx",
                       "doppiaspondasx", "doppiaspondadx", "triplaspondasx", "triplaspondadx", "bomba")
COLPI_DI_BATTUTA = ("battutasx", "battutadx")
# Le modalità della vecchia firma di gioca_partita, che la facciata di partita.py conserva.
MODALITA_OUTPUT_RISULTATO = 'risultato'
MODALITA_OUTPUT_CONSOLE = 'console'
MODALITA_OUTPUT_FILE = 'file'
# Dalla tappa 9 ogni partita ha la sua cronaca, in un file di questa cartella.
CARTELLA_CRONACHE = "cronache"
NOME_FILE_LOG_USCITE = "vecchie_glorie.log"
# Il temperamento, da 0, calmissimo, a 100, impetuoso: nasce dal numero del giocatore e si calma
# con gli anni, dieci punti a 65 anni; la scheda lo dice a parole con queste fasce.
TEMPERAMENTO_MEDIA = 50.0
TEMPERAMENTO_DEVIAZIONE = 18.0
ETA_INIZIO_CALMA = 25.0
CALMA_PER_ANNO = 0.25
FASCE_TEMPERAMENTO = ((25.0, "molto calmo", False), (42.0, "calmo", True), (58.0, "equilibrato", True), (75.0, "focoso", True), (None, "impetuoso", True))
# Infortuni. Dalla tappa 9 crescono col carico della partita, e l'ambidestro ha una probabilità un
# po' più bassa al posto di quella divisa per cinque.
PROB_INFORTUNIO_BASE_PER_PARTITA = 0.015
ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI = 30.0
ETA_MAX_PROB_INFORTUNIO_ANNI = 75.0
PROB_INFORTUNIO_AUMENTO_MAX_PERC = 10.0
INFORTUNIO_DURATA_MIN_GIORNI = 3
INFORTUNIO_DURATA_MAX_GIORNI_ETA = 35
INFORTUNIO_MALUS_MAX_RESISTENZA = 10
FATTORE_INFORTUNIO_AMBIDESTRO = 0.8
# Le azioni di un incontro al meglio dei 3 per cui il carico vale 1. Era 130, tarato sulla sola
# popolazione di prova allenata, dove le partite sono corte; nel mondo salvato e fra giocatori mai
# allenati le partite sono più lunghe, e gli infortuni uscivano dal 10 per cento in più di prima.
# Con 150 stanno nella banda in tutti e tre i mondi.
AZIONI_RIFERIMENTO_INFORTUNIO = 150
CARICO_INFORTUNIO_MINIMO = 0.7
CARICO_INFORTUNIO_MASSIMO = 1.5
# Le sedi degli infortuni: codice, frase con l'articolo, braccio, peso per il destrimano e fattore
# di durata. Per il mancino i pesi delle braccia si scambiano, per l'ambidestro se ne fa la media.
# La sede non precisata viene soltanto dalla migrazione al formato 5, e ferma tutti come prima.
SEDE_NON_PRECISATA = "non_precisata"
SEDI_INFORTUNIO = (
    ("spalla_dx", "alla spalla destra", "dx", 12, 1.0),
    ("gomito_dx", "al gomito destro", "dx", 9, 1.0),
    ("polso_dx", "al polso destro", "dx", 9, 1.0),
    ("spalla_sx", "alla spalla sinistra", "sx", 3, 1.0),
    ("gomito_sx", "al gomito sinistro", "sx", 2, 1.0),
    ("polso_sx", "al polso sinistro", "sx", 3, 1.0),
    ("schiena", "alla schiena", None, 22, 1.1),
    ("ginocchio", "al ginocchio", None, 20, 1.2),
    ("caviglia", "alla caviglia", None, 20, 0.8),
)
# Punti esperienza guadagnati in partita.
XP_VITTORIA_2_0 = 4
XP_VITTORIA_2_1 = 3
XP_SCONFITTA_1_2 = 2
XP_SCONFITTA_0_2 = 1
XP_VITTORIA_3_0 = 7
XP_VITTORIA_3_1 = 6
XP_VITTORIA_3_2 = 5
XP_SCONFITTA_2_3 = 4
XP_SCONFITTA_1_3 = 3
XP_SCONFITTA_0_3 = 2
XP_BONUS_TORNEO = 3
XP_BONUS_UNDERDOG = 1
ICV_DIFF_PERC_UNDERDOG = 25.0
# Costo dell'allenamento in punti esperienza.
XP_COSTO_SKILL_BREAKPOINTS = {0: 25, 9: 100, 15: 200, 19: 500}  # Breakpoint per skill 0-20
XP_COSTO_FISICO_MOLTIPL = 2.0  # Si applica a precisione, resistenza e forza
XP_SCONTO_IPOVEDENTI_PERC = 7.0
MAX_ALLENATO_FISICO = 5.0  # Per precisione, resistenza e forza
MAX_ALLENATO_SKILL = 20.0  # Per le altre skill
# Gloria richiesta dal giocatore.
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
# Gli ipovedenti chiedono il 10 per cento di gloria in meno, a tutti: decisione D19 della tappa 7.
FATTORE_GLORIA_RICHIESTA_IPOVEDENTE = 0.90
# Probabilità che un giocatore accetti il tesseramento.
ACCETTAZIONE_REL_DIFF_THRESHOLD = 0.30
ACCETTAZIONE_PROB_MIN = 3.0
ACCETTAZIONE_PROB_MAX = 97.0
ACCETTAZIONE_PROB_MID = 50.0
# Età in anni del simulatore.
ETA_MIN_CREAZIONE_ANNI = 9.0
ETA_MAX_CREAZIONE_ANNI = 45.0
AGING_START_AGE_ANNI = 50.0
ETA_MIN_RITIRO_ANNI = 58.0
ETA_MAX_RITIRO_ANNI = 75.0
ETA_MIN_MORTE_ANNI = 70.0
ETA_MAX_MORTE_ANNI = 103.0
AGING_PEAK_AGE_ANNI = 90.0
PROB_USCITA_PREMATURA_GIORNALIERA = 0.0075


def giorni_da_anni(anni):
    """Converte anni del simulatore in giorni del simulatore."""
    return int(anni * ANNO_SIMULAZIONE_GIORNI) if ANNO_SIMULAZIONE_GIORNI > 0 else int(anni * 365.25)


# Le età chiave in giorni del simulatore.
ETA_MIN_CREAZIONE_GIORNI = giorni_da_anni(ETA_MIN_CREAZIONE_ANNI)
ETA_MAX_CREAZIONE_GIORNI = giorni_da_anni(ETA_MAX_CREAZIONE_ANNI)
AGING_START_AGE_GIORNI = giorni_da_anni(AGING_START_AGE_ANNI)
ETA_MIN_RITIRO_GIORNI = giorni_da_anni(ETA_MIN_RITIRO_ANNI)
ETA_MAX_RITIRO_GIORNI = giorni_da_anni(ETA_MAX_RITIRO_ANNI)
ETA_MIN_MORTE_GIORNI = giorni_da_anni(ETA_MIN_MORTE_ANNI)
ETA_MAX_MORTE_GIORNI = giorni_da_anni(ETA_MAX_MORTE_ANNI)
AGING_PEAK_AGE_GIORNI = giorni_da_anni(AGING_PEAK_AGE_ANNI)
# Invecchiamento e tetti delle caratteristiche.
MAX_AGING_REDUCTION_FACTOR_PER_ANNO_SIM = 0.018
MAX_SKILL_VALUE = 20.0
MAX_PRECISIONE_RESISTENZA = 5.0  # Limite base per precisione, resistenza e forza
MAX_TOTALE_PRECISIONE_RESISTENZA = 10.0  # Limite totale, base più allenato, per precisione, resistenza e forza
MAX_TOTALE_SKILL_GIOCO = 40.0  # Limite totale per le altre skill
# Limiti vari.
MAX_XP_PER_ALLENAMENTO = 15000
MAX_TESSERATI_POLISPORTIVA = 15
PAGINAZIONE_LISTE = 25
LIMITE_MOVIMENTI_PER_TICK = 5
# La probabilità, in percentuale, che in un giorno una polisportiva del computer a rosa piena provi
# a tesserare un libero più forte del tesserato che le serve meno: decisione D19 della tappa 7.
PROB_SCAMBIO_CPU_GIORNALIERA = 10.0
# Quanti caratteri può avere il nome di una polisportiva.
NOME_POLISPORTIVA_MIN = 5
NOME_POLISPORTIVA_MAX = 50
# L'economia, tappa 8, decisione D22. Cifre in euro; quelle di partenza si tarano con la simulazione lunga.
CAPITALE_INIZIALE = 20_000
SPONSOR_PER_GLORIA = 35
STIPENDIO_DI_RIFERIMENTO = 200
VALORE_DI_RIFERIMENTO = 140
SCALA_STIPENDIO = 40
STIPENDIO_MINIMO = 50
AUMENTO_STIPENDIO_PER_ESPERIENZA = 0.03
MESI_DI_INGAGGIO = 2
REPUTAZIONE_MINIMA = 0.5
REPUTAZIONE_MASSIMA = 2.0
MESI_DI_VALORE = 6
# Fedeltà ed esperienza crescono ogni mese passato in una polisportiva; la fedeltà va da 0 a 100.
FEDELTA_PER_MESE = 2.0
FEDELTA_MASSIMA = 100.0
ESPERIENZA_PER_MESE = 0.1
ESPERIENZA_MASSIMA = 20.0
# Ogni 25 punti di fedeltà, un mese di pazienza in più oltre al primo.
FEDELTA_PER_MESE_DI_PAZIENZA = 25.0
# Un giocatore su cento nasce bandiera, e lo diventa davvero quando la fedeltà al club arriva qui.
PROBABILITA_BANDIERA_CREAZIONE = 1.0
FEDELTA_BANDIERA = 80.0
# Quanti bilanci mensili tiene una polisportiva.
BILANCI_CONSERVATI = 12
# Il computer offre il 15 per cento in più dell'ingaggio chiesto, tiene in cassa un mese di
# stipendi, e si permette un monte stipendi pari allo sponsor più un ventiquattresimo della cassa.
RIALZO_CPU = 1.15
MESI_DI_RISERVA_CPU = 1
PARTI_DI_CASSA_PER_STIPENDI = 24
# Quanti candidati troppo cari il computer scorre in un giorno, prima di lasciar perdere.
SCARTI_MASSIMI_CPU = 30
# Un'offerta d'acquisto per un tesserato del computer, decisione D23: la polisportiva vuole il suo
# valore di mercato, e fino a metà in più per il più forte della rosa.
IMPORTANZA_MASSIMA = 0.5
# La data dell'ultimo movimento di una polisportiva che non ne ha mai fatti.
DATA_NESSUN_MOVIMENTO = datetime.datetime(1900, 1, 1)  # noqa: DTZ001 - data segnaposto, fuori da ogni fuso
NUM_GIOCATORI_INIZIALI = 50
CREA_NUOVI_PER_TICK_RANGE = (1, 7)
# Le caratteristiche allenabili, con la sigla del menu di allenamento.
ATTRIBUTI_ALLENABILI_MAP = {
    "prc": "precisione_allenata", "rst": "resistenza_allenata", "for": "forza_allenata",
    "dfa": "difesa_allenata",
    "tpa": "tenutapaletta_allenata", "csa": "chiusurasx_allenata", "cda": "chiusuradx_allenata",
    "bsa": "bloccosx_allenata", "bda": "bloccodx_allenata", "cpa": "controllopalla_allenata",
    "ata": "attacco_allenata", "btsa": "battutasx_allenata", "btda": "battutadx_allenata",
    "ba": "bomba_allenata", "llsa": "lungolineasx_allenata", "llda": "lungolineadx_allenata",
    "dsa": "diagonalesx_allenata", "dda": "diagonaledx_allenata", "sss": "singolaspondasx_allenata",
    "ssd": "singolaspondadx_allenata", "dpsa": "doppiaspondasx_allenata", "dpda": "doppiaspondadx_allenata",
    "tpsa": "triplaspondasx_allenata", "tpda": "triplaspondadx_allenata",
}
# Elenchi ordinati e non insiemi: l'ordine in cui vengono percorsi decide quali tiri del caso
# toccano a quali caratteristiche alla nascita di un giocatore, e l'ordine di un insieme di
# stringhe cambia da un avvio all'altro di Python. Con questi elenchi lo stesso seme dà sempre
# lo stesso mondo, problema P17 del piano, risolto il 2026-10-06 con la tappa 3.
ATTRIBUTI_ALLENABILI: tuple[str, ...] = tuple(ATTRIBUTI_ALLENABILI_MAP.values())
ATTRIBUTI_BASE_CON_ALLENABILI: tuple[str, ...] = tuple(attr.replace('_allenata', '_base') for attr in ATTRIBUTI_ALLENABILI)
ATTRIBUTI_INVECCHIABILI: tuple[str, ...] = ATTRIBUTI_BASE_CON_ALLENABILI + ATTRIBUTI_ALLENABILI
# Le caratteristiche fisiche, compresa la forza, e i gruppi di quelle di gioco.
ALLENATE_FISICHE = ("precisione_allenata", "resistenza_allenata", "forza_allenata")
CARATTERISTICHE_FISICHE_BASE = ["precisione_base", "resistenza_base", "forza_base"]
CARATTERISTICHE_DIFESA_BASE = ["chiusurasx_base", "bloccosx_base", "bloccodx_base", "chiusuradx_base"]
CARATTERISTICHE_ATTACCO_BASE = [
    "battutasx_base", "lungolineasx_base", "diagonalesx_base", "singolaspondasx_base",
    "doppiaspondasx_base", "triplaspondasx_base", "bomba_base", "triplaspondadx_base",
    "doppiaspondadx_base", "singolaspondadx_base", "diagonaledx_base", "lungolineadx_base", "battutadx_base"
]
CARATTERISTICHE_CONTROLLO_BASE = ["difesa_base", "controllopalla_base", "tenutapaletta_base", "attacco_base"]
# Autoallenamento dei giocatori liberi e delle polisportive del computer.
ETA_GIOVANE_MAX_GIORNI = giorni_da_anni(20)
ETA_ANZIANO_MIN_GIORNI = AGING_START_AGE_GIORNI
PROB_SEGUE_ARCHETIPO = 80.0
PROB_ARCHETIPO_CASUALE_CREAZIONE = 10.0
ARCHETIPI_ALLENAMENTO = {
    "AttaccantePuro": {"desc": "Massimizza danno offensivo.", "priorita": ["attacco_allenata", "bomba_allenata", "diagonaledx_allenata", "diagonalesx_allenata", "lungolineadx_allenata", "lungolineasx_allenata", "precisione_allenata"], "strategia_scelta": "piu_bassa_prioritaria", "strategia_spesa": {"tipo": "percentuale", "valore": 25, "max_xp": 750}, "influenza_eta": {"anziano": "piu_economica_prioritaria"}},
    "DifensoreRoccioso": {"desc": "Focus su difesa e blocchi.", "priorita": ["difesa_allenata", "chiusuradx_allenata", "chiusurasx_allenata", "bloccodx_allenata", "bloccosx_allenata", "tenutapaletta_allenata", "resistenza_allenata"], "strategia_scelta": "piu_bassa_prioritaria", "strategia_spesa": {"tipo": "percentuale", "valore": 25, "max_xp": 750}, "influenza_eta": {"anziano": "piu_economica_prioritaria_o_resistenza"}},
    "MuroFisico": {"desc": "Priorità a precisione e Resistenza.", "priorita": ["precisione_allenata", "resistenza_allenata", "forza_allenata"], "strategia_scelta": "piu_bassa_tra_due", "strategia_spesa": {"tipo": "percentuale", "valore": 40, "max_xp": 1500}, "influenza_eta": {"anziano": "piu_bassa_tra_due_assoluta"}},
    "SpecialistaBlocchiDifesa": {"desc": "Eccelle nei blocchi e difesa generale.", "priorita": ["bloccodx_allenata", "bloccosx_allenata", "difesa_allenata", "chiusuradx_allenata", "chiusurasx_allenata", "tenutapaletta_allenata", "resistenza_allenata"], "strategia_scelta": "piu_bassa_prioritaria", "strategia_spesa": {"tipo": "quota_fissa", "valore": 400}, "influenza_eta": {"anziano": "piu_economica_prioritaria"}},
    "SpecialistaBlocchiAttacco": {"desc": "Blocca e riparte con attacchi controllati.", "priorita": ["bloccodx_allenata", "bloccosx_allenata", "attacco_allenata", "controllopalla_allenata", "diagonaledx_allenata", "diagonalesx_allenata", "precisione_allenata"], "strategia_scelta": "piu_bassa_prioritaria", "strategia_spesa": {"tipo": "quota_fissa", "valore": 400}, "influenza_eta": {"anziano": "piu_economica_prioritaria"}},
    "SpecialistaBlocchiControllo": {"desc": "Maestro blocchi e controllo palla.", "priorita": ["bloccodx_allenata", "bloccosx_allenata", "controllopalla_allenata", "tenutapaletta_allenata", "difesa_allenata", "resistenza_allenata"], "strategia_scelta": "a_rotazione", "strategia_spesa": {"tipo": "percentuale", "valore": 20, "max_xp": 500}, "influenza_eta": {}},
    "SpecialistaBattutaBlocco": {"desc": "Servizio efficace e buon muro.", "priorita": ["battutadx_allenata", "battutasx_allenata", "bloccodx_allenata", "bloccosx_allenata", "precisione_allenata", "difesa_allenata"], "strategia_scelta": "piu_bassa_prioritaria", "strategia_spesa": {"tipo": "obiettivo_punti", "valore": 0.1, "max_xp": 600}, "influenza_eta": {"anziano": "piu_economica_prioritaria"}},
    "CecchinoPreciso": {"desc": "Focus su colpi specifici e controllo.", "priorita": ["lungolineadx_allenata", "lungolineasx_allenata", "singolaspondadx_allenata", "singolaspondasx_allenata", "doppiaspondadx_allenata", "doppiaspondasx_allenata", "controllopalla_allenata", "tenutapaletta_allenata"], "strategia_scelta": "a_rotazione", "strategia_spesa": {"tipo": "quota_fissa", "valore": 350}, "influenza_eta": {}},
    "TuttofareBilanciato": {"desc": "Sviluppo equilibrato.",
                            "priorita_non_fisiche": [s for s in ATTRIBUTI_ALLENABILI if s not in ALLENATE_FISICHE],
                            "priorita_fisiche": list(ALLENATE_FISICHE),
                            "strategia_scelta": "piu_bassa_assoluta_non_fisica", "strategia_spesa": {"tipo": "percentuale", "valore": 15, "max_xp": 300}, "influenza_eta": {"anziano": "piu_bassa_assoluta_o_fisica_bassa"}}
}
# I nomi delle caratteristiche da mostrare.
NOME_ATTR_TO_DISPLAY_MAP = {
    "precisione_base": "Precisione", "precisione_allenata": "Precisione",
    "resistenza_base": "Resistenza", "resistenza_allenata": "Resistenza",
    "forza_base": "Forza", "forza_allenata": "Forza",
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
# Il valore complessivo, dalla tappa 9 (problema P14): le caratteristiche entrano per ruolo, con
# chiusure e blocchi di dritto e di rovescio, così un mancino specchiato vale quanto il destrimano
# di partenza; ciascuna ha un peso, e i tratti hanno il loro. Fino alla tappa 8 i pesi erano tutti
# a 1, con 33 punti per ambidestro, gioco rapido e cambio di velocità. Quelli qui sotto li ha
# misurati sul motore nuovo strumenti/taratura_valore.py, il 2026-10-07, col seme 9: sono in punti
# di caratteristica, con la media delle caratteristiche di gioco a 1, e A e B riportano la somma
# sulla scala di prima, con la mediana a 137 e lo stesso monte stipendi nel mondo maturo, perché
# l'economia della decisione D22 non cambi; la distanza fra decimo e novantesimo percentile è di
# circa il 30 per cento più larga di prima, che aveva la coda lunga dei 33 punti di ogni tratto,
# e nel mondo maturo va da 99 a 176. Le coppie speculari di colpi hanno un peso solo; le fisiche,
# che vanno da 0 a 10, pesano per punto quattro volte tanto, e la precisione, che entra in tutte
# le qualità, più di tutte.
CARATTERISTICHE_VALORE = (*COLPI_DELLO_SCAMBIO, *COLPI_DI_BATTUTA, "chiusura_dritto", "chiusura_rovescio", "blocco_dritto", "blocco_rovescio",
                          "difesa", "tenutapaletta", "controllopalla", "attacco", "precisione", "forza", "resistenza")
PESI_VALORE = {
    "lungolineasx": 0.49, "lungolineadx": 0.49, "diagonalesx": 0.49, "diagonaledx": 0.49, "singolaspondasx": 0.54, "singolaspondadx": 0.54,
    "doppiaspondasx": 0.49, "doppiaspondadx": 0.49, "triplaspondasx": 0.37, "triplaspondadx": 0.37, "bomba": 0.26, "battutasx": 0.82,
    "battutadx": 0.82, "chiusura_dritto": 2.11, "chiusura_rovescio": 2.58, "blocco_dritto": 1.05, "blocco_rovescio": 1.39, "difesa": 3.65,
    "tenutapaletta": 1.30, "controllopalla": 0.79, "attacco": 1.47, "precisione": 22.12, "forza": 6.11, "resistenza": 3.41,
}
PESI_TRATTI = {"mancino": 1.3, "ambidestro": 5.0, "giocorapido": 1.8, "cambiovelocita": 4.9}
SCALA_VALORE_A = -39.16
SCALA_VALORE_B = 1.0091
SOGLIA_PESO_INERTE = 0.25


def discrepanze_raggruppamenti():
    """
    Confronta i gruppi di caratteristiche di gioco con l'elenco completo, fisiche escluse.
    Restituisce le mancanti nei gruppi e quelle in più: due insiemi vuoti se tutto torna.
    Il vecchio sd.py faceva questo controllo a ogni avvio; ora lo fa la suite dei test.
    """
    definite = set(CARATTERISTICHE_DIFESA_BASE + CARATTERISTICHE_ATTACCO_BASE + CARATTERISTICHE_CONTROLLO_BASE)
    totali = {attr for attr in ATTRIBUTI_BASE_CON_ALLENABILI if attr not in CARATTERISTICHE_FISICHE_BASE}
    return totali - definite, definite - totali
