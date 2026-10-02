"""
Banco di prova del motore di partita di MESS, tappa 1 del piano di sviluppo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Simula in memoria alcune centinaia di partite fra i giocatori del mondo salvato, oppure di un
mondo generato apposta, e conta come finiscono i punti, quanto durano scambi e set e quanto
spesso vince il favorito. Non scrive nulla: il salvataggio dei giocatori si legge in sola
lettura, e la funzione che a fine partita aggiorna esperienza, statistiche e infortuni viene
sostituita da una che non fa niente. Servirà di nuovo alla tappa 8, per confrontare il motore
prima e dopo la revisione.
Uso, dalla cartella del progetto o da qualunque altra:
    python strumenti/banco_partite.py
    python strumenti/banco_partite.py --partite 1000 --set 5 --seme 42
    python strumenti/banco_partite.py --mondo nuovo --giocatori 250
    python strumenti/banco_partite.py --rapporto banco_prima.txt
"""

import argparse
import contextlib
import datetime
import io
import pickle
import random
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
FILE_GIOCATORI = RADICE / "sd-players.db"

# Le sole classi che il lettore dei vecchi salvataggi accetta di ricostruire.
CLASSI_AMMESSE = {
    ("__main__", "Giocatore"),
    ("sd", "Giocatore"),
    ("__main__", "Polisportiva"),
    ("sd", "Polisportiva"),
    ("datetime", "datetime"),
    ("datetime", "date"),
    ("datetime", "timedelta"),
    ("builtins", "set"),
    ("builtins", "frozenset"),
}

# Le azioni del motore, nell'ordine in cui avvengono in uno scambio.
AZIONI = ("Battuta", "Attacco", "Difesa", "Blocco", "Controllo")
ESITI_DADO = ("FalloCritico", "Fallo", "Successo", "Perfetto")

# Le fasce di distacco fra i due indici di valore, per misurare quanto conta essere favoriti.
FASCE_DISTACCO = ((0.05, "meno del 5 per cento"), (0.15, "fra il 5 e il 15 per cento"), (0.30, "fra il 15 e il 30 per cento"), (None, "oltre il 30 per cento"))


def importa_sd():
    """Importa il vecchio sd.py zittendo le stampe che fa all'importazione, problema P10 del piano."""
    if str(RADICE) not in sys.path:
        sys.path.insert(0, str(RADICE))
    with contextlib.redirect_stdout(io.StringIO()):
        import sd
    return sd


class LettoreVecchiSalvataggi(pickle.Unpickler):
    """
    Rilegge i .db del vecchio sd.py, che registrano le classi come appartenenti a __main__,
    problema P2 del piano: le riporta al modulo sd, e rifiuta qualunque classe fuori dalla
    lista, così un file costruito apposta non può eseguire nulla.
    """

    def __init__(self, file, sd):
        super().__init__(file)
        self.sd = sd

    def find_class(self, module, name):
        if (module, name) not in CLASSI_AMMESSE:
            raise pickle.UnpicklingError(f"Classe non ammessa nel salvataggio: {module}.{name}")
        if module in ("__main__", "sd"):
            return getattr(self.sd, name)
        return super().find_class(module, name)


def carica_mondo_salvato(sd):
    with FILE_GIOCATORI.open("rb") as f:
        giocatori = LettoreVecchiSalvataggi(f, sd).load()
    return {gid: g for gid, g in giocatori.items() if isinstance(gid, int)}


def genera_mondo_nuovo(sim, quanti):
    """Popola il simulatore con giocatori nuovi, creati dal generatore del vecchio sd.py."""
    sim.giocatori = {}
    sim.nuovi_giocatori_sessione = []
    # La data di creazione non conta per il banco, perché l'età si estrae a parte, e resta
    # senza fuso come tutte le date del vecchio motore, con cui potrebbe essere confrontata.
    with contextlib.redirect_stdout(io.StringIO()):
        sim._crea_giocatori_casuali(quanti, datetime.datetime.min)  # noqa: DTZ901
    return sim.giocatori


def numero(valore, decimali=1):
    return f"{valore:.{decimali}f}".replace(".", ",")


def percentuale(parte, totale):
    if not totale:
        return "nessuno"
    return f"{numero(100 * parte / totale)} per cento"


class Banco:
    """I contatori del banco e gli involucri che li alimentano, messi attorno ai metodi del motore."""

    def __init__(self, sd, sim):
        self.sd = sd
        self.sim = sim
        self.esiti_dado = Counter()
        self.somme_soglia = Counter()
        self.soglie_al_minimo = Counter()
        self.fine_punto = Counter()
        self.goal_dopo_scambio = 0
        self.attacchi_per_punto = []
        self.punteggi_set = []
        self.punti_giocati_per_set = []
        self.partite = []
        self._attacchi_punto = 0
        self._ultimo_esito = None
        self._punti_giocati = 0
        sim._risolvi_azione_vs_dado = self._involucro_dado(sim._risolvi_azione_vs_dado)
        sim._gioca_punto = self._involucro_punto(sim._gioca_punto)
        sim._gioca_set = self._involucro_set(sim._gioca_set)
        sim._aggiorna_statistiche_post_partita = self._nessun_aggiornamento

    @staticmethod
    def _nessun_aggiornamento(*_args, **_kwargs):
        """Al posto dell'aggiornamento di fine partita: niente esperienza, statistiche o infortuni."""

    def _soglia_di_successo(self, giocatore_dif, valore_azione):
        """
        Ricalcola la soglia che _risolvi_azione_vs_dado usa senza restituirla. È una copia della
        formula del vecchio motore, che il banco osserva e non cambia: alla tappa 8 va adattata.
        """
        sd = self.sd
        capacita = giocatore_dif.indice_collettivo_valore * sd.SCALING_K_DIFESA_ICV
        meta_intervallo = sd.SCALING_RANGE_DELTA_EFF / 2.0
        delta_norm = max(-1.0, min(1.0, (valore_azione - capacita) / meta_intervallo)) if meta_intervallo else 0.0
        soglia = max(5.0, min(95.0, sd.SCALING_SOGLIA_BASE + delta_norm * sd.SCALING_MODIFICATORE_MAX))
        return capacita, soglia, delta_norm <= -1.0

    def _involucro_dado(self, originale):
        def dado(giocatore_att, giocatore_dif, valore_azione, azione_descr, debug_log=None):
            esito, tiro = originale(giocatore_att, giocatore_dif, valore_azione, azione_descr, debug_log)
            azione = azione_descr.split()[0]
            capacita, soglia, al_minimo = self._soglia_di_successo(giocatore_dif, valore_azione)
            self.esiti_dado[azione, esito] += 1
            self.somme_soglia[azione, "tiri"] += 1
            self.somme_soglia[azione, "valore"] += valore_azione
            self.somme_soglia[azione, "capacita"] += capacita
            self.somme_soglia[azione, "soglia"] += soglia
            if al_minimo:
                self.soglie_al_minimo[azione] += 1
            if azione == "Attacco":
                self._attacchi_punto += 1
            self._ultimo_esito = esito
            return esito, tiro

        return dado

    def _involucro_punto(self, originale):
        def punto(*args, **kwargs):
            self._attacchi_punto = 0
            self._ultimo_esito = None
            vincitore, tipo, dettaglio = originale(*args, **kwargs)
            self._punti_giocati += 1
            self.attacchi_per_punto.append(self._attacchi_punto)
            self.fine_punto[self._classifica(tipo, dettaglio or "")] += 1
            if tipo == "Goal" and self._attacchi_punto >= 2:
                self.goal_dopo_scambio += 1
            return vincitore, tipo, dettaglio

        return punto

    def _classifica(self, tipo, dettaglio):
        """Dice come è finito il punto, ricavandolo dal dettaglio che il motore restituisce."""
        if tipo == "PallaMorta":
            if self._ultimo_esito == "Successo":
                return "palla morta, attacco e difesa troppo vicini"
            return "palla morta, azione fallita"
        if tipo == "Goal":
            if dettaglio.startswith("Ace Battuta"):
                return "goal, ace di battuta"
            if dettaglio.startswith("Attacco Perfetto"):
                return "goal, attacco con tiro perfetto"
            return "goal, attacco che supera la difesa"
        fase = "in battuta" if dettaglio.startswith("Fallo Battuta") else "nello scambio"
        if "FalloCritico" in dettaglio:
            causa = "per tiro critico sotto il 5"
        elif "Normale" in dettaglio:
            causa = "per azione fallita"
        elif dettaglio == "Limite Scambi":
            causa = "assegnato a caso al limite dei 50 scambi"
        elif dettaglio.startswith("Errore"):
            causa = "per errore di flusso del motore"
        else:
            causa = "per tiro fra la soglia e il 95"
        return f"fallo {fase}, {causa}"

    def _involucro_set(self, originale):
        def gioca_set(*args, **kwargs):
            inizio = self._punti_giocati
            punteggio, vincitore = originale(*args, **kwargs)
            self.punteggi_set.append(punteggio)
            self.punti_giocati_per_set.append(self._punti_giocati - inizio)
            return punteggio, vincitore

        return gioca_set

    def gioca(self, id1, id2, num_set):
        g1 = self.sim.giocatori[id1]
        g2 = self.sim.giocatori[id2]
        with contextlib.redirect_stdout(io.StringIO()):
            risultato = self.sim.gioca_partita(id1, id2, num_set)
        if risultato.get("error"):
            raise RuntimeError(f"Partita {id1} contro {id2} non giocata: {risultato['error']}")
        set_vinti_1 = sum(1 for a, b in risultato["punteggio_set"] if a > b)
        set_vinti_2 = len(risultato["punteggio_set"]) - set_vinti_1
        self.partite.append({
            "icv": (g1.indice_collettivo_valore, g2.indice_collettivo_valore),
            "vince_il_primo": risultato["vincitore_id"] == id1,
            "set": (max(set_vinti_1, set_vinti_2), min(set_vinti_1, set_vinti_2)),
        })


def distacco(partita):
    """Di quanto l'indice di valore del favorito supera quello dell'altro, in proporzione."""
    alto, basso = max(partita["icv"]), min(partita["icv"])
    return (alto - basso) / max(1.0, basso)


def descrivi_contatore(contatore, totale, chiavi=None):
    """Una riga discorsiva per un contatore: voce, quantità e percentuale, dalla più frequente."""
    voci = chiavi or [k for k, _ in contatore.most_common()]
    return "; ".join(f"{k}: {contatore[k]}, {percentuale(contatore[k], totale)}" for k in voci if contatore[k])


def rapporto(banco, intestazione):
    righe = list(intestazione)
    fine = banco.fine_punto
    giocati = sum(fine.values())
    morte = sum(n for k, n in fine.items() if k.startswith("palla morta"))
    goal = sum(n for k, n in fine.items() if k.startswith("goal"))
    falli = sum(n for k, n in fine.items() if k.startswith("fallo"))
    assegnati = goal + falli
    righe.append(f"Punti giocati {giocati}: {assegnati} assegnati e {morte} palle morte, che si ripetono.")
    righe.append(f"Dei punti assegnati, {goal} sono goal, {percentuale(goal, assegnati)}, e {falli} sono falli, {percentuale(falli, assegnati)}.")
    righe.append("Come nascono i goal: " + descrivi_contatore(Counter({k[6:]: n for k, n in fine.items() if k.startswith("goal")}), goal) + ".")
    righe.append(f"Goal arrivati dopo almeno due attacchi, cioè da uno scambio vero: {banco.goal_dopo_scambio}, {percentuale(banco.goal_dopo_scambio, goal)} dei goal.")
    righe.append("Come nascono i falli: " + descrivi_contatore(Counter({k[6:]: n for k, n in fine.items() if k.startswith("fallo")}), falli) + ".")
    if morte:
        righe.append("Come nascono le palle morte: " + descrivi_contatore(Counter({k[13:]: n for k, n in fine.items() if k.startswith("palla morta")}), morte) + ".")
    attacchi = Counter()
    for n in banco.attacchi_per_punto:
        if n == 0:
            attacchi["finito sulla battuta"] += 1
        elif n == 1:
            attacchi["un attacco"] += 1
        elif n == 2:
            attacchi["due attacchi"] += 1
        elif n <= 5:
            attacchi["da tre a cinque attacchi"] += 1
        else:
            attacchi["oltre cinque attacchi"] += 1
    ordine_attacchi = ["finito sulla battuta", "un attacco", "due attacchi", "da tre a cinque attacchi", "oltre cinque attacchi"]
    righe.append(f"Lunghezza degli scambi: in media {numero(statistics.fmean(banco.attacchi_per_punto), 2)} attacchi per punto, al massimo {max(banco.attacchi_per_punto)}.")
    righe.append("Punti per numero di attacchi: " + descrivi_contatore(attacchi, giocati, ordine_attacchi) + ".")
    for azione in AZIONI:
        tiri = banco.somme_soglia[azione, "tiri"]
        if not tiri:
            continue
        esiti = ", ".join(f"{e} {percentuale(banco.esiti_dado[azione, e], tiri)}" for e in ESITI_DADO)
        valore = banco.somme_soglia[azione, "valore"] / tiri
        capacita = banco.somme_soglia[azione, "capacita"] / tiri
        soglia = banco.somme_soglia[azione, "soglia"] / tiri
        righe.append(
            f"Dado di {azione}, {tiri} tiri: {esiti}. Valore medio dell'azione {numero(valore)} contro una capacità difensiva media di {numero(capacita)}; "
            f"soglia di successo media {numero(soglia)}, al minimo di 10 nel {percentuale(banco.soglie_al_minimo[azione], tiri)} dei tiri."
        )
    set_totali = len(banco.punteggi_set)
    al_limite = sum(1 for a, b in banco.punteggi_set if max(a, b) >= banco.sd.PUNTI_LIMITE_SET and abs(a - b) < banco.sd.PUNTI_VANTAGGIO_NECESSARI)
    ai_vantaggi = sum(1 for a, b in banco.punteggi_set if min(a, b) >= banco.sd.PUNTI_VITTORIA_SET_BASE - 1)
    righe.append(f"Set giocati {set_totali}, in media {numero(statistics.fmean(banco.punti_giocati_per_set))} punti giocati per set.")
    righe.append(f"Set arrivati ai vantaggi, con entrambi almeno a {banco.sd.PUNTI_VITTORIA_SET_BASE - 1}: {ai_vantaggi}, {percentuale(ai_vantaggi, set_totali)}. Chiusi dal limite dei {banco.sd.PUNTI_LIMITE_SET} punti senza due di scarto: {al_limite}, {percentuale(al_limite, set_totali)}.")
    punteggi = Counter(f"{max(a, b)} a {min(a, b)}" for a, b in banco.punteggi_set)
    righe.append("Punteggi di set più frequenti: " + descrivi_contatore(Counter(dict(punteggi.most_common(6))), set_totali) + ".")
    partite = banco.partite
    risultati = Counter(f"{a} a {b}" for a, b in (p["set"] for p in partite))
    righe.append(f"Partite giocate {len(partite)}. Risultati in set: " + descrivi_contatore(risultati, len(partite)) + ".")
    con_favorito = [p for p in partite if p["icv"][0] != p["icv"][1]]
    vinte_favorito = sum(1 for p in con_favorito if p["vince_il_primo"] == (p["icv"][0] > p["icv"][1]))
    righe.append(f"Il favorito, cioè il giocatore con l'indice di valore più alto, vince {vinte_favorito} partite su {len(con_favorito)}, {percentuale(vinte_favorito, len(con_favorito))}.")
    minimo = 0.0
    for limite, nome in FASCE_DISTACCO:
        massimo = limite if limite is not None else float("inf")
        nella_fascia = [p for p in con_favorito if minimo <= distacco(p) < massimo]
        vinte = sum(1 for p in nella_fascia if p["vince_il_primo"] == (p["icv"][0] > p["icv"][1]))
        minimo = massimo
        if nella_fascia:
            righe.append(f"Con un distacco {nome}: {len(nella_fascia)} partite, il favorito ne vince {vinte}, {percentuale(vinte, len(nella_fascia))}.")
    return righe


def main():
    parser = argparse.ArgumentParser(description="Banco di prova del motore di partita di MESS: simula partite in memoria, senza scrivere nulla.")
    parser.add_argument("--partite", type=int, default=300, help="quante partite simulare, 300 se non indicato")
    parser.add_argument("--set", type=int, choices=(3, 5), default=3, help="partite al meglio dei 3 o dei 5 set, 3 se non indicato")
    parser.add_argument("--mondo", choices=("salvato", "nuovo"), default="salvato", help="i giocatori del mondo salvato, oppure un mondo generato apposta")
    parser.add_argument("--giocatori", type=int, default=250, help="quanti giocatori generare con --mondo nuovo, 250 se non indicato")
    parser.add_argument("--seme", type=int, default=None, help="il seme del generatore casuale, per ripetere una prova identica")
    parser.add_argument("--rapporto", type=Path, default=None, help="salva il rapporto anche in questo file")
    argomenti = parser.parse_args()
    seme = argomenti.seme if argomenti.seme is not None else random.randrange(1_000_000)
    random.seed(seme)
    sd = importa_sd()
    sim = sd.Simulatore.__new__(sd.Simulatore)
    if argomenti.mondo == "salvato":
        sim.giocatori = carica_mondo_salvato(sd)
        descrizione_mondo = f"Mondo salvato in {FILE_GIOCATORI.name}"
    else:
        genera_mondo_nuovo(sim, argomenti.giocatori)
        descrizione_mondo = "Mondo generato apposta dal vecchio generatore"
    disponibili = [gid for gid, g in sim.giocatori.items() if not g.ritirato and not g.infortunato]
    if len(disponibili) < 2:
        sys.exit("Servono almeno due giocatori non ritirati e non infortunati.")
    indici = sorted(sim.giocatori[gid].indice_collettivo_valore for gid in disponibili)
    banco = Banco(sd, sim)
    inizio = time.perf_counter()
    for _ in range(argomenti.partite):
        id1, id2 = random.sample(disponibili, 2)
        banco.gioca(id1, id2, argomenti.set)
    durata = time.perf_counter() - inizio
    intestazione = [
        f"Banco di prova del motore di partita, sd.py versione {sd.VERSIONE}, {time.strftime('%Y-%m-%d %H:%M')}.",
        f"{descrizione_mondo}: {len(sim.giocatori)} giocatori, {len(disponibili)} disponibili, cioè non ritirati e non infortunati.",
        f"Indice di valore dei disponibili: minimo {numero(indici[0], 0)}, mediana {numero(statistics.median(indici), 0)}, massimo {numero(indici[-1], 0)}.",
        f"{argomenti.partite} partite al meglio dei {argomenti.set} set fra coppie estratte a caso, giocate in {numero(durata)} secondi, con il seme {seme}: per ripetere la prova identica si aggiunge --seme {seme}.",
    ]
    righe = rapporto(banco, intestazione)
    testo = "\n".join(righe)
    print(testo)
    if argomenti.rapporto:
        argomenti.rapporto.write_text(testo + "\n", encoding="utf-8")
        print(f"Rapporto salvato in {argomenti.rapporto}.")


if __name__ == "__main__":
    main()
