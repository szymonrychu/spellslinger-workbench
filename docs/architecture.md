# Architecture

## Components

```
workbench/
  code/
    spellslinger-cards/  (go)
    spellslinger-cli/  (go)
    spellslinger-codex/  (typescript)
    spellslinger-deckbuilder/  (python)
    spellslinger-docs/  (generic)
    spellslinger-golang-repo-seed/  (go)
```

- `code/spellslinger-cards` (go): card database API and Scryfall ingestion CronJob
- `code/spellslinger-cli` (go): sscli CLI and the MCP server (spellslinger-mcp-http runs sscli mcp)
- `code/spellslinger-codex` (typescript): codex service (purpose to be verified)
- `code/spellslinger-deckbuilder` (python): deck building service
- `code/spellslinger-docs` (generic): spellslinger documentation
- `code/spellslinger-golang-repo-seed` (go): Go repo seed service and template
