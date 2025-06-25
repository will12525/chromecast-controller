async function update_editor_log(response_data) {
    editor_txt_file_log = document.getElementById("editor_txt_file_log");
    prepend_text = "";

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

async function populate_splitter_form(response_data) {

    const form_editor_page = document.getElementById("form_editor_page");
    if (response_data["playlist_title"] !== undefined) {
        var playlist_title = form_editor_page.querySelector("#playlist_title");
        if (playlist_title) {
            playlist_title.value = response_data["playlist_title"];
        }
    }
    if (response_data["splitter_content"] !== undefined && response_data["splitter_content"].length) {
        var form_input_groups = form_editor_page.querySelectorAll(".content_input_group");
        var form_need_difference = response_data["splitter_content"].length - form_input_groups.length
        if (form_need_difference > 0) {
            var add_row_button = form_editor_page.querySelector('button[name="add_row_button"]');
            if(add_row_button) {
                for (let i = 0; i < form_need_difference; i++) {
                    add_row_button.click()
                }
            }
        }
        form_input_groups = form_editor_page.querySelectorAll(".content_input_group");
        for (let i = 0; i < response_data["splitter_content"].length; i++) {
            splitter_content_data = response_data["splitter_content"][i];
            if (form_input_groups[i] !== undefined) {
                var form_inputs = form_input_groups[i].querySelectorAll('input');
                form_inputs.forEach(form_input => {
                    if (form_input.name in splitter_content_data) {
                        if (form_input.type == "checkbox") {
                            form_input.checked = splitter_content_data[form_input.name]
                        } else {
                            form_input.value = splitter_content_data[form_input.name]
                        }
                    }
                });
            }
        }
    }
}

async function populate_splitter_process_queue(response_data) {
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
    document.getElementById("editor_process_metadata_end_time").innerText = response_data["process_end_time"];
    document.getElementById("editor_process_metadata_queue_size").innerText = response_data["process_queue_size"];
    document.getElementById("editor_process_queue").replaceChildren(...process_queue_list)
}

async function update_editor_webpage(response_data) {
    if (response_data["selected_txt_file_title"] !== undefined) {
        document.getElementById("editor_txt_file_name").innerHTML = response_data["selected_txt_file_title"];
    }
    if (response_data["selected_editor_file_content"] !== undefined && response_data["selected_editor_file_content"]["media_type"] !== undefined) {
        update_selected_media_type(response_data["selected_editor_file_content"]["media_type"])
        populate_splitter_form(response_data["selected_editor_file_content"])
    } else {
        update_selected_media_type("RAW")
    }
    if (response_data["error"] !== undefined) {
        update_editor_log(response_data?.error)
    }
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
}

async function update_editor_process_queue(response_data) {
    console.log(response_data)
    if (response_data["process_log"] !== undefined) {
        response_data?.process_log.forEach((element) => update_editor_log(element));
    }

    if (response_data["process_queue"] !== undefined && response_data["process_name"] !== undefined && response_data["process_end_time"] !== undefined && response_data["process_queue_size"] !== undefined) {
        populate_splitter_process_queue(response_data)
    }
    if (response_data["error"] !== undefined) {
        update_editor_log(response_data?.error)
    }
}

async function clear_editor_log() {
    document.getElementById("editor_txt_file_log").value = "";
}

async function load_txt_file(file_name) {
    fetchAndSetData('/load_txt_file', {"editor_txt_file_name": file_name}).then(response_data => {
        update_editor_webpage(response_data);
        if (document.getElementById("load_media_for_local_play").checked && response_data["local_play_url"] !== undefined) {
            update_local_media_player(response_data)
        }
        update_editor_process_queue(response_data);
    }).catch(error => {
        console.error('Error:', error);
    });
}

async function save_txt_file(content_data) {
    fetchAndSetData('/save_txt_file', content_data).then(response_data => {
        update_editor_process_queue(response_data);
    }).catch(error => {
        console.error('Error:', error);
    });
}

async function validate_txt_file(content_data) {
    fetchAndSetData('/validate_txt_file', content_data).then(response_data => {
        update_editor_process_queue(response_data);
    }).catch(error => {
        console.error('Error:', error);
    });
}

async function process_txt_file(content_data) {
    fetchAndSetData('/process_txt_file', content_data).then(response_data => {
        update_editor_process_queue(response_data);
    }).catch(error => {
        console.error('Error:', error);
    });
}
async function delete_txt_file(content_data) {
    fetchAndSetData('/delete_txt_file', content_data).then(response_data => {
        update_editor_process_queue(response_data);
    }).catch(error => {
        console.error('Error:', error);
    });
}

async function updateEditorMetadata() {
    fetchAndSetData('/process_metadata', {}).then(response_data => {
        update_editor_process_queue(response_data); // Do something with the data
    }).catch(error => {
        console.error('Error:', error);
    });
}

async function update_selected_media_type(selected_content) {
    var media_type_template_str = "raw_editor_template";
    var append_row_val = ""

    document.getElementById("media_type_dropdown").innerHTML = selected_content;
    if (selected_content == "RAW") {
        media_type_template_str = "raw_editor_template"
        append_row_val = "base_raw_group"
    } else if (selected_content == "TV") {
        media_type_template_str = "tv_editor_template"
        append_row_val = "base_tv_group"
    } else if (selected_content == "MOVIE") {
        media_type_template_str = "movie_editor_template"
    } else if (selected_content == "BOOK") {
        media_type_template_str = "book_editor_template"
    } else {
        console.log("Unknown")
    }
    const templateElement = document.getElementById(media_type_template_str);
    const templateContent = templateElement.innerHTML;
    const targetElement = document.getElementById("form_editor_page");
    targetElement.innerHTML = templateContent;
    if (append_row_val)
    {
        var add_row_button = document.querySelector('button[name="add_row_button"]');
        add_row_button.addEventListener('click', () => {
            add_content_row(append_row_val)
        });
    }
}

async function add_content_row(template_id) {
    var form_editor_page = document.getElementById("form_editor_page")
    var empty_div = document.createElement("div");
    empty_div.classList.add("col-md-2")
    form_editor_page.appendChild(empty_div);
    var cloned_element = document.getElementById(template_id).cloneNode(true)
    const form_inputs = cloned_element.querySelectorAll('input'); // Select visible inputs
    form_inputs.forEach(input => {
        input.value = null
    });
    form_editor_page.appendChild(cloned_element)
}

function extract_form_data() {
    const form_editor_page = document.getElementById("form_editor_page");

    var media_type = document.getElementById("media_type_dropdown").innerHTML.trim()
    let form_data = {
        "splitter_content":[],
        "media_type": media_type,
        "file_name": document.getElementById("editor_txt_file_name").textContent
    }
    var playlist_title = form_editor_page.querySelector("#playlist_title");
    if (playlist_title)
    {
        form_data["playlist_title"] = playlist_title.value
    }
    var form_input_groups = form_editor_page.querySelectorAll('.content_input_group'); // Select visible inputs
    if (form_input_groups.length > 0) { // Check if there are any groups
        form_input_groups.forEach(form_input_group => {
            const form_inputs = form_input_group.querySelectorAll('input');

            if (form_inputs.length > 0) { // Check if there are any inputs in the group
                let data = {};
                form_inputs.forEach(input => {
                    if (input.type == "text") {
                        data[input.name] = input.value;
                    } else if (input.type == "number") {
                        data[input.name] = parseInt(input.value)
                    } else if (input.type == "checkbox") {
                        data[input.name] = input.checked
                    }
                });
                const allValuesFilled = Object.values(data).every(value => {
                    if (typeof value === 'boolean') {
                        return true;
                    }
                    return value !== '';
                });
                if (allValuesFilled) {
                    form_data["splitter_content"].push(data);
                }
            }
        });
    }
    console.log(form_data)
    return form_data
}

async function handle_splitter_form_container_submit(event) {
    event.preventDefault(); // Prevent default form submission
    const clickedButton = event.submitter; // Get the clicked button
    // RAW: start_time, end_time
    // TV: Show title, media_title, season_index, episode_index, start_time, end_time
    // MOVIE: media_title, year, start_time, end_time
    // BOOK: media_title, author, start_time, end_time
    let form_data = extract_form_data();
    if (clickedButton.id === 'validate_button') {
        validate_txt_file(form_data)
    } else if (clickedButton.id === 'save_button') {
        save_txt_file(form_data)
    } else if (clickedButton.id === 'run_button') {
        process_txt_file(form_data)
    } else if (clickedButton.id === 'delete_button') {
        delete_txt_file(form_data)
    }
}

function setup_editor_page() {
    const media_type_btn_group = document.getElementById('media_type_btn_group');
    if (media_type_btn_group !== null)
    {
        media_type_btn_group.addEventListener('click', (event) => {
            if (event.target.tagName === 'A') {
                form_data = extract_form_data();
                update_selected_media_type(event.target.textContent)

                fetchAndSetData('/load_txt_file', {"editor_txt_file_name": form_data["file_name"]}).then(response_data => {
                    if (response_data["selected_editor_file_content"] !== undefined) {
                        populate_splitter_form(response_data["selected_editor_file_content"])
                    }
                }).catch(error => {
                    console.error('Error:', error);
                });
            }
        });
    }

    var editor_file_list = document.getElementById('editor_file_list');
    if (editor_file_list !== null)
    {
        editor_file_list.addEventListener('click', (event) => {
            if (event.target.tagName === 'A') {
                load_txt_file(event.target.textContent)
            }
        });
        const first_file_element = editor_file_list.querySelector('a');
        if (first_file_element) {
            load_txt_file(first_file_element.textContent)
        }
    }
    const form = document.getElementById('splitter_form_container');
    form.addEventListener('submit', handle_splitter_form_container_submit);
    setInterval(updateEditorMetadata, 5000);
}

document.addEventListener("DOMContentLoaded", function(event){
    if (document.getElementById("editor_content_input") !== null)
    {
        setup_editor_page()
    }

    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
});
