"""
Strumenti comuni alle prove delle migrazioni del salvataggio: un documento del formato attuale
riportato com'era nel formato 6 o nel formato 5, da cui le prove dei formati più vecchi tolgono il resto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-09 con la tappa 11 e il formato 6; dal 2026-10-13, con la tappa 12, anche il formato 7.
Dal 2026-11-02, con la decisione D40, anche il formato 10, di un documento del formato 11. È di Gabriele Battaglia
(IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode). Con la quinta tranche di D40 il formato 10 perde anche le due voci dei
conti di Sposta fondi. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import copy

from costanti import MAPPA_ARCHETIPI_INDOLI

# I campi del giocatore che nascono con il formato 6, oltre ai due rinominati.
CAMPI_DEL_FORMATO_6 = ("programma", "intensita", "talento", "apprendista_rapido", "maturazione", "ambizione", "costanza", "contratto_stipendio",
                       "contratto_scadenza", "rinnovo_stipendio", "rinnovo_scadenza", "proposte_rinnovo", "ultima_trattativa")
# I campi del giocatore che nascono con il formato 7, della tappa 12, oltre a quello rinominato.
CAMPI_DEL_FORMATO_7 = ("acciacco_fino", "acciacco_calo", "acciacco_giorni", "acciacco_sede", "tornei_giocati", "punti_mondiali", "punti_recenti", "titoli",
                       "prossimo_torneo", "iscrizione_automatica", "gare_squadre_vinte", "gare_squadre_perse")
# Le strutture del mondo che nascono con il formato 7.
CAMPI_MONDO_DEL_FORMATO_7 = ("calendario", "sfide")
# I campi rinominati dal formato 7: dal nome di prima al nome nuovo.
RINOMINATI_DEL_FORMATO_7 = {"ultima_amichevole": "ultimo_impegno"}
# I campi della polisportiva e le voci dei conti che nascono con il formato 7.
CAMPI_POLISPORTIVA_DEL_FORMATO_7 = ("palmares_recente", "sfide_da_lanciare", "ultima_sfida", "sfide_vinte", "sfide_perse")
VOCI_DEL_FORMATO_7 = ("iscrizioni", "premi", "rimborsi")
ARCHETIPO_DELL_INDOLE = {indole: archetipo for archetipo, indole in MAPPA_ARCHETIPI_INDOLI.items()}
# I campi che nascono con il formato 11, della decisione D40: nel mondo, in ogni giocatore e in ogni allenatore.
CAMPI_MONDO_DEL_FORMATO_11 = ("fondazioni_di_sempre",)
CAMPI_DEL_FORMATO_11 = ("tesserato_dal",)
CAMPI_ALLENATORE_DEL_FORMATO_11 = ("escluso_dall_utente_fino",)
# Le voci dei conti che nascono con la quinta tranche di D40, sempre nel formato 11: i fondi di Sposta fondi.
VOCI_DEL_FORMATO_11 = ("fondi_ricevuti", "fondi_versati")


def al_formato_10(contenuto):
    """
    Un documento del formato 11 com'era nel formato 10: senza il contatore delle fondazioni, la firma dei giocatori, il giorno
    degli allenatori e le voci dei conti di Sposta fondi.
    """
    vecchio = copy.deepcopy(contenuto)
    for campo in CAMPI_MONDO_DEL_FORMATO_11:
        del vecchio["mondo"][campo]
    for g in vecchio["mondo"]["giocatori"]:
        for campo in CAMPI_DEL_FORMATO_11:
            del g[campo]
    for a in vecchio["mondo"]["allenatori"]:
        for campo in CAMPI_ALLENATORE_DEL_FORMATO_11:
            del a[campo]
    for p in vecchio["mondo"]["polisportive"].values():
        for voce in VOCI_DEL_FORMATO_11:
            del p["conti_del_mese"][voce]
            for bilancio in p["bilanci"]:
                del bilancio[voce]
    vecchio["formato"] = 10
    return vecchio


def al_formato_6(contenuto):
    """Un documento del formato 7 com'era nel formato 6: senza i campi della tappa 12, con i nomi di prima."""
    vecchio = copy.deepcopy(contenuto)
    for campo in CAMPI_MONDO_DEL_FORMATO_7:
        del vecchio["mondo"][campo]
    for g in vecchio["mondo"]["giocatori"]:
        for campo in CAMPI_DEL_FORMATO_7:
            del g[campo]
        for prima, dopo in RINOMINATI_DEL_FORMATO_7.items():
            g[prima] = g.pop(dopo)
    for p in vecchio["mondo"]["polisportive"].values():
        for campo in CAMPI_POLISPORTIVA_DEL_FORMATO_7:
            del p[campo]
        for voce in VOCI_DEL_FORMATO_7:
            del p["conti_del_mese"][voce]
            for bilancio in p["bilanci"]:
                del bilancio[voce]
    vecchio["formato"] = 6
    return vecchio


def al_formato_5(contenuto):
    """
    Un documento del formato 7 com'era nel formato 5: i punti esperienza interi al posto dei punti
    allenamento, l'archetipo al posto dell'indole, senza i campi nuovi e senza le voci di diario
    delle spese d'allenamento; i conti delle polisportive senza la voce delle buonuscite.
    """
    vecchio = al_formato_6(contenuto)
    for p in vecchio["mondo"]["polisportive"].values():
        del p["conti_del_mese"]["buonuscite"]
        for bilancio in p["bilanci"]:
            del bilancio["buonuscite"]
    for g in vecchio["mondo"]["giocatori"]:
        g["puntiesperienza"] = int(g.pop("punti_allenamento"))
        g["archetipo_allenamento"] = ARCHETIPO_DELL_INDOLE[g.pop("indole")]
        for campo in CAMPI_DEL_FORMATO_6:
            del g[campo]
        g["diario"] = [voce for voce in g["diario"] if "spesa" not in voce]
    vecchio["formato"] = 5
    return vecchio
