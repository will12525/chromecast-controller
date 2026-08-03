/* Play mode selector: persist user choice, ack from server, stamp play payloads. */
const PLAY_MODE_STORAGE_KEY = "cc_play_mode";
const PLAY_MODE_VALUES = [
    "sequential",
    "reverse",
    "random_tag",
    "random_container",
    "single",
];
const PLAY_MODE_LABELS = {
    sequential: "Sequential",
    reverse: "Reverse",
    random_tag: "Tag random",
    random_container: "Container random",
    single: "Single",
};

/** Session mode last acknowledged by server (or user). */
let sessionPlayMode = null;

function normalizePlayModeClient(value) {
    if (!value) {
        return null;
    }
    const text = String(value).trim().toLowerCase();
    if (text === "play_random_content_with_tag" || text === "tag_random") {
        return "random_tag";
    }
    if (PLAY_MODE_VALUES.indexOf(text) >= 0) {
        return text;
    }
    return null;
}

function loadPersistedPlayMode() {
    try {
        return normalizePlayModeClient(localStorage.getItem(PLAY_MODE_STORAGE_KEY));
    } catch (e) {
        return null;
    }
}

function persistPlayMode(mode) {
    const m = normalizePlayModeClient(mode);
    if (!m) {
        return;
    }
    try {
        localStorage.setItem(PLAY_MODE_STORAGE_KEY, m);
    } catch (e) { /* ignore */ }
    sessionPlayMode = m;
    updatePlayModeSelectorUI(m);
}

/**
 * Effective mode for a play action.
 * Explicit user session preference wins; else sequential for TV parent, tag if tags, else single.
 * When starting a TV episode (parent set) without user having chosen reverse/random_container,
 * prefer sequential for that play (plan conflict rule) unless session is reverse.
 */
function resolveClientPlayMode(options) {
    const opts = options || {};
    const parentId = opts.parent_container_id;
    const tags = opts.tag_list || [];
    const userMode = sessionPlayMode || loadPersistedPlayMode();

    if (userMode) {
        // TV episode card: force sequential unless user picked reverse/container random/single
        if (
            parentId != null &&
            parentId !== "" &&
            parentId !== "null" &&
            (userMode === "random_tag" || !userMode)
        ) {
            return "sequential";
        }
        return userMode;
    }
    if (parentId != null && parentId !== "" && parentId !== "null") {
        return "sequential";
    }
    if (tags && tags.length) {
        return "random_tag";
    }
    return "single";
}

function acknowledgePlayMode(mode) {
    const m = normalizePlayModeClient(mode);
    if (!m) {
        return;
    }
    sessionPlayMode = m;
    updatePlayModeSelectorUI(m);
    // Do not overwrite localStorage on server ack of auto sequential unless user has no pref
    try {
        if (!localStorage.getItem(PLAY_MODE_STORAGE_KEY)) {
            localStorage.setItem(PLAY_MODE_STORAGE_KEY, m);
        }
    } catch (e) { /* ignore */ }
}

function updatePlayModeSelectorUI(mode) {
    const sel = document.getElementById("play_mode_select");
    if (!sel) {
        return;
    }
    const m = normalizePlayModeClient(mode) || loadPersistedPlayMode() || "sequential";
    if (sel.value !== m) {
        sel.value = m;
    }
    const chip = document.getElementById("play_mode_chip");
    if (chip) {
        chip.textContent = PLAY_MODE_LABELS[m] || m;
    }
}

function setupPlayModeSelector() {
    const sel = document.getElementById("play_mode_select");
    if (!sel) {
        sessionPlayMode = loadPersistedPlayMode();
        return;
    }
    // Populate options once
    if (!sel.dataset.ready) {
        sel.innerHTML = "";
        PLAY_MODE_VALUES.forEach((value) => {
            const opt = document.createElement("option");
            opt.value = value;
            opt.textContent = PLAY_MODE_LABELS[value] || value;
            sel.appendChild(opt);
        });
        sel.dataset.ready = "1";
    }
    const initial = loadPersistedPlayMode() || "sequential";
    sessionPlayMode = initial;
    sel.value = initial;
    updatePlayModeSelectorUI(initial);
    sel.addEventListener("change", () => {
        persistPlayMode(sel.value);
    });
}
