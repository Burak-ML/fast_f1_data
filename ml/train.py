"""Train the finishing-position model.

    python -m ml.train --data ml/data/race_dataset.csv
"""
import argparse

from ml import model


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="ml/data/race_dataset.csv")
    args = ap.parse_args()

    df = model.load_dataset(args.data)
    pipe, metrics = model.train(df)
    model.save(pipe, metrics)

    print("rows=%d races=%d (last %d held out)"
          % (metrics["rows"], metrics["races"], metrics["test_races"]))
    print("MAE model         : %.2f positions" % metrics["mae_model"])
    print("MAE finish = grid : %.2f positions" % metrics["mae_grid_baseline"])
    print("within 3 positions: %.0f%%" % (100 * metrics["within_3_positions"]))
    if not metrics["beats_baseline"]:
        print("WARNING: the model does not beat 'finish where you start'.")


if __name__ == "__main__":
    main()
