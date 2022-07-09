#!/bin/bash -e

# This script contains replacement patterns to convert XS to PYXS
# It implements some of the required changes, however more changes
# might be needed.

if [ "$1" == "" ]; then
  all_xs=( *.xs )  # will convert all .xs files in the folder
  xs_files=${all_xs[@]}
else
  xs_files=$*  # will convert only specified file(s)
fi

for xs_file in $xs_files; do
    pyxs_file=$(echo "$xs_file" | sed 's/\.xs$/\.pyxs/')
    sed -r --file=xs2pyxs_patterns.txt < "$xs_file" > "$pyxs_file"
done
