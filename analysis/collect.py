"""Build analysis/data/race_dataset.csv from the free OpenF1 API (no key needed).

    python -m analysis.collect --years 2024 2025

One row per driver per race: grid slot, finishing position, team, average
track temperature and whether it rained. Responses are cached under
analysis/data/raw/, so an interrupted run resumes where it stopped.
"""
import argparse
import csv
import json
import os
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://api.openf1.org/v1"
DEFAULT_OUT = "analysis/data/race_dataset.csv"
DEFAULT_CACHE = "analysis/data/raw"
COLUMNS = ["season", "round", "driver_id", "constructor_id", "grid",
           "track_temperature", "rainfall", "finish_position"]


class Client:
    """Tiny OpenF1 client: polite pacing, retries on 429/5xx, on-disk cache."""

    def __init__(self, cache_dir=DEFAULT_CACHE, pause=0.5, retries=5):
        self.cache_dir, self.pause, self.retries = cache_dir, pause, retries

    def _cache_path(self, endpoint, params):
        name = "_".join([endpoint] + ["%s-%s" % kv for kv in sorted(params.items())])
        return os.path.join(self.cache_dir, name + ".json")

    def get(self, endpoint, **params):
        path = self._cache_path(endpoint, params)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        url = "%s/%s?%s" % (BASE_URL, endpoint, urllib.parse.urlencode(params))
        for attempt in range(self.retries):
            time.sleep(self.pause)
            try:
                with urllib.request.urlopen(url, timeout=60) as resp:
                    data = json.load(resp)
                break
            except urllib.error.HTTPError as e:
                if e.code not in (429, 500, 502, 503, 504) or attempt == self.retries - 1:
                    raise
                time.sleep(float(e.headers.get("Retry-After") or 2 ** (attempt + 1)))
        if data:                                # never cache "not available yet"
            os.makedirs(self.cache_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        return data


def race_rows(client, year):
    """Rows for every finished Race session of `year`. Sprints are excluded."""
    sessions = sorted(client.get("sessions", year=year, session_name="Race"),
                      key=lambda s: s["date_start"])
    rows = []
    for rnd, session in enumerate(sessions, start=1):
        key = session["session_key"]
        results = client.get("session_result", session_key=key)
        grid = client.get("starting_grid", session_key=key)
        if not results or not grid:
            print("  skip round %d (%s): no results/grid yet" % (rnd, session.get("location")))
            continue
        drivers = {d["driver_number"]: d for d in client.get("drivers", session_key=key)}
        weather = client.get("weather", session_key=key)
        temps = [w["track_temperature"] for w in weather if w.get("track_temperature") is not None]
        track = round(statistics.mean(temps), 1) if temps else ""
        rain = int(any(w.get("rainfall") for w in weather))
        grid_of = {g["driver_number"]: g["position"] for g in grid}

        for r in results:
            n = r["driver_number"]
            d = drivers.get(n, {})
            classified = not (r.get("dnf") or r.get("dns") or r.get("dsq"))
            rows.append({
                "season": year, "round": rnd,
                "driver_id": d.get("name_acronym") or str(n),
                "constructor_id": d.get("team_name") or "",
                "grid": grid_of.get(n, ""),
                "track_temperature": track, "rainfall": rain,
                "finish_position": r["position"] if classified and r.get("position") else "",
            })
    return rows


def write_csv(rows, out):
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", type=int, nargs="+", default=[2024, 2025])
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--cache", default=DEFAULT_CACHE)
    args = ap.parse_args()

    client = Client(cache_dir=args.cache)
    rows = []
    for year in args.years:
        print("season %d ..." % year)
        got = race_rows(client, year)
        print("  %d rows" % len(got))
        rows += got
    write_csv(rows, args.out)
    print("wrote %d rows to %s" % (len(rows), args.out))


if __name__ == "__main__":
    main()
