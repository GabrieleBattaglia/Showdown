"""
La finestra della partita dal vivo di MESS, disegnata da Gabriele con la decisione D29.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-08 con la tappa 10. L'amichevole è già giocata e registrata quando la finestra si
apre: qui un incontro gemello, con lo stesso seme, si svolge un momento alla volta, e ogni tratto si
compone in un buffer solo con partita_sonora, per chi ascolta dalla sua testata, di solito il tuo
giocatore. L'azione suona e si ferma a ogni punto, sanzione o fine set.
Il pulsante Prosegui ha già il fuoco: Invio o spazio fanno partire la tranche che segue; mentre
l'azione suona lo stesso pulsante diventa Pausa, e poi Riprendi, che riparte dal punto in cui si era
fermata. Durante il riscaldamento il pulsante diventa Salta il riscaldamento: la decisione D25 lo
vuole saltabile con un tasto, e D29 non ne nomina un altro. Ascolta fino a fine set, Alt+F, non si
ferma a ogni punto ma solo a fine set, e ha il suo suono anche mentre l'azione suona o è in pausa,
perché si sappia subito che il tasto è arrivato; Alt+L passa dalla parte dell'altro giocatore anche
a metà punto, ricomponendo il suono dal punto in cui si è arrivati; Alt+V va alla fine e mostra il
risultato; Esc esce senza svelarlo, e la vista principale dice dove leggerlo, decisione D30, ma a
incontro finito, quando la cronaca l'ha già detto, porta al risultato come il pulsante. Più
e meno cambiano al volo la velocità di gioco: il motore la usa dal momento seguente, e pause e
procedura già composte, come la pausa dopo il punto, si ripiegano alla velocità nuova appena il
suono tace, così il cambio non si sente. A fine incontro il pulsante lo dice e porta al risultato.
Con Tab e Maiusc+Tab si va nel campo della cronaca, dove si legge la tranche al livello scelto: il
campo cambia mentre il fuoco resta sul pulsante, perciò NVDA non lo legge da solo e non copre i
suoni. Dal 2026-10-21, scelta di Gabriele al collaudo della 1.50.0, il campo cresce riga per riga
mentre l'azione suona, e non soltanto a fine tranche o in pausa: chi ci legge dentro trova le righe
nuove in fondo, e il cursore resta dove l'ha lasciato. Dalla 1.79.0 le righe nuove si annunciano
anche, alla sintesi, al display braille o a tutti e due, secondo gli annunci della cronaca delle
impostazioni: annunci.py, con GBsintesi di GBUtils. Prima della prima tranche il campo tiene la guida dei tasti, che dice il lato e
la velocità di adesso anche dopo Alt+L, più e meno; F1 la rimette nel campo in ogni momento. Il suono
della partita si ferma sempre con la maniglia del suo ciclo, mai con Acusticator.stop, che
zittirebbe anche gli effetti della finestra.
Prosegui fa sentire il punto dalla ripresa del gioco, con il silenzio in testa accorciato: le pause e
la procedura a palla ferma che vengono prima, il time-out, il cambio campo, l'inizio del set, si
leggono nella cronaca, perché la pausa fra due punti la decide chi ascolta. Ascolta fino a fine set
invece fa sentire tutto di seguito, un segmento dopo l'altro, con le pause accorciate dalla velocità;
ma le pause lunghe, il time-out, il cambio campo e l'inizio del set, con la decisione D30 non le fa
sentire nemmeno lui: dopo la pausa di sempre che segue il punto, il suono riprende dalla ripresa del
gioco, e la pausa lunga si legge nella cronaca. La partita suona al suo volume, quello della partita
nelle impostazioni, a parte da quello degli effetti, secondo D30.
La cassa e l'orologio si possono sostituire, e le prove lo fanno: così nessuna prova suona.
Dalla tappa 12, il 2026-10-14, punti 6.5, 7.4 e 8.9 del progetto: la stessa finestra fa ascoltare in
differita gli incontri dei tuoi tesserati nei tornei e nelle sfide, giocati anche giorni prima, dal
gemello ricostruito con le fotografie; il titolo lo dice, e si ascolta dalla parte del tuo giocatore o
della tua squadra. La gara a squadre, un set a 31, si ascolta come il singolare: le formazioni e le
pause si leggono nel campo, e il cambio al tavolo ha un suono breve, mentre il campo dice chi gioca. Il
ritiro ferma l'azione col suo suono prima del triplice fischio; il cambio di braccio dell'ambidestro e
gli acciacchi si leggono nel campo, senza un suono loro. Le parti della tappa 12 sono di Gabriele
Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Dal collaudo di gioco di Gabriele, il 24 ottobre 2026, per la regola di un suono per ogni evento: a
incontro finito Alt+V, Vai alla fine, vale come il pulsante del risultato e come Esc, e la vista mostra
l'esito senza i cinque guizzi del salto alla fine, che non c'è più. È di Gabriele Battaglia (IZ4APU) &
ClaudIA (Claude Opus 5.5, UltraCode).
"""

import functools
import time

import wx

import annunci as modulo_annunci
import impostazioni as modulo_impostazioni
import partita_sonora as ps
import suoni
import testi
from gui import aspetto
from gui.dialoghi import _Dialogo
from partita import ascoltatore_della_differita, gemello_da_differita, nomi_dell_incontro

# Ogni quanti millesimi la finestra guarda a che punto è il suono.
BATTITO = 50
# Gli stati della finestra e i due modi di ascoltare.
FERMO = "fermo"
SUONA = "suona"
PAUSA = "pausa"
FINITO = "finito"
UN_PUNTO = "punto"
FINO_A_FINE_SET = "set"
# Come la finestra si è chiusa: con Esc prima della fine, con Vai alla fine prima della fine, o dal
# risultato a incontro finito, col pulsante, con Esc o con Vai alla fine.
CON_ESC = "esc"
ALLA_FINE = "fine"
AL_RISULTATO = "risultato"


@functools.cache
def annunci_condivisi():
    """
    Gli annunci della cronaca della sessione, 1.79.0: uno solo per tutte le finestre dal vivo e in
    differita, così la sintesi resta aperta fra una partita e l'altra; le attese del display sono di wx.
    """
    return modulo_annunci.Annunci(lambda secondi, funzione: wx.CallLater(max(1, round(secondi * 1000)), funzione))


class FinestraDalVivo(_Dialogo):
    """
    La partita dal vivo: gemello è l'incontro ancora da giocare, con lo stesso seme di quello
    registrato; nomi e livello sono quelli della cronaca, velocita quella di gioco delle impostazioni,
    da cui viene anche il volume della partita; senza impostazioni vale il volume predefinito.
    Alla chiusura uscita dice come si è chiusa, e velocita la velocità a cui si è arrivati. Dalla 1.79.0
    le righe nuove della cronaca si annunciano con annunci, quelli della sessione se non se ne danno e
    ci sono le impostazioni; senza impostazioni, come nelle prove, nessun annuncio.
    """

    def __init__(self, genitore, gemello, nomi, livello, velocita, impostazioni=None, cassa=None, orologio=None, ascoltatore="A", differita=False,
                 annunci=None):
        super().__init__(genitore, testi.titolo_dal_vivo(nomi, velocita, differita))
        self.nomi = nomi
        self.livello = livello
        self.velocita = velocita
        self.differita = differita
        self.impostazioni = impostazioni
        self.volume = modulo_impostazioni.valide(impostazioni)["volume_partita"]
        self.set_al_meglio = gemello.formato.set_al_meglio
        self.cronologia = ps.Cronologia(gemello)
        self.riproduttore = ps.Riproduttore(cassa, orologio or time.monotonic)
        # Dalla tappa 12 si ascolta dalla parte del tuo giocatore o della tua squadra, che in un torneo
        # o in una sfida può essere B; Alt+L passa all'altra, come sempre.
        self.ascoltatore = ascoltatore if ascoltatore in ("A", "B") else "A"
        self.stato = FERMO
        self.modo = UN_PUNTO
        self.segmento = None
        self.resa = None
        # In pausa: il secondo del buffer a cui ci si è fermati, e il suo primo istante se il cambio di lato ha tolto la composizione.
        self.posizione = 0.0
        self._t0_ricordato = 0.0
        # Le pieghe con cui suona il segmento corrente, e se la velocità è cambiata dopo che è stato composto.
        self._pieghe = ()
        self._da_ripiegare = False
        # Vero finché nel campo della cronaca c'è la guida dei tasti, che allora segue lato e velocità.
        self._guida_in_vista = True
        self.tranche = []
        # Quante voci della tranche il campo mostra già: mentre suona, il campo si riscrive soltanto quando ne arriva una nuova.
        self._voci_nel_campo = 0
        # Gli annunci della cronaca, 1.79.0, e quante righe della tranche hanno già letto.
        self.annunci = annunci if annunci is not None or impostazioni is None else annunci_condivisi()
        self._righe_annunciate = 0
        self.uscita = None
        self.prosegui = wx.Button(self.pannello, label="&Prosegui")
        self.sizer.Add(self.prosegui, 0, wx.ALL, 8)
        self.etichetta("&Cronaca")
        self.cronaca = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2, value=self._testo_della_guida()), 1)
        if impostazioni:
            aspetto.applica(self.cronaca, impostazioni)
        riga = wx.BoxSizer(wx.HORIZONTAL)
        self.fine_set = wx.Button(self.pannello, label="Ascolta fino a &fine set")
        self.lato = wx.Button(self.pannello, label=self._etichetta_lato())
        self.alla_fine = wx.Button(self.pannello, label="&Vai alla fine")
        for pulsante in (self.fine_set, self.lato, self.alla_fine):
            riga.Add(pulsante, 0, wx.ALL, 4)
        self.sizer.Add(riga, 0, wx.ALL, 4)
        self.prosegui.SetDefault()
        self.prosegui.Bind(wx.EVT_BUTTON, self.al_prosegui)
        self.fine_set.Bind(wx.EVT_BUTTON, self.fino_a_fine_set)
        self.lato.Bind(wx.EVT_BUTTON, self.cambia_lato)
        self.alla_fine.Bind(wx.EVT_BUTTON, lambda event: self.esci(ALLA_FINE))
        self.Bind(wx.EVT_CHAR_HOOK, self._tasto)
        self.Bind(wx.EVT_CLOSE, lambda event: self.esci(CON_ESC))
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.al_battito, self.timer)
        self.completa((640, 480))
        # Le sorgenti si sintetizzano adesso, una volta per sessione: la prima tranche parte subito come le altre.
        ps.prepara()
        self.prosegui.SetFocus()

    # Le etichette e il campo della cronaca.

    def _etichetta_lato(self):
        return f"Cambia &lato, ora ascolti da {self.nomi[self.ascoltatore].testo}"

    def _aggiorna_prosegui(self):
        """L'etichetta del pulsante con il fuoco, secondo lo stato: NVDA la legge quando cambia."""
        if self.stato == FINITO:
            etichetta = "Fine dell'incontro: vai al &risultato"
        elif self.stato == PAUSA:
            etichetta = "&Riprendi"
        elif self.stato == SUONA:
            etichetta = "&Salta il riscaldamento" if self.segmento.riscaldamento else "&Pausa"
        else:
            etichetta = "&Prosegui"
        if self.prosegui.GetLabel() != etichetta:
            self.prosegui.SetLabel(etichetta)
            self.pannello.Layout()

    def _scrivi(self, testo, tieni_il_cursore=False):
        """
        Il testo nel campo della cronaca, con lo stile scelto e il cursore in cima, senza spostare il fuoco
        dal pulsante. Con tieni_il_cursore, cioè per la cronaca che cresce mentre suona, a fine tranche e in
        pausa, chi sta leggendo nel campo non perde il segno: il cursore resta dove l'ha lasciato.
        """
        punto = self.cronaca.GetInsertionPoint() if tieni_il_cursore and self.cronaca.HasFocus() else 0
        self.cronaca.ChangeValue(testo)
        if self.impostazioni:
            aspetto.ridai_stile(self.cronaca, self.impostazioni)
        self.cronaca.SetInsertionPoint(min(punto, self.cronaca.GetLastPosition()))

    def _testo_della_guida(self):
        return testi.guida_dal_vivo(self.nomi, self.ascoltatore, self.set_al_meglio, self.velocita, self.differita)

    def _mostra_guida(self):
        """La guida dei tasti nel campo, con il lato e la velocità di adesso."""
        self._scrivi(self._testo_della_guida())
        self._guida_in_vista = True

    def _mostra(self, voci):
        """La cronaca delle voci nel campo, al livello scelto, al posto della guida o della tranche di prima."""
        righe = testi.righe_degli_eventi(voci, self.nomi, self.livello)
        self._scrivi("\n".join(righe) or "In questo tratto la cronaca, a questo livello, non ha frasi.", tieni_il_cursore=True)
        self._guida_in_vista = False
        self._voci_nel_campo = len(voci)
        self._annuncia(righe)

    def _annuncia(self, righe):
        """Le righe della tranche non ancora annunciate, con gli annunci della cronaca, 1.79.0."""
        nuove = righe[self._righe_annunciate:]
        self._righe_annunciate = max(self._righe_annunciate, len(righe))
        if nuove and self.annunci is not None:
            self.annunci.annuncia(nuove, modulo_impostazioni.valide(self.impostazioni))

    def _sentite(self, posizione=None):
        """Le voci della tranche fin dove il suono è arrivato: al secondo dato, o a quello della pausa."""
        secondo = self.posizione if posizione is None else posizione
        istante = self.resa.istante(secondo) if self.resa is not None else float("inf")
        return [voce for voce in self.tranche if voce[0].t <= istante + ps.TOLLERANZA]

    def _cronaca_al_volo(self, posizione):
        """
        Mentre l'azione suona, il campo aggiunge le righe delle voci appena sentite, scelta di Gabriele del
        21 ottobre 2026: prima arrivavano tutte a fine tranche. Finché nella tranche non si è sentita
        nessuna riga a questo livello, il campo tiene quello che aveva.
        """
        if posizione is None or self.resa is None or self.riproduttore.in_anticipo():
            return
        sentite = self._sentite(posizione)
        if len(sentite) == self._voci_nel_campo:
            return
        self._voci_nel_campo = len(sentite)
        righe = testi.righe_degli_eventi(sentite, self.nomi, self.livello)
        if righe:
            self._scrivi("\n".join(righe), tieni_il_cursore=True)
            self._guida_in_vista = False
            self._annuncia(righe)

    # Il suono.

    def _componi(self, da, anticipo=None):
        self.resa = ps.componi(self.segmento.udibili, self.ascoltatore, da=da, fine=self.segmento.fine, anticipo=anticipo, pieghe=self._pieghe)

    def _per_la_cassa(self):
        return ps.per_la_cassa(self.resa.buffer, self.volume)

    def _suona_segmento(self, segmento, fresco, sovrapponi=False, anticipo=0.0):
        """
        Compone il segmento e lo fa partire, dopo anticipo secondi di silenzio. Da fresco comincia
        dalla ripresa del gioco, col silenzio in testa accorciato; altrimenti prosegue dalla fine
        del segmento di prima, pause comprese, tranne la pausa lunga, che il buffer salta. La
        procedura che il motore ha svolto a un'altra velocità si ripiega subito a quella di adesso.
        """
        da = segmento.inizio if fresco or self.segmento is None else self.segmento.fine
        self.segmento = segmento
        self._pieghe = segmento.pieghe(self.velocita)
        self._da_ripiegare = False
        self._componi(da, ps.ANTICIPO if fresco else None)
        self.riproduttore.suona(self._per_la_cassa(), anticipo=anticipo, sovrapponi=sovrapponi)

    def _ricomponi(self, posizione, t0, sempre=True):
        """
        Il segmento ricomposto dall'istante t0, con le pause e la procedura che restano dal secondo
        posizione in avanti ripiegate alla velocità di adesso; quello che è già suonato resta com'era.
        Senza sempre ricompone soltanto se le pieghe cambiano. Vero se ha ricomposto.
        """
        adesso = ps.istante_del_motore(posizione, t0, self._pieghe)
        pieghe = self.segmento.pieghe(self.velocita, self._pieghe, da=adesso)
        self._da_ripiegare = False
        if not sempre and self.resa is not None and pieghe == self._pieghe:
            return False
        self._pieghe = pieghe
        self._componi(t0)
        return True

    def _ripiega_nel_silenzio(self):
        """
        La velocità è cambiata mentre l'azione suona: pause e procedura che restano nel segmento si
        ripiegano a quella nuova. Il buffer riparte dallo stesso secondo soltanto dove tace, perché
        il cambio non si senta; se adesso suona qualcosa, ci si riprova al battito che segue.
        """
        posizione = self.riproduttore.posizione()
        if posizione is None or self.resa is None or self.riproduttore.in_anticipo():
            return
        adesso = self.resa.istante(posizione)
        if self.segmento.pieghe(self.velocita, self._pieghe, da=adesso) == self._pieghe:
            self._da_ripiegare = False
            return
        if self.resa.in_silenzio(posizione):
            self._ricomponi(posizione, self.resa.t0)
            self.riproduttore.suona(self._per_la_cassa(), da=posizione, tieni_le_code=True)

    def _avvia(self, modo, anticipo=0.0):
        segmento = self.cronologia.prossimo(self.velocita)
        if segmento is None:
            self._finisci()
            return
        self.modo = modo
        self.tranche = list(segmento.voci)
        self._voci_nel_campo = 0
        self._righe_annunciate = 0
        self._suona_segmento(segmento, fresco=True, anticipo=anticipo)
        self.stato = SUONA
        self._aggiorna_prosegui()
        self.timer.Start(BATTITO)

    def _prosegui_di_seguito(self, fresco=False):
        """
        Fino a fine set: il segmento che segue parte appena finisce quello di prima, la cui coda
        finisce di suonare, e il suo buffer comincia con la pausa dopo il punto. Se prima della
        ripresa del gioco c'è una pausa lunga, time-out, cambio campo o inizio del set, non si
        sente: dopo la pausa di sempre il buffer salta alla ripresa, come fra due punti qualunque, e
        la pausa lunga è nella cronaca. Siccome la pausa di sempre sta nel buffer, più e meno, la
        pausa e il cambio di lato la trattano come tutte le altre.
        """
        segmento = self.cronologia.prossimo(self.velocita)
        if segmento is None:
            self._fine_tranche()
            return
        self.tranche.extend(segmento.voci)
        self._suona_segmento(segmento, fresco=fresco, sovrapponi=not fresco)
        self._aggiorna_prosegui()

    def _fine_tranche(self):
        self.riproduttore.ferma()
        self.timer.Stop()
        self.stato = FINITO if self.segmento is not None and self.segmento.ultimo else FERMO
        self._mostra(self.tranche)
        self._aggiorna_prosegui()

    def _finisci(self):
        self.stato = FINITO
        self._aggiorna_prosegui()

    def al_battito(self, event=None):
        """
        Il battito del timer: ferma le code finite, ripiega la procedura se la velocità è cambiata,
        passa al segmento che segue fino a fine set, o chiude la tranche; mentre suona, la cronaca
        cresce con le voci appena sentite.
        """
        if self.stato != SUONA:
            return
        finito = self.riproduttore.battito()
        if self._da_ripiegare and not finito:
            self._ripiega_nel_silenzio()
        posizione = self.riproduttore.posizione()
        if self.modo == FINO_A_FINE_SET and not self.segmento.fine_set and posizione is not None and posizione >= self.resa.secondi(self.segmento.fine):
            self._prosegui_di_seguito()
        elif finito:
            self._fine_tranche()
        if self.stato == SUONA:
            self._cronaca_al_volo(self.riproduttore.posizione())

    # I comandi.

    def al_prosegui(self, event=None):
        """Il pulsante con il fuoco: Prosegui, Pausa, Riprendi, Salta il riscaldamento, o il risultato a incontro finito."""
        if self.stato == FINITO:
            self.esci(AL_RISULTATO)
        elif self.stato == SUONA:
            if self.segmento.riscaldamento:
                self.salta_riscaldamento()
            else:
                self.pausa()
        elif self.stato == PAUSA:
            self.riprendi()
        else:
            self._avvia(UN_PUNTO)

    def fino_a_fine_set(self, event=None):
        """
        Alt+F, con il suo suono in ogni caso: da fermi fa partire l'ascolto fino a fine set, dopo il
        suono; mentre suona smette di fermarsi a ogni punto; in pausa riparte, col suo suono al posto
        di quello della ripresa. Premuto di nuovo, il suono conferma che il modo è già quello.
        """
        if self.stato == FINITO:
            suoni.suona("incontro_finito")
            return
        suoni.suona("dal_vivo_fino_a_fine_set")
        if self.stato == FERMO:
            self._avvia(FINO_A_FINE_SET, anticipo=suoni.attesa())
            return
        self.modo = FINO_A_FINE_SET
        if self.stato == PAUSA:
            self.riprendi(suono=None)

    def pausa(self):
        self.posizione = self.riproduttore.ferma() or 0.0
        self.timer.Stop()
        self.stato = PAUSA
        suoni.suona("dal_vivo_pausa")
        self._mostra(self._sentite())
        self._aggiorna_prosegui()

    def riprendi(self, suono="dal_vivo_ripresa"):
        """
        Riparte dal punto della pausa, dopo il suono della ripresa o quello del comando che l'ha
        chiesta. Se nel frattempo è cambiato il lato, o la velocità, ricompone.
        """
        if suono:
            suoni.suona(suono)
        t0 = self.resa.t0 if self.resa is not None else self._t0_ricordato
        self._ricomponi(self.posizione, t0, sempre=False)
        self.riproduttore.suona(self._per_la_cassa(), da=self.posizione, anticipo=suoni.attesa())
        self.stato = SUONA
        self._aggiorna_prosegui()
        self.timer.Start(BATTITO)

    def salta_riscaldamento(self):
        suoni.suona("riscaldamento_saltato")
        self.riproduttore.ferma()
        if self.modo == FINO_A_FINE_SET:
            self._prosegui_di_seguito(fresco=True)
        else:
            self._fine_tranche()

    def cambia_lato(self, event=None):
        """
        Alt+L: si ascolta dalla testata dell'altro giocatore. Se l'azione suona, il segmento si
        ricompone per il nuovo lato e riparte dal punto in cui era arrivato, dopo il suono del
        cambio; in pausa si ricompone alla ripresa; da fermi vale per la tranche che segue. Se nel
        campo c'è ancora la guida, ora dice il lato nuovo.
        """
        if self.stato == FINITO:
            suoni.suona("incontro_finito")
            return
        self.ascoltatore = "B" if self.ascoltatore == "A" else "A"
        suoni.suona("dal_vivo_cambio_lato")
        self.lato.SetLabel(self._etichetta_lato())
        self.pannello.Layout()
        if self._guida_in_vista:
            self._mostra_guida()
        if self.stato == SUONA:
            posizione = self.riproduttore.ferma() or 0.0
            self._ricomponi(posizione, self.resa.t0)
            self.riproduttore.suona(self._per_la_cassa(), da=posizione, anticipo=suoni.attesa())
        elif self.stato == PAUSA and self.resa is not None:
            self._t0_ricordato = self.resa.t0
            self.resa = None

    def cambia_velocita(self, passo):
        """
        Più o meno: la velocità di gioco cambia di un gradino. Il motore la usa dal momento che
        svolge dopo; se l'azione suona, pause e procedura già composte nel segmento si ripiegano
        appena il suono tace, e in pausa alla ripresa. Se nel campo c'è la guida, ora la dice.
        """
        nuova = max(modulo_impostazioni.VELOCITA_MINIMA, min(modulo_impostazioni.VELOCITA_MASSIMA, self.velocita + passo))
        if nuova == self.velocita:
            suoni.suona("dal_vivo_velocita_al_limite")
            return
        self.velocita = nuova
        suoni.suona("dal_vivo_piu_veloce" if passo > 0 else "dal_vivo_piu_lenta")
        self.SetTitle(testi.titolo_dal_vivo(self.nomi, nuova, self.differita))
        if self._guida_in_vista:
            self._mostra_guida()
        if self.stato == SUONA:
            self._da_ripiegare = True
            self._ripiega_nel_silenzio()

    def rileggi_guida(self):
        """F1: la guida dei tasti torna nel campo della cronaca, con il lato e la velocità di adesso; il fuoco resta sul pulsante."""
        suoni.suona("guida")
        self._mostra_guida()

    def esci(self, uscita):
        """
        Esc, Vai alla fine o il risultato: il suono della partita si ferma con la sua maniglia, e la
        finestra si chiude. A incontro finito Esc vale come il pulsante del risultato: la fine si è
        sentita e la cronaca nel campo la dice già, quindi la vista mostra il risultato, con l'esito
        e i punti allenamento, invece di dire che si è usciti senza vederla. Dal collaudo di gioco vale
        così anche Alt+V, Vai alla fine, che prima faceva sentire i guizzi di un salto che non c'è.
        """
        if self.uscita is not None:
            return
        if uscita in (CON_ESC, ALLA_FINE) and self.stato == FINITO:
            uscita = AL_RISULTATO
        self.uscita = uscita
        self.timer.Stop()
        self.riproduttore.ferma()
        # Le righe ancora in fila per il display non servono più.
        if self.annunci is not None:
            self.annunci.svuota()
        self.chiudi(wx.ID_CANCEL if uscita == CON_ESC else wx.ID_OK)

    def _tasto(self, event):
        """Esc esce, F1 rimette la guida nel campo, più e meno cambiano la velocità; con Alt o Ctrl il tasto va avanti, ai pulsanti e alla finestra."""
        codice = event.GetKeyCode()
        if event.AltDown() or event.ControlDown():
            event.Skip()
            return
        carattere = event.GetUnicodeKey()
        if codice == wx.WXK_ESCAPE:
            self.esci(CON_ESC)
        elif codice == wx.WXK_F1:
            self.rileggi_guida()
        elif codice in (wx.WXK_ADD, wx.WXK_NUMPAD_ADD) or carattere == ord("+"):
            self.cambia_velocita(1)
        elif codice in (wx.WXK_SUBTRACT, wx.WXK_NUMPAD_SUBTRACT) or carattere == ord("-"):
            self.cambia_velocita(-1)
        else:
            event.Skip()


def ascolta_in_differita(genitore, differita, seme, impostazioni, tuoi, cassa=None, orologio=None):
    """
    L'ascolto in differita di un incontro dei tuoi, di torneo o di sfida, tappa 12: il gemello rifatto
    dalle fotografie, con lo stesso seme, nella finestra dal vivo, dalla parte del tuo giocatore o della
    tua squadra. Restituisce come se n'è usciti e la velocità a cui si è arrivati, che il chiamante
    salva nelle impostazioni come fa l'amichevole.
    """
    impostazioni = modulo_impostazioni.valide(impostazioni)
    velocita = impostazioni["velocita_gioco"]
    gemello = gemello_da_differita(differita, seme, velocita)
    nomi = nomi_dell_incontro(gemello)
    dialogo = FinestraDalVivo(genitore, gemello, nomi, impostazioni["amichevole_livello"], velocita, impostazioni, cassa=cassa, orologio=orologio,
                              ascoltatore=ascoltatore_della_differita(differita, tuoi), differita=True)
    try:
        suoni.suona("differita_al_via")
        dialogo.ShowModal()
        return dialogo.uscita, dialogo.velocita
    finally:
        dialogo.Destroy()
