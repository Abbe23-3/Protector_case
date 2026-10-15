"""3a. STATIC OUTPUTS: tables printed, saved as CSV, and a written answers.md."""

from pathlib import Path

import pandas as pd

from pipeline import SELECTED_METHOD, param

TABLES = [
    "case_summary",
    "frequency",
    "inflation_adjusted",
    "severity",
    "forecast_2026",
    "risk",
    "premium",
]


def print_tables(results, checks):
    with pd.option_context("display.float_format", "{:,.2f}".format, "display.width", 140):
        print("\n=== data checks ===")
        print(checks.to_string())
        for name in TABLES:
            print(f"\n=== {name} ===")
            print(results[name].to_string())


def save_tables(results, checks, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    checks.to_csv(out_dir / "data_checks.csv")
    results["claims_adj"].to_csv(out_dir / "claims_adjusted.csv", index=False)
    for name in TABLES:
        results[name].to_csv(out_dir / f"{name}.csv", float_format="%.2f")


def write_answers(results, assumptions, path):
    freq = results["frequency"]
    infl = results["inflation_adjusted"]
    fc = results["forecast_2026"]
    risk = results["risk"]["value"]
    prem = results["premium"]["value"]
    rate = param(assumptions, "inflation_rate")
    n_vehicles = int(param(assumptions, "vehicles_2026"))

    text = f"""# Protector case: answers

## Assumptions
- Accident years are fully run-off, so the claim costs are final; zero-cost claims count as claims.
- The risk per vehicle in 2026 is the same as in 2022–2025 ({n_vehicles} vehicles in 2026).
- Claim costs grow with {rate:.0%} inflation per year; admin cost is 0.
- Years are weighted by number of vehicles, so 2022–2023 (1–2 vehicles) carry almost no weight.

## 1. How many claims will occur in 2026?
**About {fc.loc[SELECTED_METHOD, 'expected_claims']:.0f} claims.**
{freq.loc['Total', 'n_claims']:.0f} claims over {freq.loc['Total', 'vehicles']:.0f} vehicle-years gives
{freq.loc['Total', 'claims_per_vehicle']:.3f} claims per vehicle × {n_vehicles} vehicles.
Using only 2024–2025 gives {fc.loc['2024–2025 only', 'expected_claims']:.1f}.

## 2. What will the claim cost be in 2026?
**About {fc.loc[SELECTED_METHOD, 'expected_claim_cost']:,.0f} SEK** (in 2026 prices).
Total cost in 2026 prices is {infl.loc['Total', 'claim_cost_2026']:,.0f} SEK over
{infl.loc['Total', 'vehicles']:.0f} vehicle-years = {infl.loc['Total', 'cost_per_vehicle_2026']:,.0f} SEK per vehicle.
That equals {fc.loc[SELECTED_METHOD, 'expected_claims']:.1f} claims × {fc.loc[SELECTED_METHOD, 'avg_claim_cost']:,.0f} SEK average claim.
Using only 2024–2025 gives {fc.loc['2024–2025 only', 'expected_claim_cost']:,.0f} SEK.

## 3. What premium shall we offer?
**{prem['Recommended premium']:,.0f} SEK for {n_vehicles} vehicles
({prem['Recommended premium per vehicle']:,.0f} SEK per vehicle).**
- Break-even (pure) premium: {prem['Pure premium (break-even)']:,.0f} SEK.
- The portfolio is small and volatile: standard deviation {risk['Standard deviation (simulated)']:,.0f} SEK,
  a 1-in-20 bad year costs {risk['P95 (1-in-20 bad year)']:,.0f} SEK.
- The recommended premium covers that bad year, is {prem['Discount vs competitor']:,.0f} SEK below the competitor
  ({prem['Competitor premium']:,.0f} SEK), and gives an expected loss ratio of {prem['Expected loss ratio']:.0%}.
- Chance that claims exceed the premium: {prem['P(claims > recommended premium)']:.1%}.

## 4. Should inflation be taken into account?
**Yes.** Old claims would cost more if they happened in 2026. Inflation raises the total historical cost from
{infl.loc['Total', 'claim_cost']:,.0f} to {infl.loc['Total', 'claim_cost_2026']:,.0f} SEK
(+{infl.loc['Total', 'claim_cost_2026'] / infl.loc['Total', 'claim_cost'] - 1:.1%}).
Without it the premium would be too low.
"""
    Path(path).write_text(text, encoding="utf-8")
