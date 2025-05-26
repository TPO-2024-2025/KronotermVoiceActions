import logging

from aiohttp import ClientSession

from collections import namedtuple
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from httpcore import URL

from .kronoterm_enums import (
    APIEndpoint,
    HeatingLoop,
    HeatingLoopMode,
    HeatingLoopStatus,
    HeatPumpOperatingMode,
    WorkingFunction,
)
from .kronoterm_models import KronotermAction

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s [%(levelname)-8s] %(module)s:%(funcName)s:%(lineno)d - %(message)s"
)


class KronotermCloudApi:

    def __init__(self, username: str, password: str, hass: HomeAssistant):
        """Kronoterm heat pump cloud API.
        :param username: Kronoterm cloud username
        :param password: Kronoterm cloud password
        """
        self.username = username
        self.password = password
        self.hass = hass

        self._base_api_url = "https://cloud.kronoterm.com/jsoncgi.php?"
        self._login_url: URL = URL("https://cloud.kronoterm.com/?login=1")
        self.headers = None
        self.session_id = None
        self.session: ClientSession | None = None

        # Heat pump information
        self.hp_id: str | None = None
        self.user_level: str | None = None
        self.location_name: str | None = None
        self.loop_names: str | None = None
        self.active_errors_count: str | None = None


    async def invoke_kronoterm_action(self, action: KronotermAction):
        """Invokes an action on the Kronoterm heat pump."""
        handler = self.map_label_to_function.get(action.action)
        if handler is None:
            raise ValueError(f"Action '{action.action}' not supported")

        # noinspection PyArgumentList
        return await handler(self, **action.parameters)


    async def login(self) -> None:
        if self.session is None:
            self.session = async_get_clientsession(self.hass)

        # Check if already logged in by looking at stored cookies
        if self.session.cookie_jar.filter_cookies(self._login_url).get("PHPSESSID"):
            log.debug("Already logged in, using existing session.")
            return

        login_data = {"username": self.username, "password": self.password}
        resp = await self.session.post(
            self._login_url,
            data=login_data,
            timeout=30
        )
        resp.raise_for_status()

        reason = resp.cookies.get("AuthReason")
        if reason:
            log.error("Login failed: %s", reason.value)
            return

        log.debug("Login successful. Cookies: %s", resp.cookies)


    async def get_raw(self, url: str, **kwargs) -> dict:
        await self.login()
        if self.session is None:
            raise RuntimeError("Session not initialized after login")

        full_url = self._base_api_url + url
        resp = await self.session.get(full_url, **kwargs)
        resp.raise_for_status()
        return await resp.json()


    async def post_raw(self, url: str, **kwargs) -> dict:
        await self.login()
        if self.session is None:
            raise RuntimeError("Session not initialized after login")

        full_url = self._base_api_url + url
        resp = await self.session.post(full_url, **kwargs)
        resp.raise_for_status()
        return await resp.json()


    async def update_heat_pump_basic_information(self):
        """Update heat pump information from INITIAL load data."""

        data = await self.get_initial_data()
        self.hp_id = data.get("hp_id")
        self.user_level = data.get("user_level")
        self.location_name = data.get("Location")
        self.loop_names = data.get("CircleNames")
        self.active_errors_count = int(data.get("ActiveErrorsCnt"))


    async def get_initial_data(self) -> dict:
        """Get initial data.
        :return: initial data
        """
        data = await self.get_raw(APIEndpoint.INITIAL.value)
        return data


    async def get_basic_data(self) -> dict:
        """Get basic view data.
        :return: basic view data
        """
        data = await self.get_raw(APIEndpoint.BASIC.value)
        return data


    async def get_system_review_data(self) -> dict:
        """Get system review view data.
        :return: System review data
        """
        data = await self.get_raw(APIEndpoint.SYSTEM_REVIEW.value)
        return data


    async def get_heating_loop_data(self, loop: HeatingLoop) -> dict:
        """Get heating loop view data. Supports:
        - HEATING_LOOP_1
        - HEATING_LOOP_2
        - TAP_WATER
        :return: Heating loop data
        """
        match loop:
            case HeatingLoop.HEATING_LOOP_1:
                loop_url = APIEndpoint.HEATING_LOOP_1.value
            case HeatingLoop.HEATING_LOOP_2:
                loop_url = APIEndpoint.HEATING_LOOP_2.value
            case HeatingLoop.TAP_WATER:
                loop_url = APIEndpoint.TAP_WATER.value
            case _:
                raise ValueError(f"Heating loop '{loop.name}' not supported")

        data = await self.get_raw(loop_url)
        return data


    async def get_alarms_data(self) -> dict:
        """Get alarm view data.
        :return: Alarm data
        """
        data = await self.get_raw(APIEndpoint.ALARMS.value)
        return data


    async def get_alarms_data_only(self, alarms_data: dict | None = None) -> list[Any]:
        """Get only AlarmsData (list of alarms) part of the alarm response.
        :param alarms_data: If supplied, it will be parsed for AlarmsData otherwise make an API request
        :return: list of alarms
        """
        if alarms_data is not None:
            return alarms_data.get("AlarmsData", [])
        data = await self.get_alarms_data()
        return data.get("AlarmsData", [])


    async def get_theoretical_use_data(self) -> dict:
        """Get theoretical use view data. As displayed in 'Theoretical use histogram'.
        :return: Theoretical use data
        """
        url = "TopPage=4&Subpage=4&Action=4"
        # TODO: research dValues[]!!!

        day_of_year = datetime.now().timetuple().tm_yday
        year = datetime.now().timetuple().tm_year
        data = {
            "year": str(year),
            "d1": str(day_of_year),  # day of the year
            "d2": "0",  # hour
            "type": "day",  # # year, month, hour, week, day, hour
            "aValues[]": "17",  # # data to graph
            "dValues[]": ["90", "0", "91", "92", "1", "2", "24", "71"],  # # data to graph
        }
        data = await self.post_raw(url, data=data, headers=self.headers)
        return data


    async def get_outside_temperature(self) -> float:
        """Get the current outside temperature.
        :return: Outside temperature in [C]
        """
        basic = await self.get_basic_data()
        data = basic["TemperaturesAndConfig"]["outside_temp"]
        return float(data)


    async def get_working_function(self) -> WorkingFunction:
        """Get currently set HP working function
        :return: WorkingFunction Enum
        """
        basic = await self.get_basic_data()
        data = basic["TemperaturesAndConfig"]["working_function"]
        return WorkingFunction(data)


    async def get_room_temp(self) -> float:
        """Get current room temperature.
        :return: Room temperature in [C]
        """
        # TODO: This could probably be different if kontrol thermostat is connected to different heating loop?
        basic = await self.get_basic_data()
        room_temp = basic["TemperaturesAndConfig"]["heating_circle_2_temp"]
        return float(room_temp)


    async def get_reservoir_temp(self) -> float:
        """Get current reservoir temperature.
        :return: reservoir temperature in [C]
        """
        basic = await self.get_basic_data()
        reservoir_temp = basic["TemperaturesAndConfig"]["reservoir_temp"]
        return float(reservoir_temp)


    async def get_outlet_temp(self) -> float:
        """Get current HP outlet temperature.
        :return: HP outlet temperature in [C]
        """
        review_data = await self.get_system_review_data()
        dv_temp = review_data["CurrentFunctionData"][0]["dv_temp"]
        return float(dv_temp)


    async def get_sanitary_water_temp(self) -> float:
        """Get current sanitary water temperature.
        :return: Sanitary water temperature in [C]
        """
        basic = await self.get_basic_data()
        dv_temp = basic["TemperaturesAndConfig"]["tap_water_temp"]
        return float(dv_temp)


    async def get_heating_loop_target_temperature(self, loop: HeatingLoop) -> float:
        """Get heating loop target temperature.
        :return: The set heating loop target temperature in [C]
        """
        heating_loop_data = await self.get_heating_loop_data(loop)
        set_temp = heating_loop_data["HeatingCircleData"]["circle_temp"]
        return float(set_temp)


    async def get_heating_loop_status(self, loop: HeatingLoop) -> HeatingLoopStatus:
        """Get HP working status.
           - ECO
           - NORMAL
           - COMFORT
           - OFF
           - AUTO
        :return: HP working status
        """
        heating_loop_data = await self.get_heating_loop_data(loop)
        status = heating_loop_data["HeatingCircleData"]["circle_status"]
        return HeatingLoopStatus(status)


    async def get_heating_loop_mode(self, loop: HeatingLoop) -> HeatingLoopMode:
        """Get the mode of heating loop:
           - ON
           - OFF
           - AUTO
        :param loop: for which loop to get mode
        :return mode: mode of the loop
        """
        heating_loop_data = await self.get_heating_loop_data(loop)
        mode = heating_loop_data["HeatingCircleData"]["circle_mode"]
        return HeatingLoopMode(mode)


    async def get_heat_pump_operating_mode(self) -> HeatPumpOperatingMode:
        """Get the mode of heating loop:
           - COMFORT
           - AUTO
           - ECO
        :return mode: mode of the heat pump
        """
        basic = await self.get_basic_data()
        mode = basic["TemperaturesAndConfig"]["main_mode"]
        return HeatPumpOperatingMode(mode)


    async def set_heating_loop_mode(self, loop: HeatingLoop, mode: HeatingLoopMode) -> bool:
        """Set the mode of heating loop:
           - ON
           - OFF
           - AUTO
        :param loop: for which loop to set mode
        :param mode: mode of the loop
        """
        match loop:
            case HeatingLoop.HEATING_LOOP_1:
                loop_url = APIEndpoint.HEATING_LOOP_1_SET.value
                page = 5
            case HeatingLoop.HEATING_LOOP_2:
                loop_url = APIEndpoint.HEATING_LOOP_2_SET.value
                page = 6
            case HeatingLoop.TAP_WATER:
                loop_url = APIEndpoint.TAP_WATER_SET.value
                page = 9
            case _:
                raise ValueError(f"Heating loop '{loop.name}' not supported")
        request_data = {"param_name": "circle_status", "param_value": mode.value, "page": page}
        response = await self.post_raw(loop_url, data=request_data, headers=self.headers)
        return response.get("result", False) == "success"


    async def set_heat_pump_operating_mode(self, mode: HeatPumpOperatingMode):
        """Set the heat pump operating mode:
           - COMFORT
           - AUTO
           - ECO
        :param mode: mode of the heat pump
        """
        request_data = {"param_name": "main_mode", "param_value": mode.value, "page": -1}
        response = await self.post_raw(APIEndpoint.ADVANCED_SETTINGS.value, data=request_data, headers=self.headers)
        return response.get("result", False) == "success"


    async def set_heating_loop_target_temperature(self, loop: HeatingLoop, temperature: int | float) -> bool:
        """Set the heating loop temperature.
        :param loop: For which loop to set temperature
        :param temperature: temperature to set
        """
        match loop:
            case HeatingLoop.HEATING_LOOP_1:
                loop_url = APIEndpoint.HEATING_LOOP_1_SET.value
                page = 5
            case HeatingLoop.HEATING_LOOP_2:
                loop_url = APIEndpoint.HEATING_LOOP_2_SET.value
                page = 6
            case HeatingLoop.TAP_WATER:
                loop_url = APIEndpoint.TAP_WATER_SET.value
                page = 9
            case _:
                raise ValueError(f"Heating loop '{loop.name}' not supported")
        request_data = {"param_name": "circle_temp", "param_value": temperature, "page": page}
        response = await self.post_raw(loop_url, data=request_data, headers=self.headers)
        return response.get("result", False) == "success"


    async def get_theoretical_power_consumption(self):
        """Get theoretically calculated power consumption (calculated by HP and/or cloud).
        :return: Named tuple with the latest daily power consumption in [kWh]
        """
        data = await self.get_theoretical_use_data()

        heating_consumption = data["trend_consumption"]["CompHeating"][-1]
        cooling_consumption = data["trend_consumption"]["CompActiveCooling"][-1]
        tap_water_consumption = data["trend_consumption"]["CompTapWater"][-1]
        pumps_consumption = data["trend_consumption"]["CPLoops"][-1]
        all_consumption = heating_consumption + cooling_consumption + tap_water_consumption + pumps_consumption

        HPConsumption = namedtuple("HPConsumption", ["heating", "cooling", "tap_water", "pumps", "all"])
        return HPConsumption(
            heating=heating_consumption,
            cooling=cooling_consumption,
            tap_water=tap_water_consumption,
            pumps=pumps_consumption,
            all=all_consumption,
        )


    async def get_heating_loop1_data(self):
        return await self.get_heating_loop_data(HeatingLoop.HEATING_LOOP_1)


    async def get_heating_loop2_data(self):
        return await self.get_heating_loop_data(HeatingLoop.HEATING_LOOP_2)


    async def get_tap_water_data(self):
        return await self.get_heating_loop_data(HeatingLoop.TAP_WATER)


    async def get_heating_loop1_mode(self):
        return await self.get_heating_loop_mode(HeatingLoop.HEATING_LOOP_1)


    async def get_heating_loop2_mode(self):
        return await self.get_heating_loop_mode(HeatingLoop.HEATING_LOOP_2)


    async def get_tap_water_mode(self):
        return await self.get_heating_loop_mode(HeatingLoop.TAP_WATER)


    async def set_heating_loop1_mode(self, mode):
        return await self.set_heating_loop_mode(HeatingLoop.HEATING_LOOP_1, mode),


    async def set_heating_loop2_mode(self, mode):
        return await self.set_heating_loop_mode(HeatingLoop.HEATING_LOOP_2, mode),


    async def set_tap_water_mode(self, mode):
        return await self.set_heating_loop_mode(HeatingLoop.TAP_WATER, mode),


    async def get_heating_loop1_target_temperature(self):
        return await self.get_heating_loop_target_temperature(HeatingLoop.HEATING_LOOP_1)


    async def get_heating_loop2_target_temperature(self):
        return await self.get_heating_loop_target_temperature(HeatingLoop.HEATING_LOOP_2)


    async def get_tap_water_target_temperature(self):
        return await self.get_heating_loop_target_temperature(HeatingLoop.TAP_WATER)


    async def set_heating_loop1_target_temperature(self, temperature):
        return await self.set_heating_loop_target_temperature(HeatingLoop.HEATING_LOOP_1, temperature),


    async def set_heating_loop2_target_temperature(self, temperature):
        return await self.set_heating_loop_target_temperature(HeatingLoop.HEATING_LOOP_2, temperature),


    async def set_tap_water_target_temperature(self, temperature):
        return await self.set_heating_loop_target_temperature(HeatingLoop.TAP_WATER, temperature),


    async def get_heating_loop1_status(self):
        return await self.get_heating_loop_status(HeatingLoop.HEATING_LOOP_1)


    async def get_heating_loop2_status(self):
        return self.get_heating_loop_status(HeatingLoop.HEATING_LOOP_2)


    async def get_tap_water_status(self):
        return await self.get_heating_loop_status(HeatingLoop.TAP_WATER)


    map_label_to_function = {
        "get_outside_temperature": get_outside_temperature,
        "get_room_temp": get_room_temp,
        "get_reservoir_temp": get_reservoir_temp,
        "get_sanitary_water_temp": get_sanitary_water_temp,
        "get_outlet_temp": get_outlet_temp,
        "get_working_function": get_working_function,
        "get_heat_pump_operating_mode": get_heat_pump_operating_mode,
        "get_heating_loop1_target_temperature": get_heating_loop1_target_temperature,
        "get_heating_loop2_target_temperature": get_heating_loop2_target_temperature,
        "get_heating_loop1_mode": get_heating_loop1_mode,
        "get_heating_loop2_mode": get_heating_loop2_mode,
        "get_heating_loop1_status": get_heating_loop1_status,
        "get_heating_loop2_status": get_heating_loop2_status,
        "get_alarms_data_only": get_alarms_data_only,
        "get_theoretical_power_consumption": get_theoretical_power_consumption,
        "set_heating_loop_1_temp": set_heating_loop1_target_temperature,
        "set_heating_loop_2_temp": set_heating_loop2_target_temperature,
    }