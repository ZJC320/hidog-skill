#!/usr/bin/env bash
# The installing agent selects its own client; no user package selection is needed.
set -euo pipefail
base=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
client= skills= prefix="${HOME}/.local/share/hidog"
fail() { echo "ERROR: $*" >&2; exit 1; }
while [[ $# -gt 0 ]]; do
  case "$1" in
    --client|--skills-dir|--prefix)
      [[ $# -ge 2 ]] || fail "Missing value for $1"
      case "$1" in --client) client=$2;; --skills-dir) skills=$2;; --prefix) prefix=$2;; esac
      shift 2 ;;
    *) fail "Unknown argument: $1" ;;
  esac
done
[[ "$(uname -s)" == Linux && "$(uname -m)" == x86_64 ]] || fail 'Requires Linux/WSL x86_64'
case "$client" in
  codex) skills=${skills:-${HOME}/.agents/skills} ;;
  claude) skills=${skills:-${HOME}/.claude/skills} ;;
  '') [[ -n "$skills" ]] || fail 'The agent must select --client codex/claude or --skills-dir' ;;
  *) fail 'Unknown client; use --skills-dir for other agents' ;;
esac
[[ "$skills" == /* && "$skills" != / ]] || fail 'skills-dir must be an absolute user directory'
[[ -f "$base/hidog/SKILL.md" ]] || fail 'Download and extract the complete package'
target="$skills/hidog"
[[ ! -L "$target" ]] || fail "Existing skill is a symlink; preserved: $target"
if [[ -e "$target" ]]; then
  diff -qr "$base/hidog" "$target" >/dev/null || fail "Existing skill differs; preserved: $target"
else
  mkdir -p "$skills"
  mkdir "$target"
  cp -R "$base/hidog/." "$target/"
fi
printf 'Skill registered: %s\n' "$target"
exec bash "$target/scripts/agent.sh" --prefix "$prefix" setup
