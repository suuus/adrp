---
name: adrp-import
description: >-
  Preserve external ADRP records verbatim and record local standing in a source
  sidecar. USE FOR: SharePoint, repository, catalogue, or policy-system ADRP
  sources. DO NOT USE FOR: converting prose or modifying source records.
license: MIT
metadata:
  version: 0.1.0
  user-invocable: true
---

## Procedure

1. Resolve the `adrp` CLI.
2. Retrieve the canonical JSON without rewriting it.
3. Run `adrp validate`, `adrp assess`, and `adrp fingerprint`.
4. Present source URI, exact identity, fingerprint, lifecycle, authority, scope,
   and assessment.
5. Ask `Accept`, `Preserve`, or `Ignore`.
6. `Accept` requires eligibility plus explicit local scope confirmation,
   authority acceptance, acceptance basis, and confirming identity.
7. Run `adrp import` with the approved disposition inputs.
8. Validate the new sidecar with `adrp validate-source`.
9. Report snapshot and sidecar paths separately.

Never inject source URI, ETag, retrieval time, or local acceptance into canonical
JSON. Future, expired, review-due, unratified, or authority-unresolved records
cannot be accepted. Do not transfer acceptance to changed bytes.

