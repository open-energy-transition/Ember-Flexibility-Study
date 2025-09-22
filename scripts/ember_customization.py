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


def apply_hourly_fuel_prices(n, carriers, fn_hourly_prices):
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
            price_col = 'LIGNITE_SPOT_PRICE_EUR_PER_MWH'
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
    
    
def include_coal_chps_for_selected_countries(n, costs, CHP_ppl_fn):
    country_code_map = {'Poland': 'PL', 'Czechia': 'CZ', 'Greece': 'GR', 'Germany': 'DE', 'Italy': 'IT', 'Netherlands': 'NL'}
    focus_full= country_code_map.keys()
    df = pd.read_csv(CHP_ppl_fn, encoding='latin-1')
    df = df.rename(columns={'lon': 'x', 'lat': 'y'})
    df = df.query("type == 'chp'")
    df = df[df['status'] == 'operating']
    df = df.query("bus in @focus_full")
    carrier_mapping = {'Hard coal': 'coal', 'Lignite': 'lignite', 'Gas':'gas'}
    
    for orig_carrier in df['carrier'].unique():
        if orig_carrier not in carrier_mapping:
            continue
        map_carrier = carrier_mapping[orig_carrier]
        sub_df = df.query('carrier == @orig_carrier').copy()
        n.add("Carrier", f"urban central {map_carrier} CHP", overwrite=True)
        sub_df['country'] = sub_df['bus'].map(country_code_map)
        sub_df = sub_df.dropna(subset=['country', 'x', 'y'])
        unique_countries = sub_df['country'].unique()
        power_buses = n.buses.query("carrier == 'AC' and country in @unique_countries")[['x', 'y', 'country']]
        power_buses = power_buses.reset_index().rename(
                  columns={
                              'Bus': 'bus_id', 
                              'x': 'bus_x',    
                              'y': 'bus_y'      
                          }
                                                       )
        if power_buses.empty:
            continue
        sub_df = sub_df.reset_index(drop=True)
        sub_df['plant_id'] = sub_df.index
        pairs = pd.merge(sub_df, power_buses, on='country')
        pairs['dx'] = pairs['x'] - pairs['bus_x']
        pairs['dy'] = pairs['y'] - pairs['bus_y']
        pairs['dist'] = (pairs['dx']**2 + pairs['dy']**2)**0.5
        min_dist_idx = pairs.groupby('plant_id')['dist'].idxmin()
        min_dist_idx = min_dist_idx.dropna()
        if min_dist_idx.empty:
            continue
        nearest_pairs = pairs.loc[min_dist_idx]
        nearest_pairs['nearest_bus'] = nearest_pairs['bus_id']
        nearest_pairs['heat_bus'] = nearest_pairs['nearest_bus'] + ' urban central heat'
        nearest_pairs = nearest_pairs.query('heat_bus in @n.buses.index')
        
        if nearest_pairs.empty:
            continue
        nearest_pairs['eff'] = nearest_pairs['efficiency'].fillna(0.45)
        nearest_pairs['heat_eff'] = nearest_pairs['heat_efficiency'].fillna(0.35)
        link_names = (nearest_pairs['nearest_bus'] + '_' + map_carrier + '_chp_' + nearest_pairs['id'].str.replace(' ', '_')).tolist()
        bus0s = [f"EU {map_carrier}"] * len(nearest_pairs)
        bus1s = nearest_pairs['nearest_bus'].tolist()
        bus2s = nearest_pairs['heat_bus'].tolist()
        bus3s = ["co2 atmosphere"] * len(nearest_pairs)
        carriers_list = [f"urban central {map_carrier} CHP"] * len(nearest_pairs)
        p_noms = (nearest_pairs['p_nom'] / nearest_pairs['eff']).tolist()
        efficiencies = nearest_pairs['eff'].tolist()
        efficiency2s = nearest_pairs['heat_eff'].tolist()
        efficiency3s = [costs.at[map_carrier, 'CO2 intensity']] * len(nearest_pairs)
        marginal_costs = [costs.at[map_carrier, 'VOM']] * len(nearest_pairs)
        capital_costs = [0] * len(nearest_pairs)
        lifetimes = [25] * len(nearest_pairs)
        p_nom_extendables = [False] * len(nearest_pairs)
        reverseds = [False] * len(nearest_pairs)
        
        if link_names:
            n.add(
                "Link",
                link_names,
                bus0=bus0s,
                bus1=bus1s,
                bus2=bus2s,
                bus3=bus3s,
                carrier=carriers_list,
                p_nom_extendable=p_nom_extendables,
                p_nom=p_noms,
                capital_cost=capital_costs,
                marginal_cost=marginal_costs,
                efficiency=efficiencies,
                efficiency2=efficiency2s,
                efficiency3=efficiency3s,
                lifetime=lifetimes,
                reversed=reverseds
            )
            logger.info(f"Added {len(link_names)} {map_carrier} CHPs")
