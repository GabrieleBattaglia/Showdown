"""
MESS, l'ascolto della partita sonora con i timbri veri, l'ultimo ascolto della tappa 10.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-08 con la decisione D28, che mette gli ascolti in quest'ordine: prima un ascolto
libero di alcuni punti composti con suoni provvisori, per lati, movimento e tempi; poi i dosaggi
dello spazio alla cieca; i timbri per ultimi. Era l'ascolto libero, coi segnaposto del prototipo
strumenti/resa_prototipo.py; con la fase dei timbri compone con partita_sonora, cioè con i suoni veri
della partita dal vivo, e il prototipo resta al banco alla cieca dello spazio.
Il primo gruppo fa sentire ogni suono della partita da solo, uno per volta, nell'ordine di
partita_sonora.SUONI, sul modello di ascolta_suoni.py: per ognuno l'azione che lo fa suonare, il nome
del preset, la sua descrizione e da dove viene, poi Invio per sentirlo e spazio per ripeterlo. Ogni
suono viene da dove viene nella partita, con lo spazio del tavolo, perché i rapporti di livello fra
i timbri siano quelli veri: i colpi e i suoni della pallina dal centro della tua metà, a un metro da
chi ascolta; i fischi dall'arbitro, alla tua sinistra a metà tavolo, lontani e un po' incupiti; la
fanfara e il cicalino del fallo dalla tua testata, come quando l'esito è del tuo giocatore. Il
rotolamento si sente come una pallina che corre per un secondo e rallenta, il controllo come una
pallina scossa per quasi un secondo.
Poi i punti, che nascono qui, in memoria e sempre uguali: un mondo di giocatori nato con un seme
fisso, mai salvato, e una serie di incontri giocati dal motore in modalità completa, ciascuno col suo
seme. Fra tutti i punti giocati lo strumento ne sceglie otto, tipici e diversi fra loro, e li compone
al volo, senza file WAV: la diagonale da un lato all'altro, la stessa diagonale ascoltata dall'altro
giocatore, un tuo goal nella porta lontana, il goal di battuta dell'avversario, uno scambio lungo, un
out con la pallina che cade a terra, uno schermo centrale e un fallo che fa un rumore suo, la paletta
che cade, o se manca il colpo a vuoto o il doppio tocco. Ogni punto si sente dalla testata di chi
ascolta, di solito il giocatore A, dal fischio che dà il via alla battuta fino alla fine dei suoni
del punto, fanfara del goal e cicalino del fallo compresi; le parole dell'arbitro non hanno un suono
e si leggono prima, nella cronaca, dove una riga dice anche da che punto comincia il suono.
Il protocollo è quello degli ascolti di Gabriele. Prima di suonare lo strumento spiega come
funziona e aspetta il via, poi lascia qualche secondo di silenzio. I gruppi si annunciano e si
possono saltare. Per ogni voce scrive che cosa si sentirà e aspetta Invio prima di farla sentire;
poi spazio la ripete, quante volte si vuole, e Invio passa alla successiva; Escape chiude il gruppo.
Un tasto premuto mentre suona la ferma e vale subito: spazio la fa ripartire, Invio passa oltre,
Escape chiude il gruppo; gli altri tasti non la fermano. Ogni gruppo si chiude con il menu comune dei
collaudi, di collaudo_comune di GBUtils: r riascolta il gruppo, c lascia un commento, Invio lo dà per
superato, Escape lo chiude senza giudizio. Le impressioni vanno nel file ascolto_partita.txt, nella
cartella del programma, una riga per voce. Di suo lo strumento non scrive righe vuote, perché
enter_escape e gruppo vanno a capo da sé; le sole che restano vengono dal menu di collaudo_comune,
che qui non si tocca.
Tutto si sente al livello dell'ascolto libero approvato, cioè quello che il gioco dà al volume della partita 100, con margine:
nessun picco supera il tetto della partita, qualunque sia il volume scelto nel gioco, che qui non
conta.
Uso, dalla cartella del programma: python strumenti/ascolta_partita.py
"""

import datetime
import random
import sys
import time
from pathlib import Path
from typing import NamedTuple

import numpy as np

STRUMENTI = Path(__file__).resolve().parent
RADICE = STRUMENTI.parent
for cartella in (RADICE, STRUMENTI):
    if str(cartella) not in sys.path:
        sys.path.insert(0, str(cartella))

import resa_prototipo as resa  # noqa: E402
from collaudo_comune import gruppo  # noqa: E402
from GBUtils import Acusticator, enter_escape, key  # noqa: E402

import partita_sonora as ps  # noqa: E402
import percorsi  # noqa: E402
from ascolta_suoni import SILENZIO_INIZIALE, Annotazioni  # noqa: E402
from costanti import ASCOLTO_DIETRO_TESTATA  # noqa: E402
from motore import COMPLETO, Incontro, formato_singolare  # noqa: E402
from motore import cronaca as C  # noqa: E402
from motore.tavolo import CENTRO_X, centro_porta, posizione_arbitro, vista  # noqa: E402
from testi import conta  # noqa: E402

FILE_DEGLI_ESITI = "ascolto_partita.txt"
# Il mondo in memoria e gli incontri: semi fissi, così i punti sono sempre gli stessi.
SEME_MONDO = 23
GIOCATORI = 24
PRIMO_SEME = 1000
INCONTRI = 30
NASCITA = datetime.datetime(2026, 1, 1)  # noqa: DTZ001 - data segnaposto, come quelle del motore
# I decimi di silenzio in testa a ogni punto, perché il suono non parta insieme al tasto.
ANTICIPO = 0.3
# Mentre un punto suona si dà un'occhiata alla tastiera a questo passo, e si aspetta un poco oltre la fine.
SGUARDO = 0.05
CODA = 0.3
# Gli arrivi di un volo che resta in gioco fino a chi difende.
ARRIVI_IN_GIOCO = ("paletta", "corpo", "porta")
# I tasti che fermano un punto mentre suona.
TASTI_DEL_PUNTO = (" ", "\r", "\x1b")
# Il gruppo dei timbri, ogni suono della partita da solo, da dove viene nella partita e con lo
# spazio del tavolo, così i livelli fra loro sono quelli della partita: i colpi e i suoni della
# pallina dal centro della metà di chi ascolta, a DISTANZA_DEI_TIMBRI centimetri; i fischi
# dall'arbitro, alla sinistra di chi ascolta; la fanfara e il cicalino del fallo dalla sua testata.
# Il rotolamento come una pallina che corre e rallenta, dalla prima alla seconda velocità, in quei
# secondi, e il controllo come una pallina scossa per quei secondi.
TITOLO_DEI_TIMBRI = "Partita, i timbri uno per uno"
DISTANZA_DEI_TIMBRI = 100.0
DAL_CENTRO = (CENTRO_X, DISTANZA_DEI_TIMBRI - ASCOLTO_DIETRO_TESTATA)
DALL_ARBITRO = posizione_arbitro(True)
DALLA_TESTATA = centro_porta("A")
DA_DOVE = {
    DAL_CENTRO: "Viene dal centro della tua metà del tavolo, a un metro da te.",
    DALL_ARBITRO: "Viene dall'arbitro, alla tua sinistra a metà tavolo, come nella partita.",
    DALLA_TESTATA: "Viene dalla tua testata, come nella partita quando il goal o il fallo è del tuo giocatore.",
}
ROTOLAMENTO_DI_PROVA = (600.0, 150.0, 1.0)
CONTROLLO_DI_PROVA = 0.9
# L'orologio dell'attesa; le prove lo sostituiscono.
orologio = time.monotonic


class Candidato(NamedTuple):
    """Un punto giocato: il seme del suo incontro, i nomi della cronaca e il momento del motore."""
    seme: int
    nomi: dict
    momento: object


class Punto(NamedTuple):
    """
    Una voce dell'ascolto: la chiave, il titolo, chi ascolta, il punto giocato, le righe da leggere,
    il buffer da sentire e i ruoli dei suoni che ci sono dentro. Per un timbro del primo gruppo la
    chiave è il ruolo, il punto giocato manca e le righe sono la descrizione del preset.
    """
    chiave: str
    titolo: str
    ascoltatore: str
    candidato: Candidato
    righe: list
    buffer: np.ndarray
    ruoli: tuple


# I punti giocati.

def mondo_in_memoria(seme=SEME_MONDO, quanti=GIOCATORI):
    """Un mondo nuovo con quanti giocatori nati col seme, senza polisportive e mai salvato; il caso globale torna com'era."""
    from mondo import Mondo

    stato = random.getstate()
    random.seed(seme)
    try:
        mondo = Mondo()
        mondo.datetime_corrente_simulazione = NASCITA
        mondo.crea_giocatori_casuali(quanti, NASCITA, annuncia=False)
    finally:
        random.setstate(stato)
    return mondo


def punti_giocati(quanti=INCONTRI, primo_seme=PRIMO_SEME, seme_mondo=SEME_MONDO):
    """Tutti i punti di una serie di incontri al meglio dei 3, fra coppie diverse del mondo in memoria, nell'ordine in cui si giocano."""
    mondo = mondo_in_memoria(seme_mondo)
    ids = sorted(mondo.giocatori)
    rng = random.Random(f"coppie-{seme_mondo}")
    candidati = []
    for seme in range(primo_seme, primo_seme + quanti):
        a, b = rng.sample(ids, 2)
        g1, g2 = mondo.giocatori[a], mondo.giocatori[b]
        incontro = Incontro(g1, g2, formato_singolare(3), seme=seme, dettaglio=COMPLETO)
        nomi = C.nomi_dei_giocatori([g1, g2])
        candidati.extend(Candidato(seme, nomi, m) for m in incontro.momenti() if m.genere == "punto")
    return candidati


# Le misure con cui si scelgono i punti.

def durata_azione(candidato):
    """I secondi dell'azione, dal fischio del via alla fine del punto."""
    eventi = resa.azione(candidato.momento.eventi)
    return eventi[-1].t - eventi[0].t


def voli_della_pallina(candidato):
    """I voli dei colpi del punto, battuta compresa, con il colpo che li ha lanciati: coppie di evento del colpo e evento del volo."""
    eventi = resa.azione(candidato.momento.eventi)
    coppie = []
    lancio = None
    for e in eventi:
        if e.tipo in ("BATTUTA", "COLPO"):
            lancio = e
        elif e.tipo == "VOLO" and lancio is not None and e.chi == lancio.chi:
            coppie.append((lancio, e))
            lancio = None
    return coppie


def escursione(volo, ascoltatore="A"):
    """
    Di quanto si sposta il pan dalla partenza all'arrivo di un volo che attraversa il tavolo da un
    lato all'altro e arriva a chi difende, per chi ascolta; zero se resta da una parte o se finisce
    fuori, perché un out non è una diagonale.
    """
    if volo.volo[-1].tipo not in ARRIVI_IN_GIOCO:
        return 0.0
    inizio = vista((volo.volo[0].x, volo.volo[0].y), ascoltatore)[0]
    fine = vista((volo.volo[-1].x, volo.volo[-1].y), ascoltatore)[0]
    return abs(fine - inizio) if inizio * fine < 0 else 0.0


def diagonale_finale(candidato):
    """L'escursione del pan dell'ultimo colpo del punto, se è una diagonale; zero altrimenti."""
    coppie = voli_della_pallina(candidato)
    if not coppie:
        return 0.0
    colpo, volo = coppie[-1]
    if colpo.tipo != "COLPO" or not (colpo.colpo or "").startswith("diagonale"):
        return 0.0
    return escursione(volo)


def colpo_finale_di(candidato, parte):
    coppie = voli_della_pallina(candidato)
    return bool(coppie) and coppie[-1][0].parte == parte


def ha_tappa(candidato, tipo):
    return any(e.volo and any(tp.tipo == tipo for tp in e.volo) for e in candidato.momento.eventi)


def _esito(candidato):
    return candidato.momento.esito


# Le scelte: per ogni punto da ascoltare, i filtri dal più stretto al più largo, e l'ordine di
# preferenza fra i punti che passano; si prende il primo filtro che trova qualcosa.

class Scelta(NamedTuple):
    """Un punto da cercare: la chiave, il titolo, i filtri dal più stretto al più largo e, se serve, la preferenza fra quelli che passano."""
    chiave: str
    titolo: str
    filtri: tuple
    preferenza: object = None


SCELTE = (
    Scelta("rumore", "la paletta che cade", (
        lambda c: _esito(c).causa == "paletta_caduta" and _esito(c).attacchi <= 6,
        lambda c: _esito(c).causa == "paletta_caduta",
        lambda c: _esito(c).causa == "battuta_a_vuoto",
        lambda c: _esito(c).causa == "battuta_doppio_tocco",
    ), lambda c: _esito(c).attacchi),
    # La diagonale dell'avversario, che attraversa il tavolo e arriva a chi ascolta: dall'altra
    # testata la stessa diagonale se ne va. Fra quelle buone, quella che si sposta di più.
    Scelta("diagonale", "la diagonale da un lato all'altro", (
        lambda c: diagonale_finale(c) >= 1.2 and colpo_finale_di(c, "B") and _esito(c).attacchi <= 3,
        lambda c: diagonale_finale(c) >= 1.0 and _esito(c).attacchi <= 4,
        lambda c: _esito(c).attacchi <= 4 and any(escursione(v) >= 1.0 for _c, v in voli_della_pallina(c)),
    ), lambda c: -max((escursione(v) for _c, v in voli_della_pallina(c)), default=0.0)),
    Scelta("goal_di_battuta", "il goal di battuta del tuo avversario", (
        lambda c: _esito(c).causa == "goal_battuta" and _esito(c).a_chi == "B",
        lambda c: _esito(c).causa == "goal_battuta",
    )),
    Scelta("schermo_centrale", "uno schermo centrale", (
        lambda c: _esito(c).causa == "schermo_contro" and _esito(c).attacchi <= 4,
        lambda c: _esito(c).causa == "schermo_contro",
    ), lambda c: _esito(c).attacchi),
    Scelta("out_a_terra", "un out, con la pallina che cade a terra", (
        lambda c: _esito(c).causa == "out_sponda" and _esito(c).attacchi <= 4,
        lambda c: _esito(c).esito == "fallo" and ha_tappa(c, "terra"),
    ), lambda c: _esito(c).attacchi),
    Scelta("goal_tuo_lontano", "un tuo goal, nella porta lontana", (
        lambda c: _esito(c).causa == "goal_scambio" and _esito(c).a_chi == "A" and 2 <= _esito(c).attacchi <= 5 and "sponda" in (_esito(c).colpo_decisivo or ""),
        lambda c: _esito(c).causa == "goal_scambio" and _esito(c).a_chi == "A",
    ), lambda c: _esito(c).attacchi),
    Scelta("scambio_lungo", "uno scambio lungo", (
        lambda c: 8 <= _esito(c).attacchi <= 11 and durata_azione(c) <= 20.0,
        lambda c: _esito(c).attacchi >= 5 and durata_azione(c) <= 30.0,
    ), lambda c: -_esito(c).attacchi),
)
# I titoli del fallo rumoroso, secondo la causa trovata.
TITOLI_DEL_RUMORE = {"paletta_caduta": "la paletta che cade", "battuta_a_vuoto": "il colpo a vuoto in battuta", "battuta_doppio_tocco": "il doppio tocco in battuta"}
# I gruppi d'ascolto dei punti, che vengono dopo quello dei timbri: il titolo, e i punti come chiave
# della scelta e parte di chi ascolta.
GRUPPI = (
    ("Partita, i lati e il movimento", (("diagonale", "A"), ("diagonale", "B"), ("goal_tuo_lontano", "A"))),
    ("Partita, la battuta e lo scambio", (("goal_di_battuta", "A"), ("scambio_lungo", "A"))),
    ("Partita, i falli", (("out_a_terra", "A"), ("schermo_centrale", "A"), ("rumore", "A"))),
)
TITOLO_DALL_ALTRA_PARTE = "la stessa diagonale, ascoltata dall'altra testata del tavolo"
# La riga della cronaca che dice dove comincia il suono: dal fischio del via, o dalla battuta se
# chi batte non l'ha aspettato.
INIZIO_COL_FISCHIO = "Qui comincia il suono: il fischio dell'arbitro dà il via."
INIZIO_CON_LA_BATTUTA = "Qui comincia il suono, con la battuta."


def scegli(candidati):
    """I punti scelti, come dizionario dalla chiave della scelta al candidato; un punto serve una scelta sola, e una scelta che non trova niente manca."""
    scelti = {}
    usati = set()
    for scelta in SCELTE:
        for filtro in scelta.filtri:
            buoni = [c for c in candidati if id(c.momento) not in usati and filtro(c)]
            if buoni:
                scelto = min(buoni, key=scelta.preferenza) if scelta.preferenza else buoni[0]
                scelti[scelta.chiave] = scelto
                usati.add(id(scelto.momento))
                break
    return scelti


# Le parole e il suono di un punto.

def presentazione(candidato, ascoltatore):
    """Chi sei, dove stanno l'avversario e l'arbitro, e la cronaca normale del punto fino alla sua fine."""
    nomi = candidato.nomi
    altro = "B" if ascoltatore == "A" else "A"
    avversario = nomi[altro]
    il_tuo = "il tuo avversario" if avversario.sesso == "m" else "la tua avversaria"
    fischio = next(e for e in candidato.momento.eventi if e.tipo == "FISCHIO")
    lato = "sinistra" if vista(fischio.pos, ascoltatore)[0] < 0 else "destra"
    righe = [f"Sei {nomi[ascoltatore].testo}, alla tua testata del tavolo; di fronte a te, oltre lo schermo, c'è {avversario.testo}, {il_tuo}; "
             f"l'arbitro sta alla tua {lato}."]
    eventi = list(candidato.momento.eventi)
    primo = resa.azione(eventi)[0]
    fine = next(i for i, e in enumerate(eventi) if e.tipo in resa.FINE_AZIONE)
    for e in eventi[:fine + 1]:
        # Le parole che vengono prima si leggono soltanto: una riga dice dove comincia il suono.
        if e is primo:
            righe.append(INIZIO_COL_FISCHIO if e.tipo == "FISCHIO" else INIZIO_CON_LA_BATTUTA)
        testo = C.frase(e, nomi, C.NORMALE)
        if testo:
            righe.append(testo)
    return righe


def componi_punto(candidato, ascoltatore):
    """
    Il buffer da sentire, cioè l'azione del punto composta con partita_sonora per chi ascolta, al
    volume della partita predefinito e con l'anticipo di silenzio in testa; e i ruoli dei suoni che
    ci sono dentro, senza doppioni.
    """
    composto = ps.componi(resa.azione(candidato.momento.eventi), ascoltatore)
    ruoli = tuple(dict.fromkeys(p.ruolo for p in composto.posati))
    return _con_l_anticipo(ps.per_la_cassa(composto.buffer, ps.VOLUME_DI_PROGETTO)), ruoli


def _con_l_anticipo(buffer):
    silenzio = np.zeros((round(ANTICIPO * ps.FS), 2), dtype=np.float32)
    return np.concatenate([silenzio, np.asarray(buffer, dtype=np.float32)])


def sorgente_di_prova(ruolo):
    """
    La sorgente mono di un ruolo come la sente il gruppo dei timbri: il preset; per il rotolamento
    il sonaglio di una pallina che corre e rallenta, col guadagno che la partita gli dà alle sue
    velocità; per il controllo la pallina scossa, col suo guadagno.
    """
    if ruolo == "rotolamento":
        inizio, fine, secondi = ROTOLAMENTO_DI_PROVA
        tempi = np.arange(0.0, secondi + ps.PASSO, ps.PASSO)
        velocita = np.linspace(inizio, fine, len(tempi))
        mono = ps.sonaglio(ruolo, tempi, velocita, 1)
        guadagni = ps.GUADAGNO_ROTOLAMENTO * np.clip(np.sqrt(velocita / ps.V_RIF), 0.15, 1.3)
        return (mono * np.interp(np.arange(len(mono)) / ps.FS, tempi, guadagni)).astype(np.float32)
    if ruolo == "controllo":
        return ps.in_fila(ruolo, CONTROLLO_DI_PROVA, 0) * np.float32(ps.GUADAGNO_CONTROLLO)
    return ps.sorgente(ruolo)


def posizione_di_prova(ruolo):
    """Da dove viene un ruolo nel gruppo dei timbri: i fischi dall'arbitro, gli esiti dalla testata di chi ascolta, il resto dal centro a un metro."""
    if ruolo.startswith("fischio_"):
        return DALL_ARBITRO
    if ruolo in ps.ESITI:
        return DALLA_TESTATA
    return DAL_CENTRO


def timbri():
    """
    Il gruppo dei timbri: ogni suono della partita da solo, nell'ordine di partita_sonora.SUONI, con
    l'azione, il preset, la sua descrizione e da dove viene, messo nello spazio del tavolo dalla
    posizione che ha nella partita, per chi ascolta da A.
    """
    voci = []
    for ruolo, preset in ps.SUONI.items():
        posizione = posizione_di_prova(ruolo)
        stereo = ps.spazializza(ps.Posato(ruolo, 0.0, sorgente_di_prova(ruolo), np.array([0.0]), [posizione]), "A")
        azione = ps.AZIONI[ruolo]
        titolo = f"{azione[0].upper()}{azione[1:]}, preset {preset}"
        righe = [Acusticator.descrizione(preset) or "Senza descrizione.", DA_DOVE[posizione]]
        buffer = ps.per_la_cassa(stereo, ps.VOLUME_DI_PROGETTO)
        voci.append(Punto(ruolo, titolo, "A", None, righe, _con_l_anticipo(buffer), (ruolo,)))
    return voci


def prepara(candidati=None):
    """
    I gruppi d'ascolto: prima quello dei timbri, poi i gruppi dei punti composti; coppie di titolo e
    lista di Punto. Una scelta che non ha trovato niente si salta.
    """
    if candidati is None:
        candidati = punti_giocati()
    scelti = scegli(candidati)
    gruppi = [(TITOLO_DEI_TIMBRI, timbri())]
    for titolo, voci in GRUPPI:
        punti = []
        for chiave, ascoltatore in voci:
            candidato = scelti.get(chiave)
            if candidato is None:
                continue
            titolo_punto = next(s.titolo for s in SCELTE if s.chiave == chiave)
            if chiave == "rumore":
                titolo_punto = TITOLI_DEL_RUMORE[_esito(candidato).causa]
            if ascoltatore != "A":
                titolo_punto = TITOLO_DALL_ALTRA_PARTE
            punti.append(Punto(chiave, titolo_punto, ascoltatore, candidato, presentazione(candidato, ascoltatore), *componi_punto(candidato, ascoltatore)))
        if punti:
            gruppi.append((titolo, punti))
    return gruppi


# L'ascolto.

def suona(buffer):
    """
    Fa sentire un punto e aspetta che finisca, senza scrivere niente, così la voce di NVDA non lo
    copre. Spazio, Invio o Escape premuti mentre suona lo fermano, e la funzione restituisce quel
    tasto; None se il punto è finito da sé.
    """
    if not Acusticator.riproduci(buffer, ps.FS):
        print("Il punto non si sente: la scheda audio non risponde.")
        return None
    scadenza = orologio() + len(buffer) / ps.FS + CODA
    while (resto := scadenza - orologio()) > 0:
        tasto = key(attesa=min(resto, SGUARDO), alla_scadenza=None)
        if tasto in TASTI_DEL_PUNTO:
            Acusticator.stop()
            return tasto
    return None


def ascolta(punti):
    """
    Fa sentire le voci di un gruppo una dopo l'altra. Di ognuna scrive il titolo e le righe, cioè
    chi sei e la cronaca per un punto, la descrizione del preset per un timbro, e aspetta Invio
    prima di suonarla; poi spazio la ripete e Invio passa oltre. Escape, in qualunque momento,
    chiude il gruppo.
    """
    for numero, punto in enumerate(punti, 1):
        print(f"{numero} di {len(punti)}: {punto.titolo}.")
        for riga in punto.righe:
            print(riga)
        tasto = key("\rInvio per sentirlo, Escape chiude il gruppo.\r")
        print()
        if tasto == "\x1b":
            return
        while True:
            tasto = suona(punto.buffer)
            if tasto is None:
                tasto = key("\rSpazio ripete, Invio prosegue, Escape chiude il gruppo.\r")
                print()
            if tasto == "\x1b":
                return
            if tasto != " ":
                break


def main():
    gruppi = prepara()
    quanti_timbri = sum(len(voci) for titolo, voci in gruppi if titolo == TITOLO_DEI_TIMBRI)
    quanti_punti = sum(len(voci) for titolo, voci in gruppi if titolo != TITOLO_DEI_TIMBRI)
    print(f"Ascolto della partita di MESS con i timbri veri: {conta(len(gruppi), 'gruppo', 'gruppi')}, "
          f"{conta(quanti_timbri, 'suono', 'suoni')} uno per uno e {conta(quanti_punti, 'punto', 'punti')} composti.")
    print(f"Il primo gruppo, {TITOLO_DEI_TIMBRI}, fa sentire ogni suono della partita da solo, con l'azione, il preset e la sua "
          "descrizione, da dove viene nella partita, perché i livelli fra loro siano quelli veri: i colpi dal centro della tua metà del tavolo, "
          "i fischi dall'arbitro, alla tua sinistra, la fanfara e il cicalino dalla tua testata. "
          "Gli altri gruppi fanno sentire punti interi, con lo spazio del tavolo, dalla testata di chi ascolta.")
    print("Ogni gruppo si annuncia e si può saltare. Per ogni voce leggi che cosa sentirai; Invio la fa sentire, spazio la ripete, "
          "Invio passa alla successiva, Escape chiude il gruppo.")
    print("Mentre suona, spazio la fa ripartire, Invio passa oltre ed Escape chiude il gruppo.")
    print("A fine gruppo: r riascolta, c commenta, Invio lo dà per superato, Escape lo chiude senza giudizio.")
    print(f"Le impressioni vanno nel file {FILE_DEGLI_ESITI}, una riga per voce.")
    # enter_escape e gruppo vanno a capo da sé: un print in più farebbe una riga vuota.
    if not enter_escape("\rInvio per cominciare, Escape per uscire\r"):
        return 0
    time.sleep(SILENZIO_INIZIALE)
    esiti = Annotazioni(percorsi.percorso(FILE_DEGLI_ESITI))
    for titolo, punti in gruppi:
        if not gruppo(titolo, len(punti), "suoni" if titolo == TITOLO_DEI_TIMBRI else "punti"):
            continue
        ascolta(punti)
        esiti.esito(titolo, riproduci=lambda p=punti: ascolta(p))
    print("Fine dell'ascolto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
