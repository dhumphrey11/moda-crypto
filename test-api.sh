#!/bin/bash

# MODA Crypto API Testing Script
# Tests all new endpoints implemented in the four recommendations

echo "🧪 MODA Crypto API Testing Suite"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0

# Function to test an endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local expected_status=${4:-200}
    
    echo -n "Testing: $description... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "%{http_code}" -o /dev/null -X "$method" "$BASE_URL$endpoint" -H "Content-Type: application/json")
    fi
    
    if [ "$response" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} ($response)"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} ($response, expected $expected_status)"
        ((FAILED++))
    fi
}

# Function to test POST endpoint with data
test_post_endpoint() {
    local endpoint=$1
    local data=$2
    local description=$3
    local expected_status=${4:-200}
    
    echo -n "Testing: $description... "
    
    response=$(curl -s -w "%{http_code}" -o /dev/null -X POST "$BASE_URL$endpoint" \
        -H "Content-Type: application/json" \
        -d "$data")
    
    if [ "$response" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} ($response)"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} ($response, expected $expected_status)"
        ((FAILED++))
    fi
}

echo ""
echo -e "${BLUE}📋 Basic Health Checks${NC}"
echo "----------------------"

test_endpoint "GET" "/" "Root endpoint"
test_endpoint "GET" "/health" "Health check"
test_endpoint "GET" "/monitoring/status" "Monitoring status"

echo ""
echo -e "${BLUE}💼 Portfolio Endpoints (Recommendation 1)${NC}"
echo "----------------------------------------"

test_endpoint "GET" "/paper-trade/portfolio/history?days=30" "Portfolio history"
test_endpoint "GET" "/paper-trade/trades/recent?limit=10" "Recent trades"
test_endpoint "GET" "/paper-trade/trades?page=1&size=20" "Paginated trades"
test_post_endpoint "/paper-trade/portfolio/snapshot" '{"notes":"Test snapshot"}' "Create portfolio snapshot"

echo ""
echo -e "${BLUE}📊 Signals Endpoints (Recommendation 2)${NC}"
echo "-------------------------------------"

test_endpoint "GET" "/compute/signals?page=1&size=10" "Paginated signals"
test_endpoint "GET" "/compute/signals?confidence_min=0.7" "Signals with confidence filter"
test_endpoint "GET" "/compute/signals?start_date=2024-01-01&end_date=2024-12-31" "Signals with date range"
test_endpoint "GET" "/compute/signals/summary" "Signals summary"

echo ""
echo -e "${BLUE}⚙️ Admin Monitoring (Recommendation 3)${NC}"
echo "------------------------------------"

test_endpoint "GET" "/admin/system/health" "System health"
test_endpoint "GET" "/admin/firebase/stats" "Firebase statistics"
test_endpoint "GET" "/admin/api/status" "API status"
test_endpoint "GET" "/admin/gcp/services" "GCP services"
test_endpoint "GET" "/admin/models" "Model management"
test_endpoint "GET" "/admin/portfolio/settings" "Portfolio settings"

echo ""
echo -e "${BLUE}🔍 Advanced Monitoring (Recommendation 4)${NC}"
echo "----------------------------------------"

test_endpoint "GET" "/admin/system/alerts" "System alerts"
test_endpoint "GET" "/admin/system/metrics/enhanced" "Enhanced metrics"
test_endpoint "POST" "/admin/system/monitoring/check-thresholds" "Threshold checks"
test_endpoint "GET" "/admin/system/monitoring/status" "Monitoring status"
test_endpoint "POST" "/admin/system/monitoring/start-background" "Start background monitoring"

echo ""
echo -e "${BLUE}📝 Watchlist Management${NC}"
echo "-------------------------"

test_endpoint "GET" "/admin/watchlist" "Get watchlist"
test_endpoint "GET" "/admin/tokens/all" "Get all tokens"
test_post_endpoint "/admin/watchlist" '{"token_id":"bitcoin","symbol":"BTC","name":"Bitcoin"}' "Add to watchlist"
test_endpoint "POST" "/admin/watchlist/sync" "Sync watchlist"

echo ""
echo -e "${BLUE}📊 API Documentation${NC}"
echo "-------------------"

test_endpoint "GET" "/docs" "Swagger UI" 200
test_endpoint "GET" "/redoc" "ReDoc documentation" 200

echo ""
echo "=================================="
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo "=================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! API is working correctly.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️ Some tests failed. Check the backend logs for details.${NC}"
    exit 1
fi