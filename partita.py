"""
Il motore di partita di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 2 del piano, dallo smontaggio di sd.py. Le regole e i numeri
sono quelli del vecchio motore, difetti compresi: la catena degli esiti che trasforma quasi ogni
azione in fallo, il problema P1, e la resistenza del primo giocatore passata a chi batte, si
correggono alla tappa 8, misurando prima e dopo con strumenti/banco_partite.py.
Il motore non stampa e non chiede nulla: le righe che il vecchio sd.py stampava le consegna alla
funzione mostra, e dove aspettava un tasto chiama la funzione pausa. Le passa chi lo usa; se non
le passa, il motore lavora in silenzio.
"""

import datetime
import math
import random

import percorsi
from costanti import (
    AGING_PEAK_AGE_GIORNI,
    ANNO_SIMULAZIONE_GIORNI,
    CARATTERISTICHE_ATTACCO_BASE,
    ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI,
    ETA_MAX_CALO_RES,
    ETA_MAX_PROB_INFORTUNIO_ANNI,
    ETA_MIN_CALO_RES,
    FATTORE_BONUS_DIFESA_SU_RITORNO_FACILE,
    ICV_DIFF_PERC_UNDERDOG,
    INFORTUNIO_DURATA_MAX_GIORNI_ETA,
    INFORTUNIO_DURATA_MIN_GIORNI,
    INFORTUNIO_MALUS_MAX_RESISTENZA,
    MAPPA_CONTRASTO_SKILL,
    MARGINE_DIFESA,
    MARGINE_GOAL,
    MAX_TOTALE_PRECISIONE_RESISTENZA,
    MODALITA_OUTPUT_CONSOLE,
    MODALITA_OUTPUT_FILE,
    MODALITA_OUTPUT_RISULTATO,
    NOME_FILE_LOG_PARTITE,
    PROB_FALLO_SU_FALLIMENTO_NORMALE,
    PROB_INFORTUNIO_AUMENTO_MAX_PERC,
    PROB_INFORTUNIO_BASE_PER_PARTITA,
    PROB_PALLAMORTA_SU_FALLIMENTO_NORMALE,
    PUNTI_LIMITE_SET,
    PUNTI_PER_FALLO_AVVERSARIO,
    PUNTI_PER_GOAL,
    PUNTI_VANTAGGIO_NECESSARI,
    PUNTI_VITTORIA_SET_BASE,
    SCALING_K_DIFESA_ICV,
    SCALING_MODIFICATORE_MAX,
    SCALING_RANGE_DELTA_EFF,
    SCALING_SOGLIA_BASE,
    SERVIZI_CONSECUTIVI_PER_GIOCATORE,
    TARGET_MAX_PERC_RES_SET5,
    TARGET_MIN_PERC_RES_SET5,
    VALORE_AZIONE_BONUS_BATTUTA,
    XP_BONUS_TORNEO,
    XP_BONUS_UNDERDOG,
    XP_SCONFITTA_0_2,
    XP_SCONFITTA_0_3,
    XP_SCONFITTA_1_2,
    XP_SCONFITTA_1_3,
    XP_SCONFITTA_2_3,
    XP_VITTORIA_2_0,
    XP_VITTORIA_2_1,
    XP_VITTORIA_3_0,
    XP_VITTORIA_3_1,
    XP_VITTORIA_3_2,
)
from utilita import adesso, caso

FALLI = ("FalloCritico", "Fallo")
COLPI_A_SPONDA = ('singolaspondasx_base', 'singolaspondadx_base', 'doppiaspondasx_base', 'doppiaspondadx_base', 'triplaspondasx_base', 'triplaspondadx_base')


def _silenzio(*_args, **_kwargs):
    """Al posto di mostra e pausa quando chi usa il motore non le passa."""


class MotorePartita:
    """Gioca le partite fra i giocatori di un mondo, di cui legge i giocatori e la data simulata."""

    def __init__(self, mondo, mostra=None, pausa=None):
        self.mondo = mondo
        self.mostra = mostra or _silenzio
        self.pausa = pausa or _silenzio

    @property
    def giocatori(self):
        return self.mondo.giocatori

    def gioca_partita(self, id_g1, id_g2, num_set_target, modalita_output=MODALITA_OUTPUT_RISULTATO, info_torneo=None):
        """Simula una partita completa tra due giocatori e ne restituisce il risultato."""
        mostra = self.mostra
        mostra(f"\n--- Inizio Partita: ID {id_g1} vs ID {id_g2} (Al meglio dei {num_set_target} set) ---")
        risultato_partita = {
            'id_originale_g1': id_g1, 'id_originale_g2': id_g2, 'num_set_target': num_set_target,
            'vincitore_id': None, 'perdente_id': None, 'punteggio_set': [],
            'stats_g1': {'goal': 0, 'falli_fatti': 0, 'falli_subiti': 0},
            'stats_g2': {'goal': 0, 'falli_fatti': 0, 'falli_subiti': 0},
            'log_partita_completa': [], 'log_path': None, 'error': None
        }
        log_partita = risultato_partita['log_partita_completa']
        errore = None
        if id_g1 not in self.giocatori or id_g2 not in self.giocatori:
            errore = "ID giocatore non valido."
        elif id_g1 == id_g2:
            errore = "I giocatori devono essere diversi."
        else:
            g1 = self.giocatori[id_g1]
            g2 = self.giocatori[id_g2]
            if g1.ritirato or g2.ritirato:
                errore = "Uno o entrambi ritirati."
            elif g1.infortunato or g2.infortunato:
                errore = "Uno o entrambi infortunati."
        if errore:
            risultato_partita['error'] = errore
            mostra(f"ERRORE: {errore}")
            return risultato_partita
        set_vinti_g1, set_vinti_g2 = 0, 0
        set_da_vincere = math.ceil(num_set_target / 2.0)
        servizio_attuale_id = random.choice([id_g1, id_g2])
        filepath = None
        if modalita_output == MODALITA_OUTPUT_FILE:
            filepath = percorsi.percorso(NOME_FILE_LOG_PARTITE)
            timestamp = adesso().strftime("%Y-%m-%d %H:%M:%S")
            header = f"\n=== PARTITA INIZIATA: {timestamp} ===\n"
            header += f"  {g1.nome} {g1.cognome} (ID:{id_g1}) vs {g2.nome} {g2.cognome} (ID:{id_g2})\n"
            header += f"  Al meglio dei {num_set_target} set\n" + "=" * 30 + "\n"
            try:
                with open(filepath, "a", encoding="utf-8") as f:
                    f.write(header)
                risultato_partita['log_path'] = filepath
            except OSError as e:
                mostra(f"ERRORE apertura file log '{NOME_FILE_LOG_PARTITE}': {e}")
                modalita_output = MODALITA_OUTPUT_RISULTATO
                filepath = None
        numero_set_attuale = 1
        try:
            while set_vinti_g1 < set_da_vincere and set_vinti_g2 < set_da_vincere:
                if modalita_output != MODALITA_OUTPUT_RISULTATO:
                    log_partita.append(f"\n-- Set {numero_set_attuale} -- (Servizio: ID {servizio_attuale_id})")
                if modalita_output == MODALITA_OUTPUT_CONSOLE:
                    mostra(f"\n-- Inizio Set {numero_set_attuale} -- (Servizio: ID {servizio_attuale_id})")
                punteggio_set, vincitore_set_id = self._gioca_set(g1, g2, servizio_attuale_id, risultato_partita['stats_g1'],
                                                                  risultato_partita['stats_g2'], log_partita, modalita_output, numero_set_attuale)
                risultato_partita['punteggio_set'].append(punteggio_set)
                if vincitore_set_id == id_g1:
                    set_vinti_g1 += 1
                elif vincitore_set_id == id_g2:
                    set_vinti_g2 += 1
                if modalita_output != MODALITA_OUTPUT_RISULTATO:
                    log_partita.append(f"-- Fine Set {numero_set_attuale}: {punteggio_set[0]}-{punteggio_set[1]} (Vincitore: ID {vincitore_set_id}) --")
                    log_partita.append(f"Parziale Partita: {set_vinti_g1} - {set_vinti_g2}\n")
                if modalita_output == MODALITA_OUTPUT_CONSOLE:
                    mostra(f"-- Fine Set {numero_set_attuale}: {punteggio_set[0]}-{punteggio_set[1]} (Vincitore Set: ID {vincitore_set_id}) --")
                    mostra(f"Partita: {set_vinti_g1} - {set_vinti_g2}")
                servizio_attuale_id = id_g2 if servizio_attuale_id == id_g1 else id_g1
                numero_set_attuale += 1
        except (EOFError, KeyboardInterrupt):
            risultato_partita['error'] = "Partita interrotta dall'utente."
            mostra(f"\n{risultato_partita['error']}")
        if risultato_partita['error'] is None:
            if set_vinti_g1 > set_vinti_g2:
                risultato_partita['vincitore_id'], risultato_partita['perdente_id'] = id_g1, id_g2
            else:
                risultato_partita['vincitore_id'], risultato_partita['perdente_id'] = id_g2, id_g1
            vincitore = self.giocatori[risultato_partita['vincitore_id']]
            mostra("\n=== PARTITA TERMINATA ===")
            mostra(f"Vincitore: {vincitore.nome} {vincitore.cognome} (ID:{vincitore.id})")
            mostra(f"Punteggio Finale: {set_vinti_g1} - {set_vinti_g2}")
            mostra(f"Set: {risultato_partita['punteggio_set']}")
            self._aggiorna_statistiche_post_partita(risultato_partita, info_torneo)
        if filepath:
            self._chiudi_cronaca(filepath, risultato_partita, log_partita, set_vinti_g1, set_vinti_g2)
        return risultato_partita

    def _chiudi_cronaca(self, filepath, risultato_partita, log_partita, set_vinti_g1, set_vinti_g2):
        """Scrive in coda al file delle cronache il racconto della partita e il suo esito."""
        footer = f"\n=== PARTITA {'TERMINATA' if risultato_partita['error'] is None else 'INTERROTTA'} ===\n"
        if risultato_partita.get('vincitore_id'):
            v_id = risultato_partita['vincitore_id']
            v_nome = self.giocatori[v_id].nome + " " + self.giocatori[v_id].cognome
            footer += f"Vincitore: ID {v_id} ({v_nome})\n"
            footer += f"Punteggio: {set_vinti_g1} - {set_vinti_g2}\n"
        footer += f"Set: {risultato_partita.get('punteggio_set', [])}\n"
        for chiave_id, chiave_stats, nome in (('id_originale_g1', 'stats_g1', 'G1'), ('id_originale_g2', 'stats_g2', 'G2')):
            stats = risultato_partita[chiave_stats]
            footer += f"Stats {nome} (ID:{risultato_partita[chiave_id]}): Goal={stats.get('goal', 0)}, Falli Fatti={stats.get('falli_fatti', 0)}, Falli Subiti={stats.get('falli_subiti', 0)}\n"
        if risultato_partita['error']:
            footer += f"Esito: {risultato_partita['error']}\n"
        footer += "=" * 30 + "\n"
        try:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write("\n".join(log_partita) + footer)
        except OSError as e:
            self.mostra(f"ERRORE scrittura file log finale: {e}")
            return
        if risultato_partita['error'] is None:
            self.mostra(f"Cronaca completa salvata in: {risultato_partita['log_path']}")

    def _gioca_set(self, g1, g2, id_servizio_inizio, stats_g1, stats_g2, log_partita, modalita_output, numero_set_attuale):
        """Simula un singolo set e ne restituisce il punteggio e il vincitore."""
        punti_g1, punti_g2 = 0, 0
        servizio_corrente_id = id_servizio_inizio
        servizi_giocati_da_attuale = 0
        res_perc_g1 = self._calcola_resistenza_set(g1, numero_set_attuale)
        res_perc_g2 = self._calcola_resistenza_set(g2, numero_set_attuale)
        if modalita_output != MODALITA_OUTPUT_RISULTATO:
            log_partita.append(f"    Res Inizio Set: G1({g1.id}): {res_perc_g1 * 100:.1f}%, G2({g2.id}): {res_perc_g2 * 100:.1f}%")
        while True:
            vincitore_set_id = None
            if punti_g1 >= PUNTI_LIMITE_SET:
                vincitore_set_id = g1.id
            elif punti_g2 >= PUNTI_LIMITE_SET:
                vincitore_set_id = g2.id
            elif punti_g1 >= PUNTI_VITTORIA_SET_BASE and punti_g1 >= punti_g2 + PUNTI_VANTAGGIO_NECESSARI:
                vincitore_set_id = g1.id
            elif punti_g2 >= PUNTI_VITTORIA_SET_BASE and punti_g2 >= punti_g1 + PUNTI_VANTAGGIO_NECESSARI:
                vincitore_set_id = g2.id
            if vincitore_set_id is not None:
                break
            servitore = g1 if servizio_corrente_id == g1.id else g2
            risponditore = g2 if servizio_corrente_id == g1.id else g1
            if modalita_output != MODALITA_OUTPUT_RISULTATO:
                log_riga = f"  Pti: {punti_g1}-{punti_g2}. Serv: ID {servitore.id} ({servitore.nome[0]}.)"
                if modalita_output == MODALITA_OUTPUT_CONSOLE:
                    self.mostra(log_riga)
                log_partita.append(log_riga)
            # Difetto del vecchio motore, da correggere alla tappa 8: le resistenze passano
            # sempre nell'ordine di g1 e g2, anche quando batte g2.
            vincitore_punto_id, tipo_punto, _dettaglio = self._gioca_punto(
                g1, g2, servitore, risponditore, stats_g1, stats_g2, log_partita, modalita_output,
                res_perc_g1, res_perc_g2
            )
            if tipo_punto == 'PallaMorta':
                if modalita_output != MODALITA_OUTPUT_RISULTATO:
                    log_partita.append("      -> Punto da Ripetere (Palla Morta)")
                continue
            punti_da_assegnare = PUNTI_PER_GOAL if tipo_punto == 'Goal' else PUNTI_PER_FALLO_AVVERSARIO if tipo_punto == 'Fallo' else 0
            if vincitore_punto_id == g1.id:
                punti_g1 += punti_da_assegnare
            elif vincitore_punto_id == g2.id:
                punti_g2 += punti_da_assegnare
            servizi_giocati_da_attuale += 1
            if servizi_giocati_da_attuale >= SERVIZI_CONSECUTIVI_PER_GIOCATORE:
                servizio_corrente_id = g2.id if servizio_corrente_id == g1.id else g1.id
                servizi_giocati_da_attuale = 0
            if modalita_output == MODALITA_OUTPUT_CONSOLE:
                self.pausa("... (Invio per prossimo punto)")
        return (punti_g1, punti_g2), vincitore_set_id

    def _fallimento_normale(self, log_attivo, log_partita, debug_log_punto, dettaglio_fallo, fallito, id_chi, id_altro, stats_altro, stats_chi):
        """
        Dopo un'azione fallita: fallo, palla morta o palla facile per l'altro. Nel vecchio motore
        questo ramo non si raggiunge mai, perché il dado non restituisce l'esito Fallimento.
        Restituisce il risultato del punto, oppure None se la palla torna facile all'altro.
        """
        rand_fallimento = random.uniform(0, 100)
        if rand_fallimento < PROB_FALLO_SU_FALLIMENTO_NORMALE:
            dettaglio = dettaglio_fallo
            if log_attivo:
                log_partita.extend(debug_log_punto)
                log_partita.append(f"      -> {dettaglio} ID {id_chi}! Punto a ID {id_altro}.")
            self._aggiorna_statistiche_punto(stats_altro, stats_chi, 'Fallo')
            return id_altro, 'Fallo', dettaglio
        if rand_fallimento < PROB_FALLO_SU_FALLIMENTO_NORMALE + PROB_PALLAMORTA_SU_FALLIMENTO_NORMALE:
            if log_attivo:
                log_partita.extend(debug_log_punto)
                log_partita.append(f"      -> {fallito} ID {id_chi}. Palla Morta.")
            return 0, 'PallaMorta', None
        if log_attivo:
            log_partita.extend(debug_log_punto)
            log_partita.append(f"      -> {fallito} ID {id_chi}. Palla facile per ID {id_altro}!")
        return None

    def _gioca_punto(self, g1, g2, servitore, risponditore, stats_g1, stats_g2, log_partita, modalita_output, res_perc_servitore, res_perc_risponditore):
        """Simula un singolo punto, dalla battuta alla fine dello scambio."""
        debug_log_punto = []
        log_attivo = modalita_output != MODALITA_OUTPUT_RISULTATO
        id_servitore = servitore.id
        id_risponditore = risponditore.id
        id_g1_orig = g1.id
        if log_attivo:
            log_partita.append(f"    Serve ID {id_servitore} ({servitore.nome[0]}. Res:{res_perc_servitore * 100:.0f}%)"
                               f" vs ID {id_risponditore} ({risponditore.nome[0]}. Res:{res_perc_risponditore * 100:.0f}%)")
        # Battuta.
        skill_battuta_base = random.choice(['battutasx_base', 'battutadx_base'])
        azione_descr_batt = f"Battuta ({skill_battuta_base.replace('_base', '')})"
        if log_attivo:
            debug_log_punto.append(f"    {azione_descr_batt} ID {id_servitore}")
        valore_battuta = self._calcola_valore_azione(servitore, "Battuta", skill_battuta_base, res_perc_servitore, debug_log=debug_log_punto)
        risultato_battuta, _ = self._risolvi_azione_vs_dado(servitore, risponditore, valore_battuta, azione_descr_batt, debug_log_punto)
        stats_servitore = stats_g1 if id_servitore == id_g1_orig else stats_g2
        stats_risponditore = stats_g1 if id_risponditore == id_g1_orig else stats_g2
        if risultato_battuta in FALLI:
            dettaglio = f"Fallo Battuta ({risultato_battuta})"
            if log_attivo:
                log_partita.extend(debug_log_punto)
                log_partita.append(f"      -> {dettaglio}! Punto a ID {id_risponditore}.")
            self._aggiorna_statistiche_punto(stats_risponditore, stats_servitore, 'Fallo')
            return id_risponditore, 'Fallo', dettaglio
        if risultato_battuta == "Perfetto":
            dettaglio = f"Ace Battuta ({skill_battuta_base.replace('_base', '')})"
            if log_attivo:
                log_partita.extend(debug_log_punto)
                log_partita.append(f"      -> {dettaglio}! Goal ID {id_servitore}!")
            self._aggiorna_statistiche_punto(stats_servitore, stats_risponditore, 'Goal')
            return id_servitore, 'Goal', dettaglio
        # Scambio.
        attaccante_corrente = risponditore
        difensore_corrente = servitore
        fattore_diff_difesa_ritorno = 1.0
        ultimo_attacco_base = skill_battuta_base
        max_scambi_per_punto = 50
        num_scambi = 0
        while num_scambi < max_scambi_per_punto:
            num_scambi += 1
            id_att = attaccante_corrente.id
            id_dif = difensore_corrente.id
            res_perc_att = res_perc_risponditore if id_att == id_risponditore else res_perc_servitore
            res_perc_dif = res_perc_servitore if id_att == id_risponditore else res_perc_risponditore
            stats_att = stats_g1 if id_att == id_g1_orig else stats_g2
            stats_dif = stats_g2 if id_att == id_g1_orig else stats_g1
            # Azione dell'attaccante.
            skill_attacco_base = random.choice(CARATTERISTICHE_ATTACCO_BASE)
            nome_colpo = skill_attacco_base.replace('_base', '')
            azione_descr_att = f"Attacco ({nome_colpo}) ID {id_att}"
            if log_attivo:
                debug_log_punto.append(f"    {azione_descr_att}")
            val_attacco = self._calcola_valore_azione(attaccante_corrente, f"Attacco:{nome_colpo}", skill_attacco_base, res_perc_att, debug_log_punto)
            ris_att, _ = self._risolvi_azione_vs_dado(attaccante_corrente, difensore_corrente, val_attacco, azione_descr_att, debug_log_punto)
            if ris_att in FALLI:
                dettaglio = f"Fallo {nome_colpo} ({ris_att})"
                if log_attivo:
                    log_partita.extend(debug_log_punto)
                    log_partita.append(f"      -> {dettaglio} ID {id_att}! Punto a ID {id_dif}.")
                self._aggiorna_statistiche_punto(stats_dif, stats_att, 'Fallo')
                return id_dif, 'Fallo', dettaglio
            if ris_att == "Perfetto":
                dettaglio = f"Attacco Perfetto ({nome_colpo})"
                if log_attivo:
                    log_partita.extend(debug_log_punto)
                    log_partita.append(f"      -> {dettaglio} ID {id_att}! Goal!")
                self._aggiorna_statistiche_punto(stats_att, stats_dif, 'Goal')
                return id_att, 'Goal', dettaglio
            if ris_att != "Successo":
                esito = self._fallimento_normale(log_attivo, log_partita, debug_log_punto, f"Fallo {nome_colpo} (Normale)", f"Attacco Fallito ({nome_colpo})", id_att, id_dif, stats_dif, stats_att)
                if esito is not None:
                    return esito
                attaccante_corrente, difensore_corrente = difensore_corrente, attaccante_corrente
                fattore_diff_difesa_ritorno = FATTORE_BONUS_DIFESA_SU_RITORNO_FACILE
                ultimo_attacco_base = None
                continue
            ultimo_attacco_base = skill_attacco_base
            # Chiusura o difesa primaria.
            chiusura_riuscita = False
            blocco_riuscito = False
            skill_difesa_base = MAPPA_CONTRASTO_SKILL.get(ultimo_attacco_base, 'difesa_base') if ultimo_attacco_base else 'difesa_base'
            nome_difesa = skill_difesa_base.replace('_base', '')
            azione_descr_chius = f"Difesa ({nome_difesa}) ID {id_dif}"
            if log_attivo:
                debug_log_punto.append(f"    {azione_descr_chius}")
            val_difesa_base_calc = self._calcola_valore_azione(difensore_corrente, f"Difesa:{nome_difesa}", skill_difesa_base, res_perc_dif,
                                                               skill_attacco_avversario_base_nome=ultimo_attacco_base, debug_log=debug_log_punto)
            val_chiusura = val_difesa_base_calc * fattore_diff_difesa_ritorno
            if log_attivo and fattore_diff_difesa_ritorno != 1.0:
                tipo_effetto = "Bonus" if fattore_diff_difesa_ritorno > 1.0 else "Malus"
                debug_log_punto.append(f"      > {tipo_effetto} Difesa Ritorno: x{fattore_diff_difesa_ritorno:.2f} -> Val {nome_difesa} Eff: {val_chiusura:.2f}")
            ris_chius, _ = self._risolvi_azione_vs_dado(difensore_corrente, attaccante_corrente, val_chiusura, azione_descr_chius, debug_log_punto)
            if ris_chius in FALLI:
                dettaglio = f"Fallo {nome_difesa} ({ris_chius})"
                if log_attivo:
                    log_partita.extend(debug_log_punto)
                    log_partita.append(f"      -> {dettaglio} ID {id_dif}! Punto a ID {id_att}.")
                self._aggiorna_statistiche_punto(stats_att, stats_dif, 'Fallo')
                return id_att, 'Fallo', dettaglio
            if ris_chius == "Perfetto":
                if log_attivo:
                    debug_log_punto.append(f"      -> Difesa ({nome_difesa}) Perfetta ID {id_dif}!")
                chiusura_riuscita = True
            elif ris_chius == "Successo":
                if val_chiusura >= val_attacco + MARGINE_DIFESA:
                    if log_attivo:
                        debug_log_punto.append(f"      -> Difesa ({nome_difesa}) riuscita!")
                    chiusura_riuscita = True
                elif val_attacco >= val_chiusura + MARGINE_GOAL:
                    dettaglio = f"Goal ({nome_colpo})"
                    if log_attivo:
                        log_partita.extend(debug_log_punto)
                        log_partita.append(f"      -> Attacco supera Difesa! {dettaglio} ID {id_att}!")
                    self._aggiorna_statistiche_punto(stats_att, stats_dif, 'Goal')
                    return id_att, 'Goal', dettaglio
                else:
                    if log_attivo:
                        log_partita.extend(debug_log_punto)
                        log_partita.append("      -> Valori Attacco/Difesa vicini! Palla Morta.")
                    return 0, 'PallaMorta', None
            else:
                esito = self._fallimento_normale(log_attivo, log_partita, debug_log_punto, f"Fallo {nome_difesa} (Normale)", f"Difesa Fallita ({nome_difesa})", id_dif, id_att, stats_att, stats_dif)
                if esito is not None:
                    return esito
                attaccante_corrente, difensore_corrente = difensore_corrente, attaccante_corrente
                fattore_diff_difesa_ritorno = FATTORE_BONUS_DIFESA_SU_RITORNO_FACILE
                ultimo_attacco_base = None
                continue
            # Blocco, dopo una chiusura specifica riuscita.
            skill_blocco_base = None
            if chiusura_riuscita:
                if skill_difesa_base == 'chiusurasx_base':
                    skill_blocco_base = 'bloccosx_base'
                elif skill_difesa_base == 'chiusuradx_base':
                    skill_blocco_base = 'bloccodx_base'
                else:
                    blocco_riuscito = True
            if skill_blocco_base:
                nome_blocco = skill_blocco_base.replace('_base', '')
                azione_descr_blocco = f"Blocco ({nome_blocco}) ID {id_dif}"
                if log_attivo:
                    debug_log_punto.append(f"    {azione_descr_blocco}")
                val_blocco_base = self._calcola_valore_azione(difensore_corrente, f"Blocco:{nome_blocco}", skill_blocco_base, res_perc_dif, debug_log=debug_log_punto)
                val_blocco = val_blocco_base * fattore_diff_difesa_ritorno
                if log_attivo and fattore_diff_difesa_ritorno != 1.0:
                    debug_log_punto.append(f"      > Fattore Difesa Ritorno: x{fattore_diff_difesa_ritorno:.2f} -> Val Blocco Eff: {val_blocco:.2f}")
                ris_blocco, _ = self._risolvi_azione_vs_dado(difensore_corrente, attaccante_corrente, val_blocco, azione_descr_blocco, debug_log_punto)
                if ris_blocco in FALLI:
                    dettaglio = f"Fallo Blocco ({nome_blocco}, {ris_blocco})"
                    if log_attivo:
                        log_partita.extend(debug_log_punto)
                        log_partita.append(f"      -> {dettaglio} ID {id_dif}! Punto a ID {id_att}.")
                    self._aggiorna_statistiche_punto(stats_att, stats_dif, 'Fallo')
                    return id_att, 'Fallo', dettaglio
                if ris_blocco in ("Perfetto", "Successo"):
                    if log_attivo:
                        debug_log_punto.append(f"      -> Blocco Riuscito ID {id_dif}!")
                    blocco_riuscito = True
                else:
                    esito = self._fallimento_normale(log_attivo, log_partita, debug_log_punto, f"Fallo Blocco ({nome_blocco}, Normale)", f"Blocco Fallito ({nome_blocco})", id_dif, id_att, stats_att, stats_dif)
                    if esito is not None:
                        return esito
                    attaccante_corrente, difensore_corrente = difensore_corrente, attaccante_corrente
                    fattore_diff_difesa_ritorno = FATTORE_BONUS_DIFESA_SU_RITORNO_FACILE
                    ultimo_attacco_base = None
                    continue
            elif chiusura_riuscita:
                blocco_riuscito = True
            # Controllo palla, dopo blocco o difesa riusciti.
            if blocco_riuscito:
                azione_descr_ctrl = f"Controllo Palla ID {id_dif}"
                if log_attivo:
                    debug_log_punto.append(f"    {azione_descr_ctrl}")
                val_controllo = self._calcola_valore_azione(difensore_corrente, "Controllo", 'controllopalla_base', res_perc_dif, debug_log=debug_log_punto)
                ris_ctrl, _ = self._risolvi_azione_vs_dado(difensore_corrente, attaccante_corrente, val_controllo, azione_descr_ctrl, debug_log_punto)
                if ris_ctrl in FALLI:
                    dettaglio = f"Fallo Controllo Palla ({ris_ctrl})"
                    if log_attivo:
                        log_partita.extend(debug_log_punto)
                        log_partita.append(f"      -> {dettaglio} ID {id_dif}! Punto a ID {id_att}.")
                    self._aggiorna_statistiche_punto(stats_att, stats_dif, 'Fallo')
                    return id_att, 'Fallo', dettaglio
                if ris_ctrl in ("Perfetto", "Successo"):
                    if log_attivo:
                        debug_log_punto.append(f"      -> Controllo Palla Riuscito ID {id_dif}! Ora attacca.")
                    attaccante_corrente, difensore_corrente = difensore_corrente, attaccante_corrente
                    fattore_diff_difesa_ritorno = 1.0
                    ultimo_attacco_base = None
                    continue
                esito = self._fallimento_normale(log_attivo, log_partita, debug_log_punto, "Fallo Controllo Palla (Normale)", "Controllo Palla Fallito", id_dif, id_att, stats_att, stats_dif)
                if esito is not None:
                    return esito
                attaccante_corrente, difensore_corrente = difensore_corrente, attaccante_corrente
                fattore_diff_difesa_ritorno = FATTORE_BONUS_DIFESA_SU_RITORNO_FACILE
                ultimo_attacco_base = None
                continue
            # Rete di sicurezza per uno stato che non dovrebbe presentarsi.
            self.mostra(f"ERRORE LOGICO: Stato imprevisto in _gioca_punto fine B GID {id_dif}. Punto a GID {id_att}.")
            if log_attivo:
                log_partita.extend(debug_log_punto)
                log_partita.append(f"      -> Errore logico B! Punto a ID {id_att}.")
            self._aggiorna_statistiche_punto(stats_att, stats_dif, 'Fallo')
            return id_att, 'Fallo', 'Errore Flusso Difesa Post-Chiusura'
        self.mostra(f"WARN: Punto terminato per limite scambi ({max_scambi_per_punto}). Assegno punto casuale.")
        if log_attivo:
            log_partita.extend(debug_log_punto)
            log_partita.append("      -> Limite scambi! Punto casuale.")
        vincitore_casuale = random.choice([id_att, id_dif])
        stats_vinc_cas = stats_att if vincitore_casuale == id_att else stats_dif
        stats_perd_cas = stats_dif if vincitore_casuale == id_att else stats_att
        self._aggiorna_statistiche_punto(stats_vinc_cas, stats_perd_cas, 'Fallo')
        return vincitore_casuale, 'Fallo', 'Limite Scambi'

    def _calcola_valore_azione(self, giocatore, azione, skill_specifica_base_nome, resistenza_perc_attuale, skill_attacco_avversario_base_nome=None, debug_log=None):
        """Il valore di un'azione: caratteristica, precisione doppia, forza, resistenza, bonus, poi la stanchezza."""
        if not skill_specifica_base_nome.endswith('_base') or not hasattr(giocatore, skill_specifica_base_nome):
            raise ValueError(f"Skill '{skill_specifica_base_nome}' non valida per il giocatore {giocatore.id}")
        skill_tot = giocatore._get_valore_totale(skill_specifica_base_nome)
        prec_tot = giocatore._get_valore_totale('precisione_base')
        forza_tot = giocatore._get_valore_totale('forza_base')
        res_tot = giocatore._get_valore_totale('resistenza_base')
        valore_base_somma = 5 + skill_tot + (prec_tot * 2.0) + forza_tot + res_tot
        bonus_azione_specifica = 0.0
        azione_key = azione.split(':')[0]
        if azione_key in ["Difesa", "Chiusura"] and skill_attacco_avversario_base_nome and skill_attacco_avversario_base_nome in COLPI_A_SPONDA:
            bonus_azione_specifica += giocatore._get_valore_totale('difesa_base') * 0.25
        elif azione_key == "Battuta":
            bonus_azione_specifica += VALORE_AZIONE_BONUS_BATTUTA
        elif skill_specifica_base_nome == 'bomba_base':
            bonus_azione_specifica += forza_tot * 0.10
        elif azione_key == "Controllo":
            bonus_azione_specifica += prec_tot * 0.15
        bonus_flags = 0.0
        if azione_key in ["Attacco", "Difesa", "Blocco", "Battuta"]:
            if getattr(giocatore, 'giocorapido', False):
                bonus_flags += 5.0
            if getattr(giocatore, 'cambiovelocita', False):
                bonus_flags += 5.0
        valore_con_bonus = valore_base_somma + bonus_azione_specifica + bonus_flags
        perc_res_effettiva = max(0.05, resistenza_perc_attuale)
        valore_finale = valore_con_bonus * perc_res_effettiva
        if debug_log is not None:
            log = f"      > Calc Val Azione ({azione} GID:{giocatore.id}):\n"
            log += f"        - Base(5)+Skill({skill_specifica_base_nome.replace('_base', '')}:{skill_tot:.1f})+Prec*2({prec_tot * 2:.1f})+Forz({forza_tot:.1f})+Res({res_tot:.1f}) = {valore_base_somma:.1f}\n"
            if bonus_azione_specifica > 0:
                log += f"        - Bonus Azione Spec: +{bonus_azione_specifica:.1f}\n"
            if bonus_flags > 0:
                log += f"        - Bonus Flags: +{bonus_flags:.1f}\n"
            log += f"        - Subtotale: {valore_con_bonus:.1f}\n"
            log += f"        - Malus Stanchezza (x{perc_res_effettiva:.2f}) -> Val Finale: {valore_finale:.2f}"
            debug_log.append(log)
        return max(0.0, valore_finale)

    def _calcola_resistenza_set(self, giocatore, num_set_attuale):
        """La resistenza che resta al giocatore nel set indicato, in frazione, calante con l'età."""
        if num_set_attuale <= 1:
            return 1.0
        range_eta_calo = ETA_MAX_CALO_RES - ETA_MIN_CALO_RES
        if range_eta_calo <= 0:
            range_eta_calo = 1
        eta_anni = giocatore.eta_anni
        perc_calo_target_set5 = TARGET_MIN_PERC_RES_SET5
        if eta_anni >= ETA_MAX_CALO_RES:
            perc_calo_target_set5 = TARGET_MAX_PERC_RES_SET5
        elif eta_anni > ETA_MIN_CALO_RES:
            progressione_eta = (eta_anni - ETA_MIN_CALO_RES) / range_eta_calo
            perc_calo_target_set5 = TARGET_MIN_PERC_RES_SET5 + progressione_eta * (TARGET_MAX_PERC_RES_SET5 - TARGET_MIN_PERC_RES_SET5)
        fattore_calo_per_set = 0.0 if perc_calo_target_set5 <= 0 else pow(perc_calo_target_set5, 0.25)
        perc_resistenza_attuale = pow(fattore_calo_per_set, max(0, num_set_attuale - 1))
        return max(0.01, perc_resistenza_attuale)

    def _risolvi_azione_vs_dado(self, giocatore_att, giocatore_dif, valore_azione, azione_descr, debug_log=None):
        """
        Tira il dado da 0 a 100: sotto il 5 fallo critico, dal 95 perfetto, in mezzo successo
        sotto la soglia scalata e fallo sopra. Restituisce l'esito e il dado tirato.
        """
        dado = random.uniform(0, 100)
        risultato = "Fallo"
        soglia_successo_scalata = valore_azione
        if dado < 5.0:
            risultato = "FalloCritico"
        elif dado >= 95.0:
            risultato = "Perfetto"
        else:
            capacita_difensiva = giocatore_dif.indice_collettivo_valore * SCALING_K_DIFESA_ICV
            delta_azione = valore_azione - capacita_difensiva
            range_div = SCALING_RANGE_DELTA_EFF / 2.0
            delta_norm = 0.0 if range_div == 0 else max(-1.0, min(1.0, delta_azione / range_div))
            soglia_successo_scalata = SCALING_SOGLIA_BASE + delta_norm * SCALING_MODIFICATORE_MAX
            soglia_successo_scalata = max(5.0, min(95.0, soglia_successo_scalata))
            if debug_log is not None:
                debug_log.append(f"      > Scaling Soglia: V.Az:{valore_azione:.1f}, Cap.Dif:{capacita_difensiva:.1f}, Delta:{delta_azione:.1f}, Soglia Scalata:{soglia_successo_scalata:.1f}")
            if 5.0 <= dado < soglia_successo_scalata:
                risultato = "Successo"
        if debug_log is not None:
            soglia_mostrata = soglia_successo_scalata if risultato not in ["FalloCritico", "Perfetto"] else valore_azione
            debug_log.append(f"      > Risolvi Dado Scalato ({azione_descr} GID:{giocatore_att.id}): Dado={dado:.2f} vs Soglia={soglia_mostrata:.1f} -> {risultato}")
        return risultato, dado

    def _aggiorna_statistiche_punto(self, stats_vincitore, stats_perdente, tipo_punto):
        """Aggiorna i contatori di goal e falli della partita in base all'esito del punto."""
        if tipo_punto == 'Goal':
            stats_vincitore['goal'] += 1
        elif tipo_punto == 'Fallo':
            stats_vincitore['falli_subiti'] += 1
            stats_perdente['falli_fatti'] += 1

    def _xp_della_partita(self, num_set_target, set_vinti_vinc, set_vinti_perd):
        """Punti esperienza a vincitore e perdente, secondo la formula e il punteggio in set."""
        if set_vinti_vinc <= set_vinti_perd:
            return 0, 0
        if num_set_target <= 3:
            tabella = {0: (XP_VITTORIA_2_0, XP_SCONFITTA_0_2), 1: (XP_VITTORIA_2_1, XP_SCONFITTA_1_2)}
        else:
            tabella = {0: (XP_VITTORIA_3_0, XP_SCONFITTA_0_3), 1: (XP_VITTORIA_3_1, XP_SCONFITTA_1_3), 2: (XP_VITTORIA_3_2, XP_SCONFITTA_2_3)}
        return tabella.get(set_vinti_perd, (0, 0))

    def _aggiorna_statistiche_post_partita(self, risultato, info_torneo=None):
        """Aggiorna statistiche di carriera ed esperienza, e controlla gli infortuni dopo la partita."""
        id_vincitore = risultato.get('vincitore_id')
        id_perdente = risultato.get('perdente_id')
        id_g1_orig = risultato.get('id_originale_g1')
        id_g2_orig = risultato.get('id_originale_g2')
        num_set_target = risultato.get('num_set_target', 3)
        punteggio_set = risultato.get('punteggio_set', [])
        stats_g1 = risultato.get('stats_g1', {'goal': 0, 'falli_fatti': 0, 'falli_subiti': 0})
        stats_g2 = risultato.get('stats_g2', {'goal': 0, 'falli_fatti': 0, 'falli_subiti': 0})
        if None in [id_vincitore, id_perdente, id_g1_orig, id_g2_orig]:
            self.mostra("WARN: Dati risultato partita incompleti.")
            return
        g_vinc = self.giocatori.get(id_vincitore)
        g_perd = self.giocatori.get(id_perdente)
        if not g_vinc or not g_perd:
            self.mostra("WARN: Giocatore vincitore/perdente non trovato.")
            return
        stats_vinc = stats_g1 if id_vincitore == id_g1_orig else stats_g2
        stats_perd = stats_g2 if id_vincitore == id_g1_orig else stats_g1
        g_vinc.partitevinte += 1
        g_perd.partiteperse += 1
        set_vinti_vinc, set_vinti_perd = 0, 0
        for p1, p2 in punteggio_set:
            vinto_dal_vincitore = p1 > p2 if id_g1_orig == id_vincitore else p2 > p1
            if vinto_dal_vincitore:
                set_vinti_vinc += 1
            else:
                set_vinti_perd += 1
        g_vinc.setsvinti += set_vinti_vinc
        g_vinc.setspersi += set_vinti_perd
        g_perd.setsvinti += set_vinti_perd
        g_perd.setspersi += set_vinti_vinc
        g_vinc.goalsfatti += stats_vinc.get('goal', 0)
        g_vinc.goalssubiti += stats_perd.get('goal', 0)
        g_perd.goalsfatti += stats_perd.get('goal', 0)
        g_perd.goalssubiti += stats_vinc.get('goal', 0)
        xp_vinc, xp_perd = self._xp_della_partita(num_set_target, set_vinti_vinc, set_vinti_perd)
        if info_torneo:
            xp_vinc += XP_BONUS_TORNEO
            xp_perd += XP_BONUS_TORNEO
        icv_vinc = g_vinc.indice_collettivo_valore
        icv_perd = g_perd.indice_collettivo_valore
        max_icv = max(icv_vinc, icv_perd, 1.0)
        diff_perc = abs(icv_vinc - icv_perd) / max_icv * 100.0
        if diff_perc >= ICV_DIFF_PERC_UNDERDOG:
            if icv_vinc < icv_perd:
                xp_vinc += XP_BONUS_UNDERDOG
            else:
                xp_perd += XP_BONUS_UNDERDOG
        g_vinc.puntiesperienza = max(0, int(g_vinc.puntiesperienza or 0) + xp_vinc)
        g_perd.puntiesperienza = max(0, int(g_perd.puntiesperienza or 0) + xp_perd)
        self.mostra(f" -> XP Assegnati: ID {id_vincitore}: +{xp_vinc}, ID {id_perdente}: +{xp_perd}")
        self.mostra(" -> Controllo Infortuni...")
        for giocatore_corrente in [g_vinc, g_perd]:
            if not getattr(giocatore_corrente, 'infortunato', False):
                prob_infortunio = self._calcola_prob_infortunio(giocatore_corrente)
                if caso(prob_infortunio):
                    giocatore_corrente.infortunato = True
                    giorni_durata = self._calcola_durata_infortunio(giocatore_corrente)
                    data_fine = self.mondo.datetime_corrente_simulazione + datetime.timedelta(days=giorni_durata)
                    giocatore_corrente.infortunio_fine_datetime = data_fine
                    self.mostra(f"    -> INFORTUNIO! ID {giocatore_corrente.id} ({giocatore_corrente.nome}) fuori per {giorni_durata} giorni sim (fino a {data_fine:%Y-%m-%d %H:%M}). (Prob: {prob_infortunio:.3f}%)")

    def _calcola_prob_infortunio(self, giocatore):
        """La probabilità di infortunio dopo una partita, in percentuale: cresce dai 30 anni."""
        prob_aum_eta = 0.0
        eta_a = giocatore.eta_anni
        if eta_a > ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI:
            eta_calc = min(eta_a, ETA_MAX_PROB_INFORTUNIO_ANNI)
            range_eta = max(1.0, ETA_MAX_PROB_INFORTUNIO_ANNI - ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI)
            prog = (eta_calc - ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI) / range_eta
            prob_aum_eta = prog * PROB_INFORTUNIO_AUMENTO_MAX_PERC
        prob_fin = PROB_INFORTUNIO_BASE_PER_PARTITA + prob_aum_eta
        if getattr(giocatore, 'ambidestro', False):
            prob_fin *= 0.20
        return max(0.0, min(prob_fin, 95.0))

    def _calcola_durata_infortunio(self, giocatore):
        """La durata di un infortunio in giorni simulati: più lunga con l'età e con poca resistenza."""
        if ANNO_SIMULAZIONE_GIORNI <= 0:
            return random.randint(3, 20)
        range_eta = max(1, AGING_PEAK_AGE_GIORNI)
        eta_norm = max(0., min(1., giocatore.eta / range_eta))
        min_d, max_d = INFORTUNIO_DURATA_MIN_GIORNI, INFORTUNIO_DURATA_MAX_GIORNI_ETA
        medio = (min_d + max_d) / 2.
        if random.random() < eta_norm ** 1.5:
            lim_i = min(math.ceil(medio), max_d)
            dur_base_cas = random.randint(lim_i, max_d) if lim_i <= max_d else max_d
        else:
            lim_s = max(math.floor(medio), min_d)
            dur_base_cas = random.randint(min_d, lim_s) if min_d <= lim_s else min_d
        res_n = max(0., min(giocatore._get_valore_totale('resistenza_base'), MAX_TOTALE_PRECISIONE_RESISTENZA))
        malus_r = 0.
        if MAX_TOTALE_PRECISIONE_RESISTENZA > 0:
            malus_r = (1. - res_n / MAX_TOTALE_PRECISIONE_RESISTENZA) * INFORTUNIO_MALUS_MAX_RESISTENZA
        dur_mod = float(dur_base_cas) + malus_r
        if getattr(giocatore, 'ambidestro', False):
            dur_mod *= 0.20
        return max(INFORTUNIO_DURATA_MIN_GIORNI, round(dur_mod))
