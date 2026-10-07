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
I suoni della partita non stanno qui: arriveranno con la tappa 10, secondo la decisione D11.
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
        "effetti_sonori_applicati": "conferma",
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
)
EVENTI = {evento: preset for _titolo, gruppo in GRUPPI for evento, preset in gruppo.items()}

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


def suona(evento, sync=False, volume=None, semitoni=0.0):
    """
    Suona il preset dell'evento al volume degli effetti, o a quello dato. A volume zero non parte
    niente. sync è quello di Acusticator: falso non aspetta, un numero aspetta al massimo quei
    secondi. semitoni sposta l'altezza, anche di frazioni. Vero se il suono è partito. Un evento
    sconosciuto, un preset che manca o una scheda audio che non risponde non fermano il programma.
    """
    volume = volume_effetti() if volume is None else volume
    if volume <= 0:
        return False
    preset = EVENTI.get(evento)
    if preset is None:
        print(f"MESS: evento sonoro sconosciuto, {evento}", file=sys.stderr)
        return False
    try:
        return _riproduci(evento, preset, sync, volume / VOLUME_DI_PROGETTO, semitoni)
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
    stesso ordine della barra: tesserati andati via, stipendi non pagati, giocatori venduti, tesserati
    usciti di scena, ritirati o diventati bandiere; poi il primo del mese, se hai una polisportiva. Un
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
        ("tuoi_non_pagati", "stipendi_non_pagati", lambda _n: "stipendi non pagati, vedi il bilancio"),
        ("tuoi_venduti", "tuo_tesserato_venduto", lambda n: conta(n, "tuo giocatore venduto", "tuoi giocatori venduti")),
        ("tuoi_usciti", "tuo_tesserato_uscito_di_scena", lambda n: conta(n, "tuo tesserato uscito di scena", "tuoi tesserati usciti di scena")),
        ("tuoi_ritirati", "tuo_tesserato_ritirato", lambda n: conta(n, "tuo tesserato ritirato", "tuoi tesserati ritirati")),
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
