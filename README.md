# ADRP — Ape Decision Record Profile

> The durable Intent record layer for the ISEE Framework.

The **Ape Decision Record Profile (ADRP)** is a human-ratified,
machine-readable standard for organisational and technical decisions that shape
agent behaviour. ADRP is the durable **Intent** record layer of the
**ISEE Framework: Intent → Structure → Execution → Evidence**.

Learn more about the operating framework at
[agentile.org](https://agentile.org).

ADRP records more than the final choice. It preserves:

- scope, stakeholders, concerns, and decision drivers;
- alternatives, rationale, consequences, and accepted risks;
- security, cost, compliance, and operational trade-offs;
- source provenance and organisational authority;
- effective dates, review dates, expiry, and drift triggers;
- implementation and evidence references;
- `PROCEED`, `ALWAYS ASK`, and `NEVER` agent boundaries;
- immutable human ratification bound to an exact context fingerprint.

This repository contains the standard, schemas, deterministic CLI, agent,
skills, examples, and conformance tests. It is intentionally independent from
Ape Context. Other systems may consume ADRP without adopting the Ape Context
workflow.

## Why ADRP?

Agents can execute instructions quickly, but an instruction alone rarely says:

- who was authorised to make the choice;
- where the choice applies;
- which alternatives were rejected;
- which risks were accepted;
- whether the choice is still current;
- what the agent may do without asking;
- what evidence should cause the choice to be reviewed.

ADRP turns consequential intent into a durable contract that both people and
software can inspect.

Every recorded decision expresses intent, but not every expression of intent is
a decision. Goals, facts, constraints, and recommendations should remain sourced
intent unless a meaningful choice has actually been made.

## ADRP in the ISEE Framework

ISEE treats agentic work as a closed governance loop:

```text
Intent       ADRP records the decision, authority, scope, trade-offs,
             autonomy boundaries, lifecycle, and expected evidence.
    ↓
Structure    Architecture, ownership, policy, controls, and agent boundaries
             are recorded by ASRP and linked to active ADRP fingerprints.
    ↓
Execution    Agents and delivery systems consume the resolved records and
             retain the exact ADRP fingerprints that shaped the action.
    ↓
Evidence     AERP binds observations, assessments, approvals, execution
             artifacts, outcomes, and drift back to those fingerprints.
    ↺
Review       Material evidence triggers ADRP review, supersession, or revocation.
```

ADRP does not attempt to own Structure, Execution, or Evidence. It makes the
Intent needed by those layers explicit and addressable. The companion
[Ape Structure Record Profile](https://github.com/suuus/asrp) provides the
Structure record layer, while the
[Ape Evidence Record Profile](https://github.com/suuus/aerp) provides the
Evidence record layer.

See [Setting up ADRP with AERP for ISEE](docs/ISEE_INTEGRATION.md) for the
end-to-end repository layout, commands, agent handoff, and CI pattern.

## Install with GitHub Copilot

The recommended installation is the complete
[ISEE plugin suite](https://github.com/suuus/isee-plugins):

```bash
copilot plugin marketplace add suuus/isee-plugins
copilot plugin install isee-suite@isee
```

This loads the ADRP agent and skills together with ASRP, AERP, ISEE
integration, ISEE Advisor, and setup guidance. To install only ADRP:

```bash
copilot plugin install adrp@isee
```

Plugin installation loads the Copilot agent and skills. Use `isee-setup` from
the complete suite to install or diagnose the deterministic CLIs explicitly.

## Install the CLI from a checkout

From a checkout:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

Then:

```bash
adrp --help
adrp --version
```

The runtime has no third-party dependencies.

## Core commands

```bash
# One record
adrp validate --target record.json
adrp fingerprint --target record.json
adrp assess --target record.json
adrp inspect record.json
adrp render --target record.json --output record.md
adrp validate-quality --target source-intake-quality.json

# Immutable lifecycle operations
adrp ratify \
  --target draft.json \
  --output decisions/ADR-0001/v001.json \
  --confirmed-by "current user" \
  --approval-meaning "Approved for the recorded scope." \
  --context-fingerprint "sha256:<digest>"

adrp import \
  --target external.json \
  --snapshot imported/ADR-0042/v003.json \
  --metadata-output imported/ADR-0042/v003.source.json \
  --source-uri "https://example.org/decisions/ADR-0042.json"

adrp check-source \
  --target refreshed.json \
  --metadata imported/ADR-0042/v003.source.json

# Sets of records
adrp verify-set .github/decisions
adrp resolve .github/decisions --scope "production deployments"
adrp autonomy .github/decisions \
  --scope "production deployments" \
  --action "Deploy while blocking security findings remain"
adrp graph .github/decisions
```

Commands intended for agents emit stable JSON contracts. Validation and
immutable-write failures return non-zero exit codes and never produce
success-shaped fallback output.

## Resolution model

The deterministic reader processes records in five stages:

```text
Recognise -> Validate -> Assess -> Resolve -> Apply
```

`adrp resolve`:

1. discovers canonical records and source sidecars;
2. validates schema, references, and fingerprints;
3. assesses lifecycle and authority;
4. requires accepted local standing for imports;
5. filters by exact normalised scope;
6. selects the highest active version of each logical decision;
7. applies supersession, invalidation, and dependencies;
8. returns active records, exclusions, warnings, and errors.

`adrp autonomy` evaluates a proposed action against that resolved set. The most
restrictive matching boundary wins:

```text
NEVER > ALWAYS ASK > PROCEED
```

An unmatched action is `UNRESOLVED`; the CLI does not invent permission.

## Documentation

- [Recording Intent with Ape Decision Records](docs/RECORDING_INTENT.md) -
  practical human and agent guide.
- [Ape Decision Record Profile 1.0](docs/STANDARD.md) - normative profile.
- [Valid security-gate example](docs/examples/ADR-SECURITY-GATE.v1.json).
- [Agent integration](docs/AGENT_INTEGRATION.md) - how agents and skills use the
  deterministic CLI.
- [ISEE integration with AERP](docs/ISEE_INTEGRATION.md) - connect ratified
  Intent to execution Evidence and close the review loop.
- [CAFE(S) quality gates](docs/QUALITY.md) - source-intake and intent-fitness
  assessment without conflating quality with authority.

## Copilot plugin

The repository includes an ADRP agent and seven focused skills:

- `adrp-write`
- `adrp-read`
- `adrp-import`
- `adrp-quality`
- `adrp-resolve`
- `adrp-ratify`
- `adrp-drift`

The dependency direction is deliberate:

```text
ADRP Agent -> ADRP Skills -> adrp CLI -> ADRP artifacts
```

Agents interpret and interact. The CLI validates, fingerprints, resolves, and
writes immutable artifacts. Skills must not reproduce deterministic operations
through prompt-only logic.

For normal use, install this plugin through the
[ISEE marketplace](https://github.com/suuus/isee-plugins) rather than copying
agent and skill files manually.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 -m build
```

## Status

ADRP is currently an alpha specification and toolchain. The `v1` record and
source schema identifiers are stable within this release line, but additional
set-level output contracts may evolve before ADRP 1.0.

## License

MIT
