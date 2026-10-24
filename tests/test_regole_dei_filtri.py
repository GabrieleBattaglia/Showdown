"""
Le prove del motore del costruttore di regole della finestra Mercato e ricerca, D36 della sera del 24 ottobre 2026: la
macchina di regole.py senza il mondo, la lettura dei valori all'italiana, ogni operatore coi dati che mancano, i
contrari esatti, le alternative con la e che lega prima della o; il catalogo di mercato.py, le voci dello Stato che
valgono insieme, la memoria che costruisce le righe una volta sola e ricorda ogni lettura, il costo che si calcola
tardi, i bersagli, gli ordini comuni e quelli dei soli giocatori; e l'equivalenza col motore a schede, filtro per
filtro, con un oracolo che traduce i filtri di prima in regole e con l'elenco delle differenze volute.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nascono il 24 ottobre 2026 sera col passo 1 del costruttore di regole. Lo stesso giorno, col cambio della finestra, il
motore a schede esce, e con lui l'oracolo: restano le impronte dei preset di serie prese coi due motori, e le differenze
volute dette dalle regole.
"""

import dataclasses
import datetime
import hashlib
import itertools
import json

import pytest
from aiuti_mercato import ORA, mondo_del_mercato

import classe
import contratti
import economia
import luoghi
import mercato
import regole

G = mercato.GIOCATORI
A = mercato.ALLENATORI


@pytest.fixture
def mondo():
    return mondo_del_mercato()


def _regola(bersaglio, chiave, operatore, valore, collegamento=mercato.E):
    return mercato.Regola(collegamento, bersaglio, chiave, operatore, valore)


def _cerca(m, *regole_della_ricerca, ordine="numero", memoria=None):
    return mercato.cerca(m, mercato.Filtri(mercato.con_la_prima_e(regole_della_ricerca), ordine), memoria)


def _numeri(righe):
    return [(r.allenatore, r.numero) for r in righe]


def _ids(righe):
    return {r.persona.id for r in righe if not r.allenatore}


# La macchina, senza il mondo: una riga finta e un catalogo finto.

@dataclasses.dataclass
class RigaFinta:
    dati: dict
    posto: int = 0


def _finta(chiave, tipo, **campi):
    return regole.Caratteristica(chiave, chiave.capitalize(), tipo, lambda r, _c: r.dati.get(chiave), **campi)


ETA = _finta("eta", regole.NUMERO, modo=regole.TRONCA, massimo=120, unita=("anno", "anni"))
VALORE = _finta("valore", regole.NUMERO, decimali=1, massimo=100_000)
COSTO = _finta("costo", regole.NUMERO, massimo=100_000_000, puo_mancare=True)
LIVELLO = _finta("classe", regole.CLASSE)
NOME = _finta("nome", regole.TESTO, puo_mancare=True, cifre=lambda r, _c: str(r.dati["numero"]))
STATO = _finta("stato", regole.SCELTA, voci=(("libero", "libero"), ("tuo", "tuo")), insieme=True)
SESSO = _finta("sesso", regole.SCELTA, voci=(("m", "uomo"), ("f", "donna")))
MANCINO = _finta("mancino", regole.SI_NO)
CONTESTO = regole.Contesto()


@pytest.mark.parametrize(("scritto", "atteso"), [
    ("1.000", 1000), ("1000", 1000), (" 25 ", 25), ("007", 7), ("1.000.000", 1_000_000),
    ("", regole.VUOTO), ("   ", regole.VUOTO), (None, regole.VUOTO),
    ("12a", regole.CIFRE), ("-5", regole.CIFRE), ("5,", regole.CIFRE), (",5", regole.CIFRE), ("1,2,3", regole.CIFRE), (".", regole.CIFRE),
    ("1.00", regole.PUNTO), ("10.00", regole.PUNTO), ("1000.000", regole.PUNTO), ("150.5", regole.PUNTO), ("1.000,5.0", regole.PUNTO),
    ("2,5", regole.DECIMALI), ("121", regole.MISURA), ("1\t2", regole.CONTROLLO),
])
def test_un_numero_intero_si_scrive_all_italiana(scritto, atteso):
    # Il costo arriva a cento milioni; l'età a 120, e 121 è fuori misura.
    letto = regole.leggi_valore(ETA if scritto == "121" else COSTO, scritto)
    if isinstance(atteso, int):
        assert letto == (atteso, None) and isinstance(letto.valore, int)
    else:
        assert letto == (None, atteso)


def test_i_decimali_vanno_dopo_la_virgola_e_il_punto_separa_le_migliaia():
    # Il caso della critica: valore maggiore di 1.000 vuol dire mille, non uno.
    assert regole.leggi_valore(VALORE, "1.000") == (1000.0, None) and regole.leggi_valore(VALORE, "1.000,5") == (1000.5, None)
    assert regole.leggi_valore(VALORE, "150,5") == (150.5, None) and isinstance(regole.leggi_valore(VALORE, "150").valore, float)
    assert regole.leggi_valore(VALORE, "1.5") == (None, regole.PUNTO) and regole.leggi_valore(VALORE, "150,25") == (None, regole.DECIMALI)
    assert regole.leggi_valore(VALORE, "100.000") == (100_000.0, None) and regole.leggi_valore(VALORE, "100.000,1") == (None, regole.MISURA)


def test_classi_testi_scelte_e_si_o_no():
    assert regole.leggi_valore(LIVELLO, " g4 ") == (64, None) and regole.leggi_valore(LIVELLO, "64") == (64, None)
    for sbagliata in ("A0", "K1", "0", "101", "Z3", "G44", "4,5"):
        assert regole.leggi_valore(LIVELLO, sbagliata) == (None, regole.NON_E_UNA_CLASSE)
    assert regole.leggi_valore(NOME, "  ros ") == ("ros", None) and regole.leggi_valore(NOME, "x" * 50) == ("x" * 50, None)
    assert regole.leggi_valore(NOME, "x" * 51) == (None, regole.MISURA) and regole.leggi_valore(NOME, "a\nb") == (None, regole.CONTROLLO)
    assert regole.leggi_valore(SESSO, None) == (None, regole.VUOTO) and regole.leggi_valore(SESSO, "f") == ("f", None)
    with pytest.raises(ValueError):
        regole.leggi_valore(SESSO, "x")
    assert regole.leggi_valore(MANCINO, None) == (None, regole.VUOTO) and regole.leggi_valore(MANCINO, False) == (False, None)
    assert regole.leggi_classe("A1") == 1 and regole.leggi_classe("K0") == 100


def test_il_valore_salvato_e_severo():
    assert regole.valore_valido(ETA, "minore", 20) and not regole.valore_valido(ETA, "minore", 20.0) and not regole.valore_valido(ETA, "minore", True)
    assert not regole.valore_valido(ETA, "minore", -1) and not regole.valore_valido(ETA, "minore", 121)
    assert regole.valore_valido(VALORE, "maggiore", 150.5) and regole.valore_valido(VALORE, "maggiore", 150)
    assert not regole.valore_valido(VALORE, "maggiore", 150.25) and not regole.valore_valido(VALORE, "maggiore", float("nan"))
    assert regole.valore_valido(COSTO, "manca", None) and not regole.valore_valido(COSTO, "manca", 3) and not regole.valore_valido(COSTO, "minore", None)
    assert regole.valore_valido(NOME, "contiene", "ros") and not regole.valore_valido(NOME, "contiene", " ros") and not regole.valore_valido(NOME, "contiene", "")
    assert not regole.valore_valido(NOME, "contiene", "a\tb") and not regole.valore_valido(NOME, "contiene", 5)
    assert regole.valore_valido(SESSO, "uguale", "m") and not regole.valore_valido(SESSO, "uguale", "x") and not regole.valore_valido(SESSO, "uguale", ["m"])
    assert regole.valore_valido(MANCINO, "uguale", True) and not regole.valore_valido(MANCINO, "uguale", 1)
    assert regole.valore_valido(LIVELLO, "migliore", 1) and not regole.valore_valido(LIVELLO, "migliore", 0) and not regole.valore_valido(LIVELLO, "migliore", 101)


def test_i_numeri_si_confrontano_come_li_scrive_la_scheda():
    assert regole.come_la_scheda(ETA, 20.99) == 20 and regole.come_la_scheda(VALORE, 149.96) == 150.0 and regole.come_la_scheda(VALORE, 57.25) == 57.2
    righe = [RigaFinta({"eta": 20.99, "valore": 149.96}), RigaFinta({"eta": 21.0, "valore": 149.94})]
    assert [regole.prova(ETA, "minore_uguale", 20)(r, CONTESTO) for r in righe] == [True, False]
    # Chi la scheda scrive 150,0 ha valore 150, anche se il numero vero è 149,96.
    assert [regole.prova(VALORE, "uguale", 150.0)(r, CONTESTO) for r in righe] == [True, False]
    assert [regole.prova(VALORE, "minore", 150.0)(r, CONTESTO) for r in righe] == [False, True]


def test_ogni_operatore_coi_dati_che_mancano():
    """Chi non ha il dato non passa nessun confronto e passa ogni negativo; non ha il dato e ha il dato lo guardano e basta."""
    con, senza = RigaFinta({"costo": 500, "nome": "Anna Rossi", "numero": 12}), RigaFinta({"numero": 7})
    for operatore, _nome in regole.operatori(COSTO):
        valore = None if operatore in regole.SENZA_VALORE else 500
        prova = regole.prova(COSTO, operatore, valore)
        assert prova(senza, CONTESTO) is (operatore in regole.NEGATIVI), operatore
    attesi = {"uguale": True, "diverso": False, "maggiore": False, "maggiore_uguale": True, "minore": False, "minore_uguale": True, "manca": False, "presente": True}
    assert {op: regole.prova(COSTO, op, None if op in regole.SENZA_VALORE else 500)(con, CONTESTO) for op, _n in regole.operatori(COSTO)} == attesi
    for operatore, _nome in regole.operatori(NOME):
        if operatore in regole.SENZA_VALORE:
            continue
        assert regole.prova(NOME, operatore, "ross")(RigaFinta({"numero": 7}), CONTESTO) is (operatore in regole.NEGATIVI), operatore
    with pytest.raises(ValueError):
        regole.prova(ETA, "manca", None)
    with pytest.raises(ValueError):
        regole.prova(ETA, "contiene", 3)


def test_i_negativi_sono_i_contrari_esatti():
    righe = [RigaFinta({"costo": costo, "nome": nome, "numero": numero, "stato": stato, "sesso": sesso})
             for costo, nome, numero, stato, sesso in ((None, None, 1, frozenset({"libero"}), "m"), (500, "Forlì Rossi", 12, frozenset({"tuo"}), "f"),
                                                       (900, "Sant'Angelo", 123, frozenset(), "m"))]
    coppie = [(COSTO, "uguale", 500), (COSTO, "presente", None), (NOME, "contiene", "forli"), (NOME, "contiene", "12"), (NOME, "uguale", "sant angelo"),
              (STATO, "uguale", "libero"), (SESSO, "uguale", "f")]
    for car, positivo, valore in coppie:
        negativo = next(neg for neg, pos in regole.NEGAZIONI.items() if pos == positivo)
        si, no = regole.prova(car, positivo, valore), regole.prova(car, negativo, valore)
        assert all(si(r, CONTESTO) != no(r, CONTESTO) for r in righe), (car.chiave, positivo)


def test_i_testi_senza_maiuscole_accenti_e_apostrofi_e_le_cifre_del_numero():
    riga = RigaFinta({"nome": "Sant'Anna Forlì", "numero": 1234})
    assert regole.prova(NOME, "contiene", "FORLI")(riga, CONTESTO) and regole.prova(NOME, "comincia", "sant anna")(riga, CONTESTO)
    assert regole.prova(NOME, "contiene", "t'a")(riga, CONTESTO) and regole.prova(NOME, "uguale", "sant'anna forli")(riga, CONTESTO)
    # Con le sole cifre si guarda il numero: contiene e comincia con dall'inizio, è il numero esatto.
    assert regole.prova(NOME, "contiene", "12")(riga, CONTESTO) and not regole.prova(NOME, "contiene", "23")(riga, CONTESTO)
    assert regole.prova(NOME, "uguale", "1234")(riga, CONTESTO) and not regole.prova(NOME, "uguale", "123")(riga, CONTESTO)
    assert regole.prova(NOME, "non_contiene", "23")(riga, CONTESTO) and regole.prova(NOME, "diverso", "123")(riga, CONTESTO)
    # L'apostrofo tipografico, come lo mettono i programmi di scrittura, e il trattino valgono uno spazio.
    assert luoghi.chiave_di_confronto(f"Sant{chr(0x2019)}Angelo-Lodigiano") == "sant angelo lodigiano"


def test_le_scelte_a_voci_insieme_e_i_si_o_no():
    entrambi = RigaFinta({"stato": frozenset({"libero", "tuo"}), "mancino": True})
    assert regole.prova(STATO, "uguale", "libero")(entrambi, CONTESTO) and regole.prova(STATO, "uguale", "tuo")(entrambi, CONTESTO)
    assert not regole.prova(STATO, "diverso", "tuo")(entrambi, CONTESTO)
    assert regole.prova(MANCINO, "uguale", True)(entrambi, CONTESTO) and not regole.prova(MANCINO, "uguale", False)(entrambi, CONTESTO)
    assert [op for op, _n in regole.operatori(MANCINO)] == ["uguale"] and [op for op, _n in regole.operatori(COSTO)][-2:] == ["manca", "presente"]


def test_la_e_lega_prima_della_o():
    def r(collegamento, chiave):
        return mercato.Regola(collegamento, G, chiave, "uguale", True)
    insieme = [r("e", "a"), r("e", "b"), r("o", "c"), r("e", "d"), r("o", "e")]
    assert [[x.caratteristica for x in alternativa] for alternativa in regole.alternative(insieme)] == [["a", "b"], ["c", "d"], ["e"]]
    assert regole.alternative([]) == [] and len(regole.alternative([r("o", "a")])) == 1
    cars = {chiave: _finta(chiave, regole.SI_NO, peso=peso) for chiave, peso in (("a", 3), ("b", 1), ("c", 1), ("d", 0), ("e", 2))}
    compilate = regole.compila(insieme, lambda regola: cars[regola.caratteristica])
    assert [len(prove) for prove in compilate] == [2, 2, 1]
    # A e B, oppure C e D, oppure E: chi ha C e D senza A è trovato, chi ha A senza B no.

    def trovata(dati):
        return any(all(p(RigaFinta(dati), CONTESTO) for p in prove) for prove in compilate)
    assert trovata({"c": True, "d": True}) and trovata({"a": True, "b": True}) and trovata({"e": True})
    assert not trovata({"a": True, "c": True}) and not trovata({"b": True, "d": True})


def test_le_prove_vanno_dalla_piu_leggera():
    chiamate = []
    pesante = regole.Caratteristica("pesante", "Pesante", regole.SI_NO, lambda r, _c: chiamate.append(1) or True, peso=9)
    leggera = regole.Caratteristica("leggera", "Leggera", regole.SI_NO, lambda r, _c: r.dati["leggera"], peso=0)
    cars = {"pesante": pesante, "leggera": leggera}
    prove = regole.compila([mercato.Regola("e", G, "pesante", "uguale", True), mercato.Regola("e", G, "leggera", "uguale", True)],
                           lambda regola: cars[regola.caratteristica])[0]
    assert not all(p(RigaFinta({"leggera": False}), CONTESTO) for p in prove) and chiamate == []
    assert all(p(RigaFinta({"leggera": True}), CONTESTO) for p in prove) and chiamate == [1]


# Il catalogo, la memoria e la ricerca, sul mondo delle prove.

def test_il_catalogo_dei_due_bersagli():
    giocatori, allenatori = mercato.CATALOGO[G], mercato.CATALOGO[A]
    assert len(giocatori) == 58 and len(allenatori) == 15
    assert list(giocatori)[:10] == ["stato", "nome", "numero", "sesso", "classe", "eta", "valore", "costo", "stipendio", "mesi_contratto"]
    assert list(allenatori) == ["stato", "nome", "numero", "sesso", "classe", "eta", "tipo", "visus", "stipendio", "mesi_contratto", "regione",
                                "provincia", "comune", "polisportiva", "gloria_richiesta"]
    assert all(chiave in giocatori for chiave in mercato.CARATTERISTICHE) and all(chiave in giocatori for chiave in mercato.TRATTI)
    assert [chiave for chiave, _ in regole.voci(giocatori["stato"])] == ["in_attivita", "sul_mercato", "libero", "in_vendita", "del_computer", "tuo",
                                                                          "ritirato", "uscito"]
    assert [nome for _chiave, nome in regole.voci(allenatori["stato"])] == ["libero", "capo allenatore", "assistente", "allena per il computer",
                                                                            "del tuo staff", "in prelazione per altri"]
    massimi = {"eta": 120, "valore": 100_000, "costo": 100_000_000, "stipendio": 10_000_000, "mesi_contratto": 240, "esperienza": 20, "ambizione": 100,
               "gloria_richiesta": 1_500}
    assert {chiave: giocatori[chiave].massimo for chiave in massimi} == massimi
    assert {chiave for chiave, car in giocatori.items() if car.puo_mancare} == {"costo", "stipendio", "mesi_contratto", "regione", "provincia", "comune",
                                                                                 "polisportiva"}
    assert {chiave for chiave, car in allenatori.items() if car.puo_mancare} == {"mesi_contratto", "regione", "provincia", "comune", "polisportiva"}
    for catalogo in (giocatori, allenatori):
        for car in catalogo.values():
            assert regole.operatori(car) and car.nome and (car.etichetta or car.tipo in (regole.SCELTA, regole.SI_NO)), car.chiave
            # Chi salta la memoria dà già il dato nella forma che si confronta: niente numeri da arrotondare né testi.
            assert car.memorizza or car.tipo in (regole.SCELTA, regole.SI_NO) or car.chiave == "numero", car.chiave
    assert {car.chiave for car in giocatori.values() if not car.memorizza} >= {"stato", "numero", "sesso"}
    assert len(mercato.ORDINI) == 41 and set(mercato.ORDINI_COMUNI) <= set(dict(mercato.ORDINI))
    assert len(regole.voci(giocatori["regione"])) == len(luoghi.regioni()) and regole.voci(giocatori["regione"])[0] == (luoghi.regioni()[0],) * 2


def test_le_voci_dello_stato_valgono_insieme(mondo):
    cpu0 = next(p for p in sorted(mondo.polisportive.values(), key=lambda p: p.nome) if p.is_cpu_controlled)
    memoria = mercato.Memoria(mondo)
    righe = {r.persona.id: r for r in memoria.righe_di(G)}
    assert len(righe) == len(mondo.giocatori)
    # Il 10 è del computer, e il computer lo vende: in attività, sul mercato, in vendita da altri e tesserato del computer.
    assert righe[10].stati == {mercato.IN_ATTIVITA, mercato.SUL_MERCATO, mercato.IN_VENDITA, mercato.DEL_COMPUTER} and righe[10].stato == mercato.IN_VENDITA
    assert righe[10].polisportiva is cpu0 and righe[10].prezzo == righe[10].costo == 3000
    # Il 6 è tuo, in vendita da Pat-Milano a 1 euro: resta tuo, e non è in vendita da altri.
    assert righe[6].stati == {mercato.IN_ATTIVITA, mercato.TUO} and righe[6].costo == 1 and righe[6].di_chi == mercato.TUA_ALTRA
    assert righe[1].stati == {mercato.IN_ATTIVITA, mercato.TUO} and righe[1].costo is None and righe[1].prezzo == 500
    assert righe[11].stati == {mercato.IN_ATTIVITA, mercato.DEL_COMPUTER}
    assert righe[40].stati == {mercato.RITIRATO} and righe[45].stati == {mercato.USCITO}
    liberi = [r for r in righe.values() if r.stato == mercato.LIBERO]
    assert liberi and all(r.stati == {mercato.IN_ATTIVITA, mercato.SUL_MERCATO, mercato.LIBERO} for r in liberi)
    allenatori = {r.persona.numero: r for r in memoria.righe_di(A)}
    assert len(allenatori) == len(mondo.allenatori)
    assert {r.stati for r in allenatori.values() if not r.persona.libero} == {frozenset({mercato.DEL_COMPUTER, mercato.CAPO}), frozenset({mercato.TUO, mercato.ASSISTENTE})}
    a = next(r for r in allenatori.values() if r.persona.libero)
    a.persona.prelazione = cpu0.nome
    memoria.dimentica_le_righe()
    assert next(r for r in memoria.righe_di(A) if r.persona is a.persona).stati == {mercato.LIBERO, mercato.IN_PRELAZIONE}
    a.persona.prelazione = mondo.miapolisportiva_attiva.nome
    memoria.dimentica_le_righe()
    assert next(r for r in memoria.righe_di(A) if r.persona is a.persona).stati == {mercato.LIBERO}


def test_tesserati_del_computer_comprende_chi_il_computer_vende(mondo):
    computer = _ids(_cerca(mondo, _regola(G, "stato", "uguale", mercato.DEL_COMPUTER)))
    cpu = [p for p in mondo.polisportive.values() if p.is_cpu_controlled]
    assert computer == set().union(*(p.tesserati for p in cpu)) and 10 in computer
    assert _ids(_cerca(mondo, _regola(G, "stato", "uguale", mercato.IN_VENDITA))) == {10}
    mercato_ = _ids(_cerca(mondo, _regola(G, "stato", "uguale", mercato.SUL_MERCATO)))
    morti = mondo._ids_morti_processati_sessione
    assert mercato_ == {gid for gid, g in mondo.giocatori.items() if g.appartenenza == "*" and not g.ritirato and gid not in morti} | {10}
    assert len(_cerca(mondo, _regola(G, "stato", "uguale", mercato.IN_ATTIVITA))) == len(mondo.giocatori) - 6


def test_il_costo_e_lo_stipendio_si_calcolano_tardi(mondo, monkeypatch):
    ingaggi, mercati = [], []
    vero_ingaggio, vero_mercato = mercato.ingaggio_richiesto, mercato.valore_di_mercato
    monkeypatch.setattr(mercato, "ingaggio_richiesto", lambda g, p: ingaggi.append(g.id) or vero_ingaggio(g, p))
    monkeypatch.setattr(mercato, "valore_di_mercato", lambda g, oggi: mercati.append(g.id) or vero_mercato(g, oggi))
    memoria = mercato.Memoria(mondo)
    trovati = _cerca(mondo, _regola(G, "stato", "uguale", mercato.SUL_MERCATO), ordine="valore_alto", memoria=memoria)
    assert trovati and ingaggi == [] and mercati == []
    libero = next(r for r in trovati if r.stato == mercato.LIBERO)
    assert libero.costo == economia.ingaggio_richiesto(libero.persona, mondo.miapolisportiva_attiva) and ingaggi == [libero.persona.id]
    assert libero.stipendio == economia.stipendio(libero.persona)
    # Il costo come regola lo legge per tutti quelli che restano, una volta sola.
    _cerca(mondo, _regola(G, "stato", "uguale", mercato.LIBERO), _regola(G, "costo", "minore_uguale", 1_000_000), memoria=memoria)
    quanti = len(ingaggi)
    assert quanti == len({r.persona.id for r in memoria.righe_di(G) if r.stato == mercato.LIBERO})
    _cerca(mondo, _regola(G, "stato", "uguale", mercato.LIBERO), _regola(G, "costo", "maggiore", 10), memoria=memoria)
    assert len(ingaggi) == quanti
    computer = next(r for r in memoria.righe_di(G) if r.stato == mercato.DEL_COMPUTER)
    assert mercati == [] and computer.costo == economia.valore_di_mercato(computer.persona, ORA) and mercati == [computer.persona.id]
    ritirato = next(r for r in memoria.righe_di(G) if r.stato == mercato.RITIRATO)
    assert ritirato.costo is None and ritirato.stipendio is None
    tuo = next(r for r in memoria.righe_di(G) if r.persona.id == 2)
    assert tuo.stipendio == economia.stipendio_pagato(tuo.persona)
    # Senza polisportiva attiva i liberi non hanno un costo.
    mondo.miapolisportiva_attiva = None
    senza = mercato.Memoria(mondo)
    assert all(r.costo is None for r in senza.righe_di(G) if r.stato == mercato.LIBERO)


def test_la_memoria_ricorda_ogni_lettura_e_le_chiavi_di_confronto(mondo, monkeypatch):
    chiavi, punteggi = [], []
    vera_chiave, vero_punteggio = luoghi.chiave_di_confronto, classe.punteggio
    monkeypatch.setattr(luoghi, "chiave_di_confronto", lambda testo: chiavi.append(testo) or vera_chiave(testo))
    monkeypatch.setattr(classe, "punteggio", lambda g: punteggi.append(g.id) or vero_punteggio(g))
    memoria = mercato.Memoria(mondo)
    in_attivita = _regola(G, "stato", "uguale", mercato.IN_ATTIVITA)
    primi = _cerca(mondo, in_attivita, _regola(G, "nome", "contiene", "ro"), memoria=memoria)
    quante = len(chiavi)
    assert quante == len(mondo.giocatori) - 6 + 1
    assert _cerca(mondo, in_attivita, _regola(G, "nome", "contiene", "ros"), memoria=memoria) and len(chiavi) == quante + 1
    assert _numeri(_cerca(mondo, in_attivita, _regola(G, "nome", "contiene", "ro"), memoria=memoria)) == _numeri(primi)
    _cerca(mondo, in_attivita, _regola(G, "classe", "migliore_uguale", 60), ordine="classe", memoria=memoria)
    assert len(punteggi) == len(set(punteggi)) == len(mondo.giocatori) - 6
    _cerca(mondo, in_attivita, _regola(G, "classe", "peggiore", 30), ordine="classe", memoria=memoria)
    assert len(punteggi) == len(mondo.giocatori) - 6
    # Dopo un esito: dimentica la persona, e le righe si rifanno.
    g = mondo.giocatori[50]
    memoria.dimentica(g)
    memoria.leggi(mercato.caratteristica(G, "classe"), next(r for r in memoria.righe_di(G) if r.persona is g))
    assert punteggi.count(50) == 2
    memoria.dimentica_le_righe()
    assert memoria._righe is None and memoria._letture == {}
    assert _numeri(_cerca(mondo, in_attivita, _regola(G, "nome", "contiene", "ro"), memoria=memoria)) == _numeri(primi)


def test_dopo_un_esito_le_righe_cambiano_stato(mondo):
    memoria = mercato.Memoria(mondo)
    libero = next(r for r in memoria.righe_di(G) if r.stato == mercato.LIBERO).persona
    assert libero.id in _ids(_cerca(mondo, _regola(G, "stato", "uguale", mercato.LIBERO), memoria=memoria))
    mondo._entra(mondo.miapolisportiva_attiva, libero)
    memoria.dimentica(libero)
    memoria.dimentica_le_righe()
    assert libero.id not in _ids(_cerca(mondo, _regola(G, "stato", "uguale", mercato.LIBERO), memoria=memoria))
    assert libero.id in _ids(_cerca(mondo, _regola(G, "stato", "uguale", mercato.TUO), memoria=memoria))


def test_senza_regole_non_si_trova_nessuno_e_i_bersagli(mondo):
    assert mercato.cerca(mondo, mercato.Filtri()) == []
    donne_g = _cerca(mondo, _regola(G, "sesso", "uguale", "f"))
    assert donne_g and not any(r.allenatore for r in donne_g)
    donne_a = _cerca(mondo, _regola(A, "sesso", "uguale", "f"))
    assert all(r.allenatore for r in donne_a)
    # Con la o, le due liste insieme; in un'alternativa che mescola i bersagli non si trova nessuno.
    insieme = _cerca(mondo, _regola(G, "sesso", "uguale", "f"), _regola(A, "sesso", "uguale", "f", mercato.O))
    assert len(insieme) == len(donne_g) + len(donne_a)
    assert _cerca(mondo, _regola(G, "sesso", "uguale", "f"), _regola(A, "sesso", "uguale", "f")) == []
    regole_miste = (_regola(G, "sesso", "uguale", "f"), _regola(A, "sesso", "uguale", "f"), _regola(G, "sesso", "uguale", "m", mercato.O))
    assert mercato.alternative_miste(regole_miste) == [1] and mercato.bersagli_delle_regole(regole_miste) == (G,)
    assert _numeri(_cerca(mondo, *regole_miste)) == _numeri(_cerca(mondo, _regola(G, "sesso", "uguale", "m")))
    assert mercato.bersagli_delle_regole((_regola(A, "eta", "maggiore", 3), _regola(G, "eta", "maggiore", 3, mercato.O))) == (G, A)
    assert mercato.conta_le_righe(insieme) == (len(donne_g), len(donne_a))


def test_gli_ordini_comuni_mescolano_e_gli_altri_mettono_gli_allenatori_in_fondo(mondo):
    oggi = mondo.datetime_corrente_simulazione
    tutti = (_regola(G, "stato", "uguale", mercato.IN_ATTIVITA), _regola(A, "numero", "maggiore", 0, mercato.O))
    per_eta = _cerca(mondo, *tutti, ordine="eta_giovane")
    eta = [r.persona.eta(oggi) if r.allenatore else r.persona.eta for r in per_eta]
    assert eta == sorted(eta) and any(r.allenatore for r in per_eta[: len(per_eta) - 1])
    per_classe = _cerca(mondo, *tutti, ordine="classe")
    memoria = mercato.Memoria(mondo)
    livelli = [r.persona.livello if r.allenatore else memoria.livello(r.persona) for r in per_classe]
    assert livelli == sorted(livelli)
    # A parità di livello, prima i giocatori.
    for (prima, livello_di_prima), (dopo, livello_di_dopo) in itertools.pairwise(zip(per_classe, livelli, strict=True)):
        if livello_di_prima == livello_di_dopo:
            assert not (prima.allenatore and not dopo.allenatore)
    numeri = _cerca(mondo, *tutti, ordine="numero")
    assert [r.numero for r in numeri] == sorted(r.numero for r in numeri)
    mesi = _cerca(mondo, *tutti, ordine="mesi_contratto")
    con = [r for r in mesi if contratti.ha_contratto(r.persona)]
    assert mesi[: len(con)] == con
    per_valore = _cerca(mondo, *tutti, ordine="valore_alto")
    allenatori = [r for r in per_valore if r.allenatore]
    assert per_valore[-len(allenatori):] == allenatori
    assert [(r.persona.livello, r.persona.eta(oggi)) for r in allenatori] == sorted((r.persona.livello, r.persona.eta(oggi)) for r in allenatori)
    valori = [r.persona.indice_collettivo_valore for r in per_valore if not r.allenatore]
    assert valori == sorted(valori, reverse=True)
    for chiave, _nome in mercato.ORDINI:
        righe = _cerca(mondo, *tutti, ordine=chiave)
        assert len(righe) == len(per_eta), chiave


def test_la_regola_in_preparazione_e_i_suoi_aiuti(mondo):
    prep = mercato.Preparazione(mercato.O, G, "eta", "minore_uguale", "20")
    regola, perche = mercato.regola_pronta(prep)
    assert regola == _regola(G, "eta", "minore_uguale", 20, mercato.O) and perche is None
    assert mercato.regola_pronta(dataclasses.replace(prep, valore="")) == (None, None)
    assert mercato.regola_pronta(dataclasses.replace(prep, valore="20,5")) == (None, regole.DECIMALI)
    assert mercato.regola_pronta(mercato.Preparazione(mercato.E, G, "costo", "manca", "")) == (_regola(G, "costo", "manca", None), None)
    assert mercato.regola_pronta(mercato.Preparazione(mercato.E, G, "sesso", "uguale", None)) == (None, None)
    # La prima regola ha sempre la e, anche quando la preparazione è l'unica.
    soltanto = mercato.con_la_preparazione(mercato.Filtri(), prep)
    assert soltanto.regole == (_regola(G, "eta", "minore_uguale", 20),)
    serie = mercato.filtri_di_serie("mercato")
    con = mercato.con_la_preparazione(serie, prep)
    assert con.regole == (*serie.regole, regola) and con.ordine == serie.ordine
    assert mercato.con_la_preparazione(serie, dataclasses.replace(prep, valore="x")) == serie
    assert mercato.con_la_prima_e((_regola(G, "eta", "minore", 3, mercato.O), regola)) == (_regola(G, "eta", "minore", 3), regola)
    assert mercato.svuota_il_valore(prep).valore == "" and mercato.svuota_il_valore(mercato.Preparazione(mercato.E, G, "sesso", "uguale", "f")).valore is None
    assert mercato.con_la_caratteristica(prep, "mancino") == mercato.Preparazione(mercato.O, G, "mancino", "uguale", None)
    # Il bersaglio nuovo tiene la caratteristica se ce l'ha, altrimenti va su Stato.
    assert mercato.con_il_bersaglio(prep, A) == dataclasses.replace(prep, bersaglio=A)
    assert mercato.con_il_bersaglio(mercato.Preparazione(mercato.E, G, "valore", "maggiore", "3"), A) == mercato.Preparazione(mercato.E, A, "stato", "uguale", None)
    assert mercato.con_il_bersaglio(mercato.Preparazione(mercato.E, G, "stato", "uguale", mercato.SUL_MERCATO), A).valore is None
    assert mercato.con_il_bersaglio(mercato.Preparazione(mercato.E, G, "stato", "uguale", mercato.LIBERO), A).valore == mercato.LIBERO
    assert mercato.con_il_bersaglio(mercato.Preparazione(mercato.E, G, "costo", "manca", ""), A) == mercato.Preparazione(mercato.E, A, "stato", "uguale", None)
    assert mercato.pulisci_la_preparazione(dataclasses.replace(prep, valore="2\t0\n")).valore == "20"
    assert len(mercato.pulisci_la_preparazione(dataclasses.replace(prep, valore="x" * 80)).valore) == 50
    due = (_regola(G, "eta", "minore", 3), _regola(G, "eta", "maggiore", 30, mercato.O))
    assert mercato.alternativa_della_preparazione(due, prep) == (3, 3) and mercato.alternativa_della_preparazione(due, dataclasses.replace(prep, collegamento="e")) == (2, 2)
    assert mercato.alternativa_della_preparazione((), prep) == (1, 1)


def test_le_mosse_sull_elenco_delle_regole():
    prima, seconda, terza = _regola(G, "eta", "minore", 30), _regola(G, "sesso", "uguale", "f", mercato.O), _regola(G, "mancino", "uguale", True)
    filtri = mercato.Filtri((prima, seconda), "classe")
    aggiunti, perche = mercato.aggiungi_la_regola(filtri, mercato.Preparazione(mercato.E, G, "mancino", "uguale", True))
    assert aggiunti == mercato.Filtri((prima, seconda, terza), "classe") and perche is None
    assert mercato.aggiungi_la_regola(filtri, mercato.Preparazione(mercato.E, G, "mancino", "uguale", None)) == (filtri, regole.VUOTO)
    assert mercato.aggiungi_la_regola(filtri, mercato.Preparazione(mercato.E, G, "eta", "minore", "3,5")) == (filtri, regole.DECIMALI)
    pieni = mercato.Filtri(tuple(_regola(G, "eta", "minore", n) for n in range(mercato.LIMITE_DELLE_REGOLE)))
    assert mercato.aggiungi_la_regola(pieni, mercato.Preparazione(mercato.E, G, "eta", "minore", "3")) == (pieni, mercato.AL_LIMITE)
    # Togliendo la prima, quella che sale in cima prende la e; spostando, ogni regola tiene il suo collegamento.
    assert mercato.togli_la_regola(aggiunti, 0).regole == (dataclasses.replace(seconda, collegamento=mercato.E), terza)
    assert mercato.togli_la_regola(aggiunti, 2).regole == (prima, seconda)
    with pytest.raises(IndexError):
        mercato.togli_la_regola(aggiunti, 3)
    spostati, posto = mercato.sposta_la_regola(aggiunti, 2, -1)
    assert spostati.regole == (prima, terza, seconda) and posto == 1
    in_cima, posto = mercato.sposta_la_regola(aggiunti, 1, -1)
    assert in_cima.regole == (dataclasses.replace(seconda, collegamento=mercato.E), prima, terza) and posto == 0
    assert mercato.sposta_la_regola(aggiunti, 0, -1) is None and mercato.sposta_la_regola(aggiunti, 2, 1) is None
    cambiati = mercato.cambia_il_collegamento(aggiunti, 2, mercato.O)
    assert cambiati.regole[2].collegamento == mercato.O and mercato.cambia_il_collegamento(aggiunti, 0, mercato.O) is None
    # Salva filtri aggiunge la preparazione che conta, finché le regole sono meno di 50.
    pronta = mercato.Preparazione(mercato.E, G, "mancino", "uguale", True)
    assert mercato.filtri_per_salva_filtri(filtri, pronta) == (aggiunti, mercato.AGGIUNTA)
    assert mercato.filtri_per_salva_filtri(pieni, pronta) == (pieni, mercato.FUORI)
    assert mercato.filtri_per_salva_filtri(filtri, dataclasses.replace(pronta, valore=None)) == (filtri, None)
    # Ctrl+F torna sul nome, e tiene il testo soltanto se la preparazione era già quella.
    assert mercato.preparazione_della_ricerca_veloce(mercato.Preparazione(mercato.O, G, "nome", "contiene", "ros")) == mercato.Preparazione(valore="ros")
    assert mercato.preparazione_della_ricerca_veloce(mercato.Preparazione(mercato.E, G, "eta", "minore", "20")) == mercato.Preparazione()
    assert mercato.preparazione_della_ricerca_veloce(mercato.Preparazione(mercato.E, A, "nome", "contiene", "ros")) == mercato.Preparazione()


def test_i_preset_di_serie_sono_fatti_di_regole_con_la_sola_e():
    assert set(mercato._FILTRI_DI_SERIE) == {chiave for chiave, _nome in mercato.PRESET_DI_SERIE}
    for chiave, _nome in mercato.PRESET_DI_SERIE:
        filtri = mercato.filtri_di_serie(chiave)
        assert filtri.regole and all(r.collegamento == mercato.E for r in filtri.regole) and filtri.ordine in dict(mercato.ORDINI)
        assert mercato.problema_dei_filtri(mercato.filtri_a_dizionario(filtri)) is None
    for porta in mercato.PORTE:
        stato = mercato.stato_di_serie(porta)
        assert stato.scelta == mercato.PRESET_DELLA_PORTA[porta] and stato.attuali == mercato.filtri_di_serie(stato.scelta)
        assert stato.preparazione == mercato.Preparazione(mercato.E, A if porta == "allenatori" else G, "nome", "contiene", "")


def test_la_ricerca_veloce_restringe_tutto_il_mercato(mondo):
    """L'obiezione 1 della critica: col Mercato sul mercato, senza o, il nome scritto restringe sia i liberi sia chi è in vendita."""
    stato = mercato.stato_di_serie("mercato")
    for scritto in ("a", "ro", "1"):
        prep = dataclasses.replace(stato.preparazione, valore=scritto)
        trovati = mercato.cerca(mondo, mercato.con_la_preparazione(stato.attuali, prep))
        tutti = mercato.cerca(mondo, stato.attuali)
        nome = mercato.caratteristica(G, "nome")
        attesi = [r for r in tutti if regole.prova(nome, "contiene", scritto)(r, regole.Contesto())]
        assert _numeri(trovati) == _numeri(attesi) and len(trovati) < len(tutti)


# L'equivalenza col motore a schede, che col cambio della finestra è uscito: i dodici preset di serie trovano, sul mondo
# delle prove, le stesse persone nello stesso ordine del motore di prima. Le impronte, quanti sono e l'SHA-256 dei loro
# numeri in ordine, sono state prese con tutti e due i motori la sera del 24 ottobre 2026, prima che quello a schede
# uscisse, ed erano uguali; fino ad allora l'oracolo che traduceva i filtri di prima in regole le provava filtro per filtro.
IMPRONTE_DEL_MOTORE_DI_PRIMA = {
    "mercato": (86, "d97af938301db433"), "tutti_in_attivita": (114, "6ba143245c95c222"), "piu_forti": (114, "15375b0b64ad8dc6"),
    "giovani_migliori": (25, "7ee4bec3d63ee54e"), "liberi_convenienti": (85, "ee9b9ea409413eb8"), "affari_in_vendita": (1, "7920a424ebc3aa30"),
    "avversari_amichevole": (114, "15375b0b64ad8dc6"), "piu_titolati": (114, "6ba143245c95c222"), "allenatori_liberi": (4, "f98358438a69ad08"),
    "capi_migliori": (1, "b4cf08021c81c4e6"), "assistenti_migliori": (1, "6bbdd42a78b227f6"), "nuovi_arrivati": (21, "8ba16bba6f46900b"),
}


def _impronta(righe):
    numeri = [[r.allenatore, r.numero] for r in righe]
    return len(numeri), hashlib.sha256(json.dumps(numeri).encode()).hexdigest()[:16]


def test_i_preset_di_serie_trovano_quello_che_trovava_il_motore_di_prima(mondo):
    memoria = mercato.Memoria(mondo)
    assert set(IMPRONTE_DEL_MOTORE_DI_PRIMA) == set(dict(mercato.PRESET_DI_SERIE))
    for chiave, nome in mercato.PRESET_DI_SERIE:
        assert _impronta(mercato.cerca(mondo, mercato.filtri_di_serie(chiave), memoria)) == IMPRONTE_DEL_MOTORE_DI_PRIMA[chiave], nome


def test_il_costo_senza_polisportiva_attiva_e_una_differenza_voluta(mondo):
    """
    Prima il limite di costo senza polisportiva attiva non contava; con le regole vale per chi ha un costo, e i liberi,
    che non ce l'hanno, non lo passano: si riprendono con la o e non ha il dato.
    """
    mondo.miapolisportiva_attiva = None
    sul_mercato = _regola(G, "stato", "uguale", mercato.SUL_MERCATO)
    assert _cerca(mondo, sul_mercato, _regola(G, "costo", "minore_uguale", 1000)) == []
    con_il_dato_che_manca = _cerca(mondo, sul_mercato, _regola(G, "costo", "minore_uguale", 1000), _regola(G, "stato", "uguale", mercato.SUL_MERCATO, mercato.O),
                                   _regola(G, "costo", "manca", None))
    assert _ids(con_il_dato_che_manca) == _ids(_cerca(mondo, sul_mercato)) - {10}


def test_le_altre_differenze_volute(mondo):
    """I numeri come la scheda, i testi senza accenti e i mesi di contratto interi, ciascuno con un caso che li tocca davvero."""
    tutti = _regola(G, "stato", "uguale", mercato.IN_ATTIVITA)
    g = mondo.giocatori[70]
    # 149,96 il motore di prima lo lasciava fuori da un valore minimo di 150; la scheda scrive 150,0, e la regola lo trova.
    g.indice_collettivo_valore = 149.96
    assert 70 in _ids(_cerca(mondo, tutti, _regola(G, "valore", "maggiore_uguale", 150.0)))
    g.cognome = "Forlì"
    assert 70 in _ids(_cerca(mondo, tutti, _regola(G, "nome", "contiene", "forli")))
    # Il 6 ottobre, un contratto fino al 30 novembre: 1,8 mesi di calendario per il motore di prima, 1 mese intero adesso.
    tuo = mondo.giocatori[2]
    tuo.contratto_scadenza = datetime.datetime(2026, 11, 30, 12, 0)
    assert 2 in _ids(_cerca(mondo, tutti, _regola(G, "mesi_contratto", "minore_uguale", 1)))
