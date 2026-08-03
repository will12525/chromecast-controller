/* Phase 4: app_main.js — plain global script (no bundler). */
/* global playerUpdateSeekSelector, playerWireControlButtons, playerBindScrubber */

async function updateSeekSelector() {
    // Unified Local + Cast scrubber (player_controls.js)
    if (typeof playerUpdateSeekSelector === "function") {
        await playerUpdateSeekSelector();
        return;
    }
}

async function setNavbarLinks() {
    var scan_media_button = document.getElementById("scan_media_button");
    var editor_button = document.getElementById("editor_button");
    var table_button = document.getElementById("table_button");

    var url = "/get_media_content_types";
    let response = await fetch(url);

    if (!response.ok) {
        throw new Error("HTTP status setNavbarLinks: " + response.status);
    } else {
        let response_data = await response.json();
        if (editor_button !== null && response_data["editor"] !== undefined)
        {
            editor_button.setAttribute('href', response_data["editor"]);
            editor_button.hidden = false;
        }
        if (table_button !== null && response_data["table_url"] !== undefined)
        {
            table_button.setAttribute('href', response_data["table_url"]);
            table_button.hidden = false;
        }
        if (scan_media_button !== null)
        {
            scan_media_button.addEventListener("click", scan_media_directories.bind(null));
        }
    }
}

async function setMediaControlButtons() {
    if (typeof playerWireControlButtons === "function") {
        await playerWireControlButtons();
        return;
    }
    // Fallback: cast-only (legacy)
    var url = "/get_chromecast_controls";
    let response = await fetch(url);
    if (!response.ok) {
        throw new Error("HTTP status setMediaControlButtons: " + response.status);
    }
    let response_data = await response.json();
    for (const [key, value] of Object.entries(response_data["chromecast_controls"])) {
        button_element = document.getElementById(key + "_media_button");
        if (button_element !== null) {
            button_element.addEventListener("click", chromecast_command.bind(null, value));
        }
    }
}

function setup_media_page() {
    var tag_list_group = document.getElementById('tag_list_group');
    if (tag_list_group !== null)
    {
        tag_list_group.addEventListener('change', (event) => {
            if (event.target.type === 'checkbox') {
                query_db_get_all_filters(event)
            }
        });
    }
    var modal_metadata_save = document.getElementById("modal_metadata_save");
    if (modal_metadata_save !== null)
    {
        modal_metadata_save.addEventListener('click', modal_metadata_save_click_handler);
    }
    const librarySearch = document.getElementById("library_search");
    if (librarySearch) {
        librarySearch.addEventListener("input", onLibrarySearchInput);
    }
    const shortcuts = document.getElementById("library_shortcuts");
    if (shortcuts) {
        shortcuts.querySelectorAll("[data-library]").forEach((btn) => {
            btn.addEventListener("click", () => load_library(btn.dataset.library));
        });
    }
    const shuffleBtn = document.getElementById("shuffle_play_button");
    if (shuffleBtn) {
        shuffleBtn.addEventListener("click", shuffle_library_play);
    }
    const navHome = document.getElementById("nav_home");
    if (navHome) {
        navHome.addEventListener("click", (e) => {
            if (new URL(window.location.href).pathname === "/" || new URL(window.location.href).pathname === "") {
                e.preventDefault();
                load_library_home();
            }
        });
    }
    ["tv", "movies", "books"].forEach((key) => {
        const el = document.getElementById("nav_library_" + key);
        if (el) {
            el.addEventListener("click", (e) => {
                e.preventDefault();
                // If on table page, still use query path
                load_library(key);
            });
        }
    });

    const pathname = new URL(window.location.href).pathname;
    if (pathname === "/table") {
        load_tv_shows();
    } else {
        load_library_home();
    }
    get_tag_list().then(tagTitles => {
        createTagElements(tagTitles)
    });
}

function setup_nav_bars() {
    var chromecast_menu = document.getElementById("chromecast_menu");
    if (chromecast_menu !== null)
    {
        chromecast_menu.addEventListener("click", getChromecastList);
    }
    // Disconnect / Local are re-bound when the cast menu is rebuilt
    if (typeof setupPlayModeSelector === "function") {
        setupPlayModeSelector();
    }
    getChromecastList();
    setNavbarLinks();
    setMediaControlButtons();
    if (typeof playerBindScrubber === "function") {
        playerBindScrubber();
    }
    setInterval(updateSeekSelector, 1000);
}

document.addEventListener("DOMContentLoaded", function(event){
    setup_nav_bars()
    if (document.getElementById("mediaContentSelectDiv") !== null)
    {
        pathname = new URL(window.location.href).pathname
        if (pathname == "/table") {
            document.getElementById("content_editor_card").hidden = false;
            const dropdownMenu = document.getElementById('add_tag_list_group_dropdown');
            const apply_tag_button = document.getElementById('apply_tag');
            const remove_tag_button = document.getElementById('remove_tag');
            dropdownMenu.addEventListener('click', (event) => {
                if (event.target.tagName === 'A') {
                    document.getElementById('add_tag_list_group_title').innerHTML = event.target.textContent
                }
            });
            apply_tag_button.addEventListener('click', () => {
                const tag_title = document.getElementById('add_tag_list_group_title').innerHTML;
                const checkedRows = Array.from(document.querySelectorAll('input[type="checkbox"]:checked')).map(checkbox => {
                    const row = checkbox.closest('tr');
                    if (row) {
                        const rowData = {
                            content_id: row.hasAttribute('data-row-content_id') ? row.getAttribute('data-row-content_id') : null,
                            container_id: row.getAttribute('data-row-container_id') ? row.getAttribute('data-row-container_id') : null,
                            tag_title: tag_title
                        }
                        add_tag_to_content(rowData)
                    }
                });
            });
            remove_tag_button.addEventListener('click', () => {
                const tag_title = document.getElementById('add_tag_list_group_title').innerHTML;
                const checkedRows = Array.from(document.querySelectorAll('input[type="checkbox"]:checked')).map(checkbox => {
                    const row = checkbox.closest('tr');
                    if (row) {
                        const rowData = {
                            content_id: row.hasAttribute('data-row-content_id') ? row.getAttribute('data-row-content_id') : null,
                            container_id: row.getAttribute('data-row-container_id') ? row.getAttribute('data-row-container_id') : null,
                            tag_title: tag_title
                        }
                        remove_tag_from_content(rowData)
                    }
                });
            });
        }
        setup_media_page()
    }
    if(document.getElementById('local_video_player') !== null) {
        const localPlayer = document.getElementById('local_video_player');
        localPlayer.addEventListener('ended', () => {
            if (localPlayer.dataset.content_id) {
                // Force flush finished state so Continue Watching drops this item
                lastProgressPostAt = 0;
                const duration = localPlayer.duration || 0;
                postPlaybackProgress(
                    localPlayer.dataset.content_id,
                    duration > 0 ? duration : 1,
                    duration > 0 ? duration : 1
                );
            }
            // Pass video element so dataset (content_id / parent / tags) is available
            get_next_media({ target: localPlayer });
        });
        localPlayer.addEventListener('timeupdate', () => {
            if (!localPlayer.dataset.content_id) {
                return;
            }
            postPlaybackProgress(
                localPlayer.dataset.content_id,
                localPlayer.currentTime,
                localPlayer.duration
            );
        });
        localPlayer.addEventListener('pause', () => {
            if (!localPlayer.dataset.content_id) {
                return;
            }
            // Force flush on pause
            lastProgressPostAt = 0;
            postPlaybackProgress(
                localPlayer.dataset.content_id,
                localPlayer.currentTime,
                localPlayer.duration
            );
        });
    }

    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
});
