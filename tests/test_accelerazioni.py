"""
Le accelerazioni della decisione 4 di Gabriele del 14 ottobre 2026, il giorno simulato e il salvataggio
a regime, provate uguali al modo di prima. Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus
5.5, modalità auto).
Le impronte di test_identita_motore.py dicono che il mondo resta lo stesso fino all'ultimo bit; qui
ogni accelerazione si confronta col conto di prima su casi tirati a sorte, pareggi compresi: la scelta
del mercato del computer con lo scorrere di tutte le righe, la scelta delle iscrizioni automatiche con
iscrizioni.scegli, e il salvataggio, che scrive i giocatori una volta sola, con il documento, la firma
e la rilettura del modo di prima, anche quando il segnaposto compare altrove e la scrittura torna al
modo di prima. Un file scritto nel modo di prima si legge uguale.
"""

import copy
import datetime
import gc
import gzip
import json
import random
import types

import pytest

import allenamento
import archivio
import costanti
import iscrizioni
import modelli
import modelli_torneo
import mondo as modulo_mondo
import palmares
import tratti
import valore
from costanti import FILE_MONDO
from modelli import Giocatore, Polisportiva
from mondo import Mondo

INIZIO = datetime.datetime(2026, 3, 1, 9, 30)
INIZIO_UTC = datetime.datetime(2026, 3, 1, 8, 30, tzinfo=datetime.UTC)


# Il mercato del computer.

def _scelta_di_prima(righe, poli, spendibile, massimo, debole):
    """La scelta di _compra_dal_mercato prima della tappa 12: tutte le righe, la più forte e, a pari forza, la prima."""
    scelta = None
    for g, venditore, prezzo, prezzo_massimo, chiesto in righe:
        if venditore is poli or venditore.in_vendita.get(g.id) != prezzo:
            continue
        if prezzo > spendibile or prezzo > prezzo_massimo or chiesto > massimo:
            continue
        if debole is not None and g.indice_collettivo_valore <= debole.indice_collettivo_valore:
            continue
        if scelta is None or g.indice_collettivo_valore > scelta[0].indice_collettivo_valore:
            scelta = (g, venditore, prezzo)
    return scelta


def _mercato_a_sorte(rng):
    venditori = [types.SimpleNamespace(nome=f"V{n}", in_vendita={}) for n in range(5)]
    righe = []
    for gid in range(rng.randint(0, 40)):
        # Pochi valori diversi, perché i pareggi ci siano.
        g = types.SimpleNamespace(id=gid, indice_collettivo_valore=rng.choice((80.0, 95.5, 110.25, 140.0, 140.0)))
        venditore = rng.choice(venditori)
        prezzo = rng.randrange(100, 5000, 100)
        venditore.in_vendita[gid] = prezzo
        righe.append((g, venditore, prezzo, rng.uniform(50, 6000), rng.randrange(300, 3000, 10)))
    # Qualcuno è già stato comprato, a qualcun altro è cambiato il prezzo.
    for g, venditore, _prezzo, _massimo, _chiesto in righe:
        tiro = rng.random()
        if tiro < 0.15:
            venditore.in_vendita.pop(g.id, None)
        elif tiro < 0.25:
            venditore.in_vendita[g.id] += 100
    return righe, venditori


def test_il_mercato_sceglie_come_prima():
    rng = random.Random("mercato del computer")
    for _ in range(3000):
        righe, venditori = _mercato_a_sorte(rng)
        mercato = modulo_mondo._Mercato(righe)
        for _ in range(5):
            poli = rng.choice([*venditori, types.SimpleNamespace(nome="Compratrice", in_vendita={})])
            spendibile = rng.uniform(-500, 6000)
            massimo = rng.uniform(-200, 3500)
            debole = None if rng.random() < 0.5 else types.SimpleNamespace(indice_collettivo_valore=rng.choice((70.0, 95.5, 140.0)))
            assert mercato.scelta(poli, spendibile, massimo, debole) == _scelta_di_prima(righe, poli, spendibile, massimo, debole)


# Le iscrizioni automatiche.

def _edizioni_a_sorte(rng, oggi):
    edizioni = []
    for numero in range(rng.randint(0, 12)):
        inizio = oggi + datetime.timedelta(days=rng.randint(1, 25))
        edizioni.append(types.SimpleNamespace(
            id=numero + 1, individuale=True, qualificazione=modelli_torneo.NESSUNA, sesso=rng.choice(("m", "f", "aperto")),
            data_inizio=inizio, data_fine=inizio + datetime.timedelta(days=rng.randint(0, 3)), filtri=rng.random() < 0.3,
            oggetto_modello=numero + 1, importanza=rng.choice((1.0, 1.0, 2.0, 4.0)), nome=rng.choice(("Open", "Gran Premio", "Open"))))
    return edizioni


def test_le_iscrizioni_automatiche_scelgono_come_prima(monkeypatch):
    # Un filtro di classe e d'età finto, ma fisso per ogni coppia di edizione e giocatore.
    monkeypatch.setattr(modelli_torneo, "idoneo", lambda modello, g: hash((modello, g.id)) % 3 != 0)
    rng = random.Random("iscrizioni automatiche")
    oggi = datetime.date(2030, 5, 10)
    for _ in range(2000):
        aperte = _edizioni_a_sorte(rng, oggi)
        scelte = iscrizioni._Scelte(aperte)
        for gid in range(6):
            g = types.SimpleNamespace(id=gid, sesso=rng.choice(("m", "f")))
            s = oggi + datetime.timedelta(days=rng.randint(1, 12))
            impegni = [(oggi + datetime.timedelta(days=giorno), oggi + datetime.timedelta(days=giorno + rng.randint(0, 2)))
                       for giorno in rng.sample(range(1, 25), rng.randint(0, 3))]
            tolte = {ed.id for ed in aperte if rng.random() < 0.15} or None
            di_prima = iscrizioni.scegli([e for e in aperte if e.id not in tolte] if tolte else aperte, g, s, impegni)
            assert scelte.scegli(g, s, impegni, tolte) is di_prima


# La finestra della gloria e il declino.

def _somma_di_prima(poli, oggi):
    """La somma del palmarès recente di prima della decisione 4: ogni chiave letta coi suoi numeri."""
    fine = oggi.year * 12 + oggi.month - 1
    medaglie = coppe = 0.0
    for chiave, (m, c) in poli.palmares_recente.items():
        if 0 <= fine - (int(chiave[:4]) * 12 + int(chiave[5:7]) - 1) < palmares.MESI_PALMARES_GLORIA:
            medaglie += m
            coppe += c
    return medaglie, coppe


def test_la_finestra_della_gloria_somma_come_prima():
    rng = random.Random("finestra della gloria")
    for _ in range(500):
        oggi = datetime.date(rng.randint(2026, 2120), rng.randint(1, 12), rng.randint(1, 28))
        poli = types.SimpleNamespace(palmares_recente={})
        for _ in range(rng.randint(0, 80)):
            anno, mese = oggi.year - rng.randint(-1, 7), rng.randint(1, 12)
            # Anche chiavi scritte in un'altra forma, che il conto di sempre legge lo stesso.
            # Lo zero arabo-indiano, che int legge come lo zero.
            chiave = f"{anno:04d}-{mese:02d}" if rng.random() < 0.9 else f"{anno:04d}-{mese:02d}"[:5] + f"{mese:02d}".replace("0", chr(0x660))
            poli.palmares_recente[chiave] = [rng.choice((0.0, 0.6, 30.0, 1.5)) * rng.random(), rng.choice((0.0, 2.0, 100.0)) * rng.random()]
        assert palmares.somma_finestra(poli, oggi) == _somma_di_prima(poli, oggi)


def _declino_di_prima(g, giorni_passati):
    """Il declino della tappa 12 prima della decisione 4, col fattore calcolato ogni volta."""
    inizio = tratti.giorni_inizio_declino(g)
    if giorni_passati <= 0 or g.eta < inizio:
        return
    prog_eta = max(0, g.eta - inizio)
    aging_f = min(1.0, prog_eta / max(1, costanti.AGING_PEAK_AGE_GIORNI - costanti.AGING_START_AGE_GIORNI))
    manten_ann = max(0.0, 1.0 - aging_f * costanti.MAX_AGING_REDUCTION_FACTOR_PER_ANNO_SIM)
    manten_tot = pow(pow(manten_ann, 1.0 / costanti.ANNO_SIMULAZIONE_GIORNI), giorni_passati)
    for attr in costanti.ATTRIBUTI_INVECCHIABILI:
        invecchiata = g.__dict__[attr] * manten_tot
        g.__dict__[attr] = invecchiata if invecchiata > 0.0 else 0.0


def test_il_declino_col_fattore_ricordato_e_quello_di_prima():
    random.seed(3)
    for eta_anni, giorni in ((49.9, 1), (50, 1), (55.5, 1), (63, 1), (70, 1), (63, 30), (80, 1)):
        g = Giocatore(1, INIZIO)
        g.eta = int(eta_anni * costanti.ANNO_SIMULAZIONE_GIORNI)
        copia = copy.deepcopy(g)
        for _ in range(3):
            g._applica_declino_aggregato(giorni)
            _declino_di_prima(copia, giorni)
            g.eta += 1
            copia.eta += 1
        assert [g.__dict__[a].hex() for a in costanti.ATTRIBUTI_INVECCHIABILI] == [copia.__dict__[a].hex() for a in costanti.ATTRIBUTI_INVECCHIABILI]


def _mantenimento_di_prima(g, giorni):
    """Il calo dei livelli alti e l'oblio del primo del mese di prima della decisione 4, con getattr e setattr."""
    perso = 0.0
    oblio = tratti.oblio_mensile(g)
    quota = giorni / costanti.ANNO_SIMULAZIONE_GIORNI
    for c in allenamento.CARATTERISTICHE:
        nome_base, nome_allenata = allenamento._NOMI[c]
        allenata = getattr(g, nome_allenata)
        if allenata <= 0.0:
            continue
        t = allenamento._TETTI[c]
        relativo = (getattr(g, nome_base) + allenata) / t
        nuova = allenata
        if relativo > costanti.SOGLIA_CALO_LIVELLI_ALTI:
            eccesso = (relativo - costanti.SOGLIA_CALO_LIVELLI_ALTI) / (1.0 - costanti.SOGLIA_CALO_LIVELLI_ALTI)
            nuova = max(0.0, nuova - costanti.CALO_MASSIMO_ANNUO * eccesso ** 3 * t * quota)
        nuova *= oblio
        if nuova != allenata:
            perso += allenata - nuova
            setattr(g, nome_allenata, nuova)
    if perso > 0.0:
        g.aggiorna_icv()
    return perso


def test_il_mantenimento_del_mese_e_quello_di_prima():
    random.seed(4)
    rng = random.Random("mantenimento")
    for numero in range(60):
        g = Giocatore(numero + 1, INIZIO)
        for c in allenamento.CARATTERISTICHE:
            nome_base, nome_allenata = allenamento._NOMI[c]
            setattr(g, nome_allenata, max(0.0, allenamento._TETTI[c] * rng.uniform(0.5, 1.0) - getattr(g, nome_base)))
        copia = copy.deepcopy(g)
        giorni = rng.choice((28, 30, 31))
        assert allenamento.mantenimento_del_mese(g, giorni).hex() == _mantenimento_di_prima(copia, giorni).hex()
        assert {k: v for k, v in vars(g).items() if k != "diario"} == {k: v for k, v in vars(copia).items() if k != "diario"}


def test_la_tabella_dei_pesi_ricordata_e_quella_fatta_da_capo(monkeypatch):
    for ambidestro, mancino in ((False, False), (False, True), (True, False), (True, True)):
        g = types.SimpleNamespace(ambidestro=ambidestro, mancino=mancino)
        for _ in range(2):
            assert allenamento._pesi_per_punto(g) == allenamento._tabella_dei_pesi(g, valore.PESI_VALORE)
    # Coi pesi del valore cambiati la tabella si rifà.
    nuovi = {nome: 2 * peso for nome, peso in valore.PESI_VALORE.items()}
    monkeypatch.setattr(valore, "PESI_VALORE", nuovi)
    g = types.SimpleNamespace(ambidestro=False, mancino=True)
    assert allenamento._pesi_per_punto(g) == allenamento._tabella_dei_pesi(g, nuovi)


# Il salvataggio.

def _mondo_popolato(nome_del_club="Club Di Prova"):
    random.seed(99)
    m = Mondo()
    m.datetime_corrente_simulazione = INIZIO
    m.datetime_ultimo_run_reale = INIZIO_UTC
    m.crea_giocatori_casuali(12, INIZIO)
    m.crea_polisportiva_cpu(INIZIO)
    mia = Polisportiva(nome_del_club, "segreta", INIZIO)
    m.polisportive[mia.nome] = mia
    m._entra(mia, m.giocatori[3])
    m.miapolisportiva_attiva = mia
    m.annota(m.giocatori[2], "Una voce del diario.")
    return m


def _testo(percorso):
    return gzip.decompress(percorso.read_bytes()).decode("utf-8")


def _canonico(dato):
    return json.dumps(dato, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def test_il_salvataggio_scrive_i_giocatori_una_volta_sola_e_si_rilegge(cartella_di_prova):
    m = _mondo_popolato()
    contenuto, _avvisi = archivio.scrivi(m, str(cartella_di_prova / FILE_MONDO), str(cartella_di_prova / "copia"))
    testo = _testo(cartella_di_prova / FILE_MONDO)
    letto = json.loads(testo)
    # Lo stesso documento e la stessa firma del modo di prima, con le chiavi di sopra nello stesso ordine.
    assert letto == {**contenuto, "firma": archivio.firma(contenuto)}
    assert list(letto) == [*contenuto, "firma"]
    assert list(letto["mondo"]) == list(contenuto["mondo"])
    # I giocatori nella forma canonica della firma.
    assert f'"giocatori":{_canonico(contenuto["mondo"]["giocatori"])},' in testo
    riletto = Mondo()
    archivio.costruisci(archivio.leggi(str(cartella_di_prova / FILE_MONDO)), riletto)
    assert archivio.componi(riletto) | {"salvato": None} == archivio.componi(m) | {"salvato": None}
    for gid, g in riletto.giocatori.items():
        assert vars(g) == vars(m.giocatori[gid])


def test_col_segnaposto_altrove_il_salvataggio_si_scrive_come_prima(cartella_di_prova):
    # Il segnaposto conta soltanto come testo intero, fra le sue virgolette: qui è il nome di una polisportiva.
    m = _mondo_popolato(archivio._SEGNAPOSTO_GIOCATORI)
    contenuto = archivio.componi(m)
    pezzi = archivio._testo_firmato(contenuto)
    assert pezzi == [json.dumps({**contenuto, "firma": archivio.firma(contenuto)}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")]
    archivio.scrivi(m, str(cartella_di_prova / FILE_MONDO), str(cartella_di_prova / "copia"))
    riletto = Mondo()
    archivio.costruisci(archivio.leggi(str(cartella_di_prova / FILE_MONDO)), riletto)
    assert sorted(riletto.polisportive) == sorted(m.polisportive)


def test_un_file_scritto_nel_modo_di_prima_si_legge_uguale(cartella_di_prova):
    m = _mondo_popolato()
    contenuto = archivio.componi(m)
    di_prima = gzip.compress(json.dumps({**contenuto, "firma": archivio.firma(contenuto)}, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
                             compresslevel=6, mtime=0)
    (cartella_di_prova / "di_prima.json.gz").write_bytes(di_prima)
    archivio.scrivi(m, str(cartella_di_prova / FILE_MONDO), str(cartella_di_prova / "copia"))
    vecchio, nuovo = Mondo(), Mondo()
    archivio.costruisci(archivio.leggi(str(cartella_di_prova / "di_prima.json.gz")), vecchio)
    archivio.costruisci(archivio.leggi(str(cartella_di_prova / FILE_MONDO)), nuovo)
    assert archivio.componi(vecchio) | {"salvato": None} == archivio.componi(nuovo) | {"salvato": None}
    assert list(vecchio.polisportive) == list(nuovo.polisportive)


def test_la_compressione_a_pezzi_ridà_il_testo_intero():
    pezzi = [b'{"a":', ("€" * 50_000).encode("utf-8"), b'"fine"}']
    dati = archivio._comprimi(pezzi)
    assert gzip.decompress(dati) == b"".join(pezzi)
    # L'intestazione di gzip.compress: l'ora a zero e il sistema 255.
    assert dati[:4] == gzip.compress(b"x", compresslevel=6, mtime=0)[:4]
    assert dati[4:8] == b"\x00\x00\x00\x00" and dati[9] == 255
    assert archivio._comprimi(pezzi) == dati


@pytest.mark.parametrize("accesa", [True, False])
def test_la_raccolta_della_memoria_torna_com_era(cartella_di_prova, accesa):
    m = _mondo_popolato()
    prima = gc.isenabled()
    try:
        if not accesa:
            gc.disable()
        archivio.scrivi(m, str(cartella_di_prova / FILE_MONDO), str(cartella_di_prova / "copia"))
        assert gc.isenabled() is accesa
    finally:
        if prima:
            gc.enable()


def test_le_date_in_testo_sono_quelle_di_isoformat():
    roma = datetime.timezone(datetime.timedelta(hours=1))
    date = [datetime.datetime(2031, 4, 5, 9, 0), datetime.datetime(2031, 4, 5, 9, 0, 0, 1), datetime.datetime(2031, 4, 5, 9, 0, fold=1),
            datetime.datetime(2031, 4, 5, 9, 0, tzinfo=datetime.UTC), datetime.datetime(2031, 4, 5, 10, 0, tzinfo=roma), datetime.date(2031, 4, 5)]
    for _ in range(2):
        for data in date:
            assert modelli.data_in_testo(data) == data.isoformat()
