"""
Test dell'ascolto alla cieca dello schermo centrale della issue 12, strumenti/ascolto_schermo.py, senza
mai suonare: la cassa di Acusticator è sostituita da un registratore, e quella vera, se qualcuno la
chiamasse, fa fallire la prova. I punti sono schermi contro brevi, tre tirati dal giocatore di chi
ascolta e tre dall'avversario, ciascuno col suo ritorno; le due versioni di un punto sono identiche
fino all'urto, e la differenza è il rotolamento del ritorno. Le coppie: sei diverse, col ritorno prima
in tre e dopo nelle altre tre, e quattro di controllo identiche campione per campione, due senza
ritorno e due col ritorno; l'ordine si mescola e si ripete col seme; le coppie di un punto durano
uguale, la seconda versione comincia sempre allo stesso campione, e nessun picco supera il tetto. Poi
la sessione intera con una tastiera finta da copione: il via, il silenzio prima della prima coppia, le
risposte anche mentre la coppia suona, il menu di fine gruppo con r che rifà le coppie, l'interruzione,
e il file dei risultati, una riga per coppia, che svela quale versione era quale soltanto alla fine,
anche se la sessione si interrompe; a schermo, prima della fine, nessuna parola che dica che cosa
cambia, e nessuna riga vuota dello strumento.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import random
import sys
from pathlib import Path

import collaudo_comune
import numpy as np
import pytest
from GBUtils import Acusticator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))

import ascolta_partita as ap
import ascolto_schermo as asc
import banco_spazio as bs
import resa_prototipo as resa

import partita_sonora as ps
import percorsi
import suoni
from motore import eventi as E

SEME = 4127
# I messaggi del menu di collaudo_comune, che dopo di sé lascia una riga vuota.
MESSAGGI_DEL_MENU = ("Annotato.", "Segnato come superato.", "Chiuso.")
# Le parole che a schermo, prima della fine, direbbero che cosa cambia o che ci sono controlli.
VIETATE = ("ritorno", "torna indietro", "si ferma", "controllo", "identic", "nuova", "di prima", "rotola")
# Le parole della rivelazione, che nel file vengono soltanto alla fine.
DELLA_RIVELAZIONE = ("ritorno", "controllo", "identic")


def _vietato(nome, chiamate):
    """Al posto di una funzione che suona: segna la chiamata e fa fallire la prova."""
    def chiamata(*_args, **_kwargs):
        chiamate.append(nome)
        raise AssertionError(f"una prova avrebbe suonato davvero, con {nome}")

    return chiamata


def _vieta_la_cassa(mp, chiamate):
    for nome in ("riproduci", "ciclo_di", "play", "stop"):
        mp.setattr(Acusticator, nome, _vietato(f"Acusticator.{nome}", chiamate))


@pytest.fixture(autouse=True)
def cassa_vera_muta(monkeypatch):
    """La cassa vera di Acusticator non deve suonare mai: chi la chiama fa fallire la prova."""
    _vieta_la_cassa(monkeypatch, [])


class Cassa:
    """Al posto di Acusticator nello strumento: tiene i buffer che avrebbe suonato e conta le fermate."""

    def __init__(self, riesce=True):
        self.suonati = []
        self.fermate = 0
        self.riesce = riesce

    def riproduci(self, buffer, fs=None, sync=False):
        self.suonati.append(buffer)
        return self.riesce

    def stop(self):
        self.fermate += 1


class Tastiera:
    """
    Al posto di key di GBUtils: scrive il prompt come quella vera e risponde dal copione. Le voci
    stringa sono i tasti delle attese senza scadenza. Mentre un suono è in corso, un'occhiata alla
    tastiera trova un tasto solo se in testa al copione c'è una terna ("durante", n, tasto) e il
    suono in corso è l'n-esimo della cassa; altrimenti fa passare il tempo dell'orologio finto e
    torna la scadenza, così il suono arriva alla fine. A ogni prompt legge il file dei risultati, se
    c'è, per vedere che cosa vi è scritto in quel momento.
    """

    def __init__(self, copione, cassa, file=None):
        self.copione = list(copione)
        self.cassa = cassa
        self.file = file
        self.adesso = 0.0
        self.prompt = []
        self.letture = []

    def orologio(self):
        return self.adesso

    def __call__(self, prompt="", attesa=None, alla_scadenza=""):
        if attesa is not None:
            voce = self.copione[0] if self.copione else None
            if isinstance(voce, tuple) and voce[1] == len(self.cassa.suonati):
                self.copione.pop(0)
                return voce[2]
            self.adesso += attesa
            return alla_scadenza
        print(prompt, end="")
        self.prompt.append(prompt)
        if self.file is not None and self.file.exists():
            self.letture.append(self.file.read_text(encoding="utf-8"))
        voce = self.copione.pop(0)
        assert isinstance(voce, str), f"il copione aspettava un tasto, trova {voce!r}"
        return voce


@pytest.fixture
def cassa(monkeypatch):
    finta = Cassa()
    monkeypatch.setattr(bs, "Acusticator", finta)
    return finta


def _tastiera(monkeypatch, cassa, copione, file=None):
    tastiera = Tastiera(copione, cassa, file)
    for modulo in (asc, bs, collaudo_comune):
        monkeypatch.setattr(modulo, "key", tastiera)
    monkeypatch.setattr(bs, "orologio", tastiera.orologio)
    return tastiera


def _enter_escape_finta(risposte):
    """Al posto di enter_escape di GBUtils: scrive il prompt e va a capo come quella vera, e risponde dal copione."""
    risposte = iter(risposte)

    def enter_escape(prompt="", *_args, **_kwargs):
        print(prompt)
        return next(risposte)

    return enter_escape


@pytest.fixture(scope="module")
def preparazione(tmp_path_factory):
    """
    I punti giocati e la prova col seme fisso, composti una volta per tutto il modulo. Una fixture di
    modulo parte prima di quelle automatiche di ogni prova: perciò le protezioni le mette lei. La cassa
    vera e il motore dei suoni della finestra sono vietati, e la cartella del mondo è temporanea.
    """
    chiamate = []
    cartella = tmp_path_factory.mktemp("ascolto_schermo")
    with pytest.MonkeyPatch.context() as mp:
        _vieta_la_cassa(mp, chiamate)
        mp.setattr(suoni, "_riproduci", _vietato("suoni._riproduci", chiamate))
        mp.setattr(percorsi, "cartella", lambda: str(cartella))
        candidati = ap.punti_giocati()
        prova = asc.prepara(SEME, candidati)
    assert chiamate == []
    return candidati, prova


@pytest.fixture
def prova(preparazione):
    """Una prova nuova per ogni prova, perché raccoglie le scelte, sulle coppie già composte."""
    return asc.Prova(SEME, preparazione[1].coppie)


def _meta(coppia):
    """Le due versioni di una coppia, senza la pausa fra loro."""
    pausa = round(asc.PAUSA_FRA_LE_VERSIONI * ps.FS)
    return coppia.buffer[:coppia.seconda - pausa], coppia.buffer[coppia.seconda:], coppia.buffer[coppia.seconda - pausa:coppia.seconda]


# I punti e le versioni.

def test_i_punti_sono_schermi_contro_brevi_dalle_due_parti(preparazione):
    candidati, _prova = preparazione
    punti = asc.scegli_punti(candidati)
    assert len(punti) == 2 * asc.PUNTI_PER_PARTE
    assert [asc.chi_tira(p) for p in punti] == ["A"] * asc.PUNTI_PER_PARTE + ["B"] * asc.PUNTI_PER_PARTE
    for p in punti:
        esito = p.momento.esito
        assert esito.causa == "schermo_contro" and esito.attacchi <= asc.ATTACCHI_MASSIMI
        assert sum(1 for e in p.momento.eventi if asc.e_ritorno(e)) == 1
    for parte in ("A", "B"):
        colpi = [p.momento.esito.colpo_decisivo for p in punti if asc.chi_tira(p) == parte]
        assert len(set(colpi)) == len(colpi)
    # Sempre gli stessi; e se una parte non ne ha abbastanza, lo strumento lo dice invece di partire.
    assert [id(p.momento) for p in asc.scegli_punti(candidati)] == [id(p.momento) for p in punti]
    with pytest.raises(LookupError):
        asc.scegli_punti([p for p in punti if asc.chi_tira(p) == "A"])


def test_le_due_versioni_sono_identiche_fino_all_urto(preparazione):
    candidati, _prova = preparazione
    for punto in asc.scegli_punti(candidati):
        azione = resa.azione(punto.momento.eventi)
        senza = asc.senza_ritorno(azione)
        assert len(senza) == len(azione) - 1 and not any(asc.e_ritorno(e) for e in senza)
        con, prima = asc.componi_versione(punto, asc.CON), asc.componi_versione(punto, asc.SENZA)
        ritorno = next(e for e in azione if asc.e_ritorno(e))
        composto = ps.componi(azione, asc.ASCOLTATORE)
        urto = round(composto.secondi(ritorno.t) * ps.FS)
        n = min(len(con), len(prima))
        differenza = np.flatnonzero(np.any(np.abs(con[:n] - prima[:n]) > 1e-7, axis=1))
        # La differenza comincia dopo l'urto, e non prima, alla prima capriola dei pallini: è il rotolamento del ritorno.
        assert len(differenza) and urto - 3 <= differenza[0] <= urto + round(0.4 * ps.FS)
        assert len(con) >= len(prima)


# Le coppie.

def test_le_coppie_diverse_e_quelle_di_controllo(preparazione):
    candidati, prova = preparazione
    punti = asc.scegli_punti(candidati)
    coppie = prova.coppie
    assert len(coppie) == len(punti) + asc.COPPIE_DI_CONTROLLO
    diverse = [c for c in coppie if not c.controllo]
    controlli = [c for c in coppie if c.controllo]
    # Ogni punto una volta con le due versioni: il ritorno prima in metà delle coppie, dopo nell'altra metà.
    assert sorted(id(c.punto.momento) for c in diverse) == sorted(id(p.momento) for p in punti)
    assert sum(1 for c in diverse if c.versioni == (asc.CON, asc.SENZA)) == sum(1 for c in diverse if c.versioni == (asc.SENZA, asc.CON)) == len(punti) // 2
    # I controlli: due senza ritorno e due col ritorno, identici campione per campione.
    assert sorted(c.versioni[0] for c in controlli) == [asc.CON, asc.CON, asc.SENZA, asc.SENZA]
    for c in controlli:
        prima, seconda, pausa = _meta(c)
        assert np.array_equal(prima, seconda) and not np.any(pausa)
    for c in diverse:
        prima, seconda, pausa = _meta(c)
        assert len(prima) == len(seconda) and not np.array_equal(prima, seconda) and not np.any(pausa)
    # Le coppie di un punto durano uguale, e la seconda versione comincia allo stesso campione.
    per_punto = {}
    for c in coppie:
        per_punto.setdefault(id(c.punto.momento), set()).add((len(c.buffer), c.seconda))
    assert all(len(forme) == 1 for forme in per_punto.values())
    # La versione col ritorno è la stessa in tutte le coppie del suo punto, e così quella senza.
    versioni = {}
    for c in coppie:
        prima, seconda, _pausa = _meta(c)
        for versione, buffer in zip(c.versioni, (prima, seconda), strict=True):
            chiave = (id(c.punto.momento), versione)
            if chiave in versioni:
                assert np.array_equal(versioni[chiave], buffer)
            versioni[chiave] = buffer
    # Il livello della partita al volume 100, col margine: nessun picco supera il tetto.
    assert all(c.buffer.dtype == np.float32 and float(np.max(np.abs(c.buffer))) <= ps.TETTO for c in coppie)


def test_l_ordine_si_mescola_e_si_ripete_col_seme(preparazione):
    candidati, _prova = preparazione
    punti = asc.scegli_punti(candidati)

    def forma(seme):
        return [(id(p.momento), v) for p, v in asc.assegna(random.Random(seme), punti)]

    assert forma(SEME) == forma(SEME)
    forme = {tuple(forma(seme)) for seme in range(20)}
    assert len(forme) == 20
    # Il nuovo non sta sempre nello stesso posto: in ogni seme metà delle coppie diverse lo mette prima.
    for seme in range(20):
        diverse = [v for _p, v in asc.assegna(random.Random(seme), punti) if v[0] != v[1]]
        assert diverse.count((asc.CON, asc.SENZA)) == diverse.count((asc.SENZA, asc.CON))


def test_i_prompt_stanno_in_quaranta_caratteri():
    for scelta in (None, *asc.RISPOSTE):
        prompt = asc.invito(scelta)
        assert prompt.startswith("\r") and prompt.endswith("\r") and len(prompt.strip("\r")) <= 40, prompt


# La sessione.

def _snapshot_senza_rivelazione(letture):
    return all(parola not in lettura for lettura in letture for parola in DELLA_RIVELAZIONE)


def test_la_sessione_intera(prova, cassa, programma_di_prova, suonati, monkeypatch, capsys):
    monkeypatch.setattr(asc, "prepara", lambda seme: prova if seme == SEME else pytest.fail(f"seme {seme}"))
    monkeypatch.setattr(asc, "enter_escape", _enter_escape_finta([True]))
    monkeypatch.setattr(collaudo_comune, "enter_escape", _enter_escape_finta([True]))
    monkeypatch.setattr(collaudo_comune, "dgt", lambda *_a, **_k: "la seconda mi sembra più vera ")
    dormite = []
    monkeypatch.setattr(asc.time, "sleep", dormite.append)
    file = programma_di_prova / asc.FILE_DEI_RISULTATI
    # Coppia 1: 1 al prompt. Coppia 2: 2 mentre suona. Coppia 3: spazio la ripete, poi u. Coppia 4: un
    # tasto che non vale, poi Invio, senza scelta. Coppie 5-10: 1, 2, u, 1, 2, u. Poi c e Invio.
    copione = ["1", ("durante", 2, "2"), " ", "u", "x", "\r", "1", "2", "u", "1", "2", "u", "c", "\r"]
    tastiera = _tastiera(monkeypatch, cassa, copione, file)
    assert asc.main([str(SEME)]) == 0
    assert tastiera.copione == [] and dormite == [] and suonati == []
    # Dieci coppie e una ripetizione; la prima ha il silenzio lungo dopo il via, le altre quello del numero.
    assert len(cassa.suonati) == 11 and cassa.fermate == 1
    assert np.array_equal(cassa.suonati[0], prova.da_sentire(0, asc.ANTICIPO_PRIMA_COPPIA))
    assert np.array_equal(cassa.suonati[1], prova.da_sentire(1, asc.ANTICIPO_COPPIA))
    assert np.array_equal(cassa.suonati[3], prova.da_sentire(2, asc.ANTICIPO_RIPETIZIONE))
    assert asc.ANTICIPO_PRIMA_COPPIA >= asc.ANTICIPO_COPPIA + 3.0
    assert prova.scelte == {0: "1", 1: "2", 2: "u", 4: "1", 5: "2", 6: "u", 7: "1", 8: "2", 9: "u"}
    assert "\rSpazio ripete; 1, 2 o u per uguali\r" in tastiera.prompt

    righe = file.read_text(encoding="utf-8").splitlines()
    assert righe[0].startswith("Ascolto dello schermo centrale, ") and righe[0].endswith(f", seme {SEME}.")
    risposte = ["la prima", "la seconda", "uguali", "senza scelta", "la prima", "la seconda", "uguali", "la prima", "la seconda", "uguali"]
    assert righe[1:11] == [f"{asc.TITOLO}, coppia {k}: {r}." for k, r in enumerate(risposte, 1)]
    assert righe[11].startswith(f"{asc.TITOLO}, ") and righe[11].endswith(": la seconda mi sembra più vera")
    # Fino al commento, e a ogni prompt della sessione, il file non dice che cosa c'era nelle coppie.
    assert not any(parola in riga for riga in righe[:12] for parola in DELLA_RIVELAZIONE)
    assert tastiera.letture and _snapshot_senza_rivelazione(tastiera.letture)
    # Poi la rivelazione, una riga per coppia, e il riepilogo.
    rivelazione = righe[12:22]
    assert rivelazione == asc.righe_della_rivelazione(prova)
    for k, (riga, coppia) in enumerate(zip(rivelazione, prova.coppie, strict=True), 1):
        assert riga.startswith(f"{asc.TITOLO}, coppia {k}, ")
        assert ("coppia di controllo" in riga) == coppia.controllo
    assert righe[22:] == asc.righe_del_riepilogo(prova)
    assert all(riga.strip() and not riga.startswith(("-", "=", "_")) for riga in righe)

    scritto = capsys.readouterr().out
    assert scritto.startswith("Preparo le coppie, qualche secondo.\nAscolto alla cieca dello schermo centrale: 10 coppie, ")
    assert scritto.rstrip().endswith("trovi le tue risposte, quale versione era quale e il riepilogo.")
    # A schermo, prima del riepilogo finale, nessuna parola dice che cosa cambia, né la cronaca dei punti.
    prima_della_fine = scritto.split("Riepilogo, ")[0]
    for parola in VIETATE:
        assert parola not in prima_della_fine, parola
    assert "Fischio" not in prima_della_fine and "schermo centrale" in prima_della_fine
    for k in range(1, 11):
        assert f"Coppia {k} di 10.\n" in scritto
    # Il riepilogo si legge anche a schermo, alla fine.
    for riga in asc.righe_del_riepilogo(prova):
        assert riga in scritto
    # Le sole righe vuote sono quelle che il menu di collaudo_comune lascia dopo i suoi messaggi.
    linee = scritto.split("\n")
    vuote = [i for i, riga in enumerate(linee[:-1]) if riga == ""]
    assert vuote and all(linee[i - 1] in MESSAGGI_DEL_MENU for i in vuote), [linee[i - 1] for i in vuote]


def test_r_rifa_le_coppie_con_le_scelte_gia_date(prova, cassa, programma_di_prova, monkeypatch):
    monkeypatch.setattr(asc, "prepara", lambda _seme: prova)
    monkeypatch.setattr(asc, "enter_escape", _enter_escape_finta([True]))
    monkeypatch.setattr(collaudo_comune, "enter_escape", _enter_escape_finta([True]))
    # Il primo giro risponde 1 a tutte; con r il secondo cambia la prima coppia in u e lascia le altre con Invio.
    copione = ["1"] * 10 + ["r", "u"] + ["\r"] * 9 + ["\r"]
    tastiera = _tastiera(monkeypatch, cassa, copione)
    assert asc.main([]) == 0
    assert tastiera.copione == [] and len(cassa.suonati) == 20
    assert prova.scelte == {0: "u", **dict.fromkeys(range(1, 10), "1")}
    assert tastiera.prompt.count("\rHai scelto la prima: spazio, 1, 2 o u\r") == 10
    righe = (programma_di_prova / asc.FILE_DEI_RISULTATI).read_text(encoding="utf-8").splitlines()
    assert righe[1] == f"{asc.TITOLO}, coppia 1: uguali." and righe[2] == f"{asc.TITOLO}, coppia 2: la prima."
    assert sum(1 for riga in righe if riga.endswith(": test superato, nessun commento")) == 1
    assert not any("chiuse prima della fine" in riga for riga in righe)


def test_escape_chiude_le_coppie_e_la_rivelazione_arriva_lo_stesso(prova, cassa, programma_di_prova, monkeypatch, capsys):
    monkeypatch.setattr(asc, "prepara", lambda _seme: prova)
    monkeypatch.setattr(asc, "enter_escape", _enter_escape_finta([True]))
    monkeypatch.setattr(collaudo_comune, "enter_escape", _enter_escape_finta([True]))
    # Tre risposte, Escape mentre suona la quarta, e il menu chiuso senza giudizio.
    copione = ["2", "2", "u", ("durante", 4, "\x1b"), "\x1b"]
    tastiera = _tastiera(monkeypatch, cassa, copione)
    assert asc.main([]) == 0
    assert tastiera.copione == [] and len(cassa.suonati) == 4 and cassa.fermate == 1
    assert prova.interrotta and prova.chiusa
    righe = (programma_di_prova / asc.FILE_DEI_RISULTATI).read_text(encoding="utf-8").splitlines()
    assert righe[1:11] == [f"{asc.TITOLO}, coppia {k}: {r}." for k, r in enumerate(["la seconda", "la seconda", "uguali"] + ["senza scelta"] * 7, 1)]
    assert righe[11].endswith(": chiuso senza giudizio")
    assert righe[12] == f"{asc.TITOLO}: le coppie si sono chiuse prima della fine."
    assert righe[13:23] == asc.righe_della_rivelazione(prova)
    assert righe[23] == f"Riepilogo, {asc.TITOLO}: il gruppo è stato chiuso senza giudizio, quindi le scelte che seguono non contano."
    assert "Coppie chiuse." in capsys.readouterr().out


def test_il_gruppo_saltato_non_svela_niente(prova, cassa, programma_di_prova, monkeypatch, capsys):
    monkeypatch.setattr(asc, "prepara", lambda _seme: prova)
    monkeypatch.setattr(asc, "enter_escape", _enter_escape_finta([True]))
    monkeypatch.setattr(collaudo_comune, "enter_escape", _enter_escape_finta([False]))
    _tastiera(monkeypatch, cassa, [])
    assert asc.main([]) == 0
    assert cassa.suonati == []
    righe = (programma_di_prova / asc.FILE_DEI_RISULTATI).read_text(encoding="utf-8").splitlines()
    assert righe[1:] == [f"{asc.TITOLO}: gruppo saltato."]
    assert "Riepilogo" not in capsys.readouterr().out


def test_senza_il_via_non_suona_niente(prova, cassa, programma_di_prova, monkeypatch, capsys):
    monkeypatch.setattr(asc, "prepara", lambda _seme: prova)
    monkeypatch.setattr(asc, "enter_escape", _enter_escape_finta([False]))
    assert asc.main([]) == 0
    assert cassa.suonati == []
    assert not (programma_di_prova / asc.FILE_DEI_RISULTATI).exists()
    assert "\n\n" not in capsys.readouterr().out


def test_un_seme_che_non_e_un_numero(cassa, programma_di_prova, capsys):
    assert asc.main(["quattro"]) == 1
    assert cassa.suonati == []
    assert not (programma_di_prova / asc.FILE_DEI_RISULTATI).exists()
    assert "Il seme dev'essere un numero intero" in capsys.readouterr().out


def test_una_scheda_che_non_risponde_non_ferma_l_ascolto(prova, monkeypatch, capsys):
    muta = Cassa(riesce=False)
    monkeypatch.setattr(bs, "Acusticator", muta)
    _tastiera(monkeypatch, muta, ["1"] * len(prova.coppie))
    assert asc.ascolta(prova)
    assert "la scheda audio non risponde" in capsys.readouterr().out


# La rivelazione e il riepilogo.

def test_la_rivelazione_e_il_riepilogo(prova):
    # Il ritorno scelto in tutte le coppie diverse, uguali in tre controlli e la seconda nel quarto.
    controlli = [posto for posto, c in enumerate(prova.coppie) if c.controllo]
    for posto, coppia in enumerate(prova.coppie):
        if coppia.controllo:
            prova.scelte[posto] = "2" if posto == controlli[-1] else "u"
        else:
            prova.scelte[posto] = "1" if coppia.versioni[0] == asc.CON else "2"
    righe = asc.righe_della_rivelazione(prova)
    for posto, (riga, coppia) in enumerate(zip(righe, prova.coppie, strict=True)):
        if coppia.controllo:
            assert "era una coppia di controllo, con due versioni identiche campione per campione, tutte e due " in riga
            assert riga.endswith("; per te erano uguali.") or (posto == controlli[-1] and riga.endswith("; hai scelto la seconda."))
        else:
            assert riga.endswith(", quella col ritorno.") and "la prima era " in riga and "; la seconda era " in riga
        tira = asc.chi_tira(coppia.punto)
        assert (", del tuo giocatore: " in riga) == (tira == "A") and (", dell'avversario: " in riga) == (tira == "B")
    riepilogo = asc.righe_del_riepilogo(prova)
    assert riepilogo[0] == "Riepilogo, coppie diverse: 6 coppie; hai scelto il ritorno 6 volte, senza ritorno 0 volte, uguali 0 volte, senza scelta 0 volte."
    assert riepilogo[1] == "Riepilogo, coppie diverse tirate dal tuo giocatore: 3 coppie; il ritorno 3 volte, senza ritorno 0 volte, uguali 0 volte, senza scelta 0 volte."
    assert riepilogo[2] == "Riepilogo, coppie diverse tirate dall'avversario: 3 coppie; il ritorno 3 volte, senza ritorno 0 volte, uguali 0 volte, senza scelta 0 volte."
    assert riepilogo[3] == "Riepilogo, coppie uguali di controllo: 4 coppie; hai detto uguali 3 volte, la prima 0 volte, la seconda 1 volta, senza scelta 0 volte."
    # Il ritorno sta prima in tre coppie diverse e dopo nelle altre tre, più la seconda del controllo.
    assert riepilogo[4] == "Riepilogo, l'ordine: in tutte le coppie hai scelto la prima 3 volte e la seconda 4 volte."
    # Senza scelte, tutto senza scelta.
    vuota = asc.Prova(SEME, prova.coppie)
    assert all(riga.endswith("; senza scelta.") for riga in asc.righe_della_rivelazione(vuota))
    assert "senza scelta 6 volte." in asc.righe_del_riepilogo(vuota)[0]


def test_il_ritorno_si_riconosce_dal_volo(preparazione):
    candidati, _prova = preparazione
    punto = asc.scegli_punti(candidati)[0]
    (ritorno,) = [e for e in punto.momento.eventi if asc.e_ritorno(e)]
    assert ritorno.tipo == E.VOLO and ritorno.volo[-1].tipo == "fermo" and ritorno.dati == {"ritorno": True}
