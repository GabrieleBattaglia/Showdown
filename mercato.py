"""
Il mercato di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 7 del piano, secondo la decisione D20: come nel mercato di
Hattrick si cercano i giocatori con tanti filtri sulle caratteristiche, gli stessi della ricerca,
e a chi interessa si fa un'offerta. Dalla tappa 8, con l'economia delle decisioni D22 e D23, al
mercato ci sono tre tipi di giocatori: i liberi, a cui si offre un premio d'ingaggio; quelli in
vendita, che si comprano al prezzo chiesto; e i tesserati del computer, per cui si fa
un'offerta d'acquisto alla loro polisportiva. Qui sta la scelta dei candidati, con quanto costa
ciascuno; le offerte sono operazioni del mondo.
"""

from dataclasses import dataclass

import ricerca
from economia import ingaggio_richiesto, stipendio, valore_di_mercato

LIBERO = "libero"
IN_VENDITA = "in_vendita"
DEL_COMPUTER = "del_computer"
# Chi mostrare: chiave, nome da mostrare e tipi di giocatori.
SCELTE = (
    ("liberi_e_vendita", "i liberi e chi è in vendita", (LIBERO, IN_VENDITA)),
    ("liberi", "solo i liberi", (LIBERO,)),
    ("vendita", "solo chi è in vendita", (IN_VENDITA,)),
    ("computer", "i tesserati del computer", (DEL_COMPUTER,)),
    ("tutti", "tutti", (LIBERO, IN_VENDITA, DEL_COMPUTER)),
)
# Gli ordini dell'elenco dei candidati: chiave e nome da mostrare.
ORDINI = (
    ("valore", "valore, dal più alto"),
    ("costo", "costo, dal più basso"),
    ("stipendio", "stipendio, dal più basso"),
    ("eta", "età, dal più giovane"),
)
_CHIAVI = {
    "valore": lambda c: (-c.giocatore.indice_collettivo_valore, c.giocatore.id),
    "costo": lambda c: (c.costo, c.giocatore.id),
    "stipendio": lambda c: (c.stipendio, c.giocatore.id),
    "eta": lambda c: (c.giocatore.eta, c.giocatore.id),
}


@dataclass
class Candidato:
    """
    Un giocatore al mercato. Il costo è l'ingaggio che chiede, per un libero; il prezzo, per chi
    è in vendita; il valore di mercato del giorno, che fa da riferimento, per un tesserato del
    computer. Lo stipendio è quello che chiede oggi: chi arriva, anche comprato, firma un contratto nuovo.
    """
    giocatore: object
    tipo: str
    costo: int
    stipendio: int
    polisportiva: object = None


def candidati(mondo, poli, filtri=(), mostra="liberi_e_vendita", costo_massimo=0, ordine="valore"):
    """
    I giocatori al mercato per la polisportiva, che soddisfano tutti i filtri, terne di criterio,
    condizione e valore della ricerca, del tipo scelto e con un costo entro il massimo, se c'è,
    nell'ordine scelto. I tesserati della polisportiva stessa non ci sono mai.
    """
    tipi = {chiave: tipi for chiave, _nome, tipi in SCELTE}[mostra]
    righe = []
    if LIBERO in tipi:
        for gid in ricerca.cerca_con_filtri(mondo, "liberi", filtri):
            g = mondo.giocatori[gid]
            righe.append(Candidato(g, LIBERO, ingaggio_richiesto(g, poli), stipendio(g)))
    if IN_VENDITA in tipi or DEL_COMPUTER in tipi:
        for gid in ricerca.cerca_con_filtri(mondo, "tesserati", filtri):
            g = mondo.giocatori[gid]
            club = mondo.polisportive.get(g.appartenenza)
            if club is None or club is poli:
                continue
            if gid in club.in_vendita:
                if IN_VENDITA in tipi:
                    righe.append(Candidato(g, IN_VENDITA, club.in_vendita[gid], stipendio(g), club))
            elif club.is_cpu_controlled and DEL_COMPUTER in tipi:
                righe.append(Candidato(g, DEL_COMPUTER, valore_di_mercato(g, mondo.datetime_corrente_simulazione), stipendio(g), club))
    if costo_massimo:
        righe = [c for c in righe if c.costo <= costo_massimo]
    righe.sort(key=_CHIAVI[ordine])
    return righe
