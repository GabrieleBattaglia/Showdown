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
Con la tappa 12, il 2026-10-14, decisione D32 e punto 12.9 del progetto, il mondo gioca: arrivano i
gruppi del calendario e delle iscrizioni, del pannello dei tornei con l'albo e la classifica mondiale,
degli editor dei modelli e delle formule, delle sfide, e delle notizie dei tornei e delle sfide, più la
casella dell'iscrizione automatica nella sala allenamento. Sono sessantanove suoni nuovi, tutti mess_,
entrati nella collezione con la V205, ciascuno per un evento solo: le medaglie e le coppe hanno un
metallo a testa, e gli esiti opposti si distinguono a orecchio. Quando il mondo avanza, la notizia più
importante sceglie ancora il suono e la riga della barra, nell'ordine del punto 12.8. Le parti della
tappa 12 sono di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Con la tappa 13, il 2026-10-21, decisione D33 e punto 4.6 del progetto, arriva il gruppo dello staff:
il dialogo dello staff, il mercato degli allenatori, le offerte, i rinnovi, il licenziamento, le schede
e i filtri, e le notizie dello staff, ventitré suoni nuovi, tutti mess_, entrati nella collezione con la V215; con la
revisione del 22 ottobre 2026 il ventiquattresimo, l'allenatore in prelazione per un altro club, nella V219. Le parti della
tappa 13 sono di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
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
        # Gli annunci della cronaca, 1.79.0: il din don degli annunci di una stazione, e lo stesso rovesciato quando si salvano.
        "dialogo_annunci_cronaca": "mess_annunci_della_cronaca",
        "annunci_cronaca_salvati": "mess_annunci_salvati",
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
        # Dalla tappa 12, la casella dell'iscrizione automatica ai tornei: un timbro che si accende e il suo specchio.
        "iscrizione_automatica_accesa": "mess_iscrizione_automatica_accesa",
        "iscrizione_automatica_spenta": "mess_iscrizione_automatica_spenta",
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
    # La tappa 13, lo staff, progetto 4.6: un preset nuovo per evento, tutti mess_. Il tic della probabilità
    # del rinnovo e dell'ingaggio, e i perché di un rinnovo che non si può proporre, sono quelli dei tesserati.
    ("Staff, gli allenatori", {
        "dialogo_staff": "mess_staff_aperto",
        "dialogo_mercato_allenatori": "mess_mercato_allenatori",
        "dialogo_cifra_ingaggio_allenatore": "mess_cifra_ingaggio_allenatore",
        # Il fischietto che chiama in campo e il suo gemello che si spegne; il fischio finale del licenziamento.
        "allenatore_assunto": "mess_allenatore_assunto",
        "allenatore_rifiuta": "mess_allenatore_rifiuta",
        "allenatore_licenziato": "mess_allenatore_licenziato",
        "staff_rinnovo_concordato": "mess_staff_rinnovo_concordato",
        "staff_rinnovo_rifiutato": "mess_staff_rinnovo_rifiutato",
        "staff_rinnovo_chiuso": "mess_staff_rinnovo_chiuso",
        "staff_posto_occupato": "mess_staff_posto_occupato",
        # Dalla revisione del 22 ottobre 2026: l'allenatore in prelazione per un'altra tua polisportiva.
        "allenatore_in_prelazione": "mess_allenatore_in_prelazione",
        "scheda_allenatore": "mess_scheda_allenatore",
        "diario_allenatore": "mess_diario_allenatore",
        # Scattano a ogni freccia sui campi del mercato: tocchi minimi; l'età quando ci si ferma.
        "staff_posto_scelto": "mess_staff_posto_scelto",
        "filtro_classe_allenatori": "mess_filtro_classe_allenatori",
        "filtro_eta_allenatori": "mess_filtro_eta_allenatori",
        "filtro_tipo_allenatori": "mess_filtro_tipo_allenatori",
        "filtro_sesso_allenatori": "mess_filtro_sesso_allenatori",
    }),
    ("Staff, le notizie", {
        "tuo_staff_partito": "mess_staff_partito",
        "tuo_staff_scaduto": "mess_staff_scaduto",
        "tuo_staff_uscito": "mess_staff_uscito",
        "tua_prelazione": "mess_prelazione",
        "tuo_staff_in_scadenza": "mess_staff_in_scadenza",
        # All'apertura col mondo aggiornato al formato 8: lo staff nasce, e il mercato degli allenatori è aperto.
        "staff_appena_nato": "mess_staff_appena_nato",
    }),
    # La tappa 12, il mondo che gioca, punto 12.9 del progetto: un preset nuovo per evento, tutti mess_.
    ("Tornei, il calendario e le iscrizioni", {
        "dialogo_calendario_tornei": "mess_calendario_tornei",
        "dialogo_iscrizioni_tornei": "mess_iscrizioni_tornei",
        # Il gettone che entra e quello che torna: l'iscrizione pagata e quella tolta col rimborso.
        "iscrizione_fatta": "mess_iscrizione_fatta",
        "iscrizione_tolta": "mess_iscrizione_tolta",
        # I tre rifiuti, ciascuno col suo perché: la cassa, i giorni già presi, il torneo per altri.
        "iscrizione_cassa_insufficiente": "mess_iscrizione_senza_quota",
        "iscrizione_sovrapposta": "mess_iscrizione_sovrapposta",
        "iscrizione_non_idoneo": "mess_iscrizione_non_idoneo",
    }),
    ("Tornei, il pannello e le classifiche", {
        "dialogo_tornei_in_corso": "mess_tornei_in_corso",
        "differita_al_via": "mess_differita_al_via",
        # Esc prima della fine dell'ascolto in differita, D30: un suono suo, che non svela il risultato e
        # non è quello di ogni Annulla; nasce con la revisione del 14 ottobre 2026.
        "differita_interrotta": "mess_differita_interrotta",
        "cronaca_torneo_letta": "mess_cronaca_torneo",
        "risultato_svelato": "mess_risultato_svelato",
        "risultati_svelati_tutti": "mess_risultati_svelati_tutti",
        "nessun_risultato_da_svelare": "mess_niente_da_svelare",
        "nessuna_differita": "mess_nessuna_differita",
        "albo_d_oro": "mess_albo_d_oro",
        "classifica_mondiale": "mess_classifica_mondiale",
    }),
    ("Tornei, gli editor", {
        "dialogo_editor_modelli": "mess_editor_modelli",
        "dialogo_modello_torneo": "mess_modello_torneo",
        "modello_salvato": "mess_modello_salvato",
        "modello_duplicato": "mess_modello_duplicato",
        "modello_eliminato": "mess_modello_eliminato",
        "dialogo_editor_formule": "mess_editor_formule",
        "formula_nuova": "mess_formula_nuova",
        "formula_salvata": "mess_formula_salvata",
        "formula_non_valida": "mess_formula_non_valida",
        "formula_in_uso": "mess_formula_in_uso",
        "formula_eliminata": "mess_formula_eliminata",
        "dialogo_fase": "mess_fase_dialogo",
        "fase_aggiunta": "mess_fase_aggiunta",
        "fase_modificata": "mess_fase_modificata",
        "fase_tolta": "mess_fase_tolta",
        "calendario_ripristinato": "mess_calendario_ripristinato",
        # Suona all'avvio, a ogni avanzamento che lo trova e all'apertura dell'editor: è lo stesso evento.
        "calendario_illeggibile": "mess_calendario_illeggibile",
    }),
    ("Partite, le sfide", {
        "dialogo_lancia_sfida": "mess_lancia_sfida",
        "sfida_accettata_dall_avversario": "mess_sfida_raccolta",
        "sfida_rifiutata_dall_avversario": "mess_sfida_declinata",
        "nessuna_sfida_da_lanciare": "mess_nessuna_sfida_da_lanciare",
        "dialogo_sfide_in_arrivo": "mess_sfide_in_arrivo",
        "sfida_accettata": "mess_sfida_accettata",
        "sfida_rifiutata": "mess_sfida_rifiutata",
        "dialogo_formazione": "mess_formazione",
        "formazione_non_valida": "mess_formazione_non_valida",
        "storico_sfide": "mess_storico_sfide",
    }),
    ("Tornei e sfide, le notizie", {
        # Le medaglie e le coppe dei tuoi, dalla più preziosa: ogni metallo ha il suo suono.
        "tua_medaglia_oro": "mess_medaglia_oro",
        "tua_medaglia_argento": "mess_medaglia_argento",
        "tua_medaglia_bronzo": "mess_medaglia_bronzo",
        "tua_medaglia_legno": "mess_medaglia_legno",
        "tuo_titolo_mondiale": "mess_titolo_mondiale",
        "tua_coppa_oro": "mess_coppa_oro",
        "tua_coppa_argento": "mess_coppa_argento",
        "tua_coppa_bronzo": "mess_coppa_bronzo",
        "tua_coppa_legno": "mess_coppa_legno",
        "tua_sfida_vinta": "mess_sfida_vinta",
        "tua_sfida_persa": "mess_sfida_persa",
        "tua_sfida_a_tavolino": "mess_sfida_a_tavolino",
        "sfida_ricevuta": "mess_sfida_ricevuta",
        "sfida_decaduta": "mess_sfida_decaduta",
        "tuoi_qualificati_mondiale": "mess_qualificati_mondiale",
        "tua_qualificazione_coppa": "mess_qualificazione_coppa",
        "tue_iscrizioni_saltate": "mess_iscrizioni_saltate",
        "tuo_infortunio_in_gara": "mess_infortunio_in_gara",
        "tuo_acciacco": "mess_acciacco",
        "tuo_tavolino": "mess_tavolino",
        "tuo_torneo_concluso": "mess_torneo_concluso",
        "tue_iscrizioni_automatiche": "mess_iscrizioni_automatiche",
        "edizione_annullata": "mess_edizione_annullata",
        "mondiale_concluso": "mess_mondiale_concluso",
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
    "lavoro_concluso": "la chiusura del mercato, delle vendite, degli arretrati, della sala allenamento, dei contratti, dello staff, del mercato degli allenatori, del calendario o degli editor dopo averci lavorato",
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
    "dialogo_annunci_cronaca": "si apre il dialogo degli annunci della cronaca",
    "annunci_cronaca_salvati": "gli annunci della cronaca confermati e salvati",
    "dialogo_scheda_giocatore": "si apre la scelta del giocatore di cui leggere la scheda, con Ctrl+G",
    "scheda_giocatore": "la scheda di un giocatore",
    "dialogo_diario_giocatore": "si apre la scelta del giocatore di cui leggere il diario, con Ctrl+Shift+D",
    "diario_giocatore": "il diario di un giocatore",
    "elenco_giocatori": "l'elenco dei giocatori, con Ctrl+E",
    "classifica": "la classifica per valore, con Ctrl+L",
    "top_10": "la TOP 10 dei migliori giocatori, con Ctrl+T",
    "statistiche_mondo": "le statistiche nazionali, con Ctrl+I",
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
    "scheda_polisportiva": "la scheda della polisportiva attiva, con Ctrl+M, o di quella scelta nel lancio di una sfida",
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
    "mercato_scheda_giocatore": "nel mercato, nella sala allenamento, nei contratti e nel pannello dei tornei, la scheda del giocatore scelto",
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
    "nessun_incontro": "Salva la cronaca quando nella sessione non c'è ancora un incontro mostrato o ascoltato",
    "cronaca_salvata": "la cronaca dell'ultimo incontro, amichevole, di torneo o di sfida, salvata nel suo file, con Ctrl+Shift+O",
    "cronaca_non_salvata": "la cronaca dell'ultimo incontro che non si può scrivere nel file",
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
    "iscrizione_automatica_accesa": "nella sala allenamento si accende l'iscrizione automatica ai tornei del tesserato, con Alt+U",
    "iscrizione_automatica_spenta": "nella sala allenamento si spegne l'iscrizione automatica ai tornei del tesserato, con Alt+U",
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
    "dialogo_staff": "si apre il dialogo dello staff della polisportiva, con Ctrl+H",
    "dialogo_mercato_allenatori": "si apre il mercato degli allenatori, con Ctrl+Shift+G o con Assumi nel dialogo dello staff",
    "dialogo_cifra_ingaggio_allenatore": "si apre il dialogo della cifra d'ingaggio di un allenatore",
    "allenatore_assunto": "l'allenatore accetta l'ingaggio ed entra nello staff",
    "allenatore_rifiuta": "l'allenatore rifiuta l'ingaggio",
    "allenatore_licenziato": "l'allenatore licenziato lascia lo staff",
    "staff_rinnovo_concordato": "l'allenatore accetta il rinnovo del contratto",
    "staff_rinnovo_rifiutato": "l'allenatore rifiuta il rinnovo, e si può riprovare un altro giorno",
    "staff_rinnovo_chiuso": "il terzo rifiuto del rinnovo, e l'allenatore non tratta più",
    "staff_posto_occupato": "si vuole assumere per un posto dello staff già occupato",
    "allenatore_in_prelazione": "si vuole assumere un allenatore in prelazione per un'altra tua polisportiva",
    "scheda_allenatore": "si apre la scheda di un allenatore",
    "diario_allenatore": "si apre il diario di un allenatore",
    "staff_posto_scelto": "nel mercato degli allenatori cambia il posto da offrire",
    "filtro_classe_allenatori": "nel mercato degli allenatori cambia la classe minima",
    "filtro_eta_allenatori": "nel mercato degli allenatori cambia l'età massima, quando ci si ferma",
    "filtro_tipo_allenatori": "nel mercato degli allenatori cambia il tipo, ex giocatori o nati allenatori",
    "filtro_sesso_allenatori": "nel mercato degli allenatori cambia il sesso",
    "tuo_staff_partito": "nell'avanzamento un allenatore del tuo staff se ne va per lo stipendio non pagato",
    "tuo_staff_scaduto": "nell'avanzamento il contratto di un allenatore del tuo staff scade senza rinnovo, e lui torna libero",
    "tuo_staff_uscito": "nell'avanzamento un allenatore del tuo staff smette di allenare, muore o lascia il mondo dello showdown",
    "tua_prelazione": "nell'avanzamento un tuo tesserato si ritira e può allenare, e per qualche giorno puoi assumerlo prima degli altri",
    "tuo_staff_in_scadenza": "nell'avanzamento il contratto di un allenatore del tuo staff entra nella finestra del rinnovo, o all'ultimo mese",
    "staff_appena_nato": "all'apertura col mondo appena aggiornato, la notizia dello staff e del mercato degli allenatori aperto",
    "dialogo_calendario_tornei": "si apre il calendario dei tornei e delle iscrizioni, con Ctrl+U",
    "dialogo_iscrizioni_tornei": "si aprono le iscrizioni dei tuoi atleti alla prima edizione aperta, con Ctrl+J",
    "iscrizione_fatta": "nel calendario un tuo atleta iscritto a un torneo con la quota pagata, o la rosa della tua polisportiva per la coppa",
    "iscrizione_tolta": "nel calendario l'iscrizione di un tuo atleta tolta, con la quota rimborsata",
    "iscrizione_cassa_insufficiente": "nel calendario la cassa della polisportiva non basta per la quota d'iscrizione",
    "iscrizione_sovrapposta": "nel calendario l'atleta negli stessi giorni ha già un altro torneo o un'altra sfida",
    "iscrizione_non_idoneo": "nel calendario l'atleta non può giocare quel torneo, per sesso, classe, età o qualificazione",
    "dialogo_tornei_in_corso": "si apre il pannello dei tornei in corso e conclusi di recente, con Ctrl+Y",
    "differita_al_via": "si apre la finestra dal vivo per ascoltare in differita un incontro dei tuoi, di torneo o di sfida",
    "differita_interrotta": "nell'ascolto in differita Esc prima della fine, e l'incontro resta da ascoltare senza svelare il risultato",
    "cronaca_torneo_letta": "la cronaca di un incontro dei tuoi, di torneo o di sfida, aperta da leggere",
    "risultato_svelato": "il risultato di un incontro dei tuoi che si mostra, dopo l'ascolto in differita o con Mostra il risultato",
    "risultati_svelati_tutti": "Mostra tutti i risultati svela in un colpo gli incontri dei tuoi ancora da ascoltare",
    "nessun_risultato_da_svelare": "Mostra tutti i risultati quando non c'è nessun incontro dei tuoi da svelare",
    "nessuna_differita": "un incontro che non si può ascoltare né leggere: non è dei tuoi, o la sua edizione è già stata sostituita",
    "albo_d_oro": "si apre l'albo d'oro dei tornei, con Ctrl+Shift+B",
    "classifica_mondiale": "la classifica nazionale per sempre, uomini e donne, con Ctrl+Shift+W",
    "dialogo_editor_modelli": "si apre l'editor dei modelli di torneo, con Ctrl+Shift+J",
    "dialogo_modello_torneo": "nell'editor si apre il dialogo di un modello di torneo, nuovo o da modificare",
    "modello_salvato": "un modello di torneo salvato",
    "modello_duplicato": "un modello di torneo duplicato, con un identificativo nuovo",
    "modello_eliminato": "un modello di torneo eliminato",
    "dialogo_editor_formule": "si apre l'editor delle formule dei tornei, con Ctrl+Shift+Y",
    "formula_nuova": "nell'editor delle formule nasce una formula nuova, ancora da salvare",
    "formula_salvata": "una formula valida salvata nel file delle formule",
    "formula_non_valida": "una formula che non si può salvare, con il motivo",
    "formula_in_uso": "si vuole eliminare una formula che dei modelli usano ancora",
    "formula_eliminata": "una formula eliminata dal file delle formule",
    "dialogo_fase": "nell'editor delle formule si apre il dialogo di una fase, nuova o da modificare",
    "fase_aggiunta": "nell'editor delle formule una fase aggiunta in fondo",
    "fase_modificata": "nell'editor delle formule una fase cambiata, con quelle che seguono aggiornate",
    "fase_tolta": "nell'editor delle formule una fase tolta",
    "calendario_ripristinato": "il calendario predefinito rimesso, con quello di prima messo da parte",
    "calendario_illeggibile": "un modello o una formula dei tornei che non si leggono, all'avvio, nell'avanzamento o all'apertura dell'editor",
    "dialogo_lancia_sfida": "si apre il lancio di una sfida a una polisportiva del computer, con Ctrl+W",
    "sfida_accettata_dall_avversario": "la polisportiva del computer accetta la tua sfida, che si gioca domani",
    "sfida_rifiutata_dall_avversario": "la polisportiva del computer rifiuta la tua sfida, e dice perché",
    "nessuna_sfida_da_lanciare": "la tua polisportiva non ha più sfide da lanciare questo mese",
    "dialogo_sfide_in_arrivo": "si aprono le sfide in arrivo, a cui rispondere entro oggi, prima dell'avanzamento seguente, con Ctrl+Shift+F",
    "sfida_accettata": "accetti una sfida in arrivo, con la tua formazione",
    "sfida_rifiutata": "rifiuti una sfida in arrivo",
    "dialogo_formazione": "si apre la formazione per una sfida o la rosa per la coppa, con titolari e riserve",
    "formazione_non_valida": "una formazione che non va, con il motivo: il due più uno, un doppione o un impegno",
    "storico_sfide": "si apre lo storico delle sfide delle tue polisportive, con Ctrl+Shift+H",
    "tua_medaglia_oro": "nell'avanzamento un tuo atleta vince la medaglia d'oro in un torneo",
    "tua_medaglia_argento": "nell'avanzamento un tuo atleta vince la medaglia d'argento",
    "tua_medaglia_bronzo": "nell'avanzamento un tuo atleta vince la medaglia di bronzo",
    "tua_medaglia_legno": "nell'avanzamento un tuo atleta arriva quarto, la medaglia di legno",
    "tuo_titolo_mondiale": "nell'avanzamento un tuo atleta vince il campionato italiano e diventa campione o campionessa d'Italia",
    "tua_coppa_oro": "nell'avanzamento la tua polisportiva vince la coppa d'oro della Coppa delle polisportive",
    "tua_coppa_argento": "nell'avanzamento la tua polisportiva prende la coppa d'argento della Coppa delle polisportive",
    "tua_coppa_bronzo": "nell'avanzamento la tua polisportiva prende la coppa di bronzo della Coppa delle polisportive",
    "tua_coppa_legno": "nell'avanzamento la tua polisportiva arriva quarta alla Coppa delle polisportive, la coppa di legno",
    "tua_sfida_vinta": "nell'avanzamento la tua polisportiva vince una sfida",
    "tua_sfida_persa": "nell'avanzamento la tua polisportiva perde una sfida",
    "tua_sfida_a_tavolino": "nell'avanzamento la tua polisportiva perde una sfida a tavolino, senza una squadra valida",
    "sfida_ricevuta": "nell'avanzamento una polisportiva del computer sfida la tua, e aspetta la risposta entro oggi",
    "sfida_decaduta": "nell'avanzamento una sfida alla tua polisportiva decade, senza risposta",
    "tuoi_qualificati_mondiale": "nell'avanzamento tuoi atleti convocati al campionato italiano",
    "tua_qualificazione_coppa": "nell'avanzamento la tua polisportiva qualificata alla Coppa delle polisportive",
    "tue_iscrizioni_saltate": "nell'avanzamento l'iscrizione automatica di un tuo atleta salta, perché la cassa non ha la quota",
    "tuo_infortunio_in_gara": "nell'avanzamento un tuo atleta si fa male in gara e si ferma, anche col ritiro",
    "tuo_acciacco": "nell'avanzamento un tuo atleta esce da una gara con un acciacco, e per qualche giorno rende un poco meno",
    "tuo_tavolino": "nell'avanzamento un tuo atleta perde a tavolino, perché non si presenta",
    "tuo_torneo_concluso": "nell'avanzamento finisce un torneo dei tuoi, senza medaglie",
    "tue_iscrizioni_automatiche": "nell'avanzamento l'iscrizione automatica iscrive tuoi atleti a un torneo",
    "edizione_annullata": "nell'avanzamento un torneo con tuoi iscritti si annulla per pochi iscritti, e la quota torna",
    "mondiale_concluso": "nell'avanzamento finisce un campionato italiano",
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


def in_coda(evento, pausa=PAUSA_IN_CODA, **opzioni):
    """
    Suona l'evento quando è finito il suono in corso, più una breve pausa, così due suoni non si
    sovrappongono; se non suona niente, subito. Non blocca: l'attesa la fa un timer di wx. Una pausa
    più lunga stacca un suono che deve farsi notare, come la notizia dello staff all'apertura.
    """
    resta = attesa()
    if resta <= 0:
        return suona(evento, **opzioni)
    import wx

    wx.CallLater(int((resta + pausa) * 1000), suona, evento, **opzioni)
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


def evento_avanzamento(rapporto, salvato=True, ha_polisportive=False, sfidante=None):
    """
    Il suono di un avanzamento del mondo e il testo della quarta riga della barra di stato, scelti
    insieme perché non dicano cose diverse: al massimo un suono per avanzamento, quello della notizia
    più importante. Prima il salvataggio che non riesce; poi i tesserati andati via, quelli tornati
    liberi a fine contratto e gli stipendi non pagati, e dalla tappa 13 gli allenatori del tuo staff
    andati via, tornati liberi o usciti; dalla tappa 12, punto 12.8 del progetto, il
    calendario dei tornei con problemi, la sfida che aspetta la tua risposta, con il nome di chi sfida
    se ci sta, sfidante, il titolo mondiale, le medaglie e le coppe dalla più preziosa, prima le
    medaglie e poi le coppe a pari metallo, le sfide vinte, perse e perse a tavolino, le convocazioni
    al mondiale e alla coppa, le iscrizioni saltate per la cassa; poi le altre notizie dei tuoi,
    venduti, usciti di scena, infortunati in seduta, infortunati e a tavolino in gara, la prelazione
    su un tuo ritirato, i ritirati, i contratti in scadenza, quelli dello staff e le bandiere; poi gli
    acciacchi in gara, il torneo finito senza medaglie, le
    iscrizioni automatiche, la sfida decaduta e il torneo annullato; poi il primo del mese, se hai una
    polisportiva. Un avanzamento di più giorni ha il suo suono, che copre le notizie del mondo: dopo
    un'assenza ce ne sono quasi sempre, e le racconta il riepilogo. Per il giorno singolo le notizie del
    mondo, dal mondiale concluso alla più leggera, e infine il giorno qualunque. Restituisce la coppia
    (evento, testo), o (None, None) se il mondo non è avanzato; il testo sta nei quaranta caratteri.
    """
    if not rapporto or not rapporto["ticks"]:
        return None, None
    giorni = rapporto["giorni"]
    di_giorni = "di un giorno" if giorni == 1 else f"di {giorni} giorni"
    if not salvato:
        testo = f"mondo avanzato {di_giorni}, non salvato"
        # Dopo un'assenza di mesi il testo supererebbe i quaranta caratteri della barra.
        return "salvataggio_non_riuscito", testo if len(testo) <= 40 else f"avanzato {di_giorni}, non salvato"

    def sfida_in_attesa(n):
        if n == 1:
            testo = f"sfida da {sfidante}, rispondi oggi" if sfidante else ""
            return testo if testo and len(testo) <= 40 else "sfida ricevuta, rispondi oggi"
        return f"{n} sfide da rispondere oggi"

    def coppa(colore):
        return lambda n: f"coppa {colore} per la tua polisportiva" if n == 1 else f"{n} coppe {colore} alle tue"

    def campioni(n):
        # La revisione della tappa 14: al femminile se i titoli sono tutti di donne, al maschile se ci sono uomini.
        donne = rapporto.get("tue_campionesse", 0) == n
        if n == 1:
            return "tua atleta campionessa d'Italia" if donne else "tuo atleta campione d'Italia"
        return f"{n} tue atlete campionesse d'Italia" if donne else f"{n} tuoi atleti campioni d'Italia"

    tuoi = (
        ("tuoi_partiti", "tuoi_tesserati_partiti", lambda n: f"{conta(n, 'tesserato andato via', 'tesserati andati via')}, non pagati"),
        ("tuoi_scaduti", "tuoi_contratti_scaduti", lambda n: conta(n, "tesserato libero a fine contratto", "tesserati liberi a fine contratto")),
        ("tuoi_non_pagati", "stipendi_non_pagati", lambda _n: "stipendi non pagati, vedi il bilancio"),
        # Dalla tappa 13 lo staff: chi se ne va, chi torna libero e chi esce dallo staff, subito dopo i tesserati.
        ("tuo_staff_partito", "tuo_staff_partito", lambda n: "allenatore andato via, non pagato" if n == 1 else f"{n} allenatori andati via, non pagati"),
        ("tuo_staff_scaduto", "tuo_staff_scaduto", lambda n: conta(n, "allenatore libero a fine contratto", "allenatori liberi a fine contratto")),
        ("tuo_staff_uscito", "tuo_staff_uscito", lambda n: conta(n, "allenatore uscito dal tuo staff", "allenatori usciti dal tuo staff")),
        ("calendario_con_problemi", "calendario_illeggibile", lambda _n: "calendario dei tornei con problemi"),
        ("sfide_in_attesa", "sfida_ricevuta", sfida_in_attesa),
        ("tuoi_titoli_mondiali", "tuo_titolo_mondiale", campioni),
        ("tue_medaglie_oro", "tua_medaglia_oro", lambda n: conta(n, "medaglia d'oro per i tuoi", "medaglie d'oro per i tuoi")),
        ("tue_coppe_oro", "tua_coppa_oro", coppa("d'oro")),
        # A pari metallo prima la medaglia e poi la coppa, come per l'oro: la revisione del 14 ottobre 2026
        # ha visto che prima un legno di un open passava davanti a un argento della Coppa delle polisportive.
        ("tue_medaglie_argento", "tua_medaglia_argento", lambda n: conta(n, "medaglia d'argento per i tuoi", "medaglie d'argento per i tuoi")),
        ("tue_coppe_argento", "tua_coppa_argento", coppa("d'argento")),
        ("tue_medaglie_bronzo", "tua_medaglia_bronzo", lambda n: conta(n, "medaglia di bronzo per i tuoi", "medaglie di bronzo per i tuoi")),
        ("tue_coppe_bronzo", "tua_coppa_bronzo", coppa("di bronzo")),
        ("tue_medaglie_legno", "tua_medaglia_legno", lambda n: conta(n, "medaglia di legno per i tuoi", "medaglie di legno per i tuoi")),
        ("tue_coppe_legno", "tua_coppa_legno", coppa("di legno")),
        ("tue_sfide_vinte", "tua_sfida_vinta", lambda n: conta(n, "sfida vinta", "sfide vinte")),
        ("tue_sfide_perse", "tua_sfida_persa", lambda n: conta(n, "sfida persa", "sfide perse")),
        ("tue_sfide_a_tavolino", "tua_sfida_a_tavolino", lambda n: conta(n, "sfida persa a tavolino", "sfide perse a tavolino")),
        ("tuoi_qualificati", "tuoi_qualificati_mondiale", lambda n: conta(n, "tuo atleta al campionato italiano", "tuoi atleti al campionato italiano")),
        ("tue_qualificazioni_coppa", "tua_qualificazione_coppa",
         lambda n: "tua polisportiva qualificata alla coppa" if n == 1 else f"{n} tue polisportive alla coppa"),
        ("tue_iscrizioni_saltate", "tue_iscrizioni_saltate", lambda n: conta(n, "iscrizione saltata per la cassa", "iscrizioni saltate per la cassa")),
        ("tuoi_venduti", "tuo_tesserato_venduto", lambda n: conta(n, "tuo giocatore venduto", "tuoi giocatori venduti")),
        ("tuoi_usciti", "tuo_tesserato_uscito_di_scena", lambda n: conta(n, "tuo tesserato uscito di scena", "tuoi tesserati usciti di scena")),
        ("tuoi_infortunati_in_seduta", "tuo_tesserato_infortunato_in_seduta",
         lambda n: "tuo tesserato infortunato in seduta" if n == 1 else f"{n} tuoi tesserati infortunati in seduta"),
        ("tuoi_infortuni_in_gara", "tuo_infortunio_in_gara", lambda n: conta(n, "tuo atleta infortunato in gara", "tuoi atleti infortunati in gara")),
        ("tuoi_tavolini", "tuo_tavolino", lambda n: conta(n, "tuo atleta perde a tavolino", "tuoi atleti perdono a tavolino")),
        # La prelazione su un tuo ritirato viene prima del ritiro, che racconta: è l'occasione da cogliere.
        ("tue_prelazioni", "tua_prelazione", lambda n: "tuo ritirato può allenare, prelazione" if n == 1 else f"{n} tuoi ritirati possono allenare"),
        ("tuoi_ritirati", "tuo_tesserato_ritirato", lambda n: conta(n, "tuo tesserato ritirato", "tuoi tesserati ritirati")),
        ("tuoi_in_scadenza", "tuoi_contratti_in_scadenza", lambda n: "1 contratto in scadenza, rinnovalo" if n == 1 else f"{n} contratti in scadenza, rinnovali"),
        ("tuo_staff_in_scadenza", "tuo_staff_in_scadenza", lambda n: conta(n, "contratto di staff in scadenza", "contratti di staff in scadenza")),
        ("tue_bandiere", "tuo_tesserato_bandiera", lambda n: conta(n, "tuo tesserato diventa bandiera", "tuoi tesserati diventano bandiere")),
        ("tuoi_acciacchi", "tuo_acciacco", lambda n: conta(n, "tuo atleta acciaccato in gara", "tuoi atleti acciaccati in gara")),
        ("tuoi_tornei_conclusi", "tuo_torneo_concluso", lambda n: conta(n, "torneo dei tuoi concluso", "tornei dei tuoi conclusi")),
        ("tue_iscrizioni", "tue_iscrizioni_automatiche", lambda n: conta(n, "iscrizione automatica dei tuoi", "iscrizioni automatiche dei tuoi")),
        ("sfide_decadute", "sfida_decaduta", lambda n: conta(n, "sfida decaduta senza risposta", "sfide decadute senza risposta")),
        ("tue_edizioni_annullate", "edizione_annullata", lambda n: conta(n, "torneo dei tuoi annullato", "tornei dei tuoi annullati")),
    )
    for chiave, evento, testo in tuoi:
        if rapporto.get(chiave):
            return evento, testo(rapporto[chiave])
    if ha_polisportive and rapporto.get("mesi"):
        return "primo_del_mese", "primo del mese, stipendi pagati"
    if giorni > 1:
        return "mondo_avanzato_piu_giorni", f"mondo avanzato {di_giorni}"
    if rapporto.get("mondiali_conclusi"):
        n = rapporto["mondiali_conclusi"]
        return "mondiale_concluso", "campionato italiano concluso" if n == 1 else f"{n} campionati italiani conclusi"
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
