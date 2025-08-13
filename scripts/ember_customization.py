
import numpy as np
import xarray as xr
import pandas as pd

def apply_custom_ramping(n):

    rampings = pd.read_csv("validation/ember_data/ramping.csv", index_col=0)

    for tech in rampings.columns:
        idx = n.links.query("carrier == @tech").index
        n.links.loc[idx, "committable"] = True
        for param in rampings.index:
            param_value = float(rampings[tech].loc[param])
            if param in [
                "min_up_time", "min_down_time",
                "ramp_limit_up", "ramp_limit_down",
                "ramp_limit_start_up", "ramp_limit_shut_down"
            ]:
                param_value /= n.snapshot_weightings.generators.mean()
                param_value = int(np.ceil(param_value))
            n.links.loc[idx, param] = param_value


def apply_custom_pf_constraint(n,
                               link_name="AL -> GR NTC 2025",
                               E_min=153 * 0.95, # MWh; use 153e3 if you meant 153 GWh
                               E_max=153 * 1.05, # MWh
                               bidirectional=False,
                               debug=False):
    m = n.model
    w = n.snapshot_weightings["objective"]  # hours per snapshot

    # 1) pick link flow variable
    if "Link-p0" in m.variables:
        v = m.variables["Link-p0"]
        var_name = "Link-p0"
    elif "Link-p" in m.variables:
        v = m.variables["Link-p"]
        var_name = "Link-p"
    else:
        raise RuntimeError("No link power variable ('Link-p0' or 'Link-p') found.")

    # 2) coord/dim name
    if "link" in v.dims:
        dim = "link"
    elif "Link" in v.dims:
        dim = "Link"
    else:
        raise RuntimeError(f"Unexpected dims for {var_name}: {v.dims}")

    if debug:
        print(f"using var={var_name}, dims={v.dims}, dim='{dim}'")
        for c in v.coords:
            vals = list(v.coords[c].values)
            print(f"coord {c} (len={len(vals)}):", vals[:3], "...")

    # 3) make sure the label actually exists
    if link_name not in n.links.index:
        # helpful hint: show a few labels the model actually uses
        some = list(n.links.index[:5])
        raise KeyError(f"Link '{link_name}' not found in n.links.index. "
                       f"Examples: {some}")

    # 4) select ONE link as a 1-D vector over 'snapshot'
    #    IMPORTANT: use coords[...] not v[dim]; the latter indexes the variable
    labels = v.coords[dim].values  # <-- THIS LINE FIXES YOUR ERROR
    idx_arr = np.where(labels == link_name)[0]
    if len(idx_arr) == 0:
        few = list(labels[:5])
        raise KeyError(f"Link '{link_name}' not found in variable coord '{dim}'. "
                       f"First few labels: {few}")
    p_sel = v.isel({dim: int(idx_arr[0])})   # dims now ('snapshot',)

    # 5) align weights as 1-D DataArray on 'snapshot'
    w_da = xr.DataArray(w.values, coords={"snapshot": n.snapshots}, dims=("snapshot",))

    # 6) build the annual energy (MWh)
    if bidirectional:
        p_pos = m.add_variables(coords={"snapshot": n.snapshots},
                                name=f"{link_name}_AtoB_pos", lb=0)
        m.add_constraints(p_pos - p_sel >= 0, name=f"{link_name}_AtoB_pos_ge_flow")
        energy = (p_pos * w_da).sum(dim="snapshot")
    else:
        energy = (p_sel * w_da).sum(dim="snapshot")

    # 7) enforce band/cap
    m.add_constraints(energy >= E_min, name=f"{link_name}_annual_min")
    m.add_constraints(energy <= E_max, name=f"{link_name}_annual_max")
