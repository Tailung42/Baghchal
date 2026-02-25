# Bagh Chal - Traditional Nepali Strategy Game

A modern web implementation of Bagh Chal (Tigers and Goats), a traditional asymmetric strategy board game from Nepal. Play online with real-time multiplayer functionality.

## 🎮 About the Game

Bagh Chal is a two-player strategy game where:

- **4 Tigers** hunt and capture goats by jumping over them
- **20 Goats** try to block all tiger movements to win
- Tigers win by capturing 5 goats
- Goats win by immobilizing all tigers

## 🛠️ Tech Stack

### Backend

- **Django 5.2.4** - Web framework
- **Django Channels** - WebSocket support for real-time gameplay
- **Django REST Framework** - API endpoints
- **SQLite** - Database (development)

### Frontend

- **React 19** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS 4** - Styling
- **React Router 7** - Client-side routing
- **Axios** - HTTP client

## 📋 Prerequisites

- Python 3.8+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

Backend runs on `http://localhost:8000`

### Frontend Setup

```
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on `http://localhost:5173`

## 🎯 How to Play

**Start a Game:**
Create a new game and share the ID with a friend
Join an existing game using a game ID
Use Quick Match to find an opponent

**Placement Phase:**
Goat player places one goat per turn on any empty intersection
Tiger player can move or capture goats

**Movement Phase:**
After all 20 goats are placed, goats can now move
Both players move strategically to achieve their win condition

**Winnng:**
Tigers win: Capture 5 goats  
Goats win: Block all tiger movements

**For detailed rules, [visit the in-game Rules page](https://baghchal-2srv.onrender.com/rules)**

## 📁 Project Structure

```
baghchal/
├── backend/
│   ├── backend/          # Django project settings
│   ├── baghchal/         # Game logic app
│   │   ├── core/         # Game state management
│   │   ├── consumers.py  # WebSocket handlers
│   │   ├── routing.py    # WebSocket URL routing
│   │   └── views.py      # HTTP views
│   ├── core/             # User management app
│   └── manage.py
│
└── frontend/
    ├── src/
    │   ├── components/   # Reusable UI components
    │   ├── routes/       # Page components
    │   ├── context/      # React context (Auth, WebSocket)
    │   └── assets/       # Images and static files
    └── package.json
```

## 🎯 Core Features

- **Real-time Multiplayer** - WebSocket-based game synchronization
- **Multiple Game Modes**:
  - Create private game with custom ID
  - Join existing game
  - Quick match (auto-matching)
- **Guest Play** - No account required
- **User Accounts** - Optional registration for tracking stats
- **Move Validation** - Server-side game rule enforcement
- **Responsive Design** - Works on desktop and mobile

## 🔧 Configuration

### Environment Variables

**Frontend** (`frontend/.env`):

```env
VITE_BASE_WS_URL=ws://localhost:8000/ws/game/
VITE_BASE_HTTP_URL=http://localhost:8000/
```

**Backend** (`backend/backend/settings.py`):

- Debug mode: Set `DEBUG = True` for development
- Allowed hosts: Update `ALLOWED_HOSTS` for production
- CORS: Configure `CORS_ALLOWED_ORIGINS`

## 🧪 Development

### Running Tests

```bash
# Backend tests
cd backend
python manage.py test

# Frontend tests (when implemented)
cd frontend
npm test
```

### Code Quality

```bash
# Frontend linting
cd frontend
npm run lint
```

## 🎨 Game Logic

The game engine is split between frontend and backend:

- **Frontend** (`MoveValidation.js`): Client-side move validation for instant feedback
- **Backend** (`baghchal/core/utils.py`): Authoritative game state and validation
- **WebSocket** (`consumers.py`): Real-time state synchronization

### Game States

- `waiting` - Waiting for second player
- `ongoing` - Game in progress
- `over` - Game completed

### Game Phases

- `placement` - Goats being placed on board (first 20 moves)
- `displacement` - Both players moving pieces

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Test thoroughly**
5. **Commit** (`git commit -m 'Add amazing feature'`)
6. **Push** (`git push origin feature/amazing-feature`)
7. **Sync your Fork with main repo**
8. **Open a Pull Request**

### Future Direction

- [ ] Chat in the game feature, may be voice chat?
- [ ] Game statistics and leaderboards
- [ ] AI opponent (minimax preferably)
- [ ] sliding animations
- [ ] Spectator mode?
- [ ] Game replay functionality?

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 📞 Contact

For questions or suggestions, please open an issue on GitHub.
