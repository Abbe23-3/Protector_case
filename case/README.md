# Protector pricing case

Prices motor insurance for a fleet of 100 vehicles in 2026, using claim history from 2022–2025.

**Result:** about 36 claims and 261,000 SEK expected claim cost; recommended premium **430,000 SEK**
(competitor: 450,000 SEK). See [outputs/answers.md](outputs/answers.md).

## Structure
| File | Purpose |
|---|---|
| `inputs.py` | Case data and assumptions as pandas DataFrames, plus data checks |
| `pipeline.py` | Calculation steps: frequency → inflation → severity → forecast → Monte Carlo risk → premium |
| `outputs.py` | Tables (CSV) and `answers.md` |
| `charts.py` | Charts (PNG) |
| `main.py` | Runs everything |

## Run
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
Results are written to `outputs/`.
