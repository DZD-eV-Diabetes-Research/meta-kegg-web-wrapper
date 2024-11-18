import sys
import time
import logging
import redis
from io import TextIOBase
from typing import Callable
import uuid

from mekeweserver.pipeline_status_clerk import MetaKeggPipelineStateManager
from mekeweserver.model import MetaKeggPipelineDef
from mekeweserver.config import Config, get_config

config: Config = get_config()


class OutputCatcher:

    def __init__(self, output_handler: Callable[[str, TextIOBase], None]):
        self.output_handler = output_handler
        self.original_stdout = sys.stdout  # Save original stdout
        self.buffer = ""  # Buffer to store partial output

    def __enter__(self):
        sys.stdout = self  # Redirect stdout to this instance
        return self

    def write(self, message):
        # Buffer the output until we hit a newline
        self.buffer += message
        if "\n" in self.buffer:
            # Split by newlines and handle each complete line
            lines = self.buffer.splitlines(keepends=True)
            for line in lines:
                if line.endswith("\n"):
                    self.output_handler(line.strip(), self.original_stdout)
            self.buffer = ""

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout  # Restore original stdout


def get_pipeline_output_handler(
    ticket_id: uuid.UUID,
    redis_client: redis.Redis,
) -> Callable[[str, TextIOBase], None]:
    def pipeline_output_handler(m: str, original_logger: TextIOBase):
        state_clerk = MetaKeggPipelineStateManager(redis_client)
        pipeline_status = state_clerk.get_pipeline_status(ticket_id)
        if pipeline_status.output_log is None:
            pipeline_status.output_log = ""
        pipeline_status.output_log += m
        if config.LOG_LEVEL == "DEBUG":
            # if we are in debug mode, print all the stuff from the metakegg pipeline. otherwise we save it only to the redis server, no redudance in non debug mode.
            original_logger.write(m)
        state_clerk.set_pipeline_status(pipeline_status)

    return pipeline_output_handler
