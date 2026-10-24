"""
Test della issue 12, decisione D37 del 24 ottobre 2026: nello schermo contro la pallina batte sullo
schermo e torna indietro. La cronaca lo dice con le parole di Gabriele. Nella partita dal vivo, dopo
l'urto, un volo breve, il ritorno, porta la pallina verso chi l'ha tirata, nella direzione del colpo
specchiata dallo schermo, per una strada fra 40 e 120 cm, finché si ferma da sola, entro il punto
assegnato. Comincia nell'istante dell'urto e l'orologio resta lì: il fallo, segnato allo schermo, il
fischio e la chiamata arrivano all'urto come prima, e tolto il ritorno la scena è quella di prima,
istante per istante. Il recupero dell'arbitro parte da dove la pallina si è fermata. Nel buffer
composto senza suonarlo lo schermo suona una volta sola, e dall'urto la pallina rotola via dallo
schermo, anche dopo il cicalino del fallo. Le invarianti vedono uno schermo senza ritorno e un ritorno
sbagliato. Gli esiti sono quelli della modalità essenziale con gli stessi semi, e il dado della
partita non tira niente di nuovo: l'impronta del motore la guarda tests/test_identita_motore.py.
Dalle verifiche, sempre il 24 ottobre: a ogni velocità di gioco quello che segue il punto aspetta che la
pallina sia ferma, e fino a velocità 4 la pausa fra i punti resta quella di sempre; le invarianti vedono
il recupero addosso alla pallina che rotola, e nella partita dal vivo nessuna piega della procedura cade
dentro il ritorno, nemmeno se la velocità cambia a punto già composto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import dataclasses
import itertools
import math
import random

import numpy as np
import pytest
from aiuti_dal_vivo import vieta_la_cassa_vera
from aiuti_motore import giocatore
from test_identita_motore import _risultato_in_json

import partita_sonora as ps
from costanti import META_TAVOLO
from motore import cronaca as C
from motore import eventi as E
from motore.eventi import CAUSE, Evento, Tappa
from motore.incontro import COMPLETO, ESSENZIALE, SINGOLARE_3, SQUADRE, Incontro, simula_incontro
from motore.regia import FRENATA_DEL_RITORNO, RITORNO_DALLO_SCHERMO, Regia, controlla_invarianti
from motore.squadre import Squadra
from motore.taratura import TARATURA
from motore.tavolo import LARGHEZZA_TAVOLO, MARGINE_GIOCO, distanza_di, lato_di, vista

INCONTRI = 30
GARE_A_SQUADRE = 3


def _partite(dettaglio, velocita=1.0):
    """Trenta singolari e tre gare a squadre con semi fissi, nella modalità e alla velocità di gioco indicate, con i nomi della cronaca."""
    rng = random.Random(12)
    partite = []
    for seme in range(INCONTRI):
        a = giocatore(1, valore=rng.uniform(8, 30), mancino=rng.random() < 0.2, giocorapido=rng.random() < 0.3, cognome="Rossi", nome="Mario")
        b = giocatore(2, valore=rng.uniform(8, 30), ambidestro=rng.random() < 0.3, sesso="f", cognome="Bianchi", nome="Anna")
        partite.append((simula_incontro(a, b, SINGOLARE_3, seme=seme, dettaglio=dettaglio, velocita=velocita), C.nomi_dei_giocatori([a, b])))
    for seme in range(GARE_A_SQUADRE):
        a = Squadra("Leoni", tuple(giocatore(i, valore=rng.uniform(8, 30), sesso=s) for i, s in ((1, "m"), (2, "m"), (3, "f"))))
        b = Squadra("Tigri", tuple(giocatore(i, valore=rng.uniform(8, 30), sesso=s) for i, s in ((11, "f"), (12, "f"), (13, "m"))))
        nomi = C.nomi_dei_giocatori([*a.giocatori, *b.giocatori], squadre=(a, b))
        partite.append((simula_incontro(a, b, SQUADRE, seme=300 + seme, dettaglio=dettaglio, velocita=velocita), nomi))
    return partite


def _senza_ritorno(self, _eventi, _chi, volo, _colpo_n):
    """La regia di prima della issue 12, con la stessa estrazione della scena: nessun ritorno, la pallina resta allo schermo."""
    self._uniforme(*RITORNO_DALLO_SCHERMO)
    return volo[-1].x, volo[-1].y


@pytest.fixture(scope="module")
def partite():
    return _partite(COMPLETO)


@pytest.fixture(scope="module")
def partite_senza_ritorno():
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(Regia, "_ritorno_dallo_schermo", _senza_ritorno)
        return _partite(COMPLETO)


def _e_ritorno(ev):
    return ev.tipo == E.VOLO and bool((ev.dati or {}).get("ritorno"))


def _schermi(risultato):
    """Gli schermi contro dell'incontro: il volo fino all'urto, il ritorno, il fallo e l'indice del fallo."""
    eventi = risultato.eventi
    for indice, ev in enumerate(eventi):
        if ev.tipo == E.FALLO and ev.causa == "schermo_contro":
            yield eventi[indice - 2], eventi[indice - 1], ev, indice


# La cronaca.

def test_la_cronaca_dice_che_la_pallina_batte_sullo_schermo_e_torna_indietro():
    assert CAUSE["schermo_contro"].frase == "la pallina di {chi} batte sullo schermo e torna indietro"
    assert CAUSE["schermo_sopra"].frase == "la pallina di {chi} passa sopra lo schermo"
    nomi = {1: C.Nome("Rossi", "m")}
    fallo = Evento(n=9, t=4.0, tipo=E.FALLO, fase=E.GIOCO, chi=1, parte="A", pos=(61.0, 181.0), lato="centro", causa="schermo_contro",
                   chiamata="schermo_centrale", fischio=E.SINGOLO, punti=1, a_chi="B")
    assert C.frase(fallo, nomi) == "Fischio: schermo centrale, la pallina di Rossi batte sullo schermo e torna indietro."
    assert C.frase(fallo, nomi, C.SINTETICA) is None


def test_la_cronaca_degli_incontri_e_il_ritorno_muto(partite):
    visti = 0
    for risultato, nomi in partite:
        for _andata, ritorno, fallo, _indice in _schermi(risultato):
            visti += 1
            assert C.frase(fallo, nomi) == f"Fischio: schermo centrale, la pallina di {nomi[fallo.chi].testo} batte sullo schermo e torna indietro."
            # Il ritorno non ha una frase sua: lo dice già quella del fallo.
            assert all(C.frase(ritorno, nomi, livello) is None for livello in C.LIVELLI)
        righe = C.componi(risultato.momenti, nomi)
        assert not any("urta lo schermo" in riga for riga in righe)
    assert visti >= 50


# La scena.

def test_ogni_schermo_contro_torna_indietro(partite):
    visti = 0
    for risultato, _nomi in partite:
        eventi = risultato.eventi
        assert controlla_invarianti(eventi) == []
        ritorni = [ev for ev in eventi if _e_ritorno(ev)]
        assert len(ritorni) == sum(1 for _s in _schermi(risultato))
        for andata, ritorno, fallo, indice in _schermi(risultato):
            visti += 1
            urto, partenza, fermo = andata.volo[-1], ritorno.volo[0], ritorno.volo[-1]
            assert andata.tipo == E.VOLO and urto.tipo == "schermo" and _e_ritorno(ritorno) and ritorno.chi == fallo.chi == andata.chi
            # Riparte dall'urto, nello stesso istante, e rotola piano fino a fermarsi da sola.
            assert (partenza.t, partenza.x, partenza.y) == pytest.approx((urto.t, urto.x, urto.y), abs=1e-9)
            assert [tappa.tipo for tappa in ritorno.volo] == ["partenza", "fermo"] and fermo.v == pytest.approx(0.0, abs=1e-3)
            strada = math.dist((partenza.x, partenza.y), (fermo.x, fermo.y))
            assert RITORNO_DALLO_SCHERMO[0] * 0.95 <= strada <= RITORNO_DALLO_SCHERMO[1] + 1e-6
            assert partenza.v == pytest.approx(math.sqrt(2.0 * FRENATA_DEL_RITORNO * strada))
            assert ritorno.durata == pytest.approx(partenza.v / FRENATA_DEL_RITORNO, abs=2e-3)
            # Verso chi l'ha tirata, sulla sua metà del tavolo, e di lato come lo specchio dello schermo.
            parte = fallo.parte
            assert distanza_di(fermo.y, parte) < distanza_di(urto.y, parte) < META_TAVOLO
            assert vista((fermo.x, fermo.y), parte)[1] < vista((urto.x, urto.y), parte)[1]
            dx_andata, dx_ritorno = urto.x - andata.volo[0].x, fermo.x - urto.x
            assert dx_andata * dx_ritorno >= 0 and MARGINE_GIOCO <= fermo.x <= LARGHEZZA_TAVOLO - MARGINE_GIOCO
            # Il fallo resta allo schermo, e con lui il fischio, all'istante dell'urto.
            assert fallo.pos == (round(urto.x, 1), round(urto.y, 1)) and fallo.t == pytest.approx(urto.t, abs=2e-3)
            fischio = eventi[indice + 1]
            assert fischio.tipo == E.FISCHIO and fischio.t == fallo.t == ritorno.t
            # A velocità di gioco 1 la pallina si ferma prima che l'arbitro assegni il punto.
            punto = next(e for e in eventi[indice:] if e.tipo == E.PUNTO)
            assert ritorno.t + ritorno.durata <= punto.t + 2e-3
    assert visti >= 50
    # Gli altri falli non tornano indietro: nemmeno la pallina che passa sopra lo schermo.
    for risultato, _nomi in partite:
        for indice, ev in enumerate(risultato.eventi):
            if _e_ritorno(ev):
                assert risultato.eventi[indice + 1].causa == "schermo_contro"


def test_la_strada_del_ritorno_viene_dal_caso_della_scena(partite):
    strade = [math.dist((r.volo[0].x, r.volo[0].y), (r.volo[-1].x, r.volo[-1].y)) for risultato, _n in partite for _a, r, _f, _i in _schermi(risultato)]
    # Sparse su tutto l'intervallo, corte e lunghe.
    assert min(strade) < 55.0 and max(strade) > 105.0 and 65.0 < float(np.median(strade)) < 95.0


def test_il_recupero_parte_da_dove_la_pallina_si_ferma(partite):
    recuperi = 0
    for risultato, _nomi in partite:
        eventi = risultato.eventi
        for _andata, ritorno, _fallo, indice in _schermi(risultato):
            ripresa = next((e for e in eventi[indice:] if e.tipo in (E.RECUPERO, E.CONSEGNA)), None)
            if ripresa is None or ripresa.tipo != E.RECUPERO:
                # Dopo l'ultimo punto del set la pallina la riprende l'arbitro per il set che segue.
                continue
            recuperi += 1
            fermo = ritorno.volo[-1]
            assert ripresa.pos == (round(fermo.x, 1), round(fermo.y, 1)) and ripresa.dati == {"da": "tavolo"}
    assert recuperi >= 40


@pytest.mark.parametrize("velocita", [4.0, 8.0])
def test_a_ogni_velocita_quello_che_segue_il_punto_aspetta_la_pallina_ferma(velocita):
    """
    Dalle verifiche: il ritorno è azione e resta a tempo reale, mentre la pausa fra i punti si accorcia
    con la velocità di gioco, e da velocità 5 l'arbitro recuperava la pallina mentre rotolava ancora. Ora
    il primo evento dopo il punto, il recupero o quello che viene prima, aspetta che sia ferma; il punto
    si assegna sempre subito dopo la chiamata. A velocità 4, la predefinita, la pausa basta sempre e
    resta quella di sempre.
    """
    pausa = TARATURA.PAUSA_FRA_PUNTI / velocita
    visti = attese = recuperi = 0
    for risultato, _nomi in _partite(COMPLETO, velocita):
        eventi = risultato.eventi
        assert controlla_invarianti(eventi) == []
        for _andata, ritorno, fallo, indice in _schermi(risultato):
            j = next(k for k in range(indice, len(eventi)) if eventi[k].tipo == E.PUNTO)
            if j + 1 == len(eventi):
                continue
            punto, seguente, fermo = eventi[j], eventi[j + 1], ritorno.volo[-1].t
            visti += 1
            assert punto.t == pytest.approx(fallo.t + max(TARATURA.FISCHIO_SINGOLO, TARATURA.RITARDO_CHIAMATA / velocita) + TARATURA.DURATA_CHIAMATA / velocita, abs=2e-3)
            assert seguente.t == pytest.approx(max(punto.t + pausa, fermo), abs=2e-3)
            attese += fermo > punto.t + pausa + 2e-3
            recupero = next((e for e in eventi[j:] if e.tipo == E.RECUPERO), None)
            if recupero is not None:
                recuperi += 1
                assert recupero.t >= fermo - 1e-3
    assert visti >= 50 and recuperi >= 40
    if velocita <= 4.0:
        assert attese == 0
    else:
        assert attese >= 0.8 * visti


def test_le_invarianti_vedono_il_recupero_addosso_alla_pallina_che_rotola():
    andata = _volo(1, 1.0, [Tappa(1.0, 60.0, 30.0, 600.0, "partenza"), Tappa(1.25, 62.0, 181.0, 590.0, "schermo")])
    fermo = 1.25 + 100.0 / FRENATA_DEL_RITORNO
    ritorno = _volo(2, 1.25, [Tappa(1.25, 62.0, 181.0, 100.0, "partenza"), Tappa(fermo, 63.0, 98.0, 0.0, "fermo")], dati={"ritorno": True})
    punto = Evento(n=5, t=1.75, tipo=E.PUNTO, fase=E.GIOCO, punti=1, a_chi="B", esito="fallo", causa="schermo_contro")
    recupero = Evento(n=6, t=2.4, tipo=E.RECUPERO, fase=E.GIOCO, durata=0.3, dati={"da": "tavolo"})
    sequenza = [andata, ritorno, _fallo(3, 1.25, (62.0, 181.0)), _fischio(4, 1.25), punto]
    assert any("prima che si fermi la pallina tornata dallo schermo" in p for p in controlla_invarianti([*sequenza, recupero]))
    assert controlla_invarianti([*sequenza, dataclasses.replace(recupero, t=round(fermo, 3))]) == []
    # Il punto si assegna mentre la pallina rotola ancora: va bene.
    assert controlla_invarianti(sequenza) == []


@pytest.mark.parametrize("composta", [1.0, 6.0])
def test_nella_partita_dal_vivo_nessuna_piega_cade_dentro_il_ritorno(composta):
    """
    Dalle verifiche: se chi ascolta alza la velocità a punto già composto, la procedura si ripiega, ma
    mai dentro il volo della pallina. Ripiegato a velocità 8, il ritorno dura nel buffer il suo tempo
    reale, e il primo suono del segmento che segue, che parte dalla fine di quello di prima come fino a
    fine set, arriva quando la pallina è ferma. Composto a 1 il ritorno finisce prima del punto, sotto
    la chiamata; composto a 6 corre oltre il punto, nella pausa che sta nel segmento dopo.
    """
    adesso = 8.0
    casi = oltre_il_punto = 0
    rng = random.Random(3)
    for seme in range(14):
        a, b = giocatore(1, valore=rng.uniform(8, 30)), giocatore(2, valore=rng.uniform(8, 30))
        cronologia = ps.Cronologia(Incontro(a, b, SINGOLARE_3, seme=seme, dettaglio=COMPLETO, velocita=composta))
        segmenti = []
        while (segmento := cronologia.prossimo(composta)) is not None:
            segmenti.append(segmento)
        for prima, dopo in itertools.pairwise(segmenti):
            for ritorno in [e for e in prima.eventi if _e_ritorno(e)]:
                urto, fermo = ritorno.t, ritorno.volo[-1].t
                assert ps.secondi_del_buffer(fermo, urto, prima.pieghe(adesso)) == pytest.approx(fermo - urto, abs=1e-9)
                resta = (fermo - urto) - ps.secondi_del_buffer(prima.fine, urto, prima.pieghe(adesso))
                if not dopo.udibili:
                    continue
                casi += 1
                oltre_il_punto += fermo > prima.fine + 1e-3
                assert ps.secondi_del_buffer(dopo.udibili[0].t, prima.fine, dopo.pieghe(adesso)) >= resta - 1e-3
    assert casi >= 20
    if composta > 4.0:
        assert oltre_il_punto >= 0.5 * casi
    else:
        assert oltre_il_punto == 0


def test_tolto_il_ritorno_la_scena_e_quella_di_prima(partite, partite_senza_ritorno):
    spostati = 0
    for (dopo, _n), (prima, _m) in zip(partite, partite_senza_ritorno, strict=True):
        assert _risultato_in_json(dopo) == _risultato_in_json(prima)
        # L'orologio resta all'urto: l'incontro dura uguale, fino all'ultima cifra.
        assert dopo.durata_simulata == prima.durata_simulata
        senza = [ev for ev in dopo.eventi if not _e_ritorno(ev)]
        assert len(senza) == len(prima.eventi)
        # Per ogni schermo contro, in ordine: dove la pallina si ferma, e dove ha urtato lo schermo.
        attesi = [((round(r.volo[-1].x, 1), round(r.volo[-1].y, 1)), f.pos) for _a, r, f, _i in _schermi(dopo)]
        in_attesa = None
        for ed, ep in zip(senza, prima.eventi, strict=True):
            if ed.tipo == E.FALLO and ed.causa == "schermo_contro":
                in_attesa = attesi.pop(0)
            elif ed.tipo == E.RECUPERO and in_attesa is not None:
                # Il recupero dopo uno schermo contro parte da dove la pallina si è fermata; prima partiva dallo schermo.
                fermo, urto = in_attesa
                assert ed.pos == fermo and ep.pos == urto
                ed = dataclasses.replace(ed, pos=ep.pos, lato=ep.lato, distanza=ep.distanza)
                spostati += 1
            if ed.tipo in (E.RECUPERO, E.CONSEGNA):
                in_attesa = None
            assert dataclasses.replace(ed, n=ep.n) == ep, (ed.n, ed.tipo)
        assert attesi == []
    assert spostati >= 40


def test_esiti_uguali_alla_modalita_essenziale(partite):
    for (completa, _n), (essenziale, _m) in zip(partite, _partite(ESSENZIALE), strict=True):
        assert _risultato_in_json(completa) == _risultato_in_json(essenziale)


# Le invarianti.

def _volo(n, t, tappe, chi=1, parte="A", **campi):
    fine = tappe[-1]
    return Evento(n=n, t=t, tipo=E.VOLO, fase=E.GIOCO, durata=round(fine.t - tappe[0].t, 3), chi=chi, parte=parte, pos=(fine.x, fine.y),
                  lato=lato_di(fine.x, parte), distanza=round(distanza_di(fine.y, parte), 1), volo=tuple(tappe), **campi)


def _fallo(n, t, pos):
    return Evento(n=n, t=t, tipo=E.FALLO, fase=E.GIOCO, chi=1, parte="A", pos=pos, lato=lato_di(pos[0], "A"), distanza=pos[1], causa="schermo_contro",
                  chiamata="schermo_centrale", fischio=E.SINGOLO, punti=1, a_chi="B")


def _fischio(n, t):
    return Evento(n=n, t=t, tipo=E.FISCHIO, fase=E.GIOCO, fischio=E.SINGOLO)


def test_le_invarianti_vedono_uno_schermo_senza_ritorno_e_un_ritorno_sbagliato():
    andata = _volo(1, 1.0, [Tappa(1.0, 60.0, 30.0, 600.0, "partenza"), Tappa(1.25, 62.0, 181.0, 590.0, "schermo")])
    ritorno = _volo(2, 1.25, [Tappa(1.25, 62.0, 181.0, 100.0, "partenza"), Tappa(1.25 + 100.0 / FRENATA_DEL_RITORNO, 63.0, 98.0, 0.0, "fermo")],
                    dati={"ritorno": True})
    fallo, fischio = _fallo(3, 1.25, (62.0, 181.0)), _fischio(4, 1.25)
    assert controlla_invarianti([andata, ritorno, fallo, fischio]) == []
    # Lo schermo senza ritorno.
    assert any("non torna indietro" in p for p in controlla_invarianti([andata, dataclasses.replace(fallo, n=2), dataclasses.replace(fischio, n=3)]))
    # Il ritorno che non parte dall'urto, o che va avanti oltre lo schermo.
    spostato = dataclasses.replace(ritorno, volo=(ritorno.volo[0]._replace(y=170.0), ritorno.volo[1]))
    assert any("non comincia dall'urto" in p for p in controlla_invarianti([andata, spostato, fallo, fischio]))
    avanti = _volo(2, 1.25, [Tappa(1.25, 62.0, 181.0, 100.0, "partenza"), Tappa(2.0, 63.0, 181.5, 0.0, "fermo")], dati={"ritorno": True})
    assert any("non torna indietro fino a fermarsi" in p for p in controlla_invarianti([andata, avanti, fallo, fischio]))
    # Il fallo segnato dove la pallina si ferma, invece che allo schermo.
    assert any("il fallo non resta allo schermo" in p for p in controlla_invarianti([andata, ritorno, _fallo(3, 1.25, (63.0, 98.0)), fischio]))


# Il suono.

def _energia(stereo):
    return float(np.sum(stereo.astype(np.float64) ** 2))


def test_il_ritorno_si_sente_dall_urto_anche_dopo_il_cicalino(partite, monkeypatch):
    vieta_la_cassa_vera(monkeypatch)
    cicalino = ps.ritardo_dell_esito("fallo") + ps.durata_della_sorgente("fallo")
    provati = dopo_il_cicalino = 0
    for risultato, _nomi in partite[:8]:
        eventi = risultato.eventi
        for andata, ritorno, fallo, indice in _schermi(risultato):
            urto, fermo = andata.volo[-1], ritorno.volo[-1]
            con = eventi[indice - 2:indice + 3]
            assert [e.tipo for e in con] == [E.VOLO, E.VOLO, E.FALLO, E.FISCHIO, E.CHIAMATA]
            senza = [e for e in con if e is not ritorno]
            for ascoltatore in ("A", "B"):
                composto = ps.componi(con, ascoltatore, da=andata.t, fine=fallo.t + 3.0)
                ruoli = [p.ruolo for p in composto.posati]
                # Lo schermo suona una volta sola, all'urto; il fischio all'urto, il cicalino dopo di lui.
                assert ruoli.count("schermo") == 1 and ruoli.count("rotolamento") == 2 and ruoli.count("fischio_singolo") == 1
                (schermo,) = [p for p in composto.posati if p.ruolo == "schermo"]
                (fischio,) = [p for p in composto.posati if p.ruolo == "fischio_singolo"]
                (cicala,) = [p for p in composto.posati if p.ruolo == "fallo"]
                assert schermo.t == urto.t and fischio.t == fallo.t and cicala.t == pytest.approx(fallo.t + ps.ritardo_dell_esito("fallo"))
                # Il ritorno rotola dall'urto, dallo schermo a dove la pallina si ferma.
                (rotola,) = [p for p in composto.posati if p.ruolo == "rotolamento" and p.t == pytest.approx(urto.t, abs=1e-9)]
                assert rotola.posizioni[0] == pytest.approx((urto.x, urto.y)) and rotola.posizioni[-1] == pytest.approx((fermo.x, fermo.y), abs=0.5)
                # Tolto il ritorno, il buffer è quello di prima fino all'urto, e la differenza è il ritorno.
                prima = ps.componi(senza, ascoltatore, da=andata.t, fine=fallo.t + 3.0)
                n = min(len(composto.buffer), len(prima.buffer))
                differenza = composto.buffer[:n] - prima.buffer[:n]
                inizio = round(composto.secondi(rotola.t) * ps.FS)
                assert not np.any(np.abs(differenza[:max(0, inizio - 3)]) > 1e-7)
                atteso = ps.spazializza(rotola, ascoltatore)
                assert np.allclose(differenza[inizio:inizio + len(atteso)], atteso[:n - inizio], atol=1e-6)
                provati += 1
                dopo_il_cicalino += _energia(atteso[round(cicalino * ps.FS):]) > 0
    assert provati >= 20
    # Quasi sempre il ritorno si sente ancora quando il cicalino è finito.
    assert dopo_il_cicalino >= 0.6 * provati
