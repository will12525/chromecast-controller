default_image_array = ['10.jpg', '11.jpg', '12.png', '13.png', '14.png', '15.png', '16.png', '1.webp', '2.webp', '3.jpg', '4.jpg', '5.jpg', '6.jpg', '7.jpg', '8.jpg', '9.jpg']

let modal_metadata_save_click_handler = (event) => {
}
let modal_metadata_select_tag_click_handler = (event) => {
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
    template.querySelector("#content_img").src = "http://192.168.1.175:8000/" + content_data['img_src'];
    template.querySelector("#content_img").dataset.img_src = content_data['img_src'];

    fragment.appendChild(template)
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
        template.querySelector("#content_img").src = "http://192.168.1.175:8000/" + parent_container['img_src'];
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
            update_media_container(response_data)
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
function createTagElements(tagTitles) {
    const container = document.getElementById('tag_list_group'); // Replace with your container ID
    container.innerHTML = '';
    tagTitles.forEach(tagTitle => {
        container.appendChild(generate_tag_list_element(tagTitle));
    });
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
    let data = {
        "tag_list": get_selected_checkboxes(document.getElementById("tag_list_group")),
        "container_txt_search": document.getElementById("container_txt_search").value,
        "content_txt_search": document.getElementById("content_txt_search").value,
        "container_dict": {}
    };
    queryDB(data)
}

async function get_next_media(event) {
    var url = "/get_next_media";
    if (event.target.dataset.content_id !== undefined && event.target.dataset.parent_container_id !== undefined) {
        let data = {
            "content_id": parseInt(event.target.dataset.content_id),
            "parent_container_id": parseInt(event.target.dataset.parent_container_id)
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
        videoPlayer.load();
        videoPlayer.scrollIntoView();
        videoPlayer.play();
    } catch (error) {
        console.error('Error playing video:', error);
    }
}

async function play_media(content_id, parent_container_id=null) {
    var url = "/play_media";
    let data = {
        "content_id": content_id,
        "parent_container_id": parent_container_id
    };
    // Send POST request
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });

    if (!response.ok) {
        throw new Error("HTTP status connect_local_player: " + response.status);
    } else {
        let response_data = await response.json();
        if (response_data["local_play_url"] !== undefined) {
            update_local_media_player(response_data)
        }
    }
}

function edit_metadata_modal_save(content_data, reference_item) {
    content_data["img_src"] = document.getElementById("modal_text_area_image_url").value
    content_data["description"] = document.getElementById("modal_text_area_description").value
    fetchAndSetData('/update_media_metadata', content_data).then(response_data => {
        if (response_data["img_src"] !== undefined) {
            reference_item.querySelector('#content_img').src = "http://192.168.1.175:8000/" + response_data["img_src"];
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
    var scan_media_button = document.getElementById("scan_media_button");
    var editor_button = document.getElementById("editor_button");

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
    let data = {
        "tag_list": [],
        "container_dict": {"container_id": container_id}
    };
    queryDB(data)
}

async function load_tv_shows() {
    let data = {
        "tag_list": ["tv show"],
        "container_dict": {}
    };
    queryDB(data)
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
    load_tv_shows()
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
        setup_media_page()
    }
    if(document.getElementById('local_video_player') !== null) {
        document.getElementById('local_video_player').addEventListener('ended', get_next_media)
    }

    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
});
