/* Phase 4 + multi-cast: chromecast.js — plain global script (no bundler). */
/* global playerApplyStreamState, playerSetStreamMode, playerUpdateStatusChip, playerStreamMode */

async function connectChromecast(chromecast_id, displayName) {
    var url = "/connect_chromecast";
    let data = {
        "chromecast_id": chromecast_id
    };
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });

    const video = document.getElementById("local_video_player");
    if (video) {
        video.hidden = true;
        video.pause();
        const src = document.getElementById("local_video_player_src");
        if (src) {
            src.setAttribute("src", "");
        }
    }

    if (!response.ok) {
        throw new Error("HTTP status connectChromecast: " + response.status);
    }
    let response_data = await response.json();
    playerApplyStreamState(response_data);
    // Default new connect to device mode on that uuid
    if (response_data.chromecast_id) {
        await playerSetStreamMode("device", response_data.chromecast_id);
    }
    // Refresh menu marks
    await getChromecastList();
}

async function apply_default_image(imageElement) {
    imageElement.setAttribute("onerror", "");
    imageElement.src = window.location.protocol + "//" + window.location.hostname + ":8000/images/" + default_image_array[Math.floor(Math.random()*default_image_array.length)];
}

function _castMenuStaticFooter() {
    const items = [];
    const divider1 = document.createElement("li");
    divider1.innerHTML = '<hr class="dropdown-divider">';
    items.push(divider1);

    // Stream mode section
    const modeHeader = document.createElement("li");
    modeHeader.innerHTML = '<h6 class="dropdown-header">Stream to</h6>';
    items.push(modeHeader);

    const modes = [
        { mode: "local", label: "Local player", id: null },
        { mode: "all", label: "All connected", id: null },
    ];
    modes.forEach((m) => {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.className = "dropdown-item stream-mode-item";
        a.href = "#";
        a.dataset.mode = m.mode;
        a.textContent = m.label;
        a.addEventListener("click", async (e) => {
            e.preventDefault();
            e.stopPropagation();
            await playerSetStreamMode(m.mode);
            await getChromecastList();
        });
        li.appendChild(a);
        items.push(li);
    });

    const divider2 = document.createElement("li");
    divider2.innerHTML = '<hr class="dropdown-divider">';
    items.push(divider2);

    const disc = document.createElement("li");
    const discA = document.createElement("a");
    discA.id = "chromecast_disconnect_button";
    discA.className = "dropdown-item";
    discA.href = "#";
    discA.textContent = "Disconnect all";
    discA.addEventListener("click", async (e) => {
        e.preventDefault();
        await disconnectChromecast();
    });
    disc.appendChild(discA);
    items.push(disc);

    const localLi = document.createElement("li");
    const localA = document.createElement("a");
    localA.id = "local_play_button";
    localA.className = "dropdown-item";
    localA.href = "#";
    localA.textContent = "Local";
    localA.addEventListener("click", async (e) => {
        e.preventDefault();
        await connect_local_player();
    });
    localLi.appendChild(localA);
    items.push(localLi);

    return items;
}

async function getChromecastList() {
    var url = "/get_chromecast_list";
    let data = {};
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });

    if (!response.ok) {
        throw new Error("HTTP status getChromecastList: " + response.status);
    }
    let response_data = await response.json();
    playerApplyStreamState(response_data);

    const dropdown_list = document.getElementById("dropdown_scanned_chromecasts");
    if (!dropdown_list) {
        return;
    }

    const scanned = response_data.scanned_devices || [];
    const connected = response_data.connected_devices || [];
    const connectedIds = new Set(connected.map((d) => d.uuid));
    const mode = response_data.stream_mode || "local";
    const activeId = response_data.active_device_id;

    dropdown_list.innerHTML = "";

    const devicesHeader = document.createElement("li");
    devicesHeader.innerHTML = '<h6 class="dropdown-header">Devices (tap to connect)</h6>';
    dropdown_list.appendChild(devicesHeader);

    for (const device of scanned) {
        const deviceId = (device && device.uuid) ? device.uuid : device;
        const deviceName = (device && device.name) ? device.name : String(device);
        const isConnected = connectedIds.has(deviceId);
        const isActive = mode === "device" && activeId === deviceId;

        const li = document.createElement("li");
        const a = document.createElement("a");
        a.className = "dropdown-item d-flex justify-content-between align-items-center";
        a.href = "#";
        a.setAttribute("data-uuid", deviceId);
        a.setAttribute("title", deviceId);

        const label = document.createElement("span");
        let prefix = "";
        if (isConnected) {
            prefix = isActive ? "● " : "✓ ";
        }
        label.textContent = prefix + deviceName;
        a.appendChild(label);

        if (isConnected) {
            const btnGroup = document.createElement("span");
            btnGroup.className = "ms-2";

            const useBtn = document.createElement("button");
            useBtn.type = "button";
            useBtn.className = "btn btn-sm btn-outline-secondary py-0 px-1";
            useBtn.textContent = "Use";
            useBtn.title = "Stream to this device only";
            useBtn.addEventListener("click", async (e) => {
                e.preventDefault();
                e.stopPropagation();
                await playerSetStreamMode("device", deviceId);
                await getChromecastList();
            });

            const xBtn = document.createElement("button");
            xBtn.type = "button";
            xBtn.className = "btn btn-sm btn-outline-danger py-0 px-1 ms-1";
            xBtn.textContent = "×";
            xBtn.title = "Disconnect";
            xBtn.addEventListener("click", async (e) => {
                e.preventDefault();
                e.stopPropagation();
                await disconnectChromecast(deviceId);
            });

            btnGroup.appendChild(useBtn);
            btnGroup.appendChild(xBtn);
            a.appendChild(btnGroup);
        }

        a.addEventListener("click", async (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (isConnected) {
                await playerSetStreamMode("device", deviceId);
                await getChromecastList();
            } else {
                await connectChromecast(deviceId, deviceName);
            }
        });
        li.appendChild(a);
        dropdown_list.appendChild(li);
    }

    if (!scanned.length) {
        const li = document.createElement("li");
        li.innerHTML = '<span class="dropdown-item-text text-muted">No devices found</span>';
        dropdown_list.appendChild(li);
    }

    _castMenuStaticFooter().forEach((li) => dropdown_list.appendChild(li));

    // Highlight active stream mode
    dropdown_list.querySelectorAll(".stream-mode-item").forEach((el) => {
        if (el.dataset.mode === mode) {
            el.classList.add("active");
        }
    });

    playerUpdateStatusChip();
}

async function connect_local_player() {
    var url = "/connect_local_player";
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify({}),
    });

    if (!response.ok) {
        throw new Error("HTTP status connect_local_player: " + response.status);
    }
    let response_data = await response.json();
    playerApplyStreamState(Object.assign({ stream_mode: "local", connected_devices: playerConnectedDevices }, response_data));
    const video = document.getElementById("local_video_player");
    if (video) {
        video.hidden = false;
    }
    playerUpdateStatusChip();
    await getChromecastList();
}

async function disconnectChromecast(chromecast_id) {
    var url = "/disconnect_chromecast";
    let data = {};
    if (chromecast_id) {
        data.chromecast_id = chromecast_id;
    }
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });

    if (!response.ok) {
        throw new Error("HTTP status disconnectChromecast: " + response.status);
    }
    let response_data = await response.json();
    playerApplyStreamState(response_data);
    playerUpdateStatusChip();
    await getChromecastList();
}

async function chromecast_command(chromecast_cmd_id) {
    var url = "/chromecast_command";
    let data = {
        "chromecast_cmd_id": chromecast_cmd_id
    };
    await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });
}

async function set_media_runtime(range) {
    try {
        if (document.activeElement && document.activeElement.blur) {
            document.activeElement.blur();
        }
    } catch (e) { /* ignore */ }

    var url = "/set_current_media_runtime";
    let data = {
        "new_media_time": range.value
    };
    await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });
}
