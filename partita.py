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
per la finestra, e alla registrazione segna il giorno nei due giocatori.
La cronaca su file può ricevere il momento reale e il giorno simulato dell'incontro, per chi la
salva più tardi.
Con la decisione D29, tappa 10, l'amichevole da assistere dal vivo si gioca e si registra subito come
le altre, e porta con sé un incontro gemello, con lo stesso seme, che la finestra dal vivo svolge un
momento alla volta alla velocità di gioco scelta.
Dalla tappa 11, il 2026-10-09, decisione D31, i punti allenamento di un incontro vengono da una
formula, al posto della vecchia tabella: una base, mezzo punto per ogni set vinto e un punto a chi
vince, così al meglio dei 5 se ne prendono appena il 13 per cento in più; il premio al più debole
resta, anche quando perde, ma il distacco si misura sulla somma pesata, che non dipende dalla scala
del valore. Con la registrazione arrivano anche l'esperienza dell'incontro e la costanza recente,
e l'intensità dell'allenamento cambia il rischio d'infortunio.
Dalla tappa 12, il 2026-10-13, decisione D32, risposte 6, 7 e 8 di Gabriele e la sua regola sugli
infortuni: gli infortuni non si estraggono più qui a fine partita, ma nel motore, a fine set, e
soltanto un quinto ferma il giocatore; il resto sono acciacchi. La facciata dà al motore la base
d'infortunio e il calo dell'acciacco di oggi di ciascuno, e anche al gemello della partita dal vivo,
che così ripete il ritiro e gli acciacchi; poi porta nel mondo quello che il motore ha estratto, con
la durata e il calo da un generatore nato dal seme. Chi si ritira tiene i punti allenamento dei set
giocati; chi vince o perde a tavolino non prende né punti né esperienza, e la partita non entra
nella sua carriera, risposta 8.
Sempre dalla tappa 12, punti 6.5, 6.6 e 10.2 del progetto: i punti di un incontro sono quelli della
formula per il fattore della sua fonte, amichevole, torneo o sfida, e per l'importanza del torneo, e
l'esperienza anche; i vecchi agganci del torneo e della sfida spariscono. La regola di una al giorno
diventa quella di un impegno al giorno, D32: ogni incontro registrato segna il giorno in chi era
presente, amichevole, torneo o sfida, e nel giorno di torneo non si gioca un'amichevole. La
registrazione leggera, senza diario, serve agli incontri del mondo, migliaia al giorno; quelli dei
tuoi tesserati hanno le voci di sempre. E le fotografie: prima di un incontro di torneo o di sfida
dei tuoi tesserati si fotografano i giocatori, così il gemello in differita, giocato anche giorni dopo,
dà gli stessi punti dell'incontro registrato, perché la modalità essenziale e la completa coincidono a
parità di seme. La gara a squadre delle sfide e della coppa entra nella carriera con registra_squadre,
punto 8.7: i titolari prendono la gara, i punti e l'esperienza, le riserve metà dell'esperienza.
"""

import random

import esperienza
import infortuni
import valore
from costanti import (
    ATTRIBUTI_INVECCHIABILI,
    COSTANZA_PER_PARTITA,
    DECADIMENTO_COSTANZA,
    DISTACCO_PIU_DEBOLE,
    GIOCATORI_AL_TAVOLO,
    MODALITA_OUTPUT_CONSOLE,
    MODALITA_OUTPUT_FILE,
    MODALITA_OUTPUT_RISULTATO,
    PA_BONUS_PIU_DEBOLE,
    PA_FATTORE_AMICHEVOLE,
    PA_FATTORE_SFIDA,
    PA_FATTORE_TORNEO,
    PA_PARTITA_BASE,
    PA_PER_SET_VINTO,
    PA_VITTORIA,
)
from modelli import CAMPI_AGGREGATA_GIOCATORE, Giocatore, annota_aggregata
from motore import COMPLETO, ESSENZIALE, RITIRO, SQUADRE, TARATURA, TAVOLINO, Incontro, Squadra, formato_singolare
from motore import cronaca as C
from motore import eventi as E
from utilita import accorda, adesso

PROMPT_PUNTO = "\rUn tasto per il punto successivo.\r"
INTERROTTA = "Partita interrotta dall'utente."
# Gli eventi di apertura e chiusura che la facciata scrive da sé, prima e dopo la cronaca.
_APERTURA_E_CHIUSURA = (E.INIZIO_INCONTRO, E.FINE_INCONTRO)
# Il fattore dei punti allenamento per ogni fonte, D32 e punto 10.2 del progetto.
PA_FATTORE = {esperienza.AMICHEVOLE: PA_FATTORE_AMICHEVOLE, esperienza.TORNEO: PA_FATTORE_TORNEO, esperienza.SFIDA: PA_FATTORE_SFIDA}
# I campi della fotografia di un giocatore, punto 6.5: quelli che servono al motore e alla cronaca.
CAMPI_FOTOGRAFIA = ("id", "nome", "cognome", "sesso", "eta", "temperamento", "esperienza", "costanza", "intensita", "mancino", "ambidestro",
                    "giocorapido", "cambiovelocita", "infortunato", "infortunio_sede", "acciacco_sede", *ATTRIBUTI_INVECCHIABILI)
FORMATO_SQUADRE = "squadre"


def _silenzio(*_args, **_kwargs):
    """Al posto di mostra e pausa quando chi usa il motore non le passa."""


def _punti(valore_dei_punti):
    """I punti allenamento con la virgola, senza decimali quando sono interi e con due al più: 4, 2,5, 1,92."""
    return f"{round(valore_dei_punti, 2):g}".replace(".", ",")


# Le fotografie e i gemelli in differita, punto 6.5 del progetto della tappa 12.

def fotografa(g):
    """
    La fotografia di un giocatore prima di un incontro da riascoltare: soltanto quello che serve al
    motore e alla cronaca, circa 1,2 KB, così il gemello in differita gioca con lui com'era quel giorno.
    """
    return {campo: getattr(g, campo, None) for campo in CAMPI_FOTOGRAFIA}


def da_fotografia(dati):
    """Un Giocatore ricostruito da una fotografia, senza tirare il caso: ha soltanto gli attributi che servono al motore e alla cronaca."""
    g = Giocatore.__new__(Giocatore)
    for campo in CAMPI_FOTOGRAFIA:
        setattr(g, campo, dati.get(campo))
    g.ritirato = False
    return g


def differita_singolare(ga, gb, basi, cali, azioni_iniziali, set_al_meglio):
    """I dati per riascoltare un singolare: le fotografie, le basi d'infortunio, i cali, le azioni iniziali e il formato, in liste di A e di B."""
    cali = cali or {}
    iniziali = azioni_iniziali or {}
    return {"fotografie": [fotografa(ga), fotografa(gb)], "basi": [basi.get(ga.id), basi.get(gb.id)], "cali": [cali.get(ga.id, 0.0), cali.get(gb.id, 0.0)],
            "azioni_iniziali": [iniziali.get(ga.id, 0), iniziali.get(gb.id, 0)], "formato": set_al_meglio}


def differita_squadre(squadra_a, squadra_b, basi, cali, azioni_iniziali=None):
    """
    I dati per riascoltare una gara a squadre: le fotografie dei giocatori di ciascuna, titolari e
    riserve nell'ordine della formazione, i nomi, le basi e i cali, in liste parallele, e il formato.
    Dalla lettura 12 delle decisioni di Gabriele del 14 ottobre 2026 anche le azioni iniziali della
    fatica della giornata, nella coppa; le differite di prima non le hanno, e valgono zero.
    """
    cali = cali or {}
    iniziali = azioni_iniziali or {}
    squadre = (squadra_a, squadra_b)
    fotografie = [[fotografa(g) for g in squadra.giocatori] for squadra in squadre]
    return {"fotografie": fotografie, "nomi": [squadra_a.nome, squadra_b.nome], "basi": [[basi.get(g.id) for g in s.giocatori] for s in squadre],
            "cali": [[cali.get(g.id, 0.0) for g in s.giocatori] for s in squadre],
            "azioni_iniziali": [[iniziali.get(g.id, 0) for g in s.giocatori] for s in squadre], "formato": FORMATO_SQUADRE}


def gemello_da_differita(differita, seme, velocita=1.0):
    """
    L'incontro gemello di un incontro giocato e registrato, da svolgere in modalità completa nella
    finestra dal vivo o da leggere come cronaca: con le fotografie, lo stesso seme, le stesse basi
    d'infortunio, gli stessi cali e le stesse azioni iniziali dà gli stessi punti, lo stesso ritiro e
    gli stessi acciacchi.
    """
    if differita["formato"] == FORMATO_SQUADRE:
        squadre, basi, cali, iniziali = [], {}, {}, {}
        # Le differite delle gare a squadre registrate prima della fatica della giornata non hanno le azioni iniziali.
        azioni_iniziali = differita.get("azioni_iniziali") or [[0] * len(f) for f in differita["fotografie"]]
        for nome, fotografie, basi_squadra, cali_squadra, iniziali_squadra in zip(differita["nomi"], differita["fotografie"], differita["basi"],
                                                                                    differita["cali"], azioni_iniziali, strict=True):
            giocatori = tuple(da_fotografia(f) for f in fotografie)
            squadre.append(Squadra(nome, giocatori))
            for g, base, calo, n in zip(giocatori, basi_squadra, cali_squadra, iniziali_squadra, strict=True):
                if base is not None:
                    basi[g.id] = base
                if calo:
                    cali[g.id] = calo
                if n:
                    iniziali[g.id] = n
        return Incontro(squadre[0], squadre[1], SQUADRE, seme=seme, dettaglio=COMPLETO, basi_infortunio=basi or None, cali=cali or None,
                        azioni_iniziali=iniziali or None, velocita=velocita)
    fa, fb = (da_fotografia(f) for f in differita["fotografie"])
    basi = {g.id: base for g, base in zip((fa, fb), differita["basi"], strict=True) if base is not None}
    cali = {g.id: calo for g, calo in zip((fa, fb), differita["cali"], strict=True) if calo}
    iniziali = {g.id: n for g, n in zip((fa, fb), differita["azioni_iniziali"], strict=True) if n}
    return Incontro(fa, fb, formato_singolare(differita["formato"]), seme=seme, dettaglio=COMPLETO, basi_infortunio=basi or None, cali=cali or None,
                    azioni_iniziali=iniziali or None, velocita=velocita)


def gemello_in_differita(incontro, velocita=1.0):
    """Il gemello di un incontro di torneo dei tuoi tesserati, che porta la sua differita e il suo seme; ValueError se non ha la differita."""
    if not getattr(incontro, "differita", None):
        raise ValueError("Questo incontro non si può riascoltare: non è di un tuo tesserato, o l'edizione è già stata sostituita.")
    return gemello_da_differita(incontro.differita, incontro.seme, velocita)


gemello_squadre_in_differita = gemello_in_differita


def nomi_dell_incontro(incontro):
    """
    I nomi della cronaca di un incontro ancora da svolgere, come quello gemello in differita: si leggono
    dalle sue parti, perché i giocatori fotografati possono non esserci più nel mondo.
    """
    a, b = incontro.parti["A"], incontro.parti["B"]
    if isinstance(a, Squadra):
        return C.nomi_dei_giocatori([*a.giocatori, *b.giocatori], squadre=(a, b))
    return C.nomi_dei_giocatori([a, b])


def risultato_della_differita(differita, seme):
    """
    Il gemello di un incontro in differita giocato tutto in modalità completa, per leggerne la cronaca o
    salvarla: il risultato, con i momenti, e i nomi della cronaca.
    """
    gemello = gemello_da_differita(differita, seme)
    nomi = nomi_dell_incontro(gemello)
    return gemello.gioca(), nomi


def ascoltatore_della_differita(differita, tuoi):
    """
    Da quale parte si ascolta un incontro in differita: quella del tuo giocatore o della tua squadra,
    tuoi è l'insieme dei loro identificativi o dei nomi delle tue polisportive; A se nessuna delle due.
    """
    if differita.get("formato") == FORMATO_SQUADRE:
        nomi = differita.get("nomi") or ["", ""]
        if nomi[1] in tuoi and nomi[0] not in tuoi:
            return "B"
        return "A"
    fotografie = differita.get("fotografie") or [{}, {}]
    if fotografie[1].get("id") in tuoi and fotografie[0].get("id") not in tuoi:
        return "B"
    return "A"


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
        """
        None se i due possono giocare un'amichevole oggi, altrimenti il motivo: quelli dell'incontro, e
        dalla tappa 12 l'impegno del giorno, D32: chi oggi ha già giocato un'amichevole, il torneo o una
        sfida non gioca un'altra amichevole.
        """
        errore = self.problema_incontro(id_g1, id_g2)
        if errore:
            return errore
        oggi = self.mondo.datetime_corrente_simulazione
        gia = [g for g in (self.giocatori[id_g1], self.giocatori[id_g2]) if g.ha_un_impegno(oggi)]
        if not gia:
            return None
        if len(gia) == 1:
            g = gia[0]
            return f"Oggi {g.nome} {g.cognome} ha già giocato {self.mondo.descrivi_impegno(g)}: ognuno gioca al massimo un incontro per giorno simulato."
        chi = " e ".join(f"{g.nome} {g.cognome}" for g in gia)
        return f"Oggi {chi} hanno già giocato: ognuno gioca al massimo un incontro per giorno simulato."

    def disponibili(self, giocatori):
        """Fra i giocatori dati, quelli che possono giocare un'amichevole oggi, in ordine di numero."""
        oggi = self.mondo.datetime_corrente_simulazione
        return sorted((g for g in giocatori if g.puo_giocare_amichevole(oggi)), key=lambda g: g.id)

    def basi_e_cali(self, *giocatori):
        """
        Quello che il motore deve sapere degli infortuni di chi gioca, tappa 12: la base d'infortunio di
        ciascuno, senza il carico, e il calo dell'acciacco di oggi di chi ne ha uno, oppure None.
        """
        oggi = self.mondo.datetime_corrente_simulazione
        basi = {g.id: infortuni.probabilita_base(g) for g in giocatori}
        cali = {g.id: calo for g in giocatori if (calo := infortuni.calo_acciacco(g, oggi))}
        return basi, cali or None

    def _tuo(self, g):
        """Vero se il giocatore è un tesserato di una polisportiva dell'utente."""
        club = self.mondo.polisportive.get(g.appartenenza)
        return club is not None and not club.is_cpu_controlled

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
        è un'amichevole, vale la regola di un impegno al giorno, se si registra; con il torneo
        l'incontro si registra come partita di torneo. Dalla tappa 14, tolta l'interfaccia
        testuale che la usava per le amichevoli, la chiamano soltanto le prove.
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
        basi, cali = self.basi_e_cali(g1, g2)
        incontro = Incontro(g1, g2, formato, seme=seme, dettaglio=COMPLETO if completo else ESSENZIALE, taratura=self.taratura, basi_infortunio=basi, cali=cali)
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
            for riga in self.registra(risultato, esperienza.TORNEO if info_torneo else esperienza.AMICHEVOLE):
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
        anche perché uno dei due oggi ha già un impegno.
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
        basi, cali = self.basi_e_cali(g1, g2)
        incontro = Incontro(g1, g2, formato, seme=seme, dettaglio=COMPLETO, taratura=self.taratura, basi_infortunio=basi, cali=cali)
        gemello = None
        if con_gemello:
            gemello = Incontro(g1, g2, formato, seme=incontro.seme, dettaglio=COMPLETO, taratura=self.taratura, velocita=velocita, basi_infortunio=basi, cali=cali)
        risultato = incontro.gioca()
        risultato.registrazione = self.registra(risultato)
        return risultato, gemello

    def gioca_squadre(self, squadra_a, squadra_b, seme=None, dettaglio=ESSENZIALE):
        """Una gara a squadre giocata senza registrarla, come negli strumenti; la registrazione nella carriera è registra_squadre."""
        return Incontro(squadra_a, squadra_b, SQUADRE, seme=seme, dettaglio=dettaglio, taratura=self.taratura).gioca()

    # La registrazione nel mondo.

    @staticmethod
    def punti_della_partita(set_vinti_vinc, set_vinti_perd):
        """
        I punti allenamento della formula di un incontro a vincitore e perdente: la base, mezzo punto
        per set vinto, un punto a chi vince. Al meglio dei 3 chi vince prende 4 e chi perde 2 o 2,5; al
        meglio dei 5 chi vince 4,5 e chi perde da 2 a 3. Dalla tappa 12 si moltiplicano per il fattore
        della fonte e per l'importanza, in registra.
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

    @staticmethod
    def punti_di_registrazione(set_vinc, set_perd, debole, g_vinc, g_perd, tipo=esperienza.AMICHEVOLE, importanza=1.0):
        """
        I punti allenamento che la registrazione dà a vincitore e perdente, D32 e punto 10.2: la formula
        con il premio al più debole, per il fattore della fonte e per l'importanza.
        """
        pa_vinc, pa_perd = MotorePartita.punti_della_partita(set_vinc, set_perd)
        if debole is g_vinc:
            pa_vinc += PA_BONUS_PIU_DEBOLE
        elif debole is g_perd:
            pa_perd += PA_BONUS_PIU_DEBOLE
        fattore = PA_FATTORE[tipo] * importanza
        return pa_vinc * fattore, pa_perd * fattore

    def segna_impegno(self, *giocatori):
        """L'impegno del giorno, D32: chi ha giocato oggi un incontro non ne gioca un altro, né amichevole né sfida."""
        oggi = self.mondo.datetime_corrente_simulazione
        for g in giocatori:
            g.ultimo_impegno = oggi

    def registra(self, risultato, tipo=esperienza.AMICHEVOLE, importanza=1.0, diario=True, solo_tuoi=False):
        """
        Porta il risultato di un singolare nel mondo: partite e set vinti e persi, goal fatti e subiti,
        punti allenamento con il premio al più debole, per il fattore della fonte e per l'importanza,
        esperienza e costanza recente, l'impegno del giorno, gli infortuni e gli acciacchi con la loro
        sede, e con diario le voci nei diari; con solo_tuoi, soltanto nei diari dei tuoi tesserati,
        perché gli altri hanno la voce aggregata dell'anno, punto 5.11. tipo è amichevole, torneo o
        sfida, come in esperienza.py. Restituisce le frasi da mostrare. La gara a squadre si registra
        con registra_squadre.
        """
        if risultato.formato.tipo != "singolare":
            return []
        if risultato.esito == TAVOLINO:
            return self._registra_tavolino(risultato, tipo, diario)
        annota = self._chi_annota(diario, solo_tuoi)
        id_a, id_b = risultato.parti
        vince_a = risultato.vincitore == "A"
        id_vinc, id_perd = (id_a, id_b) if vince_a else (id_b, id_a)
        g_vinc, g_perd = self.giocatori[id_vinc], self.giocatori[id_perd]
        stats_vinc, stats_perd = risultato.statistiche[id_vinc], risultato.statistiche[id_perd]
        # Col ritiro contano soltanto i set giocati: quelli aggiunti 11 a 0 servono alla classifica del torneo.
        giocati = risultato.set[:risultato.set_giocati]
        sa = sum(1 for a, b in giocati if a > b)
        sb = len(giocati) - sa
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
        pa_vinc, pa_perd = self.punti_di_registrazione(set_vinc, set_perd, self.piu_debole(g_vinc, g_perd), g_vinc, g_perd, tipo, importanza)
        for g, punti in ((g_vinc, pa_vinc), (g_perd, pa_perd)):
            g.punti_allenamento += punti
            esperienza.da_partita(g, tipo, importanza)
            g.costanza += (1.0 - DECADIMENTO_COSTANZA) * COSTANZA_PER_PARTITA
        self.segna_impegno(g_vinc, g_perd)
        self._annota_risultato(g_vinc, g_perd, risultato, vince_a, set_vinc, set_perd, tipo, annota)
        frasi = [f"Punti allenamento: {_punti(pa_vinc)} a {g_vinc.nome} {g_vinc.cognome}, {_punti(pa_perd)} a {g_perd.nome} {g_perd.cognome}."]
        frasi.extend(self.registra_infortuni(risultato, diario, solo_tuoi))
        return frasi

    def _chi_annota(self, diario, solo_tuoi):
        """Chi riceve le voci del diario di un incontro: tutti, nessuno, o soltanto i tuoi tesserati."""
        if not diario:
            return lambda _g: False
        if solo_tuoi:
            return self._tuo
        return lambda _g: True

    def registra_infortuni(self, risultato, diario=True, solo_tuoi=False):
        """
        Porta nel mondo gli infortuni e gli acciacchi che il motore ha estratto, tappa 12: la durata e
        il calo da un generatore nato dal seme dell'incontro, così l'incontro rigiocato dà gli stessi.
        Gli infortuni vanno nel diario di chi riceve le voci, gli acciacchi soltanto in quello dei tuoi
        tesserati; senza diario, nella registrazione leggera, in nessuno. Restituisce le frasi da mostrare.
        Dalla decisione 4 di Gabriele del 14 ottobre 2026 il generatore nasce soltanto se c'è un infortunio o
        un acciacco: è suo, e senza estrazioni non serve; prima nasceva per ogni incontro registrato.
        """
        if not risultato.infortuni and not risultato.acciacchi:
            return []
        annota = self._chi_annota(diario, solo_tuoi)
        frasi = []
        caso = random.Random(f"durata-{risultato.seme}")
        for gid, _set_n, sede in risultato.infortuni:
            g = self.giocatori[gid]
            frase = infortuni.colpisci(self.mondo, g, sede, caso, annota=annota(g))
            if frase:
                frasi.append(frase)
        for gid, sede in risultato.acciacchi:
            g = self.giocatori[gid]
            frase = infortuni.acciacca(self.mondo, g, sede, caso, annota=annota(g) and self._tuo(g))
            if frase:
                frasi.append(frase)
        return frasi

    # La gara a squadre nella carriera, punto 8.7 del progetto della tappa 12.

    def registra_squadre(self, risultato, tipo=esperienza.SFIDA, importanza=1.0, diario=True, solo_tuoi=False, gara=None, aggrega=None):
        """
        Porta una gara a squadre nel mondo, D25 e D32. Ai tre titolari di ciascuna squadra la gara vinta
        o persa, i punti allenamento della formula, la base più mezzo punto per il set vinto più il punto
        della vittoria, per il fattore della fonte e per l'importanza, senza il premio al più debole;
        l'esperienza, la costanza, l'impegno del giorno, e gli infortuni e gli acciacchi con le loro
        azioni. Alle riserve, risposta 15, metà dell'esperienza della sfida e l'impegno del giorno, e
        niente altro: né punti, né gare, né costanza. gara è il nome della gara nei diari, come «la
        sfida»; aggrega dice quali campi della voce aggregata dell'anno salgono per chi non riceve la
        voce, «sfide» o «incontri», oppure None. Il tavolino non dà niente a nessuno: soltanto l'impegno
        a chi c'era e una voce ai tuoi. Restituisce le frasi da mostrare.
        """
        if risultato.formato.tipo != "squadre":
            return []
        gara = gara or self._nome_del_tipo(tipo)
        if risultato.esito == TAVOLINO:
            return self._registra_tavolino_squadre(risultato, gara, diario)
        annota = self._chi_annota(diario, solo_tuoi)
        oggi = self.mondo.datetime_corrente_simulazione
        punti_a, punti_b = risultato.set[0]
        frasi = []
        pa = {}
        for lato, ids in zip("AB", risultato.parti, strict=True):
            vinto = risultato.vincitore == lato
            mio, suo = (punti_a, punti_b) if lato == "A" else (punti_b, punti_a)
            altra = risultato.nomi_squadre[1 if lato == "A" else 0]
            pa_vinc, pa_perd = self.punti_della_partita(1, 0)
            punti = (pa_vinc if vinto else pa_perd) * PA_FATTORE[tipo] * importanza
            pa[lato] = punti
            titolari, riserve = ids[:GIOCATORI_AL_TAVOLO], ids[GIOCATORI_AL_TAVOLO:]
            compagni = {gid: f"{self.giocatori[gid].nome} {self.giocatori[gid].cognome}" for gid in titolari}
            for gid in titolari:
                g = self.giocatori[gid]
                if vinto:
                    g.gare_squadre_vinte += 1
                else:
                    g.gare_squadre_perse += 1
                g.punti_allenamento += punti
                esperienza.da_partita(g, tipo, importanza)
                g.costanza += (1.0 - DECADIMENTO_COSTANZA) * COSTANZA_PER_PARTITA
                altri = " e ".join(nome for altro, nome in compagni.items() if altro != gid)
                testo = f"{'Vince' if vinto else 'Perde'} {gara} contro {altra}, {mio} a {suo}, al tavolo con {altri}."
                self._voce_di_squadra(g, testo, annota, aggrega, vinto, oggi)
            for gid in riserve:
                g = self.giocatori[gid]
                esperienza.da_riserva(g, importanza)
                testo = f"Riserva per {gara} contro {altra}: la squadra {'vince' if vinto else 'perde'} {mio} a {suo}."
                if annota(g) and self._tuo(g):
                    self.mondo.annota(g, testo)
            self.segna_impegno(*(self.giocatori[gid] for gid in ids))
        nome_a, nome_b = risultato.nomi_squadre
        frasi.append(f"Punti allenamento a ogni titolare: {_punti(pa['A'])} a {nome_a}, {_punti(pa['B'])} a {nome_b}.")
        frasi.extend(self.registra_infortuni(risultato, diario, solo_tuoi))
        return frasi

    def _voce_di_squadra(self, g, testo, annota, aggrega, vinto, oggi):
        """La voce di un titolare: la sua se la riceve, altrimenti, se si aggrega, la voce aggregata dell'anno."""
        if annota(g):
            self.mondo.annota(g, testo)
        elif aggrega == "sfide":
            annota_aggregata(g.diario, oggi, CAMPI_AGGREGATA_GIOCATORE, sfide=1, sfide_vinte=int(vinto))
        elif aggrega == "incontri":
            annota_aggregata(g.diario, oggi, CAMPI_AGGREGATA_GIOCATORE, incontri=1, vinti=int(vinto))

    def _registra_tavolino_squadre(self, risultato, gara, diario):
        """
        La gara a squadre vinta a tavolino, 31 a 0: chi non ha schierato una squadra valida perde, e
        nessuno prende punti, esperienza o costanza; la squadra presente segna l'impegno del giorno, e i
        tuoi hanno una voce. Restituisce le frasi da mostrare.
        """
        vince = risultato.vincitore
        presenti, assenti = (risultato.parti[0], risultato.parti[1]) if vince == "A" else (risultato.parti[1], risultato.parti[0])
        nome_vinc, nome_perd = risultato.nomi_squadre if vince == "A" else tuple(reversed(risultato.nomi_squadre))
        giocatori_presenti = [self.giocatori[gid] for gid in presenti if gid in self.giocatori]
        self.segna_impegno(*giocatori_presenti)
        if diario:
            for g in giocatori_presenti:
                if self._tuo(g):
                    self.mondo.annota(g, f"Vince a tavolino {gara} contro {nome_perd}, che non ha schierato una squadra valida.")
            for gid in assenti:
                g = self.giocatori.get(gid)
                if g is not None and self._tuo(g):
                    self.mondo.annota(g, f"Perde a tavolino {gara} contro {nome_vinc}: la squadra non aveva tre giocatori validi.")
        return [f"{nome_perd} non schiera una squadra valida: {nome_vinc} vince a tavolino."]

    @staticmethod
    def _nome_del_tipo(tipo_incontro):
        return {esperienza.TORNEO: "la partita del torneo", esperienza.SFIDA: "la sfida"}.get(tipo_incontro, "l'amichevole")

    def _annota_risultato(self, g_vinc, g_perd, risultato, vince_a, set_vinc, set_perd, tipo_incontro, annota=None):
        """
        Il risultato nei diari dei due giocatori, ciascuno con i set dal suo punto di vista. Col ritiro,
        dalla tappa 12, i set giocati davvero e chi si è ritirato. annota dice chi riceve la voce.
        """
        annota = annota or (lambda _g: True)
        # Dalla decisione 4 di Gabriele del 14 ottobre 2026: se nessuno dei due riceve la voce, come nei
        # tornei del computer, le frasi non si scrivono nemmeno.
        if not annota(g_vinc) and not annota(g_perd):
            return

        def scrivi(g, testo):
            if annota(g):
                self.mondo.annota(g, testo)

        tipo = self._nome_del_tipo(tipo_incontro)
        giocati = risultato.set[:risultato.set_giocati]
        dal_vincitore = [(a, b) if vince_a else (b, a) for a, b in giocati]
        set_vincitore = ", ".join(f"{a} a {b}" for a, b in dal_vincitore)
        set_perdente = ", ".join(f"{b} a {a}" for a, b in dal_vincitore)
        nome_perd, nome_vinc = f"{g_perd.nome} {g_perd.cognome}", f"{g_vinc.nome} {g_vinc.cognome}"
        if risultato.esito != RITIRO:
            scrivi(g_vinc, f"Vince {tipo} contro {nome_perd}, {set_vinc} set a {set_perd}: {set_vincitore}.")
            scrivi(g_perd, f"Perde {tipo} contro {nome_vinc}, {set_perd} set a {set_vinc}: {set_perdente}.")
            return
        dopo = f"dopo {len(giocati)} set"
        if g_vinc.id in risultato.ritirato:
            scrivi(g_vinc, f"Vince {tipo} contro {nome_perd}: si ritirano tutti e due {dopo}, e vince chi ha vinto più set: {set_vincitore}.")
        else:
            scrivi(g_vinc, f"Vince {tipo} contro {nome_perd}, che si ritira {dopo}: {set_vincitore}.")
        scrivi(g_perd, f"Perde {tipo} contro {nome_vinc}: si ritira {dopo}, {set_perdente}.")

    def _registra_tavolino(self, risultato, tipo=esperienza.AMICHEVOLE, diario=True):
        """
        La sconfitta a tavolino, D32 e risposta 8 di Gabriele: niente punti allenamento, niente
        esperienza, niente costanza, e la partita non entra nella carriera di nessuno dei due; soltanto
        una voce nel diario dei tuoi tesserati, e l'impegno del giorno per chi si è presentato.
        Restituisce le frasi da mostrare.
        """
        id_a, id_b = risultato.parti
        vince_a = risultato.vincitore == "A"
        g_vinc, g_perd = (self.giocatori[id_a], self.giocatori[id_b]) if vince_a else (self.giocatori[id_b], self.giocatori[id_a])
        self.segna_impegno(g_vinc)
        nome = self._nome_del_tipo(tipo)
        assente = accorda(g_perd.sesso, "presentato")
        perche = f"è {accorda(g_perd.sesso, 'infortunato')}" if g_perd.infortunato and not g_perd.puo_giocare else f"non si è {assente}"
        if diario and self._tuo(g_vinc):
            self.mondo.annota(g_vinc, f"Vince a tavolino {nome} contro {g_perd.nome} {g_perd.cognome}, che non si è {assente}.")
        if diario and self._tuo(g_perd):
            self.mondo.annota(g_perd, f"Perde a tavolino {nome} contro {g_vinc.nome} {g_vinc.cognome}: {perche}.")
        return [f"{g_perd.nome} {g_perd.cognome} non si presenta: {g_vinc.nome} {g_vinc.cognome} vince a tavolino."]

    # La cronaca su file.

    def salva_cronaca(self, risultato, livello=C.NORMALE, istante=None, data_simulata=None, nomi=None):
        """
        Scrive la cronaca dell'incontro in un file della cartella cronache e ne restituisce il
        percorso. istante e data_simulata sono il momento reale e il giorno simulato dell'incontro,
        per l'intestazione e il nome del file: chi salva più tardi, come la finestra, li ha fissati
        quando si è giocato; senza, valgono quelli di adesso, che per chi salva subito sono gli stessi.
        nomi, dalla tappa 12, sono quelli di un incontro in differita, i cui giocatori fotografati
        possono non esserci più nel mondo; senza, si leggono dal mondo.
        """
        if risultato.momenti is None:
            raise ValueError("La cronaca c'è soltanto per gli incontri giocati in modalità completa.")
        nomi = nomi or self.nomi(risultato)
        istante = istante or adesso()
        data_simulata = data_simulata or self.mondo.datetime_corrente_simulazione
        righe = C.intestazione(risultato, nomi, istante, data_simulata)
        righe += C.componi(risultato.momenti, nomi, livello)
        righe += C.riepilogo(risultato, nomi)
        return C.salva(righe, C.nome_file(nomi, istante))
