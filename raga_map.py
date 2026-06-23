"""Maps Carnatic svaras to Western (LilyPond) pitches.

Design
------
Rather than hardcoding a full svara->pitch table for every raga and every
octave, we separate three concerns:

1. CHROMATIC   - the 12 semitones above Sa -> LilyPond note name (Sa = C).
                 Defined once. Change this one table to retune everything.
2. SVARA       - named svara variants (R1/R2/R3, G1..., etc.) -> semitone.
                 Lets a raga be written the way musicians describe it.
3. RAGA_MAP    - each raga declares only which variant of each of the seven
                 svaras it uses. A raga is now ~1 line instead of a 15-entry,
                 3-octave dict.

Octaves are handled programmatically (see `to_lilypond`): the octave is read
from the diacritic on the svara, so every raga works in every octave without
re-listing notes.
"""

import unicodedata

# --- 1. Chromatic grid: semitones above Sa -> LilyPond note (Sa = C) ---------
# Middle-octave base name, no octave tick. Flats use LilyPond Dutch names
# (des, ees, aes, bes); the sharp Ma uses fis.
CHROMATIC = {
    0:  "c",    # Sa  (shadja, fixed)
    1:  "des",  # R1  (shuddha rishabha)
    2:  "d",    # R2 / G1
    3:  "ees",  # R3 / G2
    4:  "e",    # G3  (antara gandhara)
    5:  "f",    # M1  (shuddha madhyama)
    6:  "fis",  # M2  (prati madhyama)
    7:  "g",    # Pa  (panchama, fixed)
    8:  "aes",  # D1  (shuddha dhaivata)
    9:  "a",    # D2 / N1
    10: "bes",  # D3 / N2
    11: "b",    # N3  (kakali nishada)
}

# --- 2. Named svara variants -> semitone above Sa ----------------------------
# These names mirror standard Carnatic notation, so a raga reads like its
# textbook arohana. The overlaps (R2==G1, R3==G2, D2==N1, D3==N2) are real.
SVARA = {
    "S":  0,
    "R1": 1, "R2": 2, "R3": 3,
    "G1": 2, "G2": 3, "G3": 4,
    "M1": 5, "M2": 6,
    "P":  7,
    "D1": 8, "D2": 9, "D3": 10,
    "N1": 9, "N2": 10, "N3": 11,
}

# --- 3. Ragas: which variant of each svara the raga uses ----------------------
# Sa and Pa (when present) need no variant number. Only list the svaras the
# raga actually contains -- janya ragas that omit notes simply leave them out.
# A song that uses a svara absent from its raga raises a clear error.
#
# For asymmetric (vakra) ragas whose ascending/descending scales differ, list
# the union of svaras used; the single map matches this tool's one-scale model.
RAGA_DEFINITIONS = {
    # --- Melakarta (parent) ragas -------------------------------------------
    "mayamalavagowla": ["R1", "G3", "M1", "P", "D1", "N3"],  # mela 15
    "sankarabharanam": ["R2", "G3", "M1", "P", "D2", "N3"],  # mela 29 (major scale)
    "kharaharapriya":  ["R2", "G2", "M1", "P", "D2", "N2"],  # mela 22 (Dorian)
    "harikambhoji":    ["R2", "G3", "M1", "P", "D2", "N2"],  # mela 28 (Mixolydian)
    "kalyani":         ["R2", "G3", "M2", "P", "D2", "N3"],  # mela 65 (Lydian)
    "todi":            ["R1", "G2", "M1", "P", "D1", "N2"],  # mela 8  (Hanumatodi)
    "natabhairavi":    ["R2", "G2", "M1", "P", "D1", "N2"],  # mela 20 (natural minor)
    "charukesi":       ["R2", "G3", "M1", "P", "D1", "N2"],  # mela 26
    "vachaspati":      ["R2", "G3", "M2", "P", "D2", "N2"],  # mela 64

    # --- Janya (derived) ragas ----------------------------------------------
    "mohanam":     ["R2", "G3", "P", "D2"],              # janya of 28, pentatonic
    "hamsadhwani": ["R2", "G3", "P", "N3"],              # janya of 29
    "hindolam":    ["G2", "M1", "D1", "N2"],             # janya of 20, pentatonic
    "abhogi":      ["R2", "G2", "M1", "D2"],             # janya of 22
    "sriranjani":  ["R2", "G2", "M1", "D2", "N2"],       # janya of 22 (no Pa)
    "malahari":    ["R1", "G3", "M1", "P", "D1"],        # janya of 15 (no Ni)
    "kuntalavarali": ["M1", "P", "D2", "N2"],            # janya of 28 (S M P D N; no Ri/Ga)
    "suposhini":   ["R2", "M1", "P", "D2", "N2"],        # janya of 28, vakra (no Ga)
}


def variants_to_map(variants):
    """Expand a raga's variant list (['R2','G3',...]) into {base -> semitone}."""
    notes = {"S": SVARA["S"]}      # Sa is always present
    for v in variants:
        notes[v[0]] = SVARA[v]     # "R2" -> base "R", "P" -> base "P"
    return notes


# raga name -> {base svara letter (S R G M P D N) -> semitone above Sa}
RAGA_MAP = {name: variants_to_map(v) for name, v in RAGA_DEFINITIONS.items()}


def get_raga(name):
    """Resolve a raga name to its {base svara -> semitone} map.

    Lookup order: bundled RAGA_DEFINITIONS, then the local cache / Wikipedia
    (see raga_source). Raises LookupError if the name can't be resolved.
    """
    key = name.strip().lower()
    if key in RAGA_MAP:
        return RAGA_MAP[key]
    import raga_source                     # imported lazily: no web code unless needed
    return variants_to_map(raga_source.get(name))


# Taala -> Western time signature. A few common transliteration spellings map
# to the same value (rupakam / roopakam, thisra / tisra).
TAALAM_MAP = {
    "rupakam": "6/4",
    "roopakam": "6/4",
    "eka_thisra": "3/4",
    "eka_tisra": "3/4",
    "adi": "4/4",
    "misra_chapu": "7/8",
    "khanda_chapu": "5/8",
}


# --- Octave-aware svara -> LilyPond pitch -------------------------------------
_DOT_ABOVE = unicodedata.lookup("COMBINING DOT ABOVE")  # upper octave (e.g. Ṡ, Ṗ)
_DOT_BELOW = unicodedata.lookup("COMBINING DOT BELOW")  # lower octave (e.g. Ṇ, Ḍ)


def parse_svara(token):
    """Split a svara token into (base letter, octave offset).

    Octave can be written two ways, which may be combined and stacked:
      * ASCII (easy to type): trailing "'" raises an octave, "," lowers one
        (LilyPond-style), e.g. S' = upper Sa, S'' = two up, N, = lower Ni.
      * Diacritic: combining dot above = +1, dot below = -1 (e.g. Ṡ, Ṇ).
    Also accepts the legacy 'Pl' spelling for lower-octave Pa.
    """
    if token.upper() == "PL":          # legacy lower-Pa notation
        return "P", -1

    octave = 0
    base = []
    for ch in unicodedata.normalize("NFD", token):
        if ch == _DOT_ABOVE or ch == "'":
            octave += 1
        elif ch == _DOT_BELOW or ch == ",":
            octave -= 1
        elif unicodedata.combining(ch):
            continue                   # ignore any other combining mark
        else:
            base.append(ch)
    return "".join(base).upper(), octave


def to_lilypond(token, raga):
    """Translate one svara token (no duration suffix) to a LilyPond pitch."""
    base, octave = parse_svara(token)
    if base not in raga:
        raise KeyError(
            f"svara '{base}' (from '{token}') is not in this raga; "
            f"available: {sorted(raga)}"
        )
    note = CHROMATIC[raga[base]]
    ticks = 1 + octave                 # middle octave = c' (one tick) in LilyPond
    if ticks > 0:
        note += "'" * ticks
    elif ticks < 0:
        note += "," * -ticks
    return note
