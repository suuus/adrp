---
name: adrp-write
description: >-
  Draft ADRP records from explicit or strongly evidenced decisions. USE FOR:
  decision-bearing intent in prose, policy, meetings, or conventional ADRs. DO
  NOT USE FOR: generic goals, facts, silent ratification, or invented policy.
license: MIT
metadata:
  version: 0.1.0
  user-invocable: true
---

## Inputs

Use accessible source material, user statements, and existing records. Preserve
literal source locations. Classify source authority separately from location.

## Procedure

1. Resolve the `adrp` CLI and run `--version`.
2. Detect existing `ape-decision-record/v1` documents first. Route those to
   `adrp-read` or `adrp-import`; never duplicate them as candidates.
3. Separate goals, facts, constraints, guidance, and choices.
4. Create a candidate only for an explicit or strongly evidenced choice.
5. Present statement, scope, standing, alternatives, rationale, four-domain
   trade-offs, consequences, autonomy, lifecycle, relationships, and gaps.
6. Ask `Draft`, `Revise`, or `Skip`.
7. On `Draft`, write canonical JSON under a user-approved path with status
   `draft` and `ratification:null`.
8. Use `unknown`, `null`, empty arrays, or `gaps` for missing information.
9. Run `adrp validate --target <draft>` and `adrp fingerprint --target <draft>`.
10. Report the path, identity, fingerprint, and that the draft is inactive.

Never invent authority, people, dates, evidence, policy, or alternatives.
Validation failure leaves no success claim. Do not ratify, commit, or push.

