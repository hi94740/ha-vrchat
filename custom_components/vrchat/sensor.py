"""Setup sensors for the VRChat integration."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .binary_sensor import VRChatUserIsInGameBinarySensor
from .const import (
    VRCHAT_SPECIAL_LOCATION_STRINGS,
    VRCHAT_USER_LOCATION_ICON_MAP,
    VRCHAT_USER_STATE_ICON_MAP,
    VRCHAT_USER_STATE_OPTIONS,
    VRCHAT_USER_STATUS_ICON_MAP,
    VRCHAT_USER_STATUS_INDICATOR_MAP_IN_GAME,
    VRCHAT_USER_STATUS_INDICATOR_MAP_NOT_IN_GAME,
    VRCHAT_USER_STATUS_OPTIONS,
    VRChatSpecialLocationString,
    VRChatUserState,
)
from .coordinator import (
    VRChatConfigEntry,
    VRChatUserDataEntity,
    VRChatUserLocationEntityMixin,
)
from .utils import VRCHAT_WORLD_ID_PREFIX, process_vrchat_string
from .world import VRChatWorldData


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VRChatConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up entry."""
    config_entry.runtime_data.setup_entities(Platform.SENSOR, async_add_entities)


class VRChatUserDataSensorEntity(
    VRChatUserDataEntity, SensorEntity, platform=Platform.SENSOR
):
    """Base entity for all VRChat sensors."""

    @property
    def native_value(self):
        """The state."""
        return self.vrchat_user_data_state


class VRChatUserStatusSensor(VRChatUserDataSensorEntity):
    """VRChat user status sensor entity."""

    should_add_for_current_user = False

    entity_description = SensorEntityDescription(
        key="status",
        device_class=SensorDeviceClass.ENUM,
        options=VRCHAT_USER_STATUS_OPTIONS,
    )

    icon_map = VRCHAT_USER_STATUS_ICON_MAP

    @property
    def entity_picture(self):
        """User status indicator."""
        status = self.native_value
        if status is None:
            return None
        if (
            status == VRChatUserState.OFFLINE
            or VRChatUserIsInGameBinarySensor.get_state_from_user_data(self.user.data)
        ):
            return VRCHAT_USER_STATUS_INDICATOR_MAP_IN_GAME.get(status)
        return VRCHAT_USER_STATUS_INDICATOR_MAP_NOT_IN_GAME.get(status)


class VRChatUserStatusDescriptionSensor(VRChatUserDataSensorEntity):
    """VRChat user status description sensor entity."""

    entity_description = SensorEntityDescription(key="statusDescription")

    @property
    def icon(self):
        """Show icon based on user status."""
        return VRCHAT_USER_STATUS_ICON_MAP.get(
            VRChatUserStatusSensor.get_state_from_user_data(self.user.data)
        )


class VRChatUserStateSensor(VRChatUserDataSensorEntity):
    """VRChat user state sensor entity."""

    entity_description = SensorEntityDescription(
        key="state",
        device_class=SensorDeviceClass.ENUM,
        options=VRCHAT_USER_STATE_OPTIONS,
    )

    icon_map = VRCHAT_USER_STATE_ICON_MAP

    @property
    def entity_picture(self):
        """Show user icon or avatar image."""
        user_data_get = self.user.data.get
        return process_vrchat_string(
            user_data_get("userIcon")
            or user_data_get("imageUrl")
            or user_data_get("currentAvatarThumbnailImageUrl")
        )

    @classmethod
    def get_state_from_user_data(cls, user_data, key=None):
        """Summarize user state."""
        is_in_game = VRChatUserIsInGameBinarySensor.get_state_from_user_data(user_data)
        if is_in_game is None:
            return None
        status = VRChatUserStatusSensor.get_state_from_user_data(user_data)
        # platform = VRChatUserPlatformSensor.get_state_from_user_data(user_data)
        if is_in_game:
            return status
        # if platform == VRChatUserPlatform.WEB:
        #     return VRChatUserState.ACTIVE_ON_WEB
        # if platform in VRChatUserPlatformMobile:
        #     return VRChatUserState.ACTIVE_ON_MOBILE
        if status == VRChatUserState.OFFLINE:
            return VRChatUserState.OFFLINE
        return VRChatUserState.ACTIVE_ON_WEB_OR_MOBILE

    @property
    def extra_state_attributes(self):
        """User data."""
        return self.user.data


class VRChatUserLocationSensor(
    VRChatUserLocationEntityMixin, VRChatUserDataSensorEntity
):
    """VRChat user location sensor entity."""

    entity_description = SensorEntityDescription(
        key="location", icon="mdi:map-marker", device_class=SensorDeviceClass.ENUM
    )

    icon_map = VRCHAT_USER_LOCATION_ICON_MAP

    @property
    def entity_picture(self):
        """Location image thumbnail URL."""
        return self.vrchat_user_world_data_get("thumbnailImageUrl")

    @property
    def options(self):
        """Dynamically return options based on known locations."""
        return [
            *VRCHAT_SPECIAL_LOCATION_STRINGS,
            VRChatUserState.ACTIVE_ON_WEB_OR_MOBILE,
            *[
                world.data["name"]
                for world in VRChatWorldData.registry.values()
                if world.data
            ],
        ]

    @property
    def vrchat_user_data_state(self):
        """World name."""
        if (
            VRChatUserStateSensor.get_state_from_user_data(self.user.data)
            == VRChatUserState.ACTIVE_ON_WEB_OR_MOBILE
        ):
            self._attr_native_value = VRChatUserState.ACTIVE_ON_WEB_OR_MOBILE
        elif (self.get_state_from_user_data(self.user.data, "location")).startswith(
            VRChatSpecialLocationString.TRAVELING
        ):
            self._attr_native_value = VRChatSpecialLocationString.TRAVELING
        else:
            name = self.vrchat_user_world_data_get("name")
            if name is None:
                name = self.get_state_from_user_data(self.user.data, "worldId")
            if not name.startswith(VRCHAT_WORLD_ID_PREFIX):
                self._attr_native_value = name
        return self._attr_native_value

    @property
    def extra_state_attributes(self):
        """World data."""
        user_data_get = self.user.data.get
        if (world := self.user.world) is not None and (data := world.data) is not None:
            return {"instanceId": user_data_get("instanceId"), **data}
        return {
            "id": user_data_get("worldId"),
            "instanceId": user_data_get("instanceId"),
            "travelingToLocation": user_data_get("travelingToLocation"),
        }


# Not adding platform sensor for now because it's unable to get accurate platform information from websocket API.

# vrchat_user_platform_options = list(VRChatUserPlatform)
# vrchat_user_platform_options.append(VRChatUserState.OFFLINE)

# class VRChatUserPlatformSensor(VRChatUserDataSensorEntity):
#     """VRChat user platform sensor entity."""

#     entity_description = SensorEntityDescription(
#         key="platform",
#         device_class=SensorDeviceClass.ENUM,
#         options=vrchat_user_platform_options,
#     )

#     @classmethod
#     def get_state_from_user_data(cls, user_data):
#         """Empty platform string indicates offline."""
#         platform = cls.get_raw_state_from_user_data(user_data)
#         return VRChatUserState.OFFLINE if platform == "" else platform

#     @property
#     def icon(self):
#         """Platform icons."""
#         platform = self.native_value
#         if platform is None:
#             return "mdi:checkbox-multiple-blank"
#         if platform == VRChatUserPlatform.STANDALONE_WINDOWS:
#             return "mdi:monitor"
#         if platform == VRChatUserPlatform.WEB:
#             return "mdi:application-outline"
#         if platform in VRChatUserPlatformMobile:
#             return "mdi:cellphone"
#         return "mdi:help-box-multiple"
