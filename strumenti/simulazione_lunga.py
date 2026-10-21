"""
La simulazione lunga del mondo di MESS, per controllare l'economia.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9, dallo script di lavoro della tappa 8 che aveva fissato le
cifre della decisione D22 in tre giri da dieci anni simulati. Fa nascere un mondo nuovo, sempre il
primo gennaio 2026, in una cartella temporanea e lo fa avanzare un giorno simulato alla volta, come farebbe il programma in
anni di uso; ogni anno dice quanti giocatori ci sono, quanti sono tesserati, come stanno le casse
delle polisportive del computer e gli stipendi, e alla fine confronta i numeri con i bersagli.
Serve alla taratura del valore, che vi prende il mondo maturo su cui fissare la prima stima della
scala, e alla taratura dell'economia.
Dalla tappa 11, il 2026-10-09, decisione D31, nel mondo che avanza c'è già l'allenamento, perché
sta in un giorno del mondo: sedute, spesa autonoma, esperienza, costanza, contratti e infortuni in
seduta; il mondo non gioca partite fino alla tappa 12. Le misure contano lo stipendio pagato, cioè
quello del contratto, la parte allenata e il valore per fasce d'età, le classi per lettera, i
rinnovi e le scadenze dell'anno, gli infortuni in seduta e i millisecondi del giorno. I bersagli
sono quelli del punto 5 del progetto della tappa, all'anno 10 su quattro semi: lo stipendio pagato
al decimo percentile dei tesserati fra 95 e 115 euro, attorno ai 105 di D31, e mediano fra 190 e
240; la cassa mediana delle polisportive del computer fra 4.500 e 5.500 euro; i tesserati dall'88
al 92 per cento dei giocatori in attività. Con --cerca-economia la scala del valore A e B si ricava
in forma chiusa, senza bisezioni annidate: da una corsa di riferimento si prendono le somme pesate
dei giocatori in attività e quelle dei tesserati con i loro moltiplicatori di stipendio, e si
calcolano l'A che tiene la mediana del valore a 135,5 e il B che porta lo stipendio al decimo
percentile a 105; si rifà la corsa con la scala nuova, due o tre volte, finché non si sposta più.
Poi una bisezione cerca soltanto lo sponsor per punto di gloria, con la quota sul valore fissa,
perché la cassa mediana torni a 5.000 euro.
Con --prova-lunga i semi vivono 60 anni in parallelo, se non si dice altro: per decennio il valore
mediano, gli stipendi e le casse, e anno per anno il controllo che il computer resti in grado di
pagare, con i tesserati almeno all'85 per cento dei giocatori in attività e la cassa mediana fra
2.000 e 15.000 euro. È il controllo sul mondo a regime: la scala si tara all'anno 10, e da lì il
mondo deriva.
Con --scenario-utente, all'anno 10 nasce una polisportiva dell'utente che allena: tessera al mercato
i quindici liberi più forti fino a 30 anni che può pagare con la regola del computer della 1.60.11,
lo sponsor più un ventiquattresimo della cassa, senza il premio della cassa piena, così il monte
stipendi parte vicino al suo limite, e riempie allo stesso modo i posti che si liberano; ognuno gioca un'amichevole ogni due
giorni contro un compagno; ogni giorno Allena tutti spende i punti di tutti secondo il programma;
ogni rinnovo si propone alla richiesta, se la cassa lo regge con la regola del computer; gli
arretrati, se ce ne sono, si pagano appena la cassa lo permette. Dieci anni. Anno per anno dice la
cassa, lo sponsor contro gli stipendi pagati, i rinnovi mancati per mancanza di soldi, i tesserati
dell'utente tornati liberi e quanti di loro ha preso qualcun altro, e la quota dei primi 100 del
mondo per valore che sono tesserati. I bersagli: lo sponsor dell'utente, in media sull'anno, non
supera il 120 per cento degli stipendi che paga, e almeno l'80 per cento dei primi 100 è tesserato.
Non tocca mai il mondo salvato: la cartella del programma è spostata in quella temporanea, che
alla fine si cancella; scala e sponsor provati vivono soltanto nei processi della simulazione.
Dalla tappa 12, il 2026-10-14, punto 13.4 del progetto, il mondo gioca: tornei, sfide e la Coppa
delle polisportive. La simulazione semplice misura il calendario per anno di calendario, cioè ogni
365 giorni simulati, e alla fine per la parte d'anno che resta: tornei, sedi e iscritti per sede,
incontri al giorno in media e nel giorno peggiore, medaglie e premi, ritiri, tavolini, infortuni e
acciacchi per incontro, sfide al mese per polisportiva, edizioni annullate, tornei per atleta
tesserato sano, chi aspetta per il carico, liberi, la quota del palmarès nella gloria delle
polisportive del computer, il rapporto fra la gloria richiesta dei liberi e la gloria del computer, i
punti allenamento al giorno che i tesserati del computer prendono dalle gare per fascia d'età, e i
millisecondi del giorno, in media e nel peggiore, divisi fra mondo, tornei e sfide. --giorni fissa i
giorni simulati al posto degli anni; --salva-popolazione scrive alla fine i giocatori in attività in
un file JSON compresso, per la verifica dell'esito rapido del punto 13.5. I bersagli nuovi e la
ricerca dell'economia con i tornei sono del passo 4 della tappa. Dalla decisione 1 di Gabriele del 14
ottobre 2026, il computer che spende secondo la cassa, la prova lunga controlla anche i primi 100 del
mondo per valore, tesserati almeno all'80 per cento in tutti gli anni come nello scenario dell'utente; e
con --salva-mondi scrive alla fine il mondo di ogni seme, per misurare il giorno a regime a processore
libero senza rifare la simulazione. Dalla verifica del 15 ottobre 2026 la prova lunga misura e controlla
anche i primi 10 e i primi 20 del mondo tesserati, la soglia del mondiale del mondo contro quella della
carriera perfetta e la cassa mediana del computer ferma a regime; la memoria si congela a fine anno,
come fa il programma dopo ogni salvataggio, e lo scenario dell'utente spende con la regola della 1.60.11.
Dalla tappa 13, il 2026-10-21, progetto 6.1 e 6.3, misura anche lo staff del computer: le polisportive con
un capo e con lo staff pieno, la qualità, la parte dello staff nel monte e gli allenatori liberi per
lettera, coi bersagli dello staff in controlli_della_tappa_13.
Uso, dalla cartella del progetto o da qualunque altra:
    python strumenti/simulazione_lunga.py
    python strumenti/simulazione_lunga.py --giorni 1095 --seme 2026 --rapporto calendario.txt
    python strumenti/simulazione_lunga.py --anni 10 --seme 2026 --rapporto economia.txt
    python strumenti/simulazione_lunga.py --scala -58,25 1,2532 --semi 2026 7 13 21
    python strumenti/simulazione_lunga.py --cerca-economia --semi 2026 7 13 21 --cassa 5000
    python strumenti/simulazione_lunga.py --prova-lunga --semi 2026 7 13 21 --rapporto lunga.txt
    python strumenti/simulazione_lunga.py --scenario-utente --semi 2026 7 13 21 --rapporto utente.txt
"""

import argparse
import contextlib
import datetime
import gzip
import json
import math
import os
import random
import shutil
import statistics
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))

import allenamento  # noqa: E402
import archivio  # noqa: E402
import calendario  # noqa: E402
import classe  # noqa: E402
import contratti  # noqa: E402
import costanti  # noqa: E402
import economia  # noqa: E402
import esperienza  # noqa: E402
import infortuni  # noqa: E402
import iscrizioni  # noqa: E402
import modelli  # noqa: E402
import palmares  # noqa: E402
import percorsi  # noqa: E402
import sfide  # noqa: E402
import staff  # noqa: E402
import valore  # noqa: E402
from mondo import DURATA_TICK, Mondo  # noqa: E402
from motore import ESSENZIALE, SINGOLARE_3, simula_incontro  # noqa: E402
from partita import MotorePartita  # noqa: E402

# Quanti giorni simulati fanno un anno per l'età dei giocatori: con 108 avanzamenti un giocatore
# invecchia di un anno, ed è la misura usata dalle simulazioni della tappa 6 e della tappa 8.
GIORNI_PER_ANNO = 108
# L'indice della tappa 8, tutti i pesi a 1 e 33 punti per i tratti rari: le cifre dell'economia
# della decisione D22 sono tarate su di lui, e la sua mediana nel mondo maturo, circa 140, è quella
# che il valore della tappa 9 conserva.
PESI_TAPPA_8 = dict.fromkeys(costanti.CARATTERISTICHE_VALORE, 1.0)
TRATTI_TAPPA_8 = {"mancino": 0.0, "ambidestro": 33.0, "giocorapido": 33.0, "cambiovelocita": 33.0}
# Il mondo nasce sempre lo stesso giorno, perché i conti del primo del mese cadano negli stessi
# giorni simulati e la stessa simulazione dia gli stessi numeri qualunque giorno la si lanci.
NASCITA_DEL_MONDO = datetime.datetime(2026, 1, 1, 9, 0, tzinfo=datetime.UTC)
# I bersagli della tappa 11 all'anno 10, punto 5 del progetto; il novantesimo percentile è un'informazione.
BERSAGLI = (("Stipendio pagato mediano in euro", (190, 240)), ("Stipendio pagato al decimo percentile", (95, 115)),
            ("Stipendio pagato al novantesimo percentile", (0, 100_000)), ("Cassa mediana delle polisportive del computer", (4500, 5500)),
            ("Tesserati sui giocatori in attività, per cento", (88, 92)))
# Le mete della scala in forma chiusa: la mediana del valore dei giocatori in attività e lo stipendio al decimo percentile dei tesserati.
MEDIANA_DEL_VALORE = 135.5
STIPENDIO_AL_DECIMO = 105.0
FASCE_ETA = ((9, 20), (20, 35), (35, 50), (50, 76))
# Le voci del riepilogo che si sommano anno per anno.
VOCI_DELL_ANNO = ("rinnovi_cpu", "contratti_scaduti", "infortunati_in_seduta", "autoallenati", "partiti", "tuoi_scaduti", "tuoi_partiti", "tuoi_non_pagati")
# La prova lunga: quanti anni, se non si dice altro, e i bersagli di solvibilità del computer, anno per anno.
ANNI_PROVA_LUNGA = 60
TESSERATI_MINIMI_PROVA_LUNGA = 85.0
CASSA_MEDIANA_PROVA_LUNGA = (2000.0, 15000.0)
# Lo scenario dell'utente: quando nasce la sua polisportiva e per quanti anni allena, quanti tesserati
# tiene, fino a che età li sceglie al mercato, quanto offre in più dell'ingaggio chiesto, e i bersagli.
ANNI_PRIMA_DELL_UTENTE = 10
ANNI_DELL_UTENTE = 10
NOME_UTENTE = "Polisportiva Utente"
TESSERATI_UTENTE = 15
ETA_MASSIMA_UTENTE = 30.0
RIALZO_INGAGGIO_UTENTE = 1.3
SPONSOR_SU_STIPENDI_MASSIMO = 120.0
PRIMI_100_TESSERATI_MINIMI = 80.0
# Dalla tappa 12, punto 13.4 del progetto: nei primi tre anni, quando la polisportiva dell'utente non ha ancora
# palmarès, lo sponsor non scende sotto gli stipendi.
ANNI_DI_PARTENZA = 3
SPONSOR_SU_STIPENDI_PARTENZA = 100.0


def numero(valore_numerico, decimali=0):
    return f"{valore_numerico:.{decimali}f}".replace(".", ",")


def percentile(valori, quota):
    ordinati = sorted(valori)
    if not ordinati:
        return 0.0
    return ordinati[min(len(ordinati) - 1, int(len(ordinati) * quota))]


def in_attivita(mondo):
    """I giocatori vivi e non ritirati del mondo."""
    morti = mondo._ids_morti_processati_sessione
    return [g for gid, g in mondo.giocatori.items() if gid not in morti and not g.ritirato]


def moltiplicatore_di_stipendio(g):
    """Quanto lo stipendio chiesto si allontana dalla curva del valore: i tratti rari e l'esperienza, come in economia.stipendio."""
    fattore = 1.0
    if g.ambidestro:
        fattore *= costanti.FATTORE_GLORIA_RICHIESTA_AMBIDESTRO
    if g.giocorapido:
        fattore *= costanti.FATTORE_GLORIA_RICHIESTA_GIOCO_RAPIDO
    if g.cambiovelocita:
        fattore *= costanti.FATTORE_GLORIA_RICHIESTA_CAMBIO_VEL
    return fattore * (1 + costanti.AUMENTO_STIPENDIO_PER_ESPERIENZA * g.esperienza)


def misure(mondo, dell_anno=None):
    """
    Le misure di un mondo: stipendi pagati dei tesserati, casse del computer, quota di tesserati,
    valore, parte allenata e valore per fasce d'età, classi per lettera, e le voci dell'anno.
    """
    attivi = in_attivita(mondo)
    tesserati = [g for g in attivi if g.appartenenza != "*"]
    cpu = [p for p in mondo.polisportive.values() if p.is_cpu_controlled]
    stipendi = [economia.stipendio_pagato(g) for g in tesserati]
    casse = [p.cassa for p in cpu]
    monte = sum(mondo.monte_stipendi(p) for p in cpu)
    sponsor = sum(mondo.sponsor(p) for p in cpu)
    valori = [g.indice_collettivo_valore for g in attivi]
    fasce = {}
    for da, a in FASCE_ETA:
        gruppo = [g for g in attivi if da <= g.eta_anni < a]
        if gruppo:
            fasce[(da, a)] = (len(gruppo), statistics.median(g.indice_collettivo_valore for g in gruppo), statistics.median(valore.somma_pesata(g, "allenata") for g in gruppo))
    lettere = {}
    for g in attivi:
        lettera = classe.classe(g).codice[0]
        lettere[lettera] = lettere.get(lettera, 0) + 1
    primi = sorted(attivi, key=lambda g: g.indice_collettivo_valore, reverse=True)[:100]
    # Dalla verifica del 15 ottobre 2026 anche i primi 10 e i primi 20, i veri campioni, e la soglia del
    # mondiale, cioè i punti dell'ultimo anno del trentaduesimo fra gli attivi di ogni sesso.
    oggi = mondo.datetime_corrente_simulazione.date()
    soglie = {}
    for sesso in ("m", "f"):
        punti = sorted((palmares.punti_dell_anno(g, oggi) for g in attivi if g.sesso == sesso), reverse=True)
        soglie[sesso] = punti[QUALIFICATI_MONDIALE - 1] if len(punti) >= QUALIFICATI_MONDIALE else 0.0
    # Dalla tappa 12 anche la gloria mediana del computer e il rapporto della gloria richiesta mediana dei liberi, punto 13.4.
    glorie = [p.gloria for p in cpu]
    richieste = [g.gloria_richiesta for g in attivi if g.appartenenza == "*"]
    gloria_mediana = statistics.median(glorie) if glorie else 0.0
    # Dalla tappa 13, progetto 6.1: lo staff del computer, la qualità, la parte sul monte e gli allenatori liberi.
    qualita = [staff.qualita_della_polisportiva(p, mondo.allenatori) for p in cpu]
    liberi = [a for a in mondo.allenatori.values() if a.libero]
    liberi_per_lettera = {}
    for a in liberi:
        liberi_per_lettera[a.codice[0]] = liberi_per_lettera.get(a.codice[0], 0) + 1
    return {
        "con_capo": 100.0 * sum(1 for p in cpu if p.staff[0]) / max(1, len(cpu)), "senza_capo": sum(1 for p in cpu if not p.staff[0]),
        "staff_pieno": 100.0 * sum(1 for p in cpu if all(p.staff)) / max(1, len(cpu)),
        "qualita_staff": (percentile(qualita, 0.1), percentile(qualita, 0.5), percentile(qualita, 0.9)) if qualita else (0.0, 0.0, 0.0),
        "staff_sul_monte": 100.0 * sum(mondo.monte_dello_staff(p) for p in cpu) / max(1, monte),
        "allenatori": len(mondo.allenatori), "allenatori_liberi": len(liberi), "liberi_per_lettera": liberi_per_lettera,
        "attivi": len(attivi), "tesserati": len(tesserati), "polisportive": len(cpu),
        "primi_100": 100.0 * sum(1 for g in primi if g.appartenenza != "*") / max(1, len(primi)),
        "primi_10": sum(1 for g in primi[:10] if g.appartenenza != "*"), "primi_20": sum(1 for g in primi[:20] if g.appartenenza != "*"),
        "soglia_mondiale": soglie,
        "stipendi": (percentile(stipendi, 0.1), percentile(stipendi, 0.5), percentile(stipendi, 0.9)),
        "casse": (percentile(casse, 0.1), percentile(casse, 0.5), percentile(casse, 0.9)),
        "monte_su_sponsor": monte / max(1, sponsor),
        "valore": (percentile(valori, 0.1), percentile(valori, 0.5), percentile(valori, 0.9)),
        "fasce": fasce, "lettere": lettere, "anno": dict(dell_anno or {}),
        "gloria_mediana": gloria_mediana, "rapporto_richiesta": statistics.median(richieste) / max(1.0, gloria_mediana) if richieste else 0.0,
    }


def riga_dell_anno(anno, m, millisecondi):
    s10, s50, s90 = m["stipendi"]
    c10, c50, c90 = m["casse"]
    v10, v50, v90 = m["valore"]
    fasce = "; ".join(f"dai {da} ai {a} anni {quanti}, valore {numero(v, 1)}, somma allenata {numero(s, 1)}" for (da, a), (quanti, v, s) in m["fasce"].items())
    lettere = ", ".join(f"{lettera} {numero(100 * quanti / max(1, m['attivi']), 1)}" for lettera, quanti in sorted(m["lettere"].items()))
    anno_trascorso = ", ".join(f"{voce} {m['anno'].get(voce, 0)}" for voce in VOCI_DELL_ANNO)
    return (f"Anno {anno}: {m['attivi']} giocatori in attività, {numero(100 * m['tesserati'] / max(1, m['attivi']))} per cento tesserati, "
            f"{m['polisportive']} polisportive del computer. Stipendi pagati {numero(s10)}, {numero(s50)} e {numero(s90)} euro al decimo, cinquantesimo e novantesimo percentile; "
            f"casse {numero(c10)}, {numero(c50)} e {numero(c90)} euro; il monte stipendi è il {numero(100 * m['monte_su_sponsor'])} per cento dello sponsor. "
            f"Valore {numero(v10)}, {numero(v50)} e {numero(v90)}; dei primi 100 per valore è tesserato il {numero(m['primi_100'])} per cento, "
            f"dei primi 10 {m['primi_10']} e dei primi 20 {m['primi_20']}; il trentaduesimo per punti dell'ultimo anno ne ha "
            f"{numero(m['soglia_mondiale']['m'])} fra gli uomini e {numero(m['soglia_mondiale']['f'])} fra le donne. "
            f"Per fasce d'età: {fasce}. Classi per lettera, per cento: {lettere}. "
            f"Nell'anno: {anno_trascorso}. Un giorno simulato chiede {numero(millisecondi)} millisecondi.")


# Le misure del calendario della tappa 12, punto 13.4: per anno di calendario, cioè ogni 365 giorni simulati.
GIORNI_PER_ANNO_DI_CALENDARIO = 365
VOCI_DEL_CALENDARIO = ("tornei_conclusi", "incontri_torneo", "incontri_ritiro", "incontri_tavolino", "infortuni_in_gara", "acciacchi_in_gara",
                       "sfide_giocate", "edizioni_annullate", "premi_tornei")


def fascia_di(anni):
    """La fascia d'età delle misure, o None fuori da tutte."""
    for fascia in FASCE_ETA:
        if fascia[0] <= anni < fascia[1]:
            return fascia
    return None


# I conteggi grezzi delle gare per i mondi sintetici, punto 13.3 del progetto della tappa 12: per fascia
# d'età e per giocatore in attività che non è dell'utente, al giorno, i punti allenamento dei tornei e
# delle sfide divisi per il fattore della loro fonte, e l'esperienza grezza degli incontri di torneo, delle
# fasi superate, dei piazzamenti e delle sfide, cioè le volte per l'importanza senza la costante.
VOCI_DEI_CONTEGGI = ("punti_torneo", "punti_sfida", "incontri_torneo", "fasi", "piazzamenti", "sfide")


class MisuraDelCalendario:
    """
    Le misure dei tornei e delle sfide nella simulazione, per anno di calendario. Mentre la
    simulazione gira mette i suoi orologi attorno al giorno del calendario e a quello delle sfide, per
    dividere i millisecondi del giorno, e guarda i punti allenamento dei tesserati del computer prima
    dei tornei e dopo le sfide, per i punti che prendono dalle gare; alla fine li toglie.
    Dalla taratura della tappa 12, passo 4, misura anche i conteggi grezzi per i mondi sintetici, di
    tutti i giocatori in attività che non sono dell'utente: i punti dei tornei, letti dopo il calendario,
    e quelli delle sfide, letti dopo le sfide, divisi per il fattore della fonte; e l'esperienza grezza,
    con un orologio attorno alle funzioni di esperienza.py. Conta poi gli incontri al meglio dei 3 e i
    loro ritiri, perché il bersaglio dei ritiri della risposta di Gabriele sugli infortuni è al meglio
    dei 3, e tiene i numeri di ogni anno in anni_dati, per la prova lunga.
    """

    def __init__(self):
        self.righe = []
        self.anni_dati = []
        self.numero_anno = 0
        self._ms_tornei = self._ms_sfide = 0.0
        self._prima = {}
        self._prima_tutti = {}
        self._dopo_tornei = {}
        self._mondo = None
        self._originali = None
        self._apri_anno(None)

    def _apri_anno(self, mondo):
        self.voci = dict.fromkeys(VOCI_DEL_CALENDARIO, 0)
        self.incontri_al_giorno = []
        self.millisecondi = []
        self.ms_tornei = []
        self.ms_sfide = []
        self.punti_per_fascia = {fascia: [0.0, 0] for fascia in FASCE_ETA}
        self.conteggi = {fascia: dict.fromkeys(VOCI_DEI_CONTEGGI, 0.0) for fascia in FASCE_ETA}
        self.giornate = dict.fromkeys(FASCE_ETA, 0)
        self.al_meglio_dei_3 = [0, 0]
        self.voci_albo_prima = len(mondo.calendario.albo.voci) if mondo is not None else 0
        self.tornei_prima = {gid: g.tornei_giocati for gid, g in mondo.giocatori.items()} if mondo is not None else {}

    # Gli orologi attorno al calendario, alle sfide e alle funzioni dell'esperienza.

    def __enter__(self):
        giorno_del_calendario, giorno_delle_sfide = calendario.Calendario.giorno, sfide.giorno
        funzioni = {nome: getattr(esperienza, nome) for nome in ("da_partita", "da_fasi", "da_piazzamento", "da_riserva")}
        conta = calendario.Calendario._conta
        self._originali = (giorno_del_calendario, giorno_delle_sfide, funzioni, conta)
        misura = self

        def calendario_misurato(cal, mondo, data, rapporto):
            misura._mondo = mondo
            misura._prima = misura._punti_dei_tesserati(mondo)
            misura._prima_tutti = misura._punti_di_tutti(mondo)
            inizio = time.perf_counter()
            try:
                return giorno_del_calendario(cal, mondo, data, rapporto)
            finally:
                misura._ms_tornei = (time.perf_counter() - inizio) * 1000
                misura._dopo_tornei = misura._punti_di_tutti(mondo)

        def sfide_misurate(mondo, data, rapporto):
            inizio = time.perf_counter()
            try:
                return giorno_delle_sfide(mondo, data, rapporto)
            finally:
                misura._ms_sfide = (time.perf_counter() - inizio) * 1000
                misura._conta_i_punti(mondo)

        def registra(voce, g, quanto):
            fascia = fascia_di(g.eta_anni)
            if fascia is not None:
                misura.conteggi[fascia][voce] += quanto

        def da_partita(g, tipo=esperienza.AMICHEVOLE, importanza=1.0):
            if tipo == esperienza.TORNEO:
                registra("incontri_torneo", g, importanza)
            elif tipo == esperienza.SFIDA:
                registra("sfide", g, importanza)
            return funzioni["da_partita"](g, tipo, importanza)

        def da_fasi(g, fasi, importanza=1.0):
            registra("fasi", g, max(0, fasi) * importanza)
            return funzioni["da_fasi"](g, fasi, importanza)

        def da_piazzamento(g, posto, importanza=1.0):
            registra("piazzamenti", g, esperienza.premio_piazzamento(posto) / costanti.ESPERIENZA_PIAZZAMENTO_BASE * importanza)
            return funzioni["da_piazzamento"](g, posto, importanza)

        def da_riserva(g, importanza=1.0):
            registra("sfide", g, costanti.ESPERIENZA_RISERVA_QUOTA * importanza)
            return funzioni["da_riserva"](g, importanza)

        def conta_misurato(mondo, risultato, tuoi, rapporto):
            if risultato.formato.tipo == "singolare" and risultato.formato.set_al_meglio == 3:
                misura.al_meglio_dei_3[0] += 1
                misura.al_meglio_dei_3[1] += risultato.esito == "ritiro"
            return conta(mondo, risultato, tuoi, rapporto)

        calendario.Calendario.giorno = calendario_misurato
        sfide.giorno = sfide_misurate
        calendario.Calendario._conta = staticmethod(conta_misurato)
        for nome, funzione in (("da_partita", da_partita), ("da_fasi", da_fasi), ("da_piazzamento", da_piazzamento), ("da_riserva", da_riserva)):
            setattr(esperienza, nome, funzione)
        return self

    def __exit__(self, *_eccezione):
        giorno_del_calendario, giorno_delle_sfide, funzioni, conta = self._originali
        calendario.Calendario.giorno, sfide.giorno = giorno_del_calendario, giorno_delle_sfide
        calendario.Calendario._conta = staticmethod(conta)
        for nome, funzione in funzioni.items():
            setattr(esperienza, nome, funzione)
        return False

    @staticmethod
    def _punti_dei_tesserati(mondo):
        """I punti allenamento dei tesserati del computer in attività, per identificativo."""
        cpu = {nome for nome, p in mondo.polisportive.items() if p.is_cpu_controlled}
        return {gid: g.punti_allenamento for gid, g in mondo.giocatori.items() if g.appartenenza in cpu and not g.ritirato}

    @staticmethod
    def _punti_di_tutti(mondo):
        """I punti allenamento dei giocatori in attività che non sono dell'utente: tesserati del computer e liberi."""
        utente = {nome for nome, p in mondo.polisportive.items() if not p.is_cpu_controlled}
        morti = mondo._ids_morti_processati_sessione
        return {gid: g.punti_allenamento for gid, g in mondo.giocatori.items() if not g.ritirato and gid not in morti and g.appartenenza not in utente}

    def _conta_i_punti(self, mondo):
        """
        I punti che i tesserati del computer hanno preso oggi dai tornei e dalle sfide, sommati per fascia
        d'età; e i conteggi grezzi di tutti quelli che non sono dell'utente, per i mondi sintetici.
        """
        for gid, prima in self._prima.items():
            g = mondo.giocatori.get(gid)
            if g is None:
                continue
            fascia = fascia_di(g.eta_anni)
            if fascia is not None:
                conti = self.punti_per_fascia[fascia]
                conti[0] += max(0.0, g.punti_allenamento - prima)
                conti[1] += 1
        for gid, prima in self._prima_tutti.items():
            g = mondo.giocatori.get(gid)
            fascia = fascia_di(g.eta_anni) if g is not None else None
            if fascia is None:
                continue
            dopo_tornei = self._dopo_tornei.get(gid, prima)
            self.conteggi[fascia]["punti_torneo"] += max(0.0, dopo_tornei - prima) / costanti.PA_FATTORE_TORNEO
            self.conteggi[fascia]["punti_sfida"] += max(0.0, g.punti_allenamento - dopo_tornei) / costanti.PA_FATTORE_SFIDA
            self.giornate[fascia] += 1
        self._prima = {}
        self._prima_tutti = {}
        self._dopo_tornei = {}

    def conteggi_al_giorno(self):
        """I conteggi grezzi dell'anno per fascia d'età, al giorno per giocatore."""
        return {fascia: {voce: valore / max(1, self.giornate[fascia]) for voce, valore in voci.items()} for fascia, voci in self.conteggi.items()}

    # Il giorno e l'anno.

    def giorno(self, mondo, numero, rapporto, millisecondi):
        """Le misure di un giorno simulato; ogni 365 giorni chiude l'anno di calendario e ne restituisce la riga, altrimenti None."""
        for voce in VOCI_DEL_CALENDARIO:
            self.voci[voce] += rapporto[voce]
        self.incontri_al_giorno.append(rapporto["incontri_torneo"])
        self.millisecondi.append(millisecondi)
        self.ms_tornei.append(self._ms_tornei)
        self.ms_sfide.append(self._ms_sfide)
        if not self.tornei_prima:
            # Il primo anno comincia col mondo appena nato: nessuno ha ancora giocato un torneo.
            self.tornei_prima = {gid: g.tornei_giocati for gid, g in mondo.giocatori.items()}
        if numero % GIORNI_PER_ANNO_DI_CALENDARIO == 0:
            return self.chiudi_anno(mondo)
        return None

    def chiudi_anno(self, mondo):
        """La riga dell'anno di calendario appena finito, o della parte d'anno che resta alla fine; poi un anno nuovo."""
        if not self.millisecondi:
            return None
        self.numero_anno += 1
        giorni = len(self.millisecondi)
        v = self.voci
        incontri = max(1, v["incontri_torneo"])
        attivi = in_attivita(mondo)
        tesserati_sani = [g for g in attivi if g.appartenenza != "*" and not g.infortunato and g.id in self.tornei_prima]
        tornei_a_testa = statistics.fmean(g.tornei_giocati - self.tornei_prima[g.id] for g in tesserati_sani) if tesserati_sani else 0.0
        cpu = [p for p in mondo.polisportive.values() if p.is_cpu_controlled]
        liberi = [g for g in attivi if g.appartenenza == "*"]
        in_attesa = sum(1 for g in attivi if (g.appartenenza == "*" or g.appartenenza in {p.nome for p in cpu}) and iscrizioni.troppo_carico(g, g.appartenenza == "*"))
        oggi = mondo.datetime_corrente_simulazione
        quote = []
        for p in cpu:
            medaglie, coppe = palmares.somma_finestra(p, oggi)
            parte = math.sqrt(max(0.0, medaglie)) * costanti.K_GLORIA_MEDAGLIE + math.sqrt(max(0.0, coppe)) * costanti.K_GLORIA_COPPE
            quote.append(100 * parte / max(1, p.gloria))
        glorie = [p.gloria for p in cpu]
        richiesta = statistics.median(g.gloria_richiesta for g in liberi) / max(1, statistics.median(glorie)) if liberi and glorie else 0.0
        voci_albo = [voce for voce in mondo.calendario.albo.voci[self.voci_albo_prima:] if voce[6]]
        iscritti_per_sede = statistics.fmean(voce[7] for voce in voci_albo) if voci_albo else 0.0
        # Tutti i premi pagati dalle sedi concluse; l'albo conserva soltanto quelli del podio, dal 69 al 79 per cento del totale.
        premi = v["premi_tornei"]
        premi_podio = sum(sum(voce[9]) for voce in voci_albo)
        medaglie_date = sum(len(voce[8]) for voce in voci_albo)
        punti = "; ".join(f"dai {da} ai {a} anni {numero(somma / max(1, quanti), 3)}" for (da, a), (somma, quanti) in self.punti_per_fascia.items())
        conteggi = self.conteggi_al_giorno()
        testo_conteggi = "; ".join(f"dai {da} ai {a} anni " + ", ".join(f"{voce} {numero(valore, 4)}" for voce, valore in voci.items())
                                   for (da, a), voci in conteggi.items())
        peggiore = max(range(giorni), key=lambda i: self.millisecondi[i])
        sani_con_ritmo = [g.tornei_giocati - self.tornei_prima[g.id] for g in tesserati_sani]
        self.anni_dati.append({
            "anno": self.numero_anno, "giorni": giorni, "sedi": v["tornei_conclusi"], "iscritti_per_sede": iscritti_per_sede, "annullate": v["edizioni_annullate"],
            "incontri": v["incontri_torneo"], "incontri_al_giorno": v["incontri_torneo"] / giorni, "incontri_giorno_peggiore": max(self.incontri_al_giorno),
            "ritiri": v["incontri_ritiro"], "tavolini": v["incontri_tavolino"], "acciacchi": v["acciacchi_in_gara"], "infortuni": v["infortuni_in_gara"],
            "al_meglio_dei_3": list(self.al_meglio_dei_3), "sfide": v["sfide_giocate"], "sfide_al_mese": 2 * v["sfide_giocate"] / max(1, len(cpu)) / (giorni / 30.4),
            "tornei_a_testa": tornei_a_testa, "tornei_a_testa_anno": tornei_a_testa * GIORNI_PER_ANNO_DI_CALENDARIO / giorni if sani_con_ritmo else 0.0,
            "in_attesa": 100 * in_attesa / max(1, len(attivi)), "liberi": 100 * len(liberi) / max(1, len(attivi)), "attivi": len(attivi),
            "quota_palmares": (percentile(quote, 0.5), percentile(quote, 0.9)), "gloria_mediana": statistics.median(glorie) if glorie else 0.0, "richiesta": richiesta,
            "ms_medio": statistics.fmean(self.millisecondi), "ms_peggiore": self.millisecondi[peggiore], "ms_tornei": statistics.fmean(self.ms_tornei),
            "ms_sfide": statistics.fmean(self.ms_sfide), "conteggi": {f"{da}-{a}": voci for (da, a), voci in conteggi.items()},
        })
        riga = (f"Anno di calendario {self.numero_anno}, {giorni} giorni: {v['tornei_conclusi']} sedi concluse, con {numero(iscritti_per_sede, 1)} iscritti per sede, "
                f"{v['edizioni_annullate']} edizioni annullate, {medaglie_date} medaglie e coppe dei tornei e {numero(premi)} euro di premi, "
                f"di cui {numero(premi_podio)} al podio; "
                f"{v['incontri_torneo']} incontri di torneo, {numero(v['incontri_torneo'] / giorni, 1)} al giorno in media e {max(self.incontri_al_giorno)} nel giorno più pieno; "
                f"ritiri {numero(100 * v['incontri_ritiro'] / incontri, 2)} per cento degli incontri, tavolini {numero(100 * v['incontri_tavolino'] / incontri, 2)}, "
                f"uno non regolare ogni {numero(incontri / max(1, v['incontri_ritiro'] + v['incontri_tavolino']), 1)}; "
                f"infortuni in gara {v['infortuni_in_gara']}, acciacchi {v['acciacchi_in_gara']}, {numero(100 * v['acciacchi_in_gara'] / incontri, 2)} ogni cento incontri; "
                f"{v['sfide_giocate']} sfide, {numero(2 * v['sfide_giocate'] / max(1, len(cpu)) / (giorni / 30.4), 2)} al mese per polisportiva del computer. "
                f"Tornei a testa dei tesserati sani {numero(tornei_a_testa, 2)}; aspettano per il carico {numero(100 * in_attesa / max(1, len(attivi)), 1)} per cento degli attivi; "
                f"liberi {numero(100 * len(liberi) / max(1, len(attivi)), 1)} per cento. Palmarès nella gloria del computer: mediana {numero(percentile(quote, 0.5), 1)} "
                f"per cento, primo decimo {numero(percentile(quote, 0.9), 1)}; gloria richiesta mediana dei liberi su gloria mediana del computer {numero(richiesta, 3)}. "
                f"Punti allenamento al giorno dalle gare dei tesserati del computer: {punti}. Il giorno chiede {numero(statistics.fmean(self.millisecondi))} millisecondi "
                f"in media, di cui {numero(statistics.fmean(self.ms_tornei))} per i tornei e {numero(statistics.fmean(self.ms_sfide))} per le sfide; il peggiore "
                f"{numero(self.millisecondi[peggiore])}, di cui {numero(self.ms_tornei[peggiore])} per i tornei e {numero(self.ms_sfide[peggiore])} per le sfide. "
                f"Al meglio dei 3 {self.al_meglio_dei_3[0]} incontri, finiti per ritiro il {numero(100 * self.al_meglio_dei_3[1] / max(1, self.al_meglio_dei_3[0]), 2)} per cento. "
                f"I conteggi grezzi delle gare per i mondi sintetici, al giorno per giocatore in attività non dell'utente: {testo_conteggi}.")
        self.righe.append(riga)
        self._apri_anno(mondo)
        return riga


def salva_popolazione(mondo, percorso):
    """I giocatori in attività del mondo, come li salva l'archivio, in un file JSON compresso: per la verifica dell'esito rapido, punto 13.5."""
    giocatori = [g.a_dizionario() for g in in_attivita(mondo)]
    with gzip.open(percorso, "wt", encoding="utf-8") as f:
        json.dump({"data_simulata": mondo.datetime_corrente_simulazione.isoformat(), "giocatori": giocatori}, f, ensure_ascii=False)
    return len(giocatori)


def simula(anni=10, seme=2026, stampa=print, misura_ogni_anno=True, ogni_giorno=None, annuali=None, giorni=None, misura_calendario=None, salva=None):
    """
    Fa nascere un mondo in una cartella temporanea e lo fa avanzare di tanti anni simulati.
    Restituisce il mondo e le righe del racconto; la cartella si cancella alla fine. Il caso del
    mondo si rimette com'era, così chi chiama non si accorge della simulazione. Con ogni_giorno,
    una funzione, la chiama dopo ogni giorno simulato col mondo, il numero del giorno e il
    riepilogo dell'avanzamento: è lì che agisce l'utente dello scenario. Con annuali, un elenco,
    vi aggiunge le misure di ogni anno, con l'anno e i millisecondi del giorno. Dalla tappa 12, con
    giorni si simulano quei giorni al posto degli anni, e con misura_calendario, una
    MisuraDelCalendario, il racconto ha anche le righe del calendario per anno di calendario. Con
    salva, un percorso, alla fine scrive il mondo in quel file, come il programma, e lo stato del caso
    accanto, nello stesso nome con .caso al posto di .json.gz: serve a misurare il giorno a regime a
    processore libero senza rifare la simulazione.
    """
    cartella = tempfile.mkdtemp(prefix="mess_simulazione_lunga_")
    cartella_vera = percorsi.cartella
    orologi_veri = archivio.adesso, archivio.adesso_utc
    stato = random.getstate()
    percorsi.cartella = lambda: cartella
    archivio.adesso = lambda: NASCITA_DEL_MONDO.replace(tzinfo=None)
    archivio.adesso_utc = lambda: NASCITA_DEL_MONDO
    righe = []

    def racconta(riga):
        if riga:
            righe.append(riga)
            if stampa:
                stampa(riga)

    try:
        random.seed(seme)
        mondo = Mondo()
        archivio.carica(mondo)
        giorni = giorni or anni * GIORNI_PER_ANNO
        ultimo = time.perf_counter()
        dell_anno = dict.fromkeys(VOCI_DELL_ANNO, 0)
        with misura_calendario if misura_calendario is not None else contextlib.nullcontext():
            for giorno in range(1, giorni + 1):
                inizio = time.perf_counter()
                rapporto = mondo.processa_tempo_trascorso(mondo.datetime_ultimo_run_reale + DURATA_TICK)
                if misura_calendario is not None:
                    racconta(misura_calendario.giorno(mondo, giorno, rapporto, (time.perf_counter() - inizio) * 1000))
                for voce in VOCI_DELL_ANNO:
                    dell_anno[voce] += rapporto[voce]
                if ogni_giorno is not None:
                    ogni_giorno(mondo, giorno, rapporto)
                if giorno % GIORNI_PER_ANNO == 0:
                    adesso = time.perf_counter()
                    millisecondi = (adesso - ultimo) * 1000 / GIORNI_PER_ANNO
                    if misura_ogni_anno or giorno == giorni or annuali is not None:
                        m = misure(mondo, dell_anno)
                        if annuali is not None:
                            annuali.append({**m, "numero_anno": giorno // GIORNI_PER_ANNO, "millisecondi": millisecondi})
                        if misura_ogni_anno or giorno == giorni:
                            racconta(riga_dell_anno(giorno // GIORNI_PER_ANNO, m, millisecondi))
                    dell_anno = dict.fromkeys(VOCI_DELL_ANNO, 0)
                    # Il programma congela la memoria dopo ogni salvataggio, dalla verifica del 15 ottobre
                    # 2026: qui a fine anno, fuori dai tempi del giorno. Non cambia nessun esito.
                    archivio.congela_la_memoria()
                    ultimo = time.perf_counter()
        if misura_calendario is not None and giorni % GIORNI_PER_ANNO_DI_CALENDARIO:
            racconta(misura_calendario.chiudi_anno(mondo))
        if salva is not None:
            salva = Path(salva)
            salva.parent.mkdir(parents=True, exist_ok=True)
            archivio.scrivi(mondo, str(salva), str(salva) + ".bak")
            salva.with_name(salva.name.replace(".json.gz", "") + ".caso").write_text(repr(random.getstate()), encoding="utf-8")
    finally:
        percorsi.cartella = cartella_vera
        archivio.adesso, archivio.adesso_utc = orologi_veri
        random.setstate(stato)
        shutil.rmtree(cartella, ignore_errors=True)
    return mondo, righe


def confronto(mondo):
    """Le righe del confronto con i bersagli, con dentro o FUORI accanto a ciascuno."""
    m = misure(mondo)
    valori = (m["stipendi"][1], m["stipendi"][0], m["stipendi"][2], m["casse"][1], 100 * m["tesserati"] / max(1, m["attivi"]))
    righe = ["Il confronto con i bersagli della tappa 11:"]
    for (nome, (basso, alto)), misurato in zip(BERSAGLI, valori, strict=True):
        esito = "dentro" if basso <= misurato <= alto else "FUORI"
        righe.append(f"{nome}: {numero(misurato)}, bersaglio da {numero(basso)} a {numero(alto)}, {esito}.")
    attivi = in_attivita(mondo)
    indici = [g.indice_collettivo_valore for g in attivi]
    righe.append(f"Valore dei giocatori in attività: mediana {numero(statistics.median(indici), 1)}, dal decimo al novantesimo percentile "
                 f"{numero(percentile(indici, 0.1), 1)} e {numero(percentile(indici, 0.9), 1)}.")
    return righe


# La scala e lo sponsor che si stanno provando. Le simulazioni girano in processi a parte, e ognuno li
# mette nei suoi moduli, che vivono soltanto per la simulazione: il progetto non cambia. Dalla tappa
# 12 anche la gloria: i due coefficienti del palmarès, K_GLORIA_MEDAGLIE e K_GLORIA_COPPE, e il fattore
# comune della gloria richiesta, che moltiplica i valori della tappa 11, 0,9 e 12, punto 9.4 del progetto.
K_ICV_GLORIA_RICHIESTA_1_60 = 0.9
GLORIA_RICHIESTA_FISSA_1_60 = 12


def _imposta(a, b, sponsor=None, gloria=None):
    valore.SCALA_VALORE_A, valore.SCALA_VALORE_B = a, b
    if sponsor is not None:
        economia.SPONSOR_PER_GLORIA = sponsor
    if gloria is not None:
        k_medaglie, k_coppe, fattore = gloria
        for modulo in (modelli, costanti):
            modulo.K_GLORIA_MEDAGLIE, modulo.K_GLORIA_COPPE = k_medaglie, k_coppe
            modulo.K_ICV_GLORIA_RICHIESTA = K_ICV_GLORIA_RICHIESTA_1_60 * fattore
            modulo.GLORIA_RICHIESTA_FISSA = GLORIA_RICHIESTA_FISSA_1_60 * fattore


def gloria_in_vigore():
    """I due coefficienti del palmarès e il fattore comune della gloria richiesta di adesso."""
    return (modelli.K_GLORIA_MEDAGLIE, modelli.K_GLORIA_COPPE, modelli.K_ICV_GLORIA_RICHIESTA / K_ICV_GLORIA_RICHIESTA_1_60)


def campione_della_gloria(mondo):
    """
    Il campione per la gloria in forma chiusa: per ogni polisportiva del computer la gloria senza il
    palmarès e le radici dei punti delle medaglie e delle coppe della finestra; per ogni libero la gloria
    richiesta col fattore comune a 1, cioè coi valori della 1.60.11.
    """
    oggi = mondo.datetime_corrente_simulazione
    club = []
    for p in mondo.polisportive.values():
        if not p.is_cpu_controlled:
            continue
        medaglie, coppe = palmares.somma_finestra(p, oggi)
        rm, rc = math.sqrt(max(0.0, medaglie)), math.sqrt(max(0.0, coppe))
        resto = p.gloria - rm * modelli.K_GLORIA_MEDAGLIE - rc * modelli.K_GLORIA_COPPE
        club.append((resto, rm, rc))
    salvati = (modelli.K_ICV_GLORIA_RICHIESTA, modelli.GLORIA_RICHIESTA_FISSA)
    modelli.K_ICV_GLORIA_RICHIESTA, modelli.GLORIA_RICHIESTA_FISSA = K_ICV_GLORIA_RICHIESTA_1_60, GLORIA_RICHIESTA_FISSA_1_60
    try:
        richieste = [g.gloria_richiesta for g in in_attivita(mondo) if g.appartenenza == "*"]
    finally:
        modelli.K_ICV_GLORIA_RICHIESTA, modelli.GLORIA_RICHIESTA_FISSA = salvati
    return club, richieste


def quote_del_palmares(club, k_medaglie, k_coppe):
    """La quota del palmarès nella gloria di ogni polisportiva del campione, coi coefficienti indicati, in percentuale."""
    quote = []
    for resto, rm, rc in club:
        parte = k_medaglie * rm + k_coppe * rc
        quote.append(100.0 * parte / max(1.0, resto + parte))
    return quote


def gloria_in_forma_chiusa(campioni, mediana=50.0, decimo=65.0, rapporto=None):
    """
    I coefficienti del palmarès e il fattore della gloria richiesta dal campione di una corsa, punto 13.4
    del progetto. Per ogni rapporto fra i due coefficienti, quello delle medaglie si trova per bisezione
    perché la quota mediana del palmarès sia quella indicata; il rapporto si cerca perché la quota del
    primo decimo, il novantesimo percentile, sia l'altra: le coppe stanno soprattutto nelle polisportive
    più gloriose, quindi più pesano le coppe, più sale il primo decimo. Se il primo decimo non si
    raggiunge resta il rapporto che ci va più vicino. Il fattore comune della gloria richiesta, con
    rapporto, porta la gloria richiesta mediana dei liberi su quella mediana del computer a quel rapporto.
    Restituisce i due coefficienti, il fattore, o None senza rapporto, e le quote ottenute.
    """
    club = [c for campione_club, _r in campioni for c in campione_club]
    richieste = [r for _c, campione_richieste in campioni for r in campione_richieste]

    def k_per_la_mediana(rho):
        basso, alto = 0.0, 100.0
        for _passo in range(50):
            k = (basso + alto) / 2
            if percentile(quote_del_palmares(club, k, rho * k), 0.5) < mediana:
                basso = k
            else:
                alto = k
        return (basso + alto) / 2

    migliore = None
    for rho in [0.0, *(0.25 * 1.25 ** i for i in range(25))]:
        k = k_per_la_mediana(rho)
        alto = percentile(quote_del_palmares(club, k, rho * k), 0.9)
        if migliore is None or abs(alto - decimo) < abs(migliore[2] - decimo):
            migliore = (k, rho * k, alto)
    k_medaglie, k_coppe, _alto = migliore
    quote = quote_del_palmares(club, k_medaglie, k_coppe)
    fattore = None
    if rapporto is not None and richieste:
        glorie = [resto + k_medaglie * rm + k_coppe * rc for resto, rm, rc in club]
        fattore = rapporto * statistics.median(glorie) / statistics.median(richieste)
    return k_medaglie, k_coppe, fattore, (percentile(quote, 0.5), percentile(quote, 0.9))


def _misura_con_scala(anni, seme, a, b, sponsor=None, gloria=None):
    """Una simulazione con la scala, lo sponsor e la gloria indicati, in un processo a parte: le misure finali e i campioni per la scala e per la gloria in forma chiusa."""
    _imposta(a, b, sponsor, gloria)
    mondo, _righe = simula(anni, seme, stampa=None, misura_ogni_anno=False)
    m = misure(mondo)
    attivi = in_attivita(mondo)
    m["mediana_valore"] = statistics.median(g.indice_collettivo_valore for g in attivi)
    m["mediana_somme"] = statistics.median(valore.indice(g, a=0.0, b=1.0) for g in attivi)
    m["mediana_tappa_8"] = statistics.median(valore.indice(g, PESI_TAPPA_8, TRATTI_TAPPA_8, 0.0, 1.0) for g in attivi)
    m["somme_attivi"] = [valore.indice(g, a=0.0, b=1.0) for g in attivi]
    m["tesserati_campione"] = [(valore.indice(g, a=0.0, b=1.0), moltiplicatore_di_stipendio(g)) for g in attivi if g.appartenenza != "*"]
    club, richieste = campione_della_gloria(mondo)
    m["campione_gloria"] = (club, richieste)
    quote = quote_del_palmares(club, modelli.K_GLORIA_MEDAGLIE, modelli.K_GLORIA_COPPE)
    glorie = [p.gloria for p in mondo.polisportive.values() if p.is_cpu_controlled]
    liberi = [g for g in attivi if g.appartenenza == "*"]
    m["quota_palmares"] = (percentile(quote, 0.5), percentile(quote, 0.9))
    m["gloria_mediana"] = statistics.median(glorie) if glorie else 0.0
    m["rapporto_richiesta"] = statistics.median(g.gloria_richiesta for g in liberi) / max(1, m["gloria_mediana"]) if liberi else 0.0
    m["liberi"] = 100.0 * len(liberi) / max(1, len(attivi))
    return seme, m


def con_scala(anni, semi, a, b, processi, sponsor=None, gloria=None):
    """Le misure finali di più semi simulati in parallelo con la scala, lo sponsor e la gloria indicati, come dizionario seme e misure."""
    # I processi figli ricevono la funzione per nome: la si prende dal modulo importato col suo
    # nome, perché quella dello script lanciato direttamente si chiama __main__.
    from simulazione_lunga import _misura_con_scala as lavoro
    with ProcessPoolExecutor(max_workers=max(1, min(processi, len(semi)))) as esecutore:
        futuri = [esecutore.submit(lavoro, anni, seme, a, b, sponsor, gloria) for seme in semi]
        return dict(f.result() for f in futuri)


def riga_della_scala(a, b, misure_per_seme, sponsor=None, gloria=None):
    casse = [m["casse"][1] for m in misure_per_seme.values()]
    stipendi = [m["stipendi"][1] for m in misure_per_seme.values()]
    bassi = [m["stipendi"][0] for m in misure_per_seme.values()]
    alti = [m["stipendi"][2] for m in misure_per_seme.values()]
    valori = [m["mediana_valore"] for m in misure_per_seme.values()]
    monte = [100 * m["monte_su_sponsor"] for m in misure_per_seme.values()]
    tesserati = [100 * m["tesserati"] / max(1, m["attivi"]) for m in misure_per_seme.values()]
    sponsor_testo = f", sponsor {numero(sponsor, 2)} per punto di gloria" if sponsor is not None else ""
    gloria_testo = ""
    if gloria is not None:
        gloria_testo = f", coefficienti del palmarès {numero(gloria[0], 2)} e {numero(gloria[1], 2)}, fattore della gloria richiesta {numero(gloria[2], 3)}"
    riga = (f"Scala A {numero(a, 2)}, B {numero(b, 4)}{sponsor_testo}{gloria_testo}: cassa mediana {', '.join(numero(c) for c in casse)} euro, in media {numero(statistics.fmean(casse))}; "
            f"stipendio pagato mediano {', '.join(numero(s) for s in stipendi)}, decimo percentile {', '.join(numero(s) for s in bassi)}, "
            f"novantesimo {', '.join(numero(s) for s in alti)}; monte stipendi {', '.join(numero(x) for x in monte)} per cento dello sponsor; "
            f"tesserati {', '.join(numero(x) for x in tesserati)} per cento; mediana del valore {', '.join(numero(v, 1) for v in valori)}")
    if all("quota_palmares" in m for m in misure_per_seme.values()):
        riga += (f"; palmarès nella gloria del computer, mediana {', '.join(numero(m['quota_palmares'][0], 1) for m in misure_per_seme.values())} per cento, "
                 f"primo decimo {', '.join(numero(m['quota_palmares'][1], 1) for m in misure_per_seme.values())}; gloria mediana del computer "
                 f"{', '.join(numero(m['gloria_mediana']) for m in misure_per_seme.values())}; gloria richiesta mediana dei liberi su gloria mediana del computer "
                 f"{', '.join(numero(m['rapporto_richiesta'], 3) for m in misure_per_seme.values())}; liberi {', '.join(numero(m['liberi'], 1) for m in misure_per_seme.values())} per cento")
    return riga + "."


def _stipendio(valore_del_giocatore, moltiplicatore):
    euro = costanti.STIPENDIO_DI_RIFERIMENTO * math.exp((valore_del_giocatore - costanti.VALORE_DI_RIFERIMENTO) / costanti.SCALA_STIPENDIO) * moltiplicatore
    return max(costanti.STIPENDIO_MINIMO, economia.arrotonda(euro))


def scala_in_forma_chiusa(campioni, mediana=MEDIANA_DEL_VALORE, decimo=STIPENDIO_AL_DECIMO):
    """
    La scala del valore dal campione di una corsa: A tiene la mediana delle somme pesate dei
    giocatori in attività al valore indicato, e B, con A che lo segue, porta lo stipendio chiesto al
    decimo percentile dei tesserati alla cifra indicata. Il campione è un elenco, uno per seme, di
    coppie: le somme dei giocatori in attività, e le coppie di somma e moltiplicatore dei tesserati.
    Con B la mediana resta ferma e i deboli si allontanano: lo stipendio al decimo percentile scende
    al crescere di B, e B si trova con una ricerca sul campione, senza nessuna simulazione.
    """
    somme = [s for attivi, _t in campioni for s in attivi]
    tesserati = [t for _a, ts in campioni for t in ts]
    centro = statistics.median(somme)

    def al_decimo(b):
        a = mediana - b * centro
        return percentile([_stipendio(a + b * s, m) for s, m in tesserati], 0.1)

    basso, alto = 0.05, 10.0
    for _passo in range(60):
        medio = (basso + alto) / 2
        if al_decimo(medio) > decimo:
            basso = medio
        else:
            alto = medio
    b = (basso + alto) / 2
    return mediana - b * centro, b


def cerca_economia(anni, semi, cassa_bersaglio, processi, giri=3, passi=6, stampa=print, sponsor_iniziale=None, anni_gloria=None, rapporto_richiesta=None,
                   gloria_iniziale=None, giri_gloria=2):
    """
    La taratura dell'economia della tappa 11: prima la scala, in forma chiusa, rifatta per qualche
    giro finché non si sposta più; poi lo sponsor per punto di gloria, per bisezione, perché la cassa
    mediana delle polisportive del computer torni al bersaglio. Restituisce A, B, lo sponsor e le righe.
    Dalla tappa 12, punto 13.4 del progetto, con anni_gloria viene prima la gloria, in quell'anno, dove
    la finestra di cinque anni del calendario è piena: i due coefficienti del palmarès perché faccia la
    metà della gloria della polisportiva mediana del computer e il 65 per cento del primo decimo,
    risposta 11 di Gabriele, e con rapporto_richiesta il fattore comune della gloria richiesta, perché
    il rapporto fra la gloria richiesta mediana dei liberi e la gloria mediana del computer resti quello
    della 1.60.11; tutto in forma chiusa sul campione di una corsa, rifatto per giri_gloria giri. Poi la
    scala e lo sponsor come prima, negli anni dati, con la gloria trovata.
    """
    righe = []

    def annota(riga):
        righe.append(riga)
        if stampa:
            stampa(riga)

    a, b = costanti.SCALA_VALORE_A, costanti.SCALA_VALORE_B
    sponsor = costanti.SPONSOR_PER_GLORIA if sponsor_iniziale is None else sponsor_iniziale
    gloria = gloria_iniziale
    altro = {} if gloria is None else {"gloria": gloria}
    if anni_gloria:
        gloria = gloria or gloria_in_vigore()
        for giro in range(1, giri_gloria + 1):
            risultati = con_scala(anni_gloria, semi, a, b, processi, sponsor, gloria=gloria)
            annota(f"Giro {giro} della gloria, all'anno {anni_gloria}. " + riga_della_scala(a, b, risultati, sponsor, gloria))
            k_medaglie, k_coppe, fattore, quote = gloria_in_forma_chiusa([m["campione_gloria"] for m in risultati.values()], rapporto=rapporto_richiesta)
            gloria = (round(k_medaglie, 2), round(k_coppe, 2), round(fattore, 3) if fattore is not None else gloria[2])
            annota(f"La gloria in forma chiusa dal giro {giro}: K_GLORIA_MEDAGLIE {numero(gloria[0], 2)}, K_GLORIA_COPPE {numero(gloria[1], 2)}, fattore della gloria "
                   f"richiesta {numero(gloria[2], 3)}; sul campione la quota del palmarès va al {numero(quote[0], 1)} per cento alla mediana e al {numero(quote[1], 1)} "
                   "al primo decimo.")
        altro = {"gloria": gloria}
    risultati = None
    for giro in range(1, giri + 1):
        risultati = con_scala(anni, semi, a, b, processi, sponsor, **altro)
        annota(f"Giro {giro} della scala. " + riga_della_scala(a, b, risultati, sponsor, gloria))
        nuova_a, nuova_b = scala_in_forma_chiusa([(m["somme_attivi"], m["tesserati_campione"]) for m in risultati.values()])
        annota(f"La scala in forma chiusa dal giro {giro}: A {numero(nuova_a, 2)}, B {numero(nuova_b, 4)}.")
        fermo = abs(nuova_b - b) < 0.005 * b and abs(nuova_a - a) < 0.5
        a, b = nuova_a, nuova_b
        if fermo:
            break

    def cassa_con(sponsor_provato):
        prova = con_scala(anni, semi, a, b, processi, sponsor_provato, **altro)
        annota(riga_della_scala(a, b, prova, sponsor_provato, gloria))
        return statistics.fmean(m["casse"][1] for m in prova.values())

    basso, alto = 0.25 * sponsor, 2.5 * sponsor
    for _passo in range(passi):
        medio = (basso + alto) / 2
        if cassa_con(medio) > cassa_bersaglio:
            alto = medio
        else:
            basso = medio
    sponsor = (basso + alto) / 2
    annota(f"L'economia trovata, da copiare in costanti.py: SCALA_VALORE_A = {a:.2f}, SCALA_VALORE_B = {b:.4f}, SPONSOR_PER_GLORIA = {sponsor:.1f}"
           + (f", K_GLORIA_MEDAGLIE = {gloria[0]:.2f}, K_GLORIA_COPPE = {gloria[1]:.2f}, K_ICV_GLORIA_RICHIESTA = {K_ICV_GLORIA_RICHIESTA_1_60 * gloria[2]:.3f}, "
              f"GLORIA_RICHIESTA_FISSA = {GLORIA_RICHIESTA_FISSA_1_60 * gloria[2]:.2f}" if gloria is not None else "") + ".")
    return a, b, sponsor, righe


def _anni_della_prova_lunga(anni, seme, gloria=None, salva_mondi=None):
    """
    Una prova lunga in un processo a parte: le misure di ogni anno, e dalla tappa 12 quelle di ogni anno
    di calendario. Con salva_mondi, una cartella, vi scrive alla fine il mondo, lunga_SEME_anno_ANNI.json.gz.
    """
    if gloria is not None:
        _imposta(valore.SCALA_VALORE_A, valore.SCALA_VALORE_B, gloria=gloria)
    annuali = []
    misura = MisuraDelCalendario()
    salva = Path(salva_mondi) / f"lunga_{seme}_anno_{anni}.json.gz" if salva_mondi is not None else None
    simula(anni, seme, stampa=None, misura_ogni_anno=False, annuali=annuali, misura_calendario=misura, salva=salva)
    return seme, annuali, misura.anni_dati


# I bersagli nuovi della prova lunga della tappa 12, punto 13.4 del progetto: i liberi in ogni decennio,
# gli attivi a regime, i tornei a testa dei tesserati sani per anno di calendario, i ritiri al meglio dei
# 3 e gli incontri non regolari dei tornei della risposta di Gabriele sugli infortuni, la gloria mediana
# dei decenni rispetto all'anno 20, e i millisecondi del giorno sul GPD.
LIBERI_MINIMI = 5.0
ATTIVI_A_REGIME = (18_500, 22_700)
TORNEI_A_TESTA = (5.0, 6.0)
RITIRI_AL_MEGLIO_DEI_3 = (0.7, 1.4)
UNO_NON_REGOLARE_OGNI = (35.0, 60.0)
SCOSTAMENTO_GLORIA = 20.0
# Dalla verifica del 15 ottobre 2026. I veri campioni tesserati, come i primi 100: almeno 8 dei primi 10
# e 16 dei primi 20, in tutti gli anni. La soglia del mondiale del mondo, il trentaduesimo per punti
# dell'ultimo anno di ogni sesso, in media dall'anno 40 al 60, non più lontana di 15 punti da
# costanti.PUNTI_PER_IL_MONDIALE, che la carriera perfetta usa al posto del mondo: 15 punti spostano
# l'età media di A1 di circa mezzo anno. E la cassa mediana del computer a regime: dall'anno 45 al 60 la
# retta dei minimi quadrati non sale più di PENDENZA_CASSA_MASSIMA euro l'anno, non soltanto la cassa
# dentro la banda. Il bersaglio della decisione 1 di Gabriele del 14 ottobre 2026 era la cassa ferma, 250
# euro l'anno; il 21 ottobre, tolta la decisione 17 che la fermava ma lasciava liberi i campioni, Gabriele
# ha scelto di lasciarla crescere e di allargare la banda: 3.000 euro l'anno, contro i 2.256-2.477 misurati
# il 16 ottobre, così la prova segnala ancora una cassa che corre più del solito.
PRIMI_10_TESSERATI_MINIMI = 8
PRIMI_20_TESSERATI_MINIMI = 16
QUALIFICATI_MONDIALE = 32
SCARTO_SOGLIA_MONDIALE = 15.0
ANNI_SOGLIA_MONDIALE = (40, 60)
ANNI_CASSA_FERMA = (45, 60)
PENDENZA_CASSA_MASSIMA = 3000.0
GIORNO_MEDIO_MASSIMO = 450.0
GIORNO_PEGGIORE_MASSIMO = 650.0


def anno_di_calendario_del(anno_eta, anni_dati):
    """I numeri dell'anno di calendario che contiene la fine di un anno d'età della simulazione, o l'ultimo."""
    giorno = anno_eta * GIORNI_PER_ANNO
    indice = min(len(anni_dati) - 1, max(0, (giorno - 1) // GIORNI_PER_ANNO_DI_CALENDARIO))
    return anni_dati[indice] if anni_dati else None


def controlli_della_tappa_12(anni, semi, risultati):
    """Le righe dei bersagli nuovi della prova lunga, decennio per decennio e anno di calendario per anno di calendario."""
    righe = []
    for seme in semi:
        annuali, anni_dati = risultati[seme][0], risultati[seme][1]
        voci = []
        for decennio in range(10, anni + 1, 10):
            m = next(x for x in annuali if x["numero_anno"] == decennio)
            c = anno_di_calendario_del(decennio, anni_dati)
            liberi = 100.0 - 100.0 * m["tesserati"] / max(1, m["attivi"])
            voci.append(f"anno {decennio}, {m['attivi']} attivi, liberi {numero(liberi, 1)} per cento"
                        + (f", tornei a testa {numero(c['tornei_a_testa_anno'], 2)}, ritiri al meglio dei 3 "
                           f"{numero(100.0 * c['al_meglio_dei_3'][1] / max(1, c['al_meglio_dei_3'][0]), 2)} per cento, uno non regolare ogni "
                           f"{numero(c['incontri'] / max(1, c['ritiri'] + c['tavolini']), 1)}, acciacchi {numero(100.0 * c['acciacchi'] / max(1, c['incontri']), 2)} ogni cento "
                           f"incontri, gloria mediana {numero(c['gloria_mediana'])}, palmarès {numero(c['quota_palmares'][0], 1)} e {numero(c['quota_palmares'][1], 1)} per cento, "
                           f"incontri al giorno {numero(c['incontri_al_giorno'], 1)} e {c['incontri_giorno_peggiore']} nel peggiore, giorno medio {numero(c['ms_medio'])} millisecondi "
                           f"e peggiore {numero(c['ms_peggiore'])}" if c else ""))
        righe.append(f"Seme {seme}, la tappa 12 per decennio: " + "; ".join(voci) + ".")
        fuori = []
        for decennio in range(10, anni + 1, 10):
            m = next(x for x in annuali if x["numero_anno"] == decennio)
            if 100.0 - 100.0 * m["tesserati"] / max(1, m["attivi"]) < LIBERI_MINIMI:
                fuori.append(f"liberi sotto il {numero(LIBERI_MINIMI)} per cento all'anno {decennio}")
        # Dalla decisione 1 di Gabriele del 14 ottobre 2026 il computer tessera i campioni: i primi 100
        # del mondo per valore tesserati almeno all'80 per cento in tutti gli anni, come nello scenario.
        sotto = [m["numero_anno"] for m in annuali if m["primi_100"] < PRIMI_100_TESSERATI_MINIMI]
        if sotto:
            fuori.append(f"primi 100 tesserati sotto l'{numero(PRIMI_100_TESSERATI_MINIMI)} per cento in {len(sotto)} anni, dall'anno {sotto[0]} all'anno {sotto[-1]}")
        fuori.extend(fuori_dai_controlli_della_verifica(annuali))
        ultimo = annuali[-1]
        if anni >= 50 and not ATTIVI_A_REGIME[0] <= ultimo["attivi"] <= ATTIVI_A_REGIME[1]:
            fuori.append(f"{ultimo['attivi']} attivi alla fine, fuori da {ATTIVI_A_REGIME[0]} e {ATTIVI_A_REGIME[1]}")
        pieni = [c for c in anni_dati if c["giorni"] == GIORNI_PER_ANNO_DI_CALENDARIO and c["anno"] >= 3]
        for c in pieni:
            ritiri = 100.0 * c["al_meglio_dei_3"][1] / max(1, c["al_meglio_dei_3"][0])
            ogni = c["incontri"] / max(1, c["ritiri"] + c["tavolini"])
            if not TORNEI_A_TESTA[0] <= c["tornei_a_testa_anno"] <= TORNEI_A_TESTA[1]:
                fuori.append(f"anno di calendario {c['anno']}, tornei a testa {numero(c['tornei_a_testa_anno'], 2)}")
            if not RITIRI_AL_MEGLIO_DEI_3[0] <= ritiri <= RITIRI_AL_MEGLIO_DEI_3[1]:
                fuori.append(f"anno di calendario {c['anno']}, ritiri {numero(ritiri, 2)} per cento")
            if not UNO_NON_REGOLARE_OGNI[0] <= ogni <= UNO_NON_REGOLARE_OGNI[1]:
                fuori.append(f"anno di calendario {c['anno']}, uno non regolare ogni {numero(ogni, 1)}")
            if c["ms_medio"] > GIORNO_MEDIO_MASSIMO or c["ms_peggiore"] > GIORNO_PEGGIORE_MASSIMO:
                fuori.append(f"anno di calendario {c['anno']}, giorno medio {numero(c['ms_medio'])} e peggiore {numero(c['ms_peggiore'])} millisecondi")
        al_20 = anno_di_calendario_del(20, anni_dati)
        for decennio in (20, 40, 60):
            c = anno_di_calendario_del(decennio, anni_dati)
            if decennio <= anni and al_20 and c and abs(c["gloria_mediana"] / max(1.0, al_20["gloria_mediana"]) - 1.0) * 100.0 > SCOSTAMENTO_GLORIA:
                fuori.append(f"gloria mediana all'anno {decennio} {numero(c['gloria_mediana'])} contro {numero(al_20['gloria_mediana'])} all'anno 20")
        righe.append(f"Seme {seme}, i bersagli nuovi della tappa 12: " + ("tutti dentro." if not fuori else "FUORI " + "; ".join(fuori) + "."))
    return righe


# I bersagli dello staff della tappa 13, progetto 6.3: almeno il 95 per cento delle polisportive del computer
# con un capo dall'anno 5; gli allenatori liberi sempre almeno quanti le polisportive senza capo; lo staff
# non oltre un quinto del monte stipendi del computer.
CON_CAPO_MINIMO = 95.0
ANNO_DEL_CAPO = 5
STAFF_SUL_MONTE_MASSIMO = 20.0


def controlli_della_tappa_13(anni, semi, risultati):
    """Le righe dello staff della prova lunga: per decennio i numeri, poi i bersagli del progetto 6.3."""
    righe = []
    for seme in semi:
        annuali = [m for m in risultati[seme] if "con_capo" in m]
        if not annuali:
            continue
        voci = []
        for decennio in range(10, anni + 1, 10):
            m = next((x for x in annuali if x["numero_anno"] == decennio), None)
            if m is None:
                continue
            q10, q50, q90 = m["qualita_staff"]
            lettere = ", ".join(f"{lettera} {quanti}" for lettera, quanti in sorted(m["liberi_per_lettera"].items())) or "nessuno"
            voci.append(f"anno {decennio}, con un capo {numero(m['con_capo'], 1)} per cento, staff pieno {numero(m['staff_pieno'], 1)}, qualità "
                        f"{numero(q10, 2)}, {numero(q50, 2)} e {numero(q90, 2)}, staff sul monte {numero(m['staff_sul_monte'], 1)} per cento, "
                        f"allenatori {m['allenatori']}, liberi {m['allenatori_liberi']} ({lettere})")
        righe.append(f"Seme {seme}, lo staff per decennio: " + "; ".join(voci) + ".")
        fuori = []
        pochi = [m["numero_anno"] for m in annuali if m["numero_anno"] >= ANNO_DEL_CAPO and m["con_capo"] < CON_CAPO_MINIMO]
        if pochi:
            fuori.append(f"polisportive con un capo sotto il {numero(CON_CAPO_MINIMO)} per cento in {len(pochi)} anni, dall'anno {pochi[0]} all'anno {pochi[-1]}, "
                         f"al più basso {numero(min(m['con_capo'] for m in annuali if m['numero_anno'] >= ANNO_DEL_CAPO), 1)}")
        scarsi = [m["numero_anno"] for m in annuali if m["allenatori_liberi"] < m["senza_capo"]]
        if scarsi:
            fuori.append(f"allenatori liberi meno delle polisportive senza capo in {len(scarsi)} anni, dall'anno {scarsi[0]} all'anno {scarsi[-1]}")
        cari = [m["numero_anno"] for m in annuali if m["staff_sul_monte"] > STAFF_SUL_MONTE_MASSIMO]
        if cari:
            fuori.append(f"staff oltre il {numero(STAFF_SUL_MONTE_MASSIMO)} per cento del monte in {len(cari)} anni, dall'anno {cari[0]} all'anno {cari[-1]}")
        righe.append(f"Seme {seme}, i bersagli dello staff della tappa 13: " + ("tutti dentro." if not fuori else "FUORI " + "; ".join(fuori) + "."))
    return righe


def fuori_dai_controlli_della_verifica(annuali):
    """
    I controlli della verifica del 15 ottobre 2026, sulle misure di ogni anno che li hanno: i primi 10 e
    i primi 20 tesserati, la soglia del mondiale del mondo contro quella della carriera perfetta, e la
    cassa mediana del computer ferma a regime. Restituisce le frasi di quello che sta fuori.
    """
    fuori = []
    for chiave, minimo, quanti in (("primi_10", PRIMI_10_TESSERATI_MINIMI, 10), ("primi_20", PRIMI_20_TESSERATI_MINIMI, 20)):
        sotto = [m["numero_anno"] for m in annuali if chiave in m and m[chiave] < minimo]
        if sotto:
            peggiore = min(m[chiave] for m in annuali if chiave in m)
            fuori.append(f"dei primi {quanti} tesserati meno di {minimo} in {len(sotto)} anni, dall'anno {sotto[0]} all'anno {sotto[-1]}, al più basso {peggiore}")
    soglie = [m["soglia_mondiale"] for m in annuali if "soglia_mondiale" in m and ANNI_SOGLIA_MONDIALE[0] <= m["numero_anno"] <= ANNI_SOGLIA_MONDIALE[1]]
    for sesso, chi in (("m", "gli uomini"), ("f", "le donne")):
        if soglie:
            media = statistics.fmean(s[sesso] for s in soglie)
            if abs(media - costanti.PUNTI_PER_IL_MONDIALE[sesso]) > SCARTO_SOGLIA_MONDIALE:
                fuori.append(f"soglia del mondiale per {chi} dall'anno {ANNI_SOGLIA_MONDIALE[0]} al {ANNI_SOGLIA_MONDIALE[1]} in media {numero(media)} punti, "
                             f"contro {numero(costanti.PUNTI_PER_IL_MONDIALE[sesso])} della carriera perfetta")
    casse = [(m["numero_anno"], m["casse"][1]) for m in annuali if ANNI_CASSA_FERMA[0] <= m["numero_anno"] <= ANNI_CASSA_FERMA[1]]
    if len(casse) >= 2:
        pendenza = statistics.linear_regression([a for a, _c in casse], [c for _a, c in casse]).slope
        if pendenza > PENDENZA_CASSA_MASSIMA:
            fuori.append(f"cassa mediana del computer che cresce di {numero(pendenza)} euro l'anno dall'anno {casse[0][0]} al {casse[-1][0]}, "
                         f"oltre i {numero(PENDENZA_CASSA_MASSIMA)}")
    return fuori


def fuori_dalla_solvibilita(annuali):
    """Gli anni in cui il computer non resta in grado di pagare: tesserati sotto l'85 per cento, o cassa mediana fuori da 2.000 e 15.000 euro."""
    fuori = []
    for m in annuali:
        tesserati = 100.0 * m["tesserati"] / max(1, m["attivi"])
        cassa = m["casse"][1]
        if tesserati < TESSERATI_MINIMI_PROVA_LUNGA or not CASSA_MEDIANA_PROVA_LUNGA[0] <= cassa <= CASSA_MEDIANA_PROVA_LUNGA[1]:
            fuori.append((m["numero_anno"], tesserati, cassa))
    return fuori


def prova_lunga(anni, semi, processi, stampa=print, gloria=None, salva_mondi=None):
    """
    La prova lunga: tanti anni su più semi in parallelo. Per decennio il valore mediano, gli
    stipendi pagati e le casse del computer; anno per anno il controllo di solvibilità.
    Restituisce le righe del racconto. Dalla tappa 12 anche i bersagli nuovi, controlli_della_tappa_12;
    con salva_mondi, una cartella, il mondo di ogni seme alla fine, per misurare il giorno a regime.
    """
    from simulazione_lunga import _anni_della_prova_lunga as lavoro
    with ProcessPoolExecutor(max_workers=max(1, min(processi, len(semi)))) as esecutore:
        futuri = [esecutore.submit(lavoro, anni, seme, gloria, salva_mondi) for seme in semi]
        completi = {seme: (annuali, anni_dati) for seme, annuali, anni_dati in [f.result() for f in futuri]}
    risultati = {seme: annuali for seme, (annuali, _anni_dati) in completi.items()}
    righe = [f"Prova lunga, {anni} anni sui semi {', '.join(str(s) for s in semi)}."]
    for decennio in range(10, anni + 1, 10):
        voci = []
        for seme in semi:
            m = next(x for x in risultati[seme] if x["numero_anno"] == decennio)
            s10, s50, s90 = m["stipendi"]
            voci.append(f"seme {seme}: valore mediano {numero(m['valore'][1], 1)}, stipendi {numero(s10)}, {numero(s50)} e {numero(s90)}, cassa mediana {numero(m['casse'][1])}, "
                        f"tesserati {numero(100 * m['tesserati'] / max(1, m['attivi']))} per cento su {m['attivi']}, primi 100 tesserati al {numero(m['primi_100'])} per cento, "
                        f"dei primi 10 {m.get('primi_10', '?')} e dei primi 20 {m.get('primi_20', '?')}, soglia del mondiale "
                        f"{numero(m.get('soglia_mondiale', {}).get('m', 0))} e {numero(m.get('soglia_mondiale', {}).get('f', 0))}, "
                        f"gloria mediana del computer {numero(m['gloria_mediana'])}, rapporto della gloria richiesta {numero(m['rapporto_richiesta'], 3)}, un giorno {numero(m['millisecondi'])} millisecondi")
        righe.append(f"Anno {decennio}: " + "; ".join(voci) + ".")
    for seme in semi:
        fuori = fuori_dalla_solvibilita(risultati[seme])
        if fuori:
            righe.append(f"Seme {seme}, anni fuori dalla solvibilità: " + "; ".join(f"anno {a}, tesserati {numero(t)} per cento, cassa mediana {numero(c)}" for a, t, c in fuori) + ".")
        else:
            righe.append(f"Seme {seme}: per tutti i {anni} anni tesserati almeno all'{numero(TESSERATI_MINIMI_PROVA_LUNGA)} per cento e cassa mediana fra "
                         f"{numero(CASSA_MEDIANA_PROVA_LUNGA[0])} e {numero(CASSA_MEDIANA_PROVA_LUNGA[1])} euro, dentro.")
    righe.extend(controlli_della_tappa_12(anni, semi, completi))
    righe.extend(controlli_della_tappa_13(anni, semi, risultati))
    for riga in righe:
        if stampa:
            stampa(riga)
    return righe, completi


def spesa_mensile_utente(sponsor, cassa):
    """
    Il monte stipendi che lo scenario si permette per la polisportiva dell'utente: la regola del computer
    della 1.60.11, lo sponsor più un ventiquattresimo della cassa, senza il premio della cassa piena della
    decisione 1 di Gabriele del 14 ottobre 2026. La polisportiva dell'utente nasce coi 20.000 euro del
    capitale, sopra la soglia della cassa piena, e col premio i primi ingaggi si permettevano fino a circa
    1.060 euro al mese di stipendi in più: la cassa del primo anno finiva a 6.700-9.100 euro invece che
    attorno ai 3.000 su cui Gabriele, con la decisione 2, aveva scelto di lasciare la partenza com'era.
    Verifica del 15 ottobre 2026.
    """
    return sponsor + cassa / costanti.PARTI_DI_CASSA_PER_STIPENDI


class ScenarioUtente:
    """
    L'utente che allena e rinnova, dal giorno in cui nasce la sua polisportiva: tessera i giovani più
    forti fra i liberi, gioca le amichevoli, spende tutti i punti, rinnova chi può pagare e paga gli
    arretrati. Conta, anno per anno, quello che serve ai bersagli dello scenario.
    """

    def __init__(self, primo_giorno, seme):
        self.primo_giorno = primo_giorno
        self.rng = random.Random(f"scenario-utente-{seme}")
        self.poli = None
        self.motore = None
        self.ieri = set()
        self.liberati = set()
        self.mancati = set()
        self.anni = []
        self.anno = self._anno_vuoto()
        self._conti_di_ieri = {}
        self._tornei_di_ieri = {}
        self._medaglie_di_ieri = (0, 0, 0, 0)

    @staticmethod
    def _anno_vuoto():
        return {"sponsor": 0, "sponsor_valore": 0.0, "stipendi": 0, "giorni": 0, "cassa_minima": None, "tesserati": 0, "andati_via": 0, "rinnovi": 0, "rinnovi_rifiutati": 0,
                "rinnovi_mancati": 0, "amichevoli": 0, "spese": 0, "iscrizioni": 0, "premi": 0, "rimborsi": 0, "tornei": 0, "giorni_di_tesserati": 0,
                "giorni_acciaccati": 0, "giorni_infortunati": 0, "medaglie": [0, 0, 0, 0], "reputazione": [], "rinnovo_su_richiesta": [],
                "staff_assunti": 0, "staff_rifiuti": 0, "staff_rinnovi": 0, "staff_mancati": 0, "giorni_con_capo": 0, "qualita_staff": 0.0}

    def __call__(self, mondo, giorno, rapporto):
        if giorno < self.primo_giorno:
            return
        if self.poli is None:
            self.poli = mondo.fonda_polisportiva(NOME_UTENTE, attiva=True)
            self.motore = MotorePartita(mondo)
        poli = self.poli
        oggi = mondo.datetime_corrente_simulazione
        rosa_di_oggi = set(poli.tesserati)
        andati = self.ieri - rosa_di_oggi
        self.liberati |= andati
        self.anno["andati_via"] += len(andati)
        self._paga_arretrati(mondo)
        self._tessera(mondo)
        self._amichevoli(mondo, giorno)
        self._allena(mondo, oggi)
        self._rinnovi(mondo, oggi)
        self._staff(mondo, oggi)
        rosa = mondo._rosa(poli)
        self.anno["sponsor"] += mondo.sponsor(poli)
        self.anno["sponsor_valore"] += costanti.QUOTA_SPONSOR_SUL_VALORE * sum(economia.valore_di_mercato_pieno(g) for g in rosa if not g.ritirato)
        self.anno["stipendi"] += mondo.monte_stipendi(poli)
        self.anno["giorni"] += 1
        self.anno["cassa_minima"] = poli.cassa if self.anno["cassa_minima"] is None else min(self.anno["cassa_minima"], poli.cassa)
        self.anno["giorni_con_capo"] += bool(poli.staff[0])
        self.anno["qualita_staff"] += staff.qualita_della_polisportiva(poli, mondo.allenatori)
        self._conta_i_tornei(mondo, poli, rosa, oggi)
        self.ieri = set(poli.tesserati)
        if (giorno - self.primo_giorno + 1) % GIORNI_PER_ANNO == 0:
            liberi_ora = [mondo.giocatori[gid] for gid in self.liberati if gid in mondo.giocatori and gid not in mondo._ids_morti_processati_sessione]
            presi = sum(1 for g in liberi_ora if g.appartenenza not in ("*", poli.nome))
            primi = misure(mondo)["primi_100"]
            self.anni.append({**self.anno, "cassa": poli.cassa, "tesserati": len(rosa), "liberati": len(self.liberati), "presi_da_altri": presi,
                              "valore_medio": statistics.fmean(g.indice_collettivo_valore for g in rosa) if rosa else 0.0,
                              "stipendio_medio": statistics.fmean(economia.stipendio_pagato(g) for g in rosa) if rosa else 0.0,
                              "richiesto_medio": statistics.fmean(economia.stipendio(g) for g in rosa) if rosa else 0.0,
                              "classe_migliore": min((classe.classe(g).livello for g in rosa), default=100), "primi_100": primi, "gloria": poli.gloria,
                              "qualita_media_del_mondo": mondo.qualita_media_dello_staff, "staff_sul_monte": 100.0 * mondo.monte_dello_staff(poli) / max(1, mondo.monte_stipendi(poli))})
            self.anno = self._anno_vuoto()

    def _conta_i_tornei(self, mondo, poli, rosa, oggi):
        """
        I tornei della tappa 12 nello scenario: le quote, i premi e i rimborsi dei conti del giorno, i
        tornei giocati dai tesserati, le medaglie della polisportiva, e i giorni da acciaccati e da
        infortunati dei tesserati. I conti del mese ripartono il primo: quando una voce scende, la
        differenza è la voce stessa.
        """
        for voce in ("iscrizioni", "premi", "rimborsi"):
            adesso, ieri = poli.conti_del_mese.get(voce, 0), self._conti_di_ieri.get(voce, 0)
            self.anno[voce] += adesso - ieri if adesso >= ieri else adesso
            self._conti_di_ieri[voce] = adesso
        for g in rosa:
            prima = self._tornei_di_ieri.get(g.id, g.tornei_giocati)
            self.anno["tornei"] += max(0, g.tornei_giocati - prima)
            self._tornei_di_ieri[g.id] = g.tornei_giocati
            self.anno["giorni_di_tesserati"] += 1
            self.anno["giorni_acciaccati"] += infortuni.calo_acciacco(g, oggi) > 0.0
            self.anno["giorni_infortunati"] += bool(g.infortunato)
        medaglie = (poli.ori, poli.argenti, poli.bronzi, poli.legni)
        for i in range(4):
            self.anno["medaglie"][i] += max(0, medaglie[i] - self._medaglie_di_ieri[i])
        self._medaglie_di_ieri = medaglie

    def _paga_arretrati(self, mondo):
        for g in sorted(mondo._rosa(self.poli), key=lambda g: g.pazienza):
            importo = min(g.arretrati, self.poli.cassa)
            if importo > 0:
                mondo.paga(self.poli, g, importo)

    def _tessera(self, mondo):
        """
        Riempie la rosa con i liberi più forti fino a 30 anni, offrendo il 30 per cento in più dell'ingaggio,
        se il monte stipendi sta nella regola di spesa dell'utente, spesa_mensile_utente.
        """
        poli = self.poli
        if len(poli.tesserati) >= TESSERATI_UTENTE or mondo.mosse_rimaste(poli) <= 0:
            return
        liberi = [g for g in mondo.trova_giocatori_liberi_ordinati().values() if g.puo_giocare and g.eta_anni <= ETA_MASSIMA_UTENTE]
        for g in liberi:
            if len(poli.tesserati) >= TESSERATI_UTENTE or mondo.mosse_rimaste(poli) <= 0:
                return
            ingaggio = economia.arrotonda(economia.ingaggio_richiesto(g, poli) * RIALZO_INGAGGIO_UTENTE)
            monte = mondo.monte_stipendi(poli) + economia.stipendio(g)
            sponsor = mondo.sponsor(poli) + costanti.QUOTA_SPONSOR_SUL_VALORE * economia.valore_di_mercato_pieno(g)
            if ingaggio + monte > poli.cassa or monte > spesa_mensile_utente(sponsor, poli.cassa - ingaggio):
                continue
            if mondo.problema_offerta(poli, g, ingaggio) is None:
                reputazione = economia.fattore_reputazione(g, poli)
                mondo.offerta(poli, g, ingaggio)
                if g.id in poli.tesserati:
                    self.anno["reputazione"].append(reputazione)

    def _amichevoli(self, mondo, giorno):
        """Un'amichevole ogni due giorni per ciascuno, contro un compagno: oggi gioca metà della rosa, a coppie."""
        rosa = sorted(mondo._rosa(self.poli), key=lambda g: g.id)
        di_turno = [g for i, g in enumerate(rosa) if (i + giorno) % 2 == 0 and g.puo_giocare_amichevole(mondo.datetime_corrente_simulazione)]
        for a, b in zip(di_turno[0::2], di_turno[1::2], strict=False):
            # Dalla tappa 12 il motore estrae gli infortuni e gli acciacchi, e l'amichevole li riceve
            # come nel gioco, con le basi d'infortunio e i cali di oggi.
            basi, cali = self.motore.basi_e_cali(a, b)
            risultato = simula_incontro(a, b, SINGOLARE_3, seme=self.rng.getrandbits(63), dettaglio=ESSENZIALE, basi_infortunio=basi, cali=cali)
            self.motore.registra(risultato)
            self.anno["amichevoli"] += 1

    def _allena(self, mondo, oggi):
        for g in mondo._rosa(self.poli):
            if allenamento.puo_allenarsi(g) and g.punti_allenamento >= 1.0 and allenamento.allena_secondo_programma(g, data=oggi):
                self.anno["spese"] += 1

    def _rinnovi(self, mondo, oggi):
        """
        Propone il rinnovo a chi è nella finestra, alla richiesta e alla durata proposta, se il monte stipendi
        nuovo sta nella regola di spesa dell'utente, spesa_mensile_utente.
        """
        poli = self.poli
        for g in mondo._rosa(poli):
            if mondo.problema_rinnovo(poli, g) is not None:
                continue
            mesi = contratti.durata_proposta(g)
            richiesta = contratti.richiesta_rinnovo(g, poli, mesi)
            self.anno["rinnovo_su_richiesta"].append(richiesta / max(1, economia.stipendio(g)))
            monte = mondo.monte_stipendi(poli) - economia.stipendio_pagato(g) + richiesta
            if monte > spesa_mensile_utente(mondo.sponsor(poli), poli.cassa):
                if g.id not in self.mancati:
                    self.mancati.add(g.id)
                    self.anno["rinnovi_mancati"] += 1
                continue
            accetta, _probabilita, _richiesta = mondo.rinnova(poli, g, max(costanti.STIPENDIO_MINIMO, richiesta), mesi)
            self.anno["rinnovi" if accetta else "rinnovi_rifiutati"] += 1


    def _staff(self, mondo, oggi):
        """
        Dalla tappa 13, progetto 6.3: l'utente tiene uno staff medio. Per ogni posto vuoto, dal capo, offre
        l'ingaggio chiesto più il rialzo dei tesserati all'allenatore libero con la qualità più vicina allo
        staff medio del mondo, se lo stipendio sta nella regola di spesa dell'utente e l'ingaggio nella
        cassa; nella finestra rinnova alla richiesta, con la stessa regola. Nella simulazione non c'è l'ora
        riservata: l'utente sceglie a fine giorno, dopo il computer, fra chi è rimasto libero, cioè i nati e
        i ritirati del giorno e chi il computer non si può permettere.
        """
        poli = self.poli
        for a in [mondo.allenatori[n] for n in poli.staff if n and n in mondo.allenatori]:
            if mondo.problema_rinnovo_allenatore(poli, a) is not None:
                continue
            mesi = staff.durata_proposta(a, oggi)
            richiesta = staff.richiesta_rinnovo(a, poli, mesi, oggi)
            monte = mondo.monte_stipendi(poli) - a.contratto_stipendio + richiesta
            if monte > spesa_mensile_utente(mondo.sponsor(poli), poli.cassa):
                self.anno["staff_mancati"] += 1
                continue
            accetta, _probabilita, _richiesta = mondo.rinnova_allenatore(poli, a, richiesta, mesi)
            self.anno["staff_rinnovi"] += accetta
        media = mondo.qualita_media_dello_staff
        for posto in range(staff.POSTI):
            if poli.staff[posto] or mondo.mosse_rimaste(poli) <= 0:
                continue
            ruolo = staff.CAPO if posto == 0 else staff.ASSISTENTE
            for a in sorted((a for a in mondo.allenatori.values() if a.libero and a.prelazione in (None, poli.nome)), key=lambda a: (abs(a.qualita - media), a.numero)):
                ingaggio = economia.arrotonda(staff.ingaggio_richiesto(a, ruolo, poli) * RIALZO_INGAGGIO_UTENTE)
                monte = mondo.monte_stipendi(poli) + staff.stipendio_richiesto(a, ruolo)
                if ingaggio + monte > poli.cassa or monte > spesa_mensile_utente(mondo.sponsor(poli), poli.cassa - ingaggio):
                    continue
                accetta, _probabilita = mondo.offerta_allenatore(poli, a, posto, ingaggio)
                self.anno["staff_assunti" if accetta else "staff_rifiuti"] += 1
                break


def _scenario_di_un_seme(seme, anni_prima, anni_utente):
    """Lo scenario dell'utente su un seme, in un processo a parte: gli anni dell'utente e le misure del mondo di ogni anno."""
    scenario = ScenarioUtente(anni_prima * GIORNI_PER_ANNO + 1, seme)
    annuali = []
    simula(anni_prima + anni_utente, seme, stampa=None, misura_ogni_anno=False, ogni_giorno=scenario, annuali=annuali)
    return seme, scenario.anni, annuali


def scenario_utente(semi, processi, anni_prima=ANNI_PRIMA_DELL_UTENTE, anni_utente=ANNI_DELL_UTENTE, stampa=print):
    """Lo scenario dell'utente che allena e rinnova, su più semi in parallelo: le righe del racconto, con i bersagli."""
    from simulazione_lunga import _scenario_di_un_seme as lavoro
    with ProcessPoolExecutor(max_workers=max(1, min(processi, len(semi)))) as esecutore:
        risultati = [f.result() for f in [esecutore.submit(lavoro, seme, anni_prima, anni_utente) for seme in semi]]
    righe = [f"Scenario dell'utente che allena e rinnova: la sua polisportiva nasce all'anno {anni_prima} e vive {anni_utente} anni, sui semi "
             f"{', '.join(str(s) for s in semi)}. Tiene {TESSERATI_UTENTE} tesserati, scelti fra i liberi più forti fino a {numero(ETA_MASSIMA_UTENTE)} anni con "
             f"l'ingaggio chiesto più il {numero(100 * (RIALZO_INGAGGIO_UTENTE - 1))} per cento; ognuno gioca un'amichevole ogni due giorni contro un compagno; "
             "ogni giorno Allena tutti; i rinnovi alla richiesta, se il monte stipendi sta nella regola del computer. Dalla tappa 13 tiene uno staff "
             "medio: per ogni posto vuoto l'allenatore libero con la qualità più vicina allo staff medio del mondo, se lo paga."]
    esiti = {"sponsor": True, "primi": True, "partenza": True}
    tornei_per_atleta = []
    for seme, anni, annuali in risultati:
        for indice, a in enumerate(anni, start=1):
            rapporto = 100.0 * a["sponsor"] / max(1, a["stipendi"])
            esiti["sponsor"] = esiti["sponsor"] and rapporto <= SPONSOR_SU_STIPENDI_MASSIMO
            esiti["primi"] = esiti["primi"] and a["primi_100"] >= PRIMI_100_TESSERATI_MINIMI
            if indice <= ANNI_DI_PARTENZA:
                esiti["partenza"] = esiti["partenza"] and rapporto >= SPONSOR_SU_STIPENDI_PARTENZA
            atleti = a["giorni_di_tesserati"] / max(1, a["giorni"])
            tornei_l_anno = a["tornei"] / max(1e-9, atleti) * GIORNI_PER_ANNO_DI_CALENDARIO / max(1, a["giorni"])
            tornei_per_atleta.append(tornei_l_anno)
            righe.append(f"Seme {seme}, anno {indice} dell'utente: cassa {numero(a['cassa'])} euro, la più bassa {numero(a['cassa_minima'] or 0)}; "
                         f"lo sponsor è il {numero(rapporto)} per cento degli stipendi pagati, la sua parte legata al valore della rosa il "
                         f"{numero(100.0 * a['sponsor_valore'] / max(1, a['stipendi']))}; gloria {a['gloria']}; {a['tesserati']} tesserati, valore medio {numero(a['valore_medio'], 1)}, "
                         f"la classe migliore {classe.codice(a['classe_migliore'])}; stipendio pagato medio {numero(a['stipendio_medio'])} euro, richiesto {numero(a['richiesto_medio'])}; "
                         f"ingaggi firmati {len(a['reputazione'])}, fattore di reputazione medio {numero(statistics.fmean(a['reputazione']), 3) if a['reputazione'] else 'nessuno'}; "
                         f"richiesta di rinnovo sullo stipendio chiesto, in media, {numero(statistics.fmean(a['rinnovo_su_richiesta']), 3) if a['rinnovo_su_richiesta'] else 'nessuna'}; "
                         f"rinnovi {a['rinnovi']}, rifiutati {a['rinnovi_rifiutati']}, mancati per mancanza di soldi {a['rinnovi_mancati']}; "
                         f"andati via {a['andati_via']}, tornati liberi finora {a['liberati']}, di cui presi da altri {a['presi_da_altri']}; "
                         f"amichevoli {a['amichevoli']}, spese {a['spese']}; tornei dei tesserati {a['tornei']}, {numero(tornei_l_anno, 2)} a testa per anno di calendario; "
                         f"quote {numero(a['iscrizioni'])} euro, premi {numero(a['premi'])}, rimborsi {numero(a['rimborsi'])}; medaglie della polisportiva "
                         f"{a['medaglie'][0]} ori, {a['medaglie'][1]} argenti, {a['medaglie'][2]} bronzi e {a['medaglie'][3]} legni; i tesserati passano acciaccati il "
                         f"{numero(100.0 * a['giorni_acciaccati'] / max(1, a['giorni_di_tesserati']), 1)} per cento dei giorni e infortunati il "
                         f"{numero(100.0 * a['giorni_infortunati'] / max(1, a['giorni_di_tesserati']), 1)}; dei primi 100 del mondo è tesserato il {numero(a['primi_100'])} per cento; "
                         f"lo staff: con un capo il {numero(100.0 * a['giorni_con_capo'] / max(1, a['giorni']))} per cento dei giorni, qualità media "
                         f"{numero(a['qualita_staff'] / max(1, a['giorni']), 2)} contro {numero(a['qualita_media_del_mondo'], 2)} del mondo a fine anno, "
                         f"assunti {a['staff_assunti']}, rifiuti {a['staff_rifiuti']}, rinnovi {a['staff_rinnovi']}, mancati per i soldi {a['staff_mancati']}, "
                         f"staff sul monte il {numero(a['staff_sul_monte'], 1)} per cento.")
        for m in (x for x in annuali if x["numero_anno"] in (anni_prima, anni_prima + anni_utente)):
            s10, s50, s90 = m["stipendi"]
            righe.append(f"Seme {seme}, il mondo all'anno {m['numero_anno']}: {m['attivi']} giocatori in attività, tesserati al {numero(100 * m['tesserati'] / max(1, m['attivi']))} "
                         f"per cento, cassa mediana del computer {numero(m['casse'][1])} euro, stipendi pagati {numero(s10)}, {numero(s50)} e {numero(s90)}, valore mediano "
                         f"{numero(m['valore'][1], 1)}, gloria mediana del computer {numero(m['gloria_mediana'])}, gloria richiesta mediana dei liberi su quella del computer "
                         f"{numero(m['rapporto_richiesta'], 3)}.")
    righe.append(f"I bersagli dello scenario: lo sponsor dell'utente, in media sull'anno, non supera il {numero(SPONSOR_SU_STIPENDI_MASSIMO)} per cento degli stipendi pagati, "
                 f"{'dentro' if esiti['sponsor'] else 'FUORI'}; nei primi {ANNI_DI_PARTENZA} anni non scende sotto il {numero(SPONSOR_SU_STIPENDI_PARTENZA)} per cento, "
                 f"{'dentro' if esiti['partenza'] else 'FUORI'}; dei primi 100 del mondo è tesserato almeno l'{numero(PRIMI_100_TESSERATI_MINIMI)} per cento, "
                 f"{'dentro' if esiti['primi'] else 'FUORI'}; i tesserati dell'utente giocano in media {numero(statistics.fmean(tornei_per_atleta), 2)} tornei "
                 "per anno di calendario, col ritmo dell'iscrizione automatica di un torneo ogni due mesi.")
    for riga in righe:
        if stampa:
            stampa(riga)
    return righe, risultati


def _decimale(testo):
    return float(testo.replace(",", "."))


def main():
    parser = argparse.ArgumentParser(description="Simula il mondo di MESS per molti anni in una cartella temporanea e controlla l'economia.")
    parser.add_argument("--anni", type=int, default=None, help="quanti anni simulare, 10 se non indicato, 60 con --prova-lunga")
    parser.add_argument("--seme", type=int, default=2026, help="il seme del caso del mondo, 2026 se non indicato")
    parser.add_argument("--rapporto", type=Path, default=None, help="salva il racconto anche in questo file")
    parser.add_argument("--semi", type=int, nargs="+", default=None, help="più semi in parallelo, per --scala e --cerca-economia; 2026, 7, 13 e 21 se non indicati")
    parser.add_argument("--scala", type=_decimale, nargs=2, metavar=("A", "B"), default=None, help="simula i semi con questa scala del valore, senza toccare il progetto")
    parser.add_argument("--sponsor", type=_decimale, default=None, help="con --scala o --cerca-economia, lo sponsor per punto di gloria da provare")
    parser.add_argument("--cerca-economia", action="store_true", help="ricava la scala in forma chiusa e cerca per bisezione lo sponsor per punto di gloria")
    parser.add_argument("--cassa", type=float, default=5000.0, help="la cassa mediana delle polisportive del computer cercata, 5000 euro se non indicata")
    parser.add_argument("--giri", type=int, default=3, help="i giri della scala in forma chiusa, 3 se non indicati")
    parser.add_argument("--passi", type=int, default=6, help="i passi della bisezione dello sponsor, 6 se non indicati")
    parser.add_argument("--processi", type=int, default=min(8, os.cpu_count() or 1), help="quanti semi simulare insieme, fino a 8 se il computer li ha")
    parser.add_argument("--prova-lunga", action="store_true", help="i semi per 60 anni, o quelli indicati, con il controllo di solvibilità anno per anno")
    parser.add_argument("--scenario-utente", action="store_true", help="dall'anno 10 una polisportiva dell'utente che allena e rinnova, per dieci anni")
    parser.add_argument("--giorni", type=int, default=None, help="nella simulazione semplice, quanti giorni simulare al posto degli anni, per esempio 1095 per tre anni di calendario")
    parser.add_argument("--salva-popolazione", type=Path, default=None, help="nella simulazione semplice, scrive alla fine i giocatori in attività in questo file JSON compresso")
    parser.add_argument("--anni-gloria", type=int, default=None, help="con --cerca-economia, cerca prima la gloria in quest'anno, 20 per il punto 13.4 della tappa 12")
    parser.add_argument("--rapporto-richiesta", type=_decimale, default=None, help="con --anni-gloria, il rapporto fra gloria richiesta dei liberi e gloria del computer da tenere")
    parser.add_argument("--gloria", type=_decimale, nargs=3, metavar=("KM", "KC", "F"), default=None,
                        help="i coefficienti del palmarès e il fattore della gloria richiesta da provare, con --scala, --cerca-economia o --prova-lunga")
    parser.add_argument("--salva-mondi", type=Path, default=None, help="con --prova-lunga, scrive alla fine il mondo di ogni seme in questa cartella")
    argomenti = parser.parse_args()
    inizio = time.perf_counter()
    semi = argomenti.semi or [2026, 7, 13, 21]
    argomenti.anni = argomenti.anni or (ANNI_PROVA_LUNGA if argomenti.prova_lunga else 10)
    gloria = tuple(argomenti.gloria) if argomenti.gloria else None
    if argomenti.prova_lunga:
        righe, _risultati = prova_lunga(argomenti.anni, semi, argomenti.processi, gloria=gloria, salva_mondi=argomenti.salva_mondi)
        righe.append(f"Prova completata in {numero(time.perf_counter() - inizio)} secondi.")
        print(righe[-1])
    elif argomenti.scenario_utente:
        righe, _risultati = scenario_utente(semi, argomenti.processi)
        righe.append(f"Scenario completato in {numero(time.perf_counter() - inizio)} secondi.")
        print(righe[-1])
    elif argomenti.cerca_economia:
        _a, _b, _s, righe = cerca_economia(argomenti.anni, semi, argomenti.cassa, argomenti.processi, argomenti.giri, argomenti.passi, sponsor_iniziale=argomenti.sponsor,
                                           anni_gloria=argomenti.anni_gloria, rapporto_richiesta=argomenti.rapporto_richiesta, gloria_iniziale=gloria)
        righe = [f"Taratura dell'economia, {argomenti.anni} anni sui semi {', '.join(str(s) for s in semi)}, cassa mediana cercata {numero(argomenti.cassa)} euro.",
                 *righe, f"Ricerca completata in {numero(time.perf_counter() - inizio)} secondi."]
        print(righe[-1])
    elif argomenti.scala:
        a, b = argomenti.scala
        altro = {"gloria": gloria} if gloria else {}
        righe = [riga_della_scala(a, b, con_scala(argomenti.anni, semi, a, b, argomenti.processi, argomenti.sponsor, **altro), argomenti.sponsor, gloria)]
        print(righe[0])
    else:
        mondo, righe = simula(argomenti.anni, argomenti.seme, giorni=argomenti.giorni, misura_calendario=MisuraDelCalendario())
        durata = f"{argomenti.giorni} giorni" if argomenti.giorni else f"{argomenti.anni} anni"
        righe = [f"Simulazione lunga del mondo, {durata} col seme {argomenti.seme}, in {numero(time.perf_counter() - inizio)} secondi.", *righe, *confronto(mondo)]
        for riga in righe[-len(BERSAGLI) - 2:]:
            print(riga)
        if argomenti.salva_popolazione:
            quanti = salva_popolazione(mondo, argomenti.salva_popolazione)
            print(f"Popolazione di {quanti} giocatori in attività salvata in {argomenti.salva_popolazione}.")
    if argomenti.rapporto:
        argomenti.rapporto.write_text("\n".join(righe) + "\n", encoding="utf-8")
        print(f"Racconto salvato in {argomenti.rapporto}.")


if __name__ == "__main__":
    main()
