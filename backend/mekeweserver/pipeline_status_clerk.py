import redis
from pathlib import Path, PurePath
import uuid
import shutil
from fastapi import UploadFile
from mekeweserver.config import RedisConnectionParams
import redis
from mekeweserver.model import (
    PipelineRunStatus,
    PipelineRunTicket,
    MetaKeggPipelineInputParams,
    MetaKeggPipelineAnalysisMethods,
)
from config import Config

config = Config()


class PipelineStatusClerk:
    REDIS_NAME_PIPELINE_STATES = "pipeline_states"
    # REDIS_NAME_PIPELINE_QUEUE = "pipeline_queue"

    def __init__(self, redis: redis.Redis, file_storage_base_dir: Path = None):
        self.file_storage_base_dir = (
            file_storage_base_dir
            if file_storage_base_dir is not None
            else config.RESULT_CACHE_DIR
        )
        self.redis = redis

    def init_new_pipeline_run(
        self, params: MetaKeggPipelineInputParams
    ) -> PipelineRunTicket:
        ticket = PipelineRunTicket()
        pipeline_status = PipelineRunStatus(
            state="initialized",
            place_in_queue=None,
            ticket=ticket,
            pipeline_params=params,
            pipeline_input_files=None,
        )
        self.set_pipeline_status(pipeline_status)
        return ticket

    def get_pipeline_status(self, ticket_id: uuid.UUID) -> PipelineRunStatus:
        raw_data: str = self.redis.hget(self.REDIS_NAME_PIPELINE_STATES, ticket_id.hex)
        data = PipelineRunStatus.model_validate_json(raw_data)
        return data

    def set_pipeline_status(self, pipeline_status: PipelineRunStatus):
        self.redis.hset(
            self.REDIS_NAME_PIPELINE_STATES,
            pipeline_status.ticket.id.hex,
            pipeline_status.model_dump_json(),
        )

    def attach_input_file(
        self, ticket_id: uuid.UUID, upload_file_object: UploadFile
    ) -> PipelineRunStatus:
        # clean filename
        keepcharacters = (" ", ".", "_", "-")
        clean_file_name = "".join(
            c for c in upload_file_object.filename if c.isalnum() or c in keepcharacters
        ).rstrip()
        # define storage path for file
        internal_file_path = Path(
            PurePath(self.file_storage_base_dir, ticket_id.hex, clean_file_name)
        )
        internal_file_dir = internal_file_path.parent
        internal_file_dir.mkdir(parents=True, exist_ok=True)

        # store file
        with open(internal_file_path, "wb") as target_file:
            target_file.write(upload_file_object.file.read())

        # define file as pipeline input file
        pipeline_status = self.get_pipeline_status(ticket_id)
        pipeline_status.pipeline_input_files.append(clean_file_name)
        self.set_pipeline_status(pipeline_status)
        return pipeline_status

    def set_pipeline_run_as_queud(
        self, ticket_id: uuid.UUID, analysis_method_name: str
    ) -> PipelineRunStatus:
        pipeline_status = self.get_pipeline_status(ticket_id)
        pipeline_status.state = "queued"
        pipeline_status.pipeline_analyses_method = next(
            [
                e.value
                for e in MetaKeggPipelineAnalysisMethods
                if e.name == analysis_method_name
            ]
        )
        self.set_pipeline_status(pipeline_status)
        return pipeline_status

    def set_pipeline_state_as_running(
        self,
        ticket_id: uuid.UUID,
    ) -> PipelineRunStatus:
        pipeline_status = self.get_pipeline_status(ticket_id)
        pipeline_status.state = "running"
        self.set_pipeline_status(pipeline_status)
        return pipeline_status

    def set_pipeline_state_as_finished(
        self, ticket_id: uuid.UUID, error_msg: str = None, result_file_path: Path = None
    ) -> PipelineRunStatus:
        pipeline_status = self.get_pipeline_status(ticket_id)
        pipeline_status.state = "failed" if error_msg is not None else "success"
        if error_msg:
            pipeline_status.error = error_msg
        else:
            pipeline_status.result_path = result_file_path
        self.set_pipeline_status(pipeline_status)
        return pipeline_status

    def clean_pipeline_run(self, ticket_id: uuid.UUID) -> PipelineRunStatus:
        pipeline_status = self.get_pipeline_status(ticket_id)
        shutil.rmtree(PurePath(self.file_storage_base_dir, ticket_id.hex))
        pipeline_status.state = "expired"
        self.set_pipeline_status(pipeline_status)
        return pipeline_status

    def delete_pipeline_status(self, ticket_id: uuid.UUID):
        self.redis.hdel(self.REDIS_NAME_PIPELINE_STATES, ticket_id.hex)
