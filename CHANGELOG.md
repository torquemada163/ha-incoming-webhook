# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-02-05

### Added
- Complete Home Assistant integration with UI configuration
- JWT authentication for secure webhook access
- Automatic switch entity creation (no manual setup required)
- Four webhook actions: `on`, `off`, `toggle`, `status`
- Custom attributes support for tracking context
- State persistence across Home Assistant restarts
- Health check endpoints (`/` and `/health`)
- Full API documentation

### Technical
- FastAPI webhook server running inside HA process
- Background task management with graceful shutdown
- Direct entity control (no REST API overhead)
- Pydantic request/response validation
