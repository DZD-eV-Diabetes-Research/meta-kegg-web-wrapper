from typing import Annotated, Optional, Dict, List, Type
import os
import pydantic
import uuid
from fastapi import (
    FastAPI,
    APIRouter,
    File,
    UploadFile,
    Query,
    Form,
    HTTPException,
    status,
    Request,
)
from slowapi import Limiter
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field


from mekeweserver.config import Config

config = Config()


from mekeweserver.model import PipelineInputParams, PipelineRunTicket, PipelineRunStatus


def http_exception_to_resp_desc(
    e: HTTPException,
) -> Dict[int, Dict[str, str | Type[pydantic.BaseModel]]]:
    """Translate a fastapi.HTTPException into fastapi OpenAPI response description to be used as a additional response
    https://fastapi.tiangolo.com/advanced/additional-responses/
    """
    return {
        e.status_code: {
            "description": e.detail,
            "model": pydantic.create_model("Error", detail=(Dict[str, str], e.detail)),
        },
    }


pipelinerun_not_found_expection = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Pipeline-run could not be found.",
)
pipelinerun_expired_expection = HTTPException(
    status_code=status.HTTP_410_GONE,
    detail="Pipeline-run expired and result is cleaned.",
)
pipelinerun_not_finished_expection = HTTPException(
    status_code=status.HTTP_425_TOO_EARLY,
    detail="Pipeline-run is not finished.",
)
pipelinerun_failed_expection = HTTPException(
    status_code=status.HTTP_424_FAILED_DEPENDENCY,
    detail="Pipeline-run failed.",
)
pipeline_status_exceptions: List[HTTPException] = [
    pipelinerun_not_found_expection,
    pipelinerun_expired_expection,
    pipelinerun_not_finished_expection,
    pipelinerun_failed_expection,
]
pipeline_status_exceptions_reponse_models: Dict[
    int, Dict[str, str | Type[pydantic.BaseModel]]
] = {}
for e in pipeline_status_exceptions:
    pipeline_status_exceptions_reponse_models.update(http_exception_to_resp_desc(e))


def get_routes(app: FastAPI):
    mekewe_router: APIRouter = APIRouter()
    limiter: Limiter = app.state.limiter

    @mekewe_router.post(
        "/pipeline",
        response_model=PipelineRunTicket,
        description="Trigger a meta Kegg pipeline run. The pipeline-run will not start immediatily but be queued. The response of this endpoint will be a ticket that can be used to track the status of your pipeline run.",
        tags=["Pipeline"],
    )
    @limiter.limit(f"{config.MAX_PIPELINE_RUNS_PER_HOUR_PER_IP}/hour")
    async def start_meta_kegg_pipeline_run(
        request: Request,
        file: UploadFile = File(...),
        pipeline_params: Annotated[PipelineInputParams, Form()] = None,
    ):
        return PipelineRunTicket()

    @mekewe_router.get(
        "/pipeline/{pipeline_ticket_id}/status",
        response_model=PipelineRunStatus,
        responses=http_exception_to_resp_desc(pipelinerun_not_found_expection),
        description="Check the status of a triggered pipeline run.",
        tags=["Pipeline"],
    )
    @limiter.limit(f"1/second")
    async def get_pipeline_run_status(
        request: Request,
        pipeline_ticket_id: uuid.UUID,
    ):
        return PipelineRunStatus()

    @mekewe_router.get(
        "/pipeline/{pipeline_ticket_id}/result",
        response_class=FileResponse,
        description="Download the result of a succeded pipeline run.",
        responses=pipeline_status_exceptions_reponse_models,
        tags=["Pipeline"],
    )
    @limiter.limit(f"10/hour")
    async def download_pipeline_run_result(
        request: Request,
        pipeline_ticket_id: uuid.UUID,
    ):
        return PipelineRunStatus()

    @mekewe_router.get(
        "/{path_name:path}", description="Client serving path", tags=["Webclient"]
    )
    async def serve_frontend(path_name: Optional[str] = None):
        if path_name:
            file = os.path.join(config.FRONTEND_FILES_DIR, path_name)
        else:
            file = os.path.join(config.FRONTEND_FILES_DIR, "index.html")
        return FileResponse(file)

    return mekewe_router
