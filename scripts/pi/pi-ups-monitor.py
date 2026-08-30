#!/usr/bin/env python3

from __future__ import annotations

import argparse
import logging
import signal
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

I2C_BUS = 1
I2C_ADDRESS = 0x41
SAMPLE_INTERVAL_SECONDS = 0.5
KEY_STATE_CONNECTED = "1"
KEY_STATE_DISCHARGING = "0"

REG_CONFIGURATION = 0x00
REG_SHUNT_VOLTAGE = 0x01
REG_BUS_VOLTAGE = 0x02

CONTINUOUS_SHUNT_AND_BUS_MODE = 0x07
CONVERSION_READY_BIT = 0x0002
OVERFLOW_BIT = 0x0001
SHUNT_AMPS_PER_BIT = 0.001
BUS_VOLTS_PER_BIT = 0.004


class WordBus(Protocol):
    def read_word_data(self, address: int, register: int) -> int: ...

    def close(self) -> None: ...


@dataclass(frozen=True)
class Sample:
    valid: bool
    reason: str
    current_a: float | None = None
    bus_voltage_v: float | None = None


def swap_word(value: int) -> int:
    value &= 0xFFFF
    return ((value & 0xFF) << 8) | (value >> 8)


def signed_word(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def read_sample(bus: WordBus) -> Sample:
    try:
        configuration = swap_word(bus.read_word_data(I2C_ADDRESS, REG_CONFIGURATION))
        shunt_raw = signed_word(swap_word(bus.read_word_data(I2C_ADDRESS, REG_SHUNT_VOLTAGE)))
        bus_raw = swap_word(bus.read_word_data(I2C_ADDRESS, REG_BUS_VOLTAGE))
    except OSError:
        return Sample(valid=False, reason="i2c_error")

    if configuration & 0x07 != CONTINUOUS_SHUNT_AND_BUS_MODE:
        return Sample(valid=False, reason="not_continuous")
    if bus_raw & OVERFLOW_BIT:
        return Sample(valid=False, reason="overflow")
    if not bus_raw & CONVERSION_READY_BIT:
        return Sample(valid=False, reason="not_ready")

    return Sample(
        valid=True,
        reason="ok",
        current_a=shunt_raw * SHUNT_AMPS_PER_BIT,
        bus_voltage_v=(bus_raw >> 3) * BUS_VOLTS_PER_BIT,
    )


class ObservationMonitor:
    def __init__(
        self,
        threshold_a: float,
        delay_seconds: float,
        emit: Callable[[str], None],
        request_poweroff: Callable[[], None] | None = None,
        publish_key_state: Callable[[str], None] | None = None,
    ) -> None:
        if threshold_a >= 0:
            raise ValueError("threshold must be negative")
        if delay_seconds <= 0:
            raise ValueError("delay must be positive")

        self._threshold_a = threshold_a
        self._delay_seconds = delay_seconds
        self._emit = emit
        self._request_poweroff = request_poweroff
        self._publish_key_state = publish_key_state
        self._published_key_state: str | None = None
        self._publish_failed = False
        self._state = "starting"
        self._discharge_started_at: float | None = None
        self._latched = False

    def process(self, sample: Sample, now: float) -> None:
        if not sample.valid or sample.current_a is None:
            self._discharge_started_at = None
            self._transition("invalid", f"sample_invalid reason={sample.reason}")
            return

        if sample.current_a > self._threshold_a:
            self._discharge_started_at = None
            self._latched = False
            self._publish_valid_key_state("connected")
            self._transition("connected", self._message("connected", sample))
            return

        if self._latched:
            return

        if self._discharge_started_at is None:
            self._discharge_started_at = now
            self._publish_valid_key_state("discharging")
            self._transition("discharging", self._message("discharge_started", sample))
            return

        elapsed = now - self._discharge_started_at
        if elapsed < self._delay_seconds:
            return

        self._latched = True
        if self._request_poweroff is None:
            self._transition("latched", self._message("would_poweroff", sample))
            return

        self._transition("latched", self._message("poweroff_requested", sample))
        self._request_poweroff()

    def _publish_valid_key_state(self, state: str) -> None:
        if self._publish_key_state is None or state == self._published_key_state:
            return
        try:
            self._publish_key_state(state)
        except OSError as error:
            if not self._publish_failed:
                self._emit(f"key_state_publish_failed error={type(error).__name__}")
            self._publish_failed = True
            return
        if self._publish_failed:
            self._emit(f"key_state_publish_recovered state={state}")
        self._publish_failed = False
        self._published_key_state = state

    def _transition(self, state: str, message: str) -> None:
        if state == self._state:
            return
        self._state = state
        self._emit(message)

    @staticmethod
    def _message(event: str, sample: Sample) -> str:
        bus_voltage = "unknown" if sample.bus_voltage_v is None else f"{sample.bus_voltage_v:.3f}"
        return f"{event} current_a={sample.current_a:.3f} bus_voltage_v={bus_voltage}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Monitor sustained Waveshare UPS discharge")
    parser.add_argument("--threshold-amps", type=float, default=-0.20)
    parser.add_argument("--delay-seconds", type=float, default=240.0)
    parser.add_argument(
        "--poweroff",
        action="store_true",
        help="cleanly power off the OS after sustained discharge",
    )
    parser.add_argument(
        "--key-state-path",
        type=Path,
        help="gpio-mockup control used to publish connected=1/discharging=0",
    )
    return parser


class KeyStatePublisher:
    def __init__(self, path: Path) -> None:
        self._path = path

    def __call__(self, state: str) -> None:
        values = {
            "connected": KEY_STATE_CONNECTED,
            "discharging": KEY_STATE_DISCHARGING,
        }
        try:
            value = values[state]
        except KeyError as error:
            raise ValueError(f"unsupported key state: {state}") from error
        self._path.write_text(value + "\n", encoding="ascii")


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.threshold_amps >= 0:
        raise SystemExit("--threshold-amps must be negative")
    if arguments.delay_seconds <= 0:
        raise SystemExit("--delay-seconds must be positive")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger = logging.getLogger("pi-ups-monitor")
    stop = threading.Event()

    def request_stop(_signum: int, _frame: object) -> None:
        stop.set()

    def request_poweroff() -> None:
        logger.info("poweroff_command command=systemctl poweroff")
        try:
            result = subprocess.run(
                ["/usr/bin/sudo", "-n", "/usr/bin/systemctl", "poweroff"],
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            logger.error("poweroff_failed error=%s", type(error).__name__)
            return
        if result.returncode != 0:
            logger.error("poweroff_failed returncode=%d", result.returncode)

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    try:
        import smbus

        bus = smbus.SMBus(I2C_BUS)
    except (ImportError, OSError) as error:
        logger.error("monitor_start_failed error=%s", type(error).__name__)
        return 1

    monitor = ObservationMonitor(
        threshold_a=arguments.threshold_amps,
        delay_seconds=arguments.delay_seconds,
        emit=logger.info,
        request_poweroff=request_poweroff if arguments.poweroff else None,
        publish_key_state=(
            KeyStatePublisher(arguments.key_state_path)
            if arguments.key_state_path is not None
            else None
        ),
    )
    logger.info(
        "monitor_started threshold_a=%.3f delay_seconds=%.1f poweroff=%s",
        arguments.threshold_amps,
        arguments.delay_seconds,
        arguments.poweroff,
    )

    try:
        while not stop.is_set():
            started_at = time.monotonic()
            monitor.process(read_sample(bus), started_at)
            remaining = SAMPLE_INTERVAL_SECONDS - (time.monotonic() - started_at)
            stop.wait(max(0.0, remaining))
    finally:
        bus.close()

    logger.info("monitor_stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
