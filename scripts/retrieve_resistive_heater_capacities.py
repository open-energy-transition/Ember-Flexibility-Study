# SPDX-FileCopyrightText: Open Energy Transition gGmbH, Ember, and contributors to the Ember Flexibility Study
#
# SPDX-License-Identifier: CC0-1.0

import pypsa
import pandas as pd

import logging

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    if "snakemake" not in globals():
        from _helpers import mock_snakemake

        snakemake = mock_snakemake(
            "retrieve_resistive_heater_capacities",
            clusters="39",
            opts="",
            sector_opts="",
            planning_horizons=2030,
        )
    
    n = pypsa.Network(snakemake.input[0])

    resistive_heater_caps = n.links[n.links.carrier.str.contains("resistive heater")].p_nom_opt

    resistive_heater_caps.to_csv(snakemake.output[0])
