"""
La barra di stato su misura di MESS: il catalogo dei dati, la composizione delle righe scelte e la loro legenda.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-25 con la decisione D38, idea di Gabriele del 24 ottobre: la barra di stato non è più fatta di
quattro righe fisse, ma delle righe e dei dati che sceglie chi gioca, con la voce Barra di stato del menu Impostazioni.
Qui sta quello che non dipende da wx: il catalogo dei 93 dati, in undici gruppi, ciascuno con la sua chiave, che si
salva nel file delle impostazioni e non cambia mai, la sigla di tre lettere, il nome, il gruppo, l'ambito, il ritmo,
la spiegazione, l'esempio e il calcolo; la composizione delle righe, con l'istantanea che la finestra tiene fra un
comando e l'altro; la legenda della guida. Da qui vengono la finestra della barra, la barra, la guida e le prove sul
manuale. Il catalogo è quello del 24 ottobre, con le scelte di Gabriele: fra sigla e valore sempre i due punti, come
Glo:138 e Sal:-180, perché il meno attaccato a una lettera NVDA lo legge come un trattino; gare, classifiche, sfide
ricevute e di domani contano tutte le polisportive dell'utente, il resto è della polisportiva attiva; l'ora simulata
riparte da 00:00 a ogni avanzamento; il dato del salvataggio compare solo quando il salvataggio non va; la pazienza si
conta in primi del mese senza stipendio, esatta, con lo stesso conto del mondo.
Ogni dato ha un ritmo. Quelli del rinfresco, cioè l'ora, i tempi, le riserve dello staff, il salvataggio e l'ultimo
evento, si ricalcolano a ogni rinfresco; tutti gli altri vengono dall'istantanea, un dizionario fra chiave e testo che
la finestra svuota dopo ogni comando, dopo ogni avanzamento e quando si salva una barra nuova. Un dato senza testo, come
quello del salvataggio quando tutto va bene o quelli della polisportiva attiva quando non ce n'è una, non lascia spazi,
e una riga senza nessun testo non si scrive.
"""

import dataclasses
import datetime
import functools

import classe
import contratti
import economia
import formule
import impostazioni
import infortuni
import iscrizioni
import modelli_torneo
import palmares
import sfide
import staff
import testi
from partita import MotorePartita
from utilita import in_ora_locale

# I gruppi del catalogo, nell'ordine dell'elenco dei dati disponibili e del manuale.
TEMPO = "Il tempo"
ATTIVA = "La polisportiva attiva"
SOLDI = "I soldi della polisportiva attiva"
MERCATO = "Il mercato"
ROSA = "La rosa della polisportiva attiva"
STAFF = "Lo staff"
GARE = "Le gare"
CLASSIFICHE = "Le classifiche dei tuoi"
TUE = "Tutte le tue polisportive"
MONDO = "Il mondo"
SESSIONE = "La sessione e le notizie"
GRUPPI = (TEMPO, ATTIVA, SOLDI, MERCATO, ROSA, STAFF, GARE, CLASSIFICHE, TUE, MONDO, SESSIONE)
# Gli ambiti: di chi è il dato.
DEL_MONDO = "del mondo"
DELL_ATTIVA = "della polisportiva attiva"
DI_TUTTE = "di tutte le tue polisportive"
DELLA_SESSIONE = "della sessione"
# I ritmi: un dato del rinfresco si ricalcola ogni volta, uno del comando dopo ogni comando e ogni avanzamento.
RINFRESCO = "rinfresco"
COMANDO = "comando"
# Il rinfresco della barra, in millesimi: ogni minuto simulato, cioè ogni 20 secondi veri, così l'ora non resta indietro.
RINFRESCO_MILLESIMI = 20_000
# Le voci dei conti di un mese che entrano nella cassa; tutte le altre ne escono.
ENTRATE = ("sponsor", "vendite", "premi", "rimborsi")
# Il tetto dei primi del mese senza stipendio che la pazienza conta: oltre, nessuno se ne va, e il dato dice no.
MESI_DI_PAZIENZA_CONTATI = 1200
NO = "no"


@dataclasses.dataclass(frozen=True)
class Dato:
    """Un dato del catalogo: la chiave del file, la sigla, o None per i tre dati a parole, e il calcolo, che dà il valore o None."""

    chiave: str
    sigla: str | None
    nome: str
    gruppo: str
    ambito: str
    spiegazione: str
    esempio: str
    calcolo: object
    ritmo: str = COMANDO

    @property
    def etichetta(self):
        """Il dato negli elenchi della finestra: la sigla e il nome, o il nome soltanto."""
        return f"{self.sigla}, {self.nome}" if self.sigla else self.nome

    def testo(self, calcolo):
        """Il testo del dato nella barra, con la sigla e i due punti; None se adesso il dato non si mostra."""
        valore = self.calcolo(calcolo)
        if valore is None:
            return None
        return f"{self.sigla}:{valore}" if self.sigla else str(valore)


@dataclasses.dataclass
class Contesto:
    """Quello che la finestra dà al calcolo: il mondo, l'istante di adesso in UTC e le notizie della sessione."""

    mondo: object
    ora: datetime.datetime
    ultimo_evento: str = ""
    rapporto: dict | None = None
    salvataggio_riuscito: bool = True
    durata: datetime.timedelta = datetime.timedelta(0)
    comandi: int = 0


# I numeri e le date della barra: senza spazi, all'italiana.

def _intero(valore):
    return testi.intero(valore)


def _breve(valore):
    """Un numero di punti, intero quando lo è, altrimenti con un decimale: 50, 12,5."""
    arrotondato = round(valore, 1)
    return _intero(arrotondato) if arrotondato == int(arrotondato) else testi.numero(arrotondato, 1)


def _giorno_e_mese(data):
    return f"{data.day:02d}/{data.month:02d}"


def _ore_e_minuti(intervallo):
    minuti = max(0, int(intervallo.total_seconds() // 60))
    return f"{minuti // 60}h{minuti % 60:02d}m"


def _quattro(oro, argento, bronzo, legno):
    return f"{oro}-{argento}-{bronzo}-{legno}"


def _primo_del_mese_dopo(oggi):
    """Il giorno del primo del mese che viene, come data."""
    anno, mese = (oggi.year + 1, 1) if oggi.month == 12 else (oggi.year, oggi.month + 1)
    return datetime.date(anno, mese, 1)


def _saldo(conti):
    """Le entrate meno le uscite dei conti di un mese."""
    return sum(valore if voce in ENTRATE else -valore for voce, valore in conti.items() if voce != "data" and voce != "cassa")


class _Calcolo:
    """I conti di un rinfresco della barra: ognuno si fa una volta sola, anche se lo usano più dati."""

    def __init__(self, contesto):
        self.contesto = contesto
        self.mondo = contesto.mondo
        self.ora = contesto.ora
        self.oggi = self.mondo.datetime_corrente_simulazione
        self.p = self.mondo.miapolisportiva_attiva

    @functools.cached_property
    def rosa(self):
        """I tesserati presenti della polisportiva attiva, come li paga il mondo il primo del mese."""
        return self.mondo._rosa(self.p)

    @functools.cached_property
    def tue(self):
        return [q for q in self.mondo.polisportive.values() if not q.is_cpu_controlled]

    @functools.cached_property
    def nomi_delle_tue(self):
        return {q.nome for q in self.tue}

    @functools.cached_property
    def rosa_di_tutte(self):
        return [g for q in self.tue for g in self.mondo._rosa(q)]

    @functools.cached_property
    def tuoi(self):
        return iscrizioni.tuoi_del_mondo(self.mondo)

    @functools.cached_property
    def sponsor(self):
        return self.mondo.sponsor(self.p)

    @functools.cached_property
    def monte(self):
        """Gli stipendi del mese, tesserati e staff."""
        return self.mondo.monte_stipendi(self.p)

    @functools.cached_property
    def stipendi_dello_staff(self):
        return self.mondo.monte_dello_staff(self.p)

    @functools.cached_property
    def arretrati(self):
        return sum(g.arretrati for g in self.rosa)

    @functools.cached_property
    def margine(self):
        return self.p.cassa + self.sponsor - self.monte - self.arretrati

    @functools.cached_property
    def conti_del_mondo(self):
        """I giocatori liberi, sotto contratto e fermi, e la popolazione, in una passata sola."""
        morti = self.mondo._ids_morti_processati_sessione
        vivi = fermi = sotto = 0
        for gid, g in self.mondo.giocatori.items():
            if gid in morti:
                continue
            vivi += 1
            if g.ritirato or g.infortunato:
                fermi += 1
            elif g.appartenenza != "*":
                sotto += 1
        return vivi - fermi - sotto, sotto, fermi, vivi

    @functools.cached_property
    def classifiche_nazionali(self):
        """Per sesso il posto del tuo migliore nella classifica nazionale per sempre, o None: un giro solo per i due sessi."""
        return palmares.posti_mondiali(self.mondo, {g.id for g in self.rosa_di_tutte})

    @functools.cached_property
    def classifiche_dell_anno(self):
        """
        Per sesso il posto del tuo migliore nella classifica dell'anno che convoca il campionato italiano e i posti dei
        convocati; il sesso manca senza il suo campionato o senza un tuo atleta che lo può giocare. L'ordine è quello di
        iscrizioni.chiave_dell_anno: chi ha più punti dell'anno sta davanti, a pari punti chi ha il punteggio di classe più
        alto, poi il numero più basso. Una passata sola per i due sessi, e il punteggio, che è il conto caro, soltanto per
        chi ha i punti del tuo migliore.
        """
        oggi = self.oggi.date()
        migliori = {}
        for sesso in ("m", "f"):
            modello = self.modello_con(modelli_torneo.PUNTI_ANNO, sesso)
            chiavi = [iscrizioni.chiave_dell_anno(g, oggi) for g in self.rosa_di_tutte if modello is not None and not g.ritirato and modelli_torneo.idoneo(modello, g)]
            if chiavi:
                migliori[sesso] = (modello, min(chiavi))
        davanti = dict.fromkeys(migliori, 0)
        morti = self.mondo._ids_morti_processati_sessione
        for gid, g in self.mondo.giocatori.items():
            voce = migliori.get(g.sesso)
            if voce is None or gid in morti or g.ritirato:
                continue
            modello, (meno_punti, meno_punteggio, numero) = voce
            if not modelli_torneo.idoneo(modello, g):
                continue
            punti = -palmares.punti_dell_anno(g, oggi)
            if punti < meno_punti or (punti == meno_punti and (-classe.punteggio(g), gid) < (meno_punteggio, numero)):
                davanti[g.sesso] += 1
        return {sesso: (davanti[sesso] + 1, modelli_torneo.tetto(modello, self.formule_valide)) for sesso, (modello, _chiave) in migliori.items()}

    @functools.cached_property
    def modelli(self):
        return modelli_torneo.GestoreModelli().modelli()[0]

    @functools.cached_property
    def formule_valide(self):
        return formule.leggi()[0]

    def modello_con(self, qualificazione, sesso=None):
        """Il primo modello attivo con quella qualificazione, e quel sesso se si dà: il campionato italiano o la coppa."""
        return next((m for m in self.modelli if m.attivo and m.qualificazione == qualificazione and (sesso is None or m.sesso == sesso)), None)

    def staff_della_attiva(self):
        return [a for numero in self.p.staff if numero and (a := self.mondo.allenatori.get(numero)) is not None]


def _della_attiva(calcolo_del_dato):
    """Un dato della polisportiva attiva non si mostra quando non ce n'è una."""
    @functools.wraps(calcolo_del_dato)
    def calcolo(c):
        return None if c.p is None else calcolo_del_dato(c)
    return calcolo


# Il tempo.

def _data_simulata(c):
    return f"{c.oggi:%d/%m/%Y}"


def _giorno_della_settimana(c):
    return modelli_torneo.nome_del_giorno(c.oggi.weekday())


def _ora_simulata(c):
    ore, minuti = c.mondo.ora_del_giorno(c.ora)
    return f"{ore:02d}:{minuti:02d}"


def _prossimo_avanzamento_fra(c):
    return _ore_e_minuti(c.mondo.prossimo_avanzamento() - c.ora)


def _prossimo_avanzamento_alle(c):
    return f"{in_ora_locale(c.mondo.prossimo_avanzamento()):%H:%M}"


def _ultimo_avanzamento_alle(c):
    return f"{in_ora_locale(c.mondo.datetime_ultimo_run_reale):%H:%M}"


def _giorni_al_primo_del_mese(c):
    return f"{(_primo_del_mese_dopo(c.oggi) - c.oggi.date()).days}g"


# La polisportiva attiva.

def _nome_polisportiva(c):
    return "nessuna polisportiva attiva" if c.p is None else c.p.nome


@_della_attiva
def _gloria(c):
    return c.p.gloria


@_della_attiva
def _posto_per_gloria(c):
    sopra = sum(1 for q in c.mondo.polisportive.values() if q.gloria > c.p.gloria)
    return f"{sopra + 1}/{len(c.mondo.polisportive)}"


@_della_attiva
def _medaglie(c):
    return _quattro(c.p.ori, c.p.argenti, c.p.bronzi, c.p.legni)


@_della_attiva
def _coppe(c):
    return _quattro(c.p.coppe_oro, c.p.coppe_argento, c.p.coppe_bronzo, c.p.coppe_legno)


@_della_attiva
def _palmares_cinque_anni(c):
    medaglie, coppe = palmares.somma_finestra(c.p, c.oggi)
    return f"{_breve(medaglie)}+{_breve(coppe)}"


# I soldi della polisportiva attiva.

@_della_attiva
def _cassa(c):
    return _intero(c.p.cassa)


@_della_attiva
def _margine_al_primo(c):
    return _intero(c.margine)


@_della_attiva
def _saldo_mensile(c):
    return _intero(c.sponsor - c.monte)


@_della_attiva
def _autonomia(c):
    """
    Quanti primi del mese di fila la cassa paga per intero. Il primo paga anche gli arretrati, e resta il margine; ogni
    primo dopo aggiunge il saldo, e si paga finché la cassa non va sotto zero. Col saldo che non perde, sempre.
    """
    if c.margine < 0:
        return 0
    saldo = c.sponsor - c.monte
    if saldo >= 0:
        return "sempre"
    return 1 + c.margine // -saldo


def _primi_senza_stipendio(g):
    """Quanti primi del mese senza stipendio bastano perché il tesserato se ne vada: lo stesso conto di Mondo._conti_del_primo, mese per mese."""
    pazienza = g.pazienza
    for mesi in range(1, MESI_DI_PAZIENZA_CONTATI + 1):
        pazienza = max(0., pazienza - 100 / economia.mesi_di_pazienza(g))
        if pazienza <= 0:
            return mesi
    return None


@_della_attiva
def _pazienza_minima(c):
    if not c.arretrati and c.margine >= 0:
        return NO
    mesi = [m for g in c.rosa if not economia.bandiera_attiva(g) and (m := _primi_senza_stipendio(g)) is not None]
    return min(mesi) if mesi else NO


@_della_attiva
def _sponsor(c):
    return _intero(c.sponsor)


@_della_attiva
def _stipendi_tesserati(c):
    return _intero(c.monte - c.stipendi_dello_staff)


@_della_attiva
def _stipendi_staff(c):
    return _intero(c.stipendi_dello_staff)


@_della_attiva
def _quote_del_mese(c):
    return _intero(c.p.conti_del_mese["iscrizioni"] - c.p.conti_del_mese["rimborsi"])


@_della_attiva
def _premi_del_mese(c):
    return _intero(c.p.conti_del_mese["premi"])


@_della_attiva
def _movimenti_del_mese(c):
    return _intero(_saldo(c.p.conti_del_mese))


@_della_attiva
def _bilancio_ultimo_mese(c):
    return _intero(_saldo(c.p.bilanci[0])) if c.p.bilanci else NO


# Il mercato.

@_della_attiva
def _mosse_rimaste(c):
    return c.mondo.mosse_rimaste(c.p)


@_della_attiva
def _tuoi_in_vendita(c):
    return len(c.p.in_vendita)


def _in_vendita_nel_mondo(c):
    giocatori = c.mondo.giocatori
    return _intero(sum(1 for q in c.mondo.polisportive.values() for gid in q.in_vendita if (g := giocatori.get(gid)) is not None and not g.ritirato))


# La rosa della polisportiva attiva.

@_della_attiva
def _tesserati(c):
    return f"{len(c.p.tesserati)}/{c.p.maxtesserati}"


@_della_attiva
def _disponibili(c):
    return sum(1 for g in c.rosa if g.puo_giocare)


@_della_attiva
def _amichevoli_giocabili(c):
    return sum(1 for g in c.rosa if g.puo_giocare_amichevole(c.oggi))


@_della_attiva
def _impegnati_oggi(c):
    return sum(1 for g in c.rosa if g.ha_un_impegno(c.oggi))


@_della_attiva
def _infortunati(c):
    return sum(1 for g in c.rosa if g.infortunato)


@_della_attiva
def _acciaccati(c):
    return sum(1 for g in c.rosa if infortuni.calo_acciacco(g, c.oggi) > 0)


@_della_attiva
def _prossima_guarigione(c):
    fine = min((g.infortunio_fine_datetime for g in c.rosa if g.infortunato and g.infortunio_fine_datetime is not None), default=None)
    return NO if fine is None else _giorno_e_mese(fine)


@_della_attiva
def _punti_allenamento(c):
    return _intero(sum(g.punti_allenamento or 0 for g in c.rosa))


@_della_attiva
def _intensita_intensa(c):
    return sum(1 for g in c.rosa if g.intensita == "intensa")


@_della_attiva
def _iscrizione_manuale(c):
    return sum(1 for g in c.rosa if not g.iscrizione_automatica)


@_della_attiva
def _contratti_in_uscita(c):
    primo = _primo_del_mese_dopo(c.oggi)
    return sum(1 for g in c.rosa if contratti.ha_contratto(g) and not contratti.ha_rinnovo(g) and g.contratto_scadenza.date() <= primo)


@_della_attiva
def _contratti_in_scadenza(c):
    return sum(1 for g in c.rosa if contratti.in_finestra(g, c.oggi) and not contratti.ha_rinnovo(g))


@_della_attiva
def _rinnovi_da_proporre(c):
    return sum(1 for g in c.rosa if c.mondo.problema_rinnovo(c.p, g) is None)


@_della_attiva
def _migliore(c):
    if not c.rosa:
        return NO
    return classe.classe(max(c.rosa, key=lambda g: g.indice_collettivo_valore)).codice


@_della_attiva
def _valore_collettivo(c):
    return testi.numero(c.p.indicecollettivotesserati, 1)


@_della_attiva
def _valore_di_mercato(c):
    return _intero(sum(economia.valore_di_mercato(g, c.oggi) for g in c.rosa))


@_della_attiva
def _eta_media(c):
    return testi.numero(sum(g.eta_anni for g in c.rosa) / len(c.rosa), 1) if c.rosa else NO


@_della_attiva
def _uomini_donne(c):
    uomini = sum(1 for g in c.rosa if g.sesso == "m")
    return f"{uomini}u{len(c.rosa) - uomini}d"


# Lo staff.

@_della_attiva
def _capo_allenatore(c):
    capo = testi.allenatore_del_posto(c.p, 0, c.mondo)
    return NO if capo is None else capo.codice


@_della_attiva
def _posti_staff(c):
    return f"{len(c.staff_della_attiva())}/{staff.POSTI}"


@_della_attiva
def _qualita_staff(c):
    return testi.percento(round(staff.qualita_della_polisportiva(c.p, c.mondo.allenatori) * 100))


@_della_attiva
def _rinnovi_staff(c):
    return sum(1 for a in c.staff_della_attiva() if c.mondo.problema_rinnovo_allenatore(c.p, a) is None)


def _riservati_a_te(c):
    """Gli allenatori liberi riservati a te, con l'ora vera in cui scade la prima riserva."""
    scadenze = [a.riservato_fino for a in c.mondo.allenatori.values() if a.libero and a.riservato_fino is not None and a.riservato_fino > c.ora]
    if not scadenze:
        return 0
    return f"{len(scadenze)}-{in_ora_locale(min(scadenze)):%H:%M}"


def _prelazioni(c):
    """Gli allenatori su cui hai la prelazione, con il giorno simulato in cui scade la prima."""
    scadenze = [a.prelazione_fino for a in c.mondo.allenatori.values() if a.libero and a.prelazione in c.nomi_delle_tue and a.prelazione_fino is not None]
    if not scadenze:
        return 0
    return f"{len(scadenze)}-{_giorno_e_mese(min(scadenze))}"


def _allenatori_liberi(c):
    return _intero(sum(1 for a in c.mondo.allenatori.values() if a.libero))


# Le gare.

@_della_attiva
def _sfide_da_lanciare(c):
    return max(0, sfide.disponibili(c.mondo, c.p))


def _sfide_ricevute(c):
    return sum(len(c.mondo.sfide.proposte_per(nome)) for nome in c.nomi_delle_tue)


def _sfide_di_domani(c):
    nomi = c.nomi_delle_tue
    return sum(1 for s in c.mondo.sfide.attive if s.stato == sfide.ACCETTATA and (s.sfidante["nome"] in nomi or s.sfidata["nome"] in nomi))


@_della_attiva
def _sfide_vinte_perse(c):
    return f"{c.p.sfide_vinte}-{c.p.sfide_perse}"


def _sedi_dei_tuoi(c):
    """Le sedi in corso con i tuoi, ciascuna coi suoi tuoi."""
    sedi = ((t, iscrizioni.tuoi_nel_torneo(c.mondo, t, c.tuoi)) for t in c.mondo.calendario.tornei)
    return [(t, tuoi) for t, tuoi in sedi if tuoi]


def _tornei_in_corso(c):
    return len(_sedi_dei_tuoi(c))


def _tuoi_in_gara(c):
    return sum(len(tuoi - {gid for gid, _dove in testi._eliminati(t)}) for t, tuoi in _sedi_dei_tuoi(c))


def _iscritti_tuoi(c, ed):
    return [i for i in ed.iscritti if iscrizioni.iscritto_tuo(c.mondo, i["id"], i.get("club"), c.tuoi)]


def _iscrizioni_dei_tuoi(c):
    return sum(len(_iscritti_tuoi(c, ed)) for ed in c.mondo.calendario.edizioni)


def _prossimo_torneo_dei_tuoi(c):
    inizio = min((ed.data_inizio for ed in c.mondo.calendario.edizioni if _iscritti_tuoi(c, ed)), default=None)
    return NO if inizio is None else _giorno_e_mese(inizio)


def _differite_da_ascoltare(c):
    return len(c.mondo.calendario.da_svelare())


def _convocati_campionato(c):
    return sum(len(_iscritti_tuoi(c, ed)) for ed in c.mondo.calendario.edizioni if ed.qualificazione == modelli_torneo.PUNTI_ANNO)


@_della_attiva
def _coppa_delle_polisportive(c):
    """
    Fino alla qualificazione, all'apertura delle iscrizioni, il posto per gloria sui posti della coppa, nell'ordine in cui
    la coppa qualifica; dalla qualificazione alla fine, gioca o fuori. Il modello e i posti si leggono, perché l'editor dei
    tornei li può cambiare.
    """
    nome = c.p.nome
    for ed in c.mondo.calendario.edizioni:
        if ed.qualificazione == modelli_torneo.GLORIA:
            return "gioca" if nome in ed.ids() else "fuori"
    for t in c.mondo.calendario.tornei:
        if t.modello.get("qualificazione") == modelli_torneo.GLORIA:
            in_gara = nome in t.iscritti and nome not in {gid for gid, _dove in testi._eliminati(t)}
            return "gioca" if in_gara else "fuori"
    modello = c.modello_con(modelli_torneo.GLORIA)
    if modello is None:
        return NO
    davanti = sum(1 for q in c.mondo.polisportive.values() if (-q.gloria, q.nome) < (-c.p.gloria, nome))
    posti = modelli_torneo.tetto(modello, c.formule_valide)
    return f"{davanti + 1}/{posti}" if posti else davanti + 1


def _edizioni_aperte(c):
    return len(c.mondo.calendario.edizioni)


def _prossimo_torneo_del_calendario(c):
    inizio = min((ed.data_inizio for ed in c.mondo.calendario.edizioni), default=None)
    return NO if inizio is None else _giorno_e_mese(inizio)


def _prossima_apertura(c):
    """Il giorno della prossima apertura delle iscrizioni, con lo stesso conto di Calendario.apri_edizioni, dal giorno dopo l'ultima apertura."""
    domani = c.oggi.date() + datetime.timedelta(days=1)
    aperture = []
    for modello in c.modelli:
        if not modello.attivo or modelli_torneo.problema(modello, c.formule_valide) is not None:
            continue
        ultima = c.mondo.calendario.ultime_aperture.get(modello.id)
        dopo = domani if ultima is None else max(domani, datetime.date.fromisoformat(ultima) + datetime.timedelta(days=1))
        inizio = modelli_torneo.prossima_data(modello, dopo)
        aperture.append(max(domani, inizio - datetime.timedelta(days=modello.giorni_iscrizione)))
    return _giorno_e_mese(min(aperture)) if aperture else NO


# Le classifiche dei tuoi.

def _classifica_dell_anno(c, sesso):
    """Il posto del tuo migliore di quel sesso nella classifica dell'anno che convoca il campionato italiano, sui posti dei convocati."""
    voce = c.classifiche_dell_anno.get(sesso)
    if voce is None:
        return NO
    posto, posti = voce
    return f"{posto}/{posti}" if posti else posto


def _classifica_nazionale(c, sesso):
    """Il posto del tuo migliore di quel sesso nella classifica nazionale per sempre, vecchie glorie comprese."""
    posto = c.classifiche_nazionali[sesso]
    return NO if posto is None else posto


# Tutte le tue polisportive.

def _amichevoli_di_tutte(c):
    return sum(len(giocatori) for _q, giocatori in MotorePartita(c.mondo).da_far_giocare(c.tue))


def _punti_di_tutte(c):
    return _intero(sum(g.punti_allenamento or 0 for g in c.rosa_di_tutte))


def _gloria_piu_alta(c):
    return max((q.gloria for q in c.tue), default=NO)


def _medaglie_di_tutte(c):
    return _quattro(*(sum(getattr(q, campo) for q in c.tue) for campo in ("ori", "argenti", "bronzi", "legni")))


def _coppe_di_tutte(c):
    return _quattro(*(sum(getattr(q, campo) for q in c.tue) for campo in ("coppe_oro", "coppe_argento", "coppe_bronzo", "coppe_legno")))


# La sessione e le notizie.

def _stato_salvataggio(c):
    if c.mondo.salvataggio_bloccato:
        return "bloccato"
    return None if c.contesto.salvataggio_riuscito else "fallito"


def _notizie_ultimo_avanzamento(c):
    return len((c.contesto.rapporto or {}).get("notizie", ()))


def _ultimo_evento(c):
    return c.contesto.ultimo_evento or "pronto"


_DATI = (
    # Il tempo.
    Dato("data_simulata", "Dat", "data simulata", TEMPO, DEL_MONDO,
         "La data simulata, che avanza di un giorno a ogni avanzamento, cioè ogni 8 ore vere.", "Dat:26/10/2026", _data_simulata),
    Dato("giorno_della_settimana", None, "giorno della settimana", TEMPO, DEL_MONDO,
         "Il giorno della settimana, a parole. Gli open si giocano il martedì, il giovedì, il sabato e la domenica.", "lunedì", _giorno_della_settimana),
    Dato("ora_simulata", "Ora", "ora simulata", TEMPO, DEL_MONDO,
         "L'ora del giorno simulato: parte da 00:00 a ogni avanzamento e corre di tre minuti simulati per ogni minuto vero, fino alle 23:59 "
         "quando matura il giorno dopo.", "Ora:10:21", _ora_simulata, RINFRESCO),
    Dato("prossimo_avanzamento_fra", "Fra", "prossimo avanzamento fra", TEMPO, DEL_MONDO,
         "Il tempo vero che manca al prossimo avanzamento, in ore e minuti.", "Fra:4h33m", _prossimo_avanzamento_fra, RINFRESCO),
    Dato("prossimo_avanzamento_alle", "Pav", "prossimo avanzamento alle", TEMPO, DEL_MONDO,
         "L'ora vera del prossimo avanzamento. Non cambia fino all'avanzamento.", "Pav:18:51", _prossimo_avanzamento_alle),
    Dato("ultimo_avanzamento_alle", "Uav", "ultimo avanzamento alle", TEMPO, DEL_MONDO,
         "L'ora vera dell'ultimo avanzamento, da cui si contano le 8 ore.", "Uav:10:51", _ultimo_avanzamento_alle),
    Dato("giorni_al_primo_del_mese", "Pri", "giorni al primo del mese", TEMPO, DEL_MONDO,
         "I giorni simulati che mancano al primo del mese, quando arrivano sponsor e stipendi, due sfide da lanciare e le scadenze dei "
         "contratti. Ogni giorno simulato dura 8 ore vere.", "Pri:6g", _giorni_al_primo_del_mese),
    # La polisportiva attiva.
    Dato("nome_polisportiva", None, "nome della polisportiva", ATTIVA, DELL_ATTIVA,
         "Il nome della polisportiva attiva, senza abbreviazione.", "Magnavacca", _nome_polisportiva),
    Dato("gloria", "Glo", "gloria", ATTIVA, DELL_ATTIVA, "La gloria della polisportiva attiva.", "Glo:138", _gloria),
    Dato("posto_per_gloria", "Pos", "posto per gloria", ATTIVA, DELL_ATTIVA,
         "Il posto per gloria fra tutte le polisportive del mondo, sul numero delle polisportive.", "Pos:3/4", _posto_per_gloria),
    Dato("medaglie", "Med", "medaglie", ATTIVA, DELL_ATTIVA,
         "Le medaglie dei tesserati, nell'ordine oro, argento, bronzo e legno.", "Med:1-1-1-0", _medaglie),
    Dato("coppe", "Cop", "coppe", ATTIVA, DELL_ATTIVA, "Le coppe, nell'ordine oro, argento, bronzo e legno.", "Cop:0-0-0-0", _coppe),
    Dato("palmares_cinque_anni", "Pal", "palmarès di cinque anni", ATTIVA, DELL_ATTIVA,
         "Il palmarès degli ultimi cinque anni, che fa la gloria: i punti delle medaglie più quelli delle coppe.", "Pal:50+0", _palmares_cinque_anni),
    # I soldi della polisportiva attiva.
    Dato("cassa", "Cas", "cassa", SOLDI, DELL_ATTIVA, "La cassa, in euro.", "Cas:6.640", _cassa),
    Dato("margine_al_primo", "Mrg", "margine al primo del mese", SOLDI, DELL_ATTIVA,
         "Il margine al primo del mese: la cassa più lo sponsor, meno gli stipendi dei tesserati, gli arretrati e lo staff. Il primo del mese "
         "i tesserati si pagano tutti o nessuno, e chi dello staff non è pagato se ne va subito: con il margine sotto zero qualcuno resta "
         "senza stipendio.", "Mrg:6.460", _margine_al_primo),
    Dato("saldo_mensile", "Sal", "saldo del mese", SOLDI, DELL_ATTIVA,
         "Il saldo del mese, lo sponsor meno gli stipendi di tesserati e staff.", "Sal:-180", _saldo_mensile),
    Dato("autonomia", "Aut", "autonomia", SOLDI, DELL_ATTIVA,
         "L'autonomia: quanti primi del mese di fila la cassa riesce a pagare per intero, arretrati e staff compresi, se niente cambia. "
         "Zero se già il prossimo non si paga, sempre se il saldo non perde e il prossimo si paga.", "Aut:36", _autonomia),
    Dato("arretrati", "Arr", "arretrati", SOLDI, DELL_ATTIVA, "Gli arretrati da pagare ai tesserati, in euro.", "Arr:0", lambda c: None if c.p is None else _intero(c.arretrati)),
    Dato("pazienza_minima", "Paz", "pazienza", SOLDI, DELL_ATTIVA,
         "La pazienza: quanti primi del mese senza stipendio bastano perché il tesserato meno paziente se ne vada, bandiere escluse; 1 vuol "
         "dire al prossimo. Si vede quando ci sono arretrati o il margine è sotto zero, altrimenti è no.", "Paz:no", _pazienza_minima),
    Dato("sponsor", "Spo", "sponsor", SOLDI, DELL_ATTIVA, "Lo sponsor del mese, che dipende dalla rosa e dalla gloria.", "Spo:2.730", _sponsor),
    Dato("stipendi_tesserati", "Sti", "stipendi dei tesserati", SOLDI, DELL_ATTIVA, "Gli stipendi dei tesserati, ogni mese.", "Sti:2.890", _stipendi_tesserati),
    Dato("stipendi_staff", "Sst", "stipendi dello staff", SOLDI, DELL_ATTIVA, "Gli stipendi dello staff, ogni mese.", "Sst:20", _stipendi_staff),
    Dato("quote_del_mese", "Quo", "quote del mese", SOLDI, DELL_ATTIVA,
         "Le quote d'iscrizione ai tornei pagate nel mese, rimborsi tolti.", "Quo:30", _quote_del_mese),
    Dato("premi_del_mese", "Vin", "vincite del mese", SOLDI, DELL_ATTIVA, "Le vincite, cioè i premi dei tornei del mese.", "Vin:38", _premi_del_mese),
    Dato("movimenti_del_mese", "Flu", "flusso del mese", SOLDI, DELL_ATTIVA,
         "Il flusso del mese in corso, le entrate meno le uscite fin qui, cioè mercato e tornei. Sponsor e stipendi non ci sono, perché il "
         "primo del mese entrano nel mese che si chiude.", "Flu:-13.360", _movimenti_del_mese),
    Dato("bilancio_ultimo_mese", "Bil", "bilancio dell'ultimo mese", SOLDI, DELL_ATTIVA,
         "Il bilancio dell'ultimo mese chiuso, le entrate meno le uscite; no finché nessun mese si è chiuso.", "Bil:-2.626", _bilancio_ultimo_mese),
    # Il mercato.
    Dato("mosse_rimaste", "Mos", "mosse di mercato", MERCATO, DELL_ATTIVA,
         "Le mosse di mercato che restano oggi alla polisportiva attiva; tornano a 5 a ogni avanzamento.", "Mos:3", _mosse_rimaste),
    Dato("tuoi_in_vendita", "Vnd", "tuoi in vendita", MERCATO, DELL_ATTIVA,
         "I tesserati della polisportiva attiva che hai messo in vendita.", "Vnd:0", _tuoi_in_vendita),
    Dato("in_vendita_nel_mondo", "Mer", "in vendita nel mondo", MERCATO, DEL_MONDO, "I giocatori in vendita in tutto il mondo.", "Mer:345", _in_vendita_nel_mondo),
    # La rosa della polisportiva attiva.
    Dato("tesserati", "Tes", "tesserati", ROSA, DELL_ATTIVA, "I tesserati sul massimo.", "Tes:13/15", _tesserati),
    Dato("disponibili", "Dsp", "disponibili", ROSA, DELL_ATTIVA, "I disponibili, cioè chi può scendere in campo.", "Dsp:13", _disponibili),
    Dato("amichevoli_giocabili", "Ami", "amichevoli giocabili", ROSA, DELL_ATTIVA,
         "Le amichevoli che puoi ancora giocare oggi, cioè i tesserati liberi da impegni.", "Ami:2", _amichevoli_giocabili),
    Dato("impegnati_oggi", "Imp", "impegnati oggi", ROSA, DELL_ATTIVA, "I tesserati che oggi hanno già giocato.", "Imp:11", _impegnati_oggi),
    Dato("infortunati", "Inf", "infortunati", ROSA, DELL_ATTIVA, "Gli infortunati.", "Inf:0", _infortunati),
    Dato("acciaccati", "Acc", "acciaccati", ROSA, DELL_ATTIVA, "Gli acciaccati, che per qualche giorno rendono un poco meno.", "Acc:0", _acciaccati),
    Dato("prossima_guarigione", "Gua", "prossima guarigione", ROSA, DELL_ATTIVA,
         "Il giorno simulato in cui guarisce il primo infortunato; no senza infortunati.", "Gua:29/10", _prossima_guarigione),
    Dato("punti_allenamento", "Pun", "punti allenamento", ROSA, DELL_ATTIVA, "I punti allenamento da spendere in sala.", "Pun:53", _punti_allenamento),
    Dato("intensita_intensa", "Its", "intensità intensa", ROSA, DELL_ATTIVA,
         "I tesserati che si allenano all'intensità intensa, e possono infortunarsi in seduta.", "Its:3", _intensita_intensa),
    Dato("iscrizione_manuale", "Man", "iscrizione a mano", ROSA, DELL_ATTIVA,
         "I tesserati con l'iscrizione automatica ai tornei spenta.", "Man:2", _iscrizione_manuale),
    Dato("contratti_in_uscita", "Usc", "contratti in uscita", ROSA, DELL_ATTIVA,
         "I contratti che scadono al prossimo primo del mese senza rinnovo, compresi quelli di chi non tratta più: i tesserati che stai per "
         "perdere.", "Usc:1", _contratti_in_uscita),
    Dato("contratti_in_scadenza", "Sca", "contratti in scadenza", ROSA, DELL_ATTIVA,
         "I contratti negli ultimi tre mesi, quelli della finestra dei rinnovi, ancora senza rinnovo.", "Sca:0", _contratti_in_scadenza),
    Dato("rinnovi_da_proporre", "Rin", "rinnovi da proporre", ROSA, DELL_ATTIVA, "I rinnovi che puoi proporre oggi ai tesserati.", "Rin:0", _rinnovi_da_proporre),
    Dato("migliore", "Mig", "migliore", ROSA, DELL_ATTIVA, "La classe del tesserato che vale di più; no senza tesserati.", "Mig:F3", _migliore),
    Dato("valore_collettivo", "Val", "valore collettivo", ROSA, DELL_ATTIVA, "Il valore collettivo della rosa.", "Val:1.681,9", _valore_collettivo),
    Dato("valore_di_mercato", "Vdm", "valore di mercato", ROSA, DELL_ATTIVA, "Il valore di mercato della rosa, in euro.", "Vdm:17.400", _valore_di_mercato),
    Dato("eta_media", "Eta", "età media", ROSA, DELL_ATTIVA, "L'età media, in anni simulati; no senza tesserati.", "Eta:25,0", _eta_media),
    Dato("uomini_donne", "Ses", "uomini e donne", ROSA, DELL_ATTIVA,
         "Gli uomini e le donne in rosa: 10u3d sono 10 uomini e 3 donne. Sfide e Coppa vogliono squadre miste.", "Ses:10u3d", _uomini_donne),
    # Lo staff.
    Dato("capo_allenatore", "Tec", "capo allenatore", STAFF, DELL_ATTIVA,
         "La classe del capo allenatore della polisportiva attiva; no col posto vuoto.", "Tec:G4", _capo_allenatore),
    Dato("posti_staff", "Stf", "posti dello staff", STAFF, DELL_ATTIVA, "I posti dello staff occupati, sui tre.", "Stf:1/3", _posti_staff),
    Dato("qualita_staff", "Qua", "qualità dello staff", STAFF, DELL_ATTIVA, "La qualità dello staff.", "Qua:19%", _qualita_staff),
    Dato("rinnovi_staff", "Rst", "rinnovi dello staff", STAFF, DELL_ATTIVA, "I rinnovi dello staff che puoi proporre oggi.", "Rst:0", _rinnovi_staff),
    Dato("riservati_a_te", "Ris", "riservati a te", STAFF, DI_TUTTE,
         "Gli allenatori liberi riservati a te, con l'ora vera in cui scade la prima riserva. Una riserva dura due ore vere.", "Ris:2-18:40",
         _riservati_a_te, RINFRESCO),
    Dato("prelazioni", "Prl", "prelazioni", STAFF, DI_TUTTE,
         "Gli allenatori su cui hai la prelazione, con il giorno simulato in cui scade la prima. La prelazione dura 10 giorni simulati.",
         "Prl:1-05/11", _prelazioni),
    Dato("allenatori_liberi", "Alb", "allenatori liberi", STAFF, DEL_MONDO, "Gli allenatori liberi sul mercato, in tutto il mondo.", "Alb:3.911", _allenatori_liberi),
    # Le gare.
    Dato("sfide_da_lanciare", "Sfl", "sfide da lanciare", GARE, DELL_ATTIVA, "Le sfide che la polisportiva attiva può ancora lanciare.", "Sfl:2", _sfide_da_lanciare),
    Dato("sfide_ricevute", "Sfr", "sfide ricevute", GARE, DI_TUTTE,
         "Le sfide ricevute che aspettano la tua risposta, in tutte le tue polisportive. La risposta va data in giornata.", "Sfr:1", _sfide_ricevute),
    Dato("sfide_di_domani", "Sfd", "sfide di domani", GARE, DI_TUTTE,
         "Le sfide accettate dalle tue polisportive, che si giocano al prossimo avanzamento.", "Sfd:0", _sfide_di_domani),
    Dato("sfide_vinte_perse", "Sfv", "sfide vinte e perse", GARE, DELL_ATTIVA, "Le sfide vinte e perse dalla polisportiva attiva.", "Sfv:3-1", _sfide_vinte_perse),
    Dato("tornei_in_corso", "Tor", "tornei in corso", GARE, DI_TUTTE, "Le sedi di torneo in corso con tuoi atleti.", "Tor:1", _tornei_in_corso),
    Dato("tuoi_in_gara", "Gar", "tuoi in gara", GARE, DI_TUTTE, "I tuoi atleti ancora in gara in quelle sedi.", "Gar:3", _tuoi_in_gara),
    Dato("iscrizioni_dei_tuoi", "Isc", "iscrizioni dei tuoi", GARE, DI_TUTTE, "Le iscrizioni dei tuoi atleti alle edizioni aperte.", "Isc:2", _iscrizioni_dei_tuoi),
    Dato("prossimo_torneo_dei_tuoi", "Ptr", "prossimo torneo dei tuoi", GARE, DI_TUTTE,
         "Il giorno in cui comincia il prossimo torneo dei tuoi; no se non ne hai.", "Ptr:27/10", _prossimo_torneo_dei_tuoi),
    Dato("differite_da_ascoltare", "Dif", "differite da ascoltare", GARE, DI_TUTTE,
         "Gli incontri di torneo dei tuoi ancora da ascoltare in differita.", "Dif:5", _differite_da_ascoltare),
    Dato("convocati_campionato", "Cit", "convocati al campionato italiano", GARE, DI_TUTTE,
         "I tuoi atleti convocati ai campionati italiani.", "Cit:0", _convocati_campionato),
    Dato("coppa_delle_polisportive", "Cdp", "Coppa delle polisportive", GARE, DELL_ATTIVA,
         "La Coppa delle polisportive per la polisportiva attiva. Fino alla qualificazione, all'apertura delle iscrizioni, è il posto per "
         "gloria sui posti della coppa; per giocarla serve anche una squadra valida, due atleti di un sesso e uno dell'altro, liberi in quei "
         "giorni. Dalla qualificazione alla fine della coppa è gioca se sei in gara, fuori se non ti sei qualificato o sei uscito.",
         "Cdp:3/64", _coppa_delle_polisportive),
    Dato("edizioni_aperte", "Ape", "edizioni aperte", GARE, DEL_MONDO,
         "Le edizioni di tutto il calendario con le iscrizioni aperte.", "Ape:11", _edizioni_aperte),
    Dato("prossimo_torneo_del_calendario", "Cal", "prossimo torneo del calendario", GARE, DEL_MONDO,
         "Il giorno in cui comincia il prossimo torneo del calendario.", "Cal:27/10", _prossimo_torneo_del_calendario),
    Dato("prossima_apertura", "Nap", "prossima apertura", GARE, DEL_MONDO,
         "Il giorno della prossima apertura delle iscrizioni.", "Nap:27/10", _prossima_apertura),
    # Le classifiche dei tuoi.
    Dato("classifica_anno_uomini", "Anm", "classifica dell'anno, uomini", CLASSIFICHE, DI_TUTTE,
         "Il posto del tuo miglior uomo nella classifica dell'anno, quella dei punti degli ultimi 365 giorni simulati che convoca il "
         "campionato italiano, sui posti dei convocati: sopra l'ultimo posto non sarebbe convocato.", "Anm:12/32",
         lambda c: _classifica_dell_anno(c, "m")),
    Dato("classifica_anno_donne", "Anf", "classifica dell'anno, donne", CLASSIFICHE, DI_TUTTE,
         "Lo stesso per la tua miglior donna.", "Anf:41/32", lambda c: _classifica_dell_anno(c, "f")),
    Dato("classifica_uomini", "Clm", "classifica nazionale, uomini", CLASSIFICHE, DI_TUTTE,
         "Il posto del tuo miglior uomo nella classifica nazionale, quella per sempre, vecchie glorie comprese; no se nessuno dei tuoi è "
         "in classifica.", "Clm:97", lambda c: _classifica_nazionale(c, "m")),
    Dato("classifica_donne", "Clf", "classifica nazionale, donne", CLASSIFICHE, DI_TUTTE,
         "Lo stesso per la tua miglior donna.", "Clf:41", lambda c: _classifica_nazionale(c, "f")),
    # Tutte le tue polisportive.
    Dato("polisportive_tue", "Tue", "le tue polisportive", TUE, DI_TUTTE, "Le tue polisportive.", "Tue:2", lambda c: len(c.tue)),
    Dato("capitale", "Tca", "capitale", TUE, DI_TUTTE, "Il capitale, cioè la cassa di tutte le tue polisportive.", "Tca:15.680",
         lambda c: _intero(sum(q.cassa for q in c.tue))),
    Dato("atleti_in_tutto", "Atl", "atleti in tutto", TUE, DI_TUTTE, "Gli atleti tesserati in tutte le tue polisportive.", "Atl:24",
         lambda c: sum(len(q.tesserati) for q in c.tue)),
    Dato("amichevoli_di_tutte", "Tam", "amichevoli di tutte", TUE, DI_TUTTE,
         "Le amichevoli giocabili oggi in tutte le tue polisportive, quelle di Gioca tutte le amichevoli di tutte le tue polisportive.",
         "Tam:2", _amichevoli_di_tutte),
    Dato("punti_di_tutte", "Tpu", "punti allenamento di tutte", TUE, DI_TUTTE, "I punti allenamento di tutte le tue polisportive.", "Tpu:53", _punti_di_tutte),
    Dato("gloria_piu_alta", "Tgl", "gloria più alta", TUE, DI_TUTTE, "La gloria più alta fra le tue polisportive.", "Tgl:155", _gloria_piu_alta),
    Dato("medaglie_di_tutte", "Tme", "medaglie di tutte", TUE, DI_TUTTE, "Le medaglie di tutte le tue polisportive.", "Tme:2-1-1-0", _medaglie_di_tutte),
    Dato("coppe_di_tutte", "Tco", "coppe di tutte", TUE, DI_TUTTE, "Le coppe di tutte le tue polisportive.", "Tco:0-0-0-0", _coppe_di_tutte),
    # Il mondo.
    Dato("liberi_nel_mondo", "Lib", "giocatori liberi", MONDO, DEL_MONDO, "I giocatori liberi, senza contratto.", "Lib:2.196",
         lambda c: _intero(c.conti_del_mondo[0])),
    Dato("sotto_contratto_nel_mondo", "Sot", "sotto contratto", MONDO, DEL_MONDO, "I giocatori sotto contratto con una polisportiva.", "Sot:18.550",
         lambda c: _intero(c.conti_del_mondo[1])),
    Dato("fermi_nel_mondo", "Fer", "fermi", MONDO, DEL_MONDO, "I giocatori fermi, ritirati o infortunati.", "Fer:6.908",
         lambda c: _intero(c.conti_del_mondo[2])),
    Dato("popolazione", "Pop", "popolazione", MONDO, DEL_MONDO, "La popolazione, tutti i giocatori, cioè liberi, sotto contratto e fermi.", "Pop:27.654",
         lambda c: _intero(c.conti_del_mondo[3])),
    Dato("polisportive_nel_mondo", "Pol", "polisportive", MONDO, DEL_MONDO, "Le polisportive del mondo.", "Pol:1.265",
         lambda c: _intero(len(c.mondo.polisportive))),
    Dato("vecchie_glorie", "Vec", "vecchie glorie", MONDO, DEL_MONDO, "Le vecchie glorie.", "Vec:141", lambda c: _intero(len(c.mondo.vecchie_glorie))),
    Dato("nuovi_della_sessione", "Nuo", "nuovi arrivati", MONDO, DEL_MONDO, "I giocatori nuovi arrivati da quando hai aperto MESS.", "Nuo:329",
         lambda c: _intero(len(c.mondo.nuovi_giocatori_sessione))),
    Dato("ritirati_della_sessione", "Rit", "ritirati", MONDO, DEL_MONDO, "I giocatori ritirati da quando hai aperto MESS.", "Rit:0",
         lambda c: _intero(len(c.mondo.giocatori_ritirati_sessione))),
    # La sessione e le notizie.
    Dato("stato_salvataggio", "Slv", "salvataggio", SESSIONE, DELLA_SESSIONE,
         "Il salvataggio, soltanto quando non va: fallito se l'ultimo non è riuscito, bloccato se il salvataggio esiste ma non si legge e "
         "MESS non salva più niente.", "Slv:fallito", _stato_salvataggio, RINFRESCO),
    Dato("notizie_ultimo_avanzamento", "Not", "notizie", SESSIONE, DELLA_SESSIONE,
         "Le notizie dei tuoi nell'ultimo avanzamento. L'ultimo evento ne dice una sola, la più importante; tutte le altre sono nel riepilogo.",
         "Not:3", _notizie_ultimo_avanzamento),
    Dato("durata_sessione", "Dur", "durata della sessione", SESSIONE, DELLA_SESSIONE, "Da quanto tempo è aperto MESS, in ore e minuti.", "Dur:1h12m",
         lambda c: _ore_e_minuti(c.contesto.durata), RINFRESCO),
    Dato("comandi_della_sessione", "Cmd", "comandi", SESSIONE, DELLA_SESSIONE, "I comandi che hai dato da quando hai aperto MESS.", "Cmd:35",
         lambda c: c.contesto.comandi),
    Dato("ultimo_evento", None, "ultimo evento", SESSIONE, DELLA_SESSIONE,
         "L'ultimo evento, a parole e senza abbreviazione: il comando appena dato, il salvataggio, oppure la notizia più importante "
         "dell'ultimo avanzamento.", "sfida da PoliTeam07, rispondi oggi", _ultimo_evento, RINFRESCO),
)
CATALOGO = {d.chiave: d for d in _DATI}
BARRA_DI_SERIE = impostazioni.BARRA_DI_SERIE
RIGHE_MASSIME = impostazioni.RIGHE_MASSIME


def dati_noti(riga):
    """I dati di una riga che questo MESS conosce, nel loro ordine: le chiavi di un MESS più nuovo restano nel file, ma non si vedono."""
    return [CATALOGO[chiave] for chiave in riga if chiave in CATALOGO]


def righe(barra_scelta, contesto, istantanea):
    """
    Le righe della barra: per ogni riga scelta i testi dei suoi dati, uniti da uno spazio. I dati del rinfresco si calcolano
    sempre; gli altri vengono dall'istantanea, il dizionario fra chiave e testo che la finestra svuota dopo ogni comando e
    ogni avanzamento, e quelli che mancano si calcolano e ci restano. Un dato senza testo non lascia spazi, e una riga
    senza nessun testo non si scrive.
    """
    calcolo = _Calcolo(contesto)
    risultato = []
    for riga in barra_scelta:
        parti = []
        for dato in dati_noti(riga):
            if dato.ritmo == RINFRESCO:
                testo = dato.testo(calcolo)
            elif dato.chiave in istantanea:
                testo = istantanea[dato.chiave]
            else:
                testo = istantanea[dato.chiave] = dato.testo(calcolo)
            if testo:
                parti.append(testo)
        if parti:
            risultato.append(" ".join(parti))
    return risultato


# I testi della finestra della barra di stato.
SPIEGAZIONE_DELLA_FINESTRA = (
    "Scegli le righe della barra di stato e i loro dati. Ogni dato compare una volta sola: Dati disponibili ha quelli che nessuna "
    "riga usa. Invio o Spazio sposta il dato su cui sei da un elenco all'altro, Canc lo toglie dalla riga. Le righe sono da una a "
    f"{RIGHE_MASSIME}; quelle rimaste vuote non si salvano.")


def conta_dati(quanti):
    return testi.conta(quanti, "dato", "dati")


def spiegazione(chiave, contesto):
    """Il dato spiegato, per la finestra della barra: il gruppo, la sigla e il nome, la spiegazione, l'esempio e il testo di adesso."""
    dato = CATALOGO[chiave]
    adesso = dato.testo(_Calcolo(contesto))
    return (f"{dato.gruppo}: {dato.etichetta}. {dato.spiegazione} Esempio: {dato.esempio}. "
            + (f"Adesso: {adesso}." if adesso else "Adesso non si vede."))


def anteprima(riga, contesto):
    """La riga come sarebbe adesso nella barra, per la finestra della barra; a parole, se è vuota o se adesso non mostra niente."""
    if not dati_noti(riga):
        return "La riga è vuota, e non si salverà."
    testo = righe([riga], contesto, {})
    return testo[0] if testo else "Adesso questa riga non mostra niente."


def legenda(barra_scelta):
    """La legenda della barra scelta, per la guida ai comandi: una frase per riga, coi suoi dati nell'ordine."""
    frasi = [f"La barra di stato ha {testi.conta(len(barra_scelta), 'riga', 'righe')}, che scegli con la voce Barra di stato del menu Impostazioni. "
             "Quasi ogni dato comincia con un'abbreviazione di tre lettere, seguita dai due punti e dal valore."]
    for numero, riga in enumerate(barra_scelta, start=1):
        dati = dati_noti(riga)
        elenco = "; ".join(d.etichetta for d in dati) if dati else "nessun dato"
        frasi.append(f"Riga {numero}: {elenco}.")
    return " ".join(frasi)
