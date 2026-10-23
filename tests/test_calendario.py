"""
Test del calendario dei tornei nel mondo, tappa 12, punto 5 del progetto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
L'apertura secondo la ricorrenza, anche due edizioni insieme; la rinomina di un modello che non
riapre niente; il sorteggio in sedi; l'annullamento con i rimborsi e la riscrittura del giorno dopo;
i turni del giorno; il tavolino dell'infortunato e l'acciaccato che gioca col suo calo; la fatica
della giornata; l'impegno del giorno che ferma l'amichevole; il calendario che si salva a metà di un
torneo e prosegue uguale; lo stesso seme che dà lo stesso mondo.
"""

import datetime
import sys
from pathlib import Path

import pytest
from aiuti_calendario import OGGI, apri, giorno, iscrivi_tutti, modelli, mondo_di_prova, polisportiva, solo

import archivio
import esito_rapido
import formule
import iscrizioni
import modelli_torneo
import tornei
from calendario import Calendario
from mondo import Mondo
from partita import MotorePartita
from utilita import data_breve

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))
import mondi_sintetici as ms

MARTEDI = "Open maschile del martedì"


def test_l_apertura_secondo_la_ricorrenza_anche_due_insieme():
    mondo = mondo_di_prova(4, 4)
    edizioni = apri(mondo, OGGI, MARTEDI)
    # Le iscrizioni durano 14 giorni: il 5 ottobre sono aperte quelle del 6 e del 13, non quella del 20.
    assert [ed.data_inizio for ed in edizioni] == [datetime.date(2026, 10, 6), datetime.date(2026, 10, 13)]
    assert [ed.numero for ed in edizioni] == [1, 2] and all(ed.data_apertura == OGGI.date() for ed in edizioni)
    assert apri(mondo, OGGI, MARTEDI) == edizioni
    domani = OGGI + datetime.timedelta(days=1)
    assert [ed.data_inizio for ed in apri(mondo, domani, MARTEDI)][-1] == datetime.date(2026, 10, 20)
    mensile = apri(mondo, OGGI, "Gran Premio maschile")
    assert [ed.data_inizio for ed in mensile] == [datetime.date(2026, 10, 15)]
    annuale = apri(mondo, datetime.datetime(2026, 11, 30, 9, 0), "Campionato italiano maschile")
    assert [ed.data_inizio for ed in annuale] == [datetime.date(2026, 12, 10)]


def test_la_rinomina_di_un_modello_non_riapre_niente():
    mondo = mondo_di_prova(4, 4)
    apri(mondo, OGGI, MARTEDI)
    gestore = modelli_torneo.GestoreModelli()
    m = gestore.modello("modello_1")
    m.nome = "Open dei martedì"
    gestore.salva(m)
    rapporto = Mondo.rapporto_vuoto(OGGI)
    mondo.calendario.apri_edizioni(mondo, OGGI, [m], formule.leggi()[0], rapporto)
    assert len(mondo.calendario.edizioni) == 2 and mondo.calendario.ultime_aperture["modello_1"] == "2026-10-13"


def test_il_sorteggio_in_sedi_e_la_data_del_ritmo():
    mondo = mondo_di_prova(40, 0)
    ed = apri(mondo, OGGI, MARTEDI)[0]
    iscrivi_tutti(ed, mondo, range(1, 41))
    martedi = OGGI + datetime.timedelta(days=1)
    mondo.calendario.sorteggi(mondo, martedi, Mondo.rapporto_vuoto(martedi))
    sedi = [t for t in mondo.calendario.tornei if t.edizione == ed.id]
    assert [len(t.iscritti) for t in sedi] == [20, 20] and {t.sede for t in sedi} == {1, 2}
    assert ed not in mondo.calendario.edizioni and all(mondo.calendario.numero_di(t) == 1 for t in sedi)
    # La data del ritmo è fra 58 e 64 giorni dopo l'inizio.
    for gid in range(1, 41):
        distanza = (mondo.giocatori[gid].prossimo_torneo.date() - ed.data_inizio).days
        assert 58 <= distanza <= 64


def test_l_annullamento_con_i_rimborsi_e_la_riscrittura_del_giorno_dopo():
    mondo = mondo_di_prova(3, 0)
    poli = polisportiva(mondo, "Club Di Prova", cpu=False, cassa=100, ids=(1, 2, 3))
    edizioni = apri(mondo, OGGI, MARTEDI)
    prima = edizioni[0]
    for gid in (1, 2, 3):
        prima.aggiungi(gid, {"nome": poli.nome, "fondazione": poli.datetime_creazione_sim.date().isoformat()}, 10, "mano")
    poli.cassa -= 30
    martedi = OGGI + datetime.timedelta(days=1)
    rapporto = Mondo.rapporto_vuoto(martedi)
    mondo.calendario.sorteggi(mondo, martedi, rapporto)
    assert poli.cassa == 100 and poli.conti_del_mese["rimborsi"] == 30
    assert rapporto["edizioni_annullate"] == rapporto["tue_edizioni_annullate"] == 1 and rapporto["notizie"]
    # L'articolo davanti al nome del torneo, dalla seconda revisione della tappa 14.
    data = data_breve(prima.data_inizio)
    assert mondo.giocatori[1].diario[0]["testo"] == f"L'{prima.nome} del {data} è annullato: gli iscritti erano meno di 4, e la quota torna."
    assert rapporto["notizie"] == [f"L'{prima.nome} del {data} è annullato per pochi iscritti."] and prima.nome.startswith("Open ")
    assert mondo.giocatori[1].prossimo_torneo is None and not mondo.calendario.tornei
    # Il giorno dopo l'iscrizione automatica li iscrive all'edizione utile seguente.
    rapporto = giorno(mondo, martedi + datetime.timedelta(days=1))
    # Il Gran Premio del 15 è più importante dell'open del 13, e comincia nella stessa settimana: lo scelgono lui.
    iscritti = mondo.calendario.iscritti_alle_edizioni()
    assert iscritti >= {1, 2, 3} and rapporto["tue_iscrizioni"] == 3 and poli.cassa == 70
    assert all(1 in ed.ids() for ed in mondo.calendario.edizioni if ed.nome == "Gran Premio maschile")


def test_al_sorteggio_chi_ha_lasciato_l_attivita_esce_e_la_quota_torna():
    # La lettura 13 delle decisioni finali di Gabriele del 14 ottobre 2026, dalla verifica del 15 ottobre:
    # chi si è ritirato dall'attività o è uscito di scena da iscritto lascia l'edizione al sorteggio, e la
    # quota torna al club; l'infortunato resta, a suo rischio, e perde a tavolino.
    mondo = mondo_di_prova(6, 0)
    poli = polisportiva(mondo, "Club Di Prova", cpu=False, cassa=100, ids=range(1, 7))
    ed = apri(mondo, OGGI, MARTEDI)[0]
    for gid in range(1, 7):
        ed.aggiungi(gid, {"nome": poli.nome, "fondazione": poli.datetime_creazione_sim.date().isoformat()}, 10, "mano")
    poli.cassa -= 60
    martedi = OGGI + datetime.timedelta(days=1)
    mondo.datetime_corrente_simulazione = martedi
    ritirato, morto, fermo = mondo.giocatori[1], mondo.giocatori[2], mondo.giocatori[3]
    ritirato.ritirato = True
    mondo._lascia(poli, ritirato)
    mondo._uscita(morto, "morte", martedi, morto.eta)
    fermo.infortunato, fermo.infortunio_sede = True, "ginocchio"
    fermo.infortunio_fine_datetime = martedi + datetime.timedelta(days=30)
    mondo.calendario.sorteggi(mondo, martedi, Mondo.rapporto_vuoto(martedi))
    sedi = [t for t in mondo.calendario.tornei if t.edizione == ed.id]
    assert {gid for t in sedi for gid in t.iscritti} == {3, 4, 5, 6}
    assert poli.cassa == 60 and poli.conti_del_mese["rimborsi"] == 20
    voci = [voce["testo"] for voce in poli.diario if ed.nome in voce["testo"]]
    assert any("dall'attività prima del sorteggio, e la quota di 10 euro torna." in v for v in voci)
    assert any("di scena prima del sorteggio, e la quota di 10 euro torna." in v for v in voci)
    # Senza nessuno da togliere, il sorteggio è quello di prima.
    assert iscrizioni.togli_chi_ha_lasciato(mondo, ed) == 0


def test_i_turni_del_giorno_e_le_fasi_in_giorni_diversi():
    mondo = mondo_di_prova(32, 0)
    ed = apri(mondo, OGGI, MARTEDI)[0]
    iscrivi_tutti(ed, mondo, range(1, 33))
    martedi = OGGI + datetime.timedelta(days=1)
    mondo.calendario.sorteggi(mondo, martedi, Mondo.rapporto_vuoto(martedi))
    rapporto = Mondo.rapporto_vuoto(martedi)
    mondo.calendario.gioca(mondo, martedi, rapporto)
    torneo = mondo.calendario.tornei[0]
    # Il primo giorno i tre turni dei gironi da quattro, 48 incontri; il secondo giorno il tabellone.
    assert rapporto["incontri_torneo"] + rapporto["incontri_tavolino"] == 48 and torneo.fase_corrente == 1 and torneo.giorni_giocati == 1
    assert all(i.data == "2026-10-06" for i in torneo.fasi[0].incontri) and not any(i.giocato for i in torneo.fasi[1].incontri if i.esito != tornei.RIPOSO)
    mercoledi = martedi + datetime.timedelta(days=1)
    mondo.datetime_corrente_simulazione = mercoledi
    rapporto = Mondo.rapporto_vuoto(mercoledi)
    mondo.calendario.gioca(mondo, mercoledi, rapporto)
    assert not mondo.calendario.tornei and mondo.calendario.conclusi[0] is torneo and torneo.stato == tornei.CONCLUSO
    assert rapporto["tornei_conclusi"] == 1 and len(torneo.classifica_finale) == 32


def test_il_tavolino_dell_infortunato_e_l_acciaccato_che_gioca(monkeypatch):
    mondo = mondo_di_prova(4, 0)
    ed = apri(mondo, OGGI, MARTEDI)[0]
    iscrivi_tutti(ed, mondo, range(1, 5))
    martedi = OGGI + datetime.timedelta(days=1)
    mondo.datetime_corrente_simulazione = martedi
    mondo.calendario.sorteggi(mondo, martedi, Mondo.rapporto_vuoto(martedi))
    fermo = mondo.giocatori[2]
    fermo.infortunato, fermo.infortunio_sede = True, "ginocchio"
    fermo.infortunio_fine_datetime = martedi + datetime.timedelta(days=30)
    acciaccato = mondo.giocatori[3]
    acciaccato.acciacco_fino, acciaccato.acciacco_calo, acciaccato.acciacco_giorni, acciaccato.acciacco_sede = martedi + datetime.timedelta(days=4), 0.02, 4, "caviglia"
    cali_visti = []
    vero = esito_rapido.gioca

    def spia(*argomenti, **opzioni):
        cali_visti.append(opzioni.get("cali"))
        return vero(*argomenti, **opzioni)

    monkeypatch.setattr(esito_rapido, "gioca", spia)
    rapporto = Mondo.rapporto_vuoto(martedi)
    mondo.calendario.gioca(mondo, martedi, rapporto)
    torneo = mondo.calendario.tornei[0] if mondo.calendario.tornei else mondo.calendario.conclusi[0]
    di_fermo = [i for i in torneo.incontri() if 2 in (i.a, i.b)]
    assert di_fermo and all(i.esito == tornei.TAVOLINO and i.set_giocati == 0 for i in di_fermo)
    assert rapporto["incontri_tavolino"] == len(di_fermo)
    assert fermo.partitevinte + fermo.partiteperse == 0 and fermo.punti_allenamento == 0.0
    assert any(c and c.get(3) == pytest.approx(0.02) for c in cali_visti)


def test_la_fatica_della_giornata(monkeypatch):
    mondo = mondo_di_prova(4, 0)
    ed = apri(mondo, OGGI, MARTEDI)[0]
    iscrivi_tutti(ed, mondo, range(1, 5))
    martedi = OGGI + datetime.timedelta(days=1)
    mondo.datetime_corrente_simulazione = martedi
    mondo.calendario.sorteggi(mondo, martedi, Mondo.rapporto_vuoto(martedi))
    iniziali = []
    vero = esito_rapido.gioca

    def spia(*argomenti, **opzioni):
        risultato = vero(*argomenti, **opzioni)
        iniziali.append((opzioni.get("azioni_iniziali"), {gid: s.azioni for gid, s in risultato.statistiche.items()}))
        return risultato

    monkeypatch.setattr(esito_rapido, "gioca", spia)
    mondo.calendario.gioca(mondo, martedi, Mondo.rapporto_vuoto(martedi))
    # Il girone unico da quattro gioca tre turni oggi: dal secondo incontro di ciascuno un quarto delle azioni di prima.
    assert iniziali[0][0] is None
    fatte = {}
    for azioni_iniziali, azioni in iniziali:
        for gid, quante in (azioni_iniziali or {}).items():
            assert quante == round(0.25 * fatte[gid])
        for gid, quante in azioni.items():
            fatte[gid] = fatte.get(gid, 0) + quante
    assert any(a for a, _s in iniziali[2:])


def test_l_impegno_del_giorno_ferma_l_amichevole():
    mondo = mondo_di_prova(4, 0)
    ed = apri(mondo, OGGI, MARTEDI)[0]
    iscrivi_tutti(ed, mondo, range(1, 5))
    martedi = OGGI + datetime.timedelta(days=1)
    mondo.datetime_corrente_simulazione = martedi
    mondo.calendario.sorteggi(mondo, martedi, Mondo.rapporto_vuoto(martedi))
    mondo.calendario.gioca(mondo, martedi, Mondo.rapporto_vuoto(martedi))
    g = mondo.giocatori[1]
    assert g.ha_un_impegno(martedi)
    mondo.giocatori[99] = altro = mondo_di_prova(1, 0).giocatori[1]
    altro.id = 99
    problema = MotorePartita(mondo).problema_amichevole(1, 99)
    assert problema == f"Oggi {g.nome} {g.cognome} ha già giocato il torneo: ognuno gioca al massimo un incontro per giorno simulato."


def test_il_calendario_si_salva_a_meta_torneo_e_prosegue_uguale(cartella_di_prova):
    mondo = mondo_di_prova(20, 0)
    ed = apri(mondo, OGGI, MARTEDI)[0]
    iscrivi_tutti(ed, mondo, range(1, 21))
    martedi = OGGI + datetime.timedelta(days=1)
    mondo.datetime_corrente_simulazione = martedi
    mondo.calendario.sorteggi(mondo, martedi, Mondo.rapporto_vuoto(martedi))
    mondo.calendario.gioca(mondo, martedi, Mondo.rapporto_vuoto(martedi))
    assert mondo.calendario.tornei
    dati = mondo.calendario.a_dizionario()
    copia = Calendario.da_dizionario(dati)
    assert copia.a_dizionario() == dati
    with pytest.raises(ValueError):
        Calendario.da_dizionario({**dati, "prossimo_id": 1})
    assert archivio.salva(mondo)
    ricaricato = Mondo()
    archivio.carica(ricaricato)
    assert ricaricato.calendario.a_dizionario() == dati


def test_lo_stesso_seme_da_lo_stesso_mondo(cartella_di_prova):
    primo = ms.impronta_del_mondo(ms.mondo_nato(77, 45))
    secondo = ms.impronta_del_mondo(ms.mondo_nato(77, 45))
    assert primo == secondo


def test_i_modelli_fermi_non_aprono_e_il_mondo_gioca_i_tornei():
    solo([MARTEDI])
    assert sum(1 for m in modelli() if m.attivo) == 1
    mondo = mondo_di_prova(12, 12)
    polisportiva(mondo, "PoliTeam01 Prova", cassa=1_000_000, ids=range(1, 9))
    for n in range(20):
        giorno(mondo, OGGI + datetime.timedelta(days=n))
    cal = mondo.calendario
    assert {ed.nome for ed in cal.edizioni} == {MARTEDI} and cal.albo.voci
    assert all(g.tornei_giocati >= 1 for g in mondo.giocatori.values() if g.sesso == "m")
    assert all(g.tornei_giocati == 0 for g in mondo.giocatori.values() if g.sesso == "f")
