import os
import json
from dotenv import load_dotenv


class Daily_config:
    def __init__(self):
        load_dotenv()
        self.actions_file = os.environ["ACTIONS_FILE"]
        self.cards_file = os.environ["CARDS_FILE"]
        self.api_key = os.environ["API_KEY"]
        self.token = os.environ["TOKEN"]
        self.board_name = os.environ["BOARD_NAME"]
        self.done_list_name = os.environ["DONE_LIST_NAME"]
        self.archival_board_name = os.environ["ARCHIVAL_BOARD_NAME"]
        self.automation_username = os.environ["AUTOMATION_USERNAME"]
        if (os.environ.get("CONFIG_FILE") and os.environ["CONFIG_FILE"] != ""):
            self.root = json.load(open(os.environ["CONFIG_FILE"]))
        else:
            self.root = None
