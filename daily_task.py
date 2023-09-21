import os
import json
from trello import TrelloClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
import math


def init_trello_conn():
    client = TrelloClient(
        api_key=os.getenv("API_KEY"),
        token=os.getenv("TOKEN"))
    return client


def load_action_list():
    try:
        actions_json = json.load(open(os.getenv("ACTIONS_FILE"), "r"))
    except FileNotFoundError:
        actions_json = []
    return actions_json


def load_card_lookup():
    try:
        card_json_lookup = json.load(open(os.getenv("CARDS_FILE"), "r"))
    except FileNotFoundError:
        card_json_lookup = {}
    return card_json_lookup


def setup_board_lookup(handle):
    list_of_boards = handle.list_boards()
    board_lookup = {board.name: board for board in list_of_boards}
    return board_lookup


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
    return board_lookup[board_name].fetch_actions(
        {"fields", "all", "filter", action_list_str})


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
        since=last_action_id)


def retrieve_all_cards_from_trello(board_lookup, board_name):
    list_of_cards = board_lookup[board_name].get_cards()
    return list_of_cards


def create_card_lookup(cards):
    card_lookup = {card.id: card for card in cards}
    card_json_lookup = {card.id: card._json_obj for card in cards}
    return [card_lookup, card_json_lookup]


def save_card_lookup(card_json_lookup):
    json.dump(card_json_lookup,
              open(os.getenv("CARDS_FILE"), "w"), indent="  ")


def save_action_list(action_list):
    json.dump(action_list,
              open(os.getenv("ACTIONS_FILE"), "w"), indent="  ")


def load_from_local():
    action_list = load_action_list()
    card_json_lookup = load_card_lookup()
    return action_list, card_json_lookup


def first_time_load(handle):
    board_lookup = setup_board_lookup(handle)
    action_list = retrieve_all_actions_from_trello(
        board_lookup, os.getenv("BOARD_NAME"))
    save_action_list(action_list)
    cards = retrieve_all_cards_from_trello(
        board_lookup, os.getenv("BOARD_NAME"))
    card_lookup, card_json_lookup = create_card_lookup(cards)
    save_card_lookup(card_json_lookup)
    return action_list, card_lookup, card_json_lookup


def get_card_ids_from_action_list(action_list):
    card_ids = []
    for action in action_list:
        if action["data"].get("card"):
            card_ids.append(action["data"]["card"]["id"])
    return card_ids


def update_card_json_lookup(
        handle, card_json_lookup, new_action_list):
    updated_card_ids = get_card_ids_from_action_list(new_action_list)

    for updated_card_id in updated_card_ids:
        updated_card = handle.get_card(updated_card_id)
        card_json_lookup[updated_card_id] = updated_card._json_obj
    return card_json_lookup


def update_action_list(action_list, new_action_list):
    return new_action_list + action_list


def update_cards_and_actions(action_list, card_json_lookup, handle):
    board_lookup = setup_board_lookup(handle)
    new_action_list = retrieve_latest_actions_from_trello(
        board_lookup, os.getenv("BOARD_NAME"), action_list[0]['id'])
    card_json_lookup = update_card_json_lookup(
        handle,
        card_json_lookup,
        new_action_list)
    action_list = update_action_list(action_list, new_action_list)
    save_action_list(action_list)
    save_card_lookup(card_json_lookup)
    return action_list, card_json_lookup


def retrieve_done_list_from_trello(board_lookup, board_name, done_list_name):
    lists = board_lookup[board_name].get_lists("all")
    list_lookup = {list.name: list for list in lists}
    return list_lookup[done_list_name]


def retrieve_done_cards_from_trello(board_lookup, board_name, done_list_name):
    list = retrieve_done_list_from_trello(
        board_lookup, board_name, done_list_name)
    if list:
        return list.list_cards()
    return []


def calculate_sprint_dates_for_given_date(reference_start_date, given_date):
    reference_start_date = datetime.fromisoformat(reference_start_date)
    reference_end_date = reference_start_date + timedelta(days=13)
    given_date = datetime.fromisoformat(given_date)
    day_difference = (given_date - reference_start_date).days
    is_past_date = day_difference < 0

    if is_past_date:
        sprint_difference = math.ceil(abs(day_difference) / 14.0)
    else:
        sprint_difference = math.floor(abs(day_difference) / 14.0)

    for sprint_number in range(sprint_difference):
        reference_start_date = reference_start_date + \
            (timedelta(days=-14) if is_past_date else timedelta(days=14))
        reference_end_date = reference_start_date + timedelta(days=13)

    return (reference_start_date.isoformat(), reference_end_date.isoformat())


def find_archival_list(board_lookup, archival_board_name, archival_list_name):
    lists = board_lookup[archival_board_name].get_lists("open")
    list_lookup = {list.name: list for list in lists}
    return list_lookup.get(archival_list_name)


def create_archival_list(
        board_lookup, archival_board_name, archival_list_name):
    new_list = board_lookup[archival_board_name].add_list(
        archival_list_name, "bottom")
    return new_list


def create_archival_list_if_not_found(
        board_lookup, archival_board_name, archival_list_name):
    existing_list = find_archival_list(
        board_lookup, archival_board_name, archival_list_name)
    if existing_list:
        return existing_list
    return create_archival_list(
        board_lookup, archival_board_name, archival_list_name)


def create_card_action_list_lookup(action_list):
    card_action_list_lookup = {}
    for action in action_list:
        if action["data"].get("card"):
            card_id = action["data"]["card"]["id"]
            if card_action_list_lookup.get(card_id):
                card_action_list_lookup[card_id].append(action)
            else:
                card_action_list_lookup[card_id] = [action]
    return card_action_list_lookup


def get_move_to_done_list_date(card_action_list_lookup, card_id, done_list_id):
    for action in card_action_list_lookup[card_id]:
        if (action["type"] == "updateCard" and
                action["data"].get("listAfter") and
                action["data"]["listAfter"]["id"] == done_list_id):
            return action["date"]
    return None


def find_done_card_and_create_archival_jobs(
        board_lookup, board_name, action_list, done_list_name):
    archival_jobs = []
    card_action_list_lookup = create_card_action_list_lookup(action_list)
    done_list = retrieve_done_list_from_trello(
        board_lookup, board_name, done_list_name)
    done_cards = done_list.list_cards()
    for done_card in done_cards:
        done_date = get_move_to_done_list_date(
            card_action_list_lookup, done_card.id, done_list.id)
        archival_jobs.append({"date": done_date, "card": done_card})
    return archival_jobs


def perform_archival(handle, action_list):
    board_lookup = setup_board_lookup(handle)
    archival_jobs = find_done_card_and_create_archival_jobs(
        board_lookup,
        os.getenv("BOARD_NAME"),
        action_list,
        os.getenv("DONE_LIST_NAME"))
    process_archival_job(
        board_lookup, os.getenv("ARCHIVAL_BOARD_NAME"), archival_jobs)


def process_archival_job(board_lookup, archival_board_name, archival_jobs):
    today = datetime.now()
    current_sprint_dates = calculate_sprint_dates_for_given_date(
        "2023-08-02T00:00:00", today.isoformat())
    for archival_job in archival_jobs:
        start_date, end_date = calculate_sprint_dates_for_given_date(
            "2023-08-02T00:00:00", archival_job["date"][0:23])
        print((start_date, end_date))
        if current_sprint_dates == (start_date, end_date):
            continue
        archival_list = create_archival_list_if_not_found(
            board_lookup, archival_board_name, start_date)
        archival_job["card"].change_board(
            board_lookup[archival_board_name].id, archival_list.id)


def run():
    action_list, card_json_lookup = load_from_local()
    handle = init_trello_conn()
    if len(action_list) == 0:
        first_time_load(handle)
    else:
        action_list, card_json_lookup = update_cards_and_actions(
            action_list, card_json_lookup, handle)
    perform_archival(handle, action_list)


if __name__ == "__main__":
    load_dotenv()
    run()
