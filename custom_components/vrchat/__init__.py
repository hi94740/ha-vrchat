"""The VRChat integration."""

from __future__ import annotations

import logging

from homeassistant.const import CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .action import actions
from .api import VRChatAPI
from .const import DOMAIN
from .coordinator import VRChatAccountDataCoordinator, VRChatConfigEntry
from .store import VRChatAuthCookieStore, get_vrchat_auth_cookie_store

_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.IMAGE,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register actions."""
    for action in actions:
        hass.services.async_register(
            DOMAIN,
            action.service,
            action.service_func,
            action.schema,
            action.supports_response,
            action.job_type,
            description_placeholders=action.description_placeholders,
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: VRChatConfigEntry) -> bool:
    """Set up VRChat from a config entry."""

    entry.runtime_data = VRChatAccountDataCoordinator(hass, entry)
    await entry.runtime_data.starting_task

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: VRChatConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, _PLATFORMS):
        await entry.runtime_data.close()
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: VRChatConfigEntry) -> None:
    """Handle removal of an entry."""
    cookie_store = get_vrchat_auth_cookie_store(hass, entry.unique_id)
    if CONF_PASSWORD in entry.data:
        try:
            async with VRChatAPI(entry.data, await cookie_store.async_load()) as api:
                await api.logout()
        except Exception:
            _LOGGER.exception("Error logging out.")
    await VRChatAuthCookieStore.pop(entry.unique_id).async_remove()
