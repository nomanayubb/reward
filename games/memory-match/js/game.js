/* Memory Match — original game using the Game SDK.
 * Score: 100 per pair, minus 10 per extra move (moves beyond the minimum).
 */
(function () {
  "use strict";

  var PAIR_COUNT = 8;
  var SYMBOLS = ["★", "●", "▲", "■", "◆", "✦", "✚", "♥"];
  var REVEAL_MS = 700;

  var board = document.getElementById("board");
  var pairsEl = document.getElementById("pairs");
  var movesEl = document.getElementById("moves");
  var overlay = document.getElementById("overlay");
  var startButton = document.getElementById("start-button");
  var connectionEl = document.getElementById("connection");

  var firstCard = null;
  var lock = false;
  var matched = 0;
  var moves = 0;
  var running = false;
  var connected = false;

  function setConnection(text, ok) {
    connectionEl.textContent = text;
    connectionEl.classList.toggle("ok", !!ok);
  }

  function shuffle(list) {
    for (var i = list.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = list[i];
      list[i] = list[j];
      list[j] = tmp;
    }
    return list;
  }

  function score() {
    return Math.max(0, matched * 100 - Math.max(0, moves - PAIR_COUNT) * 10);
  }

  function buildBoard() {
    board.innerHTML = "";
    var cards = [];
    for (var i = 0; i < PAIR_COUNT; i++) {
      cards.push(SYMBOLS[i]);
      cards.push(SYMBOLS[i]);
    }
    shuffle(cards).forEach(function (symbol) {
      var card = document.createElement("button");
      card.type = "button";
      card.className = "card";
      card.dataset.symbol = symbol;
      card.textContent = "";
      card.addEventListener("click", function () {
        reveal(card);
      });
      board.appendChild(card);
    });
  }

  function reveal(card) {
    if (!running || lock || card.classList.contains("open") || card.classList.contains("done")) {
      return;
    }

    card.classList.add("open");
    card.textContent = card.dataset.symbol;

    if (!firstCard) {
      firstCard = card;
      return;
    }

    moves += 1;
    movesEl.textContent = String(moves);

    if (firstCard.dataset.symbol === card.dataset.symbol) {
      firstCard.classList.add("done");
      card.classList.add("done");
      firstCard = null;
      matched += 1;
      pairsEl.textContent = String(matched);
      if (connected) GameSDK.reportScore(score()).catch(function () {});
      if (matched === PAIR_COUNT) finish();
      return;
    }

    lock = true;
    var previous = firstCard;
    firstCard = null;
    setTimeout(function () {
      previous.classList.remove("open");
      previous.textContent = "";
      card.classList.remove("open");
      card.textContent = "";
      lock = false;
    }, REVEAL_MS);
  }

  function startGame() {
    matched = 0;
    moves = 0;
    firstCard = null;
    lock = false;
    running = true;
    pairsEl.textContent = "0";
    movesEl.textContent = "0";
    overlay.classList.add("hidden");
    buildBoard();

    if (connected) {
      GameSDK.startSession().catch(function (error) {
        setConnection("session error: " + error.message, false);
        connected = false;
      });
      GameSDK.reportEvent("game_start", { pairs: PAIR_COUNT }).catch(function () {});
    }
  }

  function finish() {
    running = false;
    overlay.classList.remove("hidden");
    overlay.querySelector("h1").textContent = "All pairs found!";
    overlay.querySelector("p").textContent = "Moves: " + moves + " · Score: " + score();
    startButton.textContent = "Play again";

    if (connected) {
      GameSDK.endSession(score())
        .then(function (result) {
          overlay.querySelector("p").textContent =
            "Moves: " + moves + " · Score: " + score() + " · " + describe(result);
        })
        .catch(function (error) {
          overlay.querySelector("p").textContent =
            "Moves: " + moves + " · could not close session (" + error.message + ")";
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

  startButton.addEventListener("click", startGame);
})();
