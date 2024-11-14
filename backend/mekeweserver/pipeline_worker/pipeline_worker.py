from typing import List, Dict
from multiprocessing import Process, Event
import shutil
import traceback
import os

# from metaKEGG import Pipeline
# from mekeweserver.model import PipelineInputParams
import time

import redis

from mekeweserver.pipeline_status_clerk import MetaKeggPipelineStateManager
from mekeweserver.db import get_redis_client

from mekeweserver.log import get_logger
from mekeweserver.config import Config
from mekeweserver.pipeline_worker.pipeline_processor import MetakeggPipelineProcessor

config = Config()
log = get_logger()


class PipelineWorker(Process):
    WORKER_EXCEPTION_COUNTER_REDIS_KEY = "METAKEGG_WORKER_EXCEPTION_COUNT"

    # constructor
    def __init__(self, tick_pause_sec: int = 1, env: Dict = None):
        # call the parent constructor
        Process.__init__(self)
        # create and store an event
        self.stop_event = Event()
        self.tick_pause_sec = tick_pause_sec
        self.env = env

    def run(self):
        if self.env:
            os.environ = os.environ.copy() | self.env
        log.info("Started MetaKegg Pipeline Processing Worker")
        redis_client = get_redis_client(never_start_fakeredis=True)
        redis_client.set(self.WORKER_EXCEPTION_COUNTER_REDIS_KEY, 0)

        while not self.stop_event.is_set():
            try:
                pipeline_state_manager = MetaKeggPipelineStateManager(
                    redis_client=redis_client
                )
                self._process_next_pipeline_in_queue(pipeline_state_manager)
                self._process_next_expiring_pipeline(pipeline_state_manager)
                self._process_next_deletable_pipeline(pipeline_state_manager)
                self._process_next_abandoned_pipeline_def(pipeline_state_manager)
            except Exception as e:
                exception_count: int = 99999
                try:
                    exception_count = int(
                        redis_client.get(self.WORKER_EXCEPTION_COUNTER_REDIS_KEY)
                    )
                except redis.ConnectionError:
                    print("REDIS OFFLINE")
                    exception_count = 99999
                if (
                    exception_count
                    < config.RESTART_BACKGROUND_WORKER_ON_EXCEPTION_N_TIMES
                ):
                    print("exception_count", exception_count)
                    log.error(e, exc_info=True)
                    try:
                        print("INCREASE", exception_count)
                        exception_count = redis_client.incr(
                            self.WORKER_EXCEPTION_COUNTER_REDIS_KEY, 1
                        )
                        print("INCREASED", exception_count)
                    except:
                        raise e
                else:
                    raise e
                # traceback.format_exception(e)
            else:
                redis_client.set(self.WORKER_EXCEPTION_COUNTER_REDIS_KEY, 0)
            time.sleep(self.tick_pause_sec)
        log.info("Exiting MetaKegg Pipeline Processing Worker.")

    def _process_next_pipeline_in_queue(
        self, state_manager: MetaKeggPipelineStateManager
    ):
        next_pipeline_definition_in_queue = (
            state_manager.get_next_pipeline_run_from_queue()
        )
        if next_pipeline_definition_in_queue is not None:
            pipeline_processor = MetakeggPipelineProcessor(
                pipeline_definition=next_pipeline_definition_in_queue,
                pipeline_state_manager=state_manager,
            )
            pipeline_processor.run()

    def _process_next_expiring_pipeline(
        self, state_manager: MetaKeggPipelineStateManager
    ):
        next_pipeline_definition_that_is_expired = (
            state_manager.get_next_pipeline_that_is_expired()
        )
        if next_pipeline_definition_that_is_expired is None:
            return
        log.info(
            f"Set MetaKegg pipeline defintion with ticket id {next_pipeline_definition_that_is_expired.ticket.id.hex} as expired..."
        )
        # we first need to set the pipelinestate to expired before deleting anything to prevent race cond.
        next_pipeline_definition_that_is_expired.state = "expired"
        # set a "deleted" marker behind the input filename list
        next_pipeline_definition_that_is_expired.pipeline_input_file_names = [
            f"{fn} (Deleted)"
            for fn in next_pipeline_definition_that_is_expired.pipeline_input_file_names
        ]
        output_zip_name = (
            next_pipeline_definition_that_is_expired.pipeline_output_zip_file_name
        )
        if output_zip_name is not None:
            next_pipeline_definition_that_is_expired.pipeline_output_zip_file_name = (
                f"{output_zip_name} (Deleted)"
            )
        state_manager.set_pipeline_status(next_pipeline_definition_that_is_expired)

        # delete all cached file for this pipeline
        shutil.rmtree(next_pipeline_definition_that_is_expired.get_files_base_dir())

    def _process_next_deletable_pipeline(
        self, state_manager: MetaKeggPipelineStateManager
    ):

        next_pipeline_definition_that_is_deletable = (
            state_manager.get_next_pipeline_that_is_deletable()
        )
        if next_pipeline_definition_that_is_deletable is None:
            return
        log.info(
            f"Delete MetaKegg pipeline defintion with ticket id {next_pipeline_definition_that_is_deletable.ticket.id.hex} because of age..."
        )
        state_manager.delete_pipeline_status(
            ticket_id=next_pipeline_definition_that_is_deletable.ticket.id
        )

    def _process_next_abandoned_pipeline_def(
        self, state_manager: MetaKeggPipelineStateManager
    ):
        next_pipeline_definition_that_is_deletable = (
            state_manager.get_next_pipeline_that_is_abandoned()
        )
        if next_pipeline_definition_that_is_deletable is None:
            return
        log.info(
            f"Delete MetaKegg pipeline defintion with ticket id {next_pipeline_definition_that_is_deletable.ticket.id.hex} because it is abandoned..."
        )
        state_manager.delete_pipeline_status(
            ticket_id=next_pipeline_definition_that_is_deletable.ticket.id
        )
