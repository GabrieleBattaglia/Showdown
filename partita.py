"""
La facciata del motore di partita di MESS verso il mondo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto); dalla tappa 9
Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-06 con la tappa 2 del piano, dallo smontaggio di sd.py, con il vecchio motore e i
suoi difetti. Con la tappa 9, il 2026-10-07, il motore è nuovo e sta nel pacchetto motore, secondo
le regole IBSA della decisione D25: qui resta la facciata, con lo stesso nome e la stessa firma
pubblica di prima, e una sola responsabilità, quella di scrivere nel mondo. Il motore gioca e
restituisce eventi, esiti e statistiche; la facciata controlla chi può giocare, registra il
risultato nella carriera e nei diari, decide gli infortuni con un generatore nato dal seme della
partita, e salva la cronaca, una partita per file nella cartella cronache.
Il problema P1 è risolto: la catena degli esiti non trasforma più quasi ogni azione in un fallo, e
ognuno gioca con la sua stanchezza. La vecchia firma di gioca_partita resta, con le tre modalità:
solo il risultato, la cronaca punto per punto nella console, e la cronaca su file.
Il motore non stampa e non chiede nulla: le righe le consegna alla funzione mostra, e dove aspetta
un tasto chiama la funzione pausa. Le passa chi lo usa; se non le passa, lavora in silenzio.
Dal 2026-10-08, regola di Gabriele, ogni giocatore gioca al massimo un'amichevole per giorno
simulato, perché ogni amichevole dà punti allenamento: la facciata la controlla prima di giocare,
per la finestra e per l'interfaccia testuale, e alla registrazione segna il giorno nei due giocatori.
Le partite del torneo, e quelle giocate senza registrarle, non contano. La cronaca su file può
ricevere il momento reale e il giorno simulato dell'incontro, per chi la salva più tardi.
Con la decisione D29, tappa 10, l'amichevole da assistere dal vivo si gioca e si registra subito come
le altre, e porta con sé un incontro gemello, con lo stesso seme, che la finestra dal vivo svolge un
momento alla volta alla velocità di gioco scelta.
Dalla tappa 11, il 2026-10-09, decisione D31, i punti allenamento di un incontro vengono da una
formula, al posto della vecchia tabella: una base, mezzo punto per ogni set vinto e un punto a chi
vince, così al meglio dei 5 se ne prendono appena il 13 per cento in più; il premio al più debole
resta, anche quando perde, ma il distacco si misura sulla somma pesata, che non dipende dalla scala
del valore. Con la registrazione arrivano anche l'esperienza dell'incontro e la costanza recente,
e l'intensità dell'allenamento cambia il rischio d'infortunio. Tornei e sfide sono gli agganci
della tappa 12, e il giorno dell'ultima amichevole si segna soltanto per le amichevoli.
"""

import random

import esperienza
import infortuni
import valore
from costanti import (
    COSTANZA_PER_PARTITA,
    DECADIMENTO_COSTANZA,
    DISTACCO_PIU_DEBOLE,
    MODALITA_OUTPUT_CONSOLE,
    MODALITA_OUTPUT_FILE,
    MODALITA_OUTPUT_RISULTATO,
    PA_BONUS_PIU_DEBOLE,
    PA_BONUS_SFIDA,
    PA_BONUS_TORNEO,
    PA_PARTITA_BASE,
    PA_PER_SET_VINTO,
    PA_VITTORIA,
)
from motore import COMPLETO, ESSENZIALE, SQUADRE, TARATURA, Incontro, Squadra, formato_singolare
from motore import cronaca as C
from motore import eventi as E
from utilita import adesso

PROMPT_PUNTO = "\rUn tasto per il punto successivo.\r"
INTERROTTA = "Partita interrotta dall'utente."
# Gli eventi di apertura e chiusura che la facciata scrive da sé, prima e dopo la cronaca.
_APERTURA_E_CHIUSURA = (E.INIZIO_INCONTRO, E.FINE_INCONTRO)


def _silenzio(*_args, **_kwargs):
    """Al posto di mostra e pausa quando chi usa il motore non le passa."""


def _punti(valore_dei_punti):
    """I punti allenamento con la virgola, senza decimali quando sono interi: 4, 2,5."""
    return f"{valore_dei_punti:g}".replace(".", ",")


class MotorePartita:
    """Gioca le partite fra i giocatori di un mondo, e le registra nelle loro carriere."""

    def __init__(self, mondo, mostra=None, pausa=None, taratura=None):
        self.mondo = mondo
        self.mostra = mostra or _silenzio
        self.pausa = pausa or _silenzio
        self.taratura = taratura or TARATURA

    @property
    def giocatori(self):
        return self.mondo.giocatori

    # Chi può giocare.

    def problema_incontro(self, id_g1, id_g2):
        """None se i due possono giocare un incontro, altrimenti il motivo."""
        if id_g1 not in self.giocatori or id_g2 not in self.giocatori:
            return "ID giocatore non valido."
        if id_g1 == id_g2:
            return "I giocatori devono essere diversi."
        g1, g2 = self.giocatori[id_g1], self.giocatori[id_g2]
        if g1.ritirato or g2.ritirato:
            return "Uno o entrambi ritirati."
        if not g1.puo_giocare or not g2.puo_giocare:
            return "Uno o entrambi infortunati."
        return None

    def problema_amichevole(self, id_g1, id_g2):
        """None se i due possono giocare un'amichevole oggi, altrimenti il motivo: quelli dell'incontro, e l'amichevole già giocata nel giorno simulato."""
        errore = self.problema_incontro(id_g1, id_g2)
        if errore:
            return errore
        oggi = self.mondo.datetime_corrente_simulazione
        gia = [g for g in (self.giocatori[id_g1], self.giocatori[id_g2]) if g.ha_giocato_amichevole(oggi)]
        if not gia:
            return None
        chi = " e ".join(f"{g.nome} {g.cognome}" for g in gia)
        return f"Oggi {chi} {'ha' if len(gia) == 1 else 'hanno'} già giocato un'amichevole: se ne gioca al massimo una per giorno simulato."

    def disponibili(self, giocatori):
        """Fra i giocatori dati, quelli che possono giocare un'amichevole oggi, in ordine di numero."""
        oggi = self.mondo.datetime_corrente_simulazione
        return sorted((g for g in giocatori if g.puo_giocare_amichevole(oggi)), key=lambda g: g.id)

    def nomi(self, risultato):
        """I nomi della cronaca per un incontro fra giocatori del mondo: un singolare, o una gara a squadre col nome delle squadre."""
        a, b = risultato.parti
        if risultato.formato.tipo == "squadre":
            squadre = tuple(Squadra(nome, tuple(self.giocatori[gid] for gid in ids)) for nome, ids in zip(risultato.nomi_squadre, (a, b), strict=True))
            return C.nomi_dei_giocatori([*squadre[0].giocatori, *squadre[1].giocatori], squadre=squadre)
        return C.nomi_dei_giocatori([self.giocatori[a], self.giocatori[b]])

    # La vecchia firma.

    def gioca_partita(self, id_g1, id_g2, num_set_target, modalita_output=MODALITA_OUTPUT_RISULTATO, info_torneo=None, seme=None, registra=True):
        """
        Simula una partita fra due giocatori e ne restituisce il risultato, nel dizionario di
        sempre più seme, risultato ed eventi. Con modalità risultato si gioca in modalità
        essenziale; con console e file in modalità completa, con la cronaca. Senza torneo, ed
        è l'amichevole dell'interfaccia testuale, vale la regola di una al giorno, se si registra.
        """
        risposta = {
            'id_originale_g1': id_g1, 'id_originale_g2': id_g2, 'num_set_target': num_set_target,
            'vincitore_id': None, 'perdente_id': None, 'punteggio_set': [],
            'stats_g1': {'goal': 0, 'falli_fatti': 0, 'falli_subiti': 0, 'penalita': 0},
            'stats_g2': {'goal': 0, 'falli_fatti': 0, 'falli_subiti': 0, 'penalita': 0},
            'log_partita_completa': [], 'log_path': None, 'error': None, 'seme': None, 'risultato': None, 'eventi': None,
        }
        errore = self.problema_amichevole(id_g1, id_g2) if registra and not info_torneo else self.problema_incontro(id_g1, id_g2)
        formato = None
        if errore is None:
            try:
                formato = formato_singolare(num_set_target)
            except ValueError as e:
                errore = str(e)
        if errore:
            risposta['error'] = errore
            self.mostra(f"ERRORE: {errore}")
            return risposta
        g1, g2 = self.giocatori[id_g1], self.giocatori[id_g2]
        nomi = C.nomi_dei_giocatori([g1, g2])
        self.mostra(f"Inizio dell'incontro: {nomi['A'].testo} contro {nomi['B'].testo}, al meglio dei {num_set_target} set.")
        completo = modalita_output in (MODALITA_OUTPUT_CONSOLE, MODALITA_OUTPUT_FILE)
        incontro = Incontro(g1, g2, formato, seme=seme, dettaglio=COMPLETO if completo else ESSENZIALE, taratura=self.taratura)
        risposta['seme'] = incontro.seme
        try:
            for momento in incontro.momenti():
                if modalita_output == MODALITA_OUTPUT_CONSOLE:
                    righe = [riga for evento in momento.eventi if evento.tipo not in _APERTURA_E_CHIUSURA
                             for riga in [C.frase(evento, nomi, C.NORMALE)] if riga]
                    for riga in righe:
                        self.mostra(riga)
                    if momento.genere == "punto":
                        self.pausa(PROMPT_PUNTO)
        except (EOFError, KeyboardInterrupt):
            risposta['error'] = INTERROTTA
            self.mostra(INTERROTTA)
            return risposta
        risultato = incontro.risultato
        self._riempi_risposta(risposta, risultato, nomi, completo)
        if registra:
            for riga in self.registra(risultato, info_torneo):
                self.mostra(riga)
        if modalita_output == MODALITA_OUTPUT_FILE:
            try:
                risposta['log_path'] = self.salva_cronaca(risultato)
            except OSError as e:
                self.mostra(f"ERRORE scrittura della cronaca: {e}")
            else:
                self.mostra(f"Cronaca completa salvata in: {risposta['log_path']}")
        self.mostra(self._riga_finale(risultato, nomi))
        return risposta

    def _riempi_risposta(self, risposta, risultato, nomi, completo):
        id_a, id_b = risultato.parti
        vince_a = risultato.vincitore == "A"
        risposta['vincitore_id'], risposta['perdente_id'] = (id_a, id_b) if vince_a else (id_b, id_a)
        risposta['punteggio_set'] = [tuple(s) for s in risultato.set]
        for chiave, gid in (('stats_g1', id_a), ('stats_g2', id_b)):
            stats = risultato.statistiche[gid]
            risposta[chiave] = {'goal': stats.goal, 'falli_fatti': sum(stats.falli.values()), 'falli_subiti': stats.falli_subiti, 'penalita': stats.penalita}
        risposta['risultato'] = risultato
        risposta['eventi'] = risultato.eventi
        if completo:
            risposta['log_partita_completa'] = C.componi(risultato.momenti, nomi, C.NORMALE)

    @staticmethod
    def _riga_finale(risultato, nomi):
        vince = risultato.vincitore
        sa, sb = risultato.set_vinti
        mio, suo = (sa, sb) if vince == "A" else (sb, sa)
        parziali = ", ".join(f"{a} a {b}" if vince == "A" else f"{b} a {a}" for a, b in risultato.set)
        return f"Fine dell'incontro: vince {nomi[vince].testo}, {mio} set a {suo}: {parziali}."

    # Le partite nuove.

    def gioca_amichevole(self, id_g1, id_g2, set_al_meglio=3, seme=None):
        """
        Un'amichevole in modalità completa, registrata subito: restituisce il RisultatoIncontro,
        con le frasi della registrazione nel campo registrazione. ValueError se non si può giocare,
        anche perché uno dei due ha già giocato un'amichevole oggi.
        """
        risultato, _gemello = self._amichevole(id_g1, id_g2, set_al_meglio, seme, False)
        return risultato

    def amichevole_da_assistere(self, id_g1, id_g2, set_al_meglio=3, seme=None, velocita=1.0):
        """
        L'amichevole della partita dal vivo, decisione D29: si gioca e si registra subito, come
        gioca_amichevole, così chi esce a metà la trova già nel mondo. Restituisce il risultato e un
        incontro gemello, con lo stesso seme e ancora da giocare, che la finestra dal vivo svolge un
        momento alla volta alla velocità di gioco scelta: il gemello nasce prima della registrazione,
        perché l'incontro fotografa i giocatori quando nasce, e un infortunio o un'esperienza nuova
        non lo cambiano. La velocità divide soltanto i tempi, quindi il gemello dà gli stessi punti.
        """
        return self._amichevole(id_g1, id_g2, set_al_meglio, seme, True, velocita)

    def _amichevole(self, id_g1, id_g2, set_al_meglio, seme, con_gemello, velocita=1.0):
        errore = self.problema_amichevole(id_g1, id_g2)
        if errore:
            raise ValueError(errore)
        formato = formato_singolare(set_al_meglio)
        g1, g2 = self.giocatori[id_g1], self.giocatori[id_g2]
        incontro = Incontro(g1, g2, formato, seme=seme, dettaglio=COMPLETO, taratura=self.taratura)
        gemello = None
        if con_gemello:
            gemello = Incontro(g1, g2, formato, seme=incontro.seme, dettaglio=COMPLETO, taratura=self.taratura, velocita=velocita)
        risultato = incontro.gioca()
        risultato.registrazione = self.registra(risultato)
        return risultato, gemello

    def gioca_squadre(self, squadra_a, squadra_b, seme=None, dettaglio=ESSENZIALE):
        """Una gara a squadre. Nella tappa 9 non si registra nella carriera: arriva con la tappa 12."""
        return Incontro(squadra_a, squadra_b, SQUADRE, seme=seme, dettaglio=dettaglio, taratura=self.taratura).gioca()

    # La registrazione nel mondo.

    @staticmethod
    def punti_della_partita(set_vinti_vinc, set_vinti_perd):
        """
        I punti allenamento di un incontro a vincitore e perdente: la base, mezzo punto per set vinto,
        un punto a chi vince. Al meglio dei 3 chi vince prende 4 e chi perde 2 o 2,5; al meglio dei 5
        chi vince 4,5 e chi perde da 2 a 3.
        """
        return PA_PARTITA_BASE + PA_PER_SET_VINTO * set_vinti_vinc + PA_VITTORIA, PA_PARTITA_BASE + PA_PER_SET_VINTO * set_vinti_perd

    @staticmethod
    def piu_debole(g1, g2):
        """
        Il più debole dei due, se ha almeno DISTACCO_PIU_DEBOLE punti di somma pesata in meno, tratti
        compresi; altrimenti None. Attorno alla mediana il distacco vale il 25 per cento del valore.
        """
        forza1 = valore.somma_pesata(g1) + valore.bonus_tratti(g1)
        forza2 = valore.somma_pesata(g2) + valore.bonus_tratti(g2)
        if abs(forza1 - forza2) < DISTACCO_PIU_DEBOLE:
            return None
        return g1 if forza1 < forza2 else g2

    def registra(self, risultato, info_torneo=None, sfida=None):
        """
        Porta il risultato di un singolare nel mondo: partite e set vinti e persi, goal fatti e
        subiti, punti allenamento con i bonus del torneo, della sfida e del più debole, esperienza e
        costanza recente, i diari, e gli infortuni con la loro sede. Senza torneo e senza sfida è
        un'amichevole, e i due giocatori ricordano il giorno simulato in cui l'hanno giocata.
        Restituisce le frasi da mostrare. La gara a squadre non si registra.
        """
        if risultato.formato.tipo != "singolare":
            return []
        id_a, id_b = risultato.parti
        vince_a = risultato.vincitore == "A"
        id_vinc, id_perd = (id_a, id_b) if vince_a else (id_b, id_a)
        g_vinc, g_perd = self.giocatori[id_vinc], self.giocatori[id_perd]
        stats_vinc, stats_perd = risultato.statistiche[id_vinc], risultato.statistiche[id_perd]
        sa, sb = risultato.set_vinti
        set_vinc, set_perd = (sa, sb) if vince_a else (sb, sa)
        g_vinc.partitevinte += 1
        g_perd.partiteperse += 1
        g_vinc.setsvinti += set_vinc
        g_vinc.setspersi += set_perd
        g_perd.setsvinti += set_perd
        g_perd.setspersi += set_vinc
        g_vinc.goalsfatti += stats_vinc.goal
        g_vinc.goalssubiti += stats_perd.goal
        g_perd.goalsfatti += stats_perd.goal
        g_perd.goalssubiti += stats_vinc.goal
        pa_vinc, pa_perd = self.punti_della_partita(set_vinc, set_perd)
        bonus = (PA_BONUS_TORNEO if info_torneo else 0.0) + (PA_BONUS_SFIDA if sfida else 0.0)
        pa_vinc += bonus
        pa_perd += bonus
        debole = self.piu_debole(g_vinc, g_perd)
        if debole is g_vinc:
            pa_vinc += PA_BONUS_PIU_DEBOLE
        elif debole is g_perd:
            pa_perd += PA_BONUS_PIU_DEBOLE
        tipo = esperienza.TORNEO if info_torneo else esperienza.SFIDA if sfida else esperienza.AMICHEVOLE
        for g, punti in ((g_vinc, pa_vinc), (g_perd, pa_perd)):
            g.punti_allenamento += punti
            esperienza.da_partita(g, tipo)
            g.costanza += (1.0 - DECADIMENTO_COSTANZA) * COSTANZA_PER_PARTITA
        if tipo == esperienza.AMICHEVOLE:
            g_vinc.ultima_amichevole = g_perd.ultima_amichevole = self.mondo.datetime_corrente_simulazione
        self._annota_risultato(g_vinc, g_perd, risultato, vince_a, set_vinc, set_perd, tipo)
        frasi = [f"Punti allenamento: {_punti(pa_vinc)} a {g_vinc.nome} {g_vinc.cognome}, {_punti(pa_perd)} a {g_perd.nome} {g_perd.cognome}."]
        caso_degli_infortuni = random.Random(f"infortuni-{risultato.seme}")
        for g in (g_vinc, g_perd):
            frase = infortuni.infortuna(self.mondo, g, risultato.statistiche[g.id].azioni, caso_degli_infortuni)
            if frase:
                frasi.append(frase)
        return frasi

    def _annota_risultato(self, g_vinc, g_perd, risultato, vince_a, set_vinc, set_perd, tipo_incontro):
        """Il risultato nei diari dei due giocatori, ciascuno con i set dal suo punto di vista."""
        tipo = {esperienza.TORNEO: "la partita del torneo", esperienza.SFIDA: "la sfida"}.get(tipo_incontro, "l'amichevole")
        dal_vincitore = [(a, b) if vince_a else (b, a) for a, b in risultato.set]
        set_vincitore = ", ".join(f"{a} a {b}" for a, b in dal_vincitore)
        set_perdente = ", ".join(f"{b} a {a}" for a, b in dal_vincitore)
        self.mondo.annota(g_vinc, f"Vince {tipo} contro {g_perd.nome} {g_perd.cognome}, {set_vinc} set a {set_perd}: {set_vincitore}.")
        self.mondo.annota(g_perd, f"Perde {tipo} contro {g_vinc.nome} {g_vinc.cognome}, {set_perd} set a {set_vinc}: {set_perdente}.")

    # La cronaca su file.

    def salva_cronaca(self, risultato, livello=C.NORMALE, istante=None, data_simulata=None):
        """
        Scrive la cronaca dell'incontro in un file della cartella cronache e ne restituisce il
        percorso. istante e data_simulata sono il momento reale e il giorno simulato dell'incontro,
        per l'intestazione e il nome del file: chi salva più tardi, come la finestra, li ha fissati
        quando si è giocato; senza, valgono quelli di adesso, che per chi salva subito sono gli stessi.
        """
        if risultato.momenti is None:
            raise ValueError("La cronaca c'è soltanto per gli incontri giocati in modalità completa.")
        nomi = self.nomi(risultato)
        istante = istante or adesso()
        data_simulata = data_simulata or self.mondo.datetime_corrente_simulazione
        righe = C.intestazione(risultato, nomi, istante, data_simulata)
        righe += C.componi(risultato.momenti, nomi, livello)
        righe += C.riepilogo(risultato, nomi)
        return C.salva(righe, C.nome_file(nomi, istante))
