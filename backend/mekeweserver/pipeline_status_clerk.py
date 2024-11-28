from typing import Dict, List, Optional
import redis
from pathlib import Path, PurePath
import uuid
import datetime
import shutil
from fastapi import UploadFile
from mekeweserver.config import RedisConnectionParams
import redis
from mekeweserver.model import (
    MetaKeggPipelineDef,
    MetaKeggPipelineDefStates,
    MetaKeggPipelineTicket,
    MetaKeggPipelineInputParamsDocs,
    MetaKeggPipelineAnalysisMethodDocs,
    MetaKeggPipelineInputParamsValues,
    MetaKeggPipelineInputParamsValuesAllOptional,
)
from mekeweserver.config import Config, get_config
from mekeweserver.log import get_logger
from mekeweserver.model import find_parameter_docs_by_name

config: Config = get_config()
log = get_logger()


class MetaKeggPipelineStateManager:
    REDIS_NAME_PIPELINE_STATES = "pipeline_states"
    REDIS_NAME_PIPELINE_QUEUE = "pipeline_queue"

    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    def get_all_pipeline_run_definitions(
        self, filter_state: MetaKeggPipelineDefStates = None
    ) -> List[MetaKeggPipelineDef]:
        result = []
        raw_definitions: str = self.redis_client.hgetall(
            self.REDIS_NAME_PIPELINE_STATES
        ).values()
        for raw_definition in raw_definitions:
            definition = MetaKeggPipelineDef.model_validate_json(raw_definition)
            if filter_state is not None and definition.state == filter_state:
                result.append(definition)
            elif filter_state is None:
                result.append(definition)
        return result

    def init_new_pipeline_run(
        self, params: MetaKeggPipelineInputParamsValuesAllOptional
    ) -> MetaKeggPipelineTicket:
        ticket = MetaKeggPipelineTicket()
        pipeline_status = MetaKeggPipelineDef(
            state="initialized",
            place_in_queue=None,
            ticket=ticket,
            pipeline_input_file_names=None,
            pipeline_params=MetaKeggPipelineInputParamsValuesAllOptional(
                **params.model_dump(exclude_unset=True)
            ),
        )
        self.set_pipeline_run_definition(pipeline_status)
        return ticket

    def get_pipeline_run_definition(
        self, ticket_id: uuid.UUID, raise_exception_if_not_exists: Exception = None
    ) -> MetaKeggPipelineDef:
        raw_data: str = self.redis_client.hget(
            self.REDIS_NAME_PIPELINE_STATES, ticket_id.hex
        )
        if raw_data is None and raise_exception_if_not_exists:
            raise raise_exception_if_not_exists
        data = MetaKeggPipelineDef.model_validate_json(raw_data)
        if data.state == "queued":
            pos_as_str: str | None = self.redis_client.lpos(
                self.REDIS_NAME_PIPELINE_QUEUE, ticket_id.hex
            )
            if pos_as_str is not None:
                data.place_in_queue = int(pos_as_str)
        return data

    def set_pipeline_run_definition(self, pipeline_status: MetaKeggPipelineDef):
        self.redis_client.hset(
            self.REDIS_NAME_PIPELINE_STATES,
            pipeline_status.ticket.id.hex,
            pipeline_status.model_dump_json(),
        )

    def attach_pipeline_run_input_file(
        self, ticket_id: uuid.UUID, param_name: str, upload_file_object: UploadFile
    ) -> MetaKeggPipelineDef:
        param_doc = find_parameter_docs_by_name(param_name=param_name)
        if param_doc == None or param_doc.type != "file":
            raise ValueError(
                f"Can not find parameter with name '{param_name}' to attach uploaded file to. Please provide a valid parameter name from one of MetaKegg analyses methods."
            )

        if upload_file_object.filename is None:
            upload_file_object.filename = uuid.uuid4().hex
        # clean filename
        keepcharacters = (".", "_", "-")
        clean_file_name = "".join(
            c for c in upload_file_object.filename if c.isalnum() or c in keepcharacters
        ).rstrip()

        pipeline_status = self.get_pipeline_run_definition(ticket_id)
        if pipeline_status.pipeline_input_file_names is None:
            pipeline_status.pipeline_input_file_names = {}

        # define storage path for file
        internal_file_path = Path(
            PurePath(pipeline_status.get_input_file_dir(param_name), clean_file_name)
        )
        internal_file_dir = internal_file_path.parent
        internal_file_dir.mkdir(parents=True, exist_ok=True)
        # define file as pipeline input file
        if param_name not in pipeline_status.pipeline_input_file_names:
            # ToDo: why is this nessesary? Why is default_factory not creating an empty list here?
            pipeline_status.pipeline_input_file_names[param_name] = []

        # delete old file if its "one file only" param and existent.
        if not param_doc.is_list:
            existing_file = pipeline_status.pipeline_input_file_names[param_name]
            if existing_file:
                pipeline_status = self.remove_pipeline_run_input_file(
                    ticket_id=ticket_id,
                    removefile_name=existing_file[0],
                )

        # store file
        with open(internal_file_path, "wb") as target_file:
            target_file.write(upload_file_object.file.read())

        # check if its a re-upload and we just overwrote the file...
        if clean_file_name not in pipeline_status.pipeline_input_file_names[param_name]:
            # ... otherwise we just append it as a new file
            pipeline_status.pipeline_input_file_names[param_name].append(
                clean_file_name
            )
        self.set_pipeline_run_definition(pipeline_status)
        return pipeline_status

    def remove_pipeline_run_input_file(
        self,
        ticket_id: uuid.UUID,
        param_name: str,
        removefile_name: str,
        raise_exception_if_not_exists: Exception = None,
    ) -> MetaKeggPipelineDef:
        pipeline = self.get_pipeline_run_definition(
            ticket_id=ticket_id,
            raise_exception_if_not_exists=raise_exception_if_not_exists,
        )
        upload_file_path = pipeline.get_input_files_path(param_name, removefile_name)
        if upload_file_path is None:
            # file does not exists. nothing we cant delete it
            log.warning(
                f"Tried to delete file '{param_name}'/'{removefile_name}' for pipeline '{pipeline.ticket.id}' but did not exists."
            )
            return pipeline
        pipeline.pipeline_input_file_names[param_name].remove(removefile_name)
        self.set_pipeline_run_definition(pipeline)
        upload_file_path.unlink(missing_ok=True)
        return self.get_pipeline_run_definition(ticket_id=ticket_id)

    def set_pipeline_method(
        self, ticket_id: uuid.UUID, analysis_method_name: str
    ) -> MetaKeggPipelineDef:
        log.info(f"Add pipeline-run with id '{ticket_id}' to queue.")
        pipeline_status = self.get_pipeline_run_definition(ticket_id)
        pipeline_status.pipeline_analyses_method = next(
            e.value
            for e in MetaKeggPipelineAnalysisMethodDocs
            if e.name == analysis_method_name
        )
        self.set_pipeline_run_definition(pipeline_status)
        return pipeline_status

    def set_pipeline_run_as_queud(self, ticket_id: uuid.UUID) -> MetaKeggPipelineDef:
        log.info(f"Add pipeline-run with id '{ticket_id}' to queue.")
        pipeline_status = self.get_pipeline_run_definition(ticket_id)

        # reset error from previous runs (if existent)...
        pipeline_status.error = None
        pipeline_status.error_traceback = None
        pipeline_status.output_log = None
        pipeline_status.finished_at_utc = None
        if pipeline_status.get_output_zip_file_path() is not None:
            # delete results from previous runs
            pipeline_status.get_output_zip_file_path().unlink(missing_ok=True)
        # ...reset done

        pipeline_status.state = "queued"
        queue_length = self.redis_client.llen(self.REDIS_NAME_PIPELINE_QUEUE)

        self.set_pipeline_run_definition(pipeline_status)
        self.redis_client.lpush(self.REDIS_NAME_PIPELINE_QUEUE, ticket_id.hex)
        pipeline_status.place_in_queue = queue_length + 1
        return pipeline_status

    def set_pipeline_state_as_running(
        self,
        ticket_id: uuid.UUID,
    ) -> MetaKeggPipelineDef:
        pipeline_status = self.get_pipeline_run_definition(ticket_id)

        pipeline_status.state = "running"
        pipeline_status.started_at_utc = datetime.datetime.now(tz=datetime.timezone.utc)
        self.set_pipeline_run_definition(pipeline_status)
        return pipeline_status

    def set_pipeline_state_as_finished(
        self, ticket_id: uuid.UUID, error_msg: str = None, result_file_path: Path = None
    ) -> MetaKeggPipelineDef:
        pipeline_status = self.get_pipeline_run_definition(ticket_id)
        pipeline_status.state = "failed" if error_msg is not None else "success"
        if error_msg:
            pipeline_status.error = error_msg
        else:
            pipeline_status.result_path = result_file_path
        pipeline_status.finished_at_utc = datetime.datetime.now(
            tz=datetime.timezone.utc
        )
        self.set_pipeline_run_definition(pipeline_status)
        return pipeline_status

    def wipe_pipeline_run(self, ticket_id: uuid.UUID) -> Optional[MetaKeggPipelineDef]:
        pipeline_status = self.get_pipeline_run_definition(ticket_id)
        if pipeline_status is None:
            return
        if pipeline_status.get_files_base_dir().exists():
            shutil.rmtree(pipeline_status.get_files_base_dir())
        pipeline_status.state = "expired"
        self.set_pipeline_run_definition(pipeline_status)
        return pipeline_status

    def delete_pipeline_status(self, ticket_id: uuid.UUID):
        self.redis_client.hdel(self.REDIS_NAME_PIPELINE_STATES, ticket_id.hex)

    def get_next_pipeline_run_from_queue(
        self, set_status_running: bool = True
    ) -> MetaKeggPipelineDef | None:
        raw_ticket_id: bytes = self.redis_client.rpop(self.REDIS_NAME_PIPELINE_QUEUE)
        if raw_ticket_id is None:
            return None
        raw_ticket_id = raw_ticket_id.decode("utf-8")
        # print(
        #    "TODO: FIX THIS. Failes in test and shows that backgroudn worker is not terminated properly"
        # ) # update: can not reproduce failed termination of background worker. keep eye on.

        log.info(
            f"Pick up next pipeline-run with id '{raw_ticket_id}' from queue to be processed..."
        )
        next_ticket_id = uuid.UUID(raw_ticket_id)
        pipeline_status = self.get_pipeline_run_definition(next_ticket_id)
        if set_status_running:
            pipeline_status.state = "running"
            pipeline_status.started_at_utc = datetime.datetime.now(
                tz=datetime.timezone.utc
            )
            self.set_pipeline_run_definition(pipeline_status)
        return pipeline_status

    def get_next_pipeline_that_is_expired(
        self, set_status_expired: bool = True
    ) -> MetaKeggPipelineDef | None:
        all_pipeline_states_json_raw: Dict[str, str] = self.redis_client.hgetall(
            self.REDIS_NAME_PIPELINE_STATES
        )
        for uuid_hex, pipeline_state_json_raw in all_pipeline_states_json_raw.items():

            pipeline_status = MetaKeggPipelineDef.model_validate_json(
                pipeline_state_json_raw
            )
            if self.is_pipeline_run_expired(pipeline_status):
                if set_status_expired:
                    pipeline_status.state = "expired"
                    self.set_pipeline_run_definition(pipeline_status)
                return pipeline_status
        return None

    def get_next_pipeline_that_is_deletable(self) -> MetaKeggPipelineDef | None:
        all_pipeline_states_json_raw: Dict[str, str] = self.redis_client.hgetall(
            self.REDIS_NAME_PIPELINE_STATES
        )
        for uuid_hex, pipeline_state_json_raw in all_pipeline_states_json_raw.items():
            pipeline_status = MetaKeggPipelineDef.model_validate_json(
                pipeline_state_json_raw
            )
            if self.is_pipeline_run_deletable(pipeline_status):
                return pipeline_status
        return None

    def get_next_pipeline_that_is_abandoned(
        self,
    ) -> MetaKeggPipelineDef | None:
        all_pipeline_states_json_raw: Dict[str, str] = self.redis_client.hgetall(
            self.REDIS_NAME_PIPELINE_STATES
        )
        for uuid_hex, pipeline_state_json_raw in all_pipeline_states_json_raw.items():
            pipeline_status = MetaKeggPipelineDef.model_validate_json(
                pipeline_state_json_raw
            )
            if self.is_pipeline_run_definition_abandoned(pipeline_status):
                return pipeline_status
        return None

    def is_pipeline_run_expired(self, pipeline_status: MetaKeggPipelineDef):
        if pipeline_status.finished_at_utc is None:
            # only finished pipeline run can expire.
            return False
        expire_datetime = pipeline_status.finished_at_utc + datetime.timedelta(
            minutes=config.PIPELINE_RESULT_EXPIRED_AFTER_MIN
        )
        if expire_datetime < datetime.datetime.now(tz=datetime.timezone.utc):
            return True
        return False

    def is_pipeline_run_deletable(self, pipeline_status: MetaKeggPipelineDef):
        if pipeline_status.finished_at_utc is None:
            # only finished pipeline run can expire.
            return False
        expire_datetime = pipeline_status.finished_at_utc + datetime.timedelta(
            minutes=config.PIPELINE_RESULT_EXPIRED_AFTER_MIN
        )
        deleteable_datetime = expire_datetime + datetime.timedelta(
            minutes=config.PIPELINE_ABANDONED_DEFINITION_DELETED_AFTER
        )
        if deleteable_datetime < datetime.datetime.now(tz=datetime.timezone.utc):
            return True
        return False

    def is_pipeline_run_definition_abandoned(
        self, pipeline_status: MetaKeggPipelineDef
    ):
        if pipeline_status.state != "initialized":
            # only pipeline runs with state initialized can be "abandoned".
            return False
        abandoned_datetime = pipeline_status.created_at_utc + datetime.timedelta(
            minutes=config.PIPELINE_ABANDONED_DEFINITION_DELETED_AFTER
        )
        if abandoned_datetime < datetime.datetime.now(tz=datetime.timezone.utc):
            return True
        return False
