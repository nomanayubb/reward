/* Snake — original implementation using the Game SDK.
 * Score: +1 per food. Ends on wall/self collision or when the timer runs out.
 */
(function () {
  "use strict";

  var CELLS = 20;
  var TICK_MS = 140;
  var ROUND_SECONDS = 90;

  var canvas = document.getElementById("board");
  var ctx = canvas.getContext("2d");
  var scoreEl = document.getElementById("score");
  var timeEl = document.getElementById("time");
  var overlay = document.getElementById("overlay");
  var startButton = document.getElementById("start-button");
  var connectionEl = document.getElementById("connection");

  var snake = [];
  var direction = { x: 1, y: 0 };
  var nextDirection = { x: 1, y: 0 };
  var food = { x: 5, y: 5 };
  var score = 0;
  var timeLeft = ROUND_SECONDS;
  var running = false;
  var tickId = null;
  var timerId = null;
  var connected = false;

  var cell = function () {
    return canvas.width / CELLS;
  };

  function setConnection(text, ok) {
    connectionEl.textContent = text;
    connectionEl.classList.toggle("ok", !!ok);
  }

  function reset() {
    snake = [
      { x: 8, y: 10 },
      { x: 7, y: 10 },
      { x: 6, y: 10 },
    ];
    direction = { x: 1, y: 0 };
    nextDirection = { x: 1, y: 0 };
    score = 0;
    timeLeft = ROUND_SECONDS;
    scoreEl.textContent = "0";
    timeEl.textContent = String(timeLeft);
    placeFood();
    draw();
  }

  function placeFood() {
    do {
      food = {
        x: Math.floor(Math.random() * CELLS),
        y: Math.floor(Math.random() * CELLS),
      };
    } while (
      snake.some(function (part) {
        return part.x === food.x && part.y === food.y;
      })
    );
  }

  function draw() {
    var size = cell();
    ctx.fillStyle = "#10131a";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "#f87171";
    ctx.fillRect(food.x * size + 2, food.y * size + 2, size - 4, size - 4);

    snake.forEach(function (part, index) {
      ctx.fillStyle = index === 0 ? "#7dd3fc" : "#2563eb";
      ctx.fillRect(part.x * size + 1, part.y * size + 1, size - 2, size - 2);
    });
  }

  function step() {
    if (!running) return;
    direction = nextDirection;

    var head = {
      x: snake[0].x + direction.x,
      y: snake[0].y + direction.y,
    };

    var hitWall = head.x < 0 || head.y < 0 || head.x >= CELLS || head.y >= CELLS;
    var hitSelf = snake.some(function (part) {
      return part.x === head.x && part.y === head.y;
    });
    if (hitWall || hitSelf) {
      finish(hitWall ? "You hit the wall" : "You bit yourself");
      return;
    }

    snake.unshift(head);

    if (head.x === food.x && head.y === food.y) {
      score += 1;
      scoreEl.textContent = String(score);
      if (connected) GameSDK.reportScore(score).catch(function () {});
      placeFood();
    } else {
      snake.pop();
    }

    draw();
  }

  function turn(x, y) {
    if (!running) return;
    if (direction.x === -x && direction.y === -y) return; // no instant reverse
    nextDirection = { x: x, y: y };
  }

  function onKey(event) {
    var key = event.key;
    if (key === "ArrowUp" || key === "w" || key === "W") turn(0, -1);
    else if (key === "ArrowDown" || key === "s" || key === "S") turn(0, 1);
    else if (key === "ArrowLeft" || key === "a" || key === "A") turn(-1, 0);
    else if (key === "ArrowRight" || key === "d" || key === "D") turn(1, 0);
  }

  var touchStart = null;
  function onTouchStart(event) {
    touchStart = event.touches[0];
  }
  function onTouchEnd(event) {
    if (!touchStart) return;
    var touch = event.changedTouches[0];
    var dx = touch.clientX - touchStart.clientX;
    var dy = touch.clientY - touchStart.clientY;
    if (Math.abs(dx) > Math.abs(dy)) turn(dx > 0 ? 1 : -1, 0);
    else turn(0, dy > 0 ? 1 : -1);
    touchStart = null;
  }

  function startGame() {
    reset();
    running = true;
    overlay.classList.add("hidden");

    if (connected) {
      GameSDK.startSession().catch(function (error) {
        setConnection("session error: " + error.message, false);
        connected = false;
      });
      GameSDK.reportEvent("game_start", { round_seconds: ROUND_SECONDS }).catch(function () {});
    }

    tickId = setInterval(step, TICK_MS);
    timerId = setInterval(function () {
      timeLeft -= 1;
      timeEl.textContent = String(timeLeft);
      if (timeLeft <= 0) finish("Time!");
    }, 1000);
  }

  function finish(message) {
    running = false;
    clearInterval(tickId);
    clearInterval(timerId);

    overlay.classList.remove("hidden");
    overlay.querySelector("h1").textContent = message;
    overlay.querySelector("p").textContent = "Score: " + score;
    startButton.textContent = "Play again";

    if (connected) {
      GameSDK.endSession(score)
        .then(function (result) {
          overlay.querySelector("p").textContent =
            "Score: " + score + " · " + describe(result);
        })
        .catch(function (error) {
          overlay.querySelector("p").textContent =
            "Score: " + score + " · could not close session (" + error.message + ")";
        });
    }
  }

  function describe(result) {
    if (!result) return "session closed";
    if (result.status === "invalidated") return "session too short for a reward";
    return "check your wallet";
  }

  if (window.GameSDK && GameSDK.isConnected()) {
    connected = true;
    setConnection("connected", true);
  } else {
    setConnection("offline mode — open from the platform to earn", false);
  }

  document.addEventListener("keydown", onKey);
  canvas.addEventListener("touchstart", onTouchStart, { passive: true });
  canvas.addEventListener("touchend", onTouchEnd, { passive: true });
  startButton.addEventListener("click", startGame);
  reset();
})();
