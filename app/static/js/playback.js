/* Phase 4: playback.js — plain global script (no bundler). */
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
