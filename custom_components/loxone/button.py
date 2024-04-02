"""
Loxone Switches

For more details about this component, please refer to the documentation at
https://github.com/JoDehli/PyLoxone
"""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import LoxoneEntity
from .const import DOMAIN, SENDDOMAIN, SECUREDSENDDOMAIN
from .helpers import (get_all, add_room_and_cat_to_value_values)
from .miniserver import get_miniserver_from_hass

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up Loxone Button."""
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entry."""
    miniserver = get_miniserver_from_hass(hass)
    loxconfig = miniserver.lox_config.json
    buttons = []

    """Cycle through all NFC Code Touch devices and generate a button for each configured output-id."""
    for button in get_all(loxconfig, "NfcCodeTouch"):
        for id in button["details"]["accessOutputs"]:
            button = add_room_and_cat_to_value_values(loxconfig, button)
            _LOGGER.info(f"id: {id}")
            button_entity = LoxoneNfcCTButton(**button,output_id=id)
            buttons.append(button_entity)       

    async_add_entities(buttons)


class LoxoneNfcCTButton(LoxoneEntity, ButtonEntity):
    """Representation of a loxone output button"""

    def __init__(self,output_id, **kwargs):
        
        LoxoneEntity.__init__(self, **kwargs)

        """Set the entity-name the same as the output name. Make first letter capital."""
        self._name = output_id.capitalize()

        if "uuidAction" in kwargs:
            self.uuidAction = kwargs["uuidAction"]
        else:
            self.uuidAction = ""

        """Construct a UUID based on the NFC Code Touch's UUID concatenated with the output name."""
        """The outputs themselves don't have a unique ID."""
        self._uuid = self.uuidAction + "-" + output_id
    
        """Set the entity's device to the NFC Code Touch."""
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.uuidAction)},
            name=f"{DOMAIN} {kwargs["name"]}",
            manufacturer="Loxone",
            suggested_area=self.room,
            model="NFC Code Touch",
        )

    def press(self, **kwargs):
        """Push the button. The last character is the output number that needs to be activated."""
        self.hass.bus.async_fire(SENDDOMAIN, dict(uuid=self.uuidAction, value="output/"+self.name[-1]))

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes.

        Implemented by platform classes.
        """
        state_dict = {
            "uuid": self.uuidAction,
            "room": self.room,
            "category": self.cat,
            "device_typ": self.type,
            "platform": "loxone",
        }
        return state_dict

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._uuid
