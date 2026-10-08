"""
MESS, il banco dello spazio della partita sonora: i dosaggi alla cieca della tappa 10.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-08 con la decisione D28, che dopo l'ascolto libero, superato senza note, mette i
dosaggi dello spazio alla cieca, con le coppie di controllo: quanto il lontano è più piano, quanto è
più cupo e se lo diventa con la distanza o solo dietro lo schermo, quanto è larga la metà lontana
del tavolo. Le misure del critico, all'inizio della tappa, dicono che sulla scala del tavolo l'aria
non giustifica la cupezza e lo schermo sì, perché nasconde la pallina da poco oltre la metà in poi,
e che dal punto d'ascolto l'angolo lontano sta a 8,5 gradi dal centro, mentre oggi la metà lontana
suona larga quanto quella vicina.
I gruppi sono uno per dimensione, ciascuno con quattro candidati, compreso quello di oggi, mentre le
altre due dimensioni restano ferme a oggi. Il volume: il lontano 4, 8,5, 13 o 17 decibel sotto il
vicino, cioè la legge del motore con i decibel dimezzati, com'è, moltiplicati per 1,5 o raddoppiati,
che è quasi la legge dell'aria aperta. La cupezza: nessuna; quella di oggi, che scende con la
distanza fino a 2660 hertz in fondo; quella dell'ombra dello schermo, aperta finché la pallina si
vede e poi giù, lieve fino a 6000 hertz o forte fino agli stessi 2660 di oggi: così l'ombra forte e
la distanza differiscono solo nella forma, e l'ombra lieve e quella forte solo nella quantità. La
larghezza: la metà lontana larga quanto quella vicina, come oggi; stretta dallo schermo in poi fino
al 65 o al 30 per cento in fondo, dove il 30 è quasi l'angolo vero; oppure tutto il tavolo
dall'angolo vero, con le casse a 30 gradi, che cambia anche la metà vicina. Poi, se i voti scelgono
qualcosa di diverso da oggi, un gruppo finale mette a confronto lo spazio di oggi con quello delle
scelte messe insieme, per sentire se le tre leggi stanno bene insieme.
I punti sono quelli dell'ascolto libero, scelti da strumenti/ascolta_partita.py, che Gabriele ha già
sentito: per ogni dimensione due o tre che la mettono in evidenza, composti in memoria per il
giocatore A con strumenti/resa_prototipo.py, in fila con una pausa fra l'uno e l'altro, senza file
WAV. Il materiale di una lettera è tutta la fila. I candidati di un gruppo hanno lo stesso livello:
se un picco supera il tetto della resa si abbassano tutti dello stesso fattore, così i rapporti fra
loro restano quelli delle leggi.
Il protocollo è quello delle prove alla cieca di Gabriele, che va trattato come uno strumento di
misura. Prima della prova lo strumento dice soltanto come si esegue, cosa premere e che domanda ci
sarà, mai i numeri, mai quale candidato sia quello di oggi, mai che c'è un controllo; aspetta il via
e lascia qualche secondo di silenzio prima del primo suono. In ogni gruppo un candidato, scelto a
caso, è ripetuto identico sotto due lettere e presentato come gli altri: è il controllo. Le lettere
si mescolano con un seme, che si registra; ogni gruppo comincia con la rassegna, tutte le lettere
una volta, in ordine, senza domande, e poi il voto da 1 a 5 lettera per lettera, sentendo ogni
lettera tutte le volte che si vuole, e con la possibilità di non avere preferenze. In fondo al
gruppo c'è il menu comune dei collaudi, di collaudo_comune di GBUtils: r rifà la rassegna e il voto,
c commenta, Invio dà il gruppo per superato, Escape lo chiude senza giudizio.
I risultati vanno nel file banco_spazio.txt, nella cartella del programma, una riga per voce: in
testa la data e il seme, poi i voti e i commenti di ogni gruppo, con le sole lettere; alla fine
della sessione, e soltanto allora, quale lettera era quale, il riepilogo che somma i voti per
candidato, il conto del controllo e la scelta di ogni gruppo. Di suo lo strumento non scrive righe
vuote, perché enter_escape e gruppo vanno a capo da sé; le sole che restano vengono dal menu di
collaudo_comune, che qui non si tocca.
Uso, dalla cartella del programma: python strumenti/banco_spazio.py. Con un numero, per esempio
python strumenti/banco_spazio.py 4127, usa quel seme, e quindi le stesse lettere di una sessione
passata.
"""

import math
import random
import sys
import time
from dataclasses import replace
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
from collaudo_comune import gruppo  # noqa: E402
from GBUtils import Acusticator, enter_escape, key  # noqa: E402

import ascolta_suoni  # noqa: E402
import percorsi  # noqa: E402
from costanti import LARGHEZZA_TAVOLO  # noqa: E402
from testi import conta, intero, numero, unisci  # noqa: E402

FILE_DEI_RISULTATI = "banco_spazio.txt"
LETTERE = "ABCDEFGH"
VOTI = frozenset("12345")
# Il silenzio prima di ogni lettera: nella rassegna c'è il tempo di sentire il suo nome da NVDA,
# nel voto il suono parte quasi subito, perché il tasto l'ha chiesto. Fra un punto e l'altro della
# stessa lettera, una pausa.
ANTICIPO_RASSEGNA = 2.0
ANTICIPO_VOTO = ap.ANTICIPO
PAUSA_FRA_I_PUNTI = 1.2
# Mentre una lettera suona si dà un'occhiata alla tastiera a questo passo, e si aspetta un poco oltre la fine.
SGUARDO = ap.SGUARDO
CODA = ap.CODA
# Nella rassegna soltanto Escape ferma il suono, e la interrompe.
TASTI_DELLA_RASSEGNA = frozenset("\x1b")
# L'orologio dell'attesa; le prove lo sostituiscono.
orologio = time.monotonic


class Candidato(NamedTuple):
    """Un dosaggio dello spazio: il nome, che si rivela solo alla fine, e le leggi della resa."""
    nome: str
    spazio: resa.Spazio


class Dimensione(NamedTuple):
    """
    Un gruppo del banco: la chiave, il titolo, la domanda, i punti come chiavi delle scelte
    dell'ascolto libero, i campi di Spazio che il gruppo fa cambiare e i candidati.
    """
    chiave: str
    titolo: str
    domanda: str
    punti: tuple
    campi: tuple
    candidati: tuple


class Materiale(NamedTuple):
    """Il materiale di una lettera: il buffer dei punti in fila, il campione d'inizio di ogni punto e la sua resa, che le prove misurano."""
    buffer: np.ndarray
    inizi: tuple
    rese: tuple


# I candidati.

def decibel_del_lontano(spazio):
    """Di quanti decibel il centro della porta lontana suona sopra il vicino, per la legge di volume dello spazio: un numero negativo."""
    lontano = resa.legge_del_volume(resa.D_FONDO, spazio)
    vicino = resa.legge_del_volume(resa.D_RIF_VOLUME, spazio)
    return 20.0 * math.log10(lontano / vicino)


def _volume(esponente, nota=""):
    spazio = resa.Spazio(volume=esponente)
    return Candidato(f"il lontano {numero(-decibel_del_lontano(spazio))} decibel sotto il vicino{nota}", spazio)


def _ombra(fc, quanto, nota=""):
    nome = (f"cupo solo all'ombra dello schermo, {quanto}: il taglio comincia a scendere a {intero(resa.Y_OMBRA)} centimetri "
            f"dalla tua porta e arriva a {intero(fc)} hertz a {intero(resa.Y_OMBRA_PIENA)}{nota}")
    return Candidato(nome, resa.Spazio(cupezza="ombra", fc_ombra=fc))


def _stretta(lontano):
    return Candidato(f"la metà lontana che si stringe dallo schermo in poi, fino al {intero(lontano * 100)} per cento in fondo", resa.Spazio(lontano=lontano))


ANGOLO_LONTANO = math.degrees(math.atan2(LARGHEZZA_TAVOLO / 2, resa.D_FONDO))
FC_OMBRA_LIEVE = 6000.0

VOLUME = (
    _volume(0.5),
    _volume(1.0, ", la legge di oggi"),
    _volume(1.5),
    _volume(2.0, ", quasi come all'aria aperta"),
)
CUPEZZA = (
    Candidato("nessuna cupezza: il lontano chiaro quanto il vicino", resa.Spazio(cupezza="nessuna")),
    Candidato(f"cupo con la distanza, la legge di oggi: il taglio scende da {intero(resa.D0)} centimetri in poi, fino a {intero(resa.FC_FONDO)} hertz in fondo",
              resa.Spazio()),
    _ombra(FC_OMBRA_LIEVE, "lieve"),
    _ombra(resa.FC_FONDO, "forte", ", quanto in fondo oggi"),
)
LARGHEZZA = (
    Candidato("la metà lontana larga quanto quella vicina, la legge di oggi", resa.Spazio()),
    _stretta(0.65),
    _stretta(0.3),
    Candidato(f"tutto il tavolo dall'angolo vero, con le casse a {intero(resa.ANGOLO_CASSE)} gradi: l'angolo lontano a {numero(ANGOLO_LONTANO)} gradi dal centro",
              resa.Spazio(pan="angolo")),
)
DIMENSIONI = (
    Dimensione("volume", "Spazio, il volume del lontano",
               "quanto ti sembra giusto il volume dei suoni lontani, rispetto a quelli vicini a te",
               ("goal_di_battuta", "goal_tuo_lontano"), ("volume",), VOLUME),
    Dimensione("cupezza", "Spazio, il colore del lontano",
               "quanto ti sembra giusto il colore, chiaro o scuro, dei suoni a metà tavolo e di quelli lontani, rispetto a quelli vicini a te",
               ("goal_di_battuta", "schermo_centrale", "goal_tuo_lontano"), ("cupezza", "d0", "fc_ombra"), CUPEZZA),
    Dimensione("larghezza", "Spazio, la larghezza della metà lontana",
               "quanto ti sembra giusta la posizione a destra e a sinistra dei suoni, soprattutto nella metà lontana del tavolo",
               ("diagonale", "goal_tuo_lontano"), ("pan", "lontano"), LARGHEZZA),
)
# Il gruppo finale: i candidati li danno i voti dei primi tre.
INSIEME = Dimensione("insieme", "Spazio, tutto insieme",
                     "quanto ti sembra giusto lo spazio del tavolo nel suo insieme: il volume, il colore e la posizione dei suoni",
                     ("goal_di_battuta", "diagonale", "goal_tuo_lontano"), ("volume", "cupezza", "d0", "fc_ombra", "pan", "lontano"), ())
# Come si annunciano i punti, nelle parole di chi ascolta.
TITOLI_DEI_PUNTI = {
    "goal_di_battuta": "il goal di battuta del tuo avversario",
    "goal_tuo_lontano": "un tuo goal nella porta lontana",
    "schermo_centrale": "uno schermo centrale",
    "diagonale": "una diagonale da un lato all'altro del tavolo",
}


def indice_di_oggi(dimensione):
    """La posizione fra i candidati di quello che non cambia niente rispetto a oggi."""
    return next(i for i, c in enumerate(dimensione.candidati) if not c.spazio.diverso_in(resa.OGGI))


# I punti e i materiali.

def punti_del_banco(candidati=None):
    """I punti dell'ascolto libero che servono ai gruppi, come dizionario dalla chiave della scelta al punto giocato."""
    scelti = ap.scegli(ap.punti_giocati() if candidati is None else candidati)
    chiavi = sorted({chiave for d in (*DIMENSIONI, INSIEME) for chiave in d.punti})
    mancano = [chiave for chiave in chiavi if chiave not in scelti]
    if mancano:
        raise LookupError(f"Fra i punti giocati non si trovano: {', '.join(mancano)}.")
    return {chiave: scelti[chiave] for chiave in chiavi}


def componi_materiale(punti, spazio):
    """I punti in fila per chi ascolta da A, con le leggi dello spazio e una pausa fra l'uno e l'altro: il materiale di una lettera."""
    pausa = np.zeros((round(PAUSA_FRA_I_PUNTI * resa.FS), 2), dtype=np.float32)
    pezzi = []
    inizi = []
    rese = []
    posizione = 0
    for punto in punti:
        if pezzi:
            pezzi.append(pausa)
            posizione += len(pausa)
        composto = resa.componi(resa.azione(punto.momento.eventi), "A", spazio)
        inizi.append(posizione)
        rese.append(composto)
        pezzi.append(composto.buffer)
        posizione += len(composto.buffer)
    return Materiale(np.concatenate(pezzi), tuple(inizi), tuple(rese))


def componi_dimensione(dimensione, punti):
    """I materiali di tutti i candidati di un gruppo, nell'ordine dei candidati, livellati insieme sotto il tetto della resa."""
    materiali = [componi_materiale([punti[chiave] for chiave in dimensione.punti], c.spazio) for c in dimensione.candidati]
    livellati = resa.con_margine_comune([m.buffer for m in materiali])
    return [m._replace(buffer=b) for m, b in zip(materiali, livellati, strict=True)]


def assegna(rng, quanti):
    """
    Le lettere di un gruppo: per ogni lettera, nell'ordine, l'indice del suo candidato, con un
    candidato scelto a caso ripetuto sotto due lettere, il controllo, e tutto mescolato.
    Restituisce l'ordine e l'indice del candidato ripetuto.
    """
    ripetuto = rng.randrange(quanti)
    ordine = [*range(quanti), ripetuto]
    rng.shuffle(ordine)
    return tuple(ordine), ripetuto


class Prova:
    """Un gruppo da ascoltare: la dimensione, i materiali dei candidati, le lettere con il controllo, e i voti che si raccolgono."""

    def __init__(self, dimensione, materiali, ordine, ripetuto):
        self.dimensione = dimensione
        self.materiali = materiali
        self.ordine = ordine
        self.ripetuto = ripetuto
        self.lettere = LETTERE[:len(ordine)]
        self.voti = {}
        self.nessuna_preferenza = False
        self.saltata = False
        self.svolta = False

    def indice(self, lettera):
        return self.ordine[self.lettere.index(lettera)]

    def candidato(self, lettera):
        return self.dimensione.candidati[self.indice(lettera)]

    def lettere_di(self, indice):
        """Le lettere sotto cui sta un candidato: due per quello ripetuto, una per gli altri."""
        return [lettera for lettera in self.lettere if self.indice(lettera) == indice]

    def da_sentire(self, lettera, anticipo):
        """Il materiale della lettera con il silenzio dell'anticipo in testa."""
        silenzio = np.zeros((round(anticipo * resa.FS), 2), dtype=np.float32)
        return np.concatenate([silenzio, self.materiali[self.indice(lettera)].buffer])


def prepara(seme, punti=None, materiali=None):
    """
    Le prove dei tre gruppi, con le lettere mescolate dal seme. materiali, se c'è, dà quelli già
    composti di ogni gruppo, per chiave: le prove lo usano per non ricomporli.
    """
    if punti is None:
        punti = punti_del_banco()
    rng = random.Random(seme)
    prove = []
    for dimensione in DIMENSIONI:
        composti = componi_dimensione(dimensione, punti) if materiali is None else materiali[dimensione.chiave]
        prove.append(Prova(dimensione, composti, *assegna(rng, len(dimensione.candidati))))
    return prove


# Le scelte e il gruppo finale.

def medie(prova):
    """La media dei voti di ogni candidato che ne ha, per indice."""
    risultato = {}
    for indice in range(len(prova.dimensione.candidati)):
        voti = [prova.voti[lettera] for lettera in prova.lettere_di(indice) if lettera in prova.voti]
        if voti:
            risultato[indice] = sum(voti) / len(voti)
    return risultato


def scelta(prova):
    """
    L'indice del candidato preferito: quello con la media più alta; a parità quello di oggi, se è
    fra i pari, o il primo. Senza voti, o senza preferenze, resta quello di oggi.
    """
    oggi = indice_di_oggi(prova.dimensione)
    valori = medie(prova)
    if prova.nessuna_preferenza or not valori:
        return oggi
    migliore = max(valori.values())
    pari = [indice for indice, media in valori.items() if media == migliore]
    return oggi if oggi in pari else min(pari)


def spazio_delle_scelte(prove):
    """Lo spazio che mette insieme le scelte dei gruppi: ogni gruppo dà i suoi campi, gli altri restano quelli di oggi."""
    campi = {}
    for prova in prove:
        spazio = prova.dimensione.candidati[scelta(prova)].spazio
        for campo in prova.dimensione.campi:
            campi[campo] = getattr(spazio, campo)
    return replace(resa.OGGI, **campi)


def prepara_finale(prove, seme, punti):
    """Il gruppo finale, lo spazio di oggi contro quello delle scelte, con il suo controllo; None se le scelte sono proprio lo spazio di oggi."""
    scelte = spazio_delle_scelte(prove)
    if scelte == resa.OGGI:
        return None
    nomi = "; ".join(p.dimensione.candidati[scelta(p)].nome for p in prove)
    candidati = (Candidato("lo spazio di oggi, quello dell'ascolto libero", resa.OGGI), Candidato(f"le scelte dei tre gruppi: {nomi}", scelte))
    dimensione = INSIEME._replace(candidati=candidati)
    return Prova(dimensione, componi_dimensione(dimensione, punti), *assegna(random.Random(f"{seme}-finale"), len(candidati)))


# L'ascolto.

def suona(buffer, tasti):
    """
    Fa sentire un buffer e aspetta che finisca, senza scrivere niente, così la voce di NVDA non lo
    copre. Un tasto fra quelli indicati, premuto mentre suona, lo ferma, e la funzione lo
    restituisce; None se il suono è finito da sé.
    """
    if not Acusticator.riproduci(buffer, resa.FS):
        print("Il suono non parte: la scheda audio non risponde.")
        return None
    scadenza = orologio() + len(buffer) / resa.FS + CODA
    while (resto := scadenza - orologio()) > 0:
        tasto = key(attesa=min(resto, SGUARDO), alla_scadenza=None)
        if tasto in tasti:
            Acusticator.stop()
            return tasto
    return None


def rassegna(prova):
    """Tutte le lettere una volta, in ordine, ciascuna annunciata prima di suonare, senza domande. Escape la interrompe."""
    print("Rassegna.")
    for lettera in prova.lettere:
        print(f"Lettera {lettera}.")
        if suona(prova.da_sentire(lettera, ANTICIPO_RASSEGNA), TASTI_DELLA_RASSEGNA) == "\x1b":
            print("Rassegna interrotta.")
            return


def tasti_del_voto(prova):
    """I tasti del voto, che valgono anche mentre una lettera suona: spazio, Invio, Escape, n, i voti e le lettere del gruppo."""
    return frozenset({" ", "\r", "\x1b", "n", "N", *VOTI, *prova.lettere, *prova.lettere.lower()})


def invito(lettera, voto):
    """Il prompt del voto di una lettera, entro quaranta caratteri, col voto già dato se c'è."""
    if voto is None:
        return f"\r{lettera}: spazio ascolta, da 1 a 5 il voto\r"
    return f"\r{lettera}, voto {voto}: spazio ascolta, 1-5 cambia\r"


def riassunto(prova):
    """I voti del gruppo in una riga, o la mancanza di preferenze."""
    if prova.nessuna_preferenza:
        return "Nessuna preferenza."
    return "I voti: " + ", ".join(f"{lettera} {prova.voti[lettera]}" if lettera in prova.voti else f"{lettera} senza voto" for lettera in prova.lettere) + "."


def voto(prova):
    """
    Il voto, una lettera alla volta, dalla prima. Spazio fa sentire la lettera, quante volte si
    vuole; il tasto di un'altra lettera fa sentire quella, per confronto; da 1 a 5 si vota e si
    passa alla seguente; Invio passa oltre senza cambiare il voto; n dichiara nessuna preferenza
    per tutto il gruppo e cancella i voti; Escape chiude il voto. Un tasto premuto mentre una
    lettera suona la ferma e vale subito.
    """
    print(f"Il voto, da A a {prova.lettere[-1]}: {prova.dimensione.domanda}.")
    tasti = tasti_del_voto(prova)
    i = 0
    tasto = None
    while i < len(prova.lettere):
        lettera = prova.lettere[i]
        if tasto is None:
            tasto = key(invito(lettera, prova.voti.get(lettera)))
            print()
        scelto, tasto = tasto, None
        if scelto not in tasti:
            continue
        if scelto == " ":
            tasto = suona(prova.da_sentire(lettera, ANTICIPO_VOTO), tasti)
        elif scelto == "\r":
            i += 1
        elif scelto == "\x1b":
            break
        elif scelto in ("n", "N"):
            prova.voti.clear()
            prova.nessuna_preferenza = True
            break
        elif scelto in VOTI:
            prova.voti[lettera] = int(scelto)
            prova.nessuna_preferenza = False
            i += 1
        else:
            tasto = suona(prova.da_sentire(scelto.upper(), ANTICIPO_VOTO), tasti)
    print(riassunto(prova))


def giro(prova):
    """Un giro del gruppo: la rassegna e poi il voto."""
    rassegna(prova)
    voto(prova)


# I risultati.

class Risultati:
    """Il file dei risultati, nella cartella del programma: una riga per voce, aggiunta in fondo."""

    def __init__(self, percorso):
        self.percorso = percorso

    def scrivi(self, *righe):
        if righe:
            with open(self.percorso, "a", encoding="utf-8") as f:
                f.writelines(riga + "\n" for riga in righe)


class Annotazioni(ascolta_suoni.Annotazioni):
    """
    Il menu di fine gruppo di collaudo_comune, con gli esiti scritti una riga per voce come
    nell'ascolto dei suoni, ma trattenuti finché il gruppo non si chiude: nel file vengono dopo i
    voti del gruppo, a cui si riferiscono.
    """

    def __init__(self, percorso):
        super().__init__(percorso)
        self.in_sospeso = []

    def registra(self, titolo, commento, misura=""):
        self.in_sospeso.append((titolo, commento, misura))

    def scrivi_in_sospeso(self):
        for voce in self.in_sospeso:
            super().registra(*voce)
        self.in_sospeso.clear()


def righe_dei_voti(prova):
    """I voti di un gruppo chiuso, con le sole lettere: una riga per lettera, o una per la mancanza di preferenze."""
    titolo = prova.dimensione.titolo
    if prova.nessuna_preferenza:
        return [f"{titolo}: nessuna preferenza."]
    return [f"{titolo}, lettera {lettera}: {prova.voti.get(lettera, 'senza voto')}." for lettera in prova.lettere]


def _lettere(lettere):
    return f"{'lettera' if len(lettere) == 1 else 'lettere'} {unisci(lettere)}"


def righe_della_rivelazione(prove):
    """
    Quello che si scrive soltanto alla fine, per ogni gruppo ascoltato: quale lettera era quale, il
    riepilogo che somma i voti per candidato, dal più votato, il conto del controllo e la scelta.
    """
    righe = []
    for prova in prove:
        if not prova.svolta:
            continue
        dimensione = prova.dimensione
        titolo = dimensione.titolo
        coppia = prova.lettere_di(prova.ripetuto)
        for lettera in prova.lettere:
            riga = f"{titolo}, la lettera {lettera} era: {prova.candidato(lettera).nome}"
            if lettera in coppia:
                altra = next(x for x in coppia if x != lettera)
                riga += f"; è la versione ripetuta per controllo, identica alla lettera {altra}"
            righe.append(riga + ".")
        if prova.nessuna_preferenza:
            righe.append(f"Riepilogo, {titolo}: nessuna preferenza fra le lettere.")
        else:
            valori = medie(prova)
            ordine = sorted(range(len(dimensione.candidati)), key=lambda i: -valori.get(i, 0.0))
            for indice in ordine:
                lettere = prova.lettere_di(indice)
                voti = [prova.voti[lettera] for lettera in lettere if lettera in prova.voti]
                if voti:
                    conto = f"totale {sum(voti)} con {conta(len(voti), 'voto', 'voti')}, media {numero(sum(voti) / len(voti))}"
                else:
                    conto = "nessun voto"
                righe.append(f"Riepilogo, {titolo}, {dimensione.candidati[indice].nome}: {conto}, {_lettere(lettere)}.")
        if prova.nessuna_preferenza:
            righe.append(f"Controllo, {titolo}: le lettere {unisci(coppia)} erano identiche campione per campione, e non hai dato preferenze.")
        else:
            voti_della_coppia = [f"{lettera} {prova.voti.get(lettera, 'senza voto')}" for lettera in coppia]
            righe.append(f"Controllo, {titolo}: le lettere {unisci(coppia)}, identiche campione per campione, hanno avuto {unisci(voti_della_coppia)}.")
        if dimensione.chiave != INSIEME.chiave:
            scelto = dimensione.candidati[scelta(prova)].nome
            if prova.nessuna_preferenza or not prova.voti:
                righe.append(f"Scelta, {titolo}: senza voti resta {scelto}.")
            else:
                righe.append(f"Scelta, {titolo}: {scelto}.")
    return righe


# La sessione.

def esegui(prova, risultati, annotazioni):
    """Un gruppo intero: la domanda e i punti, l'annuncio, il giro, il menu di fine gruppo e i voti nel file."""
    dimensione = prova.dimensione
    titoli = [TITOLI_DEI_PUNTI[chiave] for chiave in dimensione.punti]
    print(f"Nel prossimo gruppo la domanda è: {dimensione.domanda}, con un voto da 1 a 5 per ogni lettera.")
    print(f"In ogni lettera senti {conta(len(titoli), 'punto', 'punti')}, sempre gli stessi e in quest'ordine: {unisci(titoli)}.")
    if not gruppo(dimensione.titolo, len(prova.lettere), "lettere"):
        prova.saltata = True
        risultati.scrivi(f"{dimensione.titolo}: gruppo saltato.")
        return
    giro(prova)
    annotazioni.esito(dimensione.titolo, riproduci=lambda: giro(prova))
    prova.svolta = True
    risultati.scrivi(*righe_dei_voti(prova))
    annotazioni.scrivi_in_sospeso()


def nuovo_seme():
    return random.SystemRandom().randrange(1, 1_000_000)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        seme = int(argv[0]) if argv else nuovo_seme()
    except ValueError:
        print(f"Il seme dev'essere un numero intero, e {argv[0]} non lo è. Uso: python strumenti/banco_spazio.py, con un numero per ripetere le lettere di una sessione passata.")
        return 1
    punti = punti_del_banco()
    prove = prepara(seme, punti)
    print(f"Banco dello spazio della partita di MESS: {conta(len(prove), 'gruppo', 'gruppi')}, e forse un ultimo, che dipende dai tuoi voti.")
    print("In ogni gruppo senti gli stessi punti in più versioni, ciascuna con la sua lettera, sempre dalla tua testata del tavolo, "
          "come giocatore A, e con i suoni provvisori dell'ascolto libero.")
    print("Ogni gruppo si annuncia con la sua domanda e i suoi punti, e si può saltare. Poi viene la rassegna: tutte le lettere una volta, "
          "una dopo l'altra, senza domande; Escape la interrompe.")
    print("Poi il voto, una lettera alla volta: spazio la fa sentire, quante volte vuoi; il tasto di un'altra lettera fa sentire quella, per confronto; "
          "da 1 a 5 dai il voto, dove 5 è il migliore, e passi alla lettera seguente; Invio passa oltre senza cambiare il voto; "
          "n vuol dire nessuna preferenza fra le lettere del gruppo; Escape chiude il voto.")
    print("Mentre una lettera suona i tasti valgono subito, e spazio la fa ripartire.")
    print("A fine gruppo: r rifà la rassegna e il voto, c commenta, Invio lo dà per superato, Escape lo chiude senza giudizio.")
    print(f"I voti e i commenti vanno nel file {FILE_DEI_RISULTATI}, una riga per voce.")
    # enter_escape e gruppo vanno a capo da sé: un print in più farebbe una riga vuota.
    if not enter_escape("\rInvio per cominciare, Escape per uscire\r"):
        return 0
    time.sleep(ascolta_suoni.SILENZIO_INIZIALE)
    risultati = Risultati(percorsi.percorso(FILE_DEI_RISULTATI))
    risultati.scrivi(f"Banco dello spazio, {time.strftime('%Y-%m-%d %H:%M')}, seme {seme}.")
    annotazioni = Annotazioni(risultati.percorso)
    finale = None
    finale_inutile = False
    try:
        for prova in prove:
            esegui(prova, risultati, annotazioni)
        finale = prepara_finale(prove, seme, punti)
        if finale is None:
            finale_inutile = True
            print("Il gruppo finale non serve.")
        else:
            esegui(finale, risultati, annotazioni)
    finally:
        # Anche se la sessione si interrompe, i gruppi chiusi si svelano: senza, i loro voti non direbbero niente.
        annotazioni.scrivi_in_sospeso()
        risultati.scrivi(*righe_della_rivelazione([*prove, *([finale] if finale else [])]))
        if finale_inutile:
            risultati.scrivi(f"{INSIEME.titolo}: il gruppo non è servito, perché le scelte dei tre gruppi sono proprio lo spazio di oggi.")
    print(f"Fine del banco. Nel file {FILE_DEI_RISULTATI}, nella cartella del programma, trovi i voti, quale lettera era quale e il riepilogo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
