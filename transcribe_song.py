
import sys
import raga_map
import json

# Duration suffix on a svara token -> LilyPond note length.
#   none -> quarter, '.' -> half, '.;' -> whole, '..' -> dotted half (tie)
DURATIONS = {'': '4', '.': '2', '.;': '1'}


def translate_note(token, raag):
	svara = token.rstrip('.;')
	suffix = token[len(svara):]
	pitch = raga_map.to_lilypond(svara, raag)
	if suffix == '..':
		return f"{pitch}2~ {pitch}4"
	return pitch + DURATIONS[suffix]


def translate_string(parts, raag):
	return ' '.join(translate_note(p, raag) for p in parts)




def make_stanza(notes, raag, timesignature):
	translated = translate_string(notes, raag)
	output = """
%%%% %s
{
	\\time %s
	%s
}
\\addlyrics { 
%s
}
	""" % (" ".join(notes), timesignature, translated, " ".join(notes))
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

	with open(args[1], 'w') as outfile:
		outfile.write(r"""
\version "2.24.4"
\header {
  title = "%s"
  subtitle = "Raagam: %s"
  subsubtitle = "Taalam: %s"
}
""" % (header['title'], header['ragam'], header['taalam']))

		for line in lines:
			if len(line) < 10 or line.startswith("{"):
				continue
			notes = [l.upper() for l in line.rstrip().split(" ")]
			outfile.write(make_stanza(notes, raag, timesignature))


if __name__ == "__main__":
	main(sys.argv[1:])