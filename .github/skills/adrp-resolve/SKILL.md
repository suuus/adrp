---
name: adrp-resolve
description: >-
  Resolve applicable active ADRP records and agent autonomy for a scope or
  proposed action. USE FOR: plans, implementation choices, guardrails, and
  permission questions. DO NOT USE FOR: inventing scope or resolving authority
  conflicts without a human.
license: MIT
metadata:
  version: 0.1.0
  user-invocable: true
---

## Procedure

1. Resolve the `adrp` CLI.
2. Obtain exact scope values; do not broaden or paraphrase them.
3. Run `adrp resolve <paths> --scope "<scope>"`.
4. Inspect `active`, `excluded`, `warnings`, `errors`, and `summary`.
5. If the user proposes an action, run:
   `adrp autonomy <paths> --scope "<scope>" --action "<action>"`.
6. Apply outcomes:
   - `NEVER`: refuse while applicable;
   - `ALWAYS_ASK`: obtain specific approval immediately before action;
   - `PROCEED`: proceed only within the resolved scope;
   - `UNRESOLVED`: ask for clarification or a decision.
7. Retain decision ID, record ID, version, fingerprint, scope, and outcome in the
   plan or trace.

Errors block a resolved-policy claim. Warnings and gaps remain visible. Never
select between genuine authority conflicts by convenience, recency, or source
prestige.

