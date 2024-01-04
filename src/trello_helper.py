def find_list(board_lookup, board_name, list_name):
    lists = board_lookup[board_name].get_lists("open")
    list_lookup = {list.name: list for list in lists}
    return list_lookup.get(list_name)


def get_card(handle, card_id):
    return handle.get_card(card_id)


def get_card_actions(card, action_filter="createCard"):
    return card.fetch_actions(action_filter=action_filter, action_limit=1000)


def lookup_board_with_id(board_lookup, board_id):
    boards = board_lookup.values()
    for board in boards:
        if (board.id == board_id):
            return board
    return None
