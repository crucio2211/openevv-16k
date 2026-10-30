#!/usr/bin/env python3
"""Exercise Finnish and Brazilian Portuguese through NVDA's language path.

The NVDA driver creates one English instance, changes its language, reads all
eight voice names, and then speaks. This catches a language table that merely
compiles but faults as soon as the reader selects one of its extra languages.
"""

import ctypes
import os
import sys

FRAME = 2048
PARAM_INPUT_TYPE = 1
PARAM_LANGUAGE = 9
LANGUAGES = {
    0x70000: ("Brazilian Portuguese", b"O rato roeu a roupa."),
    0x90000: ("Finnish", b"Hei maailma."),
}


def main(path):
    dll = ctypes.CDLL(os.path.abspath(path))
    dll.eciNewEx.restype = ctypes.c_void_p
    dll.eciNewEx.argtypes = [ctypes.c_int]
    dll.eciDelete.argtypes = [ctypes.c_void_p]
    dll.eciGetAvailableLanguages.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
    dll.eciRegisterCallback.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                        ctypes.c_void_p]
    dll.eciSetOutputBuffer.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                       ctypes.c_void_p]
    dll.eciSetParam.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    dll.eciGetVoiceName.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                    ctypes.c_char_p]
    dll.eciAddText.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    dll.eciSynthesize.argtypes = [ctypes.c_void_p]
    dll.eciSynchronize.argtypes = [ctypes.c_void_p]

    count = ctypes.c_int()
    if dll.eciGetAvailableLanguages(None, ctypes.byref(count)):
        raise RuntimeError("could not enumerate engine languages")
    found = (ctypes.c_uint * count.value)()
    dll.eciGetAvailableLanguages(found, ctypes.byref(count))
    available = set(found[:count.value])
    missing = set(LANGUAGES) - available
    if missing:
        raise RuntimeError("missing language IDs: " + ", ".join(hex(x) for x in missing))

    handle = dll.eciNewEx(0x10000)
    if not handle:
        raise RuntimeError("could not create English engine instance")
    buffer = (ctypes.c_short * FRAME)()
    spoken = 0
    callback_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p,
                                     ctypes.c_int, ctypes.c_int,
                                     ctypes.c_void_p)

    @callback_type
    def callback(_handle, message, samples, _data):
        nonlocal spoken
        if message == 0:
            spoken += samples
        return 1

    try:
        dll.eciRegisterCallback(handle, callback, None)
        if not dll.eciSetOutputBuffer(handle, FRAME, buffer):
            raise RuntimeError("engine refused the output buffer")
        dll.eciSetParam(handle, PARAM_INPUT_TYPE, 1)
        for language, (name, sentence) in LANGUAGES.items():
            spoken = 0
            if not dll.eciSetParam(handle, PARAM_LANGUAGE, language):
                raise RuntimeError("engine refused " + name)
            for voice in range(1, 9):
                voice_name = ctypes.create_string_buffer(64)
                dll.eciGetVoiceName(handle, voice, voice_name)
            if not dll.eciAddText(handle, sentence):
                raise RuntimeError("engine refused text for " + name)
            if not dll.eciSynthesize(handle) or not dll.eciSynchronize(handle):
                raise RuntimeError("engine failed to synthesize " + name)
            if spoken == 0:
                raise RuntimeError("engine produced no audio for " + name)
            print("switchlangs: %s spoke %d samples" % (name, spoken))
            if not dll.eciSetParam(handle, PARAM_LANGUAGE, 0x10000):
                raise RuntimeError("engine could not return to English")
    finally:
        dll.eciDelete(handle)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: switchlangs.py <libeci.so>")
    try:
        raise SystemExit(main(sys.argv[1]))
    except Exception as exc:
        print("switchlangs: %s" % exc, file=sys.stderr)
        raise
