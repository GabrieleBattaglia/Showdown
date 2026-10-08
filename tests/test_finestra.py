"""
Test della finestra e dei dialoghi, sul desktop nascosto del conftest: ogni voce dei menu, la
barra di stato, il salvataggio, la chiusura con il riepilogo, la scelta del giocatore, la
ricerca, l'aspetto e l'invito al caffè. Le finestre modali vengono sostituite, perché una prova
che aspetta un tasto non finirebbe mai. Dal 2026-10-07 anche i suoni, che il conftest registra
senza suonarli: le prove in fondo controllano che i comandi facciano sentire il loro evento.
"""

import datetime
import json
import random
from pathlib import Path

import pytest
import wx

import archivio
import impostazioni
import mondo as modulo_mondo
import ricerca
import suoni
import testi
from costanti import FILE_MONDO
from gui import dialoghi
from gui.finestra import FinestraPrincipale
from modelli import Polisportiva
from mondo import Mondo
from utilita import adesso, adesso_utc


@pytest.fixture
def mondo():
    random.seed(11)
    ora = adesso()
    m = Mondo()
    m.datetime_corrente_simulazione = ora
    m.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=2)
    m.crea_giocatori_casuali(30, ora)
    mia = Polisportiva("Club Di Prova", "segreta", ora)
    m.polisportive[mia.nome] = mia
    for gid in (2, 5):
        mia.aggiungi_tesserato(gid, m.giocatori[gid].indice_collettivo_valore)
        m.giocatori[gid].appartenenza = mia.nome
    m.miapolisportiva_attiva = mia
    return m


@pytest.fixture
def finestra(app_wx, mondo, monkeypatch):
    # Nessuna finestra modale vera, neppure un messaggio: la prova non avrebbe nessuno che le chiude.
    monkeypatch.setattr(wx.Dialog, "ShowModal", lambda self: wx.ID_CANCEL)
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.NO)
    f = FinestraPrincipale(mondo, archivio.CARICATO, ["Mondo caricato: prova."], Mondo.rapporto_vuoto(adesso()), mondo.datetime_ultimo_run_reale)
    f.Show()
    yield f
    if f and not f.IsBeingDeleted():
        f.timer.Stop()
        f.Destroy()
    wx.Yield()


def test_apertura_e_barra(finestra):
    assert finestra.vista.GetValue().startswith("MESS, Manageriale e Simulatore Showdown, versione")
    assert "Mondo caricato: prova." in finestra.vista.GetValue()
    righe = finestra.barra.GetValue().splitlines()
    assert len(righe) == 4 and all(len(r) <= 40 for r in righe)
    assert righe[1].startswith("Club Di Prova g")


def test_ogni_voce_dei_menu_che_mostra_un_testo(finestra):
    con_dialogo = {finestra.scheda_giocatore, finestra.diario_giocatore, finestra.cerca, finestra.cambia_aspetto, finestra.cambia_conservazione,
                   finestra.caffe, finestra.esci, finestra.vai_alla_vista, finestra.vai_alla_barra, finestra.nuova_polisportiva,
                   finestra.cambia_polisportiva, finestra.mercato, finestra.svincola, finestra.password_polisportiva, finestra.chiudi_polisportiva,
                   finestra.cambia_effetti, finestra.amichevole}
    provate = 0
    for _titolo, voci in finestra.voci_menu():
        for voce in filter(None, voci):
            testo, _tasto, comando = voce
            if comando in con_dialogo:
                continue
            finestra.vista.ChangeValue("")
            finestra._esegui(comando)
            assert finestra.vista.GetValue(), testo
            assert "\n\n" not in finestra.vista.GetValue(), testo
            provate += 1
    # Le voci delle partite, senza un'amichevole nella sessione, lo dicono nella vista.
    assert provate == 25
    assert finestra.comandi == 25


def test_i_menu_hanno_tasti_e_lettere_non_ripetuti(finestra):
    tasti = [tasto for _t, voci in finestra.voci_menu() for voce in filter(None, voci) if (tasto := voce[1])]
    assert len(tasti) == len(set(tasti))
    for _titolo, voci in finestra.voci_menu():
        lettere = [voce[0][voce[0].index("&") + 1].lower() for voce in filter(None, voci)]
        assert len(lettere) == len(set(lettere)), lettere
    guida = testi.guida(finestra.voci_guida())
    assert "Scheda del giocatore, Ctrl+G" in guida and "Ctrl+Maiusc+N" in guida and "&" not in guida


def test_salva(finestra, cartella_di_prova):
    finestra.salva()
    assert finestra.vista.GetValue().startswith("Mondo salvato: 30 giocatori e 1 polisportiva.")
    assert finestra.ultimo_evento.startswith("salvato alle ")
    assert archivio.leggi(cartella_di_prova / FILE_MONDO)["mondo"]["polisportiva_attiva"] == "Club Di Prova"


def test_chiusura_salva_e_riassume(finestra, cartella_di_prova, monkeypatch):
    riepiloghi = []
    originale = dialoghi.Lettura.__init__

    def registra(self, genitore, titolo, testo, *args, **kwargs):
        riepiloghi.append((titolo, testo))
        originale(self, genitore, titolo, testo, *args, **kwargs)

    monkeypatch.setattr(dialoghi.Lettura, "__init__", registra)
    finestra.Close()
    wx.Yield()
    assert (cartella_di_prova / FILE_MONDO).exists()
    titolo, testo = riepiloghi[0]
    assert titolo == "Fine sessione"
    assert testo.startswith("Sessione di ") and "Mondo salvato:" in testo and testo.endswith("Arrivederci!")
    assert "caffè" not in testo
    assert "Nella sessione il mondo" not in testo


def test_il_timer_fa_avanzare_il_mondo(finestra, cartella_di_prova, monkeypatch):
    finestra.vista.ChangeValue("Il testo che si sta leggendo.")
    mondo = finestra.mondo
    # Una data a metà mese: un primo del mese nei due giorni avrebbe il suo avviso nella barra.
    mondo.datetime_corrente_simulazione = data_prima = datetime.datetime(2026, 10, 10, 12, 0)
    mondo.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=17)
    # Con un dialogo aperto il mondo aspetta.
    finestra._modali = 1
    finestra._al_minuto(None)
    assert mondo.datetime_corrente_simulazione == data_prima
    finestra._modali = 0
    finestra._al_minuto(None)
    assert mondo.datetime_corrente_simulazione == data_prima + datetime.timedelta(days=2)
    assert finestra.ultimo_evento == "mondo avanzato di 2 giorni"
    assert finestra.rapporto["giorni"] == finestra.rapporto_sessione["giorni"] == 2
    assert finestra.vista.GetValue() == "Il testo che si sta leggendo."
    assert archivio.leggi(cartella_di_prova / FILE_MONDO)["mondo"]["data_simulata"] == mondo.datetime_corrente_simulazione.isoformat()
    finestra._al_minuto(None)
    assert finestra.rapporto_sessione["giorni"] == 2
    riepiloghi = []
    originale = dialoghi.Lettura.__init__

    def registra(self, genitore, titolo, testo, *args, **kwargs):
        riepiloghi.append(testo)
        originale(self, genitore, titolo, testo, *args, **kwargs)

    monkeypatch.setattr(dialoghi.Lettura, "__init__", registra)
    finestra.Close()
    wx.Yield()
    assert "Nella sessione il mondo è andato avanti di 2 giorni simulati." in riepiloghi[0]


def test_diario_del_giocatore_e_della_polisportiva(finestra, monkeypatch):
    def scegli(self):
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.SceltaGiocatore, "ShowModal", scegli)
    finestra.diario_giocatore()
    g = finestra.mondo.giocatori[1]
    assert finestra.vista.GetValue().startswith(f"Diario di {g.nome} {g.cognome}, ID 1: 1 voce, dalla più recente.")
    assert finestra.ultimo_evento == f"diario di {g.nome} {g.cognome}"
    finestra.diario_polisportiva()
    assert finestra.vista.GetValue().startswith("Diario di Club Di Prova: 1 voce, dalla più recente.")
    assert finestra.vista.GetValue().endswith(": Fondata.")


def test_cambia_conservazione(finestra, monkeypatch):
    def scegli(self):
        assert self.giocatori.GetValue() == 0
        self.giocatori.SetValue(60)
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.Conservazione, "ShowModal", scegli)
    finestra.cambia_conservazione()
    assert finestra.mondo.conservazione_diari == {"giocatori": 60, "polisportive": 0}
    assert finestra.vista.GetValue().startswith("Le voci dei diari dei giocatori si conservano per 60 giorni simulati, quelle delle polisportive per sempre.")


def test_scelta_del_giocatore(app_wx, mondo):
    dialogo = dialoghi.SceltaGiocatore(None, mondo)
    try:
        assert dialogo.elenco.GetCount() == 30
        dialogo.campo.ChangeValue("2")
        dialogo.filtra()
        assert dialogo.visibili[0].id == 2
        assert all(str(g.id).startswith("2") for g in dialogo.visibili)
        cognome = mondo.giocatori[7].cognome
        dialogo.campo.ChangeValue(cognome.lower())
        dialogo.filtra()
        assert mondo.giocatori[7] in dialogo.visibili
        dialogo.elenco.SetSelection(dialogo.visibili.index(mondo.giocatori[7]))
        dialogo.conferma()
        assert dialogo.scelto is mondo.giocatori[7]
        assert dialogo.GetReturnCode() == wx.ID_OK
        dialogo.campo.ChangeValue("nessuno si chiama così")
        dialogo.filtra()
        assert dialogo.elenco.GetCount() == 0
    finally:
        dialogo.Destroy()


def test_ricerca(app_wx, monkeypatch):
    avvisi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: avvisi.append(testo))
    dialogo = dialoghi.Ricerca(None)
    try:
        dialogo.valore.ChangeValue("cento")
        dialogo.conferma()
        assert dialogo.risultato is None and avvisi == ["Il valore deve essere un numero, per esempio 150 o 12,5."]
        dialogo.valore.ChangeValue("150,5")
        dialogo.conferma()
        assert dialogo.risultato == ("attivi", "valore", "maggiore", 150.5, "i giocatori in attività, valore maggiore di 150,5")
        dialogo.criterio.SetSelection([chiave for chiave, *_resto in ricerca.CRITERI].index("ipovedente"))
        dialogo.al_criterio()
        assert not dialogo.valore.IsEnabled()
        dialogo.condizione.SetSelection(1)
        dialogo.conferma()
        assert dialogo.risultato[1:4] == ("ipovedente", "no", None)
    finally:
        dialogo.Destroy()
    filtro = dialoghi.Ricerca(None, con_ambito=False, titolo="Aggiungi un filtro", pulsante="&Aggiungi")
    try:
        assert filtro.ambito is None
        filtro.criterio.SetSelection([chiave for chiave, *_resto in ricerca.CRITERI].index("sesso"))
        filtro.al_criterio()
        assert not filtro.valore.IsEnabled()
        filtro.condizione.SetSelection(1)
        filtro.conferma()
        assert filtro.risultato == (None, "sesso", "f", None, "sesso donna")
    finally:
        filtro.Destroy()


def test_aspetto(app_wx):
    dialogo = dialoghi.Aspetto(None, {"dimensione": 20, "colore_testo": [100, 100, 100], "colore_sfondo": [0, 0, 50], "volume_effetti": 30})
    try:
        assert dialogo.valori() == {"dimensione": 20, "colore_testo": [100, 100, 100], "colore_sfondo": [0, 0, 50], "volume_effetti": 30}
        dialogo.ai_predefiniti()
        # I predefiniti dell'aspetto non toccano il volume degli effetti.
        assert dialogo.valori() == impostazioni.valide({"volume_effetti": 30})
        dialogo.conferma()
        assert dialogo.risultato == impostazioni.valide({"volume_effetti": 30})
    finally:
        dialogo.Destroy()


def test_impostazioni_salvate_e_rilette(cartella_di_prova):
    assert impostazioni.carica() == impostazioni.PREDEFINITE
    assert impostazioni.salva({"dimensione": 30, "colore_testo": [10, 20, 30], "colore_sfondo": [0, 0, 0]})
    assert impostazioni.carica()["dimensione"] == 30
    (cartella_di_prova / impostazioni.FILE_IMPOSTAZIONI).write_text(json.dumps({"dimensione": 900, "colore_testo": "rosso"}), encoding="utf-8")
    assert impostazioni.carica() == impostazioni.PREDEFINITE


def test_caffe_invio_chiude(app_wx):
    dialogo = dialoghi.Caffe(None, "Offrimi un caffè, se ti va.")
    try:
        assert dialogo.bottoni[0].GetLabel() == "Dona con &PayPal"
        assert dialogo.bottoni[-1].GetLabel() == "&Chiudi"
        assert dialogo.GetDefaultItem() is dialogo.bottoni[-1]
    finally:
        dialogo.Destroy()


# Le operazioni delle polisportive, tappa 7.

def _nome(g):
    return f"{g.nome} {g.cognome}"


def test_nuova_polisportiva(finestra, cartella_di_prova, monkeypatch):
    avvisi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: avvisi.append(testo))
    dialogo = dialoghi.NuovaPolisportiva(finestra, finestra.mondo)
    try:
        dialogo.nome.ChangeValue("club di prova")
        dialogo.conferma()
        assert dialogo.risultato is None and avvisi[-1] == "Esiste già una polisportiva che si chiama Club Di Prova."
        dialogo.nome.ChangeValue("Circolo dei ciechi")
        dialogo.password.ChangeValue("abc")
        dialogo.conferma()
        assert dialogo.risultato is None and avvisi[-1] == "La password e la conferma non coincidono."
        dialogo.conferma_password.ChangeValue("abc")
        dialogo.conferma()
        assert dialogo.risultato == ("Circolo dei ciechi", "abc", True)
    finally:
        dialogo.Destroy()

    def fonda(self):
        self.nome.ChangeValue("Circolo dei ciechi")
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.NuovaPolisportiva, "ShowModal", fonda)
    finestra.nuova_polisportiva()
    nuova = finestra.mondo.polisportive["Circolo dei ciechi"]
    assert finestra.mondo.miapolisportiva_attiva is nuova and not nuova.protetta
    assert finestra.vista.GetValue().startswith("Hai fondato Circolo dei ciechi. È la tua polisportiva attiva.")
    assert "Circolo dei ciechi" in archivio.leggi(cartella_di_prova / FILE_MONDO)["mondo"]["polisportive"]


def test_cambia_polisportiva(finestra, monkeypatch):
    mondo = finestra.mondo
    seconda = mondo.fonda_polisportiva("Seconda squadra", attiva=False)
    avvisi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: avvisi.append(testo))
    dialogo = dialoghi.CambiaPolisportiva(finestra, mondo)
    try:
        assert dialogo.elenco.GetCount() == 2
        assert dialogo.elenco.GetString(dialogo.elenco.GetSelection()).startswith("Club Di Prova, attiva, 2 tesserati su 15")
        dialogo.conferma()
        assert dialogo.scelta is None and avvisi[-1] == "La password di Club Di Prova non è giusta."
        dialogo.password.ChangeValue("segreta")
        dialogo.conferma()
        assert dialogo.scelta is mondo.polisportive["Club Di Prova"]
    finally:
        dialogo.Destroy()

    def scegli_la_seconda(self):
        self.elenco.SetSelection(1)
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.CambiaPolisportiva, "ShowModal", scegli_la_seconda)
    finestra.cambia_polisportiva()
    assert mondo.miapolisportiva_attiva is seconda
    assert finestra.vista.GetValue().startswith("[TUA] Seconda squadra")


def test_mercato(finestra, monkeypatch):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva
    messaggi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: messaggi.append(testo) or wx.YES)
    monkeypatch.setattr(modulo_mondo, "caso", lambda p: True)
    cpu = mondo.polisportive[mondo.crea_polisportiva_cpu(mondo.datetime_corrente_simulazione)]
    for gid in (10, 11):
        mondo._tessera(cpu, mondo.giocatori[gid])
    mondo.metti_in_vendita(cpu, mondo.giocatori[11], 500)
    dialogo = dialoghi.Mercato(finestra, mondo, poli)
    try:
        liberi = [g for g in mondo.giocatori.values() if g.appartenenza == "*" and not g.ritirato]
        assert len(dialogo.righe) == len(liberi) + 1
        valori = [c.giocatore.indice_collettivo_valore for c in dialogo.righe]
        assert valori == sorted(valori, reverse=True)
        assert dialogo.etichetta_trovati.GetLabel() == f"&Giocatori trovati: {len(liberi) + 1}"
        assert dialogo.elenco_filtri.GetString(0) == "Nessun filtro: compaiono tutti."
        dialogo.scelta.SetSelection(3)
        dialogo.aggiorna()
        assert [c.giocatore.id for c in dialogo.righe] == [10]
        dialogo.scelta.SetSelection(2)
        dialogo.aggiorna()
        assert [c.giocatore.id for c in dialogo.righe] == [11]
        # Chi è in vendita si compra al prezzo chiesto, dopo la conferma.
        dialogo.trovati.SetSelection(0)
        dialogo.offri()
        assert mondo.giocatori[11].appartenenza == poli.nome
        assert messaggi[-2].startswith(f"Comprare {_nome(mondo.giocatori[11])} da {cpu.nome} per 500 euro?")
        assert dialogo.esiti[-1] == (messaggi[-1], True)
        # A un libero si offre l'ingaggio scelto nel dialogo della cifra.
        dialogo.scelta.SetSelection(1)
        dialogo.aggiorna()
        candidato = dialogo.righe[0]

        def ingaggio_chiesto(self):
            self.valore = candidato.costo
            return wx.ID_OK

        monkeypatch.setattr(dialoghi.Cifra, "ShowModal", ingaggio_chiesto)
        dialogo.trovati.SetSelection(0)
        dialogo.offri()
        assert candidato.giocatore.appartenenza == poli.nome
        assert messaggi[-2].startswith(f"Offrire a {_nome(candidato.giocatore)} un ingaggio di ")
        assert messaggi[-1].startswith(f"{_nome(candidato.giocatore)} ha accettato l'ingaggio di ")
        assert dialogo.info.GetLabel().startswith(f"Club Di Prova: cassa {testi.euro(poli.cassa)}, gloria 100, tesserati 4 su 15, mosse rimaste 3 su 5.")
    finally:
        dialogo.Destroy()

    def cento_euro(self):
        self.valore = 100
        return wx.ID_OK

    def un_offerta(self):
        self.trovati.SetSelection(0)
        self.offri()
        return wx.ID_CANCEL

    monkeypatch.setattr(dialoghi.Cifra, "ShowModal", cento_euro)
    monkeypatch.setattr(dialoghi.Mercato, "ShowModal", un_offerta)
    finestra.mercato()
    assert finestra.vista.GetValue().startswith("Mercato di Club Di Prova: 1 offerta, 1 riuscita.")
    assert finestra.ultimo_evento == "mercato: 1 offerta"


def test_cifra(app_wx, monkeypatch):
    avvisi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: avvisi.append(testo))
    dialogo = dialoghi.Cifra(None, "Ingaggio", "Spiegazione.", "&Ingaggio", 500, 300, lambda cifra: f"Nota per {cifra}.")
    try:
        assert dialogo.cifra.GetValue() == 300 and dialogo.cifra.GetMax() == 300
        assert dialogo.nota.GetLabel() == "Nota per 300."
        dialogo.cifra.SetValue(0)
        dialogo.conferma()
        assert dialogo.valore is None and avvisi == ["La cifra deve essere di almeno 1 euro."]
        dialogo.cifra.SetValue(120)
        dialogo.conferma()
        assert dialogo.valore == 120
    finally:
        dialogo.Destroy()


def test_arretrati_e_vendite(finestra, monkeypatch):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva
    g = mondo.giocatori[2]
    g.arretrati = 300
    g.pazienza = 40.
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.OK)

    def paga_tutto(self):
        assert self.debitori == [g] and self.cifra.GetValue() == 300
        self.paga()
        return wx.ID_CANCEL

    monkeypatch.setattr(dialoghi.PagaArretrati, "ShowModal", paga_tutto)
    finestra.paga_arretrati()
    assert g.arretrati == 0 and poli.cassa == 20_000 - 300
    assert finestra.vista.GetValue().startswith(f"Pagati 300 euro a {_nome(g)}.")
    finestra.paga_arretrati()
    assert finestra.vista.GetValue().startswith("Nessun tesserato di Club Di Prova aspetta arretrati.")

    def vendi_il_primo(self):
        self.prezzo.SetValue(1500)
        self.metti()
        return wx.ID_CANCEL

    monkeypatch.setattr(dialoghi.Vendite, "ShowModal", vendi_il_primo)
    finestra.vendite()
    primo = max((mondo.giocatori[gid] for gid in poli.tesserati), key=lambda x: x.indice_collettivo_valore)
    assert poli.in_vendita == {primo.id: 1500}
    assert finestra.vista.GetValue() == f"{_nome(primo)} è in vendita a 1.500 euro."
    finestra.bilancio()
    assert finestra.vista.GetValue().startswith(f"Bilancio di Club Di Prova: in cassa {testi.euro(poli.cassa)}.")


def test_avviso_degli_stipendi_non_pagati(finestra):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva
    poli.cassa = 0
    poli.gloria = 1
    mondo.datetime_corrente_simulazione = datetime.datetime(2026, 10, 31, 12, 0)
    mondo.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=9)
    finestra._al_minuto(None)
    assert mondo.datetime_corrente_simulazione.day == 1
    assert finestra.ultimo_evento == "stipendi non pagati, vedi il bilancio"
    assert finestra.barra.GetValue().splitlines()[3] == "stipendi non pagati, vedi il bilancio"


def test_svincolo(finestra, monkeypatch):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva

    def scegli(self):
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.SceltaGiocatore, "ShowModal", scegli)
    finestra.svincola()
    assert poli.tesserati == [2, 5]
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.YES)
    finestra.svincola()
    assert poli.tesserati == [5] and mondo.giocatori[2].appartenenza == "*"
    assert finestra.vista.GetValue().startswith(f"{_nome(mondo.giocatori[2])} è svincolat")


def test_password_e_chiusura(finestra, monkeypatch):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva
    avvisi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: avvisi.append(testo) or wx.YES)
    dialogo = dialoghi.PasswordPolisportiva(finestra, poli)
    try:
        dialogo.attuale.ChangeValue("sbagliata")
        dialogo.conferma()
        assert dialogo.risultato is None and avvisi[-1] == "La password attuale non è giusta."
        dialogo.attuale.ChangeValue("segreta")
        dialogo.conferma()
        assert dialogo.risultato == ""
    finally:
        dialogo.Destroy()
    # Chiudere una polisportiva protetta chiede la password: senza, non succede nulla.
    finestra.chiudi_polisportiva()
    assert "Club Di Prova" in mondo.polisportive

    def togli(self):
        self.attuale.ChangeValue("segreta")
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.PasswordPolisportiva, "ShowModal", togli)
    finestra.password_polisportiva()
    assert not poli.protetta
    assert finestra.vista.GetValue() == "Club Di Prova non è protetta da password."
    finestra.chiudi_polisportiva()
    assert "Club Di Prova" not in mondo.polisportive and mondo.miapolisportiva_attiva is None
    assert finestra.vista.GetValue().startswith("Club Di Prova ha chiuso per sempre: 2 giocatori tornano liberi.")
    assert mondo.giocatori[2].appartenenza == "*"
    finestra.mercato()
    assert finestra.vista.GetValue().startswith("Non hai una polisportiva attiva")


def test_chiudere_una_protetta_con_la_password(finestra, monkeypatch):
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.YES)

    def giusta(self):
        self.password.ChangeValue("segreta")
        self.conferma()
        return self.GetReturnCode()

    monkeypatch.setattr(dialoghi.ChiediPassword, "ShowModal", giusta)
    finestra.chiudi_polisportiva()
    assert "Club Di Prova" not in finestra.mondo.polisportive


# Gli effetti sonori, decisione D24: il conftest li registra senza suonarli.

def _guasto(*_args):
    raise OSError("disco pieno")


def test_i_comandi_suonano_il_loro_evento(finestra, suonati):
    voci = {voce[0]: voce[2] for _titolo, elenco in finestra.voci_menu() for voce in filter(None, elenco)}
    for testo in ("&Guida ai comandi", "&Informazioni", "&Novità", "&TOP 10", "&Classifica per valore", "Vista &principale", "&Barra di stato",
                  "R&isultati della ricerca", "&Riepilogo dell'ultimo avanzamento", "&Scheda della polisportiva attiva", "&Bilancio della polisportiva attiva",
                  "&Tesserati della polisportiva attiva", "&Elenco delle polisportive", "&Vecchie glorie"):
        finestra._esegui(voci[testo])
    assert suonati == ["guida", "informazioni", "novita", "top_10", "classifica", "fuoco_vista", "fuoco_barra", "nessuna_ricerca", "nessun_avanzamento",
                       "scheda_polisportiva", "bilancio", "tesserati_polisportiva", "elenco_polisportive", "vecchie_glorie"]
    finestra.mondo.miapolisportiva_attiva = None
    finestra._esegui(voci["&Tesserati della polisportiva attiva"])
    assert suonati[-1] == "nessuna_polisportiva_attiva"
    assert finestra.vista.GetValue().startswith("Non hai una polisportiva attiva: fondane una con Ctrl+N")


def test_annullare_un_dialogo_suona(finestra, suonati):
    finestra.scheda_giocatore()
    finestra.cerca()
    finestra.cambia_aspetto()
    finestra.cambia_effetti()
    assert suonati == ["dialogo_scheda_giocatore", "annullato", "dialogo_ricerca", "annullato", "dialogo_aspetto", "annullato", "dialogo_effetti_sonori", "annullato"]


@pytest.mark.parametrize(("origine", "avvisi", "atteso"), [
    (archivio.CARICATO, False, "avvio"), (archivio.NATO, False, "avvio_mondo_nuovo"), (archivio.DALLA_COPIA, True, "avvio_dalla_copia"),
    (archivio.CARICATO, True, "avvio_con_avvisi"), (archivio.NATO, True, "avvio_con_avvisi"),
])
def test_il_suono_dell_avvio(app_wx, mondo, suonati, origine, avvisi, atteso):
    rapporto = Mondo.rapporto_vuoto(adesso()) | {"ticks": 3, "giorni": 3}
    f = FinestraPrincipale(mondo, origine, [], rapporto, mondo.datetime_ultimo_run_reale, avvisi_all_avvio=avvisi)
    try:
        f.suoni_d_avvio()
        if origine == archivio.NATO:
            # Il mondo appena nato avanza subito di un giorno, e quel giorno non suona.
            assert suonati == [atteso]
            assert f.ultimo_evento == "mondo pronto"
        else:
            assert suonati == [atteso, "mondo_avanzato_piu_giorni"]
            assert f.ultimo_evento == "mondo avanzato di 3 giorni"
    finally:
        f.timer.Stop()
        f.Destroy()
        wx.Yield()


def test_i_tre_esiti_del_salvataggio(finestra, suonati, monkeypatch):
    finestra.salva()
    scrivi = archivio.scrivi
    monkeypatch.setattr(archivio, "scrivi", lambda *args: (scrivi(*args)[0], ["La copia di sicurezza non si è potuta aggiornare: prova."]))
    finestra.salva()
    assert "La copia di sicurezza non si è potuta aggiornare: prova." in finestra.vista.GetValue()
    monkeypatch.setattr(archivio, "scrivi", _guasto)
    finestra.salva()
    assert suonati == ["salvataggio_riuscito", "salvataggio_con_avviso", "salvataggio_non_riuscito"]
    assert finestra.ultimo_evento == "salvataggio non riuscito"


def test_un_operazione_che_non_si_salva(finestra, suonati, monkeypatch):
    def fonda(self):
        self.nome.ChangeValue("Circolo dei ciechi")
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.NuovaPolisportiva, "ShowModal", fonda)
    monkeypatch.setattr(archivio, "scrivi", _guasto)
    finestra.nuova_polisportiva()
    assert suonati == ["dialogo_nuova_polisportiva", "polisportiva_fondata", "salvataggio_non_riuscito"]
    assert finestra.vista.GetValue().startswith("Hai fondato Circolo dei ciechi.")
    assert finestra.vista.GetValue().endswith("Salvataggio non riuscito: disco pieno. Il salvataggio precedente è rimasto com'era.")


def test_l_avanzamento_suona_una_volta_sola(finestra, suonati, monkeypatch):
    mondo = finestra.mondo
    mondo.datetime_corrente_simulazione = datetime.datetime(2026, 10, 10, 12, 0)
    mondo.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=9)
    finestra._modali = 1
    finestra._al_minuto(None)
    assert suonati == []
    finestra._modali = 0
    finestra._al_minuto(None)
    evento, testo = suoni.evento_avanzamento(finestra.rapporto, True, True)
    assert suonati == [evento]
    assert finestra.ultimo_evento == testo
    assert finestra.barra.GetValue().splitlines()[3] == testo
    # Senza giorni maturati il timer tace.
    finestra._al_minuto(None)
    assert suonati == [evento]
    mondo.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=9)
    monkeypatch.setattr(archivio, "scrivi", _guasto)
    finestra._al_minuto(None)
    assert suonati == [evento, "salvataggio_non_riuscito"]
    assert finestra.ultimo_evento == "mondo avanzato di un giorno, non salvato"


def test_gli_stipendi_non_pagati_suonano(finestra, suonati):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva
    poli.cassa = 0
    poli.gloria = 1
    mondo.datetime_corrente_simulazione = datetime.datetime(2026, 10, 31, 12, 0)
    mondo.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=9)
    finestra._al_minuto(None)
    assert finestra.rapporto["mesi"] == 1
    assert suonati == ["stipendi_non_pagati"]


@pytest.mark.parametrize(("guasto", "atteso"), [(False, "uscita"), (True, "uscita_senza_salvataggio")])
def test_l_uscita_aspetta_il_suo_suono(finestra, suonati, monkeypatch, guasto, atteso):
    if guasto:
        monkeypatch.setattr(archivio, "scrivi", _guasto)
    finestra.Close()
    wx.Yield()
    assert suonati == [atteso]
    assert suonati.dettagli[0]["sync"] == suoni.ATTESA_USCITA


def test_l_elenco_che_si_svuota_e_si_riempie(app_wx, mondo, suonati):
    dialogo = dialoghi.SceltaGiocatore(None, mondo)
    try:
        dialogo.campo.ChangeValue("2")
        dialogo.filtra()
        dialogo.campo.ChangeValue("zzzz")
        dialogo.filtra()
        dialogo.campo.ChangeValue("zzzzz")
        dialogo.filtra()
        dialogo.campo.ChangeValue("")
        dialogo.filtra()
        dialogo.campo.ChangeValue("zzzz")
        dialogo.filtra()
        dialogo.conferma()
        assert suonati == ["elenco_svuotato", "elenco_ripopolato", "elenco_svuotato", "nessuna_selezione"]
        assert dialogo.scelto is None
    finally:
        dialogo.Destroy()


def test_i_suoni_delle_password(finestra, suonati, monkeypatch):
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.OK)
    dialogo = dialoghi.PasswordPolisportiva(finestra, finestra.mondo.miapolisportiva_attiva)
    try:
        dialogo.attuale.ChangeValue("sbagliata")
        dialogo.conferma()
        dialogo.attuale.ChangeValue("segreta")
        dialogo.nuova.ChangeValue("nuova")
        dialogo.conferma()
    finally:
        dialogo.Destroy()
    nuova = dialoghi.NuovaPolisportiva(finestra, finestra.mondo)
    try:
        nuova.nome.ChangeValue("x")
        nuova.conferma()
    finally:
        nuova.Destroy()
    assert suonati == ["password_sbagliata", "password_non_coincidono", "campo_da_correggere"]


def test_i_suoni_del_mercato(finestra, suonati, monkeypatch):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.YES)
    monkeypatch.setattr(modulo_mondo, "caso", lambda p: False)
    valori = ["1000000", "0"]

    def filtro(self):
        self.valore.ChangeValue(valori.pop(0))
        self.conferma()
        return wx.ID_OK

    def cifra(self):
        self.valore = self.cifra.GetValue()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.Ricerca, "ShowModal", filtro)
    monkeypatch.setattr(dialoghi.Cifra, "ShowModal", cifra)
    dialogo = dialoghi.Mercato(finestra, mondo, poli)
    try:
        assert suonati == []
        dialogo.scelta.SetSelection(2)
        dialogo.aggiorna(suono="mercato_scelta_cambiata")
        dialogo.ordine.SetSelection(1)
        dialogo.aggiorna(suono="mercato_ordine_cambiato")
        dialogo.scelta.SetSelection(1)
        dialogo.aggiorna(suono="mercato_scelta_cambiata")
        dialogo.togli_tutti()
        # Un filtro che non lascia nessuno suona come l'elenco che si svuota, e toglierlo come l'elenco che torna pieno.
        dialogo.aggiungi_filtro()
        dialogo.togli_filtro()
        dialogo.aggiungi_filtro()
        dialogo.togli_tutti()
        dialogo.trovati.SetSelection(0)
        dialogo.offri()
        assert suonati == ["elenco_svuotato", "mercato_ordine_cambiato", "elenco_ripopolato", "nessuna_selezione",
                           "dialogo_filtro_mercato", "elenco_svuotato", "elenco_ripopolato", "dialogo_filtro_mercato", "filtro_aggiunto", "filtri_tutti_tolti",
                           "dialogo_cifra_ingaggio", "domanda", "ingaggio_rifiutato"]
        poli.movimenti_oggi = 5
        dialogo.offri()
        assert suonati[-1] == "mosse_finite"
        poli.cassa = 0
        dialogo.offri()
        assert suonati[-1] == "cassa_insufficiente"
    finally:
        dialogo.Destroy()


def test_il_mercato_che_si_apre_vuoto(finestra, suonati, monkeypatch):
    monkeypatch.setattr(dialoghi.mercato, "candidati", lambda *a, **k: [])
    finestra.mercato()
    assert suonati == ["dialogo_mercato", "elenco_svuotato", "lavoro_concluso"]


def test_i_tre_esiti_del_pagamento(finestra, suonati, monkeypatch):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva
    primo, secondo = mondo.giocatori[2], mondo.giocatori[5]
    primo.arretrati, secondo.arretrati = 300, 200
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.OK)
    dialogo = dialoghi.PagaArretrati(finestra, mondo, poli)

    def scegli(g, cifra=None):
        dialogo.elenco.SetSelection(dialogo.debitori.index(g))
        dialogo.al_giocatore()
        if cifra is not None:
            dialogo.cifra.SetValue(cifra)
        dialogo.paga()

    try:
        scegli(primo, 100)
        scegli(primo)
        scegli(secondo)
        dialogo.paga()
        assert suonati == ["arretrati_pagati_in_parte", "arretrati_saldati", "arretrati_tutti_saldati", "nessuna_selezione"]
        secondo.arretrati = 50
        poli.cassa = 0
        dialogo.aggiorna()
        dialogo.paga()
        assert suonati[-1] == "cassa_insufficiente"
    finally:
        dialogo.Destroy()


def test_i_suoni_delle_vendite(finestra, suonati, monkeypatch):
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.OK)
    dialogo = dialoghi.Vendite(finestra, finestra.mondo, finestra.mondo.miapolisportiva_attiva)
    try:
        dialogo.metti()
        dialogo.metti()
        dialogo.togli()
        dialogo.togli()
    finally:
        dialogo.Destroy()
    assert suonati == ["messo_in_vendita", "prezzo_di_vendita_cambiato", "tolto_dalla_vendita", "vendita_non_attiva"]


def test_il_volume_degli_effetti(finestra, suonati, monkeypatch, cartella_di_prova):
    def scegli(volume):
        def mostra(self):
            self.volume.SetValue(volume)
            self.prova()
            self.conferma()
            return wx.ID_OK
        return mostra

    monkeypatch.setattr(dialoghi.EffettiSonori, "ShowModal", scegli(80))
    finestra.cambia_effetti()
    assert suonati == ["dialogo_effetti_sonori", "prova_volume_effetti", "effetti_sonori_applicati"]
    assert [d["fattore"] for d in suonati.dettagli] == [1.0, 1.6, 1.6]
    assert impostazioni.carica()["volume_effetti"] == 80
    assert finestra.ultimo_evento == "volume degli effetti 80"
    # A zero tacciono la prova e la conferma; l'aspetto, salvato dopo, non cambia il volume.
    monkeypatch.setattr(dialoghi.EffettiSonori, "ShowModal", scegli(0))
    finestra.cambia_effetti()
    assert suonati == ["dialogo_effetti_sonori", "prova_volume_effetti", "effetti_sonori_applicati", "dialogo_effetti_sonori"]
    assert suoni.volume_effetti() == 0

    def ok(self):
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.Aspetto, "ShowModal", ok)
    finestra.cambia_aspetto()
    assert impostazioni.carica()["volume_effetti"] == 0
    assert len(suonati) == 4


def test_il_tic_della_probabilita(app_wx, suonati):
    dialogo = dialoghi.Cifra(None, "Ingaggio", "Spiegazione.", "&Ingaggio", 500, 1000, lambda cifra: f"Nota per {cifra}.", lambda cifra: cifra / 10)
    try:
        dialogo.aggiorna()
        assert suonati == []
        dialogo.cifra.SetValue(900)
        dialogo.tic_della_probabilita()
        assert suonati == ["probabilita_ingaggio"]
        assert suonati.dettagli[0]["semitoni"] == pytest.approx(suoni.probabilita_in_semitoni(90))
    finally:
        dialogo.Destroy()


def test_l_errore_imprevisto(finestra, suonati, monkeypatch):
    messaggi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: messaggi.append(testo))
    finestra.errore_imprevisto(ValueError, ValueError("prova"))
    assert suonati == ["errore_imprevisto"]
    assert messaggi == ["Il comando si è interrotto per un errore imprevisto: ValueError, prova. La traccia completa è sulla console."]
    assert finestra._modali == 0


def test_il_suono_di_prova_aspetta_che_ci_si_fermi(app_wx, suonati):
    # Tre ritocchi di fila danno un suono solo, al volume dell'ultimo, quando ci si ferma.
    dialogo = dialoghi.EffettiSonori(None, 50)
    try:
        for valore in (60, 70, 80):
            dialogo.volume.SetValue(valore)
            dialogo.al_volume()
        assert suonati == []
        # I timer di wx scattano soltanto dentro un ciclo degli eventi: qui ne gira uno per un secondo.
        ciclo = wx.GUIEventLoop()
        wx.CallLater(1000, ciclo.Exit)
        ciclo.Run()
        assert suonati == ["prova_volume_effetti"]
        assert suonati.dettagli[0]["fattore"] == pytest.approx(1.6)
    finally:
        dialogo.Destroy()


def test_ogni_domanda_si_o_no_ha_il_no_gia_scelto():
    # Un Invio di troppo non deve mai confermare un'operazione: vale anche al mercato, dalla 1.39.6.
    radice = Path(__file__).resolve().parent.parent / "gui"
    senza = [f"{p.name}:{n}" for p in sorted(radice.glob("*.py")) for n, riga in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
             if "wx.YES_NO" in riga and "wx.NO_DEFAULT" not in riga]
    assert not senza, f"domande con il Sì già scelto: {senza}"
