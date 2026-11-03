"""
Le prove del formato 11 del salvataggio, decisione D40 del 2 novembre 2026, terza tranche dei rimedi ai trucchi fra
le polisportive dell'utente.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
I tre campi nuovi: il contatore delle fondazioni dell'utente nel mondo, il giorno della firma in ogni giocatore, che
_entra scrive per tutti e _lascia cancella, e il giorno fino al quale un allenatore non firma con l'utente. La
migrazione dal 10, che aggiunge soltanto, su un mondo piccolo come quello di Gabriele, con due polisportive sue. La
copia di sicurezza, che al primo salvataggio dopo la migrazione si scrive anche lei nel formato nuovo, perché una
macchina col codice di prima non ripieghi su una copia del 10 coprendo il mondo. E il formato più recente, dal 12, che
ferma il caricamento senza ripiego, senza copie messe da parte e senza toccare i file.
Dalla quinta tranche di D40 la migrazione aggiunge anche le due voci dei conti di Sposta fondi, a zero, nel mese in corso e
nei bilanci. Dal 3 novembre 2026 l'errore del formato più recente dice se è della copia di sicurezza, e perché il salvataggio
non si usava. Con le note 3 e 5 della revisione dei rimedi: il messaggio della copia nuova che non si scrive dice che il
salvataggio la aspetta, e un formato più recente con un'altra firma, o senza firma, risulta più recente e non rovinato.
"""

import datetime
import gzip
import json
import os
import random

import pytest
from aiuti_formati import CAMPI_ALLENATORE_DEL_FORMATO_11, CAMPI_DEL_FORMATO_11, CAMPI_MONDO_DEL_FORMATO_11, VOCI_DEL_FORMATO_11, al_formato_10

import archivio
import cartella_del_mondo as cdm
from costanti import FILE_MONDO, FILE_MONDO_COPIA
from modelli import Polisportiva, conti_vuoti
from mondo import Mondo

INIZIO = datetime.datetime(2026, 10, 24, 9, 0)
INIZIO_UTC = datetime.datetime(2026, 10, 24, 7, 0, tzinfo=datetime.UTC)


def _mondo_con_due_polisportive():
    """Un mondo piccolo come quello di Gabriele: due polisportive dell'utente e una del computer, coi loro tesserati, e tre allenatori."""
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
        for poli, gruppo in ((prima, attivi[:5]), (seconda, attivi[5:9]), (cpu, attivi[9:15])):
            for gid in gruppo:
                m._entra(poli, m.giocatori[gid])
        for seme in range(3):
            m._nasce_un_allenatore(INIZIO, random.Random(seme))
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


# I campi nuovi.

def test_la_firma_si_scrive_entrando_e_si_cancella_uscendo():
    m = _mondo_con_due_polisportive()
    prima, cpu = m.polisportive["Magnavacca"], next(p for p in m.polisportive.values() if p.is_cpu_controlled)
    # _entra la scrive per tutti, anche per il computer, col giorno di oggi o con quello dato.
    assert all(m.giocatori[gid].tesserato_dal == INIZIO for p in m.polisportive.values() for gid in p.tesserati)
    liberi = [g for g in m.giocatori.values() if g.appartenenza == "*"]
    assert liberi and all(g.tesserato_dal is None for g in liberi)
    g = m.giocatori[prima.tesserati[0]]
    m._lascia(prima, g)
    assert g.tesserato_dal is None and g.appartenenza == "*"
    dopo = INIZIO + datetime.timedelta(days=12)
    m._entra(cpu, g, dopo)
    assert g.tesserato_dal == dopo and g.appartenenza == cpu.nome
    # Senza il giorno dato, quello simulato di oggi.
    m.datetime_corrente_simulazione = oggi = INIZIO + datetime.timedelta(days=20)
    m._lascia(cpu, g)
    m._entra(prima, g)
    assert g.tesserato_dal == oggi and g.appartenenza == prima.nome
    # Chi nasce è libero, e senza firma; i nuovi allenatori nascono senza giorno di lontananza.
    assert all(a.escluso_dall_utente_fino is None for a in m.allenatori.values())
    assert m.fondazioni_di_sempre == 0


def test_i_campi_nuovi_vanno_e_tornano_dal_salvataggio(cartella_di_prova):
    m = _mondo_con_due_polisportive()
    m.fondazioni_di_sempre = 3
    g = m.giocatori[m.polisportive["TuratiBoys"].tesserati[0]]
    g.tesserato_dal = INIZIO - datetime.timedelta(days=40)
    a = next(iter(m.allenatori.values()))
    a.escluso_dall_utente_fino = INIZIO + datetime.timedelta(days=30)
    assert archivio.salva(m)
    letto = archivio.leggi(cartella_di_prova / FILE_MONDO)
    assert letto["formato"] == archivio.FORMATO == 11 and letto["mondo"]["fondazioni_di_sempre"] == 3
    ricaricato = Mondo()
    assert archivio.carica(ricaricato) == archivio.CARICATO and ricaricato.formato_letto == 11
    assert ricaricato.fondazioni_di_sempre == 3
    assert ricaricato.giocatori[g.id].tesserato_dal == INIZIO - datetime.timedelta(days=40)
    assert ricaricato.allenatori[a.numero].escluso_dall_utente_fino == INIZIO + datetime.timedelta(days=30)
    for gid, originale in m.giocatori.items():
        assert vars(ricaricato.giocatori[gid]) == vars(originale)


def test_il_contatore_si_rilegge_com_e_scritto(cartella_di_prova):
    # Il salvataggio non si ripara in silenzio: il contatore torna com'era, anche sotto le polisportive aperte, che le regole
    # delle fondazioni contano da sé. Il mondo riletto resta quello salvato, come vogliono le prove delle accelerazioni.
    m = _mondo_con_due_polisportive()
    contenuto = archivio.componi(m)
    for scritto in (0, 5):
        contenuto["mondo"]["fondazioni_di_sempre"] = scritto
        nuovo = Mondo()
        archivio.costruisci(contenuto, nuovo)
        assert nuovo.fondazioni_di_sempre == scritto


@pytest.mark.parametrize(("dove", "campo", "valore"), [
    ("mondo", "fondazioni_di_sempre", -1), ("mondo", "fondazioni_di_sempre", "2"), ("mondo", "fondazioni_di_sempre", True),
    ("giocatore", "tesserato_dal", "ieri"), ("giocatore", "tesserato_dal", 5), ("allenatore", "escluso_dall_utente_fino", "domani"),
    ("allenatore", "escluso_dall_utente_fino", []),
])
def test_i_campi_nuovi_non_validi_si_rifiutano(dove, campo, valore):
    contenuto = archivio.componi(_mondo_con_due_polisportive())
    voce = {"mondo": contenuto["mondo"], "giocatore": contenuto["mondo"]["giocatori"][0], "allenatore": contenuto["mondo"]["allenatori"][0]}[dove]
    voce[campo] = valore
    vuoto = Mondo()
    with pytest.raises(archivio.ErroreSalvataggio, match=campo):
        archivio.costruisci(contenuto, vuoto)
    assert vuoto.giocatori == {} and vuoto.fondazioni_di_sempre == 0
    del voce[campo]
    with pytest.raises(archivio.ErroreSalvataggio, match=campo):
        archivio.costruisci(contenuto, vuoto)


# La migrazione dal formato 10.

def test_la_migrazione_dal_formato_10_aggiunge_soltanto():
    m = _mondo_con_due_polisportive()
    # Un mese già chiuso, perché le voci nuove dei conti arrivino anche nei bilanci.
    m.polisportive["Magnavacca"].bilanci = [{"data": INIZIO, "cassa": 1_000, **conti_vuoti(), "sponsor": 1_500}]
    vecchio = al_formato_10(archivio.componi(m))
    aggiornato = json.loads(json.dumps(vecchio))
    archivio.MIGRAZIONI[10](aggiornato)
    assert aggiornato["formato"] == archivio.FORMATO == 11
    # Il contatore parte dalle polisportive dell'utente aperte; la firma e la lontananza restano vuote per tutti.
    assert aggiornato["mondo"]["fondazioni_di_sempre"] == 2
    assert all(g["tesserato_dal"] is None for g in aggiornato["mondo"]["giocatori"])
    assert len(aggiornato["mondo"]["allenatori"]) == 3 and all(a["escluso_dall_utente_fino"] is None for a in aggiornato["mondo"]["allenatori"])
    # Dalla quinta tranche le voci dei conti di Sposta fondi, a zero nel mese in corso e in ogni bilancio.
    polisportive = aggiornato["mondo"]["polisportive"].values()
    assert all(conti[voce] == 0 for p in polisportive for conti in (p["conti_del_mese"], *p["bilanci"]) for voce in VOCI_DEL_FORMATO_11)
    assert any(p["bilanci"] for p in polisportive)
    # Tolti i campi nuovi, il documento è quello di prima.
    for campo in CAMPI_MONDO_DEL_FORMATO_11:
        del aggiornato["mondo"][campo]
    for chi, campi in (("giocatori", CAMPI_DEL_FORMATO_11), ("allenatori", CAMPI_ALLENATORE_DEL_FORMATO_11)):
        for voce in aggiornato["mondo"][chi]:
            for campo in campi:
                del voce[campo]
    for p in polisportive:
        for conti in (p["conti_del_mese"], *p["bilanci"]):
            for voce in VOCI_DEL_FORMATO_11:
                del conti[voce]
    assert aggiornato["mondo"] == vecchio["mondo"]
    assert set(archivio.MIGRAZIONI) == set(range(1, archivio.FORMATO))


def test_un_mondo_del_7_senza_allenatori_arriva_all_11():
    # Gli allenatori di un mondo del 7 nascono al caricamento, già col campo vuoto: la migrazione dal 10 non li trova.
    m = _mondo_con_due_polisportive()
    contenuto = al_formato_10(archivio.componi(m))
    contenuto["mondo"]["allenatori"] = None
    archivio.MIGRAZIONI[10](contenuto)
    assert contenuto["mondo"]["allenatori"] is None and contenuto["mondo"]["fondazioni_di_sempre"] == 2


def test_il_salvataggio_del_formato_10_si_aggiorna_e_anche_la_copia(cartella_di_prova):
    m = _mondo_con_due_polisportive()
    principale, copia = cartella_di_prova / FILE_MONDO, cartella_di_prova / FILE_MONDO_COPIA
    # Il salvataggio e la sua copia del formato 10, diversi come dopo due salvataggi.
    _scrivi_documento(copia, al_formato_10(archivio.componi(m)))
    m.giocatori[1].punti_allenamento = 33.0
    _scrivi_documento(principale, al_formato_10(archivio.componi(m)))
    assert _formato_del_file(principale) == _formato_del_file(copia) == 10
    ricaricato = Mondo()
    assert archivio.carica(ricaricato) == archivio.CARICATO and ricaricato.formato_letto == 10
    assert ricaricato.fondazioni_di_sempre == 2 and ricaricato.giocatori[1].punti_allenamento == 33.0
    assert all(g.tesserato_dal is None for g in ricaricato.giocatori.values())
    # Il primo salvataggio scrive il mondo nuovo in tutti e due i file: una macchina col codice di prima non trova più un 10.
    assert archivio.salva(ricaricato) and ricaricato.formato_letto == 11
    assert _formato_del_file(principale) == _formato_del_file(copia) == 11
    assert principale.read_bytes() == copia.read_bytes()
    assert set(os.listdir(cartella_di_prova)) == {FILE_MONDO, FILE_MONDO_COPIA}
    # Dal secondo la copia torna a essere il salvataggio precedente.
    primo = principale.read_bytes()
    ricaricato.giocatori[1].punti_allenamento = 44.0
    assert archivio.salva(ricaricato)
    assert copia.read_bytes() == primo and principale.read_bytes() != primo
    riletto = Mondo()
    assert archivio.carica(riletto) == archivio.CARICATO and riletto.formato_letto == 11 and riletto.fondazioni_di_sempre == 2


def test_il_mondo_dalla_copia_del_formato_10_riscrive_anche_la_copia(cartella_di_prova):
    m = _mondo_con_due_polisportive()
    principale, copia = cartella_di_prova / FILE_MONDO, cartella_di_prova / FILE_MONDO_COPIA
    _scrivi_documento(copia, al_formato_10(archivio.componi(m)))
    principale.write_bytes(b"rovinato")
    messaggi = []
    ricaricato = Mondo(notifica=messaggi.append)
    assert archivio.carica(ricaricato) == archivio.DALLA_COPIA and ricaricato.formato_letto == 10
    assert archivio.salva(ricaricato)
    assert _formato_del_file(principale) == _formato_del_file(copia) == 11


def test_se_la_copia_nuova_non_si_scrive_il_salvataggio_non_si_fa(cartella_di_prova):
    # Il mondo nuovo accanto alla copia vecchia è proprio il caso da evitare: meglio il salvataggio di prima, intatto.
    m = _mondo_con_due_polisportive()
    principale, copia = cartella_di_prova / FILE_MONDO, cartella_di_prova / FILE_MONDO_COPIA
    _scrivi_documento(principale, al_formato_10(archivio.componi(m)))
    vecchio = principale.read_bytes()
    messaggi = []
    ricaricato = Mondo(notifica=messaggi.append)
    archivio.carica(ricaricato)
    copia.mkdir()
    messaggi.clear()
    assert not archivio.salva(ricaricato)
    # Nota 3 della revisione dei rimedi di D40: il messaggio dice che il salvataggio aspetta la copia nuova, oltre all'errore di Windows.
    assert messaggi[0].startswith(f"Salvataggio non riuscito: la copia di sicurezza, {FILE_MONDO_COPIA}, non si è potuta scrivere nel formato 11: ")
    assert messaggi[0].endswith(". Il primo salvataggio nel formato 11 aspetta la copia nuova, perché un MESS di prima che apra lo stesso mondo non "
                                "torni a una copia del formato vecchio. Il salvataggio precedente è rimasto com'era, e il prossimo salvataggio ci riprova.")
    # L'errore di Windows nomina anche lui la copia, col suo percorso.
    assert messaggi[0].count(FILE_MONDO_COPIA) == 2 and len(messaggi) == 1
    assert principale.read_bytes() == vecchio and ricaricato.formato_letto == 10
    assert set(os.listdir(cartella_di_prova)) == {FILE_MONDO, FILE_MONDO_COPIA}
    copia.rmdir()
    assert archivio.salva(ricaricato)
    assert _formato_del_file(principale) == _formato_del_file(copia) == 11


# Il formato più recente.

def _mondo_del_formato_12(percorso):
    """Un salvataggio vero, firmato, di un MESS col formato 12, che questa versione non sa leggere."""
    contenuto = archivio.componi(_mondo_con_due_polisportive())
    contenuto["formato"] = archivio.FORMATO + 1
    _scrivi_documento(percorso, contenuto)


def test_il_formato_12_ferma_il_caricamento_senza_toccare_niente(cartella_di_prova):
    # Anche con la copia buona accanto: niente ripiego, niente copie messe da parte, niente blocco dei salvataggi.
    buono = _mondo_con_due_polisportive()
    assert archivio.salva(buono) and archivio.salva(buono)
    _mondo_del_formato_12(cartella_di_prova / FILE_MONDO)
    prima = _istantanea(cartella_di_prova)
    messaggi = []
    mondo = Mondo(notifica=messaggi.append)
    with pytest.raises(archivio.FormatoPiuRecente) as errore:
        archivio.carica(mondo)
    assert (errore.value.formato, errore.value.massimo) == (12, 11) and "con il formato 12" in str(errore.value)
    # Dal 3 novembre 2026 l'errore dice di quale file si tratta: qui del salvataggio.
    assert not errore.value.della_copia and errore.value.motivo is None
    assert _istantanea(cartella_di_prova) == prima and set(prima) == {FILE_MONDO, FILE_MONDO_COPIA}
    assert not mondo.salvataggio_bloccato and mondo.giocatori == {} and messaggi == []


def test_il_formato_12_con_un_altra_firma_e_piu_recente_non_rovinato(cartella_di_prova):
    # Nota 5 della revisione dei rimedi di D40: un MESS futuro che cambiasse la firma, o che non la scrivesse più, non deve
    # far tornare alla copia di sicurezza; il formato si guarda prima della firma.
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
        assert errore.value.formato == 12 and not errore.value.della_copia
        assert _istantanea(cartella_di_prova) == prima
    # Il formato di oggi con la firma sbagliata resta un file rovinato, e così un altro programma col formato 12.
    with gzip.open(principale, "wt", encoding="utf-8") as f:
        f.write(json.dumps({**archivio.componi(buono), "firma": "sbagliata"}))
    with pytest.raises(archivio.ErroreSalvataggio, match="la firma non corrisponde"):
        archivio.leggi(principale)
    with gzip.open(principale, "wt", encoding="utf-8") as f:
        f.write(json.dumps({**contenuto, "applicazione": "Altro", "firma": "sbagliata"}))
    with pytest.raises(archivio.ErroreSalvataggio, match="la firma non corrisponde"):
        archivio.leggi(principale)


def test_anche_una_copia_del_formato_12_ferma_il_caricamento(cartella_di_prova):
    (cartella_di_prova / FILE_MONDO).write_bytes(b"rovinato")
    _mondo_del_formato_12(cartella_di_prova / FILE_MONDO_COPIA)
    prima = _istantanea(cartella_di_prova)
    mondo = Mondo()
    with pytest.raises(archivio.FormatoPiuRecente) as errore:
        archivio.carica(mondo, metti_da_parte=True)
    assert _istantanea(cartella_di_prova) == prima and not mondo.salvataggio_bloccato
    # Nota 4 della revisione dei rimedi di D40: del formato più recente è la copia, e l'errore dice perché il salvataggio non si usava.
    assert errore.value.della_copia and errore.value.motivo.startswith("il file non è un JSON valido")
    # Senza il salvataggio, il perché è che il file non c'è.
    os.remove(cartella_di_prova / FILE_MONDO)
    with pytest.raises(archivio.FormatoPiuRecente) as errore:
        archivio.carica(Mondo())
    assert errore.value.della_copia and errore.value.motivo == f"il file {FILE_MONDO} non c'è"


def test_la_data_di_un_mondo_del_formato_12_non_guarda_la_copia(cartella_di_prova):
    # Come il caricamento, che non ripiega: la copia buona non rende usabile quel mondo.
    buono = _mondo_con_due_polisportive()
    assert archivio.salva(buono) and archivio.salva(buono)
    _mondo_del_formato_12(cartella_di_prova / FILE_MONDO)
    data, dal_salvataggio, errore = cdm.salvato(cartella_di_prova)
    assert data is not None and not dal_salvataggio
    assert errore == "il file viene da una versione più recente del gioco, con il formato 12, mentre questa legge fino al formato 11"
