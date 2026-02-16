# PRD-019: AI Document Classification v2

## Problem Statement

The v1 document classifier works — it uses Claude Haiku to identify document types from PDF text, with keyword-based fallback. But it has technical debt: hardcoded Anthropic client with `os.getenv()` instead of pydantic-settings, outdated model (`claude-3-haiku-20240307`), synchronous API calls, and no frontend integration. The v2 upload modal requires manual document type selection with no AI assistance.

PRD-019 introduces a **provider-agnostic LLM abstraction** (Protocol pattern, same as `StorageBackend`), upgrades the classifier, adds auto-detect UX to the upload flow, and exposes standalone classification endpoints.

## Dependencies

- PRD-004 (FastAPI on Railway — backend)
- PRD-005 (Supabase Storage — document storage)
- PRD-012 (Shipment detail — document management UI)
- PRD-018 (BoL auto-parse — triggered after classification)

## Scope

### Backend: LLM Abstraction + Classifier v2

**In scope:**
- `LLMBackend` Protocol with `complete()` and `classify()` methods (provider-agnostic)
- `AnthropicBackend` implementation (Claude Haiku 4.5 default, configurable model)
- `get_llm()` factory function (mirrors `get_storage()` pattern)
- Fix config: `SecretStr` for API keys, configurable provider/model via pydantic-settings
- Rewrite `DocumentClassifier` to use `LLMBackend` instead of raw Anthropic client
- Enhanced classification prompt with structured output
- Standalone `POST /documents/classify` endpoint
- `POST /documents/{id}/reclassify` endpoint
- Auto-detect on upload: when `auto_detect=true`, classify then set type
- Store `classification_confidence` and `classification_method` on Document model
- Configurable auto-upgrade threshold (default 0.70)

**Out of scope:**
- OpenAI / other provider implementations (just the Protocol — future PRDs add providers)
- Vision-based classification (sending images to LLM)
- Replacing keyword fallback
- Custom model fine-tuning
- Real-time classification progress (WebSocket)

### Frontend: Auto-Detect Upload UX

**In scope:**
- "Auto-detect" toggle in upload modal (default on for PDFs)
- After file selection: show AI-suggested type with confidence badge
- User can accept suggestion or override with manual selection
- Classification loading state during API call
- Re-classify button on document review panel

**Out of scope:**
- Drag-and-drop batch classification
- Document preview/thumbnail

## Architecture: LLM Abstraction

```
LLMBackend (Protocol)
├── AnthropicBackend     # Claude (default)
├── OpenAIBackend        # GPT (future)
└── MockLLMBackend       # Tests
```

```python
class LLMBackend(Protocol):
    async def complete(self, prompt: str, max_tokens: int = 1024) -> str: ...
    async def classify_document(self, text: str) -> ClassificationResult: ...
    def is_available(self) -> bool: ...
    def get_provider_name(self) -> str: ...
```

Config drives provider selection:
```python
llm_provider: str = "anthropic"          # "anthropic", "openai", "mock"
llm_model: str = "claude-haiku-4-5-20251001"
anthropic_api_key: SecretStr = SecretStr("")
```

## Acceptance Criteria

### Backend
1. `LLMBackend` Protocol defined in `services/llm.py`
2. `AnthropicBackend` uses `get_settings()` with `SecretStr`, configurable model
3. `get_llm()` factory returns configured backend based on `llm_provider` setting
4. `DocumentClassifier` uses `LLMBackend`, never imports `anthropic` directly
5. `POST /documents/classify` accepts file upload, returns classification
6. `POST /documents/{id}/reclassify` re-classifies an existing document
7. Upload with `auto_detect=true` classifies and sets type; returns classification
8. Auto-upgrade threshold configurable via `classification_confidence_threshold`
9. `classification_confidence` and `classification_method` stored on Document
10. Keyword fallback still works when LLM is unavailable
11. All endpoints filter by organization_id

### Frontend
12. Upload modal shows "Auto-detect type" toggle (default on for PDFs)
13. After file drop with auto-detect on: loading → suggested type with confidence
14. User can accept AI suggestion or select type manually
15. Re-classify button on document review panel
16. All components have Vitest tests

## API Changes

### New Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/documents/classify` | Classify a file without creating a document |
| POST | `/api/documents/{id}/reclassify` | Re-classify an existing document |

### Modified Endpoints
| Method | Path | Change |
|--------|------|--------|
| POST | `/api/documents/upload` | Returns `classification` object when `auto_detect=true` |

### Response: Classification Result
```json
{
  "document_type": "bill_of_lading",
  "confidence": 0.92,
  "method": "ai",
  "provider": "anthropic",
  "reference_number": "MSC1234567",
  "key_fields": {
    "issuer": "Mediterranean Shipping Company",
    "date": "2026-02-15"
  },
  "reasoning": "Document contains B/L number, shipper/consignee, vessel details...",
  "alternatives": [
    { "document_type": "commercial_invoice", "confidence": 0.05 }
  ]
}
```

## Config Changes

```python
# config.py — LLM settings
llm_provider: str = "anthropic"                    # Provider selection
llm_model: str = "claude-haiku-4-5-20251001"       # Model name
anthropic_api_key: SecretStr = SecretStr("")        # SecretStr (was plain str)
classification_confidence_threshold: float = 0.70   # Auto-upgrade threshold
```

## Database Changes

```sql
ALTER TABLE documents ADD COLUMN classification_confidence FLOAT;
ALTER TABLE documents ADD COLUMN classification_method VARCHAR(20);
-- classification_method: 'ai', 'keyword', 'manual'
```

## Frontend Changes

### Modified Files
- `src/components/documents/document-upload-modal.tsx` — Auto-detect toggle + AI suggestion
- `src/components/documents/document-review-panel.tsx` — Re-classify button

### New Files
- `src/lib/api/classification-types.ts` — ClassificationResult type + helpers
- `src/lib/api/classification.ts` — React Query hooks for classify/reclassify

## Compliance Impact

Classification only determines `document_type`. Compliance rules run AFTER type is set (PRD-016 engine + PRD-018 BoL pipeline). Horn/hoof (0506/0507) not affected.

## Testing

### Backend (pytest)
- `test_llm_backend.py` — LLM Protocol, AnthropicBackend, factory, mock backend
- `test_document_classifier_v2.py` — Classifier with LLM abstraction, keyword fallback
- `test_classify_endpoint.py` — Standalone + reclassify endpoint tests

### Frontend (vitest)
- `classification-types.test.ts` — Type helper tests
- `document-upload-modal.test.tsx` — Auto-detect toggle, suggestion display
