"""
Configuration for BookVerse Checkout Service.
"""

import os
from dataclasses import dataclass


@dataclass
class ServiceConfig:
    database_url: str
    inventory_base_url: str
    request_timeout_seconds: float
    retry_attempts: int
    payment_success_ratio: float
    log_level: str


def load_config() -> ServiceConfig:
    return ServiceConfig(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./checkout.db"),
        inventory_base_url=os.getenv("INVENTORY_BASE_URL", "http://localhost:8001"),
        request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "2")),
        retry_attempts=int(os.getenv("RETRY_ATTEMPTS", "2")),
        payment_success_ratio=float(os.getenv("PAYMENT_SUCCESS_RATIO", "1.0")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


