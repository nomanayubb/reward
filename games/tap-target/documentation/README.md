# Tap Target

A minimal, complete HTML5 game used as the reference implementation for the
platform's Game SDK.

## What it is

Circles appear on the board one at a time. Tap/click a circle before it
vanishes to score a point. The round lasts 30 seconds. At the end the game
reports the score to the platform; the platform validates the session and
decides the reward (the game cannot pay itself).

## Controls

- Pointer/touch: tap the circle
- Keyboard: focus + Enter/Space works because targets are real buttons

## How to run

- **Inside the platform (recommended):** open `/play/tap-target/` while logged
  in. The page hosts this game in an iframe and wires the SDK.
- **Standalone (development):** open `game.html` directly. The game detects it
  is not connected and runs in offline mode (no rewards).

## Files

```
tap-target/
  game.html              # entry point
  js/game.js             # game logic + SDK calls
  css/style.css          # styling
  documentation/         # this folder
```

## Scoring

- +1 point per tapped target
- Session duration must meet the platform's minimum (`Game.min_session_seconds`)
  or the session is invalidated and pays nothing

## Reward configuration

Rewards are configured in the platform admin (`GameRewardRule`), not in the
game code. See `REWARD_RULES.md` for examples.
