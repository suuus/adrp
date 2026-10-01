import json
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "adrp" / "cli.py"


def draft_record() -> dict:
    return {
        "schema_version": "ape-decision-record/v1",
        "decision_id": "ADR-0001",
        "record_id": str(uuid.uuid4()),
        "record_version": 1,
        "status": "draft",
        "title": "Require security review before deployment",
        "decision_statement": "Every production deployment requires a passing security gate.",
        "context": {
            "problem": "Agents can otherwise deploy without security review.",
            "scope": ["production deployments"],
            "stakeholders": ["platform engineering", "security"],
            "concerns": ["security", "delivery speed"],
        },
        "drivers": [
            {
                "name": "Mandatory security review",
                "category": "security",
                "criterion": "Block deployment until findings are resolved.",
                "source_refs": ["src-security-policy"],
            }
        ],
        "alternatives": [
            {
                "id": "blocking-gate",
                "title": "Blocking security gate",
                "description": "Security analysis must pass before deployment.",
                "benefits": ["Prevents unsafe deployment"],
                "drawbacks": ["May delay release"],
                "rejection_reason": None,
            },
            {
                "id": "advisory-only",
                "title": "Advisory review",
                "description": "Report issues without blocking.",
                "benefits": ["Faster delivery"],
                "drawbacks": ["Known issues may reach production"],
                "rejection_reason": "Does not satisfy the mandatory policy.",
            },
        ],
        "selected_alternative": "blocking-gate",
        "rationale": "The authoritative policy requires review before production.",
        "tradeoffs": {
            "security": {
                "impact": "positive",
                "summary": "Unsafe deployments are blocked.",
                "evidence_refs": ["src-security-policy"],
                "accepted_risks": [],
            },
            "cost": {
                "impact": "mixed",
                "summary": "Review consumes time but reduces incident cost.",
                "evidence_refs": [],
                "accepted_risks": ["Additional review cost"],
            },
            "compliance": {
                "impact": "positive",
                "summary": "Creates evidence of pre-deployment review.",
                "evidence_refs": ["src-security-policy"],
                "accepted_risks": [],
            },
            "operations": {
                "impact": "mixed",
                "summary": "Adds a gate to the delivery path.",
                "evidence_refs": [],
                "accepted_risks": ["Longer lead time"],
            },
        },
        "authority": {
            "authority_status": "authoritative",
            "decision_owner": "Security",
            "deciders": [],
            "approvers": [],
            "delegation_ref": None,
        },
        "provenance": {
            "sources": [
                {
                    "id": "src-security-policy",
                    "uri": "sharepoint://security/policy",
                    "title": "Production Security Policy",
                    "authority_status": "authoritative",
                    "digest": None,
                }
            ],
            "activities": [
                {
                    "id": "extract-1",
                    "type": "extraction",
                    "timestamp": "2026-10-01T08:00:00Z",
                    "used": ["src-security-policy"],
                    "associated_agents": ["ape-context"],
                }
            ],
            "agents": [
                {
                    "id": "ape-context",
                    "type": "software-agent",
                    "name": "Ape Context",
                    "role": "draft generator",
                    "acted_on_behalf_of": None,
                }
            ],
        },
        "lifecycle": {
            "created_at": "2026-10-01T08:00:00Z",
            "effective_at": None,
            "review_by": None,
            "expires_at": None,
            "review_triggers": ["security policy changes"],
        },
        "consequences": {
            "positive": ["Security review becomes structurally unavoidable"],
            "negative": ["Deployments may wait for remediation"],
            "risks": ["Security analyzer false positives"],
            "actions": ["Implement the blocking gate"],
        },
        "implementation": {
            "policy_refs": ["policy/security-gate"],
            "artifact_refs": [".github/copilot-instructions.md"],
            "evidence_refs": [],
        },
        "relationships": {
            "revises": None,
            "supersedes": None,
            "invalidates": None,
            "implements": [],
            "depends_on": [],
        },
        "autonomy": {
            "proceed": ["Run read-only security analysis"],
            "always_ask": ["Accept residual security risk"],
            "never": ["Deploy while blocking findings remain"],
        },
        "gaps": ["Named human approver not yet supplied"],
        "ratification": None,
    }


class DecisionRecordsTest(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def ratified_record(
        self,
        root: Path,
        *,
        effective_at: str | None = None,
        review_by: str | None = None,
        expires_at: str | None = None,
        authority_status: str = "authoritative",
    ) -> Path:
        draft = root / f"draft-{uuid.uuid4()}.json"
        output = root / f"ratified-{uuid.uuid4()}.json"
        record = draft_record()
        record["lifecycle"]["effective_at"] = effective_at
        record["lifecycle"]["review_by"] = review_by
        record["lifecycle"]["expires_at"] = expires_at
        record["authority"]["authority_status"] = authority_status
        draft.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        result = self.run_cli(
            "ratify",
            "--target",
            str(draft),
            "--output",
            str(output),
            "--confirmed-by",
            "source approver",
            "--approval-meaning",
            "Approved at source.",
            "--context-fingerprint",
            "sha256:" + "c" * 64,
            "--timestamp",
            "2026-09-01T08:00:00Z",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return output

    def test_validate_fingerprint_render_and_ratify(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = root / "draft.json"
            ratified = root / "ADR-0001" / "v001.json"
            rendered = root / "ADR-0001" / "v001.md"
            draft.write_text(json.dumps(draft_record()), encoding="utf-8")

            valid = self.run_cli("validate", "--target", str(draft))
            self.assertEqual(valid.returncode, 0, valid.stderr)

            digest = self.run_cli("fingerprint", "--target", str(draft))
            self.assertEqual(digest.returncode, 0, digest.stderr)
            self.assertRegex(digest.stdout.strip(), r"^sha256:[0-9a-f]{64}$")

            result = self.run_cli(
                "ratify",
                "--target",
                str(draft),
                "--output",
                str(ratified),
                "--confirmed-by",
                "current user",
                "--authority-role",
                "platform owner",
                "--approval-meaning",
                "Approves this decision for the recorded scope.",
                "--context-fingerprint",
                "sha256:" + "a" * 64,
                "--accepted-warning",
                "Named approver identity remains a gap.",
                "--timestamp",
                "2026-10-01T08:30:00Z",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            stored = json.loads(ratified.read_text(encoding="utf-8"))
            self.assertEqual(stored["status"], "ratified")
            self.assertEqual(
                stored["ratification"]["record_fingerprint"],
                json.loads(result.stdout)["fingerprint"],
            )

            checked = self.run_cli(
                "validate", "--target", str(ratified), "--require-ratified"
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)

            result = self.run_cli(
                "render",
                "--target",
                str(ratified),
                "--output",
                str(rendered),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            text = rendered.read_text(encoding="utf-8")
            self.assertIn("# ADR-0001:", text)
            self.assertIn("## Ratification", text)
            self.assertIn("Blocking security gate", text)

            render_overwrite = self.run_cli(
                "render",
                "--target",
                str(ratified),
                "--output",
                str(rendered),
            )
            self.assertEqual(render_overwrite.returncode, 2)
            self.assertIn("refusing to overwrite", render_overwrite.stderr)

            overwrite = self.run_cli(
                "ratify",
                "--target",
                str(draft),
                "--output",
                str(ratified),
                "--confirmed-by",
                "current user",
                "--approval-meaning",
                "Duplicate",
                "--context-fingerprint",
                "sha256:" + "a" * 64,
            )
            self.assertEqual(overwrite.returncode, 2)
            self.assertIn("refusing to overwrite", overwrite.stderr)

    def test_rejects_unknown_selected_alternative(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "invalid.json"
            record = draft_record()
            record["selected_alternative"] = "missing"
            target.write_text(json.dumps(record), encoding="utf-8")
            result = self.run_cli("validate", "--target", str(target))
            self.assertEqual(result.returncode, 2)
            self.assertIn("selected_alternative", result.stderr)

    def test_rejects_missing_authority_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "invalid.json"
            record = draft_record()
            del record["authority"]
            record["provenance"]["sources"] = []
            target.write_text(json.dumps(record), encoding="utf-8")
            result = self.run_cli("validate", "--target", str(target))
            self.assertEqual(result.returncode, 2)
            self.assertIn("record keys", result.stderr)

    def test_ratification_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = root / "draft.json"
            ratified = root / "ratified.json"
            draft.write_text(json.dumps(draft_record()), encoding="utf-8")
            result = self.run_cli(
                "ratify",
                "--target",
                str(draft),
                "--output",
                str(ratified),
                "--confirmed-by",
                "current user",
                "--approval-meaning",
                "Approved",
                "--context-fingerprint",
                "sha256:" + "b" * 64,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads(ratified.read_text(encoding="utf-8"))
            record["decision_statement"] = "Tampered decision"
            ratified.write_text(json.dumps(record), encoding="utf-8")
            checked = self.run_cli(
                "validate", "--target", str(ratified), "--require-ratified"
            )
            self.assertEqual(checked.returncode, 2)
            self.assertIn("fingerprint does not match", checked.stderr)

    def test_assesses_lifecycle_and_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            active = self.ratified_record(
                root,
                effective_at="2026-09-01T00:00:00Z",
                review_by="2026-12-01T00:00:00Z",
                expires_at="2027-01-01T00:00:00Z",
            )
            result = self.run_cli(
                "assess",
                "--target",
                str(active),
                "--as-of",
                "2026-10-01T09:00:00Z",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                json.loads(result.stdout)["assessment"]["eligibility"], "eligible"
            )

            expired = self.ratified_record(
                root, expires_at="2026-09-30T00:00:00Z"
            )
            result = self.run_cli(
                "assess",
                "--target",
                str(expired),
                "--as-of",
                "2026-10-01T09:00:00Z",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                json.loads(result.stdout)["assessment"]["eligibility"], "expired"
            )

            review_due = self.ratified_record(
                root, review_by="2026-09-30T00:00:00Z"
            )
            result = self.run_cli(
                "assess",
                "--target",
                str(review_due),
                "--as-of",
                "2026-10-01T09:00:00Z",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                json.loads(result.stdout)["assessment"]["eligibility"],
                "review_required",
            )

            future = self.ratified_record(
                root, effective_at="2026-10-02T00:00:00Z"
            )
            result = self.run_cli(
                "assess",
                "--target",
                str(future),
                "--as-of",
                "2026-10-01T09:00:00Z",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                json.loads(result.stdout)["assessment"]["eligibility"],
                "not_yet_effective",
            )

            advisory = self.ratified_record(root, authority_status="advisory")
            result = self.run_cli(
                "assess",
                "--target",
                str(advisory),
                "--as-of",
                "2026-10-01T09:00:00Z",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                json.loads(result.stdout)["assessment"]["eligibility"],
                "authority_review_required",
            )

    def test_imports_verbatim_snapshot_with_source_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.ratified_record(root)
            snapshot = root / "imported" / "ADR-0001" / "v001.json"
            metadata = root / "imported" / "ADR-0001" / "v001.source.json"
            source_bytes = source.read_bytes()
            result = self.run_cli(
                "import",
                "--target",
                str(source),
                "--snapshot",
                str(snapshot),
                "--metadata-output",
                str(metadata),
                "--source-uri",
                "sharepoint://architecture/ADR-0001/v001.json",
                "--source-etag",
                '"source-version-3"',
                "--retrieved-at",
                "2026-10-01T09:00:00Z",
                "--as-of",
                "2026-10-01T09:00:00Z",
                "--confirm-scope",
                "--accept-authority",
                "--acceptance-basis",
                "Trusted architecture authority",
                "--accepted-by",
                "current user",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(snapshot.read_bytes(), source_bytes)
            sidecar = json.loads(metadata.read_text(encoding="utf-8"))
            self.assertEqual(sidecar["local_disposition"], "accepted")
            self.assertEqual(
                sidecar["source_uri"],
                "sharepoint://architecture/ADR-0001/v001.json",
            )
            self.assertEqual(
                sidecar["source_digest"],
                "sha256:" + __import__("hashlib").sha256(source_bytes).hexdigest(),
            )

            validated = self.run_cli(
                "validate-source", "--target", str(metadata)
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)

            checked = self.run_cli(
                "check-source",
                "--target",
                str(source),
                "--metadata",
                str(metadata),
                "--checked-at",
                "2026-10-02T09:00:00Z",
                "--source-etag",
                '"source-version-3"',
                "--update-metadata",
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(json.loads(checked.stdout)["comparison"], "unchanged")
            self.assertEqual(
                json.loads(metadata.read_text(encoding="utf-8"))["last_checked_at"],
                "2026-10-02T09:00:00Z",
            )

            overwrite = self.run_cli(
                "import",
                "--target",
                str(source),
                "--snapshot",
                str(snapshot),
                "--metadata-output",
                str(metadata),
                "--source-uri",
                "sharepoint://architecture/ADR-0001/v001.json",
            )
            self.assertEqual(overwrite.returncode, 2)
            self.assertIn("refusing to overwrite", overwrite.stderr)

    def test_import_without_local_acceptance_stays_needs_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.ratified_record(root)
            snapshot = root / "snapshot.json"
            metadata = root / "snapshot.source.json"
            result = self.run_cli(
                "import",
                "--target",
                str(source),
                "--snapshot",
                str(snapshot),
                "--metadata-output",
                str(metadata),
                "--source-uri",
                "https://example.test/ADR-0001.json",
                "--as-of",
                "2026-10-01T09:00:00Z",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            sidecar = json.loads(metadata.read_text(encoding="utf-8"))
            self.assertEqual(sidecar["local_disposition"], "needs_review")
            self.assertIsNone(sidecar["accepted_by"])
            self.assertFalse(sidecar["scope_confirmed"])

    def test_changed_source_requires_new_import(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.ratified_record(root)
            snapshot = root / "snapshot.json"
            metadata = root / "snapshot.source.json"
            imported = self.run_cli(
                "import",
                "--target",
                str(source),
                "--snapshot",
                str(snapshot),
                "--metadata-output",
                str(metadata),
                "--source-uri",
                "https://example.test/ADR-0001.json",
                "--as-of",
                "2026-10-01T09:00:00Z",
            )
            self.assertEqual(imported.returncode, 0, imported.stderr)
            changed = json.loads(source.read_text(encoding="utf-8"))
            changed["decision_statement"] = "A changed source decision."
            source.write_text(json.dumps(changed), encoding="utf-8")

            checked = self.run_cli(
                "check-source",
                "--target",
                str(source),
                "--metadata",
                str(metadata),
            )
            self.assertEqual(checked.returncode, 2)
            self.assertIn("fingerprint does not match", checked.stderr)


if __name__ == "__main__":
    unittest.main()
