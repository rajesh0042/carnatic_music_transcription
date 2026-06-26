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


# One repeating-cycle lehra pattern per (raga, taala), in svara notation.
# Beat totals: Adi = 8 (2 bars of 4/4), Rupakam = 6 (1 bar of 6/4),
# Eka Thisra = 3 (1 bar of 3/4).  Janya ragas with missing svaras need
# custom patterns; full-7-svara ragas use the "_default" fallback.
LEHRA_PATTERNS = {
    # --- Janya: pentatonic (5 svaras + Sa) ------------------------------------
    ("mohanam",     "adi"):         "s. g. p. d.",      # S R G P D — no M N  [2+2+2+2=8]
    ("mohanam",     "rupakam"):     "s r g p d s'",      # [6]
    ("mohanam",     "eka_thisra"):  "s g p",             # [3]
    ("hamsadhwani", "adi"):         "s. g. p. n.",       # S R G P N — no M D  [8]
    ("hamsadhwani", "rupakam"):     "s r g p n s'",      # [6]
    ("hindolam",    "adi"):         "s. g. m. d.",       # S G M D N — no R P  [8]
    ("hindolam",    "rupakam"):     "s g m d n s'",      # [6]
    ("abhogi",      "adi"):         "s. r. g. m.",       # S R G M D — no P N  [8]
    ("abhogi",      "rupakam"):     "s r g m d s'",      # [6]
    ("kuntalavarali","adi"):        "s. m. p. d.",       # S M P D N — no R G  [8]
    ("kuntalavarali","rupakam"):    "s m p d n s'",      # [6]
    # --- Janya: hexatonic (6 svaras + Sa) -------------------------------------
    ("malahari",    "adi"):         "s r m p d. r.",     # S R G M P D — no N  [1+1+1+1+2+2=8]
    ("malahari",    "rupakam"):     "s r m p d s'",      # [6]
    ("malahari",    "eka_thisra"):  "s r m",             # [3]
    ("sriranjani",  "adi"):         "s. r. g. m.",       # S R G M D N — no P  [8]
    ("sriranjani",  "rupakam"):     "s r g m d n",       # [6]
    ("suposhini",   "adi"):         "s r m p d. r.",     # S R M P D N — no G  [8]
    ("suposhini",   "rupakam"):     "s r m p d n",       # [6]
    # --- Default: full 7-svara ragas (all melakarta; most Wikipedia ragas) ----
    ("_default",    "adi"):         "s r g m p d n s'",  # [8]
    ("_default",    "rupakam"):     "s r g m p d",       # [6]
    ("_default",    "eka_thisra"):  "s r g",             # [3]
}


# Tabla theka patterns per taala, in LilyPond \drummode notation.
# boh = High Bongo / dayan, bol = Low Bongo / bayan, <bol boh> = Dha (both together).
TABLA_PATTERNS = {
    "adi":          "<bol boh>4 boh4 boh4 bol4",                              # 4 beats
    "rupakam":      "<bol boh>4 boh4 boh4 boh4 bol4 boh4",                   # 6 beats
    "roopakam":     "<bol boh>4 boh4 boh4 boh4 bol4 boh4",
    "eka_thisra":   "<bol boh>4 boh4 bol4",                                   # 3 beats
    "eka_tisra":    "<bol boh>4 boh4 bol4",
    "misra_chapu":  "<bol boh>8 boh8 boh8 <bol boh>8 boh8 <bol boh>8 boh8",  # 7 eighths
    "khanda_chapu": "<bol boh>8 boh8 <bol boh>8 boh8 boh8",                   # 5 eighths
}

# Quarter-note beats per tabla cycle
_TABLA_BEATS = {
    "adi": 4, "rupakam": 6, "roopakam": 6,
    "eka_thisra": 3, "eka_tisra": 3,
    "misra_chapu": 3.5, "khanda_chapu": 2.5,
}


def get_tabla_pattern(taala_name):
    """Return (drummode_pattern, cycle_beats) or (None, None) if unsupported."""
    key = taala_name.strip().lower()
    pat = TABLA_PATTERNS.get(key)
    beats = _TABLA_BEATS.get(key)
    return (pat, beats) if (pat and beats) else (None, None)


_TAALA_ALIASES = {"roopakam": "rupakam", "eka_tisra": "eka_thisra"}


def get_lehra_pattern(raga_name, taala_name):
    """Return the lehra svara string for a (raga, taala) pair, or None if unsupported."""
    raga_key = raga_name.strip().lower()
    taala_key = _TAALA_ALIASES.get(taala_name.strip().lower(), taala_name.strip().lower())
    pat = LEHRA_PATTERNS.get((raga_key, taala_key))
    if pat is not None:
        return pat
    return LEHRA_PATTERNS.get(("_default", taala_key))  # None for compound meters


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


_DOT_ABOVE_MAP = {'S': 'Ṡ', 'R': 'Ṙ', 'G': 'Ġ', 'M': 'Ṁ', 'P': 'Ṗ', 'D': 'Ḋ', 'N': 'Ṅ'}
_DOT_BELOW_MAP = {'S': 'Ṣ', 'R': 'Ṛ', 'M': 'Ṃ', 'D': 'Ḍ', 'N': 'Ṇ'}


def to_display_svara(token):
    """Return the display form of a svara token using precomposed Unicode characters.

    Uses precomposed dot-above (Ṡ Ṙ Ġ Ṁ Ṗ Ḋ Ṅ) for upper octave and
    dot-below (Ṣ Ṛ Ṃ Ḍ Ṇ) for lower octave. Falls back to combining
    diacritics for the rare cases with no precomposed form (G↓, P↓).
    Strips duration and grace-note markers before converting.
    """
    token = token.replace('*', '').replace('!', '').rstrip('.;')
    base, octave = parse_svara(token)
    if octave == 0:
        return base
    if octave == 1:
        return _DOT_ABOVE_MAP.get(base, base + _DOT_ABOVE)
    if octave == -1:
        return _DOT_BELOW_MAP.get(base, base + _DOT_BELOW)
    if octave > 1:
        return _DOT_ABOVE_MAP.get(base, base + _DOT_ABOVE) + _DOT_ABOVE * (octave - 1)
    return _DOT_BELOW_MAP.get(base, base + _DOT_BELOW) + _DOT_BELOW * (-octave - 1)


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
