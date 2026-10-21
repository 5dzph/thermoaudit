"""Steady-state boundary checks. No fluid-property solver is embedded."""

from .validation import (
    ValidationError, array, finite_result, number, obj, positive, text,
)

DEFAULTS = {"mass_atol_kg_s": 1e-6, "energy_atol_kw": 0.01, "rtol": 0.001}


def audit(case):
    """Validate a case and return JSON-serializable, deterministic findings.

    Convention: Q positive into the unit; W positive out of the unit.
    A PASS applies only to the listed checks, never to overall feasibility.
    """
    obj(case, "case", ["schema_version", "name", "provenance", "streams", "units"],
        ["tolerances", "performance"])
    if type(case["schema_version"]) is not int or case["schema_version"] != 1:
        raise ValidationError("schema_version: only integer 1 is supported")
    name = text(case["name"], "name")
    provenance = text(case["provenance"], "provenance")
    tolerance = dict(DEFAULTS)
    if "tolerances" in case:
        obj(case["tolerances"], "tolerances", [], DEFAULTS)
        for key, val in case["tolerances"].items():
            tolerance[key] = number(val, f"tolerances.{key}", minimum=0)
    streams = {}
    for i, raw in enumerate(array(case["streams"], "streams")):
        path = f"streams[{i}]"
        obj(raw, path, ["id", "mass_kg_s", "temperature_k", "enthalpy_kj_kg"])
        sid = text(raw["id"], f"{path}.id")
        if sid in streams:
            raise ValidationError(f"{path}: duplicate stream id {sid}")
        streams[sid] = {
            "mass_kg_s": number(raw["mass_kg_s"], f"{path}.mass_kg_s", minimum=0),
            "temperature_k": positive(raw["temperature_k"], f"{path}.temperature_k"),
            "enthalpy_kj_kg": number(raw["enthalpy_kj_kg"], f"{path}.enthalpy_kj_kg"),
        }

    checks = []

    def residual_check(uid, code, residual, scale, absolute, unit):
        finite_result(residual, f"{uid}.{code}")
        limit = finite_result(absolute + tolerance["rtol"] * scale, f"{uid}.tolerance")
        checks.append({"unit": uid, "code": code,
                       "status": "PASS" if abs(residual) <= limit else "FAIL",
                       "value": residual, "limit": limit, "quantity_unit": unit,
                       "message": "Absolute residual must not exceed limit."})

    seen_units = set()
    producers, consumers = {}, {}
    for i, raw in enumerate(array(case["units"], "units")):
        path = f"units[{i}]"
        obj(raw, path, ["id", "kind", "inlets", "outlets", "heat_kw", "shaft_work_out_kw"],
            ["hot_in", "hot_out", "cold_in", "cold_out", "min_approach_k"])
        uid = text(raw["id"], f"{path}.id")
        if uid in seen_units:
            raise ValidationError(f"{path}: duplicate unit id {uid}")
        seen_units.add(uid)
        if raw["kind"] not in ("boundary", "counterflow_hx"):
            raise ValidationError(f"{path}.kind: use boundary or counterflow_hx")
        for side, registry in (("inlets", consumers), ("outlets", producers)):
            ids = array(raw[side], f"{path}.{side}")
            for sid in ids:
                text(sid, f"{path}.{side}")
                if sid not in streams:
                    raise ValidationError(f"{path}.{side}: unknown stream {sid}")
                if sid in registry:
                    raise ValidationError(f"{path}.{side}: stream {sid} reused on same side; use a splitter/mixer")
                registry[sid] = uid
        if set(raw["inlets"]) & set(raw["outlets"]):
            raise ValidationError(f"{path}: inlet/outlet ids must be distinct")
        ins, outs = [streams[s] for s in raw["inlets"]], [streams[s] for s in raw["outlets"]]
        mi, mo = sum(s["mass_kg_s"] for s in ins), sum(s["mass_kg_s"] for s in outs)
        ei = sum(s["mass_kg_s"] * s["enthalpy_kj_kg"] for s in ins)
        eo = sum(s["mass_kg_s"] * s["enthalpy_kj_kg"] for s in outs)
        heat = number(raw["heat_kw"], f"{path}.heat_kw")
        work = number(raw["shaft_work_out_kw"], f"{path}.shaft_work_out_kw")
        residual_check(uid, "mass_balance", mi - mo, max(mi, mo),
                       tolerance["mass_atol_kg_s"], "kg/s")
        residual_check(uid, "energy_balance", ei + heat - work - eo,
                       max(abs(ei), abs(eo), abs(heat), abs(work)),
                       tolerance["energy_atol_kw"], "kW")
        hx_fields = {"hot_in", "hot_out", "cold_in", "cold_out", "min_approach_k"}
        if raw["kind"] == "boundary":
            if hx_fields & raw.keys():
                raise ValidationError(f"{path}: HX fields require kind=counterflow_hx")
            continue
        if not hx_fields <= raw.keys():
            raise ValidationError(f"{path}: counterflow_hx needs {sorted(hx_fields)}")
        for key in ("hot_in", "hot_out", "cold_in", "cold_out"):
            text(raw[key], f"{path}.{key}")
        if (len(raw["inlets"]) != 2 or len(raw["outlets"]) != 2
                or set(raw["inlets"]) != {raw["hot_in"], raw["cold_in"]}
                or set(raw["outlets"]) != {raw["hot_out"], raw["cold_out"]}):
            raise ValidationError(f"{path}: HX side mapping must exactly match two inlets/two outlets")
        hi, ho, ci, co = (streams[raw[k]] for k in ("hot_in", "hot_out", "cold_in", "cold_out"))
        for label, inlet, outlet in (("hot", hi, ho), ("cold", ci, co)):
            residual_check(uid, f"{label}_side_mass_balance", inlet["mass_kg_s"] - outlet["mass_kg_s"],
                           max(inlet["mass_kg_s"], outlet["mass_kg_s"]), tolerance["mass_atol_kg_s"], "kg/s")
        if any(s["mass_kg_s"] == 0 for s in (hi, ho, ci, co)):
            raise ValidationError(f"{path}: active HX requires positive flow on both sides")
        approach = number(raw["min_approach_k"], f"{path}.min_approach_k", minimum=0)
        d1 = hi["temperature_k"] - co["temperature_k"]
        d2 = ho["temperature_k"] - ci["temperature_k"]
        checks.append({"unit": uid, "code": "terminal_approach", "value": min(d1, d2),
                       "limit": approach, "quantity_unit": "K",
                       "status": "PASS" if min(d1, d2) >= approach else "FAIL",
                       "message": "Minimum of TWO terminal differences only; internal pinch is unchecked."})
        direction_ok = (hi["temperature_k"] >= ho["temperature_k"]
                        and co["temperature_k"] >= ci["temperature_k"]
                        and hi["enthalpy_kj_kg"] >= ho["enthalpy_kj_kg"]
                        and co["enthalpy_kj_kg"] >= ci["enthalpy_kj_kg"])
        checks.append({"unit": uid, "code": "passive_hx_direction", "value": None,
                       "limit": None, "quantity_unit": "",
                       "status": "PASS" if direction_ok else "FAIL",
                       "message": "Assumes passive non-reacting HX: hot T/h non-increasing; cold T/h non-decreasing."})
    unused = set(streams) - producers.keys() - consumers.keys()
    if unused:
        raise ValidationError(f"streams: unused streams {sorted(unused)}")
    metrics = {}
    if "performance" in case:
        perf = obj(case["performance"], "performance", ["net_power_kw", "product_stream"])
        power = number(perf["net_power_kw"], "performance.net_power_kw", minimum=0)
        sid = text(perf["product_stream"], "performance.product_stream")
        if sid not in producers or sid in consumers:
            raise ValidationError("performance.product_stream: must be a boundary outlet")
        mass = positive(streams[sid]["mass_kg_s"], "product.mass_kg_s")
        metrics["specific_energy_kwh_kg"] = finite_result(power / mass / 3600, "SEC")
        metrics["net_power_kw"] = power
        metrics["product_kg_h"] = finite_result(mass * 3600, "product_kg_h")
    return {"schema_version": 1, "name": name, "provenance": provenance,
            "status": "FAIL" if any(c["status"] == "FAIL" for c in checks) else "PASS",
            "checks": checks, "metrics": metrics, "tolerances": tolerance,
            "limitations": [
                "Checks exported steady-state data; does not solve a process or certify convergence.",
                "Kinetic/potential energy and accumulation are omitted. Use one consistent enthalpy basis.",
                "HX endpoints do not establish internal pinch, finite-UA feasibility or phase behavior.",
                "No ortho-para conversion, reaction, pressure-drop or property-consistency model is provided.",
                "SEC uses user-supplied total net power; power coverage is not independently verified.",
                "PASS means listed checks passed; it is not a claim of physical feasibility.",
            ]}
