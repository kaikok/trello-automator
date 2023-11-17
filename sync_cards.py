import json


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

def find_sync_new_cards(context, config):
    return []
