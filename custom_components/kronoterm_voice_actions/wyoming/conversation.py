import logging

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.util import ulid as ulid_util

from .mqtt_client import MqttClient
from .matcher import match_command

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up the Wyoming conversation integration."""
    _LOGGER.info("🔥 Setting up Wyoming Custom Conversation Agent Entity 🔥")

    async_add_entities(
        [
            WyomingConversationEntity(config_entry, hass),
        ]
    )


class WyomingConversationEntity(
    conversation.ConversationEntity, conversation.AbstractConversationAgent
):
    """Wyoming conversation agent - Represents the custom Kronoterm agent."""

    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry: ConfigEntry,
        hass: HomeAssistant,
        #
    ) -> None:
        """Initialize the custom conversation agent."""
        super().__init__()
        self.entry = config_entry
        self.hass = hass

        self._attr_name = config_entry.title

        self._attr_supported_features = conversation.ConversationEntityFeature.CONTROL

        self._supported_languages = ["sl"]

        self._attr_unique_id = f"{config_entry.entry_id}-conversation"

        _LOGGER.debug(
            "Initialized custom conversation agent: %s (ID: %s)",
            self._attr_name,
            self._attr_unique_id,
        )

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""

        return self._supported_languages

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process user input using the custom matcher."""
        conversation_id = user_input.conversation_id or ulid_util.ulid_now()
        intent_response = intent.IntentResponse(language=user_input.language)

        try:
            response = await execute_command(user_input.text)
            intent_response.async_set_speech(response)
        except ValueError:
            intent_response.async_set_speech("Oprostite, tega nisem razumel.")

        except Exception as e:
            _LOGGER.exception("Error during command execution" + str(e))
            intent_response.async_set_speech("Pri izvajanju je prišlo do napake")
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN, f"Error: {e}"
            )
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )

        return conversation.ConversationResult(
            response=intent_response, conversation_id=conversation_id
        )


async def execute_command(text: str) -> str:
    client = MqttClient()
    commands = client.map_template_to_function.keys()
    action, parameter = match_command(text, commands)
    return await client.invoke_kronoterm_action(action, parameter)