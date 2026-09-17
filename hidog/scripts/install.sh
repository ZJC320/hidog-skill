#!/usr/bin/env bash
set -euo pipefail
version=v11.2.0-rc.1
prefix="${HOME}/.local/share/hidog"
usage() {
  echo 'Usage: bash install.sh [--version v11.2.0-rc.1] [--prefix ABSOLUTE_DIRECTORY]'
  echo 'Installs the compiled Linux x86_64 release and a private tool environment.'
}
fail() { echo "ERROR: $*" >&2; exit 1; }
while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --version|--prefix)
      [[ $# -ge 2 ]] || fail "Missing value for $1"
      if [[ "$1" == --version ]]; then version=$2; else prefix=$2; fi
      shift 2 ;;
    *) fail "Unknown argument: $1" ;;
  esac
done
[[ "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[a-z0-9]+\.[0-9]+)?$ ]] || fail 'Invalid version'
[[ "$prefix" == /* && "$prefix" != / ]] || fail 'prefix must be an absolute user directory'
[[ "$(uname -s)" == Linux && "$(uname -m)" == x86_64 ]] || fail 'Requires Linux/WSL x86_64'
for tool in curl tar sha256sum awk grep mktemp realpath getconf; do
  command -v "$tool" >/dev/null || fail "Missing prerequisite: $tool"
done
glibc=$(getconf GNU_LIBC_VERSION 2>/dev/null) || fail 'Requires a glibc Linux system'
glibc=${glibc#glibc }
awk -v v="$glibc" 'BEGIN {split(v,a,"."); exit !(a[1]>2 || (a[1]==2 && a[2]>=31))}' || fail 'Requires glibc >= 2.31 (Ubuntu 20.04 or compatible)'
prefix=$(realpath -m "$prefix")
[[ "$prefix" != / && "$prefix" != *$'\n'* ]] || fail 'Unsafe installation prefix'
destination="$prefix/$version"
[[ ! -e "$destination" && ! -L "$destination" ]] || fail "Version directory exists: $destination; use its bin/hidog or choose a new prefix"
if [[ -e "$prefix/bin/hidog" || -L "$prefix/bin/hidog" ]]; then
  [[ -L "$prefix/bin/hidog" ]] || fail "Refusing to replace existing file: $prefix/bin/hidog"
  case "$(readlink "$prefix/bin/hidog")" in
    "$prefix"/*/bin/hidog) ;;
    *) fail 'Existing launcher points outside this installation prefix' ;;
  esac
fi
mkdir -p "$prefix"
download=$(mktemp -d "$prefix/.download.XXXXXXXX")
trap 'echo "Installation failed; downloaded files/logs retained at: $download" >&2' ERR
asset="hidog-${version}-linux-x86_64.tar.gz"
base="https://github.com/ZJC320/hidog-skill/releases/download/$version"
fetch() { curl --proto '=https' --tlsv1.2 --fail --location --retry 2 --connect-timeout 20 --max-time 1800 "$1" -o "$2"; }
fetch "$base/$asset" "$download/$asset"
fetch "$base/$asset.sha256" "$download/$asset.sha256"
# Read only the digest; never trust downloaded checksum filenames as local paths.
digest=$(awk 'NR==1 {print $1}' "$download/$asset.sha256")
[[ "$digest" =~ ^[0-9a-f]{64}$ ]] || fail 'Malformed SHA256 file'
printf '%s  %s\n' "$digest" "$asset" > "$download/verified.sha256"
(cd "$download" && sha256sum -c verified.sha256) || fail 'Download checksum mismatch'
tar -tzf "$download/$asset" > "$download/members.txt"
if grep -Eq '(^/|(^|/)\.\.(/|$))' "$download/members.txt"; then
  fail 'Unsafe archive path'
fi
if ! tar -tvzf "$download/$asset" | awk 'substr($0,1,1)!="-" && substr($0,1,1)!="d" {bad=1} END {exit bad}'; then
  fail 'Archive contains links or special files'
fi
mkdir "$destination"
tar --no-same-owner --no-same-permissions -xzf "$download/$asset" -C "$destination"
[[ -x "$destination/app/hidog.bin" && -x "$destination/bootstrap/micromamba" && -f "$destination/runtime-linux-64.lock" ]] || fail 'Incomplete release payload'
[[ "$(cat "$destination/VERSION")" == "$version" ]] || fail 'Release version mismatch'
export MAMBA_ROOT_PREFIX="$destination/mamba"
export MAMBA_NO_BANNER=1
"$destination/bootstrap/micromamba" --no-rc create -y -p "$destination/runtime" \
  --file "$destination/runtime-linux-64.lock" > "$destination/install-runtime.log" 2>&1 || fail "Dependency installation failed; see $destination/install-runtime.log; incomplete directory retained"
mkdir -p "$destination/bin"
cat > "$destination/bin/hidog" <<'LAUNCHER'
#!/usr/bin/env bash
set -euo pipefail
entry=$(readlink -f "${BASH_SOURCE[0]}")
root=$(cd "$(dirname "$entry")/.." && pwd)
export MAMBA_ROOT_PREFIX="$root/mamba"
export MAMBA_NO_BANNER=1
exec "$root/bootstrap/micromamba" --no-rc run -p "$root/runtime" "$root/app/hidog.bin" "$@"
LAUNCHER
chmod 755 "$destination/bin/hidog"
"$destination/bin/hidog" --version
"$destination/bin/hidog" vector-trace --help >/dev/null
"$destination/bootstrap/micromamba" --no-rc run -p "$destination/runtime" samtools --version > "$destination/tool-versions.txt"
"$destination/bootstrap/micromamba" --no-rc run -p "$destination/runtime" trimmomatic -version >> "$destination/tool-versions.txt" 2>&1
mkdir -p "$prefix/bin"
ln -sfn "$destination/bin/hidog" "$prefix/bin/hidog"
trap - ERR
printf '\nInstalled: %s\nRun: %s --help\nLogs and downloads: %s\n' "$version" "$prefix/bin/hidog" "$download"
