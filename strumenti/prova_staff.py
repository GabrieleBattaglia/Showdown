"""
Una prova breve dello staff sul ramo allenatore: qualche anno di mondo simulato col seme dato, e per anno
gli allenatori, le polisportive del computer con un capo e con gli assistenti, la qualità media dello
staff e la parte dello staff nel monte stipendi.
Uso: python -B strumenti/prova_staff.py --codice . --anni 30 --seme 2026
"""

import argparse
import statistics
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--codice", type=Path, required=True)
    parser.add_argument("--anni", type=int, default=5)
    parser.add_argument("--seme", type=int, default=2026)
    argomenti = parser.parse_args()
    for cartella in (argomenti.codice, argomenti.codice / "strumenti"):
        sys.path.insert(0, str(cartella))
    import simulazione_lunga as sl

    import staff

    def misura(mondo, numero_anno):
        cpu = [p for p in mondo.polisportive.values() if p.is_cpu_controlled]
        con_capo = sum(1 for p in cpu if p.staff[0])
        pieni = sum(1 for p in cpu if all(p.staff))
        q = [staff.qualita_dello_staff(*staff.livelli_dello_staff(p.staff, mondo.allenatori)) for p in cpu]
        tipi = [a.tipo for a in mondo.allenatori.values()]
        monte = sum(mondo.monte_stipendi(p) for p in cpu)
        dello_staff = sum(mondo.monte_dello_staff(p) for p in cpu)
        liberi = sum(1 for a in mondo.allenatori.values() if a.libero)
        print(f"Anno {numero_anno}: {len(cpu)} polisportive del computer, con un capo {100 * con_capo / max(1, len(cpu)):.0f} per cento, "
              f"staff pieno {100 * pieni / max(1, len(cpu)):.0f}; qualità media {statistics.mean(q) if q else 0:.3f}; "
              f"allenatori {len(tipi)}, ex {tipi.count(staff.EX)}, nati {tipi.count(staff.NATO)}, liberi {liberi}; "
              f"staff sul monte {100 * dello_staff / max(1, monte):.1f} per cento.", flush=True)

    inizio = time.perf_counter()
    giorni_per_anno = sl.GIORNI_PER_ANNO

    def ogni_giorno(mondo, giorno, _rapporto):
        if giorno % giorni_per_anno == 0:
            misura(mondo, giorno // giorni_per_anno)

    sl.simula(argomenti.anni, argomenti.seme, stampa=None, misura_ogni_anno=False, ogni_giorno=ogni_giorno)
    print(f"In {time.perf_counter() - inizio:.0f} secondi.")


if __name__ == "__main__":
    main()
