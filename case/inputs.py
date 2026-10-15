"""1. DATA INPUTS: the case data as pandas DataFrames."""

import pandas as pd

# Case tab: assumptions & conditions, plus modelling choices
assumptions = pd.DataFrame(
    [
        ("vehicles_2026", 100, "Assume there will be 100 vehicles in 2026"),
        ("admin_cost", 0, "Operating/administrative cost is 0"),
        ("competitor_premium", 450_000, "Nearest competitor's premium for 100 vehicles (SEK)"),
        ("inflation_rate", 0.05, "Annual inflation rate"),
        ("target_year", 2026, "Year we are pricing"),
        ("target_percentile", 0.95, "Premium should cover a 1-in-20 bad year"),
        ("premium_rounding", 5_000, "Round the premium up to the nearest 5,000 SEK"),
        ("mc_simulations", 100_000, "Number of Monte Carlo simulations"),
        ("mc_seed", 2026, "Random seed, so results are reproducible"),
    ],
    columns=["parameter", "value", "description"],
).set_index("parameter")

# Case tab: number of vehicles per year (exposure)
vehicles = pd.DataFrame(
    {
        "year": [2022, 2023, 2024, 2025, 2026],
        "vehicles": [1, 2, 87, 100, 100],
    }
).set_index("year")

# Claims tab: one row per claim (accident years fully run-off)
claims = pd.DataFrame(
    [
        ("2024-01-05", 67050),
        ("2025-04-19", 56770),
        ("2024-05-06", 43599),
        ("2025-01-06", 33378),
        ("2024-03-06", 23957),
        ("2024-07-12", 21585),
        ("2025-02-06", 19051),
        ("2024-08-12", 18400),
        ("2025-12-04", 14173.927),
        ("2025-10-04", 14173.927),
        ("2025-05-04", 14173.927),
        ("2023-04-07", 13161),
        ("2024-06-12", 12798),
        ("2022-04-01", 11586),
        ("2025-11-04", 9841.6887),
        ("2025-08-04", 9841.6887),
        ("2025-03-04", 9841.6887),
        ("2025-06-10", 8125),
        ("2025-06-04", 7423),
        ("2024-02-11", 6600),
        ("2024-10-06", 5681),
        ("2025-09-04", 4303.1718),
        ("2025-04-04", 4303.1718),
        ("2024-09-06", 3949),
        ("2024-11-12", 3526),
        ("2023-05-02", 3256),
        ("2024-07-06", 3209),
        ("2025-03-19", 3207),
        ("2024-12-06", 2800),
        ("2025-06-19", 2620),
        ("2024-06-06", 2539),
        ("2024-12-12", 2208),
        ("2025-07-04", 336),
        ("2025-07-19", 300),
        ("2024-11-06", 0),
        ("2024-08-06", 0),
        ("2024-04-06", 0),
        ("2024-02-05", 0),
        ("2025-12-10", 0),
        ("2025-11-10", 0),
        ("2025-10-10", 0),
        ("2025-09-10", 0),
        ("2025-08-10", 0),
        ("2025-07-10", 0),
        ("2025-05-10", 0),
        ("2025-04-10", 0),
        ("2025-03-10", 0),
        ("2025-02-12", 0),
        ("2025-01-12", 0),
        ("2024-10-12", 0),
        ("2024-09-12", 0),
        ("2024-05-12", 0),
        ("2024-04-12", 0),
        ("2024-03-12", 0),
        ("2024-01-11", 0),
        ("2025-12-19", 0),
        ("2025-11-19", 0),
        ("2024-10-21", 0),
        ("2025-09-19", 0),
        ("2024-08-21", 0),
        ("2025-05-19", 0),
        ("2025-02-21", 0),
        ("2025-01-21", 0),
        ("2024-12-21", 0),
        ("2024-11-21", 0),
        ("2024-10-21", 0),
        ("2024-09-21", 0),
        ("2024-08-21", 0),
    ],
    columns=["claim_date", "claim_cost"],
)
claims["claim_date"] = pd.to_datetime(claims["claim_date"])
claims["year"] = claims["claim_date"].dt.year
claims = claims[["claim_date", "year", "claim_cost"]]


def validate(claims, vehicles):
    """Check the inputs against the totals in the case and flag data-quality notes."""
    assert len(claims) == 68, "expected 68 claims"
    assert round(claims["claim_cost"].sum(), 2) == 457_767.19, "total claim cost does not match the case"
    assert vehicles.loc[:2025, "vehicles"].sum() == 190, "expected 190 vehicle-years"
    assert claims["year"].isin(vehicles.index).all(), "claim year without vehicle data"
    assert (claims["claim_cost"] >= 0).all(), "negative claim cost"

    paid = claims[claims["claim_cost"] > 0]
    repeated = paid[paid.duplicated("claim_cost", keep=False)]
    return pd.DataFrame(
        {
            "check": [
                "Claims closed at zero cost",
                "Paid claims with a repeated amount",
                "Years with fewer than 10 vehicles",
            ],
            "result": [
                int((claims["claim_cost"] == 0).sum()),
                int(len(repeated)),
                ", ".join(str(y) for y in vehicles.index[vehicles["vehicles"] < 10]),
            ],
        }
    ).set_index("check")
