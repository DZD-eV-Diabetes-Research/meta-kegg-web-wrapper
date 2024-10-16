from typing import Literal, Optional, List
from typing_extensions import Self
from pydantic import BaseModel, Field, field_serializer
import uuid
from enum import Enum
from mekeweserver.config import Config

config = Config()


class MetaKeggPipelineAnalysisMethod(BaseModel):
    name: str
    display_name: str
    internal_id: int
    desc: Optional[str] = None


class MetaKeggPipelineAnalysisMethods(Enum):
    single_input_genes = MetaKeggPipelineAnalysisMethod(
        name="single_input_genes",
        display_name="Single Input Genes Analysis",
        internal_id=1,
        desc="Perform the Single Input Analysis for Gene IDs.",
    )
    single_input_transcripts = MetaKeggPipelineAnalysisMethod(
        name="single_input_transcripts",
        display_name="Single Input Transcripts Analysis",
        internal_id=2,
        desc="Perform the Single Input Analysis for Transcript IDs.",
    )
    single_input_genes_bulk_mapping = MetaKeggPipelineAnalysisMethod(
        name="single_input_genes_bulk_mapping",
        display_name="Single input genes bulk mapping Analysis",
        internal_id=3,
        desc="Perform a single input analysis with bulk mapping for genes.",
    )
    multiple_inputs = MetaKeggPipelineAnalysisMethod(
        name="multiple_inputs",
        display_name="multiple inputs Analysis",
        internal_id=4,
        desc="Perform the Multiple Inputs Analysis.",
    )
    single_input_with_methylation = MetaKeggPipelineAnalysisMethod(
        name="single_input_with_methylation",
        display_name="single input with methylation",
        internal_id=5,
        desc="Perform Single Input Analysis with Methylation.",
    )
    single_input_with_methylation_quantification = MetaKeggPipelineAnalysisMethod(
        name="single_input_with_methylation_quantification",
        display_name="single input with methylation quantification Analysis",
        internal_id=6,
        desc="Perform Single Input Analysis with methylation quantification.",
    )
    single_input_with_miRNA = MetaKeggPipelineAnalysisMethod(
        name="single_input_with_miRNA",
        display_name="single input with miRNA Analysis",
        internal_id=7,
        desc="Perform Single Input Analysis with miRNA.",
    )
    single_input_with_miRNA_quantification = MetaKeggPipelineAnalysisMethod(
        name="single_input_with_miRNA_quantification",
        display_name="single input with miRNA quantification Analysis",
        internal_id=8,
        desc="Perform Single Input Analysis with miRNA.",
    )
    single_input_with_methylation_and_miRNA = MetaKeggPipelineAnalysisMethod(
        name="single_input_with_methylation_and_miRNA",
        display_name="single input with methylation and miRNA Analysis",
        internal_id=9,
        desc="Perform Single Input Analysis with miRNA.",
    )


class MetaKeggPipelineInputParams(BaseModel):
    # input_file_path: str = Field(
    #    description="Path to the input file (Excel format) or list of input files. Can be a David analysis output, or RNAseq"
    # )
    sheet_name_paths: str = Field(
        default="pathways",
        description="Sheet name containing the pathway information (see docs). Has to apply to all input files in case of multiple.",
    )
    sheet_name_genes: str = Field(
        default="gene_metrics",
        description="Sheet name for gene information (see docs). Has to apply to all input files in case of multiple.",
    )
    genes_column: str = Field(
        default="gene_symbol",
        description="Column name for gene symbols in the sheet_name_genes",
    )
    log2fc_column: str = Field(
        default="logFC",
        description="Column name for log2fc values in the sheet_name_genes",
    )
    count_threshold: int = Field(
        default=2,
        description="Minimum number of genes per pathway, for pathway to be drawn. Default value : 2",
    )
    pathway_pvalue: float = Field(
        default=None, description="Raw p-value threshold for the pathways"
    )
    input_label: str = Field(
        default=None, description="Input label or list of labels for multiple inputs"
    )
    folder_extension: str = Field(
        default=None,
        description="Folder extension to be appended to the default naming scheme. If None and default folder exists, will overwrite folder",
    )
    methylation_path: str = Field(
        default=None, description="Path to methylation data (Excel , CSV or TSV format)"
    )
    methylation_pvalue: str = Field(
        default=None, description="Column name for methylation p-value"
    )
    methylation_genes: str = Field(
        default=None, description="Column name for methylation gene symbols"
    )
    methylation_pvalue_thresh: float = Field(
        default=0.05,
        description="P-value threshold for the methylation values",
    )
    methylation_probe_column: str = Field(
        default=None, description="Column name for the methylation probes."
    )
    probes_to_cgs: str = Field(
        default=False,
        description="If True, will correct the probes to positions, delete duplicated positions and keep the first CG.",
    )
    miRNA_path: str = Field(
        default=None, description="Path to miRNA data (Excel , CSV or TSV format)"
    )
    miRNA_pvalue: str = Field(default=None, description="Column name for miRNA p-value")
    miRNA_genes: str = Field(
        default=None, description="Column name for miRNA gene symbols"
    )
    miRNA_pvalue_thresh: float = Field(
        default=0.05, description="P-value threshold for the miRNA values"
    )
    miRNA_ID_column: str = Field(
        default=None, description="Column name for the miRNA IDs."
    )
    benjamini_threshold: float = Field(
        default=None,
        description="Benjamini Hochberg p-value threshold for the pathway",
    )
    save_to_eps: str = Field(
        default=False,
        description="True/False statement to save the maps and colorscales or legends as seperate .eps files in addition to the .pdf exports",
    )
    # output_folder_name: str = Field(
    #    default=None,
    #    description="Name of output folder. Will overpower default scheme. Combines with extension",
    # )


class PipelineRunTicket(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)


class PipelineRunStatus(BaseModel):

    state: Literal[
        "initialized", "queued", "running", "failed", "success", "expired"
    ] = Field(
        default="initialized",
        description=f"When a new pipeline run is started it will be `queued` first. After there is slot free in the background worker it start `running`. based on the failure or success of this run the state will be `failed` or `success`. The result of a pipeline run will be cleaned/deleted after {config.PURGE_PIPELINE_RESULT_AFTER_MIN} minutes and not be available anymore. After that the state will be `expired`",
    )
    place_in_queue: int = Field(
        default=None,
        description="Shows how many pipeline runs are ahead of a queued pipeline-run",
        examples=[4],
    )
    error: Optional[str] = Field(
        default=None,
        description="If the state of a pipeline run is `failed`, the error message will be logged into this attribute",
        examples=[None],
    )
    result_path: Optional[str] = Field(
        default=None,
        description="If the state of a pipeline run is `success`, the result can be downloaded from this path.",
        examples=[None],
    )
    ticket: PipelineRunTicket
    pipeline_params: MetaKeggPipelineInputParams
    pipeline_analyses_method: MetaKeggPipelineAnalysisMethod | None = None
    pipeline_input_files: List[str] = Field(default_factory=list)
