# Training data

`python -m ml.train` reads `ml/data/race_dataset.csv`: one row per driver per race.

| column | meaning |
|--------|---------|
| `season`, `round` | race identity (used for the time-based train/test split) |
| `driver_id`, `constructor_id`, `circuit_id` | categorical features |
| `grid` | starting grid slot (qualifying position, or the real grid when known) |
| `air_temperature`, `track_temperature` | °C, e.g. the race-session average |
| `rainfall` | 1 if it rained during the race, else 0 |
| `finish_position` | classified finishing position (empty for DNF/DSQ: those rows are dropped) |
