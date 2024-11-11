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


def add_min_to_datetime():
    import datetime

    now = datetime.datetime.now()
    minutes_to_add = 240
    print(now)
    future = now + datetime.timedelta(minutes=minutes_to_add)
    print(future)


def capture_prints():
    from io import StringIO
    import sys
    import time

    def this_is_a_test():
        print("I start")
        time.sleep(1)
        print("I worked")

    class Capturing(list):
        def __enter__(self):
            self._stdout = sys.stdout
            sys.stdout = self._stringio = StringIO()
            return self

        def __exit__(self, *args):
            self.extend(self._stringio.getvalue().splitlines())
            del self._stringio  # free up some memory
            sys.stdout = self._stdout

    with Capturing() as output:
        this_is_a_test()

    print("displays on screen")

    with Capturing(output) as output:  # note the constructor argument
        print("hello world2")

    print("done")
    print("output:", output)


def capture_prints_asynco():
    from io import StringIO
    import sys
    import time
    import asyncio

    async def this_is_a_test():
        print("I start")
        time.sleep(1)
        print("I worked")
        time.sleep(1)
        print("I am done")

    class Capturing(list):
        def __enter__(self):
            self._stdout = sys.stdout
            sys.stdout = self._stringio = StringIO()
            return self

        def __exit__(self, *args):
            self.extend(self._stringio.getvalue().splitlines())
            del self._stringio  # free up some memory
            sys.stdout = self._stdout

    l = asyncio.get_event_loop()
    with Capturing() as output:
        l.run_until_complete(this_is_a_test())

    print("displays on screen")

    with Capturing(output) as output:  # note the constructor argument
        print("hello world2")

    print("done")
    print("output:", output)


def capture_real_time():
    import sys
    import time
    import logging
    from io import TextIOBase
    from typing import Callable

    def get_logger() -> logging.Logger:
        log = logging.getLogger()
        log.setLevel("INFO")
        log.addHandler(logging.StreamHandler(sys.stdout))
        return log

    def this_is_a_test():
        print("I start")
        time.sleep(1)
        print("I worked")
        time.sleep(1)
        print("I am done")

    class RealTimeOutputCapture:

        def __init__(self, output_handler: Callable[[str, TextIOBase], None]):
            self.output_handler = output_handler
            self.original_stdout = sys.stdout  # Save original stdout
            self.buffer = ""  # Buffer to store partial output

        def __enter__(self):
            sys.stdout = self  # Redirect stdout to this instance
            return self

        def write(self, message):
            # Buffer the output until we hit a newline
            self.buffer += message
            if "\n" in self.buffer:
                # Split by newlines and handle each complete line
                lines = self.buffer.splitlines(keepends=True)
                for line in lines:
                    if line.endswith("\n"):
                        self.output_handler(line.strip(), self.original_stdout)
                self.buffer = ""

        def __exit__(self, exc_type, exc_val, exc_tb):
            sys.stdout = self.original_stdout  # Restore original stdout

    def handler(m: str, original_logger: TextIOBase):
        original_logger.write(f"PREFIX ALL THE THINGS {m}\n")

    with RealTimeOutputCapture(handler) as cap:
        this_is_a_test()


def get_typehint():
    from typing import (
        Literal,
        Optional,
        List,
        Awaitable,
        Type,
        Any,
        Union,
        get_args,
        get_origin,
        get_type_hints,
    )
    from metaKEGG import Pipeline

    def get_arg_type(annotation: Any, is_optional: bool = False):

        if get_origin(annotation) == Union:
            # we dont handle Union options. we just take the first option into account
            annotation = get_args(annotation)[0]
            return get_arg_type(annotation)
        if get_origin(annotation) == Optional:
            # we dont handle Union options. we just take the first option into account
            return get_arg_type(annotation, is_optional=True)

        print("annotation", annotation)
        get_args(annotation)
        print("get_origin", get_origin(annotation))
        print("get_args", get_args(annotation))

    for name, type_ in get_type_hints(Pipeline.__init__).items():
        print("__NAME", name, type_)
        print(get_arg_type(type_))


get_typehint()
