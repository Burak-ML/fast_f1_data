"""Check how well the estimator does on races it has not seen.

    python -m analysis.report --data analysis/data/race_dataset.csv
"""
import argparse

from analysis import estimator


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="analysis/data/race_dataset.csv")
    args = ap.parse_args()

    df = estimator.load_dataset(args.data)
    m = estimator.evaluate(df)
    a = estimator.Analyst(df)

    print("rows=%d races=%d (last %d held out)" % (m["rows"], m["races"], m["test_races"]))
    print("average miss, in positions:")
    print("  finish = grid          : %.2f" % m["mae_grid_baseline"])
    print("  + grid-slot history    : %.2f" % m["mae_grid_curve"])
    print("  + team, driver, weather: %.2f" % m["mae_full"])
    print("within 3 positions: %.0f%%" % (100 * m["within_3_positions"]))
    print("weather pull (races): rain %.2f (%d), hot %.2f (%d), cool %.2f (%d)" % (
        a.pull["rain"], a.n["rain"], a.pull["hot"], a.n["hot"], a.pull["cool"], a.n["cool"]))
    if not m["beats_baseline"]:
        print("NOTE: this does not beat 'finish where you start'.")


if __name__ == "__main__":
    main()
