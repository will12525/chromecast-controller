/* Title overlay: GET /library/title, no metadata pencils. */

let titleOverlayPayload = null;
let titleOverlaySeasonEpisodes = [];

function playTargetLabel() {
    let target = "locally";
    if (typeof playerIsLocal === "function" && !playerIsLocal()) {
        const chip = document.getElementById("connected_chromecast_id");
        const name = chip ? chip.textContent.trim() : "";
        target = name && name !== "Local" ? name : "Cast";
    }
    return "Play on " + target;
}

function titleOverlayEl() {
    return document.getElementById("title_overlay");
}

function closeTitleOverlay(opts) {
    const overlay = titleOverlayEl();
    if (overlay) {
        overlay.hidden = true;
    }
    titleOverlayPayload = null;
    const skipHash = opts && opts.skipHash;
    if (!skipHash && typeof nfSetHash === "function" && !isTablePage()) {
        if (currentLibraryKey) {
            nfSetHash("/" + currentLibraryKey);
        } else {
            nfSetHash("/");
        }
    }
}

function titleHashFor(kind, id) {
    const prefix = kind === "container" ? "c" : "m";
    return "/title/" + prefix + id;
}

function bindTitleOverlayChrome() {
    const overlay = titleOverlayEl();
    if (!overlay || overlay.dataset.bound) {
        return;
    }
    overlay.dataset.bound = "1";
    overlay.querySelectorAll("[data-title-close]").forEach((el) => {
        el.addEventListener("click", () => closeTitleOverlay());
    });
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && overlay && !overlay.hidden) {
            closeTitleOverlay();
        }
    });
    const playBtn = document.getElementById("title_overlay_play");
    if (playBtn) {
        playBtn.addEventListener("click", () => playTitleOverlay());
    }
}

function playTitleContent(row) {
    if (!row || !row.id) {
        return;
    }
    const parent = row.parent_container_id != null ? row.parent_container_id : null;
    closeTitleOverlay({ skipHash: true });
    play_media(row.id, parent);
}

function playTitleOverlay() {
    const data = titleOverlayPayload;
    if (!data) {
        return;
    }
    if (data.kind === "content") {
        playTitleContent(data);
        return;
    }
    if (data.resume_content && data.resume_content.id) {
        playTitleContent(data.resume_content);
        return;
    }
    const firstEp = (data.episodes && data.episodes[0])
        || (titleOverlaySeasonEpisodes && titleOverlaySeasonEpisodes[0])
        || ((data.seasons || []).map((s) => (s.episodes || [])[0]).find(Boolean));
    if (firstEp) {
        playTitleContent(firstEp);
    }
}

function renderTitleEpisodes(episodes) {
    const host = document.getElementById("title_overlay_episodes");
    if (!host) {
        return;
    }
    host.innerHTML = "";
    (episodes || []).forEach((ep, index) => {
        const row = document.createElement("div");
        row.className = "nf-episode";
        const n = document.createElement("div");
        n.textContent = String(index + 1);
        const body = document.createElement("div");
        const title = document.createElement("div");
        title.textContent = ep.content_title || ep.container_title || "Episode";
        const desc = document.createElement("div");
        desc.className = "text-secondary small";
        desc.textContent = ep.description || "";
        body.appendChild(title);
        body.appendChild(desc);
        row.appendChild(n);
        row.appendChild(body);
        row.addEventListener("click", () => playTitleContent(ep));
        host.appendChild(row);
    });
}

function renderTitleSeasons(data) {
    const host = document.getElementById("title_overlay_seasons");
    if (!host) {
        return;
    }
    host.innerHTML = "";
    const seasons = data.seasons || [];
    if (!seasons.length) {
        titleOverlaySeasonEpisodes = data.episodes || [];
        renderTitleEpisodes(titleOverlaySeasonEpisodes);
        return;
    }
    seasons.forEach((season, idx) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "nf-chip" + (idx === 0 ? " active" : "");
        btn.textContent = season.container_title || ("Season " + (idx + 1));
        btn.addEventListener("click", () => {
            host.querySelectorAll(".nf-chip").forEach((c) => c.classList.remove("active"));
            btn.classList.add("active");
            titleOverlaySeasonEpisodes = season.episodes || [];
            renderTitleEpisodes(titleOverlaySeasonEpisodes);
        });
        host.appendChild(btn);
    });
    titleOverlaySeasonEpisodes = seasons[0].episodes || [];
    renderTitleEpisodes(titleOverlaySeasonEpisodes);
}

function renderTitleOverlay(data) {
    titleOverlayPayload = data;
    const overlay = titleOverlayEl();
    if (!overlay) {
        return;
    }
    const name = data.container_title || data.content_title || "";
    document.getElementById("title_overlay_name").textContent = name;
    document.getElementById("title_overlay_desc").textContent = data.description || "";
    const img = document.getElementById("title_overlay_img");
    img.alt = name;
    if (data.img_url) {
        img.src = data.img_url;
    } else {
        img.removeAttribute("src");
        apply_default_image(img);
    }
    const tagsHost = document.getElementById("title_overlay_tags");
    tagsHost.innerHTML = "";
    const tags = (data.user_tags || "").split(",").map((t) => t.trim()).filter(Boolean);
    tags.forEach((tag) => {
        const chip = document.createElement("span");
        chip.className = "nf-chip";
        chip.textContent = tag;
        tagsHost.appendChild(chip);
    });
    const playBtn = document.getElementById("title_overlay_play");
    let label = playTargetLabel();
    if (data.kind === "container" && data.resume_content) {
        label = "Resume " + (typeof playTargetLabel === "function" ? playTargetLabel().replace(/^Play /, "") : "");
        if (!label.startsWith("Resume")) {
            label = "Resume";
        }
    }
    playBtn.textContent = data.kind === "container" && data.resume_content
        ? ("Resume on " + playTargetLabel().replace(/^Play on /, ""))
        : playTargetLabel();
    renderTitleSeasons(data);
    overlay.hidden = false;
}

async function openTitleOverlay(kind, id, opts) {
    bindTitleOverlayChrome();
    const skipHash = opts && opts.skipHash;
    try {
        const response = await fetch(
            "/library/title?kind=" + encodeURIComponent(kind) + "&id=" + encodeURIComponent(id)
        );
        if (!response.ok) {
            throw new Error("HTTP status library title: " + response.status);
        }
        const data = await response.json();
        renderTitleOverlay(data);
        if (!skipHash && typeof nfSetHash === "function" && !isTablePage()) {
            nfSetHash(titleHashFor(kind, id));
        }
    } catch (e) {
        console.error(e);
    }
}
