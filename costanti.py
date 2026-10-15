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
# Gloria richiesta dal giocatore. Dalla tappa 12, punto 9.4 del progetto e risposta 11 di Gabriele, la
# gloria mediana del computer raddoppia col palmarès, e la gloria che i giocatori chiedono raddoppia
# con lei, perché per la polisportiva mediana il rapporto fra gloria chiesta e offerta resti quello
# della tappa 11: erano 0,9 e 12, e le prime stime 1,8 e 24. La polisportiva nuova dell'utente, con
# metà della gloria mediana, paga ingaggi più cari. La taratura del 14 ottobre 2026, punto 13.4: con le
# prime stime, all'anno 20, la gloria richiesta mediana dei liberi era 2,4 volte la gloria mediana del
# computer, contro 0,92 della 1.60.11, e il computer non riusciva più a tesserare, al 78 per cento.
# strumenti/simulazione_lunga.py --cerca-economia trova il fattore comune in forma chiusa sul campione
# dell'anno 20, 1,81 sui valori della 1.60.11. Col mondo finale, però, il rapporto con 1,81 era 0,99
# all'anno 10, come lo 0,99 della 1.60.11, e 0,79 all'anno 20, il 14 per cento sotto lo 0,92 della
# 1.60.11; con 1,94 era 1,10 all'anno 10, l'11 per cento sopra, e 0,89 all'anno 20, il 3 sotto. Nel
# mondo che gioca il rapporto scende dall'anno 10 al 20 del 20 per cento, nella 1.60.11 dell'8, perché
# la gloria del computer cresce mentre si riempie la finestra del palmarès: con un fattore solo i due
# anni non stanno tutti e due sul rapporto della 1.60.11. Il fattore scelto, 1,9, li mette attorno al 7
# per cento sopra e sotto, dentro il 10 del progetto: 1,706 e 23.
K_ICV_GLORIA_RICHIESTA = 1.706
ETA_PICCO_RICHIESTA_GLORIA_ANNI = 17.0
ETA_MINIMO_RICHIESTA_GLORIA_ANNI = 55.0
MAX_FATTORE_ETA_GLORIA = 2.7
MIN_FATTORE_ETA_GLORIA = 0.1
GLORIA_RICHIESTA_FISSA = 23
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
# Dalla tappa 12, D32 e risposta 11 di Gabriele, il palmarès degli ultimi 5 anni fa metà della gloria,
# che per la polisportiva mediana del computer raddoppia: lo sponsor per gloria scende a 8, cioè 16,1
# per 135 diviso 270, così la mediana incassa lo sponsor di prima, e la polisportiva nuova
# dell'utente, senza palmarès, ne incassa circa un quarto in meno: partire è più difficile, come ha
# scelto Gabriele. La taratura del 14 ottobre 2026, strumenti/simulazione_lunga.py --cerca-economia,
# punto 13.4: prima la gloria all'anno 20, poi la scala e lo sponsor all'anno 10, come alla tappa 11,
# sui semi 2026, 7, 13 e 21. Con la scala nuova e la gloria nuova la bisezione dà 7,8, con la cassa
# mediana del computer all'anno 10 fra 4.870 e 5.050 euro; all'anno 20 sale fra 5.880 e 6.160, perché
# la gloria cresce mentre si riempie la finestra di cinque anni del palmarès.
SPONSOR_PER_GLORIA = 7.8
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
# Il computer spende secondo la cassa, decisione 1 di Gabriele del 14 ottobre 2026: con la cassa piena
# può offrire di più e tesserare i campioni, e la cassa smette di crescere. Nella prova di sessant'anni
# della taratura della tappa 12 la cassa mediana del computer passava i 15.000 euro dall'anno 40 e
# arrivava a 44.000-54.000 all'anno 60, mentre i più forti del mondo restavano liberi: chiedevano più di
# quanto lo sponsor e un ventiquattresimo della cassa lasciassero spendere a chiunque. Oltre
# SOGLIA_CASSA_PIENA_CPU, il doppio della cassa mediana che la taratura dell'economia cerca all'anno 10,
# la cassa in più si conta spesa in MESI_CASSA_PIENA_CPU mesi: un mese di quella spesa si aggiunge agli
# stipendi che il computer si permette, nei tesseramenti, negli acquisti e nei rinnovi, e al prezzo più
# alto che paga per un giocatore in vendita. Sotto la soglia non cambia niente. I mesi sono il parametro
# che la taratura dell'economia del passo seguente fissa con la prova di sessant'anni; il valore di
# partenza viene dal mondo del seme 2026 all'anno 50, dove la cassa mediana del computer è di 27.300
# euro e 45 dei primi 100 per valore sono liberi: con 8 mesi 34 di loro stanno nei conti di almeno una
# polisportiva del computer, con 12 mesi 22, con le regole di prima nessuno.
SOGLIA_CASSA_PIENA_CPU = 10_000
MESI_CASSA_PIENA_CPU = 8
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
# Dalla tappa 12, D32 e punto 10.3 del progetto, le fonti si abbassano perché i tornei e le sfide
# entrano nella carriera perfetta, che resta a 20 di esperienza a 50 anni. Le prime stime seguivano i
# numeri d'esempio di D32: l'età 2,05, le amichevoli 2,5, le sfide 1,5, il club 5, i tornei 9, fatti
# di incontri, fasi superate e piazzamenti. Fino alla tappa 11 le amichevoli valevano
# 0,00125 e il giorno in polisportiva 0,00279: con l'età 2,05, le amichevoli 4,98, il club il resto.
# Le prime stime del progetto erano 0,0007, 0,00108 e 0,005, e per i tornei 0,011, 0,012 e 0,06. La
# taratura del 14 ottobre 2026, strumenti/carriera_perfetta.py riscritto, punto 13.3: la carriera
# perfetta gioca davvero il calendario predefinito, 69 tornei di cui 6 mondiali, 456 incontri di
# torneo, 265 sfide e 3.614 amichevoli in 4.428 giorni, e le costanti si risolvono fonte per fonte
# sulla carriera più lenta, che a 50 anni ha 20,05 di esperienza senza il tetto: l'età 2,05, le
# amichevoli 2,50, le sfide 1,50, il club 5,00, i tornei 9,00, cioè 4,50 dagli incontri, 1,80 dalle
# fasi superate e 2,70 dai piazzamenti; le cinque carriere vedenti hanno da 19,78 a 20,19. La carta è
# strumenti/carriera_perfetta_tappa_12.txt.
# La decisione 8 di Gabriele del 14 ottobre 2026: vale l'ordine delle parole di D32, dalla fonte più
# piccola alla più grande, età, amichevoli, sfide, club e tornei, e non quello dei numeri d'esempio, che
# mettevano le sfide sotto l'età: l'età 2, le amichevoli 2,5, le sfide 3, il club 4,5, i tornei 8, sempre
# 20 a 50 anni. I valori di partenza vengono dalla taratura di sopra, nella proporzione delle quote nuove
# sulle vecchie, così coi conteggi di quella carriera le quote sono proprio queste: l'età e le amichevoli
# restano, la sfida raddoppia da 0,00566 a 0,01132, il giorno in polisportiva scende di un decimo da
# 0,001075 a 0,000968, gli incontri, le fasi e i piazzamenti dei tornei di un nono, da 0,0074, 0,00442 e
# 0,03425 a 0,00658, 0,00393 e 0,03044. La taratura della carriera perfetta del passo seguente li risolve
# di nuovo fonte per fonte, con i bersagli nuovi di strumenti/carriera_perfetta.py.
ESPERIENZA_PER_AMICHEVOLE = 0.000692
ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA = 0.000968
K_GRUPPO_ESPERIENZA = 0.2
ESPERIENZA_PER_SFIDA = 0.01132
# Le riserve di una sfida prendono metà dell'esperienza dei titolari, risposta 15 di Gabriele: stare
# in squadra insegna qualcosa, ma senza punti allenamento né partite nella carriera.
ESPERIENZA_RISERVA_QUOTA = 0.5
# I tornei, per l'importanza: ogni incontro giocato, ogni fase superata, cioè un girone passato o un
# turno di tabellone vinto o saltato col riposo, e il piazzamento a scalare per i primi 12, regola di
# Gabriele; nessuna quota per la sola partecipazione, risposta 9. Il vecchio premio dei soli primi
# quattro, da 0,3 a 0,06, sparisce. Le prime stime erano molto più alte, perché contavano sui 410
# incontri di torneo del conto del progetto senza l'importanza e su piazzamenti medi: la carriera
# perfetta vera vince 54 dei suoi 69 tornei e 6 mondiali, con l'importanza 4, e le fasi superate e i
# piazzamenti in alto le danno molto più di quanto pensato. La revisione del 14 ottobre 2026 li lascia:
# con la carriera perfetta che va al mondiale coi punti come nel mondo, la media dell'esperienza a 50 anni
# di tutte le carriere vedenti sta attorno a 20, mentre quella del nato più lento cambia di un punto da
# una misura all'altra, secondo quanti mondiali gioca. Dalla decisione 8 di Gabriele del 14 ottobre 2026
# i tornei fanno 8 invece di 9, e i tre valori scendono di un nono: vedi sopra.
ESPERIENZA_PER_PARTITA_TORNEO = 0.00658
ESPERIENZA_PER_FASE_SUPERATA = 0.00393
ESPERIENZA_PIAZZAMENTO_BASE = 0.03044
SCALA_PIAZZAMENTI = (1.0, 0.8, 0.65, 0.55, 0.45, 0.40, 0.35, 0.30, 0.25, 0.20, 0.15, 0.10)
# La classe, da K0 ad A1, D31: il 70 per cento al valore pesato e il 30 all'esperienza. Il valore
# pesato si misura in rapporto alla somma della carriera perfetta dai 9 ai 50 anni, che vale A1.
# Le soglie sono fissate una volta per sempre: la somma della carriera perfetta, i pesi della classe
# e le ancore sono costanti storiche, che scrive strumenti/carriera_perfetta.py e che poi non si
# toccano più senza Gabriele. Le ancore sono coppie di livello e punteggio: K0 a zero; il nato del
# primo percentile a I9 e quello del novantanovesimo a F0; il bravo dell'utente a 35 anni a D0; la
# carriera perfetta ad A1. In mezzo le soglie si interpolano in linea retta, e i livelli si
# allargano dal basso verso l'alto, come vuole D31: un livello vale 0,0051 di punteggio fra I9 e
# F0, dove stanno i nati, 0,0102 fra F0 e D0, dove stanno i bravi a metà carriera, 0,0135 fra D0
# e A1, le carriere eccellenti. I pesi della classe sono quelli del valore dopo la taratura del
# motore della tappa 11, e la somma e le ancore vengono da strumenti/carriera_perfetta.py.
# La revisione della tappa 11, il 9 ottobre 2026, ha cambiato tre cose. La somma non viene più da
# un nato solo, che arrivava ad A1 per caso: è la più bassa delle carriere perfette di cinque nati
# vedenti al novantesimo percentile, di cinque semi, così ognuna arriva ad A1 entro i 50 anni; le
# stesse carriere di nati ipovedenti, con lo sconto del 7 per cento sull'allenamento delle
# caratteristiche di gioco, ci arrivano verso i 48 anni e mezzo. Somma e ancore si arrotondano per
# difetto: arrotondate al più vicino erano finite tutte verso l'alto, e la carriera di riferimento
# arrivava ad A2. E il bravo a 30 anni non fa più da ancora a E0: così la classe E, dove sta quasi
# metà dei giocatori del mondo maturo, aveva i livelli più larghi di tutta la scala, più di A, B e C.
# I punteggi esatti delle ancore: 0,204776, 0,404708 e 0,609318; le carriere perfette vedenti
# arrivano da 363,5 a 366,6 di somma. Ancora del bravo e dotazione della carriera di riferimento
# sono da confermare con Gabriele. La taratura fine aveva 365,0 col nato numero 1229 e le ancore
# 0,204, 0,403 e, a E0, 0,549; la prima taratura grezza 368,5 e 0,202, 0,401 e 0,546.
PESO_VALORE_CLASSE = 0.7
PESO_ESPERIENZA_CLASSE = 0.3
SOMMA_CARRIERA_PERFETTA = 363.5
PESI_CLASSE = {
    "lungolineasx": 0.46, "lungolineadx": 0.46, "diagonalesx": 0.50, "diagonaledx": 0.50, "singolaspondasx": 0.46, "singolaspondadx": 0.46,
    "doppiaspondasx": 0.48, "doppiaspondadx": 0.48, "triplaspondasx": 0.41, "triplaspondadx": 0.41, "bomba": 0.50, "battutasx": 0.71,
    "battutadx": 0.71, "chiusura_dritto": 2.20, "chiusura_rovescio": 2.73, "blocco_dritto": 1.29, "blocco_rovescio": 1.55, "difesa": 3.33,
    "tenutapaletta": 1.25, "controllopalla": 0.75, "attacco": 1.36, "precisione": 10.25, "forza": 5.59, "resistenza": 3.63,
}
PESI_TRATTI_CLASSE = {"mancino": 2.7, "ambidestro": 3.9, "giocorapido": 0.9, "cambiovelocita": 4.5}
ANCORE_CLASSE = ((100, 0.0), (89, 0.204), (50, 0.404), (30, 0.609), (1, 1.0))
NUM_GIOCATORI_INIZIALI = 50
# Quanti giocatori nuovi entrano nel mondo ogni giorno simulato, estremi compresi. Fino alla tappa 11
# da 1 a 7, la grandezza scelta con D18, circa 15.000 attivi e 20.000 vivi a regime. Dalla tappa 12,
# idea di Gabriele in D32 con la issue 1, da 2 a 9, cinque e mezzo in media: il mondo a regime arriva
# a circa 20.600 attivi e 27.500 vivi, un terzo in più, e il giorno simulato era più lento di un
# terzo prima delle accelerazioni del punto 1.3 del progetto della tappa; in cambio al mercato restano
# sempre dei liberi, perché il computer fonda polisportive soltanto per nove attivi su dieci.
CREA_NUOVI_PER_TICK_RANGE = (2, 9)
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
# Dalla tappa 12, D32 e punto 10.2 del progetto, i punti di un incontro sono quelli della formula di
# sopra, premio al più debole compreso, per un fattore della fonte e per l'importanza del torneo: i
# vecchi agganci, tre punti in più per il torneo e due per la sfida, spariscono. Prime stime, dal
# conto della carriera perfetta di 4.428 giorni con circa 3.580 amichevoli, 410 incontri di torneo e
# 330 sfide, perché la seduta faccia il 22 per cento dei punti, i tornei il 40, le amichevoli il 34 e
# le sfide il 4, D32: un'amichevole vale circa 1,9 punti, la metà di prima, e un incontro di torneo
# circa 19, nove amichevoli. Le prime stime erano 0,48, 4,9 e 0,75.
# La taratura del 14 ottobre 2026, strumenti/carriera_perfetta.py riscritto, punto 13.3: le cinque
# carriere perfette vedenti giocano davvero il calendario predefinito, i tornei con tornei.py e i loro
# incontri col motore, il mondiale quando si qualificano, le sfide e le amichevoli, contro i mondi
# sintetici che giocano anche loro; il totale si cerca col metodo delle secanti perché la più lenta
# arrivi ad A1 nel mezzo del bersaglio fra 49,5 e 50 anni, e si divide nelle proporzioni 40, 34 e 4
# della parte delle partite. La prima corsa aveva dato 0,515, 3,512 e 1,045; questa è la terza, coi
# conteggi delle gare del mondo dopo l'economia e l'esito rapido della verifica finale: la più lenta
# arriva ad A1 a 49,76 anni con 20.876 punti, 141 al mese, la seduta ne fa il 21,2 per cento, i
# tornei il 40,4, le amichevoli il 34,3, le sfide il 4,0; un incontro di torneo vale in media 18,5
# punti, un'amichevole 1,98, una sfida 3,18. Le altre quattro arrivano ad A1 fra 49,41 e 49,55 anni, i
# tre ipovedenti fra 47,1 e 49,2. La carriera più lenta gioca il primo mondiale a 32 anni e mezzo, e i
# mondiali, con l'importanza 4, fanno il 29 per cento dei suoi punti dei tornei.
# La revisione del 14 ottobre 2026 ha rifatto la carriera perfetta: dieci nati con cinque estrazioni del
# caso ciascuno, perché una carriera sola per nato era una fortuna dell'estrazione, e il mondiale con la
# convocazione del mondo, coi punti dell'ultimo anno, PUNTI_PER_IL_MONDIALE, invece del punteggio di
# classe. Con la soglia dei punti la stessa carriera gioca da zero a dieci mondiali, e la sua età di A1
# varia di qualche anno da un'estrazione all'altra: la media del nato più lento oscilla di mezzo anno da
# una misura all'altra anche coi semi fermi. Questi fattori vengono dalla media dei passi della ricerca
# con la media del nato più lento nel bersaglio, corretta con la retta dell'età sul totale stimata su
# tutti i sedici passi: il torneo sale da 3,434 a 3,813, l'amichevole da 0,506 a 0,517, la sfida da
# 1,022 a 1,028. La carta è strumenti/carriera_perfetta_tappa_12.txt.
PA_FATTORE_AMICHEVOLE = 0.517
PA_FATTORE_TORNEO = 3.813
PA_FATTORE_SFIDA = 1.028
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
# anni, e sposta l'inizio del declino. L'oblio era 0,98 al mese, cioè il 7 per cento per anno d'età:
# la revisione della tappa 11 ha visto che così l'apprendista era avanti al gemello senza il tratto
# soltanto fino ai 30 anni, e a 50 ne aveva poco più della metà dell'allenata, quindi il tratto raro
# era quasi sempre un difetto. Con 0,99 impara e dimentica ancora in fretta: è avanti da giovane, il
# gemello lo raggiunge verso i 40 anni, e a 50 ne ha circa l'85 per cento. Da confermare con Gabriele.
TRATTI_ALLENAMENTO = {
    "talento": {"probabilita": 5.0, "efficacia": 1.3},
    "apprendista_rapido": {"probabilita": 4.0, "efficacia": 1.5, "oblio_mensile": 0.99},
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
# volta il 9 ottobre 2026 con la revisione della tappa 11, dopo l'abitudine al colpo ripetuto contata
# per tipo di colpo e con la costanza recente fra i controlli: rispetto alla tappa 9 la resistenza è
# scesa da 4,71 a 3,63, perché la parte allenata non conta più due volte, la bomba è salita da 0,36
# a 0,50 e la tripla sponda da 0,33 a 0,41, il mancino è sceso da 2,9 a 2,7. L'8
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
# i contratti. La revisione della tappa 11, coi pesi nuovi, ha rifatto la ricerca: già al primo giro
# la scala e lo sponsor di qui stanno dentro tutti i bersagli, cassa mediana 4.992 euro in media sui
# quattro semi, e i giri seguenti oscillano col rumore dei semi, A da -46,5 a -52,8, quindi restano.
# Da confermare con Gabriele: la migrazione non tocca caratteristiche e stipendi, ma il valore
# mostrato cambia per tutti con la scala e i pesi nuovi, nel suo mondo da 140,6 a 131,3 di
# mediana; la risposta 6, «la migrazione non cambia i valori di nessuno», è stata letta come
# «nessuna caratteristica cambia», e l'altra lettura chiederebbe di tenere qui la scala della 1.50.0.
# La taratura della tappa 12, il 14 ottobre 2026, punto 13.2 del progetto, sul motore della 1.60.11 col
# freno alle battute alte e col ritiro a fine set: sui quattro semi di sempre, 691.200 incontri, la
# regressione spiega il 94,9, 95,4, 95,2 e 95,5 per cento delle vittorie, e dal 94,1 al 95,4 nelle
# verifiche. Il freno ha fatto quello che la issue 2 aveva previsto: il peso delle battute scende da
# 0,71 a 0,47. Il resto si muove poco, e quasi tutto in su di qualche centesimo, perché la media delle
# caratteristiche di gioco resta 1: la precisione da 10,25 a 10,55, la difesa da 3,33 a 3,41; i tratti
# salgono, il mancino da 2,7 a 3,0, l'ambidestro da 3,9 a 4,5, il cambio di velocità da 4,5 a 4,8. La
# verifica a coppie è concorde: un punto di precisione vale 12,1 punti di valore e il valore gliene dà
# 11,8, uno di resistenza 3,9 e 4,2, il mancino 2,6 e 3,4, dentro la banda da 2 a 6 di Gabriele. I pesi
# della classe, PESI_CLASSE e PESI_TRATTI_CLASSE, restano quelli congelati della tappa 11, con le
# battute a 0,71: la classe premia le battute più del valore, ed è una decisione per Gabriele.
# La scala della tappa 12, punto 13.4: coi pesi nuovi e col mondo che gioca, i giocatori del computer
# prendono dai tornei e dalle sfide quasi quanto dalla seduta e il mondo è più forte; la forma chiusa
# all'anno 10, in tre giri, dà A -38,33 e B 1,0295, con la mediana del valore a 135 e lo stipendio
# pagato a 100, 200 e da 450 a 470 euro al decimo, cinquantesimo e novantesimo percentile, tesserati al
# 91 per cento. All'anno 20 la mediana del valore sale a 144, lo stipendio mediano a 240 e quello del
# decimo percentile a 110 o 120. La carta è strumenti/economia_tappa_12.txt.
CARATTERISTICHE_VALORE = (*COLPI_DELLO_SCAMBIO, *COLPI_DI_BATTUTA, "chiusura_dritto", "chiusura_rovescio", "blocco_dritto", "blocco_rovescio",
                          "difesa", "tenutapaletta", "controllopalla", "attacco", "precisione", "forza", "resistenza")
PESI_VALORE = {
    "lungolineasx": 0.47, "lungolineadx": 0.47, "diagonalesx": 0.50, "diagonaledx": 0.50, "singolaspondasx": 0.49, "singolaspondadx": 0.49,
    "doppiaspondasx": 0.49, "doppiaspondadx": 0.49, "triplaspondasx": 0.42, "triplaspondadx": 0.42, "bomba": 0.52, "battutasx": 0.47,
    "battutadx": 0.47, "chiusura_dritto": 2.27, "chiusura_rovescio": 2.80, "blocco_dritto": 1.31, "blocco_rovescio": 1.57, "difesa": 3.41,
    "tenutapaletta": 1.26, "controllopalla": 0.80, "attacco": 1.41, "precisione": 10.55, "forza": 5.78, "resistenza": 3.80,
}
PESI_TRATTI = {"mancino": 3.0, "ambidestro": 4.5, "giocorapido": 0.9, "cambiovelocita": 4.8}
SCALA_VALORE_A = -38.33
SCALA_VALORE_B = 1.0295
SOGLIA_PESO_INERTE = 0.25
# La tappa 12, il mondo che gioca, decisione D32 e progetto definitivo del 13 ottobre 2026. Le
# costanti nascono man mano che nascono le parti del mondo che le usano, ciascuna col suo racconto.
# Il minimo d'iscritti di un modello di torneo: sotto i quattro un torneo non ha senso, e i ricorrenti
# del calendario predefinito si giocano già con quattro, punto 4.4 del progetto; sotto il minimo
# l'edizione si annulla con i rimborsi, risposta 19 di Gabriele.
MINIMO_ISCRITTI = 4
# Il montepremi minimo che la federazione garantisce a ogni sede di un torneo, al massimo: così un
# modello che si gioca ogni settimana non stampa denaro, punto 3.3 del progetto. Il mondiale ne ha
# 3.000, risposta 10 di Gabriele.
MONTEPREMI_MINIMO_MASSIMO = 5000
# Gli infortuni in gara, D32, risposte 6 e 7 di Gabriele e la sua regola sugli infortuni, punto 7 del
# progetto. Gli infortuni d'incontro di prima erano troppo frequenti rispetto alla realtà: quelli che
# fermano il giocatore scendono a un quinto, estratti a fine set, e il ritiro in campo diventa raro;
# il resto diventa acciacchi, cioè a fine incontro il giocatore risente di un colpo, gioca lo stesso,
# ma per qualche giorno rende un poco meno. La probabilità che succeda qualcosa resta quella di prima.
# Misurato sulla popolazione a regime, al meglio dei 3 un incontro su 89 finisce per ritiro, e in un
# torneo da 32 un incontro su 42 non è regolare, fra ritiri e tavolini: vicino all'uno su 100 e
# all'uno su 45 di Gabriele. Il rischio della seduta all'intensa, D31, resta com'è.
QUOTA_INFORTUNI_CHE_FERMANO = 0.2
# L'acciacco: «qualche giorno» sono da 3 a 7 giorni, «un poco meno» un calo dell'efficienza estratto
# fra il minimo e il massimo, pieno il primo giorno, che scende in linea retta fino a zero. Le prime
# stime dell'architetto erano 0,012 e 0,028, con la media a 0,02. La taratura del 14 ottobre 2026,
# strumenti/banco_partite.py --acciacco, punto 13.1 del progetto: ogni giocatore contro il proprio
# gemello, con gli stessi semi, senza calo e col calo del primo giorno a sei scale delle prime stime,
# su tre semi, 30.000 incontri al meglio dei 3 di cui un quinto fra i forti alla pari. Con le prime
# stime l'acciaccato vinceva il 45,0, il 44,2 e il 44,5 per cento, dentro la banda dal 44 al 46, ma
# sotto il 45 del mezzo: ogni scala in più toglie circa 6 punti di vittoria, e la scala che porta al
# 45 è 0,92, cioè 0,011 e 0,0257 nella proporzione delle prime stime, calo medio 0,0184. Il collaudo di
# Gabriele dirà se il calo si sente.
ACCIACCO_GIORNI_MINIMO = 3
ACCIACCO_GIORNI_MASSIMO = 7
ACCIACCO_CALO_MINIMO = 0.011
ACCIACCO_CALO_MASSIMO = 0.0257
# La fatica della giornata di torneo, risposta 5 di Gabriele: ogni incontro dopo il primo del giorno
# parte con un quarto delle azioni già giocate quel giorno da ciascuno, nel motore e nell'esito rapido.
FATICA_RESIDUA_GIORNATA = 0.25
# La gloria col palmarès degli ultimi 5 anni del calendario, D32 e risposta 11 di Gabriele, punto 9.2
# del progetto. Le costanti della formula, che fino alla tappa 11 erano numeri dentro
# aggiorna_gloria, stanno qui, perché la taratura le possa toccare: la base, il valore medio, l'età e
# i tesserati restano quelli di prima. Le medaglie dei tesserati e le coppe valgono quello che
# valevano, pesate per l'importanza del torneo, ma contano soltanto quelle dei 60 mesi fino a oggi.
GLORIA_BASE = 60
K_GLORIA_ICV = 0.4
ETA_RIFERIMENTO_GLORIA = 35
K_GLORIA_ETA = 1.5
K_GLORIA_TESSERATI = 15
PUNTI_MEDAGLIE_GLORIA = {"oro": 30, "argento": 15, "bronzo": 5, "legno": 1}
PUNTI_COPPE_GLORIA = {"oro": 100, "argento": 50, "bronzo": 20, "legno": 5}
MESI_PALMARES_GLORIA = 60
# I coefficienti della radice dei punti: erano 8 per le medaglie e 12 per le coppe, e con i volumi del
# calendario il palmarès avrebbe fatto l'83 per cento della gloria. Gabriele lo vuole a metà, risposta
# 11: il 50 per cento della gloria della polisportiva mediana del computer dopo vent'anni, il 65 per
# il primo decimo. Le prime stime erano 3 e 3. La taratura del 14 ottobre 2026, punto 13.4: con 3 e 3,
# all'anno 20, il palmarès faceva il 38 per cento della gloria mediana e il 47 del primo decimo.
# strumenti/simulazione_lunga.py --cerca-economia li cerca in forma chiusa sul campione dell'anno 20,
# dove la finestra di cinque anni del calendario è piena: il primo giro ha dato 9,01 e 0, il secondo
# 3,36 e 9,79, perché le coppe, soprattutto quelle della Coppa delle polisportive, stanno nelle
# polisportive più gloriose e alzano il primo decimo. Con questi due, e con la scala e lo sponsor
# trovati dopo, il palmarès fa all'anno 20 il 51 per cento della gloria della polisportiva mediana del
# computer e dal 65 al 66 del primo decimo, dentro i bersagli dal 45 al 55 e dal 60 al 70; all'anno 10,
# con la finestra ancora a metà, il 44 e il 59.
K_GLORIA_MEDAGLIE = 3.36
K_GLORIA_COPPE = 9.79
# Una coppa d'oro di una sfida vale 2 punti, una della Coppa delle polisportive 300: cinque anni di
# sfide valgono quanto una Coppa vinta.
IMPORTANZA_COPPA_SFIDA = 0.02
# La coppa d'argento di una sfida persa giocando, decisione 3 di Gabriele del 14 ottobre 2026: resta,
# come vuole D32, ma nella gloria vale una piccola parte della coppa d'oro, così perdere tante sfide non
# conviene. Prima valeva la metà, come tutte le coppe d'argento: con la revisione del 14 ottobre 2026,
# novanta sfide perse in cinque anni davano 93 punti di gloria, circa 725 euro di sponsor al mese, e
# nella polisportiva mediana del computer le coppe delle sfide facevano tre quarti della gloria del
# palmarès. Con un decimo, perderle tutte vale nella gloria meno di un terzo di vincerle tutte, perché
# la gloria prende la radice dei punti. È il coefficiente che la taratura del passo seguente fissa
# insieme alla gloria; le coppe d'argento della Coppa delle polisportive restano a metà dell'oro.
QUOTA_GLORIA_ARGENTO_SFIDA = 0.1
# I punti della classifica mondiale per sempre, D32 e punto 5.9: per posto, fino al posto indicato,
# per l'importanza del torneo; None vale per tutti gli altri. Quelli dell'ultimo anno servono alla
# qualificazione al mondiale.
PUNTI_CLASSIFICA = ((1, 100), (2, 70), (3, 50), (4, 40), (8, 25), (16, 12), (32, 5), (None, 1))
GIORNI_PUNTI_RECENTI = 365
# I podi dei tornei con l'importanza almeno così, mondiali e coppa, sono titoli: hanno una voce a sé
# nei diari e nella scheda.
IMPORTANZA_TITOLO = 3
# La voce aggregata dell'anno nei diari, punto 5.11: si cerca fra le prime venti voci.
MASSIMO_VOCI_RICERCA_AGGREGATA = 20
# La fedeltà dai successi, D32: 4 punti per un oro vinto col club, 3 per l'argento, 2 per il bronzo,
# 1 per il legno, e 1 per ogni sfida vinta.
FEDELTA_PER_MEDAGLIA = {"oro": 4, "argento": 3, "bronzo": 2, "legno": 1}
FEDELTA_PER_SFIDA_VINTA = 1
# Il ritmo dei tornei, regola di Gabriele in D32 e risposta 2: un torneo ogni due mesi simulati per
# atleta, per il computer, per i liberi e per l'iscrizione automatica dei tuoi; a mano no. Dopo il
# sorteggio di ogni edizione che gioca, l'iscrizione automatica aspetta 61 giorni, più o meno uno
# scarto di 3, tirato dal numero dell'atleta e dell'edizione: senza, chi gioca la stessa edizione
# resterebbe in fila con gli altri per sempre, e il carico si ammasserebbe in pochi giorni. Si cerca
# l'edizione da una settimana prima, e alla nascita la prima data si sparge su due mesi.
GIORNI_FRA_TORNEI = 61
SCARTO_FRA_TORNEI = 3
GIORNI_ANTICIPO_ISCRIZIONE = 7
GIORNI_RITMO_INIZIALE = 60
# Il computer e i liberi non iscrivono chi ha giocato troppo di recente, D32 e risposta 3: l'eccesso
# di carico è la costanza recente meno quella della sua seduta, e la soglia scende con l'età, da 0,15
# fino ai 45 anni a 0,05 dai 65. Così sotto i 50 anni non aspetta nessuno, i titolari delle sfide
# cominciano ad aspettare verso i 57 anni, e dai 60 giocano circa un torneo ogni tre mesi.
SOGLIA_ECCESSO_CARICO_GIOVANI = 0.15
ETA_SOGLIA_CARICO_GIOVANI = 45
SOGLIA_ECCESSO_CARICO_ANZIANI = 0.05
ETA_SOGLIA_CARICO_ANZIANI = 65
# Le sedi concluse restano intere nel pannello per due settimane simulate; l'albo tiene il podio per sempre.
CONSERVAZIONE_TORNEI_CONCLUSI_GIORNI = 14
# Le sfide fra polisportive, D32 e punto 8 del progetto. Il primo del mese ogni polisportiva riceve
# due sfide da lanciare, fino a quattro; una sfida giocata ne consuma una, una rifiutata o decaduta no.
SFIDE_AL_MESE = 2
SFIDE_ACCUMULABILI = 4
# Chi ha giocato una sfida riposa cinque giorni prima di accettarne un'altra, o di lanciarla.
RIPOSO_SFIDA_GIORNI = 5
# Il computer lancia una delle sue sfide col 7 per cento al giorno, circa due al mese, e prova fino a
# tre bersagli a caso.
PROB_LANCIO_SFIDA_CPU = 7
TENTATIVI_SFIDA_CPU = 3
# Il carattere di ogni polisportiva del computer, che nasce dal suo nome e non si salva: la forbice del
# rapporto fra la forza della squadra avversaria e la propria dentro cui accetta o lancia una sfida.
FORBICI_SFIDA = {"prudente": (0.85, 1.15), "equilibrata": (0.75, 1.30), "ardita": (0.60, 1.60)}
# I convocati di una sfida, titolari e riserve, al massimo; il giorno per rispondere a una sfida che
# arriva; le sfide dei tuoi che si possono riascoltare.
CONVOCATI_SFIDA = 6
GIORNI_RISPOSTA_SFIDA = 1
DIFFERITE_SFIDE_TUE = 10
# Le gare del mondo per gli strumenti, punto 13.3 del progetto: le sfide che una polisportiva del
# computer gioca in un mese, e per fascia d'età, al giorno per giocatore in attività che non è
# dell'utente, i conteggi grezzi delle gare, cioè i punti allenamento dei tornei e delle sfide divisi per
# il fattore della loro fonte, e le volte per l'importanza degli incontri di torneo, delle fasi superate,
# dei piazzamenti, col premio a scalare senza la sua base, e delle sfide. Li misura
# strumenti/simulazione_lunga.py, e li usano strumenti/mondi_sintetici.py, perché i giocatori dei mondi
# sintetici giochino come quelli del mondo, e strumenti/carriera_perfetta.py. La prima misura, del 14
# ottobre 2026, era la media del terzo anno di calendario di due simulazioni di tre anni coi valori di
# partenza della tappa, quando i tornei a testa dei tesserati sani erano 4,1 e 4,3 l'anno, sotto il
# ritmo di Gabriele, perché le casse del computer erano ancora quelle di prima della taratura
# dell'economia. Questi sono quelli dopo l'economia: la media degli anni di calendario dal quarto al
# sesto di quattro simulazioni di vent'anni, semi 2026, 7, 13 e 21, coi tornei a testa a 5,6 l'anno e
# 2,1 sfide al mese per polisportiva; i punti dei tornei sono dal 10 al 40 per cento più di prima.
SFIDE_GIOCATE_AL_MESE = 2.1
CONTEGGI_GARE_MONDO = (
    (9, 20, 0.2095, 0.0270, 0.0626, 0.0125, 0.0017, 0.0155),
    (20, 35, 0.2464, 0.0411, 0.0703, 0.0211, 0.0034, 0.0231),
    (35, 50, 0.2142, 0.0369, 0.0640, 0.0151, 0.0022, 0.0215),
    (50, 76, 0.2025, 0.0431, 0.0619, 0.0138, 0.0019, 0.0265),
)
# La convocazione al mondiale per gli strumenti, dalla revisione del 14 ottobre 2026: i punti della
# classifica dell'ultimo anno del trentaduesimo convocato del mondo a regime, per sesso, cioè la soglia
# che la carriera perfetta deve passare all'apertura del mondiale, come nel mondo, invece del punteggio
# di classe del trentaduesimo del mondo sintetico. Misurati sulle popolazioni salvate dalla simulazione
# lunga agli anni 40 e 60 dei semi 101, 404 e 8888: da 590 a 620 punti per gli uomini, da 600 a 625 per
# le donne; all'anno 20 erano da 570 a 600. Nel mondo a regime i convocati sono per circa un terzo fra i
# primi 32 per classe, e gli altri arrivano fino al cinquecentesimo posto e oltre.
PUNTI_PER_IL_MONDIALE = {"m": 605.0, "f": 610.0}


def discrepanze_raggruppamenti():
    """
    Confronta i gruppi di caratteristiche di gioco con l'elenco completo, fisiche escluse.
    Restituisce le mancanti nei gruppi e quelle in più: due insiemi vuoti se tutto torna.
    Il vecchio sd.py faceva questo controllo a ogni avvio; ora lo fa la suite dei test.
    """
    definite = set(CARATTERISTICHE_DIFESA_BASE + CARATTERISTICHE_ATTACCO_BASE + CARATTERISTICHE_CONTROLLO_BASE)
    totali = {attr for attr in ATTRIBUTI_BASE_CON_ALLENABILI if attr not in CARATTERISTICHE_FISICHE_BASE}
    return totali - definite, definite - totali
