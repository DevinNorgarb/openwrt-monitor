#!/usr/bin/env python3
"""Regenerate openwrt-router.json — run from repo root: python3 grafana-provisioning/dashboards/generate_openwrt_dashboard.py"""

from __future__ import annotations

import json
from pathlib import Path

# Provisioned datasource (see grafana-provisioning/datasources/influxdb.yml).
DS_UID = "influx-collectd"
DS = {"type": "influxdb", "uid": DS_UID}
# Dashboard UID (must differ from the datasource UID).
DASHBOARD_UID = "openwrt-router"
HOST = 'AND ("host" =~ /^$host$/)'


def tgt(q: str, ref: str, *, alias: str | None = None) -> dict:
    t: dict = {
        "datasource": DS,
        "hide": False,
        "query": q,
        "rawQuery": True,
        "refId": ref,
        "resultFormat": "time_series",
    }
    if alias:
        t["alias"] = alias
    return t


def row(title: str, y: int, pid: int) -> dict:
    return {
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y},
        "id": pid,
        "panels": [],
        "title": title,
        "type": "row",
    }


def ts_custom(
    *,
    draw: str = "line",
    fill: int = 28,
    gradient: str = "hue",
    width: float = 2,
    stacking: str = "none",
    axis: str = "auto",
) -> dict:
    return {
        "alignValue": "center",
        "axisPlacement": axis,
        "barAlignment": 0,
        "drawStyle": draw,
        "fillOpacity": fill,
        "gradientMode": gradient,
        "hideFrom": {"legend": False, "tooltip": False, "viz": False},
        "lineInterpolation": "smooth",
        "lineWidth": width,
        "pointSize": 4,
        "scaleDistribution": {"type": "linear"},
        "showPoints": "never",
        "spanNulls": False,
        "stacking": {"group": "A", "mode": stacking},
        "thresholdsStyle": {"mode": "off"},
    }


def timeseries(
    pid: int,
    title: str,
    y: int,
    h: int,
    w: int,
    x: int,
    targets: list[dict],
    *,
    description: str = "",
    unit: str | None = None,
    defaults_custom: dict | None = None,
    overrides: list | None = None,
    thresholds: dict | None = None,
    thresholds_style: str = "off",
    color_mode: str = "palette-classic",
) -> dict:
    custom = ts_custom()
    if defaults_custom:
        custom.update(defaults_custom)
    if thresholds_style != "off":
        custom["thresholdsStyle"] = {"mode": thresholds_style}

    defaults: dict = {
        "color": {"mode": color_mode},
        "custom": custom,
        "mappings": [],
        "thresholds": thresholds
        or {"mode": "absolute", "steps": [{"color": "green", "value": None}]},
    }
    if unit:
        defaults["unit"] = unit

    legend_calcs = ["min", "max", "mean", "lastNotNull", "stdDev"]

    return {
        "datasource": DS,
        "description": description,
        "fieldConfig": {"defaults": defaults, "overrides": overrides or []},
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "id": pid,
        "options": {
            "legend": {
                "calcs": legend_calcs,
                "displayMode": "table",
                "placement": "bottom",
                "showLegend": True,
                "sortBy": "Max",
                "sortDesc": True,
            },
            "tooltip": {"mode": "multi", "sort": "desc"},
        },
        "targets": targets,
        "title": title,
        "type": "timeseries",
        "pluginVersion": "11.0.0",
    }


def stat_panel(
    pid: int,
    title: str,
    y: int,
    x: int,
    w: int,
    q: str,
    *,
    unit: str | None = None,
    decimals: int | None = None,
    thresholds: dict | None = None,
    color_mode: str = "value",
    graph_mode: str = "area",
) -> dict:
    d: dict = {
        "mappings": [],
        "thresholds": thresholds
        or {"mode": "absolute", "steps": [{"color": "green", "value": None}]},
    }
    if unit:
        d["unit"] = unit
    if decimals is not None:
        d["decimals"] = decimals

    return {
        "datasource": DS,
        "fieldConfig": {"defaults": d, "overrides": []},
        "gridPos": {"h": 6, "w": w, "x": x, "y": y},
        "id": pid,
        "options": {
            "colorMode": color_mode,
            "graphMode": graph_mode,
            "justifyMode": "auto",
            "orientation": "auto",
            "reduceOptions": {
                "calcs": ["lastNotNull", "mean", "max", "min"],
                "fields": "",
                "values": False,
            },
            "textMode": "auto",
            "wideLayout": True,
        },
        "pluginVersion": "11.0.0",
        "targets": [tgt(q, "A")],
        "title": title,
        "type": "stat",
    }


def main() -> None:
    panels: list = []
    pid = 1
    y = 0

    panels.append(row("Overview", y, pid))
    pid += 1
    y += 1

    stats = [
        (
            "Thermal (last)",
            f'SELECT last("value") FROM "thermal_value" WHERE $timeFilter {HOST}',
            "celsius",
            1,
            {
                "mode": "absolute",
                "steps": [
                    {"color": "blue", "value": None},
                    {"color": "green", "value": 0},
                    {"color": "yellow", "value": 65},
                    {"color": "red", "value": 80},
                ],
            },
        ),
        (
            "Uptime",
            f'SELECT last("value") FROM "uptime_value" WHERE $timeFilter {HOST}',
            "s",
            0,
            None,
        ),
        (
            "DHCP leases",
            f'SELECT last("value") FROM "dhcpleases_value" WHERE $timeFilter {HOST}',
            "none",
            0,
            None,
        ),
        (
            "Conntrack",
            f'SELECT last("value") FROM "conntrack_value" WHERE $timeFilter {HOST}',
            "none",
            0,
            None,
        ),
        (
            "Ping (last)",
            f'SELECT last("value") FROM "ping_value" WHERE $timeFilter {HOST}',
            "ms",
            1,
            {
                "mode": "absolute",
                "steps": [
                    {"color": "green", "value": None},
                    {"color": "yellow", "value": 40},
                    {"color": "red", "value": 100},
                ],
            },
        ),
        (
            "TCP",
            f'SELECT last("value") FROM "tcpconns_value" WHERE $timeFilter {HOST}',
            "none",
            0,
            None,
        ),
    ]
    xw = 4
    for i, (title, q, unit, dec, th) in enumerate(stats):
        p = stat_panel(
            pid,
            title,
            y,
            i * xw,
            xw,
            q,
            unit=unit,
            decimals=dec,
            thresholds=th,
            graph_mode="area",
        )
        panels.append(p)
        pid += 1
    y += 6

    # Thermal history with threshold shading
    panels.append(row("Thermal", y, pid))
    pid += 1
    y += 1
    panels.append(
        timeseries(
            pid,
            "CPU / SoC temperature (with alert-style thresholds)",
            y,
            10,
            24,
            0,
            [
                tgt(
                    f'SELECT mean("value") FROM "thermal_value" WHERE $timeFilter {HOST} GROUP BY time($__interval) fill(null)',
                    "A",
                )
            ],
            description="Yellow/red bands follow panel thresholds (edit to match your silicon).",
            unit="celsius",
            thresholds={
                "mode": "absolute",
                "steps": [
                    {"color": "transparent", "value": None},
                    {"color": "rgba(255, 200, 0, 0.12)", "value": 65},
                    {"color": "rgba(255, 80, 80, 0.15)", "value": 80},
                ],
            },
            thresholds_style="line+area",
            color_mode="continuous-BlYlRd",
        )
    )
    pid += 1
    y += 10

    panels.append(row("Network", y, pid))
    pid += 1
    y += 1
    panels.append(
        timeseries(
            pid,
            "Interface traffic (B/s, rx + tx)",
            y,
            11,
            24,
            0,
            [
                # OpenWrt / many builds expose if_octets DS names as 0/1 → Telegraf split → interface_0 / interface_1.
                tgt(
                    f'SELECT non_negative_derivative(mean("value"), 1s) FROM "interface_0" WHERE $timeFilter {HOST} GROUP BY time($__interval), "instance" fill(null)',
                    "A",
                ),
                tgt(
                    f'SELECT non_negative_derivative(mean("value"), 1s) FROM "interface_1" WHERE $timeFilter {HOST} GROUP BY time($__interval), "instance" fill(null)',
                    "B",
                ),
                # Stock types.db uses rx/tx → interface_rx / interface_tx.
                tgt(
                    f'SELECT non_negative_derivative(mean("value"), 1s) FROM "interface_rx" WHERE $timeFilter {HOST} GROUP BY time($__interval), "instance" fill(null)',
                    "C",
                ),
                tgt(
                    f'SELECT non_negative_derivative(mean("value"), 1s) FROM "interface_tx" WHERE $timeFilter {HOST} GROUP BY time($__interval), "instance" fill(null)',
                    "D",
                ),
                # Join multivalue: measurement `interface`, fields rx / tx.
                tgt(
                    f'SELECT non_negative_derivative(mean("rx"), 1s) FROM "interface" WHERE $timeFilter {HOST} GROUP BY time($__interval), "instance" fill(null)',
                    "E",
                ),
                tgt(
                    f'SELECT non_negative_derivative(mean("tx"), 1s) FROM "interface" WHERE $timeFilter {HOST} GROUP BY time($__interval), "instance" fill(null)',
                    "F",
                ),
            ],
            description='Telegraf split: `{plugin}_{dsName}` + field `value` + tag `instance`. OpenWrt often yields `interface_0`/`interface_1` (octets); stock types.db uses `interface_rx`/`interface_tx`. Join mode uses measurement `interface` fields `rx`/`tx`. Hide unused series in the legend.',
            unit="Bps",
            defaults_custom={
                **ts_custom(fill=35, gradient="opacity", width=2.5),
                "thresholdsStyle": {"mode": "off"},
            },
        )
    )
    pid += 1
    y += 11
    panels.append(
        timeseries(
            pid,
            "Collectd → Telegraf (network plugin I/O)",
            y,
            9,
            24,
            0,
            [
                tgt(
                    f'SELECT non_negative_derivative(mean("value"), 1s) FROM "network_0" WHERE $timeFilter {HOST} GROUP BY time($__interval) fill(null)',
                    "A",
                ),
                tgt(
                    f'SELECT non_negative_derivative(mean("value"), 1s) FROM "network_1" WHERE $timeFilter {HOST} GROUP BY time($__interval) fill(null)',
                    "B",
                ),
            ],
            description="Counters from collectd `network` write plugin (`ReportStats`): UDP metric export volume, not LAN/WAN usage.",
            unit="Bps",
            defaults_custom=ts_custom(fill=32, gradient="hue", width=2),
        )
    )
    pid += 1
    y += 9

    panels.append(row("Reachability · latency analytics", y, pid))
    pid += 1
    y += 1
    panels.append(
        timeseries(
            pid,
            "Ping RTT — min / mean / max / p95",
            y,
            12,
            24,
            0,
            [
                tgt(
                    f'SELECT min("value") FROM "ping_value" WHERE $timeFilter {HOST} GROUP BY time($__interval) fill(null)',
                    "A",
                    alias="min",
                ),
                tgt(
                    f'SELECT mean("value") FROM "ping_value" WHERE $timeFilter {HOST} GROUP BY time($__interval) fill(null)',
                    "B",
                    alias="mean",
                ),
                tgt(
                    f'SELECT max("value") FROM "ping_value" WHERE $timeFilter {HOST} GROUP BY time($__interval) fill(null)',
                    "C",
                    alias="max",
                ),
                tgt(
                    f'SELECT percentile("value", 95) FROM "ping_value" WHERE $timeFilter {HOST} GROUP BY time($__interval) fill(null)',
                    "D",
                    alias="p95",
                ),
            ],
            description="Envelope + trend: min/max bracket, mean centerline, p95 tail latency.",
            unit="ms",
            defaults_custom=ts_custom(fill=8, gradient="opacity", width=1.5),
            overrides=[
                {
                    "matcher": {"id": "byName", "options": "min"},
                    "properties": [
                        {"id": "custom.lineStyle", "value": {"dash": [10, 10], "fill": "dot"}},
                        {"id": "custom.lineWidth", "value": 1},
                    ],
                },
                {
                    "matcher": {"id": "byName", "options": "mean"},
                    "properties": [{"id": "custom.lineWidth", "value": 2.5}],
                },
                {
                    "matcher": {"id": "byName", "options": "p95"},
                    "properties": [
                        {"id": "custom.lineStyle", "value": {"dash": [4, 4], "fill": "dot"}},
                        {"id": "custom.fillOpacity", "value": 0},
                    ],
                },
            ],
        )
    )
    pid += 1
    y += 12

    # Histogram: distribution of samples in range (Grafana buckets the series)
    panels.append(
        {
            "datasource": DS,
            "description": "Distribution of ping samples in the selected time range.",
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "palette-classic"},
                    "custom": {
                        "fillOpacity": 80,
                        "gradientMode": "hue",
                        "hideFrom": {"legend": False, "tooltip": False, "viz": False},
                        "lineWidth": 1,
                    },
                    "mappings": [],
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [{"color": "green", "value": None}],
                    },
                    "unit": "ms",
                },
                "overrides": [],
            },
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": y},
            "id": pid,
            "options": {
                "bucketOffset": 0,
                "bucketSize": 0,
                "combine": True,
                "legend": {"displayMode": "list", "placement": "bottom", "showLegend": False},
            },
            "targets": [
                tgt(
                    f'SELECT "value" FROM "ping_value" WHERE $timeFilter {HOST}',
                    "A",
                )
            ],
            "title": "Ping RTT distribution (histogram)",
            "type": "histogram",
            "pluginVersion": "11.0.0",
        }
    )
    pid += 1

    panels.append(
        timeseries(
            pid,
            "Ping — rolling mean only (large)",
            y,
            8,
            12,
            12,
            [
                tgt(
                    f'SELECT mean("value") FROM "ping_value" WHERE $timeFilter {HOST} GROUP BY time($__interval) fill(null)',
                    "A",
                )
            ],
            unit="ms",
            thresholds={
                "mode": "absolute",
                "steps": [
                    {"color": "green", "value": None},
                    {"color": "yellow", "value": 40},
                    {"color": "red", "value": 100},
                ],
            },
            thresholds_style="line+area",
            defaults_custom=ts_custom(fill=45, gradient="hue", width=3),
        )
    )
    pid += 1
    y += 8

    panels.append(row("Processes", y, pid))
    pid += 1
    y += 1
    panels.append(
        timeseries(
            pid,
            "Processes (stacked)",
            y,
            10,
            24,
            0,
            [
                tgt(
                    f'SELECT mean("value") FROM "processes_value" WHERE $timeFilter {HOST} GROUP BY time($__interval) fill(null)',
                    "A",
                ),
                tgt(
                    f'SELECT mean("value") FROM "processes_0" WHERE $timeFilter {HOST} GROUP BY time($__interval) fill(null)',
                    "B",
                ),
                tgt(
                    f'SELECT mean("value") FROM "processes_1" WHERE $timeFilter {HOST} GROUP BY time($__interval) fill(null)',
                    "C",
                ),
            ],
            description="Stacked to show composition; turn off stacking in panel if you prefer overlaid lines.",
            defaults_custom=ts_custom(fill=40, gradient="opacity", stacking="normal"),
        )
    )
    pid += 1
    y += 10

    panels.append(row("Memory & swap", y, pid))
    pid += 1
    y += 1
    panels.append(
        timeseries(
            pid,
            "Virtual memory & swap (stacked)",
            y,
            10,
            24,
            0,
            [
                tgt(
                    f'SELECT mean("value") FROM "vmem_value" WHERE $timeFilter {HOST} GROUP BY time($__interval) fill(null)',
                    "A",
                ),
                tgt(
                    f'SELECT mean("value") FROM "swap_value" WHERE $timeFilter {HOST} GROUP BY time($__interval) fill(null)',
                    "B",
                ),
            ],
            defaults_custom=ts_custom(fill=45, gradient="hue", stacking="normal"),
            unit="bytes",
        )
    )
    pid += 1
    y += 10

    panels.append(row("Connections (dual axis)", y, pid))
    pid += 1
    y += 1
    panels.append(
        timeseries(
            pid,
            "TCP sessions vs conntrack table",
            y,
            11,
            24,
            0,
            [
                tgt(
                    f'SELECT mean("value") FROM "tcpconns_value" WHERE $timeFilter {HOST} GROUP BY time($__interval) fill(null)',
                    "A",
                ),
                tgt(
                    f'SELECT mean("value") FROM "conntrack_value" WHERE $timeFilter {HOST} GROUP BY time($__interval) fill(null)',
                    "B",
                ),
            ],
            description="Left: tcpconns_value. Right: conntrack_value (often much larger).",
            defaults_custom=ts_custom(fill=28, gradient="opacity", width=2.5),
            overrides=[
                {
                    "matcher": {"id": "byRegexp", "options": "/tcpconns/"},
                    "properties": [
                        {"id": "color", "value": {"fixedColor": "semi-dark-blue", "mode": "fixed"}},
                        {"id": "custom.axisPlacement", "value": "left"},
                    ],
                },
                {
                    "matcher": {"id": "byRegexp", "options": "/conntrack/"},
                    "properties": [
                        {"id": "color", "value": {"fixedColor": "orange", "mode": "fixed"}},
                        {"id": "custom.axisPlacement", "value": "right"},
                    ],
                },
            ],
        )
    )
    pid += 1

    dashboard = {
        "annotations": {"list": []},
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 2,
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": panels,
        "refresh": "5s",
        "schemaVersion": 39,
        "style": "dark",
        "tags": ["openwrt", "collectd", "influxdb"],
        "templating": {
            "list": [
                {
                    "current": {},
                    "datasource": DS,
                    "definition": 'SHOW TAG VALUES WITH KEY = "host"',
                    "hide": 0,
                    "includeAll": True,
                    "label": "Router",
                    "multi": False,
                    "name": "host",
                    "options": [],
                    "query": 'SHOW TAG VALUES WITH KEY = "host"',
                    "refresh": 2,
                    "regex": "",
                    "skipUrlSync": False,
                    "sort": 1,
                    "type": "query",
                    "allValue": ".*",
                }
            ]
        },
        "time": {"from": "now-6h", "to": "now"},
        "timepicker": {
            "refresh_intervals": ["5s", "10s", "30s", "1m", "5m"],
            "time_options": ["5m", "15m", "1h", "6h", "12h", "24h", "2d", "7d"],
        },
        "timezone": "browser",
        "title": "OpenWrt router health",
        "uid": DASHBOARD_UID,
        "version": 4,
        "weekStart": "",
    }

    out = Path(__file__).resolve().parent / "openwrt-router.json"
    out.write_text(json.dumps(dashboard, indent=2))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
