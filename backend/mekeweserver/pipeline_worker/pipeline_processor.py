from typing import List, Callable, Awaitable, Any, Optional, Type, Dict
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
    GlobalParamModel,
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
        self._global_params: GlobalParamModel = None
        self._method_params: BaseModel = None

    def run(self) -> MetaKeggPipelineDef:
        try:
            self._run_pipeline()
        except Exception as e:
            log.debug(self.pipeline_definition.model_dump_json(indent=2))
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

    def _gather_global_params(self) -> GlobalParamModel:
        params = {}
        for param_doc in get_param_docs(PipelineAsync.__init__):

            if (
                param_doc.type == "file"
                and param_doc.name in self.pipeline_definition.pipeline_input_file_names
                and len(
                    self.pipeline_definition.pipeline_input_file_names[param_doc.name]
                )
                != 0
            ):
                params[param_doc.name] = []
                for filename in self.pipeline_definition.pipeline_input_file_names[
                    param_doc.name
                ]:
                    params[param_doc.name].append(
                        self.pipeline_definition.get_input_files_path(
                            param_doc.name, filename, not_exists_ok=False
                        ).absolute()
                    )
                # if param_doc.is_list == False:
                # hotfix for imprecise metakegg api
                if len(params[param_doc.name]) == 1:
                    params[param_doc.name] = params[param_doc.name][0]
            elif param_doc.type != "file":
                print("# param_doc", param_doc)
                print(
                    "## self.pipeline_definition.pipeline_params.global_params",
                    self.pipeline_definition.pipeline_params.global_params,
                )

                if (
                    param_doc.name
                    in self.pipeline_definition.pipeline_params.global_params
                    and self.pipeline_definition.pipeline_params.global_params[
                        param_doc.name
                    ]
                    != ""
                ):
                    if param_doc.name == "sheet_name_genes":
                        print(
                            "## sheet_name_genes",
                            self.pipeline_definition.pipeline_params.global_params[
                                param_doc.name
                            ],
                        )
                    params[param_doc.name] = (
                        self.pipeline_definition.pipeline_params.global_params[
                            param_doc.name
                        ]
                    )
        # input_file_path HOTFIX! for imprecise metakegg api
        # FIND A BETTER SOLUTION
        if "input_file_path" in params and not isinstance(
            params["input_file_path"], list
        ):
            params["input_file_path"] = [params["input_file_path"]]
            return GlobalParamModel(**params)

        return GlobalParamModel(**params)

    def _gather_analyse_method_params(self, method: Callable | Awaitable) -> BaseModel:
        params = {}
        param_docs = get_param_docs(method)
        for param_doc in param_docs:
            log.info(
                "self.pipeline_definition.pipeline_input_file_names",
                self.pipeline_definition.pipeline_input_file_names,
            )
            if (
                param_doc.type == "file"
                and param_doc.name in self.pipeline_definition.pipeline_input_file_names
                and len(
                    self.pipeline_definition.pipeline_input_file_names[param_doc.name]
                    != 0
                )
            ):
                params[param_doc.name] = []
                for filename in self.pipeline_definition.pipeline_input_file_names[
                    param_doc.name
                ]:
                    params[param_doc.name].append(
                        self.pipeline_definition.get_input_files_path(
                            param_doc.name,
                            filename,
                        ).absolute()
                    )
                if len(params[param_doc.name]) == 1:
                    params[param_doc.name] = params[param_doc.name][0]
            elif param_doc.type != "file":
                if (
                    param_doc.name
                    in self.pipeline_definition.pipeline_params.method_specific_params
                    and self.pipeline_definition.pipeline_params.method_specific_params[
                        param_doc.name
                    ]
                    != ""
                ):
                    params[param_doc.name] = (
                        self.pipeline_definition.pipeline_params.method_specific_params[
                            param_doc.name
                        ]
                    )
        MetaKeggMethodParamModel = get_param_model(
            method_name=method.__name__, param_docs=param_docs
        )
        return MetaKeggMethodParamModel(**params)

    def _run_pipeline(self):

        method: MetaKeggPipelineAnalysisMethod = (
            self.pipeline_definition.pipeline_analyses_method
        )
        event_loop = asyncio.get_event_loop()

        # The OutputCatcher (with our handler) writes any printed output of the metakegg pipeline run into our redis database. this way we can keep the user up2date what happening.
        with OutputCatcher(
            output_handler=get_pipeline_output_handler(
                self.pipeline_definition.ticket.id,
                self.pipeline_state_manager.redis_client,
            )
        ):
            # init metakegg.Pipeline
            self._global_params = self._gather_global_params()
            global_params_dict = self._global_params.model_dump()
            # 'input_file_path' HOTFIX! for imprecise metakegg api
            # FIND A BETTER SOLUTION
            if (
                "input_file_path" in global_params_dict
                and isinstance(global_params_dict["input_file_path"], list)
                and "single" in method.name.lower()
            ):
                global_params_dict["input_file_path"] = global_params_dict[
                    "input_file_path"
                ][0]
            print("###global_params_dict", global_params_dict)
            self.pipeline = PipelineAsync(
                output_folder_name=str(
                    self.pipeline_definition.get_output_files_dir().resolve()
                ),
                **global_params_dict,
            )
            # validate/filter method params
            # get_logger().info(("method:", method, method, str(method)))
            analysis_method_func: Callable[[], Awaitable[str]] = getattr(
                self.pipeline, method.name
            )
            self._method_params = self._gather_analyse_method_params(
                analysis_method_func
            )
            event_loop.run_until_complete(
                analysis_method_func(**self._method_params.model_dump())
            )

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
        pipeline_definition.error_traceback = (
            str(traceback.format_exc())
            + f"\n PipelineDefinition: \n {self.pipeline_definition.model_dump_json(indent=2)}"
            + f"\n metakegg.PipelineAsync Params: {self._global_params.model_dump_json(indent=2) if self._global_params else 'NotInitialized'}"
            + f"\n metakegg.PipelineAsync.{pipeline_definition.pipeline_analyses_method.name} Params: {self._method_params.model_dump_json(indent=2) if self._method_params else 'NotInitialized'}"
        )
        pipeline_definition = self.pipeline_state_manager.set_pipeline_run_definition(
            pipeline_definition
        )
        return pipeline_definition
