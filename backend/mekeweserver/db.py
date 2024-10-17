from multiprocessing import Process, Event
from fakeredis import TcpFakeServer
from threading import Thread
import redis
from redis.exceptions import ConnectionError
import time
from mekeweserver.log import get_logger
from mekeweserver.config import Config, RedisConnectionParams
import atexit

config = Config()
log = get_logger()

LOCAL_FAKEREDIS_HOSTNAME = "localhost"
LOCAL_FAKEREDIS_PORT = 6379


class FakeredisServerProcess(Process):
    # constructor
    def __init__(self, hostname: str = "localhost", port: int = 19000):
        # call the parent constructor
        Process.__init__(self, daemon=True)
        self.stop_event = Event()
        self.hostname = hostname
        self.port = port
        self.fakeredis_server: TcpFakeServer | None = None
        self.server_thread: Thread | None = None

    def stop(self):
        self.stop_event.set()

    def run(
        self,
    ):
        TcpFakeServer.allow_reuse_address = True
        self.fakeredis_server = TcpFakeServer(server_address=(self.hostname, self.port))
        while not self.stop_event.is_set():
            time.sleep(0.1)
            self.fakeredis_server.handle_request()


def start_fakeredis_server(
    hostname: str = "localhost", port: int = 19000, wait_for_start_timeout_sec=3
) -> FakeredisServerProcess:
    #  Start fakeredis server
    fakeredis = FakeredisServerProcess("localhost", 19001)
    fakeredis.start()
    time.sleep(0.3)
    if not fakeredis.is_alive():
        print(" ")
        raise ChildProcessError(
            f"Could not start fakeredisserver. exit code {fakeredis.exitcode}"
        )

    # wait for server to boot by testing connection for n secs.
    boot_time = time.time()
    last_error = "init placeholder"
    while (
        boot_time + wait_for_start_timeout_sec > time.time() and last_error is not None
    ):
        try:
            test_client = redis.Redis(host="localhost", port=19001)
            test_client.ping()
            last_error = None
        except (ConnectionError, ConnectionRefusedError) as e:
            last_error = e
            time.sleep(0.3)
    if last_error is not None:
        # seems like the fakeredis server did not boot
        raise last_error
    # all ok return the fakeredis process
    return fakeredis


def stop_fakeredis_server(server: FakeredisServerProcess):
    server.stop()
    server.join(timeout=3)


def check_redis_server_running(redis_client: redis.Redis) -> bool:
    try:
        redis_client.ping()
        return True
    except:
        return False


def get_redis_client() -> redis.Redis:
    if config.REDIS_CONNECTION_PARAMS is None:
        client = redis.Redis(host=LOCAL_FAKEREDIS_HOSTNAME, port=LOCAL_FAKEREDIS_PORT)
        if check_redis_server_running(redis_client=client):
            return client
        # first call and no redis server running. Lets start a fakeredisserver
        log.warning(
            "No redis database connection provided in config.REDIS_CONNECTION_PARAMS. MetaKEGGWeb will try to boot a fakeredis-py server. this should not be used in production!"
        )
        fake_redis_server = start_fakeredis_server()

        def exit_handler():
            # shutdown redisfake server when we exit python
            stop_fakeredis_server(fake_redis_server)

        atexit.register(exit_handler)

        return client
    else:
        redis.Redis(**config.REDIS_CONNECTION_PARAMS.model_dump())
