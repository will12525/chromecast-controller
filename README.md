# Chromecast Controller

Self-hosted LAN media library with Chromecast casting, a browser player, and an optional MP4 splitter editor.

Inspired by a Plex-style **Home** (Continue Watching, Recently Added, library shortcuts), kept small with **YAGNI/KISS**: local MP4 files, SQLite catalog, no transcoding or multi-user stack.

## Features

- **Library home** — shelves for Continue Watching, Recently Added, Recently Played, and TV / Movies / Books
- **Browse** — tag filters, unified search, card grid and table view
- **Play** — Chromecast (identified by device UUID) or local HTML5; sequential next-in-show and tag-random playlists; resume position
- **Catalog** — scan disks for TV / movies / books by filename convention
- **Editor (SERVER mode)** — split raw MP4s into library layout with ffmpeg
- **Optional client mode** — pull missing content from a server node

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
pytest tests/test_library_home.py tests/test_content_transfer_unit.py -q
```

Schema migrations run on app start via `DBHandler.create_db()` (currently version **2**: playback progress columns).

## Notes

- Chromecast needs HTTP media URLs reachable on the LAN (the separate http-server ports).
- Resume auto-seeks when progress is past 30s and under 90% of duration.
- Back up `media_metadata.db` before major upgrades.
