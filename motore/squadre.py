"""
La gara a squadre del motore di partita di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9, per scelta di Gabriele nella decisione D25. Una squadra è mista,
da 3 a 6 giocatori: i primi tre sono i titolari, nell'ordine 1, 2 e 3, e al tavolo vanno due di un
sesso e uno dell'altro; gli altri sono le riserve. Si gioca un set solo a 31 punti con 2 di scarto,
con la rotazione fissa A1 contro B1, B1 contro A2, A2 contro B2 e così via: chi batte serve tre
volte contro il successivo nella sequenza, poi lascia il tavolo, e chi ha ricevuto batte contro il
seguente. Ogni squadra ha un time-out e una sostituzione per incontro, con un criterio fisso e
senza caso, scritto nell'incontro.
Nella tappa 9 il risultato di una gara a squadre non si registra nella carriera: arriva con la
tappa 12.
"""

import dataclasses

from costanti import GIOCATORI_AL_TAVOLO, GIOCATORI_SQUADRA_MAX, GIOCATORI_SQUADRA_MIN


@dataclasses.dataclass(frozen=True)
class Squadra:
    """Una squadra: il nome e i giocatori, i primi tre titolari nell'ordine di rotazione, gli altri riserve."""
    nome: str
    giocatori: tuple

    @property
    def titolari(self):
        return self.giocatori[:GIOCATORI_AL_TAVOLO]

    @property
    def riserve(self):
        return self.giocatori[GIOCATORI_AL_TAVOLO:]


def composizione_valida(giocatori):
    """Vero se tre giocatori al tavolo sono due di un sesso e uno dell'altro."""
    if len(giocatori) != GIOCATORI_AL_TAVOLO:
        return False
    uomini = sum(1 for g in giocatori if g.sesso == "m")
    return uomini in (1, 2)


def problema_squadra(squadra):
    """None se la squadra può giocare, altrimenti il motivo, in una frase."""
    giocatori = tuple(squadra.giocatori)
    if not GIOCATORI_SQUADRA_MIN <= len(giocatori) <= GIOCATORI_SQUADRA_MAX:
        return f"La squadra {squadra.nome} deve avere da {GIOCATORI_SQUADRA_MIN} a {GIOCATORI_SQUADRA_MAX} giocatori."
    if len({g.id for g in giocatori}) != len(giocatori):
        return f"La squadra {squadra.nome} ha lo stesso giocatore due volte."
    for g in giocatori:
        if not getattr(g, "puo_giocare", True):
            return f"Nella squadra {squadra.nome}, {g.nome} {g.cognome} non può giocare."
    if not composizione_valida(squadra.titolari):
        return f"Al tavolo la squadra {squadra.nome} deve avere due giocatori di un sesso e uno dell'altro."
    return None


def ordine_di_battuta(chi_batte_per_prima):
    """
    La rotazione fissa, come coppie di parte e posto da 0 a 2: A1, B1, A2, B2, A3, B3 e da capo,
    oppure B1, A1, B2, A2, B3, A3 se batte per prima la squadra B. Il giocatore in posizione i
    batte contro quello in posizione i più uno.
    """
    prima = chi_batte_per_prima
    seconda = "B" if prima == "A" else "A"
    ordine = []
    for posto in range(GIOCATORI_AL_TAVOLO):
        ordine.append((prima, posto))
        ordine.append((seconda, posto))
    return tuple(ordine)
