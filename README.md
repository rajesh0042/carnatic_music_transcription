# Carnatic Music Transcription

Converts Carnatic music notation (svaras) into Western sheet music via [LilyPond](https://lilypond.org/). You write a song in a simple text-based svara notation, run the tool, and get a typeset PDF score.

## Pipeline

```
songs/vande_meenakshi.txt   →   transcribe_song.py   →   gen/vande_meenakshi.ly   →   lilypond   →   gen/vande_meenakshi.pdf
   (svara text file)               (Python)               (LilyPond source)                              (sheet music PDF)
```

## Dependencies

- Python 3
- [LilyPond](https://lilypond.org/download.html) — must be on your `$PATH`

Install LilyPond on macOS:
```bash
brew install lilypond
```

On Ubuntu/Debian:
```bash
sudo apt install lilypond
```

## Usage

```bash
bash make_song.sh ./songs/vande_meenakshi.txt
```

This generates `./gen/vande_meenakshi.ly` and `./gen/vande_meenakshi.pdf`, then opens the PDF.

To run the Python step alone (e.g. to inspect the LilyPond output):
```bash
python3 transcribe_song.py songs/vande_meenakshi.txt gen/vande_meenakshi.ly
```

## Song File Format

Each song is a plain `.txt` file with two parts:

### 1. Header (line 1) — JSON

```json
{"title": "Vande Meenakshi", "taalam": "adi", "ragam": "SANKARABHARANAM"}
```

| Field    | Description                              | Valid values                                        |
|----------|------------------------------------------|-----------------------------------------------------|
| `title`  | Display title on the score               | Any string                                          |
| `ragam`  | Raga (scale) — maps svaras to pitches    | `mohanam`, `malahari`, `sankarabharanam` (case-insensitive) |
| `taalam` | Tala (time signature)                    | `adi`, `rupakam`, `eka_thisra` (case-insensitive)   |

### 2. Body — svara notation

Each line becomes one stanza in the score. Empty lines and lines under 10 characters are skipped. Lines starting with `{` are also skipped (reserved for section labels).

Svaras are space-separated. The notation is:

#### Notes (Svaras)

Carnatic music uses 7 svaras per octave, written as single letters. The tool supports three octaves:

| Svara | Name | Western analogy | Lower octave | Middle octave | Upper octave |
|-------|------|-----------------|--------------|---------------|--------------|
| Sa    | Shadja      | Do | —   | `S`  | `Ṡ`  |
| Ri    | Rishabha    | Re | —   | `R`  | `Ṙ`  |
| Ga    | Gandhara    | Mi | —   | `G`  | `Ġ`  |
| Ma    | Madhyama    | Fa | `Ṃ` | `M`  | `Ṁ`  |
| Pa    | Panchama    | Sol| `Pl`| `P`  | `Ṗ`  |
| Dha   | Dhaivata    | La | `Ḍ` | `D`  | —    |
| Ni    | Nishada     | Ti | `Ṇ` | `N`  | —    |

Notes are case-insensitive (`s` and `S` are the same).

#### Durations

Duration is indicated by a suffix on the note:

| Suffix | Duration      | Beats (in 4/4) | LilyPond |
|--------|---------------|----------------|----------|
| none   | Quarter note  | 1 beat         | `c4`     |
| `.`    | Half note     | 2 beats        | `c2`     |
| `..`   | Dotted half   | 3 beats        | `c2~ c4` |
| `.;`   | Whole note    | 4 beats        | `c1`     |

Examples: `S` = quarter Sa, `S.` = half Sa, `S..` = dotted half Sa, `S.;` = whole Sa.

### Example stanza

```
s. g. s. g. s. g. m g r s
```

This is: half-Sa, half-Ga, half-Sa, half-Ga, half-Sa, half-Ga, quarter-Ma, quarter-Ga, quarter-Ri, quarter-Sa.

## Ragas

A raga is a scale: it fixes which of the 12 semitones each svara maps to.
Internally (`raga_map.py`) a raga is defined by **which variant** of each svara
it uses — `R1/R2/R3`, `G1/G2/G3`, `M1/M2`, `D1/D2/D3`, `N1/N2/N3` — where the
number is the semitone position (see [Code Structure](#code-structure)).

### Built-in ragas

**Melakarta (parent) ragas:**

| Raga              | Svaras                 | Western analogy        |
|-------------------|------------------------|------------------------|
| `mayamalavagowla` | R1 G3 M1 P D1 N3       | Double harmonic / Bhairav |
| `sankarabharanam` | R2 G3 M1 P D2 N3       | Major scale (Ionian)   |
| `kharaharapriya`  | R2 G2 M1 P D2 N2       | Dorian                 |
| `harikambhoji`    | R2 G3 M1 P D2 N2       | Mixolydian             |
| `kalyani`         | R2 G3 **M2** P D2 N3   | Lydian (sharp 4)       |
| `todi`            | R1 G2 M1 P D1 N2       | Phrygian ♮3-ish        |
| `natabhairavi`    | R2 G2 M1 P D1 N2       | Natural minor (Aeolian)|
| `charukesi`       | R2 G3 M1 P D1 N2       | —                      |
| `vachaspati`      | R2 G3 **M2** P D2 N2   | Lydian dominant        |

**Janya (derived) ragas** — subsets that omit some svaras:

| Raga          | Svaras            | Notes                        |
|---------------|-------------------|------------------------------|
| `mohanam`     | R2 G3 P D2        | pentatonic (no Ma, Ni)       |
| `hamsadhwani` | R2 G3 P N3        | pentatonic (no Ma, Dha)      |
| `hindolam`    | G2 M1 D1 N2       | pentatonic (no Ri, Pa)       |
| `abhogi`      | R2 G2 M1 D2       | pentatonic (no Pa, Ni)       |
| `sriranjani`  | R2 G2 M1 D2 N2    | hexatonic (no Pa)            |
| `malahari`    | R1 G3 M1 P D1     | hexatonic (no Ni)            |

(Sa is always present and Pa is present unless the svara list omits it.)

## Taalas (Time Signatures)

| Taala         | Time signature |
|---------------|----------------|
| `adi`         | 4/4            |
| `rupakam`     | 6/4            |
| `eka_thisra`  | 3/4            |
| `misra_chapu` | 7/8            |
| `khanda_chapu`| 5/8            |

## Included Songs

| File                      | Raga            | Taala       |
|---------------------------|-----------------|-------------|
| `vande_meenakshi.txt`     | Sankarabharanam | Adi         |
| `kamalasana.txt`          | Sankarabharanam | Adi         |
| `syamale_meenakshi.txt`   | Sankarabharanam | Adi         |
| `rama_janardhana.txt`     | Sankarabharanam | Eka Thisra  |
| `vara_veena.txt`          | Mohanam         | Rupakam     |
| `sri_gananadam.txt`       | Malahari        | Rupakam     |

## Adding a New Song

1. Create `songs/my_song.txt`
2. Set the JSON header (title, ragam, taalam)
3. Write svaras line by line using the notation above
4. Run `bash make_song.sh ./songs/my_song.txt`

## Adding a New Raga

Add **one line** to `RAGA_DEFINITIONS` in `raga_map.py` listing which variant of
each svara the raga uses. You never touch pitches or octaves — those are derived.

```python
RAGA_DEFINITIONS = {
    ...,
    "simhendramadhyamam": ["R2", "G2", "M2", "P", "D1", "N3"],  # mela 57
}
```

- Use `R1/R2/R3`, `G1/G2/G3`, `M1/M2`, `D1/D2/D3`, `N1/N2/N3` (the number is the
  variant; see the `SVARA` table for the semitone each maps to).
- `S` is added automatically; include `P` only if the raga has Panchama.
- Omit any svara the raga doesn't use (that's how janya/pentatonic ragas work).
- All three octaves work automatically — no need to list them.

## Adding a New Taala

Add a line to `TAALAM_MAP` in `raga_map.py` mapping the name to a time signature:

```python
TAALAM_MAP = {
    ...,
    "tisra_triputa": "7/4",
}
```

## Code Structure

```
transcribe_song.py   # CLI: parse song file, split notes/durations, emit LilyPond
raga_map.py          # Music theory: chromatic grid, svara variants, raga & taala tables
make_song.sh         # Shell wrapper: runs transcribe_song.py then lilypond, opens PDF
songs/               # Song input files (svara text notation)
gen/                 # Generated output (.ly and .pdf) — not committed
```

### How `raga_map.py` is layered

The redesign separates three concerns so adding ragas needs no pitch math:

1. **`CHROMATIC`** — the 12 semitones above Sa → LilyPond note name, assuming
   Sa = C. Defined **once**. Change this single table to retune everything.
2. **`SVARA`** — named svara variants (`R1`, `G3`, `M2`, …) → semitone offset.
   Lets a raga be written the way musicians describe it.
3. **`RAGA_DEFINITIONS`** — each raga lists only its svara variants. A small
   builder (`_build_raga_map`) expands these into `RAGA_MAP`.

Octaves are handled in `to_lilypond`: the octave is read from the diacritic on
the svara (dot above = upper, dot below = lower), so every raga works in every
octave without re-listing notes.
