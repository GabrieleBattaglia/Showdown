"""
Le prove del motore della finestra unica Mercato e ricerca, issue 8 e decisione D36: chi cercare con le voci dello
Stato; le tredici ricerche pronte e lo stato di ogni porta d'ingresso; la funzione che dice di chi è una polisportiva;
la memoria di classe e valore di mercato; le funzioni pure che dicono, per ogni riga, quale offerta si può fare, se si
gioca un'amichevole o si sfida il club, o perché no; e i testi della finestra, la riga e la Situazione.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nascono il 24 ottobre 2026 coi passi 2 e 3 della proposta della issue 8. Lo stesso giorno, col formato 10
dell'archivio, lo stato di ogni porta che va e torna dal salvataggio, il mondo del formato 9 che riceve quello
predefinito, e il salvataggio con uno stato che non va, che si rifiuta. Con le verifiche dello stesso giorno: il
mondo che non ricorda e non scrive uno stato che poi rifiuterebbe, e ogni stato che il motore produce che si salva
e si rilegge; la migrazione dal 9 con la sua costante storica; i tesserati del computer in fondo al prezzo sul
valore di mercato.
Lo stesso giorno, coi preset dei filtri: i dodici preset di serie al posto delle ricerche pronte, la casella dei preset,
le regole del nome, il salvataggio con la sostituzione, la rinomina, l'eliminazione e lo spostamento, il mondo che
ricorda preset e porte; nel formato 10 nuovo il giro del salvataggio, la migrazione dal 9, e la lettura indulgente: i
salvataggi rovinati che tornano ai filtri di serie con un avviso nel registro, il preset che si ripara invece di
sparire.
Lo stesso giorno, col passo della finestra, il mondo delle prove sta in tests/aiuti_mercato.py, comune con quelle della
finestra; e si provano il ripiego dopo un esito e il club che oggi ha già rifiutato una sfida.
La sera dello stesso giorno, col cambio della finestra al costruttore di regole, il motore a schede esce e queste prove
passano alle regole: chi cercare con le voci dello Stato, i preset di serie fatti di regole, i preset di Gabriele coi
loro filtri di regole, le porte con la regola in preparazione, il salvataggio nella forma delle regole attraverso
l'archivio, la riga dell'allenatore col dato dei sei ordini comuni e la scheda con l'ambizione col numero. Le prove dei
filtri di prima, di Filtri attivi e dei guasti della lettura a schede escono con lui: quelle delle regole stanno in
tests/test_regole_dei_filtri.py e in tests/test_regole_dei_filtri_salvate.py.
"""

import copy
import dataclasses
import datetime
import gzip
import json
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

G = mercato.GIOCATORI
A = mercato.ALLENATORI
E = mercato.E
O = mercato.O


@pytest.fixture
def mondo():
    """Il mondo di tests/aiuti_mercato.py, comune alle prove della finestra: 120 giocatori, due tue polisportive e due del computer, sei allenatori."""
    return mondo_del_mercato()


def _cpu(m, posto=0):
    return sorted((p for p in m.polisportive.values() if p.is_cpu_controlled), key=lambda p: p.nome)[posto]


def _ids(righe):
    return {r.persona.id for r in righe}


def _regola(bersaglio, chiave, operatore, valore, collegamento=E):
    return mercato.Regola(collegamento, bersaglio, chiave, operatore, valore)


def _stato(valore, bersaglio=G, collegamento=E):
    return _regola(bersaglio, "stato", "uguale", valore, collegamento)


def _filtri(*regole, ordine="numero"):
    return mercato.Filtri(mercato.con_la_prima_e(regole), ordine)


def _cerca(m, *regole, ordine="numero"):
    return mercato.cerca(m, _filtri(*regole, ordine=ordine))


def _riga(m, gid):
    """La riga del giocatore, dalla memoria della finestra, qualunque sia il suo stato."""
    return next(r for r in mercato.Memoria(m).righe_di(G) if r.persona.id == gid)


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


# Chi cercare: le voci dello Stato.

def test_le_voci_dello_stato_scelgono_chi_cercare(mondo):
    cpu0, cpu1 = _cpu(mondo, 0), _cpu(mondo, 1)
    morti = mondo._ids_morti_processati_sessione
    liberi = {gid for gid, g in mondo.giocatori.items() if g.appartenenza == "*" and not g.ritirato and gid not in morti}
    assert _ids(_cerca(mondo, _stato(mercato.LIBERO))) == liberi
    # In vendita da altri: soltanto chi vende una polisportiva che non è tua, dalle liste in_vendita.
    in_vendita = _cerca(mondo, _stato(mercato.IN_VENDITA))
    assert [(r.persona.id, r.stato, r.polisportiva, r.prezzo, r.costo) for r in in_vendita] == [(10, mercato.IN_VENDITA, cpu0, 3000, 3000)]
    computer = _cerca(mondo, _stato(mercato.DEL_COMPUTER))
    assert _ids(computer) == set(cpu0.tesserati) | set(cpu1.tesserati)
    assert next(r for r in computer if r.persona.id == 10).stato == mercato.IN_VENDITA
    assert all(r.stato == mercato.DEL_COMPUTER and r.costo == economia.valore_di_mercato(r.persona, ORA) for r in computer if r.persona.id != 10)
    tuoi = _cerca(mondo, _stato(mercato.TUO))
    assert _ids(tuoi) == set(range(1, 10)) and all(r.stato == mercato.TUO for r in tuoi)
    assert _ids(_cerca(mondo, _stato(mercato.RITIRATO))) == set(range(40, 45))
    assert _ids(_cerca(mondo, _stato(mercato.USCITO))) == {45}
    assert mercato.cerca(mondo, mercato.Filtri()) == []
    tutte = _cerca(mondo, _stato(mercato.IN_ATTIVITA), _stato(mercato.RITIRATO, collegamento=O), _stato(mercato.USCITO, collegamento=O))
    assert len(tutte) == len(_ids(tutte)) == len(mondo.giocatori)


def test_chi_e_in_vendita_si_legge_dalle_liste_e_va_controllato(mondo):
    cpu0 = _cpu(mondo, 0)
    # Un venduto rimasto in lista, un uscito di scena e un ritirato non si comprano.
    cpu0.in_vendita[60] = 10
    cpu0.in_vendita[45] = 10
    cpu0.in_vendita[40] = 10
    assert _ids(_cerca(mondo, _stato(mercato.IN_VENDITA))) == {10}


def test_costi_e_stipendi_delle_righe(mondo):
    mia = mondo.miapolisportiva_attiva
    libero = _cerca(mondo, _stato(mercato.LIBERO))[0]
    assert libero.costo == economia.ingaggio_richiesto(libero.persona, mia) and libero.stipendio == economia.stipendio(libero.persona)
    tuoi = {r.persona.id: r for r in _cerca(mondo, _stato(mercato.TUO))}
    # Da un'altra tua polisportiva oggi si compra al prezzo; dalla attiva no, è già sua.
    assert (tuoi[6].di_chi, tuoi[6].prezzo, tuoi[6].costo) == (mercato.TUA_ALTRA, 1, 1)
    assert (tuoi[1].di_chi, tuoi[1].prezzo, tuoi[1].costo) == (mercato.TUA_ATTIVA, 500, None)
    assert tuoi[2].costo is None and tuoi[2].stipendio == economia.stipendio_pagato(mondo.giocatori[2])
    assert all(r.stipendio is None and r.costo is None for r in _cerca(mondo, _stato(mercato.RITIRATO)))
    mondo.miapolisportiva_attiva = None
    assert all(r.costo is None for r in _cerca(mondo, _stato(mercato.LIBERO)))


# I preset di serie, la casella e i preset di Gabriele.

def test_i_dodici_preset_di_serie(mondo):
    assert len(mercato.PRESET_DI_SERIE) == 12 and len(set(dict(mercato.PRESET_DI_SERIE).values())) == 12
    for chiave, _nome in mercato.PRESET_DI_SERIE:
        filtri = mercato.filtri_di_serie(chiave)
        assert filtri.regole and all(r.collegamento == E for r in filtri.regole) and filtri.ordine in dict(mercato.ORDINI), chiave
        assert mercato.cerca(mondo, filtri), chiave
    assert mercato.filtri_di_serie("mercato") == mercato.Filtri((_stato(mercato.SUL_MERCATO),), "valore_alto")
    assert _regola(G, "eta", "minore_uguale", mercato.ETA_DEI_GIOVANI) in mercato.filtri_di_serie("giovani_migliori").regole and mercato.ETA_DEI_GIOVANI == 20
    assert mercato.filtri_di_serie("avversari_amichevole") == mercato.Filtri((_regola(G, "disponibile", "uguale", True),), "classe")
    assert mercato.nome_del_preset_di_serie("tutti_in_attivita") == "Tutti in attività, per numero"
    # I capi e gli assistenti migliori guardano soltanto chi ha quel posto, niente liberi.
    capi = mercato.cerca(mondo, mercato.filtri_di_serie("capi_migliori"))
    assert [r.persona.numero for r in capi] == [_cpu(mondo).staff[0]]
    assistenti = mercato.cerca(mondo, mercato.filtri_di_serie("assistenti_migliori"))
    assert [r.persona.numero for r in assistenti] == [mondo.miapolisportiva_attiva.staff[1]]
    # Torna ai tuoi filtri non c'è più: lo sostituisce la voce Filtri attuali, non salvati. I filtri non si cambiano.
    with pytest.raises(KeyError):
        mercato.filtri_di_serie("torna_ai_tuoi")
    with pytest.raises(dataclasses.FrozenInstanceError):
        mercato.filtri_di_serie("giovani_migliori").ordine = "numero"
    assert set(mercato.PRESET_DELLA_PORTA) == set(mercato.NOMI_DELLE_PORTE) == set(mercato.PORTE) == {"mercato", "allenatori", "ricerca", "amichevole"}
    assert set(mercato.PRESET_DELLA_PORTA.values()) <= set(dict(mercato.PRESET_DI_SERIE))


def test_la_casella_dei_preset():
    fdr = mercato.filtri_di_ricerca_di_serie()
    voci = mercato.voci_della_casella(fdr)
    assert len(voci) == 14 and voci[0] == mercato.Voce(mercato.VOCE_ATTUALI, None, "Filtri attuali, non salvati")
    assert voci[-1] == mercato.Voce(mercato.VOCE_SALVA, None, "Salva filtri...")
    assert [(voce.tipo, voce.scelta, voce.nome) for voce in voci[1:-1]] == [(mercato.VOCE_DI_SERIE, chiave, nome) for chiave, nome in mercato.PRESET_DI_SERIE]
    mancini = _filtri(_stato(mercato.LIBERO), _regola(G, "mancino", "uguale", True))
    donne = _filtri(_stato(mercato.LIBERO), _regola(G, "sesso", "uguale", "f"))
    mercato.salva_preset(fdr, "Giovani mancini", mancini)
    mercato.salva_preset(fdr, "Donne", donne)
    voci = mercato.voci_della_casella(fdr)
    assert len(voci) == 16 and voci[1:3] == [mercato.Voce(mercato.VOCE_TUA, 1, "Giovani mancini"), mercato.Voce(mercato.VOCE_TUA, 2, "Donne")]
    assert voci[3].scelta == "mercato" and voci[-1].tipo == mercato.VOCE_SALVA
    assert mercato.posto_della_scelta(voci, None) == 0 and mercato.posto_della_scelta(voci, 2) == 2 and mercato.posto_della_scelta(voci, "mercato") == 3
    assert mercato.posto_della_scelta(voci, 9) is None and mercato.posto_della_scelta(voci, True) is None and mercato.posto_della_scelta(voci, "inventata") is None
    attuali = _filtri(_stato(mercato.TUO))
    assert mercato.filtri_della_voce(fdr, None, attuali) == attuali
    assert mercato.filtri_della_voce(fdr, 2, attuali) == donne and mercato.filtri_della_voce(fdr, "piu_forti", attuali) == mercato.filtri_di_serie("piu_forti")
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
    mercato.salva_preset(fdr, "Giovani", _filtri(_stato(mercato.LIBERO)))
    mercato.salva_preset(fdr, "Vecchi", _filtri(_stato(mercato.RITIRATO)))
    # Salvando, il nome di un tuo preset non è un problema: Salva filtri chiede se sostituirne i filtri.
    assert mercato.problema_del_nome(fdr, "GIOVANI") is None
    # Rinominando sì, salvo per il preset stesso, che può cambiare soltanto le maiuscole.
    assert mercato.problema_del_nome(fdr, " giovani ", 2) == "Esiste già un preset che si chiama Giovani."
    assert mercato.problema_del_nome(fdr, "GIOVANI", 1) is None


def test_salva_rinomina_elimina_e_sposta_i_preset():
    fdr = mercato.filtri_di_ricerca_di_serie()
    filtri = _filtri(_stato(mercato.LIBERO), _regola(G, "sesso", "uguale", "f"))
    preset, sostituito = mercato.salva_preset(fdr, "  Giovani mancini ", filtri)
    assert (preset.numero, preset.nome, sostituito, fdr.prossimo_preset) == (1, "Giovani mancini", False, 2) and preset.filtri == filtri
    mercato.salva_preset(fdr, "Altro", _filtri(_stato(mercato.TUO)))
    # Lo stesso nome, senza badare alle maiuscole: si sostituiscono i filtri, e il preset tiene nome, posto e numero.
    ritirati = _filtri(_stato(mercato.RITIRATO))
    stesso, sostituito = mercato.salva_preset(fdr, "GIOVANI MANCINI", ritirati)
    assert sostituito and stesso is fdr.preset[0] and (stesso.numero, stesso.nome) == (1, "Giovani mancini")
    assert stesso.filtri == ritirati and fdr.prossimo_preset == 3 and len(fdr.preset) == 2
    with pytest.raises(ValueError, match=r"^Il nome del preset deve avere da 1 a 50 caratteri\.$"):
        mercato.salva_preset(fdr, " ", mercato.Filtri())
    rotti = _filtri(_regola(G, "sesso", "uguale", ""))
    with pytest.raises(ValueError, match=r'^I filtri non sono validi: la regola 1 non va: il valore "" non va per sesso, è$'):
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
    # L'eliminazione: le porte che lo riaprivano tornano al loro preset di serie, coi filtri attuali e la regola in
    # preparazione, e il numero non torna.
    preparazione = mercato.Preparazione(E, G, "nome", "contiene", "ros")
    fdr.porte["mercato"] = mercato.StatoDellaPorta(1, _filtri(_stato(mercato.LIBERO)), preparazione)
    fdr.porte["ricerca"] = mercato.StatoDellaPorta(2, _filtri(_stato(mercato.TUO)), mercato.preparazione_di_serie("ricerca"))
    assert mercato.elimina_preset(fdr, 1).nome == "giovani MANCINI" and [p.numero for p in fdr.preset] == [2]
    assert fdr.porte["mercato"] == mercato.StatoDellaPorta("mercato", _filtri(_stato(mercato.LIBERO)), preparazione) and fdr.porte["ricerca"].scelta == 2
    assert mercato.salva_preset(fdr, "Terzo", _filtri(_stato(mercato.LIBERO)))[0].numero == 3
    with pytest.raises(KeyError):
        mercato.elimina_preset(fdr, 1)


def test_il_mondo_ricorda_preset_e_porte(mondo):
    assert mondo.filtri_di_ricerca is None and mercato.filtri_di_ricerca_del_mondo(mondo) == mercato.filtri_di_ricerca_di_serie()
    for porta in mercato.PORTE:
        stato = mercato.stato_della_porta(mondo, porta)
        chiave = mercato.PRESET_DELLA_PORTA[porta]
        assert stato == mercato.stato_di_serie(porta) == mercato.StatoDellaPorta(chiave, mercato.filtri_di_serie(chiave), mercato.preparazione_di_serie(porta))
    assert mercato.stato_della_porta(mondo, "allenatori").preparazione.bersaglio == A
    with pytest.raises(KeyError):
        mercato.stato_della_porta(mondo, "altrove")
    # La finestra cambia la sua copia; il mondo cambia soltanto con ricorda_i_preset.
    copia = mercato.filtri_di_ricerca_del_mondo(mondo)
    donne = _filtri(_stato(mercato.LIBERO), _regola(G, "sesso", "uguale", "f"))
    mercato.salva_preset(copia, "Donne libere", donne)
    assert mondo.filtri_di_ricerca is None
    mercato.ricorda_i_preset(mondo, copia)
    assert [(p.numero, p.nome) for p in mondo.filtri_di_ricerca.preset] == [(1, "Donne libere")] and mondo.filtri_di_ricerca.prossimo_preset == 2
    copia.preset[0].nome = "Altro nome"
    assert mondo.filtri_di_ricerca.preset[0].nome == "Donne libere"
    # La porta ricorda la voce scelta, i filtri attuali e la regola in preparazione; le altre restano di serie.
    tuoi = _filtri(_stato(mercato.TUO))
    preparazione = mercato.Preparazione(O, G, "eta", "minore", "2.5")
    mercato.ricorda_la_porta(mondo, "mercato", mercato.StatoDellaPorta(1, tuoi, preparazione))
    assert mercato.stato_della_porta(mondo, "mercato") == mercato.StatoDellaPorta(1, tuoi, preparazione)
    assert mercato.stato_della_porta(mondo, "ricerca") == mercato.stato_di_serie("ricerca")
    letto = mercato.stato_della_porta(mondo, "mercato")
    assert mercato.filtri_della_voce(mondo.filtri_di_ricerca, letto.scelta, letto.attuali) == donne
    # Il preset eliminato nella finestra: la porta che lo riapriva torna al suo preset di serie, coi suoi filtri attuali.
    copia = mercato.filtri_di_ricerca_del_mondo(mondo)
    mercato.elimina_preset(copia, 1)
    mercato.ricorda_i_preset(mondo, copia)
    assert mondo.filtri_di_ricerca.preset == [] and mondo.filtri_di_ricerca.prossimo_preset == 2
    assert mercato.stato_della_porta(mondo, "mercato") == mercato.StatoDellaPorta("mercato", tuoi, preparazione)
    # Una porta non ricorda un preset che non c'è, né una porta che non esiste; il mondo resta com'era.
    prima = mondo.filtri_di_ricerca.copia()
    with pytest.raises(ValueError, match=r"^La porta Mercato, Ctrl\+K, riapriva il preset numero 1, che non c'è più$"):
        mercato.ricorda_la_porta(mondo, "mercato", mercato.StatoDellaPorta(1, mercato.Filtri(), preparazione))
    with pytest.raises(KeyError):
        mercato.ricorda_la_porta(mondo, "altrove", mercato.StatoDellaPorta(None, mercato.Filtri(), preparazione))
    assert mondo.filtri_di_ricerca == prima


# La memoria della finestra.

def test_la_memoria_calcola_la_classe_una_volta_sola(mondo, monkeypatch):
    chiamate = []
    vero = classe.punteggio
    monkeypatch.setattr(classe, "punteggio", lambda g: chiamate.append(g.id) or vero(g))
    memoria = mercato.Memoria(mondo)
    tutti = _filtri(_stato(mercato.IN_ATTIVITA), _regola(G, "classe", "migliore_uguale", 60), ordine="classe")
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
    righe = _cerca(mondo, _stato(mercato.LIBERO))
    assert mercato.indice_della_persona(righe, righe[3].persona.id) == 3
    assert mercato.indice_della_persona(righe, 9999) == 0 and mercato.indice_della_persona([], 1) is None
    # Dopo un esito, chi non c'è più lascia la scelta allo stesso posto, entro le righe.
    assert mercato.indice_della_persona(righe, 9999, ripiego=2) == 2
    assert mercato.indice_della_persona(righe, 9999, ripiego=len(righe) + 5) == len(righe) - 1
    assert mercato.indice_della_persona(righe, righe[3].persona.id, ripiego=1) == 3


# Le azioni sulle righe.

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
    liberi = _cerca(mondo, _stato(mercato.LIBERO, A), ordine="classe")
    assert mercato.offerta_possibile(mondo, mia, liberi[0]) == (mercato.INGAGGIO_ALLENATORE, None, None)
    assert mercato.offerta_possibile(mondo, mia, liberi[0], posto=1).motivo == "staff_posto_occupato"
    impiegato = _cerca(mondo, _stato(mercato.DEL_COMPUTER, A))[0]
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
    allenatore = _cerca(mondo, _stato(mercato.LIBERO, A), ordine="classe")[0]
    assert mercato.amichevole_possibile(mondo, mia, allenatore).motivo == mercato.NON_GIOCA_OGGI
    assert mercato.amichevole_possibile(mondo, None, _riga(mondo, libero)).motivo == mercato.NESSUNA_POLISPORTIVA_ATTIVA
    # Il tuo giocatore si sceglie fra i disponibili della polisportiva attiva, esclusa la persona già scelta.
    assert [g.id for g in mercato.tuoi_per_l_amichevole(mondo, mia, mondo.giocatori[3])] == [1, 2, 4, 5]
    mondo.giocatori[1].ultimo_impegno = ORA
    assert [g.id for g in mercato.tuoi_per_l_amichevole(mondo, mia, None)] == [2, 3, 4, 5]
    cpu0 = _cpu(mondo)
    assert mercato.sfida_possibile(mondo, mia, _riga(mondo, 11)) == (mercato.SFIDA, None, None)
    assert mercato.sfida_possibile(mondo, mia, _riga(mondo, 10)) == (mercato.SFIDA, None, None)
    assert mercato.sfida_possibile(mondo, mia, _cerca(mondo, _stato(mercato.DEL_COMPUTER, A))[0]).problema is None
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
    assert cpu0.nome in {r.polisportiva.nome for r in _cerca(mondo, _stato(mercato.DEL_COMPUTER))}


# I testi della finestra.

def test_la_riga_del_giocatore_trovato(mondo):
    memoria = mercato.Memoria(mondo)
    libero = next(r for r in mercato.cerca(mondo, _filtri(_stato(mercato.LIBERO)), memoria) if not r.persona.mancino and not r.persona.ambidestro)
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
    # Dal costruttore di regole l'ambizione ha il decimale che le regole confrontano, come la scheda.
    assert f", 17:4:3, ambizione {testi.numero(g.ambizione)}, valore " in testi.riga_trovato(libero, mondo, "ambizione", memoria)
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


def test_la_riga_dell_allenatore_ha_l_eta_completa_la_regione_e_il_dato_degli_ordini_comuni(mondo):
    libero = _cerca(mondo, _stato(mercato.LIBERO, A), ordine="classe")[0]
    a = libero.persona
    riga = testi.riga_trovato(libero, mondo, "classe")
    assert riga == testi.riga_allenatore(a, mondo, "classe")
    assert re.match(rf"{re.escape(testi.nome_allenatore(a))}, \d+:\d:\d, (nato allenatore|nata allenatrice), ", riga)
    assert testi.eta_completa_allenatore(a, ORA) in riga and riga.endswith(f", {luoghi.provincia_e_regione(a.luogo)[1]}") and " anni, " not in riga
    assert riga.split(", ")[2] != "chiede" and testi.riga_allenatore(a, mondo, "stipendio_basso").split(", ")[3].startswith("chiede ")
    assert testi.riga_allenatore(a, mondo, "numero").split(", ")[3] == f"numero {a.numero}"
    # Un libero non ha un contratto: coi mesi di contratto la sua riga resta quella di sempre.
    assert testi.riga_allenatore(a, mondo, "mesi_contratto") == riga
    impiegato = _cerca(mondo, _stato(mercato.DEL_COMPUTER, A))[0]
    b = impiegato.persona
    per_stipendio = testi.riga_trovato(impiegato, mondo, "stipendio_basso")
    assert f", capo {'allenatrice' if b.sesso == 'f' else 'allenatore'} di {_cpu(mondo).nome}, " in per_stipendio
    # Dal costruttore di regole i sei ordini comuni hanno il loro dato in testa anche per chi allena.
    assert per_stipendio.split(", ")[3] == f"chiederebbe {testi.euro(staff.stipendio_richiesto(b, staff.CAPO))} al mese da capo"
    assert testi.riga_trovato(impiegato, mondo, "mesi_contratto").split(", ")[3].startswith("contratto fino a")


def test_la_situazione_in_una_riga_senza_blocchi(mondo):
    # Dal 24 ottobre 2026, regola di Gabriele: nelle finestre niente blocchi di quaranta caratteri, solo a console.
    assert testi.situazione(mondo) == ("Mosse rimaste 5 su 5, sfide da lanciare 2, cassa 20.000 euro, gloria 100, Pat-Bologna, "
                                       "tesserati 5 su 15, staff: mancano il capo e l'assistente 2.")
    mondo.miapolisportiva_attiva = None
    assert testi.situazione(mondo) == "Nessuna polisportiva attiva: puoi solo cercare."
    lungo = testi.a_blocchi(["x" * 45, "corto"])
    assert lungo == "x" * 45 + "," + " " * 34 + "corto."


def test_il_riepilogo_unico(mondo):
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
    assert testi.linguetta_dei_filtri(0) == "Filtri, nessuna regola" and testi.linguetta_dei_filtri(1) == "Filtri, 1 regola"
    assert testi.linguetta_dei_filtri(3) == "Filtri, 3 regole"
    r = _riga(mondo, 11)
    assert testi.etichetta_della_scheda(r) == f"Sc&heda di {testi.nome_completo(r.persona)}" and testi.etichetta_della_scheda(None) == "Sc&heda"
    assert testi.scheda_della_riga(r, mondo) == testi.scheda_giocatore(r.persona, mondo)
    # Dal costruttore di regole la scheda scrive l'ambizione anche col numero, quello che le regole confrontano.
    g = r.persona
    assert f"| Ambizione: {testi.ambizione(g)} ({testi.numero(g.ambizione)}) |" in testi.scheda_giocatore(g, mondo)
    allenatore = _cerca(mondo, _stato(mercato.LIBERO, A))[0]
    assert testi.scheda_della_riga(allenatore, mondo) == testi.scheda_allenatore(allenatore.persona, mondo)
    assert testi.scheda_della_riga(None, mondo) == testi.ELENCO_VUOTO_SENZA_SCHEDA
    assert testi.mosse_finite(mia) == "Per oggi Pat-Bologna ha finito le mosse di mercato."
    assert testi.domanda_sostituzione_preset("Giovani") == "Esiste già il preset Giovani: sostituirne i filtri con questi?"
    assert testi.domanda_eliminazione_preset("Giovani").startswith("Eliminare il preset Giovani? Le porte che lo riaprivano")
    assert testi.domanda_azzera_le_regole(3) == "Togliere tutte le 3 regole? Per toglierne una sola, Canc sull'elenco delle regole."
    assert testi.esito_preset_salvato("Giovani", sostituito=True) == "Preset Giovani: filtri sostituiti con quelli attuali."
    assert testi.esito_preset_eliminato("Giovani") == "Preset eliminato: Giovani."
    assert testi.esito_preset_spostato("Giovani", 1, 3) == "Preset Giovani spostato al posto 1 di 3 fra i tuoi."
    for testo in (testi.NESSUNA_REGOLA, testi.NESSUN_PRESET, testi.ELENCO_VUOTO_SENZA_SCHEDA, testi.NESSUN_VALORE):
        _accessibile(testo)
    # Le domande delle offerte valgono anche sulla riga della finestra, come sul candidato del mercato di prima.
    in_vendita = _riga(mondo, 10)
    assert testi.domanda_acquisto(in_vendita, mia, mondo).startswith(f"Comprare {testi.nome_completo(in_vendita.persona)} da {in_vendita.polisportiva.nome} per 3.000 euro?")
    del_computer = _riga(mondo, 11)
    assert testi.domanda_offerta_d_acquisto(del_computer, 900, mia, mondo).startswith(f"Offrire 900 euro a {del_computer.polisportiva.nome} per {testi.nome_completo(del_computer.persona)}?")
    libero = _cerca(mondo, _stato(mercato.LIBERO))[0]
    assert testi.domanda_ingaggio(libero, 450, 50.0, mia, mondo).startswith(f"Offrire a {testi.nome_completo(libero.persona)} un ingaggio di 450 euro, per tesserarsi con Pat-Bologna?")


# Il salvataggio, formato 10, attraverso l'archivio: i preset e le porte nella forma delle regole.

def _a_mano(m):
    """Filtri fatti a mano con una regola per quasi ogni tipo e operatore, tre alternative e i due bersagli."""
    return _filtri(
        _stato(mercato.SUL_MERCATO), _regola(G, "nome", "contiene", "ros"), _regola(G, "sesso", "uguale", "f"), _regola(G, "classe", "migliore_uguale", 40),
        _regola(G, "eta", "minore_uguale", 30), _regola(G, "costo", "minore_uguale", 5000), _regola(G, "disponibile", "uguale", True),
        _stato(mercato.RITIRATO, collegamento=O), _regola(G, "regione", "uguale", "Lombardia"), _regola(G, "provincia", "diverso", "Milano"),
        _regola(G, "comune", "non_contiene", "mil"), _regola(G, "polisportiva", "manca", None), _regola(G, "indole", "uguale", m.giocatori[3].indole),
        _regola(G, "mancino", "uguale", True), _regola(G, "valore", "maggiore", 120.5), _regola(G, "stipendio", "presente", None),
        _regola(G, "mesi_contratto", "minore", 12), _regola(G, "bomba_base", "maggiore_uguale", 10.5), _regola(G, "ambizione", "minore", 50.0),
        _stato(mercato.CAPO, A, O), _regola(A, "tipo", "uguale", staff.EX), _regola(A, "visus", "diverso", staff.VEDENTE),
        _regola(A, "stipendio", "minore_uguale", 2000), _regola(A, "gloria_richiesta", "maggiore", 100), ordine="bomba_base")


@pytest.fixture
def scritti(monkeypatch):
    """Le righe che il registro degli errori riceve."""
    righe = []
    monkeypatch.setattr(registro, "scrivi", righe.append)
    return righe


def _con_i_preset(m):
    """Il mondo con due preset di Gabriele, il 2 e il 3 dopo che l'1 è stato eliminato, e una porta per ogni voce della casella."""
    fdr = mercato.filtri_di_ricerca_del_mondo(m)
    mercato.salva_preset(fdr, "Da togliere", _filtri(_stato(mercato.LIBERO)))
    mercato.salva_preset(fdr, "Donne libere", _filtri(_stato(mercato.LIBERO), _regola(G, "sesso", "uguale", "f"), _regola(G, "eta", "minore_uguale", 25)))
    mercato.salva_preset(fdr, "Allenatori vedenti", _filtri(_stato(mercato.LIBERO, A), _regola(A, "visus", "uguale", staff.VEDENTE),
                                                            _stato(mercato.CAPO, A, O), ordine="eta_anziano"))
    mercato.elimina_preset(fdr, 1)
    mercato.ricorda_i_preset(m, fdr)
    mercato.ricorda_la_porta(m, "mercato", mercato.StatoDellaPorta(2, _filtri(_stato(mercato.LIBERO)), mercato.Preparazione(E, G, "nome", "contiene", "ros")))
    mercato.ricorda_la_porta(m, "allenatori", mercato.StatoDellaPorta(3, _filtri(_stato(mercato.TUO, A)), mercato.Preparazione(O, A, "visus", "uguale", None)))
    mercato.ricorda_la_porta(m, "ricerca", mercato.StatoDellaPorta(None, _a_mano(m), mercato.Preparazione(E, G, "eta", "minore", "2.5")))
    mercato.ricorda_la_porta(m, "amichevole", mercato.StatoDellaPorta("piu_forti", _filtri(_stato(mercato.TUO)), mercato.preparazione_di_serie("amichevole")))
    return m


def test_preset_e_porte_vanno_e_tornano_dal_salvataggio(mondo, cartella_di_prova, scritti):
    _con_i_preset(mondo)
    assert archivio.salva(mondo)
    letto = archivio.leggi(cartella_di_prova / FILE_MONDO)
    blocco = letto["mondo"]["filtri_di_ricerca"]
    assert letto["formato"] == archivio.FORMATO == 10 and set(blocco) == {"preset", "prossimo_preset", "porte"} and set(blocco["porte"]) == set(mercato.PORTE)
    assert [(p["numero"], p["nome"]) for p in blocco["preset"]] == [(2, "Donne libere"), (3, "Allenatori vedenti")] and blocco["prossimo_preset"] == 4
    assert {porta: stato["scelta"] for porta, stato in blocco["porte"].items()} == {"mercato": 2, "allenatori": 3, "ricerca": None, "amichevole": "piu_forti"}
    assert all(set(stato) == {"scelta", "attuali", "preparazione"} for stato in blocco["porte"].values())
    ricaricato = Mondo()
    archivio.carica(ricaricato)
    assert ricaricato.filtri_di_ricerca == mondo.filtri_di_ricerca and scritti == []
    ricerca = mercato.stato_della_porta(ricaricato, "ricerca")
    assert ricerca.attuali == _a_mano(mondo) and ricerca.preparazione == mercato.Preparazione(E, G, "eta", "minore", "2.5")
    assert mercato.filtri_della_voce(ricaricato.filtri_di_ricerca, 3, ricerca.attuali).ordine == "eta_anziano"


def test_un_mondo_del_formato_9_riceve_i_filtri_di_serie(mondo, cartella_di_prova, scritti):
    _con_i_preset(mondo)
    vecchio = archivio.componi(mondo)
    vecchio["formato"] = 9
    del vecchio["mondo"]["filtri_di_ricerca"]
    aggiornato = copy.deepcopy(vecchio)
    archivio.MIGRAZIONI[9](aggiornato)
    # La migrazione aggiunge soltanto i filtri di serie, dalla costante storica nella forma delle regole, e nient'altro cambia.
    assert aggiornato["formato"] == 10 and aggiornato["mondo"].pop("filtri_di_ricerca") == archivio.filtri_di_ricerca_del_formato_10()
    assert aggiornato["mondo"] == vecchio["mondo"]
    # Finché il formato è 10, la costante storica e i filtri di serie di oggi coincidono; ogni volta è un documento nuovo.
    if archivio.FORMATO == 10:
        assert archivio.filtri_di_ricerca_del_formato_10() == mercato.filtri_di_ricerca_a_dizionario(mercato.filtri_di_ricerca_di_serie())
    primo = archivio.filtri_di_ricerca_del_formato_10()
    primo["preset"].append({"numero": 1})
    primo["porte"]["mercato"]["attuali"]["regole"].append({"collegamento": "o"})
    secondo = archivio.filtri_di_ricerca_del_formato_10()
    assert secondo["preset"] == [] and len(secondo["porte"]["mercato"]["attuali"]["regole"]) == 1
    percorso = cartella_di_prova / FILE_MONDO
    with gzip.open(percorso, "wt", encoding="utf-8") as f:
        f.write(json.dumps({**vecchio, "firma": archivio.firma(vecchio)}))
    ricaricato = Mondo()
    archivio.carica(ricaricato)
    assert ricaricato.filtri_di_ricerca == mercato.filtri_di_ricerca_di_serie() and scritti == []
    assert archivio.salva(ricaricato) and archivio.leggi(percorso)["formato"] == archivio.FORMATO
    assert set(archivio.MIGRAZIONI) == set(range(1, archivio.FORMATO))


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
        {**buono, "numero": 13, "nome": "A schede", "filtri": {"liberi": True}, "volante": 1},
        "un preset che non è un dizionario",
    ]
    blocco["prossimo_preset"] = 2
    nuovo = Mondo()
    archivio.costruisci(contenuto, nuovo)
    fdr = nuovo.filtri_di_ricerca
    assert [(p.numero, p.nome) for p in fdr.preset] == [
        (1, "Donne libere"), (14, "DONNE LIBERE (2)"), (15, "Preset 15"), (5, "Spazi dentro"), (6, "x" * 50), (8, "I capi allenatori migliori (2)"),
        (9, "y" * 50), (12, "Y" * 46 + " (2)"), (13, "A schede")]
    assert fdr.prossimo_preset == 16 and all(len(p.nome) <= 50 for p in fdr.preset)
    assert all(p.filtri == mercato.filtri_da_dizionario(buono["filtri"]) for p in fdr.preset[:-1])
    assert fdr.preset[-1].filtri == mercato.filtri_di_serie("tutti_in_attivita")
    # Le porte si leggono dopo i preset: il 2 non c'è più, e la porta degli allenatori, che riapriva il 3, nemmeno.
    assert fdr.porte["mercato"].scelta == "mercato" and fdr.porte["allenatori"].scelta == "allenatori_liberi"
    problemi = [riga.split(" Il dato originale, in JSON: ")[0].removeprefix("Lettura del mondo, filtri di Mercato e ricerca. ") for riga in scritti]
    assert len(problemi) == 14 and problemi[:9] == [
        "Il preset al posto 10 della casella non si legge. Si toglie.",
        "Il preset al posto 2 della casella ha lo stesso numero di un preset di prima, 1. Riceve il numero 14.",
        "Il nome del preset numero 14, \"DONNE LIBERE\", lo usa già un'altra voce della casella. Diventa DONNE LIBERE (2).",
        "Il preset al posto 3 della casella non ha un numero valido, \"7\". Riceve il numero 15.",
        "Al preset numero 15 manca il nome. Si chiama Preset 15.",
        "Il nome del preset numero 5, \"  Spazi\\tdentro  \", ha degli spazi in testa o in coda e ha dei caratteri di controllo. Diventa Spazi dentro.",
        f"Il nome del preset numero 6, \"{'x' * 60}\", supera i 50 caratteri. Diventa {'x' * 50}.",
        "Il nome del preset numero 8, \"I capi allenatori migliori\", lo usa già un'altra voce della casella. Diventa I capi allenatori migliori (2).",
        f"Il nome del preset numero 12, \"{'Y' * 50}\", lo usa già un'altra voce della casella. Diventa {'Y' * 46} (2).",
    ]
    assert problemi[9] == ("I filtri del preset A schede, numero 13, non sono validi: sono nella forma di prima del costruttore di regole, con un campo "
                           "per ogni filtro. Diventano quelli del preset di serie Tutti in attività, per numero.")
    assert problemi[10:] == [
        "Il preset A schede, numero 13, ha dei dati che questa versione non conosce: volante. Si tolgono.",
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


def test_il_salvataggio_non_scrive_filtri_che_non_si_rileggerebbero(mondo, cartella_di_prova, scritti):
    assert archivio.salva(mondo)
    percorso = cartella_di_prova / FILE_MONDO
    prima = percorso.read_bytes()
    # Filtri messi nel mondo senza ricorda_la_porta: il salvataggio si rifiuta, e quello di prima resta com'era.
    mondo.filtri_di_ricerca = mercato.filtri_di_ricerca_di_serie()
    mondo.filtri_di_ricerca.porte["mercato"] = mercato.StatoDellaPorta(None, _filtri(_regola(G, "sesso", "uguale", "")), mercato.preparazione_di_serie("mercato"))
    messaggi = []
    mondo.notifica = messaggi.append
    assert archivio.salva(mondo) is False
    assert percorso.read_bytes() == prima
    assert messaggi == ["Salvataggio non riuscito: I filtri attuali della porta Mercato, Ctrl+K, non sono validi: la regola 1 non va: il valore \"\" non va per "
                        "sesso, è. Il salvataggio precedente è rimasto com'era."]
    ricaricato = Mondo()
    archivio.carica(ricaricato)
    assert ricaricato.filtri_di_ricerca == mercato.filtri_di_ricerca_di_serie() and scritti == []


def test_ogni_stato_che_il_motore_produce_si_salva_e_si_rilegge(mondo, cartella_di_prova, scritti):
    a_mano = _a_mano(mondo)
    fdr = mercato.filtri_di_ricerca_del_mondo(mondo)
    # Un preset per ogni preset di serie, per i filtri fatti a mano e per tre loro pezzi.
    for chiave, nome in mercato.PRESET_DI_SERIE:
        mercato.salva_preset(fdr, f"Come {nome}"[:50], mercato.filtri_di_serie(chiave))
    mercato.salva_preset(fdr, "A mano", a_mano)
    for inizio, fine in ((0, 7), (7, 19), (19, len(a_mano.regole))):
        mercato.salva_preset(fdr, f"A mano, regole da {inizio + 1} a {fine}", mercato.Filtri(mercato.con_la_prima_e(a_mano.regole[inizio:fine]), "classe"))
    mercato.rinomina_preset(fdr, 2, "Rinominato")
    mercato.sposta_preset(fdr, 3, -1)
    mercato.elimina_preset(fdr, 4)
    mercato.ricorda_i_preset(mondo, fdr)
    scelte = [None, *(chiave for chiave, _nome in mercato.PRESET_DI_SERIE), *(p.numero for p in fdr.preset)]
    preparazioni = [mercato.Preparazione(E, G, "nome", "contiene", "ros"), mercato.Preparazione(O, A, "visus", "uguale", None),
                    mercato.Preparazione(E, G, "eta", "minore", "2.5"), mercato.Preparazione(O, G, "mancino", "uguale", False)]
    # Quattro porte per salvataggio, ciascuna con una scelta diversa, i filtri attuali fatti a mano o di serie, e una preparazione.
    for primo in range(0, len(scelte), len(mercato.PORTE)):
        gruppo = dict(zip(mercato.PORTE, scelte[primo:primo + len(mercato.PORTE)], strict=False))
        for posto, (porta, scelta) in enumerate(gruppo.items()):
            attuali = a_mano if posto % 2 == 0 else mercato.filtri_di_serie(mercato.PRESET_DELLA_PORTA[porta])
            mercato.ricorda_la_porta(mondo, porta, mercato.StatoDellaPorta(scelta, attuali, preparazioni[posto]))
        assert archivio.salva(mondo)
        ricaricato = Mondo()
        archivio.carica(ricaricato)
        assert ricaricato.filtri_di_ricerca == mondo.filtri_di_ricerca and scritti == []


def test_svuota_il_valore_riporta_gli_operatori_senza_valore():
    # Dal controllo finale del 24 ottobre 2026: con "non ha il dato" o "ha il dato" la regola in preparazione contava
    # ancora dopo Aggiungi regola, un preset o la riapertura, perché svuotare il valore non la toglieva.
    for operatore in ("manca", "presente"):
        prep = mercato.Preparazione(caratteristica="costo", operatore=operatore, valore=None)
        assert mercato.regola_pronta(prep)[0] is not None
        vuota = mercato.svuota_il_valore(prep)
        assert vuota.operatore not in ("manca", "presente") and mercato.regola_pronta(vuota) == (None, None)
    # Gli altri operatori restano, e perdono soltanto il valore.
    prep = mercato.Preparazione(caratteristica="costo", operatore="minore", valore="5000")
    vuota = mercato.svuota_il_valore(prep)
    assert vuota.operatore == "minore" and mercato.regola_pronta(vuota) == (None, None)
