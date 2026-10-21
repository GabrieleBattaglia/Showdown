"""
Lo staff delle polisportive di MESS: gli allenatori, la qualità dello staff e i suoi effetti.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-21 con la tappa 13, decisione D33 di Gabriele e risposte del 21 ottobre, nel progetto
di lavori_tappa_13/progetto.txt. Un allenatore è di due tipi. L'ex giocatore è un giocatore ritirato del
mondo che aveva raggiunto almeno H0: nome, sesso, visus ed età sono i suoi, e quando il giocatore muore
l'allenatore esce di scena con lui. L'allenatore nato è un adulto che il mondo genera accanto alle
nascite dei giocatori, con nome, aspetto, visus, età e morte suoi. La classe da allenatore è un livello
da 1, A1, a 70, H0, fisso per sempre: per l'ex giocatore è la classe migliore della sua carriera.
Ogni polisportiva ha un capo e due posti d'assistente, nel campo staff, coi numeri degli allenatori, 0
per un posto vuoto. La qualità dello staff, da 0 a 1, dà tre fattori: l'allenamento, il rischio
d'infortunio e la crescita della fedeltà, ciascuno con le tre ancore di costanti.py.
Non conosce wx né il mondo: il mondo tiene gli allenatori in mondo.allenatori e chiama queste regole.
"""

import datetime
import math

import classe as modulo_classe
import contratti
import descrizioni
import economia
from costanti import (
    ANNI_MINIMI_DA_ALLENATORE,
    ANNO_SIMULAZIONE_GIORNI,
    CREA_NUOVI_PER_TICK_RANGE,
    ETA_FINE_ALLENATORE_ANNI,
    ETA_MAX_MORTE_GIORNI,
    ETA_MIN_MORTE_GIORNI,
    ETA_NATI_ALLENATORI_ANNI,
    FATTORI_ALLENAMENTO_STAFF,
    FATTORI_FEDELTA_STAFF,
    FATTORI_RISCHIO_STAFF,
    LIVELLO_MINIMO_ALLENATORE,
    MEDIA_CLASSE_NATI_ALLENATORI,
    MESI_CONTRATTO_MAX,
    MESI_CONTRATTO_MIN,
    MESI_DI_INGAGGIO,
    PESI_STAFF,
    PROBABILITA_ALLENATORE_PER_NASCITA,
    PROBABILITA_IPOVEDENTE_CREAZIONE,
    QUALITA_MINIMA_ALLENATORE,
    QUOTA_STIPENDIO_ASSISTENTE,
    QUOTA_VEDENTI_ALLENATORI,
    RINCARO_DURATA_RINNOVO,
    SCONTO_FEDELTA_RINNOVO,
    STIPENDIO_STAFF_MASSIMO,
    STIPENDIO_STAFF_MINIMO,
)
from modelli import DATA, DATA_O_NULLA, DIARIO, TESTO_O_NULLA, _campi_da_dizionario, annota_diario, conversione_a_json, probabilita_accettazione
from nomi import genera_identita

EX = "ex"
NATO = "nato"
TIPI = (EX, NATO)
CAPO = "capo"
ASSISTENTE = "assistente"
RUOLI = (CAPO, ASSISTENTE)
# I visus, D33 risposta 22: gli allenatori possono anche vedere.
NON_VEDENTE = "non vedente"
IPOVEDENTE = "ipovedente"
VEDENTE = "vedente"
VISUS = (NON_VEDENTE, IPOVEDENTE, VEDENTE)
# I posti dello staff di una polisportiva, nel campo staff: il capo e i due assistenti.
POSTI = 3
STAFF_VUOTO = (0, 0, 0)
CAMPI_ALLENATORE = (
    ("numero", int), ("tipo", str), ("livello", int), ("nome", str), ("cognome", str), ("sesso", str), ("visus", str),
    ("nascita", DATA), ("eta_fine", int), ("etamorte", int), ("giocatore_id", int),
    ("club_di_provenienza", TESTO_O_NULLA), ("fedelta_di_provenienza", float),
    ("polisportiva", TESTO_O_NULLA), ("ruolo", TESTO_O_NULLA), ("contratto_stipendio", int), ("contratto_scadenza", DATA_O_NULLA),
    ("rinnovo_stipendio", int), ("rinnovo_scadenza", DATA_O_NULLA), ("proposte_rinnovo", int), ("ultima_trattativa", DATA_O_NULLA),
    ("prelazione", TESTO_O_NULLA), ("prelazione_fino", DATA_O_NULLA), ("riservato_fino", DATA_O_NULLA), ("diario", DIARIO),
)
_CONVERSIONI_ALLENATORE = tuple((campo, conversione_a_json(tipo)) for campo, tipo in CAMPI_ALLENATORE)


class Allenatore:
    """
    Un allenatore. etamorte vale 0 per l'ex giocatore, che muore col suo giocatore, giocatore_id 0 per
    il nato; tratti, solo del nato, sono quelli dell'aspetto, come per i giocatori.
    """

    def __init__(self, numero, tipo, livello, nome, cognome, sesso, visus, nascita, eta_fine, etamorte=0, giocatore_id=0, tratti=None):
        self.numero = numero
        self.tipo = tipo
        self.livello = livello
        self.nome = nome
        self.cognome = cognome
        self.sesso = sesso
        self.visus = visus
        self.nascita = nascita
        self.eta_fine = eta_fine
        self.etamorte = etamorte
        self.giocatore_id = giocatore_id
        self.tratti = tratti
        self.club_di_provenienza = None
        self.fedelta_di_provenienza = 0.0
        self.polisportiva = None
        self.ruolo = None
        self.contratto_stipendio = 0
        self.contratto_scadenza = None
        self.rinnovo_stipendio = 0
        self.rinnovo_scadenza = None
        self.proposte_rinnovo = 0
        self.ultima_trattativa = None
        self.prelazione = None
        self.prelazione_fino = None
        # L'istante vero fino a cui è riservato all'utente, MINUTI_RISERVA_UTENTE, o None: il computer non lo vede.
        self.riservato_fino = None
        self.diario = []

    def annota(self, data, testo):
        annota_diario(self.diario, data, testo)

    def annulla_contratto(self):
        """Toglie contratto, rinnovo, proposte e trattativa, come per i giocatori: lo usano anche le funzioni di contratti.py."""
        self.contratto_stipendio = self.rinnovo_stipendio = self.proposte_rinnovo = 0
        self.contratto_scadenza = self.rinnovo_scadenza = self.ultima_trattativa = None

    def eta(self, oggi):
        """L'età in giorni simulati, il giorno dato."""
        return (oggi - self.nascita).days

    def eta_anni(self, oggi):
        return self.eta(oggi) / ANNO_SIMULAZIONE_GIORNI

    @property
    def codice(self):
        """La classe da allenatore, come quella dei giocatori: G4, C0, A1."""
        return modulo_classe.codice(self.livello)

    @property
    def qualita(self):
        return qualita(self.livello)

    @property
    def libero(self):
        return self.polisportiva is None

    def descrizione_fisica(self, oggi):
        """L'aspetto del nato, all'età di oggi; vuoto per l'ex giocatore, che ha la scheda da giocatore."""
        return descrizioni.descrivi(self.tratti, self.sesso, self.eta_anni(oggi)) if self.tratti else ""

    def a_dizionario(self):
        dati = {campo: converti(getattr(self, campo)) for campo, converti in _CONVERSIONI_ALLENATORE}
        if self.tratti:
            dati["tratti"] = self.tratti
        return dati

    @classmethod
    def da_dizionario(cls, dati):
        """Ricostruisce un allenatore dal suo dizionario; ValueError se un campo non va."""
        a = cls.__new__(cls)
        chi = f"Allenatore {dati.get('numero', '?') if isinstance(dati, dict) else '?'}"
        _campi_da_dizionario(a, dati, CAMPI_ALLENATORE, chi)
        for campo, buono in (("tipo", a.tipo in TIPI), ("sesso", a.sesso in ("m", "f")), ("visus", a.visus in VISUS),
                             ("livello", 1 <= a.livello <= LIVELLO_MINIMO_ALLENATORE), ("numero", a.numero > 0),
                             ("ruolo", (a.ruolo is None) == (a.polisportiva is None) and (a.ruolo is None or a.ruolo in RUOLI)),
                             ("giocatore_id", (a.giocatore_id > 0) == (a.tipo == EX)), ("etamorte", (a.etamorte > 0) == (a.tipo == NATO))):
            if not buono:
                raise ValueError(f"{chi}: il campo {campo} non è valido: {getattr(a, campo)!r}")
        tratti = dati.get("tratti")
        if tratti is not None and not isinstance(tratti, dict):
            raise ValueError(f"{chi}: il campo tratti non è valido")
        a.tratti = tratti
        return a


def puo_allenare(livello):
    """Vero se un giocatore con la classe migliore di questo livello può allenare: H0 o meglio, regola di Gabriele."""
    return 1 <= livello <= LIVELLO_MINIMO_ALLENATORE


def livello_da_allenatore(classe_migliore):
    """Il livello da allenatore di un ex giocatore: quello della sua classe migliore, un punteggio."""
    return modulo_classe.livello(classe_migliore)


def eta_di_fine(eta_inizio_giorni, rng):
    """
    L'età in giorni a cui un allenatore smette, estratta fra ETA_FINE_ALLENATORE_ANNI; se l'allenatore
    comincia dopo, la fine si sposta da lì di ANNI_MINIMI_DA_ALLENATORE.
    """
    fine = round(rng.uniform(*ETA_FINE_ALLENATORE_ANNI) * ANNO_SIMULAZIONE_GIORNI)
    minima = eta_inizio_giorni + round(ANNI_MINIMI_DA_ALLENATORE * ANNO_SIMULAZIONE_GIORNI)
    return max(fine, minima)


def ex_giocatore(numero, g, oggi, rng, club=None, fedelta=0.0):
    """
    L'allenatore che nasce dal giocatore g al suo ritiro, libero, con la classe migliore della carriera;
    club è il nome della polisportiva in cui ha chiuso, se ne aveva una, con la fedeltà che aveva.
    """
    visus = IPOVEDENTE if g.ipovedente else NON_VEDENTE
    a = Allenatore(numero, EX, livello_da_allenatore(g.classe_migliore), g.nome, g.cognome, g.sesso, visus,
                   oggi - datetime.timedelta(days=g.eta), eta_di_fine(g.eta, rng), giocatore_id=g.id)
    a.club_di_provenienza = club
    a.fedelta_di_provenienza = fedelta if club is not None else 0.0
    return a


def livello_dei_nati(rng):
    """La classe di un allenatore nato: H0 meno una parte intera esponenziale di media MEDIA_CLASSE_NATI_ALLENATORI, fino ad A1."""
    sotto = int(rng.expovariate(1.0 / MEDIA_CLASSE_NATI_ALLENATORI))
    return max(1, LIVELLO_MINIMO_ALLENATORE - sotto)


def visus_dei_nati(rng):
    """Il visus di un allenatore nato: vedente al 75 per cento, e il resto fra ipovedenti e non vedenti come i giocatori."""
    if rng.uniform(0, 100) < QUOTA_VEDENTI_ALLENATORI:
        return VEDENTE
    return IPOVEDENTE if rng.uniform(0, 100) < PROBABILITA_IPOVEDENTE_CREAZIONE else NON_VEDENTE


def nato(numero, oggi, rng, eta_giorni=None):
    """Un allenatore nato, libero: adulto, con nome, aspetto, visus, classe, fine e morte suoi; l'età si può dare, per la migrazione."""
    sesso = rng.choice(("m", "f"))
    if eta_giorni is None:
        eta_giorni = round(rng.uniform(*ETA_NATI_ALLENATORI_ANNI) * ANNO_SIMULAZIONE_GIORNI)
    nome, cognome = genera_identita(sesso)
    etamorte = max(round(rng.uniform(ETA_MIN_MORTE_GIORNI, ETA_MAX_MORTE_GIORNI)), eta_giorni + 1)
    return Allenatore(numero, NATO, livello_dei_nati(rng), nome, cognome, sesso, visus_dei_nati(rng), oggi - datetime.timedelta(days=eta_giorni),
                      eta_di_fine(eta_giorni, rng), etamorte=etamorte, tratti=descrizioni.genera_tratti(sesso, rng))


def nome_del_ruolo(a):
    """Il ruolo a parole, al femminile per le allenatrici: capo allenatore, capo allenatrice, assistente."""
    if a.ruolo == CAPO:
        return "capo allenatrice" if a.sesso == "f" else "capo allenatore"
    return "assistente"


def libera(a):
    """L'allenatore torna libero: niente polisportiva, ruolo, contratto né rinnovo."""
    a.polisportiva = a.ruolo = None
    a.annulla_contratto()


# L'economia dello staff, D33 risposta 13: i contratti sono quelli dei giocatori, e le funzioni di
# contratti.py valgono anche per l'allenatore, che ha gli stessi campi del contratto.

def stipendio_richiesto(a, ruolo):
    """Lo stipendio mensile che l'allenatore chiede per il ruolo: in linea retta sulla qualità, la metà da assistente."""
    quota = (a.qualita - QUALITA_MINIMA_ALLENATORE) / (1.0 - QUALITA_MINIMA_ALLENATORE)
    euro = STIPENDIO_STAFF_MINIMO + (STIPENDIO_STAFF_MASSIMO - STIPENDIO_STAFF_MINIMO) * quota
    if ruolo == ASSISTENTE:
        euro *= QUOTA_STIPENDIO_ASSISTENTE
    return economia.arrotonda(euro)


def ingaggio_richiesto(a, ruolo, poli=None):
    """
    Il premio d'ingaggio che l'allenatore chiede per firmare, come i giocatori: MESI_DI_INGAGGIO stipendi.
    Alla polisportiva in cui ha chiuso la carriera da giocatore chiede meno, come i giocatori fedeli ai
    rinnovi, fino a un quarto in meno alla fedeltà piena: D33 risposta 15.
    """
    return economia.arrotonda(stipendio_richiesto(a, ruolo) * MESI_DI_INGAGGIO * sconto_di_provenienza(a, poli))


def durata_proposta(a, oggi):
    """I mesi di contratto che l'allenatore propone, dalla tabella dell'età dei giocatori, da 4 a 24."""
    mesi = math.floor(contratti.durata_base(a.eta_anni(oggi)) + 0.5)
    return max(MESI_CONTRATTO_MIN, min(MESI_CONTRATTO_MAX, mesi))


def sconto_di_provenienza(a, poli):
    """Lo sconto della polisportiva dove l'ex giocatore ha chiuso la carriera: fino a un quarto alla fedeltà piena, D33 risposta 15."""
    if poli is not None and poli.nome == a.club_di_provenienza:
        return 1.0 - SCONTO_FEDELTA_RINNOVO * a.fedelta_di_provenienza / 100.0
    return 1.0


def richiesta_rinnovo(a, poli, mesi, oggi):
    """
    Lo stipendio che l'allenatore chiede per rinnovare nel suo ruolo per tanti mesi: quello che chiede
    oggi, il 2 per cento in più per ogni mese di differenza dalla durata che propone, come i giocatori, e
    meno alla polisportiva dove ha chiuso la carriera.
    """
    euro = stipendio_richiesto(a, a.ruolo) * (1.0 + RINCARO_DURATA_RINNOVO * abs(mesi - durata_proposta(a, oggi))) * sconto_di_provenienza(a, poli)
    return max(1, economia.arrotonda(euro))


def probabilita_rinnovo(a, poli, stipendio, mesi, oggi):
    """La probabilità, in percentuale, che l'allenatore accetti il rinnovo: la curva dell'ingaggio, come i giocatori."""
    return probabilita_accettazione(stipendio, richiesta_rinnovo(a, poli, mesi, oggi))


# Per la migrazione dal formato 7: le nascite medie di un giorno, da CREA_NUOVI_PER_TICK_RANGE, e
# quanto dura in media la vita da allenatore di un nato, dai 47 anni e mezzo agli 80.
NASCITE_AL_GIORNO = sum(CREA_NUOVI_PER_TICK_RANGE) / 2
CARRIERA_MEDIA_DEI_NATI = round((80.0 - sum(ETA_NATI_ALLENATORI_ANNI) / 2) * ANNO_SIMULAZIONE_GIORNI)


def nati_di_un_mondo(giorni):
    """Quanti allenatori nati ha in media un mondo di tanti giorni simulati: uno ogni venti nascite, nella loro vita da allenatori."""
    return round(NASCITE_AL_GIORNO * PROBABILITA_ALLENATORE_PER_NASCITA / 100 * min(max(0, giorni), CARRIERA_MEDIA_DEI_NATI))


def eta_sparsa(giorni, rng):
    """L'età in giorni di un allenatore nato da tanti giorni in un mondo di quell'età: quella di nascita più un tratto della sua vita."""
    return round(rng.uniform(*ETA_NATI_ALLENATORI_ANNI) * ANNO_SIMULAZIONE_GIORNI + rng.uniform(0, min(max(0, giorni), CARRIERA_MEDIA_DEI_NATI)))


def qualita(livello):
    """La qualità di un allenatore del livello dato: QUALITA_MINIMA_ALLENATORE per H0, 1 per A1, in linea retta."""
    quota = (LIVELLO_MINIMO_ALLENATORE - livello) / (LIVELLO_MINIMO_ALLENATORE - 1)
    return QUALITA_MINIMA_ALLENATORE + (1.0 - QUALITA_MINIMA_ALLENATORE) * min(1.0, max(0.0, quota))


def qualita_dello_staff(capo, assistenti):
    """
    La qualità dello staff, da 0 a 1: il capo, un livello o None, pesa PESI_STAFF[0]; gli assistenti,
    livelli o None, pesano il migliore PESI_STAFF[1] e l'altro PESI_STAFF[2].
    """
    peso_capo, peso_primo, peso_secondo = PESI_STAFF
    q = peso_capo * qualita(capo) if capo is not None else 0.0
    ordinati = sorted((qualita(n) for n in assistenti if n is not None), reverse=True)
    for peso, q_assistente in zip((peso_primo, peso_secondo), ordinati, strict=False):
        q += peso * q_assistente
    return q


def fattore(q, ancore, media):
    """
    Il fattore di un effetto per la qualità q: le ancore sono senza staff, staff medio e staff migliore,
    e fra l'una e l'altra il fattore va in linea retta. Lo staff medio è media, la qualità media dello
    staff del mondo di oggi, scelta di Gabriele del 21 ottobre 2026, risposta 30: il mondo nel suo insieme
    si allena sempre come prima dello staff. In un mondo senza nessun allenatore, media zero, tutti
    valgono lo staff medio.
    """
    senza, medio, migliore = ancore
    q = min(1.0, max(0.0, q))
    if media <= 0.0:
        return medio
    if q <= media:
        return senza + (medio - senza) * q / media
    if media >= 1.0:
        return migliore
    return medio + (migliore - medio) * (q - media) / (1.0 - media)


def fattori(q, media):
    """I tre fattori dello staff di qualità q, con lo staff medio del mondo: allenamento, rischio d'infortunio, crescita della fedeltà."""
    return fattore(q, FATTORI_ALLENAMENTO_STAFF, media), fattore(q, FATTORI_RISCHIO_STAFF, media), fattore(q, FATTORI_FEDELTA_STAFF, media)


# I fattori senza staff in un mondo dove qualcuno ha uno staff: le prime ancore.
FATTORI_SENZA_STAFF = (FATTORI_ALLENAMENTO_STAFF[0], FATTORI_RISCHIO_STAFF[0], FATTORI_FEDELTA_STAFF[0])


def livelli_dello_staff(posti, allenatori):
    """I livelli del capo e degli assistenti di una polisportiva, dai numeri del suo campo staff: None per un posto vuoto."""
    livelli = [allenatori[numero].livello if numero and numero in allenatori else None for numero in posti]
    return livelli[0], livelli[1:]


def qualita_della_polisportiva(poli, allenatori):
    """La qualità dello staff di una polisportiva, da 0 a 1."""
    capo, assistenti = livelli_dello_staff(poli.staff, allenatori)
    return qualita_dello_staff(capo, assistenti)


def qualita_media(polisportive, allenatori):
    """
    Lo staff medio del mondo, risposta 30: la media della qualità dello staff fra le polisportive con
    almeno un tesserato, quelle senza staff comprese, a zero; zero se non ce n'è nessuna.
    """
    qualita_di_ognuna = [qualita_della_polisportiva(p, allenatori) for p in polisportive if p.tesserati]
    return sum(qualita_di_ognuna) / len(qualita_di_ognuna) if qualita_di_ognuna else 0.0
