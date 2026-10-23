"""
Motore grammaticale di MESS: sostantivi con genere e numero, aggettivi con le quattro forme,
articoli e preposizioni articolate.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-02 dal motore di Terminal Beast, lore.py, secondo la decisione D8 del piano.
Rispetto all'originale aggiunge l'articolo determinativo, le preposizioni articolate, gli
aggettivi in -ico e in -cio e -gio, gli aggettivi preceduti da un avverbio e quelli seguiti
da un complemento. Dalla revisione della tappa 14, il 2026-10-23, la preposizione davanti ai nomi dei
tornei, articolata per quelli che riconosce; dalla seconda revisione anche il solo articolo, e il
genere e il numero del torneo per accordargli il participio.
"""

# Aggettivi che non cambiano mai forma. Quelli che finiscono in a, in vocale accentata o in
# consonante sono già invariabili per regola, ma stanno qui per chiarezza.
INVARIABILI = {"blu", "rosa", "viola", "nocciola", "fucsia", "lilla", "beige", "ocra", "ambra", "pesca", "magenta", "indaco"}

# Gli avverbi che possono precedere un aggettivo: in "ben curato" si accorda solo curato.
AVVERBI = {"ben", "molto", "poco", "leggermente", "appena", "quasi", "piuttosto", "perfettamente", "lievemente", "vagamente", "decisamente", "naturalmente"}

# Le eccezioni alle regole del plurale.
PLURALI_IRREGOLARI = {
    "greco": ("greci", "greca", "greche"),
    "antico": ("antichi", "antica", "antiche"),
}

PREPOSIZIONI = {
    "di": ("del", "dello", "della", "dei", "degli", "delle", "dell'"),
    "a": ("al", "allo", "alla", "ai", "agli", "alle", "all'"),
    "da": ("dal", "dallo", "dalla", "dai", "dagli", "dalle", "dall'"),
    "in": ("nel", "nello", "nella", "nei", "negli", "nelle", "nell'"),
    "su": ("sul", "sullo", "sulla", "sui", "sugli", "sulle", "sull'"),
}
ARTICOLI = ("il", "lo", "la", "i", "gli", "le", "l'")
VOCALI = "aeiouàèéìòù"


class Sostantivo:
    """Un sostantivo con genere, m o f, e numero, s o p."""

    def __init__(self, lemma, genere, numero="s"):
        self.lemma = lemma
        self.genere = genere
        self.numero = numero

    def __repr__(self):
        return f"Sostantivo({self.lemma!r}, {self.genere!r}, {self.numero!r})"


def _forme_semplici(ms):
    """Le forme maschile plurale, femminile singolare e femminile plurale di un aggettivo di una parola."""
    if ms in PLURALI_IRREGOLARI:
        return PLURALI_IRREGOLARI[ms]
    if ms in INVARIABILI or not ms.endswith(("o", "e")):
        return ms, ms, ms
    if ms.endswith(("cio", "gio")):
        radice = ms[:-2]
        femminile_plurale = radice + "e" if radice[-2] not in VOCALI else radice + "ie"
        return radice + "i", radice + "ia", femminile_plurale
    if ms.endswith("io"):
        radice = ms[:-2]
        return radice + "i", radice + "ia", radice + "ie"
    if ms.endswith("ico"):
        radice = ms[:-1]
        return radice + "i", radice + "a", radice + "he"
    if ms.endswith(("co", "go")):
        radice = ms[:-1]
        return radice + "hi", radice + "a", radice + "he"
    if ms.endswith("o"):
        radice = ms[:-1]
        return radice + "i", radice + "a", radice + "e"
    radice = ms[:-1]
    return radice + "i", ms, radice + "i"


class Aggettivo:
    """
    Un aggettivo che si accorda col sostantivo. Si costruisce dal maschile singolare, e le
    altre forme si ricavano da sole: "rosso" dà rossi, rossa, rosse. Le locuzioni di più
    parole sono invariabili, come "biondo cenere" o "a mandorla", tranne quelle che
    cominciano con un avverbio, come "ben curato", dove si accorda l'ultima parola. Con base
    e dopo si costruisce un aggettivo seguito da un complemento, come "pettinato
    all'indietro", dove si accorda solo la base. Le forme si possono anche dare tutte e quattro.
    """

    def __init__(self, ms="", mp=None, fs=None, fp=None, base=None, dopo=None):
        if base is not None:
            coda = f" {dopo}" if dopo else ""
            interno = Aggettivo(base)
            self.ms, self.mp, self.fs, self.fp = (forma + coda for forma in (interno.ms, interno.mp, interno.fs, interno.fp))
        elif mp is not None:
            self.ms, self.mp, self.fs, self.fp = ms, mp, fs or ms, fp or mp
        elif " " in ms:
            prima, _, resto = ms.partition(" ")
            if prima in AVVERBI:
                interno = Aggettivo(resto)
                self.ms = ms
                self.mp, self.fs, self.fp = (f"{prima} {forma}" for forma in (interno.mp, interno.fs, interno.fp))
            else:
                self.ms = self.mp = self.fs = self.fp = ms
        else:
            self.ms = ms
            self.mp, self.fs, self.fp = _forme_semplici(ms)

    @classmethod
    def da_vocabolario(cls, voce):
        """Costruisce l'aggettivo da una voce del vocabolario JSON: una stringa o un dizionario."""
        if isinstance(voce, str):
            return cls(voce)
        return cls(**voce)

    @property
    def chiave(self):
        """Il nome con cui l'aggettivo si salva nei tratti di un giocatore: il maschile singolare."""
        return self.ms

    def accorda(self, sostantivo):
        """La forma accordata al sostantivo, oppure a un genere e numero dati come coppia."""
        genere, numero = (sostantivo.genere, sostantivo.numero) if isinstance(sostantivo, Sostantivo) else sostantivo
        if genere == "m":
            return self.ms if numero == "s" else self.mp
        return self.fs if numero == "s" else self.fp

    def __repr__(self):
        return f"Aggettivo({self.ms!r}, {self.mp!r}, {self.fs!r}, {self.fp!r})"


def _inizio_speciale(parola):
    """Vero per le parole che vogliono lo, gli e uno: s seguita da consonante, z, gn, ps, pn, x, y, i seguita da vocale."""
    p = parola.lower()
    if len(p) > 1 and p[0] == "s" and p[1] not in VOCALI:
        return True
    if len(p) > 1 and p[0] == "i" and p[1] in VOCALI:
        return True
    return p.startswith(("z", "gn", "ps", "pn", "x", "y"))


def _inizio_vocale(parola):
    return bool(parola) and parola[0].lower() in VOCALI and not _inizio_speciale(parola)


def _indice_articolo(sostantivo):
    """La posizione nella tupla degli articoli: il, lo, la, i, gli, le, l'."""
    lemma = sostantivo.lemma
    if sostantivo.numero == "p":
        if sostantivo.genere == "f":
            return 5
        return 4 if _inizio_vocale(lemma) or _inizio_speciale(lemma) else 3
    if _inizio_vocale(lemma):
        return 6
    if sostantivo.genere == "f":
        return 2
    return 1 if _inizio_speciale(lemma) else 0


def unisci(articolo, parola):
    """Mette insieme articolo e parola, senza spazio dopo l'apostrofo."""
    if not articolo:
        return parola
    return f"{articolo}{parola}" if articolo.endswith("'") else f"{articolo} {parola}"


def articolo_determinativo(sostantivo):
    return ARTICOLI[_indice_articolo(sostantivo)]


def articolo_indeterminativo(sostantivo):
    """Un, uno, una, un'; al plurale il partitivo: dei, degli, delle."""
    lemma = sostantivo.lemma
    if sostantivo.numero == "p":
        return ("dei", "degli", "delle")[(3, 4, 5).index(_indice_articolo(sostantivo))]
    if sostantivo.genere == "f":
        return "un'" if _inizio_vocale(lemma) else "una"
    return "uno" if _inizio_speciale(lemma) else "un"


def preposizione_articolata(preposizione, sostantivo):
    """Di, a, da, in e su fuse con l'articolo determinativo: dalla, degli, sull'. Con resta separata: con il."""
    if preposizione in PREPOSIZIONI:
        return PREPOSIZIONI[preposizione][_indice_articolo(sostantivo)]
    return f"{preposizione} {articolo_determinativo(sostantivo)}"


def con_determinativo(sostantivo, preposizione=None):
    """Il sostantivo col suo articolo, o con la preposizione articolata: il naso, dagli occhi."""
    articolo = preposizione_articolata(preposizione, sostantivo) if preposizione else articolo_determinativo(sostantivo)
    return unisci(articolo, sostantivo.lemma)


def con_indeterminativo(sostantivo, partitivo=False):
    """Il sostantivo con l'articolo indeterminativo; al plurale senza articolo, a meno di chiedere il partitivo."""
    if sostantivo.numero == "p" and not partitivo:
        return sostantivo.lemma
    return unisci(articolo_indeterminativo(sostantivo), sostantivo.lemma)


def verbo(sostantivo, singolare, plurale):
    """La forma del verbo che si accorda al numero del sostantivo: è o sono, ha o hanno."""
    return plurale if sostantivo.numero == "p" else singolare


def elenco(parti, congiunzione="e"):
    """Unisce le parti con le virgole e la congiunzione prima dell'ultima: a, b e c."""
    parti = [p for p in parti if p]
    if len(parti) < 2:
        return "".join(parti)
    ultima = parti[-1]
    # Davanti a una parola che comincia per e, la congiunzione e prende la d eufonica.
    giunto = "ed" if congiunzione == "e" and ultima[:1].lower() == "e" else congiunzione
    return f"{', '.join(parti[:-1])} {giunto} {ultima}"


def maiuscola(frase):
    return frase[:1].upper() + frase[1:]


# Le prime parole dei nomi dei tornei che MESS riconosce, col genere e il numero, per la preposizione
# articolata davanti al nome: al Campionato italiano maschile, all'Open misto del mese, alla Coppa delle
# polisportive. Quelle di due parole si cercano prima, come Gran Premio. La revisione della tappa 14,
# il 23 ottobre 2026: prima si leggeva "Convocato a Campionato italiano maschile".
PAROLE_DEI_TORNEI = {
    "gran premio": ("m", "s"), "grand prix": ("m", "s"), "grand slam": ("m", "s"),
    "campionato": ("m", "s"), "campionati": ("m", "p"), "torneo": ("m", "s"), "trofeo": ("m", "s"), "open": ("m", "s"),
    "premio": ("m", "s"), "memorial": ("m", "s"), "festival": ("m", "s"), "meeting": ("m", "s"), "master": ("m", "s"),
    "masters": ("m", "s"), "circuito": ("m", "s"), "criterium": ("m", "s"), "palio": ("m", "s"), "giochi": ("m", "p"),
    "europei": ("m", "p"), "mondiali": ("m", "p"), "coppa": ("f", "s"), "supercoppa": ("f", "s"), "finale": ("f", "s"),
    "finali": ("f", "p"), "gara": ("f", "s"), "sfida": ("f", "s"), "giornata": ("f", "s"), "giornate": ("f", "p"),
    "rassegna": ("f", "s"), "festa": ("f", "s"), "maratona": ("f", "s"), "serie": ("f", "s"), "olimpiade": ("f", "s"),
    "olimpiadi": ("f", "p"),
}
# Gli articoli con cui può cominciare un nome scritto con l'editor dei tornei, con la loro posizione fra
# gli articoli: "Il Trofeo dei Tigli" diventa "al Trofeo dei Tigli". Manca i, che si confonde col numero
# romano di una prima edizione, come in "I Memorial Rossi".
ARTICOLI_DEI_NOMI = {"il": 0, "lo": 1, "la": 2, "gli": 4, "le": 5}
# Il genere e il numero che un articolo scritto in testa al nome dà al torneo, nell'ordine degli articoli.
FORME_DEGLI_ARTICOLI = (("m", "s"), ("m", "s"), ("f", "s"), ("m", "p"), ("m", "p"), ("f", "p"))
# La forma di un torneo il cui nome non si riconosce: il torneo, maschile singolare.
FORMA_PREDEFINITA = ("m", "s")


def _forma_delle_parole(minuscole):
    """Il genere e il numero dalle prime parole del nome, già in minuscolo, se MESS le riconosce; altrimenti None. Quelle di due parole vengono prima."""
    if not minuscole:
        return None
    return PAROLE_DEI_TORNEI.get(" ".join(minuscole[:2])) or PAROLE_DEI_TORNEI.get(minuscole[0])


def _riconosci(nome):
    """
    Come comincia il nome di un torneo: la posizione del suo articolo fra gli articoli, il nome senza
    l'articolo che vi fosse scritto, e il genere e il numero. Per un nome che non si riconosce
    l'articolo è None, e anche la forma, salvo quella che dà un l' scritto in testa.
    """
    parole = nome.split()
    minuscole = [parola.casefold().rstrip(",.;:") for parola in parole]
    for apostrofo in ("'", chr(0x2019)):
        if minuscole[0].startswith("l" + apostrofo) and len(parole[0]) > 2:
            resto = nome.lstrip()[2:]
            return 6, resto, _forma_delle_parole([parola.casefold().rstrip(",.;:") for parola in resto.split()])
    if minuscole[0] in ARTICOLI_DEI_NOMI and len(parole) > 1:
        indice = ARTICOLI_DEI_NOMI[minuscole[0]]
        return indice, nome.lstrip()[len(parole[0]):].lstrip(), FORME_DEGLI_ARTICOLI[indice]
    forma = _forma_delle_parole(minuscole)
    if forma is None:
        return None, nome, None
    return _indice_articolo(Sostantivo(nome, *forma)), nome, forma


def torneo_con_preposizione(nome, preposizione="a"):
    """
    Il nome di un torneo con la preposizione davanti, articolata se il nome comincia con una parola che
    MESS riconosce o con un articolo: al Campionato italiano maschile, al Gran Premio femminile,
    all'Open misto del mese, alla Coppa delle polisportive, dal Trofeo dei Tigli se il nome è "Il Trofeo
    dei Tigli". Un nome che non si riconosce, scritto dall'utente con l'editor dei tornei, resta com'è,
    con la preposizione semplice: a Showdown d'autunno; davanti a una a la preposizione a prende la d
    eufonica, come la congiunzione e in elenco: ad Autunno in gara. Con preposizione None, dalla
    seconda revisione della tappa 14, il solo articolo, in minuscolo come a metà frase: "Chiude il
    Campionato italiano maschile", "Lascia l'Open misto del mese"; il nome che non si riconosce resta
    senza: "Chiude Showdown d'autunno".
    """
    if not nome.split():
        return preposizione or ""
    indice, resto, _forma = _riconosci(nome)
    if indice is None:
        if preposizione is None:
            return nome
        eufonica = preposizione == "a" and nome.lstrip()[:1].casefold() == "a"
        return f"{'ad' if eufonica else preposizione} {nome}"
    return unisci(_articolata(preposizione, indice), resto)


def forma_del_torneo(nome):
    """
    Il genere e il numero di un torneo, per accordargli verbi e participi: dalle parole che MESS
    riconosce in testa al nome, o dall'articolo scritto con l'editor dei tornei; maschile singolare,
    il torneo, se il nome non si riconosce.
    """
    if not nome.split():
        return FORMA_PREDEFINITA
    return _riconosci(nome)[2] or FORMA_PREDEFINITA


def accorda_al_torneo(nome, participio):
    """Il verbo essere col participio, dal maschile singolare, accordati al torneo: è annullato, è annullata, sono annullate."""
    forma = forma_del_torneo(nome)
    return f"{'è' if forma[1] == 's' else 'sono'} {Aggettivo(participio).accorda(forma)}"


def _articolata(preposizione, indice):
    """La preposizione fusa con l'articolo che sta a quella posizione: il, lo, la, i, gli, le, l'; senza preposizione, l'articolo da solo."""
    if preposizione is None:
        return ARTICOLI[indice]
    if preposizione in PREPOSIZIONI:
        return PREPOSIZIONI[preposizione][indice]
    return f"{preposizione} {ARTICOLI[indice]}"
