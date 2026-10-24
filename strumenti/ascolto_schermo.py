"""
MESS, l'ascolto alla cieca della pallina che batte sullo schermo e torna indietro, issue 12.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-24 con la decisione D37: nella partita dal vivo, dopo l'urto contro lo schermo, la
regia fa tornare la pallina verso chi l'ha tirata con un breve rotolamento, e Gabriele lo conferma con
un ascolto alla cieca. Il modello sono gli ascolti che ci sono: strumenti/ascolta_partita.py per i
punti, strumenti/banco_spazio.py per la prova alla cieca, collaudo_comune di GBUtils per il menu.
I punti sono quelli dell'ascolto della partita: il mondo in memoria con il seme fisso e gli incontri
giocati dal motore in modalità completa, sempre gli stessi. Lo strumento sceglie sei punti che
finiscono con lo schermo contro, tre tirati dal giocatore di chi ascolta e tre dall'avversario, i più
brevi e con colpi diversi, e li compone al volo, senza file WAV e senza suonarli, dalla testata di A,
dal fischio del via alla fine dei suoni del punto. Ogni punto ha due versioni: col ritorno, com'è
adesso la partita, e senza, com'era prima, cioè gli stessi eventi meno il volo del ritorno. Fino
all'urto le due versioni sono identiche campione per campione.
Le coppie. Ogni punto dà una coppia con le due versioni, in un ordine sorteggiato ma pari: in tre
coppie il ritorno viene prima, nelle altre tre dopo. Poi quattro coppie di controllo, con quattro dei
sei punti ripetuti identici: due senza ritorno e due col ritorno. Le dieci coppie si mescolano con un
seme, che si registra. Ogni versione dura quanto la più lunga delle due del suo punto, col silenzio in
coda, così la seconda comincia sempre allo stesso secondo dopo la pausa, e le coppie di un punto
durano uguale, controlli compresi; le due versioni si sentono allo stesso livello, quello della
partita al volume 100, con margine.
Il protocollo è quello delle prove alla cieca di Gabriele, che va trattato come uno strumento di
misura. Prima della prova lo strumento dice soltanto come si esegue e che domanda ci sarà: mai che
cosa cambia, mai quale sia la versione nuova, mai che ci sono coppie di controllo, e la cronaca dei
punti non si legge, perché direbbe che cosa ascoltare. Aspetta il via e quello del gruppo, poi lascia
qualche secondo di silenzio prima della prima coppia. Ogni coppia si annuncia col suo numero e suona da
sé, dopo il silenzio in cui NVDA legge il numero; poi spazio la fa risentire, quante volte si vuole, 1
sceglie la prima, 2 la seconda, u dice che sono uguali o che non c'è preferenza, e si passa alla
coppia seguente; Invio passa oltre lasciando la scelta com'è; Escape chiude le coppie. Un tasto
premuto mentre la coppia suona la ferma e vale subito, e spazio la fa ripartire. In fondo c'è il menu
comune dei collaudi: r rifà le coppie dalla prima, col prompt che ricorda la scelta già data, c
commenta, Invio dà il gruppo per superato, Escape lo chiude senza giudizio.
I risultati vanno nel file ascolto_schermo.txt, nella cartella del programma, una riga per voce: in
testa la data e il seme, poi la scelta di ogni coppia, col solo numero, e i commenti; alla fine della
sessione, e soltanto allora, anche se la si interrompe, quale versione era quale in ogni coppia e il
riepilogo: quante volte è stato scelto il ritorno nelle coppie diverse, tirate dal tuo giocatore e
dall'avversario, che cosa è stato detto nelle coppie uguali, e quante volte la prima e quante la
seconda. Il riepilogo si legge anche a schermo, a sessione finita. Di suo lo strumento non scrive
righe vuote, perché enter_escape e gruppo vanno a capo da sé; le sole che restano vengono dal menu di
collaudo_comune, che qui non si tocca.
Uso, dalla cartella del programma: python strumenti/ascolto_schermo.py. Con un numero, per esempio
python strumenti/ascolto_schermo.py 4127, usa quel seme, e quindi le stesse coppie di una sessione
passata.
"""

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

import ascolta_partita as ap  # noqa: E402
import resa_prototipo as resa  # noqa: E402
from banco_spazio import Annotazioni, Risultati, nuovo_seme, suona  # noqa: E402
from collaudo_comune import gruppo  # noqa: E402
from GBUtils import enter_escape, key  # noqa: E402

import ascolta_suoni  # noqa: E402
import partita_sonora as ps  # noqa: E402
import percorsi  # noqa: E402
from motore import cronaca as C  # noqa: E402
from motore import eventi as E  # noqa: E402
from testi import conta  # noqa: E402

FILE_DEI_RISULTATI = "ascolto_schermo.txt"
TITOLO = "Schermo centrale, le coppie"
# Chi ascolta sta sempre alla testata di A, il suo giocatore.
ASCOLTATORE = "A"
# I punti: tre per parte, fra quelli con al più tre colpi di scambio, e quattro coppie di controllo.
PUNTI_PER_PARTE = 3
ATTACCHI_MASSIMI = 3
COPPIE_DI_CONTROLLO = 4
# Le due versioni di un punto.
CON = "con"
SENZA = "senza"
DESCRIZIONI = {CON: "col ritorno della pallina dopo l'urto, la versione nuova", SENZA: "senza ritorno, quella di prima"}
# Il silenzio prima di ogni coppia, per il suo numero letto da NVDA; la prima segue il via del gruppo e
# ha in più il silenzio dei collaudi. Chi risente la coppia l'ha appena chiesta: quasi niente. Fra le
# due versioni, una pausa.
ANTICIPO_COPPIA = 2.0
ANTICIPO_PRIMA_COPPIA = ANTICIPO_COPPIA + ascolta_suoni.SILENZIO_INIZIALE
ANTICIPO_RIPETIZIONE = ap.ANTICIPO
PAUSA_FRA_LE_VERSIONI = 1.5
# Le risposte, e i tasti che valgono anche mentre la coppia suona: la fermano, come nel voto del banco
# dello spazio, da cui viene suona.
RISPOSTE = {"1": "la prima", "2": "la seconda", "u": "uguali"}
TASTI_DELLE_COPPIE = frozenset({" ", "\r", "\x1b", "1", "2", "u", "U"})
DOMANDA = "quale delle due versioni ti sembra più vicina a quello che si sente al tavolo vero"


class Coppia(NamedTuple):
    """Una coppia: il punto giocato, le due versioni nell'ordine in cui si sentono, il buffer da sentire e il campione da cui comincia la seconda."""
    punto: object
    versioni: tuple
    buffer: np.ndarray
    seconda: int

    @property
    def controllo(self):
        return self.versioni[0] == self.versioni[1]


# I punti e le versioni.

def e_ritorno(evento):
    """Vero se l'evento è il volo della pallina che torna indietro dallo schermo, issue 12."""
    return evento.tipo == E.VOLO and bool((evento.dati or {}).get("ritorno"))


def senza_ritorno(eventi):
    """Gli eventi com'erano prima della issue 12: gli stessi, meno il volo del ritorno."""
    return [e for e in eventi if not e_ritorno(e)]


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
    for parte in ("A", "B"):
        buoni = [c for c in candidati
                 if c.momento.esito is not None and c.momento.esito.causa == "schermo_contro" and c.momento.esito.attacchi <= ATTACCHI_MASSIMI
                 and chi_tira(c) == parte and any(e_ritorno(e) for e in c.momento.eventi)]
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


def componi_versione(candidato, versione):
    """Il buffer di una versione del punto per chi ascolta da A, prima del livello: l'azione composta, col ritorno o senza."""
    eventi = resa.azione(candidato.momento.eventi)
    if versione == SENZA:
        eventi = senza_ritorno(eventi)
    return ps.componi(eventi, ASCOLTATORE).buffer


def componi_coppia(candidato, versioni, composte=None):
    """
    Il buffer di una coppia: le due versioni, ciascuna lunga quanto la più lunga delle due versioni
    del punto, col silenzio in coda, e la pausa fra loro, al livello della partita al volume 100, lo
    stesso per le due. Così ogni coppia dello stesso punto dura uguale, controlli compresi. composte
    tiene le versioni già composte, per punto e versione. Restituisce il buffer e il campione da cui
    comincia la seconda versione.
    """
    composte = {} if composte is None else composte
    for versione in (CON, SENZA):
        if (id(candidato.momento), versione) not in composte:
            composte[id(candidato.momento), versione] = componi_versione(candidato, versione)
    lunghezza = max(len(composte[id(candidato.momento), versione]) for versione in (CON, SENZA))
    pezzi = [composte[id(candidato.momento), versione] for versione in versioni]
    pezzi = [np.concatenate([pezzo, np.zeros((lunghezza - len(pezzo), 2), dtype=np.float32)]) for pezzo in pezzi]
    pausa = np.zeros((round(PAUSA_FRA_LE_VERSIONI * ps.FS), 2), dtype=np.float32)
    buffer = ps.per_la_cassa(np.concatenate([pezzi[0], pausa, pezzi[1]]), ps.VOLUME_DI_PROGETTO)
    return buffer, lunghezza + len(pausa)


def assegna(rng, punti):
    """
    Le coppie, come punto e versioni nell'ordine in cui si sentono, già mescolate: ogni punto con le
    due versioni, il ritorno prima in metà delle coppie e dopo nell'altra metà; poi COPPIE_DI_CONTROLLO
    punti presi a caso con una versione ripetuta, metà senza ritorno e metà col ritorno.
    """
    ordini = [(CON, SENZA)] * (len(punti) // 2) + [(SENZA, CON)] * (len(punti) - len(punti) // 2)
    rng.shuffle(ordini)
    coppie = list(zip(punti, ordini, strict=True))
    ripetute = [SENZA] * (COPPIE_DI_CONTROLLO // 2) + [CON] * (COPPIE_DI_CONTROLLO - COPPIE_DI_CONTROLLO // 2)
    rng.shuffle(ripetute)
    coppie += [(punto, (versione, versione)) for punto, versione in zip(rng.sample(punti, COPPIE_DI_CONTROLLO), ripetute, strict=True)]
    rng.shuffle(coppie)
    return coppie


class Prova:
    """L'ascolto: il seme, le coppie, le scelte che si raccolgono, per posto della coppia, e come si è chiuso."""

    def __init__(self, seme, coppie):
        self.seme = seme
        self.coppie = coppie
        self.scelte = {}
        self.saltata = False
        self.svolta = False
        self.interrotta = False
        # Chiusa senza giudizio, con Escape nel menu di fine gruppo: le scelte restano nel file ma non contano.
        self.chiusa = False

    def da_sentire(self, posto, anticipo):
        """Il buffer della coppia al suo posto con il silenzio dell'anticipo in testa."""
        silenzio = np.zeros((round(anticipo * ps.FS), 2), dtype=np.float32)
        return np.concatenate([silenzio, self.coppie[posto].buffer])


def prepara(seme, candidati=None):
    """La prova, con le coppie sorteggiate dal seme e già composte, senza suonare."""
    punti = scegli_punti(ap.punti_giocati() if candidati is None else candidati)
    composte = {}
    coppie = [Coppia(punto, versioni, *componi_coppia(punto, versioni, composte)) for punto, versioni in assegna(random.Random(seme), punti)]
    return Prova(seme, coppie)


# L'ascolto.

def invito(scelta):
    """Il prompt della risposta, entro quaranta caratteri, con la scelta già data se c'è."""
    if scelta is None:
        return "\rSpazio ripete; 1, 2 o u per uguali\r"
    return f"\rHai scelto {RISPOSTE[scelta]}: spazio, 1, 2 o u\r"


def ascolta(prova):
    """
    Le coppie una dopo l'altra, dalla prima. Ogni coppia si annuncia e suona da sé; poi spazio la fa
    risentire, 1, 2 o u è la risposta e porta alla seguente, Invio passa oltre lasciando la scelta
    com'è, Escape chiude le coppie. I tasti valgono anche mentre la coppia suona, e la fermano.
    Restituisce falso se le coppie si sono chiuse con Escape prima della fine.
    """
    for posto in range(len(prova.coppie)):
        print(f"Coppia {posto + 1} di {len(prova.coppie)}.")
        tasto = suona(prova.da_sentire(posto, ANTICIPO_COPPIA if posto else ANTICIPO_PRIMA_COPPIA), TASTI_DELLE_COPPIE)
        while True:
            if tasto is None:
                tasto = key(invito(prova.scelte.get(posto)))
                print()
            scelto, tasto = tasto, None
            if scelto == " ":
                tasto = suona(prova.da_sentire(posto, ANTICIPO_RIPETIZIONE), TASTI_DELLE_COPPIE)
            elif scelto == "\r":
                break
            elif scelto == "\x1b":
                print("Coppie chiuse.")
                return False
            elif scelto is not None and scelto.lower() in RISPOSTE:
                prova.scelte[posto] = scelto.lower()
                break
    return True


# I risultati.

def righe_delle_scelte(prova):
    """Le scelte, col solo numero della coppia: una riga per coppia."""
    return [f"{TITOLO}, coppia {posto + 1}: {RISPOSTE.get(prova.scelte.get(posto), 'senza scelta')}." for posto in range(len(prova.coppie))]


def _chi(coppia):
    nomi = coppia.punto.nomi
    parte = chi_tira(coppia.punto)
    di_chi = "del tuo giocatore" if parte == ASCOLTATORE else "dell'avversario"
    colpo = coppia.punto.momento.esito.colpo_decisivo
    return f"{C.con_articolo(colpo)} di {nomi[parte].testo}, {di_chi}"


def _scelta_detta(coppia, scelta):
    """Che cosa vuol dire la scelta di una coppia: quale versione, o uguali."""
    if scelta is None:
        return "senza scelta"
    if scelta == "u":
        return "per te erano uguali"
    if coppia.controllo:
        return f"hai scelto {RISPOSTE[scelta]}"
    versione = coppia.versioni[0 if scelta == "1" else 1]
    return f"hai scelto {RISPOSTE[scelta]}, quella {'col ritorno' if versione == CON else 'senza ritorno'}"


def righe_della_rivelazione(prova):
    """Quello che si scrive soltanto alla fine: quale versione era quale in ogni coppia, e la scelta detta in chiaro."""
    righe = []
    for posto, coppia in enumerate(prova.coppie):
        inizio = f"{TITOLO}, coppia {posto + 1}, {_chi(coppia)}"
        prima, seconda = coppia.versioni
        if coppia.controllo:
            quale = f"era una coppia di controllo, con due versioni identiche campione per campione, tutte e due {DESCRIZIONI[prima]}"
        else:
            quale = f"la prima era {DESCRIZIONI[prima]}; la seconda era {DESCRIZIONI[seconda]}"
        righe.append(f"{inizio}: {quale}; {_scelta_detta(coppia, prova.scelte.get(posto))}.")
    return righe


def conti(prova, coppie):
    """Per le coppie indicate, come posti: quante volte il ritorno, senza ritorno, uguali, la prima, la seconda e senza scelta."""
    risultato = dict.fromkeys(("ritorno", "senza", "uguali", "prima", "seconda", "nessuna"), 0)
    for posto in coppie:
        coppia, scelta = prova.coppie[posto], prova.scelte.get(posto)
        if scelta is None:
            risultato["nessuna"] += 1
        elif scelta == "u":
            risultato["uguali"] += 1
        else:
            risultato["prima" if scelta == "1" else "seconda"] += 1
            if not coppia.controllo:
                risultato["ritorno" if coppia.versioni[0 if scelta == "1" else 1] == CON else "senza"] += 1
    return risultato


def _volte(n):
    return conta(n, "volta", "volte")


def righe_del_riepilogo(prova):
    """Il riepilogo: le coppie diverse, tutte e per chi ha tirato; le coppie uguali; l'ordine."""
    diverse = [posto for posto, c in enumerate(prova.coppie) if not c.controllo]
    uguali = [posto for posto, c in enumerate(prova.coppie) if c.controllo]
    righe = []
    if prova.chiusa:
        righe.append(f"Riepilogo, {TITOLO}: il gruppo è stato chiuso senza giudizio, quindi le scelte che seguono non contano.")
    k = conti(prova, diverse)
    righe.append(f"Riepilogo, coppie diverse: {conta(len(diverse), 'coppia', 'coppie')}; hai scelto il ritorno {_volte(k['ritorno'])}, senza ritorno "
                 f"{_volte(k['senza'])}, uguali {_volte(k['uguali'])}, senza scelta {_volte(k['nessuna'])}.")
    for parte, chi in ((ASCOLTATORE, "tirate dal tuo giocatore"), ("B" if ASCOLTATORE == "A" else "A", "tirate dall'avversario")):
        posti = [posto for posto in diverse if chi_tira(prova.coppie[posto].punto) == parte]
        k = conti(prova, posti)
        righe.append(f"Riepilogo, coppie diverse {chi}: {conta(len(posti), 'coppia', 'coppie')}; il ritorno {_volte(k['ritorno'])}, senza ritorno "
                     f"{_volte(k['senza'])}, uguali {_volte(k['uguali'])}, senza scelta {_volte(k['nessuna'])}.")
    k = conti(prova, uguali)
    righe.append(f"Riepilogo, coppie uguali di controllo: {conta(len(uguali), 'coppia', 'coppie')}; hai detto uguali {_volte(k['uguali'])}, "
                 f"la prima {_volte(k['prima'])}, la seconda {_volte(k['seconda'])}, senza scelta {_volte(k['nessuna'])}.")
    k = conti(prova, range(len(prova.coppie)))
    righe.append(f"Riepilogo, l'ordine: in tutte le coppie hai scelto la prima {_volte(k['prima'])} e la seconda {_volte(k['seconda'])}.")
    return righe


# La sessione.

def esegui(prova, risultati, annotazioni):
    """
    Il gruppo intero: la domanda, prima del via, perché NVDA la legga prima del primo suono, l'annuncio,
    le coppie, il menu di fine gruppo e le scelte nel file. Se il menu si chiude con Escape, senza
    giudizio, le scelte si scrivono lo stesso ma il riepilogo lo dice.
    """
    print(f"Per ogni coppia la domanda è: {DOMANDA}? 1 la prima, 2 la seconda, u se ti sembrano uguali o non hai preferenze.")
    if not gruppo(TITOLO, len(prova.coppie), "coppie"):
        prova.saltata = True
        risultati.scrivi(f"{TITOLO}: gruppo saltato.")
        return

    def giro():
        prova.interrotta = not ascolta(prova)

    prova.svolta = True
    giro()
    prova.chiusa = annotazioni.esito(TITOLO, riproduci=giro) == "chiuso"
    risultati.scrivi(*righe_delle_scelte(prova))
    annotazioni.scrivi_in_sospeso()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        seme = int(argv[0]) if argv else nuovo_seme()
    except ValueError:
        print(f"Il seme dev'essere un numero intero, e {argv[0]} non lo è. Uso: python strumenti/ascolto_schermo.py, con un numero per ripetere le coppie di una sessione passata.")
        return 1
    print("Preparo le coppie, qualche secondo.")
    prova = prepara(seme)
    print(f"Ascolto alla cieca dello schermo centrale: {conta(len(prova.coppie), 'coppia', 'coppie')}, sempre dalla tua testata del tavolo, come giocatore A.")
    print("In ogni coppia senti due volte lo stesso punto, dal fischio dell'arbitro che dà il via fino alla fine dei suoi suoni, con una pausa fra le due volte. "
          "Il punto finisce con uno schermo centrale.")
    print(f"La domanda è sempre la stessa: {DOMANDA}. 1 se preferisci la prima, 2 la seconda, u se ti sembrano uguali o non hai preferenze.")
    print("Ogni coppia si annuncia col suo numero e suona da sola. Spazio la fa risentire, quante volte vuoi; con 1, 2 o u rispondi e passi alla coppia seguente; "
          "Invio passa oltre senza cambiare la risposta; Escape chiude le coppie. Mentre la coppia suona i tasti valgono subito, e spazio la fa ripartire.")
    print("A fine gruppo: r rifà le coppie dalla prima, c commenta, Invio lo dà per superato, Escape lo chiude senza giudizio.")
    print(f"Le risposte vanno nel file {FILE_DEI_RISULTATI}, una riga per coppia; che cosa c'era in ogni coppia lo trovi lì, ma soltanto alla fine.")
    # enter_escape e gruppo vanno a capo da sé: un print in più farebbe una riga vuota. Il silenzio
    # prima del primo suono sta nell'anticipo della prima coppia, dopo il via del gruppo.
    if not enter_escape("\rInvio per cominciare, Escape per uscire\r"):
        return 0
    risultati = Risultati(percorsi.nel_programma(FILE_DEI_RISULTATI))
    risultati.scrivi(f"Ascolto dello schermo centrale, {time.strftime('%Y-%m-%d %H:%M')}, seme {seme}.")
    annotazioni = Annotazioni(risultati.percorso)
    try:
        esegui(prova, risultati, annotazioni)
    finally:
        # Anche se la sessione si interrompe, le coppie ascoltate si svelano: senza, le scelte non direbbero niente.
        annotazioni.scrivi_in_sospeso()
        if prova.svolta:
            if prova.interrotta:
                risultati.scrivi(f"{TITOLO}: le coppie si sono chiuse prima della fine.")
            risultati.scrivi(*righe_della_rivelazione(prova), *righe_del_riepilogo(prova))
    if prova.svolta:
        for riga in righe_del_riepilogo(prova):
            print(riga)
    print(f"Fine dell'ascolto. Nel file {FILE_DEI_RISULTATI}, nella cartella del programma, trovi le tue risposte, quale versione era quale e il riepilogo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
