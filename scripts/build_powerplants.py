# SPDX-FileCopyrightText: Contributors to PyPSA-Eur <https://github.com/pypsa/pypsa-eur>
#
# SPDX-License-Identifier: MIT

"""
Retrieves conventional powerplant capacities and locations from custom data in
`data/custom_powerplants.csv` and assigns these to buses. This script disables
the default powerplantmatching data retrieval and uses only the custom entries.

Outputs
-------

- ``resource/powerplants_s_{clusters}.csv``: A list of conventional power plants
  with fields for name, fuel type, technology, country, capacity in MW, duration,
  commissioning year, retrofit year, latitude, longitude, and dam information as
  documented in the `powerplantmatching README
  <https://github.com/PyPSA/powerplantmatching/blob/master/README.md>`_;
  additionally it includes information on the closest substation/bus in
  ``networks/base_s_{clusters}.nc``.
"""

import itertools
import logging

import pandas as pd
import pypsa
from powerplantmatching.export import map_country_bus

from scripts._helpers import configure_logging, set_scenario_config

logger = logging.getLogger(__name__)

def add_everywhere_powerplants(ppl, substations, everywhere_powerplants):
    # Create a dataframe with "everywhere_powerplants" of stated carriers at the location of all substations
    everywhere_ppl = (
        pd.DataFrame(
            itertools.product(substations.index.values, everywhere_powerplants),
            columns=["substation_index", "Fueltype"],
        ).merge(
            substations[["x", "y", "country"]],
            left_on="substation_index",
            right_index=True,
        )
    ).drop(columns="substation_index")

    # PPL uses different columns names compared to substations dataframe -> rename
    everywhere_ppl = everywhere_ppl.rename(
        columns={"x": "lon", "y": "lat", "country": "Country"}
    )

    # Add default values for the powerplants
    everywhere_ppl["Name"] = (
        "Automatically added everywhere-powerplant " + everywhere_ppl.Fueltype
    )
    everywhere_ppl["Set"] = "PP"
    everywhere_ppl["Technology"] = everywhere_ppl["Fueltype"]
    everywhere_ppl["Capacity"] = 0.0

    # Assign plausible values for the commissioning and decommissioning years
    # required for multi-year models
    everywhere_ppl["DateIn"] = pd.to_datetime("1900-01-01")  # Default start date
    everywhere_ppl["DateOut"] = pd.to_datetime("2100-01-01")  # Default end date

    # NaN values for efficiency will be replaced later in add_electricity.py
    everywhere_ppl["Efficiency"] = np.nan

    return pd.concat(
        [ppl, everywhere_ppl], sort=False, ignore_index=True, verify_integrity=True
    )

if __name__ == "__main__":
    if "snakemake" not in globals():
        from scripts._helpers import mock_snakemake
        snakemake = mock_snakemake("build_powerplants")
    configure_logging(snakemake)
    set_scenario_config(snakemake)

    n = pypsa.Network(snakemake.input.network)
    countries = snakemake.params.countries

    # Load only custom power plants, skipping powerplantmatching fetch
    ppl = pd.read_csv(snakemake.input.custom_powerplants, dtype={"bus": "str"})
    ppl = ppl[ppl['Country'].isin(countries)]  # Filter for specified countries

    # Add "everywhere powerplants" to all bus locations if configured
    if snakemake.params.everywhere_powerplants:
        ppl = add_everywhere_powerplants(
            ppl, n.buses, snakemake.params.everywhere_powerplants
        )

    ppl = ppl.dropna(subset=["lat", "lon"])
    ppl = map_country_bus(ppl, n.buses)

    bus_null_b = ppl["bus"].isnull()
    if bus_null_b.any():
        logger.warning(
            f"Couldn't find close bus for {bus_null_b.sum()} powerplants. "
            "Removing them from the powerplants list."
        )
        ppl = ppl[~bus_null_b]

    # Handle potential duplicates (e.g., from custom data)
    cumcount = ppl.groupby(["bus", "Fueltype"]).cumcount() + 1
    ppl["Name"] = ppl["Name"].where(cumcount == 1, ppl["Name"] + " " + cumcount.astype(str))

    ppl.reset_index(drop=True).to_csv(snakemake.output[0])