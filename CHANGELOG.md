# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-03-28

### Added
- `GameUtils.js` - Frontend game state utilities with `applyMove` and `compareGameStates` functions
- `GameUtils.test.js` - Unit tests for GameUtils
- `useGameSounds` hook - Sound playback for move and capture actions
- `useGameNavigation` hook - Navigation blocking and leave confirmation
- `useJoinGame` hook - Join/rejoin game logic
- `WinnerModal`, `WaitingModal`, `LeaveConfirmationModal` components

### Changed
- Refactored `utils.py` into modular structure:
  - `board.py` - Board rules, move/capture connections, win conditions
  - `game_state.py` - Initial state, validation, apply move
  - `handlers.py` - Async handlers for game updates, cleanup, persistence
- `utils.py` now re-exports all symbols for backward compatibility
- `Game.jsx` broken into smaller hooks and components
- Optimistic state management added to WebSocket context

### Fixed
- `previousPosition` correctly set to `null` for placement moves