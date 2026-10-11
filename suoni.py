"""
Gli effetti sonori della finestra di MESS: un suono per ogni evento, con Acusticator di GBUtils.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la decisione D24, sul modello dei suoni di MeTeOra e di PokerMachine. Ogni
evento ha il suo preset e nessun preset serve due eventi; nessuno è un'onda quadra, salvo donazione
per l'invito al caffè, come negli altri programmi del parco. I preset vengono tutti dalla collezione
condivisa di GBUtils: quelli che c'erano già portano la firma "Usato da: mess.", quelli fatti
apposta per MESS hanno il prefisso mess_ e sono entrati nella collezione con la V199.
Il volume degli effetti, da 0 a 100, sta nelle impostazioni, e a zero non parte niente. Moltiplica
il suono intero: a 50, il predefinito, ogni preset suona com'è stato pensato, a 100 il doppio, a 25
la metà, e le parti più piane, come gli echi, restano nella stessa proporzione con le altre.
Nessun suono blocca la finestra, salvo quello dell'uscita, che aspetta di finire con una scadenza
perché il programma non lo tronchi chiudendosi. Due suoni non si sovrappongono: quello che deve
seguirne un altro si mette in coda, e parte quando il primo è finito.
I suoni della partita non stanno qui ma in partita_sonora.py, con la tappa 10, e nessuno è uguale a
un suono della finestra: lo controlla una prova.
Dal 2026-10-08, con l'amichevole della tappa 9 nella finestra, c'è il gruppo delle partite: i
dialoghi dell'amichevole, i suoi esiti, il punto per punto e la cronaca salvata, quattordici suoni
nuovi entrati nella collezione con la V201. Sono suoni della finestra, non della partita.
Con la decisione D29 arrivano i comandi della partita dal vivo: pausa, ripresa, ascolto fino a fine
set, cambio di lato e velocità, e la velocità di gioco nelle impostazioni. Quattro suoni sono nuovi,
mess_fino_a_fine_set, mess_dall_altra_parte, mess_velocita_di_gioco e mess_velocita_salvata, e
cinque della collezione portano la firma di MESS, con la V202; i quattro del punto per punto passano
ai comandi della finestra dal vivo.
Con la decisione D30 la partita ha un volume suo, nel dialogo degli effetti, con il suo suono di
prova, mess_prova_volume_partita, anche lui nella V202: suona al fattore della partita, non a quello
degli effetti, perché faccia sentire il livello che la partita avrà.
Con la fase dei timbri della tappa 10 ogni evento ha anche la sua azione detta a parole, in AZIONI:
la legge l'elenco dei suoni per Acu_Maker, suoni_di_mess.txt, che strumenti/elenco_suoni.py scrive
dalle mappe della finestra e della partita, richiesta di Gabriele della decisione D29.
Con la tappa 11, il 2026-10-09, decisione D31, arrivano tre gruppi: la sala allenamento, i
contratti con i rinnovi, e le notizie dell'avanzamento sui contratti e sugli infortuni in seduta.
Sono ventidue suoni nuovi, tutti mess_, entrati nella collezione con la V204. La probabilità del
rinnovo si sposta d'altezza come quella dell'ingaggio, ma con un timbro suo. Le parti della tappa
11 sono di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import sys
import time

import impostazioni as modulo_impostazioni
from testi import conta

# Gli eventi, gruppo per gruppo: ogni gruppo ha un titolo, che è anche quello del gruppo d'ascolto
# di ascolta_suoni.py, e i suoi eventi con il preset della collezione.
GRUPPI = (
    ("Applicazione, l'avvio e l'uscita", {
        # Il motivo di MESS e le sue varianti: il mondo caricato, quello nato al primo avvio, quello
        # ripreso dalla copia di sicurezza e l'avvio con le collezioni di nomi difettose.
        "avvio": "mess_avvio",
        "avvio_mondo_nuovo": "mess_mondo_nuovo",
        "avvio_dalla_copia": "mess_avvio_dalla_copia",
        "avvio_con_avvisi": "mess_avvio_con_avvisi",
        # Il motivo al contrario, e la sua versione grave quando il salvataggio finale non riesce.
        "uscita": "mess_uscita",
        "uscita_senza_salvataggio": "mess_uscita_senza_salvataggio",
    }),
    ("Applicazione, i salvataggi e gli errori gravi", {
        "salvataggio_riuscito": "meditimer_banco_salvato",
        "salvataggio_con_avviso": "mess_salvataggio_con_avviso",
        "salvataggio_non_riuscito": "mess_salvataggio_non_riuscito",
        "salvataggio_illeggibile": "mess_salvataggio_illeggibile",
        # Un'eccezione che nessuno aspettava: l'unico allarme vero.
        "errore_imprevisto": "sirena_d_allarme_1",
    }),
    ("Applicazione, il fuoco, i dialoghi e gli elenchi", {
        # F5 e F7 suonano come in Tornello e MeTeOra; il Tab resta muto.
        "fuoco_vista": "spostamento_f5",
        "fuoco_barra": "spostamento_f7",
        "annullato": "meteora_annullamento",
        "lavoro_concluso": "terminata",
        "nessuna_selezione": "mess_tasto_a_vuoto",
        "campo_da_correggere": "mess_campo_da_correggere",
        # Un elenco che si restringe mentre si scrive: solo nel passaggio da pieno a vuoto e ritorno.
        "elenco_svuotato": "espelli",
        "elenco_ripopolato": "aggiunta_giocatore",
        "domanda": "meteora_sottotitoli_accesi",
    }),
    ("Applicazione, l'aiuto", {
        "guida": "pokermachine_manuale",
        "novita": "jingle_scoperta",
        "novita_illeggibile": "mess_novita_illeggibile",
        "informazioni": "mess_informazioni",
        # L'unica onda quadra, così com'è, come in Tornello, Terminal Beast e MeTeOra.
        "caffe": "donazione",
        "caffe_paypal": "carillon_dolce",
    }),
    ("Applicazione, le impostazioni", {
        "dialogo_aspetto": "scintillio_di_ghiaccio",
        "aspetto_predefiniti": "meteora_bande_azzerate",
        "aspetto_applicato": "meteora_impostazione_cambiata",
        "impostazioni_non_salvate": "mess_impostazioni_non_salvate",
        "dialogo_conservazione": "meteora_console_salvata",
        "conservazione_applicata": "mess_diari_conservati",
        "dialogo_effetti_sonori": "meteora_impostazioni",
        "prova_volume_effetti": "mess_prova_volume",
        # La prova del volume della partita, decisione D30: una pallina colpita che attraversa il
        # tavolo e sbatte sulla sponda, al fattore della partita e non a quello degli effetti.
        "prova_volume_partita": "mess_prova_volume_partita",
        "effetti_sonori_applicati": "conferma",
        # La velocità di gioco della partita dal vivo: il tic tac di un metronomo, e tre note che scendono e si posano.
        "dialogo_velocita_di_gioco": "mess_velocita_di_gioco",
        "velocita_di_gioco_salvata": "mess_velocita_salvata",
    }),
    ("Mondo, i giocatori", {
        "dialogo_scheda_giocatore": "pokermachine_raddoppio_carta",
        "scheda_giocatore": "meteora_tag_letti",
        "dialogo_diario_giocatore": "pokermachine_consiglio",
        "diario_giocatore": "mess_diario_a_ritroso",
        "elenco_giocatori": "meteora_ramo_aggiornato",
        "classifica": "meditimer_classifiche",
        "top_10": "mess_fuochi_d_artificio",
        "statistiche_mondo": "meteora_marcatori",
    }),
    ("Mondo, la sessione e la ricerca", {
        # Chi arriva e chi se ne va: due gesti speculari.
        "nuovi_arrivati": "meteora_marcatori_importati",
        "ritirati_sessione": "mess_saluto_in_eco",
        "usciti_sessione": "mess_spirale_breve",
        "dialogo_ricerca": "mess_sonar",
        "ricerca_con_risultati": "meteora_marcatori_trovato",
        "ricerca_senza_risultati": "meteora_marcatori_non_trovato",
        "risultati_ricerca": "apertura",
        "nessuna_ricerca": "meditimer_allarme_zittito",
    }),
    ("Mondo, il tempo e le notizie", {
        "data_e_avanzamento": "meditimer_ora",
        "riepilogo_avanzamento": "mess_notiziario",
        "nessun_avanzamento": "mess_notiziario_vuoto",
        "vecchie_glorie": "arpeggio_pensoso",
        # L'avanzamento del mondo, al massimo un suono per volta, scelto da evento_avanzamento:
        # il giorno qualunque è un'alba, e le notizie del giorno sono la stessa alba con una coda.
        "mondo_avanzato": "mess_nuovo_giorno",
        "mondo_avanzato_piu_giorni": "mess_giorni_trascorsi",
        "notizia_morte": "mess_giorno_di_lutto",
        "notizia_ritiro": "mess_giorno_di_congedo",
        "notizia_uscita_prematura": "mess_giorno_di_partenza",
        "polisportiva_cpu_nata": "meditimer_banco_avvio",
        "polisportiva_cpu_chiusa": "mess_motore_che_si_spegne",
    }),
    ("Polisportive, fondazione, cambio e password", {
        "dialogo_nuova_polisportiva": "mess_quinte_sovrapposte",
        "polisportiva_fondata": "mess_fischio_d_inizio",
        "dialogo_cambia_polisportiva": "mess_scambio_di_posto",
        "polisportiva_attivata": "controllo_ok",
        "nessuna_polisportiva_tua": "mess_invito_a_fondare",
        "nessuna_polisportiva_attiva": "mess_segnale_di_occupato",
        "password_sbagliata": "mess_maniglia_scossa",
        "password_non_coincidono": "mess_due_voci_stonate",
        "dialogo_password": "mess_tastierino_del_codice",
        "password_impostata": "mess_chiave_che_chiude",
        "password_tolta": "mess_chiave_che_apre",
    }),
    ("Polisportive, chiusura, schede e svincolo", {
        "richiesta_password": "mess_bussare_alla_porta",
        "domanda_chiusura_polisportiva": "mess_campana_a_martello",
        "polisportiva_chiusa": "mess_triplice_fischio",
        "scheda_polisportiva": "mess_occhiata_alla_scheda",
        "tesserati_polisportiva": "mess_rosa_che_sfila",
        "diario_polisportiva": "mess_penna_sul_diario",
        "elenco_polisportive": "mess_albo_che_scorre",
        "dialogo_svincolo": "mess_porta_che_cigola",
        "tesserato_svincolato": "mess_contratto_strappato",
        "rosa_vuota": "mess_eco_nello_spogliatoio",
    }),
    ("Polisportive, le notizie dei tuoi tesserati", {
        "tuo_tesserato_bandiera": "mess_fanfara_della_bandiera",
        "tuo_tesserato_ritirato": "mess_scarpe_al_chiodo",
        "tuo_tesserato_uscito_di_scena": "mess_il_silenzio",
    }),
    ("Economia, il mercato", {
        # La saracinesca che si alza: la stessa che si abbassa quando le mosse del giorno finiscono.
        "dialogo_mercato": "mess_mercato_aperto",
        # Scattano a ogni freccia su Mostra e Ordina per: un tocco minimo.
        "mercato_scelta_cambiata": "mess_mercato_mostra",
        "mercato_ordine_cambiato": "mess_mercato_ordine",
        "dialogo_filtro_mercato": "mess_filtro_dialogo",
        "filtro_aggiunto": "mess_filtro_aggiunto",
        "filtro_tolto": "mess_filtro_tolto",
        "filtri_tutti_tolti": "mess_filtri_tutti_tolti",
        "mercato_scheda_giocatore": "carta_girata",
    }),
    ("Economia, le offerte", {
        "dialogo_cifra_ingaggio": "mess_cifra_ingaggio",
        # Il timbro della probabilità d'ingaggio: l'altezza la sposta probabilita_in_semitoni.
        "probabilita_ingaggio": "mess_probabilita",
        "dialogo_cifra_offerta_d_acquisto": "mess_cifra_offerta",
        "ingaggio_accettato": "mess_ingaggio_accettato",
        "ingaggio_rifiutato": "mess_ingaggio_rifiutato",
        "acquisto_fatto": "mess_acquisto_fatto",
        "offerta_d_acquisto_accettata": "mess_offerta_accettata",
        "offerta_d_acquisto_rifiutata": "mess_offerta_rifiutata",
        "cassa_insufficiente": "mess_cassa_vuota",
        "mosse_finite": "mess_mosse_finite",
        "rosa_piena": "pokermachine_scudi_pieni",
    }),
    ("Economia, vendite e arretrati", {
        "dialogo_vendite": "mess_vendite_aperte",
        "messo_in_vendita": "meteora_marker_messo",
        "prezzo_di_vendita_cambiato": "meteora_marker_rinominato",
        "tolto_dalla_vendita": "meteora_marker_eliminato",
        "vendita_non_attiva": "mess_vendita_non_attiva",
        "dialogo_arretrati": "mess_arretrati_aperti",
        "nessun_arretrato": "mess_conti_a_posto",
        # I tre gradini del pagamento: in parte, saldato, e tutti saldati.
        "arretrati_pagati_in_parte": "mess_arretrati_in_parte",
        "arretrati_saldati": "mess_arretrati_saldati",
        "arretrati_tutti_saldati": "mess_arretrati_tutti_saldati",
        "bilancio": "mess_bilancio",
    }),
    ("Economia, i conti del mese", {
        "primo_del_mese": "mess_primo_del_mese",
        "stipendi_non_pagati": "mess_stipendi_non_pagati",
        "tuoi_tesserati_partiti": "mess_tesserati_partiti",
        "tuo_tesserato_venduto": "mess_tesserato_venduto",
    }),
    ("Partite, l'amichevole", {
        # I due giocatori si scelgono come un invito e la sua risposta, dai due lati del tavolo.
        "dialogo_amichevole": "mess_invito_a_giocare",
        "dialogo_avversario": "mess_avversario_che_risponde",
        "dialogo_opzioni_amichevole": "mess_opzioni_dell_amichevole",
        "nessun_giocatore_oggi": "mess_torna_domani",
        # L'esito si sente solo quando si mostra: la fanfara che sale, la stessa che scende, e la
        # stretta di mano quando i due giocatori sono tutti e due tuoi.
        "amichevole_vinta": "mess_amichevole_vinta",
        "amichevole_persa": "mess_amichevole_persa",
        "amichevole_fra_tuoi": "mess_stretta_di_mano",
        "nessun_incontro": "mess_nessun_incontro",
        "cronaca_salvata": "mess_cronaca_salvata",
        "cronaca_non_salvata": "mess_cronaca_non_salvata",
    }),
    ("Partite, la partita dal vivo", {
        # Dalla decisione D29 il punto per punto con F8 è diventato la partita dal vivo, che riusa i
        # suoi suoni: il conto alla rovescia apre la finestra, il guizzo salta il riscaldamento, i
        # cinque guizzi vanno alla fine con Alt+V, e la cadenza risponde ai comandi a incontro finito.
        "amichevole_al_via": "mess_conto_alla_rovescia",
        "riscaldamento_saltato": "mess_punto_successivo",
        "resto_dell_incontro": "mess_resto_dell_incontro",
        "incontro_finito": "mess_incontro_finito",
        # Esc esce dalla partita dal vivo senza svelare il risultato, decisione D30: un suono suo, che
        # non dice chi ha vinto (Gabriele, 8 ottobre 2026, per la regola di un suono per ogni evento).
        "amichevole_registrata": "mess_amichevole_registrata",
        # Il cronometro che si ferma e riparte, la scala che sale di filato fino a fine set, il giro
        # del tavolo per l'altra testata, e il metronomo che accelera, rallenta o bussa contro il
        # fondo scala.
        "dal_vivo_pausa": "meditimer_cronometro_pausa",
        "dal_vivo_ripresa": "meditimer_cronometro_ripreso",
        "dal_vivo_fino_a_fine_set": "mess_fino_a_fine_set",
        "dal_vivo_cambio_lato": "mess_dall_altra_parte",
        "dal_vivo_piu_veloce": "meteora_velocita_su",
        "dal_vivo_piu_lenta": "meteora_velocita_giu",
        "dal_vivo_velocita_al_limite": "meteora_velocita_al_limite",
    }),
    ("Allenamento, la sala", {
        # Il passo del riscaldamento apre la sala; il peso che sale è la spesa a mano, la stessa
        # salita con l'arpeggio è quella secondo il programma, e le scivolate a scala sono la squadra.
        "dialogo_sala_allenamento": "mess_sala_allenamento",
        "allenamento_fatto": "mess_allenamento_fatto",
        "allenamento_completo": "mess_allenamento_completo",
        "allenati_tutti": "mess_allenati_tutti",
        # La campanella della classe guadagnata suona in coda all'esito.
        "classe_salita": "mess_classe_salita",
        # I tre avvisi che lasciano aperta la sala: il sacchetto vuoto, il soffitto, il passo zoppo.
        "punti_insufficienti": "mess_portafoglio_vuoto",
        "caratteristica_al_massimo": "mess_al_massimo",
        "allenando_infortunato": "mess_allenando_fermo",
        # Scattano a ogni freccia sulle due scelte: un tocco minimo e un battito di cuore.
        "programma_cambiato": "mess_programma_cambiato",
        "intensita_cambiata": "mess_intensita_cambiata",
    }),
    ("Contratti, i rinnovi", {
        "dialogo_contratti": "mess_contratti_aperti",
        # Il timbro della probabilità del rinnovo: l'altezza la sposta probabilita_in_semitoni, come
        # per l'ingaggio, ma il suono è un altro, perché non si confondano.
        "probabilita_rinnovo": "mess_probabilita_rinnovo",
        # Il motivo che sale e si ripete, il suo specchio che scende, e lo stesso a dente di sega con
        # la porta che si chiude al terzo rifiuto.
        "rinnovo_accettato": "mess_rinnovo_firmato",
        "rinnovo_rifiutato": "mess_rinnovo_rifiutato",
        "rinnovo_chiuso": "mess_rinnovo_chiuso",
        # Le quattro proposte che non si possono fare, ciascuna col suo perché.
        "rinnovo_fuori_finestra": "mess_rinnovo_non_ancora",
        "rinnovo_gia_proposto_oggi": "mess_rinnovo_domani",
        "rinnovo_senza_proposte": "mess_rinnovo_niente_da_fare",
        "rinnovo_gia_concordato": "mess_rinnovo_gia_fatto",
    }),
    ("Contratti e allenamento, le notizie", {
        # Il promemoria suona due volte per contratto: all'ingresso nella finestra e all'ultimo mese.
        "tuoi_contratti_in_scadenza": "mess_contratti_in_scadenza",
        "tuoi_contratti_scaduti": "mess_contratto_scaduto",
        "tuo_tesserato_infortunato_in_seduta": "mess_infortunio_in_allenamento",
    }),
)
EVENTI = {evento: preset for _titolo, gruppo in GRUPPI for evento, preset in gruppo.items()}

# Ogni evento detto a parole: l'azione che lo fa suonare. La legge l'elenco dei suoni per Acu_Maker,
# suoni_di_mess.txt, scritto da strumenti/elenco_suoni.py; una prova controlla che ogni evento abbia
# la sua.
AZIONI = {
    "avvio": "il programma si apre sul mondo caricato dal salvataggio",
    "avvio_mondo_nuovo": "il primo avvio, quando nasce un mondo nuovo",
    "avvio_dalla_copia": "l'avvio con il mondo ripreso dalla copia di sicurezza, perché il salvataggio principale non si usa",
    "avvio_con_avvisi": "l'avvio con le collezioni di nomi e cognomi difettose",
    "uscita": "l'uscita dal programma con il mondo salvato",
    "uscita_senza_salvataggio": "l'uscita dal programma quando il salvataggio finale non riesce",
    "salvataggio_riuscito": "il mondo salvato con Ctrl+S",
    "salvataggio_con_avviso": "il mondo salvato con Ctrl+S, ma con un avviso dell'archivio",
    "salvataggio_non_riuscito": "un salvataggio che non riesce, con Ctrl+S o dopo un'operazione",
    "salvataggio_illeggibile": "all'avvio né il salvataggio né la sua copia si leggono, e il programma si ferma",
    "errore_imprevisto": "un errore imprevisto del programma",
    "fuoco_vista": "F5, il fuoco va nella vista principale",
    "fuoco_barra": "F7, il fuoco va nella barra di stato",
    "annullato": "un'operazione annullata, con Esc o con Annulla in un dialogo",
    "lavoro_concluso": "la chiusura del mercato, delle vendite, degli arretrati, della sala allenamento o dei contratti dopo averci lavorato",
    "nessuna_selezione": "un pulsante premuto senza niente di scelto su cui lavorare",
    "campo_da_correggere": "un valore da correggere in un campo, e il dialogo resta aperto",
    "elenco_svuotato": "un elenco che si restringe mentre si scrive, e resta vuoto",
    "elenco_ripopolato": "un elenco vuoto che torna a riempirsi mentre si scrive",
    "domanda": "una domanda di conferma, con Sì e No",
    "guida": "F1, la guida ai comandi, anche nella finestra dal vivo",
    "novita": "F2, le novità della versione",
    "novita_illeggibile": "F2, quando il file delle novità non si legge",
    "informazioni": "F3, le informazioni con la versione e gli autori",
    "caffe": "Offrimi un caffè, nel menu Aiuto",
    "caffe_paypal": "Dona con PayPal, nell'invito al caffè",
    "dialogo_aspetto": "si apre il dialogo dell'aspetto, colori e caratteri, con Ctrl+P",
    "aspetto_predefiniti": "nel dialogo dell'aspetto, i valori tornano ai predefiniti",
    "aspetto_applicato": "l'aspetto confermato e applicato",
    "impostazioni_non_salvate": "le impostazioni valgono per la sessione ma il file non si scrive",
    "dialogo_conservazione": "si apre il dialogo della conservazione dei diari",
    "conservazione_applicata": "la conservazione dei diari confermata",
    "dialogo_effetti_sonori": "si apre il dialogo degli effetti sonori",
    "prova_volume_effetti": "la prova del volume degli effetti, mentre lo si cambia",
    "prova_volume_partita": "la prova del volume della partita dal vivo, mentre lo si cambia",
    "effetti_sonori_applicati": "i volumi degli effetti e della partita confermati",
    "dialogo_velocita_di_gioco": "si apre il dialogo della velocità di gioco",
    "velocita_di_gioco_salvata": "la velocità di gioco confermata e salvata",
    "dialogo_scheda_giocatore": "si apre la scelta del giocatore di cui leggere la scheda, con Ctrl+G",
    "scheda_giocatore": "la scheda di un giocatore",
    "dialogo_diario_giocatore": "si apre la scelta del giocatore di cui leggere il diario, con Ctrl+Shift+D",
    "diario_giocatore": "il diario di un giocatore",
    "elenco_giocatori": "l'elenco dei giocatori, con Ctrl+E",
    "classifica": "la classifica per valore, con Ctrl+L",
    "top_10": "la TOP 10 dei migliori giocatori, con Ctrl+T",
    "statistiche_mondo": "le statistiche del mondo, con Ctrl+I",
    "nuovi_arrivati": "i nuovi arrivati della sessione, con Ctrl+Shift+N",
    "ritirati_sessione": "i ritirati della sessione, con Ctrl+Shift+R",
    "usciti_sessione": "gli usciti di scena nella sessione, con Ctrl+Shift+U",
    "dialogo_ricerca": "si apre la ricerca dei giocatori, con Ctrl+F",
    "ricerca_con_risultati": "una ricerca che trova dei giocatori",
    "ricerca_senza_risultati": "una ricerca che non trova nessuno",
    "risultati_ricerca": "i risultati dell'ultima ricerca, con Ctrl+R",
    "nessuna_ricerca": "Ctrl+R quando nella sessione non c'è ancora una ricerca",
    "data_e_avanzamento": "la data simulata e il prossimo avanzamento, con Ctrl+D",
    "riepilogo_avanzamento": "il riepilogo dell'ultimo avanzamento del mondo, con Ctrl+Shift+A",
    "nessun_avanzamento": "il riepilogo dell'avanzamento quando il mondo non è ancora avanzato",
    "vecchie_glorie": "le vecchie glorie, con Ctrl+Shift+V",
    "mondo_avanzato": "il mondo avanza di un giorno, senza notizie importanti",
    "mondo_avanzato_piu_giorni": "il mondo avanza di più giorni in una volta",
    "notizia_morte": "nell'avanzamento del giorno muore un giocatore",
    "notizia_ritiro": "nell'avanzamento del giorno qualcuno si ritira",
    "notizia_uscita_prematura": "nell'avanzamento del giorno qualcuno lascia lo showdown prima del tempo",
    "polisportiva_cpu_nata": "nell'avanzamento del giorno nasce una polisportiva del computer",
    "polisportiva_cpu_chiusa": "nell'avanzamento del giorno chiude una polisportiva del computer",
    "dialogo_nuova_polisportiva": "si apre il dialogo della nuova polisportiva, con Ctrl+N",
    "polisportiva_fondata": "una polisportiva fondata",
    "dialogo_cambia_polisportiva": "si apre il dialogo per cambiare la polisportiva attiva, con Ctrl+Shift+C",
    "polisportiva_attivata": "una polisportiva diventa quella attiva",
    "nessuna_polisportiva_tua": "un comando che vuole una tua polisportiva quando non ne hai nessuna",
    "nessuna_polisportiva_attiva": "un comando che vuole la polisportiva attiva quando non ce n'è nessuna",
    "password_sbagliata": "una password sbagliata",
    "password_non_coincidono": "la password e la sua conferma non coincidono",
    "dialogo_password": "si apre il dialogo della password della polisportiva attiva",
    "password_impostata": "la polisportiva protetta da una password",
    "password_tolta": "la password della polisportiva tolta",
    "richiesta_password": "la richiesta della password prima di chiudere una polisportiva protetta",
    "domanda_chiusura_polisportiva": "la domanda se chiudere per sempre la polisportiva attiva",
    "polisportiva_chiusa": "una polisportiva chiusa per sempre",
    "scheda_polisportiva": "la scheda della polisportiva attiva, con Ctrl+M",
    "tesserati_polisportiva": "i tesserati della polisportiva attiva, con Ctrl+Shift+T",
    "diario_polisportiva": "il diario della polisportiva attiva, con Ctrl+Shift+M",
    "elenco_polisportive": "l'elenco delle polisportive, con Ctrl+Shift+E",
    "dialogo_svincolo": "si apre la scelta del tesserato da svincolare, con Ctrl+Shift+S",
    "tesserato_svincolato": "un tesserato svincolato, che torna libero",
    "rosa_vuota": "un comando che vuole i tesserati quando la polisportiva attiva non ne ha",
    "tuo_tesserato_bandiera": "nell'avanzamento un tuo tesserato diventa una bandiera del club",
    "tuo_tesserato_ritirato": "nell'avanzamento un tuo tesserato si ritira",
    "tuo_tesserato_uscito_di_scena": "nell'avanzamento un tuo tesserato muore o lascia lo showdown",
    "dialogo_mercato": "si apre il mercato, con Ctrl+K",
    "mercato_scelta_cambiata": "nel mercato cambia la scelta di chi mostrare",
    "mercato_ordine_cambiato": "nel mercato cambia l'ordine dell'elenco",
    "dialogo_filtro_mercato": "nel mercato si apre la ricerca per aggiungere un filtro",
    "filtro_aggiunto": "nel mercato un filtro aggiunto",
    "filtro_tolto": "nel mercato un filtro tolto",
    "filtri_tutti_tolti": "nel mercato tutti i filtri tolti",
    "mercato_scheda_giocatore": "nel mercato, nella sala allenamento e nei contratti, la scheda del giocatore scelto",
    "dialogo_cifra_ingaggio": "si apre il dialogo della cifra d'ingaggio di un libero",
    "probabilita_ingaggio": "la probabilità che il libero accetti, mentre si scrive la cifra: più è alta, più è acuto",
    "dialogo_cifra_offerta_d_acquisto": "si apre il dialogo della cifra da offrire per un tesserato di un'altra polisportiva",
    "ingaggio_accettato": "il libero accetta l'ingaggio",
    "ingaggio_rifiutato": "il libero rifiuta l'ingaggio",
    "acquisto_fatto": "l'acquisto di un giocatore in vendita",
    "offerta_d_acquisto_accettata": "la polisportiva del computer accetta l'offerta, e il tesserato passa a te",
    "offerta_d_acquisto_rifiutata": "la polisportiva del computer rifiuta l'offerta",
    "cassa_insufficiente": "i soldi in cassa non bastano",
    "mosse_finite": "le mosse di mercato del giorno sono finite",
    "rosa_piena": "la rosa della polisportiva è piena",
    "dialogo_vendite": "si apre il dialogo delle vendite dei tesserati",
    "messo_in_vendita": "un tesserato messo in vendita",
    "prezzo_di_vendita_cambiato": "il prezzo di un tesserato già in vendita cambiato",
    "tolto_dalla_vendita": "un tesserato tolto dalla vendita",
    "vendita_non_attiva": "si vuole togliere dalla vendita un tesserato che in vendita non c'è",
    "dialogo_arretrati": "si apre il pagamento degli arretrati, con Ctrl+Shift+P",
    "nessun_arretrato": "nessun tesserato aspetta arretrati",
    "arretrati_pagati_in_parte": "arretrati pagati in parte, e il tesserato aspetta ancora",
    "arretrati_saldati": "un tesserato riceve tutti gli arretrati",
    "arretrati_tutti_saldati": "pagato l'ultimo debito, nessuno aspetta più arretrati",
    "bilancio": "il bilancio della polisportiva attiva, con Ctrl+B",
    "primo_del_mese": "nell'avanzamento arriva il primo del mese, con gli stipendi pagati",
    "stipendi_non_pagati": "al primo del mese la cassa non basta per gli stipendi",
    "tuoi_tesserati_partiti": "tuoi tesserati se ne vanno per gli stipendi non pagati",
    "tuo_tesserato_venduto": "un tuo tesserato in vendita è stato comprato",
    "dialogo_amichevole": "si apre la scelta del tuo giocatore per un'amichevole, con Ctrl+O",
    "dialogo_avversario": "si apre la scelta dell'avversario dell'amichevole",
    "dialogo_opzioni_amichevole": "si apre il dialogo delle opzioni dell'amichevole",
    "nessun_giocatore_oggi": "oggi nessuno può giocare un'amichevole",
    "amichevole_vinta": "l'amichevole la vince il tuo tesserato",
    "amichevole_persa": "l'amichevole la perde il tuo tesserato",
    "amichevole_fra_tuoi": "un'amichevole fra due tuoi tesserati",
    "nessun_incontro": "Salva la cronaca quando nella sessione non c'è ancora un'amichevole",
    "cronaca_salvata": "la cronaca dell'amichevole salvata nel suo file, con Ctrl+Shift+O",
    "cronaca_non_salvata": "la cronaca dell'amichevole che non si può scrivere nel file",
    "amichevole_al_via": "si apre la finestra della partita dal vivo, con Assisti",
    "riscaldamento_saltato": "nella partita dal vivo il riscaldamento saltato",
    "resto_dell_incontro": "nella partita dal vivo Alt+V, Vai alla fine",
    "incontro_finito": "nella partita dal vivo Alt+F o Alt+L a incontro già finito",
    "amichevole_registrata": "nella partita dal vivo Esc, l'amichevole resta registrata senza svelare il risultato",
    "dal_vivo_pausa": "nella partita dal vivo la pausa, con Invio o spazio mentre l'azione suona",
    "dal_vivo_ripresa": "nella partita dal vivo la ripresa dopo la pausa",
    "dal_vivo_fino_a_fine_set": "nella partita dal vivo Alt+F, ascolta fino a fine set",
    "dal_vivo_cambio_lato": "nella partita dal vivo Alt+L, il lato d'ascolto passa all'altro giocatore",
    "dal_vivo_piu_veloce": "nella partita dal vivo il tasto più, velocità di gioco più alta",
    "dal_vivo_piu_lenta": "nella partita dal vivo il tasto meno, velocità di gioco più bassa",
    "dal_vivo_velocita_al_limite": "nella partita dal vivo più o meno con la velocità già al massimo o al minimo",
    "dialogo_sala_allenamento": "si apre la sala allenamento, con Ctrl+Shift+L",
    "allenamento_fatto": "nella sala allenamento una spesa a mano, punti allenamento su una caratteristica",
    "allenamento_completo": "nella sala allenamento l'allenamento completo di un tesserato secondo il suo programma",
    "allenati_tutti": "nella sala allenamento Allena tutti, ogni tesserato secondo il suo programma",
    "classe_salita": "nella sala allenamento un tesserato sale di classe, dopo l'esito",
    "punti_insufficienti": "nella sala allenamento non ci sono punti da spendere, o la cifra è zero",
    "caratteristica_al_massimo": "nella sala allenamento la caratteristica scelta è già al massimo",
    "allenando_infortunato": "nella sala allenamento il tesserato scelto è infortunato e oggi non si allena",
    "programma_cambiato": "nella sala allenamento cambia il programma del tesserato",
    "intensita_cambiata": "nella sala allenamento cambia l'intensità del tesserato",
    "dialogo_contratti": "si apre il dialogo dei contratti e dei rinnovi, con Ctrl+Shift+K",
    "probabilita_rinnovo": "la probabilità che il tesserato accetti il rinnovo, mentre si scrivono stipendio e durata: più è alta, più è acuto",
    "rinnovo_accettato": "il tesserato accetta il rinnovo del contratto",
    "rinnovo_rifiutato": "il tesserato rifiuta il rinnovo, e si può riprovare un altro giorno",
    "rinnovo_chiuso": "il terzo rifiuto del rinnovo, e il tesserato non tratta più",
    "rinnovo_fuori_finestra": "il rinnovo non si può ancora proporre, perché il contratto non è negli ultimi tre mesi",
    "rinnovo_gia_proposto_oggi": "oggi al tesserato è già stata fatta una proposta di rinnovo",
    "rinnovo_senza_proposte": "il tesserato ha già rifiutato tre proposte e non ne accetta altre",
    "rinnovo_gia_concordato": "il tesserato ha già rinnovato il contratto",
    "tuoi_contratti_in_scadenza": "nell'avanzamento il contratto di un tuo tesserato entra negli ultimi tre mesi, o nell'ultimo",
    "tuoi_contratti_scaduti": "nell'avanzamento il contratto di un tuo tesserato scade senza rinnovo, e lui torna libero",
    "tuo_tesserato_infortunato_in_seduta": "nell'avanzamento un tuo tesserato si infortuna nella seduta d'allenamento",
}

# Il volume a cui ogni preset suona com'è stato pensato.
VOLUME_DI_PROGETTO = 50
# Quanto aspetta al massimo il suono dell'uscita, e la pausa fra due suoni in coda.
ATTESA_USCITA = 2.0
PAUSA_IN_CODA = 0.15
# La probabilità d'ingaggio sposta il suo tic di mezza ottava per ogni 25 punti, un'ottava sotto a
# zero e una sopra a cento: più è alta, più è acuto, come l'ago di uno strumento.
SEMITONI_PER_PUNTO = 12 / 50

# Il volume del momento, letto dalle impostazioni la prima volta che serve, e quando finisce
# l'ultimo suono partito.
_VOLUME = [None]
_FINE_DELL_ULTIMO = [0.0]


def volume_effetti():
    """Il volume degli effetti, da 0 a 100: quello delle impostazioni, o quello dato con imposta_volume."""
    if _VOLUME[0] is None:
        _VOLUME[0] = modulo_impostazioni.carica()["volume_effetti"]
    return _VOLUME[0]


def imposta_volume(volume):
    """Il volume degli effetti da qui in avanti, da 0 a 100."""
    _VOLUME[0] = max(0, min(100, int(volume)))


def attesa():
    """Quanti secondi mancano alla fine dell'ultimo suono partito."""
    return max(0.0, _FINE_DELL_ULTIMO[0] - time.monotonic())


def suona(evento, sync=False, volume=None, semitoni=0.0, fattore=None):
    """
    Suona il preset dell'evento al volume degli effetti, o a quello dato. A volume zero non parte
    niente. sync è quello di Acusticator: falso non aspetta, un numero aspetta al massimo quei
    secondi. semitoni sposta l'altezza, anche di frazioni. fattore, se dato, moltiplica il suono al
    posto del volume: è per la prova del volume della partita, che suona al fattore della partita;
    a fattore zero non parte niente. Vero se il suono è partito. Un evento sconosciuto, un preset
    che manca o una scheda audio che non risponde non fermano il programma.
    """
    if fattore is None:
        volume = volume_effetti() if volume is None else volume
        fattore = volume / VOLUME_DI_PROGETTO
    if fattore <= 0:
        return False
    preset = EVENTI.get(evento)
    if preset is None:
        print(f"MESS: evento sonoro sconosciuto, {evento}", file=sys.stderr)
        return False
    try:
        return _riproduci(evento, preset, sync, fattore, semitoni)
    except Exception as errore:  # noqa: BLE001 - un suono che non parte non deve far cadere un comando della finestra
        print(f"MESS: il suono {evento} non è partito: {errore}", file=sys.stderr)
        return False


def in_coda(evento, **opzioni):
    """
    Suona l'evento quando è finito il suono in corso, più una breve pausa, così due suoni non si
    sovrappongono; se non suona niente, subito. Non blocca: l'attesa la fa un timer di wx.
    """
    resta = attesa()
    if resta <= 0:
        return suona(evento, **opzioni)
    import wx

    wx.CallLater(int((resta + PAUSA_IN_CODA) * 1000), suona, evento, **opzioni)
    return True


def probabilita_in_semitoni(percentuale):
    """Di quanti semitoni si sposta il tic della probabilità d'ingaggio: zero al 50 per cento."""
    return (max(0.0, min(100.0, float(percentuale))) - 50) * SEMITONI_PER_PUNTO


def trasposto(score, semitoni):
    """
    Lo score con le note spostate di tanti semitoni, anche frazionari: le note diventano frequenze
    in hertz, i portamenti coppie di frequenze intere; pause e bande di rumore restano com'erano.
    """
    from GBUtils import frequenza_nota

    fattore = 2 ** (semitoni / 12)
    nuovo = list(score)
    for i in range(0, len(nuovo), 4):
        nota = nuovo[i]
        if isinstance(nota, str) and "." in nota:
            parti = [frequenza_nota(parte) for parte in nota.split(".")]
            if len(parti) == 2 and all(parti):
                nuovo[i] = ".".join(str(round(f * fattore)) for f in parti)
            continue
        frequenza = frequenza_nota(nota)
        if frequenza > 0:
            nuovo[i] = frequenza * fattore
    return nuovo


def _riproduci(evento, preset, sync=False, fattore=1.0, semitoni=0.0):
    """
    Il motore dei suoni, l'unico punto che arriva alla scheda audio: le prove lo sostituiscono con
    un registratore, così la suite non suona mai. Prende il preset dalla collezione, lo sposta
    d'altezza se serve, lo sintetizza, ne moltiplica i campioni per il volume e lo manda al mixer di
    Acusticator, che se la somma supera il fondo scala la abbassa invece di tagliarla.
    """
    import numpy as np
    from GBUtils import Acusticator

    score, kind, adsr = Acusticator.preset(preset)
    if not score:
        return False
    if semitoni and kind in (1, 2, 3, 4):
        score = trasposto(score, semitoni)
    buffer = Acusticator.sintetizza(score, kind, adsr)
    if buffer is None:
        return False
    if fattore != 1:
        buffer = (np.asarray(buffer, dtype=np.float32) * float(fattore)).astype(np.float32)
    _FINE_DELL_ULTIMO[0] = time.monotonic() + sum(float(durata) for durata in score[1::4])
    return Acusticator.riproduci(buffer, sync=sync)


def evento_avanzamento(rapporto, salvato=True, ha_polisportive=False):
    """
    Il suono di un avanzamento del mondo e il testo della quarta riga della barra di stato, scelti
    insieme perché non dicano cose diverse: al massimo un suono per avanzamento, quello della notizia
    più importante. Prima il salvataggio che non riesce, poi le notizie delle tue polisportive, nello
    stesso ordine della barra: tesserati andati via, tornati liberi a fine contratto, stipendi non
    pagati, giocatori venduti, tesserati usciti di scena, infortunati in seduta, ritirati, contratti
    in scadenza o tesserati diventati bandiere; poi il primo del mese, se hai una polisportiva. Un
    avanzamento di più giorni ha il suo suono, che copre le notizie del mondo: dopo un'assenza ce ne
    sono quasi sempre, e le racconta il riepilogo. Per il giorno singolo le notizie del mondo, dalla
    più pesante, e infine il giorno qualunque. Restituisce la coppia (evento, testo), o (None, None)
    se il mondo non è avanzato.
    """
    if not rapporto or not rapporto["ticks"]:
        return None, None
    giorni = rapporto["giorni"]
    di_giorni = "di un giorno" if giorni == 1 else f"di {giorni} giorni"
    if not salvato:
        testo = f"mondo avanzato {di_giorni}, non salvato"
        # Dopo un'assenza di mesi il testo supererebbe i quaranta caratteri della barra.
        return "salvataggio_non_riuscito", testo if len(testo) <= 40 else f"avanzato {di_giorni}, non salvato"
    tuoi = (
        ("tuoi_partiti", "tuoi_tesserati_partiti", lambda n: f"{conta(n, 'tesserato andato via', 'tesserati andati via')}, non pagati"),
        ("tuoi_scaduti", "tuoi_contratti_scaduti", lambda n: conta(n, "tesserato libero a fine contratto", "tesserati liberi a fine contratto")),
        ("tuoi_non_pagati", "stipendi_non_pagati", lambda _n: "stipendi non pagati, vedi il bilancio"),
        ("tuoi_venduti", "tuo_tesserato_venduto", lambda n: conta(n, "tuo giocatore venduto", "tuoi giocatori venduti")),
        ("tuoi_usciti", "tuo_tesserato_uscito_di_scena", lambda n: conta(n, "tuo tesserato uscito di scena", "tuoi tesserati usciti di scena")),
        ("tuoi_infortunati_in_seduta", "tuo_tesserato_infortunato_in_seduta",
         lambda n: "tuo tesserato infortunato in seduta" if n == 1 else f"{n} tuoi tesserati infortunati in seduta"),
        ("tuoi_ritirati", "tuo_tesserato_ritirato", lambda n: conta(n, "tuo tesserato ritirato", "tuoi tesserati ritirati")),
        ("tuoi_in_scadenza", "tuoi_contratti_in_scadenza", lambda n: "1 contratto in scadenza, rinnovalo" if n == 1 else f"{n} contratti in scadenza, rinnovali"),
        ("tue_bandiere", "tuo_tesserato_bandiera", lambda n: conta(n, "tuo tesserato diventa bandiera", "tuoi tesserati diventano bandiere")),
    )
    for chiave, evento, testo in tuoi:
        if rapporto.get(chiave):
            return evento, testo(rapporto[chiave])
    if ha_polisportive and rapporto.get("mesi"):
        return "primo_del_mese", "primo del mese, stipendi pagati"
    if giorni > 1:
        return "mondo_avanzato_piu_giorni", f"mondo avanzato {di_giorni}"
    notizie = (
        ("morti", "notizia_morte", "morto", "morti"),
        ("poli_chiuse", "polisportiva_cpu_chiusa", "polisportiva chiusa", "polisportive chiuse"),
        ("usciti", "notizia_uscita_prematura", "uscito di scena", "usciti di scena"),
        ("ritirati", "notizia_ritiro", "ritirato", "ritirati"),
        ("poli_create", "polisportiva_cpu_nata", "nuova polisportiva", "nuove polisportive"),
    )
    for chiave, evento, singolare, plurale in notizie:
        if rapporto.get(chiave):
            return evento, f"mondo avanzato, {conta(rapporto[chiave], singolare, plurale)}"
    return "mondo_avanzato", f"mondo avanzato {di_giorni}"
