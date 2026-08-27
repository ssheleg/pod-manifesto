#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

required_files=(
  README.md
  CONTRIBUTING.md
  CODE_OF_CONDUCT.md
  SECURITY.md
  SUPPORT.md
  GOVERNANCE.md
  CITATION.cff
  .github/CODEOWNERS
  .github/PULL_REQUEST_TEMPLATE.md
  .github/ISSUE_TEMPLATE/config.yml
  .github/ISSUE_TEMPLATE/objection.yml
  .github/ISSUE_TEMPLATE/translation.yml
  docs/DOCMAP.md
  docs/DECISIONS.md
  docs/OPEN_QUESTIONS.md
  docs/ux/foundation.md
  docs/ux/screens.md
  docs/ux/scenarios.md
  docs/evidence/backlog.md
  docs/evidence/verification.md
  docs/evidence/retro.md
)

check_required() {
  local root="$1"
  local path
  local failed=0
  for path in "${required_files[@]}"; do
    if [[ ! -s "$root/$path" ]]; then
      printf 'docs: missing or empty required file: %s\n' "$path" >&2
      failed=1
    fi
  done
  return "$failed"
}

self_test() {
  local doc_gate_tmp
  doc_gate_tmp="$(mktemp -d)"
  trap 'rm -rf -- "$doc_gate_tmp"' RETURN
  local path
  for path in "${required_files[@]}"; do
    mkdir -p "$doc_gate_tmp/$(dirname "$path")"
    printf 'planted fixture\n' > "$doc_gate_tmp/$path"
  done
  rm "$doc_gate_tmp/SUPPORT.md"
  if check_required "$doc_gate_tmp" >/dev/null 2>&1; then
    printf 'docs self-test: FAIL — missing SUPPORT.md was accepted\n' >&2
    return 1
  fi
  printf 'docs self-test: PASS — missing SUPPORT.md was refused\n'
}

if [[ "${1:-}" == "--self-test" ]]; then
  self_test
  exit
fi

cd "$repo_root"
check_required "$repo_root"

grep -Fq 'bash scripts/check-docs.sh --self-test' .github/workflows/checks.yml || {
  printf 'docs: checks workflow does not run the planted documentation failure\n' >&2
  exit 1
}
grep -Eq '^[[:space:]]+- run: bash scripts/check-docs\.sh$' .github/workflows/checks.yml || {
  printf 'docs: checks workflow does not run the documentation gate\n' >&2
  exit 1
}
grep -Fq 'python3 docs/ux/lint.py' .github/workflows/checks.yml || {
  printf 'docs: checks workflow does not run the UX contract linter\n' >&2
  exit 1
}
grep -Eq '^  validate:$' .github/workflows/checks.yml || {
  printf 'docs: checks workflow has no aggregate validate job\n' >&2
  exit 1
}

ruby -e 'require "yaml"; ARGV.each { |path| YAML.safe_load(File.read(path), aliases: false) }' \
  CITATION.cff .github/ISSUE_TEMPLATE/config.yml \
  .github/ISSUE_TEMPLATE/objection.yml .github/ISSUE_TEMPLATE/translation.yml

python3 tools/check-version.py
printf 'docs: PASS — required homes, structured files, version, and CI wiring agree\n'
