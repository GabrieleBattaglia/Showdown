"""
Test della finestra della tappa 11, decisione D31, con i dialoghi veri sul desktop nascosto del
conftest e i suoni soltanto registrati: la sala allenamento, con la spesa a mano e la sua conferma,
l'allenamento completo, Allena tutti, programma e intensità, gli avvisi con i loro suoni; i
contratti, con il rinnovo dentro e fuori dalla finestra, accettato, rifiutato e chiuso; la
buonuscita nello svincolo, la proposta di contratto nel dialogo dell'ingaggio e le voci del menu
nella guida. I messaggi di wx sono sostituiti da un registratore, che risponde come gli si dice.
"""

import datetime
import random

import pytest
import wx

import allenamento
import archivio
import contratti
import economia
import mercato
import mondo as modulo_mondo
import suoni
import testi
from costanti import FILE_MONDO, MESI_CONTRATTO_MIN, STIPENDIO_MINIMO
from gui import dialoghi
from gui.finestra import FinestraPrincipale
from modelli import Polisportiva
from mondo import Mondo
from utilita import adesso_utc

ORA = datetime.datetime(2027, 10, 9, 18, 0)


@pytest.fixture
def mondo():
    random.seed(23)
    m = Mondo()
    m.datetime_corrente_simulazione = ORA
    m.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=2)
    m.crea_giocatori_casuali(40, ORA)
    mia = Polisportiva("Club Della Sala", None, ORA - datetime.timedelta(days=300))
    mia.gloria = 140
    m.polisportive[mia.nome] = mia
    for gid in (3, 7, 12):
        g = m.giocatori[gid]
        g.infortunato, g.ritirato = False, False
        m._entra(mia, g)
        g.punti_allenamento = 150.5
    m.miapolisportiva_attiva = mia
    return m


class Messaggi(list):
    """I testi dei messaggi di wx, in ordine; risposta è quello che rispondono le domande."""

    def __init__(self):
        super().__init__()
        self.risposta = wx.YES

    def __call__(self, testo, *args, **kwargs):
        self.append(testo)
        return self.risposta


@pytest.fixture
def messaggi(monkeypatch):
    registro = Messaggi()
    monkeypatch.setattr(wx, "MessageBox", registro)
    return registro


@pytest.fixture
def sala(app_wx, mondo):
    dialogo = dialoghi.SalaAllenamento(None, mondo, mondo.miapolisportiva_attiva)
    yield dialogo
    dialogo.Destroy()


@pytest.fixture
def finestra(app_wx, mondo, monkeypatch):
    monkeypatch.setattr(wx.Dialog, "ShowModal", lambda self: wx.ID_CANCEL)
    f = FinestraPrincipale(mondo, archivio.CARICATO, ["Mondo caricato: prova."], Mondo.rapporto_vuoto(ORA), mondo.datetime_ultimo_run_reale)
    f.Show()
    yield f
    if f and not f.IsBeingDeleted():
        f.timer.Stop()
        f.Destroy()
    wx.Yield()


def _nome(g):
    return testi.nome_completo(g)


def _scegli(dialogo, g, caratteristica=None):
    """Sceglie l'allenando g nella sala, e la caratteristica se data, come farebbero le frecce."""
    dialogo.elenco.SetSelection(dialogo.allenandi.index(g))
    dialogo.al_allenando()
    if caratteristica is not None:
        dialogo.caratteristiche.SetSelection(allenamento.CARATTERISTICHE.index(caratteristica))
        dialogo.aggiorna_anteprima()


# La sala allenamento.

def test_la_sala_si_apre_con_gli_allenandi(sala, mondo):
    poli = mondo.miapolisportiva_attiva
    assert sala.GetTitle() == "Sala allenamento di Club Della Sala"
    assert sala.info.GetLabel() == "Club Della Sala: 3 allenandi, 451,5 punti allenamento da spendere in tutto."
    nomi = [_nome(g) for g in sala.allenandi]
    assert nomi == sorted(nomi, key=str.casefold) and {g.id for g in sala.allenandi} == set(poli.tesserati)
    assert [sala.elenco.GetString(i) for i in range(3)] == [testi.riga_allenando(g, mondo) for g in sala.allenandi]
    assert sala.elenco.GetSelection() == 0
    assert sala.caratteristiche.GetCount() == 24
    assert sala.caratteristiche.GetString(0).startswith("Precisione: ") and ", il prossimo punto costa " in sala.caratteristiche.GetString(0)
    # I punti partono da tutto il portafoglio, nella sua parte intera, e l'anteprima li segue.
    assert sala.punti.GetMax() == 150 and sala.punti.GetValue() == 150
    assert sala.anteprima.GetValue().startswith("Con 150 punti: precisione da ")
    g = sala.allenandi[0]
    assert sala.programma.GetStringSelection().casefold() == testi.indole(g).casefold()
    assert sala.intensita.GetStringSelection() == "Normale"


def test_le_lettere_della_sala_e_dei_contratti_non_si_ripetono(sala, mondo):
    dialogo = dialoghi.Contratti(None, mondo, mondo.miapolisportiva_attiva)
    try:
        for d in (sala, dialogo):
            testi_con_lettera = [c.GetLabel() for c in d.pannello.GetChildren() if "&" in c.GetLabel()]
            lettere = [t[t.index("&") + 1].lower() for t in testi_con_lettera]
            assert len(lettere) == len(set(lettere)), testi_con_lettera
        assert len([c for c in sala.pannello.GetChildren() if "&" in c.GetLabel()]) == 11
        assert len([c for c in dialogo.pannello.GetChildren() if "&" in c.GetLabel()]) == 7
    finally:
        dialogo.Destroy()


def test_la_spesa_a_mano_con_la_conferma(sala, mondo, messaggi, suonati):
    g = sala.allenandi[1]
    _scegli(sala, g, "chiusurasx")
    sala.punti.SetValue(120)
    sala.aggiorna_anteprima()
    anteprima = testi.anteprima_allenamento(g, "chiusurasx", 120)
    assert sala.anteprima.GetValue() == anteprima
    domanda = testi.domanda_spesa(g, "chiusurasx", 120)
    prima = g.chiusurasx_allenata
    messaggi.risposta = wx.NO
    sala.spendi()
    assert messaggi == [domanda] and suonati == ["domanda", "annullato"]
    assert g.chiusurasx_allenata == prima and g.punti_allenamento == 150.5
    messaggi.risposta = wx.YES
    valore_prima = g.indice_collettivo_valore
    sala.spendi()
    assert suonati[2:4] == ["domanda", "allenamento_fatto"]
    assert g.chiusurasx_allenata > prima and g.punti_allenamento == pytest.approx(30.5)
    assert messaggi[-1].startswith(f"{_nome(g)}: 120 punti spesi, valore da {testi.numero(valore_prima)} a ") and messaggi[-1].endswith(".")
    assert "\n" not in messaggi[-1]
    assert len(sala.esiti) == 1 and sala.esiti[0].startswith(f"{_nome(g)}: 120 punti spesi") and "; chiusura sinistra da " in sala.esiti[0]
    assert "spesa" in g.diario[0] and g.diario[0]["punti"] == 120
    # La sala tiene il posto: lo stesso allenando, la stessa caratteristica, e i punti entro il portafoglio nuovo.
    assert sala.elenco.GetSelection() == 1 and sala.caratteristiche.GetSelection() == allenamento.CARATTERISTICHE.index("chiusurasx")
    assert sala.punti.GetMax() == 30 and sala.punti.GetValue() == 30
    assert sala.info.GetLabel() == "Club Della Sala: 3 allenandi, 331,5 punti allenamento da spendere in tutto."
    assert mondo.miapolisportiva_attiva.indicecollettivotesserati == pytest.approx(sum(x.indice_collettivo_valore for x in sala.allenandi))


def test_l_allenamento_completo_spende_anche_le_frazioni(sala, messaggi, suonati):
    g = sala.allenandi[0]
    _scegli(sala, g)
    sala.completo()
    assert g.punti_allenamento == 0.0
    assert suonati[0] == "allenamento_completo" and "domanda" not in suonati
    assert messaggi[-1].startswith(f"{_nome(g)}: 150,5 punti spesi, valore da ")
    assert sala.esiti and sala.esiti[0].startswith(f"{_nome(g)}: 150,5 punti spesi")
    assert sala.punti.GetMax() == 0


def test_allena_tutti_con_la_conferma(sala, mondo, messaggi, suonati):
    fermo, primo, secondo = sala.allenandi
    fermo.infortunato = True
    fermo.infortunio_fine_datetime = ORA + datetime.timedelta(days=10)
    fermo.infortunio_sede = "caviglia"
    messaggi.risposta = wx.NO
    sala.tutti()
    domanda = testi.domanda_allena_tutti([primo, secondo])
    assert messaggi == [domanda] and domanda == "Spendere 301 punti di 2 allenandi, ciascuno secondo il suo programma?"
    assert primo.punti_allenamento == 150.5
    messaggi.risposta = wx.YES
    sala.tutti()
    assert primo.punti_allenamento == 0.0 and secondo.punti_allenamento == 0.0 and fermo.punti_allenamento == 150.5
    righe = messaggi[-1].splitlines()
    assert len(righe) == 2 and righe[0].startswith(f"{_nome(primo)}: 150,5 punti spesi") and righe[1].startswith(f"{_nome(secondo)}: 150,5 punti spesi")
    assert "allenati_tutti" in suonati and len(sala.esiti) == 2
    # L'infortunato lo dice l'elenco, e un'altra volta Allena tutti non trova nessuno con un punto.
    assert sala.elenco.GetString(0).endswith(", non si allena")
    sala.tutti()
    assert suonati[-1] == "punti_insufficienti" and messaggi[-1] == testi.nessuno_da_allenare(mondo.miapolisportiva_attiva)


def test_la_classe_salita_suona_in_coda_e_va_nel_diario(sala, messaggi, suonati):
    g = sala.allenandi[2]
    g.punti_allenamento = 20_000.0
    classe_prima = testi.codice_classe(g)
    _scegli(sala, g)
    sala.completo()
    assert testi.codice_classe(g) != classe_prima
    assert suonati == ["allenamento_completo", "classe_salita"]
    assert ", sale alla classe " in messaggi[-1]
    assert any(voce.get("testo", "").startswith("Sale alla classe ") for voce in g.diario)


def test_programma_e_intensita_valgono_subito(sala, suonati):
    g = sala.allenandi[0]
    _scegli(sala, g)
    altra = next(k for k in sala.indoli if k != g.programma)
    sala.programma.SetSelection(sala.indoli.index(altra))
    sala.al_programma()
    assert g.programma == altra and suonati == ["programma_cambiato"]
    sala.intensita.SetSelection(sala.livelli.index("intensa"))
    sala.all_intensita()
    assert g.intensita == "intensa" and suonati == ["programma_cambiato", "intensita_cambiata"]
    assert sala.elenco.GetString(0).endswith(", intensità intensa")
    # Riscegliere lo stesso valore non suona.
    sala.all_intensita()
    assert suonati == ["programma_cambiato", "intensita_cambiata"]
    assert sala.cambi() == [testi.cambio_in_sala(g)]
    assert sala.cambi()[0].endswith(", intensità intensa.")


def test_gli_avvisi_della_sala_con_i_loro_suoni(sala, mondo, messaggi, suonati):
    g = sala.allenandi[0]
    # La caratteristica al massimo.
    g.lungolineasx_allenata = 40.0 - g.lungolineasx_base
    sala.aggiorna()
    _scegli(sala, g, "lungolineasx")
    assert sala.caratteristiche.GetStringSelection().endswith(", al massimo")
    assert sala.anteprima.GetValue().endswith("è al massimo.")
    sala.spendi()
    assert suonati == ["caratteristica_al_massimo"] and messaggi[-1] == testi.caratteristica_al_massimo(g, "lungolineasx")
    # La cifra zero.
    _scegli(sala, g, "difesa")
    sala.punti.SetValue(0)
    sala.spendi()
    assert suonati[-1] == "punti_insufficienti" and messaggi[-1].startswith("Scegli quanti punti spendere")
    # Il portafoglio sotto un punto.
    g.punti_allenamento = 0.4
    sala.aggiorna()
    sala.spendi()
    assert suonati[-1] == "punti_insufficienti" and messaggi[-1] == testi.senza_punti(g) and "0,4" in messaggi[-1]
    # L'allenando infortunato, per la spesa a mano e per quella completa.
    g.punti_allenamento = 50.0
    g.infortunato, g.infortunio_sede = True, "ginocchio"
    g.infortunio_fine_datetime = ORA + datetime.timedelta(days=5)
    sala.aggiorna()
    assert sala.anteprima.GetValue() == testi.allenando_fermo(g)
    sala.spendi()
    assert suonati[-1] == "allenando_infortunato" and messaggi[-1] == testi.allenando_fermo(g)
    sala.completo()
    assert suonati[-1] == "allenando_infortunato"
    assert not any(s in suonati for s in ("allenamento_fatto", "allenamento_completo", "domanda"))
    assert g.punti_allenamento == 50.0


def test_la_sala_nella_finestra(finestra, mondo, messaggi, monkeypatch, cartella_di_prova, suonati):
    poli = mondo.miapolisportiva_attiva

    def una_spesa_e_un_cambio(self):
        self.completo()
        self.intensita.SetSelection(self.livelli.index("leggera"))
        self.all_intensita()
        return wx.ID_CANCEL

    monkeypatch.setattr(dialoghi.SalaAllenamento, "ShowModal", una_spesa_e_un_cambio)
    finestra.sala_allenamento()
    righe = finestra.vista.GetValue().splitlines()
    assert righe[0] == "Sala allenamento di Club Della Sala: 1 spesa e 1 cambio di programma o d'intensità."
    assert righe[1].startswith(f"{_nome(sorted((mondo.giocatori[i] for i in poli.tesserati), key=lambda x: _nome(x).casefold())[0])}: 150,5 punti spesi")
    assert righe[2].endswith(", intensità leggera.")
    assert suonati[0] == "dialogo_sala_allenamento" and suonati[-1] == "lavoro_concluso"
    assert finestra.ultimo_evento == "sala: 1 spesa"
    assert (cartella_di_prova / FILE_MONDO).exists()
    # Senza niente di fatto la vista lo dice e il mondo non si salva.
    (cartella_di_prova / FILE_MONDO).unlink()
    monkeypatch.setattr(dialoghi.SalaAllenamento, "ShowModal", lambda self: wx.ID_CANCEL)
    finestra.sala_allenamento()
    assert finestra.vista.GetValue() == "Sala allenamento di Club Della Sala: nessuna spesa."
    assert not (cartella_di_prova / FILE_MONDO).exists()


def test_senza_tesserati_la_sala_e_i_contratti_lo_dicono(finestra, mondo, suonati):
    poli = mondo.miapolisportiva_attiva
    for gid in list(poli.tesserati):
        mondo._lascia(poli, mondo.giocatori[gid])
    finestra.sala_allenamento()
    assert finestra.vista.GetValue() == "Club Della Sala non ha tesserati da allenare." and suonati[-1] == "rosa_vuota"
    finestra.contratti()
    assert finestra.vista.GetValue() == "Club Della Sala non ha tesserati con un contratto." and suonati[-1] == "rosa_vuota"


# I contratti e i rinnovi.

@pytest.fixture
def contratti_aperti(app_wx, mondo):
    dialogo = dialoghi.Contratti(None, mondo, mondo.miapolisportiva_attiva)
    yield dialogo
    dialogo.Destroy()


def _in_finestra(mondo, g, giorni=0):
    """Porta la data del mondo dentro la finestra del rinnovo di g, più tanti giorni."""
    mondo.datetime_corrente_simulazione = contratti.inizio_finestra(g).replace(hour=18) + datetime.timedelta(days=giorni)


def test_i_contratti_si_aprono_dal_primo_che_scade(contratti_aperti, mondo):
    d = contratti_aperti
    poli = mondo.miapolisportiva_attiva
    scadenze = [g.contratto_scadenza for g in d.rosa]
    assert scadenze == sorted(scadenze) and len(d.rosa) == 3
    assert d.info.GetLabel() == testi.testata_contratti(poli, mondo)
    assert [d.elenco.GetString(i) for i in range(3)] == [testi.riga_contratto(g, poli, mondo) for g in d.rosa]
    g = d.rosa[0]
    mesi = contratti.durata_proposta(g)
    assert d.durata.GetValue() == mesi and d.stipendio.GetValue() == contratti.richiesta_rinnovo(g, poli, mesi)
    assert d.durata.GetMin() == MESI_CONTRATTO_MIN
    # Fuori dalla finestra l'esito previsto dice da quando si può proporre.
    assert d.previsto.GetValue() == mondo.problema_rinnovo(poli, g)


def test_il_rinnovo_fuori_dalla_finestra(contratti_aperti, mondo, messaggi, suonati):
    d = contratti_aperti
    g = d.rosa[0]
    d.proponi()
    assert suonati == ["rinnovo_fuori_finestra"]
    assert messaggi == [mondo.problema_rinnovo(mondo.miapolisportiva_attiva, g)] and "il rinnovo si può proporre dal" in messaggi[0]
    assert g.proposte_rinnovo == 0


def test_il_rinnovo_accettato(contratti_aperti, mondo, messaggi, suonati, monkeypatch):
    d = contratti_aperti
    poli = mondo.miapolisportiva_attiva
    g = d.rosa[0]
    _in_finestra(mondo, g)
    d.aggiorna()
    d.al_tesserato()
    assert d.previsto.GetValue().startswith("Accetterebbe al ") and ", in scadenza: chiede " in d.elenco.GetString(0)
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: True)
    stipendio, mesi = d.stipendio.GetValue(), d.durata.GetValue()
    scadenza = g.contratto_scadenza
    d.proponi()
    assert messaggi[0] == testi.domanda_rinnovo(g, poli, stipendio, mesi)
    assert suonati == ["domanda", "rinnovo_accettato"]
    assert g.rinnovo_stipendio == stipendio and g.rinnovo_scadenza == contratti.scadenza_dopo(scadenza, mesi)
    assert messaggi[-1].startswith(f"{_nome(g)} ha accettato: dal ") and d.esiti == [messaggi[-1]]
    assert ", rinnovato dal " in d.elenco.GetString(0)
    d.proponi()
    assert suonati[-1] == "rinnovo_gia_concordato" and messaggi[-1].startswith(f"{_nome(g)} ha già rinnovato")


def test_il_rinnovo_rifiutato_tre_volte_si_chiude(contratti_aperti, mondo, messaggi, suonati, monkeypatch):
    d = contratti_aperti
    g = d.rosa[0]
    _in_finestra(mondo, g)
    d.aggiorna()
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: False)
    d.proponi()
    assert suonati == ["domanda", "rinnovo_rifiutato"] and "2 proposte rimaste, una al giorno." in messaggi[-1]
    # Lo stesso giorno non si propone di nuovo.
    d.proponi()
    assert suonati[-1] == "rinnovo_gia_proposto_oggi" and "al massimo una al giorno" in messaggi[-1]
    _in_finestra(mondo, g, 1)
    d.aggiorna()
    d.proponi()
    assert suonati[-1] == "rinnovo_rifiutato" and "1 proposta rimasta, una al giorno." in messaggi[-1]
    _in_finestra(mondo, g, 2)
    d.aggiorna()
    d.proponi()
    assert suonati[-1] == "rinnovo_chiuso" and "Non vuole più trattare" in messaggi[-1]
    assert ", non tratta più: " in d.elenco.GetString(0)
    _in_finestra(mondo, g, 3)
    d.aggiorna()
    d.proponi()
    assert suonati[-1] == "rinnovo_senza_proposte" and "ha già rifiutato tre proposte" in messaggi[-1]
    assert g.proposte_rinnovo == 3 and len(d.esiti) == 3


def test_lo_stipendio_sotto_il_minimo_si_corregge(contratti_aperti, mondo, messaggi, suonati):
    d = contratti_aperti
    g = d.rosa[0]
    _in_finestra(mondo, g)
    d.aggiorna()
    d.stipendio.SetValue(STIPENDIO_MINIMO - 1)
    d.proponi()
    assert suonati == ["campo_da_correggere"] and messaggi[-1].startswith("Lo stipendio deve essere di almeno ")
    assert g.proposte_rinnovo == 0


def test_il_tic_della_probabilita_del_rinnovo(contratti_aperti, mondo, suonati):
    d = contratti_aperti
    g = d.rosa[0]
    poli = mondo.miapolisportiva_attiva
    _in_finestra(mondo, g)
    d.aggiorna()
    d.stipendio.SetValue(10_000)
    d.tic_della_probabilita()
    assert suonati == ["probabilita_rinnovo"]
    percentuale = contratti.probabilita_rinnovo(g, poli, 10_000, d.durata.GetValue())
    assert suonati.dettagli[0]["semitoni"] == pytest.approx(suoni.probabilita_in_semitoni(percentuale)) and suonati.dettagli[0]["semitoni"] > 0
    # Il tic arriva quando ci si ferma, e soltanto se la proposta oggi si può fare.
    d.al_ritocco(wx.CommandEvent())
    ciclo = wx.GUIEventLoop()
    wx.CallLater(1000, ciclo.Exit)
    ciclo.Run()
    assert suonati == ["probabilita_rinnovo", "probabilita_rinnovo"]
    mondo.datetime_corrente_simulazione = ORA
    d.aggiorna()
    d.al_ritocco(wx.CommandEvent())
    ciclo = wx.GUIEventLoop()
    wx.CallLater(1000, ciclo.Exit)
    ciclo.Run()
    assert suonati == ["probabilita_rinnovo", "probabilita_rinnovo"]


def test_i_contratti_nella_finestra(finestra, mondo, messaggi, monkeypatch, cartella_di_prova, suonati):
    poli = mondo.miapolisportiva_attiva
    primo = min((mondo.giocatori[gid] for gid in poli.tesserati), key=lambda g: (g.contratto_scadenza, _nome(g).casefold()))
    _in_finestra(mondo, primo)
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: True)

    def una_proposta(self):
        self.proponi()
        return wx.ID_CANCEL

    monkeypatch.setattr(dialoghi.Contratti, "ShowModal", una_proposta)
    finestra.contratti()
    righe = finestra.vista.GetValue().splitlines()
    assert righe[0] == "Contratti di Club Della Sala: 1 proposta." and righe[1].startswith(f"{_nome(primo)} ha accettato")
    assert suonati[0] == "dialogo_contratti" and suonati[-1] == "lavoro_concluso"
    assert finestra.ultimo_evento == "contratti: 1 proposta"
    assert (cartella_di_prova / FILE_MONDO).exists()


# Lo svincolo, l'ingaggio e la guida.

def test_lo_svincolo_dice_la_buonuscita(finestra, mondo, messaggi, monkeypatch, suonati):
    poli = mondo.miapolisportiva_attiva
    g = mondo.giocatori[3]
    buonuscita = contratti.buonuscita(g, mondo.datetime_corrente_simulazione)
    assert buonuscita > 0

    def scegli(self):
        self.elenco.SetSelection(self.visibili.index(g))
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.SceltaGiocatore, "ShowModal", scegli)
    # Con la cassa che non basta, l'avviso con il suono della cassa insufficiente, e niente svincolo.
    poli.cassa = buonuscita - 1
    finestra.svincola()
    assert suonati[-1] == "cassa_insufficiente" and "buonuscita" in finestra.vista.GetValue()
    assert g.id in poli.tesserati
    poli.cassa = 20_000
    finestra.svincola()
    assert f"la buonuscita è di {testi.euro(buonuscita)}" in messaggi[-1] and messaggi[-1].startswith(f"Svincolare {_nome(g)}? ")
    assert g.id not in poli.tesserati and poli.cassa == 20_000 - buonuscita
    assert suonati[-1] == "tesserato_svincolato"


def test_il_dialogo_dell_ingaggio_comincia_con_la_proposta(app_wx, mondo, messaggi, monkeypatch, suonati):
    poli = mondo.miapolisportiva_attiva
    spiegazioni = []
    originale = dialoghi.Cifra.__init__

    def registra(self, genitore, titolo, spiegazione, *args, **kwargs):
        spiegazioni.append((titolo, spiegazione))
        originale(self, genitore, titolo, spiegazione, *args, **kwargs)

    monkeypatch.setattr(dialoghi.Cifra, "__init__", registra)
    monkeypatch.setattr(dialoghi.Cifra, "ShowModal", lambda self: wx.ID_CANCEL)
    dialogo = dialoghi.Mercato(None, mondo, poli)
    try:
        candidato = next(c for c in mercato.candidati(mondo, poli, [], "liberi", 0, "valore") if c.tipo == mercato.LIBERO)
        dialogo._ingaggio(candidato)
    finally:
        dialogo.Destroy()
    titolo, spiegazione = spiegazioni[0]
    g = candidato.giocatore
    assert titolo == f"Ingaggio di {_nome(g)}"
    assert spiegazione.startswith(testi.proposta_di_contratto(g, mondo) + " Per firmare, ")
    assert f"chiede {testi.euro(candidato.costo)} d'ingaggio" in spiegazione
    assert spiegazione.startswith(f"Propone un contratto di {contratti.durata_proposta(g)} mesi")
    assert f"a {testi.euro(economia.stipendio(g))} al mese fissi." in spiegazione


def test_le_voci_del_menu_nella_guida(finestra):
    voci = {voce[0]: (voce[1], voce[2]) for _t, elenco in finestra.voci_menu() for voce in filter(None, elenco)}
    assert voci["Sala &allenamento..."] == ("Ctrl+Shift+L", finestra.sala_allenamento)
    assert voci["Contratti e &rinnovi..."] == ("Ctrl+Shift+K", finestra.contratti)
    guida = testi.guida(finestra.voci_guida())
    assert "Sala allenamento, Ctrl+Maiusc+L" in guida and "Contratti e rinnovi, Ctrl+Maiusc+K" in guida
    polisportive = next(elenco for titolo, elenco in finestra.voci_menu() if titolo == "&Polisportive")
    testi_voci = [voce[0] for voce in polisportive if voce]
    assert testi_voci.index("Sala &allenamento...") == testi_voci.index("Pa&ga gli arretrati...") + 1
