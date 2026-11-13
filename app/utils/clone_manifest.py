"""Per-client clone manifests and the CLIENT apply/delete path.

The server stores one JSON file per client. It never unlinks media.
File deletion runs only when system mode is CLIENT, and the mode check
sits on the line above each unlink.
"""
import json
import pathlib
import re
import socket
from datetime import datetime, timedelta, timezone

from app.utils.common import SystemMode
from app.utils.config_file_handler import load_json_file_content

MANIFEST_DIR = pathlib.Path("var/clone_manifests")
PENDING_PATH = pathlib.Path("var/clone_pending.json")
ACTIVE_WINDOW = timedelta(minutes=15)
_ID_RE = re.compile(r"[^A-Za-z0-9._-]")


def current_system_mode():
    cfg = load_json_file_content() or {}
    if cfg.get("mode") == SystemMode.SERVER.name:
        return SystemMode.SERVER
    return SystemMode.CLIENT


def safe_client_id(raw):
    cleaned = _ID_RE.sub("-", (raw or "").strip())
    cleaned = cleaned.strip(".-")[:80]
    if not cleaned or cleaned in (".", ".."):
        return "client"
    return cleaned


def client_identity():
    """Return (client_id, display_name) from config client_name or hostname."""
    cfg = load_json_file_content() or {}
    display = (cfg.get("client_name") or socket.gethostname() or "client").strip()
    return safe_client_id(display), display or "client"


def _now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def empty_manifest(client_id, display_name=None):
    return {
        "client_id": client_id,
        "display_name": display_name or client_id,
        "last_seen": None,
        "updated_at": None,
        "inventory": [],
        "selections": [],
        "exclude": [],
        "remove": [],
    }


def manifest_path(client_id):
    return MANIFEST_DIR / f"{safe_client_id(client_id)}.json"


def load_manifest(client_id):
    path = manifest_path(client_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    base = empty_manifest(safe_client_id(client_id), data.get("display_name"))
    base.update(data)
    base["client_id"] = safe_client_id(client_id)
    base["selections"] = list(data.get("selections") or [])
    base["exclude"] = list(data.get("exclude") or [])
    base["remove"] = list(data.get("remove") or [])
    base["inventory"] = list(data.get("inventory") or [])
    return base


def save_manifest(manifest):
    client_id = safe_client_id(manifest.get("client_id"))
    manifest = dict(manifest)
    manifest["client_id"] = client_id
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    path = manifest_path(client_id)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def upsert_client(client_id, display_name=None):
    client_id = safe_client_id(client_id)
    current = load_manifest(client_id) or empty_manifest(client_id, display_name)
    if display_name:
        current["display_name"] = display_name
    current["last_seen"] = _now()
    return save_manifest(current)


def is_active(last_seen, now=None):
    if not last_seen:
        return False
    try:
        seen = datetime.fromisoformat(str(last_seen).replace("Z", "+00:00"))
    except ValueError:
        return False
    current = now or datetime.now(timezone.utc)
    if seen.tzinfo is None:
        seen = seen.replace(tzinfo=timezone.utc)
    return current - seen <= ACTIVE_WINDOW


def list_clients():
    if not MANIFEST_DIR.is_dir():
        return []
    clients = []
    for path in sorted(MANIFEST_DIR.glob("*.json")):
        manifest = load_manifest(path.stem)
        if not manifest:
            continue
        manifest["active"] = is_active(manifest.get("last_seen"))
        clients.append(manifest)
    clients.sort(key=lambda row: (not row.get("active"), (row.get("display_name") or "").lower()))
    return clients


def interpret_contact(result, apply, source="scan"):
    """Decide pending-flag and user text after a server contact.

    A failed or unreachable apply keeps the pending flag. Success clears it
    only when the caller has finished the apply.
    """
    result = result or {}
    if not apply:
        if result.get("status") == "ok":
            return {
                "status": "ok",
                "message": "Scan complete (inventory updated)",
                "set_pending": False,
                "clear_pending": False,
                "rescan": False,
            }
        if result.get("status") == "skipped":
            return {
                "status": "ok",
                "message": "Scan complete. Server unreachable.",
                "set_pending": False,
                "clear_pending": False,
                "rescan": False,
            }
        return {
            "status": "error",
            "message": result.get("message") or "inventory update failed",
            "set_pending": False,
            "clear_pending": False,
            "rescan": False,
        }
    if result.get("applied"):
        message = "Sync complete" if source == "sync" else "Scan complete (sync applied)"
        return {
            "status": "ok",
            "message": message,
            "set_pending": False,
            "clear_pending": True,
            "rescan": True,
        }
    if result.get("status") == "skipped":
        message = (
            "Server unreachable. Sync will run on the next scan."
            if source == "sync"
            else "Scan complete. Server unreachable, sync still pending."
        )
        return {
            "status": "ok",
            "message": message,
            "set_pending": True,
            "clear_pending": False,
            "rescan": False,
        }
    return {
        "status": "error",
        "message": result.get("message") or "Sync did not finish",
        "set_pending": True,
        "clear_pending": False,
        "rescan": False,
    }


def pending_is_set():
    if not PENDING_PATH.is_file():
        return False
    try:
        data = json.loads(PENDING_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(isinstance(data, dict) and data.get("pending"))


def set_pending():
    PENDING_PATH.parent.mkdir(parents=True, exist_ok=True)
    PENDING_PATH.write_text(json.dumps({"pending": True}) + "\n", encoding="utf-8")


def clear_pending():
    if current_system_mode() != SystemMode.CLIENT:
        return False
    if PENDING_PATH.exists():
        PENDING_PATH.unlink()
    return True


def store_inventory(client_id, inventory, removed=None):
    manifest = load_manifest(client_id) or empty_manifest(safe_client_id(client_id))
    manifest["inventory"] = [
        {"content_src": row.get("content_src")}
        for row in (inventory or [])
        if isinstance(row, dict) and row.get("content_src")
    ]
    if removed:
        gone = set(removed)
        manifest["remove"] = [src for src in manifest.get("remove") or [] if src not in gone]
    manifest["last_seen"] = _now()
    return save_manifest(manifest)


def save_selection(client_id, selections, exclude, remove):
    manifest = load_manifest(client_id) or empty_manifest(safe_client_id(client_id))
    manifest["selections"] = list(selections or [])
    manifest["exclude"] = list(exclude or [])
    manifest["remove"] = list(remove or [])
    manifest["updated_at"] = _now()
    return save_manifest(manifest)


def _episode_row(content_src, title, img_src, show_id, show_img_src, show_title):
    return {
        "content_src": content_src,
        "title": title or content_src,
        "img_src": img_src or "",
        "show_id": show_id,
        "show_img_src": show_img_src or "",
        "show_title": show_title or "",
    }


def catalog_from_db(db):
    """Build the lookup tables build_clone_plan and the clone tree use."""
    containers = db.get_data_from_db(
        "SELECT container.id, container.container_title, container.img_src, "
        "MIN(container_container.parent_container_id) AS parent_id, "
        "GROUP_CONCAT(DISTINCT user_tags.tag_title) AS tags "
        "FROM container "
        "LEFT JOIN container_container ON container.id = container_container.container_id "
        "LEFT JOIN user_tags_content ON container.id = user_tags_content.container_id "
        "LEFT JOIN user_tags ON user_tags_content.user_tags_id = user_tags.id "
        "GROUP BY container.id;"
    ) or []
    contents = db.get_data_from_db(
        "SELECT content.content_src, content.content_title, content.img_src, "
        "content_directory.content_url AS content_url, "
        "MIN(container_content.parent_container_id) AS parent_id, "
        "GROUP_CONCAT(DISTINCT user_tags.tag_title) AS tags "
        "FROM content "
        "INNER JOIN content_directory ON content.content_directory_id = content_directory.id "
        "LEFT JOIN container_content ON content.id = container_content.content_id "
        "LEFT JOIN user_tags_content ON content.id = user_tags_content.content_id "
        "LEFT JOIN user_tags ON user_tags_content.user_tags_id = user_tags.id "
        "GROUP BY content.id;"
    ) or []
    shows = {}
    for row in containers:
        tags = set((row.get("tags") or "").split(","))
        if "tv show" not in tags:
            continue
        show_id = row.get("id")
        shows[show_id] = {
            "container_id": show_id,
            "title": row.get("container_title") or "",
            "img_src": row.get("img_src") or "",
            "img_url": "",
            "seasons": [],
        }
    seasons_by_show = {show_id: [] for show_id in shows}
    for row in containers:
        parent_id = row.get("parent_id")
        if parent_id in shows and row.get("id") not in shows:
            seasons_by_show[parent_id].append(row)
    episodes_by_parent = {}
    for row in contents:
        parent_id = row.get("parent_id")
        episodes_by_parent.setdefault(parent_id, []).append(row)

    def _cover_url(img_src, content_url):
        if not img_src or not content_url:
            return ""
        return f"{content_url}{img_src}"

    for show_id, show in shows.items():
        sample_url = ""
        for ep in episodes_by_parent.get(show_id) or []:
            sample_url = ep.get("content_url") or ""
            if sample_url:
                break
        for season in seasons_by_show.get(show_id) or []:
            for ep in episodes_by_parent.get(season.get("id")) or []:
                sample_url = ep.get("content_url") or sample_url
                if sample_url:
                    break
        show["img_url"] = _cover_url(show.get("img_src"), sample_url)
        for season in seasons_by_show.get(show_id) or []:
            episodes = [
                _episode_row(
                    ep.get("content_src"),
                    ep.get("content_title"),
                    ep.get("img_src"),
                    show_id,
                    show.get("img_src") or "",
                    show.get("title") or "",
                )
                for ep in episodes_by_parent.get(season.get("id")) or []
            ]
            show["seasons"].append(
                {
                    "container_id": season.get("id"),
                    "title": season.get("container_title") or "",
                    "episodes": episodes,
                }
            )
        direct = [
            _episode_row(
                ep.get("content_src"),
                ep.get("content_title"),
                ep.get("img_src"),
                show_id,
                show.get("img_src") or "",
                show.get("title") or "",
            )
            for ep in episodes_by_parent.get(show_id) or []
        ]
        if direct:
            show["seasons"].append(
                {
                    "container_id": show_id,
                    "title": show.get("title") or "",
                    "episodes": direct,
                    "direct": True,
                }
            )

    def _flat(tag, kind):
        rows = []
        for item in contents:
            tags = set((item.get("tags") or "").split(","))
            if tag not in tags or item.get("parent_id"):
                continue
            rows.append(
                {
                    "kind": kind,
                    "content_src": item.get("content_src"),
                    "title": item.get("content_title") or item.get("content_src"),
                    "img_src": item.get("img_src") or "",
                    "img_url": _cover_url(item.get("img_src"), item.get("content_url")),
                }
            )
        return rows

    content_by_src = {}
    for show in shows.values():
        for season in show["seasons"]:
            for ep in season["episodes"]:
                if ep.get("content_src"):
                    content_by_src[ep["content_src"]] = ep
    movies = _flat("movie", "movie")
    books = _flat("book", "book")
    for item in movies + books:
        if item.get("content_src"):
            content_by_src[item["content_src"]] = {
                "content_src": item["content_src"],
                "title": item["title"],
                "img_src": item["img_src"],
                "show_id": None,
                "show_img_src": "",
                "show_title": "",
                "kind": item["kind"],
            }
    return {
        "shows": shows,
        "movies": movies,
        "books": books,
        "content_by_src": content_by_src,
    }


def _episodes_for_show(catalog, show_id):
    show = catalog["shows"].get(show_id) or catalog["shows"].get(_as_int(show_id))
    if not show:
        return []
    episodes = []
    for season in show["seasons"]:
        episodes.extend(season["episodes"])
    return episodes


def _episodes_for_season(catalog, season_id):
    season_id = _as_int(season_id)
    for show in catalog["shows"].values():
        for season in show["seasons"]:
            if season.get("container_id") == season_id:
                return season["episodes"], show
    return [], None


def _as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def build_clone_plan(manifest, catalog):
    """Expand selections to download and delete lists. Does not touch disk."""
    exclude = set(manifest.get("exclude") or [])
    downloads = []
    seen = set()

    def add_episode(ep, kind):
        src = ep.get("content_src")
        if not src or src in exclude or src in seen:
            return
        seen.add(src)
        cover = ""
        if kind in ("movie", "book"):
            cover = ep.get("img_src") or ""
        else:
            cover = ep.get("show_img_src") or ""
        downloads.append(
            {
                "content_src": src,
                "title": ep.get("title") or src,
                "kind": kind,
                "cover_img_src": cover,
                "show_id": ep.get("show_id"),
            }
        )

    for selection in manifest.get("selections") or []:
        kind = selection.get("kind")
        if kind == "show":
            for ep in _episodes_for_show(catalog, selection.get("container_id")):
                add_episode(ep, "episode")
        elif kind == "season":
            episodes, _show = _episodes_for_season(catalog, selection.get("container_id"))
            for ep in episodes:
                add_episode(ep, "episode")
        elif kind in ("episode", "movie", "book"):
            src = selection.get("content_src")
            ep = (catalog.get("content_by_src") or {}).get(src)
            if ep:
                add_episode(ep, "episode" if kind == "episode" else kind)
            elif src and src not in exclude:
                add_episode(
                    {"content_src": src, "title": src, "img_src": "", "show_img_src": "", "show_id": None},
                    kind if kind != "episode" else "episode",
                )

    covers = []
    cover_seen = set()
    for item in downloads:
        cover = item.get("cover_img_src") or ""
        if cover and cover not in cover_seen:
            cover_seen.add(cover)
            covers.append({"img_src": cover, "kind": "image"})

    remove_srcs = [src for src in (manifest.get("remove") or []) if src]
    inventory = {
        row.get("content_src")
        for row in (manifest.get("inventory") or [])
        if isinstance(row, dict) and row.get("content_src")
    }
    remaining = (inventory - set(remove_srcs)) | {item["content_src"] for item in downloads}
    delete_paths = list(remove_srcs)
    shows_touched = set()
    for src in remove_srcs:
        ep = (catalog.get("content_by_src") or {}).get(src) or {}
        if ep.get("show_id") is not None:
            shows_touched.add(ep["show_id"])
        elif ep.get("kind") in ("movie", "book") and ep.get("img_src"):
            if ep["img_src"] not in delete_paths:
                delete_paths.append(ep["img_src"])
    for show_id in shows_touched:
        show = catalog["shows"].get(show_id)
        if not show:
            continue
        still = [
            ep.get("content_src")
            for ep in _episodes_for_show(catalog, show_id)
            if ep.get("content_src") in remaining
        ]
        cover = show.get("img_src") or ""
        if not still and cover and cover not in delete_paths:
            delete_paths.append(cover)

    return {"download": downloads, "covers": covers, "delete": delete_paths}


def unlink_media_file(path):
    """Delete one local media file. No-op unless this process is CLIENT."""
    if current_system_mode() != SystemMode.CLIENT:
        return False
    target = pathlib.Path(path)
    if target.exists():
        target.unlink()
    return True


def delete_relative(rel, media_dirs):
    """Unlink rel under a media root. Refuses paths outside those roots."""
    from app.utils.content_transfer import _path_is_under_media_roots

    dest = destination_for(rel, media_dirs)
    if dest is None:
        return False
    if not _path_is_under_media_roots(dest, media_dirs):
        return False
    if not dest.exists():
        return True
    return unlink_media_file(dest)


def destination_for(rel, media_dirs):
    if not rel or not media_dirs:
        return None
    rel_path = pathlib.PurePosixPath(str(rel).lstrip("/"))
    if rel_path.is_absolute() or ".." in rel_path.parts:
        return None
    from app.utils.content_transfer import _path_is_under_media_roots

    for media_directory in media_dirs:
        root = media_directory.get("content_src")
        if not root:
            continue
        dest = (pathlib.Path(root) / rel_path).resolve()
        if _path_is_under_media_roots(dest, media_dirs):
            return dest
    return None


def local_inventory(db):
    rows = db.get_all_content_paths() or []
    return [{"content_src": row.get("content_src")} for row in rows if row.get("content_src")]


def server_tree(catalog):
    shows = []
    for show in catalog["shows"].values():
        seasons = []
        for season in show["seasons"]:
            if season.get("direct"):
                continue
            seasons.append(
                {
                    "kind": "season",
                    "container_id": season.get("container_id"),
                    "title": season.get("title"),
                    "img_src": show.get("img_src") or "",
                    "img_url": show.get("img_url") or "",
                    "episodes": [
                        {
                            "kind": "episode",
                            "content_src": ep.get("content_src"),
                            "title": ep.get("title"),
                            "img_src": show.get("img_src") or "",
                            "img_url": show.get("img_url") or "",
                        }
                        for ep in season["episodes"]
                    ],
                }
            )
        shows.append(
            {
                "kind": "show",
                "container_id": show.get("container_id"),
                "title": show.get("title"),
                "img_src": show.get("img_src") or "",
                "img_url": show.get("img_url") or "",
                "seasons": seasons,
            }
        )
    return {"shows": shows, "movies": catalog["movies"], "books": catalog["books"]}


def client_tree(catalog, inventory):
    wanted = {
        row.get("content_src")
        for row in (inventory or [])
        if isinstance(row, dict) and row.get("content_src")
    }
    tree = server_tree(catalog)
    known = set()

    def keep_episodes(episodes):
        kept = []
        for ep in episodes:
            if ep.get("content_src") in wanted:
                kept.append(ep)
                known.add(ep.get("content_src"))
        return kept

    shows = []
    for show in tree["shows"]:
        seasons = []
        for season in show["seasons"]:
            episodes = keep_episodes(season["episodes"])
            if episodes:
                seasons.append({**season, "episodes": episodes})
        if seasons:
            shows.append({**show, "seasons": seasons})
    movies = [row for row in tree["movies"] if row.get("content_src") in wanted]
    books = [row for row in tree["books"] if row.get("content_src") in wanted]
    for row in movies + books:
        known.add(row.get("content_src"))
    other = [{"content_src": src, "title": src, "kind": "other"} for src in sorted(wanted - known)]
    return {"shows": shows, "movies": movies, "books": books, "other": other}
