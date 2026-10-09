"""
L'allenamento dei giocatori di MESS: il costo dei punti, la spesa a mano, la spesa secondo il
programma e il calo dei livelli alti.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 2 del piano, dallo smontaggio di sd.py. Il 2026-10-09 la tappa 11
lo riscrive da capo secondo la decisione D31 e le risposte di Gabriele del 9 ottobre 2026.
Il costo è tarato sul valore. Per una caratteristica, il costo marginale di un punto è il ritmo
COSTO_PER_PUNTO_PESATO per il peso che la caratteristica ha nel valore di quel giocatore, per lo
sconto degli ipovedenti, diviso l'efficacia, per l'esponenziale della crescita del costo per il
livello relativo, cioè il totale sul tetto. Così ogni punto allenamento compra la stessa somma
pesata in tutte le caratteristiche che stanno allo stesso livello relativo: la precisione, che
pesa tanto, sale piano, le sponde salgono in fretta. Il prezzo sale punto per punto: la spesa è
l'integrale del costo marginale, e duecento punti spesi in una volta rendono come due spese da cento.
Il tetto è uno solo, quello del totale, 10 per precisione, resistenza e forza e 40 per le altre:
la parte allenata non ha più tetti suoi, risposta 6 di Gabriele, e arriva fino al tetto meno
l'innata; ci pensa il prezzo, che all'ultimo punto è dodici volte il primo, e il calo dei livelli
alti, che toglie un poco ogni mese a chi sta sopra il 70 per cento del tetto.
L'efficacia viene dalla curva d'età di Hattrick, dai tratti rari e dall'aggancio dell'allenatore,
ed è quella del momento della spesa. Niente osmosi: cresce soltanto ciò su cui si spende.
La spesa secondo il programma, una per tutti, è un riempimento a livello in forma chiusa: ogni
caratteristica ha un punteggio, quanta somma pesata rende il prossimo punto lì, per la preferenza
che l'indole del programma le dà; un livello d'acqua scende finché il portafoglio non è speso, e
ogni caratteristica col punteggio sopra il livello sale fino a pareggiarlo. Le caratteristiche
alla pari salgono insieme, e una caratteristica arrivata al tetto si ferma lì.
"""

import math
from collections import namedtuple

import tratti
import valore
from costanti import (
    ANNO_SIMULAZIONE_GIORNI,
    ATTRIBUTI_ALLENABILI,
    CALO_MASSIMO_ANNUO,
    COSTO_PER_PUNTO_PESATO,
    CRESCITA_DEL_COSTO,
    FATTORE_ALLENATORE,
    INDOLE_PREDEFINITA,
    INDOLI,
    MAX_TOTALE_PRECISIONE_RESISTENZA,
    MAX_TOTALE_SKILL_GIOCO,
    PREFERENZA_PRINCIPALE,
    PREFERENZA_SECONDARIA,
    SCONTO_IPOVEDENTI,
    SOGLIA_CALO_LIVELLI_ALTI,
)
from modelli import annota_spesa

# Una spesa su una caratteristica: il nome senza suffisso, il totale prima e dopo, i punti usati.
Spesa = namedtuple("Spesa", "caratteristica da a punti")
# Le 24 caratteristiche allenabili, coi nomi senza suffisso, nell'ordine di costanti.py.
CARATTERISTICHE = tuple(valore.nome_semplice(nome) for nome in ATTRIBUTI_ALLENABILI)
_FISICHE = frozenset(("precisione", "resistenza", "forza"))
_K = CRESCITA_DEL_COSTO
_EXP_K = math.exp(CRESCITA_DEL_COSTO)
# Sotto questa soglia due numeri si considerano uguali: un totale al tetto, un portafoglio vuoto.
_QUASI_ZERO = 1e-9


def nome(caratteristica):
    """Il nome di una caratteristica allenabile senza suffisso; ValueError se non è allenabile."""
    semplice = valore.nome_semplice(caratteristica)
    if semplice not in CARATTERISTICHE:
        raise ValueError(f"Caratteristica che non si allena: {caratteristica}.")
    return semplice


def tetto(caratteristica):
    """Il tetto del totale, innata più allenata: 10 per precisione, resistenza e forza, 40 per le altre. Dalla tappa 11 è l'unico tetto."""
    return MAX_TOTALE_PRECISIONE_RESISTENZA if nome(caratteristica) in _FISICHE else MAX_TOTALE_SKILL_GIOCO


def allenata_massima(g, caratteristica):
    """Fin dove può arrivare la parte allenata: il tetto del totale meno l'innata."""
    c = nome(caratteristica)
    return max(0.0, tetto(c) - getattr(g, c + "_base"))


def totale(g, caratteristica):
    c = nome(caratteristica)
    return getattr(g, c + "_base") + getattr(g, c + "_allenata")


def livello_relativo(g, caratteristica):
    """Il totale sul tetto, da 0 a 1: lo stesso livello che il motore usa in campo."""
    return totale(g, caratteristica) / tetto(caratteristica)


def sconto(g, caratteristica):
    """Il fattore dello sconto: 0,93 per gli ipovedenti sulle caratteristiche di gioco, 1 altrimenti."""
    if getattr(g, "ipovedente", False) and nome(caratteristica) not in _FISICHE:
        return 1.0 - SCONTO_IPOVEDENTI
    return 1.0


def efficacia(g, caratteristica=None):
    """
    Quanto rende l'allenamento, oggi: la curva d'età di Hattrick per la maturazione, per il
    talento e l'apprendista rapido se ci sono, per l'allenatore. Uguale per tutte le
    caratteristiche: l'argomento c'è perché chi chiama ragiona per caratteristica.
    """
    del caratteristica
    anni = g.eta / ANNO_SIMULAZIONE_GIORNI
    return tratti.curva_eta(anni) * tratti.fattore_maturazione(g) * tratti.efficacia_dei_tratti(g) * FATTORE_ALLENATORE


def _coefficiente(g, c, efficacia_del_giorno=None):
    """Il fattore a del costo marginale, a per exp(K per il livello relativo): ritmo per peso per sconto, diviso l'efficacia."""
    e = efficacia(g) if efficacia_del_giorno is None else efficacia_del_giorno
    return COSTO_PER_PUNTO_PESATO * valore.peso_per_punto(g, c) * sconto(g, c) / e


def costo_fra(g, caratteristica, da, a):
    """I punti allenamento che servono per portare il totale della caratteristica da un valore a un altro: l'integrale del costo marginale."""
    c = nome(caratteristica)
    t = tetto(c)
    if a <= da:
        return 0.0
    return _coefficiente(g, c) * t / _K * (math.exp(_K * a / t) - math.exp(_K * da / t))


def totale_con(g, caratteristica, punti):
    """Il totale della caratteristica dopo una spesa di tanti punti, fermo al tetto del totale."""
    c = nome(caratteristica)
    t = tetto(c)
    attuale = totale(g, c)
    if punti <= 0:
        return attuale
    nuovo = t / _K * math.log(math.exp(_K * attuale / t) + punti * _K / (_coefficiente(g, c) * t))
    return min(t, nuovo)


def costo_del_prossimo_punto(g, caratteristica):
    """Quanto costa il prossimo punto, o quel che resta fino al tetto; zero per una caratteristica al massimo."""
    c = nome(caratteristica)
    attuale = totale(g, c)
    return costo_fra(g, c, attuale, min(attuale + 1.0, tetto(c)))


def anteprima(g, caratteristica, punti):
    """Cosa farebbe una spesa, senza toccare niente: Spesa con il totale prima e dopo e i punti davvero usati, mai oltre il tetto."""
    c = nome(caratteristica)
    t = tetto(c)
    attuale = totale(g, c)
    if punti <= 0 or attuale >= t - _QUASI_ZERO:
        return Spesa(c, attuale, attuale, 0.0)
    arrivo = totale_con(g, c, punti)
    usati = float(punti) if arrivo < t else min(float(punti), costo_fra(g, c, attuale, t))
    return Spesa(c, attuale, arrivo, usati)


def puo_allenarsi(g):
    """Vero se il giocatore si allena: chi può giocare, quindi non l'infortunato, ma sì l'ambidestro col braccio fermo."""
    return g.puo_giocare


def _applica(g, spese):
    """Porta le spese nelle parti allenate, entro il tetto del totale."""
    for spesa in spese:
        c = spesa.caratteristica
        base = getattr(g, c + "_base")
        setattr(g, c + "_allenata", max(0.0, min(tetto(c) - base, spesa.a - base)))


def spendi(g, caratteristica, punti, data=None):
    """
    La spesa a mano: tanti punti allenamento su una caratteristica. Toglie dal portafoglio i punti
    davvero usati, che sono meno di quelli chiesti quando la caratteristica arriva al tetto,
    ricalcola il valore e, con la data simulata, annota la spesa nel diario. Restituisce la Spesa.
    ValueError se il giocatore non si allena, se ha meno punti di quelli chiesti o se la
    caratteristica è già al tetto del totale.
    """
    c = nome(caratteristica)
    if not puo_allenarsi(g):
        raise ValueError(f"{g.nome} {g.cognome} oggi non si allena.")
    if punti <= 0:
        raise ValueError("Si spende almeno una frazione di punto.")
    if punti > g.punti_allenamento + _QUASI_ZERO:
        raise ValueError(f"{g.nome} {g.cognome} ha soltanto {g.punti_allenamento:.1f} punti allenamento.")
    if totale(g, c) >= tetto(c) - _QUASI_ZERO:
        raise ValueError(f"{c} è già al massimo.")
    spesa = anteprima(g, c, min(punti, g.punti_allenamento))
    valore_prima = g.indice_collettivo_valore
    _applica(g, [spesa])
    g.punti_allenamento = max(0.0, g.punti_allenamento - spesa.punti)
    g.aggiorna_icv()
    if data is not None:
        annota_spesa(g.diario, data, [(c + "_base", spesa.da, spesa.a)], spesa.punti, valore_prima, g.indice_collettivo_valore, fondi=True)
    return spesa


_PREFERENZE = {}


def preferenze(chiave):
    """Le preferenze del modello di spesa per un'indole: 2 alle principali, 1,4 alle secondarie, 1 alle altre."""
    if chiave not in _PREFERENZE:
        indole = INDOLI[chiave]
        tabella = dict.fromkeys(CARATTERISTICHE, 1.0)
        tabella.update(dict.fromkeys(indole["secondarie"], PREFERENZA_SECONDARIA))
        tabella.update(dict.fromkeys(indole["principali"], PREFERENZA_PRINCIPALE))
        _PREFERENZE[chiave] = tabella
    return _PREFERENZE[chiave]


def _riempimento(g, preferite, portafoglio):
    """
    Il riempimento a livello in forma chiusa: dove porta il portafoglio, per ogni caratteristica.
    Restituisce le coppie di caratteristica e totale d'arrivo, e i punti usati.
    Per una caratteristica il costo da x0 a x è coeff per (exp(K x) meno exp(K x0)), e il punteggio
    del prossimo punto è la preferenza diviso lo sconto per exp(meno K x). A un livello d'acqua λ la
    caratteristica sta dove il punteggio vale λ, cioè exp(K x) vale preferenza su sconto diviso λ:
    finché l'insieme delle caratteristiche che salgono non cambia, il costo totale è A diviso λ più B.
    Gli eventi sono due per caratteristica: l'ingresso, quando λ scende al suo punteggio di partenza,
    e il tetto, quando λ scende a preferenza su sconto per exp(meno K). Si percorrono dal λ più alto,
    finché il costo non raggiunge il portafoglio; l'ultimo tratto si risolve con una divisione.
    """
    e = efficacia(g)
    voci = []
    for c in CARATTERISTICHE:
        t = tetto(c)
        attuale = totale(g, c)
        if attuale >= t - _QUASI_ZERO:
            continue
        s = sconto(g, c)
        coeff = COSTO_PER_PUNTO_PESATO * valore.peso_per_punto(g, c) * s * t / (e * _K)
        voci.append((c, coeff, math.exp(_K * attuale / t), preferite[c] / s, t, attuale))
    eventi = []
    for i, (_c, _coeff, e0, ps, _t, _attuale) in enumerate(voci):
        eventi.append((ps / e0, 0, i))
        eventi.append((ps / _EXP_K, 1, i))
    eventi.sort(key=lambda evento: (-evento[0], evento[1]))
    a_tot = b_tot = 0.0
    stato = [0] * len(voci)
    livello = None
    for lam, tipo, i in eventi:
        if a_tot > 0.0 and a_tot / lam + b_tot >= portafoglio:
            livello = a_tot / (portafoglio - b_tot)
            break
        _c, coeff, e0, ps, _t, _attuale = voci[i]
        if tipo == 0:
            a_tot += coeff * ps
            b_tot -= coeff * e0
            stato[i] = 1
        else:
            a_tot -= coeff * ps
            b_tot += coeff * _EXP_K
            stato[i] = 2
    arrivi = []
    for (c, _coeff, _e0, ps, t, attuale), st in zip(voci, stato, strict=True):
        if st == 2:
            arrivi.append((c, t))
        elif st == 1:
            arrivi.append((c, max(attuale, min(t, t * math.log(ps / livello) / _K))))
    usati = portafoglio if livello is not None else b_tot
    return arrivi, usati


def allena_secondo_programma(g, data=None, programma=None):
    """
    Spende tutto il portafoglio secondo il programma, l'indole scelta, o quello del giocatore se
    non è dato, con il riempimento a livello. Restituisce l'elenco delle Spesa, una per
    caratteristica salita; con la data simulata scrive nel diario una voce sola. Chi non si allena,
    o non ha punti, non spende niente.
    """
    if not puo_allenarsi(g) or g.punti_allenamento <= _QUASI_ZERO:
        return []
    programma = programma or getattr(g, "programma", None) or INDOLE_PREDEFINITA
    arrivi, usati = _riempimento(g, preferenze(programma), g.punti_allenamento)
    spese = []
    for c, arrivo in arrivi:
        prima = totale(g, c)
        if arrivo > prima + _QUASI_ZERO:
            spese.append(Spesa(c, prima, arrivo, costo_fra(g, c, prima, arrivo)))
    if not spese:
        return []
    valore_prima = g.indice_collettivo_valore
    _applica(g, spese)
    g.punti_allenamento = max(0.0, g.punti_allenamento - usati)
    if g.punti_allenamento <= _QUASI_ZERO:
        g.punti_allenamento = 0.0
    g.aggiorna_icv()
    if data is not None:
        annota_spesa(g.diario, data, [(s.caratteristica + "_base", s.da, s.a) for s in spese], usati, valore_prima, g.indice_collettivo_valore)
    return spese


def mantenimento_del_mese(g, giorni):
    """
    Il primo del mese, per i giorni del mese appena finito: ogni caratteristica sopra il 70 per
    cento del tetto perde un poco dall'allenata, mai sotto zero, sempre di più verso il tetto, come
    la DropL di Hattrick; l'apprendista rapido, in più, dimentica: ogni allenata si moltiplica per
    il suo oblio. Restituisce quanto si è perso in tutto; se si è perso qualcosa ricalcola il valore.
    """
    perso = 0.0
    oblio = tratti.oblio_mensile(g)
    quota = giorni / ANNO_SIMULAZIONE_GIORNI
    for c in CARATTERISTICHE:
        nome_allenata = c + "_allenata"
        allenata = getattr(g, nome_allenata)
        if allenata <= 0.0:
            continue
        t = tetto(c)
        relativo = (getattr(g, c + "_base") + allenata) / t
        nuova = allenata
        if relativo > SOGLIA_CALO_LIVELLI_ALTI:
            eccesso = (relativo - SOGLIA_CALO_LIVELLI_ALTI) / (1.0 - SOGLIA_CALO_LIVELLI_ALTI)
            nuova = max(0.0, nuova - CALO_MASSIMO_ANNUO * eccesso ** 3 * t * quota)
        nuova *= oblio
        if nuova != allenata:
            perso += allenata - nuova
            setattr(g, nome_allenata, nuova)
    if perso > 0.0:
        g.aggiorna_icv()
    return perso
