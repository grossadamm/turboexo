# Sensor carrier build checkpoint — 2026-11-05

## Resume here: H1 relocation pending

User is pausing the build and will move the header later. **Do not assume H1
has been moved or that the carrier is ready to plug onto the Pi.**

Latest electrical/layout artifacts: [Rev H layout](revH/ADS1115_sensor_board_revH.diy),
[specification](revH/layout_spec.json), and
[soldering guide](../../../output/pdf/ADS1115_sensor_board_revH_soldering_guide.pdf).
Earlier revisions are retained as history, not alternative current build instructions.

## Actual assembly versus the drawing

- User soldered H1 and U1 and subsequently assembled the carrier and optocoupler
  cables. Top and underside photos were supplied in this conversation; their
  temporary attachment files were unavailable when this checkpoint was committed.
  The older component reference images remain saved in sensor-board-components/.
- H1 is a standard female header with socket openings on the component side and
  soldered metal tails underneath, confirmed by the user. It is NOT the intended
  underside-facing stacking socket. The Rev H drawing/guide has not been revised
  for this actual header or the proposed relocation.
- The guide combined an underside female socket with underside wire terminations
  at H1. The socket body would obstruct those joints. That was a mechanical design
  error, compounded by telling the user to plug the photographed assembly directly
  onto the Pi before checking the header.
- User proposes shifting H1, facing its socket underneath, retaining the existing
  wired pads, and passing short insulated wires through adjacent free holes to
  solder to H1 on top. This is a proposed repair, NOT a checked placement or pin map.
- Before desoldering: establish exact shift, socket mating orientation, Pi pin 1,
  five signal destinations, header lead reach, cooler clearance and support. No
  exact relocation coordinates have been agreed or verified. Preserve the rest of
  the soldered assembly. Short-tail headers will not provide the original upper
  stacking pins for UPS jumpers; the UPS connection still needs accommodation.
- Intended physical Pi pins: 1=3.3V, 3=SDA, 5=SCL, 9=GND, 13=GPIO27 brake.
  Carrier H1 currently uses only that odd-numbered row. Verify new mating mapping;
  do not infer it merely by shifting one row or flipping the header.

## Results and open checks

- User measured **1.5–2 MΩ** between the carrier power and ground buses and confirmed
  the capital M unit. This indicates no direct short for that measurement only.
- User reported doing several other checks, but did not provide their individual
  results. Do not mark them as passed or invent powered-test results.
- No successful powered carrier voltage measurement, ADC communication, optocoupler
  output low/release test, automatic wake, or completed Pi connection is confirmed.
- Photo review could not resolve crowded joints at the right end of the upper bus
  or all insulated crossings. Model validation is not assembly validation.
- Separate button lead J5 remains pending output verification; oil J3 stays
  disconnected pending sender characterization. GPIO27 availability remains open.

## Latest circuit changes and connector meanings

Rev G removed filter positions and bypass links, then rerouted W18 clear of wake
terminals and corrected R9's PDF body size. Faint pad labels were added to page 2.
Rev H adds only J8 and W33/W34; every previous part, bus and wire route is unchanged.
Independent review and generated connectivity checks passed for those additions.

| Header | Connection |
|---|---|
| J5 | Pi dedicated J2 button signal/return; separate from H1 GPIO header |
| J6 | External optocoupler OUT/GND |
| J7 | Switched regulated charger trigger +/−, nominal 12.6V; not raw vehicle power |
| J8 | Optocoupler INPUT+ at (19,13), INPUT− at (20,13) |

W33: D1 banded/K pad (21,5) to J8+. W34: R7 return pad (23,9), via (23,13),
to J8−. W33 crosses the bare 3.3V bus and must remain insulated. Optocoupler VCC
is unused in this design. The later close-up shows a PC817C marking; it does not
establish installed resistor measurements, CTR or loaded output behavior.

Wake behavior is still conditional: short off/on cycles can leave C6 charged and
weaken the next pulse. Test actual output low/release and restart behavior before
connecting it to Pi J2. The input LED flashing is not proof of output operation.

## Regeneration

Current generator: `scripts/generate_ads1115_opto_header_layout.py` from repository
root. Requires Python/reportlab, Java/Javac and DIYLC JAR at the path in the script.
It reads Rev H layout_spec.json and writes native layout/preview, validation JSON
and the PDF. Temporary Java/render files under tmp/pdfs are disposable and excluded
from this checkpoint commit. Do not regenerate as a substitute for designing the
pending H1 repair.
