import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import DOMAIN, PLATFORMS, CONF_REFRESH_TOKEN
from .api import InsisApi
from .coordinator import InsisCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api = InsisApi(entry.data[CONF_REFRESH_TOKEN], hass=hass, entry=entry)

    try:
        ok = await api.validate()
    except ConfigEntryAuthFailed:
        await api.close()
        raise
    except Exception as err:
        # Network/DNS/cloud hiccup while HA was starting. Returning False here
        # would leave the entry in a terminal setup_error state — no retries,
        # entities stay unavailable until someone reloads it by hand. Ask HA to
        # retry with backoff instead.
        _LOGGER.warning("Insis cloud unavailable, will retry: %s", err)
        await api.close()
        raise ConfigEntryNotReady(f"Insis cloud unavailable: {err}") from err

    if not ok:
        await api.close()
        raise ConfigEntryNotReady("Insis API returned an unexpected payload")

    coordinator = InsisCoordinator(hass, api)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        # first_refresh raises ConfigEntryNotReady/AuthFailed — close the
        # session so a retry does not leak one per attempt.
        await api.close()
        raise

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: InsisCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.api.close()
    return unload_ok
