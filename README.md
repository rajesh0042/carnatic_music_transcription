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

## Browsing all songs (static site)

To render every song in `songs/` and build a browsable index:

```bash
uv run python build_site.py
```

This writes `site/index.html` (a sortable list of all songs with their raga and
tala) plus `site/pdfs/<song>.pdf`. Open `site/index.html` in a browser, or host
the self-contained `site/` folder on any static host (e.g. GitHub Pages). The
`site/` folder is generated and git-ignored.

Pre-rendered PDFs of every song are also committed under [`pdfs/`](pdfs/) for
quick browsing on GitHub. Regenerate them with:

```bash
for f in songs/*.txt; do n=$(basename "$f" .txt); \
  python3 transcribe_song.py "$f" /tmp/"$n".ly && lilypond -o pdfs/"$n" /tmp/"$n".ly; done
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
| `tempo`  | MIDI playback speed in BPM (optional)    | Any integer; default `80`                           |
| `lehra`  | Include a repeating lehra melody in MIDI | `true` / `false` (default `false`)                  |
| `tabla`  | Include a tabla percussion track in MIDI | `true` / `false` (default `false`)                  |

### 2. Body — svara notation

Each line becomes one stanza in the score. Empty lines and lines under 10 characters are skipped. A line of the form `{Section Name}` becomes a heading in the score (see [Section labels](#section-labels)).

Svaras may be space-separated or written contiguously — `s n d p`, `sndp`, and
`(sndp)` all parse the same way (spacing never affects rhythm; only `( )` speed
brackets do). The notation is:

#### Notes (Svaras)

Carnatic music uses 7 svaras per octave, written as single letters. The tool supports three octaves:

| Svara | Name | Western analogy | Middle octave |
|-------|------|-----------------|---------------|
| Sa    | Shadja      | Do | `S` |
| Ri    | Rishabha    | Re | `R` |
| Ga    | Gandhara    | Mi | `G` |
| Ma    | Madhyama    | Fa | `M` |
| Pa    | Panchama    | Sol| `P` |
| Dha   | Dhaivata    | La | `D` |
| Ni    | Nishada     | Ti | `N` |

Notes are case-insensitive (`s` and `S` are the same).

#### Octaves

Mark the octave with a suffix (these stack, e.g. `s''` is two octaves up):

| Octave        | ASCII (preferred) | Diacritic   |
|---------------|-------------------|-------------|
| Upper         | `s'`              | `Ṡ Ṙ Ġ Ṁ Ṗ` |
| Middle        | `s`               | `S R G M P D N` |
| Lower         | `s,`              | `Ṇ Ḍ Ṃ` (and `Pl` for lower Pa) |

The ASCII form (`'` up, `,` down — borrowed from LilyPond) is easiest to type;
the dotted form is still accepted, so older songs keep working. The octave
suffix goes before the duration suffix: `s'.;` = whole-note upper Sa.

#### Durations

Duration is indicated by a suffix on the note:

| Suffix  | Duration           | Beats (in 4/4) | LilyPond          |
|---------|--------------------|----------------|-------------------|
| none    | Quarter note       | 1 beat         | `c4`              |
| `.`     | Half note          | 2 beats        | `c2`              |
| `..`    | Dotted half        | 3 beats        | `c2~ c4`          |
| `.;`    | Whole note         | 4 beats        | `c1`              |
| `.;;`   | Two wholes (tied)  | 8 beats        | `c1~ c1`          |
| `.;;;`  | Three wholes (tied)| 12 beats       | `c1~ c1~ c1`      |

Each additional `;` adds another whole note (4 beats) as a tie. You can stack as many as needed.

Examples: `S` = quarter Sa, `S.` = half Sa, `S..` = dotted half Sa, `S.;` = whole Sa, `S.;;;` = Sa held for 12 beats.

A duration mark may also stand on its own to **extend the previous svara**, the
way a Carnatic `,`/`;` lengthens a note: `S .` means the same as `S.`, and
`D D D .` is `D D D.` (the third Dha held for two beats).

#### Speed (double tempo / madhyamakāla)

Wrap svaras in parentheses to play them at double tempo — each `(` halves the
note values for the svaras it encloses, and `)` restores the previous speed.
Nest `(( ))` for quadruple tempo. Speed composes with the duration suffixes
above, and you can mix slow and fast within one line:

```
p d (n s' n d) p.; ((s' n d p)) s.;
```

| Nesting    | Note value (from a plain svara) | Svaras per beat |
|------------|----------------------------------|-----------------|
| none       | quarter (`4`)                    | 1               |
| `( … )`    | eighth (`8`)                     | 2 (double)      |
| `(( … ))`  | sixteenth (`16`)                 | 4 (quadruple)   |

This mirrors Carnatic underline-grouping, where notes sharing an underline are
sped up to fit a beat. A whole double-tempo section can just be one bracketed
group per line.

#### Gamaka / grace notes

Append `*` to a svara to make it a **grace ("touch") note** — a quick gamaka
ornament that decorates the next note and takes no beat time of its own. It
renders as a LilyPond acciaccatura (a small slashed note) and gets no lyric
syllable:

```
d. p* m.
```

is "Dha (held), just touch Pa, Ma (held)" — `a'2 \acciaccatura g'8 f'2`.

#### Staccato

Append `!` to a svara to mark it **staccato** — played short and detached. It
renders as a LilyPond `\staccato` articulation (dot above the note) and does not
affect the written duration or the lyric syllable:

```
p! p! p! d n p
```

Staccato composes with duration and octave suffixes: `P!.` = staccato half-Pa,
`S'!` = staccato upper-Sa.

#### Section labels

Put a section name in braces on its own line to print a heading in the score —
use it to mark **Pallavi**, **Anupallavi**, and **Charanam**:

```
{Pallavi}
s m s m p n d. s'.; s'.;
...
{Anupallavi}
...
{Charanam}
...
```

The braces line renders as a bold heading above the following stanzas and isn't
treated as svaras.

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

### Ragas not in the list: auto-fetched from Wikipedia

If a song's `ragam` isn't bundled above, the tool fetches its scale from
Wikipedia at runtime. Wikipedia encodes Carnatic scales with a
`{{svaraC|S|R2|G3|...}}` template whose tokens are exactly this project's
variant notation, so the arohana/avarohana parse directly into a raga.

```json
{"title": "Test", "taalam": "adi", "ragam": "Simhendramadhyamam"}
```

just works — it resolves to `R2 G2 M2 P D1 N3`, renders, and is **cached** to
`raga_cache.json` so later runs are offline and instant.

Notes and limits:
- **Bundled ragas always win** — they're reviewed and dodge name collisions
  (Wikipedia's "Todi" is the *Hindustani* raga; the bundled `todi` is Carnatic
  Hanumatodi). Web lookup runs only for names that are neither bundled nor cached.
- Resolution is best-effort: it tries `Name`, `Name (raga)`, `Name (ragam)` and
  requires a Carnatic `svaraC` scale. If only a Hindustani (`svaraH`) or
  plain-text scale exists, it reports a clear error — add the raga by hand instead.
- Set `RAGA_OFFLINE=1` to disable all network access (the cache is still used).
- Network/parse code lives in `raga_source.py` and is imported lazily, so bundled
  songs never touch the network.

## Taalas (Time Signatures)

| Taala         | Time signature |
|---------------|----------------|
| `adi`         | 4/4            |
| `rupakam`     | 6/4            |
| `eka_thisra`  | 3/4            |
| `misra_chapu` | 7/8            |
| `khanda_chapu`| 5/8            |

## Included Songs

| File                        | Raga            | Taala      |
|-----------------------------|-----------------|------------|
| `vande_meenakshi.txt`       | Sankarabharanam | Adi        |
| `kamalasana.txt`            | Sankarabharanam | Adi        |
| `syamale_meenakshi.txt`     | Sankarabharanam | Adi        |
| `rama_janardhana.txt`       | Sankarabharanam | Eka Thisra |
| `vara_veena.txt`            | Mohanam         | Rupakam    |
| `sri_gananadam.txt`         | Malahari        | Rupakam    |
| `raminchuvarevarura.txt`    | Suposhini       | Rupakam    |
| `sara_sara_samaraika.txt`   | Kuntalavarali   | Adi        |

## MIDI

Every song generates a `.midi` file alongside the PDF. By default it contains only the main melody. Two optional accompaniment tracks can be enabled per song in the header:

- **Lehra** (`"lehra": true`) — a repeating melodic cycle in the raga, played on violin, covering the full song duration. One-cycle patterns are defined for all bundled ragas; unknown ragas use the ascending arohana as a fallback.

- **Tabla** (`"tabla": true`) — a percussion track on General MIDI channel 10 (bongos approximate dayan/bayan). Theka patterns are defined for all supported taalas.

Example header enabling both:

```json
{"title": "My Song", "ragam": "Mohanam", "taalam": "rupakam", "tempo": 120, "lehra": true, "tabla": true}
```

## Adding a New Song

1. Create `songs/my_song.txt`
2. Set the JSON header (title, ragam, taalam)
3. Write svaras line by line using the notation above
4. Run `bash make_song.sh ./songs/my_song.txt`

## Adding a New Raga

First try just naming it in a song header — if it's on Wikipedia as a Carnatic
raga, it's [fetched automatically](#ragas-not-in-the-list-auto-fetched-from-wikipedia).

To bundle it permanently (recommended for ragas you use often, or to override a
bad/ambiguous Wikipedia entry), add **one line** to `RAGA_DEFINITIONS` in
`raga_map.py` listing which variant of each svara the raga uses. You never touch
pitches or octaves — those are derived.

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
