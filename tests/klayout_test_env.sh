#!/usr/bin/env bash
# Shared setup for the 2D, 3D, compatibility, and ruler test runners.

setup_klayout_test_env() {
  test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  repo_root="$(cd "$test_dir/.." && pwd)"
  klayout_bin="${KLAYOUT_BIN:-klayout}"

  # A fresh home avoids stale modules and conflicts with another test process.
  klayout_home="$(mktemp -d "${TMPDIR:-/tmp}/pyxs-klayout.XXXXXX")"
  trap 'rm -rf -- "$klayout_home"' EXIT

  # In 0.28 KLAYOUT_PYTHONPATH can replace the standard-library search path.
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

  mkdir -p "$klayout_home/python"
  cp -R "$repo_root/klayout_package/python/klayout_pyxs" "$klayout_home/python/"
  cd "$test_dir"

  echo "Using KLayout:"
  "$klayout_bin" -v
}
