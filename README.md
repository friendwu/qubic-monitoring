# Qubic Node Monitoring

Real-time monitoring setup for Qubic nodes using Prometheus and Grafana. Collects metrics from both local Qubic nodes and the network, providing comprehensive insights into node performance and network status.

![Grafana Dashboard](screenshot.png)

## Features

- **Node Metrics**: Current tick, epoch, version, initial tick
- **Network Metrics**: Network-wide tick/epoch information, computor tracking
- **Prometheus Integration**: Metrics exposed in Prometheus format
- **Grafana Dashboard**: Pre-configured visualization dashboard
- **Environment Configuration**: Flexible setup via environment variables

## Quick Start

### 1. Install Dependencies

```bash
cd prometheus
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file in the `prometheus/` directory:

```env
QUBIC_NODE_LIST=43.104.159.143:21841,43.104.159.144:21841,43.104.159.145:21841
SERVER_PORT=8004
DEBUG=False
```

### 3. Start Metrics Server

```bash
cd prometheus
python metrics_server.py
```

The metrics endpoint will be available at `http://localhost:8004/metrics`

### 4. Configure Prometheus

Add this job to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'qubic-node'
    static_configs:
      - targets: ['localhost:8004']
    scrape_interval: 30s
```

### 5. Import Grafana Dashboard

1. Open Grafana UI
2. Go to Dashboards → Import
3. Upload `grafana/Qubic-Node-Monitoring.json`

## Configuration

### Environment Variables

| Variable           | Default                                                      | Description                                 |
|--------------------|--------------------------------------------------------------|---------------------------------------------|
| `QUBIC_NODE_LIST`  | `43.104.159.143:21841,43.104.159.144:21841,43.104.159.145:21841` | Comma-separated list of Qubic node IP:port pairs |
| `SERVER_PORT`      | `8004`                                                       | Port for metrics server                     |
| `DEBUG`            | `False`                                                      | Enable debug mode                           |

### Metrics Collected

#### Node Metrics
- `qubic_node_current_tick`: Current tick of the monitored node (labeled by `node_addr`)
- `qubic_node_current_epoch`: Current epoch of the monitored node (labeled by `node_addr`)
- `qubic_node_version`: Version of the monitored node (labeled by `node_addr`)
- `qubic_node_initial_tick_this_epoch`: Initial tick of current epoch for the monitored node (labeled by `node_addr`)

#### Network Metrics
- `qubic_network_current_tick`: Current tick of the Qubic network
- `qubic_network_current_epoch`: Current epoch of the Qubic network
- `qubic_network_initial_tick_this_epoch`: Initial tick of current network epoch
- `qubic_network_computor`: Computor presence in the network, labeled by `epoch` and `computor_id`

## Development

### Dependencies

- **qubicly**: Qubic node client library
- **flask**: Web framework for metrics endpoint
- **prometheus_client**: Prometheus metrics generation
- **python-dotenv**: Environment variable management

### Running in Development

```bash
export DEBUG=True
python metrics_server.py
```

## Production Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY prometheus/ .
RUN pip install -r requirements.txt

EXPOSE 8004
CMD ["python", "metrics_server.py"]
```

### Systemd Service

```ini
[Unit]
Description=Qubic Metrics Server
After=network.target

[Service]
Type=simple
User=qubic
WorkingDirectory=/opt/qubic-monitoring/prometheus
ExecStart=/usr/bin/python3 metrics_server.py
Restart=always
EnvironmentFile=/opt/qubic-monitoring/.env

[Install]
WantedBy=multi-user.target
```


