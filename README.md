# BookVerse Checkout Service

This repository is part of the JFrog AppTrust BookVerse demo. The demo showcases end-to-end secure delivery using the JFrog Platform: AppTrust lifecycle and promotion, signed SBOMs, Xray policy enforcement, and GitHub Actions OIDC for passwordless CI/CD.

## What this service does
The Checkout service handles order placement, payment orchestration, and receipt generation. In the demo, it represents a Python microservice packaged as a Python distribution and a Docker image.

## How this repo fits the demo
- CI builds Python and Docker artifacts
- SBOM generation and signing (placeholders in scaffold)
- Publish to Artifactory internal repos (DEV/QA/STAGING)
- Manual promotion workflow moves artifacts through AppTrust stages to PROD
- OIDC enables secure GitHub Actions authentication to JFrog

## Repository layout
- `.github/workflows/ci.yml` – CI pipeline (test → build → SBOM/sign → publish)
- `.github/workflows/promote.yml` – Manual promotion workflow
- Application code, `Dockerfile`, and packaging files to be added as the demo evolves

## CI Expectations
Configure GitHub variables at org/repo level:
- `PROJECT_KEY` = `bookverse`
- `JFROG_URL` = base URL of your JFrog instance
- `DOCKER_REGISTRY` = Docker registry hostname in Artifactory

Internal repositories:
- Docker: `bookverse-checkout-docker-internal-local`
- Python: `bookverse-checkout-python-internal-local`

Release repositories:
- Docker: `bookverse-checkout-docker-release-local`
- Python: `bookverse-checkout-python-release-local`

## Promotion
Use `.github/workflows/promote.yml` and choose QA, STAGING, or PROD. Evidence placeholders illustrate gated promotion (tests, approvals, change refs).

## Related demo resources
- BookVerse scenario overview in the AppTrust demo materials
- Related repos: `bookverse-inventory`, `bookverse-recommendations`, `bookverse-platform`, `bookverse-demo-assets`

---
This repository is intentionally minimal to focus on platform capabilities. Extend it with real business logic as needed for demonstrations.