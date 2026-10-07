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
Il mondo non stampa: consegna i suoi messaggi alla funzione notifica, che gli passa chi lo usa.
Dal 2026-10-07 il riepilogo di un avanzamento conta anche i primi del mese e, delle polisportive
dell'utente, i tesserati ritirati, quelli usciti di scena e le bandiere nuove: la finestra ne fa
sentire il suono, secondo la decisione D24.
"""

import datetime
import math
import random

import percorsi
from allenamento import esegui_auto_allenamento
from costanti import (
    ANNO_SIMULAZIONE_GIORNI,
    BILANCI_CONSERVATI,
    CREA_NUOVI_PER_TICK_RANGE,
    ESPERIENZA_MASSIMA,
    ESPERIENZA_PER_MESE,
    ETA_MINIMA_CHIUSURA_CPU_ANNI,
    FATTORE_PROB_GLORIA,
    FATTORE_PROB_TESSERATI,
    FEDELTA_BANDIERA,
    FEDELTA_MASSIMA,
    FEDELTA_PER_MESE,
    GIOCATORI_ATTIVI_PER_POLI_CPU_TARGET,
    IMPORTANZA_MASSIMA,
    LIMITE_MOVIMENTI_PER_TICK,
    MAX_PROB_CHIUSURA_GIORNALIERA,
    MESI_DI_INGAGGIO,
    MESI_DI_RISERVA_CPU,
    NOME_FILE_LOG_USCITE,
    NOME_POLISPORTIVA_MAX,
    NOME_POLISPORTIVA_MIN,
    PARTI_DI_CASSA_PER_STIPENDI,
    PROB_CHIUSURA_BASE_GIORNALIERA,
    PROB_CREAZIONE_POLI_CPU_PER_TICK,
    PROB_SCAMBIO_CPU_GIORNALIERA,
    PROB_USCITA_PREMATURA_GIORNALIERA,
    PROBABILITA_IPOVEDENTE_CREAZIONE,
    REPUTAZIONE_MINIMA,
    RIALZO_CPU,
    SCARTI_MASSIMI_CPU,
    SOGLIA_GLORIA_BASSA_CHIUSURA,
    SOGLIA_MINIMA_TESSERATI_CHIUSURA,
)
from economia import (
    arrotonda,
    bandiera_attiva,
    ingaggio_richiesto,
    mesi_di_pazienza,
    pazienza_per_euro,
    scritta_in_euro,
    sponsor_mensile,
    stipendio,
    valore_di_mercato,
)
from modelli import Giocatore, Polisportiva, conti_vuoti, normalizza_nome, probabilita_accettazione
from nomi import genera_nome_casuale
from utilita import accorda, adesso, adesso_utc, caso, converti_in_tempo, data_breve, formatta_eta_sim, in_ora_locale

ORE_PER_TICK = 8
DURATA_TICK = datetime.timedelta(hours=ORE_PER_TICK)
# Le voci del riepilogo di un avanzamento, oltre all'ora in cui è avvenuto.
CHIAVI_RAPPORTO = ("ticks", "giorni", "guariti", "ritirati", "usciti", "morti", "nuovi", "autoallenati",
                   "tesserati_cpu", "svincolati_cpu", "poli_chiuse", "poli_create", "partiti", "vendite",
                   "tuoi_non_pagati", "tuoi_partiti", "tuoi_venduti", "mesi", "tuoi_ritirati", "tuoi_usciti", "tue_bandiere")
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

    def _entra(self, poli, g):
        """Il giocatore entra nella polisportiva: la fedeltà riparte da zero, la pazienza è piena, nessun arretrato."""
        g.appartenenza = poli.nome
        poli.aggiungi_tesserato(g.id, g.indice_collettivo_valore)
        g.fedelta = 0.
        g.pazienza = 100.
        g.arretrati = 0

    def _tessera(self, poli, g, data=None, ingaggio=None):
        self._entra(poli, g)
        con_ingaggio = f", con un ingaggio di {scritta_in_euro(ingaggio)}" if ingaggio else ""
        self.annota(g, f"{accorda(g.sesso, 'Tesserato')} con {poli.nome}{con_ingaggio}.", data)
        self.annota(poli, f"Tesserato {nome_completo(g)}{con_ingaggio}.", data)

    def _lascia(self, poli, g):
        """
        Il giocatore esce dall'elenco dei tesserati e torna libero, senza voci di diario: le
        scrive chi chiama. Esce anche dalla vendita, e i suoi arretrati non li aspetta più.
        """
        poli.rimuovi_tesserato(g.id, g.indice_collettivo_valore)
        poli.in_vendita.pop(g.id, None)
        g.appartenenza = "*"
        g.fedelta = 0.
        g.pazienza = 100.
        g.arretrati = 0

    # Arretrati, vendite e acquisti.

    def monte_stipendi(self, poli):
        """Quanto la polisportiva paga ogni mese di stipendi, a chi ha oggi."""
        return sum(stipendio(self.giocatori[gid]) for gid in poli.tesserati if gid in self.giocatori and gid not in self._ids_morti_processati_sessione)

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
        return arrotonda(valore_di_mercato(g) * (1 + IMPORTANZA_MASSIMA * posizione), 100)

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
        self._entra(compratore, g)
        cifra = scritta_in_euro(prezzo)
        self.annota(g, f"{accorda(g.sesso, 'Venduto')} da {venditore.nome} a {compratore.nome} per {cifra}.", data)
        self.annota(venditore, f"Venduto {nome_completo(g)} a {compratore.nome} per {cifra}.", data)
        self.annota(compratore, f"Comprato {nome_completo(g)} da {venditore.nome} per {cifra}.", data)

    def svincola(self, poli, g):
        """L'utente svincola un suo tesserato, che torna libero: usa una mossa; ValueError se non si può."""
        if g.id not in poli.tesserati:
            raise ValueError(f"{nome_completo(g)} non è {accorda(g.sesso, 'tesserato')} con {poli.nome}.")
        if self.mosse_rimaste(poli) <= 0:
            raise ValueError(self._senza_mosse(poli))
        self._usa_mossa(poli)
        self._lascia(poli, g)
        self.annota(g, f"{accorda(g.sesso, 'Svincolato')} da {poli.nome}.")
        self.annota(poli, f"Svincolato {nome_completo(g)}.")

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

    def annota(self, soggetto, testo, data=None):
        """Una voce nel diario di un giocatore o di una polisportiva, con la data simulata, di oggi se non è data."""
        soggetto.annota(data or self.datetime_corrente_simulazione, testo)

    def sfoltisci_diari(self):
        """Toglie dai diari le voci più vecchie dei giorni simulati da conservare; restituisce quante ne ha tolte."""
        tolte = 0
        for chiave, soggetti in (("giocatori", self.giocatori.values()), ("polisportive", self.polisportive.values())):
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
        if annuncia:
            self.notifica(f" -> Creati {quanti} nuovi giocatori.")

    def crea_polisportiva_cpu(self, dt_creaz):
        """Fonda una polisportiva del computer con un nome nuovo; ne restituisce il nome, o None."""
        suff = 1
        base = "PoliTeam"
        while True:
            prefisso = f"{base}{suff:02d} ".casefold()
            if not any(n.casefold().startswith(prefisso) for n in self.polisportive):
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
        """
        liberi = list(self.trova_giocatori_liberi_ordinati().values())
        stipendi = [stipendio(g) for g in liberi]
        vetrina = _Vetrina(stipendi)
        tesserati = svincolati = comprati = 0
        cpu = sorted((p for p in self.polisportive.values() if p.is_cpu_controlled), key=lambda p: p.gloria, reverse=True)
        for poli in cpu:
            monte = self.monte_stipendi(poli)
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
        for poli in cpu:
            if self._compra_dal_mercato(poli, data):
                comprati += 1
        return tesserati, svincolati, comprati

    def _stipendio_massimo(self, poli, monte, spendibile):
        """
        Lo stipendio più alto che una polisportiva del computer può aggiungere: deve stare nello
        sponsor più una parte della cassa, e l'ingaggio più basso possibile deve stare nella cassa.
        """
        nei_conti = sponsor_mensile(poli) + poli.cassa / PARTI_DI_CASSA_PER_STIPENDI - monte
        nella_cassa = spendibile / (MESI_DI_INGAGGIO * REPUTAZIONE_MINIMA * RIALZO_CPU)
        return min(nei_conti, nella_cassa)

    def _rosa(self, poli):
        return [self.giocatori[gid] for gid in poli.tesserati if gid in self.giocatori and gid not in self._ids_morti_processati_sessione]

    def _scambio(self, poli, liberi, vetrina, prossimo, monte, data):
        """Una polisportiva a rosa piena prova il libero più forte che si può permettere; vero se l'ha preso al posto del tesserato che vale meno."""
        rosa = self._rosa(poli)
        if not rosa:
            return False
        debole = min(rosa, key=lambda g: g.indice_collettivo_valore)
        spendibile = poli.cassa - monte * MESI_DI_RISERVA_CPU
        posto = vetrina.primo(self._stipendio_massimo(poli, monte - stipendio(debole), spendibile), prossimo)
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
        self._lascia(poli, debole)
        self._paga_ingaggio(poli, offerta)
        self._entra(poli, nuovo)
        vetrina.togli(posto)
        self.annota(nuovo, f"{accorda(nuovo.sesso, 'Tesserato')} con {poli.nome}, con un ingaggio di {scritta_in_euro(offerta)}.", data)
        self.annota(debole, f"{accorda(debole.sesso, 'Svincolato')} da {poli.nome}, che al suo posto ha tesserato {nome_completo(nuovo)}.", data)
        self.annota(poli, f"Tesserato {nome_completo(nuovo)} al posto di {nome_completo(debole)}, che torna {accorda(debole.sesso, 'libero')}.", data)
        return True

    def _compra_dal_mercato(self, poli, data):
        """
        Una polisportiva del computer compra il più forte dei giocatori in vendita, se il prezzo non
        supera di molto il suo valore di mercato e se ci sta nei conti; a rosa piena solo se è più
        forte del tesserato che vale meno, che lascia libero. Al massimo un acquisto al giorno.
        """
        if self.mosse_rimaste(poli) <= 0:
            return False
        rosa = self._rosa(poli)
        piena = len(poli.tesserati) >= poli.maxtesserati
        if piena and not rosa:
            return False
        debole = min(rosa, key=lambda g: g.indice_collettivo_valore) if piena else None
        monte = self.monte_stipendi(poli) - (stipendio(debole) if debole else 0)
        spendibile = poli.cassa - monte * MESI_DI_RISERVA_CPU
        massimo = sponsor_mensile(poli) + poli.cassa / PARTI_DI_CASSA_PER_STIPENDI - monte
        scelta = None
        for venditore in self.polisportive.values():
            if venditore is poli:
                continue
            for gid, prezzo in venditore.in_vendita.items():
                g = self.giocatori.get(gid)
                # Il ritirato non si compra: serve ai salvataggi in cui un morto era rimasto in vendita.
                if g is None or g.ritirato or prezzo > spendibile or prezzo > valore_di_mercato(g) * RIALZO_CPU or stipendio(g) > massimo:
                    continue
                if debole is not None and g.indice_collettivo_valore <= debole.indice_collettivo_valore:
                    continue
                if scelta is None or g.indice_collettivo_valore > scelta[0].indice_collettivo_valore:
                    scelta = (g, venditore, prezzo)
        if scelta is None:
            return False
        g, venditore, prezzo = scelta
        self._usa_mossa(poli)
        if debole is not None:
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
        """
        rapporto["mesi"] += 1
        for poli in list(self.polisportive.values()):
            rosa = self._rosa(poli)
            self._fedelta_ed_esperienza(poli, rosa, data, rapporto)
            sponsor = sponsor_mensile(poli)
            poli.cassa += sponsor
            poli.conti_del_mese["sponsor"] += sponsor
            dovuti = {g.id: stipendio(g) for g in rosa}
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
            poli.bilanci.insert(0, {"data": data, "cassa": poli.cassa, **poli.conti_del_mese})
            del poli.bilanci[BILANCI_CONSERVATI:]
            poli.conti_del_mese = conti_vuoti()

    def _fedelta_ed_esperienza(self, poli, rosa, data, rapporto=None):
        """Un mese in più nel club: fedeltà ed esperienza crescono, e una bandiera si accende quando la fedeltà arriva alla soglia."""
        for g in rosa:
            prima = g.fedelta
            g.fedelta = min(FEDELTA_MASSIMA, g.fedelta + FEDELTA_PER_MESE)
            g.esperienza = min(ESPERIENZA_MASSIMA, g.esperienza + ESPERIENZA_PER_MESE)
            if g.bandiera and prima < FEDELTA_BANDIERA <= g.fedelta:
                self.annota(g, f"Diventa una bandiera di {poli.nome}: giocherà per il club anche senza stipendio.", data)
                self.annota(poli, f"{nome_completo(g)} diventa una bandiera del club.", data)
                if rapporto is not None and not poli.is_cpu_controlled:
                    rapporto["tue_bandiere"] += 1

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
        caro = max(in_vendita, key=stipendio)
        prezzo = valore_di_mercato(caro)
        poli.in_vendita[caro.id] = prezzo
        self.annota(poli, f"Mette in vendita {nome_completo(caro)} a {scritta_in_euro(prezzo)}.", data)
        self.annota(caro, f"{accorda(caro.sesso, 'Messo')} in vendita da {poli.nome} a {scritta_in_euro(prezzo)}.", data)

    def aggiorna_stato_polisportive(self, annuncia=True):
        """Ricalcola indice dei tesserati e gloria di tutte le polisportive."""
        if annuncia:
            self.notifica("Aggiornamento stato polisportive...")
        for p in self.polisportive.values():
            p.aggiorna_ict(self.giocatori, self._ids_morti_processati_sessione)
            p.aggiorna_gloria(self.giocatori, self._ids_morti_processati_sessione)
        if annuncia and self.polisportive:
            self.notifica(f"-> Stato ricalcolato per {len(self.polisportive)} polisportive.")

    # Uscite di scena.

    def _registra_uscita(self, g, motivo, data, club):
        """Annota l'uscita di scena nel registro delle vecchie glorie, salvato col mondo, e nel file vecchie_glorie.log."""
        g.aggiorna_aspetto()
        voce = {
            "id": g.id, "nome": g.nome, "cognome": g.cognome, "sesso": g.sesso,
            "motivo": "morte" if motivo == DECESSO else "uscita", "eta": g.eta, "data": data.isoformat(), "club": club,
            "partite": g.partitevinte + g.partiteperse, "vittorie": g.partitevinte, "set": g.setsvinti + g.setspersi, "set_vinti": g.setsvinti,
            "goal_fatti": g.goalsfatti, "goal_subiti": g.goalssubiti, "valore": round(g.indice_collettivo_valore, 2),
            "scoperto": g.datetime_creazione_sim.isoformat(), "versione": getattr(g, "versione", "N/D"),
        }
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

    def _uscita(self, g, motivo, data, eta_pre):
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
        self._registra_uscita(g, motivo, data, club)

    def _fai_invecchiare(self, data, rapporto):
        """Un giorno per ogni giocatore vivo: guarigione, età, declino, uscita prematura, morte e ritiro."""
        morti = self._ids_morti_processati_sessione
        for gid in list(self.giocatori):
            if gid in morti:
                continue
            g = self.giocatori[gid]
            if g.infortunato and g.infortunio_fine_datetime and data >= g.infortunio_fine_datetime:
                g.infortunato = False
                g.infortunio_fine_datetime = None
                rapporto["guariti"] += 1
                self.annota(g, "Guarisce dall'infortunio.", data)
            eta_pre = g.eta
            g.eta += 1
            g._applica_declino_aggregato(1)
            club = self.polisportive.get(g.appartenenza)
            tuo = club is not None and not club.is_cpu_controlled
            if PROB_USCITA_PREMATURA_GIORNALIERA > 0 and caso(PROB_USCITA_PREMATURA_GIORNALIERA):
                self._uscita(g, USCITA_PREMATURA, data, eta_pre)
                rapporto["usciti"] += 1
                rapporto["tuoi_usciti"] += tuo
                continue
            if g.eta >= g.etamorte:
                self._uscita(g, DECESSO, data, eta_pre)
                rapporto["morti"] += 1
                rapporto["tuoi_usciti"] += tuo
                continue
            if not g.ritirato and g.eta >= g.etaritiro:
                g.ritirato = True
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
                rapporto["ritirati"] += 1

    # Il tempo.

    @staticmethod
    def rapporto_vuoto(ora):
        """Il riepilogo di un avanzamento in cui non è successo niente."""
        return dict.fromkeys(CHIAVI_RAPPORTO, 0) | {"ora": ora}

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
        for giorno in range(1, ticks + 1):
            data = inizio + datetime.timedelta(days=giorno)
            self.datetime_corrente_simulazione = data
            self._un_giorno(data, rapporto)
        self.datetime_ultimo_run_reale += DURATA_TICK * ticks
        self._notifica_rapporto(rapporto)
        return rapporto

    def _un_giorno(self, data, rapporto):
        """
        Tutto ciò che il mondo fa in un giorno simulato, nell'ordine: le mosse di mercato
        ripartono, i giocatori invecchiano, il primo del mese si fanno i conti, gli autonomi si
        allenano, le polisportive del computer tesserano, scambiano, comprano, chiudono e nascono,
        poi nascono i giocatori nuovi e si ricalcolano valori e glorie.
        """
        for p in self.polisportive.values():
            p.movimenti_oggi = 0
        self._fai_invecchiare(data, rapporto)
        if data.day == 1:
            self._primo_del_mese(data, rapporto)
        vivi = [g for gid, g in self.giocatori.items() if gid not in self._ids_morti_processati_sessione]
        for g in vivi:
            if not g.ritirato and not g.infortunato and int(g.puntiesperienza or 0) > 0:
                if g.appartenenza == "*" or (g.appartenenza in self.polisportive and self.polisportive[g.appartenenza].is_cpu_controlled):
                    xp_pre = g.puntiesperienza
                    esegui_auto_allenamento(g, data)
                    if g.puntiesperienza < xp_pre:
                        rapporto["autoallenati"] += 1
        venduti_tuoi = sum(len(p.in_vendita) for p in self.polisportive.values() if not p.is_cpu_controlled)
        tesserati, svincolati, comprati = self._esegui_logica_cpu_polisportive(data)
        rapporto["tesserati_cpu"] += tesserati
        rapporto["svincolati_cpu"] += svincolati
        rapporto["vendite"] += comprati
        rapporto["tuoi_venduti"] += venduti_tuoi - sum(len(p.in_vendita) for p in self.polisportive.values() if not p.is_cpu_controlled)
        for nome_p in list(self.polisportive.keys()):
            if nome_p in self.polisportive and self.polisportive[nome_p].is_cpu_controlled and self._controlla_chiusura_poli_cpu(self.polisportive[nome_p], data):
                rapporto["poli_chiuse"] += 1
        limite_poli = len(vivi) / GIOCATORI_ATTIVI_PER_POLI_CPU_TARGET if vivi and GIOCATORI_ATTIVI_PER_POLI_CPU_TARGET > 0 else 0.
        if len(self.polisportive) < limite_poli and caso(PROB_CREAZIONE_POLI_CPU_PER_TICK) and self.crea_polisportiva_cpu(data):
            rapporto["poli_create"] += 1
        for g in vivi:
            g.aggiorna_icv()
        nuovi = random.randint(*CREA_NUOVI_PER_TICK_RANGE)
        self.crea_giocatori_casuali(nuovi, data, annuncia=False)
        rapporto["nuovi"] += nuovi
        self.aggiorna_stato_polisportive(annuncia=False)

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
                              (rapporto["tesserati_cpu"], "* CPU Tesserati"), (rapporto["svincolati_cpu"], "* CPU Svincolati")):
            if numero > 0:
                self.notifica(f"{testo}: {numero}")
        self.notifica("-" * 30)
