"""
Gli eventi della partita di MESS, e il catalogo delle cause IBSA.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9, decisione D25. Un evento è una cosa che si sente: un colpo,
una sponda, un fischio, una chiamata dell'arbitro. Ha il suo istante in secondi simulati, la sua
posizione sul tavolo nel riferimento del primo giocatore, e il lato e la distanza visti da chi lo
compie; la partita live della tappa 10 lo trasformerà in suono, la cronaca in parole.
L'evento è piatto e uguale per tutti i tipi: i campi che a un tipo non servono restano vuoti. Il
volo di una pallina è una tupla di tappe, ciascuna con istante, posizione, velocità e tipo, così
il suono di un colpo diagonale può spostarsi da un orecchio all'altro mentre la pallina viaggia.
Le cause seguono il regolamento IBSA 2025-2028, con l'articolo, la chiamata dell'arbitro nei
termini italiani della FISPIC, i punti e una frase per la cronaca, dove {chi} è chi commette.
"""

import dataclasses
from typing import NamedTuple


class ErroreMotore(RuntimeError):
    """Uno stato che il motore non dovrebbe mai raggiungere: le prove non devono vederlo mai."""


class Tappa(NamedTuple):
    """Un punto del volo della pallina: istante, posizione nel riferimento del primo giocatore, velocità in cm/s e tipo."""
    t: float
    x: float
    y: float
    v: float
    tipo: str


# I tipi delle tappe. Le ultime sette chiudono l'azione: il loro suono appartiene all'evento che segue.
TAPPE = ("partenza", "sponda", "curva", "sotto_schermo", "base_schermo", "schermo", "sopra_schermo", "tavola_contatto",
         "fuori", "terra", "soffitto", "corpo", "paletta", "porta", "fermo", "mano_battitore", "arrivo")
TAPPE_TERMINALI = frozenset(("schermo", "porta", "terra", "soffitto", "corpo", "paletta", "fermo"))
# Le tappe che possono stare fuori dal tavolo.
TAPPE_FUORI = frozenset(("fuori", "terra", "soffitto"))

# I tipi degli eventi, in quattro famiglie. L'incontro e l'arbitro.
INIZIO_INCONTRO = "INIZIO_INCONTRO"
SORTEGGIO = "SORTEGGIO"
FORMAZIONI = "FORMAZIONI"
RISCALDAMENTO_INIZIO = "RISCALDAMENTO_INIZIO"
RISCALDAMENTO_COLPO = "RISCALDAMENTO_COLPO"
AVVISO_TEMPO = "AVVISO_TEMPO"
RISCALDAMENTO_FINE = "RISCALDAMENTO_FINE"
INIZIO_SET = "INIZIO_SET"
RECUPERO = "RECUPERO"
CONSEGNA = "CONSEGNA"
ANNUNCIO = "ANNUNCIO"
DOMANDA_PRONTO = "DOMANDA_PRONTO"
FISCHIO = "FISCHIO"
CHIAMATA = "CHIAMATA"
CAMBIO_BATTITORE = "CAMBIO_BATTITORE"
FINE_SET = "FINE_SET"
FINE_INCONTRO = "FINE_INCONTRO"
# Il gioco.
BATTUTA = "BATTUTA"
VOLO = "VOLO"
PARATA = "PARATA"
CAMBIO_MANO = "CAMBIO_MANO"
CONTROLLO = "CONTROLLO"
COLPO = "COLPO"
GOAL = "GOAL"
FALLO = "FALLO"
PALLA_MORTA = "PALLA_MORTA"
ROTTURA = "ROTTURA"
SOSTITUZIONE_ATTREZZO = "SOSTITUZIONE_ATTREZZO"
RIPETIZIONE = "RIPETIZIONE"
PUNTO = "PUNTO"
# Le pause e le sanzioni.
TIMEOUT_INIZIO = "TIMEOUT_INIZIO"
TIMEOUT_FINE = "TIMEOUT_FINE"
CAMBIO_CAMPO_INIZIO = "CAMBIO_CAMPO_INIZIO"
CAMBIO_CAMPO_FINE = "CAMBIO_CAMPO_FINE"
AMMONIZIONE = "AMMONIZIONE"
PENALITA = "PENALITA"
# Le squadre.
CAMBIO_AL_TAVOLO = "CAMBIO_AL_TAVOLO"
SOSTITUZIONE = "SOSTITUZIONE"

TIPI = (INIZIO_INCONTRO, SORTEGGIO, FORMAZIONI, RISCALDAMENTO_INIZIO, RISCALDAMENTO_COLPO, AVVISO_TEMPO, RISCALDAMENTO_FINE, INIZIO_SET, RECUPERO, CONSEGNA,
        ANNUNCIO, DOMANDA_PRONTO, FISCHIO, CHIAMATA, CAMBIO_BATTITORE, FINE_SET, FINE_INCONTRO,
        BATTUTA, VOLO, PARATA, CAMBIO_MANO, CONTROLLO, COLPO, GOAL, FALLO, PALLA_MORTA, ROTTURA, SOSTITUZIONE_ATTREZZO, RIPETIZIONE, PUNTO,
        TIMEOUT_INIZIO, TIMEOUT_FINE, CAMBIO_CAMPO_INIZIO, CAMBIO_CAMPO_FINE, AMMONIZIONE, PENALITA,
        CAMBIO_AL_TAVOLO, SOSTITUZIONE)

# Le fasi dell'incontro: la live salta il riscaldamento con un tasto.
PRELIMINARI = "preliminari"
RISCALDAMENTO = "riscaldamento"
GIOCO = "gioco"
PAUSA = "pausa"
CHIUSURA = "chiusura"

# I tre fischi dell'arbitro, sempre uguali come nella realtà.
SINGOLO = "singolo"
DOPPIO = "doppio"
LUNGO = "lungo"

# Le chiamate dell'arbitro nei termini italiani della FISPIC. Il let non c'è: l'arbitro del
# simulatore sa sempre che cosa è successo.
CHIAMATE = {
    "goal": "goal",
    "servizio_irregolare": "servizio irregolare",
    "schermo_centrale": "schermo centrale",
    "body_touch": "body touch",
    "difesa_irregolare": "difesa irregolare",
    "out": "out",
    "invasione": "invasione",
    "infrazione_paletta": "infrazione paletta",
    "infrazione_palla": "infrazione palla",
    "palla_morta": "palla morta",
    "ammonizione": "ammonizione",
    "penalita": "penalità",
    "time_out": "time-out",
    "cambio_campo": "cambio campo",
    "quindici_secondi": "15 secondi",
    "trenta_secondi": "30 secondi",
    "primo_servizio": "primo servizio",
    "secondo_servizio": "secondo servizio",
    "terzo_servizio": "terzo servizio",
    "si_ripete": "si ripete il servizio",
}


class Causa(NamedTuple):
    """Una causa IBSA: famiglia, articolo del regolamento, chiamata dell'arbitro, punti e frase per la cronaca."""
    famiglia: str
    articolo: str
    chiamata: str
    punti: int
    frase: str


def _c(famiglia, articolo, chiamata, punti, frase):
    return Causa(famiglia, articolo, chiamata, punti, frase)


CAUSE = {
    # La battuta irregolare: servizio irregolare, un punto a chi riceve.
    "battuta_senza_rimbalzo": _c("battuta", "15.3.7", "servizio_irregolare", 1, "la battuta di {chi} non tocca la sponda prima dello schermo"),
    "battuta_due_rimbalzi": _c("battuta", "15.3.7", "servizio_irregolare", 1, "la battuta di {chi} rimbalza due volte sulla sponda"),
    "battuta_strisciata": _c("battuta", "15.3.7 a", "servizio_irregolare", 1, "la battuta di {chi} striscia lungo la sponda"),
    "battuta_oltre_due_secondi": _c("battuta", "15.3.2", "servizio_irregolare", 1, "{chi} batte oltre i due secondi dal fischio"),
    "battuta_prima_del_fischio": _c("battuta", "15.3.3", "servizio_irregolare", 1, "{chi} batte prima del fischio"),
    "battuta_a_vuoto": _c("battuta", "15.3.6", "servizio_irregolare", 1, "{chi} manca la pallina, e il colpo a vuoto si sente"),
    "battuta_doppio_tocco": _c("battuta", "15.3.1", "servizio_irregolare", 1, "{chi} tocca due volte la pallina in battuta"),
    # L'attacco: schermo centrale e out.
    "schermo_contro": _c("attacco", "15.4.2", "schermo_centrale", 1, "la pallina di {chi} urta lo schermo e si ferma"),
    "schermo_sopra": _c("attacco", "15.4.1", "schermo_centrale", 1, "la pallina di {chi} passa sopra lo schermo"),
    "out_sponda": _c("attacco", "15.7.1", "out", 1, "la pallina di {chi} salta la sponda e finisce a terra"),
    "out_volo": _c("attacco", "15.7.1", "out", 1, "la pallina di {chi} vola fuori dal tavolo"),
    "out_tavola_contatto": _c("attacco", "15.7.2", "out", 1, "la pallina di {chi} sale sulla tavola di contatto"),
    "out_soffitto": _c("attacco", "15.7.3", "out", 1, "la pallina di {chi} colpisce il soffitto"),
    # La paletta che cade: in attacco, in difesa o nel controllo.
    "paletta_caduta": _c("paletta", "15.9.2", "infrazione_paletta", 1, "a {chi} cade la paletta"),
    # La difesa.
    "body_touch": _c("difesa", "15.5.1", "body_touch", 1, "la pallina tocca il corpo di {chi}"),
    "body_touch_pieno": _c("difesa", "15.5.1", "body_touch", 1, "la pallina colpisce in pieno il corpo di {chi}"),
    "difesa_irregolare": _c("difesa", "15.6.1", "difesa_irregolare", 1, "{chi} tocca la pallina dentro l'area di porta"),
    "invasione_mano_libera": _c("difesa", "15.8.1", "invasione", 1, "{chi} mette la mano libera nell'area di gioco"),
    "invasione_tavola_contatto": _c("difesa", "15.8.2", "invasione", 1, "{chi} afferra la tavola di contatto con la mano libera"),
    "out_in_difesa": _c("difesa", "15.7.1", "out", 1, "la parata di {chi} manda la pallina fuori dal tavolo"),
    # Il controllo.
    "pallina_trattenuta": _c("controllo", "15.10.1", "infrazione_palla", 1, "{chi} trattiene la pallina troppo a lungo"),
    # I goal, due punti.
    "goal_battuta": _c("goal", "15.2.1", "goal", 2, "la battuta entra in porta"),
    "goal_scambio": _c("goal", "15.2.1", "goal", 2, "la pallina entra in porta"),
    "goal_ribattuta": _c("goal", "15.2.1", "goal", 2, "la pallina tornata piano entra in porta"),
    "goal_dopo_difesa_irregolare": _c("goal", "15.6.1", "goal", 2, "{chi} tocca la pallina nell'area di porta, e la pallina entra lo stesso"),
    "autogoal": _c("goal", "15.2.1", "goal", 2, "la pallina sfugge a {chi} ed entra nella sua porta"),
    # La palla morta, nessun punto, si ripete il servizio.
    "colpo_debole": _c("palla_morta", "16.1", "palla_morta", 0, "il colpo di {chi} è troppo debole e la pallina si ferma prima di arrivare all'avversario"),
    "ribattuta_lenta": _c("palla_morta", "16.1", "palla_morta", 0, "la ribattuta di {chi} si ferma prima dello schermo"),
    "pallina_ferma": _c("palla_morta", "16.2", "palla_morta", 0, "la pallina sfugge a {chi} e resta ferma, senza suono"),
    "limite_tecnico": _c("palla_morta", "simulatore", "palla_morta", 0, "lo scambio non finisce più, e l'arbitro lo ferma"),
    # Le rotture, nessun punto, si ripete il servizio.
    "paletta_rotta": _c("rottura", "15.9.3", "si_ripete", 0, "la paletta di {chi} si rompe"),
    "pallina_rotta": _c("rottura", "15.10.2", "si_ripete", 0, "la pallina si rompe sul colpo di {chi}"),
    # Ammonizione e poi penalità, regola 19.3.
    "non_dal_fondo": _c("ammonizione", "19.3.1", "ammonizione", 2, "non gioca dal fondo del tavolo"),
    "mano_libera_al_tavolo": _c("ammonizione", "19.3.2", "ammonizione", 2, "si tiene al tavolo con la mano libera"),
    "pallina_col_dito": _c("ammonizione", "19.3.3", "ammonizione", 2, "aggancia la pallina con un dito"),
    "muovere_tavolo": _c("ammonizione", "19.3.4", "ammonizione", 2, "muove il tavolo"),
    "raschiare_paletta": _c("ammonizione", "19.3.5", "ammonizione", 2, "raschia la paletta sul tavolo"),
    "parlare": _c("ammonizione", "19.3.6", "ammonizione", 2, "parla durante il gioco"),
    "corpo_in_area_da_fuori": _c("ammonizione", "19.3.7", "ammonizione", 2, "spinge il corpo nell'area di porta da fuori"),
    "senza_piede_a_terra": _c("ammonizione", "19.3.8", "ammonizione", 2, "gioca senza un piede a terra"),
    "perdita_di_tempo": _c("ammonizione", "19.3.9", "ammonizione", 2, "perde tempo apposta"),
    # Penalità immediata, regola 19.4.
    "mascherina_toccata": _c("penalita", "19.4.1", "penalita", 2, "tocca la mascherina senza permesso"),
    "telefono": _c("penalita", "19.4.2", "penalita", 2, "ha un telefono che suona"),
}


@dataclasses.dataclass(slots=True)
class Evento:
    """
    Un evento della partita. Piatto e uguale per tutti i tipi: n è il progressivo nell'incontro,
    t i secondi simulati dall'inizio, durata zero per gli istantanei; set_n, punto_n e colpo_n
    dicono dove si è, con colpo_n zero per la battuta; chi è l'identificativo di chi agisce, None
    per l'arbitro, e parte la sua parte, A o B. La posizione è nel riferimento di A, lato e
    distanza sono visti da chi agisce. Gli eventi decisivi portano fischio e chiamata come
    riassunto, ma il suono viene soltanto dagli eventi FISCHIO e CHIAMATA che seguono.
    """
    n: int
    t: float
    tipo: str
    fase: str
    durata: float = 0.0
    set_n: int = 0
    punto_n: int = 0
    colpo_n: int = 0
    chi: int | None = None
    parte: str | None = None
    pos: tuple | None = None
    lato: str | None = None
    distanza: float | None = None
    volo: tuple | None = None
    colpo: str | None = None
    mano: str | None = None
    dritto: bool | None = None
    esito: str | None = None
    causa: str | None = None
    critico: bool = False
    fischio: str | None = None
    chiamata: str | None = None
    punti: int = 0
    a_chi: str | None = None
    punteggio: tuple | None = None
    dati: dict | None = None

    def a_dizionario(self):
        """L'evento come dizionario per il JSON, con le tappe del volo come elenchi."""
        dati = {campo.name: getattr(self, campo.name) for campo in dataclasses.fields(self)}
        if self.volo is not None:
            dati["volo"] = [tappa._asdict() for tappa in self.volo]
        if self.pos is not None:
            dati["pos"] = list(self.pos)
        if self.punteggio is not None:
            dati["punteggio"] = list(self.punteggio)
        return dati


def eventi_in_json(eventi):
    """Gli eventi come elenco di dizionari, pronti per json.dump."""
    return [evento.a_dizionario() for evento in eventi]
