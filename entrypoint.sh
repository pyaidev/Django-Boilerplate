#!/bin/sh
set -eu

if [ "${1:-}" = "gunicorn" ]; then
    # A fresh directory per master prevents stale metrics across restarts.
    PROMETHEUS_MULTIPROC_DIR="$(mktemp -d /tmp/boilerplate-metrics.XXXXXX)"
    export PROMETHEUS_MULTIPROC_DIR
fi
exec "$@"
