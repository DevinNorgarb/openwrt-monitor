#!/usr/bin/env bash
set -e

echo "🚀 Installing OpenWrt Monitoring Stack (Single Directory Layout)"

BASE="./openwrt-monitoring"
mkdir -p "$BASE/influxdb"
mkdir -p "$BASE/grafana"

cd "$BASE"

#####################################
# Docker install if missing
#####################################
if ! command -v docker &> /dev/null; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
fi

#####################################
# Compose plugin if missing
#####################################
if ! docker compose version &> /dev/null; then
  apt-get update -y || true
  apt-get install -y docker-compose-plugin || true
fi

#####################################
# Compose file
#####################################
cat > docker-compose.yml << "EOC"
version: "3.8"

services:

  influxdb:
    image: influxdb:1.8
    container_name: influxdb
    restart: unless-stopped
    ports:
      - "8086:8086"
      - "25826:25826/udp"
    environment:
      - INFLUXDB_DB=collectd
      - INFLUXDB_HTTP_AUTH_ENABLED=false
    volumes:
      - ./influxdb:/var/lib/influxdb

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./grafana:/var/lib/grafana
    depends_on:
      - influxdb

EOC

#####################################
# Start stack
#####################################
docker compose up -d

echo ""
echo "✅ DONE"
echo "Grafana: http://localhost:3000"
echo "InfluxDB: http://localhost:8086"
echo ""
echo "📁 Data lives in:"
echo "$BASE"
