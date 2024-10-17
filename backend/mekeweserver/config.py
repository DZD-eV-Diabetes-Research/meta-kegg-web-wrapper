import os
from typing import Literal, Optional, TypedDict
from pathlib import Path
from typing_extensions import Self
from pydantic import (
    Field,
    AnyUrl,
    SecretStr,
    AnyHttpUrl,
    StringConstraints,
    model_validator,
)
from pydantic_settings import BaseSettings
import socket

env_file_path = os.environ.get(
    "MEKEWESERVER_DOT_ENV_FILE", Path(__file__).parent / ".env"
)


class RedisConnectionParams(BaseSettings):
    host: str = "localhost"  # Default Redis host
    port: int = 6379  # Default Redis port
    db: int = 0  # Default Redis database (0)
    username: Optional[str] = None  # No username by default
    password: Optional[str] = None  # No password by default
    socket_timeout: Optional[float] = None  # No timeout by default
    socket_connect_timeout: Optional[float] = None  # No connect timeout by default
    max_connections: Optional[int] = None  # No limit on max connections
    retry_on_timeout: bool = False  # Default: don't retry on timeout
    ssl: bool = False  # Default: SSL disabled
    ssl_certfile: Optional[str] = None  # No SSL certfile by default
    ssl_keyfile: Optional[str] = None  # No SSL keyfile by default
    ssl_ca_certs: Optional[str] = None  # No SSL CA certs by default
    ssl_check_hostname: bool = False  # Default: don't check hostname in SSL
    socket_keepalive: Optional[bool] = None  # No socket keepalive by default
    decode_responses: bool = False


class Config(BaseSettings):
    APP_NAME: str = "Meta Kegg Webwrapper"
    LOG_LEVEL: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"] = Field(
        default="INFO"
    )
    # Client
    FRONTEND_FILES_DIR: str = Field(
        description="The generated nuxt dir that contains index.html,...",
        default=str(
            Path(Path(__file__).parent.parent.parent, "frontend/.output/public")
        ),
    )
    CLIENT_URL: Optional[str] = Field(
        default=None,
        description="The URL where the client is hosted. Usualy it comes with the server",
    )

    @model_validator(mode="after")
    def set_empty_client_url(self: Self):
        if self.CLIENT_URL is None:
            self.CLIENT_URL = self.get_server_url()
        return self

    # Webserver
    SERVER_UVICORN_LOG_LEVEL: Optional[str] = Field(
        default=None,
        description="The log level of the uvicorn server. If not defined it will be the same as LOG_LEVEL.",
    )

    SERVER_LISTENING_PORT: int = Field(default=8282)
    SERVER_LISTENING_HOST: str = Field(
        default="localhost",
        examples=["0.0.0.0", "localhost", "127.0.0.1", "176.16.8.123"],
    )
    # ToDo: Read https://fastapi.tiangolo.com/advanced/behind-a-proxy/ if that is of any help for better hostname/FQDN detection
    SERVER_HOSTNAME: Optional[str] = Field(
        default_factory=socket.gethostname,
        description="The (external) hostname/domainname where the API is available. Usally a FQDN in productive systems. If not defined, it will be automatically detected based on the hostname.",
        examples=["mydomain.com", "localhost"],
    )
    SERVER_PROTOCOL: Optional[Literal["http", "https"]] = Field(
        default=None,
        description="The protocol detection can fail in certain reverse proxy situations. This option allows you to manually override the automatic detection",
    )

    PURGE_PIPELINE_RESULT_AFTER_MIN: int = 240

    def get_server_url(self) -> AnyHttpUrl:
        proto: Literal["https", "http"] = "http"
        if self.SERVER_PROTOCOL is not None:
            proto = self.SERVER_PROTOCOL
        elif self.SERVER_LISTENING_PORT == 443:
            proto = "https"

        port = ""
        if self.SERVER_LISTENING_PORT not in [80, 443]:
            port = f":{self.SERVER_LISTENING_PORT}"
        return AnyHttpUrl(f"{proto}://{self.SERVER_HOSTNAME}{port}")

    ENABLE_RATE_LIMITING: bool = Field(
        default=True,
        description="Only allows a certain amount of API requests. Helps mitigating filling the pipeline queue with garbage and DDOS attacks.",
    )
    MAX_PIPELINE_RUNS_PER_HOUR_PER_IP: int = Field(
        default=5,
        description="Rate limiting parameter. How many pipeline runs can be started from one IP.",
    )

    REDIS_CONNECTION_PARAMS: RedisConnectionParams | None = Field(
        default=None,
        description="Connection params for a redis database to be used as backend storage/cache. Is not set a python fakeredis process will be started to be used as backend storage/cache.",
        examples=[RedisConnectionParams(host="localhost", port=6379)],
    )

    RESULT_CACHE_DIR: str = Field(
        default="/tmp/mekewe_cache",
        description="Storage directory for MetaKEGG Pipeline ressults.",
    )

    class Config:
        env_nested_delimiter = "__"
        env_file = env_file_path
        env_file_encoding = "utf-8"
        extra = "ignore"
