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

async function connectChromecast(sel) {
    var url = "/connect_chromecast";
    let data = {
        "chromecast_id": sel.options[sel.selectedIndex].text
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
            var select_connected_chromecasts = document.getElementById("select_connected_to_chromecast_id");
            // Remove existing connection options
            var i, L = select_connected_chromecasts.options.length - 1;
            for(i = L; i > 0; i--) {
                select_connected_chromecasts.remove(i);
            }

            // Add new connection option
            var option = document.createElement("option");
            option.text = response_data?.chromecast_id;
            select_connected_chromecasts.add(option);
        }
    }
};

async function disconnectChromecast(sel) {
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
        sel.remove(sel.selectedIndex)
    }
};

async function chromecast_command(chromecast_cmd_id) {
    var url = "/chromecast_command";
    let data = {
        "chromecast_cmd_id": chromecast_cmd_id
    };
    console.log(data)
    // Send POST request
    let response = await fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });
    console.log(response.status)
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

                    mediaTimeOutputId.value = media_runtime

                }
            }
        }
    }
}

setInterval(updateSeekSelector, 1000);