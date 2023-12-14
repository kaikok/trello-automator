import json
from daily_run import find_list


def perform_sync_cards(context, config):
    # context["card_sync_lookup"] = \
    #     load_card_sync_lookup(config)
    # context["card_sync_lookup"] = find_sync_new_cards(context, config)
    # sync_all_cards(context, config)
    pass


def load_card_sync_lookup(config):
    try:
        card_sync_lookup = json.load(
            open(config.root.tasks.card_sync.persistence.json_file, "r"))
    except FileNotFoundError:
        card_sync_lookup = {}
    return card_sync_lookup


def update_sync_cards(context, config):
    source_list = find_list(
        context["board_lookup"],
        config.root.tasks.card_sync.source_boards[0]["name"],
        config.root.tasks.card_sync.source_boards[0]["list_names"]["todo"])
    placeholder_list = find_list(
        context["board_lookup"],
        config.root.tasks.card_sync.destination_board["name"],
        config.root.tasks.card_sync.destination_board["list_names"]["todo"])

    source_cards = source_list.list_cards()
    new_cards = find_new_cards(source_cards)
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
    return destination_list.add_card(name=source_card.name, desc=f"SYNC-FROM({source_card.id})\n---\n")


def add_lookup(card_sync_lookup, source_card, placeholder_card):
    card_sync_lookup["source"][source_card.id] = {
        "placeholder": placeholder_card.id}
    card_sync_lookup["placeholder"][placeholder_card.id] = {
        "source": source_card.id}
    return card_sync_lookup
