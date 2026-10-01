import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src" / "adrp" / "cli.py"
EXAMPLE = ROOT / "docs" / "examples" / "source-intake-quality.v1.json"


class QualityAssessmentTest(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_valid_quality_assessment(self) -> None:
        result = self.run_cli(
            "validate-quality",
            "--target",
            str(EXAMPLE),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["overall"], "pass_with_warnings")
        self.assertEqual(payload["standing_effect"], "none")

    def test_overall_must_match_dimension_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "quality.json"
            assessment = json.loads(EXAMPLE.read_text(encoding="utf-8"))
            assessment["overall"] = "pass"
            target.write_text(json.dumps(assessment), encoding="utf-8")
            result = self.run_cli(
                "validate-quality",
                "--target",
                str(target),
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("overall must be pass_with_warnings", result.stderr)

    def test_quality_cannot_change_standing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "quality.json"
            assessment = json.loads(EXAMPLE.read_text(encoding="utf-8"))
            assessment["standing_effect"] = "authoritative"
            target.write_text(json.dumps(assessment), encoding="utf-8")
            result = self.run_cli(
                "validate-quality",
                "--target",
                str(target),
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("standing_effect must be none", result.stderr)


if __name__ == "__main__":
    unittest.main()
