"""
Test script.
"""

import subprocess
import time
import threading
import requests

COPY_LOGS = False

# if bombing the servers with much higher prime numbers, you probably need to increase
# timeout limit in loadbalancer or add more servers.
# Otherwise the requests get timed out

URL = "http://127.0.0.1:9000/is_prime/524287"   # around 50ms per request


result_list = []


def do_requests():
    """
    Do some requests.
    """
    total_time = 0
    request_count = 0

    for _ in range(10):
        start_time = time.time()
        response = requests.get(URL)  # pylint: disable=W3101
        if response.status_code == 200:
            end_time = time.time()
            time_used = end_time-start_time
            total_time += time_used
            request_count += 1
        else:
            end_time = time.time()
            time_used = end_time-start_time
            request_count += 1
            break

    result_list.append((total_time, request_count))


def calculate_results(results):
    """
    Test results
    """
    total_time = 0
    number_of_requests = 0
    for time_sum, count in results:
        total_time += time_sum/count
        number_of_requests += count

    print("Avg time per request: ", total_time/len(results))
    print("Successful requests : ", number_of_requests)
    return number_of_requests


def start_tests(amount_of_users, info):
    """
    The actual tests.
    """
    threads = []
    print(info)
    print(
        f"Creating {amount_of_users} users threads. Each will do 10 requests")
    print()
    start_time = time.time()
    for _ in range(amount_of_users):
        my_thread = threading.Thread(target=do_requests)
        my_thread.start()
        threads.append(my_thread)

    # wait until all finished
    for thread in threads:
        thread.join()
    end_time = time.time()
    num_of_requests = calculate_results(result_list)
    test_time = end_time-start_time
    print(f"Test took {test_time} seconds.")
    print("Requests per second: ", num_of_requests/(test_time))
    print()
    print("====")
    print()


def copy_logs(container_name, filename):
    """
    Copy logs.
    """
    try:
        logs_process = subprocess.Popen(
            ["docker", "logs", container_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        with open(filename, "wb") as f:
            for line in logs_process.stdout:
                f.write(line)

        print("Logs copied.")
    except Exception as e:  # pylint: disable=W0718
        print("Error:", e)


SLEEP_TIME = 15
AMOUNT_OF_THREADS = 50

print("=================Starting the tests===============")
start_tests(AMOUNT_OF_THREADS, "Phase 1 - Using 2 servers")

print("stopping server2")
subprocess.run(["docker", "stop", "server2"], check=True)

result_list = []
time.sleep(SLEEP_TIME)
start_tests(AMOUNT_OF_THREADS,
            "Phase 2 - Repeating the test with only 1 server")

print("starting the server2 again")
subprocess.run(["docker", "start", "server2"], check=True)

result_list = []
time.sleep(SLEEP_TIME)
start_tests(AMOUNT_OF_THREADS, "Phase 3 - Back to 2 servers")


if COPY_LOGS:
    copy_logs("my_loadbalancer", "./logs/loadbalancer.txt")
    copy_logs("server1", "./logs/server1.txt")
    copy_logs("server2", "./logs/server2.txt")
