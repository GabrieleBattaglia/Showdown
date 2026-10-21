"""
Test delle sfide fra polisportive, della gara a squadre nella carriera e della Coppa delle polisportive, tappa 12, punto 8 del progetto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Due sfide al mese fino a quattro; la decaduta e la rifiutata che non consumano; la convocazione con il
due più uno e le riserve; la formazione cambiata e quella non valida; il computer che accetta e che
rifiuta per la forbice, il riposo e la squadra, ciascuno col suo motivo; la sfida tua che decade dopo
un giorno; quella accettata giocata il giorno dopo, con i convocati che l'iscrizione automatica non
manda a un torneo quel giorno; chi ha giocato un torneo quel giorno non convocato; la polisportiva
chiusa; la registrazione nella carriera, con le riserve a metà dell'esperienza e senza punti
allenamento; le coppe e la fedeltà; il tavolino; i lanci del computer; la coppa con la
qualificazione per gloria, la rosa iscritta, la sostituzione di chi chiude e le coppe ai primi
quattro; il gemello della gara a squadre uguale al registrato. La finestra dal vivo della gara a
squadre è del passo 3.
"""

import datetime
import random

import pytest
from aiuti_calendario import OGGI, apri, giorno, mondo_di_prova, polisportiva, solo

import classe
import esito_rapido
import esperienza
import iscrizioni
import modelli_torneo
import palmares
import premiazioni
import sfide
import testi
import tornei
from costanti import (
    ESPERIENZA_MASSIMA,
    ESPERIENZA_PER_FASE_SUPERATA,
    ESPERIENZA_PER_SFIDA,
    ESPERIENZA_RISERVA_QUOTA,
    FATICA_RESIDUA_GIORNATA,
    FEDELTA_MASSIMA,
    FEDELTA_PER_MEDAGLIA,
    IMPORTANZA_COPPA_SFIDA,
    PA_FATTORE_SFIDA,
    PA_PARTITA_BASE,
    PA_PER_SET_VINTO,
    PA_VITTORIA,
    QUOTA_GLORIA_ARGENTO_SFIDA,
)
from mondo import Mondo
from motore import Squadra
from partita import MotorePartita, gemello_da_differita
from staff import FATTORI_SENZA_STAFF

DOMANI = OGGI + datetime.timedelta(days=1)


def _mondo():
    """
    Un mondo con tre polisportive: due del computer, A coi giocatori da 1 a 4 e da 21 a 22, B da 5 a 8
    e da 23 a 24, e la tua, C, da 9 a 11 e da 25 a 27. Uomini da 1 a 20, donne da 21 a 40.
    """
    mondo = mondo_di_prova(20, 20)
    a = polisportiva(mondo, "PoliTeam01 Prova", ids=(1, 2, 3, 4, 21, 22))
    b = polisportiva(mondo, "PoliTeam02 Prova", ids=(5, 6, 7, 8, 23, 24))
    c = polisportiva(mondo, "Club Di Prova", cpu=False, cassa=1000, ids=(9, 10, 11, 25, 26, 27))
    return mondo, a, b, c


@pytest.fixture
def quieta(monkeypatch):
    """Il computer non lancia sfide da sé: le prove guardano soltanto quelle che preparano."""
    monkeypatch.setattr(sfide, "PROB_LANCIO_SFIDA_CPU", 0)


@pytest.fixture
def larga(monkeypatch, quieta):
    """Ogni polisportiva accetta qualunque rapporto di forza, e il computer non lancia sfide da sé."""
    monkeypatch.setattr(sfide, "forbice", lambda _nome: (0.0, 99.0))


def test_due_al_mese_fino_a_quattro():
    mondo, a, b, c = _mondo()
    assert (a.sfide_da_lanciare, c.sfide_da_lanciare) == (2, 2)
    a.sfide_da_lanciare = 3
    primo = datetime.datetime(2026, 11, 1, 9, 0)
    mondo._primo_del_mese(primo, Mondo.rapporto_vuoto(primo))
    assert (a.sfide_da_lanciare, b.sfide_da_lanciare, c.sfide_da_lanciare) == (4, 4, 4)
    mondo._primo_del_mese(primo, Mondo.rapporto_vuoto(primo))
    assert a.sfide_da_lanciare == 4


def test_la_convocazione_con_il_due_piu_uno_e_le_riserve():
    mondo, a, _b, _c = _mondo()
    convocati = sfide.convoca(mondo, a, OGGI)
    assert len(convocati) == 6 and sorted(g.id for g in convocati) == [1, 2, 3, 4, 21, 22]
    sessi = [g.sesso for g in convocati[:3]]
    assert sessi.count("m") in (1, 2)
    # Tre uomini migliori di tutte: il terzo cede il posto alla migliore donna e diventa la prima riserva.
    for gid in (1, 2, 3):
        mondo.giocatori[gid].esperienza = 20.0
    uomini = sorted((mondo.giocatori[gid] for gid in (1, 2, 3)), key=lambda g: (-classe.punteggio(g), g.id))
    donne = sorted((mondo.giocatori[21], mondo.giocatori[22]), key=lambda g: (-classe.punteggio(g), g.id))
    convocati = sfide.convoca(mondo, a, OGGI)
    assert convocati[:4] == [uomini[0], uomini[1], donne[0], uomini[2]]
    # Senza donne disponibili la squadra non c'è.
    for gid in (21, 22):
        mondo.giocatori[gid].infortunato = True
    assert sfide.convoca(mondo, a, OGGI) is None


def test_chi_ha_un_impegno_quel_giorno_non_si_convoca():
    mondo, a, _b, _c = _mondo()
    mondo.giocatori[1].ultimo_impegno = OGGI
    assert 1 not in [g.id for g in sfide.convoca(mondo, a, OGGI)]
    assert 1 in [g.id for g in sfide.convoca(mondo, a, DOMANI)]
    # Chi gioca un torneo in corso quel giorno non si convoca.
    edizioni = apri(mondo, OGGI, "Open maschile del martedì")
    edizioni[0].aggiungi(2, iscrizioni.club_di(mondo, mondo.giocatori[2]), 0, iscrizioni.COMPUTER)
    assert 2 not in [g.id for g in sfide.convoca(mondo, a, DOMANI)] and 2 in [g.id for g in sfide.convoca(mondo, a, OGGI)]


def test_la_formazione_cambiata_e_quella_non_valida():
    mondo, _a, _b, c = _mondo()
    assert sfide.problema_formazione(mondo, c, [9, 10, 25, 11], DOMANI) is None
    assert sfide.problema_formazione(mondo, c, [9, 10], DOMANI) == "Servono tre titolari."
    assert "due volte" in sfide.problema_formazione(mondo, c, [9, 9, 25], DOMANI)
    assert "uno dell'altro" in sfide.problema_formazione(mondo, c, [9, 10, 11, 25], DOMANI)
    assert "non è un tesserato" in sfide.problema_formazione(mondo, c, [9, 10, 1], DOMANI)
    mondo.giocatori[25].infortunato = True
    assert "infortunata" in sfide.problema_formazione(mondo, c, [9, 10, 25], DOMANI)
    assert sfide.proposta(mondo, c)[:3] and 25 not in sfide.proposta(mondo, c)


def test_il_computer_accetta_o_rifiuta_col_suo_motivo():
    mondo, a, _b, _c = _mondo()
    propria = sfide.forza_squadra(sfide.convoca(mondo, a, DOMANI))
    basso, alto = sfide.forbice(a.nome)
    convocati, motivo = sfide.valuta(mondo, a, propria, DOMANI)
    assert convocati is not None and motivo is None
    assert sfide.valuta(mondo, a, propria * (alto + 0.1), DOMANI)[1] == f"{a.nome} vi trova troppo forti per una sfida."
    assert sfide.valuta(mondo, a, propria * (basso - 0.1), DOMANI)[1] == f"{a.nome} vi trova troppo deboli per una sfida."
    a.ultima_sfida = OGGI - datetime.timedelta(days=2)
    assert sfide.valuta(mondo, a, propria, DOMANI)[1] == f"{a.nome} ha appena giocato una sfida, e riposa."
    a.ultima_sfida = OGGI - datetime.timedelta(days=6)
    for gid in (21, 22):
        mondo.giocatori[gid].infortunato = True
    assert sfide.valuta(mondo, a, propria, DOMANI)[1] == f"{a.nome} quel giorno non ha una squadra valida."


def test_il_carattere_nasce_dal_nome():
    assert sfide.carattere("PoliTeam01 Prova") == sfide.carattere("PoliTeam01 Prova") in sfide.CARATTERI
    assert {sfide.carattere(f"PoliTeam{n:02d}") for n in range(40)} == set(sfide.CARATTERI)


def test_la_rifiutata_non_consuma_e_si_riprova_domani(monkeypatch):
    mondo, a, _b, c = _mondo()
    monkeypatch.setattr(sfide, "forbice", lambda _nome: (5.0, 6.0))
    s, messaggio = sfide.lancia(mondo, c, a.nome, [9, 10, 25])
    assert s.stato == sfide.RIFIUTATA and messaggio == f"{a.nome} rifiuta: {a.nome} vi trova troppo deboli per una sfida."
    assert c.sfide_da_lanciare == 2 and sfide.disponibili(mondo, c) == 2 and mondo.sfide.storico == [s]
    assert sfide.problema_lancio(mondo, c, a.nome, [9, 10, 25]) == f"{a.nome} ha già rifiutato oggi: si può riprovare domani."
    mondo.datetime_corrente_simulazione = DOMANI
    assert sfide.problema_lancio(mondo, c, a.nome, [9, 10, 25]) is None


def test_la_proposta_del_computer_decade_dopo_un_giorno_senza_consumare(quieta):
    mondo, a, _b, c = _mondo()
    rapporto = Mondo.rapporto_vuoto(OGGI)
    sfide._proponi(mondo, a, c, sfide.convoca(mondo, a, DOMANI), OGGI.date(), rapporto)
    assert rapporto["sfide_ricevute"] == 1 and len(sfide.in_arrivo(mondo, c)) == 1
    mondo.datetime_corrente_simulazione = DOMANI
    rapporto = Mondo.rapporto_vuoto(DOMANI)
    sfide.giorno(mondo, DOMANI, rapporto)
    assert rapporto["sfide_decadute"] == 1 and rapporto["sfide_in_attesa"] == 0
    assert mondo.sfide.storico[0].stato == sfide.DECADUTA and a.sfide_da_lanciare == 2
    assert "decaduta: nessuna risposta" in c.diario[0]["testo"]


def test_la_data_scritta_e_l_ultimo_giorno_per_rispondere(quieta):
    # La revisione del 14 ottobre 2026: i testi dicevano la data della scadenza, quando la sfida è già
    # decaduta. La data scritta dev'essere l'ultimo giorno in cui la sfida è ancora in arrivo.
    mondo, a, _b, c = _mondo()
    rapporto = Mondo.rapporto_vuoto(OGGI)
    sfide._proponi(mondo, a, c, sfide.convoca(mondo, a, DOMANI), OGGI.date(), rapporto)
    s = sfide.in_arrivo(mondo, c)[0]
    scritta = testi.data_breve(sfide.ultimo_giorno_per_rispondere(s))
    assert scritta == testi.data_breve(OGGI.date())
    assert f"rispondi entro il {scritta}" in testi.riga_sfida_in_arrivo(s, 0.5)
    assert f"si risponde entro il {scritta}, prima dell'avanzamento seguente" in rapporto["notizie"][-1]
    assert any(f"si risponde entro il {scritta}" in voce.get("testo", "") for voce in c.diario)
    # Il giorno scritto la sfida aspetta ancora; all'avanzamento seguente decade.
    assert sfide.in_arrivo(mondo, c) == [s]
    mondo.datetime_corrente_simulazione = DOMANI
    sfide.giorno(mondo, DOMANI, Mondo.rapporto_vuoto(DOMANI))
    assert sfide.in_arrivo(mondo, c) == [] and s.stato == sfide.DECADUTA


def test_la_tua_sfida_accettata_si_gioca_il_giorno_dopo(larga):
    mondo, a, _b, c = _mondo()
    apri(mondo, OGGI, "Open maschile del martedì")
    s, messaggio = sfide.lancia(mondo, c, a.nome, [9, 10, 25, 11])
    assert s.stato == sfide.ACCETTATA and s.data_gioco == DOMANI.date() and messaggio.startswith(f"{a.nome} accetta: si gioca domani, con ")
    # I convocati di domani non vanno all'edizione di domani: l'iscrizione automatica li manda a quella dopo.
    convocati = {*s.convocati["sfidante"], *s.convocati["sfidata"]}
    assert all((DOMANI.date(), DOMANI.date()) in mondo.calendario.impegni(mondo)[gid] for gid in convocati)
    iscrizioni.automatiche(mondo, mondo.calendario, OGGI, Mondo.rapporto_vuoto(OGGI))
    martedi, settimana_dopo = mondo.calendario.edizioni[0], mondo.calendario.edizioni[1]
    assert not convocati & set(martedi.ids()) and {9, 10, 11} <= set(settimana_dopo.ids())
    assert "una sfida" in mondo.calendario.impegni_descritti(mondo, 9)[-1][2]
    # Il giorno dopo si gioca, col motore vero, e la sfida passa nello storico con la differita.
    mondo.datetime_corrente_simulazione = DOMANI
    rapporto = Mondo.rapporto_vuoto(DOMANI)
    toccate = sfide.giorno(mondo, DOMANI, rapporto)
    assert s.stato == sfide.GIOCATA and s in mondo.sfide.storico and not mondo.sfide.attive and s.differita is not None
    assert s.risultato["motore"] == "vero" and rapporto["sfide_giocate"] == 1 and toccate == {a.nome, c.nome}
    assert rapporto["tue_sfide_vinte"] + rapporto["tue_sfide_perse"] == 1 and rapporto["notizie"]
    assert mondo.descrivi_impegno(mondo.giocatori[9]) == "una sfida"
    # Il gemello della gara a squadre dà lo stesso risultato.
    gemello = gemello_da_differita(s.differita, s.seme).gioca()
    assert list(gemello.set[0]) == s.risultato["punti"] and (gemello.vincitore == "A") == (s.risultato["vince"] == "sfidante")


def test_le_coppe_la_fedelta_e_la_sfida_consumata(larga):
    mondo, a, b, _c = _mondo()
    s = sfide.Sfida(mondo.sfide.nuovo_id(), iscrizioni.club_della(a), iscrizioni.club_della(b), OGGI.date(), OGGI.date(), sfide.ACCETTATA, OGGI.date(),
                    {"sfidante": [g.id for g in sfide.convoca(mondo, a, OGGI)], "sfidata": [g.id for g in sfide.convoca(mondo, b, OGGI)]})
    mondo.sfide.attive.append(s)
    fedelta = {gid: g.fedelta for gid, g in mondo.giocatori.items()}
    rapporto = Mondo.rapporto_vuoto(OGGI)
    sfide.giorno(mondo, OGGI, rapporto)
    vincitrice, perdente = (a, b) if s.risultato["vince"] == "sfidante" else (b, a)
    assert (vincitrice.coppe_oro, perdente.coppe_argento, vincitrice.sfide_vinte, perdente.sfide_perse) == (1, 1, 1, 1)
    # La decisione 3 di Gabriele del 14 ottobre 2026: nella gloria l'argento vale una piccola parte dell'oro.
    oro = palmares.punti_coppa("oro", IMPORTANZA_COPPA_SFIDA)
    assert vincitrice.palmares_recente == {"2026-10": [0.0, oro]} and perdente.palmares_recente == {"2026-10": [0.0, oro * QUOTA_GLORIA_ARGENTO_SFIDA]}
    assert oro == 2.0 and 0 < QUOTA_GLORIA_ARGENTO_SFIDA <= 0.25
    assert a.ultima_sfida == b.ultima_sfida == OGGI and a.sfide_da_lanciare == 1 and b.sfide_da_lanciare == 2
    assert s.risultato["motore"] == "rapido" and not mondo.sfide.storico and rapporto["sfide_giocate"] == 1
    for gid in s.convocati["sfidante" if vincitrice is a else "sfidata"]:
        assert mondo.giocatori[gid].fedelta == pytest.approx(fedelta[gid] + FATTORI_SENZA_STAFF[2])
    assert vincitrice.diario[0]["sfide_vinte"] == 1 and vincitrice.diario[0]["coppe_oro"] == 1 and perdente.diario[0]["coppe_argento"] == 1


def test_il_tavolino_di_chi_non_ha_piu_una_squadra(larga):
    mondo, a, _b, c = _mondo()
    s, _messaggio = sfide.lancia(mondo, c, a.nome, [9, 10, 25])
    for gid in (21, 22):
        mondo.giocatori[gid].infortunato = True
    mondo.datetime_corrente_simulazione = DOMANI
    rapporto = Mondo.rapporto_vuoto(DOMANI)
    sfide.giorno(mondo, DOMANI, rapporto)
    assert s.risultato["esito"] == "tavolino" and s.risultato["vince"] == "sfidante" and s.risultato["punti"] == [31, 0]
    assert c.coppe_oro == 1 and a.coppe_argento == 0 and rapporto["tue_sfide_vinte"] == 1
    assert all(mondo.giocatori[gid].punti_allenamento == 0 for gid in (9, 10, 25))
    assert "a tavolino" in mondo.giocatori[9].diario[0]["testo"]


def test_la_polisportiva_chiusa_fa_decadere_la_sfida(larga):
    mondo, a, _b, c = _mondo()
    s, _messaggio = sfide.lancia(mondo, c, a.nome, [9, 10, 25])
    mondo.chiudi_polisportiva(a)
    mondo.datetime_corrente_simulazione = DOMANI
    sfide.giorno(mondo, DOMANI, Mondo.rapporto_vuoto(DOMANI))
    assert s.stato == sfide.DECADUTA and c.sfide_da_lanciare == 2 and "ha chiuso" in c.diario[0]["testo"]


def test_accetta_e_rifiuta_le_sfide_in_arrivo():
    mondo, a, b, c = _mondo()
    rapporto = Mondo.rapporto_vuoto(OGGI)
    sfide._proponi(mondo, a, c, sfide.convoca(mondo, a, DOMANI), OGGI.date(), rapporto)
    sfide._proponi(mondo, b, c, sfide.convoca(mondo, b, DOMANI), OGGI.date(), rapporto)
    prima, seconda = sfide.in_arrivo(mondo, c)
    assert sfide.problema_risposta(mondo, prima.id, c, [9, 10, 11]) == "Al tavolo servono due giocatori di un sesso e uno dell'altro."
    assert sfide.accetta(mondo, prima.id, c, [9, 10, 25]).startswith(f"Sfida accettata: si gioca domani contro {a.nome}")
    assert prima.stato == sfide.ACCETTATA and prima.convocati["sfidata"] == [9, 10, 25]
    # Chi è convocato per la prima non si può schierare nella seconda.
    assert sfide.problema_risposta(mondo, seconda.id, c, [9, 11, 26]).endswith("quel giorno ha già un impegno.")
    assert sfide.rifiuta(mondo, seconda.id, c) == f"Sfida di {b.nome} rifiutata."
    assert seconda.stato == sfide.RIFIUTATA and b.sfide_da_lanciare == 2 and sfide.disponibili(mondo, a) == 1


def test_la_registrazione_nella_carriera_e_le_riserve():
    mondo, a, b, _c = _mondo()
    sq_a = Squadra(a.nome, tuple(sfide.convoca(mondo, a, OGGI, quanti=5)))
    sq_b = Squadra(b.nome, tuple(sfide.convoca(mondo, b, OGGI, quanti=4)))
    risultato = esito_rapido.gioca_squadre(sq_a, sq_b, 77)
    prima = {g.id: (g.punti_allenamento, g.esperienza, g.costanza, g.partitevinte) for g in (*sq_a.giocatori, *sq_b.giocatori)}
    MotorePartita(mondo).registra_squadre(risultato, sfide.esperienza.SFIDA, 1.0, diario=True, solo_tuoi=True, gara="la sfida", aggrega="sfide")
    vince_a = risultato.vincitore == "A"
    for squadra, vinto in ((sq_a, vince_a), (sq_b, not vince_a)):
        attesi = (PA_PARTITA_BASE + PA_PER_SET_VINTO + PA_VITTORIA if vinto else PA_PARTITA_BASE) * PA_FATTORE_SFIDA
        for g in squadra.titolari:
            assert g.punti_allenamento - prima[g.id][0] == pytest.approx(attesi)
            assert g.esperienza - prima[g.id][1] == pytest.approx(ESPERIENZA_PER_SFIDA)
            assert (g.gare_squadre_vinte, g.gare_squadre_perse) == ((1, 0) if vinto else (0, 1)) and g.partitevinte == prima[g.id][3]
            assert g.diario[0]["sfide"] == 1 and g.diario[0]["sfide_vinte"] == int(vinto)
        for g in squadra.riserve:
            assert g.punti_allenamento == prima[g.id][0] and g.costanza == prima[g.id][2] and g.gare_squadre_vinte + g.gare_squadre_perse == 0
            assert g.esperienza - prima[g.id][1] == pytest.approx(ESPERIENZA_RISERVA_QUOTA * ESPERIENZA_PER_SFIDA)
        assert all(g.ha_un_impegno(OGGI) for g in squadra.giocatori)


def test_i_lanci_del_computer_giocano_e_propongono():
    mondo, _a, _b, _c = _mondo()
    for n, primo in enumerate((12, 15, 18)):
        polisportiva(mondo, f"PoliTeam0{n + 3} Prova", ids=(primo, primo + 1, primo + 2, 28 + 3 * n, 29 + 3 * n))
    stato = random.getstate()
    random.seed(12)
    try:
        totale = Mondo.rapporto_vuoto(OGGI)
        for giorni in range(60):
            data = OGGI + datetime.timedelta(days=giorni)
            mondo.datetime_corrente_simulazione = data
            rapporto = Mondo.rapporto_vuoto(data)
            sfide.giorno(mondo, data, rapporto)
            for chiave in ("sfide_giocate", "sfide_ricevute", "sfide_decadute"):
                totale[chiave] += rapporto[chiave]
    finally:
        random.setstate(stato)
    cpu = [p for p in mondo.polisportive.values() if p.is_cpu_controlled]
    assert totale["sfide_giocate"] > 0 and sum(p.coppe_oro for p in mondo.polisportive.values()) == totale["sfide_giocate"]
    assert all(0 <= p.sfide_da_lanciare <= 2 for p in cpu) and sum(2 - p.sfide_da_lanciare for p in cpu) == totale["sfide_giocate"]
    assert totale["sfide_ricevute"] == totale["sfide_decadute"] + len(mondo.sfide.attive)


def _coppa(mondo, data, rapporto=None):
    solo(["Coppa delle polisportive"])
    return apri(mondo, data, "Coppa delle polisportive", rapporto=rapporto)[0]


def test_la_coppa_qualifica_per_gloria_con_la_rosa():
    mondo, a, b, c = _mondo()
    d = polisportiva(mondo, "PoliTeam03 Prova", ids=(12, 13, 14, 28))
    e = polisportiva(mondo, "PoliTeam04 Prova", ids=(15, 16, 17))
    for poli, gloria in ((a, 300), (b, 200), (c, 250), (d, 100), (e, 400)):
        poli.gloria = gloria
    apertura = datetime.datetime(2027, 5, 26, 9, 0)
    mondo.datetime_corrente_simulazione = apertura
    rapporto = Mondo.rapporto_vuoto(apertura)
    ed = _coppa(mondo, apertura, rapporto)
    # PoliTeam04 ha più gloria ma soltanto uomini: non si qualifica.
    assert ed.ids() == [a.nome, c.nome, b.nome, d.nome] and ed.data_inizio == datetime.date(2027, 6, 15)
    assert rapporto["tue_qualificazioni_coppa"] == 1 and c.diario[0]["testo"].startswith("Qualificata a Coppa delle polisportive")
    assert all(iscritto["origine"] == iscrizioni.QUALIFICATO and 3 <= len(iscritto["rosa"]) <= 6 for iscritto in ed.iscritti)
    assert set(ed.iscritto(d.nome)["rosa"]) == {12, 13, 14, 28}
    # La rosa resta impegnata nei giorni della coppa.
    assert (ed.data_inizio, ed.data_fine) in mondo.calendario.impegni(mondo)[12]
    # La tua rosa si cambia fino al sorteggio, con le sue regole.
    assert sfide.problema_rosa(mondo, ed.id, c, [9, 10, 11]) == "Fra i primi tre servono due giocatori di un sesso e uno dell'altro."
    sfide.cambia_rosa(mondo, ed.id, c, [25, 9, 10, 26])
    assert ed.iscritto(c.nome)["rosa"] == [25, 9, 10, 26]


def test_la_fatica_della_giornata_nella_coppa(monkeypatch):
    # La lettura 12 delle decisioni di Gabriele del 14 ottobre 2026, risposta 5: nella coppa, fra
    # polisportive del computer con l'esito rapido, ogni incontro dopo il primo del giorno parte con un
    # quarto delle azioni che ciascuno ha già giocato quel giorno.
    mondo = mondo_di_prova(20, 20)
    for numero, ids in enumerate(((1, 2, 3, 21, 22), (5, 6, 7, 23, 24), (9, 10, 11, 25, 26), (12, 13, 14, 28, 29)), start=1):
        polisportiva(mondo, f"PoliTeam0{numero} Prova", ids=ids)
    apertura = datetime.datetime(2027, 5, 26, 9, 0)
    mondo.datetime_corrente_simulazione = apertura
    _coppa(mondo, apertura)
    visti = []
    vero = esito_rapido.gioca_squadre

    def spia(*argomenti, **opzioni):
        risultato = vero(*argomenti, **opzioni)
        visti.append((mondo.datetime_corrente_simulazione, opzioni.get("azioni_iniziali"), {gid: s.azioni for gid, s in risultato.statistiche.items()}))
        return risultato

    monkeypatch.setattr(esito_rapido, "gioca_squadre", spia)
    data = datetime.datetime(2027, 6, 15, 9, 0)
    while True:
        giorno(mondo, data)
        if not mondo.calendario.tornei:
            break
        data += datetime.timedelta(days=1)
    fatte = {}
    for quando, iniziali, azioni in visti:
        del_giorno = fatte.setdefault(quando, {})
        for gid, quante in (iniziali or {}).items():
            assert quante == round(FATICA_RESIDUA_GIORNATA * del_giorno[gid])
        for gid, quante in azioni.items():
            del_giorno[gid] = del_giorno.get(gid, 0) + quante
    assert visti[0][1] is None and sum(1 for _q, iniziali, _a in visti if iniziali) >= 2


def test_la_coppa_si_gioca_e_da_le_coppe():
    mondo, a, b, c = _mondo()
    d = polisportiva(mondo, "PoliTeam03 Prova", ids=(12, 13, 14, 28, 29))
    e = polisportiva(mondo, "PoliTeam04 Prova", ids=(15, 16, 17))
    apertura = datetime.datetime(2027, 5, 26, 9, 0)
    mondo.datetime_corrente_simulazione = apertura
    ed = _coppa(mondo, apertura)
    assert e.nome not in ed.ids() and len(ed.ids()) == 4
    # PoliTeam03 chiude prima del sorteggio, e PoliTeam04, che intanto ha una donna, prende il suo posto.
    mondo.chiudi_polisportiva(d)
    mondo._entra(e, mondo.giocatori[30])
    inizio = datetime.datetime(2027, 6, 15, 9, 0)
    rapporto = Mondo.rapporto_vuoto(inizio)
    data = inizio
    while True:
        giorno(mondo, data, rapporto)
        if not mondo.calendario.tornei:
            break
        data += datetime.timedelta(days=1)
        assert data < inizio + datetime.timedelta(days=10)
    torneo = mondo.calendario.conclusi[0]
    assert torneo.squadre and set(torneo.iscritti) == {a.nome, b.nome, c.nome, e.nome} and torneo.stato == tornei.CONCLUSO
    podio = [mondo.polisportive[nome] for nome in torneo.classifica_finale]
    assert [(p.coppe_oro, p.coppe_argento, p.coppe_bronzo, p.coppe_legno) for p in podio] == [(1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)]
    assert podio[0].palmares_recente == {"2027-06": [0.0, 300.0]}
    # Gli incontri della tua polisportiva col motore vero, da riascoltare; quelli degli altri con l'esito rapido.
    tuoi = [i for i in torneo.incontri() if c.nome in (i.a, i.b) and i.esito == "regolare"]
    assert tuoi and all(i.motore == "vero" and i.differita for i in tuoi)
    assert all(i.motore == "rapido" for i in torneo.incontri() if c.nome not in (i.a, i.b) and i.esito == "regolare")
    for incontro in tuoi:
        gemello = gemello_da_differita(incontro.differita, incontro.seme).gioca()
        assert [list(s) for s in gemello.set] == [list(s) for s in incontro.set]
    # La lettura 12 delle decisioni di Gabriele del 14 ottobre 2026: anche nella coppa vale la fatica della
    # giornata, e la differita la porta, perché il gemello ripeta l'incontro.
    assert any(n for incontro in tuoi for lato in incontro.differita["azioni_iniziali"] for n in lato)
    voce = mondo.calendario.albo.voci[-1]
    assert voce[1] == modelli_torneo.SQUADRE and len(voce[8]) == 4 and mondo.calendario.albo.club[voce[8][0]][0] == podio[0].nome
    assert rapporto["tuoi_tornei_conclusi"] == 1 and any(v.get("testo", "").startswith("Chiude Coppa delle polisportive, sede 1") for v in c.diario)
    # I titolari hanno le gare a squadre e i punti allenamento per l'importanza 3.
    assert sum(mondo.giocatori[gid].gare_squadre_vinte + mondo.giocatori[gid].gare_squadre_perse for gid in range(1, 41)) > 0
    # La decisione 9 di Gabriele del 14 ottobre 2026: la coppa dà alla rosa la fedeltà della coppa, come una
    # medaglia, a chi è ancora tesserato, e a tutti l'esperienza delle fasi superate e del piazzamento, per
    # l'importanza. Si rifà la chiusura, e si guarda soltanto quanto cambia.
    fasi = torneo.fasi_superate()
    prima = {gid: (g.fedelta, g.esperienza) for gid, g in mondo.giocatori.items()}
    premiazioni.chiudi_squadre(mondo, mondo.calendario, torneo, data, Mondo.rapporto_vuoto(data))
    importanza = torneo.modello["importanza"]
    nelle_rose = set()
    for posto, cid in enumerate(torneo.classifica_finale, start=1):
        poli, coppa = mondo.polisportive[cid], premiazioni.MEDAGLIE[posto - 1]
        assert fasi.get(cid, 0) > 0 or posto > 2
        for gid in torneo.info[cid]["rosa"]:
            nelle_rose.add(gid)
            g = mondo.giocatori[gid]
            fedelta, esp = prima[gid]
            assert g.fedelta == pytest.approx(min(FEDELTA_MASSIMA, fedelta + (FEDELTA_PER_MEDAGLIA[coppa] * FATTORI_SENZA_STAFF[2] if g.appartenenza == poli.nome else 0)))
            guadagno = (ESPERIENZA_PER_FASE_SUPERATA * fasi.get(cid, 0) + esperienza.premio_piazzamento(posto)) * importanza
            assert g.esperienza == pytest.approx(min(ESPERIENZA_MASSIMA, esp + guadagno))
    assert all(prima[gid] == (g.fedelta, g.esperienza) for gid, g in mondo.giocatori.items() if gid not in nelle_rose)
