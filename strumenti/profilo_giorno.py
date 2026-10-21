"""
Il profilo del motore e del giorno simulato di MESS, per la tappa 12.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-13 con il primo passo della tappa 12, punto 1.5 del progetto: misura in sola
lettura quanto costano un incontro, un giorno del mondo a regime e un salvataggio, e dove va il
tempo, perché il mondo che gioca stia nei tempi del giorno decisi con Gabriele. Non scrive niente
nel progetto: la cartella del programma si sposta in una cartella temporanea, che alla fine si
cancella, e il caso del mondo si rimette com'era.
Tre misure, ciascuna con la sua opzione, anche insieme.
Con --incontri il motore in modalità essenziale, al meglio dei 3 e dei 5 e nella gara a squadre,
sulla popolazione di prova del banco delle partite e su una popolazione del mondo sintetico a
regime, con i punti per incontro, gli attacchi per punto e il tempo; poi un profilo, con la quota
del tempo delle funzioni che pesano di più.
Con --giorno il giorno simulato di un mondo a regime di strumenti/mondi_sintetici.py, con tanti
attivi quanti ne dice --attivi, un terzo di ritirati e le polisportive del computer per nove
tesserati su dieci: la media, la mediana e il giorno peggiore di --giorni giorni, o di un anno di
calendario con --anno, e un profilo con la quota delle parti del giorno. Dal secondo passo della
tappa nel giorno ci saranno anche i tornei e le sfide. La verifica del 15 ottobre 2026 ha visto che
quel mondo non resta a regime: i contratti sono firmati tutti lo stesso giorno, le casse sono di
5.000 euro e non c'è palmarès, e in 210 giorni perde un quarto dei tesserati e gioca meno di un terzo
degli incontri di torneo del mondo vero all'anno 60. Serve a confrontare due versioni del codice sullo
stesso mondo; il tempo del giorno a regime si misura sui mondi che la prova lunga di
strumenti/simulazione_lunga.py salva con --salva-mondi, caricati come li carica il programma.
Con --salvataggio il salvataggio dello stesso mondo, diari compresi: comporre il documento,
scriverne il testo firmato e comprimerlo, come archivio.scrivi dalla decisione 4 di Gabriele del 14
ottobre 2026, con le grandezze; poi lo stesso con un albo d'oro di
sessant'anni costruito apposta, della forma decisa al punto 5.10 del progetto, voci corte e nomi
nelle tabelle, perché l'albo conserva tutto per sempre, risposta 13 di Gabriele.
Con --rapporto il racconto va anche in strumenti/profilo_tappa_12.txt, o nel file indicato; con --nota
si aggiungono righe proprie dopo l'intestazione, per esempio le misure prese prima di un cambiamento.
Uso, dalla cartella del progetto o da qualunque altra:
    python strumenti/profilo_giorno.py --incontri
    python strumenti/profilo_giorno.py --giorno --attivi 20600 --giorni 20
    python strumenti/profilo_giorno.py --incontri --giorno --salvataggio --attivi 20600 --rapporto
"""

import argparse
import cProfile
import datetime
import json
import platform
import pstats
import random
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
for _cartella in (RADICE, RADICE / "strumenti"):
    if str(_cartella) not in sys.path:
        sys.path.insert(0, str(_cartella))

import mondi_sintetici as ms  # noqa: E402
import popolazione_di_prova as pp  # noqa: E402

import archivio  # noqa: E402
import percorsi  # noqa: E402
import utilita  # noqa: E402
from motore import ESSENZIALE, SQUADRE, Squadra, formato_singolare, simula_incontro  # noqa: E402
from motore.squadre import composizione_valida  # noqa: E402
from version import __version__  # noqa: E402

RAPPORTO_PREDEFINITO = RADICE / "strumenti" / "profilo_tappa_12.txt"
# Le funzioni del motore di cui il profilo dice la quota del tempo: il nome della funzione e quello
# del file, per non confondere due funzioni con lo stesso nome.
FUNZIONI_DEL_MOTORE = (("gioca_punto", "scambio.py"), ("prepara_punto", "campo.py"), ("fascia", "dado.py"), ("abitudine_al_colpo", "campo.py"),
                       ("_fasce_imprevisti", "incontro.py"), ("__init__", "campo.py"))
# Le parti del giorno di cui il profilo dice la quota.
FUNZIONI_DEL_GIORNO = (("_fai_invecchiare", "mondo.py"), ("_applica_declino_aggregato", "modelli.py"), ("_allenamento_del_giorno", "mondo.py"),
                       ("_esegui_logica_cpu_polisportive", "mondo.py"), ("_compra_dal_mercato", "mondo.py"), ("_stipendio_massimo", "mondo.py"),
                       ("aggiorna_icv", "modelli.py"), ("aggiorna_stato_polisportive", "mondo.py"), ("_primo_del_mese", "mondo.py"),
                       ("crea_giocatori_casuali", "mondo.py"), ("crea_polisportiva_cpu", "mondo.py"), ("giorno", "calendario.py"), ("automatiche", "iscrizioni.py"),
                       ("gioca", "esito_rapido.py"), ("registra", "partita.py"), ("chiudi", "premiazioni.py"), ("giorno", "sfide.py"))
# L'albo d'oro di prova: le sedi concluse in un anno di calendario a regime, i giocatori e i club
# diversi che salgono sul podio in sessant'anni, stime del punto 1.4 del progetto.
SEDI_ALL_ANNO = 4300
GIOCATORI_SUL_PODIO_IN_60_ANNI = 60_000
CLUB_IN_60_ANNI = 5000
MODELLI_DELL_ALBO = 10


def numero(valore, decimali=0):
    return f"{valore:.{decimali}f}".replace(".", ",")


def alimentazione():
    """Se la macchina va a batteria o a corrente, in parole: a batteria un portatile rallenta, e i tempi vanno letti così. None fuori da Windows."""
    if sys.platform != "win32":
        return None
    import ctypes

    class StatoAlimentazione(ctypes.Structure):
        _fields_ = (("ACLineStatus", ctypes.c_ubyte), ("BatteryFlag", ctypes.c_ubyte), ("BatteryLifePercent", ctypes.c_ubyte),
                    ("SystemStatusFlag", ctypes.c_ubyte), ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong))

    stato = StatoAlimentazione()
    if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(stato)):
        return None
    return {0: "a batteria", 1: "a corrente"}.get(stato.ACLineStatus, "con l'alimentazione sconosciuta")


def quote_del_profilo(profilo, funzioni):
    """Per ogni funzione indicata, la quota del tempo proprio e di quello col resto delle chiamate, sul tempo totale del profilo."""
    stats = pstats.Stats(profilo)
    totale = stats.total_tt or 1.0
    quote = []
    for nome, file in funzioni:
        proprio = cumulato = 0.0
        for (percorso, _riga, funzione), (_cc, _nc, tt, ct, _chiamanti) in stats.stats.items():
            if funzione == nome and Path(percorso).name == file:
                proprio += tt
                cumulato += ct
        if cumulato > 0:
            quote.append((nome, 100.0 * proprio / totale, 100.0 * cumulato / totale))
    return quote


def frase_delle_quote(quote):
    return "; ".join(f"{nome} {numero(proprio)} per cento del tempo proprio e {numero(cumulato)} col resto" for nome, proprio, cumulato in quote)


def misura_incontri(quanti, scrivi):
    """Il motore in modalità essenziale sulle due popolazioni, poi il profilo sulla seconda."""
    rng = random.Random("profilo-incontri")
    popolazioni = (("sulla popolazione di prova del banco, 400 giocatori col seme 7", [g for g in pp.genera(400, 7) if g.puo_giocare]),
                   ("sulla popolazione del mondo sintetico a regime, 800 giocatori col seme 7", ms.mondo_sintetico(800, None, 7, primo_id=200_000)))
    for nome, giocatori in popolazioni:
        parti = []
        for set_al_meglio in (3, 5):
            formato = formato_singolare(set_al_meglio)
            tempi, punti, attacchi = [], [], []
            for _ in range(quanti):
                a, b = rng.sample(giocatori, 2)
                inizio = time.perf_counter()
                risultato = simula_incontro(a, b, formato, seme=rng.getrandbits(63), dettaglio=ESSENZIALE)
                tempi.append(time.perf_counter() - inizio)
                punti.append(risultato.incontro.punti_giocati)
                attacchi.extend(risultato.incontro.attacchi_per_punto)
            parti.append(f"al meglio dei {set_al_meglio} {numero(1000 * statistics.median(tempi), 2)} millisecondi di mediana, {numero(statistics.fmean(punti), 1)} punti "
                         f"giocati e {numero(statistics.fmean(attacchi), 2)} attacchi per punto")
        tempi = []
        for n in range(max(10, quanti // 4)):
            squadre = _due_squadre(giocatori, rng, n)
            if squadre is None:
                break
            inizio = time.perf_counter()
            simula_incontro(*squadre, SQUADRE, seme=rng.getrandbits(63), dettaglio=ESSENZIALE)
            tempi.append(time.perf_counter() - inizio)
        if tempi:
            parti.append(f"la gara a squadre {numero(1000 * statistics.median(tempi), 2)} millisecondi di mediana")
        scrivi(f"Il motore {nome}, {quanti} incontri per formato: " + "; ".join(parti) + ".")
    giocatori = popolazioni[1][1]
    formato = formato_singolare(3)
    coppie = [(*rng.sample(giocatori, 2), rng.getrandbits(63)) for _ in range(quanti)]
    profilo = cProfile.Profile()
    profilo.enable()
    for a, b, seme in coppie:
        simula_incontro(a, b, formato, seme=seme, dettaglio=ESSENZIALE)
    profilo.disable()
    scrivi(f"Il profilo di {quanti} incontri al meglio dei 3 sulla popolazione a regime: " + frase_delle_quote(quote_del_profilo(profilo, FUNZIONI_DEL_MOTORE)) + ".")


def _due_squadre(giocatori, rng, n):
    """Due squadre a caso di quattro giocatori, due titolari di un sesso e uno dell'altro, oppure None se la popolazione non basta."""
    maschi = [g for g in giocatori if g.sesso == "m"]
    femmine = [g for g in giocatori if g.sesso == "f"]
    if len(maschi) < 4 or len(femmine) < 4:
        return None
    m, f = rng.sample(maschi, 4), rng.sample(femmine, 4)
    a = Squadra(f"Prova A{n}", (m[0], m[1], f[0], f[1]))
    b = Squadra(f"Prova B{n}", (f[2], f[3], m[2], m[3]))
    if not (composizione_valida(a.titolari) and composizione_valida(b.titolari)):
        return None
    return a, b


def costruisci_mondo(attivi, seme, scrivi):
    ritirati = attivi // 3
    polisportive = int(attivi * 0.9 / 15)
    inizio = time.perf_counter()
    mondo = ms.mondo_a_regime(attivi, ritirati, polisportive, seme)
    scrivi(f"Il mondo a regime del seme {seme}: {attivi} attivi, {ritirati} ritirati, {polisportive} polisportive del computer, "
           f"{ms.riassunto_del_mondo(mondo)['tesserati']} tesserati, costruito in {numero(time.perf_counter() - inizio, 1)} secondi.")
    return mondo


def misura_giorno(mondo, giorni, scrivi, riscaldamento=1):
    """
    La media, la mediana e il giorno peggiore dei giorni misurati, dopo i giorni di riscaldamento, e il
    profilo di tre giorni. Dalla taratura della tappa 12 il riscaldamento si sceglie: il mondo a regime
    nasce col calendario vuoto, e soltanto dopo un paio di mesi ha le sue edizioni aperte e le sue sedi
    in corso come il mondo vero; i giorni misurati dicono anche gli incontri di torneo e le sfide.
    """
    stato = random.getstate()
    random.seed("profilo-giorno")
    try:
        inizio_riscaldamento = time.perf_counter()
        for _ in range(max(1, riscaldamento)):
            ms.avanza_un_giorno(mondo)
        if riscaldamento > 1:
            scrivi(f"Riscaldamento di {riscaldamento} giorni in {numero(time.perf_counter() - inizio_riscaldamento)} secondi.")
        tempi, incontri, sfide = [], [], []
        for _ in range(giorni):
            inizio = time.perf_counter()
            rapporto = ms.avanza_un_giorno(mondo)
            tempi.append(time.perf_counter() - inizio)
            incontri.append(rapporto["incontri_torneo"])
            sfide.append(rapporto["sfide_giocate"])
        profilo = cProfile.Profile()
        for _ in range(3):
            profilo.enable()
            ms.avanza_un_giorno(mondo)
            profilo.disable()
    finally:
        random.setstate(stato)
    riassunto = ms.riassunto_del_mondo(mondo)
    peggiore = max(range(len(tempi)), key=lambda i: tempi[i])
    scrivi(f"Il giorno simulato, {giorni} giorni senza profilo: media {numero(1000 * statistics.fmean(tempi))} millisecondi, mediana "
           f"{numero(1000 * statistics.median(tempi))}, il più veloce {numero(1000 * min(tempi))}, il peggiore {numero(1000 * max(tempi))}, con "
           f"{incontri[peggiore]} incontri di torneo; in media {numero(statistics.fmean(incontri), 1)} incontri di torneo e {numero(statistics.fmean(sfide), 1)} sfide al giorno, "
           f"al più {max(incontri)} incontri. Alla fine il mondo ha {riassunto['attivi']} attivi, {riassunto['tesserati']} tesserati e {riassunto['polisportive']} polisportive.")
    scrivi("Il profilo di tre giorni: " + frase_delle_quote(quote_del_profilo(profilo, FUNZIONI_DEL_GIORNO)) + ".")


def albo_di_prova(anni, rng):
    """
    Un albo d'oro di prova della forma del punto 5.10 del progetto: una voce corta, una lista, per
    ogni sede conclusa, e i nomi una volta sola in tre tabelle, i modelli, i giocatori e i club.
    """
    modelli = {f"modello_{n}": f"Modello di prova numero {n}" for n in range(1, MODELLI_DELL_ALBO + 1)}
    giocatori = {str(100_000 + n): ["Nomedi", "Cognomedigiocatore"] for n in range(GIOCATORI_SUL_PODIO_IN_60_ANNI)}
    club = {str(n): ["PoliTeam1234 Nome-Club", f"2030-{1 + n % 12:02d}-{1 + n % 28:02d}"] for n in range(CLUB_IN_60_ANNI)}
    voci = []
    for anno in range(anni):
        for sede in range(SEDI_ALL_ANNO):
            data = datetime.date(2030 + anno, 1 + sede % 12, 1 + sede % 28).isoformat()
            podio = [[100_000 + rng.randrange(GIOCATORI_SUL_PODIO_IN_60_ANNI), rng.randrange(CLUB_IN_60_ANNI)] for _ in range(4)]
            voci.append([f"modello_{1 + sede % MODELLI_DELL_ALBO}", "individuale", "m", 1.0, data, anno * 100 + sede // 300, 1 + sede % 12, 32, podio, [192, 120, 80, 64]])
    return {"voci": voci, "modelli": modelli, "giocatori": giocatori, "club": club}


def _tempi_del_salvataggio(documento_fn):
    """
    I tempi e le grandezze delle tre fasi del salvataggio come le fa archivio.scrivi, senza scrivere su
    disco: comporre il documento, scrivere il testo firmato e comprimerlo. Dalla decisione 4 di Gabriele
    del 14 ottobre 2026 il testo e la firma sono una fase sola, archivio._testo_firmato, e la raccolta
    della memoria resta spenta come in archivio.scrivi.
    """
    with utilita.senza_raccolta():
        inizio = time.perf_counter()
        contenuto = documento_fn()
        composto = time.perf_counter()
        pezzi = archivio._testo_firmato(contenuto)
        firmato = time.perf_counter()
        dati = archivio._comprimi(pezzi)
        compresso = time.perf_counter()
    return {"componi": composto - inizio, "testo": firmato - composto, "gzip": compresso - firmato,
            "chiaro": sum(len(pezzo) for pezzo in pezzi), "compresso": len(dati), "contenuto": contenuto}


def frase_del_salvataggio(nome, t):
    totale = t["componi"] + t["testo"] + t["gzip"]
    return (f"{nome}: comporre {numero(t['componi'], 2)} secondi, scrivere il testo e firmarlo {numero(t['testo'], 2)}, comprimere "
            f"{numero(t['gzip'], 2)}, in tutto {numero(totale, 2)} secondi senza la scrittura su disco; {numero(t['chiaro'] / 1e6, 1)} MB in chiaro e "
            f"{numero(t['compresso'] / 1e6, 1)} MB compressi")


def misura_salvataggio(mondo, scrivi):
    """Il salvataggio del mondo, diari compresi, e lo stesso con un albo d'oro di sessant'anni."""
    tempi = _tempi_del_salvataggio(lambda: archivio.componi(mondo))
    giocatori = len(tempi["contenuto"]["mondo"]["giocatori"])
    diari = sum(len(g["diario"]) for g in tempi["contenuto"]["mondo"]["giocatori"])
    scrivi(frase_del_salvataggio(f"Il salvataggio del mondo, {giocatori} giocatori vivi con {diari} voci di diario", tempi)
           + f", cioè {numero(tempi['chiaro'] / giocatori)} byte in chiaro e {numero(tempi['compresso'] / giocatori)} compressi per giocatore.")
    albo = albo_di_prova(60, random.Random("albo-di-prova"))
    solo_albo = json.dumps(albo, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    scrivi(f"L'albo d'oro di prova di sessant'anni: {len(albo['voci'])} voci, {numero(len(solo_albo) / 1e6, 1)} MB in chiaro, "
           f"{numero(len(solo_albo) / len(albo['voci']))} byte per voce con le tabelle dei nomi.")

    def con_albo():
        documento = archivio.componi(mondo)
        documento["mondo"]["albo_di_prova"] = albo
        return documento

    scrivi(frase_del_salvataggio("Il salvataggio dello stesso mondo con l'albo di sessant'anni", _tempi_del_salvataggio(con_albo)) + ".")


def main():
    parser = argparse.ArgumentParser(description="Il profilo del motore, del giorno simulato e del salvataggio di MESS, in sola lettura.")
    parser.add_argument("--incontri", action="store_true", help="misura il motore in modalità essenziale, con il profilo")
    parser.add_argument("--giorno", action="store_true", help="misura il giorno simulato di un mondo a regime, con il profilo")
    parser.add_argument("--salvataggio", action="store_true", help="misura il salvataggio del mondo a regime, anche con un albo d'oro di sessant'anni")
    parser.add_argument("--attivi", type=int, default=5000, help="i giocatori in attività del mondo a regime, 5000 se non indicato")
    parser.add_argument("--giorni", type=int, default=20, help="i giorni misurati, 20 se non indicato")
    parser.add_argument("--anno", action="store_true", help="misura un anno di calendario, 365 giorni")
    parser.add_argument("--riscaldamento", type=int, default=1, help="i giorni da far avanzare prima di misurare, uno se non indicato; 90 perché il calendario sia pieno")
    parser.add_argument("--quanti", type=int, default=400, help="gli incontri per formato di --incontri, 400 se non indicato")
    parser.add_argument("--seme", type=int, default=31, help="il seme del mondo a regime, 31 se non indicato")
    parser.add_argument("--rapporto", nargs="?", type=Path, const=RAPPORTO_PREDEFINITO, default=None, help="salva il racconto, in strumenti/profilo_tappa_12.txt se non si dà un file")
    parser.add_argument("--nota", action="append", default=[], help="una riga da mettere nel racconto dopo l'intestazione, per esempio le misure di prima; si può ripetere")
    argomenti = parser.parse_args()
    if not (argomenti.incontri or argomenti.giorno or argomenti.salvataggio):
        parser.error("serve almeno una misura: --incontri, --giorno o --salvataggio")
    righe = []

    def scrivi(riga):
        righe.append(riga)
        print(riga, flush=True)

    corrente = alimentazione()
    scrivi(f"Profilo di MESS {__version__}, {time.strftime('%Y-%m-%d %H:%M')}, sulla macchina {platform.node()}" + (f" {corrente}" if corrente else "")
           + f", Python {platform.python_version()}. I tempi assoluti cambiano da una macchina all'altra e con l'alimentazione; i rapporti fra misure prese insieme reggono.")
    for nota in argomenti.nota:
        scrivi(nota)
    cartella = tempfile.mkdtemp(prefix="mess_profilo_")
    vera = percorsi.cartella
    percorsi.cartella = lambda: cartella
    stato = random.getstate()
    try:
        if argomenti.incontri:
            misura_incontri(argomenti.quanti, scrivi)
        if argomenti.giorno or argomenti.salvataggio:
            mondo = costruisci_mondo(argomenti.attivi, argomenti.seme, scrivi)
            if argomenti.giorno:
                misura_giorno(mondo, 365 if argomenti.anno else argomenti.giorni, scrivi, argomenti.riscaldamento)
            if argomenti.salvataggio:
                misura_salvataggio(mondo, scrivi)
    finally:
        random.setstate(stato)
        percorsi.cartella = vera
        shutil.rmtree(cartella, ignore_errors=True)
    if argomenti.rapporto:
        argomenti.rapporto.write_text("\n".join(righe) + "\n", encoding="utf-8")
        print(f"Rapporto salvato in {argomenti.rapporto}.")


if __name__ == "__main__":
    main()
