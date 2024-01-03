from datetime import datetime
import archival


class Test_perform_archival:
    def test_perform_archival(self, mocker):
        mocked_config = mocker.Mock()

        handle = "handle"
        action_list = []
        board_one = mocker.Mock()
        board_name = "board-one-name"
        board_lookup = {board_name: board_one}

        context = {
            "handle": handle,
            "action_list": action_list,
            "board_lookup": board_lookup
        }

        mocked_config.archival_board_name = "ABC"
        mocked_config.board_name = "DEF"
        mocked_config.done_list_name = "GHI"
        archival_jobs = [123, 456]

        mocked_find_done_card_and_create_archival_jobs = mocker.patch(
            "archival.find_done_card_and_create_archival_jobs",
            return_value=archival_jobs)
        mocked_process_archival_job = mocker.patch(
            "archival.process_archival_job",
            return_value=None)

        archival.perform_archival(context, mocked_config)

        mocked_find_done_card_and_create_archival_jobs.assert_called_once_with(
            board_lookup, "DEF", action_list, "GHI")
        mocked_process_archival_job.assert_called_once_with(
            board_lookup, "ABC", archival_jobs)


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
            "archival.create_card_action_list_lookup",
            return_value=card_action_list_lookup)
        mocked_retrieve_list_from_trello = mocker.patch(
            "archival.retrieve_list_from_trello",
            return_value=done_list)
        mocked_get_move_to_done_list_date = mocker.patch(
            "archival.get_move_to_done_list_date",
            return_value="done_date")

        archival_jobs = archival.find_done_card_and_create_archival_jobs(
            board_lookup, board_name, action_list, done_list_name)

        mocked_create_card_action_list_lookup.assert_called_once_with(
            action_list)
        mocked_retrieve_list_from_trello.assert_called_once_with(
            board_lookup, board_name, done_list_name)
        mocked_get_move_to_done_list_date.assert_called_once_with(
            card_action_list_lookup, done_card.id, done_list.id)

        assert archival_jobs == [{'date': 'done_date', 'card': done_card}]


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
        mocker.patch("archival.datetime", mocked_datetime)

        mocked_calculate_sprint_dates_for_given_date = mocker.patch(
            "archival.calculate_sprint_dates_for_given_date",
            side_effect=[("2023-09-13T00:00:00", "2023-09-26T00:00:00"),
                         ("2023-08-02T00:00:00", "2023-08-15T00:00:00")])
        mocked_create_archival_list_if_not_found = mocker.patch(
            "archival.create_archival_list_if_not_found",
            return_value=list)

        archival.process_archival_job(
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
        mocker.patch("archival.datetime", mocked_datetime)

        mocked_calculate_sprint_dates_for_given_date = mocker.patch(
            "archival.calculate_sprint_dates_for_given_date",
            side_effect=[("2023-09-13T00:00:00", "2023-09-26T00:00:00"),
                         ("2023-09-13T00:00:00", "2023-09-26T00:00:00")])
        mocked_create_archival_list_if_not_found = mocker.patch(
            "archival.create_archival_list_if_not_found",
            return_value=list)

        archival.process_archival_job(
            board_lookup, archival_board_name, archival_jobs)

        mocked_datetime.now.assert_called_once()
        mocked_calculate_sprint_dates_for_given_date.assert_has_calls([
            mocker.call("2023-08-02T00:00:00",
                        faked_datetime_for_today.isoformat()),
            mocker.call("2023-08-02T00:00:00", archival_jobs[0]["date"][0:23])
        ], True)
        mocked_create_archival_list_if_not_found.assert_not_called()
        card.change_board.assert_not_called()


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

        assert archival.create_card_action_list_lookup(
            action_list) == expected_card_action_list_lookup

    def test_empty_action_list(self, mocker):
        action_list = []
        assert archival.create_card_action_list_lookup(
            action_list) == {}


class Test_retrieve_list_from_trello:
    def test_retrieve_list_from_trello(self, mocker):
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

        assert archival.retrieve_list_from_trello(
            board_lookup, board_name, done_list_name) == list_two

        board_one.get_lists.assert_called_once_with("all")


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
        assert archival.get_move_to_done_list_date(
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
        assert archival.get_move_to_done_list_date(
            card_action_list_lookup, card_id, done_list_id) is None


class Test_calculate_sprint_dates_for_given_date:
    def test_given_date_at_sprint_end_date(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        reference_end_date = "2023-08-15T00:00:00"
        given_date = "2023-08-15T00:00:00"

        expected_sprint_dates = (reference_start_date, reference_end_date)

        assert archival.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_next_sprint_start_date(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        next_start_date = "2023-08-16T00:00:00"
        next_end_date = "2023-08-29T00:00:00"
        given_date = "2023-08-16T00:00:00"

        expected_sprint_dates = (next_start_date, next_end_date)

        assert archival.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_next_sprint_end_date(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        next_start_date = "2023-08-16T00:00:00"
        next_end_date = "2023-08-29T00:00:00"
        given_date = "2023-08-29T00:00:00"

        expected_sprint_dates = (next_start_date, next_end_date)

        assert archival.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_next_next_sprint_start_date(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        next_next_start_date = "2023-08-30T00:00:00"
        next_next_end_date = "2023-09-12T00:00:00"
        given_date = "2023-08-30T00:00:00"

        expected_sprint_dates = (next_next_start_date, next_next_end_date)

        assert archival.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_the_middle_of_next_next_sprint(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        next_next_start_date = "2023-08-30T00:00:00"
        next_next_end_date = "2023-09-12T00:00:00"
        given_date = "2023-09-05T00:00:00"

        expected_sprint_dates = (next_next_start_date, next_next_end_date)

        assert archival.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_previous_sprint_end_date(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        previous_start_date = "2023-07-19T00:00:00"
        previous_end_date = "2023-08-01T00:00:00"
        given_date = "2023-08-01T00:00:00"

        expected_sprint_dates = (previous_start_date, previous_end_date)

        assert archival.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_previous_sprint_start_date(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        previous_start_date = "2023-07-19T00:00:00"
        previous_end_date = "2023-08-01T00:00:00"
        given_date = "2023-07-19T00:00:00"

        expected_sprint_dates = (previous_start_date, previous_end_date)

        assert archival.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_previous_previous_sprint_start_date(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        previous_previous_start_date = "2023-07-05T00:00:00"
        previous_previous_end_date = "2023-07-18T00:00:00"
        given_date = "2023-07-05T00:00:00"

        expected_sprint_dates = (
            previous_previous_start_date, previous_previous_end_date)

        assert archival.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_previous_previous_sprint_end_date(self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        previous_previous_start_date = "2023-07-05T00:00:00"
        previous_previous_end_date = "2023-07-18T00:00:00"
        given_date = "2023-07-18T00:00:00"

        expected_sprint_dates = (
            previous_previous_start_date, previous_previous_end_date)

        assert archival.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == expected_sprint_dates

    def test_given_date_at_the_middle_of_previous_previous_sprint_end_date(
            self, mocker):
        reference_start_date = "2023-08-02T00:00:00"
        previous_previous_start_date = "2023-07-05T00:00:00"
        previous_previous_end_date = "2023-07-18T00:00:00"
        given_date = "2023-07-12T00:00:00"

        assert archival.calculate_sprint_dates_for_given_date(
            reference_start_date, given_date) == (
            previous_previous_start_date, previous_previous_end_date)


class Test_create_archival_list_if_not_found:
    def test_archival_list_found(self, mocker):
        board_lookup = "board-lookup"
        archival_board_name = "archival-board-name"
        archival_list_name = "archival-list-name"
        list = "list"

        mocked_find_list = mocker.patch(
            "archival.find_list",
            return_value=list)

        assert archival.create_archival_list_if_not_found(
            board_lookup, archival_board_name, archival_list_name) == list

        mocked_find_list.assert_called_once_with(
            board_lookup, archival_board_name, archival_list_name)

    def test_archival_list_not_found(self, mocker):
        board_lookup = "board-lookup"
        archival_board_name = "archival-board-name"
        archival_list_name = "archival-list-name"
        list = "list"

        mocked_find_list = mocker.patch(
            "archival.find_list",
            return_value=None)
        mocked_create_archival_list = mocker.patch(
            "archival.create_archival_list",
            return_value=list)

        assert archival.create_archival_list_if_not_found(
            board_lookup, archival_board_name, archival_list_name) == list

        mocked_find_list.assert_called_once_with(
            board_lookup, archival_board_name, archival_list_name)
        mocked_create_archival_list.assert_called_once_with(
            board_lookup, archival_board_name, archival_list_name)


class Test_create_archival_list:
    def test_create_archival_list(self, mocker):
        new_list = "new-list"
        board_one = mocker.Mock()
        archival_board_name = "board-one-name"
        archival_list_name = "new-archival-list-name"
        board_lookup = {"board-one-name": board_one}
        board_one.add_list.return_value = new_list
        assert archival.create_archival_list(
            board_lookup, archival_board_name, archival_list_name) == new_list
        board_one.add_list.assert_called_once_with(archival_list_name, "top")
