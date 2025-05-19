ALL_NOTES_BASIC = {
	"Ṃ": "f",
	"Pl": "g",
	"Ḍ": "a",
	"Ṇ": "b",
	"S": "c'",
	"R": "d'",
	"G": "e'",
	"M": "f'",
	"P": "g'",
	"D": "a'",
	"N": "b'",
	"Ṡ": "c''", 
	"Ṙ": "d''",
	"Ġ": "e''",
	"Ṁ": "f''",
	"Ṗ": "g''",
}

# MOHANAM: https://en.wikipedia.org/wiki/Mohanam
# ārohaṇa : 
# S R₂ G₃ P D₂ Ṡ
# C D E G A C
# avarohaṇa : 
# Ṡ D₂ P G₃ R₂ S
# C A G E D C
MOHAN_NOTE_MAP = {
	"Pl": "g",
	"Ḍ": "a",
	"S": "c'",
	"R": "d'",
	"G": "e'",
	"P": "g'",
	"D": "a'",
	"Ṡ": "c''", 
	"Ṙ": "d''",
	"Ġ": "e''",
	"Ṗ": "g''",
}

# MALAHARI: https://en.wikipedia.org/wiki/Malahari
# ārohaṇa: 
# S R₁ M₁ P D₁ Ṡ
# C D♭ F G A♭ C
# avarohaṇa: 
# Ṡ D₁ P M₁ G₃ R₁ S
# C A♭ G F E D♭ C
MALAHARI_NOTE_MAP = {
	"Ṃ": "f",
	"Pl": "g",
	"Ḍ": "aes",
	"S": "c'",
	"R": "des'",
	"G": "e'",
	"M": "f'",
	"P": "g'",
	"D": "aes'",
	"N": "b'",
	"Ṡ": "c''", 
	"Ṙ": "des''",
	"Ġ": "e''",
	"Ṁ": "f''",
	"Ṗ": "g''",
}

RAGA_MAP = {
	"mohanam": MOHAN_NOTE_MAP,
	"malahari": MALAHARI_NOTE_MAP,
}

TAALAM_MAP = {
	"rupakam": "6/4"
}
