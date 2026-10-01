---
name: adrp-drift
description: >-
  Read-only ADRP integrity, lifecycle, source, relationship, and implementation
  drift review. USE FOR: stale, changed, expired, superseded, or contradictory
  decisions. DO NOT USE FOR: repairs or silent re-ratification.
license: MIT
metadata:
  version: 0.1.0
  user-invocable: true
---

## Procedure

1. Resolve the `adrp` CLI.
2. Run `adrp verify-set <paths>`.
3. Run `adrp resolve <paths> --as-of <timestamp>` for current standing.
4. Run `adrp graph <paths>` for dependencies, supersession, invalidation, and
   implementation relationships.
5. For imported records, retrieve the current source and run
   `adrp check-source --target <refreshed> --metadata <sidecar>`.
6. Compare implementation and evidence references where accessible.
7. Report:
   - action required;
   - warnings;
   - informational findings;
   - affected decision IDs, record IDs, fingerprints, sources, and evidence.

Tampered, expired, review-due, changed, or unaccepted records are not active.
Changed imports require a new immutable snapshot. Never edit or re-ratify during
drift review.

