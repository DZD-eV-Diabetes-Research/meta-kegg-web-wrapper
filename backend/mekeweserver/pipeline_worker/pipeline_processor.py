from typing import List, Callable, Awaitable, Any
from io import StringIO
import sys
from pathlib import Path
import traceback
import asyncio
import redis
from metaKEGG import Pipeline

from mekeweserver.model import (
    MetaKeggPipelineInputParams,
    MetaKeggPipelineAnalysisMethod,
    MetaKeggPipelineDef,
)
from mekeweserver.pipeline_status_clerk import MetaKeggPipelineStateManager
from mekeweserver.pipeline_worker.pipeline_output_catcher import (
    OutputCatcher,
    get_pipeline_output_handler,
)


class MetakeggPipelineProcessor:

    def __init__(
        self,
        pipeline_definition: MetaKeggPipelineDef,
        pipeline_state_manager: MetaKeggPipelineStateManager,
    ):
        self.pipeline_definition = pipeline_definition
        self.pipeline_state_manager = pipeline_state_manager

    def run(self) -> MetaKeggPipelineDef:
        try:
            self.pipeline = Pipeline(
                input_file_path=[
                    str(p.resolve())
                    for p in self.pipeline_definition.get_input_files_pathes()
                ],
                output_folder_name=str(
                    self.pipeline_definition.get_output_files_dir().resolve()
                ),
                **self.pipeline_definition.pipeline_params.model_dump(),
            )
            method: MetaKeggPipelineAnalysisMethod = self.pipeline_definition
            analysis_method_func: Callable[[], Awaitable[str]] = getattr(
                self.pipeline, method.name
            )
            event_loop = asyncio.get_event_loop()

            # The OutputCatcher (with our handler) writes any printed output of the metakegg pipeline run into our redis database. this way we can keep the user up2date what happening.
            with OutputCatcher(
                output_handler=get_pipeline_output_handler(
                    self.pipeline_definition.ticket.id, self.redis_client
                )
            ):
                event_loop.run_until_complete(analysis_method_func())
        except Exception as e:
            # get latest state
            self.pipeline_definition = self.pipeline_state_manager.get_pipeline_status(
                ticket_id=self.pipeline_definition.ticket.id
            )
            self.pipeline_definition.state = "failed"
            self.pipeline_definition.error = str(e)
            self.pipeline_definition.error_traceback = str(traceback.format_exc())
            self.pipeline_definition = self.pipeline_state_manager.set_pipeline_status(
                self.pipeline_definition
            )
            return self.pipeline_definition
        self.pipeline_definition = self.pipeline_state_manager.get_pipeline_status(
            ticket_id=self.pipeline_definition.ticket.id
        )
        self.pipeline_definition.state = "success"
        self.pipeline_state_manager.set_pipeline_status(self.pipeline_definition)
        return self.pipeline_definition
