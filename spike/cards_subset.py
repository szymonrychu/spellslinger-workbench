"""Write an ironsmith cards.json holding only the cards the translated scenarios use.

T-57 spike. ironsmith's WASM build compiles and bakes every card in its cards.json (by
default the whole Scryfall Default Cards file, tens of thousands of cards). The spike only
needs the few hundred cards of the 23 MCM Modern metagame decks, so it downloads Scryfall's
Oracle Cards bulk file (one object per card, same schema) and keeps those names.

Usage: python cards_subset.py <card-names.txt> <out cards.json> [<bulk file>]
Writes <out>.missing.txt with names that matched nothing.
"""

from __future__ import annotations

import gzip
import json
import sys
import urllib.request
from pathlib import Path

BULK_INDEX = "https://api.scryfall.com/bulk-data/oracle-cards"
HEADERS = {"User-Agent": "spellslinger-workbench-spike/1.0", "Accept": "application/json"}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=600) as response:
        return response.read()


def load_bulk(path: Path | None) -> list[dict]:
    if path is not None:
        raw = path.read_bytes()
    else:
        index = json.loads(fetch(BULK_INDEX))
        raw = fetch(index["download_uri"])
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    text = raw.decode("utf-8").lstrip()
    if text.startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def names_of(card: dict) -> list[str]:
    names = [card["name"]]
    names.extend(face["name"] for face in card.get("card_faces") or [] if face.get("name"))
    return names


def rank(card: dict) -> tuple:
    """Prefer paper, non-digital, non-Alchemy printings."""
    return (
        "paper" in (card.get("games") or []),
        not card.get("digital", False),
        card.get("set_type") != "alchemy",
    )


def subset(wanted: set[str], cards: list[dict]) -> tuple[list[dict], set[str]]:
    by_name: dict[str, dict] = {}
    for card in cards:
        for name in names_of(card):
            current = by_name.get(name)
            if current is None or rank(card) > rank(current):
                by_name[name] = card
    chosen: dict[str, dict] = {}
    missing: set[str] = set()
    for name in sorted(wanted):
        card = by_name.get(name)
        if card is None:
            missing.add(name)
        else:
            chosen[card["id"]] = card
    return list(chosen.values()), missing


def main(argv: list[str]) -> int:
    if len(argv) not in (3, 4):
        print(__doc__, file=sys.stderr)
        return 2
    wanted = {line.strip() for line in Path(argv[1]).read_text().splitlines() if line.strip()}
    cards = load_bulk(Path(argv[3]) if len(argv) == 4 else None)
    chosen, missing = subset(wanted, cards)
    out = Path(argv[2])
    out.write_text(json.dumps(chosen), encoding="utf-8")
    Path(f"{out}.missing.txt").write_text("".join(f"{n}\n" for n in sorted(missing)))
    print(f"wanted {len(wanted)} names, wrote {len(chosen)} cards, {len(missing)} missing")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
