"""
Il calendario dei tornei nel mondo di MESS: le edizioni, i sorteggi, le giornate e le chiusure.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-14 con la tappa 12, decisione D32 e punto 5 del progetto. È la regia dei tornei nel
mondo: ogni giorno simulato, dopo l'allenamento e prima delle sfide e delle mosse del computer, apre
le edizioni secondo la ricorrenza dei modelli di torneo, fa le iscrizioni automatiche, sorteggia le
edizioni che cominciano, fa giocare a ogni sede la sua giornata e chiude le sedi finite. Le regole
delle iscrizioni stanno in iscrizioni.py, le chiusure in premiazioni.py, il motore delle fasi in
tornei.py; qui sta lo stato, che si salva col mondo nel formato 7.
Le edizioni si aprono da sole: per ogni modello attivo e valido la prossima data della ricorrenza dopo
l'ultima apertura e dopo oggi, se le sue iscrizioni cominciano oggi o prima; anche più d'una, se le
iscrizioni durano più del periodo. Il calendario si lega all'identificativo del modello, che non cambia
con la rinomina. Ogni edizione congela una copia del suo modello e della sua formula, così gli editor
cambiano soltanto le edizioni future, D9 e D32. Se un modello o una formula non si leggono, il
calendario apre soltanto le edizioni dei modelli validi, e il riepilogo lo dice: niente si ferma in
silenzio.
Al sorteggio chi si è ritirato dall'attività o è uscito di scena da iscritto lascia l'edizione, col
rimborso, dalla verifica del 15 ottobre 2026; poi un'edizione sotto il minimo si annulla con i rimborsi,
risposta 19; le altre si dividono
in sedi parallele, ciascuna un torneo col suo seme, e ogni iscritto, tranne i convocati al mondiale,
aggiorna la data del ritmo. Gli incontri dei tuoi tesserati si giocano col motore vero, con le
fotografie per riascoltarli; tutti gli altri con l'esito rapido. Chi non può giocare non si presenta
e perde a tavolino; l'acciaccato gioca col suo calo; ogni incontro dopo il primo del giorno parte con un
quarto delle azioni già giocate, risposta 5. Le sedi concluse restano due settimane intere, per il
pannello; gli incontri dei tuoi dell'ultima edizione conclusa di ogni modello restano nelle differite,
e l'albo d'oro tiene tutto per sempre.
Dal commit delle sfide, la Coppa delle polisportive, punto 8.8: all'apertura si qualificano per
gloria le polisportive che convocano una squadra valida, ciascuna con la sua rosa, che in quei giorni
resta impegnata; al sorteggio chi ha chiuso lascia il posto alla prima esclusa; ogni incontro schiera
i tre migliori sani della rosa, e chi non ha più una squadra valida perde a tavolino, 31 a 0. Gli
impegni del calendario comprendono le rose della coppa e le sfide accettate, così l'iscrizione
automatica non manda nessuno a un torneo nei giorni in cui ha già da giocare.
"""

import copy
import datetime
import os
import random
import types

import classe
import esito_rapido
import esperienza
import formule
import infortuni
import iscrizioni
import modelli_torneo
import premiazioni
import sfide
import tornei
from costanti import CONSERVAZIONE_TORNEI_CONCLUSI_GIORNI, FATICA_RESIDUA_GIORNATA, GIOCATORI_AL_TAVOLO
from motore import ESSENZIALE, SQUADRE, TAVOLINO, Incontro, Squadra, a_tavolino, formato_singolare
from partita import MotorePartita, differita_singolare, differita_squadre
from premiazioni import Albo
from utilita import data_breve


def _giorno(data):
    return data.date() if isinstance(data, datetime.datetime) else data


def _data(testo):
    return datetime.date.fromisoformat(testo) if isinstance(testo, str) else testo


def _controlla(condizione, motivo):
    if not condizione:
        raise ValueError(motivo)


def _intero(valore):
    return isinstance(valore, int) and not isinstance(valore, bool)


class Edizione:
    """
    Un'edizione di un modello, con le iscrizioni aperte: il modello e la formula congelati, la data
    d'inizio e quella d'apertura, il numero dell'edizione del modello, i giorni di gioco al massimo, e
    gli iscritti, ciascuno col club al momento dell'iscrizione, la quota pagata e da dove viene:
    computer, mano, automatica, libero o qualificato. Al mondiale, esclusi sono i convocati che hanno
    lasciato il posto.
    """

    def __init__(self, id_edizione, modello, formula, data_inizio, data_apertura, numero, durata, iscritti=None, esclusi=None):
        self.id = id_edizione
        self.modello = modello
        self.formula = formula
        self.data_inizio = data_inizio
        self.data_apertura = data_apertura
        self.numero = numero
        self.durata = durata
        self.iscritti = list(iscritti or [])
        self.esclusi = list(esclusi or [])
        self.oggetto_modello = modelli_torneo.ModelloTorneo.da_dizionario(modello)

    @property
    def modello_id(self):
        return self.modello["id"]

    @property
    def nome(self):
        return self.modello["nome"]

    @property
    def individuale(self):
        return self.modello["tipo"] == modelli_torneo.INDIVIDUALE

    @property
    def sesso(self):
        return self.modello["sesso"]

    @property
    def qualificazione(self):
        return self.modello["qualificazione"]

    @property
    def importanza(self):
        return self.modello["importanza"]

    @property
    def quota(self):
        return self.modello["quota_iscrizione"]

    @property
    def minimo(self):
        return self.modello["minimo_iscritti"]

    @property
    def tetto(self):
        return formule.tetto(self.formula)

    @property
    def filtri(self):
        return any(self.modello[campo] is not None for campo in ("classe_minima", "classe_massima", "eta_minima", "eta_massima"))

    @property
    def data_fine(self):
        """L'ultimo giorno di gioco al massimo."""
        return self.data_inizio + datetime.timedelta(days=max(1, self.durata) - 1)

    def ids(self):
        return [iscritto["id"] for iscritto in self.iscritti]

    def giocatori(self):
        """I giocatori impegnati dall'edizione: gli iscritti, oppure, nella coppa, le rose delle polisportive."""
        if self.individuale:
            return self.ids()
        return [gid for iscritto in self.iscritti for gid in iscritto.get("rosa", ())]

    def iscritto(self, gid):
        return next((iscritto for iscritto in self.iscritti if iscritto["id"] == gid), None)

    def aggiungi(self, gid, club, pagato, origine, rosa=None):
        """Un iscritto, col club, la quota e l'origine; nella coppa l'iscritto è la polisportiva, con la sua rosa."""
        iscritto = {"id": gid, "club": copy.deepcopy(club), "pagato": int(pagato), "origine": origine}
        if rosa is not None:
            iscritto["rosa"] = list(rosa)
        self.iscritti.append(iscritto)

    def togli(self, gid):
        iscritto = self.iscritto(gid)
        if iscritto is not None:
            self.iscritti.remove(iscritto)
        return iscritto

    def a_dizionario(self):
        return {"id": self.id, "modello": copy.deepcopy(self.modello), "formula": copy.deepcopy(self.formula), "data_inizio": self.data_inizio.isoformat(),
                "data_apertura": self.data_apertura.isoformat(), "numero": self.numero, "durata": self.durata, "iscritti": copy.deepcopy(self.iscritti),
                "esclusi": list(self.esclusi)}

    @classmethod
    def da_dizionario(cls, dati):
        campi = {"id", "modello", "formula", "data_inizio", "data_apertura", "numero", "durata", "iscritti", "esclusi"}
        _controlla(isinstance(dati, dict) and set(dati) == campi, "Un'edizione salvata ha i campi sbagliati.")
        for campo in ("id", "numero", "durata"):
            _controlla(_intero(dati[campo]) and dati[campo] >= 0, f"Edizione: il campo {campo} non è valido.")
        problema = modelli_torneo.problema_dei_campi(dati["modello"])
        _controlla(problema is None, f"Edizione {dati['id']}: il modello congelato non va: {problema}")
        problema = formule.valida_formula(dati["formula"])
        _controlla(problema is None, f"Edizione {dati['id']}: la formula congelata non va: {problema}")
        _controlla(isinstance(dati["iscritti"], list), f"Edizione {dati['id']}: gli iscritti non sono un elenco.")
        for iscritto in dati["iscritti"]:
            rosa = iscritto.get("rosa", []) if isinstance(iscritto, dict) else None
            _controlla(isinstance(iscritto, dict) and set(iscritto) - {"rosa"} == {"id", "club", "pagato", "origine"} and iscritto["origine"] in iscrizioni.ORIGINI
                       and isinstance(rosa, list) and all(_intero(gid) for gid in rosa)
                       and _intero(iscritto["pagato"]) and iscritto["pagato"] >= 0 and (_intero(iscritto["id"]) or isinstance(iscritto["id"], str))
                       and (iscritto["club"] is None or (isinstance(iscritto["club"], dict) and set(iscritto["club"]) == {"nome", "fondazione"})),
                       f"Edizione {dati['id']}: un iscritto non è valido: {iscritto!r}")
        ids = [iscritto["id"] for iscritto in dati["iscritti"]]
        _controlla(len(ids) == len(set(ids)), f"Edizione {dati['id']}: un iscritto compare due volte.")
        try:
            inizio, apertura = datetime.date.fromisoformat(dati["data_inizio"]), datetime.date.fromisoformat(dati["data_apertura"])
        except (TypeError, ValueError):
            raise ValueError(f"Edizione {dati['id']}: le date non sono valide.") from None
        return cls(dati["id"], copy.deepcopy(dati["modello"]), copy.deepcopy(dati["formula"]), inizio, apertura, dati["numero"], dati["durata"],
                   copy.deepcopy(dati["iscritti"]), list(dati["esclusi"]))


class SedeInDifferita:
    """
    Una sede di un'edizione conclusa nelle differite, con quello che serve al pannello e ai testi per
    dire i suoi incontri come quelli di una sede vera: il modello col nome che aveva, l'edizione, il
    numero della sede, i nomi degli iscritti e la grandezza dei tabelloni. Non è un torneo: non ha
    classifiche, che restano nell'albo d'oro.
    """

    stato = tornei.CONCLUSO

    def __init__(self, voce, sede):
        self.voce = voce
        self.dati = sede
        self.modello = {"id": voce["modello"], "nome": voce["nome"]}
        self.edizione = voce["edizione"]
        self.numero = voce["numero"]
        self.sede = sede["sede"]
        self.data_inizio = voce["data"]
        self.squadre = voce["squadre"]
        self.info = {gid: {"nome": sede["nomi"].get(str(gid), str(gid))} for i in sede["incontri"] for gid in (i.a, i.b) if gid is not None}
        self.fasi = {int(indice): types.SimpleNamespace(grandezza=grandezza) for indice, grandezza in sede["grandezze"].items()}

    def incontri(self):
        return list(self.dati["incontri"])


class Calendario:
    """
    Lo stato del calendario nel mondo: il contatore degli identificativi, l'ultima apertura e il numero
    dell'ultima edizione di ogni modello, le edizioni con le iscrizioni aperte, le sedi in corso e
    quelle concluse da meno di due settimane, il numero dell'edizione di ogni sede, gli incontri dei tuoi
    tesserati dell'ultima edizione conclusa di ogni modello, le iscrizioni dei tuoi già saltate per la
    cassa, quelle che hai tolto, e l'albo d'oro.
    Le differite, dalla revisione del 14 ottobre 2026, si leggono dal pannello anche dopo le due
    settimane, come vuole D32, «per il torneo in corso e l'ultimo concluso»: per ogni modello l'ultima
    edizione con i tuoi, sede per sede, con i nomi e i tabelloni che servono a dire gli incontri. In
    memoria gli incontri sono gli stessi oggetti delle sedi concluse, così un risultato svelato da una
    parte lo è anche dall'altra; alla lettura del salvataggio si ricollegano.
    """

    def __init__(self):
        self.prossimo_id = 1
        self.ultime_aperture = {}
        self.numeri = {}
        self.edizioni = []
        self.tornei = []
        self.conclusi = []
        self.numeri_dei_tornei = {}
        self.differite = {}
        self.saltate = []
        self.tolte = []
        self.albo = Albo()
        # Non si salvano: la memoria della forza del giorno e i giorni di gioco di ogni sede.
        self._memoria_forza = {}
        self._durate = {}

    # Gli identificativi e le ricerche.

    def nuovo_id(self):
        nuovo = self.prossimo_id
        self.prossimo_id += 1
        return nuovo

    def numero_di(self, torneo):
        return self.numeri_dei_tornei.get(torneo.id, 0)

    def edizione(self, id_edizione):
        return next((ed for ed in self.edizioni if ed.id == id_edizione), None)

    def torneo(self, id_torneo):
        return next((t for t in (*self.tornei, *self.conclusi) if t.id == id_torneo), None)

    def iscritti_alle_edizioni(self):
        """Gli identificativi di chi è iscritto a un'edizione aperta."""
        return {gid for ed in self.edizioni for gid in ed.ids()}

    def durata_del_torneo(self, torneo):
        """I giorni di gioco al massimo di una sede, dal suo modello e dalla sua formula congelati."""
        if torneo.id not in self._durate:
            self._durate[torneo.id] = modelli_torneo.durata_prevista(modelli_torneo.ModelloTorneo.da_dizionario(torneo.modello), torneo.formula)
        return self._durate[torneo.id]

    def _intervallo_del_torneo(self, torneo):
        inizio = _data(torneo.data_inizio)
        return inizio, inizio + datetime.timedelta(days=max(1, self.durata_del_torneo(torneo)) - 1)

    @staticmethod
    def giocatori_del_torneo(torneo):
        """I giocatori impegnati da una sede: gli iscritti, oppure, nella coppa, le rose delle polisportive."""
        if not torneo.squadre:
            return list(torneo.iscritti)
        return [gid for info in torneo.info.values() for gid in info.get("rosa", ())]

    def impegni(self, mondo, esclusa=None, con_le_iscrizioni=True):
        """
        Gli impegni di ogni giocatore nei giorni che vengono, come intervalli di date: le edizioni a cui è
        iscritto o in cui è nella rosa della coppa, tranne quella esclusa, le sedi in corso che gioca e,
        dal commit delle sfide, le sfide accettate. Senza le iscrizioni restano gli impegni che non si
        annullano, quelli che il mondiale rispetta: le sedi in corso, le rose della coppa e le sfide.
        """
        impegni = {}
        for ed in self.edizioni:
            if ed is esclusa or (ed.individuale and not con_le_iscrizioni):
                continue
            for gid in ed.giocatori():
                impegni.setdefault(gid, []).append((ed.data_inizio, ed.data_fine))
        for torneo in self.tornei:
            intervallo = self._intervallo_del_torneo(torneo)
            for gid in self.giocatori_del_torneo(torneo):
                impegni.setdefault(gid, []).append(intervallo)
        for gid, intervalli in mondo.sfide.impegni().items():
            impegni.setdefault(gid, []).extend(intervalli)
        return impegni

    def impegnati_il(self, giorno):
        """Chi ha un torneo nel giorno dato: le edizioni che giocano quel giorno e le sedi in corso, con le rose della coppa."""
        impegnati = set()
        for ed in self.edizioni:
            if ed.data_inizio <= giorno <= ed.data_fine:
                impegnati.update(ed.giocatori())
        for torneo in self.tornei:
            inizio, fine = self._intervallo_del_torneo(torneo)
            if inizio <= giorno <= fine:
                impegnati.update(self.giocatori_del_torneo(torneo))
        return impegnati

    def impegni_descritti(self, mondo, gid):
        """
        Gli impegni di un giocatore con la loro descrizione a parole e il tipo, torneo o sfida, per i
        rifiuti dell'iscrizione a mano: quadruple di inizio, fine, descrizione e tipo. Il tipo c'è dalla
        revisione del 14 ottobre 2026, perché il rifiuto diceva «due tornei» anche davanti a una sfida.
        """
        risultato = []
        for ed in self.edizioni:
            if gid in ed.giocatori():
                cosa = "l'iscrizione" if ed.individuale else "la rosa della sua polisportiva"
                risultato.append((ed.data_inizio, ed.data_fine, f"{cosa} a {ed.nome}, dal {data_breve(ed.data_inizio)}", "torneo"))
        for torneo in self.tornei:
            if gid in self.giocatori_del_torneo(torneo):
                inizio, fine = self._intervallo_del_torneo(torneo)
                risultato.append((inizio, fine, f"{torneo.modello['nome']}, in corso dal {data_breve(inizio)}", "torneo"))
        for s in mondo.sfide.attive:
            if s.stato == sfide.ACCETTATA and any(gid in ids for ids in s.convocati.values()):
                risultato.append((s.data_gioco, s.data_gioco, f"una sfida fra {s.sfidante['nome']} e {s.sfidata['nome']}, il {data_breve(s.data_gioco)}", "sfida"))
        return risultato

    def ha_giocato_oggi(self, gid, oggi):
        """Vero se il giocatore ha giocato oggi un incontro di torneo, per dire che impegno ha avuto; nella coppa, con la sua polisportiva."""
        testo = _giorno(oggi).isoformat()
        for torneo in (*self.tornei, *self.conclusi):
            if torneo.squadre:
                chi = next((cid for cid, info in torneo.info.items() if gid in info.get("rosa", ())), None)
            else:
                chi = gid if gid in torneo.info else None
            if chi is not None and any(i.data == testo and i.esito not in (tornei.RIPOSO, tornei.TAVOLINO_DOPPIO) for i in torneo.incontri_di(chi)):
                return True
        return False

    def da_svelare(self):
        """
        Gli incontri dei tuoi ancora da ascoltare, risposta 18 di Gabriele: nelle sedi in corso, in quelle
        concluse di recente e nelle ultime edizioni concluse delle differite, ciascuno una volta sola.
        """
        visti = set()
        risultato = []
        for i in [i for torneo in (*self.tornei, *self.conclusi) for i in torneo.incontri()] + [i for _voce, sede in self.sedi_in_differita() for i in sede.incontri()]:
            if id(i) not in visti and i.giocato and i.differita and not i.svelato:
                visti.add(id(i))
                risultato.append(i)
        return risultato

    def svela_tutti(self):
        """Mostra tutti i risultati, la regola che Gabriele ha aggiunto alla risposta 18: svela in un colpo solo gli incontri dei tuoi da ascoltare, e dice quanti."""
        incontri = self.da_svelare()
        for incontro in incontri:
            incontro.svelato = True
        return len(incontri)

    def conta_saltata(self, gid, id_edizione):
        """Vero la prima volta che l'iscrizione automatica di un tuo tesserato salta un'edizione per la cassa: si conta una volta sola."""
        if [gid, id_edizione] in self.saltate:
            return False
        self.saltate.append([gid, id_edizione])
        return True

    def ricorda_tolta(self, gid, id_edizione):
        """Un'iscrizione che l'utente ha tolto: l'iscrizione automatica non rimette il giocatore in quell'edizione, fino al suo sorteggio."""
        if [gid, id_edizione] not in self.tolte:
            self.tolte.append([gid, id_edizione])

    def tolte_per_giocatore(self):
        """Le edizioni tolte dall'utente, per giocatore: un dizionario dall'identificativo all'insieme delle edizioni."""
        per_giocatore = {}
        for gid, id_edizione in self.tolte:
            per_giocatore.setdefault(gid, set()).add(id_edizione)
        return per_giocatore

    def conserva_differite(self, torneo, tuoi):
        """
        Gli incontri dei tuoi tesserati della sede conclusa, per riascoltarli, al posto di quelli
        dell'edizione di prima dello stesso modello: gli stessi oggetti della sede, con i nomi degli
        iscritti e la grandezza dei tabelloni, che servono a dirli a parole.
        """
        incontri = [i for i in torneo.incontri() if i.differita and (i.a in tuoi or i.b in tuoi)]
        if not incontri:
            return
        sede = {"sede": torneo.sede, "nomi": {str(gid): torneo.info[gid]["nome"] for i in incontri for gid in (i.a, i.b) if gid is not None},
                "grandezze": {str(f.indice): f.grandezza for f in torneo.fasi if f.tipo == formule.TABELLONE}, "incontri": incontri}
        voce = self.differite.get(torneo.modello["id"])
        if voce is not None and voce["edizione"] == torneo.edizione:
            voce["sedi"].append(sede)
            return
        self.differite[torneo.modello["id"]] = {"modello": torneo.modello["id"], "edizione": torneo.edizione, "numero": self.numero_di(torneo),
                                                "nome": torneo.modello["nome"], "data": torneo.data_inizio, "squadre": torneo.squadre, "sedi": [sede]}

    def sedi_in_differita(self):
        """Le sedi delle ultime edizioni concluse con i tuoi, dalla più recente: coppie della voce del modello e della sede, come SedeInDifferita."""
        coppie = []
        for voce in sorted(self.differite.values(), key=lambda v: (v["data"], v["nome"]), reverse=True):
            for sede in sorted(voce["sedi"], key=lambda s: s["sede"]):
                coppie.append((voce, SedeInDifferita(voce, sede)))
        return coppie

    # Il giorno.

    def giorno(self, mondo, data, rapporto):
        """
        Il giorno del calendario, nell'ordine: le aperture, le iscrizioni automatiche, i sorteggi, le
        giornate delle sedi in corso con le chiusure, lo sfoltimento dei conclusi. Restituisce i nomi
        delle polisportive che hanno vinto qualcosa, perché ricalcolino subito la gloria.
        """
        self._memoria_forza = {}
        gestore = modelli_torneo.GestoreModelli()
        if not os.path.isdir(gestore.cartella()):
            gestore.crea_predefiniti()
        modelli, _scartati = gestore.modelli()
        formule_valide, _scartate = formule.leggi()
        if gestore.problemi():
            rapporto["calendario_con_problemi"] += 1
        self.apri_edizioni(mondo, data, modelli, formule_valide, rapporto)
        iscrizioni.automatiche(mondo, self, data, rapporto)
        self.sorteggi(mondo, data, rapporto)
        toccate = self.gioca(mondo, data, rapporto)
        self.sfoltisci(data)
        return toccate

    def apri_edizioni(self, mondo, data, modelli, formule_valide, rapporto):
        """Le edizioni che aprono oggi le iscrizioni, per ogni modello attivo e valido; i mondiali convocano subito."""
        oggi = _giorno(data)
        domani = oggi + datetime.timedelta(days=1)
        for modello in modelli:
            if not modello.attivo or modelli_torneo.problema(modello, formule_valide) is not None:
                continue
            formula = modelli_torneo.formula_del_modello(modello, formule_valide)
            while True:
                ultima = self.ultime_aperture.get(modello.id)
                dopo = domani if ultima is None else max(domani, _data(ultima) + datetime.timedelta(days=1))
                inizio = modelli_torneo.prossima_data(modello, dopo)
                if inizio - datetime.timedelta(days=modello.giorni_iscrizione) > oggi:
                    break
                numero = self.numeri.get(modello.id, 0) + 1
                self.numeri[modello.id] = numero
                self.ultime_aperture[modello.id] = inizio.isoformat()
                ed = Edizione(self.nuovo_id(), modello.a_dizionario(), copy.deepcopy(formula), inizio, oggi, numero,
                              modelli_torneo.durata_prevista(modello, formula))
                self.edizioni.append(ed)
                if ed.qualificazione == modelli_torneo.PUNTI_ANNO:
                    iscrizioni.convoca_mondiale(mondo, self, ed, rapporto)
                elif ed.qualificazione == modelli_torneo.GLORIA:
                    sfide.qualifica_coppa(mondo, self, ed, rapporto)

    def sorteggi(self, mondo, data, rapporto):
        """
        Le edizioni che cominciano oggi chiudono le iscrizioni: sotto il minimo si annullano, le altre si dividono in sedi.
        Prima, al mondiale gli infortunati e chi ha lasciato l'attività cedono il posto ai sostituti, alla coppa le chiuse
        alle escluse, e dalla verifica del 15 ottobre 2026 negli altri tornei chi ha lasciato l'attività esce, col rimborso.
        """
        oggi = _giorno(data)
        for ed in [ed for ed in self.edizioni if ed.data_inizio <= oggi]:
            self.edizioni.remove(ed)
            self.saltate = [voce for voce in self.saltate if voce[1] != ed.id]
            self.tolte = [voce for voce in self.tolte if voce[1] != ed.id]
            if ed.qualificazione == modelli_torneo.PUNTI_ANNO:
                iscrizioni.sostituisci_gli_infortunati(mondo, self, ed, rapporto)
            elif ed.qualificazione == modelli_torneo.GLORIA:
                sfide.rimpiazza_le_chiuse(mondo, self, ed, rapporto)
            elif ed.individuale:
                iscrizioni.togli_chi_ha_lasciato(mondo, ed)
            if len(ed.iscritti) < ed.minimo:
                self._annulla(mondo, ed, rapporto)
                continue
            self._dividi_in_sedi(mondo, ed, data)

    def _annulla(self, mondo, ed, rapporto):
        """L'annullamento sotto il minimo, risposta 19: le quote tornano, i tuoi lo sanno; il mondiale che non si disputa resta nell'albo."""
        rapporto["edizioni_annullate"] += 1
        tuoi = []
        for iscritto in ed.iscritti:
            iscrizioni.rimborsa(mondo, iscritto)
            if not ed.individuale:
                poli = iscrizioni.polisportiva_del_club(mondo, iscritto["club"])
                if sfide.tua(poli):
                    tuoi.append(poli)
                    mondo.annota(poli, f"{ed.nome} del {data_breve(ed.data_inizio)} è annullata: le qualificate erano meno di {ed.minimo}.")
                continue
            g = mondo.giocatori.get(iscritto["id"])
            if g is not None and iscrizioni.tuo(mondo, g):
                tuoi.append(g)
                mondo.annota(g, f"{ed.nome} del {data_breve(ed.data_inizio)} è annullato: gli iscritti erano meno di {ed.minimo}, e la quota torna.")
        if tuoi:
            rapporto["tue_edizioni_annullate"] += 1
            rapporto["notizie"].append(f"{ed.nome} del {data_breve(ed.data_inizio)} è annullato per pochi iscritti.")
        if ed.qualificazione != modelli_torneo.NESSUNA:
            self.albo.non_disputato(ed, ed.numero)

    def _forza_del_club(self, mondo, iscritto):
        """La forza di una polisportiva al sorteggio della coppa: la media del punteggio di classe dei tre titolari che schiererebbe oggi."""
        poli = iscrizioni.polisportiva_del_club(mondo, iscritto["club"])
        squadra = sfide.schiera_coppa(mondo, poli, iscritto["rosa"]) if poli is not None else None
        if squadra is None:
            return 0.0
        return sum(classe.punteggio(g) for g in squadra[:GIOCATORI_AL_TAVOLO]) / GIOCATORI_AL_TAVOLO

    def _dividi_in_sedi(self, mondo, ed, data):
        """
        Il sorteggio: gli iscritti dalla classe di oggi, a serpentina nelle sedi, ciascuna un torneo col
        suo seme; la data del ritmo si aggiorna. Nella coppa gli iscritti sono le polisportive, con la loro rosa.
        """
        forze = {}
        for iscritto in ed.iscritti:
            if not ed.individuale:
                forze[iscritto["id"]] = self._forza_del_club(mondo, iscritto)
                continue
            g = mondo.giocatori.get(iscritto["id"])
            forze[iscritto["id"]] = classe.punteggio(g) if g is not None else 0.0
        ordinati = sorted(forze, key=lambda gid: (-forze[gid], gid))
        per_id = {iscritto["id"]: iscritto for iscritto in ed.iscritti}
        for numero_sede, ids in enumerate(tornei.dividi_in_sedi(ordinati, ed.tetto, ed.minimo), start=1):
            info = {}
            for gid in ids:
                if not ed.individuale:
                    info[gid] = {"nome": gid, "sesso": None, "club": per_id[gid]["club"], "forza": forze[gid], "pagato": 0, "rosa": list(per_id[gid]["rosa"])}
                    continue
                g = mondo.giocatori.get(gid)
                nome = f"{g.nome} {g.cognome}" if g is not None else f"Giocatore {gid}"
                info[gid] = {"nome": nome, "sesso": g.sesso if g is not None else None, "club": per_id[gid]["club"], "forza": forze[gid],
                             "pagato": per_id[gid]["pagato"]}
            id_torneo = self.nuovo_id()
            seme = random.Random(f"MESS-torneo-{id_torneo}-{ed.data_inizio.isoformat()}").getrandbits(63)
            torneo = tornei.Torneo(id_torneo, ed.id, numero_sede, ed.modello, ed.formula, ed.data_inizio, seme, info)
            self.tornei.append(torneo)
            self.numeri_dei_tornei[id_torneo] = ed.numero
        for iscritto in ed.iscritti:
            g = mondo.giocatori.get(iscritto["id"]) if ed.individuale else None
            if g is not None and iscritto["origine"] != iscrizioni.QUALIFICATO:
                iscrizioni.aggiorna_ritmo(g, data, ed.id)

    def gioca(self, mondo, data, rapporto):
        """La giornata di ogni sede in corso, e la chiusura delle sedi finite; restituisce le polisportive che hanno vinto qualcosa."""
        motore = MotorePartita(mondo)
        toccate = set()
        for torneo in list(self.tornei):
            _giocati, finito = torneo.giornata(lambda incontro, azioni, t=torneo: self._gioca_incontro(mondo, motore, t, incontro, azioni, rapporto), data)
            if finito:
                self.tornei.remove(torneo)
                self.conclusi.append(torneo)
                if torneo.stato == tornei.CONCLUSO:
                    toccate |= premiazioni.chiudi(mondo, self, torneo, data, rapporto)
        return toccate

    def _presente(self, mondo, gid):
        """Il giocatore che si presenta all'incontro, oppure None: chi è infortunato, ritirato o uscito di scena non si presenta."""
        g = mondo.giocatori.get(gid)
        if g is None or gid in mondo._ids_morti_processati_sessione or g.ritirato or not g.puo_giocare:
            return None
        return g

    def _gioca_incontro(self, mondo, motore, torneo, incontro, azioni_del_giorno, rapporto):
        """
        Un incontro di una sede individuale: il tavolino per chi non si presenta, il motore vero se gioca
        un tuo tesserato, con le fotografie per la differita, l'esito rapido per tutti gli altri; con le
        basi d'infortunio, i cali degli acciacchi di oggi e le azioni iniziali della giornata. Gli incontri
        della coppa li gioca _gioca_squadre.
        """
        if torneo.squadre:
            return self._gioca_squadre(mondo, motore, torneo, incontro, azioni_del_giorno, rapporto)
        importanza = torneo.modello["importanza"]
        ga, gb = self._presente(mondo, incontro.a), self._presente(mondo, incontro.b)
        if ga is None and gb is None:
            rapporto["incontri_tavolino"] += 1
            return {"esito": tornei.TAVOLINO_DOPPIO, "vince": None, "set": [], "set_giocati": 0}
        formato = formato_singolare(incontro.set_al_meglio)
        if ga is None or gb is None:
            return self._tavolino(mondo, motore, incontro, ga, gb, formato, rapporto)
        rapporto["incontri_torneo"] += 1
        oggi = mondo.datetime_corrente_simulazione
        basi = {g.id: infortuni.probabilita_base(g) for g in (ga, gb)}
        cali = {g.id: calo for g in (ga, gb) if (calo := infortuni.calo_acciacco(g, oggi))} or None
        iniziali = {gid: round(FATICA_RESIDUA_GIORNATA * n) for gid, n in azioni_del_giorno.items() if n} or None
        tuoi = [g for g in (ga, gb) if iscrizioni.tuo(mondo, g)]
        differita = None
        if tuoi:
            differita = differita_singolare(ga, gb, basi, cali, iniziali, incontro.set_al_meglio)
            risultato = Incontro(ga, gb, formato, seme=incontro.seme, dettaglio=ESSENZIALE, basi_infortunio=basi, cali=cali, azioni_iniziali=iniziali).gioca()
            motore.registra(risultato, esperienza.TORNEO, importanza, diario=True, solo_tuoi=True)
        else:
            risultato = esito_rapido.gioca(ga, gb, formato, incontro.seme, basi_infortunio=basi, azioni_iniziali=iniziali, cali=cali, memoria=self._memoria_forza)
            motore.registra(risultato, esperienza.TORNEO, importanza, diario=False)
        self._conta(mondo, risultato, tuoi, rapporto)
        return {"esito": risultato.esito, "vince": risultato.vincitore, "set": [list(s) for s in risultato.set], "set_giocati": risultato.set_giocati,
                "motore": "vero" if tuoi else "rapido", "differita": differita, "azioni": {gid: risultato.statistiche[gid].azioni for gid in risultato.parti}}

    @staticmethod
    def _conta(mondo, risultato, tuoi, rapporto):
        """I contatori del riepilogo: ritiri, infortuni e acciacchi in gara del mondo, e quelli dei tuoi."""
        rapporto["incontri_ritiro"] += risultato.esito == "ritiro"
        rapporto["infortuni_in_gara"] += len(risultato.infortuni)
        rapporto["acciacchi_in_gara"] += len(risultato.acciacchi)
        if tuoi:
            ids = {g.id for g in tuoi}
            rapporto["tuoi_infortuni_in_gara"] += sum(1 for gid, _s, _sede in risultato.infortuni if gid in ids)
            rapporto["tuoi_acciacchi"] += sum(1 for gid, _sede in risultato.acciacchi if gid in ids)

    def _tavolino(self, mondo, motore, incontro, ga, gb, formato, rapporto):
        """Chi non si presenta perde a tavolino, 11 a 0 in ogni set: niente punti né esperienza, una voce nel diario dei tuoi, l'impegno per chi c'era."""
        rapporto["incontri_tavolino"] += 1
        assente = "A" if ga is None else "B"
        necessari = incontro.set_al_meglio // 2 + 1
        punti = formato.punti_set
        vince = "B" if assente == "A" else "A"
        presente = gb if assente == "A" else ga
        id_assente = incontro.a if assente == "A" else incontro.b
        g_assente = mondo.giocatori.get(id_assente)
        if g_assente is not None:
            a, b = (g_assente, presente) if assente == "A" else (presente, g_assente)
            motore.registra(a_tavolino(a, b, formato, assente, incontro.seme), esperienza.TORNEO)
            if iscrizioni.tuo(mondo, g_assente):
                rapporto["tuoi_tavolini"] += 1
        else:
            motore.segna_impegno(presente)
        return {"esito": tornei.TAVOLINO, "vince": vince, "set": [[punti, 0] if vince == "A" else [0, punti] for _ in range(necessari)], "set_giocati": 0}

    def _gioca_squadre(self, mondo, motore, torneo, incontro, azioni_del_giorno, rapporto):
        """
        Un incontro della coppa, punto 8.8: ogni polisportiva schiera i tre migliori sani della sua rosa,
        e chi non ha più una squadra valida, o ha chiuso, perde a tavolino, 31 a 0. Il motore vero se
        gioca una tua polisportiva, con le fotografie per la differita; l'esito rapido fra quelle del
        computer. Punti allenamento ed esperienza dei titolari come una sfida, per l'importanza; chi della
        rosa resta fuori conta da riserva, risposta 15. Dalla lettura 12 delle decisioni di Gabriele del
        14 ottobre 2026 vale anche qui la fatica della giornata, risposta 5: chi gioca un incontro dopo il
        primo del giorno parte con un quarto delle azioni che ha già giocato, nel motore, nell'esito rapido
        e nella differita; azioni_del_giorno le dice per ogni giocatore delle due rose, e il risultato
        restituisce quelle di questo incontro.
        """
        importanza = torneo.modello["importanza"]
        gara = f"l'incontro di {torneo.modello['nome']}"
        club, squadre = {}, {}
        for lato, cid in (("A", incontro.a), ("B", incontro.b)):
            info = torneo.info[cid]
            club[lato] = iscrizioni.polisportiva_del_club(mondo, info["club"])
            squadre[lato] = sfide.schiera_coppa(mondo, club[lato], info["rosa"]) if club[lato] is not None else None
        if squadre["A"] is None and squadre["B"] is None:
            rapporto["incontri_tavolino"] += 1
            return {"esito": tornei.TAVOLINO_DOPPIO, "vince": None, "set": [], "set_giocati": 0}
        punti = SQUADRE.punti_set
        if squadre["A"] is None or squadre["B"] is None:
            rapporto["incontri_tavolino"] += 1
            assente = "A" if squadre["A"] is None else "B"
            vince = "B" if assente == "A" else "A"
            parti = []
            for lato, cid in (("A", incontro.a), ("B", incontro.b)):
                if squadre[lato] is not None:
                    parti.append(Squadra(cid, tuple(squadre[lato])))
                    continue
                poli = club[lato]
                presenti = tuple(g for gid in torneo.info[cid]["rosa"] if (g := mondo.giocatori.get(gid)) is not None and poli is not None
                                 and g.appartenenza == poli.nome)
                parti.append(Squadra(cid, presenti))
            motore.registra_squadre(a_tavolino(parti[0], parti[1], SQUADRE, assente, incontro.seme), esperienza.SFIDA, importanza, gara=gara)
            if sfide.tua(club[assente]):
                rapporto["tuoi_tavolini"] += 1
            return {"esito": TAVOLINO, "vince": vince, "set": [[punti, 0] if vince == "A" else [0, punti]], "set_giocati": 0}
        rapporto["incontri_torneo"] += 1
        sq_a, sq_b = Squadra(incontro.a, tuple(squadre["A"])), Squadra(incontro.b, tuple(squadre["B"]))
        giocatori = (*sq_a.giocatori, *sq_b.giocatori)
        basi = {g.id: infortuni.probabilita_base(g) for g in giocatori}
        cali = {g.id: calo for g in giocatori if (calo := infortuni.calo_acciacco(g, mondo.datetime_corrente_simulazione))} or None
        iniziali = {gid: round(FATICA_RESIDUA_GIORNATA * n) for gid, n in azioni_del_giorno.items() if n} or None
        tue = any(sfide.tua(p) for p in club.values())
        differita = None
        if tue:
            differita = differita_squadre(sq_a, sq_b, basi, cali, iniziali)
            risultato = Incontro(sq_a, sq_b, SQUADRE, seme=incontro.seme, dettaglio=ESSENZIALE, basi_infortunio=basi, cali=cali, azioni_iniziali=iniziali).gioca()
        else:
            risultato = esito_rapido.gioca_squadre(sq_a, sq_b, incontro.seme, basi_infortunio=basi, cali=cali, memoria=self._memoria_forza, azioni_iniziali=iniziali)
        motore.registra_squadre(risultato, esperienza.SFIDA, importanza, diario=True, solo_tuoi=True, gara=gara, aggrega="incontri")
        self._conta(mondo, risultato, [g for g in giocatori if iscrizioni.tuo(mondo, g)], rapporto)
        return {"esito": risultato.esito, "vince": risultato.vincitore, "set": [list(s) for s in risultato.set], "set_giocati": risultato.set_giocati,
                "motore": "vero" if tue else "rapido", "differita": differita,
                "azioni": {gid: s.azioni for gid, s in risultato.statistiche.items() if s.azioni}}

    def sfoltisci(self, data):
        """Le sedi concluse da più di due settimane lasciano il pannello: l'albo tiene il podio, le differite gli incontri dei tuoi."""
        limite = _giorno(data) - datetime.timedelta(days=CONSERVAZIONE_TORNEI_CONCLUSI_GIORNI)
        restano = []
        for torneo in self.conclusi:
            ultimo = max((_data(i.data) for i in torneo.incontri() if i.data), default=_data(torneo.data_inizio))
            if ultimo >= limite:
                restano.append(torneo)
            else:
                self.numeri_dei_tornei.pop(torneo.id, None)
                self._durate.pop(torneo.id, None)
        self.conclusi = restano

    # Il salvataggio.

    def a_dizionario(self):
        return {
            "prossimo_id": self.prossimo_id, "ultime_aperture": dict(self.ultime_aperture), "numeri": dict(self.numeri),
            "edizioni": [ed.a_dizionario() for ed in self.edizioni], "tornei": [t.a_dizionario() for t in self.tornei],
            "conclusi": [t.a_dizionario() for t in self.conclusi], "numeri_dei_tornei": [[k, v] for k, v in self.numeri_dei_tornei.items()],
            "differite": {mid: _differita_a_dizionario(voce) for mid, voce in self.differite.items()}, "saltate": [list(v) for v in self.saltate],
            "tolte": [list(v) for v in self.tolte], "albo": self.albo.a_dizionario(),
        }

    @classmethod
    def da_dizionario(cls, dati):
        """
        Il calendario dal salvataggio, ValueError col motivo se non va, punto 11.5: identificativi unici
        di edizioni e sedi, sotto il contatore; stati e esiti validi; ogni nome dell'albo nelle sue tabelle.
        Un giocatore che non c'è più resta nelle sedi, perché può essere uscito di scena.
        """
        campi = {"prossimo_id", "ultime_aperture", "numeri", "edizioni", "tornei", "conclusi", "numeri_dei_tornei", "differite", "saltate", "tolte", "albo"}
        _controlla(isinstance(dati, dict) and set(dati) == campi, "Il calendario salvato ha i campi sbagliati.")
        cal = cls()
        _controlla(_intero(dati["prossimo_id"]) and dati["prossimo_id"] >= 1, "Calendario: il contatore non è valido.")
        cal.prossimo_id = dati["prossimo_id"]
        _controlla(isinstance(dati["ultime_aperture"], dict) and all(isinstance(v, str) for v in dati["ultime_aperture"].values()),
                   "Calendario: le ultime aperture non sono valide.")
        cal.ultime_aperture = dict(dati["ultime_aperture"])
        _controlla(isinstance(dati["numeri"], dict) and all(_intero(v) and v >= 0 for v in dati["numeri"].values()), "Calendario: i numeri delle edizioni non sono validi.")
        cal.numeri = dict(dati["numeri"])
        cal.edizioni = [Edizione.da_dizionario(ed) for ed in dati["edizioni"]]
        cal.tornei = [tornei.Torneo.da_dizionario(t) for t in dati["tornei"]]
        cal.conclusi = [tornei.Torneo.da_dizionario(t) for t in dati["conclusi"]]
        _controlla(all(t.stato == tornei.IN_CORSO for t in cal.tornei) and all(t.stato != tornei.IN_CORSO for t in cal.conclusi),
                   "Calendario: lo stato di una sede non è quello del suo elenco.")
        ids = [ed.id for ed in cal.edizioni] + [t.id for t in (*cal.tornei, *cal.conclusi)]
        _controlla(len(ids) == len(set(ids)) and all(i < cal.prossimo_id for i in ids), "Calendario: un'edizione o una sede ha un identificativo ripetuto.")
        _controlla(isinstance(dati["numeri_dei_tornei"], list) and all(isinstance(v, list) and len(v) == 2 and _intero(v[0]) and _intero(v[1]) for v in dati["numeri_dei_tornei"]),
                   "Calendario: i numeri delle sedi non sono validi.")
        cal.numeri_dei_tornei = dict(dati["numeri_dei_tornei"])
        _controlla(isinstance(dati["differite"], dict), "Calendario: le differite non sono valide.")
        cal.differite = {mid: _differita_da_dizionario(mid, voce) for mid, voce in dati["differite"].items()}
        # Gli incontri delle sedi concluse di recente e quelli delle differite tornano a essere gli stessi oggetti.
        for torneo in cal.conclusi:
            voce = cal.differite.get(torneo.modello["id"])
            if voce is None or voce["edizione"] != torneo.edizione:
                continue
            per_id = {i.id: i for i in torneo.incontri()}
            for sede in voce["sedi"]:
                if sede["sede"] == torneo.sede:
                    sede["incontri"] = [per_id.get(i.id, i) for i in sede["incontri"]]
        for campo, nome in (("saltate", "saltate"), ("tolte", "tolte dall'utente")):
            _controlla(isinstance(dati[campo], list) and all(isinstance(v, list) and len(v) == 2 for v in dati[campo]), f"Calendario: le iscrizioni {nome} non sono valide.")
        cal.saltate = [list(v) for v in dati["saltate"]]
        cal.tolte = [list(v) for v in dati["tolte"]]
        cal.albo = Albo.da_dizionario(dati["albo"])
        return cal


def _differita_a_dizionario(voce):
    """Una voce delle differite da salvare: gli incontri diventano dizionari."""
    return {**{k: copy.deepcopy(v) for k, v in voce.items() if k != "sedi"},
            "sedi": [{**{k: copy.deepcopy(v) for k, v in sede.items() if k != "incontri"}, "incontri": [i.a_dizionario() for i in sede["incontri"]]}
                     for sede in voce["sedi"]]}


def _differita_da_dizionario(mid, voce):
    """Una voce delle differite dal salvataggio, con gli incontri ricostruiti; ValueError col motivo se non va."""
    campi = {"modello", "edizione", "numero", "nome", "data", "squadre", "sedi"}
    _controlla(isinstance(voce, dict) and set(voce) == campi and voce["modello"] == mid and isinstance(voce["sedi"], list)
               and _intero(voce["edizione"]) and _intero(voce["numero"]) and isinstance(voce["nome"], str) and isinstance(voce["data"], str)
               and isinstance(voce["squadre"], bool), f"Calendario: la differita del modello {mid} non è valida.")
    sedi = []
    for sede in voce["sedi"]:
        _controlla(isinstance(sede, dict) and set(sede) == {"sede", "nomi", "grandezze", "incontri"} and _intero(sede["sede"]) and isinstance(sede["nomi"], dict)
                   and isinstance(sede["grandezze"], dict) and all(isinstance(k, str) and k.isdigit() and _intero(v) for k, v in sede["grandezze"].items())
                   and isinstance(sede["incontri"], list), f"Calendario: una sede della differita del modello {mid} non è valida.")
        sedi.append({"sede": sede["sede"], "nomi": dict(sede["nomi"]), "grandezze": dict(sede["grandezze"]),
                     "incontri": [tornei.IncontroDelTorneo.da_dizionario(i) for i in sede["incontri"]]})
    return {**{k: copy.deepcopy(voce[k]) for k in campi - {"sedi"}}, "sedi": sedi}


def descrivi(calendario, g, oggi):
    """Che cosa ha giocato oggi il giocatore nei tornei, per la regola di un impegno al giorno: il torneo, oppure None."""
    if calendario.ha_giocato_oggi(g.id, oggi):
        return "il torneo"
    return None
