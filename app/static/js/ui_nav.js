/* Hash routes, nav solid on scroll, tag chips. */

let nfChipTagTitles = [];
let nfApplyingHash = false;

function nfSetHash(path) {
    const next = "#" + (path.charAt(0) === "/" ? path : "/" + path);
    if (location.hash === next) {
        return;
    }
    nfApplyingHash = true;
    location.hash = next;
    setTimeout(() => {
        nfApplyingHash = false;
    }, 0);
}

function nfParseHash() {
    const raw = (location.hash || "#/").replace(/^#/, "") || "/";
    const qIndex = raw.indexOf("?");
    const path = qIndex >= 0 ? raw.slice(0, qIndex) : raw;
    const query = qIndex >= 0 ? raw.slice(qIndex + 1) : "";
    const parts = path.split("/").filter(Boolean);
    const params = new URLSearchParams(query);
    return { parts, params };
}

async function nfApplyRoute() {
    if (isTablePage()) {
        return;
    }
    const { parts, params } = nfParseHash();
    const head = parts[0] || "";
    if (!head) {
        await load_library_home();
        return;
    }
    if (head === "tv" || head === "movies" || head === "books") {
        load_library(head);
        return;
    }
    if (head === "search") {
        const q = params.get("q") || "";
        const searchEl = document.getElementById("library_search");
        if (searchEl && searchEl.value !== q) {
            searchEl.value = q;
        }
        if (q) {
            onLibrarySearchInput();
        } else {
            await load_library_home();
        }
        return;
    }
    if (head === "title") {
        const code = parts[1] || "";
        const kind = code.charAt(0) === "c" ? "container" : "content";
        const id = code.slice(1);
        if (id && typeof openTitleOverlay === "function") {
            await openTitleOverlay(kind, id, { skipHash: true });
        }
        return;
    }
    if (head === "play") {
        if (typeof openPlayerOverlay === "function") {
            openPlayerOverlay();
        }
        return;
    }
    await load_library_home();
}

function nfOnScrollNav() {
    const nav = document.querySelector(".nf-topnav");
    if (!nav) {
        return;
    }
    nav.classList.toggle("nf-nav-solid", window.scrollY > 24);
}

function nfSelectedChipTags() {
    const row = document.getElementById("library_chip_row");
    if (!row) {
        return [];
    }
    return Array.from(row.querySelectorAll(".nf-chip.active")).map((el) => el.dataset.tag);
}

function nfShowChipRow(show) {
    const row = document.getElementById("library_chip_row");
    if (!row) {
        return;
    }
    row.hidden = !show;
}

function nfIsTypeTag(tag) {
    const values = Object.values(LIBRARY_TAG_MAP || {});
    return values.indexOf(tag) >= 0;
}

function nfRenderChips(tagTitles) {
    nfChipTagTitles = tagTitles || [];
    const row = document.getElementById("library_chip_row");
    const hiddenList = document.getElementById("tag_list_group");
    if (hiddenList && typeof createTagElements === "function") {
        createTagElements(nfChipTagTitles);
    }
    if (!row) {
        return;
    }
    row.innerHTML = "";
    nfChipTagTitles.forEach((tag) => {
        if (nfIsTypeTag(tag)) {
            return;
        }
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "nf-chip";
        btn.dataset.tag = tag;
        btn.textContent = tag;
        btn.addEventListener("click", () => {
            btn.classList.toggle("active");
            const checkbox = document.getElementById("tag_checkbox_" + tag);
            if (checkbox) {
                checkbox.checked = btn.classList.contains("active");
            }
            if (currentLibraryKey) {
                load_library(currentLibraryKey);
            } else if (typeof query_db_get_all_filters === "function") {
                query_db_get_all_filters();
            }
        });
        row.appendChild(btn);
    });
}

function setupNfNav() {
    window.addEventListener("scroll", nfOnScrollNav, { passive: true });
    nfOnScrollNav();
    window.addEventListener("hashchange", () => {
        if (nfApplyingHash) {
            return;
        }
        nfApplyRoute();
    });
    ["tv", "movies", "books"].forEach((key) => {
        const el = document.getElementById("nav_library_" + key);
        if (!el) {
            return;
        }
        el.addEventListener("click", (e) => {
            e.preventDefault();
            nfSetHash("/" + key);
            load_library(key);
        });
    });
    const navHome = document.getElementById("nav_home");
    if (navHome) {
        navHome.addEventListener("click", (e) => {
            const path = new URL(window.location.href).pathname;
            if (path === "/" || path === "") {
                e.preventDefault();
                nfSetHash("/");
                load_library_home();
            }
        });
    }
}
