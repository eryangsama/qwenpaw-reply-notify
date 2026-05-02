# -*- coding: utf-8 -*-
"""QwenPaw answer-done notification via winsound (daemon-safe, no GUI)."""

from __future__ import annotations

import ctypes
import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

_active = False
_active_lock = threading.Lock()


def notify_done() -> None:
    """Play notification sound when agent reply is done."""
    global _active
    with _active_lock:
        if _active:
            return
        _active = True

    def _show():
        global _active
        try:
            _notify_impl()
        finally:
            with _active_lock:
                _active = False

    t = threading.Thread(target=_show, daemon=True)
    t.start()


def _notify_impl() -> None:
    """Play the notify.wav file via winmm MCI (supports MP3/WAV)."""
    try:
        _script_dir = Path(__file__).parent
        _wav = _script_dir / "assets" / "notify.wav"
        if _wav.exists():
            _play_via_mci(str(_wav))
        else:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception as e:
        logger.debug("notify_done sound error: %s", e)
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass


def _play_via_mci(filepath: str) -> None:
    """Play audio file via Windows MCI (supports MP3, WAV, etc.)."""
    import ctypes.wintypes as wintypes

    MCIERROR = wintypes.DWORD
    mciSendString = ctypes.windll.winmm.mciSendStringW
    mciSendString.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.UINT, wintypes.HANDLE]
    mciSendString.restype = MCIERROR

    alias = "qwenpaw_notify"

    # Close any existing instance first
    mciSendString(f"close {alias}", None, 0, None)

    # Open and play — type mpegvideo lets MCI handle any audio format
    cmd = f'open "{filepath}" type mpegvideo alias {alias}'
    err = mciSendString(cmd, None, 0, None)
    if err:
        # Fallback: try winsound
        try:
            import winsound
            winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass
        return

    mciSendString(f"play {alias}", None, 0, None)

    # Close after 3s (non-blocking via thread)
    def _cleanup():
        import time
        time.sleep(3)
        mciSendString(f"close {alias}", None, 0, None)

    threading.Thread(target=_cleanup, daemon=True).start()