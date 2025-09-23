


import os
from fastapi import FastAPI

from bookverse_core.api.app_factory import create_app
from bookverse_core.api.middleware import RequestIDMiddleware, LoggingMiddleware
from bookverse_core.api.health import create_health_router
from bookverse_core.config import BaseConfig
from bookverse_core.utils.logging import (
    setup_logging,
    LogConfig,
    get_logger,
    log_service_startup
)

from .database import create_all
from .api import router

log_config = LogConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    include_request_id=True
)
setup_logging(log_config, "checkout")

logger = get_logger(__name__)

service_version = os.getenv("SERVICE_VERSION", "0.1.0-dev")
log_service_startup(logger, "BookVerse Checkout Service", service_version)

app = create_app(
    title="BookVerse Checkout Service",
    description="Order processing and payment handling service for BookVerse platform",
    version=service_version,
    enable_cors=True,
    enable_auth=False,
    include_health_endpoints=True,
    include_info_endpoint=True
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)

health_router = create_health_router(
    service_name="checkout",
    service_version=service_version
)
app.include_router(health_router, prefix="/health", tags=["health"])

@app.on_event("startup")
def on_startup():
    create_all()
    logger.info("✅ Database initialized successfully")
    logger.info("🚀 BookVerse Checkout Service started successfully")

app.include_router(router, prefix="/api/v1", tags=["checkout"])


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

