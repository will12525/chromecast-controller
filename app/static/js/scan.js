/* Phase 4: scan.js — plain global script (no bundler). */
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

const SCAN_POLL_INTERVAL_MS = 1000;
const SCAN_POLL_MAX_MS = 30 * 60 * 1000; // 30 min safety cap

async function fetchScanStatus() {
    const response = await fetch("/scan_status", {method: "GET"});
    if (!response.ok) {
        throw new Error("HTTP status scan_status: " + response.status);
    }
    return response.json();
}

function refreshLibraryAfterScan() {
    if (currentLibraryKey) {
        load_library(currentLibraryKey);
    } else {
        load_library_home();
    }
}

/**
 * Poll GET /scan_status until idle, then surface last_result and refresh shelves.
 */
async function pollScanUntilIdle(buttonElement) {
    const startedAt = Date.now();
    showScanToast("Scanning media…", false);
    while (Date.now() - startedAt < SCAN_POLL_MAX_MS) {
        await new Promise((r) => setTimeout(r, SCAN_POLL_INTERVAL_MS));
        let statusData = {};
        try {
            statusData = await fetchScanStatus();
        } catch (e) {
            console.error(e);
            continue;
        }
        if (statusData.status === "busy" || statusData.scanning || statusData.transfer_in_progress) {
            const detail = statusData.transfer_in_progress
                ? "Syncing from server…"
                : "Scanning media…";
            showScanToast(detail, false);
            continue;
        }
        // Idle — prefer last_result from the finished job
        const last = statusData.last_result || {};
        const lastStatus = last.status || "ok";
        if (lastStatus === "error") {
            showScanToast(last.message || "Scan failed", true);
        } else {
            showScanToast(last.message || "Scan complete", false);
            refreshLibraryAfterScan();
        }
        return;
    }
    showScanToast("Scan is still running — refresh later", true);
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
        // If a scan is already running (another tab/client), just poll it
        try {
            const existing = await fetchScanStatus();
            if (existing.status === "busy" || existing.scanning) {
                showScanToast(existing.message || "Scan already in progress", false);
                await pollScanUntilIdle(button_element);
                return;
            }
        } catch (e) {
            console.warn("scan_status precheck failed", e);
        }

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
        if (status === "started" || status === "ok" || status === "busy") {
            // Background job: poll until complete (also handles concurrent busy)
            await pollScanUntilIdle(button_element);
        } else {
            showScanToast(response_data.message || "Scan failed", true);
        }
    } catch (error) {
        console.error(error);
        showScanToast("Scan failed", true);
    } finally {
        button_element.classList.remove(disable_class);
    }
}
