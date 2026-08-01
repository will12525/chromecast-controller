# Chromecast Controller — Agent Rules

Self-hosted LAN media library + Chromecast remote (optional MP4 editor).  
Stack: **Flask**, **SQLite**, **pychromecast**, plain JS (no bundler), **ffmpeg** for editor only.

Remote: `git@github.com:will12525/chromecast-controller.git`

---

## Principles (non-negotiable)

- **YAGNI / KISS.** No transcoding pipeline, multi-user auth, TMDB/metadata agents, cloud sync, or Collections product.
- **LAN trust model.** No Flask auth. Transfer handshake is a shared secret for LAN convenience, not real security.
- **Local MP4s only.** Catalog is filename + optional manual cover/description. Do not add external metadata scrapers.
- **Reuse before invent.** Shelves and library views are curated queries over existing tags/containers — not new domain models.
- Prefer small, reversible changes. Back up notes apply to `media_metadata.db` (gitignored live DBs).

---

## Architecture map

```
Browser (Jinja + Bootstrap + app/static/js/*)
        │  JSON
Flask (run.py → create_app → main_bp)
        │
BackEndHandler (singleton; started in app/routes/shared.py)
├── ChromecastHandler (daemon thread)
├── DBHandler → media_metadata.db
├── mp4_splitter (SERVER editor)
└── content_transfer (CLIENT ↔ SERVER)

http-server on media disks (:8000+)  ← Chromecast/browser fetch media
```

| Concern | Put code here |
|---------|----------------|
| HTTP routes | `app/routes/{library,cast,editor,transfer}_routes.py` |
| Shared route state / `APIEndpoints` | `app/routes/shared.py` |
| Blueprint registration | `app/routes/__init__.py` |
| Test import facade | `app/routes/main_routes.py` (re-exports; keep working) |
| SQLite access + schema version | `app/database/db_access.py` (`DBConnection.VERSION`) |
| Queries / shelf lists / progress | `app/database/db_getter.py`, `db_queries.py` |
| Disk scan → catalog | `app/database/media_metadata_collector.py` |
| Cast control | `app/utils/chromecast_handler.py` |
| Background scan/editor jobs | `app/utils/backend_handler.py` |
| CLIENT/SERVER pull | `app/utils/content_transfer.py` |
| Config load | `app/utils/config_file_handler.py` → `app/config.json` |
| Front-end modules | `app/static/js/*.js` (see load order below) |
| Templates | `app/templates/` |

Do **not** reintroduce a monolithic `flask_endpoints.py` or root-level handler modules. Package layout under `app/` is the source of truth.

---

## Domain model (schema v3)

Tables: `content_directory`, `container`, `content`, `container_content`, `container_container`, `user_tags`, `user_tags_content`, `version_info`.

**content** playback fields: `play_count`, `last_position`, `last_played_at`, `last_duration`, `added_at`.

### Filename conventions (scanner — do not break)

| Type | Pattern | Folder |
|------|---------|--------|
| TV | `Show Name - s01e01.mp4` | `tv_shows/` |
| Movie | `Title (2010).mp4` | `movies/` |
| Book | `Title - Author.mp4` | `books/` |

### Migrations

- Bump `DBConnection.VERSION` and implement **idempotent** `ALTER` / updates in the existing migration path (`create_db` / `update_database`).
- Prefer additive columns with defaults. Note backup of `media_metadata.db` in README when schema changes.
- Never require a full re-scan for upgrades if avoidable (`INSERT OR IGNORE` keeps ids).

---

## Config

- **`app/config.json`**: `mode` (`SERVER`|`CLIENT`), `media_folders[]` (`content_src`, `content_url`), editor paths, optional `server_url` (CLIENT), optional transfer handshake overrides.
- Handshake may also come from env: `TRANSFER_HANDSHAKE_SECRET` / `TRANSFER_HANDSHAKE_RESPONSE`.
- **`config.cfg`**: helper path for http-server setup scripts — not the Flask app config.
- Ports: local **5001**, production/systemd **5000** (`./start_server` / `./start_server production`).

Do not commit real LAN secrets or machine-specific paths into docs as requirements; examples may use placeholders.

---

## Front-end rules

- **No bundler, no ES modules required.** Scripts are plain globals so template `onclick` handlers keep working.
- Load order (templates must preserve):

  `shared.js` → `chromecast.js` → `browse.js` → `playback.js` → `scan.js` → `library.js` → `app_main.js`

- `app/static/app.js` is a thin legacy stub — do not re-monolith UI there.
- Editor page also loads `app_editor.js` after the shared chain.
- Progress POSTs: throttle (~10s or pause/unload). Resume: auto-seek if position ∈ (30s, 90% of duration).
- Chromecast identity is **device UUID**; friendly name is display-only.

When adding UI behavior, put it in the matching module (playback vs library vs browse vs cast vs scan), not a new mega-file.

---

## API / routes conventions

- Single blueprint `main_bp`; split across route modules for maintainability.
- Prefer existing `APIEndpoints` enum values; add new members in `shared.py` when introducing routes.
- Style today is mostly **JSON POST** for mutations/queries; home is **`GET /library/home`**. Match surrounding endpoints.
- Keep URL paths stable unless intentionally versioning — tests and templates hardcode paths.
- Scan is **async**: start job + poll `GET /scan_status`; do not block the request on full disk walk.

---

## Testing

```bash
# Default / CI (required before claiming done)
pytest tests/ -m "not integration" -q

# Optional local only (live Chromecast, editor fixtures, seeded DB)
pytest tests/ -m integration -q
```

- Mark tests that need live hardware or real media DBs with `@pytest.mark.integration`.
- CI (`.github/workflows/github-action.yml`) runs unit suite only with `PYTHONPATH` at repo root.
- Prefer unit tests with mocks (`tests/pytest_mocks.py`) over expanding integration surface.
- Keep `main_routes` / `APIEndpoints` importable for existing tests when moving code.
- Do not commit `tests/junit/` artifacts or `*.db` files.

---

## What not to change without explicit ask

- Transcoding / subtitle pipeline
- Multi-user accounts or remote auth
- External metadata agents (TMDB, etc.)
- Rewriting cast stack “while here”
- Replacing SQLite or introducing an ORM
- Adding a JS bundler or framework (React/Vue) unless scoped as a deliberate project
- Force-pushing `main` or rewriting published history

---

## Completed product scope (do not re-implement)

Phase 1 Library UX + Phase 2 backlog are **done**: home shelves, progress/resume, library nav, unified search, async scan status, route split, content_transfer hardening (no `input()`, timeouts, config/env secrets), Chromecast UUID ids, `added_at`, test markers, front-end module split.

New work is **new scope**, not unfinished plan items. Historical design doc lived in a session `plan.md`; product docs live in **README.md**.

---

## Entire (session / checkpoint tracking)

This repo is **Entire-enabled**. Checkpoints link agent work to git commits via git hooks and agent hooks.

| Item | Location / command |
|------|--------------------|
| Project settings (commit) | `.entire/settings.json` |
| Local runtime (ignore) | `.entire/logs/`, `.entire/metadata/`, `.entire/settings.local.json` |
| Checkpoint metadata branch | `entire/checkpoints/v1` (pushed on `git push` via pre-push hook) |
| Status | `entire status` / `entire doctor` / `entire checkpoint list` |

**Installed agent:** Cursor (`.cursor/hooks.json`). Entire has **no first-party Grok Build agent** yet — Grok sessions under `~/.grok/sessions/` are **not** auto-checkpointed. For live capture use Cursor (or another supported agent), or later an `entire-agent-grok` external plugin.

**Git hooks** use absolute path to `~/.local/bin/entire` (`absolute_git_hook_path: true`) so GUI / minimal-PATH commits still run Entire. Keep `~/.local/bin` on interactive PATH for Cursor agent hooks (`command -v entire`).

**Do not** hand-edit `.cursor/hooks.json` into non-standard shapes — Entire detects the Cursor agent by that file’s command pattern. Reinstall with `entire agent add cursor --force` if needed, then `entire configure --absolute-git-hook-path --force` if git hooks lost absolute paths.

**Workflow for checkpoints:** start a supported agent session → edit → `git commit` (accept session link if prompted) → `git push` (syncs `entire/checkpoints/v1`). Optional: `entire login` for entire.io cloud features. CI changelog workflow is best-effort Entire telemetry.

**Agents should not** disable Entire, force-push over `entire/checkpoints/v1`, or commit `.entire/logs/`.

---

## Git and commits

- Branch often used for this workstream: `fix_tests` (confirm with `git status` / user).
- Commit messages: short imperative summary (match history: “Phase N: …”, “Harden …”, “Add …”).
- Do not commit: `*.db`, `config.json.old`, `output.txt`, `.venv/`, `node_modules/`, local media paths.
- Do not push, open PRs, or amend published commits unless the user asks.
- Prefer focused commits over mixed refactors + features.
- After agent-driven commits with a **supported** Entire agent, expect an `Entire-Checkpoint:` trailer when linking succeeds.

---

## Verification checklist

Before finishing a task:

1. `pytest tests/ -m "not integration" -q` passes.
2. New routes registered and importable; facade/`APIEndpoints` still work if tests depend on them.
3. Front-end: correct script order if templates touched; globals used by `onclick` still defined.
4. Schema change: version bumped + idempotent migration + README note if user-facing.
5. No interactive prompts in server paths (`input()` is forbidden in headless code).
6. README updated only when behavior/setup/architecture user-facing surface changes.

---

## Quick file touch guide

| Change type | Primary files |
|-------------|----------------|
| New shelf / home data | `db_getter.py`, `library_routes.py`, `static/js/library.js` |
| Playback / resume | `library_routes.py` (`/playback_progress`, play handlers), `playback.js`, `chromecast_handler.py` |
| Browse / tags / search | `library_routes.py` (`/query_db`), `browse.js` |
| Cast list / commands | `cast_routes.py`, `chromecast_handler.py`, `chromecast.js` |
| Scan | `backend_handler.py`, `media_metadata_collector.py`, `scan.js` |
| Editor | `editor_routes.py`, `mp4_splitter.py`, `app_editor.js` |
| Client sync | `content_transfer.py`, `transfer_routes.py` |
| CI | `.github/workflows/github-action.yml` |
