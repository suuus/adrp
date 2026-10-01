import json
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

from test_cli import draft_record


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "adrp" / "cli.py"


class ResolutionTest(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def write_ratified(
        self,
        root: Path,
        *,
        decision_id: str = "ADR-0001",
        version: int = 1,
        scope: list[str] | None = None,
        depends_on: list[str] | None = None,
        supersedes: str | None = None,
    ) -> Path:
        record = draft_record()
        record["decision_id"] = decision_id
        record["record_id"] = str(uuid.uuid4())
        record["record_version"] = version
        record["context"]["scope"] = scope or ["production deployments"]
        record["relationships"]["depends_on"] = depends_on or []
        record["relationships"]["supersedes"] = supersedes
        draft = root / "drafts" / f"{decision_id}-v{version:03d}.json"
        output = root / decision_id / f"v{version:03d}.json"
        draft.parent.mkdir(parents=True, exist_ok=True)
        draft.write_text(json.dumps(record), encoding="utf-8")
        result = self.run_cli(
            "ratify",
            "--target",
            str(draft),
            "--output",
            str(output),
            "--confirmed-by",
            "test approver",
            "--approval-meaning",
            "Approved for test scope.",
            "--context-fingerprint",
            "sha256:" + "a" * 64,
            "--timestamp",
            "2026-10-01T08:00:00Z",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return output

    def test_resolve_and_autonomy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            active = self.write_ratified(root)

            resolved = self.run_cli(
                "resolve",
                str(active),
                "--scope",
                "production deployments",
                "--as-of",
                "2026-10-01T12:00:00Z",
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr)
            payload = json.loads(resolved.stdout)
            self.assertEqual(payload["schema_version"], "adrp-resolution/v1")
            self.assertEqual(payload["summary"]["active_records"], 1)
            self.assertEqual(payload["active"][0]["decision_id"], "ADR-0001")

            autonomy = self.run_cli(
                "autonomy",
                str(active),
                "--scope",
                "production deployments",
                "--action",
                "Deploy while blocking findings remain",
                "--as-of",
                "2026-10-01T12:00:00Z",
            )
            self.assertEqual(autonomy.returncode, 0, autonomy.stderr)
            autonomy_payload = json.loads(autonomy.stdout)
            self.assertEqual(autonomy_payload["outcome"], "NEVER")
            self.assertEqual(
                autonomy_payload["matches"]["never"][0]["decision_id"],
                "ADR-0001",
            )

    def test_unmatched_action_is_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            active = self.write_ratified(root)
            result = self.run_cli(
                "autonomy",
                str(active),
                "--action",
                "Delete the customer database",
                "--as-of",
                "2026-10-01T12:00:00Z",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["outcome"], "UNRESOLVED")

    def test_missing_dependency_excludes_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            active = self.write_ratified(
                root,
                decision_id="ADR-DEPENDENT",
                depends_on=["ADR-MISSING"],
            )
            result = self.run_cli(
                "resolve",
                str(active),
                "--as-of",
                "2026-10-01T12:00:00Z",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["summary"]["active_records"], 0)
            self.assertIn(
                "missing active dependency: ADR-MISSING",
                payload["excluded"][0]["reasons"],
            )

    def test_superseding_record_removes_previous_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_ratified(root, decision_id="ADR-OLD")
            self.write_ratified(
                root,
                decision_id="ADR-NEW",
                supersedes="ADR-OLD",
            )
            result = self.run_cli(
                "resolve",
                str(root),
                "--as-of",
                "2026-10-01T12:00:00Z",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            active_ids = {item["decision_id"] for item in payload["active"]}
            self.assertEqual(active_ids, {"ADR-NEW"})
            excluded = {
                item["decision_id"]: item["reasons"]
                for item in payload["excluded"]
            }
            self.assertIn("superseded by ADR-NEW", excluded["ADR-OLD"])

    def test_graph_and_verify_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_ratified(root, decision_id="ADR-BASE")
            self.write_ratified(
                root,
                decision_id="ADR-CHILD",
                depends_on=["ADR-BASE"],
            )

            graph = self.run_cli(
                "graph",
                str(root),
                "--as-of",
                "2026-10-01T12:00:00Z",
            )
            self.assertEqual(graph.returncode, 0, graph.stderr)
            graph_payload = json.loads(graph.stdout)
            self.assertIn(
                {
                    "from": "ADR-CHILD",
                    "to": "ADR-BASE",
                    "type": "depends_on",
                },
                graph_payload["edges"],
            )

            verified = self.run_cli("verify-set", str(root))
            self.assertEqual(verified.returncode, 0, verified.stderr)
            verify_payload = json.loads(verified.stdout)
            self.assertTrue(verify_payload["valid"])
            self.assertEqual(verify_payload["summary"]["records"], 4)

    def test_verify_set_require_ratified_rejects_drafts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = draft_record()
            draft = root / "draft.json"
            draft.write_text(json.dumps(record), encoding="utf-8")
            result = self.run_cli(
                "verify-set",
                str(root),
                "--require-ratified",
            )
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["valid"])
            self.assertIn("ratification must be an object", payload["errors"][0]["error"])

    def test_import_byte_digest_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.write_ratified(root / "source")
            snapshot = root / "imported" / "ADR-0001" / "v001.json"
            sidecar = root / "imported" / "ADR-0001" / "v001.source.json"
            imported = self.run_cli(
                "import",
                "--target",
                str(source),
                "--snapshot",
                str(snapshot),
                "--metadata-output",
                str(sidecar),
                "--source-uri",
                "https://example.org/ADR-0001.json",
                "--confirm-scope",
                "--accept-authority",
                "--acceptance-basis",
                "Applies to this test repository.",
                "--accepted-by",
                "test approver",
                "--as-of",
                "2026-10-01T12:00:00Z",
            )
            self.assertEqual(imported.returncode, 0, imported.stderr)

            unchanged_payload = json.loads(snapshot.read_text(encoding="utf-8"))
            snapshot.write_text(
                json.dumps(unchanged_payload, separators=(",", ":")),
                encoding="utf-8",
            )

            inspected = self.run_cli(
                "inspect",
                str(snapshot),
                "--as-of",
                "2026-10-01T12:00:00Z",
            )
            self.assertEqual(inspected.returncode, 2)
            self.assertIn("byte digest does not match", inspected.stderr)

            verified = self.run_cli("verify-set", str(root / "imported"))
            self.assertEqual(verified.returncode, 1)
            verify_payload = json.loads(verified.stdout)
            self.assertFalse(verify_payload["valid"])
            self.assertTrue(
                any(
                    "byte digest does not match" in item["error"]
                    for item in verify_payload["errors"]
                )
            )


if __name__ == "__main__":
    unittest.main()
