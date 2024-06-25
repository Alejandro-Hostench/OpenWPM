import argparse
from pathlib import Path
from typing import Literal

import tranco

from cuenta_storage import CuentaStorages
from openwpm.command_sequence import CommandSequence
from openwpm.commands.browser_commands import GetCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.task_manager import TaskManager

parser = argparse.ArgumentParser()
parser.add_argument("--tranco", action="store_true", default=False)
parser.add_argument("--headless", action="store_true", default=False),

args = parser.parse_args()


sites = [
]
if args.tranco:
    # Load the latest tranco list. See https://tranco-list.eu/
    print("Loading tranco top sites list...")
    t = tranco.Tranco(cache=True, cache_dir=".tranco")
    latest_list = t.list()
    sites = ["http://" + x for x in latest_list.top(1000)]


# Loads the default ManagerParams
# and NUM_BROWSERS copies of the default BrowserParams
NUM_BROWSERS = 4
manager_params = ManagerParams(num_browsers=NUM_BROWSERS)
browser_params = [BrowserParams() for _ in range(NUM_BROWSERS)]

# Update browser configuration (use this for per-browser settings)
for browser_param in browser_params:
    browser_param.http_instrument = True
    browser_param.cookie_instrument = True
    browser_param.js_instrument = True

    browser_param.maximum_profile_size = 100 * (10**20)  # 50 MB = 50 * 2^20 Bytes
    browser_param.bot_mitigation = True

    browser_param.donottrack = True
    browser_param.isdcac_enabled = False

# Update TaskManager configuration (use this for crawl-wide settings)
manager_params.data_directory = Path("./datadir/")
manager_params.log_path = Path("./datadir/openwpm.log")

# memory_watchdog and process_watchdog are useful for large scale cloud crawls.
# Please refer to docs/Configuration.md#platform-configuration-options for more information
# manager_params.memory_watchdog = True
# manager_params.process_watchdog = True


# Commands time out by default after 60 seconds
with TaskManager(
    manager_params,
    browser_params,
    SQLiteStorageProvider(Path("./datadir/crawl-data.sqlite")),
    None,
) as manager:
    # Visits the sites
    for index, site in enumerate(sites):

        def callback(success: bool, val: str = site) -> None:
            print(
                f"CommandSequence for {val} ran {'successfully' if success else 'unsuccessfully'}"
            )

        # Parallelize sites over all number of browsers set above.
        command_sequence = CommandSequence(
            site,
            site_rank=index,
            callback=callback,
        )

        command_sequence.append_command(GetCommand(url=site, sleep=3), timeout=60)
        command_sequence.append_command(CuentaStorages(url=site))

        manager.execute_command_sequence(command_sequence)
