"""
Le prove del motore della finestra unica Mercato e ricerca, issue 8 e decisione D36: chi cercare con le
caselle, che si sommano; i filtri dei controlli e di Altri filtri, con quelli che non contano e quelli che
si escludono a vicenda; gli ordini con la direzione nel nome; le tredici ricerche pronte e lo stato di ogni
porta d'ingresso; la funzione che dice di chi è una polisportiva; la memoria di classe e valore di mercato;
le funzioni pure che dicono, per ogni riga, quale offerta si può fare, se si gioca un'amichevole o si sfida
il club, o perché no; e i testi della finestra, la riga, la Situazione a blocchi e Filtri attivi.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nascono il 24 ottobre 2026 coi passi 2 e 3 della proposta della issue 8. Lo stesso giorno, col formato 10
dell'archivio, lo stato di ogni porta che va e torna dal salvataggio, il mondo del formato 9 che riceve quello
predefinito, e il salvataggio con uno stato che non va, che si rifiuta. Con le verifiche dello stesso giorno: il
mondo che non ricorda e non scrive uno stato che poi rifiuterebbe, e ogni stato che il motore produce che si salva
e si rilegge; la migrazione dal 9 con la sua costante storica; i tesserati del computer in fondo al prezzo sul
valore di mercato; chi va in fondo negli ordini per stipendio e mesi di contratto, e chi resta coi limiti.
Lo stesso giorno, coi preset dei filtri: i dodici preset di serie al posto delle ricerche pronte, i tre gruppi di campi, la
casella dei preset, le regole del nome, il salvataggio con la sostituzione, la rinomina, l'eliminazione e lo spostamento,
il mondo che ricorda preset e porte; nel formato 10 nuovo il giro del salvataggio, la migrazione dal 9, e la lettura
indulgente: i salvataggi rovinati che tornano ai filtri di serie con un avviso nel registro, il preset che si ripara
invece di sparire, e una lettura che non solleva mai eccezioni e dà sempre qualcosa che si riscrive.
Lo stesso giorno, col passo della finestra, il mondo delle prove sta in tests/aiuti_mercato.py, comune con quelle della
finestra; e si provano il ripiego dopo un esito e il club che oggi ha già rifiutato una sfida.
"""

import copy
import dataclasses
import datetime
import gzip
import json
import random
import re

import pytest
from aiuti_mercato import ORA, mondo_del_mercato

import archivio
import classe
import economia
import luoghi
import mercato
import registro
import staff
import testi
from costanti import ANNO_SIMULAZIONE_GIORNI, FILE_MONDO, LIMITE_MOVIMENTI_PER_TICK
from mondo import Mondo


@pytest.fixture
def mondo():
    """Il mondo di tests/aiuti_mercato.py, comune alle prove della finestra: 120 giocatori, due tue polisportive e due del computer, sei allenatori."""
    return mondo_del_mercato()


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
    # Negli ordini per costo chi non ne ha uno va in fondo, sia dal più basso sia dal più alto; nel prezzo sul
    # valore di mercato anche i tesserati del computer, il cui prezzo vero è nascosto.
    for chiave in mercato.ORDINI_DEL_COSTO:
        righe = _cerca(mondo, ordine=chiave, **tutti)
        senza = [r.costo is None or (chiave == "prezzo_sul_mercato" and r.stato == mercato.DEL_COMPUTER) for r in righe]
        assert senza == sorted(senza) and any(senza) and not all(senza), chiave
    quote = [mercato.prezzo_sul_mercato(r, memoria) for r in _cerca(mondo, ordine="prezzo_sul_mercato", **tutti)]
    presenti = [q for q in quote if q is not None]
    assert presenti == sorted(presenti) and quote[len(presenti):] == [None] * (len(quote) - len(presenti))
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


def test_in_fondo_dice_chi_ci_va_davvero(mondo):
    tutti = {"liberi": True, "in_vendita": True, "del_computer": True, "tuoi": True, "ritirati": True, "comprendi_usciti": True}
    gruppi = {mercato.LIBERO: "liberi", mercato.IN_VENDITA: "in_vendita", mercato.DEL_COMPUTER: "del_computer", mercato.TUO: "tuoi",
              mercato.RITIRATO: "ritirati", mercato.USCITO: "usciti"}
    for attiva in (mondo.miapolisportiva_attiva, None):
        mondo.miapolisportiva_attiva = attiva
        memoria = mercato.Memoria(mondo)
        dati = {**{chiave: (lambda r: r.costo) for chiave in ("costo_basso", "costo_alto", "euro_per_punto")},
                "prezzo_sul_mercato": lambda r, memoria=memoria: mercato.prezzo_sul_mercato(r, memoria), "stipendio_basso": lambda r: r.stipendio,
                "mesi_contratto": lambda r: r.persona.contratto_scadenza}
        for ordine, dato in dati.items():
            filtri = mercato.Filtri(ordine=ordine, **tutti)
            righe = mercato.cerca(mondo, filtri, memoria)
            senza = [dato(r) is None for r in righe]
            assert senza == sorted(senza) and any(senza), ordine
            assert {gruppi[r.stato] for r in righe if dato(r) is None} <= set(mercato.in_fondo(filtri, attiva)), ordine
    mia = mondo.polisportive["Pat-Bologna"]
    assert mercato.in_fondo(mercato.Filtri(in_vendita=True, del_computer=True, ordine="prezzo_sul_mercato"), mia) == ["del_computer"]
    assert mercato.in_fondo(mercato.Filtri(in_vendita=True, del_computer=True, ordine="costo_basso"), mia) == []
    assert mercato.in_fondo(mercato.Filtri(liberi=True, tuoi=True, ritirati=True, ordine="stipendio_basso"), None) == ["ritirati"]
    assert mercato.in_fondo(mercato.Filtri(liberi=True, tuoi=True, ritirati=True, comprendi_usciti=True, ordine="mesi_contratto"), mia) == [
        "liberi", "ritirati", "usciti"]
    assert mercato.in_fondo(mercato.Filtri(allenatori=True, liberi=True, ordine_allenatori="stipendio_basso", ordine="mesi_contratto"), None) == []


def test_chi_non_ha_il_dato_di_un_limite_resta_e_filtri_attivi_lo_dice(mondo):
    mia = mondo.miapolisportiva_attiva
    morti = mondo._ids_morti_processati_sessione
    liberi = {gid for gid, g in mondo.giocatori.items() if g.appartenenza == "*" and not g.ritirato and gid not in morti}
    # I tuoi hanno tutti un contratto più lungo di un mese; liberi, ritirati e usciti non ne hanno, e restano.
    assert _ids(_cerca(mondo, mesi_contratto_massimi=1, liberi=True, tuoi=True)) == liberi
    assert _ids(_cerca(mondo, mesi_contratto_massimi=1, ritirati=True, comprendi_usciti=True)) == {*range(40, 46)}
    allenatori_liberi = mercato.cerca(mondo, mercato.Filtri(allenatori=True, liberi=True))
    assert mercato.cerca(mondo, mercato.Filtri(allenatori=True, liberi=True, tuoi=True, mesi_contratto_massimi=1)) == allenatori_liberi
    assert len(mercato.cerca(mondo, mercato.Filtri(allenatori=True, liberi=True, tuoi=True, mesi_contratto_massimi=600))) == len(allenatori_liberi) + 1
    limiti = mercato.Filtri(liberi=True, tuoi=True, ritirati=True, comprendi_usciti=True, costo_massimo=100, stipendio_massimo=100, mesi_contratto_massimi=3)
    assert mercato.restano(limiti, mia) == [("costo_massimo", ["tuoi", "ritirati", "usciti"]), ("stipendio_massimo", ["ritirati", "usciti"]),
                                            ("mesi_contratto_massimi", ["liberi", "ritirati", "usciti"])]
    assert [campo for campo, _gruppi in mercato.restano(limiti, None)] == ["stipendio_massimo", "mesi_contratto_massimi"]
    assert mercato.restano(mercato.Filtri(in_vendita=True, del_computer=True, costo_massimo=100, stipendio_massimo=100, mesi_contratto_massimi=3), mia) == []
    assert mercato.restano(mercato.Filtri(allenatori=True, liberi=True, tuoi=True, ritirati=True, stipendio_massimo=100, mesi_contratto_massimi=3), mia) == [
        ("mesi_contratto_massimi", ["liberi"])]
    righe = testi.filtri_attivi(mercato.Filtri(liberi=True, ritirati=True, stipendio_massimo=300, mesi_contratto_massimi=3, ordine="mesi_contratto"), mondo)
    _accessibile(righe)
    assert righe.splitlines() == ["Chi cercare: giocatori liberi e ritirati.", "Stipendio massimo: 300 euro; restano i ritirati, che non hanno uno stipendio.",
                                  "Mesi di contratto rimasti al massimo: 3; restano i liberi e i ritirati, che non hanno un contratto.",
                                  "Nell'ordine per mesi di contratto va in fondo chi non ha un contratto: i liberi e i ritirati."]
    assert testi.filtri_attivi(mercato.Filtri(allenatori=True, liberi=True, mesi_contratto_massimi=3), mondo).splitlines()[1] == (
        "Mesi di contratto rimasti al massimo: 3; restano i liberi, che non hanno un contratto.")
    assert testi.filtri_attivi(mercato.Filtri(tuoi=True, ritirati=True, comprendi_usciti=True, ordine="stipendio_basso"), mondo).splitlines()[-1] == (
        "Nell'ordine per stipendio va in fondo chi non ha uno stipendio: i ritirati e gli usciti di scena.")
    assert testi.filtri_attivi(mercato.Filtri(in_vendita=True, del_computer=True, ordine="prezzo_sul_mercato"), mondo).splitlines()[-1] == (
        "Nell'ordine per costo va in fondo chi non ha un costo: i tesserati del computer, il cui prezzo vero è nascosto.")


# I preset di serie, i gruppi di campi, la casella e i preset di Gabriele.

def test_i_dodici_preset_di_serie(mondo):
    assert len(mercato.PRESET_DI_SERIE) == 12 and len(set(dict(mercato.PRESET_DI_SERIE).values())) == 12
    for chiave, _nome in mercato.PRESET_DI_SERIE:
        filtri = mercato.filtri_di_serie(chiave)
        assert mercato.caselle_che_contano(filtri), chiave
        assert mercato.contraddizioni(filtri) == [] and mercato.non_contano(filtri, mondo.miapolisportiva_attiva) == [], chiave
        assert filtri.ordine_scelto in dict(mercato.ORDINI_ALLENATORI if filtri.allenatori else mercato.ORDINI_GIOCATORI), chiave
        mercato.cerca(mondo, filtri)
    assert mercato.filtri_di_serie("mercato") == mercato.Filtri(liberi=True, in_vendita=True)
    assert mercato.filtri_di_serie("giovani_migliori").eta_massima == mercato.ETA_DEI_GIOVANI == 20
    avversari = mercato.filtri_di_serie("avversari_amichevole")
    assert avversari.disponibili_oggi and avversari.tuoi and avversari.ordine == "classe"
    # I capi e gli assistenti migliori guardano soltanto chi ha quel posto, niente liberi.
    capi = mercato.cerca(mondo, mercato.filtri_di_serie("capi_migliori"))
    assert [r.persona.numero for r in capi] == [_cpu(mondo).staff[0]]
    assistenti = mercato.cerca(mondo, mercato.filtri_di_serie("assistenti_migliori"))
    assert [r.persona.numero for r in assistenti] == [mondo.miapolisportiva_attiva.staff[1]]
    # Torna ai tuoi filtri non c'è più: lo sostituisce la voce Filtri attuali, non salvati.
    with pytest.raises(KeyError):
        mercato.filtri_di_serie("torna_ai_tuoi")
    primo = mercato.filtri_di_serie("giovani_migliori")
    primo.tratti["mancino"] = True
    assert mercato.filtri_di_serie("giovani_migliori").tratti == {}
    assert set(mercato.PRESET_DELLA_PORTA) == set(mercato.NOMI_DELLE_PORTE) == set(mercato.PORTE) == {"mercato", "allenatori", "ricerca", "amichevole"}
    assert set(mercato.PRESET_DELLA_PORTA.values()) <= set(dict(mercato.PRESET_DI_SERIE))


def test_i_tre_gruppi_sono_tutti_i_campi_una_volta_sola():
    gruppi = mercato.CAMPI_FILTRI + mercato.CAMPI_ALTRI_FILTRI + mercato.CAMPI_FILTRI_ALLENATORI
    assert sorted(gruppi) == sorted(campo.name for campo in dataclasses.fields(mercato.Filtri)) and len(set(gruppi)) == len(gruppi)
    assert set(mercato.CAMPI_FILTRI_ALLENATORI) == set(mercato.CAMPI_SOLO_ALLENATORI)


def test_i_filtri_di_un_gruppo_si_contano_e_si_azzerano():
    filtri = mercato.Filtri(liberi=True, sesso="f", classe_peggiore=40, tratti={"mancino": True, "talento": False}, comune=" ",
                            condizioni=(("valore", "maggiore", 3),), visus=staff.VEDENTE)
    # Ogni tratto e ogni condizione contano uno; un testo di soli spazi non conta.
    assert mercato.quanti_impostati(filtri, mercato.CAMPI_ALTRI_FILTRI) == 3
    assert mercato.quanti_impostati(filtri, mercato.CAMPI_FILTRI_ALLENATORI) == 1
    assert mercato.quanti_impostati(filtri, mercato.CAMPI_FILTRI) == 3
    azzerati = mercato.azzera(filtri, mercato.CAMPI_ALTRI_FILTRI)
    assert mercato.quanti_impostati(azzerati, mercato.CAMPI_ALTRI_FILTRI) == 0 and azzerati.comune == ""
    assert azzerati.sesso == "f" and azzerati.liberi and azzerati.classe_peggiore == 40 and azzerati.visus == staff.VEDENTE
    assert filtri.tratti == {"mancino": True, "talento": False} and filtri.condizioni == (("valore", "maggiore", 3),)
    assert mercato.azzera(filtri, mercato.CAMPI_FILTRI_ALLENATORI).visus is None


def test_la_casella_dei_preset():
    fdr = mercato.filtri_di_ricerca_di_serie()
    voci = mercato.voci_della_casella(fdr)
    assert len(voci) == 14 and voci[0] == mercato.Voce(mercato.VOCE_ATTUALI, None, "Filtri attuali, non salvati")
    assert voci[-1] == mercato.Voce(mercato.VOCE_SALVA, None, "Salva filtri...")
    assert [(voce.tipo, voce.scelta, voce.nome) for voce in voci[1:-1]] == [(mercato.VOCE_DI_SERIE, chiave, nome) for chiave, nome in mercato.PRESET_DI_SERIE]
    mercato.salva_preset(fdr, "Giovani mancini", mercato.Filtri(liberi=True, tratti={"mancino": True}))
    mercato.salva_preset(fdr, "Donne", mercato.Filtri(liberi=True, sesso="f"))
    voci = mercato.voci_della_casella(fdr)
    assert len(voci) == 16 and voci[1:3] == [mercato.Voce(mercato.VOCE_TUA, 1, "Giovani mancini"), mercato.Voce(mercato.VOCE_TUA, 2, "Donne")]
    assert voci[3].scelta == "mercato" and voci[-1].tipo == mercato.VOCE_SALVA
    assert mercato.posto_della_scelta(voci, None) == 0 and mercato.posto_della_scelta(voci, 2) == 2 and mercato.posto_della_scelta(voci, "mercato") == 3
    assert mercato.posto_della_scelta(voci, 9) is None and mercato.posto_della_scelta(voci, True) is None and mercato.posto_della_scelta(voci, "inventata") is None
    attuali = mercato.Filtri(tuoi=True)
    assert mercato.filtri_della_voce(fdr, None, attuali) == attuali and mercato.filtri_della_voce(fdr, None, attuali) is not attuali
    dal_preset = mercato.filtri_della_voce(fdr, 2, attuali)
    dal_preset.sesso = "m"
    assert fdr.preset[1].filtri.sesso == "f" and mercato.filtri_della_voce(fdr, "piu_forti", attuali) == mercato.filtri_di_serie("piu_forti")
    for scelta in (9, "inventata", True):
        with pytest.raises(KeyError):
            mercato.filtri_della_voce(fdr, scelta, attuali)


@pytest.mark.parametrize("nome, problema", [
    ("", "Il nome del preset deve avere da 1 a 50 caratteri."),
    ("   ", "Il nome del preset deve avere da 1 a 50 caratteri."),
    ("x" * 51, "Il nome del preset deve avere da 1 a 50 caratteri."),
    ("Prima riga\nseconda", "Il nome del preset non può avere a capo, tabulazioni o altri caratteri di controllo."),
    ("Con\tla tabulazione", "Il nome del preset non può avere a capo, tabulazioni o altri caratteri di controllo."),
    ("filtri ATTUALI, non salvati", "filtri ATTUALI, non salvati è il nome di una voce di serie della casella dei preset: se ne sceglie un altro."),
    (" salva filtri... ", "salva filtri... è il nome di una voce di serie della casella dei preset: se ne sceglie un altro."),
    ("I CAPI ALLENATORI MIGLIORI", "I CAPI ALLENATORI MIGLIORI è il nome di una voce di serie della casella dei preset: se ne sceglie un altro."),
])
def test_le_regole_del_nome_di_un_preset(nome, problema):
    assert mercato.problema_del_nome(mercato.filtri_di_ricerca_di_serie(), nome) == problema


def test_un_nome_gia_usato_si_sostituisce_salvando_ma_non_rinominando():
    fdr = mercato.filtri_di_ricerca_di_serie()
    assert mercato.problema_del_nome(fdr, " " + "x" * 50 + " ") is None and mercato.problema_del_nome(fdr, "Salva filtri") is None
    mercato.salva_preset(fdr, "Giovani", mercato.Filtri(liberi=True))
    mercato.salva_preset(fdr, "Vecchi", mercato.Filtri(ritirati=True))
    # Salvando, il nome di un tuo preset non è un problema: Salva filtri chiede se sostituirne i filtri.
    assert mercato.problema_del_nome(fdr, "GIOVANI") is None
    # Rinominando sì, salvo per il preset stesso, che può cambiare soltanto le maiuscole.
    assert mercato.problema_del_nome(fdr, " giovani ", 2) == "Esiste già un preset che si chiama Giovani."
    assert mercato.problema_del_nome(fdr, "GIOVANI", 1) is None


def test_salva_rinomina_elimina_e_sposta_i_preset():
    fdr = mercato.filtri_di_ricerca_di_serie()
    filtri = mercato.Filtri(liberi=True, sesso="f")
    preset, sostituito = mercato.salva_preset(fdr, "  Giovani mancini ", filtri)
    assert (preset.numero, preset.nome, sostituito, fdr.prossimo_preset) == (1, "Giovani mancini", False, 2)
    filtri.sesso = "m"
    assert preset.filtri.sesso == "f"
    mercato.salva_preset(fdr, "Altro", mercato.Filtri(tuoi=True))
    # Lo stesso nome, senza badare alle maiuscole: si sostituiscono i filtri, e il preset tiene nome, posto e numero.
    stesso, sostituito = mercato.salva_preset(fdr, "GIOVANI MANCINI", mercato.Filtri(ritirati=True))
    assert sostituito and stesso is fdr.preset[0] and (stesso.numero, stesso.nome) == (1, "Giovani mancini")
    assert stesso.filtri == mercato.Filtri(ritirati=True) and fdr.prossimo_preset == 3 and len(fdr.preset) == 2
    with pytest.raises(ValueError, match=r"^Il nome del preset deve avere da 1 a 50 caratteri\.$"):
        mercato.salva_preset(fdr, " ", mercato.Filtri())
    rotti = mercato.Filtri(liberi=True)
    rotti.sesso = ""
    with pytest.raises(ValueError, match=r"^I filtri non sono validi: il campo sesso ha un valore che non va, ''$"):
        mercato.salva_preset(fdr, "Rotti", rotti)
    assert [p.nome for p in fdr.preset] == ["Giovani mancini", "Altro"] and fdr.prossimo_preset == 3
    # La rinomina tiene posto, numero e filtri.
    assert mercato.rinomina_preset(fdr, 1, " giovani MANCINI ") is fdr.preset[0] and fdr.preset[0].nome == "giovani MANCINI"
    with pytest.raises(ValueError, match=r"^Esiste già un preset che si chiama Altro\.$"):
        mercato.rinomina_preset(fdr, 1, "ALTRO")
    with pytest.raises(KeyError):
        mercato.rinomina_preset(fdr, 9, "Nuovo")
    # Lo spostamento, e il bordo che non sposta.
    assert mercato.sposta_preset(fdr, 2, -1) and [p.numero for p in fdr.preset] == [2, 1]
    assert not mercato.sposta_preset(fdr, 2, -1) and not mercato.sposta_preset(fdr, 1, 1) and [p.numero for p in fdr.preset] == [2, 1]
    assert mercato.sposta_preset(fdr, 2, 1) and [p.numero for p in fdr.preset] == [1, 2]
    with pytest.raises(ValueError):
        mercato.sposta_preset(fdr, 1, 2)
    with pytest.raises(KeyError):
        mercato.sposta_preset(fdr, True, 1)
    # L'eliminazione: le porte che lo riaprivano tornano al loro preset di serie, coi filtri attuali, e il numero non torna.
    fdr.porte["mercato"] = mercato.StatoDellaPorta(1, mercato.Filtri(liberi=True))
    fdr.porte["ricerca"] = mercato.StatoDellaPorta(2, mercato.Filtri(tuoi=True))
    assert mercato.elimina_preset(fdr, 1).nome == "giovani MANCINI" and [p.numero for p in fdr.preset] == [2]
    assert fdr.porte["mercato"] == mercato.StatoDellaPorta("mercato", mercato.Filtri(liberi=True)) and fdr.porte["ricerca"].scelta == 2
    assert mercato.salva_preset(fdr, "Terzo", mercato.Filtri(liberi=True))[0].numero == 3
    with pytest.raises(KeyError):
        mercato.elimina_preset(fdr, 1)


def test_il_mondo_ricorda_preset_e_porte(mondo):
    assert mondo.filtri_di_ricerca is None and mercato.filtri_di_ricerca_del_mondo(mondo) == mercato.filtri_di_ricerca_di_serie()
    for porta in mercato.PORTE:
        stato = mercato.stato_della_porta(mondo, porta)
        chiave = mercato.PRESET_DELLA_PORTA[porta]
        assert stato == mercato.stato_di_serie(porta) == mercato.StatoDellaPorta(chiave, mercato.filtri_di_serie(chiave))
    assert mercato.stato_della_porta(mondo, "allenatori").attuali.allenatori
    with pytest.raises(KeyError):
        mercato.stato_della_porta(mondo, "altrove")
    # La finestra cambia la sua copia; il mondo cambia soltanto con ricorda_i_preset.
    copia = mercato.filtri_di_ricerca_del_mondo(mondo)
    mercato.salva_preset(copia, "Donne libere", mercato.Filtri(liberi=True, sesso="f"))
    assert mondo.filtri_di_ricerca is None
    mercato.ricorda_i_preset(mondo, copia)
    assert [(p.numero, p.nome) for p in mondo.filtri_di_ricerca.preset] == [(1, "Donne libere")] and mondo.filtri_di_ricerca.prossimo_preset == 2
    copia.preset[0].filtri.sesso = "m"
    assert mondo.filtri_di_ricerca.preset[0].filtri.sesso == "f"
    # La porta ricorda la voce scelta e i filtri attuali; le altre restano di serie.
    mercato.ricorda_la_porta(mondo, "mercato", mercato.StatoDellaPorta(1, mercato.Filtri(tuoi=True)))
    assert mercato.stato_della_porta(mondo, "mercato") == mercato.StatoDellaPorta(1, mercato.Filtri(tuoi=True))
    assert mercato.stato_della_porta(mondo, "ricerca") == mercato.stato_di_serie("ricerca")
    letto = mercato.stato_della_porta(mondo, "mercato")
    letto.attuali.sesso = "m"
    assert mondo.filtri_di_ricerca.porte["mercato"].attuali.sesso is None
    assert mercato.filtri_della_voce(mondo.filtri_di_ricerca, letto.scelta, letto.attuali).sesso == "f"
    # Il preset eliminato nella finestra: la porta che lo riapriva torna al suo preset di serie, coi suoi filtri attuali.
    copia = mercato.filtri_di_ricerca_del_mondo(mondo)
    mercato.elimina_preset(copia, 1)
    mercato.ricorda_i_preset(mondo, copia)
    assert mondo.filtri_di_ricerca.preset == [] and mondo.filtri_di_ricerca.prossimo_preset == 2
    assert mercato.stato_della_porta(mondo, "mercato") == mercato.StatoDellaPorta("mercato", mercato.Filtri(tuoi=True))
    # Una porta non ricorda un preset che non c'è, né una porta che non esiste; il mondo resta com'era.
    prima = mondo.filtri_di_ricerca.copia()
    with pytest.raises(ValueError, match=r"^La porta Mercato, Ctrl\+K, riapriva il preset numero 1, che non c'è più$"):
        mercato.ricorda_la_porta(mondo, "mercato", mercato.StatoDellaPorta(1, mercato.Filtri()))
    with pytest.raises(KeyError):
        mercato.ricorda_la_porta(mondo, "altrove", mercato.StatoDellaPorta(None, mercato.Filtri()))
    assert mondo.filtri_di_ricerca == prima


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
    # Dopo un esito, chi non c'è più lascia la scelta allo stesso posto, entro le righe.
    assert mercato.indice_della_persona(righe, 9999, ripiego=2) == 2
    assert mercato.indice_della_persona(righe, 9999, ripiego=len(righe) + 5) == len(righe) - 1
    assert mercato.indice_della_persona(righe, righe[3].persona.id, ripiego=1) == 3


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
    # Il club che oggi ha già rifiutato ha il suono del lancio delle sfide, dal passo della finestra.
    club = _riga(mondo, 11).polisportiva
    mondo.sfide.rifiutata_oggi = lambda nome, bersaglio, oggi: (nome, bersaglio, oggi) == (mia.nome, club.nome, ORA.date())
    azione, problema, motivo = mercato.sfida_possibile(mondo, mia, _riga(mondo, 11))
    assert (azione, motivo) == (mercato.SFIDA, "sfida_gia_rifiutata_oggi") and "ha già rifiutato oggi" in problema
    del mondo.sfide.rifiutata_oggi
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
    # Il suo prezzo vero è nascosto: nel prezzo sul valore di mercato non costa il 100%, e non ha il dato dell'ordine.
    c = computer.persona
    assert mercato.prezzo_sul_mercato(computer, memoria) is None and "costa" not in testi.riga_trovato(computer, mondo, "prezzo_sul_mercato", memoria)
    assert testi.riga_trovato(computer, mondo, "prezzo_sul_mercato", memoria).startswith(f"{c.nome} {c.cognome}, {memoria.codice(c)}, {testi.eta_completa(c)}, valore ")
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
    assert testi.filtri_attivi(mercato.filtri_di_serie("mercato"), mondo) == "Chi cercare: giocatori liberi e in vendita da altri."
    assert testi.filtri_attivi(mercato.filtri_di_serie("allenatori_liberi"), mondo) == "Chi cercare: allenatori liberi."
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
        "Costo massimo: 5.000 euro; restano i ritirati, che non hanno un costo.",
        "Disponibili oggi per un'amichevole.",
        "Regione: Lombardia.",
        "Mancino: sì.",
        "Talento: no.",
        "Bomba centrale: maggiore di 10.",
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
    # Dal passo della finestra: le operazioni sui preset sono esiti anche loro, e il riepilogo vale anche senza polisportiva attiva.
    preset = [testi.esito_preset_salvato("Giovani mancini"), testi.esito_preset_rinominato("Giovani mancini", "Giovani")]
    assert testi.riepilogo_mercato_e_ricerca(mia, mondo, preset=preset).splitlines() == [
        "Mercato e ricerca di Pat-Bologna: 2 operazioni sui preset.", "Preset salvato: Giovani mancini.", "Preset Giovani mancini rinominato Giovani.",
        testi.info_mercato(mia, mondo)]
    assert testi.riepilogo_mercato_e_ricerca(None, mondo, preset=preset[:1]) == "Mercato e ricerca: 1 operazione sui preset.\nPreset salvato: Giovani mancini."
    assert testi.evento_mercato_e_ricerca(preset=preset) == "mercato e ricerca: 2 esiti"


def test_i_testi_della_finestra(mondo):
    mia = mondo.miapolisportiva_attiva
    assert testi.titolo_mercato_e_ricerca(mia) == "Mercato e ricerca di Pat-Bologna" and testi.titolo_mercato_e_ricerca(None) == "Mercato e ricerca"
    assert testi.linguetta("Altri filtri", 0) == "Altri filtri" and testi.linguetta("Altri filtri", 1) == "Altri filtri, 1 attivo"
    assert testi.linguetta("Filtri degli allenatori", 3) == "Filtri degli allenatori, 3 attivi"
    r = _riga(mondo, 11)
    assert testi.etichetta_della_scheda(r) == f"Sc&heda di {testi.nome_completo(r.persona)}" and testi.etichetta_della_scheda(None) == "Sc&heda"
    assert testi.scheda_della_riga(r, mondo) == testi.scheda_giocatore(r.persona, mondo)
    allenatore = mercato.cerca(mondo, mercato.Filtri(allenatori=True, liberi=True))[0]
    assert testi.scheda_della_riga(allenatore, mondo) == testi.scheda_allenatore(allenatore.persona, mondo)
    assert testi.scheda_della_riga(None, mondo) == testi.ELENCO_VUOTO_SENZA_SCHEDA
    assert testi.mosse_finite(mia) == "Per oggi Pat-Bologna ha finito le mosse di mercato."
    assert testi.condizione_a_parole("ambizione", "maggiore", 50) == "Ambizione, da 0 a 100: maggiore di 50"
    assert testi.domanda_sostituzione_preset("Giovani") == "Esiste già il preset Giovani: sostituirne i filtri con questi?"
    assert testi.domanda_eliminazione_preset("Giovani").startswith("Eliminare il preset Giovani? Le porte che lo riaprivano")
    assert testi.esito_preset_salvato("Giovani", sostituito=True) == "Preset Giovani: filtri sostituiti con quelli attuali."
    assert testi.esito_preset_eliminato("Giovani") == "Preset eliminato: Giovani."
    assert testi.esito_preset_spostato("Giovani", 1, 3) == "Preset Giovani spostato al posto 1 di 3 fra i tuoi."
    for testo in (testi.NESSUNA_CONDIZIONE, testi.NESSUN_PRESET, testi.ELENCO_VUOTO_SENZA_SCHEDA):
        _accessibile(testo)
    # Le domande delle offerte valgono anche sulla riga della finestra, come sul candidato del mercato di prima.
    in_vendita = _riga(mondo, 10)
    assert testi.domanda_acquisto(in_vendita, mia, mondo).startswith(f"Comprare {testi.nome_completo(in_vendita.persona)} da {in_vendita.polisportiva.nome} per 3.000 euro?")
    del_computer = _riga(mondo, 11)
    assert testi.domanda_offerta_d_acquisto(del_computer, 900, mia, mondo).startswith(f"Offrire 900 euro a {del_computer.polisportiva.nome} per {testi.nome_completo(del_computer.persona)}?")
    libero = next(r for r in _cerca(mondo, liberi=True))
    assert testi.domanda_ingaggio(libero, 450, 50.0, mia, mondo).startswith(f"Offrire a {testi.nome_completo(libero.persona)} un ingaggio di 450 euro, per tesserarsi con Pat-Bologna?")


# Il salvataggio, formato 10: i preset e le porte.

A_MANO = {"liberi": True, "in_vendita": True, "del_computer": True, "tuoi": True, "ritirati": True, "nome": "ros", "sesso": "f", "classe_migliore": 40,
          "eta_massima": 30, "costo_massimo": 5000, "disponibili_oggi": True, "ordine": "bomba_base", "ordine_allenatori": "eta_anziano",
          "classe_peggiore": 60, "eta_minima": 18, "regione": "Lombardia", "provincia": "Milano", "comune": "mil", "polisportiva": "team",
          "tratti": {tratto: posto % 2 == 0 for posto, tratto in enumerate(mercato.TRATTI)}, "valore_minimo": 120.5, "stipendio_massimo": 900,
          "mesi_contratto_massimi": 12, "senza_acciacchi": True, "solo_ritirati_che_allenano": True, "solo_nuovi": True, "comprendi_usciti": True,
          "condizioni": (("bomba_base", "maggiore", 10.5), ("ambizione", "minore", 50)), "tipo_allenatore": staff.EX, "visus": staff.VEDENTE,
          "posto_attuale": staff.CAPO, "stipendio_capo_massimo": 2000, "senza_prelazione_altrui": True}


@pytest.fixture
def scritti(monkeypatch):
    """Le righe che il registro degli errori riceve."""
    righe = []
    monkeypatch.setattr(registro, "scrivi", righe.append)
    return righe


def _con_i_preset(m):
    """Il mondo con due preset di Gabriele, il 2 e il 3 dopo che l'1 è stato eliminato, e una porta per ogni voce della casella."""
    fdr = mercato.filtri_di_ricerca_del_mondo(m)
    mercato.salva_preset(fdr, "Da togliere", mercato.Filtri(liberi=True))
    mercato.salva_preset(fdr, "Donne libere", mercato.Filtri(liberi=True, sesso="f", eta_massima=25))
    mercato.salva_preset(fdr, "Allenatori vedenti", mercato.Filtri(allenatori=True, liberi=True, visus=staff.VEDENTE, posto_attuale=staff.CAPO,
                                                                   ordine_allenatori="eta_anziano"))
    mercato.elimina_preset(fdr, 1)
    mercato.ricorda_i_preset(m, fdr)
    mercato.ricorda_la_porta(m, "mercato", mercato.StatoDellaPorta(2, mercato.Filtri(liberi=True, sesso="f")))
    mercato.ricorda_la_porta(m, "allenatori", mercato.StatoDellaPorta(3, mercato.Filtri(allenatori=True, tuoi=True)))
    mercato.ricorda_la_porta(m, "ricerca", mercato.StatoDellaPorta(None, mercato.Filtri(**{**A_MANO, "indole": m.giocatori[3].indole})))
    mercato.ricorda_la_porta(m, "amichevole", mercato.StatoDellaPorta("piu_forti", mercato.Filtri(tuoi=True, nome="ros")))
    return m


def test_ogni_preset_di_serie_va_e_torna_dal_dizionario():
    for chiave, _nome in mercato.PRESET_DI_SERIE:
        filtri = mercato.filtri_di_serie(chiave)
        assert mercato.filtri_da_dizionario(json.loads(json.dumps(mercato.filtri_a_dizionario(filtri)))) == filtri


def test_preset_e_porte_vanno_e_tornano_dal_salvataggio(mondo, cartella_di_prova, scritti):
    _con_i_preset(mondo)
    assert archivio.salva(mondo)
    letto = archivio.leggi(cartella_di_prova / FILE_MONDO)
    blocco = letto["mondo"]["filtri_di_ricerca"]
    assert letto["formato"] == archivio.FORMATO == 10 and set(blocco) == {"preset", "prossimo_preset", "porte"} and set(blocco["porte"]) == set(mercato.PORTE)
    assert [(p["numero"], p["nome"]) for p in blocco["preset"]] == [(2, "Donne libere"), (3, "Allenatori vedenti")] and blocco["prossimo_preset"] == 4
    assert {porta: stato["scelta"] for porta, stato in blocco["porte"].items()} == {"mercato": 2, "allenatori": 3, "ricerca": None, "amichevole": "piu_forti"}
    ricaricato = Mondo()
    archivio.carica(ricaricato)
    assert ricaricato.filtri_di_ricerca == mondo.filtri_di_ricerca and scritti == []
    ricerca = mercato.stato_della_porta(ricaricato, "ricerca")
    assert ricerca.attuali.condizioni == (("bomba_base", "maggiore", 10.5), ("ambizione", "minore", 50)) and ricerca.attuali.indole == mondo.giocatori[3].indole
    assert mercato.filtri_della_voce(ricaricato.filtri_di_ricerca, 3, ricerca.attuali).visus == staff.VEDENTE


def test_un_mondo_del_formato_9_riceve_i_filtri_di_serie(mondo, cartella_di_prova, scritti):
    _con_i_preset(mondo)
    vecchio = archivio.componi(mondo)
    vecchio["formato"] = 9
    del vecchio["mondo"]["filtri_di_ricerca"]
    aggiornato = copy.deepcopy(vecchio)
    archivio.MIGRAZIONI[9](aggiornato)
    # La migrazione aggiunge soltanto i filtri di serie, dalla costante storica, e nient'altro cambia.
    assert aggiornato["formato"] == 10 and aggiornato["mondo"].pop("filtri_di_ricerca") == archivio.filtri_di_ricerca_del_formato_10()
    assert aggiornato["mondo"] == vecchio["mondo"]
    # Finché il formato è 10, la costante storica e i filtri di serie di oggi coincidono; ogni volta è un documento nuovo.
    if archivio.FORMATO == 10:
        assert archivio.filtri_di_ricerca_del_formato_10() == mercato.filtri_di_ricerca_a_dizionario(mercato.filtri_di_ricerca_di_serie())
    primo = archivio.filtri_di_ricerca_del_formato_10()
    primo["preset"].append({"numero": 1})
    primo["porte"]["mercato"]["attuali"]["tratti"]["mancino"] = True
    primo["porte"]["mercato"]["attuali"]["condizioni"].append(["valore", "maggiore", 3])
    secondo = archivio.filtri_di_ricerca_del_formato_10()
    assert secondo["preset"] == [] and secondo["porte"]["mercato"]["attuali"]["tratti"] == {} and archivio.FILTRI_VUOTI_DEL_FORMATO_10["condizioni"] == []
    percorso = cartella_di_prova / FILE_MONDO
    with gzip.open(percorso, "wt", encoding="utf-8") as f:
        f.write(json.dumps({**vecchio, "firma": archivio.firma(vecchio)}))
    ricaricato = Mondo()
    archivio.carica(ricaricato)
    assert ricaricato.filtri_di_ricerca == mercato.filtri_di_ricerca_di_serie() and scritti == []
    assert archivio.salva(ricaricato) and archivio.leggi(percorso)["formato"] == archivio.FORMATO
    assert set(archivio.MIGRAZIONI) == set(range(1, archivio.FORMATO))


def _blocco(m):
    return m["filtri_di_ricerca"]


def _metti(valore, *chiavi):
    def guasto(m):
        cosa = _blocco(m)
        for chiave in chiavi[:-1]:
            cosa = cosa[chiave]
        cosa[chiavi[-1]] = valore
    return guasto


def _togli(*chiavi):
    def guasto(m):
        cosa = m
        for chiave in chiavi[:-1]:
            cosa = cosa[chiave]
        del cosa[chiavi[-1]]
    return guasto


def _porta_di_serie(porta):
    def atteso(f):
        f.porte[porta] = mercato.stato_di_serie(porta)
    return atteso


def _attuali_di_serie(porta):
    def atteso(f):
        stato = f.porte[porta]
        stato.attuali = mercato.filtri_di_serie(mercato.PRESET_DELLA_PORTA[porta])
        if stato.scelta is None:
            stato.scelta = mercato.PRESET_DELLA_PORTA[porta]
    return atteso


def _scelta_di_serie(*porte):
    def atteso(f):
        for porta in porte:
            f.porte[porta].scelta = mercato.PRESET_DELLA_PORTA[porta]
    return atteso


def _filtri_del_preset_di_serie(posto):
    def atteso(f):
        f.preset[posto].filtri = mercato.filtri_di_serie(mercato.SERIE_DEI_FILTRI_ILLEGGIBILI)
    return atteso


def _tutto_di_serie(f):
    serie = mercato.filtri_di_ricerca_di_serie()
    f.preset, f.prossimo_preset, f.porte = serie.preset, serie.prossimo_preset, serie.porte


def _senza_i_preset(f):
    f.preset = []
    _scelta_di_serie("mercato", "allenatori")(f)


def _niente(_f):
    pass


# Ogni guasto, con quello che la lettura ne fa: la parte rovinata torna alla serie, e il resto non si tocca.
GUASTI = {
    "una porta in meno": (_togli("filtri_di_ricerca", "porte", "amichevole"), _porta_di_serie("amichevole")),
    "una porta in più": (lambda m: _blocco(m)["porte"].update(altrove=_blocco(m)["porte"]["mercato"]), _niente),
    "un campo in meno": (_togli("filtri_di_ricerca", "porte", "ricerca", "attuali", "sesso"), _attuali_di_serie("ricerca")),
    "un campo in più": (_metti(True, "porte", "mercato", "attuali", "volante"), _attuali_di_serie("mercato")),
    "un sesso che non esiste": (_metti("x", "porte", "mercato", "attuali", "sesso"), _attuali_di_serie("mercato")),
    "un ordine che non esiste": (_metti("a_caso", "porte", "mercato", "attuali", "ordine"), _attuali_di_serie("mercato")),
    "un ordine dei giocatori agli allenatori": (_metti("valore_alto", "porte", "allenatori", "attuali", "ordine_allenatori"), _attuali_di_serie("allenatori")),
    "un tratto che non esiste": (_metti({"volante": True}, "preset", 0, "filtri", "tratti"), _filtri_del_preset_di_serie(0)),
    "un tratto senza sì o no": (_metti({"mancino": None}, "preset", 1, "filtri", "tratti"), _filtri_del_preset_di_serie(1)),
    "una condizione sulla classe": (_metti([["classe", "maggiore", 3]], "porte", "mercato", "attuali", "condizioni"), _attuali_di_serie("mercato")),
    "una condizione monca": (_metti([["valore", "maggiore"]], "preset", 0, "filtri", "condizioni"), _filtri_del_preset_di_serie(0)),
    "una classe oltre K0": (_metti(101, "porte", "ricerca", "attuali", "classe_migliore"), _attuali_di_serie("ricerca")),
    "un'età negativa": (_metti(-1, "porte", "amichevole", "attuali", "eta_massima"), _attuali_di_serie("amichevole")),
    "un costo con la virgola": (_metti(10.5, "porte", "mercato", "attuali", "costo_massimo"), _attuali_di_serie("mercato")),
    "una casella scritta": (_metti("sì", "preset", 0, "filtri", "liberi"), _filtri_del_preset_di_serie(0)),
    "un valore vero o falso": (_metti(True, "preset", 1, "filtri", "valore_minimo"), _filtri_del_preset_di_serie(1)),
    "un nome che è un numero": (_metti(5, "porte", "ricerca", "attuali", "nome"), _attuali_di_serie("ricerca")),
    "un'indole che non esiste": (_metti("furiosa", "preset", 0, "filtri", "indole"), _filtri_del_preset_di_serie(0)),
    "un visus che non esiste": (_metti("miope", "preset", 1, "filtri", "visus"), _filtri_del_preset_di_serie(1)),
    "un preset di serie che non esiste": (_metti("inventata", "porte", "amichevole", "scelta"), _scelta_di_serie("amichevole")),
    "una scelta in un elenco": (_metti(["mercato"], "porte", "amichevole", "scelta"), _scelta_di_serie("amichevole")),
    "un preset che non c'è più": (_metti(7, "porte", "mercato", "scelta"), _scelta_di_serie("mercato")),
    "una scelta vero o falso": (_metti(True, "porte", "allenatori", "scelta"), _scelta_di_serie("allenatori")),
    "lo stato senza la scelta": (_togli("filtri_di_ricerca", "porte", "ricerca", "scelta"), _scelta_di_serie("ricerca")),
    "le porte in un elenco": (lambda m: _blocco(m).update(porte=list(_blocco(m)["porte"].values())), lambda f: f.porte.update(mercato.filtri_di_ricerca_di_serie().porte)),
    "i preset in un dizionario": (lambda m: _blocco(m).update(preset={str(p["numero"]): p for p in _blocco(m)["preset"]}), _senza_i_preset),
    "tutto in un elenco": (lambda m: m.update(filtri_di_ricerca=[]), _tutto_di_serie),
    "il blocco che manca": (_togli("filtri_di_ricerca"), _tutto_di_serie),
}


@pytest.mark.parametrize("guasto", list(GUASTI))
def test_un_salvataggio_rovinato_torna_ai_filtri_di_serie_con_un_avviso(mondo, guasto, scritti):
    _con_i_preset(mondo)
    rovina, atteso = GUASTI[guasto]
    contenuto = archivio.componi(mondo)
    rovina(contenuto["mondo"])
    nuovo = Mondo()
    archivio.costruisci(contenuto, nuovo)
    # Il mondo si apre lo stesso, tutto intero; soltanto la parte rovinata torna alla serie.
    previsto = mondo.filtri_di_ricerca.copia()
    atteso(previsto)
    assert nuovo.filtri_di_ricerca == previsto and set(nuovo.giocatori) == {g["id"] for g in contenuto["mondo"]["giocatori"]}
    # Ogni riparazione va nel registro, col dato originale; quello che si è letto si salva e si rilegge senza riparazioni.
    assert scritti and all(riga.startswith("Lettura del mondo, filtri di Mercato e ricerca. ") and " Il dato originale, in JSON: " in riga for riga in scritti)
    assert all("\n" not in riga for riga in scritti)
    assert mercato.filtri_di_ricerca_da_dizionario(json.loads(json.dumps(mercato.filtri_di_ricerca_da_salvare(nuovo)))) == (previsto, [])


def test_gli_avvisi_vanno_nel_registro_soltanto_per_il_mondo_che_si_apre(mondo, scritti):
    _con_i_preset(mondo)
    contenuto = archivio.componi(mondo)
    contenuto["mondo"]["filtri_di_ricerca"]["porte"]["mercato"]["scelta"] = 7
    contenuto["mondo"]["polisportiva_attiva"] = "Inesistente"
    with pytest.raises(archivio.ErroreSalvataggio):
        archivio.costruisci(contenuto, Mondo())
    assert scritti == []
    contenuto["mondo"]["polisportiva_attiva"] = "Pat-Bologna"
    archivio.costruisci(contenuto, Mondo())
    assert scritti == ["Lettura del mondo, filtri di Mercato e ricerca. La porta Mercato, Ctrl+K, riapriva il preset numero 7, che non c'è più. "
                       "Torna al suo preset di serie, Mercato: liberi e in vendita da altri, dal valore più alto. Il dato originale, in JSON: "
                       + json.dumps(contenuto["mondo"]["filtri_di_ricerca"]["porte"]["mercato"], ensure_ascii=False)]


def test_un_preset_rovinato_si_ripara_invece_di_sparire(mondo, scritti):
    _con_i_preset(mondo)
    contenuto = archivio.componi(mondo)
    blocco = contenuto["mondo"]["filtri_di_ricerca"]
    buono = blocco["preset"][0]
    blocco["preset"] = [
        {**buono, "numero": 1, "nome": "Donne libere"},
        {**buono, "numero": 1, "nome": "DONNE LIBERE"},
        {**buono, "numero": "7", "nome": None},
        {**buono, "numero": 5, "nome": "  Spazi\tdentro  "},
        {**buono, "numero": 6, "nome": "x" * 60},
        {**buono, "numero": 8, "nome": "I capi allenatori migliori"},
        {**buono, "numero": 9, "nome": "y" * 50},
        {**buono, "numero": 12, "nome": "Y" * 50},
        {**buono, "numero": 13, "nome": "Senza filtri", "filtri": {"liberi": True}, "volante": 1},
        "un preset che non è un dizionario",
    ]
    blocco["prossimo_preset"] = 2
    nuovo = Mondo()
    archivio.costruisci(contenuto, nuovo)
    fdr = nuovo.filtri_di_ricerca
    assert [(p.numero, p.nome) for p in fdr.preset] == [
        (1, "Donne libere"), (14, "DONNE LIBERE (2)"), (15, "Preset 15"), (5, "Spazi dentro"), (6, "x" * 50), (8, "I capi allenatori migliori (2)"),
        (9, "y" * 50), (12, "Y" * 46 + " (2)"), (13, "Senza filtri")]
    assert fdr.prossimo_preset == 16 and all(len(p.nome) <= 50 for p in fdr.preset)
    assert all(p.filtri == mercato.filtri_da_dizionario(buono["filtri"]) for p in fdr.preset[:-1])
    assert fdr.preset[-1].filtri == mercato.filtri_di_serie("tutti_in_attivita")
    # Le porte si leggono dopo i preset: il 2 non c'è più, e la porta degli allenatori, che riapriva il 3, nemmeno.
    assert fdr.porte["mercato"].scelta == "mercato" and fdr.porte["allenatori"].scelta == "allenatori_liberi"
    problemi = [riga.split(" Il dato originale, in JSON: ")[0].removeprefix("Lettura del mondo, filtri di Mercato e ricerca. ") for riga in scritti]
    assert len(problemi) == 14 and problemi[:9] == [
        "Il preset al posto 10 della casella non si legge. Si toglie.",
        "Il preset al posto 2 della casella ha lo stesso numero di un preset di prima, 1. Riceve il numero 14.",
        "Il nome del preset numero 14, 'DONNE LIBERE', lo usa già un'altra voce della casella. Diventa DONNE LIBERE (2).",
        "Il preset al posto 3 della casella non ha un numero valido, '7'. Riceve il numero 15.",
        "Al preset numero 15 manca il nome. Si chiama Preset 15.",
        "Il nome del preset numero 5, '  Spazi\\tdentro  ', ha degli spazi in testa o in coda e ha dei caratteri di controllo. Diventa Spazi dentro.",
        f"Il nome del preset numero 6, '{'x' * 60}', supera i 50 caratteri. Diventa {'x' * 50}.",
        "Il nome del preset numero 8, 'I capi allenatori migliori', lo usa già un'altra voce della casella. Diventa I capi allenatori migliori (2).",
        f"Il nome del preset numero 12, '{'Y' * 50}', lo usa già un'altra voce della casella. Diventa {'Y' * 46} (2).",
    ]
    assert problemi[9].startswith("I filtri del preset Senza filtri, numero 13, non sono validi: i campi non sono quelli di questa versione: mancano ")
    assert problemi[9].endswith(". Diventano quelli del preset di serie Tutti in attività, senza filtri, per numero.")
    assert problemi[10:] == [
        "Il preset Senza filtri, numero 13, ha dei dati che questa versione non conosce: volante. Si tolgono.",
        "Il numero del prossimo preset, 2, è già di un preset. Diventa 16.",
        "La porta Mercato, Ctrl+K, riapriva il preset numero 2, che non c'è più. Torna al suo preset di serie, Mercato: liberi e in vendita da altri, dal valore più alto.",
        "La porta Mercato degli allenatori, Ctrl+Maiusc+G, riapriva il preset numero 3, che non c'è più. Torna al suo preset di serie, Gli allenatori liberi migliori.",
    ]
    # Nel registro c'è il preset com'era, per ricostruirlo a mano.
    assert scritti[1].endswith(json.dumps(blocco["preset"][1], ensure_ascii=False))
    assert scritti[0].endswith(json.dumps("un preset che non è un dizionario", ensure_ascii=False))


def test_il_testo_per_il_registro_ha_il_dato_originale_in_json():
    avviso = mercato.Avviso("Lo stato della porta Amichevole, Ctrl+O, non si legge.", "Torna al suo preset di serie.", {"scelta": "città", "numero": 3})
    assert mercato.testo_per_il_registro(avviso) == ("Lettura del mondo, filtri di Mercato e ricerca. Lo stato della porta Amichevole, Ctrl+O, non si legge. "
                                                     "Torna al suo preset di serie. Il dato originale, in JSON: {\"scelta\": \"città\", \"numero\": 3}")
    assert mercato.testo_per_il_registro(mercato.Avviso("P.", "R.", {1, 2})).endswith("Il dato originale, in JSON: {1, 2}")


def test_la_lettura_non_solleva_mai_eccezioni_e_quello_che_legge_si_riscrive(mondo):
    _con_i_preset(mondo)
    buono = mercato.filtri_di_ricerca_da_salvare(mondo)
    caso = random.Random(2410)
    valori = (None, 0, -1, 1, 2, 3, 1.5, float("nan"), True, False, "", "x", "mercato", [], [1], {}, {"a": 1}, ["valore", "maggiore", 3])

    def nodi(dato, percorso=()):
        yield percorso
        figli = dato.items() if isinstance(dato, dict) else enumerate(dato) if isinstance(dato, list) else ()
        for chiave, figlio in figli:
            yield from nodi(figlio, (*percorso, chiave))

    percorsi = list(nodi(buono))
    for _ in range(400):
        dati = copy.deepcopy(buono)
        for _volta in range(caso.randint(1, 3)):
            percorso = caso.choice(percorsi)
            cosa = dati
            try:
                for chiave in percorso[:-1]:
                    cosa = cosa[chiave]
                if percorso:
                    cosa[percorso[-1]] = copy.deepcopy(caso.choice(valori))
                else:
                    dati = copy.deepcopy(caso.choice(valori))
            except (KeyError, IndexError, TypeError):
                continue
        letti, _avvisi = mercato.filtri_di_ricerca_da_dizionario(dati)
        assert mercato.filtri_di_ricerca_da_dizionario(json.loads(json.dumps(mercato.filtri_di_ricerca_a_dizionario(letti)))) == (letti, [])


# Dalla verifica del formato 10: quello che il mondo ricorda e scrive deve rileggersi, senza riparazioni.

SBAGLI_DELLA_FINESTRA = {
    "un sesso vuoto invece di None": ("sesso", ""),
    "una regione None invece del vuoto": ("regione", None),
    "un'età con la virgola": ("eta_massima", 20.0),
    "un tratto senza sì o no": ("tratti", {"mancino": None}),
    "una condizione senza numero": ("condizioni", (("valore", "maggiore", float("nan")),)),
    "un ordine che non esiste": ("ordine", "a_caso"),
}


@pytest.mark.parametrize("sbaglio", list(SBAGLI_DELLA_FINESTRA))
def test_il_mondo_non_ricorda_filtri_che_non_si_rileggerebbero(mondo, sbaglio):
    campo, valore = SBAGLI_DELLA_FINESTRA[sbaglio]
    filtri = mercato.Filtri(liberi=True)
    setattr(filtri, campo, valore)
    # Né come filtri attuali di una porta, né come preset: il mondo resta com'era.
    with pytest.raises(ValueError, match=rf"^I filtri attuali della porta Mercato, Ctrl\+K, non sono validi: il campo {campo} ha un valore che non va, "):
        mercato.ricorda_la_porta(mondo, "mercato", mercato.StatoDellaPorta(None, filtri))
    assert mondo.filtri_di_ricerca is None
    copia = mercato.filtri_di_ricerca_del_mondo(mondo)
    with pytest.raises(ValueError, match=rf"^I filtri non sono validi: il campo {campo} ha un valore che non va, "):
        mercato.salva_preset(copia, "Sbagliato", filtri)
    assert copia.preset == [] and copia.prossimo_preset == 1
    # Un preset messo nella copia senza salva_preset: ricorda_i_preset lo rifiuta.
    copia.preset.append(mercato.Preset(1, "Sbagliato", filtri))
    copia.prossimo_preset = 2
    with pytest.raises(ValueError, match=rf"^I filtri del preset Sbagliato, numero 1, non sono validi: il campo {campo} ha un valore che non va, "):
        mercato.ricorda_i_preset(mondo, copia)
    assert mondo.filtri_di_ricerca is None
    mercato.ricorda_la_porta(mondo, "mercato", mercato.StatoDellaPorta(None, mercato.Filtri(liberi=True)))
    with pytest.raises(ValueError):
        mercato.ricorda_la_porta(mondo, "mercato", mercato.StatoDellaPorta(None, filtri))
    assert mondo.filtri_di_ricerca.porte["mercato"] == mercato.StatoDellaPorta(None, mercato.Filtri(liberi=True))
    # Un valore che il JSON non sa scrivere si rifiuta allo stesso modo, in italiano.
    with pytest.raises(ValueError, match=r"^I filtri della finestra Mercato e ricerca non si possono scrivere: "):
        mercato.ricorda_la_porta(mondo, "ricerca", mercato.StatoDellaPorta(None, mercato.Filtri(nome={"ros"})))


def test_il_mondo_non_ricorda_preset_che_la_lettura_dovrebbe_riparare(mondo):
    for preset, prossimo, problema in (
        ([mercato.Preset(1, "", mercato.Filtri())], 2, "Il nome del preset numero 1, '', non ha nessun carattere"),
        ([mercato.Preset(1, "Uno", mercato.Filtri()), mercato.Preset(2, "UNO", mercato.Filtri())], 3,
         "Il nome del preset numero 2, 'UNO', lo usa già un'altra voce della casella"),
        ([mercato.Preset(1, "Uno", mercato.Filtri()), mercato.Preset(1, "Due", mercato.Filtri())], 3,
         "Il preset al posto 2 della casella ha lo stesso numero di un preset di prima, 1"),
        ([mercato.Preset(4, "Uno", mercato.Filtri())], 4, "Il numero del prossimo preset, 4, è già di un preset"),
        ([mercato.Preset(True, "Uno", mercato.Filtri())], 2, "Il preset al posto 1 della casella non ha un numero valido, True"),
    ):
        copia = mercato.filtri_di_ricerca_del_mondo(mondo)
        copia.preset, copia.prossimo_preset = preset, prossimo
        with pytest.raises(ValueError) as errore:
            mercato.ricorda_i_preset(mondo, copia)
        assert str(errore.value) == problema and mondo.filtri_di_ricerca is None


def test_il_salvataggio_non_scrive_filtri_che_non_si_rileggerebbero(mondo, cartella_di_prova, scritti):
    assert archivio.salva(mondo)
    percorso = cartella_di_prova / FILE_MONDO
    prima = percorso.read_bytes()
    # Filtri messi nel mondo senza ricorda_la_porta: il salvataggio si rifiuta, e quello di prima resta com'era.
    filtri = mercato.Filtri(liberi=True)
    filtri.sesso = ""
    mondo.filtri_di_ricerca = mercato.filtri_di_ricerca_di_serie()
    mondo.filtri_di_ricerca.porte["mercato"] = mercato.StatoDellaPorta(None, filtri)
    messaggi = []
    mondo.notifica = messaggi.append
    assert archivio.salva(mondo) is False
    assert percorso.read_bytes() == prima
    assert messaggi == ["Salvataggio non riuscito: I filtri attuali della porta Mercato, Ctrl+K, non sono validi: il campo sesso ha un valore che non va, ''. "
                        "Il salvataggio precedente è rimasto com'era."]
    ricaricato = Mondo()
    archivio.carica(ricaricato)
    assert ricaricato.filtri_di_ricerca == mercato.filtri_di_ricerca_di_serie() and scritti == []


def test_ogni_stato_che_il_motore_produce_si_salva_e_si_rilegge(mondo, cartella_di_prova, scritti):
    a_mano = mercato.Filtri(**{**A_MANO, "indole": mondo.giocatori[3].indole})
    fdr = mercato.filtri_di_ricerca_del_mondo(mondo)
    # Un preset per ogni preset di serie, per i filtri fatti a mano e per ciascuno dei tre gruppi azzerato.
    for chiave, nome in mercato.PRESET_DI_SERIE:
        mercato.salva_preset(fdr, f"Come {nome}"[:50], mercato.filtri_di_serie(chiave))
    mercato.salva_preset(fdr, "A mano", a_mano)
    for gruppo, campi in (("filtri", mercato.CAMPI_FILTRI), ("altri", mercato.CAMPI_ALTRI_FILTRI), ("allenatori", mercato.CAMPI_FILTRI_ALLENATORI)):
        mercato.salva_preset(fdr, f"A mano senza i {gruppo}", mercato.azzera(a_mano, campi))
    mercato.rinomina_preset(fdr, 2, "Rinominato")
    mercato.sposta_preset(fdr, 3, -1)
    mercato.elimina_preset(fdr, 4)
    mercato.ricorda_i_preset(mondo, fdr)
    scelte = [None, *(chiave for chiave, _nome in mercato.PRESET_DI_SERIE), *(p.numero for p in fdr.preset)]
    # Quattro porte per salvataggio, ciascuna con una scelta diversa e i filtri attuali fatti a mano o di serie.
    for primo in range(0, len(scelte), len(mercato.PORTE)):
        gruppo = dict(zip(mercato.PORTE, scelte[primo:primo + len(mercato.PORTE)], strict=False))
        for posto, (porta, scelta) in enumerate(gruppo.items()):
            attuali = a_mano if posto % 2 == 0 else mercato.filtri_di_serie(mercato.PRESET_DELLA_PORTA[porta])
            mercato.ricorda_la_porta(mondo, porta, mercato.StatoDellaPorta(scelta, attuali))
        assert archivio.salva(mondo)
        ricaricato = Mondo()
        archivio.carica(ricaricato)
        assert ricaricato.filtri_di_ricerca == mondo.filtri_di_ricerca and scritti == []
