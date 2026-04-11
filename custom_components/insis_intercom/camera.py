import logging

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import InsisCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: InsisCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for domofon in coordinator.domofons:
        urls = coordinator.video_urls.get(domofon["id"])
        if urls:
            entities.append(InsisCamera(coordinator, domofon, urls, is_alt=False))
            if urls.get("alt_rtsp") or urls.get("alt_hls") or urls.get("alt_jpeg"):
                entities.append(InsisCamera(coordinator, domofon, urls, is_alt=True))
    async_add_entities(entities)


class InsisCamera(CoordinatorEntity, Camera):
    _attr_has_entity_name = True
    _attr_supported_features = CameraEntityFeature.STREAM

    def __init__(
        self, coordinator: InsisCoordinator, domofon: dict, urls: dict, is_alt: bool
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._domofon = domofon
        self._domofon_id = domofon["id"]
        self._urls = urls
        self._is_alt = is_alt
        if is_alt:
            self._attr_unique_id = f"insis_camera_{self._domofon_id}_alt"
            self._attr_name = f"{domofon['name']} (камера 2)"
        else:
            self._attr_unique_id = f"insis_camera_{self._domofon_id}"
            self._attr_name = domofon["name"]
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"domofon_{domofon['id']}")},
        }

    @property
    def is_streaming(self) -> bool:
        return True

    async def stream_source(self) -> str | None:
        urls = self.coordinator.video_urls.get(self._domofon_id, self._urls)
        if self._is_alt:
            return urls.get("alt_rtsp")
        return urls.get("rtsp") or urls.get("alt_rtsp")

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        urls = self.coordinator.video_urls.get(self._domofon_id, self._urls)
        if self._is_alt:
            jpeg_url = urls.get("alt_jpeg")
        else:
            jpeg_url = urls.get("jpeg") or urls.get("alt_jpeg")
        if not jpeg_url:
            return None
        try:
            session = self.coordinator.api._session
            if session is None or session.closed:
                session = await self.coordinator.api._get_session()
            resp = await session.get(jpeg_url, timeout=10)
            if resp.status == 200:
                return await resp.read()
        except Exception as e:
            _LOGGER.error("Failed to get snapshot for %s: %s", self._attr_name, e)
        return None
