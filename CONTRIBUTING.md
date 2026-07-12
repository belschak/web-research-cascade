# Contributing

Most of the value of this repo is documented routes, and routes rot: providers change their blocking, endpoints close, new walls appear. If a provider changed something and you found the new way through, that is exactly the contribution this repo wants. You do not need to know the codebase for that.

## What is most welcome

1. **A new "source with its own route".** Like the existing Reddit / X / Zendesk shortcuts: a source that blocks the generic cascade, plus the route that actually works. Open an issue with the URL pattern, what each stage returned, and how you got through.
2. **A fix for a stage or route that broke.** Include what changed on the provider side (as far as you can tell) and how you verified the fix.
3. **Tested improvements to the bundled scripts** (`firecrawl_fetch.py`, `x_tweet.py`).
4. **Docs fixes**, especially platform specifics (Windows paths, shells, skills directory locations).

## Your first 30 minutes

Issues labeled [`good first issue`](https://github.com/belschak/web-research-cascade/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) are scoped to 30 to 60 minutes and need no prior knowledge of the project. Each one states its acceptance criteria in the body.

## Setup

There is no build and there are no dependencies.

```bash
git clone https://github.com/belschak/web-research-cascade.git
cd web-research-cascade
python x_tweet.py --help          # scripts run on stock Python 3.9+
```

To test the skill itself, copy (or clone) the folder into your agent's skills directory (`~/.claude/skills/` for Claude Code) and run a fetch against a page that 403s.

## Style rules

- **SKILL.md stays compact.** It is loaded into an agent's context; every sentence costs tokens. Prefer editing an existing section over adding a new one.
- **Python: standard library only.** No `pip install`, no vendored packages. Scripts must run on a stock Python 3.9+ on Windows, macOS, and Linux.
- **Never print secrets.** Scripts may confirm a key exists (length, prefix), never its value.
- **Documented routes need evidence.** A route claim should state when it was last verified and what it returns.

## PR process

1. Open an issue first for anything beyond a small fix, so the route or change can be discussed before you build it.
2. Fork, branch, commit. Keep the diff focused on one change.
3. In the PR description: what changed, why, and how you tested it (the exact URL or command you verified against, minus anything private).
4. Expect a review within a few days. Small, verifiable PRs merge fastest.

## Code of conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Short version: be decent, assume good faith.
