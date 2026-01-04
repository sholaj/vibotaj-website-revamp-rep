# Sprint 7: OCR & AI Document Detection

**Sprint Duration:** 1 week
**Sprint Goal:** Enable intelligent document classification for scanned PDFs
**Status:** PLANNED

---

## Sprint Overview

Currently, the multi-document PDF detection only works with text-based PDFs. Scanned documents (image-based) cannot be classified because:
- No extractable text for keyword matching
- AI detection not configured (missing API key)

This sprint will enable full document intelligence for all PDF types.

---

## Sprint Backlog

### Task 1: Configure AI Detection (Anthropic Claude)

**Priority:** High
**Assigned Agent:** `devops-engineer`
**Estimated Effort:** 2 hours

**Description:**
Configure the Anthropic API key in production to enable AI-powered document classification.

**Acceptance Criteria:**
- [ ] Add `ANTHROPIC_API_KEY` to production `.env` file
- [ ] Verify API key is valid and has sufficient quota
- [ ] Update `docker-compose.prod.yml` to pass env var to backend
- [ ] Test AI classification endpoint returns `ai_available: true`
- [ ] Document API key rotation procedure

**Technical Details:**
- Backend already has Anthropic SDK installed (`anthropic>=0.15.0`)
- Classifier at `backend/app/services/document_classifier.py` ready for AI
- Endpoint: `GET /api/documents/{id}/analyze?use_ai=true`

**Files to Modify:**
- `/opt/tracehub-app/tracehub/.env` (production)
- `tracehub/docker-compose.prod.yml` (add ANTHROPIC_API_KEY env var)

---

### Task 2: Integrate OCR Support (Tesseract)

**Priority:** High
**Assigned Agent:** `fullstack-developer`
**Estimated Effort:** 4-6 hours

**Description:**
Add OCR (Optical Character Recognition) capability to extract text from scanned/image-based PDFs before classification.

**Acceptance Criteria:**
- [ ] Install Tesseract OCR in backend Docker image
- [ ] Update PDF processor to detect image-based pages
- [ ] Run OCR on image pages to extract text
- [ ] Merge OCR text with native text extraction
- [ ] Test with scanned PDFs (BILL OF LADING - TWO (2).pdf, REF NO - 1417.pdf)
- [ ] Ensure OCR doesn't slow down text-based PDF processing

**Technical Details:**
```python
# Proposed flow in pdf_processor.py
1. Extract text with PyMuPDF
2. If char_count < threshold (e.g., 100 chars/page):
   - Convert page to image
   - Run Tesseract OCR
   - Use OCR text for classification
3. Combine native + OCR text
```

**Dependencies:**
- `tesseract-ocr` system package
- `pytesseract` Python package
- `Pillow` for image handling (already installed)

**Files to Modify:**
- `tracehub/backend/Dockerfile` (add Tesseract)
- `tracehub/backend/requirements.txt` (add pytesseract)
- `tracehub/backend/app/services/pdf_processor.py` (OCR integration)

---

### Task 3: Auto-Detection on Upload

**Priority:** Medium
**Assigned Agent:** `fullstack-developer`
**Estimated Effort:** 2-3 hours

**Description:**
Ensure documents are automatically analyzed and classified immediately after upload, not left in "pending" state.

**Acceptance Criteria:**
- [ ] Upload endpoint triggers auto-detection by default
- [ ] Document status updates based on classification results
- [ ] Frontend shows detected document types after upload
- [ ] Confidence scores displayed for AI-detected types
- [ ] User can override/correct misdetections

**Technical Details:**
- Current upload endpoint has `auto_detect` parameter
- Need to make `auto_detect=true` the default behavior
- Create `DocumentContent` records for each detected type
- Update document status from `uploaded` to `validated` for high-confidence detections

**Files to Modify:**
- `tracehub/backend/app/routers/documents.py` (default auto_detect)
- `tracehub/frontend/src/components/DocumentUpload.tsx` (show detection results)
- `tracehub/frontend/src/components/DocumentContents.tsx` (already built)

---

## Definition of Done

- [ ] All scanned PDFs can be classified (via OCR + AI)
- [ ] Text-based PDFs classified with keyword matching (fast path)
- [ ] AI detection works for ambiguous documents
- [ ] Upload flow automatically detects and classifies documents
- [ ] No documents left in "OTHER" type without user review
- [ ] Production deployment successful
- [ ] Tested with existing problem documents

---

## Agent Assignments Summary

| Task | Agent | Priority | Effort |
|------|-------|----------|--------|
| Configure AI Detection | `devops-engineer` | High | 2h |
| Integrate OCR Support | `fullstack-developer` | High | 4-6h |
| Auto-Detection on Upload | `fullstack-developer` | Medium | 2-3h |

---

## Dependencies & Risks

### Dependencies
1. Valid Anthropic API key with sufficient quota
2. Tesseract OCR compatible with Alpine Linux (Docker)
3. Sufficient server resources for OCR processing

### Risks
| Risk | Mitigation |
|------|------------|
| OCR slow for large PDFs | Process in background, show progress |
| Anthropic API rate limits | Implement retry with backoff |
| Tesseract accuracy issues | Use preprocessing (deskew, denoise) |

---

## Testing Plan

### Test Documents
1. `BILL OF LADING - TWO (2).pdf` (12-page scanned)
2. `REF NO - 1417.pdf` (5-page scanned)
3. Upload new text-based multi-doc PDF for comparison

### Test Cases
1. **OCR Extraction**: Verify text extracted from scanned pages
2. **AI Classification**: Verify Claude correctly identifies document types
3. **Keyword Fallback**: Verify text PDFs still use fast keyword matching
4. **Auto-Detection**: Verify upload triggers classification
5. **Performance**: Verify upload completes in <30 seconds

---

## Notes

- Sprint 6 completed multi-document PDF infrastructure
- This sprint enables the intelligence layer
- Future sprint: Add document validation rules per type
