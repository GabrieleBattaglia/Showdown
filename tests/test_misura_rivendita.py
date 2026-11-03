"""
Test della misura della rivendita della decisione D40, strumenti/misura_rivendita.py: il ciclo stimato dalla firma
alla vendita, il tetto atteso della rampa, la partenza a regime, il commerciante che vende alla rampa e aspetta il
rinnovo, la gloria tenuta al bersaglio senza le medaglie, la differenza, anche a rosa pari, e i mesi che rendono di
più, e una misura intera su un mondo piccolo, dalla nascita alla tabella, con la cassa che torna con le voci, il
margine che torna con la rosa pari, la rampa del gioco lasciata com'era e il caso del mondo lasciato com'era.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 3 novembre 2026 con la settima tranche di D40; lo stesso giorno passa alla misura della rampa del prezzo.
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
from costanti import FEDELTA_PER_MESE, MAX_TESSERATI_POLISPORTIVA, MESI_DELLA_RAMPA

OGGI = datetime.datetime(2027, 3, 15, 9, 0)


def bottega_e_libero(durata_minima=9):
    """Un mondo piccolo con una polisportiva dell'utente, e il libero col numero più basso che le rende, col contratto di almeno tanti mesi."""
    mondo = ms.mondo_nato(11)
    poli = mondo.fonda_polisportiva("Pat-Bologna")
    liberi = [g for g in mondo.giocatori.values() if g.appartenenza == "*" and not g.ritirato and g.puo_giocare
              and contratti.durata_proposta(g) >= durata_minima and economia.ingaggio_richiesto(g, poli) < mr.tetto(g)]
    return mondo, poli, min(liberi, key=lambda g: g.id)


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


def test_il_tetto_atteso_e_la_rampa_del_gioco():
    mondo, poli, g = bottega_e_libero()
    oggi = mondo.datetime_corrente_simulazione
    giorni = (0, 1, 45, 150)
    attesi = [mr.tetto_atteso(g, poli, oggi, n) for n in giorni]
    pieno = economia.tetto_pieno_di_rivendita(g, poli, oggi)
    # Il giorno della firma l'ingaggio chiesto, poi sale, e alla fine della rampa è il tetto pieno.
    assert attesi[0] == economia.ingaggio_richiesto(g, poli) and attesi == sorted(attesi) and attesi[0] < attesi[-1] < pieno
    rampa = (contratti.stesso_giorno_dopo(oggi, MESI_DELLA_RAMPA).date() - oggi.date()).days
    assert mr.tetto_atteso(g, poli, oggi, rampa - 1) < pieno == mr.tetto_atteso(g, poli, oggi, rampa) == mr.tetto_atteso(g, poli, oggi, rampa + 100)
    # Tesserato oggi, coi valori di oggi la rampa del gioco dice lo stesso, finché il contratto è lontano dalla scadenza.
    mondo._entra(poli, g, oggi)
    assert [economia.tetto_di_rivendita(g, poli, oggi + datetime.timedelta(days=n)) for n in giorni] == attesi


def test_la_partenza_a_regime_sposta_firma_contratto_e_fedelta():
    mondo, poli, g = bottega_e_libero(4)
    oggi = mondo.datetime_corrente_simulazione
    mondo._entra(poli, g, oggi)
    durata, fedelta = contratti.durata_proposta(g), g.fedelta
    mr.a_regime(mondo, poli, g, 400)
    firma = oggi - datetime.timedelta(days=400)
    assert g.tesserato_dal == firma
    # Il contratto della stessa durata, firmato quel giorno e rinnovato per la stessa durata finché scadrebbe prima di oggi.
    assert contratti.mesi_interi(contratti.inizio(firma), g.contratto_scadenza) % durata == 0
    assert contratti.aggiungi_mesi(g.contratto_scadenza, -durata).date() <= oggi.date() < g.contratto_scadenza.date()
    # La fedeltà dei primi del mese passati, con lo staff che non la sposta.
    assert mondo.fattori_staff(poli)[2] == 1.0
    assert g.fedelta == fedelta + FEDELTA_PER_MESE * contratti.mesi_interi(firma, oggi) > fedelta
    # Lontano dalla scadenza, il tetto di oggi è quello della rampa a 400 giorni dalla firma.
    assert contratti.mesi_al_termine(g, oggi) >= 3
    assert economia.tetto_di_rivendita(g, poli, oggi) == mr.tetto_atteso(g, poli, firma, 400)


def test_il_commerciante_vende_alla_rampa_e_aspetta_il_rinnovo():
    mondo, poli, g = bottega_e_libero()
    oggi = mondo.datetime_corrente_simulazione
    mondo._entra(poli, g, oggi)
    # Prima dei tre mesi di firma non è in vendita.
    mr.metti_in_vendita_alla_rampa(mondo, poli, 3)
    assert g.id not in poli.in_vendita
    mr.a_regime(mondo, poli, g, 100)
    assert mr.in_vendita_dal(g, 3) <= oggi.date()
    mr.metti_in_vendita_alla_rampa(mondo, poli, 3)
    prezzo = poli.in_vendita[g.id]
    assert prezzo == economia.tetto_di_rivendita(g, poli, oggi) and economia.ingaggio_richiesto(g, poli) < prezzo < economia.tetto_pieno_di_rivendita(g, poli, oggi)
    # Negli ultimi tre mesi di contratto, con un rinnovo concordato, il commerciante aspetta che il rinnovo parta.
    g.contratto_scadenza = contratti.aggiungi_mesi(oggi, 1)
    contratti.concorda_rinnovo(g, g.contratto_stipendio, 12)
    assert mr.aspetta_il_rinnovo(g, oggi)
    mr.metti_in_vendita_alla_rampa(mondo, poli, 3)
    assert g.id not in poli.in_vendita
    # Senza rinnovo resta in vendita, al tetto che scende con la scadenza.
    g.rinnovo_stipendio, g.rinnovo_scadenza = 0, None
    mr.metti_in_vendita_alla_rampa(mondo, poli, 3)
    assert poli.in_vendita[g.id] == economia.tetto_di_rivendita(g, poli, oggi) < prezzo


def test_la_differenza_per_posto_e_per_anno_e_i_mesi_piu_redditizi():
    def corsa(seme, strategia, mesi, saldo, rosa_finale=9_000):
        voci = dict.fromkeys(mr.VOCI_CONTI, 0)
        voci["vendite"] = max(0, saldo)
        voci["sponsor"] = 36 * 4_000
        return {"seme": seme, "giorni": 730, "club": "gloriosa", "strategia": strategia, "mesi": mesi, "saldo": saldo, "voci": voci,
                "vendite": 1, "giorni_tenuti": 30, "firme": 1, "posti_giorno": 15, "giorni_corsi": 1, "valore_alla_fine": 0,
                "margini": 0, "sotto_l_ingaggio": 0, "ingaggi_rosa_iniziale": 9_000, "ingaggi_rosa_finale": rosa_finale,
                "gloria_minima": 275, "gloria_massima": 275}

    risultati = [corsa(s, "tieni", None, 0) for s in (1, 2)]
    # 36 mesi e 15 posti: 45.000 euro di differenza fanno 1.000 euro per posto e per anno.
    risultati += [corsa(1, "rivendi", 6, 45_000), corsa(2, "rivendi", 6, 45_000), corsa(1, "rivendi", 12, 4_500), corsa(2, "rivendi", 12, -4_500)]
    # A 0 mesi la rosa si svuota: i 9.000 euro d'ingaggio della partenza diventano cassa, e a rosa pari tornano indietro.
    risultati += [corsa(1, "rivendi", 0, 50_000, 0), corsa(2, "rivendi", 0, 50_000, 0)]
    gruppi = mr.differenze(risultati, 36)
    assert [r["differenza"] for r in gruppi[(730, "gloriosa", 6)]] == [1000.0, 1000.0]
    assert mr.riassunto(gruppi[(730, "gloriosa", 6)]) == mr.riassunto(gruppi[(730, "gloriosa", 6)], "a_rosa_pari") == (1000.0, 0.0)
    media, scarto = mr.riassunto(gruppi[(730, "gloriosa", 12)])
    assert media == 0.0 and round(scarto) == 141
    assert [round(x) for x in mr.riassunto(gruppi[(730, "gloriosa", 0)])] == [1111, 0]
    assert [round(x) for x in mr.riassunto(gruppi[(730, "gloriosa", 0)], "a_rosa_pari")] == [911, 0]
    assert mr.per_posto_e_anno(45_000, 36) == 45_000 / MAX_TESSERATI_POLISPORTIVA / 3
    # Rende di più la vendita a 0 mesi, ma a rosa pari quella a 6.
    assert {chiave: mesi for chiave, (mesi, _m, _s) in mr.piu_redditizio(gruppi).items()} == {(730, "gloriosa"): 0}
    assert {chiave: mesi for chiave, (mesi, _m, _s) in mr.piu_redditizio(gruppi, "a_rosa_pari").items()} == {(730, "gloriosa"): 6}
    assert mr.residuo(gruppi) == ["Mondo di 730 giorni, polisportiva gloriosa: rende di più la vendita a 0 mesi dalla firma, 1.111 euro per posto e per "
                                  "anno, scarto fra i semi 0; con la rosa intera 16.667 euro all'anno, 1.389 al mese, il 35% dello sponsor della rosa "
                                  "onesta, 4.000 euro al mese."]
    assert mr.residuo(gruppi, "a_rosa_pari") == ["Mondo di 730 giorni, polisportiva gloriosa a rosa pari: rende di più la vendita a 6 mesi dalla firma, "
                                                 "1.000 euro per posto e per anno, scarto fra i semi 0; con la rosa intera 15.000 euro all'anno, 1.250 al "
                                                 "mese, il 31% dello sponsor della rosa onesta, 4.000 euro al mese."]


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
        # A 0 mesi il computer paga l'ingaggio, e qualche euro della rampa se compra qualche giorno dopo.
        assert 0 <= subito["margini"] < 10 * subito["vendite"] and subito["sotto_l_ingaggio"] == 0
        # Senza uscite, il saldo a rosa pari è il margine delle vendite più le voci che non sono vendite e ingaggi.
        for r in corse:
            if r["usciti"] == 0:
                assert mr.a_rosa_pari(r) - r["margini"] == r["saldo"] - r["voci"]["vendite"] + r["voci"]["ingaggi"]
        # A 3 mesi, con la partenza a regime, nel primo mese si vendono i più vecchi della partenza, al più 5 su 15, con più
        # di tre mesi di firma.
        assert 0 < tre["vendite"] <= 5 and tre["giorni_tenuti"] >= 89 * tre["vendite"] and tre["margini"] > 0
        gruppi = mr.differenze(corse, 1)
        assert set(gruppi) == {(365, "gloriosa", 0), (365, "gloriosa", 3)}
        righe = mr.tabella(gruppi, [partenza], 1)
        assert righe[0].startswith("Mondo di 365 giorni, polisportiva gloriosa, gloria 275; ")
        assert righe[1].startswith("Vendita a 0 mesi dalla firma: differenza ") and righe[2].startswith("Vendita a 3 mesi dalla firma: differenza ")
        assert all(" a rosa pari " in riga and " margine medio sull'ingaggio " in riga for riga in righe[1:])
        assert mr.residuo(gruppi)[0].startswith("Mondo di 365 giorni, polisportiva gloriosa: rende di più la vendita a ")
    finally:
        random.setstate(stato)
