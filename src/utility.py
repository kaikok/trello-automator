
import sys
import json
from dotenv import load_dotenv
from config_object import Daily_config
from daily_run import init_trello_conn, setup_board_lookup, setup_list_lookup


def pretty_print_card_by_name(context, board_name, list_name, card_name):
    board = context["board_lookup"][board_name]
    list, _board_name, _list_name = \
        context["list_lookup"]["board_name"][board_name][list_name]
    cards = board.get_cards()
    found_cards = [card for card in cards if (
        card.name == card_name and card.list_id == list.id)]
    for found_card in found_cards:
        print("# Card\n---\n")
        print(json.dumps(found_card._json_obj, indent=2))
        print("\n")
        print("\n---\n## Attachments\n")
        for attachment in found_card.attachments:
            print(json.dumps(attachment, indent=2))
            print("\n")
    if (len(found_cards) == 0):
        print("Not found")
    return found_cards


if __name__ == "__main__":
    load_dotenv()
    config = Daily_config()
    context = {}
    context["handle"] = init_trello_conn(config)
    context["board_lookup"] = setup_board_lookup(context["handle"])
    context["list_lookup"] = setup_list_lookup(context["board_lookup"])

    if (len(sys.argv) != 4):
        print(sys.argv[1:])
        print("Syntax:")
        print("  python3 src/utility.py myBoardName myListName \"My card title\"")
    else:
        [_script_name, board_name, list_name, card_name] = sys.argv
        pretty_print_card_by_name(context, board_name, list_name, card_name)
