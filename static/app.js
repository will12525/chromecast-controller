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

async function update_editor_log(response_data) {
        editor_txt_file_log = document.getElementById("editor_txt_file_log");
        prepend_text = "";
        console.log(response_data)

        if (response_data["message"] !== undefined) {
            prepend_text += response_data["message"];
        }
        if (response_data["file_name"] !== undefined) {
            prepend_text += ": " + response_data["file_name"];
        }
        if (response_data["expected_path"] !== undefined) {
            prepend_text += ": " + response_data["expected_path"];
        }
        if (response_data["value"] !== undefined) {
            prepend_text += ": " + response_data["value"];
        }
        editor_txt_file_log.value = prepend_text + "\n" + editor_txt_file_log.value;
}

async function update_editor_webpage(response_data) {
    if (response_data["selected_txt_file_title"] !== undefined) {
        document.getElementById("editor_txt_file_name").innerHTML = response_data["selected_txt_file_title"];
    }
    if (response_data["selected_txt_file_content"] !== undefined) {
        document.getElementById("editor_txt_file_content").value = response_data["selected_txt_file_content"];
    }
    if (response_data["error"] !== undefined) {
          update_editor_log(response_data?.error)
    }
    if (response_data["process_log"] !== undefined) {
        response_data?.process_log.forEach((element) => update_editor_log(element));
    }

    if (response_data["process_queue"] !== undefined && response_data["process_name"] !== undefined && response_data["process_end_time"] !== undefined && response_data["process_queue_size"] !== undefined) {
        const process_queue_list = []

        const queue_item_li = document.createElement("li");
        queue_item_li.classList.add("list-group-item")

        const queue_item_text = document.createElement("h5");
        queue_item_text.classList.add("mb-1");
        queue_item_text.appendChild(document.createTextNode(response_data["process_name"]));
        queue_item_li.appendChild(queue_item_text);

        if (response_data["process_name"] != "Split queue empty") {
            const queue_item_progress = document.createElement("div");
            queue_item_progress.classList.add("progress")
            queue_item_progress.setAttribute("role", "progressbar");
            queue_item_progress.setAttribute("aria-valuemin", "0");
            queue_item_progress.setAttribute("aria-valuemax", "100");
            queue_item_progress.setAttribute("aria-valuenow", response_data["percent_complete"]);
            const queue_item_progress_bar = document.createElement("div");
            queue_item_progress_bar.classList.add("progress-bar-striped")
            queue_item_progress_bar.classList.add("bg-info")
            queue_item_progress_bar.setAttribute("style", 'width: '.concat(response_data["percent_complete"], "%"));

            queue_item_progress.appendChild(queue_item_progress_bar);
            queue_item_li.appendChild(queue_item_progress);
        }
        process_queue_list.push(queue_item_li)

        for (const queue_item of response_data["process_queue"]) {
            const queue_item_li = document.createElement("li");
            queue_item_li.classList.add("list-group-item")
            const queue_item_text = document.createTextNode(queue_item);
            queue_item_li.appendChild(queue_item_text);
            process_queue_list.push(queue_item_li)

        }
//        document.getElementById("editor_process_metadata_name").innerText = response_data["process_name"];
        document.getElementById("editor_process_metadata_end_time").innerText = response_data["process_end_time"];
        document.getElementById("editor_process_metadata_queue_size").innerText = response_data["process_queue_size"];
        document.getElementById("editor_process_queue").replaceChildren(...process_queue_list)
    }
}

async function clear_editor_log() {
    document.getElementById("editor_txt_file_log").value = "";
}
async function edit_metadata_modal_open(metadata, content_type) {
    console.log(metadata)
    console.log(content_type)
    document.getElementById("modal_title").innerHTML = metadata['playlist_title'] || metadata['season_title'] || metadata['media_title'];
    document.getElementById("modal_text_area_image_url").value = metadata['image_url'];
    document.getElementById("modal_text_area_description").value = metadata['description'];
    document.getElementById("modal_metadata_save").setAttribute("onclick", "edit_metadata_modal_save(" + content_type + "," + metadata['id'] + ");");
}
async function edit_metadata_modal_save(content_type, content_id) {
    image_url = document.getElementById("modal_text_area_image_url").value;
    description = document.getElementById("modal_text_area_description").value;
    var url = "/update_media_metadata";
    let data = {
        "content_type": content_type,
        "id": content_id,
        "image_url": image_url,
        "description": description,
    };
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });
    location.reload();

    // Send POST request
//    if (!response.ok) {
//        throw new Error("HTTP ERROR FAILED: " + response.status);
//    } else {
//        let json_response = await response.json();
//        console.log(json_response)
//    }
}

async function load_txt_file(element) {
    var url = "/load_txt_file";
    var editor_txt_file_name = element.textContent;
    let data = {
        "editor_txt_file_name": editor_txt_file_name
    };
    console.log(data)
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });
    // Send POST request
    if (!response.ok) {
        throw new Error("HTTP ERROR FAILED: " + response.status);
    } else {
        update_editor_webpage(await response.json());
    }
}

async function save_txt_file() {
    var url = "/save_txt_file";
    const editor_txt_file_name = document.getElementById("editor_txt_file_name");
    const editor_txt_file_content = document.getElementById("editor_txt_file_content");
    let data = {
        "txt_file_name": editor_txt_file_name.textContent,
        "txt_file_content": editor_txt_file_content.value
    };
    // Send POST request
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });
    if (!response.ok) {
        throw new Error("HTTP ERROR FAILED: " + response.status);
    } else {
        update_editor_webpage(await response.json());
    }
}

async function validate_txt_file() {
    var url = "/validate_txt_file";
    const editor_txt_file_name = document.getElementById("editor_txt_file_name");
    const editor_txt_file_content = document.getElementById("editor_txt_file_content");
    const media_type_dropdown = document.getElementById("media_type_dropdown");
    let data = {
        "txt_file_name": editor_txt_file_name.textContent,
        "txt_file_content": editor_txt_file_content.value,
        "txt_file_media_type": media_type_dropdown.innerText.trim()
    };
    // Send POST request
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });
    if (!response.ok) {
        throw new Error("HTTP ERROR FAILED: " + response.status);
    } else {
        update_editor_webpage(await response.json());
    }
}

async function process_txt_file() {
    var url = "/process_txt_file";
    const editor_txt_file_name = document.getElementById("editor_txt_file_name");
    const editor_txt_file_content = document.getElementById("editor_txt_file_content");
    const media_type_dropdown = document.getElementById("media_type_dropdown");
    let data = {
        "txt_file_name": editor_txt_file_name.textContent,
        "txt_file_content": editor_txt_file_content.value,
        "txt_file_media_type": media_type_dropdown.innerText.trim()

    };
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });
    if (!response.ok) {
        throw new Error("HTTP ERROR FAILED: " + response.status);
    } else {
        update_editor_webpage(await response.json());
    }
}

async function updateEditorMetadata() {
    if (document.getElementById("editor_process_queue"))
    {
        var url = "/process_metadata";
        let response = await fetch(url);
        if (response.ok) {
            update_editor_webpage(await response.json())
        }
    }
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

async function update_selected_media_type(selected_li) {
    document.getElementById("media_type_dropdown").innerHTML = selected_li.innerText;
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
    var editor_button = document.getElementById("editor_button");

    var url = "/get_media_content_types";
    let response = await fetch(url);

    if (!response.ok) {
        throw new Error("HTTP status setNavbarLinks: " + response.status);
    } else {
        let response_data = await response.json();
        if (tv_show_select_button !== null)
        {
            tv_show_select_button.setAttribute('href', "/?content_type=" + response_data["TV"]);
        }
        if (movie_select_button !== null)
        {
            movie_select_button.setAttribute('href', "/?content_type=" + response_data["MOVIE"]);
        }
        if (editor_button !== null)
        {
            editor_button.setAttribute('href', "/editor");
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
    setInterval(updateEditorMetadata, 5000);
    getChromecastList();
    setNavbarLinks();
    setMediaControlButtons();

});



