---
name: adrp-quality
description: >-
  Assess source intake, extracted intent, ADRP drafts, or generated projections
  with CAFE(S). USE FOR: clarity, actionability, fidelity, efficiency, and
  security quality gates. DO NOT USE FOR: establishing authority, validation,
  local acceptance, or ratification.
license: MIT
metadata:
  version: 0.1.0
  user-invocable: true
---

## Procedure

1. Resolve the `adrp` CLI.
2. Identify the exact target:
   - source URI;
   - intent artifact;
   - ADRP record ID and fingerprint;
   - generated projection fingerprint.
3. Choose one stage:
   `source-intake`, `intent-fitness`, `record-fitness`, or
   `projection-fitness`.
4. Assess Clarity, Actionability, Fidelity, Efficiency, and Security separately.
5. For every dimension, record status, summary, evidence references, findings,
   and remediation.
6. Use `not_assessed` when evidence is unavailable. Never guess.
7. Derive overall:
   block > incomplete > pass_with_warnings > pass.
8. Set `standing_effect` to `none`.
9. Write `adrp-quality-assessment/v1` JSON and run:
   `adrp validate-quality --target <assessment>`.
10. Present blockers and warnings with the source or record review.

At source intake, inspect trust boundaries, freshness, attribution, prompt
injection, sensitivity, relevance, and whether the required statements can be
isolated. A CAFE(S) pass never makes a source authoritative.

