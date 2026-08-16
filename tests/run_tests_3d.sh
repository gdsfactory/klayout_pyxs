#!/bin/bash -e

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$test_dir/.." && pwd)"
cd "$test_dir"

klayout_bin="${KLAYOUT_BIN:-klayout}"
klayout_home="$test_dir/run_dir/klayout_home"

# KLAYOUT_PYTHONPATH replaces the embedded interpreter's standard-library path
# in KLayout 0.28.  Stage the package in KLAYOUT_HOME/python instead.
unset KLAYOUT_PYTHONPATH

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    if [[ "$klayout_bin" == [A-Za-z]:* ]]; then
      klayout_bin="$(cygpath -u "$klayout_bin")"
    fi

    export KLAYOUT_HOME="$(cygpath -w "$klayout_home")"
    ;;
  *)
    export KLAYOUT_HOME="$klayout_home"
    export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
    ;;
esac

echo "Using KLayout:"
"$klayout_bin" -v
echo ""

rm -rf run_dir/3d
mkdir -p run_dir/3d
mkdir -p "$klayout_home/python"
cp -R "$repo_root/klayout_package/python/klayout_pyxs" "$klayout_home/python/"

failed=""
runner="$test_dir/run_3d.py"

if [ "$1" == "" ]; then
  all_xs=( *.pyxs3d )
  tc_files=${all_xs[@]}
else
  tc_files=$*
fi

for tc_file in $tc_files; do

  tc=$(echo "$tc_file" | sed 's/\.pyxs3d$//')

  echo "---------------------------------------------------"
  echo "Running 3D testcase $tc .."

  xs_input=$(grep XS_INPUT "$tc_file" | sed 's/.*XS_INPUT *= *//')
  if [ "$xs_input" = "" ]; then
    xs_input="xs_test.gds"
  fi

  xs_out="run_dir/3d/$tc.gds"
  "$klayout_bin" -rx -z -rd xs_run="$tc_file" -rd xs_out="$xs_out" "$xs_input" -r "$runner"

  # Blank lines in KLayout's generated tech file are not semantically meaningful.
  if "$klayout_bin" -b -rd a="au/$tc.gds" -rd b="$xs_out" -rd tol=10 -r run_xor.rb \
    && diff -u -B \
      <(grep -Ev '^(Red|Green|Blue):' "au/$tc.gds_tech") \
      <(grep -Ev '^(Red|Green|Blue):' "$xs_out"_tech); then
    echo "No differences found."
  else
    failed="$failed $tc"
  fi

done

echo "---------------------------------------------------"
if [ "$failed" = "" ]; then
  echo "All 3D tests successful."
else
  echo "*** 3D TESTS FAILED:$failed"
  exit 1
fi
