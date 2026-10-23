"""
Test dei testi dei tornei, tappa 12, punto 12.12 del progetto; la voce TOR dell'interfaccia testuale se n'è andata con lei, nella tappa 14.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Il calendario, la sede in elenco, la classifica di un girone, gli incontri con i risultati dei tuoi
nascosti finché non si ascoltano, risposta 18, e Mostra tutti i risultati che li svela dopo la
conferma; l'albo d'oro dei singolari, della coppa e dell'edizione non disputata; il riepilogo
dell'avanzamento coi tornei, le sfide e le notizie, e la somma dei riepiloghi di una sessione.
"""

import datetime

import pytest
from aiuti_calendario import OGGI, apri, giorno, iscrivi_tutti, mondo_di_prova, polisportiva

import testi
from mondo import Mondo
from premiazioni import Albo

MARTEDI = OGGI + datetime.timedelta(days=1)


@pytest.fixture
def in_corso():
    """Un Open maschile del martedì da 12, con due tuoi tesserati, dopo la prima giornata."""
    mondo = mondo_di_prova(12, 0)
    polisportiva(mondo, "Club Di Prova", cpu=False, cassa=1000, ids=(1, 2))
    edizioni = apri(mondo, OGGI, "Open maschile del martedì")
    iscrivi_tutti(edizioni[0], mondo, range(1, 13))
    giorno(mondo, MARTEDI)
    return mondo


def test_il_calendario_e_la_sede_in_elenco(in_corso):
    mondo = in_corso
    ed = mondo.calendario.edizioni[0]
    assert testi.edizione_in_calendario(ed, 0).startswith("Open maschile del martedì, dal 13 ottobre 2026, edizione 2: 0 iscritti; quota ")
    torneo = mondo.calendario.tornei[0]
    testo = testi.torneo_in_elenco(torneo, 2)
    assert testo.startswith("Open maschile del martedì, sede 1, dal 6 ottobre 2026: ") and testo.endswith("; 2 tuoi atleti.")


def test_la_classifica_del_girone(in_corso):
    torneo = in_corso.calendario.tornei[0]
    fase = torneo.fasi[0]
    for lettera, ids in fase.gironi.items():
        righe = testi.classifica_del_girone(torneo, fase, lettera)
        assert len(righe) == len(ids) and righe[0].startswith("1. ") and ", set " in righe[0] and ", punti " in righe[0]


def test_i_risultati_dei_tuoi_restano_nascosti_finche_non_si_mostrano(in_corso):
    mondo = in_corso
    torneo = mondo.calendario.tornei[0]
    tuoi = mondo.calendario.da_svelare()
    assert tuoi and all(1 in (i.a, i.b) or 2 in (i.a, i.b) for i in tuoi)
    assert testi.incontro_in_elenco(torneo, tuoi[0]).endswith(", tuo, giocato, da ascoltare.")
    assert " a " in testi.incontro_in_elenco(torneo, tuoi[0], mostra=True).split(": ", 1)[1]
    altri = [i for i in torneo.incontri() if i.giocato and not i.differita]
    assert altri and "da ascoltare" not in testi.incontro_in_elenco(torneo, altri[0])
    assert mondo.calendario.svela_tutti() == len(tuoi) and not mondo.calendario.da_svelare()
    assert "da ascoltare" not in testi.incontro_in_elenco(torneo, tuoi[0])


def test_l_albo_d_oro_a_parole():
    albo = Albo()
    open_, mondiale, coppa_ = (albo.indice_del_modello(*m) for m in (("modello_1", "Open maschile del martedì"), ("modello_8", "Campionato italiano maschile"),
                                                                     ("modello_10", "Coppa delle polisportive")))
    albo.giocatori = {"7": ["Mario", "Rossi"], "9": ["Luca", "Bianchi"]}
    albo.club = [["PoliTeam04", "2020-01-01"], ["Club Di Prova", "2026-01-01"]]
    singolare = [open_, "individuale", "m", 1.0, "2026-10-06", 57, 3, 25, [[7, 0], [9, None]], [100, 60]]
    assert testi.voce_dell_albo(albo, singolare) == ("Open maschile del martedì, edizione 57, sede 3, 6 ottobre 2026, 25 iscritti: "
                                                     "oro Mario Rossi, PoliTeam04; argento Luca Bianchi.")
    coppa = [coppa_, "squadre", None, 3.0, "2027-06-15", 2, 1, 40, [1, 0], [0, 0]]
    assert testi.voce_dell_albo(albo, coppa) == "Coppa delle polisportive, edizione 2, sede 1, 15 giugno 2027, 40 polisportive: oro Club Di Prova; argento PoliTeam04."
    annullato = [mondiale, "individuale", "m", 4.0, "2026-12-10", 3, 0, 6, [], []]
    assert testi.voce_dell_albo(albo, annullato) == "Campionato italiano maschile, edizione 3, 10 dicembre 2026: edizione non disputata, con 6 iscritti."
    # La revisione del 14 ottobre 2026: un modello rinominato ha una voce nuova nella tabella, e le
    # edizioni di prima tengono il nome che avevano.
    rinominato = albo.indice_del_modello("modello_1", "Open del martedì sera")
    assert rinominato != open_ and albo.indice_del_modello("modello_1", "Open maschile del martedì") == open_
    assert testi.voce_dell_albo(albo, singolare).startswith("Open maschile del martedì, edizione 57")
    assert testi.voce_dell_albo(albo, [rinominato, *singolare[1:5], 58, *singolare[6:]]).startswith("Open del martedì sera, edizione 58")


def test_il_riepilogo_coi_tornei_le_sfide_e_le_notizie():
    primo = Mondo.rapporto_vuoto("ieri")
    primo.update(tornei_conclusi=2, incontri_torneo=40, sfide_giocate=3, sfide_in_attesa=2, notizie=["Mario Rossi vince la medaglia d'oro all'Open maschile del martedì."])
    testo = testi._fatti_avanzamento(primo)
    assert "Mario Rossi vince la medaglia d'oro" in testo and "2 sfide aspettano la tua risposta entro oggi, prima dell'avanzamento seguente." in testo
    assert "In Italia: 2 tornei conclusi, 40 incontri di torneo e 3 sfide fra polisportive." in testo
    secondo = Mondo.rapporto_vuoto("oggi")
    secondo.update(sfide_in_attesa=0, notizie=["Club Di Prova vince la sfida con PoliTeam04, 31 a 27."])
    somma = testi.somma_rapporti(primo, secondo)
    assert somma["sfide_in_attesa"] == 0 and len(somma["notizie"]) == 2 and somma["tornei_conclusi"] == 2 and somma["ora"] == "oggi"
