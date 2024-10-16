from typing import Dict, Optional, TypedDict, Callable
import redis
from pathlib import Path
from mekeweserver.config import Config, RedisConnectionParams


class PipelineQueue:

    def __init__(
        self,
        redis_connect_params: RedisConnectionParams | None = None,
        result_storage_path: Path = Path("/tmp/mekewe"),
        keep_running_check: Callable[[], bool] | None = None,
    ):
        if redis_connect_params is None:
            redis_connect_params = RedisConnectionParams(host="localhost", port=99977)
        if keep_running_check is None:
            keep_running_check = lambda: True
        self.redis_connect_params = redis_connect_params
        self.redis: redis.Redis | None = None
        self.result_storage_path = result_storage_path
        self.keep_running_check = keep_running_check

    def start(self):
        self.redis = redis.Redis(**self.redis_connect_params.model_dump())

    def _process_metakegg_pipelinerun_queue(self):
        while self.keep_running_check():
            raw_pipeline_run_params = self.redis.lpop("metakegg_pipeline_run_params")
