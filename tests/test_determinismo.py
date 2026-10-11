"""
Test del problema P17: con lo stesso seme, la nascita dei giocatori e il loro autoallenamento
danno lo stesso risultato anche in due avvii di Python con un ordine diverso degli insiemi di
stringhe, quello che decide la variabile d'ambiente PYTHONHASHSEED.
"""

import os
import subprocess
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
PROGRAMMA = """
import datetime, json, random
import allenamento, modelli
random.seed(5)
giocatori = [modelli.Giocatore(i, datetime.datetime(2026, 1, 1)) for i in range(1, 41)]
for g in giocatori:
    g.punti_allenamento = 1500.0
    allenamento.allena_secondo_programma(g)
dati = [g.a_dizionario() for g in giocatori]
for d in dati:
    d.pop("datacreazione_reale")
print(json.dumps(dati, sort_keys=True))
"""


def _mondo_con(ordine):
    ambiente = dict(os.environ, PYTHONHASHSEED=str(ordine), PYTHONPATH=str(RADICE) + os.pathsep + os.environ.get("PYTHONPATH", ""))
    esito = subprocess.run([sys.executable, "-B", "-c", PROGRAMMA], capture_output=True, text=True, encoding="utf-8", env=ambiente, cwd=RADICE, check=True)  # noqa: S603 - il Python corrente con un programma scritto qui, nessun dato esterno
    return esito.stdout


def test_stesso_seme_stesso_mondo_con_ordini_diversi():
    primo = _mondo_con(1)
    assert len(primo) > 1000
    assert _mondo_con(2) == primo
    assert _mondo_con(12345) == primo
