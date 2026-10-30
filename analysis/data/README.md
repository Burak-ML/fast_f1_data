# Race data

`analysis/data/race_dataset.csv` is not stored in the repo; build it with one command.

## Getting the data

```bash
python -m analysis.collect --years 2024 2025
```

It reads the free [OpenF1](https://openf1.org) API (no key needed): race results, starting grid,
drivers and weather for every Race session, and writes the CSV below. The first run takes a few
minutes because the API limits request speed. Responses are cached in `analysis/data/raw/`
(git-ignored), so a stopped run resumes and a second run is instant. Sprints are not included.
Run it again after each race weekend to add the new race.

OpenF1 only holds recent seasons, so older years may come back empty.

## Format

One row per driver per race.

| column | meaning |
|--------|---------|
| `season`, `round` | race identity (`round` = order of the season's Race sessions; the last races are held out when checking accuracy) |
| `driver_id`, `constructor_id` | driver code (e.g. `VER`) and team name for that race |
| `grid` | starting grid slot |
| `track_temperature` | °C, average over the race session |
| `rainfall` | 1 if any rain was recorded during the race, else 0 |
| `finish_position` | classified finishing position (empty for DNF/DSQ: those rows are dropped) |

You can also bring your own CSV with these columns, for example exported from the PostgreSQL
tables the `worker/` fills.
