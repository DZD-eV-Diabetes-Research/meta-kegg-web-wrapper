def type_dict_settings_env_var_test():
    from pydantic import BaseModel
    from pydantic_settings import BaseSettings
    from pathlib import Path
    from typing import Optional
    import redis

    class RedisConnectionParams(BaseSettings):
        host: str = "localhost"
        port: int = 6379

    class Config(BaseSettings):
        redis_connect_params: RedisConnectionParams
        result_storage_path: Path = Path("/tmp/mekewe")

        class Config:
            env_prefix = "MYAPP_"  # environment variable prefix (e.g., MYAPP_REDIS_CONNECT_PARAMS_HOST)
            env_nested_delimiter = "__"

    config = Config()
    print(config.model_dump())


def run_type_dict_settings_env_var_test():
    import os

    os.environ["MYAPP_redis_connect_params__host"] = "changed!"
    type_dict_settings_env_var_test()


def enum_test():
    from enum import Enum
    from typing_extensions import Self

    class MetaKeggPipelineAnalysisMethods(Enum):
        _1 = "single_input_genes"
        _2 = "single_input_transcripts"
        _3 = "single_input_genes_bulk_mapping"
        _4 = "multiple_inputs"
        _5 = "single_input_with_methylation"
        _6 = "single_input_with_methylation_quantification"
        _7 = "single_input_with_miRNA"
        _8 = "single_input_with_miRNA_quantification"
        _9 = "single_input_with_methylation_and_miRNA"

        @classmethod
        def get_name_as_int_by_value(cls: Self, value: str) -> int:
            return int(str(MetaKeggPipelineAnalysisMethods(value)).split("_")[1])

    print([e.value for e in MetaKeggPipelineAnalysisMethods])


enum_test()
