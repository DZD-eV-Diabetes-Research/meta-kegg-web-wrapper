import multiprocessing
import requests
import time
import urllib3
import os
import traceback


if __name__ == "__main__":
    from pathlib import Path
    import sys, os

    MODULE_DIR = Path(__file__).parent
    MODULE_PARENT_DIR = MODULE_DIR.parent.resolve()
    sys.path.insert(0, os.path.normpath(MODULE_PARENT_DIR))

from statics import (
    DOT_ENV_FILE_PATH,
)

os.environ["MEKEWESERVER_DOT_ENV_FILE"] = DOT_ENV_FILE_PATH

from utils import get_mekeweserver_base_url, get_dot_env_file_variable


from mekeweserver.main import run_server

mekeweserver_process = multiprocessing.Process(
    target=run_server,
    name="DZDMeKeWeServer",
    kwargs={"env": {"MEKEWESERVER_DOT_ENV_FILE": DOT_ENV_FILE_PATH}},
)


mekeweserver_base_url = get_mekeweserver_base_url()


def wait_for_mekeweserver_up_and_healthy(timeout_sec=5):
    mekeweserver_not_available = True
    timeout_end = time.time() + timeout_sec
    r = None
    while mekeweserver_not_available and timeout_end > time.time():
        try:
            r = requests.get(f"{mekeweserver_base_url}/health")

            r.raise_for_status()

            mekeweserver_not_available = False

        except (
            requests.HTTPError,
            requests.ConnectionError,
            urllib3.exceptions.MaxRetryError,
        ):
            pass
        time.sleep(1)
    if timeout_end < time.time():
        print("Could not boot mekeweserver...")
        exit(1)
    print(f"SERVER UP FOR TESTING: {r.status_code}: {r.json()}")


def shutdown_mekeweserver_and_backgroundworker():
    print("SHUTDOWN SERVER!")
    mekeweserver_process.terminate()
    time.sleep(5)
    print("KILL SERVER")

    # YOU ARE HERE! THIS DOES NOT KILL THE BACKGORUND WORKER PROCESS
    mekeweserver_process.kill()
    mekeweserver_process.join()
    mekeweserver_process.close()


def start_mekeweserver_and_backgroundworker():
    print("START mekeweserver")
    mekeweserver_process.start()
    wait_for_mekeweserver_up_and_healthy()
    # print("START mekeweserver BACKGROUND WORKER")
    print("STARTED mekeweserver!")


start_mekeweserver_and_backgroundworker()

# RUN TESTS
from tests.tests_pipeline_run import run_all_tests_pipeline_run

if mekeweserver_process.is_alive():
    try:
        run_all_tests_pipeline_run()
    except Exception as e:
        print("Error in user tests")
        print(print(traceback.format_exc()))
        shutdown_mekeweserver_and_backgroundworker()
        print("TESTS FAILED")
        exit(1)


shutdown_mekeweserver_and_backgroundworker()
print("TESTS SUCCEDED")
exit(0)
