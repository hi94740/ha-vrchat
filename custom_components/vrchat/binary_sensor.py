"""Setup sensors for the VRChat integration."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import VRChatUserState
from .coordinator import VRChatConfigEntry, VRChatUserDataEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VRChatConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up entry."""
    config_entry.runtime_data.setup_entities(Platform.BINARY_SENSOR, async_add_entities)


class VRChatUserDataBinarySensorEntity(
    VRChatUserDataEntity, BinarySensorEntity, platform=Platform.BINARY_SENSOR
):
    """Base entity for all VRChat sensors."""

    @property
    def is_on(self):
        """The state."""
        return self.vrchat_user_data_state


class VRChatUserIsInGameBinarySensor(VRChatUserDataBinarySensorEntity):
    """VRChat user in game online binary sensor entity."""

    entity_description = BinarySensorEntityDescription(
        key="is_in_game", device_class=BinarySensorDeviceClass.PRESENCE
    )

    @classmethod
    def get_state_from_user_data(cls, user_data, key=None):
        """Calculate user in game online state."""
        location = (
            (key and super().get_state_from_user_data(user_data, key))
            or super().get_state_from_user_data(user_data, "location")
            or super().get_state_from_user_data(user_data, "world")
            or super().get_state_from_user_data(user_data, "instance")
        )
        if location is None:
            return None
        return VRChatUserState.OFFLINE not in location and location != ""

    @property
    def icon(self):
        """Circle icon indicating online state."""
        return "mdi:circle" if self.is_on else "mdi:circle-outline"
