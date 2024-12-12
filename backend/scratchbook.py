# This file just contains some python scratchbook code and was just for testing little concepts during dev


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

    config: Config = get_config()
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
    from pydantic import BaseModel, Field
    from pydantic_core import PydanticUndefined
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
    import inspect
    from metaKEGG import Pipeline
    import json

    UNSET_TYPE = List
    UNSET = []

    class PipelineMethodParamDoc(BaseModel):
        name: str
        type: Literal["str", "int", "float", "bool"] = "str"
        is_list: bool = False
        required: bool = False
        default: Optional[
            str | int | float | List[str] | List[int] | List[float] | None | UNSET_TYPE
        ]

    class UndefinedEncoder(json.JSONEncoder):
        def default(self, obj):
            if obj is None:
                return "undefined"
            return super().default(obj)

    def get_param_doc(
        name: str,
        annotation: Any,
        default: Any,
        is_optional: bool = False,
        is_list: bool = False,
    ):
        if get_origin(annotation) == Union:
            # we dont handle Union options. we just take the first option into account
            annotation = get_args(annotation)[0]
            return get_param_doc(name, annotation, default)
        if get_origin(annotation) == Optional:
            annotation = get_args(annotation)[0]
            return get_param_doc(name, annotation, default, is_optional=True)
        if get_origin(annotation) == list:
            annotation = get_args(annotation)[0]
            return get_param_doc(
                name, annotation, default, is_optional=True, is_list=True
            )
        return PipelineMethodParamDoc(
            name=name,
            type=annotation.__name__,
            required=not is_optional,
            is_list=is_list,
            default=default,
        )

    for name, type_hint in get_type_hints(Pipeline.__init__).items():
        if name == "return":
            continue
        default = UNSET
        param = inspect.signature(Pipeline.__init__).parameters.get(name)
        if param and param.default is not inspect.Parameter.empty:
            default = param.default
        print("__NAME", name, type_hint)
        doc = get_param_doc(name, type_hint, default=default)

        print(doc.model_dump_json(indent=2))


def iter_enum():
    from enum import Enum
    from metaKEGG import PipelineAsync
    from functools import partial

    class MetaKeggPipelineMethod(Enum):
        single_input_genes = partial(PipelineAsync.single_input_genes)
        single_input_transcripts = partial(PipelineAsync.single_input_transcripts)
        single_input_genes_bulk_mapping = partial(
            PipelineAsync.single_input_genes_bulk_mapping
        )
        multiple_inputs = partial(PipelineAsync.multiple_inputs)
        single_input_with_methylation = partial(
            PipelineAsync.single_input_with_methylation
        )
        single_input_with_methylation_quantification = partial(
            PipelineAsync.single_input_with_methylation_quantification
        )
        single_input_with_miRNA = partial(PipelineAsync.single_input_with_miRNA)
        single_input_with_miRNA_quantification = partial(
            PipelineAsync.single_input_with_miRNA_quantification
        )
        single_input_with_methylation_and_miRNA = partial(
            PipelineAsync.single_input_with_methylation_and_miRNA
        )

    for meth in MetaKeggPipelineMethod:
        print(meth.name)


def pydantic_exclude_set_defaults():
    from pydantic import BaseModel, Field

    class Test(BaseModel):
        f1: str = Field(default="path1")
        f2: str = Field(default="path2")
        f3: str = Field(default="path3")

    t = Test(f1="test")
    t.f2 = "path2"
    print("EXCULDE UNSET", t.model_dump(exclude_unset=True))
    print("EXCULDE DEFAULTS", t.model_dump(exclude_defaults=True))
    print("EXCULDE BOTH", t.model_dump(exclude_defaults=True, exclude_unset=True))


def get_seconds_past():
    import time
    import datetime

    past = datetime.datetime.now(tz=datetime.timezone.utc)
    time.sleep(2.3)
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    print((now - past).seconds)


def count_per_prop():
    from pydantic import BaseModel
    from collections import Counter

    class MetaKeggPipelineStatisticPoint(BaseModel):
        pipeline_methodname: str

    l = [
        MetaKeggPipelineStatisticPoint(pipeline_methodname="A"),
        MetaKeggPipelineStatisticPoint(pipeline_methodname="A"),
        MetaKeggPipelineStatisticPoint(pipeline_methodname="A"),
        MetaKeggPipelineStatisticPoint(pipeline_methodname="B"),
        MetaKeggPipelineStatisticPoint(pipeline_methodname="A"),
        MetaKeggPipelineStatisticPoint(pipeline_methodname="A"),
        MetaKeggPipelineStatisticPoint(pipeline_methodname="B"),
    ]

    methodname_counts = Counter(obj.pipeline_methodname for obj in l)
    print("methodname_counts", dict(methodname_counts))


def get_root_dir():
    from pathlib import Path

    return Path(__file__).parent
