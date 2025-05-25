#!/bin/bash
# Run script for Orchestra Docker environment

# Check for Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo "Docker could not be found. Please install Docker."
    exit 1
fi

# Create necessary directories
mkdir -p ./monitoring/grafana-provisioning/datasources
mkdir -p ./monitoring/grafana-provisioning/dashboards
mkdir -p ./monitoring/metrics
mkdir -p ./tools/llm_test_server

# Create default Grafana datasource for Prometheus
cat > ./monitoring/grafana-provisioning/datasources/prometheus.yml << EOL
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://monitoring:9090
    isDefault: true
EOL

# Create default Grafana dashboard
cat > ./monitoring/grafana-provisioning/dashboards/llm_performance.json << EOL
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": 1,
  "links": [],
  "liveNow": false,
  "panels": [
    {
      "datasource": {
        "type": "prometheus",
        "uid": "PBFA97CFB590B2093"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 0,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "auto",
            "spanNulls": false,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 10
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "id": 1,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "tooltip": {
          "mode": "single",
          "sort": "none"
        }
      },
      "title": "LLM Request Latency by Provider",
      "type": "timeseries"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "PBFA97CFB590B2093"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            }
          },
          "mappings": []
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 0
      },
      "id": 2,
      "options": {
        "displayLabels": ["percent"],
        "legend": {
          "displayMode": "list",
          "placement": "right",
          "showLegend": true
        },
        "pieType": "pie",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "tooltip": {
          "mode": "single",
          "sort": "none"
        }
      },
      "title": "LLM Requests by Provider",
      "type": "piechart"
    }
  ],
  "refresh": "",
  "revision": 1,
  "schemaVersion": 39,
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-6h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "",
  "title": "LLM Performance Dashboard",
  "version": 0,
  "weekStart": ""
}
EOL

# Create dashboard provisioning config
cat > ./monitoring/grafana-provisioning/dashboards/dashboard.yml << EOL
apiVersion: 1

providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    options:
      path: /etc/grafana/provisioning/dashboards
EOL

echo "Starting Orchestra environment with Docker Compose..."

# Export environment variables from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Start the services
docker compose up -d

# Show running containers
echo "Running containers:"
docker compose ps

echo ""
echo "Access the services at:"
echo "- Orchestra API: http://localhost:8000"
echo "- Agno UI (Phidata): http://localhost:3000"
echo "- LLM Testing Service: http://localhost:8001"
echo "- Grafana Dashboards: http://localhost:3001 (admin/admin)"
echo "- Prometheus: http://localhost:9090"
echo ""
echo "To view logs, use: docker compose logs -f [service_name]"
echo "To stop all services: docker compose down"
