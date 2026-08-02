/**
 * Phase 4 entrypoint — kept for templates that still load app.js alone.
 * Prefer loading app/static/js/* modules (see index.html / editor.html).
 * When this file is loaded last after js/*.js, it is a no-op bootstrap marker.
 *
 * Module order:
 *   js/shared.js → js/chromecast.js → js/player_controls.js → js/browse.js
 *   → js/playback.js → js/scan.js → js/library.js → js/app_main.js
 */
/* global setup_nav_bars, setup_media_page */
// Intentional no-op when modules already registered the DOMContentLoaded handlers
// via app_main.js. If only this file is present (legacy), handlers never attach —
// templates must load the js/* chain.
