"""Pick a Pi kiosk HDMI mode and the matching stereo profile.

The mode list comes from `kmsprint -m`. Negative sync is rejected: a panel can
stay linked and show no picture on those timings. Nothing above 1920x1080 or
60 Hz is used.
"""

import json
import re
import sys

CONNECTOR_RE = re.compile(r"^Connector\s+\d+\s+\(\d+\)\s+(\S+)\s+\((\w+)\)")
MODE_RE = re.compile(
    r"(\d+)x(\d+)(i)?@([0-9.]+)\s+[0-9.]+\s+"
    r"\d+/\d+/\d+/\d+/([+-])\s+\d+/\d+/\d+/\d+/([+-])"
)
PORT_NEEDLES = {
    "HDMI-A-1": ("vc4-hdmi-0", "fef00700"),
    "HDMI-A-2": ("vc4-hdmi-1", "fef05700"),
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
        current["modes"].append(
            {
                "width": int(match.group(1)),
                "height": int(match.group(2)),
                "interlaced": match.group(3) == "i",
                "refresh": float(match.group(4)),
                "positive": match.group(5) == "+" and match.group(6) == "+",
            }
        )
    return connectors


def _target_connector(connectors):
    names = [item["name"] for item in connectors]
    if "HDMI-A-1" in names:
        return "HDMI-A-1"
    if "HDMI-A-2" in names:
        return "HDMI-A-2"
    return None


def _within_cap(mode):
    return (
        not mode["interlaced"]
        and mode["width"] <= 1920
        and mode["height"] <= 1080
        and mode["refresh"] <= 60.0
    )


def _has_negative_twin(mode, modes):
    """Sway selects by size and refresh only, so a negative mode at the same
    refresh can be the one that gets programmed."""
    return any(
        not other["positive"]
        and other["width"] == mode["width"]
        and other["height"] == mode["height"]
        and abs(other["refresh"] - mode["refresh"]) < 0.02
        for other in modes
    )


def mode_candidates(text):
    """Ordered modes to try. Empty when the port should be left alone."""
    connectors = parse_kmsprint(text)
    name = _target_connector(connectors)
    if name is None:
        return []
    modes = next(item["modes"] for item in connectors if item["name"] == name)
    usable = [
        mode
        for mode in modes
        if mode["positive"] and _within_cap(mode) and not _has_negative_twin(mode, modes)
    ]
    usable.sort(key=lambda mode: (-(mode["width"] * mode["height"]), abs(mode["refresh"] - 60.0)))
    return [
        {
            "connector": name,
            "width": mode["width"],
            "height": mode["height"],
            "refresh": mode["refresh"],
        }
        for mode in usable
    ]


def format_mode(candidate):
    refresh = f"{candidate['refresh']:.2f}".rstrip("0").rstrip(".")
    return f"{candidate['width']}x{candidate['height']}@{refresh}Hz"


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
    profiles = []
    for item in _walk(obj):
        name = item.get("name")
        if not isinstance(name, str):
            continue
        lowered = name.lower()
        if "hdmi" in lowered and "stereo" in lowered and _available(item):
            profiles.append(name)
    profiles.sort(key=lambda name: (name != "hdmi-stereo", name != "output:hdmi-stereo", name))
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
    """Return (device_id, profile_name) for a usable HDMI stereo profile."""
    for obj in _matching_devices(dump, connector):
        profiles = _stereo_profiles(obj)
        if profiles:
            return obj.get("id"), profiles[0]
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
            print(f"{candidate['connector']} {format_mode(candidate)}")
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
