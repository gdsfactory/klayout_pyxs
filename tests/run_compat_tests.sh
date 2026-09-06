#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/klayout_test_env.sh"
setup_klayout_test_env
"$klayout_bin" -b -nc -rd pyxs_test=test_compat.py -r run_python_tests.py
