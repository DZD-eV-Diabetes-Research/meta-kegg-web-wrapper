from typing import Dict
from fastapi import FastAPI
import yaml
import json
import asyncio
import uvicorn
from uvicorn.config import LOGGING_CONFIG
from fastapi.openapi.utils import get_openapi
from pathlib import Path, PurePath
import sys, os
import atexit

# Add meta kegg server to global Python modules.
# This way we address mekeweserver as a module for imports without the need of installing it first.
# this is convenient for local development
if __name__ == "__main__":
    MODULE_DIR = Path(__file__).parent
    MODULE_PARENT_DIR = MODULE_DIR.parent.absolute()
    sys.path.insert(0, os.path.normpath(MODULE_PARENT_DIR))


from mekeweserver.log import get_logger


def dump_open_api_spec(app: FastAPI):
    from mekeweserver.config import Config, get_config

    config: Config = get_config()
    if config.DUMP_OPEN_API_SPECS_ON_BOOT:
        path = Path(f"{Path(__file__).parent}/../../openapi.json")
        if config.DUMP_OPEN_API_SPECS_ON_BOOT_DIR is not None:
            path = (
                Path(config.DUMP_OPEN_API_SPECS_ON_BOOT_DIR)
                if config.DUMP_OPEN_API_SPECS_ON_BOOT_DIR.lower().endswith(".json")
                else Path(
                    PurePath(config.DUMP_OPEN_API_SPECS_ON_BOOT_DIR, "openapi.json")
                )
            )
        get_logger().info(f"Dump openapi specifications at '{path.resolve()}'")
        with open(path, "w") as f:
            json.dump(
                get_openapi(
                    title=app.title,
                    version=app.version,
                    openapi_version=app.openapi_version,
                    description=app.description,
                    routes=app.routes,
                ),
                f,
            )


def run_server(env: Dict = None):
    if env:
        os.environ = os.environ.copy() | env
    from mekeweserver.config import Config, get_config

    config: Config = get_config()
    import getversion
    import mekeweserver

    try:
        mekewe_server_version = getversion.get_module_version(mekeweserver)[0]
    except:
        mekewe_server_version = "unknown"
    from mekeweserver.log import (
        get_loglevel,
        get_uvicorn_loglevel,
        APP_LOGGER_DEFAULT_NAME,
    )

    log = get_logger()
    log.info(f"Start MetaKEGG Web API Server version '{mekewe_server_version}'")
    from mekeweserver.config import env_file_path, yaml_file_path

    log.info(
        f"Load env variables from file '{Path(env_file_path).resolve()}' (if exists)"
    )
    log.info(
        f"Load yaml variables from file '{Path(yaml_file_path).resolve()}' (if exists)"
    )

    log.debug("----CONFIG-----")
    log.debug(yaml.dump(json.loads(config.model_dump_json()), sort_keys=False))
    log.debug("----CONFIG-END-----")
    # test_exporter()
    # exit()
    print(f"LOG_LEVEL: {config.LOG_LEVEL}")
    print(f"UVICORN_LOG_LEVEL: {get_uvicorn_loglevel()}")
    print(f"allow_origins={config.get_allowed_origins()}")
    # check if client exists if needed
    if config.CLIENT_URL == config.get_server_url():
        if (
            not Path(config.FRONTEND_FILES_DIR).exists()
            or not Path(config.FRONTEND_FILES_DIR, "index.html").exists()
        ):
            raise ValueError(
                "Can not find frontend files. Maybe you need to build the frontend first. Try to run 'make frontend' or point config var `CLIENT_URL` to an alternative URL."
            )

    from mekeweserver.db import get_redis_client

    log.info("Check Cache/DB Health...")

    r = get_redis_client()
    r.ping()
    log.info("...connection to Cache/DB Health successful.")

    from mekeweserver.pipeline_worker.pipeline_worker import PipelineWorker

    log.info("Start background MetaKegg Pipeline Processor worker...")
    worker_process = PipelineWorker(env=env)

    atexit.register(worker_process.stop_event.set)
    worker_process.start()

    from mekeweserver.fastapi_app import get_fastapi_app

    app = get_fastapi_app(worker_process)
    uvicorn_log_config: Dict = LOGGING_CONFIG
    uvicorn_log_config["loggers"][APP_LOGGER_DEFAULT_NAME] = {
        "handlers": ["default"],
        "level": get_loglevel(),
    }
    event_loop = asyncio.get_event_loop()
    uvicorn_config = uvicorn.Config(
        app=app,
        host=config.SERVER_LISTENING_HOST,
        port=config.SERVER_LISTENING_PORT,
        log_level=get_uvicorn_loglevel(),
        log_config=uvicorn_log_config,
        loop=event_loop,
    )
    dump_open_api_spec(app)
    uvicorn_server = uvicorn.Server(config=uvicorn_config)
    try:
        event_loop.run_until_complete(uvicorn_server.serve())
    except:
        worker_process.stop_event.set
        raise


if __name__ == "__main__":
    run_server()
