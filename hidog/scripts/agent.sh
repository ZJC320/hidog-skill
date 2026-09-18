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
  setup)
    [[ $# -eq 0 ]] || fail 'setup does not accept extra arguments'
    bash "$base/scripts/agent.sh" --prefix "$prefix" install
    version=$("$launcher" --version)
    [[ "$version" == 'hidogV11.2 11.2.0' ]] || fail "Unexpected runtime version; preserved: $version"
    mkdir -p "$prefix/self-tests"
    run=$(mktemp -d "$prefix/self-tests/setup.XXXXXXXX")
    printf 'Runtime: %s\nSelf-test log: %s/run.log\n' "$version" "$run"
    if ! bash "$base/scripts/agent.sh" --prefix "$prefix" example "$run/results" > "$run/run.log" 2>&1; then
      fail "Self-test execution failed; see $run/run.log"
    fi
    count=0
    while IFS= read -r -d '' stats; do
      awk -F '\t' '
        NR==1 {for(i=1;i<=NF;i++) {gsub(/\r/, "", $i); col[$i]=i};
               if(!col["Assigned reads"] || !col["Modified reads"] || !col["Editing frequency"]) exit 1; next}
        NF {rows++; if($(col["Assigned reads"])+0!=40 || $(col["Modified reads"])+0!=20 || $(col["Editing frequency"])+0!=50) bad=1}
        END {if(rows!=1 || bad) exit 1}' "$stats" || fail "Unexpected Stats: $stats"
      count=$((count+1))
    done < <(find "$run/results" -type f -name '*.stats.tsv' -print0)
    [[ "$count" -eq 2 ]] || fail "Expected two Stats reports; see $run"
    [[ -n "$(find "$run/results" -type f -name '*.xlsx' -print -quit)" ]] || fail 'Missing Excel report'
    [[ -n "$(find "$run/results" -type f -name '*.html' -print -quit)" ]] || fail 'Missing HTML report'
    printf 'SELFTEST PASS: Assigned=40 Modified=20 Editing_frequency=50%%\nResults: %s/results\n' "$run" | tee "$run/verification.txt"
    ;;
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
  *) fail 'Action must be setup, check, install, run or example' ;;
esac
