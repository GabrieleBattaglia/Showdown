"""
Il banco dei tornei di MESS: migliaia di tornei a caso, giocati dal motore dei tornei senza il mondo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-13 con la tappa 12, punto 4.15 del progetto, perché Terminal Beast non aveva nessuna
prova dei suoi tornei, difetto 22. Ogni torneo ha una formula valida estratta a caso fra quelle che
l'editor accetta, da 4 iscritti al tetto, con club a caso, forze a caso e risultati che seguono la
forza, con ritiri, tavolini e tavolini doppi. Per ogni torneo controlla che ogni incontro si giochi
una volta, che nessuno giochi due volte nello stesso turno, che il vincitore non abbia mai perso nel
tabellone, che la classifica finale sia una permutazione degli iscritti, che i giorni stiano nella
durata prevista e che i premi non superino il montepremi. Misura quante volte le prime due teste di
serie arrivano in finale e quante volte due compagni di club restano nello stesso girone, anche
contro la serpentina senza la separazione, sugli stessi iscritti. Non scrive niente nel progetto,
salvo il rapporto quando lo si chiede.
Uso, dalla cartella del progetto o da qualunque altra:
    python strumenti/banco_tornei.py
    python strumenti/banco_tornei.py --tornei 20000 --seme 3 --rapporto
"""

import argparse
import dataclasses
import math
import random
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))

import formule  # noqa: E402
import modelli_torneo  # noqa: E402
import percorsi  # noqa: E402
import tornei  # noqa: E402
from modelli_torneo import ModelloTorneo  # noqa: E402

RAPPORTO_PREDEFINITO = RADICE / "strumenti" / "banco_tornei.txt"
# Il tetto più alto delle formule a caso: oltre, un torneo da centinaia d'iscritti rallenta il banco senza aggiungere casi nuovi.
TETTO_MASSIMO = 128
# Le probabilità degli esiti che non sono regolari, per incontro.
TAVOLINO_DOPPIO = 0.005
TAVOLINO = 0.02
RITIRO = 0.015
# La forza: una gaussiana, e la pendenza della vittoria per punto di distacco.
FORZA_MEDIA, FORZA_DEVIAZIONE = 100.0, 20.0
PENDENZA = 0.06
# Quanto pesa ogni scelta nella formula a caso.
PESI_DELLE_SCELTE = {"tabellone": 3.0, "gironi": 2.0, "unico": 1.0}


def numero(valore, decimali=1):
    return f"{valore:.{decimali}f}".replace(".", ",")


def _divisori_di_gironi(n):
    """Le grandezze di girone ammesse per n partecipanti: da 2 a 12 componenti, divisori di n."""
    return [s for s in range(formule.COMPONENTI_MINIMI, formule.COMPONENTI_MASSIMI + 1) if n % s == 0]


def _fasi_da(n, rng, rimaste):
    """Le fasi di una formula da n partecipanti in poi, in al massimo rimaste fasi; None se non ci si arriva."""
    if rimaste <= 0:
        return None
    potenza = formule.potenza_di_due(n)
    scelte = []
    if potenza and n >= 2:
        scelte.append("tabellone")
    if n <= formule.COMPONENTI_MASSIMI:
        scelte.append("unico")
    if any(s < n for s in _divisori_di_gironi(n)):
        scelte.append("gironi")
    # Il tabellone pesa di più, il girone unico di meno, perché la maggior parte dei tornei finisca con una finale, come nel calendario vero.
    scelte.sort(key=lambda scelta: -rng.random() * PESI_DELLE_SCELTE[scelta])
    for scelta in scelte:
        if scelta == "unico":
            return [{"tipo": "gironi", "partecipanti": n, "gironi": 1, "promossi": rng.randrange(n), "finalina": False}]
        if scelta == "tabellone":
            if n == 2:
                return [{"tipo": "tabellone", "partecipanti": 2, "gironi": 0, "promossi": 0, "finalina": False}]
            if n == 4 and rng.random() < 0.6:
                return [{"tipo": "tabellone", "partecipanti": 4, "gironi": 0, "promossi": 0, "finalina": True},
                        {"tipo": "tabellone", "partecipanti": 2, "gironi": 0, "promossi": 0, "finalina": False}]
            seguito = _fasi_da(n // 2, rng, rimaste - 1)
            if seguito is not None:
                return [{"tipo": "tabellone", "partecipanti": n, "gironi": 0, "promossi": 0, "finalina": False}, *seguito]
            continue
        grandezze = [s for s in _divisori_di_gironi(n) if s < n]
        grandezza = rng.choice(grandezze)
        quanti = n // grandezza
        promossi = rng.randint(1, grandezza - 1)
        if quanti * promossi < 2:
            continue
        seguito = _fasi_da(quanti * promossi, rng, rimaste - 1)
        if seguito is not None:
            return [{"tipo": "gironi", "partecipanti": n, "gironi": quanti, "promossi": promossi, "finalina": False}, *seguito]
    return None


def formula_a_caso(rng, numero_formula):
    """Una formula valida a caso, fra quelle che l'editor accetta, con un tetto da 4 a TETTO_MASSIMO."""
    while True:
        if rng.random() < 0.35:
            tetto = 2 ** rng.randint(2, int(math.log2(TETTO_MASSIMO)))
        else:
            grandezza = rng.randint(3, 6)
            tetto = grandezza * rng.randint(1, TETTO_MASSIMO // grandezza)
        if tetto < 4:
            continue
        fasi = _fasi_da(tetto, rng, formule.FASI_MASSIME)
        if fasi is None:
            continue
        formula = {"id": f"banco_{numero_formula}", "nome": f"Formula del banco {numero_formula}", "descrizione": "", "fasi": fasi}
        if formule.valida_formula(formula) is None:
            return formula


def modello_a_caso(rng, formula):
    tetto = formule.tetto(formula)
    finali = [f for f in modelli_torneo.FINALI_DA if f <= tetto]
    return ModelloTorneo(id="modello_1", nome="Modello del banco", formula=formula["id"], set_al_meglio=rng.choice((3, 5)), set_finali=rng.choice((3, 5)),
                         finali_da=rng.choice(finali), incontri_al_giorno=rng.randint(1, 4), quota_iscrizione=rng.choice((0, 10, 25)),
                         contributo_federazione=rng.choice((0.0, 1.0, 2.5)), montepremi_minimo=rng.choice((0, 0, 500)), posti_premiati=rng.randint(1, tetto),
                         pendenza_premi=round(rng.uniform(1.0, 3.0), 3))


def iscritti_a_caso(rng, quanti):
    """Gli iscritti: forza a caso, il club per otto su dieci da un gruppo di club, gli altri liberi, e la quota per chi ha un club."""
    club = [{"nome": f"Club {n}", "fondazione": f"2030-01-{1 + n % 28:02d}"} for n in range(max(2, quanti // 6))]
    info = {}
    for gid in range(1, quanti + 1):
        suo = rng.choice(club) if rng.random() < 0.8 else None
        info[gid] = {"nome": f"Giocatore {gid}", "sesso": "m", "club": suo, "forza": rng.gauss(FORZA_MEDIA, FORZA_DEVIAZIONE), "pagato": 10 if suo else 0}
    return info


def gioca_dalla_forza(torneo):
    """I risultati che seguono la forza, col caso del seme dell'incontro, con ritiri, tavolini e tavolini doppi."""
    def gioca(incontro, _azioni):
        rng = random.Random(incontro.seme)
        necessari = incontro.set_al_meglio // 2 + 1
        vince_a = rng.random() < 1.0 / (1.0 + math.exp(-PENDENZA * (torneo.forza(incontro.a) - torneo.forza(incontro.b))))
        tiro = rng.random()
        if tiro < TAVOLINO_DOPPIO:
            return {"esito": "tavolino_doppio", "vince": None, "set": [], "set_giocati": 0}
        if tiro < TAVOLINO_DOPPIO + TAVOLINO:
            return {"esito": "tavolino", "vince": "A" if vince_a else "B", "set": [[11, 0] if vince_a else [0, 11]] * necessari, "set_giocati": 0}
        persi = rng.randrange(necessari)
        sets = [[rng.randint(3, 9), 11] if vince_a else [11, rng.randint(3, 9)] for _ in range(persi)]
        sets += [[11, rng.randint(3, 9)] if vince_a else [rng.randint(3, 9), 11] for _ in range(necessari)]
        if incontro.set_al_meglio == tornei.SET_SQUADRE:
            sets = [[31, 25] if vince_a else [25, 31]]
        if tiro < TAVOLINO_DOPPIO + TAVOLINO + RITIRO and len(sets) > 1:
            return {"esito": "ritiro", "vince": "A" if vince_a else "B", "set": sets, "set_giocati": len(sets) - 1}
        return {"esito": "regolare", "vince": "A" if vince_a else "B", "set": sets, "set_giocati": len(sets)}
    return gioca


def _compagni_insieme(gironi, club_di):
    """Quante coppie di compagni di club stanno nello stesso girone."""
    coppie = 0
    for ids in gironi:
        chiavi = [club_di(g) for g in ids if club_di(g) is not None]
        coppie += sum(chiavi.count(k) * (chiavi.count(k) - 1) // 2 for k in set(chiavi))
    return coppie


def controlla(torneo, giorni, durata):
    """Le violazioni di un torneo giocato, in frasi: una lista vuota se è tutto in regola."""
    errori = []
    incontri = torneo.incontri()
    ids = [i.id for i in incontri]
    if len(ids) != len(set(ids)) or any(i.esito is None for i in incontri):
        errori.append("un incontro non si è giocato, o si è giocato due volte")
    for fase in torneo.fasi:
        for turno in range(1, fase.turni + 1):
            presenti = [g for i in fase.del_turno(turno) for g in (i.a, i.b) if g is not None]
            if len(presenti) != len(set(presenti)):
                errori.append(f"nella fase {fase.indice} qualcuno gioca due volte al turno {turno}")
    campione = torneo.classifica_finale[0] if torneo.classifica_finale else None
    for fase in torneo.fasi:
        if fase.tipo == formule.TABELLONE:
            for incontro in fase.incontri:
                if campione in (incontro.a, incontro.b) and not incontro.finalina and torneo.vincitore(incontro) != campione:
                    errori.append("il vincitore ha perso nel tabellone")
    if sorted(torneo.classifica_finale) != sorted(torneo.iscritti):
        errori.append("la classifica finale non è una permutazione degli iscritti")
    if giorni > durata:
        errori.append(f"{giorni} giorni di gioco, oltre la durata prevista di {durata}")
    paganti = sum(1 for dati in torneo.info.values() if dati.get("pagato", 0) > 0)
    if sum(torneo.premi.values()) > tornei.montepremi(torneo.modello, paganti):
        errori.append("i premi superano il montepremi")
    return errori


def banco(quanti, seme, scrivi=print):
    """Gioca i tornei e restituisce le misure; scrivi riceve le righe del racconto."""
    rng = random.Random(f"banco-tornei-{seme}")
    inizio = time.perf_counter()
    misure = {"tornei": 0, "incontri": 0, "errori": [], "finali_con_le_teste": 0, "finali": 0, "vince_la_prima": 0, "compagni": 0, "compagni_senza": 0,
              "gironi": 0, "giorni": [], "esiti": dict.fromkeys(tornei.ESITI, 0), "iscritti": []}
    for numero_torneo in range(quanti):
        formula = formula_a_caso(rng, numero_torneo)
        modello = modello_a_caso(rng, formula)
        tetto = formule.tetto(formula)
        iscritti = rng.randint(min(4, tetto), tetto)
        info = iscritti_a_caso(rng, iscritti)
        torneo = tornei.Torneo(numero_torneo + 1, 1, 1, modello.a_dizionario(), formula, "2030-03-02", rng.getrandbits(32), info)
        gioca = gioca_dalla_forza(torneo)
        giorni = 0
        while torneo.stato == tornei.IN_CORSO:
            torneo.giornata(gioca, "2030-03-02")
            giorni += 1
        durata = modelli_torneo.durata_prevista(dataclasses.replace(modello, minimo_iscritti=iscritti), formula)
        for errore in controlla(torneo, giorni, durata):
            misure["errori"].append(f"torneo {numero_torneo + 1}, {iscritti} iscritti, formula {[(f['tipo'], f['partecipanti']) for f in formula['fasi']]}: {errore}")
        misure["tornei"] += 1
        misure["incontri"] += sum(1 for i in torneo.incontri() if i.esito != tornei.RIPOSO)
        misure["giorni"].append(giorni)
        misure["iscritti"].append(iscritti)
        for incontro in torneo.incontri():
            misure["esiti"][incontro.esito] += 1
        ultima = torneo.fasi[-1]
        if ultima.tipo == formule.TABELLONE and torneo.fasi[-1].grandezza >= 4 and len(torneo.iscritti) >= 4:
            finale = next(i for i in ultima.del_turno(ultima.turni) if not i.finalina)
            misure["finali"] += 1
            misure["finali_con_le_teste"] += {finale.a, finale.b} == set(torneo.iscritti[:2])
        misure["vince_la_prima"] += torneo.classifica_finale[0] == torneo.iscritti[0]
        for fase in torneo.fasi:
            if fase.tipo != formule.GIRONI or len(fase.gironi) < 2:
                continue
            gironi = list(fase.gironi.values())
            ordine = [g for posto in range(max(len(ids) for ids in gironi)) for g in torneo._per_forza([ids[posto] for ids in gironi if posto < len(ids)])]
            misure["gironi"] += len(gironi)
            misure["compagni"] += _compagni_insieme(gironi, torneo._club_di)
            misure["compagni_senza"] += _compagni_insieme(tornei.gironi_a_serpentina(ordine, len(gironi), lambda _g: None), torneo._club_di)
    misure["secondi"] = time.perf_counter() - inizio
    racconta(misure, seme, scrivi)
    return misure




def racconta(misure, seme, scrivi):
    scrivi(f"Banco dei tornei col seme {seme}: {misure['tornei']} tornei a caso, {misure['incontri']} incontri giocati, in {numero(misure['secondi'])} secondi.")
    scrivi(f"Iscritti per torneo da {min(misure['iscritti'])} a {max(misure['iscritti'])}, mediana {numero(statistics.median(misure['iscritti']), 0)}; "
           f"giorni di gioco da {min(misure['giorni'])} a {max(misure['giorni'])}, in media {numero(statistics.fmean(misure['giorni']))}.")
    esiti = misure["esiti"]
    scrivi("Gli esiti degli incontri: " + ", ".join(f"{nome.replace('_', ' ')} {quanti}" for nome, quanti in esiti.items()) + ".")
    if misure["errori"]:
        scrivi(f"Violazioni trovate: {len(misure['errori'])}. Le prime: " + "; ".join(misure["errori"][:10]) + ".")
    else:
        scrivi("Nessuna violazione: ogni incontro giocato una volta, nessuno due volte nello stesso turno, il vincitore mai sconfitto nel tabellone, "
               "la classifica finale una permutazione degli iscritti, i giorni nella durata prevista, i premi entro il montepremi.")
    if misure["finali"]:
        scrivi(f"Le prime due teste di serie arrivano in finale in {misure['finali_con_le_teste']} tornei su {misure['finali']} con la finale di un tabellone, "
               f"il {numero(100 * misure['finali_con_le_teste'] / misure['finali'])} per cento; la prima testa vince il {numero(100 * misure['vince_la_prima'] / misure['tornei'])} per cento dei tornei.")
    if misure["gironi"]:
        scrivi(f"Compagni di club nello stesso girone: {misure['compagni']} coppie in {misure['gironi']} gironi, contro {misure['compagni_senza']} con la serpentina "
               "senza la separazione, sugli stessi iscritti.")


def main():
    parser = argparse.ArgumentParser(description="Il banco dei tornei di MESS: tornei a caso giocati dal motore dei tornei, con i controlli e le misure.")
    parser.add_argument("--tornei", type=int, default=5000, help="quanti tornei, 5000 se non indicato")
    parser.add_argument("--seme", type=int, default=1, help="il seme del banco, 1 se non indicato")
    parser.add_argument("--rapporto", nargs="?", type=Path, const=RAPPORTO_PREDEFINITO, default=None, help="salva il racconto, in strumenti/banco_tornei.txt se non si dà un file")
    argomenti = parser.parse_args()
    righe = []

    def scrivi(riga):
        righe.append(riga)
        print(riga, flush=True)

    cartella = tempfile.mkdtemp(prefix="mess_banco_tornei_")
    vera = percorsi.cartella
    percorsi.cartella = lambda: cartella
    try:
        misure = banco(argomenti.tornei, argomenti.seme, scrivi)
    finally:
        percorsi.cartella = vera
        shutil.rmtree(cartella, ignore_errors=True)
    if argomenti.rapporto:
        argomenti.rapporto.write_text("\n".join(righe) + "\n", encoding="utf-8")
        print(f"Rapporto salvato in {argomenti.rapporto}.")
    sys.exit(1 if misure["errori"] else 0)


if __name__ == "__main__":
    main()
