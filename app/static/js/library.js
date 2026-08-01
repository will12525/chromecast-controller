/* Phase 4: library.js — plain global script (no bundler). */
async function load_container(container_id) {
    currentLibraryKey = null;
    let data = {
        "tag_list": [],
        "container_dict": {"container_id": container_id}
    };
    queryDB(data)
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
    const tag = LIBRARY_TAG_MAP[libraryKey] || libraryKey;
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
    // TV is container-first; movies/books are content-first. Pass both search fields.
    let data = {
        "tag_list": [tag],
        "container_txt_search": libraryKey === "tv" ? search : (search || null),
        "content_txt_search": libraryKey !== "tv" ? search : (search || null),
        "container_dict": {}
    };
    // For unified search inside a library, search both dimensions lightly
    if (search) {
        data.container_txt_search = search;
        data.content_txt_search = search;
    }
    queryDB(data);
}

async function generate_media_container_for_shelf(content_data, media_card_template) {
    const wrapper = document.createElement("div");
    wrapper.className = "library-shelf-card";
    wrapper.innerHTML = media_card_template;
    const cardRoot = wrapper.querySelector("#content_container") || wrapper.firstElementChild;
    const parentId = content_data.parent_container_id != null
        ? content_data.parent_container_id
        : null;

    if ("container_title" in content_data) {
        cardRoot.dataset.containerId = content_data.container_id || content_data.id;
        const nav = wrapper.querySelector("#content_navigator");
        nav.textContent = content_data.container_title;
        nav.setAttribute("href", "javascript:load_container(" + content_data.id + ")");
    } else if ("content_title" in content_data) {
        const contentId = content_data.content_id || content_data.id;
        cardRoot.dataset.contentId = contentId;
        if (parentId != null) {
            cardRoot.dataset.parentContainerId = parentId;
        }
        const nav = wrapper.querySelector("#content_navigator");
        nav.textContent = content_data.content_title;
        nav.setAttribute(
            "href",
            "javascript:play_media(" + contentId + ", " + (parentId != null ? parentId : "null") + ")"
        );
        // Play affordance on poster click
        const img = wrapper.querySelector("#content_img");
        if (img) {
            img.classList.add("library-poster-playable");
            img.title = "Play";
            img.addEventListener("click", (e) => {
                e.preventDefault();
                play_media(contentId, parentId);
            });
        }
        // Explicit play button in footer
        const footerActions = wrapper.querySelector(".card-footer .d-grid");
        if (footerActions) {
            const playBtn = document.createElement("button");
            playBtn.type = "button";
            playBtn.className = "btn btn-success me-md-2";
            playBtn.innerHTML = '<i class="bi-play-fill"></i>';
            playBtn.title = "Play";
            playBtn.addEventListener("click", () => play_media(contentId, parentId));
            footerActions.insertBefore(playBtn, footerActions.firstChild);
        }
    }
    if ("play_count" in content_data && content_data.play_count == 0) {
        wrapper.querySelector("#new_tag").hidden = false;
    }
    if ("user_tags" in content_data && content_data.user_tags) {
        wrapper.querySelector("#card_tags").textContent = "Tags: " + content_data.user_tags;
    }
    if ("content_index" in content_data && content_data.content_index !== "" && content_data.content_index != null) {
        wrapper.querySelector("#content_index").hidden = false;
        wrapper.querySelector("#content_index").textContent = "Index: " + content_data.content_index;
    }
    wrapper.querySelector("#card_description").textContent = content_data.description || "";
    if (content_data.img_src && content_data.img_url) {
        wrapper.querySelector("#content_img").src = content_data.img_url;
    }
    wrapper.querySelector("#content_img").dataset.img_src = content_data.img_src || "";

    // Progress bar for continue watching
    const pos = parseFloat(content_data.last_position) || 0;
    const dur = parseFloat(content_data.last_duration) || 0;
    if (pos > 0) {
        const pct = dur > 0 ? Math.min(100, (pos / dur) * 100) : 10;
        const barWrap = document.createElement("div");
        barWrap.className = "library-progress";
        const bar = document.createElement("div");
        bar.className = "library-progress-bar";
        bar.style.width = pct + "%";
        barWrap.appendChild(bar);
        const body = wrapper.querySelector(".card-body");
        if (body) {
            body.appendChild(barWrap);
        }
    }
    return wrapper;
}

function build_shelf_section(title, emptyMessage) {
    const section = document.createElement("div");
    section.className = "library-shelf col-md-12";
    const heading = document.createElement("div");
    heading.className = "library-shelf-title";
    heading.textContent = title;
    const row = document.createElement("div");
    row.className = "library-shelf-row";
    section.appendChild(heading);
    section.appendChild(row);
    section._row = row;
    section._emptyMessage = emptyMessage;
    return section;
}

async function render_library_home(homeData) {
    const card_res = await fetch("static/media_card.html");
    const media_card_template = await card_res.text();
    const fragment = document.createDocumentFragment();

    // Libraries shortcut shelf
    const libSection = build_shelf_section("Libraries", "No libraries configured");
    (homeData.libraries || []).forEach((lib) => {
        const tile = document.createElement("div");
        tile.className = "library-tile";
        tile.innerHTML =
            '<div class="card" style="background-color:Linen;"><div class="card-body">' +
            '<h5 class="card-title"></h5><p class="card-text text-muted library-count"></p></div></div>';
        tile.querySelector(".card-title").textContent = lib.title;
        tile.querySelector(".library-count").textContent = (lib.count || 0) + " items";
        tile.addEventListener("click", () => load_library(lib.key));
        libSection._row.appendChild(tile);
    });
    fragment.appendChild(libSection);

    const shelves = [
        {key: "continue_watching", title: "Continue Watching", empty: "Nothing in progress"},
        {key: "recently_added", title: "Recently Added", empty: "Library is empty — try Scan Media"},
        {key: "recently_played", title: "Recently Played", empty: "Nothing played yet"},
    ];

    for (const shelf of shelves) {
        const section = build_shelf_section(shelf.title, shelf.empty);
        const items = homeData[shelf.key] || [];
        if (!items.length) {
            const empty = document.createElement("div");
            empty.className = "library-empty";
            empty.textContent = shelf.empty;
            section._row.appendChild(empty);
        } else {
            for (const item of items) {
                section._row.appendChild(
                    await generate_media_container_for_shelf(item, media_card_template)
                );
            }
        }
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
    // activeKey: null = home, or tv|movies|books
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
    // Mirror active state on sidebar library shortcuts
    const shortcuts = document.getElementById("library_shortcuts");
    if (shortcuts) {
        shortcuts.querySelectorAll("[data-library]").forEach((btn) => {
            btn.classList.toggle("active", btn.dataset.library === activeKey);
        });
    }
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
            if (currentLibraryKey) {
                load_library(currentLibraryKey);
            } else {
                load_library_home();
            }
            return;
        }
        // Unified search across containers + content (and optional current tags)
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
        queryDB({
            tag_list: tags,
            container_txt_search: search,
            content_txt_search: search,
            container_dict: {},
        });
    }, 300);
}
