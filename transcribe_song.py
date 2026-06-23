
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



def lookup(table, key, kind):
	"""Look up a raga/taala case-insensitively with a helpful error."""
	try:
		return table[key.lower()]
	except KeyError:
		raise SystemExit(
			f"unknown {kind} '{key}'. Available: {', '.join(sorted(table))}"
		)


def main(args):
	with open(args[0], 'r') as file:
		header = json.loads(file.readline())
		raag = lookup(raga_map.RAGA_MAP, header['ragam'], "ragam")
		timesignature = lookup(raga_map.TAALAM_MAP, header['taalam'], "taalam")
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