import json
import datetime
from trello_helper import find_list, lookup_board_with_id


def perform_sync_cards(context, config):
    context["card_sync_lookup"] = \
        load_card_sync_lookup(config)
    context["card_sync_lookup"] = add_new_sync_cards(context, config)
    save_card_sync_lookup(context["card_sync_lookup"], config)
    context["card_sync_lookup"] = sync_all_cards(context, config)
    save_card_sync_lookup(context["card_sync_lookup"], config)


def load_card_sync_lookup(config):
    try:
        card_sync_lookup = json.load(
            open(config.root["tasks"]["card_sync"]["persistence"]["json_file"], "r"))
    except FileNotFoundError:
        card_sync_lookup = {
            "source": {},
            "placeholder": {}
        }
    return card_sync_lookup


def add_new_sync_cards(context, config):
    source_cards = []

    for source_board in config.root["tasks"]["card_sync"]["source_boards"]:
        source_list = find_list(
            context["board_lookup"],
            source_board["name"],
            source_board["list_names"]["todo"])
        for source_card in source_list.list_cards():
            source_cards.append(source_card)

    placeholder_list = find_list(
        context["board_lookup"],
        config.root["tasks"]["card_sync"]["destination_board"]["name"],
        config.root["tasks"]["card_sync"]["destination_board"]["list_names"]["todo"])

    new_cards = find_new_cards(context['card_sync_lookup'], source_cards)
    for new_card in new_cards:
        print(f"Creating placeholder for {new_card.id}, \"{new_card.name}\"")
        placeholder_card = create_placeholder_card(new_card, placeholder_list)
        context['card_sync_lookup'] = add_lookup(
            context['card_sync_lookup'], new_card, placeholder_card)
    return context["card_sync_lookup"]


def find_new_cards(card_sync_lookup, list_of_cards):
    new_cards = []
    for card in list_of_cards:
        not_synced = (card_sync_lookup["source"].get(card.id) == None)
        if (not_synced):
            new_cards.append(card)
    return new_cards


def create_placeholder_card(source_card, destination_list):
    return destination_list.add_card(name=source_card.name, desc=f"SYNC-FROM({source_card.id})\n[Goto source card]({source_card.shortUrl})\n---\n")


def add_lookup(card_sync_lookup, source_card, placeholder_card):
    card_sync_lookup["source"][source_card.id] = {
        "placeholder": placeholder_card.id}
    card_sync_lookup["placeholder"][placeholder_card.id] = {
        "source": source_card.id}
    return card_sync_lookup


def save_card_sync_lookup(card_sync_lookup, config):
    json.dump(card_sync_lookup,
              open(config.root["tasks"]["card_sync"]["persistence"]["json_file"], "w"), indent="  ")


def sync_all_cards(context, config):
    source_cards = context["card_sync_lookup"]["source"]
    jobs = []
    for source_card_id in source_cards.keys():
        placeholder_card_id = source_cards[source_card_id]["placeholder"]
        job = sync_one_card(context, config, source_card_id,
                            placeholder_card_id)
        if (job != None):
            jobs.append(job)
    for job in jobs:
        (card, new_status) = job
        if (new_status == "not_found"):
            context["card_sync_lookup"] = remove_card_sync(context, card)
            continue
        print(f'Executing update card "{card.name}" to "{new_status}"')
        update_card_status(context, config, card, new_status)
    return context["card_sync_lookup"]


def sync_one_card(context, config, source_card_id, placeholder_card_id):
    handle = context["handle"]
    source_card = handle.get_card(source_card_id)
    placeholder_card = handle.get_card(placeholder_card_id)
    source_status = get_card_status(context, config, source_card)
    placeholder_status = get_card_status(context, config, placeholder_card)
    latest_movement = find_latest_card_movement(
        config, source_card, placeholder_card)

    if (source_status != placeholder_status):
        if (latest_movement == None):
            raise Exception("Movement action not found!")

        print("---")
        print(f"Source: {source_status}")
        print(f"Placeholder: {placeholder_status}")
        print(latest_movement["id"])
        print(latest_movement["data"]["card"]["name"])
        print(latest_movement["data"]["board"]["name"])
        print(latest_movement["data"]["listBefore"]["name"])
        print(latest_movement["data"]["listAfter"]["name"])
        print(latest_movement)

        if (latest_movement["data"]["card"]["id"] == source_card.id):
            print(
                f'Add job move placeholder from "{placeholder_status}" to "{source_status}')
            return (placeholder_card, source_status)
        else:
            print(
                f'Add job move source from "{source_status}" to "{placeholder_status}"')
            return (source_card, placeholder_status)
    return None


def get_card_status(context, config, card):
    list_id = card.list_id
    list_lookup_entry = context["list_lookup"]["list_id"].get(list_id)
    if (list_lookup_entry == None):
        return "not_found"
    (_list, list_board_name, list_name) = list_lookup_entry

    destination_board_config = config.root["tasks"]["card_sync"]["destination_board"]
    source_board_config_list = config.root["tasks"]["card_sync"]["source_boards"]

    if (destination_board_config["name"] == list_board_name):
        todo_list_name = destination_board_config["list_names"]["todo"]
        in_progress_list_name = destination_board_config["list_names"]["in_progress"]
        done_list_name = destination_board_config["list_names"]["done"]
        if (list_name == todo_list_name):
            return "todo"
        if (list_name == in_progress_list_name):
            return "in_progress"
        if (list_name == done_list_name):
            return "done"
    else:
        for source_board_config in source_board_config_list:
            if (source_board_config["name"] == list_board_name):
                todo_list_name = source_board_config["list_names"]["todo"]
                in_progress_list_name = source_board_config["list_names"]["in_progress"]
                done_list_name = source_board_config["list_names"]["done"]
                if (list_name == todo_list_name):
                    return "todo"
                if (list_name == in_progress_list_name):
                    return "in_progress"
                if (list_name == done_list_name):
                    return "done"
    return "not_found"


def update_card_status(context, config, card, new_status):
    list_lookup = context["list_lookup"]
    board_lookup = context["board_lookup"]
    board = lookup_board_with_id(board_lookup, card.board_id)

    destination_board_config = config.root["tasks"]["card_sync"]["destination_board"]
    source_board_config_list = config.root["tasks"]["card_sync"]["source_boards"]

    if (destination_board_config["name"] == board.name):
        list_name = destination_board_config["list_names"][new_status]
    else:
        for source_board_config in source_board_config_list:
            if (source_board_config["name"] == board.name):
                list_name = source_board_config["list_names"][new_status]

    (list, _list_board_name,
     _list_name) = list_lookup["board_name"][board.name][list_name]
    card.change_list(list.id)


def remove_card_sync(context, card):
    card_sync_lookup = context["card_sync_lookup"]
    if card_sync_lookup["source"].get(card.id):
        placeholder_card_id = card_sync_lookup["source"][card.id]["placeholder"]
        card_sync_lookup["source"].pop(card.id, None)
        card_sync_lookup["placeholder"].pop(placeholder_card_id, None)
    if card_sync_lookup["placeholder"].get(card.id):
        source_card_id = card_sync_lookup["placeholder"][card.id]["source"]
        card_sync_lookup["source"].pop(source_card_id, None)
        card_sync_lookup["placeholder"].pop(card.id, None)
    return card_sync_lookup


def find_latest_card_movement(config, source_card, placeholder_card):
    action_list = [
        "moveCardFromBoard",
        "moveCardToBoard",
        "updateCard",
    ]
    action_list_str = ','.join(action_list)
    action_filter = {
        "fields",
        "all",
        "filter",
        action_list_str}

    latest_move = None
    source_actions = source_card.fetch_actions(action_filter=action_filter)
    source_actions_filtered = [
        source_action for source_action in source_actions if (
            source_action["type"] == "moveCardFromBoard" or
            source_action["type"] == "moveCardToBoard" or
            source_action["data"].get("listAfter") != None
        )]

    num_of_source_actions = len(source_actions_filtered)
    if (num_of_source_actions > 0):
        latest_move = source_actions_filtered[0]

    placeholder_actions = placeholder_card.fetch_actions(
        action_filter=action_filter)
    placeholder_actions_filtered = [
        placeholder_action for placeholder_action in placeholder_actions if (
            placeholder_action["type"] == "moveCardFromBoard" or
            placeholder_action["type"] == "moveCardToBoard" or
            placeholder_action["data"].get("listAfter") != None)]

    num_of_placeholder_actions = len(placeholder_actions_filtered)
    if (num_of_placeholder_actions > 0):
        if (latest_move == None):
            latest_move = placeholder_actions_filtered[0]
        else:
            placeholder_datetime = datetime.datetime.fromisoformat(
                placeholder_actions_filtered[0]["date"].replace("Z", "+00:00"))
            latest_move_datetime = datetime.datetime.fromisoformat(
                latest_move["date"].replace("Z", "+00:00"))
            if placeholder_datetime > latest_move_datetime:
                latest_move = placeholder_actions_filtered[0]
    if (latest_move != None and
            latest_move["memberCreator"]["username"] == config.automation_username):
        return None
    return latest_move
