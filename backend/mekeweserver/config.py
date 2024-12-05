import os
import uuid
from typing import Literal, Optional, TypedDict, List, Dict
from pathlib import Path, PurePath
from typing_extensions import Self
from psyplus import YamlSettingsPlus
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
    "MEKEWESERVER_DOT_ENV_FILE", PurePath(Path(__file__).parent, ".env")
)

yaml_file_path = os.environ.get(
    "MEKEWESERVER_YAML_CONFIG_FILE",
    PurePath(Path(__file__).parent.parent.parent, "config.yaml"),
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
    APP_NAME: str = "MetaKeggWeb"
    LOG_LEVEL: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"] = Field(
        default="INFO"
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
    SERVER_ALLOWED_ORIGINS: List[str] = Field(
        default_factory=list,
        description="Additional http allowed origins values.",
    )

    def get_allowed_origins(self) -> List[str]:
        allowed_origins = self.SERVER_ALLOWED_ORIGINS
        allowed_origins.extend(
            [self.CLIENT_URL, str(self.get_server_url()).rstrip("/")]
        )
        return allowed_origins

    PIPELINE_ABANDONED_DEFINITION_DELETED_AFTER: int = Field(
        default=240,
        description="If a MetaKegg pipeline run is initialized but not started, it will be considered as abandoned after this time and be deleted.",
    )
    PIPELINE_RESULT_EXPIRED_AFTER_MIN: int = Field(
        default=1440,
        description="If a MetaKegg pipeline has finished, it will be considered as obsolete after the result will be deleted to save storage. The metadata will still be existent and the user will be notified that the pipeline is expired.",
    )
    PIPELINE_RESULT_DELETED_AFTER_MIN: int = Field(
        default=1440,
        description="If a MetaKegg pipeline has finished and is expired, all its metadata will be wiped after this amounts of minutes after expiring. If a user tries to revisit it, there will be a 404 error.",
    )

    CLIENT_CONTACT_EMAIL: Optional[str] = Field(
        default=None,
        description="A email address a contact shown on the main page of the webclient",
    )
    CLIENT_BUG_REPORT_EMAIL: Optional[str] = Field(
        default=None,
        description="A email address a contact shown when an errors occurs in the webclient",
    )
    CLIENT_ENTRY_TEXT: Optional[str] = Field(
        description="A text that will be shown at the top on the main page of the webclient",
        default="I am the entry text. You can configure me via the config variable ENTRY_TEXT. \nNo developer needs to be harmed for that.",
    )
    CLIENT_TERMS_AND_CONDITIONS: Optional[str] = Field(
        default="We are not responsible for the content uploaded by users. Uploaded files are processed and deleted as quickly as possible. While we take measures to ensure file confidentiality, we cannot guarantee absolute security or prevent potential breaches."
    )
    CLIENT_LINK_LIST: Optional[List[Dict[str, str]]] = Field(
        default_factory=list,
        examples=[[{"title": "Paper xyz", "link": "https://doi.org/12345"}]],
    )

    ENABLE_RATE_LIMITING: bool = Field(
        default=True,
        description="Only allows a certain amount of API requests. Helps mitigating filling the pipeline queue with garbage and DDOS attacks.",
    )
    MAX_FILE_SIZE_UPLOAD_LIMIT_BYTES: Optional[int] = Field(default=None)
    MAX_CACHE_SIZE_BYTES: Optional[int] = Field(default=None)
    MAX_PIPELINE_RUNS_PER_HOUR_PER_IP: int = Field(
        default=5,
        description="Rate limiting parameter. How many pipeline runs can be started from one IP.",
    )

    REDIS_CONNECTION_PARAMS: RedisConnectionParams | None = Field(
        default=None,
        description="Connection params for a redis the database (client lib used: https://github.com/redis/redis-py) to be used as backend storage/cache. Is not set a python fakeredis process will be started to be used as backend storage/cache.",
        examples=[RedisConnectionParams(host="localhost", port=6379)],
    )

    PIPELINE_RUNS_CACHE_DIR: str = Field(
        default="/tmp/mekewe_cache",
        description="Storage directory for MetaKEGG Pipeline ressults.",
    )

    def get_server_url(self) -> str:
        proto: Literal["https", "http"] = "http"
        if self.SERVER_PROTOCOL is not None:
            proto = self.SERVER_PROTOCOL
        elif self.SERVER_LISTENING_PORT == 443:
            proto = "https"

        port = ""
        if self.SERVER_HOSTNAME is None and self.SERVER_LISTENING_PORT not in [80, 443]:
            port = f":{self.SERVER_LISTENING_PORT}"
        return f"{proto}://{self.SERVER_HOSTNAME}{port}"

    # Development relevant settings

    ## Client
    FRONTEND_FILES_DIR: str = Field(
        description="Files for the web client. Should contain a builded nuxt client (`frontend/.output/public` The directory that contains index.html,...)",
        default=str(
            Path(Path(__file__).parent.parent.parent, "frontend/.output/public")
        ),
    )
    CLIENT_URL: Optional[str] = Field(
        default=None,
        description="The URL where the client is hosted. Usually it is hosted with the API Server, but if you develop on the client with a Vuejs/Nuxt Development server, you may want to change this.",
        examples=["http://localhost:3000"],
    )

    @model_validator(mode="after")
    def set_empty_client_url(self: Self):
        if self.CLIENT_URL is None:
            self.CLIENT_URL = self.get_server_url()
        return self

    ## Server

    SERVER_UVICORN_LOG_LEVEL: Optional[str] = Field(
        default=None,
        description="The log level of the uvicorn web server. If not defined it will be the same as LOG_LEVEL.",
    )

    DUMP_OPEN_API_SPECS_ON_BOOT: Optional[bool] = Field(
        default=False,
        description="If set to true, the server will dump an openapi.json file in the root dir of this repo on boot.",
    )
    DUMP_OPEN_API_SPECS_ON_BOOT_DIR: Optional[str] = Field(
        default=None,
        description="If not None and DUMP_OPEN_API_SPECS_ON_BOOT set to true, the server will dump a openapi.json file in this directory on boot.",
    )
    RESTART_BACKGROUND_WORKER_ON_EXCEPTION_N_TIMES: int = Field(
        default=3, description=""
    )

    class Config:
        env_nested_delimiter = "__"
        env_file = env_file_path
        env_file_encoding = "utf-8"
        extra = "ignore"


def get_config() -> Config:
    if Path(yaml_file_path).exists():
        return YamlSettingsPlus(Config, yaml_file_path).get_config()
    else:
        return Config()
