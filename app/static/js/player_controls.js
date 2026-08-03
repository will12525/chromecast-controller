/* Phase streaming: unified PlayerController for Local HTML5 + Chromecast(s). */
/* global postPlaybackProgress, lastProgressPostAt, chromecast_command, set_media_runtime */

/** @type {'local'|'all'|'device'} */
let playerStreamMode = "local";
/** @type {string|null} */
let playerActiveUuid = null;
/** @type {Array<{uuid:string,name:string}>} */
let playerConnectedDevices = [];
/** Scrubber is being dragged — pause poll overwrites */
let playerScrubActive = false;

const PLAYER_CMD = {
    REWIND: "CMD_REWIND",
    REWIND_15: "CMD_REWIND_15",
    PLAY: "CMD_PLAY",
    PAUSE: "CMD_PAUSE",
    SKIP_15: "CMD_SKIP_15",
    SKIP: "CMD_SKIP",
    STOP: "CMD_STOP",
};

function playerIsLocal() {
    return playerStreamMode === "local" || !playerConnectedDevices.length;
}

function playerGetVideo() {
    return document.getElementById("local_video_player");
}

function playerUpdateStatusChip() {
    const el = document.getElementById("connected_chromecast_id");
    if (!el) {
        return;
    }
    if (playerStreamMode === "local" || !playerConnectedDevices.length) {
        el.innerHTML = "Local";
        return;
    }
    if (playerStreamMode === "all") {
        const n = playerConnectedDevices.length;
        el.innerHTML = n > 1 ? `All (${n})` : (playerConnectedDevices[0].name || "Cast");
        return;
    }
    const match = playerConnectedDevices.find((d) => d.uuid === playerActiveUuid);
    el.innerHTML = (match && match.name) || playerActiveUuid || "Cast";
}

function playerApplyStreamState(state) {
    if (!state) {
        return;
    }
    if (state.stream_mode) {
        playerStreamMode = state.stream_mode;
    }
    if (state.active_device_id !== undefined) {
        playerActiveUuid = state.active_device_id;
    }
    if (Array.isArray(state.connected_devices)) {
        playerConnectedDevices = state.connected_devices;
    }
    playerUpdateStatusChip();
}

async function playerSetStreamMode(mode, chromecastId) {
    const body = { mode: mode };
    if (chromecastId) {
        body.chromecast_id = chromecastId;
    }
    const response = await fetch("/set_stream_mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!response.ok) {
        throw new Error("HTTP status set_stream_mode: " + response.status);
    }
    const data = await response.json();
    playerApplyStreamState(data);
    if (mode === "local") {
        const video = playerGetVideo();
        if (video) {
            video.hidden = false;
        }
    } else {
        const video = playerGetVideo();
        if (video) {
            video.pause();
            video.hidden = true;
        }
    }
    return data;
}

function playerLocalSeek(seconds) {
    const video = playerGetVideo();
    if (!video || video.readyState < 1) {
        return;
    }
    const dur = video.duration || 0;
    let t = seconds;
    if (dur > 0) {
        t = Math.max(0, Math.min(seconds, dur - 0.25));
    } else {
        t = Math.max(0, seconds);
    }
    try {
        video.currentTime = t;
    } catch (e) {
        console.warn("local seek failed", e);
    }
}

function playerLocalRelativeSeek(delta) {
    const video = playerGetVideo();
    if (!video) {
        return;
    }
    playerLocalSeek((video.currentTime || 0) + delta);
}

async function playerLocalNext() {
    const video = playerGetVideo();
    if (!video || !video.dataset.content_id) {
        return;
    }
    // Reuse get_next_media with synthetic event target = video dataset
    if (typeof get_next_media === "function") {
        await get_next_media({ target: video });
    }
}

async function playerLocalPrevious() {
    // No dedicated previous API for local — seek to 0
    playerLocalSeek(0);
}

async function playerCommand(cmdNameOrValue, enumValue) {
    // Accept either CMD_* name or numeric enum value from /get_chromecast_controls
    const name = typeof cmdNameOrValue === "string" && cmdNameOrValue.indexOf("CMD_") === 0
        ? cmdNameOrValue
        : null;

    if (playerIsLocal()) {
        const video = playerGetVideo();
        if (!video) {
            return;
        }
        const key = name || _playerCmdNameFromValue(enumValue);
        switch (key) {
            case "CMD_PLAY":
                video.hidden = false;
                try {
                    await video.play();
                } catch (e) {
                    console.warn("local play failed", e);
                }
                break;
            case "CMD_PAUSE":
                video.pause();
                break;
            case "CMD_STOP":
                video.pause();
                try {
                    video.currentTime = 0;
                } catch (e) { /* ignore */ }
                break;
            case "CMD_REWIND_15":
                playerLocalRelativeSeek(-15);
                break;
            case "CMD_SKIP_15":
                playerLocalRelativeSeek(15);
                break;
            case "CMD_REWIND":
                if ((video.currentTime || 0) <= 30) {
                    await playerLocalPrevious();
                } else {
                    playerLocalSeek(0);
                }
                break;
            case "CMD_SKIP":
            case "CMD_PLAY_NEXT":
                await playerLocalNext();
                break;
            case "CMD_PLAY_PREV":
                await playerLocalPrevious();
                break;
            default:
                break;
        }
        return;
    }

    // Cast path — server fans out by stream_mode
    const value = enumValue !== undefined && enumValue !== null ? enumValue : cmdNameOrValue;
    await chromecast_command(value);
}

function _playerCmdNameFromValue(value) {
    // Populated when buttons are wired (map value -> name)
    if (window._playerCmdValueToName && window._playerCmdValueToName[value] !== undefined) {
        return window._playerCmdValueToName[value];
    }
    return null;
}

async function playerSeek(seconds) {
    if (playerIsLocal()) {
        playerLocalSeek(parseFloat(seconds) || 0);
        return;
    }
    await set_media_runtime({ value: seconds });
}

async function playerGetStatus() {
    if (playerIsLocal()) {
        const video = playerGetVideo();
        if (!video || video.hidden || !video.dataset.content_id) {
            return null;
        }
        return {
            media_runtime: video.currentTime || 0,
            media_duration: video.duration || 0,
            media_title: (document.getElementById("content_title") || {}).innerHTML || "",
            content_id: video.dataset.content_id,
            parent_container_id: video.dataset.parent_container_id,
        };
    }
    try {
        const response = await fetch("/get_current_media_runtime");
        if (!response.ok) {
            return null;
        }
        return await response.json();
    } catch (e) {
        console.error(e);
        return null;
    }
}

async function playerUpdateSeekSelector() {
    if (playerScrubActive) {
        return;
    }
    const mediaTimeInputId = document.getElementById("mediaTimeInputId");
    if (!mediaTimeInputId) {
        return;
    }
    if (document.activeElement === mediaTimeInputId) {
        return;
    }
    const response_data = await playerGetStatus();
    if (!response_data || response_data.media_runtime == null) {
        return;
    }
    const media_runtime = response_data.media_runtime.toString().toHHMMSS();
    mediaTimeInputId.max = response_data.media_duration || 0;
    mediaTimeInputId.value = response_data.media_runtime;
    mediaTimeInputId.title = media_runtime;
    const mediaTimeOutputId = document.getElementById("mediaTimeOutputId");
    if (mediaTimeOutputId) {
        mediaTimeOutputId.value =
            media_runtime + "  " + (response_data.media_title || "");
    }
    if (response_data.content_id && response_data.media_runtime != null) {
        postPlaybackProgress(
            response_data.content_id,
            response_data.media_runtime,
            response_data.media_duration
        );
    }
    if (response_data.play_mode && typeof acknowledgePlayMode === "function") {
        acknowledgePlayMode(response_data.play_mode);
    }
}

function playerBindScrubber() {
    const range = document.getElementById("mediaTimeInputId");
    if (!range || range.dataset.playerBound) {
        return;
    }
    range.dataset.playerBound = "1";
    const commit = () => {
        playerScrubActive = false;
        playerSeek(range.value);
        try {
            range.blur();
        } catch (e) { /* ignore */ }
    };
    range.addEventListener("pointerdown", () => {
        playerScrubActive = true;
    });
    range.addEventListener("touchstart", () => {
        playerScrubActive = true;
    }, { passive: true });
    range.addEventListener("pointerup", commit);
    range.addEventListener("touchend", commit);
    range.addEventListener("change", commit);
    // Keep legacy mouse path
    range.addEventListener("mouseup", commit);
}

async function playerWireControlButtons() {
    const response = await fetch("/get_chromecast_controls");
    if (!response.ok) {
        throw new Error("HTTP status get_chromecast_controls: " + response.status);
    }
    const response_data = await response.json();
    window._playerCmdValueToName = {};
    for (const [key, value] of Object.entries(response_data.chromecast_controls || {})) {
        window._playerCmdValueToName[value] = key;
        const button_element = document.getElementById(key + "_media_button");
        if (button_element !== null) {
            // Prefer next-episode tooltip on skip
            if (key === "CMD_SKIP") {
                button_element.setAttribute("title", "Next");
            } else if (key === "CMD_SKIP_15") {
                button_element.setAttribute("title", "+15s");
            } else if (key === "CMD_REWIND_15") {
                button_element.setAttribute("title", "−15s");
            }
            button_element.addEventListener("click", () => playerCommand(key, value));
        }
    }
}
