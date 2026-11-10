"""Translate magic-cards-model (MCM) Modern metagame deck scenarios into ironsmith scenarios.

T-57 spike. Reads the MCM test sources as data (Python `ast`, nothing is imported or run)
and writes, for each of the 23 Modern metagame deck files under `tests/scenarios/`:

- one ironsmith test module (`<out>/ironsmith/<file stem>.test.mjs`) that the spike workflow
  copies into `scripts/spike-t57/` of an ironsmith checkout. Deck-level checks run through
  `spike-lib.mjs` (ironsmith's WASM `WasmGame`), gameplay scenarios through ironsmith's own
  XMage-port scenario runner (`registerPortedMageTests`, a JSON operation list);
- `<out>/scenarios.json`: every MCM test, how it was translated, or why it was not;
- `<out>/card-names.txt`: every card name the translated scenarios use (for the card subset).

Usage: python translate.py <mcm checkout> <out dir>
"""

from __future__ import annotations

import ast
import json
import re
import sys
from collections import Counter
from pathlib import Path

from gameplay_map import GAMEPLAY, UNTRANSLATABLE

DECK_GLOBS = ("tests/scenarios/*_deck.py", "tests/scenarios/test_deck_45c_aggro.py")

# Deck-level checks: MCM test name keywords -> canonical check kinds. First match wins, so
# the more specific rules come first. Every kind is implemented in spike-lib.mjs.
NAME_RULES: list[tuple[str, list[str]]] = [
    (
        r"engines_own_legality|construction|legal|sixty_and_fifteen|seventy_five|copy_limit"
        r"|four_copy|exceeds|more_than_four|basics_are|basic_land|six_forests|sideboard_is_fifteen"
        r"|split_counts",
        ["deck_construction"],
    ),
    (r"registering_the_deck", ["cards_known"]),
    (r"real_printing", ["cards_known"]),
    (r"skips_(the|their)_first_draw", ["first_draw_skipped"]),
    (r"own_card|separate_cards|own_physical_copies", ["distinct_objects"]),
    (r"owned_by_the_player", ["ownership"]),
    (r"both_seats|opponent_(is_dealt|draws)|both_players_are_dealt", ["opening_hand_both"]),
    (
        r"card_for_card|whole_sixty|sixty_dealt|dealt_card|card_dealt|came_from_this|comes_from_this"
        r"|from_this_deck|from_this_decklist|off_this_list|nothing_else|opening_seven_are"
        r"|mainboard_copy_of_a_sideboard",
        ["dealt_is_registered"],
    ),
    (r"sideboard|library_holds_only_mainboard", ["sideboard_aside"]),
    (r"twenty|life_totals", ["starting_life"]),
    (r"shuffl|seed|list_order|same_hand|deal_differently", ["shuffle"]),
    (r"seven|fifty_three|library_is_the|starting_hand_size|deals_seven", ["opening_hand"]),
]

UNTRANSLATABLE_KINDS = {
    "deck_construction": (
        "asserts the decklist against MCM's own Deck model (60/15 sizes, four-copy limit, "
        "Modern legality via Deck.problems/is_legal); ironsmith's Normal match setup has no "
        "constructed-format validator to compare against"
    ),
}


def literal_cards(node: ast.AST, consts: dict[str, ast.AST]) -> list[str] | None:
    """A list of card names from a list literal, `*[..] * n` and `[..] * n` included."""
    if isinstance(node, ast.Name) and node.id in consts:
        return literal_cards(consts[node.id], consts)
    if isinstance(node, ast.List | ast.Tuple):
        out: list[str] = []
        for elt in node.elts:
            if isinstance(elt, ast.Starred):
                inner = literal_cards(elt.value, consts)
                if inner is None:
                    return None
                out.extend(inner)
            elif isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                out.append(elt.value)
            else:
                return None
        return out
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        left = literal_cards(node.left, consts)
        if left is not None and isinstance(node.right, ast.Constant):
            return left * int(node.right.value)
    return None


def deck_dict(node: ast.AST, consts: dict[str, ast.AST]) -> dict[str, int] | None:
    """Resolve a mainboard/sideboard expression to {name: count}."""
    if isinstance(node, ast.Name) and node.id in consts:
        return deck_dict(consts[node.id], consts)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
        if len(node.args) == 1 and not node.keywords:
            return deck_dict(node.args[0], consts)
    if isinstance(node, ast.Dict):
        out: dict[str, int] = {}
        for key, value in zip(node.keys, node.values, strict=True):
            if key is None:
                inner = deck_dict(value, consts)
                if inner is None:
                    return None
                out.update(inner)
            elif isinstance(key, ast.Constant) and isinstance(value, ast.Constant):
                out[str(key.value)] = int(value.value)
            else:
                return None
        return out
    return None


class DeckFile:
    """One MCM deck scenario file, parsed."""

    def __init__(self, path: Path, rel: str) -> None:
        self.rel = rel
        self.stem = path.stem
        self.source = path.read_text(encoding="utf-8")
        self.tree = ast.parse(self.source)
        self.consts: dict[str, ast.AST] = {}
        self.funcs: dict[str, ast.FunctionDef] = {}
        for node in self.tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    self.consts[target.id] = node.value
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.value is not None:
                    self.consts[node.target.id] = node.value
            elif isinstance(node, ast.FunctionDef):
                self.funcs[node.name] = node

    # -- decks ---------------------------------------------------------------------------

    def deck_from_expr(self, node: ast.AST) -> dict | None:
        """A `Deck(...)` expression, or a call to a local function returning one."""
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "Deck":
                kw = {k.arg: k.value for k in node.keywords}
                main = deck_dict(kw["mainboard"], self.consts) if "mainboard" in kw else None
                if main is None:
                    return None
                side = deck_dict(kw["sideboard"], self.consts) if "sideboard" in kw else {}
                if side is None:
                    return None
                return {"main": main, "side": side}
            func = self.funcs.get(node.func.id)
            if func is not None:
                for stmt in ast.walk(func):
                    if isinstance(stmt, ast.Return) and stmt.value is not None:
                        return self.deck_from_expr(stmt.value)
        return None

    def registered_decks(self) -> list[dict] | None:
        """[pilot deck, opponent deck] from the `register_deck` calls of `match()`."""
        decks: list[dict] = []
        scope = self.funcs.get("match")
        if scope is None:
            return None
        for node in ast.walk(scope):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "register_deck"
                and len(node.args) == 2
            ):
                deck = self.deck_from_expr(node.args[1])
                if deck is None:
                    return None
                decks.append(deck)
        return decks if len(decks) == 2 else None

    def fallback_deck(self) -> dict | None:
        """The pilot deck from the first module-level function returning a Deck."""
        for func in self.funcs.values():
            if func.name.startswith("test_"):
                continue
            for stmt in ast.walk(func):
                if isinstance(stmt, ast.Return) and stmt.value is not None:
                    deck = self.deck_from_expr(stmt.value)
                    if deck is not None:
                        return deck
        return None

    # -- scenarios -----------------------------------------------------------------------

    def scenario_setup(self, func: ast.FunctionDef) -> dict[str, dict[str, list[str]]] | None:
        """Zones per player from the `Scenario().player(...)...` chain in a test (or the
        local helper it calls)."""
        chain = self._find_scenario_chain(func)
        if chain is None:
            return None
        players: dict[str, dict[str, list[str]]] = {}
        node = chain
        calls: list[ast.Call] = []
        while isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            calls.append(node)
            node = node.func.value
        for call in reversed(calls):
            if call.func.attr != "player":
                continue
            name = call.args[0].value if call.args else None
            zones: dict[str, list[str]] = {}
            for kw in call.keywords:
                cards = literal_cards(kw.value, self.consts)
                if cards is None:
                    return None
                zones[kw.arg] = cards
            players[name] = zones
        return players

    def _find_scenario_chain(self, func: ast.FunctionDef) -> ast.Call | None:
        for node in ast.walk(func):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                inner = node
                while isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute):
                    inner = inner.func.value
                if isinstance(inner, ast.Call) and getattr(inner.func, "id", "") == "Scenario":
                    return node
        for node in ast.walk(func):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                helper = self.funcs.get(node.func.id)
                if helper is not None and helper is not func:
                    found = self._find_scenario_chain(helper)
                    if found is not None:
                        return found
        return None

    def tests(self) -> list[ast.FunctionDef]:
        return [f for f in self.funcs.values() if f.name.startswith("test_")]


def expand(deck: dict[str, int]) -> list[str]:
    return [name for name, count in deck.items() for _ in range(count)]


def classify_deck_test(func: ast.FunctionDef) -> list[str] | None:
    name = func.name
    for pattern, kinds in NAME_RULES:
        if re.search(pattern, name):
            return kinds
    return None


def setup_ops(setup: dict[str, dict[str, list[str]]]) -> list[dict]:
    """Scenario zones -> mage-port `addCard` operations. Alice is player 0, Bob player 1.

    MCM lists a library top card first; the mage runner stacks library additions with the
    last one on top, so library cards are added in reverse after clearing the default
    library of 71 Mountains."""
    ops: list[dict] = []
    order = list(setup)
    for player_name, zones in setup.items():
        player = 0 if player_name in ("alice", order[0]) else 1
        for zone, cards in zones.items():
            if zone == "library":
                ops.append({"op": "clearZone", "player": player, "zone": "library"})
                cards = list(reversed(cards))
            for name, count in _runs(cards):
                ops.append(
                    {
                        "op": "addCard",
                        "zone": zone.upper(),
                        "player": player,
                        "name": name,
                        "count": count,
                    }
                )
    return ops


def _runs(cards: list[str]) -> list[tuple[str, int]]:
    runs: list[tuple[str, int]] = []
    for name in cards:
        if runs and runs[-1][0] == name:
            runs[-1] = (name, runs[-1][1] + 1)
        else:
            runs.append((name, 1))
    return runs


def translate(mcm: Path, out: Path) -> dict:
    files: list[Path] = []
    for pattern in DECK_GLOBS:
        files.extend(sorted(mcm.glob(pattern)))
    (out / "ironsmith").mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    names: set[str] = {"Mountain", "Island", "Plains", "Swamp", "Forest"}
    for path in files:
        rel = path.relative_to(mcm).as_posix()
        deck_file = DeckFile(path, rel)
        decks = deck_file.registered_decks()
        if decks is None:
            pilot = deck_file.fallback_deck()
            decks = [pilot, pilot] if pilot is not None else None
        deck_checks: list[dict] = []
        mage_tests: list[dict] = []
        for func in deck_file.tests():
            key = f"{deck_file.stem}::{func.name}"
            parametrized = any("parametrize" in ast.unparse(d) for d in func.decorator_list)
            record = {
                "key": key,
                "file": rel,
                "test": func.name,
                "parametrized": parametrized,
            }
            if key in GAMEPLAY:
                spec = GAMEPLAY[key]
                setup = deck_file.scenario_setup(func)
                if setup is None:
                    record.update(kind="untranslatable", reason="scenario setup not resolvable")
                else:
                    ops = setup_ops(setup) + spec["ops"]
                    mage_tests.append({"name": func.name, "operations": ops})
                    for zones in setup.values():
                        for cards in zones.values():
                            names.update(cards)
                    names.update(spec.get("names", []))
                    record.update(
                        kind="gameplay",
                        partial=spec.get("partial"),
                        operations=ops,
                    )
            elif key in UNTRANSLATABLE:
                record.update(kind="untranslatable", reason=UNTRANSLATABLE[key])
            else:
                kinds = classify_deck_test(func)
                if kinds is None:
                    record.update(
                        kind="untranslatable",
                        reason="no rule for this test: card-specific assertion on MCM internals",
                    )
                elif kinds[0] in UNTRANSLATABLE_KINDS:
                    record.update(kind="untranslatable", reason=UNTRANSLATABLE_KINDS[kinds[0]])
                elif decks is None:
                    record.update(kind="untranslatable", reason="decklist not resolvable by AST")
                else:
                    deck_checks.append({"name": func.name, "kinds": kinds})
                    record.update(kind="deck", checks=kinds)
            records.append(record)
        if decks is not None:
            for deck in decks:
                names.update(deck["main"])
                names.update(deck["side"])
        write_module(out, deck_file, decks, deck_checks, mage_tests)
    summary = Counter(r["kind"] for r in records)
    result = {
        "files": len(files),
        "tests": len(records),
        "by_kind": dict(summary),
        "records": records,
    }
    (out / "scenarios.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (out / "card-names.txt").write_text("".join(f"{n}\n" for n in sorted(names)), encoding="utf-8")
    return result


def write_module(
    out: Path,
    deck_file: DeckFile,
    decks: list[dict] | None,
    deck_checks: list[dict],
    mage_tests: list[dict],
) -> None:
    lines = [
        f"// Generated by spike/translate.py from magic-cards-model {deck_file.rel}. Do not edit.",
        'import { registerPortedMageTests } from "../mage-port-runner.mjs";',
        'import { registerDeckChecks } from "./spike-lib.mjs";',
        "",
    ]
    if deck_checks and decks is not None:
        spec = {
            "sourcePath": deck_file.rel,
            "decks": [{"main": expand(d["main"]), "side": expand(d["side"])} for d in decks],
            "checks": deck_checks,
        }
        lines.append(f"registerDeckChecks({json.dumps(spec)});")
    if mage_tests:
        spec = {"sourcePath": deck_file.rel, "tests": mage_tests}
        lines.append(f"registerPortedMageTests({json.dumps(spec, indent=1)});")
    (out / "ironsmith" / f"{deck_file.stem}.test.mjs").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    result = translate(Path(argv[1]), Path(argv[2]))
    print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
