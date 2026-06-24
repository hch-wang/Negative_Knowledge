import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

from reproduction.agent_command import resolve_model, run_subagent


class AgentCommandTests(unittest.TestCase):
    def test_json_protocol_and_model_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            adapter = root / "adapter.py"
            request_copy = root / "request.json"
            adapter.write_text(
                "import json, pathlib, sys\n"
                "request = json.load(sys.stdin)\n"
                f"pathlib.Path({str(request_copy)!r}).write_text(json.dumps(request))\n"
                "print(json.dumps({'tokens_in': 2, 'tokens_out': 3}))\n"
            )
            command = f"{sys.executable} {adapter}"
            with mock.patch.dict(os.environ, {"NK_MODEL_FAST": "local-fast"}):
                result = run_subagent(
                    "prompt",
                    "fast",
                    {str(root / "input.txt")},
                    {str(root / "output.txt")},
                    command=command,
                )
                self.assertEqual(resolve_model("fast"), "local-fast")
            request = json.loads(request_copy.read_text())
            self.assertEqual(request["protocol"], "negative-knowledge-agent-command/v1")
            self.assertEqual(request["model"], "local-fast")
            self.assertEqual(result["total_tokens"], 5)

    def test_missing_command_has_actionable_error(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "NK_AGENT_COMMAND"):
                run_subagent("prompt", "default", set(), set())


if __name__ == "__main__":
    unittest.main()
