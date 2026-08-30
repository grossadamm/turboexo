#!/bin/bash
# Launch TSDash on the DietPi Pi 5 with the TurboExo project already loaded.
#
# Why this exists: TSDash only reopens a project if `lastProjectPath` survives in
# ~/.efiAnalytics/tsdUser.properties. An unclean power-down (i.e. every time the
# car's key goes off) can drop that key, and TSDash then boots to the splash with
# no project — no gauges, no logging, no ECU connection.
#
# This wrapper pins the project and re-asserts the Pi-correct paths inside the
# project before every launch, so a project archive uploaded from the Mac (which
# always re-introduces the macOS com port and log dir) self-heals on next boot.
#
# Installed at /home/dietpi/TSDash/start-turboexo-dash.sh, invoked from ~/.xinitrc.

PROJECT="/home/dietpi/TSDashProjects/TurboExo_2026-06-01_21.16.20"
USER_PROPS="/home/dietpi/.efiAnalytics/tsdUser.properties"
TSDASH_SH="/home/dietpi/TSDash/TSDash.sh"

python3 - "$PROJECT" "$USER_PROPS" <<'PY'
import os, sys

project, user_props = sys.argv[1], sys.argv[2]
projects_dir = os.path.dirname(project)

if not os.path.isdir(project):
    sys.stderr.write("start-turboexo-dash: project missing: %s\n" % project)
    sys.exit(0)  # never block the dash from starting

# --- pin the project TSDash reopens on launch ---
lines, seen = [], set()
if os.path.exists(user_props):
    with open(user_props) as fh:
        lines = fh.read().splitlines()

wanted = {
    "lastProjectPath": project,
    "projectsDir": projects_dir,
    "recentlyOpenedProject_0": project,
}
out = []
for line in lines:
    key = line.split("=", 1)[0] if "=" in line and not line.startswith("#") else None
    if key in wanted:
        out.append("%s=%s" % (key, wanted[key]))
        seen.add(key)
    else:
        out.append(line)
for key, val in wanted.items():
    if key not in seen:
        out.append("%s=%s" % (key, val))

with open(user_props, "w") as fh:
    fh.write("\n".join(out) + "\n")

# --- re-assert Pi-correct paths inside the project ---
# macOS leftovers: /dev/cu.usbmodem* or /dev/tty.usbmodem* (Pi is always ttyACM0),
# and a logFileDir pointing at the Mac's filesystem (logging silently misbehaves).
import re

proj_cfg = os.path.join(project, "projectCfg")
log_dir = os.path.join(project, "DataLogs")
os.makedirs(log_dir, exist_ok=True)

for name in ("project.properties", "project.properties.bkup"):
    path = os.path.join(proj_cfg, name)
    if not os.path.exists(path):
        continue
    with open(path) as fh:
        text = fh.read()
    fixed = re.sub(r"/dev/(?:cu|tty)\.usbmodem[0-9]*", "/dev/ttyACM0", text)
    fixed = re.sub(r"(?m)^logFileDir=.*$", "logFileDir=" + log_dir, fixed)
    if "logFileDir=" not in fixed:
        fixed = fixed.rstrip("\n") + "\nlogFileDir=" + log_dir + "\n"
    if fixed != text:
        with open(path, "w") as fh:
            fh.write(fixed)
        sys.stderr.write("start-turboexo-dash: repaired %s\n" % name)
PY

# --- arm triggered data logging once TSDash is up ---
# TSDash 0.9.09.10 does NOT persist the Data Logging trigger config: every launch
# resets it to the factory default (disabled, tps > 80, log for 600 s). So we
# re-apply it through the same local config server the web UI posts to.
#
# Start when cranking first produces nonzero RPM. Close after RPM has remained at
# zero for 15 seconds, so each attempt becomes a closed file that the USB copier
# can verify and copy. This also avoids opening a log during boot before the Pi's
# clock has synchronized.
(
    for _ in $(seq 1 60); do
        if curl -sf --max-time 3 "http://127.0.0.1:16680/index.html?pageId=DataLogging" \
             | grep -q 'name="loggingEnabled"'; then
            curl -sf --max-time 10 -X POST "http://127.0.0.1:16680/index.html" \
                --data-urlencode "pageId=DataLogging" \
                --data-urlencode "action=save" \
                --data-urlencode "loggingEnabled=loggingEnabled" \
                --data-urlencode "startMode=Expression" \
                --data-urlencode "startExpression=rpm > 0" \
                --data-urlencode "selStartSingleChannel=rpm" \
                --data-urlencode "startCondition=>" \
                --data-urlencode "startSimpleValue=0" \
                --data-urlencode "stopMode=Expression" \
                --data-urlencode "stopExpression=isTrueFor(rpm < 1, 15)" \
                --data-urlencode "stopLogFor=600" \
                -o /dev/null && logger -t turboexo-dash "triggered logging armed"
            exit 0
        fi
        sleep 2
    done
    logger -t turboexo-dash "TSDash config server never came up; logging NOT armed"
) &

exec "$TSDASH_SH"
