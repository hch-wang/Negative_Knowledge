import json
import pathlib
import tempfile
import unittest

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
    def test_validate_is_strict(self):
        self.assertEqual(validate(record()), [])
        bad = record()
        bad["extra"] = True
        bad["observation"] = 42
        self.assertIn("unknown field: extra", validate(bad))
        self.assertIn("observation must be a string", validate(bad))

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


if __name__ == "__main__":
    unittest.main()
