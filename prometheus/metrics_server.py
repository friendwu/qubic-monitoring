import os
from dotenv import load_dotenv
from qubicly import QubicClient
from flask import Flask, Response
import requests 
from prometheus_client import Gauge, generate_latest, CollectorRegistry
from qubipy.rpc import rpc_client 

app = Flask(__name__)

registry = CollectorRegistry()

qubic_node_current_tick_gauge = Gauge('qubic_node_current_tick', 'Current tick of qubic node', registry=registry)
qubic_node_current_epoch_gauge = Gauge('qubic_node_current_epoch', 'Current epoch of qubic node', registry=registry)
qubic_node_version_gauge = Gauge('qubic_node_version', 'Version of qubic node', registry=registry)
qubic_node_initial_tick_this_epoch_gauge = Gauge('qubic_node_initial_tick_this_epoch', 'Initial tick this epoch of qubic node', registry=registry)

qubic_network_current_tick_gauge = Gauge('qubic_network_current_tick', 'Current tick of qubic network', registry=registry)
qubic_network_current_epoch_gauge = Gauge('qubic_network_current_epoch', 'Current epoch of qubic network', registry=registry)
qubic_network_initial_tick_this_epoch_gauge = Gauge('qubic_network_initial_tick_this_epoch', 'Initial tick this epoch of qubic network', registry=registry)
qubic_network_version_gauge = Gauge('qubic_network_version', 'Version of qubic network', registry=registry)
qubic_network_computor_gauge = Gauge('qubic_network_computor', 'Computor of qubic network', labelnames=["epoch", "computor_id"], registry=registry)

load_dotenv()

NODE_IP = os.getenv('QUBIC_NODE_IP', '43.104.159.143')
NODE_PORT = int(os.getenv('QUBIC_NODE_PORT', '21841'))
DEBUG = os.getenv('DEBUG', 'False') == 'True'
SERVER_PORT = int(os.getenv('SERVER_PORT', '8004'))

qubic_client = QubicClient(NODE_IP, NODE_PORT)
rpc = rpc_client.QubiPy_RPC()

def get_computors(epoch: int):
    url = f"https://rpc.qubic.org/v1/epochs/{epoch}/computors"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["computors"]["identities"]
    else:
        return []
    

@app.route('/metrics')
def metrics():
    tick_info = qubic_client.get_tick_info()
    system_info = qubic_client.get_system_info()

    qubic_node_current_tick_gauge.set(tick_info.tick)
    qubic_node_current_epoch_gauge.set(tick_info.epoch)
    qubic_node_version_gauge.set(system_info.version)
    qubic_node_initial_tick_this_epoch_gauge.set(system_info.initial_tick)

    network_info = rpc.get_tick_info()

    qubic_network_current_tick_gauge.set(float(network_info.get("tick", 0)))
    qubic_network_current_epoch_gauge.set(float(network_info.get("epoch", 0)))
    qubic_network_initial_tick_this_epoch_gauge.set(float(network_info.get("initialTick", 0)))

    if network_info.get("epoch", 0) > 0:
        computors = get_computors(network_info["epoch"])
        for computor in computors:
            qubic_network_computor_gauge.labels(network_info["epoch"], computor).set(1)

    return Response(generate_latest(registry), mimetype="text/plain")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=SERVER_PORT, debug=DEBUG)
