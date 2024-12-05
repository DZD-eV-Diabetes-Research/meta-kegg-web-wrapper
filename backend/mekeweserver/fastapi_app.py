from contextlib import asynccontextmanager
import getversion
from fastapi import Depends
from fastapi import FastAPI
import getversion.plugin_setuptools_scm
from multiprocessing import Process

# from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# from fastapi.security import

import mekeweserver
from mekeweserver.config import Config, get_config
from mekeweserver.log import get_logger


log = get_logger()
config: Config = get_config()


def _add_api_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.get_allowed_origins(),
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    # app.add_middleware(
    #    SessionMiddleware,
    #    secret_key=config.SERVER_SESSION_SECRET.get_secret_value(),
    # )


def _add_app_routers(app: FastAPI, background_worker: Process):
    from mekeweserver.fastapi_routes import (
        get_api_router,
        get_client_router,
        get_health_router,
        get_info_config_router,
    )

    app.include_router(get_health_router(app, background_worker))
    app.include_router(get_api_router(app))
    app.include_router(get_info_config_router(app))
    app.include_router(get_client_router(app))


def _add_rate_limiter(app: FastAPI):
    limiter = Limiter(key_func=get_remote_address, enabled=config.ENABLE_RATE_LIMITING)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def get_fastapi_app(background_worker: Process) -> FastAPI:
    try:
        v = getversion.get_module_version(mekeweserver)[0]
    except:
        v = "unknown"
    app = FastAPI(
        title="MetaKegg Web REST API",
        version=v,
        # openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        # debug=settings.debug,
    )

    _add_api_middleware(app)
    _add_rate_limiter(app)
    _add_app_routers(app, background_worker)
    return app
