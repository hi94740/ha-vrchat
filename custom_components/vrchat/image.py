"""Setup images for the VRChat integration."""

from datetime import UTC, datetime

from homeassistant.components.image import ImageEntity, ImageEntityDescription
from homeassistant.const import EntityCategory, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import (
    VRChatConfigEntry,
    VRChatUserDataEntity,
    VRChatUserLocationEntityMixin,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VRChatConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up entry."""
    config_entry.runtime_data.setup_entities(Platform.IMAGE, async_add_entities)


class VRChatUserDataImageEntity(
    VRChatUserDataEntity, ImageEntity, platform=Platform.IMAGE
):
    """Base entity for all VRChat images."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, user):
        """Initialize both parents."""
        super().__init__(user)
        ImageEntity.__init__(self, self.user.account.hass)

    @property
    def image_url(self):
        """The state."""
        return self.vrchat_user_data_state

    @property
    def image_last_updated(self):
        """The actual home assistant state."""
        current_image_url = self.image_url
        if current_image_url is None:
            return None
        if self._attr_image_url != current_image_url:
            self._attr_image_last_updated = datetime.now(UTC)
            self._attr_image_url = current_image_url
            self._cached_image = None
        return self._attr_image_last_updated

    @property
    def extra_state_attributes(self):
        """Show image URL."""
        return {"image_url": self.image_url}


class VRChatUserLocationImage(VRChatUserLocationEntityMixin, VRChatUserDataImageEntity):
    """VRChat user location image entity."""

    entity_description = ImageEntityDescription(
        key="locationImage", icon="mdi:image-marker"
    )

    @property
    def vrchat_user_data_state(self):
        """Location image url."""
        return self.vrchat_user_world_data_get("imageUrl")

    @property
    def entity_picture(self):
        """Location image thumbnail URL."""
        return self.vrchat_user_world_data_get("thumbnailImageUrl")


class VRChatUserCurrentAvatarImage(VRChatUserDataImageEntity):
    """VRChat user current avatar image entity."""

    entity_description = ImageEntityDescription(
        key="currentAvatarImage", icon="mdi:account-box"
    )

    @classmethod
    def get_state_from_user_data(cls, user_data, key=None):
        """Current avatar image URL."""
        if key is None:
            key = "currentAvatarImageUrl"
        return super().get_state_from_user_data(user_data, key)

    @property
    def entity_picture(self):
        """Current avatar image thumbnail URL."""
        return self.get_state_from_user_data(
            self.user.data, "currentAvatarThumbnailImageUrl"
        )
