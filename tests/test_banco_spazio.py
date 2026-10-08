"""
Test del banco dello spazio, strumenti/banco_spazio.py, e delle leggi dello spazio che ha aggiunto
a strumenti/resa_prototipo.py, senza mai suonare: la cassa di Acusticator è sostituita da un
registratore, e quella vera, se qualcuno la chiamasse, fa fallire la prova. Le leggi: quella di
oggi dà la resa di prima campione per campione, le altre fanno quello che dicono. I candidati: in
ogni gruppo cambia soltanto la sua dimensione, e sui buffer sono davvero diversi, con le grandezze
misurate, cioè il contrasto fra lontano e vicino, gli acuti persi in fondo e allo schermo e il pan
nelle due metà del tavolo. Il controllo è identico campione per campione; l'ordine si mescola e si
ripete con lo stesso seme; il livello è comune. Poi la sessione intera con una tastiera finta da
copione: la rassegna, il voto con i suoi tasti, anche mentre una lettera suona, il menu di fine
gruppo, il gruppo finale, e il file dei risultati, che svela le lettere solo alla fine e somma i
voti per candidato; a schermo nessun nome di candidato e nessuna riga vuota dello strumento.
"""

import functools
import itertools
import math
import random
import sys
from pathlib import Path

import collaudo_comune
import numpy as np
import pytest
from GBUtils import Acusticator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))

import banco_spazio as bs
import resa_prototipo as resa

import percorsi
import suoni
from motore.tavolo import vista, volume

FS = resa.FS
SEME = 4127
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
    stringa sono i tasti delle attese senza scadenza. Mentre un suono è in corso, un'occhiata alla
    tastiera trova un tasto solo se in testa al copione c'è una terna ("durante", n, tasto) e il
    suono in corso è l'n-esimo della cassa; altrimenti fa passare il tempo dell'orologio finto e
    torna la scadenza, così il suono arriva alla fine.
    """

    def __init__(self, copione, cassa):
        self.copione = list(copione)
        self.cassa = cassa
        self.adesso = 0.0

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
        voce = self.copione.pop(0)
        assert isinstance(voce, str), f"il copione aspettava un tasto, trova {voce!r}"
        return voce


@pytest.fixture
def cassa(monkeypatch):
    finta = Cassa()
    monkeypatch.setattr(bs, "Acusticator", finta)
    return finta


def _tastiera(monkeypatch, cassa, copione):
    tastiera = Tastiera(copione, cassa)
    monkeypatch.setattr(bs, "key", tastiera)
    monkeypatch.setattr(collaudo_comune, "key", tastiera)
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
def banco(tmp_path_factory):
    """
    I punti e i materiali dei tre gruppi, composti una volta per tutto il modulo. Una fixture di
    modulo parte prima di quelle automatiche di ogni prova: perciò le protezioni le mette lei. La
    cassa vera e il motore dei suoni della finestra sono vietati, e la cartella del programma è
    temporanea. Restituisce i punti, i materiali per chiave, le chiamate vietate e la cartella.
    """
    chiamate = []
    cartella = tmp_path_factory.mktemp("banco_spazio")
    with pytest.MonkeyPatch.context() as mp:
        _vieta_la_cassa(mp, chiamate)
        mp.setattr(suoni, "_riproduci", _vietato("suoni._riproduci", chiamate))
        mp.setattr(percorsi, "cartella", lambda: str(cartella))
        punti = bs.punti_del_banco()
        materiali = {d.chiave: bs.componi_dimensione(d, punti) for d in bs.DIMENSIONI}
    return punti, materiali, chiamate, cartella


@pytest.fixture
def prove(banco):
    """Le prove dei tre gruppi, nuove per ogni prova perché raccolgono i voti, sui materiali già composti."""
    punti, materiali, _chiamate, _cartella = banco
    return bs.prepara(SEME, punti, materiali)


def _materiali(banco, chiave):
    return banco[1][chiave]


# Le misure sui buffer.

def _finestra(materiale, punto, ruolo, quale=0, durata=0.03, da=0.0):
    """Il tratto del materiale che comincia con il suono posato del ruolo, nel punto indicato: quale dice quale dei posati di quel ruolo."""
    rese = materiale.rese[punto]
    posato = [p for p in rese.posati if p.ruolo == ruolo][quale]
    inizio = materiale.inizi[punto] + round((posato.t - rese.t0 + da) * FS)
    return materiale.buffer[inizio:inizio + round(durata * FS)].astype(np.float64), posato


def _decibel(x):
    return 10.0 * math.log10(float(np.mean(x ** 2)))


def _acuti(x, soglia=5000.0):
    """L'energia sopra la soglia, in hertz, del tratto stereo, con la finestra di Hann."""
    spettro = np.abs(np.fft.rfft(x * np.hanning(len(x))[:, None], axis=0)) ** 2
    return float(np.sum(spettro[np.fft.rfftfreq(len(x), 1.0 / FS) >= soglia]))


def _pan(x):
    """Il pan che la legge a potenza costante della resa dà a un tratto stereo, dalle energie dei due canali."""
    sinistra, destra = float(np.sum(x[:, 0] ** 2)), float(np.sum(x[:, 1] ** 2))
    return math.atan2(math.sqrt(destra), math.sqrt(sinistra)) * 4.0 / math.pi - 1.0


# Le leggi dello spazio.

def test_lo_spazio_di_oggi_da_la_resa_di_prima(banco):
    punti = banco[0]
    for chiave, punto in punti.items():
        azione = resa.azione(punto.momento.eventi)
        for ascoltatore in "AB":
            prima = resa.componi(azione, ascoltatore).buffer
            assert np.array_equal(resa.componi(azione, ascoltatore, resa.Spazio()).buffer, prima), (chiave, ascoltatore)
    # I campi di oggi sono quelli del motore: il pan e la distanza della vista, il volume e il taglio di sempre.
    posizioni = [(3.0, 20.0), (61.0, 183.0), (-50.0, 183.0), (119.0, 350.0), (40.0, 420.0)]
    for ascoltatore in "AB":
        pan, vol, fc = resa.campi(posizioni, ascoltatore)
        for i, p in enumerate(posizioni):
            laterale, d, _lato = vista(p, ascoltatore)
            assert (pan[i], vol[i], fc[i]) == (laterale, volume(d), resa.taglio(d))
    # In ogni gruppo c'è uno e un solo candidato di oggi, e il suo materiale è quello della resa di prima.
    for dimensione in bs.DIMENSIONI:
        assert [c.spazio for c in dimensione.candidati].count(resa.OGGI) == 1
        materiale = _materiali(banco, dimensione.chiave)[bs.indice_di_oggi(dimensione)]
        for k, chiave in enumerate(dimensione.punti):
            azione = resa.azione(punti[chiave].momento.eventi)
            assert np.array_equal(materiale.rese[k].buffer, resa.componi(azione, "A").buffer)


def test_la_legge_del_volume():
    for d in (40.0, 60.0, 150.0, 406.0):
        assert resa.legge_del_volume(d, resa.OGGI) == volume(d)
    # Al vicino di riferimento tutte le leggi danno lo stesso guadagno; altrove l'esponente moltiplica i decibel.
    for esponente in (0.5, 1.5, 2.0):
        spazio = resa.Spazio(volume=esponente)
        assert resa.legge_del_volume(resa.D_RIF_VOLUME, spazio) == pytest.approx(volume(resa.D_RIF_VOLUME))
        assert bs.decibel_del_lontano(spazio) == pytest.approx(esponente * bs.decibel_del_lontano(resa.OGGI))
    assert bs.decibel_del_lontano(resa.OGGI) == pytest.approx(20.0 * math.log10(volume(406.0) / volume(60.0)))


def test_la_legge_del_taglio():
    oggi = resa.OGGI
    for d in (30.0, 100.0, 250.0, 406.0):
        assert resa.legge_del_taglio(d, 0.0, oggi) == resa.taglio(d)
        assert resa.legge_del_taglio(d, 300.0, resa.Spazio(cupezza="nessuna")) == resa.FC_MAX
    assert resa.legge_del_taglio(resa.D_FONDO, 366.0, oggi) == pytest.approx(resa.FC_FONDO)
    # L'ombra: aperta finché la pallina si vede sotto lo schermo, chiusa dove è piena, e in mezzo giù sulla scala delle ottave.
    ombra = resa.Spazio(cupezza="ombra", fc_ombra=3000.0)
    assert resa.legge_del_taglio(400.0, resa.Y_OMBRA, ombra) == resa.FC_MAX
    assert resa.legge_del_taglio(100.0, 183.0, ombra) == resa.FC_MAX
    assert resa.legge_del_taglio(400.0, resa.Y_OMBRA_PIENA, ombra) == pytest.approx(3000.0)
    assert resa.legge_del_taglio(400.0, 366.0, ombra) == pytest.approx(3000.0)
    mezzo = (resa.Y_OMBRA + resa.Y_OMBRA_PIENA) / 2
    assert resa.legge_del_taglio(400.0, mezzo, ombra) == pytest.approx(math.sqrt(3000.0 * resa.FC_MAX))
    # Per chi ascolta da B l'ombra sta nella metà di A.
    assert resa.campi([(61.0, 20.0)], "B", ombra)[2][0] == pytest.approx(3000.0)
    assert resa.campi([(61.0, 20.0)], "A", ombra)[2][0] == resa.FC_MAX


def test_la_legge_del_pan():
    # La metà lontana che si stringe: la metà vicina resta com'è, in fondo il pan è moltiplicato per lontano.
    stretta = resa.Spazio(lontano=0.4)
    for p in ((3.0, 20.0), (119.0, 183.0), (-50.0, 183.0)):
        assert resa.campi([p], "A", stretta)[0][0] == vista(p, "A")[0]
    assert resa.campi([(3.0, 366.0)], "A", stretta)[0][0] == pytest.approx(0.4 * vista((3.0, 366.0), "A")[0])
    meta_lontana = (183.0 + 366.0) / 2
    assert resa.campi([(119.0, meta_lontana)], "A", stretta)[0][0] == pytest.approx(0.7 * vista((119.0, meta_lontana), "A")[0])
    # Per chi ascolta da B si stringe la metà di A, con i lati ribaltati.
    assert resa.campi([(3.0, 0.0)], "B", stretta)[0][0] == pytest.approx(0.4 * vista((3.0, 0.0), "B")[0])
    assert resa.campi([(3.0, 0.0)], "B", stretta)[0][0] > 0
    # L'angolo vero: l'angolo lontano a 8,5 gradi dal centro, con le casse a 30.
    angolo = resa.Spazio(pan="angolo")
    assert round(bs.ANGOLO_LONTANO, 2) == 8.54
    assert resa.campi([(122.0, 366.0)], "A", angolo)[0][0] == pytest.approx(bs.ANGOLO_LONTANO / 30.0)
    assert resa.campi([(0.0, 0.0)], "A", angolo)[0][0] == -1.0
    assert resa.campi([(61.0, 300.0)], "A", angolo)[0][0] == 0.0
    # L'arbitro, che con la legge laterale è tutto in un orecchio, con l'angolo vero sta a 0,88.
    assert resa.campi([(-50.0, 183.0)], "A", angolo)[0][0] == pytest.approx(-0.88, abs=0.01)


def test_le_leggi_sconosciute_non_esistono():
    with pytest.raises(ValueError, match="cupezza"):
        resa.Spazio(cupezza="aria")
    with pytest.raises(ValueError, match="panorama"):
        resa.Spazio(pan="sferico")


def test_il_livello_e_comune_e_sotto_il_tetto():
    piano = np.full((100, 2), 0.2, dtype=np.float32)
    forte = np.full((100, 2), 0.5, dtype=np.float32)
    forte[3, 1] = 1.6
    abbassati = resa.con_margine_comune([piano, forte])
    assert max(float(np.max(np.abs(b))) for b in abbassati) <= resa.TETTO
    # Lo stesso fattore per tutti: il rapporto fra i due resta quello di prima.
    assert abbassati[1][50, 0] / abbassati[0][50, 0] == pytest.approx(2.5)
    assert abbassati[0][50, 0] == pytest.approx(0.2 * resa.TETTO / 1.6)
    assert np.array_equal(resa.con_margine_comune([piano])[0], resa.con_margine(piano))
    assert np.array_equal(resa.con_margine_comune([forte])[0], resa.con_margine(forte))


# I candidati.

def test_in_ogni_gruppo_cambia_soltanto_la_sua_dimensione():
    chiavi = [d.chiave for d in bs.DIMENSIONI]
    assert chiavi == ["volume", "cupezza", "larghezza"]
    for dimensione in bs.DIMENSIONI:
        assert 3 <= len(dimensione.candidati) <= 5
        assert len({c.spazio for c in dimensione.candidati}) == len(dimensione.candidati)
        assert len({c.nome for c in dimensione.candidati}) == len(dimensione.candidati)
        for candidato in dimensione.candidati:
            assert candidato.spazio.diverso_in(resa.OGGI) <= set(dimensione.campi), candidato.nome
        assert set(dimensione.punti) <= set(bs.TITOLI_DEI_PUNTI)
        assert 2 <= len(dimensione.punti) <= 3
    # I campi dei tre gruppi non si sovrappongono e insieme sono tutto lo spazio.
    campi = [c for d in bs.DIMENSIONI for c in d.campi]
    assert len(campi) == len(set(campi)) and set(campi) == set(bs.INSIEME.campi)


def test_il_volume_cambia_davvero_sui_buffer(banco):
    # Nel goal di battuta dell'avversario: la battuta lontana contro la pallina che rotola vicino a te, poco prima del goal.
    contrasti = []
    for materiale in _materiali(banco, "volume"):
        lontano, battuta = _finestra(materiale, 0, "battuta")
        vicino, _goal = _finestra(materiale, 0, "goal", durata=0.06, da=-0.08)
        assert vista(battuta.posizioni[0], "A")[1] > 350
        contrasti.append(_decibel(lontano) - _decibel(vicino))
    salti = [a - b for a, b in itertools.pairwise(contrasti)]
    # I candidati vanno dal lontano più forte al più piano, a passi di circa quattro decibel.
    assert all(3.5 < salto < 4.6 for salto in salti), salti
    attesi = [bs.decibel_del_lontano(c.spazio) for c in bs.VOLUME]
    assert attesi == sorted(attesi, reverse=True)
    assert [round(-a) for a in attesi] == [4, 8, 13, 17]


def test_la_cupezza_cambia_davvero_sui_buffer(banco):
    materiali = _materiali(banco, "cupezza")
    nessuna = materiali[0]
    misure = []
    for materiale in materiali:
        # Gli acuti persi, rispetto a nessuna cupezza: in fondo, alla battuta dell'avversario, e allo schermo centrale.
        fondo = _acuti(_finestra(materiale, 0, "battuta", durata=0.06)[0]) / _acuti(_finestra(nessuna, 0, "battuta", durata=0.06)[0])
        schermo = _acuti(_finestra(materiale, 1, "schermo", durata=0.06)[0]) / _acuti(_finestra(nessuna, 1, "schermo", durata=0.06)[0])
        misure.append((10.0 * math.log10(fondo), 10.0 * math.log10(schermo)))
    (nessuna_fondo, nessuna_schermo), (distanza_fondo, distanza_schermo), (lieve_fondo, lieve_schermo), (forte_fondo, forte_schermo) = misure
    assert nessuna_fondo == 0.0 and nessuna_schermo == 0.0
    # La distanza chiude anche allo schermo; l'ombra lo lascia aperto e chiude solo dietro.
    assert distanza_fondo < -10.0 and distanza_schermo < -5.0
    assert lieve_schermo == pytest.approx(0.0, abs=0.05) and forte_schermo == pytest.approx(0.0, abs=0.05)
    assert -10.0 < lieve_fondo < -3.0
    assert forte_fondo < -12.0
    # L'ombra forte e la distanza di oggi chiudono quasi uguale in fondo: differiscono nella forma.
    assert abs(forte_fondo - distanza_fondo) < 3.0
    # Ogni coppia di candidati si distingue di almeno tre decibel in uno dei due posti.
    for i in range(len(misure)):
        for j in range(i + 1, len(misure)):
            assert max(abs(misure[i][0] - misure[j][0]), abs(misure[i][1] - misure[j][1])) >= 3.0, (i, j, misure)


def test_la_larghezza_cambia_davvero_sui_buffer(banco):
    misure = []
    for candidato, materiale in zip(bs.LARGHEZZA, _materiali(banco, "larghezza"), strict=True):
        # Nel tuo goal nella porta lontana: la parata lontana dell'avversario, la tua sponda a metà tavolo e la tua parata vicina.
        lontano, parata_lontana = _finestra(materiale, 1, "parata", 0)
        meta, sponda = _finestra(materiale, 1, "sponda", 0)
        vicino, parata_vicina = _finestra(materiale, 1, "parata", 1)
        assert parata_lontana.posizioni[0][1] > 300 and 150 < sponda.posizioni[0][1] < 183 and parata_vicina.posizioni[0][1] < 50
        misura = (_pan(lontano), _pan(meta), _pan(vicino))
        attese = tuple(resa.campi([p.posizioni[0]], "A", candidato.spazio)[0][0] for p in (parata_lontana, sponda, parata_vicina))
        assert misura == pytest.approx(attese, abs=0.03), candidato.nome
        misure.append(misura)
    oggi, larga, stretta, angolo = misure
    # Le tre metà lontane laterali si stringono a passi ben distinti, con la metà vicina uguale.
    assert oggi[0] - larga[0] > 0.2 and larga[0] - stretta[0] > 0.2
    assert oggi[1:] == pytest.approx(larga[1:], abs=0.01) and oggi[1:] == pytest.approx(stretta[1:], abs=0.01)
    # L'angolo vero stringe anche a metà tavolo e allarga vicino a te.
    assert abs(angolo[1]) < abs(oggi[1]) - 0.3 and abs(angolo[2]) > abs(oggi[2])
    for i in range(len(misure)):
        for j in range(i + 1, len(misure)):
            assert max(abs(a - b) for a, b in zip(misure[i], misure[j], strict=True)) >= 0.1, (i, j, misure)


def test_i_materiali_sono_i_punti_in_fila(banco):
    punti, materiali, chiamate, cartella = banco
    assert chiamate == [] and list(cartella.iterdir()) == []
    pausa = round(bs.PAUSA_FRA_I_PUNTI * FS)
    for dimensione in bs.DIMENSIONI:
        lunghezze = set()
        for materiale in materiali[dimensione.chiave]:
            buffer = materiale.buffer
            assert buffer.dtype == np.float32 and buffer.ndim == 2 and buffer.shape[1] == 2
            assert float(np.max(np.abs(buffer))) <= resa.TETTO
            assert len(materiale.rese) == len(dimensione.punti) and materiale.inizi[0] == 0
            for k, composto in enumerate(materiale.rese):
                fine = materiale.inizi[k] + len(composto.buffer)
                # Ogni punto comincia col fischio del via, e fra un punto e l'altro c'è la pausa, muta.
                assert composto.posati[0].ruolo == "fischio_singolo"
                assert np.any(buffer[materiale.inizi[k]:materiale.inizi[k] + round(0.05 * FS)])
                if k + 1 < len(materiale.rese):
                    assert materiale.inizi[k + 1] == fine + pausa
                    assert not np.any(buffer[fine:fine + pausa])
                else:
                    assert len(buffer) == fine
            lunghezze.add(len(buffer))
        # Tutti i candidati hanno la stessa durata: cambiano solo le leggi dello spazio.
        assert len(lunghezze) == 1
    assert set(punti) == {chiave for d in (*bs.DIMENSIONI, bs.INSIEME) for chiave in d.punti}


# Il controllo e l'ordine.

def test_il_controllo_e_identico_campione_per_campione(banco, prove):
    punti = banco[0]
    for prova in prove:
        assert len(prova.lettere) == len(prova.dimensione.candidati) + 1
        coppia = prova.lettere_di(prova.ripetuto)
        assert len(coppia) == 2
        sentiti = {lettera: prova.da_sentire(lettera, 0.0) for lettera in prova.lettere}
        a, b = coppia
        assert np.array_equal(sentiti[a], sentiti[b])
        # Ogni altra coppia di lettere suona diversa.
        for i, x in enumerate(prova.lettere):
            for y in prova.lettere[i + 1:]:
                if {x, y} != {a, b}:
                    assert not np.array_equal(sentiti[x], sentiti[y]), (prova.dimensione.chiave, x, y)
        # E il candidato ripetuto, composto da capo, è lo stesso campione per campione.
        candidato = prova.dimensione.candidati[prova.ripetuto]
        da_capo = bs.componi_materiale([punti[k] for k in prova.dimensione.punti], candidato.spazio)
        assert np.array_equal(resa.con_margine(da_capo.buffer), sentiti[a])


def test_l_ordine_si_mescola_e_si_ripete_col_seme(banco):
    punti, materiali, _chiamate, _cartella = banco
    impronta = lambda prove: [(p.ordine, p.ripetuto) for p in prove]  # noqa: E731
    assert impronta(bs.prepara(SEME, punti, materiali)) == impronta(bs.prepara(SEME, punti, materiali))
    assert impronta(bs.prepara(SEME, punti, materiali)) != impronta(bs.prepara(SEME + 1, punti, materiali))
    # Su molti semi ogni candidato capita sotto ogni lettera e ciascuno fa il controllo.
    ordini = set()
    ripetuti = set()
    prime = set()
    for seme in range(200):
        ordine, ripetuto = bs.assegna(random.Random(seme), 4)
        assert sorted(ordine) == sorted([0, 1, 2, 3, ripetuto])
        ordini.add(ordine)
        ripetuti.add(ripetuto)
        prime.add(ordine[0])
    assert len(ordini) > 50 and ripetuti == {0, 1, 2, 3} and prime == {0, 1, 2, 3}


def test_la_scelta_di_un_gruppo(prove):
    prova = prove[0]
    oggi = bs.indice_di_oggi(prova.dimensione)
    assert bs.scelta(prova) == oggi
    lettere = {i: prova.lettere_di(i) for i in range(len(prova.dimensione.candidati))}
    # Il più votato vince; a parità vince quello di oggi; fra pari che non sono oggi, il primo.
    altro = next(i for i in lettere if i != oggi)
    for lettera in prova.lettere:
        prova.voti[lettera] = 2
    for lettera in lettere[altro]:
        prova.voti[lettera] = 5
    assert bs.scelta(prova) == altro
    for lettera in lettere[oggi]:
        prova.voti[lettera] = 5
    assert bs.scelta(prova) == oggi
    for lettera in prova.lettere:
        prova.voti[lettera] = 4 if prova.indice(lettera) in (2, 3) else 1
    assert bs.scelta(prova) == 2
    # Il candidato ripetuto conta con la media delle sue due lettere.
    prova.voti.clear()
    a, b = prova.lettere_di(prova.ripetuto)
    prova.voti.update({a: 5, b: 1})
    unico = next(i for i in lettere if i != prova.ripetuto)
    prova.voti[lettere[unico][0]] = 4
    assert bs.medie(prova)[prova.ripetuto] == 3.0 and bs.scelta(prova) == unico
    prova.nessuna_preferenza = True
    assert bs.scelta(prova) == oggi


def test_le_scelte_messe_insieme(banco, prove):
    punti = banco[0]
    assert bs.spazio_delle_scelte(prove) == resa.OGGI
    assert bs.prepara_finale(prove, SEME, punti) is None
    volume, cupezza, larghezza = prove
    piu_piano = bs.VOLUME.index(next(c for c in bs.VOLUME if c.spazio.volume == 2.0))
    ombra = 3
    for prova, preferito in ((volume, piu_piano), (cupezza, ombra)):
        for lettera in prova.lettere:
            prova.voti[lettera] = 5 if prova.indice(lettera) == preferito else 2
    larghezza.nessuna_preferenza = True
    scelte = bs.spazio_delle_scelte(prove)
    assert scelte == resa.Spazio(volume=2.0, cupezza="ombra", fc_ombra=resa.FC_FONDO)
    finale = bs.prepara_finale(prove, SEME, punti)
    assert [c.spazio for c in finale.dimensione.candidati] == [resa.OGGI, scelte]
    assert finale.dimensione.punti == bs.INSIEME.punti and len(finale.lettere) == 3
    assert bs.CUPEZZA[ombra].nome in finale.dimensione.candidati[1].nome
    # Il gruppo finale ha anche lui il suo controllo, identico, e lettere che si ripetono col seme.
    a, b = finale.lettere_di(finale.ripetuto)
    assert np.array_equal(finale.da_sentire(a, 0.0), finale.da_sentire(b, 0.0))
    altra = next(x for x in finale.lettere if x not in (a, b))
    assert not np.array_equal(finale.da_sentire(a, 0.0), finale.da_sentire(altra, 0.0))
    assert bs.prepara_finale(prove, SEME, punti).ordine == finale.ordine


# I tasti.

def test_la_rassegna_fa_sentire_ogni_lettera_in_ordine(prove, cassa, monkeypatch, capsys):
    prova = prove[0]
    _tastiera(monkeypatch, cassa, [])
    bs.rassegna(prova)
    assert len(cassa.suonati) == len(prova.lettere) and cassa.fermate == 0
    anticipo = round(bs.ANTICIPO_RASSEGNA * FS)
    for lettera, buffer in zip(prova.lettere, cassa.suonati, strict=True):
        assert not np.any(buffer[:anticipo])
        assert np.array_equal(buffer[anticipo:], prova.materiali[prova.indice(lettera)].buffer)
    scritto = capsys.readouterr().out
    assert scritto.splitlines() == ["Rassegna."] + [f"Lettera {lettera}." for lettera in prova.lettere]
    # Escape mentre suona la seconda lettera interrompe la rassegna; gli altri tasti no.
    cassa.suonati.clear()
    _tastiera(monkeypatch, cassa, [("durante", 1, " "), ("durante", 1, "1"), ("durante", 2, "\x1b")])
    bs.rassegna(prova)
    assert len(cassa.suonati) == 2 and cassa.fermate == 1
    assert capsys.readouterr().out.splitlines()[-1] == "Rassegna interrotta."


def test_i_tasti_del_voto(prove, cassa, monkeypatch, capsys):
    prova = prove[1]
    a, b, c, d, e = prova.lettere
    # A: spazio la fa sentire, poi la lettera d la fa sentire per confronto, poi il 4. B: Invio passa
    # senza voto. C: spazio, e il 2 premuto mentre suona vale subito. D: un tasto sconosciuto non fa
    # niente, poi la lettera a, minuscola o maiuscola, e mentre suona Escape chiude il voto.
    copione = [" ", d.lower(), "4", "\r", " ", ("durante", 3, "2"), "x", "up", a, ("durante", 4, "\x1b")]
    tastiera = _tastiera(monkeypatch, cassa, copione)
    bs.voto(prova)
    assert tastiera.copione == []
    assert prova.voti == {a: 4, c: 2}
    sentiti = [a, d, c, a]
    assert len(cassa.suonati) == len(sentiti) and cassa.fermate == 2
    for lettera, buffer in zip(sentiti, cassa.suonati, strict=True):
        assert np.array_equal(buffer, prova.da_sentire(lettera, bs.ANTICIPO_VOTO))
    scritto = capsys.readouterr().out
    assert f"\r{a}: spazio ascolta, da 1 a 5 il voto\r" in scritto
    assert scritto.rstrip().endswith(f"I voti: {a} 4, {b} senza voto, {c} 2, {d} senza voto, {e} senza voto.")
    assert "\n\n" not in scritto
    # Il secondo giro mostra il voto già dato, e Invio lo lascia com'è; n cancella tutto.
    _tastiera(monkeypatch, cassa, ["\r", "n"])
    bs.voto(prova)
    assert f"\r{a}, voto 4: spazio ascolta, 1-5 cambia\r" in capsys.readouterr().out
    assert prova.nessuna_preferenza and prova.voti == {}
    _tastiera(monkeypatch, cassa, ["3", "\x1b"])
    bs.voto(prova)
    assert not prova.nessuna_preferenza and prova.voti == {a: 3}


def test_i_prompt_stanno_in_quaranta_caratteri():
    for lettera in bs.LETTERE:
        assert len(bs.invito(lettera, None).strip("\r")) <= 40
        assert len(bs.invito(lettera, 5).strip("\r")) <= 40
        assert bs.invito(lettera, None).startswith("\r") and bs.invito(lettera, None).endswith("\r")


def test_una_scheda_che_non_risponde_non_ferma_il_banco(prove, monkeypatch, capsys):
    muta = Cassa(riesce=False)
    monkeypatch.setattr(bs, "Acusticator", muta)
    _tastiera(monkeypatch, muta, [])
    bs.rassegna(prove[2])
    assert "la scheda audio non risponde" in capsys.readouterr().out


# La sessione.

def _voti_del_volume(prova):
    """I voti del copione per il gruppo del volume: 5 al lontano più piano, agli altri il loro indice più uno."""
    piu_piano = next(i for i, c in enumerate(bs.VOLUME) if c.spazio.volume == 2.0)
    return {lettera: 5 if prova.indice(lettera) == piu_piano else prova.indice(lettera) + 1 for lettera in prova.lettere}


def test_la_sessione_intera(banco, prove, cassa, cartella_di_prova, suonati, monkeypatch, capsys):
    punti = banco[0]
    volume, cupezza, larghezza = prove
    monkeypatch.setattr(bs, "punti_del_banco", lambda: punti)
    monkeypatch.setattr(bs, "prepara", lambda seme, _punti: prove if seme == SEME else pytest.fail(f"seme {seme}"))
    monkeypatch.setattr(bs, "enter_escape", _enter_escape_finta([True]))
    monkeypatch.setattr(bs.time, "sleep", lambda _secondi: None)
    # Il volume si ascolta e si commenta, il colore si salta, la larghezza si interrompe, si vota
    # nessuna preferenza e poi si rifà con r, e il gruppo finale si vota a metà.
    monkeypatch.setattr(collaudo_comune, "enter_escape", _enter_escape_finta([True, False, True, True]))
    monkeypatch.setattr(collaudo_comune, "dgt", lambda *_a, **_k: "una lettera mi sembra troppo piana ")
    voti_volume = _voti_del_volume(volume)
    a, b, c, d, e = volume.lettere
    copione = [" ", b.lower(), str(voti_volume[a]), str(voti_volume[b]), " ", ("durante", 8, str(voti_volume[c])), str(voti_volume[d]), str(voti_volume[e])]
    copione += ["c", "\r"]
    voti_larghezza = dict(zip(larghezza.lettere, (3, 3, 4, 2, 5), strict=True))
    copione += [("durante", 10, "\x1b"), "n", "r"] + [str(voti_larghezza[x]) for x in larghezza.lettere] + ["\x1b"]
    copione += ["4", "\x1b", "\r"]
    tastiera = _tastiera(monkeypatch, cassa, copione)
    assert bs.main([str(SEME)]) == 0
    assert tastiera.copione == []
    assert suonati == []
    # Le lettere suonate: il volume 5 della rassegna e 3 del voto, la larghezza 2 interrotte e 5 col
    # secondo giro, il gruppo finale 3; le fermate sono il voto dato mentre suonava e l'Escape.
    assert len(cassa.suonati) == 8 + 7 + 3 and cassa.fermate == 2
    coppia = volume.lettere_di(volume.ripetuto)
    rassegna = dict(zip(volume.lettere, cassa.suonati[:5], strict=True))
    assert np.array_equal(rassegna[coppia[0]], rassegna[coppia[1]])
    assert np.array_equal(cassa.suonati[6], volume.da_sentire(b, bs.ANTICIPO_VOTO))
    assert volume.voti == voti_volume and larghezza.voti == voti_larghezza and not larghezza.nessuna_preferenza
    assert cupezza.saltata and not cupezza.svolta and cupezza.voti == {}

    righe = (cartella_di_prova / bs.FILE_DEI_RISULTATI).read_text(encoding="utf-8").splitlines()
    assert righe[0].startswith("Banco dello spazio, ") and righe[0].endswith(f", seme {SEME}.")
    titolo_v, titolo_c, titolo_l, titolo_f = volume.dimensione.titolo, cupezza.dimensione.titolo, larghezza.dimensione.titolo, bs.INSIEME.titolo
    voti_finale = ["4", "senza voto", "senza voto"]
    attese = ([f"{titolo_v}, lettera {x}: {voti_volume[x]}." for x in volume.lettere]
              + [f"{titolo_c}: gruppo saltato."]
              + [f"{titolo_l}, lettera {x}: {voti_larghezza[x]}." for x in larghezza.lettere]
              + [f"{titolo_f}, lettera {x}: {v}." for x, v in zip("ABC", voti_finale, strict=True)])
    prima_rivelazione = next(i for i, r in enumerate(righe) if " era: " in r)
    voci = [r for r in righe[1:prima_rivelazione] if ", lettera " in r or r.endswith("gruppo saltato.")]
    assert voci == attese
    # I commenti e gli esiti vengono subito dopo i voti del loro gruppo.
    i_commento = righe.index(next(r for r in righe if r.endswith(": una lettera mi sembra troppo piana")))
    assert righe[i_commento].startswith(f"{titolo_v}, ") and righe[i_commento - 1] == f"{titolo_v}, lettera {e}: {voti_volume[e]}."
    i_chiuso = righe.index(next(r for r in righe if r.endswith(": chiuso senza giudizio")))
    assert righe[i_chiuso].startswith(f"{titolo_l}, ") and righe[i_chiuso - 1] == f"{titolo_l}, lettera {larghezza.lettere[-1]}: {voti_larghezza[larghezza.lettere[-1]]}."
    i_superato = righe.index(next(r for r in righe if r.endswith(": test superato, nessun commento")))
    assert righe[i_superato].startswith(f"{titolo_f}, ")
    # Le lettere si svelano solo alla fine, dopo tutti i voti e gli esiti.
    nomi = [cand.nome for dim in bs.DIMENSIONI for cand in dim.candidati]
    assert prima_rivelazione > max(i_commento, i_chiuso, i_superato, *(righe.index(v) for v in attese))
    assert not any(nome in riga for riga in righe[:prima_rivelazione] for nome in nomi)
    rivelate = righe[prima_rivelazione:]
    for prova in (volume, larghezza):
        titolo = prova.dimensione.titolo
        for x in prova.lettere:
            assert any(r.startswith(f"{titolo}, la lettera {x} era: {prova.candidato(x).nome}") for r in rivelate)
        x, y = prova.lettere_di(prova.ripetuto)
        assert f"{titolo}, la lettera {x} era: {prova.candidato(x).nome}; è la versione ripetuta per controllo, identica alla lettera {y}." in rivelate
        assert f"Controllo, {titolo}: le lettere {x} e {y}, identiche campione per campione, hanno avuto {x} {prova.voti[x]} e {y} {prova.voti[y]}." in rivelate
        # Il riepilogo somma i voti per candidato, dal più votato.
        riepilogo = [r for r in rivelate if r.startswith(f"Riepilogo, {titolo}, ")]
        assert len(riepilogo) == len(prova.dimensione.candidati)
        medie = bs.medie(prova)
        for indice, candidato in enumerate(prova.dimensione.candidati):
            voti = [prova.voti[x] for x in prova.lettere_di(indice)]
            riga = next(r for r in riepilogo if r.startswith(f"Riepilogo, {titolo}, {candidato.nome}: "))
            assert f": totale {sum(voti)} con {len(voti)} vot" in riga
        assert riepilogo[0].startswith(f"Riepilogo, {titolo}, {prova.dimensione.candidati[max(medie, key=medie.get)].nome}: ")
        assert f"Scelta, {titolo}: {prova.dimensione.candidati[bs.scelta(prova)].nome}." in rivelate
    assert not any(r.startswith(f"{titolo_c}, la lettera") for r in rivelate)
    # Il gruppo finale: lo spazio di oggi contro le scelte, e la scelta del volume è il lontano più piano.
    assert bs.scelta(volume) == next(i for i, cand in enumerate(bs.VOLUME) if cand.spazio.volume == 2.0)
    assert sum(1 for r in rivelate if r.startswith(f"{titolo_f}, la lettera")) == 3
    assert any(r.startswith(f"Riepilogo, {titolo_f}, lo spazio di oggi") for r in rivelate)
    assert any(r.startswith(f"Riepilogo, {titolo_f}, le scelte dei tre gruppi: ") and bs.VOLUME[-1].nome in r for r in rivelate)
    assert not any(r.startswith(f"Scelta, {titolo_f}") for r in rivelate)
    assert all(r.strip() and not r.startswith(("-", "=", "_")) for r in righe)

    scritto = capsys.readouterr().out
    assert scritto.startswith("Banco dello spazio della partita di MESS: 3 gruppi, ")
    assert scritto.rstrip().endswith("trovi i voti, quale lettera era quale e il riepilogo.")
    # A schermo non si dice mai quale lettera era quale, né che c'è un controllo, né un numero delle leggi.
    for vietata in (*nomi, "controllo", "ripetut", "decibel", "hertz", "per cento", "oggi"):
        assert vietata not in scritto, vietata
    # Le sole righe vuote sono quelle che il menu di collaudo_comune lascia dopo i suoi messaggi.
    linee = scritto.split("\n")
    vuote = [i for i, riga in enumerate(linee[:-1]) if riga == ""]
    assert vuote and all(linee[i - 1] in MESSAGGI_DEL_MENU for i in vuote), [linee[i - 1] for i in vuote]


def test_la_rivelazione_senza_preferenze_e_senza_voti(prove):
    volume, cupezza, larghezza = prove
    for prova in prove:
        prova.svolta = True
    cupezza.nessuna_preferenza = True
    larghezza.voti[larghezza.lettere[0]] = 4
    righe = bs.righe_della_rivelazione(prove)
    assert bs.righe_dei_voti(cupezza) == [f"{cupezza.dimensione.titolo}: nessuna preferenza."]
    for prova in prove:
        titolo = prova.dimensione.titolo
        x, y = prova.lettere_di(prova.ripetuto)
        assert sum(1 for r in righe if r.startswith(f"{titolo}, la lettera ")) == len(prova.lettere)
        oggi = prova.dimensione.candidati[bs.indice_di_oggi(prova.dimensione)].nome
        if prova is cupezza:
            assert f"Riepilogo, {titolo}: nessuna preferenza fra le lettere." in righe
            assert f"Controllo, {titolo}: le lettere {x} e {y} erano identiche campione per campione, e non hai dato preferenze." in righe
            assert f"Scelta, {titolo}: senza voti resta {oggi}." in righe
        elif prova is volume:
            assert f"Controllo, {titolo}: le lettere {x} e {y}, identiche campione per campione, hanno avuto {x} senza voto e {y} senza voto." in righe
            riepilogo = [r for r in righe if r.startswith(f"Riepilogo, {titolo}, ")]
            assert len(riepilogo) == len(prova.dimensione.candidati) and all(": nessun voto, letter" in r for r in riepilogo)
            assert f"Scelta, {titolo}: senza voti resta {oggi}." in righe
        else:
            premiato = prova.candidato(prova.lettere[0]).nome
            assert next(r for r in righe if r.startswith(f"Riepilogo, {titolo}, ")).startswith(f"Riepilogo, {titolo}, {premiato}: totale 4 con 1 voto, media 4,0, ")
            assert f"Scelta, {titolo}: {premiato}." in righe


def test_senza_il_via_non_suona_niente(banco, prove, cassa, cartella_di_prova, monkeypatch, capsys):
    monkeypatch.setattr(bs, "punti_del_banco", lambda: banco[0])
    monkeypatch.setattr(bs, "prepara", lambda _seme, _punti: prove)
    monkeypatch.setattr(bs, "enter_escape", _enter_escape_finta([False]))
    assert bs.main([]) == 0
    assert cassa.suonati == []
    assert not (cartella_di_prova / bs.FILE_DEI_RISULTATI).exists()
    assert "\n\n" not in capsys.readouterr().out


def test_un_seme_che_non_e_un_numero(cassa, cartella_di_prova, capsys):
    assert bs.main(["quattro"]) == 1
    assert cassa.suonati == []
    assert not (cartella_di_prova / bs.FILE_DEI_RISULTATI).exists()
    assert "Il seme dev'essere un numero intero" in capsys.readouterr().out


def test_tutto_saltato_e_il_gruppo_finale_non_serve(banco, prove, cassa, cartella_di_prova, monkeypatch, capsys):
    monkeypatch.setattr(bs, "punti_del_banco", lambda: banco[0])
    monkeypatch.setattr(bs, "prepara", functools.partial(lambda prove, _seme, _punti: prove, prove))
    monkeypatch.setattr(bs, "enter_escape", _enter_escape_finta([True]))
    monkeypatch.setattr(bs.time, "sleep", lambda _secondi: None)
    monkeypatch.setattr(collaudo_comune, "enter_escape", _enter_escape_finta([False, False, False]))
    _tastiera(monkeypatch, cassa, [])
    assert bs.main([]) == 0
    assert cassa.suonati == []
    righe = (cartella_di_prova / bs.FILE_DEI_RISULTATI).read_text(encoding="utf-8").splitlines()
    assert righe[1:] == [f"{p.dimensione.titolo}: gruppo saltato." for p in prove] + [
        f"{bs.INSIEME.titolo}: il gruppo non è servito, perché le scelte dei tre gruppi sono proprio lo spazio di oggi."]
    assert "Il gruppo finale non serve." in capsys.readouterr().out
