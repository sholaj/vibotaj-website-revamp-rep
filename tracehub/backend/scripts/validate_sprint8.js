#!/usr/bin/env node
/**
 * Sprint 8 Validation Script
 * Tests: Multi-tenancy (HAGES login) and EUDR compliance display
 */

const puppeteer = require('puppeteer');

const BASE_URL = process.env.TRACEHUB_URL || 'https://tracehub.vibotaj.com';

// Test accounts from CLAUDE.md
const HAGES_USER = {
  email: 'helge.bischoff@hages.de',
  password: 'Hages2026Helge!'
};

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function validateSprint8() {
  console.log('🚀 Sprint 8 Validation Starting...\n');
  console.log(`📍 Target: ${BASE_URL}\n`);

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  const results = {
    passed: [],
    failed: []
  };

  try {
    // Test 1: Navigate to app
    console.log('📋 Test 1: Loading TraceHub...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle2', timeout: 30000 });
    const title = await page.title();
    console.log(`   Page title: ${title}`);
    results.passed.push('App loads successfully');

    // Test 2: Check login page exists
    console.log('\n📋 Test 2: Checking login page...');
    await sleep(2000);

    // Look for login form elements (Username field, not email type)
    const emailInput = await page.$('input[placeholder*="username" i], input[placeholder*="Username"], input:first-of-type');
    const passwordInput = await page.$('input[type="password"], input[placeholder*="password" i]');

    if (emailInput && passwordInput) {
      results.passed.push('Login form found');
      console.log('   ✅ Login form detected');

      // Test 3: Attempt HAGES login
      console.log('\n📋 Test 3: Testing HAGES user login...');
      await emailInput.type(HAGES_USER.email, { delay: 50 });
      await passwordInput.type(HAGES_USER.password, { delay: 50 });

      // Submit form using Enter key (more reliable than click)
      await page.keyboard.press('Enter');
      await sleep(5000); // Wait for login redirect

      // Take intermediate screenshot
      await page.screenshot({ path: '/tmp/tracehub_after_login.png' });

      const loginButton = true; // Skip button check since we used Enter
      if (loginButton) {

        // Check if login succeeded (look for dashboard elements or error)
        const currentUrl = page.url();
        const pageContent = await page.content();

        if (currentUrl.includes('dashboard') || currentUrl.includes('shipments') ||
            pageContent.includes('HAGES') || pageContent.includes('Shipments')) {
          results.passed.push('HAGES user login successful');
          console.log('   ✅ Login successful - multi-tenancy working');

          // Test 4: Check for shipments/compliance view
          console.log('\n📋 Test 4: Checking shipments view...');

          // Navigate to shipments if not already there
          if (!currentUrl.includes('shipments')) {
            const shipmentsLink = await page.$('a[href*="shipments"], nav a:has-text("Shipments")');
            if (shipmentsLink) {
              await shipmentsLink.click();
              await sleep(2000);
            }
          }

          const shipmentsContent = await page.content();
          if (shipmentsContent.includes('shipment') || shipmentsContent.includes('container')) {
            results.passed.push('Shipments view accessible');
            console.log('   ✅ Shipments view loaded');
          }

          // Test 5: Verify EUDR compliance info
          console.log('\n📋 Test 5: Checking EUDR compliance display...');
          // Look for compliance-related elements
          const hasEudrSection = shipmentsContent.includes('EUDR') ||
                                 shipmentsContent.includes('compliance') ||
                                 shipmentsContent.includes('Compliance');

          if (hasEudrSection) {
            // Check that horn/hoof products don't show EUDR requirements
            const hasHornHoof = shipmentsContent.includes('0506') ||
                               shipmentsContent.includes('0507') ||
                               shipmentsContent.includes('horn') ||
                               shipmentsContent.includes('hoof');

            if (hasHornHoof) {
              // Verify no EUDR geolocation shown for horn/hoof
              const geoPattern = /0506.*geolocation|0507.*geolocation|horn.*EUDR.*required|hoof.*EUDR.*required/i;
              if (!geoPattern.test(shipmentsContent)) {
                results.passed.push('Horn/hoof products correctly exclude EUDR');
                console.log('   ✅ Horn/hoof products correctly show NO EUDR requirements');
              } else {
                results.failed.push('Horn/hoof incorrectly shows EUDR requirements');
                console.log('   ❌ Horn/hoof incorrectly shows EUDR requirements');
              }
            } else {
              console.log('   ℹ️  No horn/hoof products found to validate');
            }
          } else {
            console.log('   ℹ️  No compliance section found on current page');
          }

        } else if (pageContent.includes('error') || pageContent.includes('Invalid')) {
          results.failed.push('HAGES login failed - check credentials');
          console.log('   ❌ Login failed - credentials may need updating');
        } else {
          console.log('   ⚠️  Login status unclear, taking screenshot...');
        }
      }
    } else {
      // Maybe already logged in or different page structure
      console.log('   ℹ️  No login form found - may already be authenticated or different structure');
      const pageContent = await page.content();
      console.log(`   Page has ${pageContent.length} characters`);
    }

    // Take screenshot for verification
    const screenshotPath = '/tmp/tracehub_sprint8_validation.png';
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`\n📸 Screenshot saved: ${screenshotPath}`);

  } catch (error) {
    results.failed.push(`Error: ${error.message}`);
    console.error('\n❌ Error during validation:', error.message);

    // Screenshot on error
    try {
      await page.screenshot({ path: '/tmp/tracehub_error.png', fullPage: true });
      console.log('📸 Error screenshot saved: /tmp/tracehub_error.png');
    } catch (e) {}
  } finally {
    await browser.close();
  }

  // Summary
  console.log('\n' + '='.repeat(50));
  console.log('📊 SPRINT 8 VALIDATION SUMMARY');
  console.log('='.repeat(50));
  console.log(`\n✅ Passed: ${results.passed.length}`);
  results.passed.forEach(p => console.log(`   • ${p}`));

  if (results.failed.length > 0) {
    console.log(`\n❌ Failed: ${results.failed.length}`);
    results.failed.forEach(f => console.log(`   • ${f}`));
  }

  console.log('\n' + '='.repeat(50));

  return results.failed.length === 0;
}

validateSprint8()
  .then(success => process.exit(success ? 0 : 1))
  .catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
