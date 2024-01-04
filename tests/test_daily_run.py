import os
import trello
import daily_run


class Test_load_action_list:
    def test_empty_file(self, mocker):
        mocked_config = mocker.Mock()
        mocked_config.actions_file = \
            os.getcwd() + "/tests/empty_action_list.json"
        assert daily_run.load_action_list(mocked_config) == []

    def test_file_not_found(self, mocker):
        mocked_config = mocker.Mock()
        mocked_config.actions_file = \
            os.getcwd() + "/tests/not_found_action_list.json"
        assert daily_run.load_action_list(mocked_config) == []


class Test_load_card_lookup:
    def test_empty_file(self, mocker):
        mocked_config = mocker.Mock()
        mocked_config.cards_file = \
            os.getcwd() + "/tests/empty_card_lookup.json"
        assert daily_run.load_card_lookup(mocked_config) == {}

    def test_file_not_found(self, mocker):
        mocked_config = mocker.Mock()
        mocked_config.cards_file = \
            os.getcwd() + "/tests/not_found_card_lookup.json"
        assert daily_run.load_card_lookup(mocked_config) == {}

    def test_valid_file(self, mocker):
        mocked_config = mocker.Mock()
        mocked_config.cards_file = \
            os.getcwd() + "/tests/card_lookup.json"
        assert daily_run.load_card_lookup(mocked_config) == {
            "64e7072e2edd663977c39c6a": {
                "id": "64e7072e2edd663977c39c6a"
            },
            "64e6f38820e6a471e594cf0a": {
                "id": "64e6f38820e6a471e594cf0a"
            },
            "64e6f388977142a9d7c4afb9": {
                "id": "64e6f388977142a9d7c4afb9"
            }}


class Test_init_trello_conn:
    def test_should_return_a_trello_client(self, mocker):
        mocked_config = mocker.Mock()
        handle = daily_run.init_trello_conn(mocked_config)
        assert isinstance(handle, trello.trelloclient.TrelloClient)

    def test_should_retrieve_credentials_from_config_object(self, mocker):
        mocked_config = mocker.Mock()
        mocker.patch("daily_run.TrelloClient.__init__", return_value=None)
        mocked_config.api_key = "ABC"
        mocked_config.token = "DEF"
        handle = daily_run.init_trello_conn(mocked_config)
        handle.__init__.assert_called_once_with(
            api_key="ABC",
            token="DEF")


class Test_setup_board_lookup:
    def test_setup_board_lookup(self, mocker):
        handle = mocker.Mock()
        board_one = mocker.Mock()
        board_two = mocker.Mock()
        board_one.name = "board-one-name"
        board_two.name = "board-two-name"

        handle.list_boards.return_value = [board_one, board_two]
        assert daily_run.setup_board_lookup(handle) == {
            "board-one-name": board_one,
            "board-two-name": board_two}


class Test_setup_list_lookup:
    def test_returns_name_and_id_lookup(self, mocker):
        board_a_list1 = mocker.Mock()
        board_a_list1.id = "a123_id"
        board_a_list1.name = "a123_name"
        board_a_list2 = mocker.Mock()
        board_a_list2.id = "a456_id"
        board_a_list2.name = "a456_name"
        board_a_lists = [board_a_list1, board_a_list2]
        board_a = mocker.Mock()
        board_a.get_lists.return_value = board_a_lists
        board_a.name = "board_a_name"

        board_b_list1 = mocker.Mock()
        board_b_list1.id = "b123_id"
        board_b_list1.name = "b123_name"
        board_b_list2 = mocker.Mock()
        board_b_list2.id = "b456_id"
        board_b_list2.name = "b456_name"
        board_b_lists = [board_b_list1, board_b_list2]
        board_b = mocker.Mock()
        board_b.get_lists.return_value = board_b_lists
        board_b.name = "board_b_name"

        board_lookup = {
            "board_a_name": board_a,
            "board_b_name": board_b
        }

        expected_list_lookup = {
            "board_name": {
                "board_a_name": {
                    "a123_name": (board_a_list1, board_a.name, board_a_list1.name),
                    "a456_name": (board_a_list2, board_a.name, board_a_list2.name)
                },
                "board_b_name": {
                    "b123_name": (board_b_list1, board_b.name, board_b_list1.name),
                    "b456_name": (board_b_list2, board_b.name, board_b_list2.name)
                }
            },
            "list_id": {
                "a123_id": (board_a_list1, board_a.name, board_a_list1.name),
                "a456_id": (board_a_list2, board_a.name, board_a_list2.name),
                "b123_id": (board_b_list1, board_b.name, board_b_list1.name),
                "b456_id": (board_b_list2, board_b.name, board_b_list2.name)
            }
        }

        assert daily_run.setup_list_lookup(
            board_lookup) == expected_list_lookup


class Test_retrieve_all_actions_from_trello:
    def test_less_than_1000_actions(self, mocker):
        action_list = [
            "addAttachmentToCard",
            "addChecklistToCard",
            "addMemberToCard",
            "commentCard",
            "convertToCardFromCheckItem",
            "copyCard",
            "createCard",
            "deleteCard",
            "emailCard",
            "moveCardFromBoard",
            "moveCardToBoard",
            "removeChecklistFromCard",
            "removeMemberFromCard",
            "updateCard",
            "updateCheckItemStateOnCard",
        ]
        action_list_str = ','.join(action_list)

        board_one = mocker.Mock()

        results = [{"id": "action-one-id"}, {"id": "action-two-id"}]
        board_one.fetch_actions.return_value = results

        board_name = "board-one-name"
        board_lookup = {"board-one-name": board_one}

        actions = daily_run.retrieve_all_actions_from_trello(
            board_lookup, board_name)

        board_one.fetch_actions.assert_called_once_with(
            {"fields", "all", "filter", action_list_str},
            action_limit=1000)
        assert actions == results

    def test_more_than_1000_actions(self, mocker):
        action_list = [
            "addAttachmentToCard",
            "addChecklistToCard",
            "addMemberToCard",
            "commentCard",
            "convertToCardFromCheckItem",
            "copyCard",
            "createCard",
            "deleteCard",
            "emailCard",
            "moveCardFromBoard",
            "moveCardToBoard",
            "removeChecklistFromCard",
            "removeMemberFromCard",
            "updateCard",
            "updateCheckItemStateOnCard",
        ]
        action_list_str = ','.join(action_list)

        board_one = mocker.Mock()

        results_one = \
            [{"id": "action-one-id"}, {"id": "action-two-id"}] * 499 + \
            [{"id": "action-nine-nine-nine-id"}, {"id": "action-thousand-id"}]
        results_two = [{"id": "action-thousand-one-id"}]
        board_one.fetch_actions.side_effect = [results_one, results_two]

        board_name = "board-one-name"
        board_lookup = {"board-one-name": board_one}

        actions = daily_run.retrieve_all_actions_from_trello(
            board_lookup, board_name)

        board_one.fetch_actions.assert_has_calls([
            mocker.call({"fields", "all", "filter", action_list_str},
                        action_limit=1000),
            mocker.call({"fields", "all", "filter", action_list_str},
                        action_limit=1000, before='action-thousand-id')])
        assert actions == results_one + results_two

    def test_retrieve_latest_actions_from_trello(self, mocker):
        action_list = [
            "addAttachmentToCard",
            "addChecklistToCard",
            "addMemberToCard",
            "commentCard",
            "convertToCardFromCheckItem",
            "copyCard",
            "createCard",
            "deleteCard",
            "emailCard",
            "moveCardFromBoard",
            "moveCardToBoard",
            "removeChecklistFromCard",
            "removeMemberFromCard",
            "updateCard",
            "updateCheckItemStateOnCard",
        ]
        action_list_str = ','.join(action_list)

        board_one = mocker.Mock()

        results = [{"id": "action-one-id"}, {"id": "action-two-id"}]
        board_one.fetch_actions.return_value = results

        board_name = "board-one-name"
        board_lookup = {"board-one-name": board_one}

        actions = daily_run.retrieve_latest_actions_from_trello(
            board_lookup, board_name, "last_action_id")

        board_one.fetch_actions.assert_called_once_with(
            {"fields", "all", "filter", action_list_str},
            action_limit=1000,
            since="last_action_id")
        assert actions == results


class Test_retrieve_all_cards_from_trello:
    def test_retrieve_all_cards(self, mocker):
        board_one = mocker.Mock()

        card_one = mocker.Mock()
        card_two = mocker.Mock()
        card_one.id = "card-one-id"
        card_two.id = "card-two-id"
        expected_result = [card_one, card_two]
        board_one.get_cards.return_value = expected_result

        board_name = "board-one-name"
        board_lookup = {"board-one-name": board_one}
        results = daily_run.retrieve_all_cards_from_trello(
            board_lookup, board_name)

        assert results == expected_result


class Test_save_card_lookup:
    def test_save_card(self, mocker):
        mocked_config = mocker.Mock()
        mocked_config.cards_file = "cards.json"
        mocked_open = mocker.patch("daily_run.open", return_value="Mock FP")
        mocked_json_dump = mocker.patch(
            "daily_run.json.dump", return_value=None)
        daily_run.save_card_lookup({}, mocked_config)
        mocked_open.assert_called_once_with(
            "cards.json", "w")
        mocked_json_dump.assert_called_once_with(
            {},
            "Mock FP",
            indent="  ")


class Test_save_action_list:
    def test_save_action_list(self, mocker):
        mocked_config = mocker.Mock()
        mocked_config.actions_file = "actions.json"
        mocked_open = mocker.patch("daily_run.open", return_value="Mock FP")
        mocked_json_dump = mocker.patch(
            "daily_run.json.dump", return_value=None)
        assert daily_run.save_action_list([], mocked_config) is None
        mocked_open.assert_called_once_with(
            "actions.json", "w")
        mocked_json_dump.assert_called_once_with(
            [],
            "Mock FP",
            indent="  ")


class Test_create_card_lookup:
    def test_create(self, mocker):
        card_one = mocker.Mock()
        card_two = mocker.Mock()
        card_one.id = "card-one-id"
        card_one._json_obj = {"id": "card-one-id"}
        card_two.id = "card-two-id"
        card_two._json_obj = {"id": "card-two-id"}
        card_lookup = {
            card_one.id: card_one,
            card_two.id: card_two}
        card_json_lookup = {
            card_one.id: card_one._json_obj,
            card_two.id: card_two._json_obj}

        list_of_cards = [card_one, card_two]

        assert daily_run.create_card_lookup(list_of_cards) == [
            card_lookup, card_json_lookup]


class Test_load_from_local:
    def test_retrieves_from_local_json_file(self, mocker):
        mocked_config = mocker.Mock()
        action_list = [123, 456]
        card_json_lookup = {"abc": 123, "def": 456}
        mocked_load_action_list = mocker.patch(
            "daily_run.load_action_list",
            return_value=action_list)
        mocked_load_card_lookup = mocker.patch(
            "daily_run.load_card_lookup",
            return_value=card_json_lookup)

        result = daily_run.load_from_local(mocked_config)

        assert result[0] == action_list
        assert result[1] == card_json_lookup
        mocked_load_action_list.assert_called_once_with(mocked_config)
        mocked_load_card_lookup.assert_called_once_with(mocked_config)


class Test_first_time_load:
    def test_retrieve_all_actions_cards_and_save_them(self, mocker):
        mocked_config = mocker.Mock()
        mocked_config.board_name = "board-one"
        handle = "handle"
        board_lookup = {"board-one": 123}
        action_list = [123, 456]
        cards = [789, 987]
        card_lookup = {"card_lookup": 123}
        card_json_lookup = {"card_json_lookup": 456}
        context = {
            "card_json_lookup": card_json_lookup,
            "action_list": action_list,
            "handle": handle,
            "board_lookup": board_lookup
        }

        mocked_retrieve_all_actions_from_trello = mocker.patch(
            "daily_run.retrieve_all_actions_from_trello",
            return_value=action_list)
        mocked_save_action_list = mocker.patch(
            "daily_run.save_action_list",
            return_value=None)
        mocked_retrieve_all_cards_from_trello = mocker.patch(
            "daily_run.retrieve_all_cards_from_trello",
            return_value=cards)
        mocked_create_card_lookup = mocker.patch(
            "daily_run.create_card_lookup",
            return_value=[card_lookup, card_json_lookup])
        mocked_save_card_lookup = mocker.patch(
            "daily_run.save_card_lookup",
            return_value=None)

        daily_run.first_time_load(context, mocked_config)

        mocked_retrieve_all_actions_from_trello.assert_called_once_with(
            board_lookup, "board-one")
        mocked_save_action_list.assert_called_once_with(
            action_list, mocked_config)
        mocked_retrieve_all_cards_from_trello.assert_called_once_with(
            board_lookup, "board-one")
        mocked_create_card_lookup.assert_called_once_with(cards)
        mocked_save_card_lookup.assert_called_once_with(
            card_json_lookup, mocked_config)


class Test_get_card_ids_from_action_list:
    def test_find_cards_from_actions(self):
        action_list = [
            {
                "id": 123,
                "data": {
                    "card": {
                        "id": "abc"}}},
            {
                "id": 456,
                "data": {}},
            {
                "id": 789,
                "data": {
                    "card": {
                        "id": "def"}}}]
        expected_card_list = ["abc", "def"]

        assert daily_run.get_card_ids_from_action_list(
            action_list) == expected_card_list


class Test_update_card_json_lookup:
    def test_update_card_json_lookup(self, mocker):
        handle = mocker.Mock()

        updated_card_ids = ["xyz", "opq", "abc"]
        new_action_list = "new_action_list"
        card_json_lookup = {"abc": {"id": "abc"}, "def": {"id": "def"}}
        expected_card_json_lookup = {
            "abc": {"id": "abc", "updates": "existing"},
            "def": {"id": "def"},
            "xyz": {"id": "xyz"},
            "opq": {"id": "opq"}}
        mocked_get_card_ids_from_action_list = mocker.patch(
            "daily_run.get_card_ids_from_action_list",
            return_value=updated_card_ids)

        card_one = mocker.Mock()
        card_one._json_obj = {"id": "xyz"}
        card_two = mocker.Mock()
        card_two._json_obj = {"id": "opq"}
        card_three = mocker.Mock()
        card_three._json_obj = {"id": "abc", "updates": "existing"}

        progress_bar = mocker.Mock()
        mocked_tqdm = mocker.patch(
            "daily_run.tqdm",
            return_value=progress_bar)

        handle.get_card.side_effect = [card_one, card_two, card_three]

        results = daily_run.update_card_json_lookup(
            handle, card_json_lookup, new_action_list)

        mocked_get_card_ids_from_action_list.assert_called_once_with(
            new_action_list)
        mocked_tqdm.assert_called()
        assert handle.mock_calls == [mocker.call.get_card(
            'xyz'), mocker.call.get_card('opq'), mocker.call.get_card('abc')]
        assert results == expected_card_json_lookup


class Test_update_action_list:
    def test_update_action_list(self, mocker):
        action_list = [{"id": 123}, {"id": 456}]
        new_action_list = [{"id": 789}]
        results = daily_run.update_action_list(action_list, new_action_list)
        assert results == [{"id": 789}, {"id": 123}, {"id": 456}]


class Test_update_cards_and_actions:
    def test_retrieve_new_actions_cards_append_or_update_and_save(
            self, mocker):
        mocked_config = mocker.Mock()
        mocked_config.board_name = "board-one"
        handle = "handle"
        board_lookup = {"board-one": 123}
        action_list = [{"id": 123}, {"id": 456}]
        card_json_lookup = {"abc": {"id": "abc"}, "def": {"id": "def"}}
        new_action_list = [789]

        context = {
            "handle": handle,
            "card_json_lookup": card_json_lookup,
            "action_list": action_list,
            "board_lookup": board_lookup
        }

        mocked_retrieve_latest_actions_from_trello = mocker.patch(
            "daily_run.retrieve_latest_actions_from_trello",
            return_value=new_action_list)
        mocked_update_card_json_lookup = mocker.patch(
            "daily_run.update_card_json_lookup",
            return_value=card_json_lookup)
        mocked_update_action_list = mocker.patch(
            "daily_run.update_action_list",
            return_value=action_list)
        mocked_save_action_list = mocker.patch(
            "daily_run.save_action_list",
            return_value=None)
        mocked_save_card_lookup = mocker.patch(
            "daily_run.save_card_lookup",
            return_value=None)

        daily_run.update_cards_and_actions(
            context, mocked_config)

        mocked_retrieve_latest_actions_from_trello.assert_called_once_with(
            board_lookup, "board-one", action_list[0]["id"])
        mocked_update_card_json_lookup.assert_called_once_with(
            handle, card_json_lookup, new_action_list)
        mocked_update_action_list.assert_called_once_with(
            action_list, new_action_list)
        mocked_save_action_list.assert_called_once_with(
            action_list, mocked_config)
        mocked_save_card_lookup.assert_called_once_with(
            card_json_lookup, mocked_config)


class Test_run:
    def test_empty_action_list(self, mocker):
        mocked_config = mocker.Mock()
        handle = "handle"
        action_list = []
        card_json_lookup = {}

        board_one = mocker.Mock()
        board_name = "board-one-name"
        board_lookup = {board_name: board_one}

        context = {
            "handle": handle,
            "card_json_lookup": card_json_lookup,
            "action_list": action_list,
            "board_lookup": board_lookup,
            "list_lookup": "list_lookup"
        }

        mocked_create_daily_config = mocker.patch(
            "daily_run.Daily_config",
            return_value=mocked_config)
        mocked_load_from_local = mocker.patch(
            "daily_run.load_from_local",
            return_value=[action_list, card_json_lookup])
        mocked_init_trello_conn = mocker.patch(
            "daily_run.init_trello_conn",
            return_value="handle")
        mocked_setup_board_lookup = mocker.patch(
            "daily_run.setup_board_lookup",
            return_value=board_lookup)
        mocked_setup_list_lookup = mocker.patch(
            "daily_run.setup_list_lookup",
            return_value="list_lookup")
        mocked_first_time_load = mocker.patch(
            "daily_run.first_time_load",
            return_value=None)
        mocked_update_cards_and_actions = mocker.patch(
            "daily_run.update_cards_and_actions",
            return_value=None)
        mocked_perform_archival = mocker.patch(
            "daily_run.perform_archival",
            return_value=None)
        mocked_perform_sync_cards = mocker.patch(
            "daily_run.perform_sync_cards",
            return_value=None)

        daily_run.run()

        mocked_create_daily_config.assert_called_once()
        mocked_load_from_local.assert_called_once_with(mocked_config)
        mocked_init_trello_conn.assert_called_once_with(mocked_config)
        mocked_setup_board_lookup.assert_called_once_with(handle)
        mocked_setup_list_lookup.assert_called_once_with(board_lookup)
        mocked_first_time_load.assert_called_once_with(
            context,
            mocked_config)
        mocked_update_cards_and_actions.assert_not_called()
        mocked_perform_archival.assert_called_once_with(
            context, mocked_config)
        mocked_perform_sync_cards.assert_called_once_with(
            context, mocked_config)

    def test_non_empty_action_list(self, mocker):
        mocked_config = mocker.Mock()
        handle = "handle"
        action_list = [123]
        card_json_lookup = {}

        board_one = mocker.Mock()
        board_name = "board-one-name"
        board_lookup = {board_name: board_one}

        context = {
            "handle": handle,
            "action_list": action_list,
            "card_json_lookup": card_json_lookup,
            "board_lookup": board_lookup,
            "list_lookup": "list_lookup"
        }

        mocked_create_daily_config = mocker.patch(
            "daily_run.Daily_config",
            return_value=mocked_config)
        mocked_load_from_local = mocker.patch(
            "daily_run.load_from_local",
            return_value=[action_list, card_json_lookup])
        mocked_init_trello_conn = mocker.patch(
            "daily_run.init_trello_conn",
            return_value="handle")
        mocked_setup_board_lookup = mocker.patch(
            "daily_run.setup_board_lookup",
            return_value=board_lookup)
        mocked_setup_list_lookup = mocker.patch(
            "daily_run.setup_list_lookup",
            return_value="list_lookup")
        mocked_first_time_load = mocker.patch(
            "daily_run.first_time_load",
            return_value=None)
        mocked_update_cards_and_actions = mocker.patch(
            "daily_run.update_cards_and_actions",
            return_value=[action_list, card_json_lookup])
        mocked_perform_archival = mocker.patch(
            "daily_run.perform_archival",
            return_value=None)
        mocked_perform_sync_cards = mocker.patch(
            "daily_run.perform_sync_cards",
            return_value=None)

        daily_run.run()

        mocked_create_daily_config.assert_called_once()
        mocked_load_from_local.assert_called_once_with(mocked_config)
        mocked_init_trello_conn.assert_called_once_with(mocked_config)
        mocked_setup_board_lookup.assert_called_once_with(handle)
        mocked_setup_list_lookup.assert_called_once_with(board_lookup)
        mocked_update_cards_and_actions.assert_called_once_with(
            context, mocked_config)
        mocked_first_time_load.assert_not_called()
        mocked_perform_archival.assert_called_once_with(
            context, mocked_config)
        mocked_perform_sync_cards.assert_called_once_with(
            context, mocked_config)
