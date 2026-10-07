"""
Test della cronaca: una frase per ogni tipo d'evento al livello tecnico, nessun separatore grafico e
nessuna riga vuota, le chiamate FISPIC, l'annuncio dal punto di vista di chi batte, il file nella
cartella delle cronache con il suffisso per i nomi doppi, e i testi un punto alla volta.
"""

import datetime
import json
import re

import pytest
from aiuti_motore import giocatore

import testi
from costanti import CARTELLA_CRONACHE
from motore import cronaca as C
from motore import eventi as E
from motore.eventi import Evento, Tappa
from motore.incontro import COMPLETO, SINGOLARE_3, SQUADRE, StatoIncontro, simula_incontro
from motore.squadre import Squadra

SEPARATORI = re.compile(r"[=_*#~-]{3,}")


@pytest.fixture(scope="module")
def partita():
    a = giocatore(1, valore=18.0, cognome="Rossi", nome="Mario")
    b = giocatore(2, valore=16.0, cognome="Bianchi", nome="Anna", sesso="f")
    risultato = simula_incontro(a, b, SINGOLARE_3, seme=12, dettaglio=COMPLETO)
    return risultato, C.nomi_dei_giocatori([a, b])


_DATI = {
    E.INIZIO_INCONTRO: {"formato": "singolare al meglio dei 3 set"},
    E.SORTEGGIO: {"chiama": "A", "faccia_chiamata": "testa", "faccia_uscita": "croce", "vince": "B", "scelta": "lato", "batte": "A"},
    E.RISCALDAMENTO_INIZIO: {"durata": 60},
    E.AVVISO_TEMPO: {"restano": 15},
    E.INIZIO_SET: {"apre": 1},
    E.RECUPERO: {"da": "tasca"},
    E.CONSEGNA: {"a": 1},
    E.ANNUNCIO: {"numero_servizio": 2, "battitore": 2, "punteggio_visto": (3, 5)},
    E.FINE_SET: {"set": 1, "punteggio": [11, 8], "set_vinti": [1, 0], "ultimo": False},
    E.FINE_INCONTRO: {"set_vinti": [2, 1], "set": [[11, 8], [7, 11], [12, 10]]},
    E.CAMBIO_CAMPO_INIZIO: {"fra_set": True},
    E.CAMBIO_AL_TAVOLO: {"esce": 1, "entra": 3, "batte": 2},
    E.SOSTITUZIONE: {"esce": 1, "entra": 3},
    E.SOSTITUZIONE_ATTREZZO: {"attrezzo": "paletta", "di": 1},
    E.GOAL: {"zona": "dx", "battitore": 1, "ricevitore": 2},
    E.PENALITA: {"seconda_infrazione": True},
    E.VOLO: {"verso": 2},
}
_CAMPI = {
    E.FISCHIO: {"fischio": E.DOPPIO},
    E.CHIAMATA: {"chiamata": "schermo_centrale"},
    E.BATTUTA: {"colpo": "battutasx"},
    E.COLPO: {"colpo": "doppiaspondadx", "colpo_n": 2},
    E.RISCALDAMENTO_COLPO: {"colpo": "bomba"},
    E.PARATA: {"esito": "fermata", "dritto": False, "lato": "sinistra"},
    E.CAMBIO_MANO: {"mano": "sinistra"},
    E.CONTROLLO: {"esito": "riuscito"},
    E.GOAL: {"causa": "goal_scambio", "colpo": "bomba"},
    E.FALLO: {"causa": "schermo_contro", "chiamata": "schermo_centrale"},
    E.PALLA_MORTA: {"causa": "colpo_debole"},
    E.ROTTURA: {"causa": "paletta_rotta"},
    E.PUNTO: {"punti": 1, "a_chi": "B"},
    E.AMMONIZIONE: {"causa": "raschiare_paletta"},
    E.PENALITA: {"causa": "muovere_tavolo", "a_chi": "B", "punti": 2},
}


def _evento(tipo):
    campi = {"chi": 1, "parte": "A", "pos": (30.0, 30.0), "lato": "sinistra", "distanza": 30.0, "punteggio": (4, 3), "set_n": 1, "punto_n": 3}
    campi.update(_CAMPI.get(tipo, {}))
    volo = (Tappa(1.0, 30, 30, 500, "partenza"), Tappa(1.5, 3, 200, 450, "sponda"), Tappa(2.0, 90, 340, 400, "paletta"))
    return Evento(n=7, t=1.0, tipo=tipo, fase=E.GIOCO, dati=_DATI.get(tipo), volo=volo if tipo == E.VOLO else None, **campi)


@pytest.mark.parametrize("tipo", E.TIPI)
def test_ogni_tipo_ha_la_sua_frase_tecnica(tipo):
    nomi = {1: C.Nome("Rossi", "m"), 2: C.Nome("Bianchi", "f"), 3: C.Nome("Verdi", "m"), "A": C.Nome("Rossi", "m"), "B": C.Nome("Bianchi", "f")}
    testo = C.frase(_evento(tipo), nomi, C.TECNICA)
    assert testo and testo[0].isupper() and testo.rstrip(")").endswith(tuple(".!0123456789"))
    assert not SEPARATORI.search(testo) and "\n" not in testo


def test_l_annuncio_e_dal_punto_di_vista_di_chi_batte():
    nomi = {1: C.Nome("Rossi", "m"), 2: C.Nome("Bianchi", "f")}
    assert C.frase(_evento(E.ANNUNCIO), nomi, C.NORMALE) == "Secondo servizio di Bianchi, 3 a 5."


def test_la_cronaca_della_partita(partita):
    risultato, nomi = partita
    for livello in C.LIVELLI:
        righe = C.componi(risultato.momenti, nomi, livello)
        assert righe[0].startswith("Inizio dell'incontro: Rossi contro Bianchi, al meglio dei 3 set.")
        assert righe[-1].startswith("Fine dell'incontro: vince ")
        for riga in righe:
            assert riga.strip(), "Una riga vuota nella cronaca."
            assert not SEPARATORI.search(riga), riga
    normale = "\n".join(C.componi(risultato.momenti, nomi, C.NORMALE))
    assert "Doppio fischio: goal di " in normale
    chiamate = ("schermo centrale", "servizio irregolare", "out", "body touch", "infrazione palla", "infrazione paletta", "difesa irregolare")
    assert any(f"Fischio: {chiamata}," in normale for chiamata in chiamate)
    sintetica = C.componi(risultato.momenti, nomi, C.SINTETICA)
    assert len(sintetica) < len(C.componi(risultato.momenti, nomi, C.NORMALE)) / 3
    assert sum(1 for riga in sintetica if riga.startswith("Battuta di ")) == risultato.incontro.punti_giocati


def test_riepilogo_e_riga_di_stato(partita):
    risultato, nomi = partita
    righe = C.riepilogo(risultato, nomi)
    assert len(righe) == 2 and righe[0].startswith("Rossi: ") and "scambio più lungo di " in righe[0]
    stato = StatoIncontro(2, (7, 5), (1, 0), 1, 2, False)
    riga = C.riga_di_stato(stato, nomi)
    assert riga.startswith("Set 2, 7 a 5, batte Rossi")
    assert len("Set 2, 7 a 5, batte Rossi") <= 40


def test_il_file_della_cronaca_e_il_suffisso(partita, cartella_di_prova):
    risultato, nomi = partita
    istante = datetime.datetime(2026, 10, 7, 15, 30, 12)
    nome = C.nome_file(nomi, istante)
    assert nome == "2026-10-07 15.30.12 Rossi contro Bianchi.txt"
    righe = C.intestazione(risultato, nomi, istante, datetime.datetime(2026, 3, 1)) + C.componi(risultato.momenti, nomi) + C.riepilogo(risultato, nomi)
    percorso = C.salva(righe, nome)
    assert percorso == str(cartella_di_prova / CARTELLA_CRONACHE / nome)
    testo = (cartella_di_prova / CARTELLA_CRONACHE / nome).read_text(encoding="utf-8")
    assert "Il seme della partita è 12" in testo and "\n\n" not in testo
    assert C.nome_file(nomi, istante) == "2026-10-07 15.30.12 Rossi contro Bianchi (2).txt"
    strani = {"A": C.Nome('Ro/ss:i*', "m"), "B": C.Nome("Bian?chi", "f")}
    assert C.nome_file(strani, istante) == "2026-10-07 15.30.12 Rossi contro Bianchi (2).txt"
    eventi = C.salva_eventi(risultato.eventi, str(cartella_di_prova / "eventi.json"))
    letti = json.loads((cartella_di_prova / "eventi.json").read_text(encoding="utf-8"))
    assert eventi.endswith("eventi.json") and len(letti) == len(risultato.eventi) and letti[0]["tipo"] == E.INIZIO_INCONTRO


def test_i_testi_un_punto_alla_volta(partita):
    risultato, nomi = partita
    pezzi = testi.testi_della_partita(risultato.momenti, nomi)
    assert pezzi[0].startswith("Inizio dell'incontro: Rossi contro Bianchi")
    assert pezzi[1].startswith("Set 1, Rossi 0, Bianchi 0.")
    assert len(pezzi) == risultato.incontro.punti_giocati + 2
    assert pezzi[-1].startswith("Fine dell'incontro: vince ") or "Fine dell'incontro: vince " in pezzi[-1]
    assert all("\n\n" not in pezzo for pezzo in pezzi)


def test_la_cronaca_delle_squadre():
    a = Squadra("Leoni", tuple(giocatore(i, sesso=s) for i, s in ((1, "m"), (2, "m"), (3, "f"))))
    b = Squadra("Tigri", tuple(giocatore(i, sesso=s) for i, s in ((11, "f"), (12, "f"), (13, "m"))))
    risultato = simula_incontro(a, b, SQUADRE, seme=4, dettaglio=COMPLETO)
    nomi = C.nomi_dei_giocatori([*a.giocatori, *b.giocatori], squadre=(a, b))
    righe = C.componi(risultato.momenti, nomi)
    assert righe[0] == "Inizio della gara a squadre: Leoni contro Tigri, un set a 31 punti."
    assert any(riga.startswith("Cambio al tavolo: esce ") for riga in righe)
    assert righe[-1].startswith("Fine dell'incontro: vince ")
