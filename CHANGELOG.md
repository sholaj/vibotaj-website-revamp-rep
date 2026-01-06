# Changelog

All notable changes to the TraceHub project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CLAUDE.md context engineering file for AI-assisted development
- Compliance matrix documentation (`docs/COMPLIANCE_MATRIX.md`)
- Architecture Decision Record for EUDR removal (`docs/decisions/001-eudr-removal.md`)
- Slash commands for development workflow in `.claude/commands/`
  - `generate-prp.md` - Generate Product Requirements Prompts
  - `fix-bug.md` - TDD bug fix workflow
  - `code-review.md` - Code review checklist
- PRP directory structure (`PRPs/active/`, `PRPs/completed/`, `PRPs/templates/`)
- API documentation placeholder (`docs/API.md`)
- Deployment guide placeholder (`docs/DEPLOYMENT.md`)
- Root-level Makefile for common development commands
- Pre-commit hooks configuration for secret scanning
- Test structure with compliance test examples

### Changed
- Repository structure consolidated and reorganized
- Documentation moved to `/docs/` directory
- Root-level documentation archived to `docs/_archive/root-cleanup/`
- `.gitignore` updated with additional security-critical patterns

### Fixed
- Corrected EUDR applicability for horn/hoof products (HS 0506/0507) - NOT covered by EUDR

### Security
- Pre-commit hooks added for secret scanning
- Enhanced `.gitignore` patterns for credentials and API keys
- Security scan workflow added to Makefile

---

## [0.1.0] - 2026-01-06

### Added
- Initial TraceHub platform structure
- FastAPI backend with PostgreSQL
- React 18 frontend with TypeScript
- Multi-tenancy support (Sprint 8)
- Organization model for customer separation
- HAGES organization and users created
- Document classification system
- Container tracking integration
- Compliance validation framework

---

## Release Notes

### Version 0.1.0 - Initial Release

**Focus:** Single-shipment POC and multi-tenancy foundation

**Key Features:**
- Real-time container tracking
- Document lifecycle management
- Compliance validation
- Multi-tenant architecture
- Role-based access control

**Known Issues:**
- EUDR fields incorrectly applied to horn/hoof products (fixed in next release)
- Limited test coverage
- API documentation incomplete

---

**Versioning Convention:**
- **Major (X.0.0):** Breaking changes, major features
- **Minor (0.X.0):** New features, backward compatible
- **Patch (0.0.X):** Bug fixes, minor improvements

**Categories:**
- **Added:** New features
- **Changed:** Changes to existing functionality
- **Deprecated:** Soon-to-be removed features
- **Removed:** Removed features
- **Fixed:** Bug fixes
- **Security:** Security fixes and improvements
