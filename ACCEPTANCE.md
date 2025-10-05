## Acceptance Criteria

- **All backend tests pass**
  - Pass: Running tests completes with all green.
  - Fail: Any test fails or errors.

- **/v1/analyze returns required JSON shape**
  - Pass: Calling `/v1/analyze` responds 200 with JSON containing keys: `entities`, `sentiment`, `urgency`, `risk_percent`.
  - Fail: Non-200 response, missing any required key, or invalid JSON.

- **Docker Compose starts all services and the frontend loads**
  - Pass: `docker compose up -d` starts services without crash loops; visiting the frontend (e.g., `http://localhost:3000`) loads the app UI.
  - Fail: Any service fails to start or the frontend is not reachable.

- **Basic user can add a ticker to watchlist and see risk timeseries**
  - Pass: From the UI, a basic user adds a ticker to their watchlist and a risk timeseries chart renders for that ticker.
  - Fail: Cannot add to watchlist, or the timeseries does not appear.

- **Backtest script runs and produces CSV/plot for a sample ticker**
  - Pass: Running the demo backtest produces at least a CSV and a plot artifact for a sample ticker (e.g., in `backend/backtest_reports/`).
  - Fail: Script errors or no artifacts are produced.


