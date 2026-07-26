"""
Backwards-compatible facade for the former monolithic routes module.

Route handlers live in:
  - library_routes.py  — browse, play, scan, tags, pages
  - cast_routes.py     — Chromecast + local player
  - editor_routes.py   — MP4 splitter editor
  - transfer_routes.py — CLIENT/SERVER content transfer

Shared state (APIEndpoints, bh, system_mode) is in shared.py.
"""
# Re-export public symbols used by tests and callers (main_routes.APIEndpoints, …)
from app.routes.shared import (  # noqa: F401
    ALLOWED_EXTENSIONS,
    APIEndpoints,
    allowed_file,
    bh,
    build_main_content,
    main_bp,
    media_controller_button_dict,
    media_types,
    play_response_from_metadata,
    system_mode,
)

# Side-effect: register handlers on main_bp
from app.routes import cast_routes as cast_routes  # noqa: F401,E402
from app.routes import editor_routes as editor_routes  # noqa: F401,E402
from app.routes import library_routes as library_routes  # noqa: F401,E402
from app.routes import transfer_routes as transfer_routes  # noqa: F401,E402

# Alias kept for any code that imported the old helper name
_play_response_from_metadata = play_response_from_metadata
