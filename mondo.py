"""
Il mondo di MESS: giocatori, polisportive e il tempo che scorre.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 2 del piano, dallo smontaggio della classe Simulatore di sd.py:
qui resta tutto ciò che il mondo fa da solo, cioè l'avanzamento del tempo con invecchiamento,
guarigioni, ritiri, morti e nascite, l'autoallenamento e la vita delle polisportive del computer.
Dalla tappa 6, secondo la decisione D2, il tempo scorre come in Hattrick: un giorno simulato ogni
8 ore reali, anche a programma chiuso. Il tempo trascorso si misura in UTC, che l'ora legale non
sposta. Ogni giorno trascorso ha la sua elaborazione completa, nello stesso ordine, e l'ancora
dell'ultimo avanzamento si sposta di otto ore esatte per ogni giorno elaborato: il resto non va
più perso. Le nascite seguono la natura, come ha deciso Gabriele: da uno a sette giocatori nuovi
ogni giorno, senza più il tetto di cinquanta per avvio, che faceva nascere meno giocatori a chi
apriva il gioco di rado; l'equilibrio arriva quando le morti compensano le nascite. Gli eventi
finiscono nei diari di chi li vive, e chi esce di scena nel registro delle vecchie glorie.
Dalla tappa 7 ogni polisportiva ha un nome solo, che è anche la sua chiave nel mondo, e chi si
ritira o muore lascia libero il suo posto. Le polisportive del computer seguono la decisione D19:
provano ogni candidato una volta sola al giorno, le prime a scegliere sono quelle con più gloria,
e a rosa piena ogni tanto provano un libero più forte, che se accetta prende il posto del
tesserato che vale meno. La vetrina dei liberi trova in fretta il primo alla portata di ciascuna,
così le mosse reggono anche un mondo di decine di migliaia di giocatori. Qui stanno anche le
operazioni della polisportiva dell'utente: fondazione, offerta, svincolo e chiusura.
Dalla tappa 8 il mondo fa i conti, secondo la decisione D22: il primo di ogni mese ogni
polisportiva incassa lo sponsor e paga gli stipendi; chi non viene pagato aspetta, perde
pazienza e alla fine se ne va, salvo le bandiere; le offerte sono premi d'ingaggio; i tesserati
si mettono in vendita e si comprano. Il computer tessera e compra solo chi può pagare, a rosa
piena scambia solo se ci sta nei conti, e quando non paga vende il suo giocatore più caro.
Dalla tappa 9, il 2026-10-07, un infortunio ha una sede, e la guarigione la toglie insieme
all'infortunio.
Il mondo non stampa: consegna i suoi messaggi alla funzione notifica, che gli passa chi lo usa.
Dal 2026-10-07 il riepilogo di un avanzamento conta anche i primi del mese e, delle polisportive
dell'utente, i tesserati ritirati, quelli usciti di scena e le bandiere nuove: la finestra ne fa
sentire il suono, secondo la decisione D24.
Dalla tappa 11, il 2026-10-09, il mondo si allena, decisione D31: ogni giorno simulato, anche a
programma chiuso, ogni giocatore in attività che può giocare fa la sua seduta, che dà punti
allenamento al tesserato secondo l'intensità e al libero la metà; l'esperienza cresce un poco con
l'età e di più in polisportiva, col fattore del gruppo; la costanza recente segue l'attività del
giorno; chi si allena all'intensa può infortunarsi in seduta. I liberi e i tesserati del computer
spendono da soli, secondo la loro indole, quando il portafoglio arriva alla soglia; i tesserati
dell'utente aspettano lui. Il primo del mese i livelli alti calano un poco, e l'apprendista rapido
dimentica. Prima l'esperienza cresceva soltanto il primo del mese, un decimo per chi era in un club.
Sempre dalla tappa 11 ci sono i contratti, al posto della regola d'abbandono del vecchio P8: ogni
ingresso in una polisportiva firma un contratto, e lo stipendio che si paga è quello del contratto,
fisso fino alla scadenza; lo sponsor cresce col valore della rosa. Il primo del mese, dopo gli
stipendi, i contratti scaduti finiscono: con un rinnovo concordato parte quello nuovo, altrimenti
il giocatore torna libero e nessuno incassa niente. Il computer prova a rinnovare chi è negli ultimi
tre mesi, se se lo può permettere, una volta al mese e al massimo tre volte, e altrimenti lo mette in
vendita e lo lascia scadere; l'utente rinnova a trattativa, una proposta al giorno e al massimo tre,
e il mondo gli ricorda i contratti che entrano nella finestra e quelli all'ultimo mese. Lo svincolo
a contratto in corso costa una buonuscita, metà degli stipendi che restano, anche al computer.
E il computer non tessera i liberi infortunati finché non guariscono, decisione 21 di Gabriele;
l'utente invece può tesserarli subito.
Dalla tappa 12, il 2026-10-13, con la issue 1 e D32: il computer fonda polisportive contando soltanto
i giocatori in attività e soltanto le sue polisportive, e i giocatori nuovi sono da due a nove al
giorno, idea di Gabriele, così al mercato restano sempre dei liberi da cercare e tesserare.
"""

import bisect
import calendar
import datetime
import math
import random

import calendario
import classe as modulo_classe
import contratti
import esperienza
import infortuni
import palmares
import percorsi
import sfide
import staff as modulo_staff
import tratti
from allenamento import allena_secondo_programma, mantenimento_del_mese
from costanti import (
    ANNO_SIMULAZIONE_GIORNI,
    BILANCI_CONSERVATI,
    COSTANZA_LIBERI,
    CREA_NUOVI_PER_TICK_RANGE,
    DECADIMENTO_COSTANZA,
    ETA_CLASSE_MIGLIORE_GIORNI,
    ETA_MINIMA_CHIUSURA_CPU_ANNI,
    FATTORE_PROB_GLORIA,
    FATTORE_PROB_TESSERATI,
    FEDELTA_BANDIERA,
    FEDELTA_MASSIMA,
    FEDELTA_PER_MESE,
    GIOCATORI_ATTIVI_PER_POLI_CPU_TARGET,
    GIORNI_PRELAZIONE,
    IMPORTANZA_MASSIMA,
    INTENSITA,
    INTENSITA_PREDEFINITA,
    LIMITE_MOVIMENTI_PER_TICK,
    MARGINE_CAMBIO_STAFF_CPU,
    MAX_PROB_CHIUSURA_GIORNALIERA,
    MESI_CONTRATTO_MAX,
    MESI_CONTRATTO_MIN,
    MESI_DI_INGAGGIO,
    MESI_DI_RISERVA_CPU,
    MESI_FINESTRA_RINNOVO,
    MINUTI_RISERVA_UTENTE,
    NOME_FILE_LOG_USCITE,
    NOME_POLISPORTIVA_MAX,
    NOME_POLISPORTIVA_MIN,
    PA_SEDUTA,
    PROB_CHIUSURA_BASE_GIORNALIERA,
    PROB_CREAZIONE_POLI_CPU_PER_TICK,
    PROB_SCAMBIO_CPU_GIORNALIERA,
    PROB_USCITA_PREMATURA_GIORNALIERA,
    PROBABILITA_ALLENATORE_PER_NASCITA,
    PROBABILITA_IPOVEDENTE_CREAZIONE,
    QUOTA_SEDUTA_LIBERI,
    REPUTAZIONE_MINIMA,
    RIALZO_CPU,
    RIALZO_RINNOVO_CPU,
    SCARTI_MASSIMI_CPU,
    SFIDE_ACCUMULABILI,
    SFIDE_AL_MESE,
    SOGLIA_GLORIA_BASSA_CHIUSURA,
    SOGLIA_MINIMA_TESSERATI_CHIUSURA,
    SOGLIA_SPESA_AUTONOMI,
    STIPENDIO_MINIMO,
)
from economia import (
    arrotonda,
    bandiera_attiva,
    ingaggio_richiesto,
    mesi_di_pazienza,
    pazienza_per_euro,
    scritta_in_euro,
    spesa_mensile_cpu,
    sponsor_mensile,
    stipendio,
    stipendio_pagato,
    valore_di_mercato,
)
from modelli import Giocatore, Polisportiva, conti_vuoti, normalizza_nome, probabilita_accettazione
from nomi import genera_nome_casuale
from utilita import accorda, adesso, adesso_utc, caso, converti_in_tempo, data_breve, formatta_eta_sim, in_ora_locale, senza_raccolta

ORE_PER_TICK = 8
DURATA_TICK = datetime.timedelta(hours=ORE_PER_TICK)
# Le voci del riepilogo di un avanzamento, oltre all'ora in cui è avvenuto.
CHIAVI_RAPPORTO = ("ticks", "giorni", "guariti", "ritirati", "usciti", "morti", "nuovi", "autoallenati",
                   "tesserati_cpu", "svincolati_cpu", "poli_chiuse", "poli_create", "partiti", "vendite",
                   "tuoi_non_pagati", "tuoi_partiti", "tuoi_venduti", "mesi", "tuoi_ritirati", "tuoi_usciti", "tue_bandiere",
                   "infortunati_in_seduta", "tuoi_infortunati_in_seduta", "contratti_scaduti", "rinnovi_cpu", "tuoi_scaduti", "tuoi_in_scadenza",
                   # Dalla tappa 12, punto 12.8 del progetto: i tornei, le sfide e gli infortuni in gara, del mondo e dei tuoi.
                   "tornei_conclusi", "incontri_torneo", "incontri_ritiro", "incontri_tavolino", "infortuni_in_gara", "acciacchi_in_gara",
                   "sfide_giocate", "edizioni_annullate", "tue_edizioni_annullate", "tue_iscrizioni", "tue_iscrizioni_saltate",
                   "tue_medaglie_oro", "tue_medaglie_argento", "tue_medaglie_bronzo", "tue_medaglie_legno", "tuoi_titoli_mondiali",
                   "tue_coppe_oro", "tue_coppe_argento", "tue_coppe_bronzo", "tue_coppe_legno", "tuoi_premi", "tuoi_infortuni_in_gara",
                   "tuoi_acciacchi", "tuoi_tavolini", "tuoi_qualificati", "tue_qualificazioni_coppa", "tuoi_tornei_conclusi",
                   "sfide_ricevute", "sfide_in_attesa", "sfide_decadute", "tue_sfide_vinte", "tue_sfide_perse", "tue_sfide_a_tavolino",
                   "calendario_con_problemi",
                   # Il passo 3 della tappa 12: i campionati mondiali conclusi, notizia del mondo nella barra.
                   "mondiali_conclusi",
                   # La revisione della tappa 12: tutti i premi pagati dalle sedi concluse, non soltanto quelli del podio
                   # che l'albo conserva, per la misura del calendario nella simulazione lunga.
                   "premi_tornei",
                   # La tappa 13, progetto 4.5: le notizie dello staff dell'utente.
                   "tuo_staff_partito", "tuo_staff_scaduto", "tuo_staff_uscito", "tue_prelazioni", "tuo_staff_in_scadenza")
# Per quanti giorni simulati si conservano le voci dei diari: zero vuol dire per sempre, come in Terminal Beast.
CONSERVAZIONE_PREDEFINITA = {"giocatori": 0, "polisportive": 0}
USCITA_PREMATURA = "Uscita Prematura"
DECESSO = "Decesso Naturale"


def _silenzio(*_args, **_kwargs):
    """Al posto di notifica quando chi usa il mondo non la passa."""


def nome_completo(g):
    return f"{g.nome} {g.cognome}"


class _Vetrina:
    """
    I liberi del giorno in ordine di valore, con la gloria che ciascuno chiede, in un albero dei
    minimi: trova in un passo il primo, da un certo posto in poi, che chiede al massimo una certa
    gloria, e toglie chi è stato tesserato. Al posto di scorrere tutti i liberi per ogni mossa di
    ogni polisportiva, che con migliaia di giocatori costava secondi al giorno: problema P18.
    """

    def __init__(self, richieste):
        self.quanti = len(richieste)
        self.larghezza = 1
        while self.larghezza < self.quanti:
            self.larghezza *= 2
        self.minimi = [math.inf] * (2 * self.larghezza)
        self.minimi[self.larghezza:self.larghezza + self.quanti] = richieste
        for nodo in range(self.larghezza - 1, 0, -1):
            self.minimi[nodo] = min(self.minimi[2 * nodo], self.minimi[2 * nodo + 1])

    def togli(self, posto):
        nodo = self.larghezza + posto
        self.minimi[nodo] = math.inf
        nodo //= 2
        while nodo:
            self.minimi[nodo] = min(self.minimi[2 * nodo], self.minimi[2 * nodo + 1])
            nodo //= 2

    def primo(self, gloria, da=0):
        """Il posto del primo libero, da da in poi, che chiede al massimo gloria; None se non c'è."""
        if da >= self.quanti:
            return None
        return self._cerca(1, 0, self.larghezza, gloria, da)

    def _cerca(self, nodo, inizio, fine, gloria, da):
        if fine <= da or self.minimi[nodo] > gloria:
            return None
        if fine - inizio == 1:
            return inizio
        meta = (inizio + fine) // 2
        trovato = self._cerca(2 * nodo, inizio, meta, gloria, da)
        return trovato if trovato is not None else self._cerca(2 * nodo + 1, meta, fine, gloria, da)


class _Mercato:
    """
    I giocatori in vendita del giorno per gli acquisti del computer, dalla tappa 12, decisione 4 di
    Gabriele del 14 ottobre 2026: le righe di Mondo._vendibili dal valore più alto, a parità di valore
    nel loro ordine, perché l'ordinamento è stabile, e soltanto quelle col prezzo entro il prezzo più
    alto che il computer paga, che nessuna polisportiva può superare. Così la prima riga che va bene a
    una polisportiva è proprio quella che prima trovava scorrendo tutte le righe, la più forte e, a pari
    forza, la prima: la scelta resta la stessa. Le scorte dei prezzi e degli stipendi più bassi da ogni
    riga in giù fermano la ricerca appena nessuna riga rimasta può stare nei conti. Prima ogni
    polisportiva del computer scorreva tutti i giocatori in vendita: nel mondo a regime, con un mercato
    affollato, più di mezzo secondo al giorno.
    Il primo passo della decisione 1 di Gabriele del 14 ottobre 2026 alzava quel tetto col premio della
    cassa piena di chi compra, una somma in euro staccata dal valore del giocatore: una polisportiva del
    computer con 45.000 euro in cassa comprava a tre volte il suo valore chi l'utente metteva in vendita
    a un prezzo gonfiato, e l'utente faceva soldi senza limite. La verifica del 15 ottobre 2026 lo ha
    tolto: il premio della cassa piena vale negli stipendi, non nel prezzo.
    """

    def __init__(self, righe):
        self.righe = sorted((riga for riga in righe if not riga[2] > riga[3]), key=lambda riga: riga[0].indice_collettivo_valore, reverse=True)
        self.prezzi_minimi = [0] * len(self.righe)
        self.stipendi_minimi = [0] * len(self.righe)
        prezzo_minimo = stipendio_minimo = math.inf
        for posto in range(len(self.righe) - 1, -1, -1):
            _g, _venditore, prezzo, _massimo, chiesto = self.righe[posto]
            prezzo_minimo = min(prezzo_minimo, prezzo)
            stipendio_minimo = min(stipendio_minimo, chiesto)
            self.prezzi_minimi[posto] = prezzo_minimo
            self.stipendi_minimi[posto] = stipendio_minimo

    def chiuso(self, spendibile, debole):
        """
        Vero se nessuna riga può andare bene con quella cassa da spendere e quel tesserato più debole,
        qualunque sia lo stipendio che i conti permettono: è il primo controllo di scelta, che allora
        non trova niente.
        """
        if not self.righe or self.prezzi_minimi[0] > spendibile:
            return True
        return debole is not None and self.righe[0][0].indice_collettivo_valore <= debole.indice_collettivo_valore

    def scelta(self, poli, spendibile, massimo, debole):
        """
        Il giocatore che la polisportiva compra, con chi lo vende e il prezzo, oppure None: il più forte
        ancora in vendita al prezzo di stamattina, non suo, col prezzo nella cassa da spendere, lo
        stipendio nei conti e, a rosa piena, più forte del tesserato che vale meno.
        """
        soglia = None if debole is None else debole.indice_collettivo_valore
        prezzi_minimi, stipendi_minimi = self.prezzi_minimi, self.stipendi_minimi
        for posto, (g, venditore, prezzo, _massimo, chiesto) in enumerate(self.righe):
            if prezzi_minimi[posto] > spendibile or stipendi_minimi[posto] > massimo:
                return None
            if soglia is not None and g.indice_collettivo_valore <= soglia:
                return None
            # Chi è già stato comprato oggi non è più in vendita.
            if venditore is poli or venditore.in_vendita.get(g.id) != prezzo:
                continue
            if prezzo > spendibile or chiesto > massimo:
                continue
            return g, venditore, prezzo
        return None


class Mondo:
    def __init__(self, notifica=None):
        self.notifica = notifica or _silenzio
        self.giocatori = {}
        self.polisportive = {}
        self.miapolisportiva_attiva = None
        # L'istante reale dell'ultimo avanzamento, in UTC: l'ancora da cui si contano le 8 ore.
        self.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(days=1)
        # La data del calendario simulato, che avanza di un giorno per avanzamento.
        self.datetime_corrente_simulazione = adesso()
        self.nuovi_giocatori_sessione = []
        self.giocatori_ritirati_sessione = []
        self.giocatori_morti_sessione = []
        self._ids_morti_processati_sessione = set()
        self.risultati_ultima_ricerca = []
        # Il numero che avrà il prossimo giocatore: sale soltanto, e si salva col mondo.
        self.prossimo_id = 1
        # Diventa vero quando il salvataggio esiste ma non si legge: da lì non si salva più nulla.
        self.salvataggio_bloccato = False
        # Chi è uscito di scena, dal più recente: il registro delle vecchie glorie, salvato col mondo.
        self.vecchie_glorie = []
        self.conservazione_diari = dict(CONSERVAZIONE_PREDEFINITA)
        # La memoria dei conti delle mosse del computer, che vive soltanto mentre il computer muove:
        # None fuori da lì, punto 1.3 del progetto della tappa 12.
        self._conti_del_giorno = None
        # La memoria degli sponsor dei conti del primo del mese, dalla decisione 4 di Gabriele del 14
        # ottobre 2026: None fuori da lì, vedi _sponsor_del_mese.
        self._sponsor_ricordati = None
        # Dalla tappa 12 il calendario dei tornei e le sfide fra polisportive, salvati col mondo nel formato 7.
        self.calendario = calendario.Calendario()
        self.sfide = sfide.RegistroSfide()
        # Dalla tappa 13 gli allenatori del mondo, per numero, e il numero del prossimo, salvati nel
        # formato 8; i fattori dello staff di ogni polisportiva, che non si salvano: li ricava
        # aggiorna_fattori_staff. Vero se lo staff è appena nato dall'aggiornamento al formato 8.
        self.allenatori = {}
        self.prossimo_allenatore = 1
        self._fattori_staff = {}
        # Lo staff medio del mondo, risposta 30: lo misura aggiorna_fattori_staff, e zero vuol dire nessuno staff.
        self._qualita_media = 0.0
        self._norma_staff = modulo_staff.NORMA_NEUTRA
        self.staff_appena_nato = False
        # L'ora vera dell'ultimo avanzamento, per la riserva dei nuovi allenatori all'utente; None fuori dal programma.
        self._ora_reale = None

    # Probabilità, ricerche, diari.

    @staticmethod
    def probabilita_accettazione(g_off, g_rich):
        return probabilita_accettazione(g_off, g_rich)

    def trova_giocatori_liberi_ordinati(self):
        """I giocatori liberi, non ritirati e vivi, dal più forte al più debole."""
        liberi = {gid: g for gid, g in self.giocatori.items() if g.appartenenza == "*" and not g.ritirato and gid not in self._ids_morti_processati_sessione}
        return dict(sorted(liberi.items(), key=lambda item: item[1].indice_collettivo_valore, reverse=True))

    # La polisportiva dell'utente.

    def trova_polisportiva(self, nome):
        """La polisportiva con quel nome, maiuscole a parte, oppure None."""
        cercato = normalizza_nome(nome).casefold()
        return next((p for chiave, p in self.polisportive.items() if chiave.casefold() == cercato), None)

    def problema_nome_polisportiva(self, nome):
        """Perché un nome non va bene per una polisportiva nuova, oppure None se va bene."""
        nome = normalizza_nome(nome)
        if not NOME_POLISPORTIVA_MIN <= len(nome) <= NOME_POLISPORTIVA_MAX:
            return f"Il nome deve avere da {NOME_POLISPORTIVA_MIN} a {NOME_POLISPORTIVA_MAX} caratteri."
        esistente = self.trova_polisportiva(nome)
        if esistente is not None:
            return f"Esiste già una polisportiva che si chiama {esistente.nome}."
        return None

    def fonda_polisportiva(self, nome, password=None, attiva=True):
        """Fonda una polisportiva dell'utente, protetta se riceve una password; ValueError se il nome non va."""
        problema = self.problema_nome_polisportiva(nome)
        if problema:
            raise ValueError(problema)
        poli = Polisportiva(nome=nome, password=password or None, datetime_creazione_sim=self.datetime_corrente_simulazione)
        self.polisportive[poli.nome] = poli
        if attiva:
            self.miapolisportiva_attiva = poli
        return poli

    @staticmethod
    def mosse_rimaste(poli):
        return max(0, LIMITE_MOVIMENTI_PER_TICK - poli.movimenti_oggi)

    @staticmethod
    def _usa_mossa(poli):
        poli.movimenti_oggi += 1
        poli.datetime_ultimo_movimento = adesso()

    def _senza_mosse(self, poli):
        return f"Per oggi {poli.nome} ha finito le mosse di mercato: ne ha {LIMITE_MOVIMENTI_PER_TICK} al giorno."

    def problema_offerta(self, poli, g, ingaggio=None):
        """Perché la polisportiva non può offrire al giocatore l'ingaggio dato, oppure None se può."""
        if ingaggio is not None and ingaggio > poli.cassa:
            return f"La cassa di {poli.nome} ha {scritta_in_euro(poli.cassa)}: non bastano per offrirne {scritta_in_euro(ingaggio)}."
        if self.mosse_rimaste(poli) <= 0:
            return self._senza_mosse(poli)
        if len(poli.tesserati) >= poli.maxtesserati:
            return f"{poli.nome} ha già {poli.maxtesserati} tesserati, il massimo."
        if g.id in self._ids_morti_processati_sessione:
            return f"{nome_completo(g)} è {accorda(g.sesso, 'uscito')} di scena."
        if g.ritirato:
            return f"{nome_completo(g)} si è {accorda(g.sesso, 'ritirato')} dall'attività."
        if g.appartenenza != "*":
            return f"{nome_completo(g)} è già {accorda(g.sesso, 'tesserato')} con {g.appartenenza}."
        return None

    def offerta(self, poli, g, ingaggio=None):
        """
        Un'offerta di tesseramento dell'utente, con un premio d'ingaggio, per default quello che il
        giocatore chiede: usa una mossa, e il giocatore accetta con una probabilità che cresce con
        l'offerta rispetto alla richiesta. Se accetta, l'ingaggio esce dalla cassa. Restituisce
        l'esito e la probabilità; ValueError se l'offerta non si può fare.
        """
        richiesta = ingaggio_richiesto(g, poli)
        ingaggio = richiesta if ingaggio is None else int(ingaggio)
        problema = self.problema_offerta(poli, g, ingaggio)
        if problema:
            raise ValueError(problema)
        self._usa_mossa(poli)
        probabilita = probabilita_accettazione(ingaggio, richiesta)
        accetta = caso(probabilita)
        if accetta:
            self._paga_ingaggio(poli, ingaggio)
            self._tessera(poli, g, ingaggio=ingaggio)
        else:
            self.annota(g, f"Rifiuta l'offerta di {poli.nome}, con un ingaggio di {scritta_in_euro(ingaggio)}.")
            self.annota(poli, f"{nome_completo(g)} rifiuta l'offerta, con un ingaggio di {scritta_in_euro(ingaggio)}.")
        return accetta, probabilita

    @staticmethod
    def _paga_ingaggio(poli, ingaggio):
        poli.cassa -= ingaggio
        poli.conti_del_mese["ingaggi"] += ingaggio

    def _entra(self, poli, g, data=None):
        """
        Il giocatore entra nella polisportiva: la fedeltà riparte da zero, la pazienza è piena, nessun
        arretrato. Dalla tappa 11 firma un contratto, ed è il solo punto da cui si firma: ci passano
        l'ingaggio, le mosse del computer e gli acquisti, perché comprare vuol dire firmare un
        contratto nuovo col compratore. Lo stipendio è quello che chiede oggi, la durata quella che
        propone; il programma riparte dalla sua indole, a intensità normale.
        """
        g.appartenenza = poli.nome
        poli.aggiungi_tesserato(g.id, g.indice_collettivo_valore)
        self._fattori_del_giocatore(g)
        g.fedelta = 0.
        g.pazienza = 100.
        g.arretrati = 0
        contratti.stipula(g, data or self.datetime_corrente_simulazione, stipendio(g), contratti.durata_proposta(g))
        g.programma = g.indole
        g.intensita = INTENSITA_PREDEFINITA
        # Dalla tappa 12 l'iscrizione automatica ai tornei è accesa per chi si tessera, risposta 17 di Gabriele.
        g.iscrizione_automatica = True

    def _tessera(self, poli, g, data=None, ingaggio=None):
        self._entra(poli, g, data)
        con_ingaggio = f", con un ingaggio di {scritta_in_euro(ingaggio)}" if ingaggio else ""
        self.annota(g, f"{accorda(g.sesso, 'Tesserato')} con {poli.nome}{con_ingaggio}.", data)
        self.annota(poli, f"Tesserato {nome_completo(g)}{con_ingaggio}.", data)

    def _lascia(self, poli, g):
        """
        Il giocatore esce dall'elenco dei tesserati e torna libero, senza voci di diario: le
        scrive chi chiama. Esce anche dalla vendita, e i suoi arretrati non li aspetta più. Dalla
        tappa 11 il contratto si cancella, con rinnovo e proposte, e programma e intensità tornano
        quelli della sua indole.
        """
        poli.rimuovi_tesserato(g.id, g.indice_collettivo_valore)
        poli.in_vendita.pop(g.id, None)
        g.appartenenza = "*"
        self._fattori_del_giocatore(g)
        g.fedelta = 0.
        g.pazienza = 100.
        g.arretrati = 0
        g.annulla_contratto()
        g.programma = g.indole
        g.intensita = INTENSITA_PREDEFINITA

    # Lo staff, tappa 13, decisione D33.

    def nuovo_numero_allenatore(self):
        """Il numero di un allenatore nuovo: il contatore sale soltanto, e si salva col mondo."""
        numero = self.prossimo_allenatore
        self.prossimo_allenatore += 1
        return numero

    def aggiorna_fattori_staff(self, poli=None):
        """
        I fattori dello staff: per ogni polisportiva, o soltanto per quella data, i tre fattori dalla
        qualità del suo staff; sui giocatori, fattore_staff per l'allenamento e fattore_rischio_staff per
        gli infortuni, quelli della loro polisportiva per i tesserati e quelli senza staff per i liberi,
        D33 risposta 4. Si chiama al caricamento, all'inizio di ogni giorno simulato e quando cambia uno
        staff; i fattori non si salvano. Lo staff medio, scelta di Gabriele del 21 ottobre 2026, risposta
        30, è la qualità media dello staff del mondo: si misura con tutte le polisportive, e resta quella
        del giorno quando cambia lo staff di una sola. La qualità di ogni polisportiva si calcola una volta,
        per la media e per i fattori; sui giocatori il ciclo è uno solo, coi fattori senza staff calcolati
        una volta, e salta i ritirati, che non si allenano e non giocano: una chiamata per giocatore
        costava al giorno a regime il 9 per cento del giorno, misurato il 21 ottobre 2026 sera. I numeri
        sono gli stessi di _fattori_del_giocatore e di staff.qualita_media. Dalla risposta 35 di Gabriele del
        22 ottobre 2026 i fattori si dividono per la norma del giorno, la loro media sui tesserati, così il
        mondo nel suo insieme si allena sempre come prima: la norma si misura con tutte le polisportive, e
        resta quella del giorno quando cambia lo staff di una sola, come la media delle qualità.
        """
        club = [poli] if poli is not None else list(self.polisportive.values())
        qualita = [modulo_staff.qualita_della_polisportiva(p, self.allenatori) for p in club]
        if poli is None:
            self._qualita_media = modulo_staff.media([q for p, q in zip(club, qualita, strict=True) if p.tesserati])
        grezzi = [modulo_staff.fattori(q, self._qualita_media) for q in qualita]
        if poli is None:
            self._norma_staff = modulo_staff.norma([(fattori_del_club, len(p.tesserati)) for p, fattori_del_club in zip(club, grezzi, strict=True)])
        for p, fattori_del_club in zip(club, grezzi, strict=True):
            self._fattori_staff[p.nome] = modulo_staff.normalizzati(fattori_del_club, self._norma_staff)
        senza_staff = modulo_staff.normalizzati(modulo_staff.fattori(0.0, self._qualita_media), self._norma_staff)
        fattori = self._fattori_staff
        if poli is None:
            giocatori = self.giocatori.values()
        else:
            giocatori = [g for gid in poli.tesserati if (g := self.giocatori.get(gid)) is not None]
        for g in giocatori:
            if g.ritirato:
                continue
            club_del_giocatore = g.appartenenza
            allenamento, rischio, _fedelta = senza_staff if club_del_giocatore == "*" else fattori.get(club_del_giocatore, senza_staff)
            g.fattore_staff = allenamento
            g.fattore_rischio_staff = rischio

    @property
    def qualita_media_dello_staff(self):
        """Lo staff medio del mondo di oggi, risposta 30."""
        return self._qualita_media

    def fattori_staff(self, poli):
        """I tre fattori dello staff della polisportiva: allenamento, rischio d'infortunio, crescita della fedeltà."""
        fattori = self._fattori_staff.get(poli.nome)
        if fattori is None:
            grezzi = modulo_staff.fattori(modulo_staff.qualita_della_polisportiva(poli, self.allenatori), self._qualita_media)
            fattori = self._fattori_staff[poli.nome] = modulo_staff.normalizzati(grezzi, self._norma_staff)
        return fattori

    def _fattori_del_giocatore(self, g):
        """I fattori dello staff sul giocatore: quelli della sua polisportiva, o quelli senza staff per un libero."""
        poli = self.polisportive.get(g.appartenenza) if g.appartenenza != "*" else None
        if poli is not None:
            allenamento, rischio, _fedelta = self.fattori_staff(poli)
        else:
            allenamento, rischio, _fedelta = modulo_staff.normalizzati(modulo_staff.fattori(0.0, self._qualita_media), self._norma_staff)
        g.fattore_staff = allenamento
        g.fattore_rischio_staff = rischio

    def _riserva(self, a, ora=None):
        """
        La riserva all'utente di chi diventa allenatore, regola di Gabriele, risposta 29: per
        MINUTI_RISERVA_UTENTE minuti veri dall'avanzamento che lo fa nascere, o dall'ora data. Fuori dal
        programma, nelle prove e negli strumenti che fanno avanzare i giorni a mano, non c'è ora vera e non
        c'è riserva.
        """
        ora = ora or self._ora_reale
        if ora is not None:
            a.riservato_fino = ora + datetime.timedelta(minutes=MINUTI_RISERVA_UTENTE)

    def _visibile_al_computer(self, a):
        """Vero se il computer può assumere l'allenatore: libero, senza prelazione e senza riserva per l'utente."""
        if not a.libero or a.prelazione is not None:
            return False
        return a.riservato_fino is None or a.riservato_fino <= (self._ora_reale or adesso_utc())

    def _nasce_un_allenatore(self, data, rng=random, eta_giorni=None):
        """Un allenatore nato, libero, D33 risposta 8: entra nel mondo e nel suo diario."""
        a = modulo_staff.nato(self.nuovo_numero_allenatore(), data, rng, eta_giorni)
        ruolo = "allenatrice" if a.sesso == "f" else "allenatore"
        a.annota(data, f"Entra nel mondo dello showdown da {ruolo}, a {int(a.eta_anni(data))} anni, di classe {a.codice}.")
        self._riserva(a)
        self.allenatori[a.numero] = a
        return a

    def _ex_giocatore_allenatore(self, g, club, data, fedelta=0.0, rng=random, rapporto=None):
        """
        Il giocatore g, che si ritira con una classe migliore di almeno H0, diventa un allenatore libero,
        D33 risposta 7; club è la polisportiva che ha lasciato, o None, con la fedeltà che aveva. Se si
        ritira da tesserato dell'utente, l'utente ha la prelazione per GIORNI_PRELAZIONE giorni, risposte
        15 e 21, e la sua polisportiva lo legge nel diario.
        """
        a = modulo_staff.ex_giocatore(self.nuovo_numero_allenatore(), g, data, rng, club.nome if club is not None else None, fedelta)
        self._riserva(a)
        self.allenatori[a.numero] = a
        giocatore, allenatore = ("giocatrice", "allenatrice") if a.sesso == "f" else ("giocatore", "allenatore")
        a.annota(data, f"Si ritira da {giocatore} e può allenare: è di classe {a.codice} da {allenatore}, la sua classe migliore.")
        if club is not None and not club.is_cpu_controlled:
            a.prelazione = club.nome
            a.prelazione_fino = data + datetime.timedelta(days=GIORNI_PRELAZIONE)
            self.annota(club, f"{nome_completo(g)} si ritira e può allenare, di classe {a.codice}: per {GIORNI_PRELAZIONE} giorni puoi {'assumerla' if g.sesso == 'f' else 'assumerlo'} prima degli altri.", data)
            if rapporto is not None:
                rapporto["tue_prelazioni"] += 1
        return a

    def _fine_allenatore(self, a, data, testo_allenatore, testo_club, rapporto=None):
        """
        L'allenatore esce di scena: lascia il posto nello staff, se ne aveva uno, coi diari, ed esce dal
        mondo degli allenatori. Se era nello staff dell'utente, è una notizia dell'avanzamento. La polisportiva
        gli paga lo stipendio maturato fino a quel giorno, progetto 1.4, che la revisione del 22 ottobre 2026
        ha visto mancare.
        """
        poli = self.polisportive.get(a.polisportiva) if a.polisportiva is not None else None
        if poli is not None:
            if rapporto is not None and not poli.is_cpu_controlled:
                rapporto["tuo_staff_uscito"] += 1
            pagato = self._paga_il_maturato(poli, a, data)
            if pagato:
                testo_club = f"{testo_club} Pagato lo stipendio maturato, {scritta_in_euro(pagato)}."
            poli.staff = [0 if numero == a.numero else numero for numero in poli.staff]
            self.annota(poli, testo_club, data)
            self.aggiorna_fattori_staff(poli)
        a.annota(data, testo_allenatore)
        self.allenatori.pop(a.numero, None)

    def _paga_il_maturato(self, poli, a, data):
        """
        Lo stipendio maturato di un allenatore che esce di scena: lo stipendio si paga il primo del mese per il
        mese finito, quindi il primo del mese è il mese intero, che lo staff invecchia prima dei conti, e gli
        altri giorni la parte dei giorni già passati. Fin dove arriva la cassa. Restituisce quanto ha pagato.
        """
        if a.contratto_stipendio <= 0:
            return 0
        if data.day == 1:
            dovuto = a.contratto_stipendio
        else:
            dovuto = round(a.contratto_stipendio * (data.day - 1) / calendar.monthrange(data.year, data.month)[1])
        pagato = min(dovuto, max(0, poli.cassa))
        poli.cassa -= pagato
        poli.conti_del_mese["staff"] += pagato
        return pagato

    def _invecchia_lo_staff(self, data, rapporto=None):
        """
        Ogni giorno, per gli allenatori: chi è nato allenatore muore alla sua età di morte, come i
        giocatori; chi arriva all'età in cui smette smette, D33 risposta 11; e la prelazione scade.
        Gli ex giocatori muoiono col loro giocatore, in _uscita.
        """
        for a in list(self.allenatori.values()):
            eta = a.eta(data)
            chi = f"{nome_completo(a)}, {'allenatrice' if a.sesso == 'f' else 'allenatore'} dello staff,"
            if a.tipo == modulo_staff.NATO and eta >= a.etamorte:
                self._fine_allenatore(a, data, f"Muore, a {int(eta / ANNO_SIMULAZIONE_GIORNI)} anni.", f"{chi} muore.", rapporto)
            elif eta >= a.eta_fine:
                self._fine_allenatore(a, data, f"Smette di allenare, a {int(eta / ANNO_SIMULAZIONE_GIORNI)} anni.", f"{chi} smette di allenare.", rapporto)
            elif a.prelazione_fino is not None and data >= a.prelazione_fino:
                a.prelazione = a.prelazione_fino = None

    def _congeda_lo_staff(self, poli, data):
        """
        La polisportiva chiude: il suo staff torna libero, senza contratto, e decade la prelazione sui suoi
        ritirati, che restava su un club che non c'era più, revisione del 22 ottobre 2026.
        """
        for numero in poli.staff:
            a = self.allenatori.get(numero) if numero else None
            if a is not None:
                modulo_staff.libera(a)
                a.annota(data, f"Torna {'libera' if a.sesso == 'f' else 'libero'}: {poli.nome} ha chiuso.")
        for a in self.allenatori.values():
            if a.prelazione == poli.nome:
                a.prelazione = a.prelazione_fino = None
        poli.staff = [0, 0, 0]

    def problema_assunzione(self, poli, a, posto, ingaggio):
        """Perché la polisportiva non può assumere l'allenatore nel posto con quell'ingaggio, o None se può."""
        if not 0 <= posto < modulo_staff.POSTI:
            return "quel posto dello staff non esiste"
        if poli.staff[posto]:
            return "quel posto dello staff è già occupato"
        if not a.libero:
            return f"{nome_completo(a)} allena già {a.polisportiva}"
        if a.prelazione is not None and a.prelazione != poli.nome:
            return f"fino al {data_breve(a.prelazione_fino)} {nome_completo(a)} può {'assumerla' if a.sesso == 'f' else 'assumerlo'} soltanto {a.prelazione}"
        if ingaggio > poli.cassa:
            return f"l'ingaggio di {scritta_in_euro(ingaggio)} supera la cassa, {scritta_in_euro(poli.cassa)}"
        return None

    def assumi_allenatore(self, poli, a, posto, data=None, ingaggio=0):
        """
        La polisportiva assume l'allenatore nel posto, 0 il capo, 1 e 2 gli assistenti, D33 risposta 13:
        paga l'ingaggio, e l'allenatore firma un contratto, con lo stipendio che chiede per il ruolo e la
        durata che propone. Chi chiama controlla prima con problema_assunzione; ValueError se non si può.
        """
        problema = self.problema_assunzione(poli, a, posto, ingaggio)
        if problema:
            raise ValueError(problema)
        oggi = data or self.datetime_corrente_simulazione
        ruolo = modulo_staff.CAPO if posto == 0 else modulo_staff.ASSISTENTE
        if ingaggio:
            self._paga_ingaggio(poli, ingaggio)
        a.polisportiva, a.ruolo = poli.nome, ruolo
        a.prelazione = a.prelazione_fino = a.riservato_fino = None
        contratti.stipula(a, oggi, modulo_staff.stipendio_richiesto(a, ruolo), modulo_staff.durata_proposta(a, oggi))
        poli.staff[posto] = a.numero
        nome_ruolo = modulo_staff.nome_del_ruolo(a)
        con_ingaggio = f", con un ingaggio di {scritta_in_euro(ingaggio)}" if ingaggio else ""
        a.annota(oggi, f"Firma con {poli.nome} da {nome_ruolo}: {scritta_in_euro(a.contratto_stipendio)} al mese fino al {data_breve(a.contratto_scadenza)}{con_ingaggio}.")
        self.annota(poli, f"Assume {nome_completo(a)} da {nome_ruolo}, di classe {a.codice}{con_ingaggio}.", oggi)
        self.aggiorna_fattori_staff(poli)

    # Lo staff dell'utente: l'offerta d'ingaggio, il licenziamento e il rinnovo, come per i giocatori,
    # D33 risposta 13. Lettura di ClaudIA da confermare al collaudo: l'offerta e il licenziamento usano
    # una mossa di mercato, come l'ingaggio e lo svincolo di un giocatore; il rinnovo no.

    def problema_offerta_allenatore(self, poli, a, posto, ingaggio=None):
        """Perché la polisportiva non può offrire all'allenatore il posto con quell'ingaggio, oppure None se può."""
        if ingaggio is not None and ingaggio > poli.cassa:
            return f"La cassa di {poli.nome} ha {scritta_in_euro(poli.cassa)}: non bastano per offrirne {scritta_in_euro(ingaggio)}."
        if self.mosse_rimaste(poli) <= 0:
            return self._senza_mosse(poli)
        if a.numero not in self.allenatori:
            return f"{nome_completo(a)} non allena più."
        problema = self.problema_assunzione(poli, a, posto, 0)
        return f"{problema[0].upper()}{problema[1:]}." if problema else None

    def offerta_allenatore(self, poli, a, posto, ingaggio):
        """
        L'offerta dell'utente a un allenatore libero per il posto, con un premio d'ingaggio: usa una mossa,
        e l'allenatore accetta con la probabilità dell'ingaggio dei giocatori. Se accetta, firma come in
        assumi_allenatore. Restituisce l'esito e la probabilità; ValueError se l'offerta non si può fare.
        """
        ingaggio = int(ingaggio)
        problema = self.problema_offerta_allenatore(poli, a, posto, ingaggio)
        if problema:
            raise ValueError(problema)
        self._usa_mossa(poli)
        ruolo = modulo_staff.CAPO if posto == 0 else modulo_staff.ASSISTENTE
        probabilita = probabilita_accettazione(ingaggio, modulo_staff.ingaggio_richiesto(a, ruolo, poli))
        accetta = caso(probabilita)
        if accetta:
            self.assumi_allenatore(poli, a, posto, ingaggio=ingaggio)
        else:
            a.annota(self.datetime_corrente_simulazione, f"Rifiuta l'offerta di {poli.nome}, un ingaggio di {scritta_in_euro(ingaggio)}.")
            self.annota(poli, f"{nome_completo(a)} rifiuta l'ingaggio di {scritta_in_euro(ingaggio)}.")
        return accetta, probabilita

    def problema_licenziamento(self, poli, a):
        """Perché la polisportiva non può licenziare l'allenatore, oppure None: le mosse e la cassa per la buonuscita."""
        if a.polisportiva != poli.nome:
            return f"{nome_completo(a)} non è nello staff di {poli.nome}."
        if self.mosse_rimaste(poli) <= 0:
            return self._senza_mosse(poli)
        buonuscita = contratti.buonuscita(a, self.datetime_corrente_simulazione)
        if buonuscita > poli.cassa:
            return f"Licenziare {nome_completo(a)} costa una buonuscita di {scritta_in_euro(buonuscita)}, e la cassa di {poli.nome} ne ha {scritta_in_euro(poli.cassa)}."
        return None

    def licenzia_allenatore(self, poli, a, data=None):
        """
        La polisportiva licenzia l'allenatore a contratto in corso: usa una mossa, paga la buonuscita, metà
        degli stipendi che restano, come per i giocatori, e l'allenatore torna libero. Restituisce la
        buonuscita; ValueError se non si può.
        """
        problema = self.problema_licenziamento(poli, a)
        if problema:
            raise ValueError(problema)
        self._usa_mossa(poli)
        oggi = data or self.datetime_corrente_simulazione
        buonuscita = self._paga_buonuscita(poli, a, oggi)
        nome_ruolo = modulo_staff.nome_del_ruolo(a)
        self._lascia_lo_staff(poli, a, oggi, f"{accorda(a.sesso, 'Licenziato')} da {poli.nome}, con una buonuscita di {scritta_in_euro(buonuscita)}.",
                              f"Licenzia {nome_completo(a)}, {nome_ruolo}, con una buonuscita di {scritta_in_euro(buonuscita)}.")
        return buonuscita

    def problema_rinnovo_allenatore(self, poli, a, stipendio_offerto=None, mesi=None):
        """Perché la polisportiva non può proporre oggi il rinnovo all'allenatore, con quello stipendio e quella durata; None se può."""
        oggi = self.datetime_corrente_simulazione
        if a.polisportiva != poli.nome or not contratti.ha_contratto(a):
            return f"{nome_completo(a)} non è nello staff di {poli.nome}."
        if contratti.ha_rinnovo(a):
            return (f"{nome_completo(a)} ha già rinnovato: dal {data_breve(a.contratto_scadenza)} prenderà {scritta_in_euro(a.rinnovo_stipendio)} al mese, "
                    f"fino al {data_breve(a.rinnovo_scadenza)}.")
        if not contratti.in_finestra(a, oggi):
            return (f"Il contratto di {nome_completo(a)} scade il {data_breve(a.contratto_scadenza)}: il rinnovo si può proporre "
                    f"dal {data_breve(contratti.inizio_finestra(a))}.")
        if not contratti.puo_trattare(a):
            return f"{nome_completo(a)} ha già rifiutato tre proposte e non tratta più: il contratto finirà il {data_breve(a.contratto_scadenza)}."
        if a.ultima_trattativa is not None and a.ultima_trattativa.date() == oggi.date():
            return f"Oggi hai già fatto una proposta a {nome_completo(a)}: se ne fa al massimo una al giorno."
        if stipendio_offerto is not None and stipendio_offerto < 1:
            return "Lo stipendio deve essere di almeno 1 euro al mese."
        if mesi is not None and not MESI_CONTRATTO_MIN <= mesi <= MESI_CONTRATTO_MAX:
            return f"La durata va da {MESI_CONTRATTO_MIN} a {MESI_CONTRATTO_MAX} mesi."
        return None

    def rinnova_allenatore(self, poli, a, stipendio_offerto, mesi):
        """
        La proposta di rinnovo dell'utente a un allenatore del suo staff, come ai giocatori: negli ultimi
        tre mesi, una al giorno, tre in tutto, senza mosse. Se accetta, il contratto nuovo parte alla
        scadenza. Restituisce l'esito, la probabilità e la richiesta per quei mesi; ValueError se non si può.
        """
        stipendio_offerto, mesi = int(stipendio_offerto), int(mesi)
        problema = self.problema_rinnovo_allenatore(poli, a, stipendio_offerto, mesi)
        if problema:
            raise ValueError(problema)
        oggi = self.datetime_corrente_simulazione
        richiesta = modulo_staff.richiesta_rinnovo(a, poli, mesi, oggi)
        probabilita = probabilita_accettazione(stipendio_offerto, richiesta)
        a.proposte_rinnovo += 1
        a.ultima_trattativa = oggi
        accetta = caso(probabilita)
        if accetta:
            contratti.concorda_rinnovo(a, stipendio_offerto, mesi)
            cifra = f"{scritta_in_euro(a.rinnovo_stipendio)} al mese, dal {data_breve(a.contratto_scadenza)} al {data_breve(a.rinnovo_scadenza)}"
            a.annota(oggi, f"Rinnova con {poli.nome}: {cifra}.")
            self.annota(poli, f"{nome_completo(a)}, {modulo_staff.nome_del_ruolo(a)}, rinnova: {cifra}.")
        else:
            cifra = f"{scritta_in_euro(stipendio_offerto)} al mese per {mesi} mesi"
            a.annota(oggi, f"Rifiuta il rinnovo con {poli.nome} a {cifra}.")
            self.annota(poli, f"{nome_completo(a)} rifiuta il rinnovo a {cifra}.")
            if not contratti.puo_trattare(a):
                testo = f"Non vuole più trattare: il contratto con {poli.nome} finirà il {data_breve(a.contratto_scadenza)}."
                a.annota(oggi, testo)
                self.annota(poli, f"{nome_completo(a)}. {testo}")
        return accetta, probabilita, richiesta

    def _lascia_lo_staff(self, poli, a, data, testo_allenatore, testo_club):
        """L'allenatore lascia lo staff della polisportiva e torna libero, coi due diari e i fattori rifatti."""
        poli.staff = [0 if numero == a.numero else numero for numero in poli.staff]
        modulo_staff.libera(a)
        a.annota(data, testo_allenatore)
        self.annota(poli, testo_club, data)
        self.aggiorna_fattori_staff(poli)

    def _paga_lo_staff(self, poli, data, rapporto=None):
        """Il primo del mese, dopo i tesserati, lo stipendio dello staff: chi non è pagato lascia lo staff, progetto 3.2."""
        for numero in list(poli.staff):
            a = self.allenatori.get(numero) if numero else None
            if a is None:
                continue
            if a.contratto_stipendio <= poli.cassa:
                poli.cassa -= a.contratto_stipendio
                poli.conti_del_mese["staff"] += a.contratto_stipendio
            else:
                self._lascia_lo_staff(poli, a, data, f"Lascia {poli.nome}: lo stipendio non è arrivato.",
                                      f"{nome_completo(a)} lascia lo staff: lo stipendio non è arrivato.")
                if rapporto is not None and not poli.is_cpu_controlled:
                    rapporto["tuo_staff_partito"] += 1

    def _contratti_dello_staff(self, data, rapporto=None):
        """
        Il primo del mese, per lo staff di ogni polisportiva: il contratto scaduto lascia il posto al
        rinnovo concordato, oppure l'allenatore torna libero; il computer decide nella finestra se
        rinnovare o cambiare, progetto 3.4. Per l'utente, come per i tesserati, il promemoria all'ingresso
        nella finestra del rinnovo e all'ultimo mese, e le notizie dell'avanzamento.
        """
        # I livelli dei liberi che il computer vede, per i rinnovi: si fanno una volta, e si rifanno quando un
        # contratto scaduto ne libera uno, revisione del 22 ottobre 2026.
        livelli_liberi = None
        for poli in list(self.polisportive.values()):
            for numero in list(poli.staff):
                a = self.allenatori.get(numero) if numero else None
                if a is None or a.contratto_scadenza is None:
                    continue
                if a.contratto_scadenza.date() <= data.date():
                    if contratti.ha_rinnovo(a):
                        contratti.subentra_il_rinnovo(a)
                        a.annota(data, f"Comincia il contratto rinnovato con {poli.nome}: {scritta_in_euro(a.contratto_stipendio)} al mese fino al {data_breve(a.contratto_scadenza)}.")
                    else:
                        self._lascia_lo_staff(poli, a, data, f"Il contratto con {poli.nome} è scaduto: torna {'libera' if a.sesso == 'f' else 'libero'}.",
                                              f"Il contratto di {nome_completo(a)}, {modulo_staff.nome_del_ruolo(a)}, è scaduto.")
                        livelli_liberi = None
                        if rapporto is not None and not poli.is_cpu_controlled:
                            rapporto["tuo_staff_scaduto"] += 1
                elif poli.is_cpu_controlled and not contratti.ha_rinnovo(a) and contratti.in_finestra(a, data):
                    if livelli_liberi is None:
                        livelli_liberi = self._livelli_dei_liberi()
                    self._rinnovo_dello_staff_cpu(poli, a, data, livelli_liberi)
                elif not poli.is_cpu_controlled and not contratti.ha_rinnovo(a) and contratti.puo_trattare(a):
                    mesi = contratti.mesi_interi(data, a.contratto_scadenza)
                    if mesi == MESI_FINESTRA_RINNOVO:
                        testo = f"Il contratto scade il {data_breve(a.contratto_scadenza)}: da oggi si può rinnovare."
                    elif mesi == 1:
                        testo = f"Ultimo mese di contratto: se non rinnovi, il {data_breve(a.contratto_scadenza)} torna {'libera' if a.sesso == 'f' else 'libero'}."
                    else:
                        continue
                    a.annota(data, testo)
                    self.annota(poli, f"{nome_completo(a)}, {modulo_staff.nome_del_ruolo(a)}. {testo}", data)
                    if rapporto is not None:
                        rapporto["tuo_staff_in_scadenza"] += 1

    def _spazio_negli_stipendi(self, poli):
        """
        Quanto stipendio in più la polisportiva del computer si permette oggi per lo staff: soltanto lo
        sponsor, senza la cassa, risposta 31 di Gabriele del 22 ottobre 2026. Con le regole di spesa dei
        tesserati lo staff si mangiava la cassa che pagava i campioni, e i primi 10 del mondo restavano
        liberi; la prova lunga lo ha visto il 21 ottobre sera, coi quattro esperimenti della taratura.
        """
        return self._sponsor_memorizzato(poli) - self._monte_memorizzato(poli)

    def _livelli_dei_liberi(self):
        """I livelli degli allenatori che il computer vede, in ordine."""
        return sorted(b.livello for b in self.allenatori.values() if self._visibile_al_computer(b))

    def _rinnovo_dello_staff_cpu(self, poli, a, data, livelli_liberi=None):
        """
        Il computer, nella finestra del rinnovo, tiene il suo allenatore, salvo che un libero che si può
        permettere sia migliore di almeno MARGINE_CAMBIO_STAFF_CPU livelli: allora lo lascia scadere e
        assumerà l'altro, progetto 3.4. Il rinnovo è allo stipendio che l'allenatore chiede oggi. Fra i liberi
        abbastanza migliori basta guardare il più modesto, che costa meno di tutti: lo stipendio scende col
        livello. Prima si guardavano tutti gli allenatori a ogni rinnovo, revisione del 22 ottobre 2026.
        """
        if livelli_liberi is None:
            livelli_liberi = self._livelli_dei_liberi()
        stipendio = modulo_staff.stipendio_richiesto(a, a.ruolo)
        spazio = self._spazio_negli_stipendi(poli) + a.contratto_stipendio
        indice = bisect.bisect_right(livelli_liberi, a.livello - MARGINE_CAMBIO_STAFF_CPU)
        migliore = indice > 0 and modulo_staff.stipendio_del_livello(livelli_liberi[indice - 1], a.ruolo) <= spazio
        if migliore:
            return
        contratti.concorda_rinnovo(a, stipendio, modulo_staff.durata_proposta(a, data))
        a.annota(data, f"Rinnova con {poli.nome}: {scritta_in_euro(stipendio)} al mese fino al {data_breve(a.rinnovo_scadenza)}.")

    def _staff_del_computer(self, cpu, data):
        """
        Le polisportive del computer con un posto vuoto nello staff cercano l'allenatore migliore che
        possono pagare, prima il capo e poi gli assistenti, uno al giorno, D33 risposta 14: lo stipendio
        deve stare nello sponsor, risposta 31, e l'ingaggio, col rialzo del computer, nella cassa tenendo da
        parte un mese di stipendi. Non vedono gli allenatori in prelazione. I liberi si ordinano una
        volta, dal migliore: lo stipendio scende con la classe, e la ricerca è binaria. Restituisce
        quanti ne hanno assunti.
        """
        liberi = sorted((a for a in self.allenatori.values() if self._visibile_al_computer(a)), key=lambda a: (a.livello, a.numero))
        if not liberi:
            return 0
        stipendi = {ruolo: [-modulo_staff.stipendio_del_livello(a.livello, ruolo) for a in liberi] for ruolo in modulo_staff.RUOLI}
        # L'offerta più bassa che il computer potrebbe fare per ruolo, per difetto: il libero meno caro, lo
        # sconto pieno della provenienza e gli arrotondamenti alla decina. Chi non ha in cassa nemmeno
        # questa salta subito, senza calcolare lo sponsor: l'esito è lo stesso, e il caso non si tocca. Nei
        # giorni con un libero che nessuno si può permettere, il conto dello sponsor di tutte le polisportive
        # costava al giorno a regime quasi il 2 per cento, misurato il 21 ottobre 2026 sera.
        offerta_minima = {ruolo: (modulo_staff.ingaggio_minimo(min(-s for s in stipendi[ruolo])) - 5) * RIALZO_CPU - 5 for ruolo in modulo_staff.RUOLI}
        presi = set()
        assunti = 0
        # Prima i capi, per tutte: un assistente si assume soltanto coi liberi che restano, perché nei mondi
        # giovani gli allenatori sono pochi, e un club con tre allenatori ne lascerebbe due senza capo.
        senza_capo = [poli for poli in cpu if not poli.staff[0]]
        con_posti = [poli for poli in cpu if poli.staff[0] and not all(poli.staff)]
        for poli in senza_capo + con_posti:
            if len(presi) >= len(liberi):
                break
            posto = poli.staff.index(0)
            ruolo = modulo_staff.CAPO if posto == 0 else modulo_staff.ASSISTENTE
            monte = self._monte_memorizzato(poli)
            spendibile = poli.cassa - monte * MESI_DI_RISERVA_CPU
            if spendibile < offerta_minima[ruolo]:
                continue
            spazio = self._spazio_negli_stipendi(poli)
            # Il migliore libero con lo stipendio nello sponsor e l'offerta nella cassa: la ricerca binaria parte
            # dal più caro che le due cose permettono, poi si scorre fino al primo non preso con l'offerta alla
            # portata, che con la reputazione e lo sconto della provenienza cambia da club a club. Fino alla
            # revisione del 22 ottobre 2026 si guardava soltanto il più caro nello sponsor, e un club senza la
            # cassa per lui restava senza capo anche con allenatori più modesti alla portata.
            limite = min(spazio, modulo_staff.stipendio_massimo_per_la_cassa(spendibile, RIALZO_CPU))
            indice = bisect.bisect_left(stipendi[ruolo], -limite)
            a = None
            while indice < len(liberi):
                candidato = liberi[indice]
                indice += 1
                if candidato.numero in presi:
                    continue
                richiesta = modulo_staff.ingaggio_richiesto(candidato, ruolo, poli)
                offerta = arrotonda(richiesta * RIALZO_CPU)
                if offerta <= spendibile:
                    a = candidato
                    break
            if a is None:
                continue
            if caso(probabilita_accettazione(offerta, richiesta)):
                self.assumi_allenatore(poli, a, posto, data, offerta)
                presi.add(a.numero)
                assunti += 1
        return assunti

    def fai_nascere_lo_staff(self):
        """
        Lo staff di un mondo che arriva dal formato 7, D33 risposta 16: un allenatore libero per ogni
        ritirato vivo che può allenare, e gli allenatori nati che un mondo della sua età avrebbe fatto,
        uno ogni venti nascite, con età sparse. Il caso è suo, nato dalla data del mondo, e quello del
        mondo non si tocca; i nomi vengono dalle collezioni, come sempre.
        """
        oggi = self.datetime_corrente_simulazione
        rng = random.Random(f"MESS-staff-{oggi:%Y-%m-%d}")
        morti = self._ids_morti_processati_sessione
        for gid, g in sorted(self.giocatori.items()):
            if gid not in morti and g.ritirato and modulo_staff.puo_allenare(modulo_classe.livello(g.classe_migliore)):
                a = modulo_staff.ex_giocatore(self.nuovo_numero_allenatore(), g, oggi, rng)
                a.annota(oggi, f"Può allenare dal ritiro: è di classe {a.codice} da {'allenatrice' if a.sesso == 'f' else 'allenatore'}, la sua classe migliore.")
                self.allenatori[a.numero] = a
        nascite = [g.datetime_creazione_sim for g in self.giocatori.values() if isinstance(g.datetime_creazione_sim, datetime.datetime)]
        giorni = (oggi - min(nascite)).days if nascite else 0
        quanti = modulo_staff.nati_di_un_mondo(giorni)
        for _ in range(quanti):
            self._nasce_un_allenatore(oggi, rng, modulo_staff.eta_sparsa(giorni, rng))
        # Tutti diventano allenatori adesso, all'apertura: per due ore sono dell'utente, risposte 29 e 37. Chi
        # nasce allenatore già oltre l'età in cui avrebbe smesso, smette in un giorno a caso dei suoi anni
        # minimi, non tutti lo stesso giorno, revisione del 22 ottobre 2026.
        ora = adesso_utc()
        for a in self.allenatori.values():
            modulo_staff.sparpaglia_la_fine(a, oggi, rng)
            self._riserva(a, ora)
        # La notizia della partenza resta anche nel diario delle polisportive dell'utente, progetto 4.5.
        n = len(self.allenatori)
        if n == 0:
            mercato = "per ora senza allenatori liberi"
        elif n == 1:
            mercato = "con un allenatore libero, riservato a te per due ore prima del computer"
        else:
            mercato = f"con {n} allenatori liberi, riservati a te per due ore prima del computer"
        for poli in self.polisportive.values():
            if not poli.is_cpu_controlled:
                self.annota(poli, f"Arriva lo staff, un capo e due assistenti: la polisportiva parte senza, e il mercato degli allenatori è aperto, {mercato}.", oggi)
        self.staff_appena_nato = True

    # Arretrati, vendite e acquisti.

    def monte_stipendi(self, poli):
        """
        Quanto la polisportiva paga ogni mese di stipendi, a chi ha oggi: dalla tappa 11 lo stipendio del
        contratto. Dalla tappa 13 anche lo staff, così le regole di spesa del computer, la solvibilità e il
        bilancio lo contano, progetto 3.3.
        """
        giocatori = self.giocatori
        morti = self._ids_morti_processati_sessione
        tesserati = sum(stipendio_pagato(g) for gid in poli.tesserati if (g := giocatori.get(gid)) is not None and gid not in morti)
        return tesserati + self.monte_dello_staff(poli)

    def monte_dello_staff(self, poli):
        """Quanto la polisportiva paga ogni mese allo staff, tappa 13."""
        return sum(a.contratto_stipendio for numero in poli.staff if numero and (a := self.allenatori.get(numero)) is not None)

    def sponsor(self, poli):
        """Lo sponsor del mese della polisportiva, con la sua rosa di oggi."""
        return sponsor_mensile(poli, self._rosa(poli))

    def _conto_memorizzato(self, poli, posto, calcolo):
        """
        Lo sponsor del mese, al posto 0, o il monte stipendi della polisportiva, al posto 1, durante le
        mosse del computer: si calcolano una volta e si ricalcolano soltanto quando cambia la rosa, con
        una memoria indicizzata dal nome, dai tesserati nel loro ordine e dalla gloria. Mentre il
        computer muove nient'altro li cambia: la gloria si ricalcola a fine giorno, e uno stipendio
        cambia soltanto con un contratto nuovo, cioè con un tesserato che entra. Prima ogni candidato
        provato ricalcolava lo sponsor di tutta la rosa: a regime le mosse del computer erano il 18 per
        cento del giorno, e questi conti più della metà. I numeri sono gli stessi, nello stesso ordine di
        somma, punto 1.3 del progetto della tappa 12. Fuori dalle mosse del computer si calcolano ogni
        volta. Dalla decisione 4 di Gabriele del 14 ottobre 2026 ciascuno dei due si calcola soltanto
        quando serve: con la stessa chiave, niente nelle mosse li cambia, e calcolati prima o dopo sono
        gli stessi. Lo sponsor, che passa per il valore di tutta la rosa, molte polisportive non lo
        chiedono più.
        """
        memoria = self._conti_del_giorno
        if memoria is None:
            return calcolo(poli)
        # Dalla tappa 13 anche lo staff, che il computer assume mentre muove e che entra nel monte stipendi.
        chiave = (poli.nome, tuple(poli.tesserati), poli.gloria, tuple(poli.staff))
        conti = memoria.get(chiave)
        if conti is None:
            conti = memoria[chiave] = [None, None]
        if conti[posto] is None:
            conti[posto] = calcolo(poli)
        return conti[posto]

    def _sponsor_memorizzato(self, poli):
        """Lo sponsor della memoria di _conto_memorizzato."""
        return self._conto_memorizzato(poli, 0, self.sponsor)

    def _monte_memorizzato(self, poli):
        """Il monte stipendi della memoria di _conto_memorizzato."""
        return self._conto_memorizzato(poli, 1, self.monte_stipendi)

    def paga(self, poli, g, importo):
        """
        L'utente paga al tesserato una parte dei suoi arretrati, che escono dalla cassa: ricevere
        soldi gli rende pazienza, un mese per ogni stipendio. ValueError se non si può.
        """
        importo = int(importo)
        if g.id not in poli.tesserati:
            raise ValueError(f"{nome_completo(g)} non è {accorda(g.sesso, 'tesserato')} con {poli.nome}.")
        if not 0 < importo <= g.arretrati:
            raise ValueError(f"{nome_completo(g)} aspetta {scritta_in_euro(g.arretrati)}: si paga da 1 euro fino a quella cifra.")
        if importo > poli.cassa:
            raise ValueError(f"La cassa di {poli.nome} ha {scritta_in_euro(poli.cassa)}.")
        self._paga_arretrati(poli, g, importo)
        self.annota(g, f"Riceve da {poli.nome} {scritta_in_euro(importo)} di stipendi arretrati.")

    @staticmethod
    def _paga_arretrati(poli, g, importo):
        poli.cassa -= importo
        poli.conti_del_mese["arretrati"] += importo
        g.pazienza = min(100., g.pazienza + importo * pazienza_per_euro(g))
        g.arretrati -= importo

    def metti_in_vendita(self, poli, g, prezzo):
        """Mette in vendita un tesserato al prezzo dato, o glielo cambia; ValueError se non si può."""
        prezzo = int(prezzo)
        if g.id not in poli.tesserati:
            raise ValueError(f"{nome_completo(g)} non è {accorda(g.sesso, 'tesserato')} con {poli.nome}.")
        if prezzo <= 0:
            raise ValueError("Il prezzo deve essere di almeno 1 euro.")
        poli.in_vendita[g.id] = prezzo
        self.annota(poli, f"Mette in vendita {nome_completo(g)} a {scritta_in_euro(prezzo)}.")
        self.annota(g, f"{accorda(g.sesso, 'Messo')} in vendita da {poli.nome} a {scritta_in_euro(prezzo)}.")

    def togli_dalla_vendita(self, poli, g):
        if poli.in_vendita.pop(g.id, None) is None:
            raise ValueError(f"{nome_completo(g)} non è in vendita.")
        self.annota(poli, f"Toglie {nome_completo(g)} dalla vendita.")

    def venditore(self, g):
        """La polisportiva che ha in vendita il giocatore, oppure None."""
        poli = self.polisportive.get(g.appartenenza)
        return poli if poli is not None and g.id in poli.in_vendita else None

    def problema_acquisto(self, poli, g):
        """Perché la polisportiva non può comprare il giocatore, oppure None se può."""
        venditore = self.venditore(g)
        if venditore is None:
            return f"{nome_completo(g)} non è in vendita."
        if venditore is poli:
            return f"{nome_completo(g)} è già di {poli.nome}."
        if self.mosse_rimaste(poli) <= 0:
            return self._senza_mosse(poli)
        if len(poli.tesserati) >= poli.maxtesserati:
            return f"{poli.nome} ha già {poli.maxtesserati} tesserati, il massimo."
        prezzo = venditore.in_vendita[g.id]
        if prezzo > poli.cassa:
            return f"Costa {scritta_in_euro(prezzo)}, e la cassa di {poli.nome} ne ha {scritta_in_euro(poli.cassa)}."
        return None

    def acquista(self, poli, g):
        """L'utente compra un giocatore in vendita al prezzo chiesto: usa una mossa. Restituisce il prezzo; ValueError se non si può."""
        problema = self.problema_acquisto(poli, g)
        if problema:
            raise ValueError(problema)
        venditore = self.venditore(g)
        prezzo = venditore.in_vendita[g.id]
        self._usa_mossa(poli)
        self._vendi(venditore, poli, g, prezzo)
        return prezzo

    def soglia_di_vendita(self, poli, g):
        """
        Quanto vuole una polisportiva del computer per lasciar andare un suo tesserato che non ha
        messo in vendita, decisione D23: il valore di mercato, che sale fino a metà in più per il
        più forte della rosa. La cifra resta nascosta all'utente, che la deve indovinare.
        """
        rosa = self._rosa(poli)
        if len(rosa) <= 1:
            posizione = 1.
        else:
            posizione = sum(1 for altro in rosa if altro.indice_collettivo_valore < g.indice_collettivo_valore) / (len(rosa) - 1)
        return arrotonda(valore_di_mercato(g, self.datetime_corrente_simulazione) * (1 + IMPORTANZA_MASSIMA * posizione), 100)

    def posizione_in_rosa(self, g):
        """Il posto del giocatore nella sua rosa, dal più forte, e quanti sono: 1 e 15 per il più forte di quindici."""
        rosa = self._rosa(self.polisportive[g.appartenenza])
        return 1 + sum(1 for altro in rosa if altro.indice_collettivo_valore > g.indice_collettivo_valore), len(rosa)

    def problema_offerta_d_acquisto(self, compratore, g, importo=None):
        """Perché la polisportiva non può offrire la cifra per il tesserato del computer, oppure None se può."""
        venditore = self.polisportive.get(g.appartenenza)
        if venditore is None or not venditore.is_cpu_controlled:
            return f"{nome_completo(g)} non è {accorda(g.sesso, 'tesserato')} con una polisportiva del computer."
        if self.mosse_rimaste(compratore) <= 0:
            return self._senza_mosse(compratore)
        if len(compratore.tesserati) >= compratore.maxtesserati:
            return f"{compratore.nome} ha già {compratore.maxtesserati} tesserati, il massimo."
        if importo is not None and importo <= 0:
            return "L'offerta deve essere di almeno 1 euro."
        if importo is not None and importo > compratore.cassa:
            return f"La cassa di {compratore.nome} ha {scritta_in_euro(compratore.cassa)}: non bastano per offrirne {scritta_in_euro(importo)}."
        return None

    def offerta_d_acquisto(self, compratore, g, importo):
        """
        L'utente offre una cifra alla polisportiva del computer per un suo tesserato: usa una mossa,
        e se la cifra arriva alla soglia di vendita il giocatore passa al compratore. Restituisce
        vero se l'offerta è stata accettata; ValueError se non si può fare.
        """
        importo = int(importo)
        problema = self.problema_offerta_d_acquisto(compratore, g, importo)
        if problema:
            raise ValueError(problema)
        venditore = self.polisportive[g.appartenenza]
        self._usa_mossa(compratore)
        if importo < self.soglia_di_vendita(venditore, g):
            self.annota(compratore, f"Offre {scritta_in_euro(importo)} a {venditore.nome} per {nome_completo(g)}: offerta rifiutata.")
            return False
        self._vendi(venditore, compratore, g, importo)
        return True

    def _vendi(self, venditore, compratore, g, prezzo, data=None):
        """
        Il passaggio di un giocatore da una polisportiva all'altra: il compratore paga, il venditore
        incassa e dal prezzo salda gli arretrati che il giocatore aspettava.
        """
        saldati = min(g.arretrati, prezzo)
        compratore.cassa -= prezzo
        compratore.conti_del_mese["acquisti"] += prezzo
        venditore.cassa += prezzo - saldati
        venditore.conti_del_mese["vendite"] += prezzo
        venditore.conti_del_mese["arretrati"] += saldati
        self._lascia(venditore, g)
        self._entra(compratore, g, data)
        cifra = scritta_in_euro(prezzo)
        self.annota(g, f"{accorda(g.sesso, 'Venduto')} da {venditore.nome} a {compratore.nome} per {cifra}.", data)
        self.annota(venditore, f"Venduto {nome_completo(g)} a {compratore.nome} per {cifra}.", data)
        self.annota(compratore, f"Comprato {nome_completo(g)} da {venditore.nome} per {cifra}.", data)

    def problema_svincolo(self, poli, g):
        """Perché la polisportiva non può svincolare il tesserato, oppure None: dalla tappa 11 anche la cassa che non basta per la buonuscita."""
        if g.id not in poli.tesserati:
            return f"{nome_completo(g)} non è {accorda(g.sesso, 'tesserato')} con {poli.nome}."
        if self.mosse_rimaste(poli) <= 0:
            return self._senza_mosse(poli)
        buonuscita = contratti.buonuscita(g, self.datetime_corrente_simulazione)
        if buonuscita > poli.cassa:
            return f"Svincolare {nome_completo(g)} costa una buonuscita di {scritta_in_euro(buonuscita)}, e la cassa di {poli.nome} ne ha {scritta_in_euro(poli.cassa)}."
        return None

    def _paga_buonuscita(self, poli, g, data=None):
        """La buonuscita di uno svincolo a contratto in corso esce dalla cassa; restituisce quanto."""
        buonuscita = contratti.buonuscita(g, data or self.datetime_corrente_simulazione)
        poli.cassa -= buonuscita
        poli.conti_del_mese["buonuscite"] += buonuscita
        return buonuscita

    def svincola(self, poli, g):
        """
        L'utente svincola un suo tesserato, che torna libero: usa una mossa, e dalla tappa 11 paga la
        buonuscita, metà degli stipendi che restano del contratto. Restituisce la buonuscita;
        ValueError se non si può.
        """
        problema = self.problema_svincolo(poli, g)
        if problema:
            raise ValueError(problema)
        self._usa_mossa(poli)
        buonuscita = self._paga_buonuscita(poli, g)
        self._lascia(poli, g)
        con = f", con una buonuscita di {scritta_in_euro(buonuscita)}" if buonuscita else ""
        self.annota(g, f"{accorda(g.sesso, 'Svincolato')} da {poli.nome}{con}.")
        self.annota(poli, f"Svincolato {nome_completo(g)}{con}.")
        return buonuscita

    # I rinnovi dell'utente, a trattativa.

    def problema_rinnovo(self, poli, g, stipendio_offerto=None, mesi=None):
        """Perché la polisportiva non può proporre oggi il rinnovo al tesserato, con quello stipendio e quella durata; None se può."""
        oggi = self.datetime_corrente_simulazione
        if g.id not in poli.tesserati:
            return f"{nome_completo(g)} non è {accorda(g.sesso, 'tesserato')} con {poli.nome}."
        if not contratti.ha_contratto(g):
            return f"{nome_completo(g)} non ha un contratto da rinnovare."
        if contratti.ha_rinnovo(g):
            return (f"{nome_completo(g)} ha già rinnovato: dal {data_breve(g.contratto_scadenza)} prenderà {scritta_in_euro(g.rinnovo_stipendio)} al mese, "
                    f"fino al {data_breve(g.rinnovo_scadenza)}.")
        if not contratti.in_finestra(g, oggi):
            return (f"Il contratto di {nome_completo(g)} scade il {data_breve(g.contratto_scadenza)}: il rinnovo si può proporre "
                    f"dal {data_breve(contratti.inizio_finestra(g))}.")
        if not contratti.puo_trattare(g):
            return f"{nome_completo(g)} ha già rifiutato tre proposte e non tratta più: il contratto finirà il {data_breve(g.contratto_scadenza)}."
        if g.ultima_trattativa is not None and g.ultima_trattativa.date() == oggi.date():
            return f"Oggi hai già fatto una proposta a {nome_completo(g)}: se ne fa al massimo una al giorno."
        if stipendio_offerto is not None and stipendio_offerto < STIPENDIO_MINIMO:
            return f"Lo stipendio deve essere di almeno {scritta_in_euro(STIPENDIO_MINIMO)} al mese."
        if mesi is not None and not MESI_CONTRATTO_MIN <= mesi <= MESI_CONTRATTO_MAX:
            return f"La durata va da {MESI_CONTRATTO_MIN} a {MESI_CONTRATTO_MAX} mesi."
        return None

    def rinnova(self, poli, g, stipendio_offerto, mesi):
        """
        La proposta di rinnovo dell'utente: il giocatore accetta con la probabilità del rinnovo.
        Se accetta, il contratto nuovo parte alla scadenza di quello in corso, con lo stipendio
        offerto. Comunque vada, la proposta si conta, e oggi non se ne fanno altre. Non costa mosse
        di mercato. Restituisce l'esito, la probabilità e la richiesta del giocatore per quei mesi;
        ValueError se la proposta non si può fare.
        """
        stipendio_offerto, mesi = int(stipendio_offerto), int(mesi)
        problema = self.problema_rinnovo(poli, g, stipendio_offerto, mesi)
        if problema:
            raise ValueError(problema)
        oggi = self.datetime_corrente_simulazione
        richiesta = contratti.richiesta_rinnovo(g, poli, mesi)
        probabilita = contratti.probabilita_rinnovo(g, poli, stipendio_offerto, mesi)
        g.proposte_rinnovo += 1
        g.ultima_trattativa = oggi
        accetta = caso(probabilita)
        if accetta:
            contratti.concorda_rinnovo(g, stipendio_offerto, mesi)
            self._annota_rinnovo(poli, g)
        else:
            cifra = f"{scritta_in_euro(stipendio_offerto)} al mese per {mesi} mesi"
            self.annota(g, f"Rifiuta il rinnovo con {poli.nome} a {cifra}.")
            self.annota(poli, f"{nome_completo(g)} rifiuta il rinnovo a {cifra}.")
            if not contratti.puo_trattare(g):
                self._annota_chiusura(poli, g)
        return accetta, probabilita, richiesta

    def _annota_rinnovo(self, poli, g, data=None):
        cifra = f"{scritta_in_euro(g.rinnovo_stipendio)} al mese, dal {data_breve(g.contratto_scadenza)} al {data_breve(g.rinnovo_scadenza)}"
        self.annota(g, f"Rinnova il contratto con {poli.nome}: {cifra}.", data)
        self.annota(poli, f"{nome_completo(g)} rinnova il contratto: {cifra}.", data)

    def _annota_chiusura(self, poli, g, data=None):
        testo = f"Non vuole più trattare: il contratto con {poli.nome} finirà il {data_breve(g.contratto_scadenza)}."
        self.annota(g, testo, data)
        self.annota(poli, f"{nome_completo(g)}. {testo}", data)

    def chiudi_polisportiva(self, poli):
        """Chiude per sempre una polisportiva: i tesserati tornano liberi. Restituisce quanti sono."""
        liberati = 0
        for gid in list(poli.tesserati):
            g = self.giocatori.get(gid)
            if g is not None:
                self._lascia(poli, g)
                self.annota(g, f"Torna {accorda(g.sesso, 'libero')}: {poli.nome} ha chiuso.")
                liberati += 1
        poli.tesserati.clear()
        poli.indicecollettivotesserati = 0.
        self._congeda_lo_staff(poli, self.datetime_corrente_simulazione)
        self._fattori_staff.pop(poli.nome, None)
        del self.polisportive[poli.nome]
        if self.miapolisportiva_attiva is poli:
            self.miapolisportiva_attiva = None
        return liberati

    def nuovo_id(self):
        """
        L'identificativo di un giocatore nuovo. Il contatore sale soltanto, così il numero di chi
        esce di scena non tocca mai a un altro, e il registro delle vecchie glorie resta univoco:
        problema P5 del piano, risolto il 2026-10-06 con la tappa 3.
        """
        nuovo = max(self.prossimo_id, max(self.giocatori, default=0) + 1)
        self.prossimo_id = nuovo + 1
        return nuovo

    def descrivi_impegno(self, g):
        """
        Che cosa ha già giocato oggi il giocatore, a parole, per la regola di un impegno al giorno della
        tappa 12, D32: il torneo, una sfida, oppure un'amichevole.
        """
        oggi = self.datetime_corrente_simulazione
        return calendario.descrivi(self.calendario, g, oggi) or sfide.descrivi(self, g, oggi) or "un'amichevole"

    def annota(self, soggetto, testo, data=None):
        """Una voce nel diario di un giocatore o di una polisportiva, con la data simulata, di oggi se non è data."""
        soggetto.annota(data or self.datetime_corrente_simulazione, testo)

    def sfoltisci_diari(self):
        """
        Toglie dai diari le voci più vecchie dei giorni simulati da conservare; restituisce quante ne ha tolte.
        Dalla tappa 13 anche quelli degli allenatori, con i giorni dei giocatori: la revisione del 22 ottobre
        2026 ha visto che crescevano senza limite, migliaia di allenatori con tutti i loro contratti.
        """
        tolte = 0
        for chiave, soggetti in (("giocatori", self.giocatori.values()), ("polisportive", self.polisportive.values()), ("giocatori", self.allenatori.values())):
            giorni = self.conservazione_diari.get(chiave, 0)
            if giorni <= 0:
                continue
            limite = self.datetime_corrente_simulazione - datetime.timedelta(days=giorni)
            for soggetto in soggetti:
                prima = len(soggetto.diario)
                soggetto.diario[:] = [voce for voce in soggetto.diario if voce["data"] >= limite]
                tolte += prima - len(soggetto.diario)
        return tolte

    # Nascite e polisportive del computer.

    def crea_giocatori_casuali(self, quanti, dt_creaz, annuncia=True):
        """Crea il numero indicato di giocatori nuovi e li annota fra i nuovi della sessione."""
        if quanti <= 0:
            return
        if annuncia:
            self.notifica(f" -> Generazione {quanti} nuovi giocatori...")
        for _ in range(quanti):
            new_id = self.nuovo_id()
            is_ipo = caso(PROBABILITA_IPOVEDENTE_CREAZIONE)
            self.giocatori[new_id] = Giocatore(id_giocatore=new_id, datetime_creazione_sim=dt_creaz, ipovedente=is_ipo)
            self.nuovi_giocatori_sessione.append(new_id)
            self._fattori_del_giocatore(self.giocatori[new_id])
        if annuncia:
            self.notifica(f" -> Creati {quanti} nuovi giocatori.")

    def crea_polisportiva_cpu(self, dt_creaz):
        """
        Fonda una polisportiva del computer con un nome nuovo; ne restituisce il nome, o None. Il
        numero è il primo che nessun nome usa all'inizio, seguito da uno spazio, maiuscole a parte.
        Dalla tappa 12 le prime parole dei nomi si raccolgono una volta sola: prima ogni numero
        provato scorreva tutti i nomi, e con le 1.240 polisportive del mondo a regime una fondazione
        costava più di mezzo secondo. Il numero scelto è lo stesso di prima.
        """
        suff = 1
        base = "PoliTeam"
        usati = set()
        for n in self.polisportive:
            testa, spazio, _resto = n.casefold().partition(" ")
            if spazio:
                usati.add(testa)
        while True:
            if f"{base}{suff:02d}".casefold() not in usati:
                break
            suff += 1
            if suff > 9999:
                self.notifica("ATT: Suffix CPU>9999.")
                return None
        p1 = genera_nome_casuale(["cvcv"], 'x').capitalize()
        p2 = genera_nome_casuale(["cvcv"], 'x').capitalize()
        nome = f"{base}{suff:02d} {p1}-{p2}"
        if self.trova_polisportiva(nome) is not None:
            self.notifica(f"ATT: Collisione nome CPU '{nome}'.")
            return None
        self.polisportive[nome] = Polisportiva(nome=nome, password=None, datetime_creazione_sim=dt_creaz, is_cpu_controlled=True)
        return nome

    def _chiudi_polisportiva_cpu(self, nome_p, dt_chiusura):
        poli = self.polisportive.get(nome_p)
        if not poli or not poli.is_cpu_controlled:
            return False
        eta_str = formatta_eta_sim(int((dt_chiusura - poli.datetime_creazione_sim).total_seconds() / (24 * 3600)))
        self.notifica(f"** Evento ({dt_chiusura:%Y-%m-%d %H:%M}): Chiusura Poli CPU '{nome_p}' (Età: {eta_str}, G:{poli.gloria}, T:{len(poli.tesserati)}) **")
        n_lib = 0
        for gid in list(poli.tesserati):
            if gid in self.giocatori:
                g = self.giocatori[gid]
                self._lascia(poli, g)
                self.annota(g, f"Torna {accorda(g.sesso, 'libero')}: {poli.nome} ha chiuso.", dt_chiusura)
                n_lib += 1
            if gid in poli.tesserati:
                poli.tesserati.remove(gid)
        self._congeda_lo_staff(poli, dt_chiusura)
        self._fattori_staff.pop(nome_p, None)
        del self.polisportive[nome_p]
        self.notifica(f" --> Chiusa. {n_lib} liberati.")
        return True

    def _controlla_chiusura_poli_cpu(self, poli, dt_corr):
        """Una polisportiva del computer con poca gloria o pochi tesserati può chiudere, dopo un anno e mezzo di vita."""
        if not isinstance(poli.datetime_creazione_sim, datetime.datetime) or ANNO_SIMULAZIONE_GIORNI <= 0:
            return False
        anni_sim = (dt_corr - poli.datetime_creazione_sim).total_seconds() / (24 * 3600) / ANNO_SIMULAZIONE_GIORNI
        if anni_sim < ETA_MINIMA_CHIUSURA_CPU_ANNI:
            return False
        g_bassa = poli.gloria < SOGLIA_GLORIA_BASSA_CHIUSURA
        p_tess = len(poli.tesserati) < SOGLIA_MINIMA_TESSERATI_CHIUSURA
        if not (g_bassa or p_tess):
            return False
        prob = PROB_CHIUSURA_BASE_GIORNALIERA
        if g_bassa:
            norm = SOGLIA_GLORIA_BASSA_CHIUSURA or 1
            prob += max(0., norm - poli.gloria) / norm * FATTORE_PROB_GLORIA
        if p_tess:
            norm = SOGLIA_MINIMA_TESSERATI_CHIUSURA or 1
            prob += max(0., norm - len(poli.tesserati)) / norm * FATTORE_PROB_TESSERATI
        if caso(min(prob, MAX_PROB_CHIUSURA_GIORNALIERA)):
            return self._chiudi_polisportiva_cpu(poli.nome, dt_corr)
        return False

    def _esegui_logica_cpu_polisportive(self, data=None):
        """
        Le mosse del giorno delle polisportive del computer, secondo le decisioni D19 e D22.
        Scelgono per prime quelle con più gloria. Ciascuna prova a tesserare il libero più forte
        che si può permettere: lo stipendio deve stare nei suoi conti, e l'ingaggio, che offre un
        poco sopra la richiesta, nella cassa, tenendo da parte un mese di stipendi; ogni candidato
        lo prova una volta sola al giorno. A rosa piena ogni tanto prova un libero più forte del
        tesserato che vale meno, che se accetta gli prende il posto. Poi ognuna può comprare uno dei
        giocatori in vendita, se le conviene. Restituisce quanti ne hanno tesserati, svincolati e comprati.
        Dalla tappa 11, decisione 21 di Gabriele, il computer lascia stare i liberi infortunati finché
        non guariscono, mentre l'utente può tesserarli subito: quando il mondo sarà affollato, chi
        cerca un libero ne trova ancora qualcuno. Il filtro sta qui, sull'elenco da cui pescano sia
        le mosse a rosa incompleta sia lo scambio a rosa piena; gli acquisti dalle altre polisportive
        non c'entrano, perché non prendono liberi.
        Dalla tappa 12, mentre il computer muove, sponsor e monte stipendi di ogni polisportiva vivono
        in una memoria che si svuota alla fine: vedi _conto_memorizzato.
        """
        self._conti_del_giorno = {}
        try:
            return self._mosse_del_computer(data)
        finally:
            self._conti_del_giorno = None

    def _mosse_del_computer(self, data):
        """Il corpo di _esegui_logica_cpu_polisportive, con la memoria dei conti già pronta."""
        liberi = [g for g in self.trova_giocatori_liberi_ordinati().values() if not g.infortunato]
        stipendi = [stipendio(g) for g in liberi]
        vetrina = _Vetrina(stipendi)
        tesserati = svincolati = comprati = 0
        cpu = sorted((p for p in self.polisportive.values() if p.is_cpu_controlled), key=lambda p: p.gloria, reverse=True)
        for poli in cpu:
            monte = self._monte_memorizzato(poli)
            # Il posto da cui riprende la ricerca: i liberi prima di lui sono già stati provati o sono troppo cari.
            prossimo = 0
            scartati = 0
            while self.mosse_rimaste(poli) > 0 and len(poli.tesserati) < poli.maxtesserati and scartati < SCARTI_MASSIMI_CPU:
                spendibile = poli.cassa - monte * MESI_DI_RISERVA_CPU
                posto = vetrina.primo(self._stipendio_massimo(poli, monte, spendibile), prossimo)
                if posto is None:
                    break
                prossimo = posto + 1
                g = liberi[posto]
                richiesta = ingaggio_richiesto(g, poli)
                offerta = arrotonda(richiesta * RIALZO_CPU)
                if offerta > spendibile:
                    scartati += 1
                    continue
                self._usa_mossa(poli)
                if caso(probabilita_accettazione(offerta, richiesta)):
                    self._paga_ingaggio(poli, offerta)
                    self._tessera(poli, g, data, offerta)
                    vetrina.togli(posto)
                    monte += stipendi[posto]
                    tesserati += 1
            if self.mosse_rimaste(poli) > 0 and len(poli.tesserati) >= poli.maxtesserati and caso(PROB_SCAMBIO_CPU_GIORNALIERA):
                if self._scambio(poli, liberi, vetrina, prossimo, monte, data):
                    tesserati += 1
                    svincolati += 1
        # Dalla tappa 13 lo staff, prima del mercato delle vendite: un posto vuoto si riempie col migliore alla portata.
        self._staff_del_computer(cpu, data or self.datetime_corrente_simulazione)
        mercato = _Mercato(self._vendibili(data or self.datetime_corrente_simulazione))
        for poli in cpu:
            if self._compra_dal_mercato(poli, data, mercato):
                comprati += 1
        return tesserati, svincolati, comprati

    def _stipendio_massimo(self, poli, monte, spendibile):
        """
        Lo stipendio più alto che una polisportiva del computer può aggiungere: deve stare nello
        sponsor più una parte della cassa, e con la cassa piena nel suo premio, decisione 1 di Gabriele
        del 14 ottobre 2026; e l'ingaggio più basso possibile deve stare nella cassa.
        """
        nei_conti = spesa_mensile_cpu(self._sponsor_memorizzato(poli), poli.cassa) - monte
        nella_cassa = spendibile / (MESI_DI_INGAGGIO * REPUTAZIONE_MINIMA * RIALZO_CPU)
        return min(nei_conti, nella_cassa)

    def _rosa(self, poli):
        giocatori = self.giocatori
        morti = self._ids_morti_processati_sessione
        return [g for gid in poli.tesserati if (g := giocatori.get(gid)) is not None and gid not in morti]

    def _scambio(self, poli, liberi, vetrina, prossimo, monte, data):
        """Una polisportiva a rosa piena prova il libero più forte che si può permettere; vero se l'ha preso al posto del tesserato che vale meno."""
        rosa = self._rosa(poli)
        if not rosa:
            return False
        debole = min(rosa, key=lambda g: g.indice_collettivo_valore)
        buonuscita = contratti.buonuscita(debole, data or self.datetime_corrente_simulazione)
        spendibile = poli.cassa - monte * MESI_DI_RISERVA_CPU - buonuscita
        posto = vetrina.primo(self._stipendio_massimo(poli, monte - stipendio_pagato(debole), spendibile), prossimo)
        if posto is None:
            return False
        nuovo = liberi[posto]
        if nuovo.indice_collettivo_valore <= debole.indice_collettivo_valore:
            return False
        richiesta = ingaggio_richiesto(nuovo, poli)
        offerta = arrotonda(richiesta * RIALZO_CPU)
        if offerta > spendibile:
            return False
        self._usa_mossa(poli)
        if not caso(probabilita_accettazione(offerta, richiesta)):
            return False
        self._paga_buonuscita(poli, debole, data)
        self._lascia(poli, debole)
        self._paga_ingaggio(poli, offerta)
        self._entra(poli, nuovo, data)
        vetrina.togli(posto)
        self.annota(nuovo, f"{accorda(nuovo.sesso, 'Tesserato')} con {poli.nome}, con un ingaggio di {scritta_in_euro(offerta)}.", data)
        self.annota(debole, f"{accorda(debole.sesso, 'Svincolato')} da {poli.nome}, che al suo posto ha tesserato {nome_completo(nuovo)}.", data)
        self.annota(poli, f"Tesserato {nome_completo(nuovo)} al posto di {nome_completo(debole)}, che torna {accorda(debole.sesso, 'libero')}.", data)
        return True

    def _vendibili(self, oggi):
        """
        I giocatori in vendita del giorno, una volta per tutte le polisportive del computer: chi è,
        chi lo vende, il prezzo, il prezzo più alto che il computer paga, cioè il valore di mercato
        del giorno col suo rialzo, e lo stipendio che chiederà firmando. Nell'ordine in cui le
        polisportive e le loro vendite si scorrono, così la scelta resta quella di prima: dalla tappa
        11 il valore di mercato dipende dalla scadenza, e rifarne il conto per ogni polisportiva
        costava troppo.
        """
        righe = []
        for venditore in self.polisportive.values():
            for gid, prezzo in venditore.in_vendita.items():
                g = self.giocatori.get(gid)
                # Il ritirato non si compra: serve ai salvataggi in cui un morto era rimasto in vendita.
                if g is not None and not g.ritirato:
                    righe.append((g, venditore, prezzo, valore_di_mercato(g, oggi) * RIALZO_CPU, stipendio(g)))
        return righe

    def _compra_dal_mercato(self, poli, data, mercato=None):
        """
        Una polisportiva del computer compra il più forte dei giocatori in vendita, se il prezzo non
        supera di molto il suo valore di mercato e se ci sta nei conti; a rosa piena solo se è più
        forte del tesserato che vale meno, che lascia libero. Al massimo un acquisto al giorno. Dalla
        tappa 12 la ricerca la fa il mercato del giorno, _Mercato, costruito una volta per tutte le
        polisportive del computer; senza, se ne costruisce uno. Con la cassa piena, decisione 1 di
        Gabriele del 14 ottobre 2026, il premio della cassa piena alza lo stipendio che si permette, non
        il prezzo: quello resta entro il valore di mercato col rialzo del computer.
        """
        if self.mosse_rimaste(poli) <= 0:
            return False
        rosa = self._rosa(poli)
        piena = len(poli.tesserati) >= poli.maxtesserati
        if piena and not rosa:
            return False
        debole = min(rosa, key=lambda g: g.indice_collettivo_valore) if piena else None
        oggi = data or self.datetime_corrente_simulazione
        if mercato is None:
            mercato = _Mercato(self._vendibili(oggi))
        monte = self._monte_memorizzato(poli) - (stipendio_pagato(debole) if debole else 0)
        buonuscita = contratti.buonuscita(debole, oggi) if debole else 0
        spendibile = poli.cassa - monte * MESI_DI_RISERVA_CPU - buonuscita
        # Lo sponsor, il conto più caro, serve soltanto se il mercato ha qualcosa alla portata della cassa.
        if mercato.chiuso(spendibile, debole):
            return False
        massimo = spesa_mensile_cpu(self._sponsor_memorizzato(poli), poli.cassa) - monte
        scelta = mercato.scelta(poli, spendibile, massimo, debole)
        if scelta is None:
            return False
        g, venditore, prezzo = scelta
        self._usa_mossa(poli)
        if debole is not None:
            self._paga_buonuscita(poli, debole, oggi)
            self._lascia(poli, debole)
            self.annota(debole, f"{accorda(debole.sesso, 'Svincolato')} da {poli.nome}, che al suo posto ha comprato {nome_completo(g)}.", data)
        self._vendi(venditore, poli, g, prezzo, data)
        return True

    # I conti del mese.

    def _primo_del_mese(self, data, rapporto):
        """
        I conti del primo del mese, decisione D22. Chi è in una polisportiva guadagna fedeltà ed
        esperienza. Ogni polisportiva incassa lo sponsor e paga gli stipendi: se la cassa basta,
        paga tutto, arretrati compresi; altrimenti gli stipendi del mese diventano arretrati, e chi
        li aspetta perde un mese di pazienza. Per l'utente, che decide lui a chi dare i soldi che
        ci sono, il mondo non paga nessuno; il computer paga per primi i meno pazienti, e mette in
        vendita il suo giocatore più caro. Chi ha finito la pazienza se ne va, salvo le bandiere.
        Dalla tappa 12, decisione 4 di Gabriele del 14 ottobre 2026, lo sponsor di ogni polisportiva si
        ricorda finché non cambia la rosa, fino alla fine dei contratti del mese: vedi _sponsor_del_mese.
        """
        self._sponsor_ricordati = {}
        try:
            self._conti_del_primo(data, rapporto)
        finally:
            self._sponsor_ricordati = None

    def _sponsor_del_mese(self, poli, rosa=None):
        """
        Lo sponsor del mese della polisportiva con la sua rosa, quella di _rosa, che si può dare già fatta.
        Durante i conti del primo del mese si calcola una volta per polisportiva e si ricalcola soltanto
        quando cambia la rosa, con una memoria indicizzata dal nome, dai tesserati nel loro ordine e dalla
        gloria: lì niente cambia il valore dei giocatori, né la gloria, che si ricalcola a fine giorno.
        Prima ogni rinnovo provato dal computer ricalcolava lo sponsor di tutta la rosa, e il primo del
        mese era il giorno più lento. Fuori dai conti del primo del mese si calcola ogni volta.
        """
        memoria = self._sponsor_ricordati
        if memoria is None:
            return sponsor_mensile(poli, self._rosa(poli) if rosa is None else rosa)
        chiave = (poli.nome, tuple(poli.tesserati), poli.gloria)
        sponsor = memoria.get(chiave)
        if sponsor is None:
            sponsor = memoria[chiave] = sponsor_mensile(poli, self._rosa(poli) if rosa is None else rosa)
        return sponsor

    def _conti_del_primo(self, data, rapporto):
        """Il corpo di _primo_del_mese, con la memoria degli sponsor già pronta."""
        rapporto["mesi"] += 1
        for poli in list(self.polisportive.values()):
            rosa = self._rosa(poli)
            self._fedelta(poli, rosa, data, rapporto)
            sponsor = self._sponsor_del_mese(poli, rosa)
            poli.cassa += sponsor
            poli.conti_del_mese["sponsor"] += sponsor
            dovuti = {g.id: stipendio_pagato(g) for g in rosa}
            if sum(dovuti.values()) + sum(g.arretrati for g in rosa) <= poli.cassa:
                for g in rosa:
                    if g.arretrati:
                        self._paga_arretrati(poli, g, g.arretrati)
                    poli.cassa -= dovuti[g.id]
                    poli.conti_del_mese["stipendi"] += dovuti[g.id]
            else:
                for g in rosa:
                    g.arretrati += dovuti[g.id]
                    if not bandiera_attiva(g):
                        g.pazienza = max(0., g.pazienza - 100 / mesi_di_pazienza(g))
                if poli.is_cpu_controlled:
                    self._paga_i_meno_pazienti(poli, rosa)
                else:
                    rapporto["tuoi_non_pagati"] += sum(1 for g in rosa if g.arretrati)
                for g in rosa:
                    if g.arretrati and g.pazienza <= 0 and not bandiera_attiva(g):
                        self._se_ne_va(poli, g, data, rapporto)
                if poli.is_cpu_controlled:
                    self._vende_il_piu_caro(poli, data)
            # Dalla tappa 13 lo stipendio dello staff, dopo quello dei tesserati.
            self._paga_lo_staff(poli, data, rapporto)
            poli.bilanci.insert(0, {"data": data, "cassa": poli.cassa, **poli.conti_del_mese})
            del poli.bilanci[BILANCI_CONSERVATI:]
            poli.conti_del_mese = conti_vuoti()
            # Dalla tappa 12 i mesi usciti dalla finestra della gloria lasciano il palmarès recente, e
            # arrivano due sfide da lanciare, fino a quattro.
            palmares.sfoltisci(poli, data)
            poli.sfide_da_lanciare = min(SFIDE_ACCUMULABILI, poli.sfide_da_lanciare + SFIDE_AL_MESE)
        self._contratti_del_mese(data, rapporto)
        # Dalla tappa 13 i contratti dello staff, dopo quelli dei tesserati.
        self._contratti_dello_staff(data, rapporto)

    # I contratti del mese, dopo gli stipendi: il mese appena finito si paga anche a chi scade oggi.

    def _contratti_del_mese(self, data, rapporto):
        """
        Il primo del mese, per ogni polisportiva e ogni tesserato: il contratto scaduto lascia il
        posto al rinnovo concordato, oppure il giocatore torna libero; il computer prova a rinnovare
        chi è nella finestra; all'utente il mondo ricorda chi entra nella finestra e chi entra
        nell'ultimo mese, con una voce nei due diari. Poi il computer riporta il prezzo dei suoi
        tesserati in vendita al valore di mercato del giorno, che con la scadenza scende.
        Dalla tappa 12, decisione 4 di Gabriele del 14 ottobre 2026, il giorno di oggi si prende una volta
        sola, e l'inizio della finestra si ricorda per scadenza: le scadenze sono pochi primi del mese, e
        la finestra di contratti.in_finestra si ricalcolava per ogni tesserato del computer.
        """
        oggi = data.date()
        inizi = {}
        for poli in list(self.polisportive.values()):
            for g in self._rosa(poli):
                if g.contratto_scadenza is None:
                    continue
                if g.contratto_scadenza.date() <= oggi:
                    if contratti.ha_rinnovo(g):
                        contratti.subentra_il_rinnovo(g)
                        self.annota(g, f"Comincia il contratto rinnovato con {poli.nome}: {scritta_in_euro(g.contratto_stipendio)} al mese fino al {data_breve(g.contratto_scadenza)}.", data)
                    else:
                        self._scade(poli, g, data, rapporto)
                    continue
                if contratti.ha_rinnovo(g) or not contratti.puo_trattare(g):
                    continue
                if poli.is_cpu_controlled:
                    # contratti.in_finestra, con l'inizio della finestra ricordato per le scadenze senza fuso.
                    scadenza = g.contratto_scadenza
                    inizio = inizi.get(scadenza) if scadenza.tzinfo is None else None
                    if inizio is None:
                        inizio = contratti.inizio_finestra(g).date()
                        if scadenza.tzinfo is None:
                            inizi[scadenza] = inizio
                    if inizio <= oggi < scadenza.date():
                        self._rinnovo_cpu(poli, g, data, rapporto)
                    continue
                mesi = contratti.mesi_interi(data, g.contratto_scadenza)
                if mesi == MESI_FINESTRA_RINNOVO:
                    testo = f"Il contratto scade il {data_breve(g.contratto_scadenza)}: da oggi si può rinnovare."
                elif mesi == 1:
                    testo = f"Ultimo mese di contratto: se non rinnovi, il {data_breve(g.contratto_scadenza)} torna {accorda(g.sesso, 'libero')}."
                else:
                    continue
                rapporto["tuoi_in_scadenza"] += 1
                self.annota(g, testo, data)
                self.annota(poli, f"{nome_completo(g)}. {testo}", data)
            if poli.is_cpu_controlled:
                for gid in list(poli.in_vendita):
                    g = self.giocatori.get(gid)
                    if g is not None and gid in poli.tesserati:
                        poli.in_vendita[gid] = max(1, valore_di_mercato(g, data))

    def _scade(self, poli, g, data, rapporto):
        """Il contratto è scaduto senza rinnovo: il giocatore torna libero, e nessuno incassa niente."""
        self._lascia(poli, g)
        self.annota(g, f"Il contratto con {poli.nome} è scaduto: torna {accorda(g.sesso, 'libero')}.", data)
        self.annota(poli, f"Il contratto di {nome_completo(g)} è scaduto: torna {accorda(g.sesso, 'libero')}.", data)
        rapporto["contratti_scaduti"] += 1
        if not poli.is_cpu_controlled:
            rapporto["tuoi_scaduti"] += 1

    def _rinnovo_cpu(self, poli, g, data, rapporto):
        """
        Il computer prova a rinnovare un tesserato nella finestra, una volta al mese: offre la
        richiesta per la durata che il giocatore propone, con il suo rialzo. Se il monte stipendi,
        con lo stipendio nuovo al posto del vecchio, non sta nello sponsor più una parte della
        cassa, e con la cassa piena il suo premio, decisione 1 di Gabriele del 14 ottobre 2026, non
        rinnova: mette il giocatore in vendita al valore di mercato e lo lascia scadere.
        Restituisce vero se il giocatore ha accettato.
        """
        mesi = contratti.durata_proposta(g)
        richiesta = contratti.richiesta_rinnovo(g, poli, mesi)
        offerta = arrotonda(richiesta * RIALZO_RINNOVO_CPU)
        monte = self.monte_stipendi(poli) - stipendio_pagato(g) + offerta
        if monte > spesa_mensile_cpu(self._sponsor_del_mese(poli), poli.cassa):
            if g.id not in poli.in_vendita:
                prezzo = max(1, valore_di_mercato(g, data))
                poli.in_vendita[g.id] = prezzo
                self.annota(poli, f"Mette in vendita {nome_completo(g)} a {scritta_in_euro(prezzo)}: il rinnovo costerebbe troppo.", data)
                self.annota(g, f"{accorda(g.sesso, 'Messo')} in vendita da {poli.nome} a {scritta_in_euro(prezzo)}.", data)
            return False
        g.proposte_rinnovo += 1
        g.ultima_trattativa = data
        # La richiesta è quella di sopra: proposte e trattativa non la cambiano.
        if not caso(contratti.probabilita_rinnovo(g, poli, offerta, mesi, richiesta)):
            return False
        contratti.concorda_rinnovo(g, offerta, mesi)
        self._annota_rinnovo(poli, g, data)
        rapporto["rinnovi_cpu"] += 1
        return True

    def _fedelta(self, poli, rosa, data, rapporto=None):
        """
        Un mese in più nel club: la fedeltà cresce, e una bandiera si accende quando arriva alla
        soglia. Dalla tappa 11 l'esperienza cresce ogni giorno, in _allenamento_del_giorno.
        """
        for g in rosa:
            self._aggiungi_fedelta(g, poli, FEDELTA_PER_MESE, data, rapporto)

    def _aggiungi_fedelta(self, g, poli, punti, data, rapporto=None):
        """
        La fedeltà del giocatore verso il suo club cresce dei punti dati, fino al massimo; una bandiera
        si accende quando arriva alla soglia. Serve al primo del mese e, dalla tappa 12, alle medaglie
        vinte col club e alle sfide vinte, D32.
        """
        prima = g.fedelta
        # Dalla tappa 13 lo staff fa crescere la fedeltà più o meno in fretta, in tutte le crescite, D33 risposte 12 e 26.
        g.fedelta = min(FEDELTA_MASSIMA, g.fedelta + punti * self.fattori_staff(poli)[2])
        if g.bandiera and prima < FEDELTA_BANDIERA <= g.fedelta:
            self.annota(g, f"Diventa una bandiera di {poli.nome}: giocherà per il club anche senza stipendio.", data)
            self.annota(poli, f"{nome_completo(g)} diventa una bandiera del club.", data)
            if rapporto is not None and not poli.is_cpu_controlled:
                rapporto["tue_bandiere"] += 1

    def _mantenimento_del_mese(self, data):
        """
        Il primo del mese, per tutti i giocatori vivi: il calo dei livelli alti e l'oblio
        dell'apprendista, per i giorni del mese appena finito. Per i ritirati anche il valore, col
        declino del mese, che il giro di ogni giorno non ricalcola più.
        """
        giorni = (contratti.primo_del_mese(data) - contratti.aggiungi_mesi(data, -1)).days
        morti = self._ids_morti_processati_sessione
        for gid, g in self.giocatori.items():
            if gid not in morti:
                if not mantenimento_del_mese(g, giorni) and g.ritirato:
                    g.aggiorna_icv()
                # Dalla tappa 13 la classe migliore della carriera, per chi è in attività dai 40 anni: prima sale quasi sempre.
                if not g.ritirato and g.eta >= ETA_CLASSE_MIGLIORE_GIORNI:
                    g.aggiorna_classe_migliore()

    def _allenamento_del_giorno(self, data, rapporto):
        """
        L'allenamento di un giorno simulato, per ogni giocatore vivo e non ritirato, decisione D31.
        Chi può giocare fa la seduta: il tesserato prende i punti della sua intensità, il libero la
        metà; chi si allena all'intensa può infortunarsi. La costanza recente segue l'attività del
        giorno: la costanza della seduta, quella dei liberi, zero per chi non si allena. L'esperienza
        cresce con l'età e, in polisportiva, col fattore del gruppo, calcolato una volta al giorno per
        polisportiva. I liberi e i tesserati del computer spendono da soli, secondo la loro indole,
        quando il portafoglio arriva alla soglia; la spesa non va nel diario. Chi ha speso si conta
        alla voce autoallenati del riepilogo.
        Dalla tappa 12, decisione 4 di Gabriele del 14 ottobre 2026, i punti della seduta di ogni
        intensità e l'esperienza del giorno di ogni polisportiva, che non cambiano nel giorno, si
        calcolano una volta sola, prima del giro dei giocatori, con gli stessi conti di esperienza.del_giorno.
        """
        morti = self._ids_morti_processati_sessione
        gruppi = {}
        for nome_club, poli in self.polisportive.items():
            fattore = esperienza.fattore_gruppo([g for g in self._rosa(poli) if not g.ritirato])
            gruppi[nome_club] = (poli, esperienza.quanto_del_giorno(True, fattore), poli.is_cpu_controlled)
        dell_eta = esperienza.quanto_del_giorno(False)
        massima = esperienza.ESPERIENZA_MASSIMA
        sedute = {nome: (PA_SEDUTA * riga["punti"], riga["costanza"], riga["infortuni_seduta"] > 0.0) for nome, riga in INTENSITA.items()}
        resto = 1.0 - DECADIMENTO_COSTANZA
        seduta_liberi = PA_SEDUTA * QUOTA_SEDUTA_LIBERI
        for gid, g in self.giocatori.items():
            if g.ritirato or gid in morti:
                continue
            club = gruppi.get(g.appartenenza)
            attivita = 0.0
            # Chi non è infortunato può giocare; per gli infortunati decide puo_giocare, per l'ambidestro col braccio fermo.
            if not g.infortunato or g.puo_giocare:
                if club is None:
                    g.punti_allenamento += seduta_liberi
                    attivita = COSTANZA_LIBERI
                else:
                    punti, attivita, a_rischio = sedute[g.intensita]
                    g.punti_allenamento += punti
                    if a_rischio and infortuni.infortunio_in_seduta(self, g, data):
                        rapporto["infortunati_in_seduta"] += 1
                        if not club[2]:
                            rapporto["tuoi_infortunati_in_seduta"] += 1
                            self.annota(club[0], f"{nome_completo(g)} si infortuna in allenamento.", data)
            g.costanza = g.costanza * DECADIMENTO_COSTANZA + resto * attivita
            g.esperienza = min(massima, g.esperienza + (dell_eta if club is None else club[1]))
            if g.punti_allenamento >= SOGLIA_SPESA_AUTONOMI and (club is None or club[2]) and allena_secondo_programma(g, programma=g.indole):
                rapporto["autoallenati"] += 1

    def _paga_i_meno_pazienti(self, poli, rosa):
        """Il computer, quando la cassa non basta, paga gli arretrati partendo da chi ha meno pazienza."""
        for g in sorted(rosa, key=lambda g: (bandiera_attiva(g), g.pazienza)):
            importo = min(g.arretrati, poli.cassa)
            if importo > 0:
                self._paga_arretrati(poli, g, importo)

    def _se_ne_va(self, poli, g, data, rapporto):
        """Un tesserato che ha finito la pazienza lascia la polisportiva, e i suoi arretrati con lui."""
        aspettava = scritta_in_euro(g.arretrati)
        self._lascia(poli, g)
        self.annota(g, f"Lascia {poli.nome}: aspettava {aspettava} di stipendi.", data)
        self.annota(poli, f"{nome_completo(g)} se ne va: aspettava {aspettava} di stipendi.", data)
        rapporto["partiti"] += 1
        if not poli.is_cpu_controlled:
            rapporto["tuoi_partiti"] += 1

    def _vende_il_piu_caro(self, poli, data):
        """Una polisportiva del computer che non riesce a pagare mette in vendita il suo tesserato più caro, al valore di mercato."""
        in_vendita = [g for g in self._rosa(poli) if g.id not in poli.in_vendita]
        if not in_vendita or not any(g.arretrati for g in self._rosa(poli)):
            return
        caro = max(in_vendita, key=stipendio_pagato)
        prezzo = max(1, valore_di_mercato(caro, data))
        poli.in_vendita[caro.id] = prezzo
        self.annota(poli, f"Mette in vendita {nome_completo(caro)} a {scritta_in_euro(prezzo)}.", data)
        self.annota(caro, f"{accorda(caro.sesso, 'Messo')} in vendita da {poli.nome} a {scritta_in_euro(prezzo)}.", data)

    def aggiorna_stato_polisportive(self, annuncia=True):
        """Ricalcola indice dei tesserati e gloria di tutte le polisportive."""
        if annuncia:
            self.notifica("Aggiornamento stato polisportive...")
        oggi = self.datetime_corrente_simulazione
        for p in self.polisportive.values():
            p.aggiorna_ict(self.giocatori, self._ids_morti_processati_sessione)
            p.aggiorna_gloria(self.giocatori, self._ids_morti_processati_sessione, oggi)
        if annuncia and self.polisportive:
            self.notifica(f"-> Stato ricalcolato per {len(self.polisportive)} polisportive.")

    # Uscite di scena.

    def _registra_uscita(self, g, motivo, data, club):
        """Annota l'uscita di scena nel registro delle vecchie glorie, salvato col mondo, e nel file vecchie_glorie.log, col valore di oggi."""
        g.aggiorna_aspetto()
        g.aggiorna_icv()
        voce = {
            "id": g.id, "nome": g.nome, "cognome": g.cognome, "sesso": g.sesso,
            "motivo": "morte" if motivo == DECESSO else "uscita", "eta": g.eta, "data": data.isoformat(), "club": club,
            "partite": g.partitevinte + g.partiteperse, "vittorie": g.partitevinte, "set": g.setsvinti + g.setspersi, "set_vinti": g.setsvinti,
            "goal_fatti": g.goalsfatti, "goal_subiti": g.goalssubiti, "valore": round(g.indice_collettivo_valore, 2),
            "scoperto": g.datetime_creazione_sim.isoformat(), "versione": getattr(g, "versione", "N/D"),
        }
        # Dalla tappa 12 le vecchie glorie conservano i punti della classifica mondiale per sempre e le
        # medaglie, perché la classifica mondiale è un medagliere storico, D32.
        if g.punti_mondiali or g.ori or g.argenti or g.bronzi or g.legni:
            voce.update(punti_mondiali=round(g.punti_mondiali, 2), ori=g.ori, argenti=g.argenti, bronzi=g.bronzi, legni=g.legni,
                        titoli_mondiali=sum(1 for t in g.titoli if t.get("mondiale") and t.get("posto") == 1))
        self.vecchie_glorie.insert(0, voce)
        come = f"{'muore' if voce['motivo'] == 'morte' else 'lascia il mondo dello showdown'} a {int(g.eta_anni)} anni"
        dove = f"da {accorda(g.sesso, 'tesserato')} con {club}" if club != "*" else f"da {accorda(g.sesso, 'libero')}"
        riga = (f"{data_breve(data)}: {nome_completo(g)}, ID {g.id}, {come}, {dove}. Partite {voce['partite']}, vinte {voce['vittorie']}; "
                f"valore finale {voce['valore']:.1f}. Annotato nel mondo reale il {adesso():%d/%m/%Y alle %H:%M}.\n")
        try:
            with open(percorsi.percorso(NOME_FILE_LOG_USCITE), "a", encoding="utf-8") as f:
                f.write(riga)
        except OSError as e:
            self.notifica(f"ERR scrittura log uscita GID {g.id}: {e}")

    def _uscita(self, g, motivo, data, eta_pre, rapporto=None):
        """Un giocatore esce di scena: per un'uscita prematura o per morte naturale."""
        gid = g.id
        club = g.appartenenza
        if motivo == USCITA_PREMATURA:
            msg = f"{motivo.upper()}: {nome_completo(g)}(ID:{gid}) lascia il mondo a {formatta_eta_sim(g.eta)} sim."
            self.annota(g, f"Lascia il mondo dello showdown, a {int(g.eta_anni)} anni.", data)
            if club != "*" and club in self.polisportive:
                self.annota(self.polisportive[club], f"{nome_completo(g)} lascia il mondo dello showdown.", data)
                self.polisportive[club].rimuovi_tesserato(gid, g.indice_collettivo_valore)
        else:
            msg = f"DECESSO (Età): {nome_completo(g)}(ID:{gid}) tra {formatta_eta_sim(eta_pre)} e {formatta_eta_sim(g.eta)} sim."
            self.annota(g, f"Muore, a {int(g.eta_anni)} anni.", data)
            if club != "*" and club in self.polisportive:
                self.annota(self.polisportive[club], f"{nome_completo(g)} muore.", data)
                self.polisportive[club].rimuovi_tesserato(gid, g.indice_collettivo_valore)
        # Chi esce di scena esce anche dalla vendita: prima ci restava, e il computer poteva
        # comprare un giocatore morto, che finiva fra i suoi tesserati.
        if club != "*" and club in self.polisportive:
            self.polisportive[club].in_vendita.pop(gid, None)
        self.giocatori_morti_sessione.append((gid, msg))
        self._ids_morti_processati_sessione.add(gid)
        g.ritirato = True
        g.appartenenza = "*"
        # Dalla tappa 11 sul giocatore uscito di scena non resta nessun contratto.
        g.annulla_contratto()
        g.programma = g.indole
        g.intensita = INTENSITA_PREDEFINITA
        # Dalla tappa 13 il suo allenatore, se il giocatore allenava, esce di scena con lui.
        for a in [a for a in self.allenatori.values() if a.giocatore_id == gid]:
            ruolo = "allenatrice" if a.sesso == "f" else "allenatore"
            verbo = "muore" if motivo == DECESSO else "lascia il mondo dello showdown"
            self._fine_allenatore(a, data, f"Esce di scena: {verbo}.", f"{nome_completo(a)}, {ruolo} dello staff, {verbo}.", rapporto)
        self._registra_uscita(g, motivo, data, club)

    def _fai_invecchiare(self, data, rapporto):
        """
        Un giorno per ogni giocatore vivo: guarigione, età, declino, uscita prematura, morte e ritiro.
        Dalla tappa 12, decisione 4 di Gabriele del 14 ottobre 2026, restituisce anche chi resta vivo e in
        attività nel declino, a cui il giorno ricalcola il valore alla fine, e quanti restano in attività:
        il resto del giorno non fa morire né ritirare nessuno, e prima per saperlo si scorreva il mondo
        intero altre due volte. Il declino si chiama soltanto per chi è arrivato all'età del suo inizio,
        lo stesso confronto che il declino faceva per primo.
        """
        morti = self._ids_morti_processati_sessione
        polisportive = self.polisportive
        oggi = data.date()
        inizio_declino = tratti.giorni_inizio_declino
        declinanti = []
        attivi = 0
        for gid, g in list(self.giocatori.items()):
            if gid in morti:
                continue
            if g.infortunato and g.infortunio_fine_datetime and data >= g.infortunio_fine_datetime:
                g.infortunato = False
                g.infortunio_fine_datetime = None
                g.infortunio_sede = None
                rapporto["guariti"] += 1
                self.annota(g, "Guarisce dall'infortunio.", data)
            # Dalla tappa 12 l'acciacco finito se ne va, senza una voce: il calo era già arrivato a zero.
            if g.acciacco_fino is not None and oggi >= g.acciacco_fino.date():
                infortuni.guarisci_acciacco(g)
            eta_pre = g.eta
            g.eta += 1
            inizio = inizio_declino(g)
            nel_declino = g.eta >= inizio
            if nel_declino:
                g._applica_declino_aggregato(1, inizio)
            club = polisportive.get(g.appartenenza)
            tuo = club is not None and not club.is_cpu_controlled
            if PROB_USCITA_PREMATURA_GIORNALIERA > 0 and caso(PROB_USCITA_PREMATURA_GIORNALIERA):
                self._uscita(g, USCITA_PREMATURA, data, eta_pre, rapporto)
                rapporto["usciti"] += 1
                rapporto["tuoi_usciti"] += tuo
                continue
            if g.eta >= g.etamorte:
                self._uscita(g, DECESSO, data, eta_pre, rapporto)
                rapporto["morti"] += 1
                rapporto["tuoi_usciti"] += tuo
                continue
            if not g.ritirato and g.eta >= g.etaritiro:
                g.ritirato = True
                # Da qui il valore non si ricalcola più ogni giorno: parte da quello di oggi.
                g.aggiorna_icv()
                # Dalla tappa 13 la classe migliore della carriera si chiude, e chi ha raggiunto H0 può allenare, D33;
                # la fedeltà al club si ricorda prima che il ritiro la azzeri, per la prelazione.
                allena = modulo_staff.puo_allenare(modulo_classe.livello(g.aggiorna_classe_migliore()))
                fedelta_al_ritiro = g.fedelta
                self.giocatori_ritirati_sessione.append((gid, f"RITIRO: {nome_completo(g)}(ID:{gid}) a {formatta_eta_sim(g.eta)} sim."))
                rapporto["tuoi_ritirati"] += tuo
                if club is not None:
                    # Chi si ritira lascia libero il suo posto: problema P4, risolto con la tappa 7.
                    self._lascia(club, g)
                    self.annota(g, f"Si ritira dall'attività, a {int(g.eta_anni)} anni, e lascia {club.nome}.", data)
                    self.annota(club, f"{nome_completo(g)} si ritira dall'attività e lascia la polisportiva.", data)
                else:
                    g.appartenenza = "*"
                    self.annota(g, f"Si ritira dall'attività, a {int(g.eta_anni)} anni.", data)
                if allena:
                    self._ex_giocatore_allenatore(g, club, data, fedelta_al_ritiro, rapporto=rapporto)
                rapporto["ritirati"] += 1
            if not g.ritirato:
                attivi += 1
                if nel_declino:
                    declinanti.append(g)
        return declinanti, attivi

    # Il tempo.

    @staticmethod
    def rapporto_vuoto(ora):
        """
        Il riepilogo di un avanzamento in cui non è successo niente. Dalla tappa 12 ha anche le notizie,
        le frasi dei risultati dei tuoi, una lista nuova a ogni riepilogo.
        """
        return dict.fromkeys(CHIAVI_RAPPORTO, 0) | {"ora": ora, "notizie": [], "riservati": ""}

    def prossimo_avanzamento(self):
        """L'istante, in UTC, in cui maturerà il prossimo giorno simulato."""
        return self.datetime_ultimo_run_reale + DURATA_TICK

    def ticks_maturati(self, ora=None):
        """Quanti giorni simulati sono maturati e non ancora elaborati, all'istante dato o adesso."""
        ora = ora or adesso_utc()
        if ora <= self.datetime_ultimo_run_reale:
            return 0
        return int((ora - self.datetime_ultimo_run_reale) / DURATA_TICK)

    def testo_prossimo_sblocco(self, ora=None):
        """Quando arriverà il prossimo avanzamento del mondo, se non è ancora arrivato; altrimenti None."""
        ora = ora or adesso_utc()
        prossimo = self.prossimo_avanzamento()
        if ora >= prossimo:
            return None
        h, m, _s = converti_in_tempo((prossimo - ora).total_seconds())
        return f"INFO: Prox aggiornamento sim alle {in_ora_locale(prossimo):%H:%M:%S del %d/%m/%Y} (tra {h}h {m}m)."

    def processa_tempo_trascorso(self, ora=None):
        """
        Fa avanzare il mondo di un giorno simulato per ogni 8 ore reali maturate dall'ultimo
        avanzamento, un giorno alla volta, e sposta l'ancora di 8 ore per ogni giorno: il resto
        resta per la volta dopo. Oltre ai messaggi per notifica restituisce il riepilogo in numeri,
        un dizionario con le chiavi di CHIAVI_RAPPORTO e l'ora locale dell'avanzamento.
        Dal 16 ottobre 2026, decisione 4 di Gabriele, accelerare senza cambiare gli esiti: mentre passano
        i giorni la raccolta dei cicli di Python resta spenta, utilita.senza_raccolta, e si riaccende alla
        fine anche se un giorno solleva un'eccezione. Il giorno fa pochissimi cicli da buttare, e la
        raccolta che riparte dopo li trova tutti in un giro solo, invece di ripassare a ogni gruppo di
        oggetti nuovi quelli nati nei giorni prima; il salvataggio, che segue l'avanzamento, raccoglie e
        congela la memoria, archivio.congela_la_memoria.
        """
        ora = ora or adesso_utc()
        ticks = self.ticks_maturati(ora)
        rapporto = self.rapporto_vuoto(in_ora_locale(ora))
        if ticks <= 0:
            testo = self.testo_prossimo_sblocco(ora)
            if testo:
                self.notifica(testo)
            return rapporto
        self.notifica(f"\n--- Processando {ticks} tick da 8h ({ora - self.datetime_ultimo_run_reale}) ---")
        inizio = self.datetime_corrente_simulazione
        self.notifica(f"Avanzamento sim: +{ticks} giorni -> {inizio + datetime.timedelta(days=ticks):%Y-%m-%d %H:%M}")
        rapporto["ticks"] = rapporto["giorni"] = ticks
        # Dalla tappa 13 l'ora vera dell'avanzamento, per la riserva dei nuovi allenatori all'utente, risposta 29.
        self._ora_reale = ora
        with senza_raccolta():
            for giorno in range(1, ticks + 1):
                data = inizio + datetime.timedelta(days=giorno)
                self.datetime_corrente_simulazione = data
                self._un_giorno(data, rapporto)
        self.datetime_ultimo_run_reale += DURATA_TICK * ticks
        self._notizia_dei_riservati(ora, rapporto)
        self._notifica_rapporto(rapporto)
        return rapporto

    def _notizia_dei_riservati(self, ora, rapporto):
        """
        La notizia degli allenatori nuovi riservati all'utente da questo avanzamento, risposta 38 di Gabriele
        del 22 ottobre 2026: soltanto nel riepilogo, fra le notizie, con quanti sono, fino a che ora e la
        classe del migliore; soltanto se l'utente ha una polisportiva.
        """
        if not any(not p.is_cpu_controlled for p in self.polisportive.values()):
            return
        fine = ora + datetime.timedelta(minutes=MINUTI_RISERVA_UTENTE)
        # I tuoi ritirati in prelazione hanno la loro notizia, con la loro scadenza: qui non si contano.
        nuovi = [a for a in self.allenatori.values() if a.libero and a.prelazione is None and a.riservato_fino == fine]
        if not nuovi:
            return
        migliore = min(nuovi, key=lambda a: (a.livello, a.numero))
        quando = f"{in_ora_locale(fine):%H:%M}"
        if len(nuovi) == 1:
            if migliore.sesso == "f":
                testo = f"Un'allenatrice nuova è riservata a te fino alle {quando}: {nome_completo(migliore)}, di classe {migliore.codice}. La trovi"
            else:
                testo = f"Un allenatore nuovo è riservato a te fino alle {quando}: {nome_completo(migliore)}, di classe {migliore.codice}. Lo trovi"
            testo += " nel mercato degli allenatori, Ctrl+Maiusc+G."
        else:
            testo = (f"{len(nuovi)} allenatori nuovi sono riservati a te fino alle {quando}, il migliore di classe {migliore.codice}: "
                     "li trovi nel mercato degli allenatori, Ctrl+Maiusc+G.")
        # Una chiave sua e non fra le notizie: alla chiusura della sessione la riserva è quasi sempre scaduta.
        rapporto["riservati"] = testo

    def _un_giorno(self, data, rapporto):
        """
        Tutto ciò che il mondo fa in un giorno simulato, nell'ordine: le mosse di mercato
        ripartono, i giocatori invecchiano, il primo del mese si fanno i conti e calano i livelli
        alti, tutti si allenano e i liberi e il computer spendono, le polisportive del computer
        tesserano, scambiano, comprano, chiudono e nascono, poi nascono i giocatori nuovi e si
        ricalcolano valori e glorie.
        """
        for p in self.polisportive.values():
            p.movimenti_oggi = 0
        # Dalla tappa 13 i fattori dello staff si rinfrescano a ogni giorno, e gli allenatori invecchiano.
        self.aggiorna_fattori_staff()
        declinanti, attivi = self._fai_invecchiare(data, rapporto)
        self._invecchia_lo_staff(data, rapporto)
        if data.day == 1:
            self._primo_del_mese(data, rapporto)
            self._mantenimento_del_mese(data)
        self._allenamento_del_giorno(data, rapporto)
        # Dalla tappa 12 il calendario dei tornei e poi le sfide, dopo l'allenamento e prima delle mosse
        # del computer: chi ha vinto qualcosa ricalcola subito la gloria, così il mercato la vede.
        toccate = self.calendario.giorno(self, data, rapporto)
        toccate |= sfide.giorno(self, data, rapporto)
        for nome in sorted(toccate):
            poli = self.polisportive.get(nome)
            if poli is not None:
                poli.aggiorna_gloria(self.giocatori, self._ids_morti_processati_sessione, data)
        venduti_tuoi = sum(len(p.in_vendita) for p in self.polisportive.values() if not p.is_cpu_controlled)
        tesserati, svincolati, comprati = self._esegui_logica_cpu_polisportive(data)
        rapporto["tesserati_cpu"] += tesserati
        rapporto["svincolati_cpu"] += svincolati
        rapporto["vendite"] += comprati
        rapporto["tuoi_venduti"] += venduti_tuoi - sum(len(p.in_vendita) for p in self.polisportive.values() if not p.is_cpu_controlled)
        for nome_p in list(self.polisportive.keys()):
            if nome_p in self.polisportive and self.polisportive[nome_p].is_cpu_controlled and self._controlla_chiusura_poli_cpu(self.polisportive[nome_p], data):
                rapporto["poli_chiuse"] += 1
        if self._serve_una_polisportiva_cpu(attivi) and caso(PROB_CREAZIONE_POLI_CPU_PER_TICK) and self.crea_polisportiva_cpu(data):
            rapporto["poli_create"] += 1
        # Dalla tappa 11 il valore si ricalcola soltanto per chi è nel declino, che cambia ogni giorno:
        # la spesa d'allenamento e il calo del mese lo ricalcolano da sé, e rifarlo per tutti i
        # giocatori del mondo costava più di tutto il resto del giorno. I ritirati vivi, a regime
        # quasi seimila, non giocano e non firmano: il loro valore serve alla scheda, alla ricerca e
        # alle vecchie glorie, e si ricalcola al ritiro, il primo del mese e all'uscita di scena. Dalla
        # decisione 4 di Gabriele chi è nel declino lo dice già _fai_invecchiare, nello stesso ordine.
        for g in declinanti:
            g.aggiorna_icv()
        nuovi = random.randint(*CREA_NUOVI_PER_TICK_RANGE)
        self.crea_giocatori_casuali(nuovi, data, annuncia=False)
        rapporto["nuovi"] += nuovi
        # Dalla tappa 13, con un giocatore su venti nasce anche un allenatore adulto, D33 risposta 8. Si tira
        # qui e non in crea_giocatori_casuali, che serve anche ai mondi in memoria degli ascolti della
        # tappa 10: i loro giocatori, e i suoni che Gabriele ha ascoltato, restano quelli.
        for _ in range(nuovi):
            if caso(PROBABILITA_ALLENATORE_PER_NASCITA):
                self._nasce_un_allenatore(data)
        self.aggiorna_stato_polisportive(annuncia=False)

    def _serve_una_polisportiva_cpu(self, attivi):
        """
        Vero se il computer può fondare una polisportiva nuova: le sue polisportive sono meno di una
        ogni GIOCATORI_ATTIVI_PER_POLI_CPU_TARGET giocatori in attività. Dalla tappa 12, issue 1, si
        contano soltanto i giocatori in attività, non i ritirati, e soltanto le polisportive del
        computer, non quelle dell'utente: prima il limite contava tutti i vivi e tutte le polisportive,
        e dall'anno 40 simulato il computer aveva più posti che giocatori in attività, così il mercato
        dei liberi restava vuoto. A regime, con circa 20.600 attivi, il limite è di 1.248 polisportive,
        18.727 posti, il 91 per cento degli attivi. Dalla decisione 4 di Gabriele del 14 ottobre 2026 i
        giocatori in attività li conta _fai_invecchiare, e qui arriva il numero.
        """
        if GIOCATORI_ATTIVI_PER_POLI_CPU_TARGET <= 0:
            return False
        poli_cpu = sum(1 for p in self.polisportive.values() if p.is_cpu_controlled)
        return poli_cpu < attivi / GIOCATORI_ATTIVI_PER_POLI_CPU_TARGET

    def _notifica_rapporto(self, rapporto):
        """Il riepilogo dell'avanzamento nella forma dell'interfaccia testuale."""
        for numero, testo in ((rapporto["guariti"], "guariti"), (rapporto["usciti"], "giocatori usciti prematuramente"),
                              (rapporto["morti"], "deceduti per età"), (rapporto["ritirati"], "ritirati per età"),
                              (rapporto["autoallenati"], "allenamenti da autonomi")):
            if numero > 0:
                self.notifica(f"-> {numero} {testo}.")
        self.notifica("\n--- Riepilogo Avanzamento Tick ---")
        for numero, testo in ((rapporto["ritirati"], "* Ritirati (età)"), (rapporto["usciti"], "* Usciti Prematuramente"), (rapporto["morti"], "* Deceduti (età)"),
                              (rapporto["nuovi"], "* Nuovi giocatori"), (rapporto["poli_chiuse"], "* Poli CPU chiuse"), (rapporto["poli_create"], "* Poli CPU create"),
                              (rapporto["tesserati_cpu"], "* CPU Tesserati"), (rapporto["svincolati_cpu"], "* CPU Svincolati"),
                              (rapporto["tornei_conclusi"], "* Tornei conclusi"), (rapporto["incontri_torneo"], "* Incontri di torneo"),
                              (rapporto["sfide_giocate"], "* Sfide giocate")):
            if numero > 0:
                self.notifica(f"{testo}: {numero}")
        # Dalla tappa 12 le notizie dei tuoi, una per riga, e le sfide che aspettano la tua risposta.
        for notizia in rapporto["notizie"]:
            self.notifica(notizia)
        if rapporto.get("riservati"):
            self.notifica(rapporto["riservati"])
        if rapporto["sfide_in_attesa"]:
            self.notifica(f"Sfide che aspettano la tua risposta: {rapporto['sfide_in_attesa']}.")
        self.notifica("-" * 30)
