"""
Test della issue 12, decisione D37 del 24 ottobre 2026: nello schermo contro la pallina batte sullo
schermo e torna indietro, e la cronaca lo dice con le parole di Gabriele. Il ritorno della pallina
nella partita dal vivo, un volo breve dopo l'urto, se n'è andato lo stesso giorno, dopo l'ascolto alla
cieca in cui Gabriele non l'ha mai distinto dallo schermo di prima: lo schermo contro è quello di
prima. Dopo il volo che urta lo schermo vengono subito il fallo, segnato allo schermo nell'istante
dell'urto, e il fischio, nello stesso istante; nessun volo fino al recupero dell'arbitro, che parte
dallo schermo, e quello che segue il punto non aspetta più la pallina, a nessuna velocità di gioco.
Le invarianti vedono il fallo che non resta allo schermo. Nel buffer composto senza suonarlo la
pallina rotola fino allo schermo e lì si ferma, lo schermo suona una volta sola, all'urto, e dopo di
lui soltanto il fischio e il cicalino del fallo. Gli esiti sono quelli della modalità essenziale con
gli stessi semi: l'impronta del motore la guarda tests/test_identita_motore.py.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import random

import pytest
from aiuti_dal_vivo import vieta_la_cassa_vera
from aiuti_motore import giocatore
from test_identita_motore import _risultato_in_json

import partita_sonora as ps
from motore import cronaca as C
from motore import eventi as E
from motore.eventi import CAUSE, Evento, Tappa
from motore.incontro import COMPLETO, ESSENZIALE, SINGOLARE_3, SQUADRE, simula_incontro
from motore.regia import controlla_invarianti
from motore.squadre import Squadra
from motore.taratura import TARATURA
from motore.tavolo import distanza_di, lato_di

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


@pytest.fixture(scope="module")
def partite():
    return _partite(COMPLETO)


def _schermi(risultato):
    """Gli schermi contro dell'incontro: il volo fino all'urto, il fallo e l'indice del fallo."""
    eventi = risultato.eventi
    for indice, ev in enumerate(eventi):
        if ev.tipo == E.FALLO and ev.causa == "schermo_contro":
            yield eventi[indice - 1], ev, indice


# La cronaca.

def test_la_cronaca_dice_che_la_pallina_batte_sullo_schermo_e_torna_indietro():
    assert CAUSE["schermo_contro"].frase == "la pallina di {chi} batte sullo schermo e torna indietro"
    assert CAUSE["schermo_sopra"].frase == "la pallina di {chi} passa sopra lo schermo"
    nomi = {1: C.Nome("Rossi", "m")}
    fallo = Evento(n=9, t=4.0, tipo=E.FALLO, fase=E.GIOCO, chi=1, parte="A", pos=(61.0, 181.0), lato="centro", causa="schermo_contro",
                   chiamata="schermo_centrale", fischio=E.SINGOLO, punti=1, a_chi="B")
    assert C.frase(fallo, nomi) == "Fischio: schermo centrale, la pallina di Rossi batte sullo schermo e torna indietro."
    assert C.frase(fallo, nomi, C.SINTETICA) is None


def test_la_cronaca_degli_incontri_dice_la_frase(partite):
    visti = 0
    for risultato, nomi in partite:
        schermi = list(_schermi(risultato))
        for _andata, fallo, _indice in schermi:
            assert C.frase(fallo, nomi) == f"Fischio: schermo centrale, la pallina di {nomi[fallo.chi].testo} batte sullo schermo e torna indietro."
        righe = C.componi(risultato.momenti, nomi)
        assert sum("batte sullo schermo e torna indietro" in riga for riga in righe) == len(schermi)
        assert not any("urta lo schermo" in riga for riga in righe)
        visti += len(schermi)
    assert visti >= 50


# La scena.

def test_lo_schermo_contro_e_quello_di_prima(partite):
    visti = recuperi = 0
    for risultato, _nomi in partite:
        eventi = risultato.eventi
        assert controlla_invarianti(eventi) == []
        # Nessun volo porta indietro la pallina: il ritorno non c'è più.
        assert not any("ritorno" in (ev.dati or {}) for ev in eventi if ev.tipo == E.VOLO)
        for andata, fallo, indice in _schermi(risultato):
            visti += 1
            urto = andata.volo[-1]
            assert andata.tipo == E.VOLO and urto.tipo == "schermo" and andata.chi == fallo.chi
            # Il fallo resta allo schermo, nell'istante dell'urto, e il fischio arriva lì, appena la pallina tocca.
            assert fallo.pos == (round(urto.x, 1), round(urto.y, 1)) and fallo.t == pytest.approx(urto.t, abs=2e-3)
            fischio = eventi[indice + 1]
            assert fischio.tipo == E.FISCHIO and fischio.fischio == E.SINGOLO and fischio.t == fallo.t
            # Finché l'arbitro non la riprende la pallina resta allo schermo: nessun volo, e il recupero parte da lì.
            ripresa = next((k for k in range(indice, len(eventi)) if eventi[k].tipo in (E.RECUPERO, E.CONSEGNA)), len(eventi))
            assert not any(e.volo for e in eventi[indice:ripresa])
            if ripresa < len(eventi) and eventi[ripresa].tipo == E.RECUPERO:
                recuperi += 1
                assert eventi[ripresa].pos == fallo.pos and eventi[ripresa].dati == {"da": "tavolo"}
    assert visti >= 50 and recuperi >= 40


@pytest.mark.parametrize("velocita", [4.0, 8.0])
def test_quello_che_segue_il_punto_non_aspetta_piu_la_pallina(velocita):
    """
    Il punto si assegna dopo il fischio e la chiamata, e quello che segue arriva alla fine della pausa
    fra i punti, alla velocità predefinita e alla più alta: senza il ritorno non c'è più una pallina
    che rotola da aspettare.
    """
    pausa = TARATURA.PAUSA_FRA_PUNTI / velocita
    visti = 0
    for risultato, _nomi in _partite(COMPLETO, velocita):
        eventi = risultato.eventi
        assert controlla_invarianti(eventi) == []
        for _andata, fallo, indice in _schermi(risultato):
            j = next(k for k in range(indice, len(eventi)) if eventi[k].tipo == E.PUNTO)
            if j + 1 == len(eventi):
                continue
            visti += 1
            punto, seguente = eventi[j], eventi[j + 1]
            chiamata = max(TARATURA.FISCHIO_SINGOLO, TARATURA.RITARDO_CHIAMATA / velocita) + TARATURA.DURATA_CHIAMATA / velocita
            assert punto.t == pytest.approx(fallo.t + chiamata, abs=2e-3)
            assert seguente.t == pytest.approx(punto.t + pausa, abs=2e-3)
    assert visti >= 50


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


def test_le_invarianti_vedono_il_fallo_che_non_resta_allo_schermo():
    andata = _volo(1, 1.0, [Tappa(1.0, 60.0, 30.0, 600.0, "partenza"), Tappa(1.25, 62.0, 181.0, 590.0, "schermo")])
    assert controlla_invarianti([andata, _fallo(2, 1.25, (62.0, 181.0)), _fischio(3, 1.25)]) == []
    # Il fallo segnato lontano dallo schermo, o dopo l'urto.
    assert any("il fallo non resta allo schermo" in p for p in controlla_invarianti([andata, _fallo(2, 1.25, (63.0, 98.0)), _fischio(3, 1.25)]))
    assert any("il fallo non resta allo schermo" in p for p in controlla_invarianti([andata, _fallo(2, 1.4, (62.0, 181.0)), _fischio(3, 1.4)]))
    # Un volo fra l'urto e il fallo, come quello del ritorno che non c'è più.
    ritorno = _volo(2, 1.25, [Tappa(1.25, 62.0, 181.0, 100.0, "partenza"), Tappa(2.9, 63.0, 98.0, 0.0, "fermo")])
    sequenza = [andata, ritorno, _fallo(3, 1.25, (62.0, 181.0)), _fischio(4, 1.25)]
    assert any("il fallo non resta allo schermo" in p for p in controlla_invarianti(sequenza))


# Il suono.

def test_lo_schermo_contro_suona_come_prima(partite, monkeypatch):
    """
    Nel buffer composto senza suonarlo, per chi ascolta da tutte e due le testate: la pallina rotola
    fino allo schermo e lì si ferma, lo schermo suona una volta sola, all'urto, col fischio nello
    stesso istante, e poi c'è soltanto il cicalino del fallo; nessun rotolamento riparte dallo schermo.
    """
    vieta_la_cassa_vera(monkeypatch)
    provati = 0
    for risultato, _nomi in partite[:8]:
        eventi = risultato.eventi
        for andata, fallo, indice in _schermi(risultato):
            urto = andata.volo[-1]
            con = eventi[indice - 1:indice + 3]
            assert [e.tipo for e in con] == [E.VOLO, E.FALLO, E.FISCHIO, E.CHIAMATA]
            for ascoltatore in ("A", "B"):
                composto = ps.componi(con, ascoltatore, da=andata.t, fine=fallo.t + 3.0)
                assert sorted(p.ruolo for p in composto.posati) == ["fallo", "fischio_singolo", "rotolamento", "schermo"]
                posati = {p.ruolo: p for p in composto.posati}
                rotola, schermo, fischio, cicala = posati["rotolamento"], posati["schermo"], posati["fischio_singolo"], posati["fallo"]
                # La pallina rotola dalla partenza del colpo fino allo schermo, e lì si ferma.
                partenza = andata.volo[0]
                assert rotola.t == pytest.approx(partenza.t, abs=1e-9) and rotola.posizioni[0] == pytest.approx((partenza.x, partenza.y))
                # I punti di controllo del rotolamento vanno a passi di PASSO: l'ultimo è il primo che arriva all'urto.
                assert rotola.posizioni[-1] == pytest.approx((urto.x, urto.y)) and 0.0 <= float(rotola.tempi[-1]) - (urto.t - partenza.t) < ps.PASSO + 1e-9
                # Lo schermo all'urto, sul punto dell'urto; il fischio nello stesso istante, il cicalino dopo di lui.
                assert schermo.t == pytest.approx(urto.t, abs=1e-9) and schermo.posizioni[0] == pytest.approx((urto.x, urto.y))
                assert fischio.t == fallo.t == pytest.approx(urto.t, abs=2e-3)
                assert cicala.t == pytest.approx(fallo.t + ps.ritardo_dell_esito("fallo"))
                provati += 1
    assert provati >= 20
