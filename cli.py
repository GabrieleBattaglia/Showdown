"""
L'interfaccia testuale di MESS, quella del vecchio sd.py.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 2 del piano, dallo smontaggio di sd.py: qui stanno i menu, le
domande all'utente e le schermate, con i testi di prima. È un'interfaccia di passaggio: dalla
tappa 5 la sostituisce la finestra, e con lei arriveranno i testi discorsivi senza separatori,
problema P12, e le correzioni delle liste, problema P11. Le regole del gioco non stanno qui ma
nei moduli del motore, che questa interfaccia chiama: dalla tappa 7 anche fondazione, offerte,
svincoli e chiusura delle polisportive, con la password facoltativa e i nomi come li si scrive.
Dalla tappa 8 il tesseramento chiede la cifra dell'ingaggio; il resto dell'economia sta nella finestra.
"""

import datetime
import math
import time

from GBUtils import dgt, key, menu

import archivio
from allenamento import calcola_costo_xp_per_punto, guadagno, limiti
from costanti import ANNO_SIMULAZIONE_GIORNI as anno
from costanti import (
    ATTRIBUTI_ALLENABILI_MAP,
    ATTRIBUTI_BASE_CON_ALLENABILI,
    CARATTERISTICHE_FISICHE_BASE,
    ETA_MAX_MORTE_ANNI,
    LIMITE_MOVIMENTI_PER_TICK,
    MAPPA_FLAG_SOMMARIO,
    MAX_TOTALE_PRECISIONE_RESISTENZA,
    MAX_TOTALE_SKILL_GIOCO,
    MODALITA_OUTPUT_CONSOLE,
    MODALITA_OUTPUT_FILE,
    MODALITA_OUTPUT_RISULTATO,
    NOME_ATTR_TO_DISPLAY_MAP,
    NOME_POLISPORTIVA_MAX,
    NOME_POLISPORTIVA_MIN,
    PAGINAZIONE_LISTE,
    VERSIONE,
)
from economia import ingaggio_richiesto, stipendio
from modelli import e_fisica
from partita import MotorePartita
from utilita import accorda, adesso, adesso_utc, caso, converti_in_tempo, formatta_eta_sim

MAINMENU = {
    'AGT': 'Allena Giocatori Tesserati;', 'CEG': 'CErca Giocatori;', 'CLA': 'CLAssifica Globale Giocatori (per ICV);',
    'CTT': 'Copia Tesserati attuali nei Trovati;', 'MPO': 'Menu delle POlisportive;', 'OPA': 'Organizza Partita Amichevole;',
    'SGG': 'Statistica Globale Giocatori;', 'TOP': 'TOP10 giocatori e Polisportive;', 'VLN': 'Vedi Lista Nuovi;',
    'VLM': 'Vedi Lista Morti;', 'VLT': 'Vedi Lista Trovati (risultati ricerca);', 'VLR': 'Vedi Lista Ritirati;',
    'VRG': 'Vedi Riepilogo Giocatori (per ID range);', 'VSG': 'Vedi Scheda Giocatore;', 'DTS': 'Visualizza Data/Ora Simulazione;',
    '?': 'visualizza questo MENu;', '': 'INVIO a vuoto per USCIRE e salvare.'
}
POLIMENU = {
    "APR": "APRi una nuova polisportiva;", "CHI": "CHIudi la polisportiva attiva;", "CPA": "Cambia Polisportiva Attiva;",
    "ESG": "Svincola un Giocatore della polisportiva attiva;", "MPP": "Modifica, metti o togli la Password della Polisportiva attiva;",
    "TEG": "TEssera Giocatore nella polisportiva attiva;", "VGT": "Vedi Giocatori Tesserati della polisportiva attiva;",
    "VGP": "Vedi Giocatori Papabili (liberi ordinati per ICV);", "VLE": "Vedi Lista Polisportive Esistenti;",
    "VSP": "Vedi Scheda Polisportiva attiva;", "?": "Vedi Questo Menu;", "": "INVIO per tornare al menu principale;"
}
MENU_ALLENAMENTO = {
    "PRC": "Precisione;", "RST": "Resistenza;", "FOR": "Forza;",
    "DFA": "Difesa;", "TPA": "Tenuta paletta;", "CSA": "Chiusura SX;",
    "CDA": "Chiusura DX;", "BSA": "Blocco SX;", "BDA": "Blocco DX;", "CPA": "Controllo palla;", "ATA": "Attacco;",
    "BTSA": "Battuta SX;", "BTDA": "Battuta DX;", "BA": "Bomba;", "LLSA": "Lungolinea SX;", "LLDA": "Lungolinea DX;",
    "DSA": "Diagonale SX;", "DDA": "Diagonale DX;", "SSS": "S.Sponda SX;", "SSD": "S.Sponda DX;", "DPSA": "D.Sponda SX;",
    "DPDA": "D.Sponda DX;", "TPSA": "T.Sponda SX;", "TPDA": "T.Sponda DX;", "": "Termina allenamento atleta;"
}
MENU_RICERCA = {
    "ICV": "ICV;", "ETA": "Eta (anni sim);", "NOME": "Nome;", "COGNOME": "Cognome;", "IPO": "Ipovedente (s/n);",
    "PRC": "Precisione (Tot);", "RST": "Resistenza (Tot);", "FOR": "Forza (Tot);",
    "DFA": "Difesa (Tot);", "TPA": "Tenuta paletta (Tot);",
    "CSA": "Chiusura SX (Tot);", "CDA": "Chiusura DX (Tot);", "BSA": "Blocco SX (Tot);", "BDA": "Blocco DX (Tot);",
    "CPA": "Controllo palla (Tot);", "ATA": "Attacco (Tot);", "BTSA": "Battuta SX (Tot);", "BTDA": "Battuta DX (Tot);",
    "BA": "Bomba (Tot);", "LLSA": "Lungolinea SX (Tot);", "LLDA": "Lungolinea DX (Tot);", "DSA": "Diagonale SX (Tot);",
    "DDA": "Diagonale DX (Tot);", "SSS": "S.Sponda SX (Tot);", "SSD": "S.Sponda DX (Tot);",
    "DPSA": "D.Sponda SX (Tot);", "DPDA": "D.Sponda DX (Tot);", "TPSA": "T.Sponda SX (Tot);", "TPDA": "T.Sponda DX (Tot);"
}
MAPPA_RICERCA_ATTRIBUTI = {
    "ICV": "indice_collettivo_valore", "ETA": "eta_anni", "NOME": "nome", "COGNOME": "cognome", "IPO": "ipovedente",
    "PRC": "precisione_totale", "RST": "resistenza_totale", "FOR": "forza_totale",
    "DFA": "difesa_totale", "TPA": "tenutapaletta_totale",
    "CSA": "chiusurasx_totale", "CDA": "chiusuradx_totale", "BSA": "bloccosx_totale", "BDA": "bloccodx_totale",
    "CPA": "controllopalla_totale", "ATA": "attacco_totale", "BTSA": "battutasx_totale", "BTDA": "battutadx_totale",
    "BA": "bomba_totale", "LLSA": "lungolineasx_totale", "LLDA": "lungolineadx_totale", "DSA": "diagonalesx_totale",
    "DDA": "diagonaledx_totale", "SSS": "singolaspondasx_totale", "SSD": "singolaspondadx_totale",
    "DPSA": "doppiaspondasx_totale", "DPDA": "doppiaspondadx_totale", "TPSA": "triplaspondasx_totale", "TPDA": "triplaspondadx_totale"
}
ATTIVA_RICHIESTA = "Attiva Richiesta."


class InterfacciaTestuale:
    def __init__(self, mondo):
        self.mondo = mondo
        self.start_time = time.time()
        self.comandi_eseguiti = 0

    # Scorciatoie verso lo stato del mondo.

    @property
    def giocatori(self):
        return self.mondo.giocatori

    @property
    def polisportive(self):
        return self.mondo.polisportive

    @property
    def attiva(self):
        return self.mondo.miapolisportiva_attiva

    @property
    def morti(self):
        return self.mondo._ids_morti_processati_sessione

    @property
    def data_sim(self):
        return self.mondo.datetime_corrente_simulazione

    # Il ciclo principale.

    def run(self):
        """Il ciclo principale: menu, comandi, e alla fine il salvataggio."""
        now = adesso()
        print("\n" + "=" * 75)
        print(f" MESS - Versione: {VERSIONE}")
        sim_dt_str = self.data_sim.strftime('%Y-%m-%d %H:%M') if isinstance(self.data_sim, datetime.datetime) else "N/D"
        print(f" Data Reale: {now:%Y-%m-%d %H:%M}, Data Sim: {sim_dt_str}")
        print("=" * 75)
        ultimo = self.mondo.datetime_ultimo_run_reale
        if isinstance(ultimo, datetime.datetime) and (adesso_utc() - ultimo).total_seconds() < (8 * 3600 - 60):
            testo = self.mondo.testo_prossimo_sblocco()
            if testo:
                print(testo)
            print("-" * 75)
        cmd_map = {"VSG": self.visualizza_scheda_giocatore, "VRG": self.visualizza_riepilogo_giocatori, "CLA": self.visualizza_classifica_giocatori,
                   "VLN": lambda: self.visualizza_lista(self.mondo.nuovi_giocatori_sessione, "Lista Nuovi Sessione", "giocatore"),
                   "VLM": lambda: self.visualizza_lista(self.mondo.giocatori_morti_sessione, "Lista Morti Sessione", "messaggio"),
                   "VLR": lambda: self.visualizza_lista(self.mondo.giocatori_ritirati_sessione, "Lista Ritirati Sessione", "messaggio"),
                   "VLT": lambda: self.visualizza_lista(self.mondo.risultati_ultima_ricerca, "Risultati Ultima Ricerca", "giocatore"),
                   "MPO": self.menu_polisportive, "CEG": self.cerca_giocatori, "CTT": self._copia_tesserati_attivi_in_vlt,
                   "AGT": self.allenamento_giocatori_tesserati, "OPA": self.organizza_partita_amichevole, "SGG": self.statistica_globale,
                   "TOP": self.visualizza_top_10, "DTS": lambda: print(f"\nData/Ora Sim: {self.data_sim:%Y-%m-%d %H:%M:%S}")}
        running = True
        while running:
            try:
                scelta = menu(d=MAINMENU, p=self._prompt_principale(), keyslist=False, show_on_filter=True, pager=PAGINAZIONE_LISTE, show=False, ntf="Comando non valido")
                self.comandi_eseguiti += 1
                if scelta is None or scelta == '':
                    running = False
                elif scelta == '?':
                    print("\n--- Menu Principale ---")
                    for k, v in MAINMENU.items():
                        if k:
                            print(f" {k:<4}: {v}")
                    print("-" * 75)
                    input("...INVIO...")
                elif scelta in cmd_map:
                    cmd_map[scelta]()
            except EOFError:
                running = False
                print("\nUscita (EOF)...")
            except KeyboardInterrupt:
                running = False
                print("\nInterruzione...")
            except Exception as e:  # noqa: BLE001 - ultima rete del ciclo: mostra l'errore e lascia decidere se continuare
                print(f"\nERRORE LOOP: {e}")
                try:
                    if key("Errore grave. Continuare(S/n)? ").lower() != 's':
                        running = False
                except (EOFError, AttributeError):
                    running = False
        print("Uscita dal loop principale, chiamata a concludi_sessione...")
        self.concludi_sessione()

    def _prompt_principale(self):
        poli_a = self.attiva.nome if self.attiva else "Nessuna"
        n_liberi = 0
        n_tesserati = 0
        n_non_giocanti = 0
        for gid, g in self.giocatori.items():
            if gid not in self.morti:
                if g.ritirato or g.infortunato:
                    n_non_giocanti += 1
                elif g.appartenenza == "*":
                    n_liberi += 1
                else:
                    n_tesserati += 1
        return f"(MEN)<{poli_a}> Gioc(L:{n_liberi}/T:{n_tesserati}/N:{n_non_giocanti}/Tot:{len(self.giocatori)})> "

    def concludi_sessione(self):
        print("\nInizio operazioni finali...")
        archivio.salva(self.mondo)
        h, m, s = converti_in_tempo(time.time() - self.start_time)
        print(f"\nSessione: {h}h {m}m {s}s.")
        print(f"{self.comandi_eseguiti} comandi.")
        print("Arrivederci!")

    # Giocatori.

    def visualizza_scheda_giocatore(self):
        """Mostra la scheda dettagliata di un giocatore specifico."""
        try:
            gid = int(dgt("ID giocatore? ", "i", imin=1))
            if gid in self.giocatori:
                g = self.giocatori[gid]
                if gid in self.morti:
                    print(f"\nATT: Giocatore {gid} ({g.nome}) deceduto (verrà rimosso al salvataggio).")
                print(g)
            else:
                print(f"\n\tID {gid} non trovato.")
        except (ValueError, TypeError):
            print("\n\tID non valido.")
        except EOFError:
            print("\nAnnullato.")

    def visualizza_riepilogo_giocatori(self):
        try:
            id1 = int(dgt("ID iniziale? ", "i", imin=1))
            id2 = int(dgt("ID finale? ", "i", imin=id1))
            ids = [gid for gid in range(id1, id2 + 1) if gid in self.giocatori]
            if not ids:
                print(f"\nNessun giocatore ID {id1}-{id2}.")
                return
            self.visualizza_lista(ids, f"Riepilogo Giocatori (ID {id1}-{id2})", "giocatore")
        except (ValueError, TypeError):
            print("\n\tID non valido.")
        except EOFError:
            print("\nAnnullato.")

    def _attivi(self):
        return [g for gid, g in self.giocatori.items() if gid not in self.morti and not g.ritirato]

    @staticmethod
    def _club(g, lunghezza=15):
        return "Libero" if g.appartenenza == "*" else g.appartenenza[:lunghezza]

    def visualizza_classifica_giocatori(self):
        """Mostra classifica globale giocatori attivi per ICV."""
        print("\n--- Classifica Globale Giocatori (per ICV) ---")
        attivi = self._attivi()
        if not attivi:
            print("\n\tNessun giocatore attivo.")
            return
        ordinati = sorted(attivi, key=lambda g: g.indice_collettivo_valore, reverse=True)
        n_tot = len(ordinati)
        print(f"Trovati {n_tot} giocatori attivi.")
        try:
            pos_target = dgt(f"Visualizza intorno alla posizione (1-{n_tot})? ", "i", imin=1, imax=n_tot)
            idx_target = pos_target - 1
        except (ValueError, TypeError, EOFError):
            print("\nInput non valido.")
            return
        el_lato = 12
        idx_start = max(0, idx_target - el_lato)
        idx_end = min(n_tot, idx_target + el_lato + 1)
        da_vis = ordinati[idx_start:idx_end]
        if not da_vis:
            print("\n\tNessun giocatore nel range.")
            return
        print(f"\n--- Classifica Globale (Posizioni {idx_start + 1} - {idx_end}) ---")
        hdr = f"{'Pos':<5} {'ID':<5} {'Età(A/M/G)':<10} {'Archetipo':<25} {'ICV':<8} {'Club':<15} {'Nome Cognome'}"
        print(hdr)
        print("-" * (len(hdr) + 5))
        for i, g in enumerate(da_vis):
            pos = idx_start + i + 1
            eta = formatta_eta_sim(g.eta, True)
            arch = getattr(g, 'archetipo_allenamento', 'N/D')[:25]
            icv = f"{g.indice_collettivo_valore:.1f}"
            prefix = "->" if pos == pos_target else "  "
            print(f"{prefix}{pos:<3} {g.id:<5} {eta:<10} {arch:<25} {icv:<8} {self._club(g):<15} {g.nome} {g.cognome}")
        print("-" * (len(hdr) + 5))
        print(f"Visualizzate {len(da_vis)} posizioni.")

    def visualizza_lista(self, lista, titolo, tipo="giocatore"):
        if not lista:
            print(f"\n\t--- Lista '{titolo}' vuota. ---")
            return
        print(f"\n--- {titolo} ({len(lista)} elementi) ---")
        n_st = 0
        ids_mostr = set()
        items = reversed(lista) if tipo == "messaggio" or titolo.startswith("Lista Nuovi") else lista
        for item in items:
            mostra = True
            if tipo == "giocatore" and isinstance(item, int):
                somm = self.giocatori[item].sommario() if item in self.giocatori else f"ID:{item:<4d} {'DECEDUTO' if item in self.morti else 'NON TROVATO'}"
            elif tipo == "polisportiva" and isinstance(item, str):
                somm = self.polisportive[item].sommario(self.data_sim) if item in self.polisportive else f"{item:<30} NON TROVATA"
            elif tipo == "messaggio" and isinstance(item, tuple) and len(item) == 2:
                if item[0] in ids_mostr:
                    mostra = False
                else:
                    ids_mostr.add(item[0])
                    somm = item[1]
            else:
                mostra = False
            if mostra:
                print(somm)
                n_st += 1
                if n_st % PAGINAZIONE_LISTE == 0 and n_st < len(lista):
                    try:
                        k = key(f"...INVIO ({n_st}/{len(lista)}), E=Esci: ")
                        if k is not None and k.lower() == 'e':
                            break
                    except EOFError:
                        break
        print("-" * (len(titolo) + 8))

    def cerca_giocatori(self):
        print("\n--- Ricerca Giocatori ---")
        ops = {"I": "Intero DB", "A": "Attivi", "L": "Liberi", "T": "Tesserati", "N": "Nuovi", "R": "Ritirati", "M": "Morti", "V": "VLT"}
        sel_l = menu(d=ops, p="Cerca in (ESC=Annulla): ", keyslist=False, show=True, pager=10)
        if sel_l is None:
            print("Annullato.")
            return
        if sel_l and sel_l != '?':
            self.comandi_eseguiti += 1
        desc = ops.get(sel_l, "?")
        morti = self.morti
        elenchi = {
            'I': lambda: list(self.giocatori.keys()),
            'A': lambda: [gid for gid, g in self.giocatori.items() if gid not in morti and not g.ritirato],
            'L': lambda: [gid for gid, g in self.giocatori.items() if gid not in morti and not g.ritirato and g.appartenenza == "*"],
            'T': lambda: [gid for gid, g in self.giocatori.items() if gid not in morti and not g.ritirato and g.appartenenza != "*"],
            'N': lambda: list(self.mondo.nuovi_giocatori_sessione),
            'R': lambda: [gid for gid, g in self.giocatori.items() if gid not in morti and g.ritirato],
            'M': lambda: list(morti),
            'V': lambda: list(self.mondo.risultati_ultima_ricerca),
        }
        if sel_l not in elenchi:
            print("Sel. lista non valida.")
            return
        ids = elenchi[sel_l]()
        if not ids:
            print(f"\n\tLista '{desc}' vuota.")
            return
        print(f"\nRicerca in: {desc} ({len(ids)} gioc.).")
        try:
            sel_a = menu(d=MENU_RICERCA, p="Caratteristica (ESC=Annulla)? ", keyslist=True, pager=PAGINAZIONE_LISTE, show=True, show_on_filter=True)
            if sel_a is None:
                print("Annullato.")
                return
            if sel_a and sel_a != '?':
                self.comandi_eseguiti += 1
            attr_l = MAPPA_RICERCA_ATTRIBUTI.get(sel_a)
            if not attr_l:
                print("\n\tErrore mappa.")
                return
            nome_d = MENU_RICERCA.get(sel_a, "?").replace(';', '')
            if attr_l == "ipovedente":
                val = key(f"Cercare chi È '{nome_d}'(s/N)? ").lower() == 's'
                print(f"Ricerca '{nome_d}'={val}")
                res = [gid for gid in ids if gid in self.giocatori and getattr(self.giocatori[gid], attr_l, False) == val]
            elif attr_l in ["nome", "cognome"]:
                txt = dgt(f"'{nome_d}' contiene: ").lower()
                print(f"Ricerca '{nome_d}'~'{txt}'...")
                res = [gid for gid in ids if gid in self.giocatori and txt in getattr(self.giocatori[gid], attr_l, "").lower()] if txt else []
            else:
                res = self._ricerca_numerica(ids, attr_l, nome_d)
                if res is None:
                    return
            self.mondo.risultati_ultima_ricerca = res
            print(f"\nRisultati: {len(res)}." + (" Vedi VLT." if res else ""))
        except EOFError:
            print("\nAnnullato.")

    def _ricerca_numerica(self, ids, attr_l, nome_d):
        """I giocatori con il valore sopra o sotto una soglia; None se l'operatore non è valido."""
        op = dgt(f"'{nome_d}' (>/<) di? ", "s", smax=1)
        if op not in ['>', '<']:
            print("\tUsa > o <.")
            return None
        min_v = -float('inf')
        max_v = float('inf')
        if attr_l == "eta_anni":
            min_v, max_v = 0., ETA_MAX_MORTE_ANNI + 10
        elif attr_l in ["precisione_totale", "resistenza_totale", "forza_totale"]:
            min_v, max_v = 0., MAX_TOTALE_PRECISIONE_RESISTENZA
        elif "_totale" in attr_l:
            min_v, max_v = 0., MAX_TOTALE_SKILL_GIOCO
        elif attr_l == "indice_collettivo_valore":
            min_v, max_v = 0., 1000
        soglia = dgt(f"Valore({min_v:.1f}-{max_v:.1f})? ", "f", fmin=min_v, fmax=max_v)
        print(f"Ricerca '{nome_d}'{op}{soglia}...")
        res = []
        for gid in ids:
            if gid not in self.giocatori:
                continue
            g = self.giocatori[gid]
            if attr_l == "eta_anni":
                val_g = g.eta_anni
            elif "_totale" in attr_l:
                val_g = g._get_valore_totale(attr_l.replace('_totale', '_base'))
            else:
                val_g = getattr(g, attr_l, 0.)
            val_g = float(val_g)
            # Problema P11, tappa 5: il minore di è in realtà minore o uguale.
            if (op == '>' and val_g > soglia) or (op == '<' and val_g <= soglia):
                res.append(gid)
        return res

    def statistica_globale(self):
        """Mostra statistiche aggregate e i migliori giocatori e polisportive."""
        print("\n--- Statistica Globale ---")
        attivi = {gid: g for gid, g in self.giocatori.items() if gid not in self.morti and not g.ritirato}
        n_att = len(attivi)
        print("\n[ Statistiche Giocatori Attivi ]")
        if n_att == 0:
            print("Nessun giocatore attivo trovato.")
        else:
            self._statistiche_popolazione(attivi)
        print("\n[ TOP Players per Caratteristica (Attivi) ]")
        if n_att > 0:
            self._migliori_per_caratteristica(attivi)
        else:
            print("Nessun giocatore attivo per TOP Players.")
        print("\n[ TOP Polisportiva per ICT ]")
        if not self.polisportive:
            print("Nessuna polisportiva esistente.")
        else:
            top_p = max(self.polisportive.values(), key=lambda p: p.indicecollettivotesserati)
            print(f"  Migliore Polisportiva: {top_p.nome}\n  Indice Collettivo Tesserati (ICT): {top_p.indicecollettivotesserati:.2f}")
        print("-" * 75)

    def _statistiche_popolazione(self, attivi):
        n_att = len(attivi)
        m, f, et_g, et_m, et_f, icv_t, n_t, n_i = 0, 0, 0, 0, 0, 0., 0, 0
        nomi, cogn = set(), set()
        for g in attivi.values():
            et_g += g.eta
            icv_t += g.indice_collettivo_valore
            nomi.add(g.nome)
            cogn.add(g.cognome)
            if g.sesso == 'm':
                m += 1
                et_m += g.eta
            else:
                f += 1
                et_f += g.eta
            if g.appartenenza != "*":
                n_t += 1
            if g.ipovedente:
                n_i += 1
        pm = m * 100. / n_att
        pf = f * 100. / n_att
        pt = n_t * 100. / n_att
        pl = 100. - pt
        pipo = n_i * 100. / n_att
        e_m_a = (et_g / n_att / anno) if anno > 0 else 0.
        e_m_m = (et_m / m / anno) if m > 0 and anno > 0 else 0.
        e_m_f = (et_f / f / anno) if f > 0 and anno > 0 else 0.
        print(f" Popolazione: {n_att}")
        print(f" Sesso: {m} Uomini ({pm:.1f}%), {f} Donne ({pf:.1f}%)")
        print(f" Età media (anni sim): {e_m_a:.1f} (U:{e_m_m:.1f}, D:{e_m_f:.1f})")
        print(f" Stato: {n_t} Tesserati ({pt:.1f}%), {n_att - n_t} Liberi ({pl:.1f}%)")
        print(f" ICV medio: {icv_t / n_att:.2f}")
        print(f" Ipovedenti: {n_i} ({pipo:.1f}%)")
        print(f" Nomi Unici: {len(nomi)}, Cognomi Unici: {len(cogn)}")

    def _migliori_per_caratteristica(self, attivi):
        top = dict.fromkeys(sorted(ATTRIBUTI_BASE_CON_ALLENABILI), (-1.0, None))
        for gid, player in attivi.items():
            for sk_base in top:
                total_value = player._get_valore_totale(sk_base)
                if total_value > top[sk_base][0]:
                    top[sk_base] = (total_value, gid)
        print(f"{'Caratteristica':<25} {'Valore':<7} {'%':<5} {'ID':<5} {'Nome Giocatore':<30} {'Età(A/M/G)':<10} {'Club'}")
        print("-" * 97)
        for sk_base, (max_val, p_id) in top.items():
            d_name = NOME_ATTR_TO_DISPLAY_MAP.get(sk_base, sk_base.replace('_base', '').title())
            if p_id is not None and p_id in self.giocatori:
                p = self.giocatori[p_id]
                nome_c = f"{p.nome} {p.cognome}"[:30]
                eta_s = formatta_eta_sim(p.eta, True)
                max_t = MAX_TOTALE_PRECISIONE_RESISTENZA if sk_base in CARATTERISTICHE_FISICHE_BASE else MAX_TOTALE_SKILL_GIOCO
                perc = f"({(max_val * 100. / max_t if max_t > 0 else 0.):.0f}%)"
                print(f"{d_name:<25} {max_val:6.2f} {perc:<5} {p_id:<5} {nome_c:<30} {eta_s:<10} {self._club(p)}")
            else:
                print(f"{d_name:<25} {'N/D':<7} {'-':<5} {'-':<5} {'Nessuno':<30} {'-':<10} {'-'}")

    def visualizza_top_10(self):
        print("\n" + "=" * 30 + " TOP 10 " + "=" * 30)
        print("\n--- TOP 10 Giocatori (Attivi, ICV) ---")
        attivi = self._attivi()
        if not attivi:
            print("\n\tNessun attivo.")
        else:
            top10_g = sorted(attivi, key=lambda g: g.indice_collettivo_valore, reverse=True)[:10]
            print(f"{'Pos':<4} {'ID':<5} {'Nome Cognome':<30} {'ICV':<8} {'Età(A/M/G)':<10} {'Club'}")
            print("-" * 80)
            for i, g in enumerate(top10_g, 1):
                n = f"{g.nome} {g.cognome}"[:30]
                print(f"{i:<4} {g.id:<5} {n:<30} {g.indice_collettivo_valore:<8.1f} {formatta_eta_sim(g.eta, True):<10} {self._club(g)}")
        print("\n--- TOP 10 Polisportive (ICT) ---")
        if not self.polisportive:
            print("\n\tNessuna.")
        else:
            top10_p = sorted(self.polisportive.values(), key=lambda p: p.indicecollettivotesserati, reverse=True)[:10]
            print(f"{'Pos':<4} {'Nome Polisportiva':<30} {'ICT':<10} {'Tess':<10} {'Età(A/M/G)'}")
            print("-" * 85)
            for i, p in enumerate(top10_p, 1):
                ts = f"{len(p.tesserati)}/{p.maxtesserati}"
                cpu = " [CPU]" if p.is_cpu_controlled else ""
                nm = (p.nome + cpu)[:30]
                print(f"{i:<4} {nm:<30} {p.indicecollettivotesserati:<10.1f} {ts:<10} {p.eta_sim(self.data_sim)}")
        print("\n" + "=" * 85)

    def _copia_tesserati_attivi_in_vlt(self):
        if self.attiva:
            ids = [gid for gid in self.attiva.tesserati if gid in self.giocatori and gid not in self.morti and not self.giocatori[gid].ritirato]
            self.mondo.risultati_ultima_ricerca = ids
            print(f"\nTrovati {len(ids)} tesserati ATTIVI. Copiati in VLT.")
        else:
            print("\n\tNessuna poli attiva.")

    # Allenamento.

    def allenamento_giocatori_tesserati(self):
        if not self.attiva:
            print("\n\tAttiva richiesta.")
            return
        poli = self.attiva
        print(f"\n--- Allenamenti {poli.nome} ---")
        allenabili = [gid for gid in list(poli.tesserati) if gid in self.giocatori and gid not in self.morti and not self.giocatori[gid].ritirato
                      and not self.giocatori[gid].infortunato and int(self.giocatori[gid].puntiesperienza or 0) > 0]
        if not allenabili:
            print("\nNessun atleta idoneo.")
            return
        print(f"{len(allenabili)} atleti con XP.")
        n_allenati = 0
        lasciati = []
        for gid in allenabili:
            if gid not in self.giocatori or self.giocatori[gid].appartenenza != poli.nome:
                continue
            g = self.giocatori[gid]
            xp_pre = g.puntiesperienza
            icv_pre = g.indice_collettivo_valore
            self._allena_singolo_giocatore(g)
            if g.puntiesperienza < xp_pre:
                n_allenati += 1
                g.aggiorna_icv()
                icv_post = g.indice_collettivo_valore
                print(f"-> XP Spesi:{xp_pre - g.puntiesperienza}. ICV:{icv_pre:.1f}->{icv_post:.1f}")
                g_rich = g.gloria_richiesta
                p_gloria = poli.gloria
                prob_esc = max(0., 100. - self.mondo.probabilita_accettazione(p_gloria, g_rich))
                print(f"-> Valutaz: G.Rich={g_rich}, G.Poli={p_gloria} => P.Uscita={prob_esc:.1f}%")
                if caso(prob_esc):
                    print(f"!!! INSODDISFATTO: {g.nome} lascia!")
                    lasciati.append((gid, g.nome, g.cognome))
                    poli_lasc = g.appartenenza
                    g.appartenenza = "*"
                    self.mondo.annota(g, f"Lascia {poli_lasc}, {accorda(g.sesso, 'insoddisfatto')}.")
                    if poli_lasc in self.polisportive:
                        self.polisportive[poli_lasc].rimuovi_tesserato(gid, icv_post)
                        self.mondo.annota(self.polisportive[poli_lasc], f"{g.nome} {g.cognome} se ne va, {accorda(g.sesso, 'insoddisfatto')}.")
        poli.aggiorna_ict(self.giocatori, self.morti)
        poli.aggiorna_gloria(self.giocatori, self.morti)
        print(f"\n--- Allenamento {poli.nome} terminato ({n_allenati} allenati) ---")
        if lasciati:
            print("Atleti che hanno lasciato:")
            for id_l, n, c in lasciati:
                print(f"- ID:{id_l} {n} {c}")
        print(f"Stato finale {poli.nome}: ICT={poli.indicecollettivotesserati:.1f}, G={poli.gloria}")

    def _allena_singolo_giocatore(self, g):
        while int(g.puntiesperienza or 0) > 0:
            print(f"\nAllenando: {g.nome} {g.cognome} (ID:{g.id}, XP:{int(g.puntiesperienza or 0)})")
            if g.infortunato:
                print(f"{g.nome} infortunato.")
                return
            if g.ipovedente:
                print("(Ipovedente - Sconto XP)")
            try:
                scelta = menu(d=MENU_ALLENAMENTO, p="Caratteristica (ESC/Invio=Fine)? ", keyslist=True, pager=PAGINAZIONE_LISTE, show=True, show_on_filter=True)
                if scelta is None or scelta == '':
                    break
                attr_a = ATTRIBUTI_ALLENABILI_MAP.get(scelta.lower())
                if not attr_a or not hasattr(g, attr_a):
                    print("\n\tCodice non valido.")
                    continue
                self._allena_caratteristica(g, scelta, attr_a)
            except EOFError:
                print("\nInterrotto.")
                break
        print(f"\nFine allenamento per {g.nome}.")

    def _allena_caratteristica(self, g, scelta, attr_a):
        """Una spesa di esperienza su una caratteristica, con proposta e conferma."""
        is_f = e_fisica(attr_a)
        nome_d = MENU_ALLENAMENTO.get(scelta, "?").replace(';', '')
        val_a = getattr(g, attr_a, 0.)
        val_b = getattr(g, attr_a.replace('_allenata', '_base'), 0.)
        lim_a, lim_t = limiti(attr_a)
        val_t = val_b + val_a
        print(f"\nScelto: {nome_d}")
        print(f" Allenato:{val_a:.3f}(max {lim_a:.1f})")
        print(f" Totale:{val_t:.3f}(max {lim_t:.1f})")
        if val_a >= lim_a or val_t >= lim_t:
            print("** Già al massimo! **")
            input(" INVIO...")
            return
        costo_pt = calcola_costo_xp_per_punto(val_a, is_f, g.ipovedente)
        print(f" Costo:{costo_pt:.1f} XP/+1.0pt")
        xp_max = int(g.puntiesperienza or 0)
        xp_spend = int(dgt(f"XP da spendere (max {xp_max}, 0=Annulla)? ", "i", imin=0, imax=xp_max))
        if xp_spend == 0:
            print("-> Annullato.")
            return
        n_a_f, _guadagno, limitato = guadagno(val_a, val_b, xp_spend, costo_pt, lim_a, lim_t)
        guad_eff = max(0., n_a_f - val_a)
        xp_eff = xp_spend
        if limitato:
            xp_eff = min(xp_spend, math.ceil(guad_eff * costo_pt), xp_max)
            print("INFO: Guadagno limitato.")
        xp_eff = min(xp_eff, xp_max)
        xp_rimb = xp_spend - xp_eff
        if xp_eff > 0 and guad_eff > 1e-4:
            print(f"\nProposta: Spendi {xp_eff} XP per +{guad_eff:.3f} pt.")
            if xp_rimb > 0:
                print(f"({xp_spend}-{xp_rimb}={xp_eff})")
            print(f" {nome_d}(Allenata)-> {n_a_f:.3f}")
            print(f" Totale-> {val_b + n_a_f:.3f}")
            if key(" Confermi(S/n)? ").lower() != 'n':
                setattr(g, attr_a, n_a_f)
                g.puntiesperienza = max(0, xp_max - xp_eff)
                g.annota_allenamento(self.data_sim, attr_a.replace('_allenata', '_base'), val_b + val_a, val_b + n_a_f)
                print("-> Applicato!")
            else:
                print("-> Annullato.")
        else:
            print("\nNessun allenamento.")
            if xp_rimb > 0 and xp_spend > 0:
                print(f"({xp_spend} XP rimborsati).")

    # Partite.

    def _pausa_punto(self, prompt):
        """Fra un punto e l'altro della cronaca in console: aspetta un tasto."""
        try:
            key(prompt)
        except EOFError:
            print("Partita interrotta.")
            raise

    def _giocatore_per_partita(self, domanda, escluso=None):
        """Chiede un giocatore per l'amichevole; None, dopo aver spiegato il perché, se non va bene."""
        gid = dgt(domanda, "i", imin=1)
        if escluso is not None and gid == escluso:
            print("\tERRORE: I giocatori devono essere diversi.")
            return None
        if gid not in self.giocatori:
            print(f"\tERRORE: Giocatore ID {gid} non trovato.")
            return None
        g = self.giocatori[gid]
        if g.ritirato:
            print(f"\tATTENZIONE: {g.nome} è ritirato!")
            return None
        if g.infortunato:
            print(f"\tATTENZIONE: {g.nome} è infortunato!")
            return None
        return gid

    def organizza_partita_amichevole(self):
        """Chiede i dettagli e avvia una partita amichevole tra due giocatori."""
        print("\n--- Organizza Partita Amichevole ---")
        try:
            id1 = self._giocatore_per_partita("ID Giocatore 1? ")
            if id1 is None:
                return
            id2 = self._giocatore_per_partita("ID Giocatore 2? ", escluso=id1)
            if id2 is None:
                return
            g1 = self.giocatori[id1]
            g2 = self.giocatori[id2]
            print(f"\nPartita: {g1.nome} {g1.cognome} (ID:{id1}) vs {g2.nome} {g2.cognome} (ID:{id2})")
            set_input = dgt("Al meglio di quanti Set (3 o 5)? ", "i", imin=3, imax=5)
            num_set = 5 if set_input == 5 else 3
            print(f"Partita al meglio dei {num_set} set.")
            print("\nModalità Visualizzazione Risultati:")
            opzioni_output = {'R': "Solo Risultato finale", 'C': "Cronaca in Console (punto per punto)", 'F': "Salva Cronaca su File"}
            scelta_output = menu(d=opzioni_output, p="Scegli modalità (R/C/F)? ", keyslist=True, show=True)
            modalita = {'C': MODALITA_OUTPUT_CONSOLE, 'F': MODALITA_OUTPUT_FILE}.get(scelta_output, MODALITA_OUTPUT_RISULTATO)
            print("Avvio simulazione partita...")
            risultato = MotorePartita(self.mondo, mostra=print, pausa=self._pausa_punto).gioca_partita(id1, id2, num_set, modalita)
            if risultato.get('error'):
                print(f"\nErrore durante la partita: {risultato['error']}")
            else:
                print("\n--- Riepilogo Partita Amichevole ---")
                v_id = risultato.get('vincitore_id')
                p_id = risultato.get('perdente_id')
                print(f"Vincitore: ID {v_id} ({self.giocatori[v_id].nome} {self.giocatori[v_id].cognome})")
                print(f"Perdente:  ID {p_id} ({self.giocatori[p_id].nome} {self.giocatori[p_id].cognome})")
                print(f"Punteggio Set: {risultato.get('punteggio_set')}")
                if risultato.get('log_path'):
                    print(f"Cronaca completa disponibile in: {risultato['log_path']}")
        except (ValueError, TypeError) as e_input:
            print(f"\nERRORE Input/Tipo non valido: {e_input}")
            print("Operazione partita annullata.")
        except EOFError:
            print("\nOperazione annullata (EOF).")
        input("\nPremi INVIO per tornare al menu...")

    # Polisportive.

    def menu_polisportive(self):
        while True:
            print("\n" + "-" * 30 + " Menu Polisportive " + "-" * 30)
            print(f"Attiva: <{self.attiva.sommario(self.data_sim)}>" if self.attiva else "<Nessuna Attiva>")
            try:
                scelta = menu(d=POLIMENU, keyslist=True, pager=PAGINAZIONE_LISTE, show=False, show_on_filter=True)
                if scelta is None:
                    break
                if scelta and scelta != '?':
                    self.comandi_eseguiti += 1
                if scelta == '?':
                    continue
                comandi = {
                    'VLE': self._lista_polisportive, 'APR': self._apri_nuova_polisportiva, 'CPA': self._cambia_polisportiva_attiva,
                    'VSP': self._scheda_polisportiva, 'VGT': self._tesserati_attiva, 'VGP': self.visualizza_giocatori_papabili,
                    'TEG': self._tessera_giocatore, 'ESG': self._espelli_giocatore, 'CHI': self._chiudi_polisportiva_attiva,
                    'MPP': self._modifica_password_polisportiva,
                }
                serve_attiva = {'VSP', 'VGP', 'TEG', 'ESG', 'CHI', 'MPP'}
                if scelta in comandi:
                    if scelta in serve_attiva and not self.attiva:
                        print(ATTIVA_RICHIESTA)
                    else:
                        comandi[scelta]()
                else:
                    print(f"\n\tComando '{scelta}' non valido.")
                if scelta == 'CHI' and not self.attiva:
                    break
            except EOFError:
                print("\nUscita (EOF)...")
                break
        print("\nRitorno menu principale...")

    def _lista_polisportive(self):
        if self.polisportive:
            self.visualizza_lista(sorted(self.polisportive.keys()), "Lista Polisportive", "polisportiva")
        else:
            print("\n\tNessuna.")

    def _scheda_polisportiva(self):
        print(self.attiva)
        self._stampa_dettagli_tesserati_polisportiva()

    def _tesserati_attiva(self):
        if self.attiva and self.attiva.tesserati:
            self.visualizza_lista(sorted([gid for gid in self.attiva.tesserati if gid in self.giocatori]), f"Tesserati {self.attiva.nome}", "giocatore")
        else:
            print("Nessun tesserato." if self.attiva else ATTIVA_RICHIESTA)

    def _stampa_dettagli_tesserati_polisportiva(self):
        """Stampa dettagli aggiuntivi sui tesserati della polisportiva attiva."""
        if not self.attiva or not self.attiva.tesserati:
            return
        tesserati = [self.giocatori[gid] for gid in self.attiva.tesserati if gid in self.giocatori and gid not in self.morti]
        if not tesserati:
            print("Nessun tesserato valido trovato per statistiche dettagliate.")
            return
        maschi = sum(1 for g in tesserati if g.sesso == 'm')
        femmine = len(tesserati) - maschi
        ipovedenti = sum(1 for g in tesserati if g.ipovedente)
        eta_media_str = formatta_eta_sim(int(sum(g.eta for g in tesserati) / len(tesserati)), formato_breve=True)
        print("\nDettagli Tesserati:")
        print(f"  Composizione: {maschi} Uomini, {femmine} Donne ({len(tesserati)} totali)")
        print(f"  Età Media (Sim): {eta_media_str}, Ipovedenti: {ipovedenti}")
        print("-" * 30)

    def visualizza_giocatori_papabili(self):
        if not self.attiva:
            print("\n\tAttiva richiesta.")
            return
        poli = self.attiva
        try:
            target = float(dgt("P.Acc. target [%]? (0-100, INVIO=100): ", "f", fmin=0., fmax=100., default=100.))
        except (ValueError, TypeError, EOFError):
            print("\nInput non valido.")
            return
        while True:
            print(f"\n--- Papabili per {poli.nome} (G:{poli.gloria}) ---")
            mov_rim = LIMITE_MOVIMENTI_PER_TICK - poli.movimenti_oggi
            print(f"Mov.tick rimasti: {mov_rim}/{LIMITE_MOVIMENTI_PER_TICK}")
            if mov_rim <= 0:
                print("Limite movimenti.")
                break
            liberi = [g for gid, g in self.giocatori.items() if g.appartenenza == "*" and not g.ritirato and gid not in self.morti]
            if not liberi:
                print("\n\tNessun libero.")
                break
            candidati = []
            for g in liberi:
                prob = self.mondo.probabilita_accettazione(poli.gloria, g.gloria_richiesta)
                candidati.append((abs(prob - target), prob, g))
            candidati.sort(key=lambda x: (-x[1], -x[2].indice_collettivo_valore))
            top20 = candidati[:20]
            diz_papabili = {}
            hdr = f"{'P.Acc(%)':<8} {'Età(A/M/G)':<10} {'Nome Cognome':<25} {'Flg':<5} {'ICV'}"
            print("\n" + hdr + "\n" + "-" * (len(hdr) + 2))
            for _, prob, g in top20:
                flg = "".join([f for a, f in MAPPA_FLAG_SOMMARIO.items() if getattr(g, a, False)])
                flg_s = f"[{flg}]" if flg else ""
                nome = f"{g.nome} {g.cognome}"[:25]
                diz_papabili[str(g.id)] = f"{prob:5.1f}% {'':<1} {formatta_eta_sim(g.eta, True):<10} {nome:<25} {flg_s:<5} ICV:{g.indice_collettivo_valore:6.1f}"
            scelta = menu(d=diz_papabili, p="Tesserare? (ID o ESC): ", show=True, show_on_filter=True, pager=PAGINAZIONE_LISTE, keyslist=False, ntf="ID non in lista.")
            if scelta is None:
                print("Uscita.")
                break
            try:
                gid = int(scelta)
            except (ValueError, TypeError):
                print(f"\n\tID '{scelta}' non valido.")
                continue
            if scelta in diz_papabili:
                self._tessera_giocatore(gid)
            else:
                print(f"\n\tID {gid} non visualizzato.")
        print("\nRitorno Menu Poli...")

    def _chiedi_password(self, prompt="Password? "):
        return dgt(prompt, smin=1, smax=30, pwd=True)

    def _apri_nuova_polisportiva(self):
        print("\n--- Apertura Nuova Polisportiva ---")
        try:
            nome = dgt(f"Nome ({NOME_POLISPORTIVA_MIN}-{NOME_POLISPORTIVA_MAX})? ", "s", smin=NOME_POLISPORTIVA_MIN, smax=NOME_POLISPORTIVA_MAX)
            problema = self.mondo.problema_nome_polisportiva(nome)
            if problema:
                print(f"\n\t{problema}")
                return
            pwd1 = dgt("Password, facoltativa (INVIO per nessuna): ", smax=30, pwd=True)
            if pwd1 and pwd1 != self._chiedi_password("Conferma: "):
                print("\n\tPassword non coincidono.")
                return
            attiva = key("Attivarla ora (S/n)? ").lower() != 'n'
            nuova = self.mondo.fonda_polisportiva(nome, pwd1 or None, attiva)
            print(f"\nPoli '{nuova.nome}' creata ({self.data_sim:%Y-%m-%d %H:%M}).")
            if attiva:
                print("Attivata.")
        except EOFError:
            print("\nAnnullato.")

    def _cambia_polisportiva_attiva(self):
        print("\n--- Cambia Polisportiva Attiva ---")
        poli_u = {n: p for n, p in self.polisportive.items() if not p.is_cpu_controlled}
        if not poli_u:
            print("\n\tNessuna poli utente.")
            return
        print("Polisportive Utente:")
        for p in poli_u.values():
            print(f"- {p.sommario(self.data_sim)}")
        try:
            nome = dgt("Nome poli da attivare: ", "s", smin=1, smax=NOME_POLISPORTIVA_MAX)
            p_sel = self.mondo.trova_polisportiva(nome)
            if p_sel is None or p_sel.is_cpu_controlled:
                print(f"\n\tPoli utente '{nome}' non trovata.")
                return
            if p_sel.protetta and not p_sel.verifica_password(self._chiedi_password(f"Password '{p_sel.nome}': ")):
                print("\n\tPassword errata.")
                return
            self.mondo.miapolisportiva_attiva = p_sel
            print(f"\n'{p_sel.nome}' attivata.")
        except EOFError:
            print("\nAnnullato.")

    def _tessera_giocatore(self, giocatore_id=None):
        if not self.attiva:
            print("\n\tAttiva richiesta.")
            return
        poli = self.attiva
        if poli.movimenti_oggi >= LIMITE_MOVIMENTI_PER_TICK:
            print(f"\n\tLimite {LIMITE_MOVIMENTI_PER_TICK} movimenti tick.")
            return
        if len(poli.tesserati) >= poli.maxtesserati:
            print(f"\n\tLimite {poli.maxtesserati} tesserati.")
            return
        try:
            gid = giocatore_id
            if gid is None:
                print(f"\n--- Tesseramento {poli.nome} ---")
                print(f"G:{poli.gloria}. MovTick:{poli.movimenti_oggi}/{LIMITE_MOVIMENTI_PER_TICK}")
                gid = int(dgt("ID giocatore? ", "i", imin=1))
            else:
                print(f"\n--- Tentativo Tess. ID:{gid} ({poli.nome}) ---")
                print(f"MovTick:{poli.movimenti_oggi}/{LIMITE_MOVIMENTI_PER_TICK}")
            if gid not in self.giocatori:
                print(f"\n\tID {gid} non trovato.")
                return
            g = self.giocatori[gid]
            problema = self.mondo.problema_offerta(poli, g)
            if problema:
                print(f"\n\t{problema}")
                return
            richiesta = ingaggio_richiesto(g, poli)
            print(f"\tChiede {richiesta} euro d'ingaggio e {stipendio(g)} euro al mese. Cassa: {poli.cassa} euro.")
            if poli.cassa <= 0:
                print("\n\tCassa vuota.")
                return
            ingaggio = int(dgt("Ingaggio da offrire? ", "i", imin=1, imax=poli.cassa, default=min(richiesta, poli.cassa)))
            accetta, prob = self.mondo.offerta(poli, g, ingaggio)
            print(f"Tentativo... (Mov.{poli.movimenti_oggi}/{LIMITE_MOVIMENTI_PER_TICK})")
            print(f"\tProb.acc:{prob:.1f}%")
            if accetta:
                print(f"\t{g.nome} ACCETTA!")
                print(f"\n{g.nome} tesserato!")
            else:
                print(f"\t{g.nome} RIFIUTA!")
            print(f"Mov.tick rimasti: {LIMITE_MOVIMENTI_PER_TICK - poli.movimenti_oggi}")
            if giocatore_id is not None:
                input("...INVIO...")
        except (ValueError, TypeError):
            print("\n\tID non valido.")
        except EOFError:
            print("\nAnnullato.")

    def _espelli_giocatore(self):
        if not self.attiva:
            print("\n\tAttiva richiesta.")
            return
        poli = self.attiva
        print(f"\n--- Svincolo da {poli.nome} ---")
        print(f"Mov.Tick:{poli.movimenti_oggi}/{LIMITE_MOVIMENTI_PER_TICK}")
        ids_val = [gid for gid in poli.tesserati if gid in self.giocatori]
        if not ids_val:
            print("\n\tNessun tesserato.")
            return
        self.visualizza_lista(sorted(ids_val), f"Tesserati {poli.nome}", "giocatore")
        try:
            gid = int(dgt("ID da svincolare? ", "i", imin=1))
            if gid not in ids_val:
                print(f"\n\tID {gid} non tesserato qui.")
                return
            g = self.giocatori[gid]
            if key(f"Confermi lo svincolo di {g.nome} {g.cognome}(ID:{gid})? (s/N) ").lower() != 's':
                print("\nAnnullato.")
                return
            try:
                self.mondo.svincola(poli, g)
            except ValueError as e:
                print(f"\n\t{e}")
                return
            print(f"\n{g.nome} {g.cognome}(ID:{gid}) svincolato.")
            print(f"Mov.tick rimasti:{LIMITE_MOVIMENTI_PER_TICK - poli.movimenti_oggi}")
        except (ValueError, TypeError):
            print("\n\tID non valido.")
        except EOFError:
            print("\nAnnullato.")

    def _chiudi_polisportiva_attiva(self):
        if not self.attiva:
            print("\n\tNessuna poli attiva.")
            return
        poli = self.attiva
        print(f"\n--- Chiusura Definitiva {poli.nome} ---")
        print("ATT: Irreversibile.")
        try:
            if poli.protetta and not poli.verifica_password(self._chiedi_password(f"Password '{poli.nome}': ")):
                print("\n\tPassword errata.")
                return
            if dgt("Scrivi 'CHIUDI': ", "s", smax=6) != "CHIUDI":
                print("\nConferma non valida.")
                return
            n_lib = self.mondo.chiudi_polisportiva(poli)
            print(f"\nPoli '{poli.nome}' chiusa. {n_lib} liberati.")
            print("Nessuna poli attiva.")
        except EOFError:
            print("\nAnnullato.")

    def _modifica_password_polisportiva(self):
        if not self.attiva:
            print("\n\tNessuna poli attiva.")
            return
        poli = self.attiva
        print(f"\n--- Password di {poli.nome} ---")
        try:
            if poli.protetta and not poli.verifica_password(self._chiedi_password("Password attuale: ")):
                print("\n\tPassword attuale errata.")
                return
            pwd1 = dgt("Nuova password (INVIO per toglierla): ", smax=30, pwd=True)
            if pwd1 and pwd1 != self._chiedi_password("Conferma nuova: "):
                print("\n\tNon coincidono.")
                return
            poli.imposta_password(pwd1)
            print("\nPassword modificata." if pwd1 else "\nPassword tolta: la polisportiva non è più protetta.")
        except EOFError:
            print("\nAnnullato.")
