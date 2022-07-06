import logging
import os
import sys
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
    level=logging.INFO,
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    filename='main.log',
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправляет сообщение в чат Telegram."""
    try:
        logger.info('Сообщение успешно отправлено')
        return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logger.error(f'Не удалось отправить сообщение {error}', exc_info=True)
        raise exceptions.SendMessageException(error)


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту ЯП."""
    params = {'from_date': current_timestamp}
    try:
        answer = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if answer.status_code != HTTPStatus.OK:
            status = answer.raise_for_status()
            error_message = f'Неверный статус ответа: {status}'
            logger.error(error_message)
            raise exceptions.GetAPIException(error_message)
        return answer.json()
    except Exception:
        error_message = 'Не удалось получить доступ к API'
        logger.error(error_message)
        raise exceptions.GetAPIException(error_message)


def check_response(response):
    """Проверяет корректность ответа API."""
    try:
        homework_list = response['homeworks']
    except KeyError as error:
        error_message = f'В словаре нет ключа homeworks {error}'
        logger.error(error_message)
        raise KeyError(error_message)

    if not isinstance(homework_list, list):
        error_message = 'Домашние работы в ответе API выводятся не списком'
        logger.error(error_message)
        raise exceptions.APIResponseException(error_message)
    return homework_list


def parse_status(homework):
    """Получает статус домашней работы."""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
    except KeyError as error:
        error_message = f'В словаре нет ключа: {error}'
        logger.error(error_message)
        raise KeyError(error_message)
    verdict = HOMEWORK_STATUSES.get(homework_status)
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
    if not check_tokens():
        message = 'Отсутствует переменная окружения'
        logger.critical(message)
        sys.exit()

    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)

    except Exception as error:
        message = f'Ошибка при создании бота: {error}'
        logger.critical(message)
        sys.exit()

    current_timestamp = 0

    while True:
        try:
            api_response = get_api_answer(current_timestamp)
            homeworks = check_response(api_response)
            logger.info(f'Список домашних работ получен {len(homeworks)}')
            for item in homeworks:
                send_message(bot, parse_status(item))
            current_timestamp = int(time.time())

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.exception(f'Возникла ошибка: {error}')
            send_message(bot, message)

        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
