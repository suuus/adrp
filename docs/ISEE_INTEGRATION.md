# ADRP and AERP in the ISEE Framework

## Purpose

The **ISEE Framework** governs agentic work as a closed loop:

```text
Intent → Structure → Execution → Evidence
```

[ADRP](https://github.com/suuus/adrp) and
[AERP](https://github.com/suuus/aerp) provide the durable record layers at
either end:

| ISEE layer | Primary concern | Record or system |
|---|---|---|
| Intent | What was decided, why, by whom, where it applies, and what agents may do | ADRP |
| Structure | Architecture, ownership, controls, policy, workflows, and agent boundaries | Referenced implementation artifacts |
| Execution | The action performed by agents, CI/CD, platforms, or people | Git-Ape or another execution system |
| Evidence | What was observed, assessed, approved, executed, produced, or found to have drifted | AERP |

ADRP and AERP are intentionally separate:

- ADRP determines decision standing and applicability.
- AERP preserves evidence semantics and artifact integrity.
- Structure and Execution systems remain replaceable.
- Evidence can challenge Intent, but cannot silently rewrite it.

## Install both tools

From sibling checkouts:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ../adrp -e ../aerp

adrp --version
aerp --version
```

The tools do not call each other internally. Agents, workflows, or CI
orchestrate the handoff explicitly.

## Recommended repository layout

```text
.
├── .github/
│   └── decisions/
│       ├── drafts/
│       └── ADR-SECURITY-GATE/
│           └── v001.json
├── architecture/
│   ├── diagrams/
│   ├── policies/
│   └── controls/
├── evidence/
│   ├── assessments/
│   └── outcomes/
└── .azure/
    └── deployments/
        └── <deployment-id>/
            ├── requirements.json
            ├── template.json
            ├── security-gate.json
            ├── tests.json
            └── evidence/
                └── bundle.json
```

General evidence may live under `evidence/`. Execution-system evidence may
remain next to its native trace, such as Git-Ape's deployment directory.

## End-to-end setup

### 1. Intent: write and ratify ADRP

Create a draft containing:

- decision statement and exact scope;
- authority and provenance;
- alternatives and rationale;
- security, cost, compliance, and operational trade-offs;
- autonomy effects;
- lifecycle and drift triggers;
- implementation references;
- expected evidence references.

Validate and ratify it:

```bash
adrp validate --target .github/decisions/drafts/ADR-SECURITY-GATE.json

adrp ratify \
  --target .github/decisions/drafts/ADR-SECURITY-GATE.json \
  --output .github/decisions/ADR-SECURITY-GATE/v001.json \
  --confirmed-by "current user" \
  --approval-meaning "Approved for production deployments." \
  --context-fingerprint "sha256:<approved-context-digest>"
```

### 2. Intent selection: resolve exact active records

Before planning or execution:

```bash
adrp verify-set .github/decisions

adrp resolve .github/decisions \
  --scope "production deployments" \
  --as-of "2026-10-02T12:00:00Z"
```

The orchestrator MUST retain the canonical files and fingerprints returned as
active. An ID or natural-language summary alone is insufficient.

### 3. Structure: materialise the decision

Structure artifacts may include:

- architecture diagrams and component boundaries;
- ownership and escalation rules;
- OPA, Cedar, DMN, or cloud-policy artifacts;
- threat models and control mappings;
- agent definitions and skills;
- workflow gates and approval environments.

Reference these from ADRP `implementation` fields. Structure artifacts should
also retain the relevant ADRP fingerprints in generated metadata, plans, pull
requests, or manifests.

### 4. Execution: consume the resolved Intent

The execution system receives:

```json
{
  "decision_id": "ADR-SECURITY-GATE",
  "record_id": "849535a2-fb8d-4a59-a9ea-d01ff9b7b460",
  "record_version": 1,
  "record_fingerprint": "sha256:..."
}
```

It must not resolve authority by itself or silently substitute a newer decision
after approval. If the active record changes, the plan should be regenerated
or re-approved.

### 5. Evidence: bind AERP to the exact ADRP record

For one artifact:

```bash
aerp new \
  --type assessment \
  --subject "deployment deploy-20261002-103000" \
  --claim "The required security gate passed" \
  --result passed \
  --summary "No blocking security findings remained." \
  --producer "git-ape-security-gate" \
  --producer-version "1.0.0" \
  --identity "github-actions:org/repo/.github/workflows/deploy.yml" \
  --method "security-gate" \
  --method-version "1" \
  --environment production \
  --target "/subscriptions/.../resourceGroups/rg-api-prod" \
  --decision .github/decisions/ADR-SECURITY-GATE/v001.json \
  --artifact .azure/deployments/deploy-20261002-103000/security-gate.json \
  --artifact-root . \
  --artifact-role report \
  --output evidence/assessments/security-gate.json
```

For an existing evidence record:

```bash
aerp bind \
  evidence/assessments/security-gate.unbound.json \
  .github/decisions/ADR-SECURITY-GATE/v001.json \
  --output evidence/assessments/security-gate.json
```

For a Git-Ape trace:

```bash
aerp bundle-git-ape .azure/deployments/deploy-20261002-103000 \
  --identity "github-actions:org/repo/.github/workflows/deploy.yml" \
  --producer-version "0.8.0" \
  --target "/subscriptions/.../resourceGroups/rg-api-prod" \
  --decision .github/decisions/ADR-SECURITY-GATE/v001.json \
  --output .azure/deployments/deploy-20261002-103000/evidence/bundle.json
```

### 6. Verify the Evidence

```bash
aerp validate evidence/assessments/security-gate.json
aerp verify evidence/assessments/security-gate.json --artifact-root .

aerp verify \
  .azure/deployments/deploy-20261002-103000/evidence/bundle.json \
  --artifact-root .azure/deployments/deploy-20261002-103000
```

AERP verification establishes internal structure, fingerprints, and artifact
identity. Signing and producer authentication remain separate.

### 7. Close the loop

Evidence should trigger ADRP review when:

- expected evidence is missing;
- a required assessment fails or is inconclusive;
- implementation differs from the selected alternative;
- accepted risk changes materially;
- runtime drift crosses a recorded threshold;
- the decision's assumptions no longer hold;
- evidence expires or its collection method becomes obsolete.

The response is not to edit the ratified ADRP version. Review it and create a
new version, superseding decision, revocation, or explicit acceptance as
appropriate.

## Agent contract

An ISEE-aware agent should:

1. resolve ADRP before planning;
2. carry exact ADRP fingerprints into plans and executions;
3. refuse or ask according to ADRP autonomy results;
4. capture AERP evidence without upgrading observations into passes;
5. verify artifact bytes;
6. distinguish local integrity from authenticated attestation;
7. route material Evidence back to Intent review.

## CI baseline

```yaml
- name: Verify decision set
  run: adrp verify-set .github/decisions

- name: Resolve production intent
  run: |
    adrp resolve .github/decisions \
      --scope "production deployments" \
      > resolved-intent.json

- name: Verify execution evidence
  run: |
    aerp validate .azure/deployments/${DEPLOYMENT_ID}/evidence/bundle.json
    aerp verify \
      .azure/deployments/${DEPLOYMENT_ID}/evidence/bundle.json \
      --artifact-root .azure/deployments/${DEPLOYMENT_ID}
```

The workflow should separately verify any DSSE/Sigstore signature and producer
identity required by organisational policy.

## Invariants

- Intent quality does not create authority.
- Evidence quality does not create compliance standing.
- ADRP validity does not prove implementation.
- AERP validity does not prove the truth of a claim.
- Structure and Execution must retain exact decision fingerprints.
- Failures, errors, warnings, and inconclusive results remain visible.
- Material Evidence challenges Intent through review, never silent mutation.
