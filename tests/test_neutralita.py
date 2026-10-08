"""
Test della neutralità: le procedure, la regia e la cronaca non spostano mai un punto. Con lo stesso
seme, time-out e riscaldamento accesi o spenti danno gli stessi punti; la modalità essenziale e la
completa danno gli stessi set, gli stessi esiti punto per punto e gli stessi time-out, anche in due
avvii di Python con ordini diversi degli insiemi; e un incontro senza seme preleva dal caso globale
un numero solo.
"""

import json
import os
import random
import subprocess
import sys
from pathlib import Path

from aiuti_motore import giocatore

from motore.incontro import COMPLETO, ESSENZIALE, SINGOLARE_3, SINGOLARE_5, Incontro, simula_incontro

RADICE = Path(__file__).resolve().parent.parent


def _coppia(seme):
    rng = random.Random(seme)
    return (giocatore(1, valore=rng.uniform(8, 30), temperamento=rng.uniform(0, 100), esperienza=rng.uniform(0, 15)),
            giocatore(2, valore=rng.uniform(8, 30), mancino=True, temperamento=rng.uniform(0, 100)))


def test_time_out_e_riscaldamento_non_spostano_i_punti():
    for seme in range(12):
        a, b = _coppia(seme)
        acceso = simula_incontro(a, b, SINGOLARE_3, seme=seme, dettaglio=COMPLETO)
        spento = simula_incontro(a, b, SINGOLARE_3, seme=seme, dettaglio=COMPLETO, timeout=False, riscaldamento=False)
        assert acceso.punti == spento.punti and acceso.set == spento.set
        assert spento.incontro.timeout == []


def test_modalita_essenziale_e_completa_uguali():
    timeout = 0
    for seme in range(25):
        a, b = _coppia(seme)
        formato = SINGOLARE_5 if seme % 2 else SINGOLARE_3
        completa = simula_incontro(a, b, formato, seme=seme, dettaglio=COMPLETO)
        essenziale = simula_incontro(a, b, formato, seme=seme, dettaglio=ESSENZIALE)
        assert completa.set == essenziale.set
        assert completa.punti == essenziale.punti
        assert completa.incontro.timeout == essenziale.incontro.timeout
        assert essenziale.eventi is None and essenziale.durata_simulata is None
        timeout += len(completa.incontro.timeout)
    assert timeout > 0


PROGRAMMA = """
import json, random, sys
sys.path.insert(0, "tests")
from aiuti_motore import giocatore
from motore.incontro import COMPLETO, ESSENZIALE, SINGOLARE_3, simula_incontro
uscita = []
for seme in range(4):
    a, b = giocatore(1, valore=10 + seme), giocatore(2, valore=25 - seme, mancino=True)
    for dettaglio in (ESSENZIALE, COMPLETO):
        r = simula_incontro(a, b, SINGOLARE_3, seme=seme, dettaglio=dettaglio)
        uscita.append([r.set, [list(p) for p in r.punti], r.incontro.timeout])
print(json.dumps(uscita))
"""


def _gioca_con(ordine):
    ambiente = dict(os.environ, PYTHONHASHSEED=str(ordine), PYTHONPATH=str(RADICE) + os.pathsep + os.environ.get("PYTHONPATH", ""))
    esito = subprocess.run([sys.executable, "-B", "-c", PROGRAMMA], capture_output=True, text=True, encoding="utf-8", env=ambiente, cwd=RADICE, check=True)  # noqa: S603 - il Python corrente con un programma scritto qui, nessun dato esterno
    return esito.stdout


def test_stessi_punti_con_ordini_diversi_degli_insiemi():
    primo = _gioca_con(1)
    assert len(json.loads(primo)) == 8
    assert _gioca_con(2) == primo
    assert _gioca_con(4321) == primo


def test_senza_seme_si_preleva_un_numero_solo_dal_caso_globale():
    a, b = _coppia(1)
    random.seed(55)
    incontro = Incontro(a, b, SINGOLARE_3, dettaglio=ESSENZIALE)
    incontro.gioca()
    dopo = random.getstate()
    random.seed(55)
    atteso = random.getrandbits(63)
    assert incontro.seme == atteso
    assert random.getstate() == dopo
    rigiocato = simula_incontro(a, b, SINGOLARE_3, seme=atteso, dettaglio=ESSENZIALE)
    assert rigiocato.punti == incontro.risultato.punti
