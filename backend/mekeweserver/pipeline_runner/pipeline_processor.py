from typing import List, Callable, Awaitable, Any
from pathlib import Path
import asyncio
from metaKEGG import Pipeline

from mekeweserver.model import (
    MetaKeggPipelineInputParams,
    MetaKeggPipelineAnalysisMethod,
)


class MetakeggPipelineProcessor:

    def __init__(
        self,
        input_file_pathes: Path | List[Path],
        output_directory: Path,
        pipeline_params: MetaKeggPipelineInputParams,
    ):
        if not isinstance(input_file_pathes, list):
            input_file_pathes = [input_file_pathes]

        self.input_file_pathes = input_file_pathes
        self.output_directory = output_directory
        self.pipeline_params = pipeline_params
        self.error_message: str | None = None
        self.pipeline = Pipeline(
            input_file_path=[str(p.resolve()) for p in self.input_file_pathes],
            output_folder_name=str(self.output_directory.resolve()),
            **self.pipeline_params.model_dump(),
        )

    async def run(self, method: MetaKeggPipelineAnalysisMethod):
        method_func: Callable[[], Awaitable[str]] = getattr(self.pipeline, method.name)
        return await method_func()
