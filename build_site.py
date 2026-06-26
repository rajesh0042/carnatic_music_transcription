#!/usr/bin/env python3
"""Build a static website listing every song and linking to its rendered PDF.

For each songs/*.txt this runs the transcriber + LilyPond, drops the PDF in
site/pdfs/, and writes site/index.html. The site is self-contained — open
site/index.html in a browser (or host the site/ folder anywhere static).

    uv run python build_site.py
"""

import html
import json
import subprocess
import sys
from pathlib import Path

import transcribe_song

ROOT = Path(__file__).resolve().parent
SONGS = ROOT / "songs"
SITE = ROOT / "site"
PDFS = SITE / "pdfs"
MIDI = SITE / "midi"
LYDIR = SITE / "_ly"


def read_header(txt_path):
	with open(txt_path, encoding="utf-8") as f:
		return json.loads(f.readline())


def pretty(name):
	"""Tidy a raga/tala name for display: 'eka_thisra' -> 'Eka Thisra'."""
	return name.replace("_", " ").strip().title()


def render(txt_path):
	"""Render one song to PDFS/<name>.pdf + MIDI/<name>.midi."""
	name = txt_path.stem
	ly_path = LYDIR / f"{name}.ly"
	transcribe_song.main([str(txt_path), str(ly_path)])
	proc = subprocess.run(
		["lilypond", "--loglevel=ERROR", "-o", str(PDFS / name), str(ly_path)],
		cwd=LYDIR, capture_output=True, text=True,
	)
	if proc.returncode != 0:
		detail = (proc.stderr or proc.stdout).strip()
		raise RuntimeError(f"lilypond exit {proc.returncode}: {detail[-500:]}")
	midi_src = PDFS / f"{name}.midi"
	if midi_src.exists():
		midi_src.rename(MIDI / f"{name}.midi")
	return name


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Carnatic Transcriptions</title>
<script src="https://cdn.jsdelivr.net/combine/npm/tone@14,npm/@magenta/music@1.23.1/es6/core.js,npm/html-midi-player@1.5.0"></script>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg:     #f2f2f7;
    --card:   #ffffff;
    --border: #d1d1d6;
    --text:   #1c1c1e;
    --muted:  #6c6c70;
    --accent: #5856d6;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg:     #000000;
      --card:   #1c1c1e;
      --border: #38383a;
      --text:   #f2f2f7;
      --muted:  #8e8e93;
      --accent: #7d7aff;
    }
  }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, system-ui, "Segoe UI", Helvetica, sans-serif;
    max-width: 680px;
    margin: 0 auto;
    padding: 2.5rem 1.25rem 5rem;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }
  h1 {
    font-size: 1.55rem;
    font-weight: 700;
    letter-spacing: -.025em;
    margin-bottom: .2rem;
  }
  .sub {
    color: var(--muted);
    font-size: .85rem;
    margin-bottom: 1.5rem;
  }
  .controls {
    display: inline-flex;
    align-items: center;
    gap: .5rem;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: .35rem .9rem;
    font-size: .82rem;
    color: var(--muted);
    margin-bottom: 1.5rem;
  }
  .bpm-val {
    font-weight: 700;
    color: var(--text);
    min-width: 1.8rem;
    display: inline-block;
  }
  input[type=range] {
    width: 110px;
    accent-color: var(--accent);
    cursor: pointer;
  }
  .songs { display: flex; flex-direction: column; gap: .55rem; }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: .9rem 1rem .75rem;
  }
  .card-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: .75rem;
    margin-bottom: .55rem;
  }
  .song-name {
    font-size: .95rem;
    font-weight: 600;
    letter-spacing: -.01em;
  }
  .song-name a { color: var(--text); text-decoration: none; }
  .song-name a:hover { color: var(--accent); }
  .song-detail {
    color: var(--muted);
    font-size: .78rem;
    margin-top: .15rem;
  }
  .pdf-btn {
    flex-shrink: 0;
    font-size: .73rem;
    color: var(--muted);
    text-decoration: none;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: .2rem .5rem;
    white-space: nowrap;
    line-height: 1.6;
  }
  .pdf-btn:hover { color: var(--text); border-color: var(--muted); }
  /* Player always sits on white so it looks consistent in both light and dark modes */
  .player-wrap {
    background: #ffffff;
    border-radius: 999px;
    overflow: hidden;
  }
  midi-player {
    --player-button-size: 1.25em;
    display: block;
  }
</style>
</head>
<body>
<h1>Carnatic Transcriptions</h1>
<p class="sub">%%COUNT%% songs &middot; svara notation &rarr; sheet music</p>
<div class="controls">
  Tempo&thinsp;
  <input type="range" id="bpm-slider" min="20" max="300" value="80" step="5">
  <span class="bpm-val" id="bpm-val">80</span>&thinsp;BPM
</div>
<script>
  const slider = document.getElementById('bpm-slider');
  const bpmVal = document.getElementById('bpm-val');
  function applyBpm(bpm) {
    bpmVal.textContent = bpm;
    if (window.Tone?.Transport) Tone.Transport.bpm.value = bpm;
    document.querySelectorAll('midi-player').forEach(p => {
      p.playbackRate = bpm / +(p.dataset.baseBpm || 80);
    });
  }
  slider.addEventListener('input', () => applyBpm(+slider.value));
  document.addEventListener('load', () => {
    document.querySelectorAll('midi-player').forEach(p =>
      p.addEventListener('start', () => applyBpm(+slider.value))
    );
  }, { once: true, capture: true });
</script>
<div class="songs">
%%ROWS%%
</div>
</body>
</html>
"""

ROW = (
    '<div class="card">'
      '<div class="card-top">'
        '<div>'
          '<div class="song-name"><a href="pdfs/{stem}.pdf">{title}</a></div>'
          '<div class="song-detail">{raga} &middot; {tala}</div>'
        '</div>'
        '<a class="pdf-btn" href="pdfs/{stem}.pdf">PDF&nbsp;&#8599;</a>'
      '</div>'
      '<div class="player-wrap">'
        '<midi-player src="midi/{stem}.midi" sound-font data-base-bpm="{tempo}"></midi-player>'
      '</div>'
    '</div>'
)


def main():
	PDFS.mkdir(parents=True, exist_ok=True)
	MIDI.mkdir(parents=True, exist_ok=True)
	LYDIR.mkdir(parents=True, exist_ok=True)
	rows, failed = [], []
	for txt in sorted(SONGS.glob("*.txt")):
		try:
			header = read_header(txt)
			stem = render(txt)
		except (Exception, SystemExit) as exc:
			failed.append((txt.name, exc))
			continue
		title = header.get("title", txt.stem)
		rows.append((title, ROW.format(
			stem=html.escape(stem),
			title=html.escape(title),
			raga=html.escape(pretty(header.get("ragam", ""))),
			tala=html.escape(pretty(header.get("taalam", ""))),
			tempo=header.get("tempo", 80),
		)))
	rows.sort(key=lambda r: r[0].lower())
	page = (PAGE
		.replace("%%COUNT%%", str(len(rows)))
		.replace("%%ROWS%%", "\n".join(r[1] for r in rows)))
	(SITE / "index.html").write_text(page, encoding="utf-8")
	print(f"Built site/index.html with {len(rows)} song(s) -> {SITE / 'index.html'}")
	for name, exc in failed:
		print(f"  SKIPPED {name}: {exc}", file=sys.stderr)


if __name__ == "__main__":
	main()
