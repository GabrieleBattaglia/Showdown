"""
I testi che MESS mostra nella finestra: schede, elenchi, classifiche, statistiche, ricerche, la
barra di stato, l'apertura e la chiusura.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 5 del piano. Sono funzioni pure: ricevono il mondo e
restituiscono testo, senza wx, così si collaudano da sole. Seguono le regole di accessibilità del
parco: frasi intere, nessun separatore grafico, nessuna riga vuota, e righe da quaranta caratteri
soltanto nella barra di stato, scritta a codici come in meditimer.
Le schede del giocatore e della polisportiva seguono la scheda del mostro di Terminal Beast,
secondo la decisione D10: una riga d'intestazione con i dati principali separati dalla barra
verticale, poi i blocchi annunciati da un'etichetta fra parentesi quadre, le caratteristiche due
per riga con l'aggettivo alla Hattrick e il valore fra parentesi, le classifiche con posizione e
percentuale.
Dalla tappa 9, il 2026-10-07, la scheda dice il carattere del giocatore a parole e accordato, mai
col numero, e la sede dell'infortunio; la cronaca di un incontro, presa dagli eventi del motore, si
divide in testi da mostrare un punto alla volta, ciascuno aperto dal punteggio, come vuole la
decisione D17. Le parti nuove sono di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Dal 2026-10-08 ci sono i testi dell'amichevole della finestra: il risultato, aperto da chi vince,
la cronaca salvata, e il perché quando oggi nessuno può giocare. Con la decisione D29 il punto per
punto con F8 lascia il posto alla partita dal vivo, che ha qui la guida del suo campo di testo e la
cronaca di ogni tranche, ancora aperta dal punteggio come vuole D17.
"""

import datetime

import economia
import infortuni
import mercato
import version
from archivio import NATO
from costanti import (
    ANNO_SIMULAZIONE_GIORNI,
    ATTRIBUTI_BASE_CON_ALLENABILI,
    CARATTERISTICHE_ATTACCO_BASE,
    CARATTERISTICHE_CONTROLLO_BASE,
    CARATTERISTICHE_DIFESA_BASE,
    CARATTERISTICHE_FISICHE_BASE,
    ESPERIENZA_MASSIMA,
    FASCE_TEMPERAMENTO,
    INDOLI,
    LIMITE_MOVIMENTI_PER_TICK,
    MAX_TOTALE_PRECISIONE_RESISTENZA,
    MAX_TOTALE_SKILL_GIOCO,
    NOME_ATTR_TO_DISPLAY_MAP,
)
from motore import cronaca
from utilita import MESI, converti_giorni_sim, data_breve, formatta_eta_sim, in_ora_locale
from utilita import accorda as accorda_sesso

# La scala degli aggettivi delle schede di Terminal Beast, da 0 a 20.
AGGETTIVI = ("Inesistente", "Disastroso", "Tremendo", "Scarso", "Debole", "Insufficiente", "Accettabile", "Buono", "Eccellente", "Formidabile",
             "Straordinario", "Splendido", "Magnifico", "Fuoriclasse", "Sovrannaturale", "Titanico", "Extraterrestre", "Mitico", "Magico", "Utopico", "Divino")
GRUPPI = (("CARATTERISTICHE FISICHE", CARATTERISTICHE_FISICHE_BASE), ("DIFESA", CARATTERISTICHE_DIFESA_BASE),
          ("ATTACCO", CARATTERISTICHE_ATTACCO_BASE), ("POLIVALENTI", CARATTERISTICHE_CONTROLLO_BASE))
LARGHEZZA_BARRA = 40
LEGENDA_BARRA = (
    "La barra di stato ha quattro righe, ciascuna entro quaranta caratteri, scritte a codici: una lettera e un numero. "
    "Prima riga, il tempo: s è la data simulata, a il tempo che manca al prossimo avanzamento del mondo. "
    "Seconda riga, la polisportiva attiva: prima il nome, poi g la gloria, t i tesserati sul massimo, m le mosse di mercato rimaste oggi, c la cassa in migliaia di euro. "
    "Terza riga, la popolazione: l i giocatori liberi, t i tesserati, f quelli fermi perché ritirati o infortunati, n il totale, p le polisportive. "
    "Quarta riga, a parole, l'ultima cosa successa."
)


# Numeri, date e parole.

def numero(valore, decimali=1):
    """Un numero all'italiana: virgola per i decimali, punto per le migliaia."""
    testo = f"{valore:,.{decimali}f}"
    return testo.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def intero(valore):
    return f"{int(valore):,}".replace(",", ".")


def conta(n, singolare, plurale):
    """Il numero con il nome al singolare o al plurale."""
    return f"{n} {singolare if n == 1 else plurale}"


def unisci(parti):
    """Un elenco a parole: a, b e c."""
    parti = [p for p in parti if p]
    if not parti:
        return ""
    if len(parti) == 1:
        return parti[0]
    return ", ".join(parti[:-1]) + " e " + parti[-1]


def data_lunga(dt):
    """Una data con l'ora, a parole: 7 ottobre 2026 alle 18:39."""
    return f"{dt.day} {MESI[dt.month - 1]} {dt.year} alle {dt:%H:%M}"


def durata(intervallo):
    """Una durata a parole, in giorni, ore e minuti: 1 giorno, 3 ore e 5 minuti."""
    minuti = int(intervallo.total_seconds() // 60)
    if minuti < 1:
        return "meno di un minuto"
    giorni, minuti = divmod(minuti, 24 * 60)
    ore, minuti = divmod(minuti, 60)
    return unisci([conta(giorni, "giorno", "giorni") if giorni else "", conta(ore, "ora", "ore") if ore else "", conta(minuti, "minuto", "minuti") if minuti else ""])


def accorda(g, maschile):
    """Una parola che finisce in o, al maschile o al femminile secondo il giocatore: libero, libera."""
    return accorda_sesso(g.sesso, maschile)


def nome_completo(g):
    return f"{g.nome} {g.cognome}"


def anni(g):
    return int(g.eta_anni)


def indole(g):
    """L'indole del giocatore a parole, come da muro o di rimessa."""
    return INDOLI[g.indole]["nome"]


def punti(valore):
    """Una quantità di punti allenamento: senza decimali quando è intera, altrimenti con uno, 38,5."""
    arrotondato = round(valore, 1)
    return intero(arrotondato) if arrotondato == int(arrotondato) else numero(arrotondato)


def nome_caratteristica(nome_base):
    return NOME_ATTR_TO_DISPLAY_MAP[nome_base].capitalize()


def aggettivo(valore, massimo):
    """L'aggettivo della scala di Terminal Beast per un valore che va da 0 a massimo."""
    return AGGETTIVI[max(0, min(20, int(valore * 20 / massimo)))]


def valore_caratteristica(g, nome_base):
    """Una caratteristica come nelle schede di Terminal Beast: Lungolinea destro: Buono (14,6)."""
    massimo = MAX_TOTALE_PRECISIONE_RESISTENZA if nome_base in CARATTERISTICHE_FISICHE_BASE else MAX_TOTALE_SKILL_GIOCO
    valore = g._get_valore_totale(nome_base)
    return f"{nome_caratteristica(nome_base)}: {aggettivo(valore, massimo)} ({numero(valore)})"


def eta_polisportiva(p, mondo):
    """Da quanto esiste una polisportiva, in anni, mesi e giorni del simulatore: meno di un giorno, se è appena nata."""
    giorni = int((mondo.datetime_corrente_simulazione - p.datetime_creazione_sim).total_seconds() // 86400)
    a, m, g = converti_giorni_sim(max(0, giorni), per_eta=True)
    return unisci([conta(a, "anno", "anni") if a else "", conta(m, "mese", "mesi") if m else "", conta(g, "giorno", "giorni") if g else ""]) or "meno di un giorno"


def percentuale_classifica(posizione, totale):
    """La percentuale di chi sta dietro, posizione compresa, come nelle classifiche di Terminal Beast."""
    if totale <= 1:
        return 100.0
    return round((totale - posizione + 1) / totale * 100, 1)


# Il giocatore.

def attivi(mondo):
    """I giocatori in attività: vivi e non ritirati."""
    morti = mondo._ids_morti_processati_sessione
    return [g for gid, g in mondo.giocatori.items() if gid not in morti and not g.ritirato]


def stato(g, mondo):
    """Lo stato del giocatore a parole: libero, tesserato con, ritirato, uscito di scena."""
    if g.id in mondo._ids_morti_processati_sessione:
        testo = accorda(g, "uscito") + " di scena"
    elif g.ritirato:
        testo = accorda(g, "ritirato")
    elif g.appartenenza == "*":
        testo = accorda(g, "libero")
    else:
        testo = f"{accorda(g, 'tesserato')} con {g.appartenenza}"
    if g.infortunato and g.infortunio_fine_datetime:
        testo += f", {infortunio(g)}"
    return testo


def infortunio(g):
    """L'infortunio a parole, con la sede se si sa: infortunata al polso destro fino al 3 marzo 2026 alle 9:00."""
    dove = infortuni.frase_sede(g.infortunio_sede)
    testo = accorda(g, "infortunato") + (f" {dove}" if dove else "")
    testo += f" fino al {data_lunga(g.infortunio_fine_datetime)}"
    if infortuni.gioca_con_l_altro_braccio(g, g.infortunio_sede):
        testo += ", ma gioca con l'altro braccio"
    return testo


def carattere(g):
    """Il temperamento di oggi a parole e accordato, con le fasce di costanti.py: focoso, focosa."""
    attuale = g.temperamento_attuale
    for limite, parola, compreso in FASCE_TEMPERAMENTO:
        if limite is None or attuale < limite or (compreso and attuale == limite):
            return accorda(g, parola)
    return accorda(g, FASCE_TEMPERAMENTO[-1][1])


def riga_giocatore(g, mondo):
    """Il giocatore in una riga degli elenchi."""
    return f"{g.id}. {nome_completo(g)}, {'uomo' if g.sesso == 'm' else 'donna'}, {anni(g)} anni, valore {numero(g.indice_collettivo_valore)}, {stato(g, mondo)}"


def tratti_speciali(g):
    tratti = []
    if g.mancino:
        tratti.append(accorda(g, "mancino"))
    if g.ambidestro:
        tratti.append(accorda(g, "ambidestro"))
    if g.giocorapido:
        tratti.append("gioco rapido")
    if g.cambiovelocita:
        tratti.append("cambio di velocità")
    if g.ipovedente:
        tratti.append("ipovedente")
    return tratti


def _classifiche(g, mondo):
    """Le tre classifiche di Terminal Beast adattate: generale, del proprio sesso, della propria indole."""
    in_attivita = sorted(attivi(mondo), key=lambda x: x.indice_collettivo_valore, reverse=True)
    if g not in in_attivita:
        return []
    righe = []
    for titolo, gruppo in (("Classifica generale", in_attivita),
                           ("Classifica maschile" if g.sesso == "m" else "Classifica femminile", [x for x in in_attivita if x.sesso == g.sesso]),
                           (f"Classifica d'indole ({indole(g)})", [x for x in in_attivita if x.indole == g.indole])):
        posizione = gruppo.index(g) + 1
        righe.append(f"{titolo}: {posizione}° ({numero(percentuale_classifica(posizione, len(gruppo)))}%) su {len(gruppo)}")
    return righe


def scheda_giocatore(g, mondo):
    """La scheda completa di un giocatore, sul modello della scheda del mostro di Terminal Beast."""
    g.aggiorna_aspetto()
    if g.id in mondo._ids_morti_processati_sessione:
        etichetta = accorda(g, "uscito").upper() + " DI SCENA"
    elif g.ritirato:
        etichetta = accorda(g, "ritirato").upper()
    elif g.appartenenza == "*":
        etichetta = accorda(g, "libero").upper()
    else:
        etichetta = g.appartenenza
    righe = [
        f"[{etichetta}] ID: {g.id} | {nome_completo(g)} | {'Uomo' if g.sesso == 'm' else 'Donna'}, {anni(g)} anni | Valore: {numero(g.indice_collettivo_valore)}",
        f"Descrizione: {g.descrizione_fisica}",
        f"Fisico: {g.altezza} cm e {g.peso} kg | Indole: {indole(g)} | Punti allenamento: {punti(g.punti_allenamento)} | Gloria richiesta: {intero(g.gloria_richiesta)}",
    ]
    tratti = f"Tratti: {unisci(tratti_speciali(g)) or 'nessuno in particolare'} | Carattere: {carattere(g)}"
    if g.infortunato and g.infortunio_fine_datetime:
        testo = infortunio(g)
        tratti += f" | {testo[0].upper()}{testo[1:]}"
    righe.append(tratti)
    righe.extend(_economia_del_giocatore(g, mondo))
    for titolo, gruppo in GRUPPI:
        righe.append(f"[{titolo}]")
        valori = [valore_caratteristica(g, nome) for nome in gruppo]
        righe.extend(" | ".join(valori[i:i + 2]) for i in range(0, len(valori), 2))
    partite = g.partitevinte + g.partiteperse
    set_giocati = g.setsvinti + g.setspersi
    righe.append("[CARRIERA]")
    righe.append(f"Partite: {partite} (V:{g.partitevinte} - S:{g.partiteperse}) | Vittorie: {numero(g.partitevinte * 100 / partite if partite else 0)}%")
    righe.append(f"Set: {set_giocati} (V:{g.setsvinti} - S:{g.setspersi}) | Goal fatti: {g.goalsfatti} | Goal subiti: {g.goalssubiti}")
    if any((g.ori, g.argenti, g.bronzi, g.legni)):
        righe.append(f"MEDAGLIERE: Oro:{g.ori} | Argento:{g.argenti} | Bronzo:{g.bronzi} | Legno:{g.legni}")
    righe.extend(_classifiche(g, mondo))
    al_compleanno = ANNO_SIMULAZIONE_GIORNI - g.eta % ANNO_SIMULAZIONE_GIORNI
    righe.append(f"Età: {formatta_eta_sim(g.eta)} simulati | Prossimo compleanno fra {conta(al_compleanno, 'giorno', 'giorni')}")
    righe.append(f"Scoperto il {data_lunga(g.datetime_creazione_sim)} nel mondo simulato e il {data_lunga(g.datacreazione_reale)} nel mondo reale, con la versione {g.versione}.")
    return "\n".join(righe)


def euro(importo):
    return economia.scritta_in_euro(importo)


def umore(g):
    """L'umore di un tesserato, dalla pazienza che gli resta quando aspetta degli arretrati."""
    if not g.arretrati:
        return "sereno"
    if economia.bandiera_attiva(g):
        return "paziente, da bandiera"
    if g.pazienza >= 75:
        return "un po' preoccupato" if g.sesso == "m" else "un po' preoccupata"
    if g.pazienza >= 50:
        return accorda(g, "preoccupato")
    if g.pazienza >= 25:
        return "insofferente"
    return "pronto ad andarsene" if g.sesso == "m" else "pronta ad andarsene"


def attesa(g):
    """Cosa aspetta un tesserato non pagato, e per quanto ancora pazienterà."""
    if economia.bandiera_attiva(g):
        return f"aspetta {euro(g.arretrati)} di stipendi arretrati, ma da bandiera non se ne andrà"
    mesi = economia.mesi_rimasti(g)
    quanto = "meno di un mese" if mesi < 1 else f"circa {conta(round(mesi), 'mese', 'mesi')}"
    return f"aspetta {euro(g.arretrati)} di stipendi arretrati, e pazienterà ancora {quanto}"


def _economia_del_giocatore(g, mondo):
    """Le righe dell'economia nella scheda: stipendio, valore, esperienza e, per un tesserato, fedeltà e umore."""
    righe = [f"Stipendio: {euro(economia.stipendio(g))} al mese | Valore di mercato: {euro(economia.valore_di_mercato(g))} | "
             f"Esperienza di carriera: {aggettivo(g.esperienza, ESPERIENZA_MASSIMA)} ({numero(g.esperienza)})"]
    club = mondo.polisportive.get(g.appartenenza)
    if club is not None:
        riga = f"Fedeltà a {club.nome}: {numero(g.fedelta, 0)} su 100 | Umore: {umore(g)}"
        if g.arretrati:
            riga += f", {attesa(g)}"
        righe.append(riga)
        if economia.bandiera_attiva(g):
            righe.append(f"Bandiera di {club.nome}: gioca per il club anche senza stipendio.")
        if g.id in club.in_vendita:
            righe.append(f"In vendita a {euro(club.in_vendita[g.id])}.")
    return righe


def elenco_giocatori(mondo):
    giocatori = sorted(mondo.giocatori.values(), key=lambda g: g.id)
    if not giocatori:
        return "Il mondo non ha ancora giocatori."
    righe = [f"Elenco dei giocatori: {len(giocatori)} in tutto, dal numero {giocatori[0].id} al {giocatori[-1].id}."]
    righe.extend(riga_giocatore(g, mondo) for g in giocatori)
    return "\n".join(righe)


def _club(g):
    return accorda(g, "libero") if g.appartenenza == "*" else g.appartenenza


def classifica(mondo):
    ordinati = sorted(attivi(mondo), key=lambda g: g.indice_collettivo_valore, reverse=True)
    if not ordinati:
        return "Nessun giocatore in attività."
    righe = [f"Classifica per valore dei {len(ordinati)} giocatori in attività."]
    righe.extend(f"{i}. {nome_completo(g)} (ID {g.id}), valore {numero(g.indice_collettivo_valore)}, {anni(g)} anni, {indole(g)}, {_club(g)}"
                 for i, g in enumerate(ordinati, 1))
    return "\n".join(righe)


def top_10(mondo):
    righe = []
    migliori = sorted(attivi(mondo), key=lambda g: g.indice_collettivo_valore, reverse=True)[:10]
    if migliori:
        righe.append("I dieci giocatori di maggior valore:")
        righe.extend(f"{i}. {nome_completo(g)} (ID {g.id}), valore {numero(g.indice_collettivo_valore)}, {anni(g)} anni, {_club(g)}" for i, g in enumerate(migliori, 1))
    else:
        righe.append("Nessun giocatore in attività.")
    poli = sorted(mondo.polisportive.values(), key=lambda p: p.indicecollettivotesserati, reverse=True)[:10]
    if poli:
        righe.append("Le dieci polisportive di maggior valore collettivo:")
        righe.extend(f"{i}. {p.nome}{' (computer)' if p.is_cpu_controlled else ''}, valore {numero(p.indicecollettivotesserati)}, "
                     f"{len(p.tesserati)} tesserati su {p.maxtesserati}, fondata da {eta_polisportiva(p, mondo)}"
                     for i, p in enumerate(poli, 1))
    else:
        righe.append("Non esiste ancora nessuna polisportiva.")
    return "\n".join(righe)


def statistiche(mondo):
    gruppo = attivi(mondo)
    if not gruppo:
        return "Nessun giocatore in attività: non ci sono statistiche da fare."
    n = len(gruppo)

    def per_cento(parte):
        return numero(parte * 100 / n)

    uomini = [g for g in gruppo if g.sesso == "m"]
    donne = [g for g in gruppo if g.sesso == "f"]
    tesserati = sum(1 for g in gruppo if g.appartenenza != "*")
    ipovedenti = sum(1 for g in gruppo if g.ipovedente)

    def eta_media(lista):
        return numero(sum(g.eta_anni for g in lista) / len(lista)) if lista else "nessuna"

    righe = [
        f"Giocatori in attività: {n}, di cui {len(uomini)} uomini ({per_cento(len(uomini))}%) e {len(donne)} donne ({per_cento(len(donne))}%).",
        f"Età media {eta_media(gruppo)} anni: {eta_media(uomini)} per gli uomini e {eta_media(donne)} per le donne.",
        f"Tesserati {tesserati} ({per_cento(tesserati)}%), liberi {n - tesserati} ({per_cento(n - tesserati)}%).",
        f"Valore medio {numero(sum(g.indice_collettivo_valore for g in gruppo) / n)}. Ipovedenti {ipovedenti} ({per_cento(ipovedenti)}%).",
        f"Nomi diversi {len({g.nome for g in gruppo})}, cognomi diversi {len({g.cognome for g in gruppo})}.",
        "[MIGLIORI PER CARATTERISTICA]",
    ]
    for nome_base in ATTRIBUTI_BASE_CON_ALLENABILI:
        migliore = max(gruppo, key=lambda g, nb=nome_base: g._get_valore_totale(nb))
        righe.append(f"{valore_caratteristica(migliore, nome_base)}, {nome_completo(migliore)} (ID {migliore.id}), {anni(migliore)} anni, {_club(migliore)}")
    if mondo.polisportive:
        prima = max(mondo.polisportive.values(), key=lambda p: p.indicecollettivotesserati)
        righe.append(f"La polisportiva di maggior valore collettivo è {prima.nome}, con {numero(prima.indicecollettivotesserati)}.")
    return "\n".join(righe)


# Le liste della sessione e la ricerca.

def lista_nuovi(mondo):
    nuovi = [mondo.giocatori[gid] for gid in mondo.nuovi_giocatori_sessione if gid in mondo.giocatori]
    if not nuovi:
        return "In questa sessione non è arrivato nessun giocatore nuovo."
    righe = [f"Nuovi arrivati della sessione: {len(nuovi)}."]
    righe.extend(riga_giocatore(g, mondo) for g in sorted(nuovi, key=lambda g: g.id))
    return "\n".join(righe)


def lista_ritirati(mondo):
    voci = [(gid, mondo.giocatori[gid]) for gid, _testo in mondo.giocatori_ritirati_sessione if gid in mondo.giocatori]
    if not voci:
        return "In questa sessione non si è ritirato nessuno."
    righe = [f"Ritirati della sessione: {len(voci)}."]
    righe.extend(f"{nome_completo(g)} (ID {gid}) si è {accorda(g, 'ritirato')} a {anni(g)} anni." for gid, g in voci)
    return "\n".join(righe)


def lista_usciti(mondo):
    voci = [(gid, testo, mondo.giocatori[gid]) for gid, testo in mondo.giocatori_morti_sessione if gid in mondo.giocatori]
    if not voci:
        return "In questa sessione non è uscito di scena nessuno."
    righe = [f"Usciti di scena nella sessione: {len(voci)}."]
    for gid, testo, g in voci:
        come = f"è {accorda(g, 'morto')}" if testo.startswith("DECESSO") else "ha lasciato il mondo dello showdown"
        righe.append(f"{nome_completo(g)} (ID {gid}) {come} a {anni(g)} anni.")
    return "\n".join(righe)


def risultati_ricerca(mondo, descrizione, ids):
    righe = [f"Ricerca fra {descrizione}: {conta(len(ids), 'giocatore trovato', 'giocatori trovati')}."]
    righe.extend(riga_giocatore(mondo.giocatori[gid], mondo) for gid in ids if gid in mondo.giocatori)
    return "\n".join(righe)


# Le polisportive.

def scheda_polisportiva(p, mondo):
    """La scheda di una polisportiva, nello stile delle schede di Terminal Beast."""
    righe = [f"[{'COMPUTER' if p.is_cpu_controlled else 'TUA'}] {p.nome} | Gloria: {p.gloria} | Tesserati: {len(p.tesserati)} su {p.maxtesserati} | Valore collettivo: {numero(p.indicecollettivotesserati)}"]
    righe.append(f"Fondata il {data_lunga(p.datetime_creazione_sim)} nel mondo simulato, {eta_polisportiva(p, mondo)} fa, e il {data_lunga(p.datacreazione_reale)} nel mondo reale, con la versione {p.versione_creazione}.")
    mosse = f"Mosse di mercato fatte oggi: {p.movimenti_oggi} su {LIMITE_MOVIMENTI_PER_TICK}"
    if not p.is_cpu_controlled:
        mosse += " | Protetta da password" if p.protetta else " | Senza password"
    righe.append(mosse)
    righe.append("[CONTI]")
    arretrati = sum(mondo.giocatori[gid].arretrati for gid in p.tesserati if gid in mondo.giocatori)
    conti = f"Cassa: {euro(p.cassa)} | Sponsor: {euro(economia.sponsor_mensile(p))} al mese | Stipendi: {euro(mondo.monte_stipendi(p))} al mese"
    if arretrati:
        conti += f" | Arretrati da pagare: {euro(arretrati)}"
    righe.append(conti)
    righe.append("[PALMARÈS]")
    if any((p.coppe_oro, p.coppe_argento, p.coppe_bronzo, p.coppe_legno, p.ori, p.argenti, p.bronzi, p.legni)):
        righe.append(f"Coppe: Oro:{p.coppe_oro} | Argento:{p.coppe_argento} | Bronzo:{p.coppe_bronzo} | Legno:{p.coppe_legno}")
        righe.append(f"Medaglie dei tesserati: Oro:{p.ori} | Argento:{p.argenti} | Bronzo:{p.bronzi} | Legno:{p.legni}")
    else:
        righe.append("Nessun trofeo, per ora.")
    righe.append("[TESSERATI]")
    presenti = [mondo.giocatori[gid] for gid in p.tesserati if gid in mondo.giocatori]
    if presenti:
        uomini = sum(1 for g in presenti if g.sesso == "m")
        eta_media = numero(sum(g.eta_anni for g in presenti) / len(presenti))
        ipovedenti = sum(1 for g in presenti if g.ipovedente)
        righe.append(f"{conta(uomini, 'uomo', 'uomini')} e {conta(len(presenti) - uomini, 'donna', 'donne')}, età media {eta_media} anni, {conta(ipovedenti, 'ipovedente', 'ipovedenti')}.")
        for g in sorted(presenti, key=lambda x: x.indice_collettivo_valore, reverse=True):
            riga = f"{nome_completo(g)} (ID {g.id}), {anni(g)} anni, valore {numero(g.indice_collettivo_valore)}, stipendio {euro(economia.stipendio(g))}, {indole(g)}, {stato(g, mondo)}"
            if g.arretrati:
                riga += f", {attesa(g)}"
            if g.id in p.in_vendita:
                riga += f", in vendita a {euro(p.in_vendita[g.id])}"
            righe.append(riga)
    else:
        righe.append("Nessun tesserato.")
    assenti = [gid for gid in p.tesserati if gid not in mondo.giocatori]
    if assenti:
        righe.append(f"Risultano tesserati anche {unisci([str(gid) for gid in assenti])}, che non fanno più parte del mondo.")
    return "\n".join(righe)


def _voci_di_un_mese(conti):
    """Le voci diverse da zero dei conti di un mese, a parole."""
    nomi = (("sponsor", "sponsor"), ("vendite", "vendite"), ("stipendi", "stipendi"), ("arretrati", "arretrati pagati"),
            ("ingaggi", "ingaggi"), ("acquisti", "acquisti"))
    return unisci([f"{nome} {euro(conti[voce])}" for voce, nome in nomi if conti[voce]]) or "nessun movimento"


def bilancio(p, mondo):
    """Il bilancio di una polisportiva: cassa, entrate e uscite di ogni mese, arretrati, vendite e mesi passati."""
    sponsor = economia.sponsor_mensile(p)
    monte = mondo.monte_stipendi(p)
    saldo = sponsor - monte
    righe = [f"Bilancio di {p.nome}: in cassa {euro(p.cassa)}."]
    righe.append(f"Ogni mese entrano {euro(sponsor)} di sponsor ed escono {euro(monte)} di stipendi: "
                 + (f"restano {euro(saldo)}." if saldo >= 0 else f"mancano {euro(-saldo)}."))
    debitori = [mondo.giocatori[gid] for gid in p.tesserati if gid in mondo.giocatori and mondo.giocatori[gid].arretrati]
    if debitori:
        righe.append(f"Arretrati da pagare: {euro(sum(g.arretrati for g in debitori))}, a {conta(len(debitori), 'tesserato', 'tesserati')}.")
        righe.extend(f"{nome_completo(g)}, {umore(g)}, {attesa(g)}." for g in sorted(debitori, key=lambda g: g.pazienza))
    if p.in_vendita:
        righe.append("In vendita: " + unisci([f"{nome_completo(mondo.giocatori[gid])} a {euro(prezzo)}" for gid, prezzo in p.in_vendita.items() if gid in mondo.giocatori]) + ".")
    righe.append(f"Questo mese, finora: {_voci_di_un_mese(p.conti_del_mese)}.")
    if p.bilanci:
        righe.append("I mesi passati, dal più recente:")
        righe.extend(f"{data_breve(voce['data'])}: {_voci_di_un_mese(voce)}; in cassa {euro(voce['cassa'])}." for voce in p.bilanci)
    return "\n".join(righe)


def elenco_polisportive(mondo):
    if not mondo.polisportive:
        return "Non esiste ancora nessuna polisportiva."
    righe = [f"Polisportive del mondo: {len(mondo.polisportive)}."]
    for p in sorted(mondo.polisportive.values(), key=lambda x: x.nome.casefold()):
        chi = "del computer" if p.is_cpu_controlled else "tua"
        righe.append(f"{p.nome}, {chi}, {len(p.tesserati)} tesserati su {p.maxtesserati}, gloria {p.gloria}, valore {numero(p.indicecollettivotesserati)}, fondata da {eta_polisportiva(p, mondo)}")
    return "\n".join(righe)


def tesserati_attiva(mondo):
    p = mondo.miapolisportiva_attiva
    if p is None:
        return "Non hai una polisportiva attiva."
    presenti = [mondo.giocatori[gid] for gid in p.tesserati if gid in mondo.giocatori]
    if not presenti:
        return f"{p.nome} non ha tesserati."
    righe = [f"Tesserati di {p.nome}: {len(presenti)} su {p.maxtesserati}."]
    righe.extend(riga_giocatore(g, mondo) for g in sorted(presenti, key=lambda g: g.id))
    return "\n".join(righe)


# Le polisportive dell'utente e il mercato.

def riga_mia_polisportiva(p, mondo):
    """Una polisportiva dell'utente in una riga della scelta: se è attiva, tesserati, gloria e protezione."""
    parti = [p.nome]
    if p is mondo.miapolisportiva_attiva:
        parti.append("attiva")
    parti.append(f"{len(p.tesserati)} tesserati su {p.maxtesserati}")
    parti.append(f"gloria {p.gloria}")
    if p.protetta:
        parti.append("protetta da password")
    return ", ".join(parti)


def fondata(p, mondo):
    """La fondazione di una polisportiva, raccontata, con la sua scheda."""
    protetta = ", protetta da password" if p.protetta else ""
    attiva = " È la tua polisportiva attiva." if p is mondo.miapolisportiva_attiva else ""
    return f"Hai fondato {p.nome}{protetta}.{attiva}\n{scheda_polisportiva(p, mondo)}"


def info_mercato(p, mondo):
    """Cassa, gloria, posti e mosse di una polisportiva, in una frase: quello che conta al mercato."""
    return f"{p.nome}: cassa {euro(p.cassa)}, gloria {p.gloria}, tesserati {len(p.tesserati)} su {p.maxtesserati}, mosse rimaste {mondo.mosse_rimaste(p)} su {LIMITE_MOVIMENTI_PER_TICK}."


def riga_mercato(c):
    """Un candidato del mercato in una riga: chi è, quanto vale, quanto prende al mese e quanto costa averlo."""
    g = c.giocatore
    if c.tipo == mercato.LIBERO:
        costo = f"chiede {euro(c.costo)} d'ingaggio"
    elif c.tipo == mercato.IN_VENDITA:
        costo = f"in vendita da {c.polisportiva.nome} a {euro(c.costo)}"
    else:
        costo = f"{accorda(g, 'tesserato')} con {c.polisportiva.nome}, valore di mercato {euro(c.costo)}"
    tratti = "".join(", " + t for t in tratti_speciali(g))
    return f"{nome_completo(g)}, {anni(g)} anni, valore {numero(g.indice_collettivo_valore)}, stipendio {euro(c.stipendio)}, {costo}{tratti}, ID {g.id}"


def _mossa(p, mondo):
    mosse = mondo.mosse_rimaste(p)
    return "l'ultima mossa che ti resta oggi" if mosse == 1 else f"una delle {mosse} mosse che ti restano oggi"


def domanda_acquisto(c, p, mondo):
    return (f"Comprare {nome_completo(c.giocatore)} da {c.polisportiva.nome} per {euro(c.costo)}? "
            f"Prende {euro(c.stipendio)} al mese. Userai {_mossa(p, mondo)}.")


def posizione_in_rosa(posto, quanti):
    """Il posto di un giocatore nella sua rosa, dal più forte, a parole."""
    if quanti == 1:
        return "È l'unico della sua rosa"
    if posto == 1:
        return f"È il più forte dei {quanti} della sua rosa"
    return f"È il {posto}° più forte dei {quanti} della sua rosa"


def domanda_offerta_d_acquisto(c, importo, p, mondo):
    posto, quanti = mondo.posizione_in_rosa(c.giocatore)
    return (f"Offrire {euro(importo)} a {c.polisportiva.nome} per {nome_completo(c.giocatore)}? {posizione_in_rosa(posto, quanti)}, "
            f"e prende {euro(c.stipendio)} al mese. Userai {_mossa(p, mondo)}.")


def domanda_ingaggio(c, importo, probabilita, p, mondo):
    return (f"Offrire a {nome_completo(c.giocatore)} un ingaggio di {euro(importo)}, per tesserarsi con {p.nome}? "
            f"Accetta al {numero(probabilita, 0)}%, e poi prende {euro(c.stipendio)} al mese. Userai {_mossa(p, mondo)}.")


def esito_ingaggio(g, p, accetta, importo, probabilita):
    if accetta:
        return f"{nome_completo(g)} ha accettato l'ingaggio di {euro(importo)}: ora è {accorda(g, 'tesserato')} con {p.nome}."
    return f"{nome_completo(g)} ha rifiutato l'ingaggio di {euro(importo)}: accettava al {numero(probabilita, 0)}%."


def esito_acquisto(g, venditore, p, prezzo):
    return f"{nome_completo(g)} è {accorda(g, 'comprato')} da {venditore.nome} per {euro(prezzo)}: ora è {accorda(g, 'tesserato')} con {p.nome}."


def esito_offerta_d_acquisto(g, venditore, p, accettata, importo):
    if accettata:
        return esito_acquisto(g, venditore, p, importo)
    return f"{venditore.nome} ha rifiutato {euro(importo)} per {nome_completo(g)}."


def riepilogo_mercato(p, mondo, esiti):
    """Le operazioni di una visita al mercato, coppie di testo dell'esito e riuscita, con cassa e mosse che restano."""
    if not esiti:
        righe = [f"Mercato di {p.nome}: nessuna offerta."]
    else:
        riuscite = sum(1 for _testo, riuscita in esiti if riuscita)
        righe = [f"Mercato di {p.nome}: {conta(len(esiti), 'offerta', 'offerte')}, {conta(riuscite, 'riuscita', 'riuscite')}."]
        righe.extend(testo for testo, _riuscita in esiti)
    righe.append(info_mercato(p, mondo))
    return "\n".join(righe)


def riga_arretrati(g):
    """Un tesserato che aspetta arretrati, in una riga della finestra dei pagamenti."""
    return f"{nome_completo(g)}, {umore(g)}, {attesa(g)}; prende {euro(economia.stipendio(g))} al mese"


def riga_vendita(g, p):
    """Un tesserato nella finestra delle vendite: quanto vale, e se è già in vendita."""
    riga = f"{nome_completo(g)}, valore {numero(g.indice_collettivo_valore)}, stipendio {euro(economia.stipendio(g))}, valore di mercato {euro(economia.valore_di_mercato(g))}"
    return riga + (f", in vendita a {euro(p.in_vendita[g.id])}" if g.id in p.in_vendita else "")


def svincolato(g, p, mondo):
    return f"{nome_completo(g)} è {accorda(g, 'svincolato')} da {p.nome} e torna {accorda(g, 'libero')}. {info_mercato(p, mondo)}"


def domanda_chiusura(p):
    if not p.tesserati:
        return f"Chiudere per sempre {p.nome}? Non si torna indietro."
    tesserati = conta(len(p.tesserati), "tesserato tornerà libero", "tesserati torneranno liberi")
    return f"Chiudere per sempre {p.nome}? I suoi {tesserati}, e non si torna indietro." if len(p.tesserati) > 1 else f"Chiudere per sempre {p.nome}? Il suo unico tesserato tornerà libero, e non si torna indietro."


def chiusa(nome, liberati):
    tesserati = f": {conta(liberati, 'giocatore torna libero', 'giocatori tornano liberi')}" if liberati else ", senza tesserati"
    return f"{nome} ha chiuso per sempre{tesserati}. Non hai più una polisportiva attiva: fondane una con Ctrl+N, o scegline un'altra con Ctrl+Maiusc+C."


def password_cambiata(p):
    return f"{p.nome} ora è protetta da password." if p.protetta else f"{p.nome} non è protetta da password."


# Il tempo del mondo.

def data_e_avanzamento(mondo, ora):
    """La data simulata e il prossimo avanzamento; ora è l'istante attuale in UTC."""
    prossimo = mondo.prossimo_avanzamento()
    righe = [f"Data simulata: {data_lunga(mondo.datetime_corrente_simulazione)}."]
    if prossimo > ora:
        righe.append(f"Il prossimo avanzamento, di un giorno simulato, è previsto per il {data_lunga(in_ora_locale(prossimo))}, fra {durata(prossimo - ora)}.")
    else:
        righe.append("Un avanzamento è maturato in questo momento: il mondo lo farà entro un minuto.")
    righe.append(f"Nel mondo passa un giorno ogni 8 ore reali, anche a programma chiuso e a finestra aperta; un anno simulato dura {ANNO_SIMULAZIONE_GIORNI} giorni.")
    return "\n".join(righe)


def _fatti_avanzamento(rapporto):
    """Le cose successe in un avanzamento, a parole, una frase per gruppo."""
    persone = unisci([
        f"{conta(rapporto['nuovi'], 'giocatore è nato', 'giocatori sono nati')}" if rapporto["nuovi"] else "",
        f"{conta(rapporto['ritirati'], 'si è ritirato', 'si sono ritirati')}" if rapporto["ritirati"] else "",
        f"{conta(rapporto['morti'], 'è morto', 'sono morti')}" if rapporto["morti"] else "",
        f"{conta(rapporto['usciti'], 'ha lasciato', 'hanno lasciato')} il mondo dello showdown" if rapporto["usciti"] else "",
        f"{conta(rapporto['guariti'], 'è guarito', 'sono guariti')}" if rapporto["guariti"] else "",
        conta(rapporto["autoallenati"], "si è allenato da solo", "si sono allenati da soli") if rapporto["autoallenati"] else "",
    ])
    mercato = unisci([
        f"hanno tesserato {conta(rapporto['tesserati_cpu'], 'giocatore', 'giocatori')}" if rapporto["tesserati_cpu"] else "",
        f"ne hanno svincolati {rapporto['svincolati_cpu']} per fare posto" if rapporto["tesserati_cpu"] and rapporto["svincolati_cpu"] else "",
        f"ne hanno comprati {rapporto['vendite']}" if rapporto["vendite"] else "",
        f"ne hanno persi {rapporto['partiti']} che non pagavano" if rapporto["partiti"] > rapporto["tuoi_partiti"] else "",
    ])
    nascite = unisci([
        ("è nata una polisportiva del computer" if rapporto["poli_create"] == 1 else f"sono nate {rapporto['poli_create']} polisportive del computer") if rapporto["poli_create"] else "",
        ("una polisportiva del computer ha chiuso" if rapporto["poli_chiuse"] == 1 else f"{rapporto['poli_chiuse']} polisportive del computer hanno chiuso") if rapporto["poli_chiuse"] else "",
    ])
    frasi = []
    tuoi = unisci([
        conta(rapporto["tuoi_non_pagati"], "tuo tesserato aspetta lo stipendio", "tuoi tesserati aspettano lo stipendio") if rapporto["tuoi_non_pagati"] else "",
        conta(rapporto["tuoi_partiti"], "tuo tesserato se n'è andato senza stipendio", "tuoi tesserati se ne sono andati senza stipendio") if rapporto["tuoi_partiti"] else "",
        conta(rapporto["tuoi_venduti"], "tuo giocatore in vendita è stato comprato", "tuoi giocatori in vendita sono stati comprati") if rapporto["tuoi_venduti"] else "",
    ])
    if tuoi:
        frasi.append(tuoi[0].upper() + tuoi[1:] + ".")
    if persone:
        frasi.append(persone[0].upper() + persone[1:] + ".")
    if mercato:
        frasi.append(f"Le polisportive del computer {mercato}.")
    if nascite:
        frasi.append(nascite[0].upper() + nascite[1:] + ".")
    return " ".join(frasi) or "Non è successo niente di particolare."


def riepilogo_avanzamento(rapporto):
    if not rapporto or not rapporto["ticks"]:
        return "In questa sessione il mondo non è ancora avanzato."
    return f"Ultimo avanzamento, il {data_lunga(rapporto['ora'])}: il mondo è andato avanti di {conta(rapporto['giorni'], 'giorno simulato', 'giorni simulati')}. {_fatti_avanzamento(rapporto)}"


# La barra di stato.

def _entro(testo, larghezza=LARGHEZZA_BARRA):
    return testo[:larghezza]


def righe_barra(mondo, ultimo, ora):
    """Le quattro righe della barra di stato, a codici, ciascuna entro quaranta caratteri."""
    mancano = mondo.prossimo_avanzamento() - ora
    minuti = max(0, int(mancano.total_seconds() // 60))
    tempo = f"s{mondo.datetime_corrente_simulazione:%d/%m/%Y %H:%M} a{minuti // 60}h{minuti % 60:02d}m"
    p = mondo.miapolisportiva_attiva
    if p is None:
        club = "nessuna polisportiva attiva"
    else:
        codici = f" g{p.gloria} t{len(p.tesserati)}/{p.maxtesserati} m{LIMITE_MOVIMENTI_PER_TICK - p.movimenti_oggi} c{p.cassa // 1000}"
        club = p.nome[:LARGHEZZA_BARRA - len(codici)] + codici
    morti = mondo._ids_morti_processati_sessione
    vivi = [g for gid, g in mondo.giocatori.items() if gid not in morti]
    fermi = sum(1 for g in vivi if g.ritirato or g.infortunato)
    tesserati = sum(1 for g in vivi if not g.ritirato and not g.infortunato and g.appartenenza != "*")
    popolazione = f"l{len(vivi) - fermi - tesserati} t{tesserati} f{fermi} n{len(vivi)} p{len(mondo.polisportive)}"
    return [_entro(tempo), _entro(club), _entro(popolazione), _entro(ultimo or "pronto")]


# Diari e vecchie glorie.

def voce_diario(voce):
    """Una voce di diario in una riga: la data simulata e il fatto."""
    if "allenamento" in voce:
        fatto = f"Allenamento di {nome_caratteristica(voce['allenamento']).lower()}, da {numero(voce['da'])} a {numero(voce['a'])}."
    else:
        fatto = voce["testo"]
    return f"{data_breve(voce['data'])}: {fatto}"


def _diario(titolo, diario):
    if not diario:
        return f"{titolo}: nessuna voce."
    righe = [f"{titolo}: {conta(len(diario), 'voce', 'voci')}, dalla più recente."]
    righe.extend(voce_diario(voce) for voce in diario)
    return "\n".join(righe)


def diario_giocatore(g):
    return _diario(f"Diario di {nome_completo(g)}, ID {g.id}", g.diario)


def diario_polisportiva(p):
    return _diario(f"Diario di {p.nome}", p.diario)


def vecchie_glorie(mondo):
    """Il registro di chi è uscito di scena, dal più recente: problema P11, risolto con la tappa 6."""
    if not mondo.vecchie_glorie:
        return "Le vecchie glorie: ancora nessuno è uscito di scena."
    righe = [f"Le vecchie glorie: {conta(len(mondo.vecchie_glorie), 'giocatore uscito', 'giocatori usciti')} di scena, dal più recente."]
    for voce in mondo.vecchie_glorie:
        quando = data_breve(datetime.datetime.fromisoformat(voce["data"]))
        anni_uscita = voce["eta"] // ANNO_SIMULAZIONE_GIORNI
        come = f"è {accorda_sesso(voce['sesso'], 'morto')}" if voce["motivo"] == "morte" else "ha lasciato il mondo dello showdown"
        dove = f"da {accorda_sesso(voce['sesso'], 'tesserato')} con {voce['club']}" if voce["club"] != "*" else f"da {accorda_sesso(voce['sesso'], 'libero')}"
        righe.append(f"{voce['nome']} {voce['cognome']}, ID {voce['id']}, {come} il {quando} a {anni_uscita} anni, {dove}: "
                     f"{conta(voce['partite'], 'partita', 'partite')}, {voce['vittorie']} vinte, valore finale {numero(voce['valore'])}.")
    return "\n".join(righe)


def conservazione(mondo):
    """Per quanto si conservano le voci dei diari, a parole."""
    def per(giorni):
        return "per sempre" if giorni <= 0 else f"per {conta(giorni, 'giorno simulato', 'giorni simulati')}"
    c = mondo.conservazione_diari
    return f"Le voci dei diari dei giocatori si conservano {per(c['giocatori'])}, quelle delle polisportive {per(c['polisportive'])}."


# Apertura, chiusura e aiuto.

def apertura(mondo, origine, messaggi, rapporto, ultimo_prima, ora):
    """
    Il testo dell'apertura: l'intestazione, i messaggi del caricamento, il bentornato con
    l'assenza, ciò che è successo nel frattempo e la polisportiva attiva.
    """
    righe = [version.get_header() + "."]
    righe.extend(messaggi)
    if origine != NATO:
        assenza = ora - ultimo_prima
        righe.append(f"Bentornato! L'ultimo avanzamento del mondo risale al {data_lunga(in_ora_locale(ultimo_prima))}, {durata(assenza)} fa.")
    if rapporto and rapporto["ticks"]:
        righe.append(f"Il mondo è andato avanti di {conta(rapporto['giorni'], 'giorno simulato', 'giorni simulati')}, fino al {data_lunga(mondo.datetime_corrente_simulazione)}. {_fatti_avanzamento(rapporto)}")
    else:
        righe.append(f"Data simulata: {data_lunga(mondo.datetime_corrente_simulazione)}. Il prossimo avanzamento è fra {durata(max(mondo.prossimo_avanzamento() - ora, datetime.timedelta()))}.")
    p = mondo.miapolisportiva_attiva
    if p is None:
        righe.append("Non hai ancora una polisportiva attiva.")
    else:
        righe.append(f"La tua polisportiva attiva è {p.nome}: gloria {p.gloria}, {len(p.tesserati)} tesserati su {p.maxtesserati}.")
    righe.append("Premi F1 per la guida ai comandi.")
    return "\n".join(righe)


def salvataggio_illeggibile(errore):
    """Le frasi che spiegano perché il gioco si ferma quando il salvataggio non si legge."""
    righe = [f"Il salvataggio c'è ma non si può leggere: {errore}."]
    if getattr(errore, "cartella", None):
        righe.append(f"Una copia dei file è nella cartella {errore.cartella}.")
    righe.append("Per non coprirli con un mondo nuovo, il gioco si ferma qui senza salvare nulla.")
    return righe


def somma_rapporti(primo, secondo):
    """Due riepiloghi di avanzamento sommati, con l'ora del secondo: il totale di una sessione."""
    return {chiave: primo[chiave] + secondo[chiave] for chiave in primo if chiave != "ora"} | {"ora": secondo["ora"]}


def chiusura(durata_sessione, comandi, messaggi, rapporto_sessione=None):
    """Il riepilogo della fine sessione, con ciò che è successo nel mondo durante la sessione."""
    righe = [f"Sessione di {durata(durata_sessione)}, con {conta(comandi, 'comando', 'comandi')}."]
    if rapporto_sessione and rapporto_sessione["ticks"]:
        righe.append(f"Nella sessione il mondo è andato avanti di {conta(rapporto_sessione['giorni'], 'giorno simulato', 'giorni simulati')}. {_fatti_avanzamento(rapporto_sessione)}")
    righe.extend(messaggi)
    righe.append("Arrivederci!")
    return "\n".join(righe)


def guida(voci):
    """La guida ai comandi, dalle voci dei menu: coppie di menu e lista di voci con il loro tasto."""
    righe = ["Guida ai comandi di MESS. Ogni comando sta in un menu, e quasi tutti hanno un tasto rapido."]
    for menu, comandi in voci:
        elenco = "; ".join(f"{voce}, {tasto}" if tasto else voce for voce, tasto in comandi)
        righe.append(f"Menu {menu}: {elenco}.")
    righe.append("Con Tab si passa dalla vista principale alla barra di stato e ritorno; F5 porta sulla vista principale, F7 sulla barra di stato.")
    righe.append(GUIDA_DELLA_PARTITA_DAL_VIVO)
    righe.append(LEGENDA_BARRA)
    return "\n".join(righe)


# La partita dal vivo nella guida ai comandi: i suoi tasti non stanno in un menu.
GUIDA_DELLA_PARTITA_DAL_VIVO = (
    "La partita dal vivo si apre scegliendo Assisti nel dialogo dell'amichevole. Lì Invio o spazio sul pulsante Prosegui fanno sentire il gioco "
    "fino al punto seguente, e mentre suona lo mettono in pausa e lo riprendono; Alt+F ascolta fino a fine set, Alt+L passa dalla parte "
    "dell'altro giocatore, Alt+V va alla fine e mostra il risultato, Esc esce senza svelarlo, e a incontro finito porta al risultato; "
    "più e meno cambiano la velocità di gioco; "
    "F1 rimette la guida dei tasti nel campo della cronaca, che si raggiunge con Tab. Time-out, cambio campo e inizio del set non si "
    "sentono: si leggono nella cronaca, e il suono riprende dalla ripresa del gioco.")


def informazioni():
    return "\n".join([
        version.get_header() + ".",
        "MESS è un gioco gestionale dello showdown, il tennistavolo per ciechi, pensato da un giocatore cieco.",
        "Ideato da Gabriele Battaglia il 13 aprile 2015, portato in Python nel 2020 con l'aiuto di Gemini 2.5, rifatto dal 2026 con ClaudIA.",
        "Il codice è su GitHub, nel repository GabrieleBattaglia/Showdown.",
    ])


def novita(testo_changelog):
    """Il changelog in forma leggibile: titoli senza cancelletti, niente righe vuote e niente accenti gravi del codice."""
    righe = []
    for riga in testo_changelog.splitlines():
        riga = riga.strip().replace("`", "")
        if not riga:
            continue
        if riga.startswith("## [") and "] - " in riga:
            numero_versione, data = riga[4:].split("] - ", 1)
            riga = f"Versione {numero_versione} del {data}."
        elif riga.startswith("#"):
            riga = riga.lstrip("#").strip()
            if not riga.endswith((".", ":", "!", "?")):
                riga += "."
        righe.append(riga)
    return "\n".join(righe)


# La cronaca di un incontro, per la finestra.

# I tipi degli eventi che la cronaca sintetica dice anche dentro un punto, come righe_del_momento.
_SINTETICA_NEL_PUNTO = ("TIMEOUT_INIZIO", "CAMBIO_CAMPO_INIZIO", "AMMONIZIONE", "PENALITA")


def righe_degli_eventi(voci, nomi, livello="normale"):
    """
    La cronaca di un tratto della partita dal vivo, dalle terne di evento, momento e apertura della
    Cronologia di partita_sonora, che può tagliare un momento a metà: ogni punto si apre con il set e
    il punteggio di partenza, come vuole la decisione D17, e alla sintetica un punto è una riga sola,
    che arriva quando il punto finisce. Una frase per riga, nessuna riga vuota.
    """
    righe = []
    for evento, momento, apre in voci:
        nel_punto = momento.genere == "punto"
        if nel_punto and apre:
            a, b = evento.punteggio or (0, 0)
            righe.append(f"Set {evento.set_n}, {nomi['A'].testo} {a}, {nomi['B'].testo} {b}.")
        if livello == cronaca.SINTETICA and nel_punto:
            if evento.tipo in ("PUNTO", "RIPETIZIONE") and momento.esito is not None:
                righe.append(cronaca.riga_sintetica(momento.esito, nomi))
                continue
            if evento.tipo not in _SINTETICA_NEL_PUNTO:
                continue
        testo = cronaca.frase(evento, nomi, livello)
        if testo:
            righe.append(testo)
    return righe


# La partita dal vivo, decisione D29: la guida del campo della cronaca e i testi della finestra.

def dove_ascolti(nomi, ascoltatore):
    """Da quale parte del tavolo si ascolta, e chi sta di fronte."""
    altro = "B" if ascoltatore == "A" else "A"
    return f"Ascolti da {nomi[ascoltatore].testo}, alla sua testata del tavolo; {nomi[altro].testo} sta di fronte, oltre lo schermo."


def guida_dal_vivo(nomi, ascoltatore, set_al_meglio, velocita):
    """Il testo con cui si apre il campo della cronaca della finestra dal vivo: chi gioca, da dove si ascolta, i tasti e la velocità."""
    return "\n".join([
        f"Partita dal vivo: {nomi['A'].testo} contro {nomi['B'].testo}, al meglio dei {set_al_meglio} set. L'incontro è già registrato nel mondo.",
        dove_ascolti(nomi, ascoltatore),
        "Invio o spazio su Prosegui fanno sentire il gioco fino al punto seguente; mentre suona, lo stesso tasto lo ferma e lo riprende, e salta il riscaldamento.",
        "Alt+F ascolta fino a fine set, Alt+L passa dalla parte dell'altro giocatore, Alt+V va alla fine e mostra il risultato, Esc esce senza svelarlo.",
        f"Più e meno cambiano la velocità di gioco, ora {velocita}: accorcia le pause e la procedura dell'arbitro, mai l'azione.",
        "Time-out, cambio campo e inizio del set non si sentono: il suono riprende dalla ripresa del gioco.",
        "In questo campo, dopo ogni tranche, c'è la cronaca di quello che hai appena sentito, pause lunghe comprese; "
        "F1 ci rimette questa guida, Maiusc+Tab torna al pulsante.",
    ])


def titolo_dal_vivo(nomi, velocita):
    return f"Dal vivo, {nomi['A'].testo} contro {nomi['B'].testo}, velocità {velocita}"


SPIEGAZIONE_VELOCITA = ("La velocità di gioco vale per tutte le partite dal vivo: a 1 le pause fra i punti e la procedura dell'arbitro durano come nella realtà, "
                        "a 2 la metà, a 4, la predefinita, un quarto. L'azione resta sempre a tempo reale. Durante la partita più e meno la cambiano al volo.")
# Il dialogo degli effetti sonori, con il volume della partita della decisione D30.
SPIEGAZIONE_VOLUMI = ("Il volume degli effetti sonori, da 0 a 100: a 50 i suoni sono come sono stati pensati, a zero tacciono. "
                      "Il volume della partita dal vivo, da 0 a 100, vale soltanto per i suoni della partita: a 95 suona come è stata pensata, "
                      "a 100 arriva al massimo senza distorcere, a zero tace.")


# L'amichevole nella finestra, tappa 9: risultato e cronaca salvata.

SALVA_LA_CRONACA = "La cronaca dell'incontro si salva in un file con Ctrl+Maiusc+O."
NESSUNA_AMICHEVOLE = "Nella sessione non hai ancora giocato un'amichevole: se ne gioca una con Ctrl+O."


def risultato_amichevole(risultato, mondo):
    """Il risultato di un'amichevole, aperto dal dato essenziale: chi vince, i set, contro chi e i parziali dal punto di vista di chi vince."""
    id_a, id_b = risultato.parti
    vince_a = risultato.vincitore == "A"
    vincitore, perdente = (mondo.giocatori[id_a], mondo.giocatori[id_b]) if vince_a else (mondo.giocatori[id_b], mondo.giocatori[id_a])
    sa, sb = risultato.set_vinti
    mio, suo = (sa, sb) if vince_a else (sb, sa)
    parziali = ", ".join(f"{a} a {b}" if vince_a else f"{b} a {a}" for a, b in risultato.set)
    return (f"Vince {nome_completo(vincitore)}, {mio} set a {suo} contro {nome_completo(perdente)}: {parziali}. "
            f"Amichevole al meglio dei {risultato.formato.set_al_meglio} set.")


def _dopo_il_risultato(risultato, mondo):
    """Il risultato, quello che l'amichevole ha portato nel mondo, punti allenamento e infortuni, e come salvarne la cronaca."""
    return [risultato_amichevole(risultato, mondo), *(risultato.registrazione or []), SALVA_LA_CRONACA]


def amichevole_solo_risultato(risultato, mondo):
    return "\n".join(_dopo_il_risultato(risultato, mondo))


def amichevole_senza_risultato(nomi):
    """
    La vista dopo Esc nella partita dal vivo, decisione D30: l'incontro è registrato, ma il risultato
    non si svela, e nemmeno i punti allenamento, che lo farebbero capire; si dice dove leggerlo.
    """
    return "\n".join([
        f"Sei uscito dalla partita dal vivo senza vederne la fine: l'amichevole fra {nomi['A'].testo} e {nomi['B'].testo} è comunque registrata nel mondo.",
        "Il risultato lo leggi nel diario di ciascuno dei due giocatori, con Ctrl+Maiusc+D, e nella cronaca intera, che si salva in un file con Ctrl+Maiusc+O.",
    ])


def cronaca_amichevole(risultato, nomi, livello):
    """
    La cronaca intera dell'amichevole al livello scelto, che Vai alla fine mostra sotto il risultato:
    la vista la mette dopo il risultato e dopo il perché di un salvataggio non riuscito, che in fondo
    a centinaia di righe nessuno troverebbe.
    """
    return "\n".join(cronaca.componi(risultato.momenti, nomi, livello))


def nessuno_per_l_amichevole(mondo, ora, poli=None, primo=None):
    """
    Perché oggi l'amichevole non si gioca: nessun tesserato della polisportiva, o nessun avversario
    del primo giocatore, può giocare; e fra quanto arriva il giorno simulato dopo. ora è in UTC.
    """
    if primo is None:
        chi = f"Oggi nessun tesserato di {poli.nome} può giocare un'amichevole"
    else:
        chi = f"Oggi nessun altro giocatore può giocare un'amichevole contro {nome_completo(primo)}"
    prossimo = mondo.prossimo_avanzamento()
    quando = f"Il prossimo giorno simulato arriva fra {durata(prossimo - ora)}." if prossimo > ora else "Il prossimo giorno simulato arriva entro un minuto."
    return f"{chi}: ognuno ne gioca al massimo una per giorno simulato, e chi è infortunato o ritirato non gioca. {quando}"


def cronaca_salvata(percorso, livello, nomi):
    return f"La cronaca {livello} dell'amichevole fra {nomi['A'].testo} e {nomi['B'].testo} è nel file {percorso}."


def cronaca_non_salvata(errore):
    return f"La cronaca dell'amichevole non si è potuta salvare: {errore}."
