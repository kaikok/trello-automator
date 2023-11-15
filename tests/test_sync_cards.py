from sync_cards import perform_sync_cards


class Test_sync_cards:
    def test_file_exist(self):
        pass

    def test_sync_cards(self, mocker):
        mocked_daily_config = mocker.Mock()
        context = {}
        perform_sync_cards(context, mocked_daily_config)
