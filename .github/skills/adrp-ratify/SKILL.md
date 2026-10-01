---
name: adrp-ratify
description: >-
  Human approval gate for ADRP drafts. USE FOR: creating a new immutable
  ratified version after complete review. DO NOT USE FOR: automated approval,
  specialist certification, overwrite, commits, or pushes.
license: MIT
metadata:
  version: 0.1.0
  user-invocable: true
---

## Gate

Resolve the CLI and validate the draft. Present:

- exact decision statement and scope;
- alternatives, selected option, and rationale;
- authority and provenance;
- security, cost, compliance, and operational trade-offs;
- consequences, risks, implementation, and evidence;
- relationships and dependencies;
- autonomy boundaries;
- lifecycle, gaps, and warnings;
- exact context fingerprint and approval meaning.

Ask `Approve`, `Revise`, or `Stop`.

- **Approve:** run `adrp ratify` to a new `vNNN.json`, run
  `adrp validate --require-ratified`, then `adrp render` to a new Markdown view.
- **Revise:** change only the mutable draft, then repeat validation and review.
- **Stop:** write no ratified artifact.

Silence is not approval. Never overwrite an immutable version. Never claim that
ratification is legal, security, privacy, or compliance certification.

