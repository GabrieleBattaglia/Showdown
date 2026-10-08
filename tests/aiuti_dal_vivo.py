"""
Strumenti comuni alle prove della partita dal vivo della tappa 10: la cassa vera di Acusticator che
fa fallire chi la chiama, una cassa finta che tiene i buffer accesi e conta le fermate delle maniglie,
e un orologio finto che va avanti solo quando lo dice la prova. Così nessuna prova suona.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import numpy as np
from GBUtils import Acusticator


def _vietato(nome):
    def chiamata(*_args, **_kwargs):
        raise AssertionError(f"una prova avrebbe suonato davvero, con {nome}")

    return chiamata


def vieta_la_cassa_vera(monkeypatch):
    """La cassa vera di Acusticator non deve suonare mai: chi la chiama fa fallire la prova."""
    for nome in ("riproduci", "ciclo_di", "play", "stop"):
        monkeypatch.setattr(Acusticator, nome, _vietato(f"Acusticator.{nome}"))


class Maniglia:
    """La maniglia di un ciclo finto: conta quante volte la si ferma."""

    def __init__(self):
        self.fermate = 0

    def stop(self):
        self.fermate += 1
        return True


class CassaFinta:
    """Al posto della cassa vera: tiene i buffer accesi, nell'ordine, con le loro maniglie."""

    def __init__(self):
        self.buffer = []
        self.maniglie = []

    def accendi(self, buffer):
        self.buffer.append(np.asarray(buffer))
        self.maniglie.append(Maniglia())
        return self.maniglie[-1]

    @property
    def accese(self):
        """Quante maniglie non sono ancora state fermate."""
        return sum(1 for m in self.maniglie if not m.fermate)


class Orologio:
    """Un orologio che va avanti soltanto quando la prova sposta adesso."""

    def __init__(self, adesso=100.0):
        self.adesso = adesso

    def __call__(self):
        return self.adesso
