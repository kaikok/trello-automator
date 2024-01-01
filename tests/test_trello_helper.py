from trello_helper import get_card, get_card_actions, find_list


class Test_find_list:
    def test_find_list(self, mocker):
        list_name = "wanted-list-name"

        list_one = mocker.Mock()
        list_one.name = "name-list-one"
        list_two = mocker.Mock()
        list_two.name = list_name
        lists = [list_one, list_two]

        board_one = mocker.Mock()
        board_name = "board-one-name"
        board_lookup = {"board-one-name": board_one}
        board_one.get_lists.return_value = lists

        assert find_list(
            board_lookup, board_name, list_name) == list_two


class Test_get_card:
    def test_get_card(self, mocker):
        card = mocker.Mock()
        card.id = "123"
        handle = mocker.Mock()
        handle.get_card.return_value = card
        assert get_card(handle, card.id) == card


class Test_get_card_actions:
    def test_retrieve_actions_of_card(self, mocker):
        action1 = "abc"
        action2 = "def"
        actionList = [action1, action2]
        mocked_card = mocker.Mock()
        mocked_card.fetch_actions.return_value = actionList
        action_types = "action_type1,action_type2"
        assert get_card_actions(mocked_card, action_types) == actionList
        mocked_card.fetch_actions.assert_called_once_with(
            action_filter=action_types
        )
