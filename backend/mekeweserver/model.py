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

config: Config = get_config()


class MetaKeggPipelineAnalysisMethods(Enum):
    single_input_genes = partial(PipelineAsync.single_input_genes)
    single_input_transcripts = partial(PipelineAsync.single_input_transcripts)
    single_input_genes_bulk_mapping = partial(
        PipelineAsync.single_input_genes_bulk_mapping
    )
    multiple_inputs = partial(PipelineAsync.multiple_inputs)
    single_input_with_methylation = partial(PipelineAsync.single_input_with_methylation)
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


class MetaKeggPipelineAnalysisMethod(BaseModel):
    name: str
    display_name: str
    internal_id: int
    desc: Optional[str] = None

    def get_params_docs(self) -> List["MetaKeggPipelineInputParamDocItem"]:
        return get_param_docs(self.method)


class MetaKeggPipelineAnalysisMethodDocs(Enum):
    single_input_genes = MetaKeggPipelineAnalysisMethod(
        name="single_input_genes",
        display_name="Gene expression",
        internal_id=1,
        desc="Perform the Single Input Analysis for Gene IDs.",
    )
    single_input_transcripts = MetaKeggPipelineAnalysisMethod(
        name="single_input_transcripts",
        display_name="Transcript expression",
        internal_id=2,
        desc="Perform the Single Input Analysis for Transcript IDs.",
    )
    single_input_genes_bulk_mapping = MetaKeggPipelineAnalysisMethod(
        name="single_input_genes_bulk_mapping",
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
    single_input_with_methylation = MetaKeggPipelineAnalysisMethod(
        name="single_input_with_methylation",
        display_name="Methylated genes",
        internal_id=5,
        desc="Perform Single Input Analysis with Methylation.",
    )
    single_input_with_methylation_quantification = MetaKeggPipelineAnalysisMethod(
        name="single_input_with_methylation_quantification",
        display_name="DMPs per gene",
        internal_id=6,
        desc="Perform Single Input Analysis with methylation quantification.",
    )
    single_input_with_miRNA = MetaKeggPipelineAnalysisMethod(
        name="single_input_with_miRNA",
        display_name="miRNA target genes",
        internal_id=7,
        desc="Perform Single Input Analysis with miRNA.",
    )
    single_input_with_miRNA_quantification = MetaKeggPipelineAnalysisMethod(
        name="single_input_with_miRNA_quantification",
        display_name="DEmiRs per gene",
        internal_id=8,
        desc="Perform Single Input Analysis with miRNA.",
    )
    single_input_with_methylation_and_miRNA = MetaKeggPipelineAnalysisMethod(
        name="single_input_with_methylation_and_miRNA",
        display_name="Methylated + miRNA target genes",
        internal_id=9,
        desc="Perform Single Input Analysis with miRNA.",
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
    pathway_pvalue = "Raw p-value threshold for the pathways"
    input_label = "TODO: @Michail: Is this really a global param or only used for 'multiple_inputs'? (see https://github.com/dife-bioinformatics/metaKEGG/blob/master/src/metaKEGG/modules/pipeline_async.py#L196) Input label or list of labels for multiple inputs"
    folder_extension = "Folder extension to be appended to the default naming scheme. If None and default folder exists, will overwrite folder"
    methylation_path = "Path to methylation data (Excel , CSV or TSV format)"
    methylation_pvalue = "Column name for methylation p-value"
    methylation_genes = "Column name for methylation gene symbols"
    methylation_pvalue_thresh = "P-value threshold for the methylation values"
    methylation_probe_column = "Column name for the methylation probes."
    probes_to_cgs = "If True, will correct the probes to positions, delete duplicated positions and keep the first CG."
    miRNA_path = "Path to miRNA data (Excel , CSV or TSV format)"
    miRNA_pvalue = "Column name for miRNA p-value"
    miRNA_genes = "Column name for miRNA gene symbols"
    miRNA_pvalue_thresh = "P-value threshold for the miRNA values"
    miRNA_ID_column = "Column name for the miRNA IDs."
    benjamini_threshold = "Benjamini Hochberg p-value threshold for the pathway"
    save_to_eps = "True/False statement to save the maps and colorscales or legends as seperate .eps files in addition to the .pdf exports"
    compounds_list = "List of compound IDs to mapped in pathways if found."


# some params need special handling and will not be presented to the api
metaKegg_param_exclude = ["folder_extension", "output_folder_name"]


class MetaKeggPipelineInputParamsDocsTypeOverride(Enum):
    input_file_path = List[Path]
    input_label = List[str]


param_types_map = {"int": int, "bool": bool, "float": float, "str": str, "file": Path}


def get_param_model(
    method_name: str,
    param_docs: List[MetaKeggPipelineInputParamDocItem],
    make_all_params_optional: bool = False,
    exclude_file_params: bool = False,
) -> Type[BaseModel]:
    params = {}
    """from pydantic create_model docs:
            **field_definitions: Attributes of the new model. They should be passed in the format:
            `<name>=(<type>, <default value>)`, `<name>=(<type>, <FieldInfo>)`, or `typing.Annotated[<type>, <FieldInfo>]`.
            Any additional metadata in `typing.Annotated[<type>, <FieldInfo>, ...]` will be ignored.
    """

    for par_doc in param_docs:
        if exclude_file_params and par_doc.type == "file":
            continue
        type_annotation = param_types_map[par_doc.type]
        if par_doc.is_list:
            type_annotation = List[type_annotation]
        if not par_doc.required or make_all_params_optional:
            type_annotation = Optional[type_annotation]
        if make_all_params_optional:
            default = None if par_doc.default == UNSET else par_doc.default
            params[par_doc.name] = (
                type_annotation,
                Field(default=default, description=par_doc.description),
            )
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
    obj: Awaitable | Callable,
) -> List[MetaKeggPipelineInputParamDocItem]:
    params: List[MetaKeggPipelineInputParamDocItem] = []
    for name, type_hint in get_type_hints(obj).items():
        if name in metaKegg_param_exclude:
            continue
        if name == "return":
            continue
        default = UNSET
        param = inspect.signature(obj).parameters.get(name)
        if param and param.default is not inspect.Parameter.empty:
            default = param.default
        doc = _get_param_doc(name, type_hint, default=default)
        params.append(doc)
    return params


GlobalParamModel: Type[BaseModel] = get_param_model(
    "Global", get_param_docs(PipelineAsync.__init__)
)
GlobalParamModelUpdate: Type[BaseModel] = get_param_model(
    "Global",
    get_param_docs(PipelineAsync.__init__),
    make_all_params_optional=True,
    exclude_file_params=True,
)


class MetaKeggPipelineInputParamsValues(BaseModel):
    global_params: GlobalParamModel = Field()
    method_specific_params: Dict[str, Any] = Field(default_factory=dict)


class MetaKeggPipelineInputParamsValuesUpdate(BaseModel):
    global_params: GlobalParamModelUpdate = Field()
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
    pipeline_params: MetaKeggPipelineInputParamsValues
    pipeline_analyses_method: MetaKeggPipelineAnalysisMethod | None = None
    pipeline_input_file_names: Dict[str, List[str]] = Field(
        description="Uploaded file per parameter", default_factory=dict
    )
    pipeline_output_zip_file_name: Optional[str] = Field(default=None)
    created_at_utc: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(tz=datetime.timezone.utc)
    )
    started_at_utc: Optional[datetime.datetime] = Field(default=None)
    finished_at_utc: Optional[datetime.datetime] = Field(default=None)

    def get_files_base_dir(self) -> Path:
        return Path(PurePath(config.PIPELINE_RUNS_CACHE_DIR, self.ticket.id.hex))

    def get_input_files_path(
        self, parameter: str, filename: str = None
    ) -> Optional[Path]:
        basepath = self.get_input_file_dir()
        return next(
            (
                Path(PurePath(basepath, parameter, file))
                for file in self.pipeline_input_file_names
                if file == filename
            ),
            None,
        )

    def get_input_files_pathes(
        self,
        parameter: str,
    ) -> List[Path]:
        basepath = self.get_input_file_dir()
        return [
            Path(PurePath(basepath, parameter, filename))
            for filename in self.pipeline_input_file_names
        ]

    def get_input_file_dir(self, parameter: str) -> Path:
        return Path(PurePath(self.get_files_base_dir(), "input", parameter))

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
