## Learned User Preferences

- Keep the repo `collectd.conf` Telegraf destination as a placeholder (for example `IP_OF_TELEGRAF`) instead of committing real server addresses in version control.
- OpenWrt setup docs should state copying this repo’s `collectd.conf` to `/etc/collectd.conf` and document the `<Plugin network>` `Server` / `Forward` lines next to that path.

## Learned Workspace Facts

- Stack: OpenWrt collectd sends metrics over UDP 25826 to Telegraf, which writes InfluxDB 1.x database `collectd`, and Grafana reads that data; key files are `docker-compose.yml`, `telegraf.conf`, `collectd.conf`, and `grafana-provisioning/`.
- Grafana’s provisioned Influx datasource UID is `influx-collectd`; the router dashboard UID is `openwrt-router` and should remain different from the datasource UID.
- With Telegraf’s default collectd multivalue split layout, measurements follow `{plugin}_{dataSource}` with field `value`; per-interface traffic uses `interface_rx` / `interface_tx` grouped by tag `instance` (netdev name).
- Collectd `network_0` / `network_1` track the collectd network write plugin export counters (metric forwarding volume), not general WAN/LAN throughput; prefer interface octet series for link usage.
- DHCP lease counts from collectd `dhcpleases` appear as `dhcpleases_value`; `users_value` reflects logged-in UNIX users, not LAN client count.
- Typical OpenWrt AP interface names from `iw dev` are `phy0-ap0` and `phy1-ap0`; use those in `iwinfo`, `interface`, `dns`, and `netlink` selections when you need explicit AP VIFs.
- Treat the root `docker-compose.yml` as the canonical Compose stack for this repository; the compose embedded in `install-openwrt-monitoring.sh` is a different layout.
- Create local `influxdb` and `grafana` directories before the first `docker compose up` so bind mounts exist; the Compose file intentionally omits obsolete top-level `version`.
