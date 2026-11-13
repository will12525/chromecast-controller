# Chromecast Controller

Self-hosted LAN media library with Chromecast casting, a browser player, and an optional MP4 splitter editor.

Inspired by a streaming-service **Home** (billboard, Continue Watching, tag rows as genres), kept small with **YAGNI/KISS**: local MP4 files, SQLite catalog, no transcoding or multi-user stack.

## Features

- **Library home** — billboard, Continue Watching / Recently Added / Recently Played, and user-tag genre rows
- **Browse** — TV / Movies / Books grids, tag chips, unified search, title overlay, operator Table view
- **Play** — Chromecast (device UUID) and/or local HTML5; multi-device connect with stream modes; sequential next-in-show and tag-random playlists; resume position
- **Catalog** — scan disks for TV / movies / books by filename convention
- **Editor (SERVER mode)** — split raw MP4s into library layout with ffmpeg
- **Optional client mode** — local playback only. Sync copies the shows, seasons, and episodes chosen on the server.

### Playback & cast controls

Media files are progressive **HTTP MP4** from the per-disk `http-server` (`content_url`). Flask does not re-encode.

| Stream mode | Behavior |
|-------------|----------|
| **Local** | Bottom bar controls the browser `<video>` player |
| **Device** | Play/commands go to one connected Chromecast |
| **All connected** | Same media and transport commands fan out to every connected cast; multi-start loads in parallel then plays together (near-sync) |

Optional config `multi_cast_go_delay_ms` (default `0`): after all devices are loaded/paused, wait this many ms before the simultaneous `play()` burst (scheduled go-signal experiment).

| Play mode | Behavior on finish / next |
|-----------|---------------------------|
| **Sequential** | Next episode in the show (default when starting a TV episode) |
| **Reverse** | Previous episode (series backwards; stops at the start) |
| **Tag random** | Random item with the same tags; mode **persists** even if an episode is picked |
| **Container random** | Random item within the current show/container |
| **Single** | Stop; no auto-next |

- Mode selector is on the bottom bar; choice is stored in `localStorage` (`cc_play_mode`) and sent as `play_mode` on play/next. The chip updates from the **server** response after play/next.
- Connect multiple Chromecasts from the cast menu (checkmark = connected). Use **All connected**, **Local**, or **Use** on a device.
- Bottom bar: **−15 / +15**, play/pause/stop, rewind / next (advance follows current play mode).
- Scrubber works with touch and mouse; seeks the active target (or all in **All** mode).
- Cast uses pychromecast **BUFFERED** stream type for VOD MP4s.
- Non-Cast TVs: open the same LAN `content_url` in the TV browser or an external player (no DLNA built in).

```bash
# Unit suite (CI) — includes play_mode unit tests
pytest tests/ -m "not integration" -q

# Play-mode API only (local stream_mode — does NOT change TV)
# Needs non-empty media_metadata.db (Scan Media in the app first).
pytest tests/test_cast_play_modes_integration.py -m integration -q

# Live Chromecast (will play/pause on real devices)
# CAST_DEVICE_1="Family Room TV" CAST_DEVICE_2="Bedroom" \
pytest tests/test_cast_streaming_integration.py -m integration -q

# Full disk rescan from tests is opt-in only (slow / looks like a hang):
# CAST_ALLOW_FULL_SCAN=1 pytest ...
```

### Filename conventions

| Type | Pattern |
|------|---------|
| TV | `Show Name - s01e01.mp4` under `tv_shows/` |
| Movie | `Title (2010).mp4` under `movies/` |
| Book | `Title - Author.mp4` under `books/` |

## Architecture

- **Flask** (port 5001 local / 5000 production) — UI, SQLite, Chromecast control
- **http-server** on media disks — serves MP4/images to Chromecast and browser
- **SQLite** `media_metadata.db` — containers, content, tags, playback progress

## Setup

Update config:

- [config.cfg](config.cfg): media path for http-server helpers
- [app/config.json](app/config.json): mode, media folders, editor paths

Example `app/config.json`:

```json
{
  "mode": "SERVER",
  "editor_raw_folder": "/media/ssd_splitter/splitter/raw_files/",
  "editor_raw_url": "http://192.168.x.xxx:8001/",
  "media_folders": [
    {
      "content_src": "/media/raid/",
      "content_url": "http://192.168.x.xxx:8000/"
    }
  ]
}
```

- `mode`: `CLIENT` or `SERVER`
- `content_src`: absolute path on disk
- `content_url`: LAN URL where that path is served by http-server
- `server_url` (CLIENT): base URL of the SERVER node
- `client_name` (CLIENT, optional): stable name for this device. Otherwise the hostname is used. Two devices that sanitize to the same name share one manifest.
- Optional transfer handshake overrides: `transfer_handshake_secret` / `transfer_handshake_response` in config, or env `TRANSFER_HANDSHAKE_SECRET` / `TRANSFER_HANDSHAKE_RESPONSE`

### CLIENT and clone manifests

A CLIENT plays in the browser only. The cast menu is not shown, and cast routes answer 404.

The SERVER gear menu opens **Clone**. That page lists clients that have connected (active means seen in the last 15 minutes, otherwise historical). Pick a show, season, or episode on the server side. A show or season is expanded again on each sync, so new episodes are included. Unchecking one episode stores an exclude and does not copy it. **Remove from client** queues that file for deletion the next time the client applies a sync. The show poster travels with any episode of that show. A movie or book brings its own cover. Season posters and episode stills are not copied. Seasons and episodes display the show poster in the library.

Nothing is copied or deleted until the client presses **Sync** in its gear menu. Sync asks the server for a list of absolute media URLs paired with catalog paths, then downloads each URL from that disk's http-server. A finished file is skipped. An unfinished copy stays as a `.partial` file and resumes on the next Sync. One failed file does not stop the rest. If `server_url` does not answer, the client writes `var/clone_pending.json` and the next Scan that reaches the server applies it. A Scan with nothing pending only refreshes the client list. Media files are deleted only on the CLIENT.

Manifests live in `var/clone_manifests/<client_id>.json` on the server. Back that directory up with `media_metadata.db` if the selections matter. Saves overwrite the current file. There is no change log.

Install packages:

```bash
apt update && apt install sqlite3 ffmpeg npm
sudo ./setup.sh
```

### Raspberry Pi client

On the Pi, this is the client command. It calls `setup.sh` after it records a USB mount.

```bash
sudo ./setup_client.sh
```

Reboot when it finishes. The kiosk keeps HDMI on and does not send HDMI-CEC. When HDMI-A-1 connects, it picks the best positive progressive mode that display lists, at most 1080p60, trying 1080p before 720p, and sends audio to that port. HDMI-A-2 is left disabled. It disables Wi-Fi and Bluetooth, leaves Ethernet on DHCP, and leaves SSH enabled. tty1 autologins into the Chromium kiosk. HDMI is the system audio output, and the keyboard volume keys change that level. Ctrl+Alt+F2 is still a normal login. USB disks already listed in fstab are left in place. The first USB mount is written to `MEDIA_DIR` in [config.cfg](config.cfg) when that value is empty. `sudo ./setup.sh` remains the SERVER command and still requires `MEDIA_DIR`. The script does not change `server_url`. Add that in [app/config.json](app/config.json) when this client should clone from a server.

## Run locally

```bash
./start_server
```

Open `http://<host>:5001/`.

### Systemd services

- `chromecast_controller.service`
- `media_drive_as_webpage.service`

```bash
sudo systemctl <start|stop|restart> <service>
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock
# Phase 3 unit suite (CI default)
pytest tests/ -m "not integration" -q

# Optional local integration (live Chromecast / editor fixtures / seeded DB)
pytest tests/ -m integration -q
```

### Front-end layout (Phase 4)

Browser scripts are plain globals (no bundler) under `app/static/js/`:

| File | Responsibility |
|------|----------------|
| `shared.js` | State, constants, `fetchAndSetData` |
| `chromecast.js` | Multi-device cast menu, connect, stream mode |
| `player_controls.js` | Unified Local + Cast transport (bottom bar) |
| `browse.js` | Poster grid, table, query_db, tags/modal |
| `playback.js` | Play, resume progress, player overlay |
| `scan.js` | Scan toast + status polling (confirm in Manage) |
| `library.js` | Billboard, home rows, library nav, search |
| `title.js` | Title overlay (`GET /library/title`) |
| `ui_nav.js` | Hash routes, tag chips, nav |
| `app_main.js` | DOMContentLoaded / navbar wiring |

Load order is set in `index.html` / `editor.html`. Template `onclick` handlers still call global function names.

Chromecast control stays on the Flask server (`pychromecast`). The browser does not host a Cast instance. Manage (gear) holds Table, Editor, and Scan-with-confirm. Title overlays have no metadata pencils — edit covers on `/table`.

Schema migrations run on app start via `DBHandler.create_db()` (currently version **3**: playback progress + `added_at` for Recently Added).

## Notes

- Chromecast needs HTTP media URLs reachable on the LAN (the separate http-server ports).
- Resume auto-seeks when progress is past 30s and under 90% of duration.
- Back up `media_metadata.db` before major upgrades.

## Entire (optional agent history)

This repository is set up for [Entire](https://entire.io/) so AI agent sessions can be checkpointed into git.

```bash
# CLI (if missing)
curl -fsSL https://entire.io/install.sh | bash   # installs to ~/.local/bin/entire

cd /path/to/chromecast-controller
entire status          # should show Enabled + Cursor agent
entire doctor
entire checkpoint list
```

- Shared settings: `.entire/settings.json` (committed). Git hooks use an absolute `entire` path for reliability.
- Agent hooks: Cursor via `.cursor/hooks.json` (local; re-run `entire agent add cursor` on a new machine).
- Checkpoint metadata lives on branch `entire/checkpoints/v1` and is pushed with normal `git push`.
- **Grok Build is not a first-party Entire agent** — use Cursor (or another supported agent) for automatic session capture until an external `entire-agent-grok` plugin exists.
- Optional cloud: `entire login` and GitHub secrets `ENTIRE_API_TOKEN` / `ENTIRE_TOKEN` for the changelog workflow.
