"""
Test della issue 10, decisione D37 del 24 ottobre 2026: il lungolinea che va verso la porta, in goal o
nella difesa irregolare, corre sul suo lato fino all'angolo di chi difende, e lì gira in silenzio
verso la tasca, con la tappa svolta; passa al centro soltanto negli ultimi centimetri, dentro l'area di
porta. La diagonale resta com'era. La svolta non suona, e il rotolamento resta sul lato fino a lei. La
cronaca dice il goal di lungolinea e quello di diagonale con le parole di Gabriele. Gli esiti sono
gli stessi di prima, incontro per incontro con gli stessi semi, e gli altri voli non cambiano. Le
invarianti vedono una svolta fuori dall'angolo, e traiettoria chiude il volo anche con un arrivo
che ha il tipo di un rimbalzo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import random

import numpy as np
import pytest
from aiuti_dal_vivo import vieta_la_cassa_vera
from aiuti_motore import giocatore
from test_identita_motore import _risultato_in_json

import partita_sonora as ps
from costanti import RAGGIO_AREA_PORTA, RAGGIO_CURVE, RAGGIO_PALLINA
from motore import cronaca as C
from motore import eventi as E
from motore.eventi import Evento, Tappa
from motore.incontro import COMPLETO, SINGOLARE_3, SQUADRE, simula_incontro
from motore.regia import LUNGOLINEA, Regia, controlla_invarianti
from motore.squadre import Squadra
from motore.tavolo import SPONDA_DESTRA_A, SPONDA_SINISTRA_A, distanza_di, lato_di, posizione_al_tempo, traiettoria

DIAGONALI = frozenset(("diagonalesx", "diagonaledx"))
INCONTRI = 40
GARE_A_SQUADRE = 4


def _partite():
    """Quaranta singolari e quattro gare a squadre con semi fissi, in modalità completa, con i nomi della cronaca."""
    rng = random.Random(10)
    partite = []
    for seme in range(INCONTRI):
        a = giocatore(1, valore=rng.uniform(8, 30), mancino=rng.random() < 0.2, cognome="Rossi", nome="Mario")
        b = giocatore(2, valore=rng.uniform(8, 30), ambidestro=rng.random() < 0.3, sesso="f", cognome="Bianchi", nome="Anna")
        partite.append((simula_incontro(a, b, SINGOLARE_3, seme=seme, dettaglio=COMPLETO), C.nomi_dei_giocatori([a, b])))
    for seme in range(GARE_A_SQUADRE):
        a = Squadra("Leoni", tuple(giocatore(i, valore=rng.uniform(8, 30), sesso=s) for i, s in ((1, "m"), (2, "m"), (3, "f"))))
        b = Squadra("Tigri", tuple(giocatore(i, valore=rng.uniform(8, 30), sesso=s) for i, s in ((11, "f"), (12, "f"), (13, "m"))))
        nomi = C.nomi_dei_giocatori([*a.giocatori, *b.giocatori], squadre=(a, b))
        partite.append((simula_incontro(a, b, SQUADRE, seme=100 + seme, dettaglio=COMPLETO), nomi))
    return partite


def _volo_di_prima(self, partenza, punto, arrivo, v0, difensore, tipo_arrivo):
    """Il volo di prima della issue 10: una retta sola dalla partenza all'arrivo vicino alla tasca."""
    return self._volo(partenza, arrivo, (), v0, tipo_arrivo)


@pytest.fixture(scope="module")
def partite():
    return _partite()


@pytest.fixture(scope="module")
def partite_di_prima():
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(Regia, "_volo_lungolinea_in_porta", _volo_di_prima)
        return _partite()


def _verso_la_porta(risultato, colpi):
    """I voli dei colpi indicati che vanno verso la porta, in goal o nella difesa irregolare, con la parte di chi difende."""
    eventi = risultato.eventi
    parti = {e.chi: e.parte for e in eventi if e.chi is not None and e.parte is not None}
    for indice, ev in enumerate(eventi):
        dati = ev.dati or {}
        if ev.tipo != E.VOLO or ev.colpo not in colpi or "verso" not in dati or dati.get("ribattuta"):
            continue
        parata = next(e for e in eventi[indice + 1:] if e.tipo == E.PARATA)
        if ev.volo[-1].tipo == "porta" or parata.causa == "difesa_irregolare":
            yield ev, parti[dati["verso"]]


def test_il_lungolinea_resta_sul_suo_lato_fino_all_angolo(partite):
    visti = goal = 0
    for risultato, _nomi in partite:
        for ev, parte in _verso_la_porta(risultato, LUNGOLINEA):
            visti += 1
            goal += ev.volo[-1].tipo == "porta"
            tipi = [tappa.tipo for tappa in ev.volo]
            assert tipi.count("svolta") == 1 and "sponda" not in tipi and "curva" not in tipi, tipi
            svolta = ev.volo[tipi.index("svolta")]
            # La svolta sta sul fondo di chi difende, dentro la curva dell'angolo, dalla parte del colpo.
            lato = lato_di(ev.volo[0].x, parte)
            assert lato != "centro" and lato_di(svolta.x, parte) == lato
            assert distanza_di(svolta.y, parte) == pytest.approx(RAGGIO_PALLINA)
            assert min(svolta.x - SPONDA_SINISTRA_A, SPONDA_DESTRA_A - svolta.x) <= RAGGIO_CURVE + 1e-6
            # Ogni 5 millesimi: fino alla svolta la pallina non lascia il suo lato, e dopo passa al
            # centro soltanto negli ultimi centimetri, dentro l'area di porta.
            for t in np.arange(ev.volo[0].t, ev.volo[-1].t, 0.005):
                x, y = posizione_al_tempo(ev.volo, t)
                if t <= svolta.t:
                    assert lato_di(x, parte) == lato, (ev.n, t)
                elif lato_di(x, parte) == "centro":
                    assert distanza_di(y, parte) < RAGGIO_AREA_PORTA, (ev.n, t, y)
    assert visti >= 40 and goal >= 30


def test_la_diagonale_resta_com_era(partite):
    viste = 0
    for risultato, _nomi in partite:
        for ev, _parte in _verso_la_porta(risultato, DIAGONALI):
            viste += 1
            assert [tappa.tipo for tappa in ev.volo] == ["partenza", "sotto_schermo", ev.volo[-1].tipo]
    assert viste >= 30


def _energia(stereo):
    return float(np.sum(stereo[:, 0] ** 2)), float(np.sum(stereo[:, 1] ** 2))


def test_la_svolta_non_suona_e_il_rotolamento_resta_sul_lato(partite, monkeypatch):
    vieta_la_cassa_vera(monkeypatch)
    assert "svolta" in E.TAPPE and "svolta" not in E.TAPPE_TERMINALI and "svolta" not in ps.TAPPE_SONORE
    ascoltati = 0
    for risultato, _nomi in partite[:8]:
        for ev, parte in _verso_la_porta(risultato, LUNGOLINEA):
            ascoltati += 1
            # Nel volo suona soltanto il rotolamento, fino alla porta: nessun tocco di sponda alla svolta.
            posati = ps.posati_del_volo(ev)
            assert [posato.ruolo for posato in posati] == ["rotolamento"]
            (rotolamento,) = posati
            assert rotolamento.t + rotolamento.tempi[-1] >= ev.volo[-1].t - ps.PASSO
            # Il buffer stereo per chi difende, composto senza suonarlo: fino alla svolta la pallina
            # si sente dal lato del colpo.
            svolta = next(tappa for tappa in ev.volo if tappa.tipo == "svolta")
            stereo = ps.spazializza(rotolamento, parte)
            canale = 1 if lato_di(ev.volo[0].x, parte) == "destra" else 0
            prima = _energia(stereo[:round((svolta.t - rotolamento.t) * ps.FS)])
            assert prima[canale] > 3 * prima[1 - canale], (ev.n, prima)
            assert ps.componi([ev], parte).buffer.shape[1] == 2
    assert ascoltati >= 5


def _volo_di_prova(colpo, ultima, svolta):
    tappe = [Tappa(1.0, 97.0, 330.0, 600.0, "partenza"), Tappa(1.25, 97.0, 183.0, 560.0, "sotto_schermo")]
    if svolta:
        tappe.append(Tappa(1.55, 100.0, 3.0, 530.0, "svolta"))
    tappe.append(Tappa(1.65, 61.0, 6.0, 450.0, ultima))
    return Evento(n=7, t=1.0, tipo=E.VOLO, fase=E.GIOCO, durata=0.65, chi=2, parte="B", pos=(61.0, 6.0), lato="centro", distanza=360.0,
                  colpo=colpo, volo=tuple(tappe), dati={"verso": 1})


def test_le_frasi_del_goal_di_lungolinea_e_di_diagonale():
    nomi = {1: C.Nome("Rossi", "m"), 2: C.Nome("Bianchi", "f")}
    for colpo in ("lungolineasx", "lungolineadx"):
        assert C.frase(_volo_di_prova(colpo, "porta", True), nomi) == "Un veloce lungolinea si insacca nella porta di Rossi."
    assert C.frase(_volo_di_prova("lungolineadx", "porta", True), {1: C.Nome("Anna Neri", "f")}) == "Un veloce lungolinea si insacca nella porta di Anna Neri."
    for colpo in ("diagonalesx", "diagonaledx"):
        assert C.frase(_volo_di_prova(colpo, "porta", False), nomi) == "La diagonale prende precisa il punto G e finisce in goal."
    # Gli altri goal tengono la frase di sempre; nella difesa irregolare la svolta non è un rimbalzo.
    assert C.frase(_volo_di_prova("bomba", "porta", False), nomi) == "La pallina corre dritta e punta alla porta di Rossi."
    assert C.frase(_volo_di_prova("lungolineasx", "paletta", True), nomi) == "La pallina corre dritta e arriva al centro di Rossi."
    assert C.frase(_volo_di_prova("lungolineasx", "porta", True), nomi, C.SINTETICA) is None
    assert C.frase(_volo_di_prova("lungolineasx", "porta", True), nomi, C.TECNICA).startswith("Un veloce lungolinea si insacca nella porta di Rossi. (secondo ")


def test_la_cronaca_degli_incontri_dice_i_goal_con_le_parole_di_gabriele(partite):
    insaccati = diagonali = 0
    for risultato, nomi in partite:
        prima = insaccati
        for ev, _parte in _verso_la_porta(risultato, LUNGOLINEA | DIAGONALI):
            if ev.volo[-1].tipo != "porta":
                continue
            testo = C.frase(ev, nomi)
            if ev.colpo in LUNGOLINEA:
                insaccati += 1
                assert testo == f"Un veloce lungolinea si insacca nella porta di {nomi[ev.dati['verso']].testo}."
            else:
                diagonali += 1
                assert testo == "La diagonale prende precisa il punto G e finisce in goal."
        righe = C.componi(risultato.momenti, nomi)
        assert sum(1 for riga in righe if riga.startswith("Un veloce lungolinea si insacca")) == insaccati - prima
    assert insaccati >= 30 and diagonali >= 30


def _firma_del_volo(ev):
    return [(tappa.tipo, tappa.x, tappa.y) for tappa in ev.volo]


def test_esiti_ed_eventi_come_prima_con_gli_stessi_semi(partite, partite_di_prima):
    cambiati = 0
    for (dopo, _n), (prima, _m) in zip(partite, partite_di_prima, strict=True):
        # Punti, set, vincitore, statistiche e ogni punto: tutto ciò che l'incontro decide resta uguale.
        assert _risultato_in_json(dopo) == _risultato_in_json(prima)
        assert dopo.vincitore == prima.vincitore and dopo.set == prima.set
        assert [e.tipo for e in dopo.eventi] == [e.tipo for e in prima.eventi]
        nuovi = {ev.n for ev, _parte in _verso_la_porta(dopo, LUNGOLINEA)}
        for ed, ep in zip(dopo.eventi, prima.eventi, strict=True):
            if ed.tipo != E.VOLO:
                continue
            if ed.n in nuovi:
                cambiati += 1
                assert _firma_del_volo(ed) != _firma_del_volo(ep)
                # Dopo un goal di lungolinea gli istanti slittano un poco: partenza, velocità e arrivo restano quelli.
                assert (ed.volo[0][1:], ed.volo[-1].x, ed.volo[-1].y, ed.volo[-1].tipo) == (ep.volo[0][1:], ep.volo[-1].x, ep.volo[-1].y, ep.volo[-1].tipo)
            else:
                assert _firma_del_volo(ed) == _firma_del_volo(ep), (ed.n, ed.colpo)
        assert controlla_invarianti(dopo.eventi) == []
    assert cambiati >= 40


def test_le_invarianti_vedono_una_svolta_fuori_dall_angolo():
    def volo(*tappe):
        return Evento(n=1, t=0.0, tipo=E.VOLO, fase=E.GIOCO, durata=tappe[-1].t, volo=tappe)

    partenza = Tappa(0.0, 25.0, 30.0, 600.0, "partenza")
    porta = Tappa(0.7, 61.0, 360.0, 400.0, "porta")
    assert controlla_invarianti([volo(partenza, Tappa(0.6, 20.0, 363.0, 500.0, "svolta"), porta)]) == []
    for fuori in (Tappa(0.6, 40.0, 363.0, 500.0, "svolta"), Tappa(0.6, 20.0, 300.0, 500.0, "svolta")):
        assert any("svolta" in problema for problema in controlla_invarianti([volo(partenza, fuori, porta)]))
    assert any("svolta" in problema for problema in controlla_invarianti([volo(partenza, Tappa(0.6, 20.0, 363.0, 0.0, "svolta"))]))


def test_l_arrivo_chiude_il_volo_anche_col_tipo_di_un_rimbalzo():
    # La trappola dello studio della issue 10: un arrivo di tipo curva faceva ripartire il ciclo senza fine.
    for tipo in ("curva", "sponda", "svolta"):
        volo = traiettoria((25.0, 30.0), (20.0, 363.0), (), 600.0, 0.0, 40.0, 0.12, tipo)
        assert [tappa.tipo for tappa in volo] == ["partenza", "sotto_schermo", tipo]
