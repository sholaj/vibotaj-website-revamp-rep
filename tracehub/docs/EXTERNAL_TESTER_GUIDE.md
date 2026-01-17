# TraceHub External Tester Guide

> Comprehensive user story and test scenarios for all actors in TraceHub

**Version:** 1.0
**Date:** January 2026
**Application URL:** https://tracehub.vibotaj.com (Production) | https://staging.tracehub.vibotaj.com (Staging)

---

## Table of Contents

1. [Overview](#overview)
2. [Test Accounts](#test-accounts)
3. [Actor: Admin](#actor-admin)
4. [Actor: Compliance Officer](#actor-compliance-officer)
5. [Actor: Logistics Agent](#actor-logistics-agent)
6. [Actor: Buyer](#actor-buyer)
7. [Actor: Supplier](#actor-supplier)
8. [Actor: Viewer](#actor-viewer)
9. [Cross-Actor Scenarios](#cross-actor-scenarios)
10. [Bug Reporting Template](#bug-reporting-template)

---

## Overview

TraceHub is a container tracking and compliance platform for international trade. It enables exporters (VIBOTAJ) to manage shipments, documents, and compliance requirements while giving buyers (importers) visibility into their orders.

### Key Concepts

| Term | Description |
|------|-------------|
| **Shipment** | A single export transaction containing one or more containers |
| **Container** | A physical shipping container with tracking events |
| **Document** | Trade documents (Bill of Lading, Invoice, Certificates, etc.) |
| **Organization** | A company using the platform (exporter or importer) |
| **EUDR** | EU Deforestation Regulation - compliance requirements for certain products |
| **Product Type** | Category of goods (Horn & Hoof, Cocoa, Coffee, etc.) |

### Product Types and Compliance

| Product Type | HS Code | EUDR Required | Required Documents |
|--------------|---------|---------------|-------------------|
| Horn & Hoof | 0506/0507 | NO | EU TRACES, Vet Health Cert, Certificate of Origin, BoL, Invoice, Packing List |
| Cocoa | 1801-1806 | YES | EUDR Due Diligence, Geolocation, Risk Assessment + Standard docs |
| Coffee | 0901 | YES | EUDR Due Diligence, Geolocation, Risk Assessment + Standard docs |

---

## Test Accounts

### VIBOTAJ Organization (Exporter)

| Role | Email | Password | Notes |
|------|-------|----------|-------|
| Admin | admin@vibotaj.com | [Request from CEO] | Full system access |
| CEO/CTO | shola@vibotaj.com | [Request from CEO] | Full system access |

### HAGES Organization (Buyer)

| Role | Email | Password | Notes |
|------|-------|----------|-------|
| Owner | helge.bischoff@hages.de | Hages2026Helge! | Buyer org admin |
| Admin | mats.jarsetz@hages.de | Hages2026Mats! | Buyer org admin |
| Admin | eike.pannen@hages.de | Hages2026Eike! | Buyer org admin |

---

## Actor: Admin

### Role Description
Admins have full access to all platform features including user management, organization settings, and system configuration.

### User Stories

#### US-ADMIN-01: Create New Organization
**As an** Admin
**I want to** create a new buyer organization
**So that** new customers can access their shipments

**Test Steps:**
1. Log in as Admin (admin@vibotaj.com)
2. Navigate to **Organizations** in the sidebar
3. Click **+ Create Organization**
4. Fill in organization details:
   - Name: "Test Buyer GmbH"
   - Type: "importer"
   - Country: "Germany"
5. Click **Create**
6. Verify organization appears in the list

**Expected Result:** New organization is created and visible in the organizations list.

**Pass Criteria:**
- [ ] Organization form validates required fields
- [ ] Organization appears in list after creation
- [ ] Success notification is shown

---

#### US-ADMIN-02: Create User in Organization
**As an** Admin
**I want to** create new users for any organization
**So that** staff can access the platform

**Test Steps:**
1. Navigate to **Users** in the sidebar
2. Click **+ Create User**
3. Fill in user details:
   - Full Name: "Test User"
   - Email: "test.user@example.com"
   - Role: Select each role type (Compliance, Logistics Agent, Buyer, Viewer)
   - Password: "TestPassword123!"
4. Click **Create**
5. Verify user appears in the list with correct role

**Expected Result:** User is created and assigned to current organization.

**Pass Criteria:**
- [ ] Cannot create users with Admin role (only Admin can)
- [ ] Email validation works (rejects invalid formats)
- [ ] Password requirements enforced (12+ chars, uppercase, lowercase, number)
- [ ] User appears in list with correct role badge

---

#### US-ADMIN-03: Manage User Permissions
**As an** Admin
**I want to** activate/deactivate users
**So that** I can control platform access

**Test Steps:**
1. Navigate to **Users**
2. Find an active user
3. Click the **Actions** menu (three dots)
4. Select **Deactivate User**
5. Confirm the action
6. Verify user status changes to "Inactive"
7. Reactivate the user
8. Verify user status changes back to "Active"

**Expected Result:** User status toggles correctly.

**Pass Criteria:**
- [ ] Cannot deactivate own account
- [ ] Confirmation modal appears before deactivation
- [ ] Deactivated users cannot log in
- [ ] Reactivation restores access

---

#### US-ADMIN-04: View All Shipments
**As an** Admin
**I want to** view all shipments in my organization
**So that** I can monitor business operations

**Test Steps:**
1. Navigate to **Shipments** (Dashboard)
2. Verify shipment list loads
3. Use filters:
   - Status filter (Draft, In Transit, Delivered, etc.)
   - Product type filter
   - Date range filter
4. Click on a shipment to view details
5. Verify all tabs load (Documents, Tracking, Compliance)

**Expected Result:** Admin can view and filter all organizational shipments.

**Pass Criteria:**
- [ ] Shipment list loads with correct count
- [ ] Filters work correctly
- [ ] Shipment details page shows all information
- [ ] Cannot see shipments from other organizations

---

#### US-ADMIN-05: Override Validation Status
**As an** Admin
**I want to** override a failed validation
**So that** I can approve shipments with exceptions

**Test Steps:**
1. Find a shipment with "Invalid" validation status
2. Open the shipment details
3. Scroll to **Validation Status** panel
4. Click **Override** button
5. Enter override reason: "Approved per customer agreement dated 2026-01-15"
6. Click **Confirm Override**
7. Verify status changes to "Overridden (Valid)"

**Expected Result:** Validation is overridden with audit trail.

**Pass Criteria:**
- [ ] Override requires a reason
- [ ] Override is logged in audit trail
- [ ] Override banner shows who and when
- [ ] Can clear override to revert to original status

---

## Actor: Compliance Officer

### Role Description
Compliance officers review and validate documents, ensuring shipments meet regulatory requirements.

### User Stories

#### US-COMP-01: Review Document for Validation
**As a** Compliance Officer
**I want to** review uploaded documents
**So that** I can validate their accuracy

**Test Steps:**
1. Log in as Compliance user
2. Navigate to **Shipments**
3. Open a shipment with uploaded documents
4. Go to **Documents** tab
5. Click on a document (e.g., Bill of Lading)
6. Review the extracted content in the review panel
7. Compare extracted data with original document
8. Click **Validate** or **Reject**

**Expected Result:** Document status updates based on validation decision.

**Pass Criteria:**
- [ ] Extracted content is displayed accurately
- [ ] Can view original document
- [ ] Validation updates document status
- [ ] Rejection requires a reason

---

#### US-COMP-02: Run Shipment Validation
**As a** Compliance Officer
**I want to** run validation on a shipment
**So that** I can check compliance status

**Test Steps:**
1. Open a shipment details page
2. Locate the **Validation Status** panel
3. Click **Run Validation**
4. Wait for validation to complete
5. Review the results:
   - Summary (passed, failed, warnings)
   - Individual rule results by category
   - Severity indicators

**Expected Result:** Validation report shows compliance status.

**Pass Criteria:**
- [ ] Validation runs without errors
- [ ] Results grouped by category (Documents, EUDR, Business Rules)
- [ ] Failed rules show clear messages
- [ ] Can re-run validation after fixes

---

#### US-COMP-03: EUDR Compliance Check (Cocoa/Coffee)
**As a** Compliance Officer
**I want to** verify EUDR compliance for regulated products
**So that** shipments meet EU requirements

**Test Steps:**
1. Open a shipment with product type "Cocoa" or "Coffee"
2. Check the **EUDR Status** card
3. Verify required fields:
   - Geolocation coordinates
   - Deforestation statement
   - Risk assessment
4. If missing, click **Complete EUDR Data**
5. Fill in required fields
6. Save and verify status updates

**Expected Result:** EUDR compliance status reflects data completeness.

**Pass Criteria:**
- [ ] EUDR card shows for regulated products
- [ ] Missing data clearly indicated
- [ ] Can add geolocation coordinates
- [ ] Compliance status updates after data entry

---

#### US-COMP-04: Horn & Hoof Exemption Verification
**As a** Compliance Officer
**I want to** verify Horn & Hoof shipments are EUDR exempt
**So that** we don't apply unnecessary requirements

**Test Steps:**
1. Open a shipment with product type "Horn & Hoof"
2. Check the **EUDR Status** card
3. Verify it shows "Not Applicable" or "Exempt"
4. Verify no geolocation fields are required
5. Check required documents:
   - EU TRACES Certificate
   - Veterinary Health Certificate
   - Certificate of Origin

**Expected Result:** Horn & Hoof products show EUDR exemption.

**Pass Criteria:**
- [ ] EUDR status shows "Not Applicable"
- [ ] No geolocation fields displayed
- [ ] Correct documents listed as required
- [ ] Cannot submit EUDR data for this product type

---

## Actor: Logistics Agent

### Role Description
Logistics agents manage shipments, containers, and document uploads for export operations.

### User Stories

#### US-LOG-01: Create New Shipment
**As a** Logistics Agent
**I want to** create a new shipment
**So that** I can track an export transaction

**Test Steps:**
1. Log in as Logistics Agent
2. Click **+ New Shipment** button
3. Fill in shipment details:
   - Reference: "TEST-2026-001"
   - Product Type: "Horn & Hoof"
   - Exporter: "VIBOTAJ Global Nigeria Ltd"
   - Importer: "HAGES GmbH"
   - Port of Loading: "Lagos, Nigeria"
   - Port of Discharge: "Hamburg, Germany"
   - Estimated Departure: [Select date]
4. Click **Create Shipment**
5. Verify shipment appears in list

**Expected Result:** New shipment is created with Draft status.

**Pass Criteria:**
- [ ] Required fields are validated
- [ ] Reference must be unique
- [ ] Shipment created with "Draft" status
- [ ] Redirected to shipment details page

---

#### US-LOG-02: Upload Document to Shipment
**As a** Logistics Agent
**I want to** upload documents to a shipment
**So that** compliance can review them

**Test Steps:**
1. Open a shipment details page
2. Go to **Documents** tab
3. Click **Upload Document**
4. Select document type (e.g., "Bill of Lading")
5. Drag & drop or select file (PDF, max 10MB)
6. Optionally enter reference number
7. Click **Upload**
8. Wait for processing to complete
9. Verify document appears in list

**Expected Result:** Document is uploaded and AI extraction begins.

**Pass Criteria:**
- [ ] Drag & drop works
- [ ] File type validation (PDF only)
- [ ] File size validation (max 10MB)
- [ ] Progress indicator during upload
- [ ] Document appears with "Processing" then "Uploaded" status

---

#### US-LOG-03: Add Container to Shipment
**As a** Logistics Agent
**I want to** add containers to a shipment
**So that** I can track cargo movement

**Test Steps:**
1. Open a shipment details page
2. Look for container section
3. Click **Add Container**
4. Enter container number (format: XXXX1234567)
5. Enter seal number
6. Select container type (20ft, 40ft, 40ft HC)
7. Save container
8. Verify container appears in shipment

**Expected Result:** Container is linked to shipment.

**Pass Criteria:**
- [ ] Container number format validated
- [ ] Duplicate container warning
- [ ] Container appears in shipment details
- [ ] Can edit/remove container

---

#### US-LOG-04: Update Shipment Status
**As a** Logistics Agent
**I want to** update shipment status
**So that** stakeholders know current state

**Test Steps:**
1. Open a shipment in "Draft" status
2. Click **Edit Shipment**
3. Change status to "Confirmed"
4. Save changes
5. Verify status badge updates
6. Repeat for other status transitions:
   - Confirmed → In Transit
   - In Transit → Arrived
   - Arrived → Customs Clearance
   - Customs Clearance → Delivered

**Expected Result:** Status transitions follow valid workflow.

**Pass Criteria:**
- [ ] Only valid transitions allowed
- [ ] Invalid transitions show error message
- [ ] Status badge color changes appropriately
- [ ] Cannot revert from "Archived" status

---

#### US-LOG-05: View Tracking Timeline
**As a** Logistics Agent
**I want to** view container tracking events
**So that** I can monitor cargo movement

**Test Steps:**
1. Open a shipment with containers
2. Go to **Tracking** tab
3. View the tracking timeline
4. Check for events:
   - Gate In
   - Loaded on Vessel
   - Departed Port
   - In Transit
   - Arrived at Port
   - Gate Out

**Expected Result:** Timeline shows chronological tracking events.

**Pass Criteria:**
- [ ] Events displayed in chronological order
- [ ] Each event shows date/time and location
- [ ] Latest event highlighted
- [ ] Empty state if no events yet

---

## Actor: Buyer

### Role Description
Buyers (importers) have read-only access to shipments where they are the designated buyer organization.

### User Stories

#### US-BUY-01: View Assigned Shipments
**As a** Buyer
**I want to** view shipments assigned to my organization
**So that** I can track my orders

**Test Steps:**
1. Log in as Buyer user (helge.bischoff@hages.de)
2. Navigate to **Shipments**
3. Verify only shipments where HAGES is the buyer are visible
4. Click on a shipment to view details
5. Verify all tabs are accessible (read-only)

**Expected Result:** Buyer sees only their assigned shipments.

**Pass Criteria:**
- [ ] Only assigned shipments visible
- [ ] Cannot see VIBOTAJ internal shipments
- [ ] Shipment details fully visible
- [ ] Document list visible

---

#### US-BUY-02: Download Shipment Documents
**As a** Buyer
**I want to** download documents from my shipments
**So that** I can use them for customs clearance

**Test Steps:**
1. Open an assigned shipment
2. Go to **Documents** tab
3. Click download icon on a document
4. Verify file downloads correctly
5. Try **Download All** option
6. Verify ZIP file contains all documents

**Expected Result:** Documents download successfully.

**Pass Criteria:**
- [ ] Individual document download works
- [ ] Bulk download creates ZIP file
- [ ] Downloaded files are readable
- [ ] Cannot download documents from other shipments

---

#### US-BUY-03: View Compliance Status
**As a** Buyer
**I want to** see compliance status of my shipments
**So that** I know if there are issues

**Test Steps:**
1. Open an assigned shipment
2. View the compliance indicators:
   - Document completeness
   - Validation status
   - EUDR status (if applicable)
3. Check if any warnings or errors are shown

**Expected Result:** Compliance status is clearly visible.

**Pass Criteria:**
- [ ] Compliance badges are visible
- [ ] Can see validation results
- [ ] Warning indicators for issues
- [ ] Cannot modify compliance data

---

#### US-BUY-04: Cannot Modify Shipment (Read-Only)
**As a** Buyer
**I want to** be prevented from modifying shipments
**So that** data integrity is maintained

**Test Steps:**
1. Open an assigned shipment
2. Try to find edit options:
   - Edit button should not exist
   - Delete option should not exist
   - Upload document should not exist
3. Try direct URL access to edit endpoints

**Expected Result:** No modification options available.

**Pass Criteria:**
- [ ] No Edit button visible
- [ ] No Delete option visible
- [ ] No Upload document button
- [ ] API returns 403 if attempted

---

## Actor: Supplier

### Role Description
Suppliers provide origin certificates and geolocation data for products.

### User Stories

#### US-SUP-01: Upload Origin Certificate
**As a** Supplier
**I want to** upload origin certificates
**So that** product provenance is documented

**Test Steps:**
1. Log in as Supplier user
2. Navigate to assigned shipments
3. Open a shipment requiring origin data
4. Go to **Documents** tab
5. Upload "Certificate of Origin"
6. Verify document is processed

**Expected Result:** Origin certificate is uploaded and linked.

**Pass Criteria:**
- [ ] Can upload certificate of origin
- [ ] Document linked to correct shipment
- [ ] AI extracts origin details
- [ ] Status updates appropriately

---

#### US-SUP-02: Provide Geolocation Data (EUDR Products)
**As a** Supplier
**I want to** provide geolocation data
**So that** EUDR requirements are met

**Test Steps:**
1. Open a shipment with EUDR-regulated product (Cocoa/Coffee)
2. Navigate to **Origin Verification** section
3. Enter geolocation coordinates:
   - Latitude: e.g., 6.5244
   - Longitude: e.g., 3.3792
4. Add deforestation statement
5. Save the data
6. Verify EUDR status updates

**Expected Result:** Geolocation data is saved and EUDR status updates.

**Pass Criteria:**
- [ ] Coordinate format validated
- [ ] Deforestation statement required
- [ ] Data saved successfully
- [ ] EUDR compliance status reflects update

---

## Actor: Viewer

### Role Description
Viewers have read-only access to all shipment and document data in their organization.

### User Stories

#### US-VIEW-01: View All Organizational Shipments
**As a** Viewer
**I want to** browse all shipments
**So that** I can monitor business activity

**Test Steps:**
1. Log in as Viewer user
2. Navigate to **Shipments**
3. Verify all organization shipments are visible
4. Use filters and search
5. Open shipment details
6. Verify all tabs are accessible

**Expected Result:** Full read access to organizational data.

**Pass Criteria:**
- [ ] All shipments visible
- [ ] Search and filters work
- [ ] Can view all shipment details
- [ ] Cannot modify any data

---

#### US-VIEW-02: View Analytics Dashboard
**As a** Viewer
**I want to** view the analytics dashboard
**So that** I can see business metrics

**Test Steps:**
1. Navigate to **Dashboard** (Analytics)
2. View available charts and metrics:
   - Shipment count by status
   - Document upload trends
   - Compliance rates
   - Product type distribution
3. Interact with chart filters

**Expected Result:** Analytics dashboard displays correctly.

**Pass Criteria:**
- [ ] Charts load without errors
- [ ] Data reflects current state
- [ ] Filters update visualizations
- [ ] Export options available (if applicable)

---

## Cross-Actor Scenarios

### Scenario 1: Complete Shipment Lifecycle

**Actors:** Admin, Logistics Agent, Compliance Officer, Buyer

**Story:** A complete export transaction from creation to delivery.

**Steps:**

1. **Logistics Agent** creates new shipment "CROSS-TEST-001"
2. **Logistics Agent** adds container MSCU1234567
3. **Logistics Agent** uploads Bill of Lading
4. **Logistics Agent** uploads Commercial Invoice
5. **Logistics Agent** uploads Packing List
6. **Compliance Officer** reviews and validates Bill of Lading
7. **Compliance Officer** runs shipment validation
8. **Admin** views validation results
9. **Logistics Agent** updates status to "In Transit"
10. **Buyer** (HAGES user) logs in and views their shipment
11. **Buyer** downloads all documents
12. **Logistics Agent** updates status to "Delivered"
13. **Compliance Officer** archives the shipment

**Expected Result:** Complete workflow executes without errors.

---

### Scenario 2: Multi-Organization Isolation

**Actors:** Admin (VIBOTAJ), Buyer (HAGES)

**Story:** Verify data isolation between organizations.

**Steps:**

1. **VIBOTAJ Admin** creates shipment "INTERNAL-001" (no buyer assigned)
2. **VIBOTAJ Admin** creates shipment "HAGES-001" (HAGES as buyer)
3. **HAGES Buyer** logs in
4. **HAGES Buyer** should see only "HAGES-001"
5. **HAGES Buyer** should NOT see "INTERNAL-001"
6. **HAGES Buyer** tries direct URL to "INTERNAL-001" → Should get 404

**Expected Result:** Organizations cannot see each other's internal data.

---

### Scenario 3: Document Auto-Detection

**Actors:** Logistics Agent, Compliance Officer

**Story:** Test AI document type detection.

**Steps:**

1. **Logistics Agent** opens a shipment
2. **Logistics Agent** uploads document with type "auto-detect"
3. System should identify document type automatically
4. **Compliance Officer** verifies detected type is correct
5. **Compliance Officer** can override if incorrect

**Expected Result:** AI correctly identifies common document types.

---

## Bug Reporting Template

When reporting issues, please use this format:

```markdown
## Bug Report

**Title:** [Brief description]

**Environment:**
- URL: [staging/production]
- Browser: [Chrome/Firefox/Safari + version]
- User Role: [Admin/Compliance/Logistics/Buyer/Supplier/Viewer]
- User Email: [test account used]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Result:**
[What should happen]

**Actual Result:**
[What actually happened]

**Screenshots/Videos:**
[Attach if applicable]

**Console Errors:**
[Open browser DevTools → Console, paste any red errors]

**Severity:**
- [ ] Critical - Cannot use core functionality
- [ ] Major - Feature broken, workaround exists
- [ ] Minor - Cosmetic or minor inconvenience
- [ ] Enhancement - Suggestion for improvement

**Additional Notes:**
[Any other relevant information]
```

---

## Contact

For questions about testing or to report urgent issues:

- **Technical Lead:** Shola (shola@vibotaj.com)
- **Operations:** Bolaji Jibodu (bolaji@vibotaj.com)

---

*Document Version 1.0 - January 2026*
