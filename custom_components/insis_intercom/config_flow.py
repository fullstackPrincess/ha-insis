import logging
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
