from __future__ import annotations

import unittest

from spark_plan_doctor.parser import parse_plan_features

from sample_plans import SAMPLE_PLAN


class ParserTests(unittest.TestCase):
    def test_parse_plan_features(self) -> None:
        features = parse_plan_features(SAMPLE_PLAN)

        self.assertEqual(2, features.exchange_count)
        self.assertEqual(2, features.sort_count)
        self.assertEqual(1, features.python_eval_count)
        self.assertTrue(features.no_partition_pruning_signal)
        self.assertTrue(features.full_scan_signal)


if __name__ == "__main__":
    unittest.main()
