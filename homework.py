import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

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
    level=logging.INFO,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s',
    filemode='a',
)
logger = logging.getLogger(__name__)
logger.addHandler(
    logging.StreamHandler()
)

class APIResponceError(Exception):
    """Кастомная ошибка при незапланированной работе API."""
    pass


def send_message(bot, message):
    """Отправка сообщений."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Отправлено сообщение: "{message}"')
    except telegram.error.TelegramError as error:
        logger.error(f'Ошибка: {error}')

def log_and_inform(bot, message):
    """Логирование ошибок уровня ERROR. 
    Отправка сообщений об ошибках в Телеграм,
    если это возможно.
    """
    sent_error_messages = []
    logger.error(message)
    if message not in sent_error_messages:
        try:
            send_message(bot, message)
            sent_error_messages.append(message)
        except Exception as error:
            logger.info('Не удалось отправить сообщение об ошибке, '
                        f'{error}')            


def get_api_answer(current_timestamp):
    """Отправка запроса к API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception:
        message = 'Незапланированная работа API'
        raise APIResponceError(message)
    try:
        if response.status_code != HTTPStatus.OK:
            message = 'Эндпоинт не отвечает'
            raise Exception(message)
    except Exception:
        message = 'Незапланированная работа API'
        raise APIResponceError(message)
    return response.json()


def check_response(response):
    """Проверка полученного ответа."""
    if not isinstance(response, dict):
        message = 'Ответ API не словарь'
        raise TypeError(message)
    if ['homeworks'][0] not in response:
        message = 'В ответе API нет домашней работы'
        raise IndexError(message)
    homework = response.get('homeworks')[0]
    return homework


def parse_status(homework):
    """Сообщение для отправки с обновленным состоянием."""
    keys = ['status', 'homework_name']
    for key in keys:
        if key not in homework:
            message = f'Ключа {key} нет в ответе API'
            raise KeyError(message)
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        message = f'Неизвестное состояние домашней работы'
        raise KeyError(message)
    homework_name = homework['homework_name']
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменилось состояние проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка переменных окружения."""
    vars = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    return None not in vars


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    errors = False
    while True:
        try:
            response = get_api_answer(current_timestamp)
            if 'current_date' in response:
                current_timestamp = response['current_date']
            homework = check_response(response)
            if homework is not None:
                message = parse_status(homework)
                if message is not None:
                    send_message(bot, message)
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            log_and_inform(bot, message)
            time.sleep(RETRY_TIME)

if __name__ == '__main__':
    main()
