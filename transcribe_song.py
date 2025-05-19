
import sys
import raga_map
import json

def translate_string(parts, raag):
	gen = []
	for p in parts:
		if p.endswith('.'):
			count = 2
		else:
			count = 4

		gen.append(raag[p.replace('.', '')] + str(count))

	return ' '.join(gen)




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



def main(args):
	file = open(args[0], 'r')
	outfile = open(args[1], 'w')
	header = json.loads(file.readline())
	
	outfile.write("""
\header {
  title = "%s"
  subtitle = "Raagam: %s"
  subsubtitle = "Taalam: %s"
}\n
 	""" % (header['title'], header['ragam'], header['taalam']))
	
	raag = raga_map.RAGA_MAP[header['ragam'].lower()]
	print(raag)
	timesignature = raga_map.TAALAM_MAP[header['taalam'].lower()]

	for line in file:
		if (len(line) < 10):
			continue
		if (line.startswith("{")):
			continue
		stanza = make_stanza(line.rstrip().split(" "), raag, timesignature)
		outfile.write(stanza)
	
	outfile.close()

if __name__ == "__main__":
	main(sys.argv[1:])