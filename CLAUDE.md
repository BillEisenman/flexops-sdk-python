# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`flexops` is the **official hand-crafted Python SDK** for the FlexOps Platform. It targets the FlexOps **Gateway BFF**. Published to PyPI as `flexops`; current tag `v1.0.1`. Python 3.10+.

> **Gateway-targeted, not VSCS-targeted.** All hand-crafted SDKs in this family (.NET, Node, Python, Go, PHP, Ruby) hit Gateway. The Java SDK is the lone exception — it was auto-generated against VisionSuiteCoreServices and is archived as of 2026-03-08.

## Build & Run Commands

```bash
pip install -e .                                 # Editable install for local dev
pip install -e ".[dev]"                          # With dev/test extras (if configured)
python -m build                                  # Build sdist + wheel into dist/
python -m pytest                                 # Run tests (if pytest configured)
```

## Architecture

```text
Customer Python app  →  flexops (this repo)  →  Gateway BFF (gateway.flexops.io)
                                                 ↓
                                                 VSCS / Integrations / etc.
```

## Key Directories

| Path | Purpose |
|---|---|
| `src/flexops/` | Package source — client, models, errors |
| `tests/` | Test suite |
| `pyproject.toml` | Build config + project metadata (PEP 621) |
| `dist/` | Build output (sdist + wheel) — generated |
| `CHANGELOG.md` | Per-release notes |

## Conventions

- **Python ≥ 3.10** — use union types `int | None`, structural pattern matching where it clarifies.
- Use `src/` layout (already configured) so tests can't accidentally import from a sibling path.
- Errors come back as typed exception classes carrying Gateway's error envelope — don't raise plain `Exception`.
- License files explicitly listed: `license-files = ["LICENSE"]` (modern PyPI requires this).

## Publish

GitHub Actions handles PyPI publish via **OIDC trusted publishing** (no long-lived `PYPI_TOKEN`). Bump `version` in `pyproject.toml`, tag, push — the workflow does `python -m build` and `twine upload`.

## Related Repositories

| Repository | Purpose |
|---|---|
| **This repo** | `flexops` on PyPI |
| FlexOps Gateway | The HTTP API this SDK calls — `BillEisenman/FlexOpsGateway` |
| Sibling SDKs | `FlexOps.Sdk` (.NET), `@flexops/sdk` (Node), `flexops` (Ruby), `flexops/sdk` (PHP), `flexops-sdk-go` (Go) |
| FlexOps Developer Docs | Hosts the SDK page — `BillEisenman/FlexOpsDeveloperDocs` |
