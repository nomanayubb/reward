/* Game Host — platform page side.
 *
 * Hosts a game iframe and proxies the Game SDK protocol to the platform API
 * using the page's own authenticated session. Validates that messages come
 * from the hosted iframe (event.source) and from the expected origin.
 *
 * Usage:
 *   initGameHost({
 *     iframe: document.getElementById("game-frame"),
 *     gameSlug: "tap-target",
 *     gameOrigin: "http://localhost:8000",
 *     user: {...}, config: {...},
 *   });
 */
(function (global) {
  "use strict";

  var API_BASE = "/api/v1";

  function getCookie(name) {
    var match = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]*)"));
    return match ? decodeURIComponent(match[2]) : "";
  }

  function api(path, options) {
    options = options || {};
    var headers = { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") };
    return fetch(API_BASE + path, {
      method: options.method || "GET",
      headers: headers,
      credentials: "same-origin",
      body: options.body ? JSON.stringify(options.body) : undefined,
    }).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (data) {
        if (!response.ok) {
          throw new Error(data.detail || "Request failed (" + response.status + ")");
        }
        return data;
      });
    });
  }

  global.initGameHost = function (options) {
    var iframe = options.iframe;
    var gameSlug = options.gameSlug;
    var gameOrigin = options.gameOrigin || "";
    var user = options.user || null;
    var config = options.config || {};
    var sessionToken = null;
    var lastResult = null;

    function reply(id, ok, result, error) {
      iframe.contentWindow.postMessage(
        { source: "game-host", id: id, ok: ok, result: result, error: error },
        gameOrigin || "*"
      );
    }

    function handle(action, payload) {
      if (action === "start") {
        return api("/games/" + encodeURIComponent(gameSlug) + "/sessions/", {
          method: "POST",
          body: {},
        }).then(function (session) {
          sessionToken = session.session_token;
          return session;
        });
      }

      if (action === "event") {
        if (!sessionToken) throw new Error("No active session");
        return api("/games/sessions/" + sessionToken + "/events/", {
          method: "POST",
          body: { type: payload.name, payload: payload.data || {} },
        });
      }

      if (action === "score") {
        if (!sessionToken) throw new Error("No active session");
        return api("/games/sessions/" + sessionToken + "/events/", {
          method: "POST",
          body: { type: "score", payload: { score: payload.score } },
        });
      }

      if (action === "end") {
        if (!sessionToken) throw new Error("No active session");
        return api("/games/sessions/" + sessionToken + "/end/", {
          method: "POST",
          body: { score: payload.score },
        }).then(function (result) {
          lastResult = result;
          return result;
        });
      }

      if (action === "reward") return Promise.resolve(lastResult || { status: "none" });
      if (action === "user") return Promise.resolve(user);
      if (action === "config") return Promise.resolve(config);
      throw new Error("Unknown action: " + action);
    }

    global.addEventListener("message", function (event) {
      if (!iframe.contentWindow || event.source !== iframe.contentWindow) return;
      if (gameOrigin && gameOrigin !== "null" && event.origin !== gameOrigin) return;

      var data = event.data || {};
      if (data.source !== "game-sdk" || !data.id) return;

      Promise.resolve()
        .then(function () {
          return handle(data.action, data.payload || {});
        })
        .then(function (result) {
          reply(data.id, true, result);
        })
        .catch(function (error) {
          reply(data.id, false, null, String((error && error.message) || error));
        });
    });
  };
})(window);
