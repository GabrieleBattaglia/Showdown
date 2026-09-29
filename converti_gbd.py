# Showdown, conversione delle collezioni .gbd in file di testo.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
# 29/09/2026: script da eseguire una volta sola. Le collezioni erano liste
# salvate con pickle; diventano file di testo con una voce per riga nella
# cartella dati, che Gabriele può ampliare con un editor. Nomi e cognomi si
# uniscono a quelli del programma CLZ, che ne ha qualcuno in più. I .gbd si
# cancellano solo dopo aver riletto i txt e verificato che non manchi nulla.

"""Converte le collezioni CLZ-*.gbd di Showdown nei file di testo della cartella dati."""

import json
import os
import pickle
import sys
import unicodedata

RADICE = os.path.dirname(os.path.abspath(__file__))
CLZ = os.path.join(os.path.dirname(RADICE), "CLZ")

# Per ogni collezione: file di destinazione, collezione CLZ da unire, riga di commento iniziale.
CONVERSIONI = {
    "CLZ-Maschili.gbd": ("nomi_maschili.txt", "CLZ-Maschili.json", "Nomi maschili dei giocatori"),
    "CLZ-Femminili.gbd": ("nomi_femminili.txt", "CLZ-Femminili.json", "Nomi femminili delle giocatrici"),
    "CLZ-Cognomi.gbd": ("cognomi.txt", "CLZ-Cognomi.json", "Cognomi"),
    "CLZ-visi_m.gbd": (os.path.join("descrizioni", "visi_m.txt"), None, "Visi maschili"),
    "CLZ-visi_f.gbd": (os.path.join("descrizioni", "visi_f.txt"), None, "Visi femminili"),
    "CLZ-occhi_t.gbd": (os.path.join("descrizioni", "occhi.txt"), None, "Occhi"),
    "CLZ-nasi_t.gbd": (os.path.join("descrizioni", "nasi.txt"), None, "Nasi"),
    "CLZ-bocca_t.gbd": (os.path.join("descrizioni", "bocche.txt"), None, "Bocche"),
    "CLZ-taglio_capelli_m.gbd": (os.path.join("descrizioni", "tagli_capelli_m.txt"), None, "Tagli di capelli maschili"),
    "CLZ-taglio_capelli_f.gbd": (os.path.join("descrizioni", "tagli_capelli_f.txt"), None, "Tagli di capelli femminili"),
    "CLZ-colori_capelli_t.gbd": (os.path.join("descrizioni", "colori_capelli.txt"), None, "Colori dei capelli"),
}
NOTA_NOMI = "una voce per riga. Si possono aggiungere righe con un editor: il gioco le legge a ogni avvio. Le righe che iniziano con il cancelletto sono commenti."
NOTA_DESCRIZIONI = "una frase per riga, materiale di partenza per il vocabolario grammaticale. Le righe che iniziano con il cancelletto sono commenti."


def chiave_ordine(testo):
    """Ordine alfabetico che mette le lettere accentate accanto a quelle semplici."""
    scomposto = unicodedata.normalize("NFD", testo.casefold())
    return "".join(c for c in scomposto if not unicodedata.combining(c)), testo


def leggi_txt(percorso):
    with open(percorso, encoding="utf-8") as f:
        return [r.strip() for r in f if r.strip() and not r.lstrip().startswith("#")]


def main():
    mancanti = [g for g in CONVERSIONI if not os.path.exists(os.path.join(RADICE, g))]
    if len(mancanti) == len(CONVERSIONI):
        print("Nessun file .gbd da convertire: la conversione è già stata fatta.")
        return 0
    if mancanti:
        print(f"Mancano {len(mancanti)} file .gbd su {len(CONVERSIONI)}: {', '.join(mancanti)}. Non converto nulla.")
        return 1
    fatti = []
    for gbd, (destinazione, json_clz, titolo) in CONVERSIONI.items():
        with open(os.path.join(RADICE, gbd), "rb") as f:
            voci = [str(v).strip() for v in pickle.load(f) if str(v).strip()]
        aggiunte = 0
        if json_clz and os.path.exists(os.path.join(CLZ, json_clz)):
            with open(os.path.join(CLZ, json_clz), encoding="utf-8") as f:
                da_clz = [str(v).strip() for v in json.load(f) if str(v).strip()]
            aggiunte = len(set(da_clz) - set(voci))
            voci += da_clz
        voci = sorted(set(voci), key=chiave_ordine)
        percorso = os.path.join(RADICE, "dati", destinazione)
        os.makedirs(os.path.dirname(percorso), exist_ok=True)
        nota = NOTA_DESCRIZIONI if json_clz is None else NOTA_NOMI
        with open(percorso, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"# {titolo} di Showdown: {nota}\n")
            f.write("\n".join(voci) + "\n")
        if set(leggi_txt(percorso)) != set(voci):
            print(f"Errore: {destinazione} riletto non coincide con {gbd}. Mi fermo senza cancellare nulla.")
            return 1
        fatti.append(gbd)
        extra = f", di cui {aggiunte} prese da CLZ" if aggiunte else ""
        print(f"{gbd}: {len(voci)} voci in dati/{destinazione.replace(os.sep, '/')}{extra}.")
    for gbd in fatti:
        os.remove(os.path.join(RADICE, gbd))
    print(f"Conversione completata: {len(fatti)} file .gbd cancellati.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
