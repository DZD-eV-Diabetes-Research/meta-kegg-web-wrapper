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


from fastapi import FastAPI, HTTPException, UploadFile, File
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# from fastapi.security import

import mekeweserver
from mekeweserver.config import Config, get_config
from mekeweserver.log import get_logger
from mekeweserver.utils import bytes_humanreadable

log = get_logger()
config: Config = get_config()


class FileSizeLimiterMiddleware(BaseHTTPMiddleware):

    def __init__(self, app: FastAPI, max_size_bytes: int):
        super().__init__(app)
        self.max_size_bytes = max_size_bytes

    async def dispatch(self, request: Request, call_next):
        if self.max_size_bytes is None:
            return await call_next(request)
        # Check Content-Length header (if present)
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > self.max_size_bytes:
            return Response(
                f"Uploaded file is too large. Max limit is {bytes_humanreadable(self.max_size_bytes)}",
                status_code=413,
            )

        # Alternatively, check the actual body size
        body = await request.body()
        if len(body) > self.max_size_bytes:
            return Response(
                f"Uploaded file is too large. Max limit is {bytes_humanreadable(self.max_size_bytes)}",
                status_code=413,
            )

        return await call_next(request)


def _add_api_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.get_allowed_origins(),
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.add_middleware(
        FileSizeLimiterMiddleware, config.MAX_FILE_SIZE_UPLOAD_LIMIT_BYTES
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
