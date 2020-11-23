import unittest
from copy import deepcopy
from unittest.mock import patch, Mock, ANY

from pony.orm import db_session, rollback
from vk_api.bot_longpoll import VkBotMessageEvent
import settings
from generate_ticket import generate_ticket
from vk_bot import VkBot


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with db_session as session:
            test_func(*args, **kwargs)
            rollback()
    return wrapper

class TestBot(unittest.TestCase):

    def setUp(self) -> None:
        self.INPUTS = [
            'Привет',
            'А когда?',
            'Где будет конференция?',
            'Зарегистрируй меня',
            'Иван',
            'мой адрес email@email',
            'email@email.ru',
        ]
        self.EXPECTED_OUTPUTS = [
            settings.DEFAULT_ANSWER,
            settings.INTENTS[0]['answer'],
            settings.INTENTS[1]['answer'],
            settings.SCENARIOS['registration']['steps']['step1']['text'],
            settings.SCENARIOS['registration']['steps']['step2']['text'],
            settings.SCENARIOS['registration']['steps']['step2']['failure_text'],
            settings.SCENARIOS['registration']['steps']['step3']['text'].format(name='Иван', email='email@email.ru')
        ]
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

    @isolate_db
    def test_on_event(self):
        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock
        events = []

        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event['object']['message']['text'] = input_text
            events.append(VkBotMessageEvent(event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch('vk_bot.VkBotLongPoll', return_value=long_poller_mock):
            bot = VkBot('', '')
            bot.api = api_mock
            bot.run()

        assert send_mock.call_count == len(self.INPUTS)

        real_outputs = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_outputs.append(kwargs['message'])
        assert real_outputs == self.EXPECTED_OUTPUTS

    def test_generation_ticket(self):
        ticket_file = generate_ticket("DWE", 'mail@mail.ru')

        with open('image/ticket-example.png', 'rb') as expected_file:
            expected_bytes = expected_file.read()
        assert ticket_file.read() == expected_bytes


if __name__ == '__main__':
    unittest.main()