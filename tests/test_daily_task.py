import os
from datetime import datetime
import trello
import daily_task


class Test_load_action_list:
    def test_empty_file(self):
        os.environ["ACTIONS_FILE"] = \
            os.getcwd() + "/tests/empty_action_list.json"
        assert daily_task.load_action_list() == []

    def test_file_not_found(self):
        os.environ["ACTIONS_FILE"] = \
            os.getcwd() + "/tests/not_found_action_list.json"
        assert daily_task.load_action_list() == []


class Test_load_card_lookup:
    def test_empty_file(self):
        os.environ["CARDS_FILE"] = \
            os.getcwd() + "/tests/empty_card_lookup.json"
        assert daily_task.load_card_lookup() == {}

    def test_file_not_found(self):
        os.environ["CARDS_FILE"] = \
            os.getcwd() + "/tests/not_found_card_lookup.json"
        assert daily_task.load_card_lookup() == {}

    def test_valid_file(self):
        os.environ["CARDS_FILE"] = os.getcwd() + "/tests/card_lookup.json"
        assert daily_task.load_card_lookup() == {
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
    def test_should_return_a_trello_client(self):
        handle = daily_task.init_trello_conn()
        assert isinstance(handle, trello.trelloclient.TrelloClient)

    def test_should_use_env_var(self, mocker):
        mocker.patch("daily_task.TrelloClient.__init__", return_value=None)

        os.environ["API_KEY"] = "ABC"
        os.environ["TOKEN"] = "DEF"
        handle = daily_task.init_trello_conn()
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
        assert daily_task.setup_board_lookup(handle) == {
            "board-one-name": board_one,
            "board-two-name": board_two}


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

        actions = daily_task.retrieve_all_actions_from_trello(
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

        actions = daily_task.retrieve_all_actions_from_trello(
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

        actions = daily_task.retrieve_latest_actions_from_trello(
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
        results = daily_task.retrieve_all_cards_from_trello(
            board_lookup, board_name)

        assert results == expected_result


class Test_save_card_lookup:
    def test_save_card(self, mocker):
        mocker.patch("daily_task.open", return_value="Mock FP")
        mocked_json_dump = mocker.patch(
            "daily_task.json.dump", return_value=None)
        daily_task.save_card_lookup({})
        mocked_json_dump.assert_called_once_with(
            {},
            "Mock FP",
            indent="  ")


class Test_save_action_list:
    def test_save_action_list(self, mocker):
        mocked_config = mocker.Mock()
        mocked_config.actions_file = "actions.json"
        mocked_open = mocker.patch("daily_task.open", return_value="Mock FP")
        mocked_json_dump = mocker.patch(
            "daily_task.json.dump", return_value=None)
        assert daily_task.save_action_list([], mocked_config) is None
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

        assert daily_task.create_card_lookup(list_of_cards) == [
            card_lookup, card_json_lookup]


class Test_load_from_local:
    def test_retrieves_from_local_json_file(self, mocker):
        action_list = [123, 456]
        card_json_lookup = {"abc": 123, "def": 456}
        mocked_load_action_list = mocker.patch(
            "daily_task.load_action_list",
            return_value=action_list)
        mocked_load_card_lookup = mocker.patch(
            "daily_task.load_card_lookup",
            return_value=card_json_lookup)

        result = daily_task.load_from_local()

        assert result[0] == action_list
        assert result[1] == card_json_lookup
        mocked_load_action_list.assert_called_once()
        mocked_load_card_lookup.assert_called_once()


class Test_first_time_load:
    def test_retrieve_all_actions_cards_and_save_them(self, mocker):
        mocked_config = mocker.Mock()
        handle = "handle"
        board_lookup = {"board-one": 123}
        action_list = [123, 456]
        cards = [789, 987]
        card_lookup = {"card_lookup": 123}
        card_json_lookup = {"card_json_lookup": 456}
        os.environ["BOARD_NAME"] = "board-one"

        mocked_setup_board_lookup = mocker.patch(
            "daily_task.setup_board_lookup",
            return_value=board_lookup)
        mocked_retrieve_all_actions_from_trello = mocker.patch(
            "daily_task.retrieve_all_actions_from_trello",
            return_value=action_list)
        mocked_save_action_list = mocker.patch(
            "daily_task.save_action_list",
            return_value=None)
        mocked_retrieve_all_cards_from_trello = mocker.patch(
            "daily_task.retrieve_all_cards_from_trello",
            return_value=cards)
        mocked_create_card_lookup = mocker.patch(
            "daily_task.create_card_lookup",
            return_value=[card_lookup, card_json_lookup])
        mocked_save_card_lookup = mocker.patch(
            "daily_task.save_card_lookup",
            return_value=None)

        daily_task.first_time_load(handle)

        mocked_setup_board_lookup.assert_called_once_with(handle)
        mocked_retrieve_all_actions_from_trello.assert_called_once_with(
            board_lookup, "board-one")
        mocked_save_action_list.assert_called_once_with(
            action_list, mocked_config)
        mocked_retrieve_all_cards_from_trello.assert_called_once_with(
            board_lookup, "board-one")
        mocked_create_card_lookup.assert_called_once_with(cards)
        mocked_save_card_lookup.assert_called_once_with(card_json_lookup)


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

        assert daily_task.get_card_ids_from_action_list(
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
            "daily_task.get_card_ids_from_action_list",
            return_value=updated_card_ids)

        card_one = mocker.Mock()
        card_one._json_obj = {"id": "xyz"}
        card_two = mocker.Mock()
        card_two._json_obj = {"id": "opq"}
        card_three = mocker.Mock()
        card_three._json_obj = {"id": "abc", "updates": "existing"}

        progress_bar = mocker.Mock()
        mocked_tqdm = mocker.patch(
            "daily_task.tqdm",
            return_value=progress_bar)

        handle.get_card.side_effect = [card_one, card_two, card_three]

        results = daily_task.update_card_json_lookup(
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
        results = daily_task.update_action_list(action_list, new_action_list)
        assert results == [{"id": 789}, {"id": 123}, {"id": 456}]


class Test_update_cards_and_actions:
    def test_retrieve_new_actions_cards_append_or_update_and_save(
            self, mocker):
        mocked_config = mocker.Mock()
        handle = "handle"
        board_lookup = {"board-one": 123}
        action_list = [{"id": 123}, {"id": 456}]
        card_json_lookup = {"abc": {"id": "abc"}, "def": {"id": "def"}}
        new_action_list = [789]

        mocked_setup_board_lookup = mocker.patch(
            "daily_task.setup_board_lookup",
            return_value=board_lookup)
        mocked_retrieve_latest_actions_from_trello = mocker.patch(
            "daily_task.retrieve_latest_actions_from_trello",
            return_value=new_action_list)
        mocked_update_card_json_lookup = mocker.patch(
            "daily_task.update_card_json_lookup",
            return_value=card_json_lookup)
        mocked_update_action_list = mocker.patch(
            "daily_task.update_action_list",
            return_value=action_list)
        mocked_save_action_list = mocker.patch(
            "daily_task.save_action_list",
            return_value=None)
        mocked_save_card_lookup = mocker.patch(
            "daily_task.save_card_lookup",
            return_value=None)

        daily_task.update_cards_and_actions(
            action_list, card_json_lookup, handle)

        mocked_setup_board_lookup.assert_called_once_with(handle)
        mocked_retrieve_latest_actions_from_trello.assert_called_once_with(
            board_lookup, "board-one", action_list[0]["id"])
        mocked_update_card_json_lookup.assert_called_once_with(
            handle, card_json_lookup, new_action_list)
        mocked_update_action_list.assert_called_once_with(
            action_list, new_action_list)
        mocked_save_action_list.assert_called_once_with(
            action_list, mocked_config)
        mocked_save_card_lookup.assert_called_once_with(
            card_json_lookup)


class Test_calculate_sprint_dates_for_given_date:
    def test_given_date_at_sprint_end_date(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        reference_end_date = "2023-08-15T00:00:00"
        given_date = "2023-08-15T00:00:00"

        expected_sprint_dates = (reference_start_date, reference_end_date)

        assert daily_task.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_next_sprint_start_date(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        next_start_date = "2023-08-16T00:00:00"
        next_end_date = "2023-08-29T00:00:00"
        given_date = "2023-08-16T00:00:00"

        expected_sprint_dates = (next_start_date, next_end_date)

        assert daily_task.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_next_sprint_end_date(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        next_start_date = "2023-08-16T00:00:00"
        next_end_date = "2023-08-29T00:00:00"
        given_date = "2023-08-29T00:00:00"

        expected_sprint_dates = (next_start_date, next_end_date)

        assert daily_task.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_next_next_sprint_start_date(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        next_next_start_date = "2023-08-30T00:00:00"
        next_next_end_date = "2023-09-12T00:00:00"
        given_date = "2023-08-30T00:00:00"

        expected_sprint_dates = (next_next_start_date, next_next_end_date)

        assert daily_task.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_the_middle_of_next_next_sprint(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        next_next_start_date = "2023-08-30T00:00:00"
        next_next_end_date = "2023-09-12T00:00:00"
        given_date = "2023-09-05T00:00:00"

        expected_sprint_dates = (next_next_start_date, next_next_end_date)

        assert daily_task.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_previous_sprint_end_date(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        previous_start_date = "2023-07-19T00:00:00"
        previous_end_date = "2023-08-01T00:00:00"
        given_date = "2023-08-01T00:00:00"

        expected_sprint_dates = (previous_start_date, previous_end_date)

        assert daily_task.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_previous_sprint_start_date(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        previous_start_date = "2023-07-19T00:00:00"
        previous_end_date = "2023-08-01T00:00:00"
        given_date = "2023-07-19T00:00:00"

        expected_sprint_dates = (previous_start_date, previous_end_date)

        assert daily_task.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_previous_previous_sprint_start_date(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        previous_previous_start_date = "2023-07-05T00:00:00"
        previous_previous_end_date = "2023-07-18T00:00:00"
        given_date = "2023-07-05T00:00:00"

        expected_sprint_dates = (
            previous_previous_start_date, previous_previous_end_date)

        assert daily_task.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_previous_previous_sprint_end_date(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        previous_previous_start_date = "2023-07-05T00:00:00"
        previous_previous_end_date = "2023-07-18T00:00:00"
        given_date = "2023-07-18T00:00:00"

        expected_sprint_dates = (
            previous_previous_start_date, previous_previous_end_date)

        assert daily_task.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_the_middle_of_previous_previous_sprint_end_date(
            self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        previous_previous_start_date = "2023-07-05T00:00:00"
        previous_previous_end_date = "2023-07-18T00:00:00"
        given_date = "2023-07-12T00:00:00"

        assert daily_task.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == (
            previous_previous_start_date, previous_previous_end_date)


class Test_retrieve_done_list_from_trello:
    def test_retrieve_done_list_from_trello(self, mocker):
        board_one = mocker.Mock()
        board_name = "board-one-name"
        board_lookup = {"board-one-name": board_one}
        done_list_name = "done"

        list_one = mocker.Mock()
        list_one.name = "todo"
        list_one.id = "abc"

        list_two = mocker.Mock()
        list_two.name = "done"
        list_two.id = "def"

        results = [list_one, list_two]
        board_one.get_lists.return_value = results

        assert daily_task.retrieve_done_list_from_trello(
            board_lookup, board_name, done_list_name) == list_two

        board_one.get_lists.assert_called_once_with("all")


class Test_find_archival_list:
    def test_find_archival_list(self, mocker):
        archival_list_name = "new-archival-list-name"

        list_one = mocker.Mock()
        list_one.name = "name-list-one"
        list_two = mocker.Mock()
        list_two.name = archival_list_name
        lists = [list_one, list_two]

        board_one = mocker.Mock()
        archival_board_name = "board-one-name"
        board_lookup = {"board-one-name": board_one}
        board_one.get_lists.return_value = lists

        assert daily_task.find_archival_list(
            board_lookup, archival_board_name, archival_list_name) == list_two


class Test_create_archival_list:
    def test_create_archival_list(self, mocker):
        new_list = "new-list"
        board_one = mocker.Mock()
        archival_board_name = "board-one-name"
        archival_list_name = "new-archival-list-name"
        board_lookup = {"board-one-name": board_one}
        board_one.add_list.return_value = new_list
        assert daily_task.create_archival_list(
            board_lookup, archival_board_name, archival_list_name) == new_list


class Test_create_archival_list_if_not_found:
    def test_archival_list_found(self, mocker):
        board_lookup = "board-lookup"
        archival_board_name = "archival-board-name"
        archival_list_name = "archival-list-name"
        list = "list"

        mocked_find_archival_list = mocker.patch(
            "daily_task.find_archival_list",
            return_value=list)

        assert daily_task.create_archival_list_if_not_found(
            board_lookup, archival_board_name, archival_list_name) == list

        mocked_find_archival_list.assert_called_once_with(
            board_lookup, archival_board_name, archival_list_name)

    def test_archival_list_not_found(self, mocker):
        board_lookup = "board-lookup"
        archival_board_name = "archival-board-name"
        archival_list_name = "archival-list-name"
        list = "list"

        mocked_find_archival_list = mocker.patch(
            "daily_task.find_archival_list",
            return_value=None)
        mocked_create_archival_list = mocker.patch(
            "daily_task.create_archival_list",
            return_value=list)

        assert daily_task.create_archival_list_if_not_found(
            board_lookup, archival_board_name, archival_list_name) == list

        mocked_find_archival_list.assert_called_once_with(
            board_lookup, archival_board_name, archival_list_name)
        mocked_create_archival_list.assert_called_once_with(
            board_lookup, archival_board_name, archival_list_name)


class Test_create_card_action_list_lookup:
    def test_create_card_action_list_lookup(self, mocker):
        card_one = {
            "id": "card-one-id-123"}

        action_one = {
            "id": "action-one-id-234",
            "data": {
                "card": card_one}}
        action_two = {
            "id": "action-two-id-345",
            "data": {
                "card": card_one}}
        action_list = [action_one, action_two]

        expected_card_action_list_lookup = {
            card_one["id"]: [action_one, action_two]
        }

        assert daily_task.create_card_action_list_lookup(
            action_list) == expected_card_action_list_lookup

    def test_empty_action_list(self, mocker):
        action_list = []
        assert daily_task.create_card_action_list_lookup(
            action_list) == {}


class Test_get_move_to_done_list_date:
    def test_date_found(self, mocker):
        card_id = "card-id-123"
        done_list_id = "done-list-id-456"
        move_date = "move-date"
        other_date = "other-date"
        card_action_list_lookup = {
            card_id: [{
                "type": "updateCard",
                "data": {
                    "listAfter": {
                        "id": "not-this-list"}},
                      "date": other_date},
                      {
                "type": "updateCard",
                "data": {
                    "listAfter": {
                        "id": done_list_id}},
                      "date": move_date}]}
        assert daily_task.get_move_to_done_list_date(
            card_action_list_lookup, card_id, done_list_id) == move_date

    def test_date_not_found(self, mocker):
        card_id = "card-id-123"
        done_list_id = "done-list-id-456"
        other_date = "other-date"
        card_action_list_lookup = {
            card_id: [{
                "type": "updateCard",
                "data": {
                    "listAfter": {
                        "id": "not-this-list"}},
                      "date": other_date}]}
        assert daily_task.get_move_to_done_list_date(
            card_action_list_lookup, card_id, done_list_id) is None


class Test_find_done_card_and_create_archival_jobs:
    def test_find_done_card_and_create_archival_jobs(self, mocker):
        board_one = mocker.Mock()
        board_name = "board-one-name"
        board_lookup = {board_name: board_one}

        done_card = mocker.Mock()
        done_card.id = "card-123"

        action_list = []
        card_action_list_lookup = {
            "card123": [{"id": "action-id-123", "data": {"card": None}}]}

        done_list_name = "Done"
        done_list = mocker.Mock()
        done_list.list_cards.return_value = [done_card]
        done_list.id = "list-id-456"

        mocked_create_card_action_list_lookup = mocker.patch(
            "daily_task.create_card_action_list_lookup",
            return_value=card_action_list_lookup)
        mocked_retrieve_done_list_from_trello = mocker.patch(
            "daily_task.retrieve_done_list_from_trello",
            return_value=done_list)
        mocked_get_move_to_done_list_date = mocker.patch(
            "daily_task.get_move_to_done_list_date",
            return_value="done_date")

        archival_jobs = daily_task.find_done_card_and_create_archival_jobs(
            board_lookup, board_name, action_list, done_list_name)

        mocked_create_card_action_list_lookup.assert_called_once_with(
            action_list)
        mocked_retrieve_done_list_from_trello.assert_called_once_with(
            board_lookup, board_name, done_list_name)
        mocked_get_move_to_done_list_date.assert_called_once_with(
            card_action_list_lookup, done_card.id, done_list.id)

        assert archival_jobs == [{'date': 'done_date', 'card': done_card}]


class Test_perform_archival:
    def test_perform_archival(self, mocker):
        handle = "handle"
        action_list = []
        board_one = mocker.Mock()
        board_name = "board-one-name"
        board_lookup = {board_name: board_one}
        os.environ["ARCHIVAL_BOARD_NAME"] = "ABC"
        os.environ["BOARD_NAME"] = "DEF"
        os.environ["DONE_LIST_NAME"] = "GHI"
        archival_jobs = [123, 456]

        mocked_setup_board_lookup = mocker.patch(
            "daily_task.setup_board_lookup",
            return_value=board_lookup)
        mocked_find_done_card_and_create_archival_jobs = mocker.patch(
            "daily_task.find_done_card_and_create_archival_jobs",
            return_value=archival_jobs)
        mocked_process_archival_job = mocker.patch(
            "daily_task.process_archival_job",
            return_value=None)

        daily_task.perform_archival(handle, action_list)

        mocked_setup_board_lookup.assert_called_once_with(handle)
        mocked_find_done_card_and_create_archival_jobs.assert_called_once_with(
            board_lookup, "DEF", action_list, "GHI")
        mocked_process_archival_job.assert_called_once_with(
            board_lookup, "ABC", archival_jobs)


class Test_process_archival_job:
    def test_process_archival_job(self, mocker):
        board_one = mocker.Mock()
        board_one.id = "board-id-456"
        board_name = "board-one-name"
        board_lookup = {board_name: board_one}

        archival_board_name = "board-one-name"

        card = mocker.Mock()
        card.change_board.return_value = None

        archival_jobs = [{"date": "2023-08-10T11:07:49.365Z", "card": card}]
        list = mocker.Mock()
        list.id = "list-id-123"

        faked_datetime_for_today = datetime.fromisoformat(
            "2023-09-19T11:07:49.365")
        mocked_datetime = mocker.Mock()
        mocked_datetime.now.return_value = faked_datetime_for_today
        mocker.patch("daily_task.datetime", mocked_datetime)

        mocked_calculate_sprint_dates_for_given_date = mocker.patch(
            "daily_task.calculate_sprint_dates_for_given_date",
            side_effect=[("2023-09-13T00:00:00", "2023-09-26T00:00:00"),
                         ("2023-08-02T00:00:00", "2023-08-15T00:00:00")])
        mocked_create_archival_list_if_not_found = mocker.patch(
            "daily_task.create_archival_list_if_not_found",
            return_value=list)

        daily_task.process_archival_job(
            board_lookup, archival_board_name, archival_jobs)

        mocked_calculate_sprint_dates_for_given_date.assert_has_calls([
            mocker.call("2023-08-02T00:00:00",
                        faked_datetime_for_today.isoformat()),
            mocker.call("2023-08-02T00:00:00", archival_jobs[0]["date"][0:23])
        ], True)
        mocked_create_archival_list_if_not_found.assert_called_once_with(
            board_lookup,
            archival_board_name,
            "2023-08-02T00:00:00")
        card.change_board.assert_called_once_with(
            "board-id-456", "list-id-123")

    def test_do_not_process_current_sprint(self, mocker):
        board_one = mocker.Mock()
        board_one.id = "board-id-456"
        board_name = "board-one-name"
        board_lookup = {board_name: board_one}

        archival_board_name = "board-one-name"

        card = mocker.Mock()
        card.change_board.return_value = None

        archival_jobs = [{"date": "2023-09-19T11:07:49.365Z", "card": card}]
        list = mocker.Mock()
        list.id = "list-id-123"

        faked_datetime_for_today = datetime.fromisoformat(
            "2023-09-19T11:07:49.365")
        mocked_datetime = mocker.Mock()
        mocked_datetime.now.return_value = faked_datetime_for_today
        mocker.patch("daily_task.datetime", mocked_datetime)

        mocked_calculate_sprint_dates_for_given_date = mocker.patch(
            "daily_task.calculate_sprint_dates_for_given_date",
            side_effect=[("2023-09-13T00:00:00", "2023-09-26T00:00:00"),
                         ("2023-09-13T00:00:00", "2023-09-26T00:00:00")])
        mocked_create_archival_list_if_not_found = mocker.patch(
            "daily_task.create_archival_list_if_not_found",
            return_value=list)

        daily_task.process_archival_job(
            board_lookup, archival_board_name, archival_jobs)

        mocked_datetime.now.assert_called_once()
        mocked_calculate_sprint_dates_for_given_date.assert_has_calls([
            mocker.call("2023-08-02T00:00:00",
                        faked_datetime_for_today.isoformat()),
            mocker.call("2023-08-02T00:00:00", archival_jobs[0]["date"][0:23])
        ], True)
        mocked_create_archival_list_if_not_found.assert_not_called()
        card.change_board.assert_not_called()


class Test_run:
    def test_empty_action_list(self, mocker):
        action_list = []
        card_json_lookup = {}

        mocked_load_from_local = mocker.patch(
            "daily_task.load_from_local",
            return_value=[action_list, card_json_lookup])
        mocked_init_trello_conn = mocker.patch(
            "daily_task.init_trello_conn",
            return_value="handle")
        mocked_first_time_load = mocker.patch(
            "daily_task.first_time_load",
            return_value=None)
        mocked_update_cards_and_actions = mocker.patch(
            "daily_task.update_cards_and_actions",
            return_value=None)
        mocked_perform_archival = mocker.patch(
            "daily_task.perform_archival",
            return_value=None)

        daily_task.run()

        mocked_load_from_local.assert_called_once()
        mocked_init_trello_conn.assert_called_once()
        mocked_first_time_load.assert_called_once_with("handle")
        mocked_update_cards_and_actions.assert_not_called()
        mocked_perform_archival.assert_called_once()

    def test_non_empty_action_list(self, mocker):
        action_list = [123]
        card_json_lookup = {}

        mocked_load_from_local = mocker.patch(
            "daily_task.load_from_local",
            return_value=[action_list, card_json_lookup])
        mocked_init_trello_conn = mocker.patch(
            "daily_task.init_trello_conn",
            return_value="handle")
        mocked_first_time_load = mocker.patch(
            "daily_task.first_time_load",
            return_value=None)
        mocked_update_cards_and_actions = mocker.patch(
            "daily_task.update_cards_and_actions",
            return_value=[action_list, card_json_lookup])
        mocked_perform_archival = mocker.patch(
            "daily_task.perform_archival",
            return_value=None)

        daily_task.run()

        mocked_load_from_local.assert_called_once()
        mocked_init_trello_conn.assert_called_once()
        mocked_update_cards_and_actions.assert_called_once_with(
            action_list, card_json_lookup, "handle")
        mocked_first_time_load.assert_not_called()
        mocked_perform_archival.assert_called_once()
