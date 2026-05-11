"""Config flow for the VRChat integration."""

from __future__ import annotations

import logging
from typing import Any, Final

import voluptuous as vol
import vrchatapi.exceptions

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_OPTIONS, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import section
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    EntityFilterSelectorConfig,
    EntitySelector,
    EntitySelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import VRChatAPI
from .api_data_types import CurrentUser
from .const import (
    CONF_2FA_CODE,
    CONF_2FA_CODE_ENTITY,
    CONF_COOKIE_2FA,
    CONF_COOKIE_AUTH,
    CONF_EMAIL_2FA_CODE,
    CONF_PROXY,
    DOMAIN,
)
from .coordinator import VRChatConfigEntry
from .store import (
    InitialCurrentUserData,
    VRChatAuthCookie,
    VRChatConfigData,
    get_vrchat_auth_cookie_store,
)

_LOGGER = logging.getLogger(__name__)


class VRChatConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VRChat."""

    VERSION = 1

    @property
    def api(self) -> VRChatAPI | None:
        """Current API object."""
        return getattr(self, "_api", None)

    async def close_api(self):
        """Close current API object."""
        if self.api is not None:
            await self.api.close()
            self._api = None

    async def set_api(self, api):
        """Set current API object."""
        await self.close_api()
        self._api = api

    @property
    def entry(self) -> VRChatConfigEntry | None:
        """Config entry if in reauth or reconfigure flow."""
        entry_id = self.context.get("entry_id")
        return (
            self.hass.config_entries.async_get_known_entry(entry_id)
            if entry_id is not None
            else None
        )

    async def async_step_user(self, _=None) -> ConfigFlowResult:
        """Handle the initial step."""
        return await self.async_step_choose_auth_method()

    async def async_step_reauth(self, _=None):
        """Handle reauthentication."""
        return await self.async_step_choose_auth_method()

    async def async_step_reconfigure(self, _=None):
        """Handle reconfigure."""
        return await self.async_step_choose_auth_method()

    async def async_step_choose_auth_method(self, _=None) -> ConfigFlowResult:
        """Step to choose authentication method."""
        return self.async_show_menu(
            step_id="choose_auth_method", menu_options=["login", "enter_cookies"]
        )

    async def async_step_login(
        self, form_data: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step to login with username, password, and potentially 2FA code."""
        config: VRChatConfigData | None = None
        errors: dict[str, str] | None = None

        if form_data is not None:
            config = remove_options_from_dict(form_data)
            if CONF_OPTIONS in form_data:
                config.update(form_data[CONF_OPTIONS])

            await self.set_api(VRChatAPI(config))

            try:
                return await self.authenticate()
            except vrchatapi.exceptions.UnauthorizedException as e:
                if "Email 2 Factor Authentication" in e.reason:
                    return await self.async_step_email_2fa()
                if "2 Factor Authentication" in e.reason:
                    if CONF_2FA_CODE_ENTITY not in config:
                        return await self.async_step_2fa()
                    try:
                        await self.api.verify2_fa(
                            self.hass.states.get(config[CONF_2FA_CODE_ENTITY]).state
                        )
                        return await self.authenticate()
                    except vrchatapi.exceptions.ApiException as e:
                        errors = {"base": e.reason}
                else:
                    errors = {"base": e.reason}
            except vrchatapi.exceptions.ApiException as e:
                errors = {"base": e.reason}

        entry = self.entry

        if config is None:
            config = entry.data if entry is not None else {}

        return self.async_show_form(
            step_id="login",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        description={"suggested_value": config.get(CONF_USERNAME)},
                    ): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.EMAIL, autocomplete="username"
                        )
                    ),
                    vol.Required(
                        CONF_PASSWORD,
                        description={"suggested_value": config.get(CONF_PASSWORD)},
                    ): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.PASSWORD,
                            autocomplete="current-password",
                        )
                    ),
                    vol.Optional(CONF_OPTIONS): section(
                        vol.Schema(
                            {
                                vol.Optional(
                                    CONF_2FA_CODE_ENTITY,
                                    description={
                                        "suggested_value": config.get(
                                            CONF_2FA_CODE_ENTITY
                                        )
                                    },
                                ): EntitySelector(
                                    EntitySelectorConfig(
                                        filter=EntityFilterSelectorConfig(
                                            domain=["sensor", "input_text"]
                                        )
                                    )
                                ),
                                **schema_proxy(suggested_value=config.get(CONF_PROXY)),
                            }
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_email_2fa(
        self, form_data: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Verify email 2FA code."""
        code: str | None = None
        errors: dict[str, str] | None = None

        if form_data is not None:
            try:
                code = form_data[CONF_EMAIL_2FA_CODE]
                await self.api.verify2_fa_email_code(code)
                return await self.authenticate()
            except vrchatapi.exceptions.ApiException as e:
                errors = {"base": e.reason}

        return self.async_show_form(
            step_id="email_2fa",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_EMAIL_2FA_CODE,
                        description={"suggested_value": code},
                    ): selector_2fa_code,
                }
            ),
            errors=errors,
        )

    async def async_step_2fa(
        self, form_data: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Verify 2FA code."""
        code: str | None = None
        errors: dict[str, str] | None = None

        if form_data is not None:
            try:
                code = form_data[CONF_2FA_CODE]
                await self.api.verify2_fa(code)
                return await self.authenticate()
            except vrchatapi.exceptions.ApiException as e:
                errors = {"base": e.reason}

        return self.async_show_form(
            step_id="2fa",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_2FA_CODE,
                        description={"suggested_value": code},
                    ): selector_2fa_code,
                }
            ),
            errors=errors,
        )

    async def async_step_enter_cookies(
        self, form_data: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step to manually enter auth cookies."""
        options: VRChatConfigData | None = None
        cookie: VRChatAuthCookie | None = None
        errors: dict[str, str] | None = None

        if form_data is not None:
            options = form_data.get(CONF_OPTIONS, {})
            cookie = remove_options_from_dict(form_data)

            await self.set_api(VRChatAPI(options, cookie))

            try:
                return await self.authenticate()
            except vrchatapi.exceptions.ApiException as e:
                errors = {"base": e.reason}

        entry = self.entry

        if cookie is None:
            cookie = entry.runtime_data.api.cookie if entry is not None else {}

        if options is None:
            options = (
                {CONF_PROXY: entry.data.get(CONF_PROXY)} if entry is not None else {}
            )

        return self.async_show_form(
            step_id="enter_cookies",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_COOKIE_AUTH,
                        description={"suggested_value": cookie.get(CONF_COOKIE_AUTH)},
                    ): str,
                    vol.Optional(
                        CONF_COOKIE_2FA,
                        description={"suggested_value": cookie.get(CONF_COOKIE_2FA)},
                    ): str,
                    vol.Optional(CONF_OPTIONS): section(
                        vol.Schema(
                            schema_proxy(suggested_value=options.get(CONF_PROXY))
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def authenticate(self):
        """Authenticate and complete setup with configs stored in self.api."""
        return await self.complete_setup(
            self.api.config, self.api.cookie, await self.api.get_current_user()
        )

    async def complete_setup(
        self,
        config: VRChatConfigData,
        cookie: VRChatAuthCookie,
        current_user: CurrentUser,
    ):
        """Final steps to complete setup."""

        await self.close_api()

        _LOGGER.info(current_user)

        await self.async_set_unique_id(current_user["id"], raise_on_progress=True)

        entry = self.entry
        if entry is None:
            self._abort_if_unique_id_configured()
        else:
            self._abort_if_unique_id_mismatch()

        await get_vrchat_auth_cookie_store(self.hass, current_user["id"]).async_save(
            cookie
        )
        InitialCurrentUserData[current_user["id"]] = current_user

        entry = self.entry
        if entry is not None:
            if CONF_PASSWORD in entry.data:
                try:
                    async with entry.runtime_data.api.copy() as api:
                        await entry.runtime_data.close()
                        await api.logout()
                except Exception:
                    _LOGGER.exception("Error logging out.")
            return self.async_update_reload_and_abort(
                entry,
                title=current_user["username"],
                data=config,
            )

        return self.async_create_entry(title=current_user["username"], data=config)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


def remove_options_from_dict(d: dict):
    """Remove `options` from a dict. Returns a copy."""
    d = d.copy()
    d.pop(CONF_OPTIONS, None)
    return d


selector_2fa_code: Final = TextSelector(
    TextSelectorConfig(type=TextSelectorType.TEL, autocomplete="one-time-code")
)


def schema_proxy(suggested_value: str | None = None):
    """Get proxy schema."""
    return {
        vol.Optional(
            CONF_PROXY,
            description={"suggested_value": suggested_value},
        ): TextSelector(TextSelectorConfig(type=TextSelectorType.URL))
    }
