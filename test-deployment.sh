#!/bin/bash

# Secret Santa Deployment Testing Script
# This script tests the deployed application to ensure it's working correctly

set -e

# Configuration
ENVIRONMENT=${1:-dev}
API_URL=${2}

echo "=========================================="
echo "Secret Santa Deployment Testing"
echo "=========================================="
echo "Environment: ${ENVIRONMENT}"
echo "=========================================="

# Get API URL if not provided
if [ -z "${API_URL}" ]; then
    STACK_NAME="secret-santa-backend-${ENVIRONMENT}"
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_NAME}" \
        --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
        --output text 2>/dev/null || echo "")
    
    if [ -z "${API_URL}" ]; then
        echo "Error: Could not retrieve API URL."
        echo "Please provide it as the second argument: ./test-deployment.sh ${ENVIRONMENT} <API_URL>"
        exit 1
    fi
fi

echo "API URL: ${API_URL}"
echo ""

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to test endpoint
test_endpoint() {
    local test_name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_status=$5
    
    echo -n "Testing ${test_name}... "
    
    if [ -z "${data}" ]; then
        response=$(curl -s -w "\n%{http_code}" -X ${method} "${API_URL}${endpoint}")
    else
        response=$(curl -s -w "\n%{http_code}" -X ${method} \
            -H "Content-Type: application/json" \
            -d "${data}" \
            "${API_URL}${endpoint}")
    fi
    
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "${status_code}" -eq "${expected_status}" ]; then
        echo "✓ PASSED (Status: ${status_code})"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo "✗ FAILED (Expected: ${expected_status}, Got: ${status_code})"
        echo "Response: ${body}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "Running API Tests..."
echo "=========================================="

# Test 1: Health Check
test_endpoint "Health Check" "GET" "/api/health" "" 200

# Test 2: Get Participants (empty)
test_endpoint "Get Participants (empty)" "GET" "/api/participants" "" 200

# Test 3: Get Participant Count
test_endpoint "Get Participant Count" "GET" "/api/participants/count" "" 200

# Test 4: Register Participant
test_endpoint "Register Participant" "POST" "/api/participants" '{"name":"Test User"}' 201

# Test 5: Get Participants (with data)
test_endpoint "Get Participants (with data)" "GET" "/api/participants" "" 200

# Test 6: Get Gifts (empty)
test_endpoint "Get Gifts (empty)" "GET" "/api/gifts" "" 200

# Test 7: Add Gift
test_endpoint "Add Gift" "POST" "/api/gifts" '{"name":"Test Gift"}' 201

# Test 8: Get Gifts (with data)
test_endpoint "Get Gifts (with data)" "GET" "/api/gifts" "" 200

# Test 9: Get Current Turn
test_endpoint "Get Current Turn" "GET" "/api/game/current-turn" "" 200

# Test 10: Invalid Endpoint
test_endpoint "Invalid Endpoint (404)" "GET" "/api/invalid" "" 404

echo ""
echo "=========================================="
echo "Test Results"
echo "=========================================="
echo "Tests Passed: ${TESTS_PASSED}"
echo "Tests Failed: ${TESTS_FAILED}"
echo "=========================================="

if [ ${TESTS_FAILED} -eq 0 ]; then
    echo "✓ All tests passed!"
    echo ""
    echo "Your deployment is working correctly!"
    exit 0
else
    echo "✗ Some tests failed."
    echo ""
    echo "Please check the CloudWatch logs for more details:"
    echo "aws logs tail /aws/lambda/secret-santa-api-${ENVIRONMENT} --follow"
    exit 1
fi
