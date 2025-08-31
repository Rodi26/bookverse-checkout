#!/usr/bin/env sh
set -e

OUT_DIR=${OUT_DIR:-dist}
mkdir -p "$OUT_DIR"

tar -czf "$OUT_DIR/checkout-config.bundle.tar.gz" -C config defaults.env
echo "Wrote $OUT_DIR/checkout-config.bundle.tar.gz"


