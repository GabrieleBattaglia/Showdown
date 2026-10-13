"""
Test del formato 7 del salvataggio, tappa 12, punto 11 del progetto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
La catena intera dal formato 4, con un documento costruito sul modello del mondo di Gabriele, 61
giocatori, 9 tesserati e una polisportiva dell'utente con 3 tesserati, che passa dal 4 al 5, al 6 e
al 7, con giocatori, contratti e casse identici campo per campo a quelli della migrazione al 6;
l'andata e il ritorno del formato 7 con i campi nuovi; un formato 8 rifiutato. Ogni passo della
tappa che aggiunge un campo salvato allarga queste prove.
"""

import copy
import datetime
import json
import random

import pytest
from aiuti_formati import CAMPI_DEL_FORMATO_7, RINOMINATI_DEL_FORMATO_7, al_formato_5, al_formato_6

import archivio
from costanti import FILE_MONDO
from modelli import Polisportiva
from mondo import Mondo

INIZIO = datetime.datetime(2026, 9, 28, 9, 0)
INIZIO_UTC = datetime.datetime(2026, 9, 28, 7, 0, tzinfo=datetime.UTC)


def _mondo_come_quello_di_gabriele():
    """Un mondo piccolo come quello di Gabriele: 61 giocatori, una polisportiva del computer con 6 tesserati e una dell'utente con 3."""
    stato = random.getstate()
    random.seed(1961)
    try:
        m = Mondo()
        m.datetime_corrente_simulazione = INIZIO
        m.datetime_ultimo_run_reale = INIZIO_UTC
        m.crea_giocatori_casuali(61, INIZIO, annuncia=False)
        nome_cpu = m.crea_polisportiva_cpu(INIZIO)
        mia = Polisportiva("Brybox Showdown", None, INIZIO)
        m.polisportive[mia.nome] = mia
        m.miapolisportiva_attiva = mia
        attivi = sorted(m.giocatori)
        for gid in attivi[:6]:
            m._entra(m.polisportive[nome_cpu], m.giocatori[gid])
        for gid in attivi[6:9]:
            m._entra(mia, m.giocatori[gid])
        m.giocatori[attivi[10]].infortunato = True
        m.giocatori[attivi[10]].infortunio_fine_datetime = INIZIO + datetime.timedelta(days=4)
        m.aggiorna_stato_polisportive(annuncia=False)
    finally:
        random.setstate(stato)
    return m


def _al_formato_4(contenuto):
    vecchio = al_formato_5(contenuto)
    for g in vecchio["mondo"]["giocatori"]:
        for campo in ("temperamento", "infortunio_sede", "ultima_amichevole"):
            del g[campo]
    vecchio["formato"] = 4
    return vecchio


def _migra(documento, fino_a):
    documento = copy.deepcopy(documento)
    while documento["formato"] < fino_a:
        archivio.MIGRAZIONI[documento["formato"]](documento)
    return documento


def test_la_catena_dal_formato_4_al_7():
    mondo = _mondo_come_quello_di_gabriele()
    quarto = _al_formato_4(archivio.componi(mondo))
    sesto = _migra(quarto, 6)
    settimo = _migra(quarto, 7)
    assert sesto["formato"] == 6 and settimo["formato"] == 7
    per_id_6 = {g["id"]: g for g in sesto["mondo"]["giocatori"]}
    per_id_7 = {g["id"]: g for g in settimo["mondo"]["giocatori"]}
    assert len(per_id_7) == 61 and sum(1 for g in per_id_7.values() if g["appartenenza"] != "*") == 9
    for gid, g6 in per_id_6.items():
        g7 = per_id_7[gid]
        # Tutto quello che c'era nel formato 6 resta identico, contratti compresi; il 7 aggiunge soltanto, e rinomina l'ultima amichevole.
        rinominati = {RINOMINATI_DEL_FORMATO_7.get(campo, campo): valore for campo, valore in g6.items()}
        assert {campo: g7[campo] for campo in rinominati} == rinominati
        assert set(g7) - set(rinominati) == set(CAMPI_DEL_FORMATO_7)
        assert (g7["acciacco_fino"], g7["acciacco_calo"], g7["acciacco_giorni"], g7["acciacco_sede"]) == (None, 0.0, 0, None)
    for nome, p6 in sesto["mondo"]["polisportive"].items():
        p7 = settimo["mondo"]["polisportive"][nome]
        assert p7["cassa"] == p6["cassa"] and p7["tesserati"] == p6["tesserati"]
    # Il documento migrato si costruisce in un mondo, e i tesserati hanno il contratto.
    nuovo = Mondo()
    archivio.costruisci(settimo, nuovo)
    assert len(nuovo.giocatori) == 61 and len(nuovo.polisportive["Brybox Showdown"].tesserati) == 3
    assert all(nuovo.giocatori[gid].contratto_stipendio > 0 for gid in nuovo.polisportive["Brybox Showdown"].tesserati)


def test_l_ultima_amichevole_diventa_l_ultimo_impegno():
    mondo = _mondo_come_quello_di_gabriele()
    mondo.giocatori[12].ultimo_impegno = INIZIO
    sesto = al_formato_6(archivio.componi(mondo))
    assert next(g for g in sesto["mondo"]["giocatori"] if g["id"] == 12)["ultima_amichevole"] == INIZIO.isoformat()
    settimo = _migra(sesto, 7)
    per_id = {g["id"]: g for g in settimo["mondo"]["giocatori"]}
    assert per_id[12]["ultimo_impegno"] == INIZIO.isoformat() and all("ultima_amichevole" not in g for g in per_id.values())
    nuovo = Mondo()
    archivio.costruisci(settimo, nuovo)
    assert nuovo.giocatori[12].ha_un_impegno(INIZIO) and not nuovo.giocatori[13].ha_un_impegno(INIZIO)


def test_andata_e_ritorno_del_formato_7(cartella_di_prova):
    mondo = _mondo_come_quello_di_gabriele()
    g = mondo.giocatori[7]
    g.acciacco_fino = INIZIO + datetime.timedelta(days=5)
    g.acciacco_calo = 0.02
    g.acciacco_giorni = 5
    g.acciacco_sede = "caviglia"
    assert archivio.salva(mondo)
    ricaricato = Mondo()
    assert archivio.carica(ricaricato) == archivio.CARICATO
    for gid, originale in mondo.giocatori.items():
        assert vars(ricaricato.giocatori[gid]) == vars(originale)
    assert archivio.leggi(cartella_di_prova / FILE_MONDO)["formato"] == 7


def test_un_formato_8_si_rifiuta(cartella_di_prova):
    contenuto = archivio.componi(_mondo_come_quello_di_gabriele())
    contenuto["formato"] = 8
    percorso = cartella_di_prova / FILE_MONDO
    percorso.write_text(json.dumps({**contenuto, "firma": archivio.firma(contenuto)}), encoding="utf-8")
    with pytest.raises(archivio.ErroreSalvataggio, match="formato 8"):
        archivio.leggi(percorso)
