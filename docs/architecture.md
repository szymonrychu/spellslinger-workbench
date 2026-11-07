# Architecture

## Components

```
workbench/
  code/
    spellslinger-cards/  (go)
    spellslinger-cli/  (go)
    spellslinger-codex/  (typescript)
```

- `code/spellslinger-cards` (go): card database API and Scryfall ingestion CronJob
- `code/spellslinger-cli` (go): sscli CLI and the MCP server (spellslinger-mcp-http runs sscli mcp)
- `code/spellslinger-codex` (typescript): codex service (purpose to be verified)
