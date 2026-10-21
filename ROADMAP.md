# Roadmap

These are planned contributions, not implemented features or promised dates.

## Before the first tagged release

- Confirm maintainer contact and support expectations (owner: 5dzph).
- Review the Linux/Windows CI matrix; test the batch launcher on an actual Windows desktop.
- Ask one energy-process researcher to independently review sign conventions and examples.
- Enable private vulnerability reporting and verify the project name before package-index publication.

## Suitable first issues

1. **Chinese report labels** — add an explicit locale option without changing computed results; preserve HTML escaping and cover both languages.
2. **CSV conversion helper** — map user-selected stream-table columns with explicit conversions for kg/h and Celsius; reject missing units rather than infer them.
3. **Boundary fixture collection** — add hand-derived splitter, mixer and heater examples with source/license metadata and independently calculated residuals.
4. **Normalization diagnostics** — show raw objective ranges and constant-column warnings in Pareto reports; add a case where recommendations change with weights.

## Later, after validation

- A separate optional property-backend adapter with a well-defined enthalpy reference.
- Temperature-versus-duty profile checks with sampled/interpolated/internal-pinch limitations clearly separated.
- Auditable external simulator export adapters; no redistribution of proprietary simulator files.
- Optional result readers for externally run optimizers, including MATLAB workflows.

Prioritize reproducible user problems over adding integrations solely to increase feature count.
