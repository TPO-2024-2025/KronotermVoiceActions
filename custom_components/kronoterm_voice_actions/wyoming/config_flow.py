"""Config flow for Wyoming integration."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

import voluptuous as vol

from homeassistant.config_entries import SOURCE_HASSIO, ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector
from homeassistant.helpers.service_info.hassio import HassioServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .const import DOMAIN
from .data import WyomingService

_LOGGER = logging.getLogger(__name__)


CONF_TYPE = "type"
ENTRY_TYPE_REMOTE = "remote_service"
ENTRY_TYPE_CUSTOM = "custom_agent"

CUSTOM_AGENT_UNIQUE_ID = f"{DOMAIN}_custom_agent"

STEP_USER_TYPE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TYPE): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(
                        value=ENTRY_TYPE_REMOTE,
                        label="Connect to a remote Wyoming protocol service (TTS, STT, Satellite, etc.)",
                    ),
                    selector.SelectOptionDict(
                        value=ENTRY_TYPE_CUSTOM,
                        label="Set up the custom Kronoterm conversation agent",
                    ),
                ],
                mode=selector.SelectSelectorMode.LIST,
            )
        ),
    }
)

STEP_MQTT_DETAILS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT): int,
        # Optional: Add fields for MQTT username/password if your broker needs auth
        vol.Optional(CONF_USERNAME): str,
        vol.Optional(CONF_PASSWORD): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
    }
)

STEP_REMOTE_SERVICE_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT): int,
    }
)

STEP_CUSTOM_AGENT_AUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
        ),
        vol.Required(CONF_PASSWORD): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
    }
)

STEP_CONFIRM_SCHEMA = vol.Schema({})


async def _validate_remote_connection(
    hass: HomeAssistant, host: str, port: int
) -> tuple[str | None, str | None]:
    """Validate connection to remote service and get its name."""
    service = await WyomingService.create(host, port)
    if service is None:
        return "cannot_connect", None
    if not service.has_services():
        return "no_services", None

    name = service.get_name() or f"{host}:{port}"
    return None, name


class WyomingConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Wyoming integration."""

    VERSION = 1

    _entry_type: str | None = None
    _host: str | None = None
    _port: int | None = None
    _discovered_name: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step where the user chooses the type."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_TYPE_SCHEMA
            )

        self._entry_type = user_input[CONF_TYPE]

        if self._entry_type == ENTRY_TYPE_REMOTE:
            return await self.async_step_remote_service()

        if self._entry_type == ENTRY_TYPE_CUSTOM:
            await self.async_set_unique_id(CUSTOM_AGENT_UNIQUE_ID)
            self._abort_if_unique_id_configured()
            return await self.async_step_custom_agent_auth()
            # return self.async_abort(reason="unknown_entry_type")

        return self.async_abort(reason="unknown_entry_type")

    async def async_step_remote_service(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the configuration for a remote Wyoming service."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port = user_input[CONF_PORT]
            unique_id = f"{self._host}_{self._port}"

            # Check if this host/port combination is already configured
            await self.async_set_unique_id(unique_id, raise_on_progress=False)
            self._abort_if_unique_id_configured(
                updates={CONF_HOST: self._host, CONF_PORT: self._port}
            )

            # Validate connection
            error_reason, service_name = await _validate_remote_connection(
                self.hass, self._host, self._port
            )

            if error_reason:
                errors["base"] = error_reason
            else:
                # Connection successful, create entry without credentials
                _LOGGER.debug(
                    "Creating remote service entry. Title: '%s', Data: %s",
                    service_name,
                    {CONF_HOST: self._host, CONF_PORT: self._port},
                )
                return self.async_create_entry(
                    title=service_name or f"{self._host}:{self._port}",
                    data={
                        CONF_HOST: self._host,
                        CONF_PORT: self._port,
                        CONF_TYPE: ENTRY_TYPE_REMOTE,
                    },
                )

        # Show form to collect host/port
        return self.async_show_form(
            step_id="remote_service",
            data_schema=STEP_REMOTE_SERVICE_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_custom_agent_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the authentication step for the custom agent."""
        errors: dict[str, str] = {}
        description_placeholders = {"name": "Kronoterm Conversation Agent"}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            if not errors:
                _LOGGER.debug(
                    "Creating custom agent entry. Title: '%s'",
                    description_placeholders["name"],
                )
                return self.async_create_entry(
                    title=description_placeholders["name"],
                    data={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_TYPE: ENTRY_TYPE_CUSTOM,
                    },
                )

        return self.async_show_form(
            step_id="custom_agent_auth",
            data_schema=STEP_CUSTOM_AGENT_AUTH_SCHEMA,
            description_placeholders=description_placeholders,
            errors=errors,
        )

    async def async_step_hassio(
        self, discovery_info: HassioServiceInfo
    ) -> ConfigFlowResult:
        """Handle Supervisor add-on discovery."""
        _LOGGER.debug("Supervisor discovery info: %s", discovery_info)

        self._entry_type = ENTRY_TYPE_REMOTE
        host = urlparse(discovery_info.config["uri"]).hostname
        port = urlparse(discovery_info.config["uri"]).port
        self._host = host
        self._port = port
        name = discovery_info.name

        await self.async_set_unique_id(discovery_info.slug)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})

        error_reason, service_name = await _validate_remote_connection(
            self.hass, host, port
        )
        if error_reason:
            _LOGGER.warning(
                "Could not connect to discovered Hass.io service %s (%s:%s): %s",
                name,
                host,
                port,
                error_reason,
            )
            return self.async_abort(reason=error_reason)

        self._discovered_name = service_name

        self.context.update(
            {
                "title_placeholders": {"name": name},
                "configuration_url": f"homeassistant://hassio/addon/{discovery_info.slug}/info",
                "source": SOURCE_HASSIO,
            }
        )
        return await self.async_step_hassio_confirm()

    async def async_step_hassio_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask user to confirm adding the discovered Hass.io add-on."""
        _LOGGER.debug(
            "Showing zeroconf confirmation form for service: %s", self._discovered_name
        )

        if user_input is not None:
            # User confirmed, create the entry
            return self.async_create_entry(
                title=self._discovered_name,
                data={
                    CONF_HOST: self._host,
                    CONF_PORT: self._port,
                    CONF_TYPE: ENTRY_TYPE_REMOTE,
                },
            )

        # Show confirmation form
        return self.async_show_form(
            step_id="hassio_confirm",
            description_placeholders={"addon": self._discovered_name},
            data_schema=STEP_CONFIRM_SCHEMA,
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle zeroconf discovery."""
        _LOGGER.debug("Zeroconf discovery info: %s", discovery_info)

        self._entry_type = ENTRY_TYPE_REMOTE
        host = discovery_info.host
        port = discovery_info.port
        self._host = host
        self._port = port
        if port is None:
            return self.async_abort(reason="no_port")

        error_reason, service_name = await _validate_remote_connection(
            self.hass, host, port
        )
        if error_reason:
            return self.async_abort(reason=error_reason)
        self._discovered_name = service_name

        unique_id = f"{host}_{port}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})

        self.context.update(
            {
                "title_placeholders": {"name": service_name},
                "source": "zeroconf",
            }
        )

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask user to confirm adding the discovered Zeroconf service."""
        _LOGGER.debug(
            "Showing zeroconf confirmation form for service: %s", self._discovered_name
        )
        if user_input is not None:
            # User confirmed, create the entry
            return self.async_create_entry(
                title=self._discovered_name,
                data={
                    CONF_HOST: self._host,
                    CONF_PORT: self._port,
                    CONF_TYPE: ENTRY_TYPE_REMOTE,
                },
            )

        # Show confirmation form
        # Ensure strings.json has a "zeroconf_confirm" step description
        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={"name": self._discovered_name},
            data_schema=STEP_CONFIRM_SCHEMA,  # Empty schema, just needs submit
        )
