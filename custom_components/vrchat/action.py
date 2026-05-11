"""Actions for the VRChat integration."""

from abc import ABC, abstractmethod
from collections.abc import Coroutine, Mapping
from typing import Any

from vrchatapi import UpdateUserRequest

from homeassistant.core import (
    EntityServiceResponse,
    HassJobType,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.helpers.typing import VolSchemaType

from .coordinator import VRChatConfigEntry


class VRChatAction(ABC):
    """ABC for VRChat actions."""

    service: str
    schema: VolSchemaType | None = None
    supports_response: SupportsResponse = SupportsResponse.NONE
    job_type: HassJobType | None = None
    description_placeholders: Mapping[str, str] | None = None

    @classmethod
    @callback
    @abstractmethod
    def service_func(
        cls, call: ServiceCall
    ) -> (
        ServiceResponse
        | Coroutine[Any, Any, ServiceResponse | EntityServiceResponse]
        | EntityServiceResponse
    ):
        """Action function."""

    def __init_subclass__(cls):
        """Add action to list."""
        actions.append(cls)


actions: list[VRChatAction] = []


class VRChatUpdateUserStatusAction(VRChatAction):
    """VRChat update user status action."""

    service = "update_user_status"

    @classmethod
    @callback
    async def service_func(cls, call):
        """Action."""
        data = call.data
        entry: VRChatConfigEntry = call.hass.config_entries.async_get_known_entry(
            data["config_entry_id"]
        )
        await entry.runtime_data.current_user.update_user(
            UpdateUserRequest(
                status=data.get("status"),
                status_description=data.get("status_description"),
            )
        )
