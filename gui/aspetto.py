"""
L'aspetto dei controlli di MESS: caratteri e colori delle impostazioni.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 5 del piano, dalla funzione apply_visual_settings di Tornello:
carattere a spaziatura fissa, colore del testo e dello sfondo, e per le aree di testo ricche lo
stile ridato a tutto il testo, perché il RichEdit di Windows non lo eredita dai colori del controllo.
"""

import wx

from impostazioni import da_percentuale


def colore(percentuali):
    return wx.Colour(*(da_percentuale(c) for c in percentuali))


def carattere(impostazioni):
    return wx.Font(impostazioni["dimensione"], wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)


def applica(controllo, impostazioni):
    """Dà al controllo il carattere e i colori delle impostazioni."""
    testo = colore(impostazioni["colore_testo"])
    sfondo = colore(impostazioni["colore_sfondo"])
    font = carattere(impostazioni)
    controllo.SetFont(font)
    controllo.SetForegroundColour(testo)
    controllo.SetBackgroundColour(sfondo)
    if isinstance(controllo, wx.TextCtrl):
        stile = wx.TextAttr(testo, sfondo, font)
        controllo.SetDefaultStyle(stile)
        if controllo.GetLastPosition():
            controllo.SetStyle(0, controllo.GetLastPosition(), stile)
    controllo.Refresh()


def ridai_stile(controllo, impostazioni):
    """Dopo aver cambiato il testo di un'area ricca, gli ridà lo stile delle impostazioni."""
    if controllo.GetLastPosition():
        controllo.SetStyle(0, controllo.GetLastPosition(), wx.TextAttr(colore(impostazioni["colore_testo"]), colore(impostazioni["colore_sfondo"]), carattere(impostazioni)))
