# SPDX-FileCopyrightText: Contributors to PyPSA-Eur <https://github.com/pypsa/pypsa-eur>
#
# SPDX-License-Identifier: CC0-1.0

import numpy as np
import country_converter as coco
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
    
    
def include_chps_for_selected_countries(n, costs, CHP_ppl_fn, country_code_map, filter_chps):

    focus_full = country_code_map.keys()

    df = pd.read_csv(CHP_ppl_fn, encoding='latin-1').rename(columns={'lon': 'x', 'lat': 'y'})
    df = df.query(filter_chps)
    carrier_mapping = {
        'Hard coal': 'coal', 'Lignite': 'lignite', 'Gas':'gas',
        'hard coal': 'coal', 'lignite': 'lignite', 'gas': 'gas'
    }
    
    for orig_carrier in df['carrier'].unique():
        if orig_carrier not in carrier_mapping:
            continue
        map_carrier = carrier_mapping[orig_carrier]
        sub_df = df.query('carrier == @orig_carrier').copy()
        n.add("Carrier", f"urban central {map_carrier} CHP", overwrite=True)
        sub_df['country'] = sub_df['bus'].map(country_code_map)
        sub_df = sub_df.dropna(subset=['country', 'x', 'y'])
        if sub_df.empty:
            continue
        unique_countries = sub_df['country'].unique()
        power_buses = n.buses.query("carrier == 'AC' and country in @unique_countries")[['x', 'y', 'country']]
        power_buses = power_buses.reset_index().rename(
            columns={
                'Bus': 'bus_id',
                'name': 'bus_id',
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
        nearest_pairs['eff'] = nearest_pairs['efficiency'].fillna(0.32)
        nearest_pairs['heat_eff'] = nearest_pairs['heat_efficiency'].fillna(0.35)
        link_names = (nearest_pairs['nearest_bus'] + '_' + map_carrier + '_chp_' + nearest_pairs['id'].str.replace(' ', '_')).tolist()
        
        if link_names:
            n.add(
                "Link",
                link_names,
                bus0=[f"EU {map_carrier}"] * len(nearest_pairs),
                bus1=nearest_pairs['nearest_bus'].tolist(),
                bus2=nearest_pairs['heat_bus'].tolist(),
                bus3=["co2 atmosphere"] * len(nearest_pairs),
                carrier=[f"urban central {map_carrier} CHP"] * len(nearest_pairs),
                p_nom_extendable=[False] * len(nearest_pairs),
                p_nom=(nearest_pairs['p_nom'] / nearest_pairs['eff']).tolist(),
                capital_cost=[0] * len(nearest_pairs),
                marginal_cost=[costs.at[map_carrier, 'VOM']] * len(nearest_pairs),
                efficiency=nearest_pairs['eff'].tolist(),
                efficiency2=nearest_pairs['heat_eff'].tolist(),
                efficiency3=[costs.at[map_carrier, 'CO2 intensity']] * len(nearest_pairs),
                lifetime=[25] * len(nearest_pairs),
                reversed=[False] * len(nearest_pairs)
            )
            logger.info(f"Added {len(link_names)} {map_carrier} CHPs")

def set_line_s_nom_to_ntc(n, ntc_fn):
   
    """
    Scale interconnection capacities between country pairs to match target NTCs.
    This function reads a CSV of Net Transfer Capacities (NTC) between countries
    and then enforces the target NTC (MW) for each country pair found in both the
    CSV and the network.
    If DC Links exist between the two country bus sets:
        * Treat directions separately
        * For each direction, set the sum of all p_nom over links in that direction
          to the target NTC by uniformly scaling existing `p_nom` values.
          If current sum is zero, distribute the NTC evenly across links.
        * If DC links are found, remove any AC Lines connecting the same pair
           (to avoid double counting parallel AC when a DC representation exists).
    Else if AC Lines exist between the country bus sets (but no DC Links):
         * Uniformly scale their `s_nom` such that the sum of s_nom equals
           the target NTC. If the current sum is zero, distribute NTC evenly.
    If neither Lines nor Links exist, add new DC Links in both directions,
    each with p_nom equal to the target NTC.
    Pairs with NTC == 0 are skipped.
    Parameters
    ----------
    n : pypsa.Network
        The network to modify.
    ntc_fn : str or pathlib.Path
        Path to CSV with columns:
        - `source_country_code` (ISO3),
        - `target_country_code` (ISO3),
        - `NTC_2030_MW` (numeric, MW).
    Returns
    -------
    None
        The network `n` is modified in place.
    """
    n_clusters = len(n.buses.query("carrier == 'AC'"))
    if n_clusters > 39:
         raise ValueError("This feature doesn't work for n_clusters > 39")
    df = pd.read_csv(ntc_fn)
    cc = coco.CountryConverter()
    df['source_iso2'] = cc.convert(names=df['source_country_code'], src="ISO3", to="ISO2")
    df['target_iso2'] = cc.convert(names=df['target_country_code'], src="ISO3", to="ISO2")
    df = df.dropna(subset=['source_iso2', 'target_iso2'])
    pairs = []
    for _, row in df.iterrows():
        pair = tuple(sorted([row['source_iso2'], row['target_iso2']]))
        pairs.append(pair)
    df['pair'] = pairs
    pair_to_ntc = df.groupby('pair')['NTC_2030_MW'].mean()
    focus_countries = list(set(df['source_iso2']).union(df['target_iso2']).intersection(set(n.buses.country.unique())))
    for pair, ntc in pair_to_ntc.items():
        if ntc == 0:
            continue
        country1, country2 = pair
        if country1 not in focus_countries and country2 not in focus_countries:
            continue
        if country1 not in focus_countries or country2 not in focus_countries:
            continue
        buses1 = n.buses.query('country == @country1').index
        buses2 = n.buses.query('country == @country2').index
        lines_between = n.lines.query('(bus0 in @buses1 and bus1 in @buses2) or (bus0 in @buses2 and bus1 in @buses1)')
        links_between = n.links.query("carrier == 'DC' and ((bus0 in @buses1 and bus1 in @buses2) or (bus0 in @buses2 and bus1 in @buses1))")
        updated = False
        removed = False
        line_or_link = None
        if not links_between.empty:
            links_between['reversed'] = (links_between.bus0.isin(buses2) & links_between.bus1.isin(buses1))
            current_total_p_nom_1 = links_between.query("reversed == False")['p_nom'].sum()
            current_total_p_nom_2 = links_between.query("reversed == True")['p_nom'].sum()
            if current_total_p_nom_1 > 0:
                scale_factor = ntc / current_total_p_nom_1
                direction = links_between.query("reversed == False").index
                n.links.loc[direction, 'p_nom'] *= scale_factor
            else:
                direction = links_between.query("reversed == False").index
                n.links.loc[direction, 'p_nom'] = ntc / len(direction)
            if current_total_p_nom_2 > 0:
                scale_factor = ntc / current_total_p_nom_2
                direction = links_between.query("reversed == True").index
                n.links.loc[direction, 'p_nom'] *= scale_factor
            else:
                direction = links_between.query("reversed == True").index
                n.links.loc[direction, 'p_nom'] = ntc / len(direction)
            updated = True
            line_or_link = "Link"
        if (updated) and (not lines_between.empty):
            removed = True
            removed_lines = lines_between.index
            n.remove("Line", removed_lines)
            lines_between = n.lines.query('(bus0 in @buses1 and bus1 in @buses2) or (bus0 in @buses2 and bus1 in @buses1)')
        if (not updated) and (not lines_between.empty):
            current_total_s_nom = lines_between['s_nom'].sum()
            if current_total_s_nom > 0:
                scale_factor = ntc / current_total_s_nom
                n.lines.loc[lines_between.index, 's_nom'] *= scale_factor
            else:
                n.lines.loc[lines_between.index, 's_nom'] = ntc / len(lines_between)
            updated = True
            line_or_link = "Line"
        if not updated:
            # No existing connections: add new DC links in both directions
            if not buses1.empty and not buses2.empty:
                bus_from_1 = buses1[0]
                bus_to_1 = buses2[0]
                link_name_1 = f"Link {country1}-{country2}"
                n.add("Link", link_name_1, bus0=bus_from_1, bus1=bus_to_1, carrier="DC", p_nom=ntc)
                bus_from_2 = buses2[0]
                bus_to_2 = buses1[0]
                link_name_2 = f"Link {country2}-{country1}"
                n.add("Link", link_name_2, bus0=bus_from_2, bus1=bus_to_2, carrier="DC", p_nom=ntc)
                updated = True
                line_or_link = "Link"
                logger.info(f"Added new DC links '{link_name_1}' and '{link_name_2}' with capacity {ntc} MW each between {country1} and {country2}")
            else:
                logger.warning(f"Cannot add links between {country1} and {country2}: missing buses in one or both countries")
        if updated:
            logger.info(f"Set {line_or_link} capacity to a total of {ntc} MW for interconnections between {country1} and {country2}")
        else:
            logger.warning(f"No interconnections found or added between {country1} and {country2}")
        if removed:
            logger.info(f"Removed lines {removed_lines}, because there was already a valid link connection {links_between.index}.")


def apply_hourly_price_fix(n):
    for store in ["EU gas Store", "EU coal Store", "EU lignite Store"]:
        if store in n.stores.index:
            n.remove("Store", store)
            logger.info(
                f"Removing {store} to account for hourly prices for {store.split(" ")[1]}."
            )


def add_LV_capacities(n, ppl_path, max_hours):
    ppl = pd.read_csv(ppl_path, index_col=0, dtype={"Capacity": float, "bus": str})
    # For rooftop solar
    rooftop_df = ppl[(ppl['Fueltype'].str.strip().str.lower() == 'solar') & (ppl['Technology'].str.strip().str.lower() == 'solar-rooftop')]
    agg_capacity_rooftop = rooftop_df.groupby('bus')['Capacity'].sum()

    for bus, cap in agg_capacity_rooftop.items():
        rooftop_bus = bus + ' low voltage'
        matching_gens = n.generators[(n.generators.bus == rooftop_bus) & (n.generators.carrier == 'solar rooftop')]
        if not matching_gens.empty:
            num = len(matching_gens)
            add_cap = cap / num 
            n.generators.loc[matching_gens.index, 'p_nom'] = add_cap
            n.generators.loc[matching_gens.index, 'p_nom_min'] = add_cap
            n.generators.loc[matching_gens.index, 'p_nom_extendable'] = False
            logger.info(f"Fixed {add_cap:.2f} MW solar-rooftop generators at bus {bus} low voltage.")
        else:
            logger.warning(f"No matching solar-rooftop generators at bus {bus} low voltage.")

   # Home batteries 
    home_battery_df = ppl[(ppl['Fueltype'].str.strip().str.lower() == 'home battery')]
    agg_capacity_home = home_battery_df.groupby('bus')['Capacity'].sum()

    for bus, cap in agg_capacity_home.items():
        store_i = bus + " home battery"
        if store_i in n.stores.index:
            home_max_hours = max_hours.get("home_battery", 0)
            n.stores.loc[store_i, 'e_nom'] = cap * home_max_hours
            n.stores.loc[store_i, 'e_nom_min'] = cap * home_max_hours
            n.stores.loc[store_i, 'e_nom_extendable'] = False
        else:
            logger.warning(f"No home battery store at bus {bus}.")

        charger_i = bus + " home battery charger"
        if charger_i in n.links.index:
            n.links.loc[charger_i, 'p_nom'] = cap
            n.links.loc[charger_i, 'p_nom_min'] = cap
            n.links.loc[charger_i, 'p_nom_extendable'] = False
        else:
            logger.warning(f"No home battery charger at bus {bus}.")

        discharger_i = bus + " home battery discharger"
        if discharger_i in n.links.index:
            n.links.loc[discharger_i, 'p_nom'] = cap
            n.links.loc[discharger_i, 'p_nom_min'] = cap
            n.links.loc[discharger_i, 'p_nom_extendable'] = False
        else:
            logger.warning(f"No home battery discharger at bus {bus}.")

        logger.info(f"Fixed home battery at bus {bus} with p_nom {cap:.2f} MW, e_nom {cap * home_max_hours:.2f} MWh.")

    return n


def apply_BEV_dsm_restiction_country_shares(dsm_profile, country_shares):

    """
    Scale BEV DSM restriction values by country-specific shares

    Parameters
    ----------
    dsm_profile : pd.DataFrame
        DSM profile with country-coded columns.

    country_shares : str
        Path to CSV with country share values.

    Returns
    -------
    pd.DataFrame
        DSM profile with columns scaled by the corresponding shares.
    """

    country_shares = pd.read_csv(country_shares, index_col=0)
    explicit_countries = [c for c in country_shares.index if c != 'default']
    for col in dsm_profile.columns:
        country_code = col[:2]
        if country_code in explicit_countries:
            dsm_profile[col] = dsm_profile[col] * country_shares.loc[country_code].values[0]
        elif 'default' in country_shares.index:
            dsm_profile[col] = dsm_profile[col] * country_shares.loc['default'].values[0]
        else:
            logger.warning(
                f"No 'default' share found for the BEV DSM restriction in '{country_code}'. "
                f"Leaving it at 1, which implies that all EVs will be fully charged "
                f"by the specified 'bev_dsm_restriction_time'."
            )

    return dsm_profile


def apply_highflex_capacities(n, n_highflex, scenario_capacities):

    if scenario_capacities.get("resistive_heaters", False):
        rh_capacities = n_highflex.links[n_highflex.links.carrier.str.contains("resistive heater")].p_nom_opt
        n.links.loc[rh_capacities.index, "p_nom"] = rh_capacities
        n.links.loc[rh_capacities.index, "p_nom_min"] = rh_capacities
        n.links.loc[rh_capacities.index, "p_nom_extendable"] = False
        logger.info(
            "Applying resistive heater capacities from high flex scenario run."
        )

    if scenario_capacities.get("water_tanks", False):
        tank_capacities = n_highflex.stores[n_highflex.stores.carrier.str.contains("water")].e_nom_opt
        n.stores.loc[tank_capacities.index, "e_nom"] = tank_capacities
        n.stores.loc[tank_capacities.index, "e_nom_min"] = tank_capacities
        n.stores.loc[tank_capacities.index, "e_nom_extendable"] = False
        logger.info(
            "Applying water tank and water pit capacities from high flex scenario run."
        )
