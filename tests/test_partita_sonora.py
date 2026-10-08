"""
Test della partita sonora della tappa 10, partita_sonora.py, senza mai suonare: la cassa vera di
Acusticator fa fallire chi la chiama, e la riproduzione usa una cassa finta e un orologio finto.
Lo spazio: i valori del prototipo come predefiniti, il lato giusto per A e per B, le leggi che si
sostituiscono. La composizione: ogni suono al suo campione, il silenzio in testa accorciato, il volo
che attraversa il tavolo, il suono scelto da tipo, esito e causa, il margine anche al volume massimo,
con lo stesso fattore per ogni buffer, e la paletta che suona nel riscaldamento. La riproduzione: la
coda di zeri, la posizione, la pausa con la maniglia, le code che finiscono, la rampa di chi riparte a
metà. La cronologia: i segmenti fino a ogni punto, sanzione o fine set, che coprono tutto l'incontro;
la velocità di gioco che accorcia pause e procedura e lascia l'azione a tempo reale, con gli stessi
punti; i tratti di procedura di ogni segmento e le pieghe che li fanno durare quanto vuole la velocità.
Dalla decisione D30: il volume della partita, che cresce fino a 100 e al predefinito suona come
l'ascolto libero, e le pause lunghe di ogni segmento, che il buffer salta, con la pausa di sempre
che resta prima.
"""

import itertools
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from aiuti_dal_vivo import CassaFinta, Orologio, vieta_la_cassa_vera
from aiuti_motore import giocatore

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))

import resa_prototipo as resa

import impostazioni
import partita_sonora as ps
from motore import COMPLETO, SINGOLARE_3, Incontro
from motore import eventi as E
from motore.eventi import Evento
from motore.tavolo import traiettoria, vista, volume

FS = ps.FS


@pytest.fixture(autouse=True)
def cassa_vera_muta(monkeypatch):
    vieta_la_cassa_vera(monkeypatch)


def _evento(n, t, tipo, pos=None, **campi):
    return Evento(n=n, t=t, tipo=tipo, fase=E.GIOCO, pos=pos, **campi)


def _energia(stereo):
    return float(np.sum(stereo[:, 0] ** 2)), float(np.sum(stereo[:, 1] ** 2))


# Lo spazio.

def test_lo_spazio_predefinito_e_quello_del_prototipo():
    spazio = ps.Spazio()
    for pos in ((10.0, 20.0), (61.0, 183.0), (110.0, 340.0), (-40.0, 183.0)):
        for ascoltatore in ("A", "B"):
            pan, vol, taglio = spazio.punto(pos, ascoltatore)
            pan_motore, distanza, _lato = vista(pos, ascoltatore)
            assert pan == pytest.approx(pan_motore)
            assert vol == pytest.approx(volume(distanza))
            assert taglio == pytest.approx(min(18000.0, max(1500.0, 18000.0 * 60.0 / max(distanza, 60.0))))


def test_la_sinistra_di_a_e_la_destra_di_b():
    spazio = ps.SPAZIO
    pan_a, vol_a, taglio_a = spazio.punto((15.0, 30.0), "A")
    pan_b, vol_b, taglio_b = spazio.punto((15.0, 30.0), "B")
    assert pan_a < -0.5 and pan_b > 0.5
    # Vicino ad A: per A è forte e chiaro, per B, all'altra testata, piano e cupo.
    assert vol_a > 2 * vol_b and taglio_a > taglio_b


def test_le_leggi_dello_spazio_si_sostituiscono():
    ombra = ps.Spazio(cupo_solo_dietro_lo_schermo=True)
    assert ombra.punto((61.0, 150.0), "A")[2] == ombra.taglio_massimo
    assert ombra.punto((61.0, 300.0), "A")[2] < ombra.taglio_massimo
    stretta = ps.Spazio(larghezza_lontana=0.5)
    assert stretta.punto((10.0, 366.0), "A")[0] == pytest.approx(0.5 * ps.SPAZIO.punto((10.0, 366.0), "A")[0])
    assert stretta.punto((10.0, 100.0), "A")[0] == pytest.approx(ps.SPAZIO.punto((10.0, 100.0), "A")[0])
    # Per B la metà lontana è quella di A.
    assert stretta.punto((10.0, 0.0), "B")[0] == pytest.approx(0.5 * ps.SPAZIO.punto((10.0, 0.0), "B")[0])
    piano = ps.Spazio(volume_riferimento=75.0)
    assert piano.punto((61.0, 300.0), "A")[1] < ps.SPAZIO.punto((61.0, 300.0), "A")[1]


# La composizione.

def test_ogni_suono_cade_al_suo_campione():
    battuta = _evento(1, 10.0, E.BATTUTA, (40.0, 25.0), chi=1, parte="A")
    parata = _evento(2, 10.537, E.PARATA, (80.0, 340.0), chi=2, parte="B")
    resa = ps.componi([battuta, parata], "A", da=9.9)
    assert resa.t0 == 9.9
    atteso = np.zeros_like(resa.buffer)
    for posato in resa.posati:
        stereo = ps.spazializza(posato, "A")
        inizio = round((posato.t - 9.9) * FS)
        atteso[inizio:inizio + len(stereo)] += stereo
    assert np.array_equal(resa.buffer, atteso)
    assert [round((p.t - resa.t0) * FS) for p in resa.posati] == [round(0.1 * FS), round(0.637 * FS)]
    # Il primo campione che suona è quello della battuta, esatto.
    sola = ps.componi([battuta], "A", da=9.5)
    sorgente = ps.sorgente("battuta")
    primo = int(np.flatnonzero(sorgente)[0])
    assert int(np.flatnonzero(np.abs(sola.buffer[:, 0]) > 0)[0]) == round(0.5 * FS) + primo


def test_il_silenzio_in_testa_si_accorcia_e_la_fine_si_allunga():
    battuta = _evento(1, 10.0, E.BATTUTA, (40.0, 25.0), chi=1, parte="A")
    annuncio = _evento(2, 6.0, E.ANNUNCIO, (-40.0, 183.0), durata=1.6)
    resa = ps.componi([annuncio, battuta], "A", da=5.0, fine=14.0, anticipo=ps.ANTICIPO)
    assert resa.t0 == pytest.approx(10.0 - ps.ANTICIPO)
    assert resa.durata >= 14.0 - resa.t0
    # Senza anticipo il buffer comincia da da, e gli eventi di prima non suonano.
    intera = ps.componi([annuncio, battuta], "A", da=5.0)
    assert intera.t0 == 5.0
    assert ps.componi([battuta], "A", da=10.5).posati == []


def test_il_lato_e_la_distanza_per_a_e_per_b():
    battuta = _evento(1, 3.0, E.BATTUTA, (15.0, 30.0), chi=1, parte="A")
    per_a = ps.componi([battuta], "A").buffer
    per_b = ps.componi([battuta], "B").buffer
    sinistra_a, destra_a = _energia(per_a)
    sinistra_b, destra_b = _energia(per_b)
    assert sinistra_a > 4 * destra_a and destra_b > 4 * sinistra_b
    assert sinistra_a + destra_a > 4 * (sinistra_b + destra_b)


def test_la_diagonale_attraversa_il_tavolo():
    volo = traiettoria((110.0, 340.0), (15.0, 30.0), (), 420.0, 20.0, 40.0, 0.12, "paletta")
    evento = _evento(5, 20.0, E.VOLO, (15.0, 30.0), durata=volo[-1].t - volo[0].t, volo=volo, chi=2, parte="B")
    for ascoltatore, lato_iniziale in (("A", 1), ("B", 0)):
        resa = ps.componi([evento], ascoltatore)
        rotolamento = next(p for p in resa.posati if p.ruolo == "rotolamento")
        stereo = ps.spazializza(rotolamento, ascoltatore)
        quinto = len(stereo) // 5
        prima, ultima = _energia(stereo[:quinto]), _energia(stereo[-quinto:])
        # Per A la pallina parte da destra e arriva a sinistra, per B il contrario.
        assert prima[lato_iniziale] > 3 * prima[1 - lato_iniziale]
        assert ultima[1 - lato_iniziale] > 3 * ultima[lato_iniziale]


def test_il_suono_si_sceglie_da_tipo_esito_e_causa():
    fallo, fanfara = ps.ritardo_dell_esito("fallo"), ps.ritardo_dell_esito("fanfara")
    assert ps.suoni_fermi(_evento(1, 0.0, E.BATTUTA, causa="battuta_a_vuoto")) == [("colpo_a_vuoto", 0.0)]
    assert ps.suoni_fermi(_evento(1, 0.0, E.BATTUTA, causa="battuta_doppio_tocco")) == [("battuta", 0.0), ("secondo_tocco", ps.RITARDO_SECONDO_TOCCO)]
    assert ps.suoni_fermi(_evento(1, 0.0, E.COLPO, causa="paletta_caduta")) == []
    # Ogni fallo ha il suo cicalino dopo il fischio, che si aggiunge al suono della pallina senza toglierlo.
    assert ps.suoni_fermi(_evento(1, 0.0, E.FALLO, causa="paletta_caduta")) == [("paletta_caduta", 0.0), ("fallo", fallo)]
    assert ps.suoni_fermi(_evento(1, 0.0, E.FALLO, causa="out_sponda")) == [("fallo", fallo)]
    assert ps.suoni_fermi(_evento(1, 0.0, E.GOAL, causa="goal_scambio")) == [("goal", 0.0), ("fanfara", fanfara)]
    assert ps.suoni_fermi(_evento(1, 0.0, E.PALLA_MORTA, causa="colpo_debole")) == []
    assert ps.suoni_fermi(_evento(1, 0.0, E.PARATA, causa="body_touch")) == []
    assert ps.suoni_fermi(_evento(1, 0.0, E.PARATA, esito="goal")) == []
    assert ps.suoni_fermi(_evento(1, 0.0, E.PARATA, esito="ferma")) == [("parata", 0.0)]
    assert ps.suoni_fermi(_evento(1, 0.0, E.CHIAMATA)) == []


def test_due_rumori_di_fila_non_sono_uguali():
    parate = [_evento(n, 1.0 + n, E.PARATA, (61.0, 30.0), esito="ferma", chi=1, parte="A") for n in range(1, 4)]
    posati = ps.posa(parate)
    assert [p.variante for p in posati] == [0, 1, 2]
    assert not np.array_equal(posati[0].mono, posati[1].mono)


@pytest.mark.parametrize("volume_partita", [0, 25, 50, 95, 100])
def test_il_margine_tiene_anche_al_volume_massimo(volume_partita):
    battute = [_evento(n, 0.2 * n, E.BATTUTA, (61.0, 25.0), chi=1, parte="A") for n in range(1, 6)]
    buffer = ps.componi(battute, "A").buffer * 1.5
    pronto = ps.per_la_cassa(buffer, volume_partita)
    assert float(np.max(np.abs(pronto))) <= ps.TETTO
    if volume_partita == 0:
        assert not np.any(pronto)
    if volume_partita == 25:
        fattore = ps.fattore_del_volume(25)
        assert np.allclose(pronto, buffer * fattore, atol=1e-6) or float(np.max(np.abs(pronto))) == pytest.approx(ps.TETTO, abs=1e-6)


def test_le_sorgenti_si_preparano_tutte():
    ps.svuota_cache()
    ps.prepara()
    ruoli = {chiave[0] for chiave in ps._CACHE}
    assert ruoli == set(ps.SUONI.values())


# I timbri veri, la fase dei timbri di D28: i preset della collezione, il fischietto col suo trillo,
# i suoni dell'esito dopo il fischio, il sonaglio del rotolamento e i livelli delle sorgenti.

def test_ogni_ruolo_ha_il_suo_timbro_nella_collezione():
    from GBUtils import Acusticator

    assert set(ps.AZIONI) == set(ps.SUONI) and set(ps.ESITI) <= set(ps.SUONI)
    for ruolo, preset in ps.SUONI.items():
        score, kind, _adsr = Acusticator.preset(preset)
        assert score, f"il preset {preset} del ruolo {ruolo} non c'è nella collezione"
        assert preset.startswith("mess_partita_") and kind != 2, preset
        assert Acusticator.descrizione(preset).startswith("MESS, partita dal vivo, "), preset
        # Nessun volume a portamento scritto come testo: Acusticator e Acu_Maker non lo leggono allo stesso modo.
        assert all(not isinstance(score[i], str) for i in range(3, len(score), 4)), preset
        azione = ps.AZIONI[ruolo]
        assert azione.strip() == azione and azione[-1] not in ".:" and not any(s in azione for s in ("--", "==", "__"))


def _trillo(mono):
    """
    L'altezza del fischio ciclo per ciclo, dai passaggi per lo zero in salita: gli istanti e le
    frequenze, mediate su tre cicli d'onda, e quante volte l'altezza sale e scende attorno al centro.
    """
    su = np.flatnonzero((mono[:-1] < 0) & (mono[1:] >= 0))
    esatti = su + mono[su] / (mono[su] - mono[su + 1])
    frequenze = np.convolve(FS / np.diff(esatti), np.ones(3) / 3, mode="valid")
    istanti = esatti[2:len(esatti) - 1] / FS
    scarto = frequenze - np.median(frequenze)
    return istanti, frequenze, int(np.sum((scarto[:-1] < 0) & (scarto[1:] >= 0)))


def _soffi(mono, soglia=0.02):
    """I tratti in cui il fischio suona, come coppie di secondi d'inizio e di fine, separati da silenzi di almeno 20 ms."""
    acceso = np.convolve(np.abs(mono) > soglia * float(np.max(np.abs(mono))), np.ones(round(0.002 * FS)), mode="same") > 0
    cambi = np.flatnonzero(np.diff(acceso.astype(int)))
    bordi = [0, *(cambi + 1), len(mono)] if acceso[0] else [*(cambi + 1), len(mono)]
    tratti = [(bordi[i] / FS, bordi[i + 1] / FS) for i in range(0, len(bordi) - 1, 2)]
    uniti = [tratti[0]]
    for inizio, fine in tratti[1:]:
        if inizio - uniti[-1][1] < 0.02:
            uniti[-1] = (uniti[-1][0], fine)
        else:
            uniti.append((inizio, fine))
    return uniti


def test_il_fischio_e_il_fischietto_vero_col_suo_trillo():
    # Richiesta di Gabriele: un trillo rapidissimo, con l'altezza che sale e scende a sinusoide una
    # decina di volte, con poca ampiezza, come la pallina dentro il fischietto. Si misura sul buffer.
    singolo = ps.sorgente("fischio_singolo").astype(np.float64)
    istanti, frequenze, oscillazioni = _trillo(singolo)
    durata = len(singolo) / FS
    centro = float(np.median(frequenze))
    assert 9 <= oscillazioni <= 11 and durata < 0.4
    assert 2000 < centro < 4000
    # Poca ampiezza: l'altezza resta entro un semitono dal centro, ma il trillo si sente, almeno l'uno per cento.
    escursione = (np.percentile(frequenze, 95) - np.percentile(frequenze, 5)) / 2 / centro
    assert 0.01 < escursione < 0.06
    # Rapidissimo, e a sinusoide: una sinusoide alla frequenza del trillo spiega quasi tutto il movimento dell'altezza.
    ritmo = oscillazioni / (istanti[-1] - istanti[0])
    assert ritmo > 20

    def spiegato(r):
        base = np.column_stack([np.sin(2 * np.pi * r * istanti), np.cos(2 * np.pi * r * istanti), np.ones(len(istanti))])
        residuo = frequenze - base @ np.linalg.lstsq(base, frequenze, rcond=None)[0]
        return 1 - np.var(residuo) / np.var(frequenze)

    # Il ritmo contato dai passaggi è approssimato: si cerca quello vero poco attorno.
    assert max(spiegato(r) for r in np.linspace(0.85 * ritmo, 1.15 * ritmo, 61)) > 0.8
    # Il doppio, per il goal: due soffi dello stesso fischietto, con una pausa breve fra i due.
    doppio = ps.sorgente("fischio_doppio").astype(np.float64)
    soffi = _soffi(doppio)
    assert len(soffi) == 2 and 0.04 <= soffi[1][0] - soffi[0][1] <= 0.12
    for inizio, fine in soffi:
        _i, f, oscillazioni_del_soffio = _trillo(doppio[round(inizio * FS):round(fine * FS)])
        assert 5 <= oscillazioni_del_soffio <= 9 and abs(float(np.median(f)) - centro) < 0.02 * centro
    # Il lungo, a fine set e a fine incontro: più lungo del singolo, ma breve anche lui.
    lungo = ps.sorgente("fischio_lungo").astype(np.float64)
    assert len(_soffi(lungo)) == 1 and 1.5 * durata < len(lungo) / FS < 0.7
    assert _trillo(lungo)[2] > 15


def test_il_fischio_dura_quanto_il_suo_preset():
    # Non più allungato al tempo che il motore dà al fischio: la pausa del doppio e il lungo restano brevi.
    for variante, ruolo in ((E.SINGOLO, "fischio_singolo"), (E.DOPPIO, "fischio_doppio"), (E.LUNGO, "fischio_lungo")):
        fischio = _evento(1, 2.0, E.FISCHIO, (-50.0, 183.0), durata=1.4, fischio=variante)
        posato = ps.posati_dell_evento(fischio)[0]
        assert posato.ruolo == ruolo and len(posato.mono) == len(ps.sorgente(ruolo))


def _goal_o_fallo(tipo, a_chi, causa):
    """Un goal o un fallo, col suo fischio nello stesso istante, come li scrive il motore."""
    parte = "B" if a_chi == "A" else "A"
    # Il goal entra nella porta di chi lo subisce; il fallo si segna nella metà di chi lo commette.
    if tipo == E.GOAL:
        pos = (61.0, 362.0) if a_chi == "A" else (61.0, 4.0)
    else:
        pos = (61.0, 30.0) if parte == "A" else (61.0, 336.0)
    decisivo = _evento(1, 5.0, tipo, pos, causa=causa, a_chi=a_chi, chi=1 if parte == "A" else 2, parte=a_chi if tipo == E.GOAL else parte)
    fischio = _evento(2, 5.0, E.FISCHIO, (-50.0, 183.0), durata=0.8 if tipo == E.GOAL else 0.35, fischio=E.DOPPIO if tipo == E.GOAL else E.SINGOLO)
    return [decisivo, fischio]


def _energia_del_ruolo(eventi, ruolo, ascoltatore="A"):
    posato = next(p for p in ps.posa(eventi) if p.ruolo == ruolo)
    return sum(_energia(ps.spazializza(posato, ascoltatore))), posato


def test_dopo_il_goal_la_fanfara():
    # Richiesta di Gabriele: dopo il goal una piccolissima fanfara di tre o quattro note brevissime.
    from GBUtils import Acusticator, frequenza_nota

    eventi = _goal_o_fallo(E.GOAL, "A", "goal_scambio")
    posati = ps.posa(eventi)
    assert [p.ruolo for p in posati] == ["goal", "fanfara", "fischio_doppio"]
    goal, fanfara, fischio = posati
    # Viene dopo il fischio doppio, che parte insieme al goal, con un respiro.
    assert fischio.t == goal.t and fanfara.t == pytest.approx(fischio.t + len(fischio.mono) / FS + ps.RESPIRO_DELL_ESITO)
    composta = ps.componi(eventi, "A")
    inizio_fanfara = round((fanfara.t - composta.t0) * FS)
    assert np.any(composta.buffer[inizio_fanfara:]) and fanfara.t + len(fanfara.mono) / FS <= composta.t0 + composta.durata
    # Tre o quattro note brevissime che salgono, e in tutto meno di mezzo secondo.
    score, _kind, _adsr = Acusticator.preset(ps.SUONI["fanfara"])
    note = [(score[i], float(score[i + 1])) for i in range(0, len(score), 4) if score[i] != "p"]
    assert 3 <= len(note) <= 4 and all(durata <= 0.15 for _nota, durata in note) and sum(float(d) for d in score[1::4]) < 0.5
    assert frequenza_nota(note[-1][0]) > frequenza_nota(note[0][0])
    # Viene dalla testata di chi segna: chi ascolta da A la sente vicina se segna A, lontana se segna B.
    vicina, posato_vicino = _energia_del_ruolo(eventi, "fanfara")
    lontana, posato_lontano = _energia_del_ruolo(_goal_o_fallo(E.GOAL, "B", "goal_scambio"), "fanfara")
    assert vicina > 4 * lontana
    assert vista(posato_vicino.posizioni[0], "A")[1] < 50 < 350 < vista(posato_lontano.posizioni[0], "A")[1]


def test_il_fallo_si_distingue_dal_goal():
    # Richiesta di Gabriele: il suono del fallo più evidente, più lungo o di due note, perché si
    # distingua bene da quello del goal; il fallo resta riconoscibile dal fischio singolo e dalla
    # pallina, e il cicalino si aggiunge dopo il fischio.
    from GBUtils import Acusticator, frequenza_nota

    eventi = _goal_o_fallo(E.FALLO, "B", "out_sponda")
    fallo, fischio = (next(p for p in ps.posa(eventi) if p.ruolo == r) for r in ("fallo", "fischio_singolo"))
    assert fallo.t == pytest.approx(fischio.t + len(fischio.mono) / FS + ps.RESPIRO_DELL_ESITO)
    score, _kind, _adsr = Acusticator.preset(ps.SUONI["fallo"])
    note = [score[i].split(".")[0] for i in range(0, len(score), 4) if score[i] != "p"]
    fanfara = Acusticator.preset(ps.SUONI["fanfara"])[0]
    assert len(note) == 2
    assert len(ps.sorgente("fallo")) > 1.5 * len(ps.sorgente("fanfara"))
    assert max(frequenza_nota(n) for n in note) < min(frequenza_nota(fanfara[i]) for i in range(0, len(fanfara), 4) if fanfara[i] != "p") / 2
    # Viene dalla testata di chi commette il fallo: il punto va a B, il fallo è di A, vicino a chi ascolta da A.
    vicino, _p = _energia_del_ruolo(eventi, "fallo")
    lontano, _p = _energia_del_ruolo(_goal_o_fallo(E.FALLO, "A", "out_sponda"), "fallo")
    assert vicino > 4 * lontano
    # La paletta che cade suona col suo rumore e col cicalino; la palla morta non è un fallo e non ce l'ha.
    paletta = [p.ruolo for p in ps.posa(_goal_o_fallo(E.FALLO, "B", "paletta_caduta"))]
    assert paletta.count("paletta_caduta") == 1 and paletta.count("fallo") == 1
    morta = _evento(1, 5.0, E.PALLA_MORTA, (61.0, 100.0), causa="colpo_debole", a_chi=None)
    assert [p.ruolo for p in ps.posa([morta])] == []


def test_ogni_goal_e_ogni_fallo_dell_incontro_hanno_il_loro_esito():
    risultato = _incontro(4.0, seme=7).gioca()
    decisivi = [e for e in risultato.eventi if e.tipo in (E.GOAL, E.FALLO)]
    assert decisivi
    for e in decisivi:
        # Il motore fa partire il fischio nello stesso istante: l'esito arriva dopo di lui.
        fischio = next(x for x in risultato.eventi if x.n > e.n and x.tipo == E.FISCHIO)
        assert fischio.t == e.t
        ruolo = "fanfara" if e.tipo == E.GOAL else "fallo"
        assert [r for r, _ritardo in ps.suoni_fermi(e)].count(ruolo) == 1


def test_il_rotolamento_e_un_sonaglio_una_capriola_per_giro():
    tempi = np.arange(0.0, 1.0 + ps.PASSO, ps.PASSO)
    veloce = ps.capriole(tempi, np.full(len(tempi), 500.0), 3)
    lento = ps.capriole(tempi, np.full(len(tempi), 100.0), 3)
    # Una capriola per giro della pallina, cioè per ogni circonferenza percorsa, con lo scarto del giro.
    assert 500.0 / ps.GIRO_PALLINA * 0.8 <= len(veloce) <= 500.0 / ps.GIRO_PALLINA * 1.25
    assert 100.0 / ps.GIRO_PALLINA * 0.5 <= len(lento) <= 100.0 / ps.GIRO_PALLINA * 1.6
    assert all(0.0 <= t <= 1.0 for t in veloce) and veloce == sorted(veloce)
    # Sempre uguale per lo stesso evento, diverso per un altro; ferma, la pallina non suona.
    assert ps.capriole(tempi, np.full(len(tempi), 500.0), 3) == veloce != ps.capriole(tempi, np.full(len(tempi), 500.0), 4)
    assert ps.capriole(tempi, np.zeros(len(tempi)), 3) == []
    # La pallina che rallenta fa le capriole sempre più rade.
    rallenta = ps.capriole(tempi, np.linspace(600.0, 60.0, len(tempi)), 5)
    passi = np.diff(rallenta)
    assert np.mean(passi[-3:]) > 2 * np.mean(passi[:3])
    sonaglio = ps.sonaglio("rotolamento", tempi, np.full(len(tempi), 500.0), 3)
    assert len(sonaglio) >= round(tempi[-1] * FS) and np.any(sonaglio)
    # Nel volo il rotolamento è il sonaglio.
    volo = traiettoria((110.0, 340.0), (15.0, 30.0), (), 420.0, 20.0, 40.0, 0.12, "paletta")
    evento = _evento(5, 20.0, E.VOLO, (15.0, 30.0), durata=volo[-1].t - volo[0].t, volo=volo, chi=2, parte="B")
    rotolamento = next(p for p in ps.posati_del_volo(evento) if p.ruolo == "rotolamento")
    v = np.interp(volo[0].t + rotolamento.tempi, [tp.t for tp in volo], [tp.v for tp in volo])
    assert np.array_equal(rotolamento.mono, ps.sonaglio("rotolamento", rotolamento.tempi, v, evento.n))


def test_le_sorgenti_stanno_sotto_il_loro_tetto():
    # I livelli col margine: ogni sorgente si sente, e nessuna supera il tetto delle sorgenti, così un
    # colpo vicino, anche insieme al fischio, non porta la partita oltre il suo picco di progetto.
    ps.svuota_cache()
    for ruolo in ps.SUONI:
        for variante in range(ps.VARIANTI_RUMORE):
            picco = float(np.max(np.abs(ps.sorgente(ruolo, variante))))
            assert 0.05 < picco <= ps.TETTO_SORGENTI, (ruolo, variante, picco)
    # Il limitatore non tocca niente sotto il ginocchio e arrotonda il resto senza mai arrivare al tetto.
    prova = np.array([0.1, -0.5, 0.6, 0.9, -3.0, 4.0])
    limitato = ps.limita(prova.copy())
    assert np.array_equal(limitato[:3], prova[:3])
    assert np.all(np.abs(limitato) < ps.TETTO_SORGENTI) and limitato[3] > ps.GINOCCHIO_SORGENTI and limitato[4] < -ps.GINOCCHIO_SORGENTI


def _ponderazione_a():
    """Il filtro della ponderazione A, dalla sua forma analogica con la trasformata bilineare."""
    from scipy.signal import bilinear

    f1, f2, f3, f4 = 20.598997, 107.65265, 737.86223, 12194.217
    numeratore = [(2 * math.pi * f4) ** 2 * 10 ** (1.9997 / 20), 0, 0, 0, 0]
    denominatore = np.polymul([1, 4 * math.pi * f4, (2 * math.pi * f4) ** 2], [1, 4 * math.pi * f1, (2 * math.pi * f1) ** 2])
    denominatore = np.polymul(np.polymul(denominatore, [1, 2 * math.pi * f3]), [1, 2 * math.pi * f2])
    return bilinear(numeratore, denominatore, FS)


def _sonorita(stereo, finestra=0.05):
    """La sonorità di un suono stereo, in decibel: l'energia ponderata A dei due canali, sui 50 millesimi più forti."""
    from scipy.signal import lfilter

    b, a = _ponderazione_a()
    stereo = np.asarray(stereo, dtype=np.float64)
    energia = sum(lfilter(b, a, np.concatenate([stereo[:, c], np.zeros(2048)])) ** 2 for c in (0, 1))
    n = round(finestra * FS)
    return 10 * math.log10(float(np.max(np.convolve(energia, np.ones(n), mode="valid") / n)))


def _da_fermo(ruolo, mono, pos, ascoltatore="A"):
    return ps.spazializza(ps.Posato(ruolo, 0.0, mono, np.array([0.0]), [pos]), ascoltatore)


def test_ogni_timbro_si_sente_anche_dal_fondo_del_tavolo():
    # Revisione dei timbri: lo stesso suono vicino e in fondo al tavolo, per chi ascolta da A. Fra
    # questi due punti la legge del volume dello spazio approvato da Gabriele toglie al lontano 7,6
    # decibel, e la cupezza fino a 5 in più ai suoni chiari; ma un timbro che vive quasi tutto sopra
    # il taglio del lontano, come il controllo di soli pallini fra 2500 e 10000 Hz che perdeva 17
    # decibel, dall'altra parte del tavolo quasi sparisce. I fischi stanno fuori: vengono sempre
    # dall'arbitro, mai dal tavolo.
    vicino, lontano = (61.0, 30.0), (61.0, 340.0)
    legge = 20 * math.log10(ps.SPAZIO.punto(vicino, "A")[1] / ps.SPAZIO.punto(lontano, "A")[1])
    tempi = np.arange(0.0, 1.0 + ps.PASSO, ps.PASSO)
    perdite = {}
    for ruolo in ps.SUONI:
        if ruolo.startswith("fischio_"):
            continue
        valori = []
        for variante in range(ps.VARIANTI_RUMORE):
            if ruolo == "rotolamento":
                mono = ps.sonaglio(ruolo, tempi, np.full(len(tempi), 400.0), variante)
            elif ruolo == "controllo":
                mono = ps.in_fila(ruolo, 0.9, variante) * np.float32(ps.GUADAGNO_CONTROLLO)
            else:
                mono = ps.sorgente(ruolo, variante)
            valori.append(_sonorita(_da_fermo(ruolo, mono, vicino)) - _sonorita(_da_fermo(ruolo, mono, lontano)))
        perdite[ruolo] = float(np.mean(valori))
    fuori = {ruolo: round(p, 1) for ruolo, p in perdite.items() if not legge - 2.0 <= p <= legge + 5.0}
    assert not fuori, f"timbri che dal fondo del tavolo perdono troppo o troppo poco: {fuori}"


def test_il_fischio_suona_forte_quanto_nell_ascolto_libero():
    # Revisione dei timbri: il fischio viene dall'arbitro, a due metri e mezzo e un po' incupito, e
    # nella partita deve stare sopra i colpi come il segnaposto dell'ascolto libero approvato da
    # Gabriele; prima dei ritocchi il singolo, il più frequente, era 4,6 decibel sotto. Lo si
    # confronta col prototipo, dallo stesso punto; gli altri due sono lo stesso fischietto, forti uguali.
    from motore.tavolo import posizione_arbitro

    sonorita = {}
    for fischio, durata in ((E.SINGOLO, 0.35), (E.DOPPIO, 0.8), (E.LUNGO, 1.4)):
        e = _evento(1, 0.0, E.FISCHIO, posizione_arbitro(True), durata=durata, fischio=fischio)
        sonorita[fischio] = _sonorita(ps.spazializza(ps.posati_dell_evento(e)[0], "A"))
        if fischio == E.SINGOLO:
            approvato = _sonorita(resa.spazializza(resa.posati_dell_evento(e)[0], "A"))
            assert sonorita[fischio] == pytest.approx(approvato, abs=2.0)
    assert sonorita[E.DOPPIO] == pytest.approx(sonorita[E.SINGOLO], abs=1.0) and sonorita[E.LUNGO] == pytest.approx(sonorita[E.SINGOLO], abs=1.0)


# La riproduzione.

def _rumore(secondi):
    return np.full((round(secondi * FS), 2), 0.25, dtype=np.float32)


def test_il_buffer_parte_con_la_coda_di_zeri_e_si_ferma_con_la_maniglia():
    cassa, orologio = CassaFinta(), Orologio()
    rip = ps.Riproduttore(cassa, orologio)
    voce = rip.suona(_rumore(2.0), anticipo=0.5)
    acceso = cassa.buffer[0]
    assert len(acceso) == round(0.5 * FS) + round(2.0 * FS) + round(ps.CODA_DI_ZERI * FS)
    assert not np.any(acceso[:round(0.5 * FS)]) and not np.any(acceso[-round(ps.CODA_DI_ZERI * FS):])
    assert rip.posizione() == 0.0
    orologio.adesso += 1.5
    assert rip.posizione() == pytest.approx(1.0)
    assert rip.ferma() == pytest.approx(1.0)
    assert cassa.maniglie[0].fermate == 1 and voce.maniglia is None
    # La ripresa riparte dal secondo della pausa.
    rip.suona(_rumore(2.0), da=1.0)
    assert len(cassa.buffer[1]) == round(1.0 * FS) + round(ps.CODA_DI_ZERI * FS)
    orologio.adesso += 0.99
    assert not rip.battito()
    orologio.adesso += 0.02
    assert rip.battito() and rip.finito()
    assert cassa.maniglie[1].fermate == 1


def test_le_code_finiscono_di_suonare_e_il_silenzio_non_va_alla_cassa():
    cassa, orologio = CassaFinta(), Orologio()
    rip = ps.Riproduttore(cassa, orologio)
    rip.suona(_rumore(1.0))
    orologio.adesso += 0.6
    rip.suona(_rumore(1.0), sovrapponi=True)
    assert cassa.maniglie[0].fermate == 0
    orologio.adesso += 0.5
    assert not rip.battito()
    assert cassa.maniglie[0].fermate == 1 and cassa.maniglie[1].fermate == 0
    rip.suona(np.zeros((FS, 2), dtype=np.float32))
    assert len(cassa.buffer) == 2 and cassa.maniglie[1].fermate == 1
    orologio.adesso += 0.4
    assert rip.posizione() == pytest.approx(0.4)


# La cronologia e la velocità di gioco.

def _incontro(velocita=1.0, seme=31):
    return Incontro(giocatore(1, 12.0), giocatore(2, 13.0), SINGOLARE_3, seme=seme, dettaglio=COMPLETO, velocita=velocita)


def _segmenti(incontro, velocita=None):
    cronologia = ps.Cronologia(incontro)
    segmenti = []
    while (segmento := cronologia.prossimo(velocita)) is not None:
        segmenti.append(segmento)
    return segmenti


def test_i_segmenti_coprono_tutto_l_incontro():
    riferimento = _incontro().gioca()
    segmenti = _segmenti(_incontro())
    assert [e.n for s in segmenti for e in s.eventi] == [e.n for e in riferimento.eventi]
    assert segmenti[0].riscaldamento and segmenti[0].chiusura.tipo == E.RISCALDAMENTO_FINE
    assert segmenti[-1].ultimo and segmenti[-1].chiusura.tipo == E.FINE_INCONTRO
    chiusure = [s.chiusura.tipo for s in segmenti[1:]]
    assert set(chiusure) <= {E.PUNTO, E.RIPETIZIONE, E.AMMONIZIONE, E.PENALITA, E.FINE_SET, E.FINE_INCONTRO}
    assert chiusure.count(E.FINE_SET) == len(riferimento.set) - 1
    assert sum(1 for s in segmenti if s.fine_set) == len(riferimento.set)
    for segmento in segmenti:
        # Un punto che non chiude il suo segmento è quello che chiude il set, e sta col fischio lungo.
        dentro = [e for e in segmento.eventi[:-1] if e.tipo in (E.PUNTO, E.PENALITA)]
        assert len(dentro) <= 1
        if dentro:
            assert segmento.fine_set and ps.set_finito(dentro[0].punteggio, SINGOLARE_3)
        assert segmento.fine == pytest.approx(segmento.chiusura.t + segmento.chiusura.durata)
        assert segmento.eventi[0].t <= segmento.inizio <= segmento.fine
        # Si riparte dalla ripresa del gioco: il recupero o la consegna, se nel segmento c'è un punto.
        primo_del_punto = next((e for e, m, apre in segmento.voci if apre and m.genere == "punto"), None)
        if primo_del_punto is not None and not any(e.tipo in ps.SANZIONI for e in segmento.eventi):
            assert primo_del_punto.tipo in (E.RECUPERO, E.CONSEGNA) and segmento.inizio == primo_del_punto.t


def test_la_velocita_accorcia_pause_e_procedura_e_non_l_azione():
    lento = _incontro(1.0).gioca()
    veloce = _incontro(4.0).gioca()
    assert veloce.set == lento.set and [p.esito for p in veloce.punti] == [p.esito for p in lento.punti]
    assert veloce.durata_simulata < 0.75 * lento.durata_simulata
    reali = (E.VOLO, E.CONTROLLO, E.FISCHIO, E.CONSEGNA)
    scalati = (E.RECUPERO, E.ANNUNCIO, E.DOMANDA_PRONTO, E.CHIAMATA, E.SORTEGGIO)
    for m_lento, m_veloce in zip(lento.momenti, veloce.momenti, strict=True):
        tipi = [e.tipo for e in m_lento.eventi]
        assert tipi == [e.tipo for e in m_veloce.eventi]
        for e_lento, e_veloce in zip(m_lento.eventi, m_veloce.eventi, strict=True):
            if e_lento.tipo in reali:
                assert e_veloce.durata == pytest.approx(e_lento.durata, abs=1e-6)
            elif e_lento.tipo in scalati:
                assert e_veloce.durata == pytest.approx(e_lento.durata / 4, abs=2e-3)
        # Dal fischio del via alla battuta è azione: resta a tempo reale.
        if m_lento.genere == "punto" and E.FISCHIO in tipi and E.BATTUTA in tipi:
            via, battuta = tipi.index(E.FISCHIO), tipi.index(E.BATTUTA)
            if via < battuta:
                assert m_veloce.eventi[battuta].t - m_veloce.eventi[via].t == pytest.approx(m_lento.eventi[battuta].t - m_lento.eventi[via].t, abs=2e-3)
    # La pausa fra due punti, dal punto alla ripresa che segue, è un quarto.
    pause = []
    for risultato in (lento, veloce):
        eventi = risultato.eventi
        indice = next(i for i, e in enumerate(eventi) if e.tipo == E.PUNTO and eventi[i + 1].tipo in (E.RECUPERO, E.CONSEGNA))
        pause.append(eventi[indice + 1].t - eventi[indice].t)
    assert pause[1] == pytest.approx(pause[0] / 4, abs=2e-3)


def test_la_velocita_cambia_a_meta_incontro_con_gli_stessi_punti():
    riferimento = _incontro().gioca()
    gemello = _incontro()
    cronologia = ps.Cronologia(gemello)
    velocita = 1.0
    while cronologia.prossimo(velocita) is not None:
        assert gemello.regia.velocita == velocita
        velocita = 1.0 + (velocita % 8)
    assert gemello.risultato.set == riferimento.set
    assert gemello.risultato.durata_simulata < riferimento.durata_simulata
    with pytest.raises(ValueError, match="maggiore di zero"):
        _incontro().imposta_velocita(0)


def test_ogni_segmento_si_compone_dentro_il_margine():
    segmenti = _segmenti(_incontro(seme=5), 3.0)
    ultimo_fine = None
    for indice, segmento in enumerate(segmenti[:12]):
        fresco = indice % 2 == 0 or ultimo_fine is None
        da = segmento.inizio if fresco else ultimo_fine
        resa = ps.componi(segmento.eventi, "A" if indice % 3 else "B", da=da, fine=segmento.fine, anticipo=ps.ANTICIPO if fresco else None)
        assert resa.durata >= segmento.fine - resa.t0 - 1 / FS
        assert float(np.max(np.abs(ps.per_la_cassa(resa.buffer, 100)))) <= ps.TETTO
        assert math.isfinite(float(np.sum(resa.buffer)))
        ultimo_fine = segmento.fine


# Le correzioni della revisione: il livello uguale per ogni buffer, la paletta nel riscaldamento,
# la rampa della ripartenza e le pieghe della procedura.

def test_il_volume_della_partita_cresce_fino_in_fondo():
    # Decisione D30: il volume della partita moltiplica il buffer in proporzione da 0 a 100, senza
    # fermarsi a metà come faceva il volume degli effetti oltre il 53.
    fattori = [ps.fattore_del_volume(v) for v in range(101)]
    assert fattori[0] == 0.0 and all(b > a for a, b in itertools.pairwise(fattori))
    assert fattori[50] == pytest.approx(2 * fattori[25]) and fattori[100] == pytest.approx(2 * fattori[50])
    # A 100 il picco di progetto resta sotto il tetto; fuori scala vale il bordo.
    assert ps.PICCO_DI_PROGETTO * fattori[100] <= ps.TETTO
    assert ps.fattore_del_volume(150) == fattori[100] and ps.fattore_del_volume(-5) == 0.0
    # Al volume di progetto, 100, il fattore è quello dell'ascolto libero approvato; il predefinito delle
    # impostazioni è la metà, scelta di Gabriele.
    assert ps.VOLUME_DI_PROGETTO == 100 and impostazioni.VOLUME_PARTITA_PREDEFINITO == impostazioni.PREDEFINITE["volume_partita"] == 50
    assert ps.fattore_del_volume(ps.VOLUME_DI_PROGETTO) == pytest.approx(resa.GUADAGNO_PARTITA) == pytest.approx(1.0)
    assert (ps.TETTO, ps.GUADAGNO_PARTITA) == (resa.TETTO, resa.GUADAGNO_PARTITA)
    segmento = _segmenti(_incontro())[3]
    buffer = ps.componi(segmento.eventi, "A", da=segmento.inizio, fine=segmento.fine).buffer
    assert np.allclose(ps.per_la_cassa(buffer, ps.VOLUME_DI_PROGETTO), resa.con_margine(buffer), atol=1e-6)
    # E il predefinito suona davvero più piano: la metà in ampiezza.
    assert float(np.max(np.abs(ps.per_la_cassa(buffer, 50)))) == pytest.approx(float(np.max(np.abs(ps.per_la_cassa(buffer, 100)))) / 2, rel=1e-3)


def test_il_fattore_del_volume_e_lo_stesso_per_ogni_buffer():
    segmenti = _segmenti(_incontro())
    for livello in (75, 100):
        fattore = np.float32(ps.fattore_del_volume(livello))
        for segmento in segmenti[1:7]:
            for ascoltatore in ("A", "B"):
                buffer = ps.componi(segmento.eventi, ascoltatore, da=segmento.inizio, fine=segmento.fine).buffer
                assert float(np.max(np.abs(buffer))) <= ps.PICCO_DI_PROGETTO
                # Nessun buffer viene abbassato per conto suo: tutti per lo stesso fattore, punto dopo punto e lato per lato.
                assert np.array_equal(ps.per_la_cassa(buffer, livello), buffer * fattore)


def test_nel_riscaldamento_la_paletta_di_chi_riceve_suona():
    preliminari = _segmenti(_incontro())[0]
    sulla_paletta = [e for e in preliminari.eventi if e.tipo == E.RISCALDAMENTO_COLPO and e.volo[-1].tipo == "paletta"]
    assert len(sulla_paletta) > 10
    parate = [p for p in ps.posa(preliminari.eventi) if p.ruolo == "parata"]
    # Una parata per ogni volo che arriva sulla paletta, al suo istante e nel suo punto, con il giro delle varianti.
    assert [(p.t, p.posizioni[0]) for p in parate] == [(e.volo[-1].t, (e.volo[-1].x, e.volo[-1].y)) for e in sulla_paletta]
    assert [p.variante for p in parate[:5]] == [0, 1, 2, 3, 0]
    # Nel gioco la paletta del volo resta muta: suona la parata, che è un evento a sé.
    volo = [e for s in _segmenti(_incontro())[1:4] for e in s.eventi if e.tipo == E.VOLO and e.volo[-1].tipo == "paletta"]
    assert volo and not [p for p in ps.posati_del_volo(volo[0]) if p.ruolo == "parata"]


def test_la_ripartenza_a_meta_ha_la_rampa_in_testa():
    cassa, orologio = CassaFinta(), Orologio()
    rip = ps.Riproduttore(cassa, orologio)
    buffer = _rumore(2.0)
    rip.suona(buffer, da=1.0, anticipo=0.3)
    acceso = cassa.buffer[0]
    testa, rampa = round(0.3 * FS), round(ps.SFUMATURA * FS)
    # Dopo il silenzio dell'attesa il primo campione è zero, e la rampa sale per cinque millesimi.
    assert not np.any(acceso[:testa + 1])
    assert np.all(np.diff(acceso[testa:testa + rampa, 0]) > 0)
    assert np.array_equal(acceso[testa + rampa:testa + round(1.0 * FS)], buffer[round(1.0 * FS) + rampa:])
    assert rip.in_anticipo()
    orologio.adesso += 0.31
    assert not rip.in_anticipo()
    # Da capo niente rampa: il buffer comincia già col suo silenzio.
    rip.suona(buffer)
    assert np.array_equal(cassa.buffer[1][:len(buffer)], buffer)
    # Con tieni_le_code si ferma soltanto il buffer corrente, e la coda di quello di prima va avanti.
    rip.suona(buffer, sovrapponi=True)
    rip.suona(buffer, da=0.5, tieni_le_code=True)
    assert cassa.maniglie[1].fermate == 0 and cassa.maniglie[2].fermate == 1 and cassa.accese == 2


def test_le_pieghe_spostano_quello_che_viene_dopo():
    pieghe = ((2.0, 6.0, 0.25),)
    assert ps.secondi_del_buffer(1.0, 0.0, pieghe) == 1.0
    assert ps.secondi_del_buffer(4.0, 0.0, pieghe) == pytest.approx(2.5)
    assert ps.secondi_del_buffer(10.0, 0.0, pieghe) == pytest.approx(7.0)
    assert ps.secondi_del_buffer(10.0, 3.0, pieghe) == pytest.approx(4.75)
    for s in (0.5, 2.2, 2.9, 3.0, 6.5):
        assert ps.secondi_del_buffer(ps.istante_del_motore(s, 0.0, pieghe), 0.0, pieghe) == pytest.approx(s)
    # Una piega che allunga, per chi rallenta.
    assert ps.secondi_del_buffer(10.0, 1.0, ((2.0, 4.0, 2.0),)) == pytest.approx(11.0)
    # Due battute, a 1 e a 8 secondi, con la procedura in mezzo ripiegata a un quarto: la seconda arriva tre secondi prima, uguale.
    battute = [_evento(1, 1.0, E.BATTUTA, (61.0, 25.0), chi=1, parte="A"), _evento(2, 8.0, E.BATTUTA, (61.0, 25.0), chi=1, parte="A")]
    dritto = ps.componi(battute, "A", da=0.0)
    piegato = ps.componi(battute, "A", da=0.0, pieghe=pieghe)
    n = len(piegato.posati[1].mono)
    assert piegato.pieghe == pieghe and piegato.durata == pytest.approx(dritto.durata - 3.0, abs=2 / FS)
    assert np.array_equal(piegato.buffer[:round(2.0 * FS)], dritto.buffer[:round(2.0 * FS)])
    assert np.array_equal(piegato.buffer[round(5.0 * FS):round(5.0 * FS) + n], dritto.buffer[round(8.0 * FS):round(8.0 * FS) + n])
    assert piegato.secondi(8.0) == pytest.approx(5.0) and piegato.istante(5.0) == pytest.approx(8.0)
    assert piegato.in_silenzio(3.0) and not piegato.in_silenzio(5.0)


def test_ripiega_solo_quello_che_non_e_ancora_suonato():
    procedure = [(1.0, 3.0, 1.0), (5.0, 65.0, 1.0)]
    assert ps.ripiega(procedure, 1) == ()
    gia = ps.ripiega(procedure, 4)
    assert gia == ((1.0, 3.0, 0.25), (5.0, 65.0, 0.25))
    # Dal secondo 20 del motore a velocità 8: quello che è già suonato resta com'era.
    nuove = ps.ripiega(procedure, 8, gia, da=20.0)
    assert nuove == ((1.0, 3.0, 0.25), (5.0, 20.0, 0.25), (20.0, 65.0, 0.125))
    # Tornando alla velocità a cui il motore l'ha svolto, il resto non si piega più.
    assert ps.ripiega(procedure, 1, nuove, da=30.0) == ((1.0, 3.0, 0.25), (5.0, 20.0, 0.25), (20.0, 30.0, 0.125))
    # Alla stessa velocità non cambia niente: le pieghe contigue allo stesso fattore si fondono.
    assert ps.ripiega(procedure, 4, gia, da=20.0) == gia


def test_i_tratti_di_procedura_sono_il_tempo_che_la_velocita_accorcia():
    eventi, tratti = {}, {}
    for velocita in (1.0, 4.0):
        segmenti = _segmenti(_incontro(velocita, seme=5), velocita)
        eventi[velocita] = [e for s in segmenti for e in s.eventi]
        tratti[velocita] = [t for s in segmenti for t in s.procedure]
        assert {v for _a, _b, v in tratti[velocita]} == {velocita}
    tipi = {e.tipo for e in eventi[1.0]}
    assert {E.TIMEOUT_INIZIO, E.CAMBIO_CAMPO_INIZIO} <= tipi

    def azione(velocita, i):
        """Il tempo fra l'evento i e il seguente che non è pausa né procedura: non dipende dalla velocità."""
        a, b = eventi[velocita][i].t, eventi[velocita][i + 1].t
        return (b - a) - sum(max(0.0, min(b, tb) - max(a, ta)) for ta, tb, _v in tratti[velocita] if ta < b and tb > a)

    for i in range(len(eventi[1.0]) - 1):
        assert azione(1.0, i) == pytest.approx(azione(4.0, i), abs=0.004), (eventi[1.0][i].tipo, eventi[1.0][i + 1].tipo)


# La decisione D30: le pause lunghe, che non si sentono mai, e la pausa di sempre che resta.

def test_il_segmento_sa_se_ha_una_pausa_lunga():
    segmenti = _segmenti(_incontro(seme=50))
    con_la_pausa = [s for s in segmenti if s.pausa_lunga]
    # Ogni set comincia con la sua pausa lunga, l'inizio del set; poi i due time-out e il cambio campo del terzo set.
    tipi = [{e.tipo for e in s.preambolo} & ps.PAUSE_LUNGHE for s in con_la_pausa]
    assert sum(E.INIZIO_SET in t for t in tipi) == 3
    assert sum(E.TIMEOUT_INIZIO in t for t in tipi) == 2 and sum(E.CAMBIO_CAMPO_INIZIO in t for t in tipi) == 3
    for s in segmenti:
        # Il preambolo è tutto quello che viene prima della ripresa del gioco, e la ripresa è l'inizio.
        assert all(e.t <= s.inizio + ps.TOLLERANZA for e in s.preambolo)
        if s.preambolo:
            assert s.eventi[len(s.preambolo)].t == s.inizio
        if not s.pausa_lunga:
            assert not {e.tipo for e in s.eventi[:len(s.preambolo)]} & ps.PAUSE_LUNGHE
    # Il riscaldamento non ha preambolo: comincia con l'incontro.
    assert segmenti[0].riscaldamento and segmenti[0].preambolo == [] and not segmenti[0].pausa_lunga


def test_la_pausa_di_sempre_prima_della_pausa_lunga():
    for velocita in (1.0, 4.0):
        segmenti = _segmenti(_incontro(velocita, seme=50), velocita)
        for precedente, segmento in itertools.pairwise(segmenti):
            primo = segmento.eventi[0]
            if not segmento.pausa_lunga:
                assert segmento.salti == () and segmento.udibili == segmento.eventi
                continue
            # La pausa lunga, dal primo evento alla ripresa del gioco, si salta: i suoi eventi non
            # suonano, e a ogni velocità il suo tratto dura pochi campioni.
            assert segmento.salti == ((primo.t, segmento.inizio),)
            assert segmento.udibili == segmento.eventi[len(segmento.preambolo):] and segmento.udibili[0].t == segmento.inizio
            for adesso in (velocita, 8):
                assert ps.secondi_del_buffer(segmento.inizio, primo.t, segmento.pieghe(adesso)) < 5 / FS
            dopo_il_punto = [ps.secondi_del_buffer(segmento.inizio, precedente.fine, segmento.pieghe(adesso)) for adesso in (velocita, 8)]
            if any(e.tipo == E.TIMEOUT_INIZIO for e in segmento.preambolo):
                # Dopo il punto il motore lascia la pausa fra i punti, alla velocità di gioco; poi il
                # fischio del time-out. La pausa resta, e se la velocità cambia si ripiega come le altre.
                assert precedente.chiusura.tipo == E.PUNTO and primo.tipo == E.FISCHIO
                assert dopo_il_punto == pytest.approx([5.5 / velocita, 5.5 / 8], abs=0.002)
            if precedente.riscaldamento:
                # Dopo il riscaldamento il primo set comincia subito: la sua pausa lunga non lascia niente prima.
                assert primo.tipo == E.INIZIO_SET
                assert dopo_il_punto == pytest.approx([0.0, 0.0], abs=0.002)


def test_i_salti_si_piegano_quasi_a_zero():
    procedure = [(1.0, 3.0, 1.0), (5.0, 65.0, 1.0), (70.0, 72.0, 1.0)]
    salti = ((4.0, 71.0),)
    pieghe = ps.ripiega(procedure, 4, salti=salti)
    assert pieghe == ((1.0, 3.0, 0.25), (4.0, 71.0, ps.PIEGA_DEL_SALTO), (71.0, 72.0, 0.25))
    # Il salto resta piegato a ogni velocità, anche a quella a cui il motore ha svolto la procedura,
    # e la procedura che sta dentro non conta.
    assert ps.ripiega(procedure, 1, salti=salti) == ((4.0, 71.0, ps.PIEGA_DEL_SALTO),)
    # Ripiegando da un istante dentro il salto, quello che è già suonato resta com'era, e il salto continua.
    assert ps.ripiega(procedure, 8, pieghe, da=30.0, salti=salti) == ((1.0, 3.0, 0.25), (4.0, 71.0, ps.PIEGA_DEL_SALTO), (71.0, 72.0, 0.125))
    # Il buffer attraversa i 67 secondi del salto in pochi campioni, e l'inverso torna.
    assert ps.secondi_del_buffer(71.0, 0.0, pieghe) - ps.secondi_del_buffer(4.0, 0.0, pieghe) < 5 / FS
    for t in (0.5, 2.0, 3.5, 71.5, 80.0):
        assert ps.istante_del_motore(ps.secondi_del_buffer(t, 0.0, pieghe), 0.0, pieghe) == pytest.approx(t)
