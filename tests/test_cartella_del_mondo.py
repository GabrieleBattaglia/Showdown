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
import functools
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
import percorsi
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


def test_la_data_dal_salvataggio_o_dal_file(tmp_path):
    assert cdm.salvato(tmp_path) == (None, False)
    file = _salva_in(str(tmp_path), OGGI)
    assert cdm.salvato(tmp_path) == (OGGI, True)
    # Un salvataggio che non si legge dice la data del suo file.
    with open(file, "wb") as f:
        f.write(b"rovinato")
    momento = datetime.datetime(2026, 10, 20, 8, 30).timestamp()
    os.utime(file, (momento, momento))
    assert cdm.salvato(tmp_path) == (datetime.datetime(2026, 10, 20, 8, 30), False)


def test_le_frasi_della_data_e_del_piu_recente():
    assert testi.quando_salvato(OGGI, True) == "è stato salvato il 23 ottobre 2026 alle 18:40"
    assert testi.quando_salvato(datetime.datetime(2026, 10, 8, 9, 0), True) == "è stato salvato l'8 ottobre 2026 alle 09:00"
    assert testi.quando_salvato(OGGI, False).startswith("ha il file datato il 23 ottobre 2026 alle 18:40: il salvataggio non dice")
    assert testi.quando_salvato(None, False) == "non è ancora stato salvato"
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
    with open(percorsi.file_della_cartella(), "w", encoding="utf-8") as f:
        f.write("rotto")
    assert cdm.problema_della_cartella().startswith(f"il file {percorsi.FILE_DELLA_CARTELLA}, accanto al programma, non si legge")
    os.remove(percorsi.file_della_cartella())
    (programma_di_prova / "Mondo").write_text("un file, non una cartella", encoding="utf-8")
    assert cdm.problema_della_cartella().startswith(f"la cartella {programma_di_prova / 'Mondo'} non si può creare")


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
    finto = AvvisoFinto([(dialoghi.RIPROVA, None), (dialoghi.RIPROVA, lambda: penna.mkdir(parents=True))])
    monkeypatch.setattr(dialoghi.CartellaAssente, "ShowModal", finto)
    assert Showdown.prepara_la_cartella() == (None, None)
    assert suonati == ["cartella_assente", "cartella_assente"]
    assert finto.testi[0].splitlines()[0] == f"MESS non trova la cartella del mondo: la cartella {penna} non c'è."
    assert "Poi scegli Riprova." in finto.testi[0] and "\n\n" not in finto.testi[0]
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
    assert Showdown.prepara_la_cartella() == (None, None)
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
    assert Showdown.prepara_la_cartella() == (None, None)
    assert percorsi.cartella() == str(vuota) and suonati == ["cartella_assente", "cartella_mondo", "domanda"]


def test_i_dati_accanto_al_programma_passano_nella_cartella_del_mondo(avvio, suonati, programma_di_prova):
    os.remove(percorsi.file_della_cartella())
    _dati_di_prova(programma_di_prova, "di prima")
    prima = _albero(programma_di_prova)
    esito, notizia = Showdown.prepara_la_cartella()
    mondo = programma_di_prova / "Mondo"
    assert esito is None and _albero(mondo) == prima and _albero(programma_di_prova) == {os.path.join("Mondo", nome): dati for nome, dati in prima.items()}
    assert notizia == (f"Il mondo e i dati di gioco ora stanno nella cartella del mondo, {mondo}: li ho spostati da accanto al programma, nella "
                       f"cartella {programma_di_prova}. Dove tenerli si sceglie con Cartella del mondo, nel menu Impostazioni.")
    # Il suono lo fa la finestra, quando è comparsa.
    assert suonati == []
    # Alla partenza seguente non c'è più niente da spostare.
    assert Showdown.prepara_la_cartella() == (None, None)


def test_se_la_cartella_del_mondo_ne_ha_gia_uno_quelli_di_prima_vanno_in_riserva(avvio, programma_di_prova, monkeypatch):
    os.remove(percorsi.file_della_cartella())
    mondo = programma_di_prova / "Mondo"
    _dati_di_prova(mondo, "della cartella")
    _dati_di_prova(programma_di_prova, "di prima")
    prima_mondo = _albero(mondo)
    monkeypatch.setattr(cdm, "adesso", lambda: ADESSO)
    _esito, notizia = Showdown.prepara_la_cartella()
    riserva = mondo / "Riserva 2026-10-23 19.05"
    assert {nome: dati for nome, dati in _albero(mondo).items() if not nome.startswith("Riserva")} == prima_mondo
    assert _albero(riserva)[FILE_MONDO] == f"di prima {FILE_MONDO}".encode()
    assert "che resta quello in uso" in notizia and str(riserva) in notizia


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
    assert Showdown.prepara_la_cartella() == (Showdown.NON_SPOSTATI, None)
    assert suonati == ["salvataggio_non_riuscito"]
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


def test_il_comando_di_riapertura(monkeypatch, programma_di_prova):
    assert istanza.comando_di_riapertura(77) == [sys.executable, str(programma_di_prova / "Showdown.py"), "--attendi", "77"]
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert istanza.comando_di_riapertura(77) == [sys.executable, "--attendi", "77"]
    lanciati = []
    monkeypatch.setattr(istanza.subprocess, "Popen", lambda comando, **opzioni: lanciati.append((comando, opzioni)))
    istanza.riapri()
    assert lanciati == [([sys.executable, "--attendi", str(os.getpid())], {"cwd": str(programma_di_prova), "close_fds": True})]


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
    assert suonati == ["cartella_mondo", "annullato", "cartella_mondo", "annullato"]


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
    assert finestra.chiusa and percorsi.cartella() == str(dropbox) and suonati[-1] == "cartella_cambiata"


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
    assert suonati == ["cartella_mondo", "salvataggio_non_riuscito"]
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
