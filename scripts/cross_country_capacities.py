import argparse
import pathlib

import pypsa
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

path_cwd = pathlib.Path(__file__).parent.parent.resolve()


def parse_input_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed command line arguments containing:
        - path_to_network: pathlib.Path
            Path to the PyPSA-Eur network file.
        - path_to_output: pathlib.Path
            Path to the output plot file.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path_to_network",
        type=str,
        help="Path to the PyPSA-Eur network file. Example: 'results/validation_2023/networks/base_s_39_elec_Co2L-168H.nc'.",
        required=True,
    )
    parser.add_argument(
        "--path_to_ember_data",
        type=str,
        help="Path to the Ember input file. Example: 'validation/ember_data/file_name'.",
        required=True,
    )
    parser.add_argument(
        "--path_to_output",
        type=str,
        help="Path to the output file. Example: 'results/validation_2023/outputs/file_name'.",
        required=True,
    )
    parser.add_argument(
        "--path_to_output_plot",
        type=str,
        help="Path to the output plot. Example: 'results/validation_2023/plots/file_name'.",
        required=True,
    )
    return parser.parse_args()


if __name__ == "__main__":

    # Load input arguments
    args = parse_input_arguments()
    network_path = pathlib.Path(path_cwd, args.path_to_network)
    csv_path = pathlib.Path(path_cwd, args.path_to_ember_data)
    output_csv = pathlib.Path(path_cwd, args.path_to_output)
    output_plot = pathlib.Path(path_cwd, args.path_to_output_plot)

    # Load the PyPSA-Eur network
    network = pypsa.Network(network_path)

    # Ensure buses have 'country' attribute
    if 'country' not in network.buses.columns:
        network.buses['country'] = network.buses.index.map(lambda x: x.split()[0] if isinstance(x, str) else None)
        network.buses = network.buses.dropna(subset=['country'])

    # Process lines (AC transmission)
    lines = network.lines.copy()
    lines['country0'] = lines['bus0'].map(network.buses['country'])
    lines['country1'] = lines['bus1'].map(network.buses['country'])
    cross_border_lines = lines[(lines['country0'] != lines['country1']) & lines['country0'].notna() & lines['country1'].notna()]

    capacities = defaultdict(float)
    for _, row in cross_border_lines.iterrows():
        pair = frozenset({row['country0'], row['country1']})
        capacities[pair] += row['s_nom']

    # Process links (e.g., HVDC)
    links = network.links.copy()
    if not links.empty:
        links['country0'] = links['bus0'].map(network.buses['country'])
        links['country1'] = links['bus1'].map(network.buses['country'])
        cross_border_links = links[(links['country0'] != links['country1']) & links['country0'].notna() & links['country1'].notna()]
        for _, row in cross_border_links.iterrows():
            pair = frozenset({row['country0'], row['country1']})
            capacities[pair] += row['p_nom']

    # Convert to DataFrame
    capacities_df = pd.DataFrame({
        'Country Pair': ['-'.join(sorted(pair)) for pair in capacities.keys()],
        'Model Capacity (MW)': capacities.values()
    }).sort_values('Country Pair').reset_index(drop=True)

    # Load Ember reference CSV
    csv_df = pd.read_csv(csv_path)
    csv_df = csv_df[csv_df['Year'] == 2024]
    csv_df['Country Pair'] = csv_df.apply(lambda row: '-'.join(sorted([row['From'], row['To']])), axis=1)

    aggregated_csv = csv_df.groupby('Country Pair').agg({'NTC_F': 'mean', 'NTC_B': 'mean'}).reset_index()
    aggregated_csv['Ember NTC (MW)'] = (aggregated_csv['NTC_F'] + aggregated_csv['NTC_B']) / 2

    # Merge and compare
    comparison_df = pd.merge(capacities_df, aggregated_csv[['Country Pair', 'Ember NTC (MW)']], on='Country Pair', how='outer').fillna(0)
    comparison_df['Difference (MW)'] = comparison_df['Model Capacity (MW)'] - comparison_df['Ember NTC (MW)']

    # Filter for selected countries
    focus_comparison = comparison_df[comparison_df['Country Pair'].str.contains('DE|NL|IT|PL|CZ|GR', na=False)]

    # Save to CSV
    focus_comparison.to_csv(output_csv, index=False)

    # Plot bar chart for comparison
    focus_comparison.plot(x='Country Pair', y=['Model Capacity (MW)', 'Ember NTC (MW)'], kind='bar', figsize=(14, 8), width=0.35)
    plt.title("Comparison of Model vs Ember NTC Interconnection Capacities (2024) for Focus Countries")
    plt.ylabel("Capacity (MW)")
    plt.xlabel("Country Pair")
    plt.xticks(rotation=45, ha='right')
    plt.legend(title="Source")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(output_plot)
    plt.close()
