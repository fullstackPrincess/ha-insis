import logging

from homeassistant.components.button import ButtonEntity
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
        if domofon.get("status", {}).get("is_available_to_open"):
            for door in domofon.get("doors", []):
                entities.append(InsisOpenButton(coordinator, domofon, door))
    async_add_entities(entities)


class InsisOpenButton(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:door-open"

    def __init__(
        self, coordinator: InsisCoordinator, domofon: dict, door: dict
    ) -> None:
        super().__init__(coordinator)
        self._domofon_id = domofon["id"]
        self._door_id = door["number"]
        self._attr_unique_id = f"insis_open_{self._domofon_id}_{self._door_id}"
        self._attr_name = f"Открыть {domofon['name']}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"domofon_{domofon['id']}")},
        }

    async def async_press(self) -> None:
        result = await self.coordinator.api.open_door(self._domofon_id, self._door_id)
        _LOGGER.info("Door opened via button: %s -> %s", self._attr_name, result)
