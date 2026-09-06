#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/klayout_test_env.sh"
setup_klayout_test_env
"$klayout_bin" -rx -z -nc xs_test.gds -rd pyxs_test=test_rulers.py -r run_python_tests.py
