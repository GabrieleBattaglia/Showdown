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
from aiuti_calendario import apri, iscrivi_tutti
from aiuti_formati import CAMPI_DEL_FORMATO_7, RINOMINATI_DEL_FORMATO_7, al_formato_5, al_formato_6

import archivio
import iscrizioni
import sfide
from costanti import FILE_MONDO
from modelli import CAMPI_AGGREGATA_GIOCATORE, Polisportiva, annota_aggregata
from mondo import Mondo
from motore import Squadra
from partita import differita_squadre

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


def test_la_data_del_ritmo_sparsa_alla_migrazione():
    mondo = _mondo_come_quello_di_gabriele()
    settimo = _migra(_al_formato_4(archivio.componi(mondo)), 7)
    distanze = {(datetime.datetime.fromisoformat(g["prossimo_torneo"]) - INIZIO).days for g in settimo["mondo"]["giocatori"]}
    assert min(distanze) >= 0 and max(distanze) <= 60 and len(distanze) > 20
    assert all(g["iscrizione_automatica"] is True for g in settimo["mondo"]["giocatori"])
    assert settimo["mondo"]["calendario"]["edizioni"] == [] and settimo["mondo"]["calendario"]["albo"]["voci"] == []
    assert all(set(p["conti_del_mese"]) >= {"iscrizioni", "premi", "rimborsi"} and p["palmares_recente"] == {} for p in settimo["mondo"]["polisportive"].values())
    # Le sfide: il registro vuoto, due da lanciare per ogni polisportiva, nessuna giocata.
    assert settimo["mondo"]["sfide"] == {"attive": [], "storico": [], "prossimo_id": 1, "giocate_oggi": {"data": None, "ids": []}}
    assert all((p["sfide_da_lanciare"], p["ultima_sfida"], p["sfide_vinte"], p["sfide_perse"]) == (2, None, 0, 0)
               for p in settimo["mondo"]["polisportive"].values())
    assert all((g["gare_squadre_vinte"], g["gare_squadre_perse"]) == (0, 0) for g in settimo["mondo"]["giocatori"])


def test_andata_e_ritorno_del_formato_7(cartella_di_prova):
    mondo = _mondo_come_quello_di_gabriele()
    g = mondo.giocatori[7]
    g.acciacco_fino = INIZIO + datetime.timedelta(days=5)
    g.acciacco_calo = 0.02
    g.acciacco_giorni = 5
    g.acciacco_sede = "caviglia"
    # Un torneo a metà, con le iscrizioni aperte di un'altra edizione, la voce aggregata e il palmarès.
    edizioni = apri(mondo, INIZIO, "Open maschile del martedì")
    uomini = [gid for gid, x in sorted(mondo.giocatori.items()) if x.sesso == "m"][:12]
    iscrivi_tutti(edizioni[0], mondo, uomini)
    martedi = INIZIO + datetime.timedelta(days=1)
    mondo.datetime_corrente_simulazione = martedi
    mondo.calendario.sorteggi(mondo, martedi, Mondo.rapporto_vuoto(martedi))
    mondo.calendario.gioca(mondo, martedi, Mondo.rapporto_vuoto(martedi))
    assert mondo.calendario.tornei and mondo.calendario.edizioni
    annota_aggregata(mondo.giocatori[3].diario, martedi, CAMPI_AGGREGATA_GIOCATORE, tornei=1, incontri=3, vinti=2)
    mia = mondo.polisportive["Brybox Showdown"]
    mia.palmares_recente = {"2026-09": [30.0, 2.0]}
    # Una sfida proposta dal computer e, nello storico, una giocata con la differita e i cali.
    cpu = next(p for p in mondo.polisportive.values() if p.is_cpu_controlled)
    proposta = sfide.Sfida(mondo.sfide.nuovo_id(), iscrizioni.club_della(cpu), iscrizioni.club_della(mia), martedi.date(),
                           martedi.date() + datetime.timedelta(days=1), convocati={"sfidante": cpu.tesserati[:3]})
    mondo.sfide.attive.append(proposta)
    squadre = [Squadra(p.nome, tuple(mondo.giocatori[gid] for gid in p.tesserati[:3])) for p in (cpu, mia)]
    giocata = sfide.Sfida(mondo.sfide.nuovo_id(), iscrizioni.club_della(mia), iscrizioni.club_della(cpu), INIZIO.date(), INIZIO.date(), sfide.GIOCATA,
                          INIZIO.date(), {"sfidante": mia.tesserati[:3], "sfidata": cpu.tesserati[:3]},
                          risultato={"esito": "regolare", "vince": "sfidante", "punti": [31, 27], "titolari": [mia.tesserati[:3], cpu.tesserati[:3]], "motore": "vero"},
                          differita=differita_squadre(squadre[1], squadre[0], dict.fromkeys(mia.tesserati[:3], 1.5), {mia.tesserati[0]: 0.02}))
    mondo.sfide.archivia(giocata)
    mia.sfide_vinte, mia.ultima_sfida, mia.sfide_da_lanciare = 1, INIZIO, 3
    assert archivio.salva(mondo)
    ricaricato = Mondo()
    assert archivio.carica(ricaricato) == archivio.CARICATO
    for gid, originale in mondo.giocatori.items():
        assert vars(ricaricato.giocatori[gid]) == vars(originale)
    assert ricaricato.calendario.a_dizionario() == mondo.calendario.a_dizionario()
    assert ricaricato.sfide.a_dizionario() == mondo.sfide.a_dizionario()
    assert ricaricato.sfide.storico[0].differita["cali"][0][0] == 0.02 and ricaricato.sfide.attive[0].stato == sfide.PROPOSTA
    rilette = ricaricato.polisportive["Brybox Showdown"]
    assert rilette.palmares_recente == {"2026-09": [30.0, 2.0]} and (rilette.sfide_vinte, rilette.ultima_sfida, rilette.sfide_da_lanciare) == (1, INIZIO, 3)
    assert archivio.leggi(cartella_di_prova / FILE_MONDO)["formato"] == archivio.FORMATO


def test_un_calendario_incoerente_si_rifiuta():
    mondo = _mondo_come_quello_di_gabriele()
    apri(mondo, INIZIO, "Open maschile del martedì")
    contenuto = archivio.componi(mondo)
    contenuto["mondo"]["calendario"]["edizioni"][1]["id"] = contenuto["mondo"]["calendario"]["edizioni"][0]["id"]
    with pytest.raises(archivio.ErroreSalvataggio, match="identificativo ripetuto"):
        archivio.costruisci(contenuto, Mondo())


def test_un_registro_delle_sfide_incoerente_si_rifiuta():
    mondo = _mondo_come_quello_di_gabriele()
    mia = mondo.polisportive["Brybox Showdown"]
    cpu = next(p for p in mondo.polisportive.values() if p.is_cpu_controlled)
    mondo.sfide.attive.append(sfide.Sfida(mondo.sfide.nuovo_id(), iscrizioni.club_della(cpu), iscrizioni.club_della(mia), INIZIO.date(), INIZIO.date()))
    contenuto = archivio.componi(mondo)
    contenuto["mondo"]["sfide"]["prossimo_id"] = 1
    with pytest.raises(archivio.ErroreSalvataggio, match="identificativo ripetuto"):
        archivio.costruisci(contenuto, Mondo())
    contenuto = archivio.componi(mondo)
    contenuto["mondo"]["polisportive"]["Brybox Showdown"]["sfide_da_lanciare"] = 5
    with pytest.raises(archivio.ErroreSalvataggio, match="sfide_da_lanciare"):
        archivio.costruisci(contenuto, Mondo())


def test_un_formato_piu_recente_si_rifiuta(cartella_di_prova):
    # Dalla tappa 13 il formato è l'8: si rifiuta il 9.
    contenuto = archivio.componi(_mondo_come_quello_di_gabriele())
    contenuto["formato"] = archivio.FORMATO + 1
    percorso = cartella_di_prova / FILE_MONDO
    percorso.write_text(json.dumps({**contenuto, "firma": archivio.firma(contenuto)}), encoding="utf-8")
    with pytest.raises(archivio.ErroreSalvataggio, match=f"formato {archivio.FORMATO + 1}"):
        archivio.leggi(percorso)
