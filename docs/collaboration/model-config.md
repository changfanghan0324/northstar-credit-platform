# Corrective Collaboration Model Configuration

Date: 2026-08-04

## Required Claude collaborator

- Provider: Anthropic first-party through the authenticated Claude Code installation.
- Claude Code executable: bundled local CLI version `2.1.221`.
- Requested model: `claude-opus-5`.
- Requested effort: `high`.
- Invocation flags: `--model claude-opus-5 --effort high`.
- Fallback model: none. No alias or silent substitution is permitted.

## Runtime verification

A read-only structured diagnostic completed successfully on 2026-08-04:

- Session: `f96be2fb-ccfe-4cc3-9d45-6fa6074442ae`.
- Result: `MODEL_READY`.
- `modelUsage` canonical substantive model: `claude-opus-5`.
- Provider: `firstParty`.
- CLI version: `2.1.221`.

Claude Code may report a small `claude-haiku-4-5` internal routing/tool-use entry in
structured telemetry. That entry is not accepted as substantive proposal, authorship,
or review work. Every qualifying collaboration record must show `claude-opus-5` in
`modelUsage` and name the real session identifier.

## Codex role

Codex is the primary orchestrator and implementation peer. It records proposals,
authorship, review dispositions, validation evidence, and disagreements without
representing itself as an Anthropic model.
