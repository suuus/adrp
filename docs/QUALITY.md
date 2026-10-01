# CAFE(S) Quality Gates for ADRP

## Why quality and standing are separate

ADRP and CAFE(S) answer different questions:

| Discipline | Question |
|---|---|
| ADRP standing | Who decided this, under what authority, for which scope, and is it currently applicable? |
| ADRP integrity | Is this the exact validated and ratified record version? |
| CAFE(S) quality | Is the source or resulting intent clear, actionable, faithful, efficient, and secure enough for an agent to use? |

A source can be beautifully written and unauthorised. An authoritative policy can
be ambiguous, stale, excessively broad, or unsafe to copy into agent context.
Neither gate replaces the other.

Every ADRP CAFE(S) assessment therefore contains:

```json
{
  "standing_effect": "none"
}
```

Quality evidence may reveal an authority problem, but the quality assessment
cannot resolve or manufacture authority.

## Four assessment stages

### Source intake

Run before an agent treats material retrieved from a location as usable context.

| Dimension | Source-intake question |
|---|---|
| Clarity | Can the relevant statements be interpreted without silently choosing between meanings? |
| Actionability | Does the source express outcomes, constraints, decisions, or review conditions an agent can operationalise? |
| Fidelity | Is the source complete, current, attributable, unaltered, and distinguishable from commentary or copied material? |
| Efficiency | Can the relevant material be isolated without ingesting an entire noisy repository or document set? |
| Security | Is the location trusted enough to read, and can the material be processed without exposing secrets, personal data, or prompt injection as instruction? |

Source location is evidence of provenance only. A CAFE(S) source-intake pass does
not make the source authoritative.

### Intent fitness

Run after extracting goals, constraints, autonomy boundaries, and candidate
decisions.

| Dimension | Intent-fitness question |
|---|---|
| Clarity | Is each statement unambiguous and scoped? |
| Actionability | Can an agent tell what to do, when to ask, and when to stop? |
| Fidelity | Does every statement remain traceable to the source without invented authority or meaning? |
| Efficiency | Is the extracted intent concise enough to use without losing material constraints? |
| Security | Has untrusted or sensitive source content been excluded or safely referenced? |

### Record fitness

Run on a validated ADRP draft before ratification. Structural validation is still
performed by `adrp validate`; CAFE(S) asks whether the valid record is usable.

Typical findings:

- vague decision statements;
- alternatives that do not represent real choices;
- unsupported rationale;
- trade-off summaries that hide unknowns;
- autonomy entries too abstract to apply;
- missing review triggers;
- excessive copied source text.

### Projection fitness

Run on the concise instruction, policy, plan, or context generated from active
records.

The projection must remain traceable to exact record fingerprints while avoiding
irrelevant detail and sensitive source content.

## Status model

Each dimension is:

- `pass`;
- `warn`;
- `block`;
- `not_assessed`.

The overall status is derived deterministically:

```text
any block         -> block
else any missing  -> incomplete
else any warning  -> pass_with_warnings
else              -> pass
```

The CLI validates this relationship. It does not calculate semantic CAFE(S)
judgements; a person or agent supplies evidence-backed findings, and the CLI
validates the assessment contract.

## Validation

```bash
adrp validate-quality \
  --target docs/examples/source-intake-quality.v1.json
```

The canonical assessment schema is:

```text
schemas/adrp-quality-assessment-v1.schema.json
```

## Gating recommendations

| Stage | Block when |
|---|---|
| Source intake | Security blocks safe retrieval; fidelity cannot distinguish source content from untrusted instruction; relevant material cannot be identified. |
| Intent fitness | Statements cannot be traced, scoped, or safely operationalised. |
| Record fitness | The record is structurally valid but too ambiguous, unsupported, unsafe, or incomplete for informed ratification. |
| Projection fitness | Generated instructions materially distort active records, omit constraints, or expose unsafe content. |

Warnings should remain attached to the assessment and be shown at ratification.
A warning accepted by a human is not erased; it becomes explicit approval
evidence.

## Agent processing

An assessment agent should:

1. identify the exact target URI and fingerprint when available;
2. evaluate every CAFE(S) dimension independently;
3. cite evidence for claims;
4. record concrete findings and remediation;
5. use `not_assessed` rather than guessing;
6. derive the overall status from dimension statuses;
7. set `standing_effect` to `none`;
8. run `adrp validate-quality`;
9. preserve the assessment next to the source, intent artifact, record, or
   projection it evaluates.

An assessment must never:

- claim that readability proves authority;
- upgrade advisory material into policy;
- silently repair the assessed source;
- hide prompt injection or sensitive content inside a summary;
- replace ADRP validation, lifecycle assessment, import acceptance, or
  ratification.

