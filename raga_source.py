"""Fetch Carnatic raga scale definitions from Wikipedia at runtime.

Wikipedia's Carnatic raga pages encode the scale with a template,
``{{svaraC|S|R2|G3|M2|P|D2|N3|S'}}``, whose tokens are exactly this
project's svara-variant notation (see ``raga_map.SVARA``). We read the
``arohanam`` / ``avarohanam`` infobox fields, take the union of the two
scales, and return a variant list ready for ``raga_map``.

This is a *fallback* source. ``raga_map.RAGA_DEFINITIONS`` stays authoritative
for bundled ragas: it is offline, reviewed, and avoids name collisions (e.g.
the Wikipedia page "Todi" is the *Hindustani* raga, not Carnatic Hanumatodi).
Web lookup runs only for raga names that are neither bundled nor already cached,
and results are cached to ``raga_cache.json`` so repeated runs stay offline.

Set the environment variable ``RAGA_OFFLINE=1`` to disable network access
(the local cache is still consulted).
"""

import json
import os
import pathlib
import re
import urllib.parse
import urllib.request

CACHE_PATH = pathlib.Path(__file__).with_name("raga_cache.json")

_API = "https://en.wikipedia.org/w/api.php"
_USER_AGENT = (
    "carnatic-music-transcription/0.1 "
    "(https://github.com/rajesh0042/carnatic_music_transcription)"
)
_TIMEOUT = 20

# Valid svara-variant tokens (mirrors raga_map.SVARA keys); kept local to avoid
# an import cycle.
_SVARA_KEYS = {
    "S", "R1", "R2", "R3", "G1", "G2", "G3", "M1", "M2",
    "P", "D1", "D2", "D3", "N1", "N2", "N3",
}


def _http_wikitext(page):
    """Return the raw wikitext of a Wikipedia page, or None if it has none."""
    query = urllib.parse.urlencode({
        "action": "parse", "page": page, "prop": "wikitext",
        "format": "json", "formatversion": "2", "redirects": "1",
    })
    req = urllib.request.Request(
        f"{_API}?{query}", headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        data = json.load(resp)
    parse = data.get("parse")
    return parse["wikitext"] if parse else None


def _svaraC_tokens(text):
    """Extract valid svara-variant tokens from any {{svaraC|...}} in `text`."""
    tokens = []
    for body in re.findall(r"\{\{svaraC\|([^}]*)\}\}", text):
        for raw in body.split("|"):
            tok = raw.strip().rstrip("'.,").upper()  # drop octave marks
            if tok in _SVARA_KEYS:
                tokens.append(tok)
    return tokens


def _field_scale(wikitext, field_names):
    """svaraC tokens from the first matching infobox field (e.g. arohanam)."""
    for name in field_names:
        m = re.search(r"\|\s*" + name + r"\s*=\s*(.+)", wikitext)
        if m:
            tokens = _svaraC_tokens(m.group(1))
            if tokens:
                return tokens
    return []


def _parse_scale(wikitext):
    """Parse a raga's variant list (e.g. ['R2','G3','M2','P','D2','N3']).

    Uses the union of arohana and avarohana so asymmetric (vakra) ragas keep
    every svara they touch. Sa is dropped (always re-added downstream); the
    first variant seen for each base svara wins.
    """
    aro = _field_scale(wikitext, ["arohanam", "arohana", "aarohanam"])
    avaro = _field_scale(wikitext, ["avarohanam", "avarohana"])
    if not aro and not avaro:
        # Fallback: inline "...arohana... {{svaraC|...}} ...avarohana... {{svaraC|...}}"
        m = re.search(
            r"[Aa]rohana.{0,40}?\{\{svaraC\|([^}]*)\}\}"
            r".*?[Aa]varohana.{0,40}?\{\{svaraC\|([^}]*)\}\}",
            wikitext, re.S)
        if m:
            aro, avaro = _svaraC_tokens(m.group(0)), []

    variants, seen = [], set()
    for tok in aro + avaro:
        base = tok[0]
        if base == "S" or base in seen:
            continue
        seen.add(base)
        variants.append(tok)
    return variants


def _page_candidates(name):
    """Wikipedia titles to try for a raga name, most specific last."""
    title = name.strip().title()
    return [title, f"{title} (raga)", f"{title} (ragam)"]


def fetch(name):
    """Fetch a raga's variant list from Wikipedia. Raises LookupError on miss."""
    if os.environ.get("RAGA_OFFLINE"):
        raise LookupError(f"RAGA_OFFLINE set; will not fetch '{name}' from the web")
    for page in _page_candidates(name):
        try:
            wikitext = _http_wikitext(page)
        except Exception as exc:                       # network/HTTP error
            raise LookupError(f"could not reach Wikipedia for '{name}': {exc}")
        if wikitext:
            variants = _parse_scale(wikitext)
            if variants:
                return variants
    raise LookupError(
        f"no Carnatic scale found on Wikipedia for '{name}' "
        f"(tried: {', '.join(_page_candidates(name))})")


def _load_cache():
    try:
        return json.loads(CACHE_PATH.read_text())
    except (OSError, ValueError):
        return {}


def _save_cache(cache):
    try:
        CACHE_PATH.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n")
    except OSError:
        pass  # cache is best-effort; never fail a transcription over it


def get(name):
    """Return a raga's variant list, using the cache then the web."""
    key = name.strip().lower()
    cache = _load_cache()
    if key in cache:
        return cache[key]
    variants = fetch(name)         # may raise LookupError
    cache[key] = variants
    _save_cache(cache)
    return variants
