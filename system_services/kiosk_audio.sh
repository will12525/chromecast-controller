#!/bin/bash
# Point the kiosk at the HDMI-A-1 stereo sink (vc4hdmi0 / hdmi0) once PipeWire is up.

for _ in $(seq 1 50); do
    if pactl info >/dev/null 2>&1; then
        break
    fi
    sleep 0.2
done

if ! pactl info >/dev/null 2>&1; then
    echo "kiosk_audio: PipeWire did not become ready" >&2
    exit 0
fi

sink=$(pactl list short sinks | awk 'BEGIN { IGNORECASE = 1 } /vc4hdmi0|hdmi0/ { print $2; exit }')
if [[ -z "${sink}" ]]; then
    echo "kiosk_audio: no HDMI-A-1 sink found" >&2
    exit 0
fi

pactl set-default-sink "${sink}"
pactl set-sink-mute "${sink}" 0
volume=$(pactl get-sink-volume "${sink}" | sed -n 's/.* \([0-9][0-9]*\)%.*/\1/p' | head -n 1)
if [[ "${volume:-0}" -eq 0 ]]; then
    pactl set-sink-volume "${sink}" 70%
fi
