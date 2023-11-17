import os
import json
from sync_cards import perform_sync_cards, load_card_sync_lookup, find_sync_new_cards


class Test_perform_sync_cards:
    def test_method_exist(self, mocker):
        mocked_daily_config = mocker.Mock()
        context = {}
        perform_sync_cards(context, mocked_daily_config)

class Test_load_card_sync_lookup:
    def test_empty_file(self, mocker):
        mocked_daily_config = mocker.Mock()
        mocked_daily_config.root.tasks.card_sync.persistence.json_file = \
            os.getcwd() + "/tests/empty_lookup.json"
        assert load_card_sync_lookup(mocked_daily_config) == {}

    def test_file_not_found(self, mocker):
        mocked_daily_config = mocker.Mock()
        mocked_daily_config.root.tasks.card_sync.persistence.json_file = \
            os.getcwd() + "/tests/not_found_card_lookup.json"
        assert load_card_sync_lookup(mocked_daily_config) == {}

    def test_valid_file(self, fs, mocker):
        card_sync_lookup = {
            "source": {
                "cardOneID123": {
                    "placeholder": "cardOnePlaceholderID123"
                },
                "cardTwoID456": {
                    "placeholder": "cardTwoPlaceholderID456"
                }
            },
            "placeholder": {
                "cardOnePlaceholderID123": {
                    "source": "cardOneID123"
                },
                "cardTwoPlaceholderID456": {
                    "source": "cardTwoID456"
                }
            }
        }
        card_sync_lookup_string = json.dumps(card_sync_lookup, indent="  ")
        fs.create_file(os.getcwd() + "/tests/card_sync.json", contents=card_sync_lookup_string)

        mocked_daily_config = mocker.Mock()
        mocked_daily_config.root.tasks.card_sync.persistence.json_file = \
            os.getcwd() + "/tests/card_sync.json"
        assert load_card_sync_lookup(mocked_daily_config) == card_sync_lookup

class Test_find_sync_new_cards:
    def test_find_single_source_board_with_no_cards(self, mocker):
        mocked_daily_config = mocker.Mock()
        mocked_daily_config.root.tasks.card_sync.source_boards = json.loads(json.dumps([{
                "name" : "board_a",
                "list_names": {
                    "todo" : "todo_list_name",
                    "in_progress" : "in_progress_list_name",
                    "done" : "done_list_name",
                }
            }], indent="  "))
        mocked_daily_config.root.tasks.card_sync.destination_board = json.loads(json.dumps({
            "name" : "board_c",
            "list_names": {
                "todo" : "todo_list_name",
                "in_progress" : "in_progress_list_name",
                "done" : "done_list_name",
            }}, indent="  "))
        context = {
            "card_sync_lookup" : {
                "source": {},
                "placeholder": {}
            },
            "board_lookup" : {
                "board_a" : None,
                "board_c" : None
            }
        }
        source_list = mocker.Mock()
        source_list.list_cards.return_value = []
        mocked_retrieve_list_from_trello = mocker.patch(
            "sync_cards.retrieve_list_from_trello",
            return_value = source_list)
        assert find_sync_new_cards(context, mocked_daily_config) == context["card_sync_lookup"]
        mocked_retrieve_list_from_trello.assert_called_once_with(
            context["board_lookup"],
            mocked_daily_config.root.tasks.card_sync.source_boards[0]["name"],
            mocked_daily_config.root.tasks.card_sync.source_boards[0]["list_names"]["todo"]
        ) 

class Test_sync_all_cards:
    pass
