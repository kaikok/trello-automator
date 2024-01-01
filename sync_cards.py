import json
import datetime
from trello_helper import find_list


def perform_sync_cards(context, config):
    context["card_sync_lookup"] = \
        load_card_sync_lookup(config)
    context["card_sync_lookup"] = add_new_sync_cards(context, config)
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


def find_latest_card_movement(context, config, source_card_id, placeholder_card_id):
    handle = context["handle"]
    latest_move = None
    source_card = handle.get_card(source_card_id)
    placeholder_card = handle.get_card(placeholder_card_id)
    source_actions = source_card.fetch_actions(action_filter="moveCardToBoard,moveCardFromBoard")
    if (len(source_actions) > 0):
        latest_move = source_actions[0]
    
    placeholder_actions = placeholder_card.fetch_actions(action_filter="moveCardToBoard,moveCardFromBoard")
    if (len(placeholder_actions) > 0):
        if (latest_move == None):
            latest_move = placeholder_actions[0]
        else:
            placeholder_datetime = datetime.datetime.fromisoformat(
                placeholder_actions[0]["date"].replace("Z", "+00:00"))
            latest_move_datetime = datetime.datetime.fromisoformat(
                latest_move["date"].replace("Z", "+00:00"))
            if placeholder_datetime > latest_move_datetime:
                latest_move = placeholder_actions[0]
    if (latest_move != None and
        latest_move["memberCreator"]["username"] == config.automation_username):
        return None
    return latest_move
