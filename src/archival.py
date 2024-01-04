import math


import time
from datetime import datetime, timedelta

from trello_helper import find_list


def perform_archival(context, config):
    archival_jobs = find_done_card_and_create_archival_jobs(
        context["board_lookup"],
        config.board_name,
        context["action_list"],
        config.done_list_name)
    process_archival_job(
        context["board_lookup"], config.archival_board_name, archival_jobs)


def find_done_card_and_create_archival_jobs(
        board_lookup, board_name, action_list, done_list_name):
    archival_jobs = []
    card_action_list_lookup = create_card_action_list_lookup(action_list)
    done_list = retrieve_list_from_trello(
        board_lookup, board_name, done_list_name)
    done_cards = done_list.list_cards()
    for done_card in done_cards:
        done_date = get_move_to_done_list_date(
            card_action_list_lookup, done_card.id, done_list.id)
        archival_jobs.append({"date": done_date, "card": done_card})
        print(f'Add Job Move {done_card.id} {done_card.name} to {done_date}.')
    return archival_jobs


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


def retrieve_list_from_trello(board_lookup, board_name, list_name):
    lists = board_lookup[board_name].get_lists("all")
    list_lookup = {list.name: list for list in lists}
    return list_lookup[list_name]


def get_move_to_done_list_date(card_action_list_lookup, card_id, done_list_id):
    for action in card_action_list_lookup[card_id]:
        if (action["type"] == "updateCard" and
                action["data"].get("listAfter") and
                action["data"]["listAfter"]["id"] == done_list_id):
            return action["date"]
        if (action["type"] == "moveCardToBoard" and
                action["data"].get("list") and
                action["data"]["list"]["id"] == done_list_id):
            return action["date"]
    return None


def process_archival_job(board_lookup, archival_board_name, archival_jobs):
    today = datetime.now()
    current_sprint_dates = calculate_sprint_dates_for_given_date(
        "2023-08-02T00:00:00", today.isoformat())
    for archival_job in archival_jobs:
        start_date, end_date = calculate_sprint_dates_for_given_date(
            "2023-08-02T00:00:00", archival_job["date"][0:23])
        if current_sprint_dates == (start_date, end_date):
            continue
        print(
            f'Executing Move '
            f'{archival_job["card"].id} '
            f'{archival_job["card"].name} to '
            f'{start_date}.')
        archival_list = create_archival_list_if_not_found(
            board_lookup, archival_board_name, start_date)
        archival_job["card"].change_board(
            board_lookup[archival_board_name].id, archival_list.id)
        time.sleep(1)


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


def create_archival_list_if_not_found(
        board_lookup, archival_board_name, archival_list_name):
    existing_list = find_list(
        board_lookup, archival_board_name, archival_list_name)
    if existing_list:
        return existing_list
    return create_archival_list(
        board_lookup, archival_board_name, archival_list_name)


def create_archival_list(
        board_lookup, archival_board_name, archival_list_name):
    new_list = board_lookup[archival_board_name].add_list(
        archival_list_name, "top")
    return new_list
