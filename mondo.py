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
finiscono nei diari di chi li vive, e chi esce di scena nel registro delle vecchie glorie. Restano i difetti delle polisportive del computer, problemi P4, P7 e P16, che si
correggono alla tappa 7.
Il mondo non stampa: consegna i suoi messaggi alla funzione notifica, che gli passa chi lo usa.
"""

import datetime
import random

import percorsi
from allenamento import esegui_auto_allenamento
from costanti import (
    ANNO_SIMULAZIONE_GIORNI,
    CREA_NUOVI_PER_TICK_RANGE,
    ETA_MINIMA_CHIUSURA_CPU_ANNI,
    FATTORE_PROB_GLORIA,
    FATTORE_PROB_TESSERATI,
    GIOCATORI_ATTIVI_PER_POLI_CPU_TARGET,
    LIMITE_MOVIMENTI_PER_TICK,
    MAX_PROB_CHIUSURA_GIORNALIERA,
    NOME_FILE_LOG_USCITE,
    PROB_CHIUSURA_BASE_GIORNALIERA,
    PROB_CREAZIONE_POLI_CPU_PER_TICK,
    PROB_USCITA_PREMATURA_GIORNALIERA,
    PROBABILITA_IPOVEDENTE_CREAZIONE,
    SOGLIA_GLORIA_BASSA_CHIUSURA,
    SOGLIA_MINIMA_TESSERATI_CHIUSURA,
)
from modelli import Giocatore, Polisportiva, probabilita_accettazione
from nomi import genera_nome_casuale
from utilita import accorda, adesso, adesso_utc, caso, converti_in_tempo, data_breve, formatta_eta_sim, in_ora_locale

ORE_PER_TICK = 8
DURATA_TICK = datetime.timedelta(hours=ORE_PER_TICK)
# Le voci del riepilogo di un avanzamento, oltre all'ora in cui è avvenuto.
CHIAVI_RAPPORTO = ("ticks", "giorni", "guariti", "ritirati", "usciti", "morti", "nuovi", "autoallenati",
                   "tesserati_cpu", "espulsi_cpu", "poli_chiuse", "poli_create")
# Per quanti giorni simulati si conservano le voci dei diari: zero vuol dire per sempre, come in Terminal Beast.
CONSERVAZIONE_PREDEFINITA = {"giocatori": 0, "polisportive": 0}
USCITA_PREMATURA = "Uscita Prematura"
DECESSO = "Decesso Naturale"


def _silenzio(*_args, **_kwargs):
    """Al posto di notifica quando chi usa il mondo non la passa."""


def nome_completo(g):
    return f"{g.nome} {g.cognome}"


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
            prefix = f"{base}{suff:02d} "
            if not any(n.startswith(prefix) for n in self.polisportive):
                break
            suff += 1
            if suff > 9999:
                self.notifica("ATT: Suffix CPU>9999.")
                return None
        p1 = genera_nome_casuale(["cvcv"], 'x').lower()
        p2 = genera_nome_casuale(["cvcv"], 'x').lower()
        nome = f"{base}{suff:02d} {p1}-{p2}"
        if nome in self.polisportive:
            self.notifica(f"ATT: Collisione nome CPU '{nome}'.")
            return None
        self.polisportive[nome] = Polisportiva(nome=nome, password=None, datetime_creazione_sim=dt_creaz, is_cpu_controlled=True)
        return nome

    def _chiudi_polisportiva_cpu(self, nome_p, dt_chiusura):
        # Problema P16, tappa 7: chi chiama passa il nome ritoccato della polisportiva, che non è
        # la sua chiave nel mondo, quindi qui non si arriva mai.
        poli = self.polisportive.get(nome_p)
        if not poli or not poli.is_cpu_controlled:
            return False
        eta_str = formatta_eta_sim(int((dt_chiusura - poli.datetime_creazione_sim).total_seconds() / (24 * 3600)))
        self.notifica(f"** Evento ({dt_chiusura:%Y-%m-%d %H:%M}): Chiusura Poli CPU '{nome_p}' (Età: {eta_str}, G:{poli.gloria}, T:{len(poli.tesserati)}) **")
        n_lib = 0
        for gid in list(poli.tesserati):
            if gid in self.giocatori:
                g = self.giocatori[gid]
                g.appartenenza = "*"
                self.annota(g, f"Torna {accorda(g.sesso, 'libero')}: {poli.nome} ha chiuso.", dt_chiusura)
                n_lib += 1
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
        """Le polisportive del computer tesserano i liberi più forti alla loro portata ed espellono il più debole a rosa piena."""
        liberi = self.trova_giocatori_liberi_ordinati()
        # La gloria che ogni libero chiede non cambia durante le mosse del giorno: si calcola una
        # volta sola, e così la pretesa, scontata di un decimo per gli ipovedenti. Chi ha meno
        # gloria della pretesa più bassa non trova nessuno e non fa mosse, quindi non cerca.
        richieste = {gid: g.gloria_richiesta for gid, g in liberi.items()}
        pretese = {gid: int(r * .9) if liberi[gid].ipovedente else r for gid, r in richieste.items()}
        pretesa_minima = min(pretese.values(), default=None)
        n_tess_cpu_tot = 0
        n_esp_cpu_tot = 0
        for nome_p in list(self.polisportive.keys()):
            if nome_p not in self.polisportive or not self.polisportive[nome_p].is_cpu_controlled:
                continue
            poli = self.polisportive[nome_p]
            while poli.movimenti_oggi < LIMITE_MOVIMENTI_PER_TICK and len(poli.tesserati) < poli.maxtesserati:
                cand_ok = None
                gid_t = -1
                tent = False
                if not liberi or poli.gloria < pretesa_minima:
                    break
                for gid_c, cand in liberi.items():
                    g_r = richieste[gid_c]
                    if cand.appartenenza == "*" and pretese[gid_c] <= poli.gloria:
                        poli.movimenti_oggi += 1
                        poli.datetime_ultimo_movimento = adesso()
                        tent = True
                        if caso(probabilita_accettazione(poli.gloria, g_r)):
                            cand_ok = cand
                            gid_t = gid_c
                        break
                if not tent:
                    break
                if cand_ok:
                    cand_ok.appartenenza = poli.nome
                    poli.aggiungi_tesserato(gid_t, cand_ok.indice_collettivo_valore)
                    self.annota(cand_ok, f"{accorda(cand_ok.sesso, 'Tesserato')} con {poli.nome}.", data)
                    self.annota(poli, f"Tesserato {nome_completo(cand_ok)}.", data)
                    del liberi[gid_t]
                    n_tess_cpu_tot += 1
            while poli.movimenti_oggi < LIMITE_MOVIMENTI_PER_TICK and len(poli.tesserati) >= poli.maxtesserati:
                pegg_gid = -1
                min_icv = float('inf')
                tess_v = [tid for tid in poli.tesserati if tid in self.giocatori and tid not in self._ids_morti_processati_sessione]
                if not tess_v:
                    break
                for tid in tess_v:
                    icv = self.giocatori[tid].indice_collettivo_valore
                    if icv < min_icv:
                        min_icv = icv
                        pegg_gid = tid
                if pegg_gid == -1:
                    break
                poli.movimenti_oggi += 1
                poli.datetime_ultimo_movimento = adesso()
                poli.rimuovi_tesserato(pegg_gid, min_icv)
                g_p = self.giocatori[pegg_gid]
                g_p.appartenenza = "*"
                self.annota(g_p, f"{accorda(g_p.sesso, 'Espulso')} da {poli.nome}.", data)
                self.annota(poli, f"Espulso {nome_completo(g_p)}.", data)
                n_esp_cpu_tot += 1
        return n_tess_cpu_tot, n_esp_cpu_tot

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
            # Problema P4, tappa 7: il morto viene liberato ma resta fra i tesserati della sua polisportiva.
            msg = f"DECESSO (Età): {nome_completo(g)}(ID:{gid}) tra {formatta_eta_sim(eta_pre)} e {formatta_eta_sim(g.eta)} sim."
            self.annota(g, f"Muore, a {int(g.eta_anni)} anni.", data)
            if club != "*" and club in self.polisportive:
                self.annota(self.polisportive[club], f"{nome_completo(g)} muore.", data)
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
            if PROB_USCITA_PREMATURA_GIORNALIERA > 0 and caso(PROB_USCITA_PREMATURA_GIORNALIERA):
                self._uscita(g, USCITA_PREMATURA, data, eta_pre)
                rapporto["usciti"] += 1
                continue
            if g.eta >= g.etamorte:
                self._uscita(g, DECESSO, data, eta_pre)
                rapporto["morti"] += 1
                continue
            if not g.ritirato and g.eta >= g.etaritiro:
                g.ritirato = True
                self.giocatori_ritirati_sessione.append((gid, f"RITIRO: {nome_completo(g)}(ID:{gid}) a {formatta_eta_sim(g.eta)} sim."))
                self.annota(g, f"Si ritira dall'attività, a {int(g.eta_anni)} anni.", data)
                if g.appartenenza != "*" and g.appartenenza in self.polisportive:
                    self.annota(self.polisportive[g.appartenenza], f"{nome_completo(g)} si ritira dall'attività.", data)
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
        ripartono, i giocatori invecchiano, gli autonomi si allenano, le polisportive del computer
        tesserano, espellono, chiudono e nascono, poi nascono i giocatori nuovi e si ricalcolano
        valori e glorie.
        """
        for p in self.polisportive.values():
            p.movimenti_oggi = 0
        self._fai_invecchiare(data, rapporto)
        vivi = [g for gid, g in self.giocatori.items() if gid not in self._ids_morti_processati_sessione]
        for g in vivi:
            if not g.ritirato and not g.infortunato and int(g.puntiesperienza or 0) > 0:
                if g.appartenenza == "*" or (g.appartenenza in self.polisportive and self.polisportive[g.appartenenza].is_cpu_controlled):
                    xp_pre = g.puntiesperienza
                    esegui_auto_allenamento(g, data)
                    if g.puntiesperienza < xp_pre:
                        rapporto["autoallenati"] += 1
        tesserati, espulsi = self._esegui_logica_cpu_polisportive(data)
        rapporto["tesserati_cpu"] += tesserati
        rapporto["espulsi_cpu"] += espulsi
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
                              (rapporto["tesserati_cpu"], "* CPU Tesserati"), (rapporto["espulsi_cpu"], "* CPU Espulsi")):
            if numero > 0:
                self.notifica(f"{testo}: {numero}")
        self.notifica("-" * 30)
