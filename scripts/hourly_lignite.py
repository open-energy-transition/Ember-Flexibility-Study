import pandas as pd

def hourly_lignity_from_coal(hourly_coal, avg_lignite):

    hourly_lignite = (
        avg_lignite * ( hourly_coal / hourly_coal.mean() )
    )

    return hourly_lignite

if __name__ == "__main__":
    if "snakemake" not in globals():
        from scripts._helpers import mock_snakemake

        snakemake = mock_snakemake(
            "hourly_lignite_prices",
        )
    
    hourly_prices = pd.read_csv(snakemake.input[0], index_col=0)
    avg_lignite = snakemake.config["costs"].get("fuel", {"lignite": 7.7})["lignite"]

    hourly_lignite = hourly_lignity_from_coal(
        hourly_prices["COAL_SPOT_PRICE_EUR_PER_MWH"],
        avg_lignite
    )

    hourly_prices["LIGNITE_SPOT_PRICE_EUR_PER_MWH"] = hourly_lignite

    hourly_prices.to_csv(snakemake.output[0])
