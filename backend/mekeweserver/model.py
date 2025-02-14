from typing import (
    Literal,
    Optional,
    Union,
    List,
    Awaitable,
    Callable,
    Type,
    get_args,
    get_origin,
    get_type_hints,
    Any,
    Dict,
)

from functools import partial
import inspect
from typing_extensions import Self
from pydantic import BaseModel, Field, field_serializer, field_validator, create_model
import uuid
from enum import Enum
from mekeweserver.config import Config, get_config
import datetime
from pathlib import Path, PurePath
from metaKEGG import PipelineAsync
from mekeweserver.log import get_logger

config: Config = get_config()
log = get_logger()


class MetaKeggPipelineAnalysisMethods(Enum):
    gene_expression = partial(PipelineAsync.gene_expression)
    transcript_expression = partial(PipelineAsync.transcript_expression)
    multiple_inputs = partial(PipelineAsync.multiple_inputs)
    methylated_genes = partial(PipelineAsync.methylated_genes)
    mirna_target_genes = partial(PipelineAsync.mirna_target_genes)
    methylated_and_mirna_target_genes = partial(
        PipelineAsync.methylated_and_mirna_target_genes
    )
    demirs_per_gene = partial(PipelineAsync.demirs_per_gene)
    dmps_per_gene = partial(PipelineAsync.dmps_per_gene)
    bulk_rnaseq_mapping = partial(PipelineAsync.bulk_rnaseq_mapping)


class MetaKeggPipelineAnalysisMethod(BaseModel):
    name: str
    display_name: str
    internal_id: int
    desc: Optional[str] = None

    def get_params_docs(self) -> List["MetaKeggPipelineInputParamDocItem"]:
        return get_param_docs(self.method)


class MetaKeggPipelineAnalysisMethodDocs(Enum):
    gene_expression = MetaKeggPipelineAnalysisMethod(
        name="gene_expression",
        display_name="Gene expression",
        internal_id=1,
        desc="Perform the Single Input Analysis for Gene IDs.",
    )
    transcript_expression = MetaKeggPipelineAnalysisMethod(
        name="transcript_expression",
        display_name="Transcript expression",
        internal_id=2,
        desc="Perform the Single Input Analysis for Transcript IDs.",
    )
    bulk_rnaseq_mapping = MetaKeggPipelineAnalysisMethod(
        name="bulk_rnaseq_mapping",
        display_name="Bulk RNAseq mapping",
        internal_id=3,
        desc="Perform a single input analysis with bulk mapping for genes.",
    )
    multiple_inputs = MetaKeggPipelineAnalysisMethod(
        name="multiple_inputs",
        display_name="Multiple inputs",
        internal_id=4,
        desc="Perform the Multiple Inputs Analysis.",
    )
    methylated_genes = MetaKeggPipelineAnalysisMethod(
        name="methylated_genes",
        display_name="Methylated genes",
        internal_id=5,
        desc="Perform Single Input Analysis with Methylation.",
    )
    dmps_per_gene = MetaKeggPipelineAnalysisMethod(
        name="dmps_per_gene",
        display_name="DMPs per gene",
        internal_id=9,
        desc="Performs the DMPs per gene pipeline",
    )

    mirna_target_genes = MetaKeggPipelineAnalysisMethod(
        name="mirna_target_genes",
        display_name="miRNA target genes",
        internal_id=7,
        desc="Perform the miRNA target genes pipeline.",
    )
    demirs_per_gene = MetaKeggPipelineAnalysisMethod(
        name="demirs_per_gene",
        display_name="DEmiRs per gene",
        internal_id=8,
        desc="Performs the DEmiRs per gene pipeline.",
    )
    methylated_and_mirna_target_genes = MetaKeggPipelineAnalysisMethod(
        name="methylated_and_mirna_target_genes",
        display_name="Methylated + miRNA target genes",
        internal_id=6,
        desc="Performs the Methylated and miRNA target genes pipeline.",
    )


UNSET_TYPE = List
UNSET = []


class MetaKeggPipelineInputParamDocItem(BaseModel):
    name: str
    type: Literal["str", "int", "float", "bool", "file"] = "str"
    is_list: bool = False
    required: bool = False
    default: Optional[
        str
        | int
        | float
        | bool
        | List[str]
        | List[int]
        | List[float]
        | List[bool]
        | None
        | UNSET_TYPE
    ]
    description: Optional[str] = None


class MetaKeggPipelineInputParamsDocs(BaseModel):
    global_params: List[MetaKeggPipelineInputParamDocItem]
    method_specific_params: Optional[List[MetaKeggPipelineInputParamDocItem]] = Field(
        default_factory=list
    )


class MetaKeggPipelineTicket(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)


class MetaKeggWebServerModuleHealthState(BaseModel):
    name: str
    healthy: bool


class MetaKeggWebServerHealthState(BaseModel):
    healthy: bool
    dependencies: list[MetaKeggWebServerModuleHealthState]


class MetaKeggClientConfig(BaseModel):
    contact_email: Optional[str] = Field(
        description="Email that clients can present for contact.", default=None
    )
    bug_report_email: Optional[str] = Field(
        description="Email address that is used for bug reports. Will be the same as `contact_email` if not explicit configured in the backend otherwise.",
        default=None,
    )
    terms_and_conditions: Optional[str] = Field(
        description="Terms and Conditions presented to the user.", default=None
    )
    pipeline_ticket_expire_time_sec: int = Field(
        description="Time how long a Pipeline ticket is valid. This is only for informational purposes as the backend is handling ticket expiring.",
        default=config.PIPELINE_RESULT_EXPIRED_AFTER_MIN * 60,
    )
    entry_text: Optional[str] = Field(default=config.CLIENT_ENTRY_TEXT)


class MetaKeggClientLink(BaseModel):
    title: str = Field(description="Title of the link")
    link: str = Field(description="URL of the link")


### Param Doc Factory
class MetaKeggPipelineInputParamsDesc(Enum):
    sheet_name_paths = "Sheet name containing the pathway information (see docs). Has to apply to all input files in case of multiple."
    sheet_name_genes = "Sheet name for gene information (see docs). Has to apply to all input files in case of multiple."
    genes_column = "Column name for gene symbols in the sheet_name_genes"
    log2fc_column = "Column name for log2fc values in the sheet_name_genes"
    count_threshold = "Minimum number of genes per pathway, for pathway to be drawn."
    pathway_pvalue_threshold = "Raw p-value threshold for the pathways"
    input_label = "Input label or list of labels for multiple inputs"
    folder_extension = "Folder extension to be appended to the default naming scheme. If None and default folder exists, will overwrite folder"
    methylation_file_path = "Path to methylation data (Excel , CSV or TSV format)"
    methylation_pvalue_column = "Column name for methylation p-value"
    methylation_genes_column = "Column name for methylation gene symbols"
    methylation_pvalue_threshold = "P-value threshold for the methylation values"
    methylation_probe_column = "Column name for the methylation probes."
    probes_to_cgs = "If True, will correct the probes to positions, delete duplicated positions and keep the first CG."
    miRNA_file_path = "Path to miRNA data (Excel , CSV or TSV format)"
    miRNA_pvalue_column = "Column name for miRNA p-value"
    miRNA_genes_column = "Column name for miRNA gene symbols"
    miRNA_pvalue_threshold = "P-value threshold for the miRNA values"
    miRNA_ID_column = "Column name for the miRNA IDs."
    benjamini_threshold = "Benjamini Hochberg p-value threshold for the pathway"
    save_to_eps = "True/False statement to save the maps and colorscales or legends as seperate .eps files in addition to the .pdf exports"
    compounds_list = "List of compound IDs to mapped in pathways if found."


# some params need special handling and will not be presented to the api
metaKegg_param_exclude = ["folder_extension", "output_folder_name"]


class MetaKeggPipelineInputParamsDocsTypeOverride(Enum):
    input_file_path = List[Path]
    # input_label = List[str] # was adapted upstream in the metakegg api. no override needed anymore


class MetaKeggPipelineInputParamsDefaultValOverrideFactory(Enum):
    # input_label = partial(list) # was adapted upstream in the metakegg api. no override needed anymore
    pass


param_types_map = {"int": int, "bool": bool, "float": float, "str": str, "file": Path}


def get_param_model(
    method_name: str,
    param_docs: List[MetaKeggPipelineInputParamDocItem],
    make_all_params_optional: bool = False,
    file_params: Optional[bool] = None,
) -> Type[BaseModel]:
    params = {}
    """from pydantic create_model docs:
            **field_definitions: Attributes of the new model. They should be passed in the format:
            `<name>=(<type>, <default value>)`, `<name>=(<type>, <FieldInfo>)`, or `typing.Annotated[<type>, <FieldInfo>]`.
            Any additional metadata in `typing.Annotated[<type>, <FieldInfo>, ...]` will be ignored.
    """

    for par_doc in param_docs:
        if file_params == False and par_doc.type == "file":
            continue
        if file_params == True and par_doc.type != "file":
            continue
        type_annotation = param_types_map[par_doc.type]
        if par_doc.is_list:
            type_annotation = List[type_annotation]
        if not par_doc.required or make_all_params_optional:
            type_annotation = Optional[type_annotation]
        if par_doc.name in [
            f.name for f in MetaKeggPipelineInputParamsDefaultValOverrideFactory
        ]:
            default_factory = MetaKeggPipelineInputParamsDefaultValOverrideFactory[
                par_doc.name
            ].value.func
            field = Field(
                default_factory=default_factory, description=par_doc.description
            )
            params[par_doc.name] = (type_annotation, field)
        elif make_all_params_optional:
            default = None if par_doc.default == UNSET else par_doc.default
            field = Field(default=default, description=par_doc.description)
            params[par_doc.name] = (type_annotation, field)
        elif par_doc.default == UNSET:
            params[par_doc.name] = (
                type_annotation,
                Field(description=par_doc.description),
            )
        else:
            params[par_doc.name] = (
                type_annotation,
                Field(default=par_doc.default, description=par_doc.description),
            )

    return create_model(f"{method_name}Params", **params)


def _get_param_doc(
    name: str,
    annotation: Any,
    default: Any,
    is_optional: bool = False,
    is_list: bool = False,
    is_override: bool = False,
) -> MetaKeggPipelineInputParamDocItem:
    if (
        name in [o.name for o in MetaKeggPipelineInputParamsDocsTypeOverride]
        and not is_override
    ):
        return _get_param_doc(
            name,
            MetaKeggPipelineInputParamsDocsTypeOverride[name].value,
            default=default,
            is_override=True,
        )

    if (
        get_origin(annotation) == Union
        and len(list(get_args(annotation))) == 2
        and get_args(annotation)[1] == type(None)
    ):
        # We have an "Optional" annotation
        # UNder the hood "Optional" is Union[<ActualType>, None]
        # Union and len(get_args(annotation)) == 2 and get_args(annotation)[1] is None == Optional
        annotation = get_args(annotation)[0]
        return _get_param_doc(
            name,
            annotation,
            default,
            is_optional=True,
            is_list=is_list,
            is_override=is_override,
        )
    if get_origin(annotation) == Union:
        # we dont handle Union options. we just take the first option into account or the non str one
        if get_args(annotation)[0] == str:
            annotation = get_args(annotation)[1]
        else:
            annotation = get_args(annotation)[0]
        return _get_param_doc(
            name,
            annotation,
            default,
            is_optional=is_optional,
            is_list=is_list,
            is_override=is_override,
        )
    if get_origin(annotation) == list:
        annotation = get_args(annotation)[0]
        return _get_param_doc(
            name,
            annotation,
            default,
            is_optional=is_optional,
            is_list=True,
            is_override=is_override,
        )
    return MetaKeggPipelineInputParamDocItem(
        name=name,
        type=next(k for k, v in param_types_map.items() if v == annotation),
        required=not is_optional,
        is_list=is_list,
        default=default,
        description=(
            MetaKeggPipelineInputParamsDesc[name]
            if name in [p.name for p in MetaKeggPipelineInputParamsDesc]
            else None
        ),
    )


def get_param_docs(
    analyses_method: Awaitable | Callable | partial,
) -> List[MetaKeggPipelineInputParamDocItem]:
    if isinstance(analyses_method, partial):
        analyses_method = analyses_method.func
    params: List[MetaKeggPipelineInputParamDocItem] = []
    for name, type_hint in get_type_hints(analyses_method).items():
        if name in metaKegg_param_exclude:
            continue
        if name == "return":
            continue
        default = UNSET
        param = inspect.signature(analyses_method).parameters.get(name)
        if param and param.default is not inspect.Parameter.empty:
            default = param.default
        doc = _get_param_doc(name, type_hint, default=default)
        params.append(doc)
    return params


def find_parameter_docs_by_name(
    param_name: str,
) -> MetaKeggPipelineInputParamDocItem | None:
    # search in global params
    param_docs = get_param_docs(PipelineAsync.__init__)
    for param_doc in param_docs:
        if param_doc.name == param_name:
            return param_doc
    # search in analyses methods
    for analyses_method in MetaKeggPipelineAnalysisMethods:
        param_docs = get_param_docs(analyses_method.value)
        for param_doc in param_docs:
            if param_doc.name == param_name:
                return param_doc


GlobalParamModel: Type[BaseModel] = get_param_model(
    "Global", get_param_docs(PipelineAsync.__init__)
)
GlobalParamModelOptional: Type[BaseModel] = get_param_model(
    "Global",
    get_param_docs(PipelineAsync.__init__),
    make_all_params_optional=True,
    file_params=False,
)


class MetaKeggPipelineInputParamsValues(BaseModel):
    global_params: GlobalParamModelOptional = Field()
    method_specific_params: Dict[str, Any] = Field(default_factory=dict)


class MetaKeggPipelineInputParamsValuesAllOptional(BaseModel):
    global_params: GlobalParamModelOptional = Field()
    method_specific_params: Dict[str, Any] = Field(default_factory=dict)


MetaKeggPipelineDefStates = Literal[
    "initialized", "queued", "running", "failed", "success", "expired"
]


class MetaKeggPipelineDef(BaseModel):
    ticket: MetaKeggPipelineTicket
    state: MetaKeggPipelineDefStates = Field(
        default="initialized",
        description=f"When a new pipeline run is started it will be `queued` first. After there is slot free in the background worker it start `running`. based on the failure or success of this run the state will be `failed` or `success`. The result of a pipeline run will be cleaned/deleted after {config.PIPELINE_RESULT_EXPIRED_AFTER_MIN} minutes and not be available anymore. After that the state will be `expired`",
    )
    place_in_queue: Optional[int] = Field(
        default=None,
        description="Shows how many pipeline runs are ahead of a queued pipeline-run",
        examples=[4],
    )
    error: Optional[str] = Field(
        default=None,
        description="If the state of a pipeline run is `failed`, the error message will be logged into this attribute",
        examples=[None],
    )
    error_traceback: Optional[str] = Field(
        default=None,
        description="If the state of a pipeline run is `failed`, the error traceback will be logged into this attribute",
        examples=[None],
    )
    output_log: Optional[str] = Field(
        default=None, description="Output prints of a MetaKegg Pipeline analysis run."
    )
    result_path: Optional[str] = Field(
        default=None,
        description="If the state of a pipeline run is `success`, the result can be downloaded from this path.",
        examples=[None],
    )
    pipeline_params: MetaKeggPipelineInputParamsValuesAllOptional
    pipeline_analyses_method: MetaKeggPipelineAnalysisMethod | None = None
    pipeline_input_file_names: Optional[Dict[str, List[str]]] = Field(
        description="Uploaded file per parameter", default_factory=dict
    )
    pipeline_output_zip_file_name: Optional[str] = Field(default=None)
    created_at_utc: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(tz=datetime.timezone.utc)
    )
    queued_at_utc: Optional[datetime.datetime] = Field(default=None)
    started_at_utc: Optional[datetime.datetime] = Field(default=None)
    finished_at_utc: Optional[datetime.datetime] = Field(default=None)

    def get_files_base_dir(self) -> Path:
        return Path(PurePath(config.PIPELINE_RUNS_CACHE_DIR, self.ticket.id.hex))

    def get_input_files_base_dir(self) -> Path:
        return Path(PurePath(self.get_files_base_dir(), "input"))

    def get_input_file_dir(self, parameter: str) -> Path:
        return Path(PurePath(self.get_input_files_base_dir(), parameter))

    def get_input_files_path(
        self, parameter: str, filename: str = None, not_exists_ok: bool = True
    ) -> Optional[Path]:
        basepath = self.get_input_file_dir(parameter)
        result = next(
            (
                Path(PurePath(basepath, file))
                for file in self.pipeline_input_file_names[parameter]
                if file == filename
            ),
            None,
        )
        if result is None and not not_exists_ok:
            raise ValueError(
                f"Can not find any file for parameter '{parameter}' with name '{filename}' at basepath '{basepath.absolute()}'"
            )
        return result

    def get_input_existing_files_pathes(
        self,
        parameter: str,
    ) -> List[Path]:
        basepath = self.get_input_file_dir(parameter)
        return [
            Path(PurePath(basepath, parameter, filename))
            for filename in self.pipeline_input_file_names
        ]

    def get_output_files_dir(self) -> Path:
        return Path(PurePath(self.get_files_base_dir(), "output"))

    def get_output_zip_file_path(self) -> Path | None:
        # f"output-metakegg-{self.pipeline_analyses_method.name}_{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}.zip"
        if self.pipeline_output_zip_file_name is None:
            return None
        return Path(
            PurePath(
                self.get_output_files_dir(),
                self.pipeline_output_zip_file_name,
            )
        )

    def generate_output_zip_file_name(self) -> str:
        return f"output-metakegg-{self.pipeline_analyses_method.name}_{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.zip"


class MetaKeggPipelineStatisticPoint(BaseModel):

    pipeline_waiting_time_sec: int
    pipeline_running_duration_sec: int
    pipeline_failed: bool = False
    pipeline_methodname: str
    pipeline_finished_at: datetime.datetime
    input_files_amount: int
    input_files_size_bytes: int
    result_file_size_bytes: Optional[int]


class MetaKeggPipelineStatistics(BaseModel):
    statistics_from: Optional[datetime.datetime] = None
    statistics_to: Optional[datetime.datetime] = None
    total_pipelines_runs_amount: int = 0
    total_pipelines_run_successful_amount: int = 0
    total_pipelines_run_failed_amount: int = 0
    total_input_files_amount_processed: int = 0
    total_pipeline_runs_per_methodname: Dict[str, int] = Field(default_factory=dict)
    average_waiting_time_sec: int = 0
    average_running_time_sec: int = 0
    average_files_input_amount: float = 0.0
    average_files_input_size_bytes: float = 0.0
    average_result_file_size_bytes: float = 0.0
