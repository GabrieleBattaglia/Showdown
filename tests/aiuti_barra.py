"""
Gli aiuti delle prove per la barra di stato su misura, decisione D38: l'ultimo evento come lo scrive la barra di serie.
Prima della barra su misura l'ultimo evento stava sulla quarta riga, da sola; adesso sta in fondo all'ultima riga della
barra di serie, dopo il numero delle notizie dell'ultimo avanzamento.
"""

import re


def evento_della_barra(finestra):
    """L'ultimo evento come lo dice la barra di serie: l'ultima riga, senza il numero delle notizie che la apre."""
    return re.sub(r"^Not:\d+ ", "", finestra.barra.GetValue().splitlines()[-1])
