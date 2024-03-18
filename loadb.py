"""
Load balancer.
"""
import threading
import time
from flask import Flask, request
import requests  # pylint: disable=E0401


lb = Flask(__name__)

available_servers = {}
current_index = 0  # pylint: disable=C0103


def get_oldest():
    """
    Get the oldest server address, time combination.
    """
    if len(available_servers.keys()) == 0:
        return None, None

    min = (9999999999999, None)
    key = None
    for k, v in available_servers.items():
        if v[0] < min[0]:
            min = v
            key = k

    return key, min


def periodic_health_check():
    """
    If last request to server is greater than threshold, make a healthcheck.
    """
    threshold = 4
    while True:
        server_address, value = get_oldest()
        last_time = None
        if value:
            last_time, _ = value
        now = time.time()

        if server_address and last_time and ((now-last_time) > threshold):
            try:
                response = requests.get(
                    server_address+"health_check", timeout=2)

                if response.status_code == 200:
                    # update the timestamp on available server
                    available_servers[server_address] = (time.time(), True)
                else:
                    available_servers[server_address] = (time.time(), False)

            except Exception:  # pylint: disable=W0718
                available_servers[server_address] = (time.time(), False)

        time.sleep(1)


# Separate thread for health check. Daemon ends the thread when exiting.
health_check_thread = threading.Thread(target=periodic_health_check)
health_check_thread.daemon = True
health_check_thread.start()


def get_next_address():
    """
    Get next server address.
    """
    address_list = [k for k, v in available_servers.items() if v[1]]
    if len(address_list) == 0:
        return None
    global current_index  # pylint: disable=W0603
    current_index = (current_index + 1) % len(address_list)
    return address_list[current_index]


@lb.route("/server_up", methods=["POST"])
def server_up():
    """
    Endpoint for servers to notify they are ready to accept traffic from load balancer.
    """
    data = request.json
    server_url = data.get("url", None)
    if server_url:
        available_servers[server_url] = (time.time(), True)
    return "ok"


@lb.route("/<path:path>",)
def handle_request(path):
    """
    Loadbalancer handle request to actual servers.
    """
    server_address = get_next_address()

    if not server_address:
        return "no servers currently available", 503

    try:
        response = requests.request(
            request.method,
            server_address+path,
            headers=request.headers,
            timeout=60
        )
        available_servers[server_address] = (time.time(), True)
        return response.content, response.status_code
    except Exception as e:  # pylint: disable=W0718
        lb.logger.error("handle request error", exc_info=e)
        available_servers[server_address] = (time.time(), False)
        return "request failed", 503


if __name__ == "__main__":
    lb.run(host="my_loadbalancer", port=9000, debug=True)
