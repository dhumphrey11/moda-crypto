#!/bin/bash

# Firebase Configuration Validator for Moda Crypto
# This script checks if Firebase credentials are properly configured

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_PATH="$PROJECT_ROOT/backend"
ENV_FILE="$BACKEND_PATH/.env"

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "🔧 Firebase Configuration Validator"
echo "===================================="
echo ""

# Check if .env file exists
if [[ ! -f "$ENV_FILE" ]]; then
    print_error ".env file not found at $ENV_FILE"
    echo ""
    print_status "Create a .env file in the backend directory with your Firebase credentials:"
    echo "FIREBASE_PROJECT_ID=your-project-id"
    echo "FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com"
    echo 'FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMII...\n-----END PRIVATE KEY-----\n"'
    echo "FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com"
    exit 1
fi

print_success "Found .env file at $ENV_FILE"

# Check required Firebase variables
firebase_vars=("FIREBASE_PROJECT_ID" "FIREBASE_CLIENT_EMAIL" "FIREBASE_PRIVATE_KEY" "FIREBASE_STORAGE_BUCKET")
missing_vars=()
invalid_vars=()

echo ""
print_status "Checking Firebase environment variables..."

for var in "${firebase_vars[@]}"; do
    if ! grep -q "^${var}=" "$ENV_FILE"; then
        missing_vars+=("$var")
        print_error "Missing: $var"
    else
        value=$(grep "^${var}=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | head -c50)
        case $var in
            "FIREBASE_PROJECT_ID")
                if [[ -z "$value" ]]; then
                    invalid_vars+=("$var (empty)")
                    print_error "Invalid: $var is empty"
                else
                    print_success "Valid: $var = $value"
                fi
                ;;
            "FIREBASE_CLIENT_EMAIL")
                if [[ ! "$value" =~ @.*\.iam\.gserviceaccount\.com$ ]]; then
                    invalid_vars+=("$var (not service account email)")
                    print_warning "Suspicious: $var = $value (should end with .iam.gserviceaccount.com)"
                else
                    print_success "Valid: $var = $value"
                fi
                ;;
            "FIREBASE_PRIVATE_KEY")
                full_value=$(grep "^${var}=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"')
                if [[ "$full_value" == AIzaSy* ]]; then
                    invalid_vars+=("$var (API key instead of private key)")
                    print_error "Invalid: $var appears to be an API key (starts with AIzaSy)"
                elif [[ ! "$full_value" =~ ^-----BEGIN\ PRIVATE\ KEY----- ]]; then
                    invalid_vars+=("$var (wrong format)")
                    print_warning "Invalid: $var doesn't start with '-----BEGIN PRIVATE KEY-----'"
                else
                    print_success "Valid: $var format looks correct"
                fi
                ;;
            "FIREBASE_STORAGE_BUCKET")
                if [[ -z "$value" ]]; then
                    invalid_vars+=("$var (empty)")
                    print_error "Invalid: $var is empty"
                else
                    print_success "Valid: $var = $value"
                fi
                ;;
        esac
    fi
done

echo ""
echo "📊 VALIDATION SUMMARY"
echo "====================="

if [[ ${#missing_vars[@]} -eq 0 && ${#invalid_vars[@]} -eq 0 ]]; then
    print_success "All Firebase credentials are properly configured! ✨"
    echo ""
    print_status "You can now run the watchlist population script:"
    echo "  ./docs/setup/populate_watchlist.sh --dry-run"
    exit 0
else
    print_error "Configuration issues found:"
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        echo ""
        echo "Missing variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
    fi
    
    if [[ ${#invalid_vars[@]} -gt 0 ]]; then
        echo ""
        echo "Invalid variables:"
        for var in "${invalid_vars[@]}"; do
            echo "  - $var"
        done
    fi
    
    echo ""
    print_status "🛠️  To fix these issues:"
    print_status "1. Go to Firebase Console → Project Settings → Service Accounts"
    print_status "2. Click 'Generate new private key' to download service-account.json"
    print_status "3. Extract values from the JSON and add to backend/.env:"
    echo ""
    echo "   FIREBASE_PROJECT_ID=<project_id from JSON>"
    echo "   FIREBASE_CLIENT_EMAIL=<client_email from JSON>"
    echo "   FIREBASE_PRIVATE_KEY=\"<private_key from JSON>\"  # Keep quotes!"
    echo "   FIREBASE_STORAGE_BUCKET=<project_id>.appspot.com"
    echo ""
    print_status "📖 See SECRETS_REQUIRED.md for detailed instructions"
    
    exit 1
fi