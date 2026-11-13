#!/bin/bash
# Choose an HDMI mode for the connected port, point audio at that port, then
# start Chromium. Sway runs this once per kiosk session.

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

LIB_DIR=$(cd "$(dirname "$0")" && pwd)
if [[ -f /usr/local/lib/kiosk_hdmi.py ]]; then
    LIB_DIR=/usr/local/lib
fi

for _ in $(seq 1 50); do
    if swaymsg -t get_outputs >/dev/null 2>&1; then
        break
    fi
    sleep 0.2
done

connector=""
if command -v kmsprint >/dev/null 2>&1; then
    mapfile -t candidates < <(kmsprint -m | python3 "${LIB_DIR}/kiosk_hdmi.py" modes)
    for candidate in "${candidates[@]}"; do
        [[ -n "${candidate}" ]] || continue
        read -r connector mode <<<"${candidate}"
        if swaymsg output "${connector}" mode "${mode}"; then
            echo "kiosk_output: ${connector} ${mode}"
            break
        fi
        echo "kiosk_output: rejected ${connector} ${mode}" >&2
        connector=""
    done
else
    echo "kiosk_output: kmsprint is not installed; leaving the current mode" >&2
fi

if [[ -z "${connector}" ]]; then
    connector=$(swaymsg -t get_outputs | python3 "${LIB_DIR}/kiosk_hdmi.py" connected)
fi

/usr/local/bin/kiosk_audio.sh "${connector}"

exec /usr/bin/chromium --kiosk --ozone-platform=wayland \
    --enable-features=UseOzonePlatform \
    --disable-features=WaylandFractionalScaleV1 \
    --start-maximized --force-device-scale-factor=1 \
    --noerrdialogs --disable-infobars \
    --check-for-update-interval=31536000 \
    --app=http://127.0.0.1:5000
