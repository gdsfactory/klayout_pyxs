#!/bin/bash -e

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$test_dir/.." && pwd)"
cd "$test_dir"

klayout_bin="${KLAYOUT_BIN:-klayout}"

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    if [[ "$klayout_bin" == [A-Za-z]:* ]]; then
      klayout_bin="$(cygpath -u "$klayout_bin")"
    fi

    klayout_home="$test_dir/run_dir/klayout_home"
    mkdir -p "$klayout_home"
    export KLAYOUT_HOME="$(cygpath -w "$klayout_home")"
    export KLAYOUT_PYTHONPATH="$(cygpath -w "$repo_root/klayout_package/python")${KLAYOUT_PYTHONPATH:+;$KLAYOUT_PYTHONPATH}"
    ;;
  *)
    export KLAYOUT_HOME=/dev/null
    export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
    export KLAYOUT_PYTHONPATH="$repo_root/klayout_package/python${KLAYOUT_PYTHONPATH:+:$KLAYOUT_PYTHONPATH}"
    ;;
esac

echo "Using KLayout:"
"$klayout_bin" -v
echo ""

rm -rf run_dir/3d
mkdir -p run_dir/3d

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

  if "$klayout_bin" -b -rd a="au/$tc.gds" -rd b="$xs_out" -rd tol=10 -r run_xor.rb \
    && diff -u \
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
