"""
MESS, l'ascolto guidato degli effetti sonori della finestra, gruppo per gruppo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la decisione D24, sul modello dell'ascolto di PokerMachine, per collaudare
i suoni prima di sentirli nel gioco. I gruppi sono quelli di suoni.GRUPPI, nell'ordine: le quattro
famiglie, applicazione, mondo, polisportive ed economia, divise in gruppi piccoli.
Prima di suonare aspetta il via, poi lascia qualche secondo di silenzio. Ogni gruppo si annuncia e
si può saltare; per ogni evento scrive il nome, il preset e la descrizione, e lo suona al volume di
progetto, 50, quello a cui i suoni sono stati pensati, qualunque sia il volume scelto nel gioco. La
probabilità d'ingaggio si sente tre volte, al 10, al 50 e al 90 per cento, perché la sua altezza
cambia con la percentuale.
Ogni gruppo si chiude con il menu comune dei collaudi, quello di collaudo_comune di GBUtils: r
riascolta il gruppo, c lascia un commento, Invio lo dà per superato, Escape lo chiude senza
giudizio. Le impressioni vanno nel file ascolto_suoni.txt, nella cartella del programma, una riga
per voce.
Uso, dalla cartella del programma: python ascolta_suoni.py. Con una parola, per esempio
python ascolta_suoni.py economia, fa sentire soltanto i gruppi il cui titolo la contiene.
"""

import sys
import time

from collaudo_comune import Esiti, gruppo
from GBUtils import Acusticator, enter_escape

import percorsi
import suoni
from testi import conta

FILE_DEGLI_ESITI = "ascolto_suoni.txt"
SILENZIO_INIZIALE = 3.0
PAUSA_FRA_I_SUONI = 1.2
PERCENTUALI_DI_PROVA = (10, 50, 90)


class Annotazioni(Esiti):
    """Il registro e il menu di collaudo_comune, con gli esiti scritti una riga per voce: gruppo, data e commento."""

    def registra(self, titolo, commento, misura=""):
        with open(self.percorso, "a", encoding="utf-8") as f:
            f.write(f"{titolo}, {time.strftime('%Y-%m-%d %H:%M')}: {commento or 'nessun commento'}\n")


def ascolta(eventi):
    """Fa sentire gli eventi di un gruppo uno dopo l'altro, ciascuno con il nome, il preset e la descrizione."""
    for numero, (evento, preset) in enumerate(eventi.items(), 1):
        print(f"{numero} di {len(eventi)}: {evento}, preset {preset}. {Acusticator.descrizione(preset) or 'Senza descrizione.'}")
        if evento == "probabilita_ingaggio":
            print(f"Lo senti {conta(len(PERCENTUALI_DI_PROVA), 'volta', 'volte')}: al {', al '.join(map(str, PERCENTUALI_DI_PROVA))} per cento.")
            for percentuale in PERCENTUALI_DI_PROVA:
                suoni.suona(evento, sync=True, volume=suoni.VOLUME_DI_PROGETTO, semitoni=suoni.probabilita_in_semitoni(percentuale))
                time.sleep(PAUSA_FRA_I_SUONI / 2)
        else:
            suoni.suona(evento, sync=True, volume=suoni.VOLUME_DI_PROGETTO)
        time.sleep(PAUSA_FRA_I_SUONI)


def main():
    parola = " ".join(sys.argv[1:]).strip().casefold()
    gruppi = [(titolo, eventi) for titolo, eventi in suoni.GRUPPI if parola in titolo.casefold()]
    if not gruppi:
        print(f"Nessun gruppo contiene {parola}. I gruppi sono: {'; '.join(titolo for titolo, _e in suoni.GRUPPI)}.")
        return 1
    quanti = sum(len(eventi) for _titolo, eventi in gruppi)
    print(f"Ascolto degli effetti sonori di MESS: {conta(len(gruppi), 'gruppo', 'gruppi')}, {conta(quanti, 'suono', 'suoni')}, al volume di progetto.")
    print("Ogni gruppo si annuncia e si può saltare. A fine gruppo: r riascolta, c commenta, Invio lo dà per superato, Escape lo chiude senza giudizio.")
    print(f"Le impressioni vanno nel file {FILE_DEGLI_ESITI}, una riga per voce.")
    if not enter_escape("\rInvio per cominciare, Escape per uscire\r"):
        print()
        return 0
    print()
    time.sleep(SILENZIO_INIZIALE)
    esiti = Annotazioni(percorsi.percorso(FILE_DEGLI_ESITI))
    for titolo, eventi in gruppi:
        if not gruppo(titolo, len(eventi), "suoni"):
            print()
            continue
        print()
        ascolta(eventi)
        esiti.esito(titolo, riproduci=lambda e=eventi: ascolta(e))
    print("Fine dell'ascolto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
