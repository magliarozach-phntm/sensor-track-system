# Railway portfolio demo

Deploy the root Dockerfile as one application service, with a separate PostgreSQL
service in the same Railway project and region. The image builds the existing
React dashboard and serves it at `/dashboard/`; REST routes and `/docs` keep their
existing paths. HTTPS pages use same-origin HTTPS and WSS connections.

## Dashboard configuration

- Builder: Dockerfile; root directory: repository root.
- Start command: leave empty to use the image command. It runs `alembic upgrade
  head`, then Uvicorn on `0.0.0.0:$PORT` with one worker.
- Pre-deploy command: empty (migrations already run at startup).
- Healthcheck path: `/ready`, which checks PostgreSQL connectivity.
- One replica. The WebSocket connection manager is in memory; multiple processes
  or replicas would require a shared message broker.
- No cron schedule or continuously running simulator service.
- Public HTTPS domain only on the app. Connect to PostgreSQL through private networking.
- Enable app Serverless for idle savings. The first visit after sleep may take longer;
  active WebSockets or database traffic can delay sleeping.

Set these application variables using Railway references (assuming the database
service is named `Postgres`):

```dotenv
DB_HOST=${{Postgres.PGHOST}}
DB_PORT=${{Postgres.PGPORT}}
DB_USER=${{Postgres.PGUSER}}
DB_PASSWORD=${{Postgres.PGPASSWORD}}
DB_NAME=${{Postgres.PGDATABASE}}
APP_ENV=production
SQL_ECHO=false
CORS_ORIGINS=[]
SENSOR_API_KEY=<generate-a-long-random-secret>
```

Same-origin dashboard requests need no CORS allowance. Keep the key server-side;
GET endpoints and the dashboard remain public, while observation uploads require
the `X-Sensor-Key` header. Production ingestion fails closed if no key is set.

## Run a demonstration

Visitors can click **Run 60-second demo** on `/dashboard/`. One shared simulator
runs inside the existing app service, posts to its loopback API, and stops after
at most 60 seconds. The ingestion key stays on the server.

The button is limited to three tracks, 30 cycles (at most 90 observations per
run), a five-minute cooldown after the run, and 12 starts per UTC day shared
across all visitors. PostgreSQL stores and locks the limit record, so concurrent
requests and app restarts cannot reset the budget. Failed starts also consume a
slot. A restart stops the current demo; the next attempt follows the saved
cooldown. These limits apply to the public button, not authenticated ingestion.

The simulator runs only when requested. There is no extra Railway service or
continuous polling when the dashboard is closed. Existing synthetic history is
retained; at maximum public usage, up to 1,080 observations are added per day.

### Owner-operated simulator

Run the simulator locally, using the dependencies in `requirements.txt`. Put
`SENSOR_API_URL=https://your-service.up.railway.app` and the private
`SENSOR_API_KEY` in your untracked `.env` file. Open `/dashboard/`, then run:

```sh
python simulator/sensor_simulator.py --cycles 30
```

This runs about one minute and exits. The original no-argument continuous mode
remains available for local development; use Ctrl+C to stop it. Saved synthetic
observations persist, and tracks become stale/dropped after simulation stops.
No automatic history deletion is configured.

## Verification and cost

Check `/health`, `/ready`, `/docs`, and `/tracks`; connect to `/ws/tracks`, run the
bounded simulator, and confirm that a `track_updated` event matches persisted
track/history data. Confirm unauthenticated observation uploads return 401.

Use Railway metrics to measure actual memory and CPU after deployment. Resource
limits are ceilings, not reservations or spending caps. This demo shares the
account's Hobby usage allowance with other projects. Avoid automatic simulation,
extra replicas, and a separate frontend container. Do not apply a workspace-wide
hard spending cutoff without considering the other hosted applications.
