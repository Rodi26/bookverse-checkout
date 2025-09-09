# BookVerse Checkout Service

Minimal FastAPI service for BookVerse. Implements idempotent order creation,
stock validation against `bookverse-inventory`, and outbox pattern for
`order.created` domain events.

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

- `JFROG_ADMIN_TOKEN`: Admin or appropriate scoped token for API calls
- `JFROG_ACCESS_TOKEN`: Access token used by CI to interact with JFrog Platform
- `EVIDENCE_PRIVATE_KEY`: Private key PEM for evidence signing (mandatory)

### OIDC configuration

- JFrog OIDC provider name used by workflow: `github-bookverse-checkout`
- Audience: `jfrog-github`
- Ensure identity mapping enables this repo’s workflow OIDC to access the JFrog instance

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
