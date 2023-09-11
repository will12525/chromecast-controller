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

function connectChromecast(sel) {

    fetch('/connect_chromecast', {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({a: 1, b: 'Textual content'})
    });


    fetch("/connect_chromecast", {
        method: "POST" // default, so we can ignore

    })
    console.log(sel.options[sel.selectedIndex].text)
//    console.log(select_scan_chromecast_id.options[select_scan_chromecast_id.selectedIndex].text)
};

function disconnectChromecast() {
    console.log(select_scan_chromecast_id.options[select_scan_chromecast_id.selectedIndex].text)
};

function print_hello()
{

    console.log("Hello world")
};

function update_mediaTime() {
    mediaTime = mediaTimeInputId.value.toHHMMSS();
    mediaTimeInputId.title = mediaTime;
    mediaTimeOutputId.value = mediaTime;
};