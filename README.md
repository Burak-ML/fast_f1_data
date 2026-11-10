# F1 Data Analysis

**A Formula 1 analytics pipeline and dashboard for driver, team, circuit and race-performance comparisons.**

Structured 2024–2025 session data flows through PostgreSQL and FastAPI into a React interface. The repository also explores an explainable, statistics-based finishing-position estimate—not a trained machine-learning model.

**Explore:** [Features](#features) · [Architecture](#architecture) · [Setup](#getting-started) · [Limitations](#current-limitations)

Race results, lap times, pit stops and weather live in separate tables. This project brings them together behind one API so drivers, teams and circuits can be compared in an interactive interface. It also includes a small statistical module that estimates where a driver is likely to finish.

## Features

- **Driver analysis:** performance ranking (wins, podiums, DNF rate), average lap time, sector times, consistency, pit stops and positions gained or lost.
- **Team analysis:** performance ranking and driver-pair consistency.
- **Circuit and season views:** per-circuit performance, race results and strategy, championship progress.
- **Efficient queries:** per-season tables are combined with parameterized `UNION ALL` queries, results are paginated (`limit` / `offset`) and connections are pooled, so the browser never receives more data than it shows.
- **Race position estimate:** a statistics-based estimate from grid slot, driver, team and weather (see below).

## Architecture

```
OpenF1 data (JSON)
      |
   worker/   collectors, loaders, cleaning
      |
 PostgreSQL  results_*, laps_*, pit_stops_*, weather_* ... per season
      |
 FastAPI     backend/app, parameterized SQL via SQLAlchemy
      |
 React       frontend/ (Vite, TypeScript, Tailwind, Recharts)
```

The database schema is in [`database/schema.sql`](database/schema.sql). Tables are split by season (2024, 2025) and by session type (race, practice).

## Getting started

Requirements: Python 3.10+, Node.js 18+ and a PostgreSQL database.

### 1. Database and data

```bash
cd worker
cp .env.example .env              # set DATABASE_URL
cd ../database && python init_db.py   # creates the tables from schema.sql
cd .. && python -m worker.main    # loads, cleans and summarizes the data
```

`DATABASE_URL` takes the form `postgresql://USER:PASSWORD@HOST:5432/DATABASE`. The loader reads OpenF1 JSON files from an `f1_data/` directory. Downloading those files is not part of this repository yet.

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env              # set DATABASE_URL
cd .. && uvicorn backend.app.main:app --reload
```

Interactive API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Set `VITE_API_URL` if the backend is not on `http://localhost:8000`.

## API

| Endpoint | Description |
|----------|-------------|
| `GET /health` | PostgreSQL connection check |
| `GET /analysis/driver/performance-ranking` | Wins, podiums and DNF rate per driver |
| `GET /analysis/driver/average-lap-time` | Average lap time by driver and circuit |
| `GET /analysis/driver/sector-analysis` | Sector times |
| `GET /analysis/driver/consistency` | Lap-time consistency |
| `GET /analysis/driver/pit-stop-analysis` | Pit stop durations |
| `GET /analysis/driver/position-changes` | Positions gained or lost |
| `GET /analysis/team/performance-ranking` | Team ranking |
| `GET /analysis/team/consistency` | Driver-pair comparison |
| `GET /analysis/circuit/performance` | Performance by circuit |
| `GET /analysis/race/results` | Race results |
| `GET /analysis/race/strategy` | Race strategy |
| `GET /analysis/season/championship` | Championship progress |
| `GET /predict/options`, `POST /predict` | Race position estimate |

Most analysis endpoints accept `season`, `driver_id` or `driver_number`, `constructor_id`, `circuit_id`, `limit` and `offset`.

## Race position estimate

Pick a driver, a starting position, the track temperature and whether it rains, and the app estimates the finishing position. No model is trained. The estimate is built from historical averages and shows how it was put together:

```
estimate = usual finish from this grid slot (dry races)
         + what the team usually gains or loses
         + what the driver adds on top of the team
         + how rain or a hot track shuffles the order toward the middle
```

Every effect is shrunk toward zero when it rests on few races. To check accuracy, the latest races are held out, estimated from the earlier ones and compared with the baseline "a driver finishes where they start". Safety cars and retirements cannot be predicted.

```bash
python -m analysis.collect --years 2024 2025   # download results, grid and weather from OpenF1
python -m analysis.report                      # accuracy on held-out races
python -m pytest test_ml.py test_collect.py    # tests (synthetic data)
```

Data format and sources: [`analysis/data/README.md`](analysis/data/README.md).

## Current limitations

- The "Win Probability" card and the telemetry chart on the dashboard use placeholder data and do not read from the database.
- The step that downloads raw OpenF1 JSON into `f1_data/` is not included in the worker.
- Analysis covers the 2024 and 2025 seasons only.

## Project structure

```
backend/app/       FastAPI app, routes and analysis service
worker/            collectors, loaders and cleaning for OpenF1 data
database/          schema.sql and init_db.py
analysis/          statistics-based race position estimate and data collector
frontend/src/      React pages, dashboard components and API services
test_backend.py    backend checks
test_ml.py, test_collect.py   tests for the estimate and the collector
```

## Security

All SQL uses parameterized queries. Credentials are read from environment variables, so keep `.env` files out of version control (they are git-ignored).

## License

MIT. See [LICENSE](LICENSE).
