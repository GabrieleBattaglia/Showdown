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
Dalla tappa 11, il 2026-10-09, decisione D31, la scheda dice la classe, da K0 ad A1, con la
percentuale verso la classe seguente; l'indole, l'ambizione, il programma, l'intensità e la costanza
recente a parole; i tratti rari dell'allenamento; lo stipendio fisso del contratto e il valore di
mercato del giorno; il contratto, con la finestra del rinnovo. Ci sono i testi della sala
allenamento e dei contratti, che la finestra mostra, e la guida spiega classe, allenamento e contratti.
Dalla tappa 12, il 2026-10-14, decisione D32, il mondo gioca: la scheda ha i tornei e il palmarès, con
la classifica mondiale e il ritmo dei tornei, e l'acciacco accanto all'infortunio; ci sono i testi del
calendario e delle iscrizioni, del pannello dei tornei con le sue classifiche e i risultati dei tuoi
nascosti finché non li ascolti, dell'albo d'oro, della classifica mondiale, degli editor dei modelli e
delle formule, delle sfide e del calendario che non si legge; la guida spiega tornei e sfide. Le parti
della tappa 12 sono di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
"""

import copy
import datetime
import statistics

import allenamento
import classe
import contratti
import economia
import formule
import infortuni
import luoghi
import mercato
import modelli_torneo
import palmares
import sfide
import staff
import tornei
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
    FASCE_AMBIZIONE,
    FASCE_COSTANZA,
    FASCE_TEMPERAMENTO,
    INDOLI,
    LIMITE_MOVIMENTI_PER_TICK,
    MAX_TOTALE_PRECISIONE_RESISTENZA,
    MAX_TOTALE_SKILL_GIOCO,
    NOME_ATTR_TO_DISPLAY_MAP,
    PROPOSTE_RINNOVO_MASSIME,
)
from motore import cronaca
from motore.campo import costanza_relativa
from utilita import MESI, adesso_utc, converti_giorni_sim, data_breve, formatta_eta_sim, in_ora_locale
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
    "Seconda riga, la polisportiva attiva: prima il nome, poi g la gloria, t i tesserati sul massimo, m le mosse di mercato rimaste oggi, c la cassa in migliaia di euro, "
    "d le sfide che restano da lanciare. "
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


def percento(valore, decimali=0):
    """Una percentuale col simbolo, all'italiana: 64%, 1,5%. Regola di Gabriele del 23 ottobre 2026."""
    return f"{numero(valore, decimali)}%"


# L'articolo e la preposizione articolata davanti a un numero che si legge con una vocale.
ELISIONI = {"il": "l'", "al": "all'", "dal": "dall'", "del": "dell'", "nel": "nell'", "sul": "sull'"}


def _si_legge_con_vocale(scritto):
    """
    Vero se il numero scritto in cifre all'inizio del testo si legge con una vocale: uno, otto, undici,
    gli ottanta, gli ottocento e le loro migliaia, ottomila; un milione. Mille e cento no.
    """
    intera = ""
    for carattere in scritto:
        if not (carattere.isdigit() or carattere == "."):
            break
        intera += carattere
    gruppi = [g for g in intera.split(".") if g]
    if not gruppi:
        return False
    primo = int(gruppi[0])
    if len(gruppi) == 2 and primo == 1:
        return False
    return primo in (1, 8, 11) or 80 <= primo <= 89 or 800 <= primo <= 899


def con_articolo(articolo, scritto):
    """L'articolo davanti a un numero, eliso quando serve: al 64%, all'8%; il 37%, l'11%; dal 1,5% no, dall'1,5%."""
    if _si_legge_con_vocale(scritto):
        return ELISIONI[articolo] + scritto
    return f"{articolo} {scritto}"


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
    """L'indole del giocatore a parole, come granitica o di rimessa."""
    return INDOLI[g.indole]["nome"]


def punti(valore):
    """Una quantità di punti allenamento: senza decimali quando è intera, altrimenti con uno, 38,5."""
    arrotondato = round(valore, 1)
    return intero(arrotondato) if arrotondato == int(arrotondato) else numero(arrotondato)


def quanti_punti(valore, allenamento=False):
    """Una quantità di punti con il nome accordato: 1 punto, 38,5 punti; con allenamento, 1 punto allenamento."""
    testo = punti(valore)
    return f"{testo} {'punto' if testo == '1' else 'punti'}{' allenamento' if allenamento else ''}"


def da_a(prima, dopo):
    """
    Una salita a parole, da 14,6 a 15,3; con due decimali quando a uno non si vedrebbe, come da
    4,61 a 4,64 dopo una spesa piccola, che altrimenti sembrerebbe non aver fatto niente.
    """
    decimali = 2 if numero(prima) == numero(dopo) and abs(dopo - prima) >= 0.005 else 1
    return f"da {numero(prima, decimali)} a {numero(dopo, decimali)}"


def codice_classe(g):
    """La classe in breve: G4."""
    return classe.classe(g).codice


def classe_scheda(g):
    """La classe nella scheda: G4, al 37% verso G3; per A1, la più alta."""
    c = classe.classe(g)
    if c.percentuale is None:
        return f"{c.codice}, la più alta"
    return f"{c.codice}, {con_articolo('al', percento(c.percentuale))} verso {classe.codice(c.livello - 1)}"


def ambizione(g):
    """L'ambizione a parole e accordata, con le fasce di costanti.py: ambizioso, ambiziosa."""
    for limite, parola in FASCE_AMBIZIONE:
        if limite is None or g.ambizione < limite:
            return accorda(g, parola)
    return accorda(g, FASCE_AMBIZIONE[-1][1])


def costanza(g):
    """La costanza recente a parole: ferma, bassa, regolare, alta o altissima."""
    relativa = costanza_relativa(g)
    for limite, parola in FASCE_COSTANZA:
        if limite is None or relativa < limite:
            return parola
    return FASCE_COSTANZA[-1][1]


def nome_programma(chiave):
    """
    Il nome di un programma d'allenamento, cioè di un'indole, accordato a programma: aggressivo,
    difensivo, granitico, completo; i nomi con la preposizione restano come sono, di rimessa, da battuta.
    """
    nome = INDOLI[chiave]["nome"]
    return nome[:-1] + "o" if " " not in nome and nome.endswith("a") else nome


def programma(g):
    """Il programma d'allenamento a parole: secondo la sua indole, oppure il nome del programma scelto."""
    if g.programma == g.indole:
        return "secondo la sua indole"
    return nome_programma(g.programma)


def programma_e_indole(g):
    """
    Il programma nella riga della sala, sempre con l'indole, perché chi la scorre sappia a quale
    voce riportarlo: programma di rimessa, la sua indole; oppure programma aggressivo, indole di rimessa.
    """
    if g.programma == g.indole:
        return f"programma {nome_programma(g.programma)}, la sua indole"
    return f"programma {nome_programma(g.programma)}, indole {indole(g)}"


def voce_programma(chiave, g):
    """Una voce della scelta del programma nella sala: Aggressivo; per l'indole dell'allenando, Di rimessa, la sua indole."""
    voce = nome_programma(chiave).capitalize()
    return f"{voce}, la sua indole" if chiave == g.indole else voce


def mese_e_anno(dt):
    """Un mese con l'anno: dicembre 2027."""
    return f"{MESI[dt.month - 1]} {dt.year}"


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


def acciacco(g, oggi, con_calo=False):
    """
    L'acciacco della tappa 12 a parole, oppure una stringa vuota se non ce n'è: acciaccato al ginocchio
    destro fino al 20 ottobre 2026: rende un poco meno. Con con_calo dice anche quanto rende di meno oggi.
    """
    calo = infortuni.calo_acciacco(g, oggi)
    fino = getattr(g, "acciacco_fino", None)
    if fino is None or calo <= 0:
        return ""
    dove = infortuni.frase_sede(g.acciacco_sede)
    testo = accorda(g, "acciaccato") + (f" {dove}" if dove else "") + f" fino al {data_breve(fino)}: rende un poco meno"
    if con_calo:
        testo += f", oggi {con_articolo('il', percento(calo * 100, 1))}"
    return testo


def ritmo_dei_tornei(g, mondo):
    """
    La riga del ritmo dei tornei nella scheda: per i tuoi tesserati iscrizione automatica accesa, dal
    18 ottobre 2026, oppure spenta; per gli altri da quando il mondo può iscriverli al torneo seguente.
    """
    club = mondo.polisportive.get(g.appartenenza)
    dal = f", dal {data_breve(g.prossimo_torneo)}" if g.prossimo_torneo is not None else ""
    if club is not None and not club.is_cpu_controlled:
        return f"Iscrizione automatica ai tornei: accesa{dal}." if g.iscrizione_automatica else "Iscrizione automatica ai tornei: spenta, si iscrive a mano dal calendario."
    if g.prossimo_torneo is None:
        return "Ritmo dei tornei: può iscriversi al primo torneo utile."
    return f"Ritmo dei tornei: il prossimo dal {data_breve(g.prossimo_torneo)}."


def _medagliere(chi):
    """Le medaglie a parole, per un giocatore o una polisportiva: 2 ori, 1 argento; nessuna."""
    parti = [conta(getattr(chi, campo), singolare, plurale) for campo, singolare, plurale in
             (("ori", "oro", "ori"), ("argenti", "argento", "argenti"), ("bronzi", "bronzo", "bronzi"), ("legni", "legno", "legni")) if getattr(chi, campo)]
    return unisci(parti) or "nessuna"


def posto_mondiale(g, mondo):
    """Il posto del giocatore nella classifica mondiale del suo sesso, oppure None se non ci sta ancora."""
    for posto, riga in enumerate(palmares.classifica_mondiale(mondo, g.sesso), start=1):
        if riga["id"] == g.id:
            return posto
    return None


def _tornei_e_palmares(g, mondo):
    """
    La parte della scheda della tappa 12, punto 12.7: tornei giocati, medaglie, titoli, punti della
    classifica mondiale e posto, gare a squadre vinte e perse, e la riga del ritmo dei tornei.
    """
    righe = ["[TORNEI E PALMARÈS]"]
    righe.append(f"Tornei giocati: {g.tornei_giocati} | Medaglie: {_medagliere(g)} | Gare a squadre: {g.gare_squadre_vinte} vinte, {g.gare_squadre_perse} perse")
    posto = posto_mondiale(g, mondo)
    classifica = "maschile" if g.sesso == "m" else "femminile"
    mondiale = f"Classifica mondiale {classifica}: {numero(g.punti_mondiali)} punti" + (f", {posto}° posto" if posto else ", non ancora in classifica")
    righe.append(f"{mondiale} | Punti dell'ultimo anno: {numero(palmares.punti_dell_anno(g, mondo.datetime_corrente_simulazione.date()))}")
    if g.titoli:
        titoli = [f"{voce['torneo']} del {data_breve(datetime.date.fromisoformat(voce['data'][:10]))}, {_posto_del_titolo(voce['posto'])}" for voce in g.titoli]
        righe.append(f"Titoli: {'; '.join(titoli)}.")
    righe.append(ritmo_dei_tornei(g, mondo))
    return righe


def _posto_del_titolo(posto):
    return {1: "oro", 2: "argento", 3: "bronzo", 4: "legno"}.get(posto, f"{posto}° posto")


def carattere(g):
    """Il temperamento di oggi a parole e accordato, con le fasce di costanti.py: focoso, focosa."""
    attuale = g.temperamento_attuale
    for limite, parola, compreso in FASCE_TEMPERAMENTO:
        if limite is None or attuale < limite or (compreso and attuale == limite):
            return accorda(g, parola)
    return accorda(g, FASCE_TEMPERAMENTO[-1][1])


def riga_giocatore(g, mondo):
    """Il giocatore in una riga degli elenchi."""
    return (f"{g.id}. {nome_completo(g)}, {'uomo' if g.sesso == 'm' else 'donna'}, {anni(g)} anni, valore {numero(g.indice_collettivo_valore)}, "
            f"classe {codice_classe(g)}, {stato(g, mondo)}")


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
    # I tratti rari dell'allenamento, dalla tappa 11, sempre visibili.
    if g.talento:
        tratti.append("talento")
    if g.apprendista_rapido:
        tratti.append("apprendista rapido")
    if g.maturazione:
        tratti.append(f"maturazione {g.maturazione}")
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
        f"[{etichetta}] ID: {g.id} | {nome_completo(g)} | {'Uomo' if g.sesso == 'm' else 'Donna'}, {anni(g)} anni | Valore: {numero(g.indice_collettivo_valore)} | "
        f"Classe: {classe_scheda(g)} | Classe migliore della carriera: {classe.codice(g.livello_migliore())}",
        *([f"Provenienza: {luoghi.descrivi(g.luogo)}"] if getattr(g, "luogo", "") else []),
        f"Descrizione: {g.descrizione_fisica}",
        f"Fisico: {g.altezza} cm e {g.peso} kg | Indole: {indole(g)} | Ambizione: {ambizione(g)} | Punti allenamento: {punti(g.punti_allenamento)} | "
        f"Gloria richiesta: {intero(g.gloria_richiesta)}",
        riga_allenamento(g, mondo),
    ]
    tratti = f"Tratti: {unisci(tratti_speciali(g)) or 'nessuno in particolare'} | Carattere: {carattere(g)}"
    if g.infortunato and g.infortunio_fine_datetime:
        testo = infortunio(g)
        tratti += f" | {testo[0].upper()}{testo[1:]}"
    # Dalla tappa 12, accanto all'infortunio, l'acciacco con la sede, la fine e il calo di oggi.
    testo = acciacco(g, mondo.datetime_corrente_simulazione, con_calo=True)
    if testo:
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
    # Dalla tappa 13, D33, chi allena e dove, o perché non può allenare; la classe migliore sta nella prima riga.
    allena = _chi_allena_da_giocatore(g, mondo)
    if allena:
        righe.append(allena)
    righe.extend(_tornei_e_palmares(g, mondo))
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


def riga_allenamento(g, mondo):
    """La riga dell'allenamento nella scheda: per i tuoi tesserati programma, intensità e costanza; per gli altri la costanza."""
    club = mondo.polisportive.get(g.appartenenza)
    if club is not None and not club.is_cpu_controlled:
        return f"Allenamento: programma {programma(g)}, intensità {g.intensita}, costanza recente {costanza(g)}"
    return f"Allenamento: costanza recente {costanza(g)}"


def riga_contratto_scheda(g, mondo):
    """La riga del contratto di un tesserato nella scheda; None per chi non ha contratto."""
    club = mondo.polisportive.get(g.appartenenza)
    if club is None or not contratti.ha_contratto(g):
        return None
    oggi = mondo.datetime_corrente_simulazione
    scadenza = data_breve(g.contratto_scadenza)
    if contratti.ha_rinnovo(g):
        return f"Rinnovato: dal {scadenza}, {euro(g.rinnovo_stipendio)} al mese fino al {data_breve(g.rinnovo_scadenza)}"
    if not contratti.in_finestra(g, oggi):
        return f"Contratto con {club.nome} fino al {scadenza}, si rinnova da {mese_e_anno(contratti.inizio_finestra(g))}"
    if club.is_cpu_controlled:
        return f"Contratto in scadenza il {scadenza}"
    if not contratti.puo_trattare(g):
        return f"Contratto in scadenza il {scadenza}: non vuole più trattare"
    mesi = contratti.durata_proposta(g)
    return (f"Contratto in scadenza il {scadenza}: oggi chiederebbe {euro(contratti.richiesta_rinnovo(g, club, mesi))} al mese per {mesi} mesi; "
            f"proposte rimaste: {PROPOSTE_RINNOVO_MASSIME - g.proposte_rinnovo}")


def _economia_del_giocatore(g, mondo):
    """Le righe dell'economia nella scheda: stipendio, valore, esperienza, contratto e, per un tesserato, fedeltà e umore."""
    oggi = mondo.datetime_corrente_simulazione
    stipendio = f"{euro(economia.stipendio_pagato(g))} al mese"
    if contratti.ha_contratto(g):
        stipendio += f", fisso fino al {data_breve(g.contratto_scadenza)}"
    del_giorno = economia.valore_di_mercato(g, oggi)
    pieno = economia.valore_di_mercato_pieno(g)
    valore_mercato = euro(del_giorno) if del_giorno >= pieno else f"{euro(del_giorno)}, {intero(pieno)} a contratto lungo"
    righe = [f"Stipendio: {stipendio} | Valore di mercato: {valore_mercato} | "
             f"Esperienza di carriera: {aggettivo(g.esperienza, ESPERIENZA_MASSIMA)} ({numero(g.esperienza)})"]
    contratto = riga_contratto_scheda(g, mondo)
    if contratto:
        righe.append(contratto)
    club = mondo.polisportive.get(g.appartenenza)
    if club is not None:
        riga = f"Fedeltà a {club.nome}: {numero(g.fedelta, 0)}% | Umore: {umore(g)}"
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
    righe.extend(f"{i}. {nome_completo(g)} (ID {g.id}), valore {numero(g.indice_collettivo_valore)}, classe {codice_classe(g)}, {anni(g)} anni, {indole(g)}, {_club(g)}"
                 for i, g in enumerate(ordinati, 1))
    return "\n".join(righe)


def top_10(mondo):
    righe = []
    migliori = sorted(attivi(mondo), key=lambda g: g.indice_collettivo_valore, reverse=True)[:10]
    if migliori:
        righe.append("I dieci giocatori di maggior valore:")
        righe.extend(f"{i}. {nome_completo(g)} (ID {g.id}), valore {numero(g.indice_collettivo_valore)}, classe {codice_classe(g)}, {anni(g)} anni, {_club(g)}"
                     for i, g in enumerate(migliori, 1))
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
        *_statistiche_delle_classi(gruppo, mondo),
        # Dalla tappa 13 gli allenatori del mondo, D33.
        *_statistiche_dello_staff(mondo),
        "[MIGLIORI PER CARATTERISTICA]",
    ]
    for nome_base in ATTRIBUTI_BASE_CON_ALLENABILI:
        migliore = max(gruppo, key=lambda g, nb=nome_base: g._get_valore_totale(nb))
        righe.append(f"{valore_caratteristica(migliore, nome_base)}, {nome_completo(migliore)} (ID {migliore.id}), {anni(migliore)} anni, {_club(migliore)}")
    if mondo.polisportive:
        prima = max(mondo.polisportive.values(), key=lambda p: p.indicecollettivotesserati)
        righe.append(f"La polisportiva di maggior valore collettivo è {prima.nome}, con {numero(prima.indicecollettivotesserati)}.")
    return "\n".join(righe)


def _statistiche_delle_classi(gruppo, mondo):
    """Le classi dei giocatori in attività, per lettera con la percentuale, la mediana e la più alta, e i contratti che scadono nel mese."""
    livelli = {g.id: classe.classe(g).livello for g in gruppo}
    n = len(gruppo)
    per_lettera = {}
    for livello in livelli.values():
        lettera = classe.codice(livello)[0]
        per_lettera[lettera] = per_lettera.get(lettera, 0) + 1
    elenco = unisci([f"{lettera} {quanti} ({numero(quanti * 100 / n)}%)" for lettera, quanti in sorted(per_lettera.items())])
    mediana = classe.codice(round(statistics.median_low(livelli.values())))
    migliore = min(gruppo, key=lambda g: (livelli[g.id], -g.indice_collettivo_valore))
    oggi = mondo.datetime_corrente_simulazione
    scadono = sum(1 for g in gruppo if contratti.ha_contratto(g) and not contratti.ha_rinnovo(g) and contratti.mesi_interi(oggi, g.contratto_scadenza) <= 1
                  and g.contratto_scadenza > oggi)
    return [f"Classi: {elenco}. Classe mediana {mediana}; la più alta è {classe.codice(livelli[migliore.id])}, di {nome_completo(migliore)} (ID {migliore.id}).",
            f"Contratti che scadono entro il primo del mese prossimo: {scadono}."]


# Lo staff, tappa 13, decisione D33.

def _rispetto_al_medio(fattore):
    """Un fattore dello staff a parole, rispetto allo staff medio: più 6%, meno 15%, come lo staff medio."""
    scarto = round((fattore - 1.0) * 100)
    if scarto == 0:
        return "come lo staff medio"
    return f"{'più' if scarto > 0 else 'meno'} {abs(scarto)}%"


def nome_allenatore(a):
    """Il nome dell'allenatore con la classe da allenatore: Mario Rossi, C4."""
    return f"{nome_completo(a)}, {a.codice}"


def riga_allenatore(a, mondo):
    """
    Una riga per gli elenchi degli allenatori: nome, classe, età, tipo, e dove allena o quanto chiede da
    capo; la prelazione e la riserva di due ore, se ci sono. La riserva si confronta con l'ora vera di adesso:
    fino alla revisione del 22 ottobre 2026 si guardava l'ora dell'ultimo avanzamento, e la riga diceva
    riservato a te fino a un'ora già passata.
    """
    oggi = mondo.datetime_corrente_simulazione
    if a.tipo == staff.EX:
        tipo = "ex giocatrice" if a.sesso == "f" else "ex giocatore"
    else:
        tipo = "nata allenatrice" if a.sesso == "f" else "nato allenatore"
    riga = f"{nome_allenatore(a)}, {int(a.eta_anni(oggi))} anni, {tipo}, {a.visus}"
    if a.polisportiva:
        riga += f", {staff.nome_del_ruolo(a)} di {a.polisportiva}"
    else:
        riga += f", chiede {euro(staff.stipendio_richiesto(a, staff.CAPO))} al mese da capo e {euro(staff.stipendio_richiesto(a, staff.ASSISTENTE))} da assistente"
    if a.prelazione:
        riga += f", in prelazione per {a.prelazione} fino al {data_breve(a.prelazione_fino)}"
    if a.riservato_fino is not None and a.riservato_fino > adesso_utc():
        riga += f", {'riservata' if a.sesso == 'f' else 'riservato'} a te fino alle {in_ora_locale(a.riservato_fino):%H:%M}"
    return riga


def scheda_allenatore(a, mondo):
    """La scheda di un allenatore: chi è, la classe, il tipo, l'aspetto o la carriera da giocatore, l'impiego e il contratto."""
    oggi = mondo.datetime_corrente_simulazione
    ruolo = "ALLENATRICE" if a.sesso == "f" else "ALLENATORE"
    righe = [f"[{ruolo}] {nome_completo(a)} | {'Uomo' if a.sesso == 'm' else 'Donna'}, {int(a.eta_anni(oggi))} anni | {a.visus.capitalize()} | "
             f"Classe da {ruolo.lower()}: {a.codice}"]
    if a.luogo:
        righe.append(f"Provenienza: {luoghi.descrivi(a.luogo)}")
    if a.tipo == staff.EX:
        g = mondo.giocatori.get(a.giocatore_id)
        provenienza = f", ha chiuso la carriera con {a.club_di_provenienza}" if a.club_di_provenienza else ""
        giocatore, allenatore = ("giocatrice", "allenatrice") if a.sesso == "f" else ("giocatore", "allenatore")
        righe.append(f"Ex {giocatore}{provenienza}: la classe da {allenatore} è la sua classe migliore da {giocatore}.")
        if g is not None:
            righe.append(f"Da {giocatore}: {g.partitevinte + g.partiteperse} partite, {g.partitevinte} vinte; medaglie: oro {g.ori}, argento {g.argenti}, bronzo {g.bronzi}.")
    else:
        righe.append(f"{'Nata allenatrice' if a.sesso == 'f' else 'Nato allenatore'}, senza carriera da giocatore.")
        descrizione = a.descrizione_fisica(oggi)
        if descrizione:
            righe.append(f"Descrizione: {descrizione}")
    if a.polisportiva:
        rinnovo = f", poi rinnovato a {euro(a.rinnovo_stipendio)} fino al {data_breve(a.rinnovo_scadenza)}" if contratti.ha_rinnovo(a) else ""
        righe.append(f"{staff.nome_del_ruolo(a).capitalize()} di {a.polisportiva}: {euro(a.contratto_stipendio)} al mese fino al {data_breve(a.contratto_scadenza)}{rinnovo}.")
    else:
        righe.append(f"{accorda_sesso(a.sesso, 'Libero')}: chiede {euro(staff.stipendio_richiesto(a, staff.CAPO))} al mese da capo e "
                     f"{euro(staff.stipendio_richiesto(a, staff.ASSISTENTE))} da assistente.")
    if a.prelazione:
        righe.append(f"In prelazione per {a.prelazione} fino al {data_breve(a.prelazione_fino)}.")
    # Dal collaudo del 23 ottobre 2026 l'anno del calendario simulato, con le parole di Gabriele, al posto di
    # "Smetterà di allenare fra circa 30 anni simulati". Il giro del giorno in cui compie eta_fine lo toglie
    # dal mondo, quindi l'ultimo giorno in attività è quello prima: conta per chi smette il primo gennaio.
    fine = oggi + datetime.timedelta(days=max(0, a.eta_fine - a.eta(oggi) - 1))
    righe.append(f"Sarà in attività sperabilmente fino al {fine.year}.")
    return "\n".join(righe)


def _chi_allena_da_giocatore(g, mondo):
    """
    Per un giocatore che allena, la classe da allenatore e dove; per un ritirato che non può, il perché;
    altrimenti niente. La classe migliore della carriera sta accanto a quella di oggi, nella prima riga della
    scheda, risposta 25: fino alla revisione del 22 ottobre 2026 stava venti righe più giù.
    """
    a = next((a for a in mondo.allenatori.values() if a.giocatore_id == g.id), None)
    if a is not None:
        dove = f"{staff.nome_del_ruolo(a)} di {a.polisportiva}" if a.polisportiva else accorda_sesso(a.sesso, "libero")
        return f"Allena, classe da {'allenatrice' if a.sesso == 'f' else 'allenatore'} {a.codice}: {dove}"
    if g.ritirato and not staff.puo_allenare(g.livello_migliore()):
        return "Non può allenare: la classe migliore è sotto H0"
    return ""


# I nomi dei tre posti dello staff, nella scheda della polisportiva e nei dialoghi.
NOMI_DEI_POSTI = ("Capo", "Assistente 1", "Assistente 2")


def allenatore_del_posto(p, posto, mondo):
    """L'allenatore che occupa il posto dello staff della polisportiva, o None per un posto vuoto."""
    numero_allenatore = p.staff[posto]
    return mondo.allenatori.get(numero_allenatore) if numero_allenatore else None


def qualita_dello_staff(p, mondo):
    """
    La qualità dello staff in una frase, con gli effetti rispetto allo staff medio del mondo. Dalla risposta
    35 i fattori dei giocatori si dividono per la loro media, così il mondo si allena come prima; i rapporti
    fra i club restano quelli delle ancore, e la frase li dice rispetto allo staff medio, coi fattori prima
    della divisione: senza staff il 15% meno, col migliore fino al 20% in più.
    """
    q = staff.qualita_della_polisportiva(p, mondo.allenatori)
    allenamento, rischio, fedelta = staff.fattori(q, mondo.qualita_media_dello_staff)
    return (f"Qualità dello staff {round(q * 100)}%, lo staff medio del mondo {round(mondo.qualita_media_dello_staff * 100)}%: "
            f"allenamento {_rispetto_al_medio(allenamento)}, infortuni {_rispetto_al_medio(rischio)}, fedeltà {_rispetto_al_medio(fedelta)}.")


def righe_dello_staff(p, mondo):
    """Lo staff della polisportiva nella sua scheda: i tre posti e la qualità, con gli effetti rispetto allo staff medio del mondo."""
    righe = ["[STAFF]"]
    for posto, titolo in enumerate(NOMI_DEI_POSTI):
        a = allenatore_del_posto(p, posto, mondo)
        if a is None:
            righe.append(f"{titolo}: nessuno.")
        else:
            righe.append(f"{titolo}: {nome_allenatore(a)}, {euro(a.contratto_stipendio)} al mese fino al {data_breve(a.contratto_scadenza)}.")
    righe.append(qualita_dello_staff(p, mondo))
    return righe


# I dialoghi dello staff e del mercato degli allenatori, progetto 4.2 e 4.3.

def testata_staff(p, mondo):
    """In testa al dialogo dello staff: la cassa, gli stipendi dello staff, le mosse e la qualità."""
    return (f"{p.nome}: cassa {euro(p.cassa)}, stipendi dello staff {euro(mondo.monte_dello_staff(p))} al mese, "
            f"mosse rimaste {mondo.mosse_rimaste(p)} su {LIMITE_MOVIMENTI_PER_TICK}.\n{qualita_dello_staff(p, mondo)}")


def riga_posto_staff(p, posto, mondo):
    """
    Un posto nel dialogo dello staff, come un tesserato nei contratti: Capo: Mario Rossi, C4, 450 euro al
    mese fino al 1 marzo 2030, rinnovabile da dicembre; oppure in scadenza, rinnovato, che non tratta più,
    o il posto vuoto.
    """
    titolo = NOMI_DEI_POSTI[posto]
    a = allenatore_del_posto(p, posto, mondo)
    if a is None:
        return f"{titolo}: posto vuoto"
    oggi = mondo.datetime_corrente_simulazione
    chi = f"{titolo}: {nome_allenatore(a)}"
    if contratti.ha_rinnovo(a):
        return f"{chi}, rinnovato dal {data_breve(a.contratto_scadenza)}: {euro(a.rinnovo_stipendio)} al mese fino al {data_breve(a.rinnovo_scadenza)}"
    inizio = f"{chi}, {euro(a.contratto_stipendio)} al mese fino al {data_breve(a.contratto_scadenza)}"
    if not contratti.in_finestra(a, oggi):
        return f"{inizio}, rinnovabile da {MESI[contratti.inizio_finestra(a).month - 1]}"
    if not contratti.puo_trattare(a):
        return f"{chi}, non tratta più: {accorda_sesso(a.sesso, 'libero')} dal {data_breve(a.contratto_scadenza)}"
    mesi = staff.durata_proposta(a, oggi)
    return (f"{inizio}, in scadenza: chiede {euro(staff.richiesta_rinnovo(a, p, mesi, oggi))} al mese per {mesi} mesi, "
            f"proposte rimaste {PROPOSTE_RINNOVO_MASSIME - a.proposte_rinnovo}")


def esito_previsto_rinnovo_staff(a, p, stipendio, mesi, oggi):
    """L'esito previsto di una proposta di rinnovo allo staff, come per i tesserati."""
    probabilita = staff.probabilita_rinnovo(a, p, stipendio, mesi, oggi)
    return (f"Accetterebbe {con_articolo('al', percento(probabilita))}. Per {mesi} mesi chiede {euro(staff.richiesta_rinnovo(a, p, mesi, oggi))} al mese. "
            f"Il contratto nuovo partirebbe il {data_breve(a.contratto_scadenza)}.")


def domanda_rinnovo_staff(a, p, stipendio, mesi, oggi):
    """La conferma della proposta di rinnovo a un allenatore, con la probabilità."""
    probabilita = staff.probabilita_rinnovo(a, p, stipendio, mesi, oggi)
    return (f"Proporre a {nome_completo(a)}, {staff.nome_del_ruolo(a)}, il rinnovo a {euro(stipendio)} al mese per {mesi} mesi, "
            f"dal {data_breve(a.contratto_scadenza)}? Accetterebbe {con_articolo('al', percento(probabilita))}.")


def esito_rinnovo_staff(a, p, accettato, richiesta, mesi):
    """L'esito della proposta allo staff: accettata, rifiutata con le proposte rimaste, o chiusa al terzo rifiuto."""
    if accettato:
        return (f"{nome_completo(a)} ha accettato: dal {data_breve(a.contratto_scadenza)} prenderà {euro(a.rinnovo_stipendio)} al mese, "
                f"fino al {data_breve(a.rinnovo_scadenza)}.")
    vorrebbe = f"{nome_completo(a)} ha rifiutato: per firmare vorrebbe circa {euro(richiesta)} al mese per {mesi} mesi."
    rimaste = PROPOSTE_RINNOVO_MASSIME - a.proposte_rinnovo
    if rimaste <= 0:
        return f"{vorrebbe} Non vuole più trattare: il contratto con {p.nome} finirà il {data_breve(a.contratto_scadenza)}."
    return f"{vorrebbe} {conta(rimaste, 'proposta rimasta', 'proposte rimaste').capitalize()}, una al giorno."


def domanda_licenziamento(a, p, mondo):
    """La domanda del licenziamento, con la buonuscita e la mossa."""
    buonuscita = contratti.buonuscita(a, mondo.datetime_corrente_simulazione)
    costo = f"la buonuscita è di {euro(buonuscita)}" if buonuscita else "non c'è buonuscita"
    fine = f"Il contratto finirebbe il {data_breve(a.contratto_scadenza)}"
    if contratti.ha_rinnovo(a):
        fine += f", e il rinnovo già concordato il {data_breve(a.rinnovo_scadenza)}"
    return (f"Licenziare {nome_completo(a)}, {staff.nome_del_ruolo(a)} di {p.nome}? {fine}: "
            f"{costo}. Tornerà {accorda_sesso(a.sesso, 'libero')}, e userai {_mossa(p, mondo)}.")


def esito_licenziamento(a, p, buonuscita):
    con = f", con una buonuscita di {euro(buonuscita)}" if buonuscita else ""
    return f"{nome_completo(a)} non è più nello staff di {p.nome}{con}: è {accorda_sesso(a.sesso, 'libero')}."


def info_mercato_allenatori(p, mondo):
    """In testa al mercato degli allenatori: la cassa, i posti vuoti dello staff e le mosse."""
    vuoti = [NOMI_DEI_POSTI[posto].lower() for posto in range(staff.POSTI) if not p.staff[posto]]
    posti = f"posti vuoti: {unisci(vuoti)}" if vuoti else "lo staff è al completo"
    return f"{p.nome}: cassa {euro(p.cassa)}, {posti}, mosse rimaste {mondo.mosse_rimaste(p)} su {LIMITE_MOVIMENTI_PER_TICK}."


def voce_del_posto(p, posto, mondo):
    """Un posto nella scelta del mercato: Capo, vuoto; Assistente 1, occupato da Mario Rossi, C4."""
    a = allenatore_del_posto(p, posto, mondo)
    return f"{NOMI_DEI_POSTI[posto]}, {'vuoto' if a is None else f'occupato da {nome_allenatore(a)}'}"


def spiegazione_ingaggio_allenatore(a, p, posto, mondo):
    """La spiegazione della cifra d'ingaggio: il contratto che l'allenatore propone e quanto chiede per firmare."""
    oggi = mondo.datetime_corrente_simulazione
    ruolo = staff.CAPO if posto == 0 else staff.ASSISTENTE
    mesi = staff.durata_proposta(a, oggi)
    nome_ruolo = ("capo allenatrice" if a.sesso == "f" else "capo allenatore") if ruolo == staff.CAPO else "assistente"
    return (f"Da {nome_ruolo} {nome_completo(a)} propone un contratto di {mesi} mesi a {euro(staff.stipendio_richiesto(a, ruolo))} al mese fissi. "
            f"Per firmare chiede {euro(staff.ingaggio_richiesto(a, ruolo, p))} d'ingaggio: più offri, più è probabile che accetti.")


def domanda_offerta_allenatore(a, p, posto, importo, probabilita, mondo):
    return (f"Offrire a {nome_completo(a)} il posto di {NOMI_DEI_POSTI[posto].lower()} dello staff di {p.nome}, con un ingaggio di {euro(importo)}? "
            f"Accetta {con_articolo('al', percento(probabilita))}. Userai {_mossa(p, mondo)}.")


def esito_offerta_allenatore(a, p, accetta, importo, probabilita):
    if accetta:
        return (f"{nome_completo(a)} ha accettato l'ingaggio di {euro(importo)}: è {staff.nome_del_ruolo(a)} di {p.nome}, "
                f"a {euro(a.contratto_stipendio)} al mese fino al {data_breve(a.contratto_scadenza)}.")
    return f"{nome_completo(a)} ha rifiutato l'ingaggio di {euro(importo)}: accettava {con_articolo('al', percento(probabilita))}."


def riepilogo_staff(p, esiti, mondo):
    """Il riepilogo dello staff e del mercato degli allenatori alla chiusura: quante operazioni, una riga ciascuna, e lo staff di adesso."""
    if not esiti:
        return "\n".join([f"Staff di {p.nome}: nessuna operazione.", *righe_dello_staff(p, mondo)[1:]])
    return "\n".join([f"Staff di {p.nome}: {conta(len(esiti), 'operazione', 'operazioni')}.", *(testo for testo, _esito in esiti), *righe_dello_staff(p, mondo)[1:]])


def evento_staff(esiti):
    """Il fatto dello staff nella barra di stato: staff: 2 operazioni."""
    return f"staff: {conta(len(esiti), 'operazione', 'operazioni')}"


def _statistiche_dello_staff(mondo):
    """Gli allenatori del mondo, D33: quanti, ex giocatori e nati, liberi e impiegati, per lettera di classe; e le polisportive con un capo."""
    allenatori = list(mondo.allenatori.values())
    if not allenatori:
        return ["Allenatori: nessuno, per ora."]
    ex = sum(1 for a in allenatori if a.tipo == staff.EX)
    liberi = sum(1 for a in allenatori if a.libero)
    per_lettera = {}
    for a in allenatori:
        per_lettera[a.codice[0]] = per_lettera.get(a.codice[0], 0) + 1
    con_tesserati = [p for p in mondo.polisportive.values() if p.tesserati]
    con_capo = sum(1 for p in con_tesserati if p.staff[0])
    return [f"Allenatori: {len(allenatori)}, di cui {ex} ex giocatori e {len(allenatori) - ex} nati allenatori; liberi {liberi}, nello staff {len(allenatori) - liberi}.",
            f"Classi degli allenatori: {unisci([f'{lettera} {quanti}' for lettera, quanti in sorted(per_lettera.items())])}. "
            f"Polisportive con un capo: {con_capo} su {len(con_tesserati)}; staff medio del mondo {round(mondo.qualita_media_dello_staff * 100)}%."]


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
    conti = f"Cassa: {euro(p.cassa)} | Sponsor: {euro(mondo.sponsor(p))} al mese | Stipendi: {euro(mondo.monte_stipendi(p))} al mese"
    if arretrati:
        conti += f" | Arretrati da pagare: {euro(arretrati)}"
    righe.append(conti)
    righe.append("[PALMARÈS]")
    if any((p.coppe_oro, p.coppe_argento, p.coppe_bronzo, p.coppe_legno, p.ori, p.argenti, p.bronzi, p.legni)):
        righe.append(f"Coppe: Oro:{p.coppe_oro} | Argento:{p.coppe_argento} | Bronzo:{p.coppe_bronzo} | Legno:{p.coppe_legno}")
        righe.append(f"Medaglie dei tesserati: Oro:{p.ori} | Argento:{p.argenti} | Bronzo:{p.bronzi} | Legno:{p.legni}")
    else:
        righe.append("Nessun trofeo, per ora.")
    # Dalla tappa 12, punto 12.7: il palmarès degli ultimi cinque anni, che fa la gloria, e le sfide.
    medaglie, coppe = palmares.somma_finestra(p, mondo.datetime_corrente_simulazione)
    righe.append(f"Palmarès degli ultimi cinque anni, che conta nella gloria: {numero(medaglie)} punti di medaglie e {numero(coppe)} punti di coppe.")
    sfide = f"Sfide: {conta(p.sfide_vinte, 'vinta', 'vinte')} e {conta(p.sfide_perse, 'persa', 'perse')}"
    if not p.is_cpu_controlled:
        sfide += f" | Sfide da lanciare: {max(0, p.sfide_da_lanciare - mondo.sfide.lanciate_in_sospeso(p.nome))}"
    if p.ultima_sfida is not None:
        sfide += f" | Ultima sfida il {data_breve(p.ultima_sfida)}"
    righe.append(sfide)
    # Dalla tappa 13 lo staff, D33.
    righe.extend(righe_dello_staff(p, mondo))
    righe.append("[TESSERATI]")
    presenti = [mondo.giocatori[gid] for gid in p.tesserati if gid in mondo.giocatori]
    if presenti:
        uomini = sum(1 for g in presenti if g.sesso == "m")
        eta_media = numero(sum(g.eta_anni for g in presenti) / len(presenti))
        ipovedenti = sum(1 for g in presenti if g.ipovedente)
        righe.append(f"{conta(uomini, 'uomo', 'uomini')} e {conta(len(presenti) - uomini, 'donna', 'donne')}, età media {eta_media} anni, {conta(ipovedenti, 'ipovedente', 'ipovedenti')}.")
        for g in sorted(presenti, key=lambda x: x.indice_collettivo_valore, reverse=True):
            riga = (f"{nome_completo(g)} (ID {g.id}), {anni(g)} anni, valore {numero(g.indice_collettivo_valore)}, classe {codice_classe(g)}, "
                    f"stipendio {euro(economia.stipendio_pagato(g))}, {indole(g)}, {stato(g, mondo)}")
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
            ("ingaggi", "ingaggi"), ("acquisti", "acquisti"), ("buonuscite", "buonuscite"), ("iscrizioni", "iscrizioni ai tornei"),
            ("premi", "premi dei tornei"), ("rimborsi", "rimborsi delle iscrizioni"), ("staff", "stipendi dello staff"))
    return unisci([f"{nome} {euro(conti[voce])}" for voce, nome in nomi if conti[voce]]) or "nessun movimento"


def bilancio(p, mondo):
    """Il bilancio di una polisportiva: cassa, entrate e uscite di ogni mese, arretrati, vendite e mesi passati."""
    sponsor = mondo.sponsor(p)
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
    for g in sorted(presenti, key=lambda g: g.id):
        scadenza = f", contratto fino al {data_breve(g.contratto_scadenza)}" if contratti.ha_contratto(g) else ""
        righe.append(riga_giocatore(g, mondo) + scadenza)
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
    if c.tipo != mercato.LIBERO and contratti.ha_contratto(g):
        mese = mese_e_anno(g.contratto_scadenza)
        costo += f", contratto fino {'ad' if mese[0] in 'aeiou' else 'a'} {mese}"
    tratti = "".join(", " + t for t in tratti_speciali(g))
    return f"{nome_completo(g)}, {anni(g)} anni, valore {numero(g.indice_collettivo_valore)}, stipendio {euro(c.stipendio)}, {costo}{tratti}, ID {g.id}"


def _mossa(p, mondo):
    mosse = mondo.mosse_rimaste(p)
    return "l'ultima mossa che ti resta oggi" if mosse == 1 else f"una delle {mosse} mosse che ti restano oggi"


def proposta_di_contratto(g, mondo):
    """La proposta di contratto del giocatore, D31: Propone un contratto di 12 mesi, fino al 1 agosto 2027, a 220 euro al mese fissi."""
    mesi = contratti.durata_proposta(g)
    scadenza = contratti.scadenza_dopo(mondo.datetime_corrente_simulazione, mesi)
    return f"Propone un contratto di {mesi} mesi, fino al {data_breve(scadenza)}, a {euro(economia.stipendio(g))} al mese fissi."


def _firmera(g, p):
    """Il contratto che un giocatore comprato firma col compratore: con Pat-Bologna per 12 mesi a 220 euro al mese."""
    return f"con {p.nome} per {contratti.durata_proposta(g)} mesi a {euro(economia.stipendio(g))} al mese"


def domanda_acquisto(c, p, mondo):
    return (f"Comprare {nome_completo(c.giocatore)} da {c.polisportiva.nome} per {euro(c.costo)}? "
            f"Firmerà {_firmera(c.giocatore, p)}. Userai {_mossa(p, mondo)}.")


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
            f"e se passa firmerà {_firmera(c.giocatore, p)}. Userai {_mossa(p, mondo)}.")


def domanda_ingaggio(c, importo, probabilita, p, mondo):
    return (f"Offrire a {nome_completo(c.giocatore)} un ingaggio di {euro(importo)}, per tesserarsi con {p.nome}? "
            f"Accetta {con_articolo('al', percento(probabilita))}. {proposta_di_contratto(c.giocatore, mondo)} Userai {_mossa(p, mondo)}.")


def esito_ingaggio(g, p, accetta, importo, probabilita):
    if accetta:
        return f"{nome_completo(g)} ha accettato l'ingaggio di {euro(importo)}: ora è {accorda(g, 'tesserato')} con {p.nome}."
    return f"{nome_completo(g)} ha rifiutato l'ingaggio di {euro(importo)}: accettava {con_articolo('al', percento(probabilita))}."


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
    return f"{nome_completo(g)}, {umore(g)}, {attesa(g)}; prende {euro(economia.stipendio_pagato(g))} al mese"


def riga_vendita(g, p, oggi=None):
    """Un tesserato nella finestra delle vendite: quanto vale, il giorno dato, e se è già in vendita."""
    riga = (f"{nome_completo(g)}, valore {numero(g.indice_collettivo_valore)}, stipendio {euro(economia.stipendio_pagato(g))}, "
            f"valore di mercato {euro(economia.valore_di_mercato(g, oggi))}")
    return riga + (f", in vendita a {euro(p.in_vendita[g.id])}" if g.id in p.in_vendita else "")


def svincolato(g, p, mondo, buonuscita=0):
    pagata = f", con una buonuscita di {euro(buonuscita)}," if buonuscita else ""
    return f"{nome_completo(g)} è {accorda(g, 'svincolato')} da {p.nome}{pagata} e torna {accorda(g, 'libero')}. {info_mercato(p, mondo)}"


def mesi_che_restano(g, oggi):
    """
    I mesi di contratto che restano a un tesserato, per lo svincolo: Gli restano 10 mesi di
    contratto; con un rinnovo già concordato, Gli restano 2 mesi di contratto e 24 del rinnovo già
    concordato. Stringa vuota se non resta niente.
    """
    mesi = round(contratti.mesi_al_termine(g, oggi))
    rinnovo = round(contratti.mesi_del_rinnovo(g, oggi))
    pronome = "Le" if g.sesso == "f" else "Gli"
    if rinnovo >= 1:
        if mesi >= 1:
            return f"{pronome} restano {conta(mesi, 'mese', 'mesi')} di contratto e {rinnovo} del rinnovo già concordato"
        return f"Il contratto finisce fra meno di un mese, ma restano i {rinnovo} mesi del rinnovo già concordato"
    if mesi >= 1:
        return f"{pronome} {'resta' if mesi == 1 else 'restano'} {conta(mesi, 'mese', 'mesi')} di contratto"
    return "Il contratto finisce fra meno di un mese"


def domanda_svincolo(g, p, mondo):
    """La domanda dello svincolo, con la buonuscita: Svincolare Mario Rossi? Gli restano 10 mesi di contratto: la buonuscita è di 1.100 euro."""
    oggi = mondo.datetime_corrente_simulazione
    buonuscita = contratti.buonuscita(g, oggi)
    mosse = f"userai una delle {mondo.mosse_rimaste(p)} mosse che ti restano oggi"
    if not buonuscita:
        return f"Svincolare {nome_completo(g)}? Tornerà {accorda(g, 'libero')}, e {mosse}."
    return f"Svincolare {nome_completo(g)}? {mesi_che_restano(g, oggi)}: la buonuscita è di {euro(buonuscita)}. Tornerà {accorda(g, 'libero')}, e {mosse}."


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
        conta(rapporto["tuoi_scaduti"], "tuo tesserato è tornato libero a fine contratto", "tuoi tesserati sono tornati liberi a fine contratto") if rapporto["tuoi_scaduti"] else "",
        conta(rapporto["tuoi_infortunati_in_seduta"], "tuo tesserato si è infortunato in allenamento", "tuoi tesserati si sono infortunati in allenamento")
        if rapporto["tuoi_infortunati_in_seduta"] else "",
    ])
    if tuoi:
        frasi.append(tuoi[0].upper() + tuoi[1:] + ".")
    if rapporto["tuoi_in_scadenza"]:
        frasi.append(f"{conta(rapporto['tuoi_in_scadenza'], 'tuo contratto sta', 'tuoi contratti stanno')} per scadere: si rinnovano con Ctrl+Maiusc+K.")
    # Dalla tappa 13, progetto 4.5, lo staff delle tue polisportive.
    frasi.extend(_fatti_dello_staff(rapporto))
    # Dalla tappa 12 i tornei e le sfide: le notizie dei tuoi, le sfide che aspettano e i numeri del mondo.
    frasi.extend(rapporto.get("notizie") or [])
    # Dalla tappa 13, risposta 38, gli allenatori nuovi riservati a te, se ci sono.
    if rapporto.get("riservati"):
        frasi.append(rapporto["riservati"])
    if rapporto.get("sfide_decadute"):
        frasi.append(f"{conta(rapporto['sfide_decadute'], 'sfida alle tue polisportive è decaduta', 'sfide alle tue polisportive sono decadute')} senza risposta.")
    if rapporto.get("sfide_in_attesa"):
        frasi.append(f"{conta(rapporto['sfide_in_attesa'], 'sfida aspetta', 'sfide aspettano')} la tua risposta entro oggi, prima dell'avanzamento seguente.")
    gare = unisci([
        conta(rapporto["tornei_conclusi"], "torneo concluso", "tornei conclusi") if rapporto.get("tornei_conclusi") else "",
        conta(rapporto["incontri_torneo"], "incontro di torneo", "incontri di torneo") if rapporto.get("incontri_torneo") else "",
        conta(rapporto["sfide_giocate"], "sfida fra polisportive", "sfide fra polisportive") if rapporto.get("sfide_giocate") else "",
    ])
    if gare:
        frasi.append(f"Nel mondo: {gare}.")
    if persone:
        frasi.append(persone[0].upper() + persone[1:] + ".")
    if mercato:
        frasi.append(f"Le polisportive del computer {mercato}.")
    scaduti_cpu = rapporto["contratti_scaduti"] - rapporto["tuoi_scaduti"]
    if rapporto["rinnovi_cpu"] or scaduti_cpu:
        rinnovati = f"hanno rinnovato {conta(rapporto['rinnovi_cpu'], 'contratto', 'contratti')}" if rapporto["rinnovi_cpu"] else "non hanno rinnovato contratti"
        lasciati = f" e ne hanno lasciati scadere {scaduti_cpu}" if scaduti_cpu else ""
        frasi.append(f"Le polisportive del computer {rinnovati}{lasciati}.")
    if nascite:
        frasi.append(nascite[0].upper() + nascite[1:] + ".")
    return " ".join(frasi) or "Non è successo niente di particolare."


def _fatti_dello_staff(rapporto):
    """Le notizie dello staff dell'utente in un avanzamento: chi se n'è andato, chi è tornato libero, chi è uscito, la prelazione e le scadenze."""
    frasi = []
    usciti = unisci([
        conta(rapporto["tuo_staff_partito"], "allenatore del tuo staff se n'è andato senza stipendio", "allenatori del tuo staff se ne sono andati senza stipendio")
        if rapporto.get("tuo_staff_partito") else "",
        conta(rapporto["tuo_staff_scaduto"], "allenatore del tuo staff è tornato libero a fine contratto", "allenatori del tuo staff sono tornati liberi a fine contratto")
        if rapporto.get("tuo_staff_scaduto") else "",
        conta(rapporto["tuo_staff_uscito"], "allenatore del tuo staff ha smesso o è uscito di scena", "allenatori del tuo staff hanno smesso o sono usciti di scena")
        if rapporto.get("tuo_staff_uscito") else "",
    ])
    if usciti:
        frasi.append(f"{usciti[0].upper()}{usciti[1:]}: lo staff si guarda con Ctrl+H.")
    if rapporto.get("tue_prelazioni"):
        n = rapporto["tue_prelazioni"]
        # La scadenza vera, la prima se sono più d'uno: dopo un recupero lungo i dieci giorni possono essere già in parte passati.
        fino = rapporto.get("prelazione_fino")
        quando = f" {'almeno ' if n > 1 else ''}fino al {data_breve(fino)}" if fino else ""
        frasi.append(f"{conta(n, 'tuo tesserato ritirato può', 'tuoi tesserati ritirati possono')} allenare: puoi {'assumerlo' if n == 1 else 'assumerli'} "
                     f"prima degli altri{quando}, dal mercato degli allenatori con Ctrl+Maiusc+G.")
    if rapporto.get("tuo_staff_in_scadenza"):
        frasi.append(f"{conta(rapporto['tuo_staff_in_scadenza'], 'contratto del tuo staff sta', 'contratti del tuo staff stanno')} per scadere: si rinnovano con Ctrl+H.")
    return frasi


def riepilogo_avanzamento(rapporto):
    if not rapporto or not rapporto["ticks"]:
        return "In questa sessione il mondo non è ancora avanzato."
    return f"Ultimo avanzamento, il {data_lunga(rapporto['ora'])}: il mondo è andato avanti di {conta(rapporto['giorni'], 'giorno simulato', 'giorni simulati')}. {_fatti_avanzamento(rapporto)}"


# La barra di stato.

def _entro(testo, larghezza=LARGHEZZA_BARRA):
    return testo[:larghezza]


def righe_barra(mondo, ultimo, ora):
    """
    Le quattro righe della barra di stato, a codici, ciascuna entro quaranta caratteri. Dalla decisione
    11 di Gabriele del 14 ottobre 2026 la seconda dice anche, con d, quante sfide restano da lanciare,
    e il nome della polisportiva si accorcia perché la riga resti nei quaranta caratteri.
    """
    mancano = mondo.prossimo_avanzamento() - ora
    minuti = max(0, int(mancano.total_seconds() // 60))
    tempo = f"s{mondo.datetime_corrente_simulazione:%d/%m/%Y %H:%M} a{minuti // 60}h{minuti % 60:02d}m"
    p = mondo.miapolisportiva_attiva
    if p is None:
        club = "nessuna polisportiva attiva"
    else:
        codici = (f" g{p.gloria} t{len(p.tesserati)}/{p.maxtesserati} m{LIMITE_MOVIMENTI_PER_TICK - p.movimenti_oggi} c{p.cassa // 1000}"
                  f" d{sfide.disponibili(mondo, p)}")
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
    elif "spesa" in voce:
        fatto = spesa_nel_diario(voce)
    elif "anno" in voce:
        return voce_aggregata(voce)
    else:
        fatto = voce["testo"]
    return f"{data_breve(voce['data'])}: {fatto}"


def _medaglie_a_parole(voce, prefisso=""):
    """Le medaglie di una voce aggregata, a parole: un oro e due bronzi; vuota se non ce ne sono."""
    nomi = (("ori", "un oro", "ori"), ("argenti", "un argento", "argenti"), ("bronzi", "un bronzo", "bronzi"), ("legni", "un legno", "legni"))
    return unisci([singolare if voce[prefisso + campo] == 1 else f"{voce[prefisso + campo]} {plurale}" for campo, singolare, plurale in nomi if voce[prefisso + campo]])


def voce_aggregata(voce):
    """
    La voce aggregata dell'anno, tappa 12, punto 5.11: Nel 2031, dal 3 marzo al 9 ottobre, ha giocato
    6 tornei, 25 incontri, 14 vinti, con un oro e due bronzi, e 9 sfide, 5 vinte. Per le polisportive
    del computer le iscrizioni, i tornei, le medaglie, i premi e le sfide.
    """
    periodo = f"Nel {voce['anno']}, dal {data_breve(voce['da'])} al {data_breve(voce['data'])}"
    if "incontri" in voce:
        parti = []
        if voce["tornei"]:
            parti.append(f"{conta(voce['tornei'], 'torneo', 'tornei')}, {conta(voce['incontri'], 'incontro', 'incontri')}, "
                         f"{conta(voce['vinti'], 'vinto', 'vinti')}")
        medaglie = _medaglie_a_parole(voce)
        testo = f"{periodo}, ha giocato " + (unisci(parti) if parti else "nessun torneo")
        if medaglie:
            testo += f", con {medaglie}"
        if voce["sfide"]:
            testo += f", e {conta(voce['sfide'], 'sfida', 'sfide')}, {conta(voce['sfide_vinte'], 'vinta', 'vinte')}"
        return testo + "."
    testo = f"{periodo}, {conta(voce['iscrizioni'], 'iscrizione', 'iscrizioni')} ai tornei, {conta(voce['tornei'], 'torneo concluso', 'tornei conclusi')}"
    medaglie = _medaglie_a_parole(voce)
    if medaglie:
        testo += f", medaglie: {medaglie}"
    if voce["premi"]:
        testo += f", premi per {euro(voce['premi'])}"
    if voce["sfide"]:
        testo += f", {conta(voce['sfide'], 'sfida', 'sfide')}, {conta(voce['sfide_vinte'], 'vinta', 'vinte')}"
    coppe = unisci([f"{conta(voce[campo], 'coppa', 'coppe')} {colore}" for campo, colore in (("coppe_oro", "d'oro"), ("coppe_argento", "d'argento"),
                                                                                              ("coppe_bronzo", "di bronzo"), ("coppe_legno", "di legno")) if voce[campo]])
    if coppe:
        testo += f", {coppe}"
    return testo + "."


# I tornei, tappa 12, punto 12.12: i testi minimi dell'interfaccia testuale, che serviranno anche alla
# finestra del passo 3. Gli incontri dei tuoi ancora da ascoltare non dicono il risultato, risposta 18;
# le classifiche dicono comunque chi va avanti.

NOMI_DEL_TABELLONE = {2: "finale", 4: "semifinali", 8: "quarti", 16: "ottavi", 32: "sedicesimi", 64: "trentaduesimi"}


def edizione_in_calendario(ed, tuoi=0):
    """
    Un'edizione con le iscrizioni aperte: «Open maschile del martedì, dal 6 ottobre 2026, edizione 57:
    25 iscritti, 2 tuoi; quota 10 euro.» Per la coppa le polisportive qualificate, e se c'è la tua.
    """
    testa = f"{ed.nome}, dal {data_breve(ed.data_inizio)}, edizione {ed.numero}"
    if not ed.individuale:
        testo = f"{testa}: {conta(len(ed.iscritti), 'polisportiva qualificata', 'polisportive qualificate')}"
        return testo + (", la tua compresa." if tuoi else ".")
    testo = f"{testa}: {conta(len(ed.iscritti), 'iscritto', 'iscritti')}"
    if tuoi:
        testo += f", {conta(tuoi, 'tuo', 'tuoi')}"
    if ed.qualificazione != modelli_torneo.NESSUNA:
        return testo + ", convocati per i punti dell'ultimo anno."
    return testo + (f"; quota {euro(ed.quota)}." if ed.quota else "; iscrizione gratuita.")


def fase_a_parole(torneo):
    """La fase in corso di una sede: «girone unico», «4 gironi, turno 2», «tabellone, quarti»; «concluso» alla fine."""
    if torneo.stato != tornei.IN_CORSO:
        return "concluso"
    fase = torneo.fasi[torneo.fase_corrente]
    if fase.tipo == formule.GIRONI:
        gironi = "girone unico" if len(fase.gironi) == 1 else f"{len(fase.gironi)} gironi"
        return f"{gironi}, turno {min(fase.turno_corrente, fase.turni)}"
    rimasti = fase.grandezza // 2 ** (min(fase.turno_corrente, fase.turni) - 1)
    return f"tabellone, {NOMI_DEL_TABELLONE.get(rimasti, f'turno {fase.turno_corrente}')}"


def torneo_in_elenco(torneo, tuoi=0):
    """Una sede nell'elenco: «Open maschile del sabato, sede 3, dal 18 ottobre 2026: tabellone, quarti; 2 tuoi atleti.»"""
    testo = f"{torneo.modello['nome']}, sede {torneo.sede}, dal {data_breve(datetime.date.fromisoformat(torneo.data_inizio))}: {fase_a_parole(torneo)}"
    if tuoi:
        testo += f"; {conta(tuoi, 'tuo atleta', 'tuoi atleti')}" if not torneo.squadre else "; con la tua polisportiva"
    return testo + "."


def _nome_corto(torneo, gid):
    """Il nome di un iscritto negli incontri: il cognome del giocatore, il nome della polisportiva nella coppa."""
    nome = torneo.info[gid]["nome"]
    return nome if torneo.squadre else nome.partition(" ")[2] or nome


def classifica_del_girone(torneo, fase, lettera):
    """La classifica di un girone, una riga per iscritto: «1. Mario Rossi, PoliTeam04, 3 vinte, set 6 a 1, punti 77 a 40»."""
    conti = tornei.statistiche_del_girone(fase, lettera)
    righe = []
    for posto, gid in enumerate(tornei.classifica_girone(torneo, fase, lettera), start=1):
        vinte, set_vinti, set_persi, fatti, subiti = conti[gid]
        info = torneo.info[gid]
        club = f", {info['club']['nome']}" if info.get("club") and not torneo.squadre else ""
        righe.append(f"{posto}. {info['nome']}{club}, {conta(vinte, 'vinta', 'vinte')}, set {set_vinti} a {set_persi}, punti {fatti} a {subiti}")
    return righe


def incontro_in_elenco(torneo, incontro, mostra=False):
    """
    Un incontro di una sede: «Turno 2, 18 ottobre 2026: Rossi contro Bianchi, 2 a 1: 11 a 8, 9 a 11, 11
    a 6», oppure da giocare, a tavolino, per ritiro. Un incontro dei tuoi ancora da ascoltare, cioè
    con la differita e non ancora svelato, dice soltanto «tuo, giocato, da ascoltare», risposta 18, a
    meno di mostrarlo lo stesso.
    """
    testa = nome_del_turno(torneo, incontro).capitalize() if incontro.gruppo == tornei.TABELLONE else f"Girone {incontro.gruppo}, turno {incontro.turno}"
    if incontro.data:
        testa += f", {data_breve(datetime.date.fromisoformat(incontro.data))}"
    a = _nome_corto(torneo, incontro.a)
    if incontro.b is None:
        return f"{testa}: {a} riposa."
    b = _nome_corto(torneo, incontro.b)
    if not incontro.giocato:
        return f"{testa}: {a} contro {b}, da giocare."
    if incontro.differita and not incontro.svelato and not mostra:
        return f"{testa}: {a} contro {b}, tuo, giocato, da ascoltare."
    if incontro.esito == tornei.TAVOLINO_DOPPIO:
        return f"{testa}: {a} contro {b}, nessuno dei due si presenta."
    vincitore = a if incontro.vince == "A" else b
    if incontro.esito == tornei.TAVOLINO:
        return f"{testa}: {a} contro {b}, vince {vincitore} a tavolino."
    set_a, set_b, _punti_a, _punti_b = incontro.set_e_punti()
    parziali = ", ".join(f"{x} a {y}" for x, y in incontro.set)
    ritiro = ", per ritiro" if incontro.esito == tornei.RITIRO else ""
    return f"{testa}: {a} contro {b}, {set_a} a {set_b}{ritiro}: {parziali}."


def voce_dell_albo(albo, voce):
    """
    Una voce dell'albo d'oro: «Open maschile del sabato, edizione 57, sede 3, 18 ottobre 2026, 25
    iscritti: oro Mario Rossi, PoliTeam04; argento ...»; per la coppa i club; l'edizione non disputata.
    """
    modello, tipo, _sesso, _importanza, data, numero, sede, iscritti, podio, _premi = voce
    testa = f"{albo.nome_del_modello(modello)}, edizione {numero}"
    if sede:
        testa += f", sede {sede}"
    testa += f", {data_breve(datetime.date.fromisoformat(data))}"
    squadre = tipo == "squadre"
    partecipanti = conta(iscritti, "polisportiva", "polisportive") if squadre else conta(iscritti, "iscritto", "iscritti")
    if not podio:
        return f"{testa}: edizione non disputata, con {partecipanti}."
    return f"{testa}, {partecipanti}: " + "; ".join(_posti_del_podio(albo, voce)) + "."


def _posti_del_podio(albo, voce):
    """I posti del podio di una voce dell'albo, uno per medaglia: «oro Mario Rossi, PoliTeam04», o la polisportiva nella coppa."""
    parti = []
    for medaglia, posto in zip(palmares.MEDAGLIE, voce[8], strict=False):
        if voce[1] == "squadre":
            chi = albo.club[posto][0] if posto is not None else "una polisportiva"
        else:
            gid, club = posto
            nome, cognome = albo.giocatori[str(gid)]
            chi = f"{nome} {cognome}" + (f", {albo.club[club][0]}" if club is not None else "")
        parti.append(f"{medaglia} {chi}")
    return parti


# La finestra dei tornei, tappa 12, passo 3, punto 12 del progetto: i testi del calendario, del
# pannello, dell'albo, della classifica mondiale, degli editor e delle sfide. Sono funzioni pure come
# le altre, e la finestra le mostra negli elenchi e nella vista principale.

SESSI_DEI_TORNEI = {"m": "maschile", "f": "femminile", "aperto": "aperto a tutti", None: "a squadre"}
# Dove si esce dal tabellone, a parole, per la classifica generale di un torneo in corso.
USCITE_DAL_TABELLONE = {2: "in finale", 4: "in semifinale", 8: "ai quarti", 16: "agli ottavi", 32: "ai sedicesimi", 64: "ai trentaduesimi"}
MEDAGLIE_A_PAROLE = {"oro": "medaglia d'oro", "argento": "medaglia d'argento", "bronzo": "medaglia di bronzo", "legno": "medaglia di legno"}
COPPE_A_PAROLE = {"oro": "coppa d'oro", "argento": "coppa d'argento", "bronzo": "coppa di bronzo", "legno": "coppa di legno"}


def nome_del_turno(torneo, incontro):
    """Il turno di un incontro del tabellone a parole: quarti, semifinale, finale, finale per il terzo posto; turno 2 oltre i trentaduesimi."""
    if incontro.finalina:
        return "finale per il terzo posto"
    fase = torneo.fasi[incontro.fase]
    rimasti = fase.grandezza >> (incontro.turno - 1)
    return {2: "finale", 4: "semifinale"}.get(rimasti, NOMI_DEL_TABELLONE.get(rimasti, f"turno {incontro.turno}"))


def _club_dell_iscritto(torneo, gid):
    info = torneo.info[gid]
    return f", {info['club']['nome']}" if info.get("club") and not torneo.squadre else ""


def _vincitore_del_torneo(torneo):
    """Chi ha vinto una sede conclusa, col nome che aveva nel torneo; None se non è conclusa."""
    if torneo.stato != tornei.CONCLUSO or not torneo.classifica_finale:
        return None
    return torneo.info[torneo.classifica_finale[0]]["nome"]


def riga_del_pannello(torneo, tuoi=0):
    """Una sede nell'elenco del pannello: in corso con la fase, o conclusa con chi l'ha vinta, e i tuoi atleti."""
    testo = torneo_in_elenco(torneo, tuoi)
    vincitore = _vincitore_del_torneo(torneo)
    if vincitore:
        testo = testo.replace(": concluso", f": concluso, vince {vincitore}", 1)
    return testo


def testata_del_pannello(in_corso, con_i_tuoi, conclusi):
    """In testa al pannello: Tornei in corso 12, 2 con i tuoi atleti; conclusi di recente 30."""
    return f"Tornei in corso: {in_corso}, {con_i_tuoi} con i tuoi atleti. Conclusi negli ultimi 14 giorni: {conclusi}."


def parti_del_torneo(torneo, con_i_tuoi=False):
    """
    Le parti di una sede, nel pannello: la classifica generale, i tuoi incontri se ci sono, i gironi di
    ogni fase a gironi e il tabellone; come coppie di testo e chiave, la chiave come la vuole classifica_della_parte.
    """
    parti = [("Classifica generale", ("generale", None, None))]
    if con_i_tuoi:
        parti.append(("I tuoi incontri", ("tuoi", None, None)))
    piu_fasi = sum(1 for f in torneo.fasi if f.tipo == formule.GIRONI) > 1
    for fase in torneo.fasi:
        if fase.tipo == formule.GIRONI:
            for lettera in fase.gironi:
                testo = f"Fase {fase.indice + 1}, girone {lettera}" if piu_fasi else ("Girone unico" if len(fase.gironi) == 1 else f"Girone {lettera}")
                parti.append((testo, ("girone", fase.indice, lettera)))
        else:
            parti.append(("Tabellone" if not piu_fasi else f"Fase {fase.indice + 1}, tabellone", ("tabellone", fase.indice, None)))
    return parti


def _eliminati(torneo):
    """Chi è uscito da una sede ancora in corso, con dove, nell'ordine inverso dell'uscita: per la classifica generale provvisoria."""
    usciti = []
    for fase in torneo.fasi:
        if fase.tipo == formule.GIRONI:
            if not fase.finita or fase.ultima:
                continue
            for lettera in fase.gironi:
                ordine = tornei.classifica_girone(torneo, fase, lettera)
                for posto, gid in enumerate(ordine[fase.per_girone:], start=fase.per_girone + 1):
                    usciti.append((gid, f"fuori nel girone {lettera}, {posto}°"))
            continue
        for incontro in fase.incontri:
            if incontro.giocato and not incontro.finalina:
                sconfitto = torneo.sconfitto(incontro)
                if sconfitto is not None:
                    usciti.append((sconfitto, f"fuori {USCITE_DAL_TABELLONE.get(fase.grandezza >> (incontro.turno - 1), 'nel tabellone')}"))
    return list(reversed(usciti))


def _righe_generali(torneo):
    """Le righe della classifica generale, ciascuna col suo iscritto: coppie di identificativo e testo."""
    if torneo.stato == tornei.CONCLUSO:
        righe = []
        for posto, gid in enumerate(torneo.classifica_finale, start=1):
            riga = f"{posto}. {torneo.info[gid]['nome']}{_club_dell_iscritto(torneo, gid)}"
            medaglia = palmares.MEDAGLIE[posto - 1] if posto <= len(palmares.MEDAGLIE) else None
            if medaglia:
                riga += f", {(COPPE_A_PAROLE if torneo.squadre else MEDAGLIE_A_PAROLE)[medaglia]}"
            if torneo.premi.get(gid):
                riga += f", premio di {euro(torneo.premi[gid])}"
            righe.append((gid, riga))
        return righe
    if torneo.stato != tornei.IN_CORSO:
        return []
    usciti = _eliminati(torneo)
    fuori = {gid for gid, _dove in usciti}
    righe = [(gid, f"{torneo.info[gid]['nome']}{_club_dell_iscritto(torneo, gid)}, in gara") for gid in torneo.iscritti if gid not in fuori]
    righe.extend((gid, f"{torneo.info[gid]['nome']}{_club_dell_iscritto(torneo, gid)}, {dove}") for gid, dove in usciti)
    return righe


def classifica_generale(torneo):
    """
    La classifica generale di una sede: a torneo concluso il posto di tutti, con le medaglie e i premi;
    in corso chi è ancora in gara, in ordine di testa di serie, e poi chi è uscito, dall'ultimo.
    """
    if torneo.stato not in (tornei.CONCLUSO, tornei.IN_CORSO):
        return ["Torneo annullato."]
    return [riga for _gid, riga in _righe_generali(torneo)]


def classifica_del_tabellone(torneo, fase):
    """
    Il tabellone nel pannello: chi è ancora in gara col suo prossimo incontro; a tabellone finito, chi
    l'ha vinto e chi è arrivato secondo.
    """
    righe = []
    for incontro in sorted(fase.incontri, key=lambda i: (i.turno, i.finalina, i.posto)):
        if incontro.giocato or incontro.b is None:
            continue
        turno = nome_del_turno(torneo, incontro)
        for gid, altro in ((incontro.a, incontro.b), (incontro.b, incontro.a)):
            righe.append(f"{torneo.info[gid]['nome']}{_club_dell_iscritto(torneo, gid)}: prossimo incontro contro {_nome_corto(torneo, altro)}, {turno}")
    if righe:
        return righe
    finale = next((i for i in fase.del_turno(fase.turni) if not i.finalina and i.giocato), None)
    if finale is None:
        return ["Il tabellone non ha ancora incontri."]
    vincitore, secondo = torneo.vincitore(finale), torneo.sconfitto(finale)
    if not fase.ultima:
        return [f"Il tabellone di questa fase è finito: passano {unisci([torneo.info[gid]['nome'] for gid in fase.promossi])}."]
    righe = [f"Il tabellone è finito: vince {torneo.info[vincitore]['nome']}"]
    if secondo is not None:
        righe[0] += f", secondo {torneo.info[secondo]['nome']}"
    righe[0] += "."
    return righe


def classifica_della_parte(torneo, chiave, tuoi=()):
    """Le righe della classifica di una parte del pannello: la generale, i tuoi, un girone o il tabellone."""
    tipo, indice, lettera = chiave
    if tipo == "girone":
        return classifica_del_girone(torneo, torneo.fasi[indice], lettera)
    if tipo == "tabellone":
        return classifica_del_tabellone(torneo, torneo.fasi[indice])
    if tipo == "tuoi":
        righe = [riga for gid, riga in _righe_generali(torneo) if gid in tuoi]
    else:
        righe = classifica_generale(torneo)
    return righe or ["Nessun iscritto."]


def incontri_della_parte(torneo, chiave, tuoi=()):
    """Gli incontri di una parte del pannello, nell'ordine in cui si giocano; per la generale tutti, per i tuoi soltanto i loro."""
    tipo, indice, lettera = chiave
    if tipo == "girone":
        scelti = [i for i in torneo.fasi[indice].incontri if i.gruppo == lettera]
    elif tipo == "tabellone":
        scelti = list(torneo.fasi[indice].incontri)
    elif tipo == "tuoi":
        scelti = [i for i in torneo.incontri() if i.a in tuoi or i.b in tuoi]
    else:
        scelti = torneo.incontri()
    return sorted(scelti, key=lambda i: (i.fase, i.turno, i.finalina, i.gruppo, i.posto))


def risultato_di_un_incontro(torneo, incontro):
    """Il risultato di un incontro dei tuoi da mostrare, quello che l'elenco nasconde finché non si ascolta: la sua riga, svelata."""
    return incontro_in_elenco(torneo, incontro, mostra=True)


# Il calendario e le iscrizioni, punto 12.3.

def testata_del_calendario(p, aperte):
    """In testa al calendario: la cassa della polisportiva attiva e le edizioni aperte."""
    return f"{p.nome}: cassa {euro(p.cassa)}; {conta(aperte, 'edizione aperta', 'edizioni aperte')} alle iscrizioni."


def riga_edizione(ed, tuoi=0):
    """Un'edizione aperta nel calendario, col sesso: Open maschile del martedì, maschile, dal 13 ottobre 2026, edizione 2: 25 iscritti, 2 tuoi; quota 10 euro."""
    testo = edizione_in_calendario(ed, tuoi)
    return testo.replace(f"{ed.nome}, ", f"{ed.nome}, {SESSI_DEI_TORNEI.get(ed.sesso, ed.sesso)}, ", 1)


def riga_edizione_prevista(modello, inizio):
    """Un'edizione dei prossimi giorni che non ha ancora aperto le iscrizioni: quando comincia e quando si apre."""
    apertura = inizio - datetime.timedelta(days=modello.giorni_iscrizione)
    return f"{modello.nome}, {SESSI_DEI_TORNEI.get(modello.sesso, modello.sesso)}, dal {data_breve(inizio)}: le iscrizioni si aprono il {data_breve(apertura)}."


def riga_edizione_in_corso(nome, sesso, inizio, sedi, tuoi=0):
    """Un'edizione già cominciata nel calendario: Open maschile del sabato, maschile, dal 18 ottobre 2026: in corso in 3 sedi, 2 tuoi atleti."""
    testo = f"{nome}, {SESSI_DEI_TORNEI.get(sesso, sesso)}, dal {data_breve(inizio)}: in corso in {conta(sedi, 'sede', 'sedi')}"
    if tuoi:
        testo += f", {conta(tuoi, 'tuo atleta', 'tuoi atleti')}"
    return testo + "."


def _automatica(g):
    if not g.iscrizione_automatica:
        return "automatica spenta"
    return f"automatica dal {data_breve(g.prossimo_torneo)}" if g.prossimo_torneo is not None else "automatica accesa"


def riga_atleta_del_calendario(g, mondo, origine=None, ed=None):
    """
    Un tuo tesserato negli elenchi del calendario: Mario Rossi, D2, acciaccato al ginocchio destro fino
    al 20 ottobre 2026, automatica dal 18 dicembre 2026; per un iscritto anche come, a mano o in automatico;
    con l'edizione, se è un torneo per altri giocatori lo dice.
    """
    parti = [nome_completo(g), codice_classe(g)]
    if ed is not None and ed.individuale and (ed.sesso not in ("aperto", g.sesso) or (ed.filtri and not modelli_torneo.idoneo(ed.oggetto_modello, g))):
        parti.append("non può giocarlo")
    if g.infortunato and g.infortunio_fine_datetime and not g.puo_giocare:
        parti.append(f"{accorda(g, 'infortunato')} fino al {data_breve(g.infortunio_fine_datetime)}")
    testo = acciacco(g, mondo.datetime_corrente_simulazione)
    if testo:
        parti.append(testo.split(":", 1)[0])
    if origine:
        parti.append({"mano": "iscritto a mano", "automatica": "iscritto in automatico", "qualificato": "convocato", "computer": "iscritto dal club",
                      "libero": "iscritto da libero"}.get(origine, origine).replace("iscritto", accorda(g, "iscritto")))
    parti.append(_automatica(g))
    return ", ".join(parti)


def riga_della_rosa(g, mondo, posto):
    """Un giocatore della rosa per la coppa, col suo posto: titolare 1, 2 e 3, poi le riserve."""
    ruolo = f"titolare {posto}" if posto <= 3 else f"riserva {posto - 3}"
    testo = f"{nome_completo(g)}, {codice_classe(g)}, {ruolo}"
    acc = acciacco(g, mondo.datetime_corrente_simulazione)
    return testo + (f", {acc.split(':', 1)[0]}" if acc else "")


def iscrizione_fatta(g, ed, quota):
    return f"{accorda(g, 'Iscritto')} {nome_completo(g)} a {ed.nome} del {data_breve(ed.data_inizio)}" + (f", per {euro(quota)}." if quota else ".")


def iscrizione_tolta(g, ed, rimborso):
    return f"{accorda(g, 'Tolto')} {nome_completo(g)} da {ed.nome} del {data_breve(ed.data_inizio)}" + (f": rimborso di {euro(rimborso)}." if rimborso else ".")


def rosa_iscritta(poli, ed, giocatori):
    return f"Rosa di {poli.nome} per {ed.nome}: {unisci([g.cognome for g in giocatori])}."


def riepilogo_calendario(p, fatte):
    """Il riepilogo del calendario alla chiusura: quante iscrizioni fatte e tolte, poi una riga per operazione."""
    if not fatte:
        return f"Calendario e iscrizioni di {p.nome}: nessuna iscrizione cambiata."
    iscritte = sum(1 for tipo, _testo in fatte if tipo == "iscritto")
    tolte = sum(1 for tipo, _testo in fatte if tipo == "tolto")
    rose = sum(1 for tipo, _testo in fatte if tipo == "rosa")
    parti = [conta(iscritte, "iscrizione", "iscrizioni") if iscritte else "", conta(tolte, "iscrizione tolta", "iscrizioni tolte") if tolte else "",
             conta(rose, "rosa per la coppa", "rose per la coppa") if rose else ""]
    return "\n".join([f"Calendario e iscrizioni di {p.nome}: {unisci(parti)}.", *(testo for _tipo, testo in fatte)])


def evento_calendario(fatte):
    """Il fatto del calendario nella barra: calendario: 2 iscrizioni, 1 tolta."""
    iscritte = sum(1 for tipo, _testo in fatte if tipo in ("iscritto", "rosa"))
    tolte = sum(1 for tipo, _testo in fatte if tipo == "tolto")
    return f"calendario: {conta(iscritte, 'iscrizione', 'iscrizioni')}, {tolte} {'tolta' if tolte == 1 else 'tolte'}"


# L'albo d'oro e la classifica mondiale, punti 12.1 e 5.9.

def anno_della_voce(voce):
    return int(voce[4][:4])


def riga_edizione_dell_albo(albo, voci):
    """Un'edizione nell'albo, dalle voci delle sue sedi: Edizione 57, 18 ottobre 2026: 3 sedi, 75 iscritti; non disputata."""
    prima = voci[0]
    testa = f"Edizione {prima[5]}, {data_breve(datetime.date.fromisoformat(prima[4]))}"
    iscritti = sum(v[7] for v in voci)
    if all(not v[8] for v in voci):
        return f"{testa}: non disputata, con {conta(iscritti, 'iscritto', 'iscritti')}."
    chi = conta(iscritti, "polisportiva", "polisportive") if prima[1] == modelli_torneo.SQUADRE else conta(iscritti, "iscritto", "iscritti")
    return f"{testa}: {conta(len(voci), 'sede', 'sedi')}, {chi}."


def podio_dell_albo(albo, voce):
    """Il podio di una sede nell'albo, senza il nome del modello e l'edizione, che l'elenco ha già: sede 3, 25 iscritti: oro ...; argento ..."""
    testo = voce_dell_albo(albo, voce)
    testa = f"{albo.nome_del_modello(voce[0])}, edizione {voce[5]}, "
    testo = testo.removeprefix(testa)
    return testo[0].upper() + testo[1:]


def riga_della_sede_in_differita(sede):
    """
    Una sede delle ultime edizioni concluse con i tuoi, nel pannello: «Open maschile del sabato,
    edizione 57, sede 3, dal 18 ottobre 2026: 4 incontri dei tuoi, 2 da ascoltare».
    """
    incontri = sede.incontri()
    da_ascoltare = sum(1 for i in incontri if i.giocato and i.differita and not i.svelato)
    testo = f"{sede.modello['nome']}, edizione {sede.numero}, sede {sede.sede}, dal {data_breve(datetime.date.fromisoformat(sede.data_inizio))}: "
    testo += conta(len(incontri), "incontro dei tuoi", "incontri dei tuoi")
    return testo + (f", {da_ascoltare} da ascoltare." if da_ascoltare else ", tutti già ascoltati o mostrati.")


def voce_della_sede_in_differita(albo, sede):
    """La voce dell'albo d'oro della sede delle differite: lo stesso modello, la stessa edizione e la stessa sede; None se non c'è."""
    for voce in reversed(albo.voci):
        if albo.id_del_modello(voce[0]) == sede.modello["id"] and voce[5] == sede.numero and voce[6] == sede.sede:
            return voce
    return None


def podio_della_sede_in_differita(albo, sede):
    """Il podio della sede delle differite, dall'albo d'oro: una riga per posto, «oro Mario Rossi, PoliTeam04»."""
    voce = voce_della_sede_in_differita(albo, sede)
    if voce is None or not voce[8]:
        return ["Il podio di questa sede non è nell'albo d'oro."]
    return _posti_del_podio(albo, voce)


def classifica_mondiale(mondo, quanti=100, tuoi=()):
    """
    La classifica mondiale per sempre, come un medagliere storico, D32 e punto 5.9: gli uomini e poi
    le donne, i primi cento con posto, nome, punti, ori, argenti, bronzi e titoli mondiali, e sotto i tuoi
    tesserati che stanno più in basso, col loro posto.
    """
    righe = ["Classifica mondiale per sempre, come un medagliere storico: i punti di tutti i tornei giocati, vecchie glorie comprese."]
    for sesso, titolo, singolare, plurale in (("m", "Uomini", "giocatore", "giocatori"), ("f", "Donne", "giocatrice", "giocatrici")):
        elenco = palmares.classifica_mondiale(mondo, sesso)
        if not elenco:
            righe.append(f"{titolo}: ancora nessuno in classifica.")
            continue
        righe.append(f"{titolo}: {conta(len(elenco), singolare + ' in classifica', plurale + ' in classifica')}, ecco i primi {min(quanti, len(elenco))}.")
        sotto = []
        for posto, riga in enumerate(elenco, start=1):
            if posto <= quanti:
                righe.append(_riga_mondiale(posto, riga, riga["id"] in tuoi))
            elif riga["id"] in tuoi:
                sotto.append(_riga_mondiale(posto, riga, True))
        if sotto:
            righe.append(f"I tuoi tesserati più in basso: {len(sotto)}.")
            righe.extend(sotto)
    return "\n".join(righe)


def _riga_mondiale(posto, riga, tuo):
    testo = (f"{posto}. {riga['nome']}, {numero(riga['punti'])} punti, ori {riga['ori']}, argenti {riga['argenti']}, bronzi {riga['bronzi']}, "
             f"titoli mondiali {riga['titoli']}")
    if not riga["vivo"]:
        testo += ", vecchia gloria"
    if tuo:
        testo += ", tuo tesserato"
    return testo


# Gli editor dei modelli e delle formule, punto 12.5, sul modello di generate_formula_summary di Terminal Beast.

def ricorrenza_a_parole(ricorrenza):
    """La ricorrenza di un modello a parole: ogni martedì; il 15 di ogni mese; ogni anno il 10 dicembre."""
    if ricorrenza["tipo"] == modelli_torneo.SETTIMANALE:
        return f"ogni {modelli_torneo.nome_del_giorno(ricorrenza['giorno'])}"
    if ricorrenza["tipo"] == modelli_torneo.MENSILE:
        return f"il {ricorrenza['giorno']} di ogni mese"
    return f"ogni anno il {ricorrenza['giorno']} {modelli_torneo.nome_del_mese(ricorrenza['mese'])}"


def riga_modello(modello):
    """Un modello nell'editor: Open maschile del martedì, maschile, ogni martedì, attivo."""
    stato = "attivo" if modello.attivo else "fermo"
    return f"{modello.nome}, {SESSI_DEI_TORNEI.get(modello.sesso, modello.sesso)}, {ricorrenza_a_parole(modello.ricorrenza)}, {stato}"


def riga_fase(fase, indice):
    """Una fase nell'editor delle formule: Fase 1: gironi, 32 partecipanti in 8 gironi da 4, passano 2 per girone."""
    if fase["tipo"] == formule.GIRONI:
        grandezza = fase["partecipanti"] // max(1, fase["gironi"])
        gironi = "un girone unico" if fase["gironi"] == 1 else f"{fase['gironi']} gironi da {grandezza}"
        testo = f"Fase {indice + 1}: gironi, {fase['partecipanti']} partecipanti in {gironi}"
        return testo + (f", passano {fase['promossi']} per girone" if fase["promossi"] else "")
    testo = f"Fase {indice + 1}: tabellone da {fase['partecipanti']}"
    return testo + (", con la finalina per il terzo posto" if fase["finalina"] else "")


def riepilogo_formula(formula, modello=None):
    """
    Il riassunto di una formula per l'editor dei modelli, copiato da generate_formula_summary di
    Terminal Beast senza pareggi e senza maiuscole gridate: le fasi, quanti iscritti per sede, e con il
    modello i giorni di gioco e i set.
    """
    if formula is None:
        return "La formula del modello non c'è, o non è valida: se ne sceglie un'altra."
    righe = [f"Formula {formula['nome']}" + (f": {formula['descrizione']}" if formula.get("descrizione") else ".")]
    righe.append(f"{conta(len(formula['fasi']), 'fase', 'fasi')}: " + "; ".join(riga_fase(f, i)[len(f'Fase {i + 1}: '):] for i, f in enumerate(formula["fasi"])) + ".")
    tetto = formule.tetto(formula)
    if modello is not None:
        righe.append(f"Ogni sede ha al massimo {tetto} iscritti e almeno {modello.minimo_iscritti}; con più iscritti l'edizione si divide in sedi parallele.")
        durata = modelli_torneo.durata_prevista(modello, formula)
        righe.append(f"Si gioca in {conta(durata, 'giorno', 'giorni')} al massimo, {conta(modello.incontri_al_giorno, 'turno', 'turni')} al giorno.")
        finali = {0: "", 2: "la finale", 4: "dalle semifinali", 8: "dai quarti"}[modello.finali_da]
        if modello.tipo == modelli_torneo.SQUADRE:
            righe.append("Ogni incontro è una gara a squadre, un set a 31 punti.")
        elif finali and modello.set_finali != modello.set_al_meglio:
            righe.append(f"Gli incontri si giocano al meglio dei {modello.set_al_meglio} set, {finali} al meglio dei {modello.set_finali}.")
        else:
            righe.append(f"Gli incontri si giocano al meglio dei {modello.set_al_meglio} set.")
    else:
        righe.append(f"Ogni sede ha al massimo {tetto} iscritti.")
    return " ".join(righe)


def edizioni_al_mese(modello):
    """Quante edizioni apre il modello in un mese simulato, in media: un settimanale circa quattro, un mensile una, un annuale un dodicesimo."""
    return {modelli_torneo.SETTIMANALE: 30 / 7, modelli_torneo.MENSILE: 1.0, modelli_torneo.ANNUALE: 1 / 12}[modello.ricorrenza["tipo"]]


def riepilogo_premi(modello, formula):
    """
    I premi stimati di una sede piena, per l'editor: il montepremi, quanto va ai primi quattro, la
    percentuale al primo, e quanto denaro nuovo la federazione mette in un mese, una sede per edizione.
    """
    if formula is None:
        return ""
    tetto = formule.tetto(formula)
    if modello.tipo == modelli_torneo.SQUADRE:
        quote = 0
    else:
        quote = modello.quota_iscrizione * tetto
    montepremi = tornei.montepremi(modello.a_dizionario(), tetto if quote else 0)
    if montepremi <= 0:
        return "Nessun premio in euro: si gioca per le medaglie, o per le coppe."
    premi = tornei.calcola_premi(montepremi, min(modello.posti_premiati, tetto), modello.pendenza_premi, tetto)
    primi = "; ".join(f"{posto}° {euro(premio)}" for posto, premio in enumerate(premi[:4], start=1))
    percentuale = tornei.prima_percentuale(modello.pendenza_premi, min(modello.posti_premiati, tetto))
    nuovo = max(0, montepremi - quote)
    testo = (f"Una sede piena paga {euro(quote)} di quote e ha un montepremi di {euro(montepremi)}, diviso fra i primi {len(premi)}: {primi}; "
             f"al primo va {con_articolo('il', percento(percentuale))}.")
    return testo + f" La federazione mette {euro(nuovo)} di denaro nuovo per sede piena, circa {euro(round(nuovo * edizioni_al_mese(modello)))} al mese con una sede per edizione."


# Le sfide, punto 12.6.

def forza_a_parole(forza):
    """La forza di una squadra nell'esito rapido, con due decimali: 0,62."""
    return "nessuna squadra valida" if forza is None else f"forza {numero(forza, 2)}"


def riga_bersaglio(dati):
    """Una polisportiva del computer da sfidare: PoliTeam04, forza 0,62, gloria 140, ultima sfida il 3 ottobre 2026."""
    testo = f"{dati['nome']}, {forza_a_parole(dati['forza'])}, gloria {dati['gloria']}"
    if dati["ultima_sfida"] is not None:
        testo += f", ultima sfida il {data_breve(dati['ultima_sfida'])}"
    return testo


def riga_sfida_in_arrivo(s, forza):
    """
    Una sfida che aspetta la tua risposta: PoliTeam04 sfida Club Di Prova, forza 0,58; rispondi entro
    il 14 ottobre 2026, cioè l'ultimo giorno in cui la proposta aspetta, non quello della scadenza.
    """
    return f"{s.sfidante['nome']} sfida {s.sfidata['nome']}, {forza_a_parole(forza)}; rispondi entro il {data_breve(sfide.ultimo_giorno_per_rispondere(s))}"


def riga_dello_storico(s, mondo):
    """Una sfida dello storico delle tue polisportive, dal punto di vista della tua: con chi, come è finita, quando, e se si riascolta."""
    tue = [lato for lato in ("sfidante", "sfidata") if (p := mondo.polisportive.get(s.club(lato)["nome"])) is not None and not p.is_cpu_controlled]
    mia = tue[0] if tue else "sfidante"
    altra = "sfidata" if mia == "sfidante" else "sfidante"
    quando = data_breve(s.data_gioco or s.lancio)
    testa = f"{quando}: {s.club(mia)['nome']} contro {s.club(altra)['nome']}"
    if s.stato == "rifiutata":
        return f"{testa}, rifiutata" + (" da te" if mia == "sfidata" else "")
    if s.stato == "decaduta":
        return f"{testa}, decaduta"
    if s.risultato is None:
        return f"{testa}, {s.stato}"
    vinta = s.risultato["vince"] == mia
    punti = s.risultato["punti"]
    mio, suo = (punti[0], punti[1]) if mia == "sfidante" else (punti[1], punti[0])
    if s.risultato["esito"] == "tavolino":
        testo = f"{testa}, {'vinta' if vinta else 'persa'} a tavolino"
    else:
        testo = f"{testa}, {'vinta' if vinta else 'persa'} {mio} a {suo}"
    cognomi = [mondo.giocatori[gid].cognome for gid in s.risultato.get("titolari", [[], []])[("sfidante", "sfidata").index(mia)] if gid in mondo.giocatori]
    if cognomi:
        testo += f", con {unisci(cognomi)}"
    return testo + ("; si ascolta in differita" if s.differita else "")


def riga_convocabile(g, mondo):
    """Un convocabile della formazione: Mario Rossi, D2, uomo, acciaccato."""
    testo = f"{nome_completo(g)}, {codice_classe(g)}, {'uomo' if g.sesso == 'm' else 'donna'}"
    if infortuni.calo_acciacco(g, mondo.datetime_corrente_simulazione) > 0:
        testo += f", {accorda(g, 'acciaccato')}"
    if g.infortunato and not g.puo_giocare:
        testo += f", {accorda(g, 'infortunato')}"
    return testo


def convocabili_insufficienti(quanti):
    """Il perché della formazione impossibile: troppo pochi tesserati possono giocare quel giorno."""
    chi = {0: "nessun tesserato può giocare", 1: "soltanto un tesserato può giocare"}.get(quanti, f"soltanto {quanti} tesserati possono giocare")
    return f"Quel giorno {chi}, senza altri impegni: per una squadra ne servono tre, due di un sesso e uno dell'altro."


def stato_della_formazione(problema, titolari=()):
    """La riga di stato della formazione: valida, con chi va al tavolo, o il perché no."""
    if problema:
        return f"Formazione non valida: {problema}"
    return f"Formazione valida: al tavolo {unisci([g.cognome for g in titolari])}." if titolari else "Formazione valida."


def testata_del_lancio(p, disponibili):
    return f"{p.nome}: {conta(disponibili, 'sfida da lanciare', 'sfide da lanciare')} questo mese. La sfida accettata si gioca all'avanzamento di domani."


# Il calendario che non si legge, punto 12.10.

def calendario_illeggibile(problemi):
    """Il perché, nella vista all'avvio, quando un modello o una formula dei tornei non si leggono, e cosa fare."""
    return (f"Il calendario dei tornei ha {conta(len(problemi), 'problema', 'problemi')}: " + " ".join(p if p.endswith(".") else p + "." for p in problemi)
            + " Il mondo apre soltanto le edizioni dei modelli validi. Si corregge con l'editor dei modelli, Ctrl+Maiusc+J, con quello delle formule, "
            "Ctrl+Maiusc+Y, oppure rimettendo il calendario predefinito dal menu Tornei.")


def spesa_nel_diario(voce):
    """
    La voce di una spesa d'allenamento: Si allena con 120 punti allenamento: chiusura sinistra da
    14,6 a 15,3, difesa da 10,2 a 10,4; valore da 142,3 a 145,1. Una spesa completa elenca le
    caratteristiche salite di almeno un decimo, e dice quante altre sono salite di meno.
    """
    salite = [s for s in voce["spesa"] if s[2] - s[1] >= 0.1 - 1e-9 or len(voce["spesa"]) == 1]
    altre = len(voce["spesa"]) - len(salite)
    parti = [f"{nome_caratteristica(nome).lower()} {da_a(da, a)}" for nome, da, a in salite]
    if altre:
        parti.append(f"{conta(altre, 'altra caratteristica', 'altre caratteristiche')} di meno")
    da, a = voce["valore"]
    return f"Si allena con {quanti_punti(voce['punti'], True)}: {unisci(parti)}; valore {da_a(da, a)}."


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


def diario_allenatore(a):
    return _diario(f"Diario di {nome_completo(a)}, {'allenatrice' if a.sesso == 'f' else 'allenatore'}", a.diario)


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
    return f"Le voci dei diari dei giocatori e degli allenatori si conservano {per(c['giocatori'])}, quelle delle polisportive {per(c['polisportive'])}."


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
    # Dalla tappa 13, D33 risposta 16: all'aggiornamento al formato 8 nasce lo staff, e il mercato degli allenatori è aperto.
    if getattr(mondo, "staff_appena_nato", False):
        righe.append(staff_appena_nato(mondo))
    righe.append("Premi F1 per la guida ai comandi.")
    return "\n".join(righe)


def staff_appena_nato(mondo):
    """La notizia dell'aggiornamento al formato 8: lo staff, gli allenatori nati e la loro ora riservata all'utente."""
    liberi = sum(1 for a in mondo.allenatori.values() if a.libero)
    if liberi == 0:
        mercato = "per ora senza allenatori liberi"
    elif liberi == 1:
        mercato = "con 1 allenatore libero, e per due ore è riservato a te, prima del computer"
    else:
        mercato = f"con {liberi} allenatori liberi, e per due ore sono riservati a te, prima del computer"
    return (f"Novità: ogni polisportiva può avere uno staff, un capo allenatore e due assistenti, che allenano meglio, riducono gli infortuni "
            f"e fanno crescere la fedeltà. Le tue polisportive partono senza: il mercato degli allenatori è aperto, {mercato}. "
            "Lo staff è nel menu Polisportive, con Ctrl+H; il mercato degli allenatori con Ctrl+Maiusc+G.")


def salvataggio_illeggibile(errore):
    """Le frasi che spiegano perché il gioco si ferma quando il salvataggio non si legge."""
    righe = [f"Il salvataggio c'è ma non si può leggere: {errore}."]
    if getattr(errore, "cartella", None):
        righe.append(f"Una copia dei file è nella cartella {errore.cartella}.")
    righe.append("Per non coprirli con un mondo nuovo, il gioco si ferma qui senza salvare nulla.")
    return righe


def somma_rapporti(primo, secondo):
    """
    Due riepiloghi di avanzamento sommati, con l'ora del secondo: il totale di una sessione. Dalla
    tappa 12 le notizie si accodano, e le sfide in attesa sono quelle della fine del secondo.
    """
    ultimi = ("ora", "sfide_in_attesa", "riservati", "prelazione_fino")
    return {chiave: primo[chiave] + secondo[chiave] for chiave in primo if chiave not in ultimi} | {chiave: secondo[chiave] for chiave in ultimi}


def chiusura(durata_sessione, comandi, messaggi, rapporto_sessione=None):
    """Il riepilogo della fine sessione, con ciò che è successo nel mondo durante la sessione."""
    righe = [f"Sessione di {durata(durata_sessione)}, con {conta(comandi, 'comando', 'comandi')}."]
    if rapporto_sessione and rapporto_sessione["ticks"]:
        # Dalla tappa 13 senza gli allenatori riservati: alla chiusura la riserva è quasi sempre scaduta.
        fatti = _fatti_avanzamento(rapporto_sessione | {"riservati": "", "prelazione_fino": None})
        righe.append(f"Nella sessione il mondo è andato avanti di {conta(rapporto_sessione['giorni'], 'giorno simulato', 'giorni simulati')}. {fatti}")
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
    righe.extend((GUIDA_DEI_TORNEI, GUIDA_DELLE_SFIDE))
    righe.extend((LEGENDA_CLASSE, LEGENDA_ALLENAMENTO, LEGENDA_CONTRATTI, LEGENDA_STAFF))
    righe.append(LEGENDA_BARRA)
    return "\n".join(righe)


# La classe, l'allenamento e i contratti nella guida ai comandi, tappa 11, decisione D31.
LEGENDA_CLASSE = (
    "La classe dice a colpo d'occhio quanto vale un giocatore: va da K0, il livello 100, il più debole, ad A1, il livello 1, il più forte. "
    "Il codice è il numero del livello con una lettera al posto delle decine, A per lo zero fino a K per il dieci: la A va da A1 ad A9, "
    "le lettere dalla B alla J da 0 a 9, e la K ha soltanto K0. Conta per il 70% il valore delle caratteristiche, pesate come in partita, "
    "e per il 30% l'esperienza di carriera. La scheda dice anche la percentuale del cammino verso la classe seguente. Le soglie sono fisse per "
    "sempre: A1 è la carriera perfetta, dai 9 ai 50 anni, e chi la supera resta A1; i nati stanno fra la I e la F, i bravi a metà carriera fra la E e la D."
)
LEGENDA_ALLENAMENTO = (
    "L'allenamento si paga in punti allenamento, che vengono dalla seduta di ogni giorno in polisportiva, metà per i liberi, e dalle amichevoli: "
    "un incontro ne dà da 2 a 4,5, con un punto in più al più debole, anche quando perde. Ogni punto compra lo stesso valore a parità di livello, "
    "quindi la precisione, che pesa tanto, sale piano, e le sponde salgono in fretta. Ogni caratteristica può arrivare al tetto, fino a Divino, "
    "ma l'ultimo punto costa dodici volte il primo, e sopra il 70% del tetto i livelli calano un poco ogni mese se non si continuano ad allenare. "
    "I ragazzi imparano un po' più in fretta, gli anziani un po' più piano; il talento, l'apprendista rapido e la maturazione precoce o tardiva sono tratti rari. "
    "Il programma è l'indole secondo cui si spende con l'allenamento completo; l'intensità, leggera, normale o intensa, cambia i punti della seduta, "
    "il rischio d'infortunio, anche in seduta all'intensa, e la costanza recente, cioè quanto si regge la fatica in partita."
)
LEGENDA_CONTRATTI = (
    "Chi entra in una polisportiva firma un contratto: la durata la propone il giocatore, da 4 a 24 mesi, breve da ragazzo e lunga da anziano, "
    "più breve se è ambizioso; lo stipendio resta fisso fino alla scadenza. Negli ultimi tre mesi si può proporre il rinnovo, con stipendio e durata nuovi, "
    "una proposta al giorno e al massimo tre; il giocatore accetta secondo l'offerta, la fedeltà e la gloria della polisportiva, e il contratto nuovo "
    "parte alla scadenza di quello in corso. Chi non rinnova torna libero, e nessuno incassa niente; nella finestra il suo valore di mercato scende, "
    "fino al 40% alla scadenza. Lo svincolo a contratto in corso costa una buonuscita, metà degli stipendi che restano. "
    "Un mese di contratto è un mese del calendario simulato: circa 10 giorni veri."
)


# Lo staff nella guida ai comandi, tappa 13, progetto 4.7.
LEGENDA_STAFF = (
    "Dalla tappa 13 ogni polisportiva può avere uno staff, un capo allenatore e due assistenti, nel dialogo dello staff, Ctrl+H. Lo staff fa imparare "
    "più in fretta, abbassa il rischio d'infortunio in allenamento e in partita e fa crescere prima la fedeltà al club; conta la qualità dello staff, "
    "il 70% dal capo, il 20% dall'assistente migliore e il 10% dall'altro. Rispetto allo staff medio del mondo di quel giorno, senza staff si "
    "impara circa il 15% più piano, col migliore fino al 20% più in fretta, e il mondo nel suo insieme si allena sempre come prima "
    "dello staff; i liberi si allenano senza staff. Gli allenatori sono "
    "ex giocatori arrivati almeno ad H0, che allenano con la classe migliore della carriera, o nati allenatori, adulti con una classe a caso, più rara "
    "quanto più è alta. Il mercato degli allenatori, Ctrl+Maiusc+G, li mostra tutti, dal migliore, coi filtri di classe, età, tipo e sesso. Si assumono "
    "come i giocatori: un ingaggio alla firma, che costa una mossa, uno stipendio fisso, il rinnovo negli ultimi tre mesi e la buonuscita se li "
    "licenzi, anche questo con una mossa. Chi diventa allenatore resta tuo per due ore vere prima che il computer lo veda, e un tuo tesserato che si "
    "ritira e può allenare ti lascia la prelazione per dieci giorni simulati."
)


# I tornei e le sfide nella guida ai comandi, tappa 12, punto 12.11 del progetto.
GUIDA_DEI_TORNEI = (
    "I tornei si giocano da soli, secondo il calendario dei modelli: ogni modello apre le sue edizioni qualche giorno prima, e chi si iscrive gioca in sedi "
    "parallele, divise a serpentina per classe. I tuoi tesserati si iscrivono dal calendario, Ctrl+U, quanto vuoi, oppure in automatico, un torneo ogni due "
    "mesi, con la casella Iscrizione automatica della sala allenamento; il computer e i liberi seguono lo stesso ritmo. Nel calendario si iscrive e si toglie "
    "soltanto coi pulsanti: la quota si paga subito e torna se togli l'iscrizione prima del sorteggio. Le partite dei tuoi si giocano col motore vero anche a "
    "programma chiuso: nel pannello dei tornei, Ctrl+Y, un incontro dei tuoi resta da ascoltare finché non lo ascolti in differita, Invio sull'incontro, non ne "
    "leggi la cronaca o non ne chiedi il risultato; Mostra tutti i risultati li svela tutti insieme, dopo una domanda. Le classifiche e le notizie dicono comunque "
    "chi va avanti. Ogni anno c'è un campionato mondiale per sesso, a cui si è convocati per i punti dell'ultimo anno, e la Coppa delle polisportive a squadre, "
    "per gloria. L'albo d'oro, Ctrl+Maiusc+B, conserva ogni podio per sempre, la classifica mondiale, Ctrl+Maiusc+W, i punti di tutta la carriera. Gli editor "
    "cambiano soltanto le edizioni future, e il calendario predefinito si rimette dal menu Tornei, senza perdere quello di prima."
)
GUIDA_DELLE_SFIDE = (
    "Le sfide fra polisportive sono gare a squadre, un set a 31, con due giocatori di un sesso e uno dell'altro al tavolo e fino a tre riserve. Ogni polisportiva "
    "ne riceve due da lanciare il primo del mese, fino a quattro, e la barra di stato dice con d quante ne restano; si lanciano a una polisportiva del "
    "computer con Ctrl+W, che risponde subito, e quelle che ricevi si accettano o si rifiutano con Ctrl+Maiusc+F entro il giorno in cui arrivano: "
    "all'avanzamento seguente decadono. La formazione proposta si cambia prima di lanciare o di accettare; si lancia soltanto col pulsante Lancia, Alt+L, "
    "e si accetta soltanto con Accetta, Alt+A: Invio sugli elenchi non fa niente. "
    "La sfida si gioca all'avanzamento seguente, e la posta è una coppa, d'oro a chi vince e d'argento a chi perde, che nella gloria vale poco. Lo storico, "
    "Ctrl+Maiusc+H, fa riascoltare e leggere le ultime dieci."
)


# La partita dal vivo nella guida ai comandi: i suoi tasti non stanno in un menu.
GUIDA_DELLA_PARTITA_DAL_VIVO = (
    "La partita dal vivo si apre scegliendo Assisti nel dialogo dell'amichevole. Lì Invio o spazio sul pulsante Prosegui fanno sentire il gioco "
    "fino al punto seguente, e mentre suona lo mettono in pausa e lo riprendono; Alt+F ascolta fino a fine set, Alt+L passa dalla parte "
    "dell'altro giocatore, Alt+V va alla fine e mostra il risultato, Esc esce senza svelarlo, e a incontro finito porta al risultato; "
    "più e meno cambiano la velocità di gioco; "
    "F1 rimette la guida dei tasti nel campo della cronaca, che si raggiunge con Tab. Time-out, cambio campo e inizio del set non si "
    "sentono: si leggono nella cronaca, e il suono riprende dalla ripresa del gioco. Le righe della cronaca si leggono anche da sole, "
    "alla sintesi e al display braille, come dice Annunci della cronaca nel menu Impostazioni.")


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
        if evento.tipo == "CAMBIO_AL_TAVOLO":
            # La gara a squadre, tappa 12, punto 8.9: a ogni livello il campo dice chi gioca adesso.
            testo = cronaca.frase(evento, nomi, livello)
            if testo:
                righe.append(testo)
            dati = evento.dati or {}
            righe.append(f"Al tavolo {cronaca._n(nomi, dati.get('batte'))} contro {cronaca._n(nomi, dati.get('entra'))}.")
            continue
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


def guida_dal_vivo(nomi, ascoltatore, set_al_meglio, velocita, differita=False):
    """
    Il testo con cui si apre il campo della cronaca della finestra dal vivo: chi gioca, da dove si
    ascolta, i tasti e la velocità. Dalla tappa 12 anche la partita in differita di un torneo o di una
    sfida, e la gara a squadre, un set a 31, dove il lato è quello della squadra.
    """
    squadre = set_al_meglio == 1
    gara = "gara a squadre, un set a 31 punti" if squadre else f"al meglio dei {set_al_meglio} set"
    if differita:
        testa = f"Partita in differita: {nomi['A'].testo} contro {nomi['B'].testo}, {gara}. Il risultato resta nascosto finché non arrivi alla fine."
    else:
        testa = f"Partita dal vivo: {nomi['A'].testo} contro {nomi['B'].testo}, {gara}. L'incontro è già registrato nel mondo."
    altra_parte = "dell'altra squadra" if squadre else "dell'altro giocatore"
    righe = [
        testa,
        dove_ascolti(nomi, ascoltatore),
        "Invio o spazio su Prosegui fanno sentire il gioco fino al punto seguente; mentre suona, lo stesso tasto lo ferma e lo riprende, e salta il riscaldamento.",
        f"Alt+F ascolta fino a fine set, Alt+L passa dalla parte {altra_parte}, Alt+V va alla fine e mostra il risultato, Esc esce senza svelarlo.",
        f"Più e meno cambiano la velocità di gioco, ora {velocita}: accorcia le pause e la procedura dell'arbitro, mai l'azione.",
        "Time-out, cambio campo e inizio del set non si sentono: il suono riprende dalla ripresa del gioco.",
    ]
    if squadre:
        righe.append("Le formazioni si leggono nella cronaca, e a ogni cambio al tavolo un suono breve: il campo dice chi gioca adesso.")
    righe.append("In questo campo la cronaca cresce riga per riga mentre ascolti, pause lunghe comprese, senza toglierti il fuoco dal pulsante; "
                 "F1 ci rimette questa guida, Maiusc+Tab torna al pulsante.")
    return "\n".join(righe)


def titolo_dal_vivo(nomi, velocita, differita=False):
    return f"{'In differita' if differita else 'Dal vivo'}, {nomi['A'].testo} contro {nomi['B'].testo}, velocità {velocita}"


SPIEGAZIONE_VELOCITA = ("La velocità di gioco vale per tutte le partite dal vivo: a 1 le pause fra i punti e la procedura dell'arbitro durano come nella realtà, "
                        "a 2 la metà, a 4, la predefinita, un quarto. L'azione resta sempre a tempo reale. Durante la partita più e meno la cambiano al volo.")
# Il dialogo degli annunci della cronaca, 1.79.0: le parole delle scelte, con le chiavi di GBsintesi.
SPIEGAZIONE_ANNUNCI = ("Nella partita dal vivo e nell'ascolto in differita la cronaca cresce riga per riga nel suo campo. Con la lettura automatica "
                       "ogni riga nuova arriva da sé alla sintesi, al display braille o a tutti e due. Alla sintesi le righe si leggono una dopo "
                       "l'altra. Al display ogni riga si divide in blocchi grandi quanto le sue celle, e ogni blocco resta almeno per il tempo minimo "
                       "di lettura; con 0 celle la riga arriva intera. Il braille arriva da NVDA o da JAWS.")
DESTINAZIONI_DEGLI_ANNUNCI = {"entrambi": "alla sintesi e al braille", "sintesi": "solo alla sintesi", "braille": "solo al braille"}
SINTESI_DEGLI_ANNUNCI = {"automatica": "automatica, il primo screen reader attivo o la voce di Windows", "nvda": "NVDA", "jaws": "JAWS",
                         "sapi5": "la voce di Windows, SAPI5"}
# Il dialogo degli effetti sonori, con il volume della partita della decisione D30.
SPIEGAZIONE_VOLUMI = ("Il volume degli effetti sonori, da 0 a 100: a 50 i suoni sono come sono stati pensati, a zero tacciono. "
                      "Il volume della partita dal vivo, da 0 a 100, vale soltanto per i suoni della partita: a 95 suona come è stata pensata, "
                      "a 100 arriva al massimo senza distorcere, a zero tace.")


# L'amichevole nella finestra, tappa 9: risultato e cronaca salvata.

SALVA_LA_CRONACA = "La cronaca dell'incontro si salva in un file con Ctrl+Maiusc+O."
NESSUNA_AMICHEVOLE = ("Nella sessione non hai ancora mostrato né ascoltato un incontro: un'amichevole si gioca con Ctrl+O, e gli incontri dei tuoi nei tornei "
                      "e nelle sfide si ascoltano o si leggono dal pannello dei tornei, Ctrl+Y, e dallo storico delle sfide, Ctrl+Maiusc+H.")
# Come si chiama l'ultimo incontro nelle frasi della cronaca salvata, dalla tappa 12.
NOMI_DEGLI_INCONTRI = {"amichevole": "dell'amichevole", "torneo": "dell'incontro di torneo", "sfida": "della sfida"}


def risultato_amichevole(risultato, mondo):
    """Il risultato di un'amichevole, aperto dal dato essenziale: chi vince, i set, contro chi e i parziali dal punto di vista di chi vince."""
    id_a, id_b = risultato.parti
    vince_a = risultato.vincitore == "A"
    vincitore, perdente = (mondo.giocatori[id_a], mondo.giocatori[id_b]) if vince_a else (mondo.giocatori[id_b], mondo.giocatori[id_a])
    al_meglio = f"Amichevole al meglio dei {risultato.formato.set_al_meglio} set."
    if risultato.esito == "ritiro":
        # Dalla tappa 12: col ritiro si dicono soltanto i set giocati, e chi si è ritirato.
        giocati = risultato.set[:risultato.set_giocati]
        parziali = ", ".join(f"{a} a {b}" if vince_a else f"{b} a {a}" for a, b in giocati)
        chi = " e ".join(nome_completo(mondo.giocatori[gid]) for gid in risultato.ritirato)
        verbo = "si ritira" if len(risultato.ritirato) == 1 else "si ritirano"
        return f"Vince {nome_completo(vincitore)} contro {nome_completo(perdente)}: {chi} {verbo} dopo {len(giocati)} set, {parziali}. {al_meglio}"
    sa, sb = risultato.set_vinti
    mio, suo = (sa, sb) if vince_a else (sb, sa)
    parziali = ", ".join(f"{a} a {b}" if vince_a else f"{b} a {a}" for a, b in risultato.set)
    return f"Vince {nome_completo(vincitore)}, {mio} set a {suo} contro {nome_completo(perdente)}: {parziali}. {al_meglio}"


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
    return f"{chi}: ognuno gioca al massimo un incontro per giorno simulato, amichevole, torneo o sfida, e chi è infortunato o ritirato non gioca. {quando}"


def cronaca_salvata(percorso, livello, nomi, tipo="amichevole"):
    return f"La cronaca {livello} {NOMI_DEGLI_INCONTRI.get(tipo, tipo)} fra {nomi['A'].testo} e {nomi['B'].testo} è nel file {percorso}."


def cronaca_non_salvata(errore, tipo="amichevole"):
    return f"La cronaca {NOMI_DEGLI_INCONTRI.get(tipo, tipo)} non si è potuta salvare: {errore}."


# La sala allenamento e i contratti, tappa 11, decisione D31: i testi che la finestra mostra.

def _dopo_le_spese(g, spese):
    """Una copia del giocatore come sarebbe dopo le spese, per l'anteprima: il giocatore vero non si tocca."""
    copia = copy.copy(g)
    for spesa in spese:
        base = getattr(g, spesa.caratteristica + "_base")
        setattr(copia, spesa.caratteristica + "_allenata", max(0.0, spesa.a - base))
    copia.aggiorna_icv()
    return copia


def _nome_semplice(caratteristica):
    return nome_caratteristica(allenamento.nome(caratteristica) + "_base").lower()


def intestazione_sala(p, allenandi, mondo=None):
    """
    In testa alla sala: Pat-Bologna: 12 allenandi, 412,5 punti allenamento da spendere in tutto. Dalla
    tappa 13, progetto 4.4, col mondo anche chi allena e la qualità dello staff, su una riga sua.
    """
    totale = sum(g.punti_allenamento for g in allenandi)
    testo = f"{p.nome}: {conta(len(allenandi), 'allenando', 'allenandi')}, {quanti_punti(totale, True)} da spendere in tutto."
    return testo if mondo is None else f"{testo}\n{chi_allena(p, mondo)}"


def chi_allena(p, mondo):
    """Chi allena la polisportiva e la qualità dello staff: Allena Mario Rossi, C4, con 2 assistenti. Qualità dello staff..."""
    capo = allenatore_del_posto(p, 0, mondo)
    assistenti = sum(1 for posto in range(1, staff.POSTI) if p.staff[posto])
    if capo is not None:
        inizio = f"Allena {nome_allenatore(capo)}, {'con ' + conta(assistenti, 'assistente', 'assistenti') if assistenti else 'senza assistenti'}."
    elif assistenti:
        inizio = f"Nessun capo allenatore, {conta(assistenti, 'assistente', 'assistenti')}."
    else:
        inizio = "Nessuno staff: i tesserati si allenano senza allenatore."
    return f"{inizio} {qualita_dello_staff(p, mondo)}"


def riga_allenando(g, mondo):
    """Un allenando nell'elenco della sala: Mario Rossi, classe G4, 38,5 punti, programma aggressivo, indole di rimessa, intensità normale."""
    riga = f"{nome_completo(g)}, classe {codice_classe(g)}, {quanti_punti(g.punti_allenamento)}, {programma_e_indole(g)}, intensità {g.intensita}"
    if not allenamento.puo_allenarsi(g) and g.infortunio_fine_datetime:
        riga += f", {accorda(g, 'infortunato')} fino al {g.infortunio_fine_datetime.day} {MESI[g.infortunio_fine_datetime.month - 1]}, non si allena"
    # Dalla tappa 12, punto 12.4: l'acciacco, come l'infortunio.
    testo = acciacco(g, mondo.datetime_corrente_simulazione)
    if testo:
        riga += f", {testo}"
    return riga


def riga_caratteristica_allenamento(g, caratteristica):
    """Una caratteristica nella sala: Chiusura sinistra: Buono (14,6), il prossimo punto costa 37 punti allenamento; al tetto, al massimo."""
    c = allenamento.nome(caratteristica)
    riga = valore_caratteristica(g, c + "_base")
    if allenamento.totale(g, c) >= allenamento.tetto(c) - 1e-9:
        return f"{riga}, al massimo"
    return f"{riga}, il prossimo punto costa {quanti_punti(round(allenamento.costo_del_prossimo_punto(g, c)), True)}"


def _classe_dopo(prima, dopo):
    return f"classe {prima}" if prima == dopo else f"classe da {prima} a {dopo}"


def anteprima_allenamento(g, caratteristica, quanti):
    """L'anteprima di una spesa a mano: Con 120 punti: chiusura sinistra da 14,6 a 15,3, valore da 142,3 a 145,1, classe G4."""
    spesa = allenamento.anteprima(g, caratteristica, quanti)
    if spesa.punti <= 0:
        return f"Con {quanti_punti(quanti)} {_nome_semplice(caratteristica)} non sale: è al massimo." if quanti > 0 else "Scegli quanti punti spendere."
    dopo = _dopo_le_spese(g, [spesa])
    testo = (f"Con {quanti_punti(spesa.punti)}: {_nome_semplice(caratteristica)} {da_a(spesa.da, spesa.a)}, "
             f"valore {da_a(g.indice_collettivo_valore, dopo.indice_collettivo_valore)}, {_classe_dopo(codice_classe(g), codice_classe(dopo))}.")
    if spesa.punti < quanti - 1e-9:
        testo += f" Al tetto ne bastano {punti(spesa.punti)}: gli altri restano."
    return testo


def domanda_spesa(g, caratteristica, quanti):
    """La conferma della spesa a mano, che è l'anteprima stessa: Spendere 120 punti in chiusura sinistra? Da 14,6 a 15,3, valore da 142,3 a 145,1."""
    spesa = allenamento.anteprima(g, caratteristica, quanti)
    dopo = _dopo_le_spese(g, [spesa])
    return (f"Spendere {quanti_punti(spesa.punti)} in {_nome_semplice(caratteristica)}? {da_a(spesa.da, spesa.a).capitalize()}, "
            f"valore {da_a(g.indice_collettivo_valore, dopo.indice_collettivo_valore)}.")


def domanda_allena_tutti(allenandi):
    """La conferma di Allena tutti: Spendere 412,5 punti di 12 allenandi, ciascuno secondo il suo programma?"""
    totale = sum(g.punti_allenamento for g in allenandi)
    return f"Spendere {quanti_punti(totale)} di {conta(len(allenandi), 'allenando', 'allenandi')}, ciascuno secondo il suo programma?"


def esito_allenamento(g, spesi, valore_prima, classe_prima):
    """
    L'esito di una spesa in una riga: Mario Rossi: 38,5 punti spesi, valore da 142,3 a 145,1,
    classe G4; e sale alla classe G3 quando sale.
    """
    speso = "speso" if punti(spesi) == "1" else "spesi"
    riga = f"{nome_completo(g)}: {quanti_punti(spesi)} {speso}, valore {da_a(valore_prima, g.indice_collettivo_valore)}, "
    if sale_di_classe(g, classe_prima):
        return riga + f"sale alla classe {codice_classe(g)}"
    return riga + f"classe {codice_classe(g)}"


def _livello(codice):
    """Il livello di un codice di classe: 1 per A1, 100 per K0."""
    return classe.LETTERE.index(codice[0]) * 10 + int(codice[1:])


def sale_di_classe(g, classe_prima):
    """Vero se il giocatore, che aveva la classe dal codice dato, ora sta in una classe più alta."""
    return classe.classe(g).livello < _livello(classe_prima)


def voce_classe_salita(g):
    """La voce di diario della classe guadagnata in sala: Sale alla classe G3."""
    return f"Sale alla classe {codice_classe(g)}."


def _parti_spese(spese):
    """Le caratteristiche salite di almeno un decimo, a parole, e quante altre sono salite di meno."""
    salite = [s for s in spese if s.a - s.da >= 0.1 - 1e-9 or len(spese) == 1]
    parti = [f"{_nome_semplice(s.caratteristica)} {da_a(s.da, s.a)}" for s in salite]
    altre = len(spese) - len(salite)
    if altre:
        parti.append(f"{conta(altre, 'altra caratteristica', 'altre caratteristiche')} di meno")
    return unisci(parti)


def dettaglio_spese(g, spese):
    """Le caratteristiche salite in una spesa: Mario Rossi: chiusura sinistra da 14,6 a 15,3 e difesa da 10,2 a 10,4."""
    return f"{nome_completo(g)}: {_parti_spese(spese)}."


def voce_della_sala(esito, spese):
    """
    Una spesa nel riepilogo della sala, in una riga sola: l'esito, come esito_allenamento, e il
    dettaglio delle caratteristiche salite, che nel messaggio breve della sala non c'è.
    """
    return f"{esito}; {_parti_spese(spese)}."


def cambio_in_sala(g):
    """
    Programma, intensità e iscrizione automatica di un tesserato cambiati in sala, per il riepilogo:
    Mario Rossi: programma di rimessa, intensità intensa, iscrizione automatica ai tornei accesa.
    """
    automatica = "accesa" if g.iscrizione_automatica else "spenta"
    return f"{nome_completo(g)}: programma {programma(g)}, intensità {g.intensita}, iscrizione automatica ai tornei {automatica}."


def allenando_fermo(g):
    """L'avviso della sala per un allenando infortunato, che oggi non si allena."""
    return f"{nome_completo(g)} è {infortunio(g)}: finché non guarisce non si allena."


def senza_punti(g):
    """L'avviso della sala quando l'allenando non ha punti per una spesa a mano."""
    if g.punti_allenamento > 0:
        return (f"{nome_completo(g)} ha soltanto {punti(g.punti_allenamento)} punti allenamento: a mano se ne spende almeno uno, "
                "l'allenamento completo spende anche le frazioni.")
    return f"{nome_completo(g)} non ha punti allenamento da spendere: arrivano dalla seduta di ogni giorno e dalle amichevoli."


def caratteristica_al_massimo(g, caratteristica):
    """L'avviso della sala per una caratteristica già al tetto del totale: Mario Rossi ha già chiusura sinistra al massimo, 40,0 su 40."""
    c = allenamento.nome(caratteristica)
    return f"{nome_completo(g)} ha già {_nome_semplice(c)} al massimo, {numero(allenamento.totale(g, c))} su {intero(allenamento.tetto(c))}."


def tutto_al_massimo(g):
    """L'avviso dell'allenamento completo quando non c'è più niente da far salire."""
    return f"{nome_completo(g)} ha già tutte le caratteristiche al massimo."


def nessuno_da_allenare(p):
    """L'avviso di Allena tutti quando nessuno ha un punto da spendere o può allenarsi."""
    return f"Nessun tesserato di {p.nome} oggi può allenarsi con almeno un punto allenamento da spendere."


def riepilogo_sala(p, esiti, cambi=()):
    """
    Il riepilogo della sala alla chiusura: quante spese e quanti cambi di programma o d'intensità,
    poi una riga per spesa, con il dettaglio delle caratteristiche, e una per tesserato cambiato.
    """
    if not esiti and not cambi:
        return f"Sala allenamento di {p.nome}: nessuna spesa."
    parti = [conta(len(esiti), "spesa", "spese") if esiti else "nessuna spesa"]
    if cambi:
        parti.append(conta(len(cambi), "cambio di programma, d'intensità o d'iscrizione", "cambi di programma, d'intensità o d'iscrizione"))
    return "\n".join([f"Sala allenamento di {p.nome}: {unisci(parti)}.", *esiti, *cambi])


def testata_contratti(p, mondo):
    """In testa al dialogo dei contratti: la cassa, lo sponsor e il monte stipendi."""
    return f"{p.nome}: cassa {euro(p.cassa)}, sponsor {euro(mondo.sponsor(p))} al mese, stipendi {euro(mondo.monte_stipendi(p))} al mese."


def riga_contratto(g, p, mondo):
    """
    Un tesserato nel dialogo dei contratti: Mario Rossi, 220 euro al mese fino al 1 marzo 2028,
    rinnovabile da dicembre; oppure in scadenza, rinnovato, o che non tratta più.
    """
    oggi = mondo.datetime_corrente_simulazione
    if not contratti.ha_contratto(g):
        return f"{nome_completo(g)}, senza contratto"
    inizio = f"{nome_completo(g)}, {euro(g.contratto_stipendio)} al mese fino al {data_breve(g.contratto_scadenza)}"
    if contratti.ha_rinnovo(g):
        return f"{nome_completo(g)}, rinnovato dal {data_breve(g.contratto_scadenza)}: {euro(g.rinnovo_stipendio)} al mese fino al {data_breve(g.rinnovo_scadenza)}"
    if not contratti.in_finestra(g, oggi):
        return f"{inizio}, rinnovabile da {MESI[contratti.inizio_finestra(g).month - 1]}"
    if not contratti.puo_trattare(g):
        return f"{nome_completo(g)}, non tratta più: {accorda(g, 'libero')} dal {data_breve(g.contratto_scadenza)}"
    mesi = contratti.durata_proposta(g)
    return (f"{inizio}, in scadenza: chiede {euro(contratti.richiesta_rinnovo(g, p, mesi))} al mese per {mesi} mesi, "
            f"proposte rimaste {PROPOSTE_RINNOVO_MASSIME - g.proposte_rinnovo}")


def esito_previsto_rinnovo(g, p, stipendio, mesi):
    """L'esito previsto di una proposta: Accetterebbe al 64%. Per 12 mesi chiede 310 euro al mese. Il contratto nuovo partirebbe il 1 marzo 2028."""
    probabilita = contratti.probabilita_rinnovo(g, p, stipendio, mesi)
    return (f"Accetterebbe {con_articolo('al', percento(probabilita))}. Per {mesi} mesi chiede {euro(contratti.richiesta_rinnovo(g, p, mesi))} al mese. "
            f"Il contratto nuovo partirebbe il {data_breve(g.contratto_scadenza)}.")


def domanda_rinnovo(g, p, stipendio, mesi):
    """La conferma della proposta di rinnovo, con la probabilità."""
    probabilita = contratti.probabilita_rinnovo(g, p, stipendio, mesi)
    return (f"Proporre a {nome_completo(g)} il rinnovo a {euro(stipendio)} al mese per {mesi} mesi, dal {data_breve(g.contratto_scadenza)}? "
            f"Accetterebbe {con_articolo('al', percento(probabilita))}.")


def esito_rinnovo(g, p, accettato, richiesta, mesi):
    """L'esito della proposta: accettata, con il contratto nuovo; rifiutata, con quanto chiede e le proposte rimaste; o chiusa al terzo rifiuto."""
    if accettato:
        return (f"{nome_completo(g)} ha accettato: dal {data_breve(g.contratto_scadenza)} prenderà {euro(g.rinnovo_stipendio)} al mese, "
                f"fino al {data_breve(g.rinnovo_scadenza)}.")
    vorrebbe = f"{nome_completo(g)} ha rifiutato: per firmare vorrebbe circa {euro(richiesta)} al mese per {mesi} mesi."
    rimaste = PROPOSTE_RINNOVO_MASSIME - g.proposte_rinnovo
    if rimaste <= 0:
        return f"{vorrebbe} Non vuole più trattare: il contratto con {p.nome} finirà il {data_breve(g.contratto_scadenza)}."
    return f"{vorrebbe} {conta(rimaste, 'proposta rimasta', 'proposte rimaste').capitalize()}, una al giorno."


def riepilogo_contratti(p, esiti):
    """
    Il riepilogo del dialogo dei contratti alla chiusura, dal dato che conta, come quello del
    mercato: Contratti di Pat-Bologna: 3 proposte, 1 rinnovo concordato, 1 giocatore che non tratta
    più. Poi una riga per proposta. esiti sono coppie di testo ed esito: accettato, rifiutato o chiuso.
    """
    if not esiti:
        return f"Contratti di {p.nome}: nessuna proposta."
    concordati = sum(1 for _testo, esito in esiti if esito == "accettato")
    chiusi = sum(1 for _testo, esito in esiti if esito == "chiuso")
    parti = [conta(len(esiti), "proposta", "proposte"), conta(concordati, "rinnovo concordato", "rinnovi concordati") if concordati else "nessun rinnovo concordato"]
    if chiusi:
        parti.append(conta(chiusi, "giocatore che non tratta più", "giocatori che non trattano più"))
    return "\n".join([f"Contratti di {p.nome}: {', '.join(parti)}.", *(testo for testo, _esito in esiti)])


def evento_contratti(esiti):
    """Il fatto dei contratti nella barra di stato: contratti: 1 rinnovo su 3."""
    concordati = sum(1 for _testo, esito in esiti if esito == "accettato")
    return f"contratti: {concordati} {'rinnovo' if concordati == 1 else 'rinnovi'} su {len(esiti)}"


def evento_sala(esiti, cambi):
    """Il fatto della sala nella barra di stato, come la prima riga del riepilogo: sala: 2 spese e 1 cambio; sala: 1 cambio."""
    parti = [conta(len(esiti), "spesa", "spese")] if esiti else []
    if cambi:
        parti.append(conta(len(cambi), "cambio", "cambi"))
    return f"sala: {unisci(parti) if parti else 'nessuna spesa'}"
