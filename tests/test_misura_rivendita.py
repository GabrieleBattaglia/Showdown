"""
Test della misura della rivendita della decisione D40, strumenti/misura_rivendita.py: il ciclo stimato dalla firma
alla vendita, la gloria tenuta al bersaglio senza le medaglie, e una misura intera su un mondo piccolo, dalla nascita
alla tabella, con la cassa che torna con le voci, la costante che torna com'era e il caso del mondo lasciato com'era.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 3 novembre 2026 con la settima tranche di D40.
"""

import contextlib
import datetime
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))

import misura_rivendita as mr
import mondi_sintetici as ms

import contratti
import economia
import palmares
from costanti import MAX_TESSERATI_POLISPORTIVA, MESI_DELLA_RAMPA

OGGI = datetime.datetime(2027, 3, 15, 9, 0)


def test_il_ciclo_stimato_aspetta_il_rinnovo_negli_ultimi_tre_mesi():
    mondo = ms.mondo_nato(11)
    g = max(mondo.giocatori.values(), key=lambda g: (contratti.durata_proposta(g), -g.id))
    durata = contratti.durata_proposta(g)
    assert durata >= 9
    def giorni(data):
        return (data - OGGI).days + 1
    # Senza mesi d'attesa il computer lo compra il giorno dopo; a 3 mesi il contratto ha ancora più di tre mesi.
    assert mr.ciclo_stimato(g, OGGI, 0) == 1
    assert mr.ciclo_stimato(g, OGGI, 3) == giorni(contratti.stesso_giorno_dopo(OGGI, 3))
    # Alla durata del contratto manca meno di un mese alla scadenza: si vende quando parte il rinnovo, col valore pieno.
    scadenza = contratti.scadenza_dopo(OGGI, durata)
    assert mr.ciclo_stimato(g, OGGI, durata) == giorni(scadenza)
    # Oltre la scadenza il contratto si rinnova per la stessa durata, e sei mesi dopo ne restano più di tre.
    assert mr.ciclo_stimato(g, OGGI, durata + 6) == giorni(contratti.stesso_giorno_dopo(OGGI, durata + 6))


def test_la_differenza_per_posto_e_per_anno_e_il_verdetto():
    def corsa(seme, strategia, mesi, saldo):
        voci = dict.fromkeys(mr.VOCI_CONTI, 0)
        voci["vendite"] = max(0, saldo)
        return {"seme": seme, "giorni": 730, "club": "gloriosa", "strategia": strategia, "mesi": mesi, "saldo": saldo, "voci": voci,
                "vendite": 1, "giorni_tenuti": 30, "firme": 1, "posti_giorno": 15, "giorni_corsi": 1, "valore_alla_fine": 0,
                "gloria_minima": 275, "gloria_massima": 275}

    risultati = [corsa(s, "tieni", None, 0) for s in (1, 2)]
    # 36 mesi e 15 posti: 45.000 euro di differenza fanno 1.000 euro per posto e per anno.
    risultati += [corsa(1, "rivendi", 6, 45_000), corsa(2, "rivendi", 6, 45_000), corsa(1, "rivendi", 12, 4_500), corsa(2, "rivendi", 12, -4_500)]
    gruppi = mr.differenze(risultati, 36)
    assert [r["differenza"] for r in gruppi[(730, "gloriosa", 6)]] == [1000.0, 1000.0]
    assert mr.riassunto(gruppi[(730, "gloriosa", 6)]) == (1000.0, 0.0)
    media, scarto = mr.riassunto(gruppi[(730, "gloriosa", 12)])
    assert media == 0.0 and round(scarto) == 141
    # A 6 mesi la differenza sta fuori dallo scarto, a 12 dentro: basta 12.
    assert mr.verdetto(gruppi) == {730: 12}
    assert mr.per_posto_e_anno(45_000, 36) == 45_000 / MAX_TESSERATI_POLISPORTIVA / 3


def test_la_misura_su_un_mondo_piccolo(tmp_path, monkeypatch):
    # Le cartelle temporanee le dà già la prova; il caso del mondo si rimette com'era alla fine.
    monkeypatch.setattr(mr, "cartelle_temporanee", contextlib.nullcontext)
    stato = random.getstate()
    try:
        cartella = tmp_path / "lavoro"
        cartella.mkdir()
        assert mr.fai_nascere(11, [365], cartella)[0] == 11 and mr.file_del_mondo(cartella, 11, 365).exists()
        partenza = mr.prepara_la_partenza(11, 365, "gloriosa", cartella, 275)
        assert partenza["tesserati"] == MAX_TESSERATI_POLISPORTIVA and partenza["gloria"] == 275 and partenza["firme"] == 15
        # La gloria tenuta: le medaglie vere non la spostano, e una rosa che da sola sta sopra il bersaglio resta alla sua.
        salvata = mr.carica(mr.file_della_partenza(cartella, 11, 365, "gloriosa"))
        mondo = salvata["mondo"]
        poli = mondo.polisportive[salvata["nome"]]
        palmares.aggiungi(poli, mondo.datetime_corrente_simulazione, punti_medaglie=400.0, punti_coppe=300.0)
        poli.aggiorna_gloria(mondo.giocatori, mondo._ids_morti_processati_sessione, mondo.datetime_corrente_simulazione)
        assert poli.gloria > 275
        mr.tieni_la_gloria(mondo, poli, 275, partenza["chiave"])
        assert poli.gloria == 275
        mr.tieni_la_gloria(mondo, poli, 20, partenza["chiave"])
        assert 20 < poli.gloria < 275 and poli.palmares_recente[partenza["chiave"]][0] < 0
        corse = [mr.corsa(11, 365, "gloriosa", "tieni", None, 1, cartella), mr.corsa(11, 365, "gloriosa", "rivendi", 0, 1, cartella),
                 mr.corsa(11, 365, "gloriosa", "rivendi", 3, 1, cartella)]
        assert economia.MESI_DELLA_RAMPA == MESI_DELLA_RAMPA
        tieni, subito, tre = corse
        assert all(r["saldo"] == r["somma_delle_voci"] and r["gloria_minima"] == r["gloria_massima"] == 275 for r in corse)
        assert tieni["vendite"] == tieni["voci"]["vendite"] == 0 and subito["vendite"] > MAX_TESSERATI_POLISPORTIVA
        assert subito["voci"]["vendite"] > subito["voci"]["ingaggi"] > 0 and subito["saldo"] > tieni["saldo"]
        # A 3 mesi, con la partenza a regime, nel primo mese si vendono i più vecchi della partenza, al più 5 su 15.
        assert 0 < tre["vendite"] <= 5
        gruppi = mr.differenze(corse, 1)
        assert set(gruppi) == {(365, "gloriosa", 0), (365, "gloriosa", 3)}
        righe = mr.tabella(gruppi, [partenza], 1)
        assert righe[0].startswith("Mondo di 365 giorni, polisportiva gloriosa, gloria 275; ")
        assert righe[1].startswith("0 mesi: differenza ") and righe[2].startswith("3 mesi: differenza ")
    finally:
        random.setstate(stato)
