from typing import (
    Annotated,
    Optional,
    Dict,
    List,
    Type,
    Literal,
    get_origin,
    get_args,
    Union,
)
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
from multiprocessing import Process

from mekeweserver.config import Config
from mekeweserver.db import get_redis_client
from mekeweserver.pipeline_status_clerk import MetaKeggPipelineStateManager

config = Config()


from mekeweserver.model import (
    MetaKeggPipelineInputParams,
    MetaKeggPipelineInputParamsUpdate,
    MetaKeggPipelineTicket,
    MetaKeggPipelineDef,
    MetaKeggPipelineAnalysisMethods,
    MetaKeggPipelineAnalysisMethod,
    MetaKeggWebServerHealthState,
    MetaKeggWebServerModuleHealthState,
    MetaKeggClientConfig,
    MetaKeggClientLink,
)


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


pipelinerun_not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Pipeline-run could not be found.",
)
pipelinerun_expired_exception = HTTPException(
    status_code=status.HTTP_410_GONE,
    detail="Pipeline-run expired and result is cleaned.",
)
pipelinerun_not_finished_exception = HTTPException(
    status_code=status.HTTP_425_TOO_EARLY,
    detail="Pipeline-run is not finished.",
)
pipelinerun_failed_exception = HTTPException(
    status_code=status.HTTP_424_FAILED_DEPENDENCY,
    detail="Pipeline-run failed. Check endpoint '/pipeline/{pipeline_ticket_id}/status' for details",
)
pipeline_status_exceptions: List[HTTPException] = [
    pipelinerun_not_found_exception,
    pipelinerun_expired_exception,
    pipelinerun_not_finished_exception,
    pipelinerun_failed_exception,
]
pipeline_status_exceptions_reponse_models: Dict[
    int, Dict[str, str | Type[pydantic.BaseModel]]
] = {}
for e in pipeline_status_exceptions:
    pipeline_status_exceptions_reponse_models.update(http_exception_to_resp_desc(e))


def get_api_router(app: FastAPI) -> APIRouter:
    mekewe_router: APIRouter = APIRouter(prefix="/api")
    limiter: Limiter = app.state.limiter
    redis = get_redis_client()

    ##ENDPOINT: /analysis
    @mekewe_router.get(
        "/analysis",
        response_model=List[MetaKeggPipelineAnalysisMethod],
        description="List all MetaKEGG analysis methods available. The name will be used to start a analysis pipeline run in endpoint `/pipeline/{pipeline_ticket_id}/run/...`",
        tags=["Analysis Method"],
    )
    @limiter.limit(f"6/second")
    async def list_available_analysis_methods(
        request: Request,
    ):
        return [e.value for e in MetaKeggPipelineAnalysisMethods]

    ##ENDPOINT: /analysis
    @mekewe_router.get(
        "/params",
        response_model=Dict[str, Dict[str, str | int | float | bool]],
        description="List all MetaKEGG parameters available.",
        tags=["Analysis Method"],
    )
    @limiter.limit(f"6/second")
    async def list_available_analysis_parameters(
        request: Request,
    ):
        attributes = {}

        for field_name, field_info in MetaKeggPipelineInputParams.model_fields.items():
            required = True
            # Fetch the type name and default value of each param field
            field_type = field_info.annotation
            if get_origin(field_type) is Union:
                required = False
                field_type = get_args(field_type)[0]

            attributes[field_name] = {"type": field_type.__name__, "required": required}
            field_default = field_info.default
            if field_default:
                attributes[field_name]["default"] = field_default
        return attributes

    ##ENDPOINT: /pipeline
    @mekewe_router.post(
        "/pipeline",
        response_model=MetaKeggPipelineTicket,
        description="Define a new meta Kegg pipeline run. The pipeline-run will not start immediatily but be queued. The response of this endpoint will be a ticket that can be used to track the status of your pipeline run.",
        tags=["Pipeline"],
    )
    @limiter.limit(f"{config.MAX_PIPELINE_RUNS_PER_HOUR_PER_IP}/hour")
    async def initialize_a_metakegg_pipeline_run_definition(
        request: Request,
        pipeline_params: Annotated[MetaKeggPipelineInputParams, Query()] = None,
    ) -> MetaKeggPipelineTicket:
        ticket: MetaKeggPipelineTicket = MetaKeggPipelineStateManager(
            redis_client=redis
        ).init_new_pipeline_run(pipeline_params)
        return ticket

    ##ENDPOINT: /pipeline/{pipeline_ticket_id}
    @mekewe_router.patch(
        "/pipeline/{pipeline_ticket_id}",
        response_model=MetaKeggPipelineDef,
        description="Update the pipeline params of an allready existing pipeline run definition. The pipeline must not be started via `/pipeline/{pipeline_ticket_id}/run/{analysis_method_name}` allready.",
        tags=["Pipeline"],
    )
    @limiter.limit(f"10/minute")
    async def update_a_metakegg_pipeline_run_definition(
        request: Request,
        pipeline_ticket_id: uuid.UUID,
        pipeline_params: Annotated[MetaKeggPipelineInputParamsUpdate, Query()] = None,
    ) -> MetaKeggPipelineDef:
        pipeline_status: MetaKeggPipelineDef = MetaKeggPipelineStateManager(
            redis_client=redis
        ).get_pipeline_status(
            pipeline_ticket_id,
            raise_exception_if_not_exists=pipelinerun_not_found_exception,
        )
        if pipeline_status.state != "initialized":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pipeline is not in an updatable state anymore",
            )
        for key, val in pipeline_params.model_dump(exclude_unset=True).items():
            setattr(pipeline_status.pipeline_params, key, val)
        MetaKeggPipelineStateManager(redis_client=redis).set_pipeline_status(
            pipeline_status,
        )
        return pipeline_status

    ##ENDPOINT: /pipeline/{pipeline_ticket_id}/upload
    @mekewe_router.post(
        "/pipeline/{pipeline_ticket_id}/upload",
        response_model=MetaKeggPipelineDef,
        description="Add a file to an non started/queued pipeline-run definition",
        tags=["Pipeline"],
    )
    @limiter.limit(f"5/minute")
    async def attach_file_to_meta_kegg_pipeline_run_definition(
        request: Request,
        pipeline_ticket_id: uuid.UUID,
        file: UploadFile = File(...),
    ) -> MetaKeggPipelineDef:
        return MetaKeggPipelineStateManager(redis_client=redis).attach_input_file(
            pipeline_ticket_id, file
        )

    analysis_method_names_type_hint = Literal[
        tuple([str(e.name) for e in MetaKeggPipelineAnalysisMethods])
    ]

    ##ENDPOINT: /pipeline/{pipeline_ticket_id}/run/{analysis_method_name}
    @mekewe_router.post(
        "/pipeline/{pipeline_ticket_id}/run/{analysis_method_name}",
        response_model=MetaKeggPipelineDef,
        responses=http_exception_to_resp_desc(pipelinerun_not_found_exception),
        description="Qeueu the pipeline-run. If the queue is passed the pipeline will change from 'queued' into 'running' state.",
        tags=["Pipeline"],
    )
    @limiter.limit(f"1/second")
    async def start_pipeline_run(
        request: Request,
        pipeline_ticket_id: uuid.UUID,
        analysis_method_name: analysis_method_names_type_hint,
    ) -> MetaKeggPipelineDef:
        return MetaKeggPipelineStateManager(
            redis_client=redis
        ).set_pipeline_run_as_queud(
            pipeline_ticket_id, analysis_method_name=analysis_method_name
        )

    ##ENDPOINT: /pipeline/{pipeline_ticket_id}/status
    @mekewe_router.get(
        "/pipeline/{pipeline_ticket_id}/status",
        response_model=MetaKeggPipelineDef,
        responses=http_exception_to_resp_desc(pipelinerun_not_found_exception),
        description="Check the status of a triggered pipeline run.",
        tags=["Pipeline"],
    )
    @limiter.limit(f"2/second")
    async def get_pipeline_run_status(
        request: Request,
        pipeline_ticket_id: uuid.UUID,
    ):
        status: MetaKeggPipelineDef = MetaKeggPipelineStateManager(
            redis_client=redis
        ).get_pipeline_status(pipeline_ticket_id)
        return status

    ##ENDPOINT: /pipeline/{pipeline_ticket_id}/result
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
        status: MetaKeggPipelineDef | None = MetaKeggPipelineStateManager(
            redis_client=redis
        ).get_pipeline_status(pipeline_ticket_id)
        if status is None:
            raise pipelinerun_not_found_exception
        if status.state == "failed":
            raise pipelinerun_failed_exception
        elif status.state in ["initialized", "running", "queued"]:
            raise pipelinerun_not_finished_exception
        elif status.state == "expired":
            raise pipelinerun_expired_exception
        print("pipeline_output_zip_file_name", status.pipeline_output_zip_file_name)
        return FileResponse(
            status.get_output_zip_file_path(),
            filename=status.get_output_zip_file_path().name,
        )

    return mekewe_router


def get_client_router(app: FastAPI) -> APIRouter:
    mekeweclient_router: APIRouter = APIRouter()

    @mekeweclient_router.get(
        "/{path_name:path}", description="Client serving path", tags=["Webclient"]
    )
    async def serve_frontend(path_name: Optional[str] = None):
        if path_name:
            file = os.path.join(config.FRONTEND_FILES_DIR, path_name)
        else:
            file = os.path.join(config.FRONTEND_FILES_DIR, "index.html")
        return FileResponse(file)

    return mekeweclient_router


def get_health_router(app: FastAPI, background_worker_process: Process) -> APIRouter:
    mekeweclient_health_router: APIRouter = APIRouter()
    redis = get_redis_client()
    limiter: Limiter = app.state.limiter

    @mekeweclient_health_router.get(
        "/health",
        response_model=MetaKeggWebServerHealthState,
        description="Check if server is running normal",
        tags=["Health"],
    )
    @limiter.limit(f"30/minute")
    async def get_health_state(
        request: Request,
    ) -> MetaKeggWebServerHealthState:
        overall_state = MetaKeggWebServerHealthState(healthy=True, dependencies=[])

        background_worker_state = MetaKeggWebServerModuleHealthState(
            name="worker", healthy=background_worker_process.is_alive()
        )
        if background_worker_state.healthy == False:
            overall_state.healthy = False
        overall_state.dependencies.append(background_worker_state)

        cache_server_state = MetaKeggWebServerModuleHealthState(
            name="cache", healthy=False
        )
        try:
            redis.ping()
            cache_server_state.healthy = True
        except:
            overall_state.healthy = False
        overall_state.dependencies.append(cache_server_state)
        return overall_state

    return mekeweclient_health_router


def get_info_config_router(app: FastAPI) -> APIRouter:
    mekeweclient_info_router: APIRouter = APIRouter()
    redis = get_redis_client()
    limiter: Limiter = app.state.limiter

    @mekeweclient_info_router.get(
        "/config",
        response_model=MetaKeggClientConfig,
        description="Get some infos and config for the client",
        tags=["Config/Infos"],
    )
    @limiter.limit(f"30/minute")
    async def get_config(
        request: Request,
    ) -> MetaKeggClientConfig:

        return MetaKeggClientConfig(
            contact_email=config.CLIENT_CONTACT_EMAIL,
            bug_report_email=(
                config.CLIENT_BUG_REPORT_EMAIL
                if config.CLIENT_BUG_REPORT_EMAIL is not None
                else config.CLIENT_CONTACT_EMAIL
            ),
            terms_and_conditions=config.CLIENT_TERMS_AND_CONDITIONS,
            pipeline_ticket_expire_time_sec=config.PIPELINE_RESULT_EXPIRED_AFTER_MIN
            * 60,
        )

    @mekeweclient_info_router.get(
        "/info-links",
        response_model=List[MetaKeggClientLink],
        description="Get some infos and config for the client",
        tags=["Config/Infos"],
    )
    @limiter.limit(f"30/minute")
    async def get_links(
        request: Request,
    ) -> List[MetaKeggClientLink]:
        res = []
        print("config.CLIENT_LINK_LIST", config.CLIENT_LINK_LIST)
        for link in config.CLIENT_LINK_LIST:
            print("link", link)
            res.append(MetaKeggClientLink(**link))
        return res

    return mekeweclient_info_router
