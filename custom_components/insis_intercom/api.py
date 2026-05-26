import logging
import aiohttp
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import SSO_BASE_URL, API_BASE_URL, APPLICATION_ID, CONF_REFRESH_TOKEN

_LOGGER = logging.getLogger(__name__)


class InsisApi:
    def __init__(
        self,
        refresh_token: str,
        hass: HomeAssistant | None = None,
        entry: ConfigEntry | None = None,
    ) -> None:
        self._refresh_token = refresh_token
        self._hass = hass
        self._entry = entry
        self._access_token: str | None = None
        self._token_expires: float = 0
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    def _persist_refresh_token(self, new_token: str) -> None:
        """Save rotated refreshToken back into the config entry."""
        if new_token == self._refresh_token:
            return
        self._refresh_token = new_token
        if self._hass and self._entry:
            new_data = {**self._entry.data, CONF_REFRESH_TOKEN: new_token}
            self._hass.config_entries.async_update_entry(self._entry, data=new_data)
            _LOGGER.debug("Insis refresh_token rotated and persisted")

    async def _ensure_token(self) -> str:
        if self._access_token and time.time() < self._token_expires - 30:
            return self._access_token
        session = await self._get_session()
        try:
            resp = await session.post(
                f"{SSO_BASE_URL}/api/authorization/refresh",
                headers={"Content-Type": "application/json"},
                cookies={"refreshToken": self._refresh_token},
            )
        except aiohttp.ClientError as err:
            _LOGGER.warning("Insis network error during token refresh: %s", err)
            raise

        if resp.status == 401:
            body = await resp.text()
            _LOGGER.error(
                "Insis refresh_token rejected (HTTP 401). "
                "Refresh token expired or revoked — user must re-auth. Body: %s",
                body[:200],
            )
            raise ConfigEntryAuthFailed("refresh_token expired or revoked")

        try:
            data = await resp.json()
        except aiohttp.ContentTypeError as err:
            body = await resp.text()
            _LOGGER.error(
                "Insis refresh returned non-JSON (HTTP %s): %s",
                resp.status,
                body[:200],
            )
            raise Exception(f"Token refresh non-JSON response: {err}") from err

        if "accessToken" not in data:
            _LOGGER.error(
                "Insis refresh response missing accessToken (HTTP %s): %s",
                resp.status,
                data,
            )
            if resp.status in (401, 403):
                raise ConfigEntryAuthFailed("refresh_token expired or revoked")
            raise Exception(f"Token refresh failed: {data}")

        # Persist rotated refresh_token if server set a new one
        new_refresh = resp.cookies.get("refreshToken")
        if new_refresh is not None:
            self._persist_refresh_token(new_refresh.value)

        self._access_token = data["accessToken"]
        self._token_expires = time.time() + 850
        return self._access_token

    async def _request(self, method: str, path: str, **kwargs) -> dict | list:
        token = await self._ensure_token()
        session = await self._get_session()
        headers = kwargs.pop("headers", {})
        headers["access-token"] = token
        resp = await session.request(
            method, f"{API_BASE_URL}{path}", headers=headers, **kwargs
        )
        if resp.status == 403:
            self._access_token = None
            token = await self._ensure_token()
            headers["access-token"] = token
            resp = await session.request(
                method, f"{API_BASE_URL}{path}", headers=headers, **kwargs
            )
        if resp.status == 401:
            body = await resp.text()
            _LOGGER.error(
                "Insis API %s %s rejected (HTTP 401): %s",
                method, path, body[:200],
            )
            raise ConfigEntryAuthFailed("API request unauthorized")
        return await resp.json()

    async def get_apartments(self) -> list:
        return await self._request("GET", "/domo.apartment")

    async def get_domofons(self, apartment_id: int) -> list:
        return await self._request("GET", f"/v2/domo.apartment/{apartment_id}/domofon")

    async def open_door(self, domofon_id: int, door_id: int = 0) -> dict:
        return await self._request(
            "POST",
            f"/domo.domofon/{domofon_id}/open",
            json={"door_id": door_id},
        )

    async def get_video_urls(self, intercom_ids: list[int]) -> list:
        return await self._request(
            "POST",
            "/v2/domo.domofon/urlsOnType",
            json={
                "intercoms_id": intercom_ids,
                "media_type": ["HLS", "RTSP", "JPEG"],
            },
        )

    async def get_screenshot(self, domofon_id: int) -> dict:
        return await self._request(
            "POST",
            "/v2/domo.domofon/getSingleScreenshot",
            json={"domofon_id": domofon_id, "timestamp": int(time.time())},
        )

    async def get_history(self) -> dict:
        return await self._request("GET", "/domo.history")

    @staticmethod
    async def authenticate(phone: str, code: str) -> dict:
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f"{SSO_BASE_URL}/api/authorization/login/sms",
                json={
                    "phone": phone,
                    "applicationId": APPLICATION_ID,
                    "code": code,
                },
            )
            data = await resp.json()
            cookies = resp.cookies
            refresh = cookies.get("refreshToken")
            if refresh:
                data["refreshToken"] = refresh.value
            return data

    @staticmethod
    async def request_sms(phone: str) -> dict:
        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f"{SSO_BASE_URL}/api/authorization/login/phone",
                json={"phone": phone, "applicationId": APPLICATION_ID},
            )
            return await resp.json()

    async def validate(self) -> bool:
        try:
            apartments = await self.get_apartments()
            return isinstance(apartments, list)
        except ConfigEntryAuthFailed:
            raise
        except Exception as err:
            _LOGGER.warning("Insis validate failed: %s", err)
            return False
