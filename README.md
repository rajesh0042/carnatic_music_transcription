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

### Mohanam
Pentatonic (5-note) scale — no Ma or Ni.

```
ārohaṇa:   S  R₂  G₃  P  D₂  Ṡ
Western:    C  D   E   G  A   C
```

### Sankarabharanam
Equivalent to the Western major scale (Ionian mode).

```
ārohaṇa:   S  R₂  G₃  M₁  P  D₂  N₃  Ṡ
Western:    C  D   E   F   G  A   B   C
```

### Malahari
Pentatonic-ish scale with flat second and flat sixth.

```
ārohaṇa:   S  R₁  M₁  P  D₁  Ṡ
Western:    C  D♭  F   G  A♭  C
```

## Taalas (Time Signatures)

| Taala       | Time signature | Beats per cycle |
|-------------|----------------|-----------------|
| `adi`       | 4/4            | 8 (2 cycles)    |
| `rupakam`   | 6/4            | 6               |
| `eka_thisra`| 3/4            | 3               |

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

In `raga_map.py`, add a new dict mapping svara symbols to LilyPond pitch names, then register it in `RAGA_MAP`:

```python
MY_RAGA_NOTE_MAP = {
    "S": "c'",
    "R": "des'",   # flat second
    # ... fill in all svaras used by this raga
}

RAGA_MAP = {
    ...,
    "my_raga": MY_RAGA_NOTE_MAP,
}
```

LilyPond pitch names: `c d e f g a b` for naturals, `des ees fis` etc. for flats/sharps. Append `'` for middle octave, `''` for upper octave.

## Code Structure

```
transcribe_song.py   # Main script: parses song file, calls raga_map, emits LilyPond
raga_map.py          # Svara→pitch mappings for each raga; taala→time-signature table
make_song.sh         # Shell wrapper: runs transcribe_song.py then lilypond, opens PDF
songs/               # Song input files (svara text notation)
gen/                 # Generated output (.ly and .pdf) — not committed
```
