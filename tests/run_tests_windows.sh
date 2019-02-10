#!/bin/bash -e

#

# Add klayout install folder to path
export PATH=$PATH:"/C/Program Files (x86)/KLayout"

# Check klayout version
echo "Using KLayout:"
klayout_app -v
echo ""

rm -rf run_dir
mkdir -p run_dir

failed=""

# Location of the python macros pyxs.lym (dev version)
bin=../klayout_pyxs/pymacros/pyxs.lym

if [ "$1" == "" ]; then
  all_xs=( *.pyxs )  # will test all .pyxs files in the folder
  tc_files=${all_xs[@]}
else
  tc_files=$*  # will test only specified file
fi

for tc_file in $tc_files; do

  tc=`echo $tc_file | sed 's/\.pyxs$//'`

  echo "---------------------------------------------------"
  echo "Running testcase $tc .."

  # Check which gds file to use
  xs_input=$(grep XS_INPUT $tc.pyxs | sed 's/.*XS_INPUT *= *//')
  if [ "$xs_input" = "" ]; then
    xs_input="xs_test.gds"
  fi

  # Check which ruler to use for a cross-section
  xs_cut=$(grep XS_CUT $tc.pyxs | sed 's/.*XS_CUT *= *//')
  if [ "$xs_cut" = "" ]; then
    xs_cut="-1,0;1,0"
  fi

  echo $tc.pyxs
  echo $xs_cut
  echo $tc.gds
  echo $xs_input
  echo $bin

  klayout_app -rx -z -rd xs_run=$tc.pyxs -rd xs_cut="$xs_cut" -rd xs_out=run_dir/$tc.gds "$xs_input" -r $bin

  if klayout_app -b -rd a=au/$tc.gds -rd b=run_dir/$tc.gds -rd tol=10 -r run_xor.rb; then
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
fi
