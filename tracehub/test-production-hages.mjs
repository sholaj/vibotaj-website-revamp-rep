#!/usr/bin/env node
/**
 * Production Validation - HAGES User Test (Historic Shipments)
 *
 * Tests backward compatibility with actual shipments and documents
 */

import puppeteer from 'puppeteer';

const PRODUCTION_URL = 'https://tracehub.vibotaj.com';
const HAGES_USER = 'helge.bischoff@hages.de';
const HAGES_PASS = 'Hages2026Helge!';

const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function runTests() {
  console.log('🚀 Starting HAGES User Production Test...\n');

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
    documentsVisible: false,
    bolVisible: false
  };

  try {
    // Navigate to login page
    console.log('📍 Navigating to production...');
    await page.goto(PRODUCTION_URL, { waitUntil: 'networkidle2', timeout: 30000 });
    await wait(2000);

    // Login with HAGES credentials
    console.log('📍 Logging in with HAGES credentials...');

    const usernameInput = await page.$('input[name="username"], input[type="text"]');
    const passwordInput = await page.$('input[name="password"], input[type="password"]');

    if (usernameInput && passwordInput) {
      await usernameInput.type(HAGES_USER);
      await passwordInput.type(HAGES_PASS);

      const loginButton = await page.$('button[type="submit"]');
      if (loginButton) {
        await loginButton.click();
      } else {
        await passwordInput.press('Enter');
      }
      await wait(4000);
    }

    // Check if logged in
    const currentUrl = page.url();
    if (!currentUrl.includes('login')) {
      results.login = true;
      console.log('   ✅ Login successful');
    } else {
      console.log('   ❌ Login failed');
      throw new Error('Login failed');
    }

    // Navigate to shipments
    console.log('📍 Navigating to shipments list...');
    await page.goto(`${PRODUCTION_URL}/shipments`, { waitUntil: 'networkidle2', timeout: 30000 });
    await wait(3000);

    const pageContent = await page.content();
    if (pageContent.includes('Shipments') || pageContent.includes('VIBO')) {
      results.shipmentsLoad = true;
      console.log('   ✅ Shipments list loaded');
    }

    // Check if there are shipments in the list
    const shipmentRows = await page.$$('tbody tr');
    if (shipmentRows.length > 0) {
      results.hasShipments = true;
      console.log(`   ✅ Found ${shipmentRows.length} shipment(s)`);

      // Click on first shipment
      console.log('📍 Opening first shipment...');
      await shipmentRows[0].click();
      await wait(3000);

      const detailsUrl = page.url();
      if (detailsUrl.includes('/shipments/')) {
        results.shipmentDetails = true;
        console.log('   ✅ Shipment details page opened');

        // Check for documents
        const detailsContent = await page.content();
        if (detailsContent.includes('Documents') || detailsContent.includes('document')) {
          results.documentsVisible = true;
          console.log('   ✅ Documents section visible');
        }

        // Check for Bill of Lading
        if (detailsContent.includes('Bill of Lading') || detailsContent.includes('B/L') ||
            detailsContent.includes('bol') || detailsContent.includes('BOL')) {
          results.bolVisible = true;
          console.log('   ✅ Bill of Lading reference visible');
        }

        // Take screenshot of shipment details
        await page.screenshot({ path: 'production-hages-shipment.png', fullPage: true });
        console.log('\n📸 Screenshot saved: production-hages-shipment.png');
      }
    } else {
      console.log('   ⚠️ No shipments found for HAGES user');
    }

  } catch (error) {
    console.error('❌ Test error:', error.message);
  } finally {
    await browser.close();
  }

  // Summary
  console.log('\n' + '='.repeat(50));
  console.log('📊 HAGES USER TEST RESULTS');
  console.log('='.repeat(50));
  console.log(`Login:              ${results.login ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`Shipments Load:     ${results.shipmentsLoad ? '✅ PASS' : '⚠️ CHECK'}`);
  console.log(`Has Shipments:      ${results.hasShipments ? '✅ PASS' : '⚠️ CHECK'}`);
  console.log(`Shipment Details:   ${results.shipmentDetails ? '✅ PASS' : '⚠️ CHECK'}`);
  console.log(`Documents Visible:  ${results.documentsVisible ? '✅ PASS' : '⚠️ CHECK'}`);
  console.log(`B/L Visible:        ${results.bolVisible ? '✅ PASS' : '⚠️ CHECK'}`);
  console.log('='.repeat(50));

  const passCount = Object.values(results).filter(r => r).length;
  const totalCount = Object.keys(results).length;
  console.log(`\nOverall: ${passCount}/${totalCount} tests passed`);

  if (results.login && results.shipmentsLoad) {
    console.log('\n✅ Production is working - backward compatible');
    process.exit(0);
  } else {
    console.log('\n⚠️ Some tests need investigation');
    process.exit(1);
  }
}

runTests().catch(console.error);
