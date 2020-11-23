from random import randint
import vk_api
from pony.orm import db_session
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType, VkBotMessageEvent
import logging

import handlers
from generate_ticket import generate_ticket
from models import UserState, RegistrationDB

try:
    import settings
except:
    exit("setting.py.default -> settings.py and set group_id and token")

log = logging.getLogger('vk_bot_logger')


def configure_logging():
    logging_format = logging.Formatter(
        fmt="%(asctime)s %(levelname)s: %(funcName)s - %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S"
    )
    logging_format_print = logging.Formatter(fmt="%(levelname)s: %(lineno)d: %(funcName)s - %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging_format_print)
    stream_handler.setLevel(logging.INFO)

    file_handler = logging.FileHandler(filename="info.log", encoding="utf8")
    file_handler.setFormatter(logging_format)
    file_handler.setLevel(logging.DEBUG)

    log.addHandler(file_handler)
    log.addHandler(stream_handler)
    log.setLevel(logging.DEBUG)
    return log


# class UserState:
#     """State user into scenario"""
#     def __init__(self, scenario_name, step_name, context=None):
#         self.scenario_name = scenario_name
#         self.step_name = step_name
#         self.context = context or {}

class VkBot:
    """
    Сценарий регистрации на конференция "Best Conference"  через vk.com.
    Use python 3.9

    Поддерживает ответы на вопросы про дату, место проведения и сценарий регистрации:
    - спрашиваем имя
    - спрашиваем email
    - говорим об успешной регистрации
    Если шаг не пройден, задаем уточняющий вопрос пока шаг не будет пройден.
    """

    def __init__(self, group_id, token):
        """

        :param group_id: group id of VK
        :param token: secret token
        """
        self.group_id = group_id
        self.token = token
        self.vk = vk_api.VkApi(token=token)
        self.vk_bot_longpoll = VkBotLongPoll(self.vk, group_id)
        self.api = self.vk.get_api()

    def run(self):
        """
        Start bot
        :return: None
        """
        log.debug("Bot Start")
        try:
            for event in self.vk_bot_longpoll.listen():
                log.info("Поступило событие")
                self.on_event(event)
        except Exception as exc:
            log.exception(exc)

    @db_session
    def on_event(self, event):
        """
        Resend input massage
        :event VkBotMessageEvent
        :param event: obj event
        :return: None
        """
        if event.type != VkBotEventType.MESSAGE_NEW:
            log.warning(f'Мы пока не умеем обрабатывать события {event.type}')
            return
        user_id = event.message.from_id
        text = event.message.text

        state = UserState.get(user_id=str(user_id))
        if state is not None:
            self.continue_scenario(text=text, state=state, user_id=user_id)
        else:
            for intent in settings.INTENTS:
                log.debug(f'User get {intent}')
                if any(token in text.lower() for token in intent['tokens']):
                    if intent['answer']:
                        self.send_text(intent['answer'], user_id)
                    else:
                        self.start_scenario(user_id, intent['scenario'], text)
                    break
            else:
                self.send_text(settings.DEFAULT_ANSWER, user_id)

    def send_text(self, text_to_send, user_id):
        self.api.messages.send(user_id=user_id, random_id=randint(1, 2 ** 60), message=text_to_send)

    def send_image(self, image, user_id):
        pass

    def send_step(self, step, user_id, text, context):
        if 'text' in step:
            self.send_text(step['text'].format(**context), user_id=user_id)
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            image = handler(text, context)
            self.send_image(image, user_id)

    def start_scenario(self, user_id, scenario_name, text):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        self.send_step(step, user_id, text, context={})
        UserState(user_id=str(user_id), scenario_name=scenario_name, step_name=first_step, context={})

    def continue_scenario(self, text, state, user_id):
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = settings.SCENARIOS[state.scenario_name]['steps'][state.step_name]
        handler = getattr(handlers, step['handler'])
        if handler(text=text, context=state.context):
            next_step = steps[step['next_step']]
            self.send_step(next_step, user_id, text, state.context)
            if next_step['next_step']:
                state.step_name = step['next_step']
            else:
                log.info('Registered: {name}- {email}'.format(**state.context))
                RegistrationDB(name=state.context['name'], email=state.context['email'])
                generate_ticket(name=state.context['name'], email=state.context['email'])
                state.delete()
        else:
            text_to_send = step['failure_text'].format(**state.context)
            self.send_text(text_to_send, user_id)


if __name__ == '__main__':
    configure_logging()
    bot = VkBot(settings.GROUP_ID, settings.TOKEN)
    bot.run()
