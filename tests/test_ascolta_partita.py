"""
Test dell'ascolto libero della partita, strumenti/ascolta_partita.py, e del prototipo della resa,
strumenti/resa_prototipo.py, senza mai suonare: la cassa di Acusticator è sostituita da un
registratore, e quella vera, se qualcuno la chiamasse, fa fallire la prova. I preset segnaposto:
esistono, sono tutti diversi, nessuno è della finestra né un'onda quadra. Il suono si sceglie da
tipo, esito e causa dell'evento; l'azione va dal fischio del via al punto; lo spazio si ribalta per
l'altro giocatore; i rumori hanno le loro varianti, e due dello stesso ruolo di fila non sono mai
uguali; la pallina che vola fuori dal tavolo non rotola. Poi lo strumento: compone tutti i punti
scelti senza suonare e senza scrivere, nessun buffer supera il margine, i punti sono quelli
dichiarati e sempre gli stessi, la cronaca dice dove comincia il suono e la legenda nomina i suoni
provvisori; i tasti e il menu di fine gruppo funzionano con una tastiera finta da copione, e lo
strumento non scrive righe vuote di suo.
"""

import collections
import itertools
import sys
import types
from pathlib import Path

import collaudo_comune
import numpy as np
import pytest
from GBUtils import Acusticator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))

import ascolta_partita as ap
import resa_prototipo as resa

import percorsi
import suoni
from motore import eventi as E
from motore.eventi import Evento, Tappa
from motore.tavolo import vista

# I messaggi del menu di collaudo_comune, che dopo di sé lascia una riga vuota.
MESSAGGI_DEL_MENU = ("Annotato.", "Segnato come superato.", "Chiuso.")


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
    sono tasti per le attese senza scadenza; un'occhiata mentre il punto suona trova il tasto solo
    se la voce seguente è una coppia ("durante", tasto), altrimenti fa passare il tempo dell'orologio
    finto e torna la scadenza.
    """

    def __init__(self, copione):
        self.copione = list(copione)
        self.adesso = 0.0

    def orologio(self):
        return self.adesso

    def __call__(self, prompt="", attesa=None, alla_scadenza=""):
        if attesa is not None:
            if self.copione and isinstance(self.copione[0], tuple):
                return self.copione.pop(0)[1]
            self.adesso += attesa
            return alla_scadenza
        print(prompt, end="")
        voce = self.copione.pop(0)
        assert isinstance(voce, str), f"il copione aspettava un tasto, trova {voce!r}"
        return voce


@pytest.fixture
def cassa(monkeypatch):
    finta = Cassa()
    monkeypatch.setattr(ap, "Acusticator", finta)
    return finta


def _tastiera(monkeypatch, copione):
    tastiera = Tastiera(copione)
    monkeypatch.setattr(ap, "key", tastiera)
    monkeypatch.setattr(collaudo_comune, "key", tastiera)
    monkeypatch.setattr(ap, "orologio", tastiera.orologio)
    return tastiera


@pytest.fixture(scope="module")
def preparazione(tmp_path_factory):
    """
    I gruppi composti una volta per tutto il modulo. Una fixture di modulo parte prima di quelle
    automatiche di ogni prova, compresi la cassa vietata e il registratore del conftest: perciò le
    protezioni le mette lei, finché prepara lavora. La cassa vera di Acusticator e il motore dei
    suoni della finestra sono vietati, e la cartella del programma è una cartella temporanea.
    Restituisce i gruppi, le chiamate arrivate alle funzioni vietate e la cartella.
    """
    chiamate = []
    cartella = tmp_path_factory.mktemp("ascolto_partita")
    with pytest.MonkeyPatch.context() as mp:
        _vieta_la_cassa(mp, chiamate)
        mp.setattr(suoni, "_riproduci", _vietato("suoni._riproduci", chiamate))
        mp.setattr(percorsi, "cartella", lambda: str(cartella))
        gruppi = ap.prepara()
    return gruppi, chiamate, cartella


@pytest.fixture(scope="module")
def gruppi(preparazione):
    return preparazione[0]


@pytest.fixture(scope="module")
def punti(gruppi):
    return [p for _titolo, punti in gruppi for p in punti]


def _evento(tipo, n=10, t=5.0, **campi):
    return Evento(n=n, t=t, tipo=tipo, fase=E.GIOCO, **campi)


# I preset segnaposto.

def test_ogni_ruolo_ha_il_suo_preset_e_nessuno_e_della_finestra():
    preset = list(resa.SUONI.values())
    assert len(preset) == len(set(preset)), "due ruoli con lo stesso preset"
    for ruolo, nome in resa.SUONI.items():
        score, kind, _adsr = Acusticator.preset(nome)
        assert score, f"il preset {nome} del ruolo {ruolo} non c'è"
        assert kind != 2, f"{nome} è un'onda quadra"
    assert not set(preset) & set(suoni.EVENTI.values()), "un preset della partita suona già nella finestra"


# La scelta del suono.

@pytest.mark.parametrize(("campi", "attesi"), [
    ({"tipo": E.BATTUTA, "esito": "regolare"}, [("battuta", 0.0)]),
    ({"tipo": E.BATTUTA, "esito": "irregolare", "causa": "battuta_a_vuoto"}, [("colpo_a_vuoto", 0.0)]),
    ({"tipo": E.BATTUTA, "esito": "irregolare", "causa": "battuta_doppio_tocco"}, [("battuta", 0.0), ("secondo_tocco", resa.RITARDO_SECONDO_TOCCO)]),
    ({"tipo": E.BATTUTA, "esito": "irregolare", "causa": "battuta_prima_del_fischio"}, [("battuta", 0.0)]),
    ({"tipo": E.COLPO, "esito": "colpo"}, [("colpo", 0.0)]),
    ({"tipo": E.COLPO, "esito": "fallo", "causa": "paletta_caduta"}, []),
    ({"tipo": E.PARATA, "esito": "fermata"}, [("parata", 0.0)]),
    ({"tipo": E.PARATA, "esito": "ribattuta"}, [("parata", 0.0)]),
    ({"tipo": E.PARATA, "esito": "goal", "causa": "goal_scambio"}, []),
    ({"tipo": E.PARATA, "esito": "fallo", "causa": "body_touch"}, []),
    ({"tipo": E.PARATA, "esito": "fallo", "causa": "paletta_caduta"}, []),
    ({"tipo": E.PARATA, "esito": "fallo", "causa": "difesa_irregolare"}, [("parata", 0.0)]),
    ({"tipo": E.FALLO, "esito": "fallo", "causa": "paletta_caduta"}, [("paletta_caduta", 0.0)]),
    ({"tipo": E.FALLO, "esito": "fallo", "causa": "out_sponda"}, []),
    ({"tipo": E.PALLA_MORTA, "esito": "palla_morta", "causa": "colpo_debole"}, []),
    ({"tipo": E.GOAL, "esito": "goal", "causa": "goal_battuta"}, [("goal", 0.0)]),
    ({"tipo": E.ANNUNCIO}, []),
    ({"tipo": E.CHIAMATA, "chiamata": "out"}, []),
    ({"tipo": E.DOMANDA_PRONTO}, []),
])
def test_il_suono_si_sceglie_da_tipo_esito_e_causa(campi, attesi):
    assert resa.suoni_fermi(_evento(**campi)) == attesi


def test_il_secondo_tocco_arriva_dopo_la_battuta():
    battuta = _evento(E.BATTUTA, pos=(80.0, 25.0), esito="irregolare", causa="battuta_doppio_tocco")
    posati = resa.posati_dell_evento(battuta)
    assert [p.ruolo for p in posati] == ["battuta", "secondo_tocco"]
    assert posati[1].t - posati[0].t == pytest.approx(resa.RITARDO_SECONDO_TOCCO)


def test_l_azione_va_dal_fischio_del_via_alla_fine_del_punto(punti):
    for punto in punti:
        azione = resa.azione(punto.candidato.momento.eventi)
        tipi = [e.tipo for e in azione]
        assert tipi[-1] in resa.FINE_AZIONE
        assert tipi[0] == E.FISCHIO and tipi[1] == E.BATTUTA
        assert not set(tipi) & resa.PROCEDURA
    # Chi batte prima del fischio fa cominciare l'azione dalla battuta.
    eventi = [_evento(E.ANNUNCIO, n=1, t=1.0), _evento(E.BATTUTA, n=2, t=2.0), _evento(E.FISCHIO, n=3, t=2.2, fischio=E.SINGOLO),
              _evento(E.FALLO, n=4, t=2.2), _evento(E.PUNTO, n=5, t=3.0), _evento(E.CAMBIO_BATTITORE, n=6, t=9.0)]
    assert [e.n for e in resa.azione(eventi)] == [2, 3, 4, 5]


# Lo spazio e le sorgenti.

def test_ogni_suono_sta_al_suo_campione():
    eventi = [_evento(E.FISCHIO, n=1, t=1.0, pos=(-50.0, 183.0), durata=0.35, fischio=E.SINGOLO),
              _evento(E.BATTUTA, n=2, t=1.5, pos=(80.0, 25.0), esito="regolare"), _evento(E.PUNTO, n=3, t=2.0)]
    composto = resa.componi(eventi, "A")
    assert composto.t0 == 1.0 and [p.ruolo for p in composto.posati] == ["fischio_singolo", "battuta"]
    battuta = resa.spazializza(composto.posati[1], "A")
    inizio = round(0.5 * resa.FS)
    assert np.array_equal(composto.buffer[inizio:inizio + len(battuta)], battuta)
    assert not np.any(composto.buffer[round(0.36 * resa.FS):inizio])


def test_lo_spazio_si_ribalta_per_l_altro_giocatore():
    # Un colpo alla sinistra di A, vicino a lui: per A suona a sinistra e forte, per B a destra e piano.
    posato = resa._fermo("colpo", 0.0, (20.0, 30.0), 1)
    per_a = resa.spazializza(posato, "A")
    per_b = resa.spazializza(posato, "B")
    energia = lambda s, canale: float(np.sum(s[:, canale].astype(np.float64) ** 2))  # noqa: E731
    assert energia(per_a, 0) > 4 * energia(per_a, 1)
    assert energia(per_b, 1) > 4 * energia(per_b, 0)
    assert energia(per_a, 0) > energia(per_b, 1)


def test_i_rumori_hanno_le_loro_varianti_e_i_toni_no():
    resa.svuota_cache()
    prima = resa.sorgente("parata", variante=0)
    assert resa.sorgente("parata", variante=resa.VARIANTI_RUMORE) is prima
    assert not np.array_equal(resa.sorgente("parata", variante=1)[:len(prima)], prima)
    assert resa.sorgente("colpo", variante=0) is resa.sorgente("colpo", variante=3)


def test_due_rumori_di_fila_dello_stesso_ruolo_non_sono_mai_uguali(punti):
    # Nei punti veri, dove gli eventi dello scambio tornano con un passo di quattro: parate,
    # sponde, controlli e rotolamenti, uno dopo l'altro, non sono mai lo stesso suono campione per campione.
    rumori = {ruolo for ruolo, nome in resa.SUONI.items() if Acusticator.preset(nome)[1] in resa.KIND_DI_RUMORE}
    assert {"parata", "sponda", "controllo", "rotolamento"} <= rumori
    coppie = collections.Counter()
    for punto in punti:
        posati = resa.componi(resa.azione(punto.candidato.momento.eventi), punto.ascoltatore).posati
        for ruolo in rumori:
            for a, b in itertools.pairwise(p for p in posati if p.ruolo == ruolo):
                coppie[ruolo] += 1
                n = min(len(a.mono), len(b.mono))
                assert not np.array_equal(a.mono[:n], b.mono[:n]), f"{punto.chiave}, {punto.ascoltatore}: due {ruolo} di fila uguali, eventi {a.evento} e {b.evento}"
    # Le coppie sono abbastanza perché la prova dica qualcosa: lo scambio lungo da solo ha undici parate.
    assert coppie["parata"] >= 10 and coppie["controllo"] >= 5 and coppie["sponda"] >= 3, coppie


def _volo_fuori(causa, lancio=E.COLPO):
    """Un colpo, o una battuta, e il suo volo con le tappe dell'out: partenza, fuori dal bordo sinistro e terra."""
    tappe = (Tappa(5.0, 30.0, 40.0, 400.0, "partenza"), Tappa(5.277, 0.0, 160.0, 320.0, "fuori"), Tappa(5.437, -40.0, 210.0, 0.0, "terra"))
    esito = "irregolare" if lancio == E.BATTUTA else "fallo"
    return [_evento(lancio, n=10, chi=1, pos=(30.0, 40.0), esito=esito, causa=causa),
            _evento(E.VOLO, n=11, chi=1, pos=(-40.0, 210.0), durata=0.437, volo=tappe)]


@pytest.mark.parametrize(("causa", "lancio", "rotola"), [
    ("out_sponda", E.COLPO, True),
    ("out_volo", E.COLPO, False),
    ("out_volo", E.BATTUTA, False),
])
def test_la_pallina_che_vola_fuori_dal_tavolo_non_rotola(causa, lancio, rotola):
    # Le tappe sono le stesse: la pallina che salta la sponda rotola fino al bordo, quella che vola fuori no.
    ruoli = [p.ruolo for p in resa.posa(_volo_fuori(causa, lancio))]
    assert ("rotolamento" in ruoli) == rotola
    assert ruoli.count("terra") == 1
    # Il volo da solo, senza il colpo che lo lancia, resta quello di prima: le tappe non bastano a dirlo in aria.
    assert "rotolamento" in [p.ruolo for p in resa.posati_dell_evento(_volo_fuori(causa, lancio)[1])]


def test_il_margine_tiene_qualunque_livello():
    forte = np.full((1000, 2), 0.5, dtype=np.float32)
    forte[10, 0] = 2.0
    abbassato = resa.con_margine(forte)
    assert float(np.max(np.abs(abbassato))) <= resa.TETTO
    assert abbassato[20, 1] == pytest.approx(0.5 * resa.TETTO / 2.0)
    piano = np.full((1000, 2), 0.3, dtype=np.float32)
    assert np.array_equal(resa.con_margine(piano), piano * np.float32(resa.GUADAGNO_PARTITA))


# Lo strumento.

def test_lo_strumento_compone_tutti_i_punti_senza_suonare(preparazione, punti):
    gruppi, chiamate, cartella = preparazione
    # Durante la composizione la cassa vera e i suoni della finestra erano vietati: nessuno li ha
    # chiamati, e nella cartella del programma non è nato niente.
    assert chiamate == []
    assert list(cartella.iterdir()) == []
    assert [titolo for titolo, _punti in gruppi] == [titolo for titolo, _voci in ap.GRUPPI]
    assert [len(p) for _titolo, p in gruppi] == [3, 2, 3]
    anticipo = round(ap.ANTICIPO * resa.FS)
    for punto in punti:
        buffer = punto.buffer
        assert buffer.dtype == np.float32 and buffer.ndim == 2 and buffer.shape[1] == 2
        assert len(buffer) > anticipo + resa.FS
        assert not np.any(buffer[:anticipo])
        assert np.any(buffer[anticipo:anticipo + round(0.05 * resa.FS)]), f"{punto.chiave}: il fischio del via non c'è"
        assert punto.ruoli[0] == "fischio_singolo" and set(punto.ruoli) == set(_ruoli(punto))


def test_nessun_punto_supera_il_margine(punti):
    for punto in punti:
        assert float(np.max(np.abs(punto.buffer))) <= resa.TETTO, punto.chiave


def _ruoli(punto):
    return collections.Counter(p.ruolo for p in resa.componi(resa.azione(punto.candidato.momento.eventi), punto.ascoltatore).posati)


def test_i_punti_sono_quelli_dichiarati(punti):
    per_chiave = collections.defaultdict(list)
    for punto in punti:
        per_chiave[punto.chiave].append(punto)
    assert [(p.chiave, p.ascoltatore) for p in punti] == [voce for _titolo, voci in ap.GRUPPI for voce in voci]
    # La diagonale: l'ultimo colpo attraversa il tavolo e arriva in gioco; dall'altra testata è la stessa, con i lati scambiati.
    da_a, da_b = per_chiave["diagonale"]
    assert da_a.candidato is da_b.candidato and (da_a.ascoltatore, da_b.ascoltatore) == ("A", "B")
    colpo, volo = ap.voli_della_pallina(da_a.candidato)[-1]
    assert colpo.colpo.startswith("diagonale") and ap.escursione(volo) >= 1.0
    assert ap.escursione(volo, "B") == pytest.approx(ap.escursione(volo))
    assert da_b.titolo == ap.TITOLO_DALL_ALTRA_PARTE
    # Il tuo goal, nella porta lontana.
    esito = per_chiave["goal_tuo_lontano"][0].candidato.momento.esito
    assert (esito.esito, esito.causa, esito.a_chi) == ("goal", "goal_scambio", "A")
    goal = next(e for e in per_chiave["goal_tuo_lontano"][0].candidato.momento.eventi if e.tipo == E.GOAL)
    assert vista(goal.pos, "A")[1] > 300
    # Il goal di battuta dell'avversario, senza la parata che non arriva.
    punto = per_chiave["goal_di_battuta"][0]
    esito = punto.candidato.momento.esito
    assert (esito.causa, esito.a_chi, esito.parte_battitore) == ("goal_battuta", "B", "B")
    assert _ruoli(punto)["parata"] == 0 and _ruoli(punto)["goal"] == 1
    # Lo scambio lungo.
    assert per_chiave["scambio_lungo"][0].candidato.momento.esito.attacchi >= 8
    # L'out a terra e lo schermo centrale, con i loro suoni.
    punto = per_chiave["out_a_terra"][0]
    assert punto.candidato.momento.esito.causa.startswith("out") and _ruoli(punto)["terra"] == 1
    punto = per_chiave["schermo_centrale"][0]
    assert punto.candidato.momento.esito.causa == "schermo_contro" and _ruoli(punto)["schermo"] == 1
    # Il fallo che fa un rumore suo, con il suo suono e il titolo giusto.
    punto = per_chiave["rumore"][0]
    causa = punto.candidato.momento.esito.causa
    assert punto.titolo == ap.TITOLI_DEL_RUMORE[causa]
    suono = {"paletta_caduta": "paletta_caduta", "battuta_a_vuoto": "colpo_a_vuoto", "battuta_doppio_tocco": "secondo_tocco"}[causa]
    assert _ruoli(punto)[suono] == 1
    # Le righe: chi sei, l'avversario, l'arbitro e la cronaca, senza separatori né righe vuote.
    for punto in punti:
        nomi = punto.candidato.nomi
        altro = "B" if punto.ascoltatore == "A" else "A"
        assert punto.righe[0].startswith(f"Sei {nomi[punto.ascoltatore].testo}, ") and nomi[altro].testo in punto.righe[0]
        assert "l'arbitro sta alla tua " in punto.righe[0]
        assert len(punto.righe) > 3 and all(riga.strip() for riga in punto.righe)


def test_la_cronaca_dice_dove_comincia_il_suono(punti):
    # Dopo l'annuncio, che è soltanto parole, e subito prima della battuta: il fischio del via.
    for punto in punti:
        righe = punto.righe
        assert righe.count(ap.INIZIO_COL_FISCHIO) == 1 and ap.INIZIO_CON_LA_BATTUTA not in righe
        i = righe.index(ap.INIZIO_COL_FISCHIO)
        assert i > 1 and righe[i + 1].startswith("Battuta"), righe[i + 1]
    # Chi batte prima del fischio fa cominciare il suono dalla battuta.
    candidato = punti[0].candidato
    eventi = list(candidato.momento.eventi)
    i = next(i for i, e in enumerate(eventi) if e.tipo == E.BATTUTA)
    assert eventi[i - 1].tipo == E.FISCHIO
    eventi[i - 1], eventi[i] = eventi[i], eventi[i - 1]
    righe = ap.presentazione(candidato._replace(momento=types.SimpleNamespace(eventi=eventi)), "A")
    assert ap.INIZIO_COL_FISCHIO not in righe
    assert righe[righe.index(ap.INIZIO_CON_LA_BATTUTA) + 1].startswith("Battuta")


def test_la_legenda_nomina_i_suoni_che_si_sentono(gruppi):
    # Ogni ruolo della resa ha la sua voce, e la legenda stampa soltanto quelli dei punti, col loro preset.
    assert set(ap.LEGENDA) == set(resa.SUONI)
    usati = {ruolo for _titolo, punti in gruppi for punto in punti for ruolo in punto.ruoli}
    righe = ap.legenda(gruppi)
    assert len(righe) == len(usati) == len(set(righe))
    for ruolo in usati:
        evento, come = ap.LEGENDA[ruolo]
        assert f"{evento}: {come}, preset {resa.SUONI[ruolo]}." in righe
    assert {"fischio_singolo", "battuta", "parata", "sponda", "rotolamento", "controllo", "goal", "fischio_doppio"} <= usati
    assert righe[0].startswith("Il fischio dell'arbitro")
    assert all(riga.strip() and not riga.startswith(("-", "=", "_")) for riga in righe)


def test_i_punti_sono_sempre_gli_stessi():
    prima = ap.scegli(ap.punti_giocati())
    dopo = ap.scegli(ap.punti_giocati())
    impronta = lambda scelti: {k: (c.seme, c.momento.esito.set_n, c.momento.esito.punto_n) for k, c in scelti.items()}  # noqa: E731
    assert impronta(prima) == impronta(dopo)
    assert set(prima) == {s.chiave for s in ap.SCELTE}


# I tasti e il menu.

def test_l_ascolto_fa_sentire_ogni_punto_del_gruppo(gruppi, cassa, monkeypatch, capsys):
    _titolo, punti = gruppi[0]
    # Invio lo fa sentire, e finito il punto spazio lo ripete e Invio passa oltre: il primo si ripete una volta.
    _tastiera(monkeypatch, ["\r", " ", "\r"] + ["\r", "\r"] * (len(punti) - 1))
    ap.ascolta(punti)
    attesi = [punti[0].buffer] + [p.buffer for p in punti]
    assert len(cassa.suonati) == len(attesi) and all(a is b for a, b in zip(cassa.suonati, attesi, strict=True))
    assert cassa.fermate == 0
    scritto = capsys.readouterr().out
    assert f"1 di {len(punti)}: {punti[0].titolo}." in scritto
    assert "\rInvio per sentirlo, Escape chiude il gruppo.\r" in scritto
    assert "\n\n" not in scritto


def test_un_tasto_mentre_il_punto_suona_lo_ferma(gruppi, cassa, monkeypatch):
    _titolo, punti = gruppi[0]
    # Il primo punto riparte con lo spazio premuto mentre suona, e poi si lascia con Invio a metà;
    # il secondo si ascolta fino in fondo, e Escape chiude il gruppo.
    tastiera = _tastiera(monkeypatch, ["\r", ("durante", "x"), ("durante", " "), ("durante", "\r"), "\r", "\x1b"])
    ap.ascolta(punti)
    assert [len(b) for b in cassa.suonati] == [len(punti[0].buffer)] * 2 + [len(punti[1].buffer)]
    assert cassa.fermate == 2
    assert tastiera.copione == []
    # Il secondo punto ha aspettato la sua durata, più la coda.
    assert tastiera.adesso >= len(punti[1].buffer) / resa.FS + ap.CODA - 1e-9


def test_escape_chiude_il_gruppo(gruppi, cassa, monkeypatch):
    _titolo, punti = gruppi[1]
    _tastiera(monkeypatch, ["\r", "\x1b"])
    ap.ascolta(punti)
    assert len(cassa.suonati) == 1
    _tastiera(monkeypatch, ["\x1b"])
    ap.ascolta(punti)
    assert len(cassa.suonati) == 1
    # Escape premuto mentre il punto suona chiude anche lui il gruppo.
    _tastiera(monkeypatch, ["\r", ("durante", "\x1b")])
    ap.ascolta(punti)
    assert len(cassa.suonati) == 2 and cassa.fermate == 1


def test_una_scheda_che_non_risponde_non_ferma_l_ascolto(gruppi, monkeypatch, capsys):
    monkeypatch.setattr(ap, "Acusticator", Cassa(riesce=False))
    _titolo, punti = gruppi[1]
    _tastiera(monkeypatch, ["\r", "\r"] * len(punti))
    ap.ascolta(punti)
    assert "la scheda audio non risponde" in capsys.readouterr().out


def _enter_escape_finta(risposte):
    """Al posto di enter_escape di GBUtils: scrive il prompt e va a capo come quella vera, e risponde dal copione."""
    risposte = iter(risposte)

    def enter_escape(prompt="", *_args, **_kwargs):
        print(prompt)
        return next(risposte)

    return enter_escape


def test_il_menu_di_fine_gruppo_scrive_una_riga_per_voce(gruppi, cassa, cartella_di_prova, suonati, monkeypatch, capsys):
    monkeypatch.setattr(ap, "prepara", lambda: gruppi)
    monkeypatch.setattr(ap, "enter_escape", _enter_escape_finta([True]))
    monkeypatch.setattr(ap.time, "sleep", lambda _secondi: None)
    # Il primo gruppo si ascolta e si commenta, il secondo si salta, il terzo si riascolta con r e si chiude senza giudizio.
    monkeypatch.setattr(collaudo_comune, "enter_escape", _enter_escape_finta([True, False, True]))
    monkeypatch.setattr(collaudo_comune, "dgt", lambda *_a, **_k: "la diagonale si sente bene ")
    primo, terzo = len(gruppi[0][1]), len(gruppi[2][1])
    _tastiera(monkeypatch, ["\r", "\r"] * primo + ["c", "\r"] + ["\r", "\r"] * terzo + ["r"] + ["\r", "\r"] * terzo + ["\x1b"])
    assert ap.main() == 0
    assert len(cassa.suonati) == primo + 2 * terzo
    righe = (cartella_di_prova / ap.FILE_DEGLI_ESITI).read_text(encoding="utf-8").splitlines()
    assert len(righe) == 2
    assert righe[0].startswith(f"{gruppi[0][0]}, ") and righe[0].endswith(": la diagonale si sente bene")
    assert righe[1].startswith(f"{gruppi[2][0]}, ") and righe[1].endswith(": chiuso senza giudizio")
    scritto = capsys.readouterr().out
    assert scritto.startswith("Ascolto libero della partita di MESS: 3 gruppi, 8 punti, ")
    assert scritto.rstrip().endswith("Fine dell'ascolto.")
    # La legenda viene prima del via.
    assert all(f"\n{riga}\n" in scritto.split("\rInvio per cominciare")[0] for riga in ap.legenda(gruppi))
    # Le sole righe vuote sono quelle che il menu di collaudo_comune lascia dopo i suoi messaggi.
    righe = scritto.split("\n")
    vuote = [i for i, riga in enumerate(righe[:-1]) if riga == ""]
    assert vuote and all(righe[i - 1] in MESSAGGI_DEL_MENU for i in vuote), [righe[i - 1] for i in vuote]
    assert suonati == []


def test_senza_il_via_non_suona_niente(gruppi, cassa, cartella_di_prova, monkeypatch, capsys):
    monkeypatch.setattr(ap, "prepara", lambda: gruppi)
    monkeypatch.setattr(ap, "enter_escape", _enter_escape_finta([False]))
    assert ap.main() == 0
    assert cassa.suonati == []
    assert not (cartella_di_prova / ap.FILE_DEGLI_ESITI).exists()
    assert "\n\n" not in capsys.readouterr().out
