"""
Test degli acciacchi della tappa 12, regola di Gabriele sugli infortuni, punto 7.3 del progetto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Il calo che scende in linea retta e finisce; il più pesante dei due acciacchi che resta;
l'infortunio che cancella l'acciacco; il giorno simulato che toglie quelli finiti; il calo che entra
nell'efficienza e toglie vittorie; il diario soltanto per i tesserati dell'utente; la presentazione e
la chiusura nella cronaca; il salvataggio dei campi nuovi.
"""

import datetime
import random

import pytest
from aiuti_motore import giocatore

import infortuni
from modelli import Giocatore, Polisportiva
from mondo import Mondo
from motore import COMPLETO, ESSENZIALE, SINGOLARE_3, Incontro, simula_incontro
from motore import cronaca as C
from motore.campo import efficienza
from partita import MotorePartita

OGGI = datetime.datetime(2026, 5, 4, 9, 0)


def _mondo(*giocatori):
    mondo = Mondo()
    mondo.datetime_corrente_simulazione = OGGI
    for g in giocatori:
        mondo.giocatori[g.id] = g
    return mondo


def _acciaccato(g, calo=0.02, giorni=5, sede="ginocchio", da=OGGI):
    g.acciacco_fino = da + datetime.timedelta(days=giorni)
    g.acciacco_calo = calo
    g.acciacco_giorni = giorni
    g.acciacco_sede = sede
    return g


def test_il_calo_scende_in_linea_retta_e_finisce():
    g = _acciaccato(giocatore(1), calo=0.02, giorni=5)
    cali = [infortuni.calo_acciacco(g, OGGI + datetime.timedelta(days=n)) for n in range(7)]
    assert cali[:5] == pytest.approx([0.02, 0.016, 0.012, 0.008, 0.004])
    assert cali[5] == cali[6] == 0.0
    assert infortuni.calo_acciacco(giocatore(2), OGGI) == 0.0


def test_resta_il_piu_pesante_e_l_infortunio_lo_cancella():
    g = giocatore(1)
    mondo = _mondo(g)
    frase = infortuni.acciacca(mondo, g, "caviglia", random.Random(1))
    assert frase and g.acciacco_sede == "caviglia" and 3 <= g.acciacco_giorni <= 7 and 0.012 <= g.acciacco_calo <= 0.028
    pesante = (g.acciacco_calo, g.acciacco_fino)
    # Un acciacco più leggero non lo sostituisce; il giorno dopo quello di prima pesa meno, e uno nuovo lo sostituisce.
    for seme in range(2, 40):
        rng = random.Random(seme)
        prova = random.Random(seme)
        prova.randint(3, 7)
        if prova.uniform(0.012, 0.028) < pesante[0]:
            assert infortuni.acciacca(mondo, g, "schiena", rng) is None
            assert (g.acciacco_calo, g.acciacco_fino, g.acciacco_sede) == (*pesante, "caviglia")
            break
    mondo.datetime_corrente_simulazione = OGGI + datetime.timedelta(days=g.acciacco_giorni - 1)
    assert infortuni.acciacca(mondo, g, "schiena", random.Random(99)) is not None and g.acciacco_sede == "schiena"
    infortuni.colpisci(mondo, g, "gomito_dx", random.Random(5))
    assert g.infortunato and (g.acciacco_fino, g.acciacco_calo, g.acciacco_giorni, g.acciacco_sede) == (None, 0.0, 0, None)
    # Chi è infortunato non prende acciacchi.
    assert infortuni.acciacca(mondo, g, "schiena", random.Random(7)) is None


def test_il_giorno_simulato_toglie_gli_acciacchi_finiti(monkeypatch):
    g = _acciaccato(giocatore(1), giorni=3)
    g.etamorte = g.etaritiro = 10 ** 6
    mondo = _mondo(g)
    monkeypatch.setattr("mondo.PROB_USCITA_PREMATURA_GIORNALIERA", 0)
    rapporto = {"guariti": 0, "usciti": 0, "morti": 0, "ritirati": 0, "tuoi_usciti": 0, "tuoi_ritirati": 0}
    mondo._fai_invecchiare(OGGI + datetime.timedelta(days=2), rapporto)
    assert g.acciacco_fino is not None
    mondo._fai_invecchiare(OGGI + datetime.timedelta(days=3), rapporto)
    assert (g.acciacco_fino, g.acciacco_calo, g.acciacco_giorni, g.acciacco_sede) == (None, 0.0, 0, None)


def test_il_calo_entra_nell_efficienza():
    a, b = giocatore(1), giocatore(2)
    incontro = Incontro(a, b, SINGOLARE_3, seme=1, dettaglio=ESSENZIALE, cali={1: 0.05})
    c = incontro.campo[1]
    c.azioni = 40
    c.prepara_punto(incontro.campo[2])
    assert c.eff == pytest.approx(efficienza(40, c.ritmo, c.tar) * 0.95)
    incontro.campo[2].azioni = 40
    incontro.campo[2].prepara_punto(c)
    assert incontro.campo[2].eff == efficienza(40, incontro.campo[2].ritmo, c.tar)


def test_l_acciaccato_vince_di_meno():
    a, b = giocatore(1), giocatore(2)
    rng = random.Random("acciacco")
    semi = [rng.getrandbits(63) for _ in range(400)]
    sano = sum(simula_incontro(a, b, SINGOLARE_3, seme=s, dettaglio=ESSENZIALE).vincitore == "A" for s in semi)
    acciaccato = sum(simula_incontro(a, b, SINGOLARE_3, seme=s, dettaglio=ESSENZIALE, cali={1: 0.06}).vincitore == "A" for s in semi)
    assert acciaccato < sano


class SoloAcciacchi(Incontro):
    """Un incontro in cui gli infortuni che fermano non escono mai, per guardare gli acciacchi."""

    def _infortuni_a_fine_set(self, chiude):
        return []


class Sempre(random.Random):
    def random(self):
        return 0.0


def test_la_cronaca_dice_chi_gioca_acciaccato_e_chi_ne_esce():
    a = _acciaccato(giocatore(1, cognome="Rossi"), sede="caviglia")
    b = giocatore(2, cognome="Bianchi", sesso="f")
    r = SoloAcciacchi(a, b, SINGOLARE_3, seme=4, dettaglio=COMPLETO, basi_infortunio={2: 5.0}, cali={1: 0.02}, caso_infortuni=Sempre()).gioca()
    assert r.acciacchi == [(2, "spalla_dx")] and r.infortuni == []
    righe = C.componi(r.momenti, C.nomi_dei_giocatori([a, b]), C.NORMALE)
    assert righe[0].endswith("Rossi gioca con un acciacco alla caviglia.")
    assert righe[-1].endswith("A fine incontro Bianchi risente di un colpo alla spalla destra.")


def test_il_diario_dell_acciacco_soltanto_per_i_tuoi():
    tuo, altro = giocatore(1), giocatore(2)
    mondo = _mondo(tuo, altro)
    mia = Polisportiva("Club Di Prova", None, OGGI)
    mondo.polisportive[mia.nome] = mia
    mondo._entra(mia, tuo)
    r = SoloAcciacchi(tuo, altro, SINGOLARE_3, seme=4, dettaglio=ESSENZIALE, basi_infortunio={1: 5.0, 2: 5.0}, caso_infortuni=Sempre()).gioca()
    prima = len(altro.diario)
    frasi = MotorePartita(mondo).registra(r)
    assert tuo.acciacco_sede == "spalla_dx" and altro.acciacco_sede == "spalla_dx"
    assert tuo.diario[0]["testo"].startswith("Risente di un colpo alla spalla destra: per ") and tuo.diario[0]["testo"].endswith("giorni renderà un poco meno.")
    assert len(altro.diario) == prima + 1 and not altro.diario[0]["testo"].startswith("Risente")
    assert sum(1 for f in frasi if "risente di un colpo" in f) == 2


def test_l_amichevole_passa_al_motore_il_calo_di_oggi():
    a = _acciaccato(giocatore(1), calo=0.03, giorni=4, da=OGGI - datetime.timedelta(days=1))
    mondo = _mondo(a, giocatore(2))
    basi, cali = MotorePartita(mondo).basi_e_cali(a, mondo.giocatori[2])
    assert cali == {1: pytest.approx(0.03 * 3 / 4)} and set(basi) == {1, 2}
    assert MotorePartita(mondo).basi_e_cali(mondo.giocatori[2])[1] is None


def test_i_campi_dell_acciacco_si_salvano_e_si_controllano():
    g = _acciaccato(giocatore(1), calo=0.021, giorni=6, sede="schiena")
    dati = g.a_dizionario()
    riletto = Giocatore.da_dizionario(dati)
    assert (riletto.acciacco_fino, riletto.acciacco_calo, riletto.acciacco_giorni, riletto.acciacco_sede) == (g.acciacco_fino, 0.021, 6, "schiena")
    for campo, valore in (("acciacco_calo", 1.5), ("acciacco_giorni", -1), ("acciacco_sede", "naso")):
        guasto = dict(dati, **{campo: valore})
        with pytest.raises(ValueError, match=campo):
            Giocatore.da_dizionario(guasto)
    with pytest.raises(ValueError, match="acciacco_fino"):
        Giocatore.da_dizionario(dict(dati, acciacco_fino=None))
