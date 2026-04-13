# OpenWrt monitoring stack

Docker Compose stack that receives **collectd** metrics from OpenWrt over UDP, stores them in **InfluxDB 1.8**, and visualizes them in **Grafana**. **Telegraf** listens for collectd network payloads and writes to InfluxDB.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with the Compose plugin (`docker compose version`)

## Quick start

From this directory:

```bash
mkdir -p influxdb grafana
docker compose up -d
```

- **Grafana:** http://localhost:3000 — default login `admin` / `admin` (change this before exposing the host to a network you do not trust).
- **InfluxDB HTTP:** http://localhost:8086 — database `collectd` (created by the InfluxDB image from `INFLUXDB_DB`).
- **collectd receiver (Telegraf):** UDP **25826** on the Docker host — point OpenWrt collectd’s network output here.

Check configuration without starting containers:

```bash
docker compose config
```

Stop the stack:

```bash
docker compose down
```

## OpenWrt

Enable collectd (often via **LuCI → Statistics → collectd**) and configure the **network** plugin (or equivalent) to send to the IP of the machine running Docker, port **25826**, protocol **UDP**. The exact menu names depend on your OpenWrt image and packages.

Telegraf is configured in `telegraf.conf` to accept collectd on port 25826 and write to the `collectd` database in InfluxDB.

## Grafana data source

Add an **InfluxDB** data source in Grafana:

- URL: `http://influxdb:8086` (from inside the Compose network) or `http://localhost:8086` if you configure Grafana outside this stack.
- Database: `collectd`
- Auth: off for the default Compose settings (`INFLUXDB_HTTP_AUTH_ENABLED=false`).

## Data on disk

InfluxDB and Grafana persist to `./influxdb` and `./grafana` via bind mounts. Contents of those directories are listed in `.gitignore` so runtime data is not committed; create the directories locally before the first `docker compose up`.

## Optional: Linux install script

`install-openwrt-monitoring.sh` is aimed at a Debian-style host: it installs Docker if needed, writes a compose file under `./openwrt-monitoring`, and starts the stack. That embedded compose is **not** the same as the root `docker-compose.yml` in this repo (this repo includes Telegraf and a different layout). Prefer the root `docker-compose.yml` when working from this repository.

## Verification

This stack was checked with:

- `docker compose config` — valid Compose file
- `docker compose up -d` — all services start; InfluxDB responds to `GET /ping`, Grafana to `GET /api/health`, Telegraf logs show `socket_listener` listening on UDP 25826
