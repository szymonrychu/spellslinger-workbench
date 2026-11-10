"""Join MCM and ironsmith results for the translated scenarios into results.json and .md.

T-57 spike. Inputs are data only: the translator's scenarios.json and the two JUnit XML
reports (pytest for MCM, `node --test --test-reporter=junit` for ironsmith), plus the
optional JSON-lines detail file the ironsmith deck checks write.

Usage: python compare.py <scenarios.json> <mcm junit> <ironsmith junit> <details.jsonl> <out dir>
"""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

WORST = {"fail": 3, "error": 3, "pass": 1, "skipped": 0}


def outcome(case: ET.Element) -> tuple[str, str]:
    for tag in ("failure", "error"):
        node = case.find(tag)
        if node is not None:
            text = (node.get("message") or "") + "\n" + (node.text or "")
            return "fail", text.strip()
    node = case.find("skipped")
    if node is not None:
        return "skipped", (node.get("message") or "").strip()
    return "pass", ""


def merge(results: dict[str, dict], key: str, status: str, message: str) -> None:
    """Parametrized tests and replays report several cases; the worst one wins."""
    current = results.get(key)
    if current is None or WORST[status] > WORST[current["status"]]:
        results[key] = {"status": status, "message": message[:1500]}


def read_mcm(path: Path) -> dict[str, dict]:
    results: dict[str, dict] = {}
    if not path.is_file():
        return results
    for case in ET.parse(path).iter("testcase"):
        module = (case.get("classname") or "").rsplit(".", 1)[-1]
        name = re.sub(r"\[.*\]$", "", case.get("name") or "")
        status, message = outcome(case)
        merge(results, f"{module}::{name}", status, message)
    return results


def read_ironsmith(path: Path) -> dict[str, dict]:
    results: dict[str, dict] = {}
    if not path.is_file():
        return results
    for case in ET.parse(path).iter("testcase"):
        name = case.get("name") or ""
        if " :: " not in name:
            continue
        source, test = name.split(" :: ", 1)
        status, message = outcome(case)
        merge(results, f"{Path(source).stem}::{test.strip()}", status, message)
    return results


def read_details(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def rate(statuses: list[str]) -> str:
    passed = sum(1 for s in statuses if s == "pass")
    return f"{passed}/{len(statuses)} ({100 * passed / len(statuses):.1f}%)" if statuses else "0/0"


def build(scenarios: dict, mcm: dict, iron: dict, details: list[dict]) -> dict:
    rows = []
    for record in scenarios["records"]:
        key = record["key"]
        row = {
            "key": key,
            "kind": record["kind"],
            "checks": record.get("checks"),
            "partial": record.get("partial"),
            "reason": record.get("reason"),
            "mcm": mcm.get(key, {"status": "missing", "message": ""}),
        }
        if record["kind"] in ("deck", "gameplay"):
            row["ironsmith"] = iron.get(key, {"status": "missing", "message": ""})
        rows.append(row)
    translated = [r for r in rows if "ironsmith" in r]
    issues: dict[str, set[str]] = defaultdict(set)
    for item in details:
        if item.get("kind") == "cards_known":
            for issue in item.get("issues", []):
                issues[issue.get("card_name") or issue.get("cardName") or "?"].add(
                    str(issue.get("error"))[:300]
                )
    return {
        "tests_total": len(rows),
        "by_kind": dict(Counter(r["kind"] for r in rows)),
        "translated": len(translated),
        "mcm_all": rate([r["mcm"]["status"] for r in rows]),
        "mcm_translated": rate([r["mcm"]["status"] for r in translated]),
        "ironsmith_translated": rate([r["ironsmith"]["status"] for r in translated]),
        "agree": sum(1 for r in translated if r["mcm"]["status"] == r["ironsmith"]["status"]),
        "unplayable_cards": {name: sorted(errs) for name, errs in sorted(issues.items())},
        "rows": rows,
    }


def markdown(result: dict) -> str:
    out = [
        "# T-57 spike: MCM Modern metagame scenarios on MCM and ironsmith",
        "",
        f"- MCM tests in the corpus: {result['tests_total']} ({result['by_kind']})",
        f"- MCM pass rate, whole corpus: {result['mcm_all']}",
        f"- Translated scenarios: {result['translated']}",
        f"- MCM pass rate, translated: {result['mcm_translated']}",
        f"- ironsmith pass rate, translated: {result['ironsmith_translated']}",
        f"- Same verdict on both engines: {result['agree']}/{result['translated']}",
        "",
        "## Translated scenarios",
        "",
        "| Scenario | Kind | MCM | ironsmith |",
        "|---|---|---|---|",
    ]
    for row in result["rows"]:
        if "ironsmith" not in row:
            continue
        kind = row["kind"] + (f" ({', '.join(row['checks'])})" if row.get("checks") else "")
        if row.get("partial"):
            kind += " (partial)"
        out.append(
            f"| `{row['key']}` | {kind} | {row['mcm']['status']} | {row['ironsmith']['status']} |"
        )
    out += ["", "## Disagreements", ""]
    for row in result["rows"]:
        if "ironsmith" in row and row["mcm"]["status"] != row["ironsmith"]["status"]:
            message = (row["ironsmith"]["message"] or row["mcm"]["message"]).splitlines()
            first = " ".join(message[:3])[:400].replace("|", "/")
            out.append(
                f"- `{row['key']}`: MCM {row['mcm']['status']}, ironsmith "
                f"{row['ironsmith']['status']}: {first}"
            )
    out += ["", "## Cards ironsmith refused in the decklists", ""]
    for name, errors in result["unplayable_cards"].items():
        out.append(f"- {name}: {'; '.join(errors)[:300]}")
    out += ["", "## Not translated", ""]
    for row in result["rows"]:
        if row["kind"] == "untranslatable":
            out.append(f"- `{row['key']}` (MCM {row['mcm']['status']}): {row['reason']}")
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 6:
        print(__doc__, file=sys.stderr)
        return 2
    scenarios = json.loads(Path(argv[1]).read_text())
    result = build(
        scenarios,
        read_mcm(Path(argv[2])),
        read_ironsmith(Path(argv[3])),
        read_details(Path(argv[4])),
    )
    out = Path(argv[5])
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    (out / "results.md").write_text(markdown(result))
    print(markdown(result).split("## Translated")[0])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
