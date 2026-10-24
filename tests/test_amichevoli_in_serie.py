"""
Test di Gioca tutte le amichevoli, richiesta di Gabriele del 24 ottobre 2026, dal collaudo di gioco, sul desktop nascosto del
conftest e senza suonare: la scelta dell'avversario nel raggio di 15 classi, in su o in giù, fuori dalla stessa polisportiva e
fra chi oggi può giocare; nessun avversario due volte e nessuno dei tuoi due volte, anche quando un tuo di un'altra polisportiva
fa da avversario; tutte le polisportive, nell'ordine dei nomi; nessun avversario nel raggio; nessuno da far giocare; il
salvataggio, anche quando non riesce; le righe, i totali e il plurale giusto; le voci del menu Partite, col nome della
polisportiva attiva che segue i cambi; i suoni di ogni evento, con l'esito che aspetta la fine del suono dell'avvio. La classe,
dove la prova deve deciderla, la dà una funzione finta.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import datetime
import random
import types

import pytest
import wx
from aiuti_dal_vivo import vieta_la_cassa_vera

import archivio
import classe
import suoni
import testi
from costanti import FILE_MONDO, RAGGIO_CLASSI_AMICHEVOLI
from gui import finestra as finestra_modulo
from gui.finestra import FinestraPrincipale
from modelli import Polisportiva
from mondo import Mondo
from partita import MotorePartita, VoceDellaSerie
from utilita import adesso, adesso_utc

PRIMA, SECONDA = "Magnavacca", "TuratiBoys"


@pytest.fixture(autouse=True)
def nessuna_cassa(monkeypatch):
    """La cassa vera di Acusticator fa fallire chi la chiama: qui non si apre mai la finestra dal vivo."""
    vieta_la_cassa_vera(monkeypatch)


@pytest.fixture
def mondo():
    """Quaranta giocatori e due polisportive tue: Magnavacca dal numero 1 all'8, attiva, e TuratiBoys dal 9 al 15."""
    random.seed(24)
    ora = adesso()
    m = Mondo()
    m.datetime_corrente_simulazione = ora
    m.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=2)
    m.crea_giocatori_casuali(40, ora)
    for nome, ids in ((PRIMA, range(1, 9)), (SECONDA, range(9, 16))):
        p = Polisportiva(nome, None, ora)
        m.polisportive[nome] = p
        for gid in ids:
            g = m.giocatori[gid]
            if g.appartenenza != "*":
                m._lascia(m.polisportive[g.appartenenza], g)
            m._tessera(p, g, ora)
    m.miapolisportiva_attiva = m.polisportive[PRIMA]
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


def _livelli_finti(monkeypatch, livelli, altrimenti=50):
    """La classe di ogni giocatore dal dizionario dei livelli, per numero; chi non c'è ha il livello altrimenti."""
    def finta(g):
        n = livelli.get(g.id, altrimenti)
        return classe.Classe(classe.codice(n), n, None)

    monkeypatch.setattr(classe, "classe", finta)


class CasoCheRegistra:
    """
    Al posto di random: ricorda ogni elenco di candidati, ciascuno col livello della sua classe nel momento della scelta, e
    sceglie il primo, o il primo che piace a preferito.
    """

    def __init__(self, preferito=None):
        self.elenchi = []
        self.preferito = preferito

    def choice(self, candidati):
        self.elenchi.append([(g, classe.classe(g).livello) for g in candidati])
        return next((g for g in candidati if self.preferito and self.preferito(g)), candidati[0])


def _partite(g):
    return g.partitevinte + g.partiteperse


def _serie(mondo, nomi, caso=random):
    motore = MotorePartita(mondo)
    return motore.amichevoli_in_serie(motore.da_far_giocare([mondo.polisportive[n] for n in nomi]), 3, caso)


# La scelta dell'avversario.

def test_la_scelta_nel_raggio(mondo, monkeypatch):
    # Il tuo giocatore al livello 50, F0: dentro chi sta da 35 a 65, D5 e G5 compresi, anche se è di un'altra tua polisportiva;
    # fuori il 34 e il 66, il compagno di squadra al suo stesso livello e chi oggi ha già giocato.
    oggi = mondo.datetime_corrente_simulazione
    liberi = sorted(gid for gid, g in mondo.giocatori.items() if g.appartenenza == "*")
    dentro_basso, dentro_alto, fuori_basso, fuori_alto, impegnato = liberi[:5]
    livelli = dict.fromkeys(mondo.giocatori, 90)
    livelli.update({1: 50, 2: 50, 9: 50, dentro_basso: 35, dentro_alto: 65, fuori_basso: 34, fuori_alto: 66, impegnato: 50})
    mondo.giocatori[impegnato].ultimo_impegno = oggi
    motore = MotorePartita(mondo)
    candidati = motore.avversari_nel_raggio(mondo.giocatori[1], mondo.polisportive[PRIMA], dict(livelli))
    assert [g.id for g in candidati] == sorted([9, dentro_basso, dentro_alto])
    assert RAGGIO_CLASSI_AMICHEVOLI == 15


def test_le_serie_scelgono_sempre_nel_raggio_e_fuori_dalla_polisportiva(mondo):
    # Con le classi vere: ogni elenco di candidati sta nel raggio del tuo giocatore e non ha nessuno della sua polisportiva, e
    # l'avversario scelto è uno di loro. Che l'elenco li abbia tutti lo prova test_la_scelta_nel_raggio.
    caso = CasoCheRegistra()
    serie = _serie(mondo, (PRIMA, SECONDA), caso)
    giocate = testi.amichevoli_giocate(serie)
    assert len(giocate) >= 5 and len(giocate) == len(caso.elenchi)
    polisportiva = {v.tuo.id: p for p, voci in serie for v in voci}
    for v, candidati in zip(giocate, caso.elenchi, strict=True):
        p = polisportiva[v.tuo.id]
        assert v.avversario in [g for g, _livello in candidati] and v.avversario.appartenenza != p.nome
        assert abs(v.livello_avversario - v.livello_tuo) <= RAGGIO_CLASSI_AMICHEVOLI
        for g, livello in candidati:
            assert g.id not in p.tesserati and g.appartenenza != p.nome
            assert abs(livello - v.livello_tuo) <= RAGGIO_CLASSI_AMICHEVOLI


def test_nessun_avversario_gioca_due_volte(mondo):
    prima = {gid: _partite(g) for gid, g in mondo.giocatori.items()}
    serie = _serie(mondo, (PRIMA, SECONDA))
    giocate = testi.amichevoli_giocate(serie)
    coinvolti = [g.id for v in giocate for g in (v.tuo, v.avversario)]
    assert len(coinvolti) == len(set(coinvolti))
    oggi = mondo.datetime_corrente_simulazione
    for gid, g in mondo.giocatori.items():
        assert _partite(g) - prima[gid] == (1 if gid in coinvolti else 0)
        if gid in coinvolti:
            assert g.ultimo_impegno == oggi


def test_nessuno_dei_tuoi_gioca_due_volte(mondo, monkeypatch):
    # Tutti nel raggio, e per i tesserati di Magnavacca il caso preferisce quelli di TuratiBoys: i sette fanno da avversari ai
    # primi sette, l'ottavo trova un libero, e nel turno di TuratiBoys nessuno gioca di nuovo, ma la sua riga dice l'incontro.
    _livelli_finti(monkeypatch, {})
    prima = {gid: _partite(g) for gid, g in mondo.giocatori.items()}
    serie = _serie(mondo, (PRIMA, SECONDA), CasoCheRegistra(lambda g: g.appartenenza == SECONDA))
    (p1, voci1), (p2, voci2) = serie
    assert (p1.nome, p2.nome) == (PRIMA, SECONDA)
    assert [v.tuo.id for v in voci1] == list(range(1, 9)) and [v.tuo.id for v in voci2] == list(range(9, 16))
    assert [v.avversario.appartenenza == SECONDA for v in voci1] == [True] * 7 + [False]
    assert all(v.gia_giocato for v in voci2) and len(testi.amichevoli_giocate(serie)) == 8
    per_avversario = {v.avversario.id: v for v in voci1}
    for v in voci2:
        andata = per_avversario[v.tuo.id]
        assert (v.avversario, v.risultato, v.punti_tuo, v.punti_avversario) == (andata.tuo, andata.risultato, andata.punti_avversario, andata.punti_tuo)
    assert all(_partite(g) - prima[gid] <= 1 for gid, g in mondo.giocatori.items())
    testo = testi.riepilogo_amichevoli_in_serie(serie, mondo, 3, tutte=True)
    assert testo.count("ha già giocato oggi, da avversario di ") == 7
    # I punti dei due tuoi stanno tutti e due nella riga e nei totali.
    riga = testo.splitlines()[2]
    andata = voci1[0]
    assert f"punti allenamento {testi.punti(andata.punti_tuo)} a {testi.nome_completo(andata.tuo)} e {testi.punti(andata.punti_avversario)} a " in riga
    presi = sum(v.punti_tuo + (v.punti_avversario if i < 7 else 0.0) for i, v in enumerate(voci1))
    assert testo.splitlines()[-1].endswith(f"{testi.quanti_punti(presi, True)} ai tuoi tesserati.")


def test_tutte_le_polisportive(finestra, mondo, suonati, cartella_di_prova):
    # Nell'ordine dei nomi, anche quella senza tesserati e quella dove oggi non gioca nessuno.
    ora = mondo.datetime_corrente_simulazione
    mondo.polisportive["Arcieri"] = Polisportiva("Arcieri", None, ora)
    mondo.polisportive["Zeta"] = zeta = Polisportiva("Zeta", None, ora)
    mondo._tessera(zeta, mondo.giocatori[16], ora)
    mondo.giocatori[16].ultimo_impegno = ora
    finestra._esegui(finestra.amichevoli_di_tutte)
    righe = finestra.vista.GetValue().splitlines()
    assert righe[0].startswith("Tutte le amichevoli di oggi delle tue polisportive, al meglio dei 3 set, contro avversari liberi o di un'altra "
                               "polisportiva, anche tua, con la classe entro 15 livelli da quella del tuo giocatore, in su o in giù.")
    assert righe[1] == "Arcieri non ha tesserati."
    intestazioni = [r for r in righe if r.startswith(("Le amichevoli di ", "Oggi nessun tesserato di "))]
    assert intestazioni == [f"Le amichevoli di {PRIMA}:", f"Le amichevoli di {SECONDA}:", "Oggi nessun tesserato di Zeta può giocare un'amichevole."]
    assert righe.index(f"Le amichevoli di {SECONDA}:") - righe.index(f"Le amichevoli di {PRIMA}:") == 9
    assert righe[-1].startswith("In tutto ") and "\n\n" not in finestra.vista.GetValue()
    assert suonati == ["amichevoli_in_serie", "amichevoli_in_serie_finite"]


# Nessun avversario, nessuno da far giocare.

def test_nessun_avversario_nel_raggio(finestra, mondo, suonati, monkeypatch, cartella_di_prova):
    # Magnavacca tutta ad A1, gli altri a K0: nessuno trova un avversario, nessun incontro, e il mondo non si salva.
    _livelli_finti(monkeypatch, dict.fromkeys(range(1, 9), 1), altrimenti=100)
    finestra._esegui(finestra.amichevoli_dell_attiva)
    righe = finestra.vista.GetValue().splitlines()
    assert len(righe) == 10
    assert righe[1] == f"{testi.nome_completo(mondo.giocatori[1])}, A1: oggi nessun avversario nel raggio, dalla classe A1 alla B6."
    assert righe[-1] == "Nessuna amichevole giocata: oggi nessun avversario nel raggio per 8 tuoi tesserati."
    assert suonati == ["amichevoli_in_serie", "nessun_avversario_nel_raggio"] and finestra.ultimo_evento == "nessun avversario nel raggio"
    assert not (cartella_di_prova / FILE_MONDO).exists()
    assert all(_partite(mondo.giocatori[gid]) == 0 for gid in range(1, 9))


def test_qualcuno_senza_avversario_e_gli_altri_giocano(finestra, mondo, suonati, monkeypatch):
    # Il numero 1 ad A1, gli altri tutti al 50: lui solo resta senza avversario, e lo dicono la sua riga e i totali.
    _livelli_finti(monkeypatch, {1: 1})
    finestra._esegui(finestra.amichevoli_dell_attiva)
    righe = finestra.vista.GetValue().splitlines()
    assert righe[1].endswith(": oggi nessun avversario nel raggio, dalla classe A1 alla B6.")
    assert righe[-1].endswith("; 1 tesserato senza un avversario nel raggio.") and righe[-1].startswith("In tutto 7 amichevoli: ")
    assert suonati == ["amichevoli_in_serie", "amichevoli_in_serie_finite"] and finestra.ultimo_evento == "7 amichevoli in serie"


def test_nessuno_da_far_giocare(finestra, mondo, suonati):
    oggi = mondo.datetime_corrente_simulazione
    for gid in range(1, 9):
        mondo.giocatori[gid].ultimo_impegno = oggi
    finestra._esegui(finestra.amichevoli_dell_attiva)
    assert finestra.vista.GetValue().startswith(f"Oggi nessun tesserato di {PRIMA} può giocare un'amichevole: ognuno gioca al massimo un incontro")
    assert suonati == ["nessuno_per_le_amichevoli_in_serie"] and finestra.ultimo_evento == "nessuno gioca oggi"
    for gid in range(9, 16):
        mondo.giocatori[gid].ultimo_impegno = oggi
    finestra._esegui(finestra.amichevoli_di_tutte)
    assert finestra.vista.GetValue().startswith("Oggi nessun tesserato delle tue polisportive può giocare un'amichevole: ognuno gioca")
    assert suonati == ["nessuno_per_le_amichevoli_in_serie"] * 2


def test_senza_tesserati_senza_attiva_e_senza_polisportive(finestra, mondo, suonati):
    vuota = Polisportiva("Vuota", None, mondo.datetime_corrente_simulazione)
    mondo.polisportive[vuota.nome] = vuota
    mondo.miapolisportiva_attiva = vuota
    finestra._esegui(finestra.amichevoli_dell_attiva)
    assert finestra.vista.GetValue() == "Vuota non ha tesserati da far giocare." and suonati[-1] == "rosa_vuota"
    mondo.miapolisportiva_attiva = None
    finestra._esegui(finestra.amichevoli_dell_attiva)
    assert finestra.vista.GetValue().startswith("Non hai una polisportiva attiva") and suonati[-1] == "nessuna_polisportiva_attiva"
    for p in mondo.polisportive.values():
        p.is_cpu_controlled = True
    finestra._esegui(finestra.amichevoli_di_tutte)
    assert finestra.vista.GetValue() == "Non hai ancora nessuna polisportiva: fondane una con Ctrl+N." and suonati[-1] == "nessuna_polisportiva_tua"


# Il salvataggio e la vista.

def test_il_salvataggio_e_la_vista(finestra, mondo, suonati, cartella_di_prova, monkeypatch):
    # Tutti al livello 50, perché ciascuno dei tuoi trovi l'avversario.
    _livelli_finti(monkeypatch, {})
    finestra.impostazioni["amichevole_set"] = 5
    prima = {gid: mondo.giocatori[gid].punti_allenamento for gid in range(1, 9)}
    finestra._esegui(finestra.amichevoli_dell_attiva)
    testo = finestra.vista.GetValue()
    righe = testo.splitlines()
    assert righe[0] == (f"Tutte le amichevoli di oggi di {PRIMA}, al meglio dei 5 set, contro avversari liberi o di un'altra polisportiva, "
                        "con la classe entro 15 livelli da quella del tuo giocatore, in su o in giù.")
    assert len(righe) == 10 and "\n\n" not in testo and "Fine dell'incontro" not in testo
    salvati = {g["id"]: g for g in archivio.leggi(cartella_di_prova / FILE_MONDO)["mondo"]["giocatori"]}
    oggi = mondo.datetime_corrente_simulazione.isoformat()
    for gid, riga in zip(range(1, 9), righe[1:9], strict=True):
        g = mondo.giocatori[gid]
        assert riga.startswith(f"{testi.nome_completo(g)}, ") and " contro " in riga
        assert salvati[gid]["ultimo_impegno"] == oggi and salvati[gid]["punti_allenamento"] > prima[gid]
        assert any("l'amichevole contro " in voce["testo"] for voce in g.diario if "testo" in voce)
        presi = g.punti_allenamento - prima[gid]
        # Contro uno di TuratiBoys, tuo anche lui, la riga dice i punti di tutti e due.
        assert f"; {testi.quanti_punti(presi, True)}." in riga or f"; punti allenamento {testi.punti(presi)} a {testi.nome_completo(g)} e " in riga
    # Al meglio dei 5: chi vince ha 3 set.
    assert all(" 3 set a " in r or " set a 3 " in r or " si ritira" in r for r in righe[1:9])
    assert righe[-1].startswith("In tutto 8 amichevoli: ") and righe[-1].endswith(" ai tuoi tesserati.")
    assert suonati == ["amichevoli_in_serie", "amichevoli_in_serie_finite"] and finestra.ultimo_evento == "8 amichevoli in serie"
    # La serie non tocca l'ultimo incontro di Salva la cronaca, e lo stesso giorno non si rigioca.
    assert finestra.incontro is None
    finestra._esegui(finestra.amichevoli_dell_attiva)
    assert suonati[-1] == "nessuno_per_le_amichevoli_in_serie"


def test_il_salvataggio_che_non_riesce(finestra, mondo, suonati, monkeypatch):
    def guasto(*_args, **_kwargs):
        raise OSError("disco pieno")

    _livelli_finti(monkeypatch, {})
    monkeypatch.setattr(archivio, "scrivi", guasto)
    finestra._esegui(finestra.amichevoli_dell_attiva)
    righe = finestra.vista.GetValue().splitlines()
    assert righe[-1] == "Salvataggio non riuscito: disco pieno. Il salvataggio precedente è rimasto com'era."
    assert righe[-2].startswith("In tutto 8 amichevoli: ")
    assert suonati == ["amichevoli_in_serie", "amichevoli_in_serie_finite", "salvataggio_non_riuscito"]


def test_l_esito_aspetta_la_fine_del_suono_dell_avvio(finestra, monkeypatch, suonati):
    # Gli incontri si giocano in pochi millesimi: senza l'attesa, il suono della serie finita coprirebbe quello dell'avvio.
    attese = []
    monkeypatch.setattr(suoni, "attesa", lambda: 0.3)
    monkeypatch.setattr(finestra_modulo.time, "sleep", attese.append)
    finestra._esegui(finestra.amichevoli_dell_attiva)
    assert attese == [pytest.approx(0.3 + suoni.PAUSA_IN_CODA)]
    assert suonati == ["amichevoli_in_serie", "amichevoli_in_serie_finite"]


# I testi delle righe.

def _giocatore(gid, nome, cognome, sesso="m", appartenenza="*"):
    return types.SimpleNamespace(id=gid, nome=nome, cognome=cognome, sesso=sesso, appartenenza=appartenenza)


def _risultato(vincitore, set_, esito="normale", ritirato=(), set_giocati=None, registrazione=None):
    vinti_a = sum(1 for a, b in set_ if a > b)
    return types.SimpleNamespace(parti=(1, 2), vincitore=vincitore, set=set_, esito=esito, ritirato=ritirato, set_giocati=set_giocati or len(set_),
                                 set_vinti=(vinti_a, len(set_) - vinti_a), registrazione=registrazione or ["Punti allenamento: 2 a X, 1 a Y."])


def test_le_righe_e_i_totali():
    mondo = types.SimpleNamespace(polisportive={"Mia": types.SimpleNamespace(is_cpu_controlled=False),
                                                "Cpu": types.SimpleNamespace(is_cpu_controlled=True)})
    anna, bruno = _giocatore(1, "Anna", "Neri", "f", "Mia"), _giocatore(2, "Bruna", "Rossi", "f")
    vinta = VoceDellaSerie(anna, 64, bruno, 70, _risultato("A", [(11, 5), (9, 11), (11, 7)]), 2.0, 1.2)
    assert testi.riga_amichevole_in_serie(vinta, mondo) == "Anna Neri, G4, contro Bruna Rossi, H0, libera: vince 2 set a 1 (11 a 5, 9 a 11, 11 a 7); 2 punti allenamento."
    # L'avversario della polisportiva del computer, e il tuo giocatore che sta dalla parte B.
    carlo = _giocatore(2, "Carlo", "Bianchi", "m", "Cpu")
    persa = VoceDellaSerie(anna, 64, carlo, 55, types.SimpleNamespace(**{**vars(_risultato("A", [(11, 3), (11, 4)])), "parti": (2, 1)}), 1.0, 2.0)
    assert testi.riga_amichevole_in_serie(persa, mondo).endswith("contro Carlo Bianchi, F5, di Cpu: perde 0 set a 2 (3 a 11, 4 a 11); 1 punto allenamento.")
    # Il ritiro, con gli infortuni in coda alla riga.
    ritiro = VoceDellaSerie(anna, 64, bruno, 70, _risultato("A", [(11, 5), (5, 3), (11, 0)], "ritiro", (2,), 2,
                                                             ["Punti allenamento: 3 a X, 1 a Y.", "Bruna Rossi si fa male al polso."]), 3.0, 1.0)
    assert testi.riga_amichevole_in_serie(ritiro, mondo) == ("Anna Neri, G4, contro Bruna Rossi, H0, libera: vince perché Bruna Rossi si ritira dopo 2 set "
                                                             "(11 a 5, 5 a 3); 3 punti allenamento. Bruna Rossi si fa male al polso.")
    tutti_e_due = VoceDellaSerie(anna, 64, bruno, 70, _risultato("B", [(4, 11), (5, 3), (11, 0)], "ritiro", (1, 2), 2), 1.0, 1.0)
    assert ": perde, si ritirano tutti e due dopo 2 set (4 a 11, 5 a 3);" in testi.riga_amichevole_in_serie(tutti_e_due, mondo)
    da_solo = VoceDellaSerie(anna, 64, bruno, 70, _risultato("B", [(4, 11), (5, 3), (0, 11)], "ritiro", (1,), 2), 1.0, 1.0)
    assert ": perde perché si ritira dopo 2 set (4 a 11, 5 a 3);" in testi.riga_amichevole_in_serie(da_solo, mondo)
    senza = VoceDellaSerie(anna, 95)
    assert testi.riga_amichevole_in_serie(senza, mondo) == "Anna Neri, J5: oggi nessun avversario nel raggio, dalla classe I0 alla K0."
    # I totali al singolare e al plurale, coi soli esiti che ci sono.
    p = types.SimpleNamespace(nome="Mia", tesserati=[1])
    assert testi.totali_amichevoli_in_serie([(p, [vinta])], mondo) == "In tutto 1 amichevole: 1 vinta, 2 punti allenamento ai tuoi tesserati."
    assert testi.totali_amichevoli_in_serie([(p, [vinta, persa, senza])], mondo) == (
        "In tutto 2 amichevoli: 1 vinta e 1 persa, 3 punti allenamento ai tuoi tesserati; 1 tesserato senza un avversario nel raggio.")
    assert testi.totali_amichevoli_in_serie([(p, [persa, persa])], mondo).startswith("In tutto 2 amichevoli: 2 perse, ")
    assert testi.totali_amichevoli_in_serie([(p, [senza])], mondo) == "Nessuna amichevole giocata: oggi nessun avversario nel raggio per 1 tuo tesserato."
    assert testi.evento_amichevoli_in_serie([(p, [vinta])]) == "1 amichevole in serie"
    assert len(testi.evento_amichevoli_in_serie([(p, [vinta] * 100)])) <= 40


# Le voci del menu Partite, sul desktop nascosto.

def _voci_di_partite(finestra):
    barra = finestra.GetMenuBar()
    menu = barra.GetMenu(barra.FindMenu("Partite"))
    return list(menu.GetMenuItems())


def test_le_voci_del_menu(finestra, mondo, suonati, monkeypatch):
    _livelli_finti(monkeypatch, {})
    voci = _voci_di_partite(finestra)
    assert [v.GetItemLabel() for v in voci[:4]] == ["&Amichevole...\tCtrl+O", f"&Gioca tutte le amichevoli di {PRIMA}",
                                                    "Gioca tutte le amichevoli di tutte le tue &polisportive", ""]
    assert voci[3].IsSeparator()
    # La voce segue la polisportiva attiva, anche col nome che ha la e commerciale, e senza attiva dice di quale parla.
    mondo.miapolisportiva_attiva = mondo.polisportive[SECONDA]
    finestra.aggiorna_le_voci()
    assert voci[1].GetItemLabelText() == f"Gioca tutte le amichevoli di {SECONDA}"
    ora = mondo.datetime_corrente_simulazione
    mondo.polisportive["Gialli & Verdi"] = mondo.miapolisportiva_attiva = Polisportiva("Gialli & Verdi", None, ora)
    finestra.aggiorna_le_voci()
    assert voci[1].GetItemLabel() == "&Gioca tutte le amichevoli di Gialli && Verdi"
    assert voci[1].GetItemLabelText() == "Gioca tutte le amichevoli di Gialli & Verdi"
    assert "Gioca tutte le amichevoli di Gialli & Verdi; Gioca tutte le amichevoli di tutte le tue polisportive;" in testi.guida(finestra.voci_guida())
    mondo.miapolisportiva_attiva = None
    finestra.aggiorna_le_voci()
    assert voci[1].GetItemLabelText() == "Gioca tutte le amichevoli della polisportiva attiva"
    # La voce scelta nel menu gioca la serie della polisportiva attiva.
    mondo.miapolisportiva_attiva = mondo.polisportive[PRIMA]
    finestra.ProcessEvent(wx.CommandEvent(wx.wxEVT_MENU, voci[1].GetId()))
    assert finestra.vista.GetValue().startswith(f"Tutte le amichevoli di oggi di {PRIMA}, ")
    assert voci[1].GetItemLabelText() == f"Gioca tutte le amichevoli di {PRIMA}"
    finestra.ProcessEvent(wx.CommandEvent(wx.wxEVT_MENU, voci[2].GetId()))
    assert finestra.vista.GetValue().startswith("Tutte le amichevoli di oggi delle tue polisportive, ")
    assert suonati == ["amichevoli_in_serie", "amichevoli_in_serie_finite", "amichevoli_in_serie", "amichevoli_in_serie_finite"]
    assert finestra.comandi == 2
