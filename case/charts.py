"""3b. GRAPHICAL OUTPUTS: charts saved as PNG."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

BLUE = "#2F6DB5"
ORANGE = "#E07B39"
GREEN = "#3A9D5D"
RED = "#C0392B"
GREY = "#8A8F98"

SEK = FuncFormatter(lambda x, _: f"{x:,.0f}")
THOUSANDS = FuncFormatter(lambda x, _: f"{x / 1000:,.0f}k")

plt.rcParams.update(
    {
        "figure.figsize": (9, 5),
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.alpha": 0.3,
        "axes.titleweight": "bold",
    }
)


def _years(df):
    return df.drop(index="Total", errors="ignore")


def volume(case_summary, ax):
    df = case_summary.dropna(subset=["n_claims"])
    x = np.arange(len(df))
    ax.bar(x - 0.2, df["vehicles"], 0.4, label="Vehicles", color=BLUE)
    ax.bar(x + 0.2, df["n_claims"], 0.4, label="Claims", color=ORANGE)
    ax.set_xticks(x, df.index)
    ax.set_title("Vehicles and claims per year")
    ax.legend()


def frequency(frequency, ax):
    df = _years(frequency)
    total = frequency.loc["Total", "claims_per_vehicle"]
    ax.plot(df.index.astype(str), df["claims_per_vehicle"], marker="o", color=BLUE)
    ax.axhline(total, ls="--", color=GREY, label=f"All years: {total:.3f}")
    for year, row in df.iterrows():
        ax.annotate(f"{row['vehicles']:.0f} veh.", (str(year), row["claims_per_vehicle"]),
                    textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9, color=GREY)
    ax.set_ylim(0, 1.15)
    ax.set_title("Claims per vehicle (2022–23 based on 1–2 vehicles)")
    ax.legend()


def inflation(inflation_adjusted, ax):
    df = _years(inflation_adjusted)
    x = np.arange(len(df))
    ax.bar(x - 0.2, df["cost_per_vehicle"], 0.4, label="Actual prices", color=GREY)
    ax.bar(x + 0.2, df["cost_per_vehicle_2026"], 0.4, label="2026 prices", color=BLUE)
    total = inflation_adjusted.loc["Total", "cost_per_vehicle_2026"]
    ax.axhline(total, ls="--", color=ORANGE, label=f"All years, 2026 prices: {total:,.0f}")
    ax.set_xticks(x, df.index)
    ax.yaxis.set_major_formatter(SEK)
    ax.set_title("Claim cost per vehicle (SEK)")
    ax.legend()


def claim_sizes(claims_adj, ax):
    costs = claims_adj["claim_cost_2026"]
    paid = costs[costs > 0]
    ax.hist(paid, bins=np.arange(0, paid.max() + 5000, 5000), color=BLUE, edgecolor="white")
    ax.xaxis.set_major_formatter(THOUSANDS)
    ax.set_xlabel("Claim cost, 2026 prices (SEK)")
    ax.set_ylabel("Number of claims")
    ax.set_title(f"Paid claim sizes ({(costs == 0).sum()} of {len(costs)} claims closed at zero cost)")


def simulation(simulated, premium, ax):
    p = premium["value"]
    ax.hist(simulated, bins=80, color=BLUE, alpha=0.6, edgecolor="none")
    for value, label, color in [
        (p["Expected claim cost"], "Expected cost", GREY),
        (p["Recommended premium"], "Recommended premium", GREEN),
        (p["Competitor premium"], "Competitor", RED),
    ]:
        ax.axvline(value, color=color, lw=2, label=f"{label}: {value:,.0f}")
    ax.xaxis.set_major_formatter(THOUSANDS)
    ax.set_xlabel("Total claim cost 2026 (SEK)")
    ax.set_ylabel("Simulated years")
    ax.set_title(f"Simulated 2026 claim cost ({len(simulated):,} simulations)")
    ax.legend()


def waterfall(premium, ax):
    p = premium["value"]
    steps = [
        ("Expected\nclaim cost", 0, p["Expected claim cost"], BLUE),
        ("Admin cost", p["Expected claim cost"], p["Admin cost"], GREY),
        ("Risk & profit\nmargin", p["Pure premium (break-even)"], p["Risk & profit margin"], ORANGE),
        ("Recommended\npremium", 0, p["Recommended premium"], GREEN),
        ("Competitor", 0, p["Competitor premium"], RED),
    ]
    for i, (label, bottom, height, color) in enumerate(steps):
        ax.bar(i, height, bottom=bottom, color=color)
        ax.text(i, bottom + height, f"{height:,.0f}", ha="center", va="bottom", fontsize=9)
    ax.set_xticks(range(len(steps)), [s[0] for s in steps])
    ax.yaxis.set_major_formatter(THOUSANDS)
    ax.set_title("From expected cost to premium (SEK, 100 vehicles)")


def save_all(results, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    charts = {
        "1_volume": lambda ax: volume(results["case_summary"], ax),
        "2_frequency": lambda ax: frequency(results["frequency"], ax),
        "3_inflation": lambda ax: inflation(results["inflation_adjusted"], ax),
        "4_claim_sizes": lambda ax: claim_sizes(results["claims_adj"], ax),
        "5_simulation": lambda ax: simulation(results["simulated"], results["premium"], ax),
        "6_premium_waterfall": lambda ax: waterfall(results["premium"], ax),
    }
    for name, draw in charts.items():
        fig, ax = plt.subplots()
        draw(ax)
        fig.tight_layout()
        fig.savefig(out_dir / f"{name}.png", dpi=150)
        plt.close(fig)
    return list(charts)
