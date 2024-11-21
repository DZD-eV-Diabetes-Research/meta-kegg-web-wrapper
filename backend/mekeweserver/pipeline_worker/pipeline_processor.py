from typing import List, Callable, Awaitable, Any, Optional, Type
from pydantic import BaseModel
from io import StringIO
import sys
from pathlib import Path
import traceback
import asyncio
import redis
import zipfile
import datetime
from metaKEGG.modules.pipeline_async import PipelineAsync

from mekeweserver.model import (
    MetaKeggPipelineInputParamsDocs,
    MetaKeggPipelineAnalysisMethod,
    MetaKeggPipelineDef,
    UNSET,
    get_param_model,
    get_param_docs,
)
from mekeweserver.pipeline_status_clerk import MetaKeggPipelineStateManager
from mekeweserver.pipeline_worker.pipeline_output_catcher import (
    OutputCatcher,
    get_pipeline_output_handler,
)
from mekeweserver.log import get_logger

log = get_logger()


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
            self.pipeline = PipelineAsync(
                input_file_path=[
                    str(p.resolve())
                    for p in self.pipeline_definition.get_input_files_pathes()
                ],
                output_folder_name=str(
                    self.pipeline_definition.get_output_files_dir().resolve()
                ),
                **self.pipeline_definition.pipeline_params.global_params.model_dump(),
            )
            method: MetaKeggPipelineAnalysisMethod = (
                self.pipeline_definition.pipeline_analyses_method
            )

            # get_logger().info(("method:", method, method, str(method)))
            analysis_method_func: Callable[[], Awaitable[str]] = getattr(
                self.pipeline, method.name
            )
            event_loop = asyncio.get_event_loop()

            # The OutputCatcher (with our handler) writes any printed output of the metakegg pipeline run into our redis database. this way we can keep the user up2date what happening.
            with OutputCatcher(
                output_handler=get_pipeline_output_handler(
                    self.pipeline_definition.ticket.id,
                    self.pipeline_state_manager.redis_client,
                )
            ):
                # validate/filter method params
                method_non_files_params_model: Type[BaseModel] = get_param_model(
                    method_name=method.name,
                    param_docs=get_param_docs(analysis_method_func),
                    file_params=False,
                )

                # extract only valud params for this method
                attrs_non_file = {}
                for (
                    attr_name,
                    field_info,
                ) in method_non_files_params_model.model_fields.items():
                    if (
                        attr_name
                        in self.pipeline_definition.pipeline_params.method_specific_params
                    ):
                        attrs_non_file[attr_name] = (
                            self.pipeline_definition.pipeline_params.method_specific_params[
                                attr_name
                            ]
                        )
                method_files_params_model: Type[BaseModel] = get_param_model(
                    method_name=method.name,
                    param_docs=get_param_docs(analysis_method_func),
                    file_params=True,
                )
                attrs_file = {}
                for (
                    attr_name,
                    field_info,
                ) in method_files_params_model.model_fields.items():
                    if attr_name in [
                        self.pipeline_definition.pipeline_input_file_names.keys()
                    ]:
                        if (
                            len(
                                self.pipeline_definition.pipeline_input_file_names[
                                    attr_name
                                ]
                            )
                            == 1
                        ):
                            self.pipeline.input_file_path = (
                                self.pipeline.input_file_path[0]
                            )
                            attrs_file[attr_name] = (
                                self.pipeline_definition.pipeline_input_file_names[
                                    attr_name
                                ][0]
                            )
                        else:
                            attrs_file[attr_name] = (
                                self.pipeline_definition.pipeline_input_file_names[
                                    attr_name
                                ]
                            )
                # create a model instance to validate the inputs
                method_params = method_non_files_params_model(**attrs_non_file)
                event_loop.run_until_complete(
                    analysis_method_func(**method_params.model_dump())
                )
        except Exception as e:
            self.pipeline_definition = self.handle_exception(e)
            return self.pipeline_definition

        self.pipeline_definition = (
            self.pipeline_state_manager.get_pipeline_run_definition(
                ticket_id=self.pipeline_definition.ticket.id
            )
        )
        self.pipeline_definition.pipeline_output_zip_file_name = (
            self.pipeline_definition.generate_output_zip_file_name()
        )
        try:
            self.pack_output()
        except Exception as e:
            self.pipeline_definition = self.handle_exception(
                e, self.pipeline_definition
            )
            return self.pipeline_definition

        self.pipeline_definition.state = "success"
        self.pipeline_state_manager.set_pipeline_run_definition(
            self.pipeline_definition
        )
        return self.pipeline_definition

    def pack_output(self):
        # todo: i dont like this function here...maybe find a better place
        target_zip_file_path = (
            self.pipeline_definition.get_output_zip_file_path().resolve()
        )
        output_files = [
            f
            for f in self.pipeline_definition.get_output_files_dir().iterdir()
            if f.is_file()
        ]
        log.info(
            f"Zip output file {[f.name for f in self.pipeline_definition.get_output_files_dir().iterdir()]} into {target_zip_file_path}"
        )
        with zipfile.ZipFile(target_zip_file_path, "w") as output_zip:
            for output_file in output_files:
                output_zip.write(output_file, arcname=output_file.name)
        for output_file in output_files:
            output_file.unlink(missing_ok=True)

    def handle_exception(
        self, e: Exception, pipeline_status: Optional[MetaKeggPipelineDef] = None
    ) -> MetaKeggPipelineDef:
        if pipeline_status is None:
            pipeline_definition = (
                self.pipeline_state_manager.get_pipeline_run_definition(
                    ticket_id=self.pipeline_definition.ticket.id
                )
            )
        pipeline_definition.state = "failed"
        pipeline_definition.error = str(e)
        pipeline_definition.error_traceback = str(traceback.format_exc())
        pipeline_definition = self.pipeline_state_manager.set_pipeline_run_definition(
            pipeline_definition
        )
        return pipeline_definition
