#!/bin/bash -e

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export KLAYOUT_BIN="${KLAYOUT_BIN:-klayout_app}"

exec bash "$test_dir/run_tests_3d.sh" "$@"
