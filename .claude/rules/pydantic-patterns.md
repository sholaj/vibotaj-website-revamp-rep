# Pydantic Patterns

## Schemas (API Boundaries)

All request/response models live in `tracehub/backend/app/schemas/`.

```python
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime

class ShipmentResponse(BaseModel):
    """Shipment API response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reference: str
    status: ShipmentStatus
    organization_id: UUID
    created_at: datetime
```

### Rules

- `ConfigDict(from_attributes=True)` for ORM model conversion
- Separate Create/Update/Response models — never expose internal fields in responses
- Use `Field()` with constraints: `min_length`, `ge`, `le`, `max_length`
- Use `StrEnum` for status fields — never bare strings
- Use `UUID` for all IDs
- Use `datetime` with timezone awareness

## Settings

All config via `pydantic-settings` in `tracehub/backend/app/config.py`.

```python
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql://..."
    jwt_secret: SecretStr = SecretStr("change-me")
    anthropic_api_key: SecretStr = SecretStr("")
```

### Rules

- `SecretStr` for ALL secrets (API keys, tokens, passwords)
- `@lru_cache` on `get_settings()` for singleton
- Override in tests: `Settings(database_url="sqlite:///:memory:")`
- Never `os.getenv()` — always via Settings

## Validation

- Validators on the model, not in service logic
- Use `field_validator` for complex validation (e.g., ISO 6346 container numbers)
- Use `model_validator` for cross-field validation
- Return clear error messages that the frontend can display

## Anti-Patterns

- Never use `dict` for structured data — make a model
- Never use `Any` — find the right type
- Never use `model_dump()` to convert between model types — use explicit mapping
- Never put validation outside models — validators belong on the model
- Never return raw SQLAlchemy objects from API endpoints — convert to Pydantic
