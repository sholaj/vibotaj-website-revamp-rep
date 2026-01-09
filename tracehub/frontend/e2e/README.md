# Playwright E2E Tests
# TraceHub actor-based user journey tests covering all 6 roles

## Directory Structure

```
e2e/
├── helpers.ts              # Login, navigation, permission helpers
├── admin.spec.ts           # ADMIN role - full system access
├── compliance.spec.ts      # COMPLIANCE - document approval
├── logistics.spec.ts       # LOGISTICS_AGENT - shipment creation
├── buyer-supplier-viewer.spec.ts  # BUYER, SUPPLIER, VIEWER - read-only roles
└── README.md               # This file
```

## Quick Start

### 1. Install Dependencies
```bash
cd tracehub/frontend
npm install
```

### 2. Start Local Environment (Docker Compose)
```bash
cd tracehub
docker-compose up -d
sleep 15
docker-compose exec backend python -m seed_data
```

### 3. Run E2E Tests

**Run all tests:**
```bash
npm run e2e
```

**Run with UI (interactive mode):**
```bash
npm run e2e:ui
```

**See browser while running:**
```bash
npm run e2e:headed
```

**Debug mode (pauses on errors):**
```bash
npm run e2e:debug
```

**Run specific test file:**
```bash
npx playwright test e2e/admin.spec.ts
```

**Run specific test:**
```bash
npx playwright test -g "should login as admin"
```

## Test Coverage

| Role | File | Tests | Key Scenarios |
|------|------|-------|---------------|
| **ADMIN** | admin.spec.ts | 10 | Full access, user management, all data visible |
| **COMPLIANCE** | compliance.spec.ts | 14 | Document validation, approval, no create |
| **LOGISTICS_AGENT** | logistics.spec.ts | 14 | Create shipments, upload docs, no approve |
| **BUYER** | buyer-supplier-viewer.spec.ts | 11 | Read-only assigned shipments |
| **SUPPLIER** | buyer-supplier-viewer.spec.ts | 10 | Origin docs only, limited upload |
| **VIEWER** | buyer-supplier-viewer.spec.ts | 11 | Read-only all data, analytics only |

**Total: 6 actors, 70+ tests, covering permission enforcement & UI workflows**

## Test Structure

Each test file follows this pattern:

```typescript
test.describe('ROLE - Description', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, 'role');
    await verifyLoggedIn(page, 'role');
  });

  test('should do something role-specific', async ({ page }) => {
    // Arrange
    // Act
    // Assert
  });

  test.afterEach(async ({ page }) => {
    await logout(page);
  });
});
```

## Test Users

| Role | Email | Password | Org |
|------|-------|----------|-----|
| admin | admin@vibotaj.com | tracehub2026 | VIBOTAJ |
| compliance | compliance@vibotaj.com | tracehub2026 | VIBOTAJ |
| logistics | logistic@vibotaj.com | tracehub2026 | VIBOTAJ |
| buyer | buyer@witatrade.de | tracehub2026 | WITATRADE |
| supplier | supplier@vibotaj.com | tracehub2026 | VIBOTAJ |
| viewer | viewer@vibotaj.com | tracehub2026 | VIBOTAJ |

## Helper Functions

**Authentication:**
- `login(page, role)` - Login as specific user
- `logout(page)` - Logout
- `verifyLoggedIn(page, role)` - Check logged in state

**Navigation:**
- `navigateTo(page, section)` - Navigate to menu section
- `verifyMenuVisibility(page, role)` - Check role-specific menu items

**Permissions:**
- `expectActionAvailable(page, buttonLabel)` - Assert button visible & enabled
- `expectActionNotAvailable(page, buttonLabel)` - Assert button hidden or disabled
- `verifyMenuVisibility(page, role)` - Verify role-based menu visibility

**Utilities:**
- `verifyNoConsoleErrors(page)` - Check for JS errors
- `getShipmentCount(page)` - Count visible shipments
- `waitForElement(page, selector, timeout)` - Wait for element to appear

## Common Assertions

```typescript
// Navigation
await expect(page).toHaveURL(/dashboard/);

// Element visibility
await expect(element).toBeVisible({ timeout: 5000 });
await expect(element).toBeHidden();

// Element state
await expect(element).toBeDisabled();
await expect(element).toBeEnabled();

// Text content
await expect(element).toContainText('text');

// Permissions
await expectActionAvailable(page, 'Create Shipment');
await expectActionNotAvailable(page, 'Approve');
```

## Debugging

### View Test Report
After running tests:
```bash
npx playwright show-report
```

### Run with Video Recording
Tests are configured to record video on failure. Videos saved to `test-results/`.

### Run with Screenshots
Screenshots on failure are automatically saved to `test-results/`.

### View Trace (detailed browser action log)
```bash
npx playwright show-trace test-results/trace.zip
```

## CI/CD Integration

Tests run automatically in GitHub Actions on:
- Push to feature/* branches
- Pull requests to develop/main

See `.github/workflows/integration-tests.yml` for configuration.

## Troubleshooting

### Tests timeout
- Check if Docker Compose services are running: `docker-compose ps`
- Verify backend is healthy: `docker-compose logs backend | grep "Application startup"`
- Increase timeout in playwright.config.ts

### Login fails
- Verify test users exist in database: `docker-compose exec db psql -U tracehub -d tracehub -c "SELECT email FROM users;"`
- Check backend logs: `docker-compose logs backend`
- Verify API is responding: `curl http://localhost:8000/docs`

### Elements not found
- Check if UI selectors match actual HTML (may differ from design)
- Use Playwright Inspector: `PWDEBUG=1 npm run e2e`
- Screenshot on failure shows what UI looks like

### Database state issues
- Reset database: `docker-compose down -v && docker-compose up -d`
- Re-seed: `docker-compose exec backend python -m seed_data`

## Performance Targets

- Page load: < 3s
- Button click → navigation: < 1s
- Form submit: < 2s
- Document upload: < 5s
- Overall test suite: < 5 min

## Best Practices

1. **Use helpers** - Don't repeat login/navigation code
2. **One assertion per test** - Tests should be focused and independent
3. **Avoid hardcoded waits** - Use `waitForLoadState`, `waitForURL`, `waitForSelector`
4. **Clean data state** - Login/logout in beforeEach/afterEach
5. **Test user journeys** - Not just individual buttons
6. **Verify both positive and negative** - Check visible AND hidden elements

## Related Documentation

- [E2E Test Plan](../E2E_TEST_PLAN.md) - Detailed actor journeys
- [Local Build Setup](../LOCAL_BUILD_SETUP.md) - How to run locally
- [Playwright Docs](https://playwright.dev)
- [TraceHub Architecture](../../docs/architecture/tracehub-architecture.md)

## Contributing

When adding new tests:
1. Follow existing test structure
2. Use role-specific test user
3. Add assertions for both positive (action works) and negative (action blocked)
4. Test permission enforcement
5. Include descriptive test names
6. Update this README with new test count

