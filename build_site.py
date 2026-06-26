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
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, system-ui, "Segoe UI", sans-serif;
         max-width: 900px; margin: 2.5rem auto; padding: 0 1.5rem; line-height: 1.5; }
  h1 { margin-bottom: .2rem; font-size: 1.8rem; }
  p.sub { color: #888; margin-top: 0; font-size: .9rem; }
  table { border-collapse: collapse; width: 100%; margin-top: 1.5rem; }
  th, td { text-align: left; padding: .55rem .75rem; border-bottom: 1px solid #8883; vertical-align: middle; }
  th { font-size: .7rem; text-transform: uppercase; letter-spacing: .06em; color: #999; }
  td a { text-decoration: none; font-weight: 600; }
  td a:hover { text-decoration: underline; }
  td.muted a { font-weight: 400; color: #888; }
  td.player { width: 200px; padding: 4px 6px; }
  midi-player { --player-button-size: 1.4em; display: block; border-radius: 999px; }
  @media (prefers-color-scheme: dark) {
    midi-player { filter: invert(1) hue-rotate(180deg); }
  }
  .controls { display: flex; align-items: center; gap: .75rem; margin-top: 1rem; }
  .controls label { font-size: .85rem; color: #777; white-space: nowrap; }
  .controls input[type=range] { width: 160px; accent-color: #7c7; }
  .controls .bpm-val { font-weight: 700; min-width: 2.2em; display: inline-block; }
</style>
</head>
<body>
<h1>Carnatic Transcriptions</h1>
<p class="sub">%%COUNT%% songs &middot; svara notation &rarr; Western sheet music</p>
<div class="controls">
  <label for="bpm-slider">Tempo: <span class="bpm-val" id="bpm-val">80</span> BPM</label>
  <input type="range" id="bpm-slider" min="20" max="300" value="80" step="5">
</div>
<script>
  const slider = document.getElementById('bpm-slider');
  const bpmVal = document.getElementById('bpm-val');

  function applyBpm(bpm) {
    bpmVal.textContent = bpm;
    if (window.Tone?.Transport) {
      Tone.Transport.bpm.value = bpm;
    }
    // Each player uses its own encoded tempo as the base so the slider sets
    // an absolute BPM regardless of what tempo is baked into the MIDI file.
    document.querySelectorAll('midi-player').forEach(p => {
      const baseBpm = +(p.dataset.baseBpm || 80);
      p.playbackRate = bpm / baseBpm;
    });
  }

  slider.addEventListener('input', () => applyBpm(+slider.value));

  document.addEventListener('load', () => {
    document.querySelectorAll('midi-player').forEach(p => {
      p.addEventListener('start', () => applyBpm(+slider.value));
    });
  }, { once: true, capture: true });
</script>
<table>
<thead><tr><th>Song</th><th>Raga</th><th>Tala</th><th>Listen</th><th></th></tr></thead>
<tbody>
%%ROWS%%
</tbody>
</table>
</body>
</html>
"""

ROW = ('<tr><td><a href="pdfs/{stem}.pdf">{title}</a></td>'
       '<td>{raga}</td><td>{tala}</td>'
       '<td class="player"><midi-player src="midi/{stem}.midi" sound-font data-base-bpm="{tempo}"></midi-player></td>'
       '<td class="muted"><a href="pdfs/{stem}.pdf">PDF &rarr;</a></td></tr>')


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
