def find_list(board_lookup, board_name, list_name):
    lists = board_lookup[board_name].get_lists("open")
    list_lookup = {list.name: list for list in lists}
    return list_lookup.get(list_name)


def get_card(board_lookup, board_name, card_id):
    return board_lookup[board_name].get_card(card_id)


def get_card_actions(card):
    return card.fetch_actions()
