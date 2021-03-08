"""Config flow for Smart Car integration."""
import logging
import os
import webbrowser
import smartcar

import voluptuous as vol
from aiohttp.web import Response


from homeassistant import config_entries, core, exceptions
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import callback
from homeassistant.helpers.network import get_url
from homeassistant.util.json import load_json, save_json

from .const import (  # pylint:disable=unused-import
    AUTH_CALLBACK_PATH,
    AUTHORIZATION_BASE_URL,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DOMAIN,
    SCOPE,
    SMART_CAR_AUTH_FILE,
    TEST_MODE,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {CONF_CLIENT_ID: str, CONF_CLIENT_SECRET: str, TEST_MODE: bool}
)


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, hass):
        """Initialize."""
        self.hass = hass

    async def authenticate(self, data) -> bool:
        callback_url = f"{get_url(self.hass, prefer_external=True)}{AUTH_CALLBACK_PATH}"
        _LOGGER.exception(callback_url)
        callback_url = "https://ha.dumpin.in"
        scoper = [
            "read_odometer",
            "required:read_location",
            "read_vehicle_info",
            "read_engine_oil",
            "read_battery",
            "read_charge",
            "read_fuel",
            "control_security",
            "read_tires",
            "read_vin",
        ]
        _LOGGER.exception(callback_url)
        client = smartcar.AuthClient(
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            redirect_uri=callback_url,
            scope=scoper,
            test_mode=bool(data["test_mode"]),
        )
        try:
            auth_url = client.get_auth_url()
            _LOGGER.exception(auth_url)
            hass = self.hass
            hass.http.register_view(SmartCarAuthCallbackView())
            webbrowser.open(auth_url)
            """Test if we can authenticate with the host."""
            return True
        except:
            return False

class SmartCarAuthCallbackView(HomeAssistantView):
    url = AUTH_CALLBACK_PATH
    name = "auth:smart_car:callback"
    requires_auth = False

    @callback
    def get(self, request):
        hass = request.app["hass"]
        data = request.query

        html_response = """<html><head><title>Smart Car authorization</title></head>
                           <body><h1>{}</h1></body></html>"""

        if data.get("code") is None:
            error_msg = "No code returned from Smart Car Auth API"
            _LOGGER.error(error_msg)
            return Response(
                text=html_response.format(error_msg), content_type="text/html"
            )

        token = data.get("code")

        try:
            access = smartcar.AuthClient.exchange_code(token)
            save_json(hass.config.path(SMART_CAR_AUTH_FILE), token)
            response_message = """Smart Car has been successfully authorized!
                              You can close this window now!"""
        except:
            response_message = """Smart Car auth has failed"""

        # hass.async_add_job(setup_platform, *self.setup_args)

        return Response(
            text=html_response.format(response_message), content_type="text/html"
        )

async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    hub = PlaceholderHub(hass)

    if not await hub.authenticate(data):
        raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Smart Car"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Car."""

    VERSION = 1
    # TODO pick one of the available connection classes in homeassistant/config_entries.py
    CONNECTION_CLASS = config_entries.CONN_CLASS_UNKNOWN

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
