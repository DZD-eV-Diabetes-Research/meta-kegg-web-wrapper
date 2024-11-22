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
from pathlib import Path
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
    Body,
)
from slowapi import Limiter
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from multiprocessing import Process

from mekeweserver.config import Config, get_config
from mekeweserver.db import get_redis_client
from mekeweserver.pipeline_status_clerk import MetaKeggPipelineStateManager

config: Config = get_config()

from metaKEGG import PipelineAsync
from mekeweserver.model import (
    MetaKeggPipelineInputParamsDocs,
    MetaKeggPipelineTicket,
    MetaKeggPipelineDef,
    MetaKeggPipelineAnalysisMethodDocs,
    MetaKeggPipelineAnalysisMethod,
    MetaKeggWebServerHealthState,
    MetaKeggWebServerModuleHealthState,
    MetaKeggClientConfig,
    MetaKeggClientLink,
    MetaKeggPipelineInputParamDocItem,
    MetaKeggPipelineInputParamsDesc,
    MetaKeggPipelineAnalysisMethods,
    MetaKeggPipelineInputParamsValues,
    MetaKeggPipelineInputParamsValuesAllOptional,
    get_param_docs,
    get_param_model,
    GlobalParamModel,
    GlobalParamModelOptional,
    MetaKeggPipelineDefStates,
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

analyses_method_names = [e.name for e in MetaKeggPipelineAnalysisMethods]


def get_api_router(app: FastAPI) -> APIRouter:
    mekewe_router: APIRouter = APIRouter(prefix="/api")
    limiter: Limiter = app.state.limiter
    redis = get_redis_client()

    ##ENDPOINT: /analysis
    @mekewe_router.get(
        "/analysis",
        response_model=List[MetaKeggPipelineAnalysisMethod],
        description="List all MetaKEGG analysis methods available. The name will be used to start a analysis pipeline run in endpoint `/pipeline/{pipeline_ticket_id}/run/...`",
        tags=["Analysis Methods"],
    )
    @limiter.limit(f"6/second")
    async def list_available_analysis_methods(
        request: Request,
    ):
        return [e.value for e in MetaKeggPipelineAnalysisMethodDocs]

    ##ENDPOINT: /analysis
    @mekewe_router.get(
        "/{analysis_method_name}/params",
        response_model=MetaKeggPipelineInputParamsDocs,
        description="List all MetaKEGG parameters per analysis methods available. ",
        tags=["Analysis Methods"],
    )
    @limiter.limit(f"6/second")
    async def list_available_analysis_parameters(
        request: Request, analysis_method_name: Literal[tuple(analyses_method_names)]
    ) -> MetaKeggPipelineInputParamsDocs:
        if analysis_method_name not in analyses_method_names:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There is no analyses method with the name {analysis_method_name}",
            )
        return MetaKeggPipelineInputParamsDocs(
            global_params=get_param_docs(PipelineAsync.__init__),
            method_specific_params=get_param_docs(
                MetaKeggPipelineAnalysisMethods[analysis_method_name].value.func
            ),
        )

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
        pipeline_params: Annotated[
            Optional[MetaKeggPipelineInputParamsValuesAllOptional], Body()
        ] = None,
        # pipeline_params: Annotated[MetaKeggPipelineInputParamsDocs, Query()] = None,
    ) -> MetaKeggPipelineTicket:
        if pipeline_params is None:
            pipeline_params = MetaKeggPipelineInputParamsValuesAllOptional(
                global_params={}, method_specific_params={}
            )
        ticket: MetaKeggPipelineTicket = MetaKeggPipelineStateManager(
            redis_client=redis
        ).init_new_pipeline_run(pipeline_params)
        return ticket

    ##ENDPOINT: /pipeline/{pipeline_ticket_id}

    @mekewe_router.delete(
        "/pipeline/{pipeline_ticket_id}",
        description="""
        Delete an existing pipeline definiton with all input and output files.""",
        tags=["Pipeline"],
    )
    @limiter.limit(f"10/minute")
    async def delete_a_metakegg_pipeline_run_definition(
        request: Request,
        pipeline_ticket_id: uuid.UUID,
    ):
        pipeline_status_manager = MetaKeggPipelineStateManager(redis_client=redis)
        pipeline_status = pipeline_status_manager.get_pipeline_run_definition(
            pipeline_ticket_id,
            raise_exception_if_not_exists=pipelinerun_not_found_exception,
        )
        if pipeline_status.state in ["running", "queued"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pipeline is not in an updatable state. Wait for it to be finished.",
            )
        pipeline_status_manager.wipe_pipeline_run(pipeline_ticket_id)
        pipeline_status_manager.delete_pipeline_status(pipeline_ticket_id)

    @mekewe_router.patch(
        "/pipeline/{pipeline_ticket_id}",
        response_model=MetaKeggPipelineDef,
        description="""
        Update the pipeline params of an allready existing pipeline run definition. 
        The pipeline must **NOT** be started via `/pipeline/{pipeline_ticket_id}/run/{analysis_method_name}` allready. 
        Only provided params get updated. You dont have to supply all params every PATCH call.  
        For setting `file`-based parameters use the endpoint `/api/pipeline/{pipeline_ticket_id}/upload`""",
        tags=["Pipeline"],
    )
    @limiter.limit(f"10/minute")
    async def update_metakegg_pipeline_non_file_parameters(
        request: Request,
        pipeline_ticket_id: uuid.UUID,
        pipeline_params: Annotated[
            MetaKeggPipelineInputParamsValuesAllOptional, Body()
        ],
    ) -> MetaKeggPipelineDef:

        # get current params from db
        pipeline_status: MetaKeggPipelineDef = MetaKeggPipelineStateManager(
            redis_client=redis
        ).get_pipeline_run_definition(
            pipeline_ticket_id,
            raise_exception_if_not_exists=pipelinerun_not_found_exception,
        )

        # check if we still can update the pipeline params of if the pipeline is allready triggered
        if pipeline_status.state in ["queued", "running", "expired"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pipeline is not in an updatable state",
            )

        # Update the current state with new params that where supplied
        for key, val in pipeline_params.global_params.model_dump(
            exclude_unset=True
        ).items():
            setattr(pipeline_status.pipeline_params.global_params, key, val)
        for key, val in pipeline_params.method_specific_params.items():
            pipeline_status.pipeline_params.method_specific_params[key] = val

        # Save the new state to the db
        MetaKeggPipelineStateManager(redis_client=redis).set_pipeline_run_definition(
            pipeline_status,
        )
        return pipeline_status

    ##ENDPOINT: /pipeline/{pipeline_ticket_id}/upload
    @mekewe_router.post(
        "/pipeline/{pipeline_ticket_id}/file/upload/{param_name}",
        response_model=MetaKeggPipelineDef,
        description="Add a file to an non started/queued pipeline-run definition",
        tags=["Pipeline"],
    )
    @limiter.limit(f"5/minute")
    async def attach_file_to_meta_kegg_pipeline_run_definition(
        request: Request,
        pipeline_ticket_id: uuid.UUID,
        param_name: str,
        file: UploadFile = File(...),
    ) -> MetaKeggPipelineDef:
        return MetaKeggPipelineStateManager(
            redis_client=redis
        ).attach_pipeline_run_input_file(pipeline_ticket_id, param_name, file)

    analysis_method_names_type_hint = Literal[
        tuple([str(e.name) for e in MetaKeggPipelineAnalysisMethodDocs])
    ]

    ##ENDPOINT: /pipeline/{pipeline_ticket_id}/upload
    @mekewe_router.delete(
        "/pipeline/{pipeline_ticket_id}/file/remove/{param_name}/{file_name}",
        response_model=MetaKeggPipelineDef,
        description="Remove a file from an non started/queued pipeline-run definition",
        tags=["Pipeline"],
    )
    @limiter.limit(f"5/minute")
    async def remove_file_from_meta_kegg_pipeline_run_definition(
        request: Request,
        param_name: str,
        file_name: str,
        pipeline_ticket_id: uuid.UUID,
    ) -> MetaKeggPipelineDef:

        return MetaKeggPipelineStateManager(
            redis_client=redis
        ).remove_pipeline_run_input_file(
            ticket_id=pipeline_ticket_id,
            param_name=param_name,
            removefile_name=file_name,
            raise_exception_if_not_exists=pipelinerun_not_found_exception,
        )

    analysis_method_names_type_hint = Literal[
        tuple([str(e.name) for e in MetaKeggPipelineAnalysisMethodDocs])
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
        ).get_pipeline_run_definition(pipeline_ticket_id)

        """HOTPATCH FOR TESTING LINE-QUEUING IN UI
        current = None
        if status.state not in ["initialized"]:
            current = redis.get("TEST_QUEUE_KEY")
            if current is None:

                redis.set("TEST_QUEUE_KEY", b"4")
                current = redis.get("TEST_QUEUE_KEY")
            current = int(current)

            if current > 0:
                next = current - 1
                redis.set("TEST_QUEUE_KEY", str(next))
                status.state = "queued"
                status.place_in_queue = current
            elif current == 0:
                # reset fake queue for next run
                redis.delete("TEST_QUEUE_KEY")
        print("QUEUE", current)
        # , "queued", "running", "failed", "success", "expired"]
        """
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
        ).get_pipeline_run_definition(pipeline_ticket_id)
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
            if not Path(file).exists():
                file = os.path.join(config.FRONTEND_FILES_DIR, "index.html")
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
        for link in config.CLIENT_LINK_LIST:
            res.append(MetaKeggClientLink(**link))
        return res

    return mekeweclient_info_router
