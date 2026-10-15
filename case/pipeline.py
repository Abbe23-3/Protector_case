"""2. PIPELINE: each step takes DataFrames and returns a new DataFrame."""

import numpy as np
import pandas as pd

SELECTED_METHOD = "All years"
RECENT_YEARS = [2024, 2025]


def param(assumptions, name):
    return assumptions.loc[name, "value"]


# Step 0: yearly summary built from the individual claims
def build_case_summary(claims, vehicles):
    by_year = claims.groupby("year").agg(
        claim_cost=("claim_cost", "sum"),
        n_claims=("claim_cost", "size"),
    )
    summary = vehicles.join(by_year)[["claim_cost", "n_claims", "vehicles"]]
    summary["n_claims"] = summary["n_claims"].astype("Int64")
    return summary


# Step 1: claim frequency (Q1)
def frequency(case_summary):
    df = case_summary.dropna(subset=["n_claims"])[["n_claims", "vehicles"]].copy()
    df.loc["Total"] = df.sum()
    df["claims_per_vehicle"] = df["n_claims"] / df["vehicles"]
    return df


# Step 2: claim cost in target-year prices (Q4)
def inflation_adjusted(case_summary, assumptions):
    rate = param(assumptions, "inflation_rate")
    target = param(assumptions, "target_year")

    df = case_summary.dropna(subset=["claim_cost"])[["claim_cost", "vehicles"]].copy()
    df["inflation_factor"] = (1 + rate) ** (target - df.index)
    df["claim_cost_2026"] = df["claim_cost"] * df["inflation_factor"]
    df.loc["Total", ["claim_cost", "vehicles", "claim_cost_2026"]] = df[
        ["claim_cost", "vehicles", "claim_cost_2026"]
    ].sum()
    df["cost_per_vehicle"] = df["claim_cost"] / df["vehicles"]
    df["cost_per_vehicle_2026"] = df["claim_cost_2026"] / df["vehicles"]
    return df


def adjust_claims(claims, assumptions):
    rate = param(assumptions, "inflation_rate")
    target = param(assumptions, "target_year")

    df = claims.copy()
    df["inflation_factor"] = (1 + rate) ** (target - df["year"])
    df["claim_cost_2026"] = df["claim_cost"] * df["inflation_factor"]
    return df


# Step 3: claim size (Q2)
def severity(claims_adj):
    def stats(costs):
        return pd.Series(
            {
                "n_claims": len(costs),
                "n_zero_cost": (costs == 0).sum(),
                "share_zero_cost": (costs == 0).mean(),
                "avg_claim_cost": costs.mean(),
                "avg_paid_claim_cost": costs[costs > 0].mean(),
                "max_claim_cost": costs.max(),
            }
        )

    df = claims_adj.groupby("year")["claim_cost_2026"].apply(stats).unstack()
    df.loc["Total"] = stats(claims_adj["claim_cost_2026"])
    return df


# Step 4: 2026 forecast, compared across data windows (Q1, Q2)
def forecast_2026(frequency, inflation_adjusted, assumptions):
    n_vehicles = param(assumptions, "vehicles_2026")
    windows = {
        "All years": ["Total"],
        "2024–2025 only": RECENT_YEARS,
        "2025 only": [2025],
    }

    rows = {}
    for name, years in windows.items():
        freq = frequency.loc[years, "n_claims"].sum() / frequency.loc[years, "vehicles"].sum()
        cost = inflation_adjusted.loc[years, "claim_cost_2026"].sum() / inflation_adjusted.loc[years, "vehicles"].sum()
        rows[name] = {
            "claims_per_vehicle": freq,
            "expected_claims": freq * n_vehicles,
            "avg_claim_cost": cost / freq,
            "cost_per_vehicle": cost,
            "expected_claim_cost": cost * n_vehicles,
        }

    df = pd.DataFrame(rows).T
    df["selected"] = df.index == SELECTED_METHOD
    return df


# Step 5: risk, via Monte Carlo (Q3)
def simulate_claim_cost(claims_adj, forecast, assumptions):
    """Compound Poisson: number of claims ~ Poisson, each claim drawn from historical claims."""
    rng = np.random.default_rng(int(param(assumptions, "mc_seed")))
    n_sims = int(param(assumptions, "mc_simulations"))
    expected_claims = forecast.loc[SELECTED_METHOD, "expected_claims"]
    pool = claims_adj["claim_cost_2026"].to_numpy()

    counts = rng.poisson(expected_claims, n_sims)
    draws = rng.choice(pool, counts.sum())
    totals = np.bincount(np.repeat(np.arange(n_sims), counts), weights=draws, minlength=n_sims)
    return pd.Series(totals, name="simulated_claim_cost")


def risk(simulated, claims_adj, forecast):
    expected_claims = forecast.loc[SELECTED_METHOD, "expected_claims"]
    std_formula = np.sqrt(expected_claims * (claims_adj["claim_cost_2026"] ** 2).mean())
    return pd.DataFrame(
        {
            "value": {
                "Mean": simulated.mean(),
                "Standard deviation (simulated)": simulated.std(),
                "Standard deviation (formula)": std_formula,
                "Median (P50)": simulated.quantile(0.50),
                "P75": simulated.quantile(0.75),
                "P90": simulated.quantile(0.90),
                "P95 (1-in-20 bad year)": simulated.quantile(0.95),
                "P99 (1-in-100 bad year)": simulated.quantile(0.99),
                "Worst simulated year": simulated.max(),
            }
        }
    )


# Step 6: premium (Q3)
def premium(forecast, simulated, assumptions):
    n_vehicles = param(assumptions, "vehicles_2026")
    admin = param(assumptions, "admin_cost")
    competitor = param(assumptions, "competitor_premium")
    rounding = param(assumptions, "premium_rounding")

    expected_cost = forecast.loc[SELECTED_METHOD, "expected_claim_cost"]
    pure_premium = expected_cost + admin
    bad_year = simulated.quantile(param(assumptions, "target_percentile")) + admin
    recommended = np.ceil(bad_year / rounding) * rounding
    if recommended >= competitor:
        recommended = competitor - rounding  # stay below the competitor

    return pd.DataFrame(
        {
            "value": {
                "Expected claim cost": expected_cost,
                "Admin cost": admin,
                "Pure premium (break-even)": pure_premium,
                "Risk & profit margin": recommended - pure_premium,
                "Recommended premium": recommended,
                "Recommended premium per vehicle": recommended / n_vehicles,
                "Competitor premium": competitor,
                "Discount vs competitor": competitor - recommended,
                "Expected profit": recommended - pure_premium,
                "Expected loss ratio": expected_cost / recommended,
                "P(claims > recommended premium)": (simulated + admin > recommended).mean(),
                "P(claims > competitor premium)": (simulated + admin > competitor).mean(),
            }
        }
    )


def run(claims, vehicles, assumptions):
    """Run every step and return all results by name."""
    r = {}
    r["case_summary"] = build_case_summary(claims, vehicles)
    r["frequency"] = frequency(r["case_summary"])
    r["inflation_adjusted"] = inflation_adjusted(r["case_summary"], assumptions)
    r["claims_adj"] = adjust_claims(claims, assumptions)
    r["severity"] = severity(r["claims_adj"])
    r["forecast_2026"] = forecast_2026(r["frequency"], r["inflation_adjusted"], assumptions)
    r["simulated"] = simulate_claim_cost(r["claims_adj"], r["forecast_2026"], assumptions)
    r["risk"] = risk(r["simulated"], r["claims_adj"], r["forecast_2026"])
    r["premium"] = premium(r["forecast_2026"], r["simulated"], assumptions)
    return r
