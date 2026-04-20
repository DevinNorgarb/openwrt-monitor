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

1. Copy the repo’s `collectd.conf` to the router as **`/etc/collectd.conf`** (this is the main collectd config path on OpenWrt).
2. Edit the **network** block so `IP_OF_TELEGRAF` is the LAN-reachable IP of the host where Docker (and Telegraf) is running:

```text
	Server "IP_OF_TELEGRAF" "25826" # Telegraf IP
	Forward true
```

Those lines belong inside `<Plugin network> … </Plugin>` (see the full example in `collectd.conf` in this repo).

3. Enable collectd (often via **LuCI → Statistics → collectd**) or restart the service so the new config is loaded. Metrics are sent to Telegraf on **UDP 25826**.

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

## Dashboard looks unchanged or panels show “No data”

1. **Use the provisioned dashboard** — open **OpenWrt router health** with UID **`openwrt-router`**. Remove any older copy you imported manually (same title, old queries).
2. **Reload provisioning** — after changing JSON under `grafana-provisioning/`, run `docker compose restart grafana` (or wait for the next provision cycle). This repo sets **`allowUiUpdates: false`** so file updates are not overridden by an old UI-saved dashboard.
3. **Confirm Telegraf is writing interface metrics** — with the stack up and the router sending collectd data:

   ```bash
   curl -sG 'http://localhost:8086/query' --data-urlencode 'db=collectd' \
     --data-urlencode 'q=SHOW MEASUREMENTS' | tr ',' '\n' | grep -E 'interface|network_'
   ```

   With **`collectd_parse_multivalue = "split"`** (in `telegraf.conf`), interface octets usually appear as **`interface_0`** / **`interface_1`** (OpenWrt-style DS names) or **`interface_rx`** / **`interface_tx`** (stock `types.db`). The dashboard queries both, plus join-mode `interface` (`rx`/`tx`). Use **`SHOW MEASUREMENTS`** on your host to see which names you actually have.
4. **Router** — ensure collectd is using an `interface` / `LoadPlugin network` config that actually emits counters (see `collectd.conf` in this repo) and that UDP **25826** reaches the Telegraf host.
