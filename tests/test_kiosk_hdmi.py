import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "system_services" / "kiosk_hdmi.py"
SPEC = importlib.util.spec_from_file_location("kiosk_hdmi", MODULE_PATH)
kiosk_hdmi = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kiosk_hdmi)


THIS_TV = """
Connector 0 (35) HDMI-A-1 (connected)
  Encoder 0 (34) TMDS
    Crtc 3 (102) 720x480@59.94 27.000 720/16/62/60/- 480/9/6/30/- 60 (59.94) P|D
  1920x1080@60.00 148.500 1920/88/44/148/- 1080/4/5/36/- 60 (60.00) D
  1920x1080@59.94 148.352 1920/88/44/148/+ 1080/4/5/36/+ 60 (59.94) D 16:9
  1920x1080@120.00 297.000 1920/88/44/148/+ 1080/4/5/36/+ 120 (120.00) D 16:9
  1280x720@60.00 74.250 1280/110/40/220/+ 720/5/5/20/+ 60 (60.00) D
  3840x2160@30.00 297.000 3840/176/88/296/+ 2160/8/10/72/+ 30 (30.00) D
  1920x1080i@60.00 74.250 1920/88/44/148/+ 1080/2/5/15/+ 60 (60.00) D
Connector 1 (44) HDMI-A-2 (disconnected)
  Encoder 1 (43) TMDS
"""


def test_this_tv_uses_positive_1080p59():
    modes = kiosk_hdmi.mode_candidates(THIS_TV)
    assert modes[0]["connector"] == "HDMI-A-1"
    assert (modes[0]["width"], modes[0]["height"], modes[0]["refresh"]) == (1920, 1080, 59.94)
    assert kiosk_hdmi.format_mode(modes[0]) == "1920x1080@59.94Hz"
    assert all(mode["width"] <= 1920 and mode["height"] <= 1080 for mode in modes)
    assert all(mode["refresh"] <= 60 for mode in modes)
    assert (1920, 1080, 60.0) not in [(mode["width"], mode["height"], mode["refresh"]) for mode in modes]
    assert (1280, 720, 60.0) in [(mode["width"], mode["height"], mode["refresh"]) for mode in modes]


def test_positive_60_is_kept_when_a_negative_twin_exists():
    text = """
Connector 0 (35) HDMI-A-1 (connected)
  1920x1080@60.00 148.500 1920/88/44/148/- 1080/4/5/36/- 60 (60.00) D
  1920x1080@60.00 148.500 1920/88/44/148/+ 1080/4/5/36/+ 60 (60.00) D
  1920x1080@59.94 148.352 1920/88/44/148/+ 1080/4/5/36/+ 60 (59.94) D 16:9
"""
    modes = kiosk_hdmi.mode_candidates(text)
    assert modes[0]["refresh"] == 60.0
    assert modes[0]["positive"] is True
    assert kiosk_hdmi.format_candidate(modes[0]) == (
        "HDMI-A-1 148.500 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync"
    )


def test_positive_60_beats_59_when_both_are_safe():
    text = """
Connector 0 (35) HDMI-A-1 (connected)
  1920x1080@59.94 148.352 1920/88/44/148/+ 1080/4/5/36/+ 60 (59.94) D
  1920x1080@60.00 148.500 1920/88/44/148/+ 1080/4/5/36/+ 60 (60.00) D
"""
    modes = kiosk_hdmi.mode_candidates(text)
    assert modes[0]["refresh"] == 60.0
    assert kiosk_hdmi.format_mode(modes[0]) == "1920x1080@60Hz"


def test_no_positive_mode_leaves_the_port_alone():
    text = """
Connector 0 (35) HDMI-A-1 (connected)
  1920x1080@60.00 148.500 1920/88/44/148/- 1080/4/5/36/- 60 (60.00) D
"""
    assert kiosk_hdmi.mode_candidates(text) == []


def test_1080p_is_tried_before_720p_even_when_720p_is_closer_to_60():
    text = """
Connector 0 (35) HDMI-A-1 (connected)
  1280x720@60.00 74.250 1280/110/40/220/+ 720/5/5/20/+ 60 (60.00) D
  1920x1080@24.00 74.250 1920/88/44/148/+ 1080/4/5/36/+ 24 (24.00) D
"""
    modes = kiosk_hdmi.mode_candidates(text)
    assert (modes[0]["width"], modes[0]["height"], modes[0]["refresh"]) == (1920, 1080, 24.0)
    assert (modes[1]["width"], modes[1]["height"], modes[1]["refresh"]) == (1280, 720, 60.0)


def test_hdmi_a1_wins_when_both_ports_are_connected():
    text = """
Connector 0 (35) HDMI-A-1 (connected)
  1920x1080@60.00 148.500 1920/88/44/148/+ 1080/4/5/36/+ 60 (60.00) D
Connector 1 (44) HDMI-A-2 (connected)
  1280x720@60.00 74.250 1280/110/40/220/+ 720/5/5/20/+ 60 (60.00) D
"""
    modes = kiosk_hdmi.mode_candidates(text)
    assert {mode["connector"] for mode in modes} == {"HDMI-A-1"}


def test_hdmi_a2_alone_is_ignored():
    text = """
Connector 0 (35) HDMI-A-1 (disconnected)
Connector 1 (44) HDMI-A-2 (connected)
  1280x720@50.00 74.250 1280/110/40/220/+ 720/5/5/20/+ 50 (50.00) D
"""
    assert kiosk_hdmi.mode_candidates(text) == []
    assert kiosk_hdmi.disabled_outputs() == ["HDMI-A-2"]


def test_connected_output_prefers_the_active_port():
    outputs = [
        {"name": "HDMI-A-1", "active": False, "current_mode": None},
        {"name": "HDMI-A-2", "active": True, "current_mode": {"width": 1280, "height": 720}},
    ]
    assert kiosk_hdmi.connected_output(outputs) == "HDMI-A-2"
    outputs[0]["active"] = True
    assert kiosk_hdmi.connected_output(outputs) == "HDMI-A-1"


def test_audio_target_prefers_hdmi_stereo_and_skips_unavailable():
    dump = [
        {
            "id": 49,
            "type": "PipeWire:Interface:Device",
            "info": {
                "props": {"device.nick": "vc4-hdmi-0", "device.name": "alsa_card.platform-fef00700.hdmi"},
                "params": {
                    "EnumProfile": [
                        {"index": 0, "name": "off", "available": "yes"},
                        {"index": 1, "name": "hdmi-stereo", "available": "no"},
                        {"index": 2, "name": "hdmi-stereo-extra1", "available": "yes"},
                    ]
                },
            },
        },
        {
            "id": 50,
            "type": "PipeWire:Interface:Device",
            "info": {"props": {"device.nick": "vc4-hdmi-1"}},
        },
    ]
    assert kiosk_hdmi.audio_target(dump, "HDMI-A-1") == (49, 2)
    assert kiosk_hdmi.audio_target(dump, "HDMI-A-2") is None
    report = kiosk_hdmi.profile_report(dump, "HDMI-A-1")
    assert "hdmi-stereo available=no" in report
    dump[0]["info"]["params"]["EnumProfile"] = [
        {"index": 0, "name": "off", "available": "yes"},
        {"index": 1, "name": "output:hdmi-stereo", "available": "yes"},
        {"index": 2, "name": "output:hdmi-surround", "available": "yes"},
    ]
    assert kiosk_hdmi.audio_target(dump, "HDMI-A-1") == (49, 1)


def test_1080p50_beats_720p60_and_720p_beats_other_modes():
    text = """
Connector 0 (35) HDMI-A-1 (connected)
  1280x720@60.00 74.250 1280/110/40/220/+ 720/5/5/20/+ 60 (60.00) D
  1920x1080@50.00 148.500 1920/528/44/148/+ 1080/4/5/36/+ 50 (50.00) D
"""
    modes = kiosk_hdmi.mode_candidates(text)
    assert modes[0]["refresh"] == 50.0
    assert modes[0]["height"] == 1080

    text = """
Connector 0 (35) HDMI-A-1 (connected)
  1280x1024@60.00 108.000 1280/48/112/248/+ 1024/1/3/38/+ 60 (60.00) D
  1280x720@50.00 74.250 1280/440/40/220/+ 720/5/5/20/+ 50 (50.00) D
"""
    modes = kiosk_hdmi.mode_candidates(text)
    assert (modes[0]["width"], modes[0]["height"], modes[0]["refresh"]) == (1280, 720, 50.0)


def test_different_porches_produce_a_different_modeline():
    text = """
Connector 0 (35) HDMI-A-1 (connected)
  1920x1080@60.00 148.500 1920/88/44/148/+ 1080/4/5/36/+ 60 (60.00) D
"""
    other = """
Connector 0 (35) HDMI-A-1 (connected)
  1920x1080@60.00 138.500 1920/48/32/80/+ 1080/3/5/23/+ 60 (60.00) D
"""
    first = kiosk_hdmi.format_candidate(kiosk_hdmi.mode_candidates(text)[0])
    second = kiosk_hdmi.format_candidate(kiosk_hdmi.mode_candidates(other)[0])
    assert first != second
    assert second.startswith("HDMI-A-1 138.500 1920 1968 2000 2080 1080 1083 1088 1111 +hsync +vsync")


POSITIVE_CRTC = """
Connector 0 (35) HDMI-A-1 (connected)
  Encoder 0 (34) TMDS
    Crtc 3 (102) 1920x1080@60.00 148.500 1920/88/44/148/+ 1080/4/5/36/+ 60 (60.00) D 16:9
      Plane 3 (91) fb-id: 1
Connector 1 (44) HDMI-A-2 (connected)
  Encoder 1 (43) TMDS
    Crtc 4 (103) 1280x720@60.00 74.250 1280/110/40/220/+ 720/5/5/20/+ 60 (60.00) D
"""
POSITIVE_FIELDS = [
    "148.500", "1920", "2008", "2052", "2200", "1080", "1084", "1089", "1125", "+hsync", "+vsync",
]


def test_readback_accepts_a_matching_positive_crtc():
    assert kiosk_hdmi.crtc_matches(POSITIVE_CRTC, "HDMI-A-1", POSITIVE_FIELDS)


def test_readback_rejects_a_negative_crtc_another_timing_and_a_dropped_link():
    negative = POSITIVE_CRTC.replace("1920/88/44/148/+", "1920/88/44/148/-").replace(
        "1080/4/5/36/+", "1080/4/5/36/-"
    )
    assert kiosk_hdmi.crtc_matches(negative, "HDMI-A-1", POSITIVE_FIELDS) is False
    other = ["148.352", "1920", "2008", "2052", "2200", "1080", "1084", "1089", "1125", "+hsync", "+vsync"]
    assert kiosk_hdmi.crtc_matches(POSITIVE_CRTC, "HDMI-A-1", other) is False
    dropped = POSITIVE_CRTC.replace("HDMI-A-1 (connected)", "HDMI-A-1 (disconnected)")
    assert kiosk_hdmi.crtc_matches(dropped, "HDMI-A-1", POSITIVE_FIELDS) is False
    assert kiosk_hdmi.active_mode(POSITIVE_CRTC, "HDMI-A-2")["height"] == 720


def test_output_event_watches_hdmi_a1_only():
    assert kiosk_hdmi.watched_output({"change": "connected", "output": {"name": "HDMI-A-1"}}) == "HDMI-A-1"
    assert kiosk_hdmi.watched_output({"change": "connected", "output": {"name": "HDMI-A-2"}}) == ""
    assert kiosk_hdmi.watched_output({"change": "disconnected"}) == ""


def test_sink_id_follows_the_connector():
    dump = [
        {
            "id": 68,
            "type": "PipeWire:Interface:Node",
            "info": {"props": {"media.class": "Audio/Sink", "node.name": "alsa_output.platform-bcm2835.stereo"}},
        },
        {
            "id": 70,
            "type": "PipeWire:Interface:Node",
            "info": {
                "props": {
                    "media.class": "Audio/Sink",
                    "node.name": "alsa_output.platform-fef00700.hdmi.hdmi-stereo",
                }
            },
        },
    ]
    assert kiosk_hdmi.sink_id(dump, "HDMI-A-1") == 70
    assert kiosk_hdmi.sink_id(dump, "HDMI-A-2") is None
