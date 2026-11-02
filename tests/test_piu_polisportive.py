"""
Le prove delle regole fra più polisportive dell'utente, decisione D40 del 2 novembre 2026. La prima tranche, le regole che
non chiedono campi nuovi nel salvataggio: fra le tue polisportive i giocatori non si vendono, e al computer sì; la riserva;
lo svincolo e la vendita che saldano gli arretrati, col computer che non compra quando i soldi non bastano; la chiusura che
salda tutto, con le altre tue polisportive oltre la loro riserva, dalla più ricca, e che non si fa quando non basta, dicendo
chi la blocca; i convocati delle sfide accettate e le rose della Coppa, fermi sul mercato fino alla partita, che escono
dalla vendita, e la rosa che non entra in due polisportive della stessa coppa. Il computer resta com'era.
La seconda tranche, lo sponsor delle tue polisportive, che paga la gloria per i tesserati in attività su 15: la stessa
cifra nei conti del mese, nella barra, nella scheda, nel bilancio e nei contratti, e le frasi della rosa non piena.
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
import sfide
import testi
from costanti import FEDELTA_BANDIERA, QUOTA_SPONSOR_SUL_VALORE, SPONSOR_PER_GLORIA
from mondo import VENDITA_FRA_TUE, Mondo, _Mercato
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
    # Al computer la vendita resta com'era.
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
    domanda = testi.domanda_svincolo(g, bologna, mondo)
    assert f"la buonuscita è di {_euro(buonuscita)}. Lo svincolo salda anche i 1.020 euro di arretrati che aspetta. " in domanda
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
    assert mondo.problema_svincolo(cpu, tesserato_cpu) is None


def test_la_vendita_dell_utente_salda_tutti_gli_arretrati():
    mondo, cpu, bologna, _milano = _mondo()
    g = mondo.giocatori[10]
    g.arretrati = 1500
    bologna.cassa = 300
    assert mondo.arretrati_scoperti(bologna, g, 1000) == 200
    atteso = f"A 1.000 euro mancano 200 euro: la vendita salda i 1.500 euro di arretrati di {_nome(g)}, prima dal prezzo e poi dalla cassa di Pat-Bologna, che ne ha 300 euro."
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
        f"Pat-Bologna ha chiuso per sempre: 6 giocatori tornano liberi. Ha saldato {_euro(costo)} di debiti, con l'aiuto di Pat-Roma 700 euro e Pat-Milano 300 euro. ")


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
    return (f"{_nome(g)} è {testi.accorda(g, 'convocato')} nella sfida del {testi.data_breve(giorno_del_gioco)}: fino alla partita non si vende, "
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
    # Una sfida proposta non ferma nessuno.
    s.stato = sfide.PROPOSTA
    assert sfide.convocazioni(mondo) == {} and sfide.impegno_di_squadra(mondo, mondo.giocatori[9]) is None


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
