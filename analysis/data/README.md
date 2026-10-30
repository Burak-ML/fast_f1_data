# Race data

`analysis/data/race_dataset.csv`: one row per driver per race.

| column | meaning |
|--------|---------|
| `season`, `round` | race identity (the last races are held out when checking accuracy) |
| `driver_id`, `constructor_id` | who drove, for which team |
| `grid` | starting grid slot |
| `track_temperature` | °C, e.g. the race-session average |
| `rainfall` | 1 if it rained during the race, else 0 |
| `finish_position` | classified finishing position (empty for DNF/DSQ: those rows are dropped) |
