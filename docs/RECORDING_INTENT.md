# Recording Intent with Ape Decision Records

## A human and agent guide to writing, reading, and processing organisational intent

Organisations rarely suffer from a complete absence of intent. More often, the
intent is scattered across strategy documents, policies, architecture decisions,
meeting notes, issue trackers, approval threads, and the memories of people who
were present when a choice was made.

Humans can sometimes work around that fragmentation. They ask a colleague, infer
the missing context, or remember why a rule exists. Agents cannot safely rely on
those informal recovery mechanisms. If an agent is expected to plan, write code,
review a change, deploy infrastructure, or operate a service, it needs intent in
a form that is:

- attributable to a source;
- explicit about scope and authority;
- honest about uncertainty and missing information;
- clear about alternatives and trade-offs;
- usable as an autonomy boundary;
- reviewable over time;
- safe to process deterministically.

The **Ape Decision Record Profile (ADRP)** is a standard for that purpose. Its
canonical schema identifier is:

```text
ape-decision-record/v1
```

ADRP is not merely a nicer Architecture Decision Record. It is a
human-ratified, machine-readable record of a choice that carries organisational
intent into agent behaviour.

This guide explains how people and agents should create, interpret, adopt, use,
review, and retire those records. The normative field definitions and lifecycle
rules remain in the
[Ape Decision Record Profile](STANDARD.md) and its
[JSON Schema](../schemas/ape-decision-record-v1.schema.json).

## How to use this guide

- **If you are deciding whether something needs a record**, start with
  [The central idea](#1-the-central-idea-intent-is-broader-than-a-decision).
- **If you are writing a record by hand**, use the
  [human authoring workflow](#6-human-authoring-workflow) and the
  [worked example](#17-worked-example).
- **If you are building an agent that creates records**, follow
  [How an agent should write a record](#7-how-an-agent-should-write-a-record).
- **If you are building an agent that consumes records**, follow
  [How an agent should read a record](#8-how-an-agent-should-read-a-record) and
  [How an agent should process records into action](#9-how-an-agent-should-process-records-into-action).
- **If records originate outside the repository**, read
  [External records and source-linked adoption](#11-external-records-and-source-linked-adoption).
- **If you operate or audit the system**, use the
  [lifecycle and drift](#13-lifecycle-drift-and-renewal),
  [security and privacy](#14-security-and-privacy-rules), and
  [agent processing checklist](#16-agent-processing-checklist) sections.

### Contents

1. [The central idea: intent is broader than a decision](#1-the-central-idea-intent-is-broader-than-a-decision)
2. [What ADRP adds to a conventional ADR](#2-what-adrp-adds-to-a-conventional-adr)
3. [The three forms of recorded intent](#3-the-three-forms-of-recorded-intent)
4. [Repository layout and immutability](#4-repository-layout-and-immutability)
5. [Anatomy of an Ape Decision Record](#5-anatomy-of-an-ape-decision-record)
6. [Human authoring workflow](#6-human-authoring-workflow)
7. [How an agent should write a record](#7-how-an-agent-should-write-a-record)
8. [How an agent should read a record](#8-how-an-agent-should-read-a-record)
9. [How an agent should process records into action](#9-how-an-agent-should-process-records-into-action)
10. [From records to agent instructions](#10-from-records-to-agent-instructions)
11. [External records and source-linked adoption](#11-external-records-and-source-linked-adoption)
12. [Conventional ADRs and unstructured sources](#12-conventional-adrs-and-unstructured-sources)
13. [Lifecycle, drift, and renewal](#13-lifecycle-drift-and-renewal)
14. [Security and privacy rules](#14-security-and-privacy-rules)
15. [Command reference](#15-command-reference)
16. [Agent processing checklist](#16-agent-processing-checklist)
17. [Worked example](#17-worked-example)
18. [The safety invariants](#18-the-safety-invariants)

---

## 1. The central idea: intent is broader than a decision

Intent describes what an organisation is trying to achieve and the boundaries
within which work should happen. It can include:

- desired outcomes;
- principles;
- obligations;
- constraints;
- priorities;
- accepted risks;
- operating assumptions;
- autonomy boundaries;
- explicit choices.

Not every expression of intent is a decision record.

An ADRP record is appropriate when the organisation has made, or needs to make,
a meaningful choice that agents and people may need to apply later. The record
captures not only *what* was chosen, but also:

- why the choice exists;
- which alternatives were considered;
- who had standing to decide;
- what security, cost, compliance, and operational trade-offs were accepted;
- where the choice applies;
- what an agent may do, must ask about, or must never do;
- when the choice becomes effective, must be reviewed, or expires;
- what evidence can confirm or challenge it.

This distinction prevents two dangerous errors:

1. **Promoting every sentence into policy.** A recommendation, observation, or
   document location does not automatically become an authoritative decision.
2. **Reducing decisions to instructions.** An instruction such as "always run
   security scanning" is incomplete if nobody can tell where it came from, who
   approved it, what it applies to, or when it should be reconsidered.

### 1.1 A useful test

Create or identify a decision record when most of these questions matter:

- Was there a choice between plausible alternatives?
- Does the choice constrain future work?
- Could applying it incorrectly create security, cost, compliance, operational,
  architectural, or product consequences?
- Does an agent need to know whether it can proceed autonomously?
- Will somebody later need to understand why the choice was made?
- Could the choice expire, drift, be superseded, or become invalid?
- Does authority or local applicability need to be proved?

If the answer is mostly no, keep the item as sourced intent, a constraint,
guidance, a fact, or a gap instead of forcing it into ADRP.

### 1.2 Examples

| Source statement | Classification | Why |
|---|---|---|
| "Reduce checkout abandonment this quarter." | Intent | It states an outcome, but not a durable choice. |
| "EU customer data must remain in approved EU regions." | Constraint | It may be an obligation without representing a locally made choice. |
| "The platform team recommends PostgreSQL." | Guidance | A recommendation is not automatically authoritative. |
| "We selected PostgreSQL over Cosmos DB because relational consistency and existing operational skills outweigh global distribution." | Decision candidate | It records a choice, alternatives, and rationale. |
| "Production deployments require a passing security gate; residual risk acceptance always requires a named human approver." | Decision record | It carries intent, authority, trade-offs, and autonomy boundaries into execution. |
| "The SharePoint architecture folder contains the standards." | Source location | Location proves where something was found, not whether it is authoritative. |

---

## 2. What ADRP adds to a conventional ADR

Conventional ADR formats are valuable for recording architecture choices. ADRP
retains that useful core and adds the information an agentic operating model
needs.

| Conventional concern | ADRP extension |
|---|---|
| Context and decision | Explicit scope, stakeholders, concerns, and drivers |
| Alternatives and rationale | Structured alternatives with benefits, drawbacks, and rejection reasons |
| Consequences | Security, cost, compliance, and operational trade-offs |
| Status | Effective dates, review dates, expiry, and event-based triggers |
| Author | Separate source, extraction agent, decision owner, decider, approver, and confirmer roles |
| Record history | Stable decision identity, immutable version identity, revision, supersession, and invalidation |
| Human-readable narrative | Canonical machine-readable JSON plus generated Markdown |
| Approval | Fingerprint-bound ratification tied to the exact Enterprise Context |
| Agent use | `PROCEED`, `ALWAYS ASK`, and `NEVER` autonomy boundaries |
| External reuse | Verbatim source snapshot plus local acceptance sidecar |
| Ongoing validity | Evidence references, source refresh, tamper checks, and drift triggers |

ADRP deliberately keeps **content integrity**, **source provenance**,
**organisational authority**, and **local acceptance** separate. A cryptographic
digest can prove that content has not changed. It cannot prove that the source
was correct, that an approver had authority, or that a decision made elsewhere
applies in this repository.

---

## 3. The three forms of recorded intent

An ADRP-aware workflow processes intent in three related but distinct forms.

### 3.1 Distilled intent

`context-distill` extracts sourced items into:

```text
distilled_intent:
  intent[]
  constraints[]
  autonomy[]
  topology[]
  gaps[]
```

These items should retain a statement, kind, source, authority status, and any
known owner, scope, or lifecycle dates. They are useful even when no decision
has been made.

### 3.2 Decision candidates

`decision_candidates` are sourced items that appear to contain a meaningful
choice. They still require human confirmation. A candidate should normally
contain enough evidence to discuss:

- the proposed decision statement;
- standing and authority;
- alternatives;
- rationale;
- consequences;
- cross-domain trade-offs;
- autonomy effects;
- lifecycle and review triggers;
- unresolved gaps.

A candidate is not active policy and must not be silently upgraded into one.

### 3.3 Canonical Ape Decision Records

Confirmed candidates become canonical ADRP JSON drafts. Encountered external
ADRP documents become source-linked imports. Both are validated
deterministically, but they follow different trust paths:

- **Local draft:** created in the repository, reviewed, and ratified locally.
- **External record:** preserved byte-for-byte, assessed, and explicitly
  accepted or preserved for local use.

Only a ratified local record or a currently eligible and locally accepted import
may contribute active decision context.

---

## 4. Repository layout and immutability

```text
.github/decisions/
├── drafts/
│   └── ADR-SECURITY-GATE.json
├── imported/
│   └── ADR-DATA-RESIDENCY/
│       ├── v003.json
│       └── v003.source.json
└── ADR-SECURITY-GATE/
    ├── v001.json
    └── v001.md
```

### Drafts

`.github/decisions/drafts/*.json`

- Mutable while the choice is being clarified.
- Must have `ratification: null`.
- May have status `discovered`, `draft`, or `under-review`.
- Must not be treated as active policy.

### Ratified local versions

`.github/decisions/<decision-id>/vNNN.json`

- Immutable after creation.
- Bound to a canonical record fingerprint.
- Bound to the Enterprise Context fingerprint reviewed at ratification.
- Accompanied by generated Markdown for human reading.
- Corrected through a new version, never an in-place edit.

### Imported external versions

`.github/decisions/imported/<decision-id>/vNNN.json`

- Exact byte-for-byte snapshot of the external canonical record.
- Never modified to add local metadata.
- Accompanied by a `.source.json` sidecar containing retrieval, trust, lifecycle,
  and local acceptance information.

This separation matters. If an agent inserts a SharePoint URL, local approval,
or refresh timestamp into the imported JSON, the source bytes no longer match
the source record. Provenance has been damaged rather than improved.

---

## 5. Anatomy of an Ape Decision Record

The canonical artifact is JSON. Markdown is a generated view, not the source of
truth.

### 5.1 Identity

| Field | Meaning |
|---|---|
| `schema_version` | Must be exactly `ape-decision-record/v1`. |
| `decision_id` | Stable logical identity, such as `ADR-SECURITY-GATE`. |
| `record_id` | UUID identifying one immutable record version. |
| `record_version` | Positive integer version of the logical decision. |

Do not use these identifiers interchangeably. An agent may cite the stable
`decision_id` in instructions, but integrity checks and evidence should also
retain the exact `record_id`, version, and fingerprint.

### 5.2 Decision content

| Field | Question it answers |
|---|---|
| `title` | What is this decision called? |
| `decision_statement` | What was actually chosen? |
| `context.problem` | What problem made the choice necessary? |
| `context.scope` | Where does it apply? |
| `context.stakeholders` | Who is affected or has a legitimate concern? |
| `context.concerns` | Which concerns shaped the decision? |
| `drivers` | What criteria had to be satisfied, and which sources support them? |
| `alternatives` | What other plausible choices were considered? |
| `selected_alternative` | Which alternative was selected? |
| `rationale` | Why did the selected alternative win? |

The decision statement should be testable enough that a future reader can tell
whether a proposed action complies with it. Avoid slogans such as "be secure" or
"use the cloud responsibly."

### 5.3 Trade-offs

Every record explicitly addresses:

- security;
- cost;
- compliance;
- operations.

Each domain records:

- an impact classification: `positive`, `negative`, `mixed`, `neutral`, or
  `unknown`;
- a summary;
- evidence references;
- accepted risks.

`unknown` is valid and preferable to invention. An empty cost impact should not
be rewritten as "neutral" unless a source or qualified reviewer supports that
conclusion.

### 5.4 Authority

The authority block separates provenance from standing:

```json
{
  "authority_status": "authoritative",
  "decision_owner": "Security",
  "deciders": ["Head of Platform"],
  "approvers": ["Chief Information Security Officer"],
  "delegation_ref": "policy://security/delegations/production-risk"
}
```

Allowed authority states are:

- `authoritative`;
- `advisory`;
- `conflicting`;
- `unknown`;
- `user-confirmed`.

An agent must never infer `authoritative` from a prestigious filename, a
SharePoint location, the identity of the uploader, or the presence of a logo.
When standing cannot be established, record `unknown` and add a gap.

### 5.5 Provenance

Provenance records:

- the source entities used;
- the discovery, extraction, generation, review, approval, or invalidation
  activities performed;
- the people, organisations, software agents, or models involved.

It should distinguish at least:

- who authored or owned the source;
- which software agent extracted or generated the draft;
- on whose behalf the agent acted, if known;
- who reviewed or approved the result.

Agent generation is not human approval. Human approval is not proof of specialist
security, legal, privacy, or compliance certification.

### 5.6 Lifecycle

| Field | Meaning |
|---|---|
| `created_at` | When this version was created. |
| `effective_at` | When it may start applying. |
| `review_by` | Latest date by which continued validity must be reviewed. |
| `expires_at` | When it stops being eligible. |
| `review_triggers` | Events that require reconsideration before a calendar date. |

Useful event triggers include:

- a regulation or policy changes;
- the decision owner changes;
- a model, provider, jurisdiction, or deployment topology changes;
- autonomy or tool permissions expand;
- a cost threshold is exceeded;
- required evidence disappears;
- runtime evidence contradicts an assumption;
- an accepted risk reaches its review date.

### 5.7 Consequences and implementation

`consequences` records positive outcomes, negative outcomes, risks, and required
actions. `implementation` links the decision to executable policy, artifacts,
and evidence.

The decision record should not duplicate an entire OPA policy, OSCAL assessment,
runbook, or telemetry stream. Link to the specialised artifact and preserve the
decision that explains why it exists.

### 5.8 Relationships

ADRP distinguishes:

- `revises`: corrects or refines an earlier version of the same logical choice;
- `supersedes`: replaces a previous decision with a materially different choice;
- `invalidates`: records that another record or claim can no longer be relied on;
- `implements`: identifies higher-level intent or decisions this record puts
  into practice;
- `depends_on`: identifies decisions that must remain valid for this one to hold.

Revision and supersession are not synonyms. Agents should preserve that
distinction when building decision graphs.

### 5.9 Autonomy

The autonomy block translates intent into agent boundaries:

```json
{
  "proceed": [
    "Run read-only security analysis"
  ],
  "always_ask": [
    "Accept residual security risk"
  ],
  "never": [
    "Deploy while blocking security findings remain"
  ]
}
```

Interpretation:

- **PROCEED**: the agent may perform the action within the recorded scope.
- **ALWAYS ASK**: a human decision is required each time; prior approval of the
  record is not blanket approval for the action.
- **NEVER**: the action is structurally forbidden while the record is active.

When multiple active records apply, the more restrictive applicable boundary
wins until the conflict is resolved. An agent must not use a broad `PROCEED` to
override a scoped `ALWAYS ASK` or `NEVER`.

### 5.10 Gaps and ratification

`gaps` is where uncertainty is made visible. Examples:

- named approver not supplied;
- review date not established;
- cost impact unassessed;
- source authority unresolved;
- evidence link unavailable;
- local scope not confirmed.

A gap is not an invitation for an agent to guess.

Drafts use `ratification: null`. Ratified records contain a separate envelope
with:

- the confirming identity;
- authority role, when supplied;
- approval meaning;
- timestamp;
- exact record fingerprint;
- exact Enterprise Context fingerprint;
- accepted warnings;
- optional external signature reference.

---

## 6. Human authoring workflow

### Step 1: start with a real choice

Write one sentence describing the choice, not the aspiration:

> Every production deployment requires a passing security gate.

Then state the problem:

> Agents can otherwise deploy changes without the security review required by
> production policy.

If these statements cannot yet be written without speculation, keep the item as
a candidate or gap.

### Step 2: establish sources before authority

Record the source URI exactly as it was retrieved. Then classify authority
separately.

Good:

```text
Source: sharepoint://security/policy/production-deployment
Authority: authoritative
Basis: policy owner and delegation reference confirmed
```

Unsafe:

```text
Source: SharePoint security folder
Authority: authoritative because it was in the security folder
```

### Step 3: record alternatives honestly

Include plausible alternatives, including "do nothing" when it was genuinely an
option. Do not manufacture alternatives after the fact merely to make the record
look rigorous.

For each alternative, record:

- what it means;
- benefits;
- drawbacks;
- why it was rejected, or `null` for the selected alternative.

### Step 4: expose the trade-offs

Ask four explicit questions:

1. What changes for security?
2. What changes for cost?
3. What changes for compliance?
4. What changes for operations?

If a domain was not assessed, say `unknown`. That creates a reviewable gap instead
of false confidence.

### Step 5: define agent autonomy

Write autonomy entries as concrete actions, not abstract values.

Weak:

```text
PROCEED: normal work
ALWAYS ASK: risky things
NEVER: unsafe behaviour
```

Strong:

```text
PROCEED: Run read-only security analysis against the proposed deployment.
ALWAYS ASK: Accept or waive a residual production security finding.
NEVER: Deploy while a blocking security finding remains unresolved.
```

### Step 6: add lifecycle and evidence

Every durable decision should identify what could make it stale. Use a review
date when validity naturally decays and event triggers when a specific change
matters more than elapsed time.

Link to evidence that can challenge the decision. For a security gate, that
might include analyzer output, waiver records, deployment audit events, or
incident findings.

### Step 7: validate before review

```bash
adrp validate \
  --target .github/decisions/drafts/ADR-SECURITY-GATE.json
```

Validation is necessary but not sufficient. It proves that the record satisfies
the deterministic contract. It does not prove that the decision is wise,
authoritative, complete, or approved.

### Step 8: review and ratify separately

The reviewer should see:

- decision statement and scope;
- alternatives and rationale;
- authority and provenance;
- all four trade-off domains;
- consequences and accepted risks;
- autonomy boundaries;
- lifecycle and review triggers;
- gaps and warnings;
- the Enterprise Context that will carry the decision.

Approval creates a new immutable version. It must never overwrite the draft or
an earlier ratified version.

---

## 7. How an agent should write a record

An agent may discover, extract, structure, validate, and render a decision. It
must not silently manufacture authority or claim ratification.

### 7.1 Agent authoring algorithm

```text
1. Read only the accessible, in-scope sources supplied or discovered.
2. Preserve each literal source location and available digest.
3. Separate facts, goals, constraints, guidance, and choices.
4. If the source is already ape-decision-record/v1:
   a. validate it;
   b. assess lifecycle and authority;
   c. record it as a decision source;
   d. do not create a duplicate candidate.
5. For ordinary prose, create a decision candidate only when a choice is
   explicit or strongly evidenced.
6. Present the candidate to a human with sources, standing, alternatives,
   trade-offs, autonomy effects, lifecycle, and gaps.
7. On "Draft", create canonical JSON with status draft and ratification null.
8. Use unknown, null, empty arrays, or gaps for missing information.
9. Run deterministic validation and fingerprinting.
10. Do not activate, ratify, commit, or push unless the relevant workflow and
    human approval explicitly permit it.
```

### 7.2 Rules for generation

An agent writing ADRP must:

- preserve exact identifiers and source references;
- use a new UUID for a new immutable record version;
- ensure `selected_alternative` references an existing alternative ID;
- ensure provenance activities reference known source and agent IDs;
- distinguish source authority from decision authority;
- keep all unconfirmed people, roles, dates, and evidence out of the record;
- put unresolved information in `gaps`;
- use `ratification: null`;
- validate before reporting success.

An agent must not:

- infer authority from document location;
- turn recommendations into obligations;
- invent a decision owner or approver;
- claim a draft is active;
- set a ratified or effective status without a valid ratification envelope;
- copy secrets or unnecessary sensitive text from a source;
- rewrite an imported record to fit the local repository;
- use a generated Markdown rendering as the canonical input.

### 7.3 Candidate presentation pattern

Before drafting, an agent should present a compact but complete review:

```text
Proposed decision:
  Every production deployment requires a passing security gate.

Source and standing:
  Production Security Policy
  sharepoint://security/policy
  Authority: authoritative

Alternatives:
  1. Blocking security gate
  2. Advisory-only review

Selected alternative and rationale:
  Blocking gate, because the source policy requires review before production.

Trade-offs:
  Security: positive
  Cost: mixed
  Compliance: positive
  Operations: mixed

Autonomy:
  PROCEED: read-only analysis
  ALWAYS ASK: residual-risk acceptance
  NEVER: deployment with blocking findings

Gaps:
  Named human approver is not yet supplied.

Choose: Draft, Revise, or Skip.
```

The human choice is part of the workflow evidence. Silence is not approval.

---

## 8. How an agent should read a record

Reading ADRP is not equivalent to extracting the `decision_statement` and
ignoring the rest. An agent should process the record in a fail-closed order.

### 8.1 Recognition

Treat a JSON document as ADRP only when:

```json
{
  "schema_version": "ape-decision-record/v1"
}
```

Do not guess based on filename or shape.

### 8.2 Validation

Run:

```bash
adrp validate --target <record.json>
```

For a local ratified version:

```bash
adrp validate \
  --target <record.json> \
  --require-ratified
```

If validation fails:

- do not use the record as active policy;
- report the exact failure;
- preserve the source reference;
- classify the item as invalid, tampered, or requiring review;
- do not "repair" a ratified or imported artifact in place.

### 8.3 Lifecycle and authority assessment

Run:

```bash
adrp assess \
  --target <record.json> \
  --as-of 2026-10-01T12:00:00Z
```

Possible eligibility results:

| Result | Agent treatment |
|---|---|
| `eligible` | Continue to local standing and scope checks. |
| `inactive` | Preserve if useful, but do not apply. |
| `not_yet_effective` | Do not apply before `effective_at`. |
| `expired` | Do not apply; request renewal or replacement. |
| `review_required` | Do not treat as current without review. |
| `authority_review_required` | Do not activate until authority is resolved. |

### 8.4 Local versus imported standing

For a local record, verify its ratification fingerprint and its relationship to
the current Enterprise Context.

For an imported record, validate both files:

```bash
adrp validate \
  --target .github/decisions/imported/ADR-DATA-RESIDENCY/v003.json \
  --require-ratified

adrp validate-source \
  --target .github/decisions/imported/ADR-DATA-RESIDENCY/v003.source.json
```

An imported record is active only when the sidecar says:

```json
{
  "assessment": {
    "eligibility": "eligible"
  },
  "local_disposition": "accepted",
  "scope_confirmed": true,
  "authority_accepted": true
}
```

External approval is evidence about the source organisation. It is not automatic
approval for the consuming repository.

### 8.5 Applicability

Before applying a valid and active record, an agent should ask:

- Does the current action fall within `context.scope`?
- Does the record apply to this repository, product, environment, jurisdiction,
  deployment tier, or agent?
- Are all `depends_on` decisions still active?
- Has another active record superseded or invalidated it?
- Is there a conflicting applicable record?
- Does a more restrictive autonomy boundary apply?

If applicability is ambiguous, the action moves to `ALWAYS ASK`; ambiguity does
not broaden authority.

---

## 9. How an agent should process records into action

The safest processing model has five stages:

```text
Recognise -> Validate -> Assess -> Resolve -> Apply
```

### 9.1 Recognise

- Detect canonical ADRP by schema version.
- Keep ordinary prose, conventional ADRs, policies, and recommendations as
  tagged sources until they are explicitly converted.
- Deduplicate by `record_id` and canonical fingerprint, not title alone.

### 9.2 Validate

- Enforce the exact schema and semantic integrity checks.
- Verify ratification fingerprints for ratified/effective records.
- Validate import sidecars separately.
- Treat malformed or tampered records as non-active.

### 9.3 Assess

- Evaluate status, effective date, review date, expiry, and authority.
- For imports, evaluate local disposition, scope confirmation, and authority
  acceptance.
- Check source refresh state and accessibility when required.

### 9.4 Resolve

Build the applicable decision set:

1. Filter to active, eligible records.
2. Filter by current scope.
3. Resolve revision and supersession relationships.
4. Verify dependencies.
5. Surface conflicts rather than selecting the most convenient record.
6. Merge autonomy boundaries conservatively:
   `NEVER` outranks `ALWAYS ASK`, which outranks `PROCEED`.
7. Keep gaps and accepted warnings attached to the resulting instruction.

No timestamp, version number, or source prestige should be used as an invented
conflict-resolution rule. A genuine authority conflict requires human review.

### 9.5 Apply

An agent may use an applicable record to:

- generate or refine repository instructions;
- select allowed implementation paths;
- configure a policy or quality gate;
- decide whether an action can proceed autonomously;
- require human approval;
- block a prohibited operation;
- attach rationale and evidence to a plan or pull request;
- identify required checks;
- monitor drift against implementation and evidence references.

When applying a record, retain a trace such as:

```text
Applied decision:
  decision_id: ADR-SECURITY-GATE
  record_id: 849535a2-fb8d-4a59-a9ea-d01ff9b7b460
  record_version: 1
  fingerprint: sha256:...
  scope: production deployments
  result: blocking security gate required
```

This enables a future reviewer to reconstruct why the agent acted.

---

## 10. From records to agent instructions

ADRP records are richer than the instructions an agent needs in every prompt.
An integrating system should therefore project the active decision set into a
concise, scoped instruction or policy context.

The generated instructions should include:

- applicable decision IDs and statuses;
- source or imported snapshot references;
- current fingerprints;
- scope and authority;
- review and expiry information;
- concise constraints;
- `PROCEED`, `ALWAYS ASK`, and `NEVER` boundaries;
- unresolved conflicts, warnings, and standing gaps.

The instruction layer should not copy:

- full source documents;
- every rejected alternative;
- unnecessary personal or sensitive information;
- secret values;
- an entire decision graph when only a scoped subset applies.

This is where CAFE(S) becomes important:

- **Clarity:** can the agent interpret the projected rule?
- **Actionability:** does it know what to do or when to stop?
- **Fidelity:** can the instruction be traced to the exact active record?
- **Efficiency:** is only relevant decision context included?
- **Security:** is sensitive or untrusted source content excluded?

The decision record preserves depth. The generated instruction preserves focus.

---

## 11. External records and source-linked adoption

An organisation may publish ADRP records in SharePoint, another repository, an
architecture catalogue, or a policy system. ADRP-aware systems import those
records without rewriting them.

### 11.1 Import without local acceptance

```bash
adrp import \
  --target /tmp/ADR-DATA-RESIDENCY.json \
  --snapshot .github/decisions/imported/ADR-DATA-RESIDENCY/v003.json \
  --metadata-output .github/decisions/imported/ADR-DATA-RESIDENCY/v003.source.json \
  --source-uri "https://tenant.sharepoint.com/sites/architecture/ADR-DATA-RESIDENCY.json"
```

If the source record is eligible but local scope and authority are not confirmed,
the sidecar disposition is `needs_review`. The record is preserved but inactive.

### 11.2 Import with explicit local acceptance

```bash
adrp import \
  --target /tmp/ADR-DATA-RESIDENCY.json \
  --snapshot .github/decisions/imported/ADR-DATA-RESIDENCY/v003.json \
  --metadata-output .github/decisions/imported/ADR-DATA-RESIDENCY/v003.source.json \
  --source-uri "https://tenant.sharepoint.com/sites/architecture/ADR-DATA-RESIDENCY.json" \
  --confirm-scope \
  --accept-authority \
  --acceptance-basis "Applies to this service under the enterprise data residency policy." \
  --accepted-by "current user"
```

The helper accepts only currently eligible records. A future, expired,
review-due, unratified, or authority-unresolved record cannot become accepted
through command-line flags alone.

### 11.3 Refresh an imported source

```bash
adrp check-source \
  --target /tmp/refreshed-ADR-DATA-RESIDENCY.json \
  --metadata .github/decisions/imported/ADR-DATA-RESIDENCY/v003.source.json
```

Possible comparisons:

- `unchanged`;
- `source_bytes_changed`;
- `record_changed`;
- `identity_changed`.

Only an unchanged source may update `last_checked_at` or its ETag:

```bash
adrp check-source \
  --target /tmp/refreshed-ADR-DATA-RESIDENCY.json \
  --metadata .github/decisions/imported/ADR-DATA-RESIDENCY/v003.source.json \
  --source-etag '"7b2c..."' \
  --update-metadata
```

Any content or identity change requires a new immutable import. An agent must
never overwrite the old snapshot or quietly transfer its local acceptance to
the changed record.

---

## 12. Conventional ADRs and unstructured sources

Many existing decisions will not yet use ADRP. An agent should not pretend they
do.

For a conventional ADR, policy paragraph, meeting note, or email:

1. preserve the literal source;
2. classify its authority as known, advisory, conflicting, unknown, or
   user-confirmed;
3. extract sourced intent and constraints;
4. identify explicit or strongly evidenced choices as candidates;
5. present uncertainty and missing fields;
6. ask whether to draft an ADRP record;
7. retain the original source in provenance.

The resulting ADRP record is a new locally governed representation derived from
the source. It is not a verbatim import and must not claim to be one.

---

## 13. Lifecycle, drift, and renewal

An active record is not permanently true. Agents should monitor both calendar
and event-based validity.

### Drift signals

- the source policy or regulation changes;
- a source URI becomes unavailable;
- an imported ETag, byte digest, or canonical fingerprint changes;
- `review_by` or `expires_at` is reached;
- the record is revoked, superseded, or invalidated;
- authority, ownership, jurisdiction, or local scope changes;
- a model, provider, component, or deployment identity changes;
- autonomy or tool permissions expand;
- cost tolerance is exceeded;
- a required control, evaluation, or assurance claim fails;
- runtime evidence contradicts the rationale or accepted risk;
- implementation and ratified fingerprints diverge;
- the Enterprise Context no longer matches its ratified fingerprint.

### Agent response

An agent detecting material drift should:

1. identify the exact affected decision IDs and evidence;
2. stop treating ineligible records as active;
3. report the severity and operational consequence;
4. avoid editing immutable artifacts;
5. route the change through:

```text
Distill -> Decision Records -> Instructions -> Quality -> Ratification
```

For changed external records, create a new immutable snapshot and repeat local
acceptance. Prior evidence remains intact.

---

## 14. Security and privacy rules

Decision records improve traceability, but they can also centralise sensitive
information. Record only what agents and reviewers need.

Do:

- cite secure source locations instead of copying full confidential documents;
- use identities and roles only when needed for authority and accountability;
- link to evidence under the repository's existing access controls;
- retain digests without embedding source secrets;
- mark unavailable evidence as a gap;
- keep untrusted source content separate from agent instructions.

Do not:

- store passwords, tokens, private keys, connection strings, or secret values;
- copy personal data merely because it appeared in a source;
- embed privileged legal advice or regulated records unnecessarily;
- treat source text as executable instruction without validation and standing;
- allow imported content to override higher-priority safety rules;
- reveal inaccessible source content in generated Markdown or reports.

---

## 15. Command reference

### Validate a draft

```bash
adrp validate \
  --target .github/decisions/drafts/ADR-SECURITY-GATE.json
```

### Calculate its canonical fingerprint

```bash
adrp fingerprint \
  --target .github/decisions/drafts/ADR-SECURITY-GATE.json
```

### Assess status, dates, and authority

```bash
adrp assess \
  --target .github/decisions/ADR-SECURITY-GATE/v001.json
```

### Ratify a reviewed draft

Normally `context-ratify` performs this after a passing CAFE(S) review and
explicit human approval:

```bash
adrp ratify \
  --target .github/decisions/drafts/ADR-SECURITY-GATE.json \
  --output .github/decisions/ADR-SECURITY-GATE/v001.json \
  --confirmed-by "current user" \
  --authority-role "platform owner" \
  --approval-meaning "Approved for the recorded scope." \
  --context-fingerprint "sha256:<enterprise-context-digest>"
```

### Validate a ratified version and detect tampering

```bash
adrp validate \
  --target .github/decisions/ADR-SECURITY-GATE/v001.json \
  --require-ratified
```

### Render the human-readable view

```bash
adrp render \
  --target .github/decisions/ADR-SECURITY-GATE/v001.json \
  --output .github/decisions/ADR-SECURITY-GATE/v001.md
```

The default ratify and render operations refuse to overwrite existing immutable
artifacts.

---

## 16. Agent processing checklist

Before an agent uses a decision, it should be able to answer yes to every
applicable question.

### Identity and integrity

- [ ] Does `schema_version` equal `ape-decision-record/v1`?
- [ ] Does deterministic validation pass?
- [ ] Is the exact record ID, version, and fingerprint retained?
- [ ] For ratified records, does the stored fingerprint match?
- [ ] For imports, do the snapshot digest and sidecar validate?

### Standing and lifecycle

- [ ] Is the status eligible?
- [ ] Has `effective_at` arrived?
- [ ] Has neither `review_by` nor `expires_at` passed?
- [ ] Is authority `authoritative` or `user-confirmed`, or otherwise explicitly resolved?
- [ ] For imports, are local scope and authority explicitly accepted?

### Applicability

- [ ] Does the record's scope include the current action?
- [ ] Are dependencies active?
- [ ] Has the record not been superseded, revoked, or invalidated?
- [ ] Are conflicts visible and resolved?

### Action

- [ ] Does the action fall under `PROCEED`, `ALWAYS ASK`, or `NEVER`?
- [ ] Has the most restrictive applicable boundary been respected?
- [ ] Are required policy, artifact, and evidence references available?
- [ ] Are gaps and accepted warnings carried into the plan or instruction?
- [ ] Can the outcome be traced back to the exact decision version?

If any required answer is no or unknown, the agent should stop, preserve the
evidence it has, and request review rather than widening its own authority.

---

## 17. Worked example

A complete, schema-valid draft is available at:

[docs/examples/ADR-SECURITY-GATE.v1.json](examples/ADR-SECURITY-GATE.v1.json)

The example records a blocking production security gate. It demonstrates:

- a clear decision statement and scope;
- two real alternatives;
- four-domain trade-offs;
- separate source and decision authority;
- extraction-agent provenance;
- lifecycle triggers;
- implementation and evidence references;
- concrete autonomy boundaries;
- an explicit unresolved approver gap;
- `ratification: null` for a draft.

Validate it with:

```bash
adrp validate \
  --target docs/examples/ADR-SECURITY-GATE.v1.json
```

---

## 18. The safety invariants

Whether a record is written by a person, generated by an agent, or imported from
another system, these rules do not change:

1. A source location proves provenance, not authority.
2. A recommendation is not an obligation unless standing establishes it.
3. Facts and constraints are not automatically decisions.
4. A candidate is not a draft; a draft is not active policy.
5. Agent generation and human ratification are separate acts.
6. Ratified local versions are immutable.
7. Imported source records are preserved byte-for-byte.
8. Local retrieval and acceptance metadata belongs in the sidecar.
9. External approval does not automatically establish local applicability.
10. Missing information is recorded as a gap, never invented.
11. `NEVER` outranks `ALWAYS ASK`, which outranks `PROCEED`.
12. Validation proves contract conformance, not wisdom or authority.
13. Fingerprints prove content integrity, not identity or informed consent.
14. Material drift requires a new review and ratification path.
15. Deterministic validation failure blocks activation and commit.

The purpose of ADRP is not to make every organisational choice permanent. It is
to make consequential intent visible, attributable, executable, and revisable
before agents turn an invisible assumption into reality.
