"""
MESS, l'ascolto di confronto dello schermo centrale, issue 12.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-24 con la decisione D37. All'ascolto alla cieca dello stesso giorno Gabriele ha sentito
uguali tutte e sei le coppie, con il ritorno della pallina dopo lo schermo e senza, e lo schermo non gli
è sembrato quello dello showdown vero, dove la pallina batte contro qualcosa a metà fra i due giocatori,
inverte la direzione e torna da chi l'ha tirata, e il fischio arriva appena tocca. Il ritorno è uscito
dalla partita, e questo strumento gli fa sentire versioni nuove dello schermo contro accanto a quella
di oggi, perché scelga quella che somiglia di più al tavolo vero, o nessuna. Esiti, dado e impronta
del motore non cambiano: le versioni nascono soltanto qui, ritoccando i suoni posati del punto.
Lo studio, sui 142 schermi contro dei 932 punti dei trenta incontri di strumenti/ascolta_partita.py,
composti dalla testata di A senza suonarli, metà tirati da A e metà da B. L'urto di oggi cade a 2 cm
dallo schermo, dalla parte di chi tira, a 223 o 228 cm dal punto d'ascolto: volume 0,40 e taglio della
cupezza fra 4700 e 4900 Hz; il pan è quello della pallina, da -0,9 a 0,9. Il fischio singolo parte
nello stesso campione dell'urto, dall'arbitro, a pan -1, o 1 dopo il cambio campo, a 249 cm, con volume
0,38 e taglio 4300 Hz: urto e fischio vengono dalla stessa distanza, ugualmente incupiti, e quando la
pallina tocca dalla parte dell'arbitro anche dalla stessa direzione. Con la ponderazione A, nei primi
100 ms dopo l'urto, l'urto sta da 7 a 9 dB sotto il fischio, che dura 320 ms contro i suoi 102, e da 7
a 8 dB sotto il colpo del tuo giocatore che l'ha mandato lì; sta da 3 a 4 dB sopra il colpo lontano
dell'avversario, e da 8 a 11 sopra il rotolamento che lo precede. La sua energia è quasi tutta sotto i
600 Hz, 18 dB più che fra 600 e 2000, dove l'orecchio la pesa di meno, mentre fra 2000 e 4000 Hz il
fischio lo supera di 25 dB: l'urto diventa l'attacco del fischio. Il rotolamento del colpo finisce
nell'istante dell'urto, e poi niente dice che la pallina torna: dopo 0,38 secondi arriva il cicalino
del fallo, dalla testata di chi ha tirato, a 40 cm se è il tuo giocatore. Il ritorno tolto, partendo
fra 70 e 120 cm/s, stava 35 dB sotto il fischio e da 30 a 39 sotto il cicalino, e quando il cicalino
finiva rotolava ancora per 0,7 secondi, 25 dB sotto il rotolamento del colpo: non si sentiva.
Le versioni, con le lettere da A a F mescolate in ogni punto. Oggi: lo schermo della partita, com'è.
Netto: un urto nuovo, chiaro e secco, dalla metà strada fra il punto dell'urto e il centro dello
schermo, perché la tavola risuona tutta e perché si stacchi dal fischio, che viene dal lato; il fischio
resta nello stesso istante del tocco. Netto col ritorno: lo stesso urto, poi la pallina ricade sul
tavolo, 70 ms dopo, e torna rotolando verso chi l'ha tirata. Legno col ritorno e plastica col ritorno:
il ritorno con un urto di timbro diverso, una tavola di legno più grave e rimbombante, o una lastra di
plastica dura, più chiara. I tre urti nuovi si sentono forti uguali, da 2 a 3 dB sopra il fischio nei
primi 100 ms, cioè una decina di dB più di oggi, e da 4 a 5 sopra il colpo del tuo giocatore; il picco
più alto dei punti sta intorno a 0,7, sotto il tetto della partita, 0,8. Il ritorno riparte con il
35% della velocità dell'urto, fra 150 e 250 cm/s, 175 in mediana, nella direzione del colpo specchiata
dallo schermo, e si ferma dopo una strada fra 120 e 150 cm, fra 30 e 65 cm dalla linea di chi ha
tirato, in un secondo e mezzo circa; il suo rotolamento è quello della partita, col guadagno 2,5 volte
più alto. Così sta 19 dB sotto il fischio invece di 35, da 18 a 24 sotto il cicalino invece che da 30
a 39, e dopo il cicalino rotola ancora per 0,74 secondi, 14 dB più forte del ritorno tolto e 11 sotto
il rotolamento del colpo. I numeri cambiano di un decibel da una sessione all'altra, perché i rumori
dei preset nascono senza seme.
I timbri candidati sono preset nel formato della collezione di Acusticator, scritti qui in TIMBRI e
non in GBUtils: lo strumento li mette in una collezione sua, in un file temporaneo, che Acusticator
cerca prima di quella condivisa, e partita_sonora.sorgente_del_preset li sintetizza come le altre
sorgenti della partita. Le versioni le compone partita_sonora.componi col suo ritocco dei suoni
posati: al posto dell'urto di oggi quello nuovo, col suo guadagno e la sua posizione, e poi, se c'è, il
ritorno, un volo che la partita non conosce, con la ricaduta e il rotolamento. Fino all'urto le versioni
di un punto sono identiche campione per campione, fischio e cicalino compresi.
I punti sono quelli dell'ascolto della partita: il mondo in memoria col seme fisso e gli incontri
giocati dal motore in modalità completa. Lo strumento sceglie, per ogni parte, i tre schermi contro più
brevi, con al più tre colpi di scambio e colpi diversi, e li compone senza file WAV, dal fischio del via
alla fine dei suoni del punto. Due gruppi: i tiri del tuo giocatore, che tornano verso di te, e quelli
dell'avversario. Ogni punto ha sei lettere: le cinque versioni e una ripetuta, identica campione per
campione, che è il controllo; la versione ripetuta cambia da un punto all'altro, e ognuna lo è almeno
una volta. Le lettere si mescolano con un seme, che si registra. Le versioni di un punto durano uguali,
col silenzio in coda, e hanno lo stesso livello, quello della partita al volume 100, con un margine solo
per tutte.
Il protocollo è quello delle prove alla cieca di Gabriele, che va trattato come uno strumento di
misura. Prima della prova lo strumento dice soltanto come si esegue e che domanda ci sarà: mai che
cosa cambia, mai quale lettera sia oggi, mai che c'è un controllo. Aspetta il via e quello del gruppo,
e lascia qualche secondo di silenzio prima del primo suono. Ogni punto comincia con la rassegna, tutte
le lettere una volta, in ordine, ciascuna annunciata; Escape la interrompe. Poi la scelta: il tasto di
una lettera la fa sentire, spazio ripete l'ultima sentita, s la sceglie, n dice che nessuna somiglia;
dopo la scelta c lascia un commento al punto, Invio prosegue. Invio senza scegliere passa al punto
seguente, Escape chiude i punti del gruppo. Mentre una lettera suona i tasti valgono subito, e la
fermano. In fondo al gruppo c'è il menu comune dei collaudi, di collaudo_comune di GBUtils: r rifà il
gruppo dal primo punto, con la scelta già data ricordata, c commenta, Invio dà il gruppo per superato,
Escape lo chiude senza giudizio, e allora le sue scelte restano nel file ma non contano.
I risultati vanno nel file ascolto_schermo.txt, nella cartella del programma, una riga per voce: in
testa la data e il seme, poi la scelta di ogni punto, con la sola lettera, i commenti dei punti e del
gruppo; alla fine della sessione, e soltanto allora, anche se la si interrompe, che cosa era ogni
versione, quale lettera era quale in ogni punto, con la coppia identica, e il riepilogo: quante volte è
stata scelta ogni versione, nei tiri tuoi e in quelli dell'avversario, quante volte nessuna, quante
volte una delle due lettere identiche, e le lettere scelte. Il riepilogo si legge anche a schermo, a
sessione finita. Di suo lo strumento non scrive righe vuote, perché enter_escape e gruppo vanno a capo
da sé; le sole che restano vengono dal menu di collaudo_comune, che qui non si tocca.
Uso, dalla cartella del programma: python strumenti/ascolto_schermo.py. Con un numero, per esempio
python strumenti/ascolto_schermo.py 4127, usa quel seme, e quindi le stesse lettere di una sessione
passata.
"""

import dataclasses
import json
import math
import os
import random
import sys
import tempfile
import time
from pathlib import Path
from typing import NamedTuple

import numpy as np

STRUMENTI = Path(__file__).resolve().parent
RADICE = STRUMENTI.parent
for cartella in (RADICE, STRUMENTI):
    if str(cartella) not in sys.path:
        sys.path.insert(0, str(cartella))

import ascolta_partita as ap  # noqa: E402
import resa_prototipo as resa  # noqa: E402
from banco_spazio import Annotazioni, Risultati, nuovo_seme, suona  # noqa: E402
from collaudo_comune import gruppo  # noqa: E402
from GBUtils import Acusticator, dgt, enter_escape, key  # noqa: E402

import ascolta_suoni  # noqa: E402
import partita_sonora as ps  # noqa: E402
import percorsi  # noqa: E402
from costanti import LARGHEZZA_TAVOLO  # noqa: E402
from motore import cronaca as C  # noqa: E402
from motore import eventi as E  # noqa: E402
from motore.tavolo import CENTRO_X, MARGINE_GIOCO, traiettoria  # noqa: E402
from testi import conta, unisci  # noqa: E402

FILE_DEI_RISULTATI = "ascolto_schermo.txt"
# Chi ascolta sta sempre alla testata di A, il suo giocatore.
ASCOLTATORE = "A"
# I punti: tre per parte, fra gli schermi contro con al più tre colpi di scambio, i più brevi.
PUNTI_PER_PARTE = 3
ATTACCHI_MASSIMI = 3
GRUPPI = (("A", "Schermo, i tiri del tuo giocatore"), ("B", "Schermo, i tiri dell'avversario"))
# Le lettere di un punto: una per versione, più una versione ripetuta identica, il controllo.
LETTERE = "ABCDEF"
NESSUNA = "nessuna"
# Il silenzio prima di ogni lettera della rassegna, per il suo nome letto da NVDA; la prima del gruppo
# segue il via e ha in più il silenzio dei collaudi. Nella scelta la lettera l'ha appena chiesta chi
# ascolta: quasi niente.
ANTICIPO_LETTERA = 2.0
ANTICIPO_PRIMA_LETTERA = ANTICIPO_LETTERA + ascolta_suoni.SILENZIO_INIZIALE
ANTICIPO_SCELTA = ap.ANTICIPO
# Nella rassegna soltanto Escape ferma il suono, e la interrompe.
TASTI_DELLA_RASSEGNA = frozenset("\x1b")
TASTI_DELLA_SCELTA = frozenset({" ", "\r", "\x1b", "s", "S", "n", "N", *LETTERE, *LETTERE.lower()})
DOMANDA = "quale lettera somiglia di più alla pallina che batte sullo schermo, al tavolo vero"

# I timbri candidati dell'urto e della ricaduta, nel formato della collezione di Acusticator: le
# quartine di nota, durata, panorama e scarto dal volume base, il kind e l'inviluppo. Non stanno in
# GBUtils: lo strumento li scrive in una collezione sua, in un file temporaneo, e Acusticator la cerca
# prima di quella condivisa. Quello che Gabriele sceglierà entrerà nella collezione col suo nome.
TIMBRI = {
    "ascolto_schermo_netto": {
        "descrizione": "MESS, prova dello schermo centrale, l'urto netto: rumore rosa al centro, uno schiocco duro di 3 ms fra 1500 e "
                       "6000 Hz, la tavola secca, 28 ms fra 700 e 2000 Hz, e tre grani dei pallini; 56 ms.",
        "score": [["1500-6000", 0.003, 0.0, 0.45], ["700-2000", 0.028, 0.0, 0.35], ["3000-9000", 0.004, 0.0, 0.0], ["p", 0.006, 0.0, -0.5],
                  ["3500-10000", 0.004, 0.0, -0.1], ["p", 0.008, 0.0, -0.5], ["2500-8000", 0.003, 0.0, -0.2]],
        "kind": 6,
        "adsr": [1.0, 99.0, 0.0, 0.0],
    },
    "ascolto_schermo_legno": {
        "descrizione": "MESS, prova dello schermo centrale, l'urto sulla tavola di legno, più grave: rumore rosa al centro, il colpo di 6 ms "
                       "fra 800 e 3500 Hz e il rimbombo cavo della tavola, 110 ms fra 180 e 380 Hz, poi due grani dei pallini; 131 ms.",
        "score": [["800-3500", 0.006, 0.0, 0.4], ["180-380", 0.11, 0.0, 0.3], ["3000-8000", 0.004, 0.0, -0.1], ["p", 0.008, 0.0, -0.5],
                  ["2800-8000", 0.003, 0.0, -0.25]],
        "kind": 6,
        "adsr": [1.0, 99.0, 0.0, 0.0],
    },
    "ascolto_schermo_plastica": {
        "descrizione": "MESS, prova dello schermo centrale, l'urto su una lastra di plastica dura: rumore rosa al centro, uno schiocco di "
                       "3 ms fra 2500 e 9000 Hz e il corpo chiaro della lastra, 22 ms fra 1200 e 3000 Hz, e tre grani dei pallini; 50 ms.",
        "score": [["2500-9000", 0.003, 0.0, 0.45], ["1200-3000", 0.022, 0.0, 0.35], ["3000-9000", 0.004, 0.0, 0.0], ["p", 0.006, 0.0, -0.5],
                  ["3500-10000", 0.004, 0.0, -0.1], ["p", 0.008, 0.0, -0.5], ["2500-8000", 0.003, 0.0, -0.2]],
        "kind": 6,
        "adsr": [1.0, 99.0, 0.0, 0.0],
    },
    "ascolto_schermo_ricaduta": {
        "descrizione": "MESS, prova dello schermo centrale, la pallina che dopo lo schermo ricade sul tavolo: rumore bianco al centro, il "
                       "guscio che batte, 7 ms fra 250 e 900 Hz, due grani dei pallini, e un rimbalzo più piccolo 45 ms dopo; 71 ms.",
        "score": [["250-900", 0.007, 0.0, 0.1], ["3000-9000", 0.004, 0.0, -0.05], ["p", 0.004, 0.0, -0.5], ["2500-8000", 0.003, 0.0, -0.2],
                  ["p", 0.045, 0.0, -0.5], ["250-900", 0.005, 0.0, -0.15], ["3000-9000", 0.003, 0.0, -0.3]],
        "kind": 5,
        "adsr": [1.0, 99.0, 0.0, 0.0],
    },
}
RICADUTA = "ascolto_schermo_ricaduta"
# Il ritorno: la pallina ricade sul tavolo poco dopo l'urto e torna rotolando verso chi l'ha tirata,
# nella direzione del colpo specchiata dallo schermo, per una strada fra queste distanze, in cm, e si
# ferma fra 30 e 65 cm dalla linea di chi ha tirato. Riparte con questa parte della velocità che aveva
# all'urto, dentro questi limiti, in cm/s, e rallenta sempre allo stesso modo fino a fermarsi, così
# rotola ancora quando il fischio e il cicalino del fallo sono finiti. Il suo rotolamento ha questo
# guadagno in più su quello della partita, perché sotto il fischio e il cicalino si senta.
RITARDO_DELLA_RICADUTA = 0.07
STRADA_DEL_RITORNO = (120.0, 150.0)
RIMBALZO = 0.35
VELOCITA_DEL_RITORNO = (150.0, 250.0)
GUADAGNO_DEL_RITORNO = 2.5
# Il numero dell'evento del ritorno, che dà il caso delle capriole dei pallini: lontano da quelli veri.
SCARTO_DEL_NUMERO = 100_000


class Versione(NamedTuple):
    """
    Una versione dello schermo contro: la chiave, il nome breve e la descrizione, che si svelano solo
    alla fine, il preset dell'urto, None per quello di oggi, il guadagno dell'urto, se l'urto viene
    dalla metà strada fra il punto dell'urto e il centro dello schermo, e se la pallina torna indietro.
    """
    chiave: str
    nome: str
    descrizione: str
    urto: str | None
    guadagno: float
    verso_il_centro: bool
    ritorno: bool


# Il guadagno di ogni urto nuovo, sopra il limitatore delle sorgenti: i tre si sentono forti uguali,
# con la ponderazione A, da 2 a 3 dB sopra il fischio che parte nello stesso istante, misurato nei
# primi 100 ms dopo l'urto. Oggi l'urto sta da 7 a 9 dB sotto.
GUADAGNO_DELL_URTO = {"ascolto_schermo_netto": 2.35, "ascolto_schermo_legno": 1.7, "ascolto_schermo_plastica": 2.8}
VERSIONI = (
    Versione("oggi", "oggi", "lo schermo com'è oggi nella partita: l'urto di mess_partita_schermo dove la pallina tocca, e niente dopo", None, 1.0,
             False, False),
    Versione("netto", "netto", "l'urto netto e secco, più forte, verso il centro dello schermo, senza ritorno", "ascolto_schermo_netto",
             GUADAGNO_DELL_URTO["ascolto_schermo_netto"], True, False),
    Versione("netto_ritorno", "netto col ritorno", "lo stesso urto netto, poi la pallina ricade sul tavolo e torna rotolando verso chi l'ha "
             "tirata", "ascolto_schermo_netto", GUADAGNO_DELL_URTO["ascolto_schermo_netto"], True, True),
    Versione("legno", "legno col ritorno", "l'urto su una tavola di legno, più grave e rimbombante, più forte, verso il centro, e il ritorno",
             "ascolto_schermo_legno", GUADAGNO_DELL_URTO["ascolto_schermo_legno"], True, True),
    Versione("plastica", "plastica col ritorno", "l'urto su una lastra di plastica dura, più chiaro, più forte, verso il centro, e il ritorno",
             "ascolto_schermo_plastica", GUADAGNO_DELL_URTO["ascolto_schermo_plastica"], True, True),
)
PER_CHIAVE = {v.chiave: v for v in VERSIONI}


# I timbri candidati.

_COLLEZIONE = []


def registra_i_timbri():
    """
    Scrive i timbri candidati in una collezione temporanea, una volta per processo, e la fa cercare ad
    Acusticator prima di quella condivisa; restituisce il percorso. La scrittura passa per un file a
    parte e una rinomina, così due processi insieme non leggono mai un file a metà.
    """
    if _COLLEZIONE:
        return _COLLEZIONE[0]
    percorso = os.path.join(tempfile.gettempdir(), "mess_ascolto_schermo_timbri.json")
    provvisorio = f"{percorso}.{os.getpid()}"
    with open(provvisorio, "w", encoding="utf-8") as f:
        json.dump(TIMBRI, f, ensure_ascii=False, indent=1)
    os.replace(provvisorio, percorso)
    Acusticator.collezione(percorso)
    _COLLEZIONE.append(percorso)
    return percorso


# I punti.

def chi_tira(candidato):
    """La parte di chi ha mandato la pallina contro lo schermo: quella del fallo."""
    return next(e.parte for e in candidato.momento.eventi if e.tipo == E.FALLO)


def scegli_punti(candidati):
    """
    I punti dell'ascolto: per ogni parte, A e poi B, i PUNTI_PER_PARTE più brevi che finiscono con lo
    schermo contro, con al più ATTACCHI_MASSIMI colpi di scambio, ciascuno con un colpo diverso finché
    ce ne sono. LookupError se non bastano.
    """
    scelti = []
    for parte, _titolo in GRUPPI:
        buoni = [c for c in candidati
                 if c.momento.esito is not None and c.momento.esito.causa == "schermo_contro" and c.momento.esito.attacchi <= ATTACCHI_MASSIMI
                 and chi_tira(c) == parte]
        buoni.sort(key=lambda c: (c.momento.esito.attacchi, ap.durata_azione(c)))
        presi = []
        for c in buoni:
            if len(presi) < PUNTI_PER_PARTE and c.momento.esito.colpo_decisivo not in {p.momento.esito.colpo_decisivo for p in presi}:
                presi.append(c)
        for c in buoni:
            if len(presi) < PUNTI_PER_PARTE and all(c is not p for p in presi):
                presi.append(c)
        if len(presi) < PUNTI_PER_PARTE:
            raise LookupError(f"Fra i punti giocati ci sono soltanto {len(presi)} schermi contro brevi tirati dalla parte {parte}.")
        scelti.extend(presi)
    return scelti


def volo_dello_schermo(eventi):
    """Il volo che finisce contro lo schermo."""
    return next(e for e in reversed(eventi) if e.tipo == E.VOLO and e.volo and e.volo[-1].tipo == "schermo")


# Le versioni.

def ritorno(volo):
    """
    Il volo della pallina che, dopo l'urto, ricade sul tavolo e torna verso chi l'ha tirata: comincia
    RITARDO_DELLA_RICADUTA dopo l'urto, nella direzione del colpo specchiata dallo schermo, e rotola
    per una strada di STRADA_DEL_RITORNO fino a fermarsi. Il caso viene dal numero del volo, così lo
    stesso punto torna sempre uguale. È un evento VOLO che la partita non conosce: vive soltanto qui.
    """
    urto, prima = volo.volo[-1], volo.volo[-2]
    dx, dy = urto.x - prima.x, urto.y - prima.y
    lunghezza = math.hypot(dx, dy)
    caso = random.Random(volo.n)
    strada = caso.uniform(*STRADA_DEL_RITORNO)
    x = min(LARGHEZZA_TAVOLO - MARGINE_GIOCO, max(MARGINE_GIOCO, urto.x + strada * dx / lunghezza))
    y = urto.y - strada * dy / lunghezza
    strada = math.hypot(x - urto.x, y - urto.y)
    v0 = min(VELOCITA_DEL_RITORNO[1], max(VELOCITA_DEL_RITORNO[0], RIMBALZO * urto.v))
    t0 = urto.t + RITARDO_DELLA_RICADUTA
    tappe = traiettoria((urto.x, urto.y), (x, y), (), v0, t0, v0 * v0 / (2.0 * strada), 0.0, "fermo")
    return dataclasses.replace(volo, n=volo.n + SCARTO_DEL_NUMERO, t=t0, durata=tappe[-1].t - t0, pos=(round(x, 1), round(y, 1)), volo=tappe,
                               colpo=None, dati={"ritorno": True})


def posati_del_ritorno(volo):
    """
    I suoni del ritorno: la ricaduta sul tavolo, dove la pallina ha urtato, e il rotolamento verso chi
    l'ha tirata, quello della partita col guadagno in più del ritorno.
    """
    indietro = ritorno(volo)
    urto = volo.volo[-1]
    ricaduta = ps.Posato("ricaduta", indietro.t, ps.sorgente_del_preset(RICADUTA), np.array([0.0]), [(urto.x, urto.y)], None, indietro.n)
    rotolamento = [dataclasses.replace(p, guadagni=p.guadagni * GUADAGNO_DEL_RITORNO) if p.ruolo == "rotolamento" else p
                   for p in ps.posati_del_volo(indietro)]
    return [ricaduta, *rotolamento]


def ritocco(volo, versione):
    """
    La funzione che partita_sonora.componi applica ai suoni posati del punto per farne la versione: al
    posto dell'urto di oggi quello della versione, col suo guadagno e, se la versione lo vuole, dalla
    metà strada fra il punto dell'urto e il centro dello schermo; poi, se c'è, il ritorno. Il resto
    del punto, fischio e cicalino compresi, resta com'è, campione per campione.
    """
    urto = volo.volo[-1]

    def applica(posati):
        nuovi = []
        for p in posati:
            if p.ruolo == "schermo" and abs(p.t - urto.t) <= ps.TOLLERANZA:
                x = (urto.x + CENTRO_X) / 2.0 if versione.verso_il_centro else p.posizioni[0][0]
                mono = ps.sorgente_del_preset(versione.urto, p.variante)
                nuovi.append(ps.Posato("schermo", p.t, mono, np.array([0.0]), [(x, p.posizioni[0][1])], np.array([versione.guadagno]), p.evento,
                                       p.variante))
            else:
                nuovi.append(p)
        if versione.ritorno:
            nuovi.extend(posati_del_ritorno(volo))
        return nuovi

    return applica


def componi_versione(candidato, versione):
    """La resa di una versione del punto per chi ascolta da A, prima del livello: l'azione composta da partita_sonora, ritoccata se non è quella di oggi."""
    eventi = resa.azione(candidato.momento.eventi)
    if versione.urto is None and not versione.ritorno:
        return ps.componi(eventi, ASCOLTATORE)
    registra_i_timbri()
    return ps.componi(eventi, ASCOLTATORE, ritocco=ritocco(volo_dello_schermo(eventi), versione))


def componi_punto(candidato):
    """
    I buffer di tutte le versioni del punto, come dizionario dalla chiave, ciascuno lungo quanto il più
    lungo col silenzio in coda, e allo stesso livello: quello della partita al volume 100, col margine
    calcolato su tutte insieme, così se una supera il tetto si abbassano tutte dello stesso fattore.
    """
    composte = [componi_versione(candidato, v).buffer for v in VERSIONI]
    lunghezza = max(len(b) for b in composte)
    pile = np.stack([np.concatenate([b, np.zeros((lunghezza - len(b), 2), dtype=np.float32)]) for b in composte])
    pronte = ps.per_la_cassa(pile.reshape(-1, 2), ps.VOLUME_DI_PROGETTO).reshape(pile.shape)
    return {v.chiave: pronte[i] for i, v in enumerate(VERSIONI)}


# La prova.

class Punto(NamedTuple):
    """Un punto dell'ascolto: il punto giocato, chi ha tirato, le chiavi delle versioni nell'ordine delle lettere e i loro buffer."""
    candidato: object
    parte: str
    lettere: tuple
    buffer: dict

    def versione(self, lettera):
        return PER_CHIAVE[self.lettere[LETTERE.index(lettera)]]

    def lettere_di(self, chiave):
        return [lettera for lettera, k in zip(LETTERE, self.lettere, strict=True) if k == chiave]

    @property
    def ripetuta(self):
        """La chiave della versione ripetuta sotto due lettere: il controllo."""
        return next(k for k in self.lettere if self.lettere.count(k) > 1)

    def da_sentire(self, lettera, anticipo):
        """Il buffer della lettera con il silenzio dell'anticipo in testa."""
        silenzio = np.zeros((round(anticipo * ps.FS), 2), dtype=np.float32)
        return np.concatenate([silenzio, self.buffer[self.lettere[LETTERE.index(lettera)]]])


class Gruppo(NamedTuple):
    parte: str
    titolo: str
    punti: list


class Prova:
    """L'ascolto: il seme, i gruppi, le scelte e i commenti, per gruppo e punto, e come si è chiuso ogni gruppo."""

    def __init__(self, seme, gruppi):
        self.seme = seme
        self.gruppi = gruppi
        self.scelte = {}
        self.commenti = {}
        self.svolti = set()
        self.saltati = set()
        self.interrotti = set()
        # Chiusi senza giudizio, con Escape nel menu di fine gruppo: le scelte restano nel file ma non contano.
        self.chiusi = set()


def controlli(rng, quanti):
    """Le versioni da ripetere, una per punto: tutte una volta, in un ordine a caso, e poi da capo."""
    chiavi = []
    while len(chiavi) < quanti:
        giro = [v.chiave for v in VERSIONI]
        rng.shuffle(giro)
        chiavi.extend(giro)
    return chiavi[:quanti]


def prepara(seme, candidati=None):
    """La prova, con le lettere sorteggiate dal seme e tutte le versioni già composte, senza suonare."""
    registra_i_timbri()
    punti = scegli_punti(ap.punti_giocati() if candidati is None else candidati)
    rng = random.Random(seme)
    costruiti = []
    for candidato, ripetuta in zip(punti, controlli(rng, len(punti)), strict=True):
        lettere = [v.chiave for v in VERSIONI] + [ripetuta]
        rng.shuffle(lettere)
        costruiti.append(Punto(candidato, chi_tira(candidato), tuple(lettere), componi_punto(candidato)))
    return Prova(seme, [Gruppo(parte, titolo, [p for p in costruiti if p.parte == parte]) for parte, titolo in GRUPPI])


# L'ascolto.

def rassegna(punto, primo):
    """Tutte le lettere una volta, in ordine, ciascuna annunciata; la prima del gruppo dopo il silenzio dei collaudi. Escape la interrompe."""
    for posto, lettera in enumerate(LETTERE):
        print(f"Lettera {lettera}.")
        anticipo = ANTICIPO_PRIMA_LETTERA if primo and not posto else ANTICIPO_LETTERA
        if suona(punto.da_sentire(lettera, anticipo), TASTI_DELLA_RASSEGNA) == "\x1b":
            print("Rassegna interrotta.")
            return


def invito(corrente):
    """Il prompt della scelta, entro quaranta caratteri, con l'ultima lettera sentita se c'è."""
    if corrente is None:
        return f"\rUna lettera da A a {LETTERE[-1]}, n nessuna\r"
    return f"\r{corrente}: spazio ripete, s sceglie, n nessuna\r"


def detta(scelta):
    """Una scelta detta a parole, con la sola lettera."""
    if scelta is None:
        return "senza scelta"
    if scelta == NESSUNA:
        return "nessuna somiglia al tavolo vero"
    return f"hai scelto la {scelta}"


def commento(prova, chiave):
    """Dopo la scelta: c lascia un commento al punto, Invio prosegue. Falso se si chiude con Escape."""
    tasto = key("\rc per un commento, Invio prosegue\r")
    print()
    if tasto in ("c", "C"):
        testo = dgt("Il tuo commento al punto: ", kind="s", smin=0, smax=2000).strip()
        if testo:
            prova.commenti[chiave] = testo
            print("Commento annotato.")
    if tasto == "\x1b":
        print("Punti chiusi.")
        return False
    return True


def scegli(prova, indice, posto):
    """
    La scelta di un punto. Il tasto di una lettera la fa sentire, spazio ripete l'ultima sentita, o la
    A se non se n'è sentita nessuna, s sceglie l'ultima sentita, n dice nessuna; poi il commento. Invio
    passa oltre lasciando la scelta com'è, Escape chiude i punti del gruppo. I tasti valgono anche mentre
    la lettera suona, e la fermano. Falso se i punti si sono chiusi.
    """
    punto = prova.gruppi[indice].punti[posto]
    chiave = (indice, posto)
    if chiave in prova.scelte:
        print(f"Finora: {detta(prova.scelte[chiave])}.")
    corrente = None
    tasto = None
    while True:
        if tasto is None:
            tasto = key(invito(corrente))
            print()
        scelto, tasto = tasto, None
        if scelto not in TASTI_DELLA_SCELTA:
            continue
        if scelto == " " or scelto.upper() in LETTERE:
            corrente = scelto.upper() if scelto != " " else corrente or LETTERE[0]
            tasto = suona(punto.da_sentire(corrente, ANTICIPO_SCELTA), TASTI_DELLA_SCELTA)
        elif scelto in ("s", "S"):
            if corrente is None:
                print("Prima ascolta una lettera.")
                continue
            prova.scelte[chiave] = corrente
            print(f"Scelta la {corrente}.")
            return commento(prova, chiave)
        elif scelto in ("n", "N"):
            prova.scelte[chiave] = NESSUNA
            print("Nessuna.")
            return commento(prova, chiave)
        elif scelto == "\r":
            return True
        else:
            print("Punti chiusi.")
            return False


def ascolta(prova, indice):
    """I punti di un gruppo, dal primo: la rassegna e la scelta. Falso se si sono chiusi con Escape prima della fine."""
    punti = prova.gruppi[indice].punti
    for posto, punto in enumerate(punti):
        print(f"Punto {posto + 1} di {len(punti)}.")
        rassegna(punto, primo=not posto)
        if not scegli(prova, indice, posto):
            return False
    return True


# I risultati.

def righe_delle_scelte(prova, indice):
    """Le scelte di un gruppo, con le sole lettere, e i commenti dei punti: una riga per voce."""
    il_gruppo = prova.gruppi[indice]
    righe = []
    for posto in range(len(il_gruppo.punti)):
        righe.append(f"{il_gruppo.titolo}, punto {posto + 1}: {detta(prova.scelte.get((indice, posto)))}.")
        if (indice, posto) in prova.commenti:
            righe.append(f"{il_gruppo.titolo}, punto {posto + 1}, il tuo commento: {prova.commenti[indice, posto]}")
    return righe


def _chi(punto):
    nomi = punto.candidato.nomi
    di_chi = "del tuo giocatore" if punto.parte == ASCOLTATORE else "dell'avversario"
    return f"{C.con_articolo(punto.candidato.momento.esito.colpo_decisivo)} di {nomi[punto.parte].testo}, {di_chi}"


def _scelta_svelata(punto, scelta):
    if scelta is None or scelta == NESSUNA:
        return detta(scelta)
    versione = punto.versione(scelta)
    doppia = ", una delle due lettere identiche" if versione.chiave == punto.ripetuta else ""
    return f"hai scelto la {scelta}, {versione.nome}{doppia}"


def righe_della_rivelazione(prova):
    """Quello che si scrive soltanto alla fine: che cosa era ogni versione e, per ogni punto ascoltato, quale lettera era quale."""
    righe = [f"Rivelazione, la versione {v.nome}: {v.descrizione}." for v in VERSIONI]
    for indice, il_gruppo in enumerate(prova.gruppi):
        if indice not in prova.svolti:
            continue
        if indice in prova.interrotti:
            righe.append(f"{il_gruppo.titolo}: i punti si sono chiusi prima della fine.")
        for posto, punto in enumerate(il_gruppo.punti):
            lettere = ", ".join(f"{lettera} {punto.versione(lettera).nome}" for lettera in LETTERE)
            doppie = punto.lettere_di(punto.ripetuta)
            controllo = f"le lettere {unisci(doppie)} erano identiche campione per campione, la versione {PER_CHIAVE[punto.ripetuta].nome} ripetuta"
            righe.append(f"Rivelazione, {il_gruppo.titolo}, punto {posto + 1}, {_chi(punto)}: {lettere}; {controllo}; "
                         f"{_scelta_svelata(punto, prova.scelte.get((indice, posto)))}.")
    return righe


def _volte(n):
    return conta(n, "volta", "volte")


def righe_del_riepilogo(prova):
    """
    Il riepilogo dei gruppi ascoltati e non chiusi senza giudizio: quante volte ogni versione, nei tiri
    tuoi e dell'avversario, quante volte nessuna e senza scelta, quante volte una delle due lettere
    identiche, e le lettere scelte.
    """
    righe = [f"Riepilogo, {prova.gruppi[i].titolo}: il gruppo è stato chiuso senza giudizio, e le sue scelte non contano." for i in sorted(prova.chiusi)]
    validi = [i for i in sorted(prova.svolti) if i not in prova.chiusi]
    voci = [(i, posto, punto) for i in validi for posto, punto in enumerate(prova.gruppi[i].punti)]
    if not voci:
        return [*righe, "Riepilogo: nessun punto da contare."]
    per_versione = {v.chiave: {"A": 0, "B": 0} for v in VERSIONI}
    nessuna = senza = doppie = 0
    per_lettera = dict.fromkeys(LETTERE, 0)
    for i, posto, punto in voci:
        scelta = prova.scelte.get((i, posto))
        if scelta is None:
            senza += 1
        elif scelta == NESSUNA:
            nessuna += 1
        else:
            versione = punto.versione(scelta)
            per_versione[versione.chiave][punto.parte] += 1
            per_lettera[scelta] += 1
            doppie += versione.chiave == punto.ripetuta
    for v in VERSIONI:
        conti = per_versione[v.chiave]
        righe.append(f"Riepilogo, {v.nome}: scelta {_volte(conti['A'] + conti['B'])} su {conta(len(voci), 'punto', 'punti')}, {conti['A']} nei tiri "
                     f"del tuo giocatore e {conti['B']} in quelli dell'avversario.")
    righe.append(f"Riepilogo, nessuna somiglia al tavolo vero: {_volte(nessuna)}; senza scelta: {_volte(senza)}.")
    righe.append(f"Riepilogo, i controlli: in ogni punto una versione stava sotto due lettere identiche, e hai scelto una delle due {_volte(doppie)}; "
                 f"scegliendo a caso succederebbe nel {round(200 / len(LETTERE))}% dei punti.")
    righe.append("Riepilogo, le lettere scelte: " + ", ".join(f"la {lettera} {_volte(n)}" for lettera, n in per_lettera.items()) + ".")
    return righe


# La sessione.

def esegui(prova, indice, risultati, annotazioni):
    """
    Un gruppo intero: la domanda, prima del via, perché NVDA la legga prima del primo suono, l'annuncio,
    i punti, il menu di fine gruppo e le scelte nel file. Se il menu si chiude con Escape, senza giudizio,
    le scelte si scrivono lo stesso ma il riepilogo non le conta.
    """
    il_gruppo = prova.gruppi[indice]
    print(f"Nel prossimo gruppo, per ogni punto, la domanda è: {DOMANDA}? Se nessuna ci somiglia, n.")
    if not gruppo(il_gruppo.titolo, len(il_gruppo.punti), "punti"):
        prova.saltati.add(indice)
        risultati.scrivi(f"{il_gruppo.titolo}: gruppo saltato.")
        return

    def giro():
        if ascolta(prova, indice):
            prova.interrotti.discard(indice)
        else:
            prova.interrotti.add(indice)

    prova.svolti.add(indice)
    giro()
    if annotazioni.esito(il_gruppo.titolo, riproduci=giro) == "chiuso":
        prova.chiusi.add(indice)
    risultati.scrivi(*righe_delle_scelte(prova, indice))
    annotazioni.scrivi_in_sospeso()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        seme = int(argv[0]) if argv else nuovo_seme()
    except ValueError:
        print(f"Il seme dev'essere un numero intero, e {argv[0]} non lo è. Uso: python strumenti/ascolto_schermo.py, con un numero per ripetere le "
              "lettere di una sessione passata.")
        return 1
    print("Preparo i punti, qualche secondo.")
    prova = prepara(seme)
    quanti = sum(len(g.punti) for g in prova.gruppi)
    print(f"Ascolto di confronto dello schermo centrale: {conta(len(prova.gruppi), 'gruppo', 'gruppi')}, {conta(quanti, 'punto', 'punti')}, sempre "
          "dalla tua testata del tavolo, come giocatore A.")
    print(f"Ogni punto finisce con la pallina contro lo schermo centrale, e lo senti in {len(LETTERE)} lettere, da A a {LETTERE[-1]}, dal fischio "
          "dell'arbitro che dà il via fino alla fine dei suoi suoni.")
    print(f"La domanda è sempre la stessa: {DOMANDA}. Puoi anche dire che nessuna ci somiglia.")
    print("Ogni punto comincia con la rassegna: tutte le lettere una volta, in ordine, ciascuna col suo nome; Escape la interrompe.")
    print("Poi la scelta: il tasto di una lettera la fa sentire, quante volte vuoi, e spazio ripete l'ultima sentita; s sceglie l'ultima sentita, "
          "n dice che nessuna ci somiglia, e dopo c lascia un commento al punto, Invio prosegue. Invio senza scegliere passa al punto seguente; "
          "Escape chiude i punti del gruppo. Mentre una lettera suona i tasti valgono subito.")
    print("A fine gruppo: r rifà il gruppo dal primo punto, c commenta, Invio lo dà per superato, Escape lo chiude senza giudizio, e allora le sue "
          "scelte non contano.")
    print(f"Le scelte vanno nel file {FILE_DEI_RISULTATI}, una riga per voce; che cosa c'era dietro le lettere lo trovi lì, ma soltanto alla fine.")
    # enter_escape e gruppo vanno a capo da sé: un print in più farebbe una riga vuota. Il silenzio
    # prima del primo suono sta nella prima lettera del gruppo, dopo il suo via.
    if not enter_escape("\rInvio per cominciare, Escape per uscire\r"):
        return 0
    risultati = Risultati(percorsi.nel_programma(FILE_DEI_RISULTATI))
    risultati.scrivi(f"Ascolto di confronto dello schermo centrale, {time.strftime('%Y-%m-%d %H:%M')}, seme {seme}.")
    annotazioni = Annotazioni(risultati.percorso)
    try:
        for indice in range(len(prova.gruppi)):
            esegui(prova, indice, risultati, annotazioni)
    finally:
        # Anche se la sessione si interrompe, le lettere ascoltate si svelano: senza, le scelte non direbbero niente.
        annotazioni.scrivi_in_sospeso()
        if prova.svolti:
            risultati.scrivi(*righe_della_rivelazione(prova), *righe_del_riepilogo(prova))
    if prova.svolti:
        for riga in righe_del_riepilogo(prova):
            print(riga)
    print(f"Fine dell'ascolto. Nel file {FILE_DEI_RISULTATI}, nella cartella del programma, trovi le tue scelte, quale lettera era quale e il "
          "riepilogo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
