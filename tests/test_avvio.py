"""
Le prove dell'avvio di MESS, Showdown.py, dalla tappa 14: l'interfaccia testuale, che le prove di prima
recitavano con un copione, se n'è andata con cli.py. Qui main con l'istanza unica sostituita: un MESS
già aperto fa chiudere subito questa copia, senza toccare il registro né la cartella del mondo; l'avvio e l'uscita si scrivono
nel registro, che all'uscita si chiude, e l'ascolto si ferma; il crash della volta prima arriva alla
finestra; un errore che ferma MESS si scrive nel registro e si dice in un messaggio che nomina il file,
col suono dell'allarme. Poi la finestra: davanti a un salvataggio rovinato il gioco si ferma senza
toccare niente, e la rete per gli errori scrive il resoconto nel registro e fa suonare l'allarme.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import faulthandler
import sys
import threading

import pytest
import wx

import istanza
import percorsi
import registro
import Showdown
from costanti import FILE_MONDO, FILE_MONDO_COPIA, VERSIONE

# Gli ascolti finti creati in ogni prova, nell'ordine.
ASCOLTI = []


class AscoltoFinto:
    """L'ascolto dell'istanza unica senza pipe: tiene la funzione che porta la finestra in primo piano."""

    def __init__(self, mostra, nome_della_pipe=None, attiva=True):
        self.mostra = mostra
        self.attiva = attiva
        self.fermo = False
        ASCOLTI.append(self)

    def ferma(self):
        self.fermo = True


@pytest.fixture(autouse=True)
def senza_sistema(monkeypatch):
    """Nessuna pipe vera, i ganci delle eccezioni rimessi a posto, il registro chiuso e faulthandler com'era."""
    ASCOLTI.clear()
    monkeypatch.setattr(istanza, "manda", lambda: False)
    monkeypatch.setattr(istanza, "Ascolto", AscoltoFinto)
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    monkeypatch.setattr(threading, "excepthook", threading.excepthook)
    acceso = faulthandler.is_enabled()
    yield
    registro.chiudi()
    if acceso and not faulthandler.is_enabled():
        faulthandler.enable(file=sys.__stderr__)


def _non_si_apre(*_argomenti, **_opzioni):
    pytest.fail("la finestra non doveva aprirsi")


def test_un_mess_gia_aperto_fa_chiudere_questa_copia(monkeypatch, cartella_di_prova, programma_di_prova):
    monkeypatch.setattr(istanza, "manda", lambda: True)
    monkeypatch.setattr(Showdown, "avvia_finestra", _non_si_apre)
    assert Showdown.main([]) == 0
    assert ASCOLTI == [] and list(cartella_di_prova.iterdir()) == []
    assert [p.name for p in programma_di_prova.iterdir()] == [percorsi.FILE_DELLA_CARTELLA]


def test_la_pipe_presa_da_una_copia_partita_insieme(monkeypatch, cartella_di_prova, programma_di_prova):
    risposte = iter([False, True])
    monkeypatch.setattr(istanza, "manda", lambda: next(risposte))
    monkeypatch.setattr(istanza, "Ascolto", lambda mostra: AscoltoFinto(mostra, attiva=False))
    monkeypatch.setattr(Showdown, "avvia_finestra", _non_si_apre)
    assert Showdown.main([]) == 0
    assert list(cartella_di_prova.iterdir()) == []
    assert [p.name for p in programma_di_prova.iterdir()] == [percorsi.FILE_DELLA_CARTELLA]


def test_l_avvio_e_l_uscita_nel_registro(monkeypatch, programma_di_prova):
    ricevuti = []

    class FinestraFinta:
        def __init__(self):
            self.chiamate = 0

        def porta_in_primo_piano(self):
            self.chiamate += 1

    aperta = FinestraFinta()

    def finestra(crash_precedente, finestre):
        ricevuti.append(crash_precedente)
        # Prima che la finestra ci sia, la richiesta di un'altra copia non fa niente; poi la porta in primo piano.
        ASCOLTI[0].mostra()
        finestre.append(aperta)
        ASCOLTI[0].mostra()
        assert (programma_di_prova / registro.FILE_DEL_CRASH).exists()
        return Showdown.APERTA

    monkeypatch.setattr(Showdown, "avvia_finestra", finestra)
    monkeypatch.setattr(wx, "CallAfter", lambda funzione, *a, **k: funzione(*a, **k))
    assert Showdown.main([]) == 0
    assert ricevuti == [None] and aperta.chiamate == 1 and ASCOLTI[0].fermo
    testo = (programma_di_prova / registro.FILE_DEGLI_ERRORI).read_text(encoding="utf-8")
    assert f"MESS {VERSIONE} si avvia." in testo and testo.rstrip().endswith("MESS si chiude.")
    assert not (programma_di_prova / registro.FILE_DEL_CRASH).exists()


def test_il_salvataggio_illeggibile_da_il_codice_uno(monkeypatch, programma_di_prova):
    monkeypatch.setattr(Showdown, "avvia_finestra", lambda *_a: Showdown.ILLEGGIBILE)
    assert Showdown.main([]) == 1
    registro.chiudi()
    assert (programma_di_prova / registro.FILE_DEGLI_ERRORI).read_text(encoding="utf-8").rstrip().endswith("MESS si ferma: il salvataggio non si legge.")


@pytest.mark.parametrize(("esito", "codice"), [(Showdown.SENZA_CARTELLA, 0), (Showdown.NON_SPOSTATI, 1)])
def test_gli_esiti_della_cartella_del_mondo(monkeypatch, programma_di_prova, esito, codice):
    # Dal 23 ottobre 2026: uscire perché la cartella del mondo non c'è è una scelta, i dati che non si spostano un guasto.
    monkeypatch.setattr(Showdown, "avvia_finestra", lambda *_a: esito)
    assert Showdown.main([]) == codice
    registro.chiudi()
    assert (programma_di_prova / registro.FILE_DEGLI_ERRORI).read_text(encoding="utf-8").rstrip().endswith(Showdown.ESITI[esito][1])


def test_il_crash_della_volta_prima_arriva_alla_finestra(monkeypatch, programma_di_prova):
    (programma_di_prova / registro.FILE_DEL_CRASH).write_text("Fatal Python error: Aborted\n", encoding="utf-8")
    ricevuti = []
    monkeypatch.setattr(Showdown, "avvia_finestra", lambda crash_precedente, finestre: ricevuti.append(crash_precedente) or Showdown.APERTA)
    assert Showdown.main([]) == 0
    assert ricevuti == [str(programma_di_prova / registro.FILE_DEL_CRASH_PRECEDENTE)]


def test_l_errore_fatale(app_wx, monkeypatch, programma_di_prova, suonati, capsys):
    def guasto(*_argomenti):
        raise RuntimeError("guasto")

    messaggi = []
    monkeypatch.setattr(Showdown, "avvia_finestra", guasto)
    monkeypatch.setattr(wx, "MessageBox", lambda testo, titolo, *a, **k: messaggi.append((testo, titolo)))
    assert Showdown.main([]) == 1
    assert messaggi == [(f"MESS si è fermato per un errore imprevisto: RuntimeError, guasto. Il resoconto completo è nel file MESS - Errori.log, "
                         f"nella cartella {programma_di_prova}: allegalo quando chiedi aiuto.", "MESS si è fermato")]
    assert suonati == ["errore_imprevisto"] and ASCOLTI[0].fermo
    testo = (programma_di_prova / registro.FILE_DEGLI_ERRORI).read_text(encoding="utf-8")
    assert "Traceback (most recent call last):" in testo and "RuntimeError: guasto" in testo and "MESS si ferma per un errore fatale." in testo
    # Da sorgente la traccia va anche sulla console, come prima.
    assert "RuntimeError: guasto" in capsys.readouterr().err
    assert not (programma_di_prova / registro.FILE_DEL_CRASH).exists()


def test_il_salvataggio_rovinato_ferma_il_gioco(app_wx, monkeypatch, cartella_di_prova, suonati):
    (cartella_di_prova / FILE_MONDO).write_text("non è un salvataggio", encoding="utf-8")
    messaggi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: messaggi.append(testo))
    assert Showdown.avvia_finestra() == Showdown.ILLEGGIBILE
    assert len(messaggi) == 1 and "il gioco si ferma qui senza salvare nulla" in messaggi[0]
    assert suonati == ["salvataggio_illeggibile"]
    assert (cartella_di_prova / FILE_MONDO).read_text(encoding="utf-8") == "non è un salvataggio"
    assert not (cartella_di_prova / FILE_MONDO_COPIA).exists()


def test_la_rete_per_gli_errori(monkeypatch, cartella_di_prova, suonati, capsys):
    detti = []

    class FinestraFinta:
        vera = True

        def __bool__(self):
            return self.vera

        def errore_imprevisto(self, tipo, valore):
            detti.append((tipo, str(valore)))

    finestra = FinestraFinta()
    monkeypatch.setattr(wx, "CallAfter", lambda funzione, *a, **k: funzione(*a, **k))
    # Il gancio dei fili di prima, al posto di quello di pytest, che segnalerebbe l'eccezione di prova.
    fili = []
    monkeypatch.setattr(threading, "excepthook", lambda argomenti: fili.append(argomenti.exc_type))
    registro.avvia(str(cartella_di_prova))
    Showdown._rete_per_gli_errori(finestra)
    try:
        raise ValueError("nel comando")
    except ValueError:
        sys.excepthook(*sys.exc_info())
    assert detti == [(ValueError, "nel comando")] and suonati == []
    # La finestra che non c'è più lascia l'allarme.
    finestra.vera = False
    try:
        raise KeyError("dopo la chiusura")
    except KeyError:
        sys.excepthook(*sys.exc_info())
    assert suonati == ["errore_imprevisto"]
    # Gli altri fili vanno soltanto nel registro.
    try:
        raise OSError("nel filo")
    except OSError:
        threading.excepthook(threading.ExceptHookArgs((*sys.exc_info(), None)))
    assert suonati == ["errore_imprevisto"] and len(detti) == 1 and fili == [OSError]
    registro.chiudi()
    testo = (cartella_di_prova / registro.FILE_DEGLI_ERRORI).read_text(encoding="utf-8")
    assert "ValueError: nel comando" in testo and "KeyError: 'dopo la chiusura'" in testo and "OSError: nel filo" in testo
    assert "ValueError: nel comando" in capsys.readouterr().err
