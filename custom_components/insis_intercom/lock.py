import logging

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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
        if domofon.get("status", {}).get("is_available_to_open"):
            for door in domofon.get("doors", []):
                entities.append(InsisLock(coordinator, domofon, door))
    async_add_entities(entities)


class InsisLock(CoordinatorEntity, LockEntity):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: InsisCoordinator, domofon: dict, door: dict
    ) -> None:
        super().__init__(coordinator)
        self._domofon = domofon
        self._door = door
        self._domofon_id = domofon["id"]
        self._door_id = door["number"]
        self._attr_unique_id = f"insis_lock_{self._domofon_id}_{self._door_id}"
        self._attr_name = domofon["name"]
        self._attr_is_locked = True
        self._attr_device_info = _device_info(domofon)

    @property
    def is_locked(self) -> bool:
        return True

    async def async_unlock(self, **kwargs) -> None:
        result = await self.coordinator.api.open_door(self._domofon_id, self._door_id)
        _LOGGER.info("Door opened: %s -> %s", self._attr_name, result)
        self._attr_is_locked = False
        self.async_write_ha_state()
        self.hass.loop.call_later(5, self._relock)

    async def async_lock(self, **kwargs) -> None:
        pass

    @callback
    def _relock(self) -> None:
        self._attr_is_locked = True
        self.async_write_ha_state()


def _device_info(domofon: dict) -> dict:
    return {
        "identifiers": {(DOMAIN, f"domofon_{domofon['id']}")},
        "name": domofon["name"],
        "manufacturer": domofon.get("model", {}).get("manufacturer", "Insis"),
        "model": domofon.get("model", {}).get("name", ""),
        "suggested_area": domofon.get("_address", ""),
    }
