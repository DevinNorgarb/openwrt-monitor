#!/usr/bin/env python3
"""
Delete Grafana dashboards that look like OpenWrt copies (by tag or title).

Usage (defaults match docker-compose in this repo):
  export GRAFANA_URL=http://localhost:3000   # optional
  export GRAFANA_USER=admin GRAFANA_PASSWORD=admin   # optional
  python3 scripts/delete-grafana-openwrt-dashboards.py

Note: Dashboards loaded from file provisioning will be recreated on the next
provision cycle unless you remove/rename the JSON under grafana-provisioning/.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def main() -> int:
    base = os.environ.get("GRAFANA_URL", "http://localhost:3000").rstrip("/")
    user = os.environ.get("GRAFANA_USER", "admin")
    password = os.environ.get("GRAFANA_PASSWORD", "admin")

    auth = base64.b64encode(f"{user}:{password}".encode()).decode()

    def request_json(method: str, path: str) -> object | None:
        url = base + path
        req = urllib.request.Request(url, method=method)
        req.add_header("Authorization", f"Basic {auth}")
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode()
                if not body.strip():
                    return None
                return json.loads(body)
        except urllib.error.HTTPError as e:
            err = e.read().decode() if e.fp else str(e)
            print(f"HTTP {e.code} for {path}: {err}", file=sys.stderr)
            raise
        except urllib.error.URLError as e:
            print(f"Cannot reach Grafana at {base!r}: {e.reason}", file=sys.stderr)
            raise SystemExit(2) from e

    hits: dict[str, dict] = {}

    def merge_search(params: dict[str, str]) -> None:
        qs = urllib.parse.urlencode(params)
        data = request_json("GET", f"/api/search?{qs}")
        if not isinstance(data, list):
            return
        for item in data:
            uid = item.get("uid")
            if isinstance(uid, str) and uid:
                hits[uid] = item

    merge_search({"type": "dash-db", "tag": "openwrt"})
    merge_search({"type": "dash-db", "query": "OpenWrt"})
    merge_search({"type": "dash-db", "query": "openwrt"})

    # Title filter (search API can return unrelated hits).
    selected: list[tuple[str, str]] = []
    for uid, item in hits.items():
        title = (item.get("title") or "").lower()
        uri = (item.get("uri") or "").lower()
        tags = [str(t).lower() for t in (item.get("tags") or []) if t is not None]
        if "openwrt" in tags or "openwrt" in title or "openwrt" in uri:
            selected.append((uid, item.get("title") or uid))

    if not selected:
        print("No OpenWrt-related dashboards found (tag/title/uri).", file=sys.stderr)
        return 1

    for uid, title in selected:
        request_json("DELETE", f"/api/dashboards/uid/{urllib.parse.quote(uid)}")
        print(f"Deleted: {title!r} (uid={uid})")

    print(f"Done. Removed {len(selected)} dashboard(s).", file=sys.stderr)
    print(
        "If any were file-provisioned from this repo, Grafana will re-add them "
        "from grafana-provisioning/dashboards/ on the next provision cycle.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
