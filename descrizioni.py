"""
Descrizioni fisiche dei giocatori di MESS, costruite col motore grammaticale.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-02 con la tappa 4 del piano, secondo la decisione D8.
Alla nascita di un giocatore si estraggono i suoi tratti con genera_tratti: colori, forme e
segni particolari, scritti come parole del vocabolario, e la sua posizione nelle curve di
crescita di altezza e massa corporea. I tratti si salvano col giocatore. Il testo invece non
si salva: descrivi lo compone ogni volta con l'età del momento, così il ragazzino cresce, i
capelli si fanno brizzolati e poi grigi, le rughe compaiono, e l'altezza e il peso che
calcola fisico seguono l'età. Le scelte di stile, cioè il modello di frase e i sinonimi,
vengono da un seme salvato nei tratti: lo stesso giocatore ha sempre la stessa descrizione,
finché non cambia la sua età.
"""

import bisect
import itertools
import json
import os
import random

from grammatica import (
    Aggettivo,
    Sostantivo,
    articolo_indeterminativo,
    con_determinativo,
    con_indeterminativo,
    elenco,
    maiuscola,
    unisci,
    verbo,
)

FILE_VOCABOLARIO = os.path.join("dati", "vocabolario.json")

# Curve di crescita, come coppie di età in anni e valore: altezza media in centimetri, sua
# deviazione standard, indice di massa corporea medio e sua deviazione standard. Fra due età
# il valore si interpola, e oltre gli estremi resta quello dell'estremo.
ALTEZZA_MEDIA = {
    "m": ((9, 134), (10, 139), (11, 144), (12, 150), (13, 157), (14, 164), (15, 169), (16, 173), (17, 175), (18, 176), (50, 176), (90, 172)),
    "f": ((9, 133), (10, 139), (11, 145), (12, 151), (13, 156), (14, 159), (15, 161), (16, 162), (17, 163), (50, 163), (90, 159)),
}
ALTEZZA_DEVIAZIONE = {
    "m": ((9, 6.0), (14, 7.5), (18, 7.0)),
    "f": ((9, 6.0), (13, 6.5), (18, 6.5)),
}
MASSA_MEDIA = {
    "m": ((9, 16.8), (11, 17.8), (13, 19.0), (15, 20.2), (17, 21.3), (20, 22.6), (25, 23.8), (30, 24.6), (40, 25.6), (50, 26.2), (60, 26.4), (80, 25.5)),
    "f": ((9, 16.9), (11, 18.0), (13, 19.2), (15, 20.2), (17, 20.9), (20, 21.5), (25, 22.2), (30, 22.9), (40, 24.0), (50, 25.0), (60, 25.6), (80, 25.0)),
}
MASSA_DEVIAZIONE = ((9, 2.2), (16, 2.6), (20, 3.0), (30, 3.4))
MASSA_LIMITI = (14.5, 42.0)

# Dove finisce ciascuna fascia di statura e di corporatura, in deviazioni standard dalla media
# della propria età e del proprio sesso. Le fasce sono, nell'ordine, quelle del vocabolario.
SOGLIE_STATURA = (-1.2, -0.5, 0.5, 1.2, 2.0)
SOGLIE_CORPORATURA = (-1.3, -0.4, 0.6, 1.5)

# Probabilità dei tratti facoltativi, in frazioni.
PROB_QUALITA_PELLE = 0.5
PROB_SEGNI = ((0, 0.25), (1, 0.45), (2, 0.30))
PROB_LUOGO_SEGNO = 0.8
PROB_DETTAGLIO_OCCHI = 0.6
PROB_DETTAGLIO_NASO = 0.35
PROB_MASSA_CAPELLI = 0.4
PROB_ACCONCIATURA = 0.65
PROB_TINTA = {"m": 0.04, "f": 0.09}
PROB_CALVIZIE = 0.45
PROB_BARBA = 0.55
PROB_TRUCCO = 0.55

# Le età in cui compaiono barba e trucco, e le distanze fra gli stadi dei capelli bianchi e
# della calvizie, in anni dall'età estratta per ciascun giocatore.
ETA_BARBA = 16
ETA_TRUCCO = 14
ETA_TINTA = 15
ETA_QUALCHE_RUGA = 60
ANNI_GRIGI = (0, 12, 25)
ANNI_CALVO = 18

_VOCABOLARIO = None


def vocabolario():
    """Il vocabolario, letto dal file JSON alla prima richiesta e poi tenuto in memoria."""
    global _VOCABOLARIO
    if _VOCABOLARIO is None:
        from GBUtils import percorso_risorsa

        with open(percorso_risorsa(FILE_VOCABOLARIO), encoding="utf-8") as f:
            _VOCABOLARIO = _prepara(json.load(f))
    return _VOCABOLARIO


def _prepara(grezzo):
    """Aggiunge al vocabolario l'indice degli aggettivi, dal maschile singolare all'aggettivo."""
    indice = {}

    def registra(voce):
        aggettivo = aggettivo_da_voce(voce)
        indice.setdefault(aggettivo.chiave, aggettivo)

    def visita(nodo, chiave=None):
        if isinstance(nodo, dict):
            if "lemma" in nodo:
                for voce in nodo.get("aggettivi", ()):
                    registra(voce)
                return
            if "base" in nodo or "voce" in nodo:
                registra(nodo)
                return
            for k, v in nodo.items():
                visita(v, k)
        elif isinstance(nodo, list):
            for v in nodo:
                # I dettagli del naso sono complementi fissi, non aggettivi.
                if isinstance(v, str) and chiave != "dettagli":
                    registra(v)
                else:
                    visita(v, chiave)

    visita({k: v for k, v in grezzo.items() if k not in ("nota", "versione", "anteposti", "persona")})
    grezzo["_aggettivi"] = indice
    return grezzo


def aggettivo_da_voce(voce):
    """L'aggettivo di una voce del vocabolario, tolti i campi che non lo riguardano, come peso."""
    if isinstance(voce, str):
        return Aggettivo(voce)
    if "voce" in voce:
        return Aggettivo(voce["voce"])
    return Aggettivo(**{k: v for k, v in voce.items() if k in ("ms", "mp", "fs", "fp", "base", "dopo")})


def _aggettivo(chiave):
    """Ritrova un aggettivo dal suo maschile singolare; se il vocabolario non lo ha più, lo ricostruisce."""
    return vocabolario()["_aggettivi"].get(chiave) or Aggettivo(chiave)


def _peso(voce):
    return voce.get("peso", 1) if isinstance(voce, dict) else 1


def _estrai(rng, voci):
    """Una voce a caso, tenendo conto dei pesi."""
    voci = list(voci)
    return rng.choices(voci, weights=[_peso(v) for v in voci])[0]


def _estrai_aggettivo(rng, voci):
    return aggettivo_da_voce(_estrai(rng, voci)).chiave


def _sostantivo(voce):
    return Sostantivo(voce["lemma"], voce["genere"], voce.get("numero", "s"))


def _interpola(curva, x):
    if x <= curva[0][0]:
        return curva[0][1]
    for (x0, y0), (x1, y1) in itertools.pairwise(curva):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return curva[-1][1]


def fisico(tratti, sesso, eta):
    """Altezza in centimetri e peso in chili all'età data, dalla posizione del giocatore nelle curve di crescita."""
    altezza = _interpola(ALTEZZA_MEDIA[sesso], eta) + tratti["z_altezza"] * _interpola(ALTEZZA_DEVIAZIONE[sesso], eta)
    massa = _interpola(MASSA_MEDIA[sesso], eta) + tratti["z_massa"] * _interpola(MASSA_DEVIAZIONE, eta)
    massa = max(MASSA_LIMITI[0], min(MASSA_LIMITI[1], massa))
    return round(altezza), round(massa * (altezza / 100) ** 2)


def genera_tratti(sesso, rng=random):
    """I tratti stabili di un giocatore nuovo, sesso m o f: un dizionario che si può salvare in JSON."""
    v = vocabolario()
    viso = v["viso"]
    segni_possibili = list(viso["segni"])
    numero_segni = rng.choices([n for n, _ in PROB_SEGNI], weights=[p for _, p in PROB_SEGNI])[0]
    segni = []
    for voce in rng.sample(segni_possibili, numero_segni):
        segno = {"lemma": voce["lemma"], "aggettivo": _estrai_aggettivo(rng, voce["aggettivi"])}
        if voce.get("luoghi") and rng.random() < PROB_LUOGO_SEGNO:
            segno["luogo"] = rng.choice(voce["luoghi"])
        segni.append(segno)
    occhi = v["occhi"]
    dettaglio_occhi = None
    if rng.random() < PROB_DETTAGLIO_OCCHI:
        voce = rng.choice(occhi["dettagli"])
        dettaglio_occhi = {"lemma": voce["lemma"], "aggettivo": _estrai_aggettivo(rng, voce["aggettivi"])}
    naso = v["naso"]
    bocca = rng.choice(v["bocca"]["sostantivi"])
    capelli = v["capelli"]
    lunghezza = _estrai_aggettivo(rng, capelli["lunghezze"][sesso])
    acconciature = [a for a in capelli["acconciature"][sesso] if not isinstance(a, dict) or lunghezza in a.get("lunghezze", (lunghezza,))]
    tratti = {
        "seme": rng.randrange(1_000_000_000),
        "z_altezza": round(max(-2.6, min(2.6, rng.gauss(0, 1))), 3),
        "z_massa": round(max(-2.4, min(2.6, rng.gauss(0, 1))), 3),
        "viso": {
            "forma": _estrai_aggettivo(rng, viso["forme"]),
            "tinta": _estrai_aggettivo(rng, viso["tinte"]),
            "qualita": _estrai_aggettivo(rng, viso["qualita_pelle"]) if rng.random() < PROB_QUALITA_PELLE else None,
            "segni": segni,
        },
        "occhi": {
            "colore": _estrai_aggettivo(rng, occhi["colori"]),
            "forma": _estrai_aggettivo(rng, occhi["forme"]),
            "sguardo": _estrai_aggettivo(rng, occhi["sguardi"]),
            "dettaglio": dettaglio_occhi,
        },
        "naso": {
            "forma": _estrai_aggettivo(rng, naso["forme"]),
            "secondo": _estrai_aggettivo(rng, naso["misure"] + naso["caratteri"]),
            "dettaglio": rng.choice(naso["dettagli"]) if rng.random() < PROB_DETTAGLIO_NASO else None,
        },
        "bocca": {"lemma": bocca["lemma"], "aggettivo": _estrai_aggettivo(rng, bocca["aggettivi"])},
        "capelli": {
            "colore": _estrai_aggettivo(rng, capelli["colori_naturali"]),
            "tinta": rng.choice(capelli["colori_tinti"]) if rng.random() < PROB_TINTA[sesso] else None,
            "lunghezza": lunghezza,
            "piega": _estrai_aggettivo(rng, capelli["pieghe"]),
            "massa": _estrai_aggettivo(rng, capelli["masse"]) if rng.random() < PROB_MASSA_CAPELLI else None,
            "acconciatura": _estrai_aggettivo(rng, acconciature) if acconciature and rng.random() < PROB_ACCONCIATURA else None,
            "eta_grigi": round(rng.triangular(30, 75, 48), 1),
            "eta_calvizie": round(rng.uniform(22, 60), 1) if sesso == "m" and rng.random() < PROB_CALVIZIE else None,
        },
    }
    if sesso == "m":
        if rng.random() < PROB_BARBA:
            voce = _estrai(rng, v["barba"]["sostantivi"])
            tratti["barba"] = {"lemma": voce["lemma"], "aggettivo": _estrai_aggettivo(rng, voce["aggettivi"])}
        else:
            tratti["barba"] = {"senza": rng.choice(v["barba"]["senza"])}
    elif rng.random() < PROB_TRUCCO:
        tratti["trucco"] = _estrai_aggettivo(rng, v["trucco"]["aggettivi"])
    return tratti


def _voce_con_lemma(voci, lemma):
    return next(v for v in voci if v["lemma"] == lemma)


def _scegli(lista, u):
    """Una voce della lista secondo il numero u fra 0 e 1, sempre la stessa per lo stesso u."""
    return lista[min(len(lista) - 1, int(u * len(lista)))]


def _gruppo_nominale(sostantivo, aggettivo, anteposti, articolo=True):
    """Sostantivo e aggettivo accordati, con l'aggettivo prima o dopo, e l'articolo che vuole la prima parola."""
    forma = aggettivo.accorda(sostantivo)
    if aggettivo.chiave in anteposti:
        gruppo = f"{forma} {sostantivo.lemma}"
        prima = Sostantivo(forma.split()[0], sostantivo.genere, sostantivo.numero)
    else:
        gruppo = f"{sostantivo.lemma} {forma}"
        prima = sostantivo
    if not articolo or sostantivo.numero == "p":
        return gruppo
    return unisci(articolo_indeterminativo(prima), gruppo)


class _Parti:
    """Le parti della descrizione già accordate, pronte per i modelli di frase."""

    def __init__(self, tratti, sesso, eta):
        v = vocabolario()
        anteposti = set(v["anteposti"])
        u = random.Random(tratti["seme"])
        scelte = [u.random() for _ in range(12)]
        self.modello = _scegli((0, 1, 2), scelte[0])
        self.persona = _sostantivo(next(p for p in v["persona"][sesso] if eta <= p["eta_max"]))
        fascia_statura = bisect.bisect(SOGLIE_STATURA, tratti["z_altezza"])
        fascia_corporatura = bisect.bisect(SOGLIE_CORPORATURA, tratti["z_massa"])
        statura = aggettivo_da_voce(_scegli(v["statura"][fascia_statura], scelte[1]))
        # Slanciato vuol dire anche alto: con una statura bassa o media si sceglie un'altra parola.
        corporature = [c for c in v["corporatura"][fascia_corporatura] if c != "slanciato" or fascia_statura >= 3]
        corporatura = aggettivo_da_voce(_scegli(corporature, scelte[2]))
        parole = sorted((statura.accorda(self.persona), corporatura.accorda(self.persona)), key=lambda p: p.startswith("di "))
        self.persona_np = f"{con_indeterminativo(self.persona)} {elenco(parole)}"
        tv = tratti["viso"]
        self.viso = _sostantivo(_scegli(v["viso"]["sostantivi"], scelte[3]))
        self.viso_forma = _aggettivo(tv["forma"]).accorda(self.viso)
        self.tinta_sost = _sostantivo(_scegli(v["viso"]["tinte_sostantivi"], scelte[4]))
        self.tinta = _aggettivo(tv["tinta"]).accorda(self.tinta_sost)
        pelle = Sostantivo("pelle", "f")
        self.qualita = _aggettivo(tv["qualita"]).accorda(pelle) if tv.get("qualita") else None
        self.sost_pelle = pelle
        self.segni = []
        numeri = []
        for segno in tv["segni"]:
            voce = _voce_con_lemma(v["viso"]["segni"], segno["lemma"])
            if eta < voce.get("eta_min", 0):
                continue
            testo = _gruppo_nominale(_sostantivo(voce), _aggettivo(segno["aggettivo"]), anteposti)
            self.segni.append(f"{testo} {segno['luogo']}" if segno.get("luogo") else testo)
            numeri.append(voce.get("numero", "s"))
        # Chi non ha rughe fra i suoi segni ne prende comunque qualcuna con gli anni.
        if eta >= ETA_QUALCHE_RUGA and not any(s["lemma"] in ("rughe", "zampe di gallina") for s in tv["segni"]):
            self.segni.append("qualche ruga")
            numeri.append("s")
        self.segni_singolare = numeri == ["s"]
        to = tratti["occhi"]
        self.occhi = Sostantivo("occhi", "m", "p")
        self.occhi_colore = _aggettivo(to["colore"]).accorda(self.occhi)
        self.occhi_forma = _aggettivo(to["forma"]).accorda(self.occhi)
        self.sguardo = Sostantivo("sguardo", "m")
        self.sguardo_agg = _aggettivo(to["sguardo"]).accorda(self.sguardo)
        self.dettaglio_occhi = None
        if to.get("dettaglio"):
            sost = _sostantivo(_voce_con_lemma(v["occhi"]["dettagli"], to["dettaglio"]["lemma"]))
            self.dettaglio_occhi = (sost, _aggettivo(to["dettaglio"]["aggettivo"]).accorda(sost))
        tn = tratti["naso"]
        naso = Sostantivo("naso", "m")
        self.naso = (_aggettivo(tn["forma"]).accorda(naso), _aggettivo(tn["secondo"]).accorda(naso))
        self.naso_dettaglio = tn.get("dettaglio")
        tb = tratti["bocca"]
        self.bocca = _sostantivo(_voce_con_lemma(v["bocca"]["sostantivi"], tb["lemma"]))
        self.bocca_agg = _aggettivo(tb["aggettivo"]).accorda(self.bocca)
        tc = tratti["capelli"]
        self.capelli = Sostantivo("capelli", "m", "p")
        naturale = tc["colore"]
        for stadio, anni in reversed(list(enumerate(ANNI_GRIGI))):
            if eta >= tc["eta_grigi"] + anni:
                naturale = _scegli(v["capelli"]["colori_eta"][stadio], scelte[5])
                break
        self.colore_naturale = naturale
        colore = tc["tinta"] if tc.get("tinta") and eta >= ETA_TINTA else naturale
        self.capelli_colore = _aggettivo(colore).accorda(self.capelli)
        self.capelli_descrittori = elenco([_aggettivo(tc[k]).accorda(self.capelli) for k in ("lunghezza", "piega", "massa") if tc.get(k)])
        self.acconciatura = _aggettivo(tc["acconciatura"]).accorda(self.capelli) if tc.get("acconciatura") else None
        self.calvizie = 0
        if tc.get("eta_calvizie") is not None and eta >= tc["eta_calvizie"]:
            self.calvizie = 2 if eta >= tc["eta_calvizie"] + ANNI_CALVO else 1
        self.barba = None
        barba = tratti.get("barba")
        if barba and eta >= ETA_BARBA:
            if "senza" in barba:
                self.barba = ("senza", _aggettivo(barba["senza"]).accorda(self.persona))
            else:
                sost = _sostantivo(_voce_con_lemma(v["barba"]["sostantivi"], barba["lemma"]))
                agg = _aggettivo(barba["aggettivo"]).accorda(sost)
                parti = [agg]
                if scelte[6] < 0.5 and not agg.startswith(("di ", "a ")) and " e " not in self.colore_naturale:
                    parti.append(_aggettivo(self.colore_naturale).accorda(sost))
                self.barba = (sost, elenco(parti))
        self.trucco = None
        if tratti.get("trucco") and eta >= ETA_TRUCCO:
            self.trucco = _aggettivo(tratti["trucco"]).accorda(Sostantivo("trucco", "m"))

    def pelle(self, preposizione=None):
        """Le parti sulla pelle, da unire alle altre con elenco: dalla carnagione chiara e dalla pelle liscia, o la pelle olivastra e vellutata."""
        if self.tinta_sost.lemma == "pelle":
            return [f"{con_determinativo(self.sost_pelle, preposizione)} {elenco([self.tinta, self.qualita])}"]
        parti = [f"{con_determinativo(self.tinta_sost, preposizione)} {self.tinta}"]
        if self.qualita:
            parti.append(f"{con_determinativo(self.sost_pelle, preposizione)} {self.qualita}")
        return parti

    def viso_con_complemento(self):
        """La forma del viso che comincia già con da, come dai tratti decisi, non vuole davanti il viso."""
        return self.viso_forma.startswith(("dal", "dai ", "dagli ", "dalle "))

    def bocca_np(self):
        return f"{con_indeterminativo(self.bocca)} {self.bocca_agg}"

    def bocca_predicato(self):
        return f"{con_determinativo(self.bocca)} {verbo(self.bocca, 'è', 'sono')} {self.bocca_agg}"

    def barba_frase(self, verbo_avere):
        """Porta una barba corta, Ha i baffi folti, È sbarbato; niente sotto l'età della barba."""
        if not self.barba:
            return None
        sost, testo = self.barba
        if sost == "senza":
            return f"È {testo}."
        np = f"{con_determinativo(sost)} {testo}" if sost.numero == "p" else f"{con_indeterminativo(sost)} {testo}"
        return f"{verbo_avere} {np}."

    def capelli_coda(self):
        coda = f", {self.acconciatura}" if self.acconciatura else ""
        if self.calvizie == 1:
            coda += ", con una stempiatura evidente"
        return coda

    def calvo(self):
        return Aggettivo("calvo").accorda(self.persona)


def descrivi(tratti, sesso, eta):
    """La descrizione fisica di un giocatore all'età data, in anni anche con i decimali."""
    p = _Parti(tratti, sesso, eta)
    frasi = []
    if p.modello == 0:
        viso = p.viso_forma if p.viso_con_complemento() else f"{con_determinativo(p.viso, 'da')} {p.viso_forma}"
        frasi.append(f"È {p.persona_np}, {elenco([viso, *p.pelle('da')])}.")
        if p.segni:
            frasi.append(f"Ha {elenco(p.segni)}.")
        occhi = f"Ha gli occhi {elenco([p.occhi_colore, p.occhi_forma])}, {con_determinativo(p.sguardo, 'da')} {p.sguardo_agg}"
        if p.dettaglio_occhi:
            sost, agg = p.dettaglio_occhi
            occhi += f", e {con_determinativo(sost)} {agg}"
        frasi.append(occhi + ".")
        naso = f"Il naso è {elenco(p.naso)}"
        if p.naso_dettaglio:
            naso += f", {p.naso_dettaglio},"
        frasi.append(f"{naso} e {p.bocca_predicato()}.")
        if p.calvizie == 2:
            frasi.append(f"È {p.calvo()}, con pochi capelli {p.capelli_colore} ai lati e sulla nuca.")
        else:
            frasi.append(f"Porta i capelli {p.capelli_colore}, {p.capelli_descrittori}{p.capelli_coda()}.")
        frasi.append(p.barba_frase("Porta"))
        if p.trucco:
            frasi.append(f"Porta un trucco {p.trucco}.")
    elif p.modello == 1:
        testa = "dalla testa calva" if p.calvizie == 2 else f"{con_determinativo(p.capelli, 'da')} {p.capelli_colore}"
        frasi.append(f"Si presenta come {p.persona_np}, {testa} e {con_determinativo(p.occhi, 'da')} {p.occhi_colore}.")
        viso = f"Ha {elenco([f'{con_indeterminativo(p.viso)} {p.viso_forma}', *p.pelle()])}"
        if p.segni:
            viso += f", con {elenco(p.segni)}"
        frasi.append(viso + ".")
        occhi = f"Gli occhi, {p.occhi_forma}, hanno {con_indeterminativo(p.sguardo)} {p.sguardo_agg}"
        if p.dettaglio_occhi:
            sost, agg = p.dettaglio_occhi
            occhi += f", e {con_determinativo(sost)} {verbo(sost, 'è', 'sono')} {agg}"
        frasi.append(occhi + ".")
        naso = f"Ha un naso {p.naso[0]}"
        if p.naso_dettaglio:
            naso += f", {p.naso_dettaglio},"
        frasi.append(f"{naso} e {p.bocca_np()}.")
        if p.calvizie == 2:
            frasi.append(f"Ai lati e sulla nuca restano pochi capelli {p.capelli_colore}.")
        else:
            frasi.append(f"I capelli sono {p.capelli_descrittori}{p.capelli_coda()}.")
        frasi.append(p.barba_frase("Porta"))
        if p.trucco:
            frasi.append(f"Il trucco è {p.trucco}.")
    else:
        frasi.append(f"Ha l'aspetto di {p.persona_np}.")
        if p.viso_con_complemento():
            viso = f"{maiuscola(con_determinativo(p.viso))} ha {p.viso_forma.split(' ', 1)[1]}"
        else:
            viso = f"{maiuscola(con_determinativo(p.viso))} è {p.viso_forma}"
        frasi.append(f"{viso}, {elenco(p.pelle())}.")
        if p.segni:
            frasi.append(f"{'Si nota' if p.segni_singolare else 'Si notano'} {elenco(p.segni)}.")
        occhi = f"Ha occhi {p.occhi_colore}, {p.occhi_forma}, {con_determinativo(p.sguardo, 'da')} {p.sguardo_agg}"
        if p.dettaglio_occhi:
            sost, agg = p.dettaglio_occhi
            occhi += f", con {sost.lemma} {agg}"
        frasi.append(occhi + ".")
        naso = f"Il naso è {elenco(p.naso)}"
        if p.naso_dettaglio:
            naso += f", {p.naso_dettaglio}"
        frasi.append(f"{naso}. {maiuscola(p.bocca_predicato())}.")
        if p.calvizie == 2:
            frasi.append(f"È {p.calvo()}, e restano pochi capelli {p.capelli_colore} ai lati e sulla nuca.")
        else:
            frasi.append(f"Ha capelli {p.capelli_colore}, {p.capelli_descrittori}{p.capelli_coda()}.")
        frasi.append(p.barba_frase("Ha"))
        if p.trucco:
            frasi.append(f"Di solito usa un trucco {p.trucco}.")
    return " ".join(f for f in frasi if f)
