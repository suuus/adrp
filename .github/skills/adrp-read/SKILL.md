---
name: adrp-read
description: >-
  Validate, assess, and explain ADRP records. USE FOR: understanding status,
  scope, authority, lifecycle, trade-offs, autonomy, provenance, and gaps. DO
  NOT USE FOR: activation, acceptance, or rewriting immutable records.
license: MIT
metadata:
  version: 0.1.0
  user-invocable: true
---

## Procedure

1. Resolve the `adrp` CLI and run `--version`.
2. Run `adrp inspect <record> [--as-of <timestamp>]`.
3. If inspection fails, report the exact error and treat the record as inactive.
4. Explain:
   - stable decision ID versus immutable record ID/version;
   - status and lifecycle eligibility;
   - scope and authority;
   - alternatives and rationale;
   - security, cost, compliance, and operational trade-offs;
   - consequences, accepted risks, and implementation references;
   - relationships and dependencies;
   - `PROCEED`, `ALWAYS ASK`, and `NEVER`;
   - provenance, gaps, and import disposition.
5. Preserve the exact fingerprint in any downstream reference.

Do not read only `decision_statement`. Do not infer local applicability from
external ratification or source location.

