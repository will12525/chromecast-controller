/* Phase 4: chromecast.js — plain global script (no bundler). */
async function connectChromecast(chromecast_id, displayName) {
    var url = "/connect_chromecast";
    // chromecast_id is the stable UUID when available (friendly name still accepted server-side)
    let data = {
        "chromecast_id": chromecast_id
    };
    // Send POST request
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });

    document.getElementById("local_video_player").hidden = true;
    document.getElementById("local_video_player").pause();
    document.getElementById("local_video_player_src").setAttribute("src", '')

    if (!response.ok) {
        throw new Error("HTTP status connectChromecast: " + response.status);
    } else {
        let response_data = await response.json();
        const label =
            response_data.chromecast_name ||
            displayName ||
            response_data.chromecast_id ||
            "Chromecast";
        document.getElementById("connected_chromecast_id").innerHTML = label;
    }
};

async function apply_default_image(imageElement) {
    imageElement.setAttribute("onerror", "")
    imageElement.src = window.location.protocol + "//" + window.location.hostname + ":8000/images/" + default_image_array[Math.floor(Math.random()*default_image_array.length)];
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
    } else {
        let response_data = await response.json();
        if (response_data["scanned_devices"] !== undefined)
        {
            const scanned = response_data["scanned_devices"] || [];
            const dropdown_list = document.getElementById("dropdown_scanned_chromecasts");
            if (!dropdown_list) {
                return;
            }
            // Keep static controls (divider / disconnect / local); rebuild devices only.
            // Dead devices from prior scans are dropped by replacing the prefix list.
            const staticItems = [];
            let hitDivider = false;
            Array.from(dropdown_list.children).forEach((li) => {
                if (!hitDivider && li.querySelector("hr.dropdown-divider")) {
                    hitDivider = true;
                }
                if (hitDivider) {
                    staticItems.push(li);
                }
            });
            dropdown_list.innerHTML = "";
            for (const device of scanned) {
                // Prefer {uuid, name}; accept legacy bare string device entries
                const deviceId = (device && device.uuid) ? device.uuid : device;
                const deviceName = (device && device.name) ? device.name : String(device);
                var li = document.createElement("li");
                var a_element = document.createElement("a");
                a_element.appendChild(document.createTextNode(deviceName));
                a_element.setAttribute("class", "dropdown-item");
                a_element.setAttribute("value", deviceId);
                a_element.setAttribute("data-uuid", deviceId);
                a_element.setAttribute("title", deviceId);
                a_element.addEventListener(
                    "click",
                    connectChromecast.bind(null, deviceId, deviceName)
                );
                li.appendChild(a_element);
                dropdown_list.appendChild(li);
            }
            // If template had no static divider section, ensure disconnect/local remain
            if (!staticItems.length) {
                const divider = document.createElement("li");
                divider.innerHTML = '<hr class="dropdown-divider">';
                dropdown_list.appendChild(divider);
            } else {
                staticItems.forEach((li) => dropdown_list.appendChild(li));
            }
        }
        if (response_data["connected_device"] !== undefined)
        {
            document.getElementById("connected_chromecast_id").innerHTML = response_data["connected_device"] || "Local";
        }
    }
};

async function connect_local_player() {
    disconnectChromecast();
    var url = "/connect_local_player";
    let data = {};
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });

    if (!response.ok) {
        throw new Error("HTTP status connect_local_player: " + response.status);
    } else {
        let response_data = await response.json();
        document.getElementById("connected_chromecast_id").innerHTML = "Local"
    }
};

async function disconnectChromecast() {
    var url = "/disconnect_chromecast";
    let data = {};
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });

    if (!response.ok) {
        throw new Error("HTTP status disconnectChromecast: " + response.status);
    } else {
        let response_data = await response.json();
        document.getElementById("connected_chromecast_id").innerHTML = "Local"
    }
};

async function chromecast_command(chromecast_cmd_id) {
    var url = "/chromecast_command";
    let data = {
        "chromecast_cmd_id": chromecast_cmd_id
    };
    // Send POST request
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });
}

async function set_media_runtime(range) {
    document.activeElement.blur()

    var url = "/set_current_media_runtime";
    let data = {
        "new_media_time": range.value
    };
    // Send POST request
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });
};
