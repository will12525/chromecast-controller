"""Pick a Pi kiosk HDMI mode and the matching stereo profile.

Modes come from `kmsprint -m` on HDMI-A-1. HDMI-A-2 is ignored. Negative sync
is rejected. A positive mode is kept when a negative mode shares its refresh,
and the Sway modeline carries the positive porches. Nothing above 1920x1080
or 60 Hz is used.
"""

import json
import re
import sys

CONNECTOR_RE = re.compile(r"^Connector\s+\d+\s+\(\d+\)\s+(\S+)\s+\((\w+)\)")
MODE_RE = re.compile(
    r"(\d+)x(\d+)(i)?@([0-9.]+)\s+([0-9.]+)\s+"
    r"(\d+)/(\d+)/(\d+)/(\d+)/([+-])\s+"
    r"(\d+)/(\d+)/(\d+)/(\d+)/([+-])"
)
PORT_NEEDLES = {
    "HDMI-A-1": ("vc4-hdmi-0", "fef00700"),
    "HDMI-A-2": ("vc4-hdmi-1", "fef05700"),
}
WATCHED_OUTPUT = "HDMI-A-1"
DISABLED_OUTPUTS = ("HDMI-A-2",)


def _mode_from_match(match):
    hpol = match.group(10)
    vpol = match.group(15)
    return {
        "width": int(match.group(1)),
        "height": int(match.group(2)),
        "interlaced": match.group(3) == "i",
        "refresh": float(match.group(4)),
        "clock": float(match.group(5)),
        "hdisplay": int(match.group(6)),
        "hfront": int(match.group(7)),
        "hsync": int(match.group(8)),
        "hback": int(match.group(9)),
        "hpol": hpol,
        "vdisplay": int(match.group(11)),
        "vfront": int(match.group(12)),
        "vsync": int(match.group(13)),
        "vback": int(match.group(14)),
        "vpol": vpol,
        "positive": hpol == "+" and vpol == "+",
    }


def parse_kmsprint(text):
    """Return connected connectors in kmsprint order, each with its modes."""
    connectors = []
    current = None
    for line in text.splitlines():
        header = CONNECTOR_RE.match(line.strip())
        if header:
            current = None
            name, status = header.group(1), header.group(2)
            if status == "connected":
                current = {"name": name, "modes": []}
                connectors.append(current)
            continue
        if current is None:
            continue
        match = MODE_RE.search(line)
        if not match:
            continue
        current["modes"].append(_mode_from_match(match))
    return connectors


def active_mode(text, connector):
    """Return the CRTC timing for a connected port, or None."""
    in_connector = False
    for line in text.splitlines():
        stripped = line.strip()
        header = CONNECTOR_RE.match(stripped)
        if header:
            in_connector = header.group(1) == connector and header.group(2) == "connected"
            continue
        if not in_connector or not stripped.startswith("Crtc"):
            continue
        match = MODE_RE.search(stripped)
        if match:
            return _mode_from_match(match)
    return None


def _within_cap(mode):
    return (
        not mode["interlaced"]
        and mode["width"] <= 1920
        and mode["height"] <= 1080
        and mode["refresh"] <= 60.0
    )


def _rank(mode):
    if mode["width"] == 1920 and mode["height"] == 1080:
        tier = 0
    elif mode["width"] == 1280 and mode["height"] == 720:
        tier = 1
    else:
        tier = 2
    return (tier, abs(mode["refresh"] - 60.0), -(mode["width"] * mode["height"]))


def mode_candidates(text):
    """Ordered HDMI-A-1 modes to try. Empty when that port should be left alone."""
    connectors = parse_kmsprint(text)
    modes = next((item["modes"] for item in connectors if item["name"] == WATCHED_OUTPUT), None)
    if not modes:
        return []
    usable = [mode for mode in modes if mode["positive"] and _within_cap(mode)]
    usable.sort(key=_rank)
    return [{**mode, "connector": WATCHED_OUTPUT} for mode in usable]


def modeline_parts(mode):
    """Sway modeline fields for this EDID timing."""
    hdisplay = mode["hdisplay"]
    hsync_start = hdisplay + mode["hfront"]
    hsync_end = hsync_start + mode["hsync"]
    htotal = hsync_end + mode["hback"]
    vdisplay = mode["vdisplay"]
    vsync_start = vdisplay + mode["vfront"]
    vsync_end = vsync_start + mode["vsync"]
    vtotal = vsync_end + mode["vback"]
    return [
        f"{mode['clock']:.3f}",
        str(hdisplay),
        str(hsync_start),
        str(hsync_end),
        str(htotal),
        str(vdisplay),
        str(vsync_start),
        str(vsync_end),
        str(vtotal),
        "+hsync" if mode["hpol"] == "+" else "-hsync",
        "+vsync" if mode["vpol"] == "+" else "-vsync",
    ]


def format_candidate(candidate):
    return " ".join([candidate["connector"], *modeline_parts(candidate)])


def format_mode(candidate):
    refresh = f"{candidate['refresh']:.2f}".rstrip("0").rstrip(".")
    return f"{candidate['width']}x{candidate['height']}@{refresh}Hz"


def _timing(mode):
    parts = modeline_parts(mode)
    return (round(float(parts[0]), 3),) + tuple(int(part) for part in parts[1:9]) + tuple(parts[9:])


def _timing_from_fields(fields):
    return (round(float(fields[0]), 3),) + tuple(int(part) for part in fields[1:9]) + tuple(fields[9:])


def crtc_matches(text, connector, fields):
    """True when the connector's CRTC is the requested positive timing."""
    active = active_mode(text, connector)
    if active is None or len(fields) != 11:
        return False
    return _timing(active) == _timing_from_fields(fields)


def disabled_outputs():
    return list(DISABLED_OUTPUTS)


def watched_output(payload):
    """HDMI-A-1 when an output event names it, otherwise empty."""
    output = payload.get("output") if isinstance(payload, dict) else None
    name = output.get("name") if isinstance(output, dict) else ""
    if name == WATCHED_OUTPUT:
        return name
    return ""


def connected_output(outputs):
    """HDMI port Sway reports as active. HDMI-A-1 wins when both are active."""
    names = []
    for item in outputs:
        name = item.get("name")
        if name not in ("HDMI-A-1", "HDMI-A-2"):
            continue
        if item.get("active") or item.get("current_mode"):
            names.append(name)
    if "HDMI-A-1" in names:
        return "HDMI-A-1"
    if "HDMI-A-2" in names:
        return "HDMI-A-2"
    return ""


def _walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _blob(props):
    return " ".join(str(value) for value in props.values())


def _device_matches(obj, needles):
    props = (obj.get("info") or {}).get("props") or obj.get("props") or {}
    blob = _blob(props)
    return any(needle in blob for needle in needles)


def _available(profile):
    value = profile.get("available", "unknown")
    return value not in ("no", 0, "0", False)


def _stereo_profiles(obj):
    """Available HDMI stereo card profiles as (name, index).

    wpctl set-profile takes the integer index. A profile name is ignored and
    leaves the card off, so entries without an index are not usable.
    """
    profiles = []
    for item in _walk(obj):
        name = item.get("name")
        index = item.get("index")
        if not isinstance(name, str) or not isinstance(index, int):
            continue
        lowered = name.lower()
        if "hdmi" in lowered and "stereo" in lowered and _available(item):
            profiles.append((name, index))
    profiles.sort(key=lambda item: (item[0] != "hdmi-stereo", item[0] != "output:hdmi-stereo", item[0]))
    return profiles


def _matching_devices(dump, connector):
    needles = PORT_NEEDLES.get(connector)
    if not needles or not isinstance(dump, list):
        return
    for obj in dump:
        if obj.get("type") != "PipeWire:Interface:Device":
            continue
        if _device_matches(obj, needles):
            yield obj


def audio_target(dump, connector):
    """Return (device_id, profile_index) for a usable HDMI stereo profile."""
    for obj in _matching_devices(dump, connector):
        profiles = _stereo_profiles(obj)
        if profiles:
            return obj.get("id"), profiles[0][1]
    return None


def profile_report(dump, connector):
    """Text list of HDMI profiles for the log when none can be selected."""
    lines = []
    for obj in _matching_devices(dump, connector):
        lines.append(f"device {obj.get('id')}")
        for item in _walk(obj):
            name = item.get("name")
            if not isinstance(name, str):
                continue
            lowered = name.lower()
            if "hdmi" in lowered or name == "off":
                lines.append(f"  {name} available={item.get('available', 'unknown')}")
    return "\n".join(lines)


def sink_id(dump, connector):
    """Return the PipeWire sink id for the connector, if one exists."""
    needles = PORT_NEEDLES.get(connector)
    if not needles or not isinstance(dump, list):
        return None
    for obj in dump:
        props = (obj.get("info") or {}).get("props") or obj.get("props") or {}
        if props.get("media.class") != "Audio/Sink":
            continue
        if _device_matches(obj, needles):
            return obj.get("id")
    return None


def main(argv):
    command = argv[1] if len(argv) > 1 else ""
    if command == "modes":
        for candidate in mode_candidates(sys.stdin.read()):
            print(format_candidate(candidate))
        return 0
    if command == "disabled":
        for name in disabled_outputs():
            print(name)
        return 0
    if command == "matches":
        connector = argv[2] if len(argv) > 2 else ""
        fields = argv[3:]
        if len(fields) != 11:
            print("kiosk_hdmi: matches needs a connector and 11 modeline fields", file=sys.stderr)
            return 1
        return 0 if crtc_matches(sys.stdin.read(), connector, fields) else 1
    if command == "event":
        try:
            payload = json.load(sys.stdin)
        except json.JSONDecodeError:
            return 0
        name = watched_output(payload)
        if name:
            print(name)
        return 0
    if command == "connected":
        print(connected_output(json.load(sys.stdin)))
        return 0
    payload = json.load(sys.stdin)
    connector = argv[2] if len(argv) > 2 else ""
    if command == "profile":
        found = audio_target(payload, connector)
        if found:
            print(f"{found[0]} {found[1]}")
        return 0
    if command == "sink":
        found = sink_id(payload, connector)
        if found is not None:
            print(found)
        return 0
    if command == "profiles":
        print(profile_report(payload, connector))
        return 0
    print(f"kiosk_hdmi: unknown command {command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
