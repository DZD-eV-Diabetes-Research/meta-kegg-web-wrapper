import redis
from pathlib import Path
import uuid
from mekeweserver.config import RedisConnectionParams
from mekeweserver.model import (
    PipelineRunStatus,
    PipelineRunTicket,
    MetaKeggPipelineInputParams,
)


class PipelineClerk:
    REDIS_NAME_PIPELINE_STATES = "pipeline_states"
    REDIS_NAME_PIPELINE_QUEUE = "pipeline_queue"

    def __init__(self, redis_con: RedisConnectionParams, file_storage_base_dir: Path):
        self.redis = redis.Redis(**redis_con.model_dump)

    def init_new_pipeline_run(
        self, params: MetaKeggPipelineInputParams
    ) -> PipelineRunTicket:
        ticket = PipelineRunTicket()
        pipeline_state = PipelineRunStatus(
            state="initialized",
            place_in_queue=None,
            ticket=ticket,
            pipeline_params=params,
            pipeline_input_files=None,
        )
        self.redis.hset(
            self.REDIS_NAME_PIPELINE_STATES, pipeline_state.model_dump_json()
        )

    def get_pipeline_status(self, ticket_id: uuid.UUID):
        return PipelineRunStatus.model_validate_json(
            self.redis.hget(self.REDIS_NAME_PIPELINE_STATES, ticket_id)
        )

    def attach_input_file(self, ticket_id: uuid.UUID, file: bytes):
        raise NotImplementedError()

    def start_pipeline_run(self, ticket_id: uuid.UUID, analysis_method_name: str):
        raise NotImplementedError()

    def finish_pipeline_run(self, ticket_id: uuid.UUID, result_file_path: Path):
        raise NotImplementedError()

    def clean_pipeline_run(self, ticket_id: uuid.UUID):
        raise NotImplementedError()

    def delete_pipeline_run(self, ticket_id: uuid.UUID):
        raise NotImplementedError()
