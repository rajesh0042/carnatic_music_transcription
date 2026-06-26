
import sys
import math
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
	staccato = '!' in token
	token = token.replace('*', '').replace('!', '')
	svara = token.rstrip('.;')
	suffix = token[len(svara):]
	pitch = raga_map.to_lilypond(svara, raag)
	if grace:
		return f"\\acciaccatura {pitch}8"
	if suffix == '..':
		result = f"{pitch}{2 * speed}~ {pitch}{4 * speed}"
	else:
		n_wholes = suffix.count(';')           # .;=1, .;;=2, .;;;=3, ...
		if n_wholes:
			result = '~ '.join([f"{pitch}{1 * speed}"] * n_wholes)
		else:
			result = f"{pitch}{DURATIONS[suffix] * speed}"
	if staccato:
		# Insert \staccato after the first note's duration, before any tie (~)
		if '~' in result:
			idx = result.index('~')
			result = result[:idx].rstrip() + '\\staccato~ ' + result[idx + 2:]
		else:
			result += '\\staccato'
	return result


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


def note_beats(suffix, speed=1):
	"""Quarter-note beat count for a note with the given duration suffix and speed."""
	if suffix == '..':
		return 3.0 / speed
	n_wholes = suffix.count(';')           # each ; = one whole note = 4 beats
	if n_wholes:
		return 4.0 * n_wholes / speed
	return 4.0 / (DURATIONS.get(suffix, 4) * speed)


def count_beats(units):
	"""Count total quarter-note beats in a tokenized unit list (grace notes = 0)."""
	total = 0.0
	speed = 1
	for unit in units:
		if unit == '(':
			speed *= 2
		elif unit == ')':
			speed //= 2
		elif '*' not in unit:
			svara = unit.rstrip('.;')
			total += note_beats(unit[len(svara):], speed)
	return total


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
	total_beats = 0.0
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
			units = tokenize(stripped.upper())
			all_notes.append(translate_units(units, raag))
			total_beats += count_beats(units)

		# MIDI score: main melody + optional lehra/tabla tracks.
		if all_notes:
			outfile.write(_midi_score(
				header['ragam'], header['taalam'], raag,
				timesignature, all_notes, total_beats,
				tempo=header.get('tempo', 80),
				lehra=header.get('lehra', False),
				tabla=header.get('tabla', False),
			))


def _build_lehra_voice(raga_name, taala_name, raag, total_beats):
	"""Return a LilyPond fragment for the lehra voice, or None if unavailable."""
	pattern = raga_map.get_lehra_pattern(raga_name, taala_name)
	if pattern is None:
		return None
	try:
		units = tokenize(pattern.upper())
		lehra_beats = count_beats(units)
		if lehra_beats == 0:
			return None
		lehra_ly = translate_units(units, raag)
	except KeyError:
		return None
	n_repeats = max(1, math.ceil(total_beats / lehra_beats))
	return f"\\repeat unfold {n_repeats} {{ {lehra_ly} }}"


def _build_tabla_voice(taala_name, total_beats):
	"""Return a LilyPond drummode fragment for the tabla, or None if unsupported."""
	pattern, cycle_beats = raga_map.get_tabla_pattern(taala_name)
	if pattern is None:
		return None
	n_repeats = max(1, math.ceil(total_beats / cycle_beats))
	return f"\\repeat unfold {n_repeats} {{ {pattern} }}"


def _midi_score(raga_name, taala_name, raag, timesig, all_notes, total_beats, tempo=80, lehra=False, tabla=False):
	song = '\n    '.join(all_notes)
	lehra = _build_lehra_voice(raga_name, taala_name, raag, total_beats) if lehra else None
	tabla = _build_tabla_voice(taala_name, total_beats) if tabla else None

	parts = [f"    \\new Staff {{\n      \\time {timesig}\n      {song}\n    }}"]
	if lehra:
		parts.append(
			f'    \\new Staff {{\n'
			f'      \\set Staff.midiInstrument = "violin"\n'
			f'      \\time {timesig}\n'
			f'      {lehra}\n'
			f'    }}'
		)
	if tabla:
		parts.append(
			f'    \\new DrumStaff \\drummode {{\n'
			f'      \\time {timesig}\n'
			f'      {tabla}\n'
			f'    }}'
		)

	if len(parts) > 1:
		inner = '\n'.join(parts)
		return f"\n\\score {{\n  <<\n{inner}\n  >>\n  \\midi {{ \\tempo 4 = {tempo} }}\n}}\n"
	return f"\n\\score {{\n  {{\n    \\time {timesig}\n    {song}\n  }}\n  \\midi {{ \\tempo 4 = {tempo} }}\n}}\n"


if __name__ == "__main__":
	main(sys.argv[1:])