"""
La taratura del motore di partita di MESS: tutti i numeri che si regolano col banco.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9. I numeri stanno in un oggetto congelato, Taratura, con i
valori iniziali scritti come predefiniti: il motore lo riceve, e il banco ne prova le varianti con
dataclasses.replace, oppure le legge da un file JSON con carica_taratura, senza sostituire
funzioni. Le regole IBSA e le misure del tavolo non stanno qui ma in costanti.py, perché non si
tarano: si rispettano.
Ogni colpo ha la sua riga nella tabella COLPI, nel riferimento di chi colpisce: il nome sx vuol
dire che la pallina va verso la sinistra di chi colpisce, o vi tocca la prima sponda. La zona è
quella d'arrivo vista da chi difende, le sponde sono in ordine, e la partenza è in centimetri dalla
sponda sinistra di chi colpisce. Invertire un colpo costa una riga.
I valori sono quelli della taratura fatta col banco il 2026-10-07, a fine tappa 9: dove si
allontanano dal progetto il commento accanto dice il valore di partenza e il motivo, e il racconto
dei passi sta in strumenti/banco_partite_dopo.txt.
"""

import dataclasses
import json
from typing import NamedTuple


class Colpo(NamedTuple):
    """Un colpo: zona d'arrivo vista da chi difende, sponde in ordine, partenza, e i suoi numeri di gioco."""
    nome: str
    zona: str
    sponde: tuple
    partenza_u: float
    potenza: float
    bonus: float
    fallo_base: float
    quota_schermo: float
    velocita: float


def _colpi_iniziali():
    """La tabella dei colpi del punto 21.2 del progetto, con zone, sponde e partenze del punto 3.4."""
    # La taratura ha tolto un ventesimo ai falli di base, e di più a tripla sponda e bomba, che si
    # sceglievano troppo poco perché il loro peso nel valore si potesse misurare; le quote di
    # schermo sono salite di qualche punto, per centrare il bersaglio dello schermo centrale. I
    # valori del progetto erano 0,060, 0,065, 0,055, 0,070, 0,095 e 0,090 per i falli, 0,60,
    # 0,65, 0,50, 0,40, 0,35 e 0,85 per lo schermo.
    righe = (
        ("lungolineasx", "dx", (), 25.0, 0.60, 0.0, 0.057, 0.64, 600.0),
        ("lungolineadx", "sx", (), 97.0, 0.60, 0.0, 0.057, 0.64, 600.0),
        ("diagonalesx", "dx", (), 90.0, 0.70, 0.05, 0.061, 0.69, 650.0),
        ("diagonaledx", "sx", (), 32.0, 0.70, 0.05, 0.061, 0.69, 650.0),
        ("singolaspondasx", "dx", ("sinistra",), 61.0, 0.50, 0.0, 0.052, 0.55, 560.0),
        ("singolaspondadx", "sx", ("destra",), 61.0, 0.50, 0.0, 0.052, 0.55, 560.0),
        ("doppiaspondasx", "sx", ("sinistra", "destra"), 61.0, 0.45, 0.05, 0.066, 0.45, 540.0),
        ("doppiaspondadx", "dx", ("destra", "sinistra"), 61.0, 0.45, 0.05, 0.066, 0.45, 540.0),
        ("triplaspondasx", "dx", ("sinistra", "destra", "sinistra"), 61.0, 0.40, 0.10, 0.084, 0.40, 520.0),
        ("triplaspondadx", "sx", ("destra", "sinistra", "destra"), 61.0, 0.40, 0.10, 0.084, 0.40, 520.0),
        ("bomba", "centro", (), 61.0, 1.00, 0.15, 0.082, 0.87, 850.0),
        # Le battute partono fra 61 e 100 centimetri, la sinistra, e fra 22 e 61, la destra: la
        # regia estrae il punto, qui c'è il centro dell'intervallo.
        ("battutasx", "sx", ("sinistra",), 80.5, 0.50, 0.0, 0.0, 0.0, 450.0),
        ("battutadx", "dx", ("destra",), 41.5, 0.50, 0.0, 0.0, 0.0, 450.0),
    )
    return {riga[0]: Colpo(*riga) for riga in righe}


@dataclasses.dataclass(frozen=True)
class Taratura:
    """
    I numeri regolabili del motore, con i valori iniziali del progetto. I nomi seguono il
    progetto della tappa 9; le tabelle delle cause sono tuple di coppie, codice e peso.
    """
    COLPI: dict = dataclasses.field(default_factory=_colpi_iniziali)
    # Le qualità, da 0 a 100: pesi di caratteristica, attacco, precisione e forza per i colpi;
    # di caratteristica, precisione, forza e attacco per le battute; di caratteristica, difesa e
    # precisione per chiusure e blocchi; di controllo palla, precisione e tenuta per il controllo.
    PESI_COLPO: tuple = (0.50, 0.15, 0.20, 0.15)
    PESI_BOMBA: tuple = (0.50, 0.15, 0.10, 0.25)
    PESI_BATTUTA: tuple = (0.55, 0.25, 0.10, 0.10)
    PESI_CHIUSURA: tuple = (0.55, 0.25, 0.20)
    PESI_BLOCCO: tuple = (0.60, 0.20, 0.20)
    PESI_CONTROLLO: tuple = (0.55, 0.25, 0.20)
    # Q0 era 10: schiacciava i rapporti fra pressione e difesa dei giocatori poco allenati, che
    # sono il mondo vero, e lì il favorito vinceva poco più di otto volte su dieci anche con un
    # distacco oltre il 30 per cento.
    Q0: float = 5.0
    # La difesa: logit di goal, fallo, fuori e ribattuta rispetto alla fermata, che vale zero.
    # G0 era -2,0: più goal, perché i giocatori veri del mondo, poco allenati, segnassero almeno
    # quanto sbagliano. KG era 2,6: col valore nuovo il favorito vinceva quasi sempre, il 98 per
    # cento oltre il 30 per cento di distacco, e la pendenza si è abbassata fino alla banda.
    G0: float = -1.7
    KG: float = 1.6
    F0: float = -3.9
    KF: float = 1.0
    O0: float = -4.2
    KO: float = 1.0
    R0: float = -0.7
    KR: float = 0.6
    # Quanto il blocco conta accanto alla chiusura nel decidere se la pallina passa: zero vuol dire
    # soltanto la chiusura, come nel progetto; la taratura del valore ha mostrato che allora il
    # blocco, che sceglie solo fra ribattuta e fermata, non pesava quasi nulla.
    PESO_BLOCCO_PARATA: float = 0.3
    CAUSE_DIFESA: tuple = (("body_touch", 70), ("difesa_irregolare", 25), ("invasione_mano_libera", 4), ("invasione_tavola_contatto", 1))
    CAUSE_DIFESA_CRITICHE: tuple = (("paletta_caduta", 60), ("body_touch_pieno", 40))
    CAUSE_DIFESA_CRITICHE_CENTRO: tuple = (("paletta_caduta", 80), ("body_touch_pieno", 20))
    QUOTA_DIFESA_IRREGOLARE_IN_PORTA: float = 0.5
    # La battuta. P_BATTUTA_IRREGOLARE era 0,035: col fallo meno legato all'abilità le battute
    # irregolari erano scese al 4 per cento, il bordo della banda.
    P_BATTUTA_IRREGOLARE: float = 0.042
    PRESSIONE_BATTUTA: float = 0.80
    QUOTA_BATTUTA_LATERALE: float = 0.55
    CAUSE_BATTUTA: tuple = (("battuta_senza_rimbalzo", 34), ("battuta_due_rimbalzi", 26), ("battuta_strisciata", 14), ("battuta_oltre_due_secondi", 7),
                            ("battuta_prima_del_fischio", 7), ("battuta_a_vuoto", 6), ("battuta_doppio_tocco", 6))
    CAUSE_BATTUTA_CRITICHE: tuple = (("battuta_a_vuoto", 30), ("battuta_doppio_tocco", 25), ("out_volo", 25), ("schermo_sopra", 20))
    K_TEMP_CAUSE_BATTUTA: float = 0.5
    # L'attacco. K_SKILL_FALLI era 0,8: con quel valore i giocatori del mondo vero, quasi tutti
    # sotto 30 di qualità, facevano sei punti su dieci con i falli. K_TEMPO_FALLI era 0,6: il
    # tempo del controllo deve contare, perché il controllo palla non resti una caratteristica
    # quasi inerte nel valore.
    K_SKILL_FALLI: float = 0.4
    RISCHIO_POTENZA: float = 0.3
    K_TEMPO_FALLI: float = 1.0
    P_FALLO_MASSIMA: float = 0.5
    P_COLPO_DEBOLE: float = 0.0006
    QUOTA_SCHERMO_SOPRA: float = 0.15
    QUOTA_SCHERMO_SOPRA_BOMBA: float = 0.30
    QUOTA_OUT_CONTATTO: float = 0.25
    QUOTA_OUT_CONTATTO_BOMBA: float = 0.60
    CAUSE_ATTACCO_CRITICHE: tuple = (("schermo_sopra", 35), ("out_volo", 30), ("out_soffitto", 15), ("paletta_caduta", 20))
    QUOTA_CRITICO: float = 0.12
    # Il controllo e la ribattuta.
    P_TRATTENUTA: float = 0.0025
    K_TEMP_TRATTENUTA: float = 0.3
    P_SFUGGITA: float = 0.035
    SOGLIA_FERMATA_SPORCA: float = 0.25
    MAGGIORAZIONE_FERMATA_SPORCA: float = 0.5
    QUOTA_AUTOGOAL: float = 0.04
    QUOTA_PALLINA_FERMA: float = 0.03
    TEMPO_DOPO_RECUPERO: float = 0.25
    # Il tempo del controllo riuscito: erano 0,55, 0,45 e 15, e il tempo restava fra 0,85 e 0,95
    # per tutti, bravi e meno bravi; ora va da 0,7 a 0,9 col controllo, e quel che resta lo fa il
    # caso del tiro.
    TEMPO_BASE: float = 0.5
    TEMPO_SCALA: float = 0.8
    TEMPO_MEZZO: float = 60.0
    PRESSIONE_RIBATTUTA: float = 0.35
    P_RIBATTUTA_LENTA: float = 0.002
    # La pressione dell'attacco. PRESSIONE_TEMPERAMENTO era 0,22: con la pendenza dei goal più
    # bassa l'impetuoso valeva sei punti meno del calmo, e il temperamento deve essere uno stile,
    # non una forza. PRESSIONE_TEMPO_BASE era 0,7, e TEMPO_GIOCO_RAPIDO 0,8, che col tempo nuovo
    # quasi nessuno raggiungeva.
    PRESSIONE_TEMPERAMENTO: float = 0.26
    PRESSIONE_TEMPO_BASE: float = 0.5
    BONUS_CAMBIO_VELOCITA: float = 0.05
    BONUS_GIOCO_RAPIDO: float = 0.04
    TEMPO_GIOCO_RAPIDO: float = 0.75
    # La pressione sulla palla set: spenta finché Gabriele non decide.
    PRESSIONE_PALLA_SET: float = 0.0
    PRESSIONE_PALLA_SET_TEMPERAMENTO: float = 0.5
    PRESSIONE_PALLA_SET_ESPERIENZA: float = 0.6
    # La stanchezza.
    FATICA_MAX: float = 0.35
    FATICA_SCALA: float = 600.0
    ETA_INIZIO_FATICA: float = 30.0
    ANNI_FATICA: float = 20.0
    ETA_FATICA_GIOVANI: float = 16.0
    FATICA_GIOVANI_PER_ANNO: float = 0.10
    RESISTENZA_BASE: float = 0.6
    RESISTENZA_PER_PUNTO: float = 0.08
    K_FATICA_FALLI: float = 1.5
    # Lettura del gioco, esperienza e temperamento. K_ESP_FALLI era 0,35: gli esperti facevano
    # dal 14 al 22 per cento di falli in meno secondo il seme, al bordo della banda.
    K_LETTURA: float = 6.0
    K_ESP_FALLI: float = 0.45
    K_TEMP_FALLI: float = 0.25
    # La scelta del colpo.
    T0: float = 0.15
    K_FATICA_SCELTA: float = 3.0
    K_LETTURA_SCELTA: float = 0.6
    PESO_DEBOLEZZA: float = 1.5
    PESO_POTENZA: float = 0.25
    PESO_RISCHIO: float = 2.0
    # I priori erano 0,08 e meno 0,04: tutti tiravano sul rovescio sei volte su dieci, e i colpi
    # verso il dritto pesavano nel valore un quarto degli altri. Il vantaggio del mancino che ne
    # nasceva era comunque sotto il punto di valore. COLPI_PER_CAPIRE era 30: gli esperti
    # mandavano sul lato debole poco più del 60 per cento degli attacchi laterali.
    PRIORE_ROVESCIO: float = 0.03
    PRIORE_ALTRE_ZONE: float = -0.015
    COLPI_PER_CAPIRE: float = 20.0
    # La mano.
    MALUS_ROVESCIO: float = 0.10
    COSTO_CAMBIO_MANO: float = 0.03
    # Gli imprevisti a palla ferma. P_SANZIONE era 0,0010, e le ammonizioni stavano al bordo
    # basso della banda.
    P_SANZIONE: float = 0.0014
    K_TEMP_SANZIONI: float = 1.0
    K_ESP_SANZIONI: float = 0.4
    CAUSE_AMMONIZIONE: tuple = (("raschiare_paletta", 22), ("muovere_tavolo", 18), ("parlare", 18), ("mano_libera_al_tavolo", 12), ("non_dal_fondo", 10),
                                ("perdita_di_tempo", 10), ("pallina_col_dito", 6), ("corpo_in_area_da_fuori", 6), ("senza_piede_a_terra", 4))
    P_MASCHERINA: float = 0.00008
    K_TEMP_MASCHERINA: float = 0.8
    P_TELEFONO: float = 0.00002
    P_ROTTURA_PALETTA: float = 0.0001
    P_ROTTURA_PALLINA: float = 0.00008
    COLPO_ROTTURA_MASSIMO: int = 3
    LIMITE_COLPI_PUNTO: int = 150
    # Time-out e sorteggio.
    SERIE_TIMEOUT: int = 3
    P_TIMEOUT_PER_PUNTO: float = 0.08
    P_TIMEOUT_MAX: float = 0.6
    K_LETTURA_TIMEOUT: float = 0.5
    P_SCEGLIE_BATTUTA: float = 0.7
    # Le squadre.
    DISTACCO_SOSTITUZIONE: int = 6
    VANTAGGIO_RISERVA: float = 0.08
    EFFICIENZA_SOSTITUZIONE: float = 0.85
    # La regia: velocità e attriti in centimetri e secondi.
    DECELERAZIONE: float = 40.0
    PERDITA_PER_SPONDA: float = 0.12
    VELOCITA_RIBATTUTA: float = 250.0
    VELOCITA_CONSEGNA: float = 120.0
    FATTORE_FORZA_VELOCITA_BASE: float = 0.8
    FATTORE_FORZA_VELOCITA: float = 0.4
    FATTORE_TEMP_VELOCITA: float = 0.10
    VARIAZIONE_VELOCITA: float = 0.10
    DISTANZA_PARATA: tuple = (15.0, 35.0)
    SCOSTAMENTO_MASSIMO: float = 8.0
    # I tempi della regia, in secondi: scalati dalla velocità di gioco della tappa 10, decisione D12.
    RECUPERO_TASCA: float = 4.0
    RECUPERO_TAVOLO: float = 2.5
    RECUPERO_TERRA: float = 9.0
    DURATA_ANNUNCIO: float = 1.6
    DURATA_DOMANDA_PRONTO: float = 3.0
    FISCHIO_SINGOLO: float = 0.35
    FISCHIO_DOPPIO: float = 0.8
    FISCHIO_LUNGO: float = 1.4
    RITARDO_CHIAMATA: float = 0.8
    DURATA_CHIAMATA: float = 1.2
    ATTESA_BATTUTA: tuple = (0.5, 1.6)
    ATTESA_OLTRE_DUE_SECONDI: float = 2.4
    FATTORE_TEMPI_GIOCO_RAPIDO: float = 0.6
    FATTORE_CONTROLLO_GIOCO_RAPIDO: float = 0.7
    DURATA_CONTROLLO: tuple = (0.4, 1.4)
    DURATA_TRATTENUTA: tuple = (2.3, 3.0)
    # Era 1,5: l'incontro al meglio dei 3 durava meno di 12 minuti simulati.
    PAUSA_FRA_PUNTI: float = 3.5
    DURATA_SOSTITUZIONE: float = 30.0
    DURATA_CAMBIO_ATTREZZO: float = 30.0
    INTERVALLO_RISCALDAMENTO: tuple = (2.0, 3.5)


TARATURA = Taratura()


def carica_taratura(percorso, base=TARATURA):
    """
    Una taratura letta da un file JSON di sostituzioni: un dizionario dei nomi da cambiare, con
    il valore nuovo. Le tabelle si scrivono come liste di coppie; per un colpo basta un dizionario
    con i campi da cambiare, come {"COLPI": {"bomba": {"fallo_base": 0.08}}}. Un nome che non
    esiste solleva ValueError, perché un errore di battitura non passi in silenzio.
    """
    with open(percorso, encoding="utf-8") as f:
        sostituzioni = json.load(f)
    return applica_sostituzioni(sostituzioni, base)


def applica_sostituzioni(sostituzioni, base=TARATURA):
    """La taratura base con le sostituzioni indicate in un dizionario; ValueError per un nome sconosciuto."""
    if not isinstance(sostituzioni, dict):
        raise ValueError("Le sostituzioni della taratura vanno scritte come un dizionario di nomi e valori.")
    campi = {campo.name for campo in dataclasses.fields(Taratura)}
    nuovi = {}
    for nome, valore in sostituzioni.items():
        if nome not in campi:
            raise ValueError(f"La taratura non ha un numero che si chiami {nome}.")
        if nome == "COLPI":
            nuovi[nome] = _colpi_sostituiti(base.COLPI, valore)
        elif isinstance(getattr(base, nome), tuple):
            nuovi[nome] = tuple(tuple(v) if isinstance(v, list) else v for v in valore)
        else:
            nuovi[nome] = valore
    return dataclasses.replace(base, **nuovi)


def _colpi_sostituiti(colpi, sostituzioni):
    if not isinstance(sostituzioni, dict):
        raise ValueError("I colpi della taratura vanno scritti come un dizionario di colpi.")
    nuovi = dict(colpi)
    for nome, campi in sostituzioni.items():
        if nome not in colpi:
            raise ValueError(f"La taratura non ha un colpo che si chiami {nome}.")
        for campo in campi:
            if campo not in Colpo._fields or campo == "nome":
                raise ValueError(f"Il colpo {nome} non ha un campo che si chiami {campo}.")
        valori = {campo: tuple(v) if isinstance(v, list) else v for campo, v in campi.items()}
        nuovi[nome] = colpi[nome]._replace(**valori)
    return nuovi
