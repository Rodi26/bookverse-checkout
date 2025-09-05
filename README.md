# BookVerse Checkout Service

Minimal FastAPI service for BookVerse.

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

## CI/CD

This repository includes a GitHub Actions workflow at `.github/workflows/ci.yml` that:

- Runs tests with coverage
- Builds and pushes a Docker image to JFrog Artifactory
- Publishes Build Info
- Creates an AppTrust application version with build sources


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

- `${JFROG_URL}/artifactory/${PROJECT_KEY}-checkout-docker-internal-local/checkout:<semver>`

### Running the workflow

- Manual trigger: Actions → CI → Run workflow
- Later, enable push/PR triggers when ready