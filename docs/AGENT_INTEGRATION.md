# Agent Integration

## Purpose

ADRP separates semantic work from deterministic record processing.

In the ISEE Framework, this agent owns the **Intent** boundary:

```text
Intent             Structure            Execution            Evidence
ADRP record   →     referenced      →    consuming agent  →    AERP record
and resolution      architecture          or system             or bundle
```

Agents must carry the exact ADRP identity and fingerprint across the later
stages. A paraphrased instruction is not an adequate decision binding.

```text
Agent
  -> selects and orchestrates a skill
Skill
  -> gathers sources and human decisions
ADRP CLI
  -> validates, fingerprints, assesses, resolves, and writes artifacts
Record set
  -> supplies durable decision-bearing intent
```

The agent is responsible for conversation, interpretation, source discovery,
candidate presentation, and asking for decisions. The CLI is responsible for
the operations where identical input must produce identical results.

An agent must never replace a failing CLI operation with prompt-only validation
or a success-shaped summary.

## Locating the CLI

Skills should resolve the command in this order:

1. `adrp` on `PATH`;
2. `python3 -m adrp` when the package is importable;
3. `python3 src/adrp/cli.py` when operating in an ADRP checkout;
4. the installed plugin checkout, when its path is known.

After resolving it, run:

```bash
<adrp-command> --version
```

If no deterministic CLI is available, the skill may explain or review source
material, but it must not claim validation, resolution, ratification, import,
or active standing.

## Stable machine contracts

Commands intended for agents emit JSON:

| Command | Output schema |
|---|---|
| `inspect` | `adrp` record inspection object |
| `resolve` | `adrp-resolution/v1` |
| `autonomy` | `adrp-autonomy/v1` |
| `graph` | `adrp-graph/v1` |
| `verify-set` | `adrp-verification/v1` |

Agents should parse JSON fields rather than console wording. Non-zero exit means
the operation did not complete successfully.

## Writing workflow

An authoring agent should:

1. identify accessible sources and preserve literal locations;
2. separate goals, facts, constraints, guidance, and choices;
3. recognise existing `ape-decision-record/v1` documents before extraction;
4. create a candidate only for an explicit or strongly evidenced choice;
5. expose alternatives, authority, trade-offs, autonomy, lifecycle, and gaps;
6. ask the human to choose `Draft`, `Revise`, or `Skip`;
7. create a draft with `ratification: null`;
8. run `adrp validate`;
9. run `adrp fingerprint`;
10. report the draft as inactive.

The agent must not invent an owner, approver, source standing, review date,
accepted risk, or evidence reference.

## CAFE(S) quality workflow

Use `adrp-quality` at two important boundaries:

1. **Source intake:** before extracted material is trusted as useful agent
   context.
2. **Intent or record fitness:** after extraction or drafting, before
   ratification and projection.

The assessment covers Clarity, Actionability, Fidelity, Efficiency, and
Security. Write `adrp-quality-assessment/v1` JSON and run:

```bash
adrp validate-quality --target <assessment.json>
```

Quality never creates authority. The required `standing_effect` is `none`.

## Reading workflow

A consuming agent should:

1. recognise the schema version;
2. run `adrp inspect`;
3. reject malformed or tampered records as active policy;
4. evaluate status, lifecycle, authority, and import sidecar standing;
5. preserve decision ID, record ID, version, and fingerprint;
6. keep gaps and warnings visible.

Reading only `decision_statement` is unsafe because applicability depends on
scope, lifecycle, authority, relationships, and local acceptance.

## Set resolution

Use:

```bash
adrp resolve <path> [<path> ...] \
  --scope "<exact scope>" \
  --as-of "<timestamp>"
```

The agent should consume:

- `active`;
- `excluded`;
- `warnings`;
- `errors`;
- `summary`.

An empty `active` list is not permission. It means no applicable active decision
was resolved.

Resolution uses exact case-insensitive, whitespace-normalised scope values. An
agent should pass the scopes it knows rather than broadening or paraphrasing
them. A record scope containing `*` is explicitly global.

## Autonomy evaluation

Use:

```bash
adrp autonomy <path> \
  --scope "<exact scope>" \
  --action "<proposed action>"
```

Outcomes:

| Outcome | Agent behaviour |
|---|---|
| `PROCEED` | The matching action may proceed within resolved scope. |
| `ALWAYS_ASK` | Ask for specific approval immediately before the action. |
| `NEVER` | Refuse the action while the decision remains applicable. |
| `UNRESOLVED` | Do not infer permission; request clarification or a decision. |

The CLI applies `NEVER > ALWAYS_ASK > PROCEED`. Agents must not weaken that
result.

Action matching is deterministic but intentionally conservative: normalised
exact or containing phrases match. Integrations that require richer policy
evaluation should link ADRP to DMN, OPA, Cedar, or another executable policy
artifact through `implementation.policy_refs`.

## Import workflow

For an external canonical record:

1. retrieve it without rewriting;
2. validate and assess it;
3. present source URI, identity, fingerprint, status, authority, dates, and
   scope;
4. ask `Accept`, `Preserve`, or `Ignore`;
5. on `Accept`, require explicit scope confirmation, authority acceptance,
   acceptance basis, and confirming identity;
6. call `adrp import`;
7. preserve the canonical bytes and sidecar separately.

An agent must not copy external ratification into local standing. The source
record proves what the source approved. The sidecar records whether it applies
here.

## Ratification workflow

Ratification is always a human decision. Before offering approval, show:

- exact decision statement and scope;
- alternatives and rationale;
- authority and provenance;
- all four trade-off domains;
- consequences and accepted risks;
- autonomy boundaries;
- lifecycle and relationships;
- gaps and warnings;
- the exact context fingerprint being approved.

Only explicit `Approve` permits `adrp ratify`. `Revise`, `Stop`, silence, or tool
failure produce no immutable version.

## Drift workflow

Use `adrp verify-set`, `adrp inspect`, `adrp check-source`, and `adrp graph` to
detect:

- invalid or tampered records;
- changed imported bytes or fingerprints;
- review-due or expired records;
- inactive or unaccepted imports;
- broken dependencies;
- superseded or invalidated decisions;
- changed authority or scope;
- implementation or evidence divergence.

Agents report drift and route it to review. They never repair immutable records
in place.

## Logging applied decisions

When a record materially shapes an action, retain:

```json
{
  "decision_id": "ADR-SECURITY-GATE",
  "record_id": "849535a2-fb8d-4a59-a9ea-d01ff9b7b460",
  "record_version": 1,
  "record_fingerprint": "sha256:...",
  "scope": ["production deployments"],
  "outcome": "NEVER",
  "action": "Deploy while blocking security findings remain"
}
```

This can be attached to a plan, pull request, policy decision, audit event, or
agent trace.

## AERP evidence handoff

When an active ADRP record materially shapes an execution:

1. run `adrp resolve` for the exact scope;
2. retain the canonical record file selected in `active`;
3. give Structure and Execution systems the decision identity, version, and
   fingerprint;
4. capture the resulting artifact or assessment with AERP;
5. pass the canonical ADRP file to AERP using `--decision` or `aerp bind`;
6. verify the AERP record and its referenced artifact bytes;
7. route material failure or drift back into ADRP review.

Example:

```bash
adrp resolve .github/decisions \
  --scope "production deployments" \
  --as-of "2026-10-02T12:00:00Z"

aerp new \
  --type assessment \
  --subject "production deployment security gate" \
  --claim "The deployment passed the required security gate" \
  --result passed \
  --summary "The configured security gate completed without blocking findings." \
  --producer "security-gate" \
  --producer-version "1.0.0" \
  --identity "github-actions:org/repo/.github/workflows/deploy.yml" \
  --method "security-gate" \
  --method-version "1" \
  --environment production \
  --target "deployment:deploy-20261002-103000" \
  --decision .github/decisions/ADR-SECURITY-GATE/v001.json \
  --artifact reports/security-gate.json \
  --artifact-root . \
  --artifact-role report \
  --output evidence/security-gate.json

aerp verify evidence/security-gate.json --artifact-root .
```

The AERP binding proves which exact Intent record the evidence refers to. It
does not itself prove that the ADRP record was active or authoritative; ADRP
resolution remains the source of that standing.

See [ADRP and AERP in ISEE](ISEE_INTEGRATION.md) for complete setup.

## Safety invariants

- Source location does not establish authority.
- Agent extraction does not establish ratification.
- Validation does not establish wisdom or local applicability.
- Drafts and candidates are inactive.
- Imported canonical bytes are immutable.
- Local import acceptance lives only in the sidecar.
- Missing information remains a gap.
- Conflicts require review; agents do not choose the convenient record.
- An unmatched action is unresolved, not permitted.
- A failed deterministic operation blocks the dependent agent claim.
