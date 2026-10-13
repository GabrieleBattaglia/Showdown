"""
Test del motore dei tornei della tappa 12, tornei.py, punto 4.14 del progetto: le sedi e i gironi a
serpentina, i compagni separati quando si può, il metodo del cerchio, gli spareggi del girone con
casi costruiti a mano, il tabellone classico con i riposi alle prime teste, i compagni di girone
separati al primo turno, la finalina senza sconfitti che rientrano, la classifica finale, la
struttura adattata e i giorni di gioco, i premi e le loro conversioni, il salvataggio a metà
torneo e lo stesso seme che dà lo stesso torneo.
"""

import json
import random

import pytest

import formule
import modelli_torneo
import tornei
from modelli_torneo import ModelloTorneo


@pytest.fixture(autouse=True)
def formule_pulite():
    formule.azzera_cache()
    yield
    formule.azzera_cache()


def _modello(**campi):
    return ModelloTorneo(id="modello_1", nome="Torneo di prova").a_dizionario() | campi


def _info(quanti, club=None, primo=1):
    """Gli iscritti da primo in su, con la forza che scende col numero: 1 è il più forte."""
    return {gid: {"nome": f"Giocatore {gid}", "sesso": "m", "club": club(gid) if club else None, "forza": 1000.0 - gid, "pagato": 10}
            for gid in range(primo, primo + quanti)}


def _torneo(quanti, formula="gironi_32", seme=7, club=None, **campi):
    return tornei.Torneo(1, 1, 1, _modello(**campi), formule.formula(formula), "2030-03-02", seme, _info(quanti, club))


def _set_vinti(incontro, vince_a, punti_perdente=5):
    necessari = incontro.set_al_meglio // 2 + 1
    if incontro.set_al_meglio == tornei.SET_SQUADRE:
        return [[31, 20]] if vince_a else [[20, 31]]
    return [[11, punti_perdente] if vince_a else [punti_perdente, 11] for _ in range(necessari)]


def gioca_per_forza(torneo):
    """Vince sempre il più forte, due a zero."""
    def gioca(incontro, _azioni):
        vince_a = torneo.forza(incontro.a) > torneo.forza(incontro.b)
        return {"esito": "regolare", "vince": "A" if vince_a else "B", "set": _set_vinti(incontro, vince_a), "set_giocati": incontro.set_al_meglio // 2 + 1}
    return gioca


def gioca_dal_seme(incontro, _azioni):
    """Un risultato a caso, ma deciso dal seme dell'incontro: con ritiri, tavolini e qualche tavolino doppio."""
    rng = random.Random(incontro.seme)
    caso = rng.random()
    vince_a = rng.random() < 0.5
    necessari = incontro.set_al_meglio // 2 + 1
    if caso < 0.02:
        return {"esito": "tavolino_doppio", "vince": None, "set": [], "set_giocati": 0}
    if caso < 0.06:
        return {"esito": "tavolino", "vince": "A" if vince_a else "B", "set": _set_vinti(incontro, vince_a, 0), "set_giocati": 0}
    persi = rng.randrange(necessari)
    sets = [[rng.randrange(0, 10), 11] if vince_a else [11, rng.randrange(0, 10)] for _ in range(persi)] + _set_vinti(incontro, vince_a, rng.randrange(0, 10))
    if incontro.set_al_meglio == tornei.SET_SQUADRE:
        sets = _set_vinti(incontro, vince_a)
    if caso < 0.09 and len(sets) > 1:
        return {"esito": "ritiro", "vince": "A" if vince_a else "B", "set": sets, "set_giocati": len(sets) - 1, "azioni": {incontro.a: 40, incontro.b: 40}}
    return {"esito": "regolare", "vince": "A" if vince_a else "B", "set": sets, "set_giocati": len(sets), "azioni": {incontro.a: 60, incontro.b: 60}}


def gioca_tutto(torneo, gioca, inizio=None):
    giorni = 0
    while torneo.stato == tornei.IN_CORSO:
        torneo.giornata(gioca, f"2030-03-{2 + giorni:02d}" if inizio is None else inizio)
        giorni += 1
        assert giorni < 50
    return giorni


# Le sedi e i gironi.

def test_le_sedi_a_serpentina():
    sedi = tornei.dividi_in_sedi(list(range(1, 71)), 32, 4)
    assert [len(s) for s in sedi] == [23, 23, 24]
    assert sedi[0][:4] == [1, 6, 7, 12] and sedi[2][:4] == [3, 4, 9, 10]
    assert tornei.dividi_in_sedi([1, 2, 3], 32, 4) == []
    assert tornei.dividi_in_sedi(list(range(32)), 32, 4) == [list(range(32))]


def test_la_serpentina_anche_con_un_numero_non_multiplo():
    assert tornei.gironi_a_serpentina(list(range(1, 9)), 2, lambda _g: None) == [[1, 4, 5, 8], [2, 3, 6, 7]]
    assert tornei.gironi_a_serpentina(list(range(1, 14)), 3, lambda _g: None) == [[1, 6, 7, 12, 13], [2, 5, 8, 11], [3, 4, 9, 10]]


def test_i_compagni_si_separano_quando_si_puo():
    club = {1: "rossi", 4: "rossi"}
    gironi = tornei.gironi_a_serpentina(list(range(1, 9)), 2, club.get)
    assert gironi == [[1, 3, 5, 8], [2, 4, 6, 7]]
    # Tutti dello stesso club: non si può, e la serpentina resta com'è.
    assert tornei.gironi_a_serpentina(list(range(1, 9)), 2, lambda _g: "rossi") == [[1, 4, 5, 8], [2, 3, 6, 7]]


def test_le_lettere_dei_gironi():
    assert [tornei.lettera_girone(i) for i in (0, 1, 25, 26, 27, 51, 52)] == ["A", "B", "Z", "AA", "AB", "AZ", "BA"]


@pytest.mark.parametrize("quanti", [2, 3, 4, 5, 6, 7, 12])
def test_il_metodo_del_cerchio(quanti):
    ids = list(range(1, quanti + 1))
    turni = tornei.calendario_del_girone(ids)
    assert len(turni) == formule.turni_del_girone(quanti)
    coppie = []
    for turno in turni:
        presenti = [g for coppia in turno for g in coppia if g is not None]
        assert len(presenti) == len(set(presenti))
        riposi = [a for a, b in turno if b is None]
        assert len(riposi) == quanti % 2 and all(a is not None for a, _b in turno)
        coppie.extend(frozenset(c) for c in turno if None not in c)
    assert len(coppie) == len(set(coppie)) == quanti * (quanti - 1) // 2
    if quanti >= 3:
        assert frozenset((1, 2)) in {frozenset(c) for c in turni[-1]}


# Il tabellone.

def test_l_ordine_del_tabellone():
    assert tornei.ordine_tabellone(8) == [1, 8, 4, 5, 2, 7, 3, 6]
    for grandezza in (2, 4, 8, 16, 32, 64):
        ordine = tornei.ordine_tabellone(grandezza)
        assert sorted(ordine) == list(range(1, grandezza + 1))
        assert all(ordine[2 * k] + ordine[2 * k + 1] == grandezza + 1 for k in range(grandezza // 2))
        meta = grandezza // 2
        assert (1 in ordine[:meta]) != (2 in ordine[:meta]) or grandezza == 2
        if grandezza >= 4:
            quarti = [ordine[i:i + grandezza // 4] for i in range(0, grandezza, grandezza // 4)]
            assert all(sum(1 for testa in (1, 2, 3, 4) if testa in quarto) == 1 for quarto in quarti)


def test_i_riposi_toccano_alle_prime_teste_e_non_sono_vittorie():
    torneo = _torneo(5, "tabellone_32")
    primo = torneo.fasi[0].del_turno(1)
    riposi = [i for i in primo if i.esito == tornei.RIPOSO]
    assert sorted(i.a for i in riposi) == [1, 2, 3] and all(i.b is None for i in riposi)
    gioca_tutto(torneo, gioca_per_forza(torneo))
    conti = tornei._statistiche(torneo.incontri(), torneo.iscritti)
    assert conti[1][0] == 2
    assert torneo.fasi_superate()[1] == 3
    assert torneo.classifica_finale[:2] == [1, 2]


def test_i_compagni_di_girone_si_separano_al_primo_turno():
    torneo = _torneo(8)
    gioca_tutto(torneo, gioca_per_forza(torneo))
    gironi, tabellone = torneo.fasi
    assert gironi.gironi == {"A": [1, 4, 5, 8], "B": [2, 3, 6, 7]}
    girone_di = {gid: lettera for lettera, ids in gironi.gironi.items() for gid in ids}
    primo_turno = tabellone.del_turno(1)
    assert all(girone_di[i.a] != girone_di[i.b] for i in primo_turno)
    assert {frozenset((i.a, i.b)) for i in primo_turno} == {frozenset((1, 3)), frozenset((2, 4))}


def test_la_finalina_e_nessuno_sconfitto_rientra():
    torneo = _torneo(32)
    giorni = gioca_tutto(torneo, gioca_per_forza(torneo))
    assert giorni == 2
    tabellone = torneo.fasi[-1]
    ultimo = tabellone.del_turno(tabellone.turni)
    finale = next(i for i in ultimo if not i.finalina)
    finalina = next(i for i in ultimo if i.finalina)
    assert {finale.a, finale.b} == {1, 2} and {finalina.a, finalina.b} == {3, 4}
    assert finale.set_al_meglio == finalina.set_al_meglio == 5
    assert all(i.set_al_meglio == 3 for i in tabellone.incontri if i.turno < tabellone.turni)
    eliminati = set()
    for turno in range(1, tabellone.turni + 1):
        for incontro in tabellone.del_turno(turno):
            if not incontro.finalina:
                assert not {incontro.a, incontro.b} & eliminati
        eliminati |= {torneo.sconfitto(i) for i in tabellone.del_turno(turno) if not i.finalina}
    assert torneo.classifica_finale[:4] == [1, 2, 3, 4]
    assert torneo.medaglie == {"oro": 1, "argento": 2, "bronzo": 3, "legno": 4}


def test_lo_sconfitto_della_finale_e_sempre_secondo():
    torneo = _torneo(4, "tabellone_32")

    def gioca(incontro, _azioni):
        # Nelle semifinali vincono i più deboli a tavolino; la finale la vince il più forte dei due.
        if incontro.turno == 1 and not incontro.finalina:
            return {"esito": "tavolino", "vince": "B", "set": _set_vinti(incontro, False, 0), "set_giocati": 0}
        return gioca_per_forza(torneo)(incontro, None)

    gioca_tutto(torneo, gioca)
    assert torneo.classifica_finale == [3, 4, 1, 2]


def test_il_ritiro_e_il_tavolino_doppio_nel_tabellone():
    torneo = _torneo(2, "tabellone_32")

    def gioca(_incontro, _azioni):
        return {"esito": "tavolino_doppio", "vince": None, "set": [], "set_giocati": 0}

    gioca_tutto(torneo, gioca)
    # Nel tavolino doppio passa la testa di serie più alta.
    assert torneo.classifica_finale == [1, 2]
    assert tornei._statistiche(torneo.incontri(), torneo.iscritti)[1][0] == 0


# Gli spareggi del girone, con casi costruiti a mano.

def _girone_scritto(quanti, risultati):
    """Un girone unico coi risultati scritti: per coppia di iscritti, chi vince, l'esito e i set visti da chi vince."""
    torneo = _torneo(quanti, "girone_unico_8")

    def gioca(incontro, _azioni):
        chiave = frozenset((incontro.a, incontro.b))
        vincitore, esito, sets = risultati[chiave]
        if esito == "tavolino_doppio":
            return {"esito": esito, "vince": None, "set": [], "set_giocati": 0}
        vince_a = vincitore == incontro.a
        visti = [list(s) if vince_a else [s[1], s[0]] for s in sets]
        giocati = 0 if esito == "tavolino" else len(sets) - (1 if esito == "ritiro" else 0)
        return {"esito": esito, "vince": "A" if vince_a else "B", "set": visti, "set_giocati": giocati}

    gioca_tutto(torneo, gioca)
    return torneo


def _r(vincitore, *sets, esito="regolare"):
    return vincitore, esito, [list(s) for s in sets]


def test_fra_tre_a_pari_vittorie_decide_la_differenza_set_fra_loro():
    risultati = {frozenset((1, 2)): _r(1, (11, 5), (9, 11), (11, 7)), frozenset((2, 3)): _r(2, (11, 6), (8, 11), (11, 4)), frozenset((3, 1)): _r(3, (11, 2), (11, 3)),
                 frozenset((1, 4)): _r(1, (11, 0), (11, 0)), frozenset((2, 4)): _r(2, (11, 0), (11, 0)), frozenset((3, 4)): _r(3, (11, 0), (11, 0))}
    assert _girone_scritto(4, risultati).classifica_finale == [3, 2, 1, 4]


def test_quando_ne_restano_due_si_ricomincia_dallo_scontro_diretto():
    risultati = {frozenset((1, 2)): _r(1, (11, 0), (11, 0)), frozenset((2, 3)): _r(2, (11, 4), (11, 5)), frozenset((3, 1)): _r(3, (11, 9), (11, 9)),
                 frozenset((1, 4)): _r(1, (11, 0), (11, 0)), frozenset((2, 4)): _r(2, (11, 0), (11, 0)), frozenset((3, 4)): _r(3, (11, 0), (11, 0))}
    assert _girone_scritto(4, risultati).classifica_finale == [1, 2, 3, 4]
    # Rovesciato lo scontro diretto fra 2 e 3, a parità di tutto il resto passa avanti 3.
    risultati[frozenset((2, 3))] = _r(3, (11, 4), (11, 5))
    risultati[frozenset((3, 1))] = _r(3, (11, 9), (11, 9))
    risultati[frozenset((1, 2))] = _r(1, (11, 0), (11, 0))
    torneo = _girone_scritto(4, risultati)
    assert torneo.classifica_finale[0] == 3


def test_fra_due_a_pari_vittorie_decide_lo_scontro_diretto():
    risultati = {frozenset((1, 2)): _r(2, (11, 9), (11, 9)), frozenset((1, 3)): _r(1, (11, 0), (11, 0)), frozenset((2, 3)): _r(3, (11, 0), (11, 0))}
    # 1 e 2 una vittoria a testa, 3 una: tre a pari. Fra loro una vittoria a testa, set 2 a 2 per tutti; i punti decidono.
    torneo = _girone_scritto(3, risultati)
    assert torneo.classifica_finale == [1, 3, 2]
    # 1 e 2 a due vittorie, 3 e 4 a una: lo scontro diretto vale più dei set e dei punti di tutto il girone.
    risultati = {frozenset((1, 2)): _r(2, (11, 9), (11, 9)), frozenset((1, 3)): _r(1, (11, 0), (11, 0)), frozenset((1, 4)): _r(1, (11, 0), (11, 0)),
                 frozenset((2, 3)): _r(2, (11, 9), (11, 9)), frozenset((2, 4)): _r(4, (11, 0), (11, 0)), frozenset((3, 4)): _r(3, (11, 9), (11, 9))}
    assert _girone_scritto(4, risultati).classifica_finale == [2, 1, 3, 4]


def test_il_tavolino_doppio_e_una_sconfitta_per_tutti_e_due():
    risultati = {frozenset((1, 2)): _r(None, esito="tavolino_doppio"), frozenset((1, 3)): _r(1, (11, 0), (11, 0)), frozenset((2, 3)): _r(2, (11, 0), (11, 0))}
    torneo = _girone_scritto(3, risultati)
    conti = tornei._statistiche(torneo.incontri(), torneo.iscritti)
    assert conti[1][:3] == [1, 2, 0] and conti[2][:3] == [1, 2, 0]
    # Pari in tutto, anche fra loro: decide la forza al sorteggio.
    assert torneo.classifica_finale == [1, 2, 3]


def test_il_ritiro_e_il_tavolino_contano_come_registrati():
    risultati = {frozenset((1, 2)): _r(2, (11, 7), (11, 0), esito="ritiro"), frozenset((1, 3)): _r(3, (11, 0), (11, 0), esito="tavolino"),
                 frozenset((2, 3)): _r(2, (11, 5), (11, 5)), frozenset((1, 4)): _r(1, (11, 1), (11, 1)), frozenset((2, 4)): _r(4, (11, 8), (11, 8)),
                 frozenset((3, 4)): _r(3, (11, 3), (11, 3))}
    torneo = _girone_scritto(4, risultati)
    conti = tornei._statistiche(torneo.incontri(), torneo.iscritti)
    assert conti[2] == [2, 4, 2, 60, 39]
    ritiro = next(i for i in torneo.incontri() if {i.a, i.b} == {1, 2})
    assert ritiro.esito == "ritiro" and ritiro.set_giocati == 1
    # 2 e 3 con due vittorie: fra loro ha vinto 2.
    assert torneo.classifica_finale[:2] == [2, 3]


# La struttura, i giorni e il gioco.

@pytest.mark.parametrize(("formula", "da", "a"), [("gironi_32", 4, 32), ("gironi_64", 33, 64), ("tabellone_32", 2, 32), ("girone_unico_8", 2, 8)])
def test_tornei_interi_da_4_al_tetto(formula, da, a):
    for quanti in range(da, a + 1):
        torneo = _torneo(quanti, formula, seme=quanti, incontri_al_giorno=3)
        giorni = gioca_tutto(torneo, gioca_dal_seme)
        modello = ModelloTorneo.da_dizionario(torneo.modello | {"minimo_iscritti": max(4, quanti) if quanti >= 4 else 4})
        if quanti >= 4:
            assert giorni <= modelli_torneo.durata_prevista(modello, torneo.formula), (formula, quanti)
        assert sorted(torneo.classifica_finale) == sorted(torneo.iscritti)
        for fase in torneo.fasi:
            for turno in range(1, fase.turni + 1):
                presenti = [g for i in fase.del_turno(turno) for g in (i.a, i.b) if g is not None]
                assert len(presenti) == len(set(presenti))
        coppie = [frozenset((i.a, i.b)) for fase in torneo.fasi if fase.tipo == formule.GIRONI for i in fase.incontri if i.b is not None]
        assert len(coppie) == len(set(coppie))


def test_la_giornata_gioca_tanti_turni_e_ogni_fase_comincia_in_un_giorno_nuovo():
    torneo = _torneo(32)
    giocati, finito = torneo.giornata(gioca_per_forza(torneo), "2030-03-02")
    assert len(giocati) == 48 and not finito and torneo.fase_corrente == 1
    giocati, finito = torneo.giornata(gioca_per_forza(torneo), "2030-03-03")
    assert len(giocati) == 16 and finito and torneo.giorni_giocati == 2
    assert torneo.giornata(gioca_per_forza(torneo), "2030-03-04") == ([], True)
    assert all(i.data in ("2030-03-02", "2030-03-03") for i in torneo.incontri() if i.esito != tornei.RIPOSO)


def test_le_azioni_della_giornata_arrivano_all_incontro_seguente():
    torneo = _torneo(4, "girone_unico_8")
    viste = []

    def gioca(incontro, azioni):
        viste.append((incontro.turno, dict(azioni)))
        return gioca_per_forza(torneo)(incontro, azioni) | {"azioni": {incontro.a: 50, incontro.b: 50}}

    torneo.giornata(gioca, "2030-03-02")
    assert all(set(azioni.values()) == {50 * (turno - 1)} for turno, azioni in viste)


def test_un_risultato_incoerente_si_rifiuta():
    torneo = _torneo(4, "girone_unico_8")
    incontro = torneo.fasi[0].incontri[0]
    assert tornei.problema_del_risultato(incontro, {"esito": "pareggio"})
    assert tornei.problema_del_risultato(incontro, {"esito": "regolare", "vince": "A", "set": [[11, 5]], "set_giocati": 1})
    assert tornei.problema_del_risultato(incontro, {"esito": "regolare", "vince": "A", "set": [[11, 5], [5, 11], [5, 11]], "set_giocati": 3})
    assert tornei.problema_del_risultato(incontro, {"esito": "tavolino", "vince": "B", "set": [[0, 11], [0, 11]], "set_giocati": 2})
    assert tornei.problema_del_risultato(incontro, {"esito": "tavolino_doppio", "vince": "A", "set": [], "set_giocati": 0})
    assert tornei.problema_del_risultato(incontro, {"esito": "regolare", "vince": "B", "set": [[5, 11], [5, 11]], "set_giocati": 2}) is None
    with pytest.raises(ValueError, match="esito valido"):
        torneo.giornata(lambda _i, _a: {"esito": "pareggio"}, "2030-03-02")


def test_la_coppa_a_squadre_gioca_un_set():
    info = {f"Club {n:02d}": {"nome": f"Club {n:02d}", "sesso": None, "club": None, "forza": 100.0 - n, "pagato": 0, "rosa": [n * 10 + k for k in range(4)]} for n in range(10)}
    modello = _modello(tipo="squadre", sesso=None, qualificazione="gloria", formula="squadre_64", quota_iscrizione=0, contributo_federazione=0.0, posti_premiati=4)
    torneo = tornei.Torneo(5, 2, 1, modello, formule.formula("squadre_64"), "2030-06-15", 3, info)
    assert all(i.set_al_meglio == tornei.SET_SQUADRE for i in torneo.incontri())
    gioca_tutto(torneo, gioca_per_forza(torneo))
    assert torneo.classifica_finale[:2] == ["Club 00", "Club 01"]
    assert torneo.premi == {}


# I premi.

def test_il_montepremi():
    assert tornei.montepremi(_modello(), 32) == 640
    assert tornei.montepremi(_modello(quota_iscrizione=0, contributo_federazione=0.0, montepremi_minimo=3000), 32) == 3000
    assert tornei.montepremi(_modello(contributo_federazione=0.5), 7) == 105


@pytest.mark.parametrize(("montepremi", "posti", "pendenza", "iscritti"), [(640, 8, 1.385, 32), (3000, 16, 1.466, 32), (100, 8, 1.385, 5), (9999, 30, 3.0, 64), (7, 8, 2.0, 32)])
def test_i_premi_non_superano_il_montepremi_e_scendono(montepremi, posti, pendenza, iscritti):
    premi = tornei.calcola_premi(montepremi, posti, pendenza, iscritti)
    assert sum(premi) <= montepremi
    assert premi == sorted(premi, reverse=True)
    assert len(premi) <= min(posti, iscritti)


def test_le_conversioni_della_percentuale_al_primo():
    assert tornei.prima_percentuale(tornei.pendenza_per_prima(30, 8), 8) == pytest.approx(30, abs=0.1)
    assert tornei.prima_percentuale(tornei.pendenza_per_prima(25, 16), 16) == pytest.approx(25, abs=0.1)
    assert tornei.pendenza_per_prima(5, 16) == 1.0 and tornei.pendenza_per_prima(50, 1) == 1.0
    # Sopra i dieci posti la percentuale mostrata è quella vera: la stessa che danno i premi.
    premi = tornei.calcola_premi(100_000, 16, 1.466)
    assert 100 * premi[0] / 100_000 == pytest.approx(tornei.prima_percentuale(1.466, 16), abs=0.01)


def test_i_premi_vanno_ai_primi_della_classifica():
    torneo = _torneo(32)
    gioca_tutto(torneo, gioca_per_forza(torneo))
    premi = tornei.calcola_premi(640, 8, torneo.modello["pendenza_premi"], 32)
    assert [torneo.premi[gid] for gid in torneo.classifica_finale[:8]] == premi
    assert sum(torneo.premi.values()) <= 640


# Il salvataggio e il seme.

def test_salvato_a_meta_prosegue_uguale():
    torneo = _torneo(29, seme=11)
    torneo.giornata(gioca_dal_seme, "2030-03-02")
    copia = tornei.Torneo.da_dizionario(json.loads(json.dumps(torneo.a_dizionario())))
    assert copia.a_dizionario() == torneo.a_dizionario()
    gioca_tutto(torneo, gioca_dal_seme, "2030-03-03")
    gioca_tutto(copia, gioca_dal_seme, "2030-03-03")
    assert copia.a_dizionario() == torneo.a_dizionario()


def test_lo_stesso_seme_da_lo_stesso_torneo():
    primo, secondo = _torneo(27, seme=5), _torneo(27, seme=5)
    gioca_tutto(primo, gioca_dal_seme)
    gioca_tutto(secondo, gioca_dal_seme)
    assert primo.a_dizionario() == secondo.a_dizionario()
    diverso = _torneo(27, seme=6)
    gioca_tutto(diverso, gioca_dal_seme)
    assert [i.seme for i in diverso.incontri()] != [i.seme for i in primo.incontri()]


def test_un_salvataggio_rovinato_si_rifiuta():
    dati = _torneo(8).a_dizionario()
    with pytest.raises(ValueError, match="campi sbagliati"):
        tornei.Torneo.da_dizionario(dati | {"extra": 1})
    with pytest.raises(ValueError, match="stato"):
        tornei.Torneo.da_dizionario(dati | {"stato": "sospeso"})
    rovinato = json.loads(json.dumps(dati))
    rovinato["fasi"][0]["incontri"][0]["a"] = 99
    with pytest.raises(ValueError, match="non c'è"):
        tornei.Torneo.da_dizionario(rovinato)
