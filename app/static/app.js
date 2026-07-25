default_image_array = ['10.jpg', '11.jpg', '12.png', '13.png', '14.png', '15.png', '16.png', '1.webp', '2.webp', '3.jpg', '4.jpg', '5.jpg', '6.jpg', '7.jpg', '8.jpg', '9.jpg']

let modal_metadata_save_click_handler = (event) => {
}
let modal_metadata_select_tag_click_handler = (event) => {
};

/** Active library key: null = home, or tv|movies|books */
let currentLibraryKey = null;
let librarySearchDebounce = null;
let lastProgressPostAt = 0;
const PROGRESS_POST_INTERVAL_MS = 10000;
const RESUME_MIN_SECONDS = 30;
const RESUME_MAX_FRACTION = 0.9;

const LIBRARY_TAG_MAP = {
    tv: "tv show",
    movies: "movie",
    books: "book",
};

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
async function fetchAndSetData(url, data) {
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    let response_data = await response.json();
    return response_data;
  } catch (error) {
    console.error('Error fetching data:', error);
    // Handle errors (display message, retry, etc.)
  }

}

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

    document.getElementById("local_video_player").hidden = true;
    document.getElementById("local_video_player").pause();
    document.getElementById("local_video_player_src").setAttribute("src", '')

    if (!response.ok) {
        throw new Error("HTTP status connectChromecast: " + response.status);
    } else {
        let response_data = await response.json();
        if ("chromecast_id" in response_data) {
            document.getElementById("connected_chromecast_id").innerHTML = response_data?.chromecast_id;
        }
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
                var li = document.createElement("li");
                var a_element = document.createElement("a");
                a_element.appendChild(document.createTextNode(device));
                a_element.setAttribute("class", "dropdown-item");
                a_element.setAttribute("value", device);
                a_element.addEventListener("click", connectChromecast.bind(null, device));
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

async function generate_media_container(content_data, media_card_template, fragment) {
    const template = document.createElement("div");
    template.className = "col-sm-3";
    template.innerHTML = media_card_template;
    if ('container_title' in content_data) {
        if (content_data["container_id"])
        {
            template.querySelector("#content_container").dataset.containerId = content_data["container_id"];
        } else {
            template.querySelector("#content_container").dataset.containerId = content_data["id"];
        }
        template.querySelector("#content_navigator").textContent = content_data["container_title"]
        template.querySelector("#content_navigator").setAttribute('href', "javascript:load_container(" + content_data["id"] + ")")
    }
    else if ('content_title' in content_data) {
        if (content_data["content_id"])
        {
            template.querySelector("#content_container").dataset.contentId = content_data["content_id"];
        } else {
            template.querySelector("#content_container").dataset.contentId = content_data["id"];
        }
        template.querySelector("#content_navigator").textContent = content_data["content_title"]
        template.querySelector("#content_navigator").setAttribute('href', "javascript:play_media(" + content_data["id"] + ", " + content_data["parent_container_id"] + ")")
    }
    else {
        console.log("Missing title")
    }
    if ('play_count' in content_data) {
        if (content_data["play_count"] == 0) {
            template.querySelector("#new_tag").hidden = false
        }
    }
    if ('user_tags' in content_data) {
        template.querySelector("#card_tags").textContent = "Tags: " + content_data["user_tags"]
    }
    if ('content_index' in content_data) {
        template.querySelector("#content_index").hidden = false
        template.querySelector("#content_index").textContent = "Index: " + content_data["content_index"]
    }
    template.querySelector("#card_description").textContent = content_data["description"]
    if ('img_src' in content_data && 'img_url' in content_data) {
        template.querySelector("#content_img").src = content_data['img_url'];
    }
    template.querySelector("#content_img").dataset.img_src = content_data['img_src'];

    fragment.appendChild(template)
}
async function update_media_table(response_data) {
    const fragment = document.createDocumentFragment();
    const template = document.createElement("div");
    template.className = "col-md-12";

    const table = document.createElement("table");
    table.className = "table table-striped table-hover";

    const table_head = document.createElement("thead");
    const table_head_row = document.createElement("tr");
    column_list = ["Select", "Title", "Type", "Tags", "Index", "Play"]
    for (const column_title of column_list) {
        const th_element = document.createElement("th");
        th_element.scope = 'col';
        th_element.textContent = column_title;
        table_head_row.appendChild(th_element)
    }
    const table_body = document.createElement("tbody");
    if ('parent_containers' in response_data) {
        for (const content_data of response_data["parent_containers"]) {
            const tr_element = document.createElement("tr");
            tr_element.setAttribute('data-row-container_id', content_data["id"]);
            const td_title = document.createElement("td");
            const load_anchor = document.createElement('a');
            load_anchor.href = "javascript:load_container(" + content_data["id"] + ")";
            load_anchor.textContent = content_data["container_title"];
            td_title.appendChild(load_anchor);

            const td_type = document.createElement("td");
            td_type.textContent = "Playlist";

            const td_tags = document.createElement("td");
            td_tags.textContent = content_data["user_tags"];

            const td_index = document.createElement("td");
            td_index.textContent = content_data["season_index"];

            const td_play = document.createElement("td");
            const play_anchor = document.createElement('a');
            play_anchor.textContent = "Play";
            if ('parent_container_id' in content_data) {
                play_anchor.href = "javascript:play_media(" + content_data["id"] + ", " + content_data["parent_container_id"] + ", 'container')";
            } else {
                play_anchor.href = "javascript:play_media(" + content_data["id"] + ", null, 'container')";
            }
            td_play.appendChild(play_anchor);

            // Create the checkbox element
            const td_checkbox = document.createElement("td");
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            td_checkbox.appendChild(checkbox);

            // Append all the elements to the row
            tr_element.appendChild(td_checkbox);
            tr_element.appendChild(td_title);
            tr_element.appendChild(td_type);
            tr_element.appendChild(td_tags);
            tr_element.appendChild(td_index);
            tr_element.appendChild(td_play);
            table_body.appendChild(tr_element);
        }
    }
    if ('containers' in response_data) {
        for (const content_data of response_data["containers"]) {
            const tr_element = document.createElement("tr");
            tr_element.setAttribute('data-row-container_id', content_data["id"]);

            const td_title = document.createElement("td");
            const load_anchor = document.createElement('a');
            load_anchor.href = "javascript:load_container(" + content_data["id"] + ")";
            load_anchor.textContent = content_data["container_title"];
            td_title.appendChild(load_anchor);

            const td_type = document.createElement("td");
            td_type.textContent = "Playlist";

            const td_tags = document.createElement("td");
            td_tags.textContent = content_data["user_tags"];

            const td_index = document.createElement("td");
            td_index.textContent = content_data["season_index"];

            const td_play = document.createElement("td");
            const play_anchor = document.createElement('a');
            play_anchor.textContent = "Play";
            if ('parent_container_id' in content_data) {
                play_anchor.href = "javascript:play_media(" + content_data["id"] + ", " + content_data["parent_container_id"] + ", 'container')";
            } else {
                play_anchor.href = "javascript:play_media(" + content_data["id"] + ", null, 'container')";
            }
            td_play.appendChild(play_anchor);

            // Create the checkbox element
            const td_checkbox = document.createElement("td");
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            td_checkbox.appendChild(checkbox);

            // Append all the elements to the row
            tr_element.appendChild(td_checkbox);
            tr_element.appendChild(td_title);
            tr_element.appendChild(td_type);
            tr_element.appendChild(td_tags);
            tr_element.appendChild(td_index);
            tr_element.appendChild(td_play);
            table_body.appendChild(tr_element);
        }
    }
    if ('content' in response_data) {
        for (const content_data of response_data["content"]) {
            const tr_element = document.createElement("tr");
            tr_element.setAttribute('data-row-content_id', content_data["id"]);
            const td_checkbox = document.createElement("td");
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            td_checkbox.appendChild(checkbox);
            const td_title = document.createElement("td");
            td_title.textContent = content_data["content_title"];

            const td_type = document.createElement("td");
            td_type.textContent = "Media";

            const td_tags = document.createElement("td");
            td_tags.textContent = content_data["user_tags"];

            const td_index = document.createElement("td");
            td_index.textContent = content_data["content_index"];

            const td_play = document.createElement("td");
            const play_anchor = document.createElement('a');
            play_anchor.textContent = "Play";

            // Use ternary operator for cleaner conditional logic
            play_anchor.href = `javascript:play_media(${content_data["id"]}, ${'parent_container_id' in content_data ? content_data["parent_container_id"] : null}, 'content')`;

            td_play.appendChild(play_anchor);

            tr_element.appendChild(td_checkbox);
            tr_element.appendChild(td_title);
            tr_element.appendChild(td_type);
            tr_element.appendChild(td_tags);
            tr_element.appendChild(td_index);
            tr_element.appendChild(td_play);

            table_body.appendChild(tr_element);
        }
    }

    table_head.appendChild(table_head_row)
    table.appendChild(table_head)
    table.appendChild(table_body)
    template.appendChild(table)
    fragment.appendChild(template)

    const mainContent = document.getElementById("mediaContentSelectDiv");
    mainContent.innerHTML = "";
    document.getElementById("mediaContentSelectDiv").appendChild(fragment);

    document.getElementById("rainbow_loading_bar").hidden = true;
    window.scroll({
        top: 0,
        behavior: 'smooth'
    });
}
async function update_media_container(response_data) {
    const header_res = await fetch("static/media_list_header.html")
    const media_list_template = await header_res.text()
    const card_res = await fetch("static/media_card.html")
    const media_card_template = await card_res.text()

    const fragment = document.createDocumentFragment();
    if ('parent_containers' in response_data) {
        const template = document.createElement("div");
        template.className = "col-md-12";
        template.innerHTML = media_list_template;

        const parent_containers = response_data["parent_containers"]
        const parent_container = parent_containers[parent_containers.length - 1];
        const nav_item_container = template.querySelector("#nav_item_container")
        for (const content_data of response_data["parent_containers"]) {
            nav_item = document.createElement("li");
            nav_item.className = "nav-item";
            nav_item_a = document.createElement("a");
            nav_item_a.className = "nav-link";
            nav_item_a.setAttribute('aria-current', true)
            nav_item_a.textContent = content_data["container_title"];
            nav_item_a.setAttribute('href', "javascript:load_container(" + content_data["id"] + ")")
            nav_item.appendChild(nav_item_a)
            nav_item_container.appendChild(nav_item)
        }

        if (parent_container["container_id"]) {
            template.querySelector("#content_container").dataset.containerId = parent_container["container_id"];
        } else {
            template.querySelector("#content_container").dataset.containerId = parent_container["id"];
        }
        if ('content_index' in parent_container) {
            template.querySelector("#content_index").hidden = false
            template.querySelector("#content_index").textContent = "Index: " + parent_container["content_index"]
        }
        template.querySelector("#card_description").textContent = parent_container["description"];
        if ('img_src' in parent_container && 'img_url' in parent_container) {
            template.querySelector("#content_img").src = parent_container['img_url'];
        }
        template.querySelector("#content_img").dataset.img_src = parent_container['img_src'];
        if ('user_tags' in parent_container) {
            template.querySelector("#card_tags").textContent = "Tags: " + parent_container["user_tags"]
        }
        fragment.appendChild(template)
    }
    if ('containers' in response_data) {
        for (const content_data of response_data["containers"]) {
            generate_media_container(content_data, media_card_template, fragment)
        }
    }
    if ('content' in response_data) {
        for (const content_data of response_data["content"]) {
            generate_media_container(content_data, media_card_template, fragment)
        }
    }
    const mainContent = document.getElementById("mediaContentSelectDiv");
    mainContent.innerHTML = "";
    document.getElementById("mediaContentSelectDiv").appendChild(fragment);

    const contentEditors = document.querySelectorAll("#content_editor");
    contentEditors.forEach(editor => {
        editor.addEventListener('click', (event) => {
            const cardElement = event.target.closest('.card');
            if (cardElement) {
                let data = {
                    "tag_list": []
                };
                const container_id = cardElement?.dataset.containerId;
                const content_id = cardElement?.dataset.contentId;
                if (container_id != null) {
                    data["container_dict"] = {"container_id": container_id}
                    queryDBLocal(data).then(response_data => {
                        if (response_data["parent_containers"][0] !== undefined) {
                            const content_data = response_data["parent_containers"][response_data["parent_containers"].length - 1];
                            edit_metadata_modal_open({"container_id": container_id}, content_data["container_title"], content_data["img_src"], content_data["description"], content_data["user_tags"], cardElement);
                        }
                    });
                }
                if (content_id != null) {
                    data["container_dict"] = {"content_id": content_id}
                    queryDBLocal(data).then(response_data => {
                        if (response_data["content"][0] !== undefined) {
                            content_data = response_data["content"][0]
                            edit_metadata_modal_open({"content_id": content_id}, content_data["content_title"], content_data["img_src"], content_data["description"], content_data["user_tags"], cardElement);
                        }
                    });
                }
            }
        });
    });

    document.getElementById("rainbow_loading_bar").hidden = true;
    window.scroll({
        top: 0,
        behavior: 'smooth'
    });
}

async function queryDB(data) {
    document.getElementById("rainbow_loading_bar").hidden = false
    const url = "/query_db";
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    }).then(response => response.json())
        .then(response_data => {
            pathname = new URL(window.location.href).pathname
            if (pathname == "/table") {
                update_media_table(response_data)
            } else {
                update_media_container(response_data)
            }
        })
        .catch(error => console.error(error));
}
async function queryDBLocal(data) {
    var url = "/query_db";
    // Send POST request
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });
    if (!response.ok) {
        throw new Error("HTTP status connect_local_player: " + response.status);
    } else {
        return await response.json();
    }
}

function generate_tag_list_element(tag_title) {
    // Create the checkbox input element
    const checkbox = document.createElement('input');
    checkbox.className = 'form-check-input me-1';
    checkbox.type = 'checkbox';
    checkbox.value = tag_title;
    checkbox.id = `tag_checkbox_${tag_title}`;

    // Create the label element
    const label = document.createElement('label');
    label.className = 'form-check-label stretched-link';
    label.htmlFor = `tag_checkbox_${tag_title}`;
    label.textContent = tag_title;

    const tag_group_item = document.createElement('li');
    tag_group_item.className = 'list-group-item';
    tag_group_item.appendChild(checkbox);
    tag_group_item.appendChild(label);

    return tag_group_item;
}
function generate_tag_dropdown_element(tag_title) {
    // Create the label element
    const a = document.createElement('a');
    a.className = 'dropdown-item';
    a.textContent = tag_title;

    const tag_group_item = document.createElement('li');
    tag_group_item.appendChild(a);
    return tag_group_item;
}
function createTagElements(tagTitles) {
    const container = document.getElementById('tag_list_group'); // Replace with your container ID
    container.innerHTML = '';
    tagTitles.forEach(tagTitle => {
        container.appendChild(generate_tag_list_element(tagTitle));
    });
    if (!document.getElementById("content_editor_card").hidden) {
        const add_tag_list_group_dropdown = document.getElementById('add_tag_list_group_dropdown'); // Replace with your container ID
        add_tag_list_group_dropdown.innerHTML = '';
        document.getElementById('add_tag_list_group_title').innerHTML = tagTitles[0]
        tagTitles.forEach(tagTitle => {
            add_tag_list_group_dropdown.appendChild(generate_tag_dropdown_element(tagTitle));
        });
    }

}
async function add_new_tag(element) {
    const url = "/add_new_tag";
    const input = element.previousElementSibling;
    let data = {
        "tag_title": input.value
    };
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    }).then(response => response.json()).then(response_data => {
        if (response_data["tag_list"] !== undefined) {
            const tagTitles = response_data["tag_list"].map(tag => tag.tag_title);
            createTagElements(tagTitles)
        }
    })
    .catch(error => console.error(error));
};
async function get_tag_list(element) {
    var url = "/get_tag_list";
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"}
    });
    if (!response.ok) {
        throw new Error("HTTP status connect_local_player: " + response.status);
    } else {
        let response_data = await response.json();
        if (response_data["tag_list"] !== undefined) {
            return response_data["tag_list"].map(tag => tag.tag_title);
        }
    }
};


function get_selected_checkboxes(listGroup) {
  const checkboxes = listGroup.querySelectorAll('input[type="checkbox"]:checked');
  return Array.from(checkboxes).map(checkbox => checkbox.value);
}

async function query_db_get_all_filters(event) {
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
        "tag_list": get_selected_checkboxes(document.getElementById("tag_list_group")),
        "container_txt_search": search || null,
        "content_txt_search": search || null,
        "container_dict": {}
    };
    queryDB(data)
}

async function get_next_media(event) {
    var url = "/get_next_media";
    if (event.target.dataset.content_id !== undefined) {
        const rawTags = event.target.dataset.tagList;
        let data = {
            "content_id": parseInt(event.target.dataset.content_id),
            "parent_container_id": parseInt(event.target.dataset.parent_container_id),
            "play_mode": event.target.dataset.play_mode,
            "tag_list": rawTags ? JSON.parse(rawTags) : []
        };
        let response = await fetch(url, {
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": JSON.stringify(data),
        });

        if (!response.ok) {
            throw new Error("HTTP status get_next_media: " + response.status);
        } else {
            let response_data = await response.json();
            if (response_data["local_play_url"] !== undefined) {
                update_local_media_player(response_data)
            }
        }
    }
};
function shouldResume(position, duration) {
    const pos = parseFloat(position) || 0;
    const dur = parseFloat(duration) || 0;
    if (pos <= RESUME_MIN_SECONDS) {
        return false;
    }
    if (dur > 0 && pos / dur >= RESUME_MAX_FRACTION) {
        return false;
    }
    return true;
}

async function postPlaybackProgress(contentId, position, duration) {
    if (!contentId) {
        return;
    }
    const now = Date.now();
    if (now - lastProgressPostAt < PROGRESS_POST_INTERVAL_MS) {
        return;
    }
    lastProgressPostAt = now;
    try {
        await fetch("/playback_progress", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                content_id: parseInt(contentId, 10),
                position: position,
                duration: duration || 0,
            }),
        });
    } catch (error) {
        console.error("progress post failed", error);
    }
}

async function update_local_media_player(response_data) {
    const videoPlayer = document.getElementById('local_video_player');
    const videoSource = document.getElementById('local_video_player_src');

    try {
        videoPlayer.pause();
        videoPlayer.hidden = false;
        videoPlayer.style.visibility = 'visible';
        videoSource.setAttribute('src', response_data['local_play_url']);
        if (response_data["id"] !== undefined) {
            videoPlayer.dataset.content_id = response_data['id'];
        }
        if (response_data["parent_container_id"] !== undefined) {
            videoPlayer.dataset.parent_container_id = response_data['parent_container_id'];
        }
        if (response_data["play_mode"] !== undefined) {
            videoPlayer.dataset.play_mode = response_data['play_mode'];
        }
        if (response_data["tag_list"] !== undefined) {
            videoPlayer.dataset.tagList = JSON.stringify(response_data['tag_list']);
        }
        if (response_data["content_title"] !== undefined) {
            document.getElementById('content_title').innerHTML = response_data['content_title'];
        }
        const resumeAt = response_data["last_position"];
        const resumeDuration = response_data["last_duration"];
        videoPlayer.dataset.resumeAt = shouldResume(resumeAt, resumeDuration) ? String(resumeAt) : "";
        videoPlayer.load();
        videoPlayer.scrollIntoView();
        const onLoaded = () => {
            videoPlayer.removeEventListener("loadedmetadata", onLoaded);
            if (videoPlayer.dataset.resumeAt) {
                try {
                    videoPlayer.currentTime = parseFloat(videoPlayer.dataset.resumeAt);
                } catch (e) {
                    console.warn("resume seek failed", e);
                }
            }
            videoPlayer.play();
        };
        videoPlayer.addEventListener("loadedmetadata", onLoaded);
        // Fallback if metadata already available
        if (videoPlayer.readyState >= 1) {
            onLoaded();
        }
    } catch (error) {
        console.error('Error playing video:', error);
    }
}

async function play_media(content_id, parent_container_id=null, content_type=null) {
    var url = "/play_media";
    let tagList = [];
    const tagListEl = document.getElementById("tag_list_group");
    if (tagListEl) {
        tagList = get_selected_checkboxes(tagListEl);
    }
    // When browsing a library type, include its tag so auto-next can shuffle
    if (!tagList.length && currentLibraryKey && LIBRARY_TAG_MAP[currentLibraryKey]) {
        tagList = [LIBRARY_TAG_MAP[currentLibraryKey]];
    }
    let data = {
        "content_id": content_id,
        "parent_container_id": parent_container_id,
        "content_type": content_type,
        "tag_list": tagList
    };
    // Send POST request
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });

    if (!response.ok) {
        throw new Error("HTTP status play_media: " + response.status);
    } else {
        let response_data = await response.json();
        if (response_data["local_play_url"] !== undefined) {
            update_local_media_player(response_data)
        }
    }
}

/**
 * Shuffle-play a random item for the active library or selected tags.
 * Reuses /play_media with tag_list and no parent container (tag-random mode).
 */
async function shuffle_library_play() {
    let tags = [];
    const tagListEl = document.getElementById("tag_list_group");
    if (tagListEl) {
        tags = get_selected_checkboxes(tagListEl);
    }
    if (!tags.length && currentLibraryKey && LIBRARY_TAG_MAP[currentLibraryKey]) {
        tags = [LIBRARY_TAG_MAP[currentLibraryKey]];
    }
    if (!tags.length) {
        // Default shuffle across movies if nothing selected
        tags = ["movie"];
    }
    // Use a dummy content_id of 0 — server needs an id path; pick first from recently added via home
    try {
        const homeRes = await fetch("/library/home");
        if (!homeRes.ok) {
            throw new Error("library home for shuffle failed");
        }
        const home = await homeRes.json();
        const pool = (home.recently_added || []).concat(home.recently_played || []);
        // Prefer items matching tag when available; otherwise any content
        let pick = pool.find((item) => {
            const itemTags = (item.user_tags || "").split(",").map((t) => t.trim());
            return tags.some((t) => itemTags.includes(t));
        }) || pool[0];
        if (!pick || !pick.id) {
            showScanToast("Nothing to shuffle — try Scan Media", true);
            return;
        }
        await play_media(pick.id, pick.parent_container_id || null);
    } catch (e) {
        console.error(e);
        showScanToast("Shuffle play failed", true);
    }
}

function edit_metadata_modal_save(content_data, reference_item) {
    content_data["img_src"] = document.getElementById("modal_text_area_image_url").value
    content_data["description"] = document.getElementById("modal_text_area_description").value
    fetchAndSetData('/update_media_metadata', content_data).then(response_data => {
        if (response_data["img_src"] !== undefined) {
            if ('img_src' in response_data && 'img_url' in response_data) {
                reference_item.querySelector("#content_img").src = response_data['img_url'];
            }
            reference_item.querySelector('#content_img').src = response_data["img_url"];
            reference_item.querySelector('#content_img').dataset.img_src = response_data["img_src"];
        }
    }).catch(error => {
        console.error('Error:', error);
    });
}

function update_tag_content(url, content_data) {
    fetchAndSetData(url, content_data).then(response_data => {
        if (response_data["user_tags"] !== undefined) {
            const tagTitles = response_data["user_tags"].split(',');
            createTagButtons(tagTitles, content_data)
        }
    }).catch(error => {
        console.error('Error:', error);
    });
}

function add_tag_to_content(content_data) {
    update_tag_content('/add_tag_to_content', content_data)
}

function remove_tag_from_content(content_data) {
    update_tag_content('/remove_tag_from_content', content_data)
}

function create_tag_button_element(text, data) {
    const btnGroup = document.createElement('div');
    btnGroup.classList.add('btn-group', 'role', 'group', 'aria-label');

    const disabledButton = document.createElement('button');
    disabledButton.type = 'button';
    disabledButton.classList.add('btn', 'btn-primary', 'disabled');
    disabledButton.textContent = text;

    const deleteButton = document.createElement('button');
    deleteButton.type = 'button';
    deleteButton.classList.add('btn', 'btn-danger');

    const deleteIcon = document.createElement('i');
    deleteIcon.classList.add('bi', 'bi-trash');
    deleteButton.appendChild(deleteIcon);
    deleteIcon.addEventListener("click", function() {
        var copy = {...data};
        copy["tag_title"] = text
        remove_tag_from_content(copy)
    });

    btnGroup.appendChild(disabledButton);
    btnGroup.appendChild(deleteButton);

    return btnGroup;
}
function createTagButtons(tagTitles, data) {
    const container = document.getElementById('modal_user_tags'); // Replace with your container ID
    container.innerHTML = '';
    tagTitles.forEach(tagTitle => {
        const tag_group_item = create_tag_button_element(tagTitle, data);
        container.appendChild(tag_group_item);
    });
}

function populate_modal_tag_select_list(tagTitles) {
    user_tag_select = document.getElementById("user_tag_select")
    user_tag_select.innerHTML = ''
    tagTitles.forEach(tagTitle => {
        const tag_select_item = document.createElement('option');
        tag_select_item.value = tagTitle
        tag_select_item.innerHTML = tagTitle
        user_tag_select.appendChild(tag_select_item);
    });
}

function edit_metadata_modal_open(data, title, img_src, description, tags, reference_item) {
    document.getElementById("modal_title").innerHTML = title;
    document.getElementById("modal_text_area_image_url").value = img_src;
    document.getElementById("modal_text_area_description").value = description;

    const tagTitles = tags.split(',');
    createTagButtons(tagTitles, data)

    get_tag_list().then(tagTitles => {
        populate_modal_tag_select_list(tagTitles)
    });
    user_tag_select_button = document.getElementById("user_tag_select_button")
    user_tag_select_button.removeEventListener('click', modal_metadata_select_tag_click_handler);
    modal_metadata_select_tag_click_handler = (event) => {
        const selectElement = document.getElementById('user_tag_select');
        const selectedOption = selectElement.options[selectElement.selectedIndex];
        var copy = {...data};
        copy["tag_title"] = selectedOption.value;
        add_tag_to_content(copy)
    };
    user_tag_select_button.addEventListener('click', modal_metadata_select_tag_click_handler);

    save_button = document.getElementById("modal_metadata_save")
    save_button.removeEventListener('click', modal_metadata_save_click_handler);
    modal_metadata_save_click_handler = (event) => {
        edit_metadata_modal_save(data, reference_item);
    };
    save_button.addEventListener('click', modal_metadata_save_click_handler);
}

function showScanToast(message, isError) {
    const toast = document.getElementById("scan_toast");
    if (!toast) {
        return;
    }
    toast.hidden = false;
    toast.classList.toggle("alert-success", !isError);
    toast.classList.toggle("alert-danger", !!isError);
    toast.textContent = message;
    setTimeout(() => {
        toast.hidden = true;
    }, 4000);
}

async function scan_media_directories() {
    var url = "/scan_media_directories";
    let data = {};
    var disable_class = "disabled";
    var button_id = "scan_media_button";
    var button_element = document.getElementById(button_id);
    if (!button_element || button_element.classList.contains(disable_class)) {
        return;
    }

    button_element.classList.add(disable_class);
    try {
        let response = await fetch(url, {
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": JSON.stringify(data),
        });
        let response_data = {};
        try {
            response_data = await response.json();
        } catch (e) {
            response_data = {};
        }
        const status = response_data.status || (response.ok ? "ok" : "error");
        if (status === "ok") {
            showScanToast(response_data.message || "Scan complete", false);
            if (currentLibraryKey) {
                load_library(currentLibraryKey);
            } else {
                load_library_home();
            }
        } else if (status === "busy") {
            showScanToast(response_data.message || "Scan already in progress", true);
        } else {
            showScanToast(response_data.message || "Scan failed", true);
        }
    } catch (error) {
        console.error(error);
        showScanToast("Scan failed", true);
    }
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

                    if (response_data.content_id && response_data.media_runtime != null) {
                        postPlaybackProgress(
                            response_data.content_id,
                            response_data.media_runtime,
                            response_data.media_duration
                        );
                    }
                }
            }
        }
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
    var chromecast_disconnect_button = document.getElementById("chromecast_disconnect_button");
    if (chromecast_disconnect_button !== null)
    {
        chromecast_disconnect_button.addEventListener("click", disconnectChromecast);
    }
    var local_play_button = document.getElementById("local_play_button");
    if (local_play_button !== null)
    {
        local_play_button.addEventListener("click", connect_local_player);
    }
    getChromecastList();
    setNavbarLinks();
    setMediaControlButtons();
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
            get_next_media();
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
