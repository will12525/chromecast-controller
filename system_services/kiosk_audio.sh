#!/bin/bash
# Select the stereo sink for the HDMI port kiosk_output.sh is using.
# pactl is not installed. wpctl is.

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
connector="${1:-}"

LIB_DIR=$(cd "$(dirname "$0")" && pwd)
if [[ -f /usr/local/lib/kiosk_hdmi.py ]]; then
    LIB_DIR=/usr/local/lib
fi

if [[ "${connector}" != "HDMI-A-1" && "${connector}" != "HDMI-A-2" ]]; then
    echo "kiosk_audio: no HDMI port; leaving the headphone sink" >&2
    exit 0
fi

if ! command -v wpctl >/dev/null 2>&1 || ! command -v pw-dump >/dev/null 2>&1; then
    echo "kiosk_audio: wpctl or pw-dump is not installed" >&2
    exit 0
fi

for _ in $(seq 1 50); do
    if wpctl status >/dev/null 2>&1; then
        break
    fi
    sleep 0.2
done

if ! wpctl status >/dev/null 2>&1; then
    echo "kiosk_audio: PipeWire did not become ready" >&2
    exit 0
fi

target=""
for _ in $(seq 1 10); do
    target=$(pw-dump | python3 "${LIB_DIR}/kiosk_hdmi.py" profile "${connector}")
    [[ -n "${target}" ]] && break
    sleep 0.5
done

if [[ -z "${target}" ]]; then
    echo "kiosk_audio: no HDMI stereo profile for ${connector}; leaving the headphone sink" >&2
    pw-dump | python3 "${LIB_DIR}/kiosk_hdmi.py" profiles "${connector}" >&2
    exit 0
fi

read -r device profile_index <<<"${target}"
# wpctl set-profile takes the profile index. The name is not accepted.
if ! wpctl set-profile "${device}" "${profile_index}"; then
    echo "kiosk_audio: set-profile ${device} ${profile_index} failed" >&2
    exit 0
fi

sink=""
for _ in $(seq 1 10); do
    sink=$(pw-dump | python3 "${LIB_DIR}/kiosk_hdmi.py" sink "${connector}")
    [[ -n "${sink}" ]] && break
    sleep 0.3
done

if [[ -z "${sink}" ]]; then
    echo "kiosk_audio: profile ${profile_index} did not create a sink" >&2
    exit 0
fi

wpctl set-default "${sink}"
wpctl set-mute "${sink}" 0
wpctl set-volume "${sink}" 70%
echo "kiosk_audio: ${connector} sink ${sink} profile ${profile_index}"
