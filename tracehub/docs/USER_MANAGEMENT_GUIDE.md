# User Management System - Admin Guide

## Overview
The admin user management system in TraceHub provides full CRUD (Create, Read, Update, Delete) capabilities for user accounts with proper role-based access control.

## Current Status
✅ **ALL FUNCTIONALITY IS WORKING CORRECTLY**

- Backend API endpoints: ✅ Fully functional
- Permission system: ✅ Working correctly  
- Admin user CRUD: ✅ All operations verified
- Frontend UI: ✅ Password requirements clearly displayed

## Password Requirements

When creating or resetting passwords, the following requirements MUST be met:

- **Minimum length**: 8 characters
- **Uppercase letter**: At least one (A-Z)
- **Lowercase letter**: At least one (a-z)
- **Digit**: At least one (0-9)

### Examples:
✅ Valid: `Password123`, `TestUser2024`, `Admin!Pass1`  
❌ Invalid: `password` (missing uppercase and digit), `PASSWORD123` (missing lowercase)

## Admin Capabilities

Admins (role: `admin`) have the following permissions:

- **Create users**: Add new users with any role (except creating other admins)
- **Update users**: Modify user details, roles, and status
- **Delete users**: Soft-delete (deactivate) users
- **Reactivate users**: Restore previously deactivated users
- **Reset passwords**: Set new passwords for other users
- **List users**: View all users in the organization

## API Endpoints

All endpoints require authentication with admin role:

### Get Current User (with permissions)
```bash
GET /api/auth/me/full
Authorization: Bearer <token>
```

Returns `CurrentUser` with permissions array.

### List Users
```bash
GET /api/users?page=1&limit=20
Authorization: Bearer <token>
```

Optional filters: `role`, `is_active`, `search`

### Create User
```bash
POST /api/users
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "newuser@example.com",
  "full_name": "New User",
  "password": "ValidPass123",
  "role": "viewer"
}
```

### Update User
```bash
PATCH /api/users/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "Updated Name",
  "role": "compliance",
  "is_active": true
}
```

### Delete (Deactivate) User
```bash
DELETE /api/users/{user_id}
Authorization: Bearer <token>
```

Soft-deletes the user (sets `is_active = false`).

### Reactivate User
```bash
POST /api/users/{user_id}/activate
Authorization: Bearer <token>
```

### Reset User Password (Admin)
```bash
POST /api/users/{user_id}/reset-password?new_password=<encoded_password>
Authorization: Bearer <token>
```

## Common Issues & Solutions

### Issue: "Failed to create user"
**Cause**: Password doesn't meet requirements  
**Solution**: Ensure password has uppercase, lowercase, and digit

### Issue: "Permission denied"
**Cause**: User is not admin or token expired  
**Solution**: 
1. Verify you're logged in as admin
2. Check token is still valid
3. Refresh the page to reload permissions

### Issue: "Cannot see Add User button"
**Cause**: Permissions not loaded yet  
**Solution**: Refresh the page; the frontend loads permissions from `/api/auth/me/full`

### Issue: "User not appearing in list"
**Cause**: User might be filtered or pagination issue  
**Solution**: Clear filters and check pagination

## Testing

A comprehensive test script is available:

```bash
bash tracehub/scripts/test_user_crud.sh
```

This script verifies:
- Admin authentication
- Permission verification
- User creation
- User updates
- User listing
- User deactivation
- User reactivation

## Role Hierarchy

Admins can manage all roles below them:

1. **Admin** (highest) - Full system access
2. **Compliance** - Document validation and approval
3. **Logistics Agent** - Shipment and document management
4. **Buyer** - Read-only shipment access
5. **Supplier** - Upload documents, view assigned shipments
6. **Viewer** (lowest) - Read-only access to all data

**Rule**: Admins can create/modify users with any role except creating other admin users.

## Frontend Integration

The user management page is at `/users` and requires:
- Role: `admin`
- Permission: `users:list`

The page automatically:
- Fetches current user with permissions on load
- Shows "Add User" button only if user has `users:create` permission
- Displays password requirements inline
- Shows clear error messages for validation failures

## Security Notes

- All operations are logged in the audit trail
- Passwords are hashed with bcrypt before storage
- JWT tokens expire after configured duration
- Soft-delete preserves user data for audit purposes
- Cannot delete your own account (prevents lockout)
- Cannot change your own role (prevents privilege escalation)

## Verification Commands

Quick verification that admin user can perform all operations:

```bash
# 1. Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@vibotaj.com&password=tracehub2026" | jq -r .access_token)

# 2. Check permissions
curl -s http://localhost:8000/api/auth/me/full \
  -H "Authorization: Bearer $TOKEN" | jq '.permissions'

# 3. Create test user
curl -s -X POST http://localhost:8000/api/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","full_name":"Test","password":"Password123","role":"viewer"}' | jq .
```

## Summary

The user management system is **fully functional**. The most common user confusion stems from:

1. **Password validation requirements** - now clearly displayed in the UI
2. **Permission loading** - requires page refresh if token is stale
3. **Role hierarchy** - admins cannot create other admins

All backend tests pass, and the comprehensive test script (`test_user_crud.sh`) validates all operations successfully.
