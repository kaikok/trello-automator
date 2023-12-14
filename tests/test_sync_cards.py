import os
import json
from sync_cards import \
    perform_sync_cards, \
    load_card_sync_lookup, \
    update_sync_cards, \
    find_new_cards, \
    create_placeholder_card, \
    add_lookup, \
    save_card_sync_lookup


class Test_perform_sync_cards:
    def test_method_exist(self, mocker):
        # mocked_daily_config = mocker.Mock()
        # context = {}
        # perform_sync_cards(context, mocked_daily_config)
        pass


class Test_load_card_sync_lookup:
    def test_empty_file(self, mocker):
        mocked_daily_config = mocker.Mock()
        mocked_daily_config.root = {
            "tasks": {
                "card_sync": {
                    "persistence": {
                        "json_file":
                        os.getcwd() + "/tests/empty_card_sync.json"}}}}
        assert load_card_sync_lookup(mocked_daily_config) == {
            "source": {},
            "placeholder": {}
        }

    def test_file_not_found(self, mocker):
        mocked_daily_config = mocker.Mock()
        mocked_daily_config.root = {
            "tasks": {
                "card_sync": {
                    "persistence": {
                        "json_file":
                        os.getcwd() + "/tests/not_found_card_lookup.json"}}}}
        assert load_card_sync_lookup(mocked_daily_config) == {
            "source": {},
            "placeholder": {}
        }

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
        fs.create_file(os.getcwd() + "/tests/card_sync.json",
                       contents=card_sync_lookup_string)

        mocked_daily_config = mocker.Mock()
        mocked_daily_config.root = {
            "tasks": {
                "card_sync": {
                    "persistence": {
                        "json_file":
                        os.getcwd() + "/tests/card_sync.json"}}}}

        assert load_card_sync_lookup(mocked_daily_config) == card_sync_lookup


class Test_update_sync_cards:
    def test_find_single_source_board_with_no_cards(self, mocker):
        source_boards = json.loads(json.dumps([{
            "name": "board_a",
            "list_names": {
                "todo": "todo_list_name",
                "in_progress": "in_progress_list_name",
                "done": "done_list_name",
            }
        }], indent="  "))

        destination_board = json.loads(json.dumps({
            "name": "board_c",
            "list_names": {
                "todo": "todo_list_name",
                "in_progress": "in_progress_list_name",
                "done": "done_list_name",
            }}, indent="  "))

        mocked_daily_config = mocker.Mock()
        mocked_daily_config.root = {
            "tasks": {
                "card_sync": {
                    "source_boards": source_boards,
                    "destination_board": destination_board
                }
            }}

        context = {
            "card_sync_lookup": {
                "source": {},
                "placeholder": {}
            },
            "board_lookup": {
                "board_a": None,
                "board_c": None
            }
        }

        source_list_on_trello = mocker.Mock()
        source_list_on_trello.list_cards.return_value = []

        destination_list_on_trello = mocker.Mock()
        destination_list_on_trello.list_cards.return_value = []

        mocked_find_list = mocker.patch(
            "sync_cards.find_list")
        mocked_find_list.side_effect = [
            source_list_on_trello, destination_list_on_trello]
        mocked_find_new_cards = mocker.patch(
            "sync_cards.find_new_cards",
            return_value=[]
        )

        assert update_sync_cards(
            context, mocked_daily_config) == context["card_sync_lookup"]
        mocked_find_list.assert_has_calls([
            mocker.call(
                context["board_lookup"],
                source_boards[0]["name"],
                mocked_daily_config.root["tasks"]["card_sync"]["source_boards"][0]["list_names"]["todo"]),
            mocker.call(
                context["board_lookup"],
                destination_board["name"],
                mocked_daily_config.root["tasks"]["card_sync"]["destination_board"]["list_names"]["todo"])
        ])
        mocked_find_new_cards.assert_called_once_with(
            context["card_sync_lookup"],
            source_list_on_trello.list_cards())

    def test_find_single_source_board_with_two_cards(self, mocker):
        source_boards = json.loads(json.dumps([{
            "name": "board_a",
            "list_names": {
                "todo": "todo_list_name",
                "in_progress": "in_progress_list_name",
                "done": "done_list_name",
            }
        }], indent="  "))

        destination_board = json.loads(json.dumps({
            "name": "board_c",
            "list_names": {
                "todo": "todo_list_name",
                "in_progress": "in_progress_list_name",
                "done": "done_list_name",
            }}, indent="  "))

        mocked_daily_config = mocker.Mock()
        mocked_daily_config.root = {
            "tasks": {
                "card_sync": {
                    "source_boards": source_boards,
                    "destination_board": destination_board
                }
            }}

        context = {
            "card_sync_lookup": {
                "source": {},
                "placeholder": {}
            },
            "board_lookup": {
                "board_a": None,
                "board_c": None
            }
        }

        mocked_card_a = mocker.Mock()
        mocked_card_a.id = "123"
        mocked_card_b = mocker.Mock()
        mocked_card_b.id = "456"

        mocked_placeholder_card_a = mocker.Mock()
        mocked_placeholder_card_a.id = "p123"
        mocked_placeholder_card_b = mocker.Mock()
        mocked_placeholder_card_b.id = "p456"

        destination_list_on_trello = mocker.Mock()
        destination_list_on_trello.list_cards.return_value = []

        source_list_on_trello = mocker.Mock()
        source_list_on_trello.list_cards.return_value = [
            mocked_card_a, mocked_card_b]

        mocked_find_list = mocker.patch(
            "sync_cards.find_list")
        mocked_find_list.side_effect = [
            source_list_on_trello, destination_list_on_trello]
        mocked_find_new_cards = mocker.patch(
            "sync_cards.find_new_cards",
            return_value=[mocked_card_a, mocked_card_b]
        )

        mocked_create_placeholder_card = mocker.patch(
            "sync_cards.create_placeholder_card")
        mocked_create_placeholder_card.side_effect = [
            mocked_placeholder_card_a, mocked_placeholder_card_b]

        context["card_sync_lookup"] = update_sync_cards(
            context, mocked_daily_config)

        assert context["card_sync_lookup"]["source"][mocked_card_a.id]["placeholder"] == mocked_placeholder_card_a.id
        assert context["card_sync_lookup"]["source"][mocked_card_b.id]["placeholder"] == mocked_placeholder_card_b.id
        assert context["card_sync_lookup"]["placeholder"][mocked_placeholder_card_a.id]["source"] == mocked_card_a.id
        assert context["card_sync_lookup"]["placeholder"][mocked_placeholder_card_b.id]["source"] == mocked_card_b.id

        mocked_find_list.assert_has_calls([
            mocker.call(
                context["board_lookup"],
                source_boards[0]["name"],
                mocked_daily_config.root["tasks"]["card_sync"]["source_boards"][0]["list_names"]["todo"]),
            mocker.call(
                context["board_lookup"],
                destination_board["name"],
                mocked_daily_config.root["tasks"]["card_sync"]["destination_board"]["list_names"]["todo"])
        ])
        mocked_find_new_cards.assert_called_once_with(
            context["card_sync_lookup"],
            source_list_on_trello.list_cards())
        mocked_create_placeholder_card.assert_has_calls([
            mocker.call(mocked_card_a, destination_list_on_trello),
            mocker.call(mocked_card_b, destination_list_on_trello)])

    def test_find_two_source_board_with_one_card_each(self, mocker):
        source_boards = json.loads(json.dumps([
            {
                "name": "board_a",
                "list_names": {
                    "todo": "todo_list_name",
                    "in_progress": "in_progress_list_name",
                    "done": "done_list_name",
                },
            },
            {
                "name": "board_b",
                "list_names": {
                    "todo": "todo_list_name_b",
                    "in_progress": "in_progress_list_name_b",
                    "done": "done_list_name_b",
                }
            }], indent="  "))

        destination_board = json.loads(json.dumps({
            "name": "board_c",
            "list_names": {
                "todo": "todo_list_name",
                "in_progress": "in_progress_list_name",
                "done": "done_list_name",
            }}, indent="  "))

        mocked_daily_config = mocker.Mock()
        mocked_daily_config.root = {
            "tasks": {
                "card_sync": {
                    "source_boards": source_boards,
                    "destination_board": destination_board
                }
            }}

        context = {
            "card_sync_lookup": {
                "source": {},
                "placeholder": {}
            },
            "board_lookup": {
                "board_a": None,
                "board_b": None,
                "board_c": None
            }
        }

        mocked_card_a = mocker.Mock()
        mocked_card_a.id = "123"
        mocked_card_b = mocker.Mock()
        mocked_card_b.id = "456"

        mocked_placeholder_card_a = mocker.Mock()
        mocked_placeholder_card_a.id = "p123"
        mocked_placeholder_card_b = mocker.Mock()
        mocked_placeholder_card_b.id = "p456"

        destination_list_on_trello = mocker.Mock()
        destination_list_on_trello.list_cards.return_value = []

        source_list_a_on_trello = mocker.Mock()
        source_list_a_on_trello.list_cards.side_effect = [
            [mocked_card_a]
        ]

        source_list_b_on_trello = mocker.Mock()
        source_list_b_on_trello.list_cards.side_effect = [
            [mocked_card_b]
        ]

        mocked_find_list = mocker.patch(
            "sync_cards.find_list")
        mocked_find_list.side_effect = [
            source_list_a_on_trello, source_list_b_on_trello, destination_list_on_trello]
        mocked_find_new_cards = mocker.patch(
            "sync_cards.find_new_cards",
            return_value=[mocked_card_a, mocked_card_b]
        )

        mocked_create_placeholder_card = mocker.patch(
            "sync_cards.create_placeholder_card")
        mocked_create_placeholder_card.side_effect = [
            mocked_placeholder_card_a, mocked_placeholder_card_b]

        context["card_sync_lookup"] = update_sync_cards(
            context, mocked_daily_config)

        assert context["card_sync_lookup"]["source"][mocked_card_a.id]["placeholder"] == mocked_placeholder_card_a.id
        assert context["card_sync_lookup"]["source"][mocked_card_b.id]["placeholder"] == mocked_placeholder_card_b.id
        assert context["card_sync_lookup"]["placeholder"][mocked_placeholder_card_a.id]["source"] == mocked_card_a.id
        assert context["card_sync_lookup"]["placeholder"][mocked_placeholder_card_b.id]["source"] == mocked_card_b.id

        mocked_find_list.assert_has_calls([
            mocker.call(
                context["board_lookup"],
                source_boards[0]["name"],
                source_boards[0]["list_names"]["todo"]),
            mocker.call(
                context["board_lookup"],
                source_boards[1]["name"],
                source_boards[1]["list_names"]["todo"]),
            mocker.call(
                context["board_lookup"],
                destination_board["name"],
                mocked_daily_config.root["tasks"]["card_sync"]["destination_board"]["list_names"]["todo"])
        ])
        mocked_find_new_cards.assert_called_once_with(
            context["card_sync_lookup"],
            [mocked_card_a, mocked_card_b])
        mocked_create_placeholder_card.assert_has_calls([
            mocker.call(mocked_card_a, destination_list_on_trello),
            mocker.call(mocked_card_b, destination_list_on_trello)])


class Test_find_new_cards:
    def test_no_cards_on_list(self, mocker):
        list_of_cards = []
        card_sync_lookup = {
            "source": {},
            "placeholder": {}
        }
        assert find_new_cards(card_sync_lookup, list_of_cards) == []

    def test_one_new_card_on_list(self, mocker):
        card = mocker.Mock()
        card.id = "cardOneID123"
        list_of_cards = [card]
        card_sync_lookup = {
            "source": {},
            "placeholder": {}
        }
        assert find_new_cards(card_sync_lookup, list_of_cards) == [card]

    def test_one_existing_card_on_list(self, mocker):
        card = mocker.Mock()
        card.id = "cardOneID123"
        list_of_cards = [card]
        card_sync_lookup = {
            "source": {
                "cardOneID123": {
                    "placeholder": "cardOnePlaceholderID123"
                }
            },
            "placeholder": {
                "cardOnePlaceholderID123": {
                    "source": "cardOneID123"
                }
            }
        }
        assert find_new_cards(card_sync_lookup, list_of_cards) == []


class Test_create_placeholder_card:
    def test_creates_new_card_at_destination_list(self, mocker):
        source_card = mocker.Mock()
        source_card.id = "cardOneID123"
        source_card.name = "new task on source list"

        new_card = mocker.Mock()
        new_card.id = "cardOnePlaceholderID123"

        destination_list = mocker.Mock()
        destination_list.add_card.return_value = new_card

        assert create_placeholder_card(
            source_card, destination_list) == new_card
        destination_list.add_card.assert_called_once_with(
            name=source_card.name,
            desc=f"SYNC-FROM({source_card.id})\n---\n")


class Test_add_lookup:
    def test_add_placeholder_card(self, mocker):
        source_card = mocker.Mock()
        source_card.id = "cardOneID123"

        placeholder_card = mocker.Mock()
        placeholder_card.id = "cardOnePlaceholderID123"

        card_sync_lookup = {
            "source": {},
            "placeholder": {}
        }

        updated_card_sync_lookup = {
            "source": {
                "cardOneID123": {
                    "placeholder": "cardOnePlaceholderID123"
                }
            },
            "placeholder": {
                "cardOnePlaceholderID123": {
                    "source": "cardOneID123"
                }
            }
        }
        assert add_lookup(card_sync_lookup, source_card,
                          placeholder_card) == updated_card_sync_lookup


class Test_save_card_sync_lookup:
    def test_save_card(self, mocker):
        mocked_daily_config = mocker.Mock()
        mocked_daily_config.root = {
            "tasks": {
                "card_sync": {
                    "persistence": {
                        "json_file": "cards.json"
                    }
                }
            }}
        mocked_open = mocker.patch("sync_cards.open", return_value="Mock FP")
        mocked_json_dump = mocker.patch(
            "daily_run.json.dump", return_value=None)
        save_card_sync_lookup({}, mocked_daily_config)
        mocked_open.assert_called_once_with(
            "cards.json", "w")
        mocked_json_dump.assert_called_once_with(
            {},
            "Mock FP",
            indent="  ")


class Test_sync_all_cards:
    pass
