"""Settings for running the announcements service."""

from pydantic import Field
from pydantic_settings import BaseSettings

from .hub import DEFAULT_STORE_PATH


class ServiceSettings(BaseSettings):
    """Read from the environment JupyterHub sets for managed services."""

    service_prefix: str = Field("/", validation_alias="JUPYTERHUB_SERVICE_PREFIX")
    store_path: str = Field(DEFAULT_STORE_PATH, validation_alias="ANNOUNCEMENTS_STORE")
