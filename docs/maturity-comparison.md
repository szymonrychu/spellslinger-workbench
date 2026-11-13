# Rules engine maturity: ironsmith vs magic-cards-model vs spellslinger

Date: 2026-11-10 (T-57 phase 2). Static analysis only: files, git history, committed measurement artifacts and
`gh` metadata were read; no code from any of the three was built, installed, tested or run. Helper scripts that
only read files: `.scratchpad/spellslinger/tools/` in the tatara workbench (`mcm_coverage.py`,
`iron_coverage.py`); their outputs are in `.logs/spellslinger/t57p2-*`.

Revisions compared:

| Project | Repo | Revision |
|---|---|---|
| ironsmith | github.com/Chiplis/ironsmith (third party, public) | pinned `0596688` (2026-11-06); upstream main is 7 commits ahead |
| magic-cards-model (MCM) | github.com/szymonrychu/magic-cards-model (private) | `8b615e0` (main, 2026-10-14) |
| spellslinger | 17 `szymonrychu/spellslinger-*` repos | submodule pins of this workbench |

## 0. Where the rules logic lives on our side

**No spellslinger repo holds a rules engine.** The spellslinger services are Go data and analysis services:
cards (Scryfall card DB), knowledge (Comprehensive Rules text, rulings, wiki, embeddings), statistics (tournament
scraping), synergy-api (heuristic synergy tags, deck evaluation, manabase maths, card-interaction lookups), reveries,
llm-queue, identity, and `sscli` (CLI plus the MCP server). None models a game state, stack, priority or card
resolution. The rules engine on our side is **magic-cards-model** (Python, pydantic), the project the user calls
"gargantuan, not manageable, about 80% of Modern". It uses the spellslinger MCP as its rules reference, and its
FastAPI/web/agent wrapper `magic-cards-model-api` runs in namespace `mtg-engine` (sha-tagged image). So the real
comparison is ironsmith vs MCM; spellslinger is the consumer that would call whichever engine wins.

## 1. Headline numbers

| | ironsmith | magic-cards-model |
|---|---|---|
| Language | Rust (engine, compiler) + TypeScript/React UI, shipped as WASM | Python 3.13 + pydantic |
| Card model | Oracle text compiled by a grammar compiler into runtime definitions; 160 hand-written definitions | Oracle text read clause by clause by hand-written parsers and dispatch tables in `machines/` |
| Modern-legal pool coverage, own measurement | 95.5% (21,985 of 23,012) at 2026-10-08; author claims 100% from 2026-10-18 | 81.9% "handled" (18,857 of 23,012), 26.9% scenario-tested (6,180) |
| Whole-corpus coverage, own measurement | 94.0% of 32,138 oracle ids (2026-10-08) | 83.3% of 22,688 baseline cards |
| Source LOC (non-test) | about 1.88M Rust (2.94M total incl. 1.06M in test files) + 141k TS | 335,664 Python in 293 files |
| Test LOC / tests | 31,628 `#[test]` fns, 257 `#[ignore]`; 1,744 ported XMage card tests; 125k-line CR audit test | 527,600 LOC, 23,186 test fns in 1,883 files, 75 xfail mentions |
| CI on main | none runs tests (only an npm publish workflow on tags) | GitHub Actions lint+test; last green 2026-10-04, every run since cancelled at the 20 min timeout |
| Commits / first / last | 4,690 / 2026-02-06 / 2026-11-06 (upstream active today) | 2,930 / 2026-08-30 / 2026-10-14 (dormant 4 weeks) |
| Humans | 1 core (Chiplis, 3,250 commits) + 1 UI contributor (151) + 955 bot and about 300 cloud-agent commits; 885 PRs, 564 merged | 1 (the owner, agent-driven) |
| Licence | `BUSL-1.1 OR AGPL-3.0-or-later` (BSL: non-commercial production only; MIT after 4 years per version) | none (private, all rights reserved) |

## 2. Card coverage

### Method

- **Pool:** Scryfall `oracle-cards` bulk file of 2026-11-10, filtered to `legalities.modern` in (legal, restricted):
  **23,012 oracle ids**. No Modern-legal list exists in any of the repos, so the pool was fetched once from Scryfall
  (a public data file, not code).
- **MCM:** `docs/card_coverage/support-baseline.json` (2026-10-14) is the output of MCM's own sweep
  (`support.card_support`, every card through the real dispatchers) with a per-card verdict `handled`, `notice`
  (fails closed with a notice) or `silent` (text nothing reads). Joined on oracle id. "Tested" comes from the
  per-set `docs/card_coverage/*/status.md` tables (cards with a scenario test).
- **ironsmith:** no per-card source files exist (cards are compiled from Oracle text at build time; the generated
  catalogue is not committed). Two committed full-corpus measurements were used:
  `fixtures/card-failure-campaign/baseline-e8740178.snapshot.json.gz` (2026-10-03, per card, `supported` flag) and
  `reports/card-failure-campaign/refresh-20261008-main1dd81cd/current-unresolved-entries.json.gz` (2026-10-08,
  every unresolved card with oracle id and failure category). Modern support = pool minus unresolved Modern ids.
- README claims were not used as evidence; they are quoted only as claims.

### Results

| Measurement | ironsmith | MCM |
|---|---|---|
| Modern pool supported, own tool | 20,857 / 22,718 matched names = 91.8% (Oct 3); 21,985 / 23,012 = **95.5%** (Oct 8) | **18,857 / 23,012 = 81.9%** (Oct 14; 376 Modern ids are not in the baseline at all) |
| Modern unsupported, by kind | 1,027 (Oct 8): 920 parser failures, 58 lossy, 41 semantic-output failures, 7 permissive fallback, 1 unsupported mechanic, 1 compiler panic | 3,068 silent (does nothing, logs nothing) + 711 notice (refuses, fails closed) |
| Cards with a scenario/gameplay test | not measurable per card (tests are per mechanic family, plus 1,744 ported XMage card tests) | 6,180 tested, 12,787 "works (untested)" (status.md sums) |
| Later claims | commit `72816a2c8` "100% card desired parity reached" (2026-10-18), `aac6c0e98` "0.99 similarity threshold achieved for 32226 card corpus" (2026-10-20), README "every single card legally playable in Legacy/Vintage/Modern/Standard/Pioneer/Commander/Pauper works in-game" | user's estimate "about 80% of Modern" matches the 81.9% above |

### Limits

- Both numbers are each project's **own compile/parse acceptance**, not proof of correct gameplay. ironsmith's
  own packet says so explicitly ("Compile acceptance does not prove gameplay correctness"; its "supported" means
  strict compile plus a rendered-text similarity check against the Oracle text). MCM's "handled" means a dispatcher
  claims every clause; its 6,180 tested cards are the stronger evidence.
- The ironsmith 100% claim (Oct 18-20) has **no committed per-card artifact**; the last committed measurement is
  Oct 8 (95.5% Modern). Rising from about 1,900 unresolved cards to zero in 10 days is plausible given the commit
  rate (990 commits in October) but is unverified here because nothing could be run.
- About 294 Modern names postdate the ironsmith Oct 3 corpus; the Oct 8 number assumes those are supported.

## 3. Rules accuracy evidence

**ironsmith**
- 31,628 Rust `#[test]` functions (257 ignored); per-mechanic fixture sets (`fixtures/*.json.fixture`, 371 files).
- `crates/ironsmith-engine/tests/cr_complete_audit.rs`: a 125,732-line Comprehensive Rules audit test file.
- 1,784 XMage (Java) card tests vendored under `scripts/cards/` with 1,744 JavaScript ports under
  `scripts/ported-mage-tests/` and `run-mage-tests.sh`: an independent, mature oracle (XMage) used as a test source.
- Determinism and multiplayer integrity: replayable transcripts, verified mode with zero-knowledge shuffles
  (README admits no independent security review).
- **CI:** only `publish-npm.yml` (on tag) exists at the pin; 9 workflow runs ever (last 2026-10-01, a failed Pages
  deploy whose workflow file is gone at the pin). Tests are run locally and by agents, not gated in CI. npm `ironsmith-wasm` 0.1.2 is from
  2026-07-24, far behind main.
- **Issues:** 0 issues ever filed (issues are enabled); bug intake is through PRs and internal reports
  (`reports/cards/*.md`, `reports/card-failure-campaign/`).

**MCM**
- 23,186 test functions, all scenario-style on real Scryfall printings (mocks banned by project memory), including
  46 judge-scenario files (`tests/scenarios/judge/`), golden game transcripts, and a behavioural pool sweep.
- `docs/engine-coverage.md` (8,690 lines) keeps an honest "Not modelled" table: battles not modelled, flip cards
  not modelled, cloak missing, copied mana cost absent from the layer engine, several companion conditions unread,
  among others. The engine fails closed on most unread text (notice), but 3,068 Modern cards are still silent no-ops.
- **CI:** 228 runs: 69 success, 99 failure, 60 cancelled. Last success 2026-10-04; every run since 2026-10-03 was
  cancelled at the 20-minute job timeout, so main has had no green CI for the last 10 days of activity.
- **Issues:** 0 issues ever filed.

## 4. Architecture and maintainability

**ironsmith**: 37 crates with a clear pipeline: `card-source` -> `compiler-syntax` / `compiler-grammar` ->
`compiler-resolve` -> `compiler-semantic` -> `compiler-lowering` -> `compiled-artifact` -> `runtime` / `engine`,
plus `card-catalog` (Brotli-chunked embedded catalogue), `verifier*` (ZK), `wasm*` facades, `status-db` (SQLite
measurement), and tools. 5,752 Rust files, average about 510 lines; the largest are the CR audit test and text
renderers (56k-line `ast_render.rs`). The size (about 1.9M non-test Rust lines) is itself a maintainability risk for
anyone but its author and his agents, but the crate boundaries are explicit and documented (`architecture/`).
Notable: the repo carries 48k UI image assets (2.7 GB clone), so it is heavy to vendor.

**MCM**: one Python package, `machines/` (152 files) holding hand-written readers and dispatch tables per
mechanic family; 293 source files averaging 1,146 lines, with several 6k-14k-line modules
(`layers/parse.py` 14,144, `effects/continuous.py` 13,445, `effects/removal.py` 10,392). Card behaviour is spread
across many parsers keyed on text shapes; MEMORY records "silent-default dispatch tables" as the recurring defect
class. Test code is 1.6x the source. Single dependency (pydantic). This matches the user's own assessment: it does
not scale to the remaining 18% without proportionally more parser code.

**spellslinger**: 17 small Go/TS repos (largest about 28k LOC), one chart each, deployed by helmfile; conventional
and maintainable, but with no engine.

## 5. Activity and bus factor

| | ironsmith | MCM | spellslinger |
|---|---|---|---|
| Commits by month (2026) | Feb 633, Mar 371, Apr 415, May 945, Jun 892, Jul 42, Aug 49, Sep 330, Oct 990, Nov 23 (to the 6th) | Aug 320, Sep 1,279, Oct 1,331 | feature work May-Aug; docs-only since 2026-09-21 |
| Last activity | today (upstream main) | 2026-10-14 | 2026-11-10 (two memory-limit fixes) |
| Bus factor | 1 (Chiplis), heavily agent-assisted (card-fixer bot, EC2 agents, Codex co-authorship) | 1 (owner, agent-driven) | 1 |
| Community | 17 stars, 8 forks, 5 PR authors | private | private |

Both engines are effectively single-author, agent-built codebases. ironsmith has been active for 9 months and is
still moving; MCM for 6 weeks and has been idle for 4.

## 6. Licence and whether we can use or merge it

ironsmith is dual-licensed `BUSL-1.1 OR AGPL-3.0-or-later` (`LICENSE.md`); `vendor/` has its own licences;
the XMage test sources it carries are XMage's.

- **Use as-is, unmodified, non-commercial**: allowed under either licence (BSL's Additional Use Grant permits
  non-commercial production use; AGPL permits any use).
- **Modify and run as a network service** (an engine API behind our MCP): under AGPL we must offer the modified
  source to users who interact with it over the network. For a private, single-user deployment this is cheap; it
  becomes a real obligation only if the service is opened to others.
- **Merge into MCM or spellslinger code**: any derivative work becomes AGPL (or BSL) as a whole. Copying ironsmith
  code into private, unlicensed repos is not permitted unless those repos take the same licence. Calling it as a
  separate process over HTTP keeps our services separate works.
- **Commercial use** under BSL needs a commercial licence from the author until each version's change date (four
  years after release, then MIT).

Conclusion: usable, as a separately deployed component consumed over an API; not mergeable into MCM's or
spellslinger's private source without relicensing those.

## 7. Integration cost with spellslinger

Today `sscli mcp` (spellslinger-cli, Go, mcp-go) registers tools that proxy HTTP to the services
(`internal/raw/<service>` clients, `internal/mcp/server.go`). A rules engine plugs in the same way: one HTTP service
plus one client package plus tool definitions.

| Path | Work | Cost (agent wall-clock) | Risks |
|---|---|---|---|
| ironsmith native service: a small Rust binary (or Go via the CLI) linking `ironsmith-runtime` / `ironsmith-engine` at the pinned commit, exposing card compile/support, game setup, legal actions, apply action, state | new repo `spellslinger-engine`, Dockerfile building the Rust workspace, chart, helmfile release, `sscli` client and tools | 1-2 days | new language in the stack (Go services today); multi-GB build context; API surface must be discovered from crates (no stable native API is documented) |
| ironsmith WASM in a Node service: wrap the existing JS/WASM facade (`dispatchForAutomation`, `advancePhase`, `getEmbeddedCardSourceJson`, savepoints, ...) | build the WASM from the pin (npm 0.1.2 is July and stale), thin HTTP layer, chart, `sscli` tools | about 1 day | the facade is UI-oriented; card catalogue build needs the Scryfall pipeline |
| MCM via `magic-cards-model-api` (already FastAPI, already deployed in `mtg-engine`) | `sscli` client and tools, semver tagging, move release into spellslinger-helmfile | about half a day | engine stays at about 82% handled Modern, 3,068 silent cards; CI red; the user's scaling problem stays |

Either ironsmith path keeps ironsmith a pinned, unmodified, separately deployed dependency, which also keeps the
AGPL obligation trivial and the workbench rule "code/ironsmith is read-only" intact.

## 8. Recommendation

Adopt ironsmith as the rules engine of record behind a new, separately deployed engine service called from
`sscli mcp`, pinned to a reviewed commit and never modified; stop new card work in magic-cards-model and keep its
6,180 scenario-tested cards as an acceptance corpus to verify ironsmith's gameplay (its coverage lead is
95.5% vs 81.9% of Modern on each project's own measurement, it has a compiler architecture that scales to new
cards where MCM's hand-written parsers do not, and it is actively maintained), with a short differential spike on
the Modern metagame decks before MCM is archived.

## 9. Decision questions

1. **Engine strategy.**
   - A) Adopt ironsmith as the engine of record, freeze MCM. **Recommended**
   - B) Time-boxed differential spike first: replay MCM's Modern metagame scenario tests against ironsmith, then
     decide. **MVP**
   - C) Keep MCM as the engine and use ironsmith only as a design reference.
2. **Licence path for ironsmith.**
   - A) AGPL-3.0, unmodified, private non-commercial deployment; publish any patch we ever make.
     **MVP, Recommended**
   - B) BSL-1.1 non-commercial terms.
   - C) Ask the author for a separate licence (needed only for commercial use or merging code into private repos).
3. **Integration shape.**
   - A) Rust-native `spellslinger-engine` HTTP service built from the pinned crates, exposed as `sscli mcp` tools.
     **Recommended**
   - B) Node service wrapping the ironsmith WASM facade built from the pin. **MVP**
   - C) No service; agents use the hosted web UI only.
4. **Fate of magic-cards-model and magic-cards-model-api.**
   - A) Archive both after the spike; port the scenario corpus to an engine acceptance suite. **Recommended**
   - B) Leave both running untouched, no new work. **MVP**
   - C) Keep developing MCM in parallel.
