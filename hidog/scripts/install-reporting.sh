#!/usr/bin/env bash
# Separate reporting environment: the core runtime and its lock remain unchanged.
set -euo pipefail
base=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
prefix=${1:?Expected absolute HiDOG prefix}
core="$prefix/v11.2.0-rc.1/runtime/bin/python"
destination="$prefix/reporting-1.2.0"
[[ -x "$core" ]] || { echo 'Install the fixed HiDOG core first' >&2; exit 1; }
digest=$(sha256sum "$base/reporting-requirements.txt" | cut -d ' ' -f1)
if [[ -e "$destination" ]]; then
  [[ -f "$destination/requirements.sha256" && "$(cat "$destination/requirements.sha256")" == "$digest" ]] || {
    echo "Incomplete or different reporting environment; preserved: $destination" >&2; exit 1;
  }
else
  "$core" -m venv "$destination"
  "$destination/bin/python" -m pip --isolated install --disable-pip-version-check --no-input \
    --index-url https://pypi.org/simple --only-binary=:all: --require-hashes \
    -r "$base/reporting-requirements.txt" > "$destination/install.log" 2>&1 || {
      echo "Report dependency installation failed; see $destination/install.log" >&2; exit 1;
    }
  printf '%s\n' "$digest" > "$destination/requirements.sha256"
fi
"$destination/bin/python" -m pip --isolated check
"$destination/bin/python" -c 'import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot'
printf 'Reporting environment ready: %s\n' "$destination"
