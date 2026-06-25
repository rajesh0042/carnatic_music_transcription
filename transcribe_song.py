
import sys
import unicodedata
import raga_map
import json

_SVARA_BASES = set("SRGMPDN")


def _is_svara_start(ch):
	"""True if `ch` begins a new svara (a base letter S R G M P D N, including
	the precomposed octave-diacritic forms like Ṡ or Ṇ)."""
	return unicodedata.normalize("NFD", ch)[0].upper() in _SVARA_BASES


def tokenize(text):
	"""Split a svara line into units: '(' , ')' , or one svara token.

	Svaras may be space-separated or written contiguously, so 'SNDP', 'S N D P'
	and '(SNDP)' all tokenize sensibly. Octave/duration marks ('  ,  .  ;) and
	combining diacritics attach to the svara they follow; whitespace is optional
	and never affects tempo (only ( ) brackets do)."""
	units, cur = [], ""
	for ch in text:
		if ch.isspace():
			if cur:
				units.append(cur); cur = ""
		elif ch in "()":
			if cur:
				units.append(cur); cur = ""
			units.append(ch)
		elif _is_svara_start(ch):
			if cur:
				units.append(cur)
			cur = ch
		elif cur:
			cur += ch                     # octave/duration/combining mark
		elif units and units[-1] not in "()":
			units[-1] += ch               # standalone mark extends previous svara
		else:
			cur += ch                     # leading stray mark -> surfaces as error
	if cur:
		units.append(cur)
	return units

# Duration suffix on a svara token -> LilyPond base note value (at normal speed).
#   none -> quarter, '.' -> half, '.;' -> whole, '..' -> dotted half (tie)
# LilyPond durations are inverse, so doubling the tempo doubles these numbers
# (4 -> 8 eighths, 8 -> 16 sixteenths), which composes cleanly with `speed`.
DURATIONS = {'': 4, '.': 2, '.;': 1}


def translate_note(token, raag, speed=1):
	"""Translate one svara token to a LilyPond note. `speed` halves note values
	(2 = double tempo/eighths, 4 = quadruple/sixteenths). A '*' marks a grace
	(gamaka "touch") note, rendered as an acciaccatura that ornaments the next
	note and takes no beat time."""
	grace = '*' in token
	token = token.replace('*', '')
	svara = token.rstrip('.;')
	suffix = token[len(svara):]
	pitch = raga_map.to_lilypond(svara, raag)
	if grace:
		return f"\\acciaccatura {pitch}8"
	if suffix == '..':
		return f"{pitch}{2 * speed}~ {pitch}{4 * speed}"
	return f"{pitch}{DURATIONS[suffix] * speed}"


def translate_units(units, raag):
	"""Translate tokenized units to LilyPond, honoring ( ) speed brackets: each
	'(' doubles the tempo for the svaras it encloses, ')' restores it (nest for
	4x)."""
	out = []
	speed = 1
	for unit in units:
		if unit == "(":
			speed *= 2
		elif unit == ")":
			speed //= 2
		else:
			out.append(translate_note(unit, raag, speed))
	return ' '.join(out)


def section_heading(label):
	"""A standalone LilyPond heading, e.g. for Pallavi / Anupallavi / Charanam."""
	return '\n\\markup \\vspace #0.5\n\\markup \\bold \\large "%s"\n' % label


def make_stanza(line, raag, timesignature):
	units = tokenize(line)
	notes = [u for u in units if u not in "()"]
	comment = " ".join(notes)                              # show every svara
	lyrics = " ".join(raga_map.to_display_svara(u) for u in notes if '*' not in u)    # grace notes get no syllable
	translated = translate_units(units, raag)
	output = """
%%%% %s
{
	\\time %s
	%s
}
\\addlyrics { 
%s
}
	""" % (comment, timesignature, translated, lyrics)
	return output



def lookup_taalam(name):
	try:
		return raga_map.TAALAM_MAP[name.lower()]
	except KeyError:
		raise SystemExit(
			f"unknown taalam '{name}'. Available: "
			f"{', '.join(sorted(raga_map.TAALAM_MAP))}"
		)


def lookup_ragam(name):
	# Bundled ragas first, then the local cache / Wikipedia (see raga_source).
	try:
		return raga_map.get_raga(name)
	except LookupError as exc:
		raise SystemExit(
			f"unknown ragam '{name}': {exc}\nBundled ragas: "
			f"{', '.join(sorted(raga_map.RAGA_MAP))}"
		)


def main(args):
	with open(args[0], 'r') as file:
		header = json.loads(file.readline())
		raag = lookup_ragam(header['ragam'])
		timesignature = lookup_taalam(header['taalam'])
		lines = file.readlines()

	all_notes = []
	with open(args[1], 'w') as outfile:
		outfile.write(r"""
\version "2.24.0"
\header {
  title = "%s"
  subtitle = "Raagam: %s"
  subsubtitle = "Taalam: %s"
}
""" % (header['title'], header['ragam'], header['taalam']))

		for line in lines:
			stripped = line.strip()
			# A "{Section Name}" line becomes a heading (Pallavi, Anupallavi, ...).
			if stripped.startswith("{") and stripped.endswith("}"):
				label = stripped[1:-1].strip()
				if label:
					outfile.write(section_heading(label))
				continue
			if len(line) < 10:
				continue
			outfile.write(make_stanza(stripped.upper(), raag, timesignature))
			all_notes.append(translate_units(tokenize(stripped.upper()), raag))

		# Single MIDI score combining all stanzas in sequence (no visual layout).
		if all_notes:
			outfile.write("""
\\score {
  {
    \\time %s
    %s
  }
  \\midi { \\tempo 4 = 80 }
}
""" % (timesignature, '\n    '.join(all_notes)))


if __name__ == "__main__":
	main(sys.argv[1:])