# BookVerse Checkout Service

Demo-ready FastAPI microservice for the BookVerse platform, showcasing JFrog AppTrust capabilities with complex multi-container application patterns.

## 🎯 Demo Purpose & Patterns

This service demonstrates the **Multi-Container Application Pattern** - showcasing how complex applications with multiple runtime components can be managed as a single application version in AppTrust.

### 📦 **Multi-Container Application Pattern**
- **What it demonstrates**: Application versions built from multiple Docker containers (main service + worker + database migrations)
- **AppTrust benefit**: Complex applications with multiple containers promoted together through all stages (DEV → QA → STAGING → PROD)
- **Real-world applicability**: Enterprise applications with background workers, database migrations, and auxiliary services

This service is **intentionally complex** - it demonstrates real-world patterns where applications need multiple runtime components working together.

## 🏗️ Checkout Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  BookVerse Platform                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐                      ┌─────────────┐       │
│  │     Web     │                      │  Inventory  │       │
│  │  Frontend   │                      │   Service   │       │
│  └─────────────┘                      └─────────────┘       │
│         │                                    │               │
│         │            ┌───────────────┐      │               │
│         └────────────│   Checkout    │──────┘               │
│                      │    Service    │                      │
│                      │               │                      │
│                      │ Multi-Container │                    │
│                      │  Application   │                     │
│                      │ ┌─────────────┐ │                    │
│                      │ │    API      │ │                    │
│                      │ │   Service   │ │                    │
│                      │ └─────────────┘ │                    │
│                      │ ┌─────────────┐ │                    │
│                      │ │  Background │ │                    │
│                      │ │   Worker    │ │                    │
│                      │ └─────────────┘ │                    │
│                      │ ┌─────────────┐ │                    │
│                      │ │   Payment   │ │                    │
│                      │ │    Mock     │ │                    │
│                      │ └─────────────┘ │                    │
│                      └───────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘

AppTrust Promotion Pipeline:
DEV → QA → STAGING → PROD
 │     │       │        │
 └─────┴───────┴────────┘
   Multiple Container Images
   Move Together as One Version
```

## 🔧 JFrog AppTrust Integration

This service creates multiple artifacts per application version:

1. **Multiple Docker Images** - API service, background worker, payment mock, database migrations
2. **Python Packages** - Shared libraries and service packages
3. **SBOMs** - Software Bill of Materials for all container images
4. **Test Reports** - E2E testing across all components
5. **Build Evidence** - Comprehensive build and security attestations

Each artifact moves together through the promotion pipeline: DEV → QA → STAGING → PROD.

For the non-JFrog evidence plan and gates, see: `../bookverse-demo-init/docs/EVIDENCE_PLAN.md`.

## 🔄 Workflows

- [`ci.yml`](.github/workflows/ci.yml) — CI: tests, multi-container builds, publish artifacts/build-info, AppTrust version and evidence
- [`promote.yml`](.github/workflows/promote.yml) — Promote the checkout app version through stages with evidence
- [`promotion-rollback.yml`](.github/workflows/promotion-rollback.yml) — Roll back a promoted checkout application version (demo utility)
