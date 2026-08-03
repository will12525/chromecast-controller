"""Canonical play_mode values and resolution for cast / local auto-advance."""
from __future__ import annotations

from typing import Any, Mapping, Optional

# Canonical modes
PLAY_MODE_SEQUENTIAL = "sequential"
PLAY_MODE_REVERSE = "reverse"
PLAY_MODE_RANDOM_TAG = "random_tag"
PLAY_MODE_RANDOM_CONTAINER = "random_container"
PLAY_MODE_SINGLE = "single"

# Legacy alias used in older clients / metadata
PLAY_MODE_LEGACY_TAG = "play_random_content_with_tag"

ALL_PLAY_MODES = (
    PLAY_MODE_SEQUENTIAL,
    PLAY_MODE_REVERSE,
    PLAY_MODE_RANDOM_TAG,
    PLAY_MODE_RANDOM_CONTAINER,
    PLAY_MODE_SINGLE,
)

PLAY_MODE_LABELS = {
    PLAY_MODE_SEQUENTIAL: "Sequential",
    PLAY_MODE_REVERSE: "Reverse",
    PLAY_MODE_RANDOM_TAG: "Tag random",
    PLAY_MODE_RANDOM_CONTAINER: "Container random",
    PLAY_MODE_SINGLE: "Single",
}


def normalize_play_mode(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if text in (PLAY_MODE_LEGACY_TAG, "tag_random", "random-tag"):
        return PLAY_MODE_RANDOM_TAG
    if text in ("seq", "forward", "next"):
        return PLAY_MODE_SEQUENTIAL
    if text in ("rev", "backwards", "backward"):
        return PLAY_MODE_REVERSE
    if text in ALL_PLAY_MODES:
        return text
    return None


def resolve_play_mode(request: Mapping[str, Any]) -> str:
    """
    Resolve effective play_mode for a play/next request.

    Order:
    1. Explicit play_mode on request
    2. TV episode start (parent_container_id set) → sequential
    3. tag_list non-empty → random_tag
    4. single
    """
    explicit = normalize_play_mode(request.get("play_mode"))
    if explicit:
        return explicit

    parent = request.get("parent_container_id")
    if parent is not None and parent != "" and str(parent).lower() != "null":
        return PLAY_MODE_SEQUENTIAL

    tags = request.get("tag_list") or []
    if isinstance(tags, str):
        tags = [tags]
    if tags:
        return PLAY_MODE_RANDOM_TAG

    return PLAY_MODE_SINGLE


def stamp_play_mode(
    media_metadata: dict,
    play_mode: str,
    request: Mapping[str, Any] | None = None,
) -> dict:
    """Attach durable play_mode (+ tag_list / parent) for cast metadata and API."""
    if not media_metadata:
        return media_metadata
    mode = normalize_play_mode(play_mode) or PLAY_MODE_SINGLE
    media_metadata["play_mode"] = mode
    req = request or {}
    if mode == PLAY_MODE_RANDOM_TAG:
        tags = req.get("tag_list") or media_metadata.get("tag_list") or []
        media_metadata["tag_list"] = tags
    parent = req.get("parent_container_id")
    if parent is not None and parent != "" and str(parent).lower() != "null":
        media_metadata["parent_container_id"] = parent
    return media_metadata


def restamp_from_session(
    media_info: Optional[dict], session_meta: Mapping[str, Any]
) -> Optional[dict]:
    """Copy durable mode/tags from current session onto next item metadata."""
    if not media_info:
        return media_info
    mode = normalize_play_mode(session_meta.get("play_mode")) or PLAY_MODE_SEQUENTIAL
    media_info["play_mode"] = mode
    if mode == PLAY_MODE_RANDOM_TAG:
        media_info["tag_list"] = (
            session_meta.get("tag_list") or media_info.get("tag_list") or []
        )
    if media_info.get("parent_container_id") is None and session_meta.get(
        "parent_container_id"
    ):
        if mode in (
            PLAY_MODE_SEQUENTIAL,
            PLAY_MODE_REVERSE,
            PLAY_MODE_RANDOM_CONTAINER,
        ):
            media_info["parent_container_id"] = session_meta.get("parent_container_id")
    return media_info
