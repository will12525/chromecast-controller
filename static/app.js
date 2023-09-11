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

function sendPost(url, data) {
    fetch(url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    });
}

function connectChromecast(sel) {
    let data = {
        "chromecast_id": sel.options[sel.selectedIndex].text
    };
    sendPost("/connect_chromecast", data);
};

function disconnectChromecast(sel) {
    let data = {
        "chromecast_id": sel.options[sel.selectedIndex].text
    };
    sendPost("/disconnect_chromecast", data);
};

function print_hello()
{

    console.log("Hello world");
};

function update_mediaTime() {
    mediaTime = mediaTimeInputId.value.toHHMMSS();
    mediaTimeInputId.title = mediaTime;
    mediaTimeOutputId.value = mediaTime;
};