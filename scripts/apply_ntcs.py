import pandas as pd

def apply_ntc(n, ntc_file, year=2025):
    # Load NTC CSV
    df = pd.read_csv(ntc_file)

    # Get unique years and sort
    available_years = sorted(df['Year'].unique())

    # Function to get NTC for a border at a specific year
    def get_ntc(border, y, direction):
        row = df[(df['Border'] == border) & (df['Year'] == y)]
        if not row.empty:
            return row.iloc[0][direction]
        return 0

    # If year exactly matches, filter directly
    if year in available_years:
        ntc_df = df[df['Year'] == year]
    else:
        # Find lower and upper bounds
        lower = max([y for y in available_years if y <= year] or [available_years[0]])
        upper = min([y for y in available_years if y >= year] or [available_years[-1]])
        
        if lower == upper:
            ntc_df = df[df['Year'] == lower]
        else:
            # Interpolate
            factor = (year - lower) / (upper - lower)
            ntc_df = df[df['Year'] == lower].copy()  # Base on lower
            for i, row in ntc_df.iterrows():
                border = row['Border']
                ntc_f_lower = row['NTC_F']
                ntc_b_lower = row['NTC_B']
                ntc_f_upper = get_ntc(border, upper, 'NTC_F')
                ntc_b_upper = get_ntc(border, upper, 'NTC_B')
                ntc_df.at[i, 'NTC_F'] = ntc_f_lower + factor * (ntc_f_upper - ntc_f_lower)
                ntc_df.at[i, 'NTC_B'] = ntc_b_lower + factor * (ntc_b_upper - ntc_b_lower)

    # Load the network
    # n = pypsa.Network(snakemake.input.network)

    # Function to identify cross-border components
    def is_cross_border(component):
        bus0_country = n.buses.at[component.bus0, 'country']
        bus1_country = n.buses.at[component.bus1, 'country']
        return bus0_country != bus1_country

    # Remove existing cross-border lines and links
    cross_border_lines = n.lines[n.lines.apply(is_cross_border, axis=1)].index
    n.mremove("Line", cross_border_lines)

    cross_border_links = n.links[n.links.apply(is_cross_border, axis=1)].index
    n.mremove("Link", cross_border_links)

    # Add a single bidirectional link for each border using one NTC configuration
    for _, row in ntc_df.iterrows():
        from_country = row['From']
        to_country = row['To']
        ntc_f = row['NTC_F']
        ntc_b = row['NTC_B']
        
        from_buses = n.buses[n.buses['country'] == from_country].index
        to_buses = n.buses[n.buses['country'] == to_country].index
        
        if from_buses.empty or to_buses.empty:
            print(f"Skipping {from_country}-{to_country}: Country not in network.")
            continue
        
        from_bus = from_buses[0]
        to_bus = to_buses[0]
        
        larger = max(ntc_f, ntc_b)
        smaller = min(ntc_f, ntc_b)
        
        if larger > 0:
            if ntc_f >= ntc_b:
                bus0 = from_bus
                bus1 = to_bus
                direction = f"{from_country} -> {to_country}"
            else:
                bus0 = to_bus
                bus1 = from_bus
                direction = f"{to_country} -> {from_country}"
            
            p_min_pu = -smaller / larger if larger > 0 else 0
            
            n.add(
                "Link",
                f"{direction} NTC {year}",
                bus0=bus0,
                bus1=bus1,
                p_nom=larger,
                p_min_pu=p_min_pu,
                p_max_pu=1,
                efficiency=1.0,
                carrier="DC",
                capital_cost=0,
                length=1,
                p_nom_extendable=False
            )
