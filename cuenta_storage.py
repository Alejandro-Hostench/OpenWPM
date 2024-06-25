import logging
import json
import os

from selenium.webdriver import Firefox

from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.socket_interface import ClientSocket


class CuentaStorages(BaseCommand):
    """Esto cuenta los storages que hay en una página"""

    def __init__(self, url) -> None:
        self.logger = logging.getLogger("openwpm")
        self.url = url

    # While this is not strictly necessary, we use the repr of a command for logging
    # So not having a proper repr will make your logs a lot less useful
    def __repr__(self) -> str:
        return "CuentaStorages"

    # Have a look at openwpm.commands.types.BaseCommand.execute to see
    # an explanation of each parameter
    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        filename="./datadir/storage.json"
        local= webdriver.execute_script("return window.localStorage.length")
        session = webdriver.execute_script("return window.sessionStorage.length")

        data = {
            self.url: {
                "localStorage": local,
                "sessionStorage": session
            }
        }

        if os.path.exists(filename):
            with open(filename, 'r') as file:
                try:
                    existing_data = json.load(file)
                except json.JSONDecodeError:
                    existing_data = {}
        else:
            existing_data = {}

        # Update or add the new data
        existing_data.update(data)

        # Write the updated data back to the file
        with open(filename, 'w') as file:
            json.dump(existing_data, file, indent=4)
