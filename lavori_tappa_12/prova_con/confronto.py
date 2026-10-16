"""
Il confronto della prova breve della decisione 17 con la prova di sessant'anni di prima, sui primi anni:
per seme e per anno la cassa mediana del computer, i primi 10, 20 e 100 tesserati, lo stipendio mediano,
il monte stipendi sullo sponsor e i tesserati, prima e dopo. Legge soltanto i JSON di prova_con.py.
Uso: python -B confronto.py PRIMA.json DOPO.json
"""

import json
import sys
from pathlib import Path


def leggi(file):
    dati = json.loads(Path(file).read_text(encoding="utf-8"))
    return {int(seme): {m["numero_anno"]: m for m in annuali} for seme, (annuali, _anni_dati) in dati.items()}


prima, dopo = leggi(sys.argv[1]), leggi(sys.argv[2])
for seme in sorted(dopo):
    print(f"Seme {seme}, anno: cassa mediana prima e dopo; primi 10, 20, 100 prima e dopo; stipendio mediano; monte su sponsor; tesserati.")
    for anno in sorted(dopo[seme]):
        p, d = prima[seme].get(anno), dopo[seme][anno]
        if p is None:
            continue
        print(f"anno {anno}: cassa {p['casse'][1]:.0f} {d['casse'][1]:.0f} (90° {p['casse'][2]:.0f} {d['casse'][2]:.0f}); "
              f"primi 10 {p['primi_10']} {d['primi_10']}, 20 {p['primi_20']} {d['primi_20']}, 100 {p['primi_100']:.0f} {d['primi_100']:.0f}; "
              f"stipendio {p['stipendi'][1]:.0f} {d['stipendi'][1]:.0f}; monte {100 * p['monte_su_sponsor']:.0f} {100 * d['monte_su_sponsor']:.0f}; "
              f"tesserati {100 * p['tesserati'] / p['attivi']:.1f} {100 * d['tesserati'] / d['attivi']:.1f}; rinnovi {p['anno'].get('rinnovi_cpu', 0)} {d['anno'].get('rinnovi_cpu', 0)}")
    anni = sorted(set(dopo[seme]) & set(prima[seme]))
    for nome, chiave in (("cassa mediana", lambda m: m["casse"][1]), ("primi 10", lambda m: m["primi_10"])):
        somma_p = sum(chiave(prima[seme][a]) for a in anni)
        somma_d = sum(chiave(dopo[seme][a]) for a in anni)
        print(f"Seme {seme}, {nome} in media sugli anni {anni[0]}-{anni[-1]}: prima {somma_p / len(anni):.1f}, dopo {somma_d / len(anni):.1f}.")
    sotto_p = [a for a in anni if prima[seme][a]["primi_10"] < 8]
    sotto_d = [a for a in anni if dopo[seme][a]["primi_10"] < 8]
    print(f"Seme {seme}, anni coi primi 10 tesserati sotto 8: prima {sotto_p}, dopo {sotto_d}.")
