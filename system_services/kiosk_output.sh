#!/bin/bash
# Choose an HDMI-A-1 mode from the connected display, point audio at that
# port, then start Chromium. HDMI-A-2 is disabled. A watcher repeats the
# selection when HDMI-A-1 connects or its mode list changes.

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

LIB_DIR=$(cd "$(dirname "$0")" && pwd)
if [[ -f /usr/local/lib/kiosk_hdmi.py ]]; then
    LIB_DIR=/usr/local/lib
fi

wait_for_sway() {
    local _attempt
    for _attempt in $(seq 1 50); do
        if swaymsg -t get_outputs >/dev/null 2>&1; then
            return 0
        fi
        sleep 0.2
    done
    return 1
}

disable_other_ports() {
    local port
    while IFS= read -r port; do
        [[ -n "${port}" ]] || continue
        swaymsg output "${port}" disable >/dev/null 2>&1 || true
    done < <(python3 "${LIB_DIR}/kiosk_hdmi.py" disabled)
}

mode_matches() {
    kmsprint | python3 "${LIB_DIR}/kiosk_hdmi.py" matches "$@"
}

apply_hdmi() {
    local connector clock hdisplay hss hse htot vdisplay vss vse vtot hsync vsync
    local candidate
    if ! command -v kmsprint >/dev/null 2>&1; then
        echo "kiosk_output: kmsprint is not installed; leaving the current mode" >&2
        return 0
    fi
    local candidates=()
    mapfile -t candidates < <(kmsprint -m | python3 "${LIB_DIR}/kiosk_hdmi.py" modes)
    if [[ ${#candidates[@]} -eq 0 ]]; then
        echo "kiosk_output: no usable HDMI-A-1 mode; leaving the current mode" >&2
        return 0
    fi
    read -r connector clock hdisplay hss hse htot vdisplay vss vse vtot hsync vsync <<<"${candidates[0]}"
    if mode_matches "${connector}" "${clock}" "${hdisplay}" "${hss}" "${hse}" "${htot}" \
        "${vdisplay}" "${vss}" "${vse}" "${vtot}" "${hsync}" "${vsync}"; then
        return 0
    fi
    for candidate in "${candidates[@]}"; do
        [[ -n "${candidate}" ]] || continue
        read -r connector clock hdisplay hss hse htot vdisplay vss vse vtot hsync vsync <<<"${candidate}"
        if ! swaymsg output "${connector}" modeline \
            "${clock}" "${hdisplay}" "${hss}" "${hse}" "${htot}" \
            "${vdisplay}" "${vss}" "${vse}" "${vtot}" \
            "${hsync}" "${vsync}"; then
            echo "kiosk_output: rejected ${candidate}" >&2
            continue
        fi
        sleep 0.4
        if mode_matches "${connector}" "${clock}" "${hdisplay}" "${hss}" "${hse}" "${htot}" \
            "${vdisplay}" "${vss}" "${vse}" "${vtot}" "${hsync}" "${vsync}"; then
            echo "kiosk_output: ${candidate}"
            /usr/local/bin/kiosk_audio.sh "${connector}"
            return 0
        fi
        echo "kiosk_output: readback rejected ${candidate}" >&2
    done
    echo "kiosk_output: no HDMI-A-1 mode stuck; leaving the current mode" >&2
    return 0
}

watch_hdmi() {
    local line name
    swaymsg -t subscribe -m '["output"]' | while IFS= read -r line; do
        name=$(printf '%s\n' "${line}" | python3 "${LIB_DIR}/kiosk_hdmi.py" event)
        [[ "${name}" == "HDMI-A-1" ]] || continue
        apply_hdmi
    done
}

wait_for_sway

if [[ "${1:-}" == "watch" ]]; then
    watch_hdmi
    exit 0
fi

disable_other_ports
apply_hdmi
nohup "$0" watch >/dev/null 2>&1 &
disown
exec /usr/bin/chromium --kiosk --ozone-platform=wayland \
    --enable-features=UseOzonePlatform \
    --disable-features=WaylandFractionalScaleV1 \
    --start-maximized --force-device-scale-factor=1 \
    --noerrdialogs --disable-infobars \
    --check-for-update-interval=31536000 \
    --app=http://127.0.0.1:5000
