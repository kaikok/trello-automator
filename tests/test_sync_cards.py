import pytest
import os
import json
from sync_cards import \
    perform_sync_cards, \
    load_card_sync_lookup, \
    add_new_sync_cards, \
    find_new_cards, \
    create_placeholder_card, \
    add_lookup, \
    remove_card_sync, \
    save_card_sync_lookup, \
    find_latest_card_movement, \
    get_card_status, \
    sync_one_card, \
    sync_all_cards, \
    update_card_status


class Test_perform_sync_cards:
    def test_method_will_find_and_add_new_sync_cards(self, mocker):
        last_card_sync_lookup = {}
        updated_card_sync_lookup = {}
        mocked_config = mocker.Mock()
        context = {
            "card_sync_lookup": None}

        mocked_load_card_sync_lookup = mocker.patch(
            "sync_cards.load_card_sync_lookup",
            return_value=last_card_sync_lookup)

        mocked_add_new_sync_cards = mocker.patch(
            "sync_cards.add_new_sync_cards",
            return_value=updated_card_sync_lookup)

        mocked_save_card_sync_lookup = mocker.patch(
            "sync_cards.save_card_sync_lookup")

        mocked_sync_all_cards = mocker.patch(
            "sync_cards.sync_all_cards",
            return_value=updated_card_sync_lookup)

        perform_sync_cards(context, mocked_config)

        mocked_load_card_sync_lookup.assert_called_once_with(
            mocked_config)

        mocked_add_new_sync_cards.assert_called_once_with(
            context,
            mocked_config)

        mocked_save_card_sync_lookup.assert_has_calls([
            mocker.call(context["card_sync_lookup"], mocked_config),
            mocker.call(context["card_sync_lookup"], mocked_config)
        ])

        mocked_sync_all_cards.assert_called_once_with(
            context,
            mocked_config)

        assert context["card_sync_lookup"] == updated_card_sync_lookup


class Test_load_card_sync_lookup:
    def test_empty_file(self, mocker):
        mocked_config = mocker.Mock()
        mocked_config.root = {
            "tasks": {
                "card_sync": {
                    "persistence": {
                        "json_file":
                        os.getcwd() + "/tests/empty_card_sync.json"}}}}
        assert load_card_sync_lookup(mocked_config) == {
            "source": {},
            "placeholder": {}
        }

    def test_file_not_found(self, mocker):
        mocked_config = mocker.Mock()
        mocked_config.root = {
            "tasks": {
                "card_sync": {
                    "persistence": {
                        "json_file":
                        os.getcwd() + "/tests/not_found_card_lookup.json"}}}}
        assert load_card_sync_lookup(mocked_config) == {
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

        mocked_config = mocker.Mock()
        mocked_config.root = {
            "tasks": {
                "card_sync": {
                    "persistence": {
                        "json_file":
                        os.getcwd() + "/tests/card_sync.json"}}}}

        assert load_card_sync_lookup(mocked_config) == card_sync_lookup


class Test_add_new_sync_cards:
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

        mocked_config = mocker.Mock()
        mocked_config.root = {
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

        assert add_new_sync_cards(
            context, mocked_config) == context["card_sync_lookup"]
        mocked_find_list.assert_has_calls([
            mocker.call(
                context["board_lookup"],
                source_boards[0]["name"],
                mocked_config.root["tasks"]["card_sync"]["source_boards"][0]["list_names"]["todo"]),
            mocker.call(
                context["board_lookup"],
                destination_board["name"],
                mocked_config.root["tasks"]["card_sync"]["destination_board"]["list_names"]["todo"])
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

        mocked_config = mocker.Mock()
        mocked_config.root = {
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

        context["card_sync_lookup"] = add_new_sync_cards(
            context, mocked_config)

        assert context["card_sync_lookup"]["source"][mocked_card_a.id]["placeholder"] == mocked_placeholder_card_a.id
        assert context["card_sync_lookup"]["source"][mocked_card_b.id]["placeholder"] == mocked_placeholder_card_b.id
        assert context["card_sync_lookup"]["placeholder"][mocked_placeholder_card_a.id]["source"] == mocked_card_a.id
        assert context["card_sync_lookup"]["placeholder"][mocked_placeholder_card_b.id]["source"] == mocked_card_b.id

        mocked_find_list.assert_has_calls([
            mocker.call(
                context["board_lookup"],
                source_boards[0]["name"],
                mocked_config.root["tasks"]["card_sync"]["source_boards"][0]["list_names"]["todo"]),
            mocker.call(
                context["board_lookup"],
                destination_board["name"],
                mocked_config.root["tasks"]["card_sync"]["destination_board"]["list_names"]["todo"])
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

        mocked_config = mocker.Mock()
        mocked_config.root = {
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

        context["card_sync_lookup"] = add_new_sync_cards(
            context, mocked_config)

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
                mocked_config.root["tasks"]["card_sync"]["destination_board"]["list_names"]["todo"])
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
            desc=f"SYNC-FROM({source_card.id})\n[Goto source card]({source_card.shortUrl})\n---\n")


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
        mocked_config = mocker.Mock()
        mocked_config.root = {
            "tasks": {
                "card_sync": {
                    "persistence": {
                        "json_file": "cards.json"
                    }
                }
            }}
        mocked_open = mocker.patch("sync_cards.open", return_value="Mock FP")
        mocked_json_dump = mocker.patch(
            "sync_cards.json.dump", return_value=None)
        save_card_sync_lookup({}, mocked_config)
        mocked_open.assert_called_once_with(
            "cards.json", "w")
        mocked_json_dump.assert_called_once_with(
            {},
            "Mock FP",
            indent="  ")


class Test_sync_all_cards:
    pass


class Test_sync_one_card:
    pass


class Test_find_latest_card_movement:
    def test_return_latest_only_move_from_source(self, mocker):
        action_actual_update = {
            "id": "224b90",
            "data": {
                "card": {
                    "id": "6473a5",
                },
                "board": {
                    "id": "8ebadb",
                    "name": "Source Board 1",
                },
                "boardTarget": {
                    "id": "0c9324"
                },
                "list": {
                    "id": "abb6d6",
                    "name": "source board in progress"
                }
            },
            "type": "moveCardFromBoard",
            "date": "2023-09-21T09:02:41.576Z",
            "memberCreator": {
                "username": "expected user"
            }
        }

        action_older_update = {
            "id": "bcbvcvb",
            "data": {
                "card": {
                    "id": "6473a5",
                },
                "board": {
                    "id": "8ebadb",
                    "name": "Source Board 1",
                },
                "boardTarget": {
                    "id": "0c9324"
                },
                "list": {
                    "id": "abb6d6",
                    "name": "source board in progress"
                }
            },
            "type": "moveCardFromBoard",
            "date": "2023-09-21T08:02:41.576Z",
            "memberCreator": {
                "username": "expected user"
            }
        }

        source_card_actions = [
            action_actual_update,
            action_older_update
        ]

        source_card = mocker.Mock()
        source_card.id.side_effect = "123"
        source_card.fetch_actions.return_value = source_card_actions

        placeholder_card_actions = [
            action_older_update
        ]
        placeholder_card = mocker.Mock()
        placeholder_card.id.side_effect = "456"
        placeholder_card.fetch_actions.return_value = placeholder_card_actions

        mocked_config = mocker.Mock()
        mocked_config.automation_username = "automation"

        assert find_latest_card_movement(
            mocked_config, source_card, placeholder_card) == action_actual_update

    def test_return_latest_only_move_from_placeholder(self, mocker):
        action_older_update = {
            "id": "224b90",
            "data": {
                "card": {
                    "id": "6473a5",
                },
                "board": {
                    "id": "8ebadb",
                    "name": "Source Board 1",
                },
                "boardTarget": {
                    "id": "0c9324"
                },
                "list": {
                    "id": "abb6d6",
                    "name": "source board in progress"
                }
            },
            "type": "moveCardFromBoard",
            "date": "2023-09-21T09:02:41.576Z",
            "memberCreator": {
                "username": "expected user"
            }
        }

        action_newer_update = {
            "id": "bcbvcvb",
            "data": {
                "card": {
                    "id": "6473a5",
                },
                "board": {
                    "id": "8ebadb",
                    "name": "Source Board 1",
                },
                "boardTarget": {
                    "id": "0c9324"
                },
                "list": {
                    "id": "abb6d6",
                    "name": "source board in progress"
                }
            },
            "type": "moveCardFromBoard",
            "date": "2023-09-21T10:02:41.576Z",
            "memberCreator": {
                "username": "expected user"
            }
        }

        source_card_actions = [
            action_older_update
        ]

        source_card = mocker.Mock()
        source_card.id.side_effect = "123"
        source_card.fetch_actions.return_value = source_card_actions

        placeholder_card_actions = [
            action_newer_update,
            action_older_update
        ]

        placeholder_card = mocker.Mock()
        placeholder_card.id.side_effect = "456"
        placeholder_card.fetch_actions.return_value = placeholder_card_actions

        mocked_config = mocker.Mock()
        mocked_config.automation_username = "automation"

        assert find_latest_card_movement(
            mocked_config, source_card, placeholder_card) == action_newer_update

    def test_return_none_if_not_found(self, mocker):
        source_card_actions = []

        source_card = mocker.Mock()
        source_card.id.side_effect = "123"
        source_card.fetch_actions.return_value = source_card_actions

        placeholder_card_actions = []

        placeholder_card = mocker.Mock()
        placeholder_card.id.side_effect = "456"
        placeholder_card.fetch_actions.return_value = placeholder_card_actions

        mocked_config = mocker.Mock()
        mocked_config.automation_username = "automation"

        assert find_latest_card_movement(
            mocked_config, source_card, placeholder_card) == None

    def test_return_none_if_latest_action_is_automation(self, mocker):
        action_belongs_to_automation = {
            "id": "fgdgfgfd",
            "data": {
                "card": {
                    "id": "6473a5",
                },
                "board": {
                    "id": "8ebadb",
                    "name": "Source Board 1",
                },
                "boardTarget": {
                    "id": "0c9324"
                },
                "list": {
                    "id": "abb6d6",
                    "name": "source board in progress"
                }
            },
            "type": "moveCardFromBoard",
            "date": "2023-09-21T08:02:41.576Z",
            "memberCreator": {
                "username": "automation"
            }
        }

        source_card_actions = []

        source_card = mocker.Mock()
        source_card.id.side_effect = "123"
        source_card.fetch_actions.return_value = source_card_actions

        placeholder_card_actions = [action_belongs_to_automation]

        placeholder_card = mocker.Mock()
        placeholder_card.id.side_effect = "456"
        placeholder_card.fetch_actions.return_value = placeholder_card_actions

        mocked_config = mocker.Mock()
        mocked_config.automation_username = "automation"

        assert find_latest_card_movement(
            mocked_config, source_card, placeholder_card) == None


class Test_get_card_status:
    @pytest.fixture
    def source_board(self, mocker):
        source_board = mocker.Mock()
        source_board.id = "123"
        source_board.name = "board_a"
        return source_board

    @pytest.fixture
    def destination_board(self, mocker):
        destination_board = mocker.Mock()
        destination_board.id = "456"
        destination_board.name = "board_c"
        return destination_board

    @pytest.fixture
    def create_card(self, mocker):
        def _create_card(board_id, list_id):
            source_card = mocker.Mock()
            source_card.board_id = board_id
            source_card.list_id = list_id
            return source_card
        return _create_card

    @pytest.fixture
    def mocked_config(self, mocker):
        source_boards_config = [
            {
                "name": "board_a",
                "list_names": {
                    "todo": "board_a_todo_list_name",
                    "in_progress": "board_a_in_progress_list_name",
                    "done": "board_a_done_list_name",
                },
            }]

        destination_board_config = {
            "name": "board_c",
            "list_names": {
                "todo": "board_c_todo_list_name",
                "in_progress": "board_c_in_progress_list_name",
                "done": "board_c_done_list_name",
            }}

        mocked_config = mocker.Mock()
        mocked_config.root = {
            "tasks": {
                "card_sync": {
                    "source_boards": source_boards_config,
                    "destination_board": destination_board_config
                }
            }}
        return mocked_config

    @pytest.fixture
    def create_context(self, mocker):
        def _create_context(source_board, destination_board):
            source_todo_list = mocker.Mock()
            source_todo_list.id = "source_todo_list_id"
            source_todo_list.name = "board_a_todo_list_name"
            source_in_progress_list = mocker.Mock()
            source_in_progress_list.id = "source_in_progress_list_id"
            source_in_progress_list.name = "board_a_in_progress_list_name"
            source_done_list = mocker.Mock()
            source_done_list.id = "source_done_list_id"
            source_done_list.name = "board_a_done_list_name"

            destination_todo_list = mocker.Mock()
            destination_todo_list.id = "destination_todo_list_id"
            destination_todo_list.name = "board_c_todo_list_name"
            destination_in_progress_list = mocker.Mock()
            destination_in_progress_list.id = "destination_in_progress_list_id"
            destination_in_progress_list.name = "board_c_in_progress_list_name"
            destination_done_list = mocker.Mock()
            destination_done_list.id = "destination_done_list_id"
            destination_done_list.name = "board_c_done_list_name"

            unrelated_list = mocker.Mock()
            unrelated_list.id = "unrelated_list_id"
            unrelated_list.name = "board_c_unrelated_list_name"

            context = {
                "board_lookup": {
                    "board_a": source_board,
                    "board_c": destination_board
                },
                "list_lookup": {
                    "board_name": {
                        "board_a": {
                            source_todo_list.name: (source_todo_list, "board_a", source_todo_list.name),
                            source_in_progress_list.name: (source_in_progress_list, "board_a", source_in_progress_list.name),
                            source_done_list.name: (
                                source_done_list, "board_a", source_done_list.name)
                        },
                        "board_c": {
                            destination_todo_list.name: (destination_todo_list, "board_c", destination_todo_list.name),
                            destination_in_progress_list.name: (destination_in_progress_list, "board_c", destination_in_progress_list.name),
                            destination_done_list.name: (
                                destination_done_list, "board_c", destination_done_list.name),
                            unrelated_list.name: (
                                unrelated_list, "board_c", unrelated_list.name)
                        }
                    },
                    "list_id": {
                        source_todo_list.id: (source_todo_list, "board_a", source_todo_list.name),
                        source_in_progress_list.id: (source_in_progress_list, "board_a", source_in_progress_list.name),
                        source_done_list.id: (source_done_list, "board_a", source_done_list.name),
                        destination_todo_list.id: (destination_todo_list, "board_c", destination_todo_list.name),
                        destination_in_progress_list.id: (destination_in_progress_list, "board_c", destination_in_progress_list.name),
                        destination_done_list.id: (destination_done_list, "board_c", destination_done_list.name),
                        unrelated_list.id: (
                            unrelated_list, "board_c", unrelated_list.name)
                    }
                }
            }
            return context
        return _create_context

    def test_given_source_card_determine_todo_status(self, mocker,
                                                     source_board, destination_board,
                                                     create_card, mocked_config, create_context):
        source_card = create_card(source_board.id, "source_todo_list_id")
        mocked_context = create_context(source_board, destination_board)

        assert get_card_status(
            mocked_context, mocked_config, source_card) == "todo"

    def test_given_source_card_determine_done_status(self, mocker,
                                                     source_board, destination_board,
                                                     create_card, mocked_config, create_context):
        source_card = create_card(source_board.id, "source_done_list_id")
        mocked_context = create_context(source_board, destination_board)

        assert get_card_status(
            mocked_context, mocked_config, source_card) == "done"

    def test_given_source_card_determine_in_progress_status(self, mocker,
                                                            source_board, destination_board,
                                                            create_card, mocked_config, create_context):
        source_card = create_card(
            source_board.id, "source_in_progress_list_id")
        mocked_context = create_context(source_board, destination_board)

        assert get_card_status(
            mocked_context, mocked_config, source_card) == "in_progress"

    def test_given_destination_card_determine_todo_status(self, mocker,
                                                          source_board, destination_board,
                                                          create_card, mocked_config, create_context):
        destination_card = create_card(
            destination_board.id, "destination_todo_list_id")
        mocked_context = create_context(source_board, destination_board)

        assert get_card_status(mocked_context, mocked_config,
                               destination_card) == "todo"

    def test_given_destination_card_determine_done_status(self, mocker,
                                                          source_board, destination_board,
                                                          create_card, mocked_config, create_context):
        destination_card = create_card(
            destination_board.id, "destination_done_list_id")
        mocked_context = create_context(source_board, destination_board)

        assert get_card_status(mocked_context, mocked_config,
                               destination_card) == "done"

    def test_given_destination_card_determine_in_progress_status(self, mocker,
                                                                 source_board, destination_board,
                                                                 create_card, mocked_config, create_context):
        destination_card = create_card(
            destination_board.id, "destination_in_progress_list_id")
        mocked_context = create_context(source_board, destination_board)

        assert get_card_status(mocked_context, mocked_config,
                               destination_card) == "in_progress"

    def test_given_destination_card_not_found(self, mocker,
                                              source_board, destination_board,
                                              create_card, mocked_config, create_context):
        destination_card = create_card(destination_board.id, "other_list_id")
        mocked_context = create_context(source_board, destination_board)

        assert get_card_status(mocked_context, mocked_config,
                               destination_card) == "not_found"

    def test_destination_card_belongs_to_unrelated_list_return_not_found(self, mocker,
                                                                         source_board, destination_board,
                                                                         create_card, mocked_config, create_context):
        destination_card = create_card(
            destination_board.id, "unrelated_list_id")
        mocked_context = create_context(source_board, destination_board)

        assert get_card_status(mocked_context, mocked_config,
                               destination_card) == "not_found"


class Test_update_card_status:
    @pytest.fixture
    def source_board(self, mocker):
        source_board = mocker.Mock()
        source_board.id = "123"
        source_board.name = "board_a"
        return source_board

    @pytest.fixture
    def destination_board(self, mocker):
        destination_board = mocker.Mock()
        destination_board.id = "456"
        destination_board.name = "board_c"
        return destination_board

    @pytest.fixture
    def create_card(self, mocker):
        def _create_card(board_id, list_id):
            source_card = mocker.Mock()
            source_card.board_id = board_id
            source_card.list_id = list_id
            return source_card
        return _create_card

    @pytest.fixture
    def mocked_config(self, mocker):
        source_boards_config = [
            {
                "name": "board_a",
                "list_names": {
                    "todo": "board_a_todo_list_name",
                    "in_progress": "board_a_in_progress_list_name",
                    "done": "board_a_done_list_name",
                },
            }]

        destination_board_config = {
            "name": "board_c",
            "list_names": {
                "todo": "board_c_todo_list_name",
                "in_progress": "board_c_in_progress_list_name",
                "done": "board_c_done_list_name",
            }}

        mocked_config = mocker.Mock()
        mocked_config.root = {
            "tasks": {
                "card_sync": {
                    "source_boards": source_boards_config,
                    "destination_board": destination_board_config
                }
            }}
        return mocked_config

    @pytest.fixture
    def create_context(self, mocker):
        def _create_context(source_board, destination_board):
            source_todo_list = mocker.Mock()
            source_todo_list.id = "source_todo_list_id"
            source_todo_list.name = "board_a_todo_list_name"
            source_in_progress_list = mocker.Mock()
            source_in_progress_list.id = "source_in_progress_list_id"
            source_in_progress_list.name = "board_a_in_progress_list_name"
            source_done_list = mocker.Mock()
            source_done_list.id = "source_done_list_id"
            source_done_list.name = "board_a_done_list_name"

            destination_todo_list = mocker.Mock()
            destination_todo_list.id = "destination_todo_list_id"
            destination_todo_list.name = "board_c_todo_list_name"
            destination_in_progress_list = mocker.Mock()
            destination_in_progress_list.id = "destination_in_progress_list_id"
            destination_in_progress_list.name = "board_c_in_progress_list_name"
            destination_done_list = mocker.Mock()
            destination_done_list.id = "destination_done_list_id"
            destination_done_list.name = "board_c_done_list_name"

            context = {
                "board_lookup": {
                    "board_a": source_board,
                    "board_c": destination_board
                },
                "list_lookup": {
                    "board_name": {
                        "board_a": {
                            source_todo_list.name: (source_todo_list, "board_a", source_todo_list.name),
                            source_in_progress_list.name: (source_in_progress_list, "board_a", source_in_progress_list.name),
                            source_done_list.name: (
                                source_done_list, "board_a", source_done_list.name)
                        },
                        "board_c": {
                            destination_todo_list.name: (destination_todo_list, "board_c", destination_todo_list.name),
                            destination_in_progress_list.name: (destination_in_progress_list, "board_c", destination_in_progress_list.name),
                            destination_done_list.name: (
                                destination_done_list, "board_c", destination_done_list.name)
                        }
                    },
                    "list_id": {
                        source_todo_list.id: (source_todo_list, "board_a", source_todo_list.name),
                        source_in_progress_list.id: (source_in_progress_list, "board_a", source_in_progress_list.name),
                        source_done_list.id: (source_done_list, "board_a", source_done_list.name),
                        destination_todo_list.id: (destination_todo_list, "board_c", destination_todo_list.name),
                        destination_in_progress_list.id: (destination_in_progress_list, "board_c", destination_in_progress_list.name),
                        destination_done_list.id: (destination_done_list, "board_c", destination_done_list.name),
                    }
                }
            }
            return context
        return _create_context

    def test_set_destination_card_to_new_status(self, mocker,
                                                source_board, destination_board,
                                                create_card, create_context,
                                                mocked_config):
        destination_card = create_card(
            destination_board.id, "destination_todo_list_id")
        mocked_context = create_context(source_board, destination_board)

        mocked_lookup_board_with_id = mocker.patch(
            "sync_cards.lookup_board_with_id", return_value=destination_board)

        destination_card.change_list.return_value = None

        update_card_status(mocked_context, mocked_config,
                           destination_card, "in_progress")

        mocked_lookup_board_with_id.assert_called_with(
            mocked_context["board_lookup"], destination_card.board_id)

        destination_card.change_list.assert_called_with(
            "destination_in_progress_list_id")

    def test_set_source_card_to_new_status(self, mocker,
                                           source_board, destination_board,
                                           create_card, create_context,
                                           mocked_config):
        source_card = create_card(source_board.id, "source_todo_list_id")
        mocked_context = create_context(source_board, destination_board)

        mocked_lookup_board_with_id = mocker.patch(
            "sync_cards.lookup_board_with_id", return_value=source_board)

        source_card.change_list.return_value = None

        update_card_status(mocked_context, mocked_config,
                           source_card, "in_progress")

        mocked_lookup_board_with_id.assert_called_with(
            mocked_context["board_lookup"], source_card.board_id)

        source_card.change_list.assert_called_with(
            "source_in_progress_list_id")


class Test_remove_card_sync:
    def test_remove_both_source_and_placeholder_entries_from_lookup_given_source_card(self, mocker):
        initial_card_sync_lookup = {
            "source": {
                "source_card_id_123": {
                    "placeholder": "placeholder_card_id_123"
                },
                "source_card_id_456": {
                    "placeholder": "placeholder_card_id_456"
                }
            },
            "placeholder": {
                "placeholder_card_id_123": {
                    "source": "source_card_id_123"
                },
                "placeholder_card_id_456": {
                    "source": "source_card_id_456"
                }
            }
        }

        final_card_sync_lookup = {
            "source": {
                "source_card_id_456": {
                    "placeholder": "placeholder_card_id_456"
                }
            },
            "placeholder": {
                "placeholder_card_id_456": {
                    "source": "source_card_id_456"
                }
            }
        }

        mocked_context = {
            "card_sync_lookup": initial_card_sync_lookup
        }

        source_card = mocker.Mock()
        source_card.id = "source_card_id_123"

        assert remove_card_sync(
            mocked_context, source_card) == final_card_sync_lookup

    def test_remove_both_source_and_placeholder_entries_from_lookup_given_placeholder_card(self, mocker):
        initial_card_sync_lookup = {
            "source": {
                "source_card_id_123": {
                    "placeholder": "placeholder_card_id_123"
                },
                "source_card_id_456": {
                    "placeholder": "placeholder_card_id_456"
                }
            },
            "placeholder": {
                "placeholder_card_id_123": {
                    "source": "source_card_id_123"
                },
                "placeholder_card_id_456": {
                    "source": "source_card_id_456"
                }
            }
        }

        final_card_sync_lookup = {
            "source": {
                "source_card_id_123": {
                    "placeholder": "placeholder_card_id_123"
                }
            },
            "placeholder": {
                "placeholder_card_id_123": {
                    "source": "source_card_id_123"
                }
            }
        }

        mocked_context = {
            "card_sync_lookup": initial_card_sync_lookup
        }

        placeholder_card = mocker.Mock()
        placeholder_card.id = "placeholder_card_id_456"

        assert remove_card_sync(
            mocked_context, placeholder_card) == final_card_sync_lookup


class Test_sync_one_card:
    @pytest.fixture
    def source_board(self, mocker):
        source_board = mocker.Mock()
        source_board.id = "123"
        source_board.name = "board_a"
        return source_board

    @pytest.fixture
    def destination_board(self, mocker):
        destination_board = mocker.Mock()
        destination_board.id = "456"
        destination_board.name = "board_c"
        return destination_board

    @pytest.fixture
    def create_card(self, mocker):
        def _create_card(board_id, list_id):
            source_card = mocker.Mock()
            source_card.board_id = board_id
            source_card.list_id = list_id
            return source_card
        return _create_card

    def test_returns_none_if_status_is_same(self, mocker,
                                            source_board, destination_board,
                                            create_card):
        source_card = create_card(source_board.id, "source_todo_list_id")
        placeholder_card = create_card(
            destination_board.id, "destination_todo_list_id")

        latest_card_movement = {
            "id": "123",
            "data": {
                "card": {
                    "name": source_card.name,
                    "id": source_card.id
                },
                "board": {
                    "name": ""
                },
                "listBefore": {
                    "name": ""
                },
                "listAfter": {
                    "name": ""
                }
            }
        }

        mocked_handle = mocker.Mock()
        mocked_handle.get_card.side_effect = [
            source_card, placeholder_card
        ]

        mocked_get_card_status = mocker.patch(
            "sync_cards.get_card_status", side_effect=["todo", "todo"]
        )

        mocked_find_latest_card_movement = mocker.patch(
            "sync_cards.find_latest_card_movement", return_value=latest_card_movement
        )

        mocked_context = {
            "handle": mocked_handle
        }

        mocked_config = mocker.Mock()

        assert sync_one_card(mocked_context, mocked_config,
                             source_card.id, placeholder_card.id) == None

        mocked_handle.get_card.assert_has_calls([
            mocker.call(source_card.id),
            mocker.call(placeholder_card.id)
        ])

        mocked_get_card_status.assert_has_calls([
            mocker.call(mocked_context, mocked_config, source_card),
            mocker.call(mocked_context, mocked_config, placeholder_card)
        ])

        mocked_find_latest_card_movement.assert_called_with(
            mocked_config, source_card, placeholder_card
        )

    def test_returns_job_when_status_is_different_and_last_move_was_source(self, mocker,
                                                                           source_board, destination_board,
                                                                           create_card):
        source_card = create_card(source_board.id, "source_todo_list_id")
        placeholder_card = create_card(
            destination_board.id, "destination_todo_list_id")

        latest_card_movement = {
            "id": "123",
            "data": {
                "card": {
                    "name": source_card.name,
                    "id": source_card.id
                },
                "board": {
                    "name": ""
                },
                "listBefore": {
                    "name": ""
                },
                "listAfter": {
                    "name": ""
                }
            }
        }

        mocked_handle = mocker.Mock()
        mocked_handle.get_card.side_effect = [
            source_card, placeholder_card
        ]

        mocked_get_card_status = mocker.patch(
            "sync_cards.get_card_status", side_effect=["todo", "in_progress"]
        )

        mocked_find_latest_card_movement = mocker.patch(
            "sync_cards.find_latest_card_movement", return_value=latest_card_movement
        )

        mocked_context = {
            "handle": mocked_handle
        }

        mocked_config = mocker.Mock()

        assert sync_one_card(mocked_context, mocked_config, source_card.id,
                             placeholder_card.id) == (placeholder_card, "todo")

        mocked_handle.get_card.assert_has_calls([
            mocker.call(source_card.id),
            mocker.call(placeholder_card.id)
        ])

        mocked_get_card_status.assert_has_calls([
            mocker.call(mocked_context, mocked_config, source_card),
            mocker.call(mocked_context, mocked_config, placeholder_card)
        ])

        mocked_find_latest_card_movement.assert_called_with(
            mocked_config, source_card, placeholder_card
        )

    def test_returns_job_when_status_is_different_and_last_move_was_placeholder(self, mocker,
                                                                                source_board, destination_board,
                                                                                create_card):
        source_card = create_card(source_board.id, "source_todo_list_id")
        placeholder_card = create_card(
            destination_board.id, "destination_todo_list_id")

        latest_card_movement = {
            "id": "123",
            "data": {
                "card": {
                    "name": placeholder_card.name,
                    "id": placeholder_card.id
                },
                "board": {
                    "name": ""
                },
                "listBefore": {
                    "name": ""
                },
                "listAfter": {
                    "name": ""
                }
            }
        }

        mocked_handle = mocker.Mock()
        mocked_handle.get_card.side_effect = [
            source_card, placeholder_card
        ]

        mocked_get_card_status = mocker.patch(
            "sync_cards.get_card_status", side_effect=["todo", "in_progress"]
        )

        mocked_find_latest_card_movement = mocker.patch(
            "sync_cards.find_latest_card_movement", return_value=latest_card_movement
        )

        mocked_context = {
            "handle": mocked_handle
        }

        mocked_config = mocker.Mock()

        assert sync_one_card(mocked_context, mocked_config, source_card.id,
                             placeholder_card.id) == (source_card, "in_progress")

        mocked_handle.get_card.assert_has_calls([
            mocker.call(source_card.id),
            mocker.call(placeholder_card.id)
        ])

        mocked_get_card_status.assert_has_calls([
            mocker.call(mocked_context, mocked_config, source_card),
            mocker.call(mocked_context, mocked_config, placeholder_card)
        ])

        mocked_find_latest_card_movement.assert_called_with(
            mocked_config, source_card, placeholder_card
        )

    def test_throw_exception_if_movement_not_found(self, mocker,
                                                   source_board, destination_board,
                                                   create_card):
        source_card = create_card(source_board.id, "source_todo_list_id")
        placeholder_card = create_card(
            destination_board.id, "destination_todo_list_id")

        latest_card_movement = None

        mocked_handle = mocker.Mock()
        mocked_handle.get_card.side_effect = [
            source_card, placeholder_card
        ]

        mocked_get_card_status = mocker.patch(
            "sync_cards.get_card_status", side_effect=["todo", "in_progress"]
        )

        mocked_find_latest_card_movement = mocker.patch(
            "sync_cards.find_latest_card_movement", return_value=latest_card_movement
        )

        mocked_context = {
            "handle": mocked_handle
        }

        mocked_config = mocker.Mock()

        with pytest.raises(Exception) as excinfo:
            sync_one_card(mocked_context, mocked_config,
                          source_card.id, placeholder_card.id)

        assert str(excinfo.value) == "Movement action not found!"

        mocked_handle.get_card.assert_has_calls([
            mocker.call(source_card.id),
            mocker.call(placeholder_card.id)
        ])

        mocked_get_card_status.assert_has_calls([
            mocker.call(mocked_context, mocked_config, source_card),
            mocker.call(mocked_context, mocked_config, placeholder_card)
        ])

        mocked_find_latest_card_movement.assert_called_with(
            mocked_config, source_card, placeholder_card
        )


class Test_sync_all_cards:
    def test_processing_jobs(self, mocker):
        card_sync_lookup = {
            "source": {
                "source_card_id_123": {
                    "placeholder": "placeholder_card_id_123"
                },
                "source_card_id_456": {
                    "placeholder": "placeholder_card_id_456"
                },
                "source_card_id_789": {
                    "placeholder": "placeholder_card_id_789"
                }
            },
            "placeholder": {
                "placeholder_card_id_123": {
                    "source": "source_card_id_123"
                },
                "placeholder_card_id_456": {
                    "source": "source_card_id_456"
                },
                "placeholder_card_id_789": {
                    "source": "source_card_id_789"
                }
            }
        }

        mocked_context = {
            "card_sync_lookup": card_sync_lookup
        }

        mocked_config = mocker.Mock()

        card1 = mocker.Mock()
        card1.name = "card1"

        card2 = mocker.Mock()
        card2.name = "card2"

        card3 = mocker.Mock()
        card3.name = "card2"

        mocked_sync_one_card = mocker.patch(
            "sync_cards.sync_one_card", side_effect=[(card1, "todo"), (card2, "in_progress"), (card3, "not_found")]
        )

        mocked_update_card_status = mocker.patch(
            "sync_cards.update_card_status")

        mocked_remove_card_sync = mocker.patch(
            "sync_cards.remove_card_sync", return_value=card_sync_lookup)

        assert sync_all_cards(
            mocked_context, mocked_config) == card_sync_lookup

        mocked_sync_one_card.assert_has_calls([
            mocker.call(mocked_context, mocked_config,
                        "source_card_id_123", "placeholder_card_id_123"),
            mocker.call(mocked_context, mocked_config,
                        "source_card_id_456", "placeholder_card_id_456")
        ])

        mocked_update_card_status.assert_has_calls([
            mocker.call(mocked_context, mocked_config, card1, "todo"),
            mocker.call(mocked_context, mocked_config, card2, "in_progress")
        ])

        mocked_remove_card_sync.assert_called_with(mocked_context, card3)
