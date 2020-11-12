from random import randint
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import logging
try:
    import settings
except:
    exit("setting.py.defualt -> settings.py and set group_id and token")

def configure_logging():
    logging_format = logging.Formatter(
        fmt="%(asctime)s %(levelname)s: %(funcName)s - %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S"
    )
    logging_format_print = logging.Formatter(fmt="%(levelname)s: %(lineno)d: %(funcName)s - %(message)s")
    log = logging.getLogger('vk_bot_logger')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging_format_print)
    stream_handler.setLevel(logging.INFO)

    file_handler = logging.FileHandler(filename="info.log", encoding="utf8")
    file_handler.setFormatter(logging_format)
    file_handler.setLevel(logging.DEBUG)

    log.addHandler(file_handler)
    log.addHandler(stream_handler)
    log.setLevel(logging.DEBUG)

class vkBot:
    """
    Echo Bot for vk.com
    Use python 3.9
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

    def on_event(self, event: VkBotEventType):
        """
        Resend input massage
        :param event: obj event
        :return: None
        """
        if event.type is VkBotEventType.MESSAGE_NEW:
            message = event.message.text
            log.debug("Новое сообщение")
            from_id = event.message.from_id
            random_id = randint(1, 2**60)
            self.api.messages.send(user_id=from_id, random_id=random_id, message=message)
        else:
            log.warning(f'Мы пока не умеем обрабатывать события {event.type}')


if __name__ == '__main__':
    configure_logging()
    bot = vkBot(settings.GROUP_ID, settings.TOKEN)
    bot.run()