#!/bin/bash
# Openbox calls this only after it is ready to manage windows. MPV owns the
# startup overlay while TSDash loads underneath it.

OVERLAY_PLAYER="/usr/bin/mpv"
OVERLAY_VIDEO="/home/dietpi/TSDash/boot/exocet-boot-loop-final-pi.mp4"
BOOT_READY_FILE="/tmp/turboexo-dash-ready"
BOOT_VISIBLE_FILE="/tmp/turboexo-overlay-visible"
BOOT_REVEALED_FILE="/tmp/turboexo-overlay-revealed"
OVERLAY_LOG="/tmp/turboexo-overlay.log"
DASH_PAINTED_FILE="/tmp/turboexo-dash-painted"
MIN_OVERLAY_MS=8000
VISUAL_STABLE_MS=1000
HTTP_FALLBACK_MS=15000
MAX_OVERLAY_MS=60000

unlink "$BOOT_READY_FILE" 2>/dev/null || true
unlink "$BOOT_VISIBLE_FILE" 2>/dev/null || true
unlink "$BOOT_REVEALED_FILE" 2>/dev/null || true
unlink "$DASH_PAINTED_FILE" 2>/dev/null || true
: > "$OVERLAY_LOG"

overlay_pid=""
overlay_window=""
if [ -x "$OVERLAY_PLAYER" ] && [ -r "$OVERLAY_VIDEO" ]; then
    nice -n 10 "$OVERLAY_PLAYER" \
        --no-config \
        --fs \
        --ontop \
        --loop-file=inf \
        --x11-bypass-compositor=never \
        --x11-name=TurboExoBoot \
        --no-audio \
        --osc=no \
        --input-default-bindings=no \
        --cursor-autohide=always \
        --title="TurboExo Boot" \
        --really-quiet \
        "$OVERLAY_VIDEO" >>"$OVERLAY_LOG" 2>&1 &
    overlay_pid=$!
    # Do not let TSDash paint until MPV is genuinely mapped. Exit immediately if
    # MPV fails; otherwise cap the mapping wait at two seconds.
    for _ in $(seq 1 40); do
        overlay_window=$(xdotool search --onlyvisible --name '^TurboExo Boot$' 2>/dev/null | tail -1)
        if [ -n "$overlay_window" ]; then
            : > "$BOOT_VISIBLE_FILE"
            overlay_mapped_ms=$(date +%s%3N)
            break
        fi
        kill -0 "$overlay_pid" 2>/dev/null || break
        sleep 0.05
    done
fi

/home/dietpi/TSDash/start-turboexo-dash.sh &
dash_pid=$!

# HTTP readiness is early: the traced startup continued creating top-level
# loading windows (win0..win3) for roughly another 13 seconds. Openbox maps all
# ecuhubdash windows below MPV. Reveal only after the full animation, HTTP
# readiness, and one second with the main TS Dash window as the sole remaining
# ecuhubdash top-level. All deadlines use the monotonic-enough wall clock in
# milliseconds so command latency cannot stretch an 8 s animation into 20+ s.
if [ -n "${overlay_mapped_ms:-}" ] && kill -0 "$dash_pid" 2>/dev/null; then
    saw_aux_window=0
    visually_stable_since_ms=""
    http_ready_since_ms=""
    while kill -0 "$dash_pid" 2>/dev/null; do
        now_ms=$(date +%s%3N)
        overlay_elapsed_ms=$((now_ms - overlay_mapped_ms))

        if [ -e "$BOOT_READY_FILE" ] && [ -z "$http_ready_since_ms" ]; then
            http_ready_since_ms=$now_ms
        fi

        dash_window_count=$(wmctrl -lx 2>/dev/null | awk \
            '$3 ~ /^ecuhubdash-EcuHubDash\./ { count++ } END { print count + 0 }')
        if [ "$dash_window_count" -gt 1 ]; then
            saw_aux_window=1
            visually_stable_since_ms=""
        elif [ "$saw_aux_window" -eq 1 ] && [ "$dash_window_count" -eq 1 ]; then
            if [ -z "$visually_stable_since_ms" ]; then
                visually_stable_since_ms=$now_ms
            fi
        else
            visually_stable_since_ms=""
        fi

        visually_ready=0
        if [ -n "$visually_stable_since_ms" ] \
                && [ $((now_ms - visually_stable_since_ms)) -ge "$VISUAL_STABLE_MS" ]; then
            visually_ready=1
        elif [ "$saw_aux_window" -eq 0 ] \
                && [ -n "$http_ready_since_ms" ] \
                && [ $((now_ms - http_ready_since_ms)) -ge "$HTTP_FALLBACK_MS" ]; then
            # Fail open only if a future TSDash version never creates aux
            # windows. Once any loading window is observed, it must close.
            visually_ready=1
        fi

        if [ "$overlay_elapsed_ms" -ge "$MIN_OVERLAY_MS" ] \
                && [ -n "$http_ready_since_ms" ] \
                && [ "$visually_ready" -eq 1 ]; then
            : > "$DASH_PAINTED_FILE"
            break
        fi
        [ "$overlay_elapsed_ms" -ge "$MAX_OVERLAY_MS" ] && break
        sleep 0.1
    done
fi

# Crossfade only the main dashboard. Auxiliary Java loading windows deliberately
# remain transparent even if a failure cap fires while one still exists.
dash_window=$(wmctrl -lx 2>/dev/null | awk \
    '$3 ~ /^ecuhubdash-EcuHubDash\./ && $0 ~ / TS Dash$/ { print $1; exit }')
if [ -n "$dash_window" ]; then
    full_opacity=4294967295
    fade_steps=10
    for fade_step in $(seq 0 "$fade_steps"); do
        dash_opacity=$((full_opacity * fade_step / fade_steps))
        overlay_opacity=$((full_opacity - dash_opacity))
        xprop -id "$dash_window" \
            -f _NET_WM_WINDOW_OPACITY 32c \
            -set _NET_WM_WINDOW_OPACITY "$dash_opacity" >/dev/null 2>&1 || true
        if [ -n "$overlay_window" ]; then
            xprop -id "$overlay_window" \
                -f _NET_WM_WINDOW_OPACITY 32c \
                -set _NET_WM_WINDOW_OPACITY "$overlay_opacity" >/dev/null 2>&1 || true
        fi
        sleep 0.03
    done
fi

if [ -n "$overlay_pid" ]; then
    : > "$BOOT_REVEALED_FILE"
    kill "$overlay_pid" 2>/dev/null || true
    wait "$overlay_pid" 2>/dev/null || true
fi

if [ -n "$dash_window" ]; then
    wmctrl -i -a "$dash_window" >/dev/null 2>&1 || true
fi

wait "$dash_pid"

# TSDash's staging updater exits Java and relaunches this session wrapper. Give
# that managed replacement time to map before deciding the dashboard actually
# died. If a replacement appears, its own wrapper now owns the eventual cleanup;
# leave Openbox and X running. Genuine exits still recycle tty1 as before.
for _ in $(seq 1 200); do
    if pgrep -f 'java .*TSDash\.jar' >/dev/null 2>&1; then
        exit 0
    fi
    sleep 0.05
done

openbox --exit
