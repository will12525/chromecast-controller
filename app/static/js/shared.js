/* Phase 4: shared.js — plain global script (no bundler). */
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
