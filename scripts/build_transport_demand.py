# SPDX-FileCopyrightText: Contributors to PyPSA-Eur <https://github.com/pypsa/pypsa-eur>
#
# SPDX-License-Identifier: MIT
"""
Build land transport demand per clustered model region including efficiency
improvements due to drivetrain changes, time series for electric vehicle
availability and demand-side management constraints.
"""

import logging

import numpy as np
import pandas as pd
import pypsa
import xarray as xr

from scripts._helpers import (
    configure_logging,
    generate_periodic_profiles,
    get_snapshots,
    set_scenario_config,
)

logger = logging.getLogger(__name__)


def build_nodal_transport_data(fn, fn_ember, pop_layout, energy_totals_year, planning_horizon):
    # get numbers of car and fuel efficiency per country
    transport_data = pd.read_csv(fn, index_col=[0, 1])
    transport_data_ember = pd.read_csv(fn_ember, index_col=[0])
    transport_data = transport_data.xs(energy_totals_year, level="year")
    if planning_horizon in transport_data_ember.columns:
        transport_data_ember = transport_data_ember[planning_horizon]
        transport_data.loc[transport_data_ember.index, "number cars"] = (
            transport_data_ember
        )

    # break number of cars down to nodal level based on population density
    nodal_transport_data = transport_data.loc[pop_layout.ct].fillna(0.0)
    nodal_transport_data.index = pop_layout.index
    nodal_transport_data["number cars"] = (
        pop_layout["fraction"] * nodal_transport_data["number cars"]
    )
    # fill missing fuel efficiency with average data
    nodal_transport_data.loc[
        nodal_transport_data["average fuel efficiency"] == 0.0,
        "average fuel efficiency",
    ] = transport_data["average fuel efficiency"].mean()

    return nodal_transport_data


def build_transport_demand(traffic_fn, airtemp_fn, nodes, nodal_transport_data):
    """
    Returns transport demand per bus in unit km driven [100 km].
    """
    # averaged weekly counts from the year 2010-2015
    traffic = pd.read_csv(traffic_fn, skiprows=2, usecols=["count"]).squeeze("columns")

    # create annual profile take account time zone + summer time
    transport_shape = generate_periodic_profiles(
        dt_index=snapshots,
        nodes=nodes,
        weekly_profile=traffic.values,
    )
    transport_shape = transport_shape / transport_shape.sum()

    # get heating demand for correction to demand time series
    temperature = xr.open_dataarray(airtemp_fn).to_pandas()

    # correction factors for vehicle heating
    dd_ICE = transport_degree_factor(
        temperature,
        options["transport_heating_deadband_lower"],
        options["transport_heating_deadband_upper"],
        options["ICE_lower_degree_factor"],
        options["ICE_upper_degree_factor"],
    )

    # divide out the heating/cooling demand from ICE totals
    ice_correction = (transport_shape * (1 + dd_ICE)).sum() / transport_shape.sum()

    # unit TWh
    energy_totals_transport = (
        pop_weighted_energy_totals["total road"]
        + pop_weighted_energy_totals["total rail"]
        - pop_weighted_energy_totals["electricity rail"]
    )

    # average fuel efficiency in MWh/100 km
    eff = nodal_transport_data["average fuel efficiency"]

    return (transport_shape.multiply(energy_totals_transport) * 1e6 * nyears).divide(
        eff * ice_correction
    )


def transport_degree_factor(
    temperature,
    deadband_lower=15,
    deadband_upper=20,
    lower_degree_factor=0.5,
    upper_degree_factor=1.6,
):
    """
    Work out how much energy demand in vehicles increases due to heating and
    cooling.

    There is a deadband where there is no increase. Degree factors are %
    increase in demand compared to no heating/cooling fuel consumption.
    Returns per unit increase in demand for each place and time
    """

    dd = temperature.copy()

    dd[(temperature > deadband_lower) & (temperature < deadband_upper)] = 0.0

    dT_lower = deadband_lower - temperature[temperature < deadband_lower]
    dd[temperature < deadband_lower] = lower_degree_factor / 100 * dT_lower

    dT_upper = temperature[temperature > deadband_upper] - deadband_upper
    dd[temperature > deadband_upper] = upper_degree_factor / 100 * dT_upper

    return dd


def bev_availability_profile(fn, snapshots, nodes, options):
    """
    Derive plugged-in availability for passenger electric vehicles.
    """
    # car count in typical week
    traffic = pd.read_csv(fn, skiprows=2, usecols=["count"]).squeeze("columns")
    # maximum share plugged-in availability for passenger electric vehicles
    avail_max = options["bev_avail_max"]
    # minimum share plugged-in availability for passenger electric vehicles
    avail_min = options["bev_avail_min"]

    if avail_min < 0:
        logger.warning(
            "Minimum BEV availability is negative, which may lead to infeasibility."
        )
    if avail_max < avail_min:
        logger.warning(
            "Maximum BEV availability is lower than minimum, which may "
            "lead to infeasibility."
        )

    # linear scaling, highest when traffic is lowest, decreases if traffic increases
    avail = avail_max - (avail_max - avail_min) * (traffic - traffic.min()) / (
        traffic.max() - traffic.min()
    )

    return generate_periodic_profiles(
        dt_index=snapshots,
        nodes=nodes,
        weekly_profile=avail.values,
    )


if __name__ == "__main__":
    if "snakemake" not in globals():
        from scripts._helpers import mock_snakemake

        snakemake = mock_snakemake("build_transport_demand", clusters=128)
    configure_logging(snakemake)
    set_scenario_config(snakemake)

    pop_layout = pd.read_csv(snakemake.input.clustered_pop_layout, index_col=0)

    nodes = pop_layout.index

    pop_weighted_energy_totals = pd.read_csv(
        snakemake.input.pop_weighted_energy_totals, index_col=0
    )

    options = snakemake.params.sector

    snapshots = get_snapshots(
        snakemake.params.snapshots, snakemake.params.drop_leap_day, tz="UTC"
    )

    n = pypsa.Network(snakemake.input.network)
    nyears = n.snapshot_weightings.generators.sum() / 8760.0

    energy_totals_year = snakemake.params.energy_totals_year
    planning_horizon = snakemake.wildcards.planning_horizons
    nodal_transport_data = build_nodal_transport_data(
        snakemake.input.transport_data, snakemake.input.transport_data_ember,
        pop_layout, energy_totals_year, planning_horizon
    )

    transport_demand = build_transport_demand(
        snakemake.input.traffic_data_KFZ,
        snakemake.input.temp_air_total,
        nodes,
        nodal_transport_data,
    )

    avail_profile = bev_availability_profile(
        snakemake.input.traffic_data_Pkw, snapshots, nodes, options
    )

    nodal_transport_data.to_csv(snakemake.output.transport_data)
    transport_demand.to_csv(snakemake.output.transport_demand)
    avail_profile.to_csv(snakemake.output.avail_profile)
