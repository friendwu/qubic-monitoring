import os
from dotenv import load_dotenv
from qubicly import QubicClient
from flask import Flask, Response
import requests
from prometheus_client import Gauge, generate_latest, CollectorRegistry

app = Flask(__name__)
load_dotenv()

def parse_node_list(env_var):
    val = os.getenv(env_var)
    if val:
        nodes = []
        for entry in val.split(","):
            ip_port = entry.strip().split(":")
            if len(ip_port) == 2:
                ip, port = ip_port
                nodes.append((ip, int(port)))
        if len(nodes) == 0:
            raise Exception(f"Error getting node list: {env_var} is not set")
        return nodes
    else:
        raise Exception(f"Error getting node list: {env_var} is not set")
    
NODE_LIST = parse_node_list('QUBIC_NODE_LIST')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
SERVER_PORT = int(os.getenv('SERVER_PORT', '8004'))


def get_network_computors(epoch: int):
    url = f"https://rpc.qubic.org/v1/epochs/{epoch}/computors"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        return response.json()["computors"]["identities"]
    else:
        return []


def get_network_tick_info():
    url = f"https://rpc.qubic.org/v1/tick-info"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        return response.json()["tickInfo"]
    else:
        raise Exception(f"Error getting network tick info: {response.status_code}")


@app.route('/metrics')
def metrics():
    registry = CollectorRegistry()

    qubic_node_current_tick_gauge = Gauge('qubic_node_current_tick', 'Current tick of qubic node', labelnames=["node_addr"], registry=registry)
    qubic_node_current_epoch_gauge = Gauge('qubic_node_current_epoch', 'Current epoch of qubic node', labelnames=["node_addr"],registry=registry)
    qubic_node_version_gauge = Gauge('qubic_node_version', 'Version of qubic node', labelnames=["node_addr"],registry=registry)
    qubic_node_initial_tick_this_epoch_gauge = Gauge('qubic_node_initial_tick_this_epoch', 'Initial tick this epoch of qubic node', labelnames=["node_addr"],registry=registry)

    qubic_network_current_tick_gauge = Gauge('qubic_network_current_tick', 'Current tick of qubic network', registry=registry)
    qubic_network_current_epoch_gauge = Gauge('qubic_network_current_epoch', 'Current epoch of qubic network', registry=registry)
    qubic_network_initial_tick_this_epoch_gauge = Gauge('qubic_network_initial_tick_this_epoch', 'Initial tick this epoch of qubic network', registry=registry)
    qubic_network_version_gauge = Gauge('qubic_network_version', 'Version of qubic network', registry=registry)
    qubic_network_computor_gauge = Gauge('qubic_network_computor', 'Computor of qubic network', labelnames=["epoch", "computor_id"], registry=registry)

    for (node_ip, node_port) in NODE_LIST:
        node_addr = f"{node_ip}:{node_port}"
        try:
            qubic_client = QubicClient(node_ip, node_port)
            tick_info = qubic_client.get_tick_info()
            system_info = qubic_client.get_system_info()

            qubic_node_current_tick_gauge.labels(node_addr).set(tick_info.tick)
            qubic_node_current_epoch_gauge.labels(node_addr).set(tick_info.epoch)
            qubic_node_version_gauge.labels(node_addr).set(system_info.version)
            qubic_node_initial_tick_this_epoch_gauge.labels(node_addr).set(system_info.initial_tick)
        except Exception as e:
            print(f"failed to fetch node info: {node_addr}, {e}")
            continue
        finally:
            qubic_client.close()

    try:
        network_info = get_network_tick_info()

        qubic_network_current_tick_gauge.set(float(network_info.get("tick", 0)))
        qubic_network_current_epoch_gauge.set(float(network_info.get("epoch", 0)))
        qubic_network_initial_tick_this_epoch_gauge.set(float(network_info.get("initialTick", 0)))

        if network_info.get("epoch", 0) > 0:
            computors = get_network_computors(network_info["epoch"])
            for computor in computors:
                qubic_network_computor_gauge.labels(network_info["epoch"], computor).set(1)
    except Exception as e:
        print(f"failed to fetch network info: {e}")

    return Response(generate_latest(registry), mimetype="text/plain")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=SERVER_PORT, debug=DEBUG)
