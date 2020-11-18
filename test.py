import unittest
from unittest.mock import patch, Mock, ANY

import self as self
from vk_api.bot_longpoll import VkBotMessageEvent

from vk_bot import VkBot


class TestBot(unittest.TestCase):

    def setUp(self) -> None:
        self.RAW_EVENT = {
            'type': 'message_new',
            'object': {
                'message': {
                    'date': 1605664299,
                    'from_id': 5123054,
                    'id': 38, 'out': 0,
                    'peer_id': 5123054,
                    'text': 'sdfasdf',
                    'conversation_message_id': 38,
                    'fwd_messages': [],
                    'important': False,
                    'random_id': 0,
                    'attachments': [],
                    'is_hidden': False
                },
                'client_info': {
                    'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link'],
                    'keyboard': True,
                    'inline_keyboard': True,
                    'carousel': False,
                    'lang_id': 0
                }
            },
            'group_id': 50574685,
            'event_id': 'dbd9102ea6e4bb1a20729e49424ee31d0ebe958f'
        }

    def test_run(self):
        count = 5
        events = [{}] * count
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock

        with patch('vk_bot.vk_api.VkApi'):
            with patch('vk_bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                bot = VkBot('', '')
                bot.on_event = Mock()
                bot.run()

                bot.on_event.assert_called()
                bot.on_event.assert_any_call({})
                assert bot.on_event.call_count == count

    def test_on_event(self):
        event = VkBotMessageEvent(raw=self.RAW_EVENT)
        send_mock = Mock()
        with patch('vk_bot.vk_api.VkApi'):
            with patch('vk_bot.VkBotLongPoll'):
                bot = VkBot('', '')
                bot.api = Mock()
                bot.api.messages.send = send_mock
                bot.on_event(event=event)
        send_mock.assert_called_once_with(
            user_id=self.RAW_EVENT['object']['message']['from_id'],
            random_id=ANY,
            message=self.RAW_EVENT['object']['message']['text']
        )


if __name__ == '__main__':
    unittest.main()