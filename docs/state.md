# Spellslinger - current state

Date: 2026-11-10 (T-57 phase 2). Sources: phase-1 discovery (`docs/discovery.md`, read-only cluster, Grafana and
forge inspection on 2026-11-07), the repo map built the same day, and the submodules in `code/`. Live numbers
below are from 2026-11-07 unless dated otherwise; nothing was re-measured on the cluster for this document.

## 1. What runs today

Namespace `spellslinger-development` (age about 185 days), deployed by `code/spellslinger-helmfile` from
semver images in the private Harbor registry. All in-house services are Go; the web front ends are React.

| Component | Repo | Deployed | Role |
|---|---|---|---|
| cards | spellslinger-cards | 0.9.2 | card DB API; nightly `cards-ingestion` from Scryfall |
| identity | spellslinger-identity | 0.6.1 | users and identity |
| knowledge | spellslinger-knowledge | 0.19.1 | Comprehensive Rules, rulings, wiki, decks, embeddings; 8 worker CronJobs |
| statistics | spellslinger-statistics | 0.21.0 | tournament data; scrapers (mtgtop8, topdeck, magicgg, videre, mtgocache; melee and mtgdecks suspended) |
| synergy-api | spellslinger-synergy-api | 0.21.2 | synergy and deck evaluation heuristics; `synergy-api-worker` every 15 min |
| reveries | spellslinger-reveries | 0.1.4 | curated MTG knowledge |
| codex | spellslinger-codex | 1.3.1 | React SPA (web UI) |
| golang / react repo seeds | spellslinger-*-repo-seed | 0.2.1 / 0.1.0 | service templates, deployed as probes |
| MCP server | spellslinger-cli (`sscli mcp`) | sscli 0.5.1 | the MCP endpoint, HTTP on :8080/mcp, Keycloak client credentials |
| llm-queue | spellslinger-llm-queue | 0.2.0 (ns `ai`) | LLM task queue |
| LightRAG x2, Neo4j x2 | spellslinger-lightrag (charts) / upstream images | lightrag v1.4.16, neo4j 5.26.0 | graph RAG stores |
| 7 CNPG Postgres clusters | spellslinger-helmfile | PG 15/16, 1 instance each | one per service |

Not deployed: `spellslinger-mcp` (archived 2026-05-18, superseded by `sscli mcp`; this resolves the repo-map's
"mcp 0.7.2 vs sscli 0.5.1" gap), `spellslinger-deckbuilder` (Claude Code plugin, consumer of the MCP),
`spellslinger-docs`, `spellslinger-login` (Keycloak theme image).

There is **no rules engine in spellslinger**. The rules work lives in `code/magic-cards-model` (Python, pydantic),
deployed separately as `mtg-stack` (magic-cards-model-api, sha-tagged image) in namespace `mtg-engine`. It consumes
the spellslinger MCP for rules lookups during development. See `docs/maturity-comparison.md`.

## 2. Current usage

- MCP consumers: hermes-agent (ns `ai`, 26 tools: card pool and search, chat, knowledge search, meta banwatch /
  forecast / history / strength, resolve_cards, reveries, upcoming sets, statistics, synergy) and the orchestrator
  presets `mtg` and `marek-mtg`; magic-cards-model sessions via `.mcp.json`; the deckbuilder plugin.
- MCP request volume is not measurable: `sscli` logs only token refreshes and exposes no request metrics, and
  in-cluster traffic bypasses the ingress.
- Web/API ingress over 14 days: synergy-api 394x 200, statistics 35, cards 5, oauth2-proxy about 1046 redirects.
  Light, single-user load.
- Storage: LightRAG DB PVC at 73% of 5Gi (highest); others under 25%.

## 3. Stability challenges (evidenced 2026-11-07)

1. synergy-api-worker OOMKilled every run at the 1Gi limit. Fixed in source on 2026-11-10: spellslinger-helmfile #1
   and spellslinger-synergy-api #1 merged (512Mi request, 2Gi limit); submodule pointers bumped in this branch.
   Not yet verified on the cluster after a sync.
2. `cards-ingestion` has not succeeded since 2026-08-24; the card DB is stale, a likely cause of the "unresolved card
   name" flood in synergy.
3. knowledge-worker-deck OOMKilled at 512Mi, no success since 2026-08-24 (loads about 196k decks into memory).
4. statistics-worker-magicgg has never succeeded (Keycloak token fetch times out through the gluetun VPN proxy);
   melee and mtgdecks scrapers suspended.
5. knowledge-worker-enrich retires rows at the retry cap every 15 minutes.
6. No backups: 7 single-instance CNPG clusters without backup spec, Neo4j PVCs unbacked.
7. Restarts in 14 days: mcp-http 18 (14 distinct pods), synergy-api 12, reveries-lightrag 9; single replicas, no PDB.
   An MCP restart drops in-flight agent tool calls.
8. Start-up ordering: services crash once at reschedule until their databases are up.
9. No resource limits on most Deployments; 15 of 23 pods on node `nas-d0w363i` (nodeSelector pins).
10. Drift: `spellslinger-llm-queue-database` Helm release failed since 2026-10-19; cli `Chart.yaml` 0.1.1 vs tag
    0.5.1; Neo4j community and LightRAG pinned to old versions; no renovate coverage.
11. Observability: no MCP request logs or metrics.

## 4. Code and activity snapshot

All 17 spellslinger repos have a single author. Feature work ran 2026-05-06 to 2026-08-25; every main HEAD since
is the docs-only workbench-flow commit of 2026-09-21 (plus today's two memory fixes). Biggest repos by Go/TS LOC:
synergy-api 27.9k, statistics 26.6k, knowledge 25.9k, deckbuilder 15.5k (Python), cli 12.4k, cards 11.4k.
CI is GitLab (`.gitlab-ci.yml`); there are no GitHub Actions in these repos. No repo carries a LICENSE file.

## 5. Open items carried from phase 1

- Verify the synergy worker after the next helmfile sync.
- Re-run cards ingestion and fix its retry on a down API; fix knowledge-worker-deck streaming.
- Enable CNPG backups and a Neo4j backup; fix the failed llm-queue database release.
- Add request metrics and logs to `sscli mcp`; consider 2 replicas plus a PDB for mcp-http.
