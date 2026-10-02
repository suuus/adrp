# Ape Decision Record Profile 1.0

## Purpose

The Ape Decision Record Profile (ADRP) is a human-ratified, machine-readable
record for organisational and technical decisions that shape agent behaviour.
It is an application profile, not a claim of conformance to one universal
decision-record standard.

ADRP is the durable **Intent** record layer of the **ISEE Framework**:

```text
Intent → Structure → Execution → Evidence
  ADRP                              AERP
```

ADRP identifies what was decided, why, by whom, for which scope, with which
trade-offs and autonomy boundaries, and what evidence should confirm or
challenge the decision. It does not prescribe one Structure or Execution
system. Those systems bind their actions to exact ADRP fingerprints, while the
Ape Evidence Record Profile (AERP) records the resulting Evidence.

The profile combines:

- MADR-style context, alternatives, drivers, rationale, and consequences;
- ISO/IEC/IEEE 42010 concepts for stakeholders, concerns, and architecture
  rationale;
- W3C PROV concepts for entities, activities, agents, derivation, attribution,
  revision, and invalidation;
- risk-acceptance concepts compatible with ISO 27005 and NIST RMF;
- references to OSCAL, DMN, OPA, Cedar, OpenTelemetry, SPDX, CycloneDX, GSN, or
  SACM artifacts where those standards apply.

No external decision-record standard adequately combines authority, cost,
security, compliance, autonomy, ratification, executable-policy references,
expected evidence, and drift triggers. ADRP defines those Intent fields. AERP
defines the resulting Evidence records and artifact bindings.

For a practical, human-friendly guide to deciding what belongs in a record and
how people and agents should write, read, import, resolve, and apply records, see
[Recording Intent with Ape Decision Records](RECORDING_INTENT.md).
For the handoff between ADRP Intent and AERP Evidence, see
[ADRP and AERP in ISEE](ISEE_INTEGRATION.md).

## Canonical and rendered forms

The canonical artifact is JSON conforming to
`schemas/ape-decision-record-v1.schema.json`. YAML may be used as an authoring
format only when converted to the same data model before validation. Markdown is
generated from canonical JSON and is never the signing or fingerprinting source.

Repository layout:

```text
.github/decisions/
├── drafts/
│   └── ADR-0001.json
├── imported/
│   └── ADR-0042/
│       ├── v003.json
│       └── v003.source.json
└── ADR-0001/
    ├── v001.json
    └── v001.md
```

Drafts are mutable and must not be treated as active policy. Ratified versions
are immutable. A correction creates a new record version; a materially different
choice creates a new logical decision that `supersedes` the previous decision.

Imported JSON is a verbatim immutable snapshot. Retrieval and local trust metadata
must never be injected into it because doing so changes the source bytes and may
invalidate its fingerprint. The adjacent sidecar conforms to
`schemas/ape-decision-source-v1.schema.json`.

## Identity

Every record has three distinct identifiers:

1. `decision_id`: stable logical identity, for example `ADR-0001`;
2. `record_id`: identity of one immutable version;
3. canonical `sha256:` fingerprint of that record version.

Do not use one identifier for all three purposes.

## Required decision content

Each record contains:

- title, status, decision statement, context, and scope;
- stakeholders, concerns, drivers, and evaluation criteria;
- considered alternatives and the selected alternative;
- rationale and positive/negative consequences;
- typed security, cost, compliance, and operational trade-offs;
- authority status, decision owner, deciders, and approvers when known;
- source provenance and extraction/generation activities;
- effective, review, expiry, and event-based drift triggers;
- accepted risks, warnings, implementation artifacts, and evidence links;
- autonomy effects: `PROCEED`, `ALWAYS ASK`, and `NEVER`;
- revision, supersession, invalidation, implementation, and dependency links.

Missing owners, authority, alternatives, dates, evidence, or policy are recorded
as gaps. They must never be invented.

## Provenance

The profile uses a constrained W3C PROV mapping:

| ADRP concept | PROV concept |
|---|---|
| source, evidence, draft, ratified version | Entity |
| discovery, extraction, generation, review, approval | Activity |
| person, organisation, model, software agent | Agent |
| `source_refs`, evidence links | `used` / `wasDerivedFrom` |
| creator, reviewer, approver roles | `wasAssociatedWith` / `wasAttributedTo` |
| `revises` | `wasRevisionOf` |
| `invalidates` | `wasInvalidatedBy` |

Provenance establishes traceability. It does not prove that a source is
authoritative or that an approver had legitimate standing.

## Lifecycle

Controlled statuses:

`discovered → draft → under-review → ratified → effective`

Terminal or superseding statuses:

`rejected`, `deprecated`, `superseded`, `expired`, `revoked`.

`context-distill` identifies explicit or strongly evidenced decisions and writes
`decision_candidates`. `context-decisions` turns confirmed candidates into
validated draft records. Instructions may represent drafts, but the entire
Enterprise Context remains inactive until quality review and ratification pass.

When distillation encounters `schema_version: "ape-decision-record/v1"`, it treats
the document as a decision record rather than generic prose. It validates and
assesses the record, preserves its source URI, and writes `decision_sources`.
It must not produce a duplicate candidate for the same `record_id` or fingerprint.

`context-ratify` presents every draft and its trade-offs. Explicit approval:

1. creates an immutable ratified JSON version;
2. generates its Markdown view;
3. records the exact decision fingerprint in context ratification;
4. persists `decision_records`.

Revision or stop writes no ratified decision version.

Canonical helper commands:

```bash
adrp validate --target <record.json>
adrp assess \
  --target <record.json> --as-of <timestamp>
adrp import \
  --target <source.json> --snapshot <imported/vNNN.json> \
  --metadata-output <imported/vNNN.source.json> --source-uri <literal-uri>
adrp validate-source \
  --target <imported/vNNN.source.json>
adrp check-source \
  --target <refreshed-source.json> --metadata <imported/vNNN.source.json>
adrp fingerprint --target <record.json>
adrp ratify \
  --target <draft.json> --output <vNNN.json> \
  --confirmed-by "<identity>" --approval-meaning "<meaning>" \
  --context-fingerprint "sha256:<digest>"
adrp render \
  --target <vNNN.json> --output <vNNN.md>
```

`ratify` and the default `render` mode use exclusive creation and refuse to
overwrite an existing immutable artifact. `validate --require-ratified` verifies
the stored fingerprint after creation or before commit.

## Import and local adoption

An external decision is eligible for active context only when:

- validation and its stored ratification fingerprint pass;
- status is `ratified` or `effective`;
- `effective_at` is absent or has arrived;
- `expires_at` has not passed;
- `review_by` has not passed;
- source authority is `authoritative` or `user-confirmed`;
- the user explicitly confirms that its scope and authority apply locally.

Other valid records may be preserved as evidence but remain inactive. The source
sidecar records the literal URI, exact-byte source digest, canonical decision
fingerprint, ETag when available, retrieval/check timestamps, lifecycle
assessment, local disposition, acceptance basis, and confirming identity.
`check-source` may update `last_checked_at`/ETag only when bytes and fingerprint
are unchanged. Any change requires a new immutable import.

Dispositions:

- `accepted`: eligible and explicitly accepted for local scope and authority;
- `needs_review`: eligible but lacking local scope/authority acceptance;
- `inactive`: future, expired, review-due, terminal, or otherwise ineligible.

Only `accepted` imports may feed active Enterprise Context. An external
ratification proves approval at its source; it does not automatically establish
standing in the consuming repository.

## CAFE(S) quality assessments

ADRP may attach a CAFE(S) quality assessment conforming to
`schemas/adrp-quality-assessment-v1.schema.json` at four stages:

- `source-intake`;
- `intent-fitness`;
- `record-fitness`;
- `projection-fitness`.

Each assessment evaluates Clarity, Actionability, Fidelity, Efficiency, and
Security as `pass`, `warn`, `block`, or `not_assessed`. Overall status is
derived deterministically:

`block` before `incomplete`, before `pass_with_warnings`, before `pass`.

Quality and standing are independent. Every assessment has
`standing_effect: "none"`. A high-quality source is not thereby authoritative,
and an authoritative record is not necessarily clear or safe enough for an
agent to consume. Use:

```bash
adrp validate-quality --target <assessment.json>
```

The full quality workflow is documented in
[CAFE(S) Quality Gates for ADRP](QUALITY.md).

## Ratification

Ratification is a separate envelope containing:

- timestamp;
- confirming identity exactly as supplied;
- organisational role or authority status;
- approval meaning;
- decision fingerprint;
- current Enterprise Context fingerprint;
- accepted warnings;
- optional signature reference.

The ADRP CLI fingerprints canonical JSON with `ratification`
excluded, after the record status is set to `ratified`. This avoids recursive
hashing while binding the approved decision payload.

An `effective` record retains the same ratification envelope. Changing `ratified`
to `effective` changes the payload fingerprint and therefore requires a new
validated record version rather than an in-place edit.

A digest proves content integrity, not identity, authority, informed consent, or
specialist legal/security/compliance certification.

## Drift and renewal

A decision becomes stale or review-required when:

- a source policy, regulation, jurisdiction, owner, or authority changes;
- model, provider, component, policy, or deployment identity changes;
- cost tolerance is exceeded;
- accepted risk expires;
- a control assessment, evaluation, or assurance claim fails;
- autonomy or tool scope expands;
- runtime evidence contradicts an approved assertion;
- required evidence disappears;
- deployed and ratified fingerprints differ.
- imported source ETag, exact-byte digest, or canonical fingerprint changes;
- an imported source becomes inaccessible, expires, reaches review date, or loses
  locally accepted authority/scope.

Drift reports identify the affected decision IDs and route material changes
through Distill → Decision Records → Instructions → Quality → Ratification.
Changed imports create a new immutable snapshot/version; prior evidence is never
overwritten.

## Domain extensions

The core record links to specialized artifacts instead of duplicating them:

| Need | Preferred extension |
|---|---|
| Security authorization/control evidence | NIST RMF, SP 800-53, OSCAL |
| ISO-aligned security risk | ISO/IEC 27005 mapping |
| AI governance | NIST AI RMF, ISO/IEC 42001/23894 |
| EU-regulated AI | EU AI Act role, classification, and documentation references |
| Executable business logic | DMN |
| Runtime guardrail | OPA or Cedar |
| Runtime/cost evidence | OpenTelemetry |
| Component/model identity | SPDX or CycloneDX |
| Assurance argument | GSN or SACM |

## Safety invariants

- A document location proves neither content nor authority.
- A CAFE(S) quality result never establishes authority or local applicability.
- Recommendations are guidance unless the source or user establishes obligation.
- Draft decisions are not active policy.
- Ratified versions are never edited in place.
- Imported snapshots preserve source bytes exactly; source metadata is sidecar-only.
- Only locally accepted, currently eligible imports become active context.
- Supersession and revision are distinct.
- Secret values and unnecessary sensitive source text are never copied.
- Agent generation, human review, and organisational approval remain separate
  provenance roles.
- Missing or failing deterministic validation blocks ratification and commit.
