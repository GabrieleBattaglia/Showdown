"""
Le prove del motore della finestra unica Mercato e ricerca, issue 8 e decisione D36: chi cercare con le
caselle, che si sommano; i filtri dei controlli e di Altri filtri, con quelli che non contano e quelli che
si escludono a vicenda; gli ordini con la direzione nel nome; le tredici ricerche pronte e lo stato di ogni
porta d'ingresso; la funzione che dice di chi è una polisportiva; la memoria di classe e valore di mercato;
le funzioni pure che dicono, per ogni riga, quale offerta si può fare, se si gioca un'amichevole o si sfida
il club, o perché no; e i testi della finestra, la riga, la Situazione a blocchi e Filtri attivi.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nascono il 24 ottobre 2026 coi passi 2 e 3 della proposta della issue 8.
"""

import datetime
import random
import re

import pytest

import classe
import economia
import luoghi
import mercato
import staff
import testi
from costanti import ANNO_SIMULAZIONE_GIORNI, LIMITE_MOVIMENTI_PER_TICK
from mondo import Mondo

ORA = datetime.datetime(2026, 10, 6, 18, 0)


@pytest.fixture
def mondo():
    """
    Un mondo di 120 giocatori: due polisportive tue, Pat-Bologna attiva con cinque tesserati e Pat-Milano con
    quattro, due del computer con dodici e otto; in vendita uno del computer, uno di Pat-Milano a 1 euro e uno
    di Pat-Bologna; cinque ritirati, uno uscito di scena; sei allenatori, uno nello staff del computer, uno
    nel tuo, gli altri liberi.
    """
    random.seed(808)
    m = Mondo()
    m.datetime_corrente_simulazione = ORA
    m.crea_giocatori_casuali(120, ORA, annuncia=False)
    m.nuovi_giocatori_sessione = list(range(100, 121))
    mia = m.fonda_polisportiva("Pat-Bologna", luogo="Bologna")
    altra = m.fonda_polisportiva("Pat-Milano", attiva=False, luogo="Milano")
    cpu = [m.polisportive[m.crea_polisportiva_cpu(ORA)] for _ in range(2)]
    for gid in range(1, 6):
        m._entra(mia, m.giocatori[gid])
    for gid in range(6, 10):
        m._entra(altra, m.giocatori[gid])
    for gid in range(10, 22):
        m._entra(cpu[0], m.giocatori[gid])
    for gid in range(22, 30):
        m._entra(cpu[1], m.giocatori[gid])
    cpu[0].in_vendita[10] = 3000
    altra.in_vendita[6] = 1
    mia.in_vendita[1] = 500
    for gid in range(40, 45):
        m.giocatori[gid].ritirato = True
    m._ids_morti_processati_sessione.add(45)
    m.giocatori[45].ritirato = True
    rng = random.Random(9)
    allenatori = [m._nasce_un_allenatore(ORA, rng) for _ in range(6)]
    m.assumi_allenatore(cpu[0], allenatori[0], 0, ORA)
    m.assumi_allenatore(mia, allenatori[1], 1, ORA)
    return m


def _cpu(m, posto=0):
    return sorted((p for p in m.polisportive.values() if p.is_cpu_controlled), key=lambda p: p.nome)[posto]


def _ids(righe):
    return {r.persona.id for r in righe}


def _cerca(m, **campi):
    return mercato.cerca(m, mercato.Filtri(**campi))


def _accessibile(testo):
    assert testo and "\n\n" not in testo
    for riga in testo.splitlines():
        assert riga.strip(), "riga vuota"
        assert not re.search(r"(-{3,}|={3,}|_{3,})", riga), riga


# Di chi è una polisportiva.

def test_una_funzione_sola_dice_di_chi_e_una_polisportiva(mondo):
    mia, altra = mondo.polisportive["Pat-Bologna"], mondo.polisportive["Pat-Milano"]
    assert mercato.di_chi(mondo, mia) == mercato.TUA_ATTIVA and mercato.di_chi(mondo, altra) == mercato.TUA_ALTRA
    assert mercato.di_chi(mondo, _cpu(mondo)) == mercato.DEL_COMPUTER and mercato.di_chi(mondo, None) is None
    mondo.miapolisportiva_attiva = altra
    assert mercato.di_chi(mondo, mia) == mercato.TUA_ALTRA and mercato.di_chi(mondo, altra) == mercato.TUA_ATTIVA


# Chi cercare.

def test_le_caselle_di_chi_cercare_si_sommano(mondo):
    cpu0, cpu1 = _cpu(mondo, 0), _cpu(mondo, 1)
    morti = mondo._ids_morti_processati_sessione
    liberi = {gid for gid, g in mondo.giocatori.items() if g.appartenenza == "*" and not g.ritirato and gid not in morti}
    assert _ids(_cerca(mondo, liberi=True)) == liberi
    # In vendita da altri: soltanto chi vende una polisportiva che non è tua, dalle liste in_vendita.
    in_vendita = _cerca(mondo, in_vendita=True)
    assert [(r.persona.id, r.stato, r.polisportiva, r.prezzo, r.costo) for r in in_vendita] == [(10, mercato.IN_VENDITA, cpu0, 3000, 3000)]
    computer = _cerca(mondo, del_computer=True)
    assert _ids(computer) == set(cpu0.tesserati) | set(cpu1.tesserati)
    assert next(r for r in computer if r.persona.id == 10).stato == mercato.IN_VENDITA
    assert all(r.stato == mercato.DEL_COMPUTER and r.costo == economia.valore_di_mercato(r.persona, ORA) for r in computer if r.persona.id != 10)
    tuoi = _cerca(mondo, tuoi=True)
    assert _ids(tuoi) == set(range(1, 10)) and all(r.stato == mercato.TUO for r in tuoi)
    assert _ids(_cerca(mondo, ritirati=True)) == set(range(40, 45))
    assert _ids(_cerca(mondo, ritirati=True, comprendi_usciti=True)) == {*range(40, 45), 45}
    assert _cerca(mondo) == []
    tutte = _cerca(mondo, liberi=True, in_vendita=True, del_computer=True, tuoi=True, ritirati=True, comprendi_usciti=True)
    assert len(tutte) == len(_ids(tutte)) == len(mondo.giocatori)


def test_chi_e_in_vendita_si_legge_dalle_liste_e_va_controllato(mondo):
    cpu0 = _cpu(mondo, 0)
    # Un venduto rimasto in lista, un uscito di scena e un ritirato non si comprano.
    cpu0.in_vendita[60] = 10
    cpu0.in_vendita[45] = 10
    cpu0.in_vendita[40] = 10
    assert _ids(_cerca(mondo, in_vendita=True)) == {10}


def test_costi_e_stipendi_delle_righe(mondo):
    mia = mondo.miapolisportiva_attiva
    libero = next(r for r in _cerca(mondo, liberi=True))
    assert libero.costo == economia.ingaggio_richiesto(libero.persona, mia) and libero.stipendio == economia.stipendio(libero.persona)
    tuoi = {r.persona.id: r for r in _cerca(mondo, tuoi=True)}
    # Da un'altra tua polisportiva oggi si compra al prezzo; dalla attiva no, è già sua.
    assert (tuoi[6].di_chi, tuoi[6].prezzo, tuoi[6].costo) == (mercato.TUA_ALTRA, 1, 1)
    assert (tuoi[1].di_chi, tuoi[1].prezzo, tuoi[1].costo) == (mercato.TUA_ATTIVA, 500, None)
    assert tuoi[2].costo is None and tuoi[2].stipendio == economia.stipendio_pagato(mondo.giocatori[2])
    assert all(r.stipendio is None and r.costo is None for r in _cerca(mondo, ritirati=True))
    mondo.miapolisportiva_attiva = None
    assert all(r.costo is None for r in _cerca(mondo, liberi=True))


# I filtri dei controlli.

def test_nome_cognome_o_numero_come_nella_scelta_del_giocatore(mondo):
    tutti = {"liberi": True, "del_computer": True, "tuoi": True}
    assert _ids(_cerca(mondo, nome="1", **tutti)) == {gid for gid in _ids(_cerca(mondo, **tutti)) if str(gid).startswith("1")}
    g = mondo.giocatori[33]
    trovati = _cerca(mondo, nome=f"  {g.cognome[1:4].upper()} ", **tutti)
    assert 33 in _ids(trovati) and all(g.cognome[1:4].casefold() in f"{r.persona.nome} {r.persona.cognome}".casefold() for r in trovati)
    assert _ids(_cerca(mondo, nome="   ", **tutti)) == _ids(_cerca(mondo, **tutti))


def test_sesso_classe_ed_eta_dei_controlli(mondo):
    tutti = {"liberi": True, "del_computer": True, "tuoi": True, "ritirati": True}
    assert all(r.persona.sesso == "f" for r in _cerca(mondo, sesso="f", **tutti))
    livelli = {gid: classe.classe(g).livello for gid, g in mondo.giocatori.items()}
    soglia = sorted(livelli.values())[60]
    migliori = _cerca(mondo, classe_migliore=soglia, **tutti)
    assert migliori and all(livelli[r.persona.id] <= soglia for r in migliori)
    assert any(livelli[r.persona.id] == soglia for r in migliori)
    # L'età conta gli anni interi, compreso quello scritto.
    mondo.giocatori[50].eta = 20 * ANNO_SIMULAZIONE_GIORNI + ANNO_SIMULAZIONE_GIORNI - 1
    mondo.giocatori[51].eta = 21 * ANNO_SIMULAZIONE_GIORNI
    giovani = _ids(_cerca(mondo, eta_massima=20, **tutti))
    assert 50 in giovani and 51 not in giovani and all(int(mondo.giocatori[gid].eta_anni) <= 20 for gid in giovani)
    anziani = _ids(_cerca(mondo, eta_minima=21, **tutti))
    assert 51 in anziani and 50 not in anziani


def test_il_costo_massimo_conta_soltanto_con_la_polisportiva_attiva(mondo):
    righe = _cerca(mondo, liberi=True, in_vendita=True, tuoi=True, costo_massimo=2000)
    assert all(r.costo is None or r.costo <= 2000 for r in righe)
    # Chi non ha un costo, come i tuoi tesserati non in vendita, con quel limite non c'entra, e resta.
    assert {2, 3, 6} <= _ids(righe) and 10 not in _ids(righe)
    mondo.miapolisportiva_attiva = None
    assert _ids(_cerca(mondo, liberi=True, in_vendita=True, costo_massimo=2000)) == _ids(_cerca(mondo, liberi=True, in_vendita=True))
    assert mercato.non_contano(mercato.Filtri(costo_massimo=2000), None) == [("costo_massimo", "senza_attiva")]


def test_disponibili_oggi_per_un_amichevole(mondo):
    tutti = {"liberi": True, "del_computer": True, "tuoi": True, "ritirati": True, "comprendi_usciti": True}
    mondo.giocatori[60].ultimo_impegno = ORA
    mondo.giocatori[61].infortunato = True
    mondo.giocatori[61].ambidestro = False
    disponibili = _ids(_cerca(mondo, disponibili_oggi=True, **tutti))
    assert 60 not in disponibili and 61 not in disponibili and not disponibili & {*range(40, 46)}
    assert all(mondo.giocatori[gid].puo_giocare_amichevole(ORA) for gid in disponibili)


# Altri filtri.

def test_i_filtri_di_luogo_e_di_polisportiva(mondo):
    tutti = {"liberi": True, "del_computer": True, "tuoi": True}
    g = mondo.giocatori[70]
    provincia, regione = luoghi.provincia_e_regione(g.luogo)
    nella_regione = _cerca(mondo, regione=regione, **tutti)
    assert 70 in _ids(nella_regione) and all(luoghi.provincia_e_regione(r.persona.luogo)[1] == regione for r in nella_regione)
    assert all(luoghi.provincia_e_regione(r.persona.luogo)[0] == provincia for r in _cerca(mondo, provincia=provincia, **tutti))
    assert provincia in luoghi.province(regione) and regione in luoghi.regioni() and luoghi.regione_della_provincia(provincia) == regione
    pezzo = g.luogo[:3].upper()
    assert 70 in _ids(_cerca(mondo, comune=pezzo, **tutti))
    assert luoghi.comuni_che_contengono("forli") >= {"Forlì"}
    club = _cerca(mondo, polisportiva="milano", **tutti)
    assert _ids(club) == set(range(6, 10))


def test_tratti_a_tre_voci_indole_e_soldi(mondo):
    tutti = {"liberi": True, "del_computer": True, "tuoi": True, "ritirati": True}
    insieme = _ids(_cerca(mondo, **tutti))
    mancini = _ids(_cerca(mondo, tratti={"mancino": True}, **tutti))
    destri = _ids(_cerca(mondo, tratti={"mancino": False}, **tutti))
    assert mancini | destri == insieme and not mancini & destri
    assert all(mondo.giocatori[gid].mancino for gid in mancini)
    assert all(mondo.giocatori[gid].maturazione == "precoce" for gid in _ids(_cerca(mondo, tratti={"precoce": True}, **tutti)))
    indole = mondo.giocatori[3].indole
    assert all(mondo.giocatori[gid].indole == indole for gid in _ids(_cerca(mondo, indole=indole, **tutti))) and 3 in _ids(_cerca(mondo, indole=indole, **tutti))
    soglia = sorted(g.indice_collettivo_valore for g in mondo.giocatori.values())[60]
    assert all(r.persona.indice_collettivo_valore >= soglia for r in _cerca(mondo, valore_minimo=soglia, **tutti))
    poveri = _cerca(mondo, stipendio_massimo=300, **tutti)
    assert all(r.stipendio is None or r.stipendio <= 300 for r in poveri) and set(range(40, 45)) <= _ids(poveri)
    assert _ids(_cerca(mondo, mesi_contratto_massimi=1, tuoi=True)) == set()
    assert _ids(_cerca(mondo, mesi_contratto_massimi=60, tuoi=True)) == set(range(1, 10))


def test_salute_carriera_sessione_e_condizioni(mondo):
    tutti = {"liberi": True, "del_computer": True, "tuoi": True, "ritirati": True}
    mondo.giocatori[62].acciacco_fino = ORA + datetime.timedelta(days=4)
    mondo.giocatori[62].acciacco_giorni = 5
    mondo.giocatori[62].acciacco_calo = 0.1
    mondo.giocatori[63].infortunato = True
    sani = _ids(_cerca(mondo, senza_acciacchi=True, **tutti))
    assert 62 not in sani and 63 not in sani and 64 in sani
    # Il ritirato 41 allena: un allenatore nato dal giocatore.
    mondo._ex_giocatore_allenatore(mondo.giocatori[41], None, ORA, rng=random.Random(4))
    assert _ids(_cerca(mondo, solo_ritirati_che_allenano=True, **tutti)) == {41}
    assert _ids(_cerca(mondo, solo_nuovi=True, **tutti)) == {gid for gid in range(100, 121) if gid in _ids(_cerca(mondo, **tutti))}
    soglia = mondo.giocatori[5]._get_valore_totale("bomba_base")
    forti = _cerca(mondo, condizioni=(("bomba_base", "maggiore", soglia),), **tutti)
    assert forti and all(r.persona._get_valore_totale("bomba_base") > soglia for r in forti) and 5 not in _ids(forti)
    assert len(mercato.CRITERI_DELLE_CONDIZIONI) == 30 and "classe" not in mercato.CRITERI_DELLE_CONDIZIONI


def test_gli_allenatori_e_i_loro_filtri(mondo):
    mia, cpu0 = mondo.miapolisportiva_attiva, _cpu(mondo, 0)
    liberi = mercato.cerca(mondo, mercato.Filtri(allenatori=True, liberi=True))
    assert {r.persona.numero for r in liberi} == {a.numero for a in mondo.allenatori.values() if a.libero}
    assert all(r.allenatore and r.stato == mercato.LIBERO and r.stipendio == staff.stipendio_richiesto(r.persona, staff.CAPO) for r in liberi)
    assert [r.persona.livello for r in liberi] == sorted(r.persona.livello for r in liberi)
    computer = mercato.cerca(mondo, mercato.Filtri(allenatori=True, del_computer=True))
    assert [(r.persona.numero, r.polisportiva, r.stato) for r in computer] == [(cpu0.staff[0], cpu0, mercato.DEL_COMPUTER)]
    tuoi = mercato.cerca(mondo, mercato.Filtri(allenatori=True, tuoi=True))
    assert [(r.persona.numero, r.di_chi) for r in tuoi] == [(mia.staff[1], mercato.TUA_ATTIVA)]
    impiegati = {"allenatori": True, "del_computer": True, "tuoi": True}
    assert {r.persona.numero for r in _cerca(mondo, posto_attuale=staff.CAPO, **impiegati)} == {cpu0.staff[0]}
    # In vendita e Ritirati non hanno un equivalente per gli allenatori: non contano, invece di svuotare.
    assert mercato.cerca(mondo, mercato.Filtri(allenatori=True, liberi=True, in_vendita=True, ritirati=True, tratti={"mancino": True})) == liberi
    a = liberi[0].persona
    a.prelazione = "PoliTeam99 Altrove"
    senza = mercato.cerca(mondo, mercato.Filtri(allenatori=True, liberi=True, senza_prelazione_altrui=True))
    assert a.numero not in {r.persona.numero for r in senza}
    a.prelazione = mia.nome
    assert a.numero in {r.persona.numero for r in mercato.cerca(mondo, mercato.Filtri(allenatori=True, liberi=True, senza_prelazione_altrui=True))}
    visus = a.visus
    assert all(r.persona.visus == visus for r in mercato.cerca(mondo, mercato.Filtri(allenatori=True, liberi=True, visus=visus)))
    tipo = mercato.cerca(mondo, mercato.Filtri(allenatori=True, liberi=True, tipo_allenatore=staff.EX))
    assert tipo == []
    tetto = sorted(r.stipendio for r in liberi)[1]
    assert all(r.stipendio <= tetto for r in mercato.cerca(mondo, mercato.Filtri(allenatori=True, liberi=True, stipendio_capo_massimo=tetto)))
    giovani = mercato.cerca(mondo, mercato.Filtri(allenatori=True, liberi=True, ordine_allenatori="eta_giovane"))
    assert [r.persona.eta(ORA) for r in giovani] == sorted(r.persona.eta(ORA) for r in giovani)
    assert all(int(r.persona.eta_anni(ORA)) <= 40 for r in mercato.cerca(mondo, mercato.Filtri(allenatori=True, liberi=True, eta_massima=40)))


# Quelli che non contano e quelli che si escludono a vicenda.

def test_i_filtri_che_non_contano(mondo):
    per_allenatori = mercato.Filtri(allenatori=True, liberi=True, in_vendita=True, costo_massimo=100, tratti={"talento": True}, indole="aggressiva",
                                    condizioni=(("valore", "maggiore", 3),), visus=staff.VEDENTE)
    assert mercato.non_contano(per_allenatori, mondo.miapolisportiva_attiva) == [
        ("in_vendita", "allenatori"), ("costo_massimo", "allenatori"), ("tratti", "allenatori"), ("indole", "allenatori"), ("condizioni", "allenatori")]
    per_giocatori = mercato.Filtri(liberi=True, visus=staff.VEDENTE, posto_attuale=staff.CAPO)
    assert mercato.non_contano(per_giocatori, None) == [("visus", "giocatori"), ("posto_attuale", "giocatori")]
    assert mercato.caselle_che_contano(per_allenatori) == ["liberi"]


def test_i_filtri_che_si_escludono_a_vicenda(mondo):
    contraddittori = mercato.Filtri(liberi=True, ritirati=True, comprendi_usciti=True, disponibili_oggi=True, solo_ritirati_che_allenano=True,
                                    classe_migliore=30, classe_peggiore=50, eta_minima=30, eta_massima=20, tratti={"mancino": True, "ambidestro": True},
                                    polisportiva="team", regione="Lombardia", provincia="Bologna")
    codici = mercato.contraddizioni(contraddittori)
    assert codici == [("disponibili", ["ritirati", "usciti"]), ("allenano", ["liberi", "usciti"]), ("classi", (30, 50)), ("eta", (30, 20)),
                      ("tratti", ("mancino", "ambidestro")), ("polisportiva", ["liberi", "ritirati", "usciti"]), ("luogo", ("Bologna", "Emilia-Romagna"))]
    # Si applicano tutti: l'elenco resta vuoto, e Filtri attivi dice perché.
    assert mercato.cerca(mondo, contraddittori) == []
    assert mercato.contraddizioni(mercato.Filtri(liberi=True, solo_ritirati_che_allenano=True)) == [("allenano", ["liberi"]), ("allenano_senza_ritirati", None)]
    assert mercato.contraddizioni(mercato.Filtri(allenatori=True, liberi=True, posto_attuale=staff.CAPO, disponibili_oggi=True)) == [("posto", None)]
    assert mercato.in_fondo(mercato.Filtri(liberi=True, tuoi=True, ordine="costo_basso"), None) == ["liberi", "tuoi"]
    assert mercato.in_fondo(mercato.Filtri(liberi=True, tuoi=True, ordine="costo_basso"), mondo.miapolisportiva_attiva) == ["tuoi"]
    assert mercato.in_fondo(mercato.Filtri(liberi=True, ordine="valore_alto"), None) == []


# Gli ordini.

def test_ogni_ordine_ha_la_direzione_nel_nome_e_a_parita_decide_il_numero(mondo):
    assert len(mercato.ORDINI_GIOCATORI) == 17 + 24 and len({chiave for chiave, _nome in mercato.ORDINI_GIOCATORI}) == 41
    assert all(", dal" in nome or ", dalla" in nome or ", dai" in nome for _chiave, nome in (*mercato.ORDINI_GIOCATORI, *mercato.ORDINI_ALLENATORI))
    tutti = {"liberi": True, "in_vendita": True, "del_computer": True, "tuoi": True, "ritirati": True}
    memoria = mercato.Memoria(mondo)
    for chiave, _nome in mercato.ORDINI_GIOCATORI:
        righe = mercato.cerca(mondo, mercato.Filtri(ordine=chiave, **tutti), memoria)
        assert len(righe) == len(_ids(righe)) == len(mercato.cerca(mondo, mercato.Filtri(**tutti), memoria)), chiave
    valori = [r.persona.indice_collettivo_valore for r in _cerca(mondo, ordine="valore_basso", **tutti)]
    assert valori == sorted(valori)
    bombe = [r.persona._get_valore_totale("bomba_base") for r in _cerca(mondo, ordine="bomba_base", **tutti)]
    assert bombe == sorted(bombe, reverse=True)
    classi = [memoria.punteggio(r.persona) for r in _cerca(mondo, ordine="classe", **tutti)]
    assert classi == sorted(classi, reverse=True)
    # Negli ordini per costo chi non ne ha uno va in fondo, sia dal più basso sia dal più alto.
    for chiave in mercato.ORDINI_DEL_COSTO:
        costi = [r.costo for r in _cerca(mondo, ordine=chiave, **tutti)]
        primo_senza = costi.index(None)
        assert all(c is None for c in costi[primo_senza:]) and all(c is not None for c in costi[:primo_senza]), chiave
    alti = [r.costo for r in _cerca(mondo, ordine="costo_alto", **tutti) if r.costo is not None]
    assert alti == sorted(alti, reverse=True)
    euro = [r.costo / r.persona.indice_collettivo_valore for r in _cerca(mondo, ordine="euro_per_punto", liberi=True)]
    assert euro == sorted(euro)
    # A parità decide il numero; per i punti della classifica nazionale prima ori, argenti e bronzi.
    mondo.giocatori[70].punti_mondiali = mondo.giocatori[71].punti_mondiali = 50.0
    mondo.giocatori[71].ori = 1
    titolati = [r.persona.id for r in _cerca(mondo, ordine="punti_nazionali", **tutti)]
    assert titolati[:2] == [71, 70]
    stessi = [r.persona.id for r in _cerca(mondo, ordine="punti_anno", **tutti)]
    assert stessi == sorted(stessi)
    assert [r.persona.id for r in _cerca(mondo, ordine="numero", **tutti)] == sorted(_ids(_cerca(mondo, **tutti)))
    contratti = _cerca(mondo, ordine="mesi_contratto", liberi=True, tuoi=True)
    assert all(r.stato == mercato.TUO for r in contratti[:9]) and all(r.stato == mercato.LIBERO for r in contratti[9:])


# Le ricerche pronte e le porte d'ingresso.

def test_le_tredici_ricerche_pronte(mondo):
    assert len(mercato.PRONTE) == 13 and mercato.PRONTE[0][0] == mercato.TORNA_AI_TUOI
    for chiave, _nome in mercato.PRONTE[1:]:
        filtri = mercato.filtri_della_pronta(chiave)
        assert mercato.caselle_che_contano(filtri), chiave
        assert mercato.contraddizioni(filtri) == [] and mercato.non_contano(filtri, mondo.miapolisportiva_attiva) == [], chiave
        assert filtri.ordine_scelto in dict(mercato.ORDINI_ALLENATORI if filtri.allenatori else mercato.ORDINI_GIOCATORI), chiave
        mercato.cerca(mondo, filtri)
    assert mercato.filtri_della_pronta("mercato") == mercato.Filtri(liberi=True, in_vendita=True)
    assert mercato.filtri_della_pronta("giovani_migliori").eta_massima == mercato.ETA_DEI_GIOVANI == 20
    avversari = mercato.filtri_della_pronta("avversari_amichevole")
    assert avversari.disponibili_oggi and avversari.tuoi and avversari.ordine == "classe"
    capi = mercato.cerca(mondo, mercato.filtri_della_pronta("capi_migliori"))
    assert [r.persona.numero for r in capi] == [_cpu(mondo).staff[0]]
    with pytest.raises(KeyError):
        mercato.filtri_della_pronta(mercato.TORNA_AI_TUOI)


def test_torna_ai_tuoi_filtri_rimette_quelli_fatti_a_mano(mondo):
    stato = mercato.stato_predefinito("ricerca")
    assert stato.pronta == "tutti_in_attivita" and stato.a_mano is None
    assert mercato.TORNA_AI_TUOI not in dict(mercato.pronte_disponibili(stato))
    # Dalla pronta d'ingresso a un'altra non c'è niente fatto a mano da rimettere.
    stato = mercato.con_la_pronta(stato, "piu_forti")
    assert stato.a_mano is None and mercato.TORNA_AI_TUOI not in dict(mercato.pronte_disponibili(stato))
    a_mano = mercato.Filtri(liberi=True, sesso="f", eta_massima=25)
    stato = mercato.con_la_pronta(mercato.fatti_a_mano(a_mano), "mercato")
    assert stato.filtri == mercato.filtri_della_pronta("mercato") and stato.a_mano == a_mano
    stato = mercato.con_la_pronta(stato, "piu_titolati")
    assert stato.a_mano == a_mano and mercato.pronte_disponibili(stato)[0] == (mercato.TORNA_AI_TUOI, "Torna ai tuoi filtri")
    tornato = mercato.con_la_pronta(stato, mercato.TORNA_AI_TUOI)
    assert tornato.filtri == a_mano and tornato.pronta is None and tornato.a_mano is None
    with pytest.raises(ValueError):
        mercato.con_la_pronta(tornato, mercato.TORNA_AI_TUOI)
    a_mano.sesso = "m"
    assert stato.a_mano.sesso == "f" and tornato.filtri.sesso == "f"


def test_ogni_porta_d_ingresso_ha_il_suo_stato_nel_mondo(mondo):
    assert mercato.PORTE == ("mercato", "allenatori", "ricerca", "amichevole")
    for porta in mercato.PORTE:
        stato = mercato.stato_della_porta(mondo, porta)
        assert stato == mercato.stato_predefinito(porta) and stato.filtri == mercato.filtri_della_pronta(mercato.PRONTA_DELLA_PORTA[porta])
    assert mercato.stato_della_porta(mondo, "allenatori").filtri.allenatori
    cambiato = mercato.fatti_a_mano(mercato.Filtri(liberi=True, sesso="f"))
    mercato.ricorda_la_porta(mondo, "mercato", cambiato)
    cambiato.filtri.sesso = "m"
    assert mercato.stato_della_porta(mondo, "mercato").filtri.sesso == "f"
    assert mercato.stato_della_porta(mondo, "ricerca") == mercato.stato_predefinito("ricerca")
    letto = mercato.stato_della_porta(mondo, "mercato")
    letto.filtri.sesso = "m"
    assert mondo.filtri_di_ricerca["mercato"].filtri.sesso == "f"
    with pytest.raises(KeyError):
        mercato.ricorda_la_porta(mondo, "altrove", cambiato)


def test_altri_filtri_si_contano_e_si_azzerano():
    filtri = mercato.Filtri(liberi=True, sesso="f", classe_peggiore=40, tratti={"mancino": True, "talento": False}, comune=" ",
                            condizioni=(("valore", "maggiore", 3),), visus=staff.VEDENTE)
    assert mercato.quanti_altri_filtri(filtri) == 5
    azzerati = mercato.azzera_altri(filtri)
    assert mercato.quanti_altri_filtri(azzerati) == 0 and azzerati.sesso == "f" and azzerati.liberi and filtri.tratti == {"mancino": True, "talento": False}


# La memoria della finestra.

def test_la_memoria_calcola_la_classe_una_volta_sola(mondo, monkeypatch):
    chiamate = []
    vero = classe.punteggio
    monkeypatch.setattr(classe, "punteggio", lambda g: chiamate.append(g.id) or vero(g))
    memoria = mercato.Memoria(mondo)
    tutti = mercato.Filtri(liberi=True, del_computer=True, tuoi=True, classe_migliore=60, ordine="classe")
    prima = mercato.cerca(mondo, tutti, memoria)
    assert len(chiamate) == len(set(chiamate))
    quante = len(chiamate)
    assert mercato.cerca(mondo, tutti, memoria) == prima and len(chiamate) == quante
    g = mondo.giocatori[12]
    assert memoria.livello(g) == classe.classe(g).livello and memoria.codice(g) == classe.classe(g).codice
    assert memoria.valore_di_mercato(g) == economia.valore_di_mercato(g, ORA)
    memoria.dimentica(g)
    quante = len(chiamate)
    memoria.livello(g)
    memoria.codice(g)
    assert len(chiamate) == quante + 1


def test_dopo_un_ricalcolo_resta_la_stessa_persona(mondo):
    righe = _cerca(mondo, liberi=True)
    assert mercato.indice_della_persona(righe, righe[3].persona.id) == 3
    assert mercato.indice_della_persona(righe, 9999) == 0 and mercato.indice_della_persona([], 1) is None


# Le azioni sulle righe.

def _riga(mondo, gid, **caselle):
    return next(r for r in _cerca(mondo, **(caselle or {"liberi": True, "in_vendita": True, "del_computer": True, "tuoi": True, "ritirati": True,
                                                         "comprendi_usciti": True})) if r.persona.id == gid)


def test_quale_offerta_si_puo_fare_a_ogni_riga(mondo):
    mia = mondo.miapolisportiva_attiva
    libero = next(gid for gid, g in mondo.giocatori.items() if g.appartenenza == "*" and not g.ritirato and gid != 45)
    assert mercato.offerta_possibile(mondo, mia, _riga(mondo, libero)) == (mercato.INGAGGIO, None, None)
    assert mercato.offerta_possibile(mondo, mia, _riga(mondo, 10)) == (mercato.ACQUISTO, None, None)
    assert mercato.offerta_possibile(mondo, mia, _riga(mondo, 11)) == (mercato.OFFERTA_D_ACQUISTO, None, None)
    # Da un'altra tua polisportiva oggi si compra; i tuoi della attiva e chi non è in vendita no.
    assert mercato.offerta_possibile(mondo, mia, _riga(mondo, 6)) == (mercato.ACQUISTO, None, None)
    for gid in (1, 2, 7, 40, 45):
        azione, problema, motivo = mercato.offerta_possibile(mondo, mia, _riga(mondo, gid))
        assert azione is None and problema and motivo == mercato.OFFERTA_NON_POSSIBILE, gid
    g7 = mondo.giocatori[7]
    assert mercato.offerta_possibile(mondo, mia, _riga(mondo, 7)).problema == f"{g7.nome} {g7.cognome} è già {'tuo' if g7.sesso == 'm' else 'tua'}: è {'tesserato' if g7.sesso == 'm' else 'tesserata'} con Pat-Milano."
    assert mercato.offerta_possibile(mondo, None, _riga(mondo, libero)).motivo == mercato.NESSUNA_POLISPORTIVA_ATTIVA
    # I motivi, nell'ordine in cui controlla il mondo, con la cassa vuota prima di tutto, come nel mercato di oggi.
    mia.cassa = 100
    assert mercato.offerta_possibile(mondo, mia, _riga(mondo, 10)).motivo == "cassa_insufficiente"
    mia.maxtesserati = len(mia.tesserati)
    assert mercato.offerta_possibile(mondo, mia, _riga(mondo, libero)) == (mercato.INGAGGIO, f"Pat-Bologna ha già {mia.maxtesserati} tesserati, il massimo.", "rosa_piena")
    mia.movimenti_oggi = LIMITE_MOVIMENTI_PER_TICK
    assert mercato.offerta_possibile(mondo, mia, _riga(mondo, 11)).motivo == "mosse_finite"
    mia.cassa = 0
    assert mercato.offerta_possibile(mondo, mia, _riga(mondo, libero)) == (mercato.INGAGGIO, "La cassa di Pat-Bologna è vuota.", "cassa_insufficiente")


def test_quale_offerta_si_puo_fare_a_un_allenatore(mondo):
    mia, cpu0 = mondo.miapolisportiva_attiva, _cpu(mondo)
    liberi = mercato.cerca(mondo, mercato.Filtri(allenatori=True, liberi=True))
    assert mercato.offerta_possibile(mondo, mia, liberi[0]) == (mercato.INGAGGIO_ALLENATORE, None, None)
    assert mercato.offerta_possibile(mondo, mia, liberi[0], posto=1).motivo == "staff_posto_occupato"
    impiegato = mercato.cerca(mondo, mercato.Filtri(allenatori=True, del_computer=True))[0]
    assert mercato.offerta_possibile(mondo, mia, impiegato) == (None, f"{impiegato.persona.nome} {impiegato.persona.cognome} allena già {cpu0.nome}: non si possono fare offerte.",
                                                               mercato.OFFERTA_NON_POSSIBILE)
    liberi[0].persona.prelazione = "Pat-Milano"
    liberi[0].persona.prelazione_fino = ORA + datetime.timedelta(days=5)
    assert mercato.offerta_possibile(mondo, mia, liberi[0]).motivo == "allenatore_in_prelazione"
    mia.staff = [liberi[2].persona.numero, mia.staff[1], liberi[3].persona.numero]
    assert mercato.offerta_possibile(mondo, mia, liberi[1]) == (mercato.INGAGGIO_ALLENATORE, "Lo staff di Pat-Bologna è al completo: per un'offerta serve un posto vuoto.",
                                                               "staff_posto_occupato")


def test_amichevole_e_sfida_possibili(mondo):
    mia = mondo.miapolisportiva_attiva
    libero = next(gid for gid, g in mondo.giocatori.items() if g.appartenenza == "*" and not g.ritirato and gid != 45)
    assert mercato.amichevole_possibile(mondo, mia, _riga(mondo, libero)) == (mercato.AMICHEVOLE, None, None)
    mondo.giocatori[libero].ultimo_impegno = ORA
    azione, problema, motivo = mercato.amichevole_possibile(mondo, mia, _riga(mondo, libero))
    assert azione is None and motivo == mercato.NON_GIOCA_OGGI and "ha già giocato un'amichevole" in problema
    for gid in (40, 45):
        assert mercato.amichevole_possibile(mondo, mia, _riga(mondo, gid)).motivo == mercato.NON_GIOCA_OGGI
    allenatore = mercato.cerca(mondo, mercato.Filtri(allenatori=True, liberi=True))[0]
    assert mercato.amichevole_possibile(mondo, mia, allenatore).motivo == mercato.NON_GIOCA_OGGI
    assert mercato.amichevole_possibile(mondo, None, _riga(mondo, libero)).motivo == mercato.NESSUNA_POLISPORTIVA_ATTIVA
    # Il tuo giocatore si sceglie fra i disponibili della polisportiva attiva, esclusa la persona già scelta.
    assert [g.id for g in mercato.tuoi_per_l_amichevole(mondo, mia, mondo.giocatori[3])] == [1, 2, 4, 5]
    mondo.giocatori[1].ultimo_impegno = ORA
    assert [g.id for g in mercato.tuoi_per_l_amichevole(mondo, mia, None)] == [2, 3, 4, 5]
    cpu0 = _cpu(mondo)
    assert mercato.sfida_possibile(mondo, mia, _riga(mondo, 11)) == (mercato.SFIDA, None, None)
    assert mercato.sfida_possibile(mondo, mia, _riga(mondo, 10)) == (mercato.SFIDA, None, None)
    assert mercato.sfida_possibile(mondo, mia, mercato.cerca(mondo, mercato.Filtri(allenatori=True, del_computer=True))[0]).problema is None
    assert mercato.sfida_possibile(mondo, mia, _riga(mondo, 2)) == (mercato.SFIDA, "Si sfidano soltanto le polisportive del computer.", mercato.CLUB_NON_SFIDABILE)
    assert mercato.sfida_possibile(mondo, mia, _riga(mondo, libero)).motivo == mercato.CLUB_NON_SFIDABILE
    mia.sfide_da_lanciare = 0
    assert mercato.sfida_possibile(mondo, mia, _riga(mondo, 11)).motivo == "nessuna_sfida_da_lanciare"
    assert cpu0.nome in {r.polisportiva.nome for r in _cerca(mondo, del_computer=True)}


# I testi della finestra.

def test_la_riga_del_giocatore_trovato(mondo):
    memoria = mercato.Memoria(mondo)
    libero = next(r for r in _cerca(mondo, liberi=True) if not r.persona.mancino and not r.persona.ambidestro)
    g = libero.persona
    g.eta = 17 * ANNO_SIMULAZIONE_GIORNI + 9 * 4 + 3
    riga = testi.riga_trovato(libero, mondo, "valore_alto", memoria)
    regione = luoghi.provincia_e_regione(g.luogo)[1]
    assert riga.startswith(f"{g.nome} {g.cognome}, {classe.classe(g).codice}, 17:4:3, valore {testi.numero(g.indice_collettivo_valore)}, "
                           f"stipendio {testi.euro(libero.stipendio)}, chiede {testi.euro(libero.costo)} d'ingaggio")
    assert riga.endswith(f", {regione}, ID {g.id}")
    # Il dato dell'ordine viene subito dopo l'età, tolto dal suo posto.
    per_costo = testi.riga_trovato(libero, mondo, "costo_basso", memoria)
    assert per_costo.startswith(f"{g.nome} {g.cognome}, {classe.classe(g).codice}, 17:4:3, chiede ") and per_costo.count("chiede") == 1
    per_numero = testi.riga_trovato(libero, mondo, "numero", memoria)
    assert per_numero.startswith(f"{g.nome} {g.cognome}, {classe.classe(g).codice}, 17:4:3, ID {g.id}, valore ") and per_numero.endswith(regione)
    bomba = testi.numero(g._get_valore_totale("bomba_base"))
    assert testi.riga_trovato(libero, mondo, "bomba_base", memoria).startswith(f"{g.nome} {g.cognome}, {classe.classe(g).codice}, 17:4:3, bomba centrale {bomba}, valore ")
    assert ", euro per punto di valore" not in testi.riga_trovato(libero, mondo, "euro_per_punto", memoria)
    assert " euro per punto di valore, valore " in testi.riga_trovato(libero, mondo, "euro_per_punto", memoria)
    assert ", stipendio " in testi.riga_trovato(libero, mondo, "stipendio_basso", memoria).split(", valore ")[0]
    assert "del valore di mercato, valore " in testi.riga_trovato(libero, mondo, "prezzo_sul_mercato", memoria)
    assert ", classifica nazionale 0,0 punti, " in testi.riga_trovato(libero, mondo, "punti_nazionali", memoria)
    assert testi.riga_trovato(libero, mondo, "classe", memoria) == riga
    # Gli stati nuovi, con l'accordo del sesso.
    tuo, in_vendita_da_te, ritirato, uscito = (_riga(mondo, gid) for gid in (2, 6, 40, 45))
    assert f", {testi.accorda(tuo.persona, 'tuo')}, di Pat-Bologna, contratto fino " in testi.riga_trovato(tuo, mondo, "valore_alto", memoria)
    assert f", {testi.accorda(in_vendita_da_te.persona, 'tuo')}, in vendita da Pat-Milano a 1 euro, " in testi.riga_trovato(in_vendita_da_te, mondo, "valore_alto")
    assert f", {testi.accorda(ritirato.persona, 'ritirato')}, " in testi.riga_trovato(ritirato, mondo, "valore_alto") and "stipendio" not in testi.riga_trovato(ritirato, mondo)
    assert f", {testi.accorda(uscito.persona, 'uscito')} di scena" in testi.riga_trovato(uscito, mondo)
    computer = _riga(mondo, 11)
    assert f", {testi.accorda(computer.persona, 'tesserato')} con {_cpu(mondo).nome}, valore di mercato " in testi.riga_trovato(computer, mondo)
    # L'infortunio va dopo lo stato, come in testi.stato.
    tuo.persona.infortunato = True
    tuo.persona.infortunio_fine_datetime = ORA + datetime.timedelta(days=3)
    assert f"di Pat-Bologna, {testi.infortunio(tuo.persona)}, contratto" in testi.riga_trovato(tuo, mondo)


def test_la_riga_dell_allenatore_ha_l_eta_completa_e_la_regione(mondo):
    libero = mercato.cerca(mondo, mercato.Filtri(allenatori=True, liberi=True))[0]
    a = libero.persona
    riga = testi.riga_trovato(libero, mondo, "classe")
    assert riga == testi.riga_allenatore(a, mondo, "classe")
    assert re.match(rf"{re.escape(testi.nome_allenatore(a))}, \d+:\d:\d, (nato allenatore|nata allenatrice), ", riga)
    assert testi.eta_completa_allenatore(a, ORA) in riga and riga.endswith(f", {luoghi.provincia_e_regione(a.luogo)[1]}") and " anni, " not in riga
    assert riga.split(", ")[2] != "chiede" and testi.riga_allenatore(a, mondo, "stipendio_basso").split(", ")[3].startswith("chiede ")
    assert testi.riga_allenatore(a, mondo, "numero").split(", ")[3] == f"numero {a.numero}"
    impiegato = mercato.cerca(mondo, mercato.Filtri(allenatori=True, del_computer=True))[0]
    assert f", capo {'allenatrice' if impiegato.persona.sesso == 'f' else 'allenatore'} di {_cpu(mondo).nome}, " in testi.riga_trovato(impiegato, mondo, "stipendio_basso")


def test_la_situazione_in_blocchi_di_quaranta_caratteri(mondo):
    testo = testi.situazione(mondo)
    blocchi = [testo[i:i + 40] for i in range(0, len(testo), 40)]
    assert all(blocco[0] != " " for blocco in blocchi) and all(blocco.endswith(" ") for blocco in blocchi[:-1])
    assert " ".join(blocco.strip() for blocco in blocchi) == ("Mosse rimaste 5 su 5, sfide da lanciare 2, cassa 20.000 euro, gloria 100, Pat-Bologna, "
                                                             "tesserati 5 su 15, staff: mancano il capo e l'assistente 2.")
    assert blocchi[0].strip() == "Mosse rimaste 5 su 5,"
    mondo.miapolisportiva_attiva = None
    assert testi.situazione(mondo) == "Nessuna polisportiva attiva: puoi solo cercare."
    lungo = testi.a_blocchi(["x" * 45, "corto"])
    assert lungo == "x" * 45 + "," + " " * 34 + "corto."


def test_il_testo_dei_filtri_attivi(mondo):
    assert testi.filtri_attivi(mercato.filtri_della_pronta("mercato"), mondo) == "Chi cercare: giocatori liberi e in vendita da altri."
    assert testi.filtri_attivi(mercato.filtri_della_pronta("allenatori_liberi"), mondo) == "Chi cercare: allenatori liberi."
    filtri = mercato.Filtri(liberi=True, ritirati=True, nome=" ros ", sesso="f", classe_migliore=30, eta_massima=20, costo_massimo=5000, disponibili_oggi=True,
                            regione="Lombardia", tratti={"talento": False, "mancino": True}, condizioni=(("bomba_base", "maggiore", 10.0),),
                            visus=staff.VEDENTE, ordine="costo_basso")
    testo = testi.filtri_attivi(filtri, mondo)
    _accessibile(testo)
    assert testo.splitlines() == [
        "Chi cercare: giocatori liberi e ritirati.",
        "Nome, cognome o numero: ros.",
        "Sesso: donne.",
        "Classe migliore o uguale a D0.",
        "Età massima: 20 anni.",
        "Costo massimo: 5.000 euro.",
        "Disponibili oggi per un'amichevole.",
        "Regione: Lombardia.",
        "Mancino: sì.",
        "Talento: no.",
        "Bomba centrale maggiore di 10.",
        "Visus: vedente, non conta per i giocatori.",
        "Disponibili oggi esclude i ritirati.",
        "Nell'ordine per costo va in fondo chi non ha un costo: i ritirati.",
    ]
    mondo.miapolisportiva_attiva = None
    assert "Costo massimo: 5.000 euro, non conta senza polisportiva attiva." in testi.filtri_attivi(filtri, mondo).splitlines()
    allenatori = mercato.Filtri(allenatori=True, in_vendita=True, ritirati=True, tratti={"mancino": True}, posto_attuale=staff.CAPO, del_computer=True)
    righe = testi.filtri_attivi(allenatori, mondo).splitlines()
    assert righe == ["Chi cercare: allenatori che allenano per il computer.", "In vendita da altri, non conta per gli allenatori.",
                     "Ritirati, non conta per gli allenatori.", "Mancino: sì, non conta per gli allenatori.", "Posto attuale: capo."]
    assert testi.filtri_attivi(mercato.Filtri(allenatori=True, in_vendita=True), mondo).splitlines()[0] == (
        "Chi cercare: nessuna casella spuntata che valga per gli allenatori, e non si trova nessuno.")
    assert testi.filtri_attivi(mercato.Filtri(), mondo) == "Chi cercare: nessuna casella spuntata, e non si trova nessuno."
    contraddittori = mercato.Filtri(liberi=True, solo_ritirati_che_allenano=True, classe_migliore=30, classe_peggiore=50, eta_minima=30, eta_massima=20,
                                    tratti={"precoce": True, "tardiva": True}, polisportiva="team", regione="Lombardia", provincia="Bologna")
    righe = testi.filtri_attivi(contraddittori, mondo).splitlines()
    assert righe[-7:] == ["Solo i ritirati che allenano esclude i liberi.", "Solo i ritirati che allenano vuole spuntata la casella Ritirati: senza, non trova nessuno.",
                          "Classe migliore o uguale a D0 e peggiore o uguale a F0 si escludono.", "Età minima di 30 anni ed età massima di 20 anni si escludono.",
                          "Maturazione precoce e maturazione tardiva si escludono: nessuno li ha insieme.",
                          "Polisportiva che contiene esclude i liberi, che non hanno una polisportiva.",
                          "Provincia e regione si escludono: la provincia Bologna sta in Emilia-Romagna."]


def test_l_etichetta_dei_trovati_e_il_riepilogo_unico(mondo):
    assert testi.etichetta_trovati(2180) == "Trovati: 2.180 giocatori" and testi.etichetta_trovati(1, allenatori=True) == "Trovati: 1 allenatore"
    mia = mondo.miapolisportiva_attiva
    assert testi.riepilogo_mercato_e_ricerca(mia, mondo) is None
    riepilogo = testi.riepilogo_mercato_e_ricerca(mia, mondo, [("Primo esito.", False), ("Secondo esito.", True)], [("Assunto.", "assunto")], ["Sfida lanciata."])
    _accessibile(riepilogo)
    righe = riepilogo.splitlines()
    assert righe[:5] == ["Mercato e ricerca di Pat-Bologna: 2 offerte ai giocatori, 1 riuscita; 1 offerta agli allenatori, 1 riuscita; 1 sfida lanciata.",
                         "Primo esito.", "Secondo esito.", "Assunto.", "Sfida lanciata."]
    assert righe[5] == testi.info_mercato(mia, mondo) and righe[6:] == testi.righe_dello_staff(mia, mondo)[1:]
    assert testi.evento_mercato_e_ricerca([("a", True)], (), ["b"]) == "mercato e ricerca: 2 esiti"
