#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/klayout_test_env.sh"
setup_klayout_test_env
mkdir -p run_dir/3d

failed=()
runner="$test_dir/run_3d.py"
if (( $# )); then
  tc_files=( "$@" )
else
  shopt -s nullglob
  tc_files=( *.pyxs3d )
fi
if (( ${#tc_files[@]} == 0 )); then
  echo "No 3D testcases found." >&2
  exit 1
fi

for tc_file in "${tc_files[@]}"; do
  tc="$(basename "$tc_file" .pyxs3d)"
  echo "---------------------------------------------------"
  echo "Running 3D testcase $tc .."

  xs_input="$(sed -n 's/.*XS_INPUT *= *//p' "$tc_file")"
  xs_input="${xs_input:-xs_test.gds}"
  xs_out="run_dir/3d/$tc.gds"
  rm -f -- "$xs_out" "${xs_out}_tech"

  # RGB values and blank lines in the generated tech file are not semantic.
  if "$klayout_bin" -rx -z -nc -rm "$test_dir/raise_on_gui_error.py" \
      -rd "xs_run=$tc_file" -rd "xs_out=$xs_out" \
      "$xs_input" -r "$runner" \
    && "$klayout_bin" -b -nc -rd "a=au/$tc.gds" -rd "b=$xs_out" \
      -rd tol=10 -r run_xor.rb \
    && test -s "au/$tc.gds_tech" && test -s "${xs_out}_tech" \
    && diff -u -B \
      <(sed -E '/^(Red|Green|Blue):/d' "au/$tc.gds_tech") \
      <(sed -E '/^(Red|Green|Blue):/d' "${xs_out}_tech"); then
    echo "No differences found."
  else
    failed+=( "$tc" )
  fi
done

echo "---------------------------------------------------"
if (( ${#failed[@]} )); then
  echo "*** 3D TESTS FAILED: ${failed[*]}"
  exit 1
fi
echo "All ${#tc_files[@]} 3D tests successful."
