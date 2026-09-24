G0 SIGNED | 2026-09-22 | lead | SEALED OK
ENGINE READY | 2026-09-23 | engine commit 4945864238e3 | run_tests: 164 green | CLI self-test: pass
VENDOR | 2026-09-23 | tools/reconcile from northledger-core | pbi.py sha256 2d119cf4737eb6aff5e8eadac4085fcf3e9731e9b3b37d6e9f316747abb79ff8 | tests 30/30

<!-- G0 = PROCESS.md §P1 steps 1-4. Checked: tools/check_sealed.sh prints SEALED OK on the empty repo; red-tested in a scratch repo (engine path in working copy, force-staged PROCESS.md, stray _design file) and the pre-commit hook blocked a bad commit. The staged-first-commit check runs automatically through the pre-commit hook (git config core.hooksPath tools/hooks). The owner's EXPOSURE record goes below this line, before any build step. -->
PLAN CHANGE | 2026-09-23 | owner: AI builds v1 (answer key unsealed for the builders); card label: AI-built, owner-directed
DECISION | 2026-09-23 | Requests Daily, no Manage aggregations (SPEC §5.1, 2.3.3) | Desktop's Manage aggregations (user-defined aggregations) only redirects queries when the detail table it summarises is in DirectQuery storage mode; in v1 every table, Requests included, is import, so an aggregation mapping on Requests Daily would never be used. Requests Daily therefore stays a plain imported table: its measure Requests (Daily) is shown through C1 (equality with Requests at its grain) and the §11 query-time comparison, and no v1 visual uses it. Routing visuals through it automatically needs an aggregation-aware measure, which is v2 (SPEC §13.2).

<!-- Evidence lines still to be made in the Power BI service; each stays [unrun] until it has been run there and its screenshot or export is in docs/evidence/. -->
SPIKE 1 | [unrun] | Key Influencers (Plan A', numeric Breach Flag) before and after Time Calc (SPEC §8)
SPIKE 2 | [unrun] | Explain the increase on the RLS-free copy _scratch-insights-no-rls (SPEC §8)
SPIKE 3 | [unrun] | Decomposition tree AI (high value) splits on Requests, page 5 (SPEC §8)
PERF | [unrun] | Performance Analyzer, page 3 agency line, Open Backlog EOP vs (Fast), three runs dev and full: visual ms, DAX ms (SPEC §11)
REFRESH PROJECTION | [unrun] | projected full refresh = 25 x median dev refresh of Requests x 4 (SPEC §11)
REQUESTS DAILY SWITCH | [unrun] | keep or switch Requests Daily after the refresh projection (SPEC §11)
DUPLICATE FORK | [unrun] | reason the debug duplicate of Requests was made and deleted (SPEC §11)
CI | 2026-09-24 | first push without .github/workflows/sealing.yml: the GitHub login lacks the 'workflow' permission. To add it: gh auth refresh -h github.com -s workflow (approve in the browser), then git add .github && git commit -m 'Add the sealing CI workflow' && git push. The pre-push hook (tools/check_sealed.sh) guards every push meanwhile.
