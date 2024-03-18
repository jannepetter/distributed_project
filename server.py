"""
Server functions.
"""
import os
from flask import Flask
import requests  # pylint: disable=E0401

app = Flask(__name__)

port = int(os.environ.get("PORT", 5000))
name = os.environ.get("NAME")


def _is_prime(num):
    num = int(num)
    if num <= 1:
        return False

    for i in range(2, num):
        if num % i == 0:
            return False

    return True


def notify_loadbalancer():
    """
    Notifies the loadbalancer this server is up.
    """
    try:
        load_balancer_url = "http://my_loadbalancer:9000/server_up"
        response = requests.post(
            load_balancer_url,
            json={
                "url": f"http://{name}:{port}/"
            },
            timeout=10
        )
        if response.status_code == 200:
            return True

        return False
    except Exception as e:  # pylint: disable=W0718
        print("exeption", e)
        return False


@app.route('/health_check')
def health_check():
    """
    For loadbalancer to check server is ok.
    """
    return "ok"


@app.route('/is_prime/<num>')
def is_prime(num):
    """
    The endpoint.
    """

    if _is_prime(num):
        return "yes"

    return "no"


if __name__ == '__main__':
    print("started server", name, port)
    notify_loadbalancer()
    app.run(host=name, port=port, debug=True)
