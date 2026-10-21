"""
Test delle fotografie e dei gemelli in differita della tappa 12, punto 6.5 del progetto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Un incontro giocato in modalità essenziale con le basi d'infortunio, i cali e le azioni iniziali, e
il suo gemello ricostruito dalle fotografie, passate per il JSON del salvataggio, danno gli stessi
punti, gli stessi set, lo stesso ritiro e gli stessi acciacchi, anche con un braccio cambiato
dall'ambidestro e con un acciaccato; lo stesso per la gara a squadre. Le fotografie restano quelle
del giorno, anche se dopo il giocatore cambia.
"""

import json
import random

from aiuti_motore import giocatore

from motore import ESSENZIALE, SINGOLARE_3, SINGOLARE_5, SQUADRE, Incontro, Squadra
from partita import differita_singolare, differita_squadre, fotografa, gemello_da_differita, gemello_in_differita


def _per_json(dati):
    return json.loads(json.dumps(dati))


def _uguali(a, b):
    assert a.punti == b.punti and a.set == b.set and a.set_giocati == b.set_giocati
    assert a.infortuni == [tuple(i) for i in b.infortuni] and a.acciacchi == b.acciacchi and a.ritirato == b.ritirato and a.esito == b.esito


def test_il_gemello_in_differita_ripete_l_incontro():
    visti = set()
    for seme in range(1, 160):
        ga = giocatore(1, valore=14.0, ambidestro=seme % 2 == 0, anni=50)
        gb = giocatore(2, valore=13.0, anni=55, acciacco_sede="ginocchio")
        basi = {1: 300.0, 2: 300.0}
        cali = {2: 0.02}
        iniziali = {1: 30, 2: 10}
        differita = _per_json(differita_singolare(ga, gb, basi, cali, iniziali, 3))
        vero = Incontro(ga, gb, SINGOLARE_3, seme=seme, dettaglio=ESSENZIALE, basi_infortunio=basi, cali=cali, azioni_iniziali=iniziali).gioca()
        # Dopo l'incontro il giocatore vero cambia: il gemello gioca con la fotografia.
        ga.difesa_allenata += 5.0
        ga.esperienza += 3.0
        gemello = gemello_da_differita(differita, seme).gioca()
        _uguali(gemello, vero)
        if vero.esito == "ritiro":
            visti.add("ritiro")
        if any(g == 1 for g, _s, _sede in vero.infortuni) and ga.ambidestro and vero.esito != "ritiro":
            visti.add("braccio")
        if vero.acciacchi:
            visti.add("acciacco")
        if visti == {"ritiro", "braccio", "acciacco"}:
            break
    assert visti >= {"ritiro", "acciacco"}


def test_il_gemello_di_un_incontro_del_torneo():
    class IncontroDelTorneo:
        pass

    ga, gb = giocatore(1), giocatore(2, sesso="f")
    incontro = IncontroDelTorneo()
    incontro.seme = 77
    incontro.differita = differita_singolare(ga, gb, {1: 2.0, 2: 2.0}, None, None, 5)
    vero = Incontro(ga, gb, SINGOLARE_5, seme=77, dettaglio=ESSENZIALE, basi_infortunio={1: 2.0, 2: 2.0}).gioca()
    gemello = gemello_in_differita(incontro)
    assert gemello.formato.set_al_meglio == 5 and gemello.completo
    _uguali(gemello.gioca(), vero)
    incontro.differita = None
    try:
        gemello_in_differita(incontro)
    except ValueError as e:
        assert "non si può riascoltare" in str(e)
    else:
        raise AssertionError("Senza differita il gemello non nasce.")


def test_il_gemello_della_gara_a_squadre():
    uomini = [giocatore(n, valore=10.0 + n) for n in range(1, 6)]
    donne = [giocatore(n, valore=8.0 + n, sesso="f") for n in range(6, 11)]
    a = Squadra("Leoni", (uomini[0], uomini[1], donne[0], donne[1]))
    b = Squadra("Tigri", (uomini[2], donne[2], donne[3], uomini[3]))
    basi = {g.id: 5.0 for g in (*a.giocatori, *b.giocatori)}
    cali = {uomini[0].id: 0.03}
    for seme in (3, 9, 21):
        vero = Incontro(a, b, SQUADRE, seme=seme, dettaglio=ESSENZIALE, basi_infortunio=basi, cali=cali).gioca()
        differita = _per_json(differita_squadre(a, b, basi, cali))
        gemello = gemello_da_differita(differita, seme)
        assert [g.id for g in gemello.parti["A"].giocatori] == [g.id for g in a.giocatori]
        _uguali(gemello.gioca(), vero)
        # Una differita registrata prima della fatica della giornata nelle gare a squadre non ha le azioni iniziali.
        del differita["azioni_iniziali"]
        _uguali(gemello_da_differita(differita, seme).gioca(), vero)
    # La lettura 12 delle decisioni di Gabriele del 14 ottobre 2026: la differita porta le azioni iniziali
    # della fatica della giornata, e il gemello ripete l'incontro stanco.
    iniziali = {uomini[0].id: 90, donne[2].id: 40}
    for seme in (4, 10):
        vero = Incontro(a, b, SQUADRE, seme=seme, dettaglio=ESSENZIALE, basi_infortunio=basi, cali=cali, azioni_iniziali=iniziali).gioca()
        differita = _per_json(differita_squadre(a, b, basi, cali, iniziali))
        assert differita["azioni_iniziali"] == [[90, 0, 0, 0], [0, 40, 0, 0]]
        _uguali(gemello_da_differita(differita, seme).gioca(), vero)


def test_la_fotografia_ha_soltanto_quello_che_serve():
    g = giocatore(5)
    foto = fotografa(g)
    assert foto["id"] == 5 and "diario" not in foto and "contratto_stipendio" not in foto
    assert len(json.dumps(foto)) < 2000
    assert random.Random(1).random() == random.Random(1).random()
