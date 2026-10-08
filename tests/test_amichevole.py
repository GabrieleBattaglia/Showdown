"""
Test dell'amichevole nella finestra, tappe 9 e 10, sul desktop nascosto del conftest e senza suonare:
il menu Partite, che con la decisione D29 non ha più F8 e Ctrl+F8; il primo giocatore scelto fra i
tuoi, l'avversario fra tutti gli altri, chi ha già giocato oggi che non compare; le opzioni, con i
due modi Assisti e Vai alla fine e la migrazione di quelli ricordati dalla tappa 9; la finestra dal
vivo, che si apre con l'incontro già registrato e salvato, e la vista che dopo Vai alla fine o il
risultato mostra lo stesso testo di Vai alla fine, mentre dopo Esc, decisione D30, non svela il
risultato e dice dove leggerlo, senza il suono dell'esito; la velocità di gioco passata al motore e
ricordata; il salvataggio della cronaca in una cartella temporanea, con il momento dell'incontro
anche se si salva dopo un avanzamento; il perché di un mondo non salvato prima della cronaca intera;
i suoni di ogni passo. I dialoghi sono sostituiti da risposte scritte, la cassa della partita da una
cassa finta.
"""

import datetime
import json
import random

import pytest
import wx
from aiuti_dal_vivo import CassaFinta, vieta_la_cassa_vera

import archivio
import impostazioni
import partita
import partita_sonora
import testi
from costanti import CARTELLA_CRONACHE, FILE_MONDO
from gui import dal_vivo, dialoghi
from gui.finestra import FinestraPrincipale
from modelli import Polisportiva
from mondo import Mondo
from motore import cronaca
from utilita import adesso, adesso_utc

# Le scelte delle opzioni nell'ordine del dialogo: set, modo di seguire l'incontro, livello.
ASSISTI, FINE = 0, 1
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


@pytest.fixture(autouse=True)
def cassa(monkeypatch):
    """La cassa della partita è finta, e quella vera di Acusticator fa fallire chi la chiama."""
    vieta_la_cassa_vera(monkeypatch)
    finta = CassaFinta()
    monkeypatch.setattr(partita_sonora, "Cassa", lambda: finta)
    return finta


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


def _esce_con_esc(finestra_dal_vivo):
    finestra_dal_vivo.esci(dal_vivo.CON_ESC)


def _va_alla_fine(finestra_dal_vivo):
    """Alt+V, Vai alla fine: la vista mostra il risultato, come dopo Vai alla fine nelle opzioni."""
    finestra_dal_vivo.esci(dal_vivo.ALLA_FINE)


class Scelte:
    """
    Le risposte scritte ai dialoghi dell'amichevole: i due giocatori, le opzioni, e quello che si fa
    nella finestra dal vivo, una funzione che la riceve; in elenchi e titoli restano gli elenchi e i
    titoli dei dialoghi, in iniziali il modo da cui il dialogo delle opzioni è partito.
    """

    def __init__(self, monkeypatch, tuo, avversario, set_scelti=0, modo=FINE, livello=NORMALE, annulla_opzioni=False, nel_vivo=_esce_con_esc):
        self.giocatori = [tuo, avversario]
        self.elenchi = []
        self.titoli = []
        self.opzioni = (set_scelti, modo, livello)
        self.annulla_opzioni = annulla_opzioni
        self.nel_vivo = nel_vivo
        self.iniziali = None
        self.dal_vivo = []
        # Funzioni e non metodi legati: sulla classe del dialogo ricevono il dialogo come primo argomento.
        monkeypatch.setattr(dialoghi.SceltaGiocatore, "ShowModal", lambda dialogo: self.scegli(dialogo))
        monkeypatch.setattr(dialoghi.OpzioniAmichevole, "ShowModal", lambda dialogo: self.opzioni_scelte(dialogo))
        monkeypatch.setattr(dal_vivo.FinestraDalVivo, "ShowModal", lambda dialogo: self.assisti(dialogo))

    def scegli(self, dialogo):
        self.elenchi.append([g.id for g in dialogo.tutti])
        self.titoli.append(dialogo.GetTitle())
        gid = self.giocatori[len(self.elenchi) - 1]
        dialogo.elenco.SetSelection([g.id for g in dialogo.visibili].index(gid))
        dialogo.conferma()
        return wx.ID_OK

    def opzioni_scelte(self, dialogo):
        self.iniziali = dialogo.modo.GetStringSelection()
        if self.annulla_opzioni:
            return wx.ID_CANCEL
        for controllo, scelta in zip((dialogo.set, dialogo.modo, dialogo.livello), self.opzioni, strict=True):
            controllo.SetSelection(scelta)
        dialogo.conferma()
        return wx.ID_OK

    def assisti(self, dialogo):
        self.dal_vivo.append(dialogo)
        self.nel_vivo(dialogo)
        return dialogo.GetReturnCode()


def _esito_atteso(finestra, tuo):
    risultato = finestra.incontro.risultato
    vincitore = risultato.parti[0] if risultato.vincitore == "A" else risultato.parti[1]
    return "amichevole_vinta" if vincitore == tuo else "amichevole_persa"


def _testo_alla_fine(finestra):
    v = finestra.incontro
    return f"{testi.amichevole_solo_risultato(v.risultato, finestra.mondo)}\n{testi.cronaca_amichevole(v.risultato, v.nomi, v.livello)}"


# Il menu.

def test_il_menu_partite_e_la_guida(finestra):
    titoli = [titolo for titolo, _voci in finestra.voci_menu()]
    assert titoli.index("Pa&rtite") == titoli.index("&Polisportive") + 1
    # Ogni titolo della barra ha la sua lettera: Partite usa la R, perché la P è di Polisportive.
    lettere = [titolo[titolo.index("&") + 1].lower() for titolo in titoli]
    assert len(lettere) == len(set(lettere)), lettere
    partite = dict(finestra.voci_menu())["Pa&rtite"]
    assert [(voce[0], voce[1]) for voce in partite if voce] == [("&Amichevole...", "Ctrl+O"), ("&Salva la cronaca", "Ctrl+Shift+O")]
    # F8 e Ctrl+F8 tornano liberi: il punto per punto è diventato la partita dal vivo.
    tasti = [voce[1] for _t, elenco in finestra.voci_menu() for voce in filter(None, elenco)]
    assert "F8" not in tasti and "Ctrl+F8" not in tasti
    guida = testi.guida(finestra.voci_guida())
    assert "Menu Partite: Amichevole, Ctrl+O; Salva la cronaca, Ctrl+Maiusc+O." in guida
    assert "F8" not in guida and "Punto successivo" not in guida


def test_senza_un_amichevole_salva_la_cronaca_lo_dice(finestra, suonati):
    finestra.salva_cronaca()
    assert finestra.vista.GetValue() == testi.NESSUNA_AMICHEVOLE
    assert suonati == ["nessun_incontro"] and finestra.ultimo_evento == "nessuna amichevole"


# Assisti: la finestra dal vivo.

def test_assisti_apre_la_finestra_dal_vivo_con_l_incontro_gia_registrato(finestra, suonati, monkeypatch, cartella_di_prova, cassa):
    mondo = finestra.mondo
    visto = {}

    def nel_vivo(f):
        # L'incontro è già giocato, registrato e salvato prima che la partita cominci.
        visto["partite"] = mondo.giocatori[2].partitevinte + mondo.giocatori[2].partiteperse
        visto["salvati"] = {g["id"]: g for g in archivio.leggi(cartella_di_prova / FILE_MONDO)["mondo"]["giocatori"]}
        visto["velocita"] = f.velocita
        f.al_prosegui()
        f.al_prosegui()
        f.al_prosegui()
        f.esci(dal_vivo.CON_ESC)

    scelte = Scelte(monkeypatch, 2, 7, modo=ASSISTI, nel_vivo=nel_vivo)
    finestra.amichevole()
    assert scelte.elenchi[0] == [2, 5, 9]
    assert scelte.elenchi[1] == sorted(gid for gid in mondo.giocatori if gid != 2)
    assert len(scelte.dal_vivo) == 1 and scelte.dal_vivo[0].uscita == dal_vivo.CON_ESC
    # La velocità di gioco predefinita, decisione D30, è 4.
    assert visto["partite"] == 1 and visto["velocita"] == 4
    assert visto["salvati"][2]["ultima_amichevole"] == visto["salvati"][7]["ultima_amichevole"] == mondo.datetime_corrente_simulazione.isoformat()
    # Il gemello rigioca lo stesso incontro registrato.
    assert scelte.dal_vivo[0].cronologia.incontro.seme == finestra.incontro.risultato.seme
    # Uscendo con Esc il risultato non si svela, né con il suono dell'esito né nella vista o nella barra:
    # si sente soltanto il suono dell'amichevole registrata.
    assert suonati == ["dialogo_amichevole", "dialogo_avversario", "dialogo_opzioni_amichevole", "amichevole_al_via", "riscaldamento_saltato",
                       "amichevole_registrata"]
    testo = finestra.vista.GetValue()
    assert testo == testi.amichevole_senza_risultato(finestra.incontro.nomi)
    assert finestra.ultimo_evento == "amichevole registrata"
    assert len(cassa.buffer) == 2 and cassa.accese == 0


def test_esc_non_svela_il_risultato(finestra, suonati, monkeypatch, cartella_di_prova):
    mondo = finestra.mondo
    Scelte(monkeypatch, 2, 7, modo=ASSISTI)
    finestra.amichevole()
    v = finestra.incontro
    testo = finestra.vista.GetValue()
    risultato = testi.risultato_amichevole(v.risultato, mondo)
    assert risultato not in testo and "Vince" not in testo and "set a" not in testo and "Punti allenamento" not in testo
    assert all(frase not in testo for frase in v.risultato.registrazione)
    assert f"l'amichevole fra {v.nomi['A'].testo} e {v.nomi['B'].testo} è comunque registrata nel mondo" in testo
    assert "\n\n" not in testo and len(testo.splitlines()) == 2
    # I tasti che la vista nomina sono quelli dei menu: il diario del giocatore e la cronaca salvata.
    guida = testi.guida(finestra.voci_guida())
    assert "Ctrl+Maiusc+D" in testo and "Diario del giocatore, Ctrl+Maiusc+D" in guida
    assert "Ctrl+Maiusc+O" in testo and "Salva la cronaca, Ctrl+Maiusc+O" in guida
    # Il risultato c'è davvero dove la vista dice: nel diario dei due giocatori e nella cronaca salvata.
    for gid in (2, 7):
        assert any("l'amichevole contro " in voce["testo"] for voce in mondo.giocatori[gid].diario if "testo" in voce)
    finestra.salva_cronaca()
    assert suonati[-1] == "cronaca_salvata"
    scritto = next((cartella_di_prova / CARTELLA_CRONACHE).iterdir()).read_text(encoding="utf-8")
    assert "Fine dell'incontro: vince " in scritto
    # Nessun suono d'esito, mai: né subito né in coda.
    assert not {"amichevole_vinta", "amichevole_persa", "amichevole_fra_tuoi", "resto_dell_incontro"} & set(suonati)


def test_esc_con_il_mondo_non_salvato(finestra, suonati, monkeypatch):
    # Anche dopo Esc il perché di un salvataggio non riuscito si legge, e si sente, senza svelare il risultato.
    def guasto(*_args, **_kwargs):
        raise OSError("disco pieno")

    monkeypatch.setattr(archivio, "scrivi", guasto)
    Scelte(monkeypatch, 2, 4, modo=ASSISTI)
    finestra.amichevole()
    v = finestra.incontro
    righe = finestra.vista.GetValue().splitlines()
    assert righe == [*testi.amichevole_senza_risultato(v.nomi).splitlines(), "Salvataggio non riuscito: disco pieno. Il salvataggio precedente è rimasto com'era."]
    assert suonati[-3:] == ["amichevole_al_via", "amichevole_registrata", "salvataggio_non_riuscito"]


def test_il_risultato_dalla_finestra_dal_vivo(finestra, suonati, monkeypatch, cassa):
    # A incontro finito il pulsante porta al risultato, come prova test_dal_vivo: la vista lo mostra
    # come Vai alla fine, e l'esito suona.
    Scelte(monkeypatch, 2, 7, modo=ASSISTI, nel_vivo=lambda f: f.esci(dal_vivo.AL_RISULTATO))
    finestra.amichevole()
    assert finestra.vista.GetValue() == _testo_alla_fine(finestra)
    assert suonati[-1] == _esito_atteso(finestra, 2) and finestra.ultimo_evento.startswith("vince ")


def test_vai_alla_fine_dalla_finestra_dal_vivo(finestra, suonati, monkeypatch, cassa):
    def nel_vivo(f):
        f.al_prosegui()
        f.fino_a_fine_set()
        f.alla_fine.Command(wx.CommandEvent(wx.wxEVT_BUTTON, f.alla_fine.GetId()))

    Scelte(monkeypatch, 2, 7, modo=ASSISTI, nel_vivo=nel_vivo)
    finestra.amichevole()
    # Alt+F mentre suona il riscaldamento ha il suo suono; poi i guizzi del salto alla fine, e l'esito; il suono della partita è fermo.
    assert suonati[-4:] == ["amichevole_al_via", "dal_vivo_fino_a_fine_set", "resto_dell_incontro", _esito_atteso(finestra, 2)]
    assert finestra.vista.GetValue() == _testo_alla_fine(finestra)
    assert cassa.accese == 0


def test_la_velocita_cambiata_dal_vivo_si_ricorda(finestra, suonati, monkeypatch, cartella_di_prova):
    def nel_vivo(f):
        for _ in range(2):
            evento = wx.KeyEvent(wx.wxEVT_CHAR_HOOK)
            evento.SetKeyCode(ord("+"))
            evento.SetUnicodeKey(ord("+"))
            f._tasto(evento)
        f.esci(dal_vivo.CON_ESC)

    Scelte(monkeypatch, 2, 7, modo=ASSISTI, nel_vivo=nel_vivo)
    finestra.amichevole()
    assert suonati.count("dal_vivo_piu_veloce") == 2
    # Dalla predefinita, 4, a 6.
    assert finestra.impostazioni["velocita_gioco"] == 6 and impostazioni.carica()["velocita_gioco"] == 6
    # La prossima partita dal vivo parte a quella velocità, e il motore la usa.
    finestra.mondo.datetime_corrente_simulazione += datetime.timedelta(days=1)
    visto = {}

    def guarda(f):
        f.al_prosegui()
        visto["velocita"] = (f.velocita, f.cronologia.incontro.regia.velocita)
        f.esci(dal_vivo.CON_ESC)

    Scelte(monkeypatch, 2, 7, modo=ASSISTI, nel_vivo=guarda)
    finestra.amichevole()
    assert visto["velocita"] == (6, 6.0)


def test_l_amichevole_da_assistere_nel_motore(mondo):
    motore = partita.MotorePartita(mondo)
    risultato, gemello = motore.amichevole_da_assistere(2, 7, 3, seme=99, velocita=5)
    assert risultato.seme == gemello.seme == 99 and gemello.regia.velocita == 5.0
    assert risultato.registrazione and mondo.giocatori[7].ultima_amichevole == mondo.datetime_corrente_simulazione
    # Il gemello nasce prima della registrazione e rigioca gli stessi punti, a un'altra velocità.
    rigiocato = gemello.gioca()
    assert rigiocato.set == risultato.set and [p.esito for p in rigiocato.punti] == [p.esito for p in risultato.punti]
    assert rigiocato.durata_simulata < risultato.durata_simulata
    with pytest.raises(ValueError, match="già giocato"):
        motore.amichevole_da_assistere(2, 5, 3)


# Vai alla fine.

def test_vai_alla_fine_mostra_risultato_e_cronaca(finestra, suonati, monkeypatch, cartella_di_prova, cassa):
    mondo = finestra.mondo
    scelte = Scelte(monkeypatch, 2, 7, modo=FINE)
    finestra.amichevole()
    assert scelte.dal_vivo == [] and cassa.buffer == []
    assert scelte.titoli == ["Amichevole, il tuo giocatore di Club Di Prova", f"Amichevole, l'avversario di {testi.nome_completo(mondo.giocatori[2])}"]
    assert suonati == ["dialogo_amichevole", "dialogo_avversario", "dialogo_opzioni_amichevole", _esito_atteso(finestra, 2)]
    testo = finestra.vista.GetValue()
    assert testo == _testo_alla_fine(finestra)
    assert testo.splitlines()[0] == testi.risultato_amichevole(finestra.incontro.risultato, mondo)
    assert "Battuta destra di " in testo or "Battuta sinistra di " in testo
    salvati = {g["id"]: g for g in archivio.leggi(cartella_di_prova / FILE_MONDO)["mondo"]["giocatori"]}
    assert salvati[2]["ultima_amichevole"] == mondo.datetime_corrente_simulazione.isoformat()


def test_un_amichevole_al_giorno_nella_finestra(finestra, suonati, monkeypatch):
    mondo = finestra.mondo
    Scelte(monkeypatch, 5, 9)
    finestra.amichevole()
    # Fra due tuoi tesserati l'esito è la stretta di mano.
    assert suonati[-1] == "amichevole_fra_tuoi"
    testo = finestra.vista.GetValue()
    assert testo.startswith("Vince ") and testo.splitlines()[1].startswith("Punti allenamento: ")
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


def test_al_meglio_dei_5_e_la_cronaca_salvata(finestra, suonati, monkeypatch, cartella_di_prova):
    Scelte(monkeypatch, 9, 11, set_scelti=1, modo=FINE, livello=SINTETICA)
    finestra.amichevole()
    v = finestra.incontro
    assert v.risultato.formato.set_al_meglio == 5 and v.livello == cronaca.SINTETICA
    testo = finestra.vista.GetValue()
    assert testo.startswith("Vince ") and "Amichevole al meglio dei 5 set." in testo.splitlines()[0]
    assert "Battuta di " in testo and "\n\n" not in testo
    assert suonati[-1] == _esito_atteso(finestra, 9)
    finestra.salva_cronaca()
    file = list((cartella_di_prova / CARTELLA_CRONACHE).iterdir())
    assert len(file) == 1
    assert finestra.vista.GetValue() == f"La cronaca sintetica dell'amichevole fra {v.nomi['A'].testo} e {v.nomi['B'].testo} è nel file {file[0]}."
    assert suonati[-1] == "cronaca_salvata" and finestra.ultimo_evento == "cronaca salvata"
    scritto = file[0].read_text(encoding="utf-8")
    assert scritto.startswith(f"Cronaca dell'incontro fra {v.nomi['A'].testo} e {v.nomi['B'].testo}, singolare al meglio dei 5 set.")
    assert "Il seme della partita è " in scritto and "Fine dell'incontro: vince " in scritto and "\n\n" not in scritto


@pytest.mark.parametrize("modo", [ASSISTI, FINE])
def test_il_mondo_che_non_si_salva_e_la_cronaca_che_non_si_salva(finestra, suonati, monkeypatch, modo):
    def guasto(*_args, **_kwargs):
        raise OSError("disco pieno")

    monkeypatch.setattr(archivio, "scrivi", guasto)
    # Dalla finestra dal vivo si esce con Alt+V, che mostra il risultato; Esc ha la sua prova.
    Scelte(monkeypatch, 2, 4, modo=modo, nel_vivo=_va_alla_fine)
    finestra.amichevole()
    v = finestra.incontro
    righe = finestra.vista.GetValue().splitlines()
    # Il perché del salvataggio non riuscito viene subito dopo il risultato, non in fondo alla cronaca intera.
    testa = testi.amichevole_solo_risultato(v.risultato, finestra.mondo).splitlines()
    assert righe[:len(testa)] == testa
    assert righe[len(testa)] == "Salvataggio non riuscito: disco pieno. Il salvataggio precedente è rimasto com'era."
    assert righe[len(testa) + 1:] == testi.cronaca_amichevole(v.risultato, v.nomi, v.livello).splitlines()
    assert suonati[-2:] == [_esito_atteso(finestra, 2), "salvataggio_non_riuscito"]
    monkeypatch.setattr(cronaca, "salva", guasto)
    finestra.salva_cronaca()
    assert finestra.vista.GetValue() == "La cronaca dell'amichevole non si è potuta salvare: disco pieno."
    assert suonati[-1] == "cronaca_non_salvata"


@pytest.mark.parametrize("livello", [SINTETICA, TECNICA])
def test_il_testo_si_apre_col_risultato_a_ogni_livello(finestra, monkeypatch, livello):
    Scelte(monkeypatch, 2, 7, modo=ASSISTI, livello=livello, nel_vivo=_va_alla_fine)
    finestra.amichevole()
    assert finestra.vista.GetValue().splitlines()[0] == testi.risultato_amichevole(finestra.incontro.risultato, finestra.mondo)


def test_la_cronaca_salvata_dopo_un_avanzamento_dice_quando_si_e_giocata(finestra, monkeypatch, cartella_di_prova):
    mondo = finestra.mondo
    Scelte(monkeypatch, 2, 7)
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


# Il dialogo delle opzioni e la migrazione.

def test_il_dialogo_delle_opzioni(app_wx, mondo):
    dialogo = dialoghi.OpzioniAmichevole(None, mondo, mondo.giocatori[2], mondo.giocatori[3])
    try:
        assert dialogo.set.GetStringSelection() == "Al meglio di 3 set"
        assert [dialogo.modo.GetString(i) for i in range(dialogo.modo.GetCount())] == ["Assisti", "Vai alla fine"]
        assert dialogo.modo.GetStringSelection() == "Assisti"
        assert dialogo.livello.GetStringSelection() == "Normale"
        dialogo.conferma()
        assert dialogo.risultato == (3, dialoghi.ASSISTI, cronaca.NORMALE)
        dialogo.set.SetSelection(1)
        dialogo.modo.SetSelection(1)
        dialogo.livello.SetSelection(2)
        dialogo.conferma()
        assert dialogo.risultato == (5, dialoghi.VAI_ALLA_FINE, cronaca.TECNICA)
        assert dialogo.GetReturnCode() == wx.ID_OK
    finally:
        dialogo.Destroy()


def test_le_opzioni_dell_amichevole_si_ricordano(app_wx, mondo):
    # Il dialogo riparte dalle ultime scelte, e le impostazioni le conservano anche dopo la chiusura.
    dialogo = dialoghi.OpzioniAmichevole(None, mondo, mondo.giocatori[2], mondo.giocatori[3], (5, dialoghi.VAI_ALLA_FINE, cronaca.SINTETICA))
    try:
        assert dialogo.set.GetStringSelection() == "Al meglio di 5 set"
        assert dialogo.modo.GetStringSelection() == "Vai alla fine"
        assert dialogo.livello.GetStringSelection() == "Sintetica"
    finally:
        dialogo.Destroy()
    salvate = impostazioni.valide({"amichevole_set": 5, "amichevole_modo": "fine", "amichevole_livello": "tecnica"})
    assert (salvate["amichevole_set"], salvate["amichevole_modo"], salvate["amichevole_livello"]) == (5, "fine", "tecnica")
    rovinate = impostazioni.valide({"amichevole_set": 4, "amichevole_modo": "boh", "amichevole_livello": True})
    assert (rovinate["amichevole_set"], rovinate["amichevole_modo"], rovinate["amichevole_livello"]) == (3, "assisti", "normale")
    assert set(impostazioni.MODI_DELL_AMICHEVOLE) == {chiave for chiave, _nome in dialoghi.MODI_DI_SEGUIRE}
    assert set(impostazioni.LIVELLI_DELL_AMICHEVOLE) == {chiave for chiave, _nome in dialoghi.LIVELLI_DI_CRONACA}


@pytest.mark.parametrize(("di_prima", "adesso_vale"), [("punto", "assisti"), ("tutta", "fine"), ("risultato", "fine"), ("assisti", "assisti"),
                                                      ("fine", "fine"), (None, "assisti"), (["punto"], "assisti")])
def test_i_modi_ricordati_dalla_tappa_9_si_migrano(di_prima, adesso_vale):
    assert impostazioni.valide({"amichevole_modo": di_prima})["amichevole_modo"] == adesso_vale


def test_il_file_delle_impostazioni_di_prima_si_migra(finestra, monkeypatch, cartella_di_prova):
    # Il file scritto dalla tappa 9, con un punto alla volta: il dialogo parte da Assisti, e il file si riscrive migrato.
    (cartella_di_prova / impostazioni.FILE_IMPOSTAZIONI).write_text(json.dumps({**impostazioni.PREDEFINITE, "amichevole_modo": "tutta"}), encoding="utf-8")
    finestra.impostazioni = impostazioni.carica()
    assert finestra.impostazioni["amichevole_modo"] == "fine"
    scelte = Scelte(monkeypatch, 2, 7, modo=ASSISTI)
    finestra.amichevole()
    assert scelte.iniziali == "Vai alla fine"
    assert json.loads((cartella_di_prova / impostazioni.FILE_IMPOSTAZIONI).read_text(encoding="utf-8"))["amichevole_modo"] == "assisti"
