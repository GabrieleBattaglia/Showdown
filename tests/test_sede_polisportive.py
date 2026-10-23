"""
Le prove della sede delle polisportive, tappa 14, richiesta di Gabriele del 23 ottobre 2026: anche le
polisportive appartengono a un territorio. Quelle del computer ricevono il comune coi pesi della
popolazione da un caso nato dal nome, che non tocca quello del mondo; l'utente lo sceglie alla fondazione
in un elenco che si restringe mentre scrive, con la percentuale della popolazione di ogni comune su quella
del più popoloso, Roma 100%. La scheda dice la sede, l'elenco delle polisportive il comune, e i mondi del
formato 8 la ricevono nell'aggiornamento al 9. Il dialogo della fondazione nasce sul desktop nascosto del
conftest, coi messaggi di wx sostituiti da un registratore che risponde come gli si dice.
Dal 2026-10-24, col collaudo di gioco, la sede che non corrisponde a nessun comune suona come un campo da correggere.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
"""

import collections
import datetime
import gzip
import json
import random

import pytest
import wx

import archivio
import luoghi
import testi
from costanti import FILE_MONDO
from gui import dialoghi
from modelli import Polisportiva
from mondo import Mondo

INIZIO = datetime.datetime(2026, 5, 15, 12, 0)


# L'estrazione delle polisportive del computer.

def test_la_sede_segue_la_popolazione_e_non_tocca_il_caso_del_mondo():
    random.seed(7)
    prima = random.random()
    random.seed(7)
    nomi = [f"PoliTeam{n:02d} Prova" for n in range(1, 40_001)]
    estratti = collections.Counter(Polisportiva(nome, None, INIZIO, is_cpu_controlled=True).luogo for nome in nomi[:2000])
    estratti.update(luoghi.luogo_della_polisportiva(nome) for nome in nomi[2000:])
    assert random.random() == prima
    tabella = luoghi._carica()
    # Roma ha il 7,3% degli abitanti della collezione: su 40.000 estrazioni, circa 2.940.
    atteso = 40_000 * tabella["abitanti"]["Roma"] / tabella["totale"]
    assert abs(estratti["Roma"] - atteso) < 4 * atteso ** 0.5
    assert estratti["Milano"] > estratti["Bologna"] > estratti["Pescocostanzo"]
    # Lo stesso nome dà sempre lo stesso comune, e nomi diversi danno sedi diverse.
    assert luoghi.luogo_della_polisportiva("PoliTeam01 Abab-Cdcd") == Polisportiva("PoliTeam01 Abab-Cdcd", None, INIZIO, True).luogo
    assert len(estratti) > 500


def test_la_polisportiva_dell_utente_ha_il_comune_scelto():
    m = Mondo()
    m.datetime_corrente_simulazione = INIZIO
    scelta = m.fonda_polisportiva("Circolo dei ciechi", luogo="Bologna")
    estratta = m.fonda_polisportiva("Seconda squadra", attiva=False)
    assert scelta.luogo == "Bologna" and estratta.luogo == luoghi.luogo_della_polisportiva("Seconda squadra")
    # Il comune va e torna dal salvataggio.
    assert Polisportiva.da_dizionario(json.loads(json.dumps(scelta.a_dizionario()))).luogo == "Bologna"
    # La proposta della fondazione viene da un caso suo: il caso del mondo resta dov'era.
    random.seed(3)
    prima = random.random()
    random.seed(3)
    proposte = {luoghi.comune_a_caso() for _ in range(200)}
    assert random.random() == prima and proposte <= set(tabella_dei_comuni()) and len(proposte) > 20


def tabella_dei_comuni():
    return luoghi._carica()["abitanti"]


# Le percentuali e la ricerca.

def test_le_percentuali_rispetto_al_comune_piu_popoloso():
    assert luoghi.percentuale("Roma") == 100 and luoghi.percentuale("Atlantide") is None
    assert testi.riga_del_comune("Roma") == "Roma 100%, provincia di Roma, Lazio"
    assert testi.riga_del_comune("Bologna") == "Bologna 14%, provincia di Bologna, Emilia-Romagna"
    assert testi.riga_del_comune("Pescocostanzo") == "Pescocostanzo 0,04%, provincia dell'Aquila, Abruzzo"
    assert testi.riga_del_comune("Bard") == "Bard 0,004%, provincia di Aosta, Valle d'Aosta"
    assert testi.riga_del_comune("Atlantide") == "Atlantide"
    # I decimali crescono quando il numero è piccolo, e si arrotonda come si scrive: 0,96 è 1%, non 1,0%.
    assert [luoghi.decimali_della_percentuale(v) for v in (100, 14.1, 0.96, 0.4, 0.0393, 0.0039)] == [0, 0, 0, 1, 2, 3]
    # Nessun comune della collezione si legge 0%.
    for comune in tabella_dei_comuni():
        valore = luoghi.percentuale(comune)
        cifre = testi.percento(valore, luoghi.decimali_della_percentuale(valore))
        assert testi.riga_del_comune(comune).startswith(f"{comune} {cifre}, provincia ") and any(c in "123456789" for c in cifre), comune


def test_la_ricerca_dei_comuni():
    tutti = luoghi.candidati("")
    assert len(tutti) == 1291 and tutti[:3] == ["Roma", "Milano", "Napoli"]
    # Prima il nome giusto, poi chi comincia così, poi chi ha una parola che comincia così, poi chi lo contiene.
    assert luoghi.candidati("ROMA")[:2] == ["Roma", "Romano di Lombardia"] and "Genzano di Roma" in luoghi.candidati("roma")
    bol = luoghi.candidati("bol")
    assert bol[:4] == ["Bologna", "Bolzano", "Bolsena", "Castel Bolognese"] and bol.index("Castel Bolognese") < bol.index("Eboli")
    # Senza badare ad accenti, apostrofi, anche quello tipografico, e trattini.
    assert luoghi.candidati("forli")[0] == "Forlì" and luoghi.candidati("Forlì") == luoghi.candidati("FORLI")
    assert luoghi.candidati("sant'angelo") == luoghi.candidati("sant angelo") == luoghi.candidati(f"sant{chr(0x2019)}angelo")
    assert "Città Sant'Angelo" in luoghi.candidati("sant'angelo") and luoghi.candidati("l aquila")[0] == "L'Aquila"
    assert luoghi.candidati("  pescocostanzo ") == ["Pescocostanzo"] and luoghi.candidati("xyz") == []


# La scheda e l'elenco.

def _mondo_con_le_polisportive():
    random.seed(5)
    m = Mondo()
    m.datetime_corrente_simulazione = INIZIO
    m.crea_giocatori_casuali(12, INIZIO, annuncia=False)
    mia = m.fonda_polisportiva("Circolo dei ciechi", luogo="Bologna")
    cpu = Polisportiva("PoliTeam01 Abab-Cdcd", None, INIZIO, is_cpu_controlled=True)
    m.polisportive[cpu.nome] = cpu
    return m, mia, cpu


def test_la_scheda_e_l_elenco_dicono_la_sede():
    m, mia, cpu = _mondo_con_le_polisportive()
    righe = testi.scheda_polisportiva(mia, m).splitlines()
    assert righe[1] == "Sede: Bologna, provincia di Bologna, Emilia-Romagna"
    assert f"Sede: {luoghi.descrivi(cpu.luogo)}" in testi.scheda_polisportiva(cpu, m)
    elenco = testi.elenco_polisportive(m)
    assert "\nCircolo dei ciechi, tua, sede Bologna, 0 tesserati su 15, gloria 100," in elenco
    assert f"\nPoliTeam01 Abab-Cdcd, del computer, sede {cpu.luogo}, " in elenco
    # Senza la collezione dei comuni la sede resta vuota, e la scheda non ne parla.
    mia.luogo = ""
    assert "Sede" not in testi.scheda_polisportiva(mia, m) and "\nCircolo dei ciechi, tua, 0 tesserati" in testi.elenco_polisportive(m)


# L'aggiornamento dal formato 8.

def _al_formato_8(m):
    contenuto = archivio.componi(m)
    contenuto["formato"] = 8
    for p in contenuto["mondo"]["polisportive"].values():
        del p["luogo"]
    return contenuto


def test_l_aggiornamento_dal_formato_8_da_una_sede_a_tutte(cartella_di_prova):
    m, mia, cpu = _mondo_con_le_polisportive()
    m.miapolisportiva_attiva = mia
    contenuto = _al_formato_8(m)
    archivio.MIGRAZIONI[8](contenuto)
    assert contenuto["formato"] == 9 == archivio.FORMATO
    nuovo = Mondo()
    archivio.costruisci(contenuto, nuovo)
    # Anche quella dell'utente riceve il comune estratto dal nome: nel formato 8 nessuno l'aveva scelto.
    assert {nome: p.luogo for nome, p in nuovo.polisportive.items()} == {nome: luoghi.luogo_della_polisportiva(nome) for nome in m.polisportive}
    # Dal file: il salvataggio dell'8 si legge, si aggiorna e si riscrive nel 9.
    vecchio = _al_formato_8(m)
    percorso = cartella_di_prova / FILE_MONDO
    with gzip.open(percorso, "wt", encoding="utf-8") as f:
        f.write(json.dumps({**vecchio, "firma": archivio.firma(vecchio)}))
    ricaricato = Mondo()
    archivio.carica(ricaricato)
    assert ricaricato.polisportive["PoliTeam01 Abab-Cdcd"].luogo == cpu.luogo
    assert ricaricato.polisportive["Circolo dei ciechi"].luogo == luoghi.luogo_della_polisportiva("Circolo dei ciechi")
    assert archivio.salva(ricaricato)
    assert archivio.leggi(percorso)["formato"] == 9


def test_i_formati_vecchi_arrivano_fino_al_9():
    m, _mia, _cpu = _mondo_con_le_polisportive()
    contenuto = _al_formato_8(m)
    contenuto["formato"] = 7
    for g in contenuto["mondo"]["giocatori"]:
        del g["classe_migliore"], g["luogo"]
    for p in contenuto["mondo"]["polisportive"].values():
        del p["staff"]
    del contenuto["mondo"]["allenatori"], contenuto["mondo"]["prossimo_allenatore"]
    while contenuto["formato"] < archivio.FORMATO:
        archivio.MIGRAZIONI[contenuto["formato"]](contenuto)
    nuovo = Mondo()
    archivio.costruisci(contenuto, nuovo)
    assert all(p.luogo == luoghi.luogo_della_polisportiva(nome) for nome, p in nuovo.polisportive.items())
    assert set(archivio.MIGRAZIONI) == set(range(1, archivio.FORMATO))


# Il dialogo della fondazione.

class Messaggi(list):
    """I testi dei messaggi di wx, in ordine; risposta è quello che rispondono le domande."""

    def __init__(self):
        super().__init__()
        self.risposta = wx.NO

    def __call__(self, testo, *args, **kwargs):
        self.append(testo)
        return self.risposta


@pytest.fixture
def messaggi(monkeypatch):
    registro = Messaggi()
    monkeypatch.setattr(wx, "MessageBox", registro)
    return registro


@pytest.fixture
def fondazione(app_wx):
    m, _mia, _cpu = _mondo_con_le_polisportive()
    dialogo = dialoghi.NuovaPolisportiva(None, m, proposta="Pescocostanzo")
    yield dialogo
    dialogo.Destroy()


def test_il_dialogo_propone_un_comune_e_ogni_controllo_ha_la_sua_lettera(fondazione, suonati):
    d = fondazione
    assert d.sede.GetValue() == "Pescocostanzo" and d.elenco.GetCount() == 1
    assert d.elenco.GetString(d.elenco.GetSelection()) == "Pescocostanzo 0,04%, provincia dell'Aquila, Abruzzo"
    assert d.etichetta_comuni.GetLabel() == "&Comuni trovati: 1" and d.comune_scelto() == "Pescocostanzo"
    # All'apertura l'elenco è pieno: nessun suono.
    assert suonati == []
    etichette = [c.GetLabel() for c in d.pannello.GetChildren() if isinstance(c, (wx.StaticText, wx.CheckBox, wx.Button)) and c.GetLabel() != "Annulla"]
    lettere = [e[e.index("&") + 1].casefold() for e in etichette]
    assert all(e.count("&") == 1 for e in etichette) and len(lettere) == len(set(lettere)) == 7
    # Senza una proposta il dialogo ne estrae una lui, coi pesi della popolazione.
    libero = dialoghi.NuovaPolisportiva(None, d.mondo)
    try:
        assert libero.sede.GetValue() in tabella_dei_comuni() and libero.comune_scelto() == libero.sede.GetValue()
    finally:
        libero.Destroy()


def test_l_elenco_si_restringe_mentre_si_scrive(fondazione, suonati, messaggi):
    d = fondazione
    d.sede.SetValue("bol")
    assert d.comuni[:3] == ["Bologna", "Bolzano", "Bolsena"] and d.elenco.GetSelection() == 0
    assert d.elenco.GetString(0) == "Bologna 14%, provincia di Bologna, Emilia-Romagna"
    assert d.etichetta_comuni.GetLabel() == f"&Comuni trovati: {len(d.comuni)}" and suonati == []
    d.sede.SetValue("bolx")
    assert d.elenco.GetCount() == 0 and d.etichetta_comuni.GetLabel() == "&Comuni trovati: 0"
    d.sede.SetValue("")
    assert d.elenco.GetCount() == 1291 and d.elenco.GetString(0) == "Roma 100%, provincia di Roma, Lazio"
    assert d.etichetta_comuni.GetLabel() == "&Comuni trovati: 1.291"
    assert suonati == ["elenco_svuotato", "elenco_ripopolato"]
    # Con l'elenco vuoto Fonda non fonda, e dice perché; dal collaudo di gioco col suono del campo da correggere,
    # la sede, e non più con quello di chi non ha scelto.
    d.nome.ChangeValue("Circolo nuovo")
    d.sede.SetValue("atlantide")
    d.conferma()
    assert d.risultato is None and messaggi[-1].startswith("Nessun comune corrisponde a quello che hai scritto nella sede")
    assert suonati[-2:] == ["elenco_svuotato", "campo_da_correggere"]
    # Con un nome scritto a metà Fonda chiede prima, dalla revisione della tappa 14, e al sì fonda nel comune scelto.
    d.sede.SetValue("bol")
    d.elenco.SetSelection(1)
    messaggi.risposta = wx.YES
    d.conferma()
    assert messaggi[-1] == "Vuoi fondare la polisportiva Circolo nuovo? Sede: Bolzano, provincia di Bolzano, Trentino-Alto Adige."
    assert d.risultato == ("Circolo nuovo", None, True, "Bolzano") and d.GetReturnCode() == wx.ID_OK


def test_invio_sulla_sede_chiede_conferma(fondazione, suonati, messaggi):
    d = fondazione
    d.nome.ChangeValue("  circolo   nuovo ")
    # Invio sul nome resta a Fonda, il pulsante predefinito; sul campo Sede e sull'elenco chiede prima.
    assert not d.invio(d.nome) and not d.invio(d.password)
    assert d.invio(d.elenco)
    assert d.risultato is None and messaggi == ["Vuoi fondare la polisportiva circolo nuovo? Sede: Pescocostanzo, provincia dell'Aquila, Abruzzo."]
    assert suonati == ["domanda", "annullato"]
    # I controlli vengono prima della domanda: con le password diverse la domanda non arriva.
    d.password.ChangeValue("abc")
    assert d.invio(d.sede)
    assert d.risultato is None and messaggi[-1] == "La password e la conferma non coincidono." and suonati[-1] == "password_non_coincidono"
    d.conferma_password.ChangeValue("abc")
    messaggi.risposta = wx.YES
    assert d.invio(d.sede)
    assert d.risultato == ("  circolo   nuovo ", "abc", True, "Pescocostanzo") and d.GetReturnCode() == wx.ID_OK


def _premi_fonda(d):
    """Il clic su Fonda, che è anche quello che fa Invio sul nome e sulle password, col pulsante predefinito."""
    fonda = d.GetDefaultItem()
    assert fonda.GetLabel() == "&Fonda" and fonda.GetId() == wx.ID_OK
    evento = wx.CommandEvent(wx.wxEVT_BUTTON, wx.ID_OK)
    evento.SetEventObject(fonda)
    fonda.GetEventHandler().ProcessEvent(evento)


def test_la_sede_si_confronta_col_comune_scelto():
    assert luoghi.coincide("forli", "Forlì") and luoghi.coincide(" L'AQUILA ", "L'Aquila") and luoghi.coincide("sant angelo", "Sant'Angelo")
    assert not luoghi.coincide("bol", "Bologna") and not luoghi.coincide("", "Roma") and not luoghi.coincide("", "")


def test_fonda_chiede_conferma_se_la_sede_non_dice_il_comune_scelto(fondazione, suonati, messaggi):
    # La revisione della tappa 14: prima Fonda e Invio sul nome fondavano in silenzio a Roma, il primo dell'elenco pieno.
    d = fondazione
    d.nome.ChangeValue("Circolo nuovo")
    d.sede.SetValue("")
    _premi_fonda(d)
    assert d.risultato is None and messaggi == ["Vuoi fondare la polisportiva Circolo nuovo? Sede: Roma, provincia di Roma, Lazio."]
    assert suonati[-2:] == ["domanda", "annullato"]
    # Un nome scritto a metà, o un comune dell'elenco diverso da quello scritto: la stessa domanda, col no già scelto.
    d.sede.SetValue("pescocost")
    d.conferma()
    assert d.risultato is None and messaggi[-1] == "Vuoi fondare la polisportiva Circolo nuovo? Sede: Pescocostanzo, provincia dell'Aquila, Abruzzo."
    d.sede.SetValue("roma")
    d.elenco.SetSelection(1)
    d.conferma()
    assert d.risultato is None and messaggi[-1] == f"Vuoi fondare la polisportiva Circolo nuovo? Sede: {luoghi.descrivi('Romano di Lombardia')}."
    assert len(messaggi) == 3 and suonati.count("domanda") == 3 == suonati.count("annullato")
    # Il campo che dice proprio il comune scelto, anche senza maiuscole e accenti, fonda senza domande.
    d.sede.SetValue("PESCOCOSTANZO")
    _premi_fonda(d)
    assert len(messaggi) == 3 and d.risultato == ("Circolo nuovo", None, True, "Pescocostanzo") and d.GetReturnCode() == wx.ID_OK


def test_al_si_la_sede_vuota_fonda_nel_comune_scelto(fondazione, messaggi):
    d = fondazione
    d.nome.ChangeValue("Circolo nuovo")
    d.sede.SetValue("")
    messaggi.risposta = wx.YES
    _premi_fonda(d)
    assert messaggi[-1].endswith("Sede: Roma, provincia di Roma, Lazio.") and d.risultato == ("Circolo nuovo", None, True, "Roma")


def test_il_doppio_clic_sull_elenco_chiede_conferma(fondazione, suonati, messaggi):
    d = fondazione
    d.nome.ChangeValue("Circolo nuovo")
    evento = wx.CommandEvent(wx.wxEVT_LISTBOX_DCLICK, d.elenco.GetId())
    evento.SetEventObject(d.elenco)
    # Anche quando il campo dice proprio il comune: il doppio clic sembra sceglierlo, come Invio sull'elenco.
    d.elenco.GetEventHandler().ProcessEvent(evento)
    assert d.risultato is None and messaggi == ["Vuoi fondare la polisportiva Circolo nuovo? Sede: Pescocostanzo, provincia dell'Aquila, Abruzzo."]
    assert suonati == ["domanda", "annullato"]
    messaggi.risposta = wx.YES
    d.elenco.GetEventHandler().ProcessEvent(evento)
    assert d.risultato == ("Circolo nuovo", None, True, "Pescocostanzo") and d.GetReturnCode() == wx.ID_OK
