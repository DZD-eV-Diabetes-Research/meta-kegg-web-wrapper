from typing import Dict
from fastapi import FastAPI
import yaml
import json
import asyncio
import uvicorn
from uvicorn.config import LOGGING_CONFIG

# Add meta kegg server to global Python modules.
# This way we address mekeweserver as a module for imports without installing it first.
if __name__ == "__main__":
    from pathlib import Path
    import sys, os

    MODULE_DIR = Path(__file__).parent
    MODULE_PARENT_DIR = MODULE_DIR.parent.absolute()
    sys.path.insert(0, os.path.normpath(MODULE_PARENT_DIR))

from mekeweserver.config import Config

config = Config()


def run_server():
    import mekeweserver

    from mekeweserver.log import (
        get_logger,
        get_loglevel,
        get_uvicorn_loglevel,
        APP_LOGGER_DEFAULT_NAME,
    )

    log = get_logger()

    log.debug("----CONFIG-----")
    log.debug(yaml.dump(json.loads(config.model_dump_json()), sort_keys=False))
    log.debug("----CONFIG-END-----")
    # test_exporter()
    # exit()
    print(f"LOG_LEVEL: {config.LOG_LEVEL}")
    print(f"UVICORN_LOG_LEVEL: {get_uvicorn_loglevel()}")
    print(
        f"allow_origins=[{config.CLIENT_URL}, {str(config.get_server_url()).rstrip('/')}]"
    )

    # check if client exists if needed
    if config.CLIENT_URL == config.get_server_url():
        if (
            not Path(config.FRONTEND_FILES_DIR).exists()
            or not Path(config.FRONTEND_FILES_DIR, "index.html").exists()
        ):
            raise ValueError(
                "Can not find frontend files. Maybe you need to build the frontend first. Try to run 'make frontend'"
            )

    from mekeweserver.fastapi_app import get_fastapi_app

    app = get_fastapi_app()
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
    uvicorn_server = uvicorn.Server(config=uvicorn_config)
    event_loop.run_until_complete(uvicorn_server.serve())


if __name__ == "__main__":
    run_server()
