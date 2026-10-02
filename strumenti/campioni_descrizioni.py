"""
Campioni delle descrizioni fisiche di MESS, da leggere e giudicare a orecchio.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Genera venti giocatori, dieci maschi e dieci femmine di età varia, e scrive per ciascuno sesso,
età, altezza, peso e descrizione. Quattro di loro compaiono di nuovo più avanti negli anni, per
sentire come la descrizione invecchia con il giocatore. Non scrive nulla nel gioco.
Uso, dalla cartella del progetto o da qualunque altra:
    python strumenti/campioni_descrizioni.py
    python strumenti/campioni_descrizioni.py --seme 42 --quanti 30
Il file va in strumenti/campioni_descrizioni.txt, oppure dove dice --file.
"""

import argparse
import random
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))

import descrizioni  # noqa: E402

ETA_INVECCHIATE = (52, 61, 68, 75)


def riga_dati(numero, sesso, eta, tratti):
    altezza, peso = descrizioni.fisico(tratti, sesso, eta)
    chi = "Maschio" if sesso == "m" else "Femmina"
    return f"{numero}. {chi} di {int(eta)} anni, {altezza} centimetri e {peso} chili."


def main():
    parser = argparse.ArgumentParser(description="Scrive in un file di testo una serie di descrizioni fisiche di prova.")
    parser.add_argument("--seme", type=int, default=None, help="il seme del generatore casuale, per riavere gli stessi campioni")
    parser.add_argument("--quanti", type=int, default=20, help="quanti giocatori, 20 se non indicato")
    parser.add_argument("--file", type=Path, default=RADICE / "strumenti" / "campioni_descrizioni.txt", help="il file da scrivere")
    argomenti = parser.parse_args()
    seme = argomenti.seme if argomenti.seme is not None else random.randrange(1_000_000)
    rng = random.Random(seme)
    righe = [f"Campioni di descrizioni fisiche, seme {seme}: per riavere gli stessi si aggiunge --seme {seme}."]
    giocatori = []
    for i in range(argomenti.quanti):
        sesso = "m" if i % 2 == 0 else "f"
        eta = rng.uniform(9, 45)
        tratti = descrizioni.genera_tratti(sesso, rng)
        giocatori.append((sesso, eta, tratti))
        righe.append(riga_dati(i + 1, sesso, eta, tratti))
        righe.append(descrizioni.descrivi(tratti, sesso, eta))
    righe.append("Gli stessi giocatori, più avanti negli anni.")
    for indice, eta in zip(range(0, len(giocatori), max(1, len(giocatori) // len(ETA_INVECCHIATE))), ETA_INVECCHIATE, strict=False):
        sesso, _, tratti = giocatori[indice]
        righe.append(riga_dati(indice + 1, sesso, eta, tratti))
        righe.append(descrizioni.descrivi(tratti, sesso, eta))
    argomenti.file.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print(f"Scritti {argomenti.quanti} giocatori e {len(ETA_INVECCHIATE)} invecchiati in {argomenti.file}.")


if __name__ == "__main__":
    main()
