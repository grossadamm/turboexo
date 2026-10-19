#!/usr/bin/env python3
"""Run as root on the Pi from a staged copy. Stage only; do not activate networking."""
from datetime import datetime, timezone
from pathlib import Path
import os
import re
import secrets
import shutil
import subprocess


def main():
    if os.geteuid() != 0:
        raise SystemExit("Run as root on the Pi")
    source = Path(__file__).resolve().parent
    config = Path('/etc/turboexo/wifi')
    units = ['turboexo-ap0.service', 'turboexo-hostapd.service', 'turboexo-dhcp.service']
    targets = [config / 'hostapd.conf', config / 'dnsmasq.conf',
               Path('/usr/local/libexec/turboexo-ap0')]
    targets += [Path('/etc/systemd/system') / unit for unit in units]
    if any(path.exists() for path in targets):
        raise SystemExit('Existing hotspot installation found; inspect before replacing it')
    wpa_path = Path('/etc/wpa_supplicant/wpa_supplicant.conf')
    original = wpa_path.read_text()
    blocks = list(re.finditer(r'(?ms)^network=\{\s*\n.*?^\}', original))
    if len(blocks) != 1 or 'ssid="exterminate"' not in blocks[0].group():
        raise SystemExit('Unexpected station configuration; inspect before editing')
    for key in ('freq_list', 'scan_freq', 'autoscan', 'sched_scan_plans'):
        if re.search(rf'(?m)^\s*{key}\s*=', original):
            raise SystemExit(f'Existing {key} needs reconciliation')
    status = subprocess.check_output(['/usr/sbin/wpa_cli', '-i', 'wlan0', 'status'], text=True)
    if 'freq=5200\n' not in status or 'wpa_state=COMPLETED\n' not in status:
        raise SystemExit('Expected current home association on 5200 MHz')

    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = Path('/var/backups/turboexo-wifi') / stamp
    backup.mkdir(parents=True, mode=0o700)
    os.chmod(backup, 0o700)
    shutil.copy2(wpa_path, backup / 'wpa_supplicant.conf')
    os.chmod(backup / 'wpa_supplicant.conf', 0o600)
    shutil.copy2(source / 'rollback.sh', backup / 'rollback.sh')
    os.chmod(backup / 'rollback.sh', 0o700)

    # Stage the station file separately; activation owns the guarded replacement.
    match = blocks[0]
    block = match.group()[:-1] + '    scan_freq=5200\n    freq_list=5200\n}'
    staged = original[:match.start()] + block + original[match.end():]
    staged = 'freq_list=5200\nautoscan=periodic:30\n' + staged
    (backup / 'wpa_supplicant.staged.conf').write_text(staged)
    os.chmod(backup / 'wpa_supplicant.staged.conf', 0o600)

    config.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(config, 0o700)
    password = secrets.token_urlsafe(18)
    text = (source / 'hostapd.conf.template').read_text()
    text = text.replace('@COUNTRY_CODE@', 'US').replace('@WPA_PASSPHRASE@', password)
    # Keep generated credentials out of terminal output and source control.
    (config / 'hostapd.conf').write_text(text)
    os.chmod(config / 'hostapd.conf', 0o600)
    shutil.copy2(source / 'dnsmasq.conf', config / 'dnsmasq.conf')
    os.chmod(config / 'dnsmasq.conf', 0o600)
    for unit in units:
        shutil.copy2(source / unit, Path('/etc/systemd/system') / unit)
        os.chmod(Path('/etc/systemd/system') / unit, 0o644)
    Path('/usr/local/libexec').mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / 'turboexo-ap0', '/usr/local/libexec/turboexo-ap0')
    os.chmod('/usr/local/libexec/turboexo-ap0', 0o755)
    subprocess.run(['systemctl', 'daemon-reload'], check=True)
    subprocess.run(['systemd-analyze', 'verify', *[f'/etc/systemd/system/{u}' for u in units]], check=True)
    subprocess.run(['/usr/sbin/dnsmasq', '--test', f'--conf-file={config}/dnsmasq.conf'], check=True)
    print(f'BACKUP={backup}')
    print('Staged and validated; services not enabled or started; station configuration unchanged.')


if __name__ == '__main__':
    main()
