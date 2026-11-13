> NOTE (2026-11-07): written before the sources were located. Sections 3, 6 and the open questions are SUPERSEDED:
> the sources live in the 17 szymonrychu/spellslinger-* GitHub repos plus magic-cards-model, all submodules of this
> workbench (ironsmith is a read-only third-party reference). Sections 1, 2, 4, 5 and 7 still describe the live state.
> Scrubbed: no secret values were present; only chart metadata and counts.

# Spellslinger discovery (T-57, phase 1, read-only)

Date: 2026-11-07. Method: kubectl/helm read-only as `system:serviceaccount:agents:agents-orchestrator-kube-access`,
glab/gh read-only, Grafana Prometheus + Loki. Raw outputs: `/workdir/workdir/.logs/spellslinger/`.
No secrets were read (only Helm chart metadata was extracted from release records).

Tool notes: `kubectl` and `helm` mise shims have no version set in this container (call the binaries directly:
`/opt/mise/installs/kubectl/1.33.13/kubectl`, `/opt/mise/installs/helm/4.3.1/linux-amd64/helm`). metrics-server is
absent (`kubectl top` fails); Prometheus covers it. Loki 14d/7d aggregate queries return 502; 1d works.

## 1. Topology (namespace `spellslinger-development`, age 185d)

All in-house images: `registry.example.com/containers/<name>:<semver>`. Services are Go (slog JSON logs).

| Release (Helm) | Image:tag | Rev | Last deploy | Role / notes |
|---|---|---|---|---|
| spellslinger-cards | spellslinger-cards:0.9.2 | 73 | 2026-08-24 | card DB API; CronJob `cards-ingestion` 03:00 (Scryfall) |
| spellslinger-identity | spellslinger-identity:0.6.1 | 23 | 2026-05-24 | users/identity |
| spellslinger-knowledge | spellslinger-knowledge:0.19.1 | 124 | 2026-08-24 | knowledge base; 8 worker CronJobs (sync, yt, wiki, cr, deck, enrich, embed-poll, backfill-embeddings) |
| spellslinger-statistics | spellslinger-statistics:0.21.0 | 209 | 2026-08-25 | tournament stats; scraper CronJobs mtgtop8, topdeck, magicgg, videre, mtgocache (melee, mtgdecks suspended); gluetun VPN sidecar + flaresolverr |
| spellslinger-synergy-api | spellslinger-synergy-api:0.21.2 | 88 | 2026-08-25 | synergy/deck evaluation; CronJob `synergy-api-worker` */15 |
| spellslinger-reveries | spellslinger-reveries:0.1.4 | 8 | 2026-05-19 | curated MTG knowledge |
| spellslinger-codex | spellslinger-codex:1.3.1 | 44 | 2026-09-09 | (purpose unverified) |
| spellslinger-golang-repo-seed / react-repo-seed | 0.2.1 / 0.1.0 | 4 / 2 | 2026-05 | repo seed services; harbor-probe CronJob */5 |
| spellslinger-mcp-http | **sscli:0.5.1** | 3 | 2026-08-25 | the MCP server (`sscli mcp` over HTTP, :8080/mcp), client_credentials to Keycloak |
| spellslinger-lightrag, -reveries-lightrag | ghcr.io/hkuds/lightrag:v1.4.16 | 2 / 1 | 2026-05 | LightRAG, 1Gi limit |
| spellslinger-neo4j, -reveries-neo4j (sts) | neo4j:5.26.0-community | 2 / 36 | 2026-07/08 | graph stores, 5Gi PVC each |
| 7x `*-database` (CNPG `cluster-0.6.0`) | postgresql 15/16 | | 2026-05..08 | cards, identity, knowledge, lightrag, reveries, statistics, synergy-api; 1 instance each |
| oauth2-proxy-external | oauth2-proxy v7.15.2 | 18 | 2026-05-24 | SSO in front of spellslinger.example.com |
| flaresolverr (not Helm, kubectl apply) | flaresolverr v3.3.21 | | | Cloudflare bypass for scrapers, 2 replicas |

Related elsewhere:
- ns `ai`: `spellslinger-llm-queue` 0.2.0 (+ worker, CNPG `spellslinger-llm-queue-database` release in **failed** state since
  2026-10-19, rev 13). This one IS in `szymonrychu/helmfile` (`helmfiles/ai`).
- Keycloak realm `spellslinger` (auth.example.com): clients, groups, IdP, scopes, service accounts, test users in
  `szymonrychu/terraform` `keycloak/spellslinger_*.tf`. Login theme image from `szymonrychu/spellslinger-login`.
- ns `mtg-engine`: `mtg-stack` (magic-cards-model-api, sha tag) - separate product (GitHub `magic-cards-model*`), not spellslinger.
- ns `mtg`: empty.

Ingresses: `spellslinger.example.com` (cards, identity, knowledge, lightrag, reveries, statistics, synergy-api,
oauth2-proxy) and `mcp.example.com` (`spellslinger-mcp-http-lan`). NetworkPolicy only on mcp-http.
Placement: 15 of 23 long-running pods on `nas-d0w363i`; some Deployments nodeSelector-pinned to it.

## 2. How it is deployed

- 22 Helm releases, applyMethod `ssa` (Helm 4 client), one chart per service (`spellslinger-<svc>-<appVersion>`), no
  `home`/`sources` in chart metadata. Not in `szymonrychu/helmfile` (its MEMORY/remediation docs state "only
  spellslinger-llm-queue is in our helmfile; spellslinger-* live in external repos") and not in `szymonrychu/charts`.
  No Argo CD. So: manual `helm upgrade` from each service's own repo/chart (high revision counts: statistics 209,
  knowledge 124), last activity 2026-08-24/25 (codex 2026-09-09). flaresolverr is a raw `kubectl apply`.
- Values, charts and source code: **not found**. See section 5 blocker.

## 3. GitLab / GitHub mapping

glab is authenticated to gitlab.com (user szymonrychu); no groups visible; owned projects searched.
- No `spellslinger-*` or `sscli` source project exists in any namespace visible to this token (global search, group
  probes `spellslinger`, `spellslinger-development`, `mtg` all 404). Harbor API requires auth (no anonymous access),
  so OCI labels could not be read.
- Found and related:
  - `gitlab.com/szymonrychu/spellslinger-login` (main, last activity 2026-04-26) - Keycloak theme.
  - `gitlab.com/szymonrychu/terraform` (main) - Keycloak realm/clients for spellslinger.
  - `gitlab.com/szymonrychu/helmfile` (main) - only spellslinger-llm-queue.
  - April 2026 predecessors (Go, last activity 2026-05-03..05, own charts named cardpool, mtg-statistics, webui,
    overseer, match-manager, player, rules-engine, operator, mtg-user; none deployed): `szymonrychu/{cardpool,
    mtg-statistics, mtg-user, mtg-webui, mtg-overseer, match-manager, player, rules-engine, operator}`.
    cardpool docs reference "spellslinger realm"; likely ancestors, not the deployed code.
  - GitHub `szymonrychu/mtg-decks` (private, 2026-10-28) - decklists managed by tatara agents with spellslinger tooling (consumer).

## 4. Usage (last 14 days)

- MCP consumers: hermes-agent (ns `ai`, configmap `hermes-agent`, `mcp_servers.spellslinger` ->
  `http://spellslinger-mcp-http.spellslinger-development.svc.cluster.local:8080/mcp`, 26 tools: card_pool,
  card_search, chat_*, knowledge_search, meta_banwatch/forecast/history/strength, resolve_cards, reveries_*,
  sets_upcoming, statistics_archetypes/decks/matchups/trending, synergy_card/evaluate/flex_slots/hypothetical/
  manabase/meta_snapshot); orchestrator presets `mtg` and `marek-mtg` (per caller; presets API returned 403 to this
  SA, so not independently verified). Nothing in any-mcp-tatara-plugins or this workbench references spellslinger.
- MCP request volume: **not measurable** - sscli logs only token refreshes, exposes no metrics; in-cluster traffic
  bypasses ingress. LAN ingress `mcp.example.com`: 2510x 403, 821x 308, 0x 2xx in 14d (only rejected/redirected
  external hits). mcp-http pod RX ~9 B/s average.
- Web/API ingress 14d: synergy-api 394x 200, statistics 35, cards 5, oauth2-proxy ~1046 302s. Light, single-user.
- Memory peaks 14d (MiB): flaresolverr 3071, workers 1024 (= limit), postgres 994, neo4j 591, lightrag 363,
  statistics 329.
- Storage: lightrag DB PVC 73% of 5Gi (highest); others under 25%; synergy DB 19% of 50Gi.

## 5. Stability challenges and risks (evidenced)

1. **synergy-api-worker OOMKilled every run** (1Gi limit): 13 OOMKilled pods in the last ~80 min, last success
   2026-11-07 02:01; logs flood with "unresolved card name" (Black Lotus, Moxen, ...).
2. **cards-ingestion has not succeeded since 2026-08-24** (~75 days): today's run died with "connection refused" to
   spellslinger-cards when all pods were rescheduled at 03:30. Card DB is stale (likely cause of unresolved names).
3. **knowledge-worker-deck OOMKilled (512Mi), no success since 2026-08-24** (fetches ~196k decks into memory).
4. **statistics-worker-magicgg never succeeded**: Keycloak token fetch times out through the gluetun VPN proxy.
   melee and mtgdecks scrapers suspended (mtgdecks since 2026-05-26).
5. knowledge-worker-enrich logs "rows permanently retired at the retry cap" every 15 min (104 deck_archetypes, 30 wiki_sections).
6. **No backups**: all 7 CNPG clusters have no `backup` spec and no ScheduledBackup (CNPG backups disabled
   cluster-wide per helmfile ROADMAP), single instance each; neo4j PVCs unbacked too. Data loss on a rook-ceph incident.
7. Restarts 14d: mcp-http 18, synergy-api 12, reveries-lightrag 9, oauth2-proxy 7, lightrag 6. mcp-http had 14 distinct
   pods in 14d (frequent rescheduling); a restart drops in-flight agent tool calls. Single replica, no PDB.
8. Startup ordering: services crash once (Error) at reschedule until DBs come up.
9. No resource limits on most Deployments (only workers, lightrag, neo4j, flaresolverr).
10. Drift and ownership: no source/values found; no CI-driven deploy; not covered by renovate; Postgres 15 + 16 mix;
    `spellslinger-llm-queue-database` Helm release failed; known llm-queue migrate initContainer 0.1.0 vs image 0.2.0
    mismatch (terraform ROADMAP); neo4j community and lightrag pinned to old versions.
11. Observability: no MCP request logs/metrics; duplicated "Spellslinger Synergy API" Grafana dashboard noted in terraform ROADMAP.
12. Concentration on node `nas-d0w363i` (nodeSelector pins).

## 6. Proposed submodules for the new GitLab workbench

Known, cloneable now:

| Path | URL | Branch |
|---|---|---|
| code/spellslinger-login | git@gitlab.com:szymonrychu/spellslinger-login.git | main |

Needed but source location unknown (blocker - user must supply): spellslinger-cards, -identity, -knowledge,
-statistics, -synergy-api, -reveries, -codex, -golang-repo-seed, -react-repo-seed, sscli (mcp-http),
-llm-queue, lightrag charts (spellslinger-lightrag, -reveries-lightrag), neo4j values, oauth2-proxy-external values,
flaresolverr manifest.

Reference-only candidates (decide): GitHub `szymonrychu/mtg-decks` (consumer), April predecessors
(`cardpool`, `mtg-statistics`, ...) if they are the ancestors. Infra stays in the infra workbench
(`helmfile`, `terraform`, `charts`) rather than as submodules here.

## 7. For the infrastructure agent

- Home for deploy config: move the 22 Helm releases (and flaresolverr) into `szymonrychu/helmfile` (new bucket, e.g.
  `helmfiles/spellslinger`) after values are recovered (`helm get values`, done by someone allowed to see secrets, with
  secrets moved to SOPS).
- Enable CNPG backups for the 7 spellslinger clusters + neo4j PVC backups.
- Fix `spellslinger-llm-queue-database` failed release (ns ai).
- Raise worker memory (synergy-api-worker, knowledge-worker-deck) only as a stopgap.
- Harbor read access for the takeover agent (to read image OCI labels / list tags).
- Create the GitLab workbench repo and, if sources live under another account/group, grant this token access.

## Open questions for the user

1. Where is the source of the spellslinger-* services and sscli (other GitLab account/group, self-hosted, local only)?
   Recommended: grant this glab token access to that group, then all go in as submodules.
2. Are the April `szymonrychu/mtg-*`/`cardpool` repos ancestors to archive, not submodules? Recommended: yes, leave them out.
3. Should `mtg-decks` (GitHub) be a submodule of the spellslinger workbench? Recommended: yes, as the main consumer/test bed.
