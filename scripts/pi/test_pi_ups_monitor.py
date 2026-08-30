#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("pi-ups-monitor.py")
SPEC = importlib.util.spec_from_file_location("pi_ups_monitor", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class KeyStatePublisherTests(unittest.TestCase):
    def test_maps_valid_states_to_mock_pull_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pull"
            publisher = MODULE.KeyStatePublisher(path)

            publisher("connected")
            self.assertEqual(path.read_text(encoding="ascii"), "1\n")

            publisher("discharging")
            self.assertEqual(path.read_text(encoding="ascii"), "0\n")

    def test_rejects_unknown_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            publisher = MODULE.KeyStatePublisher(Path(directory) / "pull")
            with self.assertRaises(ValueError):
                publisher("invalid")


class ObservationMonitorPublishingTests(unittest.TestCase):
    def make_monitor(self, published: list[str], emitted: list[str]):
        return MODULE.ObservationMonitor(
            threshold_a=-0.20,
            delay_seconds=240,
            emit=emitted.append,
            publish_key_state=published.append,
        )

    def test_publishes_only_valid_connected_and_discharging_transitions(self) -> None:
        published: list[str] = []
        emitted: list[str] = []
        monitor = self.make_monitor(published, emitted)

        monitor.process(MODULE.Sample(True, "ok", 0.1, 12.0), 0.0)
        monitor.process(MODULE.Sample(True, "ok", 0.2, 12.0), 0.5)
        monitor.process(MODULE.Sample(False, "i2c_error"), 1.0)
        monitor.process(MODULE.Sample(True, "ok", 0.1, 12.0), 1.5)
        monitor.process(MODULE.Sample(True, "ok", -0.4, 11.8), 2.0)
        monitor.process(MODULE.Sample(False, "not_ready"), 2.5)

        self.assertEqual(published, ["connected", "discharging"])

    def test_publish_failure_does_not_interrupt_shutdown_monitor(self) -> None:
        attempts = 0
        emitted: list[str] = []

        def fail_once(_state: str) -> None:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise OSError("temporary")

        monitor = MODULE.ObservationMonitor(
            threshold_a=-0.20,
            delay_seconds=240,
            emit=emitted.append,
            publish_key_state=fail_once,
        )
        sample = MODULE.Sample(True, "ok", 0.1, 12.0)

        monitor.process(sample, 0.0)
        monitor.process(sample, 0.5)

        self.assertEqual(attempts, 2)
        self.assertTrue(any("key_state_publish_failed" in item for item in emitted))
        self.assertTrue(any("key_state_publish_recovered" in item for item in emitted))


if __name__ == "__main__":
    unittest.main()
