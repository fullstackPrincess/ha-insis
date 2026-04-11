import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import InsisApi

_LOGGER = logging.getLogger(__name__)


class InsisCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, api: InsisApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Инсис Домофон",
            update_interval=timedelta(minutes=5),
        )
        self.api = api
        self.apartments: list = []
        self.domofons: list = []
        self.video_urls: dict = {}

    async def _async_update_data(self) -> dict:
        self.apartments = await self.api.get_apartments()

        all_domofons = []
        intercom_ids = []
        for apt in self.apartments:
            domofons = await self.api.get_domofons(apt["id"])
            for d in domofons:
                d["_apartment_name"] = apt["name"]
                d["_address"] = apt["location"]["readable_address"]
            all_domofons.extend(domofons)
            intercom_ids.extend([d["id"] for d in domofons])

        self.domofons = all_domofons

        if intercom_ids:
            urls = await self.api.get_video_urls(intercom_ids)
            self.video_urls = {u["intercom_id"]: u for u in urls}

        return {
            "apartments": self.apartments,
            "domofons": self.domofons,
            "video_urls": self.video_urls,
        }
