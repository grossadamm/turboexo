#!/usr/bin/env python3
"""Controlled station-unavailable trial; run under systemd-run, with rollback armed."""
import argparse
import json
from pathlib import Path
import signal
import subprocess
import time


def cli(*args):
    return subprocess.check_output(['/usr/sbin/wpa_cli', '-i', 'wlan0', *args], text=True, timeout=5).strip()


def state():
    values = dict(line.split('=', 1) for line in cli('status').splitlines() if '=' in line)
    return {k: values.get(k) for k in ('wpa_state', 'freq', 'ssid', 'ip_address')}


def stop(signum, frame):
    raise SystemExit(f'Interrupted by signal {signum}')


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
parser = argparse.ArgumentParser()
parser.add_argument('--restart-ap', action='store_true', help='Also test a fresh AP start while home is unavailable')
args = parser.parse_args()
original_bssid = cli('get_network', '0', 'bssid')
# SET_NETWORK zero-MAC pins the station to that address. Only 'any' clears
# an unset restriction. (The separate BSSID control command differs.)
restore_bssid = 'any' if original_bssid == 'FAIL' else original_bssid
if cli('get_network', '0', 'ssid') != '"exterminate"':
    raise SystemExit('Unexpected network id; no change made')
result = {'before': state(), 'unavailable': [], 'recovery': []}
try:
    # A deliberately nonexistent BSSID makes the saved home network unavailable
    # without changing the router or disabling automatic station scanning.
    assert cli('set_network', '0', 'bssid', '02:00:00:00:00:01') == 'OK'
    assert cli('disconnect') == 'OK'
    time.sleep(1)
    result['after_disconnect'] = state()
    if args.restart_ap:
        subprocess.run(['systemctl', 'stop', 'turboexo-ap0.service'], check=True, timeout=20)
    assert cli('reconnect') == 'OK'
    if args.restart_ap:
        subprocess.run(['systemctl', 'start', 'turboexo-hostapd.service', 'turboexo-dhcp.service'], check=True, timeout=20)
        result['fresh_ap_start_station_state'] = state()
        result['fresh_ap_info'] = subprocess.check_output(['/usr/sbin/iw', 'dev', 'ap0', 'info'], text=True, timeout=5)
    for _ in range(35):
        time.sleep(1)
        result['unavailable'].append(state())
finally:
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    result['restore_bssid'] = cli('set_network', '0', 'bssid', restore_bssid)
    result['restored_bssid_readback'] = cli('get_network', '0', 'bssid')
    if result['restore_bssid'] != 'OK' or result['restored_bssid_readback'] != original_bssid:
        cli('reconfigure')
        Path('/run/turboexo-wifi-handoff.json').write_text(json.dumps(result, indent=2) + '\n')
        raise SystemExit('BSSID restore verification failed; reloaded the saved configuration')
    # Let the configured automatic retry discover home again. Do not force a
    # reconnect here: the result must distinguish automatic recovery.
    recovery_started = time.monotonic()
    for _ in range(40):
        time.sleep(1)
        current = state()
        result['recovery'].append(current)
        if current.get('wpa_state') == 'COMPLETED':
            break
    result['recovery_elapsed_s'] = round(time.monotonic() - recovery_started, 2)
    Path('/run/turboexo-wifi-handoff.json').write_text(json.dumps(result, indent=2) + '\n')
    result['automatic_recovery'] = bool(result['recovery'] and result['recovery'][-1].get('wpa_state') == 'COMPLETED')
    if not result['automatic_recovery']:
        # Cleanup is separate from the automatic-recovery result. Never leave a
        # failed trial waiting indefinitely for the full rollback timer.
        result['cleanup_reconfigure'] = cli('reconfigure')
        result['cleanup_reconnect'] = cli('reconnect')
    Path('/run/turboexo-wifi-handoff.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'before': result['before'],
                      'unavailable_states': sorted({r['wpa_state'] for r in result['unavailable']}),
                      'restore': result['restore_bssid'],
                      'restore_readback': result['restored_bssid_readback'],
                      'automatic_recovery': result['automatic_recovery'],
                      'after': result['recovery'][-1] if result['recovery'] else None,
                      'recovery_seconds': len(result['recovery'])}), flush=True)
