#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/klayout_test_env.sh"
setup_klayout_test_env
mkdir -p run_dir

failed=()
bin="$repo_root/klayout_package/pymacros/pyxs.lym"
if (( $# )); then
  tc_files=( "$@" )
else
  shopt -s nullglob
  tc_files=( *.pyxs )
fi
if (( ${#tc_files[@]} == 0 )); then
  echo "No 2D testcases found." >&2
  exit 1
fi

for tc_file in "${tc_files[@]}"; do
  tc="$(basename "$tc_file" .pyxs)"
  echo "---------------------------------------------------"
  echo "Running testcase $tc .."

  xs_input="$(sed -n 's/.*XS_INPUT *= *//p' "$tc_file")"
  xs_cut="$(sed -n 's/.*XS_CUT *= *//p' "$tc_file")"
  xs_input="${xs_input:-xs_test.gds}"
  xs_cut="${xs_cut:--1,0;1,0}"
  xs_out="run_dir/$tc.gds"
  # A failed generation must not be compared against an earlier run's output.
  rm -f -- "$xs_out"

  if "$klayout_bin" -rx -z -nc -rm "$test_dir/raise_on_gui_error.py" \
      -rd "xs_run=$tc_file" -rd "xs_cut=$xs_cut" \
      -rd "xs_out=$xs_out" "$xs_input" -r "$bin" \
    && "$klayout_bin" -b -nc -rd "a=au/$tc.gds" -rd "b=$xs_out" \
      -rd tol=10 -r run_xor.rb; then
    echo "No differences found."
  else
    failed+=( "$tc" )
  fi
done

echo "---------------------------------------------------"
if (( ${#failed[@]} )); then
  echo "*** TESTS FAILED: ${failed[*]}"
  exit 1
fi
echo "All ${#tc_files[@]} 2D tests successful."
