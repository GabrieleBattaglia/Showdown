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
# Time-out, riscaldamento e pause, in secondi dove sono durate. Nella gara a squadre non ci sono
# sostituzioni durante l'incontro, decisione D26: uno scostamento voluto dalla regola IBSA 22.8.
TIMEOUT_PER_SET = 1
TIMEOUT_SQUADRE = 1
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
# Lo sponsor, dalla tappa 11, metà e metà, risposta 5 di Gabriele: SPONSOR_PER_GLORIA euro al mese
# per ogni punto di gloria, che la simulazione lunga ritocca, più il 9 per cento al mese del valore
# di mercato pieno dei tesserati, che resta fisso. Fino alla tappa 10 erano 35 euro per la gloria.
# Il punto di partenza era 18; la prima taratura grezza del 2026-10-09, simulazione_lunga.py
# --cerca-economia su quattro semi, aveva trovato 16,2, e la taratura fine dello stesso giorno, dopo
# quella del motore e coi pesi nuovi, 16,1: la cassa mediana del computer all'anno 10 sta fra 4.870
# e 5.110 euro sui quattro semi, in media 5.010.
SPONSOR_PER_GLORIA = 16.1
QUOTA_SPONSOR_SUL_VALORE = 0.09
STIPENDIO_DI_RIFERIMENTO = 200
VALORE_DI_RIFERIMENTO = 140
SCALA_STIPENDIO = 40
STIPENDIO_MINIMO = 50
AUMENTO_STIPENDIO_PER_ESPERIENZA = 0.03
MESI_DI_INGAGGIO = 2
REPUTAZIONE_MINIMA = 0.5
REPUTAZIONE_MASSIMA = 2.0
MESI_DI_VALORE = 6
# La fedeltà cresce ogni mese passato in una polisportiva, da 0 a 100. L'esperienza di carriera va
# da 0 a 20, e dalla tappa 11 cresce da più fonti, più sotto.
FEDELTA_PER_MESE = 2.0
FEDELTA_MASSIMA = 100.0
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
# I contratti della tappa 11, D31 e risposte di Gabriele del 9 ottobre 2026. La durata la propone il
# giocatore, da 4 a 24 mesi: la base cresce con l'età, i ragazzi li vogliono brevi e gli anziani
# lunghi, e l'ambizione la accorcia o la allunga fino al 40 per cento, risposta 3. Un mese di
# contratto è un mese del calendario simulato, circa 10 giorni veri.
MESI_CONTRATTO_MIN = 4
MESI_CONTRATTO_MAX = 24
DURATA_PER_ETA = ((9.0, 8.0), (25.0, 10.0), (35.0, 13.0), (45.0, 16.0), (55.0, 20.0), (65.0, 24.0))
K_AMBIZIONE_DURATA = 0.4
GIORNI_PER_MESE = 30.44
# Negli ultimi tre mesi si può rinnovare: tre proposte per finestra, una al giorno, risposta 2;
# il computer ne fa una al mese, con la stessa regola delle tre.
MESI_FINESTRA_RINNOVO = 3
PROPOSTE_RINNOVO_MASSIME = 3
# La richiesta di rinnovo: la gloria del club conta di più per l'ambizioso, la fedeltà fa chiedere
# fino a un quarto in meno, ogni mese di differenza dalla durata proposta costa il 2 per cento.
ESPONENTE_GLORIA_RINNOVO = 0.25
ESPONENTE_GLORIA_PER_AMBIZIONE = 0.5
SCONTO_FEDELTA_RINNOVO = 0.25
RINCARO_DURATA_RINNOVO = 0.02
# Il computer offre al rinnovo il 15 per cento in più della richiesta.
RIALZO_RINNOVO_CPU = 1.15
# Il valore di mercato scende in linea retta negli ultimi tre mesi, fino al 40 per cento alla scadenza.
MESI_VALORE_PIENO = 3
VALORE_A_SCADENZA = 0.4
# Lo svincolo a contratto in corso costa una buonuscita: metà degli stipendi che restano, risposta 4.
QUOTA_BUONUSCITA = 0.5
# Alla migrazione dal formato 5 i contratti durano almeno un anno di calendario, perché non scadano tutti insieme.
MESI_MINIMI_MIGRAZIONE = 12
# L'esperienza della tappa 11: cresce dalla fonte più piccola alla più grande, regola di Gabriele
# dell'8 ottobre 2026. Un poco con l'età, anche da liberi; le amichevoli; lo stare in polisportiva,
# per il fattore del gruppo, che cresce con l'esperienza media della rosa; i tornei e le sfide,
# agganci della tappa 12, con un premio per i piazzamenti.
ESPERIENZA_PER_ANNO_DI_VITA = 0.05
ESPERIENZA_PER_AMICHEVOLE = 0.00125
# 0,00279 porta la carriera perfetta, con le sue 3985 amichevoli, a 20 di esperienza a 50 anni:
# l'ha trovato strumenti/carriera_perfetta.py nella prima taratura grezza e confermato nella taratura
# fine del 9 ottobre 2026, dopo quella del motore. Con l'età fa 2,05, con le amichevoli 4,98, con la
# polisportiva il resto.
ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA = 0.00279
K_GRUPPO_ESPERIENZA = 0.2
ESPERIENZA_PER_PARTITA_TORNEO = 0.01
ESPERIENZA_PER_SFIDA = 0.006
ESPERIENZA_PER_PIAZZAMENTO = {1: 0.3, 2: 0.2, 3: 0.12, 4: 0.06}
# La classe, da K0 ad A1, D31: il 70 per cento al valore pesato e il 30 all'esperienza. Il valore
# pesato si misura in rapporto alla somma della carriera perfetta dai 9 ai 50 anni, che vale A1.
# Le soglie sono fissate una volta per sempre: la somma della carriera perfetta, i pesi della classe
# e le ancore sono costanti storiche, che scrive strumenti/carriera_perfetta.py e che poi non si
# toccano più senza Gabriele. Le ancore sono coppie di livello e punteggio: K0 a zero; il nato del
# primo percentile a I9 e quello del novantanovesimo a F0; il bravo a 30 anni a E0; la carriera
# perfetta ad A1. In mezzo le soglie si interpolano in linea retta. I pesi della classe sono quelli
# del valore dopo la taratura del motore della tappa 11, e la somma e le ancore vengono da
# strumenti/carriera_perfetta.py sui pesi nuovi, nella taratura fine del 9 ottobre 2026: il nato
# numero 1229 al novantesimo percentile senza tratti arriva a 365,0 di somma e a 20 di esperienza a
# 50 anni; il nato del primo percentile vale 0,204, quello del novantanovesimo 0,403, il bravo a
# 30 anni 0,549. Sono congelate: alla tappa 12 si abbassano le fonti, non le soglie, e da qui non si
# toccano più senza Gabriele. La prima taratura grezza aveva 368,5 e 0,202, 0,401 e 0,546, con i
# pesi della tappa 9.
PESO_VALORE_CLASSE = 0.7
PESO_ESPERIENZA_CLASSE = 0.3
SOMMA_CARRIERA_PERFETTA = 365.0
PESI_CLASSE = {
    "lungolineasx": 0.48, "lungolineadx": 0.48, "diagonalesx": 0.51, "diagonaledx": 0.51, "singolaspondasx": 0.49, "singolaspondadx": 0.49,
    "doppiaspondasx": 0.48, "doppiaspondadx": 0.48, "triplaspondasx": 0.39, "triplaspondadx": 0.39, "bomba": 0.43, "battutasx": 0.72,
    "battutadx": 0.72, "chiusura_dritto": 2.24, "chiusura_rovescio": 2.74, "blocco_dritto": 1.30, "blocco_rovescio": 1.48, "difesa": 3.32,
    "tenutapaletta": 1.22, "controllopalla": 0.75, "attacco": 1.36, "precisione": 10.36, "forza": 5.54, "resistenza": 3.71,
}
PESI_TRATTI_CLASSE = {"mancino": 2.4, "ambidestro": 3.4, "giocorapido": 1.0, "cambiovelocita": 4.6}
ANCORE_CLASSE = ((100, 0.0), (89, 0.204), (50, 0.403), (40, 0.549), (1, 1.0))
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
# L'allenamento della tappa 11, decisione D31. Tutti i numeri sono una prima stima, da fissare con
# strumenti/carriera_perfetta.py e strumenti/simulazione_lunga.py e da approvare con Gabriele.
# I punti allenamento della seduta quotidiana: il tesserato ne prende PA_SEDUTA per il fattore della
# sua intensità, il libero la metà, senza intensità.
PA_SEDUTA = 1.0
QUOTA_SEDUTA_LIBERI = 0.5
# I punti di un incontro: una base, mezzo punto per ogni set vinto e un punto a chi vince, così al
# meglio dei 5 se ne prendono appena il 13 per cento in più che al meglio dei 3, come vuole D31. Il
# premio al più debole va a chi ha almeno DISTACCO_PIU_DEBOLE punti di somma pesata in meno, anche
# quando perde: attorno alla mediana sono il 25 per cento del valore, la soglia di prima. Tornei e
# sfide sono gli agganci della tappa 12.
PA_PARTITA_BASE = 2.0
PA_PER_SET_VINTO = 0.5
PA_VITTORIA = 1.0
PA_BONUS_PIU_DEBOLE = 1.0
DISTACCO_PIU_DEBOLE = 25.0
PA_BONUS_TORNEO = 3.0
PA_BONUS_SFIDA = 2.0
# Il costo dei punti, tarato sul valore: il costo marginale di una caratteristica è
# COSTO_PER_PUNTO_PESATO per il suo peso nel valore, per lo sconto, diviso l'efficacia, per
# exp(CRESCITA_DEL_COSTO per il livello relativo). Dal livello zero al tetto il costo cresce di
# 12,2 volte, come le 12,6 di Hattrick dal livello 0 al 20; il ritmo medio, 50, l'ha scelto
# Gabriele con la risposta 1 del 9 ottobre 2026.
COSTO_PER_PUNTO_PESATO = 50.0
CRESCITA_DEL_COSTO = 2.5
# Agli ipovedenti il 7 per cento di sconto sulle caratteristiche di gioco: chi vede un poco impara
# qualcosa in più guardando, D31.
SCONTO_IPOVEDENTI = 0.07
# La curva d'età di Hattrick, 54 diviso gli anni più 37: 1,17 a 9 anni, 0,87 a 25, 0,62 a 50.
CURVA_ETA_NUMERATORE = 54.0
CURVA_ETA_SPOSTAMENTO = 37.0
# L'aggancio dell'allenatore di una tappa futura: per ora non c'è, e vale 1.
FATTORE_ALLENATORE = 1.0
# Il calo dei livelli alti, come la DropL di Hattrick: sopra il 70 per cento del tetto l'allenata
# perde, ogni anno d'età, fino a CALO_MASSIMO_ANNUO del tetto al tetto pieno, con una curva cubica.
SOGLIA_CALO_LIVELLI_ALTI = 0.7
CALO_MASSIMO_ANNUO = 0.05
# I liberi e i tesserati del computer spendono da soli quando il portafoglio arriva qui.
SOGLIA_SPESA_AUTONOMI = 20.0
# Il modello di spesa: le preferenze delle caratteristiche principali e secondarie dell'indole.
PREFERENZA_PRINCIPALE = 2.0
PREFERENZA_SECONDARIA = 1.4
# Le intensità dell'allenamento di un tesserato, una riga per intensità con i suoi quattro effetti:
# i punti della seduta, la costanza della seduta, il fattore degli infortuni in partita e la
# probabilità, in percentuale al giorno, di un infortunio in seduta. La costanza della seduta l'ha
# decisa Gabriele con la risposta 7: l'intensa fa reggere meglio la fatica, la leggera la peggiora.
INTENSITA = {
    "leggera": {"punti": 0.6, "costanza": 0.6, "infortuni_partita": 0.85, "infortuni_seduta": 0.0},
    "normale": {"punti": 1.0, "costanza": 1.0, "infortuni_partita": 1.0, "infortuni_seduta": 0.0},
    "intensa": {"punti": 1.4, "costanza": 1.3, "infortuni_partita": 1.25, "infortuni_seduta": 0.3},
}
INTENSITA_PREDEFINITA = "normale"
# Il rischio in seduta cresce dai 30 anni: fino al triplo a 75.
AUMENTO_RISCHIO_SEDUTA = 2.0
# I tre tratti rari dell'allenamento, D31, con la probabilità alla nascita in percentuale e
# l'effetto: il talento e l'apprendista rapido moltiplicano l'efficacia, e l'apprendista dimentica
# in fretta, perché ogni mese la sua allenata si moltiplica per l'oblio; la maturazione precoce o
# tardiva sposta gli anni migliori, con un fattore che va da 1 più a 1 meno l'effetto attorno ai 30
# anni, e sposta l'inizio del declino.
TRATTI_ALLENAMENTO = {
    "talento": {"probabilita": 5.0, "efficacia": 1.3},
    "apprendista_rapido": {"probabilita": 4.0, "efficacia": 1.5, "oblio_mensile": 0.98},
    "precoce": {"probabilita": 4.0, "maturazione": 0.3},
    "tardiva": {"probabilita": 4.0, "maturazione": -0.25},
}
ETA_PERNO_MATURAZIONE = 30.0
ANNI_RAMPA_MATURAZIONE = 10.0
SPOSTAMENTO_DECLINO = {"precoce": -6.0, "tardiva": 6.0}
MATURAZIONI = tuple(SPOSTAMENTO_DECLINO)
# L'ambizione, da 0 a 100: nasce dal numero del giocatore come il temperamento, decide la durata
# dei contratti e conta nel rinnovo; la scheda la dice a parole con queste fasce.
AMBIZIONE_MEDIA = 50.0
AMBIZIONE_DEVIAZIONE = 18.0
FASCE_AMBIZIONE = ((30.0, "modesto"), (45.0, "poco ambizioso"), (60.0, "ambizioso"), (75.0, "molto ambizioso"), (None, "ambiziosissimo"))
# La costanza recente, D31: la media mobile esponenziale dell'attività di ogni giorno, con una
# mezza vita di tre settimane. La seduta del tesserato vale la costanza della sua intensità, quella
# del libero COSTANZA_LIBERI, ogni partita aggiunge COSTANZA_PER_PARTITA. Il motore la porta da 0 a 1
# dividendola per COSTANZA_PIENA, che è l'intensa con un'amichevole al giorno; la scheda la dice a
# parole con le fasce.
MEZZA_VITA_COSTANZA_GIORNI = 21.0
DECADIMENTO_COSTANZA = 0.5 ** (1.0 / MEZZA_VITA_COSTANZA_GIORNI)
COSTANZA_LIBERI = 0.5
COSTANZA_PER_PARTITA = 0.7
COSTANZA_PIENA = 2.0
FASCE_COSTANZA = ((0.1, "ferma"), (0.35, "bassa"), (0.6, "regolare"), (0.85, "alta"), (None, "altissima"))
# Le indoli della nascita, D31: gli archetipi di prima rivisti e corretti, con il nome da leggere
# nella scheda e le caratteristiche principali e secondarie, coi nomi senza suffisso. Il modello di
# spesa, uno per tutti, dà alle principali e alle secondarie le loro preferenze; completa non ne ha.
_SPONDE = ("singolaspondasx", "singolaspondadx", "doppiaspondasx", "doppiaspondadx", "triplaspondasx", "triplaspondadx")
_CHIUSURE = ("chiusurasx", "chiusuradx")
_BLOCCHI = ("bloccosx", "bloccodx")
INDOLI = {
    "aggressiva": {"nome": "aggressiva", "principali": ("lungolineasx", "lungolineadx", "diagonalesx", "diagonaledx", "bomba", "attacco"),
                   "secondarie": (*_SPONDE, "forza")},
    "difensiva": {"nome": "difensiva", "principali": (*_CHIUSURE, *_BLOCCHI, "difesa"), "secondarie": ("controllopalla", "tenutapaletta", "resistenza")},
    "atletica": {"nome": "atletica", "principali": ("precisione", "resistenza", "forza"), "secondarie": ("difesa", *_CHIUSURE)},
    "muro": {"nome": "da muro", "principali": (*_BLOCCHI, "difesa"), "secondarie": (*_CHIUSURE, "tenutapaletta")},
    "rimessa": {"nome": "di rimessa", "principali": (*_BLOCCHI, "attacco"), "secondarie": ("diagonalesx", "diagonaledx", "controllopalla")},
    "controllo": {"nome": "di controllo", "principali": ("controllopalla", "tenutapaletta"), "secondarie": (*_BLOCCHI, "difesa")},
    "battuta": {"nome": "da battuta", "principali": ("battutasx", "battutadx"), "secondarie": (*_BLOCCHI, "precisione")},
    "tecnica": {"nome": "tecnica", "principali": (*_SPONDE, "lungolineasx", "lungolineadx"), "secondarie": ("controllopalla", "tenutapaletta")},
    "completa": {"nome": "completa", "principali": (), "secondarie": ()},
}
INDOLE_PREDEFINITA = "completa"
# Alla nascita vince l'indole col punteggio standardizzato più alto, se supera la soglia, altrimenti
# completa; una volta su dieci l'indole si tira a caso, come prima l'archetipo.
SOGLIA_INDOLE = 0.07
PROB_INDOLE_CASUALE = 10.0
# I nove archetipi dei salvataggi fino al formato 5, nelle chiavi delle indoli.
MAPPA_ARCHETIPI_INDOLI = {
    "AttaccantePuro": "aggressiva", "DifensoreRoccioso": "difensiva", "MuroFisico": "atletica", "SpecialistaBlocchiDifesa": "muro",
    "SpecialistaBlocchiAttacco": "rimessa", "SpecialistaBlocchiControllo": "controllo", "SpecialistaBattutaBlocco": "battuta",
    "CecchinoPreciso": "tecnica", "TuttofareBilanciato": "completa",
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
# misurati sul motore nuovo strumenti/taratura_valore.py, sugli incontri al meglio dei 3, l'ultima
# volta il 9 ottobre 2026 con la tappa 11, dopo l'abitudine al colpo ripetuto e con la costanza
# recente fra i controlli: la resistenza è scesa da 4,71 a 3,71, perché la parte allenata non conta
# più due volte, i colpi dello scambio sono saliti un poco, il mancino è sceso da 2,9 a 2,4. L'8
# ottobre, dopo la revisione della decisione D26, la taratura aveva dimezzato il peso della
# precisione nelle qualità. Sono in punti di caratteristica, con la media delle caratteristiche
# di gioco a 1, e sono la media di quattro semi, 9, 19, 29 e 39, perché con un seme solo il
# mancino andava da 2,9 a 5,6 punti di valore. A e B riportano la somma sulla scala del valore, e
# dalla decisione D26 si cercano con strumenti/simulazione_lunga.py --cerca-scala: B per
# bisezione, perché in dieci anni simulati su quattro semi la cassa mediana delle polisportive del
# computer torni sui 5000 euro della tappa 8, e A perché la mediana del valore nel mondo maturo
# stia a 135,5, così lo stipendio mediano resta fra 210 e 220 euro. Il valore è più largo di
# prima: nel mondo maturo va da 94 a 178 dal decimo al novantesimo percentile, e gli stipendi più
# bassi scendono a 90 euro. Le coppie
# speculari di colpi hanno un peso solo; le fisiche, che vanno da 0 a 10, pesano per punto
# quattro volte tanto, e la precisione, che entra in tutte le qualità, più di tutte, ma la metà
# di prima. Dalla tappa 11 la scala si tara col mondo che si allena, all'anno 10 della simulazione
# lunga, con --cerca-economia: A tiene la mediana del valore dei giocatori in attività a 135,5, B
# porta lo stipendio pagato al decimo percentile dei tesserati a 105 euro. La taratura fine del
# 9 ottobre 2026, dopo quella del motore e coi pesi nuovi, ha dato A -50,68 e B 1,1414: sui quattro
# semi, all'anno 10, stipendio pagato mediano 210 o 220 euro, decimo percentile 100, novantesimo
# da 510 a 520, tesserati al 90 o 91 per cento, cassa mediana del computer attorno ai 5.000 euro,
# mediana del valore da 135,4 a 136,0. La prima taratura grezza aveva dato A -49,68 e B 1,1302, coi
# pesi della tappa 9. Fino alla tappa 10 erano A -82,61 e B 1,3878, che la migrazione conserva per
# i contratti.
CARATTERISTICHE_VALORE = (*COLPI_DELLO_SCAMBIO, *COLPI_DI_BATTUTA, "chiusura_dritto", "chiusura_rovescio", "blocco_dritto", "blocco_rovescio",
                          "difesa", "tenutapaletta", "controllopalla", "attacco", "precisione", "forza", "resistenza")
PESI_VALORE = {
    "lungolineasx": 0.48, "lungolineadx": 0.48, "diagonalesx": 0.51, "diagonaledx": 0.51, "singolaspondasx": 0.49, "singolaspondadx": 0.49,
    "doppiaspondasx": 0.48, "doppiaspondadx": 0.48, "triplaspondasx": 0.39, "triplaspondadx": 0.39, "bomba": 0.43, "battutasx": 0.72,
    "battutadx": 0.72, "chiusura_dritto": 2.24, "chiusura_rovescio": 2.74, "blocco_dritto": 1.30, "blocco_rovescio": 1.48, "difesa": 3.32,
    "tenutapaletta": 1.22, "controllopalla": 0.75, "attacco": 1.36, "precisione": 10.36, "forza": 5.54, "resistenza": 3.71,
}
PESI_TRATTI = {"mancino": 2.4, "ambidestro": 3.4, "giocorapido": 1.0, "cambiovelocita": 4.6}
SCALA_VALORE_A = -50.68
SCALA_VALORE_B = 1.1414
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
