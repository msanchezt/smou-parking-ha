"""Config flow for SMOU Parking integration."""
from __future__ import annotations

import os
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DEFAULT_JSON_PATH

YEARS = [2023, 2024, 2025]
RATE_TYPES_BY_YEAR = {
    2023: {
        "blue_regular": 3.00,
        "blue_eco": 2.25,
        "blue_zero": 0.0,
        "green_regular": 3.5,
        "green_eco": 2.75,
        "green_zero": 0.5
    },
    2024: {
        "blue_regular": 3.00,
        "blue_eco": 2.25,
        "blue_zero": 0.0,
        "green_regular": 3.5,
        "green_eco": 2.75,
        "green_zero": 0.5
    },
    2025: {
        "blue_regular": 3.00,
        "blue_eco": 2.25,
        "blue_zero": 1.15,
        "green_regular": 3.5,
        "green_eco": 2.75,
        "green_zero": 1.4
    }
}

# Create schema for rates with support for both int and float
rate_schema = {
    vol.Required(f"{rate_type}_{year}", default=RATE_TYPES_BY_YEAR[year][rate_type]): vol.Coerce(float)
    for year in YEARS
    for rate_type in RATE_TYPES_BY_YEAR[year]
}

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("json_path", default=DEFAULT_JSON_PATH): str,
    **rate_schema
})

async def validate_input(hass: HomeAssistant, data: dict[str, any]) -> dict[str, any]:
    """Validate the user input allows us to connect."""
    
    if not os.path.exists(data["json_path"]):
        raise InvalidPath

    return {"title": "SMOU Parking", "data": data}

class SMOUConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SMOU Parking."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except InvalidPath:
                errors["base"] = "invalid_path"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

class InvalidPath(HomeAssistantError):
    """Error to indicate the path is invalid."""