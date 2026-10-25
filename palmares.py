"""
Il palmarès di MESS: i punti delle medaglie e delle coppe nella gloria, e i punti della classifica mondiale.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-14 con la tappa 12, decisione D32, risposta 11 di Gabriele e punti 5.9 e 9.2 del
progetto. Qui stanno i conti, senza il mondo: le chiusure dei tornei stanno in premiazioni.py.
La gloria di una polisportiva conta le medaglie dei suoi tesserati e le sue coppe degli ultimi 5
anni del calendario simulato, circa 20 mesi veri, regola di Gabriele; il palmarès storico resta nei
contatori di sempre e si legge nella scheda. Ogni polisportiva tiene il suo palmarès recente come
un dizionario dal mese, AAAA-MM, a una coppia di punti, medaglie e coppe, già pesati per l'importanza:
30 per un oro, 15 per un argento, 5 per un bronzo, 1 per un legno; 100, 50, 20 e 5 per le coppe, che
nelle sfide hanno l'importanza IMPORTANZA_COPPA_SFIDA, un cinquantesimo di quella della Coppa delle
polisportive. Dalla decisione 3 di Gabriele del 14 ottobre 2026 la coppa d'argento di una sfida vale
soltanto QUOTA_GLORIA_ARGENTO_SFIDA di quella d'oro: la conta sfide._posta. I mesi più vecchi della
finestra si tolgono il primo del mese.
La classifica mondiale è per sempre, come un medagliere storico, scelta di Gabriele: a ogni chiusura
ogni partecipante prende l'importanza del torneo per i punti del suo posto, che vanno nei punti
mondiali, per sempre, e nei punti recenti, una lista di coppie di giorno e punti dell'ultimo anno,
che servono alla qualificazione al mondiale.
Dal 2026-10-25, con la barra di stato su misura di D38, le righe e la chiave della classifica mondiale si leggono anche
a parte, così la barra conta chi sta davanti al tuo migliore invece di ordinare tutti. È di Gabriele Battaglia
(IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import datetime

from costanti import (
    GIORNI_PUNTI_RECENTI,
    MESI_PALMARES_GLORIA,
    PUNTI_CLASSIFICA,
    PUNTI_COPPE_GLORIA,
    PUNTI_MEDAGLIE_GLORIA,
)

MEDAGLIE = ("oro", "argento", "bronzo", "legno")


def punti_medaglia(medaglia, importanza=1.0):
    """I punti di gloria di una medaglia di un tesserato, per l'importanza del torneo: 30 per un oro."""
    return PUNTI_MEDAGLIE_GLORIA[medaglia] * importanza


def punti_coppa(coppa, importanza=1.0):
    """I punti di gloria di una coppa, per l'importanza: 100 per un oro della coppa d'importanza 1."""
    return PUNTI_COPPE_GLORIA[coppa] * importanza


def mese(data):
    """Il mese di una data nel palmarès recente: AAAA-MM."""
    return f"{data.year:04d}-{data.month:02d}"


def _indice_del_mese(chiave):
    anno, mese_numero = chiave.split("-")
    return int(anno) * 12 + int(mese_numero) - 1


def aggiungi(poli, data, punti_medaglie=0.0, punti_coppe=0.0):
    """Aggiunge al palmarès recente della polisportiva i punti delle medaglie e delle coppe del mese della data."""
    chiave = mese(data)
    voce = poli.palmares_recente.setdefault(chiave, [0.0, 0.0])
    voce[0] += float(punti_medaglie)
    voce[1] += float(punti_coppe)


def nella_finestra(chiave, oggi):
    """Vero se il mese è dentro la finestra della gloria che finisce oggi: gli ultimi MESI_PALMARES_GLORIA mesi, quello di oggi compreso."""
    distanza = _indice_del_mese(mese(oggi)) - _indice_del_mese(chiave)
    return 0 <= distanza < MESI_PALMARES_GLORIA


def somma_finestra(poli, oggi):
    """
    I punti delle medaglie e delle coppe della polisportiva negli ultimi 5 anni del calendario, fino a
    oggi, sommati nello stesso ordine di sempre, così i numeri restano uguali fino all'ultimo bit. Il
    mese di oggi si calcola una volta sola e quello di ogni chiave senza chiamate, perché la revisione
    del 14 ottobre 2026 ha visto che nella_finestra, chiamata per ogni mese di ogni polisportiva ogni
    giorno, era la catena più cara del giorno a regime. Le chiavi hanno sempre la forma AAAA-MM di mese().
    """
    fine = oggi.year * 12 + oggi.month - 1
    finestra = _mesi_della_finestra(fine)
    medaglie = coppe = 0.0
    for chiave, (m, c) in poli.palmares_recente.items():
        # Dalla decisione 4 di Gabriele del 14 ottobre 2026 i mesi della finestra si scrivono una volta
        # sola, e una chiave che non è fra loro si guarda col conto di sempre: così anche una chiave
        # scritta in un'altra forma resta dove stava.
        if chiave in finestra or 0 <= fine - (int(chiave[:4]) * 12 + int(chiave[5:7]) - 1) < MESI_PALMARES_GLORIA:
            medaglie += m
            coppe += c
    return medaglie, coppe


_FINESTRE = {}


def _mesi_della_finestra(fine):
    """Le chiavi AAAA-MM dei mesi della finestra della gloria che finisce col mese numero fine, contato da gennaio dell'anno zero."""
    finestra = _FINESTRE.get(fine)
    if finestra is None:
        if len(_FINESTRE) > 1000:
            _FINESTRE.clear()
        # Soltanto gli anni di quattro cifre, la forma di mese(), che il conto di sempre legge allo stesso modo.
        finestra = _FINESTRE[fine] = frozenset(f"{indice // 12:04d}-{indice % 12 + 1:02d}" for indice in range(fine - MESI_PALMARES_GLORIA + 1, fine + 1)
                                               if 0 <= indice < 10000 * 12)
    return finestra


def sfoltisci(poli, oggi):
    """Toglie dal palmarès recente i mesi usciti dalla finestra, col conto veloce di somma_finestra; restituisce quanti ne ha tolti."""
    fine = oggi.year * 12 + oggi.month - 1
    vecchi = [chiave for chiave in poli.palmares_recente if not 0 <= fine - (int(chiave[:4]) * 12 + int(chiave[5:7]) - 1) < MESI_PALMARES_GLORIA]
    for chiave in vecchi:
        del poli.palmares_recente[chiave]
    return len(vecchi)


def punti_classifica(posto, importanza=1.0):
    """I punti della classifica mondiale di un piazzamento: 100 al primo, 70, 50 e 40, 25 fino all'ottavo, 12 al sedicesimo, 5 al trentaduesimo, 1 agli altri, per l'importanza."""
    for fino_a, punti in PUNTI_CLASSIFICA:
        if fino_a is None or posto <= fino_a:
            return punti * importanza
    return 0.0


def aggiungi_punti(g, data, punti):
    """I punti di un piazzamento al giocatore: nei punti mondiali, per sempre, e nei punti recenti, con il giorno."""
    g.punti_mondiali += punti
    g.punti_recenti.append([data.toordinal() if isinstance(data, datetime.date) else int(data), float(punti)])


def sfoltisci_punti(g, oggi):
    """Toglie dai punti recenti quelli più vecchi di un anno."""
    limite = oggi.toordinal() - GIORNI_PUNTI_RECENTI
    g.punti_recenti[:] = [voce for voce in g.punti_recenti if voce[0] > limite]


def punti_dell_anno(g, oggi):
    """I punti della classifica dell'ultimo anno, fino a oggi, per la qualificazione al mondiale."""
    limite = oggi.toordinal() - GIORNI_PUNTI_RECENTI
    return sum(punti for giorno, punti in g.punti_recenti if giorno > limite)


def classifica_mondiale(mondo, sesso):
    """
    La classifica mondiale per sempre di un sesso, come un medagliere storico: i giocatori vivi,
    ritirati compresi, e le vecchie glorie, con i punti, le medaglie e i titoli mondiali, dal primo.
    Ogni riga è un dizionario con id, nome, punti, ori, argenti, bronzi, legni, titoli e vivo.
    """
    return sorted(righe_mondiali(mondo, sesso), key=chiave_mondiale)


def chiave_mondiale(riga):
    """La chiave di una riga della classifica mondiale: chi l'ha più piccola sta davanti."""
    return _chiave_mondiale(riga["punti"], riga["ori"], riga["argenti"], riga["bronzi"], riga["id"])


def _chiave_mondiale(punti, ori, argenti, bronzi, numero):
    return -punti, -ori, -argenti, -bronzi, str(numero)


def _in_classifica(mondo, sessi):
    """
    Chi sta nella classifica mondiale di ciascuno dei sessi dati, in un giro solo: per sesso le coppie di numero e giocatore
    dei vivi, ritirati compresi, con dei punti o un oro, e le voci delle vecchie glorie con dei punti che non sono già fra i
    vivi, ciascuna una volta sola. Un numero è di una persona sola, quindi di un sesso solo.
    """
    morti = getattr(mondo, "_ids_morti_processati_sessione", set())
    vivi = {sesso: [] for sesso in sessi}
    for gid, g in mondo.giocatori.items():
        elenco = vivi.get(g.sesso)
        if elenco is not None and gid not in morti and (g.punti_mondiali > 0 or g.ori):
            elenco.append((gid, g))
    visti = {gid for elenco in vivi.values() for gid, _g in elenco}
    glorie = {sesso: [] for sesso in sessi}
    for voce in mondo.vecchie_glorie:
        elenco = glorie.get(voce.get("sesso"))
        if elenco is None or voce.get("id") in visti or not voce.get("punti_mondiali"):
            continue
        visti.add(voce.get("id"))
        elenco.append(voce)
    return {sesso: (vivi[sesso], glorie[sesso]) for sesso in sessi}


def righe_mondiali(mondo, sesso):
    """Le righe della classifica mondiale di un sesso, come classifica_mondiale, ma nell'ordine in cui si trovano."""
    vivi, glorie = _in_classifica(mondo, (sesso,))[sesso]
    # I titoli mondiali sono i mondiali vinti, come per le vecchie glorie: g.titoli tiene anche gli altri podi del mondiale.
    righe = [{"id": gid, "nome": f"{g.nome} {g.cognome}", "punti": g.punti_mondiali, "ori": g.ori, "argenti": g.argenti, "bronzi": g.bronzi,
              "legni": g.legni, "titoli": sum(1 for t in g.titoli if t.get("mondiale") and t.get("posto") == 1), "vivo": True} for gid, g in vivi]
    righe.extend({"id": voce.get("id"), "nome": f"{voce.get('nome', '')} {voce.get('cognome', '')}".strip(), "punti": voce.get("punti_mondiali", 0.0),
                  "ori": voce.get("ori", 0), "argenti": voce.get("argenti", 0), "bronzi": voce.get("bronzi", 0), "legni": voce.get("legni", 0),
                  "titoli": voce.get("titoli_mondiali", 0), "vivo": False} for voce in glorie)
    return righe


def posti_mondiali(mondo, ids):
    """
    Per sesso il posto nella classifica mondiale del migliore fra i giocatori ids, contando chi gli sta davanti senza
    ordinare né costruire le righe, in un giro solo per i due sessi; None per il sesso in cui nessuno di loro è in
    classifica. Per la barra di stato su misura, D38.
    """
    posti = {}
    for sesso, (vivi, glorie) in _in_classifica(mondo, ("m", "f")).items():
        tuoi = [_chiave_mondiale(g.punti_mondiali, g.ori, g.argenti, g.bronzi, gid) for gid, g in vivi if gid in ids]
        if not tuoi:
            posti[sesso] = None
            continue
        migliore = min(tuoi)
        punti = -migliore[0]
        # Chi ha più punti sta davanti, chi ne ha meno dietro: la chiave intera serve soltanto a pari punti.
        davanti = sum(1 for gid, g in vivi if g.punti_mondiali > punti
                      or (g.punti_mondiali == punti and _chiave_mondiale(g.punti_mondiali, g.ori, g.argenti, g.bronzi, gid) < migliore))
        for voce in glorie:
            punti_della_gloria = voce.get("punti_mondiali", 0.0)
            if punti_della_gloria > punti or (punti_della_gloria == punti and _chiave_mondiale(punti_della_gloria, voce.get("ori", 0), voce.get("argenti", 0),
                                                                                                  voce.get("bronzi", 0), voce.get("id")) < migliore):
                davanti += 1
        posti[sesso] = davanti + 1
    return posti
