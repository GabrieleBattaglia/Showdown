"""
Test dei modelli di torneo della tappa 12, modelli_torneo.py, punto 3.5 del progetto: i campi
controllati uno per uno, la ricorrenza ai bordi di mese e d'anno, la durata prevista che conta il
girone da 5, i predefiniti in una cartella vuota, il file rovinato in problemi(), i nomi rifiutati,
l'identificativo che resta alla rinomina e cambia al duplicato, il ripristino che mette da parte i
file di prima, e a_dizionario che non condivide niente col modello.
Dal 2026-10-24, col collaudo di gioco, il ripristino fermo a metà, che porta nell'errore la cartella dei file già messi da parte, o non ne lascia una vuota.
"""

import dataclasses
import datetime
import json
import types

import pytest
from aiuti_motore import giocatore

import formule
import modelli_torneo as mt
from modelli_torneo import GestoreModelli, ModelloTorneo


@pytest.fixture(autouse=True)
def cache_pulite():
    formule.azzera_cache()
    mt._CACHE.clear()
    yield
    formule.azzera_cache()
    mt._CACHE.clear()


@pytest.fixture
def gestore(cartella_di_prova):
    gestore = GestoreModelli()
    assert gestore.crea_predefiniti()
    return gestore


def _modello(**campi):
    return ModelloTorneo(id="modello_99", nome="Torneo di prova", **campi)


def test_i_predefiniti_si_copiano_in_una_cartella_vuota(gestore, cartella_di_prova):
    validi, scartati = gestore.modelli()
    assert len(validi) == 10 and scartati == []
    assert gestore.problemi() == []
    assert (cartella_di_prova / mt.CARTELLA / "Open maschile del sabato.json").exists()
    assert not gestore.crea_predefiniti()
    nomi = {m.nome: m for m in validi}
    assert nomi["Campionato italiano maschile"].qualificazione == mt.PUNTI_ANNO
    assert nomi["Coppa delle polisportive"].tipo == mt.SQUADRE and nomi["Coppa delle polisportive"].sesso is None
    assert sorted(m.id for m in validi) == sorted(f"modello_{n}" for n in range(1, 11))


def test_i_predefiniti_seguono_il_progetto(gestore):
    nomi = {m.nome: m for m in gestore.modelli()[0]}
    sabato = nomi["Open maschile del sabato"]
    assert (sabato.sesso, sabato.ricorrenza, sabato.giorni_iscrizione, sabato.formula, sabato.incontri_al_giorno) == ("m", {"tipo": "settimanale", "giorno": 5}, 14, "gironi_32", 4)
    assert (sabato.set_al_meglio, sabato.set_finali, sabato.finali_da, sabato.quota_iscrizione, sabato.contributo_federazione, sabato.posti_premiati) == (3, 5, 2, 10, 1.0, 8)
    mondiale = nomi["Campionato italiano femminile"]
    assert (mondiale.ricorrenza, mondiale.minimo_iscritti, mondiale.finali_da, mondiale.importanza, mondiale.montepremi_minimo) == ({"tipo": "annuale", "mese": 12, "giorno": 12}, 8, 8, 4.0, 3000)
    assert nomi["Open misto del mese"].sesso == "aperto"


def test_un_file_rovinato_e_scartato_e_detto_in_problemi(gestore, cartella_di_prova):
    (cartella_di_prova / mt.CARTELLA / "Rovinato.json").write_text("{ non è json", encoding="utf-8")
    dati = gestore.modello("modello_1").a_dizionario() | {"id": "modello_50", "nome": "Con un campo in più", "pareggio": 1}
    (cartella_di_prova / mt.CARTELLA / "Con un campo in più.json").write_text(json.dumps(dati), encoding="utf-8")
    gestore.azzera_cache()
    validi, scartati = gestore.modelli()
    assert len(validi) == 10
    motivi = dict(scartati)
    assert "Rovinato.json" in motivi and "campi sconosciuti: pareggio" in motivi["Con un campo in più.json"]
    problemi = gestore.problemi()
    assert len(problemi) == 2 and any("Rovinato.json" in p for p in problemi)
    # L'identificativo nuovo viene dopo il più alto, anche di un file scartato ma leggibile.
    assert mt._numero_dell_id(gestore.nuovo_id()) > 50


def test_una_formula_che_manca_e_detta_in_problemi(gestore):
    modello = gestore.modello("modello_3")
    valide = [f for f in formule.leggi()[0] if f["id"] != modello.formula]
    assert "non c'è" in mt.problema(modello, valide)
    formule.scrivi(valide)
    assert any("non può aprire edizioni" in p for p in gestore.problemi())
    with pytest.raises(ValueError, match="usata da"):
        formule.elimina("gironi_64", gestore.modelli()[0])


@pytest.mark.parametrize(("campo", "valore", "parole"), [
    ("nome", "ab", "da 3 a 60"), ("nome", " Spazio", "senza spazi"), ("attivo", 1, "sì o no"), ("tipo", "doppio", "individuale o squadre"),
    ("sesso", "x", "maschile, femminile o aperto"), ("formula", "", "identificativo"), ("ricorrenza", {"tipo": "quindicinale"}, "settimanale, mensile"),
    ("ricorrenza", {"tipo": "settimanale", "giorno": 7}, "da 0, lunedì"), ("ricorrenza", {"tipo": "mensile", "giorno": 31}, "da 1 a 28"),
    ("ricorrenza", {"tipo": "annuale", "mese": 13, "giorno": 1}, "da 1 a 12"), ("ricorrenza", {"tipo": "mensile", "giorno": 3, "mese": 1}, "ha i campi"),
    ("giorni_iscrizione", 0, "giorni d'iscrizione"), ("giorni_iscrizione", 61, "giorni d'iscrizione"), ("minimo_iscritti", 3, "minimo d'iscritti"),
    ("set_al_meglio", 4, "al meglio dei 3 o dei 5"), ("finali_da", 16, "fasi finali"), ("incontri_al_giorno", 5, "turni al giorno"),
    ("importanza", 1.1, "a passi di 0,25"), ("importanza", 5.25, "da 0,5 a 5"), ("quota_iscrizione", 1001, "quota d'iscrizione"),
    ("contributo_federazione", -1, "contributo"), ("montepremi_minimo", 5001, "montepremi minimo"), ("posti_premiati", 0, "posti premiati"),
    ("pendenza_premi", 0.9, "pendenza"), ("qualificazione", "gloria", "soltanto per i tornei a squadre"), ("qualificazione", "sorteggio", "qualificazione"),
    ("classe_minima", "Z9", "codice"), ("eta_minima", 8, "età"), ("quota_iscrizione", 10.5, "quota d'iscrizione"),
])
def test_ogni_campo_e_controllato(campo, valore, parole):
    dati = _modello().a_dizionario() | {campo: valore}
    with pytest.raises(ValueError, match=parole):
        ModelloTorneo.da_dizionario(dati)


def test_campi_che_si_controllano_insieme():
    base = _modello().a_dizionario()
    with pytest.raises(ValueError, match="campi sconosciuti: invitati"):
        ModelloTorneo.da_dizionario(base | {"invitati": []})
    senza = dict(base)
    del senza["note"]
    with pytest.raises(ValueError, match="mancano dei campi: note"):
        ModelloTorneo.da_dizionario(senza)
    with pytest.raises(ValueError, match="non ha sesso"):
        ModelloTorneo.da_dizionario(base | {"tipo": "squadre", "qualificazione": "gloria"})
    with pytest.raises(ValueError, match="per gloria"):
        ModelloTorneo.da_dizionario(base | {"tipo": "squadre", "sesso": None})
    with pytest.raises(ValueError, match="più alta della minima"):
        ModelloTorneo.da_dizionario(base | {"classe_minima": "C0", "classe_massima": "E0"})
    with pytest.raises(ValueError, match="non può superare"):
        ModelloTorneo.da_dizionario(base | {"eta_minima": 40, "eta_massima": 30})
    with pytest.raises(ValueError, match="soltanto per i tornei individuali"):
        ModelloTorneo.da_dizionario(base | {"tipo": "squadre", "sesso": None, "qualificazione": "gloria", "eta_massima": 30})
    assert ModelloTorneo.da_dizionario(base | {"importanza": 2, "classe_minima": "E0", "classe_massima": "C0"}).importanza == 2.0


def test_a_dizionario_non_condivide_niente_col_modello():
    modello = _modello()
    dati = modello.a_dizionario()
    dati["ricorrenza"]["giorno"] = 2
    assert modello.ricorrenza["giorno"] == 5
    copia = ModelloTorneo.da_dizionario(modello.a_dizionario())
    copia.ricorrenza["giorno"] = 0
    assert modello.ricorrenza["giorno"] == 5 and copia == dataclasses.replace(modello, ricorrenza={"tipo": "settimanale", "giorno": 0})


def test_la_ricorrenza_settimanale():
    sabato = _modello(ricorrenza={"tipo": "settimanale", "giorno": 5})
    assert mt.prossima_data(sabato, datetime.date(2026, 10, 13)) == datetime.date(2026, 10, 17)
    assert mt.prossima_data(sabato, datetime.date(2026, 10, 17)) == datetime.date(2026, 10, 17)
    assert mt.prossima_data(sabato, datetime.datetime(2026, 12, 27, 9, 0)) == datetime.date(2027, 1, 2)


def test_la_ricorrenza_mensile_ai_bordi_del_mese_e_dell_anno():
    mensile = _modello(ricorrenza={"tipo": "mensile", "giorno": 28})
    assert mt.prossima_data(mensile, datetime.date(2027, 2, 28)) == datetime.date(2027, 2, 28)
    assert mt.prossima_data(mensile, datetime.date(2027, 3, 1)) == datetime.date(2027, 3, 28)
    assert mt.prossima_data(mensile, datetime.date(2026, 12, 29)) == datetime.date(2027, 1, 28)


def test_la_ricorrenza_annuale_ai_bordi_dell_anno():
    mondiale = _modello(ricorrenza={"tipo": "annuale", "mese": 12, "giorno": 10})
    assert mt.prossima_data(mondiale, datetime.date(2026, 12, 10)) == datetime.date(2026, 12, 10)
    assert mt.prossima_data(mondiale, datetime.date(2026, 12, 11)) == datetime.date(2027, 12, 10)
    assert mt.prossima_data(mondiale, datetime.date(2027, 1, 1)) == datetime.date(2027, 12, 10)


def test_la_durata_prevista_conta_il_girone_da_5(gestore):
    nomi = {m.nome: m for m in gestore.modelli()[0]}
    gironi_32 = formule.formula("gironi_32")
    assert mt.durata_prevista(nomi["Open maschile del sabato"], gironi_32) == 3
    assert mt.durata_prevista(dataclasses.replace(nomi["Open maschile del sabato"], minimo_iscritti=32), gironi_32) == 2
    # Il mondiale con i suoi 32 qualificati dura tre giorni, risposta 10 di Gabriele; al massimo
    # quattro, se è a metà, con un girone da 5 e il tabellone da 16.
    mondiale = nomi["Campionato italiano maschile"]
    assert mt.giorni_di_gioco(formule.struttura(gironi_32, 32), mondiale.incontri_al_giorno) == 3
    assert mt.durata_prevista(mondiale, gironi_32) == 4
    assert mt.durata_prevista(nomi["Gran Premio femminile"], formule.formula("gironi_64")) == 4
    assert mt.durata_prevista(nomi["Coppa delle polisportive"], formule.formula("squadre_64")) == 4


def test_il_tetto_e_il_problema_dei_posti(gestore):
    sabato = next(m for m in gestore.modelli()[0] if m.nome == "Open maschile del sabato")
    assert mt.tetto(sabato) == 32
    assert "supera il tetto" in mt.problema(dataclasses.replace(sabato, minimo_iscritti=40))
    assert "superano il tetto" in mt.problema(dataclasses.replace(sabato, posti_premiati=33))
    assert mt.problema(sabato) is None


def test_chi_e_idoneo():
    maschile = _modello(sesso="m")
    uomo, donna = giocatore(1, sesso="m", anni=30), giocatore(2, sesso="f", anni=30)
    assert mt.idoneo(maschile, uomo) and not mt.idoneo(maschile, donna)
    assert mt.idoneo(_modello(sesso="aperto"), donna)
    assert not mt.idoneo(_modello(sesso="aperto", eta_massima=25), uomo)
    assert mt.idoneo(_modello(sesso="aperto", eta_minima=30, eta_massima=30), uomo)
    assert not mt.idoneo(_modello(sesso="aperto", classe_massima="K0"), uomo)
    assert not mt.idoneo(dataclasses.replace(_modello(), tipo="squadre", sesso=None), uomo)


def test_i_nomi_rifiutati(gestore):
    assert "Esiste già" in gestore.problema_nome("open maschile del sabato")
    assert gestore.problema_nome("Open maschile del sabato", escluso="modello_2") is None
    assert "riserva" in gestore.problema_nome("CON")
    assert "riserva" in gestore.problema_nome("com3.mio torneo")
    assert "riserva" in gestore.problema_nome("Lpt1")
    assert gestore.problema_nome("Console del sabato") is None
    assert "punto" in gestore.problema_nome("Torneo finale.")
    assert mt.nome_file('Open: "il ritorno"') == "Open_ _il ritorno_.json"
    modello = gestore.modello("modello_1")
    modello.nome = "Open: il ritorno"
    gestore.salva(modello)
    assert "stesso file" in gestore.problema_nome("Open/ il ritorno")


def test_l_identificativo_resta_alla_rinomina_e_cambia_al_duplicato(gestore, cartella_di_prova):
    modello = gestore.modello("modello_2")
    modello.nome = "Open del sabato sera"
    gestore.salva(modello)
    assert gestore.modello("modello_2").nome == "Open del sabato sera"
    cartella = cartella_di_prova / mt.CARTELLA
    assert not (cartella / "Open maschile del sabato.json").exists() and (cartella / "Open del sabato sera.json").exists()
    copia = gestore.duplica("modello_2")
    assert mt._numero_dell_id(copia.id) > 10 and copia.nome == "Copia di Open del sabato sera"
    seconda = gestore.duplica("modello_2")
    assert mt._numero_dell_id(seconda.id) > mt._numero_dell_id(copia.id) and seconda.nome == "Copia di Open del sabato sera 2"
    gestore.elimina(copia.id)
    assert gestore.modello(copia.id) is None and len(gestore.modelli()[0]) == 11
    with pytest.raises(ValueError, match="Esiste già"):
        gestore.salva(dataclasses.replace(seconda, nome="Gran Premio maschile"))
    with pytest.raises(ValueError, match="non c'è"):
        gestore.elimina("modello_99")


def test_due_gestori_della_stessa_cartella_vedono_le_stesse_scritture(gestore):
    altro = GestoreModelli()
    assert len(altro.modelli()[0]) == 10
    gestore.duplica("modello_1")
    assert len(altro.modelli()[0]) == 11


def test_il_ripristino_mette_da_parte_i_file_di_prima(gestore, cartella_di_prova):
    formule.leggi()
    gestore.elimina("modello_1")
    modello = gestore.modello("modello_2")
    modello.nome = "Il mio open"
    gestore.salva(modello)
    da_parte = gestore.ripristina_predefiniti()
    assert len(gestore.modelli()[0]) == 10 and gestore.modello("modello_2").nome == "Open maschile del sabato"
    salvati = sorted(p.name for p in (cartella_di_prova / mt.CARTELLA).glob(f"{mt.PREFISSO_RIPRISTINO}*/*"))
    assert "Il mio open.json" in salvati and formule.NOME_FILE in salvati and len(salvati) == 10
    assert (cartella_di_prova / formule.NOME_FILE).exists()
    assert gestore.ripristina_predefiniti() != da_parte


def test_il_ripristino_fermo_a_meta_dice_dove_sono_i_file(gestore, cartella_di_prova, monkeypatch):
    # Dal collaudo di gioco: se i predefiniti non si copiano dopo che i file di prima sono già da parte, l'errore porta la
    # cartella dove sono, perché il messaggio la nomini, e i modelli si rileggono dai file.
    formule.leggi()
    assert len(gestore.modelli()[0]) == 10

    def non_si_copia(_cartella):
        raise PermissionError(13, "Accesso negato")

    monkeypatch.setattr(mt, "_copia_predefiniti", non_si_copia)
    with pytest.raises(PermissionError) as errore:
        gestore.ripristina_predefiniti()
    da_parte = errore.value.da_parte
    assert da_parte.startswith(str(cartella_di_prova / mt.CARTELLA / mt.PREFISSO_RIPRISTINO))
    salvati = sorted(p.name for p in (cartella_di_prova / mt.CARTELLA).glob(f"{mt.PREFISSO_RIPRISTINO}*/*"))
    # I dieci modelli e il file delle formule.
    assert len(salvati) == 11 and formule.NOME_FILE in salvati
    assert gestore.modelli()[0] == []


def test_il_ripristino_fermo_al_primo_file_non_lascia_cartelle(gestore, cartella_di_prova, monkeypatch):
    # Se non si sposta nemmeno il primo file, la cartella vuota se ne va, e l'errore non nomina niente.
    def non_si_sposta(*_argomenti):
        raise PermissionError(13, "Accesso negato")

    monkeypatch.setattr(mt.shutil, "move", non_si_sposta)
    with pytest.raises(PermissionError) as errore:
        gestore.ripristina_predefiniti()
    assert not hasattr(errore.value, "da_parte")
    assert not list((cartella_di_prova / mt.CARTELLA).glob(f"{mt.PREFISSO_RIPRISTINO}*"))
    assert len(gestore.modelli()[0]) == 10


def test_l_identificativo_di_un_modello_non_torna_mai(gestore, monkeypatch):
    # La revisione del 14 ottobre 2026: con l'orologio fermo, un modello eliminato, l'ultimo nato, o un
    # ripristino del calendario predefinito non restituiscono il suo identificativo a un modello nuovo,
    # che erediterebbe la sua storia nel calendario del mondo.
    monkeypatch.setattr(mt, "adesso", lambda: datetime.datetime(2027, 6, 18, 9, 30, 12))
    copia = gestore.duplica("modello_1")
    assert copia.id == "modello_20270618093012"
    gestore.elimina(copia.id)
    dopo = gestore.nuovo_id()
    assert dopo != copia.id and mt._numero_dell_id(dopo) > mt._numero_dell_id(copia.id)
    altra = gestore.duplica("modello_1")
    gestore.ripristina_predefiniti()
    assert len(gestore.modelli()[0]) == 10 and mt._numero_dell_id(gestore.nuovo_id()) > mt._numero_dell_id(altra.id)


def test_un_modello_a_squadre_non_ha_premi_in_euro():
    # La revisione del 14 ottobre 2026: la coppa si gioca per le coppe, risposta 14, e la chiusura non paga premi.
    squadre = {"tipo": mt.SQUADRE, "sesso": None, "qualificazione": mt.GLORIA, "quota_iscrizione": 0, "contributo_federazione": 0.0, "montepremi_minimo": 0}
    assert mt.problema_dei_campi(_modello(**squadre).a_dizionario()) is None
    for campo, valore in (("montepremi_minimo", 2000), ("quota_iscrizione", 10), ("contributo_federazione", 1.0)):
        assert mt.problema_dei_campi(_modello(**(squadre | {campo: valore})).a_dizionario()).startswith("Un torneo a squadre non ha premi in euro")


def test_gli_oggetti_con_nome_e_formula_bastano_a_in_uso():
    assert formule.in_uso("x", [types.SimpleNamespace(nome="A", formula="x")]) == ["A"]
