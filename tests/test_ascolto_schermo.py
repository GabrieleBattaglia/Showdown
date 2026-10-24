"""
Test dell'ascolto di confronto dello schermo centrale della issue 12, strumenti/ascolto_schermo.py,
senza mai suonare: la cassa di Acusticator è sostituita da un registratore, e quella vera, se qualcuno
la chiamasse, fa fallire la prova. I punti sono schermi contro brevi, tre tirati dal giocatore di chi
ascolta e tre dall'avversario. Le versioni: fino all'urto identiche campione per campione a quella di
oggi, fischio compreso; l'urto nuovo sta più in alto di quello di oggi rispetto al fischio, e i tre urti
nuovi si sentono forti uguali; il ritorno ricade dopo l'urto, nel punto da cui l'urto si sente, e da
lì torna verso chi ha tirato fino a fermarsi nella sua metà; i timbri candidati restano fuori dalla collezione di GBUtils. Le lettere: sei
per punto, le cinque versioni e una ripetuta identica, che cambia da un punto all'altro; tutte lunghe
uguali e allo stesso livello, sotto il tetto; mescolate e ripetute col seme. Poi la sessione intera con
una tastiera finta da copione: il via, il silenzio prima della prima lettera, la rassegna, la scelta
anche mentre una lettera suona, il commento al punto, il menu di fine gruppo con r che rifà il gruppo,
l'interruzione, il gruppo saltato, e il file dei risultati, una riga per voce, che svela quale lettera
era quale soltanto alla fine, anche se la sessione si interrompe; a schermo, prima della fine, nessuna
parola che dica che cosa cambia, e nessuna riga vuota dello strumento. Infine le due aggiunte di
partita_sonora per lo strumento, il ritocco di componi e sorgente_del_preset, che lasciano la partita
com'era.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import json
import math
import sys
import types
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
from costanti import LUNGHEZZA_TAVOLO
from motore import cronaca as C
from motore.tavolo import CENTRO_X

SEME = 4127
# I messaggi del menu di collaudo_comune, che dopo di sé lascia una riga vuota.
MESSAGGI_DEL_MENU = ("Annotato.", "Segnato come superato.", "Chiuso.")
# Le parole che a schermo, prima della fine, direbbero che cosa cambia o che ci sono controlli.
VIETATE = ("ritorno", "torna", "controllo", "identic", "oggi", "netto", "legno", "plastica", "versione", "più forte", "rotola", "ricade")
# Le parole della rivelazione, che nel file vengono soltanto alla fine.
DELLA_RIVELAZIONE = ("Rivelazione", "ritorno", "identic", "oggi", "netto", "legno", "plastica")


def livello_a(stereo):
    """Il livello di un tratto stereo in decibel, con la ponderazione A della norma IEC 61672, sulla media dei due canali."""
    from scipy.signal import bilinear, lfilter

    f1, f2, f3, f4 = 20.598997, 107.65265, 737.86223, 12194.217
    numeratore = [(2 * math.pi * f4) ** 2 * 10 ** (1.9997 / 20), 0, 0, 0, 0]
    denominatore = np.polymul([1, 4 * math.pi * f4, (2 * math.pi * f4) ** 2], [1, 4 * math.pi * f1, (2 * math.pi * f1) ** 2])
    denominatore = np.polymul(np.polymul(denominatore, [1, 2 * math.pi * f3]), [1, 2 * math.pi * f2])
    b, a = bilinear(numeratore, denominatore, ps.FS)
    pesato = lfilter(b, a, np.asarray(stereo, dtype=np.float64).mean(axis=1))
    return 10 * math.log10(max(float(np.mean(pesato ** 2)), 1e-24))


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


def _dgt_finta(risposte):
    """Al posto di dgt di GBUtils: scrive il prompt e va a capo come input, e risponde dal copione."""
    risposte = iter(risposte)

    def dgt(prompt="", *_args, **_kwargs):
        print(prompt)
        return next(risposte)

    return dgt


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
    """Una prova nuova per ogni prova, perché raccoglie le scelte, sugli stessi punti già composti."""
    return asc.Prova(SEME, preparazione[1].gruppi)


def _punti(prova):
    return [p for g in prova.gruppi for p in g.punti]


# I punti e le versioni.

def test_i_punti_sono_schermi_contro_brevi_dalle_due_parti(preparazione):
    candidati, prova = preparazione
    punti = asc.scegli_punti(candidati)
    assert len(punti) == 2 * asc.PUNTI_PER_PARTE
    assert [asc.chi_tira(p) for p in punti] == ["A"] * asc.PUNTI_PER_PARTE + ["B"] * asc.PUNTI_PER_PARTE
    for p in punti:
        esito = p.momento.esito
        assert esito.causa == "schermo_contro" and esito.attacchi <= asc.ATTACCHI_MASSIMI
    for parte in ("A", "B"):
        colpi = [p.momento.esito.colpo_decisivo for p in punti if asc.chi_tira(p) == parte]
        assert len(set(colpi)) == len(colpi)
    # I gruppi: prima i tiri del tuo giocatore, poi quelli dell'avversario, con gli stessi punti.
    assert [(g.parte, g.titolo) for g in prova.gruppi] == list(asc.GRUPPI)
    assert [id(p.candidato.momento) for p in _punti(prova)] == [id(p.momento) for p in punti]
    assert all(p.parte == g.parte for g in prova.gruppi for p in g.punti)
    # Sempre gli stessi; e se una parte non ne ha abbastanza, lo strumento lo dice invece di partire.
    assert [id(p.momento) for p in asc.scegli_punti(candidati)] == [id(p.momento) for p in punti]
    with pytest.raises(LookupError):
        asc.scegli_punti([p for p in punti if asc.chi_tira(p) == "A"])


def _urto(punto):
    eventi = resa.azione(punto.candidato.momento.eventi)
    volo = asc.volo_dello_schermo(eventi)
    composto = ps.componi(eventi, asc.ASCOLTATORE)
    return volo, composto, round(composto.secondi(volo.volo[-1].t) * ps.FS)


def test_le_versioni_sono_identiche_fino_all_urto(prova):
    for punto in _punti(prova):
        _volo, _composto, urto = _urto(punto)
        oggi = punto.buffer["oggi"]
        for chiave, buffer in punto.buffer.items():
            assert len(buffer) == len(oggi)
            if chiave == "oggi":
                continue
            differenza = np.flatnonzero(np.any(np.abs(buffer - oggi) > 1e-7, axis=1))
            # Prima dell'urto, un campione d'arrotondamento al più, tutto uguale: anche il colpo, il rotolamento e il fischio.
            assert len(differenza) and urto - 2 <= differenza[0] <= urto + 2, chiave
        # Il netto e il netto col ritorno hanno lo stesso urto: si separano alla ricaduta.
        netto, col_ritorno = punto.buffer["netto"], punto.buffer["netto_ritorno"]
        dopo = np.flatnonzero(np.any(np.abs(col_ritorno - netto) > 1e-7, axis=1))
        ricaduta = urto + round(asc.RITARDO_DELLA_RICADUTA * ps.FS)
        assert len(dopo) and ricaduta - 2 <= dopo[0] <= ricaduta + 2


def test_l_urto_nuovo_si_stacca_dal_fischio(prova):
    for punto in _punti(prova)[::2]:
        volo, composto, _urto_i = _urto(punto)
        urto = volo.volo[-1]
        fischio = next(p for p in composto.posati if p.ruolo == "fischio_singolo" and p.t >= urto.t - 1e-3)
        # Il fischio parte nello stesso istante del tocco, in tutte le versioni: lo dice il ritocco, che non lo tocca.
        assert fischio.t == pytest.approx(urto.t, abs=1e-3)
        n = round(0.1 * ps.FS)
        fischio_a = livello_a(ps.spazializza(fischio, "A")[:n])
        livelli = {}
        for versione in asc.VERSIONI:
            resa_v = asc.componi_versione(punto.candidato, versione)
            (schermo,) = [p for p in resa_v.posati if p.ruolo == "schermo"]
            livelli[versione.chiave] = livello_a(ps.spazializza(schermo, "A")[:n]) - fischio_a
            # Il fischio e il cicalino sono quelli di oggi, nello stesso istante.
            assert [(p.ruolo, p.t) for p in resa_v.posati if p.ruolo in ("fischio_singolo", "fallo")] == \
                [(p.ruolo, p.t) for p in composto.posati if p.ruolo in ("fischio_singolo", "fallo")]
            if versione.verso_il_centro:
                assert schermo.posizioni == [((urto.x + CENTRO_X) / 2.0, urto.y)]
        # Oggi l'urto sta sotto il fischio; gli urti nuovi sopra, forti uguali entro pochi dB.
        assert livelli["oggi"] < -4.0
        nuovi = [livelli[k] for k in ("netto", "legno", "plastica")]
        assert min(nuovi) > 0.5 and max(nuovi) - min(nuovi) < 3.0, livelli


def test_il_ritorno_torna_verso_chi_ha_tirato(prova):
    for punto in _punti(prova):
        volo, _composto, _urto_i = _urto(punto)
        urto = volo.volo[-1]
        # Il ritorno parte dal punto da cui si sente l'urto, a metà fra quello vero e il centro dello schermo.
        dove = asc.punto_dell_urto(urto, asc.PER_CHIAVE["netto_ritorno"])
        assert dove == ((urto.x + CENTRO_X) / 2.0, urto.y)
        indietro = asc.ritorno(volo, dove)
        partenza, fermo = indietro.volo[0], indietro.volo[-1]
        assert partenza.t == pytest.approx(urto.t + asc.RITARDO_DELLA_RICADUTA) and (partenza.x, partenza.y) == dove
        assert fermo.tipo == "fermo" and fermo.v == pytest.approx(0.0, abs=1e-3)
        assert asc.VELOCITA_DEL_RITORNO[0] <= partenza.v <= asc.VELOCITA_DEL_RITORNO[1]
        strada = math.hypot(fermo.x - dove[0], fermo.y - dove[1])
        assert strada <= asc.STRADA_DEL_RITORNO[1] + 1e-6 and strada > 80.0
        # Verso chi ha tirato, dalla sua parte, e si ferma fra 25 e 70 cm dalla sua linea.
        linea = fermo.y if punto.parte == "A" else LUNGHEZZA_TAVOLO - fermo.y
        assert 25.0 <= linea <= 70.0, linea
        # Lo stesso punto torna sempre uguale; i suoni: la ricaduta e il rotolamento, più forte di quello della partita.
        assert asc.ritorno(volo, dove).volo == indietro.volo
        ricaduta, rotolamento = asc.posati_del_ritorno(volo, dove)
        assert ricaduta.ruolo == "ricaduta" and ricaduta.t == partenza.t and ricaduta.posizioni == [dove]
        (della_partita,) = ps.posati_del_volo(indietro)
        assert rotolamento.ruolo == "rotolamento" and np.allclose(rotolamento.guadagni, della_partita.guadagni * asc.GUADAGNO_DEL_RITORNO)


def test_il_ritorno_riparte_da_dove_si_sente_l_urto(prova):
    """Nelle versioni col ritorno la ricaduta e il rotolamento partono dal punto dell'urto che si sente, anche quando è verso il centro."""
    col_ritorno = [v for v in asc.VERSIONI if v.ritorno]
    assert col_ritorno and all(v.verso_il_centro for v in col_ritorno)
    for punto in _punti(prova):
        volo, _composto, _urto_i = _urto(punto)
        for versione in col_ritorno:
            posati = asc.componi_versione(punto.candidato, versione).posati
            (schermo,) = [p for p in posati if p.ruolo == "schermo"]
            (ricaduta,) = [p for p in posati if p.ruolo == "ricaduta"]
            (indietro,) = [p for p in posati if p.ruolo == "rotolamento" and p.evento == volo.n + asc.SCARTO_DEL_NUMERO]
            assert schermo.posizioni == [asc.punto_dell_urto(volo.volo[-1], versione)]
            assert ricaduta.posizioni == schermo.posizioni, versione.chiave
            assert indietro.posizioni[0] == pytest.approx(schermo.posizioni[0], abs=1e-6), versione.chiave
            # Per chi ascolta, l'urto, la ricaduta e la partenza del rotolamento hanno lo stesso pan: niente salti di lato.
            pan = [float(ps.SPAZIO.campi(p.posizioni[:1], asc.ASCOLTATORE)[0][0]) for p in (schermo, ricaduta, indietro)]
            assert max(pan) - min(pan) < 1e-6, (versione.chiave, pan)


def test_i_timbri_candidati_restano_fuori_da_gbutils():
    import GBUtils

    condivisa = json.loads((Path(GBUtils.__file__).resolve().parent / "Acu_Collection.json").read_text(encoding="utf-8"))
    percorso = asc.registra_i_timbri()
    assert Path(percorso).parent == Path(asc.tempfile.gettempdir())
    assert asc.registra_i_timbri() == percorso
    for nome, preset in asc.TIMBRI.items():
        assert nome not in condivisa and nome.startswith("ascolto_schermo_")
        assert set(preset) == {"descrizione", "score", "kind", "adsr"} and all(len(q) == 4 for q in preset["score"])
        assert Acusticator.descrizione(nome) == preset["descrizione"]
        assert len(ps.sorgente_del_preset(nome)) > 0
    # Ogni versione nuova usa un timbro candidato, e la ricaduta il suo.
    assert {v.urto for v in asc.VERSIONI if v.urto} | {asc.RICADUTA} == set(asc.TIMBRI)
    with pytest.raises(KeyError, match="non c'è nella collezione"):
        ps.sorgente_del_preset("ascolto_schermo_che_non_esiste")


# Le lettere.

def test_le_lettere_e_i_controlli(prova):
    punti = _punti(prova)
    chiavi = [v.chiave for v in asc.VERSIONI]
    for punto in punti:
        assert len(punto.lettere) == len(asc.LETTERE) == len(chiavi) + 1 and set(punto.lettere) == set(chiavi)
        doppie = punto.lettere_di(punto.ripetuta)
        assert len(doppie) == 2
        assert np.array_equal(punto.da_sentire(doppie[0], 0.0), punto.da_sentire(doppie[1], 0.0))
        # Le lettere durano uguali, e nessun picco supera il tetto della partita.
        assert len({len(b) for b in punto.buffer.values()}) == 1
        assert all(b.dtype == np.float32 and float(np.max(np.abs(b))) <= ps.TETTO for b in punto.buffer.values())
        # L'anticipo è silenzio in testa.
        sentita = punto.da_sentire("A", 2.0)
        assert not np.any(sentita[:round(2.0 * ps.FS)]) and np.array_equal(sentita[round(2.0 * ps.FS):], punto.buffer[punto.lettere[0]])
    # Ogni versione è la ripetuta almeno una volta.
    assert {p.ripetuta for p in punti} == set(chiavi)


def test_lo_stesso_livello_per_tutte_le_lettere_del_punto(preparazione):
    _candidati, prova = preparazione
    punto = _punti(prova)[0]
    composte = {v.chiave: asc.componi_versione(punto.candidato, v).buffer for v in asc.VERSIONI}
    picco = max(float(np.max(np.abs(b))) for b in composte.values())
    fattore = min(1.0, ps.TETTO / picco)
    for chiave, buffer in composte.items():
        assert np.allclose(punto.buffer[chiave][:len(buffer)], buffer * fattore, atol=2e-6)


def test_l_ordine_si_mescola_e_si_ripete_col_seme(preparazione, monkeypatch):
    candidati, prova = preparazione
    # Le lettere vengono soltanto dal seme: per vederlo basta comporre niente.
    monkeypatch.setattr(asc, "componi_punto", lambda _candidato: {})

    def forma(seme):
        return [p.lettere for g in asc.prepara(seme, candidati).gruppi for p in g.punti]

    assert forma(SEME) == forma(SEME) == [p.lettere for p in _punti(prova)]
    assert len({tuple(forma(seme)) for seme in range(12)}) == 12


def test_i_prompt_stanno_in_quaranta_caratteri():
    for prompt in (asc.invito(None), *(asc.invito(lettera) for lettera in asc.LETTERE), "\rc per un commento, Invio prosegue\r"):
        assert prompt.startswith("\r") and prompt.endswith("\r") and len(prompt.strip("\r")) <= 40, prompt


# La sessione.

def test_la_sessione_intera(prova, cassa, programma_di_prova, suonati, monkeypatch, capsys):
    monkeypatch.setattr(asc, "prepara", lambda seme: prova if seme == SEME else pytest.fail(f"seme {seme}"))
    monkeypatch.setattr(asc, "enter_escape", _enter_escape_finta([True]))
    monkeypatch.setattr(collaudo_comune, "enter_escape", _enter_escape_finta([True, True]))
    monkeypatch.setattr(collaudo_comune, "dgt", lambda *_a, **_k: "la terza lettera mi piace ")
    monkeypatch.setattr(asc, "dgt", _dgt_finta(["la seconda è più vera "]))
    dormite = []
    monkeypatch.setattr(asc.time, "sleep", dormite.append)
    file = programma_di_prova / asc.FILE_DEI_RISULTATI
    # Primo gruppo. Punto 1: la rassegna, poi b la fa sentire, s la sceglie, c e il commento. Punto 2:
    # a suona e d, premuto mentre suona, la ferma e fa sentire la D; spazio la ripete, s, Invio. Punto
    # 3: Escape alla seconda lettera della rassegna, un tasto che non vale, n, Invio. Il menu: c e Invio.
    # Secondo gruppo. Punto 1: Invio, senza scelta. Punto 2: s senza aver sentito niente, f, s, Invio.
    # Punto 3: e, s, Invio. Il menu: Invio.
    copione = ["b", "s", "c",
               "a", ("durante", 14, "d"), " ", "s", "\r",
               ("durante", 18, "\x1b"), "x", "n", "\r",
               "c", "\r",
               "\r",
               "s", "f", "s", "\r",
               "e", "s", "\r",
               "\r"]
    tastiera = _tastiera(monkeypatch, cassa, copione, file)
    assert asc.main([str(SEME)]) == 0
    assert tastiera.copione == [] and dormite == [] and suonati == []
    primo, secondo = prova.gruppi
    p1, p2, p3 = primo.punti
    q1, q2, q3 = secondo.punti
    # Le lettere sentite, nell'ordine: la rassegna ha in testa il silenzio lungo dopo il via, poi quello del nome.
    attesi = [p1.da_sentire(lettera, asc.ANTICIPO_PRIMA_LETTERA if not i else asc.ANTICIPO_LETTERA) for i, lettera in enumerate(asc.LETTERE)]
    attesi.append(p1.da_sentire("B", asc.ANTICIPO_SCELTA))
    attesi += [p2.da_sentire(lettera, asc.ANTICIPO_LETTERA) for lettera in asc.LETTERE]
    attesi += [p2.da_sentire(lettera, asc.ANTICIPO_SCELTA) for lettera in "ADD"]
    attesi += [p3.da_sentire(lettera, asc.ANTICIPO_LETTERA) for lettera in "AB"]
    attesi += [q1.da_sentire(lettera, asc.ANTICIPO_PRIMA_LETTERA if not i else asc.ANTICIPO_LETTERA) for i, lettera in enumerate(asc.LETTERE)]
    attesi += [q2.da_sentire(lettera, asc.ANTICIPO_LETTERA) for lettera in asc.LETTERE] + [q2.da_sentire("F", asc.ANTICIPO_SCELTA)]
    attesi += [q3.da_sentire(lettera, asc.ANTICIPO_LETTERA) for lettera in asc.LETTERE] + [q3.da_sentire("E", asc.ANTICIPO_SCELTA)]
    assert len(cassa.suonati) == len(attesi) and all(np.array_equal(a, b) for a, b in zip(cassa.suonati, attesi, strict=True))
    assert cassa.fermate == 2
    assert asc.ANTICIPO_PRIMA_LETTERA >= asc.ANTICIPO_LETTERA + 3.0
    assert prova.scelte == {(0, 0): "B", (0, 1): "D", (0, 2): asc.NESSUNA, (1, 1): "F", (1, 2): "E"}
    assert prova.commenti == {(0, 0): "la seconda è più vera"}
    assert prova.svolti == {0, 1} and not prova.interrotti and not prova.chiusi
    assert "\rUna lettera da A a F, n nessuna\r" in tastiera.prompt and "\rD: spazio ripete, s sceglie, n nessuna\r" in tastiera.prompt

    righe = file.read_text(encoding="utf-8").splitlines()
    assert righe[0].startswith("Ascolto di confronto dello schermo centrale, ") and righe[0].endswith(f", seme {SEME}.")
    t1, t2 = primo.titolo, secondo.titolo
    assert righe[1:5] == [f"{t1}, punto 1: hai scelto la B.", f"{t1}, punto 1, il tuo commento: la seconda è più vera", f"{t1}, punto 2: hai scelto la D.",
                          f"{t1}, punto 3: nessuna somiglia al tavolo vero."]
    assert righe[5].startswith(f"{t1}, ") and righe[5].endswith(": la terza lettera mi piace")
    assert righe[6:9] == [f"{t2}, punto 1: senza scelta.", f"{t2}, punto 2: hai scelto la F.", f"{t2}, punto 3: hai scelto la E."]
    assert righe[9].startswith(f"{t2}, ") and righe[9].endswith(": test superato, nessun commento")
    # Fino alla fine, e a ogni prompt della sessione, il file non dice che cosa c'era dietro le lettere.
    assert not any(parola in riga for riga in righe[:10] for parola in DELLA_RIVELAZIONE)
    assert tastiera.letture and not any(parola in lettura for lettura in tastiera.letture for parola in DELLA_RIVELAZIONE)
    # Poi la rivelazione e il riepilogo.
    assert righe[10:] == asc.righe_della_rivelazione(prova) + asc.righe_del_riepilogo(prova)
    assert all(riga.strip() and not riga.startswith(("-", "=", "_")) for riga in righe)

    scritto = capsys.readouterr().out
    assert scritto.startswith("Preparo i punti, qualche secondo.\nAscolto di confronto dello schermo centrale: 2 gruppi, 6 punti, ")
    assert scritto.rstrip().endswith("trovi le tue scelte, quale lettera era quale e il riepilogo.")
    prima_della_fine = scritto.split("Riepilogo, ")[0]
    for parola in VIETATE:
        assert parola not in prima_della_fine, parola
    assert "schermo centrale" in prima_della_fine and "Fischio" not in prima_della_fine
    for testo in ("Punto 1 di 3.\n", "Lettera F.\n", "Rassegna interrotta.\n", "Scelta la B.\n", "Nessuna.\n", "Commento annotato.\n", "Prima ascolta una lettera.\n"):
        assert testo in scritto, testo
    for riga in asc.righe_del_riepilogo(prova):
        assert riga in scritto
    # Le sole righe vuote sono quelle che il menu di collaudo_comune lascia dopo i suoi messaggi.
    linee = scritto.split("\n")
    vuote = [i for i, riga in enumerate(linee[:-1]) if riga == ""]
    assert vuote and all(linee[i - 1] in MESSAGGI_DEL_MENU for i in vuote), [linee[i - 1] for i in vuote]


def test_r_rifa_il_gruppo_con_le_scelte_gia_date(prova, cassa, programma_di_prova, monkeypatch, capsys):
    monkeypatch.setattr(asc, "prepara", lambda _seme: prova)
    monkeypatch.setattr(asc, "enter_escape", _enter_escape_finta([True]))
    monkeypatch.setattr(collaudo_comune, "enter_escape", _enter_escape_finta([True, False]))
    # Il primo giro sceglie la A in tutti e tre i punti; con r il secondo cambia il primo in nessuna e lascia gli altri con Invio.
    giro = ["a", "s", "\r"] * 3
    copione = [*giro, "r", "n", "\r", "\r", "\r", "\r"]
    tastiera = _tastiera(monkeypatch, cassa, copione)
    assert asc.main([]) == 0
    assert tastiera.copione == []
    assert prova.scelte == {(0, 0): asc.NESSUNA, (0, 1): "A", (0, 2): "A"}
    assert "Finora: hai scelto la A.\n" in capsys.readouterr().out
    righe = (programma_di_prova / asc.FILE_DEI_RISULTATI).read_text(encoding="utf-8").splitlines()
    titolo = prova.gruppi[0].titolo
    assert righe[1:4] == [f"{titolo}, punto 1: nessuna somiglia al tavolo vero.", f"{titolo}, punto 2: hai scelto la A.", f"{titolo}, punto 3: hai scelto la A."]
    assert sum(1 for riga in righe if riga.endswith(": test superato, nessun commento")) == 1
    assert f"{prova.gruppi[1].titolo}: gruppo saltato." in righe
    # Il gruppo saltato non si svela.
    assert not any(riga.startswith(f"Rivelazione, {prova.gruppi[1].titolo}") for riga in righe)


def test_escape_chiude_i_punti_e_la_rivelazione_arriva_lo_stesso(prova, cassa, programma_di_prova, monkeypatch, capsys):
    monkeypatch.setattr(asc, "prepara", lambda _seme: prova)
    monkeypatch.setattr(asc, "enter_escape", _enter_escape_finta([True]))
    monkeypatch.setattr(collaudo_comune, "enter_escape", _enter_escape_finta([True, True]))
    # Primo gruppo: la scelta del primo punto, poi Escape mentre suona una lettera del secondo, e il menu
    # chiuso senza giudizio. Secondo gruppo: Escape al commento del primo punto, e Invio al menu.
    copione = ["c", "s", "\r", "b", ("durante", 14, "\x1b"), "\x1b",
               "d", "n", "\x1b", "\r"]
    tastiera = _tastiera(monkeypatch, cassa, copione)
    assert asc.main([]) == 0
    assert tastiera.copione == [] and cassa.fermate == 1
    assert prova.interrotti == {0, 1} and prova.chiusi == {0}
    assert prova.scelte == {(0, 0): "C", (1, 0): asc.NESSUNA}
    righe = (programma_di_prova / asc.FILE_DEI_RISULTATI).read_text(encoding="utf-8").splitlines()
    t1, t2 = prova.gruppi[0].titolo, prova.gruppi[1].titolo
    assert righe[1:4] == [f"{t1}, punto 1: hai scelto la C.", f"{t1}, punto 2: senza scelta.", f"{t1}, punto 3: senza scelta."]
    assert righe[4].endswith(": chiuso senza giudizio")
    rivelazione = asc.righe_della_rivelazione(prova)
    assert f"{t1}: i punti si sono chiusi prima della fine." in rivelazione and f"{t2}: i punti si sono chiusi prima della fine." in rivelazione
    assert righe[-len(rivelazione) - len(asc.righe_del_riepilogo(prova)):] == rivelazione + asc.righe_del_riepilogo(prova)
    riepilogo = asc.righe_del_riepilogo(prova)
    assert riepilogo[0] == f"Riepilogo, {t1}: il gruppo è stato chiuso senza giudizio, e le sue scelte non contano."
    # Contano soltanto i tre punti del secondo gruppo: uno nessuna, due senza scelta.
    assert "Riepilogo, nessuna somiglia al tavolo vero: 1 volta; senza scelta: 2 volte." in riepilogo
    assert capsys.readouterr().out.count("Punti chiusi.") == 2


def test_senza_il_via_non_suona_niente(prova, cassa, programma_di_prova, monkeypatch, capsys):
    monkeypatch.setattr(asc, "prepara", lambda _seme: prova)
    monkeypatch.setattr(asc, "enter_escape", _enter_escape_finta([False]))
    assert asc.main([]) == 0
    assert cassa.suonati == []
    assert not (programma_di_prova / asc.FILE_DEI_RISULTATI).exists()
    assert "\n\n" not in capsys.readouterr().out


def test_i_gruppi_saltati_non_svelano_niente(prova, cassa, programma_di_prova, monkeypatch, capsys):
    monkeypatch.setattr(asc, "prepara", lambda _seme: prova)
    monkeypatch.setattr(asc, "enter_escape", _enter_escape_finta([True]))
    monkeypatch.setattr(collaudo_comune, "enter_escape", _enter_escape_finta([False, False]))
    _tastiera(monkeypatch, cassa, [])
    assert asc.main([]) == 0
    assert cassa.suonati == []
    righe = (programma_di_prova / asc.FILE_DEI_RISULTATI).read_text(encoding="utf-8").splitlines()
    assert righe[1:] == [f"{g.titolo}: gruppo saltato." for g in prova.gruppi]
    assert "Riepilogo" not in capsys.readouterr().out


def test_un_seme_che_non_e_un_numero(cassa, programma_di_prova, capsys):
    assert asc.main(["quattro"]) == 1
    assert cassa.suonati == []
    assert not (programma_di_prova / asc.FILE_DEI_RISULTATI).exists()
    assert "Il seme dev'essere un numero intero" in capsys.readouterr().out


def test_una_scheda_che_non_risponde_non_ferma_l_ascolto(prova, monkeypatch, capsys):
    muta = Cassa(riesce=False)
    monkeypatch.setattr(bs, "Acusticator", muta)
    _tastiera(monkeypatch, muta, ["n", "\r"] * asc.PUNTI_PER_PARTE)
    assert asc.ascolta(prova, 0)
    assert "la scheda audio non risponde" in capsys.readouterr().out


# La rivelazione e il riepilogo, su una prova finta di cui si conoscono le lettere.

def _prova_finta():
    nomi = {"A": types.SimpleNamespace(testo="Mario Rossi"), "B": types.SimpleNamespace(testo="Anna Bianchi")}
    candidato = types.SimpleNamespace(nomi=nomi, momento=types.SimpleNamespace(esito=types.SimpleNamespace(colpo_decisivo="diagonalesx")))
    ordini = (("oggi", "netto", "netto_ritorno", "legno", "plastica", "oggi"), ("netto", "netto_ritorno", "legno", "plastica", "oggi", "legno"))
    gruppi = [asc.Gruppo(parte, titolo, [asc.Punto(candidato, parte, ordine, {}) for ordine in ordini]) for parte, titolo in asc.GRUPPI]
    prova = asc.Prova(SEME, gruppi)
    prova.svolti = {0, 1}
    return prova


def test_la_rivelazione_e_il_riepilogo():
    prova = _prova_finta()
    # Primo gruppo: la C, netto col ritorno, e la F, legno col ritorno, identica alla C. Secondo: la C, netto col ritorno, e nessuna.
    prova.scelte = {(0, 0): "C", (0, 1): "F", (1, 0): "C", (1, 1): asc.NESSUNA}
    t1, t2 = prova.gruppi[0].titolo, prova.gruppi[1].titolo
    colpo = f"{C.con_articolo('diagonalesx')} di"
    righe = asc.righe_della_rivelazione(prova)
    assert righe[:5] == [f"Rivelazione, la versione {v.nome}: {v.descrizione}." for v in asc.VERSIONI]
    assert righe[5] == (f"Rivelazione, {t1}, punto 1, {colpo} Mario Rossi, del tuo giocatore: A oggi, B netto, C netto col ritorno, D legno col ritorno, "
                        "E plastica col ritorno, F oggi; le lettere A e F erano identiche campione per campione, la versione oggi ripetuta; "
                        "hai scelto la C, netto col ritorno.")
    assert righe[6].endswith("; le lettere C e F erano identiche campione per campione, la versione legno col ritorno ripetuta; "
                             "hai scelto la F, legno col ritorno, una delle due lettere identiche.")
    assert righe[7].startswith(f"Rivelazione, {t2}, punto 1, {colpo} Anna Bianchi, dell'avversario: ") and righe[7].endswith("; hai scelto la C, netto col ritorno.")
    assert righe[8].endswith("; nessuna somiglia al tavolo vero.")
    assert asc.righe_del_riepilogo(prova) == [
        "Riepilogo, oggi: scelta 0 volte su 4 punti, 0 nei tiri del tuo giocatore e 0 in quelli dell'avversario.",
        "Riepilogo, netto: scelta 0 volte su 4 punti, 0 nei tiri del tuo giocatore e 0 in quelli dell'avversario.",
        "Riepilogo, netto col ritorno: scelta 2 volte su 4 punti, 1 nei tiri del tuo giocatore e 1 in quelli dell'avversario.",
        "Riepilogo, legno col ritorno: scelta 1 volta su 4 punti, 1 nei tiri del tuo giocatore e 0 in quelli dell'avversario.",
        "Riepilogo, plastica col ritorno: scelta 0 volte su 4 punti, 0 nei tiri del tuo giocatore e 0 in quelli dell'avversario.",
        "Riepilogo, nessuna somiglia al tavolo vero: 1 volta; senza scelta: 0 volte.",
        "Riepilogo, i controlli: in ogni punto una versione stava sotto due lettere identiche, e hai scelto una delle due 1 volta; "
        "scegliendo a caso succederebbe nel 33% dei punti.",
        "Riepilogo, le lettere scelte: la A 0 volte, la B 0 volte, la C 2 volte, la D 0 volte, la E 0 volte, la F 1 volta.",
    ]
    # Senza punti da contare il riepilogo lo dice.
    prova.chiusi = {0, 1}
    assert asc.righe_del_riepilogo(prova)[-1] == "Riepilogo: nessun punto da contare."


# Le due aggiunte di partita_sonora per lo strumento.

def test_il_ritocco_e_la_sorgente_del_preset_lasciano_la_partita_com_era(preparazione):
    _candidati, prova = preparazione
    eventi = resa.azione(_punti(prova)[0].candidato.momento.eventi)
    senza = ps.componi(eventi, "A")
    uguale = ps.componi(eventi, "A", ritocco=lambda posati: posati)
    assert np.array_equal(senza.buffer, uguale.buffer) and [p.ruolo for p in senza.posati] == [p.ruolo for p in uguale.posati]
    # Il ritocco vede i suoni posati e decide quelli da comporre: senza nessuno, il buffer è silenzio.
    muto = ps.componi(eventi, "A", ritocco=lambda _posati: [])
    assert muto.posati == [] and not np.any(muto.buffer)
    for ruolo in ("schermo", "fischio_singolo", "rotolamento"):
        for variante in range(ps.VARIANTI_RUMORE):
            assert ps.sorgente(ruolo, variante) is ps.sorgente_del_preset(ps.SUONI[ruolo], variante)
    with pytest.raises(KeyError, match="del ruolo schermo non c'è"):
        ps.sorgente_del_preset("mess_partita_che_non_esiste", ruolo="schermo")
