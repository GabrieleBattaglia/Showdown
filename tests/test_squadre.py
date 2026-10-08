"""
Test della gara a squadre: composizione, rotazione fissa, tre servizi, set a 31 con 2 di scarto,
cambio campo a 16, anche dopo una penalità, un time-out per squadra; nessuna sostituzione durante
l'incontro, decisione D26, nemmeno con la squadra stanca e molto sotto e le riserve fortissime, e
una riserva messa fra i primi tre che gioca tutta la gara; le ammonizioni che valgono per tutta la
squadra, il sorteggio con la lettura delle formazioni e gli avvisi del riscaldamento.
"""

import itertools

import pytest
from aiuti_motore import giocatore

from motore import cronaca as C
from motore import eventi as E
from motore.incontro import COMPLETO, ESSENZIALE, SQUADRE, Incontro, StatisticheIncontro, simula_incontro
from motore.regia import controlla_invarianti
from motore.squadre import Squadra, ordine_di_battuta, problema_squadra


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


def _chi_ha_giocato(risultato):
    return {p.battitore for p in risultato.punti} | {p.ricevitore for p in risultato.punti}


def test_un_time_out_per_squadra_e_nessuna_sostituzione():
    # La squadra A ha tre titolari anziani, deboli e poco resistenti, e tre riserve fortissime:
    # col vecchio criterio sarebbe entrata una riserva, per il distacco o per la stanchezza. Con
    # la decisione D26 la formazione dichiarata all'inizio gioca tutta la gara.
    timeout = 0
    for seme in range(40):
        a = _squadra("Leoni", 1, "mmfmmf", valori=[6.0, 6.0, 6.0, 35.0, 35.0, 35.0], anni=60, fisico=1.0)
        b = _squadra("Tigri", 11, "ffmffm", valori=[30.0, 30.0, 30.0, 10.0, 10.0, 10.0])
        incontro = Incontro(a, b, SQUADRE, seme=seme, dettaglio=COMPLETO if seme < 5 else ESSENZIALE)
        risultato = incontro.gioca()
        x, y = risultato.set[0]
        assert y - x >= 10, "La squadra A deve finire molto sotto, perché la prova abbia senso."
        if risultato.eventi:
            assert controlla_invarianti(risultato.eventi) == []
            assert "SOSTITUZIONE" not in {e.tipo for e in risultato.eventi}
        assert _chi_ha_giocato(risultato) == {1, 2, 3, 11, 12, 13}
        assert incontro.formazione == {"A": [1, 2, 3], "B": [11, 12, 13]}
        assert max(sum(1 for _s, _p, parte in risultato.incontro.timeout if parte == quale) for quale in "AB") <= 1
        timeout += len(risultato.incontro.timeout)
    assert timeout > 0
    assert "SOSTITUZIONE" not in E.TIPI and "sostituzioni" not in StatisticheIncontro.__slots__
    assert not hasattr(SQUADRE, "sostituzioni")


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


def test_la_riserva_messa_in_formazione_gioca_tutta_la_gara():
    # La formazione si dichiara all'inizio: la squadra mette la riserva forte fra i primi tre, al
    # posto del secondo, e quella gioca tutta la gara; chi resta fuori non entra mai, nemmeno
    # stanco o sotto nel punteggio.
    for seme in range(20):
        titolari = (giocatore(1, valore=10.0, anni=70, fisico=1.0), giocatore(4, valore=38.0), giocatore(3, valore=10.0, sesso="f", anni=70, fisico=1.0))
        a = Squadra("Leoni", (*titolari, giocatore(2, valore=20.0), giocatore(5, valore=36.0, sesso="f")))
        b = _squadra("Tigri", 11, "mmf", valori=[32.0, 32.0, 32.0])
        incontro = Incontro(a, b, SQUADRE, seme=seme, dettaglio=ESSENZIALE)
        risultato = incontro.gioca()
        giocato = _chi_ha_giocato(risultato)
        assert {1, 4, 3} <= giocato and not {2, 5} & giocato
        assert incontro.formazione["A"] == [1, 4, 3]
        assert risultato.sorteggio["riserve"]["A"] == [2, 5]


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
