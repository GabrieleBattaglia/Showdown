"""
Nomi e cognomi dei giocatori di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 2 del piano, dallo smontaggio di sd.py. Le collezioni stanno
nella cartella dati, una voce per riga, e si leggono alla prima richiesta e non all'importazione
del modulo, secondo il problema P10. Una piccola quota di nomi non viene dalle collezioni ma si
inventa dagli schemi di vocali e consonanti dei nomi veri.
"""

import os
import random

import percorsi
from costanti import FILE_COGNOMI, FILE_NOMI_F, FILE_NOMI_M
from utilita import caso

VOCALI = 'aeiouy'
CONSONANTI = 'bcdfghjklmnpqrstvwxz'

_collezioni = {}
# Le collezioni che non si sono potute leggere, con il motivo: le mostra l'interfaccia.
avvisi = []


def carica_nomi(nome_file):
    """Legge una collezione dalla cartella dati: una voce per riga, commenti col cancelletto."""
    percorso = percorsi.risorsa(os.path.join("dati", nome_file))
    try:
        with open(percorso, encoding="utf-8") as f:
            return [r.strip() for r in f if r.strip() and not r.lstrip().startswith("#")]
    except OSError as e:
        avvisi.append(f"File {percorso} non leggibile: {e}")
        return []


def genera_modelli(lista_nomi):
    """Gli schemi di vocali, consonanti e spazi dei nomi di una collezione."""
    modelli = set()
    for nome in lista_nomi:
        modello = "".join(["v" if c in VOCALI else "c" if c in CONSONANTI else "s" if c == ' ' else '' for c in nome.lower()])
        if modello:
            modelli.add(modello)
    return list(modelli)


def genera_nome_casuale(modelli, tipo=None):
    """Un nome inventato, che segue uno degli schemi dati."""
    if not modelli:
        return "Casuale"
    modello = random.choice(modelli)
    nome = "".join([random.choice(CONSONANTI) if ct == 'c' else " " if ct == 's' else random.choice(VOCALI) for ct in modello])
    return nome.title()


def collezioni():
    """Le tre collezioni e i loro schemi, lette una volta sola."""
    if not _collezioni:
        nomi_m = carica_nomi(FILE_NOMI_M)
        nomi_f = carica_nomi(FILE_NOMI_F)
        cognomi = carica_nomi(FILE_COGNOMI)
        _collezioni.update({
            "nomi_m": nomi_m, "nomi_f": nomi_f, "cognomi": cognomi,
            "modelli_m": genera_modelli(nomi_m), "modelli_f": genera_modelli(nomi_f), "modelli_cognomi": genera_modelli(cognomi),
        })
    return _collezioni


def genera_identita(sesso):
    """Nome e cognome per un giocatore del sesso indicato."""
    c = collezioni()
    lista_n = c["nomi_m"] if sesso == 'm' else c["nomi_f"]
    modelli_n = c["modelli_m"] if sesso == 'm' else c["modelli_f"]
    nome = genera_nome_casuale(modelli_n, sesso) if caso(6.0) else random.choice(lista_n) if lista_n else "NomeCasuale"
    cogn = genera_nome_casuale(c["modelli_cognomi"], 'c') if caso(8.0) else random.choice(c["cognomi"]) if c["cognomi"] else "CognomeCasuale"
    return nome.title(), cogn.title()
