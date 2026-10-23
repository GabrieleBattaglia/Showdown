"""
Test della chiusura delle sedi di torneo, tappa 12, punti 5.6, 5.9, 5.10 e 5.11 del progetto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
La chiusura con le medaglie del giocatore e del club, i premi nei conti, l'esperienza delle fasi e dei
piazzamenti, la fedeltà e la bandiera; il club chiuso che lascia la medaglia al giocatore e il premio
alla federazione, e il libero che non porta premi a nessuno; i punti della classifica; i diari dei tuoi
e le voci aggregate degli altri; l'albo che conserva tutto, con le tabelle dei nomi senza doppioni, e il
podio che si legge anche dopo l'uscita del giocatore e la chiusura del club.
"""

import datetime

import pytest
from aiuti_calendario import OGGI, modello, mondo_di_prova, polisportiva

import esperienza
import formule
import iscrizioni
import palmares
import premiazioni
import tornei
from calendario import Calendario
from costanti import ESPERIENZA_PER_FASE_SUPERATA
from mondo import Mondo

# L'ordine di forza: 1 del computer, 5 di un club chiuso, 3 dell'utente, 4 libero, 2 del computer, gli altri liberi.
ORDINE = (1, 5, 3, 4, 2, 6, 7, 8)


def _sede(mondo, club_a, club_b):
    info = {}
    for posto, gid in enumerate(ORDINE):
        g = mondo.giocatori[gid]
        club = None
        pagato = 0
        if gid in (1, 2, 3):
            club, pagato = iscrizioni.club_di(mondo, g), 10
        elif gid == 5:
            club, pagato = {"nome": "Club Chiuso", "fondazione": "2020-01-01"}, 10
        info[gid] = {"nome": f"{g.nome} {g.cognome}", "sesso": g.sesso, "club": club, "forza": 1.0 - posto / 10.0, "pagato": pagato}
    return tornei.Torneo(1, 1, 1, modello("Open maschile del martedì").a_dizionario(), formule.formula("gironi_32"), OGGI, 7, info)


def _gioca_fino_alla_fine(torneo):
    def vince_il_piu_forte(incontro, _azioni):
        a_vince = torneo.forza(incontro.a) > torneo.forza(incontro.b)
        necessari = incontro.set_al_meglio // 2 + 1
        sets = [[11, 5] if a_vince else [5, 11] for _ in range(necessari)]
        return {"esito": "regolare", "vince": "A" if a_vince else "B", "set": sets, "set_giocati": necessari}

    giorno = OGGI
    while torneo.stato == tornei.IN_CORSO:
        torneo.giornata(vince_il_piu_forte, giorno)
        giorno += datetime.timedelta(days=1)


@pytest.fixture
def chiusa():
    mondo = mondo_di_prova(8, 0)
    club_a = polisportiva(mondo, "PoliTeam01 Prova", ids=(1, 2))
    club_b = polisportiva(mondo, "Club Di Prova", cpu=False, ids=(3,))
    g1 = mondo.giocatori[1]
    g1.bandiera, g1.fedelta = True, 77.0
    torneo = _sede(mondo, club_a, club_b)
    _gioca_fino_alla_fine(torneo)
    cassa_a, cassa_b = club_a.cassa, club_b.cassa
    calendario = Calendario()
    calendario.numeri_dei_tornei[torneo.id] = 4
    rapporto = Mondo.rapporto_vuoto(OGGI)
    toccate = premiazioni.chiudi(mondo, calendario, torneo, OGGI, rapporto)
    return {"mondo": mondo, "torneo": torneo, "a": club_a, "b": club_b, "cassa_a": cassa_a, "cassa_b": cassa_b, "calendario": calendario, "rapporto": rapporto,
            "toccate": toccate}


def test_le_medaglie_del_giocatore_e_del_club(chiusa):
    mondo, torneo, a, b = chiusa["mondo"], chiusa["torneo"], chiusa["a"], chiusa["b"]
    assert torneo.classifica_finale[:4] == [1, 5, 3, 4]
    g = mondo.giocatori
    assert (g[1].ori, g[5].argenti, g[3].bronzi, g[4].legni) == (1, 1, 1, 1)
    assert (a.ori, b.bronzi, a.argenti) == (1, 1, 0)
    assert a.palmares_recente == {"2026-10": [30.0, 0.0]} and b.palmares_recente == {"2026-10": [5.0, 0.0]}
    assert chiusa["toccate"] == {a.nome, b.nome}
    assert chiusa["rapporto"]["tue_medaglie_bronzo"] == 1 and chiusa["rapporto"]["tuoi_tornei_conclusi"] == 1 and chiusa["rapporto"]["tornei_conclusi"] == 1


def test_i_premi_nei_conti_e_alla_federazione(chiusa):
    torneo, a, b = chiusa["torneo"], chiusa["a"], chiusa["b"]
    # Quattro paganti a 10 euro con il contributo che raddoppia: 80 euro, divisi fra gli otto posti.
    assert sum(torneo.premi.values()) <= 80 and torneo.premi[1] > torneo.premi[5]
    assert a.cassa - chiusa["cassa_a"] == torneo.premi[1] + torneo.premi.get(2, 0) == a.conti_del_mese["premi"]
    assert b.cassa - chiusa["cassa_b"] == torneo.premi[3] and chiusa["rapporto"]["tuoi_premi"] == torneo.premi[3]


def test_esperienza_fedelta_e_bandiera(chiusa):
    mondo, torneo = chiusa["mondo"], chiusa["torneo"]
    g1 = mondo.giocatori[1]
    fasi = torneo.fasi_superate()
    atteso = fasi[1] * ESPERIENZA_PER_FASE_SUPERATA + esperienza.premio_piazzamento(1)
    assert g1.esperienza == pytest.approx(atteso)
    assert mondo.giocatori[8].esperienza == pytest.approx(esperienza.premio_piazzamento(8))
    assert g1.fedelta == 81.0 and any("Diventa una bandiera" in v.get("testo", "") for v in g1.diario)
    assert mondo.giocatori[3].fedelta == 2.0 and mondo.giocatori[2].fedelta == 0.0


def test_i_punti_della_classifica_e_i_tornei_giocati(chiusa):
    mondo = chiusa["mondo"]
    assert [mondo.giocatori[gid].punti_mondiali for gid in ORDINE] == [palmares.punti_classifica(p) for p in range(1, 9)]
    assert all(mondo.giocatori[gid].tornei_giocati == 1 for gid in ORDINE)


def test_i_diari(chiusa):
    mondo, a, b = chiusa["mondo"], chiusa["a"], chiusa["b"]
    tuo = mondo.giocatori[3].diario[0]["testo"]
    assert tuo.startswith("Chiude Open maschile del martedì, sede 1, terzo su 8:") and "medaglia di bronzo" in tuo and "premio di" in tuo
    assert b.diario[0]["testo"].startswith("Chiude Open maschile del martedì, sede 1: ")
    del_computer = mondo.giocatori[2].diario[0]
    assert del_computer["anno"] == 2026 and del_computer["tornei"] == 1 and del_computer["incontri"] >= 3
    assert a.diario[0]["anno"] == 2026 and a.diario[0]["ori"] == 1 and a.diario[0]["iscrizioni"] == 2


@pytest.mark.parametrize(("nome", "uomini", "donne", "titolo"), [("Campionato italiano maschile", 8, 0, "campione"),
                                                                 ("Campionato italiano femminile", 0, 8, "campionessa")])
def test_il_tuo_campione_d_italia(nome, uomini, donne, titolo):
    # Dalla tappa 14, D34: il mondiale è il campionato italiano, e il tuo che lo vince è campione o campionessa d'Italia.
    mondo = mondo_di_prova(uomini, donne)
    polisportiva(mondo, "Club Di Prova", cpu=False, ids=(1,))
    info = {gid: {"nome": f"{g.nome} {g.cognome}", "sesso": g.sesso, "club": iscrizioni.club_di(mondo, g) if gid == 1 else None,
                  "forza": 1.0 - gid / 10.0, "pagato": 0} for gid, g in mondo.giocatori.items()}
    torneo = tornei.Torneo(1, 1, 1, modello(nome).a_dizionario(), formule.formula("gironi_32"), OGGI, 7, info)
    _gioca_fino_alla_fine(torneo)
    calendario = Calendario()
    calendario.numeri_dei_tornei[torneo.id] = 1
    rapporto = Mondo.rapporto_vuoto(OGGI)
    premiazioni.chiudi(mondo, calendario, torneo, OGGI, rapporto)
    g = mondo.giocatori[1]
    assert torneo.classifica_finale[0] == 1 and rapporto["tuoi_titoli_mondiali"] == 1 and rapporto["mondiali_conclusi"] == 1
    assert f"{g.nome} {g.cognome} è {titolo} d'Italia." in rapporto["notizie"]
    assert [(t["torneo"], t["posto"], t["mondiale"]) for t in g.titoli] == [(nome, 1, True)]


def test_l_albo_conserva_tutto_e_si_legge_dopo(chiusa):
    mondo, calendario, a = chiusa["mondo"], chiusa["calendario"], chiusa["a"]
    albo = calendario.albo
    voce = albo.voci[0]
    assert voce[:8] == [0, "individuale", "m", 1.0, "2026-10-05", 4, 1, 8] and albo.modelli[0] == ["modello_1", "Open maschile del martedì"]
    podio = voce[8]
    assert [p[0] for p in podio] == [1, 5, 3, 4] and podio[3][1] is None
    assert albo.club[podio[0][1]] == [a.nome, a.datetime_creazione_sim.date().isoformat()] and albo.club[podio[1][1]] == ["Club Chiuso", "2020-01-01"]
    # Un secondo torneo con gli stessi club non raddoppia le tabelle.
    prima = (len(albo.club), len(albo.giocatori))
    albo.registra(mondo, chiusa["torneo"], 5)
    assert (len(albo.club), len(albo.giocatori)) == prima and len(albo.voci) == 2
    # Il podio si legge dopo l'uscita del giocatore e la chiusura del club.
    nome = mondo.giocatori[1].nome
    del mondo.giocatori[1]
    mondo.chiudi_polisportiva(a)
    copia = premiazioni.Albo.da_dizionario(albo.a_dizionario())
    assert copia.giocatori["1"][0] == nome and copia.club[podio[0][1]][0] == "PoliTeam01 Prova"
    with pytest.raises(ValueError):
        guasto = albo.a_dizionario()
        guasto["giocatori"].pop("1")
        premiazioni.Albo.da_dizionario(guasto)
