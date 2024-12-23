# homework_bot
python telegram bot
Этот телеграм-бот создан для того, чтобы оповещать студента о новом статусе домашней работы. Основная цель -- обращение к API Яндекс.Практикума, который позволяет получить доступ к домашним работам и узнать их статус. 

# Установка и локальный запуск
# Настройка виртуального окружения
pythom -m venv
venv/Scripts/activate
# Установка зависимостей
pip install -r requirements.txt

# Переменные окружения
PRACTICUM_TOKEN = ваш_практикум_токен
TELEGRAM_CHAT_ID = ваш_телеграм_id
TELEGRAM_TOKEN = ваш_телеграм_токен

# Интервал работы программы (проверки статуса)
RETRY_PERIOD = 600
# Эндпоинт
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/' 
# HTTP-заголовки для авторизации при отправке запросов к API
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'} 

# Возможные статусы работ
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
} 


