"""
L'economia di MESS: i conti di giocatori e polisportive.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 8 del piano, secondo la decisione D22, sul modello di Hattrick.
Qui stanno i calcoli, che non cambiano niente: lo stipendio che un giocatore chiede, secondo
valore, tratti rari ed esperienza; il premio d'ingaggio che chiede a una polisportiva, secondo la
reputazione di lei; il suo valore di mercato; lo sponsor di una polisportiva, secondo la gloria;
la pazienza di chi non viene pagato, che dura secondo la fedeltà, e l'umore che ne viene fuori.
Le operazioni che muovono i soldi sono regole del mondo, e stanno in mondo.py.
Dalla tappa 11, il 2026-10-09, decisione D31, c'è il contratto: lo stipendio che il giocatore
chiede resta la formula di prima, ma quello che una polisportiva paga è fisso fino alla scadenza,
quindi chi migliora allenandosi non costa di più finché il contratto dura; il valore di mercato
scende negli ultimi tre mesi di contratto, fino al 40 per cento alla scadenza, per chi non ha
rinnovato.
Dalla tappa 12, decisione 1 di Gabriele del 14 ottobre 2026, il computer spende secondo la cassa:
oltre una soglia la cassa in più si conta spesa in qualche mese, e un mese di quella spesa si aggiunge
agli stipendi che si permette. Non al prezzo che paga per un giocatore in vendita, che resta entro il
valore di mercato col rialzo del computer: la verifica del 15 ottobre 2026 lo ha tolto, perché faceva
comprare a più volte il loro valore i giocatori che l'utente metteva in vendita a un prezzo gonfiato.
Dal 2 novembre 2026, con la decisione D40, lo sponsor delle polisportive dell'utente paga la parte della
gloria in proporzione ai tesserati in attività sul massimo dei posti: una polisportiva vuota non la
incassa, e dividere i giocatori fra più polisportive non rende più. La parte sul valore della rosa e lo
sponsor del computer restano come prima. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5,
UltraCode).
Dal 3 novembre 2026, con la sesta tranche di D40, il commercio dei liberi: rivendita_dal dice da quando il
computer compra un tesserato dell'utente, MESI_PRIMA_DELLA_RIVENDITA mesi dopo la firma; e il valore di una
vendita dell'utente non conta il rinnovo concordato, che il compratore annulla, ma la scadenza vera. Fra le
polisportive del computer il valore resta quello di prima. È di Gabriele Battaglia (IZ4APU) & ClaudIA
(Claude Opus 5.5, UltraCode).
Lo stesso giorno, con la scelta di Gabriele che vale come D40, al posto dell'attesa la rampa del prezzo:
tetto_di_rivendita dice il prezzo più alto che il computer paga oggi per un tesserato dell'utente, che parte
dall'ingaggio il giorno della firma e sale in linea retta fino al tetto pieno, tetto_pieno_di_rivendita, in
MESI_DELLA_RAMPA mesi; rivendita_piena_dal dice il giorno del tetto pieno, e rivendita_al_prezzo_dal il giorno
in cui il tetto arriva a un prezzo dato. rivendita_dal non c'è più. È di Gabriele Battaglia (IZ4APU) & ClaudIA
(Claude Opus 5.5, UltraCode).
"""

import datetime
import math

import contratti
from costanti import (
    AUMENTO_STIPENDIO_PER_ESPERIENZA,
    FATTORE_GLORIA_RICHIESTA_AMBIDESTRO,
    FATTORE_GLORIA_RICHIESTA_CAMBIO_VEL,
    FATTORE_GLORIA_RICHIESTA_GIOCO_RAPIDO,
    FEDELTA_BANDIERA,
    FEDELTA_PER_MESE_DI_PAZIENZA,
    MAX_TESSERATI_POLISPORTIVA,
    MESI_CASSA_PIENA_CPU,
    MESI_DELLA_RAMPA,
    MESI_DI_INGAGGIO,
    MESI_DI_VALORE,
    MESI_VALORE_PIENO,
    PARTI_DI_CASSA_PER_STIPENDI,
    QUOTA_SPONSOR_SUL_VALORE,
    REPUTAZIONE_MASSIMA,
    REPUTAZIONE_MINIMA,
    RIALZO_CPU,
    SCALA_STIPENDIO,
    SOGLIA_CASSA_PIENA_CPU,
    SPONSOR_PER_GLORIA,
    STIPENDIO_DI_RIFERIMENTO,
    STIPENDIO_MINIMO,
    VALORE_A_SCADENZA,
    VALORE_DI_RIFERIMENTO,
)


def arrotonda(euro, passo=10):
    """Una cifra in euro arrotondata a un passo, per default alla decina."""
    return round(euro / passo) * passo


def scritta_in_euro(importo):
    """Una cifra in euro a parole, con il punto delle migliaia: 2.400 euro."""
    return f"{int(importo):,} euro".replace(",", ".")


def stipendio(g):
    """
    Lo stipendio mensile che il giocatore chiede, in euro. Come in Hattrick lo decide lui, non si
    contratta: cresce di un fattore e ogni SCALA_STIPENDIO punti di valore, sale per i tratti rari,
    ambidestro, gioco rapido e cambio di velocità, e per l'esperienza di carriera.
    """
    euro = STIPENDIO_DI_RIFERIMENTO * math.exp((g.indice_collettivo_valore - VALORE_DI_RIFERIMENTO) / SCALA_STIPENDIO)
    if g.ambidestro:
        euro *= FATTORE_GLORIA_RICHIESTA_AMBIDESTRO
    if g.giocorapido:
        euro *= FATTORE_GLORIA_RICHIESTA_GIOCO_RAPIDO
    if g.cambiovelocita:
        euro *= FATTORE_GLORIA_RICHIESTA_CAMBIO_VEL
    euro *= 1 + AUMENTO_STIPENDIO_PER_ESPERIENZA * g.esperienza
    return max(STIPENDIO_MINIMO, arrotonda(euro))


def stipendio_pagato(g):
    """
    Lo stipendio che la polisportiva paga ogni mese: quello del contratto, fisso fino alla scadenza,
    oppure, per chi non ha contratto, quello che chiede oggi.
    """
    return g.contratto_stipendio if getattr(g, "contratto_stipendio", 0) > 0 else stipendio(g)


def fattore_reputazione(g, poli):
    """
    Quanto la reputazione della polisportiva sposta l'ingaggio chiesto: sotto uno con una
    polisportiva più gloriosa di quanto il giocatore pretende, sopra uno con una meno gloriosa.
    """
    rapporto = g.gloria_richiesta / max(1, poli.gloria)
    return min(REPUTAZIONE_MASSIMA, max(REPUTAZIONE_MINIMA, math.sqrt(rapporto)))


def ingaggio_richiesto(g, poli):
    """Il premio d'ingaggio, una tantum, che il giocatore chiede alla polisportiva per firmare."""
    return arrotonda(stipendio(g) * MESI_DI_INGAGGIO * fattore_reputazione(g, poli))


def valore_di_mercato_pieno(g):
    """Quanto vale il giocatore sul mercato a contratto lungo: lo stipendio che chiede per sei mesi, arrotondato al centinaio."""
    return arrotonda(stipendio(g) * MESI_DI_VALORE, 100)


def fattore_scadenza(g, oggi=None, col_rinnovo=True):
    """
    Quanto scende il valore di mercato verso la scadenza: 1 per i liberi, per chi ha già un rinnovo
    concordato e per chi ha almeno tre mesi di contratto; sotto, in linea retta fino al 40 per cento
    alla scadenza. Senza la data di oggi, 1. Senza col_rinnovo il rinnovo concordato non conta, e
    vale la scadenza vera: è il valore di una vendita dell'utente, decisione D40, perché chi compra
    firma un contratto nuovo e il rinnovo si annulla.
    """
    if oggi is None or not contratti.ha_contratto(g) or (col_rinnovo and contratti.ha_rinnovo(g)):
        return 1.0
    mesi = contratti.mesi_al_termine(g, oggi)
    if mesi >= MESI_VALORE_PIENO:
        return 1.0
    return VALORE_A_SCADENZA + (1.0 - VALORE_A_SCADENZA) * mesi / MESI_VALORE_PIENO


def valore_di_mercato(g, oggi=None, col_rinnovo=True):
    """
    Quanto vale il giocatore sul mercato delle vendite, il giorno dato: il prezzo di partenza, e il
    metro del computer. È il valore pieno per il fattore della scadenza, arrotondato al centinaio.
    Senza col_rinnovo, per le vendite dell'utente, il rinnovo concordato non lo tiene pieno.
    """
    pieno = valore_di_mercato_pieno(g)
    fattore = fattore_scadenza(g, oggi, col_rinnovo)
    return pieno if fattore >= 1.0 else arrotonda(pieno * fattore, 100)


def tetto_pieno_di_rivendita(g, poli, oggi):
    """
    Il prezzo più alto che il computer paga per un giocatore della polisportiva a rampa finita, in euro interi: il
    valore di mercato del giorno col rialzo del computer. Per l'utente, decisione D40, senza il rinnovo concordato,
    che il compratore annulla; per il computer col rinnovo, il valore che Mondo._vendibili usa, dove però il tetto
    delle sue vendite resta quello di prima, in virgola mobile. Il valore è un multiplo di 100, quindi col rialzo
    del 15% fa un multiplo di 5, e l'arrotondamento toglie soltanto l'errore della virgola mobile: prima, per circa
    metà dei valori, il prodotto cadeva appena sotto, e il computer non pagava il 15% pieno ma un euro di meno.
    """
    return round(valore_di_mercato(g, oggi, poli.is_cpu_controlled) * RIALZO_CPU)


def _rampa(g, poli, oggi, pieno):
    """
    La rampa del prezzo di un tesserato dell'utente, se il tetto non è ancora pieno: la partenza, cioè l'ingaggio che
    il giocatore chiede alla polisportiva, i giorni passati dalla firma, quelli dalla firma al tetto pieno e il giorno
    del tetto pieno. None quando il tetto è già pieno: polisportiva del computer, firma prima del formato 11 senza il
    giorno, partenza che non sta sotto il tetto pieno, e dal giorno del tetto pieno in poi.
    """
    if poli.is_cpu_controlled or g.tesserato_dal is None:
        return None
    partenza = ingaggio_richiesto(g, poli)
    if partenza >= pieno:
        return None
    fine = contratti.stesso_giorno_dopo(g.tesserato_dal, MESI_DELLA_RAMPA)
    giorni = (fine.date() - g.tesserato_dal.date()).days
    passati = max(0, (oggi.date() - g.tesserato_dal.date()).days)
    if passati >= giorni:
        return None
    return partenza, passati, giorni, fine


def tetto_di_rivendita(g, poli, oggi):
    """
    Il prezzo più alto che il computer paga oggi per un giocatore della polisportiva, in euro interi: il computer lo
    compra soltanto a un prezzo che non lo supera. Decisione D40, scelta di Gabriele del 3 novembre 2026, per un
    tesserato dell'utente: il giorno della firma con la polisportiva di oggi il tetto è l'ingaggio che il giocatore le
    chiede, cioè circa quello che è costato, e sale in linea retta, giorno per giorno, fino al tetto pieno di oggi,
    tetto_pieno_di_rivendita, lo stesso giorno del mese MESI_DELLA_RAMPA mesi dopo la firma. Se la partenza non sta
    sotto il tetto pieno vale il tetto pieno, e così per chi ha firmato prima del formato 11, senza il giorno della
    firma. Per le polisportive del computer è il tetto pieno, senza rampa: Mondo._vendibili non lo usa per loro, e
    le loro vendite restano quelle di prima.
    """
    pieno = tetto_pieno_di_rivendita(g, poli, oggi)
    rampa = _rampa(g, poli, oggi, pieno)
    if rampa is None:
        return pieno
    partenza, passati, giorni, _fine = rampa
    return partenza + (pieno - partenza) * passati // giorni


def rivendita_piena_dal(g, poli, oggi):
    """
    Il giorno dal quale il computer paga il tetto pieno per un tesserato dell'utente, decisione D40: lo stesso giorno del
    mese MESI_DELLA_RAMPA mesi dopo la firma. None se il tetto è già pieno oggi, come dice tetto_di_rivendita.
    """
    rampa = _rampa(g, poli, oggi, tetto_pieno_di_rivendita(g, poli, oggi))
    return None if rampa is None else rampa[3]


def rivendita_al_prezzo_dal(g, poli, prezzo, oggi):
    """
    Il giorno dal quale il tetto di tetto_di_rivendita arriva al prezzo dato, coi valori di oggi: oggi se ci arriva già,
    None se il prezzo supera il tetto pieno, e allora il computer, col valore di oggi, non lo compra. Il giorno è il primo
    in cui la retta della rampa tocca il prezzo, contato coi numeri interi, come il tetto.
    """
    pieno = tetto_pieno_di_rivendita(g, poli, oggi)
    if prezzo > pieno:
        return None
    rampa = _rampa(g, poli, oggi, pieno)
    if rampa is None:
        return oggi
    partenza, passati, giorni, _fine = rampa
    salita = pieno - partenza
    # Il primo giorno n dalla firma in cui partenza + salita * n // giorni arriva al prezzo.
    n = max(passati, -(-(prezzo - partenza) * giorni // salita))
    return oggi if n == passati else g.tesserato_dal + datetime.timedelta(days=n)


def sponsor_mensile(poli, rosa):
    """
    Quanto lo sponsor paga ogni mese alla polisportiva: dalla tappa 11 metà per la gloria e metà
    per il valore della rosa, cioè una quota del valore di mercato pieno dei tesserati in attività.
    La rosa la passa chi chiama, con i tesserati vivi: è il guadagno di chi allena di D31, perché
    durante il contratto lo stipendio è fisso e lo sponsor cresce col valore.
    Dalla decisione D40, nelle polisportive dell'utente la parte della gloria si paga per i tesserati in
    attività sul massimo dei posti, quota_della_gloria; il computer non cambia. Tutte le cifre dello
    sponsor, nei conti del mese, nella barra, nella scheda e nei bilanci, passano di qui.
    """
    valore_della_rosa = sum(valore_di_mercato_pieno(g) for g in rosa if not g.ritirato)
    gloria = poli.gloria * SPONSOR_PER_GLORIA
    if not poli.is_cpu_controlled:
        gloria *= quota_della_gloria(rosa)
    return arrotonda(gloria + QUOTA_SPONSOR_SUL_VALORE * valore_della_rosa)


def tesserati_in_attivita(rosa):
    """Quanti tesserati della rosa sono in attività, cioè non ritirati, fino al massimo dei posti: quelli che lo sponsor dell'utente paga nella gloria."""
    return min(MAX_TESSERATI_POLISPORTIVA, sum(1 for g in rosa if not g.ritirato))


def quota_della_gloria(rosa):
    """La parte della gloria che lo sponsor paga a una polisportiva dell'utente, decisione D40: i tesserati in attività sul massimo dei posti."""
    return tesserati_in_attivita(rosa) / MAX_TESSERATI_POLISPORTIVA


def gloria_di_un_posto(poli):
    """Quanto costa al mese un posto vuoto nello sponsor di una polisportiva dell'utente: la parte della gloria divisa per i posti, arrotondata alla decina."""
    return arrotonda(poli.gloria * SPONSOR_PER_GLORIA / MAX_TESSERATI_POLISPORTIVA)


def premio_cassa_piena(cassa):
    """
    Quanto in più al mese si permette una polisportiva del computer con la cassa piena, decisione 1 di
    Gabriele del 14 ottobre 2026: la cassa oltre SOGLIA_CASSA_PIENA_CPU divisa per i mesi in cui conta di
    spenderla, MESI_CASSA_PIENA_CPU; zero sotto la soglia. Si aggiunge agli stipendi che il computer si
    permette nei tesseramenti, negli scambi, negli acquisti e nei rinnovi, non al prezzo.
    """
    return max(0.0, cassa - SOGLIA_CASSA_PIENA_CPU) / MESI_CASSA_PIENA_CPU


def spesa_mensile_cpu(sponsor, cassa):
    """
    Il monte stipendi che una polisportiva del computer si permette ogni mese: lo sponsor, un
    ventiquattresimo della cassa e, con la cassa piena, il suo premio. Sotto la soglia il premio è zero,
    e il conto è quello di prima fino all'ultimo bit.
    """
    return sponsor + cassa / PARTI_DI_CASSA_PER_STIPENDI + premio_cassa_piena(cassa)


def mesi_di_pazienza(g):
    """Per quanti mesi senza stipendio il giocatore aspetta, secondo la fedeltà: da uno a cinque."""
    return 1 + g.fedelta / FEDELTA_PER_MESE_DI_PAZIENZA


def bandiera_attiva(g):
    """Vero per una bandiera che ha già dato abbastanza al suo club: gioca anche senza stipendio."""
    return g.bandiera and g.fedelta >= FEDELTA_BANDIERA


def pazienza_per_euro(g):
    """Quanta pazienza rende o toglie un euro di stipendio: un mese intero, quello del contratto, vale un mese di pazienza."""
    return 100 / mesi_di_pazienza(g) / max(1, stipendio_pagato(g))


def mesi_rimasti(g):
    """Per quanti mesi ancora il giocatore aspetterebbe senza stipendio, con la pazienza di adesso."""
    return g.pazienza / (100 / mesi_di_pazienza(g))
