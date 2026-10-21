# ThermoAudit

**Transparent checks for exported energy-process data.**

Repository: https://github.com/5dzph/thermoaudit · Maintainer: [5dzph](https://github.com/5dzph)

[中文说明](README.zh-CN.md) · [Data contract & equations](docs/data-contract.md) · [Contributing](CONTRIBUTING.md)

ThermoAudit helps researchers catch balance, sign and temperature-direction errors before interpreting simulation results. It is a small Python library and command-line tool with **no runtime dependencies**, deterministic JSON output, and offline HTML reports.

**Status:** initial 0.1.0 release candidate. Included data are synthetic, hand-constructed teaching fixtures. No real plant validation, adoption, performance improvements or program endorsement are claimed. Package-index name availability has not been checked.

## What works

- Strict explicit-unit JSON input with unknown-field, duplicate-ID and connectivity checks.
- Per-unit steady-state mass and energy balances with configurable tolerances.
- Two-stream counterflow HX side-flow conservation, passive temperature/enthalpy direction and terminal approach checks.
- Specific energy from supplied net power and boundary product flow.
- CSV candidate screening: minimize SEC/CAPEX and maximize exergy efficiency; exclude infeasible points, retain the exact Pareto set, and select a transparent weighted compromise.
- Self-contained HTML/JSON reports with an input SHA-256 fingerprint; no account, network request or API key.
- Regression tests, CI configuration, issue templates and an MIT license.

## Try it in one minute

Requires Python 3.10 or newer. Extract or clone the source and open a terminal **inside the folder containing this README**:

```bash
python -m thermoaudit audit examples/balanced_hx.json --out reports
python -m thermoaudit pareto examples/candidates.csv --out reports
python -m unittest discover -s tests -v
```

Use `python3` instead of `python` where appropriate. No pip installation is needed for these commands. On Windows, double-click **run_demo.bat**, or run `py -3 run_demo.py`. Open `reports/audit.html` and `reports/pareto.html` in your browser. Static summaries in `demo_reports/` can be opened without Python; running the commands produces the full reports.

The balanced fixture has 320 kW incoming and outgoing enthalpy flow, a 40 K minimum terminal approach, and a supplied-power SEC of 0.5 kWh/kg. These are arithmetic checks, **not hydrogen liquefaction performance**.

To see an intentional failure:

```bash
python -m thermoaudit audit examples/broken_hx.json --out reports/broken
```

Exit codes: `0` = listed checks pass / candidate screening completes; `1` = valid audit input with failed checks; `2` = invalid input, unsupported data or I/O error. Reports are generated for exit code 1. Existing reports with the same name are replaced; use separate output directories to retain runs.

## Python API

```python
import json
from pathlib import Path
from thermoaudit import audit, analyze_candidates
from thermoaudit.pareto import read_candidates

case = json.loads(Path("examples/balanced_hx.json").read_text())
result = audit(case)
tradeoffs = analyze_candidates(read_candidates("examples/candidates.csv"), weights=(2, 1, 1))
print(result["status"], tradeoffs["recommendation_id"])
```

Optional installation from source: `python -m pip install .`. This may download the setuptools build dependency. Then the `thermoaudit` console command is available. Do not assume a package named `thermoaudit` on PyPI is this project.

## Boundaries that matter

ThermoAudit checks supplied numbers; it does not calculate fluid properties, converge a cycle, automate Aspen/HYSYS, run a genetic algorithm, estimate CAPEX, or compute exergy efficiency. HX endpoint checks do not prove that an internal pinch is absent. Variable heat capacity, phase transitions, finite UA, ortho-para hydrogen conversion, reactions and pressure drops need a separate model. A PASS is limited to the listed checks.

The Pareto tool ranks existing candidate points only. `feasible=true` must come from your own validated constraints. All costs need the same currency year, boundary and scope; efficiencies need the same exergy definition and system boundary. Constant objective columns contribute zero to compromise distance. Duplicate objective vectors remain Pareto-equivalent. No continuous frontier interpolation is claimed.

## Development

```bash
python -m unittest discover -s tests -v
python run_demo.py --no-open
```

CI targets Python 3.10/3.12/3.13 on Linux and Windows. See [docs/verification.md](docs/verification.md) and the repository's Actions page for observed results.

Read [CONTRIBUTING.md](CONTRIBUTING.md), [ROADMAP.md](ROADMAP.md), [SECURITY.md](SECURITY.md), and [AGENTS.md](AGENTS.md). Contributions should include a reproducible example and independently checkable expected values.

## License

MIT, see [LICENSE](LICENSE). Code was prepared with AI assistance. Maintainers are responsible for reviewing changes, validating domain assumptions and reporting limitations honestly.
