"""Data store for the VRChat integration."""

from typing import TypedDict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .api_data_types import CurrentUser
from .const import DOMAIN

VRChatConfigData = TypedDict(
    "VRChatConfigData",
    {"username": str, "password": str, "2fa_code_entity": str, "proxy": str},
    total=False,
)


class VRChatAuthCookie(TypedDict, total=False):
    """VRChat auth cookie."""

    auth: str
    twoFactorAuth: str


VRChatAuthCookieStore: dict[str, Store[VRChatAuthCookie]] = {}


def get_vrchat_auth_cookie_store(hass: HomeAssistant, id: str):
    """Get an auth cookie store for given user id."""
    store = VRChatAuthCookieStore.get(id)
    if store is None:
        store = Store[VRChatAuthCookie](hass, 1, f"{DOMAIN}.{id}")
        VRChatAuthCookieStore[id] = store
    return store


InitialCurrentUserData: dict[str, CurrentUser] = {}
