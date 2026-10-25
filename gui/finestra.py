"""
La finestra principale di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 5 del piano, sul modello di Terminal Beast e di Tornello: due
aree di testo, la vista principale grande e in sola lettura, dove ogni comando mostra il suo
risultato al posto del precedente, e la barra di stato di quattro righe a codici; nessun albero
dei comandi, ma i menu, ciascuna voce con il suo tasto rapido. I menu nascono da una tabella sola,
da cui nasce anche la guida ai comandi, così le due cose non possono andare d'accordo a metà.
Dalla tappa 6 il mondo avanza anche a finestra aperta: ogni minuto un timer guarda se è maturato
un giorno simulato, lo fa elaborare, salva il mondo e lo annuncia nella barra di stato, senza
toccare la vista principale, dove chi legge non deve vedersi spostare il testo. Mentre è aperto
un dialogo aspetta che si chiuda.
Dalla tappa 7 il menu Polisportive ha le operazioni: fondazione, cambio della polisportiva
attiva, mercato, svincolo, password e chiusura. Ogni operazione si salva subito, così l'esito di
un'offerta resta quello che è stato.
Dalla tappa 8 ci sono il bilancio, gli arretrati da pagare e le vendite, e quando il mondo avanza
la barra di stato dice prima di tutto se i tuoi tesserati sono rimasti senza stipendio.
Dal 2026-10-07, con la decisione D24, ogni evento della finestra ha il suo effetto sonoro: i
comandi, l'apertura e l'esito dei dialoghi, i salvataggi, l'avvio e l'uscita. Quando il mondo
avanza suona un solo suono, quello della notizia più importante, scelto insieme al testo della
barra di stato perché non dicano cose diverse: è l'invito a premere F7. Se un salvataggio
automatico non riesce, dopo il suono dell'operazione si sente quello del salvataggio fallito, e la
vista dice il perché. Nel menu Impostazioni c'è il volume degli effetti.
Dal 2026-10-08, con la tappa 9, c'è il menu Partite, con le scelte di Gabriele: l'amichevole fra un
tuo tesserato e un giocatore qualunque, ciascuno al massimo una al giorno, si gioca e si registra
subito, il mondo si salva, e la cronaca si salva nel suo file al livello scelto. Con la decisione
D29, tappa 10, i modi di seguirla sono due: Vai alla fine mostra nella vista il risultato, i punti
allenamento e sotto la cronaca intera; Assisti apre la finestra dal vivo di gui/dal_vivo.py, e
quando se ne esce con Vai alla fine o dal risultato la vista mostra lo stesso testo. Il punto per
punto con F8 e Ctrl+F8 non c'è più. L'esito si sente solo quando si mostra, perché la partita dal
vivo non lo sveli prima; e con la decisione D30 chi esce con Esc prima della fine non lo vede
affatto: la vista dice che l'incontro è registrato e dove leggerne il risultato. Nel menu Impostazioni c'è la velocità di
gioco, e il dialogo degli effetti sonori ha anche il volume della partita. Le parti delle tappe 9 e
10 sono di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Dal 2026-10-09, con la tappa 11 e la decisione D31, il menu Polisportive ha la sala allenamento,
dove si spendono i punti allenamento dei tesserati e se ne scelgono programma e intensità, e i
contratti, dove si propongono i rinnovi; lo svincolo dice la buonuscita, e alla chiusura di ciascun
dialogo la vista mostra che cosa è cambiato e il mondo si salva. Anche queste parti sono di
Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Dal 2026-10-14, con la tappa 12 e la decisione D32, il mondo gioca. Il menu Tornei ha il calendario con
le iscrizioni a mano, le iscrizioni dei tuoi atleti, il pannello dei tornei in corso, dove gli incontri
dei tuoi si ascoltano in differita o si leggono, l'albo d'oro, la classifica mondiale, gli editor dei
modelli e delle formule e il ripristino del calendario predefinito; il menu Partite ha le sfide fra
polisportive, da lanciare, in arrivo e nello storico. Salva la cronaca salva l'ultimo incontro mostrato
o ascoltato, amichevole, di torneo o di sfida. All'avvio un calendario che non si legge si dice in
testa alla vista; quando il mondo avanza, la barra dice le notizie dei tornei e delle sfide, con un
suono solo, quello della più importante. Le parti della tappa 12 sono di Gabriele Battaglia (IZ4APU) &
ClaudIA (Claude Opus 5.5, modalità auto).
Dal 2026-10-21, con la tappa 13 e la decisione D33, il menu Polisportive ha lo staff della polisportiva
attiva e il mercato degli allenatori, che alla chiusura riepilogano le operazioni nella vista; all'avvio
col mondo appena aggiornato, la notizia dello staff ha il suo suono. Le parti della tappa 13 sono di
Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Dal 2026-10-23, con la tappa 14 e la decisione D34, il menu Aiuto ha il manuale, manuale.html, che si
apre nel browser con Maiusc+F1. La finestra conduce la sua parte dell'aggiornamento automatico: la
proposta con le note della release, gli esiti in un messaggio che aspetta l'OK, l'avanzamento dello
scaricamento nella barra di stato e la chiusura per farsi sostituire, che salva il mondo e non aspetta
il riepilogo di fine sessione. Torna in primo piano quando si prova ad aprire MESS una seconda volta;
all'apertura dopo un crash la vista lo dice in testa, col suono staccato come la notizia dello staff; e
il messaggio di un errore imprevisto rimanda al registro degli errori, accanto al programma. Con la
issue 4 il menu Aiuto ha anche Entra al PUB e Chiedi aiuto al PUB, il gruppo di supporto: preparano
la mail con le funzioni comuni di GBUtils, nella finestra di GBwx che senza posta guida passo per
passo, e quella d'aiuto chiede di allegare i file del registro che ci sono. Le parti della tappa 14
sono di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Dal 2026-10-23, richiesta di Gabriele, il menu Impostazioni ha Cartella del mondo: la finestra di
Windows sceglie dove stanno il mondo, le impostazioni, i tornei e le cronache, per portarli fra le
macchine con una penna o con un cloud. Prima di tutto il mondo si salva. Se la cartella scelta non ha un
mondo, i dati ci si spostano e MESS continua; se ne ha uno, una domanda dice quando è stato salvato
l'uno e l'altro e quale è il più recente, e chiede quale tenere: con Usa il mondo della cartella i dati
di adesso restano dove sono, e MESS si chiude senza salvare di nuovo e si riapre sul mondo della
cartella; con Porta il mio mondo i dati della cartella vanno in una sua riserva, e i tuoi ci si
spostano. All'apertura dopo lo spostamento dei dati che stavano accanto al programma, la vista lo
dice in testa, col suo suono. I registri stanno accanto al programma, non nella cartella del mondo.
Anche queste parti sono di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Dalla revisione dello stesso giorno non si accetta una cartella dentro i dati che le versioni di prova
tenevano accanto al programma; il mondo della cartella che non si legge non si offre di usarlo; e se la
cartella del mondo aperto non si raggiunge più, per esempio una penna staccata, il mondo e le
impostazioni si salvano nella cartella scelta invece di andare persi. Con l'ultima verifica il file della
cartella rovinato a MESS aperto e quello che non si scrive hanno ciascuno il suo suono, e quando MESS non
riesce a riaprirsi si chiude col suono dell'uscita di sempre, non con quello che promette la riapertura.
Con la verifica seguente hanno ciascuno il suo suono anche il calendario predefinito che non si riesce a
rimettere, il mondo salvato nella cartella scelta quando quella di prima non si raggiunge più, e all'avvio
i dati di accanto al programma messi in una riserva della cartella del mondo, che la notizia dice col suo tipo.
Con la issue 6 di Gabriele, dal collaudo di gioco dello stesso giorno, quando la polisportiva attiva ha
finito le mosse di mercato la voce Mercato non è disponibile, e NVDA la legge così; si rimette in pari
all'apertura della finestra e dei menu, alla fine di ogni comando e a ogni avanzamento del mondo.
Windows non manda il comando di una voce disattivata, e Ctrl+K resterebbe muto: lo prende prima il
gancio dei tasti della finestra, e la vista dice che per oggi le mosse sono finite, col loro suono. È
di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Dal collaudo di gioco, il 24 ottobre 2026, il calendario predefinito che non si rimette perché il
ripristino si è fermato a metà dice in quale cartella sono i modelli e le formule già messi da parte; e
nell'amichevole Alt+V a incontro finito mostra il risultato senza i guizzi di un salto che non c'è, perché
la finestra dal vivo lo restituisce come il risultato. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude
Opus 5.5, UltraCode). Con le verifiche dello stesso collaudo quel messaggio parla dei file di prima, che
possono essere soltanto dei modelli, e la voce Mercato si rimette in pari anche quando un errore ferma a
metà l'avanzamento del mondo. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Con la richiesta di Gabriele dello stesso collaudo il menu Partite ha, subito dopo Amichevole, Gioca tutte le amichevoli
di, col nome della polisportiva attiva, e Gioca tutte le amichevoli di tutte le tue polisportive: ogni tesserato che oggi
può giocare ne gioca una contro un avversario scelto a caso, con la classe entro 15 livelli dalla sua e di un'altra
polisportiva, senza la finestra dal vivo; il mondo si salva, e la vista riassume ogni incontro in una riga, coi totali in
fondo. Ogni evento nuovo ha il suo suono. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Con la verifica, quando nessuna delle tue polisportive ha tesserati, la seconda voce lo dice come la prima, col suono della
rosa vuota, e non rimanda al giorno simulato dopo. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Lo stesso giorno, con la finestra Mercato e ricerca della issue 8 e della decisione D36, Mercato, Ctrl+K, Mercato degli
allenatori, Ctrl+Maiusc+G, Cerca giocatori, Ctrl+F, e Amichevole, Ctrl+O, aprono la stessa finestra, ciascuno col suo
ultimo preset, e lei suona la sua apertura. A mosse finite anche la voce del mercato degli allenatori non è disponibile,
e Ctrl+Maiusc+G lo dice come Ctrl+K; senza polisportiva attiva le due porte del mercato si aprono lo stesso, per cercare.
L'amichevole sceglie prima l'avversario nella finestra, poi il tuo giocatore e le opzioni, e la partita la gioca la
finestra principale, col riepilogo della finestra davanti; Ctrl+O tiene i suoi controlli prima di aprirla. Alla
chiusura, con degli esiti, compresi i preset, la vista li riassume e il mondo si salva; senza, la vista resta com'era,
con un suono suo. Lo staff riassume anche quello che si è fatto nella finestra aperta da Assumi. Spariscono la ricerca
che stampava nella vista e Risultati della ricerca, Ctrl+R. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5,
UltraCode).
Dal 2026-10-25, con la decisione D38, la barra di stato su misura: le righe e i dati li sceglie chi gioca, con la voce
Barra di stato del menu Impostazioni, da una a sedici righe, lunghe quanto serve, e la barra è alta quanto le sue righe.
Si rinfresca ogni 20 secondi, quanto dura un minuto simulato, anche col cursore sopra, che resta sulla stessa riga e nella
stessa colonna. I dati vengono da barra.py: quelli che cambiano col tempo si ricalcolano a ogni rinfresco, gli altri
vengono da un'istantanea che si svuota dopo ogni comando, dopo ogni avanzamento e quando si salva una barra nuova; F7
sulla barra la rifà tutta. A metà di un comando la barra non si riscrive: lo fa la fine del comando, una volta sola. È di
Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Lo stesso giorno, richiesta di Gabriele perché le sigle sono tante da ricordare: quando ti muovi col cursore nella barra e
entri in un dato che ha la sigla, la sintesi e il display braille ne dicono il nome, con la voce degli annunci della
cronaca, e lo ridicono se ne esci e ci rientri. Lo dice soltanto il cursore che si muove, coi tasti o col clic: né
l'arrivo sulla barra né la riscrittura sotto il cursore. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5,
UltraCode).
Lo stesso giorno, dal collaudo di Gabriele: il nome si dice entrando nel dato con le frecce orizzontali, Inizio e Fine, col
clic o col cursor routing del display braille, che non manda né tasti né clic e si vede perché la finestra, mentre la barra
ha il fuoco, guarda il cursore ogni 150 millesimi; con le frecce verticali, Pagina su e giù, Ctrl+Inizio e Ctrl+Fine no,
perché si voleva cambiare riga per leggerla. Se il cursore resta fermo 10 secondi in un dato di cui ha detto il nome,
parte anche la spiegazione lunga, una volta per ingresso. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5,
UltraCode).
"""

import contextlib
import os
import time

import wx
from GBUtils import Donazione
from GBwx import dentro_area_utile

import aggiornamento
import archivio
import barra as modulo_barra
import cartella_del_mondo
import impostazioni as modulo_impostazioni
import istanza
import modelli_torneo
import percorsi
import registro
import sfide
import suoni
import testi
from gui import aspetto
from gui.barra_di_stato import BarraDiStato
from gui.dal_vivo import ALLA_FINE, CON_ESC, FinestraDalVivo, annunci_condivisi
from gui.dialoghi import (
    ASSISTI,
    PORTA_IL_MIO_MONDO,
    USA_IL_MONDO_DELLA_CARTELLA,
    Aggiornamento,
    AnnunciDellaCronaca,
    Aspetto,
    Caffe,
    CambiaPolisportiva,
    ChiediPassword,
    Conservazione,
    Contratti,
    EffettiSonori,
    Lettura,
    MondoGiaPresente,
    NuovaPolisportiva,
    PagaArretrati,
    PasswordPolisportiva,
    SalaAllenamento,
    SceltaGiocatore,
    Staff,
    VelocitaDiGioco,
    Vendite,
    scegli_cartella,
)
from gui.editor_tornei import EditorFormule, EditorModelli
from gui.mercato_e_ricerca import MercatoERicerca
from gui.sfide import LanciaSfida, SfideInArrivo, StoricoSfide
from gui.tornei import AlboDOro, CalendarioTornei, PannelloTornei, UltimoIncontro, tuoi_del_mondo
from partita import MotorePartita
from utilita import adesso, adesso_utc

TITOLO = "MESS, Manageriale e Simulatore Showdown"
# Il silenzio fra il suono dell'avvio e quello della notizia dello staff: con la pausa breve della coda
# il fischietto si confondeva con l'avvio, collaudo di Gabriele del 23 ottobre 2026. Dalla tappa 14
# vale anche per la notizia del crash della volta prima.
PAUSA_NOTIZIA_DELLO_STAFF = 1.0
# La barra di stato su misura, D38, col collaudo di Gabriele del 25 ottobre 2026. I tasti che cambiano riga: entrando così in
# un dato il suo nome non si dice, perché si voleva leggere la riga; Inizio e Fine cambiano riga soltanto con Ctrl. I
# modificatori da soli non spostano il cursore. Ogni quanto si guarda il cursore della barra che ha il fuoco, per il cursor
# routing del display braille, e dopo quanto parte la spiegazione lunga del dato, in millesimi.
TASTI_DI_RIGA = frozenset({wx.WXK_UP, wx.WXK_DOWN, wx.WXK_NUMPAD_UP, wx.WXK_NUMPAD_DOWN, wx.WXK_PAGEUP, wx.WXK_PAGEDOWN,
                           wx.WXK_NUMPAD_PAGEUP, wx.WXK_NUMPAD_PAGEDOWN})
TASTI_DI_INIZIO_E_FINE = frozenset({wx.WXK_HOME, wx.WXK_END, wx.WXK_NUMPAD_HOME, wx.WXK_NUMPAD_END})
MODIFICATORI = frozenset({wx.WXK_SHIFT, wx.WXK_CONTROL, wx.WXK_ALT, wx.WXK_WINDOWS_LEFT, wx.WXK_WINDOWS_RIGHT})
CONTROLLO_DEL_CURSORE = 150
ATTESA_DELLA_SPIEGAZIONE_LUNGA = 10_000
# Ogni quanti millesimi la chiusura per l'aggiornamento riprova, finché un messaggio resta aperto.
RIPROVA_DELLA_CHIUSURA = 200
# Dopo quanti secondi la chiusura per l'aggiornamento smette di riprovare: lo script di sostituzione
# aspetta la chiusura di MESS al massimo 30 secondi, e oltre si chiuderebbe per niente. Dalla terza
# revisione della tappa 14 sono 20, non 25: i 30 secondi contano dall'avvio dello script, e la
# chiusura che comincia allo scadere del limite comprende ancora il salvataggio del mondo, lento
# coi mondi grandi, e il suono d'uscita, fino a ATTESA_USCITA.
LIMITE_DELLA_CHIUSURA = 20
NON_INSTALLATO = ("L'aggiornamento non si è installato: MESS doveva chiudersi entro 30 secondi, ma un messaggio è rimasto aperto. "
                  "Continui con questa versione, e l'aggiornamento te lo ripropongo al prossimo avvio.")
# Il suono degli esiti dell'aggiornamento che non sono quello buono, lo scaricamento finito.
SUONI_DEGLI_ESITI = {aggiornamento.NON_RIUSCITO: "aggiornamento_non_riuscito", aggiornamento.NON_PRONTO: "aggiornamento_non_pronto"}
# I modificatori di un tasto rapido dei menu e quelli di un evento dei tasti, per riconoscere il tasto rapido nel gancio della finestra, issue 6.
MODIFICATORI_DEI_TASTI_RAPIDI = ((wx.ACCEL_ALT, wx.MOD_ALT), (wx.ACCEL_CTRL, wx.MOD_CONTROL), (wx.ACCEL_SHIFT, wx.MOD_SHIFT))


def _modificatori(flags):
    """I modificatori, come li dà wx.KeyEvent.GetModifiers, del tasto rapido coi flags di un wx.AcceleratorEntry."""
    modificatori = wx.MOD_NONE
    for rapido, tasto in MODIFICATORI_DEI_TASTI_RAPIDI:
        if flags & rapido:
            modificatori |= tasto
    return modificatori


def _parti_degli_esiti(esiti, allenatori=True):
    """Gli esiti della finestra Mercato e ricerca come li vogliono il riepilogo e il fatto della barra; per lo staff senza gli allenatori, che sono suoi."""
    return {"giocatori": esiti.giocatori, "allenatori": esiti.allenatori if allenatori else (), "sfide_lanciate": esiti.sfide, "preset": esiti.preset}


def _davanti(prima, testo):
    """Il testo con davanti prima, il riepilogo della finestra da cui arriva l'amichevole, se c'è."""
    return f"{prima}\n{testo}" if prima else testo


class FinestraPrincipale(wx.Frame):
    def __init__(self, mondo, origine, messaggi, rapporto, ultimo_prima, avvisi_all_avvio=False, crash_precedente=None, cartella_spostata=None):
        super().__init__(None, title=TITOLO)
        self.mondo = mondo
        self.origine = origine
        self.avvisi_all_avvio = avvisi_all_avvio
        # Dalla tappa 14: il resoconto del crash della volta prima, se c'è stato; chiusa diventa vera
        # quando la finestra comincia a chiudersi, e il filo dell'aggiornamento non le chiede più niente.
        self.crash_precedente = crash_precedente
        self.chiusa = False
        self._per_aggiornare = False
        # Dal 23 ottobre 2026: la riga dei dati spostati da accanto al programma alla cartella del mondo, se è
        # successo a questo avvio, testi.DatiInRiserva se sono andati in una sua riserva; e il cambio di
        # cartella che chiude MESS per riaprirlo sul mondo della cartella,
        # con la riapertura che non è partita, e allora MESS si chiude e basta.
        self.cartella_spostata = cartella_spostata
        self._per_cambiare_cartella = False
        self._riapertura_mancata = False
        # Da quando, in secondi di time.monotonic, la finestra prova a chiudersi per l'aggiornamento.
        self._chiusura_dal = None
        self.rapporto = rapporto
        self.rapporto_sessione = rapporto
        self._modali = 0
        self.impostazioni = modulo_impostazioni.carica()
        suoni.imposta_volume(self.impostazioni["volume_effetti"])
        self.inizio = adesso()
        self.comandi = 0
        self.ultimo_evento = "mondo pronto"
        # La barra su misura, D38: l'istantanea dei dati che non cambiano col tempo, l'esito dell'ultimo salvataggio, e i
        # comandi in corso, durante i quali la barra non si riscrive.
        self._istantanea = {}
        self._salvataggio_riuscito = True
        self._comandi_in_corso = 0
        # Le righe della barra coi loro dati, e la chiave del dato su cui stava il cursore, per dirne il nome quando ci entra.
        self._dati_della_barra = []
        self._dato_sotto_il_cursore = None
        # Dal collaudo dello stesso giorno: la posizione del cursore già vista, il tasto che lo sta muovendo, il dato di cui si
        # è detto il nome e che aspetta la spiegazione lunga, e le due attese, quella del controllo del cursore e quella lunga.
        self._posizione_nota = None
        self._tasto_della_mossa = None
        self._dato_spiegato = None
        self._controllo_attivo = False
        self._attesa_lunga = None
        # Dalla tappa 12, punto 12.10: un modello o una formula dei tornei che non si leggono si dicono in
        # testa alla vista all'avvio, col loro suono, e nella barra una volta per sessione e a ogni cambio.
        self.problemi_all_avvio = self._problemi_del_calendario()
        self._problemi_detti = tuple(self.problemi_all_avvio) or None
        # Il mondo nato adesso avanza subito di un giorno, che non va annunciato: è appena nato.
        self.avanzamento_all_avvio = None
        if origine != archivio.NATO:
            evento, testo = self._evento_avanzamento(rapporto, True)
            if evento:
                self.avanzamento_all_avvio = evento
                self.ultimo_evento = testo
        # L'ultima amichevole giocata nella sessione, di cui si salva la cronaca.
        self.incontro = None
        self._testo_barra = None
        self._errore_aperto = False
        self._crea_controlli()
        self._crea_menu()
        self.applica_aspetto()
        dentro_area_utile(self, (1024, 768))
        self.Bind(wx.EVT_CLOSE, self._alla_chiusura)
        # Dalla issue 6 la voce Mercato segue le mosse della polisportiva attiva, e Ctrl+K parla anche quando non è disponibile;
        # dalla issue 8 anche quella del mercato degli allenatori, con Ctrl+Maiusc+G.
        self.Bind(wx.EVT_MENU_OPEN, self._all_apertura_del_menu)
        self.Bind(wx.EVT_CHAR_HOOK, self._tasto)
        self.aggiorna_le_voci()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._al_rinfresco, self.timer)
        self.timer.Start(modulo_barra.RINFRESCO_MILLESIMI)
        apertura = testi.apertura(mondo, origine, messaggi, rapporto, ultimo_prima, adesso_utc())
        if self.problemi_all_avvio:
            apertura = f"{testi.calendario_illeggibile(self.problemi_all_avvio)}\n{apertura}"
        if cartella_spostata:
            apertura = f"{cartella_spostata}\n{apertura}"
        if crash_precedente:
            apertura = f"{testi.crash_precedente(crash_precedente)}\n{apertura}"
        self.mostra(apertura)

    # Costruzione.

    def _crea_controlli(self):
        self.pannello = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.etichetta_vista = wx.StaticText(self.pannello, label="Vista principale")
        self.vista = wx.TextCtrl(self.pannello, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        self.vista.SetName("Vista principale")
        self.etichetta_barra = wx.StaticText(self.pannello, label="Barra di stato")
        # Le righe della barra non vanno mai a capo, come in Tornello: una riga lunga scorre di lato, e le
        # frecce su e giù passano da una riga di dati all'altra anche con i caratteri grandi.
        self.barra = wx.TextCtrl(self.pannello, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.TE_DONTWRAP)
        self.barra.SetName("Barra di stato")
        self.barra.Bind(wx.EVT_SET_FOCUS, self._alla_barra)
        self.barra.Bind(wx.EVT_KILL_FOCUS, self._via_dalla_barra)
        self.barra.Bind(wx.EVT_KEY_DOWN, self._tasto_giu_nella_barra)
        self.barra.Bind(wx.EVT_KEY_UP, self._mossa_nella_barra)
        self.barra.Bind(wx.EVT_LEFT_UP, lambda event: (event.Skip(), self._segui_il_cursore(None)))
        sizer.Add(self.etichetta_vista, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        sizer.Add(self.vista, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.etichetta_barra, 0, wx.LEFT | wx.RIGHT, 5)
        sizer.Add(self.barra, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        self.pannello.SetSizer(sizer)

    def voci_menu(self):
        """La tabella dei menu: per ogni menu il titolo e le voci, cioè testo, tasto rapido e comando; None separa."""
        return (
            ("&File", (("&Salva il mondo", "Ctrl+S", self.salva), None, ("&Esci", "Ctrl+Q", self.esci))),
            ("&Giocatori", (
                ("&Scheda del giocatore...", "Ctrl+G", self.scheda_giocatore),
                ("&Diario del giocatore...", "Ctrl+Shift+D", self.diario_giocatore),
                ("&Elenco dei giocatori", "Ctrl+E", lambda: self.mostra(testi.elenco_giocatori(self.mondo), "elenco dei giocatori", "elenco_giocatori")),
                ("&Classifica per valore", "Ctrl+L", lambda: self.mostra(testi.classifica(self.mondo), "classifica per valore", "classifica")),
                ("&TOP 10", "Ctrl+T", lambda: self.mostra(testi.top_10(self.mondo), "TOP 10", "top_10")),
                ("St&atistiche nazionali", "Ctrl+I", lambda: self.mostra(testi.statistiche(self.mondo), "statistiche nazionali", "statistiche_mondo")),
                None,
                ("Ce&rca giocatori...", "Ctrl+F", self.cerca),
                None,
                ("&Nuovi arrivati della sessione", "Ctrl+Shift+N", lambda: self.mostra(testi.lista_nuovi(self.mondo), "nuovi arrivati", "nuovi_arrivati")),
                ("Ritirati della sessi&one", "Ctrl+Shift+R", lambda: self.mostra(testi.lista_ritirati(self.mondo), "ritirati della sessione", "ritirati_sessione")),
                ("&Usciti di scena nella sessione", "Ctrl+Shift+U", lambda: self.mostra(testi.lista_usciti(self.mondo), "usciti di scena", "usciti_sessione")),
            )),
            ("&Polisportive", (
                ("&Nuova polisportiva...", "Ctrl+N", self.nuova_polisportiva),
                ("&Cambia polisportiva attiva...", "Ctrl+Shift+C", self.cambia_polisportiva),
                None,
                ("&Mercato...", "Ctrl+K", self.mercato),
                ("&Vendite dei tesserati...", None, self.vendite),
                ("Sv&incola un tesserato...", "Ctrl+Shift+S", self.svincola),
                ("Pa&ga gli arretrati...", "Ctrl+Shift+P", self.paga_arretrati),
                ("Sala &allenamento...", "Ctrl+Shift+L", self.sala_allenamento),
                ("Contratti e &rinnovi...", "Ctrl+Shift+K", self.contratti),
                # Lo staff della tappa 13, progetto 4.1: i tasti sono una proposta da confermare con Gabriele al collaudo.
                ("Staf&f della polisportiva attiva...", "Ctrl+H", self.staff),
                ("Mercato degli a&llenatori...", "Ctrl+Shift+G", self.mercato_allenatori),
                None,
                ("&Scheda della polisportiva attiva", "Ctrl+M", self.scheda_polisportiva),
                ("&Bilancio della polisportiva attiva", "Ctrl+B", self.bilancio),
                ("&Tesserati della polisportiva attiva", "Ctrl+Shift+T", self.tesserati_polisportiva),
                ("&Diario della polisportiva attiva", "Ctrl+Shift+M", self.diario_polisportiva),
                ("&Elenco delle polisportive", "Ctrl+Shift+E", lambda: self.mostra(testi.elenco_polisportive(self.mondo), "elenco delle polisportive", "elenco_polisportive")),
                None,
                ("&Password della polisportiva attiva...", None, self.password_polisportiva),
                ("C&hiudi la polisportiva attiva...", None, self.chiudi_polisportiva),
            )),
            ("Pa&rtite", (
                ("&Amichevole...", "Ctrl+O", self.amichevole),
                # Le amichevoli in serie, richiesta di Gabriele del 24 ottobre 2026: la prima voce dice il nome della polisportiva attiva.
                (self._voce_delle_amichevoli_dell_attiva(), None, self.amichevoli_dell_attiva),
                ("Gioca tutte le amichevoli di tutte le tue &polisportive", None, self.amichevoli_di_tutte),
                None,
                ("&Lancia una sfida...", "Ctrl+W", self.lancia_sfida),
                ("Sfide in a&rrivo...", "Ctrl+Shift+F", self.sfide_in_arrivo),
                ("S&torico delle sfide...", "Ctrl+Shift+H", self.storico_sfide),
                None,
                ("&Salva la cronaca", "Ctrl+Shift+O", self.salva_cronaca),
            )),
            # Il menu dei tornei, tappa 12, punto 12.1 del progetto: i tasti sono una proposta da confermare con Gabriele al collaudo.
            ("&Tornei", (
                ("&Calendario e iscrizioni...", "Ctrl+U", self.calendario_tornei),
                ("&Iscrizioni dei tuoi atleti...", "Ctrl+J", self.iscrizioni_tornei),
                ("&Tornei in corso...", "Ctrl+Y", self.tornei_in_corso),
                None,
                ("&Albo d'oro...", "Ctrl+Shift+B", self.albo_d_oro),
                ("Classifica &nazionale", "Ctrl+Shift+W", self.classifica_mondiale),
                None,
                ("&Editor dei modelli di torneo...", "Ctrl+Shift+J", self.editor_modelli),
                ("Editor delle &formule...", "Ctrl+Shift+Y", self.editor_formule),
                ("&Ripristina il calendario predefinito...", None, self.ripristina_calendario),
            )),
            ("&Mondo", (
                ("&Data e prossimo avanzamento", "Ctrl+D", lambda: self.mostra(testi.data_e_avanzamento(self.mondo, adesso_utc()), "data simulata", "data_e_avanzamento")),
                ("&Riepilogo dell'ultimo avanzamento", "Ctrl+Shift+A", self.riepilogo),
                ("&Vecchie glorie", "Ctrl+Shift+V", lambda: self.mostra(testi.vecchie_glorie(self.mondo), "vecchie glorie", "vecchie_glorie")),
            )),
            ("&Visualizza", (("Vista &principale", "F5", self.vai_alla_vista), ("&Barra di stato", "F7", self.vai_alla_barra))),
            ("&Impostazioni", (
                ("&Aspetto, colori e caratteri...", "Ctrl+P", self.cambia_aspetto),
                ("&Conservazione dei diari...", None, self.cambia_conservazione),
                ("&Effetti sonori...", None, self.cambia_effetti),
                ("&Velocità di gioco...", None, self.cambia_velocita),
                ("A&nnunci della cronaca...", None, self.cambia_annunci),
                ("&Barra di stato...", None, self.cambia_barra),
                None,
                ("Cartella del &mondo...", None, self.scegli_la_cartella_del_mondo),
            )),
            ("&Aiuto", (
                ("&Guida ai comandi", "F1", lambda: self.mostra(testi.guida(self.voci_guida(), modulo_barra.legenda(self.impostazioni["barra_di_stato"])),
                                                                "guida ai comandi", "guida")),
                ("&Manuale", "Shift+F1", self.manuale),
                ("&Novità", "F2", self.novita),
                ("&Informazioni", "F3", lambda: self.mostra(testi.informazioni(), "informazioni", "informazioni")),
                ("&Offrimi un caffè...", None, self.caffe),
                None,
                # Il PUB, il gruppo di supporto, issue 4: le mail si preparano con le funzioni comuni di GBUtils V221.
                ("&Entra al PUB (gruppo di supporto)...", None, self.entra_al_pub),
                ("&Chiedi aiuto al PUB...", None, self.chiedi_aiuto_al_pub),
            )),
        )

    def _crea_menu(self):
        barra_menu = wx.MenuBar()
        # Le voci dei menu per comando, da rendere disponibili o no: dalla issue 6 quella del mercato, dalla issue 8 anche quella degli allenatori.
        self.voci_del_menu = {}
        for titolo, voci in self.voci_menu():
            menu = wx.Menu()
            for voce in voci:
                if voce is None:
                    menu.AppendSeparator()
                    continue
                testo, tasto, comando = voce
                elemento = menu.Append(wx.ID_ANY, f"{testo}\t{tasto}" if tasto else testo)
                self.voci_del_menu[comando] = elemento
                self.Bind(wx.EVT_MENU, lambda event, c=comando: self._esegui(c), elemento)
            barra_menu.Append(menu, titolo)
        self.SetMenuBar(barra_menu)

    def voci_guida(self):
        """Le voci dei menu per la guida: titoli e testi senza le e commerciali, tasti con i nomi italiani."""
        voci = []
        for titolo, elenco in self.voci_menu():
            # La e commerciale doppia è quella di un nome, come nella voce delle amichevoli della polisportiva attiva: resta, una.
            comandi = [(testo.replace("&&", "\x00").replace("&", "").replace("\x00", "&").rstrip("."), tasto.replace("Shift", "Maiusc") if tasto else None)
                       for testo, tasto, _c in filter(None, elenco)]
            voci.append((titolo.replace("&", ""), comandi))
        return voci

    def applica_aspetto(self):
        for controllo in (self.pannello, self.etichetta_vista, self.vista, self.etichetta_barra, self.barra):
            aspetto.applica(controllo, self.impostazioni)
        # La barra è alta quanto le sue righe, nel suo carattere, più il bordo, la barra di scorrimento
        # orizzontale e mezza riga di margine, come il pie' di pagina di Tornello: dalla barra su misura di
        # D38 le righe sono quelle scelte, da una a sedici.
        riga = self.barra.GetCharHeight()
        fuori = max(self.barra.GetSize().height - self.barra.GetClientSize().height,
                    self.barra.GetWindowBorderSize().height + wx.SystemSettings.GetMetric(wx.SYS_HSCROLL_Y, self.barra))
        self.barra.SetMinSize(wx.Size(-1, riga * len(self.impostazioni["barra_di_stato"]) + riga // 2 + fuori))
        self.pannello.Layout()

    # I suoni dell'avvio e degli errori.

    def suoni_d_avvio(self):
        """
        Il suono dell'avvio, da chiamare quando la finestra è comparsa: prima l'avvio dalla copia di
        sicurezza, poi quello con le collezioni di nomi difettose, poi la nascita di un mondo nuovo,
        e infine l'avvio di sempre. Se il mondo è avanzato mentre il programma era chiuso, segue il
        suono dell'avanzamento, quando il primo è finito. Dopo l'avvio suona una notizia sola, la più
        importante: dalla tappa 14 prima di tutte il crash della volta prima, staccato di un secondo
        come la notizia dello staff; dal 23 ottobre 2026, subito dopo, i dati spostati da accanto al
        programma alla cartella del mondo, staccati allo stesso modo, col suono dei dati in riserva se sono
        andati in una riserva della cartella, perché lei aveva già un mondo, che resta in uso.
        """
        if self.origine == archivio.DALLA_COPIA:
            primo = "avvio_dalla_copia"
        elif self.avvisi_all_avvio:
            primo = "avvio_con_avvisi"
        elif self.origine == archivio.NATO:
            primo = "avvio_mondo_nuovo"
        else:
            primo = "avvio"
        suoni.suona(primo)
        if self.crash_precedente:
            suoni.in_coda("crash_precedente", pausa=PAUSA_NOTIZIA_DELLO_STAFF)
        elif self.cartella_spostata:
            suono = "dati_in_riserva" if isinstance(self.cartella_spostata, testi.DatiInRiserva) else "cartella_spostata"
            suoni.in_coda(suono, pausa=PAUSA_NOTIZIA_DELLO_STAFF)
        elif self.problemi_all_avvio:
            suoni.in_coda("calendario_illeggibile")
        elif getattr(self.mondo, "staff_appena_nato", False):
            # Dalla tappa 13: il mondo appena aggiornato al formato 8 ha lo staff, e la notizia vale più dell'avanzamento.
            suoni.in_coda("staff_appena_nato", pausa=PAUSA_NOTIZIA_DELLO_STAFF)
        elif self.avanzamento_all_avvio:
            suoni.in_coda(self.avanzamento_all_avvio)

    def errore_imprevisto(self, tipo, valore):
        """
        Un'eccezione sfuggita a un comando: il comando muore in silenzio, e dalla tappa 14 il resoconto
        completo va nel registro degli errori, accanto al programma. Qui la dicono il suono
        dell'allarme e un messaggio, che dice dove sta il resoconto.
        """
        if not self or self.IsBeingDeleted() or self._errore_aperto:
            return
        self._errore_aperto = True
        self._modali += 1
        try:
            suoni.suona("errore_imprevisto")
            wx.MessageBox(f"Il comando si è interrotto per un errore imprevisto: {tipo.__name__}, {valore}. {testi.resoconto_degli_errori(percorsi.cartella_del_programma())}",
                          "Errore imprevisto", wx.OK | wx.ICON_ERROR, self)
        finally:
            self._modali -= 1
            self._errore_aperto = False

    # Mostrare.

    def _esegui(self, comando):
        self.comandi += 1
        self._comandi_in_corso += 1
        try:
            comando()
        finally:
            self._comandi_in_corso -= 1
            # Dalla issue 6: il comando può aver speso mosse di mercato o cambiato la polisportiva attiva.
            self.aggiorna_le_voci()
            # Dalla barra su misura di D38: il comando può aver cambiato qualunque dato, e la barra si rifà tutta, una volta sola.
            self._istantanea.clear()
            self.aggiorna_barra()

    # La voce Mercato a mosse finite, issue 6 di Gabriele, dal collaudo di gioco del 23 ottobre 2026; dalla issue 8 anche
    # quella del mercato degli allenatori.

    def _mercato_chiuso(self):
        """Vero se la polisportiva attiva ha finito le mosse di mercato di oggi; senza polisportiva attiva no, e il comando lo dice."""
        p = self.mondo.miapolisportiva_attiva
        return p is not None and self.mondo.mosse_rimaste(p) <= 0

    def _comandi_del_mercato(self):
        """I comandi delle voci che a mosse finite non sono disponibili: Mercato, Ctrl+K, e Mercato degli allenatori, Ctrl+Maiusc+G."""
        return (self.mercato, self.mercato_allenatori)

    def aggiorna_le_voci(self):
        """
        Rimette in pari le voci Mercato e Mercato degli allenatori: non disponibili quando la polisportiva attiva
        ha finito le mosse di mercato, e NVDA le legge così, di nuovo disponibili appena le mosse tornano o cambia
        la polisportiva attiva. Senza polisportiva attiva restano disponibili. Dal 24 ottobre 2026 anche la voce
        delle amichevoli in serie della polisportiva attiva, che ne dice il nome.
        """
        if not self or self.chiusa:
            return
        disponibile = not self._mercato_chiuso()
        for comando in self._comandi_del_mercato():
            voce = self.voci_del_menu[comando]
            if voce.IsEnabled() != disponibile:
                voce.Enable(disponibile)
        voce = self.voci_del_menu[self.amichevoli_dell_attiva]
        testo = self._voce_delle_amichevoli_dell_attiva()
        if voce.GetItemLabel() != testo:
            voce.SetItemLabel(testo)

    def _all_apertura_del_menu(self, event):
        """
        All'apertura di un menu le voci del mercato si rimettono in pari. Windows apre il menu per finta anche
        quando si preme il tasto rapido di una sua voce, e guarda se la voce è disponibile soltanto dopo:
        così anche Ctrl+K e Ctrl+Maiusc+G la trovano com'è adesso.
        """
        self.aggiorna_le_voci()
        event.Skip()

    def _tasto(self, event):
        """
        Il gancio dei tasti della finestra, che wx chiama prima dei tasti rapidi dei menu. Windows non
        manda il comando di una voce disattivata, e Ctrl+K o Ctrl+Maiusc+G a mosse finite resterebbero muti:
        qui, se la voce non è disponibile, il suo tasto rapido esegue lo stesso il comando, che dice nella
        vista che per oggi le mosse sono finite. Ogni altro tasto prosegue come sempre.
        """
        for comando in self._comandi_del_mercato():
            voce = self.voci_del_menu[comando]
            rapido = voce.GetAccel()
            if rapido is None or event.GetKeyCode() != rapido.GetKeyCode() or event.GetModifiers() != _modificatori(rapido.GetFlags()):
                continue
            self.aggiorna_le_voci()
            if not voce.IsEnabled():
                self._esegui(comando)
                return
            break
        event.Skip()

    def mostra(self, testo, evento=None, suono=None):
        """Mette il testo nella vista principale, al posto di quello di prima, con il cursore all'inizio; suono è l'effetto del comando."""
        if suono:
            suoni.suona(suono)
        self.vista.ChangeValue(testo)
        aspetto.ridai_stile(self.vista, self.impostazioni)
        self.vista.SetInsertionPoint(0)
        self.vista.ShowPosition(0)
        self.vista.SetFocus()
        if evento:
            self.ultimo_evento = evento
        self.aggiorna_barra()

    def contesto_della_barra(self):
        """Quello che i dati della barra devono sapere della finestra: l'ultimo evento, l'ultimo avanzamento, il salvataggio e la sessione."""
        return modulo_barra.Contesto(self.mondo, adesso_utc(), self.ultimo_evento, self.rapporto, self._salvataggio_riuscito, adesso() - self.inizio,
                                     self.comandi)

    def aggiorna_barra(self):
        """
        Riscrive la barra di stato con le righe scelte nelle impostazioni, ma solo se è cambiata, e mai a metà di un comando:
        lo fa la fine del comando. Dalla barra su misura di D38 si riscrive anche col cursore sopra, che non disturba NVDA: il
        cursore resta sulla stessa riga e nella stessa colonna, a fine riga se la riga si è accorciata, sull'ultima riga se le
        righe sono meno di prima. Con TE_RICH2 le posizioni non sono indici della stringa: righe e colonne le traduce wx.
        """
        if not self or self.chiusa or self._comandi_in_corso:
            return
        self._dati_della_barra = modulo_barra.righe_coi_dati(self.impostazioni["barra_di_stato"], self.contesto_della_barra(), self._istantanea)
        testo = "\n".join(modulo_barra.testo_della_riga(riga) for riga in self._dati_della_barra)
        if testo == self._testo_barra:
            return
        self._testo_barra = testo
        _trovata, colonna, riga = self.barra.PositionToXY(self.barra.GetInsertionPoint())
        self.barra.ChangeValue(testo)
        aspetto.ridai_stile(self.barra, self.impostazioni)
        riga = min(max(riga, 0), max(self.barra.GetNumberOfLines() - 1, 0))
        colonna = min(max(colonna, 0), max(self.barra.GetLineLength(riga), 0))
        posizione = self.barra.XYToPosition(colonna, riga)
        if posizione >= 0:
            self.barra.SetInsertionPoint(posizione)
        # La riscrittura non è una mossa: il dato sotto il cursore si ricorda in silenzio, e se non è più quello di prima la
        # sua spiegazione lunga non parte.
        self._ricorda_il_cursore()

    def _ricorda_il_cursore(self):
        """Il dato e la posizione del cursore si ricordano in silenzio; se il dato è un altro, la spiegazione lunga non parte più."""
        chiave = self._chiave_al_cursore()
        if chiave != self._dato_sotto_il_cursore:
            self._ferma_la_spiegazione_lunga()
            self._dato_spiegato = None
        self._dato_sotto_il_cursore = chiave
        self._posizione_nota = self.barra.GetInsertionPoint()

    def _dato_al_cursore(self):
        """Il dato della barra su cui sta il cursore, o None sullo spazio fra due dati e dopo la fine della riga."""
        _trovata, colonna, riga = self.barra.PositionToXY(self.barra.GetInsertionPoint())
        if not 0 <= riga < len(self._dati_della_barra):
            return None
        return modulo_barra.dato_alla_colonna(self._dati_della_barra[riga], colonna)

    def _chiave_al_cursore(self):
        dato = self._dato_al_cursore()
        return dato.chiave if dato is not None else None

    def _tasto_giu_nella_barra(self, event):
        """Si ricorda il tasto che muove il cursore, anche ripetuto; i modificatori da soli non lo muovono."""
        if event.GetKeyCode() not in MODIFICATORI:
            self._tasto_della_mossa = (event.GetKeyCode(), event.ControlDown())
        event.Skip()

    def _mossa_nella_barra(self, event):
        """
        A ogni tasto lasciato sulla barra il cursore si segue col tasto che l'ha mosso: con Ctrl+Giù si lascia spesso Ctrl
        prima della freccia, e conta la freccia. Un tasto tenuto giù parla una volta sola, quando si lascia.
        """
        event.Skip()
        tasto = self._tasto_della_mossa or (event.GetKeyCode(), event.ControlDown())
        self._tasto_della_mossa = None
        self._segui_il_cursore(tasto)

    def _segui_il_cursore(self, tasto):
        """
        Il cursore si è forse mosso, col tasto dato, o senza tasti, col clic o col cursor routing del display: se è entrato
        in un dato che ha la sigla, la sintesi e il display braille ne dicono il nome, dopo quello che NVDA sta leggendo, e
        parte l'attesa della spiegazione lunga. Con un tasto che cambia riga il dato si ricorda in silenzio. Dentro lo stesso
        dato, già spiegato col nome, ogni mossa fa ripartire l'attesa; uscendo su uno spazio e rientrando, il nome si ridice.
        """
        if not self or self.chiusa:
            return
        posizione = self.barra.GetInsertionPoint()
        if posizione == self._posizione_nota:
            return
        self._posizione_nota = posizione
        di_riga = tasto is not None and (tasto[0] in TASTI_DI_RIGA or (tasto[0] in TASTI_DI_INIZIO_E_FINE and tasto[1]))
        dato = self._dato_al_cursore()
        chiave = dato.chiave if dato is not None else None
        if chiave == self._dato_sotto_il_cursore:
            if chiave is not None and chiave == self._dato_spiegato:
                self._aspetta_la_spiegazione_lunga()
            return
        self._dato_sotto_il_cursore = chiave
        self._ferma_la_spiegazione_lunga()
        self._dato_spiegato = None
        if dato is None or not dato.sigla or di_riga:
            return
        self._dato_spiegato = chiave
        annunci_condivisi().breve(dato.nome, self.impostazioni)
        self._aspetta_la_spiegazione_lunga()

    def _aspetta_la_spiegazione_lunga(self):
        self._ferma_la_spiegazione_lunga()
        self._attesa_lunga = wx.CallLater(ATTESA_DELLA_SPIEGAZIONE_LUNGA, self._spiega_a_lungo)

    def _ferma_la_spiegazione_lunga(self):
        if self._attesa_lunga is not None:
            self._attesa_lunga.Stop()
            self._attesa_lunga = None

    def _spiega_a_lungo(self):
        """Il cursore è rimasto fermo nel dato di cui si è detto il nome: la spiegazione lunga, una volta sola per ingresso."""
        self._attesa_lunga = None
        if not self or self.chiusa:
            return
        dato = self._dato_al_cursore()
        if dato is None or dato.chiave != self._dato_spiegato:
            return
        self._dato_spiegato = None
        annunci_condivisi().breve(dato.spiegazione, self.impostazioni)

    def _controlla_il_cursore(self):
        """
        Mentre la barra ha il fuoco, ogni CONTROLLO_DEL_CURSORE millesimi: il cursore mosso senza tasti, dal cursor routing del
        display braille, si segue come un clic. Mentre un tasto è giù lo segue il tasto, quando si lascia.
        """
        if not self or self.chiusa or not self._controllo_attivo:
            return
        if self._tasto_della_mossa is None:
            self._segui_il_cursore(None)
        wx.CallLater(CONTROLLO_DEL_CURSORE, self._controlla_il_cursore)

    def _alla_barra(self, event):
        """
        Quando il cursore arriva sulla barra, la ricalcola prima che lo screen reader la legga. L'arrivo non è una mossa: il
        dato su cui sta il cursore si ricorda in silenzio, e il suo nome si dice soltanto se ci si entra muovendosi. Da qui
        parte il controllo del cursore, per il cursor routing.
        """
        self.aggiorna_barra()
        self._tasto_della_mossa = None
        self._ricorda_il_cursore()
        if not self._controllo_attivo:
            self._controllo_attivo = True
            wx.CallLater(CONTROLLO_DEL_CURSORE, self._controlla_il_cursore)
        event.Skip()

    def _via_dalla_barra(self, event):
        """Il fuoco lascia la barra: si fermano il controllo del cursore e l'attesa della spiegazione lunga."""
        self._controllo_attivo = False
        self._ferma_la_spiegazione_lunga()
        self._dato_spiegato = None
        event.Skip()

    def _al_rinfresco(self, event):
        """
        Ogni 20 secondi, quanto dura un minuto simulato, se è maturato un giorno simulato e non c'è un dialogo aperto, fa
        avanzare il mondo; poi rinfresca la barra, anche sotto il cursore di chi legge, che resta dov'è.
        """
        if not self._modali and self.mondo.ticks_maturati():
            self.avanza()
        self.aggiorna_barra()

    def _ha_polisportive(self):
        return any(not p.is_cpu_controlled for p in self.mondo.polisportive.values())

    @staticmethod
    def _problemi_del_calendario():
        """I problemi del calendario dei tornei, modelli e formule che non si leggono, in frasi; una lista vuota se va tutto bene."""
        try:
            return modelli_torneo.GestoreModelli().problemi()
        except OSError as errore:
            return [f"La cartella dei tornei non si legge: {errore}"]

    def _sfidante(self):
        """Il nome della prima polisportiva che aspetta la risposta di una delle tue a una sfida, per la barra; None se nessuna."""
        for p in self.mondo.polisportive.values():
            if not p.is_cpu_controlled:
                for s in self.mondo.sfide.proposte_per(p.nome):
                    return s.sfidante["nome"]
        return None

    def _evento_avanzamento(self, rapporto, salvato):
        """
        Il suono e la riga della barra di un avanzamento, con suoni.evento_avanzamento: il calendario
        con problemi si dice una volta per sessione e a ogni cambio, e la sfida in attesa col nome di chi sfida.
        """
        if rapporto and rapporto.get("calendario_con_problemi"):
            problemi = tuple(self._problemi_del_calendario())
            if problemi == self._problemi_detti:
                rapporto = {**rapporto, "calendario_con_problemi": 0}
            else:
                self._problemi_detti = problemi or None
        return suoni.evento_avanzamento(rapporto, salvato, self._ha_polisportive(), self._sfidante())

    def avanza(self):
        """
        Fa avanzare il mondo dei giorni maturati, salva e lo annuncia nella barra di stato, con un
        suono solo: quello della notizia più importante, che si mette in coda se sta suonando
        l'effetto di un comando.
        """
        try:
            rapporto = self.mondo.processa_tempo_trascorso()
        except Exception:
            # Dalle verifiche del collaudo di gioco: l'avanzamento fermato a metà da un errore può aver già portato un
            # giorno nuovo, con le mosse di mercato di nuovo libere, e la voce Mercato si rimette in pari lo stesso.
            self.aggiorna_le_voci()
            raise
        if not rapporto["ticks"]:
            return
        # Dalla issue 6: col giorno nuovo le mosse di mercato ripartono, e la voce Mercato torna disponibile.
        self.aggiorna_le_voci()
        self._istantanea.clear()
        self.rapporto = rapporto
        self.rapporto_sessione = testi.somma_rapporti(self.rapporto_sessione, rapporto) if self.rapporto_sessione else rapporto
        salvato, _messaggi, _avvisi = self._salva_raccogliendo()
        evento, self.ultimo_evento = self._evento_avanzamento(rapporto, salvato)
        suoni.in_coda(evento)

    def _modale(self, dialogo):
        """Mostra un dialogo modale; finché resta aperto, il mondo non avanza."""
        self._modali += 1
        try:
            return dialogo.ShowModal()
        finally:
            self._modali -= 1

    def _domanda(self, testo, titolo, suono="domanda"):
        """Una domanda sì o no, con il no già scelto; finché è aperta, il mondo non avanza. Al no suona l'annullamento."""
        self._modali += 1
        try:
            suoni.suona(suono)
            risposta = wx.MessageBox(testo, titolo, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION, self)
        finally:
            self._modali -= 1
        if risposta != wx.YES:
            suoni.suona("annullato")
        return risposta

    def vai_alla_vista(self):
        suoni.suona("fuoco_vista")
        self.vista.SetFocus()

    def vai_alla_barra(self):
        """F7: il fuoco va nella barra; se c'è già, la barra si rifà tutta, anche i dati dell'istantanea."""
        suoni.suona("fuoco_barra")
        if self.barra.HasFocus():
            self._istantanea.clear()
            self._testo_barra = None
            self.aggiorna_barra()
        self.barra.SetFocus()

    # Comandi.

    def _salva_raccogliendo(self):
        """Salva il mondo e restituisce l'esito, i messaggi dell'archivio e, a parte, i suoi avvisi."""
        messaggi = []
        notifica = self.mondo.notifica
        self.mondo.notifica = messaggi.append
        try:
            riuscito, avvisi = archivio.salva_con_avvisi(self.mondo)
        finally:
            self.mondo.notifica = notifica
        # Per la barra su misura di D38: il dato del salvataggio compare finché l'ultimo non riesce.
        self._salvataggio_riuscito = riuscito
        return riuscito, messaggi, avvisi

    def _concludi(self, testo, evento, suono, salvare=True, coda=None, salvataggio=None):
        """
        La fine di un'operazione sulle polisportive: si salva subito, poi la vista mostra l'esito con
        il suo suono. Se il salvataggio non riesce, la vista aggiunge il perché, e dopo il suono
        dell'operazione si sente quello del salvataggio fallito. coda, se c'è, è un testo lungo da
        mettere dopo il perché, come la cronaca intera di un'amichevole, perché il perché resti a
        portata di mano e non in fondo a centinaia di righe. salvataggio, se c'è, è la coppia di
        esito e messaggi di un salvataggio già fatto, come quello prima della partita dal vivo.
        """
        riuscito, messaggi = True, []
        if salvataggio is not None:
            riuscito, messaggi = salvataggio
        elif salvare:
            riuscito, messaggi, _avvisi = self._salva_raccogliendo()
        if not riuscito:
            testo = "\n".join([testo, *messaggi])
        if coda:
            testo = f"{testo}\n{coda}"
        self.mostra(testo, evento, suono)
        if not riuscito:
            suoni.in_coda("salvataggio_non_riuscito")

    def salva(self):
        riuscito, messaggi, avvisi = self._salva_raccogliendo()
        if not riuscito:
            suono = "salvataggio_non_riuscito"
        elif avvisi:
            suono = "salvataggio_con_avviso"
        else:
            suono = "salvataggio_riuscito"
        self.mostra("\n".join(messaggi), f"salvato alle {adesso():%H:%M}" if riuscito else "salvataggio non riuscito", suono)

    def esci(self):
        self.Close()

    def _scegli_giocatore(self, titolo, pulsante, suono, giocatori=None):
        """
        Il giocatore scelto nel dialogo, oppure None se il dialogo è stato annullato; suono è quello
        dell'apertura, e giocatori, se dato, restringe l'elenco, che altrimenti ha tutto il mondo.
        """
        dialogo = SceltaGiocatore(self, self.mondo, titolo, pulsante, giocatori)
        try:
            suoni.suona(suono)
            if self._modale(dialogo) == wx.ID_OK:
                return dialogo.scelto
            suoni.suona("annullato")
            return None
        finally:
            dialogo.Destroy()

    def scheda_giocatore(self):
        g = self._scegli_giocatore("Scheda del giocatore", "&Mostra la scheda", "dialogo_scheda_giocatore")
        if g is not None:
            self.mostra(testi.scheda_giocatore(g, self.mondo), f"scheda di {testi.nome_completo(g)}", "scheda_giocatore")

    def diario_giocatore(self):
        g = self._scegli_giocatore("Diario del giocatore", "&Mostra il diario", "dialogo_diario_giocatore")
        if g is not None:
            self.mostra(testi.diario_giocatore(g), f"diario di {testi.nome_completo(g)}", "diario_giocatore")

    def diario_polisportiva(self):
        p = self._attiva()
        if p is not None:
            self.mostra(testi.diario_polisportiva(p), f"diario di {p.nome}", "diario_polisportiva")

    def cambia_conservazione(self):
        dialogo = Conservazione(self, self.mondo.conservazione_diari)
        try:
            suoni.suona("dialogo_conservazione")
            if self._modale(dialogo) == wx.ID_OK and dialogo.risultato is not None:
                self.mondo.conservazione_diari = dialogo.risultato
                self.mostra(testi.conservazione(self.mondo) + " Le voci più vecchie si tolgono a ogni salvataggio.", "conservazione dei diari", "conservazione_applicata")
            else:
                suoni.suona("annullato")
        finally:
            dialogo.Destroy()

    def cerca(self):
        """Ctrl+F, Cerca giocatori: dalla issue 8 la finestra Mercato e ricerca su tutti quelli in attività, col cursore nel campo del nome. Si apre sempre."""
        self._dopo_la_finestra(self._apri_mercato_e_ricerca("ricerca"))

    def riepilogo(self):
        """Il riepilogo dell'ultimo avanzamento; se nella sessione il mondo non è ancora avanzato, lo dice con il suo suono."""
        avanzato = bool(self.rapporto and self.rapporto["ticks"])
        self.mostra(testi.riepilogo_avanzamento(self.rapporto), "ultimo avanzamento", "riepilogo_avanzamento" if avanzato else "nessun_avanzamento")

    def scheda_polisportiva(self):
        p = self._attiva()
        if p is not None:
            self.mostra(testi.scheda_polisportiva(p, self.mondo), f"scheda di {p.nome}", "scheda_polisportiva")

    def tesserati_polisportiva(self):
        if self._attiva() is not None:
            self.mostra(testi.tesserati_attiva(self.mondo), "tesserati", "tesserati_polisportiva")

    # Le operazioni delle polisportive.

    def _attiva(self):
        """La polisportiva attiva; se non c'è, lo dice nella vista principale e restituisce None."""
        p = self.mondo.miapolisportiva_attiva
        if p is None:
            self.mostra("Non hai una polisportiva attiva: fondane una con Ctrl+N, o sceglila con Ctrl+Maiusc+C.", "nessuna polisportiva", "nessuna_polisportiva_attiva")
        return p

    def nuova_polisportiva(self):
        dialogo = NuovaPolisportiva(self, self.mondo)
        try:
            suoni.suona("dialogo_nuova_polisportiva")
            if self._modale(dialogo) != wx.ID_OK or dialogo.risultato is None:
                suoni.suona("annullato")
                return
            nome, password, attiva, luogo = dialogo.risultato
        finally:
            dialogo.Destroy()
        p = self.mondo.fonda_polisportiva(nome, password, attiva, luogo)
        self._concludi(testi.fondata(p, self.mondo), f"fondata {p.nome}", "polisportiva_fondata")

    def cambia_polisportiva(self):
        if all(p.is_cpu_controlled for p in self.mondo.polisportive.values()):
            self.mostra("Non hai ancora nessuna polisportiva: fondane una con Ctrl+N.", "nessuna polisportiva", "nessuna_polisportiva_tua")
            return
        dialogo = CambiaPolisportiva(self, self.mondo)
        try:
            suoni.suona("dialogo_cambia_polisportiva")
            if self._modale(dialogo) != wx.ID_OK or dialogo.scelta is None:
                suoni.suona("annullato")
                return
            p = dialogo.scelta
        finally:
            dialogo.Destroy()
        self.mondo.miapolisportiva_attiva = p
        self._concludi(testi.scheda_polisportiva(p, self.mondo), f"attiva {p.nome}", "polisportiva_attivata")

    def _mosse_finite(self, p):
        """Vero se per oggi la polisportiva p ha finito le mosse di mercato, e allora lo dice nella vista, col suo suono."""
        if self.mondo.mosse_rimaste(p) > 0:
            return False
        self.mostra(testi.mosse_finite(p), "nessuna mossa", "mosse_finite")
        return True

    def mercato(self):
        """
        Ctrl+K, il mercato dei giocatori: dalla issue 8 la finestra Mercato e ricerca, di serie sui liberi e su chi è in
        vendita da altri. Dalla issue 6, a mosse finite, la voce non è disponibile, e Ctrl+K arriva qui dal gancio dei
        tasti: la vista dice che per oggi le mosse sono finite, e la finestra non si apre. Senza polisportiva attiva si
        apre lo stesso, e si può soltanto cercare.
        """
        self._porta_del_mercato("mercato")

    def mercato_allenatori(self):
        """Ctrl+Maiusc+G, il mercato degli allenatori: la finestra Mercato e ricerca, di serie sugli allenatori liberi, che a mosse finite fa come Ctrl+K."""
        self._porta_del_mercato("allenatori")

    def _porta_del_mercato(self, porta):
        p = self.mondo.miapolisportiva_attiva
        if p is not None and self._mosse_finite(p):
            return
        self._dopo_la_finestra(self._apri_mercato_e_ricerca(porta))

    # La finestra Mercato e ricerca, issue 8 e decisione D36.

    def _apri_mercato_e_ricerca(self, porta):
        """
        La finestra Mercato e ricerca dalla porta d'ingresso data, che suona da sé la sua apertura; finché è aperta il
        mondo non avanza. Restituisce i suoi esiti: un metodo a sé, perché le prove lo sostituiscono.
        """
        dialogo = MercatoERicerca(self, self.mondo, self.impostazioni, porta)
        try:
            self._modale(dialogo)
            return dialogo.esiti_alla_fine()
        finally:
            dialogo.Destroy()

    def _dopo_la_finestra(self, esiti):
        """
        Dopo la finestra Mercato e ricerca: con un'amichevole scelta, la partita, col riepilogo della finestra davanti;
        con degli esiti, compresi quelli dei preset, la vista li riassume e il mondo si salva; senza, la vista resta
        com'era, e suona la finestra chiusa senza esiti. I filtri ricordati dalle porte vanno col salvataggio seguente.
        """
        parti = _parti_degli_esiti(esiti)
        riepilogo = testi.riepilogo_mercato_e_ricerca(self.mondo.miapolisportiva_attiva, self.mondo, **parti)
        if esiti.amichevole is not None:
            tuo, avversario, scelte = esiti.amichevole
            self.gioca_amichevole(tuo, avversario, scelte, prima=riepilogo)
            return
        if riepilogo is None:
            suoni.suona("finestra_chiusa_senza_esiti")
            return
        self._concludi(riepilogo, testi.evento_mercato_e_ricerca(**parti), "lavoro_concluso")

    def bilancio(self):
        p = self._attiva()
        if p is not None:
            self.mostra(testi.bilancio(p, self.mondo), f"bilancio di {p.nome}", "bilancio")

    def paga_arretrati(self):
        p = self._attiva()
        if p is None:
            return
        if not any(self.mondo.giocatori[gid].arretrati for gid in p.tesserati if gid in self.mondo.giocatori):
            self.mostra(f"Nessun tesserato di {p.nome} aspetta arretrati. {testi.info_mercato(p, self.mondo)}", "nessun arretrato", "nessun_arretrato")
            return
        dialogo = PagaArretrati(self, self.mondo, p)
        try:
            suoni.suona("dialogo_arretrati")
            self._modale(dialogo)
            pagati = list(dialogo.pagati)
        finally:
            dialogo.Destroy()
        righe = [f"Pagati {testi.euro(importo)} a {testi.nome_completo(g)}." for g, importo in pagati] or ["Nessun pagamento."]
        self._concludi("\n".join([*righe, testi.bilancio(p, self.mondo)]), f"arretrati: {testi.conta(len(pagati), 'pagamento', 'pagamenti')}", "lavoro_concluso", bool(pagati))

    def vendite(self):
        p = self._attiva()
        if p is None:
            return
        if not p.tesserati:
            self.mostra(f"{p.nome} non ha tesserati da vendere.", "nessun tesserato", "rosa_vuota")
            return
        dialogo = Vendite(self, self.mondo, p)
        try:
            suoni.suona("dialogo_vendite")
            self._modale(dialogo)
            fatte = list(dialogo.fatte)
        finally:
            dialogo.Destroy()
        self._concludi("\n".join(fatte or ["Nessuna vendita cambiata."]), f"vendite: {testi.conta(len(fatte), 'modifica', 'modifiche')}", "lavoro_concluso", bool(fatte))

    def _rosa_attiva(self, p):
        return [self.mondo.giocatori[gid] for gid in p.tesserati if gid in self.mondo.giocatori]

    def sala_allenamento(self):
        """
        La sala allenamento della tappa 11: spese a mano, allenamento completo, Allena tutti,
        programma e intensità. Alla chiusura la vista mostra le spese con il dettaglio e i cambi, e il
        mondo si salva soltanto se qualcosa è cambiato.
        """
        p = self._attiva()
        if p is None:
            return
        if not self._rosa_attiva(p):
            self.mostra(f"{p.nome} non ha tesserati da allenare.", "nessun tesserato", "rosa_vuota")
            return
        suoni.suona("dialogo_sala_allenamento")
        dialogo = SalaAllenamento(self, self.mondo, p, self.impostazioni)
        try:
            self._modale(dialogo)
            esiti, cambi = list(dialogo.esiti), dialogo.cambi()
        finally:
            dialogo.Destroy()
        self._concludi(testi.riepilogo_sala(p, esiti, cambi), testi.evento_sala(esiti, cambi), "lavoro_concluso", bool(esiti or cambi))

    def contratti(self):
        """I contratti e i rinnovi della tappa 11: alla chiusura la vista mostra gli esiti delle proposte, e il mondo si salva se ce ne sono."""
        p = self._attiva()
        if p is None:
            return
        if not self._rosa_attiva(p):
            self.mostra(f"{p.nome} non ha tesserati con un contratto.", "nessun tesserato", "rosa_vuota")
            return
        suoni.suona("dialogo_contratti")
        dialogo = Contratti(self, self.mondo, p, self.impostazioni)
        try:
            self._modale(dialogo)
            esiti = list(dialogo.esiti)
        finally:
            dialogo.Destroy()
        self._concludi(testi.riepilogo_contratti(p, esiti), testi.evento_contratti(esiti), "lavoro_concluso", bool(esiti))

    def staff(self):
        """
        Lo staff della tappa 13: alla chiusura la vista mostra le operazioni e lo staff di adesso, e il mondo si salva se
        ce ne sono. Dalla issue 8 Assumi apre la finestra Mercato e ricerca: le offerte agli allenatori sono operazioni
        dello staff, e il resto di quello che si è fatto nella finestra la vista lo riassume subito dopo; con
        un'amichevole scelta lì, lo staff si chiude e la partita si gioca, coi riepiloghi davanti.
        """
        p = self._attiva()
        if p is None:
            return
        suoni.suona("dialogo_staff")
        dialogo = Staff(self, self.mondo, p, self.impostazioni)
        try:
            self._modale(dialogo)
            esiti, della_finestra = list(dialogo.esiti), dialogo.esiti_della_finestra
        finally:
            dialogo.Destroy()
        parti = _parti_degli_esiti(della_finestra, allenatori=False)
        altri = testi.riepilogo_mercato_e_ricerca(p, self.mondo, **parti)
        testo = testi.riepilogo_staff(p, esiti, self.mondo)
        if altri is not None:
            testo = f"{testo}\n{altri}"
        if della_finestra.amichevole is not None:
            tuo, avversario, scelte = della_finestra.amichevole
            self.gioca_amichevole(tuo, avversario, scelte, prima=testo)
            return
        evento = testi.evento_staff(esiti) if altri is None else f"{testi.evento_staff(esiti)}, {testi.evento_mercato_e_ricerca(**parti)}"
        self._concludi(testo, evento, "lavoro_concluso", bool(esiti) or altri is not None)

    def svincola(self):
        p = self._attiva()
        if p is None:
            return
        rosa = [self.mondo.giocatori[gid] for gid in p.tesserati if gid in self.mondo.giocatori]
        if not rosa:
            self.mostra(f"{p.nome} non ha tesserati da svincolare.", "nessun tesserato", "rosa_vuota")
            return
        # Le mosse si guardano prima di far scegliere il tesserato, non dopo.
        if self._mosse_finite(p):
            return
        dialogo = SceltaGiocatore(self, self.mondo, f"Svincola un tesserato di {p.nome}", "S&vincola", rosa)
        try:
            suoni.suona("dialogo_svincolo")
            if self._modale(dialogo) != wx.ID_OK or dialogo.scelto is None:
                suoni.suona("annullato")
                return
            g = dialogo.scelto
        finally:
            dialogo.Destroy()
        # Dalla tappa 11 lo svincolo a contratto in corso costa una buonuscita: se la cassa non basta, si dice prima.
        problema = self.mondo.problema_svincolo(p, g)
        if problema:
            self.mostra(problema, "cassa insufficiente", "cassa_insufficiente")
            return
        if self._domanda(testi.domanda_svincolo(g, p, self.mondo), "Svincolo") != wx.YES:
            return
        buonuscita = self.mondo.svincola(p, g)
        self._concludi(testi.svincolato(g, p, self.mondo, buonuscita), f"svincolato {testi.nome_completo(g)}", "tesserato_svincolato")

    def password_polisportiva(self):
        p = self._attiva()
        if p is None:
            return
        dialogo = PasswordPolisportiva(self, p)
        try:
            suoni.suona("dialogo_password")
            if self._modale(dialogo) != wx.ID_OK or dialogo.risultato is None:
                suoni.suona("annullato")
                return
            p.imposta_password(dialogo.risultato)
        finally:
            dialogo.Destroy()
        self._concludi(testi.password_cambiata(p), "password" if p.protetta else "senza password", "password_impostata" if p.protetta else "password_tolta")

    def chiudi_polisportiva(self):
        p = self._attiva()
        if p is None:
            return
        if p.protetta:
            dialogo = ChiediPassword(self, p, f"Per chiudere {p.nome} serve la sua password.")
            try:
                suoni.suona("richiesta_password")
                if self._modale(dialogo) != wx.ID_OK:
                    suoni.suona("annullato")
                    return
            finally:
                dialogo.Destroy()
        if self._domanda(testi.domanda_chiusura(p), "Chiusura", "domanda_chiusura_polisportiva") != wx.YES:
            return
        liberati = self.mondo.chiudi_polisportiva(p)
        self._concludi(testi.chiusa(p.nome, liberati), f"chiusa {p.nome}", "polisportiva_chiusa")

    # L'amichevole, tappa 9.

    def _tuoi(self):
        """I numeri dei tesserati di tutte le tue polisportive."""
        return {gid for p in self.mondo.polisportive.values() if not p.is_cpu_controlled for gid in p.tesserati}

    def amichevole(self):
        """
        Ctrl+O, un'amichevole, regole di Gabriele: il tuo giocatore è un tesserato della polisportiva attiva,
        l'avversario chiunque altro, e nessuno dei due deve aver già giocato oggi. Prima i controlli di sempre, che
        la vista dice col loro suono: la polisportiva attiva, i suoi tesserati, chi di loro oggi gioca e, se ne
        gioca uno solo, qualcun altro da affrontare. Poi, dalla issue 8, la finestra Mercato e ricerca sugli
        avversari di oggi: lì si sceglie l'avversario, poi il tuo giocatore e le opzioni, e alla conferma la finestra
        si chiude e la partita la gioca gioca_amichevole.
        """
        p = self._attiva()
        if p is None:
            return
        rosa = self._rosa_attiva(p)
        if not rosa:
            self.mostra(f"{p.nome} non ha tesserati da far giocare.", "nessun tesserato", "rosa_vuota")
            return
        primi = MotorePartita(self.mondo).disponibili(rosa)
        if not primi:
            self.mostra(testi.nessuno_per_l_amichevole(self.mondo, adesso_utc(), poli=p), "nessuno gioca oggi", "nessun_giocatore_oggi")
            return
        oggi = self.mondo.datetime_corrente_simulazione
        if len(primi) == 1 and not any(g is not primi[0] and g.puo_giocare_amichevole(oggi) for g in self.mondo.giocatori.values()):
            self.mostra(testi.nessuno_per_l_amichevole(self.mondo, adesso_utc(), primo=primi[0]), "nessuno gioca oggi", "nessun_giocatore_oggi")
            return
        self._dopo_la_finestra(self._apri_mercato_e_ricerca("amichevole"))

    def gioca_amichevole(self, tuo, avversario, scelte, prima=None):
        """
        L'amichevole fra il tuo giocatore e l'avversario scelti nella finestra Mercato e ricerca, con le scelte delle
        opzioni, set, modo e livello, che si ricordano per la prossima. L'incontro si gioca e si registra subito e il
        mondo si salva; con Assisti si apre la finestra dal vivo, e quando se ne esce con Alt+V o dal risultato, o
        subito con Vai alla fine, la vista mostra il risultato, i punti allenamento e sotto la cronaca intera. L'esito
        suona quando si vede, non prima. Chi esce con Esc prima della fine non lo vede, decisione D30: la vista dice
        soltanto che l'incontro è registrato e dove leggerne il risultato; a incontro finito Esc vale come il pulsante
        del risultato. prima, se c'è, è il riepilogo della finestra da cui si arriva, che la vista mette davanti.
        """
        set_al_meglio, modo, livello = scelte
        ultime = (self.impostazioni["amichevole_set"], self.impostazioni["amichevole_modo"], self.impostazioni["amichevole_livello"])
        # Le scelte si ricordano per la prossima amichevole, anche dopo la chiusura (Gabriele, 8 ottobre 2026).
        # Se il file non si scrive, valgono comunque per questa sessione: l'incontro non si ferma per questo.
        if ultime != (set_al_meglio, modo, livello):
            self.impostazioni.update(amichevole_set=set_al_meglio, amichevole_modo=modo, amichevole_livello=livello)
            modulo_impostazioni.salva(self.impostazioni)
        motore = MotorePartita(self.mondo)
        # Il tuo giocatore è tuo per definizione; l'avversario può esserlo anche lui, di una qualunque delle tue polisportive.
        fra_tuoi = avversario.id in self._tuoi()
        istante, data_simulata = adesso(), self.mondo.datetime_corrente_simulazione
        gemello = None
        if modo == ASSISTI:
            risultato, gemello = motore.amichevole_da_assistere(tuo.id, avversario.id, set_al_meglio, velocita=self.impostazioni["velocita_gioco"])
        else:
            risultato = motore.gioca_amichevole(tuo.id, avversario.id, set_al_meglio)
        id_vincitore = risultato.parti[0] if risultato.vincitore == "A" else risultato.parti[1]
        if fra_tuoi:
            esito = "amichevole_fra_tuoi"
        elif id_vincitore == tuo.id:
            esito = "amichevole_vinta"
        else:
            esito = "amichevole_persa"
        self.incontro = v = UltimoIncontro(risultato, motore.nomi(risultato), livello, esito, istante, data_simulata)
        # Il mondo si salva subito, anche prima della partita dal vivo: chi esce a metà la trova già registrata.
        riuscito, messaggi, _avvisi = self._salva_raccogliendo()
        uscita = self._dal_vivo(v, gemello) if gemello is not None else None
        if uscita == CON_ESC:
            # Esc non svela il risultato, decisione D30: la vista dice soltanto che l'incontro è
            # registrato e dove leggerlo, con un suono suo e non quello dell'esito, e la barra non dice chi ha vinto.
            self._concludi(_davanti(prima, testi.amichevole_senza_risultato(v.nomi)), "amichevole registrata", "amichevole_registrata", salvataggio=(riuscito, messaggi))
            return
        # Alt+V nella finestra dal vivo: prima i cinque guizzi del salto alla fine, poi l'esito. Se il
        # salvataggio non è riuscito, dopo l'esito si sente quello, e i guizzi restano fuori: due suoni
        # messi in coda insieme si sovrapporrebbero. A incontro finito, dal collaudo di gioco, Alt+V torna
        # come il risultato, e i guizzi di un salto che non c'è non si sentono.
        salto = uscita == ALLA_FINE and riuscito
        # La cronaca intera va in coda, dopo il perché di un salvataggio non riuscito, che così resta in cima.
        self._concludi(_davanti(prima, testi.amichevole_solo_risultato(risultato, self.mondo)), v.evento_esito, "resto_dell_incontro" if salto else esito,
                       coda=testi.cronaca_amichevole(risultato, v.nomi, livello), salvataggio=(riuscito, messaggi))
        if salto:
            suoni.in_coda(esito)

    def _dal_vivo(self, v, gemello):
        """
        La finestra dal vivo dell'amichevole v, con l'incontro gemello da svolgere; restituisce come se
        n'è usciti. La velocità di gioco cambiata con più e meno vale anche per le partite che seguono.
        """
        dialogo = FinestraDalVivo(self, gemello, v.nomi, v.livello, self.impostazioni["velocita_gioco"], self.impostazioni)
        try:
            suoni.suona("amichevole_al_via")
            self._modale(dialogo)
            uscita, velocita = dialogo.uscita, dialogo.velocita
        finally:
            dialogo.Destroy()
        if velocita != self.impostazioni["velocita_gioco"]:
            self.impostazioni = modulo_impostazioni.valide({**self.impostazioni, "velocita_gioco": velocita})
            modulo_impostazioni.salva(self.impostazioni)
        return uscita

    # Le amichevoli in serie, Gioca tutte le amichevoli, richiesta di Gabriele del 24 ottobre 2026, dal collaudo di gioco.

    def _voce_delle_amichevoli_dell_attiva(self):
        """
        Il testo della voce delle amichevoli in serie della polisportiva attiva, col suo nome, e la e commerciale di un nome
        raddoppiata, perché il menu non la prenda per la lettera della voce; senza polisportiva attiva, della polisportiva attiva.
        """
        p = self.mondo.miapolisportiva_attiva
        if p is None:
            return "&Gioca tutte le amichevoli della polisportiva attiva"
        return f"&Gioca tutte le amichevoli di {p.nome.replace('&', '&&')}"

    def amichevoli_dell_attiva(self):
        """
        Gioca tutte le amichevoli della polisportiva attiva: ogni suo tesserato che oggi può giocare ne gioca una contro un
        avversario scelto a caso nel raggio delle classi, come in _amichevoli_in_serie. Senza polisportiva attiva, o senza
        tesserati, la vista lo dice come per l'amichevole.
        """
        p = self._attiva()
        if p is None:
            return
        if not self._rosa_attiva(p):
            self.mostra(f"{p.nome} non ha tesserati da far giocare.", "nessun tesserato", "rosa_vuota")
            return
        self._amichevoli_in_serie([p], tutte=False)

    def amichevoli_di_tutte(self):
        """
        Gioca tutte le amichevoli di tutte le tue polisportive, nell'ordine dei nomi, come in _amichevoli_in_serie. Se nessuna
        ha tesserati la vista lo dice come per la polisportiva attiva, col nome quando la tua è una sola: il giorno dopo non serve.
        """
        mie = sorted((p for p in self.mondo.polisportive.values() if not p.is_cpu_controlled), key=lambda p: p.nome.casefold())
        if not mie:
            self.mostra("Non hai ancora nessuna polisportiva: fondane una con Ctrl+N.", "nessuna polisportiva", "nessuna_polisportiva_tua")
            return
        if not any(self._rosa_attiva(p) for p in mie):
            testo = f"{mie[0].nome} non ha tesserati da far giocare." if len(mie) == 1 else "Nessuna delle tue polisportive ha tesserati da far giocare."
            self.mostra(testo, "nessun tesserato", "rosa_vuota")
            return
        self._amichevoli_in_serie(mie, tutte=True)

    def _amichevoli_in_serie(self, polisportive, tutte):
        """
        Le amichevoli in serie delle polisportive date, regola di Gabriele del 24 ottobre 2026: per ogni tesserato che oggi
        può giocare, nell'ordine dei numeri, l'avversario si sceglie a caso fra chi oggi può giocare, con la classe entro 15
        livelli dalla sua e di un'altra polisportiva, con MotorePartita.amichevoli_in_serie. Si gioca senza la finestra dal
        vivo, al meglio dei set delle ultime opzioni dell'amichevole; poi il mondo si salva, e la vista riassume ogni incontro
        in una riga, con i totali in fondo. Se oggi nessuno dei tuoi può giocare, la vista dice perché, col suo suono. Gli
        incontri si giocano in pochi millesimi: il suono dell'esito aspetta la fine di quello dell'avvio.
        """
        motore = MotorePartita(self.mondo)
        gruppi = motore.da_far_giocare(polisportive)
        if not any(tesserati for _p, tesserati in gruppi):
            testo = testi.nessuno_per_l_amichevole(self.mondo, adesso_utc(), poli=polisportive[0], tutte=tutte)
            self.mostra(testo, "nessuno gioca oggi", "nessuno_per_le_amichevoli_in_serie")
            return
        set_al_meglio = self.impostazioni["amichevole_set"]
        suoni.suona("amichevoli_in_serie")
        serie = motore.amichevoli_in_serie(gruppi, set_al_meglio)
        giocate = bool(testi.amichevoli_giocate(serie))
        self._aspetta_il_suono()
        self._concludi(testi.riepilogo_amichevoli_in_serie(serie, self.mondo, set_al_meglio, tutte), testi.evento_amichevoli_in_serie(serie),
                       "amichevoli_in_serie_finite" if giocate else "nessun_avversario_nel_raggio", giocate)

    @staticmethod
    def _aspetta_il_suono():
        """Aspetta che finisca il suono in corso, più la pausa della coda, perché il prossimo non gli si sovrapponga."""
        resta = suoni.attesa()
        if resta > 0:
            time.sleep(resta + suoni.PAUSA_IN_CODA)

    def salva_cronaca(self):
        """
        La cronaca dell'ultimo incontro mostrato o ascoltato, dalla tappa 12 anche di torneo o di sfida,
        nel suo file, nella cartella delle cronache, al livello scelto; intestazione e nome del file
        dicono quando si è giocato, non quando si salva.
        """
        v = self.incontro
        if v is None:
            self.mostra(testi.NESSUNA_AMICHEVOLE, "nessun incontro", "nessun_incontro")
            return
        try:
            percorso = MotorePartita(self.mondo).salva_cronaca(v.risultato, v.livello, istante=v.istante, data_simulata=v.data_simulata, nomi=v.nomi)
        except OSError as errore:
            self.mostra(testi.cronaca_non_salvata(errore, v.tipo), "cronaca non salvata", "cronaca_non_salvata")
            return
        self.mostra(testi.cronaca_salvata(percorso, v.livello, v.nomi, v.tipo), "cronaca salvata", "cronaca_salvata")

    def _salva_velocita(self, velocita):
        """La velocità di gioco a cui si è arrivati ascoltando dal vivo o in differita: vale anche per le partite che seguono."""
        if velocita is not None and velocita != self.impostazioni["velocita_gioco"]:
            self.impostazioni = modulo_impostazioni.valide({**self.impostazioni, "velocita_gioco": velocita})
            modulo_impostazioni.salva(self.impostazioni)

    # Le sfide, tappa 12, punto 12.6.

    def lancia_sfida(self):
        """Il lancio di una sfida a una polisportiva del computer, che risponde subito; alla chiusura la vista dice gli esiti e il mondo si salva."""
        p = self._attiva()
        if p is None:
            return
        if sfide.disponibili(self.mondo, p) <= 0:
            self.mostra(f"{p.nome} non ha sfide da lanciare: il primo del mese ne arrivano due, fino a quattro.", "nessuna sfida da lanciare",
                        "nessuna_sfida_da_lanciare")
            return
        suoni.suona("dialogo_lancia_sfida")
        dialogo = LanciaSfida(self, self.mondo, p, self.impostazioni)
        try:
            self._modale(dialogo)
            esiti = list(dialogo.esiti)
        finally:
            dialogo.Destroy()
        testo = "\n".join([f"Sfide lanciate da {p.nome}: {len(esiti)}.", *esiti]) if esiti else f"{p.nome} non ha lanciato sfide."
        self._concludi(testo, f"sfide: {testi.conta(len(esiti), 'lancio', 'lanci')}", "lavoro_concluso", bool(esiti))

    def sfide_in_arrivo(self):
        """
        Le sfide che aspettano la risposta delle tue polisportive, entro oggi, prima dell'avanzamento seguente: accettare con la
        formazione o rifiutare. Dal collaudo di gioco del 25 ottobre 2026, risposte di Gabriele: di tutte le tue polisportive,
        l'attiva per prima, come le conta il dato Sfr della barra; senza sfide la finestra non si apre, e la vista lo dice.
        """
        attiva = self.mondo.miapolisportiva_attiva
        tue = sorted((p for p in self.mondo.polisportive.values() if not p.is_cpu_controlled), key=lambda p: p is not attiva)
        if not tue:
            self.mostra("Non hai ancora nessuna polisportiva: fondane una con Ctrl+N.", "nessuna polisportiva", "nessuna_polisportiva_tua")
            return
        if not any(sfide.in_arrivo(self.mondo, p) for p in tue):
            self.mostra(testi.nessuna_sfida_in_arrivo(), "nessuna sfida in arrivo", "nessuna_sfida_in_arrivo")
            return
        suoni.suona("dialogo_sfide_in_arrivo")
        dialogo = SfideInArrivo(self, self.mondo, tue)
        try:
            self._modale(dialogo)
            esiti = list(dialogo.esiti)
        finally:
            dialogo.Destroy()
        testo = "\n".join([f"Risposte alle sfide: {len(esiti)}.", *esiti]) if esiti else "Non hai risposto a nessuna sfida."
        self._concludi(testo, f"sfide: {testi.conta(len(esiti), 'risposta', 'risposte')}", "lavoro_concluso", bool(esiti))

    def storico_sfide(self):
        """Lo storico delle sfide delle tue polisportive, con l'ascolto in differita e la cronaca delle ultime dieci."""
        if not any(not p.is_cpu_controlled for p in self.mondo.polisportive.values()):
            self.mostra("Non hai ancora nessuna polisportiva: fondane una con Ctrl+N.", "nessuna polisportiva", "nessuna_polisportiva_tua")
            return
        suoni.suona("storico_sfide")
        dialogo = StoricoSfide(self, self.mondo, self.impostazioni)
        try:
            self._modale(dialogo)
            ultimo, velocita = dialogo.ultimo, dialogo.velocita
        finally:
            dialogo.Destroy()
        self._salva_velocita(velocita)
        if ultimo is not None:
            self.incontro = ultimo

    # I tornei, tappa 12, punto 12.1.

    def calendario_tornei(self, iscrizioni_subito=False):
        """
        Il calendario dei tornei e le iscrizioni a mano della polisportiva attiva: alla chiusura la vista
        dice le iscrizioni fatte e tolte, e il mondo si salva; se si è chiesto il pannello di un'edizione
        in corso, si apre subito dopo.
        """
        p = self._attiva()
        if p is None:
            return
        suoni.suona("dialogo_iscrizioni_tornei" if iscrizioni_subito else "dialogo_calendario_tornei")
        dialogo = CalendarioTornei(self, self.mondo, p, self.impostazioni, iscrizioni_subito)
        try:
            self._modale(dialogo)
            fatte, pannello = list(dialogo.fatte), dialogo.pannello_chiesto
        finally:
            dialogo.Destroy()
        self._concludi(testi.riepilogo_calendario(p, fatte), testi.evento_calendario(fatte) if fatte else "calendario", "lavoro_concluso", bool(fatte))
        if pannello is not None:
            self.tornei_in_corso(pannello)

    def iscrizioni_tornei(self):
        self.calendario_tornei(iscrizioni_subito=True)

    def tornei_in_corso(self, torneo_scelto=None):
        """
        Il pannello dei tornei in corso e conclusi di recente: alla chiusura l'ultimo incontro ascoltato o
        letto diventa quello di Salva la cronaca, e se si sono mostrati dei risultati il mondo si salva.
        """
        suoni.suona("dialogo_tornei_in_corso")
        dialogo = PannelloTornei(self, self.mondo, self.impostazioni, torneo_scelto)
        try:
            self._modale(dialogo)
            ultimo, velocita, svelati = dialogo.ultimo, dialogo.velocita, dialogo.svelati
        finally:
            dialogo.Destroy()
        self._salva_velocita(velocita)
        if ultimo is not None:
            self.incontro = ultimo
        righe = [f"Pannello dei tornei: {testi.conta(svelati, 'risultato mostrato', 'risultati mostrati')}."]
        if ultimo is not None:
            righe.append(f"L'ultimo incontro, {ultimo.nomi['A'].testo} contro {ultimo.nomi['B'].testo}, ha la cronaca da salvare con Ctrl+Maiusc+O.")
        self._concludi("\n".join(righe), "pannello dei tornei", "lavoro_concluso", bool(svelati))

    def albo_d_oro(self):
        suoni.suona("albo_d_oro")
        dialogo = AlboDOro(self, self.mondo)
        try:
            self._modale(dialogo)
        finally:
            dialogo.Destroy()

    def classifica_mondiale(self):
        self.mostra(testi.classifica_mondiale(self.mondo, tuoi=tuoi_del_mondo(self.mondo)), "classifica nazionale", "classifica_mondiale")

    def editor_modelli(self):
        """L'editor dei modelli di torneo: alla chiusura la vista dice che cosa è cambiato; il mondo non si tocca, perché i modelli stanno fuori dal salvataggio."""
        suoni.suona("dialogo_editor_modelli")
        dialogo = EditorModelli(self)
        try:
            self._modale(dialogo)
            esiti = list(dialogo.esiti)
        finally:
            dialogo.Destroy()
        testo = "\n".join(["Modelli di torneo: le modifiche valgono per le edizioni future.", *esiti]) if esiti else "Nessun modello di torneo cambiato."
        self._problemi_detti = None
        self.mostra(testo, f"modelli: {testi.conta(len(esiti), 'modifica', 'modifiche')}", "lavoro_concluso")

    def editor_formule(self):
        """L'editor delle formule: alla chiusura la vista dice le formule salvate ed eliminate."""
        suoni.suona("dialogo_editor_formule")
        dialogo = EditorFormule(self)
        try:
            self._modale(dialogo)
            esiti = list(dialogo.esiti)
        finally:
            dialogo.Destroy()
        testo = "\n".join(["Formule dei tornei: le modifiche valgono per le edizioni future.", *esiti]) if esiti else "Nessuna formula cambiata."
        self._problemi_detti = None
        self.mostra(testo, f"formule: {testi.conta(len(esiti), 'modifica', 'modifiche')}", "lavoro_concluso")

    def ripristina_calendario(self):
        """Rimette il calendario predefinito, dopo la domanda col no già scelto: quello di prima va da parte, e cambiano soltanto le edizioni future."""
        domanda = ("Rimettere il calendario predefinito dei tornei? I modelli e le formule di adesso vanno in una cartella a parte, dentro la cartella tornei, "
                   "e cambiano soltanto le edizioni future.")
        if self._domanda(domanda, "Ripristina il calendario") != wx.YES:
            return
        try:
            da_parte = modelli_torneo.GestoreModelli().ripristina_predefiniti()
        except OSError as errore:
            # Dalla V228 col suo suono, e non più con quello del calendario illeggibile, che parla d'altro. Dal collaudo
            # di gioco, se il ripristino si è fermato a metà, il messaggio dice dove sono i file già messi da parte: dalle
            # verifiche li chiama file, perché possono esserci soltanto dei modelli, senza le formule.
            testo = f"Il calendario predefinito non si è potuto rimettere: {errore}."
            da_parte = getattr(errore, "da_parte", None)
            if da_parte:
                testo += f" I file di prima già messi da parte sono nella cartella {da_parte}."
            self.mostra(testo, "calendario non ripristinato", "calendario_non_ripristinato")
            return
        self._problemi_detti = None
        self.mostra(f"Il calendario predefinito è tornato. Quello di prima è nella cartella {da_parte}.", "calendario predefinito", "calendario_ripristinato")

    # Le impostazioni.

    def _salva_impostazioni(self, suono_riuscito):
        """Salva le impostazioni e suona com'è andata; restituisce vero se il file si è scritto."""
        salvate = modulo_impostazioni.salva(self.impostazioni)
        suoni.suona(suono_riuscito if salvate else "impostazioni_non_salvate")
        return salvate

    def cambia_aspetto(self):
        dialogo = Aspetto(self, self.impostazioni)
        try:
            suoni.suona("dialogo_aspetto")
            if self._modale(dialogo) == wx.ID_OK and dialogo.risultato is not None:
                self.impostazioni = dialogo.risultato
                salvate = self._salva_impostazioni("aspetto_applicato")
                self.applica_aspetto()
                self.ultimo_evento = "aspetto aggiornato" if salvate else "aspetto non salvato"
                self._testo_barra = None
                self.aggiorna_barra()
            else:
                suoni.suona("annullato")
        finally:
            dialogo.Destroy()

    def cambia_effetti(self):
        """
        Il volume degli effetti sonori e, dalla decisione D30, quello della partita dal vivo: il primo
        vale subito, e l'OK si sente già al volume nuovo; il secondo dalla prossima partita.
        """
        dialogo = EffettiSonori(self, self.impostazioni["volume_effetti"], self.impostazioni["volume_partita"])
        try:
            suoni.suona("dialogo_effetti_sonori")
            if self._modale(dialogo) == wx.ID_OK and dialogo.risultato is not None:
                effetti, partita = dialogo.risultato
                self.impostazioni = modulo_impostazioni.valide({**self.impostazioni, "volume_effetti": effetti, "volume_partita": partita})
                suoni.imposta_volume(self.impostazioni["volume_effetti"])
                salvate = self._salva_impostazioni("effetti_sonori_applicati")
                volumi = f"effetti {self.impostazioni['volume_effetti']}, partita {self.impostazioni['volume_partita']}"
                self.ultimo_evento = f"volume {volumi}" if salvate else "volumi non salvati"
                self.aggiorna_barra()
            else:
                suoni.suona("annullato")
        finally:
            dialogo.Destroy()

    def cambia_velocita(self):
        """La velocità di gioco della partita dal vivo, decisioni D12 e D29: vale dalla prossima partita, e anche dopo la chiusura."""
        dialogo = VelocitaDiGioco(self, self.impostazioni["velocita_gioco"])
        try:
            suoni.suona("dialogo_velocita_di_gioco")
            if self._modale(dialogo) == wx.ID_OK and dialogo.risultato is not None:
                self.impostazioni = modulo_impostazioni.valide({**self.impostazioni, "velocita_gioco": dialogo.risultato})
                salvate = self._salva_impostazioni("velocita_di_gioco_salvata")
                self.ultimo_evento = f"velocità di gioco {self.impostazioni['velocita_gioco']}" if salvate else "velocità di gioco non salvata"
                self.aggiorna_barra()
            else:
                suoni.suona("annullato")
        finally:
            dialogo.Destroy()

    def cambia_barra(self):
        """
        La barra di stato su misura, D38: la finestra sceglie le righe e i loro dati; al Salva la barra nuova si scrive nel
        file delle impostazioni e si vede subito, alta quanto le sue righe, e anche dopo la chiusura.
        """
        dialogo = BarraDiStato(self, self.impostazioni, self.contesto_della_barra)
        try:
            suoni.suona("dialogo_barra_di_stato")
            if self._modale(dialogo) == wx.ID_OK and dialogo.risultato is not None:
                self.impostazioni = modulo_impostazioni.valide({**self.impostazioni, "barra_di_stato": dialogo.risultato})
                salvate = self._salva_impostazioni("barra_di_stato_salvata")
                self.ultimo_evento = "barra di stato salvata" if salvate else "barra di stato non salvata"
                self._istantanea.clear()
                self.applica_aspetto()
                self.aggiorna_barra()
            else:
                suoni.suona("annullato")
        finally:
            dialogo.Destroy()

    def cambia_annunci(self):
        """Gli annunci della cronaca della partita dal vivo e della differita, 1.79.0: valgono dalla riga seguente, e anche dopo la chiusura."""
        dialogo = AnnunciDellaCronaca(self, self.impostazioni)
        try:
            suoni.suona("dialogo_annunci_cronaca")
            if self._modale(dialogo) == wx.ID_OK and dialogo.risultato is not None:
                self.impostazioni = modulo_impostazioni.valide({**self.impostazioni, **dialogo.risultato})
                salvate = self._salva_impostazioni("annunci_cronaca_salvati")
                stato = "accesi" if self.impostazioni["annunci_cronaca"] else "spenti"
                self.ultimo_evento = f"annunci della cronaca {stato}" if salvate else "annunci della cronaca non salvati"
                self.aggiorna_barra()
            else:
                suoni.suona("annullato")
        finally:
            dialogo.Destroy()

    def novita(self):
        try:
            with open(percorsi.risorsa("CHANGELOG.md"), encoding="utf-8") as f:
                testo = testi.novita(f.read())
            suono = "novita"
        except OSError as e:
            testo = f"Il file delle novità non si può leggere: {e}."
            suono = "novita_illeggibile"
        self.mostra(testo, "novità", suono)

    def manuale(self):
        """
        Il manuale, manuale.html, nel browser predefinito, dalla tappa 14: la vista resta com'era, e la
        barra dice che il manuale è aperto. Se il file manca, o Windows non lo apre, lo dice la vista,
        col suono suo del manuale che manca.
        """
        percorso = percorsi.risorsa("manuale.html")
        if not os.path.isfile(percorso):
            self.mostra(f"Il manuale non c'è: dovrebbe essere il file {percorso}. Reinstallare MESS lo rimette al suo posto.", "manuale mancante",
                        "manuale_mancante")
            return
        try:
            os.startfile(percorso)  # noqa: S606 - il manuale si apre col browser che Windows associa all'HTML
        except OSError as errore:
            self.mostra(f"Il manuale non si apre nel browser: {errore.strerror or errore}. È il file {percorso}.", "manuale non aperto", "manuale_mancante")
            return
        suoni.suona("manuale")
        self.ultimo_evento = "manuale nel browser"
        self.aggiorna_barra()

    def caffe(self):
        invito = Donazione(lang="it", probabilita=100, stampa=False) or "Grazie se vorrai offrire un caffè all'autore."
        dialogo = Caffe(self, invito, self.impostazioni)
        try:
            suoni.suona("caffe")
            self._modale(dialogo)
        finally:
            dialogo.Destroy()

    # La cartella del mondo, richiesta di Gabriele del 23 ottobre 2026: si sceglie con la finestra di
    # Windows, e i dati ci si spostano, oppure MESS si riapre sul mondo che la cartella ha già.

    def scegli_la_cartella_del_mondo(self):
        """
        Cartella del mondo, nel menu Impostazioni: la finestra di Windows sceglie dove stanno il mondo, le
        impostazioni, i tornei e le cronache. Se la cartella scelta ha già un mondo, una domanda chiede
        quale tenere; altrimenti i dati ci si spostano e MESS continua. Finché si sceglie, il mondo non avanza.
        """
        try:
            attuale = percorsi.cartella()
        except OSError as errore:
            # Il file che nomina la cartella del mondo si è rovinato a MESS aperto: lo sistema il prossimo avvio.
            # Dall'ultima verifica col suo suono, e non più con quello dell'avviso dell'avvio.
            self.mostra(f"Non so più dove sia la cartella del mondo: {errore}. Riapri MESS, e all'avvio potrai sceglierla.",
                        "cartella del mondo illeggibile", "cartella_illeggibile")
            return
        ora = adesso()
        self._modali += 1
        try:
            suoni.suona("cartella_mondo")
            nuova = scegli_cartella(self, testi.TITOLO_DELLA_SCELTA, attuale)
        finally:
            self._modali -= 1
        programma = percorsi.cartella_del_programma()
        if nuova is None:
            self._cartella_invariata()
        elif percorsi.stessa(nuova, attuale):
            # Dalla verifica del 23 ottobre 2026 le cartelle rifiutate hanno il loro suono: l'annullamento resta ad Annulla e a Esc.
            self.mostra(testi.cartella_gia_del_mondo(attuale), "cartella del mondo invariata", "cartella_rifiutata")
        elif cartella_del_mondo.intrecciate(attuale, nuova):
            self.mostra(testi.cartelle_intrecciate(nuova, attuale), "cartella del mondo invariata", "cartella_rifiutata")
        elif cartella_del_mondo.intrecciate(programma, nuova):
            # Dentro la cartella tornei del programma, per esempio: alla partenza seguente MESS la sposterebbe dentro sé stessa.
            self.mostra(testi.intrecciata_col_programma(nuova, programma, attuale), "cartella del mondo invariata", "cartella_rifiutata")
        elif not cartella_del_mondo.ha_un_mondo(nuova):
            self._porta_il_mondo(attuale, nuova, ora)
        else:
            scelta = self._quale_mondo(attuale, nuova, ora)
            if scelta == USA_IL_MONDO_DELLA_CARTELLA:
                self._usa_il_mondo_della_cartella(nuova)
            elif scelta == PORTA_IL_MIO_MONDO:
                self._porta_il_mondo(attuale, nuova, ora)
            else:
                self._cartella_invariata()

    def _cartella_invariata(self):
        suoni.suona("annullato")
        self.ultimo_evento = "cartella del mondo invariata"
        self.aggiorna_barra()

    def _quale_mondo(self, attuale, nuova, ora):
        """
        La domanda col suono delle domande quando la cartella scelta ha già un mondo: il codice della scelta,
        o wx.ID_CANCEL. Usa il mondo della cartella non si offre quando quel mondo non si legge, perché MESS
        si riaprirebbe su un salvataggio che lo ferma, né quando la cartella del mondo aperto non si
        raggiunge più, perché i suoi progressi non si salverebbero da nessuna parte.
        """
        raggiungibile = os.path.isdir(attuale)
        tuo = cartella_del_mondo.salvato(attuale) if raggiungibile else None
        suo = cartella_del_mondo.salvato(nuova)
        usabile = raggiungibile and not suo.errore
        testo = testi.mondo_gia_presente(attuale, tuo, nuova, suo, cartella_del_mondo.nome_della_riserva(nuova, ora))
        recente = testi.piu_recente(tuo.data, suo.data) if usabile else None
        dialogo = MondoGiaPresente(self, testo, recente, self.impostazioni, usabile)
        try:
            suoni.suona("domanda")
            return self._modale(dialogo)
        finally:
            dialogo.Destroy()

    def _porta_il_mondo(self, attuale, nuova, ora):
        """
        Il mondo si salva, poi i dati passano nella cartella nuova, e quelli che lei aveva in una sua riserva
        datata; il file accanto al programma la nomina. Se qualcosa non riesce, niente è cambiato, e la vista
        dice il perché, dalla verifica del 23 ottobre 2026 col suono dello spostamento non riuscito; quello
        del salvataggio non riuscito resta al mondo che non si salva. Se la cartella del mondo di adesso non
        si raggiunge più, per esempio una penna staccata a MESS aperto, lì non si salva e non c'è niente da
        spostare: il mondo e le impostazioni si salvano nella cartella nuova, appena il file la nomina, così
        i progressi non si perdono; se nemmeno lì il mondo si salva, tutto torna com'era.
        """
        raggiungibile = os.path.isdir(attuale)
        if raggiungibile:
            riuscito, messaggi, _avvisi = self._salva_raccogliendo()
            if not riuscito:
                self.mostra(testi.mondo_non_salvato_per_la_cartella(messaggi), "cartella del mondo invariata", "salvataggio_non_riuscito")
                return
        dal_salvataggio = []
        non_salvato = []

        def salva_nella_nuova():
            riuscito, messaggi, _avvisi = self._salva_raccogliendo()
            dal_salvataggio.extend(messaggi)
            if riuscito:
                modulo_impostazioni.salva(self.impostazioni)
            else:
                non_salvato.append(True)
            return riuscito

        try:
            trasloco = cartella_del_mondo.cambia_cartella(nuova, ora, None if raggiungibile else salva_nella_nuova)
        except cartella_del_mondo.SpostamentoNonRiuscito as errore:
            registro.scrivi(f"I dati del mondo non si sono spostati da {attuale} a {nuova}: {errore.motivo}.")
            testo = "\n".join([testi.cartella_non_spostata(errore, nuova, attuale), *dal_salvataggio])
            self.mostra(testo, "mondo non spostato", "salvataggio_non_riuscito" if non_salvato else "cartella_non_spostata")
            return
        if raggiungibile:
            registro.scrivi(f"I dati del mondo sono passati da {attuale} a {nuova}.")
            self.mostra(testi.cartella_spostata(trasloco, attuale), "cartella del mondo cambiata", "cartella_spostata")
        else:
            registro.scrivi(f"La cartella del mondo {attuale} non si raggiungeva: il mondo si è salvato nella cartella {nuova}.")
            # Dalla V228 col suo suono: qui niente si è spostato, e il resto dei dati è rimasto nella cartella di prima.
            self.mostra(testi.cartella_salvata_altrove(trasloco, attuale), "cartella del mondo cambiata", "cartella_salvata_altrove")

    def _usa_il_mondo_della_cartella(self, nuova):
        """
        Il mondo di adesso si salva dov'è e lì resta, intatto; il file accanto al programma nomina la cartella
        nuova, e MESS lancia la copia che si riaprirà sul suo mondo, poi si chiude senza salvare di nuovo: il
        salvataggio andrebbe ormai nella cartella nuova, sopra il suo mondo. Se la copia non parte, un messaggio
        dice di riaprire MESS a mano, e MESS si chiude col suono dell'uscita di sempre, perché non si riapre.
        """
        riuscito, messaggi, _avvisi = self._salva_raccogliendo()
        if not riuscito:
            self.mostra(testi.mondo_non_salvato_per_la_cartella(messaggi), "cartella del mondo invariata", "salvataggio_non_riuscito")
            return
        try:
            percorsi.imposta_cartella(nuova)
        except OSError as errore:
            # Dall'ultima verifica col suo suono, e non più con quello delle impostazioni non salvate.
            self.mostra(testi.cartella_non_scritta(errore, nuova), "cartella del mondo invariata", "cartella_non_registrata")
            return
        self._per_cambiare_cartella = True
        registro.scrivi(f"MESS si chiude per riaprirsi sul mondo della cartella {nuova}.")
        try:
            istanza.riapri()
        except OSError as errore:
            registro.scrivi(f"MESS non si è riaperto da solo: {errore}.")
            # Dalla verifica del 23 ottobre 2026 ha il suo suono, prima del messaggio.
            self._riapertura_mancata = True
            suoni.suona("riapertura_mancata")
            self._modali += 1
            try:
                wx.MessageBox(testi.riapertura_non_riuscita(errore, nuova), "Cartella del mondo", wx.OK | wx.ICON_WARNING, self)
            finally:
                self._modali -= 1
        self.Close(force=True)

    # Il PUB, il gruppo di supporto, issue 4: indirizzi, informazioni di sistema e mail vengono da
    # GBUtils V221, la finestra della mail da GBwx, le parole da testi. La finestra si apre sempre,
    # anche quando il programma di posta c'è, e senza posta guida un passo alla volta.

    def entra_al_pub(self):
        """Entra al PUB, nel menu Aiuto: la mail che iscrive al gruppo di supporto."""
        suoni.suona("pub_entra")
        self._mail_al_pub(testi.mail_d_iscrizione_al_pub(), "mail d'iscrizione al PUB pronta", "iscrizione al PUB annullata")

    def chiedi_aiuto_al_pub(self):
        """
        Chiedi aiuto al PUB, nel menu Aiuto: la mail al gruppo, con l'oggetto che dice la versione, la
        riga da sostituire con la domanda e le informazioni del computer; se ci sono il crash della volta
        prima o il registro degli errori, la finestra dice di allegarli.
        """
        from GBUtils import informazioni_di_sistema

        suoni.suona("pub_aiuto")
        mail = testi.mail_d_aiuto_al_pub(informazioni_di_sistema(","), self._registri_da_allegare(), percorsi.cartella_del_programma())
        self._mail_al_pub(mail, "mail d'aiuto al PUB pronta", "richiesta d'aiuto annullata")

    def _registri_da_allegare(self):
        """
        I nomi dei file del registro da allegare a una richiesta d'aiuto, quelli che ci sono e non sono
        vuoti, accanto al programma: il resoconto del crash della volta prima, che resta nel file del
        crash quando non si è potuto mettere da parte, e il registro degli errori.
        """
        nomi = [registro.FILE_DEL_CRASH_PRECEDENTE, registro.FILE_DEGLI_ERRORI]
        if self.crash_precedente:
            nomi.insert(0, os.path.basename(self.crash_precedente))
        presenti = []
        for nome in dict.fromkeys(nomi):
            with contextlib.suppress(OSError):
                if os.path.getsize(percorsi.nel_programma(nome)):
                    presenti.append(nome)
        return presenti

    def _mail_al_pub(self, mail, pronta, annullata):
        """
        La finestra di GBwx che prepara la mail; finché resta aperta, il mondo non avanza. La barra dice
        se la mail è pronta, cioè aperta nel programma di posta o scritta passo per passo, o se si è
        chiusa prima, con il suono dell'annullamento.
        """
        from GBwx import finestra_mail

        self._modali += 1
        try:
            riuscita = finestra_mail(self, mail["titolo"], mail["destinatario"], mail["oggetto"], mail["corpo"], mail["spiegazione"],
                                     mail["passi"], testi.PULSANTI_DEL_PUB, testi.SENZA_POSTA_DEL_PUB)
        finally:
            self._modali -= 1
        if not riuscita:
            suoni.suona("annullato")
        self.ultimo_evento = pronta if riuscita else annullata
        self.aggiorna_barra()

    # L'aggiornamento automatico e l'istanza unica, tappa 14, decisione D34: li conducono
    # aggiornamento.py e istanza.py, dai loro fili; qui la finestra e le frasi.

    def proponi_l_aggiornamento(self, versione_attuale, versione_nuova, note, attesa=None):
        """
        La proposta dell'aggiornamento, con le note della release rese leggibili come le novità: vero
        se si sceglie Aggiorna. Allo scadere dell'attesa il dialogo si chiude come Non adesso. Finché è
        aperto il mondo non avanza.
        """
        dialogo = Aggiornamento(self, versione_attuale, versione_nuova, testi.novita(note or ""), attesa, self.impostazioni)
        try:
            # In coda: all'avvio può suonare ancora il motivo di MESS.
            suoni.in_coda("aggiornamento_disponibile")
            scelta = self._modale(dialogo)
            scaduta = dialogo.scaduta
        finally:
            dialogo.Destroy()
        # Aggiorna, Non adesso e la proposta lasciata scadere hanno ciascuno il suo suono.
        if scelta == wx.ID_YES:
            suoni.suona("aggiornamento_scelto")
            self.ultimo_evento = f"scarico MESS {versione_nuova}"
        elif scaduta:
            suoni.suona("aggiornamento_scaduto")
            self.ultimo_evento = "aggiornamento rimandato: tempo scaduto"
        else:
            suoni.suona("annullato")
            self.ultimo_evento = "aggiornamento rimandato"
        self.aggiorna_barra()
        return scelta == wx.ID_YES

    def avvisa_dell_aggiornamento(self, testo):
        """
        Un esito dell'aggiornamento, in un messaggio che aspetta l'OK: torna soltanto quando lo si è
        chiuso, perché i 30 secondi dello script di sostituzione partano dopo, non mentre lo si legge.
        Il suono lo sceglie la frase: l'aggiornamento scaricato, quello non riuscito e il pacchetto
        non ancora pronto hanno ciascuno il suo. Lo scaricamento non riuscito ha l'icona dell'errore;
        il pacchetto non ancora pronto, che non è un guasto, dalla terza revisione quella dell'avviso.
        """
        esito = aggiornamento.esito(testo)
        suono = SUONI_DEGLI_ESITI.get(esito, "aggiornamento_esito")
        icona = {aggiornamento.NON_RIUSCITO: wx.ICON_ERROR, aggiornamento.NON_PRONTO: wx.ICON_WARNING}.get(esito, wx.ICON_INFORMATION)
        self._modali += 1
        try:
            suoni.in_coda(suono)
            wx.MessageBox(testo, "Aggiornamento di MESS", wx.OK | icona, self)
        finally:
            self._modali -= 1

    def avanzamento_dell_aggiornamento(self, presi, totale):
        """A che punto è lo scaricamento, nell'ultimo evento della barra di stato; dalla barra su misura di D38 anche sotto il cursore di chi legge."""
        if not self or self.chiusa:
            return
        if totale:
            self.ultimo_evento = f"aggiornamento scaricato {testi.con_articolo('al', testi.percento(presi * 100 // totale))}"
        else:
            self.ultimo_evento = f"aggiornamento: {testi.numero(presi / 1048576, 1)} MB scaricati"
        self.aggiorna_barra()

    def chiudi_per_aggiornare(self):
        """
        GBUtils sta per sostituire MESS: la finestra salva il mondo e si chiude senza il riepilogo di
        fine sessione, che aspetterebbe l'OK mentre lo script di sostituzione aspetta al massimo 30
        secondi. Un dialogo aperto si chiude prima: la partita dal vivo e la differita come con Esc,
        che ferma il suono e la cronaca e non svela il risultato, decisione D30; gli altri come
        annullati. Un messaggio aperto, che non si può chiudere da qui, si aspetta, e la chiusura
        riprova finché non è stato letto, ma per LIMITE_DELLA_CHIUSURA secondi al massimo: dopo, lo
        script ha rinunciato, o sta per farlo, e MESS resta aperto, e lo dice appena il messaggio si chiude.
        """
        if not self or self.chiusa:
            return
        if not self._per_aggiornare:
            self._per_aggiornare = True
            self._chiusura_dal = time.monotonic()
        if self._chiudi_i_dialoghi():
            if time.monotonic() - self._chiusura_dal < LIMITE_DELLA_CHIUSURA:
                wx.CallLater(RIPROVA_DELLA_CHIUSURA, self.chiudi_per_aggiornare)
            else:
                self._per_aggiornare = False
                self._chiusura_dal = None
                self._di_che_non_si_e_installato()
            return
        self.Close(force=True)

    def _chiudi_i_dialoghi(self):
        """Chiude i dialoghi modali aperti; vero se ce n'erano, o se resta aperto un messaggio, e la chiusura deve aspettare."""
        aperti = [d for d in wx.GetTopLevelWindows() if isinstance(d, wx.Dialog) and d.IsModal()]
        for dialogo in aperti:
            if isinstance(dialogo, FinestraDalVivo):
                dialogo.esci(CON_ESC)
            else:
                dialogo.EndModal(wx.ID_CANCEL)
        return bool(aperti or self._modali)

    def _di_che_non_si_e_installato(self):
        """L'aggiornamento non si è installato perché un messaggio è rimasto aperto: la vista lo dice quando nessun messaggio e nessun dialogo è più aperto."""
        if not self or self.chiusa:
            return
        if self._modali or any(isinstance(d, wx.Dialog) and d.IsModal() for d in wx.GetTopLevelWindows()):
            wx.CallLater(RIPROVA_DELLA_CHIUSURA, self._di_che_non_si_e_installato)
            return
        self.mostra(NON_INSTALLATO, "aggiornamento non installato", "aggiornamento_non_installato")

    def porta_in_primo_piano(self):
        """Si è provato ad aprire MESS una seconda volta: questa finestra torna in primo piano, col suo suono, e l'altra copia si chiude."""
        if not self or self.chiusa:
            return
        if self.IsIconized():
            self.Iconize(False)
        self.Raise()
        suoni.suona("primo_piano")

    # Chiusura.

    def _alla_chiusura(self, event):
        """
        Alla chiusura il mondo si salva, e una finestra riassume la sessione; poi la finestra se ne va.
        Il suono del congedo aspetta di finire, fino a un massimo, prima del riepilogo: dopo, il
        programma si chiude, e lo troncherebbe. Quando si chiude per l'aggiornamento il riepilogo non
        c'è; un salvataggio non riuscito si scrive nel registro degli errori e si dice in un messaggio.
        """
        self.chiusa = True
        self.timer.Stop()
        self._controllo_attivo = False
        self._ferma_la_spiegazione_lunga()
        if self._per_cambiare_cartella:
            # Il mondo si è appena salvato nella sua cartella, e il file accanto al programma nomina ormai l'altra:
            # un salvataggio adesso finirebbe lì, sopra il mondo che MESS sta per riaprire. Niente riepilogo.
            # Se la riapertura non è partita, MESS non si riapre: dall'ultima verifica il suono è quello
            # dell'uscita di sempre, che dice il mondo salvato, e non quello che promette la riapertura.
            suoni.suona("uscita" if self._riapertura_mancata else "cartella_cambiata", sync=suoni.ATTESA_USCITA)
            self.Destroy()
            return
        riuscito, messaggi, _avvisi = self._salva_raccogliendo()
        suoni.suona("uscita" if riuscito else "uscita_senza_salvataggio", sync=suoni.ATTESA_USCITA)
        if self._per_aggiornare:
            if not riuscito:
                perche = " ".join(["Il mondo non si è salvato prima dell'aggiornamento.", *messaggi])
                registro.scrivi(perche)
                wx.MessageBox(f"{perche}\nAlla riapertura ritroverai il mondo dell'ultimo salvataggio riuscito. Con OK MESS si chiude e installa la versione nuova.",
                              "Aggiornamento di MESS", wx.OK | wx.ICON_ERROR, self)
        else:
            riepilogo = testi.chiusura(adesso() - self.inizio, self.comandi, messaggi, self.rapporto_sessione)
            if not riuscito:
                riepilogo += "\nIl mondo non è stato salvato: alla prossima partenza ritroverai quello dell'ultimo salvataggio riuscito."
            dialogo = Lettura(self, "Fine sessione", riepilogo, self.impostazioni)
            with contextlib.suppress(RuntimeError):
                dialogo.ShowModal()
            dialogo.Destroy()
        self.Destroy()
