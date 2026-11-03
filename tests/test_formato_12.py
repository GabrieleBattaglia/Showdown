"""
Le prove del formato 12 del salvataggio, con le scelte di Gabriele del 3 novembre 2026 che valgono come D40, dopo la misura
della rivendita a 36 mesi: la rampa del prezzo parte da quello che la polisportiva ha pagato alla firma.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Il campo nuovo, pagato_alla_firma, in ogni giocatore: _entra lo scrive, _lascia lo svuota, chi nasce o entra senza pagare lo
ha vuoto, e il computer lo ricorda quando tessera un libero e quando ne prende uno al posto di un tesserato debole. Va e torna
dal salvataggio, e un valore che non è un intero né il vuoto si rifiuta. La migrazione dall'11, che aggiunge soltanto; un
mondo del formato 10, come quello di Gabriele, che arriva al 12 in un caricamento solo, con la copia di sicurezza nel formato
nuovo; e un mondo dell'11, che sa il giorno della firma ma non quello pagato, dove la rampa parte dall'ingaggio chiesto oggi.
E il formato più recente, ora dal 13, che ferma il caricamento senza ripiego, senza copie messe da parte e senza toccare i
file: le prove sono quelle del formato 11, coi numeri di oggi.
"""

import datetime
import gzip
import json
import os
import random

import pytest
from aiuti_formati import CAMPI_DEL_FORMATO_12, al_formato_10, al_formato_11

import archivio
import cartella_del_mondo as cdm
import contratti
import economia
import mondo as modulo_mondo
from costanti import FILE_MONDO, FILE_MONDO_COPIA, MESI_DELLA_RAMPA
from modelli import Giocatore, Polisportiva
from mondo import Mondo

INIZIO = datetime.datetime(2026, 10, 24, 9, 0)
INIZIO_UTC = datetime.datetime(2026, 10, 24, 7, 0, tzinfo=datetime.UTC)
# L'ingaggio di partenza dei tesserati di prova: a ognuno si aggiunge il suo numero, così ogni cifra è diversa.
PAGATO = 300


def _mondo_con_due_polisportive():
    """
    Un mondo piccolo come quello di Gabriele: due polisportive dell'utente e una del computer. I tesserati di Magnavacca e del
    computer hanno pagato un ingaggio, PAGATO o il doppio più il loro numero; quelli di TuratiBoys sono entrati senza pagare.
    """
    stato = random.getstate()
    random.seed(2611)
    try:
        m = Mondo()
        m.datetime_corrente_simulazione = INIZIO
        m.datetime_ultimo_run_reale = INIZIO_UTC
        m.crea_giocatori_casuali(40, INIZIO, annuncia=False)
        cpu = m.polisportive[m.crea_polisportiva_cpu(INIZIO)]
        prima, seconda = Polisportiva("Magnavacca", None, INIZIO), Polisportiva("TuratiBoys", None, INIZIO)
        for poli in (prima, seconda):
            m.polisportive[poli.nome] = poli
        m.miapolisportiva_attiva = prima
        attivi = sorted(m.giocatori)
        for gid in attivi[:5]:
            m._tessera(prima, m.giocatori[gid], ingaggio=PAGATO + gid)
        for gid in attivi[5:9]:
            m._entra(seconda, m.giocatori[gid])
        for gid in attivi[9:15]:
            m._tessera(cpu, m.giocatori[gid], ingaggio=2 * PAGATO + gid)
        m.aggiorna_stato_polisportive(annuncia=False)
    finally:
        random.setstate(stato)
    return m


def _scrivi_documento(percorso, documento):
    """Un documento firmato e compresso, come lo scrive il gioco."""
    with gzip.open(percorso, "wt", encoding="utf-8") as f:
        f.write(json.dumps({**documento, "firma": archivio.firma(documento)}))


def _formato_del_file(percorso):
    """Il numero di formato scritto nel file, senza aggiornarlo come fa leggi."""
    return json.loads(gzip.decompress(percorso.read_bytes()).decode("utf-8"))["formato"]


def _istantanea(cartella):
    """Tutti i file della cartella coi loro byte, sottocartelle comprese."""
    return {os.path.relpath(os.path.join(radice, nome), cartella): open(os.path.join(radice, nome), "rb").read()
            for radice, _cartelle, nomi in os.walk(cartella) for nome in nomi}


# Il campo nuovo.

def test_quello_pagato_si_scrive_entrando_e_si_svuota_uscendo():
    m = _mondo_con_due_polisportive()
    prima, seconda = m.polisportive["Magnavacca"], m.polisportive["TuratiBoys"]
    cpu = next(p for p in m.polisportive.values() if p.is_cpu_controlled)
    # _tessera passa l'ingaggio, anche per il computer; chi entra senza pagare lo ha vuoto, e così chi è libero.
    assert {gid: m.giocatori[gid].pagato_alla_firma for gid in prima.tesserati} == {gid: PAGATO + gid for gid in prima.tesserati}
    assert {gid: m.giocatori[gid].pagato_alla_firma for gid in cpu.tesserati} == {gid: 2 * PAGATO + gid for gid in cpu.tesserati}
    assert len(seconda.tesserati) == 4 and all(m.giocatori[gid].pagato_alla_firma is None for gid in seconda.tesserati)
    liberi = [g for g in m.giocatori.values() if g.appartenenza == "*"]
    assert liberi and all(g.pagato_alla_firma is None for g in liberi)
    # Uscendo si svuota, insieme al giorno della firma.
    g = m.giocatori[prima.tesserati[0]]
    m._lascia(prima, g)
    assert g.pagato_alla_firma is None and g.tesserato_dal is None and g.appartenenza == "*"
    # Zero euro è una cifra, non il vuoto; chi rientra senza pagare lo ha di nuovo vuoto.
    m._entra(seconda, g, pagato=0)
    assert g.pagato_alla_firma == 0
    m._lascia(seconda, g)
    m._entra(prima, g)
    assert g.pagato_alla_firma is None and g.tesserato_dal == INIZIO
    # Chi nasce è libero, e non ha pagato niente.
    stato = random.getstate()
    try:
        assert Giocatore(999, INIZIO).pagato_alla_firma is None
    finally:
        random.setstate(stato)


def test_il_computer_ricorda_quello_che_paga(monkeypatch):
    # Ogni libero accetta: il computer tessera chi può, e a rosa piena prende il libero più forte al posto del più debole.
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: True)
    stato = random.getstate()
    random.seed(909)
    try:
        m = Mondo()
        m.datetime_corrente_simulazione = INIZIO
        m.crea_giocatori_casuali(40, INIZIO, annuncia=False)
    finally:
        random.setstate(stato)
    cpu = m.polisportive[m.crea_polisportiva_cpu(INIZIO)]
    cpu.gloria, cpu.cassa = 10_000, 1_000_000
    tesserati, _svincolati, _comprati = m._esegui_logica_cpu_polisportive(INIZIO)
    assert tesserati > 0 and len(cpu.tesserati) == tesserati
    pagati = [m.giocatori[gid].pagato_alla_firma for gid in cpu.tesserati]
    assert None not in pagati and sum(pagati) == cpu.conti_del_mese["ingaggi"] > 0
    # Lo scambio: una rosa piena di deboli, entrati senza pagare, e il libero più forte che prende il posto del primo.
    altra = m.polisportive[m.crea_polisportiva_cpu(INIZIO)]
    altra.gloria, altra.cassa = 10_000, 1_000_000
    liberi = sorted(g.id for g in m.giocatori.values() if g.appartenenza == "*")
    for gid in liberi[:15]:
        m._entra(altra, m.giocatori[gid])
        m.giocatori[gid].indice_collettivo_valore = 0.1
    forte = max((g for g in m.giocatori.values() if g.appartenenza == "*"), key=lambda g: g.indice_collettivo_valore)
    cpu.cassa = 0
    m.datetime_corrente_simulazione = dopo = INIZIO + datetime.timedelta(days=1)
    for p in m.polisportive.values():
        p.movimenti_oggi = 0
    assert m._esegui_logica_cpu_polisportive(dopo)[1] == 1
    assert forte.appartenenza == altra.nome and forte.pagato_alla_firma == altra.conti_del_mese["ingaggi"] > 0


def test_quello_pagato_va_e_torna_dal_salvataggio(cartella_di_prova):
    m = _mondo_con_due_polisportive()
    zero = m.giocatori[m.polisportive["TuratiBoys"].tesserati[0]]
    zero.pagato_alla_firma = 0
    assert archivio.salva(m)
    letto = archivio.leggi(cartella_di_prova / FILE_MONDO)
    assert letto["formato"] == archivio.FORMATO == 12
    scritti = {g["id"]: g["pagato_alla_firma"] for g in letto["mondo"]["giocatori"]}
    assert scritti == {gid: g.pagato_alla_firma for gid, g in m.giocatori.items()}
    assert scritti[zero.id] == 0 and None in scritti.values() and PAGATO + m.polisportive["Magnavacca"].tesserati[0] in scritti.values()
    ricaricato = Mondo()
    assert archivio.carica(ricaricato) == archivio.CARICATO and ricaricato.formato_letto == 12
    for gid, originale in m.giocatori.items():
        assert vars(ricaricato.giocatori[gid]) == vars(originale)


@pytest.mark.parametrize("valore", ["300", 300.0, True, [300]])
def test_quello_pagato_non_valido_si_rifiuta(valore):
    contenuto = archivio.componi(_mondo_con_due_polisportive())
    voce = contenuto["mondo"]["giocatori"][0]
    voce["pagato_alla_firma"] = valore
    vuoto = Mondo()
    with pytest.raises(archivio.ErroreSalvataggio, match="pagato_alla_firma"):
        archivio.costruisci(contenuto, vuoto)
    assert vuoto.giocatori == {}
    # Il formato 12 lo vuole in ogni giocatore: anche senza, il salvataggio si rifiuta.
    del voce["pagato_alla_firma"]
    with pytest.raises(archivio.ErroreSalvataggio, match="pagato_alla_firma"):
        archivio.costruisci(contenuto, vuoto)


# Le migrazioni.

def test_la_migrazione_dall_11_aggiunge_soltanto():
    m = _mondo_con_due_polisportive()
    vecchio = al_formato_11(archivio.componi(m))
    assert vecchio["formato"] == 11 and all("pagato_alla_firma" not in g for g in vecchio["mondo"]["giocatori"])
    aggiornato = json.loads(json.dumps(vecchio))
    archivio.MIGRAZIONI[11](aggiornato)
    assert aggiornato["formato"] == archivio.FORMATO == 12
    # Nessuno ricorda quello che ha pagato: vuoto per tutti, anche per chi ha il giorno della firma.
    assert all(g["pagato_alla_firma"] is None for g in aggiornato["mondo"]["giocatori"])
    assert any(g["tesserato_dal"] is not None for g in aggiornato["mondo"]["giocatori"])
    # Tolto il campo nuovo, il documento è quello di prima.
    for g in aggiornato["mondo"]["giocatori"]:
        for campo in CAMPI_DEL_FORMATO_12:
            del g[campo]
    assert aggiornato["mondo"] == vecchio["mondo"]
    assert set(archivio.MIGRAZIONI) == set(range(1, archivio.FORMATO))


def test_un_mondo_del_10_arriva_al_12_in_un_caricamento(cartella_di_prova):
    # Come quello di Gabriele: il salvataggio e la copia del formato 10, che passano per l'11 e per il 12 in un caricamento solo.
    m = _mondo_con_due_polisportive()
    principale, copia = cartella_di_prova / FILE_MONDO, cartella_di_prova / FILE_MONDO_COPIA
    _scrivi_documento(copia, al_formato_10(archivio.componi(m)))
    _scrivi_documento(principale, al_formato_10(archivio.componi(m)))
    assert _formato_del_file(principale) == _formato_del_file(copia) == 10
    messaggi = []
    ricaricato = Mondo(notifica=messaggi.append)
    assert archivio.carica(ricaricato) == archivio.CARICATO and ricaricato.formato_letto == 10 and ricaricato.fondazioni_di_sempre == 2
    assert all(g.tesserato_dal is None and g.pagato_alla_firma is None for g in ricaricato.giocatori.values())
    # I tuoi tesserati hanno firmato prima del formato 11: il computer li paga subito al tetto pieno, come prima.
    tuoi = [(g, ricaricato.polisportive[g.appartenenza]) for g in ricaricato.giocatori.values() if g.appartenenza in ("Magnavacca", "TuratiBoys")]
    assert len(tuoi) == 9
    for g, poli in tuoi:
        assert economia.tetto_di_rivendita(g, poli, INIZIO) == economia.tetto_pieno_di_rivendita(g, poli, INIZIO)
        assert economia.rivendita_piena_dal(g, poli, INIZIO) is None
    # Il primo salvataggio scrive il formato 12 nel salvataggio e nella copia.
    assert archivio.salva(ricaricato) and ricaricato.formato_letto == archivio.FORMATO == 12
    assert _formato_del_file(principale) == _formato_del_file(copia) == 12 and principale.read_bytes() == copia.read_bytes()
    riletto = Mondo()
    assert archivio.carica(riletto) == archivio.CARICATO and riletto.formato_letto == 12
    assert all(g.pagato_alla_firma is None for g in riletto.giocatori.values())


def test_chi_ha_firmato_nel_formato_11_parte_dall_ingaggio_di_oggi(cartella_di_prova):
    # Un mondo dell'11 sa il giorno della firma, ma non quello che si è pagato: la rampa parte dall'ingaggio che il giocatore
    # chiede oggi, la regola di prima del 3 novembre 2026.
    m = _mondo_con_due_polisportive()
    _scrivi_documento(cartella_di_prova / FILE_MONDO, al_formato_11(archivio.componi(m)))
    ricaricato = Mondo()
    assert archivio.carica(ricaricato) == archivio.CARICATO and ricaricato.formato_letto == 11
    poli = ricaricato.polisportive["Magnavacca"]
    rosa = [ricaricato.giocatori[gid] for gid in poli.tesserati]
    assert len(rosa) == 5 and all(g.tesserato_dal == INIZIO and g.pagato_alla_firma is None for g in rosa)
    fine = contratti.stesso_giorno_dopo(INIZIO, MESI_DELLA_RAMPA)
    con_la_rampa = 0
    for g in rosa:
        pieno = economia.tetto_pieno_di_rivendita(g, poli, INIZIO)
        chiesto = economia.ingaggio_richiesto(g, poli)
        assert economia.tetto_di_rivendita(g, poli, INIZIO) == min(chiesto, pieno)
        if chiesto < pieno:
            con_la_rampa += 1
            assert economia.rivendita_piena_dal(g, poli, INIZIO) == fine
        # Col campo del formato 12 la stessa rampa parte da quello pagato.
        g.pagato_alla_firma = PAGATO + g.id
        assert economia.tetto_di_rivendita(g, poli, INIZIO) == min(PAGATO + g.id, pieno)
    assert con_la_rampa > 0


# Il formato più recente, dal 13.

def _mondo_del_formato_13(percorso):
    """Un salvataggio vero, firmato, di un MESS col formato 13, che questa versione non sa leggere."""
    contenuto = archivio.componi(_mondo_con_due_polisportive())
    contenuto["formato"] = archivio.FORMATO + 1
    _scrivi_documento(percorso, contenuto)


def test_il_formato_13_ferma_il_caricamento_senza_toccare_niente(cartella_di_prova):
    # Anche con la copia buona accanto: niente ripiego, niente copie messe da parte, niente blocco dei salvataggi.
    buono = _mondo_con_due_polisportive()
    assert archivio.salva(buono) and archivio.salva(buono)
    _mondo_del_formato_13(cartella_di_prova / FILE_MONDO)
    prima = _istantanea(cartella_di_prova)
    messaggi = []
    mondo = Mondo(notifica=messaggi.append)
    with pytest.raises(archivio.FormatoPiuRecente) as errore:
        archivio.carica(mondo)
    assert (errore.value.formato, errore.value.massimo) == (13, 12) and "con il formato 13" in str(errore.value)
    assert not errore.value.della_copia and errore.value.motivo is None
    assert _istantanea(cartella_di_prova) == prima and set(prima) == {FILE_MONDO, FILE_MONDO_COPIA}
    assert not mondo.salvataggio_bloccato and mondo.giocatori == {} and messaggi == []


def test_il_formato_13_con_un_altra_firma_e_piu_recente_non_rovinato(cartella_di_prova):
    # Un MESS futuro che cambiasse la firma, o che non la scrivesse più, non deve far tornare alla copia di sicurezza.
    buono = _mondo_con_due_polisportive()
    assert archivio.salva(buono) and archivio.salva(buono)
    principale = cartella_di_prova / FILE_MONDO
    contenuto = archivio.componi(_mondo_con_due_polisportive())
    contenuto["formato"] = archivio.FORMATO + 1
    for firma in ("una firma calcolata in un altro modo", None):
        documento = contenuto if firma is None else {**contenuto, "firma": firma}
        with gzip.open(principale, "wt", encoding="utf-8") as f:
            f.write(json.dumps(documento))
        prima = _istantanea(cartella_di_prova)
        with pytest.raises(archivio.FormatoPiuRecente) as errore:
            archivio.carica(Mondo())
        assert errore.value.formato == 13 and not errore.value.della_copia
        assert _istantanea(cartella_di_prova) == prima
    # Il formato di oggi con la firma sbagliata resta un file rovinato, e così un altro programma col formato 13.
    with gzip.open(principale, "wt", encoding="utf-8") as f:
        f.write(json.dumps({**archivio.componi(buono), "firma": "sbagliata"}))
    with pytest.raises(archivio.ErroreSalvataggio, match="la firma non corrisponde"):
        archivio.leggi(principale)
    with gzip.open(principale, "wt", encoding="utf-8") as f:
        f.write(json.dumps({**contenuto, "applicazione": "Altro", "firma": "sbagliata"}))
    with pytest.raises(archivio.ErroreSalvataggio, match="la firma non corrisponde"):
        archivio.leggi(principale)


def test_anche_una_copia_del_formato_13_ferma_il_caricamento(cartella_di_prova):
    (cartella_di_prova / FILE_MONDO).write_bytes(b"rovinato")
    _mondo_del_formato_13(cartella_di_prova / FILE_MONDO_COPIA)
    prima = _istantanea(cartella_di_prova)
    mondo = Mondo()
    with pytest.raises(archivio.FormatoPiuRecente) as errore:
        archivio.carica(mondo, metti_da_parte=True)
    assert _istantanea(cartella_di_prova) == prima and not mondo.salvataggio_bloccato
    assert errore.value.della_copia and errore.value.motivo.startswith("il file non è un JSON valido")
    os.remove(cartella_di_prova / FILE_MONDO)
    with pytest.raises(archivio.FormatoPiuRecente) as errore:
        archivio.carica(Mondo())
    assert errore.value.della_copia and errore.value.motivo == f"il file {FILE_MONDO} non c'è"


def test_la_data_di_un_mondo_del_formato_13_non_guarda_la_copia(cartella_di_prova):
    # Come il caricamento, che non ripiega: la copia buona non rende usabile quel mondo.
    buono = _mondo_con_due_polisportive()
    assert archivio.salva(buono) and archivio.salva(buono)
    _mondo_del_formato_13(cartella_di_prova / FILE_MONDO)
    data, dal_salvataggio, errore = cdm.salvato(cartella_di_prova)
    assert data is not None and not dal_salvataggio
    assert errore == "il file viene da una versione più recente del gioco, con il formato 13, mentre questa legge fino al formato 12"
