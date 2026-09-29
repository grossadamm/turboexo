# Spartan manufacturer manuals

Downloaded 2026-09-28 from 14Point7’s official documentation page.
User confirms the earlier OEM module has been replaced by a non-OEM Spartan with
the separate status wire. The Spartan 3 v2 manual documents that brown wire.
Exact installed hardware/firmware revision has not been read back.

- [Spartan_3_v2_User_Manual_2026-01-21.pdf](Spartan_3_v2_User_Manual_2026-01-21.pdf)
  - Source: https://cdn.shopify.com/s/files/1/0189/1312/files/Spartan_3_v2_User_Manual_a3aca744-bca6-4148-8214-e93e0c07858a.pdf?v=1768973819
  - SHA-256: `9f8f4e8a76707642d7cb40af484ee79c4f6204663ccfb49b2cc73814717e1857`
- [Spartan_3_User_Manual_2023-11-24.pdf](Spartan_3_User_Manual_2023-11-24.pdf)
  - Source: https://cdn.shopify.com/s/files/1/0189/1312/files/Spartan_3_User_Manual_Nov_24_2023_8629a08a-df06-4e93-9b34-cf4a83a73ccb.pdf?v=1700880083
  - SHA-256: `cee84c0d4f0577aa56c6472d3387856461795ce544030cc7de42fda6f861f7ee`

## Status output (Spartan 3 v2, page 1 and page 3)

Brown standard-performance analog output defaults to heater status:
0 V = waiting for trigger; 1 V = heat-up started; 2 V = heat-up complete,
heater in closed-loop control. `GETNBMODE` reads the output function;
mode 2 is heater status, mode 0 simulated narrowband. These are analog
voltages, not the separate CAN status codes 1/2/3.

Aux0/WideBandStatus warm log values 565–604 ADC counts must not be relabelled
2 V ready without verifying the input transfer or actual brown-wire voltage.
At an assumed direct 10-bit/5 V conversion those counts represent 2.76–2.95 V,
which does not match the manual's nominal 2 V. This mismatch does not itself
prove the sensor is unready; measurement or firmware behavior needs checking.
Readiness also does not verify AFR analog calibration.


## UA4C hardware documents

- [Official UA4C connection sheet](https://github.com/turboedge/SpeedyBoards/blob/master/UA4C/DOC/Connections.pdf)
  — local copy `../../tmp/pdfs/UA4C-Connections.pdf`.
- [Official vC5 White Fang schematic](https://github.com/turboedge/SpeedyBoards/blob/master/UA4C/vC5-WHITE%20FANG/SCHEM/UA4C-vC5.pdf)
  — local copy `../../tmp/pdfs/UA4C-vC5.pdf`; input conditioning on page 5.
- [Assembly instructions](https://github.com/turboedge/SpeedyBoards/blob/master/UA4C/DOC/Assembly%20Instructions.pdf)
  — physical assembly; does not establish JP7/JP8 factory configuration.

See [expected voltage/status readings and jumper configuration](../WIRING.md#expected-spartan-status-connection-and-readings).
Actual installed board revision/jumper positions remain unverified. Do not apply
Speeduino v0.4 pinouts to the UA4C.
