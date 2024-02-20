import traceback
import json
import trello
from trello import TrelloClient
from dotenv import load_dotenv
import time
from tqdm import tqdm
from archival import perform_archival
from config_object import Daily_config
from sync_cards import perform_sync_cards


def run():
    config = Daily_config()
    context = {}
    context["action_list"], context["card_json_lookup"] = \
        load_from_local(config)

    context["handle"] = init_trello_conn(config)
    context["board_lookup"] = setup_board_lookup(context["handle"])
    context["list_lookup"] = setup_list_lookup(context["board_lookup"])

    if len(context["action_list"]) == 0:
        first_time_load(context, config)
    else:
        context["action_list"], context["card_json_lookup"] = \
            update_cards_and_actions(context, config)
    perform_archival(context, config)
    perform_sync_cards(context, config)


def load_from_local(config):
    action_list = load_action_list(config)
    card_json_lookup = load_card_lookup(config)
    return action_list, card_json_lookup


def load_action_list(config):
    try:
        actions_json = json.load(open(config.actions_file, "r"))
    except FileNotFoundError:
        actions_json = []
    return actions_json


def load_card_lookup(config):
    try:
        card_json_lookup = json.load(open(config.cards_file, "r"))
    except FileNotFoundError:
        card_json_lookup = {}
    return card_json_lookup


def init_trello_conn(config):
    client = TrelloClient(
        api_key=config.api_key,
        token=config.token)
    return client


def first_time_load(context, config):
    print("First time setup...")
    action_list = retrieve_all_actions_from_trello(
        context["board_lookup"], config.board_name)
    save_action_list(action_list, config)
    cards = retrieve_all_cards_from_trello(
        context["board_lookup"], config.board_name)
    card_lookup, card_json_lookup = create_card_lookup(cards)
    save_card_lookup(card_json_lookup, config)
    return action_list, card_lookup, card_json_lookup


def setup_board_lookup(handle):
    list_of_boards = handle.list_boards()
    board_lookup = {board.name: board for board in list_of_boards}
    return board_lookup


def setup_list_lookup(board_lookup):
    list_lookup = {
        "board_name": {},
        "list_id": {}
    }
    for board_name in board_lookup.keys():
        board = board_lookup[board_name]
        lists = board.get_lists("open")
        for list in lists:
            list_lookup["list_id"][list.id] = (list, board_name, list.name)
            if list_lookup["board_name"].get(board_name):
                list_lookup["board_name"][board_name][list.name] = \
                    (list, board_name, list.name)
            else:
                list_lookup["board_name"][board_name] = {
                    list.name: (list, board_name, list.name)
                }
    return list_lookup


def retrieve_all_actions_from_trello(board_lookup, board_name):
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
    all_actions = []
    actions = board_lookup[board_name].fetch_actions(
        {"fields", "all", "filter", action_list_str}, action_limit=1000)
    all_actions = all_actions + actions
    print(len(actions))
    while len(actions) == 1000:
        actions = board_lookup[board_name].fetch_actions(
            {"fields", "all", "filter", action_list_str},
            action_limit=1000,
            before=all_actions[-1]['id'])
        all_actions = all_actions + actions
    return all_actions


def save_action_list(action_list, config):
    json.dump(action_list,
              open(config.actions_file, "w"), indent="  ")


def retrieve_all_cards_from_trello(board_lookup, board_name):
    list_of_cards = board_lookup[board_name].get_cards()
    return list_of_cards


def create_card_lookup(cards):
    card_lookup = {card.id: card for card in cards}
    card_json_lookup = {card.id: card._json_obj for card in cards}
    return [card_lookup, card_json_lookup]


def save_card_lookup(card_json_lookup, config):
    json.dump(card_json_lookup,
              open(config.cards_file, "w"), indent="  ")


def update_cards_and_actions(context, config):
    print("Looking for updates...")
    new_action_list = retrieve_latest_actions_from_trello(
        context["board_lookup"], config.board_name, context["action_list"][0]['id'])
    print(f'{len(new_action_list)} new Actions found.')
    card_json_lookup = update_card_json_lookup(
        context["handle"],
        context["card_json_lookup"],
        new_action_list)
    action_list = update_action_list(
        context["action_list"], new_action_list)
    save_action_list(action_list, config)
    save_card_lookup(card_json_lookup, config)
    return action_list, card_json_lookup


def retrieve_latest_actions_from_trello(board_lookup,
                                        board_name,
                                        last_action_id):
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
    return board_lookup[board_name].fetch_actions(
        {"fields",
         "all",
         "filter",
         action_list_str},
        action_limit=1000,
        since=last_action_id)


def update_card_json_lookup(
        handle, card_json_lookup, new_action_list):
    updated_card_entries = get_card_ids_from_action_list(new_action_list)
    total_cards = len(updated_card_entries)
    print(f'{total_cards} Cards need to be checked for update')
    progress_bar = tqdm(total=total_cards)
    for updated_card_entry in updated_card_entries:
        (updated_card_id, updated_card_name, updated_card_link) = updated_card_entry
        progress_bar.set_description(f"Processing {updated_card_id} {updated_card_link} {updated_card_name}")
        try:
            updated_card = handle.get_card(updated_card_id)
            card_json_lookup[updated_card_id] = updated_card._json_obj
        except (trello.ResourceUnavailable):
            print(f"Error getting {updated_card_id} {trello.ResourceUnavailable}")
            print(traceback.format_exc())
        time.sleep(1)
        progress_bar.update(1)
    progress_bar.close()
    return card_json_lookup


def get_card_ids_from_action_list(action_list):
    card_ids = []
    for action in action_list:
        card = action["data"].get("card")
        if card and card.get("id"):
            card_name = card.get("name")
            card_link = card.get("shortLink")
            card_ids.append(
                (action["data"]["card"]["id"],
                 card_name if card_name else "Name not found",
                 card_link if card_link else "Card shortlink not found"))
    return list(set(card_ids))


def update_action_list(action_list, new_action_list):
    return new_action_list + action_list


if __name__ == "__main__":
    load_dotenv()
    run()
