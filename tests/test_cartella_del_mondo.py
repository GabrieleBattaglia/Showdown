"""
Le prove della cartella del mondo, richiesta di Gabriele del 23 ottobre 2026: il mondo, lo stato di gioco
e le impostazioni stanno in una cartella sola, da portare fra le macchine, che si sceglie dal menu
Impostazioni. Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Prima percorsi.py: il file accanto al programma si rilegge a ogni chiamata, senza vale la cartella
predefinita, rovinato non manda mai a scrivere altrove. Poi cartella_del_mondo.py: i dati, la data di un
salvataggio, il trasloco tutto o niente, sullo stesso disco e fra due dischi, con la riserva datata, e la
vecchia disposizione. Poi l'avvio: la predefinita che si crea, la cartella che non c'è con Riprova,
Scegli un'altra cartella ed Esci, i dati spostati alla prima partenza, --attendi e la riapertura. Infine
la finestra: la voce del menu, la cartella senza mondo, quella con un mondo e le tre scelte, gli errori.
Nessuna finestra di Windows vera: la scelta della cartella e i dialoghi si sostituiscono; e niente si
scrive fuori dalle cartelle temporanee delle prove.
"""

import datetime
import errno
import faulthandler
import functools
import itertools
import json
import os
import random
import sys

import pytest
import wx

import archivio
import cartella_del_mondo as cdm
import impostazioni
import istanza
import modelli_torneo
import percorsi
import registro
import Showdown
import testi
from costanti import CARTELLA_CRONACHE, FILE_MONDO, FILE_MONDO_COPIA, NOME_FILE_LOG_USCITE
from gui import dialoghi
from gui import finestra as finestra_modulo
from gui.finestra import FinestraPrincipale
from modelli import Polisportiva
from mondo import Mondo
from utilita import adesso, adesso_utc

IERI = datetime.datetime(2026, 10, 22, 21, 15)
OGGI = datetime.datetime(2026, 10, 23, 18, 40)
ADESSO = datetime.datetime(2026, 10, 23, 19, 5)


def _mondo(giocatori=6):
    random.seed(5)
    ora = adesso()
    m = Mondo()
    m.datetime_corrente_simulazione = ora
    m.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=1)
    m.crea_giocatori_casuali(giocatori, ora)
    return m


def _salva_in(cartella, quando, m=None):
    """Un mondo salvato nella cartella, col momento del salvataggio dato; restituisce il percorso del file."""
    os.makedirs(cartella, exist_ok=True)
    file = os.path.join(cartella, FILE_MONDO)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(archivio, "adesso", lambda: quando)
        archivio.scrivi(m or _mondo(), file, os.path.join(cartella, FILE_MONDO_COPIA))
    return file


def _dati_di_prova(cartella, segno):
    """Tutti i dati di una cartella del mondo, finti tranne il nome, ciascuno col segno dato per riconoscerlo."""
    os.makedirs(os.path.join(cartella, CARTELLA_CRONACHE), exist_ok=True)
    os.makedirs(os.path.join(cartella, "tornei"), exist_ok=True)
    for nome in (FILE_MONDO, FILE_MONDO_COPIA, impostazioni.FILE_IMPOSTAZIONI, NOME_FILE_LOG_USCITE, "formule.json"):
        with open(os.path.join(cartella, nome), "w", encoding="utf-8") as f:
            f.write(f"{segno} {nome}")
    with open(os.path.join(cartella, CARTELLA_CRONACHE, "partita.txt"), "w", encoding="utf-8") as f:
        f.write(segno)
    with open(os.path.join(cartella, "tornei", "Open.json"), "w", encoding="utf-8") as f:
        f.write(segno)


def _lancia(errore):
    """Una funzione che solleva l'errore dato, qualunque cosa riceva."""

    def lancia(*_argomenti, **_opzioni):
        raise errore

    return lancia


def _leggi(percorso):
    with open(percorso, encoding="utf-8") as f:
        return f.read()


def _albero(cartella):
    """Tutti i file sotto la cartella, con il contenuto, per vedere che niente si è perso o cambiato."""
    trovati = {}
    for radice, _cartelle, file in os.walk(cartella):
        for nome in file:
            percorso = os.path.join(radice, nome)
            with open(percorso, "rb") as f:
                trovati[os.path.relpath(percorso, cartella)] = f.read()
    return trovati


# percorsi.py.

def test_senza_il_file_vale_la_cartella_predefinita(programma_di_prova):
    os.remove(percorsi.file_della_cartella())
    predefinita = str(programma_di_prova / "Mondo")
    assert percorsi.cartella_scelta() is None
    assert percorsi.cartella() == predefinita == percorsi.cartella_predefinita()
    assert percorsi.percorso(FILE_MONDO) == os.path.join(predefinita, FILE_MONDO)
    # I registri e il file della cartella stanno accanto al programma.
    assert percorsi.nel_programma("MESS - Errori.log") == str(programma_di_prova / "MESS - Errori.log")
    assert percorsi.file_della_cartella() == str(programma_di_prova / percorsi.FILE_DELLA_CARTELLA)


def test_il_file_si_rilegge_a_ogni_chiamata(cartella_di_prova, tmp_path_factory):
    assert percorsi.cartella() == str(cartella_di_prova)
    altra = tmp_path_factory.mktemp("altra")
    # Un altro processo, o la mano di chi gioca, cambia il file: la chiamata seguente lo vede.
    with open(percorsi.file_della_cartella(), "w", encoding="utf-8") as f:
        json.dump({"cartella": str(altra)}, f)
    assert percorsi.cartella() == str(altra)


def test_la_predefinita_toglie_il_file_e_una_cartella_del_programma_si_scrive_relativa(programma_di_prova):
    percorsi.imposta_cartella(percorsi.cartella_predefinita())
    assert not os.path.exists(percorsi.file_della_cartella())
    dentro = programma_di_prova / "Dati" / "Mondo di casa"
    percorsi.imposta_cartella(str(dentro))
    assert json.loads(_leggi(percorsi.file_della_cartella())) == {"cartella": os.path.join("Dati", "Mondo di casa")}
    assert percorsi.cartella() == str(dentro)
    assert not os.path.exists(percorsi.file_della_cartella() + ".tmp")


@pytest.mark.parametrize("contenuto", ["non è json", "[]", '{"cartella": ""}', '{"altro": "x"}'])
def test_il_file_rovinato_non_manda_mai_a_scrivere_altrove(programma_di_prova, contenuto):
    with open(percorsi.file_della_cartella(), "w", encoding="utf-8") as f:
        f.write(contenuto)
    with pytest.raises(percorsi.CartellaIllegibile) as errore:
        percorsi.cartella()
    assert isinstance(errore.value, OSError) and percorsi.FILE_DELLA_CARTELLA in str(errore.value)
    # Il salvataggio fallisce col suo messaggio, e non nasce niente nella cartella predefinita.
    messaggi = []
    m = _mondo()
    m.notifica = messaggi.append
    assert archivio.salva(m) is False
    assert messaggi and messaggi[0].startswith("Salvataggio non riuscito:")
    assert not os.path.exists(percorsi.cartella_predefinita())
    assert impostazioni.salva(impostazioni.valide(None)) is False


def test_stessa_e_dentro():
    assert percorsi.stessa("C:\\Giochi\\MESS\\", "c:\\giochi\\mess")
    assert percorsi.dentro("C:\\Giochi\\MESS\\cronache", "C:\\Giochi\\MESS")
    assert not percorsi.dentro("C:\\Giochi\\MESSA", "C:\\Giochi\\MESS")
    assert not percorsi.dentro("D:\\MESS", "C:\\MESS")
    # Un disco che non c'è, come una penna staccata, non fa sollevare niente.
    assert not percorsi.stessa("Q:\\Penna\\MESS", "C:\\Giochi\\MESS") and percorsi.stessa("Q:\\Penna\\MESS", "q:\\penna\\mess\\")


def _giunzione(verso, dove):
    """Una giunzione di Windows, come quella di mklink /J: la stessa cartella raggiunta per un'altra strada."""
    _winapi = pytest.importorskip("_winapi")
    if not hasattr(_winapi, "CreateJunction"):
        pytest.skip("questo Python non sa creare giunzioni")
    _winapi.CreateJunction(str(verso), str(dove))


def test_la_stessa_cartella_per_una_giunzione_non_si_trasloca(tmp_path):
    # Revisione del 23 ottobre 2026, difetto 2: stessa() rispondeva falso, e Porta il mio mondo metteva tutti i dati in una riserva dentro sé stessi.
    vera, giunzione = tmp_path / "Mondo vero", tmp_path / "Collegamento"
    _dati_di_prova(vera, "mio")
    prima = _albero(vera)
    _giunzione(vera, giunzione)
    try:
        assert percorsi.stessa(vera, giunzione) and percorsi.normale(vera) == percorsi.normale(giunzione)
        assert percorsi.dentro(giunzione / "cronache" / "nuova", vera)
        assert cdm.intrecciate(str(vera), str(giunzione / "tornei" / "nuova"))
        with pytest.raises(cdm.SpostamentoNonRiuscito) as errore:
            cdm.trasloca(str(vera), str(giunzione), ADESSO)
        assert errore.value.motivo == f"le cartelle {vera} e {giunzione} sono la stessa"
        assert _albero(vera) == prima and not any(nome.startswith("Riserva") for nome in os.listdir(vera))
    finally:
        os.rmdir(giunzione)


def test_la_cartella_relativa_si_scrive_fra_le_forme_reali(programma_di_prova, tmp_path):
    # Il programma raggiunto per una giunzione: la cartella del mondo dentro di lui si scrive relativa, senza errori.
    giunzione = tmp_path / "MESS per collegamento"
    _giunzione(programma_di_prova, giunzione)
    try:
        percorsi.imposta_cartella(str(giunzione / "Dati"))
        assert json.loads(_leggi(percorsi.file_della_cartella())) == {"cartella": "Dati"}
    finally:
        os.rmdir(giunzione)


# cartella_del_mondo.py: i dati e la data del salvataggio.

def test_i_dati_e_il_mondo_di_una_cartella(tmp_path):
    assert cdm.presenti(tmp_path) == [] and not cdm.ha_un_mondo(tmp_path)
    (tmp_path / impostazioni.FILE_IMPOSTAZIONI).write_text("{}", encoding="utf-8")
    (tmp_path / "Riserva 2026-10-01 10.00").mkdir()
    (tmp_path / "foto.jpg").write_bytes(b"x")
    assert cdm.presenti(tmp_path) == [impostazioni.FILE_IMPOSTAZIONI] and not cdm.ha_un_mondo(tmp_path)
    (tmp_path / "mess_mondo.json").write_text("{}", encoding="utf-8")
    assert cdm.ha_un_mondo(tmp_path)
    # Nella cartella del mondo stanno tutti i dati della richiesta, e nessun registro.
    assert set(cdm.DATI) == {"mess_mondo.json.gz", "mess_mondo.json.gz.bak", "mess_mondo.json", "mess_mondo.json.bak", "mess_mondo.json.gz.tmp",
                             "mess_impostazioni.json", "vecchie_glorie.log", "cronache", "tornei", "formule.json", "salvataggi_illeggibili"}


def _mondo_del_futuro(cartella):
    """Un salvataggio firmato di una versione più recente, che questa non sa leggere: il caso realistico del mondo dell'altro computer."""
    documento = {"applicazione": "MESS", "formato": archivio.FORMATO + 1, "versione": "9.0.0", "salvato": OGGI.isoformat(), "mondo": {}}
    os.makedirs(cartella, exist_ok=True)
    with open(os.path.join(cartella, FILE_MONDO), "w", encoding="utf-8") as f:
        json.dump({**documento, "firma": archivio.firma(documento)}, f)


def test_la_data_dal_salvataggio_dalla_copia_o_il_perche(tmp_path):
    assert cdm.salvato(tmp_path) == cdm.Salvato(None, False, None)
    file = _salva_in(str(tmp_path), OGGI)
    assert cdm.salvato(tmp_path) == (OGGI, True, None)
    # Un secondo salvataggio: il primo passa nella copia.
    _salva_in(str(tmp_path), ADESSO)
    assert cdm.salvato(tmp_path) == (ADESSO, True, None)
    # Il salvataggio rovinato e la copia buona: la data è quella della copia, che MESS caricherebbe.
    with open(file, "wb") as f:
        f.write(b"rovinato")
    momento = datetime.datetime(2026, 10, 20, 8, 30).timestamp()
    os.utime(file, (momento, momento))
    assert cdm.salvato(tmp_path) == (OGGI, True, None)
    # Nessuno dei due: la data del file del salvataggio, e il perché con le parole del caricamento.
    with open(tmp_path / FILE_MONDO_COPIA, "wb") as f:
        f.write(b"rovinata anche lei")
    data, dal_salvataggio, errore = cdm.salvato(tmp_path)
    assert data == datetime.datetime(2026, 10, 20, 8, 30) and not dal_salvataggio
    assert errore.startswith("il file non è un JSON valido") and "; e la copia di sicurezza nemmeno, perché il file non è un JSON valido" in errore
    # Il mondo di una versione più recente non si legge, e lo dice.
    altra = tmp_path / "altra"
    _mondo_del_futuro(str(altra))
    assert cdm.salvato(altra).errore.startswith(f"il file viene da una versione più recente del gioco, con il formato {archivio.FORMATO + 1}")


def test_le_frasi_della_data_e_del_piu_recente():
    assert testi.quando_salvato(OGGI, True) == "è stato salvato il 23 ottobre 2026 alle 18:40"
    assert testi.quando_salvato(datetime.datetime(2026, 10, 8, 9, 0), True) == "è stato salvato l'8 ottobre 2026 alle 09:00"
    assert testi.quando_salvato(OGGI, False).startswith("ha il file datato il 23 ottobre 2026 alle 18:40: il salvataggio non dice")
    assert testi.quando_salvato(None, False) == "non è ancora stato salvato"
    assert testi.quando_salvato(OGGI, False, "la firma non corrisponde") == "non si legge, con il file datato il 23 ottobre 2026 alle 18:40: la firma non corrisponde"
    assert testi.piu_recente(IERI, OGGI) == testi.QUELLO_DELLA_CARTELLA
    assert testi.piu_recente(OGGI, IERI) == testi.IL_TUO
    assert testi.piu_recente(OGGI, OGGI) is None
    assert testi.piu_recente(None, OGGI) == testi.IL_TUO


# Il trasloco.

def test_il_trasloco_con_la_riserva_non_perde_niente(tmp_path):
    mia, sua = tmp_path / "mia", tmp_path / "sua"
    _dati_di_prova(mia, "mio")
    _dati_di_prova(sua, "suo")
    (sua / "foto.jpg").write_bytes(b"di chi usa Dropbox")
    prima_mia, prima_sua = _albero(mia), _albero(sua)
    trasloco = cdm.trasloca(str(mia), str(sua), ADESSO)
    trasloco.concludi()
    riserva = sua / "Riserva 2026-10-23 19.05"
    assert trasloco.riserva == str(riserva) and trasloco.avanzi == []
    # I miei dati sono nella cartella, i suoi nella riserva, i file non di MESS dove erano.
    assert _albero(riserva) == {nome: dati for nome, dati in prima_sua.items() if nome != "foto.jpg"}
    assert {nome: dati for nome, dati in _albero(sua).items() if not nome.startswith("Riserva")} == {**prima_mia, "foto.jpg": b"di chi usa Dropbox"}
    assert _albero(mia) == {} and os.path.isdir(mia)


def test_il_nome_della_riserva_non_copre_quella_dello_stesso_minuto(tmp_path):
    (tmp_path / "Riserva 2026-10-23 19.05").mkdir()
    (tmp_path / "Riserva 2026-10-23 19.05 (2)").mkdir()
    assert cdm.nome_della_riserva(tmp_path, ADESSO) == "Riserva 2026-10-23 19.05 (3)"


def test_uno_spostamento_che_non_riesce_rimette_tutto_a_posto(tmp_path, monkeypatch):
    mia, sua = tmp_path / "mia", tmp_path / "sua"
    _dati_di_prova(mia, "mio")
    _dati_di_prova(sua, "suo")
    prima_mia, prima_sua = _albero(mia), _albero(sua)
    nella_riserva = len(cdm.presenti(sua))
    vera = os.rename
    chiamate = []

    def rinomina(da, a):
        chiamate.append(da)
        # La riserva si riempie, poi il terzo dei miei dati non si sposta, per esempio perché un altro programma lo tiene aperto.
        if len(chiamate) == nella_riserva + 3:
            raise PermissionError(errno.EACCES, "Accesso negato", str(da))
        vera(da, a)

    monkeypatch.setattr(os, "rename", rinomina)
    with pytest.raises(cdm.SpostamentoNonRiuscito) as errore:
        cdm.trasloca(str(mia), str(sua), ADESSO)
    assert errore.value.rimasti == [] and "Accesso negato" in errore.value.motivo
    assert _albero(mia) == prima_mia and _albero(sua) == prima_sua
    # La riserva vuota se n'è andata.
    assert not any(nome.startswith("Riserva") for nome in os.listdir(sua))


def test_fra_due_dischi_si_copia_e_l_originale_si_toglie_alla_fine(tmp_path, monkeypatch):
    mia, sua = tmp_path / "mia", tmp_path / "sua"
    _dati_di_prova(mia, "mio")
    prima = _albero(mia)

    def altro_disco(da, a):
        raise OSError(errno.EXDEV, "Impossibile spostare il file in un'unità disco differente", str(da))

    monkeypatch.setattr(os, "rename", altro_disco)
    trasloco = cdm.trasloca(str(mia), str(sua), ADESSO)
    # Prima della conclusione gli originali ci sono ancora: il mondo non è mai in una cartella sola a metà.
    assert _albero(mia) == prima and _albero(sua) == prima
    assert trasloco.concludi() == []
    assert _albero(mia) == {} and _albero(sua) == prima


def test_fra_due_dischi_l_annullamento_toglie_le_copie(tmp_path, monkeypatch):
    mia, sua = tmp_path / "mia", tmp_path / "sua"
    _dati_di_prova(mia, "mio")
    prima = _albero(mia)
    monkeypatch.setattr(os, "rename", _lancia(OSError(errno.EXDEV, "altro disco")))
    trasloco = cdm.trasloca(str(mia), str(sua), ADESSO)
    assert trasloco.annulla() == []
    assert _albero(mia) == prima and not sua.exists()


def test_le_cartelle_intrecciate_si_rifiutano(tmp_path):
    mia = tmp_path / "mia"
    _dati_di_prova(mia, "mio")
    assert cdm.intrecciate(str(mia), str(mia / "cronache" / "nuova"))
    assert cdm.intrecciate(str(mia / "tornei"), str(mia))
    assert not cdm.intrecciate(str(mia), str(mia / "Nuova"))
    with pytest.raises(cdm.SpostamentoNonRiuscito):
        cdm.trasloca(str(mia), str(mia / "cronache" / "nuova"))
    assert _albero(mia)[os.path.join("cronache", "partita.txt")] == b"mio"


def test_cambia_cartella_nomina_la_nuova_e_se_il_file_non_si_scrive_torna_indietro(cartella_di_prova, tmp_path_factory):
    _dati_di_prova(cartella_di_prova, "mio")
    prima = _albero(cartella_di_prova)
    nuova = tmp_path_factory.mktemp("penna")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(percorsi, "imposta_cartella", _lancia(PermissionError(errno.EACCES, "Accesso negato")))
        with pytest.raises(cdm.SpostamentoNonRiuscito) as errore:
            cdm.cambia_cartella(str(nuova), ADESSO)
    assert percorsi.FILE_DELLA_CARTELLA in errore.value.motivo
    assert _albero(cartella_di_prova) == prima and _albero(nuova) == {}
    assert percorsi.cartella() == str(cartella_di_prova)
    trasloco = cdm.cambia_cartella(str(nuova), ADESSO)
    assert percorsi.cartella() == str(nuova) and _albero(nuova) == prima and trasloco.spostati == cdm.presenti(nuova)


# La cartella all'avvio.

def test_la_predefinita_si_crea_senza_domande(programma_di_prova):
    os.remove(percorsi.file_della_cartella())
    assert cdm.problema_della_cartella() is None
    assert (programma_di_prova / "Mondo").is_dir()


def test_i_problemi_della_cartella(programma_di_prova, tmp_path):
    assente = tmp_path / "penna" / "MESS"
    percorsi.imposta_cartella(str(assente))
    assert cdm.problema_della_cartella() == f"la cartella {assente} non c'è"
    # Non si crea: è su una penna che magari non è collegata.
    assert not assente.exists()
    # Il file rovinato lo dice in italiano, senza l'errore di json in inglese.
    with open(percorsi.file_della_cartella(), "w", encoding="utf-8") as f:
        f.write("rotto")
    assert cdm.problema_della_cartella() == f"il file {percorsi.FILE_DELLA_CARTELLA}, accanto al programma, è rovinato"
    os.remove(percorsi.file_della_cartella())
    (programma_di_prova / "Mondo").write_text("un file, non una cartella", encoding="utf-8")
    assert cdm.problema_della_cartella().startswith(f"la cartella {programma_di_prova / 'Mondo'} non si può creare")


def test_la_cartella_scelta_senza_mondo_e_un_problema_dell_avvio(programma_di_prova, tmp_path):
    # Revisione del 23 ottobre 2026, osservazione 2: il cloud non ancora pronto faceva nascere un mondo nuovo accanto al vero.
    cloud = tmp_path / "Dropbox" / "MESS"
    cloud.mkdir(parents=True)
    (cloud / impostazioni.FILE_IMPOSTAZIONI).write_text("{}", encoding="utf-8")
    percorsi.imposta_cartella(str(cloud))
    problema = cdm.problema_della_cartella()
    assert problema == f"nella cartella {cloud} non c'è un mondo di MESS" and isinstance(problema, cdm.SenzaMondo)
    # Dopo il sì a un mondo nuovo, quella cartella va bene; un'altra no.
    assert cdm.problema_della_cartella(str(cloud)) is None
    assert isinstance(cdm.problema_della_cartella(str(tmp_path)), cdm.SenzaMondo)
    _salva_in(str(cloud), OGGI)
    assert cdm.problema_della_cartella() is None
    # La predefinita senza mondo no: lì nasce il primo mondo di chi comincia.
    percorsi.imposta_cartella(percorsi.cartella_predefinita())
    assert cdm.problema_della_cartella() is None and not cdm.ha_un_mondo(percorsi.cartella_predefinita())


class _MetodoFinto:
    """Un finto ShowModal, da mettere nella classe del dialogo: come un metodo, riceve il dialogo."""

    def __get__(self, dialogo, _tipo=None):
        return self if dialogo is None else functools.partial(self, dialogo)


class AvvisoFinto(_MetodoFinto):
    """Al posto di ShowModal dell'avviso dell'avvio: risponde dal copione, e prima fa l'azione della risposta, se c'è."""

    def __init__(self, copione):
        self.copione = list(copione)
        self.testi = []

    def __call__(self, dialogo):
        self.testi.append(dialogo.testo.GetValue())
        risposta, azione = self.copione.pop(0)
        if azione:
            azione()
        return risposta


@pytest.fixture
def avvio(app_wx, monkeypatch):
    """L'avvio senza messaggi veri: risponde no alle domande, e annota i testi."""
    messaggi = []

    def messaggio(testo, titolo="", stile=0, *_a, **_k):
        messaggi.append(testo)
        return wx.NO if stile & wx.YES_NO else wx.OK

    monkeypatch.setattr(wx, "MessageBox", messaggio)
    return messaggi


def test_la_cartella_che_manca_e_riprova(avvio, suonati, tmp_path, monkeypatch):
    penna = tmp_path / "penna" / "MESS"
    percorsi.imposta_cartella(str(penna))
    # La penna collegata, ma il cloud che non ha ancora portato il mondo; poi arriva anche lui.
    finto = AvvisoFinto([(dialoghi.RIPROVA, None), (dialoghi.RIPROVA, lambda: penna.mkdir(parents=True)),
                         (dialoghi.RIPROVA, lambda: _salva_in(str(penna), OGGI))])
    monkeypatch.setattr(dialoghi.CartellaAssente, "ShowModal", finto)
    assert Showdown.prepara_la_cartella() == (None, None, None)
    assert suonati == ["cartella_assente"] * 3
    assert finto.testi[0].splitlines()[0] == f"MESS non trova il mondo: la cartella {penna} non c'è."
    assert "Poi scegli Riprova." in finto.testi[0] and "\n\n" not in finto.testi[0] and "nascere" not in finto.testi[0]
    assert finto.testi[2].splitlines()[0] == f"MESS non trova il mondo: nella cartella {penna} non c'è un mondo di MESS."
    assert "o per indicare di nuovo questa, se vuoi farci nascere un mondo nuovo." in finto.testi[2]
    assert percorsi.cartella() == str(penna)


def test_esci_non_fa_nascere_un_mondo_altrove(avvio, suonati, tmp_path, programma_di_prova, monkeypatch):
    penna = tmp_path / "penna"
    percorsi.imposta_cartella(str(penna))
    monkeypatch.setattr(dialoghi.CartellaAssente, "ShowModal", AvvisoFinto([(dialoghi.ESCI, None)]))
    assert Showdown.avvia_finestra() == Showdown.SENZA_CARTELLA
    assert suonati == ["cartella_assente"]
    assert not penna.exists() and sorted(p.name for p in programma_di_prova.iterdir()) == [percorsi.FILE_DELLA_CARTELLA]


def test_scegli_un_altra_cartella_all_avvio(avvio, suonati, tmp_path, monkeypatch):
    penna, vuota, col_mondo = tmp_path / "penna", tmp_path / "vuota", tmp_path / "dropbox"
    vuota.mkdir()
    _salva_in(str(col_mondo), OGGI)
    percorsi.imposta_cartella(str(penna))
    scelte = iter([None, str(vuota), str(col_mondo)])
    monkeypatch.setattr(dialoghi, "scegli_cartella", lambda genitore, titolo, partenza="": next(scelte))
    copione = AvvisoFinto([(dialoghi.UN_ALTRA_CARTELLA, None)] * 3)
    monkeypatch.setattr(dialoghi.CartellaAssente, "ShowModal", copione)
    assert Showdown.prepara_la_cartella() == (None, None, str(col_mondo))
    # La finestra chiusa con Annulla; la cartella senza mondo, con la domanda a cui si risponde no; quella col mondo, senza domande.
    assert suonati == ["cartella_assente", "cartella_mondo", "annullato", "cartella_assente", "cartella_mondo", "domanda", "annullato",
                       "cartella_assente", "cartella_mondo"]
    assert avvio == [testi.nessun_mondo_nella_cartella(str(vuota))]
    assert "ci nasce un mondo nuovo" in avvio[0]
    assert percorsi.cartella() == str(col_mondo)


def test_la_cartella_senza_mondo_scelta_all_avvio_col_si(avvio, suonati, tmp_path, monkeypatch):
    vuota = tmp_path / "vuota"
    vuota.mkdir()
    percorsi.imposta_cartella(str(tmp_path / "penna"))
    monkeypatch.setattr(dialoghi, "scegli_cartella", lambda genitore, titolo, partenza="": str(vuota))
    monkeypatch.setattr(dialoghi.CartellaAssente, "ShowModal", AvvisoFinto([(dialoghi.UN_ALTRA_CARTELLA, None)]))
    monkeypatch.setattr(wx, "MessageBox", lambda testo, titolo="", stile=0, *a, **k: wx.YES)
    # Dopo il sì la cartella senza mondo è accettata, e l'avviso non torna.
    assert Showdown.prepara_la_cartella() == (None, None, str(vuota))
    assert percorsi.cartella() == str(vuota) and suonati == ["cartella_assente", "cartella_mondo", "domanda"]


def test_all_avvio_non_si_sceglie_una_cartella_dentro_i_dati_del_programma(avvio, suonati, programma_di_prova, tmp_path, monkeypatch):
    # Revisione del 23 ottobre 2026, difetto 3: la cartella tornei del programma bloccava MESS a ogni avvio.
    penna = tmp_path / "penna"
    percorsi.imposta_cartella(str(penna))
    dentro = programma_di_prova / "tornei"
    monkeypatch.setattr(dialoghi, "scegli_cartella", lambda genitore, titolo, partenza="": str(dentro))
    monkeypatch.setattr(dialoghi.CartellaAssente, "ShowModal", AvvisoFinto([(dialoghi.UN_ALTRA_CARTELLA, None), (dialoghi.ESCI, None)]))
    assert Showdown.prepara_la_cartella() == (Showdown.SENZA_CARTELLA, None, None)
    assert avvio == [testi.intrecciata_col_programma(str(dentro), str(programma_di_prova))]
    # Dalla verifica finale la cartella rifiutata ha il suo suono, e non quello dell'annullamento, che resta ad Annulla.
    assert suonati == ["cartella_assente", "cartella_mondo", "cartella_rifiutata", "cartella_assente"]
    assert percorsi.cartella() == str(penna) and not dentro.exists()


def test_i_dati_accanto_al_programma_passano_nella_cartella_del_mondo(avvio, suonati, programma_di_prova):
    os.remove(percorsi.file_della_cartella())
    _dati_di_prova(programma_di_prova, "di prima")
    prima = _albero(programma_di_prova)
    esito, notizia, _accettata = Showdown.prepara_la_cartella()
    mondo = programma_di_prova / "Mondo"
    assert esito is None and _albero(mondo) == prima and _albero(programma_di_prova) == {os.path.join("Mondo", nome): dati for nome, dati in prima.items()}
    assert notizia == (f"Il mondo e i dati di gioco ora stanno nella cartella del mondo, {mondo}: li ho spostati da accanto al programma, nella "
                       f"cartella {programma_di_prova}. Dove tenerli si sceglie con Cartella del mondo, nel menu Impostazioni.")
    # Il suono lo fa la finestra, quando è comparsa.
    assert suonati == []
    # Alla partenza seguente non c'è più niente da spostare.
    assert Showdown.prepara_la_cartella() == (None, None, None)


def test_se_la_cartella_del_mondo_ne_ha_gia_uno_quelli_di_prima_vanno_in_riserva(avvio, programma_di_prova, monkeypatch):
    os.remove(percorsi.file_della_cartella())
    mondo = programma_di_prova / "Mondo"
    _dati_di_prova(mondo, "della cartella")
    _dati_di_prova(programma_di_prova, "di prima")
    prima_mondo = _albero(mondo)
    monkeypatch.setattr(cdm, "adesso", lambda: ADESSO)
    _esito, notizia, _accettata = Showdown.prepara_la_cartella()
    riserva = mondo / "Riserva 2026-10-23 19.05"
    assert {nome: dati for nome, dati in _albero(mondo).items() if not nome.startswith("Riserva")} == prima_mondo
    assert _albero(riserva)[FILE_MONDO] == f"di prima {FILE_MONDO}".encode()
    assert "che resta quello in uso" in notizia and str(riserva) in notizia


@pytest.mark.parametrize(("accanto", "nella_cartella", "resta"), [(OGGI, IERI, "accanto"), (IERI, OGGI, "cartella"), (OGGI, None, "cartella")])
def test_alla_prima_partenza_resta_in_uso_il_mondo_piu_recente(avvio, programma_di_prova, monkeypatch, accanto, nella_cartella, resta):
    # Revisione del 23 ottobre 2026, osservazione 6: una versione di prima aperta nel frattempo ha salvato accanto al programma.
    os.remove(percorsi.file_della_cartella())
    mondo = programma_di_prova / "Mondo"
    if nella_cartella is None:
        _mondo_del_futuro(str(mondo))
    else:
        _salva_in(str(mondo), nella_cartella, _mondo(4))
    _salva_in(str(programma_di_prova), accanto, _mondo(8))
    (programma_di_prova / impostazioni.FILE_IMPOSTAZIONI).write_text("{}", encoding="utf-8")
    monkeypatch.setattr(cdm, "adesso", lambda: ADESSO)
    _esito, notizia, _accettata = Showdown.prepara_la_cartella()
    riserva = mondo / "Riserva 2026-10-23 19.05"
    in_uso, da_parte = (8, 4) if resta == "accanto" else (4, 8)
    if nella_cartella is None:
        # Quello della cartella non si legge: resta lui, e quello di accanto va da parte, senza confronti.
        assert len(archivio.leggi(str(riserva / FILE_MONDO))["mondo"]["giocatori"]) == 8 and "che resta quello in uso" in notizia
        return
    assert len(archivio.leggi(str(mondo / FILE_MONDO))["mondo"]["giocatori"]) == in_uso
    assert len(archivio.leggi(str(riserva / FILE_MONDO))["mondo"]["giocatori"]) == da_parte
    if resta == "accanto":
        assert "quello di accanto al programma è stato salvato dopo, e resta lui in uso" in notizia
        assert notizia.endswith("Quello che la cartella del mondo aveva prima è nella sua sottocartella Riserva 2026-10-23 19.05.")
        assert (mondo / impostazioni.FILE_IMPOSTAZIONI).exists()
    else:
        assert "che resta quello in uso" in notizia and (riserva / impostazioni.FILE_IMPOSTAZIONI).exists()


def test_la_vecchia_disposizione_salta_le_cartelle_vuote_e_la_cartella_del_mondo(avvio, programma_di_prova):
    # Revisione del 23 ottobre 2026, difetto 3: la cartella del mondo dentro la cartella tornei del programma fermava MESS a ogni avvio.
    mondo = programma_di_prova / "tornei"
    _salva_in(str(mondo), OGGI)
    percorsi.imposta_cartella(str(mondo))
    (programma_di_prova / "cronache").mkdir()
    (programma_di_prova / archivio.CARTELLA_QUARANTENA).mkdir()
    assert cdm.vecchia_disposizione() == []
    assert Showdown.prepara_la_cartella() == (None, None, None)
    (programma_di_prova / impostazioni.FILE_IMPOSTAZIONI).write_text("{}", encoding="utf-8")
    assert cdm.vecchia_disposizione() == [impostazioni.FILE_IMPOSTAZIONI]
    esito, notizia, _accettata = Showdown.prepara_la_cartella()
    assert esito is None and "che resta quello in uso" in notizia
    # Le cartelle vuote e quella che contiene il mondo restano dove sono, e il mondo pure.
    assert (programma_di_prova / "cronache").is_dir() and (mondo / FILE_MONDO).is_file()
    assert not (programma_di_prova / impostazioni.FILE_IMPOSTAZIONI).exists()


def test_se_lo_spostamento_della_prima_partenza_non_riesce_mess_si_ferma(avvio, suonati, programma_di_prova, monkeypatch):
    os.remove(percorsi.file_della_cartella())
    _dati_di_prova(programma_di_prova, "di prima")
    prima = _albero(programma_di_prova)
    vera = os.rename

    def rinomina(da, a):
        if os.path.basename(da) == "formule.json":
            raise PermissionError(errno.EACCES, "Accesso negato", str(da))
        vera(da, a)

    monkeypatch.setattr(os, "rename", rinomina)
    assert Showdown.prepara_la_cartella() == (Showdown.NON_SPOSTATI, None, None)
    # Dalla verifica finale lo spostamento che non riesce ha il suo suono, e non quello del salvataggio non riuscito.
    assert suonati == ["cartella_non_spostata"]
    assert avvio[0].startswith(f"I dati del mondo stanno ancora accanto al programma, nella cartella {programma_di_prova}, e non si sono potuti")
    assert avvio[0].endswith("Non ho toccato niente, e MESS si chiude: controlla che nessun altro programma stia usando quei file, e riaprilo.")
    assert _albero(programma_di_prova) == prima


def test_la_vecchia_disposizione_non_conta_se_la_cartella_del_mondo_e_quella_del_programma(programma_di_prova):
    percorsi.imposta_cartella(str(programma_di_prova))
    _dati_di_prova(programma_di_prova, "mio")
    assert cdm.vecchia_disposizione() == [] and cdm.sposta_la_vecchia_disposizione() is None


# La copia che si riapre: --attendi e il comando.

def test_attendi_prima_dell_istanza_unica(monkeypatch, programma_di_prova):
    ordine = []
    monkeypatch.setattr(istanza, "aspetta_l_uscita", lambda pid, *a: ordine.append(("aspetta", pid)))
    monkeypatch.setattr(istanza, "manda", lambda: ordine.append(("manda",)) or True)
    assert Showdown.main(["--attendi", "4321"]) == 0
    assert ordine == [("aspetta", 4321), ("manda",)]
    ordine.clear()
    assert Showdown.main([]) == 0 and ordine == [("manda",)]


def test_gli_argomenti_di_attendi():
    assert istanza.da_attendere(["--attendi", "12"]) == 12
    assert istanza.da_attendere(["-q", "--attendi"]) is None
    assert istanza.da_attendere(["--attendi", "dodici"]) is None
    assert istanza.da_attendere(["-q", "-p", "no:cacheprovider"]) is None


def test_aspetta_l_uscita_di_un_processo_vero():
    # Un processo che non c'è più: subito vero. Questo stesso processo non esce: falso allo scadere.
    assert istanza.aspetta_l_uscita(0xFFFFFFF0, 1) is True
    assert istanza.aspetta_l_uscita(os.getpid(), 0.05) is False


def test_aspetta_l_uscita_di_un_processo_che_esce_durante_l_attesa():
    # Come la copia vecchia di MESS che si chiude mentre la nuova aspetta: l'attesa finisce all'uscita, ben prima dello scadere.
    import subprocess
    import time

    processo = subprocess.Popen([sys.executable, "-B", "-c", "import time; time.sleep(0.4)"])
    try:
        inizio = time.monotonic()
        assert istanza.aspetta_l_uscita(processo.pid, 30) is True
        assert time.monotonic() - inizio < 20 and processo.wait(5) == 0
    finally:
        if processo.poll() is None:
            processo.kill()


class _ProcessoFinto:
    pid = 4321


def test_il_comando_di_riapertura(monkeypatch, programma_di_prova):
    assert istanza.comando_di_riapertura(77) == [sys.executable, str(programma_di_prova / "Showdown.py"), "--attendi", "77"]
    lanciati, permessi = [], []
    monkeypatch.setattr(istanza.subprocess, "Popen", lambda comando, **opzioni: lanciati.append((comando, opzioni)) or _ProcessoFinto())
    monkeypatch.setattr(istanza.ctypes.windll.user32, "AllowSetForegroundWindow", permessi.append)
    # Da sorgente: l'ambiente di adesso, e la copia nuova può venire in primo piano.
    istanza.riapri()
    assert lanciati == [([sys.executable, str(programma_di_prova / "Showdown.py"), "--attendi", str(os.getpid())],
                         {"cwd": str(programma_di_prova), "close_fds": True})]
    assert permessi == [4321]
    # Dal programma compilato: MESS.exe, aperto da capo per PyInstaller.
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert istanza.comando_di_riapertura(77) == [sys.executable, "--attendi", "77"]
    istanza.riapri()
    comando, opzioni = lanciati[-1]
    assert comando == [sys.executable, "--attendi", str(os.getpid())] and opzioni["cwd"] == str(programma_di_prova)
    assert opzioni["env"]["PYINSTALLER_RESET_ENVIRONMENT"] == "1" and opzioni["env"].get("PATH") == os.environ.get("PATH")
    assert permessi == [4321, 4321]


def test_la_vera_scelta_della_cartella(app_wx, monkeypatch, tmp_path):
    # La funzione vera, con la finestra di Windows che risponde da sé: parte dalla cartella data se c'è, e restituisce quella scelta.
    partenze = []

    def mostra(dialogo):
        partenze.append(dialogo.GetPath())
        return wx.ID_OK

    monkeypatch.setattr(wx.DirDialog, "ShowModal", mostra)
    assert dialoghi.scegli_cartella(None, testi.TITOLO_DELLA_SCELTA, str(tmp_path)) == str(tmp_path)
    dialoghi.scegli_cartella(None, testi.TITOLO_DELLA_SCELTA, str(tmp_path / "manca"))
    assert partenze == [str(tmp_path), ""]
    monkeypatch.setattr(wx.DirDialog, "ShowModal", lambda dialogo: wx.ID_CANCEL)
    assert dialoghi.scegli_cartella(None, testi.TITOLO_DELLA_SCELTA, str(tmp_path)) is None


def test_dopo_lo_spostamento_i_modelli_si_rileggono(cartella_di_prova, tmp_path_factory):
    # Revisione del 23 ottobre 2026, difetto 5: tornando nella cartella di prima si rileggevano i modelli di prima del primo spostamento.
    gestore = modelli_torneo.GestoreModelli()
    gestore.crea_predefiniti()
    quanti = len(gestore.modelli()[0])
    nuova = tmp_path_factory.mktemp("penna")
    cdm.cambia_cartella(str(nuova), ADESSO)
    file = sorted(nome for nome in os.listdir(nuova / modelli_torneo.CARTELLA) if nome.endswith(modelli_torneo.ESTENSIONE))[0]
    os.remove(nuova / modelli_torneo.CARTELLA / file)
    cdm.cambia_cartella(str(cartella_di_prova), ADESSO)
    assert len(gestore.modelli()[0]) == quanti - 1


# La finestra.

@pytest.fixture
def finestra(app_wx, monkeypatch, cartella_di_prova):
    monkeypatch.setattr(wx.Dialog, "ShowModal", lambda self: wx.ID_CANCEL)
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.NO)
    random.seed(11)
    ora = adesso()
    m = _mondo(12)
    mia = Polisportiva("Club Di Prova", "segreta", ora)
    m.polisportive[mia.nome] = mia
    m.miapolisportiva_attiva = mia
    f = FinestraPrincipale(m, archivio.CARICATO, [], Mondo.rapporto_vuoto(ora), m.datetime_ultimo_run_reale)
    f.Show()
    yield f
    if f and not f.IsBeingDeleted():
        f.timer.Stop()
        f.Destroy()
    wx.Yield()


def _sceglie(monkeypatch, cartella):
    scelte = []

    def scegli(genitore, titolo, partenza=""):
        scelte.append((titolo, partenza))
        return None if cartella is None else str(cartella)

    monkeypatch.setattr(finestra_modulo, "scegli_cartella", scegli)
    return scelte


def test_la_voce_del_menu_impostazioni(finestra):
    voci = dict(finestra.voci_menu())["&Impostazioni"]
    assert ("Cartella del &mondo...", None, finestra.scegli_la_cartella_del_mondo) in voci
    assert "Cartella del mondo" in testi.guida(finestra.voci_guida())


def test_la_finestra_di_windows_chiusa_con_annulla(finestra, suonati, monkeypatch, cartella_di_prova):
    scelte = _sceglie(monkeypatch, None)
    finestra.scegli_la_cartella_del_mondo()
    assert scelte == [(testi.TITOLO_DELLA_SCELTA, str(cartella_di_prova))]
    assert suonati == ["cartella_mondo", "annullato"]
    assert finestra.barra.GetValue().splitlines()[3] == "cartella del mondo invariata"
    assert percorsi.cartella() == str(cartella_di_prova)


def test_la_stessa_cartella_e_una_dentro_i_dati(finestra, suonati, monkeypatch, cartella_di_prova):
    _sceglie(monkeypatch, cartella_di_prova)
    finestra.scegli_la_cartella_del_mondo()
    assert finestra.vista.GetValue() == f"La cartella {cartella_di_prova} è già quella del mondo: non cambia niente."
    _sceglie(monkeypatch, cartella_di_prova / "cronache" / "dentro")
    finestra.scegli_la_cartella_del_mondo()
    assert finestra.vista.GetValue().startswith(f"La cartella {cartella_di_prova / 'cronache' / 'dentro'} sta dentro i dati del mondo")
    # Due cartelle rifiutate, non annullate: Annulla della finestra di Windows ha l'altro suono.
    assert suonati == ["cartella_mondo", "cartella_rifiutata", "cartella_mondo", "cartella_rifiutata"]


def test_la_cartella_del_mondo_per_una_giunzione_e_la_stessa(finestra, suonati, monkeypatch, cartella_di_prova, tmp_path_factory):
    # Revisione del 23 ottobre 2026, difetto 2: la domanda col mondo già presente partiva, e Porta il mio mondo svuotava la cartella.
    _il_mio_salvato_ieri(finestra, cartella_di_prova)
    prima = _albero(cartella_di_prova)
    giunzione = tmp_path_factory.mktemp("altrove") / "Collegamento"
    _giunzione(cartella_di_prova, giunzione)
    try:
        _sceglie(monkeypatch, giunzione)
        finestra.scegli_la_cartella_del_mondo()
        assert finestra.vista.GetValue() == f"La cartella {cartella_di_prova} è già quella del mondo: non cambia niente."
        assert suonati == ["cartella_mondo", "cartella_rifiutata"] and _albero(cartella_di_prova) == prima
        assert percorsi.cartella() == str(cartella_di_prova)
    finally:
        os.rmdir(giunzione)


def test_dal_menu_non_si_sceglie_una_cartella_dentro_i_dati_del_programma(finestra, suonati, monkeypatch, cartella_di_prova, programma_di_prova):
    # Revisione del 23 ottobre 2026, difetto 3: alla partenza seguente MESS avrebbe dovuto spostare la cartella tornei dentro sé stessa.
    dentro = programma_di_prova / "tornei"
    _sceglie(monkeypatch, dentro)
    finestra.scegli_la_cartella_del_mondo()
    assert finestra.vista.GetValue() == testi.intrecciata_col_programma(str(dentro), str(programma_di_prova), str(cartella_di_prova))
    assert finestra.vista.GetValue().endswith(f"come tornei o cronache: scegline un'altra. Il mondo resta nella cartella {cartella_di_prova}.")
    assert suonati == ["cartella_mondo", "cartella_rifiutata"] and percorsi.cartella() == str(cartella_di_prova) and not dentro.exists()


def test_la_cartella_senza_mondo_riceve_i_dati_e_mess_continua(finestra, suonati, monkeypatch, cartella_di_prova, tmp_path_factory):
    nuova = tmp_path_factory.mktemp("penna")
    impostazioni.salva({**impostazioni.valide(None), "volume_effetti": 33})
    # La finestra all'apertura ha già copiato le formule dei tornei nella cartella del mondo.
    dati = set(os.listdir(cartella_di_prova)) | {FILE_MONDO}
    _sceglie(monkeypatch, nuova)
    finestra.scegli_la_cartella_del_mondo()
    assert suonati == ["cartella_mondo", "cartella_spostata"]
    # Il mondo si è salvato prima, e con le impostazioni è passato nella cartella nuova; la vecchia è vuota.
    assert set(os.listdir(nuova)) == dati and {FILE_MONDO, impostazioni.FILE_IMPOSTAZIONI} <= dati
    assert os.listdir(cartella_di_prova) == []
    assert percorsi.cartella() == str(nuova) and impostazioni.carica()["volume_effetti"] == 33
    assert finestra.vista.GetValue() == (f"Il mondo e i dati di gioco ora stanno nella cartella {nuova}: li ho spostati dalla cartella "
                                         f"{cartella_di_prova}. Su questo computer MESS li cercherà lì anche alle prossime partenze.")
    righe = finestra.barra.GetValue().splitlines()
    assert righe[3] == "cartella del mondo cambiata" and all(len(r) <= 40 for r in righe)
    # E MESS continua: il salvataggio seguente va nella cartella nuova.
    finestra.salva()
    assert os.path.exists(os.path.join(nuova, FILE_MONDO_COPIA)) and not finestra.chiusa


class DomandaFinta(_MetodoFinto):
    """Al posto di ShowModal della domanda col mondo già presente: annota il testo e i pulsanti, e risponde."""

    def __init__(self, risposta):
        self.risposta = risposta
        self.testo = None
        self.pulsanti = None

    def __call__(self, dialogo):
        self.testo = dialogo.testo.GetValue()
        self.pulsanti = [b.GetLabel() for b in dialogo.bottoni]
        self.predefinito = dialogo.GetDefaultItem().GetLabel()
        return self.risposta


def _cartella_col_mondo(tmp_path_factory):
    dropbox = tmp_path_factory.mktemp("dropbox")
    _salva_in(str(dropbox), OGGI, _mondo(4))
    (dropbox / impostazioni.FILE_IMPOSTAZIONI).write_text(json.dumps({"volume_effetti": 70}), encoding="utf-8")
    return dropbox


def _il_mio_salvato_ieri(finestra, cartella_di_prova):
    _salva_in(str(cartella_di_prova), IERI, finestra.mondo)


def test_la_domanda_dice_le_date_e_il_piu_recente(finestra, suonati, monkeypatch, cartella_di_prova, tmp_path_factory):
    dropbox = _cartella_col_mondo(tmp_path_factory)
    _il_mio_salvato_ieri(finestra, cartella_di_prova)
    prima_mia, prima_sua = _albero(cartella_di_prova), _albero(dropbox)
    domanda = DomandaFinta(wx.ID_CANCEL)
    monkeypatch.setattr(dialoghi.MondoGiaPresente, "ShowModal", domanda)
    monkeypatch.setattr(finestra_modulo, "adesso", lambda: ADESSO)
    _sceglie(monkeypatch, dropbox)
    finestra.scegli_la_cartella_del_mondo()
    assert domanda.testo.splitlines()[:3] == [
        f"Nella cartella {dropbox} c'è già un mondo di MESS, che è stato salvato il 23 ottobre 2026 alle 18:40.",
        f"Il tuo mondo, nella cartella {cartella_di_prova}, è stato salvato il 22 ottobre 2026 alle 21:15.",
        "Il più recente è quello della cartella.",
    ]
    assert "Riserva 2026-10-23 19.05" in domanda.testo and "\n\n" not in domanda.testo
    assert domanda.pulsanti == ["&Usa il mondo della cartella, il più recente", "&Porta il mio mondo", "Annulla"]
    assert domanda.predefinito == "Annulla"
    # Annulla non cambia niente.
    assert suonati == ["cartella_mondo", "domanda", "annullato"]
    assert _albero(cartella_di_prova) == prima_mia and _albero(dropbox) == prima_sua and percorsi.cartella() == str(cartella_di_prova)
    assert finestra.barra.GetValue().splitlines()[3] == "cartella del mondo invariata"


def test_porta_il_mio_mondo(finestra, suonati, monkeypatch, cartella_di_prova, tmp_path_factory):
    dropbox = _cartella_col_mondo(tmp_path_factory)
    _il_mio_salvato_ieri(finestra, cartella_di_prova)
    prima_sua = _albero(dropbox)
    monkeypatch.setattr(dialoghi.MondoGiaPresente, "ShowModal", DomandaFinta(dialoghi.PORTA_IL_MIO_MONDO))
    monkeypatch.setattr(finestra_modulo, "adesso", lambda: ADESSO)
    _sceglie(monkeypatch, dropbox)
    finestra.scegli_la_cartella_del_mondo()
    riserva = dropbox / "Riserva 2026-10-23 19.05"
    assert suonati == ["cartella_mondo", "domanda", "cartella_spostata"]
    assert _albero(riserva) == prima_sua
    assert percorsi.cartella() == str(dropbox) and os.listdir(cartella_di_prova) == []
    # Il mondo arrivato è il mio, salvato appena prima di spostarlo.
    assert len(archivio.leggi(str(dropbox / FILE_MONDO))["mondo"]["giocatori"]) == 12
    assert finestra.vista.GetValue().endswith("Quello che la cartella aveva prima è nella sua sottocartella Riserva 2026-10-23 19.05.")


def test_usa_il_mondo_della_cartella_e_mess_si_riapre(finestra, suonati, monkeypatch, cartella_di_prova, tmp_path_factory):
    dropbox = _cartella_col_mondo(tmp_path_factory)
    _il_mio_salvato_ieri(finestra, cartella_di_prova)
    prima_sua = _albero(dropbox)
    riaperture = []
    monkeypatch.setattr(istanza, "riapri", lambda: riaperture.append(percorsi.cartella()))
    monkeypatch.setattr(dialoghi.MondoGiaPresente, "ShowModal", DomandaFinta(dialoghi.USA_IL_MONDO_DELLA_CARTELLA))
    _sceglie(monkeypatch, dropbox)
    finestra.scegli_la_cartella_del_mondo()
    # La copia nuova parte quando il file nomina già la cartella; la vecchia si chiude senza scriverci niente.
    assert riaperture == [str(dropbox)] and finestra.chiusa
    assert suonati == ["cartella_mondo", "domanda", "cartella_cambiata"]
    assert _albero(dropbox) == prima_sua
    # Il mio mondo resta dov'era, salvato adesso, intatto, con i suoi 12 giocatori.
    assert {FILE_MONDO, FILE_MONDO_COPIA} <= set(os.listdir(cartella_di_prova))
    assert len(archivio.leggi(str(cartella_di_prova / FILE_MONDO))["mondo"]["giocatori"]) == 12
    assert archivio.leggi(str(cartella_di_prova / FILE_MONDO))["salvato"] != IERI.isoformat()


def test_se_mess_non_si_riapre_lo_dice_e_si_chiude_lo_stesso(finestra, suonati, monkeypatch, cartella_di_prova, tmp_path_factory):
    dropbox = _cartella_col_mondo(tmp_path_factory)
    messaggi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: messaggi.append(testo) or wx.OK)
    monkeypatch.setattr(istanza, "riapri", _lancia(FileNotFoundError(errno.ENOENT, "Impossibile trovare il file")))
    monkeypatch.setattr(dialoghi.MondoGiaPresente, "ShowModal", DomandaFinta(dialoghi.USA_IL_MONDO_DELLA_CARTELLA))
    _sceglie(monkeypatch, dropbox)
    finestra.scegli_la_cartella_del_mondo()
    assert messaggi == [testi.riapertura_non_riuscita(FileNotFoundError(errno.ENOENT, "Impossibile trovare il file"), str(dropbox))]
    assert messaggi[0].startswith("MESS non si è potuto riaprire da solo: Impossibile trovare il file.")
    # Dalla verifica finale la riapertura che non parte ha il suo suono, prima del messaggio; poi MESS si chiude per il cambio di cartella.
    assert finestra.chiusa and percorsi.cartella() == str(dropbox)
    assert suonati == ["cartella_mondo", "domanda", "riapertura_mancata", "cartella_cambiata"]


def test_lo_spostamento_che_non_riesce_lascia_tutto_com_era(finestra, suonati, monkeypatch, cartella_di_prova, tmp_path_factory):
    nuova = tmp_path_factory.mktemp("penna")
    vera = os.rename

    def rinomina(da, a):
        if os.path.basename(da) == impostazioni.FILE_IMPOSTAZIONI:
            raise PermissionError(errno.EACCES, "Accesso negato", str(da))
        vera(da, a)

    impostazioni.salva(impostazioni.valide(None))
    dati = set(os.listdir(cartella_di_prova)) | {FILE_MONDO}
    monkeypatch.setattr(os, "rename", rinomina)
    _sceglie(monkeypatch, nuova)
    finestra.scegli_la_cartella_del_mondo()
    # Il mondo si è salvato, sono i dati che non si spostano: il suono dello spostamento, non quello del salvataggio.
    assert suonati == ["cartella_mondo", "cartella_non_spostata"]
    assert set(os.listdir(cartella_di_prova)) == dati and os.listdir(nuova) == []
    assert percorsi.cartella() == str(cartella_di_prova)
    assert finestra.vista.GetValue().startswith(f"I dati del mondo non si sono potuti spostare nella cartella {nuova}: Accesso negato:")
    assert finestra.vista.GetValue().endswith(f"Non è cambiato niente: il mondo resta nella cartella {cartella_di_prova}.")
    assert finestra.barra.GetValue().splitlines()[3] == "mondo non spostato"


def test_il_mondo_che_non_si_salva_non_cambia_cartella(finestra, suonati, monkeypatch, tmp_path_factory, cartella_di_prova):
    nuova = tmp_path_factory.mktemp("penna")
    finestra.mondo.salvataggio_bloccato = True
    _sceglie(monkeypatch, nuova)
    finestra.scegli_la_cartella_del_mondo()
    assert suonati == ["cartella_mondo", "salvataggio_non_riuscito"]
    assert finestra.vista.GetValue().startswith("Prima di cambiare cartella il mondo si salva, ma il salvataggio non è riuscito")
    assert percorsi.cartella() == str(cartella_di_prova) and os.listdir(nuova) == []


def test_il_mondo_della_cartella_che_non_si_legge_non_si_offre(finestra, suonati, monkeypatch, cartella_di_prova, tmp_path_factory):
    # Revisione del 23 ottobre 2026, difetto 4: Usa il mondo della cartella riapriva MESS su un salvataggio che lo fermava a ogni avvio.
    dropbox = tmp_path_factory.mktemp("dropbox")
    _mondo_del_futuro(str(dropbox))
    _il_mio_salvato_ieri(finestra, cartella_di_prova)
    domanda = DomandaFinta(wx.ID_CANCEL)
    monkeypatch.setattr(dialoghi.MondoGiaPresente, "ShowModal", domanda)
    monkeypatch.setattr(finestra_modulo, "adesso", lambda: ADESSO)
    _sceglie(monkeypatch, dropbox)
    finestra.scegli_la_cartella_del_mondo()
    righe = domanda.testo.splitlines()
    assert righe[0].startswith(f"Nella cartella {dropbox} c'è già un mondo di MESS, che non si legge, con il file datato ")
    assert "il file viene da una versione più recente del gioco" in righe[0]
    assert righe[1] == f"Il tuo mondo, nella cartella {cartella_di_prova}, è stato salvato il 22 ottobre 2026 alle 21:15."
    assert righe[2].startswith("Quel mondo non si può usare") and "più recente è" not in domanda.testo and "Usa il mondo" not in domanda.testo
    assert domanda.pulsanti == ["&Porta il mio mondo", "Annulla"] and domanda.predefinito == "Annulla"
    assert suonati == ["cartella_mondo", "domanda", "annullato"] and percorsi.cartella() == str(cartella_di_prova)


def _penna_staccata(finestra, suonati, tmp_path_factory):
    """La cartella del mondo su una penna, col mondo salvato, che si stacca a MESS aperto: dove stava, e dove è finita."""
    penna = tmp_path_factory.mktemp("penna") / "MESS"
    penna.mkdir()
    percorsi.imposta_cartella(str(penna))
    finestra.salva()
    staccata = penna.with_name("MESS staccata")
    os.rename(penna, staccata)
    suonati.clear()
    return penna, staccata


def test_la_penna_staccata_a_mess_aperto_e_il_mondo_salvato_nella_cartella_scelta(finestra, suonati, monkeypatch, tmp_path_factory):
    # Revisione del 23 ottobre 2026, osservazione 3: il mondo si salvava soltanto nella cartella che non c'era più, e i progressi si perdevano.
    penna, staccata = _penna_staccata(finestra, suonati, tmp_path_factory)
    prima = _albero(staccata)
    finestra.impostazioni = impostazioni.valide({**finestra.impostazioni, "volume_effetti": 33})
    nuova = tmp_path_factory.mktemp("nuova")
    _sceglie(monkeypatch, nuova)
    finestra.scegli_la_cartella_del_mondo()
    assert suonati == ["cartella_mondo", "cartella_spostata"]
    assert percorsi.cartella() == str(nuova) and impostazioni.carica()["volume_effetti"] == 33
    assert len(archivio.leggi(str(nuova / FILE_MONDO))["mondo"]["giocatori"]) == 12
    assert finestra.vista.GetValue().startswith(f"La cartella del mondo di prima, {penna}, non si raggiunge più: il mondo e le impostazioni ora "
                                                f"stanno nella cartella {nuova}, dove li ho salvati")
    assert finestra.barra.GetValue().splitlines()[3] == "cartella del mondo cambiata"
    assert _albero(staccata) == prima


def test_la_penna_staccata_e_la_cartella_col_mondo(finestra, suonati, monkeypatch, tmp_path_factory):
    penna, _staccata = _penna_staccata(finestra, suonati, tmp_path_factory)
    dropbox = _cartella_col_mondo(tmp_path_factory)
    prima_sua = _albero(dropbox)
    domanda = DomandaFinta(dialoghi.PORTA_IL_MIO_MONDO)
    monkeypatch.setattr(dialoghi.MondoGiaPresente, "ShowModal", domanda)
    monkeypatch.setattr(finestra_modulo, "adesso", lambda: ADESSO)
    _sceglie(monkeypatch, dropbox)
    finestra.scegli_la_cartella_del_mondo()
    # Usare il mondo della cartella perderebbe i progressi, che non si salvano da nessuna parte: non si offre.
    assert domanda.pulsanti == ["&Porta il mio mondo", "Annulla"]
    assert domanda.testo.splitlines()[1] == f"Il tuo mondo è aperto, ma la sua cartella, {penna}, non si raggiunge più, e lì non si può salvare."
    assert "ci salvo il tuo mondo e le tue impostazioni" in domanda.testo
    riserva = dropbox / "Riserva 2026-10-23 19.05"
    assert _albero(riserva) == prima_sua and len(archivio.leggi(str(dropbox / FILE_MONDO))["mondo"]["giocatori"]) == 12
    assert suonati == ["cartella_mondo", "domanda", "cartella_spostata"] and percorsi.cartella() == str(dropbox)
    assert finestra.vista.GetValue().endswith("Quello che la cartella aveva prima è nella sua sottocartella Riserva 2026-10-23 19.05.")


def test_la_penna_staccata_e_il_mondo_che_non_si_salva_nemmeno_nella_nuova(finestra, suonati, monkeypatch, tmp_path_factory):
    penna, _staccata = _penna_staccata(finestra, suonati, tmp_path_factory)
    dropbox = _cartella_col_mondo(tmp_path_factory)
    prima_sua = _albero(dropbox)
    monkeypatch.setattr(dialoghi.MondoGiaPresente, "ShowModal", DomandaFinta(dialoghi.PORTA_IL_MIO_MONDO))
    finestra.mondo.salvataggio_bloccato = True
    _sceglie(monkeypatch, dropbox)
    finestra.scegli_la_cartella_del_mondo()
    # Tutto torna com'era: i dati della cartella al loro posto, senza riserva, e il file che nomina ancora la penna.
    assert _albero(dropbox) == prima_sua and percorsi.cartella() == str(penna)
    # Qui è il mondo che non si salva, e il suono resta quello del salvataggio non riuscito.
    assert suonati == ["cartella_mondo", "domanda", "salvataggio_non_riuscito"]
    testo = finestra.vista.GetValue()
    assert testo.startswith(f"I dati del mondo non si sono potuti spostare nella cartella {dropbox}: il mondo non si è potuto salvare nella cartella nuova.")
    assert "Salvataggio rifiutato" in testo


def test_l_apertura_dopo_lo_spostamento_della_prima_partenza(app_wx, suonati, monkeypatch):
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.NO)
    m = _mondo()
    f = FinestraPrincipale(m, archivio.CARICATO, [], Mondo.rapporto_vuoto(adesso()), m.datetime_ultimo_run_reale, cartella_spostata="I dati sono passati.")
    try:
        assert f.vista.GetValue().startswith("I dati sono passati.\nMESS, ")
        f.suoni_d_avvio()
        assert suonati == ["avvio", "cartella_spostata"]
    finally:
        f.timer.Stop()
        f.Destroy()


# I dialoghi.

def test_l_avviso_dell_avvio_e_i_suoi_pulsanti(app_wx):
    dialogo = dialoghi.CartellaAssente(None, "MESS non trova la cartella del mondo.")
    try:
        assert [b.GetLabel() for b in dialogo.bottoni] == ["&Riprova", "&Scegli un'altra cartella", "&Esci"]
        assert dialogo.GetDefaultItem() is dialogo.bottoni[0] and dialogo.GetEscapeId() == dialoghi.ESCI == wx.ID_CANCEL
        for bottone, codice in zip(dialogo.bottoni, (dialoghi.RIPROVA, dialoghi.UN_ALTRA_CARTELLA, dialoghi.ESCI), strict=True):
            evento = wx.CommandEvent(wx.wxEVT_BUTTON, bottone.GetId())
            evento.SetEventObject(bottone)
            bottone.GetEventHandler().ProcessEvent(evento)
            assert dialogo.GetReturnCode() == codice
    finally:
        dialogo.Destroy()


def test_il_piu_recente_sul_pulsante_del_mio_mondo(app_wx):
    dialogo = dialoghi.MondoGiaPresente(None, "Testo.", testi.IL_TUO)
    try:
        assert [b.GetLabel() for b in dialogo.bottoni] == ["&Usa il mondo della cartella", "&Porta il mio mondo, il più recente", "Annulla"]
    finally:
        dialogo.Destroy()


class _Tasto:
    """Un Invio come lo vede il gancio della tastiera: il controllo da cui arriva, e se wx lo crede ripetuto."""

    def __init__(self, oggetto, codice=wx.WXK_RETURN, ripetuto=False):
        self.oggetto, self.codice, self.ripetuto, self.saltato = oggetto, codice, ripetuto, False

    def GetKeyCode(self):
        return self.codice

    def GetEventObject(self):
        return self.oggetto

    def IsAutoRepeat(self):
        return self.ripetuto

    def HasAnyModifiers(self):
        return False

    def Skip(self):
        self.saltato = True


@pytest.mark.parametrize(("fabbrica", "predefinito"), [
    (lambda: dialoghi.MondoGiaPresente(None, "Testo.", testi.QUELLO_DELLA_CARTELLA), wx.ID_CANCEL),
    (lambda: dialoghi.CartellaAssente(None, "Testo."), dialoghi.RIPROVA),
    (lambda: dialoghi.MondoIllegibile(None, "Testo."), dialoghi.RIPROVA),
])
def test_invio_nel_testo_vale_il_predefinito_ma_tenuto_giu_no(app_wx, monkeypatch, fabbrica, predefinito):
    # Revisione del 23 ottobre 2026, osservazione 8: un Invio rimasto dalla finestra di Windows annullava la domanda, o ripeteva Riprova.
    orologio = [100.0]
    monkeypatch.setattr(dialoghi, "_adesso", lambda: orologio[0])
    dialogo = fabbrica()
    try:
        # L'Invio tenuto giù dall'apertura, con NVDA: pressioni nuove ogni 30 ms, che non chiudono, nel testo come sui pulsanti.
        for oggetto in (dialogo.testo, dialogo.bottoni[0]) * 10:
            orologio[0] += 0.03
            tasto = _Tasto(oggetto)
            dialogo._tasto(tasto)
            assert not tasto.saltato and dialogo.GetReturnCode() == 0
        # Lasciato il tasto, un Invio nel testo vale il pulsante predefinito.
        orologio[0] += 1.0
        dialogo._tasto(_Tasto(dialogo.testo))
        assert dialogo.GetReturnCode() == predefinito
        # Su un pulsante l'Invio resta suo, ed Esc va a wx.
        orologio[0] += 1.0
        sul_pulsante, esc = _Tasto(dialogo.bottoni[0]), _Tasto(dialogo.testo, wx.WXK_ESCAPE)
        dialogo._tasto(sul_pulsante)
        dialogo._tasto(esc)
        assert sul_pulsante.saltato and esc.saltato
    finally:
        dialogo.Destroy()


def test_l_avviso_del_salvataggio_illeggibile_e_i_suoi_pulsanti(app_wx):
    dialogo = dialoghi.MondoIllegibile(None, "Il salvataggio non si legge.")
    try:
        assert dialogo.GetTitle() == "MESS, il salvataggio non si legge"
        assert [b.GetLabel() for b in dialogo.bottoni] == ["&Riprova", "&Scegli un'altra cartella", "&Esci"]
        assert dialogo.GetDefaultItem() is dialogo.bottoni[0] and dialogo.GetEscapeId() == dialoghi.ESCI
    finally:
        dialogo.Destroy()


# L'avvio intero, con la finestra principale e il suo ciclo finti.

class FinestraFinta:
    """Al posto di FinestraPrincipale: annota il mondo con cui nasce, e non mostra niente."""

    def __init__(self, nate, mondo, origine, *_argomenti, **opzioni):
        nate.append(self)
        self.mondo, self.origine, self.opzioni = mondo, origine, opzioni

    def Maximize(self):
        pass

    def Show(self):
        pass

    def suoni_d_avvio(self):
        pass


@pytest.fixture
def avvio_intero(avvio, monkeypatch):
    """avvia_finestra vero fino alla fine: la finestra principale, il suo ciclo e i rinvii di wx sono finti. Restituisce le finestre nate."""
    import threading

    nate = []
    monkeypatch.setattr(finestra_modulo, "FinestraPrincipale", functools.partial(FinestraFinta, nate))
    monkeypatch.setattr(wx.App, "MainLoop", lambda self: 0)
    monkeypatch.setattr(wx, "CallAfter", lambda funzione, *a, **k: None)
    # La rete per gli errori cambia i ganci delle eccezioni: tornano com'erano.
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    monkeypatch.setattr(threading, "excepthook", threading.excepthook)
    return nate


def test_il_salvataggio_illeggibile_all_avvio_e_un_altra_cartella(avvio_intero, suonati, monkeypatch, cartella_di_prova, tmp_path_factory):
    # Revisione del 23 ottobre 2026, difetto 4: il mondo di una versione più recente nella cartella scelta fermava MESS a ogni avvio.
    _mondo_del_futuro(str(cartella_di_prova))
    illeggibile = (cartella_di_prova / FILE_MONDO).read_bytes()
    buona = tmp_path_factory.mktemp("buona")
    _salva_in(str(buona), OGGI)
    monkeypatch.setattr(dialoghi, "scegli_cartella", lambda genitore, titolo, partenza="": str(buona))
    avviso = AvvisoFinto([(dialoghi.RIPROVA, None), (dialoghi.UN_ALTRA_CARTELLA, None)])
    monkeypatch.setattr(dialoghi.MondoIllegibile, "ShowModal", avviso)
    assert Showdown.avvia_finestra() == Showdown.APERTA
    assert suonati == ["salvataggio_illeggibile", "salvataggio_illeggibile", "cartella_mondo"]
    righe = avviso.testi[0].splitlines()
    assert righe[0].startswith(f"Il salvataggio del mondo, nella cartella {cartella_di_prova}, c'è ma non si può leggere: il file viene da una versione")
    assert righe[-1] == "Scegli un'altra cartella apre la finestra di Windows per indicarne un'altra. Esci, o Esc, chiude MESS senza toccare niente."
    # MESS si apre sul mondo della cartella scelta, e quello illeggibile resta com'era.
    assert len(avvio_intero) == 1 and avvio_intero[0].origine == archivio.CARICATO and percorsi.cartella() == str(buona)
    assert (cartella_di_prova / FILE_MONDO).read_bytes() == illeggibile


def test_dopo_il_si_a_un_mondo_nuovo_mess_si_apre_senza_altri_avvisi(avvio_intero, suonati, monkeypatch, tmp_path):
    vuota = tmp_path / "vuota"
    vuota.mkdir()
    percorsi.imposta_cartella(str(tmp_path / "penna"))
    monkeypatch.setattr(dialoghi, "scegli_cartella", lambda genitore, titolo, partenza="": str(vuota))
    monkeypatch.setattr(dialoghi.CartellaAssente, "ShowModal", AvvisoFinto([(dialoghi.UN_ALTRA_CARTELLA, None)]))
    monkeypatch.setattr(wx, "MessageBox", lambda testo, titolo="", stile=0, *a, **k: wx.YES)
    assert Showdown.avvia_finestra() == Showdown.APERTA
    assert suonati == ["cartella_assente", "cartella_mondo", "domanda"]
    assert avvio_intero[0].origine == archivio.NATO and percorsi.cartella() == str(vuota)


# La verifica finale del 23 ottobre 2026: le copie dei file illeggibili una volta sola, la notizia dei dati spostati nel registro.

def _riga_delle_copie(cartella):
    return f"Una copia dei file è nella cartella {cartella}."


def test_carica_puo_non_mettere_da_parte_i_file_illeggibili(cartella_di_prova):
    _mondo_del_futuro(str(cartella_di_prova))
    with pytest.raises(archivio.SalvataggioIllegibile) as errore:
        archivio.carica(Mondo(), metti_da_parte=False)
    assert errore.value.cartella is None and not (cartella_di_prova / archivio.CARTELLA_QUARANTENA).exists()
    with pytest.raises(archivio.SalvataggioIllegibile) as errore:
        archivio.carica(Mondo())
    assert os.listdir(cartella_di_prova / archivio.CARTELLA_QUARANTENA) == [os.path.basename(errore.value.cartella)]


def test_due_riprova_sullo_stesso_salvataggio_illeggibile_fanno_una_cartella_di_copie_sola(avvio_intero, suonati, monkeypatch, cartella_di_prova,
                                                                                           tmp_path_factory):
    # Ogni Riprova rifaceva le copie, in una cartella datata nuova a ogni secondo: col cloud, dove il testo consiglia di riprovare, si moltiplicavano.
    _mondo_del_futuro(str(cartella_di_prova))
    altra = tmp_path_factory.mktemp("altra")
    _mondo_del_futuro(str(altra))
    # Un secondo in più a ogni lettura dell'orologio: senza la correzione, ogni Riprova avrebbe la sua cartella.
    secondi = itertools.count()
    monkeypatch.setattr(archivio, "adesso", lambda: OGGI + datetime.timedelta(seconds=next(secondi)))
    monkeypatch.setattr(dialoghi, "scegli_cartella", lambda genitore, titolo, partenza="": str(altra))
    avviso = AvvisoFinto([(dialoghi.RIPROVA, None), (dialoghi.RIPROVA, None), (dialoghi.UN_ALTRA_CARTELLA, None), (dialoghi.RIPROVA, None),
                          (dialoghi.ESCI, None)])
    monkeypatch.setattr(dialoghi.MondoIllegibile, "ShowModal", avviso)
    assert Showdown.avvia_finestra() == Showdown.ILLEGGIBILE
    qui = os.listdir(cartella_di_prova / archivio.CARTELLA_QUARANTENA)
    la = os.listdir(altra / archivio.CARTELLA_QUARANTENA)
    assert len(qui) == 1 and len(la) == 1
    # L'avviso dice sempre dove stanno le copie: quelle della prima volta, per ciascuna cartella.
    copie_qui, copie_la = cartella_di_prova / archivio.CARTELLA_QUARANTENA / qui[0], altra / archivio.CARTELLA_QUARANTENA / la[0]
    assert [_riga_delle_copie(copie_qui) in testo for testo in avviso.testi] == [True, True, True, False, False]
    assert [_riga_delle_copie(copie_la) in testo for testo in avviso.testi] == [False, False, False, True, True]
    assert all("MESS non salva il mondo in quella cartella." in testo for testo in avviso.testi)
    assert suonati == ["salvataggio_illeggibile"] * 3 + ["cartella_mondo"] + ["salvataggio_illeggibile"] * 2


def test_le_copie_che_non_riescono_si_riprovano(avvio_intero, monkeypatch, cartella_di_prova):
    _mondo_del_futuro(str(cartella_di_prova))
    vera, chiamate = archivio._metti_da_parte, []

    def metti_da_parte(*file):
        chiamate.append(file)
        return None if len(chiamate) == 1 else vera(*file)

    monkeypatch.setattr(archivio, "_metti_da_parte", metti_da_parte)
    avviso = AvvisoFinto([(dialoghi.RIPROVA, None), (dialoghi.RIPROVA, None), (dialoghi.ESCI, None)])
    monkeypatch.setattr(dialoghi.MondoIllegibile, "ShowModal", avviso)
    assert Showdown.avvia_finestra() == Showdown.ILLEGGIBILE
    # La prima volta le copie non riescono, e l'avviso non le nomina; la seconda sì, e poi basta.
    assert len(chiamate) == 2
    copie = cartella_di_prova / archivio.CARTELLA_QUARANTENA / os.listdir(cartella_di_prova / archivio.CARTELLA_QUARANTENA)[0]
    assert ["Una copia dei file" in testo for testo in avviso.testi] == [False, True, True]
    assert _riga_delle_copie(copie) in avviso.testi[2]


def test_la_notizia_dei_dati_spostati_resta_nel_registro(avvio_intero, suonati, monkeypatch, programma_di_prova):
    # Alla prima partenza i dati accanto al programma si spostavano, poi il mondo non si leggeva, e con Esci la notizia non compariva mai.
    os.remove(percorsi.file_della_cartella())
    _mondo_del_futuro(str(programma_di_prova))
    avviso = AvvisoFinto([(dialoghi.ESCI, None)])
    monkeypatch.setattr(dialoghi.MondoIllegibile, "ShowModal", avviso)
    acceso = faulthandler.is_enabled()
    registro.avvia(str(programma_di_prova))
    try:
        assert Showdown.avvia_finestra() == Showdown.ILLEGGIBILE
    finally:
        registro.chiudi()
        if acceso and not faulthandler.is_enabled():
            faulthandler.enable(file=sys.__stderr__)
    mondo = programma_di_prova / "Mondo"
    assert (mondo / FILE_MONDO).is_file() and not (programma_di_prova / FILE_MONDO).exists()
    testo = (programma_di_prova / registro.FILE_DEGLI_ERRORI).read_text(encoding="utf-8")
    assert (f"Il mondo e i dati di gioco ora stanno nella cartella del mondo, {mondo}: li ho spostati da accanto al programma, nella "
            f"cartella {programma_di_prova}.") in testo
    assert suonati == ["salvataggio_illeggibile"] and avviso.testi[0].startswith(f"Il salvataggio del mondo, nella cartella {mondo}, c'è ma")
