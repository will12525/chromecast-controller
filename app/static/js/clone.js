/* Clone manifest editor. Loaded only on /clone. */
let cloneCatalog = {shows: [], movies: [], books: []};
let cloneClientTree = {shows: [], movies: [], books: [], other: []};
let cloneState = {selections: [], exclude: [], remove: []};

function cloneToast(message, isError) {
    const toast = document.getElementById("clone_toast");
    if (!toast) {
        return;
    }
    toast.hidden = false;
    toast.className = "alert py-2 " + (isError ? "alert-danger" : "alert-success");
    toast.textContent = message;
}

function clonePoster(node) {
    const src = (node && (node.img_url || node.show_img_url)) || "";
    if (!src) {
        return "";
    }
    return '<img alt="" src="' + src.replace(/"/g, "") + '" width="36" height="36" class="me-2 rounded">';
}

function cloneCheckedAttr(on) {
    return on ? " checked" : "";
}

async function cloneLoadClients() {
    const response = await fetch("/clone/clients");
    if (!response.ok) {
        throw new Error("clients " + response.status);
    }
    const data = await response.json();
    const select = document.getElementById("clone_client");
    select.innerHTML = "";
    const active = document.createElement("optgroup");
    active.label = "Active";
    const historical = document.createElement("optgroup");
    historical.label = "Historical";
    (data.clients || []).forEach((client) => {
        const option = document.createElement("option");
        option.value = client.client_id;
        option.textContent = client.display_name || client.client_id;
        (client.active ? active : historical).appendChild(option);
    });
    if (!active.children.length) {
        const empty = document.createElement("option");
        empty.value = "";
        empty.textContent = "No active clients";
        empty.disabled = true;
        active.appendChild(empty);
    }
    if (!historical.children.length) {
        const empty = document.createElement("option");
        empty.value = "";
        empty.textContent = "No earlier clients";
        empty.disabled = true;
        historical.appendChild(empty);
    }
    select.appendChild(active);
    select.appendChild(historical);
    if (!(data.clients || []).length) {
        cloneToast("No clients yet. A client appears here after it scans while the server is reachable.", false);
    }
}

async function cloneLoadCatalog() {
    const response = await fetch("/clone/catalog");
    if (!response.ok) {
        throw new Error("catalog " + response.status);
    }
    cloneCatalog = await response.json();
    cloneRenderServer();
}

function cloneEpisodeChecked(contentSrc, parentPicked) {
    if ((cloneState.exclude || []).indexOf(contentSrc) !== -1) {
        return false;
    }
    if (parentPicked) {
        return true;
    }
    return (cloneState.selections || []).some((row) => row.kind === "episode" && row.content_src === contentSrc);
}

function cloneRenderServer() {
    const host = document.getElementById("clone_server");
    const filter = (document.getElementById("clone_filter").value || "").toLowerCase();
    host.innerHTML = "";
    (cloneCatalog.shows || []).forEach((show) => cloneAppendShow(host, show, filter));
    cloneAppendFlat(host, "Movies", cloneCatalog.movies || [], "movie", filter);
    cloneAppendFlat(host, "Books", cloneCatalog.books || [], "book", filter);
}

function cloneAppendShow(host, show, filter) {
    const showSelected = (cloneState.selections || []).some(
        (row) => row.kind === "show" && String(row.container_id) === String(show.container_id)
    );
    const block = document.createElement("div");
    block.className = "mb-3";
    const title = document.createElement("label");
    title.className = "d-flex align-items-center fw-semibold";
    title.innerHTML = clonePoster(show)
        + '<input type="checkbox" class="form-check-input me-2" data-role="show" data-id="'
        + show.container_id + '"' + (showSelected ? ' data-picked="1"' : '')
        + cloneCheckedAttr(showSelected) + "> "
        + (show.title || "Show");
    block.appendChild(title);
    (show.seasons || []).forEach((season) => {
        const seasonSelected = showSelected || (cloneState.selections || []).some(
            (row) => row.kind === "season" && String(row.container_id) === String(season.container_id)
        );
        const seasonLabel = document.createElement("label");
        seasonLabel.className = "d-flex align-items-center ms-3 mt-2";
        seasonLabel.innerHTML = clonePoster(season)
            + '<input type="checkbox" class="form-check-input me-2" data-role="season" data-id="'
            + season.container_id + '" data-show="' + show.container_id + '"'
            + cloneCheckedAttr(seasonSelected) + "> "
            + (season.title || "Season");
        block.appendChild(seasonLabel);
        (season.episodes || []).forEach((episode) => {
            const text = (episode.title || "") + " " + (episode.content_src || "");
            if (filter && text.toLowerCase().indexOf(filter) === -1 && (show.title || "").toLowerCase().indexOf(filter) === -1) {
                return;
            }
            const row = document.createElement("label");
            row.className = "d-flex align-items-center ms-5";
            const on = cloneEpisodeChecked(episode.content_src, seasonSelected);
            row.innerHTML = clonePoster(episode)
                + '<input type="checkbox" class="form-check-input me-2" data-role="episode" data-src="'
                + (episode.content_src || "") + '" data-show="' + show.container_id
                + '" data-season="' + season.container_id + '"' + cloneCheckedAttr(on) + "> "
                + (episode.title || episode.content_src);
            block.appendChild(row);
        });
    });
    host.appendChild(block);
}

function cloneAppendFlat(host, heading, rows, kind, filter) {
    if (!rows.length) {
        return;
    }
    const title = document.createElement("div");
    title.className = "fw-semibold mt-3";
    title.textContent = heading;
    host.appendChild(title);
    rows.forEach((item) => {
        const text = (item.title || "") + " " + (item.content_src || "");
        if (filter && text.toLowerCase().indexOf(filter) === -1) {
            return;
        }
        const selected = (cloneState.selections || []).some(
            (row) => row.kind === kind && row.content_src === item.content_src
        );
        const label = document.createElement("label");
        label.className = "d-flex align-items-center ms-2";
        label.innerHTML = clonePoster(item)
            + '<input type="checkbox" class="form-check-input me-2" data-role="' + kind
            + '" data-src="' + (item.content_src || "") + '"' + cloneCheckedAttr(selected) + "> "
            + (item.title || item.content_src);
        host.appendChild(label);
    });
}

function cloneBoxes(role) {
    return Array.from(document.querySelectorAll('#clone_server input[data-role="' + role + '"]'));
}

function cloneWireChecks() {
    document.getElementById("clone_server").addEventListener("change", (event) => {
        const box = event.target;
        if (!box || box.type !== "checkbox") {
            return;
        }
        const role = box.dataset.role;
        if (role === "show") {
            box.dataset.picked = box.checked ? "1" : "";
            cloneBoxes("season").forEach((season) => {
                if (season.dataset.show === box.dataset.id) {
                    season.checked = box.checked;
                }
            });
            cloneBoxes("episode").forEach((episode) => {
                if (episode.dataset.show === box.dataset.id) {
                    episode.checked = box.checked;
                }
            });
        } else if (role === "season") {
            box.dataset.picked = box.checked ? "1" : "";
            cloneBoxes("episode").forEach((episode) => {
                if (episode.dataset.season === box.dataset.id) {
                    episode.checked = box.checked;
                }
            });
            const show = cloneBoxes("show").find((row) => row.dataset.id === box.dataset.show);
            if (show && !box.checked) {
                show.checked = false;
                show.dataset.picked = "";
            }
        } else if (role === "episode") {
            if (!box.checked) {
                const show = cloneBoxes("show").find((row) => row.dataset.id === box.dataset.show);
                const season = cloneBoxes("season").find((row) => row.dataset.id === box.dataset.season);
                if (show) {
                    show.checked = false;
                }
                if (season) {
                    season.checked = false;
                }
            }
        }
    });
}

function cloneCollect() {
    const selections = [];
    const exclude = [];
    cloneBoxes("show").forEach((showBox) => {
        const episodes = cloneBoxes("episode").filter((row) => row.dataset.show === showBox.dataset.id);
        const checked = episodes.filter((row) => row.checked);
        if (!checked.length) {
            return;
        }
        if (showBox.dataset.picked === "1" || showBox.checked || checked.length === episodes.length) {
            selections.push({
                kind: "show",
                container_id: Number(showBox.dataset.id),
                title: showBox.parentElement.textContent.trim(),
            });
            episodes.filter((row) => !row.checked).forEach((row) => exclude.push(row.dataset.src));
            return;
        }
        const seasons = cloneBoxes("season").filter((row) => row.dataset.show === showBox.dataset.id);
        seasons.forEach((seasonBox) => {
            const seasonEpisodes = episodes.filter((row) => row.dataset.season === seasonBox.dataset.id);
            const seasonChecked = seasonEpisodes.filter((row) => row.checked);
            if (!seasonChecked.length) {
                return;
            }
            if (seasonBox.dataset.picked === "1" || seasonBox.checked || seasonChecked.length === seasonEpisodes.length) {
                selections.push({
                    kind: "season",
                    container_id: Number(seasonBox.dataset.id),
                    title: seasonBox.parentElement.textContent.trim(),
                });
                seasonEpisodes.filter((row) => !row.checked).forEach((row) => exclude.push(row.dataset.src));
                return;
            }
            seasonChecked.forEach((row) => {
                selections.push({kind: "episode", content_src: row.dataset.src, title: row.parentElement.textContent.trim()});
            });
        });
    });
    ["movie", "book"].forEach((kind) => {
        cloneBoxes(kind).forEach((box) => {
            if (box.checked) {
                selections.push({kind: kind, content_src: box.dataset.src, title: box.parentElement.textContent.trim()});
            }
        });
    });
    return {selections: selections, exclude: exclude};
}

function cloneRenderClient() {
    const host = document.getElementById("clone_client_files");
    host.innerHTML = "";
    const pending = new Set(cloneState.remove || []);
    function addRow(src, title, poster) {
        const label = document.createElement("label");
        label.className = "d-flex align-items-center";
        const queued = pending.has(src) ? " (queued)" : "";
        label.innerHTML = poster
            + '<input type="checkbox" class="form-check-input me-2" data-remove-src="'
            + src + '"> ' + title + queued;
        host.appendChild(label);
    }
    (cloneClientTree.shows || []).forEach((show) => {
        const heading = document.createElement("div");
        heading.className = "fw-semibold mt-2";
        heading.innerHTML = clonePoster(show) + (show.title || "Show");
        host.appendChild(heading);
        (show.seasons || []).forEach((season) => {
            const seasonLabel = document.createElement("div");
            seasonLabel.className = "ms-3 text-secondary";
            seasonLabel.textContent = season.title || "Season";
            host.appendChild(seasonLabel);
            (season.episodes || []).forEach((episode) => {
                const row = document.createElement("div");
                row.className = "ms-5";
                row.innerHTML = "";
                host.appendChild(row);
                const label = document.createElement("label");
                label.className = "d-flex align-items-center";
                const queued = pending.has(episode.content_src) ? " (queued)" : "";
                label.innerHTML = clonePoster(episode)
                    + '<input type="checkbox" class="form-check-input me-2" data-remove-src="'
                    + episode.content_src + '"> ' + (episode.title || episode.content_src) + queued;
                row.appendChild(label);
            });
        });
    });
    (cloneClientTree.movies || []).forEach((item) => addRow(item.content_src, item.title || item.content_src, clonePoster(item)));
    (cloneClientTree.books || []).forEach((item) => addRow(item.content_src, item.title || item.content_src, clonePoster(item)));
    (cloneClientTree.other || []).forEach((item) => {
        const heading = document.getElementById("clone_other_heading");
        if (!heading) {
            const title = document.createElement("div");
            title.id = "clone_other_heading";
            title.className = "fw-semibold mt-3";
            title.textContent = "Other";
            host.appendChild(title);
        }
        addRow(item.content_src, item.title || item.content_src, "");
    });
}

async function cloneSelectClient() {
    const clientId = document.getElementById("clone_client").value;
    const meta = document.getElementById("clone_client_meta");
    if (!clientId) {
        meta.textContent = "";
        cloneClientTree = {shows: [], movies: [], books: [], other: []};
        cloneState = {selections: [], exclude: [], remove: []};
        cloneRenderServer();
        cloneRenderClient();
        return;
    }
    const response = await fetch("/clone/clients/" + encodeURIComponent(clientId));
    if (!response.ok) {
        cloneToast("Could not load that client", true);
        return;
    }
    const data = await response.json();
    const manifest = data.manifest || {};
    cloneState = {
        selections: manifest.selections || [],
        exclude: manifest.exclude || [],
        remove: manifest.remove || [],
    };
    cloneClientTree = data.client_tree || {shows: [], movies: [], books: [], other: []};
    meta.textContent = "Last seen " + (manifest.last_seen || "never")
        + (manifest.updated_at ? " · manifest " + manifest.updated_at : "");
    cloneRenderServer();
    cloneRenderClient();
}

async function cloneSave() {
    const clientId = document.getElementById("clone_client").value;
    if (!clientId) {
        cloneToast("Pick a client first", true);
        return;
    }
    const response = await fetch("/clone/clients/" + encodeURIComponent(clientId), {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(cloneState),
    });
    if (!response.ok) {
        cloneToast("Save failed", true);
        return;
    }
    cloneToast("Manifest saved", false);
    await cloneSelectClient();
}

document.addEventListener("DOMContentLoaded", () => {
    const server = document.getElementById("clone_server");
    if (!server) {
        return;
    }
    cloneWireChecks();
    document.getElementById("clone_filter").addEventListener("input", cloneRenderServer);
    document.getElementById("clone_client").addEventListener("change", () => {
        cloneSelectClient().catch((error) => {
            console.error(error);
            cloneToast("Could not load that client", true);
        });
    });
    document.getElementById("clone_add").addEventListener("click", () => {
        const collected = cloneCollect();
        cloneState.selections = collected.selections;
        cloneState.exclude = collected.exclude;
        cloneToast("Selection updated. Save the manifest to keep it.", false);
        cloneRenderServer();
    });
    document.getElementById("clone_remove").addEventListener("click", () => {
        const picked = Array.from(document.querySelectorAll("#clone_client_files input[data-remove-src]:checked"));
        picked.forEach((box) => {
            const src = box.dataset.removeSrc;
            if (cloneState.remove.indexOf(src) === -1) {
                cloneState.remove.push(src);
            }
            if (cloneState.exclude.indexOf(src) === -1) {
                cloneState.exclude.push(src);
            }
        });
        cloneToast("Removal queued. Save the manifest, then Sync on the client.", false);
        cloneRenderClient();
    });
    document.getElementById("clone_save").addEventListener("click", () => {
        cloneSave().catch((error) => {
            console.error(error);
            cloneToast("Save failed", true);
        });
    });
    cloneLoadClients()
        .then(() => cloneLoadCatalog())
        .then(() => cloneSelectClient())
        .catch((error) => {
            console.error(error);
            cloneToast("Could not load the clone page", true);
        });
});
