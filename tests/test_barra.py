"""
Test della barra di stato su misura, decisione D38, senza wx: il catalogo dei dati, con chiavi e sigle uniche e ogni sigla
nel manuale; la barra salvata nelle impostazioni, con le sue regole; i testi dei dati su un mondo di prova, senza spazi e
coi due punti; i conti dei soldi, l'autonomia e la pazienza esatta; l'ora del giorno simulato che corre; l'istantanea, coi
dati del rinfresco che si ricalcolano sempre; le classifiche, la coppa e il calendario; la legenda della guida.
"""

import datetime
import random
import re
from pathlib import Path

import pytest
from aiuti_calendario import modello, polisportiva

import barra
import economia
import impostazioni
import testi
from modelli import Polisportiva, conti_vuoti
from mondo import Mondo
from utilita import adesso_utc

OGGI = datetime.datetime(2026, 10, 26, 9, 0)
MANUALE = Path(__file__).resolve().parent.parent / "manuale.html"


@pytest.fixture
def mondo():
    random.seed(23)
    m = Mondo()
    m.datetime_corrente_simulazione = OGGI
    m.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=3, minutes=27)
    m.crea_giocatori_casuali(40, OGGI)
    mia = Polisportiva("Club Di Prova", "segreta", OGGI - datetime.timedelta(days=150))
    m.polisportive[mia.nome] = mia
    for gid in (2, 5, 9, 12):
        m._entra(mia, m.giocatori[gid])
    m.miapolisportiva_attiva = mia
    polisportiva(m, "Computer Uno", ids=(20, 21, 22))
    return m


def _contesto(mondo, **altro):
    return barra.Contesto(mondo, adesso_utc(), **altro)


def _testi(mondo, **altro):
    calcolo = barra._Calcolo(_contesto(mondo, **altro))
    return {chiave: dato.testo(calcolo) for chiave, dato in barra.CATALOGO.items()}


# Il catalogo.

def test_il_catalogo_ha_chiavi_e_sigle_uniche():
    dati = barra._DATI
    assert len(dati) == len(barra.CATALOGO) == 93
    sigle = [d.sigla for d in dati if d.sigla]
    assert len(sigle) == len(set(sigle)) == 90
    assert all(re.fullmatch(r"[A-Z][a-z]{2}", s) for s in sigle), sigle
    assert [d.chiave for d in dati if not d.sigla] == ["giorno_della_settimana", "nome_polisportiva", "ultimo_evento"]
    assert list(barra.GRUPPI) == list(dict.fromkeys(d.gruppo for d in dati))
    assert {d.ritmo for d in dati} == {barra.RINFRESCO, barra.COMANDO}
    # Ogni esempio è un testo come quelli della barra: la sigla e i due punti davanti.
    assert all(d.esempio.startswith(f"{d.sigla}:") for d in dati if d.sigla)


def test_ogni_sigla_sta_nel_manuale():
    manuale = MANUALE.read_text(encoding="utf-8")
    mancano = [d.sigla for d in barra._DATI if d.sigla and not re.search(rf"\b{d.sigla}:", manuale)]
    assert not mancano, mancano


def test_la_barra_di_serie_usa_tutto_il_catalogo_una_volta():
    chiavi = [chiave for riga in barra.BARRA_DI_SERIE for chiave in riga]
    assert len(barra.BARRA_DI_SERIE) == 10 and sorted(chiavi) == sorted(barra.CATALOGO)
    # L'ultimo evento in fondo all'ultima riga, dove porta Ctrl+Fine; il salvataggio in testa alla prima.
    assert barra.BARRA_DI_SERIE[-1][-1] == "ultimo_evento" and barra.BARRA_DI_SERIE[0][0] == "stato_salvataggio"
    assert impostazioni.valide(None)["barra_di_stato"] == [list(riga) for riga in barra.BARRA_DI_SERIE]


# La barra nel file delle impostazioni.

def test_la_barra_si_pulisce_e_conserva_le_chiavi_sconosciute():
    valide = impostazioni.barra_valida
    assert valide([["gloria", "cassa"], [], ["gloria", "dato_di_domani", 7, ""], "riga"]) == [["gloria", "cassa"], ["dato_di_domani"]]
    assert valide([[], [3]]) == valide(None) == valide("barra") == [list(r) for r in barra.BARRA_DI_SERIE]
    lunga = [[f"dato_{n}"] for n in range(20)]
    assert valide(lunga) == lunga[:impostazioni.RIGHE_MASSIME] and impostazioni.RIGHE_MASSIME == 16
    # Nel file salvato restano anche le chiavi sconosciute, e si rileggono uguali.
    scelta = {"barra_di_stato": [["dato_di_domani", "gloria"], ["ultimo_evento"]]}
    assert impostazioni.salva(scelta)
    assert impostazioni.carica()["barra_di_stato"] == [["dato_di_domani", "gloria"], ["ultimo_evento"]]


def test_le_chiavi_sconosciute_non_si_vedono(mondo):
    righe = barra.righe([["dato_di_domani", "gloria"], ["dato_di_domani_2"], ["ultimo_evento"]], _contesto(mondo, ultimo_evento="pronto"), {})
    assert righe == ["Glo:100", "pronto"]


# I testi dei dati.

def test_ogni_dato_ha_un_testo_senza_spazi_coi_due_punti(mondo):
    testi_dei_dati = _testi(mondo, ultimo_evento="mondo pronto", rapporto={"notizie": ["una", "due"]}, durata=datetime.timedelta(minutes=72), comandi=35)
    a_parole = {"giorno_della_settimana", "nome_polisportiva", "ultimo_evento"}
    for chiave, testo in testi_dei_dati.items():
        dato = barra.CATALOGO[chiave]
        if chiave == "stato_salvataggio":
            assert testo is None
            continue
        assert testo, chiave
        if chiave not in a_parole:
            assert " " not in testo and testo.startswith(f"{dato.sigla}:"), (chiave, testo)
    assert testi_dei_dati["giorno_della_settimana"] == "lunedì" and testi_dei_dati["nome_polisportiva"] == "Club Di Prova"
    assert testi_dei_dati["data_simulata"] == "Dat:26/10/2026" and testi_dei_dati["giorni_al_primo_del_mese"] == "Pri:6g"
    assert testi_dei_dati["tesserati"] == "Tes:4/15" and testi_dei_dati["posto_per_gloria"].startswith("Pos:") and testi_dei_dati["polisportive_tue"] == "Tue:1"
    assert testi_dei_dati["notizie_ultimo_avanzamento"] == "Not:2" and testi_dei_dati["durata_sessione"] == "Dur:1h12m"
    assert testi_dei_dati["comandi_della_sessione"] == "Cmd:35" and testi_dei_dati["ultimo_evento"] == "mondo pronto"
    assert testi_dei_dati["uomini_donne"] == f"Ses:{sum(1 for g in mondo._rosa(mondo.miapolisportiva_attiva) if g.sesso == 'm')}u" \
        f"{sum(1 for g in mondo._rosa(mondo.miapolisportiva_attiva) if g.sesso == 'f')}d"
    assert testi_dei_dati["popolazione"] == f"Pop:{len(mondo.giocatori)}"


def test_senza_polisportiva_attiva_i_suoi_dati_spariscono(mondo):
    mondo.miapolisportiva_attiva = None
    testi_dei_dati = _testi(mondo)
    assert testi_dei_dati["nome_polisportiva"] == "nessuna polisportiva attiva"
    della_attiva = [d.chiave for d in barra._DATI if d.ambito == barra.DELL_ATTIVA and d.chiave != "nome_polisportiva"]
    assert della_attiva and all(testi_dei_dati[chiave] is None for chiave in della_attiva)
    # Gli altri ci sono: le tue polisportive, il mondo, il tempo.
    assert testi_dei_dati["capitale"] == "Tca:20.000" and testi_dei_dati["data_simulata"] == "Dat:26/10/2026"


def test_il_salvataggio_compare_soltanto_quando_non_va(mondo):
    assert _testi(mondo)["stato_salvataggio"] is None
    assert _testi(mondo, salvataggio_riuscito=False)["stato_salvataggio"] == "Slv:fallito"
    mondo.salvataggio_bloccato = True
    assert _testi(mondo)["stato_salvataggio"] == "Slv:bloccato"
    # Senza testo il dato non lascia spazi in testa alla riga.
    mondo.salvataggio_bloccato = False
    assert barra.righe([["stato_salvataggio", "data_simulata"]], _contesto(mondo), {}) == ["Dat:26/10/2026"]


# I soldi.

def test_margine_saldo_e_autonomia(mondo, monkeypatch):
    p = mondo.miapolisportiva_attiva
    monkeypatch.setattr(Mondo, "sponsor", lambda self, poli: 2730)
    monkeypatch.setattr(Mondo, "monte_stipendi", lambda self, poli: 2910)
    monkeypatch.setattr(Mondo, "monte_dello_staff", lambda self, poli: 20)
    p.cassa = 6640
    t = _testi(mondo)
    # Gli esempi del catalogo del 24 ottobre: i conti tornano.
    assert (t["cassa"], t["margine_al_primo"], t["saldo_mensile"], t["autonomia"]) == ("Cas:6.640", "Mrg:6.460", "Sal:-180", "Aut:36")
    assert (t["sponsor"], t["stipendi_tesserati"], t["stipendi_staff"], t["pazienza_minima"]) == ("Spo:2.730", "Sti:2.890", "Sst:20", "Paz:no")
    p.cassa = 100
    assert _testi(mondo)["autonomia"] == "Aut:0" and _testi(mondo)["margine_al_primo"] == "Mrg:-80"
    monkeypatch.setattr(Mondo, "sponsor", lambda self, poli: 3000)
    assert _testi(mondo)["autonomia"] == "Aut:sempre"


def test_la_pazienza_esatta_coi_conti_del_mondo(mondo, monkeypatch):
    p = mondo.miapolisportiva_attiva
    rosa = mondo._rosa(p)
    for g in rosa:
        g.arretrati = 100
        g.pazienza = 100.0
    rosa[0].pazienza = 50.0
    t = _testi(mondo)
    # Lo stesso conto del primo del mese, mese per mese: chi ha la pazienza più bassa se ne va per primo.
    passo = 100 / economia.mesi_di_pazienza(rosa[0])
    mesi, pazienza = 0, 50.0
    while pazienza > 0:
        pazienza = max(0., pazienza - passo)
        mesi += 1
    altri = [barra._primi_senza_stipendio(g) for g in rosa[1:]]
    assert t["pazienza_minima"] == f"Paz:{min([mesi, *altri])}" and t["arretrati"] == f"Arr:{100 * len(rosa)}"
    # Le bandiere non contano.
    monkeypatch.setattr(economia, "bandiera_attiva", lambda g: True)
    assert _testi(mondo)["pazienza_minima"] == "Paz:no"


def test_flusso_e_bilancio_coi_segni(mondo):
    p = mondo.miapolisportiva_attiva
    p.conti_del_mese = conti_vuoti()
    p.conti_del_mese.update({"vendite": 500, "premi": 38, "rimborsi": 10, "acquisti": 1200, "iscrizioni": 40})
    p.bilanci = [{"data": OGGI, "cassa": 900, "sponsor": 2730, "stipendi": 2910, "staff": 20, "vendite": 0, "arretrati": 0, "ingaggi": 0,
                  "acquisti": 0, "buonuscite": 0, "iscrizioni": 0, "premi": 0, "rimborsi": 0}]
    t = _testi(mondo)
    assert t["movimenti_del_mese"] == "Flu:-692" and t["quote_del_mese"] == "Quo:30" and t["premi_del_mese"] == "Vin:38"
    assert t["bilancio_ultimo_mese"] == "Bil:-200"
    p.bilanci = []
    assert _testi(mondo)["bilancio_ultimo_mese"] == "Bil:no"


# Il tempo.

def test_l_ora_del_giorno_simulato_corre_e_si_ferma_alle_23_59(mondo):
    ultimo = mondo.datetime_ultimo_run_reale
    assert mondo.ora_del_giorno(ultimo) == (0, 0)
    # Tre minuti simulati per minuto vero: uno ogni 20 secondi.
    assert mondo.ora_del_giorno(ultimo + datetime.timedelta(seconds=19)) == (0, 0)
    assert mondo.ora_del_giorno(ultimo + datetime.timedelta(seconds=20)) == (0, 1)
    assert mondo.ora_del_giorno(ultimo + datetime.timedelta(hours=3, minutes=27)) == (10, 21)
    assert mondo.ora_del_giorno(ultimo + datetime.timedelta(hours=9)) == (23, 59)
    contesto = barra.Contesto(mondo, ultimo + datetime.timedelta(hours=3, minutes=27))
    calcolo = barra._Calcolo(contesto)
    assert barra.CATALOGO["ora_simulata"].testo(calcolo) == "Ora:10:21" and barra.CATALOGO["prossimo_avanzamento_fra"].testo(calcolo) == "Fra:4h33m"


def test_la_data_del_comando_ha_l_ora_che_corre(mondo):
    ora = mondo.datetime_ultimo_run_reale + datetime.timedelta(hours=3, minutes=27)
    assert testi.data_e_avanzamento(mondo, ora).splitlines()[0] == "Data simulata: 26 ottobre 2026 alle 10:21."


# L'istantanea.

def test_l_istantanea_tiene_i_dati_del_comando_e_rifà_quelli_del_rinfresco(mondo):
    istantanea = {}
    scelta = [["gloria", "ultimo_evento", "comandi_della_sessione"]]
    assert barra.righe(scelta, _contesto(mondo, ultimo_evento="primo", comandi=1), istantanea) == ["Glo:100 primo Cmd:1"]
    assert set(istantanea) == {"gloria", "comandi_della_sessione"}
    mondo.miapolisportiva_attiva.gloria = 150
    # Fino al prossimo comando la gloria e i comandi restano quelli dell'istantanea; l'ultimo evento no.
    assert barra.righe(scelta, _contesto(mondo, ultimo_evento="secondo", comandi=2), istantanea) == ["Glo:100 secondo Cmd:1"]
    istantanea.clear()
    assert barra.righe(scelta, _contesto(mondo, ultimo_evento="secondo", comandi=2), istantanea) == ["Glo:150 secondo Cmd:2"]
    # Una riga che adesso non ha niente da dire non si scrive.
    assert barra.righe([["stato_salvataggio"], ["gloria"]], _contesto(mondo), {}) == ["Glo:150"]


# Le gare e le classifiche.

def test_le_classifiche_dell_anno_e_la_coppa(mondo):
    campionato = modello("Campionato italiano maschile")
    t = _testi(mondo)
    posti = t["classifica_anno_uomini"]
    tuoi = [g for g in mondo._rosa(mondo.miapolisportiva_attiva) if g.sesso == "m"]
    if tuoi:
        assert re.fullmatch(r"Anm:\d+/\d+", posti) and posti.endswith(f"/{barra.modelli_torneo.tetto(campionato)}")
    else:
        assert posti == "Anm:no"
    assert re.fullmatch(r"Cdp:\d+/\d+", t["coppa_delle_polisportive"]), t["coppa_delle_polisportive"]
    assert re.fullmatch(r"Nap:\d\d/\d\d", t["prossima_apertura"]), t["prossima_apertura"]
    # Nessuno dei tuoi ha punti nella classifica nazionale: no.
    assert t["classifica_uomini"] == "Clm:no" and t["classifica_donne"] == "Clf:no"


def test_il_posto_dell_anno_e_quello_della_classifica_ordinata(mondo):
    # Il conto della barra, col punteggio di classe soltanto a pari punti, dà il posto della classifica intera che convoca.
    oggi = OGGI.date()
    for numero, g in enumerate(mondo.giocatori.values()):
        # Punti dell'anno con molti pareggi, anche a zero, perché decidano il punteggio e poi il numero.
        g.punti_recenti = [[oggi.toordinal() - 3, float(numero % 4)]] if numero % 4 else []
    for sesso, chiave in (("m", "classifica_anno_uomini"), ("f", "classifica_anno_donne")):
        campionato = modello("Campionato italiano maschile" if sesso == "m" else "Campionato italiano femminile")
        elenco = barra.iscrizioni.classifica_dell_anno(mondo, campionato, oggi)
        tuoi = [posto for posto, g in enumerate(elenco, start=1) if g.appartenenza == "Club Di Prova"]
        atteso = f"{barra.CATALOGO[chiave].sigla}:{tuoi[0]}/{barra.modelli_torneo.tetto(campionato)}" if tuoi else f"{barra.CATALOGO[chiave].sigla}:no"
        assert _testi(mondo)[chiave] == atteso


def test_la_classifica_nazionale_conta_chi_sta_davanti(mondo):
    mia = mondo._rosa(mondo.miapolisportiva_attiva)
    for punti, g in enumerate(mondo.giocatori.values()):
        g.punti_mondiali = float(punti)
    sesso = mia[0].sesso
    sigla = "classifica_uomini" if sesso == "m" else "classifica_donne"
    migliore = max((g for g in mia if g.sesso == sesso), key=lambda g: g.punti_mondiali)
    davanti = sum(1 for g in mondo.giocatori.values() if g.sesso == sesso and g.punti_mondiali > migliore.punti_mondiali)
    assert _testi(mondo)[sigla] == f"{barra.CATALOGO[sigla].sigla}:{davanti + 1}"
    elenco = barra.palmares.classifica_mondiale(mondo, sesso)
    assert [r["id"] for r in elenco].index(migliore.id) == davanti


def test_i_dati_di_tutte_le_tue_polisportive(mondo):
    seconda = polisportiva(mondo, "Seconda Mia", cpu=False, ids=(30, 31))
    assert seconda.nome in barra._Calcolo(_contesto(mondo)).nomi_delle_tue
    assert _testi(mondo)["polisportive_tue"] == "Tue:2" and _testi(mondo)["atleti_in_tutto"] == "Atl:6"


# La legenda e la finestra.

def test_la_legenda_dice_le_righe_scelte():
    legenda = barra.legenda([["gloria", "dato_di_domani"], [], ["ultimo_evento"]])
    assert legenda.startswith("La barra di stato ha 3 righe, che scegli con la voce Barra di stato del menu Impostazioni.")
    assert "Riga 1: Glo, gloria. Riga 2: nessun dato. Riga 3: ultimo evento." in legenda
    assert testi.guida([], legenda).endswith(legenda)


def test_spiegazione_e_anteprima(mondo):
    contesto = _contesto(mondo)
    assert barra.spiegazione("gloria", contesto) == ("La polisportiva attiva: Glo, gloria. La gloria della polisportiva attiva. Esempio: Glo:138. "
                                                      "Adesso: Glo:100.")
    assert barra.spiegazione("stato_salvataggio", contesto).endswith("Adesso non si vede.")
    assert barra.anteprima(["gloria", "cassa"], contesto) == "Glo:100 Cas:20.000"
    assert barra.anteprima([], contesto) == "La riga è vuota, e non si salverà."
    assert barra.anteprima(["stato_salvataggio"], contesto) == "Adesso questa riga non mostra niente."
