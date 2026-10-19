# TurboExo Pi Wi-Fi hotspot

Deployed 2026-10-10. Three dedicated services are active and enabled:
`turboexo-ap0`, `turboexo-hostapd`, and `turboexo-dhcp`.

- SSID: `TurboExo`; Pi: `192.168.50.1`; Dash Echo: TCP `21848`; web: TCP `16680`.
- Mac joins the Pi SSID for tuning. Home access stays at `192.168.1.134`.
- WPA2 credential: `/etc/turboexo/wifi/hostapd.conf` on the Pi, mode 0600. Do not commit it.
- No hotspot default gateway/DNS advertisement or NAT. Local tuning works without Internet.
- Both radio roles share channel 40. The station configuration restricts scans and association to 5200 MHz and retries automatically every 30 seconds.

## Files and deployment

`turboexo-ap0` creates only the virtual AP and assigns its address. Its unit waits for the wlan0 device, not home association or networking.service completion. hostapd and DHCP depend on that virtual interface. Source templates contain no credentials.

`deploy.py` runs as root from a staged copy on the Pi. It refuses to overwrite an existing installation, backs up the station configuration, generates a new hotspot passphrase, and stages configuration without starting services or altering the active station. The caller must arm a rollback before applying the staged station file/runtime settings and starting the services. The deployed station file is the generated `wpa_supplicant.staged.conf`, copied from the protected backup directory to `/etc/wpa_supplicant/wpa_supplicant.conf` after the guard is armed.

Installed paths:

- `/usr/local/libexec/turboexo-ap0`
- `/etc/systemd/system/turboexo-{ap0,hostapd,dhcp}.service`
- `/etc/turboexo/wifi/{hostapd,dnsmasq}.conf`

`hostapd` 2:2.10-24, `dnsmasq-base`, and its `libnftables1` dependency were installed. The existing wpa_supplicant package was retained. The generic package hostapd service remains masked; only the dedicated instance runs.

## Validation and recovery

See `validation-2026-10-10.json` and `docs/PI_WIFI_HOTSPOT_PLAN.md`. The corrected unavailable-home test passed, as did a fresh AP service start with home unavailable. A physical cold boot away from home and a sustained road session have not been tested.

`test-handoff.py` is a disruptive, parked/engine-off diagnostic, not a production service. It temporarily excludes the home BSSID, then restores the exact original restriction (`any` when unset) and measures passive automatic recovery. Run it only with a local rollback armed and the user aware of connectivity interruption. `--restart-ap` also tests a fresh AP service start without home association. Do not use an all-zero MAC with SET_NETWORK to clear a BSSID restriction.

Rollback on the Pi:

```sh
sudo /var/backups/turboexo-wifi/20261010T190927Z/rollback.sh
```

Rollback stops/removes only the hotspot units and configuration, restores the previous station file, and reconfigures/reconnects wpa_supplicant. It retains packages and protected backups. TSDash startup, logging, shutdown and ECU settings are not modified.


### Restart verification, 2026-10-10 13:58

Two controlled Pi restarts confirmed AP/DHCP startup; the user saw TurboExo in
Wi-Fi discovery. The first exposed a missing RFCOMM module load, now fixed in
`../turboexo-bluetooth-serial.service`. The second restored Bluetooth telemetry
automatically. An intentional Bluetooth disconnect also recovered without manual
intervention. Mac TunerStudio subsequently logged StackOverflowError; restart it
and verify live gauges before AutoTune. A full power-off boot away from home and
sustained driving remain untested. Home Wi-Fi preserves Internet during remote
agent work; use 192.168.1.134:21848 there and 192.168.50.1:21848 on TurboExo.
