# Data contract and calculation methods

## Scope

Steady-state open-system bookkeeping, excluding kinetic/potential energy and accumulation. Input enthalpies must use a consistent reference and compatible composition convention. The software cannot infer units or validate thermophysical properties. It checks each declared unit, not a derived global boundary. Separate streams are required across equipment, including recycle connections. A stream may have at most one producer and one consumer; use explicit splitter/mixer boundaries for branches.

## JSON schema version 1

Unknown keys are rejected. Top-level required fields: `schema_version` (integer 1), `name` (nonempty string), `provenance` (nonempty description of data source), `streams` (nonempty array), `units` (nonempty array). Optional: `tolerances`, `performance`. All numeric inputs must be finite JSON numbers; booleans are not numbers. Unused streams and duplicate identifiers are rejected.

| Stream field | Type / unit | Constraint |
| --- | --- | --- |
| id | string | unique, nonempty |
| mass_kg_s | number, kg/s | nonnegative; active HX sides must be positive |
| temperature_k | number, K | positive |
| enthalpy_kj_kg | number, kJ/kg | finite, may be negative |

| Unit field | Meaning |
| --- | --- |
| id | unique string |
| kind | `boundary` or `counterflow_hx` |
| inlets / outlets | nonempty arrays of existing stream IDs, no repetition |
| heat_kw | heat INTO the unit positive, cooling negative |
| shaft_work_out_kw | shaft work OUT positive, compressor input negative |
| hot_in / hot_out / cold_in / cold_out | required only for HX; exactly match two inlets/two outlets |
| min_approach_k | required only for HX, nonnegative terminal approach threshold |

`boundary` is a bookkeeping control volume (compressor, turbine, heater, mixer, splitter, etc.); it makes no type-specific constitutive checks. `counterflow_hx` additionally assumes passive, nonreacting heat exchange for direction checks. For conversion reactors or devices where that assumption is inappropriate, use a boundary and separately validate its physics.

Optional performance object has exactly `net_power_kw` (nonnegative total net input power) and `product_stream` (a produced stream with no downstream consumer and positive mass flow). This value is independently supplied; it is **not** automatically summed from unit shaft work. Declare auxiliaries, expander recovery and your system boundary externally.

## Residuals and tolerances

Mass: `r_m = sum(m_in) - sum(m_out)` in kg/s.

Energy: `r_E = sum(m_in*h_in) + Q_in - W_out - sum(m_out*h_out)` in kW.

PASS if `abs(residual) <= absolute_tolerance + rtol * scale`.

Mass scale is `max(sum(m_in), sum(m_out))`. Energy scale is `max(abs(sum(m_in*h_in)), abs(sum(m_out*h_out)), abs(Q), abs(W))`. HX side-flow checks use that side's inlet/outlet maximum.

Defaults: `mass_atol_kg_s=1e-6`, `energy_atol_kw=0.01`, `rtol=0.001`. The optional `tolerances` object can override any of these with nonnegative finite numbers. These are software defaults, not universal engineering acceptance criteria. Select tolerances for export precision and your application. The relative energy tolerance depends on enthalpy reference, and a mass imbalance can also affect the energy residual; inspect absolute residuals and mass checks together.

Counterflow terminal differences: `dT1 = T_hot,in - T_cold,out`, `dT2 = T_hot,out - T_cold,in`; require `min(dT1,dT2) >= min_approach_k`. The two endpoint values do not bound the internal approach for variable-property or phase-changing fluids. Direction requires hot-side T and h not to increase, and cold-side T and h not to decrease. No temperature tolerance is applied in this first release.

SEC: `SEC [kWh/kg] = P_net [kW] / m_product [kg/s] / 3600`.

Hand check: 3600 kW / 2 kg/s / 3600 = 0.5 kWh/kg. The demonstration's 3600 kW is an arbitrary supplied whole-system value; the example HX alone does not establish this plant power.

## Pareto CSV

Exact headers: `id,sec_kwh_kg,exergy_efficiency,capex_usd,feasible` (column order may differ). IDs must be unique; SEC/CAPEX nonnegative; efficiency in [0,1]; feasible `true` or `false` (case-insensitive). UTF-8 with or without BOM is supported. File limit: 10 MiB at the CLI; candidate limit: 2000 for the O(n²) reference implementation. Direct Python calls accept the same data as a list of dictionaries, with actual boolean feasibility values.

Transform to minimization vectors `f=(SEC, -efficiency, CAPEX)`. Candidate b dominates a if b is no worse on every objective and strictly better on at least one. Exact floating-point comparisons are used, with no epsilon dominance. Objective ties are retained; duplicate IDs are rejected. Infeasible points never set the front or normalization ranges.

For each objective, `z=(f-min(f))/(max(f)-min(f))`, over all feasible supplied candidates. A constant column has z=0. Normalize the three strictly positive weights to sum to 1. For each Pareto point compute `distance=sqrt(sum(weight*z²))`; choose minimum distance, breaking exact ties by lexicographic ID. This selection is a preference-dependent candidate, not a global optimum or intrinsic knee. Dominated points can change normalization ranges; compare runs only with the same data set and weights.

## Reports

`audit.json` includes checks, values, tolerances, limitations and optional SEC metrics. `pareto.json` includes all candidates, exclusions, front membership, weights and compromise scores. The CLI adds package version and a SHA-256 fingerprint of original input bytes. The library API does not add file provenance automatically. HTML escapes text labels and has no executable JavaScript or external resources. CLI output directories may be overwritten on rerun.
