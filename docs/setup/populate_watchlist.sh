#!/bin/bash

# Moda Crypto Watchlist Populator - Bash Wrapper
# This script provides an easy way to run the watchlist population script

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT_PATH="$PROJECT_ROOT/docs/setup/populate_watchlist.py"
BACKEND_PATH="$PROJECT_ROOT/backend"

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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_ROOT/README.md" ]] || [[ ! -d "$BACKEND_PATH" ]]; then
        print_error "This script must be run from the moda-crypto project directory"
        exit 1
    fi
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check if backend directory exists
    if [[ ! -d "$BACKEND_PATH" ]]; then
        print_error "Backend directory not found at $BACKEND_PATH"
        exit 1
    fi
    
    # Check if requirements.txt exists
    if [[ ! -f "$BACKEND_PATH/requirements.txt" ]]; then
        print_warning "Backend requirements.txt not found"
    fi
    
    # Check if .env file exists
    if [[ ! -f "$BACKEND_PATH/.env" ]]; then
        print_warning "Backend .env file not found. Firebase credentials may not be configured."
    fi
    
    # Check if script exists
    if [[ ! -f "$SCRIPT_PATH" ]]; then
        print_error "Watchlist population script not found at $SCRIPT_PATH"
        exit 1
    fi
    
    print_success "Prerequisites check completed"
}

# Function to install dependencies
install_dependencies() {
    if [[ -f "$BACKEND_PATH/requirements.txt" ]]; then
        print_status "Installing backend dependencies..."
        cd "$BACKEND_PATH"
        
        # Check if virtual environment exists
        if [[ -d "venv" ]]; then
            print_status "Using existing virtual environment"
            source venv/bin/activate
        else
            print_warning "No virtual environment found. Installing to system Python."
        fi
        
        pip install -r requirements.txt
        cd "$PROJECT_ROOT"
        print_success "Dependencies installed"
    else
        print_warning "Skipping dependency installation (requirements.txt not found)"
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Populate the Moda Crypto watchlist with top 40 cryptocurrencies"
    echo ""
    echo "Options:"
    echo "  --dry-run         Preview changes without making them"
    echo "  --force          Overwrite existing tokens"
    echo "  --install-deps   Install backend dependencies first"
    echo "  --help, -h       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --dry-run                    # Preview what would be added"
    echo "  $0                             # Add tokens to watchlist"
    echo "  $0 --force                     # Overwrite existing tokens"
    echo "  $0 --install-deps --dry-run    # Install deps and preview"
    echo ""
}

# Main execution
main() {
    local dry_run=false
    local force=false
    local install_deps=false
    local python_args=()
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run=true
                python_args+=("--dry-run")
                shift
                ;;
            --force)
                force=true
                python_args+=("--force")
                shift
                ;;
            --install-deps)
                install_deps=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Header
    echo "🚀 Moda Crypto Watchlist Setup"
    echo "=============================="
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Install dependencies if requested
    if [[ "$install_deps" == true ]]; then
        install_dependencies
    fi
    
    # Show execution plan
    print_status "Execution Plan:"
    if [[ "$dry_run" == true ]]; then
        echo "  - Mode: DRY RUN (preview only)"
    else
        echo "  - Mode: LIVE (will add tokens to Firestore)"
    fi
    
    if [[ "$force" == true ]]; then
        echo "  - Force: Enabled (will overwrite existing tokens)"
    fi
    
    echo "  - Tokens: Top 40 cryptocurrencies"
    echo "  - Source: CoinGecko API for market data"
    echo ""
    
    # Confirmation for live runs
    if [[ "$dry_run" == false ]]; then
        read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Operation cancelled by user"
            exit 0
        fi
    fi
    
    # Execute the Python script
    print_status "Executing watchlist population script..."
    cd "$PROJECT_ROOT"
    
    # Check if backend virtual environment should be used
    if [[ -f "$BACKEND_PATH/venv/bin/activate" ]]; then
        print_status "Using backend virtual environment"
        source "$BACKEND_PATH/venv/bin/activate"
        python3 "$SCRIPT_PATH" "${python_args[@]}"
    else
        python3 "$SCRIPT_PATH" "${python_args[@]}"
    fi
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        print_success "Watchlist population completed successfully!"
        if [[ "$dry_run" == true ]]; then
            print_status "To actually add the tokens, run without --dry-run"
        fi
    else
        print_error "Watchlist population failed with exit code $exit_code"
        exit $exit_code
    fi
}

# Run main function with all arguments
main "$@"