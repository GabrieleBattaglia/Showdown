"""
Il mondo delle prove della finestra Mercato e ricerca, comune alle prove del motore e a quelle della finestra.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-24 col passo della finestra, dalla fixture delle prove del motore, tests/test_mercato_e_ricerca.py.
"""

import datetime
import random

from mondo import Mondo

ORA = datetime.datetime(2026, 10, 6, 18, 0)


def mondo_del_mercato():
    """
    Un mondo di 120 giocatori: due polisportive tue, Pat-Bologna attiva con cinque tesserati e Pat-Milano con
    quattro, due del computer con dodici e otto; in vendita uno del computer, uno di Pat-Milano a 1 euro e uno
    di Pat-Bologna; cinque ritirati, uno uscito di scena; sei allenatori, uno nello staff del computer, uno
    nel tuo, gli altri liberi.
    """
    random.seed(808)
    m = Mondo()
    m.datetime_corrente_simulazione = ORA
    m.crea_giocatori_casuali(120, ORA, annuncia=False)
    m.nuovi_giocatori_sessione = list(range(100, 121))
    mia = m.fonda_polisportiva("Pat-Bologna", luogo="Bologna")
    altra = m.fonda_polisportiva("Pat-Milano", attiva=False, luogo="Milano")
    cpu = [m.polisportive[m.crea_polisportiva_cpu(ORA)] for _ in range(2)]
    for gid in range(1, 6):
        m._entra(mia, m.giocatori[gid])
    for gid in range(6, 10):
        m._entra(altra, m.giocatori[gid])
    for gid in range(10, 22):
        m._entra(cpu[0], m.giocatori[gid])
    for gid in range(22, 30):
        m._entra(cpu[1], m.giocatori[gid])
    cpu[0].in_vendita[10] = 3000
    altra.in_vendita[6] = 1
    mia.in_vendita[1] = 500
    for gid in range(40, 45):
        m.giocatori[gid].ritirato = True
    m._ids_morti_processati_sessione.add(45)
    m.giocatori[45].ritirato = True
    rng = random.Random(9)
    allenatori = [m._nasce_un_allenatore(ORA, rng) for _ in range(6)]
    m.assumi_allenatore(cpu[0], allenatori[0], 0, ORA)
    m.assumi_allenatore(mia, allenatori[1], 1, ORA)
    return m
