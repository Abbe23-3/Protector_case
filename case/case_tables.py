import pandas as pd

FILE = "Case Protector Analyst 2026 (kopia).xlsx"
INFLATION = 0.05
TARGET_YEAR = 2026
VEHICLES_2026 = 100
COMPETITOR_PREMIUM = 450_000

pd.options.display.float_format = "{:,.2f}".format

# --- Claims tab: one row per individual claim ---
claims = pd.read_excel(FILE, sheet_name="Claims")
claims["Claim date"] = pd.to_datetime(claims["Claim date"])
claims["Inflation factor"] = (1 + INFLATION) ** (TARGET_YEAR - claims["Year"])
claims["Claim cost 2026"] = claims["Claim cost"] * claims["Inflation factor"]

# --- Case tab: yearly summary table (rows 17-20, columns B-G) ---
case_summary = (
    pd.read_excel(FILE, sheet_name="Case", usecols="B:G", skiprows=16, nrows=3, index_col=0)
    .rename_axis(None)
)
case_summary.columns = case_summary.columns.astype(int)
case_summary = case_summary.T.rename_axis("Year")
case_summary = case_summary.apply(pd.to_numeric, errors="coerce")  # '?' in 2026 -> NaN

history = case_summary.loc[: TARGET_YEAR - 1].copy()

# --- Claim frequency per year ---
frequency = history[["Number of claims", "Number of vehicles"]].copy()
frequency["Claims per vehicle"] = frequency["Number of claims"] / frequency["Number of vehicles"]
frequency.loc["Total"] = frequency[["Number of claims", "Number of vehicles"]].sum()
frequency.loc["Total", "Claims per vehicle"] = (
    frequency.loc["Total", "Number of claims"] / frequency.loc["Total", "Number of vehicles"]
)

# --- Claim cost adjusted to 2026 prices ---
inflation_adjusted = history[["Claim cost", "Number of vehicles"]].copy()
inflation_adjusted["Inflation factor"] = (1 + INFLATION) ** (TARGET_YEAR - inflation_adjusted.index)
inflation_adjusted["Claim cost 2026"] = inflation_adjusted["Claim cost"] * inflation_adjusted["Inflation factor"]
inflation_adjusted["Cost per vehicle 2026"] = (
    inflation_adjusted["Claim cost 2026"] / inflation_adjusted["Number of vehicles"]
)
inflation_adjusted.loc["Total"] = inflation_adjusted[["Claim cost", "Number of vehicles", "Claim cost 2026"]].sum()
inflation_adjusted.loc["Total", "Cost per vehicle 2026"] = (
    inflation_adjusted.loc["Total", "Claim cost 2026"] / inflation_adjusted.loc["Total", "Number of vehicles"]
)

# --- 2026 forecast and premium ---
freq_2026 = frequency.loc["Total", "Claims per vehicle"]
severity_2026 = claims["Claim cost 2026"].mean()
expected_claims = freq_2026 * VEHICLES_2026
expected_cost = inflation_adjusted.loc["Total", "Cost per vehicle 2026"] * VEHICLES_2026
# Compound Poisson standard deviation: sqrt(lambda * E[X^2])
std_cost = (expected_claims * (claims["Claim cost 2026"] ** 2).mean()) ** 0.5

premium = pd.DataFrame(
    {
        "Value (SEK)": [
            expected_claims,
            severity_2026,
            expected_cost,
            std_cost,
            expected_cost + 1.645 * std_cost,
            COMPETITOR_PREMIUM,
            expected_cost / COMPETITOR_PREMIUM,
        ]
    },
    index=[
        "Expected number of claims",
        "Average claim cost (2026 prices)",
        "Expected claim cost (pure premium)",
        "Standard deviation of claim cost",
        "Bad year (95th percentile)",
        "Competitor premium",
        "Loss ratio at competitor price",
    ],
)

if __name__ == "__main__":
    for name, df in [
        ("claims", claims),
        ("case_summary", case_summary),
        ("frequency", frequency),
        ("inflation_adjusted", inflation_adjusted),
        ("premium", premium),
    ]:
        print(f"\n=== {name} ===")
        print(df.to_string())
