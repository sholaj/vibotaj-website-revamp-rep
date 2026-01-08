#!/bin/bash
# Test script for admin user CRUD operations

set -e

echo "==================================="
echo "Admin User Management CRUD Test"
echo "==================================="
echo ""

# Base URL
BASE_URL="http://localhost:8000/api"

# Step 1: Login as admin
echo "Step 1: Login as admin..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@vibotaj.com&password=tracehub2026")

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Login failed!"
  echo "$LOGIN_RESPONSE" | jq .
  exit 1
fi
echo "✅ Login successful, got token"
echo ""

# Step 2: Verify permissions
echo "Step 2: Verify admin has user management permissions..."
ME_RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me/full" \
  -H "Authorization: Bearer $TOKEN")

HAS_CREATE=$(echo "$ME_RESPONSE" | jq -r '.permissions | contains(["users:create"])')
HAS_UPDATE=$(echo "$ME_RESPONSE" | jq -r '.permissions | contains(["users:update"])')
HAS_DELETE=$(echo "$ME_RESPONSE" | jq -r '.permissions | contains(["users:delete"])')

if [ "$HAS_CREATE" != "true" ] || [ "$HAS_UPDATE" != "true" ] || [ "$HAS_DELETE" != "true" ]; then
  echo "❌ Missing required permissions!"
  echo "  users:create = $HAS_CREATE"
  echo "  users:update = $HAS_UPDATE"
  echo "  users:delete = $HAS_DELETE"
  exit 1
fi
echo "✅ Admin has all required permissions"
echo ""

# Step 3: Create a test user
echo "Step 3: Create a test user..."
TEST_EMAIL="testuser_$(date +%s)@example.com"
CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"full_name\": \"Test User\",
    \"password\": \"TestPassword123\",
    \"role\": \"viewer\"
  }")

USER_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')
if [ "$USER_ID" == "null" ] || [ -z "$USER_ID" ]; then
  echo "❌ User creation failed!"
  echo "$CREATE_RESPONSE" | jq .
  exit 1
fi
echo "✅ User created successfully (ID: $USER_ID)"
echo ""

# Step 4: Update the user
echo "Step 4: Update the user..."
UPDATE_RESPONSE=$(curl -s -X PATCH "$BASE_URL/users/$USER_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"full_name\": \"Updated Test User\",
    \"role\": \"compliance\"
  }")

UPDATED_NAME=$(echo "$UPDATE_RESPONSE" | jq -r '.full_name')
UPDATED_ROLE=$(echo "$UPDATE_RESPONSE" | jq -r '.role')
if [ "$UPDATED_NAME" != "Updated Test User" ] || [ "$UPDATED_ROLE" != "compliance" ]; then
  echo "❌ User update failed!"
  echo "$UPDATE_RESPONSE" | jq .
  exit 1
fi
echo "✅ User updated successfully"
echo "  Name: $UPDATED_NAME"
echo "  Role: $UPDATED_ROLE"
echo ""

# Step 5: List users (verify new user appears)
echo "Step 5: List users..."
LIST_RESPONSE=$(curl -s -X GET "$BASE_URL/users?limit=100" \
  -H "Authorization: Bearer $TOKEN")

FOUND_USER=$(echo "$LIST_RESPONSE" | jq -r ".items[] | select(.id == \"$USER_ID\") | .email")
if [ "$FOUND_USER" != "$TEST_EMAIL" ]; then
  echo "❌ Created user not found in list!"
  exit 1
fi
echo "✅ User found in list"
echo ""

# Step 6: Deactivate (delete) the user
echo "Step 6: Deactivate (soft delete) the user..."
DELETE_RESPONSE=$(curl -s -X DELETE "$BASE_URL/users/$USER_ID" \
  -H "Authorization: Bearer $TOKEN")

DELETE_MSG=$(echo "$DELETE_RESPONSE" | jq -r '.message')
if [[ ! "$DELETE_MSG" =~ "deactivated" ]]; then
  echo "❌ User deactivation failed!"
  echo "$DELETE_RESPONSE" | jq .
  exit 1
fi
echo "✅ User deactivated successfully"
echo ""

# Step 7: Verify user is inactive
echo "Step 7: Verify user is inactive..."
GET_RESPONSE=$(curl -s -X GET "$BASE_URL/users/$USER_ID" \
  -H "Authorization: Bearer $TOKEN")

IS_ACTIVE=$(echo "$GET_RESPONSE" | jq -r '.is_active')
if [ "$IS_ACTIVE" != "false" ]; then
  echo "❌ User is still active!"
  exit 1
fi
echo "✅ User is inactive"
echo ""

# Step 8: Reactivate the user
echo "Step 8: Reactivate the user..."
ACTIVATE_RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/activate" \
  -H "Authorization: Bearer $TOKEN")

ACTIVATE_MSG=$(echo "$ACTIVATE_RESPONSE" | jq -r '.message')
if [[ ! "$ACTIVATE_MSG" =~ "activated" ]]; then
  echo "❌ User reactivation failed!"
  echo "$ACTIVATE_RESPONSE" | jq .
  exit 1
fi
echo "✅ User reactivated successfully"
echo ""

echo "==================================="
echo "✅ ALL TESTS PASSED!"
echo "==================================="
echo ""
echo "Summary:"
echo "  - Admin authentication: ✅"
echo "  - Permission verification: ✅"
echo "  - Create user: ✅"
echo "  - Update user: ✅"
echo "  - List users: ✅"
echo "  - Deactivate user: ✅"
echo "  - Verify inactive: ✅"
echo "  - Reactivate user: ✅"
echo ""
