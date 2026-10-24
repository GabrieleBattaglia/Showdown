"""
La tastiera simulata delle prove e dei banchi delle finestre di MESS, dentro il processo, sul desktop nascosto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-24 con la decisione D36, dal prototipo dell'elenco virtuale, strumenti/prova_elenco_virtuale.py,
per le prove della finestra Mercato e ricerca. Niente arriva allo schermo vero: SendInput lo toccherebbe, e qui
non si usa mai. Ci sono tre modi di battere un tasto, perché wx e Windows li trattano in tre modi diversi.
premi e batti mandano il tasto al controllo con SendMessage: arriva diritto alla finestra del controllo, come
le frecce di un elenco o le lettere della ricerca per iniziali, senza passare dal ciclo dei messaggi.
posta_tasto, posta_alt e posta_esc mettono il tasto nella coda dei messaggi, con PostMessage: lo prende il ciclo
che gira, e passa da IsDialogMessage come il tasto vero, quindi Tab, Ctrl+Tab e le lettere rapide con Alt fanno
quello che fanno con la tastiera. Le lettere con Alt arrivano come WM_SYSCHAR soltanto: un WM_SYSKEYDOWN messo in
coda farebbe nascere a TranslateMessage un secondo WM_SYSCHAR, e il pulsante si premerebbe due volte, come ha
misurato il passo della finestra il 24 ottobre 2026.
gancio fa a mano l'evento wxEVT_CHAR_HOOK, che il gancio dei tasti di wx crea per un tasto vero e manda al
controllo col fuoco, da cui sale fino alla finestra: Windows chiama quel gancio soltanto per i tasti veri, e
nessuno dei tasti qui sopra lo raggiunge. Restituisce vero se qualcuno ha tenuto il tasto, senza lasciarlo andare.
Il gancio vero, coi tasti veri e NVDA, si collauda a mano: collaudo.txt.
"""

import ctypes
import time
from ctypes import wintypes

import wx

# user32 in una copia tutta sua, con le firme che servono qui: le prove delle finestre sono soltanto per Windows.
user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.SendMessageW.restype = ctypes.c_ssize_t
user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.GetKeyboardState.restype = wintypes.BOOL
user32.GetKeyboardState.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
user32.SetKeyboardState.restype = wintypes.BOOL
user32.SetKeyboardState.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
user32.MapVirtualKeyW.restype = wintypes.UINT
user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
user32.GetFocus.restype = wintypes.HWND
WM_KEYDOWN, WM_KEYUP, WM_CHAR, WM_SYSCHAR = 0x0100, 0x0101, 0x0102, 0x0106
VK_TAB, VK_RETURN, VK_SHIFT, VK_CONTROL, VK_MENU, VK_ESCAPE = 0x09, 0x0D, 0x10, 0x11, 0x12, 0x1B
VK_SPACE, VK_PRIOR, VK_NEXT, VK_END, VK_HOME, VK_LEFT, VK_UP, VK_RIGHT, VK_DOWN = 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28
VK_LSHIFT, VK_LCONTROL, VK_LMENU = 0xA0, 0xA2, 0xA4
# I tasti estesi, che senza il bit 24 di lParam wx leggerebbe come quelli del tastierino.
ESTESI = frozenset({VK_PRIOR, VK_NEXT, VK_END, VK_HOME, VK_LEFT, VK_UP, VK_RIGHT, VK_DOWN})
# I tasti di wx per i codici di Windows che servono al gancio fatto a mano.
_TASTI_DI_WX = {VK_RETURN: wx.WXK_RETURN, VK_ESCAPE: wx.WXK_ESCAPE, VK_TAB: wx.WXK_TAB, VK_SPACE: wx.WXK_SPACE}


def pompa(volte=500):
    """Smista i messaggi e gli eventi in attesa, anche fuori da un ciclo di wx."""
    ciclo = wx.EventLoopBase.GetActive()
    attivatore = None
    if ciclo is None:
        ciclo = wx.GUIEventLoop()
        attivatore = wx.EventLoopActivator(ciclo)
    applicazione = wx.GetApp()
    try:
        for _ in range(volte):
            if ciclo.Pending():
                ciclo.Dispatch()
            elif applicazione.HasPendingEvents():
                applicazione.ProcessPendingEvents()
            else:
                break
    finally:
        del attivatore


def aspetta(condizione, secondi=2.0):
    """Smista i messaggi finché condizione() è vera, al più per tanti secondi; restituisce l'ultimo valore."""
    fine = time.monotonic() + secondi
    while not condizione() and time.monotonic() < fine:
        pompa()
        time.sleep(0.01)
    return condizione()


def _lparam(vk, su=False, alt=False):
    lparam = 1 | ((user32.MapVirtualKeyW(vk, 0) & 0xFF) << 16)
    if vk in ESTESI:
        lparam |= 1 << 24
    if alt:
        lparam |= 1 << 29
    if su:
        lparam |= (1 << 30) | (1 << 31)
    return lparam


def _con_i_tasti_giu(tasti, funzione):
    """Chiama funzione con i tasti dati giù per il filo, con SetKeyboardState, e alla fine torna come prima."""
    prima = (ctypes.c_ubyte * 256)()
    user32.GetKeyboardState(prima)
    stato = (ctypes.c_ubyte * 256)(*prima)
    for vk in tasti:
        stato[vk] = 0x80
    try:
        user32.SetKeyboardState(stato)
        return funzione()
    finally:
        user32.SetKeyboardState(prima)


def _modificatori(ctrl=False, shift=False, alt=False):
    return [*((VK_CONTROL, VK_LCONTROL) if ctrl else ()), *((VK_SHIFT, VK_LSHIFT) if shift else ()), *((VK_MENU, VK_LMENU) if alt else ())]


def premi(controllo, vk, ctrl=False, shift=False):
    """
    Un tasto al controllo, come dalla tastiera ma dentro il processo: lo stato dei tasti del filo dice Ctrl e
    Maiusc se servono, e i messaggi vanno al controllo con SendMessage, senza passare dal ciclo dei messaggi.
    """
    hwnd = controllo.GetHandle()

    def giu_e_su():
        user32.SendMessageW(hwnd, WM_KEYDOWN, vk, _lparam(vk))
        if vk == VK_SPACE:
            user32.SendMessageW(hwnd, WM_CHAR, 0x20, _lparam(vk))
        pompa()
        user32.SendMessageW(hwnd, WM_KEYUP, vk, _lparam(vk, su=True))
        pompa()

    _con_i_tasti_giu([vk, *_modificatori(ctrl, shift)], giu_e_su)


def batti(controllo, carattere):
    """Un carattere al controllo, come un tasto battuto: la lettera arriva con WM_CHAR."""
    user32.SendMessageW(controllo.GetHandle(), WM_CHAR, ord(carattere), 1)
    pompa()


def posta_tasto(vk, ctrl=False, shift=False, controllo=None):
    """
    Un tasto nella coda dei messaggi del controllo col fuoco, o di quello dato, come dalla tastiera: lo prende il
    ciclo che gira, e passa da IsDialogMessage, come Tab e Ctrl+Tab veri.
    """
    hwnd = controllo.GetHandle() if controllo is not None else user32.GetFocus()

    def giu_e_su():
        user32.PostMessageW(hwnd, WM_KEYDOWN, vk, _lparam(vk))
        pompa()
        user32.PostMessageW(hwnd, WM_KEYUP, vk, _lparam(vk, su=True))
        pompa()

    _con_i_tasti_giu([vk, *_modificatori(ctrl, shift)], giu_e_su)


def posta_alt(lettera, controllo=None):
    """Alt e una lettera nella coda dei messaggi del controllo col fuoco, o di quello dato: la lettera rapida, come dalla tastiera."""
    hwnd = controllo.GetHandle() if controllo is not None else user32.GetFocus()

    def lettera_rapida():
        user32.PostMessageW(hwnd, WM_SYSCHAR, ord(lettera.lower()), _lparam(ord(lettera.upper()), alt=True))
        pompa()

    _con_i_tasti_giu(_modificatori(alt=True), lettera_rapida)


def posta_esc(controllo):
    """Esc nella coda dei messaggi del controllo, come dalla tastiera: lo prende il ciclo che gira, anche quello di ShowModal."""
    hwnd = controllo.GetHandle()
    user32.PostMessageW(hwnd, WM_KEYDOWN, VK_ESCAPE, _lparam(VK_ESCAPE))
    user32.PostMessageW(hwnd, WM_KEYUP, VK_ESCAPE, _lparam(VK_ESCAPE, su=True))


def gancio(controllo, tasto, ctrl=False, shift=False, alt=False):
    """
    Il tasto come lo vede il gancio dei tasti di wx: l'evento wxEVT_CHAR_HOOK sul controllo, che sale fino alla
    finestra. tasto è un codice di Windows, come VK_RETURN, o una lettera. Restituisce vero se un gestore lo ha
    tenuto, senza lasciarlo andare oltre: allora wx butta il tasto, e Windows non lo vede.
    """
    evento = wx.KeyEvent(wx.wxEVT_CHAR_HOOK)
    evento.SetEventObject(controllo)
    if isinstance(tasto, str):
        evento.SetKeyCode(ord(tasto.upper()))
        evento.SetUnicodeKey(ord(tasto.upper()))
    else:
        evento.SetKeyCode(_TASTI_DI_WX.get(tasto, tasto))
    evento.SetControlDown(ctrl)
    evento.SetShiftDown(shift)
    evento.SetAltDown(alt)
    tenuto = controllo.GetEventHandler().ProcessEvent(evento) and not evento.IsNextEventAllowed()
    pompa()
    return tenuto
