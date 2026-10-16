"""Sentinella del flusso finale della tappa 12: ogni minuto guarda il registro del workflow e i commit
del ramo, stampa una riga per ogni fase che comincia o finisce e per ogni commit nuovo, e dopo 29
minuti senza notizie stampa uno stato breve ed esce, perché il monitor va riarmato."""

import json
import subprocess
import sys
import time
from pathlib import Path

GIORNALE = Path(r"C:\Users\Gabriele\.claude\projects\E--git\27fed563-c373-4641-9680-74975b271914\subagents\workflows\wf_8d769798-6fc\journal.jsonl")
WORKTREE = r"C:\Users\Gabriele\AppData\Local\Temp\claude\E--git\27fed563-c373-4641-9680-74975b271914\scratchpad\showdown-tappa12"
DURATA = 29 * 60
PAUSA = 60


def righe_giornale():
    try:
        return GIORNALE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []


def commit_del_ramo():
    try:
        esito = subprocess.run(["git", "-C", WORKTREE, "log", "--format=%h %s", "-n", "200"], capture_output=True, text=True, encoding="utf-8", timeout=30)
        return esito.stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        return []


def di(voce, etichette):
    return etichette.get(voce.get("key", ""), voce.get("label", "una fase"))


def main():
    etichette = {}
    righe = righe_giornale()
    for riga in righe:
        voce = json.loads(riga)
        if voce.get("type") == "started":
            etichette[voce["key"]] = voce["label"]
    # Lo stato si ricorda fra un'accensione e l'altra, così niente si perde nell'intervallo.
    stato = Path(__file__).with_name("sentinella_stato.json")
    try:
        ricordo = json.loads(stato.read_text(encoding="utf-8"))
        visti = ricordo["visti"]
        commit_visti = set(ricordo["commit"])
    except (OSError, ValueError, KeyError):
        visti = len(righe)
        commit_visti = set(commit_del_ramo())

    def ricorda():
        stato.write_text(json.dumps({"visti": visti, "commit": sorted(commit_visti)}, ensure_ascii=False), encoding="utf-8")

    ricorda()
    fase_attuale = "nessuna"
    for riga in righe:
        voce = json.loads(riga)
        if voce.get("type") == "started":
            fase_attuale = voce["label"]
    inizio = time.monotonic()
    notizie = 0
    while time.monotonic() - inizio < DURATA:
        time.sleep(PAUSA)
        righe = righe_giornale()
        for riga in righe[visti:]:
            try:
                voce = json.loads(riga)
            except ValueError:
                continue
            tipo = voce.get("type")
            if tipo == "started":
                etichette[voce["key"]] = voce["label"]
                fase_attuale = voce["label"]
                print(f"Comincia la fase {voce['label']}.", flush=True)
                notizie += 1
            elif tipo == "result":
                print(f"Finita la fase {di(voce, etichette)}.", flush=True)
                notizie += 1
            elif tipo not in ("launched",):
                print(f"Evento {tipo} nella fase {di(voce, etichette)}.", flush=True)
                notizie += 1
        visti = len(righe)
        attuali = commit_del_ramo()
        nuovi = [c for c in attuali if c not in commit_visti]
        for c in reversed(nuovi):
            print(f"Commit {c[:150]}", flush=True)
            notizie += 1
        commit_visti.update(attuali)
        ricorda()
        if notizie:
            # Si esce alla prima notizia: la fine del monitor è l'avviso che arriva di sicuro, e lo si riarma.
            sys.exit(0)
    if notizie == 0:
        print(f"Stato: nessuna novità nell'ultima mezz'ora, lavora la fase {fase_attuale}.", flush=True)
    sys.exit(0)


main()
