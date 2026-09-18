#!/usr/bin/env bash
set -euo pipefail
base=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
target="${HOME}/.claude/skills/hidog"
[[ "$(uname -s)" == Linux ]] || { echo 'Use Linux/WSL for this HiDOG release.' >&2; exit 1; }
[[ -f "$base/hidog/SKILL.md" ]] || { echo 'Extract the complete package first.' >&2; exit 1; }
if [[ -e "$target" || -L "$target" ]]; then
  echo "Skill already exists; preserved unchanged: $target" >&2
  exit 1
fi
mkdir -p "$(dirname "$target")"
mkdir "$target"
cp -R "$base/hidog/." "$target/"
printf 'Skill installed: %s\nOpen Claude Code and use /hidog. First analysis installs the compiled runtime online.\n' "$target"
