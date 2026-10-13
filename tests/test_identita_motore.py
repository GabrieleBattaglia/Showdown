"""
Le impronte della tappa 12: il motore e il mondo restano uguali fino all'ultimo bit.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-13 con il primo passo della tappa 12, punto 13.7 del progetto. Le impronte si
prendono prima di toccare il codice, e da lì ogni accelerazione deve lasciarle uguali: gli stessi
numeri fino all'ultimo bit, punto 1.3.
Tre impronte. Il motore: 200 incontri fissi della popolazione di prova al meglio dei 3 e 200 al
meglio dei 5, più 20 gare a squadre, in modalità essenziale, con tutti i punti, le statistiche e i
set; senza basi d'infortunio, senza cali e senza azioni iniziali il motore fa sempre quello che
faceva, e questa impronta non cambia mai in tutta la tappa. Il mondo nato col seme 2026, dai 50
giocatori del primo avvio, dopo 120 giorni simulati. Il mondo a regime di
strumenti/mondi_sintetici.py, 1.200 attivi, 400 ritirati e 70 polisportive del computer, dopo dieci
giorni: soltanto lì ci sono giocatori nel declino e abbastanza polisportive del computer da toccare
la memoria di sponsor e monte stipendi. Le impronte dei mondi tolgono gli istanti del mondo reale e
le versioni del programma, e cambiano soltanto per scelta: ogni commit che le rigenera dice perché.
Per rigenerarle, dalla cartella del progetto:
    python tests/test_identita_motore.py --rigenera
"""

import hashlib
import json
import random
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
for _cartella in (RADICE, RADICE / "strumenti"):
    if str(_cartella) not in sys.path:
        sys.path.insert(0, str(_cartella))

import mondi_sintetici as ms  # noqa: E402
import popolazione_di_prova as pp  # noqa: E402

from motore import ESSENZIALE, SQUADRE, Squadra, formato_singolare, simula_incontro  # noqa: E402

FILE_IMPRONTE = Path(__file__).resolve().parent / "dati" / "impronte_tappa_12.json"
# Il motore: la popolazione del banco delle partite, 400 giocatori col seme 7.
GIOCATORI_MOTORE = 400
SEME_POPOLAZIONE = 7
INCONTRI_PER_FORMATO = 200
GARE_A_SQUADRE = 20
# Il mondo nato e il mondo a regime.
SEME_MONDO = 2026
GIORNI_MONDO_NATO = 120
REGIME = {"attivi": 1200, "ritirati": 400, "polisportive": 70, "seme": 31}
GIORNI_REGIME = 10


def _in_json(valore):
    """Un valore del motore come dato JSON: le tuple con nome diventano dizionari, i contatori dizionari con le chiavi in testo, gli oggetti con gli slot dizionari."""
    if hasattr(valore, "_asdict"):
        return {chiave: _in_json(v) for chiave, v in valore._asdict().items()}
    if isinstance(valore, (dict, Counter)):
        return {str(chiave): _in_json(v) for chiave, v in valore.items()}
    if isinstance(valore, (list, tuple)):
        return [_in_json(v) for v in valore]
    if hasattr(valore, "__slots__") and not isinstance(valore, (str, int, float, bool)):
        return {nome: _in_json(getattr(valore, nome)) for nome in valore.__slots__}
    return valore


def _risultato_in_json(risultato):
    """Tutto ciò che un incontro decide: seme, parti, vincitore, set, esito, ogni punto e le statistiche."""
    return {
        "seme": risultato.seme, "parti": _in_json(risultato.parti), "vincitore": risultato.vincitore, "set": _in_json(risultato.set), "esito": risultato.esito,
        "punti": _in_json(risultato.punti), "statistiche": _in_json(risultato.statistiche), "incontro": _in_json(risultato.incontro),
    }


def _sha(dato):
    return hashlib.sha256(json.dumps(dato, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def impronta_del_motore():
    """L'impronta degli incontri fissi: la popolazione e le coppie vengono da semi fissi, e il caso del mondo non si tocca."""
    giocatori = [g for g in pp.genera(GIOCATORI_MOTORE, SEME_POPOLAZIONE) if g.puo_giocare]
    rng = random.Random("impronta-del-motore")
    risultati = []
    for set_al_meglio in (3, 5):
        formato = formato_singolare(set_al_meglio)
        for _ in range(INCONTRI_PER_FORMATO):
            a, b = rng.sample(giocatori, 2)
            risultati.append(_risultato_in_json(simula_incontro(a, b, formato, seme=rng.getrandbits(63), dettaglio=ESSENZIALE)))
    maschi = [g for g in giocatori if g.sesso == "m"]
    femmine = [g for g in giocatori if g.sesso == "f"]
    for n in range(GARE_A_SQUADRE):
        scelti = rng.sample(maschi, 4) + rng.sample(femmine, 4)
        squadra_a = Squadra(f"Prova A{n}", (scelti[0], scelti[1], scelti[4], scelti[5]))
        squadra_b = Squadra(f"Prova B{n}", (scelti[2], scelti[6], scelti[7], scelti[3]))
        risultati.append(_risultato_in_json(simula_incontro(squadra_a, squadra_b, SQUADRE, seme=rng.getrandbits(63), dettaglio=ESSENZIALE)))
    return {"sha256": _sha(risultati), "incontri": len(risultati)}


def impronta_del_mondo_nato():
    """Il mondo nato col seme 2026, dopo 120 giorni simulati."""
    mondo = ms.mondo_nato(SEME_MONDO, GIORNI_MONDO_NATO)
    return {"sha256": ms.impronta_del_mondo(mondo), **ms.riassunto_del_mondo(mondo)}


def impronta_del_mondo_a_regime():
    """Il mondo a regime di strumenti/mondi_sintetici.py, dopo dieci giorni simulati col seme 2026."""
    mondo = ms.mondo_a_regime(REGIME["attivi"], REGIME["ritirati"], REGIME["polisportive"], REGIME["seme"])
    ms.avanza(mondo, GIORNI_REGIME, SEME_MONDO)
    return {"sha256": ms.impronta_del_mondo(mondo), **ms.riassunto_del_mondo(mondo)}


def _attese():
    return json.loads(FILE_IMPRONTE.read_text(encoding="utf-8"))


def test_il_motore_non_cambia():
    assert impronta_del_motore() == _attese()["motore"]


def test_il_mondo_nato_non_cambia():
    assert impronta_del_mondo_nato() == _attese()["mondo_nato"]


def test_il_mondo_a_regime_non_cambia():
    assert impronta_del_mondo_a_regime() == _attese()["mondo_a_regime"]


def rigenera(nota):
    """Riscrive il file delle impronte, nella cartella del programma spostata in una temporanea, e dice che cosa è cambiato."""
    import percorsi

    cartella = tempfile.mkdtemp(prefix="mess_impronte_")
    vera = percorsi.cartella
    percorsi.cartella = lambda: cartella
    try:
        nuove = {"motore": impronta_del_motore(), "mondo_nato": impronta_del_mondo_nato(), "mondo_a_regime": impronta_del_mondo_a_regime()}
    finally:
        percorsi.cartella = vera
        shutil.rmtree(cartella, ignore_errors=True)
    vecchie = _attese() if FILE_IMPRONTE.exists() else {}
    for chiave, impronta in nuove.items():
        stato = "uguale" if vecchie.get(chiave) == impronta else "cambiata"
        print(f"{chiave}: {stato}, {impronta}")
    FILE_IMPRONTE.parent.mkdir(parents=True, exist_ok=True)
    FILE_IMPRONTE.write_text(json.dumps({"nota": nota, **nuove}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if "--rigenera" not in sys.argv:
        sys.exit("Per riscrivere le impronte: python tests/test_identita_motore.py --rigenera \"perché cambiano\"")
    argomenti = [a for a in sys.argv[1:] if a != "--rigenera"]
    rigenera(argomenti[0] if argomenti else "Impronte rigenerate senza una nota.")
