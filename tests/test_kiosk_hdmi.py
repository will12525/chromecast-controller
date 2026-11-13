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


def test_larger_mode_wins_over_a_closer_refresh():
    text = """
Connector 0 (35) HDMI-A-1 (connected)
  1280x720@60.00 74.250 1280/110/40/220/+ 720/5/5/20/+ 60 (60.00) D
  1920x1080@24.00 74.250 1920/88/44/148/+ 1080/4/5/36/+ 24 (24.00) D
"""
    modes = kiosk_hdmi.mode_candidates(text)
    assert (modes[0]["width"], modes[0]["height"]) == (1920, 1080)


def test_hdmi_a1_wins_when_both_ports_are_connected():
    text = """
Connector 0 (35) HDMI-A-1 (connected)
  1920x1080@60.00 148.500 1920/88/44/148/+ 1080/4/5/36/+ 60 (60.00) D
Connector 1 (44) HDMI-A-2 (connected)
  1280x720@60.00 74.250 1280/110/40/220/+ 720/5/5/20/+ 60 (60.00) D
"""
    modes = kiosk_hdmi.mode_candidates(text)
    assert {mode["connector"] for mode in modes} == {"HDMI-A-1"}


def test_only_hdmi_a2_is_used_when_it_is_the_connected_port():
    text = """
Connector 0 (35) HDMI-A-1 (disconnected)
Connector 1 (44) HDMI-A-2 (connected)
  1280x720@50.00 74.250 1280/110/40/220/+ 720/5/5/20/+ 50 (50.00) D
"""
    modes = kiosk_hdmi.mode_candidates(text)
    assert modes[0]["connector"] == "HDMI-A-2"
    assert modes[0]["height"] == 720


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
                        {"name": "off", "available": "yes"},
                        {"name": "hdmi-stereo", "available": "no"},
                        {"name": "hdmi-stereo-extra1", "available": "yes"},
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
    assert kiosk_hdmi.audio_target(dump, "HDMI-A-1") == (49, "hdmi-stereo-extra1")
    assert kiosk_hdmi.audio_target(dump, "HDMI-A-2") is None
    report = kiosk_hdmi.profile_report(dump, "HDMI-A-1")
    assert "hdmi-stereo available=no" in report


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
