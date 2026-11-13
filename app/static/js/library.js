/* Phase 4 + Netflix-like home: shelves, billboard, poster tiles. */
let nfCardTemplatePromise = null;

function isTablePage() {
    return new URL(window.location.href).pathname === "/table";
}

function nfCardTemplate() {
    if (!nfCardTemplatePromise) {
        nfCardTemplatePromise = fetch("static/nf_card.html").then((r) => r.text());
    }
    return nfCardTemplatePromise;
}

function nfItemKind(data) {
    if (data.kind === "container" || data.kind === "content") {
        return data.kind;
    }
    if ("container_title" in data && data.container_title != null) {
        return "container";
    }
    return "content";
}

function nfItemId(data) {
    if (nfItemKind(data) === "container") {
        return data.container_id || data.id;
    }
    return data.content_id || data.id;
}

function nfItemTitle(data) {
    return data.container_title || data.content_title || data.show_title || "";
}

async function load_container(container_id) {
    if (typeof openTitleOverlay === "function" && !isTablePage()) {
        openTitleOverlay("container", container_id);
        return;
    }
    currentLibraryKey = null;
    queryDB({
        tag_list: [],
        container_dict: { container_id: container_id },
    });
}

async function load_tv_shows() {
    load_library("tv");
}
async function load_movies() {
    load_library("movies");
}

function load_library(libraryKey) {
    currentLibraryKey = libraryKey;
    setActiveLibraryNav(libraryKey);
    const billboard = document.getElementById("billboard");
    if (billboard && !isTablePage()) {
        billboard.hidden = true;
        billboard.innerHTML = "";
    }
    if (typeof nfShowChipRow === "function") {
        nfShowChipRow(true);
    }
    const searchEl = document.getElementById("library_search");
    const search = searchEl ? searchEl.value.trim() : "";
    const containerSearch = document.getElementById("container_txt_search");
    const contentSearch = document.getElementById("content_txt_search");
    if (containerSearch) {
        containerSearch.value = search;
    }
    if (contentSearch) {
        contentSearch.value = search;
    }
    let data = {
        tag_list: [LIBRARY_TAG_MAP[libraryKey] || libraryKey],
        tag_match: "all",
        container_txt_search: libraryKey === "tv" ? search : (search || null),
        content_txt_search: libraryKey !== "tv" ? search : (search || null),
        container_dict: {},
    };
    if (search) {
        data.container_txt_search = search;
        data.content_txt_search = search;
    }
    const extra = typeof nfSelectedChipTags === "function" ? nfSelectedChipTags() : [];
    extra.forEach((tag) => {
        if (data.tag_list.indexOf(tag) < 0) {
            data.tag_list.push(tag);
        }
    });
    queryDB(data);
}

function nfProgressPct(data) {
    const pos = parseFloat(data.last_position) || 0;
    const dur = parseFloat(data.last_duration) || 0;
    if (pos <= 0) {
        return 0;
    }
    return dur > 0 ? Math.min(100, (pos / dur) * 100) : 10;
}

async function buildNfTile(content_data, options) {
    const opts = options || {};
    const html = await nfCardTemplate();
    const wrap = document.createElement("div");
    wrap.innerHTML = html.trim();
    const tile = wrap.firstElementChild;
    const kind = nfItemKind(content_data);
    const id = nfItemId(content_data);
    const parentId = content_data.parent_container_id != null
        ? content_data.parent_container_id
        : null;
    tile.dataset.kind = kind;
    tile.dataset.id = String(id);
    if (parentId != null) {
        tile.dataset.parentContainerId = String(parentId);
    }
    if (opts.wide) {
        tile.classList.add("nf-tile-wide");
    }
    const title = nfItemTitle(content_data);
    tile.querySelector(".nf-tile-title").textContent = title;
    const showTitle = content_data.show_title || content_data.tv_show_title || "";
    const sub = tile.querySelector(".nf-tile-sub");
    if (showTitle && showTitle !== title) {
        sub.textContent = showTitle;
    } else {
        sub.textContent = "";
    }
    const img = tile.querySelector(".nf-tile-img");
    img.alt = title;
    const art = typeof displayArt === "function" ? displayArt(content_data) : {
        src: content_data.img_url || "",
        imgSrc: content_data.img_src || "",
    };
    if (art.src) {
        img.src = art.src;
    }
    img.dataset.img_src = art.imgSrc || "";
    const pct = nfProgressPct(content_data);
    const progress = tile.querySelector(".nf-tile-progress");
    if (pct > 0) {
        progress.hidden = false;
        progress.querySelector(".nf-tile-progress-bar").style.width = pct + "%";
    }
    if (content_data.play_count == 0) {
        tile.querySelector(".nf-tile-new").hidden = false;
    }
    const playDirect = !!opts.playDirect && kind === "content";
    const playBtn = tile.querySelector(".nf-tile-play");
    if (playDirect) {
        playBtn.classList.add("visible");
        playBtn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            play_media(id, parentId);
        });
    } else {
        playBtn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (typeof openTitleOverlay === "function") {
                openTitleOverlay(kind, id);
            }
        });
    }
    tile.addEventListener("click", () => {
        if (playDirect) {
            play_media(id, parentId);
            return;
        }
        if (typeof openTitleOverlay === "function" && !isTablePage()) {
            openTitleOverlay(kind, id);
            return;
        }
        if (kind === "container") {
            load_container(id);
        } else {
            play_media(id, parentId);
        }
    });
    return tile;
}

function build_shelf_section(title, emptyMessage) {
    const section = document.createElement("div");
    section.className = "library-shelf";
    const heading = document.createElement("div");
    heading.className = "library-shelf-title";
    heading.textContent = title;
    const wrap = document.createElement("div");
    wrap.className = "nf-row-wrap";
    const row = document.createElement("div");
    row.className = "library-shelf-row";
    const left = document.createElement("button");
    left.type = "button";
    left.className = "nf-row-arrow left";
    left.setAttribute("aria-label", "Scroll left");
    left.textContent = "‹";
    const right = document.createElement("button");
    right.type = "button";
    right.className = "nf-row-arrow right";
    right.setAttribute("aria-label", "Scroll right");
    right.textContent = "›";
    left.addEventListener("click", () => {
        row.scrollBy({ left: -Math.max(240, row.clientWidth * 0.8), behavior: "smooth" });
    });
    right.addEventListener("click", () => {
        row.scrollBy({ left: Math.max(240, row.clientWidth * 0.8), behavior: "smooth" });
    });
    wrap.appendChild(left);
    wrap.appendChild(row);
    wrap.appendChild(right);
    section.appendChild(heading);
    section.appendChild(wrap);
    section._row = row;
    section._emptyMessage = emptyMessage;
    return section;
}

function pickBillboardItem(homeData) {
    const watching = homeData.continue_watching || [];
    const added = homeData.recently_added || [];
    const withArt = watching.find((item) => item.img_url) || added.find((item) => item.img_url);
    return withArt || watching[0] || added[0] || null;
}

function render_billboard(item) {
    const el = document.getElementById("billboard");
    if (!el) {
        return;
    }
    if (!item || isTablePage()) {
        el.hidden = true;
        el.innerHTML = "";
        return;
    }
    el.hidden = false;
    const kind = nfItemKind(item);
    const id = nfItemId(item);
    const title = nfItemTitle(item);
    const desc = item.description || "";
    const img = item.img_url || "";
    el.innerHTML =
        (img ? '<img class="nf-billboard-img" alt="">' : "") +
        '<div class="nf-billboard-fade"></div>' +
        '<div class="nf-billboard-copy">' +
        '<h1 class="nf-billboard-title"></h1>' +
        '<p class="nf-billboard-desc"></p>' +
        '<div><button type="button" class="nf-btn-play" id="billboard_play"></button>' +
        '<button type="button" class="nf-btn-info" id="billboard_info">More Info</button></div>' +
        "</div>";
    if (img) {
        const imgEl = el.querySelector(".nf-billboard-img");
        imgEl.src = img;
        imgEl.alt = title;
        imgEl.onerror = function () {
            apply_default_image(this);
        };
    }
    el.querySelector(".nf-billboard-title").textContent = title;
    el.querySelector(".nf-billboard-desc").textContent = desc;
    const playBtn = el.querySelector("#billboard_play");
    playBtn.textContent = typeof playTargetLabel === "function" ? playTargetLabel() : "Play";
    const parentId = item.parent_container_id != null ? item.parent_container_id : null;
    playBtn.addEventListener("click", () => {
        if (kind === "content") {
            play_media(id, parentId);
        } else if (typeof openTitleOverlay === "function") {
            openTitleOverlay(kind, id);
        }
    });
    el.querySelector("#billboard_info").addEventListener("click", () => {
        if (typeof openTitleOverlay === "function") {
            openTitleOverlay(kind, id);
        }
    });
}

async function fill_shelf_row(section, items, options) {
    const opts = options || {};
    if (!items.length) {
        const empty = document.createElement("div");
        empty.className = "library-empty";
        empty.textContent = section._emptyMessage || "";
        section._row.appendChild(empty);
        return;
    }
    for (const item of items) {
        section._row.appendChild(await buildNfTile(item, opts));
    }
}

async function render_library_home(homeData) {
    if (typeof nfShowChipRow === "function") {
        nfShowChipRow(false);
    }
    const fragment = document.createDocumentFragment();
    render_billboard(pickBillboardItem(homeData));

    const shelves = [
        { key: "continue_watching", title: "Continue Watching", empty: "Nothing in progress", playDirect: true, wide: true },
        { key: "recently_added", title: "Recently Added", empty: "Library is empty — try Scan Media" },
        { key: "recently_played", title: "Recently Played", empty: "Nothing played yet" },
    ];
    for (const shelf of shelves) {
        const section = build_shelf_section(shelf.title, shelf.empty);
        await fill_shelf_row(section, homeData[shelf.key] || [], {
            playDirect: !!shelf.playDirect,
            wide: !!shelf.wide,
        });
        fragment.appendChild(section);
    }
    for (const tagShelf of homeData.tag_shelves || []) {
        const section = build_shelf_section(tagShelf.tag, "No titles");
        await fill_shelf_row(section, tagShelf.items || [], {});
        fragment.appendChild(section);
    }

    const mainContent = document.getElementById("mediaContentSelectDiv");
    mainContent.innerHTML = "";
    mainContent.appendChild(fragment);
    const loading = document.getElementById("rainbow_loading_bar");
    if (loading) {
        loading.hidden = true;
    }
}

function setActiveLibraryNav(activeKey) {
    const navMap = {
        home: document.getElementById("nav_home"),
        tv: document.getElementById("nav_library_tv"),
        movies: document.getElementById("nav_library_movies"),
        books: document.getElementById("nav_library_books"),
    };
    Object.entries(navMap).forEach(([key, el]) => {
        if (!el) {
            return;
        }
        const isActive = (activeKey === null && key === "home") || key === activeKey;
        el.classList.toggle("active", isActive);
        if (isActive) {
            el.setAttribute("aria-current", "page");
        } else {
            el.removeAttribute("aria-current");
        }
    });
}

async function load_library_home() {
    currentLibraryKey = null;
    setActiveLibraryNav(null);
    const loading = document.getElementById("rainbow_loading_bar");
    if (loading) {
        loading.hidden = false;
    }
    try {
        const response = await fetch("/library/home");
        if (!response.ok) {
            throw new Error("HTTP status library home: " + response.status);
        }
        const homeData = await response.json();
        await render_library_home(homeData);
    } catch (error) {
        console.error(error);
        if (loading) {
            loading.hidden = true;
        }
    }
}

function onLibrarySearchInput() {
    clearTimeout(librarySearchDebounce);
    librarySearchDebounce = setTimeout(() => {
        const searchEl = document.getElementById("library_search");
        const search = searchEl ? searchEl.value.trim() : "";
        if (!search) {
            if (typeof nfSetHash === "function" && !isTablePage()) {
                if (currentLibraryKey) {
                    nfSetHash("/" + currentLibraryKey);
                } else {
                    nfSetHash("/");
                }
            }
            if (currentLibraryKey) {
                load_library(currentLibraryKey);
            } else {
                load_library_home();
            }
            return;
        }
        if (typeof nfSetHash === "function" && !isTablePage()) {
            nfSetHash("/search?q=" + encodeURIComponent(search));
        }
        const containerSearch = document.getElementById("container_txt_search");
        const contentSearch = document.getElementById("content_txt_search");
        if (containerSearch) {
            containerSearch.value = search;
        }
        if (contentSearch) {
            contentSearch.value = search;
        }
        const tagListEl = document.getElementById("tag_list_group");
        let tags = tagListEl ? get_selected_checkboxes(tagListEl) : [];
        if (currentLibraryKey && LIBRARY_TAG_MAP[currentLibraryKey]) {
            if (!tags.length) {
                tags = [LIBRARY_TAG_MAP[currentLibraryKey]];
            }
        }
        const extra = typeof nfSelectedChipTags === "function" ? nfSelectedChipTags() : [];
        extra.forEach((tag) => {
            if (tags.indexOf(tag) < 0) {
                tags.push(tag);
            }
        });
        queryDB({
            tag_list: tags,
            tag_match: tags.length ? "all" : undefined,
            container_txt_search: search,
            content_txt_search: search,
            container_dict: {},
        });
    }, 300);
}
