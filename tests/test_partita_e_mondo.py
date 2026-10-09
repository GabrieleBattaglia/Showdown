"""
Test della facciata del motore di partita, che non stampa nulla, e del mondo che avanza col tempo.
Dalla tappa 9 la cronaca su file sta nella cartella cronache, una partita per file, e la partita si
può giocare senza registrarla. Dal 2026-10-08 ogni giocatore gioca al massimo un'amichevole per giorno
simulato, nella facciata e nell'interfaccia testuale.
"""

import datetime
import random
import re

import pytest

import cli
import infortuni as modulo_infortuni
import testi
import valore
from costanti import (
    CARTELLA_CRONACHE,
    COSTANZA_PER_PARTITA,
    DECADIMENTO_COSTANZA,
    ESPERIENZA_PER_AMICHEVOLE,
    ESPERIENZA_PER_ANNO_DI_VITA,
    ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA,
    MODALITA_OUTPUT_CONSOLE,
    MODALITA_OUTPUT_FILE,
    SOGLIA_SPESA_AUTONOMI,
)
from mondo import Mondo
from motore import Squadra
from partita import MotorePartita
from utilita import in_ora_locale

INIZIO = datetime.datetime(2026, 1, 1, 12, 0)
# L'istante reale dell'ultimo avanzamento, che il mondo conta in UTC.
ANCORA = datetime.datetime(2026, 1, 1, 11, 0, tzinfo=datetime.UTC)


@pytest.fixture
def mondo():
    random.seed(4242)
    m = Mondo()
    m.datetime_corrente_simulazione = INIZIO
    m.crea_giocatori_casuali(40, INIZIO)
    return m


def test_mondo_senza_notifica_non_stampa(mondo, capsys):
    assert len(mondo.giocatori) == 40
    assert sorted(mondo.giocatori) == list(range(1, 41))
    assert capsys.readouterr().out == ""


def test_partita_silenziosa_e_coerente(mondo, capsys):
    motore = MotorePartita(mondo)
    g1, g2 = mondo.giocatori[1], mondo.giocatori[2]
    g1.infortunato = g2.infortunato = False
    risultato = motore.gioca_partita(1, 2, 5)
    assert capsys.readouterr().out == ""
    assert risultato["error"] is None
    assert {risultato["vincitore_id"], risultato["perdente_id"]} == {1, 2}
    vinti_dal_primo = sum(1 for a, b in risultato["punteggio_set"] if a > b)
    vinti_dal_secondo = len(risultato["punteggio_set"]) - vinti_dal_primo
    assert max(vinti_dal_primo, vinti_dal_secondo) == 3
    assert (vinti_dal_primo == 3) == (risultato["vincitore_id"] == 1)
    for a, b in risultato["punteggio_set"]:
        assert max(a, b) >= 11
    vincitore = mondo.giocatori[risultato["vincitore_id"]]
    assert vincitore.partitevinte == 1
    assert vincitore.punti_allenamento > 0


def test_partita_con_mostra_e_cronaca_su_file(mondo, cartella_di_prova):
    righe = []
    for g in mondo.giocatori.values():
        g.infortunato = False
    g3, g4 = mondo.giocatori[3], mondo.giocatori[4]
    MotorePartita(mondo, mostra=righe.append).gioca_partita(3, 4, 3, MODALITA_OUTPUT_FILE)
    assert righe[0] == f"Inizio dell'incontro: {g3.cognome} contro {g4.cognome}, al meglio dei 3 set."
    assert righe[-1].startswith("Fine dell'incontro: vince ")
    assert any(r.startswith("Cronaca completa salvata in:") for r in righe)
    cronache = list((cartella_di_prova / CARTELLA_CRONACHE).iterdir())
    assert len(cronache) == 1 and cronache[0].name.endswith(f" {g3.cognome} contro {g4.cognome}.txt")
    testo = cronache[0].read_text(encoding="utf-8")
    assert testo.count("Fine dell'incontro: vince ") == 1
    assert "\n\n" not in testo


def test_partita_in_console_un_punto_alla_volta(mondo):
    righe, pause = [], []
    for g in mondo.giocatori.values():
        g.infortunato = False
    risultato = MotorePartita(mondo, mostra=righe.append, pausa=pause.append).gioca_partita(5, 6, 3, MODALITA_OUTPUT_CONSOLE, seme=11)
    assert risultato["error"] is None
    assert len(pause) == risultato["risultato"].incontro.punti_giocati
    assert set(pause) == {"\rUn tasto per il punto successivo.\r"}
    assert righe[-1].startswith("Fine dell'incontro: vince ")
    assert sum(1 for r in righe if r.startswith("Fine dell'incontro")) == 1


def test_partita_interrotta_non_si_registra(mondo):
    for g in mondo.giocatori.values():
        g.infortunato = False
    prima = mondo.giocatori[5].a_dizionario()
    righe = []

    def interrompi(_prompt):
        raise EOFError

    risultato = MotorePartita(mondo, mostra=righe.append, pausa=interrompi).gioca_partita(5, 6, 3, MODALITA_OUTPUT_CONSOLE)
    assert risultato["error"] == "Partita interrotta dall'utente."
    assert righe[-1] == "Partita interrotta dall'utente."
    assert mondo.giocatori[5].a_dizionario() == prima


def test_partita_rifiutata(mondo):
    righe = []
    motore = MotorePartita(mondo, mostra=righe.append)
    assert motore.gioca_partita(1, 1, 3)["error"] == "I giocatori devono essere diversi."
    assert motore.gioca_partita(1, 999, 3)["error"] == "ID giocatore non valido."
    assert righe[-1] == "ERRORE: ID giocatore non valido."
    for g in mondo.giocatori.values():
        g.infortunato = False
    assert motore.gioca_partita(1, 2, 4)["error"] == "Il numero di set deve essere 3 o 5."
    mondo.giocatori[2].infortunato = True
    mondo.giocatori[2].infortunio_sede = "ginocchio"
    assert motore.gioca_partita(1, 2, 3)["error"] == "Uno o entrambi infortunati."


def test_registra_falso_lascia_il_mondo_identico(mondo):
    for g in mondo.giocatori.values():
        g.infortunato = False
    prima = {gid: g.a_dizionario() for gid, g in mondo.giocatori.items()}
    risultato = MotorePartita(mondo).gioca_partita(7, 8, 5, seme=3, registra=False)
    assert risultato["error"] is None and risultato["seme"] == 3
    assert {gid: g.a_dizionario() for gid, g in mondo.giocatori.items()} == prima


def test_stesso_seme_stessa_partita(mondo):
    for g in mondo.giocatori.values():
        g.infortunato = False
    motore = MotorePartita(mondo)
    primo = motore.gioca_partita(9, 10, 3, seme=42, registra=False)
    secondo = motore.gioca_partita(9, 10, 3, seme=42, registra=False)
    assert primo["punteggio_set"] == secondo["punteggio_set"]
    assert primo["risultato"].punti == secondo["risultato"].punti


def test_avanzamento_del_tempo(mondo):
    mondo.datetime_ultimo_run_reale = ANCORA
    eta_prima = {gid: g.eta for gid, g in mondo.giocatori.items()}
    messaggi = []
    mondo.notifica = messaggi.append
    rapporto = mondo.processa_tempo_trascorso(ANCORA + datetime.timedelta(hours=17))
    assert rapporto["ticks"] == rapporto["giorni"] == 2
    assert mondo.datetime_corrente_simulazione == INIZIO + datetime.timedelta(days=2)
    # L'ora che avanza resta per la volta dopo.
    assert mondo.datetime_ultimo_run_reale == ANCORA + datetime.timedelta(hours=16)
    for gid, eta in eta_prima.items():
        if gid not in mondo._ids_morti_processati_sessione:
            assert mondo.giocatori[gid].eta == eta + 2
    # I nuovi della sessione restano, quelli di prima compresi: si contano i nati nei due giorni.
    assert 2 <= len([gid for gid in mondo.nuovi_giocatori_sessione if gid not in eta_prima]) <= 14
    assert any("Processando 2 tick" in m for m in messaggi)


def test_niente_avanzamento_prima_di_otto_ore(mondo):
    mondo.datetime_ultimo_run_reale = ANCORA
    messaggi = []
    mondo.notifica = messaggi.append
    assert mondo.processa_tempo_trascorso(ANCORA + datetime.timedelta(hours=3))["ticks"] == 0
    assert mondo.datetime_corrente_simulazione == INIZIO
    assert mondo.datetime_ultimo_run_reale == ANCORA
    prossimo = in_ora_locale(ANCORA + datetime.timedelta(hours=8))
    assert messaggi == [f"INFO: Prox aggiornamento sim alle {prossimo:%H:%M:%S del %d/%m/%Y} (tra 5h 0m)."]


def test_polisportive_del_computer(mondo):
    nome = mondo.crea_polisportiva_cpu(INIZIO)
    assert nome.startswith("PoliTeam01 ")
    assert mondo.polisportive[nome].is_cpu_controlled
    assert mondo.crea_polisportiva_cpu(INIZIO).startswith("PoliTeam02 ")
    tesserati, svincolati, comprati = mondo._esegui_logica_cpu_polisportive()
    assert svincolati == comprati == 0
    assert tesserati == sum(len(p.tesserati) for p in mondo.polisportive.values())
    for p in mondo.polisportive.values():
        for gid in p.tesserati:
            assert mondo.giocatori[gid].appartenenza == p.nome


def test_amichevole_registrata_e_cronaca_salvata(mondo, cartella_di_prova):
    for g in mondo.giocatori.values():
        g.infortunato = False
    motore = MotorePartita(mondo)
    risultato = motore.gioca_amichevole(11, 12, set_al_meglio=5, seme=8)
    assert risultato.eventi and risultato.momenti and risultato.registrazione[0].startswith("Punti allenamento: ")
    assert mondo.giocatori[11].partitevinte + mondo.giocatori[11].partiteperse == 1
    percorso = motore.salva_cronaca(risultato)
    assert percorso.startswith(str(cartella_di_prova / CARTELLA_CRONACHE))
    testo = testi.cronaca_amichevole(risultato, motore.nomi(risultato), "normale")
    assert testo.startswith("Inizio dell'incontro: ") and testo.count("Battuta ") == risultato.incontro.punti_giocati
    with pytest.raises(ValueError, match=r"I giocatori devono essere diversi\."):
        motore.gioca_amichevole(11, 11)
    with pytest.raises(ValueError, match="3 o 5"):
        motore.gioca_amichevole(13, 14, set_al_meglio=4)
    uomini = [g for g in mondo.giocatori.values() if g.sesso == "m"][:4]
    donne = [g for g in mondo.giocatori.values() if g.sesso == "f"][:2]
    prima = {gid: g.a_dizionario() for gid, g in mondo.giocatori.items()}
    squadre = motore.gioca_squadre(Squadra("Leoni", (uomini[0], uomini[1], donne[0])), Squadra("Tigri", (uomini[2], donne[1], uomini[3])), seme=2)
    assert max(squadre.set[0]) >= 31 and squadre.eventi is None
    assert {gid: g.a_dizionario() for gid, g in mondo.giocatori.items()} == prima
    # La cronaca di una gara a squadre giocata in modalità completa si salva col nome delle squadre.
    completa = motore.gioca_squadre(Squadra("Leoni", (uomini[0], uomini[1], donne[0])), Squadra("Tigri", (uomini[2], donne[1], uomini[3])), seme=2, dettaglio="completo")
    assert completa.nomi_squadre == ("Leoni", "Tigri")
    percorso = motore.salva_cronaca(completa)
    assert percorso.startswith(str(cartella_di_prova / CARTELLA_CRONACHE)) and percorso.endswith("Leoni contro Tigri.txt")
    with open(percorso, encoding="utf-8") as f:
        cronaca = f.read()
    assert "Inizio della gara a squadre: Leoni contro Tigri" in cronaca and "L'arbitro legge le formazioni: Leoni con " in cronaca


def test_un_amichevole_al_giorno(mondo):
    for g in mondo.giocatori.values():
        g.infortunato = False
    motore = MotorePartita(mondo)
    motore.gioca_amichevole(11, 12, seme=1)
    assert mondo.giocatori[11].ultima_amichevole == mondo.giocatori[12].ultima_amichevole == INIZIO
    g11 = mondo.giocatori[11]
    atteso = f"Oggi {g11.nome} {g11.cognome} ha già giocato un'amichevole: se ne gioca al massimo una per giorno simulato."
    assert motore.problema_amichevole(11, 13) == atteso
    assert "hanno già giocato" in motore.problema_amichevole(12, 11)
    with pytest.raises(ValueError, match="già giocato"):
        motore.gioca_amichevole(13, 11)
    assert motore.gioca_partita(13, 12, 3)["error"].startswith("Oggi ")
    disponibili = motore.disponibili(mondo.giocatori.values())
    assert [g.id for g in disponibili] == sorted(gid for gid in mondo.giocatori if gid not in (11, 12))
    # Una partita non registrata, o di un torneo, non conta come amichevole e non la impedisce.
    assert motore.gioca_partita(11, 13, 3, registra=False)["error"] is None
    assert mondo.giocatori[13].ultima_amichevole is None
    assert motore.gioca_partita(11, 13, 3, info_torneo={"nome": "Coppa"})["error"] is None
    assert mondo.giocatori[13].ultima_amichevole is None
    # Il giorno simulato dopo si gioca di nuovo; gli infortuni di queste partite non contano qui.
    for g in mondo.giocatori.values():
        g.infortunato, g.infortunio_sede = False, None
    mondo.datetime_corrente_simulazione = INIZIO + datetime.timedelta(days=1)
    assert motore.problema_amichevole(11, 12) is None
    assert motore.gioca_partita(11, 12, 3)["error"] is None
    assert mondo.giocatori[11].ultima_amichevole == INIZIO + datetime.timedelta(days=1)


def test_l_interfaccia_testuale_rifiuta_chi_ha_gia_giocato(mondo, monkeypatch, capsys):
    for g in mondo.giocatori.values():
        g.infortunato = False
    mondo.giocatori[7].ultima_amichevole = INIZIO
    interfaccia = cli.InterfacciaTestuale(mondo)
    monkeypatch.setattr(cli, "dgt", lambda *a, **k: 7)
    assert interfaccia._giocatore_per_partita("ID Giocatore 1? ") is None
    assert "oggi" in capsys.readouterr().out
    monkeypatch.setattr(cli, "dgt", lambda *a, **k: 8)
    assert interfaccia._giocatore_per_partita("ID Giocatore 1? ") == 8



# Tappa 11, decisione D31: i punti di un incontro, il premio al più debole, l'esperienza e la
# costanza della registrazione, e l'allenamento quotidiano del mondo.

def test_i_punti_a_tre_e_a_cinque_set():
    assert MotorePartita.punti_della_partita(2, 0) == (4.0, 2.0)
    assert MotorePartita.punti_della_partita(2, 1) == (4.0, 2.5)
    assert MotorePartita.punti_della_partita(3, 0) == (4.5, 2.0)
    assert MotorePartita.punti_della_partita(3, 2) == (4.5, 3.0)
    # Fra due giocatori alla pari: al meglio dei 3 la metà degli incontri finisce 2 a 1, al meglio
    # dei 5 tre ottavi 3 a 1 e tre ottavi 3 a 2. Al meglio dei 5 al massimo il 15 per cento in più.
    tre = (sum(MotorePartita.punti_della_partita(2, 0)) + sum(MotorePartita.punti_della_partita(2, 1))) / 4
    cinque = (2 * sum(MotorePartita.punti_della_partita(3, 0)) + 3 * sum(MotorePartita.punti_della_partita(3, 1)) + 3 * sum(MotorePartita.punti_della_partita(3, 2))) / 16
    assert 1.0 < cinque / tre <= 1.15


def _alla_pari(mondo, *ids):
    for gid in ids:
        g = mondo.giocatori[gid]
        g.infortunato = False
        g.infortunio_sede = None


def test_il_premio_al_piu_debole_anche_quando_perde(mondo):
    _alla_pari(mondo, 1, 2)
    forte, debole = mondo.giocatori[1], mondo.giocatori[2]
    for nome in ("difesa_allenata", "chiusurasx_allenata", "chiusuradx_allenata"):
        setattr(forte, nome, 15.0)
    forte.aggiorna_icv()
    assert valore.somma_pesata(forte) - valore.somma_pesata(debole) >= 25.0
    assert MotorePartita.piu_debole(forte, debole) is debole
    assert MotorePartita.piu_debole(debole, debole) is None
    motore = MotorePartita(mondo)
    risultato = motore.gioca_partita(1, 2, 3, seme=5)
    vinti = max(sum(1 for a, b in risultato["punteggio_set"] if a > b), sum(1 for a, b in risultato["punteggio_set"] if b > a))
    persi = len(risultato["punteggio_set"]) - vinti
    pa_vinc, pa_perd = MotorePartita.punti_della_partita(vinti, persi)
    if risultato["vincitore_id"] == 1:
        assert (forte.punti_allenamento, debole.punti_allenamento) == (pa_vinc, pa_perd + 1.0)
    else:
        assert (debole.punti_allenamento, forte.punti_allenamento) == (pa_vinc + 1.0, pa_perd)


def test_l_amichevole_porta_esperienza_e_costanza(mondo):
    _alla_pari(mondo, 3, 4)
    g = mondo.giocatori[3]
    g.costanza = 0.5
    MotorePartita(mondo).gioca_partita(3, 4, 3)
    assert g.esperienza == pytest.approx(ESPERIENZA_PER_AMICHEVOLE)
    assert g.costanza == pytest.approx(0.5 + (1 - DECADIMENTO_COSTANZA) * COSTANZA_PER_PARTITA)
    assert g.ultima_amichevole == mondo.datetime_corrente_simulazione


def test_gli_agganci_di_torneo_e_sfida(mondo):
    _alla_pari(mondo, 5, 6, 7, 8)
    motore = MotorePartita(mondo)
    torneo = motore.gioca_partita(5, 6, 3, info_torneo={"nome": "prova"}, seme=3)["risultato"]
    g5 = mondo.giocatori[5]
    assert g5.ultima_amichevole is None and g5.esperienza == pytest.approx(0.01)
    assert g5.punti_allenamento >= 2.0 + 3.0
    assert mondo.giocatori[5].diario[0]["testo"].startswith(("Vince la partita del torneo", "Perde la partita del torneo"))
    del torneo
    incontro = motore.gioca_partita(7, 8, 3, seme=4, registra=False)["risultato"]
    frasi = motore.registra(incontro, sfida=True)
    assert frasi[0].startswith("Punti allenamento: ")
    g7 = mondo.giocatori[7]
    assert g7.ultima_amichevole is None and g7.esperienza == pytest.approx(0.006)
    assert g7.punti_allenamento >= 2.0 + 2.0 and g7.diario[0]["testo"].startswith(("Vince la sfida", "Perde la sfida"))


def test_la_frase_dei_punti_con_la_virgola(mondo):
    from partita import _punti
    assert (_punti(4.0), _punti(2.5), _punti(5.0)) == ("4", "2,5", "5")
    _alla_pari(mondo, 9, 10)
    incontro = MotorePartita(mondo).gioca_partita(9, 10, 3, registra=False)["risultato"]
    frase = MotorePartita(mondo).registra(incontro)[0]
    assert re.fullmatch(r"Punti allenamento: \d+(,5)? a .+, \d+(,5)? a .+\.", frase)


def _giorno(mondo):
    """Il mondo va avanti di un giorno simulato, con il suo rapporto."""
    data = mondo.datetime_corrente_simulazione + datetime.timedelta(days=1)
    mondo.datetime_corrente_simulazione = data
    rapporto = Mondo.rapporto_vuoto(data)
    mondo._allenamento_del_giorno(data, rapporto)
    return rapporto


def test_la_seduta_secondo_l_intensita_e_la_meta_ai_liberi(mondo, monkeypatch):
    mia = mondo.fonda_polisportiva("Club della seduta")
    cpu = mondo.polisportive[mondo.crea_polisportiva_cpu(INIZIO)]
    for gid in (1, 2, 3):
        mondo._tessera(mia, mondo.giocatori[gid])
    mondo._tessera(cpu, mondo.giocatori[4])
    for gid in range(1, 6):
        g = mondo.giocatori[gid]
        g.infortunato = False
        g.infortunio_sede = None
        g.punti_allenamento = g.costanza = g.esperienza = 0.0
    mondo.giocatori[1].intensita = "leggera"
    mondo.giocatori[3].intensita = "intensa"
    fermo = mondo.giocatori[6]
    fermo.infortunato, fermo.infortunio_sede, fermo.punti_allenamento, fermo.costanza = True, "ginocchio", 0.0, 1.0
    fermo.infortunio_fine_datetime = INIZIO + datetime.timedelta(days=99)
    _giorno(mondo)
    resto = 1 - DECADIMENTO_COSTANZA
    assert [mondo.giocatori[gid].punti_allenamento for gid in range(1, 6)] == pytest.approx([0.6, 1.0, 1.4, 1.0, 0.5])
    assert [mondo.giocatori[gid].costanza for gid in range(1, 6)] == pytest.approx([0.6 * resto, resto, 1.3 * resto, resto, 0.5 * resto])
    assert fermo.punti_allenamento == 0.0 and fermo.costanza == pytest.approx(DECADIMENTO_COSTANZA)
    libero = mondo.giocatori[5]
    assert libero.esperienza == pytest.approx(ESPERIENZA_PER_ANNO_DI_VITA / 108)
    assert mondo.giocatori[2].esperienza == pytest.approx(ESPERIENZA_PER_ANNO_DI_VITA / 108 + ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA)
    # A regime la costanza della seduta vale la costanza della sua intensità, anche 1,3 per l'intensa,
    # risposta 7 di Gabriele. Senza infortuni in seduta, che hanno le loro prove in test_infortuni:
    # qui _giorno non fa guarire nessuno, e l'intenso infortunato smetterebbe di allenarsi.
    monkeypatch.setattr(modulo_infortuni, "infortunio_in_seduta", lambda *_a, **_k: None)
    for _ in range(300):
        _giorno(mondo)
    assert not any(mondo.giocatori[gid].infortunato for gid in (1, 2, 3, 5))
    assert [round(mondo.giocatori[gid].costanza, 3) for gid in (1, 2, 3, 5)] == [0.6, 1.0, 1.3, 0.5]


def test_liberi_e_computer_spendono_da_soli_i_tuoi_no(mondo):
    mia = mondo.fonda_polisportiva("Club della spesa")
    cpu = mondo.polisportive[mondo.crea_polisportiva_cpu(INIZIO)]
    mondo._tessera(mia, mondo.giocatori[1])
    mondo._tessera(cpu, mondo.giocatori[2])
    for gid in (1, 2, 3):
        g = mondo.giocatori[gid]
        g.infortunato = False
        g.infortunio_sede = None
        g.punti_allenamento = SOGLIA_SPESA_AUTONOMI + 5.0
    prima = {gid: mondo.giocatori[gid].indice_collettivo_valore for gid in (1, 2, 3)}
    rapporto = _giorno(mondo)
    assert rapporto["autoallenati"] == 2
    assert mondo.giocatori[1].punti_allenamento > SOGLIA_SPESA_AUTONOMI
    assert mondo.giocatori[2].punti_allenamento == 0.0 and mondo.giocatori[3].punti_allenamento == 0.0
    assert mondo.giocatori[2].indice_collettivo_valore > prima[2] and mondo.giocatori[3].indice_collettivo_valore > prima[3]
    assert not any("spesa" in voce for voce in mondo.giocatori[3].diario)


def test_il_primo_del_mese_calano_i_livelli_alti(mondo):
    g = mondo.giocatori[1]
    g.difesa_allenata = 40.0 - g.difesa_base - 0.5
    g.attacco_allenata = 1.0
    mondo.datetime_corrente_simulazione = datetime.datetime(2026, 2, 28, 12, 0)
    mondo._mantenimento_del_mese(datetime.datetime(2026, 3, 1, 12, 0))
    assert g.difesa_allenata < 40.0 - g.difesa_base - 0.5
    assert g.attacco_allenata == 1.0 or g.apprendista_rapido
