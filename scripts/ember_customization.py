# SPDX-FileCopyrightText: Contributors to PyPSA-Eur <https://github.com/pypsa/pypsa-eur>
#
# SPDX-License-Identifier: CC0-1.0

import numpy as np
import xarray as xr
import pandas as pd
import pandas as pd
import logging

logger = logging.getLogger(__name__)


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


def apply_2023_nuclear_decommissioning(n, year=2023):
    if year == 2023:
        nuclear_info = {
            "Isar 2": {"coords": [12.29315, 48.60560556], "country": 'DE', "dateout": "2023-04-15"},
            "Emsland": {"coords": [7.317858333, 52.47423056], "country": 'DE', "dateout": "2023-04-15"},
            "Neckarwestheim 2": {"coords": [9.175, 49.04111111], "country": 'DE', "dateout": "2023-04-15"},
        }

    seen_plants = []
    for plant, info in nuclear_info.items():
        # network details
        country = nuclear_info[plant]["country"]
        country_buses = n.buses.query("country in @country").index
        network_coords = (
            n.buses.loc[n.links.query("carrier == 'nuclear' and bus1 in @country_buses").bus1, ["x", "y"]]
            .set_index(n.links.query("carrier == 'nuclear' and bus1 in @country_buses").index)
        )
        network_coords = network_coords.drop(index=seen_plants)

        # plant details
        dateout = pd.Timestamp(info["dateout"])
        px, py = info["coords"]
        dx = network_coords["x"].to_numpy() - px
        dy = network_coords["y"].to_numpy() - py

        # closest country nuclear plant
        dist = np.sqrt(dx**2 + dy**2)
        nearest_gen = network_coords.index[np.argmin(dist)]

        # decommission
        n.links_t.p_max_pu[nearest_gen] = (
            n.links.loc[nearest_gen].p_max_pu * ((n.snapshots < dateout).astype(int))
        )

        seen_plants.append(nearest_gen)


def apply_hourly_gas_prices(n, carriers, fn_hourly_prices):
    df = pd.read_csv(fn_hourly_prices)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
       
    if not df.index.equals(n.snapshots):
        logger.warning("Snapshot indices do not match exactly. Overwriting prices index with network snapshots.")
        df.index = n.snapshots
    
    if 'marginal_cost' not in n.generators_t:
        n.generators_t['marginal_cost'] = pd.DataFrame(index=n.snapshots, columns=[])
    
    for carrier in carriers:
        idx = n.generators.index[n.generators.carrier == carrier]
        if len(idx) == 0:
            continue
        if carrier == 'gas':
            price_col = 'GAS_SPOT_PRICE_EUR_PER_MWH'
        elif carrier == 'coal':
            price_col = 'COAL_SPOT_PRICE_EUR_PER_MWH'
        else:
            price_col = 'LIGNITE_PRICE_EUR_PER_MWH'
        prices = df[price_col]
        
        mc_t_array = prices.to_numpy()[:, np.newaxis]
        mc_t_df = pd.DataFrame(mc_t_array, index=prices.index, columns=idx)
        n.generators_t['marginal_cost'][idx] = mc_t_df


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
