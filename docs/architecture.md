# Architecture

## Components

```
workbench/
  code/
    spellslinger-cards/  (go)
    spellslinger-cli/  (go)
```

- `code/spellslinger-cards` (go): card database API and Scryfall ingestion CronJob
- `code/spellslinger-cli` (go): sscli CLI and the MCP server (spellslinger-mcp-http runs sscli mcp)
