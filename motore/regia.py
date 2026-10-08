"""
La regia dell'incontro di showdown nel motore di MESS: dagli esiti agli eventi.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9, decisione D25, e prepara la partita live sonora della tappa 10,
decisione D11. La regia non cambia mai un risultato: riceve gli esiti di ogni punto, già decisi
dalla catena, e li trasforma in eventi con l'istante, la posizione sul tavolo, il lato e la
distanza. Riceve tutti i passi di un punto insieme, quindi sa come finisce lo scambio e mette le
posizioni in modo coerente: l'arrivo di un volo è il punto della parata che segue.
Il caso della regia è soltanto quello della scena, nato dal seme dell'incontro: coordinate dentro
la zona, velocità, attese. La regia tiene l'orologio, la posizione dell'arbitro, che cambia lato a
ogni cambio campo perché il riferimento resta ancorato ai giocatori, la mano di ogni giocatore e il
punto in cui è finita la pallina, da cui dipende quanto dura il recupero.
controlla_invarianti verifica una sequenza di eventi: la usano le prove e il banco.
"""

import itertools
import math

from costanti import COLPI_DELLO_SCAMBIO, LARGHEZZA_TAVOLO, LUNGHEZZA_TAVOLO, META_TAVOLO, RAGGIO_AREA_PORTA
from motore import eventi as E
from motore.eventi import CAUSE, ErroreMotore, Evento, Tappa
from motore.tavolo import (
    CENTRO_X,
    FONDO_A,
    FONDO_B,
    MARGINE_GIOCO,
    SPONDA_DESTRA_A,
    SPONDA_SINISTRA_A,
    centro_porta,
    distanza_di,
    intervallo_zona,
    lato_di,
    locale_in_assoluto,
    partenza_massima_battuta,
    posizione_al_tempo,
    posizione_arbitro,
    sponda_assoluta,
    traiettoria,
)

_NUMERI_SERVIZIO = {1: "primo_servizio", 2: "secondo_servizio", 3: "terzo_servizio"}
_FISCHI = {E.SINGOLO: "FISCHIO_SINGOLO", E.DOPPIO: "FISCHIO_DOPPIO", E.LUNGO: "FISCHIO_LUNGO"}


def altra(parte):
    return "B" if parte == "A" else "A"


class Regia:
    """Trasforma gli esiti dell'incontro in eventi, con il tempo, le posizioni, i lati e le distanze."""

    def __init__(self, rng, taratura, formato, campo, velocita=1.0):
        self.rng = rng
        self.tar = taratura
        self.formato = formato
        self.campo = campo
        # La velocità di gioco della tappa 10, decisione D12: divide le attese e le pause.
        self.velocita = velocita
        self.t = 0.0
        self.n = 0
        self.fase = E.PRELIMINARI
        self.set_n = 0
        self.punto_n = 0
        self.punteggio = (0, 0)
        self.arbitro_a_sinistra = True
        self.mani = {gid: c.mano for gid, c in campo.items()}
        self.pallina = "arbitro"
        self.pos_pallina = None
        # La mano del battitore e l'arrivo della battuta, scelti insieme alla ripresa.
        self._mano_battuta = None
        self._arrivo_battuta_locale = None

    # Gli strumenti.

    def _attesa(self, secondi):
        self.t += secondi / self.velocita

    def _uniforme(self, a, b):
        return a + (b - a) * self.rng.random()

    def _evento(self, tipo, durata=0.0, chi=None, pos=None, avanza=True, **campi):
        """Un evento all'istante attuale; con avanza, l'orologio va avanti della sua durata."""
        self.n += 1
        parte = campi.pop("parte", None)
        if chi is not None and parte is None:
            parte = self.campo[chi].parte
        punto_di_vista = parte or "A"
        lato = distanza = None
        if pos is not None:
            pos = (round(pos[0], 1), round(pos[1], 1))
            lato = lato_di(pos[0], punto_di_vista)
            distanza = round(distanza_di(pos[1], punto_di_vista), 1)
        evento = Evento(n=self.n, t=round(self.t, 3), tipo=tipo, fase=self.fase, durata=round(durata, 3), set_n=self.set_n, punto_n=self.punto_n,
                        chi=chi, parte=parte, pos=pos, lato=lato, distanza=distanza, punteggio=self.punteggio, **campi)
        if avanza and durata:
            self.t += durata
        return evento

    def _pos_arbitro(self):
        return posizione_arbitro(self.arbitro_a_sinistra)

    def _arbitro(self, tipo, durata=0.0, **campi):
        return self._evento(tipo, durata, None, self._pos_arbitro(), **campi)

    def _fischio(self, variante):
        durata = getattr(self.tar, _FISCHI[variante])
        return self._arbitro(E.FISCHIO, durata, fischio=variante)

    def _fischio_e_chiamata(self, variante, chiave, **campi):
        """Il fischio e, 0,8 secondi dopo il suo inizio o appena finito, la chiamata dell'arbitro."""
        inizio = self.t
        fischio = self._fischio(variante)
        self.t = max(self.t, inizio + self.tar.RITARDO_CHIAMATA)
        return [fischio, self._arbitro(E.CHIAMATA, self.tar.DURATA_CHIAMATA, chiamata=chiave, **campi)]

    def _velocita(self, chi, base):
        c = self.campo[chi]
        t = self.tar
        return base * (t.FATTORE_FORZA_VELOCITA_BASE + t.FATTORE_FORZA_VELOCITA * c.forza) * (1.0 + t.FATTORE_TEMP_VELOCITA * c.tau) * \
            (1.0 + self._uniforme(-t.VARIAZIONE_VELOCITA, t.VARIAZIONE_VELOCITA))

    def _volo(self, partenza, arrivo, sponde, v0, tipo_arrivo="arrivo", decelerazione=None):
        t = self.tar
        return traiettoria(partenza, arrivo, sponde, v0, self.t, t.DECELERAZIONE if decelerazione is None else decelerazione, t.PERDITA_PER_SPONDA, tipo_arrivo)

    def _evento_volo(self, chi, volo, colpo=None, dati=None):
        """Il VOLO: comincia con la prima tappa e dura fino all'ultima; posizione dell'arrivo vista da chi ha colpito."""
        arrivo = (volo[-1].x, volo[-1].y)
        return self._evento(E.VOLO, volo[-1].t - volo[0].t, chi, arrivo, volo=volo, colpo=colpo, dati=dati)

    def _punto_parata(self, chi, zona):
        """Dove chi difende incontra la pallina: dentro la zona, fra 15 e 35 cm dalla sua linea."""
        parte = self.campo[chi].parte
        x_min, x_max = intervallo_zona(zona, parte)
        x = self._uniforme(x_min, x_max)
        d = self._uniforme(*self.tar.DISTANZA_PARATA)
        y = d if parte == "A" else LUNGHEZZA_TAVOLO - d
        return x, y

    def _partenza_colpo(self, chi, nome):
        """Il colpo parte dalla partenza del colpo, più uno scostamento, fra 25 e 40 cm dalla linea di chi colpisce."""
        colpo = self.tar.COLPI[nome]
        s = self.tar.SCOSTAMENTO_MASSIMO
        u = min(LARGHEZZA_TAVOLO - MARGINE_GIOCO, max(MARGINE_GIOCO, colpo.partenza_u + self._uniforme(-s, s)))
        v = self._uniforme(25.0, 40.0)
        return locale_in_assoluto(self.campo[chi].parte, u, v)

    def _sponde(self, chi, nome):
        parte = self.campo[chi].parte
        return tuple(sponda_assoluta(parte, s) for s in self.tar.COLPI[nome].sponde)

    def _dritto(self, chi, zona):
        return self.campo[chi].dritto(zona) if zona else None

    # L'incontro e il sorteggio.

    def inizio_incontro(self, ids):
        self.fase = E.PRELIMINARI
        return [self._arbitro(E.INIZIO_INCONTRO, 0.0, dati={"formato": self.formato.nome, "al_tavolo": list(ids)})]

    def sorteggio(self, info):
        """
        Il lancio della moneta; nella gara a squadre, subito dopo, l'arbitro legge le formazioni e
        chiede alla squadra che ha vinto se tiene il primo servizio o lo cede.
        """
        self.arbitro_a_sinistra = info["arbitro_a_sinistra_di_a"]
        eventi = [self._arbitro(E.SORTEGGIO, 8.0, dati=dict(info))]
        if "formazioni" in info:
            dati = {chiave: info[chiave] for chiave in ("formazioni", "riserve", "vince", "scelta", "batte")}
            eventi.append(self._arbitro(E.FORMAZIONI, self.tar.DURATA_FORMAZIONI / self.velocita, dati=dati))
        return eventi

    def riscaldamento(self, ids):
        """
        Il riscaldamento: colpi liberi a turno, gli avvisi del tempo e il fischio di fine. Nel
        singolare l'arbitro chiama 15 secondi prima della fine; nella gara a squadre, regola IBSA
        22.3, chiama 30 secondi ogni 30 secondi.
        """
        self.fase = E.RISCALDAMENTO
        durata = float(self.formato.riscaldamento)
        eventi = [self._arbitro(E.RISCALDAMENTO_INIZIO, 0.0, dati={"durata": durata})]
        inizio = self.t
        avvisi = list(self.formato.avvisi_riscaldamento)
        turno = 0
        while True:
            trascorso = self.t - inizio
            while avvisi and trascorso >= avvisi[0]:
                restano = round(durata - avvisi.pop(0))
                if self.formato.tipo == "squadre":
                    chiamata = "trenta_secondi"
                else:
                    chiamata = "quindici_secondi" if restano == 15 else None
                eventi.append(self._arbitro(E.AVVISO_TEMPO, 0.0, chiamata=chiamata, dati={"restano": restano}))
            if trascorso >= durata - 2.0:
                break
            chi = ids[turno % 2]
            nome = COLPI_DELLO_SCAMBIO[int(self.rng.random() * len(COLPI_DELLO_SCAMBIO))]
            difensore = ids[(turno + 1) % 2]
            colpo = self.tar.COLPI[nome]
            partenza = self._partenza_colpo(chi, nome)
            arrivo = self._punto_parata(difensore, colpo.zona)
            volo = self._volo(partenza, arrivo, self._sponde(chi, nome), self._velocita(chi, colpo.velocita), "paletta")
            eventi.append(self._evento(E.RISCALDAMENTO_COLPO, 0.0, chi, partenza, volo=volo, colpo=nome, mano=self.mani[chi]))
            self._attesa(self._uniforme(*self.tar.INTERVALLO_RISCALDAMENTO))
            turno += 1
        self.t = max(self.t, inizio + durata)
        eventi.append(self._fischio(E.SINGOLO))
        eventi.append(self._arbitro(E.RISCALDAMENTO_FINE, 0.0))
        self.pallina = "arbitro"
        return eventi

    # I set e le riprese.

    def inizio_set(self, set_n, battitore):
        self.fase = E.GIOCO
        self.set_n = set_n
        self.punto_n = 0
        self.punteggio = (0, 0)
        self.pallina = "arbitro"
        return [self._arbitro(E.INIZIO_SET, 0.0, dati={"apre": battitore.id})]

    def ripresa(self, battitore, ricevitore, numero_servizio, punteggio_visto, lunga, passi, punteggio):
        """
        La pallina recuperata, portata al battitore, l'annuncio, la domanda di pronto alle riprese
        lunghe e il fischio. Riceve tutti i passi del punto, perché il battitore si mette dove la
        sua battuta, regolare, arriverà davvero: alla parata, in porta, nell'area di porta o sul
        corpo di chi riceve.
        """
        self.fase = E.GIOCO
        self.punto_n += 1
        self.punteggio = punteggio
        t = self.tar
        passo_battuta = passi[0]
        eventi = []
        if self.pallina != "arbitro":
            durata = {"tasca": t.RECUPERO_TASCA, "terra": t.RECUPERO_TERRA}.get(self.pallina, t.RECUPERO_TAVOLO) / self.velocita
            eventi.append(self._evento(E.RECUPERO, durata, None, self.pos_pallina or self._pos_arbitro(), dati={"da": self.pallina}))
        # La pallina va dal bordo dalla parte dell'arbitro, a metà tavolo, alla mano del battitore.
        bordo = (0.0 if self.arbitro_a_sinistra else float(LARGHEZZA_TAVOLO), float(META_TAVOLO))
        mano = self._partenza_battuta(battitore.id, passi)
        self._mano_battuta = mano
        distanza = math.hypot(mano[0] - bordo[0], mano[1] - bordo[1])
        durata = distanza / t.VELOCITA_CONSEGNA
        volo = (Tappa(round(self.t, 3), bordo[0], bordo[1], t.VELOCITA_CONSEGNA, "partenza"), Tappa(round(self.t + durata, 3), mano[0], mano[1], 0.0, "mano_battitore"))
        eventi.append(self._evento(E.CONSEGNA, durata, None, mano, parte=battitore.parte, volo=volo, dati={"a": battitore.id}))
        eventi.append(self._arbitro(E.ANNUNCIO, t.DURATA_ANNUNCIO / self.velocita, chiamata=_NUMERI_SERVIZIO.get(numero_servizio),
                                    dati={"numero_servizio": numero_servizio, "battitore": battitore.id, "punteggio_visto": tuple(punteggio_visto)}))
        if lunga:
            eventi.append(self._arbitro(E.DOMANDA_PRONTO, t.DURATA_DOMANDA_PRONTO / self.velocita))
        self.pallina = "battitore"
        causa = passo_battuta.causa if passo_battuta.esito == "irregolare" else None
        if causa == "battuta_prima_del_fischio":
            # Il battitore colpisce prima del fischio: l'arbitro fischierà il fallo.
            self._attesa(0.2)
            return eventi
        eventi.append(self._fischio(E.SINGOLO))
        if causa == "battuta_oltre_due_secondi":
            self._attesa(t.ATTESA_OLTRE_DUE_SECONDI)
        else:
            attesa = self._uniforme(*t.ATTESA_BATTUTA)
            if battitore.giocorapido:
                attesa *= t.FATTORE_TEMPI_GIOCO_RAPIDO
            self._attesa(attesa)
        return eventi

    def _partenza_battuta(self, chi, passi):
        """
        Dove il battitore colpisce. Per la battuta regolare si sceglie insieme all'arrivo vero,
        perché l'unica sponda cada prima dello schermo: con l'arrivo a u dalla sponda, la
        partenza più lontana possibile mette il rimbalzo a 175 cm dalla linea. Di solito si
        sceglie fra 61 cm e quella; quando l'arrivo sta verso il centro, come la porta, la
        partenza più lontana scende sotto 61, e il battitore si sposta verso la sua sponda. La
        battuta irregolare parte fra 61 e 100 cm, come una battuta qualunque.
        """
        c = self.campo[chi]
        passo = passi[0]
        nome = passo.colpo
        # Nel riferimento specchiato la battuta destra diventa sinistra.
        destra = nome == "battutadx"
        if passo.esito == "regolare":
            arrivo_u, arrivo_v = self._arrivo_vero_battuta(c, passi)
            self._arrivo_battuta_locale = (arrivo_u, arrivo_v)
            u_a = LARGHEZZA_TAVOLO - arrivo_u if destra else arrivo_u
            alto = min(100.0, partenza_massima_battuta(u_a, arrivo_v))
            basso = 61.0 if alto > 61.0 else max(MARGINE_GIOCO, alto - 25.0)
            u_s = self._uniforme(basso, alto)
        else:
            self._arrivo_battuta_locale = None
            u_s = self._uniforme(61.0, 100.0)
        if destra:
            u_s = LARGHEZZA_TAVOLO - u_s
        return locale_in_assoluto(c.parte, u_s, 25.0)

    def _arrivo_vero_battuta(self, battitore, passi):
        """
        L'arrivo della battuta regolare nel riferimento del battitore: nella zona di chi riceve,
        alla distanza di parata, e poi spostato dove lo porta la parata che segue, con le stesse
        regole degli altri colpi.
        """
        parata = self._prossima_parata(passi, 0)
        if parata is None:
            raise ErroreMotore("Una battuta regolare senza la parata che segue.")
        u, v = self._arrivo_battuta(passi[0].colpo, parata.zona)
        assoluto = locale_in_assoluto(battitore.parte, u, v)
        assoluto = self._arrivo_dopo_la_parata(parata, assoluto)
        # Lo specchio è l'inverso di sé stesso: la stessa funzione riporta al riferimento del battitore.
        return locale_in_assoluto(battitore.parte, *assoluto)

    def _arrivo_battuta(self, nome, zona):
        """L'arrivo della battuta nel riferimento del battitore: nella zona di chi riceve, alla distanza di parata."""
        if zona is None:
            zona = self.tar.COLPI[nome].zona
        d = self._uniforme(*self.tar.DISTANZA_PARATA)
        v = LUNGHEZZA_TAVOLO - d
        # La zona sx di chi riceve è la destra di chi batte, cioè u alto.
        if zona == "centro":
            u = self._uniforme(70.0, CENTRO_X + 20.0) if nome == "battutasx" else self._uniforme(CENTRO_X - 20.0, LARGHEZZA_TAVOLO - 70.0)
        elif zona == "sx":
            u = self._uniforme(CENTRO_X + 21.0, LARGHEZZA_TAVOLO - MARGINE_GIOCO)
        else:
            u = self._uniforme(MARGINE_GIOCO, CENTRO_X - 21.0)
        return u, v

    # Il punto.

    def punto(self, passi, esito, punteggio):
        """Gli eventi del punto dai suoi passi, poi il fischio, la chiamata e il punto o la ripetizione."""
        t = self.tar
        eventi = []
        pos = self._mano_battuta
        colpo_n = 0
        i = 0
        n = len(passi)
        decisivo = None
        ultimo_colpitore = None
        while i < n:
            p = passi[i]
            chi = p.chi.id
            if p.tipo in ("battuta", "colpo", "ribattuta"):
                ultimo_colpitore = chi
            if p.tipo == "battuta":
                eventi.append(self._evento(E.BATTUTA, 0.0, chi, pos, colpo=p.colpo, mano=self.mani[chi], esito=p.esito, causa=p.causa, critico=p.critico,
                                           dati={"qualita": round(p.valore, 1), "prob": _arrotonda(p.prob)}))
                if p.esito == "regolare":
                    pos = self._vola_verso_parata(eventi, chi, pos, p, passi, i, colpo_n)
                else:
                    pos = self._volo_battuta_irregolare(eventi, chi, pos, p)
            elif p.tipo == "cambio_mano":
                self.mani[chi] = "sinistra" if self.mani[chi] == "destra" else "destra"
                eventi.append(self._evento(E.CAMBIO_MANO, 0.0, chi, pos, mano=self.mani[chi], colpo_n=colpo_n))
            elif p.tipo == "parata":
                eventi.append(self._evento(E.PARATA, 0.0, chi, pos, colpo=p.colpo, mano=self.mani[chi], dritto=self._dritto(chi, p.zona), esito=p.esito,
                                           causa=p.causa, critico=p.critico, colpo_n=colpo_n,
                                           dati={"da": ultimo_colpitore, "zona": p.zona, "qualita": round(p.valore, 1), "prob": _arrotonda(p.prob)}))
                if p.esito == "fuori":
                    # La parata manda la pallina oltre la sponda: il fallo resta dove ha parato.
                    lato = 1.0 if pos[0] > CENTRO_X else -1.0
                    fuori = (CENTRO_X + lato * (CENTRO_X + 25.0), pos[1] + (30.0 if self.campo[chi].parte == "A" else -30.0))
                    volo = (Tappa(self.t, pos[0], pos[1], 200.0, "partenza"), Tappa(self.t + 0.3, CENTRO_X + lato * CENTRO_X, pos[1], 150.0, "fuori"),
                            Tappa(self.t + 0.6, fuori[0], fuori[1], 0.0, "terra"))
                    eventi.append(self._evento_volo(chi, volo))
            elif p.tipo == "controllo":
                durata = self._uniforme(*t.DURATA_CONTROLLO)
                if self.campo[chi].giocorapido:
                    durata *= t.FATTORE_CONTROLLO_GIOCO_RAPIDO
                if p.esito == "trattenuta":
                    durata = self._uniforme(*t.DURATA_TRATTENUTA)
                eventi.append(self._evento(E.CONTROLLO, durata, chi, pos, mano=self.mani[chi], esito=p.esito, causa=p.causa, critico=p.critico, colpo_n=colpo_n,
                                           dati={"valore": round(p.valore, 3), "prob": _arrotonda(p.prob)}))
            elif p.tipo == "sfuggita":
                if p.esito == "autogoal":
                    porta = centro_porta(self.campo[chi].parte)
                    volo = self._volo(pos, (porta[0], porta[1] + (4.0 if porta[1] == 0 else -4.0)), (), 150.0, "porta")
                    eventi.append(self._evento_volo(chi, volo))
                    pos = (volo[-1].x, volo[-1].y)
                elif p.esito == "pallina_ferma":
                    self._attesa(2.0)
                else:
                    eventi.append(self._evento(E.CONTROLLO, 0.6, chi, pos, mano=self.mani[chi], esito="recupero", colpo_n=colpo_n))
            elif p.tipo == "colpo":
                colpo_n += 1
                partenza = self._partenza_colpo(chi, p.colpo)
                eventi.append(self._evento(E.COLPO, 0.0, chi, partenza, colpo=p.colpo, mano=self.mani[chi], esito=p.esito, causa=p.causa, critico=p.critico,
                                           colpo_n=colpo_n, dati=self._dati_colpo(p)))
                pos = partenza
                if p.esito == "colpo":
                    pos = self._vola_verso_parata(eventi, chi, pos, p, passi, i, colpo_n)
                elif p.esito == "debole":
                    pos = self._volo_debole(eventi, chi, pos, p, colpo_n)
                else:
                    pos = self._volo_del_fallo(eventi, chi, pos, p, colpo_n)
            elif p.tipo == "ribattuta":
                colpo_n += 1
                pos = self._vola_verso_parata(eventi, chi, pos, p, passi, i, colpo_n, ribattuta=True)
            elif p.tipo in ("goal", "fallo", "palla_morta", "rottura"):
                decisivo = p
                pos = self._esito_finale(eventi, p, pos, esito, punteggio, passi, i, colpo_n)
            else:
                raise ErroreMotore(f"Passo sconosciuto per la regia: {p.tipo}")
            i += 1
        if decisivo is None:
            raise ErroreMotore("Un punto senza passo decisivo.")
        # Il fischio, la chiamata, e il punto o la ripetizione. Per una rottura il fischio è già
        # arrivato, nell'istante stesso della rottura, e non c'è chiamata: l'arbitro ha fatto
        # cambiare l'attrezzo e fa ripetere il servizio.
        causa = CAUSE[esito.causa]
        variante = E.DOPPIO if esito.esito == "goal" else E.SINGOLO
        if causa.chiamata != "si_ripete":
            eventi.extend(self._fischio_e_chiamata(variante, causa.chiamata, causa=esito.causa))
        if esito.punti:
            eventi.append(self._arbitro(E.PUNTO, 0.0, punti=esito.punti, a_chi=esito.a_chi, esito=esito.esito, causa=esito.causa))
        else:
            eventi.append(self._arbitro(E.RIPETIZIONE, 0.0, chiamata="si_ripete", esito=esito.esito, causa=esito.causa))
        self._attesa(t.PAUSA_FRA_PUNTI)
        return eventi

    def _dati_colpo(self, p):
        dati = {"pressione" if p.esito == "colpo" else "qualita": round(p.valore, 1), "prob": _arrotonda(p.prob)}
        if p.chi.cambiovelocita and p.esito == "colpo":
            dati["cambio_velocita"] = True
        return dati

    def _prossima_parata(self, passi, i):
        """Il passo della parata che segue, saltando un cambio di mano."""
        for p in passi[i + 1:]:
            if p.tipo == "parata":
                return p
            if p.tipo not in ("cambio_mano",):
                return None
        return None

    def _vola_verso_parata(self, eventi, chi, pos, p, passi, i, colpo_n, ribattuta=False):
        """Il volo fino alla parata che segue, con l'arrivo dove la parata avviene; per un goal, fino in porta."""
        parata = self._prossima_parata(passi, i)
        if parata is None:
            raise ErroreMotore("Un colpo senza la parata che segue.")
        difensore = parata.chi.id
        zona = parata.zona
        causa = parata.causa
        if p.tipo == "battuta":
            # L'arrivo vero della battuta è già stato scelto alla ripresa, insieme alla partenza.
            u, v = self._arrivo_battuta_locale
            arrivo = locale_in_assoluto(self.campo[chi].parte, u, v)
            sponde = self._sponde(chi, p.colpo)
            v0 = self._velocita(chi, self.tar.COLPI[p.colpo].velocita)
        else:
            if ribattuta:
                sponde = ()
                v0 = self.tar.VELOCITA_RIBATTUTA * (1.0 + self._uniforme(-0.1, 0.1))
            else:
                sponde = self._sponde(chi, p.colpo)
                v0 = self._velocita(chi, self.tar.COLPI[p.colpo].velocita)
            arrivo = self._arrivo_dopo_la_parata(parata, self._punto_parata(difensore, zona))
            if parata.esito == "goal" or (parata.esito == "fallo" and causa == "difesa_irregolare"):
                sponde = self._sponde_compatibili(sponde, pos, arrivo)
        tipo_arrivo = "paletta"
        if parata.esito == "goal":
            tipo_arrivo = "porta"
        elif parata.esito == "fallo" and causa in ("body_touch", "body_touch_pieno"):
            tipo_arrivo = "corpo"
        volo = self._volo(pos, arrivo, sponde, v0, tipo_arrivo)
        dati = {"verso": difensore}
        if ribattuta:
            dati["ribattuta"] = True
        evento = self._evento_volo(chi, volo, p.colpo, dati)
        evento.colpo_n = colpo_n
        if p.tipo != "battuta" and self.campo[chi].cambiovelocita and not ribattuta:
            evento.dati = {**(evento.dati or {}), "cambio_velocita": True}
        eventi.append(evento)
        if parata.esito == "goal":
            # La parata che non arriva: un attimo prima che la pallina entri.
            fine = volo[-1].t
            self.t = fine - 0.05
            quasi = posizione_al_tempo(volo, self.t)
            self.t = max(self.t, volo[0].t)
            return quasi
        return arrivo

    def _arrivo_dopo_la_parata(self, parata, arrivo):
        """
        Dove arriva davvero la pallina, dato l'arrivo alla parata: per un goal entra a non più di
        12 cm dal centro della tasca, per una difesa irregolare è toccata dentro l'area di porta,
        per un body touch colpisce il corpo fra 5 e 25 cm dalla linea; altrimenti resta dov'era.
        """
        parte_dif = parata.chi.parte
        causa = parata.causa
        if parata.esito == "goal" or (parata.esito == "fallo" and causa == "difesa_irregolare"):
            porta = centro_porta(parte_dif)
            raggio = self._uniforme(2.0, 12.0 if parata.esito == "goal" else RAGGIO_AREA_PORTA - 1.0)
            angolo = self._uniforme(0.15 * math.pi, 0.85 * math.pi)
            verso_il_tavolo = 1.0 if porta[1] == 0 else -1.0
            return porta[0] + raggio * math.cos(angolo), porta[1] + verso_il_tavolo * raggio * math.sin(angolo)
        if parata.esito == "fallo" and causa in ("body_touch", "body_touch_pieno"):
            d = self._uniforme(5.0, 25.0)
            return arrivo[0], d if parte_dif == "A" else LUNGHEZZA_TAVOLO - d
        return arrivo

    def _sponde_compatibili(self, sponde, partenza, arrivo):
        """Le sponde del colpo, se il volo verso la porta le può ancora toccare; altrimenti un tiro diretto."""
        try:
            traiettoria(partenza, arrivo, sponde, 500.0, 0.0, 0.0, 0.0)
        except ErroreMotore:
            return ()
        return sponde

    def _volo_debole(self, eventi, chi, pos, p, colpo_n):
        """Il colpo debole si ferma da solo fra 120 e 280 cm dalla linea di chi ha colpito, prima di arrivare all'avversario."""
        parte = self.campo[chi].parte
        u = pos[0] if parte == "A" else LARGHEZZA_TAVOLO - pos[0]
        v_fermo = self._uniforme(120.0, 280.0)
        u_fermo = min(LARGHEZZA_TAVOLO - MARGINE_GIOCO, max(MARGINE_GIOCO, u + self._uniforme(-20.0, 20.0)))
        arrivo = locale_in_assoluto(parte, u_fermo, v_fermo)
        lunghezza = math.hypot(arrivo[0] - pos[0], arrivo[1] - pos[1])
        v0 = self._uniforme(80.0, 140.0)
        decelerazione = v0 * v0 / (2.0 * lunghezza)
        volo = self._volo(pos, arrivo, (), v0, "fermo", decelerazione)
        evento = self._evento_volo(chi, volo, p.colpo)
        evento.colpo_n = colpo_n
        eventi.append(evento)
        return arrivo

    def _volo_del_fallo(self, eventi, chi, pos, p, colpo_n):
        """Il volo di un attacco che finisce in fallo: contro lo schermo, sopra, fuori, sulla tavola di contatto o al soffitto."""
        causa = p.causa
        parte = self.campo[chi].parte
        if causa == "paletta_caduta":
            return pos
        avanti = 1.0 if parte == "A" else -1.0
        v0 = self._velocita(chi, self.tar.COLPI[p.colpo].velocita)
        x = min(LARGHEZZA_TAVOLO - MARGINE_GIOCO, max(MARGINE_GIOCO, pos[0] + self._uniforme(-30.0, 30.0)))
        if causa == "schermo_contro":
            arrivo = (x, META_TAVOLO - avanti * 2.0)
            volo = self._volo(pos, arrivo, (), v0, "schermo")
        elif causa in ("schermo_sopra", "out_soffitto", "out_volo", "out_tavola_contatto", "out_sponda"):
            volo = self._volo_aereo(pos, causa, parte, v0)
        else:
            raise ErroreMotore(f"Volo di un fallo d'attacco sconosciuto: {causa}")
        evento = self._evento_volo(chi, volo, p.colpo)
        evento.colpo_n = colpo_n
        eventi.append(evento)
        # Il fallo si segna nell'ultimo punto del volo che sta sul tavolo.
        dentro = [tappa for tappa in volo if _dentro((tappa.x, tappa.y))]
        return (dentro[-1].x, dentro[-1].y)

    def _volo_aereo(self, pos, causa, parte, v0):
        """I voli che lasciano il piano del tavolo: tappe scritte a mano fra punti fissi, a velocità costante."""
        avanti = 1.0 if parte == "A" else -1.0
        lato = 1.0 if self.rng.random() < 0.5 else -1.0
        punti = []
        if causa == "schermo_sopra":
            meta = (pos[0], META_TAVOLO)
            punti = [(meta, "sopra_schermo"), ((pos[0], META_TAVOLO + avanti * self._uniforme(60.0, 140.0)), "arrivo")]
        elif causa == "out_soffitto":
            punti = [((pos[0], pos[1] + avanti * 80.0), "soffitto"), ((pos[0] + lato * 40.0, pos[1] + avanti * 150.0), "terra")]
        elif causa == "out_volo":
            bordo = CENTRO_X + lato * CENTRO_X
            punti = [((bordo, pos[1] + avanti * 120.0), "fuori"), ((bordo + lato * 40.0, pos[1] + avanti * 170.0), "terra")]
        elif causa == "out_tavola_contatto":
            fondo = LUNGHEZZA_TAVOLO if parte == "A" else 0.0
            x = min(LARGHEZZA_TAVOLO - MARGINE_GIOCO, max(MARGINE_GIOCO, pos[0] + self._uniforme(-25.0, 25.0)))
            punti = [((x, fondo), "tavola_contatto"), ((x, fondo + avanti * 40.0), "terra")]
        else:
            # out_sponda: la pallina salta la sponda o la curva e finisce a terra.
            y = pos[1] + avanti * self._uniforme(120.0, 300.0)
            bordo = CENTRO_X + lato * CENTRO_X
            punti = [((bordo, y), "fuori"), ((bordo + lato * 35.0, y + avanti * 20.0), "terra")]
        return self._tappe_a_mano(pos, punti, v0)

    def _tappe_a_mano(self, pos, punti, v0, rallenta=0.8):
        """Un volo per punti fissi, ciascuno col suo tipo: ogni tratto a velocità costante, che poi cala."""
        tappe = [Tappa(self.t, pos[0], pos[1], v0, "partenza")]
        t, prima, v = self.t, pos, v0
        for punto, tipo in punti:
            lunghezza = math.hypot(punto[0] - prima[0], punto[1] - prima[1])
            t += lunghezza / max(v, 50.0)
            v *= rallenta
            tappe.append(Tappa(t, punto[0], punto[1], v if tipo not in E.TAPPE_TERMINALI else 0.0, tipo))
            prima = punto
        return tuple(tappe)

    def _volo_battuta_irregolare(self, eventi, chi, pos, p):
        """
        Il volo della battuta irregolare, secondo la causa, perché nella partita live il fallo si
        distingua dal suono di ciò che fa la pallina. Senza rimbalzo: dritta sotto lo schermo,
        senza sponde. Due rimbalzi: due sponde prima dello schermo. Strisciata: la pallina tocca la
        sponda e la percorre fin oltre lo schermo. Fuori in volo e sopra lo schermo, le cause
        critiche: il volo che lascia il tavolo. Il colpo a vuoto, la battuta prima del fischio e
        quella oltre i due secondi non hanno volo, perché il fallo è di chi batte, nel momento in
        cui batte; il doppio tocco fa fare alla pallina pochi centimetri. Il fallo si segna
        nell'ultimo punto del volo che sta sul tavolo, o nella mano di chi batte.
        """
        causa = p.causa
        if causa in ("battuta_a_vuoto", "battuta_prima_del_fischio", "battuta_oltre_due_secondi"):
            return pos
        parte = self.campo[chi].parte
        destra = p.colpo == "battutadx"
        v0 = self._velocita(chi, self.tar.COLPI[p.colpo].velocita)

        def locale(u, v):
            # Dal riferimento della battuta sinistra a quello assoluto: la destra è lo specchio.
            return locale_in_assoluto(parte, LARGHEZZA_TAVOLO - u if destra else u, v)

        u_s, v_s = locale_in_assoluto(parte, *pos)
        if destra:
            u_s = LARGHEZZA_TAVOLO - u_s
        dati = None
        if causa in ("out_volo", "schermo_sopra"):
            volo = self._volo_aereo(pos, causa, parte, v0)
        elif causa == "battuta_doppio_tocco":
            arrivo = locale(min(LARGHEZZA_TAVOLO - MARGINE_GIOCO, max(MARGINE_GIOCO, u_s + self._uniforme(-6.0, 6.0))), v_s + self._uniforme(10.0, 30.0))
            volo = self._volo(pos, arrivo, (), self._uniforme(80.0, 150.0), "arrivo")
        elif causa == "battuta_senza_rimbalzo":
            arrivo = locale(self._uniforme(20.0, LARGHEZZA_TAVOLO - 20.0), self._uniforme(220.0, 320.0))
            volo = self._volo(pos, arrivo, (), v0, "arrivo")
        elif causa == "battuta_due_rimbalzi":
            # Due sponde prima dello schermo: sinistra e poi destra, viste dalla battuta sinistra.
            # Col metodo delle immagini il secondo rimbalzo sta prima di 175 cm dalla linea se
            # l'arrivo non va oltre v_massima.
            u_a = self._uniforme(MARGINE_GIOCO + 4.0, 40.0)
            orizzontale = (u_s - SPONDA_SINISTRA_A) + (SPONDA_DESTRA_A - SPONDA_SINISTRA_A) + (SPONDA_DESTRA_A - u_a)
            v_massima = v_s + (175.0 - v_s) * orizzontale / (u_s - SPONDA_SINISTRA_A + SPONDA_DESTRA_A - SPONDA_SINISTRA_A)
            arrivo = locale(u_a, self._uniforme(META_TAVOLO + 12.0, min(280.0, v_massima)))
            nomi_sponde = ("destra", "sinistra") if destra else ("sinistra", "destra")
            volo = self._volo(pos, arrivo, tuple(sponda_assoluta(parte, s) for s in nomi_sponde), v0, "arrivo")
        elif causa == "battuta_strisciata":
            # La pallina tocca la sponda presto e la percorre, strisciando, fin oltre lo schermo.
            sponda_u = SPONDA_SINISTRA_A
            punti = [(locale(sponda_u, self._uniforme(60.0, 120.0)), "sponda"), (locale(sponda_u, META_TAVOLO), "sotto_schermo"),
                     (locale(sponda_u + self._uniforme(0.0, 4.0), self._uniforme(220.0, 280.0)), "arrivo")]
            volo = self._tappe_a_mano(pos, punti, v0, rallenta=0.7)
            dati = {"strisciata": True}
        else:
            raise ErroreMotore(f"Volo di una battuta irregolare sconosciuto: {causa}")
        evento = self._evento_volo(chi, volo, p.colpo, dati)
        eventi.append(evento)
        dentro = [tappa for tappa in volo if _dentro((tappa.x, tappa.y))]
        return (dentro[-1].x, dentro[-1].y)

    def _esito_finale(self, eventi, p, pos, esito, punteggio, passi, i, colpo_n):
        """L'evento decisivo del punto, con la sua posizione, e dove resta la pallina."""
        chi = p.chi.id
        causa = CAUSE[p.causa]
        comuni = {"esito": esito.esito, "causa": p.causa, "critico": p.critico, "chiamata": causa.chiamata, "punti": esito.punti, "a_chi": esito.a_chi,
                  "colpo": esito.colpo_decisivo, "colpo_n": colpo_n, "dati": {"zona": esito.zona, "origine": esito.origine, "attacchi": esito.attacchi,
                                                                                "battitore": esito.battitore, "ricevitore": esito.ricevitore}}
        self.punteggio = punteggio
        if p.tipo == "goal":
            # La pallina entra nella porta di chi subisce: anche l'autogoal, dove la pallina sfugge
            # a chi difende e finisce nella sua porta.
            porta_di = altra(p.chi.parte)
            if p.causa == "goal_dopo_difesa_irregolare":
                difensore = self._ultimo_difensore(passi, i)
                porta = centro_porta(difensore.parte)
                volo = self._volo(pos, (porta[0], porta[1] + (4.0 if porta[1] == 0 else -4.0)), (), 120.0, "porta")
                eventi.append(self._evento_volo(difensore.id, volo))
            ultimo_volo = next((e for e in reversed(eventi) if e.tipo == E.VOLO), None)
            if ultimo_volo is not None and ultimo_volo.volo[-1].tipo == "porta":
                self.t = max(self.t, ultimo_volo.t + ultimo_volo.durata)
                pos = (ultimo_volo.volo[-1].x, ultimo_volo.volo[-1].y)
            else:
                porta = centro_porta(porta_di)
                pos = (porta[0], porta[1] + (4.0 if porta[1] == 0 else -4.0))
            eventi.append(self._evento(E.GOAL, 0.0, chi, pos, fischio=E.DOPPIO, **comuni))
            self.pallina = "tasca"
        elif p.tipo == "fallo":
            eventi.append(self._evento(E.FALLO, 0.0, chi, pos, fischio=E.SINGOLO, **comuni))
            ultimo_volo = next((e for e in reversed(eventi) if e.tipo == E.VOLO), None)
            fuori = ultimo_volo is not None and ultimo_volo.volo[-1].tipo == "terra"
            self.pallina = "terra" if fuori else "tavolo"
        elif p.tipo == "palla_morta":
            if p.causa == "ribattuta_lenta":
                pos = self._volo_ribattuta_lenta(eventi, chi, pos, colpo_n)
            if p.causa in ("pallina_ferma", "colpo_debole", "ribattuta_lenta"):
                self._attesa(2.0)
            eventi.append(self._evento(E.PALLA_MORTA, 0.0, chi, pos, fischio=E.SINGOLO, **comuni))
            self.pallina = "tavolo"
        else:
            # La rottura, regole IBSA 15.9.3 e 15.10.2: il fischio singolo ferma il gioco subito,
            # poi l'attrezzo si cambia, e alla fine si ripete il servizio.
            eventi.append(self._evento(E.ROTTURA, 0.0, chi, pos, fischio=E.SINGOLO, **comuni))
            eventi.append(self._fischio(E.SINGOLO))
            eventi.append(self._evento(E.SOSTITUZIONE_ATTREZZO, self.tar.DURATA_CAMBIO_ATTREZZO / self.velocita, None, self._pos_arbitro(),
                                       causa=p.causa, dati={"attrezzo": "paletta" if p.causa == "paletta_rotta" else "pallina", "di": chi}))
            self.pallina = "arbitro"
        self.pos_pallina = pos
        return pos

    def _ultimo_difensore(self, passi, i):
        for p in reversed(passi[:i]):
            if p.tipo == "parata":
                return p.chi
        raise ErroreMotore("Una difesa irregolare senza parata.")

    def _volo_ribattuta_lenta(self, eventi, chi, pos, colpo_n):
        parte = self.campo[chi].parte
        u = pos[0] if parte == "A" else LARGHEZZA_TAVOLO - pos[0]
        v_fermo = self._uniforme(80.0, 170.0)
        arrivo = locale_in_assoluto(parte, min(LARGHEZZA_TAVOLO - MARGINE_GIOCO, max(MARGINE_GIOCO, u + self._uniforme(-25.0, 25.0))), v_fermo)
        lunghezza = max(1.0, math.hypot(arrivo[0] - pos[0], arrivo[1] - pos[1]))
        v0 = self._uniforme(50.0, 90.0)
        volo = self._volo(pos, arrivo, (), v0, "fermo", v0 * v0 / (2.0 * lunghezza))
        evento = self._evento_volo(chi, volo, None, {"ribattuta": True})
        evento.colpo_n = colpo_n
        eventi.append(evento)
        return arrivo

    # Sanzioni, pause, cambi.

    def sanzione(self, g, tipo, causa, seconda, punteggio):
        self.punteggio = punteggio
        eventi = [self._fischio(E.SINGOLO)]
        tipo_evento = E.PENALITA if tipo == "penalita" else E.AMMONIZIONE
        pos = locale_in_assoluto(g.parte, CENTRO_X, -20.0)
        pos = (pos[0], min(max(pos[1], 0.0), float(LUNGHEZZA_TAVOLO)))
        punti = 2 if tipo == "penalita" else 0
        self._attesa(max(0.0, self.tar.RITARDO_CHIAMATA - self.tar.FISCHIO_SINGOLO))
        eventi.append(self._evento(tipo_evento, self.tar.DURATA_CHIAMATA, g.id, pos, causa=causa, chiamata=tipo, punti=punti,
                                   a_chi=altra(g.parte) if punti else None, dati={"seconda_infrazione": seconda}))
        return eventi

    def timeout(self, g):
        """Il time-out chiesto dal giocatore: un minuto, con l'avviso dei 15 secondi."""
        self.fase = E.PAUSA
        eventi = [self._fischio(E.SINGOLO)]
        eventi.append(self._evento(E.TIMEOUT_INIZIO, 0.0, g.id, locale_in_assoluto(g.parte, CENTRO_X, 0.0), chiamata="time_out"))
        self._attesa(45.0)
        eventi.append(self._arbitro(E.AVVISO_TEMPO, 0.0, chiamata="quindici_secondi", dati={"restano": 15}))
        self._attesa(15.0)
        eventi.append(self._evento(E.TIMEOUT_FINE, 0.0, g.id, locale_in_assoluto(g.parte, CENTRO_X, 0.0)))
        self.fase = E.GIOCO
        return eventi

    def cambio_campo(self, fra_set):
        """Il cambio campo, fra i set o a metà dell'ultimo set: un minuto, con l'avviso a 45 secondi; l'arbitro passa all'altro lato."""
        self.fase = E.PAUSA
        eventi = []
        if not fra_set:
            eventi.append(self._fischio(E.SINGOLO))
        eventi.append(self._arbitro(E.CAMBIO_CAMPO_INIZIO, 0.0, chiamata="cambio_campo", dati={"fra_set": fra_set}))
        self.arbitro_a_sinistra = not self.arbitro_a_sinistra
        self._attesa(45.0)
        eventi.append(self._arbitro(E.AVVISO_TEMPO, 0.0, chiamata="quindici_secondi", dati={"restano": 15}))
        self._attesa(15.0)
        eventi.append(self._arbitro(E.CAMBIO_CAMPO_FINE, 0.0))
        self.fase = E.GIOCO
        self.pallina = "arbitro"
        return eventi

    def cambio_battitore(self, nuovo):
        return [self._evento(E.CAMBIO_BATTITORE, 0.0, nuovo.id, locale_in_assoluto(nuovo.parte, CENTRO_X, 25.0))]

    def cambio_al_tavolo(self, esce, battitore, entra):
        """Nella gara a squadre il battitore lascia il tavolo: chi ha ricevuto batte contro chi entra."""
        evento = self._evento(E.CAMBIO_AL_TAVOLO, 6.0 / self.velocita, entra.id, locale_in_assoluto(entra.parte, CENTRO_X, 25.0),
                              dati={"esce": esce.id, "entra": entra.id, "batte": battitore.id})
        return [evento]

    def fine_set(self, set_n, punteggio, set_vinti, ultimo):
        self.punteggio = punteggio
        self.fase = E.CHIUSURA if ultimo else E.PAUSA
        eventi = [self._fischio(E.LUNGO)]
        eventi.append(self._arbitro(E.FINE_SET, 0.0, dati={"set": set_n, "punteggio": list(punteggio), "set_vinti": list(set_vinti), "ultimo": ultimo}))
        return eventi

    def fine_incontro(self, set_vinti, set_giocati):
        self.fase = E.CHIUSURA
        return [self._arbitro(E.FINE_INCONTRO, 0.0, dati={"set_vinti": list(set_vinti), "set": [list(s) for s in set_giocati]})]


def _arrotonda(prob):
    if prob is None:
        return None
    return [round(p, 4) for p in prob]


def controlla_invarianti(eventi):
    """
    I problemi di una sequenza di eventi, in una lista vuota se va tutto bene: progressivi
    crescenti e istanti che non tornano indietro, coordinate dentro il tavolo, voli coerenti, lati
    uguali alla posizione, un solo punto o una sola ripetizione per punto, il fischio doppio per
    ogni goal e quello singolo per ogni fallo, la battuta regolare con una sponda sola prima dello
    schermo, e il fischio singolo nell'istante stesso di una rottura.
    """
    problemi = []
    precedente = None
    esiti_per_punto = {}
    for indice, ev in enumerate(eventi):
        if precedente is not None:
            if ev.n <= precedente.n:
                problemi.append(f"Evento {ev.n}: il progressivo non cresce.")
            if ev.t + 1e-6 < precedente.t:
                problemi.append(f"Evento {ev.n} {ev.tipo}: l'istante {ev.t} torna indietro rispetto a {precedente.t}.")
        precedente = ev
        if ev.tipo not in E.TIPI:
            problemi.append(f"Evento {ev.n}: tipo sconosciuto {ev.tipo}.")
        finisce_fuori = ev.volo is not None and ev.tipo == E.VOLO and ev.volo[-1].tipo in E.TAPPE_FUORI
        if ev.pos is not None and ev.chi is not None and not finisce_fuori and not _dentro(ev.pos):
            problemi.append(f"Evento {ev.n} {ev.tipo}: posizione fuori dal tavolo {ev.pos}.")
        if ev.pos is not None and ev.lato != lato_di(ev.pos[0], ev.parte or "A"):
            problemi.append(f"Evento {ev.n} {ev.tipo}: il lato {ev.lato} non corrisponde alla posizione.")
        if ev.volo is not None:
            problemi.extend(_controlla_volo(ev))
        if ev.tipo in (E.PUNTO, E.RIPETIZIONE):
            chiave = (ev.set_n, ev.punto_n)
            esiti_per_punto[chiave] = esiti_per_punto.get(chiave, 0) + 1
        if ev.tipo in (E.GOAL, E.FALLO):
            atteso = E.DOPPIO if ev.tipo == E.GOAL else E.SINGOLO
            seguente = next((e for e in eventi[indice + 1:] if e.tipo == E.FISCHIO), None)
            if ev.fischio != atteso or seguente is None or seguente.fischio != atteso:
                problemi.append(f"Evento {ev.n} {ev.tipo}: il fischio non è {atteso}.")
            if ev.causa not in CAUSE:
                problemi.append(f"Evento {ev.n} {ev.tipo}: causa sconosciuta {ev.causa}.")
        seguente = eventi[indice + 1] if indice + 1 < len(eventi) else None
        if ev.tipo == E.BATTUTA and ev.esito == "regolare":
            problemi.extend(_controlla_battuta(ev, seguente))
        if ev.tipo == E.ROTTURA and (seguente is None or seguente.tipo != E.FISCHIO or seguente.fischio != E.SINGOLO or abs(seguente.t - ev.t) > 1e-6):
            problemi.append(f"Evento {ev.n}: la rottura non è seguita subito dal fischio singolo.")
    for chiave, quanti in esiti_per_punto.items():
        if quanti != 1:
            problemi.append(f"Set {chiave[0]}, punto {chiave[1]}: {quanti} eventi di punto o ripetizione.")
    return problemi


def _controlla_battuta(battuta, volo):
    """La battuta regolare, regola IBSA 15.3.7: il suo volo tocca una sponda sola prima dello schermo, e passa sotto."""
    if volo is None or volo.tipo != E.VOLO or volo.volo is None:
        return [f"Evento {battuta.n}: la battuta regolare non ha il suo volo."]
    tipi = [tappa.tipo for tappa in volo.volo]
    if "sotto_schermo" not in tipi:
        return [f"Evento {volo.n}: la battuta regolare non passa sotto lo schermo."]
    sponde = sum(1 for tipo in tipi[:tipi.index("sotto_schermo")] if tipo in ("sponda", "curva"))
    if sponde != 1:
        return [f"Evento {volo.n}: la battuta regolare tocca {sponde} sponde prima dello schermo invece di una."]
    return []


def _dentro(pos):
    x, y = pos
    return -1e-6 <= x <= LARGHEZZA_TAVOLO + 1e-6 and -1e-6 <= y <= LUNGHEZZA_TAVOLO + 1e-6


def _controlla_volo(ev):
    problemi = []
    volo = ev.volo
    if abs(volo[0].t - ev.t) > 2e-3:
        problemi.append(f"Evento {ev.n} {ev.tipo}: il volo non comincia con l'evento.")
    if ev.tipo == E.VOLO and abs((volo[-1].t - volo[0].t) - ev.durata) > 2e-3:
        problemi.append(f"Evento {ev.n}: la durata del volo non corrisponde alle tappe.")
    for prima, dopo in itertools.pairwise(volo):
        if dopo.t + 1e-9 < prima.t:
            problemi.append(f"Evento {ev.n}: le tappe del volo tornano indietro nel tempo.")
    for tappa in volo:
        if tappa.tipo not in E.TAPPE:
            problemi.append(f"Evento {ev.n}: tappa di tipo sconosciuto {tappa.tipo}.")
        if tappa.tipo not in E.TAPPE_FUORI and not _dentro((tappa.x, tappa.y)):
            problemi.append(f"Evento {ev.n}: la tappa {tappa.tipo} sta fuori dal tavolo, a {tappa.x:.1f}, {tappa.y:.1f}.")
        if tappa.tipo == "sponda" and min(abs(tappa.x - SPONDA_SINISTRA_A), abs(tappa.x - SPONDA_DESTRA_A)) > 1e-6:
            problemi.append(f"Evento {ev.n}: un rimbalzo non sta su una sponda.")
        if tappa.tipo in ("curva",) and not (tappa.y < FONDO_A + 30 or tappa.y > FONDO_B - 30):
            problemi.append(f"Evento {ev.n}: una curva lontana dagli angoli.")
    return problemi
