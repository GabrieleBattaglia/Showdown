"""
Le prove delle regole fra più polisportive dell'utente, decisione D40 del 2 novembre 2026. La prima tranche, le regole che
non chiedono campi nuovi nel salvataggio: fra le tue polisportive i giocatori non si vendono, e al computer sì; la riserva;
lo svincolo e la vendita che saldano gli arretrati, col computer che non compra quando i soldi non bastano; la chiusura che
salda tutto, con le altre tue polisportive oltre la loro riserva, dalla più ricca, e che non si fa quando non basta, dicendo
chi la blocca; i convocati delle sfide accettate e le rose della Coppa, fermi sul mercato fino alla partita, che escono
dalla vendita, e la rosa che non entra in due polisportive della stessa coppa. Il computer resta com'era.
La seconda tranche, lo sponsor delle tue polisportive, che paga la gloria per i tesserati in attività su 15: la stessa
cifra nei conti del mese, nella barra, nella scheda, nel bilancio e nei contratti, e le frasi della rosa non piena.
La quarta tranche, le fondazioni: le prime due col capitale, dalla terza aperta a pagamento, pagate dalla polisportiva attiva
oltre la sua riserva, il capitale dopo le chiusure e per chi riparte da zero, e il ripensamento, che vale soltanto per una
polisportiva di pochi giorni, vuota e con la cassa ancora piena.
La quinta tranche: Sposta fondi, che passa i soldi fra le tue polisportive senza mosse e senza limiti di tempo ma non sotto
la riserva di chi paga, con le frasi del limite, le voci dei conti e i diari; e l'allenatore licenziato da una tua
polisportiva, che per 30 giorni non firma con le tue, mentre il computer lo assume subito e lo staff di una chiusura non è
licenziato.
La sesta tranche: il computer non compra un tuo tesserato firmato da meno di dodici mesi, e lo compra dal giorno esatto;
chi ha firmato prima del formato 11 si compra come prima, e fra le polisportive del computer niente cambia. Il valore di una
tua vendita non conta il rinnovo concordato; le Vendite, la riga del mercato e la scheda dicono da quando il computer
comprerà. Le prove delle tranche di prima in cui il computer compra un tuo tesserato spostano la firma un anno indietro.
Con la rampa del prezzo scelta da Gabriele il 3 novembre 2026, al posto dei dodici mesi: il tetto del computer parte
dall'ingaggio il giorno della firma e sale giorno per giorno fino al valore pieno col rialzo, dove arriva dopo
MESI_DELLA_RAMPA mesi; vale subito pieno per chi ha firmato prima del formato 11 e quando la partenza non sta sotto il
pieno; il computer compra al tetto del giorno e non sopra. Le Vendite partono dal tetto e lo dicono, la riga del mercato e
la scheda lo dicono durante la rampa, e l'esito di un prezzo sopra il tetto dice da quando il computer lo comprerà, o che
non lo comprerà. Le prove delle tranche di prima spostano la firma alla fine della rampa.
Con un'altra scelta di Gabriele del 3 novembre 2026, la password che protegge anche la cassa: Sposta fondi vuole quella della
polisportiva che paga, se è protetta e non è l'attiva, e senza quella giusta non sposta niente; la chiusura chiede quella di
ogni sorella protetta che il piano fa pagare, dalla più ricca, e chi resta fuori non paga: il piano si rifà senza di lei, e se
non basta più la chiusura si blocca con la frase che la nomina.
Con le correzioni della revisione dei rimedi di D40: la rosa della Coppa e la sfida accettata di una polisportiva chiusa non
fermano più nessuno, né la sorella che firma chi è tornato libero né un club nuovo con lo stesso nome (A7); lo svincolo che
si ferma per gli arretrati (T6); le date dell'allenatore licenziato e della prelazione, che dicono soltanto dal e si elidono
(T3 e T8); le frasi dei convocati, dello svincolo, della vendita, di Sposta fondi e della chiusura (T3); e il ripensamento,
che guarda lo stato di oggi e la domanda lo dice (T4).
Con le scelte di Gabriele del 3 novembre 2026 che valgono come D40, dopo la misura della rivendita a 36 mesi: la rampa dura
36 mesi e parte da quello che la polisportiva ha pagato alla firma, pagato_alla_firma. Il libero pagato sotto o sopra
l'ingaggio che chiedeva parte da quello pagato, che non cambia con la gloria; l'acquisto dal computer parte dal prezzo, e
sopra il tetto pieno non ha rampa; l'offerta d'acquisto accettata parte dall'offerta; la vendita al computer ricorda il
prezzo, e il computer resta senza rampa; chi esce lo dimentica; e senza quello pagato, come chi ha firmato nel formato 11
prima del cambio, la rampa parte dall'ingaggio chiesto oggi.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import datetime

import pytest
from aiuti_calendario import OGGI, apri, giorno, mondo_di_prova, polisportiva, solo

import barra
import contratti
import economia
import iscrizioni
import mercato
import mondo as modulo_mondo
import sfide
import testi
from costanti import CAPITALE_INIZIALE, FEDELTA_BANDIERA, MESI_DELLA_RAMPA, QUOTA_SPONSOR_SUL_VALORE, RIALZO_CPU, SPONSOR_PER_GLORIA
from mondo import VENDITA_FRA_TUE, Mondo, _Mercato, fondi_senza_password, prezzo_della_fondazione
from utilita import adesso_utc

DOMANI = OGGI + datetime.timedelta(days=1)


def _euro(importo):
    return economia.scritta_in_euro(importo)


def _nome(g):
    return f"{g.nome} {g.cognome}"


def _mondo():
    """
    Un mondo con una polisportiva del computer, PoliTeam01 Prova, coi giocatori da 1 a 4, 21 e 22, e due tue, Pat-Bologna,
    da 9 a 11 e da 25 a 27, e Pat-Milano, 12, 13 e 28. Uomini da 1 a 20, donne da 21 a 40.
    """
    mondo = mondo_di_prova(20, 20)
    cpu = polisportiva(mondo, "PoliTeam01 Prova", ids=(1, 2, 3, 4, 21, 22))
    bologna = polisportiva(mondo, "Pat-Bologna", cpu=False, cassa=20_000, ids=(9, 10, 11, 25, 26, 27))
    milano = polisportiva(mondo, "Pat-Milano", cpu=False, cassa=8_000, ids=(12, 13, 28))
    mondo.miapolisportiva_attiva = bologna
    return mondo, cpu, bologna, milano


def _firmati_a_rampa_finita(*giocatori):
    """
    La firma dei giocatori MESI_DELLA_RAMPA mesi prima di OGGI: dalla rampa del prezzo di D40 il computer paga il valore pieno
    di un tuo tesserato soltanto da quel giorno, e prima al più il tetto della rampa.
    """
    for g in giocatori:
        g.tesserato_dal = contratti.stesso_giorno_dopo(OGGI, -MESI_DELLA_RAMPA)


@pytest.fixture
def larga(monkeypatch):
    """Ogni polisportiva accetta qualunque rapporto di forza, e il computer non lancia sfide da sé."""
    monkeypatch.setattr(sfide, "PROB_LANCIO_SFIDA_CPU", 0)
    monkeypatch.setattr(sfide, "forbice", lambda _nome: (0.0, 99.0))


# Fra le tue polisportive non si vende.

def test_fra_le_tue_polisportive_i_giocatori_non_si_vendono():
    mondo, cpu, bologna, milano = _mondo()
    g = mondo.giocatori[12]
    mondo.metti_in_vendita(milano, g, 100)
    assert mondo.problema_acquisto(bologna, g) == VENDITA_FRA_TUE == "Fra le tue polisportive i giocatori non si vendono."
    with pytest.raises(ValueError, match="Fra le tue polisportive i giocatori non si vendono"):
        mondo.acquista(bologna, g)
    assert g.appartenenza == milano.nome and bologna.movimenti_oggi == 0 and bologna.cassa == 20_000
    # Il mercato lo dice, anche con la cassa vuota, e la domanda d'acquisto non parte.
    riga = next(r for r in mercato.Memoria(mondo).righe_di(mercato.GIOCATORI) if r.persona.id == 12)
    bologna.cassa = 0
    assert mercato.offerta_possibile(mondo, bologna, riga) == (None, VENDITA_FRA_TUE, mercato.VENDITA_FRA_TUE) and riga.costo is None
    # Al computer la vendita resta com'era, a rampa finita.
    _firmati_a_rampa_finita(g)
    prezzo = max(1, economia.valore_di_mercato(g, OGGI))
    mondo.metti_in_vendita(milano, g, prezzo)
    cpu.cassa = 1_000_000
    assert mondo._compra_dal_mercato(cpu, OGGI)
    assert g.appartenenza == cpu.nome and milano.cassa == 8_000 + prezzo


# La riserva.

def test_la_riserva_e_quello_che_si_deve_al_primo_del_mese():
    mondo, _cpu, bologna, milano = _mondo()
    rosa = [mondo.giocatori[gid] for gid in bologna.tesserati]
    rosa[0].arretrati = 700
    a = mondo._nasce_un_allenatore(OGGI)
    mondo.assumi_allenatore(bologna, a, 0, OGGI)
    attesa = sum(economia.stipendio_pagato(g) for g in rosa) + 700 + a.contratto_stipendio
    assert mondo.riserva(bologna) == attesa == mondo.monte_stipendi(bologna) + 700
    assert mondo.riserva(milano) == sum(economia.stipendio_pagato(mondo.giocatori[gid]) for gid in milano.tesserati)
    # Chi è uscito di scena non si paga più.
    mondo._ids_morti_processati_sessione.add(rosa[0].id)
    assert mondo.riserva(bologna) == attesa - economia.stipendio_pagato(rosa[0]) - 700


# Lo svincolo e la vendita saldano gli arretrati.

def test_lo_svincolo_salda_anche_gli_arretrati():
    mondo, cpu, bologna, _milano = _mondo()
    g = mondo.giocatori[9]
    g.arretrati = 1020
    buonuscita = contratti.buonuscita(g, OGGI)
    assert buonuscita > 0
    bologna.cassa = buonuscita + 1019
    assert mondo.problema_svincolo(bologna, g) == (f"Svincolare {_nome(g)} costa {_euro(buonuscita)} di buonuscita e 1.020 euro di arretrati, "
                                                   f"e la cassa di Pat-Bologna ne ha {_euro(buonuscita + 1019)}.")
    # Scoperta T6 della revisione dei rimedi: a fermarlo sono gli arretrati, che hanno il loro suono; quando la cassa non basta
    # nemmeno per la buonuscita, no, e il suono resta quello della cassa insufficiente.
    assert mondo.arretrati_fermano_lo_svincolo(bologna, g)
    bologna.cassa = buonuscita - 1
    assert mondo.problema_svincolo(bologna, g) and not mondo.arretrati_fermano_lo_svincolo(bologna, g)
    bologna.cassa = buonuscita + 1019
    domanda = testi.domanda_svincolo(g, bologna, mondo)
    assert f"la buonuscita è di {_euro(buonuscita)}. Lo svincolo salda anche gli arretrati che aspetta, 1.020 euro. " in domanda
    # Scoperta T3 della revisione dei rimedi: la cifra dopo gli arretrati, perché con 800 euro i 800 euro non si dice.
    g.arretrati = 800
    assert "Lo svincolo salda anche gli arretrati che aspetta, 800 euro. " in testi.domanda_svincolo(g, bologna, mondo)
    g.arretrati = 1020
    bologna.cassa += 1
    assert mondo.svincola(bologna, g) == buonuscita
    assert bologna.cassa == 0 and bologna.conti_del_mese["buonuscite"] == buonuscita and bologna.conti_del_mese["arretrati"] == 1020
    assert g.appartenenza == "*" and g.arretrati == 0
    assert bologna.diario[0]["testo"] == f"Svincolato {_nome(g)}, con una buonuscita di {_euro(buonuscita)} e 1.020 euro di arretrati."
    assert testi.svincolato(g, bologna, mondo, buonuscita, 1020).startswith(
        f"{_nome(g)} è {testi.accorda(g, 'svincolato')} da Pat-Bologna, con una buonuscita di {_euro(buonuscita)} e 1.020 euro di arretrati, e torna ")
    # Il computer non cambia: per lui lo svincolo guarda soltanto la buonuscita.
    tesserato_cpu = mondo.giocatori[1]
    tesserato_cpu.arretrati = 5000
    cpu.cassa = contratti.buonuscita(tesserato_cpu, OGGI)
    assert mondo.problema_svincolo(cpu, tesserato_cpu) is None and not mondo.arretrati_fermano_lo_svincolo(cpu, tesserato_cpu)


def test_la_vendita_dell_utente_salda_tutti_gli_arretrati():
    mondo, cpu, bologna, _milano = _mondo()
    g = mondo.giocatori[10]
    g.arretrati = 1500
    bologna.cassa = 300
    assert mondo.arretrati_scoperti(bologna, g, 1000) == 200
    atteso = f"A 1.000 euro mancano 200 euro: la vendita salda gli arretrati di {_nome(g)}, 1.500 euro, prima dal prezzo e poi dalla cassa di Pat-Bologna, che ne ha 300 euro."
    assert mondo.problema_vendita(bologna, g, 1000) == atteso
    with pytest.raises(ValueError, match="mancano 200 euro"):
        mondo.metti_in_vendita(bologna, g, 1000)
    assert g.id not in bologna.in_vendita
    mondo.metti_in_vendita(bologna, g, 1200)
    mondo._vendi(bologna, cpu, g, 1200, OGGI)
    assert bologna.cassa == 0 and bologna.conti_del_mese["vendite"] == 1200 and bologna.conti_del_mese["arretrati"] == 1500
    assert bologna.diario[0]["testo"] == f"Venduto {_nome(g)} a {cpu.nome} per 1.200 euro, e salda 1.500 euro di arretrati."
    assert g.diario[0]["testo"].endswith(f"a {cpu.nome} per 1.200 euro: riceve 1.500 euro di arretrati.")
    assert cpu.diario[0]["testo"] == f"Comprato {_nome(g)} da Pat-Bologna per 1.200 euro."
    # Il computer, quando vende lui, salda fino al prezzo, come prima, e i diari non cambiano.
    suo = mondo.giocatori[2]
    suo.arretrati = 800
    cassa_cpu = cpu.cassa
    mondo._vendi(cpu, bologna, suo, 500, OGGI)
    assert cpu.cassa == cassa_cpu and cpu.conti_del_mese["arretrati"] == 500
    assert cpu.diario[0]["testo"] == f"Venduto {_nome(suo)} a Pat-Bologna per 500 euro."
    assert mondo.arretrati_scoperti(cpu, mondo.giocatori[3], 1) == 0


def test_il_computer_non_compra_se_gli_arretrati_restano_scoperti():
    mondo, cpu, bologna, _milano = _mondo()
    altra = polisportiva(mondo, "PoliTeam02 Prova", ids=(5, 6))
    cpu.cassa = altra.cassa = 1_000_000
    primo, secondo = mondo.giocatori[10], mondo.giocatori[11]
    _firmati_a_rampa_finita(primo, secondo)
    prezzi = {}
    for g in (primo, secondo):
        prezzi[g.id] = max(1, economia.valore_di_mercato(g, OGGI))
        g.arretrati = prezzi[g.id] + 500
    bologna.cassa = 700
    for g in (primo, secondo):
        mondo.metti_in_vendita(bologna, g, prezzi[g.id])
    # Ciascuno da solo si può vendere, ma la cassa ne copre uno soltanto: il computer vede il primo, e il secondo aspetta.
    assert [riga[0].id for riga in mondo._vendibili(OGGI)] == [10]
    mercato_del_giorno = _Mercato(mondo._vendibili(OGGI))
    comprati = [poli for poli in (cpu, altra) if mondo._compra_dal_mercato(poli, OGGI, mercato_del_giorno)]
    assert len(comprati) == 1 and bologna.cassa == 200 and list(bologna.in_vendita) == [11]
    # Con la cassa che non basta il giocatore resta fuori dal mercato del computer.
    assert mondo._vendibili(OGGI) == []
    bologna.cassa = 500
    assert len(mondo._vendibili(OGGI)) == 1


# La chiusura salda tutto.

def _con_lo_staff(mondo, poli):
    """Un capo allenatore assunto dieci giorni fa, che oggi ha uno stipendio maturato."""
    a = mondo._nasce_un_allenatore(OGGI)
    mondo.assumi_allenatore(poli, a, 0, OGGI - datetime.timedelta(days=10))
    return a


def test_la_chiusura_salda_tutto_e_le_altre_coprono_oltre_la_riserva():
    mondo, _cpu, bologna, milano = _mondo()
    roma = polisportiva(mondo, "Pat-Roma", cpu=False, ids=(14, 29))
    # Gli arretrati di Roma alzano la sua riserva, e così la sua cassa, che resta la più ricca.
    mondo.giocatori[14].arretrati = 9000
    a = _con_lo_staff(mondo, bologna)
    tesserato = mondo.giocatori[9]
    tesserato.arretrati = 400
    debiti = mondo.debiti_di_chiusura(bologna)
    assert [d.persona for d in debiti] == [mondo.giocatori[gid] for gid in bologna.tesserati] + [a]
    assert debiti[0] == (tesserato, False, contratti.buonuscita(tesserato, OGGI), 400)
    maturato = round(a.contratto_stipendio * 4 / 31)
    a_buonuscita = contratti.buonuscita(a, OGGI)
    assert debiti[-1] == (a, True, contratti.buonuscita(a, OGGI), maturato) and maturato > 0
    costo = sum(d.buonuscita + d.altro for d in debiti)
    # Roma è la più ricca e ha 700 euro oltre la riserva, Milano 600: la chiusura prende da Roma, poi da Milano.
    bologna.cassa = costo - 1000
    roma.cassa = mondo.riserva(roma) + 700
    milano.cassa = mondo.riserva(milano) + 600
    assert roma.cassa > milano.cassa
    piano = mondo.piano_di_chiusura(bologna)
    assert piano.costo == costo and piano.manca == 0 and piano.cassa_persa == 0
    assert piano.paganti == [(bologna, costo - 1000), (roma, 700), (milano, 300)]
    assert mondo.problema_chiusura(bologna) is None
    domanda = testi.domanda_chiusura(bologna, piano)
    assert domanda.startswith(f"Chiudere per sempre Pat-Bologna? Costa {_euro(costo)}: ai tesserati ")
    assert (f"La sua cassa ne paga {_euro(costo - 1000)}, e il resto lo coprono le tue altre polisportive, oltre la loro riserva: "
            "Pat-Roma 700 euro e Pat-Milano 300 euro. Della cassa non resta niente. I suoi 6 tesserati torneranno liberi") in domanda
    assert f", allo staff {_euro(a_buonuscita)} di buonuscite e {_euro(maturato)} di stipendi maturati." in domanda
    cassa_roma, cassa_milano = roma.cassa, milano.cassa
    assert mondo.chiudi_polisportiva(bologna) == 6
    assert bologna.nome not in mondo.polisportive and roma.cassa == cassa_roma - 700 and milano.cassa == cassa_milano - 300
    assert roma.diario[0]["testo"] == "Paga 700 euro dei debiti di Pat-Bologna, che chiude: buonuscite, arretrati e stipendi che la sua cassa non copriva."
    # Le voci dei conti dicono che cosa hanno pagato: Milano, l'ultima, paga la fine dei debiti, cioè lo staff.
    assert sum(roma.conti_del_mese.values()) == 700 and sum(milano.conti_del_mese.values()) == 300
    assert milano.conti_del_mese["staff"] == min(300, maturato)
    assert tesserato.diario[0]["testo"] == (f"Torna {testi.accorda(tesserato, 'libero')}: Pat-Bologna ha chiuso, con una "
                                            f"buonuscita di {_euro(debiti[0].buonuscita)} e 400 euro di arretrati.")
    assert a.diario[0]["testo"].endswith(f": Pat-Bologna ha chiuso, con una buonuscita di {_euro(a_buonuscita)} e {_euro(maturato)} di stipendio maturato.")
    assert tesserato.arretrati == 0 and a.libero
    assert testi.chiusa("Pat-Bologna", 6, piano).startswith(
        f"Pat-Bologna ha chiuso per sempre: 6 giocatori tornano liberi. Ha saldato {_euro(costo)} di debiti, con l'aiuto di Pat-Roma, 700 euro e "
        "Pat-Milano, 300 euro. ")


def test_la_chiusura_che_non_si_puo_fare_dice_chi_la_blocca():
    mondo, _cpu, bologna, milano = _mondo()
    bandiera = mondo.giocatori[25]
    # Gli altri tesserati senza contratto non hanno buonuscite: il debito è soltanto quello della bandiera.
    for gid in bologna.tesserati:
        if gid != 25:
            mondo.giocatori[gid].annulla_contratto()
    bandiera.bandiera, bandiera.fedelta = True, FEDELTA_BANDIERA
    bandiera.arretrati = 50_000
    debito = contratti.buonuscita(bandiera, OGGI) + 50_000
    costo = sum(d.buonuscita + d.altro for d in mondo.debiti_di_chiusura(bologna))
    assert costo == debito
    bologna.cassa = 1000
    milano.cassa = mondo.riserva(milano) + 200
    manca = costo - 1200
    atteso = (f"Per chiudere Pat-Bologna servono {_euro(costo)}: la sua cassa ne ha 1.000 euro, le tue altre polisportive, oltre la loro "
              f"riserva, 200 euro, e mancano {_euro(manca)}. La blocca il debito con {_nome(bandiera)}, bandiera, per {_euro(debito)}. "
              "Una bandiera non se ne va da sola, nemmeno senza stipendio.")
    assert mondo.problema_chiusura(bologna) == atteso
    with pytest.raises(ValueError, match="Per chiudere Pat-Bologna"):
        mondo.chiudi_polisportiva(bologna)
    assert bologna.nome in mondo.polisportive and bologna.cassa == 1000 and bandiera.appartenenza == bologna.nome
    assert milano.cassa == mondo.riserva(milano) + 200
    # Senza la bandiera, e coi contratti di tutti, i debiti più grandi bloccano insieme, dal primo, quanti ne servono a fare la cifra che manca.
    mondo, _cpu, bologna, milano = _mondo()
    bologna.cassa = milano.cassa = 0
    debiti = sorted(mondo.debiti_di_chiusura(bologna), key=lambda d: (-(d.buonuscita + d.altro), _nome(d.persona)))
    assert len(debiti) == 6 and all(not d.altro for d in debiti)
    primi = ", con ".join(f"{_nome(d.persona)} per {_euro(d.buonuscita)}" for d in debiti[:3])
    problema = mondo.problema_chiusura(bologna)
    assert problema.startswith(f"Per chiudere Pat-Bologna servono {_euro(sum(d.buonuscita for d in debiti))}: la sua cassa ne ha 0 euro, le tue altre ")
    assert problema.endswith(f" La bloccano i debiti con {primi} e con altre 3 persone.")


def test_la_polisportiva_del_computer_chiude_come_prima():
    mondo, cpu, _bologna, _milano = _mondo()
    g = mondo.giocatori[1]
    g.arretrati = 300
    cpu.cassa = 0
    assert mondo.problema_chiusura(cpu) is None
    assert mondo.chiudi_polisportiva(cpu) == 6
    assert g.diario[0]["testo"] == f"Torna {testi.accorda(g, 'libero')}: PoliTeam01 Prova ha chiuso."


# I convocati e le rose della Coppa.

def _frase_della_sfida(g, giorno_del_gioco):
    return (f"{_nome(g)} è {testi.accorda(g, 'convocato')} nella sfida {testi.con_articolo('del', testi.data_breve(giorno_del_gioco))}: fino alla partita non si vende, "
            "non si compra e non si svincola.")


def test_chi_e_convocato_in_una_sfida_non_si_muove_fino_alla_partita(larga):
    mondo, cpu, bologna, _milano = _mondo()
    in_vendita = mondo.giocatori[11]
    mondo.metti_in_vendita(bologna, in_vendita, 100)
    # La proposta del lancio lascia fuori chi è in vendita; se lo convochi tu, accettata la sfida esce dalla vendita.
    assert 11 not in sfide.proposta(mondo, bologna)
    s, messaggio = sfide.lancia(mondo, bologna, cpu.nome, [9, 10, 25, 11])
    assert s.stato == sfide.ACCETTATA and messaggio.endswith(f"{_nome(in_vendita)} esce dalla vendita fino alla partita.")
    assert 11 not in bologna.in_vendita
    convocato = "convocato" if in_vendita.sesso == "m" else "convocata"
    assert any(v["testo"] == f"Toglie {_nome(in_vendita)} dalla vendita: è {convocato} nella sfida del {testi.data_breve(DOMANI)}." for v in bologna.diario)
    g = mondo.giocatori[9]
    frase = _frase_della_sfida(g, DOMANI)
    assert mondo.impegno_di_squadra(g) == frase
    assert mondo.problema_vendita(bologna, g, 100) == frase and mondo.problema_svincolo(bologna, g) == frase
    with pytest.raises(ValueError, match="fino alla partita"):
        mondo.metti_in_vendita(bologna, g, 100)
    # I convocati del computer non si comprano e non ricevono offerte d'acquisto, e il mercato lo dice col suo perché.
    suoi = s.convocati["sfidata"]
    cpu.in_vendita[suoi[0]] = 100
    assert mondo.problema_acquisto(bologna, mondo.giocatori[suoi[0]]) == _frase_della_sfida(mondo.giocatori[suoi[0]], DOMANI)
    assert mondo.problema_offerta_d_acquisto(bologna, mondo.giocatori[suoi[1]], 100) == _frase_della_sfida(mondo.giocatori[suoi[1]], DOMANI)
    righe = {r.persona.id: r for r in mercato.Memoria(mondo).righe_di(mercato.GIOCATORI)}
    assert mercato.offerta_possibile(mondo, bologna, righe[suoi[0]]).motivo == mercato.CONVOCATO_BLOCCATO
    assert mercato.offerta_possibile(mondo, bologna, righe[suoi[1]]) == (mercato.OFFERTA_D_ACQUISTO, _frase_della_sfida(mondo.giocatori[suoi[1]], DOMANI),
                                                                        mercato.CONVOCATO_BLOCCATO)
    # Il computer non compra i tuoi convocati; i suoi, fra sé, sì, come prima.
    _firmati_a_rampa_finita(mondo.giocatori[10], mondo.giocatori[26])
    bologna.in_vendita[10] = 1
    bologna.in_vendita[26] = 1
    assert {riga[0].id for riga in mondo._vendibili(OGGI) if riga[1] is bologna} == {26}
    # Dopo la partita tutto torna libero.
    mondo.datetime_corrente_simulazione = DOMANI
    sfide.giorno(mondo, DOMANI, Mondo.rapporto_vuoto(DOMANI))
    assert mondo.impegno_di_squadra(g) is None and mondo.problema_vendita(bologna, g, 100) is None


def test_accettare_una_sfida_toglie_dalla_vendita_i_convocati(larga):
    mondo, cpu, bologna, _milano = _mondo()
    sfide._proponi(mondo, cpu, bologna, sfide.convoca(mondo, cpu, DOMANI), OGGI.date(), Mondo.rapporto_vuoto(OGGI))
    s = sfide.in_arrivo(mondo, bologna)[0]
    for gid in (25, 26):
        mondo.metti_in_vendita(bologna, mondo.giocatori[gid], 100)
    messaggio = sfide.accetta(mondo, s.id, bologna, [9, 10, 25])
    assert messaggio.endswith(f" {_nome(mondo.giocatori[25])} esce dalla vendita fino alla partita.")
    assert 25 not in bologna.in_vendita and 26 in bologna.in_vendita
    assert mondo.giocatori[25].diario[0]["testo"] == f"Esce dalla vendita di Pat-Bologna: è convocata nella sfida del {testi.data_breve(DOMANI)}."


def test_la_rosa_della_coppa_resta_ferma_fino_alla_fine():
    mondo, cpu, bologna, milano = _mondo()
    # Quattro qualificate, il minimo della coppa.
    altra = polisportiva(mondo, "PoliTeam02 Prova", ids=(5, 6, 7, 8, 23, 24))
    for poli, gloria in ((cpu, 300), (bologna, 250), (milano, 200), (altra, 100)):
        poli.gloria = gloria
    for gid in (14, 29):
        mondo._entra(milano, mondo.giocatori[gid])
    apertura = datetime.datetime(2027, 5, 26, 9, 0)
    mondo.datetime_corrente_simulazione = apertura
    g = mondo.giocatori[9]
    mondo.metti_in_vendita(bologna, g, 100)
    solo(["Coppa delle polisportive"])
    ed = apri(mondo, apertura, "Coppa delle polisportive")[0]
    assert ed.ids() == [cpu.nome, bologna.nome, milano.nome, altra.nome] and 9 in ed.iscritto(bologna.nome)["rosa"]
    # Alla qualificazione chi era in vendita ne esce, con la voce nel diario.
    frase = (f"{_nome(g)} è nella rosa della Coppa delle polisportive del 15 giugno 2027: fino alla fine della coppa non si vende, "
             "non si compra e non si svincola.")
    assert 9 not in bologna.in_vendita and mondo.impegno_di_squadra(g) == frase
    assert any(v["testo"] == f"Toglie {_nome(g)} dalla vendita: è nella rosa della Coppa delle polisportive del 15 giugno 2027." for v in bologna.diario)
    assert mondo.problema_svincolo(bologna, g) == frase
    # Chi entra nella rosa cambiata esce dalla vendita, come alla qualificazione.
    nuovo = mondo.giocatori[30]
    mondo._entra(bologna, nuovo)
    mondo.metti_in_vendita(bologna, nuovo, 100)
    sfide.cambia_rosa(mondo, ed.id, bologna, [25, 9, 10, 30])
    assert 30 not in bologna.in_vendita
    # Chi è nella rosa di un'altra polisportiva iscritta alla stessa coppa non entra nella tua: la rosa che ha lasciato non lo ferma più sul mercato.
    mondo._lascia(bologna, nuovo)
    mondo._entra(milano, nuovo)
    assert mondo.impegno_di_squadra(nuovo) is None
    assert sfide.problema_rosa(mondo, ed.id, milano, [12, 13, 30]) == f"{_nome(nuovo)} è già nella rosa di Pat-Bologna per la Coppa delle polisportive."
    # Durante la coppa la rosa resta ferma, e alla fine torna libera.
    data = datetime.datetime(2027, 6, 15, 9, 0)
    giorno(mondo, data)
    assert mondo.calendario.tornei and mondo.impegno_di_squadra(g) == frase
    while mondo.calendario.tornei:
        data += datetime.timedelta(days=1)
        giorno(mondo, data)
    assert mondo.impegno_di_squadra(g) is None


def test_i_convocati_si_leggono_da_sfide_e_coppe():
    mondo, cpu, bologna, _milano = _mondo()
    s = sfide.Sfida(mondo.sfide.nuovo_id(), iscrizioni.club_della(bologna), iscrizioni.club_della(cpu), OGGI.date(), OGGI.date(), sfide.ACCETTATA,
                    DOMANI.date(), {"sfidante": [9, 10, 25], "sfidata": [1, 2, 21]})
    mondo.sfide.attive.append(s)
    impegni = sfide.convocazioni(mondo)
    assert impegni[9] == [(bologna.nome, None, DOMANI.date())] and impegni[1] == [(cpu.nome, None, DOMANI.date())]
    assert sfide.convocazione(mondo, mondo.giocatori[9], impegni) == (bologna.nome, None, DOMANI.date())
    # Scoperta T3 della revisione dei rimedi: davanti all'8 e all'11 l'articolo si elide, nella sfida e nella rosa.
    g = mondo.giocatori[9]
    s.data_gioco = datetime.date(2026, 10, 8)
    assert sfide.impegno_di_squadra(mondo, g).startswith(f"{_nome(g)} è {testi.accorda(g, 'convocato')} nella sfida dell'8 ottobre 2026: ")
    mondo.metti_in_vendita(bologna, mondo.giocatori[26], 100)
    sfide.fuori_dalla_vendita(mondo, bologna, [26], "Coppa delle polisportive", datetime.date(2027, 6, 11))
    assert any(v["testo"] == f"Toglie {_nome(mondo.giocatori[26])} dalla vendita: è nella rosa della Coppa delle polisportive dell'11 giugno 2027."
               for v in bologna.diario)
    s.data_gioco = DOMANI.date()
    # Una sfida proposta non ferma nessuno.
    s.stato = sfide.PROPOSTA
    assert sfide.convocazioni(mondo) == {} and sfide.impegno_di_squadra(mondo, mondo.giocatori[9]) is None


def _coppa_con_due_tue():
    """La Coppa delle polisportive con quattro qualificate, due tue, Pat-Bologna e Pat-Milano, il giorno dell'apertura."""
    mondo, cpu, bologna, milano = _mondo()
    altra = polisportiva(mondo, "PoliTeam02 Prova", ids=(5, 6, 7, 8, 23, 24))
    for poli, gloria in ((cpu, 300), (bologna, 250), (milano, 200), (altra, 100)):
        poli.gloria = gloria
    for gid in (14, 29):
        mondo._entra(milano, mondo.giocatori[gid])
    apertura = datetime.datetime(2027, 5, 26, 9, 0)
    mondo.datetime_corrente_simulazione = apertura
    solo(["Coppa delle polisportive"])
    ed = apri(mondo, apertura, "Coppa delle polisportive")[0]
    return mondo, bologna, milano, ed


def test_la_rosa_di_una_polisportiva_chiusa_non_ferma_piu_nessuno():
    # Scoperta A7 della revisione dei rimedi di D40: la chiusura lascia il club fra gli iscritti fino al sorteggio, ma la sua
    # rosa non ferma più i giocatori che ha liberato.
    mondo, bologna, milano, ed = _coppa_con_due_tue()
    x = mondo.giocatori[ed.iscritto(bologna.nome)["rosa"][0]]
    assert mondo.impegno_di_squadra(x) is not None
    mondo.datetime_corrente_simulazione += datetime.timedelta(days=2)
    assert mondo.problema_chiusura(bologna) is None
    mondo.chiudi_polisportiva(bologna)
    assert ed.iscritto(bologna.nome) is not None and x.id not in sfide.convocazioni(mondo)
    # Primo caso: la sorella firma chi è tornato libero e lo mette nella sua rosa.
    mondo._entra(milano, x)
    rosa = [*ed.iscritto(milano.nome)["rosa"][:2], x.id]
    assert mondo.impegno_di_squadra(x) is None and sfide.problema_rosa(mondo, ed.id, milano, rosa) is None
    mondo._lascia(milano, x)
    # Secondo caso: un club nuovo con lo stesso nome non trova il giocatore fermo dalla rosa del club chiuso.
    nuova = mondo.fonda_polisportiva("Pat-Bologna", luogo="Bologna")
    mondo._entra(nuova, x)
    assert mondo.impegno_di_squadra(x) is None
    assert mondo.problema_svincolo(nuova, x) is None and mondo.problema_vendita(nuova, x, 100) is None


def test_la_sfida_accettata_di_una_polisportiva_chiusa_non_ferma_piu_nessuno(larga):
    # Scoperta A7 della revisione dei rimedi di D40: la sfida decade al giro seguente, e intanto non ferma nessuno, né i
    # tuoi convocati liberati dalla chiusura né quelli del computer.
    mondo, cpu, bologna, milano = _mondo()
    s = sfide.Sfida(mondo.sfide.nuovo_id(), iscrizioni.club_della(bologna), iscrizioni.club_della(cpu), OGGI.date(), OGGI.date(), sfide.ACCETTATA,
                    DOMANI.date(), {"sfidante": [9, 10, 25], "sfidata": [1, 2, 21]})
    mondo.sfide.attive.append(s)
    tuo, suo = mondo.giocatori[9], mondo.giocatori[1]
    cpu.in_vendita[suo.id] = 100
    assert mondo.problema_acquisto(milano, suo) == _frase_della_sfida(suo, DOMANI)
    assert mondo.problema_chiusura(bologna) is None
    mondo.chiudi_polisportiva(bologna)
    assert s in mondo.sfide.attive and sfide.convocazioni(mondo) == {}
    mondo._entra(milano, tuo)
    assert mondo.impegno_di_squadra(tuo) is None and mondo.problema_vendita(milano, tuo, 100) is None
    assert mondo.impegno_di_squadra(suo) is None and mondo.problema_acquisto(milano, suo) is None
    # Al giro seguente la sfida decade, come prima.
    sfide.giorno(mondo, OGGI, Mondo.rapporto_vuoto(OGGI))
    assert s not in mondo.sfide.attive and s.stato == sfide.DECADUTA


# Lo sponsor paga la gloria per i tesserati in attività.

# I quindici liberi del mondo di prova, per una rosa piena.
LIBERI = (5, 6, 7, 8, 14, 15, 16, 17, 18, 19, 20, 23, 24, 29, 30)


def _con_la_gloria(mondo, gloria=150):
    """Tutte le polisportive del mondo con la stessa gloria: 150 punti fanno 1.260 euro al mese, e un posto 84, cioè 80 euro."""
    for poli in mondo.polisportive.values():
        poli.gloria = gloria
    return gloria * SPONSOR_PER_GLORIA


def _parte_del_valore(mondo, poli):
    return QUOTA_SPONSOR_SUL_VALORE * sum(economia.valore_di_mercato_pieno(g) for g in mondo._rosa(poli) if not g.ritirato)


def test_lo_sponsor_paga_la_gloria_per_i_tesserati_in_attivita():
    mondo, cpu, bologna, milano = _mondo()
    vuota = polisportiva(mondo, "Pat-Vuota", cpu=False)
    piena = polisportiva(mondo, "Pat-Piena", cpu=False, ids=LIBERI)
    gloria = _con_la_gloria(mondo)
    # Pat-Bologna ha 6 tesserati su 15, e la gloria si paga per 6; il computer, con 6 anche lui, la incassa tutta.
    assert mondo.tesserati_nello_sponsor(bologna) == 6 and mondo.tesserati_nello_sponsor(cpu) is None
    assert mondo.sponsor(bologna) == economia.arrotonda(gloria * 6 / 15 + _parte_del_valore(mondo, bologna))
    assert mondo.sponsor(cpu) == economia.arrotonda(gloria + _parte_del_valore(mondo, cpu))
    # Chi si è ritirato non conta, né nella gloria né nel valore.
    rosa = mondo._rosa(bologna)
    rosa[0].ritirato = True
    assert economia.sponsor_mensile(bologna, rosa) == economia.arrotonda(gloria * 5 / 15 + _parte_del_valore(mondo, bologna))
    rosa[0].ritirato = False
    # Una polisportiva vuota non incassa niente; con la rosa piena la gloria si paga tutta, come al computer.
    assert mondo.tesserati_nello_sponsor(vuota) == 0 and mondo.sponsor(vuota) == 0
    assert mondo.tesserati_nello_sponsor(piena) == 15 and mondo.sponsor(piena) == economia.arrotonda(gloria + _parte_del_valore(mondo, piena))
    # Dividere non rende: i 9 tesserati di Bologna e Milano portano la stessa gloria che porterebbero insieme.
    insieme = economia.quota_della_gloria(mondo._rosa(bologna) + mondo._rosa(milano))
    assert economia.quota_della_gloria(mondo._rosa(bologna)) + economia.quota_della_gloria(mondo._rosa(milano)) == pytest.approx(insieme) == 9 / 15
    assert economia.gloria_di_un_posto(bologna) == 80


def test_conti_barra_scheda_e_bilancio_dicono_la_stessa_cifra():
    mondo, _cpu, bologna, _milano = _mondo()
    _con_la_gloria(mondo)
    sponsor = mondo.sponsor(bologna)
    cifra = _euro(sponsor)
    assert f"| Sponsor: {cifra} al mese, con la gloria pagata per 6 tesserati su 15 | Stipendi: " in testi.scheda_polisportiva(bologna, mondo)
    bilancio = testi.bilancio(bologna, mondo)
    assert f"\nOgni mese entrano {cifra} di sponsor ed escono " in bilancio
    assert "\nLo sponsor paga la gloria per 6 tesserati su 15: ogni posto vuoto costa 80 euro al mese.\n" in bilancio
    assert testi.testata_contratti(bologna, mondo).startswith(f"Pat-Bologna: cassa 20.000 euro, sponsor {cifra} al mese, con la gloria pagata per 6 tesserati su 15, stipendi ")
    assert barra.CATALOGO["sponsor"].testo(barra._Calcolo(barra.Contesto(mondo, adesso_utc()))) == f"Spo:{testi.intero(sponsor)}"
    # I conti del primo del mese incassano proprio quella cifra.
    primo = datetime.datetime(2026, 11, 1, 9, 0)
    mondo._primo_del_mese(primo, Mondo.rapporto_vuoto(primo))
    assert bologna.bilanci[0]["sponsor"] == sponsor


def test_le_frasi_dello_sponsor_con_la_rosa_non_piena():
    mondo, cpu, bologna, milano = _mondo()
    _con_la_gloria(mondo)
    # Il computer e la rosa piena non dicono niente di nuovo.
    assert testi.gloria_dello_sponsor(cpu, mondo) == testi.posti_vuoti_nello_sponsor(cpu, mondo) == ""
    assert f"| Sponsor: {_euro(mondo.sponsor(cpu))} al mese | Stipendi: " in testi.scheda_polisportiva(cpu, mondo)
    for gid in LIBERI[:9]:
        mondo._entra(bologna, mondo.giocatori[gid])
    assert testi.gloria_dello_sponsor(bologna, mondo) == "" and "posto vuoto" not in testi.bilancio(bologna, mondo)
    # Un tesserato solo, e nessuno.
    for gid in (13, 28):
        mondo._lascia(milano, mondo.giocatori[gid])
    assert testi.gloria_dello_sponsor(milano, mondo) == "con la gloria pagata per 1 tesserato su 15"
    assert testi.posti_vuoti_nello_sponsor(milano, mondo) == "Lo sponsor paga la gloria per 1 tesserato su 15: ogni posto vuoto costa 80 euro al mese."
    mondo._lascia(milano, mondo.giocatori[12])
    assert "| Sponsor: 0 euro al mese, senza la gloria, perché non ha tesserati | Stipendi: " in testi.scheda_polisportiva(milano, mondo)
    assert testi.posti_vuoti_nello_sponsor(milano, mondo) == "Senza tesserati lo sponsor non paga la gloria: ogni posto vuoto costa 80 euro al mese."


# Le fondazioni: due col capitale, poi a pagamento, e il ripensamento.

def test_le_prime_due_fondazioni_sono_gratis_e_dalla_terza_si_paga():
    mondo = mondo_di_prova(20, 20)
    # La prima e la seconda sono gratis, coi 20.000 euro del capitale, e il contatore sale a ogni fondazione.
    conto = mondo.conto_della_fondazione()
    assert conto == (0, 0, CAPITALE_INIZIALE, None, 0, 0) and testi.conto_della_fondazione(conto) == "Fondazione gratis, con 20.000 euro di cassa."
    prima = mondo.fonda_polisportiva("Pat-Bologna")
    assert prima.cassa == 20_000 and mondo.fondazioni_di_sempre == 1 and testi.fondata(prima, mondo, conto).startswith("Hai fondato Pat-Bologna. È la tua ")
    seconda = mondo.fonda_polisportiva("Pat-Milano")
    assert seconda.cassa == 20_000 and mondo.fondazioni_di_sempre == 2 and mondo.miapolisportiva_attiva is seconda
    # La terza costa 50.000 euro, li paga la polisportiva attiva alla voce acquisti, e la nuova parte con la cassa vuota.
    mondo._entra(seconda, mondo.giocatori[1])
    seconda.cassa = mondo.riserva(seconda) + 60_000
    cassa = seconda.cassa
    conto = mondo.conto_della_fondazione()
    assert conto == (2, 50_000, 0, seconda, 60_000, 0) and mondo.problema_fondazione() is None
    assert testi.conto_della_fondazione(conto) == "La tua terza polisportiva aperta costa 50.000 euro, pagati da Pat-Milano, e parte con la cassa vuota."
    terza = mondo.fonda_polisportiva("Pat-Roma")
    assert terza.cassa == 0 and seconda.cassa == cassa - 50_000 and seconda.conti_del_mese["acquisti"] == 50_000 and mondo.fondazioni_di_sempre == 3
    assert seconda.diario[0]["testo"] == "Paga 50.000 euro per fondare Pat-Roma, la tua terza polisportiva aperta."
    assert terza.diario[0]["testo"] == "Parte con la cassa vuota: la fondazione è costata 50.000 euro, pagati da Pat-Milano."
    assert testi.fondata(terza, mondo, conto).startswith("Hai fondato Pat-Roma, la tua terza polisportiva aperta: Pat-Milano ha pagato 50.000 euro, e "
                                                         "Pat-Roma parte con la cassa vuota. È la tua polisportiva attiva.\n")
    # La quarta costa 80.000 euro per il quadrato dei posti oltre il secondo, 320.000 euro, e la quinta 720.000.
    terza.cassa = 400_000
    conto = mondo.conto_della_fondazione()
    assert conto.prezzo == 320_000 and conto.pagante is terza and conto.capitale == 0
    quarta = mondo.fonda_polisportiva("Pat-Napoli")
    assert terza.cassa == 80_000 and quarta.cassa == 0 and mondo.fondazioni_di_sempre == 4
    assert mondo.conto_della_fondazione().prezzo == 720_000
    assert [prezzo_della_fondazione(aperte) for aperte in range(6)] == [0, 0, 50_000, 320_000, 720_000, 1_280_000]
    # Il computer fonda come prima: coi 20.000 euro, senza prezzo e senza toccare il contatore, e non entra nel conto.
    cpu = mondo.polisportive[mondo.crea_polisportiva_cpu(OGGI)]
    assert cpu.cassa == CAPITALE_INIZIALE and mondo.fondazioni_di_sempre == 4 and mondo.conto_della_fondazione().aperte == 4


def test_il_capitale_dopo_le_chiusure_e_chi_riparte_da_zero():
    mondo = mondo_di_prova(20, 20)
    bologna = mondo.fonda_polisportiva("Pat-Bologna")
    milano = mondo.fonda_polisportiva("Pat-Milano")
    # Tutte e due usate, con un tesserato: chiuderle non è un ripensamento.
    mondo._entra(bologna, mondo.giocatori[1])
    mondo._entra(milano, mondo.giocatori[2])
    mondo.chiudi_polisportiva(milano)
    assert mondo.fondazioni_di_sempre == 2
    # Il prezzo conta soltanto le aperte, e la nuova è gratis; ma il capitale è già andato alle prime due fondazioni.
    conto = mondo.conto_della_fondazione()
    assert conto == (1, 0, 0, None, 0, 0) and testi.conto_della_fondazione(conto) == "Fondazione gratis, con la cassa vuota."
    roma = mondo.fonda_polisportiva("Pat-Roma")
    assert roma.cassa == 0 and mondo.fondazioni_di_sempre == 3 and roma.diario[0]["testo"] == "Parte con la cassa vuota."
    assert testi.fondata(roma, mondo, conto).startswith("Hai fondato Pat-Roma, con la cassa vuota. È la tua polisportiva attiva.\n")
    # Chi resta senza nessuna polisportiva aperta riparte col capitale, e la fondazione conta come le altre.
    mondo.chiudi_polisportiva(roma)
    mondo.chiudi_polisportiva(bologna)
    assert mondo.fondazioni_di_sempre == 3
    conto = mondo.conto_della_fondazione()
    assert conto == (0, 0, CAPITALE_INIZIALE, None, 0, 0) and testi.conto_della_fondazione(conto) == "Fondazione gratis, con 20.000 euro di cassa."
    napoli = mondo.fonda_polisportiva("Pat-Napoli")
    assert napoli.cassa == 20_000 and mondo.fondazioni_di_sempre == 4
    # La sorella di chi è ripartito è gratis, ma vuota.
    assert mondo.conto_della_fondazione() == (1, 0, 0, None, 0, 0)


def test_la_fondazione_che_la_riserva_non_lascia_pagare():
    mondo, _cpu, bologna, _milano = _mondo()
    mondo.fondazioni_di_sempre = 2
    riserva = mondo.riserva(bologna)
    bologna.cassa = riserva + 49_000
    # La polisportiva del computer non entra nel conto: le tue aperte sono due, e la nuova è la terza.
    conto = mondo.conto_della_fondazione()
    assert conto == (2, 50_000, 0, bologna, 49_000, 1_000) and riserva > 0
    atteso = (f"La tua terza polisportiva aperta costa 50.000 euro, e mancano 1.000 euro: Pat-Bologna, che la paga, ha 49.000 euro oltre la sua "
              f"riserva di {_euro(riserva)}.")
    assert mondo.problema_fondazione() == atteso
    with pytest.raises(ValueError, match=r"mancano 1\.000 euro"):
        mondo.fonda_polisportiva("Pat-Roma")
    assert "Pat-Roma" not in mondo.polisportive and mondo.fondazioni_di_sempre == 2
    assert bologna.cassa == riserva + 49_000 and bologna.conti_del_mese["acquisti"] == 0 and bologna.diario[0]["testo"] == "Fondata."
    # Con mille euro in più si fonda, e la cassa scende proprio fino alla riserva.
    bologna.cassa += 1_000
    roma = mondo.fonda_polisportiva("Pat-Roma")
    assert bologna.cassa == riserva and roma.cassa == 0 and mondo.fondazioni_di_sempre == 3
    # Senza una polisportiva attiva nessuno paga: la quarta costa 320.000 euro, e la vista dice come sceglierne una.
    mondo.miapolisportiva_attiva = None
    assert mondo.problema_fondazione() == ("La tua quarta polisportiva aperta costa 320.000 euro, e la paga la polisportiva attiva: scegline una "
                                          "con Ctrl+Maiusc+C.")
    with pytest.raises(ValueError, match="la paga la polisportiva attiva"):
        mondo.fonda_polisportiva("Pat-Napoli")


def test_il_ripensamento_riporta_indietro_il_contatore():
    mondo = mondo_di_prova(20, 20)
    mondo.fonda_polisportiva("Pat-Bologna")
    seconda = mondo.fonda_polisportiva("Pat-Milano")
    assert mondo.fondazioni_di_sempre == 2 and mondo.giorni_del_ripensamento(seconda) == 0
    # Tre giorni dopo, senza tesserati né staff e coi suoi 20.000 euro: chiuderla annulla la fondazione, e la cassa si perde.
    mondo.datetime_corrente_simulazione = OGGI + datetime.timedelta(days=3)
    assert mondo.giorni_del_ripensamento(seconda) == 3
    piano = mondo.piano_di_chiusura(seconda)
    assert piano.costo == 0 and piano.cassa_persa == 20_000
    # Dalla scoperta T4 della revisione la frase dice lo stato di oggi, non mai usata; il giorno della fondazione dice ora.
    assert testi.domanda_chiusura(seconda, piano, 3) == ("Chiudere per sempre Pat-Milano? Fondata da 3 giorni, e oggi senza tesserati né staff: "
                                                         "la fondazione non conterà, e la cassa, 20.000 euro, si perde. Non si torna indietro.")
    assert testi.domanda_chiusura(seconda, piano, 0).startswith("Chiudere per sempre Pat-Milano? Fondata oggi, e ora senza tesserati né staff: ")
    assert mondo.chiudi_polisportiva(seconda) == 0 and mondo.fondazioni_di_sempre == 1
    assert testi.chiusa("Pat-Milano", 0, piano, 3).startswith("Pat-Milano ha chiuso per sempre, senza tesserati. La sua fondazione non conta più. ")
    # La prossima fondazione riceve di nuovo il capitale e il contatore torna a 2: il giro non rende niente.
    assert mondo.conto_della_fondazione().capitale == CAPITALE_INIZIALE
    assert mondo.fonda_polisportiva("Pat-Roma").cassa == 20_000 and mondo.fondazioni_di_sempre == 2
    # Il giorno della fondazione, il giorno dopo e il decimo valgono ancora.
    assert [testi.fondata_da(giorni) for giorni in (0, 1, 10)] == ["oggi", "ieri", "da 10 giorni"]
    decimo = polisportiva(mondo, "Pat-Decimo", cpu=False, cassa=20_000, fondazione_giorni=10)
    assert mondo.giorni_del_ripensamento(decimo) == 10


def test_il_ripensamento_non_vale_per_una_polisportiva_usata():
    mondo = mondo_di_prova(20, 20)
    mondo.fondazioni_di_sempre = 5
    vecchia = polisportiva(mondo, "Pat-Vecchia", cpu=False, cassa=20_000, fondazione_giorni=11)
    con_tesserato = polisportiva(mondo, "Pat-Tesserato", cpu=False, cassa=20_000, fondazione_giorni=1, ids=(1,))
    con_lo_staff = polisportiva(mondo, "Pat-Staff", cpu=False, cassa=20_000, fondazione_giorni=1)
    _con_lo_staff(mondo, con_lo_staff)
    povera = polisportiva(mondo, "Pat-Povera", cpu=False, cassa=19_999, fondazione_giorni=0)
    cpu = polisportiva(mondo, "PoliTeam01 Prova", cassa=20_000, fondazione_giorni=0)
    for p in (vecchia, con_tesserato, con_lo_staff, povera, cpu):
        assert mondo.giorni_del_ripensamento(p) is None, p.nome
    # Chiuderle non tocca il contatore, e la domanda non parla di ripensamento.
    for p in (vecchia, con_tesserato, con_lo_staff, povera, cpu):
        assert "la fondazione non conterà" not in testi.domanda_chiusura(p, mondo.piano_di_chiusura(p))
        mondo.chiudi_polisportiva(p)
    assert mondo.fondazioni_di_sempre == 5 and not mondo.polisportive


def test_il_ripensamento_guarda_lo_stato_di_oggi_e_la_domanda_lo_dice():
    # Scoperta T4 della revisione dei rimedi di D40: chi ha tesserato e poi svincolato, con la cassa di nuovo a 20.000 euro, ha
    # il ripensamento anche lui, e la domanda non dice più mai usata.
    mondo = mondo_di_prova(20, 20)
    usata = polisportiva(mondo, "Pat-Usata", cpu=False, cassa=20_000, fondazione_giorni=3, ids=(1,))
    assert mondo.giorni_del_ripensamento(usata) is None
    mondo._lascia(usata, mondo.giocatori[1])
    assert mondo.giorni_del_ripensamento(usata) == 3
    domanda = testi.domanda_chiusura(usata, mondo.piano_di_chiusura(usata), 3)
    assert "Fondata da 3 giorni, e oggi senza tesserati né staff: la fondazione non conterà" in domanda and "mai usata" not in domanda


def test_il_conto_dice_le_fondazioni_di_sempre():
    # Scelta di Gabriele del 3 novembre 2026, che vale come D40: il conto di Nuova polisportiva e il dialogo Cambia polisportiva
    # attiva dicono quante polisportive hai fondato finora, chiuse comprese, e a chi va il capitale.
    coda = ": il capitale di 20.000 euro va soltanto alle prime due, e a chi riparte senza nessuna polisportiva aperta."
    assert testi.fondazioni_finora(0) == "Non hai ancora fondato nessuna polisportiva" + coda
    assert testi.fondazioni_finora(1) == "Finora hai fondato una polisportiva" + coda
    assert testi.fondazioni_finora(3) == "Finora hai fondato 3 polisportive" + coda
    assert testi.fondazioni_finora(1_000) == "Finora hai fondato 1.000 polisportive" + coda
    mondo = mondo_di_prova(20, 20)
    conto = mondo.conto_della_fondazione()
    # Senza il conteggio il conto resta quello di prima; col conteggio lo aggiunge in fondo, gratis o a pagamento.
    assert testi.conto_della_fondazione(conto) == "Fondazione gratis, con 20.000 euro di cassa."
    assert testi.conto_della_fondazione(conto, mondo.fondazioni_di_sempre) == "Fondazione gratis, con 20.000 euro di cassa. " + testi.fondazioni_finora(0)
    bologna = mondo.fonda_polisportiva("Pat-Bologna")
    mondo._entra(bologna, mondo.giocatori[1])
    milano = mondo.fonda_polisportiva("Pat-Milano")
    milano.cassa = 60_000
    assert testi.conto_della_fondazione(mondo.conto_della_fondazione(), mondo.fondazioni_di_sempre) == (
        "La tua terza polisportiva aperta costa 50.000 euro, pagati da Pat-Milano, e parte con la cassa vuota. Finora hai fondato 2 polisportive" + coda)
    # Il ripensamento riporta indietro il contatore, e il conto lo segue; una chiusura vera no.
    assert mondo.chiudi_polisportiva(milano) == 0 and mondo.fondazioni_di_sempre == 1
    assert testi.conto_della_fondazione(mondo.conto_della_fondazione(), mondo.fondazioni_di_sempre).endswith(" Finora hai fondato una polisportiva" + coda)
    mondo.chiudi_polisportiva(bologna)
    assert testi.conto_della_fondazione(mondo.conto_della_fondazione(), mondo.fondazioni_di_sempre) == (
        "Fondazione gratis, con 20.000 euro di cassa. Finora hai fondato una polisportiva" + coda)


# Sposta fondi, quinta tranche.

def test_sposta_fondi_passa_i_soldi_oltre_la_riserva():
    mondo, _cpu, bologna, milano = _mondo()
    riserva = mondo.riserva(bologna)
    spostabile = 20_000 - riserva
    assert 0 < riserva < 20_000 and mondo.spostabile(bologna) == spostabile
    limite = f"Da Pat-Bologna puoi spostare fino a {_euro(spostabile)}: il resto serve agli stipendi del primo novembre."
    assert mondo.limite_dei_fondi(bologna) == limite
    # Oltre la riserva non si sposta, e niente cambia.
    assert mondo.problema_sposta_fondi(bologna, milano, spostabile + 1) == (
        f"Da Pat-Bologna puoi spostare fino a {_euro(spostabile)}, non {_euro(spostabile + 1)}: il resto serve agli stipendi del primo novembre.")
    with pytest.raises(ValueError, match="puoi spostare fino a"):
        mondo.sposta_fondi(bologna, milano, spostabile + 1)
    assert bologna.cassa == 20_000 and milano.cassa == 8_000 and bologna.diario[0]["testo"] == milano.diario[0]["testo"] == "Fondata."
    # Fino alla riserva sì: le due casse, le voci dei conti, i diari, e nessuna mossa.
    mondo.sposta_fondi(bologna, milano, spostabile)
    assert bologna.cassa == riserva and milano.cassa == 8_000 + spostabile
    assert bologna.conti_del_mese["fondi_versati"] == spostabile and milano.conti_del_mese["fondi_ricevuti"] == spostabile
    assert bologna.conti_del_mese["fondi_ricevuti"] == milano.conti_del_mese["fondi_versati"] == 0
    assert bologna.movimenti_oggi == milano.movimenti_oggi == 0
    assert bologna.diario[0]["testo"] == f"Versa {_euro(spostabile)} a Pat-Milano, con Sposta fondi."
    assert milano.diario[0]["testo"] == f"Riceve {_euro(spostabile)} da Pat-Bologna, con Sposta fondi."
    assert mondo.limite_dei_fondi(bologna) == f"Da Pat-Bologna non puoi spostare niente: la sua cassa, {_euro(riserva)}, serve tutta agli stipendi del primo novembre."
    # Il bilancio e la barra li contano: per chi riceve un'entrata, per chi versa un'uscita.
    assert f"fondi ricevuti dalle tue polisportive {_euro(spostabile)}" in testi.bilancio(milano, mondo)
    assert f"fondi versati alle tue polisportive {_euro(spostabile)}" in testi.bilancio(bologna, mondo)
    assert barra._saldo(milano.conti_del_mese) == spostabile and barra._saldo(bologna.conti_del_mese) == -spostabile
    # Nessun limite di tempo: i soldi tornano subito indietro, quelli che Milano ha oltre la sua riserva.
    mondo.sposta_fondi(milano, bologna, 1_000)
    assert bologna.cassa == riserva + 1_000 and bologna.conti_del_mese["fondi_ricevuti"] == 1_000
    # Il primo del mese chi ha pagato paga tutti, e i conti vanno nel bilancio.
    primo = datetime.datetime(2026, 11, 1, 9, 0)
    mondo._primo_del_mese(primo, Mondo.rapporto_vuoto(primo))
    assert not any(mondo.giocatori[gid].arretrati for gid in bologna.tesserati)
    assert bologna.bilanci[0]["fondi_versati"] == spostabile and bologna.bilanci[0]["fondi_ricevuti"] == 1_000
    assert bologna.conti_del_mese["fondi_versati"] == 0
    # Il primo del mese i conti sono già fatti: la riserva è per il primo del mese dopo.
    mondo.datetime_corrente_simulazione = primo
    assert mondo.limite_dei_fondi(milano).endswith("serve agli stipendi del primo dicembre.")


def test_le_frasi_e_i_rifiuti_di_sposta_fondi():
    mondo, cpu, bologna, milano = _mondo()
    roma = polisportiva(mondo, "Pat-Roma", cpu=False, cassa=20_000)
    assert [p.nome for p in mondo.tue_polisportive()] == ["Pat-Bologna", "Pat-Milano", "Pat-Roma"]
    # Senza stipendi da pagare si sposta tutta la cassa.
    assert mondo.riserva(roma) == 0 and mondo.limite_dei_fondi(roma) == (
        "Da Pat-Roma puoi spostare fino a 20.000 euro: è tutta la cassa, perché il primo novembre non deve niente.")
    # Gli arretrati entrano nella riserva, e la frase li dice.
    mondo.giocatori[12].arretrati = 500
    assert mondo.limite_dei_fondi(milano).endswith(": il resto serve agli stipendi e agli arretrati del primo novembre.")
    roma.cassa = 0
    assert mondo.limite_dei_fondi(roma) == "Da Pat-Roma non puoi spostare niente: la sua cassa è vuota."
    assert mondo.problema_sposta_fondi(roma, bologna, 1) == "Da Pat-Roma non puoi spostare niente: la sua cassa è vuota."
    assert mondo.problema_sposta_fondi(bologna, bologna, 100) == "Da Pat-Bologna a Pat-Bologna non si sposta niente: scegli due polisportive diverse."
    assert mondo.problema_sposta_fondi(bologna, milano, 0) == "La cifra deve essere di almeno 1 euro."
    assert mondo.problema_sposta_fondi(bologna, cpu, 100) == mondo.problema_sposta_fondi(cpu, bologna, 100) == (
        "Sposta fondi passa soldi soltanto fra le tue polisportive.")
    assert mondo.problema_sposta_fondi(None, bologna, 100) == "Scegli da quale polisportiva e a quale spostare i fondi."
    assert mondo.problema_sposta_fondi(bologna, milano, 100) is None
    # Le frasi della finestra.
    assert testi.sposta_fondi_non_disponibile(1) == "Sposta fondi passa i soldi fra le tue polisportive, e ne hai una sola: fondane un'altra con Ctrl+N."
    assert testi.sposta_fondi_non_disponibile(0) == "Sposta fondi passa i soldi fra le tue polisportive, e non ne hai nessuna: fondane una con Ctrl+N."
    assert testi.riga_dei_fondi(bologna, mondo) == "Pat-Bologna, attiva, in cassa 20.000 euro"
    assert testi.riga_dei_fondi(milano, mondo) == "Pat-Milano, in cassa 8.000 euro"
    mondo.sposta_fondi(bologna, milano, 2_000)
    assert testi.fondi_spostati(bologna, milano, 2_000) == ("Spostati 2.000 euro da Pat-Bologna a Pat-Milano. Ora Pat-Bologna ha in cassa 18.000 euro, "
                                                            "e Pat-Milano 10.000 euro.")
    # Scoperta T3 della revisione dei rimedi: con 1 euro al singolare, anche nella barra.
    assert testi.fondi_spostati(bologna, milano, 1).startswith("Spostato 1 euro da Pat-Bologna a Pat-Milano.")
    assert (testi.spostato_o_spostati(1), testi.spostato_o_spostati(2)) == ("spostato", "spostati")


def test_sposta_fondi_vuole_la_password_di_chi_paga_se_e_protetta():
    # Scelta di Gabriele del 3 novembre 2026, che vale come D40, scoperte A4 e T2: la password protegge anche la cassa.
    mondo, _cpu, bologna, milano = _mondo()
    milano.imposta_password("segreta")
    milano.cassa = mondo.riserva(milano) + 5_000
    # Bologna è l'attiva: Milano, protetta, paga soltanto con la sua password.
    assert mondo.serve_la_password_dei_fondi(milano) and not mondo.serve_la_password_dei_fondi(bologna)
    frase = "Nessun fondo spostato: Pat-Milano è protetta, e senza la sua password i suoi soldi restano dove sono."
    assert fondi_senza_password(milano) == frase
    cassa_milano, cassa_bologna = milano.cassa, bologna.cassa
    for sbagliata in (None, "", "sbagliata"):
        with pytest.raises(ValueError) as rifiuto:
            mondo.sposta_fondi(milano, bologna, 1_000, sbagliata)
        assert str(rifiuto.value) == frase
    assert milano.cassa == cassa_milano and bologna.cassa == cassa_bologna and milano.conti_del_mese["fondi_versati"] == 0
    # Il limite della riserva viene prima della password, come nel dialogo.
    with pytest.raises(ValueError, match="puoi spostare fino a"):
        mondo.sposta_fondi(milano, bologna, 5_001, "segreta")
    mondo.sposta_fondi(milano, bologna, 1_000, "segreta")
    assert milano.cassa == cassa_milano - 1_000 and bologna.cassa == cassa_bologna + 1_000
    # L'attiva la sua password l'ha già data, anche se è protetta; e chi riceve non la dà.
    bologna.imposta_password("altra")
    assert not mondo.serve_la_password_dei_fondi(bologna)
    mondo.sposta_fondi(bologna, milano, 500)
    # Diventata attiva, Milano non la chiede più; una polisportiva non protetta non la chiede mai.
    mondo.miapolisportiva_attiva = milano
    assert not mondo.serve_la_password_dei_fondi(milano) and mondo.serve_la_password_dei_fondi(bologna)
    mondo.sposta_fondi(milano, bologna, 500)
    milano.imposta_password("")
    mondo.miapolisportiva_attiva = bologna
    assert not mondo.serve_la_password_dei_fondi(milano) and not mondo.serve_la_password_dei_fondi(None)
    assert testi.password_dei_fondi(milano, bologna, 1_000) == "Pat-Milano è protetta: per spostare 1.000 euro a Pat-Bologna serve la sua password."


def _chiusura_con_due_protette(mondo, bologna, milano, oltre_milano=1_500):
    """
    Pat-Bologna chiude, e la sua cassa copre tutto tranne 1.000 euro; Pat-Roma, la più ricca per gli arretrati di un suo
    tesserato, ha 700 euro oltre la riserva, Pat-Milano oltre_milano. Tutte e due protette. Restituisce Pat-Roma e il costo.
    """
    roma = polisportiva(mondo, "Pat-Roma", cpu=False, ids=(14, 29))
    mondo.giocatori[14].arretrati = 9000
    costo = sum(d.buonuscita + d.altro for d in mondo.debiti_di_chiusura(bologna))
    bologna.cassa = costo - 1000
    roma.cassa = mondo.riserva(roma) + 700
    milano.cassa = mondo.riserva(milano) + oltre_milano
    assert roma.cassa > milano.cassa
    roma.imposta_password("roma")
    milano.imposta_password("milano")
    return roma, costo


def test_la_chiusura_chiede_la_password_delle_protette_dalla_piu_ricca():
    # Scelta di Gabriele del 3 novembre 2026, che vale come D40: ogni sorella protetta che il piano fa pagare dà la sua password.
    mondo, _cpu, bologna, milano = _mondo()
    roma, costo = _chiusura_con_due_protette(mondo, bologna, milano)
    # Dalla più ricca, con la quota del piano; quella già sbloccata non si chiede più.
    assert mondo.password_da_chiedere(bologna) == (roma, 700)
    assert mondo.password_da_chiedere(bologna, (), [roma]) == (milano, 300)
    assert mondo.password_da_chiedere(bologna, (), [roma, milano]) is None
    # Roma resta fuori: il piano si rifà, Milano paga tutto il resto, e la sua quota è quella che le si dice.
    piano = mondo.piano_di_chiusura(bologna, [roma])
    assert piano.paganti == [(bologna, costo - 1000), (milano, 1000)] and piano.manca == 0
    assert mondo.password_da_chiedere(bologna, [roma]) == (milano, 1000)
    assert mondo.problema_chiusura(bologna, [roma]) is None
    domanda = testi.domanda_chiusura(bologna, piano, None, [roma])
    assert ("e il resto lo coprono le tue altre polisportive, oltre la loro riserva: Pat-Milano 1.000 euro. Pat-Roma, protetta, resta fuori: "
            "senza la sua password non paga. Della cassa non resta niente.") in domanda
    assert testi.password_della_sorella(bologna, milano, 1000) == (
        "Per chiudere Pat-Bologna, Pat-Milano pagherebbe 1.000 euro dei suoi debiti, oltre la sua riserva, ed è protetta: serve la sua "
        "password. Con Annulla Pat-Milano non paga, e se le altre tue polisportive non bastano la chiusura non si fa.")
    cassa_roma, cassa_milano = roma.cassa, milano.cassa
    mondo.chiudi_polisportiva(bologna, [roma])
    assert bologna.nome not in mondo.polisportive and roma.cassa == cassa_roma and milano.cassa == cassa_milano - 1000
    assert not any("Pat-Bologna" in voce["testo"] for voce in roma.diario)
    assert milano.diario[0]["testo"].startswith("Paga 1.000 euro dei debiti di Pat-Bologna, che chiude")
    # Una sorella non protetta non si chiede mai: paga come prima.
    mondo, _cpu, bologna, milano = _mondo()
    roma, _costo = _chiusura_con_due_protette(mondo, bologna, milano)
    roma.imposta_password("")
    assert mondo.password_da_chiedere(bologna) == (milano, 300)


def test_la_chiusura_senza_le_password_si_blocca_e_dice_chi_resta_fuori():
    mondo, _cpu, bologna, milano = _mondo()
    roma, costo = _chiusura_con_due_protette(mondo, bologna, milano, oltre_milano=600)
    # Senza Roma, Milano non basta: la chiusura è bloccata, e altre password non servono.
    assert mondo.password_da_chiedere(bologna, [roma]) is None
    problema = mondo.problema_chiusura(bologna, [roma])
    assert problema.startswith(f"Per chiudere Pat-Bologna servono {_euro(costo)}: la sua cassa ne ha {_euro(costo - 1000)}, le tue altre polisportive, "
                               "oltre la loro riserva, 600 euro, e mancano 400 euro. ")
    assert problema.endswith(" La blocca anche Pat-Roma, protetta, che senza la sua password non paga: oltre la sua riserva ha 700 euro.")
    with pytest.raises(ValueError, match="La blocca anche Pat-Roma"):
        mondo.chiudi_polisportiva(bologna, [roma])
    assert bologna.nome in mondo.polisportive and milano.cassa == mondo.riserva(milano) + 600
    # Fuori tutte e due: le dice tutte, dalla più ricca.
    assert mondo.problema_chiusura(bologna, [milano, roma]).endswith(
        " La bloccano anche Pat-Roma e Pat-Milano, protette, che senza la loro password non pagano: oltre la loro riserva hanno 700 euro e 600 euro.")
    # Con tutte le password la chiusura si fa, come prima.
    assert mondo.problema_chiusura(bologna) is None


def test_fondare_e_portare_via_il_capitale_non_annulla_la_fondazione():
    # Il ripensamento vuole la cassa ancora piena: chi sposta altrove il capitale della nuova non riavrà il capitale dopo.
    mondo = mondo_di_prova(20, 20)
    prima = mondo.fonda_polisportiva("Pat-Bologna")
    seconda = mondo.fonda_polisportiva("Pat-Milano")
    mondo.sposta_fondi(seconda, prima, mondo.spostabile(seconda))
    assert prima.cassa == 40_000 and seconda.cassa == 0 and mondo.giorni_del_ripensamento(seconda) is None
    mondo.chiudi_polisportiva(seconda)
    assert mondo.fondazioni_di_sempre == 2 and mondo.conto_della_fondazione().capitale == 0


# L'allenatore licenziato, quinta tranche.

def _frase_del_licenziamento(a, da, il_giorno, fino):
    return (f"{_nome(a)} è {testi.accorda(a, 'stato')} {testi.accorda(a, 'licenziato')} da {da} {testi.con_articolo('il', il_giorno)}: "
            f"firma con le tue polisportive soltanto {testi.con_articolo('dal', fino)}")


def test_l_allenatore_licenziato_non_firma_con_le_tue_per_30_giorni():
    mondo, _cpu, bologna, milano = _mondo()
    a = _con_lo_staff(mondo, bologna)
    assert testi.domanda_licenziamento(a, bologna, mondo).endswith(" Per 30 giorni non firmerà con nessuna delle tue polisportive.")
    buonuscita = mondo.licenzia_allenatore(bologna, a)
    assert a.libero and a.escluso_dall_utente_fino == OGGI + datetime.timedelta(days=30)
    assert testi.esito_licenziamento(a, bologna, buonuscita).endswith(" Firma con le tue polisportive soltanto dal 4 novembre 2026.")
    assert bologna.diario[0]["testo"].endswith(" Firma con le tue polisportive soltanto dal 4 novembre 2026.")
    frase = _frase_del_licenziamento(a, "Pat-Bologna", "5 ottobre 2026", "4 novembre 2026")
    assert mondo.licenziato_dall_utente(a) == frase
    # Nessuna tua polisportiva lo assume, nemmeno quella che l'ha licenziato.
    for poli in (milano, bologna):
        assert mondo.problema_assunzione(poli, a, 1, 0) == frase
        assert mondo.problema_offerta_allenatore(poli, a, 1) == f"{frase}."
        with pytest.raises(ValueError, match="firma con le tue polisportive soltanto dal"):
            mondo.assumi_allenatore(poli, a, 1)
    # Il mercato lo dice sulla riga e nella scheda, e l'offerta ha il suo perché, prima del posto e della cassa.
    riga = next(r for r in mercato.Memoria(mondo).righe_di(mercato.ALLENATORI) if r.persona is a)
    milano.staff = [99, 98, 97]
    milano.cassa = 0
    assert mercato.offerta_possibile(mondo, milano, riga) == (mercato.INGAGGIO_ALLENATORE, f"{frase}.", mercato.ALLENATORE_ESCLUSO)
    milano.staff = [0, 0, 0]
    milano.cassa = 8_000
    assert "firma con le tue polisportive soltanto dal 4 novembre 2026" in testi.riga_allenatore(a, mondo)
    assert f"\n{frase}.\n" in testi.scheda_allenatore(a, mondo)
    # Se il diario non ricorda più chi l'ha licenziato, la frase dice una tua polisportiva.
    diario = a.diario
    a.diario = []
    assert mondo.licenziato_dall_utente(a) == _frase_del_licenziamento(a, "una tua polisportiva", "5 ottobre 2026", "4 novembre 2026")
    a.diario = diario
    # Il ventinovesimo giorno ancora no, il trentesimo sì.
    mondo.datetime_corrente_simulazione = OGGI + datetime.timedelta(days=29)
    assert mondo.problema_assunzione(milano, a, 1, 0) == frase
    mondo.datetime_corrente_simulazione = OGGI + datetime.timedelta(days=30)
    assert mondo.licenziato_dall_utente(a) is None and mondo.problema_assunzione(milano, a, 1, 0) is None
    assert "firma con le tue" not in testi.riga_allenatore(a, mondo) and "firma con le tue" not in testi.scheda_allenatore(a, mondo)
    assert mercato.offerta_possibile(mondo, milano, riga).motivo is None
    mondo.assumi_allenatore(milano, a, 1)
    assert a.polisportiva == "Pat-Milano"


def test_le_date_del_licenziato_e_della_prelazione_dicono_dal_e_si_elidono():
    # Scoperte T3 e T8 della revisione dei rimedi di D40: il giorno della fine è già libero, e la frase dice soltanto dal,
    # non fino al; davanti all'8 e all'11 l'articolo si elide.
    mondo, _cpu, bologna, milano = _mondo()
    a = _con_lo_staff(mondo, bologna)
    mondo.datetime_corrente_simulazione = datetime.datetime(2026, 10, 9, 9, 0)
    buonuscita = mondo.licenzia_allenatore(bologna, a)
    assert mondo.licenziato_dall_utente(a) == (f"{_nome(a)} è {testi.accorda(a, 'stato')} {testi.accorda(a, 'licenziato')} da Pat-Bologna il 9 ottobre "
                                               "2026: firma con le tue polisportive soltanto dall'8 novembre 2026")
    assert testi.esito_licenziamento(a, bologna, buonuscita).endswith(" Firma con le tue polisportive soltanto dall'8 novembre 2026.")
    assert bologna.diario[0]["testo"].endswith(" Firma con le tue polisportive soltanto dall'8 novembre 2026.")
    assert "firma con le tue polisportive soltanto dall'8 novembre 2026" in testi.riga_allenatore(a, mondo)
    b = _con_lo_staff(mondo, bologna)
    mondo.datetime_corrente_simulazione = datetime.datetime(2026, 10, 11, 9, 0)
    mondo.licenzia_allenatore(bologna, b)
    assert mondo.licenziato_dall_utente(b).endswith(" da Pat-Bologna l'11 ottobre 2026: firma con le tue polisportive soltanto dal 10 novembre 2026")
    # La prelazione di un'altra polisportiva, che finisce l'8 dicembre: da quel giorno la assumono anche le altre.
    c = mondo._nasce_un_allenatore(OGGI)
    c.prelazione, c.prelazione_fino = "Pat-Roma", datetime.datetime(2026, 12, 8, 9, 0)
    lo = "assumerla" if c.sesso == "f" else "assumerlo"
    assert mondo.problema_assunzione(milano, c, 1, 0) == f"{_nome(c)} può {lo} soltanto Pat-Roma, e le altre polisportive soltanto dall'8 dicembre 2026"


def test_il_computer_assume_subito_e_la_chiusura_non_licenzia():
    mondo, cpu, bologna, milano = _mondo()
    a = _con_lo_staff(mondo, bologna)
    mondo.licenzia_allenatore(bologna, a)
    # Il computer lo vede e lo assume subito, come prima.
    assert mondo._visibile_al_computer(a) and mondo.problema_assunzione(cpu, a, 0, 0) is None
    mondo.assumi_allenatore(cpu, a, 0, OGGI)
    assert a.polisportiva == cpu.nome
    # Se poi lo licenzia anche il computer, i 30 giorni dell'utente restano; chi licenzia soltanto il computer non è tenuto
    # lontano dalle tue polisportive.
    mondo.licenzia_allenatore(cpu, a)
    assert a.escluso_dall_utente_fino == OGGI + datetime.timedelta(days=30) and mondo.licenziato_dall_utente(a)
    b = _con_lo_staff(mondo, cpu)
    mondo.licenzia_allenatore(cpu, b)
    assert b.escluso_dall_utente_fino is None and mondo.problema_assunzione(milano, b, 0, 0) is None
    # Lo staff che se ne va per la chiusura di una tua polisportiva non è licenziato.
    roma = polisportiva(mondo, "Pat-Roma", cpu=False, cassa=20_000)
    c = _con_lo_staff(mondo, roma)
    mondo.chiudi_polisportiva(roma)
    assert c.libero and c.escluso_dall_utente_fino is None and mondo.problema_assunzione(bologna, c, 0, 0) is None


# La rampa del prezzo al posto dei dodici mesi, e il valore senza il rinnovo concordato.

def _dopo(giorni, ora=9, minuto=0):
    """Il giorno che viene tanti giorni dopo OGGI, all'ora data."""
    return (OGGI + datetime.timedelta(days=giorni)).replace(hour=ora, minute=minuto)


def test_la_rampa_del_prezzo_sale_da_quello_pagato_al_valore_pieno():
    mondo, cpu, bologna, _milano = _mondo()
    cpu.cassa = 1_000_000
    g = mondo.giocatori[9]
    # Un contratto più lungo della rampa, così il valore pieno resta lo stesso fino alla fine.
    g.contratto_scadenza = contratti.aggiungi_mesi(OGGI, MESI_DELLA_RAMPA + 6)
    # Dalle scelte di Gabriele del 3 novembre 2026 la rampa parte da quello che la polisportiva ha pagato alla firma: qui
    # 50 euro più dell'ingaggio che il giocatore chiede oggi, e la rampa dura 36 mesi.
    partenza = economia.ingaggio_richiesto(g, bologna) + 50
    g.pagato_alla_firma = partenza
    pieno = economia.tetto_pieno_di_rivendita(g, bologna, OGGI)
    fine = contratti.stesso_giorno_dopo(OGGI, MESI_DELLA_RAMPA)
    giorni = (fine - OGGI).days
    assert MESI_DELLA_RAMPA == 36 and fine == datetime.datetime(2029, 10, 5, 9, 0)
    assert g.tesserato_dal == OGGI and pieno == round(economia.valore_di_mercato(g, OGGI, col_rinnovo=False) * RIALZO_CPU) and partenza < pieno
    # Il giorno della firma il computer paga al più quello che è costato, poi il tetto sale in linea retta, giorno per giorno.
    assert economia.tetto_di_rivendita(g, bologna, OGGI) == partenza and economia.rivendita_piena_dal(g, bologna, OGGI) == fine
    meta = giorni // 2
    assert economia.tetto_di_rivendita(g, bologna, _dopo(meta)) == partenza + (pieno - partenza) * meta // giorni
    # Il giorno prima della fine il tetto non è ancora pieno; il giorno esatto, dalla mezzanotte, sì.
    vigilia = _dopo(giorni - 1, 23, 59)
    assert economia.tetto_di_rivendita(g, bologna, vigilia) < pieno and economia.rivendita_piena_dal(g, bologna, vigilia) == fine
    mattina = _dopo(giorni, 0, 1)
    assert economia.tetto_di_rivendita(g, bologna, mattina) == pieno and economia.rivendita_piena_dal(g, bologna, mattina) is None
    assert economia.tetto_di_rivendita(g, bologna, _dopo(giorni + 30)) == pieno
    # Il computer compra al tetto del giorno, non sopra: un euro oltre la partenza lo compra dal primo giorno in cui il tetto ci
    # arriva, e la firma col computer è di quel giorno, col prezzo che ha pagato.
    prezzo = partenza + 1
    assert mondo.problema_vendita(bologna, g, prezzo) is None
    mondo.metti_in_vendita(bologna, g, prezzo)
    assert [(riga[0], riga[3]) for riga in mondo._vendibili(OGGI)] == [(g, partenza)] and not mondo._compra_dal_mercato(cpu, OGGI)
    primo = -(-giorni // (pieno - partenza))
    dal = economia.rivendita_al_prezzo_dal(g, bologna, prezzo, OGGI)
    assert dal == OGGI + datetime.timedelta(days=primo) and economia.rivendita_al_prezzo_dal(g, bologna, partenza, OGGI) == OGGI
    assert economia.rivendita_al_prezzo_dal(g, bologna, pieno, OGGI) == fine and economia.rivendita_al_prezzo_dal(g, bologna, pieno + 1, OGGI) is None
    giorno_prima = _dopo(primo - 1)
    assert economia.tetto_di_rivendita(g, bologna, giorno_prima) == partenza and not mondo._compra_dal_mercato(cpu, giorno_prima)
    assert g.appartenenza == bologna.nome and cpu.movimenti_oggi == 0
    assert economia.tetto_di_rivendita(g, bologna, dal) >= prezzo and economia.rivendita_al_prezzo_dal(g, bologna, prezzo, dal) == dal
    assert mondo._compra_dal_mercato(cpu, dal)
    assert g.appartenenza == cpu.nome and g.tesserato_dal == dal and g.pagato_alla_firma == prezzo and bologna.cassa == 20_000 + prezzo
    # Il computer non ha rampa: per lui il tetto è subito pieno, anche col prezzo appena pagato.
    assert economia.rivendita_piena_dal(g, cpu, dal) is None
    # Lo stesso giorno del mese, o l'ultimo se quel giorno non c'è.
    assert contratti.stesso_giorno_dopo(datetime.datetime(2028, 2, 29, 9, 0), 12) == datetime.datetime(2029, 2, 28, 9, 0)
    assert contratti.stesso_giorno_dopo(datetime.datetime(2027, 1, 31), 1) == datetime.datetime(2027, 2, 28)
    assert contratti.stesso_giorno_dopo(datetime.datetime(2027, 3, 31), -1) == datetime.datetime(2027, 2, 28)


def test_chi_ha_firmato_prima_del_formato_11_vale_subito_il_tetto_pieno():
    mondo, cpu, bologna, _milano = _mondo()
    cpu.cassa = 1_000_000
    g = mondo.giocatori[10]
    # La migrazione dal formato 10 lascia vuoto il giorno della firma: il computer lo paga subito al tetto pieno.
    g.tesserato_dal = None
    pieno = economia.tetto_pieno_di_rivendita(g, bologna, OGGI)
    assert economia.tetto_di_rivendita(g, bologna, OGGI) == pieno and economia.rivendita_piena_dal(g, bologna, OGGI) is None
    assert testi.rivendita(g, bologna, OGGI) == "" and testi.rivendita(g, bologna, OGGI, anche_pieno=True) == f"il computer lo paga fino a {_euro(pieno)}"
    assert economia.rivendita_al_prezzo_dal(g, bologna, pieno, OGGI) == OGGI and economia.rivendita_al_prezzo_dal(g, bologna, pieno + 1, OGGI) is None
    mondo.metti_in_vendita(bologna, g, pieno)
    assert [(riga[0], riga[3]) for riga in mondo._vendibili(OGGI)] == [(g, pieno)]
    assert mondo._compra_dal_mercato(cpu, OGGI) and g.appartenenza == cpu.nome and g.tesserato_dal == OGGI


def test_la_partenza_sopra_il_tetto_pieno_vale_il_tetto_pieno():
    mondo, _cpu, bologna, _milano = _mondo()
    g = mondo.giocatori[11]
    # Pagato quanto il tetto pieno, o di più, il computer lo paga da subito al tetto pieno; un euro sotto, la rampa c'è.
    pieno = economia.tetto_pieno_di_rivendita(g, bologna, OGGI)
    for pagato in (pieno, pieno + 500):
        g.pagato_alla_firma = pagato
        assert economia.tetto_di_rivendita(g, bologna, OGGI) == pieno and economia.rivendita_piena_dal(g, bologna, OGGI) is None
    g.pagato_alla_firma = pieno - 1
    assert economia.tetto_di_rivendita(g, bologna, OGGI) == pieno - 1 and economia.rivendita_piena_dal(g, bologna, OGGI) is not None
    # Senza quello pagato vale l'ingaggio di oggi. Un contratto che scade oggi, al 40% del valore, e una polisportiva senza
    # gloria, a cui il giocatore chiede l'ingaggio più alto: la partenza della rampa supera il tetto pieno, e vale il tetto
    # pieno da subito.
    g.pagato_alla_firma = None
    g.contratto_scadenza = OGGI
    bologna.gloria = 1
    pieno = economia.tetto_pieno_di_rivendita(g, bologna, OGGI)
    assert g.tesserato_dal == OGGI and economia.ingaggio_richiesto(g, bologna) > pieno
    assert economia.tetto_di_rivendita(g, bologna, OGGI) == pieno and economia.rivendita_piena_dal(g, bologna, OGGI) is None
    assert testi.rivendita(g, bologna, OGGI) == "" and testi.riga_vendita(g, bologna, OGGI).endswith(f", il computer lo paga fino a {_euro(pieno)}")


def test_il_computer_fra_se_compra_come_prima():
    mondo, cpu, _bologna, _milano = _mondo()
    altra = polisportiva(mondo, "PoliTeam02 Prova", ids=(5, 6))
    altra.cassa = 1_000_000
    g = mondo.giocatori[1]
    # Firmato oggi, e con un rinnovo concordato a meno di un mese dalla scadenza: fra le polisportive del computer il
    # giorno della firma non conta, e il rinnovo tiene pieno il valore, come prima.
    g.contratto_scadenza = contratti.aggiungi_mesi(OGGI, 1)
    contratti.concorda_rinnovo(g, economia.stipendio(g), 12)
    pieno = economia.valore_di_mercato_pieno(g)
    assert g.tesserato_dal == OGGI and economia.rivendita_piena_dal(g, cpu, OGGI) is None and testi.rivendita(g, cpu, OGGI, anche_pieno=True) == ""
    assert economia.tetto_di_rivendita(g, cpu, OGGI) == round(pieno * RIALZO_CPU) and testi.sopra_il_tetto(g, cpu, 10 * pieno, OGGI) == ""
    mondo.metti_in_vendita(cpu, g, pieno)
    assert [(riga[0], riga[3]) for riga in mondo._vendibili(OGGI)] == [(g, pieno * RIALZO_CPU)]
    assert mondo._compra_dal_mercato(altra, OGGI) and g.appartenenza == altra.nome


def test_il_valore_della_tua_vendita_non_conta_il_rinnovo_concordato():
    mondo, cpu, bologna, _milano = _mondo()
    cpu.cassa = 1_000_000
    g = mondo.giocatori[9]
    _firmati_a_rampa_finita(g)
    g.contratto_scadenza = contratti.aggiungi_mesi(OGGI, 1)
    pieno = economia.valore_di_mercato_pieno(g)
    senza = economia.valore_di_mercato(g, OGGI)
    assert senza < pieno
    contratti.concorda_rinnovo(g, economia.stipendio(g), 12)
    # Il rinnovo concordato tiene pieno il valore di mercato, ma non quello di una tua vendita: il compratore lo annulla.
    assert economia.valore_di_mercato(g, OGGI) == pieno and economia.valore_di_mercato(g, OGGI, col_rinnovo=False) == senza
    assert economia.fattore_scadenza(g, OGGI) == 1.0 and economia.fattore_scadenza(g, OGGI, col_rinnovo=False) < 1.0
    mondo.metti_in_vendita(bologna, g, pieno)
    tetto = economia.tetto_di_rivendita(g, bologna, OGGI)
    assert [riga[3] for riga in mondo._vendibili(OGGI)] == [tetto] and tetto == round(senza * RIALZO_CPU)
    assert not mondo._compra_dal_mercato(cpu, OGGI) and g.appartenenza == bologna.nome
    # Le Vendite dicono il valore che il computer paga, e il tetto da cui partono.
    assert testi.riga_vendita(g, bologna, OGGI) == (f"{_nome(g)}, valore {testi.numero(g.indice_collettivo_valore)}, "
                                                   f"stipendio {_euro(economia.stipendio_pagato(g))}, valore di mercato {_euro(senza)}, "
                                                   f"senza il rinnovo concordato, in vendita a {_euro(pieno)}, il computer lo paga fino a {_euro(tetto)}")
    mondo.metti_in_vendita(bologna, g, tetto)
    assert mondo._compra_dal_mercato(cpu, OGGI) and g.appartenenza == cpu.nome and g.rinnovo_scadenza is None


def _fino_al_pieno(lui, g, poli, oggi=OGGI):
    """La frase della rampa, a metà riga: il computer oggi lo paga fino a 2.300 euro, il valore pieno dal 5 ottobre 2028."""
    fine = testi.con_articolo("dal", testi.data_breve(contratti.stesso_giorno_dopo(g.tesserato_dal, MESI_DELLA_RAMPA)))
    return f"il computer oggi {lui} paga fino a {_euro(economia.tetto_di_rivendita(g, poli, oggi))}, il valore pieno {fine}"


def test_vendite_mercato_e_scheda_dicono_il_tetto_di_oggi():
    mondo, cpu, bologna, milano = _mondo()
    g, lei = mondo.giocatori[9], mondo.giocatori[25]
    # Il tetto di oggi, il giorno della firma, è quello che la polisportiva ha pagato.
    g.pagato_alla_firma = economia.ingaggio_richiesto(g, bologna) // 2
    tetto = economia.tetto_di_rivendita(g, bologna, OGGI)
    assert tetto == g.pagato_alla_firma > 0
    frase = f"il computer oggi lo paga fino a {_euro(tetto)}, il valore pieno dal {testi.data_breve(contratti.stesso_giorno_dopo(OGGI, MESI_DELLA_RAMPA))}"
    assert frase.endswith(", il valore pieno dal 5 ottobre 2029")
    assert testi.rivendita(g, bologna, OGGI) == frase == _fino_al_pieno("lo", g, bologna)
    assert testi.avviso_di_rivendita(lei, bologna, OGGI) == f"{_fino_al_pieno('la', lei, bologna)[0].upper()}{_fino_al_pieno('la', lei, bologna)[1:]}."
    assert testi.riga_vendita(g, bologna, OGGI).endswith(f"valore di mercato {_euro(economia.valore_di_mercato(g, OGGI))}, {frase}")
    mondo.metti_in_vendita(bologna, g, 700)
    assert testi.riga_vendita(g, bologna, OGGI).endswith(f", in vendita a 700 euro, {frase}")
    # La riga del mercato lo dice per i tuoi in vendita, da qualunque tua polisportiva, e la scheda anche; chi non è in
    # vendita non ne ha bisogno.
    mondo.metti_in_vendita(milano, mondo.giocatori[28], 300)
    righe = {r.persona.id: r for r in mercato.Memoria(mondo).righe_di(mercato.GIOCATORI)}
    assert f"tuo, in vendita da Pat-Bologna a 700 euro, {frase}" in testi.riga_trovato(righe[9], mondo)
    assert f"tua, in vendita da Pat-Milano a 300 euro, {_fino_al_pieno('la', mondo.giocatori[28], milano)}" in testi.riga_trovato(righe[28], mondo)
    assert "paga fino" not in testi.riga_trovato(righe[10], mondo)
    assert f"In vendita a 700 euro. {frase[0].upper()}{frase[1:]}." in testi.scheda_giocatore(g, mondo)
    # A rampa finita, senza il giorno della firma e per i giocatori del computer, niente frase; le Vendite dicono soltanto
    # il tetto pieno.
    fine = contratti.stesso_giorno_dopo(OGGI, MESI_DELLA_RAMPA)
    pieno = economia.tetto_pieno_di_rivendita(g, bologna, fine)
    assert testi.rivendita(g, bologna, fine) == "" and testi.riga_vendita(g, bologna, fine).endswith(f", in vendita a 700 euro, il computer lo paga fino a {_euro(pieno)}")
    mondo.metti_in_vendita(cpu, mondo.giocatori[1], 500)
    assert testi.rivendita(mondo.giocatori[1], cpu, OGGI) == "" and "In vendita a 500 euro." in testi.scheda_giocatore(mondo.giocatori[1], mondo)
    assert "paga fino" not in testi.riga_vendita(mondo.giocatori[1], cpu, OGGI)
    g.tesserato_dal = None
    assert "In vendita a 700 euro.\n" in testi.scheda_giocatore(g, mondo) + "\n"
    assert testi.riga_vendita(g, bologna, OGGI).endswith(f", il computer lo paga fino a {_euro(economia.tetto_pieno_di_rivendita(g, bologna, OGGI))}")


def test_l_esito_di_un_prezzo_sopra_il_tetto_dice_da_quando_il_computer_compra():
    mondo, _cpu, bologna, _milano = _mondo()
    g, lei = mondo.giocatori[9], mondo.giocatori[25]
    tetto = economia.tetto_di_rivendita(g, bologna, OGGI)
    pieno = economia.tetto_pieno_di_rivendita(g, bologna, OGGI)
    # Fino al tetto di oggi l'esito non ha avvisi.
    assert testi.sopra_il_tetto(g, bologna, tetto, OGGI) == ""
    assert testi.messo_in_vendita(g, bologna, tetto, OGGI) == f"{_nome(g)} è in vendita a {_euro(tetto)}."
    # Sopra il tetto, fino al tetto pieno, il giorno in cui la rampa arriva al prezzo, con l'articolo eliso se serve.
    prezzo = (tetto + pieno) // 2
    dal = economia.rivendita_al_prezzo_dal(g, bologna, prezzo, OGGI)
    assert OGGI < dal < contratti.stesso_giorno_dopo(OGGI, MESI_DELLA_RAMPA)
    avviso = f"Il computer oggi lo paga fino a {_euro(tetto)}: a questo prezzo lo comprerà {testi.con_articolo('dal', testi.data_breve(dal))}."
    assert testi.sopra_il_tetto(g, bologna, prezzo, OGGI) == avviso
    assert testi.messo_in_vendita(g, bologna, prezzo, OGGI) == f"{_nome(g)} è in vendita a {_euro(prezzo)}. {avviso}"
    # Sopra il tetto pieno il computer, col valore di oggi, non lo compra.
    assert testi.sopra_il_tetto(lei, bologna, 10 * pieno, OGGI) == (f"Il computer la paga al più {_euro(economia.tetto_pieno_di_rivendita(lei, bologna, OGGI))}, "
                                                                 "a valore pieno: a questo prezzo, col valore di oggi, non la comprerà.")
    # Anche a rampa finita, o senza il giorno della firma, un prezzo sopra il tetto pieno ha il suo avviso.
    g.tesserato_dal = None
    assert testi.sopra_il_tetto(g, bologna, pieno, OGGI) == ""
    assert testi.messo_in_vendita(g, bologna, pieno + 1, OGGI) == (f"{_nome(g)} è in vendita a {_euro(pieno + 1)}. Il computer lo paga al più "
                                                                   f"{_euro(pieno)}, a valore pieno: a questo prezzo, col valore di oggi, non lo comprerà.")
    # Le date con l'articolo eliso: chi ha firmato l'8 settembre ha il valore pieno dall'8 settembre, MESI_DELLA_RAMPA mesi dopo.
    lei.tesserato_dal = datetime.datetime(2026, 9, 8, 9, 0)
    fine = contratti.stesso_giorno_dopo(lei.tesserato_dal, MESI_DELLA_RAMPA)
    assert testi.rivendita(lei, bologna, OGGI).endswith(f", il valore pieno dall'8 settembre {fine.year}")


# Da dove parte la rampa, scelte di Gabriele del 3 novembre 2026: da quello che la polisportiva ha pagato alla firma.

def _contratto_oltre_la_rampa(g):
    """Un contratto più lungo della rampa, così il valore pieno resta lo stesso per tutta la rampa."""
    g.contratto_scadenza = contratti.aggiungi_mesi(OGGI, MESI_DELLA_RAMPA + 6)


def _tetto_atteso(partenza, pieno, passati):
    """Il tetto della rampa tanti giorni dopo una firma di OGGI: in linea retta dalla partenza al tetto pieno, coi numeri interi."""
    giorni = (contratti.stesso_giorno_dopo(OGGI, MESI_DELLA_RAMPA) - OGGI).days
    return partenza + (pieno - partenza) * passati // giorni


def test_la_rampa_del_libero_parte_dall_ingaggio_pagato_sotto_o_sopra_il_chiesto(monkeypatch):
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: True)
    mondo, _cpu, bologna, _milano = _mondo()
    liberi = [g for g in mondo.giocatori.values() if g.appartenenza == "*"
              and economia.ingaggio_richiesto(g, bologna) + 100 < round(economia.valore_di_mercato_pieno(g) * RIALZO_CPU)]
    sotto, sopra = liberi[:2]
    fine = contratti.stesso_giorno_dopo(OGGI, MESI_DELLA_RAMPA)
    for g, offerta in ((sotto, economia.ingaggio_richiesto(sotto, bologna) // 2), (sopra, economia.ingaggio_richiesto(sopra, bologna) + 100)):
        chiesto = economia.ingaggio_richiesto(g, bologna)
        accetta, _probabilita = mondo.offerta(bologna, g, offerta)
        assert accetta and g.appartenenza == bologna.nome and g.pagato_alla_firma == offerta != chiesto
        _contratto_oltre_la_rampa(g)
        pieno = economia.tetto_pieno_di_rivendita(g, bologna, OGGI)
        # Il giorno della firma il computer paga al più l'ingaggio pagato davvero, non quello chiesto; poi la rampa sale.
        assert economia.tetto_di_rivendita(g, bologna, OGGI) == offerta < pieno and economia.rivendita_piena_dal(g, bologna, OGGI) == fine
        assert economia.tetto_di_rivendita(g, bologna, _dopo(400)) == _tetto_atteso(offerta, pieno, 400)
    # L'ingaggio che il giocatore chiederebbe oggi cambia con la gloria della polisportiva; la partenza resta quella pagata.
    prima = economia.ingaggio_richiesto(sopra, bologna)
    bologna.gloria = 1
    assert economia.ingaggio_richiesto(sopra, bologna) != prima
    assert economia.tetto_di_rivendita(sopra, bologna, OGGI) == sopra.pagato_alla_firma


def test_la_rampa_di_un_acquisto_dal_computer_parte_dal_prezzo():
    mondo, cpu, bologna, _milano = _mondo()
    bologna.cassa = 1_000_000
    sotto, sopra = mondo.giocatori[1], mondo.giocatori[2]
    pieni = {g.id: round(economia.valore_di_mercato_pieno(g) * RIALZO_CPU) for g in (sotto, sopra)}
    # Al prezzo chiesto dal computer, sotto il tetto pieno: la rampa parte dal prezzo pagato.
    prezzo = pieni[sotto.id] // 2
    mondo.metti_in_vendita(cpu, sotto, prezzo)
    assert mondo.acquista(bologna, sotto) == prezzo
    _contratto_oltre_la_rampa(sotto)
    assert sotto.appartenenza == bologna.nome and sotto.tesserato_dal == OGGI and sotto.pagato_alla_firma == prezzo
    assert economia.tetto_pieno_di_rivendita(sotto, bologna, OGGI) == pieni[sotto.id]
    assert economia.tetto_di_rivendita(sotto, bologna, OGGI) == prezzo and economia.rivendita_piena_dal(sotto, bologna, OGGI) == contratti.stesso_giorno_dopo(OGGI, MESI_DELLA_RAMPA)
    assert economia.tetto_di_rivendita(sotto, bologna, _dopo(200)) == _tetto_atteso(prezzo, pieni[sotto.id], 200)
    # Sopra il tetto pieno la rampa non c'è: il computer lo ricompra da subito al tetto pieno, e non oltre.
    mondo.metti_in_vendita(cpu, sopra, pieni[sopra.id] + 500)
    assert mondo.acquista(bologna, sopra) == pieni[sopra.id] + 500 == sopra.pagato_alla_firma
    assert economia.tetto_di_rivendita(sopra, bologna, OGGI) == pieni[sopra.id] and economia.rivendita_piena_dal(sopra, bologna, OGGI) is None


def test_l_offerta_d_acquisto_accettata_e_la_partenza_della_rampa():
    mondo, cpu, bologna, _milano = _mondo()
    bologna.cassa = 1_000_000
    # Il più debole della rosa del computer: la soglia di vendita è il suo valore di mercato, sotto il tetto pieno.
    g = min((mondo.giocatori[gid] for gid in cpu.tesserati), key=lambda g: g.indice_collettivo_valore)
    offerta = mondo.soglia_di_vendita(cpu, g) + 30
    assert mondo.offerta_d_acquisto(bologna, g, offerta)
    _contratto_oltre_la_rampa(g)
    pieno = economia.tetto_pieno_di_rivendita(g, bologna, OGGI)
    assert g.appartenenza == bologna.nome and g.pagato_alla_firma == offerta < pieno
    assert economia.tetto_di_rivendita(g, bologna, OGGI) == offerta and economia.tetto_di_rivendita(g, bologna, _dopo(300)) == _tetto_atteso(offerta, pieno, 300)


def test_chi_esce_non_ricorda_piu_quello_che_era_costato(monkeypatch):
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: True)
    mondo, _cpu, bologna, milano = _mondo()
    g = mondo.giocatori[5]
    assert g.appartenenza == "*" and g.pagato_alla_firma is None
    assert mondo.offerta(bologna, g, 777)[0] and g.pagato_alla_firma == 777
    # Lo svincolo lo dimentica, col giorno della firma; la firma nuova ricorda l'ingaggio nuovo.
    mondo.svincola(bologna, g)
    assert g.appartenenza == "*" and g.pagato_alla_firma is None and g.tesserato_dal is None
    assert mondo.offerta(milano, g, 555)[0] and g.pagato_alla_firma == 555


def test_senza_quello_pagato_la_rampa_parte_dall_ingaggio_di_oggi():
    mondo, _cpu, bologna, _milano = _mondo()
    g = mondo.giocatori[10]
    # Entrato senza pagare, come chi ha firmato nel formato 11 prima del cambio: la rampa parte dall'ingaggio che chiede oggi.
    assert g.tesserato_dal == OGGI and g.pagato_alla_firma is None
    _contratto_oltre_la_rampa(g)
    pieno = economia.tetto_pieno_di_rivendita(g, bologna, OGGI)
    chiesto = economia.ingaggio_richiesto(g, bologna)
    assert economia.partenza_della_rampa(g, bologna) == chiesto == economia.tetto_di_rivendita(g, bologna, OGGI) < pieno
    assert economia.rivendita_piena_dal(g, bologna, OGGI) == contratti.stesso_giorno_dopo(OGGI, MESI_DELLA_RAMPA)
    # È l'ingaggio di oggi: con un'altra gloria cambia, e la rampa con lui.
    bologna.gloria = 1
    oggi = economia.ingaggio_richiesto(g, bologna)
    assert oggi != chiesto and economia.tetto_di_rivendita(g, bologna, OGGI) == min(oggi, pieno)
