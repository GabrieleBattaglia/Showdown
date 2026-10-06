"""
Il mercato di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 7 del piano, secondo la decisione D20: come nel mercato di
Hattrick si cercano i giocatori liberi con tanti filtri sulle caratteristiche, gli stessi della
ricerca, e a chi interessa si fa un'offerta, che il giocatore accetta o rifiuta secondo la gloria
che chiede, cioè forza, età e caratteristiche rare, e la gloria della polisportiva, la sua
reputazione. Qui sta la scelta dei candidati; l'offerta è un'operazione del mondo. Con la tappa
8 nell'offerta entrerà lo stipendio.
"""

import ricerca
from modelli import probabilita_accettazione

# Gli ordini dell'elenco dei candidati: chiave e nome da mostrare.
ORDINI = (
    ("valore", "valore, dal più alto"),
    ("probabilita", "probabilità di accettare, dalla più alta"),
    ("eta", "età, dal più giovane"),
    ("richiesta", "gloria richiesta, dalla più bassa"),
)
_CHIAVI = {
    "valore": lambda g, p: (-g.indice_collettivo_valore, g.id),
    "probabilita": lambda g, p: (-p, -g.indice_collettivo_valore, g.id),
    "eta": lambda g, p: (g.eta, g.id),
    "richiesta": lambda g, p: (g.gloria_richiesta, g.id),
}


def candidati(mondo, poli, filtri=(), probabilita_minima=0., ordine="valore"):
    """
    I giocatori liberi che soddisfano tutti i filtri, terne di criterio, condizione e valore della
    ricerca, e che accetterebbero un'offerta della polisportiva almeno con la probabilità minima,
    in percentuale. Restituisce coppie di giocatore e probabilità, nell'ordine scelto.
    """
    righe = []
    for gid in ricerca.cerca_con_filtri(mondo, "liberi", filtri):
        g = mondo.giocatori[gid]
        probabilita = probabilita_accettazione(poli.gloria, g.gloria_richiesta)
        if probabilita >= probabilita_minima:
            righe.append((g, probabilita))
    chiave = _CHIAVI[ordine]
    righe.sort(key=lambda riga: chiave(*riga))
    return righe
