"""
Il mondo di MESS: giocatori, polisportive e il tempo che scorre.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 2 del piano, dallo smontaggio della classe Simulatore di sd.py:
qui resta tutto ciò che il mondo fa da solo, cioè l'avanzamento del tempo con invecchiamento,
guarigioni, ritiri, morti e nascite, l'autoallenamento e la vita delle polisportive del computer.
Le regole sono quelle del vecchio file, con i loro difetti: quelli del tempo, problema P3, si
correggono alla tappa 6, quelli delle polisportive, problemi P4 e P7, alla tappa 7.
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
    MAPPA_FLAG_SOMMARIO,
    MAX_NUOVI_GIOCATORI_PER_AVVIO,
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
from utilita import adesso, caso, converti_in_tempo, formatta_eta_sim

ORE_PER_TICK = 8


def _silenzio(*_args, **_kwargs):
    """Al posto di notifica quando chi usa il mondo non la passa."""


class Mondo:
    def __init__(self, notifica=None):
        self.notifica = notifica or _silenzio
        self.giocatori = {}
        self.polisportive = {}
        self.miapolisportiva_attiva = None
        ora = adesso()
        self.datetime_ultimo_run_reale = ora - datetime.timedelta(days=1)
        self.datetime_corrente_simulazione = ora
        self.nuovi_giocatori_sessione = []
        self.giocatori_ritirati_sessione = []
        self.giocatori_morti_sessione = []
        self._ids_morti_processati_sessione = set()
        self.risultati_ultima_ricerca = []

    # Probabilità e ricerche.

    @staticmethod
    def probabilita_accettazione(g_off, g_rich):
        return probabilita_accettazione(g_off, g_rich)

    def trova_giocatori_liberi_ordinati(self):
        """I giocatori liberi, non ritirati e vivi, dal più forte al più debole."""
        liberi = {gid: g for gid, g in self.giocatori.items() if g.appartenenza == "*" and not g.ritirato and gid not in self._ids_morti_processati_sessione}
        return dict(sorted(liberi.items(), key=lambda item: item[1].indice_collettivo_valore, reverse=True))

    def trova_prossimo_id_libero(self):
        """Il primo identificativo intero libero partendo da 1. Riusa quelli dei morti: problema P5, tappa 3."""
        next_id = 1
        while next_id in self.giocatori:
            next_id += 1
        return next_id

    # Nascite e polisportive del computer.

    def crea_giocatori_casuali(self, quanti, dt_creaz):
        """Crea il numero indicato di giocatori nuovi e li annota fra i nuovi della sessione."""
        if quanti <= 0:
            return
        self.notifica(f" -> Generazione {quanti} nuovi giocatori...")
        n_cr = 0
        for _ in range(quanti):
            new_id = self.trova_prossimo_id_libero()
            is_ipo = caso(PROBABILITA_IPOVEDENTE_CREAZIONE)
            self.giocatori[new_id] = Giocatore(id_giocatore=new_id, datetime_creazione_sim=dt_creaz, ipovedente=is_ipo)
            self.nuovi_giocatori_sessione.append(new_id)
            n_cr += 1
        self.notifica(f" -> Creati {n_cr} nuovi giocatori.")

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
        poli = self.polisportive.get(nome_p)
        if not poli or not poli.is_cpu_controlled:
            return False
        eta_str = formatta_eta_sim(int((dt_chiusura - poli.datetime_creazione_sim).total_seconds() / (24 * 3600)))
        self.notifica(f"** Evento ({dt_chiusura:%Y-%m-%d %H:%M}): Chiusura Poli CPU '{nome_p}' (Età: {eta_str}, G:{poli.gloria}, T:{len(poli.tesserati)}) **")
        n_lib = 0
        for gid in list(poli.tesserati):
            if gid in self.giocatori:
                self.giocatori[gid].appartenenza = "*"
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

    def _esegui_logica_cpu_polisportive(self):
        """Le polisportive del computer tesserano i liberi più forti alla loro portata ed espellono il più debole a rosa piena."""
        liberi = self.trova_giocatori_liberi_ordinati()
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
                ids_lib_rim = list(liberi.keys())
                if not ids_lib_rim:
                    break
                for gid_c in ids_lib_rim:
                    if gid_c not in liberi:
                        continue
                    cand = liberi[gid_c]
                    g_r = cand.gloria_richiesta
                    g_p = int(g_r * .9) if cand.ipovedente else g_r
                    if cand.appartenenza == "*" and g_p <= poli.gloria:
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
                self.giocatori[pegg_gid].appartenenza = "*"
                n_esp_cpu_tot += 1
        return n_tess_cpu_tot, n_esp_cpu_tot

    def aggiorna_stato_polisportive(self):
        """Ricalcola indice dei tesserati e gloria di tutte le polisportive."""
        self.notifica("Aggiornamento stato polisportive...")
        if self.polisportive:
            n_agg = 0
            for nome_p in list(self.polisportive.keys()):
                if nome_p in self.polisportive:
                    p = self.polisportive[nome_p]
                    p.aggiorna_ict(self.giocatori, self._ids_morti_processati_sessione)
                    p.aggiorna_gloria(self.giocatori, self._ids_morti_processati_sessione)
                    n_agg += 1
            self.notifica(f"-> Stato ricalcolato per {n_agg} polisportive.")

    # Uscite di scena.

    def _logga_uscita_giocatore(self, giocatore, motivo, dt_evento_sim):
        """Scrive l'uscita di un giocatore nel registro storico delle vecchie glorie."""
        giocatore.aggiorna_aspetto()
        eta_mom = formatta_eta_sim(giocatore.eta, False)
        flags = ", ".join([f for a, f in MAPPA_FLAG_SOMMARIO.items() if getattr(giocatore, a, False)]) or "Nessuno"
        log = [f"--- {motivo.upper()} - GID: {giocatore.id} ---", f"Nome: {giocatore.nome} {giocatore.cognome}", f"Età (Sim): {eta_mom}",
               f"Sesso: {'Uomo' if giocatore.sesso == 'm' else 'Donna'}", f"Club Finale: {'Libero' if giocatore.appartenenza == '*' else giocatore.appartenenza}",
               f"Fisico: {giocatore.altezza} cm / {giocatore.peso} kg", f"Flags: {flags}",
               f"Scoperto (Sim): {giocatore.datetime_creazione_sim:%Y-%m-%d %H:%M}", f"Scoperto (Reale): {giocatore.datacreazione_reale:%Y-%m-%d %H:%M}",
               f"Versione Creazione: {getattr(giocatore, 'versione', 'N/D')}", f"Evento (Sim): {dt_evento_sim:%Y-%m-%d %H:%M}",
               f"Evento (Reale): {adesso():%Y-%m-%d %H:%M:%S}",
               f"Stats Partite: G={giocatore.partitevinte + giocatore.partiteperse}, V={giocatore.partitevinte}",
               f"Stats Sets: G={giocatore.setsvinti + giocatore.setspersi}, V={giocatore.setsvinti}",
               f"Stats Goals: F={giocatore.goalsfatti}, S={giocatore.goalssubiti}", f"XP Finali: {int(giocatore.puntiesperienza or 0)}",
               f"ICV Finale: {giocatore.indice_collettivo_valore:.2f}", "-" * 50 + "\n"]
        try:
            with open(percorsi.percorso(NOME_FILE_LOG_USCITE), "a", encoding="utf-8") as f:
                f.write("\n".join(log))
        except OSError as e:
            self.notifica(f"ERR scrittura log uscita GID {giocatore.id}: {e}")

    # Il tempo.

    def testo_prossimo_sblocco(self):
        """Quando arriverà il prossimo avanzamento del mondo, se non è ancora arrivato; altrimenti None."""
        if not isinstance(self.datetime_ultimo_run_reale, datetime.datetime):
            return None
        ora_sblocco = self.datetime_ultimo_run_reale + datetime.timedelta(hours=ORE_PER_TICK)
        now = adesso()
        if now >= ora_sblocco:
            return None
        h, m, _s = converti_in_tempo((ora_sblocco - now).total_seconds())
        return f"INFO: Prox aggiornamento sim alle {ora_sblocco:%H:%M:%S del %d/%m/%Y} (tra {h}h {m}m)."

    def _notifica_prossimo_sblocco(self):
        testo = self.testo_prossimo_sblocco()
        if testo:
            self.notifica(testo)

    def processa_tempo_trascorso(self):
        """Fa avanzare il mondo di un giorno simulato per ogni 8 ore reali trascorse dall'ultimo avanzamento."""
        now = adesso()
        if not isinstance(self.datetime_ultimo_run_reale, datetime.datetime):
            self.notifica("WARN: dt_ultimo_run non valido. Reset.")
            self.datetime_ultimo_run_reale = now - datetime.timedelta(hours=ORE_PER_TICK)
        delta_r = now - self.datetime_ultimo_run_reale
        ticks = int(delta_r.total_seconds() // (ORE_PER_TICK * 3600)) if delta_r.total_seconds() > 0 else 0
        if ticks <= 0:
            self._notifica_prossimo_sblocco()
            return
        self.notifica(f"\n--- Processando {ticks} tick da 8h ({delta_r}) ---")
        for p in self.polisportive.values():
            p.movimenti_oggi = 0
        # Tre conti diversi del tempo, problema P3: un giorno per tick per età e salute, circa un
        # decimo di giorno per tick per le date di fondazione delle polisportive nuove.
        gg_tick = ANNO_SIMULAZIONE_GIORNI / (365.25 * 3.) if ANNO_SIMULAZIONE_GIORNI > 0 else 0.0
        gg_sim_i = int(ticks * 1.0)
        dt_sim_s = self.datetime_corrente_simulazione
        dt_sim_e = dt_sim_s + datetime.timedelta(days=float(gg_sim_i))
        self.notifica(f"Avanzamento sim: +{gg_sim_i} giorni -> {dt_sim_e:%Y-%m-%d %H:%M}")
        ids_proc = list(self.giocatori.keys())
        n_rit, n_usciti_prem, n_dec = self._fai_invecchiare(ids_proc, gg_sim_i, dt_sim_e)
        self.notifica("Esecuzione azioni aggregate...")
        ids_vivi = [gid for gid in ids_proc if gid not in self._ids_morti_processati_sessione and gid in self.giocatori]
        n_autoall = 0
        for gid in ids_vivi:
            g = self.giocatori[gid]
            if not g.ritirato and not g.infortunato and int(g.puntiesperienza or 0) > 0:
                if g.appartenenza == "*" or (g.appartenenza in self.polisportive and self.polisportive[g.appartenenza].is_cpu_controlled):
                    xp_pre = g.puntiesperienza
                    esegui_auto_allenamento(g)
                    if g.puntiesperienza < xp_pre:
                        n_autoall += 1
        if n_autoall > 0:
            self.notifica(f"-> {n_autoall} giocatori si sono auto-allenati.")
        n_tess_cpu, n_esp_cpu = self._esegui_logica_cpu_polisportive()
        n_chiuse = 0
        n_cr_ciclo = 0
        n_gioc_att = len(ids_vivi)
        lim_poli = (n_gioc_att / GIOCATORI_ATTIVI_PER_POLI_CPU_TARGET) if n_gioc_att > 0 and GIOCATORI_ATTIVI_PER_POLI_CPU_TARGET > 0 else 0.
        for nome_p in list(self.polisportive.keys()):
            if nome_p in self.polisportive and self.polisportive[nome_p].is_cpu_controlled and self._controlla_chiusura_poli_cpu(self.polisportive[nome_p], dt_sim_e):
                n_chiuse += 1
        for k in range(ticks):
            if len(self.polisportive) < lim_poli and caso(PROB_CREAZIONE_POLI_CPU_PER_TICK):
                dt_tick = dt_sim_s + datetime.timedelta(days=(k + 1) * gg_tick)
                if self.crea_polisportiva_cpu(dt_tick):
                    n_cr_ciclo += 1
        self.datetime_corrente_simulazione = dt_sim_e
        self.datetime_ultimo_run_reale = now
        for gid in ids_vivi:
            if gid in self.giocatori:
                self.giocatori[gid].aggiorna_icv()
        self.nuovi_giocatori_sessione.clear()
        n_nuovi_creati_ciclo = 0
        inf, sup = CREA_NUOVI_PER_TICK_RANGE
        min_n = inf * ticks
        max_n = sup * ticks
        n_des = random.randrange(min_n, max_n + 1) if max_n >= min_n else min_n
        n_crea = min(n_des, MAX_NUOVI_GIOCATORI_PER_AVVIO)
        if n_crea < n_des:
            self.notifica(f"INFO: Nuovi limitati a {MAX_NUOVI_GIOCATORI_PER_AVVIO} (desiderati: {n_des}).")
        if n_crea > 0:
            self.crea_giocatori_casuali(n_crea, self.datetime_corrente_simulazione)
            n_nuovi_creati_ciclo = len(self.nuovi_giocatori_sessione)
        self.aggiorna_stato_polisportive()
        self.notifica("\n--- Riepilogo Avanzamento Tick ---")
        for numero, testo in ((n_rit, "* Ritirati (età)"), (n_usciti_prem, "* Usciti Prematuramente"), (n_dec, "* Deceduti (età)"),
                              (n_nuovi_creati_ciclo, "* Nuovi giocatori"), (n_chiuse, "* Poli CPU chiuse"), (n_cr_ciclo, "* Poli CPU create"),
                              (n_tess_cpu, "* CPU Tesserati"), (n_esp_cpu, "* CPU Espulsi")):
            if numero > 0:
                self.notifica(f"{testo}: {numero}")
        self.notifica("-" * 30)

    def _fai_invecchiare(self, ids_proc, gg_sim_i, dt_sim_e):
        """Guarigioni, età, declino, uscite premature, morti e ritiri dei giorni trascorsi. Restituisce i conteggi."""
        ids_morti_c, ids_rit_c = set(), set()
        self.giocatori_morti_sessione.clear()
        self.giocatori_ritirati_sessione.clear()
        self._ids_morti_processati_sessione.clear()
        n_gua, n_dec, n_rit, n_usciti_prem = 0, 0, 0, 0
        for gid in ids_proc:
            if gid not in self.giocatori:
                continue
            g = self.giocatori[gid]
            eta_pre = g.eta
            if g.infortunato and g.infortunio_fine_datetime and dt_sim_e >= g.infortunio_fine_datetime:
                g.infortunato = False
                g.infortunio_fine_datetime = None
                n_gua += 1
            g.eta += gg_sim_i
            if gg_sim_i > 0:
                g._applica_declino_aggregato(gg_sim_i)
            if gg_sim_i > 0 and PROB_USCITA_PREMATURA_GIORNALIERA > 0:
                prob_non_uscire_n = pow(1.0 - (PROB_USCITA_PREMATURA_GIORNALIERA / 100.0), gg_sim_i)
                prob_uscire_n = (1.0 - prob_non_uscire_n) * 100.0
                if caso(prob_uscire_n) and gid not in ids_morti_c:
                    motivo_uscita = "Uscita Prematura"
                    msg = f"{motivo_uscita.upper()}: {g.nome} {g.cognome}(ID:{gid}) lascia il mondo a {formatta_eta_sim(g.eta)} sim."
                    self.giocatori_morti_sessione.append((gid, msg))
                    self._ids_morti_processati_sessione.add(gid)
                    ids_morti_c.add(gid)
                    n_usciti_prem += 1
                    g.ritirato = True
                    if g.appartenenza != "*" and g.appartenenza in self.polisportive:
                        self.polisportive[g.appartenenza].rimuovi_tesserato(gid, g.indice_collettivo_valore)
                    g.appartenenza = "*"
                    self._logga_uscita_giocatore(g, motivo_uscita, dt_sim_e)
                    continue
            if g.eta >= g.etamorte and gid not in ids_morti_c:
                # Problema P4, tappa 7: il morto viene liberato ma resta fra i tesserati della sua polisportiva.
                motivo_uscita = "Decesso Naturale"
                msg = f"DECESSO (Età): {g.nome} {g.cognome}(ID:{gid}) tra {formatta_eta_sim(eta_pre)} e {formatta_eta_sim(g.eta)} sim."
                self.giocatori_morti_sessione.append((gid, msg))
                self._ids_morti_processati_sessione.add(gid)
                ids_morti_c.add(gid)
                n_dec += 1
                g.ritirato = True
                g.appartenenza = "*"
                self._logga_uscita_giocatore(g, motivo_uscita, dt_sim_e)
                continue
            if not g.ritirato and g.eta >= g.etaritiro and gid not in ids_rit_c:
                msg = f"RITIRO: {g.nome} {g.cognome}(ID:{gid}) a {formatta_eta_sim(g.eta)} sim."
                self.giocatori_ritirati_sessione.append((gid, msg))
                ids_rit_c.add(gid)
                n_rit += 1
                g.ritirato = True
        for numero, testo in ((n_gua, "guariti"), (n_usciti_prem, "giocatori usciti prematuramente"), (n_dec, "deceduti per età"), (n_rit, "ritirati per età")):
            if numero > 0:
                self.notifica(f"-> {numero} {testo}.")
        self._ids_morti_processati_sessione.update(ids_morti_c)
        return n_rit, n_usciti_prem, n_dec
