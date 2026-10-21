"""Pareto filtering of supplied results, not an optimizer or surrogate model."""

import csv
import math
from pathlib import Path

from .validation import ValidationError, array, finite_result, number, obj, positive, text

METRICS = ("sec_kwh_kg", "exergy_efficiency", "capex_usd")


def read_candidates(path):
    """Read explicit-units CSV; reject missing/duplicate/unknown columns."""
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        required = {"id", *METRICS, "feasible"}
        if len(fields) != len(required) or set(fields) != required:
            raise ValidationError(f"CSV headers must be exactly {sorted(required)}")
        rows = []
        for line, row in enumerate(reader, 2):
            if None in row or any(v is None for v in row.values()):
                raise ValidationError(f"CSV line {line}: wrong number of fields")
            if row["feasible"].strip().lower() not in ("true", "false"):
                raise ValidationError(f"CSV line {line}: feasible must be true or false")
            parsed = {"id": row["id"], "feasible": row["feasible"].strip().lower() == "true"}
            for key in METRICS:
                try:
                    parsed[key] = float(row[key])
                except ValueError:
                    raise ValidationError(f"CSV line {line}: invalid {key}") from None
            rows.append(parsed)
    return rows


def analyze_candidates(rows, weights=(1, 1, 1)):
    """Minimize SEC/CAPEX, maximize efficiency; keep objective duplicates.

    Recommendation minimizes sqrt(sum(w_j*z_j**2)) on the Pareto front.
    Normalize using feasible-candidate ranges; constant columns contribute 0.
    Feasibility is supplied by the caller, never inferred from objectives.
    """
    array(rows, "candidates")
    if len(rows) > 2000:
        raise ValidationError("candidates: maximum 2000 rows for this quadratic reference implementation")
    if not isinstance(weights, (list, tuple)) or len(weights) != 3:
        raise ValidationError("weights: exactly three positive numbers required")
    weights = [positive(v, f"weights[{i}]") for i, v in enumerate(weights)]
    scale = max(weights)
    weights = [v / scale for v in weights]
    total = sum(weights)
    weights = [v / total for v in weights]
    if any(w == 0 for w in weights):
        raise ValidationError("weights: dynamic range is too large")
    validated, seen = [], set()
    for i, row in enumerate(rows):
        obj(row, f"candidates[{i}]", ["id", *METRICS, "feasible"])
        sid = text(row["id"], f"candidates[{i}].id")
        if sid in seen:
            raise ValidationError(f"duplicate candidate id: {sid}")
        seen.add(sid)
        if type(row["feasible"]) is not bool:
            raise ValidationError(f"{sid}.feasible: expected boolean")
        validated.append({"id": sid, "feasible": row["feasible"],
                          "sec_kwh_kg": number(row["sec_kwh_kg"], f"{sid}.sec_kwh_kg", minimum=0),
                          "exergy_efficiency": number(row["exergy_efficiency"], f"{sid}.exergy_efficiency", 0, 1),
                          "capex_usd": number(row["capex_usd"], f"{sid}.capex_usd", minimum=0)})
    feasible = [r for r in validated if r["feasible"]]
    if not feasible:
        raise ValidationError("no feasible candidates; no recommendation can be made")
    vectors = [(r["sec_kwh_kg"], -r["exergy_efficiency"], r["capex_usd"]) for r in feasible]
    front = [i for i, a in enumerate(vectors) if not any(
        all(x <= y for x, y in zip(b, a)) and any(x < y for x, y in zip(b, a))
        for j, b in enumerate(vectors) if i != j)]
    lo = [min(v[j] for v in vectors) for j in range(3)]
    span = [finite_result(max(v[j] for v in vectors) - lo[j], "normalization") for j in range(3)]
    scores = {feasible[i]["id"]: math.sqrt(sum(
        weights[j] * (((vectors[i][j] - lo[j]) / span[j]) if span[j] else 0) ** 2
        for j in range(3))) for i in front}
    recommendation = min(scores, key=lambda sid: (scores[sid], sid))
    return {"schema_version": 1, "candidate_count": len(rows), "feasible_count": len(feasible),
            "excluded_ids": [r["id"] for r in validated if not r["feasible"]],
            "pareto_ids": [feasible[i]["id"] for i in front], "recommendation_id": recommendation,
            "weights": dict(zip(METRICS, weights)), "scores": scores, "candidates": validated,
            "method": "Exact dominance; feasible-set min-max normalization; weighted Euclidean distance to ideal.",
            "limitations": ["Candidate screening only; no new operating points or global optimum are generated.",
                            "Feasibility and objective values are supplied, not independently simulated.",
                            "Recommendation depends on weights and the supplied candidate set; it is not a unique physical optimum."]}
