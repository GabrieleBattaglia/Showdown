"""
La catena degli esiti di un punto di showdown, nel motore di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9, decisione D25, e chiude il problema P1. La catena decide che
cosa succede, con probabilità pure, senza geometria e senza testi: battuta, parata, controllo,
attacco, e di nuovo parata, finché qualcuno segna o sbaglia. Ogni dado ha fasce esaustive, quindi
non ci sono rami irraggiungibili come nel vecchio motore, dove quasi ogni azione diventava un fallo,
e nessun ramo assegna un punto a caso.
La battuta è un colpo come gli altri: se è regolare, chi riceve la para, e il goal di battuta nasce
solo da una parata che non arriva. La parata confronta la pressione dell'attacco con la chiusura e
il blocco di chi difende: ne escono goal, fallo, fuori, ribattuta o fermata. Se la pallina passa lo
decide la chiusura, con una parte del blocco, PESO_BLOCCO_PARATA; il contatto, ribattuta o
fermata, pesa sempre come alla pari, e il blocco sceglie soltanto come finisce: è la correzione
venuta dalla taratura del valore, perché nel softmax unico del progetto un blocco migliore
spostava peso anche su goal e falli, e allenarlo faceva perdere punti. Il tiro critico vale
sempre un punto, e sceglie soltanto una causa più clamorosa.
Con l'elenco passi la catena annota ogni passo, per la regia che ne farà eventi e posizioni; senza,
in modalità essenziale, non crea nulla. Le statistiche dei giocatori le aggiorna la catena stessa,
così valgono uguali nelle due modalità.
"""

import math
from typing import NamedTuple

from costanti import COLPI_DELLO_SCAMBIO, COLPI_DI_BATTUTA, PUNTI_PER_FALLO_AVVERSARIO, PUNTI_PER_GOAL
from motore.campo import scegli


class Passo(NamedTuple):
    """Un passo della catena, per la regia: chi lo compie è l'InCampo; valore è qualità, pressione o tempo, prob le fasce."""
    tipo: str
    chi: object
    colpo: str | None = None
    zona: str | None = None
    esito: str | None = None
    causa: str | None = None
    critico: bool = False
    valore: float | None = None
    prob: tuple | None = None


class EsitoPunto(NamedTuple):
    """
    Come è finito un punto. esito è goal, fallo, palla_morta o rottura; a_chi la parte che riceve
    i punti; origine dice da dove nasce la fine, battuta, scambio, ribattuta o controllo. I campi
    dell'incontro li riempie l'Incontro, con _replace.
    """
    esito: str
    causa: str
    critico: bool
    chi_commette: int | None
    a_chi: str | None
    punti: int
    attacchi: int
    origine: str
    colpo_decisivo: str | None
    zona: str | None
    set_n: int = 0
    punto_n: int = 0
    battitore: int | None = None
    ricevitore: int | None = None
    parte_battitore: str | None = None
    numero_servizio: int = 0
    punteggio: tuple = (0, 0)
    sanzioni_prima: tuple = ()


ZONE_RIBATTUTA = ("sx", "centro", "dx")


def gioca_punto(battitore, ricevitore, dado, taratura, passi=None, rottura_al_colpo=0, causa_rottura="paletta_rotta"):
    """
    Gioca un punto fra due InCampo già preparati e restituisce l'EsitoPunto. Con passi, un
    elenco, vi annota i passi per la regia. Con rottura_al_colpo, se lo scambio arriva a quel
    colpo, il punto si ferma lì con la rottura indicata, senza punti.
    """
    t = taratura
    tiro = dado.tiro
    fascia = dado.fascia
    q0 = t.Q0
    kskill = t.K_SKILL_FALLI
    critico_quota = t.QUOTA_CRITICO
    colpi_tabella = t.COLPI
    log = math.log
    exp = math.exp
    e_r0 = exp(t.R0)
    peso_blocco = t.PESO_BLOCCO_PARATA
    annota = passi.append if passi is not None else None

    # La battuta.
    indice = scegli(battitore.cum_battute, tiro())
    nome_battuta = COLPI_DI_BATTUTA[indice]
    battitore.conta_azione()
    q = battitore.QB[indice] * battitore.eff
    p_irr = min(t.P_FALLO_MASSIMA, t.P_BATTUTA_IRREGOLARE * battitore.mf * exp(-kskill * (q - 50.0) / 50.0))
    fascia_battuta, residuo = fascia((p_irr, 1.0 - p_irr))
    if fascia_battuta == 0:
        critico = residuo < critico_quota
        causa = dado.pesata(t.CAUSE_BATTUTA_CRITICHE if critico else battitore.pesi_cause_battuta)
        if annota:
            annota(Passo("battuta", battitore, nome_battuta, None, "irregolare", causa, critico, q, (p_irr, 1.0 - p_irr)))
            annota(Passo("fallo", battitore, nome_battuta, None, "fallo", causa, critico))
        return _fallo(battitore, ricevitore, causa, critico, 0, "battuta", nome_battuta, None)
    colpo_battuta = colpi_tabella[nome_battuta]
    zona = colpo_battuta.zona if tiro() < t.QUOTA_BATTUTA_LATERALE else "centro"
    pressione = t.PRESSIONE_BATTUTA * q
    if annota:
        annota(Passo("battuta", battitore, nome_battuta, zona, "regolare", None, False, pressione, (p_irr, 1.0 - p_irr)))

    attaccante, difensore = battitore, ricevitore
    origine = "battuta"
    colpo_corrente = nome_battuta
    colpi = 0
    limite = t.LIMITE_COLPI_PUNTO
    while True:
        # La parata di chi difende, contro la pressione del colpo che arriva nella sua zona.
        difensore.conta_azione()
        d, b, cambio = difensore.difesa(zona)
        if cambio and annota:
            annota(Passo("cambio_mano", difensore, None, zona, None, None, False, None, None))
        eff = difensore.eff
        d *= eff
        b *= eff
        # Se la pallina passa lo decide soprattutto la chiusura, ma anche il blocco: una pallina
        # toccata e non fermata può finire in porta lo stesso.
        r = log((pressione + q0) / (d + peso_blocco * (b - d) + q0))
        rb = log((pressione + q0) / (b + q0))
        ln_mf = difensore.ln_mf
        e_goal = exp(t.G0 + t.KG * r)
        e_fallo = exp(t.F0 + t.KF * r + ln_mf)
        e_fuori = exp(t.O0 + t.KO * r + ln_mf)
        e_ribattuta = exp(t.R0 + t.KR * rb)
        # Il contatto, cioè ribattuta o fermata, pesa sempre quanto alla pari: la chiusura decide se
        # la pallina passa, il blocco soltanto come finisce il contatto. In un softmax unico un
        # blocco migliore toglieva peso alla ribattuta e lo spargeva anche su goal e falli: la
        # taratura del valore l'ha scoperto, perché allenare il blocco faceva perdere punti.
        contatto = 1.0 + e_r0
        totale = e_goal + e_fallo + e_fuori + contatto
        p_contatto = contatto / totale
        p_ribattuta = p_contatto * e_ribattuta / (1.0 + e_ribattuta)
        probabilita = (e_goal / totale, e_fallo / totale, e_fuori / totale, p_ribattuta, p_contatto - p_ribattuta)
        esito_parata, residuo = fascia(probabilita)
        if esito_parata == 0:
            causa = {"battuta": "goal_battuta", "ribattuta": "goal_ribattuta"}.get(origine, "goal_scambio")
            if annota:
                annota(Passo("parata", difensore, colpo_corrente, zona, "goal", causa, False, d, probabilita))
                annota(Passo("goal", attaccante, colpo_corrente, zona, "goal", causa))
            return _goal(attaccante, difensore, causa, None, colpi, origine, colpo_corrente, zona)
        if esito_parata == 1:
            critico = residuo < critico_quota
            if critico:
                causa = dado.pesata(t.CAUSE_DIFESA_CRITICHE_CENTRO if zona == "centro" else t.CAUSE_DIFESA_CRITICHE)
            else:
                causa = dado.pesata(t.CAUSE_DIFESA)
            if causa == "difesa_irregolare" and tiro() < t.QUOTA_DIFESA_IRREGOLARE_IN_PORTA:
                if annota:
                    annota(Passo("parata", difensore, colpo_corrente, zona, "fallo", "difesa_irregolare", False, d, probabilita))
                    annota(Passo("goal", attaccante, colpo_corrente, zona, "goal", "goal_dopo_difesa_irregolare"))
                return _goal(attaccante, difensore, "goal_dopo_difesa_irregolare", difensore.id, colpi, origine, colpo_corrente, zona)
            if annota:
                annota(Passo("parata", difensore, colpo_corrente, zona, "fallo", causa, critico, d, probabilita))
                annota(Passo("fallo", difensore, colpo_corrente, zona, "fallo", causa, critico))
            return _fallo(difensore, attaccante, causa, critico, colpi, origine, colpo_corrente, zona)
        if esito_parata == 2:
            if annota:
                annota(Passo("parata", difensore, colpo_corrente, zona, "fuori", "out_in_difesa", False, d, probabilita))
                annota(Passo("fallo", difensore, colpo_corrente, zona, "fallo", "out_in_difesa", False))
            return _fallo(difensore, attaccante, "out_in_difesa", False, colpi, origine, colpo_corrente, zona)
        if esito_parata == 3:
            # La ribattuta: la pallina torna piano a chi aveva attaccato. È un colpo dello scambio.
            if annota:
                annota(Passo("parata", difensore, colpo_corrente, zona, "ribattuta", None, False, d, probabilita))
            if tiro() < t.P_RIBATTUTA_LENTA:
                if annota:
                    annota(Passo("palla_morta", difensore, None, zona, "palla_morta", "ribattuta_lenta"))
                return _palla_morta(difensore, "ribattuta_lenta", colpi, "ribattuta", None, zona)
            colpi += 1
            esito_limite = _controlla_colpo(colpi, rottura_al_colpo, causa_rottura, limite, difensore, zona, annota)
            if esito_limite is not None:
                return esito_limite
            pressione = t.PRESSIONE_RIBATTUTA * d
            zona = ZONE_RIBATTUTA[dado.intero(0, 2)]
            if annota:
                annota(Passo("ribattuta", difensore, None, zona, "ribattuta", None, False, pressione, None))
            attaccante, difensore = difensore, attaccante
            origine = "ribattuta"
            colpo_corrente = None
            _aggiorna_scambio(attaccante, difensore, colpi)
            continue
        # La fermata, forse sporca, e poi il controllo palla.
        sporca = residuo < t.SOGLIA_FERMATA_SPORCA
        if annota:
            annota(Passo("parata", difensore, colpo_corrente, zona, "fermata", "sporca" if sporca else None, False, d, probabilita))
        difensore.conta_azione()
        qc = difensore.C * difensore.eff
        k = exp(-kskill * (qc - 50.0) / 50.0)
        p_trattenuta = t.P_TRATTENUTA * k * max(0.0, 1.0 - t.K_TEMP_TRATTENUTA * difensore.tau)
        if difensore.giocorapido:
            p_trattenuta *= 0.5
        p_sfuggita = t.P_SFUGGITA * k * difensore.mf
        if sporca:
            p_sfuggita *= 1.0 + t.MAGGIORAZIONE_FERMATA_SPORCA
        p_sfuggita = min(p_sfuggita, 0.9 - p_trattenuta)
        prob_controllo = (p_trattenuta, p_sfuggita, 1.0 - p_trattenuta - p_sfuggita)
        esito_controllo, residuo = fascia(prob_controllo)
        if esito_controllo == 0:
            critico = residuo < critico_quota
            causa = "paletta_caduta" if critico else "pallina_trattenuta"
            if annota:
                annota(Passo("controllo", difensore, None, zona, "trattenuta", causa, critico, qc, prob_controllo))
                annota(Passo("fallo", difensore, None, zona, "fallo", causa, critico))
            return _fallo(difensore, attaccante, causa, critico, colpi, "controllo", None, zona)
        if esito_controllo == 1:
            if annota:
                annota(Passo("controllo", difensore, None, zona, "sfuggita", None, False, qc, prob_controllo))
            u = tiro()
            if u < t.QUOTA_AUTOGOAL:
                if annota:
                    annota(Passo("sfuggita", difensore, None, zona, "autogoal", "autogoal"))
                    annota(Passo("goal", attaccante, None, zona, "goal", "autogoal"))
                return _goal(attaccante, difensore, "autogoal", difensore.id, colpi, "controllo", None, zona)
            if u < t.QUOTA_AUTOGOAL + t.QUOTA_PALLINA_FERMA:
                if annota:
                    annota(Passo("sfuggita", difensore, None, zona, "pallina_ferma", "pallina_ferma"))
                    annota(Passo("palla_morta", difensore, None, zona, "palla_morta", "pallina_ferma"))
                return _palla_morta(difensore, "pallina_ferma", colpi, "controllo", None, zona)
            tempo = t.TEMPO_DOPO_RECUPERO
            if annota:
                annota(Passo("sfuggita", difensore, None, zona, "recupero", None, False, tempo, None))
        else:
            tempo = min(1.0, t.TEMPO_BASE + t.TEMPO_SCALA * (qc + q0) / (qc + q0 + t.TEMPO_MEZZO)) * (0.85 + 0.15 * residuo)
            if annota:
                annota(Passo("controllo", difensore, None, zona, "riuscito", None, False, tempo, prob_controllo))
        # L'attacco di chi ha controllato.
        attaccante, difensore = difensore, attaccante
        colpi += 1
        esito_limite = _controlla_colpo(colpi, rottura_al_colpo, causa_rottura, limite, attaccante, zona, annota)
        if esito_limite is not None:
            return esito_limite
        indice = scegli(attaccante.cum_colpi, tiro())
        nome = COLPI_DELLO_SCAMBIO[indice]
        colpo = colpi_tabella[nome]
        attaccante.conta_azione()
        attaccante.osservati += 1
        q = attaccante.Q[indice] * attaccante.eff
        tau = attaccante.tau
        p_fallo = min(t.P_FALLO_MASSIMA, colpo.fallo_base * attaccante.mf * exp(-kskill * (q - 50.0) / 50.0)
                      * (1.0 + t.K_TEMPO_FALLI * (1.0 - tempo)) * max(0.0, 1.0 + t.RISCHIO_POTENZA * tau * colpo.potenza))
        if nome == "bomba":
            p_debole = 0.0
        else:
            p_debole = t.P_COLPO_DEBOLE * (1.0 + 2.0 * (1.0 - attaccante.forza)) * (1.0 + (1.0 - tempo))
        prob_attacco = (p_fallo, p_debole, 1.0 - p_fallo - p_debole)
        esito_attacco, residuo = fascia(prob_attacco)
        stats = attaccante.stats
        stats.attacchi += 1
        stats.colpi[nome] += 1
        stats.attacchi_verso[colpo.zona] += 1
        if esito_attacco == 0:
            critico = residuo < critico_quota
            if critico:
                causa = dado.pesata(t.CAUSE_ATTACCO_CRITICHE)
            elif tiro() < colpo.quota_schermo:
                quota_sopra = t.QUOTA_SCHERMO_SOPRA_BOMBA if nome == "bomba" else t.QUOTA_SCHERMO_SOPRA
                causa = "schermo_sopra" if tiro() < quota_sopra else "schermo_contro"
            else:
                quota_contatto = t.QUOTA_OUT_CONTATTO_BOMBA if nome == "bomba" else t.QUOTA_OUT_CONTATTO
                causa = "out_tavola_contatto" if tiro() < quota_contatto else "out_sponda"
            if annota:
                annota(Passo("colpo", attaccante, nome, colpo.zona, "fallo", causa, critico, q, prob_attacco))
                annota(Passo("fallo", attaccante, nome, colpo.zona, "fallo", causa, critico))
            return _fallo(attaccante, difensore, causa, critico, colpi, "scambio", nome, colpo.zona)
        if esito_attacco == 1:
            if annota:
                annota(Passo("colpo", attaccante, nome, colpo.zona, "debole", "colpo_debole", False, q, prob_attacco))
                annota(Passo("palla_morta", attaccante, nome, colpo.zona, "palla_morta", "colpo_debole"))
            return _palla_morta(attaccante, "colpo_debole", colpi, "scambio", nome, colpo.zona)
        pressione = q * (1.0 + colpo.bonus) * (1.0 + t.PRESSIONE_TEMPERAMENTO * tau) * (t.PRESSIONE_TEMPO_BASE + (1.0 - t.PRESSIONE_TEMPO_BASE) * tempo)
        if attaccante.giocorapido and tempo >= t.TEMPO_GIOCO_RAPIDO:
            pressione *= 1.0 + t.BONUS_GIOCO_RAPIDO
        if attaccante.cambiovelocita:
            pressione *= 1.0 + t.BONUS_CAMBIO_VELOCITA
        zona = colpo.zona
        if annota:
            annota(Passo("colpo", attaccante, nome, zona, "colpo", None, False, pressione, prob_attacco))
        origine = "scambio"
        colpo_corrente = nome
        _aggiorna_scambio(attaccante, difensore, colpi)


def _aggiorna_scambio(a, b, colpi):
    if colpi > a.stats.scambio_piu_lungo:
        a.stats.scambio_piu_lungo = colpi
    if colpi > b.stats.scambio_piu_lungo:
        b.stats.scambio_piu_lungo = colpi


def _controlla_colpo(colpi, rottura_al_colpo, causa_rottura, limite, chi, zona, annota):
    """La rottura al colpo indicato e il limite tecnico dei colpi, prima che il colpo si giochi."""
    if rottura_al_colpo and colpi == rottura_al_colpo:
        if annota:
            annota(Passo("rottura", chi, None, zona, "rottura", causa_rottura))
        return EsitoPunto("rottura", causa_rottura, False, chi.id, None, 0, colpi - 1, "scambio", None, zona)
    if colpi >= limite:
        if annota:
            annota(Passo("palla_morta", chi, None, zona, "palla_morta", "limite_tecnico"))
        return EsitoPunto("palla_morta", "limite_tecnico", False, None, None, 0, colpi - 1, "scambio", None, zona)
    return None


def _goal(segna, subisce, causa, chi_commette, colpi, origine, colpo, zona):
    segna.stats.goal += 1
    if origine == "battuta":
        segna.stats.goal_battuta += 1
    subisce.stats.goal_subiti += 1
    if causa == "goal_dopo_difesa_irregolare":
        # La difesa irregolare resta un fallo di chi difende, anche se il punto è un goal: un
        # fallo fatto da lui e subito da chi segna, perché i due conti tornino.
        subisce.stats.falli[causa] += 1
        segna.stats.falli_subiti += 1
    return EsitoPunto("goal", causa, False, chi_commette, segna.parte, PUNTI_PER_GOAL, colpi, origine, colpo, zona)


def _fallo(commette, subisce, causa, critico, colpi, origine, colpo, zona):
    commette.stats.falli[causa] += 1
    subisce.stats.falli_subiti += 1
    return EsitoPunto("fallo", causa, critico, commette.id, subisce.parte, PUNTI_PER_FALLO_AVVERSARIO, colpi, origine, colpo, zona)


def _palla_morta(chi, causa, colpi, origine, colpo, zona):
    return EsitoPunto("palla_morta", causa, False, chi.id, None, 0, colpi, origine, colpo, zona)

