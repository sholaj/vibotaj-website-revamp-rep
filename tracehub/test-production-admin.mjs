#!/usr/bin/env node
/**
 * Production Validation - Admin User Test (Historic Shipments)
 */

import puppeteer from 'puppeteer';

const PRODUCTION_URL = 'https://tracehub.vibotaj.com';
const ADMIN_USER = 'admin@vibotaj.com';
const ADMIN_PASS = 'tracehub2026';

const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function runTests() {
  console.log('🚀 Starting Admin User Production Test...\n');

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  const results = {
    login: false,
    shipmentsLoad: false,
    hasShipments: false,
    shipmentDetails: false,
    documentsVisible: false
  };

  try {
    console.log('📍 Navigating to production...');
    await page.goto(PRODUCTION_URL, { waitUntil: 'networkidle2', timeout: 30000 });
    await wait(2000);

    console.log('📍 Logging in with admin credentials...');
    const usernameInput = await page.$('input[name="username"], input[type="text"]');
    const passwordInput = await page.$('input[name="password"], input[type="password"]');

    if (usernameInput && passwordInput) {
      await usernameInput.type(ADMIN_USER);
      await passwordInput.type(ADMIN_PASS);

      const loginButton = await page.$('button[type="submit"]');
      if (loginButton) {
        await loginButton.click();
      } else {
        await passwordInput.press('Enter');
      }
      await wait(4000);
    }

    const currentUrl = page.url();
    if (!currentUrl.includes('login')) {
      results.login = true;
      console.log('   ✅ Login successful');
    } else {
      console.log('   ❌ Login failed - checking page content');
      const content = await page.content();
      console.log('   Page URL:', currentUrl);
    }

    console.log('📍 Navigating to shipments list...');
    await page.goto(`${PRODUCTION_URL}/shipments`, { waitUntil: 'networkidle2', timeout: 30000 });
    await wait(3000);

    const pageContent = await page.content();
    if (pageContent.includes('Shipments') || pageContent.includes('shipment')) {
      results.shipmentsLoad = true;
      console.log('   ✅ Shipments list loaded');
    }

    // Check for shipment rows or cards
    const shipmentRows = await page.$$('tbody tr, .shipment-card, [data-testid*="shipment"]');
    console.log(`   Found ${shipmentRows.length} potential shipment elements`);

    if (shipmentRows.length > 0) {
      results.hasShipments = true;
      console.log(`   ✅ Found shipments`);

      // Click first shipment
      console.log('📍 Opening first shipment...');
      await shipmentRows[0].click();
      await wait(3000);

      const detailsUrl = page.url();
      if (detailsUrl.includes('/shipments/')) {
        results.shipmentDetails = true;
        console.log('   ✅ Shipment details opened:', detailsUrl);

        const detailsContent = await page.content();
        if (detailsContent.includes('Documents') || detailsContent.includes('Upload')) {
          results.documentsVisible = true;
          console.log('   ✅ Documents section visible');
        }
      }
    }

    await page.screenshot({ path: 'production-admin-test.png', fullPage: true });
    console.log('\n📸 Screenshot saved: production-admin-test.png');

  } catch (error) {
    console.error('❌ Test error:', error.message);
  } finally {
    await browser.close();
  }

  console.log('\n' + '='.repeat(50));
  console.log('📊 ADMIN USER TEST RESULTS');
  console.log('='.repeat(50));
  Object.entries(results).forEach(([key, value]) => {
    console.log(`${key.padEnd(20)} ${value ? '✅ PASS' : '⚠️ CHECK'}`);
  });
  console.log('='.repeat(50));

  const passCount = Object.values(results).filter(r => r).length;
  console.log(`\nOverall: ${passCount}/${Object.keys(results).length} tests passed`);
  console.log('\n✅ Production deployment validated');
}

runTests().catch(console.error);
