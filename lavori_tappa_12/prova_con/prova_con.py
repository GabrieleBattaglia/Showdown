"""
La prova lunga di strumenti/simulazione_lunga.py con valori provati soltanto nei processi della prova,
senza toccare costanti.py: i mesi e la soglia della cassa piena del computer, lo sponsor per gloria, la
scala del valore, la gloria (coefficienti e fattore), la quota d'argento delle sfide. Scrive il racconto
come la prova lunga, e i numeri grezzi in un JSON accanto.
Uso: python -B prova_con.py --codice DIR --anni 60 --semi 2026 7 --processi 2 --rapporto FILE [--mesi 8] [--soglia 10000]
     [--sponsor 7,8] [--scala A B] [--gloria KM KC F] [--argento 0,1] [--salva-mondi DIR]
"""

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


def decimale(testo):
    return float(testo.replace(",", "."))


def argomenti_della_riga():
    parser = argparse.ArgumentParser()
    parser.add_argument("--codice", type=Path, required=True)
    parser.add_argument("--anni", type=int, default=60)
    parser.add_argument("--semi", type=int, nargs="+", default=[2026, 7])
    parser.add_argument("--processi", type=int, default=2)
    parser.add_argument("--rapporto", type=Path, required=True)
    parser.add_argument("--mesi", type=decimale, default=None)
    parser.add_argument("--soglia", type=decimale, default=None)
    parser.add_argument("--sponsor", type=decimale, default=None)
    parser.add_argument("--scala", type=decimale, nargs=2, default=None)
    parser.add_argument("--gloria", type=decimale, nargs=3, default=None)
    parser.add_argument("--argento", type=decimale, default=None)
    parser.add_argument("--salva-mondi", type=Path, default=None)
    return parser.parse_args()


def prepara(codice):
    for cartella in (codice, codice / "strumenti"):
        if str(cartella) not in sys.path:
            sys.path.insert(0, str(cartella))


def imposta(valori):
    """I valori provati, nei moduli di questo processo."""
    import economia
    import sfide
    import simulazione_lunga as sl
    import valore

    if valori["mesi"] is not None:
        economia.MESI_CASSA_PIENA_CPU = valori["mesi"]
    if valori["soglia"] is not None:
        economia.SOGLIA_CASSA_PIENA_CPU = valori["soglia"]
    if valori["argento"] is not None:
        sfide.QUOTA_GLORIA_ARGENTO_SFIDA = valori["argento"]
    a, b = valori["scala"] if valori["scala"] is not None else (valore.SCALA_VALORE_A, valore.SCALA_VALORE_B)
    sl._imposta(a, b, valori["sponsor"], tuple(valori["gloria"]) if valori["gloria"] is not None else None)


def lavoro(codice, valori, anni, seme, salva_mondi):
    prepara(Path(codice))
    imposta(valori)
    import simulazione_lunga as sl

    return sl._anni_della_prova_lunga(anni, seme, None, salva_mondi)


def main():
    argomenti = argomenti_della_riga()
    prepara(argomenti.codice)
    import simulazione_lunga as sl

    valori = {"mesi": argomenti.mesi, "soglia": argomenti.soglia, "sponsor": argomenti.sponsor, "scala": argomenti.scala, "gloria": argomenti.gloria,
              "argento": argomenti.argento}
    inizio = time.perf_counter()
    with ProcessPoolExecutor(max_workers=argomenti.processi) as esecutore:
        futuri = [esecutore.submit(lavoro, str(argomenti.codice), valori, argomenti.anni, seme, str(argomenti.salva_mondi) if argomenti.salva_mondi else None)
                  for seme in argomenti.semi]
        completi = {seme: (annuali, anni_dati) for seme, annuali, anni_dati in [f.result() for f in futuri]}
    righe = [f"Prova con {json.dumps(valori, ensure_ascii=False)}, {argomenti.anni} anni sui semi {argomenti.semi}, in {time.perf_counter() - inizio:.0f} secondi."]
    for decennio in range(10, argomenti.anni + 1, 10):
        voci = []
        for seme in argomenti.semi:
            m = next(x for x in completi[seme][0] if x["numero_anno"] == decennio)
            voci.append(f"seme {seme}: valore {m['valore'][1]:.1f}, stipendi {m['stipendi'][0]:.0f} {m['stipendi'][1]:.0f} {m['stipendi'][2]:.0f}, cassa "
                        f"{m['casse'][0]:.0f} {m['casse'][1]:.0f} {m['casse'][2]:.0f}, tesserati {100 * m['tesserati'] / max(1, m['attivi']):.1f} su {m['attivi']}, "
                        f"primi 100 {m['primi_100']:.0f}, gloria {m['gloria_mediana']:.0f}, richiesta {m['rapporto_richiesta']:.3f}, monte su sponsor "
                        f"{100 * m['monte_su_sponsor']:.0f}, giorno {m['millisecondi']:.0f} ms")
        righe.append(f"Anno {decennio}: " + "; ".join(voci) + ".")
    for seme in argomenti.semi:
        annuali = completi[seme][0]
        righe.append(f"Seme {seme}, anno per anno: cassa mediana " + ", ".join(f"{m['casse'][1]:.0f}" for m in annuali) + "; primi 100 tesserati "
                     + ", ".join(f"{m['primi_100']:.0f}" for m in annuali) + "; tesserati " + ", ".join(f"{100 * m['tesserati'] / max(1, m['attivi']):.0f}" for m in annuali) + ".")
        fuori = sl.fuori_dalla_solvibilita(annuali)
        righe.append(f"Seme {seme}, fuori dalla solvibilità: " + ("nessun anno." if not fuori else "; ".join(f"anno {a}, tesserati {t:.1f}, cassa {c:.0f}" for a, t, c in fuori)))
    righe.extend(sl.controlli_della_tappa_12(argomenti.anni, argomenti.semi, completi))
    testo = "\n".join(righe) + "\n"
    argomenti.rapporto.write_text(testo, encoding="utf-8")
    grezzi = {str(s): ([{k: v for k, v in m.items() if k != "fasce"} for m in annuali], anni_dati) for s, (annuali, anni_dati) in completi.items()}
    argomenti.rapporto.with_suffix(".json").write_text(json.dumps(grezzi, ensure_ascii=False, default=str), encoding="utf-8")
    print(testo)


if __name__ == "__main__":
    main()
