# Spike: MCM Modern metagame scenarios replayed on ironsmith (T-57, Q3 = B)

Date: 2026-11-10. Status: **harness written, not yet run**. GitHub Actions does not start any
job in the private `szymonrychu/spellslinger-workbench` repository (see "Blocker"), and the
hard constraint for this spike is that ironsmith and MCM execute nowhere else. No pass rates
exist yet; every number below that is not a pass rate comes from reading files.

## Blocker

Every workflow run ever made in this repository (8 runs) has failed within 1 to 3 seconds
with no runner assigned and no steps: the 7 `ci` runs on main and branches since 2026-11-07,
and
run [42920705061](https://github.com/szymonrychu/spellslinger-workbench/actions/runs/42920705061)
of `spike-ironsmith` (all four jobs, including `translate`, which uses only `actions/*`).
Repository Actions permissions are `enabled, allowed_actions: all`, so it is not a policy
block. Public repositories of the same account run normally today (agents-web,
agents-orchestrator); the last private-repository run that actually executed steps was
magic-cards-model-api on 2026-10-14. This pattern (job fails instantly, no runner, no log)
is what GitHub shows when private-repository Actions minutes or the spending limit are
exhausted or a payment failed. The API token available here cannot read billing to
confirm it.

Unblock (one of):

1. Restore private-repository Actions for the account (spending limit or payment), then
   re-run `spike-ironsmith` on PR #2. **Recommended, MVP.** Nothing else changes.
2. Approve running the ironsmith half in a public scratch repository (MCM half stays here
   once minutes return). Not recommended: splits the comparison and still needs (1).

## Method

### Corpus and why

MCM's "Modern metagame scenario tests" are the 23 deck files in
`tests/scenarios/`: `test_*_deck.py` (22) plus `test_deck_45c_aggro.py`. Each registers a
real tournament decklist (pilot, date and source deck id in its docstring, 0.8 to 1.8 percent
of the Modern metagame) and plays it through MCM's real `Match` and `Scenario` paths. 228 test
functions in total. The whole corpus is translated: no subset was needed because most tests
are deck-level and share a small set of shapes.

Test shapes found by reading the files:

| Shape | Examples | Translation |
|---|---|---|
| Card resolution (every name is a real printing) | `test_every_card_in_the_list_is_a_real_printing` | ironsmith `validateMatchConfig` must report no unloadable or unsupported card for the pilot's 75 |
| Start of game (CR 103) | seven in hand, 53 in library, 20 life, sideboard set aside, seeded shuffle, own copies, ownership, first draw skipped | the same deck pair through ironsmith `startMatch` (opening hand 7, seed 1 and 2), asserted on its inspection state |
| Deck construction (CR 100.2a, 100.4a, Modern legality) | `test_the_registered_list_is_sixty_and_fifteen`, four-copy limit tests | untranslatable: they test MCM's `Deck` model; ironsmith's Normal match setup has no constructed-format validator |
| Gameplay (`Scenario()` board plus actions) | Charbelcher kill, Grafdigger's Cage, prowess, Isochron Scepter imprint, storm copies, Allosaurus Rider pitch, Neoform, Summoner's Pact, Leyline of the Guildpact, Territorial Kavu, land play | board extracted by AST; actions and expected outcomes hand-mapped to ironsmith's XMage-port operation language (15 tests) |
| MCM internals | `parse_abilities`, `Casting.total_cost`, `mana_from`, `cost_reduction_for`, rigged opening hands, transient stack contents | untranslatable, reason recorded per test (13 tests listed in `spike/gameplay_map.py`, plus every test no rule matches) |

### ironsmith side

ironsmith has no stable scenario API, but it ships a data-driven scenario runner: its 1,744
ported XMage card tests are JSON operation lists (`addCard`, `castSpell`, `activateAbility`,
`setChoice`, `assertLife`, `assertPermanentCount`, ...) executed by
`scripts/mage-port-runner.mjs` against the WASM engine. Gameplay scenarios are translated
into that language; deck-level checks call the WASM `WasmGame` facade directly
(`spike/ironsmith/spike-lib.mjs`). Engine shims (`MAGE_PORT_ALLOW_ENGINE_SHIMS`) stay off.

The WASM build normally compiles the whole Scryfall corpus into a registry database first.
The spike builds it from a subset `cards.json` holding only the scenario cards
(`spike/cards_subset.py`, Scryfall Oracle Cards bulk file), registered and compiled with
ironsmith's own `sync_registry_db` and `sync_card_status_db`, then `rebuild-wasm.sh
--skip-scryfall-sync`.

### Files

| Path | Role |
|---|---|
| `spike/translate.py` | AST translator: decks from `match()`/`register_deck`, test classification, `Scenario()` boards, emits one ironsmith test module per deck file, `scenarios.json`, `card-names.txt` |
| `spike/gameplay_map.py` | hand-mapped actions and assertions for 15 gameplay tests, reasons for 13 untranslatable ones |
| `spike/ironsmith/spike-lib.mjs` | deck-level check kinds against `WasmGame` |
| `spike/cards_subset.py` | card subset for the ironsmith build |
| `spike/compare.py` | joins MCM and ironsmith JUnit into `results.json` and `results.md` |
| `.github/workflows/spike-ironsmith.yml` | `translate`, `mcm` (pytest on the 23 files), `ironsmith` (build at `0596688`, run), `report` (artifact `spike-results`, also in the job summary) |

Security shape: `permissions: contents: read`, no `secrets.*`, all actions pinned to commit
SHAs, `persist-credentials: false`. MCM is private and a cross-repository checkout needs a
token, so the MCM subset at `8b615e0` (src, test harness, the 23 deck files; 54 MB) was
pushed once to the orphan branch `spike/t57-mcm-snapshot` of this repository and is checked
out from there with the default read-only token. ironsmith is checked out sparse (no
`web/ui/public`, 1.2 GB of UI assets).

## Results

None yet: blocked as above. When the run completes, `spike-results` holds `results.md` with
the per-engine pass rate over the translated set, every disagreement with the ironsmith
failure message, the cards ironsmith refused in the decklists, and the untranslated list.

Known risks to read the first results against:

- Gameplay translations are first drafts that never ran: choice encoding (`setChoice`
  values for may-abilities, pitch costs, searches) and MDFC back-face names (`Jwari Ruins`)
  may need one or two CI iterations before a failure can be blamed on either engine.
- The subset build is a supported path in ironsmith's script but not its default one; the
  first run may need a fix in the workflow (for example a missing sparse-checkout directory).
- MCM's own CI has not been green since 2026-10-04 (20-minute timeouts on the full suite);
  the spike runs only the 23 files, so its MCM numbers are new information too.

## Recommendation for Q3

Unchanged until the run produces data: **A (adopt ironsmith, freeze MCM) stays the
recommendation** on the static evidence in `docs/maturity-comparison.md` (95.5 vs 81.9
percent of the Modern pool on each project's own measurement, a compiler that scales to new
cards, active maintenance). The spike can only overturn it if ironsmith fails a material
share of the translated deck-level checks (cards from these 23 lists it cannot load, or CR
103 start-of-game behaviour), which would point to C. Decision rule proposed for the first
run: adopt (A) if ironsmith passes at least as many translated scenarios as MCM and loads
every card of at least 20 of the 23 lists; otherwise report the gaps and re-ask.
