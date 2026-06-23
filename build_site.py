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
LYDIR = SITE / "_ly"


def read_header(txt_path):
	with open(txt_path, encoding="utf-8") as f:
		return json.loads(f.readline())


def pretty(name):
	"""Tidy a raga/tala name for display: 'eka_thisra' -> 'Eka Thisra'."""
	return name.replace("_", " ").strip().title()


def render(txt_path):
	"""Render one song to PDFS/<name>.pdf and return the PDF's file name."""
	name = txt_path.stem
	ly_path = LYDIR / f"{name}.ly"
	transcribe_song.main([str(txt_path), str(ly_path)])
	subprocess.run(
		["lilypond", "--loglevel=ERROR", "-o", str(PDFS / name), str(ly_path)],
		check=True, cwd=LYDIR,
		stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
	)
	return f"{name}.pdf"


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Carnatic Transcriptions</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, system-ui, "Segoe UI", sans-serif;
         max-width: 820px; margin: 2.5rem auto; padding: 0 1rem; line-height: 1.5; }
  h1 { margin-bottom: .25rem; }
  p.sub { color: #888; margin-top: 0; }
  table { border-collapse: collapse; width: 100%; margin-top: 1.5rem; }
  th, td { text-align: left; padding: .6rem .8rem; border-bottom: 1px solid #8884; }
  th { font-size: .75rem; text-transform: uppercase; letter-spacing: .05em; color: #888; }
  td a { text-decoration: none; font-weight: 600; }
  td a:hover { text-decoration: underline; }
  td.muted a { font-weight: 400; color: #888; }
</style>
</head>
<body>
<h1>Carnatic Transcriptions</h1>
<p class="sub">%%COUNT%% songs &middot; svara notation &rarr; Western sheet music</p>
<table>
<thead><tr><th>Song</th><th>Raga</th><th>Tala</th><th></th></tr></thead>
<tbody>
%%ROWS%%
</tbody>
</table>
</body>
</html>
"""

ROW = ('<tr><td><a href="pdfs/{pdf}">{title}</a></td>'
       '<td>{raga}</td><td>{tala}</td>'
       '<td class="muted"><a href="pdfs/{pdf}">PDF &rarr;</a></td></tr>')


def main():
	PDFS.mkdir(parents=True, exist_ok=True)
	LYDIR.mkdir(parents=True, exist_ok=True)
	rows, failed = [], []
	for txt in sorted(SONGS.glob("*.txt")):
		try:
			header = read_header(txt)
			pdf = render(txt)
		except (Exception, SystemExit) as exc:
			failed.append((txt.name, exc))
			continue
		title = header.get("title", txt.stem)
		rows.append((title, ROW.format(
			pdf=html.escape(pdf),
			title=html.escape(title),
			raga=html.escape(pretty(header.get("ragam", ""))),
			tala=html.escape(pretty(header.get("taalam", ""))),
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
