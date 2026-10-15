"""Run the Protector case: inputs -> pipeline -> static and graphical outputs."""

from pathlib import Path

import charts
import outputs
import pipeline
from inputs import assumptions, claims, validate, vehicles

OUT = Path(__file__).parent / "outputs"


def main():
    checks = validate(claims, vehicles)
    results = pipeline.run(claims, vehicles, assumptions)

    outputs.print_tables(results, checks)
    outputs.save_tables(results, checks, OUT / "tables")
    outputs.write_answers(results, assumptions, OUT / "answers.md")
    charts.save_all(results, OUT / "charts")

    print(f"\nSaved tables, answers.md and charts to {OUT}")


if __name__ == "__main__":
    main()
