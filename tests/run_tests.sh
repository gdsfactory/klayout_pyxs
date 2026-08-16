#!/bin/bash -e

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$test_dir/.." && pwd)"
cd "$test_dir"

klayout_bin="${KLAYOUT_BIN:-klayout}"
klayout_home=""

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    if [[ "$klayout_bin" == [A-Za-z]:* ]]; then
      klayout_bin="$(cygpath -u "$klayout_bin")"
    fi

    klayout_home="$test_dir/run_dir/klayout_home"
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

rm -rf run_dir
mkdir -p run_dir
if [ -n "$klayout_home" ]; then
  mkdir -p "$klayout_home"
fi

failed=""

bin="$repo_root/klayout_package/pymacros/pyxs.lym"

if [ "$1" == "" ]; then
  all_xs=( *.pyxs )
  tc_files=${all_xs[@]}
else
  tc_files=$*
fi

for tc_file in $tc_files; do

  tc=$(echo "$tc_file" | sed 's/\.pyxs$//')

  echo "---------------------------------------------------"
  echo "Running testcase $tc .."

  xs_input=$(grep XS_INPUT $tc.pyxs | sed 's/.*XS_INPUT *= *//')
  if [ "$xs_input" = "" ]; then
    xs_input="xs_test.gds"
  fi
  xs_cut=$(grep XS_CUT $tc.pyxs | sed 's/.*XS_CUT *= *//')
  if [ "$xs_cut" = "" ]; then
    xs_cut="-1,0;1,0"
  fi

  "$klayout_bin" -rx -z -rd xs_run=$tc.pyxs -rd xs_cut="$xs_cut" -rd xs_out=run_dir/$tc.gds "$xs_input" -r "$bin"

  if "$klayout_bin" -b -rd a=au/"$tc".gds -rd b=run_dir/"$tc".gds -rd tol=10 -r run_xor.rb; then
    echo "No differences found."
  else
    failed="$failed $tc"
  fi

done

echo "---------------------------------------------------"
if [ "$failed" = "" ]; then
  echo "All tests successful."
else
  echo "*** TESTS FAILED:$failed"
  exit 1
fi
