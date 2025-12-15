# SPDX-FileCopyrightText: Open Energy Transition gGmbH, Ember, and contributors to the Ember Flexibility Study
#
# SPDX-License-Identifier: MIT

from scripts._helpers import (
    path_provider,
    get_rdir,
)

rule retrieve_resistive_heater_capacities:
    params:
        config_provider("ember_settings", "apply_rh_highflex_capacities")
    input:
        "results/scenario_{planning_horizons}_flex_on/networks/base_s_{clusters}_{opts}_{sector_opts}_{planning_horizons}.nc",
    output:
        resources("resistive_heater_capacities_s_{clusters}_{opts}_{sector_opts}_{planning_horizons}.csv"),
    log:
        logs("retrieve_resistive_heater_capacities_s_{clusters}_{opts}_{sector_opts}_{planning_horizons}.log"),
    resources:
        mem_mb=20000,
    benchmark:
        benchmarks("retrieve_resistive_heater_capacities_s_{clusters}_{opts}_{sector_opts}_{planning_horizons}")
    threads: 8
    script:
        "../scripts/retrieve_resistive_heater_capacities.py"
