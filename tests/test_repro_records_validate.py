"""One-directional regression: the paper's shipped NK records must pass
the PUBLIC validate().

This ties the reproduction archive (frozen artifacts) to the released
module without merging the per-study curator forks: any record that
carries the full six-field core is required to satisfy the public
contract. Deep/cross-round synthesis records and legacy bank entries use
different shapes and are out of scope by construction (they lack the
full core field set).
"""
import json
import pathlib
import unittest

import negative_knowledge as nk


ROOT = pathlib.Path(__file__).resolve().parent.parent
REPRODUCTION = ROOT / "reproduction"


def candidate_records(data):
    if isinstance(data, dict):
        yield data
        output_nk = data.get("output_nk")
        if isinstance(output_nk, dict):
            yield output_nk


class ReproRecordsValidateTests(unittest.TestCase):
    def test_shipped_full_records_pass_public_validate(self):
        checked = 0
        for path in sorted(REPRODUCTION.rglob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            for record in candidate_records(data):
                if not (nk.FIELDS <= set(record)):
                    continue
                self.assertEqual(nk.validate(record), [], str(path))
                checked += 1
        # 67 such records at the time of writing; guard against the test
        # silently checking nothing if the archive layout changes.
        self.assertGreaterEqual(checked, 60)


if __name__ == "__main__":
    unittest.main()
