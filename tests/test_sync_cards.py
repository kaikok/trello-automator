from sync_cards import perform_sync_cards


class Test_perform_sync_cards:
    def test_method_exist(self, mocker):
        mocked_daily_config = mocker.Mock()
        context = {}
        perform_sync_cards(context, mocked_daily_config)

class Test_load_card_sync_lookup:
    pass

class Test_find_sync_new_cards:
    pass

class Test_sync_all_cards:
    pass
