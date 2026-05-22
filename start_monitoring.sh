#!/bin/bash
set -e

echo "=== Starting Quality Monitoring Stack ==="

pip install prometheus_client -q 2>/dev/null || true

echo "[1/3] Starting Python metrics app on port 8000..."
python app.py &
APP_PID=$!
sleep 2

echo "[2/3] Starting Prometheus on port 9000..."
prometheus \
  --config.file=prometheus.yml \
  --storage.tsdb.path=prometheus_data \
  --web.listen-address=0.0.0.0:9000 \
  --log.level=warn &
PROM_PID=$!
sleep 3

echo "[3/3] Starting Grafana on port 5000..."
GRAFANA_HOME=$(dirname $(dirname $(which grafana-server)))/share/grafana
grafana server \
  --config=/home/runner/workspace/grafana_config/grafana.ini \
  --homepath=$GRAFANA_HOME &
GRAFANA_PID=$!

echo ""
echo "=== All services started ==="
echo "Metrics App : http://localhost:8000"
echo "Prometheus  : http://localhost:9090"
echo "Grafana     : http://localhost:5000  (admin / admin123)"
echo ""

# Wait for Grafana to be ready
for i in $(seq 1 30); do
  if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "Grafana is ready!"
    break
  fi
  sleep 1
done

wait $APP_PID $PROM_PID $GRAFANA_PID
