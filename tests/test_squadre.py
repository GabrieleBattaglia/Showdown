"""
Test della gara a squadre: composizione, rotazione fissa, tre servizi, set a 31 con 2 di scarto,
cambio campo a 16, anche dopo una penalità, un time-out e una sostituzione per squadra, chi esce
non rientra e chi entra vale più di chi esce; le ammonizioni che valgono per tutta la squadra, il
sorteggio con la lettura delle formazioni e gli avvisi del riscaldamento.
"""

import itertools

import pytest
from aiuti_motore import giocatore

from motore import cronaca as C
from motore.incontro import COMPLETO, ESSENZIALE, SQUADRE, Incontro, simula_incontro
from motore.regia import controlla_invarianti
from motore.squadre import Squadra, composizione_valida, ordine_di_battuta, problema_squadra


def _squadra(nome, primo_id, sessi="mmf", valori=None, **altro):
    valori = valori or [15.0] * len(sessi)
    return Squadra(nome, tuple(giocatore(primo_id + i, valore=v, sesso=s, **altro) for i, (s, v) in enumerate(zip(sessi, valori, strict=True))))


def test_composizione_della_squadra():
    assert problema_squadra(_squadra("Leoni", 1)) is None
    assert problema_squadra(_squadra("Leoni", 1, "ffmmff")) is None
    assert "da 3 a 6" in problema_squadra(_squadra("Leoni", 1, "mf"))
    assert "da 3 a 6" in problema_squadra(_squadra("Leoni", 1, "mmfmmff"))
    assert "due giocatori di un sesso" in problema_squadra(_squadra("Leoni", 1, "mmmf"))
    doppione = _squadra("Leoni", 1)
    assert "due volte" in problema_squadra(Squadra("Leoni", (*doppione.giocatori, doppione.giocatori[0])))
    fermo = _squadra("Leoni", 1)
    fermo.giocatori[1].infortunato = True
    fermo.giocatori[1].infortunio_sede = "caviglia"
    assert "non può giocare" in problema_squadra(fermo)
    with pytest.raises(ValueError, match="comune"):
        Incontro(_squadra("Leoni", 1), _squadra("Tigri", 3), SQUADRE)


def test_ordine_di_battuta():
    assert ordine_di_battuta("A") == (("A", 0), ("B", 0), ("A", 1), ("B", 1), ("A", 2), ("B", 2))
    assert ordine_di_battuta("B") == (("B", 0), ("A", 0), ("B", 1), ("A", 1), ("B", 2), ("A", 2))


def _turni(risultato):
    """Le coppie di chi batte e chi riceve, nell'ordine, con quanti servizi assegnati ciascuna."""
    turni = []
    for punto in risultato.punti:
        coppia = (punto.battitore, punto.ricevitore)
        if not turni or turni[-1][0] != coppia:
            turni.append([coppia, 0])
        if punto.punti:
            turni[-1][1] += 1
    return turni


def test_rotazione_e_tre_servizi():
    a, b = _squadra("Leoni", 1), _squadra("Tigri", 11, "ffm")
    visti_b = False
    for seme in range(6):
        risultato = simula_incontro(a, b, SQUADRE, seme=seme, dettaglio=ESSENZIALE)
        ordine = ordine_di_battuta(risultato.sorteggio["batte"])
        ids = {"A": [g.id for g in a.giocatori], "B": [g.id for g in b.giocatori]}
        sequenza = [ids[parte][posto] for parte, posto in ordine]
        attese = [(sequenza[i % 6], sequenza[(i + 1) % 6]) for i in range(40)]
        turni = _turni(risultato)
        assert [coppia for coppia, _n in turni] == attese[:len(turni)]
        assert all(n == 3 for _coppia, n in turni[:-1])
        assert max(p.numero_servizio for p in risultato.punti) == 3
        visti_b |= risultato.sorteggio["batte"] == "B"
        assert turni[0][0] == (sequenza[0], sequenza[1])
    assert visti_b


def test_un_set_a_31_e_il_cambio_campo_a_16():
    a, b = _squadra("Leoni", 1), _squadra("Tigri", 11, "ffm")
    for seme in range(10):
        risultato = simula_incontro(a, b, SQUADRE, seme=seme, dettaglio=ESSENZIALE)
        assert len(risultato.set) == 1
        x, y = risultato.set[0]
        assert max(x, y) >= 31 and abs(x - y) >= 2
        cambi = risultato.incontro.cambi_campo
        assert len(cambi) == 1 and cambi[0][0] == 1 and max(cambi[0][1]) >= 16
        prima = [p.punteggio for p in risultato.punti]
        indice = next(i for i, punteggio in enumerate(prima) if max(punteggio) >= 16)
        assert indice == 0 or max(prima[indice - 1]) < 16


def test_time_out_e_sostituzione_una_per_squadra():
    sostituzioni = timeout = 0
    for seme in range(40):
        a = _squadra("Leoni", 1, "mmfmmf", valori=[6.0, 6.0, 6.0, 35.0, 35.0, 35.0], anni=60)
        b = _squadra("Tigri", 11, "ffmffm", valori=[30.0, 30.0, 30.0, 10.0, 10.0, 10.0])
        incontro = Incontro(a, b, SQUADRE, seme=seme, dettaglio=COMPLETO if seme < 5 else ESSENZIALE)
        risultato = incontro.gioca()
        if risultato.eventi:
            assert controlla_invarianti(risultato.eventi) == []
        per_parte = {"A": 0, "B": 0}
        for _set_n, punto_n, parte, esce, entra in risultato.incontro.sostituzioni:
            per_parte[parte] += 1
            dopo = risultato.punti[punto_n:]
            assert all(esce not in (p.battitore, p.ricevitore) for p in dopo)
            assert any(entra in (p.battitore, p.ricevitore) for p in dopo) or not dopo
        assert max(per_parte.values()) <= 1
        assert max(sum(1 for _s, _p, parte in risultato.incontro.timeout if parte == quale) for quale in "AB") <= 1
        for parte, squadra in (("A", a), ("B", b)):
            al_tavolo = [next(g for g in squadra.giocatori if g.id == gid) for gid in incontro.formazione[parte]]
            assert composizione_valida(al_tavolo)
        sostituzioni += len(risultato.incontro.sostituzioni)
        timeout += len(risultato.incontro.timeout)
    assert sostituzioni > 0 and timeout > 0


def test_gli_eventi_delle_squadre():
    a, b = _squadra("Leoni", 1), _squadra("Tigri", 11, "ffm")
    risultato = simula_incontro(a, b, SQUADRE, seme=3, dettaglio=COMPLETO)
    tipi = [e.tipo for e in risultato.eventi]
    assert "CAMBIO_AL_TAVOLO" in tipi and "CAMBIO_BATTITORE" not in tipi
    cambi = [e for e in risultato.eventi if e.tipo == "CAMBIO_AL_TAVOLO"]
    for prima, dopo in itertools.pairwise(cambi):
        assert prima.dati["entra"] == dopo.dati["batte"] or prima.dati["batte"] == dopo.dati["esce"]


class _SanzioniAllaSquadraA(Incontro):
    """Due sanzioni 19.3 alla squadra A, date a due giocatori diversi: a chi è al tavolo, e poi al primo compagno che arriva al tavolo."""

    def __init__(self, *argomenti, **opzioni):
        super().__init__(*argomenti, **opzioni)
        self.puniti = []

    def _fasce_imprevisti(self, battitore, ricevitore):
        fasce = super()._fasce_imprevisti(battitore, ricevitore)
        di_a = self._per_parte()["A"]
        if len(self.puniti) < 2 and di_a.id not in self.puniti:
            self.puniti.append(di_a.id)
            return [1.0] + [0.0] * (len(fasce) - 1)
        return fasce


def test_le_ammonizioni_valgono_per_tutta_la_squadra():
    # Regola IBSA 22.15: dopo l'ammonizione di un compagno, la prima infrazione di un altro
    # giocatore della stessa squadra è già una penalità.
    for seme in range(5):
        incontro = _SanzioniAllaSquadraA(_squadra("Leoni", 1), _squadra("Tigri", 11, "ffm"), SQUADRE, seme=seme, dettaglio=ESSENZIALE)
        risultato = incontro.gioca()
        (_s1, _p1, primo, tipo_1, _c1), (_s2, _p2, secondo, tipo_2, _c2) = risultato.incontro.sanzioni
        assert primo != secondo
        assert (tipo_1, tipo_2) == ("ammonizione", "penalita")
        assert risultato.statistiche[secondo].penalita == 1 and risultato.statistiche[secondo].ammonizioni == 0


def test_la_riserva_che_entra_vale_piu_di_chi_esce():
    # Il più debole al tavolo è l'unica donna: la riserva forte è un uomo e non può prenderne il
    # posto, e la riserva donna vale meno di lei. Nessuna sostituzione per il distacco.
    for seme in range(20):
        a = Squadra("Leoni", (giocatore(1, valore=20.0), giocatore(2, valore=20.0), giocatore(3, valore=10.0, sesso="f"),
                              giocatore(4, valore=38.0), giocatore(5, valore=6.0, sesso="f")))
        b = _squadra("Tigri", 11, "mmf", valori=[30.0, 30.0, 30.0])
        risultato = simula_incontro(a, b, SQUADRE, seme=seme, dettaglio=ESSENZIALE)
        assert all(parte != "A" for _s, _p, parte, _esce, _entra in risultato.incontro.sostituzioni)
    # Il più debole è un uomo: entra la riserva forte, al suo posto.
    entrate = 0
    for seme in range(20):
        a = Squadra("Leoni", (giocatore(1, valore=10.0), giocatore(2, valore=20.0), giocatore(3, valore=20.0, sesso="f"),
                              giocatore(4, valore=38.0), giocatore(5, valore=6.0, sesso="f")))
        b = _squadra("Tigri", 11, "mmf", valori=[30.0, 30.0, 30.0])
        risultato = simula_incontro(a, b, SQUADRE, seme=seme, dettaglio=ESSENZIALE)
        for _s, _p, parte, esce, entra in risultato.incontro.sostituzioni:
            if parte == "A":
                assert (esce, entra) == (1, 4)
                entrate += 1
    assert entrate > 5


def test_senza_riserva_valida_per_il_distacco_conta_la_stanchezza():
    # Sotto nel punteggio, col più debole che è l'unica donna e una sola riserva, un uomo: per il
    # distacco nessuno può entrare, ma la stanchezza degli anziani fa entrare l'uomo al posto di un uomo.
    entrate = 0
    for seme in range(10):
        a = Squadra("Leoni", (giocatore(1, valore=20.0, anni=72, fisico=1.0), giocatore(2, valore=20.0, anni=72, fisico=1.0),
                              giocatore(3, valore=10.0, sesso="f", anni=72, fisico=1.0), giocatore(4, valore=38.0)))
        b = _squadra("Tigri", 11, "mmf", valori=[32.0, 32.0, 32.0])
        risultato = simula_incontro(a, b, SQUADRE, seme=seme, dettaglio=ESSENZIALE)
        for _s, _p, parte, esce, entra in risultato.incontro.sostituzioni:
            if parte == "A":
                assert esce in (1, 2) and entra == 4
                entrate += 1
    assert entrate > 0


class _PenalitaVersoIl16(Incontro):
    """Una penalità per la mascherina alla squadra B la prima volta che A è a 14 o 15 punti, e B sotto i 16."""

    fatta = False

    def _fasce_imprevisti(self, battitore, ricevitore):
        fasce = super()._fasce_imprevisti(battitore, ricevitore)
        if not self.fatta and self.punteggio[0] in (14, 15) and self.punteggio[1] < 16:
            self.fatta = True
            return [0.0, 0.0, 0.0, 1.0] + [0.0] * (len(fasce) - 4)
        return fasce


def test_il_cambio_campo_a_16_anche_dopo_una_penalita():
    visti = 0
    for seme in range(10):
        incontro = _PenalitaVersoIl16(_squadra("Leoni", 1, valori=[25.0] * 3), _squadra("Tigri", 11, "ffm"), SQUADRE, seme=seme, dettaglio=COMPLETO)
        risultato = incontro.gioca()
        tipi = [e.tipo for e in risultato.eventi]
        if "PENALITA" not in tipi:
            continue
        visti += 1
        penalita = tipi.index("PENALITA")
        assert "CAMBIO_CAMPO_INIZIO" in tipi[penalita:tipi.index("BATTUTA", penalita)]
        assert controlla_invarianti(risultato.eventi) == []
    assert visti > 3


def test_sorteggio_formazioni_e_riscaldamento_delle_squadre():
    # Regole IBSA 22.3, 22.5 e 22.7: chi vince il sorteggio tiene o cede il primo servizio dopo la
    # lettura delle formazioni, e nel riscaldamento l'arbitro chiama 30 secondi ogni 30 secondi.
    a, b = _squadra("Leoni", 1, "mmfm"), _squadra("Tigri", 11, "ffm")
    nomi = C.nomi_dei_giocatori([*a.giocatori, *b.giocatori], squadre=(a, b))
    scelte = set()
    for seme in range(8):
        risultato = simula_incontro(a, b, SQUADRE, seme=seme, dettaglio=COMPLETO)
        sorteggio = risultato.sorteggio
        scelte.add(sorteggio["scelta"])
        assert sorteggio["scelta"] in ("tiene", "cede")
        assert sorteggio["batte"] == (sorteggio["vince"] if sorteggio["scelta"] == "tiene" else ("B" if sorteggio["vince"] == "A" else "A"))
        tipi = [e.tipo for e in risultato.eventi]
        assert tipi[1:3] == ["SORTEGGIO", "FORMAZIONI"]
        formazioni = risultato.eventi[2]
        assert formazioni.dati["formazioni"] == {"A": [1, 2, 3], "B": [11, 12, 13]} and formazioni.dati["riserve"]["A"] == [4]
        frase = C.frase(formazioni, nomi, C.NORMALE)
        assert frase.startswith("L'arbitro legge le formazioni: Leoni con ") and "in riserva " in frase
        assert ("tiene il primo servizio." in frase) == (sorteggio["scelta"] == "tiene")
        avvisi = [e for e in risultato.eventi if e.tipo == "AVVISO_TEMPO" and e.fase == "riscaldamento"]
        assert [(e.chiamata, e.dati["restano"]) for e in avvisi] == [("trenta_secondi", 60), ("trenta_secondi", 30)]
    assert scelte == {"tiene", "cede"}
