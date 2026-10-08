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
risultato; Esc esce senza svelarlo, e la vista principale dice dove leggerlo, decisione D30. Più
e meno cambiano al volo la velocità di gioco: il motore la usa dal momento seguente, e pause e
procedura già composte, come la pausa dopo il punto, si ripiegano alla velocità nuova appena il
suono tace, così il cambio non si sente. A fine incontro il pulsante lo dice e porta al risultato.
Con Tab e Maiusc+Tab si va nel campo della cronaca, dove si legge la tranche appena ascoltata al
livello scelto: il campo cambia mentre il fuoco resta sul pulsante, perciò NVDA non lo legge da solo
e non copre i suoni. Prima della prima tranche il campo tiene la guida dei tasti, che dice il lato e
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
"""

import time

import wx

import impostazioni as modulo_impostazioni
import partita_sonora as ps
import suoni
import testi
from gui import aspetto
from gui.dialoghi import _Dialogo

# Ogni quanti millesimi la finestra guarda a che punto è il suono.
BATTITO = 50
# Gli stati della finestra e i due modi di ascoltare.
FERMO = "fermo"
SUONA = "suona"
PAUSA = "pausa"
FINITO = "finito"
UN_PUNTO = "punto"
FINO_A_FINE_SET = "set"
# Come la finestra si è chiusa: con Esc, con Vai alla fine, o dal risultato a incontro finito.
CON_ESC = "esc"
ALLA_FINE = "fine"
AL_RISULTATO = "risultato"


class FinestraDalVivo(_Dialogo):
    """
    La partita dal vivo: gemello è l'incontro ancora da giocare, con lo stesso seme di quello
    registrato; nomi e livello sono quelli della cronaca, velocita quella di gioco delle impostazioni,
    da cui viene anche il volume della partita; senza impostazioni vale il volume predefinito.
    Alla chiusura uscita dice come si è chiusa, e velocita la velocità a cui si è arrivati.
    """

    def __init__(self, genitore, gemello, nomi, livello, velocita, impostazioni=None, cassa=None, orologio=None):
        super().__init__(genitore, testi.titolo_dal_vivo(nomi, velocita))
        self.nomi = nomi
        self.livello = livello
        self.velocita = velocita
        self.impostazioni = impostazioni
        self.volume = modulo_impostazioni.valide(impostazioni)["volume_partita"]
        self.set_al_meglio = gemello.formato.set_al_meglio
        self.cronologia = ps.Cronologia(gemello)
        self.riproduttore = ps.Riproduttore(cassa, orologio or time.monotonic)
        self.ascoltatore = "A"
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

    def _scrivi(self, testo):
        """Il testo nel campo della cronaca, con lo stile scelto e il cursore in cima, senza spostare il fuoco dal pulsante."""
        self.cronaca.ChangeValue(testo)
        if self.impostazioni:
            aspetto.ridai_stile(self.cronaca, self.impostazioni)
        self.cronaca.SetInsertionPoint(0)

    def _testo_della_guida(self):
        return testi.guida_dal_vivo(self.nomi, self.ascoltatore, self.set_al_meglio, self.velocita)

    def _mostra_guida(self):
        """La guida dei tasti nel campo, con il lato e la velocità di adesso."""
        self._scrivi(self._testo_della_guida())
        self._guida_in_vista = True

    def _mostra(self, voci):
        """La cronaca delle voci nel campo, al livello scelto, al posto della guida o della tranche di prima."""
        righe = testi.righe_degli_eventi(voci, self.nomi, self.livello)
        self._scrivi("\n".join(righe) or "In questo tratto la cronaca, a questo livello, non ha frasi.")
        self._guida_in_vista = False

    def _sentite(self):
        """Le voci della tranche fin dove il suono è arrivato."""
        istante = self.resa.istante(self.posizione) if self.resa is not None else float("inf")
        return [voce for voce in self.tranche if voce[0].t <= istante + ps.TOLLERANZA]

    # Il suono.

    def _componi(self, da, anticipo=None):
        self.resa = ps.componi(self.segmento.eventi, self.ascoltatore, da=da, fine=self.segmento.fine, anticipo=anticipo, pieghe=self._pieghe)

    def _per_la_cassa(self):
        return ps.per_la_cassa(self.resa.buffer, self.volume)

    def _suona_segmento(self, segmento, fresco, sovrapponi=False, anticipo=0.0):
        """
        Compone il segmento e lo fa partire, dopo anticipo secondi di silenzio. Da fresco comincia
        dalla ripresa del gioco, col silenzio in testa accorciato; altrimenti prosegue dalla fine
        del segmento di prima, pause comprese. La procedura che il motore ha svolto a un'altra
        velocità si ripiega subito a quella di adesso.
        """
        da = segmento.inizio if fresco or self.segmento is None else self.segmento.fine
        self.segmento = segmento
        self._pieghe = ps.ripiega(segmento.procedure, self.velocita)
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
        pieghe = ps.ripiega(self.segmento.procedure, self.velocita, self._pieghe, da=adesso)
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
        if ps.ripiega(self.segmento.procedure, self.velocita, self._pieghe, da=adesso) == self._pieghe:
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
        self._suona_segmento(segmento, fresco=True, anticipo=anticipo)
        self.stato = SUONA
        self._aggiorna_prosegui()
        self.timer.Start(BATTITO)

    def _prosegui_di_seguito(self, fresco=False):
        """
        Fino a fine set: il segmento che segue parte appena finisce quello di prima, la cui coda
        finisce di suonare. Se prima della ripresa del gioco c'è una pausa lunga, time-out, cambio
        campo o inizio del set, non si sente: resta la pausa di sempre dopo il punto, in silenzio, e
        il segmento comincia dalla ripresa, come con Prosegui; la pausa lunga è nella cronaca.
        """
        segmento = self.cronologia.prossimo(self.velocita)
        if segmento is None:
            self._fine_tranche()
            return
        self.tranche.extend(segmento.voci)
        if not fresco and segmento.pausa_lunga:
            attesa = segmento.attesa_prima(self.segmento.fine, self.velocita)
            self._suona_segmento(segmento, fresco=True, sovrapponi=True, anticipo=attesa)
        else:
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
        passa al segmento che segue fino a fine set, o chiude la tranche.
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
        self.SetTitle(testi.titolo_dal_vivo(self.nomi, nuova))
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
        """Esc, Vai alla fine o il risultato: il suono della partita si ferma con la sua maniglia, e la finestra si chiude."""
        if self.uscita is not None:
            return
        self.uscita = uscita
        self.timer.Stop()
        self.riproduttore.ferma()
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
