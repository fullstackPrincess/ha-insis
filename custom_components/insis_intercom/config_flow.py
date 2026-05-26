import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_REFRESH_TOKEN, CONF_PHONE
from .api import InsisApi

_LOGGER = logging.getLogger(__name__)


class InsisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._phone: str = ""
        self._reauth_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            self._phone = user_input[CONF_PHONE]
            if not self._phone.startswith("+"):
                self._phone = "+" + self._phone
            try:
                result = await InsisApi.request_sms(self._phone)
                if "ttl" in result:
                    return await self.async_step_code()
                errors["base"] = "sms_failed"
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_PHONE): str,
            }),
            errors=errors,
            description_placeholders={"phone_hint": "+79991234567"},
        )

    async def async_step_code(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            code = user_input["code"]
            try:
                result = await InsisApi.authenticate(self._phone, code)
                if "refreshToken" in result:
                    if self._reauth_entry is not None:
                        self.hass.config_entries.async_update_entry(
                            self._reauth_entry,
                            data={
                                **self._reauth_entry.data,
                                CONF_REFRESH_TOKEN: result["refreshToken"],
                            },
                        )
                        await self.hass.config_entries.async_reload(
                            self._reauth_entry.entry_id
                        )
                        return self.async_abort(reason="reauth_successful")
                    await self.async_set_unique_id(self._phone)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"Домофон ({self._phone})",
                        data={
                            CONF_PHONE: self._phone,
                            CONF_REFRESH_TOKEN: result["refreshToken"],
                        },
                    )
                errors["base"] = "invalid_code"
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="code",
            data_schema=vol.Schema({
                vol.Required("code"): str,
            }),
            errors=errors,
            description_placeholders={"phone": self._phone},
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> FlowResult:
        """Triggered automatically when ConfigEntryAuthFailed raised."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        if self._reauth_entry is not None:
            self._phone = self._reauth_entry.data.get(CONF_PHONE, "")
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            try:
                result = await InsisApi.request_sms(self._phone)
                if "ttl" in result:
                    return await self.async_step_code()
                errors["base"] = "sms_failed"
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={"phone": self._phone},
        )
