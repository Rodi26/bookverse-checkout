# BookVerse Checkout Service

Minimal FastAPI service for BookVerse. Implements idempotent order creation,
stock validation against `bookverse-inventory`, and outbox pattern for
`order.created` domain events.

## Testing Status
- Testing automatic CI triggers with 3 Docker images (API, Worker, Migrations)
- Validating commit filtering, application version creation, and auto-promotion

## Local run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Docker

```bash
docker build -t bookverse-checkout:dev .
docker run -p 8000:8000 bookverse-checkout:dev
```

## API

- POST `/orders` — create order (supports `Idempotency-Key` header)
- GET `/orders/{order_id}` — fetch order by id

## CI/CD

This repository includes a GitHub Actions workflow at `.github/workflows/ci.yml` that:

- Runs tests with coverage
- Builds and pushes one API image plus worker/migrations images
- Publishes Build Info and uploads OpenAPI and contract artifacts
- Creates an AppTrust application version with build sources
- Attaches coverage/SAST/quality/license evidence

### Required repository variables (Settings → Variables → Repository variables)

- `PROJECT_KEY`: `bookverse`
- `DOCKER_REGISTRY`: e.g., `releases.jfrog.io` (or your Artifactory Docker registry host)
- `JFROG_URL`: e.g., `https://releases.jfrog.io`
- `EVIDENCE_KEY_ALIAS`: alias for evidence signing key (non-secret)

### Required repository secrets (Settings → Secrets and variables → Actions)

- `EVIDENCE_PRIVATE_KEY`: Private key PEM for evidence signing (mandatory)

**Note**: No JFrog admin tokens required - all authentication uses OIDC.

### OIDC configuration

- JFrog OIDC provider name used by workflow: `github-bookverse-checkout`
- Audience: `jfrog-github`
- **All JFrog API authentication is handled via OIDC** - no admin tokens required
- Ensure identity mapping enables this repo's workflow OIDC to access the JFrog instance

### Image naming

- `${JFROG_URL}/artifactory/${PROJECT_KEY}-checkout-internal-docker-nonprod-local/checkout:<semver>`

### Mandatory OIDC application binding (.jfrog/config.yml)

This repository must include a committed, non-sensitive `.jfrog/config.yml` declaring the AppTrust application key. This is mandatory for package binding.

- During an OIDC-authenticated CI session, JFrog CLI reads the key so packages uploaded by the workflow are automatically bound to the correct AppTrust application.
- Contains no secrets and must be versioned. If the key changes, commit the update.

Path: `bookverse-checkout/.jfrog/config.yml`

Example:

```yaml
application:
  key: "bookverse-checkout"
```

### Running the workflow

- Manual trigger: Actions → CI → Run workflow
- Later, enable push/PR triggers when ready

## Workflows

- [`ci.yml`](.github/workflows/ci.yml) — CI for the checkout service: tests, multi-image build, publish artifacts/build-info, AppTrust version and evidence.
- [`promote.yml`](.github/workflows/promote.yml) — Promote the checkout application version through stages with evidence.
- [`promotion-rollback.yml`](.github/workflows/promotion-rollback.yml) — Roll back a promoted checkout application version (demo utility).
# Test comment for tag management validation - Sat Sep 20 20:13:08 IDT 2025
# Test fixed tag management library - Sat Sep 20 20:20:56 IDT 2025
# Debug test for tag management - Sat Sep 20 20:32:58 IDT 2025
# CRITICAL FIX TEST: Tag management should now work - Sat Sep 20 20:38:23 IDT 2025
# FINAL FIX TEST: Tag management should now work correctly - Sat Sep 20 20:41:57 IDT 2025
# CRITICAL TEMP FILE FIX: This should finally work - Sat Sep 20 20:45:38 IDT 2025
# STEP 1 TEST: Minimal tag management baseline - Sat Sep 20 20:53:06 IDT 2025
# STEP 2 TEST: API connectivity test - Sat Sep 20 20:57:54 IDT 2025
# STEP 3 TEST: Latest candidate identification - Sat Sep 20 21:01:56 IDT 2025
# STEP 4 TEST: Complete tag management system - Sat Sep 20 21:08:04 IDT 2025
# STEP 4 FIX TEST: Corrected API endpoints - Sat Sep 20 21:12:49 IDT 2025
# STEP 4 DEBUG TEST: Debug info and timing - Sat Sep 20 21:17:42 IDT 2025
# STEP 4 REAL DEBUG TEST: With actual debug code - Sat Sep 20 21:22:20 IDT 2025
# FINAL TEST: Complete self-healing tag management system - Sat Sep 20 21:27:16 IDT 2025
