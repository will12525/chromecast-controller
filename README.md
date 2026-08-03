# Chromecast Controller

Self-hosted LAN media library with Chromecast casting, a browser player, and an optional MP4 splitter editor.

Inspired by a Plex-style **Home** (Continue Watching, Recently Added, library shortcuts), kept small with **YAGNI/KISS**: local MP4 files, SQLite catalog, no transcoding or multi-user stack.

## Features

- **Library home** — shelves for Continue Watching, Recently Added, Recently Played, and TV / Movies / Books
- **Browse** — tag filters, unified search, card grid and table view
- **Play** — Chromecast (device UUID) and/or local HTML5; multi-device connect with stream modes; sequential next-in-show and tag-random playlists; resume position
- **Catalog** — scan disks for TV / movies / books by filename convention
- **Editor (SERVER mode)** — split raw MP4s into library layout with ffmpeg
- **Optional client mode** — pull missing content from a server node

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
- `server_url` (CLIENT): base URL of the SERVER node for content pull on scan
- Optional transfer handshake overrides: `transfer_handshake_secret` / `transfer_handshake_response` in config, or env `TRANSFER_HANDSHAKE_SECRET` / `TRANSFER_HANDSHAKE_RESPONSE`

Install packages:

```bash
apt update && apt install sqlite3 ffmpeg npm
sudo ./setup.sh
```

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
| `browse.js` | Cards, table, query_db, tags/modal |
| `playback.js` | Play, resume progress, shuffle |
| `scan.js` | Scan toast + status polling |
| `library.js` | Home shelves, library nav, search |
| `app_main.js` | DOMContentLoaded / navbar wiring |

Load order is set in `index.html` / `editor.html`. Template `onclick` handlers still call global function names.

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
