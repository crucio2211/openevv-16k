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
PARAM_CONSONANT_DURATION = 35
LANGUAGES = {
    0x70000: ("Brazilian Portuguese", b"O rato roeu a roupa."),
    0x90000: ("Finnish", b"Hei maailma."),
}


def main(path):
    dll = ctypes.CDLL(os.path.abspath(path))
    print("switchlangs: loaded library", flush=True)
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
    dll.eciGetParam.argtypes = [ctypes.c_void_p, ctypes.c_int]
    dll.eciGetParam.restype = ctypes.c_int
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
    print("switchlangs: available languages %s" % sorted(hex(x) for x in available), flush=True)

    handle = dll.eciNewEx(0x10000)
    if not handle:
        raise RuntimeError("could not create English engine instance")
    print("switchlangs: created English instance", flush=True)
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
        print("switchlangs: set output buffer", flush=True)
        dll.eciSetParam(handle, PARAM_INPUT_TYPE, 1)

        # Test the public parameter and the actual US English duration rule.
        # Repeated /p/ words make the duration difference measurable.
        default_duration = dll.eciGetParam(handle, PARAM_CONSONANT_DURATION)
        if default_duration != 100:
            raise RuntimeError("unexpected default consonant duration: %d" % default_duration)

        def sample_count_at(percent):
            nonlocal spoken
            if dll.eciSetParam(handle, PARAM_CONSONANT_DURATION, percent) < 0:
                raise RuntimeError("engine refused consonant duration %d" % percent)
            if dll.eciGetParam(handle, PARAM_CONSONANT_DURATION) != percent:
                raise RuntimeError("consonant duration did not retain %d" % percent)
            spoken = 0
            # Explicitly exercise the consonants from the reported examples:
            # /t/ in "settings", /d/ in "daddy/did", and /p/, /k/, /f/, /s/.
            phrase = b" ".join(
                [b"settings settings settings daddy did it pepper poppy paper piper popper take two tickets fifty five sunny summer"] * 4
            ) + b"."
            if not dll.eciAddText(handle, phrase):
                raise RuntimeError("engine refused consonant-duration test text")
            if not dll.eciSynthesize(handle) or not dll.eciSynchronize(handle):
                raise RuntimeError("engine failed consonant-duration test synthesis")
            if spoken == 0:
                raise RuntimeError("consonant-duration test produced no audio")
            return spoken

        shorter = sample_count_at(80)
        normal = sample_count_at(100)
        longer = sample_count_at(120)
        if not shorter < normal < longer:
            raise RuntimeError(
                "consonant duration did not scale monotonically: "
                "80%%=%d, 100%%=%d, 120%%=%d" % (shorter, normal, longer)
            )
        print(
            "switchlangs: 32-bit consonant duration scaling passed "
            "(80%%=%d, 100%%=%d, 120%%=%d samples)" % (shorter, normal, longer),
            flush=True,
        )
        if dll.eciSetParam(handle, PARAM_CONSONANT_DURATION, default_duration) < 0:
            raise RuntimeError("could not restore default consonant duration")

        for language, (name, sentence) in LANGUAGES.items():
            spoken = 0
            print("switchlangs: selecting " + name, flush=True)
            if not dll.eciSetParam(handle, PARAM_LANGUAGE, language):
                raise RuntimeError("engine refused " + name)
            print("switchlangs: selected " + name, flush=True)
            for voice in range(1, 9):
                voice_name = ctypes.create_string_buffer(64)
                dll.eciGetVoiceName(handle, voice, voice_name)
            print("switchlangs: read voices for " + name, flush=True)
            print("switchlangs: synthesizing " + name, flush=True)
            if not dll.eciAddText(handle, sentence):
                raise RuntimeError("engine refused text for " + name)
            if not dll.eciSynthesize(handle) or not dll.eciSynchronize(handle):
                raise RuntimeError("engine failed to synthesize " + name)
            print("switchlangs: synthesized " + name, flush=True)
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
