"""Settings for running the announcements service."""

from pydantic import Field
from pydantic_settings import BaseSettings

from .hub import DEFAULT_STORE_PATH


class ServiceSettings(BaseSettings):
    """Read from the environment JupyterHub sets for managed services."""

    service_prefix: str = Field("/", validation_alias="JUPYTERHUB_SERVICE_PREFIX")
    # Used to load the hub's own CSS, so the preview looks exactly like hub pages.
    hub_base_url: str = Field("/", validation_alias="JUPYTERHUB_BASE_URL")
    store_path: str = Field(DEFAULT_STORE_PATH, validation_alias="ANNOUNCEMENTS_STORE")
