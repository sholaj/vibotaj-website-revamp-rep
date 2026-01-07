# TraceHub E2E Testing - One-Page Reference Card

## 🚀 Quick Start (Copy & Paste)

```bash
# 1. Start services (Docker Compose)
cd /path/to/tracehub
docker-compose up -d && sleep 15 && docker-compose exec backend python -m seed_data

# 2. Install Playwright
cd frontend
npm install

# 3. Run all E2E tests
npm run e2e

# Expected: 70 tests pass in ~4-5 minutes ✅
```

---

## 📋 Test User Credentials

```
ADMIN
  Email: admin@vibotaj.com | Password: tracehub2026

COMPLIANCE
  Email: compliance@vibotaj.com | Password: tracehub2026

LOGISTICS AGENT
  Email: 31stcenturyglobalventures@gmail.com | Password: Adeshola123!

BUYER
  Email: buyer@vibotaj.com | Password: tracehub2026

SUPPLIER
  Email: supplier@vibotaj.com | Password: tracehub2026

VIEWER
  Email: viewer@vibotaj.com | Password: tracehub2026
```

---

## 🎮 Test Commands

| Command | Purpose |
|---------|---------|
| `npm run e2e` | Run all 70 tests (headless) |
| `npm run e2e:ui` | Interactive test runner (visual UI mode) |
| `npm run e2e:headed` | See browser while running |
| `npm run e2e:debug` | Debug mode (pause on errors) |
| `npx playwright test e2e/admin.spec.ts` | Run one test file only |
| `npx playwright test -g "login"` | Run tests matching pattern |
| `npx playwright show-report` | View HTML test report |

---

## 🧪 Test Coverage Matrix

| Role | Tests | Key Verifications |
|------|-------|-------------------|
| **ADMIN** | 10 | Full access, users, orgs, settings |
| **COMPLIANCE** | 14 | Document approval, all shipments visible |
| **LOGISTICS** | 14 | Create shipments, upload docs |
| **BUYER** | 11 | Read-only assigned shipments |
| **SUPPLIER** | 10 | Origin docs upload only |
| **VIEWER** | 11 | Read-only all data, analytics |
| **TOTAL** | **70** | **Permission enforcement across all roles** |

---

## 🔑 Key Assertions Per Test

✓ **Can perform action?** → Button visible & enabled  
✓ **Cannot perform action?** → Button hidden or disabled  
✓ **Right data visible?** → Expected shipments/documents showing  
✓ **Wrong data hidden?** → Other users' data not visible  
✓ **Menu correct?** → Role-specific nav items only  
✓ **Status updated?** → DRAFT → DOCS_PENDING → etc.  

---

## 📁 File Locations

**Configuration:**
- `tracehub/frontend/playwright.config.ts` ← Test environment setup
- `tracehub/frontend/package.json` ← Playwright dependency + npm scripts

**Test Files:**
- `tracehub/frontend/e2e/helpers.ts` ← Shared functions (login, nav, assertions)
- `tracehub/frontend/e2e/admin.spec.ts` ← Admin role tests (10)
- `tracehub/frontend/e2e/compliance.spec.ts` ← Compliance tests (14)
- `tracehub/frontend/e2e/logistics.spec.ts` ← Logistics tests (14)
- `tracehub/frontend/e2e/buyer-supplier-viewer.spec.ts` ← 3 roles (32)

**Documentation:**
- `E2E_TEST_PLAN.md` ← Actor journeys & test design
- `LOCAL_BUILD_SETUP.md` ← Docker setup & debugging
- `e2e/README.md` ← Test structure & execution
- `PLAYWRIGHT_E2E_ARCHITECTURE.md` ← Visual architecture
- `E2E_TESTING_FILE_INVENTORY.md` ← Complete file listing

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| **`Cannot find module '@playwright/test'`** | Run `npm install` in frontend/ |
| **Port 80/8000/5433 already in use** | `docker-compose down -v` |
| **Tests timeout** | Check backend: `docker-compose logs backend` |
| **Login fails** | Verify user seeded: `docker-compose exec db psql -U tracehub -d tracehub -c "SELECT email FROM users;"` |
| **Need fresh database** | `docker-compose down -v && docker-compose up -d && docker-compose exec backend python -m seed_data` |
| **View test results** | `npx playwright show-report` |

---

## 🧩 Helper Functions (In e2e/helpers.ts)

```typescript
// Authentication
login(page, 'admin')                              // Login with role
logout(page)                                      // Logout
verifyLoggedIn(page, 'admin')                     // Check logged in

// Navigation
navigateTo(page, 'Shipments')                     // Go to section
verifyMenuVisibility(page, 'admin')               // Check menu items

// Permissions
expectActionAvailable(page, 'Create Shipment')    // Button visible & enabled
expectActionNotAvailable(page, 'Approve')         // Button hidden/disabled

// Utilities
verifyNoConsoleErrors(page)                       // Check for JS errors
getShipmentCount(page)                            // Count visible shipments
waitForElement(page, '.selector')                 // Wait for element
```

---

## 📊 Test Execution Flow

```
npm run e2e
    ↓
playwright.config.ts loads (headless chromium, localhost:80)
    ↓
admin.spec.ts → (beforeEach login) → 10 tests → (afterEach logout)
    ↓
compliance.spec.ts → (beforeEach login) → 14 tests → (afterEach logout)
    ↓
logistics.spec.ts → (beforeEach login) → 14 tests → (afterEach logout)
    ↓
buyer-supplier-viewer.spec.ts → (beforeEach login) → 32 tests → (afterEach logout)
    ↓
Test Results:
├─ test-results/index.html (visual report)
├─ Screenshots on failure
├─ Videos on failure
└─ JUnit XML for CI/CD
```

---

## ✨ Test Pattern (All Tests Follow This)

```typescript
test.describe('ROLE - Description', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, 'role');
  });

  test('should do something role-specific', async ({ page }) => {
    // Arrange: setup complete (already logged in)
    // Act: interact with page
    await button.click();
    // Assert: verify expectation
    await expect(element).toBeVisible();
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });
});
```

---

## 🎯 Permission Enforcement Examples

### Admin Can Access Settings ✅
```typescript
const settingsLink = page.locator('text="Settings"');
await expect(settingsLink).toBeVisible();
```

### Compliance Cannot Approve Their Own Docs ✅
```typescript
const approveButton = page.locator('button:has-text("Approve")');
await expectActionNotAvailable(page, 'Approve');
```

### Buyer Can Only See Assigned Shipments ✅
```typescript
const shipmentCount = await page.locator('table tbody tr').count();
expect(shipmentCount).toBeLessThan(10); // Limited visible
```

### Supplier Can Upload Origin Docs Only ✅
```typescript
const originUpload = page.locator('[aria-label*="Origin"] button:has-text("Upload")');
await expect(originUpload).toBeVisible();

const invoiceUpload = page.locator('[aria-label*="Invoice"] button:has-text("Upload")');
await expect(invoiceUpload).toBeDisabled();
```

---

## 📈 Performance Targets

- Page Load: < 3 seconds
- Navigation: < 1 second  
- Single Test: < 30 seconds
- Full Suite (70 tests): < 5 minutes

---

## 🔗 Documentation Map

| Want to... | See this file |
|-----------|--------------|
| Set up locally | LOCAL_BUILD_SETUP.md |
| Run tests | e2e/README.md |
| Debug failures | e2e/README.md → Debugging |
| Understand test design | E2E_TEST_PLAN.md |
| See architecture | PLAYWRIGHT_E2E_ARCHITECTURE.md |
| Know what files exist | E2E_TESTING_FILE_INVENTORY.md |
| Get quick overview | TRACEHUB_E2E_QUICK_START.md (this file) |

---

## ✅ Status

**Ready to use:** YES ✅  
**All tests passing:** TBD (run locally)  
**CI/CD integrated:** NO (next step - see setup instructions)  
**Documentation complete:** YES ✅  

---

## 🚀 Next Actions

1. **Try locally:** `npm run e2e` in frontend/
2. **View results:** `npx playwright show-report`
3. **Debug failures:** `npm run e2e:ui` (interactive mode)
4. **Add more tests:** Follow pattern in existing spec files
5. **Integrate CI/CD:** Add E2E step to GitHub Actions workflow

---

**Need help?** All details in the numbered documentation files. This is just a reference card.
