import json
from daily_run import retrieve_list_from_trello


def perform_sync_cards(context, config):
    # context["card_sync_lookup"] = \
    #     load_card_sync_lookup(config)
    # context["card_sync_lookup"] = find_sync_new_cards(context, config)
    # sync_all_cards(context, config)
    pass

def load_card_sync_lookup(config):
    try:
        card_sync_lookup = json.load(open(config.root.tasks.card_sync.persistence.json_file, "r"))
    except FileNotFoundError:
        card_sync_lookup = {}
    return card_sync_lookup

def update_sync_cards(context, config):
    source_list = retrieve_list_from_trello(
        context["board_lookup"], 
        config.root.tasks.card_sync.source_boards[0]["name"],
        config.root.tasks.card_sync.source_boards[0]["list_names"]["todo"])
    source_cards = source_list.list_cards()
    for card in source_cards:
        is_synced = context['card_sync_lookup'].get(card.id) != None
        if (not is_synced):
            placeholder_card = create_placeholder_card(context, config, card)
            context["card_sync_lookup"]["source"][card.id] = placeholder_card
            context["card_sync_lookup"]["placeholder"][placeholder_card.id] = card
    print(context["card_sync_lookup"])
    return context["card_sync_lookup"]

def find_new_cards(card_sync_lookup, card_list):
    new_cards = []
    for card in card_list:
        not_synced = (card_sync_lookup["source"].get(card.id) == None)
        if (not_synced):
            new_cards.append(card) 
    return new_cards

def create_placeholder_card(card_sync_lookup, card_list):
    pass