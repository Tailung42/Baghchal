# Contributing to Bagh Chal

Thanks for your interest. This document covers local setup, project structure, and how to contribute.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Manual Setup — Unix (macOS / Linux)](#manual-setup--unix-macos--linux)
- [Manual Setup — Windows](#manual-setup--windows)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [How to Contribute](#how-to-contribute)
- [What We're Working On](#what-were-working-on)

---

## Quick Start

The fastest way to get running. You'll need Python 3.8+, Node.js 18+, and npm installed.

```bash
git clone https://github.com/yourusername/baghchal.git
cd baghchal
chmod +x start.sh
./start.sh
```

The script handles everything — backend, frontend, and Redis detection. Once running:

- Game: http://localhost:5173
- API: http://localhost:8000

**Stop everything:** `Ctrl+C`

> The `start.sh` script is Unix only. Windows users see [manual setup below](#manual-setup--windows).

---

## Manual Setup — Unix (macOS / Linux)

### Prerequisites

- Python 3.8+
- Node.js 18+ and npm
- Docker (optional, for Redis)

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Redis

```bash
docker run -d --name redis -p 6379:6379 redis:latest
```

---

## Manual Setup — Windows

### Prerequisites

- [Python 3.8+](https://www.python.org/downloads/windows/) — check "Add to PATH" during install
- [Node.js 18+](https://nodejs.org/en/download) — npm is included
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for Redis)

### Backend

Open **Command Prompt** or **PowerShell**:

```bat
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

> If `python` isn't recognized, try `py` instead. If activation is blocked, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` in PowerShell first.

### Frontend

Open a **second** Command Prompt or PowerShell window:

```bat
cd frontend
npm install
npm run dev
```

### Redis

```bat
docker run -d --name redis -p 6379:6379 redis:latest
```
---

## Environment Variables

**`frontend/.env`**
```
VITE_BASE_WS_URL=ws://localhost:8000/
VITE_BASE_HTTP_URL=http://localhost:8000/
```

**`backend/.env`**
```
SECRET_KEY=your-django-secret-key
DEBUG=True
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
GOOGLE_CLIENT_ID=your-google-client-id
```

---

## Project Structure

```
baghchal/
├── backend/
│   ├── backend/          # Django settings
│   ├── baghchal/         # Game logic
│   │   ├── core/         # Game state & validation
│   │   ├── consumers.py  # WebSocket handlers
│   │   └── views.py      # HTTP endpoints
│   └── core/             # User management
│
└── frontend/
    └── src/
        ├── components/   # Reusable UI
        ├── routes/       # Pages
        ├── context/      # Auth & WebSocket state
        └── assets/
```

The game engine lives in two places intentionally: `MoveValidation.js` on the frontend gives instant feedback, while `baghchal/core/utils.py` on the backend is the authoritative source.

---

## Running Tests

```bash
# Backend
cd backend
python manage.py test

# Frontend linting
cd frontend
npm run lint
```

---

## How to Contribute

1. Fork the repo
2. Create a branch: `git checkout -b your-feature`
3. Make your changes and test them
4. Commit: `git commit -m 'describe what you did'`
5. Push: `git push origin your-feature`
6. Open a pull request against `main`

Keep pull requests focused — one thing per PR makes review much faster.

---

## Our Future Goals

- AI opponent (minimax)
- Game replay
- In-game chat(possibly voice too)
- Leaderboards & stats
- Spectator mode
- Move animations

If you want to pick something up, open an issue first so we can coordinate.

---

## Questions

Open an issue on GitHub. That's the best place to reach us.