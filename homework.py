import os
import time
import logging
import requests
from dotenv import load_dotenv
from telebot import TeleBot

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

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
)


def check_tokens():
    """Проверка наличия переменных окружения."""
    required_tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in required_tokens:
        if token is None:
            logging.critical(f'Переменная окружения {token} отсутствует.'
                             f'Бот не может быть запущен.')
            raise ValueError(
                'Нет необходимых переменных окружения'
            )


def send_message(bot, message):
    """Отправка сообщения боту."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID, text=message
        )
        logging.debug(f"Сообщение отправлено: '{message}'")
    except Exception as error:
        logging.error(f"Ошибка при отправке сообщения: {error}")


def get_api_answer(timestamp):
    """Проверка API-адреса."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=payload
        )
        if homework_statuses.status_code != 200:
            logging.error(
                f'Неожиданный статус работы: {homework_statuses.status_code}.'
            )
            raise ConnectionError(
                f'Неожиданный статус работы: {homework_statuses.status_code}'
            )
    except requests.RequestException as error:
        logging.error(f'Ошибка при запросе к API: {error}')
    return homework_statuses.json()


def check_response(response):
    """Проверка ответа."""
    if not isinstance(response, dict):
        raise TypeError('Неверный тип ответа')
    if 'homeworks' not in response or 'current_date' not in response:
        logging.error('Таких ключей нет')
        raise KeyError('В ответе нет нужных ключей')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Неверный тип данных')
    return homeworks


def parse_status(homework):
    """Извлечение информации из ответа."""
    if 'homework_name' not in homework or 'status' not in homework:
        logging.error('Таких ключей нет')
        raise KeyError('В ответе нет нужных ключей')
    if homework['status'] not in HOMEWORK_VERDICTS:
        logging.error('Неизвестный статус работы')
        raise ValueError(f"Неизвестный статус работы: '{homework['status']}'")
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    prev_homeworks = {}
    while True:
        try:
            response = get_api_answer(timestamp)
            if response:
                homeworks = check_response(response)
                if homeworks:
                    new_homework = homeworks[0]
                    new_homework_name = new_homework['homework_name']
                    new_status = new_homework['status']
                    if (
                        new_homework_name not in prev_homeworks
                        or prev_homeworks[new_homework_name] != new_status
                    ):
                        message = parse_status(new_homework)
                        send_message(bot, message)
                        prev_homeworks[new_homework_name] = new_status
                else:
                    message = 'Не удалось извлечь домашние задания.'
                    logging.error(message)
                    send_message(bot, message)
            else:
                message = 'Не удалось получить данные от API.'
                logging.error(message)
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
