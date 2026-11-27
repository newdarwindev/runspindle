import unittest

from tools.platform_fleet_freshness import CALLS, IDENTITY, run


class PlatformFleetFreshnessTest(unittest.TestCase):
    def test_exact_platform_pin_capacity_and_restart_observations(self) -> None:
        report = run()
        self.assertEqual(report["real_component"], "platform")
        self.assertEqual(report["repeat_runs"], 2)
        self.assertEqual(report["system_aggregate"], "blocked")
        self.assertEqual(len(report["components"]), 7)
        cases = {sample["case"]: sample for sample in report["observations"]}
        self.assertEqual(cases["fresh-idle"]["capacity"]["available_slots"], 2)
        self.assertEqual(cases["fresh-owned"]["capacity"]["available_slots"], 1)
        self.assertEqual(cases["old-owner"]["capacity"]["available_slots"], 0)
        self.assertEqual(cases["owner-recovered"]["capacity"]["available_slots"], 1)
        self.assertEqual(cases["owner-recovered"]["reservations"][0][0], IDENTITY)
        self.assertEqual(
            cases["owner-recovered"]["events"], cases["old-owner"]["events"]
        )
        self.assertEqual(cases["missing-heartbeat"]["heartbeat"], None)
        for sample in cases.values():
            self.assertEqual(
                sample["calls"], [["store", "read", "fleet.sqlite"], *CALLS]
            )
            self.assertEqual(sample["forbidden"], [])
            self.assertEqual(sample["durable_changes"], 0)

    def test_mutated_platform_guest_ownership_cannot_pass(self) -> None:
        with self.assertRaisesRegex(ValueError, "old-owner: capacity mismatch"):
            run(mutation=True)


if __name__ == "__main__":
    unittest.main()
