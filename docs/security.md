# IP-SAKTI Sahayak — Security & Privacy Architecture

## Security Controls

1. **Strict Input Sanitization & Type Validation**: Pydantic v2 validation across all request payloads, query length limits, and file size checks.
2. **SQL Injection Prevention**: Full use of SQLAlchemy async parameterized queries and typed ORM models.
3. **CORS & Origin Hardening**: Explicit origin whitelisting via environment variable (`CORS_ORIGINS`).
4. **Environment Secrets**: Zero hardcoded secrets; all database passwords, JWT signing keys, and OpenAI credentials must be passed via `.env`.
5. **Rate Limiting**: Configurable IP-based rate limiting via SlowAPI / FastAPI middleware.

---

## Privacy by Design (User Document Protection)

When users upload drafts or examination notices to `/api/documents/upload`:
- **Ephemeral Processing**: The file is parsed in-memory solely to retrieve relevant statutory references and is discarded immediately after analysis.
- **No Model Training**: User data is never fed back into embedding indexes or training datasets.
- **Clear Boundary**: The UI and API explicitly delineate *User Documents* from *Authoritative Statutory Law*.
