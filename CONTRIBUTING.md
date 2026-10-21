# Contributing

Thank you for helping make process-data checks easier to verify.

1. Open an issue describing the problem, a minimal anonymized input and expected behavior. Small fixes can come directly as pull requests.
2. Make a focused change with a regression test. For numerical methods, include an independently hand-calculated case or a citable reference with lawful data access.
3. Run `python -m unittest discover -s tests -v` and `python run_demo.py --no-open`.
4. Explain assumptions, units, boundaries, tolerances and backward-compatibility changes in the PR.

Keep the runtime standard-library-only unless a new dependency has a clear benefit and maintainer agreement. Optional property solvers should stay separate from the audit core. Do not round intermediate calculations just to make tests pass. Do not weaken tolerances to hide a balance error.

For data contributions, state source, license, unit conventions, composition basis, validation procedure and whether values are measured, simulated or synthetic. Never submit confidential exports, credentials or someone else's proprietary case. AI-assisted contributions are welcome when reviewed; document assistance and do not invent benchmark results.

Maintainer: [5dzph](https://github.com/5dzph). Maintainers review correctness and scope before merging. There is no promised review SLA. Use repository issues for non-sensitive coordination. Be respectful, critique work rather than people, and avoid harassment or unwanted promotion.

First contribution suggestions are in ROADMAP.md. They describe unimplemented work, not completed features.
