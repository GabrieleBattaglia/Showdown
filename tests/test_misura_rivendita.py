"""
Test della misura della rivendita della decisione D40, strumenti/misura_rivendita.py: il ciclo stimato dalla firma
alla vendita, il tetto atteso della rampa, la partenza a regime, il commerciante che vende alla rampa e aspetta il
rinnovo, la gloria tenuta al bersaglio senza le medaglie, la differenza, anche a rosa pari, e i mesi che rendono di
più, e una misura intera su un mondo piccolo, dalla nascita alla tabella, con la cassa che torna con le voci, il
margine che torna con la rosa pari, la rampa del gioco lasciata com'era e il caso del mondo lasciato com'era.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 3 novembre 2026 con la settima tranche di D40; lo stesso giorno passa alla misura della rampa del prezzo, e
prova anche la rampa di un'altra durata, --mesi-della-rampa, nei processi figli e nel principale.
Lo stesso giorno prova anche la rampa che parte dall'ingaggio della firma, --partenza-della-rampa firma: in un vero
processo figlio il tetto di un tesserato il cui ingaggio chiesto è cresciuto dopo la firma parte da quello pagato, e
con la partenza di serie, vendita, da quello di oggi; nel principale la rampa sostituita è la regola del gioco con
un'altra partenza, anche per il computer che compra, e la misura sul mondo piccolo dice la partenza che ha visto.
Dalle scelte di Gabriele dello stesso giorno, che valgono come D40, la partenza dalla firma è la regola del gioco, col
campo pagato_alla_firma, e la partenza di serie dello strumento; vendita è la variante, la regola di prima, per
confronto. Le prove cambiano di conseguenza, e ne arriva una che mancava: nella misura sul mondo piccolo i quindici della
partenza non hanno quello pagato finché la corsa non lo scrive, e la vendita a 0 mesi vende anche chi firma nella corsa,
così una rampa che non trova quello pagato, dei quindici o di chi firma, fa fallire la prova.
"""

import contextlib
import datetime
import random
import sys
from pathlib import Path

import pytest

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


def firma_pagando(mondo, poli, g, oggi):
    """Il libero firma oggi pagando l'ingaggio che chiede, come fa il commerciante: il gioco lo ricorda in pagato_alla_firma."""
    mondo._entra(poli, g, oggi, economia.ingaggio_richiesto(g, poli))
    assert g.pagato_alla_firma == economia.ingaggio_richiesto(g, poli)


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
    # Tesserato oggi all'ingaggio che chiede, coi valori di oggi la rampa del gioco dice lo stesso, finché il contratto è
    # lontano dalla scadenza: parte da quello pagato, che il giorno della firma è l'ingaggio chiesto.
    firma_pagando(mondo, poli, g, oggi)
    assert [economia.tetto_di_rivendita(g, poli, oggi + datetime.timedelta(days=n)) for n in giorni] == attesi


def test_la_rampa_di_un_altra_durata_vale_nei_figli_e_nei_conti(monkeypatch):
    # Di serie la rampa del gioco; --mesi-della-rampa la cambia, e meno di zero mesi è un errore.
    assert mr.argomenti([]).mesi_della_rampa == MESI_DELLA_RAMPA == 36
    assert mr.argomenti(["--mesi-della-rampa", "42"]).mesi_della_rampa == 42
    with pytest.raises(SystemExit):
        mr.argomenti(["--mesi-della-rampa", "-1"])
    mondo, poli, g = bottega_e_libero()
    oggi = mondo.datetime_corrente_simulazione
    pieno = economia.tetto_pieno_di_rivendita(g, poli, oggi)
    def fine(mesi):
        return (contratti.stesso_giorno_dopo(oggi, mesi).date() - oggi.date()).days
    giorni = (0, 45, 150, fine(MESI_DELLA_RAMPA), fine(42) - 1, fine(42))
    del_gioco = [mr.tetto_atteso(g, poli, oggi, n) for n in giorni]
    assert del_gioco[3] == pieno
    # Nel processo figlio dello strumento, con l'inizializzatore, la rampa dura 42 mesi: sale più piano, e il tetto pieno
    # arriva soltanto a 42 mesi dalla firma. Il processo della prova resta alla rampa del gioco.
    with mr.esecutore(1, 42) as figli:
        nei_figli = list(figli.map(mr.tetto_atteso, [g] * len(giorni), [poli] * len(giorni), [oggi] * len(giorni), giorni))
    assert economia.MESI_DELLA_RAMPA == MESI_DELLA_RAMPA
    assert nei_figli[0] == del_gioco[0] == economia.ingaggio_richiesto(g, poli)
    assert all(lenta < veloce for lenta, veloce in zip(nei_figli[1:4], del_gioco[1:4], strict=True))
    assert nei_figli == sorted(nei_figli) and nei_figli[4] < pieno == nei_figli[5]
    # Nel processo principale imposta_la_rampa fa lo stesso, e il tetto del gioco, che il computer usa per comprare,
    # segue la rampa dello strumento finché il contratto è lontano dalla scadenza.
    monkeypatch.setattr(economia, "MESI_DELLA_RAMPA", economia.MESI_DELLA_RAMPA)
    monkeypatch.setattr(economia, "_rampa", economia._rampa)
    mr.imposta_la_rampa(42)
    assert [mr.tetto_atteso(g, poli, oggi, n) for n in giorni] == nei_figli
    firma_pagando(mondo, poli, g, oggi)
    assert [economia.tetto_di_rivendita(g, poli, oggi + datetime.timedelta(days=n)) for n in giorni[:3]] == nei_figli[:3]


def tesserato_cresciuto():
    """
    Il libero di bottega_e_libero tesserato oggi, pagando l'ingaggio che chiede, che il gioco ricorda; poi in rosa
    l'esperienza cresce, e con lei l'ingaggio che chiede, che resta sotto il tetto pieno. Restituisce anche l'ingaggio
    pagato, quello di oggi e i giorni della rampa del gioco.
    """
    mondo, poli, g = bottega_e_libero()
    oggi = mondo.datetime_corrente_simulazione
    firma_pagando(mondo, poli, g, oggi)
    pagato = g.pagato_alla_firma
    g.esperienza += 10
    cresciuto = economia.ingaggio_richiesto(g, poli)
    assert pagato < cresciuto < economia.tetto_pieno_di_rivendita(g, poli, oggi)
    giorni = (contratti.stesso_giorno_dopo(oggi, MESI_DELLA_RAMPA).date() - oggi.date()).days
    return mondo, poli, g, pagato, cresciuto, giorni


def test_la_partenza_della_rampa_vale_nei_figli():
    # Di serie la partenza è firma, quella del gioco; vendita è la variante di prima, e un'altra parola è un errore.
    assert mr.argomenti([]).partenza_della_rampa == "firma"
    assert mr.argomenti(["--partenza-della-rampa", "vendita"]).partenza_della_rampa == "vendita"
    with pytest.raises(SystemExit):
        mr.argomenti(["--partenza-della-rampa", "oggi"])
    mondo, poli, g, pagato, cresciuto, giorni = tesserato_cresciuto()
    oggi = mondo.datetime_corrente_simulazione
    date = [oggi + datetime.timedelta(days=n) for n in (0, 45, 150)]
    pieni = [economia.tetto_pieno_di_rivendita(g, poli, d) for d in date]
    def rampa(partenza):
        return [partenza + (pieno - partenza) * (d - oggi).days // giorni for d, pieno in zip(date, pieni, strict=True)]
    # Nel processo della prova la rampa del gioco parte da quello pagato alla firma, non dall'ingaggio cresciuto in rosa.
    assert mr.partenza_vista() == "firma"
    assert [economia.tetto_di_rivendita(g, poli, d) for d in date] == rampa(pagato)
    # In un vero processo figlio, con la variante vendita, la rampa parte dall'ingaggio di oggi, e il tetto sta sopra.
    with mr.esecutore(1, MESI_DELLA_RAMPA, "vendita") as figli:
        vista = figli.submit(mr.partenza_vista).result()
        dalla_vendita = list(figli.map(economia.tetto_di_rivendita, [g] * len(date), [poli] * len(date), date))
    assert vista == "vendita" and dalla_vendita == rampa(cresciuto)
    assert all(firma < vendita for firma, vendita in zip(rampa(pagato), dalla_vendita, strict=True))
    # Con la partenza di serie il figlio fa come il gioco, e il processo della prova non è cambiato.
    with mr.esecutore(1, MESI_DELLA_RAMPA) as figli:
        vista = figli.submit(mr.partenza_vista).result()
        dalla_firma = list(figli.map(economia.tetto_di_rivendita, [g] * len(date), [poli] * len(date), date))
    assert vista == "firma" and dalla_firma == rampa(pagato)
    assert mr.partenza_vista() == "firma" and economia._rampa is mr.RAMPA_DEL_GIOCO


def test_la_variante_vendita_e_la_regola_di_prima(monkeypatch):
    monkeypatch.setattr(economia, "_rampa", economia._rampa)
    monkeypatch.setattr(mr, "SENZA_FIRMA", {"volte": 0})
    mondo, poli, g, pagato, cresciuto, giorni = tesserato_cresciuto()
    oggi = mondo.datetime_corrente_simulazione
    date = [oggi + datetime.timedelta(days=n) for n in (0, 1, 45, 150)]
    def rampa(partenza):
        return [partenza + (economia.tetto_pieno_di_rivendita(g, poli, d) - partenza) * (d - oggi).days // giorni for d in date]
    del_gioco = [economia.tetto_di_rivendita(g, poli, d) for d in date]
    assert del_gioco == rampa(pagato)
    # La partenza di serie è la rampa del gioco: imposta_la_rampa l'avvolge soltanto per contare i ripieghi.
    mr.imposta_la_rampa(MESI_DELLA_RAMPA)
    assert mr.partenza_vista() == "firma" and economia._rampa is mr.rampa_del_gioco
    assert [economia.tetto_di_rivendita(g, poli, d) for d in date] == del_gioco and mr.SENZA_FIRMA["volte"] == 0
    # Senza quello pagato la rampa del gioco ripiega sull'ingaggio di oggi, e ogni volta si conta.
    g.pagato_alla_firma = None
    assert [economia.tetto_di_rivendita(g, poli, d) for d in date] == rampa(cresciuto) and mr.SENZA_FIRMA["volte"] == len(date)
    g.pagato_alla_firma = pagato
    # La variante vendita, la regola di prima: parte dall'ingaggio chiesto oggi, cresciuto in rosa, anche per il computer che
    # compra, Mondo._vendibili, e non conta ripieghi.
    mr.SENZA_FIRMA["volte"] = 0
    mr.imposta_la_rampa(MESI_DELLA_RAMPA, "vendita")
    assert mr.partenza_vista() == "vendita"
    assert [economia.tetto_di_rivendita(g, poli, d) for d in date] == rampa(cresciuto)
    assert economia.rivendita_piena_dal(g, poli, oggi) == contratti.stesso_giorno_dopo(oggi, MESI_DELLA_RAMPA)
    mondo.metti_in_vendita(poli, g, pagato)
    righe = [riga for riga in mondo._vendibili(date[2]) if riga[0] is g]
    assert [riga[3] for riga in righe] == [rampa(cresciuto)[2]] and mr.SENZA_FIRMA["volte"] == 0
    # Una partenza che non sta sotto il tetto pieno vale il tetto pieno, come nel gioco.
    pieno = economia.tetto_pieno_di_rivendita(g, poli, date[2])
    monkeypatch.setattr(economia, "ingaggio_richiesto", lambda _g, _p: pieno)
    assert economia.tetto_di_rivendita(g, poli, date[2]) == pieno and economia.rivendita_piena_dal(g, poli, date[2]) is None
    # La partenza di serie rimette la rampa del gioco.
    mr.imposta_la_rampa(MESI_DELLA_RAMPA)
    assert economia._rampa is mr.rampa_del_gioco and mr.partenza_vista() == "firma"


def test_quello_pagato_di_chi_firma_nella_corsa_viene_dal_gioco(tmp_path, monkeypatch):
    monkeypatch.setattr(mr, "SENZA_FIRMA", {"volte": 0})
    mondo, poli, g = bottega_e_libero()
    oggi = mondo.datetime_corrente_simulazione
    # Chi firma nella corsa ha quello pagato dal gioco, e il margine conta quello.
    mondo._entra(poli, g, oggi, 123)
    assert mr.pagato_alla_firma(g, poli) == 123 and mr.SENZA_FIRMA["volte"] == 0
    # Senza, l'ingaggio che chiede oggi, e la volta si conta.
    g.pagato_alla_firma = None
    assert mr.pagato_alla_firma(g, poli) == economia.ingaggio_richiesto(g, poli) and mr.SENZA_FIRMA["volte"] == 1
    # Un mondo nato col codice di prima del formato 12 non ha il campo: al caricamento lo riceve vuoto, nel mondo nato e
    # nella partenza.
    for gid in list(mondo.giocatori)[:5]:
        del vars(mondo.giocatori[gid])["pagato_alla_firma"]
    for nome, oggetto in (("mondo.pickle", mondo), ("partenza.pickle", {"mondo": mondo, "nome": poli.nome, "dati": {}})):
        mr.salva(oggetto, tmp_path / nome)
        letto = mr.carica(tmp_path / nome)
        giocatori = (letto["mondo"] if isinstance(letto, dict) else letto).giocatori
        assert all(vars(x).get("pagato_alla_firma", "manca") is None for x in list(giocatori.values())[:5])


def test_la_partenza_a_regime_sposta_firma_contratto_e_fedelta():
    mondo, poli, g = bottega_e_libero(4)
    oggi = mondo.datetime_corrente_simulazione
    firma_pagando(mondo, poli, g, oggi)
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
    # All'inizio della corsa quello pagato è l'ingaggio chiesto quel giorno, scritto nel campo del gioco.
    assert mr.ricorda_la_firma(g, poli) == g.pagato_alla_firma == economia.ingaggio_richiesto(g, poli)
    # Lontano dalla scadenza, il tetto di oggi è quello della rampa a 400 giorni dalla firma.
    assert contratti.mesi_al_termine(g, oggi) >= 3
    assert economia.tetto_di_rivendita(g, poli, oggi) == mr.tetto_atteso(g, poli, firma, 400)


def test_il_commerciante_vende_alla_rampa_e_aspetta_il_rinnovo():
    mondo, poli, g = bottega_e_libero()
    oggi = mondo.datetime_corrente_simulazione
    firma_pagando(mondo, poli, g, oggi)
    # Prima dei tre mesi di firma non è in vendita.
    mr.metti_in_vendita_alla_rampa(mondo, poli, 3)
    assert g.id not in poli.in_vendita
    mr.a_regime(mondo, poli, g, 100)
    assert mr.in_vendita_dal(g, 3) <= oggi.date()
    mr.metti_in_vendita_alla_rampa(mondo, poli, 3)
    prezzo = poli.in_vendita[g.id]
    assert prezzo == economia.tetto_di_rivendita(g, poli, oggi) and g.pagato_alla_firma < prezzo < economia.tetto_pieno_di_rivendita(g, poli, oggi)
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
    # Le cartelle temporanee le dà già la prova; il caso del mondo e la rampa si rimettono come erano alla fine. La rampa del
    # processo è quella che main imposta di serie, la rampa del gioco che conta i ripieghi.
    monkeypatch.setattr(mr, "cartelle_temporanee", contextlib.nullcontext)
    monkeypatch.setattr(economia, "_rampa", economia._rampa)
    monkeypatch.setattr(economia, "MESI_DELLA_RAMPA", economia.MESI_DELLA_RAMPA)
    mr.imposta_la_rampa(MESI_DELLA_RAMPA)
    stato = random.getstate()
    try:
        cartella = tmp_path / "lavoro"
        cartella.mkdir()
        assert mr.fai_nascere(11, [365], cartella)[0] == 11 and mr.file_del_mondo(cartella, 11, 365).exists()
        partenza = mr.prepara_la_partenza(11, 365, "gloriosa", cartella, 275)
        assert partenza["tesserati"] == MAX_TESSERATI_POLISPORTIVA and partenza["gloria"] == 275 and partenza["firme"] == 15
        # I quindici hanno firmato pagando, e il gioco lo ricorda. La prova che mancava: la corsa li conta come già pagati e
        # scrive lei quello pagato, all'inizio; qui lo si toglie, come per chi fosse entrato senza pagare, e la rampa della
        # vendita a 0 mesi, che li vende nei primi giorni, non deve mai ripiegare sull'ingaggio di oggi.
        percorso = mr.file_della_partenza(cartella, 11, 365, "gloriosa")
        da_svuotare = mr.carica(percorso)
        quindici = [da_svuotare["mondo"].giocatori[gid] for gid in da_svuotare["mondo"].polisportive[da_svuotare["nome"]].tesserati]
        assert len(quindici) == 15 and all(g.pagato_alla_firma is not None for g in quindici)
        for g in quindici:
            g.pagato_alla_firma = None
        mr.salva(da_svuotare, percorso)
        # La gloria tenuta: le medaglie vere non la spostano, e una rosa che da sola sta sopra il bersaglio resta alla sua.
        salvata = mr.carica(percorso)
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
        assert economia.MESI_DELLA_RAMPA == MESI_DELLA_RAMPA and all(r["mesi_della_rampa"] == MESI_DELLA_RAMPA for r in corse)
        # La partenza di serie è firma, la regola del gioco; la rampa trova sempre quello pagato, dei quindici e di chi firma
        # nella corsa, e gli ingaggi della firma sono quelli pagati.
        assert all(r["partenza_della_rampa"] == "firma" and r["rampe_senza_firma"] == 0 for r in corse)
        assert all(r["ingaggi_alla_firma"] == r["voci"]["ingaggi"] for r in corse)
        tieni, subito, tre = corse
        assert all(r["saldo"] == r["somma_delle_voci"] and r["gloria_minima"] == r["gloria_massima"] == 275 for r in corse)
        # A 0 mesi il computer compra pochi giorni dopo la firma, anche chi firma nella corsa: il margine pieno resta quasi
        # tutto, e il computer paga quello che è costato e qualche euro della rampa, mai meno.
        assert tieni["vendite"] == tieni["voci"]["vendite"] == 0 and subito["vendite"] > MAX_TESSERATI_POLISPORTIVA and subito["firme"] > 0
        assert subito["margini_pieni"] > 10 * subito["margini"] and 0 <= subito["margini"] < 10 * subito["vendite"] and subito["sotto_l_ingaggio"] == 0
        # Senza uscite, il saldo a rosa pari è il margine delle vendite più le voci che non sono vendite e ingaggi.
        for r in corse:
            if r["usciti"] == 0:
                assert mr.a_rosa_pari(r) - r["margini"] == r["saldo"] - r["voci"]["vendite"] + r["voci"]["ingaggi"]
        # A 3 mesi, con la partenza a regime, nel primo mese si vendono i più vecchi della partenza, al più 5 su 15, con più
        # di tre mesi di firma.
        assert 0 < tre["vendite"] <= 5 and tre["giorni_tenuti"] >= 89 * tre["vendite"] and tre["margini"] > 0
        # Con la variante vendita la stessa corsa a 0 mesi lo dice nel risultato, e l'ingaggio cresciuto in quei giorni
        # diventa margine.
        mr.imposta_la_rampa(MESI_DELLA_RAMPA, "vendita")
        dalla_vendita = mr.corsa(11, 365, "gloriosa", "rivendi", 0, 1, cartella)
        assert dalla_vendita["partenza_della_rampa"] == "vendita" and dalla_vendita["rampe_senza_firma"] == 0 and dalla_vendita["vendite"] > 0
        assert dalla_vendita["saldo"] == dalla_vendita["somma_delle_voci"] and dalla_vendita["ingaggi_alla_firma"] == dalla_vendita["voci"]["ingaggi"]
        assert 0 <= dalla_vendita["crescita_degli_ingaggi"] <= dalla_vendita["margini"]
        mr.imposta_la_rampa(MESI_DELLA_RAMPA)
        gruppi = mr.differenze(corse, 1)
        assert set(gruppi) == {(365, "gloriosa", 0), (365, "gloriosa", 3)}
        righe = mr.tabella(gruppi, [partenza], 1)
        assert righe[0].startswith("Mondo di 365 giorni, polisportiva gloriosa, gloria 275; ")
        assert righe[1].startswith("Vendita a 0 mesi dalla firma: differenza ") and righe[2].startswith("Vendita a 3 mesi dalla firma: differenza ")
        assert all(" a rosa pari " in riga and " margine medio sull'ingaggio " in riga for riga in righe[1:])
        assert mr.residuo(gruppi)[0].startswith("Mondo di 365 giorni, polisportiva gloriosa: rende di più la vendita a ")
    finally:
        random.setstate(stato)
