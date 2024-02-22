import sys
import trello
import json
from dotenv import load_dotenv
from config_object import Daily_config
from daily_run import init_trello_conn, setup_board_lookup, setup_list_lookup


def patched_fetch_json(self,
            uri_path,
            http_method='GET',
            headers=None,
            query_params=None,
            post_args=None,
            files=None):
    """ Fetch some JSON from Trello """

    # explicit values here to avoid mutable default values
    if headers is None:
        headers = {}
    if query_params is None:
        query_params = {}
    if post_args is None:
        post_args = {}

    # if files specified, we don't want any data
    data = None
    if files is None and post_args != {}:
        data = json.dumps(post_args)

    # set content type and accept headers to handle JSON
    if http_method in ("POST", "PUT", "DELETE") and not files:
        headers['Content-Type'] = 'application/json; charset=utf-8'

    headers['Accept'] = 'application/json'

    # construct the full URL without query parameters
    if uri_path[0] == '/':
        uri_path = uri_path[1:]
    url = 'https://api.trello.com/1/%s' % uri_path

    if self.oauth is None:
        query_params['key'] = self.api_key
        query_params['token'] = self.api_secret

    # perform the HTTP requests, if possible uses OAuth authentication
    response = self.http_service.request(http_method, url, params=query_params,
                                            headers=headers, data=data,
                                            auth=self.oauth, files=files,
                                            proxies=self.proxies)

    if response.status_code == 401:
        raise trello.Unauthorized("%s at %s" % (response.text, url), response)
    if response.status_code != 200:
        raise trello.ResourceUnavailable("%s at %s" % (response.text, url), response)

    return response.json()


trello.TrelloClient.fetch_json = patched_fetch_json


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
    if (len(sys.argv) != 4):
        print(sys.argv[1:])
        print("Syntax:")
        print("  python3 src/utility.py myBoardName myListName \"My card title\"")
    else:
        load_dotenv()
        config = Daily_config()
        context = {}
        context["handle"] = init_trello_conn(config)
        context["board_lookup"] = setup_board_lookup(context["handle"])
        context["list_lookup"] = setup_list_lookup(context["board_lookup"])
        [_script_name, board_name, list_name, card_name] = sys.argv
        pretty_print_card_by_name(context, board_name, list_name, card_name)
