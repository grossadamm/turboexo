# Pi Wi-Fi hotspot implementation plan

2026-10-10. Implemented: hotspot services are active and enabled at boot.

## Implementation result

- `TurboExo` hotspot on `ap0`, `192.168.50.1/24`; DHCP `.20`–`.100`.
- Existing home Wi-Fi remains on `wlan0`. Both use channel 40 / 5200 MHz.
- Station scans/selection are limited to 5200 MHz with automatic retry every 30 seconds. No manual driving mode was added.
- Dash Echo remains unchanged on TCP 21848. The Mac must join `TurboExo` to use `192.168.50.1:21848`; on home Wi-Fi the existing endpoint is `192.168.1.134:21848`.
- The Mac was returned to home Wi-Fi for Internet after testing. The hotspot intentionally does not advertise an Internet gateway or DNS server.
- Corrected loss/return trial: 76/76 HTTP checks passed; station automatically returned after about 26 seconds, with no forced reconnect.
- Fresh AP startup while home was unavailable: the Mac joined while the station was SCANNING; 72/72 HTTP checks passed; home returned automatically in 26.06 seconds.
- TunerStudio connected through Dash Echo during the trial. Its later offline event followed the intentional AP stop used to return the Mac to home Wi-Fi.
- Boot enablement is configured, but a full cold boot away from home and sustained road/sleep testing remain unverified.

The first failed recovery result was a test-script bug: `SET_NETWORK bssid 00:00:00:00:00:00` pins a zero BSSID rather than clearing it. The corrected script restores `any`, verifies the original unset state, and then measures automatic recovery. That first result is not evidence that the single-radio configuration cannot work.

Deployment source: `scripts/pi/wifi/`. Protected live configuration: `/etc/turboexo/wifi/`. The generated hotspot passphrase is in root-readable `hostapd.conf`, not this repository. Rollback: `sudo /var/backups/turboexo-wifi/20261010T190927Z/rollback.sh` on the Pi. No trial rollback or return-home timer remains scheduled. The rollback leaves the installed packages in place but removes the hotspot services/configuration and restores the prior station file.

The remainder records the implementation design. Existing TSDash, ECU tune, logging and UPS settings were not changed by this work.

## Existing setup — carry forward

Dash Echo already works. In the chat “Find Dash Echo client port”, it was enabled on the Pi and the user confirmed “connected”. The Mac project uses `192.168.1.134:21848`. The Mac's TunerStudio debug log on October 10 at 11:11:14 records a successful controller connection over that endpoint and matching page checksums. Do not repeat activation, licensing, port discovery, or home-LAN setup.

The Pi already runs TSDash over ECU USB, with its established startup, logging, backup, key-input and UPS-shutdown configuration. This task changes network access to that existing service; it does not rebuild those systems or claim that all historical logging issues are resolved.

Read-only inspection established Pi 5 / DietPi 10.4 RC2 / Debian 13.5, kernel `6.18.39+rpt-rpi-2712`, `brcmfmac`, and ifupdown with wpa_supplicant. One radio supports one client plus one AP on **one shared channel**. Home Wi-Fi `exterminate` currently uses channel 40. These facts are the baseline, not another research checklist.

## What to implement

1. **Prepare recovery.** Back up only the network files and service state being changed. Arrange a local timed rollback and an independent recovery route before touching the sole SSH uplink. Keep credentials out of Git. Preserve the current power/shutdown behavior.

2. **Add `ap0` alongside `wlan0`.** Keep existing home Wi-Fi credentials and ifupdown. Use hostapd for the virtual AP and a DHCP service bound only to `ap0`. Do not run DietPi's standard hotspot installer: its documented configuration repurposes Wi-Fi as an AP with Ethernet upstream.

3. **Give the laptop a stable local endpoint.** Proposed SSID: `TurboExo`; proposed subnet: `192.168.50.0/24`, after checking route conflicts; Pi address: `192.168.50.1`. Use a new strong WPA2-AES passphrase. The Mac's existing Dash Echo client uses the hotspot address with the same port, **21848**. TSDash web remains on **16680**. No Internet sharing is required; initially omit NAT and DHCP default-router advertisement.

4. **Keep both roles on the same channel.** Start with channel 40, matching the current home connection, and a compatible channel width. Confirm the home router's channel policy before relying on a fixed channel; do not change router settings silently. Use the actual regulatory permissions when starting the AP.

5. **Make the hotspot independent of home availability.** Create/start the AP from radio-device availability, without waiting for home association, ifupdown's DHCP attempt, or `networking.service` completion. The hotspot must boot when the car is away from home.

6. **Prioritize the hotspot during tuning.** Keep its channel/address stable when home Wi-Fi disappears. Test client retry/scanning behavior; suspend retries if they disrupt the AP. The implemented client retries automatically on 5200 MHz; it does not change the hotspot channel to follow a different home-router channel. Home Wi-Fi therefore needs to remain on channel 40 for simultaneous operation.

7. **Persist the configuration after the temporary trial works.** Use dedicated service units/drop-ins with explicit interface creation, ordering and cleanup. Preserve the existing TSDash connection and launch configuration.

## Tests specific to this change

- Home present: the Pi stays connected to home Wi-Fi while the Mac connects to its hotspot and uses the existing Dash Echo service.
- Home disappears/returns: laptop telemetry remains usable, and the hotspot does not enter a restart loop. Record any dropout and whether the proposed retry policy prevents it.
- Boot away from home: hotspot is available without waiting on the missing home network; reconnect by fixed IP.
- Mac reconnect/sleep: rejoining the hotspot restores the tuning connection without restarting TSDash or the Pi.
- Sustained session: run at least 30 minutes and inspect for `brcmfmac` resets, lost AP interfaces, and new ECU-communication/logging interruptions attributable to the network change.

Test parked first, then verify the home-to-away transition with a passenger operating the laptop. No tune edits are necessary to test connectivity. Existing subsystems need regression observation during these tests, not separate requalification projects.

## Decision after the trial

Keep one radio if these tests pass. If shared-channel or firmware behavior prevents a stable hotspot, use a second AP-capable USB Wi-Fi adapter: built-in Wi-Fi remains the home client, and the second radio hosts the laptop independently. No purchase or OS migration is part of this plan.

## Evidence

- Existing Dash Echo: chat “Find Dash Echo client port”, user confirmation after enablement; `projectCfg/project.properties`; `/Users/adamgross/TunerStudioProjects/TunerStudioAppDebug.txt`, October 10, 11:11:14.
- Current radio/network facts: read-only SSH inspection on October 10 (`iw dev`, `iw list`, package/service state, routes).
- [Linux interface-combination documentation](https://www.kernel.org/doc/html/latest/driver-api/80211/cfg80211.html): concurrent channel limit.
- [DietPi hotspot documentation](https://dietpi.com/docs/software/advanced_networking/#wifi-hotspot): standard Ethernet-uplink design.
- [Raspberry Pi issue 7092](https://github.com/raspberrypi/linux/issues/7092): concurrent-mode crashes reported on another kernel/client combination; motivates the targeted trial, not a diagnosis of this Pi.
