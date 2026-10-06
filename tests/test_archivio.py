"""
Test dell'archivio JSON firmato, tutti in una cartella temporanea: salvataggio e ricarica,
copia di sicurezza, firma che scopre le modifiche, ripiego sulla copia, quarantena e blocco dei
salvataggi, formato, identificativi che non si riusano, nascita del mondo nuovo.
"""

import datetime
import json
import os
import random

import pytest

import archivio
from costanti import FILE_MONDO, FILE_MONDO_COPIA
from modelli import Polisportiva
from mondo import Mondo

INIZIO = datetime.datetime(2026, 3, 1, 9, 30)


def _mondo_popolato():
    random.seed(99)
    m = Mondo()
    m.datetime_corrente_simulazione = INIZIO
    m.datetime_ultimo_run_reale = INIZIO
    m.crea_giocatori_casuali(12, INIZIO)
    m.crea_polisportiva_cpu(INIZIO)
    mia = Polisportiva("Club Di Prova", "segreta", INIZIO)
    m.polisportive[mia.nome] = mia
    mia.aggiungi_tesserato(3, m.giocatori[3].indice_collettivo_valore)
    m.giocatori[3].appartenenza = mia.nome
    m.miapolisportiva_attiva = mia
    return m


def _ricarica(messaggi=None):
    m = Mondo(notifica=messaggi.append if messaggi is not None else None)
    archivio.carica(m)
    return m


def test_salva_e_ricarica(cartella_di_prova):
    originale = _mondo_popolato()
    originale._ids_morti_processati_sessione.add(5)
    messaggi = []
    originale.notifica = messaggi.append
    assert archivio.salva(originale)
    assert messaggi == ["Mondo salvato: 11 giocatori e 2 polisportive. Il giocatore uscito di scena in questa sessione non ne fa più parte."]
    ricaricato = _ricarica()
    assert sorted(ricaricato.giocatori) == [g for g in range(1, 13) if g != 5]
    for gid, g in ricaricato.giocatori.items():
        assert vars(g) == vars(originale.giocatori[gid])
    for chiave, p in ricaricato.polisportive.items():
        assert vars(p) == vars(originale.polisportive[chiave])
    assert ricaricato.miapolisportiva_attiva is ricaricato.polisportive["Club Di Prova"]
    assert ricaricato.miapolisportiva_attiva.verifica_password("segreta")
    assert ricaricato.datetime_corrente_simulazione == INIZIO
    assert ricaricato.prossimo_id == 13
    assert set(os.listdir(cartella_di_prova)) == {FILE_MONDO}
    assert "segreta" not in (cartella_di_prova / FILE_MONDO).read_text(encoding="utf-8")


def test_il_salvataggio_precedente_diventa_la_copia(cartella_di_prova):
    m = _mondo_popolato()
    archivio.salva(m)
    primo = (cartella_di_prova / FILE_MONDO).read_text(encoding="utf-8")
    m.giocatori[1].puntiesperienza = 77
    archivio.salva(m)
    assert (cartella_di_prova / FILE_MONDO_COPIA).read_text(encoding="utf-8") == primo
    assert set(os.listdir(cartella_di_prova)) == {FILE_MONDO, FILE_MONDO_COPIA}


def _due_salvataggi(cartella):
    """Salva due volte, la seconda con 77 punti esperienza al giocatore 1; restituisce il percorso del salvataggio."""
    m = _mondo_popolato()
    archivio.salva(m)
    m.giocatori[1].puntiesperienza = 77
    archivio.salva(m)
    return cartella / FILE_MONDO


def test_la_firma_scopre_una_modifica_e_si_usa_la_copia(cartella_di_prova):
    percorso = _due_salvataggi(cartella_di_prova)
    testo = percorso.read_text(encoding="utf-8")
    manomesso = testo.replace('"puntiesperienza": 77', '"puntiesperienza": 9999')
    assert manomesso != testo
    percorso.write_text(manomesso, encoding="utf-8")
    messaggi = []
    ricaricato = _ricarica(messaggi)
    assert ricaricato.giocatori[1].puntiesperienza == 0
    assert "la firma non corrisponde" in messaggi[0]
    assert "ha preso il suo posto" in messaggi[0]
    assert messaggi[1].startswith("Mondo caricato dalla copia:")
    assert percorso.read_text(encoding="utf-8") == (cartella_di_prova / FILE_MONDO_COPIA).read_text(encoding="utf-8")
    messi_da_parte = list((cartella_di_prova / archivio.CARTELLA_QUARANTENA).iterdir())
    assert len(messi_da_parte) == 1
    assert (messi_da_parte[0] / FILE_MONDO).read_text(encoding="utf-8") == manomesso


def test_spazi_e_a_capo_non_contano(cartella_di_prova):
    percorso = _due_salvataggi(cartella_di_prova)
    documento = json.loads(percorso.read_text(encoding="utf-8"))
    percorso.write_text(json.dumps(documento, indent=4, ensure_ascii=False).replace("\n", "\r\n"), encoding="utf-8")
    messaggi = []
    ricaricato = _ricarica(messaggi)
    assert messaggi[0].startswith("Mondo caricato:")
    assert ricaricato.giocatori[1].puntiesperienza == 77


def test_se_manca_il_principale_si_usa_la_copia(cartella_di_prova):
    percorso = _due_salvataggi(cartella_di_prova)
    os.remove(percorso)
    messaggi = []
    ricaricato = _ricarica(messaggi)
    assert f"il file {FILE_MONDO} non c'è" in messaggi[0]
    assert ricaricato.giocatori[1].puntiesperienza == 0
    assert percorso.exists()
    assert not (cartella_di_prova / archivio.CARTELLA_QUARANTENA).exists()


def test_se_nessuno_si_legge_si_blocca_e_si_mettono_da_parte(cartella_di_prova):
    percorso = _due_salvataggi(cartella_di_prova)
    percorso.write_text("{ rotto", encoding="utf-8")
    (cartella_di_prova / FILE_MONDO_COPIA).write_text("[]", encoding="utf-8")
    m = Mondo()
    with pytest.raises(archivio.SalvataggioIllegibile) as informazioni:
        archivio.carica(m)
    assert "non è un JSON valido" in str(informazioni.value)
    assert "e la copia di sicurezza nemmeno" in str(informazioni.value)
    assert m.salvataggio_bloccato
    assert sorted(os.listdir(informazioni.value.cartella)) == sorted([FILE_MONDO, FILE_MONDO_COPIA])
    assert not archivio.salva(m)
    assert percorso.read_text(encoding="utf-8") == "{ rotto"


def test_formato_piu_recente_rifiutato(cartella_di_prova):
    contenuto = archivio.componi(_mondo_popolato())
    contenuto["formato"] = archivio.FORMATO + 1
    percorso = cartella_di_prova / FILE_MONDO
    percorso.write_text(json.dumps({**contenuto, "firma": archivio.firma(contenuto)}), encoding="utf-8")
    with pytest.raises(archivio.ErroreSalvataggio, match="più recente"):
        archivio.leggi(percorso)


def test_un_dato_non_valido_lascia_il_mondo_com_era():
    contenuto = archivio.componi(_mondo_popolato())
    contenuto["mondo"]["giocatori"][0]["sesso"] = "x"
    vuoto = Mondo()
    with pytest.raises(archivio.ErroreSalvataggio, match="sesso"):
        archivio.costruisci(contenuto, vuoto)
    assert vuoto.giocatori == {}
    contenuto["mondo"]["giocatori"][0]["sesso"] = "f"
    del contenuto["mondo"]["polisportiva_attiva"]
    with pytest.raises(archivio.ErroreSalvataggio, match="manca il dato"):
        archivio.costruisci(contenuto, vuoto)


def test_gli_identificativi_non_si_riusano(cartella_di_prova):
    m = _mondo_popolato()
    m._ids_morti_processati_sessione.update({11, 12})
    archivio.salva(m)
    ricaricato = _ricarica()
    assert max(ricaricato.giocatori) == 10
    ricaricato.crea_giocatori_casuali(2, INIZIO)
    assert sorted(ricaricato.giocatori)[-2:] == [13, 14]


def test_mondo_nuovo_se_non_ci_sono_salvataggi(cartella_di_prova):
    random.seed(1)
    messaggi = []
    m = _ricarica(messaggi)
    assert len(m.giocatori) == 50
    assert m.prossimo_id == 51
    assert m.nuovi_giocatori_sessione == []
    assert messaggi[0] == "Nessun salvataggio trovato: nasce un mondo nuovo, con 50 giocatori."
    assert m.datetime_ultimo_run_reale == m.datetime_corrente_simulazione - datetime.timedelta(hours=8)
    assert os.listdir(cartella_di_prova) == []
