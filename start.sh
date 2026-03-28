#!/bin/bash

# Bagh Chal Project Startup Script
# This script starts the backend, frontend, and any required services

set -e  # Exit on any error

echo "🚀 Starting Bagh Chal Project..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is not installed. Please install Python 3.8+"
        exit 1
    fi

    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 16+"
        exit 1
    fi

    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install npm"
        exit 1
    fi

    if ! command -v redis-server &> /dev/null; then
        print_warning "Redis server not found. Make sure Redis is running separately or install it."
    fi

    print_success "Dependencies check passed"
}

# Start Redis if available
start_redis() {
    if command -v redis-server &> /dev/null; then
        print_status "Starting Redis server..."
        redis-server --daemonize yes --port 6379
        sleep 2
        if pgrep -x "redis-server" > /dev/null; then
            print_success "Redis server started"
        else
            print_warning "Failed to start Redis server"
        fi
    else
        print_warning "Redis server not available. Please start Redis manually if needed."
    fi
}

# Setup and start backend
start_backend() {
    print_status "Setting up backend..."

    cd backend

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Set Django settings module
    export DJANGO_SETTINGS_MODULE=backend.settings

    # Install/update requirements
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt

    # Run migrations
    print_status "Running database migrations..."
    python manage.py makemigrations
    python manage.py migrate

    # Start Django server with Daphne in background
    print_status "Starting Django server with Daphne..."
    daphne backend.asgi:application --bind 0.0.0.0 --port 8000 &
    BACKEND_PID=$!

    # Wait a bit for server to start
    sleep 3

    if kill -0 $BACKEND_PID 2>/dev/null; then
        print_success "Backend server started (PID: $BACKEND_PID)"
    else
        print_error "Failed to start backend server"
        exit 1
    fi

    cd ..
}

# Setup and start frontend
start_frontend() {
    print_status "Setting up frontend..."

    cd frontend

    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        print_status "Installing Node.js dependencies..."
        npm install
    fi

    # Start development server in background
    print_status "Starting frontend development server..."
    npm run dev &
    FRONTEND_PID=$!

    # Wait a bit for server to start
    sleep 5

    if kill -0 $FRONTEND_PID 2>/dev/null; then
        print_success "Frontend server started (PID: $FRONTEND_PID)"
    else
        print_error "Failed to start frontend server"
        exit 1
    fi

    cd ..
}

# Function to stop all services
stop_services() {
    print_status "Stopping all services..."

    # Kill backend
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null && print_success "Backend stopped" || print_warning "Backend was not running"
    fi

    # Kill frontend
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null && print_success "Frontend stopped" || print_warning "Frontend was not running"
    fi

    # Stop Redis if we started it
    if pgrep -x "redis-server" > /dev/null; then
        redis-cli shutdown 2>/dev/null && print_success "Redis stopped" || print_warning "Failed to stop Redis"
    fi
}

# Trap SIGINT (Ctrl+C) to stop services
trap stop_services SIGINT

# Main execution
main() {
    check_dependencies
    start_redis
    start_backend
    start_frontend

    print_success "🎉 All services started successfully!"
    echo ""
    echo "🌐 Frontend: http://localhost:5173"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📡 WebSocket: ws://localhost:8000"
    echo ""
    print_status "Press Ctrl+C to stop all services"

    # Wait for user interrupt
    wait
}

# Run main function
main "$@"