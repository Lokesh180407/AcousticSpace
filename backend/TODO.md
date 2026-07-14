# Acoustic Space Backend - TODO

## Steps
1. Create backend folder structure under `backend/app/` plus required root files (main.py, requirements.txt, Dockerfile, docker-compose.yml, .env.example, README.md).
   - Completed core scaffold in `backend/app/` (app_factory, middleware, exception handlers, health, base config, DB session).
2. Implement configuration, logging, and database layer (async SQLAlchemy + session management) and Alembic scaffolding.
3. Implement security/auth: JWT access+refresh, bcrypt hashing, RBAC, audit logging, register/login/refresh/logout, forgot/reset, email verification (architecture).
4. Implement user/profile features including avatar upload and password/settings management.
5. Implement projects, rooms, materials modules with full CRUD and related operations (invite/share/version/geometry/material assignment/floor plan upload).
6. Implement simulations persistence and status queue model; provide results storage and metrics fields.
7. Implement reports endpoints (PDF/CSV/Excel export endpoints + AI summary placeholder architecture only).
8. Implement uploads storage abstraction with local filesystem adapter.
9. Implement notifications module (in-app only) and AI module placeholder endpoints (no AI logic).
10. Implement middleware (CORS, secure headers, rate-limiting readiness hook) and global exception handling.
11. Add API routes under `/api/v1/` with full Swagger metadata.
12. Add tests with pytest for health and basic auth.
13. Run docker-compose build and local uvicorn smoke checks.

