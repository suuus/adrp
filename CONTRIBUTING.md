# Contributing

ADRP changes can affect how agents interpret authority and permission. Prefer
small, reviewable changes with explicit tests.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
```

## Change requirements

- Schema changes must update the normative standard, practical guide, examples,
  CLI validation, and conformance tests.
- CLI output contracts must retain a `schema_version`.
- Immutable-write behavior must remain fail-closed.
- New resolution behavior must include adversarial tests.
- Agent and skill instructions must call the deterministic CLI rather than
  reproducing validation or fingerprinting in prompts.
- Missing authority or lifecycle information must remain visible; never add a
  permissive default.

## Pull requests

Describe:

- the problem and intended semantics;
- compatibility impact;
- affected record or output schema;
- human and agent behavior changes;
- tests added;
- migration guidance, if required.

