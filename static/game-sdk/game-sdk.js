/* Game SDK — iframe side.
 *
 * Runs inside the sandboxed game iframe and talks to the platform host page
 * via postMessage only. Game code never sees cookies, tokens or the wallet.
 *
 * The platform loads the game with ?origin=<platform-origin>; messages from
 * any other origin are ignored.
 */
(function (global) {
  "use strict";

  var params = new URLSearchParams(global.location.search);
  var PARENT_ORIGIN = params.get("origin") || "*";
  var pending = {};
  var counter = 0;

  function call(action, payload) {
    return new Promise(function (resolve, reject) {
      var id = "sdk-" + ++counter + "-" + Date.now();
      pending[id] = { resolve: resolve, reject: reject };
      global.parent.postMessage(
        { source: "game-sdk", id: id, action: action, payload: payload || {} },
        PARENT_ORIGIN
      );
    });
  }

  global.addEventListener("message", function (event) {
    if (PARENT_ORIGIN !== "*" && event.origin !== PARENT_ORIGIN) return;
    var data = event.data || {};
    if (data.source !== "game-host" || !data.id || !pending[data.id]) return;
    var entry = pending[data.id];
    delete pending[data.id];
    if (data.ok) {
      entry.resolve(data.result);
    } else {
      entry.reject(new Error(data.error || "Game host error"));
    }
  });

  global.GameSDK = {
    /** Start a server-side session. Returns { session_token, status, ... }. */
    startSession: function () {
      return call("start");
    },
    /** Telemetry event (never a reward by itself). */
    reportEvent: function (name, data) {
      return call("event", { name: name, data: data || {} });
    },
    /** Report an intermediate score (telemetry). */
    reportScore: function (score) {
      return call("score", { score: score });
    },
    /** End the session; the server validates and decides the reward. */
    endSession: function (score) {
      return call("end", { score: score });
    },
    /** Last end-of-session result (status only, never a direct payout). */
    requestReward: function () {
      return call("reward");
    },
    /** Non-sensitive profile fields only. */
    getUser: function () {
      return call("user");
    },
    /** Public per-game configuration. */
    getConfiguration: function () {
      return call("config");
    },
    /** False when the game is opened directly (not inside the platform). */
    isConnected: function () {
      return global.parent !== global;
    },
  };
})(window);
