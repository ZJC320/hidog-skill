#!/usr/bin/env bash
# Shared local entry point for desktop agents; forwards the original HiDOG CLI.
set -euo pipefail
base=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
prefix="${HOME}/.local/share/hidog"
fail() { echo "ERROR: $*" >&2; exit 1; }
if [[ "${1:-}" == --prefix ]]; then
  [[ $# -ge 3 ]] || fail 'Expected --prefix ABSOLUTE_DIRECTORY ACTION'
  prefix=$2
  shift 2
fi
[[ "$prefix" == /* && "$prefix" != / ]] || fail 'prefix must be an absolute user directory'
action=${1:-check}
[[ $# -eq 0 ]] || shift
[[ "$(uname -s)" == Linux && "$(uname -m)" == x86_64 ]] || fail 'Requires Linux/WSL x86_64'
launcher="$prefix/bin/hidog"
case "$action" in
  check|install)
    [[ $# -eq 0 ]] || fail 'Unexpected arguments'
    if [[ -x "$launcher" ]]; then
      exec "$launcher" --version
    elif [[ "$action" == install ]]; then
      exec bash "$base/scripts/install.sh" --prefix "$prefix"
    else
      fail 'HiDOG is not installed. Run this entry point with action install.'
    fi ;;
  run)
    [[ -x "$launcher" ]] || fail 'Run action install first'
    exec "$launcher" "$@" ;;
  example)
    [[ $# -le 1 ]] || fail 'example accepts one absolute output directory'
    [[ -x "$launcher" ]] || fail 'Run action install first'
    output=${1:-${HOME}/hidog-results/example-$(date +%Y%m%d-%H%M%S)-$$}
    [[ "$output" == /* && "$output" != / ]] || fail 'Use an absolute output directory'
    [[ ! -e "$output" && ! -L "$output" ]] || fail "Output already exists: $output"
    mkdir -p "$(dirname "$output")"
    exec "$launcher" -t disjoint --editing-tool dualPE \
      -r "$base/examples/reference.fa" \
      -i "$base/examples/replacement_R1.fq.gz" -I "$base/examples/replacement_R2.fq.gz" \
      -b "$base/examples/barcodes.tsv" -o "$output" -T 2 \
      --spacer-length 0 --barcode-length 4 --bridge-length 0 \
      --prime_editing_pegRNA_spacer_seq "$base/examples/spacers.fa" \
      --prime_editing_pegRNA_extension_seq "$base/examples/extensions.fa" \
      --prime_editing_override_prime_edited_ref_seq "$base/examples/expected.fa" \
      --min-genotype-depth 1 --min-ratio 0 ;;
  *) fail 'Action must be check, install, run or example' ;;
esac
