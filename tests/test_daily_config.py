from daily_config import Daily_config
import os


class Test_config_class:
    class Test_init:
        def test_load_config_from_env_file(self, mocker):
            mocked_load_dotenv = mocker.patch("daily_config.load_dotenv")
            os.environ["ACTIONS_FILE"] = "1"
            os.environ["CARDS_FILE"] = "2"
            os.environ["API_KEY"] = "3"
            os.environ["TOKEN"] = "4"
            os.environ["BOARD_NAME"] = "5"
            os.environ["DONE_LIST_NAME"] = "6"
            os.environ["ARCHIVAL_BOARD_NAME"] = "7"
            config = Daily_config()
            mocked_load_dotenv.assert_called_once()
            assert config.actions_file == "1"
            assert config.cards_file == "2"
            assert config.api_key == "3"
            assert config.token == "4"
            assert config.board_name == "5"
            assert config.done_list_name == "6"
            assert config.archival_board_name == "7"