/* Tap Target — a minimal, complete game that uses the Game SDK.
 *
 * The game only reports telemetry and a final score; the platform validates
 * the session server-side and decides the reward (see documentation/).
 */
(function () {
  "use strict";

  var ROUND_SECONDS = 30;
  var SPAWN_INTERVAL_MS = 700;
  var TARGET_LIFETIME_MS = 900;

  var board = document.getElementById("board");
  var scoreEl = document.getElementById("score");
  var timeEl = document.getElementById("time");
  var overlay = document.getElementById("overlay");
  var startButton = document.getElementById("start-button");
  var connectionEl = document.getElementById("connection");

  var score = 0;
  var timeLeft = ROUND_SECONDS;
  var running = false;
  var timerId = null;
  var spawnId = null;
  var currentTarget = null;
  var connected = false;

  function setConnection(text, ok) {
    connectionEl.textContent = text;
    connectionEl.classList.toggle("ok", !!ok);
  }

  function startGame() {
    score = 0;
    timeLeft = ROUND_SECONDS;
    running = true;
    scoreEl.textContent = "0";
    timeEl.textContent = String(timeLeft);
    overlay.classList.add("hidden");

    if (connected) {
      GameSDK.startSession().catch(function (error) {
        setConnection("session error: " + error.message, false);
        connected = false;
      });
      GameSDK.reportEvent("game_start", { round_seconds: ROUND_SECONDS }).catch(function () {});
    }

    timerId = setInterval(tick, 1000);
    spawnLoop();
  }

  function tick() {
    timeLeft -= 1;
    timeEl.textContent = String(timeLeft);
    if (timeLeft <= 0) endGame();
  }

  function spawnLoop() {
    spawn();
    spawnId = setInterval(spawn, SPAWN_INTERVAL_MS);
  }

  function spawn() {
    if (!running) return;
    clearTarget();

    var target = document.createElement("button");
    target.type = "button";
    target.className = "target";
    target.setAttribute("aria-label", "target");

    var size = 44 + Math.random() * 36;
    var rect = board.getBoundingClientRect();
    target.style.width = size + "px";
    target.style.height = size + "px";
    target.style.left = Math.random() * Math.max(0, rect.width - size) + "px";
    target.style.top = Math.random() * Math.max(0, rect.height - size) + "px";

    target.addEventListener("pointerdown", hit);
    board.appendChild(target);
    currentTarget = target;

    setTimeout(function () {
      if (target === currentTarget) clearTarget();
    }, TARGET_LIFETIME_MS);
  }

  function clearTarget() {
    if (currentTarget) {
      currentTarget.remove();
      currentTarget = null;
    }
  }

  function hit(event) {
    event.preventDefault();
    if (!running) return;
    score += 1;
    scoreEl.textContent = String(score);
    if (connected) GameSDK.reportScore(score).catch(function () {});
    clearTarget();
  }

  function endGame() {
    running = false;
    clearInterval(timerId);
    clearInterval(spawnId);
    clearTarget();

    overlay.classList.remove("hidden");
    overlay.querySelector("h1").textContent = "Time!";
    overlay.querySelector("p").textContent = "Score: " + score;
    startButton.textContent = "Play again";

    if (connected) {
      GameSDK.endSession(score)
        .then(function (result) {
          overlay.querySelector("p").textContent =
            "Score: " + score + " · " + describeResult(result);
        })
        .catch(function (error) {
          overlay.querySelector("p").textContent =
            "Score: " + score + " · could not close session (" + error.message + ")";
        });
    }
  }

  function describeResult(result) {
    if (!result) return "session closed";
    if (result.status === "invalidated") return "session too short for a reward";
    return "session complete — check your wallet";
  }

  if (window.GameSDK && GameSDK.isConnected()) {
    connected = true;
    setConnection("connected", true);
  } else {
    setConnection("offline mode — open from the platform to earn", false);
  }

  startButton.addEventListener("click", startGame);
})();
