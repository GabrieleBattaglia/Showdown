"""
MESS, l'elenco dei suoni per Acu_Maker: per ogni azione della finestra e della partita, il preset
della collezione di GBUtils che la fa suonare.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-08 con la fase dei timbri della tappa 10, richiesta di Gabriele della decisione
D29: un file di testo nella cartella del progetto, suoni_di_mess.txt, che elenca ogni azione con il
nome del suo preset, così Gabriele può ritoccare i suoni come vuole con Acu_Maker. Il file si genera
dalle mappe dei suoni, suoni.GRUPPI con suoni.AZIONI per la finestra e partita_sonora.SUONI con
partita_sonora.AZIONI per la partita, e una prova controlla che sia aggiornato: quando una mappa
cambia, si rilancia lo strumento.
Il testo è una riga per voce, senza separatori grafici né righe vuote: in testa due righe che dicono
che cosa è il file, poi per ogni gruppo una riga col suo titolo, preceduto da Finestra per quelli
della finestra, e quanti suoni ha, e sotto le sue voci, ciascuna con l'azione detta a parole, i due
punti e il nome del preset.
Uso, dalla cartella del programma: python strumenti/elenco_suoni.py
"""

import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))

import partita_sonora  # noqa: E402
import suoni  # noqa: E402
from testi import conta  # noqa: E402

NOME_DEL_FILE = "suoni_di_mess.txt"
TITOLO_DELLA_PARTITA = "Partita dal vivo, i suoni dell'incontro"


def _voce(azione, preset):
    return f"{azione[0].upper()}{azione[1:]}: {preset}."


def righe():
    """Le righe del file, senza fine riga: l'intestazione, poi i gruppi della finestra e quello della partita."""
    quanti = len(suoni.EVENTI) + len(partita_sonora.SUONI)
    uscita = [
        f"I suoni di MESS e i loro preset nella collezione di GBUtils, da ritoccare con Acu_Maker: {conta(quanti, 'suono', 'suoni')}, "
        f"{len(suoni.EVENTI)} della finestra e {len(partita_sonora.SUONI)} della partita dal vivo.",
        "Ogni riga dice l'azione che fa suonare il preset e, dopo i due punti, il suo nome. Il file lo scrive strumenti/elenco_suoni.py "
        "dalle mappe dei suoni: non va modificato a mano.",
    ]
    for titolo, gruppo in suoni.GRUPPI:
        uscita.append(f"Finestra, {titolo[0].lower()}{titolo[1:]}, {conta(len(gruppo), 'suono', 'suoni')}.")
        uscita.extend(_voce(suoni.AZIONI[evento], preset) for evento, preset in gruppo.items())
    uscita.append(f"{TITOLO_DELLA_PARTITA}, {conta(len(partita_sonora.SUONI), 'suono', 'suoni')}.")
    uscita.extend(_voce(partita_sonora.AZIONI[ruolo], preset) for ruolo, preset in partita_sonora.SUONI.items())
    return uscita


def testo():
    return "".join(f"{riga}\n" for riga in righe())


def percorso():
    return RADICE / NOME_DEL_FILE


def main():
    destinazione = percorso()
    destinazione.write_text(testo(), encoding="utf-8")
    print(f"Scritto {destinazione.name}: {conta(len(righe()), 'riga', 'righe')}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
