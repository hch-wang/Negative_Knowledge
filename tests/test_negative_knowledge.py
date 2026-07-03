import json
import pathlib
import tempfile
import unittest

import negative_knowledge as nk
from negative_knowledge import append, curate, load, validate


def record():
    return {
        "task_id": "demo",
        "attempted_route": "Import an unavailable package",
        "observation": "ModuleNotFoundError before execution",
        "failure": {
            "layer": "implementation_failure",
            "scope": "local_failure",
            "degree": "artifact_driven",
            "recommended_action": "change_method",
            "risk": "low_risk_omission",
        },
        "rationale": "The required package is absent.",
        "recommended_alternative": "Use the equivalent built-in function.",
    }


class NegativeKnowledgeTests(unittest.TestCase):
    def test_validate_core_contract(self):
        self.assertEqual(validate(record()), [])
        # Extra top-level fields are allowed as extensions.
        extended = record()
        extended["round"] = 2
        self.assertEqual(validate(extended), [])
        # Type errors and unknown failure-subfields are still caught.
        bad = record()
        bad["observation"] = 42
        bad["failure"]["bogus"] = 1
        issues = validate(bad)
        self.assertIn("observation must be a string", issues)
        self.assertIn("unknown field: failure.bogus", issues)

    def test_curate_accepts_a_mapping(self):
        seen = []
        result = curate(
            lambda prompt: seen.append(prompt) or record(),
            task_id="demo",
            task="task",
            evidence={"error": "boom"},
        )
        self.assertEqual(result, record())
        self.assertIn("boom", seen[0])

    def test_curate_accepts_json_code_fences(self):
        payload = "```json\n" + json.dumps(record()) + "\n```"
        self.assertEqual(
            curate(lambda prompt: payload, task_id="demo", task="task", evidence={}),
            record(),
        )

    def test_curate_rejects_invalid_output(self):
        with self.assertRaisesRegex(ValueError, "invalid negative-knowledge"):
            curate(lambda prompt: {}, task_id="demo", task="task", evidence={})

    def test_append_and_load(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "memory.jsonl"
            append(path, record())
            append(path, record())
            self.assertEqual(load(path), [record(), record()])

    def test_missing_memory_is_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(load(pathlib.Path(directory) / "missing.jsonl"), [])

    def test_validate_rejects_null_failure(self):
        bad = record()
        bad["failure"] = None
        self.assertIn("failure must be a JSON object", validate(bad))

    def test_every_vocabulary_value_is_accepted_and_advertised(self):
        vocab = {
            "layer": nk.LAYERS,
            "scope": nk.SCOPES,
            "degree": nk.DEGREES,
            "recommended_action": nk.ACTIONS,
            "risk": nk.RISKS,
        }
        for field, allowed in vocab.items():
            for value in allowed:
                good = record()
                good["failure"][field] = value
                self.assertEqual(validate(good), [], f"{field}={value}")
                self.assertIn(value, nk._PROMPT, f"{value} missing from _PROMPT")
            bad = record()
            bad["failure"][field] = "bogus_value"
            self.assertIn(f"failure.{field} has an unknown value", validate(bad))

    def test_curate_rejects_task_id_mismatch(self):
        with self.assertRaisesRegex(ValueError, "task_id does not match"):
            curate(lambda prompt: record(), task_id="other", task="t", evidence={})

    def test_curate_handles_unclosed_code_fence(self):
        payload = "```json\n" + json.dumps(record())  # truncated: no closing fence
        self.assertEqual(
            curate(lambda prompt: payload, task_id="demo", task="t", evidence={}),
            record(),
        )

    def test_evidence_truncation_boundary(self):
        seen = []

        def backend(prompt):
            seen.append(prompt)
            return record()

        curate(backend, task_id="demo", task="t", evidence={"blob": "x" * 100_000})
        self.assertIn("...[truncated]...", seen[0])
        curate(backend, task_id="demo", task="t", evidence={"blob": "x" * 99_000})
        self.assertNotIn("...[truncated]...", seen[1])

    def test_roundtrip_survives_unicode_line_separators(self):
        rec = record()
        rec["attempted_route"] = "route A\u2028route B\u2029route C\u0085done 中文"
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "memory.jsonl"
            append(path, rec)
            append(path, record())
            self.assertEqual(load(path), [rec, record()])

    def test_load_accepts_utf8_bom(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "memory.jsonl"
            path.write_bytes(
                b"\xef\xbb\xbf" + json.dumps(record()).encode("utf-8") + b"\n"
            )
            self.assertEqual(load(path), [record()])

    def test_load_skips_blank_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "memory.jsonl"
            path.write_text("\n" + json.dumps(record()) + "\n\n", encoding="utf-8")
            self.assertEqual(load(path), [record()])

    def test_load_reports_malformed_json_with_line_number(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "memory.jsonl"
            path.write_text(json.dumps(record()) + "\n{not json}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, r"invalid JSON at .*:2"):
                load(path)

    def test_load_reports_invalid_record_with_line_number(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "memory.jsonl"
            path.write_text(
                json.dumps(record()) + "\n" + json.dumps({"task_id": "x"}) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, r"invalid record at .*:2"):
                load(path)


if __name__ == "__main__":
    unittest.main()
