"""
Le formule dei tornei di MESS: le fasi, la loro validazione e il file formule.json nella cartella del mondo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-13 con la tappa 12, decisioni D9 e D13 e punto 3.2 del progetto: copiato da
get_formulas_data, formulas_path e reset_formulas_cache di tournament_engine.py di Terminal Beast e
dalla validazione dei suoi dialoghi, con le chiavi in italiano e i difetti corretti.
Una formula ha un identificativo, un nome, una descrizione e un elenco ordinato di fasi. Ogni fase
ha un tipo, gironi o tabellone, i partecipanti, i gironi, i promossi per girone e la finalina, cioè
l'incontro per il terzo posto fra i due sconfitti delle semifinali. Come in Terminal Beast ogni turno
del tabellone è una fase: le fasi di tabellone consecutive, a tempo di gioco, sono un tabellone solo.
La validazione sta in un posto solo, qui, e non nei dialoghi: in Terminal Beast stava in due
finestre, la finalina su una fase a gironi mandava il motore in errore, e una formula eliminata
faceva ripiegare i suoi modelli, in silenzio, su un girone unico. Le regole: da 1 a 12 fasi;
partecipanti fra 2 e 1024; nei gironi almeno un girone, partecipanti divisibili per i gironi,
gironi da 2 a 12 componenti, promossi fra 1 e la grandezza meno 1, tranne nell'ultima fase, e niente
finalina; nel tabellone partecipanti potenza di 2, gironi e promossi a zero, e la finalina soltanto
con 4 partecipanti, cioè in semifinale, seguita dalla finale; la coerenza a cascata, cioè la fase
dopo ha i promossi di tutti i gironi o la metà dei partecipanti di un turno di tabellone; l'ultima
fase è un tabellone da 2, la finale, o un girone unico.
Qui sta anche la struttura adattata agli iscritti veri, punto 4.4 del progetto, perché dipende
soltanto dalla formula: la usano il motore dei tornei e la durata prevista dei modelli.
Le formule non stanno nel salvataggio, D9: ogni edizione aperta ne conserva una copia congelata,
così l'editor cambia soltanto le edizioni future.
"""

import contextlib
import copy
import json
import math
import os
import shutil

import percorsi

NOME_FILE = "formule.json"
# La copia predefinita, che viaggia col programma e si copia nella cartella del mondo al primo uso.
RISORSA = os.path.join("dati", "tornei", NOME_FILE)
GIRONI = "gironi"
TABELLONE = "tabellone"
TIPI = (GIRONI, TABELLONE)
FASI_MASSIME = 12
PARTECIPANTI_MINIMI = 2
PARTECIPANTI_MASSIMI = 1024
COMPONENTI_MINIMI = 2
COMPONENTI_MASSIMI = 12
# La finalina sta nella semifinale, il turno di tabellone con quattro partecipanti.
PARTECIPANTI_FINALINA = 4
NOME_MINIMO = 3
NOME_MASSIMO = 60
DESCRIZIONE_MASSIMA = 500
CAMPI_FASE = ("tipo", "partecipanti", "gironi", "promossi", "finalina")
CAMPI_FORMULA = ("id", "nome", "descrizione", "fasi")
PREFISSO_ID = "formula_"

# Le formule lette, valide e scartate, per file, finché qualcuno non riscrive il file o azzera la cache.
_CACHE = {}


def percorso_formule():
    """
    Il file delle formule nella cartella del mondo. Al primo uso, se manca, lo copia dalla risorsa che
    viaggia col programma, come formulas_path di Terminal Beast; se la copia non riesce, legge la
    risorsa stessa, e la prima scrittura lo creerà nella cartella del mondo.
    """
    percorso = percorsi.percorso(NOME_FILE)
    if not os.path.exists(percorso):
        origine = percorsi.risorsa(RISORSA)
        if os.path.exists(origine) and os.path.abspath(origine) != os.path.abspath(percorso):
            try:
                shutil.copy2(origine, percorso)
            except OSError:
                return origine
    return percorso


def azzera_cache():
    """Le formule si rileggono dal file alla prossima richiesta."""
    _CACHE.clear()


def _intero(valore):
    return isinstance(valore, int) and not isinstance(valore, bool)


def potenza_di_due(n):
    return _intero(n) and n >= 1 and n & (n - 1) == 0


def partecipanti_dopo(fase):
    """Quanti partecipanti passano alla fase dopo: i promossi di tutti i gironi, oppure la metà dopo un turno di tabellone."""
    if fase["tipo"] == GIRONI:
        return fase["gironi"] * fase["promossi"]
    return fase["partecipanti"] // 2


def valida_fase(fase, indice, ultima):
    """
    None se la fase, la numero indice contando da zero, va bene da sola; altrimenti il motivo, in
    una frase. ultima dice se è l'ultima della formula, dove i promossi non contano.
    """
    numero = indice + 1
    if not isinstance(fase, dict):
        return f"La fase {numero} non è descritta come si deve."
    sconosciuti = sorted(set(fase) - set(CAMPI_FASE))
    if sconosciuti:
        return f"La fase {numero} ha campi sconosciuti: {', '.join(sconosciuti)}."
    mancanti = [campo for campo in CAMPI_FASE if campo not in fase]
    if mancanti:
        return f"Alla fase {numero} mancano dei campi: {', '.join(mancanti)}."
    tipo, partecipanti, gironi, promossi, finalina = (fase[campo] for campo in CAMPI_FASE)
    if tipo not in TIPI:
        return f"La fase {numero} deve essere a gironi o a tabellone."
    if not (_intero(partecipanti) and _intero(gironi) and _intero(promossi)):
        return f"Nella fase {numero} partecipanti, gironi e promossi devono essere numeri interi."
    if not isinstance(finalina, bool):
        return f"Nella fase {numero} la finalina dev'essere sì o no."
    if not PARTECIPANTI_MINIMI <= partecipanti <= PARTECIPANTI_MASSIMI:
        return f"Nella fase {numero} i partecipanti vanno da {PARTECIPANTI_MINIMI} a {PARTECIPANTI_MASSIMI}."
    if tipo == GIRONI:
        if gironi < 1:
            return f"Nella fase {numero} ci vuole almeno un girone."
        if partecipanti % gironi:
            return f"Nella fase {numero} {partecipanti} partecipanti non si dividono in parti uguali in {gironi} gironi."
        grandezza = partecipanti // gironi
        if not COMPONENTI_MINIMI <= grandezza <= COMPONENTI_MASSIMI:
            return f"Nella fase {numero} ogni girone avrebbe {grandezza} componenti: vanno da {COMPONENTI_MINIMI} a {COMPONENTI_MASSIMI}."
        if ultima:
            if not 0 <= promossi < grandezza:
                return f"Nella fase {numero} i promossi vanno da 0 a {grandezza - 1}."
        elif not 1 <= promossi < grandezza:
            return f"Nella fase {numero} ogni girone ha {grandezza} componenti: i promossi per girone vanno da 1 a {grandezza - 1}."
        if finalina:
            return f"La fase {numero} è a gironi: la finalina c'è soltanto nella semifinale del tabellone."
        return None
    if not potenza_di_due(partecipanti):
        return f"Nella fase {numero} il tabellone ha {partecipanti} partecipanti: devono essere una potenza di 2, come 2, 4, 8 o 16."
    if gironi or promossi:
        return f"Nella fase {numero} il tabellone non ha gironi né promossi: valgono zero."
    if finalina and partecipanti != PARTECIPANTI_FINALINA:
        return f"Nella fase {numero} la finalina c'è soltanto con {PARTECIPANTI_FINALINA} partecipanti, cioè in semifinale."
    return None


def valida_formula(formula):
    """None se la formula va bene; altrimenti il motivo, in una frase."""
    if not isinstance(formula, dict):
        return "La formula non è descritta come si deve."
    sconosciuti = sorted(set(formula) - set(CAMPI_FORMULA))
    if sconosciuti:
        return f"La formula ha campi sconosciuti: {', '.join(sconosciuti)}."
    mancanti = [campo for campo in CAMPI_FORMULA if campo not in formula]
    if mancanti:
        return f"Alla formula mancano dei campi: {', '.join(mancanti)}."
    if not isinstance(formula["id"], str) or not formula["id"].strip():
        return "L'identificativo della formula dev'essere un testo non vuoto."
    nome = formula["nome"]
    if not isinstance(nome, str) or not NOME_MINIMO <= len(nome.strip()) <= NOME_MASSIMO:
        return f"Il nome della formula deve avere da {NOME_MINIMO} a {NOME_MASSIMO} caratteri."
    if not isinstance(formula["descrizione"], str) or len(formula["descrizione"]) > DESCRIZIONE_MASSIMA:
        return f"La descrizione della formula è un testo di al massimo {DESCRIZIONE_MASSIMA} caratteri."
    fasi = formula["fasi"]
    if not isinstance(fasi, list) or not 1 <= len(fasi) <= FASI_MASSIME:
        return f"Una formula ha da 1 a {FASI_MASSIME} fasi."
    for indice, fase in enumerate(fasi):
        problema = valida_fase(fase, indice, indice == len(fasi) - 1)
        if problema:
            return problema
    for indice in range(len(fasi) - 1):
        attesi = partecipanti_dopo(fasi[indice])
        if fasi[indice + 1]["partecipanti"] != attesi:
            return f"La fase {indice + 2} deve avere {attesi} partecipanti, quanti ne passano dalla fase {indice + 1}."
        if fasi[indice]["finalina"] and fasi[indice + 1]["tipo"] != TABELLONE:
            return f"Dopo la semifinale con la finalina, nella fase {indice + 1}, viene la finale del tabellone."
    ultima = fasi[-1]
    if not ((ultima["tipo"] == TABELLONE and ultima["partecipanti"] == 2) or (ultima["tipo"] == GIRONI and ultima["gironi"] == 1)):
        return "L'ultima fase dev'essere la finale di un tabellone, con 2 partecipanti, oppure un girone unico."
    return None


def aggiorna_cascata(fasi, da_indice=0):
    """
    Dopo un cambio nella fase da_indice, i partecipanti delle fasi seguenti si ricalcolano dalla
    precedente, come _update_phases_cascade di Terminal Beast. Cambia l'elenco che riceve.
    """
    for indice in range(da_indice + 1, len(fasi)):
        fasi[indice]["partecipanti"] = partecipanti_dopo(fasi[indice - 1])


def _leggi_dal_file(percorso):
    """Le formule valide e quelle scartate, con il motivo, dal file indicato."""
    if not os.path.exists(percorso):
        return [], [(NOME_FILE, "il file delle formule non c'è, e nemmeno la sua copia predefinita")]
    try:
        with open(percorso, encoding="utf-8") as f:
            dati = json.load(f)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        return [], [(NOME_FILE, f"il file non si legge: {e}")]
    if not isinstance(dati, dict) or not isinstance(dati.get("formule"), list):
        return [], [(NOME_FILE, "il file non contiene un elenco di formule")]
    valide, scartate, visti = [], [], set()
    for posto, formula in enumerate(dati["formule"], start=1):
        chi = formula.get("id") if isinstance(formula, dict) and isinstance(formula.get("id"), str) else f"la formula numero {posto}"
        problema = valida_formula(formula)
        if problema is None and formula["id"] in visti:
            problema = "l'identificativo è già di un'altra formula"
        if problema:
            scartate.append((chi, problema))
            continue
        visti.add(formula["id"])
        valide.append(formula)
    return valide, scartate


def leggi():
    """
    Le formule, come una coppia: l'elenco delle valide e quello delle scartate, ciascuna come
    coppia di nome e motivo. Restano in memoria fino alla prossima scrittura, una lettura per
    file; chi riceve gli elenchi riceve copie, e può cambiarle senza toccare quelle in memoria.
    """
    percorso = os.path.abspath(percorso_formule())
    if percorso not in _CACHE:
        _CACHE[percorso] = _leggi_dal_file(percorso)
    valide, scartate = _CACHE[percorso]
    return copy.deepcopy(valide), list(scartate)


def formula(id_formula):
    """La formula valida con quell'identificativo, in una copia; None se non c'è."""
    return next((f for f in leggi()[0] if f["id"] == id_formula), None)


def scrivi(formule):
    """
    Scrive le formule nella cartella del mondo con la scrittura sicura, un file temporaneo e poi
    os.replace, e azzera la cache. ValueError, senza scrivere niente, se una formula non va o
    due hanno lo stesso identificativo.
    """
    visti = set()
    for f in formule:
        problema = valida_formula(f)
        if problema:
            raise ValueError(problema)
        if f["id"] in visti:
            raise ValueError(f"Due formule hanno lo stesso identificativo, {f['id']}.")
        visti.add(f["id"])
    percorso = percorsi.percorso(NOME_FILE)
    temporaneo = percorso + ".tmp"
    try:
        with open(temporaneo, "w", encoding="utf-8") as file:
            json.dump({"formule": list(formule)}, file, ensure_ascii=False, indent=1)
            file.write("\n")
        os.replace(temporaneo, percorso)
    finally:
        if os.path.exists(temporaneo):
            with contextlib.suppress(OSError):
                os.remove(temporaneo)
    azzera_cache()


def in_uso(id_formula, modelli):
    """I nomi dei modelli che usano la formula, in ordine alfabetico: modelli è un elenco di oggetti con nome e formula."""
    return sorted((m.nome for m in modelli if m.formula == id_formula), key=str.casefold)


def elimina(id_formula, modelli):
    """Toglie la formula dal file; ValueError col nome dei modelli se qualcuno la usa, o se la formula non c'è."""
    usata = in_uso(id_formula, modelli)
    if usata:
        raise ValueError(f"La formula è usata da {len(usata)} modelli: {', '.join(usata)}. Prima si cambia la loro formula.")
    valide, _scartate = leggi()
    restanti = [f for f in valide if f["id"] != id_formula]
    if len(restanti) == len(valide):
        raise ValueError(f"La formula {id_formula} non c'è.")
    scrivi(restanti)


def nuovo_id(formule):
    """L'identificativo di una formula nuova: formula_ e il primo numero libero."""
    usati = {f["id"] for f in formule if isinstance(f, dict)}
    n = 1
    while f"{PREFISSO_ID}{n}" in usati:
        n += 1
    return f"{PREFISSO_ID}{n}"


def tetto(formula_data):
    """Quanti iscritti al massimo una sede di torneo con questa formula: i partecipanti della prima fase."""
    return formula_data["fasi"][0]["partecipanti"]


# La struttura adattata agli iscritti veri, punto 4.4 del progetto della tappa 12.

def _piu_vicino(x):
    """L'intero più vicino, con le metà verso l'alto: 1,5 fa 2 e 2,5 fa 3."""
    return math.floor(x + 0.5)


def grandezze_dei_gironi(n, gironi):
    """Come si dividono n giocatori in tanti gironi che differiscono al più di uno: i più grandi per primi."""
    base, resto = divmod(n, gironi)
    return [base + 1 if i < resto else base for i in range(gironi)]


def turni_del_girone(grandezza):
    """I turni di un girone col metodo del cerchio: uno meno i componenti se sono pari, quanti sono se dispari, perché ogni turno qualcuno riposa."""
    return grandezza - 1 if grandezza % 2 == 0 else grandezza


def struttura(formula_data, n):
    """
    La struttura di una sede con n iscritti veri, al massimo il tetto, come elenco delle fasi che si
    giocano, ciascuna un dizionario. Una fase a gironi con P partecipanti, G gironi e S uguale a P
    diviso G componenti ne usa G' uguale al più vicino di n diviso S, almeno 1 e al massimo G, poi
    ridotto finché ogni girone ha almeno promossi più uno componenti; i gironi differiscono al più di
    uno, e i promossi per girone restano quelli della formula, se non sono troppi per un girone
    rimasto piccolo. Le fasi di tabellone consecutive sono un tabellone solo, che parte dai
    qualificati veri: la grandezza è la prima potenza di 2 che li contiene, e i posti vuoti sono
    turni di riposo. Un tabellone che nella formula non arriva alla finale gioca tanti turni quanti
    ne ha nella formula; se così resterebbe un giocatore solo, il torneo finisce lì.
    Le fasi: {"tipo": "gironi", "grandezze": [...], "promossi": p, "turni": t, "ultima": bool} oppure
    {"tipo": "tabellone", "grandezza": s, "qualificati": q, "turni": t, "finalina": bool, "ultima": bool}.
    """
    fasi = formula_data["fasi"]
    if not _intero(n) or n < PARTECIPANTI_MINIMI:
        raise ValueError(f"Una sede di torneo ha almeno {PARTECIPANTI_MINIMI} iscritti.")
    if n > tetto(formula_data):
        raise ValueError(f"Una sede con la formula {formula_data['nome']} ha al massimo {tetto(formula_data)} iscritti.")
    giocate = []
    corrente = n
    indice = 0
    while indice < len(fasi):
        fase = fasi[indice]
        if fase["tipo"] == GIRONI:
            ultima = indice == len(fasi) - 1
            componenti = fase["partecipanti"] // fase["gironi"]
            quanti = 1 if ultima else max(1, min(fase["gironi"], _piu_vicino(corrente / componenti)))
            while quanti > 1 and corrente // quanti < fase["promossi"] + 1:
                quanti -= 1
            grandezze = grandezze_dei_gironi(corrente, quanti)
            promossi = 0 if ultima else max(1, min(fase["promossi"], grandezze[-1] - 1))
            avanzano = quanti * promossi
            # Un girone che promuove uno solo decide il torneo: il suo primo ha vinto.
            ultima = ultima or avanzano < 2
            giocate.append({"tipo": GIRONI, "grandezze": grandezze, "promossi": 0 if ultima else promossi, "turni": turni_del_girone(grandezze[0]), "ultima": ultima})
            if ultima:
                break
            corrente = avanzano
            indice += 1
            continue
        fine = indice
        while fine < len(fasi) and fasi[fine]["tipo"] == TABELLONE:
            fine += 1
        grandezza = 1 << max(1, (corrente - 1).bit_length())
        turni_pieni = grandezza.bit_length() - 1
        arriva_in_finale = fine == len(fasi)
        turni = turni_pieni if arriva_in_finale else min(fine - indice, turni_pieni)
        ultima = arriva_in_finale or grandezza >> turni < 2
        finalina = ultima and grandezza >= PARTECIPANTI_FINALINA and turni == turni_pieni and any(fasi[k]["finalina"] for k in range(indice, fine))
        giocate.append({"tipo": TABELLONE, "grandezza": grandezza, "qualificati": corrente, "turni": turni, "finalina": finalina, "ultima": ultima})
        if ultima:
            break
        corrente = grandezza >> turni
        indice = fine
    return giocate
