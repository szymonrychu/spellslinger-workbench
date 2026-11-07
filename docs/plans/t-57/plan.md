# T-57: spellslinger takeover (remaining scope)

Date: 2026-11-07. Phase 1 (read-only discovery) is done: see `docs/discovery.md`.

Hard constraint: the spellslinger MCP (spellslinger-mcp-http) is in live use by the mtg and marek-mtg
presets and by hermes-agent. No disruption. Cluster changes only through reviewed PRs and planned,
announced applies.

## Remaining scope

1. State report: one document of the real current state (what runs, what fails, what is missing),
   built from `docs/discovery.md` plus the now-located sources in `code/`.
2. synergy-api worker memory 512Mi request / 2Gi limit into helm values (stopgap for the OOMKilled
   worker, discovery 5.1). Open PRs, both to be reviewed and merged before any apply:
   - https://github.com/szymonrychu/spellslinger-helmfile/pull/1 (branch synergy-worker-memory)
   - https://github.com/szymonrychu/spellslinger-synergy-api/pull/1 (branch synergy-worker-memory)
   The apply is a planned, announced `helm upgrade` of spellslinger-synergy-api only.
3. Phase 2: maturity comparison of ironsmith (Chiplis/ironsmith, `code/ironsmith`, read-only, pinned)
   versus magic-cards-model (`code/magic-cards-model`) and the spellslinger engine. Axes: coverage
   (measured, not claimed), rules accuracy, architecture, activity and bus factor, licence (GitHub
   reports NOASSERTION for ironsmith: read LICENSE.md), integration cost. Ends with a recommendation
   and the decisions the user must take.

## Notes

- ironsmith is about 2.6 GB. Its submodule entry has `update = none`, so a normal
  `git submodule update --init --recursive` skips it. Fetch on demand with
  `git submodule update --init --checkout --depth 1 code/ironsmith` (needs several GB free; it has a nested
  submodule vendor/mana).
- Other discovery follow-ups (CNPG backups, failed spellslinger-llm-queue-database release, cards-ingestion
  stale since 2026-08-24, knowledge-worker-deck OOM) are in discovery section 5 and 7 and are not in the
  T-57 scope above until the user adds them.
