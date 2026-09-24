#!/bin/sh
# PROCESS.md §P1. Prints SEALED OK and exits 0, or names every problem and exits 1.
# Default: working copy + staged files + history. --ci: tracked files + full history.
cd "$(git rev-parse --show-toplevel)" || exit 1
SEALED='^(answer-key/|twin/|\.twin-cache/|run_tests\.sh$|tools/extract|tools/tests/|_scratch-insights-no-rls|_design/(PROCESS\.md|DESIGN\.md|critiques\.json|design-plan\.json|research-format\.md|REVISION-NOTES\.md|research-data\.unredacted\.md)$)'
fail=0
bad() { echo "SEALING: $1"; fail=1; }
# ls without -A: dotfiles such as Finder's .DS_Store are ignored here (and in .gitignore)
extra=$(ls _design 2>/dev/null | grep -v -E '^(SPEC|HINTS|PROCESS)\.md$|^research-(exam|mac|data)\.md$')
[ -n "$extra" ] && bad "_design/ holds more than SPEC, HINTS, PROCESS, research-(exam|mac|data): $extra"
git check-ignore -q answer-key/ANSWER-KEY.md || bad "answer-key/ is not ignored"
git check-ignore -q _design/PROCESS.md || bad "_design/PROCESS.md is not ignored"
if [ "$1" = "--ci" ]; then
  t=$(git ls-files | grep -E "$SEALED"); [ -n "$t" ] && bad "tracked: $t"
else
  for p in twin .twin-cache run_tests.sh tools/extract.py tools/tests; do
    [ -e "$p" ] && bad "engine path in working copy: $p"; done
  s=$(git diff --cached --name-only | grep -E "$SEALED"); [ -n "$s" ] && bad "staged: $s"
fi
if git rev-parse -q --verify HEAD >/dev/null; then
  h=$(git log --all --format= --name-only | grep -E "$SEALED" | sort -u)
  [ -n "$h" ] && bad "in history (rewrite before any push): $h"
fi
[ $fail -eq 0 ] && echo "SEALED OK"
exit $fail
