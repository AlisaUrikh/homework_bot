import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.apihelper import ApiTelegramException

from exceptions import APIResponseError, UnavailablePageError


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка наличия переменных окружения."""
    required_tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    unavailable_tokens = []
    for key, value in required_tokens.items():
        if value is None:
            unavailable_tokens.append(key)
    return unavailable_tokens


def send_message(bot, message: str) -> None:
    """Отправка сообщения боту."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID, text=message
        )
    except (ApiTelegramException, requests.RequestException) as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')
    else:
        logging.debug(f"Сообщение успешно отправлено: '{message}'")


def get_api_answer(timestamp):
    """Проверка API-адреса."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=payload
        )
        if homework_statuses.status_code != HTTPStatus.OK:
            raise UnavailablePageError(
                f'Неожиданный статус работы: {homework_statuses.status_code}'
            )
    except requests.RequestException as error:
        raise APIResponseError(
            f'Не удалось получить ответ от API: {error}'
        )
    return homework_statuses.json()


def check_response(response):
    """Проверка ответа."""
    if not isinstance(response, dict):
        raise TypeError('Неверный тип ответа')
    if 'homeworks' not in response or 'current_date' not in response:
        raise KeyError('В ответе нет нужных ключей')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Неверный тип данных')
    return homeworks


def parse_status(homework):
    """Извлечение информации из ответа."""
    if 'homework_name' not in homework or 'status' not in homework:
        raise KeyError('В ответе нет нужных ключей')
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise ValueError(f"Неизвестный статус работы: '{homework['status']}'")
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    missing_tokens = check_tokens()
    if len(missing_tokens) > 0:
        unavailable_tokens = ', '.join(missing_tokens)
        logging.critical(
            f'Нет необходимых переменных окружения: {unavailable_tokens}. '
            'Бот не может быть запущен.'
        )
        sys.exit()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_message = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                new_homework = homeworks[0]
                message = parse_status(new_homework)
            else:
                message = 'Статус работы не изменился.'
            if message != previous_message:
                send_message(bot, message)
                previous_message = message
        except Exception as error:
            message = f'Ошибка в работе программы: {error}'
            logging.error(message)
            if message != previous_message:
                send_message(bot, message)
                previous_message = message
                timestamp = response.get('current_date')
        else:
            timestamp = response.get('current_date', timestamp)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG,
    )
    main()
