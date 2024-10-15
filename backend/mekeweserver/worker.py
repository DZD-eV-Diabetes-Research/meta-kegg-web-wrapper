from typing import List
from metaKEGG import Pipeline
from mekeweserver.model import PipelineInputParams


async def run_pipeline(files: str | List[str], params: PipelineInputParams):
    pipeline = Pipeline(input_file_path=files, **params)
