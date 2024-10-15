from typing import Literal, Optional
from pydantic import BaseModel, Field
import uuid
from mekeweserver.config import Config

config = Config()


class PipelineInputParams(BaseModel):
    sheet_name_paths: str = Field(
        "pathways", description="Sheet name containing pathway information."
    )
    sheet_name_genes: str = Field(description=" Sheet name containing gene information")
    genes_column: str = Field(
        description=" Column name for genes in in the sheet_name_genes"
    )
    log2fc_column: str = Field(
        description=" Column name for log2 fold change in in the sheet_name_genes"
    )
    analysis_type: int = Field(description=" Type of analysis to be performed")
    input_label: str | list = Field(
        description=" Label or list of labels for the input files"
    )
    methylation_path: str = Field(description=" Path to the methylation file")
    methylation_pvalue: str = Field(
        description=" Column name for p-value in methylation file"
    )
    methylation_genes: str = Field(
        description=" Column name for genes in methylation file"
    )
    methylation_pvalue_thresh: float = Field(
        description=" Threshold for methylation p-value"
    )
    miRNA_path: str = Field(description=" Path to the miRNA file")
    miRNA_pvalue: str = Field(description=" Column name for p-value in miRNA file")
    miRNA_genes: str = Field(description=" Column name for genes in miRNA file")
    miRNA_pvalue_thresh: float = Field(description=" Threshold for miRNA p-value")
    folder_extension: str = Field(description=" Extension for the output folder")


class PipelineRunTicket(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)


class PipelineRunStatus(BaseModel):
    ticket_id: uuid.UUID
    state: Literal["queued", "running", "failed", "success", "expired"] = Field(
        default="queued",
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
