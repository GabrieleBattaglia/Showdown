"""
Test dell'amichevole nella finestra, tappa 9, sul desktop nascosto del conftest e senza suonare:
il menu Partite, il primo giocatore scelto fra i tuoi, l'avversario fra tutti gli altri, chi ha
già giocato oggi che non compare, le opzioni, il punto per punto fino alla fine, il resto
dell'incontro, la cronaca tutta subito o solo il risultato, il salvataggio della cronaca in una
cartella temporanea, con il momento dell'incontro anche se si salva dopo un avanzamento, il perché
di un mondo non salvato prima della cronaca intera, e i suoni di ogni passo. I dialoghi sono
sostituiti da risposte scritte.
"""

import datetime
import random

import pytest
import wx

import archivio
import partita
import testi
from costanti import CARTELLA_CRONACHE, FILE_MONDO
from gui import dialoghi
from gui.finestra import FinestraPrincipale
from modelli import Polisportiva
from mondo import Mondo
from motore import cronaca
from utilita import adesso, adesso_utc

# Le scelte delle opzioni nell'ordine del dialogo: set, modo di mostrare, livello.
PUNTO, TUTTA, RISULTATO = 0, 1, 2
SINTETICA, NORMALE, TECNICA = 0, 1, 2


@pytest.fixture
def mondo():
    random.seed(23)
    ora = adesso()
    m = Mondo()
    m.datetime_corrente_simulazione = ora
    m.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=2)
    m.crea_giocatori_casuali(20, ora)
    mia = Polisportiva("Club Di Prova", None, ora)
    m.polisportive[mia.nome] = mia
    for gid in (2, 5, 9):
        mia.aggiungi_tesserato(gid, m.giocatori[gid].indice_collettivo_valore)
        m.giocatori[gid].appartenenza = mia.nome
    m.miapolisportiva_attiva = mia
    return m


@pytest.fixture
def finestra(app_wx, mondo, monkeypatch):
    monkeypatch.setattr(wx.Dialog, "ShowModal", lambda self: wx.ID_CANCEL)
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.NO)
    f = FinestraPrincipale(mondo, archivio.CARICATO, [], Mondo.rapporto_vuoto(adesso()), mondo.datetime_ultimo_run_reale)
    f.Show()
    yield f
    if f and not f.IsBeingDeleted():
        f.timer.Stop()
        f.Destroy()
    wx.Yield()


class Scelte:
    """Le risposte scritte ai dialoghi dell'amichevole: i due giocatori, le opzioni, e gli elenchi che i dialoghi hanno mostrato."""

    def __init__(self, monkeypatch, tuo, avversario, set_scelti=0, modo=PUNTO, livello=NORMALE, annulla_opzioni=False):
        self.giocatori = [tuo, avversario]
        self.elenchi = []
        self.titoli = []
        self.opzioni = (set_scelti, modo, livello)
        self.annulla_opzioni = annulla_opzioni
        # Funzioni e non metodi legati: sulla classe del dialogo ricevono il dialogo come primo argomento.
        monkeypatch.setattr(dialoghi.SceltaGiocatore, "ShowModal", lambda dialogo: self.scegli(dialogo))
        monkeypatch.setattr(dialoghi.OpzioniAmichevole, "ShowModal", lambda dialogo: self.opzioni_scelte(dialogo))

    def scegli(self, dialogo):
        self.elenchi.append([g.id for g in dialogo.tutti])
        self.titoli.append(dialogo.GetTitle())
        gid = self.giocatori[len(self.elenchi) - 1]
        dialogo.elenco.SetSelection([g.id for g in dialogo.visibili].index(gid))
        dialogo.conferma()
        return wx.ID_OK

    def opzioni_scelte(self, dialogo):
        if self.annulla_opzioni:
            return wx.ID_CANCEL
        for controllo, scelta in zip((dialogo.set, dialogo.modo, dialogo.livello), self.opzioni, strict=True):
            controllo.SetSelection(scelta)
        dialogo.conferma()
        return wx.ID_OK


def _esito_atteso(finestra, tuo):
    risultato = finestra.incontro.risultato
    vincitore = risultato.parti[0] if risultato.vincitore == "A" else risultato.parti[1]
    return "amichevole_vinta" if vincitore == tuo else "amichevole_persa"


def test_il_menu_partite_e_la_guida(finestra):
    titoli = [titolo for titolo, _voci in finestra.voci_menu()]
    assert titoli.index("&Partite") == titoli.index("&Polisportive") + 1
    voci = {voce[0]: voce[1] for _t, elenco in finestra.voci_menu() for voce in filter(None, elenco)}
    assert voci["&Amichevole..."] == "Ctrl+O" and voci["&Punto successivo"] == "F8"
    assert voci["&Resto dell'incontro"] == "Ctrl+F8" and voci["&Salva la cronaca..."] == "Ctrl+Shift+O"
    guida = testi.guida(finestra.voci_guida())
    assert "Menu Partite: Amichevole, Ctrl+O; Punto successivo, F8; Resto dell'incontro, Ctrl+F8; Salva la cronaca, Ctrl+Maiusc+O." in guida


def test_senza_un_amichevole_i_comandi_lo_dicono(finestra, suonati):
    for comando in (finestra.punto_successivo, finestra.resto_dell_incontro, finestra.salva_cronaca):
        finestra.vista.ChangeValue("")
        comando()
        assert finestra.vista.GetValue() == testi.NESSUNA_AMICHEVOLE
    assert suonati == ["nessun_incontro"] * 3
    assert finestra.ultimo_evento == "nessuna amichevole"


def test_il_punto_per_punto_fino_alla_fine(finestra, suonati, monkeypatch, cartella_di_prova):
    mondo = finestra.mondo
    scelte = Scelte(monkeypatch, 2, 7)
    finestra.amichevole()
    # Il tuo giocatore si sceglie fra i tuoi tesserati, l'avversario fra tutti gli altri.
    assert scelte.elenchi[0] == [2, 5, 9]
    assert scelte.elenchi[1] == sorted(gid for gid in mondo.giocatori if gid != 2)
    assert scelte.titoli == ["Amichevole, il tuo giocatore di Club Di Prova", f"Amichevole, l'avversario di {testi.nome_completo(mondo.giocatori[2])}"]
    assert suonati == ["dialogo_amichevole", "dialogo_avversario", "dialogo_opzioni_amichevole", "amichevole_al_via"]
    v = finestra.incontro
    primo = finestra.vista.GetValue()
    assert primo.startswith("Inizio dell'incontro: ") and primo.endswith(testi.AVANTI_UN_PUNTO)
    assert finestra.ultimo_evento == "amichevole al via"
    # L'incontro è già giocato, registrato e salvato: il diario e il salvataggio lo sanno.
    assert mondo.giocatori[2].partitevinte + mondo.giocatori[2].partiteperse == 1
    salvati = {g["id"]: g for g in archivio.leggi(cartella_di_prova / FILE_MONDO)["mondo"]["giocatori"]}
    assert salvati[2]["ultima_amichevole"] == salvati[7]["ultima_amichevole"] == mondo.datetime_corrente_simulazione.isoformat()
    testi_visti = [primo]
    while not v.finita:
        finestra.punto_successivo()
        testi_visti.append(finestra.vista.GetValue())
    assert len(testi_visti) == len(v.testi) == v.risultato.incontro.punti_giocati + 2
    assert all(t.startswith("Set ") for t in testi_visti[1:-1])
    assert finestra.ultimo_evento.startswith("vince ")
    ultimo = testi_visti[-1]
    # Anche l'ultimo testo, come vuole D17, si apre con il dato essenziale: il risultato, non il fischio.
    assert ultimo.splitlines()[0] == testi.risultato_amichevole(v.risultato, mondo) and ultimo.startswith("Vince ")
    assert "Fine dell'incontro: vince " in ultimo and "Punti allenamento: " in ultimo and ultimo.endswith(testi.SALVA_LA_CRONACA)
    assert not any("\n\n" in t for t in testi_visti)
    assert suonati[4:] == ["punto_successivo"] * (len(v.testi) - 2) + [_esito_atteso(finestra, 2)]
    # Finito l'incontro, F8 e Ctrl+F8 lo dicono.
    finestra.punto_successivo()
    assert finestra.vista.GetValue().startswith("L'amichevole è già tutta mostrata. Vince ")
    finestra.resto_dell_incontro()
    assert suonati[-2:] == ["incontro_finito", "incontro_finito"]
    # La cronaca si salva nella cartella delle cronache, al livello scelto.
    finestra.salva_cronaca()
    file = list((cartella_di_prova / CARTELLA_CRONACHE).iterdir())
    assert len(file) == 1
    assert finestra.vista.GetValue() == f"La cronaca normale dell'amichevole fra {v.nomi['A'].testo} e {v.nomi['B'].testo} è nel file {file[0]}."
    assert suonati[-1] == "cronaca_salvata" and finestra.ultimo_evento == "cronaca salvata"
    scritto = file[0].read_text(encoding="utf-8")
    assert scritto.startswith(f"Cronaca dell'incontro fra {v.nomi['A'].testo} e {v.nomi['B'].testo}, singolare al meglio dei 3 set.")
    assert "Il seme della partita è " in scritto and "Fine dell'incontro: vince " in scritto and "\n\n" not in scritto


def test_un_amichevole_al_giorno_nella_finestra(finestra, suonati, monkeypatch):
    mondo = finestra.mondo
    Scelte(monkeypatch, 5, 9, modo=RISULTATO)
    finestra.amichevole()
    # Fra due tuoi tesserati l'esito è la stretta di mano.
    assert suonati[-1] == "amichevole_fra_tuoi"
    assert finestra.incontro.finita
    testo = finestra.vista.GetValue()
    assert testo.startswith("Vince ") and testo.splitlines()[1].startswith("Punti allenamento: ") and testo.endswith(testi.SALVA_LA_CRONACA)
    # Chi ha giocato oggi non compare più negli elenchi.
    scelte = Scelte(monkeypatch, 2, 3, annulla_opzioni=True)
    finestra.amichevole()
    assert scelte.elenchi == [[2], sorted(gid for gid in mondo.giocatori if gid not in (2, 5, 9))]
    assert suonati[-2:] == ["dialogo_opzioni_amichevole", "annullato"]
    assert mondo.giocatori[2].partitevinte + mondo.giocatori[2].partiteperse == 0
    # Se oggi non può giocare nessuno dei tuoi, la vista lo dice.
    mondo.giocatori[2].ultima_amichevole = mondo.datetime_corrente_simulazione
    finestra.amichevole()
    assert finestra.vista.GetValue().startswith("Oggi nessun tesserato di Club Di Prova può giocare un'amichevole: ognuno ne gioca al massimo una per giorno simulato")
    assert suonati[-1] == "nessun_giocatore_oggi"
    # Il giorno dopo si torna a giocare; ma se tutti gli altri sono fermi, manca l'avversario.
    mondo.datetime_corrente_simulazione += datetime.timedelta(days=1)
    for g in mondo.giocatori.values():
        if g.id != 2:
            g.ultima_amichevole = mondo.datetime_corrente_simulazione
    scelte = Scelte(monkeypatch, 2, 3)
    finestra.amichevole()
    assert scelte.elenchi == [[2]]
    assert finestra.vista.GetValue().startswith(f"Oggi nessun altro giocatore può giocare un'amichevole contro {testi.nome_completo(mondo.giocatori[2])}")
    assert suonati[-2:] == ["dialogo_amichevole", "nessun_giocatore_oggi"]


def test_tutta_subito_e_il_resto_dell_incontro(finestra, suonati, monkeypatch, cartella_di_prova):
    mondo = finestra.mondo
    Scelte(monkeypatch, 9, 11, set_scelti=1, modo=TUTTA, livello=SINTETICA)
    finestra.amichevole()
    v = finestra.incontro
    assert v.risultato.formato.set_al_meglio == 5 and v.livello == cronaca.SINTETICA
    testo = finestra.vista.GetValue()
    assert testo.startswith("Vince ") and "Amichevole al meglio dei 5 set." in testo.splitlines()[0]
    assert "Battuta di " in testo and "\n\n" not in testo
    assert suonati[-1] == _esito_atteso(finestra, 9)
    finestra.punto_successivo()
    assert suonati[-1] == "incontro_finito"
    finestra.salva_cronaca()
    file = next((cartella_di_prova / CARTELLA_CRONACHE).iterdir())
    assert "La cronaca sintetica dell'amichevole" in finestra.vista.GetValue()
    assert "Battuta di " in file.read_text(encoding="utf-8")
    # Un'altra amichevole, il giorno dopo: due punti con F8, poi tutto il resto con Ctrl+F8.
    mondo.datetime_corrente_simulazione += datetime.timedelta(days=1)
    Scelte(monkeypatch, 2, 11, livello=TECNICA)
    finestra.amichevole()
    finestra.punto_successivo()
    finestra.punto_successivo()
    assert finestra.ultimo_evento == "amichevole, punto 2"
    finestra.resto_dell_incontro()
    v = finestra.incontro
    testo = finestra.vista.GetValue()
    assert v.finita and testo.startswith("Vince ") and "(secondo " in testo
    assert testo.splitlines()[0] == testi.risultato_amichevole(v.risultato, mondo)
    assert suonati[-4:] == ["punto_successivo", "punto_successivo", "resto_dell_incontro", _esito_atteso(finestra, 2)]


def test_la_cronaca_che_non_si_salva_e_il_mondo_che_non_si_salva(finestra, suonati, monkeypatch):
    def guasto(*_args, **_kwargs):
        raise OSError("disco pieno")

    monkeypatch.setattr(archivio, "scrivi", guasto)
    Scelte(monkeypatch, 2, 4)
    finestra.amichevole()
    assert suonati[-2:] == ["amichevole_al_via", "salvataggio_non_riuscito"]
    assert finestra.vista.GetValue().endswith("Salvataggio non riuscito: disco pieno. Il salvataggio precedente è rimasto com'era.")
    monkeypatch.setattr(cronaca, "salva", guasto)
    finestra.salva_cronaca()
    assert finestra.vista.GetValue() == "La cronaca dell'amichevole non si è potuta salvare: disco pieno."
    assert suonati[-1] == "cronaca_non_salvata"


def test_tutta_subito_col_mondo_che_non_si_salva(finestra, suonati, monkeypatch):
    def guasto(*_args, **_kwargs):
        raise OSError("disco pieno")

    monkeypatch.setattr(archivio, "scrivi", guasto)
    Scelte(monkeypatch, 2, 4, modo=TUTTA)
    finestra.amichevole()
    v = finestra.incontro
    righe = finestra.vista.GetValue().splitlines()
    # Il perché del salvataggio non riuscito viene subito dopo il risultato, non in fondo alla cronaca intera.
    testa = testi.amichevole_solo_risultato(v.risultato, finestra.mondo).splitlines()
    assert righe[:len(testa)] == testa
    assert righe[len(testa)] == "Salvataggio non riuscito: disco pieno. Il salvataggio precedente è rimasto com'era."
    assert righe[len(testa) + 1:] == testi.cronaca_amichevole(v.risultato, v.nomi, v.livello).splitlines()
    assert len(righe) > len(testa) + 20
    assert suonati[-2:] == [_esito_atteso(finestra, 2), "salvataggio_non_riuscito"]


@pytest.mark.parametrize("livello", [SINTETICA, TECNICA])
def test_l_ultimo_punto_si_apre_col_risultato_a_ogni_livello(finestra, monkeypatch, livello):
    Scelte(monkeypatch, 2, 7, livello=livello)
    finestra.amichevole()
    v = finestra.incontro
    while not v.finita:
        finestra.punto_successivo()
    assert finestra.vista.GetValue().splitlines()[0] == testi.risultato_amichevole(v.risultato, finestra.mondo)


def test_la_cronaca_salvata_dopo_un_avanzamento_dice_quando_si_e_giocata(finestra, monkeypatch, cartella_di_prova):
    mondo = finestra.mondo
    Scelte(monkeypatch, 2, 7, modo=RISULTATO)
    prima = adesso()
    finestra.amichevole()
    dopo = adesso()
    v = finestra.incontro
    giorno = mondo.datetime_corrente_simulazione
    assert prima <= v.istante <= dopo and v.data_simulata == giorno
    assert mondo.giocatori[2].ultima_amichevole == mondo.giocatori[7].ultima_amichevole == giorno
    # Prima di salvare la cronaca il mondo passa al giorno dopo, e l'ora reale va avanti di nove ore.
    mondo.datetime_corrente_simulazione += datetime.timedelta(days=1)
    monkeypatch.setattr(partita, "adesso", lambda: dopo + datetime.timedelta(hours=9))
    finestra.salva_cronaca()
    file = next((cartella_di_prova / CARTELLA_CRONACHE).iterdir())
    assert file.name.startswith(f"{v.istante:%Y-%m-%d %H.%M.%S} ")
    seconda = file.read_text(encoding="utf-8").splitlines()[1]
    assert seconda == cronaca.intestazione(v.risultato, v.nomi, v.istante, giorno)[1]
    assert seconda.endswith(f", data simulata {cronaca.data_a_parole(giorno)}.")
    assert f"alle {v.istante:%H:%M}," in seconda


def test_senza_polisportiva_o_senza_tesserati(finestra, suonati):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva
    for gid in list(poli.tesserati):
        mondo.svincola(poli, mondo.giocatori[gid])
    finestra.amichevole()
    assert finestra.vista.GetValue() == "Club Di Prova non ha tesserati da far giocare."
    mondo.miapolisportiva_attiva = None
    finestra.amichevole()
    assert suonati == ["rosa_vuota", "nessuna_polisportiva_attiva"]


def test_il_dialogo_delle_opzioni(app_wx, mondo):
    dialogo = dialoghi.OpzioniAmichevole(None, mondo, mondo.giocatori[2], mondo.giocatori[3])
    try:
        assert dialogo.set.GetStringSelection() == "Al meglio di 3 set"
        assert dialogo.modo.GetStringSelection() == "Un punto alla volta"
        assert dialogo.livello.GetStringSelection() == "Normale"
        dialogo.conferma()
        assert dialogo.risultato == (3, dialoghi.UN_PUNTO_ALLA_VOLTA, cronaca.NORMALE)
        dialogo.set.SetSelection(1)
        dialogo.modo.SetSelection(2)
        dialogo.livello.SetSelection(2)
        dialogo.conferma()
        assert dialogo.risultato == (5, dialoghi.SOLO_IL_RISULTATO, cronaca.TECNICA)
        assert dialogo.GetReturnCode() == wx.ID_OK
    finally:
        dialogo.Destroy()
