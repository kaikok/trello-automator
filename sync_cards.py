import json
import datetime
from trello_helper import change_card_list, find_list, lookup_board_with_id, find_list_with_id


def perform_sync_cards(context, config):
    context["card_sync_lookup"] = \
        load_card_sync_lookup(config)
    context["card_sync_lookup"] = add_new_sync_cards(context, config)
    save_card_sync_lookup(context["card_sync_lookup"], config)
    # sync_all_cards(context, config)


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
        (card, list_id) = job
        print(f'Executing move card "{card.name}" to list "{list_id}"')
        change_card_list(card, list_id)


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

        before_list_id = latest_movement["data"]["listBefore"]["id"]
        before_list_name = latest_movement["data"]["listBefore"]["name"]
        after_list_id = latest_movement["data"]["listAfter"]["id"]
        after_list_name = latest_movement["data"]["listAfter"]["name"]

        if (latest_movement["data"]["card"]["id"] == source_card.id):
            print(
                f'Add job move placeholder from "{before_list_name}" {before_list_id} to "{after_list_name}" {after_list_id}')
            return (placeholder_card, after_list_id)
        else:
            print(
                f'Add job move source from "{before_list_name}" {before_list_id} to "{after_list_name}" {after_list_id}')
            return (source_card, after_list_id)
    return None


def get_card_status(context, config, card):
    board_id = card.board_id
    board_lookup = context["board_lookup"]
    board = lookup_board_with_id(board_lookup, board_id)
    list_id = card.list_id
    list = find_list_with_id(board_lookup, board.name, list_id)

    destination_board_config = config.root["tasks"]["card_sync"]["destination_board"]
    source_board_config_list = config.root["tasks"]["card_sync"]["source_boards"]

    if (destination_board_config["name"] == board.name):
        todo_list_name = destination_board_config["list_names"]["todo"]
        in_progress_list_name = destination_board_config["list_names"]["in_progress"]
        done_list_name = destination_board_config["list_names"]["done"]
        if (list.name == todo_list_name):
            return "todo"
        if (list.name == in_progress_list_name):
            return "in_progress"
        if (list.name == done_list_name):
            return "done"
    else:
        for source_board_config in source_board_config_list:
            if (source_board_config["name"] == board.name):
                todo_list_name = source_board_config["list_names"]["todo"]
                in_progress_list_name = source_board_config["list_names"]["in_progress"]
                done_list_name = source_board_config["list_names"]["done"]
                if (list.name == todo_list_name):
                    return "todo"
                if (list.name == in_progress_list_name):
                    return "in_progress"
                if (list.name == done_list_name):
                    return "done"
    return "not_found"


def get_list_id_for_new_status(context, config, board_id, new_status):
    board_lookup = context["board_lookup"]
    board = lookup_board_with_id(board_lookup, board_id)
    destination_board_config = config.root["tasks"]["card_sync"]["destination_board"]
    source_board_config_list = config.root["tasks"]["card_sync"]["source_boards"]
    # list_name = None
    # if (destination_board_config["name"] == board.name):
    #     list_name = destination_board_config[]
    # else:


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
