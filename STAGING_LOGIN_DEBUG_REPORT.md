# Staging Login Debug Report

**Date:** January 7, 2026
**Environment:** Staging (https://staging.tracehub.vibotaj.com)
**Issue:** Users cannot log in - "Incorrect username or password" error
**Status:** Under investigation

---

## Executive Summary

Login authentication fails on staging despite users being successfully created in the database with valid bcrypt password hashes. The same code works correctly in CI tests and local development.

---

## Issue Description

### Symptom
Users receive "Incorrect username or password" error when attempting to log in on staging, even with correct credentials.

### Test Account Used
- **Email:** helge.bischoff@hages.de
- **Password:** Hages2026Helge!

---

## Investigation Timeline

### 1. Initial Discovery
- Staging deployment was completing successfully
- Backend health check passes
- Frontend loads correctly
- Login fails for all users

### 2. First Hypothesis: Code Not Deploying
**Test:** Added debug endpoints to verify new code is deployed
- `/api/auth/debug/ping` - Returns "Not Found" (unexpected)
- `/api/auth/debug/user-count` - Returns "Not Found" (unexpected)

**Finding:** Debug endpoints not accessible, but this may be due to routing issues or the environment check blocking them.

### 3. Second Hypothesis: Users Not Being Created
**Test:** Checked deployment logs for seeding output

**Log Evidence:**
```
Creating user admin@vibotaj.com with hash prefix: $2b$12$FHKRjKh7bFaE...
Creating user compliance@vibotaj.com with hash prefix: $2b$12$Rb/NxJfU.aZi...
Creating user logistic@vibotaj.com with hash prefix: $2b$12$o9FJNPz.xuxd...
Creating user buyer@witatrade.de with hash prefix: $2b$12$J0NKYtL9wdPO...
Creating user helge.bischoff@hages.de with hash prefix: $2b$12$CrLRIp03tNiA...
Creating user mats.jarsetz@hages.de with hash prefix: $2b$12$77wGUqmHIdJH...
Creating user eike.pannen@hages.de with hash prefix: $2b$12$tdrfRzqKXOZJ...
Verified: 7 users in database after seeding.
```

**Finding:** Users ARE being created with valid bcrypt hashes (`$2b$12$...` format).

### 4. Third Hypothesis: Password Hashing Mismatch

**Background:** Originally discovered that `seed_data.py` used passlib while `auth.py` used raw bcrypt. This was fixed.

**Current State:**
- `seed_data.py` - Uses raw bcrypt: `bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')`
- `auth.py` - Uses raw bcrypt: `bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))`

**Finding:** Both files now use the same hashing method.

### 5. Session Isolation Fix
Discovered that user seeding was being rolled back when sample shipment data failed. Fixed by using separate database sessions:

```python
# Session for users (committed independently)
db_users = SessionLocal()
try:
    vibotaj_id, witatrade_id = seed_users(db_users)
finally:
    db_users.close()

# Session for sample data (can fail without affecting users)
db_sample = SessionLocal()
try:
    seed_sample_data(db_sample, vibotaj_id, witatrade_id)
except Exception as e:
    print("Warning: Sample data seeding failed - users still committed")
finally:
    db_sample.close()
```

---

## Current Code State

### Key Files

#### 1. `tracehub/backend/app/routers/auth.py`

**Login function (line 226-299):**
```python
@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Debug logging
    db_user = get_user_by_email(db, form_data.username)
    if db_user:
        logger.info(f"LOGIN DEBUG: Found user {db_user.email}")
        password_match = verify_password(form_data.password, db_user.hashed_password)
        logger.info(f"LOGIN DEBUG: Password verification result: {password_match}")
    else:
        logger.info(f"LOGIN DEBUG: No user found for email: {form_data.username}")

    # Authenticate
    user = authenticate_user(db, form_data.username, form_data.password)

    if user:
        # Success - create token
        ...

    # Fall back to demo user
    if form_data.username == settings.demo_username or form_data.username == settings.demo_email:
        if form_data.password == settings.demo_password:
            # Demo user login
            ...

    # Login failed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
    )
```

**Password verification (line 47-49):**
```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
```

#### 2. `tracehub/backend/seed_data.py`

**Password hashing (line 31-33):**
```python
def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
```

#### 3. `tracehub/backend/requirements.txt`

```
bcrypt>=4.0.0,<4.1.0  # Pinned for compatibility
```

---

## Possible Root Causes (To Investigate)

### 1. Database Connection Issue
The login endpoint may be connecting to a different database or the users table may not be persisting between container restarts.

**Test:**
```bash
# SSH to staging server
docker compose exec -T db psql -U tracehub_staging -d tracehub_staging -c "SELECT email, LEFT(hashed_password, 20) as hash_prefix FROM users;"
```

### 2. Environment Variable Not Set
The `ENVIRONMENT` setting may not be properly set to "staging", affecting behavior.

**Test:**
```bash
docker compose exec -T backend python -c "from app.config import get_settings; print(get_settings().environment)"
```

### 3. bcrypt Encoding Issue
The password or hash may have encoding issues during verification.

**Test:**
```bash
docker compose exec -T backend python -c "
import bcrypt
# Test with the exact hash from database
hash_from_db = 'PASTE_HASH_HERE'  # Get from database
test_password = 'Hages2026Helge!'
result = bcrypt.checkpw(test_password.encode('utf-8'), hash_from_db.encode('utf-8'))
print(f'Password match: {result}')
"
```

### 4. Database User Query Failing Silently
The `get_user_by_email` function may be failing silently due to UUID validation issues.

**Note:** There's an exception handler that catches errors when user_id is not a valid UUID:
```python
try:
    user = get_user_by_id(db, user_id)
except Exception:
    db.rollback()
```

### 5. Demo User Fallback Masking Real Issue
The demo user fallback in login might be interfering.

---

## Recommended Next Steps

### 1. Verify Database State Directly
```bash
ssh tracehub@<server> "cd /home/tracehub/staging && docker compose exec -T db psql -U tracehub_staging -d tracehub_staging -c 'SELECT id, email, LEFT(hashed_password, 30) as hash_preview, is_active, role FROM users;'"
```

### 2. Test bcrypt Verification Directly on Server
```bash
ssh tracehub@<server> "cd /home/tracehub/staging && docker compose exec -T backend python -c \"
import bcrypt
from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()
user = db.query(User).filter(User.email == 'helge.bischoff@hages.de').first()
if user:
    print(f'User found: {user.email}')
    print(f'Hash: {user.hashed_password}')
    print(f'Active: {user.is_active}')
    test = bcrypt.checkpw('Hages2026Helge!'.encode(), user.hashed_password.encode())
    print(f'Password match: {test}')
else:
    print('User not found')
db.close()
\""
```

### 3. Check Container Logs During Login Attempt
```bash
# In one terminal, watch logs:
ssh tracehub@<server> "cd /home/tracehub/staging && docker compose logs -f backend"

# In another terminal, attempt login:
curl -sk -X POST https://staging.tracehub.vibotaj.com/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=helge.bischoff@hages.de&password=Hages2026Helge!"
```

### 4. Apply Debug Response (Uncommitted Change)
There's an uncommitted change in `tracehub/backend/app/routers/auth.py` that adds debug info to the login error response:

```python
# Return debug info for non-production environments
if debug_settings.environment != "production":
    debug_info = {
        "user_found": db_user is not None,
        "email_searched": form_data.username,
        "hash_exists": db_user.hashed_password is not None if db_user else False,
        "hash_prefix": db_user.hashed_password[:20] if db_user and db_user.hashed_password else None,
        "password_match": password_match if db_user else None,
        "environment": debug_settings.environment
    }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Incorrect username or password. Debug: {debug_info}",
    )
```

To apply and test:
```bash
git add tracehub/backend/app/routers/auth.py
git commit -m "debug(auth): Add debug info to login error response"
git push origin develop
# Wait for deployment, then test login to see debug info
```

---

## Environment Details

| Component | Value |
|-----------|-------|
| Backend Framework | FastAPI |
| Python Version | 3.11 |
| Database | PostgreSQL 15 |
| Password Hashing | bcrypt 4.0.x |
| Deployment | Docker Compose |
| CI/CD | GitHub Actions |
| Staging URL | https://staging.tracehub.vibotaj.com |
| Staging Backend Port | 8100 |
| Staging DB Port | 5532 |

---

## Files Changed During Investigation

1. `tracehub/backend/seed_data.py` - Fixed password hashing, added session isolation
2. `tracehub/backend/app/routers/auth.py` - Added debug endpoints and logging
3. `tracehub/backend/app/config.py` - Added environment setting
4. `.github/workflows/deploy-staging.yml` - Added FORCE_RESEED for database seeding

---

## Contact

For questions about this investigation, contact the development team.
