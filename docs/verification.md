# Verification record

Date: 2026-10-21.

## Original local source delivery

The initial local project was tested on Linux, Python 3.12.14:
- 34 regression tests passed.
- Both examples generated reports.
- The package wheel was built, installed without dependencies into a separate directory, and successfully ran the balanced audit.

## Repository recovery and verification

The local execution environment subsequently disconnected. The source and tests were recovered from the creation conversation and published through the GitHub connector. This repository is not claimed to be byte-identical to the earlier ZIP. Documentation was updated with the real repository and maintainer; static demo summaries explicitly describe expected results rather than claiming a new local run.

Current-version verification is provided by [GitHub Actions](https://github.com/5dzph/thermoaudit/actions). The workflow runs the full test suite and both examples on Linux and Windows with Python 3.10, 3.12 and 3.13. Workflow configuration alone does not establish a passing result; check the run associated with the commit you use.

Tests cover hand calculations, compressor/turbine work signs, temperature crossing, compensating HX side-flow errors, negative enthalpy references, tolerance boundaries, invalid inputs, Pareto dominance/direction/ties/weights, HTML escaping, input-overwrite protection and CLI exit codes.

## Independent fixture expectations

- Balanced HX: 320 kW incoming and outgoing enthalpy flow, zero mass and energy residual, 40 K terminal approach, supplied-power SEC 0.5 kWh/kg.
- Broken HX: failed mass/energy/direction checks; CLI exit 1.
- Candidate CSV: A/B/C/F are Pareto candidates; D is dominated; E is explicitly infeasible. Equal-weight compromise is F.
- Invalid or missing input: CLI exit 2.

## Not established by these tests

- Windows desktop browser launch through the batch file.
- Real engineering dataset validity, simulator interoperability or industrial suitability.
- Thermophysical property consistency, full internal pinch or finite-UA feasibility.
- Full visual inspection in every browser.

All included examples are synthetic. They are software demonstrations, not plant-performance evidence.
