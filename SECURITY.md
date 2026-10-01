# Security

## Reporting a vulnerability

Please use GitHub private vulnerability reporting for `suuus/adrp` rather than
opening a public issue with exploit details.

Include:

- affected ADRP or source schema version;
- affected CLI version and command;
- a minimal record or record set that reproduces the issue;
- the security consequence;
- whether immutable artifacts, authority, lifecycle, scope, or autonomy
  resolution are affected.

Do not include real secrets, credentials, personal data, or confidential source
documents in a report.

## Security model

ADRP treats deterministic processing as a trust boundary:

- malformed or tampered records fail closed;
- ratification fingerprints bind immutable payloads;
- imported source bytes and local metadata remain separate;
- changed imported bytes require a new immutable snapshot;
- unresolved actions do not become permission;
- `NEVER` outranks `ALWAYS ASK`, which outranks `PROCEED`;
- a source location never establishes authority.

A valid ADRP record is not proof that its content is correct or that its
approver had legitimate authority. Integrators must enforce repository access,
identity, signature, and source-system controls appropriate to their risk.

## Supported versions

Security fixes are applied to the latest release. ADRP is currently alpha; the
project will document a formal support window before 1.0.

