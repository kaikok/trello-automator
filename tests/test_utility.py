from utility import pretty_print_card_by_name


class Test_get_pretty_card:
    def test_returns_found_cards(self, mocker):
        list1 = mocker.Mock()
        list1.id = "list1-id"
        list1.name = "list1"

        list2 = mocker.Mock()
        list2.id = "list2-id"
        list2.name = "list2"

        card1 = mocker.Mock()
        card1.list_id = list1.id
        card1.attachments = []
        card1._json_obj = {}

        card2 = mocker.Mock()
        card2.list_id = list2.id
        card2.attachments = ["attachment1", "attachment2"]
        card2._json_obj = {}

        board = mocker.Mock()
        board.get_cards.return_value = [card1, card2]
        context = {
            "board_lookup": {
                board.name: board
            },
            "list_lookup": {
                "board_name": {
                    board.name: {
                        list1.name: (list1, board.name, list1.name),
                        list2.name: (list2, board.name, list2.name)
                    }
                },
                "list_id": {
                    list1.id: (list1, board.name, list1.name),
                    list2.id: (list2, board.name, list2.name)
                }
            }
        }

        assert pretty_print_card_by_name(
            context, board.name, list2.name, card2.name) == [card2]

    def test_no_card_found(self, mocker):
        list1 = mocker.Mock()
        list1.id = "list1-id"
        list1.name = "list1"

        list2 = mocker.Mock()
        list2.id = "list2-id"
        list2.name = "list2"

        card1 = mocker.Mock()
        card1.list_id = "not-found-list-id"
        card1.attachments = []
        card1._json_obj = {}

        card2 = mocker.Mock()
        card2.list_id = list2.id
        card2.attachments = ["attachment1", "attachment2"]
        card2._json_obj = {}

        board = mocker.Mock()
        board.get_cards.return_value = [card1, card2]
        context = {
            "board_lookup": {
                board.name: board
            },
            "list_lookup": {
                "board_name": {
                    board.name: {
                        list1.name: (list1, board.name, list1.name),
                        list2.name: (list2, board.name, list2.name)
                    }
                },
                "list_id": {
                    list1.id: (list1, board.name, list1.name),
                    list2.id: (list2, board.name, list2.name)
                }
            }
        }

        assert pretty_print_card_by_name(
            context, board.name, list1.name, card1.name) == []
