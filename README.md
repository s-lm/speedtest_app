# speedtest_app

A small Flask web app that runs [`speedtest-cli`](https://github.com/sivel/speedtest-cli)
on a schedule (every 8 hours, at :15) and stores the results in PostgreSQL. It
exposes a JSON API and a single-page dashboard, with optional OIDC authentication
in front of every route.

The image is built and published to
[GitHub Container Registry (GHCR)](https://ghcr.io) via GitHub Actions.

## ✨ Features

- Scheduled download/upload/ping measurements (APScheduler, every 8h at :15)
- Single-page dashboard (Chart.js) with light/dark theme
- **By-month** view plus **rolling windows** (last 7 / 30 / 90 days)
- Summary cards: latest, median, min/max, p5–p95
- Optional **"% of plan"** lines from your advertised ISP speed
- **Pinnable test server(s)** to keep results comparable run-to-run
- Server-change markers on the x-axis, failure logging, and a freshness/reliability badge
- Manual **"Run test now"** button and **CSV/JSON export** of any period
- Optional OIDC authentication gating all routes

## 🚀 Quick start

### Pull the image from GHCR

```bash
docker pull ghcr.io/s-lm/speedtest_app:latest
```

### Run with Docker Compose

```bash
cp conf/.env.example conf/.env   # fill in values
docker compose up --build
```

The container serves on **port 8080** via gunicorn. `conf/speedtest.cfg` is
bind-mounted read-only, and `conf/.env` is loaded as the environment.

### Run locally (dev)

```bash
cp conf/.env.example conf/.env   # fill in values

# Initialize the database (creates tables)
FLASK_DEBUG=1 SPEEDTEST_SETTINGS=$PWD/conf/speedtest.cfg FLASK_APP=speedtest_app flask database_init

# Run the dev server
FLASK_DEBUG=1 SPEEDTEST_SETTINGS=$PWD/conf/speedtest.cfg FLASK_APP=speedtest_app flask run

# Drop and recreate tables
flask database_init -d
```

## ⚙️ Configuration

Configuration is layered: Flask defaults → built-in defaults → the file pointed
to by **`SPEEDTEST_SETTINGS`** (`conf/speedtest.cfg`). That cfg file is plain
Python, and most values read from environment variables, so in practice you set
things in **`conf/.env`** (copied from `conf/.env.example`) and leave the cfg
file alone.

### General

| Setting | Env var | Default | Description |
| --- | --- | --- | --- |
| `SECRET_KEY` | `FLASK_SECRET_KEY` | `insecure-dev-secret` | Flask session secret. **Set this in production.** |
| `LOGLEVEL` | — | `debug` | Logging level (`debug`, `info`, `warning`, …). |
| `LOGFORMAT` | — | see cfg | Python logging format string. |
| `ENABLE_TRACE_REQUEST_HDR` | — | `False` | Log incoming request headers (debugging). |

### Speedtest

| Setting | Env var | Default | Description |
| --- | --- | --- | --- |
| `SPEEDTEST_SERVER_IDS` | `SPEEDTEST_SERVER_IDS` | _(empty)_ | Pin specific speedtest.net server IDs so every run uses the same server(s) instead of auto-picking the "best" one (which makes results jump around). Comma/space separated, e.g. `1234,5678`. Empty = auto-select. Find IDs with `speedtest-cli --list`. |
| `PLAN_DOWNLOAD` | `PLAN_DOWNLOAD` | `0` | Advertised download speed in Mbit/s. Shows a "% of plan" line on the dashboard. `0` disables it. |
| `PLAN_UPLOAD` | `PLAN_UPLOAD` | `0` | Advertised upload speed in Mbit/s. `0` disables it. |

### Database

| Setting | Env var | Default | Description |
| --- | --- | --- | --- |
| `DB_USER` | `DB_USER` | `postgres` | PostgreSQL user. |
| `DB_PASSWORD` | `DB_PASSWORD` | `changeme` | PostgreSQL password. |
| `DB_NAME` | `DB_NAME` | `speedtest` | Database name. |
| `DB_HOST` | `DB_HOST` | `localhost` | Database host. |
| `DB_PORT` | `DB_PORT` | `5432` | Database port. |
| `DB_CREATE_DB` | — | `True` | Auto-create tables on startup. Handy in dev; **turn off in prod** and use `flask database_init`. |

### Authentication (OIDC)

Optional. When `ENABLE_OIDC = False` (the default) auth is disabled entirely and
all routes are open.

| Setting | Env var | Default | Description |
| --- | --- | --- | --- |
| `ENABLE_OIDC` | — | `False` | Gate every route behind the OIDC authorization-code flow. |
| `OIDC_CLIENT_ID` | `OIDC_CLIENT_ID` | — | OIDC client ID. |
| `OIDC_CLIENT_SECRET` | `OIDC_CLIENT_SECRET` | — | OIDC client secret. |
| `OIDC_AUTHORITY` | `OIDC_AUTHORITY` | — | OIDC provider base URL. |
| `OIDC_REDIRECT_URI` | `OIDC_REDIRECT_URI` | — | Callback URL, e.g. `https://your-app/auth/callback`. |

## 🔌 API

All routes are gated by OIDC when it is enabled.

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/` | Dashboard (single-page UI). |
| `GET` | `/api/data?year=&month=&days=` | Speedtest results as JSON. `days` (rolling window) takes precedence over `year`/`month`. |
| `GET` | `/api/years_months` | `{year: [months]}` for the filter dropdowns. |
| `GET` | `/api/status` | Freshness/reliability summary (last test, failures). |
| `POST` | `/api/run` | Trigger a test immediately (runs ~30s; returns `409` if one is already running). |
| `GET` | `/api/export?year=&month=&days=&format=csv\|json` | Download a period as CSV or JSON. |
| `GET` | `/auth/login`, `/auth/callback`, `/auth/logout` | OIDC flow. |

## 🗓️ Schedule

A background APScheduler job runs a speedtest every 8 hours at minute 15
(`hour="*/8", minute="15"`). Failed runs are recorded in a `speedtest_failure`
table and surfaced in the dashboard's reliability badge. Use the **Run test now**
button to trigger an on-demand measurement.
