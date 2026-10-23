"""
MESS, utilità: prepara l'archivio della release per l'aggiornamento automatico.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-23 con la tappa 14, dal modello di MeTeOra. Comprime dist/MESS in MESS.zip, coi
file alla radice e il manifesto di _internal: tutto il mestiere sta in crea_archivio_release di
GBUtils, così la regola delle esclusioni è una sola per tutti i progetti (prontuario, fase 7). Qui
restano i nomi di MESS: i file che nascono accanto all'eseguibile provandolo, cioè il mondo, le
impostazioni, i modelli e le formule dei tornei copiati al primo avvio, le cronache e i salvataggi
illeggibili; i registri .log li toglie già GBUtils.
"""

import sys

from GBUtils import crea_archivio_release

FUORI = [
    "mess_mondo.json*",
    "mess_impostazioni.json",
    "formule.json",
    "tornei/",
    "cronache/",
    "salvataggi_illeggibili/",
]


def main():
    try:
        crea_archivio_release("MESS", escludi=FUORI)
    except (FileNotFoundError, OSError) as e:
        print(f"Archivio non creato: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
