# Changes since openevv-16k-main.zip

Base: your openevv-16k main (forked from Mudb0y/openevv ~50 commits before its HEAD).
This tree = your main + Mudb0y/openevv main merged in + your evdroid patches/dictionary edits.
Copy the contents of `openevv-16k/` over your repo (or add it as a branch and review with `git diff`).

## Merged from upstream (Mudb0y/openevv)
- 6.1 number / hyphen / money / phone rules (what evdroid 0014, 0023-0027 did), Finnish (fifi), Brazilian Portuguese (ptbr), new pause mode in the engine (PARAM 33).
- Not applied because upstream has them natively: evdroid 0011 (partly, see below), 0012, 0013, 0014, 0023-0027.
- Conflicts: your driver (nvda/addon/synthDrivers/*.py) and nvda tests kept as yours; engine C conflicts combined (your wideband THIS/MANGLED changes + upstream setPauses).

## Your evdroid patches re-applied
- 0006 hetero plain words, 0007 enus codepoints (adds lang/enus/enus.codepoints), 0009 wide above 16k, 0019 encourage/mutual, 0028 exclamation second npush.
- 0011 names: the 36 entries upstream did not have were re-added to lang/enus/enus.dict (buffet left to upstream's homograph entry).

## Your own enus.dict edits (restored)
- candidate `k A n d X d e t`, open `o p X n`, poor `p u r`, poors `p u r z`, produce (roots3) `p r U d u s`.
- Removed: produce (it lives in the hetero table, src/eci/hetero), fatima (pronounced by the rules again), quality, produce (homog_roots, pnames4), address, persona, visual, and 13 punctuation names in eng_char_name.
- After editing enus.dict run: `make rulecode LANGS=lang/enus` then `EVV_LANG_DIR=lang/enus python3 tools/module/dict.py build`.
  New entries must be in the engine's search order (use `dict.py where`).

## NVDA driver (nvda/addon/synthDrivers)
- Sample rates 8, 11.025, 16, 22.05, 32, 44.1, 48 kHz (engine codes 0,1,3,2,4,5,6); label format `%g kHz`.
- Finnish (0x90000, fi_FI, fin) and Brazilian Portuguese (0x70000, pt_BR, ptb) in the language tables.
- New "Pauses" setting like IBMTTS: 0 Do not shorten / 1 Shorten at end of text only / 2 Shorten all pauses (default 1).
- nvda/test/engine.py expectation updated for the rate list. nvda/test/sequence.py still has 5 stale checks (PIECE_CAP = 20).

## Build used
`EVVPLAIN=1 make nvda LANGS="lang/enus lang/engb lang/dede lang/eses lang/esus lang/fifi lang/frca lang/frfr lang/itit lang/jajp lang/plpl lang/ptbr"`
then `python3 nvda/build.py --version 1.3.6`. The `matrix` baseline was not regenerated.
- nvda/manifest.ini.in: author set to "Rosendo Barde Hubilla Jr." (url still upstream; keep LICENSE/NOTICE as they are, MIT requires the copyright notice).
- nvda/addon/installTasks.py (packed by nvda/build.py): on update, copies the reader's dictionary files (enumain.dic etc.) from the old synthDrivers folder into the new one, never overwriting; same idea as IBMTTS.
