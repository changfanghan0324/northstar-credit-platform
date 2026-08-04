# Model Configuration

## Claude collaborator

- Invocation mechanism: Claude Code CLI 2.1.217, executed inside the Codex workspace terminal.
- Authentication: verified logged in through `claude.ai` first-party account authentication on 2026-08-03; no API key path is being used.
- Requested display configuration: Claude Opus 5, medium effort (the user's latest instruction supersedes the master prompt's earlier High setting).
- CLI selection: `--model claude-opus-5 --effort medium`.
- Resolved model identifier: `claude-opus-5` (verified by structured invocation telemetry on 2026-08-03).
- Fallback model: none. Sonnet, Haiku, older Opus, or another provider must not be selected silently.

### Startup diagnostic

The convenient `--model opus` alias resolved to `claude-opus-4-8`, so that first proposal invocation is explicitly non-qualifying and is excluded from decisions and review credit. The exact `claude-opus-5` endpoint was then tested successfully and is required for all project collaboration. Claude Code may report small internal Haiku routing/tool-use token counts; substantive proposal, implementation, and review output must show `claude-opus-5` in `modelUsage`.

## Codex orchestrator

- Role: primary engineering orchestrator and implementation peer.
- Model identifier: supplied by the Codex host; no alternate provider is being represented as Codex.

## Audit rule

Each recorded Claude review must come from a real CLI invocation. Where the CLI exposes an exact resolved model identifier in structured output, that identifier is recorded here and referenced in review records.
