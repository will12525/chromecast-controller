String.prototype.toHHMMSS = function () {
    var sec_num = parseInt(this, 10);
    var hours   = Math.floor(sec_num / 3600);
    var minutes = Math.floor((sec_num - (hours * 3600)) / 60);
    var seconds = sec_num - (hours * 3600) - (minutes * 60);

    if (hours   < 10) {hours   = "0"+hours;}
    if (minutes < 10) {minutes = "0"+minutes;}
    if (seconds < 10) {seconds = "0"+seconds;}
    return hours+":"+minutes+":"+seconds;
};

async function connectChromecast(chromecast_id) {
    var url = "/connect_chromecast";
    let data = {
        "chromecast_id": chromecast_id
    };
    // Send POST request
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });

    if (!response.ok) {
        throw new Error("HTTP status connectChromecast: " + response.status);
    } else {
        let response_data = await response.json();
        if ("chromecast_id" in response_data) {
            document.getElementById("connected_chromecast_id").innerHTML = response_data?.chromecast_id;
        }
    }
};

async function getChromecastList() {
    var url = "/get_chromecast_list";
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
        if (response_data["scanned_devices"] !== undefined)
        {
            const chromecasts = [];
            const dropdown_list = document.getElementById("dropdown_scanned_chromecasts");
            const listItems = dropdown_list.getElementsByTagName('li');
            // The dropdown list has a divider and disconnect button
            for (let i = 0; i <= listItems.length - 3; i++) {
                chromecasts.push(listItems[i].textContent);
            }
            for (const device of response_data["scanned_devices"]) {
               if (!chromecasts.includes(device)) {
                   var li = document.createElement("li");
                   var a_element = document.createElement("a");
                   a_element.appendChild(document.createTextNode(device));
                   a_element.setAttribute("class", "dropdown-item")
                   a_element.setAttribute("value", device)
                   a_element.addEventListener("click", connectChromecast.bind(null, device));
                   li.appendChild(a_element)
                   dropdown_list.prepend(li);
               }
            }
        }
        if (response_data["connected_device"] !== undefined)
        {
            document.getElementById("connected_chromecast_id").innerHTML = response_data["connected_device"];
        }
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
        document.getElementById("connected_chromecast_id").innerHTML = ""
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

async function setMediaRuntime(range) {
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

async function play_media(media_id, playlist_id=null) {
    var url = "/play_media";
    let data = {
        "media_id": media_id,
        "playlist_id": playlist_id
    };
    // Send POST request
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });
}

async function scan_media_directories() {
    var url = "/scan_media_directories";
    let data = {};
    var disable_class = "disabled";
    var button_id = "scan_media_button";
    var button_element = document.getElementById(button_id);

    button_element.classList.add(disable_class);
    // Send POST request
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });
    button_element.classList.remove(disable_class);
}

async function updateSeekSelector() {
    var mediaTimeInputId = document.getElementById("mediaTimeInputId");
    if (mediaTimeInputId)
    {
        if (document.activeElement !== mediaTimeInputId)
        {
            var url = "/get_current_media_runtime";
            let response = await fetch(url);

            if (!response.ok) {
                throw new Error("HTTP status disconnectChromecast: " + response.status);
            } else {
                let response_data = await response.json();
                if ("media_runtime" in response_data) {
                    media_runtime = response_data?.media_runtime.toString().toHHMMSS();
                    mediaTimeInputId.max = response_data?.media_duration
                    mediaTimeInputId.value = response_data?.media_runtime
                    mediaTimeInputId.title = media_runtime

                    mediaTimeOutputId.value = media_runtime + "  " + response_data?.media_title

                }
            }
        }
    }
}

async function setNavbarLinks() {
    var tv_show_select_button = document.getElementById("tv_show_select_button");
    var movie_select_button = document.getElementById("movie_select_button");
    var scan_media_button = document.getElementById("scan_media_button");

    var url = "/get_media_content_types";
    let response = await fetch(url);

    if (!response.ok) {
        throw new Error("HTTP status setNavbarLinks: " + response.status);
    } else {
        let response_data = await response.json();
        if (tv_show_select_button !== null)
        {
            tv_show_select_button.setAttribute('href', "?content_type=" + response_data["TV"]);
        }
        if (movie_select_button !== null)
        {
            movie_select_button.setAttribute('href', "?content_type=" + response_data["MOVIE"]);
        }
        if (scan_media_button !== null)
        {
            scan_media_button.addEventListener("click", scan_media_directories.bind(null));
        }
    }
}

async function setMediaControlButtons() {
    var url = "/get_chromecast_controls";
    let response = await fetch(url);

    if (!response.ok) {
        throw new Error("HTTP status setMediaControlButtons: " + response.status);
    } else {
        let response_data = await response.json();
        for (const [key, value] of Object.entries(response_data["chromecast_controls"])) {
            button_element = document.getElementById(key + "_media_button")
            if (button_element !== null) {
                button_element.addEventListener("click", chromecast_command.bind(null, value));
            }
        }
    }
}

document.addEventListener("DOMContentLoaded", function(event){
    var chromecast_menu = document.getElementById("chromecast_menu");
    if (chromecast_menu !== null)
    {
        chromecast_menu.addEventListener("click", getChromecastList.bind(null));
    }
    var chromecast_disconnect_button = document.getElementById("chromecast_disconnect_button");
    if (chromecast_disconnect_button !== null)
    {
        chromecast_disconnect_button.addEventListener("click", disconnectChromecast.bind(null));
    }

    setInterval(updateSeekSelector, 1000);
    getChromecastList();
    setNavbarLinks();
    setMediaControlButtons();

});



