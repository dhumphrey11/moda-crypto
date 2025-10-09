#!/bin/bash

# MODA Crypto Development Environment Startup Script

echo "🚀 Starting MODA Crypto Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "Please run this script from the moda-crypto root directory"
    exit 1
fi

# Set up environment variables for live Firebase connection
# NOTE: You need to set your real Firebase credentials here
export FIREBASE_PROJECT_ID="moda-crypto"
export FIREBASE_STORAGE_BUCKET="moda-crypto.appspot.com"

# IMPORTANT: Set these to your actual Firebase service account credentials:
# export FIREBASE_CLIENT_EMAIL="firebase-adminsdk-xxxxx@moda-crypto.iam.gserviceaccount.com"
# export FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_ACTUAL_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----"

# Check if Firebase credentials are set
if [ -z "$FIREBASE_CLIENT_EMAIL" ] || [ -z "$FIREBASE_PRIVATE_KEY" ]; then
    print_warning "Firebase credentials not set. Please set:"
    echo "  export FIREBASE_CLIENT_EMAIL=\"your-service-account@moda-crypto.iam.gserviceaccount.com\""
    echo "  export FIREBASE_PRIVATE_KEY=\"-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY\\n-----END PRIVATE KEY-----\""
    echo ""
    print_warning "Or create a .env file with these variables"
    print_warning "The backend will run but database operations will fail without proper credentials"
fi

print_status "Environment variables set for development mode"

# Check if Python virtual environment exists
if [ ! -d "backend/venv" ]; then
    print_error "Python virtual environment not found in backend/venv"
    print_status "Creating virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    print_status "Virtual environment created and dependencies installed"
else
    print_status "Python virtual environment found"
fi

# Check if Node.js dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    print_warning "Node modules not found, installing..."
    cd frontend
    npm install
    cd ..
    print_status "Node.js dependencies installed"
else
    print_status "Node.js dependencies found"
fi

# Kill any existing processes on ports 8000 and 3000
print_status "Checking for existing processes..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port 8000 is in use, attempting to free it..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port 3000 is in use, attempting to free it..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
fi

echo ""
print_status "Environment setup complete! 🎉"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo ""
echo -e "${YELLOW}1. Start Backend Server:${NC}"
echo "   cd backend && source venv/bin/activate"
echo "   python -m uvicorn app.main:app --host localhost --port 8000 --reload"
echo ""
echo -e "${YELLOW}2. Start Frontend Server (in a new terminal):${NC}"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo -e "${YELLOW}3. Access the Application:${NC}"
echo "   • Frontend: http://localhost:3000"
echo "   • Backend API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}4. Quick Test Commands:${NC}"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:8000/admin/system/metrics/enhanced"
echo ""

read -p "Would you like to start both servers now? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting backend server..."
    
    # Start backend in background
    cd backend
    source venv/bin/activate
    python -m uvicorn app.main:app --host localhost --port 8000 --reload &
    BACKEND_PID=$!
    cd ..
    
    # Wait a moment for backend to start
    sleep 3
    
    print_status "Starting frontend server..."
    
    # Start frontend in background
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    echo ""
    print_status "Both servers starting up..."
    print_status "Backend PID: $BACKEND_PID"
    print_status "Frontend PID: $FRONTEND_PID"
    echo ""
    print_status "Give it a few seconds to start up, then visit:"
    echo -e "  ${GREEN}• Frontend: http://localhost:3000${NC}"
    echo -e "  ${GREEN}• Backend API: http://localhost:8000/docs${NC}"
    echo ""
    print_warning "Press Ctrl+C to stop both servers"
    
    # Wait for user to stop servers
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; print_status 'Servers stopped'; exit 0" INT
    wait
else
    print_status "Setup complete. Use the commands above to start the servers manually."
fi