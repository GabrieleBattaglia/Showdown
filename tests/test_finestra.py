"""
Test della finestra e dei dialoghi, sul desktop nascosto del conftest: ogni voce dei menu, la
barra di stato, il salvataggio, la chiusura con il riepilogo, la scelta del giocatore, la
ricerca, l'aspetto e l'invito al caffè. Le finestre modali vengono sostituite, perché una prova
che aspetta un tasto non finirebbe mai.
"""

import datetime
import json
import random

import pytest
import wx

import archivio
import impostazioni
import mondo as modulo_mondo
import ricerca
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
                   finestra.cambia_polisportiva, finestra.mercato, finestra.svincola, finestra.password_polisportiva, finestra.chiudi_polisportiva}
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
    assert provate == 22
    assert finestra.comandi == 22


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
    data_prima = mondo.datetime_corrente_simulazione
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
    dialogo = dialoghi.Aspetto(None, {"dimensione": 20, "colore_testo": [100, 100, 100], "colore_sfondo": [0, 0, 50]})
    try:
        assert dialogo.valori() == {"dimensione": 20, "colore_testo": [100, 100, 100], "colore_sfondo": [0, 0, 50]}
        dialogo.ai_predefiniti()
        assert dialogo.valori() == impostazioni.valide(None)
        dialogo.conferma()
        assert dialogo.risultato == impostazioni.valide(None)
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
