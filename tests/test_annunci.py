"""
Le prove degli annunci della cronaca, 1.79.0: le righe alla sintesi, accodate, e al display braille in
blocchi grandi quanto le celle, in fila col tempo minimo di lettura. Le uscite sono finte, dal conftest,
e le attese pure: nessuna prova parla né aspetta.
"""

import types

import annunci
import impostazioni


class Attese:
    """Le attese della coda del display: si annotano, e la prova le fa scadere quando vuole."""

    def __init__(self):
        self.adesso = 0.0
        self.in_attesa = []

    def pianifica(self, secondi, funzione):
        attesa = types.SimpleNamespace(quando=self.adesso + secondi, funzione=funzione, ferma=False)
        attesa.Stop = lambda: setattr(attesa, "ferma", True)
        self.in_attesa.append(attesa)
        return attesa

    def scorri(self, secondi):
        self.adesso += secondi
        for attesa in [a for a in self.in_attesa if not a.ferma and a.quando <= self.adesso]:
            self.in_attesa.remove(attesa)
            attesa.funzione()


def _annunci():
    attese = Attese()
    return annunci.Annunci(attese.pianifica, orologio=lambda: attese.adesso), attese


def test_i_predefiniti_leggono_alla_sintesi_e_al_braille(voce_finta):
    lettore, _attese = _annunci()
    lettore.annuncia(["Set 1, Rossi 0, Bianchi 0.", "Rossi in battuta."], impostazioni.valide(None))
    # Alla sintesi le righe si accodano, con l'uscita automatica: NVDA, attivo nelle prove.
    assert voce_finta.detti == [("nvda", "Set 1, Rossi 0, Bianchi 0."), ("nvda", "Rossi in battuta.")]
    # Al display la prima riga subito, la seconda aspetta il suo turno.
    assert voce_finta.braille == [("nvda", "Set 1, Rossi 0, Bianchi 0.")] and lettore.in_fila == 1


def test_il_display_a_blocchi_col_tempo_minimo(voce_finta):
    lettore, attese = _annunci()
    scelte = impostazioni.valide({"annunci_dove": "braille", "annunci_celle": 20, "annunci_lettura_minima": 1500})
    lettore.annuncia(["Rossi attacca di diritto, Bianchi para in tuffo."], scelte)
    assert voce_finta.detti == []
    assert voce_finta.braille == [("nvda", "Rossi attacca di")]
    attese.scorri(1.0)
    assert len(voce_finta.braille) == 1
    attese.scorri(0.5)
    attese.scorri(1.5)
    assert [testo for _uscita, testo in voce_finta.braille] == ["Rossi attacca di", "diritto, Bianchi", "para in tuffo."]
    assert all(len(testo) <= 20 for _uscita, testo in voce_finta.braille)


def test_zero_celle_manda_la_riga_intera_e_solo_alla_sintesi(voce_finta):
    lettore, _attese = _annunci()
    riga = "Rossi attacca di diritto, Bianchi para in tuffo e rilancia lungo la sponda."
    lettore.annuncia([riga], impostazioni.valide({"annunci_celle": 0}))
    assert voce_finta.braille == [("nvda", riga)]
    lettore.annuncia(["Punto per Rossi."], impostazioni.valide({"annunci_dove": "sintesi"}))
    assert voce_finta.detti[-1] == ("nvda", "Punto per Rossi.") and len(voce_finta.braille) == 1


def test_spenti_non_dicono_niente(voce_finta):
    lettore, _attese = _annunci()
    lettore.annuncia(["Set 1, Rossi 0, Bianchi 0."], impostazioni.valide({"annunci_cronaca": False}))
    assert voce_finta.detti == [] and voce_finta.braille == [] and lettore.in_fila == 0


def test_con_la_voce_di_windows_il_braille_arriva_dallo_screen_reader(voce_finta):
    # SAPI5 non ha il braille: il display riceve le righe dallo screen reader che risponde.
    lettore, _attese = _annunci()
    lettore.annuncia(["Punto per Rossi."], impostazioni.valide({"annunci_sintesi": "sapi5"}))
    assert voce_finta.detti == [("sapi5", "Punto per Rossi.")]
    assert voce_finta.braille == [("nvda", "Punto per Rossi.")]


def test_svuota_toglie_le_righe_in_fila(voce_finta):
    lettore, attese = _annunci()
    lettore.annuncia(["Uno.", "Due.", "Tre."], impostazioni.valide({"annunci_dove": "braille"}))
    assert lettore.in_fila == 2
    lettore.svuota()
    attese.scorri(10.0)
    assert lettore.in_fila == 0 and voce_finta.braille == [("nvda", "Uno.")]
