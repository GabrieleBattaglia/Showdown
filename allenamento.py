"""
L'allenamento dei giocatori di MESS: costo dei punti, allenamento a mano e autoallenamento.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 2 del piano, dallo smontaggio di sd.py, senza cambiare le
regole: la loro revisione è la tappa 10, per il problema P8.
I giocatori liberi e quelli delle polisportive del computer si allenano da soli: quattro volte
su cinque seguono il loro archetipo, altrimenti reagiscono allo stato del momento, rinforzando
il fisico se anziani, poi la caratteristica più debole, poi quella più forte.
"""

import math
import random

from costanti import (
    ALLENATE_FISICHE,
    ARCHETIPI_ALLENAMENTO,
    ATTRIBUTI_ALLENABILI,
    ETA_ANZIANO_MIN_GIORNI,
    ETA_GIOVANE_MAX_GIORNI,
    MAX_ALLENATO_FISICO,
    MAX_ALLENATO_SKILL,
    MAX_TOTALE_PRECISIONE_RESISTENZA,
    MAX_TOTALE_SKILL_GIOCO,
    MAX_XP_PER_ALLENAMENTO,
    PROB_SEGUE_ARCHETIPO,
    XP_COSTO_FISICO_MOLTIPL,
    XP_COSTO_SKILL_BREAKPOINTS,
    XP_SCONTO_IPOVEDENTI_PERC,
)
from modelli import e_fisica
from utilita import caso


def limiti(nome_allenato):
    """Il tetto della parte allenata e quello del totale per una caratteristica allenabile."""
    if e_fisica(nome_allenato):
        return MAX_ALLENATO_FISICO, MAX_TOTALE_PRECISIONE_RESISTENZA
    return MAX_ALLENATO_SKILL, MAX_TOTALE_SKILL_GIOCO


def calcola_costo_xp_per_punto(val_allenato, is_fis, is_ipo):
    """
    Quanti punti esperienza costa un punto di caratteristica, partendo dal valore allenato:
    il costo cresce in linea retta fra i gradini della tabella, si raddoppia per le
    caratteristiche fisiche e si sconta per gli ipovedenti su quelle di gioco.
    """
    liv_calc = min(val_allenato, MAX_ALLENATO_FISICO if is_fis else MAX_ALLENATO_SKILL)
    bp_inf = 0
    bps = sorted(XP_COSTO_SKILL_BREAKPOINTS.keys())
    for bp in bps:
        if liv_calc >= bp:
            bp_inf = bp
        else:
            break
    costo_base = XP_COSTO_SKILL_BREAKPOINTS[bp_inf]
    idx_inf = bps.index(bp_inf)
    bp_sup = bps[idx_inf + 1] if idx_inf + 1 < len(bps) else bp_inf
    costo_sup = XP_COSTO_SKILL_BREAKPOINTS[bp_sup]
    costo = costo_base
    if bp_sup > bp_inf:
        costo = costo_base + ((liv_calc - bp_inf) / (bp_sup - bp_inf)) * (costo_sup - costo_base)
    if is_fis:
        costo *= XP_COSTO_FISICO_MOLTIPL
    if is_ipo and not is_fis:
        costo *= (1. - XP_SCONTO_IPOVEDENTI_PERC / 100.)
    return max(1., costo)


def costo_per(giocatore, nome_allenato):
    """Il costo di un punto della caratteristica indicata, per quel giocatore."""
    return calcola_costo_xp_per_punto(getattr(giocatore, nome_allenato, 0.), e_fisica(nome_allenato), giocatore.ipovedente)


def guadagno(val_allenato, val_base, xp_spesa, costo_pt, lim_a, lim_t):
    """
    Quanto rende una spesa di esperienza su una caratteristica, rispettando i due tetti.
    Restituisce il nuovo valore allenato, il guadagno effettivo, i punti esperienza davvero
    necessari quando un tetto taglia il guadagno, e se un tetto è intervenuto.
    """
    guad_p = xp_spesa / costo_pt
    nuovo = val_allenato + guad_p
    limitato = False
    if nuovo > lim_a:
        nuovo = lim_a
        limitato = True
    if val_base + nuovo > lim_t:
        nuovo = max(0., lim_t - val_base)
        limitato = True
    guad_eff = max(0., nuovo - val_allenato) if limitato else guad_p
    return nuovo, guad_eff, limitato


def fascia_eta(giocatore):
    if giocatore.eta <= ETA_GIOVANE_MAX_GIORNI:
        return "giovane"
    if giocatore.eta >= ETA_ANZIANO_MIN_GIORNI:
        return "anziano"
    return "prime"


def _allenabili(giocatore, nomi):
    """Le caratteristiche dell'elenco che non hanno ancora raggiunto i loro tetti."""
    pronte = []
    for s in nomi:
        if hasattr(giocatore, s):
            v_a = getattr(giocatore, s, 0.)
            v_b = getattr(giocatore, s.replace('_allenata', '_base'), 0.)
            lim_a, lim_t = limiti(s)
            if v_a < lim_a and (v_b + v_a) < lim_t:
                pronte.append(s)
    return pronte


def _piu_bassa(giocatore, nomi, predefinito=float('inf')):
    return min(nomi, key=lambda s: getattr(giocatore, s, predefinito))


def _fisica_bassa(giocatore, disponibili, soglia=3.):
    """Fra precisione, resistenza e forza, quella allenata più bassa fra le disponibili con totale sotto la soglia."""
    basse = [s for s in ALLENATE_FISICHE if s in disponibili and giocatore._get_valore_totale(s.replace('_allenata', '_base')) < soglia]
    return _piu_bassa(giocatore, basse, 0) if basse else None


def _scelta_da_archetipo(giocatore, cfg, str_scelta, skill_ok):
    """La caratteristica da allenare secondo la strategia di scelta dell'archetipo."""
    skill_scelta = None
    non_fisiche = [s for s in skill_ok if not e_fisica(s)]
    fisiche = [s for s in skill_ok if e_fisica(s)]
    if str_scelta == "piu_bassa_prioritaria":
        skill_scelta = _piu_bassa(giocatore, skill_ok)
    elif str_scelta == "piu_economica_prioritaria":
        costi = {s: costo_per(giocatore, s) for s in skill_ok}
        skill_scelta = min(costi, key=costi.get)
    elif str_scelta == "a_rotazione":
        skill_scelta = random.choice(skill_ok)
    elif str_scelta == "piu_bassa_tra_due":
        skill_scelta = _piu_bassa(giocatore, fisiche) if fisiche else random.choice(skill_ok)
    elif str_scelta == "piu_bassa_assoluta_non_fisica":
        skill_scelta = _piu_bassa(giocatore, non_fisiche) if non_fisiche else random.choice(skill_ok)
    elif str_scelta == "piu_economica_prioritaria_o_resistenza":
        if "resistenza_allenata" in skill_ok and giocatore._get_valore_totale("resistenza_base") < 3.:
            skill_scelta = "resistenza_allenata"
        else:
            costi = {s: costo_per(giocatore, s) for s in skill_ok}
            skill_scelta = min(costi, key=costi.get)
    elif str_scelta == "piu_bassa_tra_due_assoluta":
        skill_scelta = _piu_bassa(giocatore, fisiche) if fisiche else skill_ok[0]
    elif str_scelta == "piu_bassa_assoluta_o_fisica_bassa":
        skill_scelta = _fisica_bassa(giocatore, skill_ok)
        if not skill_scelta:
            skill_scelta = _piu_bassa(giocatore, non_fisiche) if non_fisiche else random.choice(skill_ok)
    if not skill_scelta:
        skill_scelta = random.choice(skill_ok)
    return skill_scelta


def _spesa_da_archetipo(giocatore, str_spesa, skill_scelta, xp_disp):
    """I punti esperienza da spendere secondo la strategia di spesa dell'archetipo."""
    t_spesa = str_spesa.get("tipo", "perc")
    v_spesa = str_spesa.get("valore", 10)
    max_xp = str_spesa.get("max_xp", MAX_XP_PER_ALLENAMENTO)
    if t_spesa == "perc":
        xp_spend = min(int(xp_disp * (v_spesa / 100.)), xp_disp, max_xp)
    elif t_spesa == "quota":
        xp_spend = min(int(v_spesa), xp_disp, max_xp)
    elif t_spesa == "obiettivo":
        costo_p = costo_per(giocatore, skill_scelta)
        xp_calc = math.ceil(costo_p * v_spesa) if costo_p > 0 else 0
        xp_spend = min(xp_calc, xp_disp, max_xp)
    else:
        # Le strategie degli archetipi si chiamano percentuale, quota_fissa e obiettivo_punti, che
        # non corrispondono a nessuno dei nomi qui sopra: finiscono tutte qui, al 10 per cento.
        # È il comportamento del vecchio sd.py, da rivedere alla tappa 10.
        xp_spend = min(int(xp_disp * 0.1), max_xp)
    return max(0, xp_spend)


def _segui_archetipo(giocatore, arch_nome, xp_disp):
    cfg = ARCHETIPI_ALLENAMENTO[arch_nome]
    priorita = list(cfg.get("priorita", []))
    if arch_nome == "TuttofareBilanciato":
        priorita = list(cfg.get("priorita_non_fisiche", [])) + list(cfg.get("priorita_fisiche", []))
    str_scelta_base = cfg.get("strategia_scelta", "piu_bassa_prioritaria")
    str_spesa = cfg.get("strategia_spesa", {"tipo": "perc", "valore": 10, "max_xp": 200})
    str_scelta = cfg.get("influenza_eta", {}).get(fascia_eta(giocatore), str_scelta_base)
    skill_ok = _allenabili(giocatore, priorita)
    if not skill_ok:
        return None, 0
    skill_scelta = _scelta_da_archetipo(giocatore, cfg, str_scelta, skill_ok)
    return skill_scelta, _spesa_da_archetipo(giocatore, str_spesa, skill_scelta, xp_disp)


def _reagisci(giocatore, xp_disp):
    """La scelta reattiva: fisico per gli anziani, poi la debolezza più grave, poi la specialità."""
    skill_nf = _allenabili(giocatore, [s for s in ATTRIBUTI_ALLENABILI if not e_fisica(s)])
    skill_f = _allenabili(giocatore, [s for s in ATTRIBUTI_ALLENABILI if e_fisica(s)])
    skill_scelta = None
    xp_spend = 0
    if fascia_eta(giocatore) == "anziano":
        allenare = _fisica_bassa(giocatore, skill_f)
        if allenare:
            skill_scelta = allenare
            xp_spend = min(xp_disp, 350)
    if not skill_scelta and skill_nf:
        vals = {s: getattr(giocatore, s, 0.) for s in skill_nf}
        p_b = min(vals, key=vals.get)
        if vals[p_b] < 5.:
            skill_scelta = p_b
            xp_spend = min(xp_disp, 250)
    if not skill_scelta and skill_nf:
        vals = {s: getattr(giocatore, s, 0.) for s in skill_nf}
        skill_scelta = max(vals, key=vals.get)
        xp_spend = min(xp_disp, 450)
    if not skill_scelta and (skill_nf or skill_f):
        costi = {s: costo_per(giocatore, s) for s in skill_nf + skill_f}
        skill_scelta = min(costi, key=costi.get)
        xp_spend = min(int(xp_disp * .15), 300)
    return skill_scelta, xp_spend


def esegui_auto_allenamento(giocatore, data=None):
    """
    Un giocatore libero o di una polisportiva del computer spende da solo la sua esperienza.
    Con la data simulata, l'allenamento finisce anche nel suo diario.
    """
    xp_disp = int(giocatore.puntiesperienza or 0)
    if xp_disp <= 0 or giocatore.ritirato or giocatore.infortunato:
        return
    arch_nome = getattr(giocatore, 'archetipo_allenamento', "Non Definito")
    if arch_nome == "Non Definito" or arch_nome not in ARCHETIPI_ALLENAMENTO:
        validi = list(ARCHETIPI_ALLENAMENTO.keys())
        arch_nome = random.choice(validi) if validi else "TuttofareBilanciato"
        giocatore.archetipo_allenamento = arch_nome
    if caso(PROB_SEGUE_ARCHETIPO):
        skill_scelta, xp_spend = _segui_archetipo(giocatore, arch_nome, xp_disp)
        if skill_scelta is None:
            return
    else:
        skill_scelta, xp_spend = _reagisci(giocatore, xp_disp)
    if not skill_scelta or xp_spend <= 0:
        return
    v_a_att = getattr(giocatore, skill_scelta)
    v_b = getattr(giocatore, skill_scelta.replace('_allenata', '_base'), 0.)
    lim_a, lim_t = limiti(skill_scelta)
    if v_a_att >= lim_a or v_b + v_a_att >= lim_t:
        return
    xp_eff = min(xp_spend, xp_disp)
    costo_pt = calcola_costo_xp_per_punto(v_a_att, e_fisica(skill_scelta), giocatore.ipovedente)
    if costo_pt <= 0:
        return
    nuovo, guad_eff, limitato = guadagno(v_a_att, v_b, xp_eff, costo_pt, lim_a, lim_t)
    if limitato:
        xp_eff = min(xp_eff, math.ceil(guad_eff * costo_pt), xp_disp)
    else:
        xp_eff = min(math.ceil(guad_eff * costo_pt), xp_disp)
    if xp_eff > 0 and guad_eff > 1e-4:
        setattr(giocatore, skill_scelta, nuovo)
        giocatore.puntiesperienza = max(0, xp_disp - xp_eff)
        giocatore.aggiorna_icv()
        if data is not None:
            giocatore.annota_allenamento(data, skill_scelta.replace('_allenata', '_base'), v_b + v_a_att, v_b + nuovo)
