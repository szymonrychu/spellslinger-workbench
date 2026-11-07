# Workbench

## What this repository is

This is a **workbench metarepository**: a thin superrepo whose real content lives in git
submodules under `code/`, plus shared skills, rules and documentation that support
development across the components. It is a working root, not a place for code.

- The submodules ARE the code. Every substantive change happens inside a `code/<component>`
  submodule, which is its own independent repo with its own tests, `MEMORY.md` and
  `ROADMAP.md`.
- This superrepo carries no build of its own for components. It pins submodule commits and
  hosts cross-cutting workbench material; the tooling lives under `plugins/`.

Bootstrap and refresh submodules:

    git submodule update --init --recursive     # first checkout
    git submodule update --remote               # advance each to its tracked branch

Each submodule tracks a branch (see `.gitmodules`). Work inside a submodule on its own
branch, land on that submodule's default branch, then commit the moved pointer here.

<!-- workbench:project:begin -->
## What this project is building

spellslinger is an MTG deck-optimization system: Go microservices (cards, identity, knowledge, statistics, synergy-api, reveries, codex, llm-queue), the sscli CLI and MCP server spellslinger-mcp-http, LightRAG, neo4j and CNPG Postgres, deployed in k8s namespace spellslinger-development (llm-queue in ns ai) by manual helm upgrade with no CI today; being taken over under the tatara agents system. Facts: docs/discovery.md. Read-only third-party reference: code/ironsmith (Chiplis/ironsmith, pinned, never updated, never edited).

## Components (code/)

| Submodule | Lang | Role | Build |
|-----------|------|------|-------|
| spellslinger-cards | go | card database API and Scryfall ingestion CronJob | `mise run --cd code/spellslinger-cards test` |
| spellslinger-cli | go | sscli CLI and the MCP server (spellslinger-mcp-http runs sscli mcp) | `mise run --cd code/spellslinger-cli test` |
| spellslinger-codex | typescript | codex service (purpose to be verified) | `mise run --cd code/spellslinger-codex test` |
| spellslinger-deckbuilder | python | deck building service | `mise run --cd code/spellslinger-deckbuilder test` |

## Component hard rules

- The spellslinger MCP is in live use by the mtg and marek-mtg presets and by hermes-agent: NO disruption allowed.
- Cluster changes only through reviewed PRs and planned, announced applies; discovery is read-only first.
- Go services; deploy only semver-tagged images (X.Y.Z), never a sha tag.
- code/ironsmith is a read-only third-party reference pinned to one commit: no branch tracking, no edits, no submodule update --remote for it.

## Highest-risk surface

Live MCP and the spellslinger-development namespace (stateful Postgres and neo4j without backups): any helm upgrade, restart or node move can drop agent tool calls or lose data.

## Forge

Origins are on GitHub: changes land through pull requests (PRs), via `gh`.
<!-- workbench:project:end -->

## Ground rules

1. **Development flow.** Non-trivial work (a feature, a cross-component change, a change to
   the workbench itself) starts with `start-development` (Claude Code:
   `workbench:start-development`): discovery, design and plan behind one approval gate, then
   unattended execution. Reviews go through `start-review`, failures through
   `start-debugging`. Implementation goes through `epic-run`: one implementer and one reviewer per
   task, two fix rounds, one scope audit per epic; never hand-roll a loop beyond that. In
   harnesses other than Claude Code, invoke the skills by their bare names.
2. **Always use subagents, with an explicit model.** Set the model on every dispatch:
   research opus; implementation sonnet, opus only for the hardest tasks; review sonnet;
   very complex architecture decisions fable; mechanical relays and classifiers: haiku;
   everything else (lookups, summaries, merges, monitoring) sonnet. Never use a stronger model when a weaker one
   suffices. On other harnesses use the harness's strongest or default equivalents of these
   tiers.
3. **Finish the whole scope and nothing outside it.** Implement everything asked, to the
   letter: never skip, "all" and "each" mean all and each. If it needs a missing subsystem,
   build the subsystem. Difficulty changes sequencing, never whether it gets done. The only
   acceptable non-delivery is a genuine blocker: name it and ask. Never cut corners or reduce
   scope (see "Housekeeping rules": full scope). Do not widen scope; a tangent gets exactly
   one line, "noted, not doing now: <thing>", and work continues.
4. **Never report waiting.** "Waiting", "holding", "blocked", "nothing to do yet" are a
   signal you have not found the work. Enumerate every open item (PR/MR, pipeline, branch,
   worktree, background task) and act on its state:

   | State | Action, now |
   |---|---|
   | green and mergeable, no unresolved review | merge it |
   | conflicted, `DIRTY`, `BEHIND` | rebase the branch |
   | changes requested, unresolved discussions | judge each finding, fix the real ones, drop the wrong ones |
   | `BLOCKED`, not approved, discussions unresolved | read the actual reason and act on it |
   | failing CI | read the log tail, fix the cause |
   | a dependency just merged | rebase and re-push what was waiting on it |

   Only when every item is genuinely pending on someone else may you say so, naming each
   item, its state and what it waits on. Act on the first item that transitions, never the
   batch: independent items get independent action. Bound every wait at 10 minutes, then
   re-enumerate and report concretely. Use a tested watcher script, never a hand-rolled
   polling loop. For agents running in the background, the Agent notification on exit is the
   wake signal: do not poll.
5. **Stay on the assignment and answer short.** Do the task given: no unrelated issues, no
   refactors beyond the task, no extra hardening. Keep answers to a few lines: what
   changed, what is next, anything needing a decision. Detail only when asked. If scope
   genuinely must grow, stop and ask in one sentence.
6. **Recurring corrections.**
   - Give estimates in agent wall-clock time, not human-days.
   - Main is always green: never merge or leave a red default branch.
   - Take the least destructive action first wherever actions have real side effects
     (deletes, force-pushes, applies, deploys); escalate only when it fails.
   - Record standing approvals in writing and honour them without re-asking.
   - Deferral sticks: what the user deferred stays deferred until they say otherwise.
   - Use the project's wrappers (`mise run ...`, helper scripts) instead of raw commands.
   - Do not run what the user said they will run themselves.
   - Boy-scout, reconciled: simplify the files the task already touches; for any other
     file, state the observation in one line and carry on.

## Writing and working conventions

- No em dashes, smart quotes, arrows or decorative Unicode, in code, comments, commits,
  messages or any other content (see "Housekeeping rules"). Plain hyphens and straight
  quotes. No preamble.
- Before working in a component, read its `AGENTS.md`, `MEMORY.md` and `ROADMAP.md`.
- Update `MEMORY.md` on every non-obvious decision, with the date and the why.
- `ROADMAP.md` is human-owned requirements; ask the user rather than inventing entries.
- Near context limits, use the `handoff` skill instead of pushing on.

<!-- workbench:rules:begin -->
_Generated from plugins/workbench/rules/; edit there, then run `mise run harness-setup`._

## Test-driven development

Every behaviour change is written test-first. Not "tested afterwards" - the test
comes first and is seen failing before the code that makes it pass exists.

1. **Red.** Write the test and run it. Watch it fail, and check it fails for the
   reason you expect. A test that passes before the implementation exists is
   asserting nothing, and this is the step that catches that.
2. **Green.** Write the smallest implementation that passes it.
3. **Refactor.** Clean up with the test still green.

This is not optional because the change is small, urgent, or "obviously
correct". Those are the changes that ship broken.

Legitimate exceptions, and they are narrow: pure formatting, a comment or doc
edit, a dependency bump with no behaviour change, a spike you are going to
throw away, or a deletion pinned by a retirement test (the diff's non-test
changes are deletions only and it adds or changes a test that pins the removal). If you skip the cycle, say which exception applied - do not claim a
red-green cycle you did not run.

### Verify before reporting back

Never report work as done, passing, or complete without having run the check and
read its output. This applies especially when handing work back to an
orchestrating agent, which cannot see your terminal and will take the claim at
face value.

- Run the repo's own command (`mise run test`, or whatever the repo defines).
- Quote the real output, including the pass/fail summary line.
- "Should pass", "the change is straightforward", and a green diff are not
  evidence. An unread command is an unrun command.

If verification fails and you cannot fix it, say so with the output. A named
failure is useful; a false pass costs the next agent hours.

## Boy scout rule

Leave the tree better than you found it, and never let someone else's loose
end become a reason your own work is incomplete.

1. **Simplify what you touch.** If code you are already working in can be made
   simpler without changing behaviour, do it. Not a refactor tour - the files
   the task already puts in your hands.
2. **Functional but uncommitted work gets committed.** Uncommitted changes that
   work are not "someone else's problem" to route around. Review them, confirm
   they are green, and commit them.
3. **Uncommitted work that blocks full delivery must be cleared, not worked
   around.** Review it, adjust it until lint and tests pass, commit it as its
   own commit, then commit your work on top. Never leave your change sitting in
   a tree that was already broken, and never report a failure that belongs to
   pre-existing work as a reason your task is unfinished.

Commit boundaries stay honest: pre-existing work and your work are separate,
adjacent commits with their own messages. Fixing someone's lint does not make
their feature yours, and it does not get folded into your commit.

Do not commit work that is broken, half-finished, or that you cannot verify.
"Functional" means you ran the checks and they passed.

## Concise orchestrator output

The orchestrator's context is the most expensive thing in a session: every turn
re-reads all of it. After the initial discussion of a task, every update,
notification reply, poll reply and status is VERY short.

- Progress update: one line. `<what moved> - <next> - <decision needed, if any>`.
- Poll result with nothing actionable: no tool call, and no text
  beyond the line itself.
- Never restate what a notification already says. Never paste logs, tables,
  JSON or diffs unless asked; cite a path instead.
- A finished task: what landed, verified how (the one summary line of the real
  output), what is next. Three lines at most.
- Subagent prompts and reports follow the same rule: ask for capped reports
  (a word limit), and read their files rather than their full transcripts.
- Detail only when the user asks for it, or a decision needs it.

## Housekeeping rules

The user's standing rules for every agent, every harness and every task.

1. **Supervisor only.** The agent the user talks to never writes code or builds
   anything. It is the supervisor, responsible and accountable for any and all
   work its subagents do. Its own duties are not building: ticket and plan files
   through `ticket.py` (design.md and record.md directly), running the repo's test
   and lint commands to read results, and the git operations of close through
   `ticket.py close`. It never edits source, tests, skills, agents, hooks or docs
   outside `docs/plans/`.
2. **Tests are not negotiable.** Never edit, delete or xfail a test to make it
   pass, unless the test itself is no longer accurate; then say which test and
   why. Tests make the code repeatable and guard against regressions.
3. **Read, then edit, then run.** Before changing anything, an implementing or
   reviewing subagent must list every file the step touches, read them all in one
   pass, and only then make all edits for the step. It then runs the targeted
   verify once per step; under TDD that is once per red step and once per green
   step, never an edit-run-edit-run dribble.
4. **No backward compatibility** (shims, aliases, legacy fallbacks) unless the
   user explicitly asks for it.
5. **No em dash characters** in any code, comment, commit, message or content of
   any kind. Use a plain hyphen.
6. **Do not guess, at any level.** When unsure of a fact, ask the user or the
   fable architect; a subagent returns it as a question instead of guessing.
7. **Full scope.** Always aim for the full scope of the improvement; never cut
   corners or reduce scope.
8. **One scratchpad.** Every scratchpad edit lands under `.scratchpad` in the
   workbench root (the main checkout, never a worktree); it is the only
   scratchpad dir (`workbench.py scratchpad` prints it).
9. **One log dir.** Every log lands in the gitignored `.logs` in the workbench
   root (`workbench.py logs` prints it).
<!-- workbench:rules:end -->
