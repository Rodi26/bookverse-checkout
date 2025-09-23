import logging
import os
import time


def configure_logging() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def run_dispatch_loop() -> None:
    logger = logging.getLogger("checkout-worker")
    interval_seconds = float(os.getenv("DISPATCH_INTERVAL_SECONDS", "5"))
    logger.info("Starting checkout worker (demo stub)")
    while True:
        logger.info("Dispatching queued order.created events (demo stub)")
        time.sleep(interval_seconds)


def main() -> None:
    configure_logging()
    run_dispatch_loop()


if __name__ == "__main__":
    main()


