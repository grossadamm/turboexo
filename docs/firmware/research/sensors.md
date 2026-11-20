# External fuel and oil-temperature input evidence

The sensor-carrier work and firmware were integrated on main on 2026-11-20.
These facts were originally checked against sensor-carrier commit `9a0827c`.
The owning references are [REFERENCE.md](../../REFERENCE.md), the
[Rev H specification](../../hardware/ads1115/revH/layout_spec.json), and the
[physical build checkpoint](../../hardware/ads1115/BUILD_STATUS.md).

- The carrier uses an ADS1115-style blue ten-pin breakout, intended at 3.3 V.
  Rev H routes fuel to A0 and oil temperature to A1. The exact breakout vendor,
  pull-ups and powered physical operation are unverified.
- Fuel is the original 1999 Miata sender with the old gauge disconnected. The
  user's measured very-empty observation was **110 ohms**. Factory float
  inspection points in the referenced Mazda workshop manual were 6.4–7.6 ohms
  full, 31.8–33.2 halfway, and 93–97 empty. These are not a measured tank-volume
  curve and must not overwrite the user's observation. Rev H's 1 kohm pull-up
  at nominal 3.3 V is a bench starting point, not final calibration.
- Oil temperature is a Dweekiy B07ZYWMV89 single-stud, body-grounded sender.
  Its resistance-temperature curve and appropriate bias are not established;
  R3 oil bias is unpopulated and J3 was to remain disconnected. A lookalike
  sender's curve is not equivalent evidence.
- The last saved assembly checkpoint has H1 header relocation pending and no
  confirmed powered ADC communication. Pi stacking/wake circuitry is not a P4
  pin map and must not be connected by inference.

Consequently the P4 adapter uses an explicit optional ADS1115 configuration,
raw ADC-to-engineering calibration knots supplied after measurement, A0/A1
channel defaults, and no production calibration values. Invalid/unconfigured
calibration produces unavailable engineering readings, not guessed percentages
or temperatures. Replay still populates these fields with conspicuously
identified synthetic values as accepted in the visual mocks.

P4 external I²C and connector candidates are in [board.md](board.md). Validate
3.3 V bus levels, the actual carrier pin map, channel assignment, supply and
known-point measurements before enabling these inputs. This is firmware
configuration support; it does not authorize modifying the physical carrier.
