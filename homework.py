import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    encoding='utf-8',
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    filemode='a',
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream='sys.stdout')
logger.addHandler(handler)

def send_message(bot, message):
    """Отправляет сообщение в чат Telegram."""
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        logger.info('Сообщение успешно отправлено')
        return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logger.error(f'Не удалось отправить сообщение {error}', exc_info=True)
        raise exceptions.SendMessageException(error)


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту ЯП."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        answer = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception:
        error_message = 'Не удалось получить доступ к API'
        logger.error(error_message)
        raise exceptions.GetAPIException(error_message)
    if answer.status_code != HTTPStatus.OK:
        answer.raise_for_status()
        error_message = 'Неверный статус ответа'
        logger.error(error_message)
        raise exceptions.GetAPIException(error_message)
    return answer.json()


def check_response(response):
    """Проверяет корректность ответа API."""
    try:
        home_list = response['homeworks']
    except KeyError as error:
        error_message = f'В словаре нет ключа homeworks {error}'
        logger.error(error_message)
        raise KeyError(error_message)
    if not home_list:
        error_message = 'В ответе API нет списка домашних работ'
        logger.error(error_message)
        raise exceptions.APIResponseException(error_message)
    if len(home_list) == 0:
        error_message = 'На ревью ничего не отправлено'
        logger.error(error_message)
        raise exceptions.APIResponseException(error_message)
    if not isinstance(home_list, list):
        error_message = 'Домашние работы в ответе API выводятся не списком'
        logger.error(error_message)
        raise exceptions.APIResponseException(error_message)
    return home_list


def parse_status(homework):
    """Получает статус домашней работы."""
    try:
        homework_name = homework['homework_name']
    except KeyError as error:
        error_message = f'В словаре нет ключа homework_name {error}'
        logger.error(error_message)
        raise KeyError(error_message)
    try:
        homework_status = homework['status']
    except KeyError as error:
        error_message = f'В словаре нет ключа status {error}'
        logger.error(error_message)
        raise KeyError(error_message)
    verdict = HOMEWORK_STATUSES[homework_status]
    if verdict is None:
        error_message = 'Нет сообщения о статусе проверки домашней работы'
        logger.error(error_message)
        raise exceptions.StatusException(error_message)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет наличие переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    current_timestamp = int(time.time())
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    previous_response = 0
    while True:
        try:
            response = get_api_answer(current_timestamp)
            check_response(response)
            if response != previous_response:
                previous_response = response
                check_response(response)
                message = parse_status(response.get('homeworks')[0])
                send_message(bot, message)
            if not check_tokens():
                error_message = 'Нет переменной окружения!'
                logger.error(error_message)
                raise exceptions.VariableException(error_message)
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.exception(f'Возникла ошибка: {error}')
            send_message(f'{message} {error}', bot)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
