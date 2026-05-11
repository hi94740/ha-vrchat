"""Setup selects for the VRChat integration."""

from vrchatapi import UpdateUserRequest

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .binary_sensor import VRChatUserIsInGameBinarySensor
from .const import (
    VRCHAT_USER_STATUS_ICON_MAP,
    VRCHAT_USER_STATUS_INDICATOR_MAP_IN_GAME,
    VRCHAT_USER_STATUS_INDICATOR_MAP_NOT_IN_GAME,
    VRCHAT_USER_STATUS_OPTIONS,
    VRChatUserState,
)
from .coordinator import VRChatConfigEntry, VRChatUserDataEntity
from .sensor import VRChatUserStatusSensor


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VRChatConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up entry."""
    config_entry.runtime_data.setup_entities(Platform.SELECT, async_add_entities)


VRCHAT_CURRENT_USER_STATUS_OPTIONS = VRCHAT_USER_STATUS_OPTIONS.copy()
VRCHAT_CURRENT_USER_STATUS_OPTIONS.remove(VRChatUserState.OFFLINE)


class VRChatUserDataSelectEntity(
    VRChatUserDataEntity, SelectEntity, platform=Platform.SELECT
):
    """Base entity for all VRChat selects."""

    @property
    def current_option(self):
        """The state."""
        return self.vrchat_user_data_state


class VRChatUserStatusSelect(VRChatUserDataSelectEntity):
    """VRChat user status select entity."""

    should_add_for_non_current_user = False

    entity_description = SelectEntityDescription(
        key="status_select",
        options=VRCHAT_CURRENT_USER_STATUS_OPTIONS,
    )

    icon_map = VRCHAT_USER_STATUS_ICON_MAP

    @classmethod
    def get_state_from_user_data(cls, user_data, key=None):
        """Mirror behavior from user status sensor."""
        return VRChatUserStatusSensor.get_state_from_user_data(user_data, key)

    @property
    def entity_picture(self):
        """User status indicator."""
        status = self.current_option
        if status is None:
            return None
        if (
            status == VRChatUserState.OFFLINE
            or VRChatUserIsInGameBinarySensor.get_state_from_user_data(self.user.data)
        ):
            return VRCHAT_USER_STATUS_INDICATOR_MAP_IN_GAME.get(status)
        return VRCHAT_USER_STATUS_INDICATOR_MAP_NOT_IN_GAME.get(status)

    async def async_select_option(self, option):
        """Update user status."""
        await self.user.update_user(UpdateUserRequest(status=option))
